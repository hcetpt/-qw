SPDX 许可证标识符: GPL-2.0

===========
数据包 MMAP
===========

摘要
========

本文档介绍了与 PACKET 套接字接口一起使用的 mmap() 功能。这种类型的套接字用于：

i) 使用像 tcpdump 这样的工具捕获网络流量，
ii) 发送网络流量，或任何需要直接访问网络接口的情况。
详细用法可以在以下网址找到：

    https://sites.google.com/site/packetmmap/

请将您的意见发送给：
    - Ulisses Alonso Camaró <uaca@i.hate.spam.alumni.uv.es>
    - Johann Baudy

为什么使用 PACKET_MMAP
===================

非 PACKET_MMAP 捕获过程（普通的 AF_PACKET）非常低效。它使用非常有限的缓冲区，并且每次捕获数据包都需要一次系统调用；如果你想要获取数据包的时间戳（就像 libpcap 总是做的那样），则需要两次系统调用。相比之下，PACKET_MMAP 非常高效。PACKET_MMAP 提供了一个大小可配置的循环缓冲区，该缓冲区映射到用户空间中，可用于发送或接收数据包。这样读取数据包只需要等待它们的到来，大多数情况下不需要发出任何系统调用。关于传输方面，可以通过一次系统调用来发送多个数据包以获得最高的带宽。通过在内核和用户之间使用共享缓冲区也有助于最小化数据包复制。

使用 PACKET_MMAP 可以提高捕获和传输过程的性能，但这并不是全部。至少，如果你以高速度进行捕获（这相对于 CPU 速度而言），你应该检查你的网卡设备驱动是否支持某种中断负载减轻措施，或者更好的是，是否支持 NAPI，并确保已启用这些功能。对于传输，检查网络设备所使用和支持的最大传输单元（MTU）。你的网卡的 CPU 中断引脚固定也可以带来优势。

如何使用 mmap() 改进捕获过程
============================================

从用户的角度来看，你应该使用更高级别的 libpcap 库，这是一个事实上的标准，在几乎所有操作系统（包括 Win32）上都是便携的。Packet MMAP 支持大约在版本 1.3.0 时被集成到 libpcap 中；TPACKET_V3 支持在版本 1.5.0 中加入。

如何直接使用 mmap() 改进捕获过程
=====================================================

从系统调用的角度来看，使用 PACKET_MMAP 涉及以下过程：

    [设置]     socket() -------> 创建捕获套接字
		setsockopt() ---> 分配循环缓冲区（环）
				  选项：PACKET_RX_RING
		mmap() ---------> 将分配的缓冲区映射到
				  用户进程

    [捕获]   poll() ---------> 等待传入的数据包

    [关闭]  close() --------> 销毁捕获套接字并释放所有相关
				  资源
创建和销毁套接字的过程很简单，无论是否有 PACKET_MMAP 都是一样的：

    int fd = socket(PF_PACKET, mode, htons(ETH_P_ALL));

其中 mode 是 SOCK_RAW，用于可以捕获链路级别信息的原始接口，或者 SOCK_DGRAM，用于不支持捕获链路级别信息的已处理接口，内核会提供一个链路级别的伪首部。

销毁套接字及其所有相关资源只需简单地调用 close(fd)。

同样地，即使没有 PACKET_MMAP，也可以使用一个套接字进行捕获和传输。这可以通过一次 mmap() 调用来映射分配的 RX 和 TX 缓冲区环来实现。

参见“循环缓冲区（环）的映射和使用”。
接下来我将描述 PACKET_MMAP 设置及其约束条件，同时介绍用户进程中的环形缓冲区映射及该缓冲区的使用方法。
如何直接使用 mmap() 来改进传输过程
======================================
传输过程与捕获过程类似，如下所示：

    [设置]           socket() -------> 创建传输套接字
		    setsockopt() ---> 分配环形缓冲区（ring）
				      选项：PACKET_TX_RING
		    bind() ---------> 将传输套接字绑定到网络接口
		    mmap() ---------> 将分配的缓冲区映射到用户进程

    [传输]          poll() ---------> 等待空闲数据包（可选）
		    send() ---------> 发送环形缓冲区中设置为就绪的所有数据包
				      可以使用标志 MSG_DONTWAIT 在传输结束前返回

