### SPDX 许可证标识符: GPL-2.0

#### AF_XDP
#### 概览

AF_XDP 是一个针对高性能数据包处理进行了优化的地址族。
本文档假设读者熟悉 BPF 和 XDP。如果不熟悉，Cilium 项目提供了一个优秀的参考指南：http://cilium.readthedocs.io/en/latest/bpf/
通过使用 XDP 程序中的 XDP_REDIRECT 动作，程序可以将入站帧重定向到其他启用了 XDP 的网络设备上，使用 `bpf_redirect_map()` 函数实现。AF_XDP 套接字使 XDP 程序能够将帧重定向到用户空间应用程序中的内存缓冲区成为可能。
AF_XDP 套接字（XSK）是通过标准的 `socket()` 系统调用来创建的。每个 XSK 都关联有两个环：接收环（RX 环）和发送环（TX 环）。套接字可以在 RX 环上接收数据包，并可以在 TX 环上发送数据包。这些环分别通过设置选项 XDP_RX_RING 和 XDP_TX_RING 进行注册和配置大小。每个套接字至少需要有一个环。RX 或 TX 描述符环指向位于称为 UMEM 的内存区域中的数据缓冲区。RX 和 TX 可以共享同一个 UMEM，这样数据包就不需要在 RX 和 TX 之间进行复制。此外，如果由于可能的重传而需要暂时保留数据包，指向该数据包的描述符可以被更改以指向另一个并立即重复使用。这同样避免了数据复制。
UMEM 由数量相等的多个块组成。环中的一个描述符通过引用其地址来引用一个帧。地址只是在整个 UMEM 区域内的偏移量。用户空间使用任何认为最合适的手段（如 `malloc`、`mmap`、大页等）为 UMEM 分配内存。然后使用新的设置选项 `XDP_UMEM_REG` 将这个内存区域注册给内核。UMEM 也有两个环：填充环（FILL 环）和完成环（COMPLETION 环）。填充环用于应用程序向下发送地址，供内核填充 RX 数据包数据。一旦每个数据包被接收，这些帧的引用就会出现在 RX 环中。另一方面，完成环包含内核已完全传输的帧地址，现在可以被用户空间重新使用，无论是用于 TX 还是 RX。因此，出现在完成环中的帧地址是之前使用 TX 环传输的地址。简而言之，RX 和 FILL 环用于 RX 路径，TX 和 COMPLETION 环用于 TX 路径。
最后，通过 `bind()` 调用将套接字绑定到设备及其特定的队列 ID 上，直到绑定完成后流量才会开始流动。
UMEM 可以根据需要在进程间共享。如果一个进程想要这样做，它只需跳过 UMEM 及其相应的两个环的注册步骤，在 `bind` 调用中设置 `XDP_SHARED_UMEM` 标志，并提交与其共享 UMEM 的进程的 XSK 以及自身新创建的 XSK 套接字。然后新进程将在自己的 RX 环中收到指向共享 UMEM 的帧地址引用。请注意，由于环结构是单消费者/单生产者（出于性能原因），新进程必须创建自己的带有相关 RX 和 TX 环的套接字，因为它不能与另一个进程共享这些环。这也是为什么每个 UMEM 只有一组填充环和完成环的原因。处理 UMEM 的责任由单一进程承担。
那么，数据包是如何从 XDP 程序分配到 XSK 的呢？存在一个名为 XSKMAP（或 BPF_MAP_TYPE_XSKMAP）的 BPF 映射。用户空间应用程序可以将 XSK 放置在这个映射的任意位置。XDP 程序可以将数据包重定向到这个映射中的特定索引，此时 XDP 会验证映射中的 XSK 是否确实绑定到了该设备和队列号上。如果不是，则丢弃数据包。如果该索引处的映射为空，也会丢弃数据包。这也意味着目前必须加载一个 XDP 程序（并且至少有一个 XSK 在 XSKMAP 中），才能将任何流量传递到用户空间通过 XSK。
AF_XDP 可以在两种不同的模式下运行：XDP_SKB 和 XDP_DRV。如果驱动不支持 XDP，或者在加载 XDP 程序时明确选择了 XDP_SKB，则使用 XDP_SKB 模式，该模式使用 SKB 并结合通用 XDP 支持将数据复制到用户空间。这是一种适用于任何网络设备的回退模式。另一方面，如果驱动支持 XDP，AF_XDP 代码将利用这一点以提供更好的性能，但仍然需要将数据复制到用户空间。

#### 概念

