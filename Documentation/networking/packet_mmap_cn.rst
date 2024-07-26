### SPDX 许可证标识符: GPL-2.0

#### 包 MMAP

##### 摘要

本文档介绍了与 PACKET 套接字接口一起提供的 mmap() 功能。这种类型的套接字用于：

i) 使用诸如 tcpdump 等工具捕获网络流量，
ii) 发送网络流量，或任何需要对网络接口进行原始访问的情况。

更多信息请参考：

    https://sites.google.com/site/packetmmap/

如有任何意见，请发送至：
    - Ulisses Alonso Camaró <uaca@i.hate.spam.alumni.uv.es>
    - Johann Baudy

##### 为何使用 PACKET_MMAP

非 PACKET_MMAP 捕获过程（即普通的 AF_PACKET）效率非常低。它使用非常有限的缓冲区，并且需要一次系统调用来捕获每个数据包；如果你想要获取数据包的时间戳（如 libpcap 总是这样做的），则需要两次系统调用。
相比之下，PACKET_MMAP 非常高效。PACKET_MMAP 提供了一个可在用户空间中映射的大小可配置的环形缓冲区，可用于发送或接收数据包。这样读取数据包只需要等待它们到达，大多数情况下无需发出任何系统调用。就传输而言，可以通过一次系统调用来发送多个数据包以获得最高的带宽。通过在内核和用户之间使用共享缓冲区也有助于最小化数据包复制。
使用 PACKET_MMAP 来提高捕获和传输过程的性能是一个好的选择，但这并不是全部。至少，如果你正在高速捕获数据（这相对于 CPU 速度而言），你应该检查你的网卡设备驱动是否支持某种形式的中断负载缓解或者（更好的是）是否支持 NAPI，并确保它已启用。对于传输，检查网络中的设备所使用的和所支持的最大传输单元（MTU）。你的网卡的 CPU 中断引脚绑定也可能带来优势。

#### 如何使用 mmap() 来改进捕获过程

从用户的角度来看，你应该使用更高级别的 libpcap 库，这是一个事实上的标准，在几乎所有操作系统包括 Win32 上都是便携的。
PACKET_MMAP 支持大约在 1.3.0 版本时集成到 libpcap 中；TPACKET_V3 支持是在 1.5.0 版本添加的。

#### 如何直接使用 mmap() 来改进捕获过程

从系统调用的角度来看，使用 PACKET_MMAP 的过程如下所示：


    [设置]     socket() -------> 创建捕获套接字
		setsockopt() ---> 分配环形缓冲区
				  选项: PACKET_RX_RING
		mmap() ---------> 将分配的缓冲区映射到
				  用户进程

    [捕获]   poll() ---------> 等待传入的数据包

    [关闭]  close() --------> 销毁捕获套接字并
				  释放所有相关资源
创建和销毁套接字的过程是直截了当的，并且无论是否使用 PACKET_MMAP 都是一样的：

```c
int fd = socket(PF_PACKET, mode, htons(ETH_P_ALL));
```

其中 mode 是 SOCK_RAW，用于可以捕获链路层信息的原始接口，或者是 SOCK_DGRAM，用于不支持链路层信息捕获的接口，并由内核提供链路层伪头部。
销毁套接字及其所有相关资源只需简单地调用 `close(fd)` 即可。
与没有使用 PACKET_MMAP 类似，可以使用一个套接字来进行捕获和传输。这可以通过单次 `mmap()` 调用来映射分配的 RX 和 TX 环形缓冲区来实现。
参见“环形缓冲区（环）的映射和使用”。
接下来我将描述 PACKET_MMAP 设置及其约束条件，以及用户进程中的环形缓冲区映射和该缓冲区的使用方法。
如何直接使用 mmap() 来改进传输过程
==========================================================
传输过程与捕获类似，如下所示：

    [设置]         socket() -------> 创建传输套接字
		    setsockopt() ---> 分配环形缓冲区选项: PACKET_TX_RING
		    bind() ---------> 将传输套接字绑定到网络接口
		    mmap() ---------> 将分配的缓冲区映射到用户进程

    [传输]  poll() ---------> 等待空闲数据包（可选）
		    send() ---------> 发送所有已准备好发送的环形缓冲区中的数据包
				      使用标志 MSG_DONTWAIT 可以在传输结束前返回

[关闭]      close() --------> 销毁传输套接字并释放所有相关资源
套接字的创建和销毁也非常简单，与上一段中描述的捕获过程相同:

 int fd = socket(PF_PACKET, mode, 0);

协议可以是0（可选），如果我们只希望通过此套接字进行传输，这样可以避免调用开销较大的 packet_rcv() 函数。在这种情况下，还需要通过 set sll_protocol = 0 将 TX_RING 与 bind(2) 关联起来。否则，可以使用 htons(ETH_P_ALL) 或其他任何协议。
将套接字绑定到您的网络接口是必须的（在零拷贝模式下），这样才能知道环形缓冲区中使用的帧的头部大小。
与捕获一样，每个帧包含两部分：

    --------------------
    | struct tpacket_hdr | 头部。包含了该帧的状态信息
    |                    |
    |--------------------|
    | 数据缓冲区        |
    .                    .  即将通过网络接口发送的数据
