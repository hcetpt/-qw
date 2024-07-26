SPDX 许可证标识符: GPL-2.0

==============================
QorIQ DPAA 以太网驱动程序
==============================

作者:
- Madalin Bucur <madalin.bucur@nxp.com>
- Camelia Groza <camelia.groza@nxp.com>

.. 目录

	- DPAA 以太网概述
	- 支持的 DPAA 以太网 SoC
	- 在内核中配置 DPAA 以太网
	- DPAA 以太网帧处理
	- DPAA 以太网特性
	- DPAA 中断亲和力与接收侧扩展
	- 调试

DPAA 以太网概述
======================

DPAA 代表数据路径加速架构，它是一系列网络加速 IP 的集合，这些 IP 可用于多个代别的 SoC 上，包括 PowerPC 和 ARM64。Freescale 的 DPAA 架构由一系列支持以太网连接的硬件模块组成。以太网驱动程序依赖于 Linux 内核中的以下驱动程序：

 - 外围访问内存单元 (PAMU)（仅在 PPC 平台上需要）
    drivers/iommu/fsl_*
 - 帧管理器 (FMan)
    drivers/net/ethernet/freescale/fman
 - 队列管理器 (QMan)，缓冲区管理器 (BMan)
    drivers/soc/fsl/qbman

以下是简化后的 dpaa_eth 接口映射到 FMan MAC 的示意图：

  dpaa_eth       /eth0\     ...       /ethN\
  驱动程序      |      |             |      |
  -------------   ----   -----------   ----   -------------
       -端口  / Tx  Rx \    ...    / Tx  Rx \
  FMan        |          |         |          |
       -MAC   |   MAC0   |         |   MACN   |
	    /   dtsec0   \  ...  /   dtsecN   \ (或 tgec)
	    /              \     /              \(或 memac)
  ---------  --------------  ---  --------------  ---------
      FMan, FMan 端口, FMan SP, FMan MURAM 驱动程序
  ---------------------------------------------------------
      FMan 硬件模块: MURAM, MACs, 端口, SP
  ---------------------------------------------------------

dpaa_eth 与 QMan、BMan 和 FMan 的关系如下所示：

	      ________________________________
  dpaa_eth   /            eth0                \
  驱动程序  /                                  \
  ---------   -^-   -^-   -^-   ---    ---------
  QMan 驱动程序 / \   / \   / \  \   /  | BMan    |
	     |Rx | |Rx | |Tx | |Tx |  | 驱动程序  |
  ---------  |Dfl| |Err| |Cnf| |FQs|  |         |
  QMan 硬件    |FQ | |FQ | |FQs| |   |  |         |
	     /   \ /   \ /   \  \ /   |         |
  ---------   ---   ---   ---   -v-    ---------
	    |        FMan QMI         |         |
	    | FMan 硬件       FMan BMI  | BMan 硬件 |
	      -----------------------   --------

其中上文提到的缩写词及其含义为：

=============== ===========================================================
DPAA 		数据路径加速架构
FMan 		DPAA 帧管理器
QMan 		DPAA 队列管理器
BMan 		DPAA 缓冲区管理器
QMI 		QMan 在 FMan 中的接口
BMI 		BMan 在 FMan 中的接口
FMan SP 	FMan 存储配置文件
MURAM 		FMan 中的多用户 RAM
FQ 		QMan 帧队列
Rx Dfl FQ 	默认接收 FQ
Rx Err FQ 	接收错误帧 FQ
Tx Cnf FQ 	传输确认 FQ
Tx FQs 		传输帧队列
dtsec 		数据路径三速以太网控制器 (10/100/1000 Mbps)
tgec 		十吉比特以太网控制器 (10 Gbps)
memac 		多速率以太网 MAC (10/100/1000/10000)
=============== ===========================================================

支持的 DPAA 以太网 SoC
============================

DPAA 驱动程序使以下 SoC 上的以太网控制器得以启用：

PPC
- P1023
- P2041
- P3041
- P4080
- P5020
- P5040
- T1023
- T1024
- T1040
- T1042
- T2080
- T4240
- B4860

ARM
- LS1043A
- LS1046A

在内核中配置 DPAA 以太网
========================================

要启用 DPAA 以太网驱动程序，需要以下 Kconfig 选项：

  # 对于 arch/arm64 和 arch/powerpc 平台都是通用的
  CONFIG_FSL_DPAA=y
  CONFIG_FSL_FMAN=y
  CONFIG_FSL_DPAA_ETH=y
  CONFIG_FSL_XGMAC_MDIO=y

  # 仅对于 arch/powerpc
  CONFIG_FSL_PAMU=y

  # 适用于 RDBs 上使用的 PHY 所需的通用选项
  CONFIG_VITESSE_PHY=y
  CONFIG_REALTEK_PHY=y
  CONFIG_AQUANTIA_PHY=y

DPAA 以太网帧处理
==============================

在接收时，从专用接口缓冲池中获取传入帧的缓冲区。驱动程序初始化并填充这些缓冲区为一页大小。
在发送时，所有已发送的帧通过发送确认帧队列返回给驱动程序。然后驱动程序负责释放这些缓冲区。为了正确地完成这个操作，在发送前会在缓冲区中添加一个指向 skb 的回指针。当缓冲区通过确认 FQ 返回给驱动程序时，可以正确地消耗 skb。
DPAA 以太网特性
======================