为了使用 AF_XDP 套接字，需要设置一些相关的对象。以下各节将解释这些对象及其选项。
为了了解 AF_XDP 的工作原理，您还可以参阅 2018 年 Linux Plumbers 会议的相关论文：
http://vger.kernel.org/lpc_net2018_talks/lpc18_paper_af_xdp_perf-v2.pdf。请不要参考 2017 年关于“AF_PACKET v4”的论文，那是 AF_XDP 的首次尝试。自那时以来几乎所有内容都已改变。Jonathan Corbet 还在 LWN 上写了一篇优秀的文章，“使用 AF_XDP 加速网络”。该文章可在此处找到：https://lwn.net/Articles/750845/

UMEM
----

UMEM 是一片连续虚拟内存区域，被划分为大小相等的帧。一个 UMEM 与一个网卡设备和该设备的特定队列 ID 关联。通过使用 XDP_UMEM_REG setsockopt 系统调用来创建并配置 UMEM（块大小、头部预留空间、起始地址及大小）。UMEM 通过 bind() 系统调用绑定到特定的网卡设备及其队列 ID。
一个 AF_XDP 套接字链接到单个 UMEM，但一个 UMEM 可以拥有多个 AF_XDP 套接字。要共享由套接字 A 创建的 UMEM，下一个套接字 B 可以通过设置 sockaddr_xdp 结构中的 sxdp_flags 成员为 XDP_SHARED_UMEM 标志，并将 A 的文件描述符传递给 sockaddr_xdp 结构中的 sxdp_shared_umem_fd 成员来实现。
UMEM 包含两个单生产者/单消费者环形缓冲区，用于在内核与用户空间应用之间转移 UMEM 帧的所有权。

环形缓冲区
-----

存在四种不同类型的环形缓冲区：FILL、COMPLETION、RX 和 TX。所有环形缓冲区都是单生产者/单消费者模式，因此用户空间应用需要显式地同步多个进程/线程对它们的读写操作。
UMEM 使用两个环形缓冲区：FILL 和 COMPLETION。每个与 UMEM 关联的套接字必须有一个 RX 队列、TX 队列或两者都有。例如，假设有四个套接字（都在进行 TX 和 RX 操作）。那么就会有一个 FILL 环形缓冲区、一个 COMPLETION 环形缓冲区、四个 TX 环形缓冲区和四个 RX 环形缓冲区。
这些环形缓冲区是基于头部（生产者）/尾部（消费者）的结构。生产者在 struct xdp_ring 的 producer 成员所指的索引位置写入数据，并增加 producer 索引。消费者从 struct xdp_ring 的 consumer 成员所指的索引位置读取数据，并增加 consumer 索引。
通过 _RING setsockopt 系统调用来配置和创建这些环形缓冲区，并使用适当的偏移量通过 mmap() 映射到用户空间（XDP_PGOFF_RX_RING、XDP_PGOFF_TX_RING、XDP_UMEM_PGOFF_FILL_RING 和 XDP_UMEM_PGOFF_COMPLETION_RING）。
环形缓冲区的大小必须是 2 的幂次方。

UMEM FILL 环形缓冲区
~~~~~~~~~~~~~~

FILL 环形缓冲区用于从用户空间向内核空间转移 UMEM 帧的所有权。UMEM 地址通过环形缓冲区传递。例如，如果 UMEM 的大小为 64KB，每个块为 4KB，则 UMEM 具有 16 个块，可以传递 0 到 64KB 之间的地址。
传递给内核的帧用于入站路径（RX 环形缓冲区）。
用户应用程序为这个环形缓冲区生成 UMEM 地址。需要注意的是，如果
以对齐块模式运行应用程序，则内核将屏蔽
传入地址。例如，对于 2K 的块大小，log2(2048) 最低位
地址会被屏蔽掉，这意味着 2048、2050 和 3000 指向
相同的块。如果用户应用程序在非对齐
块模式下运行，则传入地址将保持不变。
UMEM 完成环形缓冲区
~~~~~~~~~~~~~~~~~~~~

完成环形缓冲区用于将 UMEM 帧的所有权从
内核空间转移到用户空间。就像填充环一样，使用 UMEM 索引
从内核传递到用户空间的帧是已经被发送（TX 环形缓冲区）并且可以被用户空间再次使用的帧。
用户应用程序从这个环形缓冲区消费 UMEM 地址。
RX 环形缓冲区
~~~~~~~

