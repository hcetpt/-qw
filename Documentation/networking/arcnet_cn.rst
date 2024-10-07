SPDX 许可证标识符: GPL-2.0

======
ARCnet
======

.. note::

   如果你像我们中的许多人一样，购买 ARCnet 卡时没有附带手册，也可以查看本目录中的 arcnet-hardware.txt 文件，了解跳线设置和电缆信息。
由于似乎没有人听我说话，或许一首诗能引起你的注意::

		这个驱动变得越来越庞大，
		但我家的猫仍然叫菲菲。

嗯，我想我可以称那是一首诗，尽管它只有两行。嘿，我是学计算机科学的，不是英语专业的。请给我一点宽容吧。
重点是：我真的真的真的真的真的希望你在测试这个驱动并使其工作后能告诉我。或者即使不成功也告诉我。任何情况都行。
ARCnet 0.32 ALPHA 首次出现在 Linux 内核 1.1.80 中——这很好，但之后甚至更少的人给我写信了，因为他们连补丁都不用安装了。<叹气>

来吧，做个好人！发个成功的报告给我！

（嘿，这比我的原诗还要好……这太糟糕了！）

.. warning::

   如果你不尽快给我发邮件告诉我你的成功或失败情况，我可能被迫开始唱歌。而我们都不想那样，对吗？

   （你知道吗，也许有人会认为我在这一点上有点过分。如果你这么认为，为什么不给我发封简短的邮件批评我一下呢？请也包括你使用的卡类型、软件、网络规模以及是否成功运行。）

   我的电子邮件地址是：apenwarr@worldvisions.ca

这些是 Linux 的 ARCnet 驱动程序。
这个新版本（2.91）是由 David Woodhouse <dwmw2@infradead.org> 整理的，目的是在添加对另一个芯片组的支持后清理驱动程序。现在通用支持已经从各个芯片组驱动中分离出来，并且源文件不再那么充斥着 #ifdef！我对这个文件做了一些修改，但还是保留了 Avery 的第一人称叙述，因为我并不想完全重写它。
之前的版本是我（Avery Pennarun）经过数月断断续续的努力，加上许多人的错误报告/修复和建议，特别是 Tomasz Motylewski 的大量投入和编码。从 ARCnet 2.10 ALPHA 开始，Tomasz 全新的改进后的 RFC1051 支持已经被包含进来，并且看起来运行良好！

在哪里讨论这些驱动？
-----------------------------

Tomasz 善意地建立了一个新的改进的邮件列表。
订阅该邮件列表，请发送一封包含正文 "subscribe linux-arcnet YOUR REAL NAME" 的邮件到 listserv@tichy.ch.uj.edu.pl。然后，要向邮件列表提交消息，请发送邮件到 linux-arcnet@tichy.ch.uj.edu.pl。
邮件列表的归档位于：

	http://epistolary.org/mailman/listinfo.cgi/arcnet

linux-net@vger.kernel.org（现已停用，被 netdev@vger.kernel.org 替代）的人们也非常乐于帮助，特别是在谈论可能不稳定的 ALPHA Linux 内核时。
其他驱动程序和信息
----------------------

您可以在万维网上访问我的ARCNET页面：

	http://www.qis.net/~jschmitz/arcnet/

此外，SMC（一家生产ARCnet卡的公司）也有一个您可能感兴趣的万维网站点，其中包含各种卡（包括ARCnet）的多个驱动程序。请访问：

	http://www.smc.com/

Performance Technologies 提供支持ARCnet的各种网络软件：

	http://www.perftech.com/ 或者通过ftp访问 ftp.perftech.com
Novell为DOS提供了一个包含ARCnet驱动程序的网络堆栈。尝试
通过FTP访问 ftp.novell.com
您可以从 oak.oakland.edu:/simtel/msdos/pktdrvr 获取Crynwr包驱动程序集合（包括arcether.com，这是您希望与ARCnet卡一起使用的驱动程序）。但是，未经修补的情况下，在386+上无法完美运行，并且也不兼容某些卡。修补后的版本在我的万维网页上有提供，或者如果您没有万维网访问权限，也可以通过电子邮件获取。
安装驱动程序
---------------------

