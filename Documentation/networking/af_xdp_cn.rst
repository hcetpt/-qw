SPDX 许可证标识符: GPL-2.0

======
AF_XDP
======

概述
========

AF_XDP 是一个针对高性能数据包处理进行了优化的地址族。
本文档假定读者熟悉 BPF 和 XDP。如果不熟悉，Cilium 项目有一个优秀的参考指南：
http://cilium.readthedocs.io/en/latest/bpf/
通过使用 XDP_REDIRECT 动作，XDP 程序可以将入站帧重定向到其他启用了 XDP 的网络设备，使用 bpf_redirect_map() 函数。AF_XDP 套接字使得 XDP 程序能够将帧重定向到用户空间应用程序中的内存缓冲区成为可能。
AF_XDP 套接字（XSK）是通过常规的 socket() 系统调用来创建的。每个 XSK 都关联有两个环：RX 环和 TX 环。套接字可以在 RX 环上接收数据包，并在 TX 环上发送数据包。这些环分别通过 setsockopt 的 XDP_RX_RING 和 XDP_TX_RING 进行注册和设置大小。每个套接字必须至少有一个环。RX 或 TX 描述符环指向一个称为 UMEM 的内存区域中的数据缓冲区。RX 和 TX 可以共享同一个 UMEM，这样数据包就不需要在 RX 和 TX 之间复制。此外，如果由于可能的重传而需要保留某个数据包一段时间，则指向该数据包的描述符可以更改为其另一个位置并立即重用。这再次避免了数据复制。
UMEM 由若干个等大小的块组成。环中的一个描述符通过引用其 addr 来引用一个帧。addr 仅仅是整个 UMEM 区域内的偏移量。用户空间使用其认为最合适的方法（如 malloc、mmap、大页等）为这个 UMEM 分配内存。然后使用新的 setsockopt XDP_UMEM_REG 将此内存区域注册到内核。UMEM 也有两个环：FILL 环和 COMPLETION 环。FILL 环用于应用程序向内核发送 addr，以便内核填充 RX 数据包数据。一旦每个数据包被接收，这些帧的引用就会出现在 RX 环中。另一方面，COMPLETION 环包含内核已完全传输的帧 addr，现在可以被用户空间重新使用，无论是用于 TX 还是 RX。因此，出现在 COMPLETION 环中的帧 addr 是之前使用 TX 环传输的 addr。总之，RX 和 FILL 环用于 RX 路径，而 TX 和 COMPLETION 环用于 TX 路径。
然后，套接字通过 bind() 调用绑定到设备及其上的特定队列 ID，直到 bind 完成后流量才会开始流动。
如果需要，UMEM 可以在进程间共享。如果一个进程希望这样做，它只需跳过 UMEM 及其相应两个环的注册，在 bind 调用中设置 XDP_SHARED_UMEM 标志，并提交其希望共享 UMEM 的进程的 XSK 以及其自身新创建的 XSK 套接字。新的进程将在其自己的 RX 环中收到指向这个共享 UMEM 的帧 addr 引用。请注意，由于环结构是单消费者/单生产者（为了性能原因），新的进程必须创建其自己的带有相关 RX 和 TX 环的套接字，因为它不能与另一个进程共享。这也是为什么每个 UMEM 只有一组 FILL 和 COMPLETION 环的原因。由单个进程负责处理 UMEM。
那么，XDP 程序如何将数据包分发到 XSK？这里有一个名为 XSKMAP（或 BPF_MAP_TYPE_XSKMAP）的 BPF 地图。用户空间应用程序可以在该地图中的任意位置放置一个 XSK。XDP 程序可以将数据包重定向到该地图中的特定索引，并在此时验证该地图中的 XSK 是否确实绑定到了该设备和队列编号。如果不是，则丢弃该数据包。如果该索引处的地图为空，数据包也会被丢弃。这也意味着目前必须加载一个 XDP 程序（并且 XSKMAP 中至少有一个 XSK）才能通过 XSK 将任何流量传递到用户空间。
AF_XDP 可以在两种不同的模式下运行：XDP_SKB 和 XDP_DRV。如果驱动程序不支持 XDP，或者在加载 XDP 程序时明确选择了 XDP_SKB，则会使用 XDP_SKB 模式，该模式使用 SKB 并结合通用的 XDP 支持将数据复制到用户空间。这是一种适用于任何网络设备的回退模式。另一方面，如果驱动程序支持 XDP，则 AF_XDP 代码将使用它来提供更好的性能，但仍然需要将数据复制到用户空间。

