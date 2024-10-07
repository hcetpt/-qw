SPDX 许可声明标识符: GPL-2.0+

==============================================================
Synopsys(R) 以太网控制器的 Linux 驱动 "stmmac"
==============================================================

作者: Giuseppe Cavallaro <peppe.cavallaro@st.com>,
Alexandre Torgue <alexandre.torgue@st.com>, Jose Abreu <joabreu@synopsys.com>

内容
========

- 本发行版中的内容
- 功能列表
- 内核配置
- 命令行参数
- 驱动信息和说明
- 调试信息
- 支持

本发行版中的内容
===============

此文件描述了适用于所有 Synopsys(R) 以太网控制器的 stmmac Linux 驱动。
目前，此网络设备驱动适用于所有 STi 嵌入式 MAC/GMAC（即 7xxx/5xxx SoC），SPEAr（arm），Loongson1B（mips）以及 XILINX XC2V3000 FF1152AMT0221 D1215994A VIRTEX FPGA 板。Synopsys 以太网 QoS 5.0 IPK 也得到了支持。
此驱动使用了 DesignWare(R) Cores 10/100/1000 通用版 3.70a 及其早期版本以及 DesignWare(R) Cores 以太网服务质量版 4.0 及其更高版本，并且还包括了 DesignWare(R) Cores XGMAC - 10G 以太网 MAC 和 DesignWare(R) Cores 企业级 MAC - 100G 以太网 MAC。
此驱动同时支持平台总线和 PCI 总线。
此驱动包括对以下 Synopsys(R) DesignWare(R) Cores 以太网控制器及其对应的最小和最大版本的支持：

+-------------------------------+--------------+--------------+--------------+
| 控制器名称                     | 最小版本      | 最大版本      | 简称         |
+===============================+==============+==============+==============+
| 通用以太网 MAC                | N/A          | 3.73a        | GMAC         |
+-------------------------------+--------------+--------------+--------------+
| 以太网服务质量                 | 4.00a        | N/A          | GMAC4+       |
+-------------------------------+--------------+--------------+--------------+
| XGMAC - 10G 以太网 MAC         | 2.10a        | N/A          | XGMAC2+      |
+-------------------------------+--------------+--------------+--------------+
| XLGMAC - 100G 以太网 MAC       | 2.00a        | N/A          | XLGMAC2+     |
+-------------------------------+--------------+--------------+--------------+

有关硬件要求的问题，请参阅随您的以太网适配器提供的文档。列出的所有硬件要求均适用于 Linux 使用。

功能列表
============

此驱动提供了以下功能：
 - GMII/MII/RGMII/SGMII/RMII/XGMII/XLGMII 接口
 - 半双工/全双工操作
 - 能效以太网（EEE）
 - IEEE 802.3x 暂停包（流控制）
 - RMON/MIB 计数器
 - IEEE 1588 时间戳（PTP）
 - 每秒脉冲输出（PPS）
 - MDIO 第 22/45 款接口
 - MAC 环回
 - ARP 卸载
 - 自动 CRC/PAD 插入和检查
 - 发送和接收数据包的校验和卸载
 - 标准或巨型以太网数据包
 - 源地址插入/替换
 - VLAN 标签插入/替换/删除/过滤（HASH 和 PERFECT）
 - 可编程 TX 和 RX 看门狗和合并设置
 - 目标地址过滤（PERFECT）
 - HASH 过滤（多播）
 - 第 3 层/第 4 层过滤
 - 远程唤醒检测
 - 接收端扩展（RSS）
 - 发送和接收帧抢占
 - 可编程突发长度、阈值、队列大小
 - 多个队列（最多 8 个）
 - 多种调度算法（发送：WRR, DWRR, WFQ, SP, CBS, EST, TBS；接收：WRR, SP）
 - 灵活的 RX 解析器
 - TCP/UDP 分段卸载（TSO, USO）
 - 分割报头（SPH）
 - 安全特性（ECC 保护、数据奇偶校验保护）
 - 使用 ethtool 的自检

内核配置
====================

内核配置选项为 ``CONFIG_STMMAC_ETH``：
 - ``CONFIG_STMMAC_PLATFORM``：启用平台驱动
- ``CONFIG_STMMAC_PCI``：启用 PCI 驱动

命令行参数
=======================

如果将驱动编译为模块，则可以通过在命令行中使用 modprobe 命令并使用以下语法来使用这些可选参数（例如对于 PCI 模块）：

```
modprobe stmmac_pci [<option>=<VAL1>,<VAL2>,...]
```

也可以通过命令行传递驱动参数：

```
stmmaceth=watchdog:100,chain_mode=1
```

每个参数的默认值通常是推荐的设置，除非另有说明。

watchdog
--------
:有效范围: 5000-无
:默认值: 5000

