SocketCAN - 控制器局域网络
===================================

概述 / 什么是SocketCAN
============================

socketcan包是Linux上CAN协议（控制器局域网络）的实现。CAN是一种广泛应用于自动化、嵌入式设备和汽车领域的网络技术。虽然之前有基于字符设备的其他Linux上的CAN实现，但SocketCAN使用了Berkeley套接字API、Linux网络堆栈，并将CAN设备驱动程序实现为网络接口。CAN套接字API设计得尽可能类似于TCP/IP协议，以便让熟悉网络编程的程序员能够轻松学习如何使用CAN套接字。
.. _socketcan-motivation:

动机 / 为什么使用套接字API
=====================================

在SocketCAN之前已经有其他Linux上的CAN实现，因此人们会问，为什么我们还要启动另一个项目。大多数现有的实现都是某个CAN硬件的设备驱动程序，它们基于字符设备并且提供的功能相对较少。通常，只有一个特定于硬件的设备驱动程序提供用于发送和接收原始CAN帧的字符设备接口，直接与控制器硬件交互。队列化帧和更高层次的传输协议（如ISO-TP）需要在用户空间应用程序中实现。此外，大多数字符设备实现只支持一次打开一个进程，类似于串行接口。更换CAN控制器需要使用另一个设备驱动程序，并且通常需要对应用程序的大部分类进行适应新的驱动程序API。

SocketCAN的设计目的是克服所有这些限制。一个新的协议家族被实现，它为用户空间应用程序提供了套接字接口，并且构建在Linux网络层之上，使能够使用所有提供的队列功能。CAN控制器硬件的设备驱动程序将其自身注册到Linux网络层作为网络设备，以便CAN帧可以从控制器传递到网络层并进而传递到CAN协议家族模块，反之亦然。此外，协议家族模块还提供了传输协议模块注册的API，使得可以动态加载或卸载任意数量的传输协议。事实上，仅凭can核心模块本身不提供任何协议，并且在没有加载至少一个附加协议模块的情况下无法使用。多个套接字可以同时打开，针对不同的或相同的协议模块，并且可以在不同的或相同的CAN ID上监听/发送帧。几个在同一接口上监听相同CAN ID帧的套接字都会收到相同的匹配CAN帧。希望使用特定传输协议（例如ISO-TP）通信的应用程序只需在打开套接字时选择该协议，然后就可以读取和写入应用程序数据流，而无需处理CAN-ID、帧等。

类似的从用户空间可见的功能也可以通过字符设备来提供，但这将导致技术上不够优雅的解决方案，原因如下：

* **复杂的使用方式：** 相比于通过socket(2)传递协议参数并使用bind(2)选择CAN接口和CAN ID，应用程序必须使用ioctl(2)完成所有这些操作。
* **代码重复：** 字符设备无法利用Linux网络队列代码，所以所有这些代码都需要为CAN网络复制。
* **抽象：** 在大多数现有字符设备实现中，CAN控制器的特定硬件设备驱动程序直接为应用程序提供字符设备以供其使用。
这在Unix系统中对于字符设备和块设备来说都是不寻常的。例如，您不会为串行接口的某个UART、计算机中的某个声卡、提供硬盘或磁带流设备访问的SCSI或IDE控制器提供一个字符设备。相反，您会有抽象层为应用程序提供统一的字符或块设备接口，并为特定硬件设备驱动程序提供接口。这些抽象由子系统如tty层、音频子系统或上述设备的SCSI和IDE子系统提供。

实现CAN设备驱动程序的最简单方法是作为字符设备而不带有这样的（完整的）抽象层，正如大多数现有驱动程序所做的那样。然而，正确的方法应该是添加这样一个具有所有功能的层，如注册特定的CAN ID、支持多个打开的文件描述符并在它们之间（解）复用CAN帧、（高级）队列化CAN帧，并提供设备驱动程序注册的API。但是，这样之后，使用Linux内核提供的网络框架并不会更困难，甚至可能更容易，这就是SocketCAN所做的事情。

使用Linux内核的网络框架只是实现Linux上CAN的自然且最合适的方式。
SocketCAN 概念
=============

如 :ref:`socketcan-motivation` 中所述，SocketCAN 的主要目标是为用户空间应用程序提供一个基于 Linux 网络层的套接字接口。与常见的 TCP/IP 和以太网网络不同，CAN 总线是一个仅广播的介质，并没有像以太网那样的 MAC 层地址。CAN 标识符（can_id）用于 CAN 总线上的仲裁。因此，CAN 标识符必须在总线上唯一选择。在设计 CAN-ECU 网络时，CAN 标识符会被映射到由特定 ECU 发送。因此，CAN 标识符可以最好地被视为一种源地址。

.. _socketcan-receive-lists:

接收列表
---------

多个应用程序通过网络透明访问会导致一个问题：不同的应用程序可能对同一 CAN 网络接口上的相同 CAN 标识符感兴趣。为此，SocketCAN 核心模块（实现了 CAN 协议族）提供了多个高效的接收列表。例如，当用户空间应用程序打开一个 CAN RAW 套接字时，RAW 协议模块本身会从 SocketCAN 核心请求用户所需的 CAN 标识符范围。CAN 标识符的订阅和取消订阅可以通过 can_rx_(un)register() 函数针对特定的 CAN 接口或所有已知的 CAN 接口进行（这些函数由 SocketCAN 核心提供给 CAN 协议模块）。为了优化运行时的 CPU 使用率，接收列表被拆分成每个设备的多个具体列表，以匹配给定用例所请求的过滤器复杂度。

.. _socketcan-local-loopback1:

发送帧的本地环回
-------------------

正如其他网络概念所熟知的那样，数据交换应用程序可以在同一个节点或不同节点上运行，无需任何更改（除了相应的寻址信息）：

.. code::

	 ___   ___   ___                   _______   ___
	| _ | | _ | | _ |                 | _   _ | | _ |
	||A|| ||B|| ||C||                 ||A| |B|| ||C||
	|___| |___| |___|                 |_______| |___|
	  |     |     |                       |       |
	-----------------(1)- CAN bus -(2)---------------