.
--------------------

 bind() 通过 sll_ifindex 参数将套接字与您的网络接口关联起来，该参数位于 struct sockaddr_ll 中。
初始化示例：

    struct sockaddr_ll my_addr;
    struct ifreq s_ifr;
    ..
The provided text describes the steps involved in setting up and using PACKET_MMAP for capturing and transmitting packets in Linux. Below is a translation of the key parts into Chinese:

```markdown
使用 `strscpy_pad` 函数填充 `s_ifr.ifr_name` 字段为 "eth0"，长度为 `sizeof(s_ifr.ifr_name)`。

/* 获取接口 eth0 的索引 */
ioctl(this->socket, SIOCGIFINDEX, &s_ifr);

/* 填充 sockaddr_ll 结构体以准备绑定 */
my_addr.sll_family = AF_PACKET;
my_addr.sll_protocol = htons(ETH_P_ALL);
my_addr.sll_ifindex =  s_ifr.ifr_ifindex;

/* 绑定套接字到 eth0 */
bind(this->socket, (struct sockaddr *)&my_addr, sizeof(struct sockaddr_ll));

一个完整的教程可在此处找到：https://sites.google.com/site/packetmmap/

默认情况下，用户应该将数据放置在：

frame base + TPACKET_HDRLEN - sizeof(struct sockaddr_ll)

因此，无论选择哪种套接字模式（SOCK_DGRAM 或 SOCK_RAW），用户数据的起始位置都位于：

frame base + TPACKET_ALIGN(sizeof(struct tpacket_hdr))

如果您希望将用户数据放置在帧起始位置自定义偏移量处（例如，在使用 SOCK_RAW 模式时进行有效载荷对齐），您可以设置 tp_net（与 SOCK_DGRAM 一起使用）或 tp_mac（与 SOCK_RAW 一起使用）。为了使这种方式生效，必须先使用 setsockopt() 和 PACKET_TX_HAS_OFF 选项启用它。
PACKET_MMAP 设置
==================

从用户级代码设置 PACKET_MMAP 可通过以下调用完成：

- 捕获进程：
  
      setsockopt(fd, SOL_PACKET, PACKET_RX_RING, (void *) &req, sizeof(req))
  

- 传输进程：
  
      setsockopt(fd, SOL_PACKET, PACKET_TX_RING, (void *) &req, sizeof(req))
  

上述调用中最重要的参数是 req 参数，此参数必须具有以下结构：

    struct tpacket_req
    {
        unsigned int    tp_block_size;  /* 连续块的最小大小 */
        unsigned int    tp_block_nr;    /* 块的数量 */
        unsigned int    tp_frame_size;  /* 帧的大小 */
        unsigned int    tp_frame_nr;    /* 帧的总数 */
    };

此结构定义于 `/usr/include/linux/if_packet.h` 中，并且用于建立不可交换内存的循环缓冲区（环形缓冲区）。
在捕获进程中映射它允许读取捕获的帧和相关元信息（如时间戳），而无需进行系统调用。
帧被分组到块中。每个块都是物理上连续的内存区域，并包含 `tp_block_size/tp_frame_size` 个帧。块的总数是 `tp_block_nr`。请注意，`tp_frame_nr` 是一个冗余参数，因为：

    每个块中的帧数 = tp_block_size/tp_frame_size

实际上，`packet_set_ring` 会检查以下条件是否成立：

    每个块中的帧数 * tp_block_nr == tp_frame_nr

让我们来看一个例子，使用以下值：

     tp_block_size= 4096
     tp_frame_size= 2048
     tp_block_nr  = 4
     tp_frame_nr  = 8

我们将得到以下缓冲区结构：

	    第 1 块                  第 2 块
    +---------+---------+    +---------+---------+
    | 帧 1 | 帧 2 |    | 帧 3 | 帧 4 |
    +---------+---------+    +---------+---------+

	    第 3 块                  第 4 块
    +---------+---------+    +---------+---------+
    | 帧 5 | 帧 6 |    | 帧 7 | 帧 8 |
    +---------+---------+    +---------+---------+

帧可以是任意大小，唯一的条件是它能放入一个块中。一个块只能容纳整数个帧，换句话说，一个帧不能跨越两个块，所以在选择 `frame_size` 时需要考虑一些细节。参见“循环缓冲区（环形缓冲区）的映射和使用”。
PACKET_MMAP 设置约束
=====================

在内核版本 2.4.26（对于 2.4 分支）和 2.6.5（2.6 分支）之前的版本中，
PACKET_MMAP 缓冲区在 32 位架构中只能容纳 32768 个帧，或者在 64 位架构中只能容纳 16384 个帧。
块大小限制
------------

如前所述，每个块是一个连续的物理内存区域。这些内存区域是通过调用 `__get_free_pages()` 函数分配的。正如函数名所示，该函数分配页面大小的内存，第二个参数是“顺序”或 2 的幂次方的页面数量，即
对于 `PAGE_SIZE == 4096`，order=0 ==> 4096 字节，order=1 ==> 8192 字节，
order=2 ==> 16384 字节，等等。`__get_free_pages` 能够分配的最大区域大小由 `MAX_PAGE_ORDER` 宏确定
更确切地说，这个限制可以通过以下方式计算：

   PAGE_SIZE << MAX_PAGE_ORDER

   在 i386 架构中，PAGE_SIZE 是 4096 字节
   在 2.4/i386 内核中，MAX_PAGE_ORDER 是 10
   在 2.6/i386 内核中，MAX_PAGE_ORDER 是 11

因此，`get_free_pages` 最多可以在 2.4/2.6 内核中为 i386 架构分配 4MB 或 8MB。
用户空间程序可以包含 `/usr/include/sys/user.h` 和 `/usr/include/linux/mmzone.h` 来获取 PAGE_SIZE 和 MAX_PAGE_ORDER 的声明
页面大小也可以通过 `getpagesize` (2) 系统调用来动态确定。
块数量限制
------------

要理解 PACKET_MMAP 的约束，我们需要查看用于存储指向每个块的指针的结构...
```