概念
========

为了使用 AF_XDP 套接字，需要设置一些相关的对象。以下各节将解释这些对象及其选项。
关于 AF_XDP 的工作原理概述，你也可以参考 2018 年 Linux Plumbers 会议的论文：
http://vger.kernel.org/lpc_net2018_talks/lpc18_paper_af_xdp_perf-v2.pdf。不要查阅 2017 年关于“AF_PACKET v4”的论文，因为那是 AF_XDP 的首次尝试，从那时起几乎一切都发生了变化。Jonathan Corbet 还在 LWN 上撰写了一篇优秀的文章，“使用 AF_XDP 加速网络”。该文章可以在 https://lwn.net/Articles/750845/ 找到。

### UMEM
---

UMEM 是一个虚拟连续内存区域，分为大小相等的帧。一个 UMEM 与一个网卡设备及其特定的队列 ID 相关联。它通过使用 XDP_UMEM_REG setsockopt 系统调用来创建和配置（块大小、头部空间、起始地址和大小）。一个 UMEM 通过 bind() 系统调用与一个网卡设备和队列 ID 绑定。
一个 AF_XDP 套接字与单个 UMEM 相关联，但一个 UMEM 可以有多个 AF_XDP 套接字。为了共享通过套接字 A 创建的 UMEM，下一个套接字 B 可以通过设置 sockaddr_xdp 结构中的 XDP_SHARED_UMEM 标志，并将 A 的文件描述符传递给 sockaddr_xdp 结构的 sxdp_shared_umem_fd 成员来实现这一点。
UMEM 包含两个单生产者/单消费者的环，用于在内核和用户空间应用程序之间传输 UMEM 帧的所有权。

### 环
---

总共有四种不同类型的环：FILL、COMPLETION、RX 和 TX。所有环都是单生产者/单消费者，因此用户空间应用程序需要显式同步多个进程/线程对它们的读写操作。
UMEM 使用两个环：FILL 和 COMPLETION。每个与 UMEM 关联的套接字必须有一个 RX 队列、TX 队列或两者都有。假设有一个包含四个套接字（全部进行 TX 和 RX）的设置，则将有一个 FILL 环、一个 COMPLETION 环、四个 TX 环和四个 RX 环。
这些环是基于头部（生产者）/尾部（消费者）的环。生产者在由 xdp_ring 结构的 producer 成员指向的索引处写入数据环，并增加生产者索引。消费者在由 xdp_ring 结构的 consumer 成员指向的索引处读取数据环，并增加消费者索引。
环通过 _RING setsockopt 系统调用来配置和创建，并使用适当的偏移量通过 mmap() 映射到用户空间（XDP_PGOFF_RX_RING、XDP_PGOFF_TX_RING、XDP_UMEM_PGOFF_FILL_RING 和 XDP_UMEM_PGOFF_COMPLETION_RING）。
环的大小需要为 2 的幂次方。

### UMEM Fill 环
~~~~~~~~~~~~~~

FILL 环用于将 UMEM 帧的所有权从用户空间转移到内核空间。UMEM 地址通过环传递。例如，如果 UMEM 大小为 64K，每个块为 4K，则 UMEM 有 16 个块，并且可以传递 0 到 64K 之间的地址。
传递给内核的帧用于入站路径（接收环[RX环]）
用户应用程序生成UMEM地址到这个环。请注意，如果在对齐块模式下运行该应用程序，内核将屏蔽传入的地址。例如，对于2K的块大小，log2(2048)最低有效位（LSB）的地址将被屏蔽，这意味着2048、2050和3000指向同一个块。如果用户应用程序以未对齐的块模式运行，则传入的地址将保持不变。