为了确保应用 A 在示例 (2) 中接收到的信息与其在示例 (1) 中接收到的一样，需要在适当的节点上对发送的 CAN 帧执行某种形式的本地环回。Linux 网络设备（默认情况下）只能处理媒体依赖帧的传输和接收。由于 CAN 总线上的仲裁，低优先级的 CAN 标识符可能会因高优先级的 CAN 帧的接收而延迟。为了反映节点上的正确 [#f1]_ 通信，成功传输后应立即执行发送数据的环回。如果 CAN 网络接口由于某些原因无法执行环回，则 SocketCAN 核心可以作为备选方案执行此任务。详细信息请参阅 :ref:`socketcan-local-loopback2`（推荐）。环回功能默认启用，以反映 CAN 应用程序的标准网络行为。由于来自 RT-SocketCAN 组的一些请求，环回可选地为每个单独的套接字禁用。有关 CAN RAW 套接字的 sockopts，请参阅 :ref:`socketcan-raw-sockets`。
.. [#f1] 当您在同一节点上运行分析工具（如 'candump' 或 'cansniffer'）时，您确实希望拥有这一点

.. _socketcan-network-problem-notifications:

网络问题通知
-------------------

使用 CAN 总线可能会导致物理层和媒体访问控制层上的多个问题。检测和记录这些较低层的问题对于 CAN 用户识别物理收发器层上的硬件问题以及不同 ECU 引起的仲裁问题和错误帧至关重要。检测到的错误的发生对于诊断很重要，并且必须与确切的时间戳一起记录。因此，CAN 接口驱动程序可以生成所谓的错误消息帧，并可选择性地以与其他 CAN 帧相同的方式传递给用户应用程序。每当检测到物理层或 MAC 层上的错误（例如由 CAN 控制器检测到）时，驱动程序会创建一个合适的错误消息帧。用户应用程序可以使用通用的 CAN 过滤机制请求错误消息帧。在此过滤定义中可以选择感兴趣的错误类型。默认情况下，错误消息的接收是禁用的。CAN 错误消息帧的格式在 Linux 头文件 "include/uapi/linux/can/error.h" 中简要描述。
如何使用SocketCAN
==================

与TCP/IP相似，在通过CAN网络进行通信之前，您需要先打开一个套接字。由于SocketCAN实现了一个新的协议族，因此在调用socket(2)系统调用时，需要将PF_CAN作为第一个参数传递。目前有两种CAN协议可供选择：原始套接字协议和广播管理器（BCM）。要打开一个套接字，您可以这样写：

```c
s = socket(PF_CAN, SOCK_RAW, CAN_RAW);
```

以及：

```c
s = socket(PF_CAN, SOCK_DGRAM, CAN_BCM);
```

分别地。成功创建套接字后，通常会使用bind(2)系统调用来将套接字绑定到CAN接口（这与TCP/IP不同，因为地址格式不同——参见:ref:`socketcan-concept`）。在绑定（CAN_RAW）或连接（CAN_BCM）套接字之后，您可以从/向套接字读取(2)和写入(2)，或者像往常一样使用send(2)，sendto(2)，sendmsg(2)及其recv*系列操作。下面还描述了一些CAN特定的套接字选项。

经典CAN帧结构（即CAN 2.0B），CAN FD帧结构和sockaddr结构在include/linux/can.h中定义如下：

```c
struct can_frame {
        canid_t can_id;  /* 32位CAN_ID + EFF/RTR/ERR标志 */
        union {
                /* CAN帧有效载荷长度（0 .. CAN_MAX_DLEN）字节
                 * 此前称为can_dlc，因此我们需要保留这个名称以支持遗留代码
                 */
                __u8 len;
                __u8 can_dlc; /* 已废弃 */
        };
        __u8    __pad;   /* 填充 */
        __u8    __res0;  /* 保留/填充 */
        __u8    len8_dlc; /* 可选的8字节有效载荷长度DLC（9 .. 15） */
        __u8    data[8] __attribute__((aligned(8)));
};
```

备注：len元素包含有效载荷长度（字节），应优先使用而不是can_dlc。已废弃的can_dlc名称误导性地表示它始终包含实际的有效载荷长度（字节），而不是所谓的“数据长度码”（DLC）。
为了将原始DLC从/至经典CAN网络设备传递，当len元素为8时（对于所有大于或等于8的DLC值的实际有效载荷长度），len8_dlc元素可以包含9到15的值。
（线性）有效载荷数据[]对齐到64位边界，允许用户定义自己的结构和联合体来轻松访问CAN有效载荷。默认情况下，CAN总线上没有给定的字节顺序。对CAN_RAW套接字的read(2)系统调用将struct can_frame传输到用户空间。
sockaddr_can结构具有类似PF_PACKET套接字的接口索引，也绑定到特定接口：

```c
struct sockaddr_can {
        sa_family_t can_family;
        int         can_ifindex;
        union {
                /* 传输协议类地址信息（例如ISOTP） */
                struct { canid_t rx_id, tx_id; } tp;

                /* J1939地址信息 */
                struct {
                        /* 使用动态寻址时的8字节名称 */
                        __u64 name;

                        /* pgn:
                         * 8位：PDU2情况下的PS，否则为0
                         * 8位：PF
                         * 1位：DP
                         * 1位：保留
                         */
                        __u32 pgn;

                        /* 1字节地址 */
                        __u8 addr;
                } j1939;

                /* 为未来CAN协议预留的地址信息 */
        } can_addr;
};
```

为了确定接口索引，需要使用适当的ioctl()（CAN_RAW套接字示例，不包括错误检查）：

```c
int s;
struct sockaddr_can addr;
struct ifreq ifr;

s = socket(PF_CAN, SOCK_RAW, CAN_RAW);

strcpy(ifr.ifr_name, "can0");
ioctl(s, SIOCGIFINDEX, &ifr);

addr.can_family = AF_CAN;
addr.can_ifindex = ifr.ifr_ifindex;

bind(s, (struct sockaddr *)&addr, sizeof(addr));
```

为了将套接字绑定到所有（！）CAN接口，接口索引必须为0（零）。在这种情况下，套接字接收来自每个启用的CAN接口的CAN帧。为了确定来源CAN接口，可以使用recvfrom(2)系统调用代替read(2)。为了在绑定到“任意”接口的套接字上发送，需要使用sendto(2)来指定传出接口。
从绑定的CAN_RAW套接字读取CAN帧（如上所述）包括读取struct can_frame：

```c
struct can_frame frame;

nbytes = read(s, &frame, sizeof(struct can_frame));

if (nbytes < 0) {
        perror("can raw socket read");
        return 1;
}

/* 多疑检查... */
if (nbytes < sizeof(struct can_frame)) {
        fprintf(stderr, "read: incomplete CAN frame\n");
        return 1;
}

/* 对收到的CAN帧执行某些操作 */
```

写入CAN帧可以通过write(2)系统调用类似地完成：

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

要在绑定到“任意”CAN接口的套接字上写入CAN帧，必须明确定义传出接口：

```c
strcpy(ifr.ifr_name, "can0");
ioctl(s, SIOCGIFINDEX, &ifr);
addr.can_ifindex = ifr.ifr_ifindex;
addr.can_family  = AF_CAN;

nbytes = sendto(s, &frame, sizeof(struct can_frame),
                0, (struct sockaddr*)&addr, sizeof(addr));
```

在从套接字读取消息后，可以使用ioctl(2)调用来获取精确的时间戳：

```c
struct timeval tv;
ioctl(s, SIOCGSTAMP, &tv);
```

时间戳的分辨率为一微秒，并在接收到CAN帧时自动设置。
关于CAN FD（灵活数据速率）支持的备注：

通常处理CAN FD的方式与前面描述的例子非常相似。新的CAN FD控制器支持在CAN FD帧的仲裁阶段和有效载荷阶段使用两种不同的比特率，并且最多支持64字节的有效载荷。这种扩展的有效载荷长度破坏了严重依赖于固定八字节有效载荷（struct can_frame）的所有内核接口（ABI），例如CAN_RAW套接字。因此，例如，CAN_RAW套接字支持一个新的套接字选项CAN_RAW_FD_FRAMES，该选项将套接字切换到一种模式，允许同时处理CAN FD帧和经典CAN帧（参见:ref:`socketcan-rawfd`）。
struct canfd_frame在include/linux/can.h中定义如下：

```c
struct canfd_frame {
        canid_t can_id;  /* 32位CAN_ID + EFF/RTR/ERR标志 */
        __u8    len;     /* 帧有效载荷长度（0 .. 64）字节 */
        __u8    flags;   /* CAN FD附加标志 */
        __u8    __res0;  /* 保留/填充 */
        __u8    __res1;  /* 保留/填充 */
        __u8    data[64] __attribute__((aligned(8)));
};
```

struct canfd_frame和现有的struct can_frame在它们的结构中具有相同的偏移量的can_id、有效载荷长度和有效载荷数据。这使得可以非常相似地处理这些不同的结构。
当将struct can_frame的内容复制到struct canfd_frame时，所有结构元素都可以直接使用——只有data[]会被扩展。
在介绍 `struct canfd_frame` 时发现，`struct can_frame` 中的数据长度码（DLC）被用作长度信息，因为该长度和 DLC 在 0 到 8 的范围内是一一对应的。为了保持长度信息的易用性，`canfd_frame.len` 元素包含一个从 0 到 64 的简单长度值。因此，`canfd_frame.len` 和 `can_frame.len` 是相等的，并且都包含长度信息而不是 DLC。

关于 CAN 和 CAN FD 设备的区别以及与总线相关的数据长度码（DLC）的映射，请参见 :ref:`socketcan-can-fd-driver`。

两个 CAN(FD) 帧结构的长度定义了 CAN(FD) 网络接口的最大传输单元（MTU）和 skbuff 数据长度。在 `include/linux/can.h` 中为 CAN 特定的 MTU 定义了两种规格：

```c
#define CAN_MTU   (sizeof(struct can_frame))   == 16  // 经典 CAN 帧
#define CANFD_MTU (sizeof(struct canfd_frame)) == 72  // CAN FD 帧
```

返回的消息标志
---------------

当在 RAW 或 BCM 套接字上使用系统调用 `recvmsg(2)` 时，`msg->msg_flags` 字段可能包含以下标志：

`MSG_DONTROUTE`：
接收的帧是在本地主机上创建的。

`MSG_CONFIRM`：
当帧通过该套接字发送时设置此标志。此标志可以解释为“传输确认”，如果 CAN 驱动支持在驱动级别回显帧，请参见 :ref:`socketcan-local-loopback1` 和 :ref:`socketcan-local-loopback2`。
（注意：要在 RAW 套接字上接收此类消息，必须设置 `CAN_RAW_RECV_OWN_MSGS`。）

.. _socketcan-raw-sockets:

带有 `can_filters` 的 RAW 协议套接字（SOCK_RAW）
----------------------------------------------

使用 CAN_RAW 套接字与通常已知的访问 CAN 字符设备非常相似。为了满足多用户 SocketCAN 方法提供的新功能，在绑定 RAW 套接字时设置了一些合理的默认值：

- 过滤器设置为恰好一个接收所有内容的过滤器
- 套接字只接收有效的数据帧（即不接收错误消息帧）
- 发送的 CAN 帧的环回被启用（参见 :ref:`socketcan-local-loopback2`）
- 套接字不会接收其自身发送的帧（在环回模式下）

这些默认设置可以在绑定套接字之前或之后更改。要使用 CAN_RAW 套接字选项的定义，请包含 `<linux/can/raw.h>`。

.. _socketcan-rawfilter:

RAW 套接字选项 `CAN_RAW_FILTER`
---------------------------------

使用 CAN_RAW 套接字接收 CAN 帧可以通过定义 0 到 n 个过滤器来控制，使用 `CAN_RAW_FILTER` 套接字选项。CAN 过滤器结构定义在 `include/linux/can.h` 中：

```c
struct can_filter {
        canid_t can_id;
        canid_t can_mask;
};
```

当满足以下条件时，过滤器匹配：

```c
<received_can_id> & mask == can_id & mask
```

这类似于已知的 CAN 控制器硬件过滤器语义。如果在 `can_filter` 结构中的 `can_id` 元素中设置了 `CAN_INV_FILTER` 标志，则可以反转过滤器语义。与 CAN 控制器硬件过滤器不同，用户可以为每个打开的套接字单独设置 0 到 n 个接收过滤器：

```c
struct can_filter rfilter[2];

rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = CAN_SFF_MASK;
rfilter[1].can_id   = 0x200;
rfilter[1].can_mask = 0x700;

setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter));
```

要禁用选定的 CAN_RAW 套接字上的 CAN 帧接收：

```c
setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, NULL, 0);
```

将过滤器设置为零过滤器几乎过时，因为这样做会导致原始套接字丢弃接收到的 CAN 帧。但考虑到这种“仅发送”的用例，我们可以移除内核中的接收列表以节省一点点（真的是一点点！）CPU 使用率。
### CAN 滤波器使用优化

CAN 滤波器在接收 CAN 帧时按照每个设备的滤波列表进行处理。为了减少遍历滤波列表时需要执行的检查次数，CAN 核心提供了优化的滤波处理，特别是当滤波订阅集中在单一 CAN ID 上时。

对于可能的 2048 个标准帧（SFF）CAN 标识符，标识符用作索引以直接访问相应的订阅列表而无需进一步检查。对于可能的 2^29 个扩展帧（EFF）CAN 标识符，使用 10 位 XOR 折叠作为哈希函数来获取 EFF 表索引。

为了从针对单一 CAN 标识符的优化滤波器中受益，必须将 `CAN_SFF_MASK` 或 `CAN_EFF_MASK` 设置到 `can_filter.mask` 中，并设置 `CAN_EFF_FLAG` 和 `CAN_RTR_FLAG` 位。在 `can_filter.mask` 中设置 `CAN_EFF_FLAG` 位表明是否关注 SFF 或 EFF CAN ID。例如：

```C
rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = CAN_SFF_MASK;
```

这样，SFF 帧与 CAN ID 0x123 以及 EFF 帧与 0xXXXXX123 都可以通过。如果只想过滤 0x123（SFF）和 0x12345678（EFF）CAN 标识符，则需要这样定义滤波器才能从优化滤波器中受益：

```C
struct can_filter rfilter[2];

rfilter[0].can_id   = 0x123;
rfilter[0].can_mask = (CAN_EFF_FLAG | CAN_RTR_FLAG | CAN_SFF_MASK);
rfilter[1].can_id   = 0x12345678 | CAN_EFF_FLAG;
rfilter[1].can_mask = (CAN_EFF_FLAG | CAN_RTR_FLAG | CAN_EFF_MASK);

setsockopt(s, SOL_CAN_RAW, CAN_RAW_FILTER, &rfilter, sizeof(rfilter));
```

### RAW Socket 选项 CAN_RAW_ERR_FILTER

如 :ref:`socketcan-network-problem-notifications` 所述，CAN 接口驱动程序可以生成所谓的错误消息帧，这些帧可以选择性地传递给用户应用程序，就像其他 CAN 帧一样。可能的错误分为不同的错误类别，可以使用适当的错误掩码进行过滤。要注册所有可能的错误条件，可以使用 `CAN_ERR_MASK` 作为错误掩码的值。错误掩码的值定义在 `linux/can/error.h` 中：

```C
can_err_mask_t err_mask = ( CAN_ERR_TX_TIMEOUT | CAN_ERR_BUSOFF );

setsockopt(s, SOL_CAN_RAW, CAN_RAW_ERR_FILTER, &err_mask, sizeof(err_mask));
```

### RAW Socket 选项 CAN_RAW_LOOPBACK

为满足多用户需求，默认情况下启用了本地环回功能（详见 :ref:`socketcan-local-loopback1`）。但在某些嵌入式用例中（例如只有一个应用程序使用 CAN 总线），可以禁用此环回功能（每个套接字单独禁用）：

```C
int loopback = 0; /* 0 = 禁用, 1 = 启用 (默认) */

setsockopt(s, SOL_CAN_RAW, CAN_RAW_LOOPBACK, &loopback, sizeof(loopback));
```

### RAW Socket 选项 CAN_RAW_RECV_OWN_MSGS

当启用本地环回时，所有发送的 CAN 帧都会回环到该接口上注册了 CAN 帧的 CAN-ID 的打开 CAN 套接字，以满足多用户需求。默认情况下，假设在同一套接字上接收自己发送的 CAN 帧是不需要的，因此被禁用。此默认行为可以根据需要更改：

```C
int recv_own_msgs = 1; /* 0 = 禁用 (默认), 1 = 启用 */

setsockopt(s, SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS, &recv_own_msgs, sizeof(recv_own_msgs));
```

请注意，套接字自身的 CAN 帧接收受与其他 CAN 帧相同的过滤规则约束（参见 :ref:`socketcan-rawfilter`）。

### RAW Socket 选项 CAN_RAW_FD_FRAMES

可以在 CAN_RAW 套接字中通过新的套接字选项 `CAN_RAW_FD_FRAMES` 启用 CAN FD 支持，默认情况下此选项关闭。如果 CAN_RAW 套接字不支持新的套接字选项（例如，在较旧的内核上），则切换 `CAN_RAW_FD_FRAMES` 选项会返回错误 `-ENOPROTOOPT`。
一旦启用了 `CAN_RAW_FD_FRAMES`，应用程序就可以发送 CAN 帧和 CAN FD 帧。另一方面，应用程序在从套接字读取时需要处理 CAN 和 CAN FD 帧：

```C
CAN_RAW_FD_FRAMES 启用：允许 CAN_MTU 和 CANFD_MTU
CAN_RAW_FD_FRAMES 禁用：仅允许 CAN_MTU (默认)
```

示例：

```C
[记住：CANFD_MTU == sizeof(struct canfd_frame)]

struct canfd_frame cfd;

nbytes = read(s, &cfd, CANFD_MTU);

if (nbytes == CANFD_MTU) {
        printf("收到长度为 %d 的 CAN FD 帧\n", cfd.len);
        /* cfd.flags 包含有效数据 */
} else if (nbytes == CAN_MTU) {
        printf("收到长度为 %d 的经典 CAN 帧\n", cfd.len);
        /* cfd.flags 未定义 */
} else {
        fprintf(stderr, "读取：无效的 CAN(FD) 帧\n");
        return 1;
}

/* 接收的内容可以独立于接收到的 MTU 大小进行处理 */

printf("can_id: %X 数据长度: %d 数据: ", cfd.can_id, cfd.len);
for (i = 0; i < cfd.len; i++)
        printf("%02X ", cfd.data[i]);
```

当使用大小为 CANFD_MTU 进行读取时，只返回从套接字接收到的 CAN_MTU 字节。这意味着已将经典 CAN 帧读入提供的 CAN FD 结构中。请注意，`canfd_frame.flags` 数据字段在 `struct can_frame` 中未定义，因此它仅在大小为 CANFD_MTU 的 CAN FD 帧中有效。

新 CAN 应用程序实现提示：

为了构建一个 CAN FD 兼容的应用程序，请使用 `struct canfd_frame` 作为基于 CAN_RAW 的应用程序的基本 CAN 数据结构。如果应用程序在较旧的 Linux 内核上运行并且切换 `CAN_RAW_FD_FRAMES` 套接字选项返回错误，则没问题。您将收到经典 CAN 帧或 CAN FD 帧，并且可以以相同的方式处理它们。
当向CAN设备发送数据时，请确保该设备能够处理CAN FD帧，方法是检查设备的最大传输单元（Maximum Transfer Unit, MTU）是否为CANFD_MTU。
CAN设备的MTU可以通过SIOCGIFMTU ioctl()系统调用来获取。

RAW套接字选项CAN_RAW_JOIN_FILTERS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN_RAW套接字可以设置多个特定于CAN标识符的过滤器，这些过滤器在af_can.c中的过滤器处理中表现为多个过滤器。这些过滤器相互独立，因此应用时会进行逻辑或运算（参见 :ref:`socketcan-rawfilter`）。
此套接字选项将给定的CAN过滤器以逻辑与的方式组合在一起，只有匹配所有给定CAN过滤器的CAN帧才会传递到用户空间。因此，应用的过滤器语义变为逻辑与。
这对于包含设置了CAN_INV_FILTER标志的过滤器的过滤器集特别有用，以便从传入流量中排除单个CAN ID或CAN ID范围。

广播管理协议套接字（SOCK_DGRAM）
-----------------------------------------------

广播管理协议提供了一个基于命令的配置接口，用于在内核空间中过滤和发送（例如周期性的）CAN消息。
接收过滤器可用于降低频繁消息的频率；检测事件如消息内容变化、包长度变化，并对收到的消息进行超时监控。
可以在运行时创建和修改CAN帧或CAN帧序列的周期性传输任务；消息内容和两个可能的传输间隔都可以改变。
BCM套接字不打算用于使用结构体can_frame（即CAN_RAW套接字所熟知的那种）发送单个CAN帧。相反，定义了一种特殊的BCM配置消息。基本的BCM配置消息用于与广播管理器通信，以及可用的操作定义在linux/can/bcm.h头文件中。BCM消息由一个带有命令（'opcode'）的消息头后跟零个或多个CAN帧组成。广播管理器以相同的形式向用户空间发送响应：

.. code-block:: C

    struct bcm_msg_head {
            __u32 opcode;                   /* 命令 */
            __u32 flags;                    /* 特殊标志 */
            __u32 count;                    /* 使用ival1运行'count'次 */
            struct timeval ival1, ival2;    /* count和后续间隔 */
            canid_t can_id;                 /* 任务唯一的can_id */
            __u32 nframes;                  /* 随后的can_frame数量 */
            struct can_frame frames[0];
    };

对齐的有效负载'frames'使用了在 :ref:`socketcan-rawfd` 和include/linux/can.h头文件中定义的基本CAN帧结构。所有从用户空间发送到广播管理器的消息都有这种结构。
注意：创建套接字后，必须连接（而不是绑定）CAN_BCM套接字（以下是一个不包含错误检查的示例）：

.. code-block:: C

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

广播管理器套接字能够同时处理任意数量的在途传输或接收过滤器。不同的接收/发送任务通过每个BCM消息中的唯一can_id来区分。然而，建议使用额外的CAN_BCM套接字来与多个CAN接口通信。当广播管理器套接字绑定到“任何”CAN接口（即接口索引设置为零）时，配置的接收过滤器适用于任何CAN接口，除非使用sendto()系统调用来覆盖“任何”CAN接口索引。当使用recvfrom()而不是read()来检索BCM套接字消息时，源CAN接口将提供在can_ifindex中。

广播管理器操作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

操作码定义了广播管理器要执行的操作，或者详细描述了广播管理器对若干事件（包括用户请求）的响应。
发送操作（用户空间到广播管理器）:

TX_SETUP:
  创建（周期性）发送任务
TX_DELETE:
  删除（周期性）发送任务，仅需要can_id
TX_READ:
  读取can_id对应的（周期性）发送任务属性
TX_SEND:
  发送一个CAN帧
发送响应（广播管理器到用户空间）:

TX_STATUS:
  响应TX_READ请求（发送任务配置）
TX_EXPIRED:
  当计数器在初始间隔'ival1'结束发送时的通知。要求在TX_SETUP时设置TX_COUNTEVT标志
接收操作（用户空间到广播管理器）:

RX_SETUP:
  创建RX内容过滤器订阅
RX_DELETE:
	移除 RX 内容过滤订阅，仅需要 can_id
RX_READ:
	读取 RX 内容过滤订阅的属性（针对 can_id）
接收响应（广播管理器到用户空间）：

RX_STATUS:
	回复 RX_READ 请求（过滤任务配置）
RX_TIMEOUT:
	周期性消息被检测为缺失（定时器 ival1 过期）
RX_CHANGED:
	带有更新后的 CAN 帧的 BCM 消息（检测到内容变化）
在接收到第一条消息或接收到修订后的 CAN 消息时发送
广播管理器消息标志
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当向广播管理器发送消息时，“flags”元素可以包含以下标志定义，这些定义会影响行为：

SETTIMER:
	设置 ival1、ival2 和 count 的值

STARTTIMER:
	使用当前的 ival1、ival2 和 count 值启动定时器。启动定时器会同时触发发送一个 CAN 帧
TX_COUNTEVT:
	当 count 到期时创建消息 TX_EXPIRED

TX_ANNOUNCE:
	进程中的数据更改会立即发出
TX_CP_CAN_ID:
	将消息头中的 can_id 复制到 frames 中的每个后续帧。这旨在简化使用。对于 TX 任务，消息头中的唯一 can_id 可能与后续 struct can_frame(s) 中存储用于传输的 can_id 不同
RX_FILTER_ID:
	仅通过 can_id 进行过滤，不需要 frames（nframes=0）
### RX_CHECK_DLC：
DLC 的变化会导致 RX_CHANGED。

### RX_NO_AUTOTIMER：
防止自动启动超时监视器。

### RX_ANNOUNCE_RESUME：
如果在 RX_SETUP 时传递，并且发生了接收超时，则当（循环）接收重新开始时，会生成一个 RX_CHANGED 消息。

### TX_RESET_MULTI_IDX：
重置多帧传输的索引。

### RX_RTR_FRAME：
发送对 RTR 请求的回复（放置在 op->frames[0] 中）。

### CAN_FD_FRAME：
跟随在 bcm_msg_head 后面的 CAN 帧是 struct canfd_frame 类型的。

### 广播管理器传输定时器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

周期性传输配置可以使用最多两个间隔定时器。在这种情况下，BCM 以一个间隔 'ival1' 发送一定数量的消息（'count'），然后继续以另一个给定的间隔 'ival2' 发送。当只需要一个定时器时，将 'count' 设置为零，只使用 'ival2'。当设置了 SET_TIMER 和 START_TIMER 标志时，定时器被激活。仅设置 SET_TIMER 时，可以在运行时更改定时器值。

### 广播管理器消息序列传输
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在一个周期性的 TX 任务配置中，最多可以按顺序传输 256 个 CAN 帧。CAN 帧的数量由 BCM 消息头中的 'nframes' 元素提供。定义的 CAN 帧数量作为数组添加到 TX_SETUP BCM 配置消息中：

```C
/* 创建一个结构体来设置四个 CAN 帧的序列 */
struct {
        struct bcm_msg_head msg_head;
        struct can_frame frame[4];
} mytxmsg;

(..)
mytxmsg.msg_head.nframes = 4;
(..)

write(s, &mytxmsg, sizeof(mytxmsg));
```

每次传输时，CAN 帧数组的索引都会增加，在索引溢出时会被重置为零。
广播管理器接收过滤定时器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在RX_SETUP时可以将定时器值ival1或ival2设置为非零值。当SET_TIMER标志被设置时，这些定时器会被启用：

ival1：
当接收到的消息在给定时间内未再次接收到时发送RX_TIMEOUT。当在RX_SETUP时设置了START_TIMER标志，则即使没有先前的CAN帧接收也会立即激活超时检测。

ival2：
将接收到的消息速率限制到ival2的值。当CAN帧内的信号是无状态的（即ival2周期内的状态变化可能会丢失）时，这有助于减少应用层的消息数量。

广播管理器多路复用消息接收过滤
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

为了过滤多路复用消息序列中的内容变化，可以在RX_SETUP配置消息中传递一个包含多个CAN帧的数组。第一个CAN帧的数据字节包含后续CAN帧与接收到的CAN帧之间需要匹配的相关位掩码。
如果后续的CAN帧中的位与该帧数据中的位相匹配，则标记这些相关的内容以与之前接收到的内容进行比较。
最多可以向TX_SETUP BCM配置消息添加257个CAN帧（多路复用滤波位掩码CAN帧加上256个CAN滤波器）：

```C
/* 通常用于清除CAN帧数据[] - 注意字节序问题！ */
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
U64_DATA(&msg.frame[1]) = 0x01000000000000FFULL; /* 数据掩码 (多路复用0x01) */
U64_DATA(&msg.frame[2]) = 0x0200FFFF000000FFULL; /* 数据掩码 (多路复用0x02) */
U64_DATA(&msg.frame[3]) = 0x330000FFFFFF0003ULL; /* 数据掩码 (多路复用0x33) */
U64_DATA(&msg.frame[4]) = 0x4F07FC0FF0000000ULL; /* 数据掩码 (多路复用0x4F) */

write(s, &msg, sizeof(msg));
```

广播管理器CAN FD支持
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN_BCM编程API依赖于直接位于bcm_msg_head结构后面的struct can_frame数组。为了遵循这一模式处理CAN FD帧，在bcm_msg_head的标志中新增了一个'CAN_FD_FRAME'标志，指示在bcm_msg_head后面定义的连接CAN帧结构为struct canfd_frame：

```C
struct {
        struct bcm_msg_head msg_head;
        struct canfd_frame frame[5];
} msg;

msg.msg_head.opcode  = RX_SETUP;
msg.msg_head.can_id  = 0x42;
msg.msg_head.flags   = CAN_FD_FRAME;
msg.msg_head.nframes = 5;
(..)
```

在使用CAN FD帧进行多路复用过滤时，多路复用掩码仍然期望在struct canfd_frame数据部分的第一个64位中出现。

连接传输协议（SOCK_SEQPACKET）
----------------------------------------------

（待撰写）

非连接传输协议（SOCK_DGRAM）
----------------------------------------------

（待撰写）

.. _socketcan-core-module:

SocketCAN核心模块
=====================

SocketCAN核心模块实现了协议族PF_CAN。CAN协议模块由核心模块在运行时加载。核心模块提供了一个接口供CAN协议模块订阅所需的CAN ID（参见 :ref:`socketcan-receive-lists`）。

can.ko模块参数
--------------------

- **stats_timer**：
  为了计算SocketCAN核心统计信息（例如当前/最大每秒帧数），此1秒定时器默认在can.ko模块启动时调用。可以通过在模块命令行上使用stattimer=0来禁用此定时器。
- **debug**：
  （自SocketCAN SVN r546起移除）

procfs内容
--------------

如 :ref:`socketcan-receive-lists` 所述，SocketCAN核心使用多个过滤列表将接收到的CAN帧传递给CAN协议模块。这些接收列表、它们的过滤器和过滤匹配次数可以在相应的接收列表中查看。所有条目都包含设备和协议模块标识符：

```
foo@bar:~$ cat /proc/net/can/rcvlist_all

接收列表 'rx_all':
  (vcan3: 无条目)
  (vcan2: 无条目)
  (vcan1: 无条目)
  设备   can_id   can_mask  function  userdata   匹配次数  标识
   vcan0     000    00000000  f88e6370  f6c6f400         0  raw
  (any: 无条目)
```

在这个示例中，应用程序请求从vcan0接收任何CAN流量：

- rcvlist_all - 无过滤条目的列表（不执行过滤操作）
- rcvlist_eff - 单个扩展帧（EFF）条目的列表
- rcvlist_err - 错误消息帧掩码列表
- rcvlist_fil - 掩码/值过滤器列表
- rcvlist_inv - 反义掩码/值过滤器列表
- rcvlist_sff - 单个标准帧（SFF）条目的列表

/proc/net/can中的其他procfs文件：

- stats - SocketCAN核心统计信息（接收/发送帧数、匹配比例等）
- reset_stats - 手动重置统计信息
- version - 打印SocketCAN核心和ABI版本（Linux 5.10中移除）

编写自己的CAN协议模块
--------------------------------

为了在协议族PF_CAN中实现新的协议，需要在include/linux/can.h中定义一个新的协议。通过包含include/linux/can/core.h可以访问使用SocketCAN核心的原型和定义。
除了注册 CAN 协议和 CAN 设备通知链的功能外，还有订阅 CAN 接口接收到的 CAN 帧以及发送 CAN 帧的功能：

    can_rx_register   - 订阅特定接口的 CAN 帧
    can_rx_unregister - 取消订阅特定接口的 CAN 帧
    can_send          - 发送一个 CAN 帧（可选地支持本地回环）

详情请参见 net/can/af_can.c 中的 kerneldoc 文档，或 net/can/raw.c 或 net/can/bcm.c 的源代码。

CAN 网络驱动程序
==================

编写 CAN 网络设备驱动程序比编写 CAN 字符设备驱动程序要容易得多。与其它已知的网络设备驱动程序类似，您主要需要处理以下内容：

- TX：将 CAN 帧从套接字缓冲区发送到 CAN 控制器
- RX：将 CAN 帧从 CAN 控制器接收至套接字缓冲区

详见 Documentation/networking/netdevices.rst 。编写 CAN 网络设备驱动程序的不同之处如下所述：

通用设置
------------

```c
    dev->type  = ARPHRD_CAN; /* 网络设备硬件类型 */
    dev->flags = IFF_NOARP;  /* CAN 没有 ARP */

    dev->mtu = CAN_MTU; /* sizeof(struct can_frame) -> 经典 CAN 接口 */

    或者替代方案，当控制器支持带有灵活数据速率的 CAN 时：
    dev->mtu = CANFD_MTU; /* sizeof(struct canfd_frame) -> CAN FD 接口 */
```

在协议家族 PF_CAN 中，每个套接字缓冲区（skbuff）的有效载荷是 struct can_frame 或 struct canfd_frame。
_本地回环发送帧
----------------------

如 :ref:`socketcan-local-loopback1` 所述，CAN 网络设备驱动程序应支持类似于 tty 设备本地回显功能的本地回环功能。在这种情况下，需要设置驱动标志 IFF_ECHO 以防止 PF_CAN 核心作为回退解决方案本地回显发送的帧（即回环）：

```c
    dev->flags = (IFF_NOARP | IFF_ECHO);
```

CAN 控制器硬件过滤器
-------------------------------

为了减少深度嵌入式系统上的中断负载，一些 CAN 控制器支持对 CAN ID 或 CAN ID 范围进行过滤。这些硬件过滤能力因控制器而异，在多用户网络方法中被认为是不可行的。使用非常特定于控制器的硬件过滤器在非常专用的应用场景中可能有意义，因为驱动程序级别的过滤器会影响多用户系统中的所有用户。PF_CAN 核心中的高效过滤集允许为每个套接字单独设置不同的多个过滤器。因此，使用硬件过滤器归类为“深度嵌入式系统的手工调优”。作者在 2002 年运行的 MPC603e @133MHz 上使用四个 SJA1000 CAN 控制器，在高总线负载下没有遇到任何问题。
可切换的终端电阻
-----------------------

CAN 总线要求在差分对之间具有特定的阻抗，通常由总线上最远节点上的两个 120 欧姆电阻提供。某些 CAN 控制器支持激活/停用终端电阻以提供正确的阻抗。

查询可用的电阻值：

```
    $ ip -details link show can0
    ..
    termination 120 [ 0, 120 ]
```

激活终端电阻：

```
    $ ip link set dev can0 type can termination 120
```

停用终端电阻：

```
    $ ip link set dev can0 type can termination 0
```

要使 CAN 控制器支持终端电阻，请在其结构体 can-priv 中实现：

    termination_const
    termination_const_cnt
    do_set_termination

或者使用来自 Documentation/devicetree/bindings/net/can/can-controller.yaml 的设备树条目添加 GPIO 控制。

虚拟 CAN 驱动程序（vcan）
-----------------------------

类似于网络回环设备，vcan 提供了一个虚拟的本地 CAN 接口。在 CAN 上的一个完整地址由以下部分组成：

- 一个唯一的 CAN 标识符（CAN ID）
- 此 CAN ID 传输所在的 CAN 总线（例如 can0）

因此，在常见的使用场景中，通常需要不止一个虚拟 CAN 接口。
虚拟CAN接口允许在没有实际CAN控制器硬件的情况下发送和接收CAN帧。虚拟CAN网络设备通常命名为'vcanX'，例如 vcan0、vcan1、vcan2 等。当编译为模块时，虚拟CAN驱动程序模块称为 vcan.ko。

自Linux内核版本2.6.24起，vcan驱动支持通过内核的netlink接口创建vcan网络设备。使用ip(8)工具可以管理vcan网络设备的创建和删除：

- 创建一个虚拟CAN网络接口：
  ```
  $ ip link add type vcan
  ```

- 使用特定名称 'vcan42' 创建虚拟CAN网络接口：
  ```
  $ ip link add dev vcan42 type vcan
  ```

- 删除名为 'vcan42' 的（虚拟CAN）网络接口：
  ```
  $ ip link del vcan42
  ```

### CAN网络设备驱动接口

CAN网络设备驱动接口提供了一个通用接口来设置、配置和监控CAN网络设备。用户可以通过netlink接口使用“IPROUTE2”工具套件中的“ip”程序来配置CAN设备，如设置位定时参数。以下章节简要描述了如何使用它。此外，该接口使用了一种通用的数据结构并导出了一组通用函数，所有实际的CAN网络设备驱动都应使用这些函数。请参考SJA1000或MSCAN驱动来了解如何使用它们。该模块名称为 can-dev.ko。

#### Netlink接口用于设置/获取设备属性

CAN设备必须通过netlink接口进行配置。支持的netlink消息类型在“include/linux/can/netlink.h”中定义并进行了简要描述。“IPROUTE2”工具套件中的“ip”程序支持CAN链路，并可如下所示使用：

**设置CAN设备属性：**

```
$ ip link set can0 type can help
用法: ip link set DEVICE type can
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

其中:
    BITRATE       := { 1..1000000 }
    SAMPLE-POINT  := { 0.000..0.999 }
    TQ            := { NUMBER }
    PROP-SEG      := { 1..8 }
    PHASE-SEG1    := { 1..8 }
    PHASE-SEG2    := { 1..8 }
    SJW           := { 1..4 }
    RESTART-MS    := { 0 | NUMBER }
```

**显示CAN设备详细信息和统计信息：**

```
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
```

更多关于上述输出的信息：

- `<TRIPLE-SAMPLING>`  
  显示选定的CAN控制器模式列表：LOOPBACK、LISTEN-ONLY 或 TRIPLE-SAMPLING。

- `state ERROR-ACTIVE`  
  当前CAN控制器的状态：“ERROR-ACTIVE”、“ERROR-WARNING”、“ERROR-PASSIVE”、“BUS-OFF” 或 “STOPPED”。

- `restart-ms 100`  
  自动重启延迟时间。如果设置为非零值，则在总线关闭条件后，经过指定的延迟时间（毫秒）将自动触发CAN控制器重启，默认情况下不启用。

- `bitrate 125000 sample-point 0.875`  
  显示实际比特率（bps）和采样点（范围0.000至0.999）。如果内核启用了位定时参数计算（CONFIG_CAN_CALC_BITTIMING=y），则可以通过设置“bitrate”参数来定义位定时。可选地，还可以指定“sample-point”，默认值为0.000，假设采用CIA推荐的采样点。

- `tq 125 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1`  
  显示时间量子（ns）、传播段、相位缓冲段1和2以及同步跳转宽度（以tq为单位）。它们允许以硬件独立的格式定义CAN位定时，如Bosch CAN 2.0规范所建议（参见 http://www.semiconductors.bosch.de/pdf/can2spec.pdf 第8章）。

- `sja1000: tseg1 1..16 tseg2 1..8 sjw 1..4 brp 1..64 brp-inc 1 clock 8000000`  
  显示CAN控制器的位定时常量，此处为“sja1000”。显示了时间段1和2的最小和最大值、同步跳转宽度（以tq为单位）、比特率预分频器和CAN系统时钟频率（Hz）。

这些常量可用于用户空间中自定义（非标准）的位定时计算算法。
重新启动总线错误、仲裁丢失错误、警告错误、被动错误和总线关闭状态
显示重启次数、总线和仲裁丢失错误，以及转换到错误警告、错误被动和总线关闭状态的次数。接收缓冲区溢出错误列在标准网络统计中的“溢出”字段中。

设置CAN位定时
~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN位定时参数可以始终按照Bosch CAN 2.0规范中建议的方式以硬件无关的格式定义，该规范指定了“tq”、“prop_seg”、“phase_seg1”、“phase_seg2”和“sjw”等参数，例如：

```
$ ip link set canX type can tq 125 prop-seg 6 phase-seg1 7 phase-seg2 2 sjw 1
```

如果启用了内核选项`CONFIG_CAN_CALC_BITTIMING`，当使用“bitrate”参数指定比特率时，将计算CIA推荐的CAN位定时参数，例如：

```
$ ip link set canX type can bitrate 125000
```

请注意，这适用于大多数常见的CAN控制器和标准比特率，但对于异类比特率或CAN系统时钟频率可能会*失败*。禁用`CONFIG_CAN_CALC_BITTIMING`可以节省一些空间，并允许用户空间工具单独确定并设置位定时参数。可以使用CAN控制器特定的位定时常数来实现这一目的。这些常数可以通过以下命令列出：

```
$ ip -details link show can0
..
sja1000: clock 8000000 tseg1 1..16 tseg2 1..8 sjw 1..4 brp 1..64 brp-inc 1
```

启动和停止CAN网络设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CAN网络设备可以通过“ifconfig canX up/down”或“ip link set canX up/down”命令启动或停止。请注意，对于真实的CAN设备，在启动之前必须定义适当的位定时参数，以避免出现易错的默认设置，例如：

```
$ ip link set canX up type can bitrate 125000
```

如果CAN总线上发生了太多错误，设备可能会进入“总线关闭”状态。在这种情况下，不再接收或发送任何消息。可以通过将“restart-ms”设置为非零值来启用自动总线关闭恢复功能，例如：

```
$ ip link set canX type can restart-ms 100
```

或者，应用程序可以通过监控CAN错误消息帧来识别“总线关闭”条件，并在适当的时候使用以下命令进行重启：

```
$ ip link set canX type can restart
```

请注意，重启也会生成一个CAN错误消息帧（参见：:ref:`socketcan-network-problem-notifications`）。

CAN FD（灵活数据速率）驱动支持
------------------------------------------

支持CAN FD的CAN控制器可以在仲裁阶段和CAN FD帧的有效载荷阶段支持两种不同的比特率。因此，需要指定第二个位定时以启用CAN FD比特率。此外，支持CAN FD的CAN控制器最多可以支持64字节的有效载荷。这种长度在用户空间应用程序和Linux网络层内部表示为从0到64的简单值，而不是CAN的“数据长度代码”。数据长度代码在经典CAN帧中已经是有效载荷长度的一对一映射。有效载荷长度到总线相关的DLC的映射仅在CAN驱动程序内部完成，最好使用辅助函数`can_fd_dlc2len()`和`can_fd_len2dlc()`。
CAN网络设备驱动的能力可以通过网络设备的最大传输单元（MTU）来区分：

- MTU = 16（CAN_MTU）=> `sizeof(struct can_frame)` => 经典CAN设备
- MTU = 72（CANFD_MTU）=> `sizeof(struct canfd_frame)` => 支持CAN FD的设备

可以通过SIOCGIFMTU ioctl()系统调用来获取CAN设备的MTU。
请注意，支持CAN FD的设备也可以处理并发送经典CAN帧。配置支持CAN FD的CAN控制器时，需要设置一个额外的“数据”比特率。这个用于CAN FD帧数据阶段的比特率至少应等于为仲裁阶段配置的比特率。这个第二比特率的设置类似于第一个比特率，但用于“数据”比特率的比特率设置关键字以“d”开头，例如dbitrate、dsample-point、dsjw或dtq等类似设置。当设置了数据比特率后，在配置过程中可以指定控制器选项“fd on”，以在CAN控制器中启用CAN FD模式。此控制器选项还将设备MTU切换为72（CANFD_MTU）。
第一个CAN FD规范是在2012年国际CAN会议中以白皮书形式发布的，为了数据完整性原因需要改进。
因此，今天需要区分两种CAN FD实现：

- 符合ISO标准：ISO 11898-1:2015的CAN FD实现（默认）
- 不符合ISO标准：遵循2012年白皮书的CAN FD实现

最终，有三种类型的CAN FD控制器：

1. 符合ISO标准（固定）
2. 不符合ISO标准（固定，例如m_can.c中的M_CAN IP core v3.0.1）
3. 可切换的ISO/非ISO CAN FD控制器（可切换，例如PEAK PCAN-USB FD）

当前的ISO/非ISO模式由CAN控制器驱动通过netlink宣布，并且可以通过`ip`工具显示（控制器选项FD-NON-ISO）
只有对于可切换的CAN FD控制器，才能通过设置`fd-non-iso {on|off}`来更改ISO/非ISO模式
配置500 kbit/s仲裁比特率和4 Mbit/s数据比特率的示例：

```
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
```

当在可切换的CAN FD适配器上添加`fd-non-iso on`时的示例：

```
can <FD,FD-NON-ISO> state ERROR-ACTIVE (berr-counter tx 0 rx 0) restart-ms 0
```

支持的CAN硬件
--------------

请检查`drivers/net/can`目录下的“Kconfig”文件以获取支持的CAN硬件列表。在SocketCAN项目网站上（参见 :ref:`socketcan-resources`）可能会有更多的驱动程序可用，也适用于旧版本内核。
.. _socketcan-resources:

SocketCAN资源
==============

Linux CAN / SocketCAN项目的资源（项目站点/邮件列表）在Linux源代码树中的MAINTAINERS文件中有引用。
致谢
=====

- Oliver Hartkopp（PF_CAN核心、过滤器、驱动程序、bcm、SJA1000驱动程序）
- Urs Thuermann（PF_CAN核心、内核集成、套接字接口、raw、vcan）
- Jan Kizka（RT-SocketCAN核心、Socket-API协调）
- Wolfgang Grandegger（RT-SocketCAN核心及驱动程序、Raw Socket-API评审、CAN设备驱动接口、MSCAN驱动程序）
- Robert Schwebel（设计评审、PTXdist集成）
- Marc Kleine-Budde（设计评审、Kernel 2.6清理、驱动程序）
- Benedikt Spranger（评审）
- Thomas Gleixner（LKML评审、编码风格、发布提示）
- Andrey Volkov（内核子树结构、ioctl、MSCAN驱动程序）
- Matthias Brukner（2003年第二季度第一个SJA1000 CAN网络设备实现）
- Klaus Hitschler（PEAK驱动程序集成）
- Uwe Koppe（使用PF_PACKET方法的CAN网络设备）
- Michael Schulze（驱动层环回要求、RT CAN驱动程序评审）
- Pavel Pisa（位定时计算）
- Sascha Hauer（SJA1000平台驱动程序）
- Sebastian Haas（SJA1000 EMS PCI驱动程序）
- Markus Plessing（SJA1000 EMS PCI驱动程序）
- Per Dalen（SJA1000 Kvaser PCI驱动程序）
- Sam Ravnborg（评审、编码风格、kbuild帮助）