RX 环形缓冲区是一个套接字的接收端。环中的每一项都是一个 xdp_desc 结构体描述符。该描述符包含 UMEM 偏移量
（地址）和数据长度（len）。
如果没有帧通过填充环传递给内核，则不会出现任何
（或无法出现）描述符在 RX 环形缓冲区中。
用户应用程序从这个环形缓冲区消费 xdp_desc 结构体描述符。
TX 环形缓冲区
~~~~~~~

TX 环形缓冲区用于发送帧。xdp_desc 结构体描述符被填满（索引、长度和偏移量），并传递到环形缓冲区中。
要开始传输，需要调用 sendmsg() 系统调用。这在未来可能会放宽。
用户应用程序为这个环生成 `struct xdp_desc` 描述符。
Libbpf
======

Libbpf 是一个用于 eBPF 和 XDP 的辅助库，它使得使用这些技术变得更为简单。它还包含了一些特定的辅助函数，在 `tools/lib/bpf/xsk.h` 中，以方便使用 AF_XDP。它包含了两种类型的函数：一种可用于简化 AF_XDP 套接字设置的过程，另一种则可在数据平面中安全快速地访问环。要了解如何使用此 API 的示例，请参阅 `samples/bpf/xdpsock_usr.c` 中的示例程序，该程序在设置和数据平面操作中都使用了 libbpf。除非您已成为高级用户，否则我们建议您使用这个库，这将使您的程序变得更加简单。
XSKMAP / BPF_MAP_TYPE_XSKMAP
============================

在 XDP 方面，有一个名为 BPF_MAP_TYPE_XSKMAP（简称 XSKMAP）的 BPF 地图类型，它与 `bpf_redirect_map()` 结合使用，以将入站帧传递给套接字。
用户应用程序通过 `bpf()` 系统调用将套接字插入到地图中。
需要注意的是，如果 XDP 程序试图重定向到与队列配置和网络设备不匹配的套接字，则帧将被丢弃。例如，AF_XDP 套接字绑定到网络设备 eth0 和队列 17。只有执行于 eth0 和队列 17 的 XDP 程序才能成功地将数据传送给套接字。请参考示例应用（位于 `samples/bpf/` 目录下）以获取示例。
配置标志和套接字选项
======================

以下是可用于控制和监控 AF_XDP 套接字行为的各种配置标志：
XDP_COPY 和 XDP_ZEROCOPY 绑定标志
------------------------------------

当您绑定到一个套接字时，内核首先尝试使用零复制模式。如果无法支持零复制，它将回退到使用复制模式，即把所有数据包复制到用户空间。但如果您想强制某种模式，可以使用以下标志。如果您在绑定调用中传递 XDP_COPY 标志，内核将强制套接字进入复制模式。如果无法使用复制模式，绑定调用将以错误失败。相反地，XDP_ZEROCOPY 标志将强制套接字进入零复制模式或导致失败。
XDP_SHARED_UMEM 绑定标志
-------------------------

此标志允许您将多个套接字绑定到同一 UMEM 上。它适用于相同的队列 ID、不同的队列 ID 以及不同的网络设备。在这种模式下，每个套接字仍然拥有它们自己的接收 (RX) 和发送 (TX) 环，但您将有一个或多个填充 (FILL) 和完成 (COMPLETION) 环对。您需要为每个独特的网络设备和队列 ID 对创建一对这样的环。
从希望在相同网络设备和队列 ID 之间共享 UMEM 的情况开始。与第一个创建的套接字绑定的 UMEM 将只有一个 FILL 环和一个 COMPLETION 环，因为我们只绑定到了一个唯一的网络设备、队列 ID 组合。要使用这种模式，先创建第一个套接字并以常规方式绑定它。然后创建第二个套接字，并创建一个 RX 和一个 TX 环（或者至少创建其中一个），但不需要创建 FILL 或 COMPLETION 环，因为将使用来自第一个套接字的环。在绑定调用中，设置 XDP_SHARED_UMEM 选项，并在 sxdp_shared_umem_fd 字段中提供初始套接字的文件描述符。您可以以这种方式附加任意数量的额外套接字。
那么数据包将到达哪个套接字？这由XDP程序决定。将所有套接字放入XSK_MAP中，并仅指示你希望将每个数据包发送到数组中的哪个索引。下面展示了一个简单的轮询分发数据包的例子：

