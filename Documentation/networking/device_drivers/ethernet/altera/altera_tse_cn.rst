SPDX 许可标识符: GPL-2.0

.. include:: <isonum.txt>

=======================================
Altera 三速以太网 MAC 驱动程序
=======================================

版权所有 © 2008-2014 Altera 公司

这是针对使用 SGDMA 和 MSGDMA 软件 DMA IP 组件的 Altera 三速以太网 (TSE) 控制器的驱动程序。该驱动程序通过平台总线来获取组件资源。用于测试此驱动程序的设计是在 Cyclone® V SOC FPGA 板卡、Cyclone® V FPGA 板卡上构建，并分别在 ARM 和 NIOS 处理器主机上进行了测试。预期的应用场景是嵌入式系统与外部对等设备之间进行简单的通信，用于状态报告和嵌入式系统的简单配置。更多信息请访问 www.altera.com 和 www.rocketboards.org。驱动程序的支持论坛可以在 www.rocketboards.org 上找到，同时也可以在那里找到用于测试此驱动程序的设计。此外，还可以从该驱动程序的维护者处获得支持，维护者信息可以在 MAINTAINERS 文件中找到。
三速以太网、SGDMA 和 MSGDMA 组件都是可以使用 Altera 的 Quartus 工具链组装并集成到 FPGA 中的软件 IP 组件。使用 Quartus 13.1 和 14.0 构建了用于测试此驱动程序的设计。sopc2dts 工具用于创建驱动程序的设备树，可以在 rocketboards.org 找到该工具。
驱动程序的探测函数会检查设备树，并确定三速以太网实例是否使用了 SGDMA 或 MSGDMA 组件。然后，探测函数将安装适当的 DMA 常规程序集，以初始化、设置发送、接收以及为相应的配置处理中断。
SGDMA 组件预计在未来不久（截至2014年初的1-2年内）将被 MSGDMA 组件取代。
SGDMA 支持仅是为了现有设计和参考目的，以防开发者希望支持自己的软件 DMA 逻辑和驱动程序支持。任何新设计都不应再使用 SGDMA。
SGDMA 每次只能支持单个发送或接收操作，因此相比 MSGDMA 软件 IP 的性能较差。请访问 www.altera.com 查看已知的 SGDMA 错误记录。
目前 SGDMA 和 MSGDMA 不支持分散/聚合 DMA。
分散/聚合 DMA 将会在未来对该驱动程序的维护更新中添加。
目前不支持巨型帧。
该驱动将物理层（PHY）的操作限制在10/100Mbps，并且尚未完全针对1Gbps进行测试。对于1Gbps的支持将在未来的维护更新中添加。

1. 内核配置
===========
内核配置选项为`ALTERA_TSE`：

 设备驱动程序 ---> 网络设备支持 ---> 以太网驱动程序支持 --->
 Altera 三速以太网MAC支持 (`ALTERA_TSE`)

2. 驱动参数列表
==============
   - `debug`: 消息级别（0：无输出，16：全部）；
   - `dma_rx_num`: 接收队列中的描述符数量（默认值为64）；
   - `dma_tx_num`: 发送队列中的描述符数量（默认值为64）

3. 命令行选项
=============
驱动参数也可以通过命令行传递，使用如下格式：

    `altera_tse=dma_rx_num:128,dma_tx_num:512`

4. 驾驶器信息和注释
==================

