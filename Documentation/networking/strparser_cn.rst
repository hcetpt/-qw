SPDX 许可证标识符: GPL-2.0

=========================
流解析器（strparser）
=========================

简介
============

流解析器（strparser）是一个解析运行在数据流上的应用层协议消息的工具。流解析器与内核中的上层协同工作，为应用层消息提供内核支持。例如，内核连接复用器（KCM）使用流解析器通过BPF程序解析消息。strparser有两种工作模式：接收回调模式或通用模式。
在接收回调模式下，strparser从TCP套接字的数据准备好（data_ready）回调中被调用。消息在接收到时被解析并传递。
在通用模式下，一系列skbs从外部源馈送到strparser。随着序列的处理，消息被解析并传递。这种模式允许strparser应用于任意数据流。

接口
=========

API包含一个上下文结构、一组回调函数、实用函数以及接收回调模式下的数据准备好（data_ready）函数。这些回调函数包括一个parse_msg函数，用于执行解析（如KCM中的BPF解析），以及一个rcv_msg函数，在完整消息完成后被调用。

函数
=========

     ::

	strp_init(struct strparser *strp, struct sock *sk,
		const struct strp_callbacks *cb)

     被调用来初始化一个流解析器。strp是一个由上层分配的类型为strparser的结构体。sk是与流解析器关联的TCP套接字，用于接收回调模式；在通用模式下设置为NULL。流解析器会调用回调函数（如下所示）。

::

	void strp_pause(struct strparser *strp)

     暂时暂停一个流解析器。消息解析被挂起，并且不会向上传递任何新消息。

::

	void strp_unpause(struct strparser *strp)

     恢复已暂停的流解析器。

::

	void strp_stop(struct strparser *strp);

     strp_stop被调用来完全停止流解析器的操作。当流解析器遇到错误时内部会调用它，并且可以从上层调用以停止解析操作。
```
void strp_done(struct strparser *strp);

    strp_done 被调用来释放流解析器实例持有的任何资源。这必须在流处理器停止后调用。

int strp_process(struct strparser *strp, struct sk_buff *orig_skb,
		 unsigned int orig_offset, size_t orig_len,
		 size_t max_msg_size, long timeo)

    strp_process 通常用于流解析器解析一个 `sk_buff`。返回值是处理的字节数或负的错误码。注意，strp_process 不会消耗 `sk_buff`。`max_msg_size` 是流解析器将解析的最大消息大小。`timeo` 是完成一条消息的超时时间。

void strp_data_ready(struct strparser *strp);

    当底层套接字上有数据可供 `strparser` 处理时，上层调用 `strp_data_ready`。这应该从设置在套接字上的数据就绪回调中调用。注意，最大消息大小是接收套接字缓冲区的限制，消息超时是套接字的接收超时时间。

void strp_check_rcv(struct strparser *strp);

    strp_check_rcv 被调用来检查套接字上的新消息。这通常在流解析器实例初始化时或 `strp_unpause` 后调用。

回调函数
========

共有六个回调函数：

    ::

int (*parse_msg)(struct strparser *strp, struct sk_buff *skb);

    `parse_msg` 用于确定流中的下一条消息长度。上层必须实现这个函数。它应该解析 `sk_buff` 作为包含流中下一个应用层消息的头部。
输入 `skb->cb` 中是一个 `struct strp_msg`。在 `parse_msg` 中仅 `offset` 字段相关，它给出了消息在 `sk_buff` 中的起始偏移量。
此函数的返回值为：

    =========    ===========================================================
    >0           表示成功解析的消息长度
    0            表示需要接收更多数据才能解析消息
    -ESTRPIPE    当前消息不应由内核处理，将套接字控制权交还给用户空间，以便自行读取消息
    其他 < 0     解析出错，假定同步已丢失且流不可恢复（预期应用程序关闭 TCP 套接字）
    =========    ===========================================================

    如果返回错误（返回值小于零），并且解析器处于接收回调模式，则会在 TCP 套接字上设置错误并唤醒它。如果 `parse_msg` 返回 `-ESTRPIPE` 并且流解析器先前已经读取了当前消息的一些字节，则在关联的套接字上设置的错误为 `ENODATA`，因为此时流不可恢复。

::

void (*lock)(struct strparser *strp)

    锁定回调被调用来锁定 `strp` 结构，当流解析器执行异步操作（例如处理超时）时。在接收回调模式下，默认函数是对关联套接字调用 `lock_sock`。在一般模式下，回调必须适当设置。

::

void (*unlock)(struct strparser *strp)

    解锁回调被调用来释放由锁定回调获得的锁。在接收回调模式下，默认函数是对关联套接字调用 `release_sock`。在一般模式下，回调必须适当设置。
```
```c
// 指向接收消息函数的指针定义
void (*rcv_msg)(struct strparser *strp, struct sk_buff *skb);

// 当接收到完整的消息并入队时调用 rcv_msg。
// 被调用者必须消费 sk_buff；它可以调用 strp_pause 来防止在 rcv_msg 中接收任何进一步的消息（见上方的 strp_pause）。
// 此回调必须设置。
// 输入 skb 的 skb->cb 是一个 struct strp_msg 结构。该结构包含两个字段：offset 和 full_len。
// offset 表示消息在 skb 中的起始位置，full_len 是消息的长度。
// skb->len - offset 可能大于 full_len，因为 strparser 不会修剪 skb。

// 读取套接字完成的回调函数
int (*read_sock_done)(struct strparser *strp, int err);

// 当流解析器在接收回调模式下完成从 TCP 套接字读取时调用 read_sock_done。
// 流解析器可能在一个循环中读取多个消息，此函数允许在退出循环时进行清理。
// 如果未设置回调（strp_init 中为 NULL），则使用默认函数。

// 解析错误时的回调函数
void (*abort_parser)(struct strparser *strp, int err);

// 当流解析器在解析过程中遇到错误时调用此函数。
// 默认函数停止流解析器，并在接收回调模式下设置套接字中的错误。
// 通过在 strp_init 中将回调设置为非 NULL 可以更改默认函数。

// 统计信息
// =========

// 对于每个流解析器实例，维护了各种计数器。这些计数器位于 strp_stats 结构中。
// strp_aggr_stats 是一个方便的结构，用于累积多个流解析器实例的统计信息。
// save_strp_stats 和 aggregate_strp_stats 是用于保存和累积统计信息的辅助函数。

// 消息组装限制
// ==============

// 流解析器提供了限制消息组装所消耗资源的机制。
// 在开始组装新消息时设置一个定时器。在接收回调模式下，消息超时是从关联的 TCP 套接字的 rcvtime 获取的。
// 在通用模式下，超时作为参数传递给 strp_process。
// 如果定时器在组装完成前触发，则流解析器被终止，并且如果在接收回调模式下则在 TCP 套接字上设置 ETIMEDOUT 错误。

// 在接收回调模式下，消息长度限制为关联的 TCP 套接字的接收缓冲区大小。
// 如果 parse_msg 返回的长度大于套接字缓冲区大小，则流解析器被终止，并且在 TCP 套接字上设置 EMSGSIZE 错误。
// 注意，这使得具有流解析器的套接字的最大接收 sk_buff 大小为 2 * sk_rcvbuf 的 TCP 套接字大小。

// 在通用模式下，消息长度限制作为参数传递给 strp_process。
```

希望这个翻译对你有帮助！如果有任何需要进一步解释的地方，请告诉我。
作者
======

汤姆·赫伯特（tom@quantonium.net）