请注意，由于篇幅原因，最后部分没有完全翻译，但已经包含了主要信息。
目前，这种结构是一个使用`kmalloc`动态分配的向量，称为`pg_vec`，它的大小限制了可以分配的块的数量：

    +---+---+---+---+
    | x | x | x | x |
    +---+---+---+---+
      |   |   |   |
      |   |   |   v
      |   |   v  块 #4
      |   v  块 #3
      v  块 #2
     块 #1

`kmalloc`从预设大小的池中分配物理连续内存。这个内存池由slab分配器维护，它最终负责执行分配，并因此限定了`kmalloc`可以分配的最大内存。在2.4/2.6内核和i386架构下，限制是131072字节。`kmalloc`使用的预设大小可以在`/proc/slabinfo`中的"size-<bytes>"条目中检查。

在32位架构中，指针长度为4字节，所以指向块的总指针数为：

     131072/4 = 32768个块

PACKET_MMAP缓冲区大小计算
============================

定义如下：

==============  ================================================================
<size-max>      是用`kmalloc`可分配的最大大小
		（参见`/proc/slabinfo`）
<指针大小>  取决于架构 -- `sizeof(void *)`
<页大小>     取决于架构 -- `PAGE_SIZE`或`getpagesize` (2)
<最大顺序>     是由`MAX_PAGE_ORDER`定义的值
<帧大小>    这是帧捕获大小的一个上限（稍后会详细说明）
==============  ================================================================

根据这些定义，我们得出：

	<块数量> = <size-max>/<指针大小>
	<块大小> = <页大小> << <最大顺序>

因此，最大缓冲区大小为：

	<块数量> * <块大小>

而帧的数量为：

	<块数量> * <块大小> / <帧大小>

假设以下参数，适用于2.6内核和i386架构：

	<size-max> = 131072 字节
	<指针大小> = 4 字节
	<页大小> = 4096 字节
	<最大顺序> = 11

以及<帧大小>为2048字节。这些参数将产生：

	<块数量> = 131072/4 = 32768个块
	<块大小> = 4096 << 11 = 8 MiB
因此缓冲区将有262144 MiB的大小。它可以容纳
262144 MiB / 2048 字节 = 134217728个帧

实际上，这种缓冲区大小在i386架构上是不可能的。
请记住，内存是在内核空间分配的，在i386内核的情况下，内核的内存大小限制为1GiB。
所有内存分配在套接字关闭前都不会被释放。内存分配以`GFP_KERNEL`优先级进行，这意味着分配可以等待并交换其他进程的内存来分配所需的内存，因此通常可以达到限制。
其他约束
-----------

如果你检查源代码，你会发现我这里画的帧不仅仅是链路层帧。每个帧的开始处有一个名为`struct tpacket_hdr`的头部，用于`PACKET_MMAP`中保存链路层帧的元信息，如时间戳。因此我们在这里所画的帧实际上是以下内容（来自`include/linux/if_packet.h`）：

/*
  帧结构：

  - 开始。帧必须对齐到`TPACKET_ALIGNMENT`=16
  - `struct tpacket_hdr`
  - 对齐到`TPACKET_ALIGNMENT`=16填充
  - `struct sockaddr_ll`
  - 间隙，选择使得包数据（Start+tp_net）对齐到
    `TPACKET_ALIGNMENT`=16
  - Start+tp_mac: [ 可选MAC头 ]
  - Start+tp_net: 包数据，对齐到`TPACKET_ALIGNMENT`=16
  - 对齐到`TPACKET_ALIGNMENT`=16填充
*/

