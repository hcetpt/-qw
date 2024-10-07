SPDX 许可证标识符: GPL-2.0

=====================
Linux 的 TLAN 驱动程序
=====================

:版本: 1.14a

(C) 1997-1998 Caldera, Inc
(C) 1998 James Banks

(C) 1999-2001 Torben Mathiasen <tmm@image.dk, torben.mathiasen@compaq.com>

有关驱动程序信息/更新，请访问 http://www.compaq.com

---

I. 支持的设备
====================

    仅支持 PCI 设备使用此驱动程序
支持的设备：

    =========	=========	===========================================
    厂商ID	设备ID	名称
    =========	=========	===========================================
    0e11	ae32		康柏 Netelligent 10/100 TX PCI UTP
    0e11	ae34		康柏 Netelligent 10 T PCI UTP
    0e11	ae35		康柏 Integrated NetFlex 3/P
    0e11	ae40		康柏 Netelligent 双 10/100 TX PCI UTP
    0e11	ae43		康柏 Netelligent Integrated 10/100 TX UTP
    0e11	b011		康柏 Netelligent 10/100 TX 嵌入式 UTP
    0e11	b012		康柏 Netelligent 10 T/2 PCI UTP/同轴
    0e11	b030		康柏 Netelligent 10/100 TX UTP
    0e11	f130		康柏 NetFlex 3/P
    0e11	f150		康柏 NetFlex 3/P
    108d	0012		Olicom OC-2325
    108d	0013		Olicom OC-2183
    108d	0014		Olicom OC-2326
    =========	=========	===========================================

注意事项：

    我不确定是否 100BaseTX 扩展板（对于那些支持此类扩展板的网卡）能够工作。我还没有得到任何确凿的证据。
然而，如果一张网卡支持 100BaseTx 而不需要额外的扩展板，则应该能正常工作。
“Netelligent 10 T/2 PCI UTP/同轴”（b012）设备未经测试，但我预计不会有任何问题。

---

II. 驱动程序选项
==================

    1. 您可以在 insmod 命令行末尾添加 debug=x 来获取调试消息，其中 x 是一个位字段，位的意义如下：

       ====		=====================================
       0x01		启用一般调试消息
0x02		启用接收调试消息
0x04		启用发送调试消息
0x08		启用列表调试消息
       ====		=====================================

    2. 您可以在 insmod 命令行末尾添加 aui=1 以使适配器使用 AUI 接口而不是 10 Base T 接口。这也是如果您想使用基于 TLAN 的设备上的 BNC 连接器时应做的设置。（在没有 AUI/BNC 连接器的设备上设置此选项可能会导致其无法正确运行。）

    3. 您可以设置 duplex=1 强制半双工模式，设置 duplex=2 强制全双工模式
4. 您可以设置 `speed=10` 来强制使用 10 Mbps，设置 `speed=100` 来强制使用 100 Mbps。（我不确定如果一张只支持 10 Mbps 的网卡被强制到 100 Mbps 模式会发生什么。）

5. 现在您必须一起使用 `speed=X` 和 `duplex=Y`。如果您只执行 `insmod tlan.o speed=100`，驱动程序将会进行自动协商（Auto-Neg）。要强制一个 10 Mbps 半双工连接，请执行 `insmod tlan.o speed=10 duplex=1`。

6. 如果驱动程序被编译进内核中，您可以使用第三个和第四个参数分别设置 AUI 和调试选项。例如：

```
ether=0,0,0x1,0x7,eth0
```

这将把 AUI 设置为 0x1 并把调试设置为 0x7，假设 eth0 是一个受支持的 TLAN 设备。
第三个字节中的位分配如下：

| 位值 | 含义           |
|------|----------------|
| 0x01 | AUI            |
| 0x02 | 使用半双工     |
| 0x04 | 使用全双工     |
| 0x08 | 使用 10BaseT   |
| 0x10 | 使用 100BaseTx |

当通过内核参数强制速度时，也需要设置速度和双工模式。
例如，`ether=0,0,0x12,0,eth0` 将强制连接为 100 Mbps 半双工。

7. 如果您的系统中有多个 tlan 适配器，您可以按每个适配器分别使用上述选项。要强制 eth1 适配器为 100 Mbps/半双工连接，请执行：

```
insmod tlan speed=0,100 duplex=0,1
```

现在 eth0 将使用自动协商，而 eth1 将被强制为 100 Mbps/半双工。
请注意，tlan 驱动程序最多支持 8 个适配器。

### III. 如果遇到问题可以尝试的方法
1. 确保您的网卡的 PCI ID 在上面第一部分列出的范围内。
2. 确保路由配置正确。
3. 尝试强制不同的速度/双工设置。

还有一个 tlan 邮件列表，您可以通过发送包含 “subscribe tlan” 的邮件内容到 majordomo@vuser.vu.union.edu 加入该邮件列表。
还有一个tlan网站，网址是http://www.compaq.com