UMEM完成环
~~~~~~~~~~~
完成环用于将UMEM帧的所有权从内核空间转移到用户空间。与填充环类似，使用UMEM索引。
从内核传递到用户空间的帧是已经发送过的帧（TX环），并且可以再次被用户空间使用。
用户应用程序从这个环消费UMEM地址。

接收环（RX环）
~~~~~~~~~~~
接收环是套接字的接收端。环中的每一项都是一个`struct xdp_desc`描述符。该描述符包含UMEM偏移量（地址）和数据长度。
如果没有帧通过填充环传递给内核，则接收环上不会出现（也无法出现）任何描述符。
用户应用程序从这个环消费`struct xdp_desc`描述符。

发送环（TX环）
~~~~~~~~~~~
发送环用于发送帧。`struct xdp_desc`描述符将被填充（索引、长度和偏移量），并传递到环中。
要开始传输，需要调用`sendmsg()`系统调用。这在未来可能会放宽。
用户应用程序生成结构 `xdp_desc` 描述符到此环中。

Libbpf
======

Libbpf 是一个用于 eBPF 和 XDP 的辅助库，使得使用这些技术变得更加简单。它还包含了一些特定的辅助函数，在 `tools/lib/bpf/xsk.h` 中，以方便使用 AF_XDP。它包含两种类型的函数：一种可以用来简化 AF_XDP 套接字的设置，另一种可以在数据平面中安全快速地访问环。要查看如何使用此 API 的示例，请参阅 `samples/bpf/xdpsock_usr.c` 中的示例应用程序，该程序在设置和数据平面操作中均使用了 libbpf。我们建议您除非已成为高级用户，否则使用此库会使您的程序更加简单。

XSKMAP / BPF_MAP_TYPE_XSKMAP
============================

在 XDP 方面，有一种名为 BPF_MAP_TYPE_XSKMAP（XSKMAP）的 BPF 映射类型，与 `bpf_redirect_map()` 结合使用，将入站帧传递给套接字。
用户应用程序通过 `bpf()` 系统调用将套接字插入映射表。
请注意，如果 XDP 程序尝试重定向到不匹配队列配置和网卡的套接字，则帧将被丢弃。例如，AF_XDP 套接字绑定到网卡 eth0 和队列 17。只有执行在 eth0 和队列 17 上的 XDP 程序才能成功将数据传递给套接字。请参阅示例应用程序（位于 `samples/bpf/` 目录下）了解示例。

配置标志和套接字选项
======================

这些是各种可用于控制和监控 AF_XDP 套接字行为的配置标志。

XDP_COPY 和 XDP_ZEROCOPY 绑定标志
------------------------------------

当您绑定到一个套接字时，内核会首先尝试使用零拷贝模式。如果零拷贝模式不受支持，则会回退到使用复制模式，即复制所有数据包到用户空间。但是如果您希望强制某种模式，您可以使用以下标志。如果您在绑定调用中传递 XDP_COPY 标志，内核将强制套接字进入复制模式。如果无法使用复制模式，绑定调用将返回错误。相反地，XDP_ZEROCOPY 标志将强制套接字进入零拷贝模式或失败。

XDP_SHARED_UMEM 绑定标志
-------------------------

此标志允许您将多个套接字绑定到同一个 UMEM。它适用于相同的队列 ID、不同的队列 ID 以及不同的网卡/设备。在此模式下，每个套接字都有自己的 RX 和 TX 环，但您将有一个或多个 FILL 和 COMPLETION 环对。您需要为每个唯一的网卡和队列 ID 组合创建一对这样的环。

