QorIQ DPAA 以太网驱动程序

作者:
- Madalin Bucur <madalin.bucor@nxp.com>
- Camelia Groza <camelia.groza@nxp.com>

目录
- DPAA 以太网概述
- 支持的 DPAA 以太网 SoC
- 在内核中配置 DPAA 以太网
- DPAA 以太网帧处理
- DPAA 以太网功能
- DPAA 中断亲和性和接收侧扩展
- 调试

DPAA 以太网概述
======================

DPAA 指的是数据路径加速架构（Data Path Acceleration Architecture），它是一组在多代 SoC 上可用的网络加速 IP，包括 PPC 和 ARM64 平台。Freescale 的 DPAA 架构包含一系列支持以太网连接的硬件块。以太网驱动依赖于以下 Linux 内核中的驱动程序：

- 周边访问内存单元（PAMU）（仅适用于 PPC 平台）
  `drivers/iommu/fsl_*`
- 帧管理器（FMan）
  `drivers/net/ethernet/freescale/fman`
- 队列管理器（QMan），缓冲区管理器（BMan）
  `drivers/soc/fsl/qbman`

一个简化的 dpaa_eth 接口映射到 FMan MAC 的示意图如下：

```
dpaa_eth       /eth0\     ...       /ethN\
driver        |      |             |      |
-------------   ----   -----------   ----   -------------
       -Ports  / Tx  Rx \    ...    / Tx  Rx \
FMan        |          |         |          |
       -MACs  |   MAC0   |         |   MACN   |
	     /   dtsec0   \  ...  /   dtsecN   \ (或 tgec)
	    /              \     /              \(或 memac)
  ---------  --------------  ---  --------------  ---------
      FMan, FMan Port, FMan SP, FMan MURAM 驱动
  ---------------------------------------------------------
      FMan 硬件块：MURAM, MACs, Ports, SP
  ---------------------------------------------------------
```

dpaa_eth 与 QMan、BMan 和 FMan 的关系如下：

```
	      ________________________________
dpaa_eth   /            eth0                \
driver    /                                  \
---------   -^-   -^-   -^-   ---    ---------
QMan 驱动 / \   / \   / \  \   /  | BMan    |
	     |Rx | |Rx | |Tx | |Tx |  | 驱动  |
---------  |Dfl| |Err| |Cnf| |FQs|  |       |
QMan 硬件    |FQ | |FQ | |FQs| |   |  |       |
	     /   \ /   \ /   \  \ /   |       |
---------   ---   ---   ---   -v-    ---------
	    |        FMan QMI         |       |
	    | FMan 硬件       FMan BMI  | BMan 硬件 |
	      -----------------------   --------
```

其中使用的缩写词及其含义如下：

| 缩写 | 含义 |
|------|----------------------------------------------------------|
| DPAA | 数据路径加速架构 |
| FMan | DPAA 帧管理器 |
| QMan | DPAA 队列管理器 |
| BMan | DPAA 缓冲区管理器 |
| QMI  | QMan 在 FMan 中的接口 |
| BMI  | BMan 在 FMan 中的接口 |
| FMan SP | FMan 存储配置文件 |
| MURAM | FMan 中的多用户 RAM |
| FQ   | QMan 帧队列 |
| Rx Dfl FQ | 默认接收 FQ |
| Rx Err FQ | 接收错误帧 FQ |
| Tx Cnf FQ | 发送确认 FQ |
| Tx FQs | 发送帧队列 |
| dtsec | 数据路径三速以太网控制器（10/100/1000 Mbps） |
| tgec | 十吉比特以太网控制器（10 Gbps） |
| memac | 多速率以太网 MAC（10/100/1000/10000） |

支持的 DPAA 以太网 SoC
============================

DPAA 驱动程序启用了以下 SoC 上的以太网控制器：

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

```plaintext
# 对于 arm64 和 powerpc 平台通用
CONFIG_FSL_DPAA=y
CONFIG_FSL_FMAN=y
CONFIG_FSL_DPAA_ETH=y
CONFIG_FSL_XGMAC_MDIO=y

# 仅适用于 powerpc 平台
CONFIG_FSL_PAMU=y

# 用于 RDBs 上使用的 PHY 的通用选项
CONFIG_VITESSE_PHY=y
CONFIG_REALTEK_PHY=y
CONFIG_AQUANTIA_PHY=y
```

DPAA 以太网帧处理
==============================

在接收（Rx）时，从专用接口缓冲池中获取传入帧的缓冲区。驱动程序初始化并填充这些缓冲区为一页大小。
在发送（Tx）时，所有已发送的帧通过发送确认帧队列返回给驱动程序。然后驱动程序负责释放这些缓冲区。为了正确完成此操作，在传输前向缓冲区添加一个回指针，指向 skb。当缓冲区通过确认 FQ 返回给驱动程序时，skb 可以被正确消费。

DPAA 以太网功能
======================