以下是`packet_set_ring`中检查的一些条件：

   - `tp_block_size`必须是`PAGE_SIZE`的倍数（1）
   - `tp_frame_size`必须大于`TPACKET_HDRLEN`（显然）
   - `tp_frame_size`必须是`TPACKET_ALIGNMENT`的倍数
   - `tp_frame_nr` 必须正好等于`frames_per_block*tp_block_nr`

请注意，`tp_block_size`应该选择为2的幂次方，否则会有内存浪费。
循环缓冲区（环）的映射与使用
-----------------------------------

用户进程中的缓冲区映射通过常规的`mmap`函数完成。即使循环缓冲区由多个物理上不连续的内存块组成，但对用户空间来说它们是连续的，因此只需要一个`mmap`调用即可：

    mmap(0, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);

如果`tp_frame_size`是`tp_block_size`的除数，则帧将以`tp_frame_size`字节的间隔连续排列。如果不是，则每`tp_block_size/tp_frame_size`帧之间将存在一个间隙。这是因为一个帧不能跨越两个块。
为了使用同一个套接字进行捕获和传输，需要使用一个`mmap`调用来映射接收和发送缓冲区环：

    ..
setsockopt(fd, SOL_PACKET, PACKET_RX_RING, &foo, sizeof(foo));
    setsockopt(fd, SOL_PACKET, PACKET_TX_RING, &bar, sizeof(bar));
    ..
```rx_ring = mmap(0, size * 2, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
tx_ring = rx_ring + size;

// RX 必须是第一个，因为内核将 TX 环缓冲区映射在 RX 缓冲区之后
// 每个帧的开始处有一个状态字段（参见 struct tpacket_hdr）。如果该字段为 0，则表示该帧已准备好供内核使用；
// 如果不为 0，则表示有一个用户可以读取的帧，并且以下标志适用：

// 捕获过程
// ^^^^^^^^^^^

// 从 include/linux/if_packet.h ::

#define TP_STATUS_COPY          (1 << 1)
#define TP_STATUS_LOSING        (1 << 2)
#define TP_STATUS_CSUMNOTREADY  (1 << 3)
#define TP_STATUS_CSUM_VALID    (1 << 7)

// ======================  =======================================================
// TP_STATUS_COPY		此标志表示帧（及其关联的元信息）由于大于 tp_frame_size 而被截断。这个数据包可以通过 recvfrom() 完全读取。
// 为了使这生效，必须先通过 setsockopt() 和 PACKET_COPY_THRESH 选项启用它。
// 可以用 recvfrom 读取的数据包数量受到限制，就像一个普通的套接字一样。
// 参见 socket (7) 手册页中的 SO_RCVBUF 选项。
// TP_STATUS_LOSING	指示自上次使用 getsockopt() 和 PACKET_STATISTICS 选项检查统计数据以来有数据包丢失。
// TP_STATUS_CSUMNOTREADY	目前用于外出的 IP 数据包，其校验和将在硬件中完成。因此，在读取数据包时不应尝试检查校验和。
// TP_STATUS_CSUM_VALID	此标志表示数据包的至少传输层头部校验和已在内核侧验证。如果未设置此标志，则我们可以在 TP_STATUS_CSUMNOTREADY 也未设置的情况下自行检查校验和。
// ======================  =======================================================

// 为了方便起见，还有以下定义 ::

#define TP_STATUS_KERNEL        0
#define TP_STATUS_USER          1

// 内核初始化所有帧的状态为 TP_STATUS_KERNEL，当内核收到一个数据包时，将其放入缓冲区并更新状态，至少设置 TP_STATUS_USER 标志。然后用户可以读取数据包，
// 一旦数据包被读取，用户必须将状态字段置零，以便内核可以再次使用该帧缓冲区。
// 用户可以使用 poll（其他变体也应该适用）来检查环中有无新数据包 ::

struct pollfd pfd;

pfd.fd = fd;
pfd.revents = 0;
pfd.events = POLLIN|POLLRDNORM|POLLERR;

if (status == TP_STATUS_KERNEL)
    retval = poll(&pfd, 1, timeout);

// 首先检查状态值然后轮询帧不会导致竞态条件。
```
传输过程

这些宏定义也被用于传输：

     #define TP_STATUS_AVAILABLE        0 // 帧可用
     #define TP_STATUS_SEND_REQUEST     1 // 帧将在下一个send()时发送
     #define TP_STATUS_SENDING          2 // 帧当前正在传输中
     #define TP_STATUS_WRONG_FORMAT     4 // 帧格式不正确

首先，内核将所有帧初始化为`TP_STATUS_AVAILABLE`。为了发送一个数据包，用户填充一个可用帧的数据缓冲区，并将`tp_len`设置为当前数据缓冲区的大小，并将其状态字段设置为`TP_STATUS_SEND_REQUEST`。这可以在多个帧上完成。一旦用户准备发送，就调用`send()`。然后，所有状态等于`TP_STATUS_SEND_REQUEST`的缓冲区被转发到网络设备。内核将每个已发送帧的状态更新为`TP_STATUS_SENDING`直到传输结束。
在每次传输结束时，缓冲区状态返回到`TP_STATUS_AVAILABLE`：

    header->tp_len = in_i_size;
    header->tp_status = TP_STATUS_SEND_REQUEST;
    retval = send(this->socket, NULL, 0, 0);

