SPDX 许可声明标识符: GPL-2.0
.. include:: <isonum.txt>

=================================
Marvell（Aquantia）AQtion 驱动程序
=================================

适用于 aQuantia 多千兆位 PCI Express 系列以太网适配器

.. 目录

    - 识别您的适配器
    - 配置
    - 支持的 ethtool 选项
    - 命令行参数
    - 配置文件参数
    - 支持
    - 许可证

识别您的适配器
================

此版本的驱动程序兼容基于 AQC-100、AQC-107 和 AQC-108 的以太网适配器。
SFP+ 设备（对于基于 AQC-100 的适配器）
-----------------------------------------

此版本已使用被动直连电缆（DAC）和 SFP+/LC 光收发器进行了测试。

配置
=============

查看链路消息
---------------------
如果发行版限制了系统消息，则不会在控制台上显示链路消息。为了在控制台上看到网络驱动程序的链路消息，请将 dmesg 设置为 8，方法如下：

```
dmesg -n 8
```

.. note::

    此设置不会保存到重启后。

巨型帧
------------
该驱动程序支持所有适配器的巨型帧。要启用巨型帧支持，需要将 MTU 更改为大于默认值 1500 的数值。MTU 的最大值是 16000。使用 `ip` 命令来增加 MTU 大小。例如：

```
ip link set mtu 16000 dev enp1s0
```

ethtool
-------
该驱动程序利用 ethtool 接口进行驱动程序配置和诊断，以及显示统计信息。此功能需要最新版本的 ethtool。

NAPI
----
NAPI（接收轮询模式）在 atlantic 驱动程序中受支持。

支持的 ethtool 选项
=========================

查看适配器设置
------------------------

```
ethtool <ethX>
```

输出示例：

```
enp1s0 的设置：
    支持的端口：[ TP ]
    支持的链路模式：   100baseT/全双工
			    1000baseT/全双工
			    10000baseT/全双工
			    2500baseT/全双工
			    5000baseT/全双工
    支持的暂停帧使用：对称
    支持自动协商：是
    支持的 FEC 模式：未报告
    宣告的链路模式：  100baseT/全双工
			    1000baseT/全双工
			    10000baseT/全双工
			    2500baseT/全双工
			    5000baseT/全双工
    宣告的暂停帧使用：对称
    宣告的自动协商：是
    宣告的 FEC 模式：未报告
    速度：10000Mbps
    双工模式：全双工
    端口：双绞线
    PHY 地址：0
    收发器：内部
    自动协商：开启
    MDI-X：未知
    支持的唤醒功能：g
    唤醒功能：d
    检测到链路：是
```

.. note::

    AQrate 速度（2.5/5 Gbps）仅在 Linux 内核版本 > 4.10 中显示。但您仍然可以使用这些速度：

```
ethtool -s eth0 autoneg off speed 2500
```

查看适配器信息
---------------------------

```
ethtool -i <ethX>
```

输出示例：

```
驱动程序：atlantic
版本：5.2.0-050200rc5-generic-kern
固件版本：3.1.78
扩展 ROM 版本：
总线信息：0000:01:00.0
支持统计信息：是
支持测试：否
支持 EEPROM 访问：否
支持寄存器转储：是
支持私有标志：否
```

查看以太网适配器统计信息
-----------------------------------

```
ethtool -S <ethX>
```

输出示例：

```
NIC 统计信息：
     接收数据包：13238607
     接收单播数据包：13293852
     接收组播数据包：52
     接收广播数据包：3
     接收错误：0
     发送数据包：23703019
     发送单播数据包：23704941
     发送组播数据包：67
     发送广播数据包：11
     接收单播字节数：213182760
     发送单播字节数：22698443
     接收组播字节数：6600
     发送组播字节数：8776
     接收广播字节数：192
     发送广播字节数：704
     接收字节数：2131839552
     发送字节数：226938073
     DMA 接收数据包：95532300
     DMA 发送数据包：59503397
     DMA 接收字节数：1137102462
     DMA 发送字节数：2394339518
     DMA 接收丢弃：0
     队列[0] 接收数据包：23567131
     队列[0] 发送数据包：20070028
     队列[0] 接收巨型数据包：0
     队列[0] 接收 LRO 数据包：0
     队列[0] 接收错误：0
     队列[1] 接收数据包：45428967
     队列[1] 发送数据包：11306178
     队列[1] 接收巨型数据包：0
     队列[1] 接收 LRO 数据包：0
     队列[1] 接收错误：0
     队列[2] 接收数据包：3187011
     队列[2] 发送数据包：13080381
     队列[2] 接收巨型数据包：0
     队列[2] 接收 LRO 数据包：0
     队列[2] 接收错误：0
     队列[3] 接收数据包：23349136
     队列[3] 发送数据包：15046810
     队列[3] 接收巨型数据包：0
     队列[3] 接收 LRO 数据包：0
     队列[3] 接收错误：0
```

