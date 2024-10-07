SPDX 许可声明标识符: BSD-3-Clause

=======================
Netlink 简介
=======================

Netlink 经常被描述为 ioctl() 的替代方案。
它的目标是用一种允许轻松添加或扩展参数的格式替换 ioctl() 接收的固定格式的 C 结构体。
为了实现这一点，Netlink 使用了一个最小的固定格式元数据头，后面跟着多个类型长度值（TLV）格式的属性。
不幸的是，该协议多年来经历了有机且未文档化的演变，使得其难以连贯地解释。
为了更实际地理解，本文档首先描述了当前使用的 Netlink，并在后续部分探讨更多“历史”用途。

打开套接字
================

Netlink 通信通过套接字进行，需要先打开一个套接字：

```c
fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_GENERIC);
```

使用套接字允许以自然的方式双向交换信息（从用户空间到内核和从内核到用户空间）。当应用程序发送（send）请求时，操作仍然是同步的，但需要单独的接收（recv）系统调用来读取回复。
因此，Netlink “调用”的简化流程如下：

```c
fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_GENERIC);

/* 格式化请求 */
send(fd, &request, sizeof(request));
n = recv(fd, &response, RSP_BUFFER_SIZE);
/* 解释响应 */
```

Netlink 还提供了自然的支持来“转储”，即向用户空间传输特定类型的全部对象（例如转储所有网络接口）：

```c
fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_GENERIC);

/* 格式化转储请求 */
send(fd, &request, sizeof(request));
while (1) {
    n = recv(fd, &buffer, RSP_BUFFER_SIZE);
    /* 单次 recv() 调用可能读取多条消息，因此下面需要循环处理 */
    for (nl_msg in buffer) {
        if (nl_msg.nlmsg_type == NLMSG_DONE)
            goto dump_finished;
        /* 处理对象 */
    }
}
dump_finished:
```

`socket()` 调用的前两个参数需要较少的解释 - 它是在打开一个 Netlink 套接字，其中所有头部由用户提供（因此使用 NETLINK 和 RAW）。最后一个参数是 Netlink 内部的协议。这个字段用于标识套接字将与之通信的子系统。

经典 Netlink 与通用 Netlink
--------------------------

Netlink 初始实现依赖于对子系统的静态 ID 分配，并提供的支持基础设施很少。
让我们将这些协议统称为**经典Netlink**。
它们的列表定义在文件`include/uapi/linux/netlink.h`的顶部，其中包括但不限于一般网络（NETLINK_ROUTE）、iSCSI（NETLINK_ISCSI）和审计（NETLINK_AUDIT）。

**通用Netlink**（2005年引入）允许动态注册子系统（以及子系统ID分配），提供内省功能，并简化了实现接口的内核部分。
以下部分描述了如何使用通用Netlink，因为使用通用Netlink的子系统的数量比旧协议的数量多出一个数量级。目前也没有计划向内核添加更多的经典Netlink协议。

关于如何与Linux内核的核心网络部分（或使用经典Netlink的其他20个子系统之一）通信与通用Netlink的不同之处将在本文档后面的章节中提供。

通用Netlink
===========

除了Netlink固定的元数据头外，每个Netlink协议还定义了自己的固定元数据头。（类似于网络报头的堆叠方式：以太网 > IP > TCP，我们有Netlink > 通用Netlink > 家族。）

一个Netlink消息总是以结构体`nlmsghdr`开始，其后是特定于协议的头。在通用Netlink的情况下，协议头是结构体`genlmsghdr`。

在通用Netlink的情况下，字段的实际含义如下：

```c
struct nlmsghdr {
	__u32	nlmsg_len;	/* 包括头部的消息长度 */
	__u16	nlmsg_type;	/* 通用Netlink家族（子系统）ID */
	__u16	nlmsg_flags;	/* 标志 - 请求或转储 */
	__u32	nlmsg_seq;	/* 序列号 */
	__u32	nlmsg_pid;	/* 端口ID，设置为0 */
};
struct genlmsghdr {
	__u8	cmd;		/* 家族定义的命令 */
	__u8	version;	/* 无关紧要，设置为1 */
	__u16	reserved;	/* 预留，设置为0 */
};
/* TLV属性跟随... */
```