```c
#include <linux/bpf.h>
#include "bpf_helpers.h"

#define MAX_SOCKS 16

struct {
    __uint(type, BPF_MAP_TYPE_XSKMAP);
    __uint(max_entries, MAX_SOCKS);
    __uint(key_size, sizeof(int));
    __uint(value_size, sizeof(int));
} xsks_map SEC(".maps");

static unsigned int rr;

SEC("xdp_sock") int xdp_sock_prog(struct xdp_md *ctx)
{
    rr = (rr + 1) & (MAX_SOCKS - 1);

    return bpf_redirect_map(&xsks_map, rr, XDP_DROP);
}
```

请注意，由于只有一个FILL和COMPLETION环形缓冲区集，并且它们是单生产者、单消费者的环形缓冲区，你需要确保多个进程或线程不会同时使用这些环形缓冲区。在当前的libbpf代码中没有同步原语来保护多个用户。如果创建一个以上的套接字与同一个UMEM关联，libbpf会使用这种模式。但是，请注意，在xsk_socket__create调用时需要提供XSK_LIBBPF_FLAGS__INHIBIT_PROG_LOAD libbpf标志，并加载你自己的XDP程序，因为libbpf中没有内置的程序来为你路由流量。
第二种情况是你在不同的队列ID和/或网络设备之间共享一个UMEM。在这种情况下，你需要为每个唯一的netdev,queue_id对创建一个FILL环形缓冲区和一个COMPLETION环形缓冲区。假设你想在同一网络设备上创建两个绑定到不同队列ID的套接字。以正常方式创建并绑定第一个套接字。创建第二个套接字并创建一个RX环形缓冲区和一个TX环形缓冲区，或者至少创建其中一个，然后为这个套接字创建一个FILL环形缓冲区和一个COMPLETION环形缓冲区。在bind调用中设置XDP_SHARED_UMEM选项，并在sxdp_shared_umem_fd字段中提供初始套接字的文件描述符，因为你已经在该套接字上注册了UMEM。这两个套接字现在将共享同一个UMEM。
在这种情况下，不需要像前面案例那样提供一个XDP程序（其中套接字绑定到了相同的队列ID和设备）。相反，利用网卡的数据包导向能力将数据包导向正确的队列。在前面的例子中，只有在一个队列上共享套接字，因此网卡无法进行这种导向；它只能在队列之间导向。
在libbpf中，你需要使用xsk_socket__create_shared() API，因为它会为你创建并绑定到共享UMEM的一个FILL环形缓冲区和一个COMPLETION环形缓冲区。你可以为创建的所有套接字使用此函数，或者只用于第二个及以后的套接字，并为第一个套接字使用xsk_socket__create()。这两种方法都能得到相同的结果。
请注意，一个UMEM可以在同一队列ID和设备上的套接字之间共享，也可以在同一个设备的不同队列之间共享，甚至可以在不同的设备之间共享。

### XDP_USE_NEED_WAKEUP 绑定标志

此选项支持一个新的标志 `need_wakeup`，该标志存在于FILL环形缓冲区和TX环形缓冲区中，即用户空间作为生产者的环形缓冲区。当在bind调用中设置此选项时，如果内核需要通过系统调用来明确唤醒以继续处理数据包，则 `need_wakeup` 标志会被设置。如果该标志为零，则不需要系统调用。
如果FILL环形缓冲区设置了此标志，应用程序需要调用 `poll()` 才能继续在RX环形缓冲区接收数据包。例如，当内核检测到FILL环形缓冲区上没有更多缓冲区，而且NIC的RX硬件环形缓冲区上也没有剩余缓冲区时，就会发生这种情况。此时中断被关闭，因为NIC无法接收任何数据包（因为没有缓冲区可以放置数据包），并且设置 `need_wakeup` 标志以便用户空间可以在FILL环形缓冲区上放置缓冲区，然后调用 `poll()` 以便内核驱动器可以将这些缓冲区放在硬件环形缓冲区上并开始接收数据包。
如果TX环形缓冲区设置了此标志，则表示应用程序需要显式通知内核发送TX环形缓冲区上的任何数据包。这可以通过 `poll()` 调用实现，就像在RX路径中一样，或者通过调用 `sendto()` 实现。
如何使用此标志的一个示例可以在 `samples/bpf/xdpsock_user.c` 中找到。对于TX路径，使用libbpf辅助函数的示例看起来像这样：

```c
if (xsk_ring_prod__needs_wakeup(&my_tx_ring))
    sendto(xsk_socket__fd(xsk_handle), NULL, 0, MSG_DONTWAIT, NULL, 0);
```