中断合并支持
----------------------------

ITR 模式，TX/RX 合并定时可以通过以下命令查看：

```
ethtool -c <ethX>
```

并且可以通过以下命令更改：

```
ethtool -C <ethX> tx-usecs <usecs> rx-usecs <usecs>
```

要禁用合并：

```
ethtool -C <ethX> tx-usecs 0 rx-usecs 0 tx-max-frames 1 tx-max-frames 1
```

WOL 支持
-------------------

通过魔法包支持 WOL：

```
ethtool -s <ethX> wol g
```

要禁用 WOL：

```
ethtool -s <ethX> wol d
```

设置和检查驱动程序消息级别
--------------------------------------

设置消息级别

```
ethtool -s <ethX> msglvl <level>
```

级别值：

======   =============================
0x0001   驱动程序的一般状态
0x0002   硬件探测
0x0004   链路状态
0x0008   周期性状态检查
0x0010   接口被关闭
0x0020   接口被启动
0x0040   接收错误
0x0080   发送错误
0x0200   中断处理
0x0400   发送完成
0x0800   接收完成
0x1000   数据包内容
0x2000   硬件状态
0x4000   Wake-on-LAN 状态
======   =============================

默认情况下，调试消息的级别设置为 0x0001（通用驱动程序状态）。
检查消息级别：

::
    
    ethtool <ethX> | grep "当前消息级别"

如果您想禁用消息输出：

::
    
    ethtool -s <ethX> msglvl 0

接收流规则（n元组过滤器）
------------------------------

支持的规则如下，并按此顺序应用：

1. 16 个 VLAN ID 规则
2. 16 个 L2 EtherType 规则
3. 8 个 L3/L4 五元组规则

驱动程序利用 ethtool 接口配置 n 元组过滤器，通过 `ethtool -N <设备> <过滤器>` 命令来实现。要启用或禁用接收流规则：

::
    
    ethtool -K ethX ntuple <on|off>

当禁用 n 元组过滤器时，所有用户编程的过滤器将从驱动程序缓存和硬件中清除。重新启用 ntuple 时必须重新添加所有需要的过滤器。

由于规则的顺序是固定的，因此过滤器的位置也是固定的：
- VLAN ID 过滤器位于位置 0 - 15
- L2 EtherType 过滤器位于位置 16 - 31
- L3/L4 五元组过滤器位于位置 32 - 39（IPv6 的位置为 32 和 36）

L3/L4 五元组（协议、源和目标 IP 地址、源和目标 TCP/UDP/SCTP 端口）将与 8 个过滤器进行比较。对于 IPv4，最多可以匹配 8 个源和目标地址。对于 IPv6，最多可以支持 2 对地址。仅对 TCP/UDP/SCTP 数据包进行源和目标端口的比较。

要添加一个将数据包导向队列 5 的过滤器，使用 `<-N|-U|--config-nfc|--config-ntuple>` 选项：

::
    
    ethtool -N <ethX> flow-type udp4 src-ip 10.0.0.1 dst-ip 10.0.0.2 src-port 2000 dst-port 2001 action 5 <loc 32>

- action 是队列编号
- loc 是规则编号

对于 `flow-type ip4|udp4|tcp4|sctp4|ip6|udp6|tcp6|sctp6`，您必须在位置 32 - 39 内设置 loc 编号。

