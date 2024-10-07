SPDX 许可证标识符: GPL-2.0

.. include:: <isonum.txt>

=======================================
Altera 三速以太网 MAC 驱动程序
=======================================

版权所有 © 2008-2014 Altera Corporation

这是用于 Altera 三速以太网（TSE）控制器的驱动程序，该控制器使用 SGDMA 和 MSGDMA 软件 DMA IP 组件。该驱动程序使用平台总线来获取组件资源。用于测试此驱动程序的设计是在 Cyclone® V SOC FPGA 板和 Cyclone® V FPGA 板上构建的，并分别在 ARM 和 NIOS 处理器主机上进行了测试。预期的应用场景是嵌入式系统与外部对等设备之间的简单通信，以便进行状态查询和嵌入式系统的简单配置。欲了解更多信息，请访问 www.altera.com 和 www.rocketboards.org。可以在 www.rocketboards.org 上找到驱动程序的支持论坛，并且还可以在那里找到用于测试此驱动程序的设计。此外，也可以从驱动程序维护者那里获得支持，维护者信息可以在 MAINTAINERS 文件中找到。

三速以太网、SGDMA 和 MSGDMA 组件都是软 IP 组件，可以使用 Altera 的 Quartus 工具链进行组装并集成到 FPGA 中。使用 Quartus 13.1 和 14.0 构建了此驱动程序所针对的设计。sopc2dts 工具用于为驱动程序创建设备树，并可在 rocketboards.org 上找到。

驱动程序的探测函数会检查设备树，并确定三速以太网实例是否使用了 SGDMA 或 MSGDMA 组件。然后，探测函数将安装适当的 DMA 例程集，用于初始化、设置传输、接收以及相应配置中的中断处理原语。

预计 SGDMA 组件将在不久的将来（截至2014年初的1-2年内）被 MSGDMA 组件取代。SGDMA 支持仅包含在现有设计和参考中，以防开发人员希望支持自己的软件 DMA 逻辑和驱动程序支持。任何新设计都不应使用 SGDMA。

SGDMA 每次只能支持单个传输或接收操作，因此其性能不如 MSGDMA 软件 IP。请访问 www.altera.com 获取已知的 SGDMA 错误文档。

目前 SGDMA 和 MSGDMA 均不支持分散/聚集 DMA。
分散/聚集 DMA 将会在未来的维护更新中添加到此驱动程序中。

目前不支持巨型帧。
驱动程序限制了 PHY 操作在 10/100 Mbps，并且尚未完全针对 1Gbps 进行测试。此支持将在未来的维护更新中添加。

1. 内核配置
=============

内核配置选项是 ALTERA_TSE：

设备驱动程序 ---> 网络设备支持 ---> 以太网驱动程序支持 ---> Altera 三速以太网 MAC 支持 (ALTERA_TSE)

2. 驱动参数列表
==================

- debug: 消息级别（0：无输出，16：全部）；
- dma_rx_num: RX 列表中的描述符数量（默认为 64）；
- dma_tx_num: TX 列表中的描述符数量（默认为 64）

3. 命令行选项
==================

驱动程序参数也可以通过命令行传递，例如：

```
altera_tse=dma_rx_num:128,dma_tx_num:512
```

4. 驱动信息和说明
==================

4.1. 发送过程
---------------------
当内核调用驱动程序的发送例程时，它会通过调用底层的 DMA 发送例程（SGDMA 或 MSGDMA）来设置一个发送描述符，并启动发送操作。一旦发送完成，发送 DMA 逻辑将触发中断。驱动程序在中断处理链的上下文中处理发送完成，回收发送所需资源并跟踪请求的发送操作。

4.2. 接收过程
--------------------
驱动程序会在初始化期间向接收 DMA 逻辑提交接收缓冲区。根据底层 DMA 逻辑（MSGDMA 能够排队接收缓冲区，而 SGDMA 不能排队），接收缓冲区可能会或可能不会被排队。当接收到数据包时，DMA 逻辑将生成中断。驱动程序通过获取 DMA 接收逻辑的状态来处理接收中断，并收集所有可用的接收完成情况。