为了安装驱动程序，您需要做的是：

	make config
		（确保在选择网络设备时选择了ARCnet，
		并且至少选择了一个芯片组驱动程序。）
	make clean
	make zImage

如果您是将此ARCnet包作为对当前内核中ARCnet驱动程序的升级，则首先需要将arcnet.c复制到linux/drivers/net目录下。
如果在启动到新的Linux内核时看到一些ARCnet消息，那么说明驱动程序已正确安装。
有四个芯片组选项：

 1. 标准ARCnet COM90xx芯片组
这是最常见的ARCnet卡，您可能拥有这种卡。这是唯一一个如果未指定卡的位置就会自动探测的芯片组驱动程序。
其命令行选项如下：

 com90xx=[<io>[,<irq>[,<shmem>]]][,<name>] | <name>

如果您将芯片组支持作为模块加载，选项如下：

 io=<io> irq=<irq> shmem=<shmem> device=<name>

要禁用自动探测，只需在内核命令行上指定“com90xx=”
如果仅指定名称但允许自动探测，只需输入“com90xx=<name>”

 2. ARCnet COM20020芯片组
这是SMC的新芯片组，支持混杂模式（包嗅探）、额外的诊断信息等。不幸的是，对于这些卡没有合理的自动探测方法。您必须在内核命令行上指定I/O地址
命令行选项如下：

```
com20020=<io>[,<irq>[,<node_ID>[,backplane[,CKP[,timeout]]]]][,name]
```

如果您将芯片组支持作为模块加载，选项如下：

```
io=<io> irq=<irq> node=<node_ID> backplane=<backplane> clock=<CKP> timeout=<timeout> device=<name>
```

COM20020 芯片组允许您在软件中设置节点 ID，从而覆盖默认值，该默认值仍然通过卡上的 DIP 开关设置。如果您没有 COM20020 的数据手册，并且不知道其他三个选项指的是什么，那么这些选项不会引起您的兴趣——请忽略它们。

3. ARCnet COM90xx 芯片组在 IO 映射模式下工作
这也可以与普通的 ARCnet 卡一起工作，但不使用共享内存。其性能比上述驱动程序差，但在以下情况下提供支持：您的卡不支持共享内存，或者（奇怪的是）您机器中的 ARCnet 卡太多以至于共享内存槽不足。
如果您不在内核命令行上指定 IO 地址，则驱动程序将找不到该卡。
命令行选项如下：

```
com90io=<io>[,<irq>][,<name>]
```

如果您将芯片组支持作为模块加载，选项如下：

```
io=<io> irq=<irq> device=<name>
```

4. ARCnet RIM I 卡
这些是完全内存映射的 COM90xx 芯片。对这些的支持尚未经过测试。如果您有一张这样的卡，请向作者发送成功报告。除设备名称外，所有选项都必须指定。
命令行选项如下：

```
arcrimi=<shmem>,<irq>,<node_ID>[,<name>]
```

如果您将芯片组支持作为模块加载，选项如下：

```
shmem=<shmem> irq=<irq> node=<node_ID> device=<name>
```

可加载模块支持
----------------------

配置并重新编译 Linux。当被询问时，对于“通用 ARCnet 支持”以及您希望使用的 ARCnet 芯片组支持，回答 'm'。您也可以对“通用 ARCnet 支持”回答 'y'，对芯片组支持回答 'm'。

```
make config
make clean
make zImage
make modules
```

如果您正在使用可加载模块，需要使用 `insmod` 来加载它，并且可以在命令行上指定各种卡的特性。（在最近版本的驱动程序中，自动探测更加可靠并且可以作为模块运行，因此现在大部分步骤已不再必要。）

例如：

```
cd /usr/src/linux/modules
insmod arcnet.o
insmod com90xx.o
insmod com20020.o io=0x2e0 device=eth1
```