对于 `flow-type ip4|udp4|tcp4|sctp4|ip6|udp6|tcp6|sctp6`，您可以设置 8 条 IPv4 流量规则，或者设置 2 条 IPv6 流量规则。IPv6 流量的 loc 编号为 32 和 36。

目前，您不能同时使用 IPv4 和 IPv6 过滤器。
IPv6流量过滤示例：

```
sudo ethtool -N <ethX> flow-type tcp6 src-ip 2001:db8:0:f101::1 dst-ip 2001:db8:0:f101::2 action 1 loc 32
sudo ethtool -N <ethX> flow-type ip6 src-ip 2001:db8:0:f101::2 dst-ip 2001:db8:0:f101::5 action -1 loc 36
```

IPv4流量过滤示例：

```
sudo ethtool -N <ethX> flow-type udp4 src-ip 10.0.0.4 dst-ip 10.0.0.7 src-port 2000 dst-port 2001 loc 32
sudo ethtool -N <ethX> flow-type tcp4 src-ip 10.0.0.3 dst-ip 10.0.0.9 src-port 2000 dst-port 2001 loc 33
sudo ethtool -N <ethX> flow-type ip4 src-ip 10.0.0.6 dst-ip 10.0.0.4 loc 34
```

如果设置`action -1`，则所有符合该过滤器的流量将被丢弃。
`action`的最大值为31。
VLAN过滤器（VLAN ID）与16个过滤器进行比较。
VLAN ID必须带有掩码`0xF000`。这是为了区分VLAN过滤器和带有用户优先级（UserPriority）的L2 Ethertype过滤器，因为两者都通过相同的`vlan`参数传递。

要添加一个将VLAN 2001中的数据包定向到队列5的过滤器，请执行以下命令：

```
ethtool -N <ethX> flow-type ip4 vlan 2001 m 0xF000 action 1 loc 0
```

L2 Ethertype过滤器允许根据Ethertype字段或同时根据Ethertype和用户优先级（PCP）字段过滤数据包。
`UserPriority`（vlan）参数必须带有掩码`0x1FFF`。这是为了区分VLAN过滤器和带有用户优先级的L2 Ethertype过滤器，因为两者都通过相同的`vlan`参数传递。

要添加一个将优先级为3的IP4数据包定向到队列3的过滤器，请执行以下命令：

```
ethtool -N <ethX> flow-type ether proto 0x800 vlan 0x600 m 0x1FFF action 3 loc 16
```

要查看当前存在的过滤器列表，请执行以下命令：

```
ethtool <-u|-n|--show-nfc|--show-ntuple> <ethX>
```

可以从表中删除规则。这可以通过以下命令完成：

```
sudo ethtool <-N|-U|--config-nfc|--config-ntuple> <ethX> delete <loc>
```

- `loc`是要删除的规则编号

接收过滤器是一个加载过滤器表的接口，所有流量默认都会进入队列0，除非使用`action`指定了其他队列。在这种情况下，任何符合过滤器条件的流量都将被定向到相应的队列。接收过滤器支持所有2.6.30及更高版本的内核。

UDP RSS
-------

目前，NIC不支持分片IP数据包的RSS，这会导致分片UDP流量的RSS工作不正确。可以使用L3/L4接收流规则来禁用UDP的RSS。
示例：

```
ethtool -N eth0 flow-type udp4 action 0 loc 32
```

UDP GSO硬件卸载
-------------------

UDP GSO允许通过将UDP报头分配卸载到硬件来提高UDP传输速率。为此需要一个特殊的用户空间套接字选项，可以通过以下命令验证：

```
udpgso_bench_tx -u -4 -D 10.0.1.1 -s 6300 -S 100
```

这将导致发送由单个6300字节用户缓冲区组成的100字节大小的UDP数据包。
UDP GSO 的配置如下：

    ethtool -K eth0 tx-udp-segmentation on

私有标志（测试）
-----------------------

Atlantic 驱动支持用于硬件自定义功能的私有标志：

	$ ethtool --show-priv-flags ethX

	ethX 的私有标志：
	DMASystemLoopback  : 关闭
	PKTSystemLoopback  : 关闭
	DMANetworkLoopback : 关闭
	PHYInternalLoopback: 关闭
	PHYExternalLoopback: 关闭