从我们希望在相同网卡和队列 ID 上共享 UMEM 的情况开始。UMEM（与第一个创建的套接字关联）将只有一个 FILL 环和一个 COMPLETION 环，因为我们只绑定了一个唯一的网卡和队列 ID 组合。要使用此模式，请创建第一个套接字并按常规方式绑定。创建第二个套接字并创建 RX 和 TX 环，或者至少创建其中一个，但不要创建 FILL 或 COMPLETION 环，因为将使用第一个套接字的环。在绑定调用中，设置 XDP_SHARED_UMEM 选项，并在 sxdp_shared_umem_fd 字段中提供初始套接字的文件描述符。这样您可以附加任意数量的额外套接字。
数据包将到达哪个套接字？这由XDP程序决定。将所有套接字放入XSK_MAP中，并指定你希望将每个数据包发送到数组中的哪个索引。下面是一个简单的轮询分发数据包的例子：

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

请注意，由于只有一个填充（FILL）和完成（COMPLETION）环形缓冲区，并且它们是单生产者、单消费者的环形缓冲区，因此你需要确保多个进程或线程不要同时使用这些环形缓冲区。目前libbpf代码中没有同步原语来保护多个用户。如果你创建了多个与同一UMEM绑定的套接字，libbpf会使用这种模式。但是，请注意，你需要在xsk_socket__create调用时提供XSK_LIBBPF_FLAGS__INHIBIT_PROG_LOAD标志并加载自己的XDP程序，因为libbpf中没有内置的XDP程序来为你路由流量。

第二种情况是你在一个UMEM上绑定了具有不同队列ID和/或网络设备的套接字。在这种情况下，你需要为每个唯一的netdev,queue_id对创建一个FILL环和一个COMPLETION环。假设你想在同一网络设备上创建两个绑定到不同队列ID的套接字。按照正常方式创建第一个套接字并将其绑定。创建第二个套接字并创建一个RX环和一个TX环，或者至少创建其中一个环，然后为这个套接字创建一个FILL环和一个COMPLETION环。然后，在bind调用中设置XDP_SHARED_UMEM选项，并在sxdp_shared_umem_fd字段中提供初始套接字的文件描述符，因为你是在该套接字上注册的UMEM。这两个套接字现在将共享同一个UMEM。

在这种情况下不需要像前一种情况那样提供XDP程序（前一种情况中套接字绑定到相同的队列ID和设备）。相反，可以使用NIC的数据包转向能力将数据包引导到正确的队列。在前面的例子中，所有套接字共享一个队列，所以NIC无法进行这种转向，它只能在队列之间进行转向。

在libbpf中，你需要使用xsk_socket__create_shared() API，因为它会为你创建一个FILL环和一个COMPLETION环，并将其绑定到共享的UMEM。你可以为所有创建的套接字使用此函数，也可以仅用于第二个及后续的套接字，并为第一个套接字使用xsk_socket__create()。这两种方法都会产生相同的结果。

请注意，一个UMEM可以在同一队列ID和设备上的套接字之间共享，也可以在同一设备的不同队列之间共享，甚至可以在不同设备之间共享。

XDP_USE_NEED_WAKEUP绑定标志
------------------------------

此选项支持一个新的标志need_wakeup，该标志存在于FILL环和TX环中，即用户空间作为生产者的环。当在bind调用中设置了此选项后，如果内核需要通过系统调用来显式唤醒以继续处理数据包，则会设置need_wakeup标志。如果此标志为零，则不需要系统调用。

如果此标志在FILL环上被设置，应用程序需要调用poll()才能继续从RX环接收数据包。例如，当内核检测到FILL环上没有更多缓冲区并且NIC的RX硬件环上也没有剩余缓冲区时，就会发生这种情况。此时中断被关闭，因为NIC无法接收任何数据包（因为没有缓冲区可以放置数据包），并且设置need_wakeup标志以便用户空间可以将缓冲区放到FILL环上，然后调用poll()，从而使内核驱动器将这些缓冲区放到硬件环上并开始接收数据包。

