SocketCAN - 控制器局域网络
=============================

概述 / 什么是 SocketCAN
==============================

SocketCAN 包是为 Linux 实现 CAN 协议（控制器局域网络）的一种方法。CAN 是一种在网络技术领域得到广泛应用的技术，特别是在自动化、嵌入式设备及汽车行业中。虽然以前存在基于字符设备的其他 Linux 上的 CAN 实现，但 SocketCAN 利用了 Berkeley 套接字 API、Linux 网络栈，并将 CAN 设备驱动程序作为网络接口来实现。CAN 套接字 API 被设计得尽可能与 TCP/IP 协议相似，以便让熟悉网络编程的程序员能够轻松学会如何使用 CAN 套接字。
.. _socketcan-motivation:

动机 / 为何采用套接字 API
==============================

在 SocketCAN 之前已经有针对 Linux 的 CAN 实现，因此自然而然会有人问为什么还要启动另一个项目。大多数现有的实现都是作为特定 CAN 硬件的设备驱动程序提供的，它们基于字符设备并且提供的功能相对有限。通常，只有一个硬件特定的设备驱动程序提供了用于直接从/向控制器硬件发送和接收原始 CAN 帧的字符设备接口。帧队列和更高级别的传输协议（如 ISO-TP）必须在用户空间应用程序中实现。此外，大多数字符设备实现只支持一个进程一次打开该设备，类似于串行接口。更换 CAN 控制器需要使用另一个设备驱动程序，并且经常需要对应用的大部分部分进行适应新驱动程序 API 的更改。
SocketCAN 被设计来克服所有这些限制。一个新的协议家族被实现，它为用户空间应用程序提供了一个套接字接口，并建立在 Linux 网络层之上，使用户可以使用所有提供的队列功能。CAN 控制器硬件的设备驱动程序注册到 Linux 网络层作为一个网络设备，使得来自控制器的 CAN 帧可以传递给网络层并进一步传递给 CAN 协议家族模块，反之亦然。此外，协议家族模块提供了一个 API 供传输协议模块注册，这意味着任何数量的传输协议都可以动态地加载或卸载。实际上，仅凭 can 核心模块本身并不提供任何协议，并且在没有加载至少一个额外的协议模块的情况下无法使用。多个套接字可以在同一时间打开，可能在不同的或相同的协议模块上，并且它们可以在不同的或相同的 CAN ID 上监听/发送帧。多个套接字监听同一接口上的相同 CAN ID 的帧时，所有匹配的接收 CAN 帧都会被传送给它们。希望使用特定传输协议（例如 ISO-TP）进行通信的应用程序只需在打开套接字时选择该协议，然后就可以读取和写入应用程序数据流，无需处理 CAN-ID、帧等细节。

通过字符设备也可以提供类似的用户空间功能，但这会导致一些技术上不够优雅的解决方案：

* **复杂的使用方式：** 相对于通过 socket(2) 传递协议参数并使用 bind(2) 来选择 CAN 接口和 CAN ID，应用程序必须使用 ioctl(2) 执行所有这些操作。
* **代码重复：** 字符设备无法利用 Linux 网络队列代码，所以所有这些代码都必须为 CAN 网络复制。
* **抽象：** 在大多数现有字符设备实现中，特定 CAN 控制器的硬件特定设备驱动程序直接为应用程序提供了字符设备。
这种做法在 Unix 系统中无论是对于字符设备还是块设备来说都非常不寻常。例如，您不会为串行接口的某个 UART、计算机中的某个声音芯片、提供硬盘或磁带流设备访问的 SCSI 或 IDE 控制器拥有一个字符设备。相反，您会有抽象层，一方面为应用程序提供统一的字符或块设备接口，另一方面为硬件特定的设备驱动程序提供接口。这些抽象由子系统（如 tty 层、音频子系统或上述设备的 SCSI 和 IDE 子系统）提供。
实现 CAN 设备驱动程序最简单的方式是作为没有这种（完整）抽象层的字符设备，正如大多数现有驱动程序所做的一样。然而，正确的方式应该是添加这样一个包含所有功能的层，例如注册特定的 CAN ID、支持多个打开的文件描述符以及在它们之间（解）复用 CAN 帧、（复杂）的 CAN 帧队列，以及提供设备驱动程序注册的 API。但是，这样做之后，使用 Linux 内核提供的网络框架并不会更加困难，甚至可能更容易，而这正是 SocketCAN 所做的事情。
使用 Linux 内核的网络框架来实现 CAN 是自然且最合适的方式来为 Linux 实现 CAN。
SocketCAN 概念
=============

如 :ref:`socketcan-motivation` 中所述，SocketCAN 的主要目标是为用户空间应用程序提供一个基于 Linux 网络层的套接字接口。与广为人知的 TCP/IP 和以太网通信不同的是，CAN 总线是一种仅广播的介质，并没有像以太网那样的 MAC 层地址。CAN 标识符 (can_id) 用于 CAN 总线上的仲裁。因此，在总线上必须唯一地选择 CAN 标识符。在设计 CAN-ECU 网络时，将 CAN 标识符映射到由特定 ECU 发送。因此，CAN 标识符最好被视为一种源地址。

.. _socketcan-receive-lists:

接收列表
---------

多个应用程序通过网络透明访问导致的问题是，不同的应用程序可能对同一 CAN 网络接口的相同 CAN 标识符感兴趣。为此，SocketCAN 核心模块（实现了 CAN 协议家族）提供了多个高效的接收列表。例如，当用户空间应用程序打开一个 CAN RAW 套接字时，RAW 协议模块本身会从 SocketCAN 核心请求 (范围内的) CAN 标识符，这些标识符是由用户请求的。CAN 标识符的订阅和取消订阅可以针对特定的 CAN 接口或所有已知的 CAN 接口进行，使用 SocketCAN 核心为 CAN 协议模块提供的 can_rx_(un)register() 函数（参见 :ref:`socketcan-core-module`）。为了优化运行时的 CPU 使用率，接收列表被拆分成每个设备的多个特定列表，以匹配给定用例所需的过滤器复杂性。

.. _socketcan-local-loopback1:

发送帧的本地回环
------------------

正如其他网络概念所熟知的那样，数据交换的应用程序可以在相同的节点上运行，也可以在不同的节点上运行，而不需要任何改变（除了相应的地址信息）：

.. code::

    ___   ___   ___                   _______   ___
    | _ | | _ | | _ |                 | _   _ | | _ |
    ||A|| ||B|| ||C||                 ||A| |B|| ||C||
    |___| |___| |___|                 |_______| |___|
      |     |     |                       |       |
    -----------------(1)- CAN bus -(2)---------------