在经典Netlink中，`nlmsghdr.nlmsg_type`用于标识消息所指的子系统中的操作（例如获取netdev的信息）。通用Netlink需要在一个协议中复用多个子系统，因此它使用此字段来标识子系统，而`genlmsghdr.cmd`则标识操作。（有关如何找到感兴趣的子系统家族ID的信息，请参阅：:ref:`res_fam`。）
请注意，此字段的前16个值（0 - 15）在经典Netlink和通用Netlink中都保留用于控制消息。
有关更多详细信息，请参阅：:ref:`nl_msg_type`。
在Netlink套接字上通常有三种类型的消息交换：

- 执行单个动作（`do`）；
- 转储信息（`dump`）；
- 接收异步通知（`multicast`）。

经典Netlink非常灵活，理论上允许其他类型的交换发生，但在实践中，这三种是最常用的。
异步通知由内核发送并被订阅了这些通知的用户套接字接收。`do` 和 `dump` 请求由用户发起。:c:member:`nlmsghdr.nlmsg_flags` 应按如下设置：

- 对于 `do`：`NLM_F_REQUEST | NLM_F_ACK`
- 对于 `dump`：`NLM_F_REQUEST | NLM_F_ACK | NLM_F_DUMP`

:c:member:`nlmsghdr.nlmsg_seq` 应设置为单调递增的值。该值在响应中会被回显，但实际上并不重要，但为每个发送的消息设置一个递增的值被认为是良好的编程习惯。该字段的目的是匹配请求和响应。异步通知将具有 :c:member:`nlmsghdr.nlmsg_seq` 的值为 `0`。

:c:member:`nlmsghdr.nlmsg_pid` 是 Netlink 中的地址等价物。与内核通信时，可以将其设置为 `0`。
请参阅 :ref:`nlmsg_pid` 了解该字段的（不常见）用途。

:c:member:`genlmsghdr.version` 预期用途是允许子系统提供的 API 版本化。到目前为止，没有子系统显著使用此字段，因此将其设置为 `1` 看起来是一个安全的选择。

.. _nl_msg_type:

Netlink 消息类型
---------------------

如前所述，:c:member:`nlmsghdr.nlmsg_type` 包含特定协议的值，但前 16 个标识符是保留的（第一个子系统特定消息类型的值应等于 `NLMSG_MIN_TYPE`，即 `0x10`）。
只有 4 种 Netlink 控制消息定义：

- `NLMSG_NOOP` - 忽略消息，实践中未使用；
- `NLMSG_ERROR` - 携带操作的返回码；
- `NLMSG_DONE` - 标记转储的结束；
- `NLMSG_OVERRUN` - 套接字缓冲区溢出，至今未使用

`NLMSG_ERROR` 和 `NLMSG_DONE` 在实践中很重要。它们携带操作的返回码。请注意，除非请求设置了 `NLM_F_ACK` 标志，否则如果没有错误，Netlink 不会用 `NLMSG_ERROR` 响应。为了避免为此特性做特殊处理，建议始终设置 `NLM_F_ACK`。

`NLMSG_ERROR` 的格式由结构体 `nlmsgerr` 描述如下：

```
----------------------------------------------
| struct nlmsghdr - 响应头                    |
----------------------------------------------
|    int error                                |
----------------------------------------------
| struct nlmsghdr - 原始请求头               |
----------------------------------------------
| ** 可选 (1) 请求的有效载荷                 |
----------------------------------------------
| ** 可选 (2) 扩展确认                       |
----------------------------------------------
```

这里有两个 `struct nlmsghdr` 实例，一个是响应的，另一个是请求的。`NLMSG_ERROR` 携带导致错误的请求信息。这在尝试匹配请求和响应或将请求重新解析以记录日志时可能是有用的。
请求的有效载荷在报告成功（`error == 0`）的消息中不会回显，或者如果设置了 `NETLINK_CAP_ACK` 的 setsockopt()。后者很常见，并且可能建议这样做，因为从内核读取每个请求的副本是非常浪费的。请求有效载荷的缺失由 `nlmsghdr.nlmsg_flags` 中的 `NLM_F_CAPPED` 表示。`NLMSG_ERROR` 的第二个可选元素是扩展确认属性。更多详细信息请参见 :ref:`ext_ack`。扩展确认的存在由 `nlmsghdr.nlmsg_flags` 中的 `NLM_F_ACK_TLVS` 表示。

`NLMSG_DONE` 更简单，请求从不回显，但可能包含扩展确认属性：

