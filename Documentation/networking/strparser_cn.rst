### SPDX 许可证标识符: GPL-2.0

=========================
流解析器（strparser）
=========================

简介
============

流解析器（strparser）是一个用于解析在数据流上运行的应用层协议消息的工具。流解析器与内核中的上层协同工作，为应用层消息提供内核支持。例如，内核连接复用器（KCM）使用流解析器通过BPF程序来解析消息。
strparser有两种工作模式：接收回调模式或通用模式。
在接收回调模式下，strparser从TCP套接字的数据_ready回调中被调用。消息在收到时即被解析并传递。
在通用模式下，一系列skb从外部源送入strparser。随着序列的处理，消息被解析并传递。这种模式允许strparser应用于任意的数据流。

接口
=========

API包括一个上下文结构、一组回调函数、实用函数和一个用于接收回调模式的数据_ready函数。回调函数包括一个parse_msg函数，该函数被调用来执行解析（例如，在KCM的情况下进行BPF解析），以及一个rcv_msg函数，在完成一条完整消息时被调用。

函数
=========

     ::

    strp_init(struct strparser *strp, struct sock *sk,
        const struct strp_callbacks *cb)

     用于初始化流解析器。strp是类型为strparser的结构体，由上层分配。sk是与流解析器关联的TCP套接字，用于接收回调模式；在通用模式下设置为NULL。回调函数由流解析器调用（下面列出了这些回调函数）。

::

    void strp_pause(struct strparser *strp)

     暂时暂停流解析器。消息解析被挂起，并且不会向高层交付新的消息。

::

    void strp_unpause(struct strparser *strp)

     解除已暂停的流解析器的暂停状态。

::

    void strp_stop(struct strparser *strp);

     调用strp_stop来完全停止流解析器的操作。当流解析器遇到错误时内部会调用它，也可以从上层调用来停止解析操作。
下面是给定代码段的中文翻译：

```
void strp_done(struct strparser *strp);

```

`strp_done`函数用于释放流解析器实例持有的任何资源。必须在停止流处理器后调用此函数。

```
int strp_process(struct strparser *strp, struct sk_buff *orig_skb,
                 unsigned int orig_offset, size_t orig_len,
                 size_t max_msg_size, long timeo)

```

`strp_process`通常模式下调用，用于让流解析器解析一个`sk_buff`。返回值是处理的字节数或负数错误码。需要注意的是，`strp_process`并不会消耗`sk_buff`。`max_msg_size`是流解析器将解析的最大消息大小。`timeo`是完成消息的超时时间。

```
void strp_data_ready(struct strparser *strp);

```

当底层套接字上有数据可供`strparser`处理时，上层调用`strp_data_ready`。这应该从设置在套接字上的`data_ready`回调中调用。需要注意的是，最大消息大小是接收套接字缓冲区的限制，而消息超时是套接字的接收超时。

```
void strp_check_rcv(struct strparser *strp);

```

`strp_check_rcv`用于检查套接字上是否有新消息。这通常在流解析器实例初始化时或`strp_unpause`之后调用。
  
### 回调

共有六个回调：

```
int (*parse_msg)(struct strparser *strp, struct sk_buff *skb);

```

`parse_msg`用于确定流中的下一个消息的长度。上层必须实现这个函数。它应当解析`sk_buff`，将其视为包含流中的下一个应用层消息的头部。
输入`skb->cb`是一个`struct strp_msg`结构。在`parse_msg`中，只有`offset`字段是相关的，并给出消息在`sk_buff`中开始的位置。
该函数的返回值说明如下：

| 返回值 | 解释 |
| --- | --- |
| >0 | 成功解析的消息长度 |
| 0 | 需要接收更多数据才能解析消息 |
| -ESTRPIPE | 当前消息不应由内核处理，将套接字控制权交还用户空间自行读取消息 |
| 其他 < 0 | 解析出错，将控制权交还给用户空间，假设同步已丢失且流无法恢复（预期应用程序会关闭TCP套接字） |

如果返回错误（返回值小于零），并且解析器处于接收回调模式，则会设置TCP套接字的错误并唤醒它。如果`parse_msg`返回-ESTRPIPE，并且流解析器之前已经为当前消息读取了一些字节，则在相关联的套接字上设置的错误是ENODATA，因为此时流是不可恢复的。

```
void (*lock)(struct strparser *strp)

```

当流解析器执行异步操作（例如处理超时）时，调用`lock`回调来锁定`strp`结构。在接收回调模式下，默认函数是为关联套接字调用`lock_sock`。在通常模式下，需要适当设置此回调。

```
void (*unlock)(struct strparser *strp)

```

调用`unlock`回调以释放`lock`回调获得的锁。在接收回调模式下，默认函数是为关联套接字调用`release_sock`。在通常模式下，需要适当设置此回调。
### 函数指针定义

```c
void (*rcv_msg)(struct strparser *strp, struct sk_buff *skb);
```

`rcv_msg` 在接收到完整消息并将其排队时被调用。调用者必须消费 `sk_buff`；它可以调用 `strp_pause` 来阻止在 `rcv_msg` 中接收任何进一步的消息（参见上面的 `strp_pause`）。此回调必须设置。

输入 `sk_buff` 的 `skb->cb` 是一个 `struct strp_msg` 结构体。该结构包含两个字段：`offset` 和 `full_len`。`offset` 表示消息在 `sk_buff` 中的起始位置，而 `full_len` 是消息的长度。`skb->len - offset` 可能大于 `full_len`，因为 `strparser` 不会修剪 `sk_buff`。

```c
int (*read_sock_done)(struct strparser *strp, int err);
```

`read_sock_done` 在流解析器完成读取 TCP 套接字（在接收回调模式下）时被调用。流解析器可能在一个循环中读取多个消息，并且此函数允许在退出循环时进行清理。如果未设置回调（即 `strp_init` 中为 NULL），则使用默认函数。

```c
void (*abort_parser)(struct strparser *strp, int err);
```

当流解析器在解析过程中遇到错误时调用此函数。默认函数会停止流解析器并在套接字上设置错误（如果解析器处于接收回调模式）。可以通过在 `strp_init` 中将回调设置为非 NULL 来更改默认函数。

### 统计信息

每个流解析器实例都维护了各种计数器。这些计数器位于 `strp_stats` 结构体中。`strp_aggr_stats` 是用于汇总多个流解析器实例统计信息的便利结构体。`save_strp_stats` 和 `aggregate_strp_stats` 是用于保存和汇总统计信息的辅助函数。

### 消息组装限制

流解析器提供了限制消息组装消耗资源的机制。

- **超时机制**：当开始组装新消息时设置一个定时器。在接收回调模式下，消息超时时间从关联的 TCP 套接字的 `rcvtime` 获取。在一般模式下，超时时间作为参数传递给 `strp_process`。如果定时器在组装完成前触发，则流解析器被终止，并在 TCP 套接字上设置 `ETIMEDOUT` 错误（如果处于接收回调模式）。
  
- **消息长度限制**：
  - 在接收回调模式下，消息长度受限于关联的 TCP 套接字的接收缓冲区大小。如果 `parse_msg` 返回的长度大于套接字缓冲区大小，则流解析器被终止，并在 TCP 套接字上设置 `EMSGSIZE` 错误。请注意，这使得带有流解析器的套接字的最大接收 `sk_buff` 大小为 TCP 套接字 `sk_rcvbuf` 的两倍。
  - 在一般模式下，消息长度限制作为参数传递给 `strp_process`。
作者
======

汤姆·赫伯特 (tom@quantonium.net)