4.3. 中断缓解
-------------------------
驱动程序能够使用 NAPI 来减少其 DMA 接收操作的中断次数。发送操作的中断缓解目前尚未支持，但将在未来的维护版本中添加。

4.4. Ethtool 支持
--------------------
Ethtool 是支持的。可以通过以下命令获取驱动统计信息和内部错误：
```
ethtool -S ethX
```
还可以转储寄存器等信息，例如：
```
ethtool -d ethX
```

4.5. PHY 支持
----------------
该驱动程序与 PAL 兼容，可以与 PHY 和 GPHY 设备一起工作。

4.7. 源文件列表
--------------------------
- Kconfig
- Makefile
- altera_tse_main.c: 主网络设备驱动程序
- altera_tse_ethtool.c: Ethtool 支持
- altera_tse.h: 私有驱动结构和通用定义
- altera_msgdma.h: MSGDMA 实现函数定义
- altera_sgdma.h: SGDMA 实现函数定义
- altera_msgdma.c: MSGDMA 实现
- altera_sgdma.c: SGDMA 实现
- altera_sgdmahw.h: SGDMA 寄存器和描述符定义
- altera_msgdmahw.h: MSGDMA 寄存器和描述符定义
- altera_utils.c: 驱动程序工具函数
- altera_utils.h: 驱动程序工具函数定义

5. 调试信息
==================

驱动程序导出了调试信息，如内部统计、调试信息、MAC 和 DMA 寄存器等。
用户可以使用 Ethtool 支持来获取统计信息，例如：
```
ethtool -S ethX （显示统计计数器）
```
或者查看 MAC 寄存器，例如：
```
ethtool -d ethX
```

开发者也可以使用“debug”模块参数来获取更多调试信息。

6. 统计支持
==================

控制器和驱动程序支持混合标准定义的统计信息，包括 IEEE 标准定义的统计信息、RFC 定义的统计信息以及驱动程序或 Altera 定义的统计信息。这些统计信息的标准定义包含在以下四个规范中：

- IEEE 802.3-2012 - IEEE 以太网标准
以下是在指定链接中找到的相关RFC文档和Altera Triple Speed Ethernet (TSE) 用户指南：

- RFC 2863 可在 http://www.rfc-editor.org/rfc/rfc2863.txt 找到
- RFC 2819 可在 http://www.rfc-editor.org/rfc/rfc2819.txt 找到
- Altera Triple Speed Ethernet 用户指南可在 http://www.altera.com 找到

TSE 和设备驱动程序支持的统计信息如下：

- "tx_packets" 等同于 IEEE 802.3-2012 第 5.2.2.1.2 节定义的 aFramesTransmittedOK。这个统计值表示成功传输的数据帧数量。
- "rx_packets" 等同于 IEEE 802.3-2012 第 5.2.2.1.5 节定义的 aFramesReceivedOK。这个统计值表示成功接收的数据帧数量。此计数不包括任何错误数据包，如 CRC 错误、长度错误或对齐错误。
- "rx_crc_errors" 等同于 IEEE 802.3-2012 第 5.2.2.1.6 节定义的 aFrameCheckSequenceErrors。这个统计值表示长度为整数倍字节但未通过 CRC 检验的数据帧数量。
- "rx_align_errors" 等同于 IEEE 802.3-2012 第 5.2.2.1.7 节定义的 aAlignmentErrors。这个统计值表示长度不是整数倍字节且未通过 CRC 检验的数据帧数量。
- "tx_bytes" 等同于 IEEE 802.3-2012 第 5.2.2.1.8 节定义的 aOctetsTransmittedOK。这个统计值表示从接口成功传输的数据和填充字节数量。
- "rx_bytes" 等同于 IEEE 802.3-2012 第 5.2.2.1.14 节定义的 aOctetsReceivedOK。这个统计值表示控制器成功接收的数据和填充字节数量。
- "tx_pause" 等同于 IEEE 802.3-2012 第 30.3.4.2 节定义的 aPAUSEMACCtrlFramesTransmitted。这个统计值表示网络控制器发送的 PAUSE 帧数量。
- "rx_pause" 等同于 IEEE 802.3-2012 第 30.3.4.3 节定义的 aPAUSEMACCtrlFramesReceived。这个统计值表示网络控制器接收到的 PAUSE 帧数量。
"rx_errors" 等同于 RFC 2863 中定义的 ifInErrors。这个统计值表示接收到的包含错误的包的数量，这些错误阻止了包被传递到更高层协议。