如果此标志针对TX环被设置，则意味着应用程序需要显式通知内核发送任何放在TX环上的数据包。可以通过调用poll()（如在RX路径中）或调用sendto()来实现这一点。

如何使用此标志的一个例子可以在samples/bpf/xdpsock_user.c中找到。对于TX路径使用libbpf辅助函数的一个示例如下：

```c
if (xsk_ring_prod__needs_wakeup(&my_tx_ring))
    sendto(xsk_socket__fd(xsk_handle), NULL, 0, MSG_DONTWAIT, NULL, 0);
```

也就是说，只有在标志被设置时才使用系统调用。
我们建议您始终启用此模式，因为它通常能带来更好的性能，尤其是在应用程序和驱动程序运行在同一内核的情况下，即使应用程序和内核驱动程序使用不同的内核，也能减少传输路径所需的系统调用次数。
XDP_{RX|TX|UMEM_FILL|UMEM_COMPLETION}_RING setsockopt

这些 setsockopt 设置了 RX、TX、FILL 和 COMPLETION 环形缓冲区应具有的描述符数量。至少必须设置 RX 和 TX 环形缓冲区之一的大小。如果您设置了两者，则可以从您的应用程序同时接收和发送流量；但如果您只想执行其中一项操作，可以通过仅设置一个环形缓冲区来节省资源。FILL 环形缓冲区和 COMPLETION 环形缓冲区是必需的，因为您需要将 UMEM 绑定到您的套接字上。但如果使用了 XDP_SHARED_UMEM 标志，第一个套接字之后的任何套接字都不会有 UMEM，并且在这种情况下不应创建任何 FILL 或 COMPLETION 环形缓冲区，因为将使用共享 UMEM 的环形缓冲区。请注意，这些环形缓冲区是单生产者单消费者的，因此请勿尝试同时从多个进程中访问它们。参见 XDP_SHARED_UMEM 部分。

在 libbpf 中，您可以通过向 xsk_socket__create 函数分别提供 NULL 参数来创建仅接收（Rx-only）或仅发送（Tx-only）套接字。
如果您创建了一个仅发送（Tx-only）套接字，我们建议您不要在填充环形缓冲区中放置任何数据包。如果这样做，驱动程序可能会认为您将接收某些内容，但实际上您不会接收，这可能会对性能产生负面影响。

XDP_UMEM_REG setsockopt
-----------------------

此 setsockopt 将 UMEM 注册到套接字。这是包含所有数据包可以驻留的缓冲区的区域。此调用需要指向该区域开头的指针及其大小。此外，它还有一个名为 chunk_size 的参数，表示 UMEM 被划分的大小。目前只能为 2K 或 4K。例如，如果您有一个大小为 128K 的 UMEM 区域且 chunk 大小为 2K，这意味着您可以在 UMEM 区域中存储最多 128K / 2K = 64 个数据包，且最大数据包大小为 2K。
还可以设置每个 UMEM 缓冲区头部的空间。如果您将其设置为 N 字节，则意味着数据包将从缓冲区的第 N 字节开始，留下前 N 字节供应用程序使用。最后一个选项是标志字段，但每个 UMEM 标志将在单独的部分中处理。

SO_BINDTODEVICE setsockopt
--------------------------

这是一个通用的 SOL_SOCKET 选项，可用于将 AF_XDP 套接字绑定到特定的网络接口。当一个特权进程创建套接字并传递给非特权进程时，这很有用。
一旦设置了此选项，内核将拒绝尝试将该套接字绑定到不同接口的尝试。更新值需要 CAP_NET_RAW 权限。

XDP_STATISTICS getsockopt
-------------------------

获取套接字的丢弃统计信息，这对于调试很有用。支持的统计信息如下所示：

