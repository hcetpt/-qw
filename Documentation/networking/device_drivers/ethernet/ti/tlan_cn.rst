SPDX 许可证标识符: GPL-2.0

=====================
Linux 下的 TLAN 驱动程序
=====================

:版本: 1.14a

(C) 1997-1998 Caldera, Inc
(C) 1998 James Banks

(C) 1999-2001 Torben Mathiasen <tmm@image.dk, torben.mathiasen@compaq.com>

有关驱动程序信息/更新，请访问 http://www.compaq.com



I. 支持的设备
====================

    仅支持 PCI 设备使用此驱动程序
支持的设备：

    =========	=========	===========================================
    厂商ID	设备ID	名称
    =========	=========	===========================================
    0e11	ae32		Compaq Netelligent 10/100 TX PCI UTP
    0e11	ae34		Compaq Netelligent 10 T PCI UTP
    0e11	ae35		Compaq Integrated NetFlex 3/P
    0e11	ae40		Compaq Netelligent 双端口 10/100 TX PCI UTP
    0e11	ae43		Compaq Netelligent 集成 10/100 TX UTP
    0e11	b011		Compaq Netelligent 10/100 TX 嵌入式 UTP
    0e11	b012		Compaq Netelligent 10 T/2 PCI UTP/同轴
    0e11	b030		Compaq Netelligent 10/100 TX UTP
    0e11	f130		Compaq NetFlex 3/P
    0e11	f150		Compaq NetFlex 3/P
    108d	0012		Olicom OC-2325
    108d	0013		Olicom OC-2183
    108d	0014		Olicom OC-2326
    =========	=========	===========================================


    注意事项：

    我不确定带有 100BaseTX 子板的卡（对于支持此类子板的卡）是否能正常工作。目前没有得到任何确凿证据。
但是，如果一张卡支持 100BaseTx 并且不需要额外的子板，则它应该能够以 100BaseTx 模式运行。
“Netelligent 10 T/2 PCI UTP/同轴”（b012）设备未经测试，
但我预计不会出现任何问题。
II. 驱动程序选项
==================

	1. 您可以在 insmod 命令行的末尾追加 debug=x 来获取调试信息，其中 x 是一个位字段，位的含义如下：

	   ====		=====================================
	   0x01		启用一般调试消息
0x02		启用接收调试消息
0x04		启用发送调试消息
0x08		启用列表调试消息
====		=====================================

	2. 您可以在 insmod 命令行的末尾追加 aui=1 以使适配器使用 AUI 接口而非 10 Base T 接口。这也是如果您想要使用基于 TLAN 的设备上的 BNC 连接器时需要做的设置。（在没有 AUI/BNC 连接器的设备上设置此选项可能会导致其无法正常工作。）

	3. 您可以设置 duplex=1 来强制半双工模式，以及 duplex=2 来强制全双工模式。
4. 您可以设置 `speed=10` 来强制使用 10Mbps 的操作，以及设置 `speed=100` 来强制使用 100Mbps 的操作。（我不确定如果一张仅支持 10Mbps 的网卡被强制设置为 100Mbps 模式会发生什么情况。）

5. 现在您必须一起使用 `speed=X` 和 `duplex=Y`。如果您只执行 `"insmod tlan.o speed=100"`，驱动程序将进行自动协商（Auto-Negotiation）。要强制设置一个 10Mbps 半双工连接，请执行 `"insmod tlan.o speed=10 duplex=1"`。
   
6. 如果驱动程序集成在内核中，您可以使用第三个和第四个参数分别设置 AUI 和调试级别。例如：

```
ether=0,0,0x1,0x7,eth0
```

这将把 AUI 设置为 0x1 并将调试级别设置为 0x7，前提是 eth0 是一个受支持的 TLAN 设备。
第三个字节中的位分配如下：

| 位值 | 含义             |
|------|------------------|
| 0x01 | AUI              |
| 0x02 | 使用半双工       |
| 0x04 | 使用全双工       |
| 0x08 | 使用 10BaseT     |
| 0x10 | 使用 100BaseTx   |

当使用内核参数强制设置速度时，还需要同时设置速度和双工模式。
例如，`ether=0,0,0x12,0,eth0` 将强制连接为 100Mbps 半双工。

7. 如果您的系统中有多个 tlan 适配器，您可以针对每个适配器单独使用上述选项。要将 eth1 适配器的连接强制设置为 100Mbps/半双工，请执行：

```
insmod tlan speed=0,100 duplex=0,1
```

现在 eth0 将使用自动协商，而 eth1 将被强制设置为 100Mbps/半双工。
请注意，tlan 驱动程序最多支持 8 个适配器。

### 如果遇到问题可尝试以下步骤
1. 确保您的网卡的 PCI ID 在上文第一部分所列出的范围内。
2. 确保路由配置正确。
3. 尝试强制不同的速度/双工设置。

此外，还有一个 tlan 邮件列表，您可以通过发送包含 "subscribe tlan" 的邮件正文到 `majordomo@vuser.vu.union.edu` 来加入。
还有一个网站位于 http://www.compaq.com，但似乎"tlan"可能是输入错误或语义不清晰的部分。如果是指的 "Compaq" 的官方网站，那么正确的表达应该是：“还有一个 Compaq 的官方网站位于 http://www.compaq.com。” 如果 "tlan" 有特别的意思或者是指的其他内容，请提供更多的上下文信息以便我能更准确的帮助您。