此参数覆盖了以毫秒为单位的传输超时时间。

debug
-----
:有效范围: 0-16（0=无，..., 16=全部）
:默认值: 0

此参数调整系统日志中显示的调试消息级别。
### phyaddr
- **有效范围**: 0-31
- **默认值**: -1

此参数覆盖 PHY 设备的物理地址。

### flow_ctrl
- **有效范围**: 0-3（0=关闭，1=接收，2=发送，3=接收/发送）
- **默认值**: 3

此参数更改默认的流控制能力。

### pause
- **有效范围**: 0-65535
- **默认值**: 65535

此参数更改默认的流控制暂停时间。

### tc
- **有效范围**: 64-256
- **默认值**: 64

此参数更改默认的硬件 FIFO 阈值控制值。

### buf_sz
- **有效范围**: 1536-16384
- **默认值**: 1536

此参数更改默认的 RX DMA 数据包缓冲区大小。

### eee_timer
- **有效范围**: 0-无
- **默认值**: 1000

此参数更改默认的 LPI TX 过期时间（以毫秒为单位）。

### chain_mode
- **有效范围**: 0-1（0=关闭，1=开启）
- **默认值**: 0

此参数更改默认的操作模式，从环形模式更改为链式模式。

### 驱动信息和注意事项

#### 发送过程

当内核需要发送一个数据包时，会调用 `xmit` 方法；它设置环中的描述符，并通知 DMA 引擎有数据包准备好发送。
默认情况下，驱动程序在 `net_device` 结构的 `features` 字段中设置了 `NETIF_F_SG` 标志位，启用了分散/聚集功能。这是在可以进行硬件校验和的情况下。
一旦控制器完成数据包的发送，将安排定时器释放发送资源。
接收过程
---------------
当接收到一个或多个数据包时，会产生中断。中断不会被排队，因此驱动程序在接收过程中必须扫描环中的所有描述符。
这是基于NAPI的，因此中断处理程序仅在有工作需要完成时发出信号，然后退出。随后，在某个未来的时刻将调度轮询方法。
传入的数据包由DMA存储在一个预先分配的套接字缓冲区列表中，以避免使用memcpy（零复制）。

中断缓解
--------------------
对于3.50版本之前的芯片，驱动程序能够通过NAPI来减少DMA中断的数量。新芯片有一个硬件接收端看门狗用于这种缓解措施。
可以通过ethtool调整缓解参数。

WoL
---
通过Magic和单播帧支持GMAC、GMAC4/5和XGMAC核心的局域网唤醒功能。

DMA描述符
---------------
驱动程序处理普通描述符和备用描述符。后者仅在DesignWare® Cores Ethernet MAC Universal 3.41a及更高版本上进行了测试。
stmmac支持DMA描述符在双缓冲（RING）模式和链表（CHAINED）模式下运行。在RING模式下，每个描述符指向两个数据缓冲区指针；而在CHAINED模式下，它们只指向一个数据缓冲区指针。
默认模式为RING模式。
在CHAINED模式下，每个描述符将包含指向列表中下一个描述符的指针，从而在描述符本身中创建显式的链式结构，而在RING模式下无法实现这种显式的链式结构。
扩展描述符
--------------------

扩展描述符提供了关于以太网负载的信息，当其携带PTP数据包或TCP/UDP/ICMP通过IP时。这些功能在早于3.50版本的GMAC Synopsys®芯片上不可用。在探测期间，驱动程序将决定是否可以实际使用这些描述符。对于PTPv2而言，这种支持是强制性的，因为额外的描述符用于保存硬件时间戳和扩展状态。

Ethtool 支持
---------------

Ethtool得到了支持。例如，可以通过以下命令获取驱动程序统计信息（包括RMON）和内部错误：

    ethtool -S ethX

Ethtool自测也得到支持。这允许使用MAC和PHY环回机制进行一些初步的硬件检查：

    ethtool -t ethX

巨型帧和分段卸载
---------------------------------

GMAC支持并测试了巨型帧。GSO（分段卸载）也被加入，但其操作是在软件中完成的。LRO（大型接收卸载）不被支持。

TSO（TCP分段卸载）支持
--------------

TSO（TCP分段卸载）功能由GMAC > 4.x 和 XGMAC芯片家族支持。当通过TCP协议发送数据包时，TCP堆栈确保提供给低级驱动程序（在本例中为stmmac）的SKB与最大帧长度匹配（IP头 + TCP头 + 负载 ≤ 1500字节，对于MTU设置为1500）。这意味着如果使用TCP的应用程序要发送一个长度（加上头部后）大于1514字节的数据包，则该数据包会被拆分成多个TCP数据包：数据负载被分割，并添加头部（TCP/IP等）。这是由软件完成的。
当启用TSO时，TCP堆栈不会关心最大帧长度，并将SKB数据包原样提供给stmmac。GMAC IP必须自行执行分段以匹配最大帧长度。
此功能可以通过设备树中的“snps,tso”条目启用。