使用驱动程序
----------------

如果您构建的内核包含 ARCnet COM90xx 支持，则在启动时应自动探测您的卡。如果您使用了编译到内核的不同芯片组驱动程序，必须在内核命令行上给出必要的选项，如前所述。
请阅读 Linux 的 NET-2-HOWTO 和 ETHERNET-HOWTO；它们应该可以从您获取此驱动程序的地方获得。将您的 ARCnet 视为一个增强版（或简化的）以太网卡。
顺便说一句，请确保在 HOWTO 中将所有 “eth0” 参考改为 “arc0”。记住，ARCnet 不是真正的以太网，设备名称是不同的。
### 一台计算机中的多张网卡

现在 Linux 对此有很好的支持，但由于我最近很忙，ARCnet 驱动在这一方面有些落后。如果将 COM90xx 支持编译进内核，它（尝试）自动检测所有已安装的网卡。如果你还有其他编译进内核的网卡支持，你可以在内核命令行中重复这些选项，例如：

```
LILO: linux com20020=0x2e0 com20020=0x380 com90io=0x260
```

如果你将芯片组支持作为可加载模块构建，则需要执行类似的操作：

```
insmod -o arc0 com90xx
insmod -o arc1 com20020 io=0x2e0
insmod -o arc2 com90xx
```

ARCnet 驱动程序现在会自动整理它们的名字。

### 如何让它与其他系统工作？

**NFS：**
   在 Linux 到 Linux 的情况下应该没有问题，就像你在使用以太网卡一样。`oak.oakland.edu:/simtel/msdos/nfs` 上有一些不错的 DOS 客户端。还有一个基于 DOS 的 NFS 服务器叫做 SOSS。虽然它不像 Linux 那样多任务处理（实际上它根本不能多任务处理），但你永远不知道你会需要什么。
   
   使用 AmiTCP（以及其他一些工具）时，你可能需要在你的 Amiga 的 `nfstab` 中设置以下选项：MD 1024 MR 1024 MW 1024。（感谢 Christian Gottschling <ferksy@indigo.tng.oche.de> 提供了这些信息。）
   
   这些可能是指最大的 NFS 数据/读/写块大小。我不知道为什么默认值在 Amiga 上不起作用；如果你知道更多信息，请告诉我。

**DOS：**
   如果你使用的是免费软件 `arcether.com`，你可能希望安装我网页上的驱动补丁。这对 PC/TCP 有帮助，并且还可以让 `arcether` 在初始化过程中超时后成功加载。事实上，如果你在 386+ 上使用它，你真的需要这个补丁。

**Windows：**
   参见 DOS :)。无论你使用 Novell 还是 Arcether 客户端，Trumpet Winsock 都可以正常工作，当然前提是你要记得加载 `winpkt`。

**LAN Manager 和 Windows for Workgroups：**
   这些程序使用的协议与互联网标准不兼容。它们试图假装这些网卡是 Ethernet 网卡，从而混淆网络上的其他人。
   
   然而，Linux ARCnet 驱动程序 2.00 版及以上版本通过 `arc0e` 设备支持这种协议。更多详细信息请参阅“多协议支持”部分。

通过使用免费的 Samba 服务器和客户端，你现在可以很好地与基于 TCP/IP 的 Windows for Workgroups 或 Lan Manager 网络进行交互。
Windows 95：
随 Windows 95 提供了一些工具，使您可以使用 LANMAN 风格的网络驱动程序（NDIS）或 Novell 驱动程序（ODI）来处理您的 ARCnet 数据包。如果您使用 ODI，则需要在 Linux 中使用 'arc0' 设备。如果您使用 NDIS，则尝试使用 'arc0e' 设备。
如果需要 arc0e，您完全疯了，或者需要构建一种混合网络以使用两种封装类型，请参阅下面的“多协议支持”部分。