[关闭]          close() --------> 销毁传输套接字并释放所有相关资源

套接字的创建和销毁也十分简单，与前面段落中描述的捕获过程相同：

```c
int fd = socket(PF_PACKET, mode, 0);
```

协议可以是 0（可选），如果我们仅通过此套接字进行传输，这样可以避免调用昂贵的 packet_rcv() 函数。在这种情况下，还需要将 TX_RING 绑定到 sll_protocol = 0。否则，使用 htons(ETH_P_ALL) 或其他任何协议。

将套接字绑定到网络接口是必须的（零拷贝情况下），以便知道环形缓冲区中使用的帧的头部大小。

与捕获一样，每个帧包含两部分：

    --------------------
    | struct tpacket_hdr | 头部。它包含了该帧的状态
    |                    |
    |--------------------|
    | 数据缓冲区         |
    .                    .  通过网络接口发送的数据
    .
    --------------------

bind() 通过 sll_ifindex 参数将套接字关联到网络接口。

初始化示例：

```c
struct sockaddr_ll my_addr;
struct ifreq s_ifr;
..
```
```cpp
strscpy_pad(s_ifr.ifr_name, "eth0", sizeof(s_ifr.ifr_name));

/* 获取 eth0 的接口索引 */
ioctl(this->socket, SIOCGIFINDEX, &s_ifr);

/* 填充 sockaddr_ll 结构体以准备绑定 */
my_addr.sll_family = AF_PACKET;
my_addr.sll_protocol = htons(ETH_P_ALL);
my_addr.sll_ifindex = s_ifr.ifr_ifindex;

/* 将套接字绑定到 eth0 */
bind(this->socket, (struct sockaddr *)&my_addr, sizeof(struct sockaddr_ll));

一个完整的教程可以在以下链接找到：https://sites.google.com/site/packetmmap/

默认情况下，用户应该将数据放置在：

frame base + TPACKET_HDRLEN - sizeof(struct sockaddr_ll)

因此，无论您选择哪种套接字模式（SOCK_DGRAM 或 SOCK_RAW），用户数据的起始位置都在：

frame base + TPACKET_ALIGN(sizeof(struct tpacket_hdr))

如果您希望将用户数据放置在帧起始位置的自定义偏移处（例如，在使用 SOCK_RAW 模式时对齐有效负载），您可以设置 tp_net（使用 SOCK_DGRAM）或 tp_mac（使用 SOCK_RAW）。为了使这生效，必须事先通过 setsockopt() 和 PACKET_TX_HAS_OFF 选项启用。

PACKET_MMAP 设置
==================

从用户级代码设置 PACKET_MMAP 需要调用如下：

- 捕获进程：
  
      setsockopt(fd, SOL_PACKET, PACKET_RX_RING, (void *) &req, sizeof(req))

- 传输进程：
  
      setsockopt(fd, SOL_PACKET, PACKET_TX_RING, (void *) &req, sizeof(req))

上述调用中最重要的参数是 req 参数，此参数必须具有以下结构：

    struct tpacket_req
    {
        unsigned int    tp_block_size;  /* 连续块的最小大小 */
        unsigned int    tp_block_nr;    /* 块的数量 */
        unsigned int    tp_frame_size;  /* 帧大小 */
        unsigned int    tp_frame_nr;    /* 总帧数 */
    };

此结构定义在 /usr/include/linux/if_packet.h 中，并建立了一个不可交换内存的环形缓冲区。在捕获进程中映射允许读取捕获的帧及其相关的元信息（如时间戳），而无需进行系统调用。帧按块分组。每个块是一个物理连续的内存区域，包含 tp_block_size/tp_frame_size 帧。块的总数为 tp_block_nr。请注意，tp_frame_nr 是一个冗余参数，因为：

    frames_per_block = tp_block_size/tp_frame_size

实际上，packet_set_ring 检查以下条件是否为真：

    frames_per_block * tp_block_nr == tp_frame_nr

让我们看一个例子，假设以下值：

     tp_block_size= 4096
     tp_frame_size= 2048
     tp_block_nr  = 4
     tp_frame_nr  = 8

我们将得到以下缓冲区结构：

	    块 #1                 块 #2
    +---------+---------+    +---------+---------+
    | 帧 1   | 帧 2   |    | 帧 3   | 帧 4   |
    +---------+---------+    +---------+---------+

	    块 #3                 块 #4
    +---------+---------+    +---------+---------+
    | 帧 5   | 帧 6   |    | 帧 7   | 帧 8   |
    +---------+---------+    +---------+---------+

一个帧可以是任意大小，只要它能放入一个块中即可。一个块只能容纳整数个帧，换句话说，一个帧不能跨越两个块，所以在选择帧大小时需要注意一些细节。请参阅“环形缓冲区（环）的映射和使用”。

PACKET_MMAP 设置约束
======================

在内核版本 2.4.26（对于 2.4 分支）和 2.6.5（对于 2.6 分支）之前，PACKET_MMAP 缓冲区只能在 32 位架构中容纳 32768 个帧，或者在 64 位架构中容纳 16384 个帧。

块大小限制
------------

如前所述，每个块都是一个连续的物理内存区域。这些内存区域通过调用 __get_free_pages() 函数分配。顾名思义，这个函数分配内存页面，第二个参数是“order”或页面数量的 2 的幂次方（对于 PAGE_SIZE == 4096）order=0 ==> 4096 字节，order=1 ==> 8192 字节，order=2 ==> 16384 字节等。__get_free_pages 分配的最大区域大小由 MAX_PAGE_ORDER 宏确定。更准确地说，限制可以计算为：

   PAGE_SIZE << MAX_PAGE_ORDER

   在 i386 架构中，PAGE_SIZE 是 4096 字节
   在 2.4/i386 内核中，MAX_PAGE_ORDER 是 10
   在 2.6/i386 内核中，MAX_PAGE_ORDER 是 11

因此，在 2.4/2.6 内核中，get_free_pages 可以分配最多 4MB 或 8MB 的内存，对于 i386 架构来说。

用户空间程序可以通过包含 /usr/include/sys/user.h 和 /usr/include/linux/mmzone.h 来获取 PAGE_SIZE 和 MAX_PAGE_ORDER 的声明。页面大小也可以通过 getpagesize(2) 系统调用来动态确定。

块数量限制
------------

为了理解 PACKET_MMAP 的约束，我们需要查看用于存储指向每个块的指针的结构。
```
目前，该结构是一个动态分配的向量，使用 `kmalloc` 分配，称为 `pg_vec`，其大小限制了可分配的块数量：

    +---+---+---+---+
    | x | x | x | x |
    +---+---+---+---+
      |   |   |   |
      |   |   |   v
      |   |   v  块 #4
      |   v  块 #3
      v  块 #2
     块 #1