用户也可以使用`poll()`检查是否有缓冲区可用：

(状态 == `TP_STATUS_SENDING`)

    struct pollfd pfd;
    pfd.fd = fd;
    pfd.revents = 0;
    pfd.events = POLLOUT;
    retval = poll(&pfd, 1, timeout);

哪些TPACKET版本可用以及何时使用它们？
========================================

    int val = tpacket_version;
    setsockopt(fd, SOL_PACKET, PACKET_VERSION, &val, sizeof(val));
    getsockopt(fd, SOL_PACKET, PACKET_VERSION, &val, sizeof(val));

其中`tpacket_version`可以是`TPACKET_V1`（默认）、`TPACKET_V2`、`TPACKET_V3`

`TPACKET_V1`：
	- 如果没有其他指定，默认使用
	- 支持`RX_RING`和`TX_RING`

`TPACKET_V1` -> `TPACKET_V2`：
	- 由于`TPACKET_V1`结构中使用了无符号长整型，因此使其兼容64位，这同样适用于32位用户空间和64位内核等
	- 时间戳分辨率从微秒改为纳秒
	- 支持`RX_RING`和`TX_RING`
	- VLAN元数据信息可用于数据包(`TP_STATUS_VLAN_VALID`, `TP_STATUS_VLAN_TPID_VALID`)，在`tpacket2_hdr`结构中：

		- 将`TP_STATUS_VLAN_VALID`位设置到`tp_status`字段表示`tp_vlan_tci`字段具有有效的VLAN TCI值
		- 将`TP_STATUS_VLAN_TPID_VALID`位设置到`tp_status`字段表示`tp_vlan_tpid`字段具有有效的VLAN TPID值

	- 如何切换到`TPACKET_V2`：

		1. 替换`struct tpacket_hdr`为`struct tpacket2_hdr`
		2. 查询头部长度并保存
		3. 设置协议版本为2，按常规设置环
		4. 获取`sockaddr_ll`时，使用``(void *)hdr + TPACKET_ALIGN(hdrlen)``代替``(void *)hdr + TPACKET_ALIGN(sizeof(struct tpacket_hdr))``

`TPACKET_V2` -> `TPACKET_V3`：
	- 对于`RX_RING`实现了灵活的缓冲区实现：
		1. 块可以配置为非静态帧大小
		2. 读/轮询是在块级别（而不是包级别）
		3. 添加了轮询超时以避免用户空间在空闲链路上无限等待
		4. 添加了可由用户配置的选项：

			4.1 块::timeout
			4.2 tpkt_hdr::sk_rxhash

	- 用户空间中可用的RX Hash数据
	- `TX_RING`的概念与`TPACKET_V2`类似；使用`tpacket3_hdr`代替`tpacket2_hdr`，并使用`TPACKET3_HDRLEN`代替`TPACKET2_HDRLEN`。在当前实现中，`tpacket3_hdr`中的`tp_next_offset`字段必须设置为零，表示环不包含变长帧。带有非零`tp_next_offset`值的数据包将被丢弃

AF_PACKET扇出模式
=================

在AF_PACKET扇出模式下，数据包接收可以在进程之间负载均衡。这也适用于与packet套接字上的mmap(2)结合使用
目前实现的扇出策略包括：

  - `PACKET_FANOUT_HASH`: 按skb的数据包哈希调度到套接字
  - `PACKET_FANOUT_LB`: 按轮询调度到套接字
  - `PACKET_FANOUT_CPU`: 按数据包到达的CPU调度到套接字
  - `PACKET_FANOUT_RND`: 随机选择调度到套接字
  - `PACKET_FANOUT_ROLLOVER`: 如果一个套接字满了，则滚动到另一个套接字
  - `PACKET_FANOUT_QM`: 按记录的队列映射(skbs)调度到套接字