也就是说，仅在标志设置的情况下使用系统调用。
我们建议您始终开启此模式，因为它通常能带来更好的性能，特别是在应用程序和驱动程序运行在同一核心的情况下，即使在应用程序和内核驱动程序使用不同核心时也是如此，因为它减少了TX路径所需的系统调用数量。
XDP_{RX|TX|UMEM_FILL|UMEM_COMPLETION}_RING 设置套接字选项
------------------------------------------------------

这些设置套接字选项分别设置了 RX、TX、FILL 和 COMPLETION 环中的描述符数量。至少需要设置 RX 和 TX 环中的一个的大小。如果您同时设置了这两个环，那么您的应用程序将能够同时接收和发送流量；但如果您只需要执行其中一种操作，则可以通过仅设置其中一个环来节省资源。FILL 环和 COMPLETION 环都是必需的，因为您需要有一个 UMEM 与您的套接字绑定。但是，如果使用了 XDP_SHARED_UMEM 标志，则除了第一个套接字外的任何其他套接字都没有 UMEM，因此在这种情况下不应创建任何 FILL 或 COMPLETION 环，而是使用共享 UMEM 中的那些环。请注意，这些环是单生产者单消费者的，所以不要尝试同时从多个进程中访问它们。请参阅 XDP_SHARED_UMEM 部分。
在 libbpf 中，您可以为 Rx-only 和 Tx-only 套接字提供 NULL 参数给 xsk_socket__create 函数的 rx 和 tx 参数，从而创建只接收或只发送的套接字。
如果您创建了一个只发送的套接字，我们建议您不要向填充环中添加任何数据包。如果您这样做，驱动程序可能会误以为您要接收某些数据，但实际上并不会接收，这可能对性能产生负面影响。
XDP_UMEM_REG 设置套接字选项
-----------------------

此设置套接字选项将 UMEM 注册到一个套接字。这是包含所有数据包可以驻留的缓冲区的区域。该调用需要这个区域的起始指针和其大小。此外，它还有一个名为 chunk_size 的参数，表示 UMEM 被划分的大小。目前只能是 2K 或 4K。如果您有一个 128K 大小的 UMEM 区域且 chunk 大小为 2K，这意味着您可以在 UMEM 区域中最多容纳 128K / 2K = 64 个数据包，并且您的最大数据包大小可以是 2K。
还可以设置 UMEM 中每个单独缓冲区的头部空间。如果您将其设置为 N 字节，意味着数据包将在缓冲区的第 N 字节开始，留下前 N 字节供应用程序使用。最后一个是标志字段，但每种 UMEM 标志将在单独的部分中处理。
SO_BINDTODEVICE 设置套接字选项
--------------------------

这是一个通用的 SOL_SOCKET 选项，可用于将 AF_XDP 套接字绑定到特定网络接口。当套接字由特权进程创建并传递给非特权进程时，此选项很有用。
一旦设置了此选项，内核会拒绝尝试将该套接字绑定到另一个接口的尝试。更新值需要 CAP_NET_RAW 权限。
XDP_STATISTICS 获取套接字选项
-------------------------

获取用于调试目的的套接字丢弃统计信息。支持的统计信息如下：

.. code-block:: c

   struct xdp_statistics {
       __u64 rx_dropped;    /* 因除无效描述符以外的原因被丢弃的数据包 */
       __u64 rx_invalid_descs; /* 因无效描述符被丢弃的数据包 */
       __u64 tx_invalid_descs; /* 因无效描述符被丢弃的数据包 */
   };

XDP_OPTIONS 获取套接字选项
----------------------

从 XDP 套接字获取选项。目前为止唯一支持的是 XDP_OPTIONS_ZEROCOPY，它可以告诉您零拷贝是否已启用。
多缓冲支持
====================

通过多缓冲支持，使用 AF_XDP 套接字的程序可以在复制和零拷贝模式下接收和传输由多个缓冲区组成的数据包。例如，一个数据包可以由两个帧/缓冲区组成，一个包含头部，另一个包含数据；或者一个 9K 以太网巨型帧可以通过链接三个 4K 帧来构建。
一些定义：

* 一个数据包由一个或多个帧组成。

* AF_XDP 环中的描述符始终指向单个帧。如果数据包仅由单个帧组成，该描述符则指向整个数据包。

为了在 AF_XDP 套接字中启用多缓冲支持，请使用新的绑定标志 `XDP_USE_SG`。如果不提供此标志，则所有多缓冲数据包将像以前一样被丢弃。请注意，加载的 XDP 程序也需要处于多缓冲模式。可以通过将使用的 XDP 程序的部分名称设置为 "xdp.frags" 来实现这一点。

