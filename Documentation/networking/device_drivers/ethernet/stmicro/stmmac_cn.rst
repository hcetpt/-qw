以下是文档的中文翻译：

---

### SPDX 许可证标识符: GPL-2.0+

=================================================================================================
### Linux 驱动程序针对Synopsys® 以太网控制器 "stmmac"
=================================================================================================

**作者:** Giuseppe Cavallaro <peppe.cavallaro@st.com>,
Alexandre Torgue <alexandre.torgue@st.com>, Jose Abreu <joabreu@synopsys.com>

#### 目录
- 本版内容
- 特性列表
- 内核配置
- 命令行参数
- 驱动信息与注释
- 调试信息
- 支持

#### 本版内容
本文件描述了适用于所有 Synopsys® 以太网控制器的 stmmac Linux 驱动程序。
目前，此网络设备驱动程序适用于所有 STi 嵌入式 MAC/GMAC（即 7xxx/5xxx 系统级芯片），SPEAr (arm)，Loongson1B (mips) 和 XILINX XC2V3000 FF1152AMT0221 D1215994A VIRTEX FPGA 板卡。还支持 Synopsys 以太网 QoS 5.0 IPK。
在开发此驱动程序时使用了 DesignWare® Cores 10/100/1000 通用版本 3.70a（及更早版本）和 DesignWare® Cores 以太网服务质量版本 4.0（及更高版本），以及 DesignWare® Cores XGMAC - 10G 以太网 MAC 和 DesignWare® Cores Enterprise MAC - 100G 以太网 MAC。
此驱动程序同时支持平台总线和 PCI。
此驱动程序包括以下 Synopsys® DesignWare® Cores 以太网控制器及其对应的最小和最大版本的支持：

| 控制器名称             | 最小版本 | 最大版本 | 简称 |
|------------------------|----------|----------|------|
| 以太网 MAC 通用        | N/A      | 3.73a    | GMAC |
| 以太网服务质量         | 4.00a    | N/A      | GMAC4+ |
| XGMAC - 10G 以太网 MAC | 2.10a    | N/A      | XGMAC2+ |
| XLGMAC - 100G 以太网 MAC| 2.00a    | N/A      | XLGMAC2+ |

有关硬件需求的问题，请参阅随您的以太网适配器提供的文档。列出的所有硬件需求均适用于 Linux。

#### 特性列表
该驱动程序具有以下特性：
- GMII/MII/RGMII/SGMII/RMII/XGMII/XLGMII 接口
- 半双工/全双工操作
- 能效以太网 (EEE)
- IEEE 802.3x PAUSE 包（流控制）
- RMON/MIB 计数器
- IEEE 1588 时间戳（PTP）
- 每秒脉冲输出 (PPS)
- MDIO 第 22 条款/第 45 条款接口
- MAC 环回
- ARP 卸载
- 自动 CRC/PAD 插入和检查
- 发送和接收包的校验和卸载
- 标准或巨型以太网包
- 源地址插入/替换
- VLAN 标签插入/替换/删除/过滤（哈希和完美）
- 可编程 TX 和 RX 看门狗及合并设置
- 目标地址过滤（完美）
- 哈希过滤（多播）
- 第 3 层/第 4 层过滤
- 远程唤醒检测
- 接收侧扩展 (RSS)
- TX 和 RX 帧抢占
- 可编程突发长度、阈值、队列大小
- 多个队列（最多 8 个）
- 多种调度算法（TX: WRR, DWRR, WFQ, SP, CBS, EST, TBS; RX: WRR, SP）
- 灵活的 RX 解析器
- TCP/UDP 分段卸载 (TSO, USO)
- 分割报头 (SPH)
- 安全特性（ECC 保护、数据奇偶校验保护）
- 使用 ethtool 的自检

#### 内核配置
内核配置选项为 `CONFIG_STMMAC_ETH`：
- `CONFIG_STMMAC_PLATFORM`: 启用平台驱动
- `CONFIG_STMMAC_PCI`: 启用 PCI 驱动