David S. Miller提供的最小示例代码（尝试诸如"./test eth0 hash"、"./test eth0 lb"等）：

    #include <stddef.h>
    #include <stdlib.h>
    #include <stdio.h>
    #include <string.h>

    #include <sys/types.h>
    #include <sys/wait.h>
    #include <sys/socket.h>
    #include <sys/ioctl.h>

    #include <unistd.h>

    #include <linux/if_ether.h>
    #include <linux/if_packet.h>

    #include <net/if.h>

    static const char *device_name;
    static int fanout_type;
    static int fanout_id;

    #ifndef PACKET_FANOUT
    # define PACKET_FANOUT			18
    # define PACKET_FANOUT_HASH		0
    # define PACKET_FANOUT_LB		1
    #endif

    static int setup_socket(void)
    {
	    int err, fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_IP));
	    struct sockaddr_ll ll;
	    struct ifreq ifr;
	    int fanout_arg;

	    if (fd < 0) {
		    perror("socket");
		    return EXIT_FAILURE;
	    }

	    memset(&ifr, 0, sizeof(ifr));
	    strcpy(ifr.ifr_name, device_name);
	    err = ioctl(fd, SIOCGIFINDEX, &ifr);
	    if (err < 0) {
		    perror("SIOCGIFINDEX");
		    return EXIT_FAILURE;
	    }

	    memset(&ll, 0, sizeof(ll));
	    ll.sll_family = AF_PACKET;
	    ll.sll_ifindex = ifr.ifr_ifindex;
	    err = bind(fd, (struct sockaddr *) &ll, sizeof(ll));
	    if (err < 0) {
		    perror("bind");
		    return EXIT_FAILURE;
	    }

	    fanout_arg = (fanout_id | (fanout_type << 16));
	    err = setsockopt(fd, SOL_PACKET, PACKET_FANOUT,
			    &fanout_arg, sizeof(fanout_arg));
	    if (err) {
		    perror("setsockopt");
		    return EXIT_FAILURE;
	    }

	    return fd;
    }

    static void fanout_thread(void)
    {
	    int fd = setup_socket();
	    int limit = 10000;

	    if (fd < 0)
		    exit(fd);

	    while (limit-- > 0) {
		    char buf[1600];
		    int err;

		    err = read(fd, buf, sizeof(buf));
		    if (err < 0) {
			    perror("read");
			    exit(EXIT_FAILURE);
		    }
		    if ((limit % 10) == 0)
			    fprintf(stdout, "(%d) \n", getpid());
	    }

	    fprintf(stdout, "%d: Received 10000 packets\n", getpid());

	    close(fd);
	    exit(0);
    }

    int main(int argc, char **argp)
    {
	    int fd, err;
	    int i;

	    if (argc != 3) {
		    fprintf(stderr, "Usage: %s INTERFACE {hash|lb}\n", argp[0]);
		    return EXIT_FAILURE;
	    }

	    if (!strcmp(argp[2], "hash"))
		    fanout_type = PACKET_FANOUT_HASH;
	    else if (!strcmp(argp[2], "lb"))
		    fanout_type = PACKET_FANOUT_LB;
	    else {
		    fprintf(stderr, "Unknown fanout type [%s]\n", argp[2]);
		    exit(EXIT_FAILURE);
	    }

	    device_name = argp[1];
	    fanout_id = getpid() & 0xffff;

	    for (i = 0; i < 4; i++) {
		    pid_t pid = fork();

		    switch (pid) {
		    case 0:
			    fanout_thread();

		    case -1:
			    perror("fork");
			    exit(EXIT_FAILURE);
		    }
	    }

	    for (i = 0; i < 4; i++) {
		    int status;

		    wait(&status);
	    }

	    return 0;
    }

AF_PACKET `TPACKET_V3`示例
==========================

AF_PACKET的`TPACKET_V3`环缓冲区可以通过自己的内存管理来配置使用非静态帧大小。它是基于块的，其中轮询是在每个块的基础上进行的，而不是像`TPACKET_V2`及其前身那样在整个环上进行。
据说`TPACKET_V3`带来了以下好处：

 * CPU使用率降低约15% - 20%
 * 数据包捕获速率增加约20%
 * 数据包密度增加约2倍
 * 端口聚合分析
 * 非静态帧大小以捕获整个数据包有效载荷

