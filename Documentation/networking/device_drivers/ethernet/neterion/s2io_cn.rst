### SPDX 许可证标识符: GPL-2.0

=========================================================
Neterion 的（原 S2io）Xframe I/II PCI-X 10GbE 驱动程序
=========================================================

Neterion 的（原 S2io）Xframe I/II PCI-X 10GbE 驱动程序的发行说明
.. 目录
  - 1. 引言
  - 2. 识别适配器/接口
  - 3. 支持的功能
  - 4. 命令行参数
  - 5. 性能建议
  - 6. 可用下载

1. 引言
===============
此 Linux 驱动程序支持 Neterion 的 Xframe I PCI-X 1.0 和 Xframe II PCI-X 2.0 适配器。它支持多种功能，例如巨型帧、MSI/MSI-X、校验和卸载、TSO、UFO 等等。请参阅下面列出的所有功能。
所有这些功能都同时支持 IPv4 和 IPv6。
2. 识别适配器/接口
====================================

a. 将适配器安装到您的系统中
b. 构建并加载驱动程序：

	# insmod s2io.ko

c. 查看日志消息：

	# dmesg | tail -40

您会看到类似以下的消息：

	eth3: Neterion Xframe I 10GbE 适配器 (版本 3)，版本 2.0.9.1，中断类型 INTA
	eth4: Neterion Xframe II 10GbE 适配器 (版本 2)，版本 2.0.9.1，中断类型 INTA
	eth4: 设备位于 64 位 133MHz PCIX(M1) 总线上

上述消息可以识别出适配器类型（Xframe I/II）、适配器修订版、驱动程序版本、接口名称（eth3, eth4）、中断类型（INTA, MSI, MSI-X）
在 Xframe II 的情况下，还会显示 PCI/PCI-X 总线宽度和频率。
要将接口与物理适配器关联，请使用 "ethtool -p <ethX>"。
相应的适配器 LED 将闪烁多次。
3. 支持的功能
=====================
a. 巨型帧。Xframe I/II 支持最大传输单元（MTU）最高可达 9600 字节，
   可通过 ip 命令进行修改
### b. 卸载功能。支持在发送和接收时的校验和卸载（TCP/UDP/IP），以及传输分段卸载（TSO）
c. 多缓冲接收模式。将数据包分散到多个缓冲区中。目前驱动支持2缓冲模式，在某些平台（如SGI Altix、IBM xSeries）上可显著提升性能。
d. MSI/MSI-X。可以在支持该特性的平台上启用，从而带来明显的性能提升（在某些平台上最高可达7%）。
e. 统计信息。使用“ethtool -S”选项显示全面的MAC层及软件统计信息。
f. 多FIFO/环形队列。支持多达8个发送队列和接收环，具有多种导向选项。

### 4. 命令行参数

a. `tx_fifo_num`
- 发送队列的数量

有效范围：1-8

默认值：1

b. `rx_ring_num`
- 接收环的数量

有效范围：1-8

默认值：1

c. `tx_fifo_len`
- 每个发送队列的大小

有效范围：所有队列总长度不应超过8192

默认值：4096

d. `rx_ring_sz`
- 每个接收环的大小（以4K块为单位）

有效范围：受系统内存限制

默认值：30

e. `intr_type`
- 指定中断类型。可能的值为0（INTA）、2（MSI-X）

有效值：0, 2

默认值：2

### 5. 性能建议

#### 通用：

a. 将MTU设置为最大值（对于交换机设置为9000，对于背对背配置为9600）。
b. 将TCP窗口大小设置为最优值。例如，对于MTU=1500的情况，观察到210K的结果会带来良好的性能：
```shell
# sysctl -w net.ipv4.tcp_rmem="210000 210000 210000"
# sysctl -w net.ipv4.tcp_wmem="210000 210000 210000"
```
对于MTU=9000，推荐的TCP窗口大小为10MB：
```shell
# sysctl -w net.ipv4.tcp_rmem="10000000 10000000 10000000"
# sysctl -w net.ipv4.tcp_wmem="10000000 10000000 10000000"
```

#### 发送性能：

a. 默认情况下，驱动程序遵守BIOS设置中的PCI总线参数。然而，您可能需要尝试调整PCI总线参数，比如最大分割事务（MOST）和MMRBC（使用`setpci`命令）。对于Opteron处理器，MOST值为2被发现是最优的；而对于Itanium处理器，MOST值为3是最优的。这些值可能会因您的硬件而异。
设置 MMRBC 为 4K**
例如，您可以设置

   对于 Opteron:: 

	#setpci -d 17d5:* 62=1d

   对于 Itanium::

	#setpci -d 17d5:* 62=3d

   关于 PCI 寄存器的详细描述，请参阅 Xframe 用户指南。
b. 确保启用了传输校验和卸载。使用 ethtool 设置/验证此参数
c. 打开 TSO（使用 "ethtool -K"）::

	# ethtool -K <ethX> tso on

接收性能：

a. 默认情况下，驱动程序遵循 BIOS 设置的 PCI 总线参数。
但是，您可能需要将 PCI 延迟计时器设置为 248::

	#setpci -d 17d5:* LATENCY_TIMER=f8

   关于 PCI 寄存器的详细描述，请参阅 Xframe 用户指南。
b. 使用 2 缓冲模式。这在某些平台上（如 SGI Altix、IBM xSeries）可以显著提高性能。
c. 确保启用了接收校验和卸载。使用 "ethtool -K ethX" 命令来设置/验证此选项。
d. 启用 NAPI 特性（在内核配置中，设备驱动程序 ---> 网络设备支持 ---> 以太网（10000 Mbit）---> S2IO 10Gbe Xframe 网卡），以降低 CPU 利用率。
.. 注意::

   对于采用 8131 芯片组的 AMD Opteron 平台，推荐将 MMRBC=1 和 MOST=1 作为安全参数。
更多信息，请参阅 AMD8131 错误列表：
http://vip.amd.com/us-en/assets/content_type/white_papers_and_tech_docs/
26310_AMD-8131_HyperTransport_PCI-X_Tunnel_Revision_Guide_rev_3_18.pdf

6. 支持
==========

如需进一步的支持，请联系您的 10GbE Xframe 网卡供应商（如 IBM、HP、SGI 等）。