#### 命令行参数
如果将驱动程序构建为模块，则可以使用以下可选参数通过 modprobe 命令命令行传递这些参数（例如对于 PCI 模块）：

```shell
modprobe stmmac_pci [<option>=<VAL1>,<VAL2>,...]
```

也可以通过命令行传递驱动程序参数：

```shell
stmmaceth=watchdog:100,chain_mode=1
```

每个参数的默认值通常是推荐的设置，除非另有说明。

- **watchdog**
  - 有效范围: 5000-无
  - 默认值: 5000

  此参数覆盖发送超时（毫秒）

- **debug**
  - 有效范围: 0-16 (0=无,...,16=全部)
  - 默认值: 0

  此参数调整系统日志中显示的调试消息级别
### 参数说明

- **phyaddr**
  - **有效范围:** 0-31
  - **默认值:** -1

  此参数覆盖了物理层设备的物理地址。

- **flow_ctrl**
  - **有效范围:** 0-3 (0=关闭,1=接收,2=发送,3=接收/发送)
  - **默认值:** 3

  此参数改变默认的流控能力。

- **pause**
  - **有效范围:** 0-65535
  - **默认值:** 65535

  此参数改变默认的流控暂停时间。

- **tc**
  - **有效范围:** 64-256
  - **默认值:** 64

  此参数改变默认的硬件FIFO阈值控制值。

- **buf_sz**
  - **有效范围:** 1536-16384
  - **默认值:** 1536

  此参数改变默认的接收DMA数据包缓冲区大小。

- **eee_timer**
  - **有效范围:** 0-无
  - **默认值:** 1000

  此参数改变默认的低功耗闲置（LPI）传输过期时间（以毫秒为单位）。

- **chain_mode**
  - **有效范围:** 0-1 (0=关闭,1=开启)
  - **默认值:** 0

  此参数改变默认的操作模式，从环形模式切换到链式模式。

### 驱动信息和注意事项

#### 发送过程

当内核需要发送一个数据包时，会调用`xmit`方法；该方法设置环中的描述符，并通知DMA引擎有数据包准备发送。
默认情况下，驱动程序会在`net_device`结构的特性字段中设置`NETIF_F_SG`位，启用散列聚集功能。这在能够进行硬件校验和处理的芯片和配置上是正确的。
一旦控制器完成数据包的发送后，将安排定时器释放发送资源。
接收过程
------------

当接收到一个或多个数据包时，会触发中断。中断不会被排队，因此驱动程序必须在接收过程中扫描环中的所有描述符。
这是基于NAPI（New API）的，所以中断处理程序仅在有工作需要完成时发出信号，并随后退出。之后，在某个将来的时间点将安排轮询方法。
传入的数据包由DMA存储在预分配的套接字缓冲区列表中，以避免使用`memcpy`（零复制）。

中断缓解
------------

对于比3.50版本更老的芯片，驱动程序能够利用NAPI来减少其DMA中断的数量。新芯片具有用于此缓解的硬件接收端看门狗（HW RX Watchdog）。
可以通过ethtool调整缓解参数。

WoL
---

通过Magic和单播帧支持局域网唤醒(LAN Wake-up)功能，适用于GMAC、GMAC4/5和XGMAC核心。

DMA描述符
------------

驱动程序同时处理正常和交替描述符。后者仅在DesignWare® Cores Ethernet MAC Universal版本3.41a及以后版本上进行了测试。
stmmac支持DMA描述符在双缓冲（RING）和链表（CHAINED）模式下运行。在RING模式下，每个描述符指向两个数据缓冲区指针；而在CHAINED模式下，它们只指向一个数据缓冲区指针。
RING模式是默认模式。
在CHAINED模式下，每个描述符都有指向列表中下一个描述符的指针，从而在描述符本身中创建显式的链式结构，而在RING模式下无法实现这样的显式链接。
### 扩展描述符