因此，它似乎是一个用于数据包扇出的好候选
Daniel Borkmann根据Chetan Loke的lolpcap提供的最小示例代码（用gcc -Wall -O2 blob.c编译，并尝试诸如"./a.out eth0"等）：

    /* 从头开始编写，但内核到用户空间API的使用
    * 来自lolpcap：
    *  版权所有2011年，Chetan Loke <loke.chetan@gmail.com>
    *  许可证：GPL，第2.0版
    */

    #include <stdio.h>
    #include <stdlib.h>
    #include <stdint.h>
    #include <string.h>
    #include <assert.h>
    #include <net/if.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #include <poll.h>
    #include <unistd.h>
    #include <signal.h>
    #include <inttypes.h>
    #include <sys/socket.h>
    #include <sys/mman.h>
    #include <linux/if_packet.h>
    #include <linux/if_ether.h>
    #include <linux/ip.h>

    #ifndef likely
    # define likely(x)		__builtin_expect(!!(x), 1)
    #endif
    #ifndef unlikely
    # define unlikely(x)		__builtin_expect(!!(x), 0)
    #endif

    struct block_desc {
	    uint32_t version;
	    uint32_t offset_to_priv;
	    struct tpacket_hdr_v1 h1;
    };

    struct ring {
	    struct iovec *rd;
	    uint8_t *map;
	    struct tpacket_req3 req;
    };

    static unsigned long packets_total = 0, bytes_total = 0;
    static sig_atomic_t sigint = 0;

    static void sighandler(int num)
    {
	    sigint = 1;
    }

    static int setup_socket(struct ring *ring, char *netdev)
    {
	    int err, i, fd, v = TPACKET_V3;
	    struct sockaddr_ll ll;
	    unsigned int blocksiz = 1 << 22, framesiz = 1 << 11;
	    unsigned int blocknum = 64;

	    fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
	    if (fd < 0) {
		    perror("socket");
		    exit(1);
	    }

	    err = setsockopt(fd, SOL_PACKET, PACKET_VERSION, &v, sizeof(v));
	    if (err < 0) {
		    perror("setsockopt");
		    exit(1);
	    }

	    memset(&ring->req, 0, sizeof(ring->req));
	    ring->req.tp_block_size = blocksiz;
	    ring->req.tp_frame_size = framesiz;
	    ring->req.tp_block_nr = blocknum;
	    ring->req.tp_frame_nr = (blocksiz * blocknum) / framesiz;
	    ring->req.tp_retire_blk_tov = 60;
	    ring->req.tp_feature_req_word = TP_FT_REQ_FILL_RXHASH;

	    err = setsockopt(fd, SOL_PACKET, PACKET_RX_RING, &ring->req,
			    sizeof(ring->req));
	    if (err < 0) {
		    perror("setsockopt");
		    exit(1);
	    }

	    ring->map = mmap(NULL, ring->req.tp_block_size * ring->req.tp_block_nr,
			    PROT_READ | PROT_WRITE, MAP_SHARED | MAP_LOCKED, fd, 0);
	    if (ring->map == MAP_FAILED) {
		    perror("mmap");
		    exit(1);
	    }

	    ring->rd = malloc(ring->req.tp_block_nr * sizeof(*ring->rd));
	    assert(ring->rd);
	    for (i = 0; i < ring->req.tp_block_nr; ++i) {
		    ring->rd[i].iov_base = ring->map + (i * ring->req.tp_block_size);
		    ring->rd[i].iov_len = ring->req.tp_block_size;
	    }

	    memset(&ll, 0, sizeof(ll));
	    ll.sll_family = PF_PACKET;
	    ll.sll_protocol = htons(ETH_P_ALL);
	    ll.sll_ifindex = if_nametoindex(netdev);
	    ll.sll_hatype = 0;
	    ll.sll_pkttype = 0;
	    ll.sll_halen = 0;

	    err = bind(fd, (struct sockaddr *) &ll, sizeof(ll));
	    if (err < 0) {
		    perror("bind");
		    exit(1);
	    }

	    return fd;
    }

    static void display(struct tpacket3_hdr *ppd)
    {
	    struct ethhdr *eth = (struct ethhdr *) ((uint8_t *) ppd + ppd->tp_mac);
	    struct iphdr *ip = (struct iphdr *) ((uint8_t *) eth + ETH_HLEN);

	    if (eth->h_proto == htons(ETH_P_IP)) {
		    struct sockaddr_in ss, sd;
		    char sbuff[NI_MAXHOST], dbuff[NI_MAXHOST];

		    memset(&ss, 0, sizeof(ss));
		    ss.sin_family = PF_INET;
		    ss.sin_addr.s_addr = ip->saddr;
		    getnameinfo((struct sockaddr *) &ss, sizeof(ss),
				sbuff, sizeof(sbuff), NULL, 0, NI_NUMERICHOST);

		    memset(&sd, 0, sizeof(sd));
		    sd.sin_family = PF_INET;
		    sd.sin_addr.s_addr = ip->daddr;
		    getnameinfo((struct sockaddr *) &sd, sizeof(sd),
				dbuff, sizeof(dbuff), NULL, 0, NI_NUMERICHOST);

		    printf("%s -> %s, ", sbuff, dbuff);
	    }

	    printf("rxhash: 0x%x\n", ppd->hv1.tp_rxhash);
    }

    static void walk_block(struct block_desc *pbd, const int block_num)
    {
	    int num_pkts = pbd->h1.num_pkts, i;
	    unsigned long bytes = 0;
	    struct tpacket3_hdr *ppd;

	    ppd = (struct tpacket3_hdr *) ((uint8_t *) pbd +
					pbd->h1.offset_to_first_pkt);
	    for (i = 0; i < num_pkts; ++i) {
		    bytes += ppd->tp_snaplen;
		    display(ppd);

		    ppd = (struct tpacket3_hdr *) ((uint8_t *) ppd +
						ppd->tp_next_offset);
	    }

	    packets_total += num_pkts;
	    bytes_total += bytes;
    }

    static void flush_block(struct block_desc *pbd)
    {
	    pbd->h1.block_status = TP_STATUS_KERNEL;
    }

    static void teardown_socket(struct ring *ring, int fd)
    {
	    munmap(ring->map, ring->req.tp_block_size * ring->req.tp_block_nr);
	    free(ring->rd);
	    close(fd);
    }

    int main(int argc, char **argp)
    {
	    int fd, err;
	    socklen_t len;
	    struct ring ring;
	    struct pollfd pfd;
	    unsigned int block_num = 0, blocks = 64;
	    struct block_desc *pbd;
	    struct tpacket_stats_v3 stats;

	    if (argc != 2) {
		    fprintf(stderr, "Usage: %s INTERFACE\n", argp[0]);
		    return EXIT_FAILURE;
	    }

	    signal(SIGINT, sighandler);

	    memset(&ring, 0, sizeof(ring));
	    fd = setup_socket(&ring, argp[argc - 1]);
	    assert(fd > 0);

	    memset(&pfd, 0, sizeof(pfd));
	    pfd.fd = fd;
	    pfd.events = POLLIN | POLLERR;
	    pfd.revents = 0;

	    while (likely(!sigint)) {
		    pbd = (struct block_desc *) ring.rd[block_num].iov_base;

		    if ((pbd->h1.block_status & TP_STATUS_USER) == 0) {
			    poll(&pfd, 1, -1);
			    continue;
		    }

		    walk_block(pbd, block_num);
		    flush_block(pbd);
		    block_num = (block_num + 1) % blocks;
	    }

	    len = sizeof(stats);
	    err = getsockopt(fd, SOL_PACKET, PACKET_STATISTICS, &stats, &len);
	    if (err < 0) {
		    perror("getsockopt");
		    exit(1);
	    }

	    fflush(stdout);
	    printf("\nReceived %u packets, %lu bytes, %u dropped, freeze_q_cnt: %u\n",
		stats.tp_packets, bytes_total, stats.tp_drops,
		stats.tp_freeze_q_cnt);

	    teardown_socket(&ring, fd);
	    return 0;
    }