示例：

	$ ethtool --set-priv-flags ethX DMASystemLoopback on

DMASystemLoopback:   DMA 主机环回
PKTSystemLoopback:   数据包缓冲区主机环回
DMANetworkLoopback:  在 DMA 块上的网络侧环回
PHYInternalLoopback: 在 PHY 上的内部环回
PHYExternalLoopback: 在 PHY 上的外部环回（使用环回以太网线）

命令行参数
=======================
以下命令行参数可用于 Atlantic 驱动：

aq_itr - 中断节流模式
---------------------------------
接受的值：0, 1, 0xFFFF

默认值：0xFFFF

======   ==============================================================
0        禁用中断节流
1        启用中断节流并使用指定的发送和接收速率
0xFFFF   自动节流模式。驱动程序将根据链路速度选择最佳的接收和发送中断节流设置
======   ==============================================================

aq_itr_tx - 发送中断节流速率
--------------------------------------

接受的值：0 - 0x1FF

默认值：0

发送端节流，单位为微秒。适配器将设置最大中断延迟为此值。最小中断延迟将是此值的一半。

aq_itr_rx - 接收中断节流速率
--------------------------------------

接受的值：0 - 0x1FF

默认值：0

接收端节流，单位为微秒。适配器将设置最大中断延迟为此值。最小中断延迟将是此值的一半。

.. note::

   可以通过 ethtool -c 在运行时更改 ITR 设置（见下文）

配置文件参数
======================

为了进行一些细微调整和性能优化，
可以在 {source_dir}/aq_cfg.h 文件中更改某些参数

AQ_CFG_RX_PAGEORDER
-------------------

默认值：0

接收页面顺序覆盖。这是分配给每个描述符的接收页面数量的2的幂次。接收到的描述符大小仍受 AQ_CFG_RX_FRAME_MAX 的限制。
增加 `pageorder` 可以提高页面重用效果（在启用了 IOMMU 的系统上尤为明显）。

AQ_CFG_RX_REFILL_THRES
----------------------

默认值：32

接收（RX）路径的重新填充阈值。在达到指定数量的空闲描述符之前，接收路径不会重新填充已释放的描述符。较大的值可能会更好地利用页面，但也可能导致丢包。

AQ_CFG_VECS_DEF
---------------

队列的数量

有效范围：0 - 8（最多为 AQ_CFG_VECS_MAX）

默认值：8

请注意，此值将受系统可用核心数量的限制。

AQ_CFG_IS_RSS_DEF
-----------------

启用/禁用接收端扩展（Receive Side Scaling）

此功能允许适配器将接收处理分布在多个 CPU 核心上，防止单个 CPU 核心过载。
有效值：

==  ========
0   禁用
1   启用
==  ========

默认值：1

AQ_CFG_NUM_RSS_QUEUES_DEF
-------------------------

用于接收端扩展的队列数量

有效范围：0 - 8（最多为 AQ_CFG_VECS_DEF）

默认值：AQ_CFG_VECS_DEF

AQ_CFG_IS_LRO_DEF
-----------------

启用/禁用大包接收卸载（Large Receive Offload）

此卸载使适配器能够合并多个 TCP 分段，并将其作为一个合并后的单元指示给操作系统网络子系统。这减少了系统的能耗，但也会引入更多的数据包处理延迟。
有效值：

==  ========
0   禁用
1   启用
==  ========

默认值：1

AQ_CFG_TX_CLEAN_BUDGET
----------------------

一次可以清理的最大发送（TX）描述符数量

默认值：256

在修改了 `aq_cfg.h` 文件后，必须重新编译驱动程序才能生效。

支持
=====

如果在支持的内核和适配器上发现发布源代码存在问题，请将与问题相关的信息发送到 aqn_support@marvell.com。

许可
=====

aQuantia Corporation 网络驱动程序

版权所有 © 2014 - 2019 aQuantia Corporation
本程序是自由软件；您可以根据由 Free Software Foundation 发布的 GNU 通用公共许可证版本 2 的条款和条件进行再分发或修改。
当然，请提供您需要翻译的文本。