```
----------------------------------------------
| struct nlmsghdr - 响应头部                  |
----------------------------------------------
|    int error                                |
----------------------------------------------
| ** 可选地扩展确认                           |
----------------------------------------------
```

注意，某些实现可能会针对 `do` 操作请求发出自定义的 `NLMSG_DONE` 消息。在这种情况下，有效载荷是特定于实现的，也可能不存在。

.. _res_fam:

解析家庭ID
-----------

本节解释了如何找到子系统的家庭ID。这也作为通用Netlink通信的一个示例。通用Netlink本身是一个通过通用Netlink API暴露的子系统。为了避免循环依赖，通用Netlink有一个静态分配的家庭ID (`GENL_ID_CTRL`，等于 `NLMSG_MIN_TYPE`)。通用Netlink家庭实现了一个命令，用于获取其他家庭的信息 (`CTRL_CMD_GETFAMILY`)。为了获取名为 "test1" 的通用Netlink家庭的信息，我们需要在之前打开的通用Netlink套接字上发送一条消息。这条消息应该针对通用Netlink家庭 (1)，并调用 `CTRL_CMD_GETFAMILY` (2) 的 `do` (3) 操作。这个调用的 `dump` 版本将使内核响应所有它知道的家庭信息。最后但并非最不重要的是，需要指定相关家庭的名字 (4)，作为具有适当类型的属性：

```
struct nlmsghdr:
  __u32 nlmsg_len:   32
  __u16 nlmsg_type:  GENL_ID_CTRL               // (1)
  __u16 nlmsg_flags: NLM_F_REQUEST | NLM_F_ACK  // (2)
  __u32 nlmsg_seq:   1
  __u32 nlmsg_pid:   0

struct genlmsghdr:
  __u8 cmd:      CTRL_CMD_GETFAMILY           // (3)
  __u8 version:  2 /* 或 1，没有区别 */
  __u16 reserved: 0

struct nlattr:                                      // (4)
  __u16 nla_len:  10
  __u16 nla_type: CTRL_ATTR_FAMILY_NAME
  char data:     test1\0

(填充:)
  char data: \0\0
```

Netlink 中的长度字段（`nlmsghdr.nlmsg_len` 和 `nlattr.nla_len`）总是 包含 头部。
Netlink中的属性头必须从消息的起始位置对齐到4字节，因此在`CTRL_ATTR_FAMILY_NAME`之后有额外的`\0\0`。属性长度不包括填充。

如果找到家族，内核将回复两条消息，其中一条包含关于该家族的所有信息：

  /* 消息#1 - 回复 */
  struct nlmsghdr:
    __u32 nlmsg_len: 136
    __u16 nlmsg_type: GENL_ID_CTRL
    __u16 nlmsg_flags: 0
    __u32 nlmsg_seq: 1    /* 从我们的请求中回显 */
    __u32 nlmsg_pid: 5831 /* 我们用户空间进程的PID */

  struct genlmsghdr:
    __u8 cmd: CTRL_CMD_GETFAMILY
    __u8 version: 2
    __u16 reserved: 0

  struct nlattr:
    __u16 nla_len: 10
    __u16 nla_type: CTRL_ATTR_FAMILY_NAME
    char data: test1\0

  （填充：）
    data: \0\0

  struct nlattr:
    __u16 nla_len: 6
    __u16 nla_type: CTRL_ATTR_FAMILY_ID
    __u16: 123  /* 我们要找的家族ID */

  （填充：）
    char data: \0\0

  struct nlattr:
    __u16 nla_len: 9
    __u16 nla_type: CTRL_ATTR_FAMILY_VERSION
    __u16: 1

  /* ... 等等，后面还有更多属性。 */

以及成功后的错误代码（成功），因为请求中设置了`NLM_F_ACK`：

  /* 消息#2 - ACK */
  struct nlmsghdr:
    __u32 nlmsg_len: 36
    __u16 nlmsg_type: NLMSG_ERROR
    __u16 nlmsg_flags: NLM_F_CAPPED /* 不会有负载 */
    __u32 nlmsg_seq: 1    /* 从我们的请求中回显 */
    __u32 nlmsg_pid: 5831 /* 我们用户空间进程的PID */

  int error: 0

  struct nlmsghdr: /* 我们发送时的请求头的副本 */
    __u32 nlmsg_len: 32
    __u16 nlmsg_type: GENL_ID_CTRL
    __u16 nlmsg_flags: NLM_F_REQUEST | NLM_F_ACK
    __u32 nlmsg_seq: 1
    __u32 nlmsg_pid: 0