能效以太网
-------------------------

能效以太网（EEE）使IEEE 802.3 MAC子层和一系列物理层能够在低功耗闲置（LPI）模式下运行。EEE模式支持在100Mbps、1000Mbps和1Gbps速率下的IEEE 802.3 MAC操作。
LPI模式通过在没有数据需要传输和接收时关闭通信设备的部分功能来节省电力。
链路两端的系统可以在链路利用率低的期间禁用某些功能并节省电力。MAC控制着系统何时进入或退出LPI模式，并将这一信息传达给PHY。
一旦接口被打开，驱动程序会检查EEE是否可以被支持。这是通过查看DMA硬件能力寄存器和PHY设备的MCD寄存器来实现的。
为了进入TX LPI模式，驱动程序需要有一个软件定时器，在没有任何东西需要传输时启用和禁用LPI模式。
精度时间协议（PTP）
-----------------------------

该驱动支持IEEE 1588-2002精度时间协议（PTP），该协议能够在使用网络通信等技术实现的测量和控制系统中实现精确的时间同步。除了IEEE 1588-2002中提到的基本时间戳功能外，新的GMAC核心还支持IEEE 1588-2008中的高级时间戳功能。当配置内核时可以启用这些功能。

SGMII/RGMII 支持
-------------------

新的GMAC设备提供了自己管理RGMII/SGMII的方法。此信息在运行时通过查看硬件能力寄存器获得。这意味着stmmac可以在不使用PHYLIB的情况下管理自动协商和链路状态。事实上，硬件提供了一组扩展寄存器来重启自动协商、验证全双工/半双工模式和速度。借助这些寄存器，可以查看自动协商的链路伙伴能力。

物理层
--------

该驱动与物理抽象层兼容，可连接PHY和GPHY设备。

平台信息
--------------------

可以通过平台和设备树传递多种信息：
```
struct plat_stmmacenet_data {
1) 总线标识符：
        int bus_id;

2) PHY物理地址。如果设置为-1，则驱动程序将选择找到的第一个PHY：
        int phy_addr;

3) PHY设备接口：
        int interface;

4) MDIO总线特定平台字段：
        struct stmmac_mdio_bus_data *mdio_bus_data;

5) 内部DMA参数：
        struct stmmac_dma_cfg *dma_cfg;

6) 固定CSR时钟范围选择：
        int clk_csr;

7) 硬件使用GMAC核心：
        int has_gmac;

8) 如果设置，则MAC将使用增强描述符：
        int enh_desc;

9) 核心能够在硬件中执行TX校验和和/或RX校验和：
        int tx_coe;
        int rx_coe;

11) 由于缓冲区大小有限，某些硬件无法在硬件中处理超大帧的校验和。设置此标志后，将在软件中对巨型帧进行校验和：
        int bugged_jumbo;

12) 核心具有嵌入式电源模块：
        int pmt;

13) 强制DMA使用存储转发模式或阈值模式：
        int force_sf_dma_mode;
        int force_thresh_dma_mode;

15) 强制禁用RX看门狗功能并切换到NAPI模式：
        int riwt_off;

16) 限制最大操作速度和MTU：
        int max_speed;
        int maxmtu;

18) 多播/单播过滤器数量：
        int multicast_filter_bins;
        int unicast_filter_entries;

20) 限制最大TX和RX FIFO大小：
        int tx_fifo_size;
        int rx_fifo_size;

21) 使用指定数量的TX和RX队列：
        u32 rx_queues_to_use;
        u32 tx_queues_to_use;

22) 使用指定的TX和RX调度算法：
        u8 rx_sched_algorithm;
        u8 tx_sched_algorithm;

23) 内部TX和RX队列参数：
        struct stmmac_rxq_cfg rx_queues_cfg[MTL_MAX_RX_QUEUES];
        struct stmmac_txq_cfg tx_queues_cfg[MTL_MAX_TX_QUEUES];

24) 此回调用于根据物理层协商的链路速度修改一些syscfg寄存器（在ST SoC上）：
        void (*fix_mac_speed)(void *priv, unsigned int speed);

25) 用于调用自定义初始化的回调；在某些平台上（例如ST盒子）有时需要设置一些PIO线或系统配置寄存器。初始化/退出回调不应使用或修改平台数据：
        int (*init)(struct platform_device *pdev, void *priv);
        void (*exit)(struct platform_device *pdev, void *priv);

26) 执行总线硬件设置。例如，在某些ST平台上，此字段用于配置AMBA桥以生成更有效的STBus流量：
        struct mac_device_info *(*setup)(void *priv);
        void *bsp_priv;

27) 内部时钟和速率：
        struct clk *stmmac_clk;
        struct clk *pclk;
        struct clk *clk_ptp_ref;
        unsigned int clk_ptp_rate;
        unsigned int clk_ref_rate;
        s32 ptp_max_adj;

28) 主重置：
        struct reset_control *stmmac_rst;

29) AXI内部参数：
        struct stmmac_axi *axi;

30) 硬件使用GMAC>4核心：
        int has_gmac4;

31) 硬件基于sun8i：
        bool has_sun8i;

32) 启用TSO功能：
        bool tso_en;

33) 启用接收端扩展（RSS）功能：
        int rss_en;

34) MAC端口选择：
        int mac_port_sel_speed;

35) 启用TX低功耗时钟门控：
        bool en_tx_lpi_clockgating;

36) 硬件使用XGMAC>2.10核心：
        int has_xgmac;
}
```