4.1. 发送过程
--------------
当内核调用驱动的发送例程时，它通过调用底层的DMA发送例程（SGDMA或MSGDMA）来设置一个发送描述符，并发起一个发送操作。一旦发送完成，发送DMA逻辑会触发中断。驱动程序在中断处理链上下文中处理发送完成事件，回收发送请求所需的资源。
4.2. 接收过程
--------------
在驱动初始化期间，驱动程序会向接收DMA逻辑提交接收缓冲区。根据底层DMA逻辑的不同，这些接收缓冲区可能被排队也可能不被排队（MSGDMA能够排队接收缓冲区，而SGDMA不能）。当接收到数据包时，DMA逻辑会生成中断。驱动程序通过获取DMA接收逻辑的状态来处理接收中断，并收集所有可用的接收完成事件。
4.3. 中断缓解
---------------
驱动程序能够通过NAPI来减少其DMA中断的数量，这仅限于接收操作。对于发送操作的中断缓解尚未支持，但会在未来的维护版本中添加。
4.4. Ethtool支持
-----------------
Ethtool得到支持。可以使用`ethtool -S ethX`命令获取驱动统计信息和内部错误等。此外还可以导出寄存器等信息。
4.5. PHY支持
-------------
该驱动与PHY和GPHY设备兼容，可以通过PHY抽象层（PAL）工作。
4.7. 源文件列表
----------------
 - `Kconfig`
 - `Makefile`
 - `altera_tse_main.c`: 主网络设备驱动程序
 - `altera_tse_ethtool.c`: Ethtool支持
 - `altera_tse.h`: 私有驱动结构和通用定义
 - `altera_msgdma.h`: MSGDMA实现函数定义
 - `altera_sgdma.h`: SGDMA实现函数定义
 - `altera_msgdma.c`: MSGDMA实现
 - `altera_sgdma.c`: SGDMA实现
 - `altera_sgdmahw.h`: SGDMA寄存器和描述符定义
 - `altera_msgdmahw.h`: MSGDMA寄存器和描述符定义
 - `altera_utils.c`: 驱动实用函数
 - `altera_utils.h`: 驱动实用函数定义

5. 调试信息
==========
驱动程序导出了调试信息，例如内部统计、调试信息、MAC和DMA寄存器等。
用户可以使用ethool支持来获取统计信息：
例如使用`ethtool -S ethX`（显示统计计数器），
或者查看MAC寄存器：例如使用`ethtool -d ethX`。
开发者还可以使用“debug”模块参数来获取更多的调试信息。

6. 统计支持
==========
控制器和驱动支持混合的IEEE标准定义的统计、RFC定义的统计以及Altera定义的统计。这些统计的标准定义遵循以下四个规范：

 - IEEE 802.3-2012 - IEEE以太网标准
以下是在以下链接中找到的相关文档：
- RFC 2863 可在 http://www.rfc-editor.org/rfc/rfc2863.txt 查阅
- RFC 2819 可在 http://www.rfc-editor.org/rfc/rfc2819.txt 查阅
- Altera 三速以太网用户指南可在 http://www.altera.com 查阅

TSE（Triple Speed Ethernet）和设备驱动程序支持的统计信息如下：