为了表示由多个帧组成的数据包，引入了一个新的标志 `XDP_PKT_CONTD` 在接收（Rx）和发送（Tx）描述符的选项字段中。如果其值为真（1），则表示数据包将继续到下一个描述符；如果为假（0），则表示这是数据包的最后一个描述符。为什么与许多网卡中找到的包结束（EOP）标志的逻辑相反？仅仅是为了保持与非多缓冲应用程序的兼容性，这些应用程序在接收时会将这个位设置为假（0），且应用在发送时将选项字段设置为零，因为其他任何值都会被视为无效描述符。

以下是向 AF_XDP 发送环中生产由多个帧组成的数据包的语义：

* 当发现无效描述符时，该数据包中的其他描述符/帧会被标记为无效且未完成。下一个描述符被视为新数据包的开始，即使这不是预期的行为（因为我们无法猜测意图）。如同之前所述，如果你的程序生成了无效描述符，那么必须修复其中的错误。
* 长度为零的描述符被视为无效描述符。
* 对于复制模式，一个数据包中支持的最大帧数等于 `CONFIG_MAX_SKB_FRAGS + 1`。如果超过了这个限制，那么迄今为止积累的所有描述符将被丢弃并视为无效。为了使应用程序能在任何系统上运行，无论其配置如何，应将分片数量限制为 18，因为配置的最小值是 17。
* 对于零复制模式，限制取决于网卡硬件支持的数量。通常至少为五个，基于我们检查过的网卡。我们有意选择不对零复制模式强制执行固定限制（例如 `CONFIG_MAX_SKB_FRAGS + 1`），因为这会导致在幕后进行复制操作以适应网卡支持的限制，这违背了零复制模式的目的。如何探测这一限制在“探测多缓冲支持”部分中有解释。

在复制模式下的接收路径中，xsk 核心根据需要将 XDP 数据复制到多个描述符中，并按照前面详述的方式设置 `XDP_PKT_CONTD` 标志。零复制模式的工作原理相同，只是数据不会被复制。当应用程序收到一个设置了 `XDP_PKT_CONTD` 标志为 1 的描述符时，这意味着数据包由多个缓冲区组成，并且它将在下一个描述符中继续。当收到 `XDP_PKT_CONTD` 为 0 的描述符时，意味着这是数据包的最后一个缓冲区。AF_XDP 保证只有完整的数据包（数据包中的所有帧）才会发送给应用程序。如果 AF_XDP 接收环中没有足够的空间，数据包的所有帧都将被丢弃。

如果应用程序使用 libxdp 等接口读取一批描述符，则不能保证这批描述符会以一个完整的数据包结束。它可能在数据包中间结束，而该数据包的其余缓冲区将在下一批的开始处到达，因为 libxdp 接口并不会读取整个环（除非你有一个巨大的批处理大小或非常小的环大小）。

可以在本文档后面的示例程序中找到接收和发送多缓冲支持的例子。
### 使用
------

为了使用 AF_XDP 套接字，需要两个部分：用户空间应用程序和 XDP 程序。对于完整的设置和使用示例，请参考样本应用。用户空间侧是 `xdpsock_user.c`，而 XDP 侧则是 `libbpf` 的一部分。

XDP 代码示例包含在 `tools/lib/bpf/xsk.c` 中，如下所示：

```c
SEC("xdp_sock") 
int xdp_sock_prog(struct xdp_md *ctx)
{
    int index = ctx->rx_queue_index;

    // 如果在此 map 中有条目，则意味着对应的 queue_id
    // 有一个绑定到它的活动 AF_XDP 套接字
    if (bpf_map_lookup_elem(&xsks_map, &index))
        return bpf_redirect_map(&xsks_map, index, 0);

    return XDP_PASS;
}
```

一个简单但性能不佳的环形队列出队和入队操作可能如下所示：

```c
// struct xdp_rxtx_ring {
//     __u32 *producer;
//     __u32 *consumer;
//     struct xdp_desc *desc;
// };

// struct xdp_umem_ring {
//     __u32 *producer;
//     __u32 *consumer;
//     __u64 *desc;
// };

// typedef struct xdp_rxtx_ring RING;
// typedef struct xdp_umem_ring RING;

// typedef struct xdp_desc RING_TYPE;
// typedef __u64 RING_TYPE;

int dequeue_one(RING *ring, RING_TYPE *item)
{
    __u32 entries = *ring->producer - *ring->consumer;

    if (entries == 0)
        return -1;

    // 读屏障！

    *item = ring->desc[*ring->consumer & (RING_SIZE - 1)];
    (*ring->consumer)++;
    return 0;
}

int enqueue_one(RING *ring, const RING_TYPE *item)
{
    u32 free_entries = RING_SIZE - (*ring->producer - *ring->consumer);

    if (free_entries == 0)
        return -1;

    ring->desc[*ring->producer & (RING_SIZE - 1)] = *item;

    // 写屏障！

    (*ring->producer)++;
    return 0;
}
```