OS/2：
有人告诉我它可以在带有 SMC 的 ARCnet 驱动程序的 Warp Connect 下工作。您需要为此使用 'arc0e' 接口。如果您能让 SMC 驱动程序与“正常”的 Warp Bonus Pack 中包含的 TCP/IP 组件一起工作，请告知我。
ftp.microsoft.com 还提供了一个免费的“LAN Manager for OS/2”客户端，应该使用与 WfWg 相同的协议。然而，在 Warp 下安装时我没有成功。请将任何结果邮件给我。

NetBSD/AmiTCP：
这些使用旧版本的互联网标准 ARCnet 协议（RFC1051），该协议与使用 arc0s 设备的 Linux 驱动程序 v2.10 ALPHA 及以上版本兼容。（参见下方的“多协议 ARCnet”。）** 新版本的 NetBSD 显然支持 RFC1201。

使用多协议 ARCnet
--------------------------

ARCnet 驱动程序 v2.10 ALPHA 支持三种协议，每种协议都有其自己的“虚拟网络设备”：

======  ===============================================================
arc0    RFC1201 协议，即官方的互联网标准，恰好与 Novell 的 TRXNET 驱动程序完全兼容。
        版本 1.00 的 ARCnet 驱动程序仅支持此协议。arc0 是这三种协议中最快的（出于某种原因），并且由于它支持 RFC1201 的“数据包拆分”操作，允许使用更大的数据包。
除非您有特定需求要使用其他协议，否则我强烈建议您坚持使用这一种。

arc0e   “以太网封装”，通过 ARCnet 发送的数据包实际上是类似于以太网数据包的，包括 6 字节的硬件地址。此协议与 Microsoft 的 NDIS ARCnet 驱动程序兼容，例如 WfWg 和 LANMAN 中的驱动程序。由于 493 的最大传输单元（MTU）实际上小于 TCP/IP 所“要求”的（576），因此某些网络操作可能无法正常运行。然而，在大多数情况下，Linux 的 TCP/IP 层可以通过自动将 TCP/IP 数据包分段以使其适应来补偿。arc0e 比 arc0 稍慢一些，具体原因尚待确定。（可能是较小的 MTU 导致的。）

arc0s   “[简化的] RFC1051 协议是‘旧’的互联网标准，与新标准完全不兼容。然而，今天的一些软件仍然支持旧标准（并且只支持旧标准），包括 NetBSD 和 AmiTCP。RFC1051 也不支持 RFC1201 的数据包拆分，且 507 的 MTU 仍小于互联网的要求，因此很有可能会遇到问题。它也比 RFC1201 慢约 25%，原因与 arc0e 相同。
对 arc0s 的支持由 Tomasz Motylewski 贡献，并由我进行了部分修改。如果有 bug，很可能是我的责任。
你可以选择不在驱动中编译arc0e和arc0s——这将为你节省一些内存，并且在使用最近的Linux内核中的"NFS-root"功能时避免混淆。
arc0e和arc0s设备会在你首次配置arc0设备时自动创建。然而，要实际使用它们，还需要配置其他所需的虚拟设备。你可以通过以下几种方式设置网络：

1. 单协议
这是最简单的网络配置方法：仅使用两种可用协议中的一种。如上所述，除非你有特殊原因（例如某些仅支持arc0e的软件，如WfWg），否则最好只使用arc0。
如果你只需要arc0，以下命令应该可以让你开始使用：

```
ifconfig arc0 MY.IP.ADD.RESS
route add MY.IP.ADD.RESS arc0
route add -net SUB.NET.ADD.RESS arc0
[在此添加其他本地路由]
```

如果你需要arc0e（并且只使用arc0e），则略有不同：

```
ifconfig arc0 MY.IP.ADD.RESS
ifconfig arc0e MY.IP.ADD.RESS
route add MY.IP.ADD.RESS arc0e
route add -net SUB.NET.ADD.RESS arc0e
```

arc0s的工作方式与arc0e相似。

2. 在同一物理链路上使用多种协议
现在事情开始变得复杂了。要尝试这种方式，你可能需要有点疯狂。下面是我所做的一些尝试。:)
请注意，我没有在我的家庭网络中包含arc0s；因为我没有NetBSD或AmiTCP计算机，所以只在有限测试时使用arc0s。