为了确保应用程序 A 在示例 (2) 中接收到的信息与它在示例 (1) 中接收到的信息相同，需要在适当的节点上进行某种形式的发送 CAN 帧的本地回环。
Linux 网络设备（默认情况下）只能处理媒体相关的帧的传输和接收。由于 CAN 总线上的仲裁，低优先级的 CAN 标识符的传输可能会被高优先级的 CAN 帧的接收延迟。为了反映节点上的正确 [#f1]_ 通信情况，成功传输后必须立即执行发送数据的回环。如果 CAN 网络接口由于某些原因无法执行回环，则 SocketCAN 核心可以作为回退解决方案执行此任务。有关详细信息，请参阅 :ref:`socketcan-local-loopback2`（推荐）。
回环功能默认启用，以反映 CAN 应用的标准网络行为。根据来自 RT-SocketCAN 组的一些请求，对于每个单独的套接字可选地禁用回环。请参阅 :ref:`socketcan-raw-sockets` 中的 CAN RAW 套接字的 sockopts。
.. [#f1] 当您在同一节点上运行诸如 'candump' 或 'cansniffer' 这样的分析工具时，您确实希望拥有这一点。

.. _socketcan-network-problem-notifications:

网络问题通知
-----------------

使用 CAN 总线可能会在物理层和媒体访问控制层产生多种问题。检测和记录这些较低层的问题对于 CAN 用户来说是一个至关重要的要求，以便识别物理收发器层的硬件问题以及由不同 ECU 引起的仲裁问题和错误帧。检测到的错误的发生对于诊断很重要，必须与确切的时间戳一起记录。为此，CAN 接口驱动程序可以生成所谓的错误消息帧，这些帧可以像其他 CAN 帧一样可选地传递给用户应用程序。每当检测到物理层或 MAC 层的错误（例如，由 CAN 控制器检测到），驱动程序都会创建一个合适的错误消息帧。用户应用程序可以使用常见的 CAN 过滤机制来请求错误消息帧。在此过滤定义中，可以选择（感兴趣的）错误类型。默认情况下禁用了错误消息的接收。CAN 错误消息帧的格式在 Linux 头文件 "include/uapi/linux/can/error.h" 中简要描述。
如何使用SocketCAN
==================

就像TCP/IP一样，首先需要为通过CAN网络进行通信打开一个套接字。由于SocketCAN实现了一个新的协议族，因此在调用socket(2)系统调用来创建套接字时，需要将PF_CAN作为第一个参数传递。目前有两种可选的CAN协议：原始套接字协议和广播管理器（BCM）。为了打开一个套接字，你可以这样写：

```c
s = socket(PF_CAN, SOCK_RAW, CAN_RAW);
```

以及：

```c
s = socket(PF_CAN, SOCK_DGRAM, CAN_BCM);
```

分别对应两种情况。成功创建套接字后，通常会使用bind(2)系统调用来绑定套接字到一个CAN接口（这与TCP/IP不同，因为地址形式不同——请参见 :ref:`socketcan-concept`）。在绑定（CAN_RAW）或连接（CAN_BCM）套接字之后，可以从/向套接字读取(2)/写入(2)，或者像平常一样使用send(2)、sendto(2)、sendmsg(2)及其recv*系列操作。下面还描述了一些CAN特定的套接字选项。

经典的CAN帧结构（即CAN 2.0B），CAN FD帧结构以及sockaddr结构在include/linux/can.h中定义：

```c
struct can_frame {
        canid_t can_id;  /* 32位CAN_ID + EFF/RTR/ERR标志 */
        union {
                /* CAN帧有效载荷长度（0 .. CAN_MAX_DLEN）字节
                 * 以前名为can_dlc，所以我们需要保留这个名字以支持遗留代码
                 */
                __u8 len;
                __u8 can_dlc; /* 过时 */
        };
        __u8    __pad;   /* 填充 */
        __u8    __res0;  /* 预留/填充 */
        __u8    len8_dlc; /* 可选DLC，用于8字节有效载荷长度（9 .. 15） */
        __u8    data[8] __attribute__((aligned(8)));
};
```

备注：len元素包含有效载荷长度（以字节为单位），应使用它而不是can_dlc。过时的can_dlc名称误导性地命名了，因为它总是包含了实际的有效载荷长度（以字节为单位），而不是所谓的“数据长度代码”（DLC）。
当从/向经典CAN网络设备传递原始DLC时，如果len元素是8（对于所有大于等于8的DLC值的实际有效载荷长度），len8_dlc元素可以包含9至15的值。
线性有效载荷数据[]对齐到64位边界允许用户定义自己的结构和联合体以便轻松访问CAN有效载荷。默认情况下，CAN总线上没有给定的字节序。对CAN_RAW套接字的read(2)系统调用将struct can_frame传输到用户空间。

sockaddr_can结构具有接口索引，类似于PF_PACKET套接字，也绑定到特定的接口：

```c
struct sockaddr_can {
        sa_family_t can_family;
        int         can_ifindex;
        union {
                /* 传输协议类地址信息（例如ISOTP） */
                struct { canid_t rx_id, tx_id; } tp;

                /* J1939地址信息 */
                struct {
                        /* 动态寻址时使用的8字节名称 */
                        __u64 name;

                        /* pgn:
                         * 8位: PS在PDU2情况下，否则为0
                         * 8位: PF
                         * 1位: DP
                         * 1位: 预留
                         */
                        __u32 pgn;

                        /* 1字节地址 */
                        __u8 addr;
                } j1939;

                /* 为未来的CAN协议地址信息预留 */
        } can_addr;
};
```

要确定接口索引，需要使用适当的ioctl()（以下是一个不包括错误检查的CAN_RAW套接字示例）：

```c
int s;
struct sockaddr_can addr;
struct ifreq ifr;

s = socket(PF_CAN, SOCK_RAW, CAN_RAW);

strcpy(ifr.ifr_name, "can0" );
ioctl(s, SIOCGIFINDEX, &ifr);

addr.can_family = AF_CAN;
addr.can_ifindex = ifr.ifr_ifindex;

bind(s, (struct sockaddr *)&addr, sizeof(addr));
```

要绑定到所有(!)CAN接口的套接字，接口索引必须为0（零）。在这种情况下，该套接字会从每一个启用的CAN接口接收CAN帧。为了确定来源CAN接口，可以使用recvfrom(2)系统调用代替read(2)。如果要发送到被绑定为“任意”接口的套接字，则需要使用sendto(2)来指定输出接口。

从已绑定的CAN_RAW套接字读取CAN帧（如上所述）包括读取struct can_frame：

```c
struct can_frame frame;

nbytes = read(s, &frame, sizeof(struct can_frame));

if (nbytes < 0) {
        perror("can raw socket read");
        return 1;
}

/* 检查完整性... */
if (nbytes < sizeof(struct can_frame)) {
        fprintf(stderr, "read: incomplete CAN frame\n");
        return 1;
}

/* 对收到的CAN帧做处理 */
```

写CAN帧可以通过类似的方式完成，使用write(2)系统调用：

```c
nbytes = write(s, &frame, sizeof(struct can_frame));
```

当CAN接口绑定到“任意”现有CAN接口（addr.can_ifindex = 0）时，如果需要关于来源CAN接口的信息，则建议使用recvfrom(2)：

```c
struct sockaddr_can addr;
struct ifreq ifr;
socklen_t len = sizeof(addr);
struct can_frame frame;

nbytes = recvfrom(s, &frame, sizeof(struct can_frame),
                  0, (struct sockaddr*)&addr, &len);

/* 获取收到的CAN帧的接口名称 */
ifr.ifr_ifindex = addr.can_ifindex;
ioctl(s, SIOCGIFNAME, &ifr);
printf("Received a CAN frame from interface %s", ifr.ifr_name);
```

为了在绑定为“任意”CAN接口的套接字上写CAN帧，需要明确指定输出接口：

```c
strcpy(ifr.ifr_name, "can0");
ioctl(s, SIOCGIFINDEX, &ifr);
addr.can_ifindex = ifr.ifr_ifindex;
addr.can_family  = AF_CAN;

nbytes = sendto(s, &frame, sizeof(struct can_frame),
                0, (struct sockaddr*)&addr, sizeof(addr));
```

在从套接字读取消息后，可以通过ioctl(2)调用来获取精确的时间戳：

```c
struct timeval tv;
ioctl(s, SIOCGSTAMP, &tv);
```

时间戳的分辨率是一微秒，并且在接收CAN帧时自动设置。

关于CAN FD（灵活数据率）支持的备注：

总的来说，CAN FD的处理与前面描述的例子非常相似。新的CAN FD兼容控制器支持在仲裁阶段和CAN FD帧的有效载荷阶段使用两种不同的比特率，并支持最多64字节的有效载荷。这种扩展的有效载荷长度破坏了严重依赖于固定8字节有效载荷的CAN帧（struct can_frame）的所有内核接口（ABI），例如CAN_RAW套接字。因此，例如，CAN_RAW套接字支持一个新的套接字选项CAN_RAW_FD_FRAMES，它将套接字切换到一种模式，允许同时处理CAN FD帧和经典CAN帧（见 :ref:`socketcan-rawfd`）。

struct canfd_frame在include/linux/can.h中定义：

```c
struct canfd_frame {
        canid_t can_id;  /* 32位CAN_ID + EFF/RTR/ERR标志 */
        __u8    len;     /* 帧有效载荷长度（0 .. 64）字节 */
        __u8    flags;   /* CAN FD的额外标志 */
        __u8    __res0;  /* 预留/填充 */
        __u8    __res1;  /* 预留/填充 */
        __u8    data[64] __attribute__((aligned(8)));
};
```

struct canfd_frame和现有的struct can_frame具有相同的偏移量的can_id、有效载荷长度和有效载荷数据。这使得可以非常类似地处理不同的结构。
当struct can_frame的内容被复制到struct canfd_frame中时，所有结构元素都可以直接使用——只有data[]被扩展。
在介绍 canfd_frame 结构体时发现，can_frame 结构体中的数据长度代码（DLC）被用作长度信息，因为长度和 DLC 在 0 到 8 的范围内具有一对一的映射关系。为了保持长度信息处理的简便性，canfd_frame.len 元素包含了一个从 0 到 64 的简单长度值。因此，canfd_frame.len 和 can_frame.len 是相等的，它们都包含了长度信息而不再是 DLC。

关于 CAN 和 CAN FD 设备的区别以及与总线相关的数据长度代码（DLC）的映射，请参阅 :ref:`socketcan-can-fd-driver`

两个 CAN(FD) 帧结构的长度定义了 CAN(FD) 网络接口的最大传输单元（MTU）以及 skbuff 数据长度。对于 CAN 特定的 MTU，在 include/linux/can.h 中指定了两种定义：

```C
#define CAN_MTU   (sizeof(struct can_frame))   == 16  // 经典 CAN 帧
#define CANFD_MTU (sizeof(struct canfd_frame)) == 72  // CAN FD 帧
```

返回的消息标志
------------------

在 RAW 或 BCM 套接字上使用系统调用 recvmsg(2) 时，msg->msg_flags 字段可能包含以下标志：

MSG_DONTROUTE:
当收到的帧是在本地主机上创建时设置。
MSG_CONFIRM:
当帧通过该套接字发送时设置。此标志可以解释为“传输确认”，如果 CAN 驱动支持驱动级的帧回送功能的话，参见 :ref:`socketcan-local-loopback1` 和 :ref:`socketcan-local-loopback2`。

（注：为了在 RAW 套接字上接收此类消息，必须设置 CAN_RAW_RECV_OWN_MSGS。）

### 带有 can_filters 的 RAW 协议套接字 (SOCK_RAW)

使用 CAN_RAW 套接字在很大程度上类似于常见的 CAN 字符设备访问方式。为了满足多用户 SocketCAN 方法提供的新可能性，在绑定 RAW 套接字时设定了一些合理的默认值：

- 过滤器设置为恰好一个接收所有内容的过滤器
- 套接字只接收有效的数据帧（即不接收错误消息帧）
- 发送的 CAN 帧的回环已启用（参见 :ref:`socketcan-local-loopback2`）
- 套接字不会接收其自身发送的帧（在回环模式下）

这些默认设置可以在绑定套接字之前或之后更改。为了使用 CAN_RAW 套接字选项的引用定义，请包含 <linux/can/raw.h>。

#### CAN_RAW_FILTER 原始套接字选项

使用 CAN_RAW 套接字接收 CAN 帧可以通过 CAN_RAW_FILTER 套接字选项定义 0 到 n 个过滤器来控制。CAN 过滤器结构在 include/linux/can.h 中定义如下：

```C
struct can_filter {
        canid_t can_id;
        canid_t can_mask;
};
```

当满足以下条件时，过滤器匹配：

```C
<received_can_id> & mask == can_id & mask
```

这类似于已知 CAN 控制器硬件过滤器的语义。如果在 can_filter 结构的 can_id 元素中设置了 CAN_INV_FILTER 位，则可以在这种语义中反转过滤器。与 CAN 控制器硬件过滤器不同的是，用户可以为每个打开的套接字单独设置 0 到 n 个接收过滤器：

```C
struct can_filter rfilter[2];

rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = CAN_SFF_MASK;
rfilter[1].can_id   = 0x200;
rfilter[1].can_mask = 0x700;

setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter));
```

要禁用选定 CAN_RAW 套接字上的 CAN 帧接收：

```C
setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, NULL, 0);
```

将过滤器设置为零过滤器是非常过时的做法，因为这样做会导致原始套接字丢弃接收到的 CAN 帧。但考虑到存在“仅发送”的使用情况，我们可以在内核中移除接收列表以节省一点（确实是非常少！）CPU 使用率。
CAN 滤波器使用优化

CAN 滤波器在接收 CAN 帧时按设备处理滤波器列表。为了减少遍历滤波器列表时需要执行的检查次数，CAN 核心提供了优化的滤波器处理方式，当滤波器订阅集中在单一 CAN ID 上时可以利用这一优化。对于可能的 2048 个标准 CAN 标识符（SFF），标识符用作索引来访问相应的订阅列表，无需进行额外检查。对于可能的 2^29 个扩展 CAN 标识符（EFF），使用 10 位 XOR 折叠作为哈希函数来检索 EFF 表索引。

为了从针对单个 CAN 标识符的优化滤波器中受益，需要在 `can_filter.mask` 中设置 `CAN_SFF_MASK` 或 `CAN_EFF_MASK`，同时设置 `CAN_EFF_FLAG` 和 `CAN_RTR_FLAG` 位。在 `can_filter.mask` 中设置 `CAN_EFF_FLAG` 位表明 SFF 还是 EFF CAN ID 的订阅是有区别的。例如：

```C
rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = CAN_SFF_MASK;
```

这样既可以允许 SFF CAN 帧（CAN ID 为 0x123）通过，也可以允许 EFF CAN 帧（CAN ID 为 0xXXXXX123）通过。为了仅过滤 0x123（SFF）和 0x12345678（EFF）CAN 标识符，需要定义如下滤波器以利用优化的滤波器：

```C
struct can_filter rfilter[2];

rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = (CAN_EFF_FLAG | CAN_RTR_FLAG | CAN_SFF_MASK);
rfilter[1].can_id   = 0x12345678 | CAN_EFF_FLAG;
rfilter[1].can_mask = (CAN_EFF_FLAG | CAN_RTR_FLAG | CAN_EFF_MASK);

setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter));
```

### RAW Socket 选项 CAN_RAW_ERR_FILTER

如 :ref:`socketcan-network-problem-notifications` 中所述，CAN 接口驱动程序可以生成所谓的错误消息帧，这些帧可选择性地以与其他 CAN 帧相同的方式传递给用户应用程序。可能的错误被分为不同的错误类别，可以通过适当的错误掩码进行过滤。要注册所有可能的错误条件，可以使用 `CAN_ERR_MASK` 作为错误掩码的值。错误掩码的值定义在 `linux/can/error.h` 中：

```C
can_err_mask_t err_mask = ( CAN_ERR_TX_TIMEOUT | CAN_ERR_BUSOFF );

setsockopt(s, SOL_CAN_RAW, CAN_RAW_ERR_FILTER,
           &err_mask, sizeof(err_mask));
```

### RAW Socket 选项 CAN_RAW_LOOPBACK

为了满足多用户需求，默认情况下启用了本地环回（详情见 :ref:`socketcan-local-loopback1`）。但在某些嵌入式使用案例中（例如只有一个应用程序使用 CAN 总线时），可以禁用此环回功能（每个套接字单独禁用）：

```C
int loopback = 0; /* 0 = 禁用, 1 = 启用（默认） */

setsockopt(s, SOL_CAN_RAW, CAN_RAW_LOOPBACK, &loopback, sizeof(loopback));
```

### RAW Socket 选项 CAN_RAW_RECV_OWN_MSGS

当本地环回启用时，所有发送的 CAN 帧都会循环回到注册了该 CAN ID 的打开的 CAN 套接字上，以满足多用户的需求。假设在同一套接字上接收自己发送的 CAN 帧通常是不需要的，因此默认情况下是禁用的。此默认行为可以根据需要更改：

```C
int recv_own_msgs = 1; /* 0 = 禁用（默认）, 1 = 启用 */

setsockopt(s, SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS,
           &recv_own_msgs, sizeof(recv_own_msgs));
```

请注意，接收套接字自己的 CAN 帧受与其它 CAN 帧相同的过滤规则限制（参见 :ref:`socketcan-rawfilter`）。

### RAW Socket 选项 CAN_RAW_FD_FRAMES

可以在 CAN_RAW 套接字中通过新的套接字选项 CAN_RAW_FD_FRAMES 启用 CAN FD 支持，默认情况下该选项处于关闭状态。如果 CAN_RAW 套接字不支持新的套接字选项（例如，在较旧的内核上），切换 CAN_RAW_FD_FRAMES 选项会返回错误 -ENOPROTOOPT。
一旦启用了 CAN_RAW_FD_FRAMES，应用程序就可以发送 CAN 帧和 CAN FD 帧。另一方面，当从套接字读取数据时，应用程序必须处理 CAN 帧和 CAN FD 帧：

```C
CAN_RAW_FD_FRAMES 启用: 允许 CAN_MTU 和 CANFD_MTU
CAN_RAW_FD_FRAMES 禁用: 只允许 CAN_MTU（默认）

示例:

```C
[记住: CANFD_MTU == sizeof(struct canfd_frame)]

struct canfd_frame cfd;

nbytes = read(s, &cfd, CANFD_MTU);

if (nbytes == CANFD_MTU) {
        printf("收到 CAN FD 帧，长度为 %d\n", cfd.len);
        /* cfd.flags 包含有效数据 */
} else if (nbytes == CAN_MTU) {
        printf("收到经典 CAN 帧，长度为 %d\n", cfd.len);
        /* cfd.flags 未定义 */
} else {
        fprintf(stderr, "读取: 无效的 CAN(FD) 帧\n");
        return 1;
}

/* 接收的数据内容独立于接收到的 MTU 大小处理 */

printf("can_id: %X 数据长度: %d 数据: ", cfd.can_id, cfd.len);
for (i = 0; i < cfd.len; i++)
        printf("%02X ", cfd.data[i]);
```

当使用大小为 CANFD_MTU 读取时，如果只接收到 CAN_MTU 字节，则说明读取的是经典 CAN 帧，并且将数据放入提供的 CAN FD 结构中。需要注意的是，`canfd_frame.flags` 数据字段在 `struct can_frame` 中未定义，因此它仅在 CANFD_MTU 大小的 CAN FD 帧中有效。

对于新 CAN 应用程序的实现提示：

为了构建一个 CAN FD 意识的应用程序，请使用 `struct canfd_frame` 作为基于 CAN_RAW 的应用程序的基本 CAN 数据结构。当应用程序在较旧的 Linux 内核上运行并且切换 CAN_RAW_FD_FRAMES 套接字选项返回错误时：没问题。您将收到经典 CAN 帧或 CAN FD 帧，并可以以相同的方式处理它们。
当向 CAN 设备发送数据时，请确保该设备能够处理 CAN FD 帧，这可以通过检查设备的最大传输单元（MTU）是否为 CANFD_MTU 来实现。
CAN 设备的 MTU 可以通过 SIOCGIFMTU ioctl() 系统调用来获取。
RAW 套接字选项 CAN_RAW_JOIN_FILTERS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN_RAW 套接字可以设置多个特定于 CAN 标识符的过滤器，这些过滤器在 af_can.c 的过滤处理中导致了多个过滤器。这些过滤器是相互独立的，因此在应用时形成了逻辑“或”（参见 :ref:`socketcan-rawfilter`）。
此套接字选项将给定的 CAN 过滤器进行组合，使得只有匹配所有给定 CAN 过滤器的 CAN 帧才会传递到用户空间。因此，应用的过滤器的语义被改变为逻辑“与”。
这对于由设置了 CAN_INV_FILTER 标志的过滤器组合而成的过滤器集尤其有用，以便从传入流量中排除单个 CAN ID 或 CAN ID 范围。
广播管理器协议套接字 (SOCK_DGRAM)
-----------------------------------------------

广播管理器协议提供了一个基于命令的配置接口，用于在内核空间中过滤和发送（例如周期性）CAN 消息。
接收过滤器可用于降低频繁消息的采样率；检测事件如消息内容变化、包长变化，并监控收到的消息的超时。
可以创建并修改 CAN 帧或 CAN 帧序列的周期性传输任务；消息内容和两种可能的发送间隔都可以在运行时更改。
BCM 套接字不是为了使用来自 CAN_RAW 套接字的 struct can_frame 发送单独的 CAN 帧。相反，定义了一种特殊的 BCM 配置消息。用于与广播管理器通信的基本 BCM 配置消息以及可用的操作定义在 linux/can/bcm.h 头文件中。BCM 消息包含一个带有命令（‘opcode’）的消息头，后面跟着零个或多个 CAN 帧。
广播管理器以同样的形式向用户空间发送响应：

.. code-block:: C

    struct bcm_msg_head {
            __u32 opcode;                   /* 命令 */
            __u32 flags;                    /* 特殊标志 */
            __u32 count;                    /* 使用 ival1 运行 'count' 次 */
            struct timeval ival1, ival2;    /* count 和随后的间隔 */
            canid_t can_id;                 /* 任务唯一的 can_id */
            __u32 nframes;                  /* 随后跟的 can_frame 数量 */
            struct can_frame frames[0];
    };

对齐的有效载荷 'frames' 使用了在 :ref:`socketcan-rawfd` 和 include/linux/can.h 中定义的相同基本 CAN 帧结构。所有从用户空间到广播管理器的消息都具有这种结构。
请注意，创建套接字后必须连接（而非绑定）CAN_BCM套接字（示例中未进行错误检查）：

.. 代码段:: C

    int s;
    struct sockaddr_can addr;
    struct ifreq ifr;

    s = socket(PF_CAN, SOCK_DGRAM, CAN_BCM);

    strcpy(ifr.ifr_name, "can0");
    ioctl(s, SIOCGIFINDEX, &ifr);

    addr.can_family = AF_CAN;
    addr.can_ifindex = ifr.ifr_ifindex;

    connect(s, (struct sockaddr *)&addr, sizeof(addr));

    (..)

广播管理器套接字能够同时处理任意数量的在途传输或接收过滤器。不同的收发任务通过每个BCM消息中的唯一can_id来区分。然而，为了在多个CAN接口上通信，建议使用额外的CAN_BCM套接字。当广播管理器套接字绑定到“任意”CAN接口（即接口索引设置为零）时，配置的接收过滤器适用于任何CAN接口，除非使用sendto()系统调用来覆盖“任意”CAN接口索引。如果使用recvfrom()而不是read()来检索BCM套接字消息，则原始CAN接口会在can_ifindex中提供。

广播管理器操作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

opcode定义了广播管理器需要执行的操作，或者详细描述了广播管理器对若干事件（包括用户请求）的响应。
发送操作（用户空间到广播管理器）:

TX_SETUP:
创建（周期性的）发送任务
TX_DELETE:
移除（周期性的）发送任务，仅需can_id
TX_READ:
读取can_id对应的（周期性）发送任务属性
TX_SEND:
发送一个CAN帧
发送响应（广播管理器到用户空间）:

TX_STATUS:
响应TX_READ请求（发送任务配置）
TX_EXPIRED:
当计数器在初始间隔'ival1'完成发送时的通知。要求在TX_SETUP时设置TX_COUNTEVT标志
接收操作（用户空间到广播管理器）:

RX_SETUP:
创建RX内容过滤器订阅
以下是对提供的英文文本的中文翻译：

### 接收命令（用户空间到广播管理器）:

**RX_DELETE:**
- 删除接收内容过滤订阅，只需要 `can_id`。

**RX_READ:**
- 读取针对 `can_id` 的接收内容过滤订阅的属性。

### 接收响应（广播管理器到用户空间）:

**RX_STATUS:**
- 对 `RX_READ` 请求的回复（过滤任务配置）。

**RX_TIMEOUT:**
- 周期性消息被检测为缺失（定时器 `ival1` 已过期）。

**RX_CHANGED:**
- 包含更新后的 CAN 帧的 BCM 消息（检测到内容变化）。
- 在接收到第一条消息或接收到修订后的 CAN 消息时发送。

### 广播管理器消息标志
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当向广播管理器发送消息时，“标志”元素可以包含以下标志定义，这些定义会影响行为：

**SETTIMER:**
- 设置 `ival1`、`ival2` 和 `count` 的值。

**STARTTIMER:**
- 使用 `ival1`、`ival2` 和 `count` 的当前值启动定时器。启动定时器的同时会发出一个 CAN 帧。

**TX_COUNTEVT:**
- 当 `count` 到达设定值时生成 `TX_EXPIRED` 消息。

**TX_ANNOUNCE:**
- 进程数据的变化会立即发出。

**TX_CP_CAN_ID:**
- 将消息头中的 `can_id` 复制到后续帧中的每一帧。这主要是为了简化使用。对于 TX 任务，消息头中的唯一 `can_id` 可能与后续 `struct can_frame` 中用于传输的 `can_id` 不同。

**RX_FILTER_ID:**
- 仅通过 `can_id` 进行过滤，不需要帧（`nframes`=0）。
### RX_CHECK_DLC:
DLC（数据长度码）的改变会导致 RX_CHANGED 事件的发生。

### RX_NO_AUTOTIMER:
防止自动启动超时监视器。

### RX_ANNOUNCE_RESUME:
如果在 RX_SETUP 时传递，并且发生了接收超时，当循环接收重启时，将生成一个 RX_CHANGED 消息。

### TX_RESET_MULTI_IDX:
重置多帧传输的索引。

### RX_RTR_FRAME:
对 RTR 请求发送回应（放置在 op->frames[0] 中）。

### CAN_FD_FRAME:
紧随 bcm_msg_head 的 CAN 帧是 struct canfd_frame 结构体。

### 广播管理器传输定时器
周期性传输配置最多可以使用两个间隔定时器。在这种情况下，BCM 会以一个间隔 'ival1' 发送一定数量的消息 ('count')，然后继续以另一个给定的间隔 'ival2' 发送消息。当只需要一个定时器时，'count' 被设置为零，仅使用 'ival2'。当设置了 SET_TIMER 和 START_TIMER 标志时，这些定时器会被激活。如果仅设置了 SET_TIMER，可以在运行时更改定时器值。

### 广播管理器消息序列传输
对于循环 TX 任务配置，最多可以按顺序传输 256 个 CAN 帧。BCM 消息头中的 'nframes' 元素提供了 CAN 帧的数量。定义数量的 CAN 帧作为数组添加到 TX_SETUP BCM 配置消息中：

```c
/* 创建一个结构体来设置四个 CAN 帧的序列 */
struct {
        struct bcm_msg_head msg_head;
        struct can_frame frame[4];
} mytxmsg;

//...
mytxmsg.msg_head.nframes = 4;
//...

write(s, &mytxmsg, sizeof(mytxmsg));
```

每次传输后，CAN 帧数组的索引都会增加，并在索引溢出时重置为零。
广播管理器接收过滤器定时器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在RX_SETUP时可以将定时器值ival1或ival2设置为非零值。当SET_TIMER标志被设置时，这些定时器会被启用：

ival1:
	当接收到的消息在指定时间内未再次接收到时发送RX_TIMEOUT。如果在RX_SETUP时设置了START_TIMER，则即使没有先前的CAN帧接收也会直接激活超时检测。
ival2:
	将接收消息速率限制到ival2的值。这对于减少应用中的消息很有用，尤其是当CAN帧内的信号是无状态的，即在ival2周期内可能发生的状态变化可能会丢失。

广播管理器多路复用消息接收过滤器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

为了过滤多路复用消息序列中的内容变化，可以在RX_SETUP配置消息中传递一个包含多个CAN帧的数组。第一个CAN帧的数据字节包含相关位掩码，后续的CAN帧必须与接收到的CAN帧匹配这些位。
如果其中一个后续CAN帧与该帧数据中的位匹配，则标记这些位以比较之前接收到的内容。
最多可以向TX_SETUP BCM配置消息添加257个CAN帧（多路复用滤波位掩码CAN帧加上256个CAN滤波器）：

.. code-block:: C

    /* 通常用于清空CAN帧数据[] - 注意字节序问题！ */
    #define U64_DATA(p) (*(unsigned long long*)(p)->data)

    struct {
            struct bcm_msg_head msg_head;
            struct can_frame frame[5];
    } msg;

    msg.msg_head.opcode  = RX_SETUP;
    msg.msg_head.can_id  = 0x42;
    msg.msg_head.flags   = 0;
    msg.msg_head.nframes = 5;
    U64_DATA(&msg.frame[0]) = 0xFF00000000000000ULL; /* 多路复用掩码 */
    U64_DATA(&msg.frame[1]) = 0x01000000000000FFULL; /* 数据掩码 (多路复用 0x01) */
    U64_DATA(&msg.frame[2]) = 0x0200FFFF000000FFULL; /* 数据掩码 (多路复用 0x02) */
    U64_DATA(&msg.frame[3]) = 0x330000FFFFFF0003ULL; /* 数据掩码 (多路复用 0x33) */
    U64_DATA(&msg.frame[4]) = 0x4F07FC0FF0000000ULL; /* 数据掩码 (多路复用 0x4F) */

    write(s, &msg, sizeof(msg));

广播管理器CAN FD支持
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN_BCM的编程API依赖于结构体can_frame，该结构体直接位于bcm_msg_head结构之后。为了遵循CAN FD帧的这个模式，在bcm_msg_head的标志中新增了一个'CAN_FD_FRAME'标志，表示bcm_msg_head之后的连接的CAN帧结构定义为struct canfd_frame：

.. code-block:: C

    struct {
            struct bcm_msg_head msg_head;
            struct canfd_frame frame[5];
    } msg;

    msg.msg_head.opcode  = RX_SETUP;
    msg.msg_head.can_id  = 0x42;
    msg.msg_head.flags   = CAN_FD_FRAME;
    msg.msg_head.nframes = 5;
    (..)

使用CAN FD帧进行多路复用过滤时，多路复用掩码仍然期望出现在struct canfd_frame数据部分的第一个64位中。

连接传输协议 (SOCK_SEQPACKET)
----------------------------------------------

(待撰写)

非连接传输协议 (SOCK_DGRAM)
----------------------------------------------

(待撰写)

.. _socketcan-core-module:

SocketCAN核心模块
=====================

SocketCAN核心模块实现了协议族PF_CAN。CAN协议模块由核心模块在运行时加载。核心模块为CAN协议模块提供了订阅所需的CAN ID的接口（参见 :ref:`socketcan-receive-lists`）
can.ko模块参数
--------------------

- **stats_timer**:
  为了计算SocketCAN核心统计信息（例如当前/最大每秒帧数），此1秒定时器默认在can.ko模块启动时被调用。可以通过在模块命令行上使用stattimer=0来禁用此定时器。
- **debug**:
  （自SocketCAN SVN r546以来已移除）

procfs内容
--------------

如 :ref:`socketcan-receive-lists` 中所述，SocketCAN核心使用多个过滤列表将接收到的CAN帧交付给CAN协议模块。这些接收列表、它们的过滤器和过滤匹配次数可以在相应的接收列表中检查。所有条目都包含设备和协议模块标识符：

    foo@bar:~$ cat /proc/net/can/rcvlist_all

    接收列表 'rx_all':
      (vcan3: 无条目)
      (vcan2: 无条目)
      (vcan1: 无条目)
      设备   can_id   can_mask  function  userdata   匹配次数  标识
       vcan0     000    00000000  f88e6370  f6c6f400         0  raw
      (任何: 无条目)

在这个例子中，一个应用程序请求从vcan0接收任何CAN流量：

    rcvlist_all - 无过滤条目的列表（不执行过滤操作）
    rcvlist_eff - 单一扩展帧 (EFF) 条目的列表
    rcvlist_err - 错误消息帧掩码的列表
    rcvlist_fil - 掩码/值过滤器的列表
    rcvlist_inv - 掩码/值过滤器的列表（逆向语义）
    rcvlist_sff - 单一标准帧 (SFF) 条目的列表

/proc/net/can中的其他procfs文件：

    stats       - SocketCAN核心统计信息（接收/发送帧、匹配比率等）
    reset_stats - 手动重置统计信息
    version     - 显示SocketCAN核心和ABI版本（在Linux 5.10中移除）

编写自己的CAN协议模块
--------------------------------

要在协议族PF_CAN中实现一个新的协议，需要在include/linux/can.h中定义一个新的协议。
使用SocketCAN核心的原型和定义可以通过包含include/linux/can/core.h获得。
除了注册 CAN 协议和 CAN 设备通知链的功能之外，还有一些功能可以订阅 CAN 接口接收到的 CAN 帧以及发送 CAN 帧：

    can_rx_register   - 从特定接口订阅 CAN 帧
    can_rx_unregister - 取消从特定接口订阅 CAN 帧
    can_send          - 发送一个 CAN 帧（可选地带有本地回环）

详细信息请参阅 net/can/af_can.c 中的 kerneldoc 文档或 net/can/raw.c 或 net/can/bcm.c 的源代码。
CAN 网络驱动程序
==================

编写 CAN 网络设备驱动程序比编写 CAN 字符设备驱动程序要容易得多。与已知的其他网络设备驱动程序类似，你主要需要处理以下内容：

- TX：将 CAN 帧从套接字缓冲区发送到 CAN 控制器
- RX：将 CAN 帧从 CAN 控制器接收至套接字缓冲区

详情请参见 Documentation/networking/netdevices.rst 。编写 CAN 网络设备驱动程序的不同之处如下所述。

通用设置
---------

```C
    dev->type  = ARPHRD_CAN; /* 网络设备硬件类型 */
    dev->flags = IFF_NOARP;  /* CAN 没有 ARP */

    dev->mtu = CAN_MTU; /* sizeof(struct can_frame) -> 经典 CAN 接口 */

    或者，如果控制器支持 CAN 的灵活数据速率：
    dev->mtu = CANFD_MTU; /* sizeof(struct canfd_frame) -> CAN FD 接口 */
```

结构体 `can_frame` 或 `canfd_frame` 是协议家族 PF_CAN 中每个套接字缓冲区 (skbuff) 的有效载荷。
_局部回环发送帧_

发送帧的局部回环
-----------------

如 :ref:`socketcan-local-loopback1` 所述，CAN 网络设备驱动程序应该支持类似 tty 设备本地回显的局部回环功能。在这种情况下，必须设置驱动标志 IFF_ECHO 以防止 PF_CAN 核心作为备选方案局部回显发送的帧 (即回环)：

```C
    dev->flags = (IFF_NOARP | IFF_ECHO);
```

CAN 控制器硬件过滤器
-------------------

为了减轻深度嵌入式系统上的中断负载，一些 CAN 控制器支持对 CAN ID 或 CAN ID 范围进行过滤。这些硬件过滤器的能力因控制器而异，在多用户网络环境中实现起来并不现实。在非常专用的应用场景中使用特定于控制器的硬件过滤器可能有意义，因为驱动程序级别的过滤器会影响多用户系统中的所有用户。PF_CAN 核心中高效的过滤集允许为每个套接字单独设置不同的多个过滤器。因此，使用硬件过滤器归类于“深度嵌入式系统的手工调优”。作者自 2002 年起在重负载下运行 MPC603e @133MHz 和四个 SJA1000 CAN 控制器，没有遇到任何问题。
可切换终端电阻
------------------

CAN 总线要求差分对之间具有特定的阻抗，通常由总线最远节点上的两个 120 欧姆电阻提供。一些 CAN 控制器支持激活/去激活终端电阻以提供正确的阻抗。查询可用的电阻值：

```
$ ip -details link show can0
..
termination 120 [ 0, 120 ]
```

激活终端电阻：

```
$ ip link set dev can0 type can termination 120
```

去激活终端电阻：

```
$ ip link set dev can0 type can termination 0
```

为了支持 CAN 控制器的终端电阻，可以在控制器的 `struct can_priv` 中实现：

    termination_const
    termination_const_cnt
    do_set_termination

或者通过设备树条目添加 GPIO 控制，这些条目来自 Documentation/devicetree/bindings/net/can/can-controller.yaml。
虚拟 CAN 驱动程序 (vcan)
--------------------------

类似于网络回环设备，vcan 提供了一个虚拟的本地 CAN 接口。CAN 上的一个完整合格地址由以下部分组成：

- 一个唯一的 CAN 标识符 (CAN ID)
- 此 CAN ID 所传输的 CAN 总线 (例如 can0)

因此，在常见的使用案例中，通常需要不止一个虚拟 CAN 接口。
虚拟 CAN 接口允许在没有真实的 CAN 控制器硬件的情况下发送和接收 CAN 帧。虚拟 CAN 网络设备通常被命名为 'vcanX'，例如 vcan0、vcan1、vcan2 等。如果作为模块编译，则虚拟 CAN 驱动程序模块称为 vcan.ko。

自 Linux 内核版本 2.6.24 起，vcan 驱动支持内核的 netlink 接口来创建 vcan 网络设备。使用 ip(8) 工具可以管理 vcan 网络设备的创建和删除：

- 创建一个虚拟 CAN 网络接口：
        $ ip link add type vcan

- 使用特定名称 'vcan42' 创建一个虚拟 CAN 网络接口：
        $ ip link add dev vcan42 type vcan

- 删除一个（虚拟 CAN）网络接口 'vcan42'：
        $ ip link del vcan42

### CAN 网络设备驱动接口

CAN 网络设备驱动接口提供了一个通用的接口来设置、配置和监控 CAN 网络设备。用户可以通过 netlink 接口使用 "IPROUTE2" 实用套件中的 "ip" 程序来配置 CAN 设备，如设置比特定时参数等。下面的章节简要描述了如何使用它。此外，该接口使用了一种公共的数据结构，并导出了一系列公共函数，所有真实的 CAN 网络设备驱动都应该使用它们。请参阅 SJA1000 或 MSCAN 驱动以了解如何使用这些功能。该模块名为 can-dev.ko。

#### Netlink 接口设置/获取设备属性

CAN 设备必须通过 netlink 接口进行配置。支持的 netlink 消息类型在 "include/linux/can/netlink.h" 中定义并进行了简要描述。对于 "IPROUTE2" 实用套件中的 "ip" 程序提供了 CAN 链路支持，并可按照以下方式使用：

设置 CAN 设备属性：

    $ ip link set can0 type can help
    用法：ip link set DEVICE type can
        [ bitrate BITRATE [ sample-point SAMPLE-POINT] ] |
        [ tq TQ prop-seg PROP_SEG phase-seg1 PHASE-SEG1
          phase-seg2 PHASE-SEG2 [ sjw SJW ] ]

        [ dbitrate BITRATE [ dsample-point SAMPLE-POINT] ] |
        [ dtq TQ dprop-seg PROP_SEG dphase-seg1 PHASE-SEG1
          dphase-seg2 PHASE-SEG2 [ dsjw SJW ] ]

        [ loopback { on | off } ]
        [ listen-only { on | off } ]
        [ triple-sampling { on | off } ]
        [ one-shot { on | off } ]
        [ berr-reporting { on | off } ]
        [ fd { on | off } ]
        [ fd-non-iso { on | off } ]
        [ presume-ack { on | off } ]
        [ cc-len8-dlc { on | off } ]

        [ restart-ms TIME-MS ]
        [ restart ]

    其中：BITRATE       := { 1..1000000 }
          SAMPLE-POINT  := { 0.000..0.999 }
          TQ            := { NUMBER }
          PROP-SEG      := { 1..8 }
          PHASE-SEG1    := { 1..8 }
          PHASE-SEG2    := { 1..8 }
          SJW           := { 1..4 }
          RESTART-MS    := { 0 | NUMBER }

显示 CAN 设备详细信息和统计信息：

    $ ip -details -statistics link show can0
    2: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UP qlen 10
      link/can
      can <TRIPLE-SAMPLING> state ERROR-ACTIVE restart-ms 100
      bitrate 125000 sample_point 0.875
      tq 125 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1
      sja1000: tseg1 1..16 tseg2 1..8 sjw 1..4 brp 1..64 brp-inc 1
      clock 8000000
      re-started bus-errors arbit-lost error-warn error-pass bus-off
      41         17457      0          41         42         41
      RX: bytes  packets  errors  dropped overrun mcast
      140859     17608    17457   0       0       0
      TX: bytes  packets  errors  dropped carrier collsns
      861        112      0       41      0       0

更多关于上述输出的信息：

"<TRIPLE-SAMPLING>"
    显示选定的 CAN 控制器模式列表：LOOPBACK、LISTEN-ONLY 或 TRIPLE-SAMPLING
"state ERROR-ACTIVE"
    当前的 CAN 控制器状态：“ERROR-ACTIVE”、“ERROR-WARNING”、“ERROR-PASSIVE”、“BUS-OFF”或“STOPPED”

"restart-ms 100"
    自动重启延迟时间。如果设置为非零值，在发生总线关闭条件后，将在指定的延迟时间内自动触发 CAN 控制器重启（以毫秒为单位）。默认情况下是关闭的。
"bitrate 125000 sample-point 0.875"
    显示实际比特率（bits/sec）和采样点（范围 0.000~0.999）。如果内核启用了比特定时参数计算（CONFIG_CAN_CALC_BITTIMING=y），则可以通过设置 "bitrate" 参数来定义比特定时。
    可选地，还可以指定 "sample-point"。默认值为 0.000，假设采用 CIA 推荐的采样点。
"tq 125 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1"
    显示时间量子（ns）、传播段、相位缓冲段 1 和 2 以及同步跳跃宽度（以 tq 单位）。它们允许以博世 CAN 2.0 规范提出的硬件独立格式定义 CAN 比特定时（参见 http://www.semiconductors.bosch.de/pdf/can2spec.pdf 第 8 章）。
"sja1000: tseg1 1..16 tseg2 1..8 sjw 1..4 brp 1..64 brp-inc 1 clock 8000000"
    显示 CAN 控制器（这里是 "sja1000"）的比特定时常数。时间段 1 和 2 的最小值和最大值、同步跳跃宽度（以 tq 单位）、比特率预标度器以及 CAN 系统时钟频率（Hz）。
    这些常数可用于用户空间中用户定义（非标准）的比特定时计算算法。
这段文档主要描述了CAN（Controller Area Network）网络设备的配置和使用细节，下面是对文档内容的中文翻译：

### 重新启动、总线错误、仲裁丢失、错误警告、错误被动及总线关闭状态
显示重启次数、总线错误以及仲裁丢失错误的数量，并且展示了状态变化到错误警告状态、错误被动状态及总线关闭状态。接收溢出错误被列在标准网络统计信息中的“溢出”字段中。

### 设置CAN位定时
CAN位定时参数总是可以以硬件无关的格式定义，如Bosch CAN 2.0规范中所建议的那样，指定参数“tq”、“prop_seg”、“phase_seg1”、“phase_seg2”和“sjw”：
```
$ ip link set canX type can tq 125 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1
```
如果内核选项`CONFIG_CAN_CALC_BITTIMING`被启用，则当通过参数“bitrate”指定比特率时，将计算CIA推荐的CAN位定时参数：
```
$ ip link set canX type can bitrate 125000
```
需要注意的是，这适用于大多数常见的CAN控制器与标准比特率，但可能对特殊比特率或CAN系统时钟频率不适用。禁用`CONFIG_CAN_CALC_BITTIMING`可以节省一些空间，并允许用户空间工具完全确定并设置位定时参数。为此目的可以使用特定于CAN控制器的位定时常量，这些常量可以通过以下命令列出：
```
$ ip -details link show can0
..
sja1000: clock 8000000 tseg1 1..16 tseg2 1..8 sjw 1..4 brp 1..64 brp-inc 1
```

### 启动和停止CAN网络设备
CAN网络设备可以像通常那样通过命令“ifconfig canX up/down”或“ip link set canX up/down”启动或停止。需要注意的是，在启动真实的CAN设备之前必须定义合适的位定时参数，以避免默认设置导致的问题：
```
$ ip link set canX up type can bitrate 125000
```
如果CAN总线上发生了太多错误，设备可能会进入“总线关闭”状态。此时不再接收或发送任何消息。可以通过设置“restart-ms”为非零值来启用自动总线恢复，例如：
```
$ ip link set canX type can restart-ms 100
```
或者，应用程序可以通过监控CAN错误消息帧来检测“总线关闭”条件，并在适当的时候执行重启操作：
```
$ ip link set canX type can restart
```
需要注意的是，重启也会产生一个CAN错误消息帧（参见[socketcan网络问题通知](#socketcan-network-problem-notifications))。

### CAN FD（灵活数据速率）驱动支持
CAN FD兼容的CAN控制器支持在CAN FD帧的仲裁阶段和有效载荷阶段使用两种不同的比特率。因此，需要指定第二个位定时才能启用CAN FD比特率。此外，CAN FD兼容的CAN控制器支持最多64字节的有效载荷。这种长度在用户空间应用和Linux网络层内部表示为一个简单的值从0到64，而不是CAN“数据长度代码”。数据长度代码在经典CAN帧中无论如何都是与有效载荷长度一对一映射的。有效载荷长度与总线相关的DLC（Data Length Code）之间的映射只在CAN驱动程序内部进行，最好使用辅助函数`can_fd_dlc2len()`和`can_fd_len2dlc()`。
CAN网络设备驱动程序的能力可以通过网络设备的最大传输单元(MTU)来区分：
- MTU = 16 (CAN_MTU) => `struct can_frame` 的大小 => 经典CAN设备
- MTU = 72 (CANFD_MTU) => `struct canfd_frame` 的大小 => CAN FD兼容设备
CAN设备的MTU可以通过SIOCGIFMTU ioctl()系统调用来获取。
请注意，CAN FD兼容设备也可以处理并发送经典CAN帧。
当配置CAN FD兼容的CAN控制器时，需要额外设置一个‘数据’比特率。这个用于CAN FD帧数据阶段的比特率至少要等于为仲裁阶段配置的比特率。第二个比特率的设置方式类似于第一个比特率，但是比特率设置关键字以'd'开头，例如dbitrate、dsample-point、dsjw或dtq等类似设置。当设置了数据比特率后，在配置过程中可以指定控制器选项"fd on"以在CAN控制器中启用CAN FD模式。此控制器选项还会将设备MTU切换为72 (CANFD_MTU)。
首个CAN FD规格作为白皮书在2012年国际CAN会议上提出，为了数据完整性原因需要改进。
因此，今天需要区分两种CAN FD实现：

- 符合ISO标准：ISO 11898-1:2015的CAN FD实现（默认）
- 不符合ISO标准：遵循2012年白皮书的CAN FD实现

最终存在三种类型的CAN FD控制器：

1. 符合ISO标准（固定）
2. 不符合ISO标准（固定，如m_can.c中的M_CAN IP core v3.0.1）
3. 符合ISO/不符合ISO的CAN FD控制器（可切换，如PEAK PCAN-USB FD）

当前的ISO/非ISO模式由CAN控制器驱动程序通过netlink宣布，并由'ip'工具显示（控制器选项FD-NON-ISO）。对于可切换的CAN FD控制器，可以通过设置'fd-non-iso {on|off}'来更改ISO/非ISO模式。
配置示例：500 kbit/s仲裁比特率和4 Mbit/s数据比特率：

    $ ip link set can0 up type can bitrate 500000 sample-point 0.75 \
                                   dbitrate 4000000 dsample-point 0.8 fd on
    $ ip -details link show can0
    5: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 72 qdisc pfifo_fast state UNKNOWN \
             mode DEFAULT group default qlen 10
    link/can  promiscuity 0
    can <FD> state ERROR-ACTIVE (berr-counter tx 0 rx 0) restart-ms 0
          bitrate 500000 sample-point 0.750
          tq 50 prop-seg 14 phase-seg1 15 phase-seg2 10 sjw 1
          pcan_usb_pro_fd: tseg1 1..64 tseg2 1..16 sjw 1..16 brp 1..1024 \
          brp-inc 1
          dbitrate 4000000 dsample-point 0.800
          dtq 12 dprop-seg 7 dphase-seg1 8 dphase-seg2 4 dsjw 1
          pcan_usb_pro_fd: dtseg1 1..16 dtseg2 1..8 dsjw 1..4 dbrp 1..1024 \
          dbrp-inc 1
          clock 80000000

当添加'on'到'switchable CAN FD adapter'的'fd-non-iso'时的示例：

   can <FD,FD-NON-ISO> state ERROR-ACTIVE (berr-counter tx 0 rx 0) restart-ms 0

支持的CAN硬件
--------------

请检查"drivers/net/can"目录下的"Kconfig"文件以获取支持的CAN硬件列表。在SocketCAN项目网站上（参见 :ref:`socketcan-resources`）可能有其他驱动程序可用，也包括较旧内核版本的驱动。
.. _socketcan-resources:

SocketCAN资源
==============

Linux CAN / SocketCAN项目的资源（项目站点/邮件列表）在Linux源代码树中的MAINTAINERS文件中有引用。搜索关键词CAN NETWORK [LAYERS|DRIVERS]。
致谢
=====

- Oliver Hartkopp（PF_CAN核心、过滤器、驱动程序、bcm、SJA1000驱动程序）
- Urs Thuermann（PF_CAN核心、内核集成、套接字接口、raw、vcan）
- Jan Kizka（RT-SocketCAN核心、Socket-API协调）
- Wolfgang Grandegger（RT-SocketCAN核心与驱动程序、Raw Socket-API审查、CAN设备驱动程序接口、MSCAN驱动程序）
- Robert Schwebel（设计审查、PTXdist集成）
- Marc Kleine-Budde（设计审查、Kernel 2.6清理、驱动程序）
- Benedikt Spranger（审查）
- Thomas Gleixner（LKML审查、编码风格、发布提示）
- Andrey Volkov（内核子树结构、ioctl、MSCAN驱动程序）
- Matthias Brukner（2003年第二季度首个SJA1000 CAN网络设备实现）
- Klaus Hitschler（PEAK驱动程序集成）
- Uwe Koppe（使用PF_PACKET方法的CAN网络设备）
- Michael Schulze（驱动层环回要求、RT CAN驱动程序审查）
- Pavel Pisa（位定时计算）
- Sascha Hauer（SJA1000平台驱动程序）
- Sebastian Haas（SJA1000 EMS PCI驱动程序）
- Markus Plessing（SJA1000 EMS PCI驱动程序）
- Per Dalen（SJA1000 Kvaser PCI驱动程序）
- Sam Ravnborg（审查、编码风格、kbuild帮助）