但是请使用 `libbpf` 中的函数，因为它们已经过优化且准备就绪，将会让您的生活更轻松。

### 多缓冲接收路径使用
---------------------

这里是一个简单的接收路径伪代码示例（为简化起见使用 `libxdp` 接口）。错误处理路径已被省略以保持简洁：

```c
void rx_packets(struct xsk_socket_info *xsk)
{
    static bool new_packet = true;
    u32 idx_rx = 0, idx_fq = 0;
    static char *pkt;

    int rcvd = xsk_ring_cons__peek(&xsk->rx, opt_batch_size, &idx_rx);

    xsk_ring_prod__reserve(&xsk->umem->fq, rcvd, &idx_fq);

    for (int i = 0; i < rcvd; i++) {
        struct xdp_desc *desc = xsk_ring_cons__rx_desc(&xsk->rx, idx_rx++);
        char *frag = xsk_umem__get_data(xsk->umem->buffer, desc->addr);
        bool eop = !(desc->options & XDP_PKT_CONTD);

        if (new_packet)
            pkt = frag;
        else
            add_frag_to_pkt(pkt, frag);

        if (eop)
            process_pkt(pkt);

        new_packet = eop;

        *xsk_ring_prod__fill_addr(&xsk->umem->fq, idx_fq++) = desc->addr;
    }

    xsk_ring_prod__submit(&xsk->umem->fq, rcvd);
    xsk_ring_cons__release(&xsk->rx, rcvd);
}
```

### 多缓冲发送路径使用
---------------------

这里是一个发送路径伪代码示例（为简化起见使用 `libxdp` 接口），忽略了 umem 是有限大小的事实，并且最终我们将耗尽要发送的数据包。还假设 `pkts.addr` 指向 umem 中的有效位置。

```c
void tx_packets(struct xsk_socket_info *xsk, struct pkt *pkts,
                int batch_size)
{
    u32 idx, i, pkt_nb = 0;

    xsk_ring_prod__reserve(&xsk->tx, batch_size, &idx);

    for (i = 0; i < batch_size;) {
        u64 addr = pkts[pkt_nb].addr;
        u32 len = pkts[pkt_nb].size;

        do {
            struct xdp_desc *tx_desc;

            tx_desc = xsk_ring_prod__tx_desc(&xsk->tx, idx + i++);
            tx_desc->addr = addr;

            if (len > xsk_frame_size) {
                tx_desc->len = xsk_frame_size;
                tx_desc->options = XDP_PKT_CONTD;
            } else {
                tx_desc->len = len;
                tx_desc->options = 0;
                pkt_nb++;
            }
            len -= tx_desc->len;
            addr += xsk_frame_size;

            if (i == batch_size) {
                /* 记住 len, addr, pkt_nb 用于下一次迭代
* 为简化起见被忽略
*/
                break;
            }
        } while (len);
    }

    xsk_ring_prod__submit(&xsk->tx, i);
}
```

### 多缓冲支持探测
-------------------

要发现驱动程序是否支持多缓冲 AF_XDP 在 SKB 或 DRV 模式下，可以使用 `linux/netdev.h` 中 netlink 的 `XDP_FEATURES` 特性来查询 `NETDEV_XDP_ACT_RX_SG` 支持。这是与查询 XDP 多缓冲支持相同的标志。如果 XDP 在驱动程序中支持多缓冲，则 AF_XDP 也会在 SKB 和 DRV 模式下支持它。

要发现驱动程序是否支持零复制模式下的多缓冲 AF_XDP，可以使用 `XDP_FEATURES` 并首先检查 `NETDEV_XDP_ACT_XSK_ZEROCOPY` 标志。如果设置了该标志，则表示至少支持零复制，并且您应该检查 `linux/netdev.h` 中的 netlink 属性 `NETDEV_A_DEV_XDP_ZC_MAX_SEGS`。将返回一个无符号整数值，表示此设备在零复制模式下支持的最大分段数。可能的返回值包括：