我家庭网络中有三台计算机；两台运行Linux的操作系统（出于上述原因，它们更偏好RFC1201协议），以及一台无法运行Linux但安装了免费Microsoft LANMAN客户端的XT计算机。

更糟糕的是，其中一台Linux计算机（名为freedom）还装有一个调制解调器并作为到我的互联网服务提供商的路由器。另一台Linux计算机（名为insight）也有自己的IP地址，并且需要将freedom作为默认网关。而XT计算机（名为patience）没有自己的互联网IP地址，因此我在一个“私有子网”（根据RFC1597定义）中为其分配了一个IP地址。

首先，我们来看一个只有insight和freedom的简单网络。
Insight 需要：

- 通过 RFC1201 (arc0) 协议与 Freedom 通信，因为我更喜欢这种协议，而且它更快。
- 使用 Freedom 作为其互联网网关。

这样做非常简单。按照以下方式设置 Insight：

```
ifconfig arc0 insight
route add insight arc0
route add freedom arc0	/* 我会在这里使用子网（如我在“单一协议”部分所说），
					但不幸的是子网的其余部分跨过 Freedom 上的 PPP 链接，
				 这使事情变得复杂。*/
route add default gw freedom
```

而 Freedom 的配置如下：

```
ifconfig arc0 freedom
route add freedom arc0
route add insight arc0
/* 默认网关由 pppd 配置 */
```

这样，Insight 就可以直接在 arc0 上与 Freedom 通信，并通过 Freedom 发送数据包到互联网。如果你不知道如何进行上述操作，那么你可能应该停止阅读这一部分，因为接下来的内容只会更复杂。

现在，如何将 Patience 加入网络？它将使用 LANMAN 客户端，这意味着我需要 arc0e 设备。它需要能够与 Insight 和 Freedom 通信，并且还需要使用 Freedom 作为互联网网关。（回顾一下，Patience 拥有一个“私有 IP 地址”，这在互联网上是不可用的；没关系，我已经在 Freedom 上为这个子网配置了 Linux IP 伪装）

因此，Patience （不可避免地；我没有从我的供应商那里获得其他 IP 地址）拥有一个与 Freedom 和 Insight 不同子网的 IP 地址，但需要使用 Freedom 作为互联网网关。更糟糕的是，大多数 DOS 网络程序（包括 LANMAN）都有愚蠢的网络方案，完全依赖于子网掩码和“默认网关”来确定如何路由数据包。这意味着无论事实如何，Patience 要到达 Freedom 或 Insight 都会通过其默认网关发送数据包，尽管 Freedom 和 Insight（借助 arc0e 设备）可以理解直接传输。

我通过给 Freedom 分配一个额外的 IP 地址——别名为“Gatekeeper”——来解决这个问题，这个地址位于我的私有子网上，也就是 Patience 所在的子网。然后我将 Gatekeeper 定义为 Patience 的默认网关。

为了配置 Freedom（除了上面的命令之外）：

```
ifconfig arc0e gatekeeper
route add gatekeeper arc0e
route add patience arc0e
```

这样，Freedom 将通过 arc0e 发送所有针对 Patience 的数据包，将其 IP 地址设为 Gatekeeper（位于私有子网上）。当它与 Insight 或互联网通信时，它会使用其“Freedom”的互联网 IP 地址。

你会发现我们还没有在 Insight 上配置 arc0e 设备。这样做也可以，但并不是真的必要，而且需要我从我的私有子网中分配给 Insight 另一个特殊的 IP 地址。由于 Insight 和 Patience 都使用 Freedom 作为它们的默认网关，这两者已经可以互相通信了。