`kmalloc` 从一个预定义大小的内存池中分配物理上连续的任意字节数。这个内存池由 slab 分配器维护，最终负责实际分配，因此它也限定了 `kmalloc` 能够分配的最大内存。在 2.4/2.6 内核和 i386 架构中，限制是 131072 字节。`kmalloc` 使用的预定义大小可以在 `/proc/slabinfo` 中的 `size-<bytes>` 条目中查看。

在 32 位架构中，指针长度为 4 字节，因此指向块的总指针数为：

     131072/4 = 32768 块

PACKET_MMAP 缓冲区大小计算器
=============================

定义：

==============  ================================================================
<size-max>      是 `kmalloc` 可分配的最大大小（参见 `/proc/slabinfo`）
<指针大小>      依赖于架构——`sizeof(void *)`
<页大小>        依赖于架构——PAGE_SIZE 或 getpagesize (2)
<最大顺序>      是通过 MAX_PAGE_ORDER 定义的值
<帧大小>        帧捕获大小的上限（稍后详述）
==============  ==============================================================

根据这些定义，我们可以推导出：

	<块数> = <size-max>/<指针大小>
	<块大小> = <页大小> << <最大顺序>

因此，最大缓冲区大小为：

	<块数> * <块大小>

并且，帧的数量为：

	<块数> * <块大小> / <帧大小>