属性（struct nlattr）的顺序没有保证，因此用户需要遍历这些属性并解析它们。
请注意，通用Netlink套接字与单一家族无关联或绑定。一个套接字可以用于与许多不同的家族交换消息，通过使用`:c:member:'nlmsghdr.nlmsg_type'`字段选择每个消息的目标家族。
.. _ext_ack:

扩展ACK
--------

扩展ACK控制在`NLMSG_ERROR`和`NLMSG_DONE`消息中报告附加的错误/警告TLV。为了保持向后兼容性，此功能必须通过设置`NETLINK_EXT_ACK` setsockopt()为`1`来显式启用。
扩展ACK属性类型定义在枚举`nlmsgerr_attrs`中。最常用的属性是`NLMSGERR_ATTR_MSG`、`NLMSGERR_ATTR_OFFS`和`NLMSGERR_ATTR_MISS_*`。
`NLMSGERR_ATTR_MSG`携带一个英文描述，说明遇到的问题。这些消息比标准UNIX错误代码所能表达的详细得多。
`NLMSGERR_ATTR_OFFS`指向导致问题的属性。
`NLMSGERR_ATTR_MISS_TYPE`和`NLMSGERR_ATTR_MISS_NEST`会告知缺少的属性。
扩展确认（ACK）可以在错误发生时以及成功时报告
后者应被视为警告
扩展ACK显著提高了Netlink的可用性，应始终启用，并适当地解析和报告给用户

高级主题
===============

转储一致性
----------------

内核用于存储对象的一些数据结构使得在转储中提供所有对象的原子快照变得困难（而不影响更新它们的快速路径）
如果转储被中断且可能不一致（例如缺少对象），内核可能会在转储中的任何消息上（包括`NLMSG_DONE`消息）设置`NLM_F_DUMP_INTR`标志。用户空间如果看到该标志，则应重试转储
自省
--------------

基本的自省能力通过访问在:ref:`res_fam`中报告的家庭对象来实现。用户可以查询有关通用Netlink家庭的信息，包括内核支持哪些操作以及内核理解哪些属性
家庭信息包括内核可以解析的最高属性ID，单独的命令（`CTRL_CMD_GETPOLICY`）提供了有关支持的属性的详细信息，包括内核接受的值范围
查询家庭信息在用户空间需要确保内核支持某项功能之前发出请求的情况下是有用的
.. _nlmsg_pid:

nlmsg_pid
---------

:c:member:`nlmsghdr.nlmsg_pid` 是Netlink中的地址等价物
它被称为端口ID，有时也称为进程ID，因为出于历史原因，如果应用程序没有选择（使用bind()绑定到）一个显式的端口ID，内核将自动为其分配等于其进程ID的ID（由getpid()系统调用报告）
与TCP/IP网络协议中的`bind()`语义类似，值为零表示“自动分配”，因此应用程序通常会将`:c:member:` `nlmsghdr.nlmsg_pid`字段初始化为`0`。这个字段仍然在某些罕见情况下使用，当内核需要发送单播通知时。用户空间的应用程序可以使用`bind()`将其套接字与特定的PID关联，然后将它的PID告知内核。这样，内核就可以与特定的用户空间进程通信。这种通信方式在UMH（用户模式助手）类似的场景中被利用，当内核需要触发用户空间处理或请求用户空间进行策略决策时。

### 组播通知

Netlink的一个优势是能够向用户空间发送事件通知。这是一种单向通信形式（内核 -> 用户），不涉及任何控制消息如`NLMSG_ERROR`或`NLMSG_DONE`。
例如，Generic Netlink家族本身定义了一组关于已注册家族的组播通知。当一个新的家族被添加时，订阅了这些通知的套接字将会收到以下消息：