我很幸运第一次就这样设置了（咳咳），因为当我把 Insight 引导到 DOS 时，这是非常方便的。在那里，它运行 Novell ODI 协议栈，该协议栈仅支持 RFC1201 ARCnet。
在这种模式下，洞察（insight）无法直接与耐心（patience）通信，因为Novell堆栈与Microsoft的以太网封装（Ethernet-Encap）不兼容。在不改变自由（freedom）或耐心上的任何设置的情况下，我只是将自由设置为洞察的默认网关（现在是在DOS环境中），所有的转发就“自动地”在这两个通常无法通信的主机之间发生了。

对于喜欢图表的人来说，我在同一个物理ARCnet线上创建了两个“虚拟子网”。你可以这样想象：

```
	[RFC1201 NETWORK]                   [ETHER-ENCAP NETWORK]
	(注册的互联网子网)                (RFC1597私有子网)

				     (IP伪装)
	/---------------\         *            /---------------\
	|               |         *            |               |
	|               +-自由-*-网关-+               |
	|               |    |    *            |               |
	\-------+-------/    |    *            \-------+-------/
		  |            |                         |
	       洞察         |                      耐心
			   (互联网)
```

它工作了：接下来怎么办？
----------------------------

请发送邮件描述你的配置，最好包括驱动版本、内核版本、ARCnet卡型号、CPU类型、网络中的系统数量以及正在使用的软件列表，发给我如下地址：

	apenwarr@worldvisions.ca

我会回复所有收到的消息（有时是自动回复）。我的电子邮件可能会很奇怪（而且通常会在传递到我这里的过程中被转发很多地方），所以如果你在合理的时间内没有收到回复，请重新发送。

它不工作：接下来怎么办？
----------------------------

做同样的事情，但还要包含`ifconfig`和`route`命令的输出，以及任何相关的日志条目（即任何以“arcnet:”开头且自上次重启以来出现的日志条目）。

如果你想自己尝试解决问题（我强烈建议你先告诉我这个问题，因为它可能已经被解决了），你可以尝试一些可用的调试级别。对于大量的测试（例如D_DURING或更高），最好先关闭klogd守护进程！D_DURING在每个数据包发送或接收时显示4-5行信息。D_TX、D_RX和D_SKB实际上会在数据包发送或接收时显示每个数据包的内容，这显然是相当大的。

从v2.40 ALPHA开始，自动探测程序有了显著的变化。特别是，除非开启D_INIT_REASONS调试标志，否则它们不会告诉你为什么没有找到该卡。

一旦驱动程序运行起来，你可以作为root用户运行arcdump shell脚本（可以从我这里获取，或者在完整的ARCnet包中，如果你有的话）来随时列出ARCnet缓冲区的内容。要理解这些内容，你应该获取相关的RFC。（在arcnet.c顶部附近列出了部分RFC）。arcdump假设你的卡位于0xD0000。如果不是，请编辑脚本。

缓冲区0和1用于接收，而缓冲区2和3用于发送。乒乓缓冲区实现了双向操作。

如果你的调试级别包括D_DURING，并且你没有定义SLOW_XMIT_COPY，则每次重置卡时（这应该只在你执行ifconfig up或Linux认为驱动程序有问题时发生），缓冲区会被清零至一个常数值0x42。在传输过程中，未使用的缓冲区部分也会被清零至0x42。这是为了更容易确定哪些字节被数据包使用。

无需重新编译内核即可更改调试级别，方法如下：

```
ifconfig arc0 down metric 1xxx
/etc/rc.d/rc.inet1
```

其中“xxx”是你想要的调试级别。例如，“metric 1015”会将调试级别设置为15。当前默认的调试级别为7。
请注意，调试级别（从 v1.90 ALPHA 开始）是不同的调试标志的二进制组合；因此，调试级别 7 实际上是 1+2+4 或 D_NORMAL+D_EXTRA+D_INIT。若要包含 D_DURING，您需要在此基础上加上 16，结果就是调试级别 23。
如果您不明白这一点，您可能也不需要知道这些细节。
关于您的问题，请给我发邮件。
我想寄钱：现在怎么办？
-------------------------------
去睡个觉或者做点别的事情。早上起来您会感觉好些的。