假设以下参数，适用于 2.6 内核和 i386 架构：

	<size-max> = 131072 字节
	<指针大小> = 4 字节
	<页大小> = 4096 字节
	<最大顺序> = 11

以及 <帧大小> 的值为 2048 字节。这些参数将得出：

	<块数> = 131072/4 = 32768 块
	<块大小> = 4096 << 11 = 8 MiB
因此缓冲区大小为 262144 MiB。它可以容纳
262144 MiB / 2048 字节 = 134217728 帧

实际上，在 i386 架构下无法实现这样的缓冲区大小。
请记住，内存是在内核空间中分配的，在 i386 内核的情况下，内存大小限制为 1 GiB。
所有内存分配直到套接字关闭时才释放。内存分配使用 GFP_KERNEL 优先级，这意味着分配可以等待并交换其他进程的内存以分配所需的内存，因此通常可以达到极限。

其他约束
--------

如果你检查源代码，会发现我在这里所画的帧不仅仅是链路层帧。每个帧的开头有一个名为 `struct tpacket_hdr` 的头部，用于在 PACKET_MMAP 中保存链路层帧的元信息，如时间戳。因此我们这里所画的一个帧实际上是以下结构（来自 `include/linux/if_packet.h`）：

/*
  帧结构：

  - 开始。帧必须对齐到 TPACKET_ALIGNMENT=16
  - struct tpacket_hdr
  - 填充到 TPACKET_ALIGNMENT=16
  - struct sockaddr_ll
  - 间隙，选择使得数据包数据（Start+tp_net）对齐到 TPACKET_ALIGNMENT=16
  - Start+tp_mac: [ 可选的 MAC 头 ]
  - Start+tp_net: 数据包数据，对齐到 TPACKET_ALIGNMENT=16
- 填充以对齐到 TPACKET_ALIGNMENT=16
*/

以下是 `packet_set_ring` 中检查的一些条件：

   - tp_block_size 必须是 PAGE_SIZE 的倍数（1）
   - tp_frame_size 必须大于 TPACKET_HDRLEN（显然）
   - tp_frame_size 必须是 TPACKET_ALIGNMENT 的倍数
   - tp_frame_nr 必须正好等于 frames_per_block * tp_block_nr

注意，tp_block_size 应选择为 2 的幂次方，否则会造成内存浪费。

循环缓冲区（环形缓冲区）的映射和使用
------------------------------------------