1: 此设备不支持零复制模式下的多缓冲，因为只支持一个分段意味着无法实现多缓冲。
>=2: 此设备支持零复制模式下的多缓冲。返回的数字表示支持的最大分段数。

有关如何通过 `libbpf` 使用这些功能的示例，请参阅 `tools/testing/selftests/bpf/xskxceiver.c`。
### 多缓冲区支持零拷贝驱动程序

零拷贝驱动程序通常使用批量处理API来进行接收（Rx）和发送（Tx）处理。需要注意的是，发送（Tx）批量API保证它将提供一个以完整数据包结束的发送描述符批量。这样做是为了便于在零拷贝驱动程序中扩展多缓冲区支持。

#### 示例应用

包含了一个名为`xdpsock`的基准测试/测试应用程序，用于演示如何使用带有私有UMEM的AF_XDP套接字。假设您希望端口4242上的UDP流量最终进入队列16，我们将在该队列上启用AF_XDP。这里我们使用ethtool进行设置：

```bash
ethtool -N p3p2 rx-flow-hash udp4 fn
ethtool -N p3p2 flow-type udp4 src-port 4242 dst-port 4242 \
    action 16
```

可以在XDP_DRV模式下通过以下命令运行rxdrop基准测试：

```bash
samples/bpf/xdpsock -i p3p2 -q 16 -r -N
```

对于XDP_SKB模式，使用"-S"代替"-N"，所有选项可以通过"-h"显示，如同往常一样。
此示例应用使用libbpf简化了AF_XDP的设置和使用。如果您想知道如何使用AF_XDP的原始uapi来实现更高级的功能，请查看tools/lib/bpf/xsk.[ch]中的libbpf代码。

### 常见问题解答

**问：我在套接字上看不到任何流量。我做错了什么？**

**答：** 当物理网卡的网络设备初始化时，Linux通常会为每个核心分配一个RX和TX队列对。因此，在8核系统上，队列ID 0到7将被分配，每个核心一个。在AF_XDP绑定调用或libbpf函数xsk_socket__create中，您指定要绑定到的具体队列ID，并且您仅能通过套接字获取指向该队列的流量。因此，在上面的例子中，如果您绑定到队列0，则不会收到任何分配给队列1至7的流量。您可能会幸运地看到一些流量，但通常情况下它会落到您未绑定的队列之一上。
有多种方法可以解决将所需的流量引导到您绑定的队列ID的问题。如果您想看到所有流量，可以强制网络设备只保留1个队列（队列ID 0），然后绑定到队列0。您可以使用ethtool完成此操作：

```bash
sudo ethtool -L <interface> combined 1
```

如果您只想看到部分流量，可以通过ethtool编程NIC以将您的流量过滤到单个队列ID，然后将XDP套接字绑定到该队列ID。以下是一个例子，其中端口4242的UDP流量被发送到队列2：

```bash
sudo ethtool -N <interface> rx-flow-hash udp4 fn
sudo ethtool -N <interface> flow-type udp4 src-port 4242 dst-port \
    4242 action 2
```

还有许多其他方法，具体取决于您所拥有的NIC的能力。

**问：我可以使用XSKMAP在复制模式下实现在不同UMEM之间的切换吗？**

**答：** 简短的回答是不可以，目前不支持这种功能。XSKMAP只能用于将来自队列ID X的流量导向绑定到相同队列ID X的套接字。XSKMAP可以包含绑定到不同队列ID（例如X和Y）的套接字，但是只有来自队列ID Y的流量才能被导向绑定到相同队列ID Y的套接字。在零拷贝模式下，您应该使用NIC中的交换机或其他分发机制来将流量导向正确的队列ID和套接字。

**问：我的数据包有时会被破坏。出了什么问题？**

**答：** 必须小心不要在同一时间将UMEM中的同一个缓冲区馈送到多个环中。例如，如果同时将相同的缓冲区馈送到FILL环和TX环中，NIC可能在发送数据的同时接收数据，这会导致某些数据包损坏。同样的规则也适用于将相同缓冲区馈送到属于不同队列ID或使用XDP_SHARED_UMEM标志绑定的不同网络设备的FILL环。

### 致谢

- Björn Töpel (AF_XDP 核心)
- Magnus Karlsson (AF_XDP 核心)
- Alexander Duyck
- Alexei Starovoitov
- Daniel Borkmann
- Jesper Dangaard Brouer
- John Fastabend
- Jonathan Corbet (LWN报道)
- Michael S. Tsirkin
- Qi Z Zhang
- Willem de Bruijn