扩展描述符为我们提供了有关以太网负载的信息，当它承载PTP数据包或TCP/UDP/ICMP通过IP时。这些描述符在早于3.50版本的GMAC Synopsys®芯片上不可用。在探测过程中，驱动程序将决定这些描述符是否可以实际使用。对于PTPv2而言，这种支持是必需的，因为额外的描述符用于保存硬件时间戳和扩展状态。

### Ethtool 支持

Ethtool得到支持。例如，可以通过以下命令获取驱动程序统计信息（包括RMON）和内部错误：

```
ethtool -S ethX
```

Ethtool自我测试也得到支持。这允许使用MAC和PHY环回机制进行一些初步的合理性检查：

```
ethtool -t ethX
```

### 巨型帧和分段卸载

GMAC支持并测试了巨型帧。已经添加了GSO（分段卸载），但它是通过软件完成的。不支持LRO（大型接收卸载）。

### TSO支持

TSO（TCP分段卸载）功能由GMAC > 4.x和XGMAC芯片家族支持。当一个数据包通过TCP协议发送时，TCP堆栈确保提供给低级驱动程序（在我们的情况下为stmmac）的SKB与最大帧长度匹配（IP头 + TCP头 + 负载 ≤ 1500字节[对于MTU设置为1500]）。这意味着如果使用TCP的应用程序想要发送一个在添加头部后长度大于1514的数据包，则该数据包将被拆分为多个TCP数据包：数据负载被分割，并添加头部（TCP/IP等）。这是由软件完成的。
当启用TSO时，TCP堆栈不再关心最大帧长度，并按原样向stmmac提供SKB数据包。GMAC IP必须自行执行分段以匹配最大帧长度。
此特性可通过设备树中的`snps,tso`条目启用。

### 能效以太网

能效以太网（EEE）使IEEE 802.3 MAC子层以及一系列物理层能够运行在低功耗闲置（LPI）模式下。EEE模式支持IEEE 802.3 MAC在100Mbps、1000Mbps和1Gbps下的操作。
LPI模式通过在没有数据需要传输和接收时关闭通信设备的部分功能来节省电力。
链接两端的系统可以在链路利用率低的期间禁用某些功能并节省电力。MAC控制着系统何时进入或退出LPI模式，并将这些信息传达给PHY。
一旦接口打开，驱动程序会验证EEE是否可以得到支持。这是通过查看DMA硬件能力寄存器和PHY设备的MCD寄存器来完成的。
为了进入TX LPI模式，驱动程序需要有一个软件定时器，在没有任何数据需要传输时启用和禁用LPI模式。
这段文档描述了一个网络驱动（特别是针对STMicroelectronics的GMAC控制器）的相关配置和特性，下面是对这段内容的中文翻译。

---

### 精确时间协议 (PTP)

该驱动支持IEEE 1588-2002精确时间协议(PTP)，它使测量和控制系统中的时钟能够实现精确同步，这些系统采用诸如网络通信等技术实现。除了IEEE 1588-2002中提到的基本时间戳功能外，新的GMAC核心还支持IEEE 1588-2008中的高级时间戳功能。当配置内核时可以启用这些功能。

### SGMII/RGMII 支持

新的GMAC设备提供了自己的方式来管理RGMII/SGMII。这些信息可以通过查看硬件能力寄存器在运行时获得。这意味着stmmac可以在不使用PHYLIB的情况下管理自动协商和链路状态。事实上，硬件提供了一组扩展寄存器子集来重启ANE、验证全双工/半双工模式和速度。借助这些寄存器，可以查看自动协商的链路伙伴能力物理层。

### 物理层

该驱动与物理抽象层兼容，可用于连接PHY和GPHY设备。

### 平台信息

可以通过平台和设备树传递多种信息：

1. 总线标识符：
   ```c
   int bus_id;
   ```

2. PHY物理地址。如果设置为-1，驱动将选择找到的第一个PHY：
   ```c
   int phy_addr;
   ```