对于MDIO总线数据，我们有：
```
struct stmmac_mdio_bus_data {
1) 注册MDIO总线时传递的PHY掩码：
        unsigned int phy_mask;

2) 每个PHY的一个IRQ列表：
        int *irqs;

3) 如果IRQs为NULL，则使用此值作为探测到的PHY的IRQ：
        int probed_phy_irq;

4) 如果PHY需要重置则设置为true：
        bool needs_reset;
}
```

对于DMA引擎配置，我们有：
```
struct stmmac_dma_cfg {
1) 可编程突发长度（TX和RX）：
        int pbl;

2) 如果设置，则DMA TX / RX将使用此值而不是pbl：
        int txpbl;
        int rxpbl;

3) 启用8xPBL：
        bool pblx8;

4) 启用固定或混合突发：
        int fixed_burst;
        int mixed_burst;

5) 启用地址对齐节拍：
        bool aal;

6) 启用增强地址（> 32位）：
        bool eame;
}
```

对于DMA AXI参数，我们有：
```
struct stmmac_axi {
1) 启用AXI LPI：
        bool axi_lpi_en;
        bool axi_xit_frm;

2) 设置AXI写/读最大未完成请求：
        u32 axi_wr_osr_lmt;
        u32 axi_rd_osr_lmt;

3) 设置AXI 4KB突发：
        bool axi_kbbe;

4) 设置AXI最大突发长度映射：
        u32 axi_blen[AXI_BLEN];

5) 设置AXI固定突发/混合突发：
        bool axi_fb;
        bool axi_mb;

6) 设置AXI重建incrx模式：
        bool axi_rb;
}
```

对于RX队列配置，我们有：
```
struct stmmac_rxq_cfg {
1) 要使用的模式（DCB或AVB）：
        u8 mode_to_use;

2) 要使用的DMA通道：
        u32 chan;

3) 如果适用，则设置数据包路由：
        u8 pkt_route;

4) 使用优先级路由及优先级：
        bool use_prio;
        u32 prio;
}
```

对于TX队列配置，我们有：
```
struct stmmac_txq_cfg {
1) 在调度器中的队列权重：
        u32 weight;

2) 要使用的模式（DCB或AVB）：
        u8 mode_to_use;

3) 基于信用整形参数：
        u32 send_slope;
        u32 idle_slope;
        u32 high_credit;
        u32 low_credit;

4) 使用优先级调度及优先级：
        bool use_prio;
        u32 prio;
}
```

设备树信息
-----------------------

请参阅以下文档：Documentation/devicetree/bindings/net/snps,dwmac.yaml

硬件能力
-----------------------

请注意，从新芯片开始，如果存在硬件能力寄存器，则许多配置都可以在运行时发现，例如了解EEE、硬件校验和、PTP、增强描述符等是否可用。该驱动采用的策略是，硬件能力寄存器中的信息可以替换从平台传递的信息。

调试信息
=================

该驱动导出了许多信息，如内部统计、调试信息、MAC和DMA寄存器等。
这些信息可以根据实际需求以不同方式读取。
例如，用户可以使用ethtool支持获取统计信息：例如
使用 `ethtool -S ethX`（如果支持的话，这会显示管理计数器（MMC））或查看MAC/DMA寄存器：例如，使用 `ethtool -d ethX`

编译内核时启用 `CONFIG_DEBUG_FS`，驱动程序将导出以下 debugfs 条目：

- `descriptors_status`：显示 DMA TX/RX 描述符环
- `dma_cap`：显示硬件功能

开发者还可以使用 `debug` 模块参数以获取更多的调试信息（请参阅：NETIF 消息级别）

支持
=====

如果在受支持的内核上使用受支持的适配器发现源代码存在问题，请将与问题相关的确切信息发送至 netdev@vger.kernel.org