```plaintext
struct nlmsghdr:
  __u32 nlmsg_len:      136
  __u16 nlmsg_type:     GENL_ID_CTRL
  __u16 nlmsg_flags:    0
  __u32 nlmsg_seq:      0
  __u32 nlmsg_pid:      0

struct genlmsghdr:
  __u8 cmd:             CTRL_CMD_NEWFAMILY
  __u8 version:         2
  __u16 reserved:       0

struct nlattr:
  __u16 nla_len:        10
  __u16 nla_type:       CTRL_ATTR_FAMILY_NAME
  char data:            test1\0

  (填充:)
  data:                 \0\0

struct nlattr:
  __u16 nla_len:        6
  __u16 nla_type:       CTRL_ATTR_FAMILY_ID
  __u16:                123  /* 我们关注的家族ID */

  (填充:)
  char data:            \0\0

struct nlattr:
  __u16 nla_len:        9
  __u16 nla_type:       CTRL_ATTR_FAMILY_VERSION
  __u16:                1

/* ... 等等，后续还有更多属性。 */
```

该通知包含的信息与对`CTRL_CMD_GETFAMILY`请求的响应相同。Netlink头信息大多为零且无关紧要。`:c:member:` `nlmsghdr.nlmsg_seq`可以是零或者由家族维护的单调递增的通知序列号。
为了接收通知，用户的套接字必须订阅相关的通知组。与家族ID类似，给定组播组的组ID也是动态的，并且可以在家族信息内部找到。`CTRL_ATTR_MCAST_GROUPS`属性包含嵌套的名字（`CTRL_ATTR_MCAST_GRP_NAME`）和ID（`CTRL_ATTR_MCAST_GRP_ID`）的组信息。
一旦已知组ID，通过一个`setsockopt()`调用将套接字添加到该组：

```c
unsigned int group_id;

/* ... 找到组ID ... */

setsockopt(fd, SOL_NETLINK, NETLINK_ADD_MEMBERSHIP,
           &group_id, sizeof(group_id));
```

现在该套接字将接收通知。
建议使用独立的套接字来接收通知和向内核发送请求。由于通知的异步特性，它们可能会与响应混合在一起，从而使消息处理变得更加困难。

缓冲区大小
-----------

Netlink 套接字是数据报套接字而不是流套接字，这意味着每个消息必须由单个`recv()`或`recvmsg()`系统调用完整地接收。如果用户提供的缓冲区太小，消息将会被截断，并且在结构`msghdr`中设置`MSG_TRUNC`标志（结构`msghdr`是`recvmsg()`系统调用的第二个参数，而不是Netlink头）。一旦消息被截断，剩余部分将被丢弃。

Netlink 预期用户缓冲区至少为8 kB或CPU架构的页面大小，取其中较大的值。然而，特定的Netlink家族可能需要更大的缓冲区。推荐使用32 kB的缓冲区以最有效地处理导出数据（较大的缓冲区可以容纳更多的导出对象，因此需要较少的`recvmsg()`调用）。

经典Netlink
===========

经典Netlink和通用Netlink的主要区别在于子系统的动态分配标识符和内省功能的可用性。理论上，这两种协议并没有显著差异，但在实践中，经典Netlink尝试了一些概念，这些概念在通用Netlink中被放弃了（实际上，它们通常只在一个子系统的某个角落中使用）。本节旨在解释这些概念中的几个，目的是让通用Netlink用户在阅读uAPI头文件时有信心忽略它们。

这里的大多数概念和示例都涉及`NETLINK_ROUTE`家族，它涵盖了Linux网络堆栈的大部分配置。关于该家族的真实文档应该有一章（或一本书）专门介绍。

家族
----

Netlink 将子系统称为家族。这是使用套接字和协议家族概念的遗留问题，这些概念是`NETLINK_ROUTE`中消息分用的一部分。
遗憾的是，每一层封装都喜欢将其携带的内容称为“家族”，这使得这个术语非常混乱：

1. AF_NETLINK 是一个真正的套接字协议族。
2. AF_NETLINK 的文档将消息中其自身头结构（struct nlmsghdr）之后的部分称为“家族头”。
3. 通用Netlink是AF_NETLINK的一个族（struct genlmsghdr 跟在 struct nlmsghdr 之后），但它也称其用户为“家族”。

请注意，通用Netlink的家族ID位于不同的“ID空间”中，并且与经典Netlink的协议编号重叠（例如，“NETLINK_CRYPTO”具有经典Netlink协议ID 21，而通用Netlink也会愉快地将其分配给其中一个家族）。

严格检查
-----------

``NETLINK_GET_STRICT_CHK`` 套接字选项启用了在 ``NETLINK_ROUTE`` 中的严格输入检查。这是因为历史上内核没有验证它不处理的结构字段。这使得后来开始使用这些字段变得不可能，因为应用程序可能会错误地初始化它们或根本不初始化。