3. PHY设备接口：
   ```c
   int interface;
   ```

4. 用于MDIO总线的具体平台字段：
   ```c
   struct stmmac_mdio_bus_data *mdio_bus_data;
   ```

5. 内部DMA参数：
   ```c
   struct stmmac_dma_cfg *dma_cfg;
   ```

6. 固定CSR时钟范围选择：
   ```c
   int clk_csr;
   ```

7. 硬件使用GMAC核心：
   ```c
   int has_gmac;
   ```

8. 如果设置，则MAC将使用增强型描述符：
   ```c
   int enh_desc;
   ```

9. 核心能够在硬件中执行TX校验和和/或RX校验和：
   ```c
   int tx_coe;
   int rx_coe;
   ```

11. 由于有限的缓冲区大小，一些硬件无法在硬件中为超大帧进行校验和计算。设置此标志后，对于JUMBO帧将在软件中完成校验和：
   ```c
   int bugged_jumbo;
   ```

12. 核心具有嵌入式电源模块：
   ```c
   int pmt;
   ```

13. 强制DMA使用存储转发模式或阈值模式：
   ```c
   int force_sf_dma_mode;
   int force_thresh_dma_mode;
   ```

15. 强制禁用RX Watchdog功能并切换到NAPI模式：
   ```c
   int riwt_off;
   ```

16. 限制最大工作速度和MTU：
   ```c
   int max_speed;
   int maxmtu;
   ```

18. 多播/单播过滤器的数量：
   ```c
   int multicast_filter_bins;
   int unicast_filter_entries;
   ```

20. 限制最大TX和RX FIFO大小：
   ```c
   int tx_fifo_size;
   int rx_fifo_size;
   ```

21. 使用指定数量的TX和RX队列：
   ```c
   u32 rx_queues_to_use;
   u32 tx_queues_to_use;
   ```

22. 使用指定的TX和RX调度算法：
   ```c
   u8 rx_sched_algorithm;
   u8 tx_sched_algorithm;
   ```

23. 内部TX和RX队列参数：
   ```c
   struct stmmac_rxq_cfg rx_queues_cfg[MTL_MAX_RX_QUEUES];
   struct stmmac_txq_cfg tx_queues_cfg[MTL_MAX_TX_QUEUES];
   ```

24. 此回调用于根据物理层协商的链接速度修改某些syscfg寄存器（在ST SoC上）：
   ```c
   void (*fix_mac_speed)(void *priv, unsigned int speed);
   ```

25. 用于调用自定义初始化的回调；这在某些平台上有时是必要的（例如ST盒子），其中硬件需要设置一些PIO线或系统配置寄存器。初始化/退出回调不应使用或修改平台数据：
   ```c
   int (*init)(struct platform_device *pdev, void *priv);
   void (*exit)(struct platform_device *pdev, void *priv);
   ```

26. 执行总线的硬件设置。例如，在某些ST平台上，此字段用于配置AMBA桥以生成更高效的STBus流量：
   ```c
   struct mac_device_info *(*setup)(void *priv);
   void *bsp_priv;
   ```

27. 内部时钟和速率：
   ```c
   struct clk *stmmac_clk;
   struct clk *pclk;
   struct clk *clk_ptp_ref;
   unsigned int clk_ptp_rate;
   unsigned int clk_ref_rate;
   s32 ptp_max_adj;
   ```

28. 主重置：
   ```c
   struct reset_control *stmmac_rst;
   ```

29. AXI内部参数：
   ```c
   struct stmmac_axi *axi;
   ```

30. 硬件使用GMAC>4核心：
   ```c
   int has_gmac4;
   ```

31. 硬件基于sun8i：
   ```c
   bool has_sun8i;
   ```

32. 启用TSO特性：
   ```c
   bool tso_en;
   ```

33. 启用接收侧扩展(RSS)特性：
   ```c
   int rss_en;
   ```

34. MAC端口选择：
   ```c
   int mac_port_sel_speed;
   ```