```c
struct xdp_statistics {
    __u64 rx_dropped;      /* 因无效描述符以外的原因被丢弃 */
    __u64 rx_invalid_descs;/* 因无效描述符被丢弃 */
    __u64 tx_invalid_descs;/* 因无效描述符被丢弃 */
};
```

XDP_OPTIONS getsockopt
----------------------

从 XDP 套接字获取选项。目前唯一支持的选项是 XDP_OPTIONS_ZEROCOPY，用于告诉您是否启用了零拷贝。

多缓冲支持
===========

通过多缓冲支持，使用 AF_XDP 套接字的程序可以在复制模式和零拷贝模式下接收和发送由多个缓冲区组成的分组。例如，一个分组可以由两个帧/缓冲区组成，一个包含报头，另一个包含数据，或者一个 9K 以太网巨型帧可以通过链接三个 4K 帧来构建。
一些定义：

* 一个数据包由一个或多个帧组成。

* AF_XDP 环中的描述符始终指向单个帧。如果数据包仅由一个帧组成，则该描述符指代整个数据包。

为了在 AF_XDP 套接字中启用多缓冲支持，需要使用新的绑定标志 XDP_USE_SG。如果不提供此标志，所有多缓冲数据包将像以前一样被丢弃。请注意，加载的 XDP 程序也需要处于多缓冲模式。这可以通过将“xdp.frags”作为所使用的 XDP 程序的部分名称来实现。

为了表示由多个帧组成的数据包，引入了一个新的标志 XDP_PKT_CONTD 在接收（Rx）和发送（Tx）描述符的选项字段中。如果它为真（1），则数据包会继续到下一个描述符；如果为假（0），则意味着这是数据包的最后一个描述符。为什么与许多网卡上找到的包结束（EOP）标志相反？只是为了保持与非多缓冲应用程序的兼容性，这些应用程序在接收时将此位设置为假，并且应用程序在发送时将选项字段设置为零，因为任何其他值都将被视为无效描述符。

以下是将由多个帧组成的包生产到 AF_XDP 发送环上的语义：

* 当发现无效描述符时，该数据包的所有其他描述符/帧都会被标记为无效且未完成。下一个描述符被视为新数据包的开始，即使这不是本意（因为我们无法猜测意图）。如果您的程序生成了无效描述符，那么您有一个必须修复的错误。
* 零长度描述符被视为无效描述符。
* 对于复制模式，一个数据包中支持的最大帧数等于 CONFIG_MAX_SKB_FRAGS + 1。如果超过此限制，所有累积的描述符将被丢弃并视为无效。为了使应用程序能够在任何系统上工作，无论此配置设置如何，请将分片数量限制为 18，因为此配置的最小值为 17。
* 对于零复制模式，限制取决于网卡硬件支持的数量。通常至少为五个，在我们检查过的网卡中。我们有意选择不在零复制模式下强制实施硬性限制（例如 CONFIG_MAX_SKB_FRAGS + 1），因为这将导致内部进行复制操作以适应网卡支持的限制。这有点违背了零复制模式的目的。如何探测此限制在“探测多缓冲支持”部分中有解释。

在复制模式下的接收路径中，xsk 核心根据需要将 XDP 数据复制到多个描述符，并如前所述设置 XDP_PKT_CONTD 标志。零复制模式的工作方式相同，只是数据不会被复制。当应用程序接收到带有 XDP_PKT_CONTD 标志设置为 1 的描述符时，这意味着数据包由多个缓冲区组成，并且在下一个描述符中继续下一个缓冲区。当接收到 XDP_PKT_CONTD == 0 的描述符时，意味着这是数据包的最后一个缓冲区。AF_XDP 保证只有完整的数据包（数据包中的所有帧）才会发送给应用程序。如果 AF_XDP 接收环中没有足够的空间，数据包的所有帧将被丢弃。