目前 DPAA 以太网驱动程序启用了基本的特性，这是 Linux 以太网驱动程序所必需的。对高级特性的支持将逐步增加。
该驱动程序具有 UDP 和 TCP 的接收和发送校验和卸载功能。目前，接收校验和卸载功能默认启用，并且不能通过 ethtool 控制。此外，还增加了 rx-flow-hash 和 rx-hashing 功能。RSS 的加入为转发场景提供了显著的性能提升，允许一个接口接收到的不同流量流可以被不同的 CPU 并行处理。
该驱动程序支持多个优先级的发送交通类别。优先级范围从 0（最低）到 3（最高）。这些被映射到具有严格优先级级别的硬件工作队列。每个交通类别包含 NR_CPU 发送队列。默认情况下，仅启用一个交通类别，并使用最低优先级的发送队列。可以通过 mqprio qdisc 启用更高的优先级交通类别。例如，所有四个交通类别可以在一个接口上通过以下命令启用。此外，skb 的优先级级别被映射到交通类别如下：

	* 优先级 0 到 3 - 交通类别 0（低优先级）
	* 优先级 4 到 7 - 交通类别 1（中低优先级）
	* 优先级 8 到 11 - 交通类别 2（中高优先级）
	* 优先级 12 到 15 - 交通类别 3（高优先级）

::

  tc qdisc add dev <int> root handle 1: \
	 mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 hw 1

DPAA 中断亲和力与接收侧扩展
==========================================

来自 DPAA 接收队列或 DPAA 发送确认队列的流量被视为特定门户上的 CPU 入站流量。
DPAA QMan 门户中断各自绑定到某个 CPU。
相同的门户中断服务于所有的 QMan 门户消费者。
默认情况下，DPAA 以太网驱动程序启用 RSS，利用 DPAA FMan 解析器和密钥生成块来使用基于接收到的帧中的 IPv4/v6 源和目标以及第 4 层源和目标端口的哈希值将流量分布到 128 个硬件帧队列上。
当禁用 RSS 时，某个接口接收到的所有流量都在默认接收帧队列上接收。默认的 DPAA 接收帧队列被配置为将接收到的流量放入一个通道池中，这允许任何可用的 CPU 门户来出列入站流量。
默认的帧队列设置了HOLDACTIVE选项，确保来自特定队列的突发流量由同一CPU处理。
这保证了非常低的帧重排序率。但缺点是当未启用RSS时，某一接口接收到的流量只能由一个CPU处理。

为了实现RSS（接收侧缩放），DPAA以太网驱动分配了一组额外的128个Rx帧队列，并以循环方式配置到专用通道中。帧队列与CPU的映射现在被硬编码，没有间接表来将特定FQ（哈希结果）的流量转移到另一个CPU。到达这些帧队列之一的入站流量将到达相同的端口，并始终由同一个CPU处理。这样既保证了流内部顺序的保持，也实现了多流量流的工作负载分布。

可以通过ethtool关闭某个接口上的RSS功能，例如：

	# ethtool -N fm1-mac9 rx-flow-hash tcp4 ""

要重新启用它，需要为tcp4/6或udp4/6设置rx-flow-hash，例如：

	# ethtool -N fm1-mac9 rx-flow-hash udp4 sfdn

对于各个协议没有独立的控制，针对tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6中的任何一个命令都会控制该接口上所有协议的rx-flow-hashing。

除了使用FMan Keygen计算出的哈希值来在128个Rx FQ之间分散流量之外，当NETIF_F_RXHASH特性开启（默认激活）时，DPAA以太网驱动也会设置skb哈希值。这可以通过ethtool打开或关闭，例如：

	# ethtool -K fm1-mac9 rx-hashing off
	# ethtool -k fm1-mac9 | grep hash
	receive-hashing: off
	# ethtool -K fm1-mac9 rx-hashing on
	实际更改：
	receive-hashing: on
	# ethtool -k fm1-mac9 | grep hash
	receive-hashing: on

请注意，Rx哈希依赖于该接口上的rx-flow-hashing处于开启状态——关闭rx-flow-hashing也会禁用rx-hashing（ethtool不会报告其为关闭，因为它取决于NETIF_F_RXHASH特性标志）。

调试
=====

以下统计信息通过ethtool为每个接口导出：

	- 每个CPU的中断计数
	- 每个CPU的接收数据包计数
	- 每个CPU的发送数据包计数
	- 每个CPU的确认发送数据包计数
	- 每个CPU的S/G帧发送计数
	- 每个CPU的发送错误计数
	- 每个CPU的接收错误计数
	- 按类型划分的接收错误计数
	- 与拥塞相关的统计数据：

		- 拥塞状态
		- 处于拥塞的时间
		- 设备进入拥塞状态的次数
		- 按原因划分的丢弃数据包计数

驱动还通过sysfs导出了以下信息：

	- 每种FQ类型的FQ ID
	  /sys/devices/platform/soc/<addr>.fman/<addr>.ethernet/dpaa-ethernet.<id>/net/fm<nr>-mac<nr>/fqids

	- 正在使用的缓冲池ID
	  /sys/devices/platform/soc/<addr>.fman/<addr>.ethernet/dpaa-ethernet.<id>/net/fm<nr>-mac<nr>/bpids