35. 启用TX LPI时钟门控：
   ```c
   bool en_tx_lpi_clockgating;
   ```

36. 硬件使用XGMAC>2.10核心：
   ```c
   int has_xgmac;
   ```

对于MDIO总线数据，我们有：

```c
struct stmmac_mdio_bus_data {
    // PHY掩码在注册MDIO总线时传递
    unsigned int phy_mask;

    // 每个PHY的IRQ列表
    int *irqs;

    // 如果irqs为NULL，则使用此值为探测到的PHY
    int probed_phy_irq;

    // 如果PHY需要重置，设置为true
    bool needs_reset;
};
```

对于DMA引擎配置，我们有：

```c
struct stmmac_dma_cfg {
    // 可编程突发长度(TX和RX)
    int pbl;

    // 如果设置，DMA TX / RX将使用此值而不是pbl
    int txpbl;
    int rxpbl;

    // 启用8倍PBL
    bool pblx8;

    // 启用固定或混合突发
    int fixed_burst;
    int mixed_burst;

    // 启用地址对齐拍节
    bool aal;

    // 启用增强地址映射(> 32位)
    bool eame;
};
```

对于DMA AXI参数，我们有：

```c
struct stmmac_axi {
    // 启用AXI LPI
    bool axi_lpi_en;
    bool axi_xit_frm;

    // 设置AXI写/读最大未决请求
    u32 axi_wr_osr_lmt;
    u32 axi_rd_osr_lmt;

    // 设置AXI 4KB突发
    bool axi_kbbe;

    // 设置AXI最大突发长度映射
    u32 axi_blen[AXI_BLEN];

    // 设置AXI固定突发/混合突发
    bool axi_fb;
    bool axi_mb;

    // 设置AXI重建incrx模式
    bool axi_rb;
};
```

对于RX队列配置，我们有：

```c
struct stmmac_rxq_cfg {
    // 要使用的模式(DCB或AVB)
    u8 mode_to_use;

    // 要使用的DMA通道
    u32 chan;

    // 包路由，如果适用
    u8 pkt_route;

    // 使用优先级路由，并设置优先级
    bool use_prio;
    u32 prio;
};
```

对于TX队列配置，我们有：

```c
struct stmmac_txq_cfg {
    // 在调度程序中的队列权重
    u32 weight;

    // 要使用的模式(DCB或AVB)
    u8 mode_to_use;

    // 信用基础整形参数
    u32 send_slope;
    u32 idle_slope;
    u32 high_credit;
    u32 low_credit;

    // 使用优先级调度，并设置优先级
    bool use_prio;
    u32 prio;
};
```

### 设备树信息

请参阅以下文档：Documentation/devicetree/bindings/net/snps,dwmac.yaml

### 硬件能力

请注意，从新芯片开始，通过可用的硬件能力寄存器，许多配置都可以在运行时发现，例如了解EEE、硬件校验和、PTP、增强型描述符等是否实际可用。作为该驱动采用的策略，来自硬件能力寄存器的信息可以替代平台传递的信息。

### 调试信息

该驱动导出了许多信息，如内部统计、调试信息、MAC和DMA寄存器等。
这些信息可以根据所需信息的类型以多种方式读取。
例如，用户可以使用ethtool支持获取统计信息：
使用 `ethtool -S ethX`（如果受支持，这会显示管理计数器（MMC））或查看 MAC/DMA 寄存器：例如，使用 `ethtool -d ethX`。

如果使用 `CONFIG_DEBUG_FS` 编译内核，驱动程序将导出以下 debugfs 条目：

- `descriptors_status`：用于显示 DMA TX/RX 描述符环
- `dma_cap`：用于显示硬件功能

开发人员还可以使用 `debug` 模块参数来获取更多的调试信息（请参阅：NETIF 消息级别）
支持
=====

如果在受支持的内核上使用发布的源代码和受支持的适配器时发现有问题，请将与问题相关的确切信息发送到 netdev@vger.kernel.org。