如果应用程序读取一批描述符，例如使用 libxdp 接口，则不能保证这批描述符将以一个完整的数据包结束。它可能在一个数据包中间结束，并且该数据包的其余缓冲区将在下一批的开头到达，因为 libxdp 接口不会读取整个环（除非您有巨大的批处理大小或非常小的环大小）。

有关接收和发送多缓冲支持的示例程序可以在本文档后面找到。
用法
-----

为了使用AF_XDP套接字，需要两个部分：用户空间应用程序和XDP程序。对于完整的配置和使用示例，请参阅示例应用程序。用户空间部分是xdpsock_user.c，而XDP部分是libbpf的一部分。包含在tools/lib/bpf/xsk.c中的XDP代码示例如下：

```c
SEC("xdp_sock")
int xdp_sock_prog(struct xdp_md *ctx)
{
    int index = ctx->rx_queue_index;

    // 如果在此处设置了一个条目，则表示对应的queue_id
    // 已绑定到一个活动的AF_XDP套接字
    if (bpf_map_lookup_elem(&xsks_map, &index))
        return bpf_redirect_map(&xsks_map, index, 0);

    return XDP_PASS;
}
```

一个简单的但性能不佳的环形队列出队入队操作可能如下所示：

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

    // 读取屏障！

    *item = ring->desc[*ring->consumer & (RING_SIZE - 1)];
    (*ring->consumer)++;
    return 0;
}