用户进程中的缓冲区映射是通过常规的 `mmap` 函数完成的。即使循环缓冲区由多个物理不连续的内存块组成，它们在用户空间中是连续的，因此只需要一次 `mmap` 调用即可：

    mmap(0, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

如果 tp_frame_size 是 tp_block_size 的除数，则帧将以 tp_frame_size 字节为间隔连续排列。如果不是，则每 tp_block_size/tp_frame_size 帧之间将有一个间隙。这是因为一个帧不能跨越两个块。

为了在一个套接字上进行捕获和传输，需要通过一次 `mmap` 调用来映射 RX 和 TX 缓冲区环：

    ..
setsockopt(fd, SOL_PACKET, PACKET_RX_RING, &foo, sizeof(foo));
    setsockopt(fd, SOL_PACKET, PACKET_TX_RING, &bar, sizeof(bar));
    ..
```c
rx_ring = mmap(0, size * 2, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
tx_ring = rx_ring + size;
```

RX 必须是第一个，因为内核将 TX 环形缓冲区映射在 RX 缓冲区之后。

每个帧的开头都有一个状态字段（参见 `struct tpacket_hdr`）。如果这个字段为 0，则表示该帧已准备好供内核使用；如果不是，则表示有一个用户可以读取的帧，并且以下标志适用：

### 捕获过程
^^^^^^^^^^^^^^^

从 `include/linux/if_packet.h` 中定义的宏：

```c
#define TP_STATUS_COPY          (1 << 1)
#define TP_STATUS_LOSING        (1 << 2)
#define TP_STATUS_CSUMNOTREADY  (1 << 3)
#define TP_STATUS_CSUM_VALID    (1 << 7)
```

| 标志              | 描述                                                                                          |
|-------------------|-----------------------------------------------------------------------------------------------|
| TP_STATUS_COPY    | 表示该帧（及其关联的元信息）已被截断，因为它大于 `tp_frame_size`。此数据包可以通过 `recvfrom()` 完整读取。为了使这生效，必须通过 `setsockopt()` 和 `PACKET_COPY_THRESH` 选项预先启用。可被 `recvfrom` 读取的数据包数量受到普通套接字的限制，参见 `SO_RCVBUF` 选项的 `socket(7)` 手册页。 |
| TP_STATUS_LOSING  | 表示自上次使用 `getsockopt()` 和 `PACKET_STATISTICS` 选项检查统计数据以来发生了数据包丢失。                                |
| TP_STATUS_CSUMNOTREADY | 当前用于出站 IP 数据包，其校验和将在硬件中完成。因此，在读取数据包时不应尝试检查校验和。                                       |
| TP_STATUS_CSUM_VALID | 此标志表示内核已验证数据包的传输头校验和。如果未设置此标志，则可以在不设置 `TP_STATUS_CSUMNOTREADY` 的情况下自行检查校验和。 |

为了方便起见，还有以下定义：

```c
#define TP_STATUS_KERNEL        0
#define TP_STATUS_USER          1
```

内核初始化所有帧的状态为 `TP_STATUS_KERNEL`。当内核接收到一个数据包时，它将其放入缓冲区并更新状态，至少设置 `TP_STATUS_USER` 标志。然后用户可以读取数据包。一旦数据包被读取，用户必须将状态字段置零，以便内核可以再次使用该帧缓冲区。

用户可以使用 `poll`（其他变体也适用）来检查环形缓冲区中是否有新数据包：

```c
struct pollfd pfd;

pfd.fd = fd;
pfd.revents = 0;
pfd.events = POLLIN | POLLRDNORM | POLLERR;

if (status == TP_STATUS_KERNEL)
    retval = poll(&pfd, 1, timeout);
```

首先检查状态值然后轮询帧不会导致竞态条件。
传输过程

这些宏定义也用于传输：

```c
#define TP_STATUS_AVAILABLE        0 // 帧可用
#define TP_STATUS_SEND_REQUEST     1 // 帧将在下次send()时发送
#define TP_STATUS_SENDING          2 // 帧正在传输中
#define TP_STATUS_WRONG_FORMAT     4 // 帧格式不正确
```

首先，内核将所有帧初始化为`TP_STATUS_AVAILABLE`。为了发送一个数据包，用户填充一个可用帧的数据缓冲区，并将`tp_len`设置为当前数据缓冲区的大小，并将其状态字段设置为`TP_STATUS_SEND_REQUEST`。这可以在多个帧上完成。一旦用户准备好发送，它会调用`send()`。然后所有状态等于`TP_STATUS_SEND_REQUEST`的缓冲区将被转发到网络设备。内核将每个已发送帧的状态更新为`TP_STATUS_SENDING`直到传输结束。每次传输结束后，缓冲区状态返回到`TP_STATUS_AVAILABLE`。

```c
header->tp_len = in_i_size;
header->tp_status = TP_STATUS_SEND_REQUEST;
retval = send(this->socket, NULL, 0, 0);
```

用户还可以使用`poll()`来检查是否有缓冲区可用：

```c
(status == TP_STATUS_SENDING)
```

```c
struct pollfd pfd;
pfd.fd = fd;
pfd.revents = 0;
pfd.events = POLLOUT;
retval = poll(&pfd, 1, timeout);
```

哪些版本的TPACKET可用以及何时使用它们？
=========================================

```c
int val = tpacket_version;
setsockopt(fd, SOL_PACKET, PACKET_VERSION, &val, sizeof(val));
getsockopt(fd, SOL_PACKET, PACKET_VERSION, &val, sizeof(val));
```

其中`tpacket_version`可以是`TPACKET_V1`（默认），`TPACKET_V2`或`TPACKET_V3`。

- `TPACKET_V1`：
  - 如果未通过`setsockopt`指定其他值，则为默认值。
  - 支持`RX_RING`和`TX_RING`。

- `TPACKET_V1`到`TPACKET_V2`：
  - 由于在`TPACKET_V1`结构中使用了无符号长整型，因此使其兼容64位，从而也能在64位内核与32位用户空间中工作。
  - 时间戳分辨率从微秒变为纳秒。
  - 支持`RX_RING`和`TX_RING`。
  - 支持VLAN元数据信息（`TP_STATUS_VLAN_VALID`, `TP_STATUS_VLAN_TPID_VALID`）在`tpacket2_hdr`结构中：
    - 将`TP_STATUS_VLAN_VALID`标志设置到`tp_status`字段表示`tp_vlan_tci`字段包含有效的VLAN TCI值。
    - 将`TP_STATUS_VLAN_TPID_VALID`标志设置到`tp_status`字段表示`tp_vlan_tpid`字段包含有效的VLAN TPID值。

  - 如何切换到`TPACKET_V2`：
    1. 替换`struct tpacket_hdr`为`struct tpacket2_hdr`。
    2. 查询头长度并保存。
    3. 将协议版本设置为2，并按常规方式设置环。
    4. 对于获取`sockaddr_ll`，使用`"（void *）hdr + TPACKET_ALIGN（hdrlen）"`代替`"（void *）hdr + TPACKET_ALIGN（sizeof（struct tpacket_hdr））"`。

- `TPACKET_V2`到`TPACKET_V3`：
  - RX_RING的灵活缓冲实现：
    1. 可以配置非静态帧大小的块。
    2. 读/轮询是在块级别（而不是包级别）进行的。
    3. 添加了轮询超时以避免用户空间在空闲链路上无限等待。
    4. 添加了用户可配置的参数：
      - 4.1 `block::timeout`
      - 4.2 `tpkt_hdr::sk_rxhash`
  - RX Hash数据可在用户空间获取。
  - TX_RING的概念与`TPACKET_V2`类似；使用`tpacket3_hdr`代替`tpacket2_hdr`，并使用`TPACKET3_HDRLEN`代替`TPACKET2_HDRLEN`。在当前实现中，`tp_next_offset`字段在`tpacket3_hdr`中必须设置为零，表示环不持有变长帧。具有非零`tp_next_offset`值的包将被丢弃。

AF_PACKET扇出模式
==================

在AF_PACKET扇出模式下，包接收可以在多个进程之间负载均衡。这也可以与packet套接字上的mmap结合使用。目前实现的扇出策略有：

- `PACKET_FANOUT_HASH`：根据skb的包哈希调度到套接字。
- `PACKET_FANOUT_LB`：按轮询调度到套接字。
- `PACKET_FANOUT_CPU`：根据包到达的CPU调度到套接字。
- `PACKET_FANOUT_RND`：随机选择调度到套接字。
- `PACKET_FANOUT_ROLLOVER`：如果一个套接字满了，则转到另一个。
- `PACKET_FANOUT_QM`：根据记录的队列映射调度到套接字。

David S. Miller提供的最小示例代码（尝试如"./test eth0 hash"、"./test eth0 lb"等）：

```c
// 示例代码省略
```

AF_PACKET的TPACKET_V3示例
=============================

AF_PACKET的TPACKET_V3环缓冲区可以通过自己的内存管理配置为使用非静态帧大小。它是基于块的，轮询工作在每个块的基础上，而不是像TPACKET_V2及其前身那样在整个环上进行。据说TPACKET_V3带来了以下好处：

- 减少约15%-20%的CPU使用率。
- 提高约20%的包捕获率。
- 提高约2倍的包密度。
- 端口聚合分析。
- 非静态帧大小以捕获整个包有效载荷。

因此，它似乎是与包扇出一起使用的良好候选者。Daniel Borkmann基于Chetan Loke的lolpcap提供的最小示例代码（用gcc -Wall -O2编译blob.c，尝试如"./a.out eth0"等）：

```c
// 示例代码省略
```

PACKET_QDISC_BYPASS
===================

如果需要以类似于pktgen的方式加载网络，您可能在创建套接字后设置以下选项：

```c
int one = 1;
setsockopt(fd, SOL_PACKET, PACKET_QDISC_BYPASS, &one, sizeof(one));
```

这会导致通过PF_PACKET发送的包绕过内核的qdisc层，并直接推送到驱动程序。这意味着包不会被缓冲，TC规则会被忽略，可能会增加丢失，并且这些包也不会再对其他PF_PACKET套接字可见。因此，请注意，通常这可用于压力测试系统各个组件。
默认情况下，`PACKET_QDISC_BYPASS` 是禁用的，需要在 `PF_PACKET` 套接字上显式启用。

`PACKET_TIMESTAMP`
=================

`PACKET_TIMESTAMP` 设置决定了映射到内存 (`mmap(2)`) 的 RX_RING 和 TX_RING 中的数据包元信息的时间戳来源。如果您的 NIC 支持硬件时间戳，则可以请求使用这些硬件时间戳。注意：您可能需要通过 `SIOCSHWTSTAMP` 启用硬件时间戳的生成（请参阅 `Documentation/networking/timestamping.rst` 中的相关信息）。

`PACKET_TIMESTAMP` 接受与 `SO_TIMESTAMPING` 相同的整数位字段：

```c
int req = SOF_TIMESTAMPING_RAW_HARDWARE;
setsockopt(fd, SOL_PACKET, PACKET_TIMESTAMP, (void *) &req, sizeof(req));
```

对于映射到内存的环形缓冲区，此类时间戳存储在 `tpacket{,2,3}_hdr` 结构的 `tp_sec` 和 `tp_{n,u}sec` 成员中。要确定报告了哪种类型的时间戳，可以通过 `tp_status` 字段中的以下可能位进行二进制或运算：
```c
TP_STATUS_TS_RAW_HARDWARE
TP_STATUS_TS_SOFTWARE
```

这些位等同于其对应的 `SOF_TIMESTAMPING_*` 值。对于 RX_RING，如果没有设置任何位（即未设置 `PACKET_TIMESTAMP`），则在 `PF_PACKET` 处理代码内部调用了软件回退（精度较低）。

获取 TX_RING 时间戳的工作方式如下：i) 填充环帧；ii) 调用 `sendto()`，例如在阻塞模式下；iii) 等待相关帧的状态更新或帧传递给应用程序；iv) 遍历帧以提取单个硬件/软件时间戳。
只有（！）当启用了传输时间戳时，这些位才会与 `TP_STATUS_AVAILABLE` 进行二进制或运算，因此您必须在应用程序中检查这一点（例如，首先检查 `!(tp_status & (TP_STATUS_SEND_REQUEST | TP_STATUS_SENDING))` 来查看该帧是否属于应用程序，然后在第二步中从 `tp_status` 提取时间戳类型）！

如果您不关心它们，即禁用了时间戳，那么检查 `TP_STATUS_AVAILABLE` 或 `TP_STATUS_WRONG_FORMAT` 就足够了。如果在 TX_RING 部分仅设置了 `TP_STATUS_AVAILABLE`，则 `tp_sec` 和 `tp_{n,u}sec` 成员中将不包含有效值。对于 TX_RING，默认情况下不会生成时间戳！

有关硬件时间戳的更多信息，请参阅 `include/linux/net_tstamp.h` 和 `Documentation/networking/timestamping.rst`。

杂项位
==================

- 数据包套接字与 Linux 套接字过滤器配合良好，因此您可能还希望查看 `Documentation/networking/filter.rst`。

感谢
======

   Jesse Brandeburg，修正了我的语法和拼写错误。