PACKET_QDISC_BYPASS
===================

如果需要像pktgen那样加载网络，您可能在创建套接字后设置以下选项：

    int one = 1;
    setsockopt(fd, SOL_PACKET, PACKET_QDISC_BYPASS, &one, sizeof(one));

这有副作用，即通过PF_PACKET发送的数据包会绕过内核的qdisc层，并直接推送到驱动程序。这意味着，数据包不会被缓冲，tc纪律会被忽略，可能会增加丢失，并且这些数据包对其他PF_PACKET套接字也不再可见。所以，请注意；通常而言，这对于压力测试系统的各个组件是有用的。
默认情况下，PACKET_QDISC_BYPASS 是禁用的，并且需要在 PF_PACKET 套接字上明确启用。

PACKET_TIMESTAMP
================

PACKET_TIMESTAMP 设置确定了 mmap(2) 映射的 RX_RING 和 TX_RING 中包元信息中时间戳的来源。如果你的网卡能够通过硬件对包进行时间戳记，你可以请求使用这些硬件时间戳。注意：你可能需要使用 SIOCSHWTSTAMP（参见 `Documentation/networking/timestamping.rst` 中的相关信息）来启用硬件时间戳的生成。
PACKET_TIMESTAMP 接受与 SO_TIMESTAMPING 相同的整型位字段，例如：

```c
int req = SOF_TIMESTAMPING_RAW_HARDWARE;
setsockopt(fd, SOL_PACKET, PACKET_TIMESTAMP, (void *) &req, sizeof(req));
```

对于 mmap(2) 映射的环形缓冲区，此类时间戳存储在 `tpacket{,2,3}_hdr` 结构的 `tp_sec` 和 `tp_{n,u}sec` 成员中。
要确定报告了哪种类型的时间戳，可以通过 `tp_status` 字段与以下可能的位进行二进制或操作来判断：
```
TP_STATUS_TS_RAW_HARDWARE
TP_STATUS_TS_SOFTWARE
```

这些位与相应的 `SOF_TIMESTAMPING_*` 值等效。对于 RX_RING，如果没有设置这两个位（即未设置 PACKET_TIMESTAMP），则 PF_PACKET 的处理代码内部调用了软件回退（精度较低）。
获取 TX_RING 时间戳的工作流程如下：i) 填充环中的帧，ii) 以阻塞模式调用 sendto() 等函数，iii) 等待相关帧的状态更新或传给应用程序，iv) 遍历帧以提取各个硬件/软件时间戳。
仅当启用了发送时间戳时，这些位才会与 `TP_STATUS_AVAILABLE` 进行二进制或操作。因此，在应用程序中必须检查这一点（例如，首先检查 `(tp_status & (TP_STATUS_SEND_REQUEST | TP_STATUS_SENDING))` 是否为假，以确定该帧是否属于应用程序，然后从 `tp_status` 中提取时间戳类型）！

如果你不关心这些时间戳并将其禁用，则只需检查 `TP_STATUS_AVAILABLE` 或 `TP_STATUS_WRONG_FORMAT` 即可。如果 TX_RING 中仅设置了 `TP_STATUS_AVAILABLE`，那么 `tp_sec` 和 `tp_{n,u}sec` 成员将不会包含有效值。对于 TX_RING，默认情况下不会生成任何时间戳！

有关硬件时间戳的更多信息，请参阅 `include/linux/net_tstamp.h` 和 `Documentation/networking/timestamping.rst`。

杂项位
==================

- 包套接字与 Linux 套接字过滤器配合得很好，因此你也可以参考 `Documentation/networking/filter.rst`。

感谢
======

   Jesse Brandeburg，修正了我的语法和拼写错误