- "tx_packets" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.2 节中的 aFramesTransmittedOK。该统计信息表示成功传输的数据帧数量。
- "rx_packets" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.5 节中的 aFramesReceivedOK。该统计信息表示成功接收的数据帧数量，不包括诸如 CRC 错误、长度错误或对齐错误等错误包。
- "rx_crc_errors" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.6 节中的 aFrameCheckSequenceErrors。该统计信息表示长度为整数个字节但未能通过接收时的 CRC 测试的数据帧数量。
- "rx_align_errors" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.7 节中的 aAlignmentErrors。该统计信息表示长度非整数个字节且未能通过接收时的 CRC 测试的数据帧数量。
- "tx_bytes" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.8 节中的 aOctetsTransmittedOK。该统计信息表示从接口成功传输的数据和填充字节数量。
- "rx_bytes" 等同于 IEEE 802.3-2012 标准第 5.2.2.1.14 节中的 aOctetsReceivedOK。该统计信息表示控制器成功接收的数据和填充字节数量。
- "tx_pause" 等同于 IEEE 802.3-2012 标准第 30.3.4.2 节中的 aPAUSEMACCtrlFramesTransmitted。该统计信息表示从网络控制器发送的 PAUSE 帧的数量。
- "rx_pause" 等同于 IEEE 802.3-2012 标准第 30.3.4.3 节中的 aPAUSEMACCtrlFramesReceived。该统计信息表示网络控制器接收到的 PAUSE 帧的数量。
"rx_errors" 等同于 RFC 2863 中定义的 ifInErrors。该统计值记录了接收到的包含错误的包的数量，这些错误阻止了数据包被递送到更高层协议。
"tx_errors" 等同于 RFC 2863 中定义的 ifOutErrors。该统计值记录了由于错误而无法传输的数据包数量。
"rx_unicast" 等同于 RFC 2863 中定义的 ifInUcastPkts。该统计值记录了接收的未被广播地址或组播群组寻址的数据包数量。
"rx_multicast" 等同于 RFC 2863 中定义的 ifInMulticastPkts。该统计值记录了接收的被组播地址群组寻址的数据包数量。
"rx_broadcast" 等同于 RFC 2863 中定义的 ifInBroadcastPkts。该统计值记录了接收的被广播地址寻址的数据包数量。
"tx_discards" 等同于 RFC 2863 中定义的 ifOutDiscards。该统计值记录了即使没有检测到错误也没有被发送出去的出站数据包数量。发生这种情况的一个例子是为了释放内部缓冲空间。
"tx_unicast" 等同于 RFC 2863 中定义的 ifOutUcastPkts。该统计值记录了发送的未被组播群组或广播地址寻址的数据包数量。
"tx_multicast" 等同于 RFC 2863 中定义的 ifOutMulticastPkts。该统计值记录了发送的被组播群组寻址的数据包数量。
"tx_broadcast" 等同于 RFC 2863 中定义的 ifOutBroadcastPkts。该统计值记录了发送的被广播地址寻址的数据包数量。
"ether_drops" 等同于 RFC 2819 中定义的 etherStatsDropEvents。
这一统计指标计算由于内部控制器资源不足而导致丢弃的数据包数量。

"rx_total_bytes" 等同于在 RFC 2819 中定义的 etherStatsOctets。
该统计指标计算控制器接收到的总字节数，包括错误和被丢弃的数据包。

"rx_total_packets" 等同于在 RFC 2819 中定义的 etherStatsPkts。
该统计指标计算控制器接收到的总数据包数，包括错误、被丢弃的、单播、组播和广播数据包。

"rx_undersize" 等同于在 RFC 2819 中定义的 etherStatsUndersizePkts。
该统计指标计算接收到的长度小于 64 字节的正确格式的数据包数量。

"rx_oversize" 等同于在 RFC 2819 中定义的 etherStatsOversizePkts。
该统计指标计算接收到的大于 1518 字节的正确格式的数据包数量。

"rx_64_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts64Octets。
此统计计算接收的所有长度为 64 字节的数据包总数。

"rx_65_127_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts65to127Octets。此统计计算接收的所有长度在 65 到 127 字节（含）之间的数据包总数。

"rx_128_255_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts128to255Octets。此统计是接收的所有长度在 128 到 255 字节（含）之间的数据包总数。

"rx_256_511_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts256to511Octets。此统计是接收的所有长度在 256 到 511 字节（含）之间的数据包总数。

"rx_512_1023_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts512to1023Octets。此统计是接收的所有长度在 512 到 1023 字节（含）之间的数据包总数。

"rx_1024_1518_bytes" 等同于在 RFC 2819 中定义的 etherStatsPkts1024to1518Octets。此统计是接收的所有长度在 1024 到 1518 字节（含）之间的数据包总数。

"rx_gte_1519_bytes" 是针对 Altera TSE 行为特别定义的统计。此统计计算接收的良好和错误帧的数量，这些帧的长度介于 1519 和在 frm_length 寄存器中配置的最大帧长度之间。更多详情请参阅 Altera TSE 用户指南。

"rx_jabbers" 等同于在 RFC 2819 中定义的 etherStatsJabbers。此统计是接收的所有长度超过 1518 字节，并且具有整数个字节的坏 CRC（CRC 错误）或非整数个字节的坏 CRC（对齐错误）的数据包总数。

"rx_runts" 等同于在 RFC 2819 中定义的 etherStatsFragments。此统计是接收的所有长度小于 64 字节，并且具有整数个字节的坏 CRC（CRC 错误）或非整数个字节的坏 CRC（对齐错误）的数据包总数。