目前 DPAA 以太网驱动程序实现了基本功能，满足 Linux 以太网驱动的要求。对高级功能的支持将逐步增加。
该驱动程序支持 UDP 和 TCP 的接收和发送校验和卸载。目前，接收校验和卸载功能默认启用，并且无法通过 ethtool 控制。此外，还增加了 rx-flow-hash 和 rx-hashing。RSS 的加入为转发场景提供了显著的性能提升，允许不同流量流由不同 CPU 并行处理。
该驱动程序支持多个优先级的发送流量类。优先级范围从 0（最低）到 3（最高）。这些映射到具有严格优先级级别的硬件工作队列。每个流量类包含 NR_CPU TX 队列。默认情况下，仅启用一个流量类，并使用最低优先级的 TX 队列。可以通过 mqprio qdisc 启用更高优先级的流量类。例如，可以在接口上使用以下命令启用所有四个流量类。此外，skb 优先级级别映射到流量类如下：

- 优先级 0 到 3 - 流量类 0（低优先级）
- 优先级 4 到 7 - 流量类 1（中低优先级）
- 优先级 8 到 11 - 流量类 2（中高优先级）
- 优先级 12 到 15 - 流量类 3（高优先级）

```plaintext
tc qdisc add dev <int> root handle 1: \
	 mqprio num_tc 4 map 0 0 0 0 1 1 1 1 2 2 2 2 3 3 3 3 hw 1
```

DPAA 中断亲和性和接收侧扩展
==========================================

来自 DPAA 接收队列或 DPAA 发送确认队列的流量被视为在特定端口上的传入流量。
DPAA QMan 端口中断与特定 CPU 绑定。
相同的端口中断服务于所有 QMan 端口消费者。
默认情况下，DPAA 以太网驱动程序启用了 RSS，利用 DPAA FMan 解析器和 Keygen 块来使用哈希算法分发流量到 128 个硬件帧队列，哈希算法基于接收到的帧中的 IPv4/v6 源和目标地址以及第 4 层源和目标端口。
当禁用 RSS 时，所有通过特定接口接收到的流量都在默认的接收帧队列上接收。默认的 DPAA 接收帧队列配置为将接收到的流量放入一个池通道中，允许任何可用的 CPU 端口取消排队传入流量。
默认的帧队列设置了HOLDACTIVE选项，确保来自某个队列的流量突发由同一个CPU处理。这保证了非常低的帧重排序率。缺点是当没有启用RSS时，某一接口接收的流量只能由一个CPU处理。

为了实现RSS（接收侧扩展），DPAA以太网驱动分配了一组额外的128个Rx帧队列，并以轮询方式配置到专用通道中。帧队列到CPU的映射现在是硬编码的，没有间接表来将特定FQ（哈希结果）的流量移动到另一个CPU。到达这些帧队列之一的入站流量将到达相同的端口，并且始终由同一CPU处理。这确保了流内顺序保持和多路流量的工作负载分发。

可以使用ethtool为某个接口关闭RSS，例如：

	# ethtool -N fm1-mac9 rx-flow-hash tcp4 ""

要重新启用它，需要为tcp4/6或udp4/6设置rx-flow-hash，例如：

	# ethtool -N fm1-mac9 rx-flow-hash udp4 sfdn

对于单个协议没有独立控制，对tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6中的任何一个运行命令都将控制该接口上所有协议的rx-flow-hashing。

除了使用FMan Keygen计算的哈希值在128个Rx FQ上分散流量外，当启用了NETIF_F_RXHASH特性（默认激活）时，DPAA以太网驱动还会设置skb哈希值。这可以通过ethtool打开或关闭，例如：

	# ethtool -K fm1-mac9 rx-hashing off
	# ethtool -k fm1-mac9 | grep hash
	receive-hashing: off
	# ethtool -K fm1-mac9 rx-hashing on
	实际更改：
	receive-hashing: on
	# ethtool -k fm1-mac9 | grep hash
	receive-hashing: on

请注意，Rx哈希依赖于该接口上的rx-flow-hashing处于开启状态——关闭rx-flow-hashing也会禁用rx-hashing（ethtool不会报告其为关闭，因为这取决于NETIF_F_RXHASH特性标志）。

调试
=====

以下统计信息通过ethtool为每个接口导出：

- 每个CPU的中断计数
- 每个CPU的接收包计数
- 每个CPU的发送包计数
- 每个CPU的确认发送包计数
- 每个CPU的发送S/G帧计数
- 每个CPU的发送错误计数
- 每个CPU的接收错误计数
- 按类型划分的接收错误计数
- 与拥塞相关的统计信息：

    - 拥塞状态
    - 处于拥塞状态的时间
    - 设备进入拥塞状态的次数
    - 按原因划分的丢弃包计数

驱动程序还在sysfs中导出了以下信息：

- 每种FQ类型的FQ ID
  /sys/devices/platform/soc/<addr>.fman/<addr>.ethernet/dpaa-ethernet.<id>/net/fm<nr>-mac<nr>/fqids

- 当前使用的缓冲池ID
  /sys/devices/platform/soc/<addr>.fman/<addr>.ethernet/dpaa-ethernet.<id>/net/fm<nr>-mac<nr>/bpids