``NETLINK_GET_STRICT_CHK`` 声明应用程序正确初始化了所有字段。它还选择验证消息中不包含尾随数据，并请求内核拒绝类型大于内核已知最大属性类型的属性。

``NETLINK_GET_STRICT_CHK`` 仅在 ``NETLINK_ROUTE`` 中使用。

未知属性
---------

历史上Netlink会忽略所有未知属性。这种想法是为了让应用程序无需探测内核支持哪些功能。应用程序可以发出更改状态的请求，并检查请求中的哪些部分被接受。

对于新的通用Netlink族和那些选择进行严格检查的族，这种情况不再适用。请参见 `enum netlink_validation` 以了解每种验证类型。

固定的元数据和结构
-------------------

经典Netlink广泛使用固定格式的结构来表示消息内的内容。消息通常会在 struct nlmsghdr 之后包含大量字段。此外，通常会在属性中放置多个成员的结构，而不是将每个成员拆分成单独的属性。

这导致了验证和扩展性的问题，因此对于新属性，使用二进制结构是被积极劝阻的。
请求类型
-------------

``NETLINK_ROUTE`` 将请求分为四种类型：``NEW``、``DEL``、``GET`` 和 ``SET``。每个对象可以处理这些请求中的全部或部分（这些对象包括网卡设备、路由、地址、队列管理器等）。请求类型由消息类型的最低两位定义，因此新对象的命令总是以 4 的步长分配。每个对象还会有其固定的元数据，这些元数据被所有请求类型共享（例如，netdev 请求使用 struct ifinfomsg，地址请求使用 struct ifaddrmsg，队列管理器请求使用 struct tcmsg）。
尽管其他协议和通用 Netlink 命令通常在消息名称中使用相同的动词（如 ``GET``、``SET``），但请求类型的概念并未得到广泛采用。

通知回声
-----------------

``NLM_F_ECHO`` 请求将因请求而产生的通知排队到请求套接字上。这有助于发现请求的影响。需要注意的是，此功能并非普遍实现。

其他请求类型特定标志
---------------------------------

经典 Netlink 在结构体 nlmsghdr 的 nlmsg_flags 字段的高字节中定义了各种针对其 ``GET``、``NEW`` 和 ``DEL`` 请求的标志。由于请求类型未被普遍化，因此这些请求类型特定的标志很少使用（并且对于新的家族被认为是过时的）。
对于 ``GET`` - ``NLM_F_ROOT`` 和 ``NLM_F_MATCH`` 结合成了 ``NLM_F_DUMP``，不再单独使用。``NLM_F_ATOMIC`` 从未使用过。
对于 ``DEL`` - ``NLM_F_NONREC`` 仅被 nftables 使用，而 ``NLM_F_BULK`` 仅被 FDB 某些操作使用。
``NEW`` 的标志在经典 Netlink 中最常用。不幸的是，其含义并不十分明确。以下描述基于对作者意图的最佳猜测，在实际中所有家族都以某种方式偏离了这一意图。``NLM_F_REPLACE`` 要求替换现有对象，如果没有匹配的对象，则操作应失败。
``NLM_F_EXCL`` 的语义正好相反，只有在对象已经存在的情况下才会成功。
``NLM_F_CREATE`` 要求如果对象不存在，则创建该对象，它可以与 ``NLM_F_REPLACE`` 和 ``NLM_F_EXCL`` 结合使用。

主 Netlink 用户 API 头文件中的注释说明如下：

   4.4BSD 添加		NLM_F_CREATE|NLM_F_EXCL
   4.4BSD 修改	NLM_F_REPLACE

   真正的修改		NLM_F_CREATE|NLM_F_REPLACE
   追加		NLM_F_CREATE
   检查		NLM_F_EXCL

这似乎表明这些标志早于请求类型。
最初使用 ``NLM_F_REPLACE`` 而不是 ``SET`` 命令。
仅使用 ``NLM_F_EXCL`` 而不使用 ``NLM_F_CREATE`` 用于检查对象是否存在而不创建它，这可能早于 ``GET`` 命令。
``NLM_F_APPEND`` 表示如果一个键可以关联多个对象（例如，一个路由可以有多个下一跳对象），则新对象应添加到列表中而不是替换整个列表。

用户 API 参考
==============

.. kernel-doc:: include/uapi/linux/netlink.h