int enqueue_one(RING *ring, const RING_TYPE *item)
{
    __u32 free_entries = RING_SIZE - (*ring->producer - *ring->consumer);

    if (free_entries == 0)
        return -1;

    ring->desc[*ring->producer & (RING_SIZE - 1)] = *item;

    // 写入屏障！

    (*ring->producer)++;
    return 0;
}
```

但是请使用libbpf提供的函数，因为它们经过优化且易于使用，会简化您的工作。

多缓冲接收路径
---------------------

以下是一个简单的接收路径伪代码示例（为简化起见使用libxdp接口）。错误处理已省略以保持简洁：

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

多缓冲发送路径
---------------------

以下是一个发送路径伪代码示例（为简化起见使用libxdp接口），忽略umem有限大小的问题，并假设我们最终不会耗尽要发送的数据包。还假设pkts.addr指向umem中的有效位置：

```c
void tx_packets(struct xsk_socket_info *xsk, struct pkt *pkts, int batch_size)
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
                /* 记住len、addr、pkt_nb用于下次迭代
* 简化起见已省略
*/
                break;
            }
        } while (len);
    }

    xsk_ring_prod__submit(&xsk->tx, i);
}
```

多缓冲支持探测
-------------------

为了发现驱动是否支持SKB或DRV模式下的多缓冲AF_XDP，可以使用linux/netdev.h中的netlink特性XDP_FEATURES来查询NETDEV_XDP_ACT_RX_SG支持。这是与查询XDP多缓冲支持相同的标志。如果XDP在某个驱动中支持多缓冲，那么AF_XDP也将支持SKB和DRV模式下的多缓冲。
为了发现驱动是否支持零拷贝模式下的多缓冲AF_XDP，可以使用XDP_FEATURES并首先检查NETDEV_XDP_ACT_XSK_ZEROCOPY标志。如果该标志被设置，则意味着至少支持零拷贝，您应该进一步检查netlink属性NETDEV_A_DEV_XDP_ZC_MAX_SEGS（位于linux/netdev.h中）。将返回一个无符号整数值，指示此设备在零拷贝模式下支持的最大分段数。可能的返回值如下：

1: 此设备不支持零拷贝模式下的多缓冲，因为最大支持一个分段意味着无法实现多缓冲
>=2: 此设备支持零拷贝模式下的多缓冲。返回的数字表示支持的最大分段数

有关如何通过libbpf使用这些功能的示例，请参阅tools/testing/selftests/bpf/xskxceiver.c。
多缓冲支持零拷贝驱动程序
------------------------------------------

零拷贝驱动程序通常使用批量处理API来进行接收（Rx）和发送（Tx）处理。请注意，Tx批量API保证会提供一个以完整数据包结尾的Tx描述符批次。这有助于扩展具有多缓冲支持的零拷贝驱动程序。

示例应用
==================

包含了一个xdpsock基准测试/测试应用，展示了如何使用带有私有UMEM的AF_XDP套接字。假设你想让你的UDP流量从端口4242进入队列16，我们将在此队列启用AF_XDP功能。这里我们使用ethtool进行设置：

```
ethtool -N p3p2 rx-flow-hash udp4 fn
ethtool -N p3p2 flow-type udp4 src-port 4242 dst-port 4242 action 16
```

在XDP_DRV模式下运行rxdrop基准测试可以使用以下命令：

```
samples/bpf/xdpsock -i p3p2 -q 16 -r -N
```

对于XDP_SKB模式，使用"-S"代替"-N"，所有选项可以通过"-h"显示，如常。

这个示例应用使用libbpf简化了AF_XDP的设置和使用。如果你想了解如何使用AF_XDP的原始uapi实现更高级的功能，请查看tools/lib/bpf/xsk.[ch]中的libbpf代码。

常见问题解答
=======

问：我没有看到任何流量出现在套接字上。我做错了什么？

答：当物理NIC的网络设备初始化时，Linux通常为每个核心分配一个RX和TX队列对。因此，在8核系统中，队列ID 0到7将被分配，每个核心一个。在AF_XDP绑定调用或xsk_socket__create的libbpf函数调用中，你指定了一个特定的队列ID来绑定，并且你只能接收到指向该队列的流量。因此，在上面的例子中，如果你绑定到队列0，则不会接收到分配给队列1到7的任何流量。如果幸运的话，你会看到这些流量，但通常它们会出现在你未绑定的队列之一。

有多种方法可以解决将所需流量导向你绑定的队列ID的问题。如果你想看到所有流量，可以强制netdev仅有一个队列，即队列ID 0，并绑定到队列0。你可以使用ethtool完成此操作：

```
sudo ethtool -L <interface> combined 1
```

如果你想只看到部分流量，可以通过ethtool编程NIC将你的流量过滤到单个队列ID，然后绑定你的XDP套接字。以下是一个例子，其中UDP流量到端口4242和从端口4242发出的数据被发送到队列2：

```
sudo ethtool -N <interface> rx-flow-hash udp4 fn
sudo ethtool -N <interface> flow-type udp4 src-port 4242 dst-port 4242 action 2
```

还有其他多种方法，取决于你所拥有的NIC的能力。

问：我可以使用XSKMAP在复制模式下实现不同UMEM之间的切换吗？

答：简短的答案是不可以，目前不支持这样做。XSKMAP只能用于将队列ID X上的流入流量重定向到绑定到相同队列ID X的套接字。XSKMAP可以包含绑定到不同队列ID（例如X和Y）的套接字，但只有来自队列ID Y的流量才能被重定向到绑定到相同队列ID Y的套接字。在零拷贝模式下，你应该使用NIC中的交换机或其他分发机制将流量导向正确的队列ID和套接字。

问：我的数据包有时会被破坏。这是怎么回事？

答：必须小心不要将UMEM中的同一缓冲区同时馈送到多个环中。例如，如果你同时将同一缓冲区馈送到FILL环和TX环，NIC可能会在发送数据的同时接收数据，导致某些数据包损坏。同样，将同一缓冲区馈送到属于不同队列ID或使用XDP_SHARED_UMEM标志绑定的不同netdev的FILL环也会出现相同的问题。

致谢
=======

- Björn Töpel（AF_XDP 核心）
- Magnus Karlsson（AF_XDP 核心）
- Alexander Duyck
- Alexei Starovoitov
- Daniel Borkmann
- Jesper Dangaard Brouer
- John Fastabend
- Jonathan Corbet（LWN报道）
- Michael S. Tsirkin
- Qi Z Zhang
- Willem de Bruijn
