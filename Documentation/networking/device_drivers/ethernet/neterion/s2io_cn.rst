.. SPDX 许可证标识符: GPL-2.0

=========================================================
Neterion（原S2io）的Xframe I/II PCI-X 10GbE驱动程序
=========================================================

Neterion（原S2io）的Xframe I/II PCI-X 10GbE驱动程序的发布说明
.. 目录
  - 1. 引言
  - 2. 识别适配器/接口
  - 3. 支持的功能
  - 4. 命令行参数
  - 5. 性能建议
  - 6. 可用下载

1. 引言
===============
此Linux驱动程序支持Neterion的Xframe I PCI-X 1.0和Xframe II PCI-X 2.0适配器。它支持多种功能，例如巨型帧、MSI/MSI-X、校验和卸载、TSO、UFO等。
详见以下完整功能列表。
所有功能都支持IPv4和IPv6。

2. 识别适配器/接口
====================================

a. 将适配器插入系统中。
b. 构建并加载驱动程序::

	# insmod s2io.ko

c. 查看日志消息::

	# dmesg | tail -40

您将看到类似以下的消息::

	eth3: Neterion Xframe I 10GbE 适配器 (rev 3)，版本 2.0.9.1，中断类型 INTA
	eth4: Neterion Xframe II 10GbE 适配器 (rev 2)，版本 2.0.9.1，中断类型 INTA
	eth4: 设备位于 64 位 133MHz PCIX(M1) 总线上

以上消息会显示适配器类型（Xframe I/II）、适配器修订版、驱动程序版本、接口名称（eth3, eth4）、中断类型（INTA, MSI, MSI-X）。
在Xframe II的情况下，还会显示PCI/PCI-X总线宽度和频率。
要将接口与物理适配器关联，请使用“ethtool -p <ethX>”命令。
相应的适配器LED将闪烁多次。

3. 支持的功能
=====================

a. 巨型帧。Xframe I/II 支持最大传输单元（MTU）高达 9600 字节，
   可以使用 ip 命令进行修改。
b. 卸载。支持在发送和接收时的校验和卸载（TCP/UDP/IP），以及TSO。
c. 多缓冲区接收模式。将数据包分散到多个缓冲区中。目前驱动程序支持2缓冲区模式，在某些平台（如SGI Altix、IBM xSeries）上可显著提高性能。
d. MSI/MSI-X。可以在支持此特性的平台上启用，从而带来明显的性能提升（在某些平台上最高可达7%）。
e. 统计信息。使用“ethtool -S”选项显示全面的MAC层和软件统计信息。
f. 多FIFO/环。支持最多8个发送队列和接收环，并具有多种转向选项。

4. 命令行参数
===============
a. tx_fifo_num  
发送队列的数量。

有效范围：1-8

默认值：1

b. rx_ring_num  
接收环的数量。

有效范围：1-8

默认值：1

c. tx_fifo_len  
每个发送队列的大小。

有效范围：所有队列的总长度不应超过8192

默认值：4096

d. rx_ring_sz  
每个接收环的大小（以4K块为单位）。

有效范围：受系统内存限制

默认值：30

e. intr_type  
指定中断类型。可能的值为0（INTA）、2（MSI-X）。

有效值：0, 2

默认值：2

5. 性能建议
==========================
一般建议：
a. 将MTU设置为最大值（交换机设置为9000，背对背配置为9600）。
b. 将TCP窗口大小设置为最优值。
例如，对于MTU=1500，观察到210K的值可以带来良好的性能：

```
# sysctl -w net.ipv4.tcp_rmem="210000 210000 210000"
# sysctl -w net.ipv4.tcp_wmem="210000 210000 210000"
```

对于MTU=9000，建议TCP窗口大小为10MB：

```
# sysctl -w net.ipv4.tcp_rmem="10000000 10000000 10000000"
# sysctl -w net.ipv4.tcp_wmem="10000000 10000000 10000000"
```

发送性能：
a. 默认情况下，驱动程序遵循BIOS设置中的PCI总线参数。然而，您可以尝试调整PCI总线参数max-split-transactions（MOST）和MMRBC（使用setpci命令）。
对于Opterons，MOST值为2是最优的；对于Itanium，MOST值为3是最优的。对于您的硬件，最优值可能会有所不同。
**将MMRBC设置为4K**
例如，您可以设置

   对于Opteron:: 

	```
	#setpci -d 17d5:* 62=1d
	```

   对于Itanium:: 

	```
	#setpci -d 17d5:* 62=3d
	```

   有关PCI寄存器的详细描述，请参阅Xframe用户指南。

b. 确保启用了传输校验和卸载。使用ethtool来设置/验证此参数。
c. 启用TSO（使用“ethtool -K”）:: 

	```
	# ethtool -K <ethX> tso on
	```

接收性能：

a. 默认情况下，驱动程序会遵循BIOS设置中的PCI总线参数。但是，您可能需要将PCI延迟计时器设置为248:: 

	```
	#setpci -d 17d5:* LATENCY_TIMER=f8
	```

   有关PCI寄存器的详细描述，请参阅Xframe用户指南。
b. 使用2缓冲模式。这在某些平台上（例如SGI Altix、IBM xSeries）可以显著提高性能。
c. 确保启用了接收校验和卸载。使用“ethtool -K ethX”命令来设置/验证此选项。
d. 启用NAPI特性（在内核配置中：设备驱动程序 ---> 网络设备支持 ---> 以太网（10000 Mbit）---> S2IO 10Gbe Xframe NIC），以降低CPU利用率。
.. note:: 

   对于具有8131芯片组的AMD Opteron平台，推荐将MMRBC=1和MOST=1作为安全参数。
更多详细信息，请参阅AMD8131的勘误表：
http://vip.amd.com/us-en/assets/content_type/white_papers_and_tech_docs/26310_AMD-8131_HyperTransport_PCI-X_Tunnel_Revision_Guide_rev_3_18.pdf

### 支持
对于进一步的支持，请联系您的10GbE Xframe NIC供应商（如IBM、HP、SGI等）。