"tx_errors" 等同于 RFC 2863 中定义的 ifOutErrors。这个统计值表示由于错误而无法传输的包的数量。

"rx_unicast" 等同于 RFC 2863 中定义的 ifInUcastPkts。这个统计值表示接收到的未发送到广播地址或组播组的包的数量。

"rx_multicast" 等同于 RFC 2863 中定义的 ifInMulticastPkts。这个统计值表示接收到的发送到组播地址组的包的数量。

"rx_broadcast" 等同于 RFC 2863 中定义的 ifInBroadcastPkts。这个统计值表示接收到的发送到广播地址的包的数量。

"tx_discards" 等同于 RFC 2863 中定义的 ifOutDiscards。这个统计值表示即使没有检测到错误也未传输的出站包的数量。这种情况的一个例子是为了释放内部缓冲区空间。

"tx_unicast" 等同于 RFC 2863 中定义的 ifOutUcastPkts。这个统计值表示发送的未发送到组播组或广播地址的包的数量。

"tx_multicast" 等同于 RFC 2863 中定义的 ifOutMulticastPkts。这个统计值表示发送的发送到组播组的包的数量。

"tx_broadcast" 等同于 RFC 2863 中定义的 ifOutBroadcastPkts。这个统计值表示发送的发送到广播地址的包的数量。

"ether_drops" 等同于 RFC 2819 中定义的 etherStatsDropEvents。
这一统计数据记录了由于内部控制器资源不足而丢弃的数据包数量。

"rx_total_bytes" 等同于 RFC 2819 中定义的 etherStatsOctets。
这一统计数据记录了控制器接收到的总字节数，包括错误和被丢弃的数据包。

"rx_total_packets" 等同于 RFC 2819 中定义的 etherStatsPkts。
这一统计数据记录了控制器接收到的总数据包数，包括错误、被丢弃的、单播、组播和广播数据包。

"rx_undersize" 等同于 RFC 2819 中定义的 etherStatsUndersizePkts。
这一统计数据记录了接收到的小于 64 字节的正确格式数据包的数量。

"rx_oversize" 等同于 RFC 2819 中定义的 etherStatsOversizePkts。
这一统计数据记录了接收到的大于 1518 字节的正确格式数据包的数量。

"rx_64_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts64Octets。
此统计数据计算接收到的长度为 64 字节的数据包总数。

"rx_65_127_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts65to127Octets。此统计数据计算接收到的长度在 65 到 127 字节（包括两端）之间的数据包总数。

"rx_128_255_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts128to255Octets。此统计数据是接收到的长度在 128 到 255 字节（包括两端）之间的数据包总数。

"rx_256_511_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts256to511Octets。此统计数据是接收到的长度在 256 到 511 字节（包括两端）之间的数据包总数。

"rx_512_1023_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts512to1023Octets。此统计数据是接收到的长度在 512 到 1023 字节（包括两端）之间的数据包总数。

"rx_1024_1518_bytes" 等同于 RFC 2819 中定义的 etherStatsPkts1024to1518Octets。此统计数据是接收到的长度在 1024 到 1518 字节（包括两端）之间的数据包总数。

"rx_gte_1519_bytes" 是针对 Altera TSE 行为特别定义的统计数据。此统计数据计算接收到的有效帧和错误帧的数量，这些帧的长度在 1519 字节到 frm_length 寄存器中配置的最大帧长度之间。详见 Altera TSE 用户指南以获取更多详细信息。

"rx_jabbers" 等同于 RFC 2819 中定义的 etherStatsJabbers。此统计数据是接收到的长度超过 1518 字节，并且具有整数字节数的坏 CRC（CRC 错误）或非整数字节数的坏 CRC（对齐错误）的数据包总数。

"rx_runts" 等同于 RFC 2819 中定义的 etherStatsFragments。此统计数据是接收到的长度小于 64 字节，并且具有整数字节数的坏 CRC（CRC 错误）或非整数字节数的坏 CRC（对齐错误）的数据包总数。
