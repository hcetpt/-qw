Marvell (Aquantia) AQtion 驱动程序

针对 aQuantia 多千兆位 PCI Express 系列以太网适配器

.. 目录

    - 识别您的适配器
    - 配置
    - 支持的 ethtool 选项
    - 命令行参数
    - 配置文件参数
    - 支持
    - 许可证

识别您的适配器
========================

本版本中的驱动程序与基于 AQC-100、AQC-107 和 AQC-108 的以太网适配器兼容。
SFP+ 设备（针对基于 AQC-100 的适配器）
-----------------------------------------

此版本经过测试，支持被动直连电缆 (DAC) 和 SFP+/LC 光收发器。
配置
=============

查看连接消息
---------------------
如果操作系统限制了系统消息，则不会在控制台上显示连接消息。为了在控制台上看到网络驱动程序的连接消息，请将 dmesg 设置为 8，方法如下：

       dmesg -n 8

  .. 注意::

     此设置不会在重启后保存
巨型帧
------------
该驱动程序支持所有适配器的巨型帧。通过将最大传输单元 (MTU) 更改为大于默认值 1500 的值来启用对巨型帧的支持。MTU 的最大值为 16000。使用 `ip` 命令增加 MTU 大小。例如：

	ip link set mtu 16000 dev enp1s0

ethtool
-------
该驱动程序利用 ethtool 接口进行驱动程序配置和诊断，以及显示统计信息。此功能需要最新的 ethtool 版本。
NAPI
----
NAPI（接收轮询模式）在 atlantic 驱动程序中得到支持。
支持的 ethtool 选项
=========================

查看适配器设置
------------------------

 ::

    ethtool <ethX>

输出示例：

  对于 enp1s0 的设置：
    支持的端口：[ TP ]
    支持的连接模式：   100baseT/全双工
			    1000baseT/全双工
			    10000baseT/全双工
			    2500baseT/全双工
			    5000baseT/全双工
    支持的暂停帧使用：对称
    支持自动协商：是
    支持的 FEC 模式：未报告
    宣告的连接模式：  100baseT/全双工
			    1000baseT/全双工
			    10000baseT/全双工
			    2500baseT/全双工
			    5000baseT/全双工
    宣告的暂停帧使用：对称
    宣告的自动协商：是
    宣告的 FEC 模式：未报告
    速度：10000Mb/s
    双工：全双工
    端口：双绞线
    PHY 地址：0
    收发器：内部
    自动协商：开启
    MDI-X：未知
    支持唤醒：g
    唤醒：d
    检测到链接：是

 .. 注意::

    AQrate 速度（2.5/5 Gb/s）仅在 Linux 内核 > 4.10 中显示。但您仍然可以使用这些速度：

	ethtool -s eth0 autoneg off speed 2500

查看适配器信息
---------------------------

 ::

  ethtool -i <ethX>

输出示例：

  驱动程序：atlantic
  版本：5.2.0-050200rc5-generic-kern
  固件版本：3.1.78
  扩展ROM版本：
  总线信息：0000:01:00.0
  支持统计信息：是
  支持测试：否
  支持 EEPROM 访问：否
  支持寄存器转储：是
  支持私有标志：否


查看以太网适配器统计信息
-----------------------------------

 ::

    ethtool -S <ethX>

输出示例：

  NIC 统计信息：
     接收数据包：13238607
     接收单播：13293852
     接收多播：52
     接收广播：3
     接收错误：0
     发送数据包：23703019
     发送单播：23704941
     发送多播：67
     发送广播：11
     接收单播字节：213182760
     发送单播字节：22698443
     接收多播字节：6600
     发送多播字节：8776
     接收广播字节：192
     发送广播字节：704
     接收字节：2131839552
     发送字节：226938073
     DMA 接收数据包：95532300
     DMA 发送数据包：59503397
     DMA 接收字节：1137102462
     DMA 发送字节：2394339518
     DMA 接收丢弃：0
     队列[0] 接收数据包：23567131
     队列[0] 发送数据包：20070028
     队列[0] 接收巨型帧：0
     队列[0] 接收 LRO 数据包：0
     队列[0] 接收错误：0
     队列[1] 接收数据包：45428967
     队列[1] 发送数据包：11306178
     队列[1] 接收巨型帧：0
     队列[1] 接收 LRO 数据包：0
     队列[1] 接收错误：0
     队列[2] 接收数据包：3187011
     队列[2] 发送数据包：13080381
     队列[2] 接收巨型帧：0
     队列[2] 接收 LRO 数据包：0
     队列[2] 接收错误：0
     队列[3] 接收数据包：23349136
     队列[3] 发送数据包：15046810
     队列[3] 接收巨型帧：0
     队列[3] 接收 LRO 数据包：0
     队列[3] 接收错误：0

中断合并支持
----------------------------

ITR 模式，TX/RX 合并定时可以通过以下方式查看：

    ethtool -c <ethX>

并且可以更改：

    ethtool -C <ethX> tx-usecs <usecs> rx-usecs <usecs>

要禁用合并：

    ethtool -C <ethX> tx-usecs 0 rx-usecs 0 tx-max-frames 1 tx-max-frames 1

远程唤醒支持
-------------------

通过魔术封包支持 WOL：

    ethtool -s <ethX> wol g

要禁用 WOL：

    ethtool -s <ethX> wol d

设置和检查驱动程序消息级别
--------------------------------------

设置消息级别

 ::

    ethtool -s <ethX> msglvl <level>

级别值：

 ======   =============================
 0x0001   驱动程序的一般状态
0x0002   硬件探测
0x0004   链接状态
0x0008   周期性状态检查
0x0010   接口被关闭
0x0020   接口被启用
0x0040   接收错误
0x0080   发送错误
0x0200   中断处理
0x0400   发送完成
0x0800   接收完成
0x1000   数据包内容
0x2000   硬件状态
0x4000   网络唤醒状态  
======   =============================  

默认情况下，调试消息的级别设置为 0x0001（通用驱动程序状态）。  
检查消息级别  

::  

    ethtool <ethX> | grep "当前消息级别"  

如果您想禁用消息输出：  

    ethtool -s <ethX> msglvl 0  

RX 流量规则（n元组过滤器）  
------------------------------

支持以下独立规则，应用顺序如下：  

1. 16 个 VLAN ID 规则  
2. 16 个第 2 层 EtherType 规则  
3. 8 个第 3/4 层 5 元组规则  

驱动程序通过 ethtool 接口配置 n 元组过滤器，使用命令 `ethtool -N <设备> <过滤器>`。  
要启用或禁用 RX 流量规则：  

    ethtool -K ethX ntuple <on|off>  

当禁用 n 元组过滤器时，所有用户编程的过滤器都会从驱动程序缓存和硬件中清除。重新启用 ntuple 时，必须重新添加所有必要的过滤器。  
由于规则的固定顺序，过滤器的位置也是固定的：  

- 位置 0 - 15 用于 VLAN ID 过滤器  
- 位置 16 - 31 用于第 2 层 EtherType 过滤器  
- 位置 32 - 39 用于第 3/4 层 5 元组过滤器（位置 32、36 用于 IPv6）  

第 3/4 层 5 元组（协议、源和目标 IP 地址、源和目标 TCP/UDP/SCTP 端口）将与 8 个过滤器进行比较。对于 IPv4，最多可以匹配 8 个源和目标地址。对于 IPv6，最多可以支持 2 对地址。源端口和目标端口仅在 TCP/UDP/SCTP 数据包中进行比较。  
要添加一个将数据包导向队列 5 的过滤器，请使用 `<-N|-U|--config-nfc|--config-ntuple>` 开关：  

    ethtool -N <ethX> flow-type udp4 src-ip 10.0.0.1 dst-ip 10.0.0.2 src-port 2000 dst-port 2001 action 5 <loc 32>  

- action 是队列编号  
- loc 是规则编号  

对于 `flow-type ip4|udp4|tcp4|sctp4|ip6|udp6|tcp6|sctp6`，您必须在 32 - 39 之间设置 loc 编号。  
对于 `flow-type ip4|udp4|tcp4|sctp4|ip6|udp6|tcp6|sctp6`，您可以为 IPv4 流量设置 8 条规则，或者为 IPv6 流量设置 2 条规则。IPv6 流量的 loc 编号是 32 和 36。  
目前，您不能同时使用 IPv4 和 IPv6 过滤器。
示例IPv6流量过滤命令：

    sudo ethtool -N <ethX> flow-type tcp6 src-ip 2001:db8:0:f101::1 dst-ip 2001:db8:0:f101::2 action 1 loc 32
    sudo ethtool -N <ethX> flow-type ip6 src-ip 2001:db8:0:f101::2 dst-ip 2001:db8:0:f101::5 action -1 loc 36

示例IPv4流量过滤命令：

    sudo ethtool -N <ethX> flow-type udp4 src-ip 10.0.0.4 dst-ip 10.0.0.7 src-port 2000 dst-port 2001 loc 32
    sudo ethtool -N <ethX> flow-type tcp4 src-ip 10.0.0.3 dst-ip 10.0.0.9 src-port 2000 dst-port 2001 loc 33
    sudo ethtool -N <ethX> flow-type ip4 src-ip 10.0.0.6 dst-ip 10.0.0.4 loc 34

如果设置`action -1`，则所有与该过滤器匹配的流量将被丢弃。
`action`的最大值为31。
VLAN过滤器（VLAN ID）与16个过滤器进行比较。
VLAN ID必须与掩码`0xF000`一起使用。这是为了区分VLAN过滤器和带有用户优先级的L2 Ethertype过滤器，因为用户优先级和VLAN ID都通过相同的`vlan`参数传递。
要添加一个将VLAN 2001中的数据包导向队列5的过滤器：

    ethtool -N <ethX> flow-type ip4 vlan 2001 m 0xF000 action 1 loc 0

L2 Ethertype过滤器允许根据Ethertype字段或同时根据Ethertype字段和802.1Q中的用户优先级字段来过滤数据包。
`UserPriority (vlan)`参数必须与掩码`0x1FFF`一起使用。这是为了区分VLAN过滤器和带有用户优先级的L2 Ethertype过滤器，因为用户优先级和VLAN ID都通过相同的`vlan`参数传递。
要添加一个将优先级为3的IP4数据包导向队列3的过滤器：

    ethtool -N <ethX> flow-type ether proto 0x800 vlan 0x600 m 0x1FFF action 3 loc 16

要查看当前存在的过滤器列表：

    ethtool <-u|-n|--show-nfc|--show-ntuple> <ethX>

可以删除表中的规则。这可以通过以下命令完成：

    sudo ethtool <-N|-U|--config-nfc|--config-ntuple> <ethX> delete <loc>

- `loc`是要删除的规则编号
接收过滤器是一个接口，用于加载将所有流量引导至队列0（除非使用"action"指定其他队列）的过滤器表。在这种情况下，任何符合过滤器标准的流量都将被导向适当的队列。所有内核版本2.6.30及以后均支持RX过滤器。

UDP RSS
-------

目前，网卡不支持分片IP数据包的RSS功能，这导致分片UDP流量的RSS工作不正确。可以使用RX流L3/L4规则禁用UDP的RSS功能。
示例命令：

    ethtool -N eth0 flow-type udp4 action 0 loc 32

UDP GSO硬件卸载
----------------

UDP GSO通过将UDP头分配卸载到硬件中来提高UDP发送速率。为此需要一个特殊的用户空间套接字选项，可以通过以下命令验证：

    udpgso_bench_tx -u -4 -D 10.0.1.1 -s 6300 -S 100

这将导致从单个6300字节的用户缓冲区中形成并发送100字节大小的UDP数据包。
UDP GSO 通过以下命令进行配置：

    ethtool -K eth0 tx-udp-segmentation on

私有标志（测试）
-----------------------

Atlantic 驱动支持用于硬件自定义特性的私有标志：

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
PHYInternalLoopback: 物理层内部环回
PHYExternalLoopback: 物理层外部环回（使用环回以太网线）

命令行参数
=======================

Atlantic 驾驶程序支持以下命令行参数：

aq_itr - 中断节流模式
---------------------------------
接受的值：0, 1, 0xFFFF

默认值：0xFFFF

======
0        禁用中断节流
1        启用中断节流并使用指定的发送和接收速率
0xFFFF   自动节流模式。驱动程序将根据链路速度选择最佳的接收和发送中断节流设置
======

aq_itr_tx - 发送侧中断节流速率
--------------------------------------

接受的值：0 - 0x1FF

默认值：0

发送侧每微秒的节流设置。适配器将设置最大中断延迟为该值。最小中断延迟将是这个值的一半。

aq_itr_rx - 接收侧中断节流速率
--------------------------------------

接受的值：0 - 0x1FF

默认值：0

接收侧每微秒的节流设置。适配器将设置最大中断延迟为该值。最小中断延迟将是这个值的一半。

.. 注意::
   
   ITR 设置可以在运行时通过 ethtool -c 进行更改（见下文）

配置文件参数
======================

为了进行一些微调和性能优化，
可以在 {source_dir}/aq_cfg.h 文件中更改一些参数
AQ_CFG_RX_PAGEORDER
-------------------

默认值：0

接收页顺序覆盖。这是为每个描述符分配的接收页数的 2 的幂次。接收到的描述符大小仍受限于 AQ_CFG_RX_FRAME_MAX。
增加页面排序可提高页面重用效果（在启用了iommu的系统上实际生效）

AQ_CFG_RX_REFILL_THRES
----------------------

默认值：32

接收（RX）填充阈值。在观察到指定数量的空闲描述符之前，接收路径不会重新填充已释放的描述符。较大的值可能有助于更好的页面重用，但也可能导致数据包丢失。

AQ_CFG_VECS_DEF
---------------

队列的数量

有效范围：0 - 8（最多为 AQ_CFG_VECS_MAX）

默认值：8

请注意，此值将受系统可用核心数量的限制。

AQ_CFG_IS_RSS_DEF
-----------------

启用/禁用接收端扩展

此功能允许适配器将接收处理分布在多个CPU核心上，并防止单个CPU核心过载。

有效值

==  ========
0   禁用
1   启用
==  ========

默认值：1

AQ_CFG_NUM_RSS_QUEUES_DEF
-------------------------

接收端扩展使用的队列数量

有效范围：0 - 8（最多为 AQ_CFG_VECS_DEF）

默认值：AQ_CFG_VECS_DEF

AQ_CFG_IS_LRO_DEF
-----------------

启用/禁用大型接收卸载

此卸载允许适配器合并多个TCP段并将其作为一个合并后的单元指示给操作系统网络子系统。
这样可以减少系统的能源消耗，但也会在处理数据包时引入更多的延迟。

有效值

==  ========
0   禁用
1   启用
==  ========

默认值：1

AQ_CFG_TX_CLEAN_BUDGET
----------------------

一次在发送（TX）方向上清理的最大描述符数

默认值：256

修改aq_cfg.h文件后，必须重新构建驱动程序才能生效。

支持
=======

如果在支持的内核上使用支持的适配器时发现发布源代码存在问题，请将与问题相关的信息发送至 aqn_support@marvell.com。

许可协议
=======

aQuantia Corporation 网络驱动程序

版权所有 © 2014 - 2019 aQuantia Corporation
本程序是自由软件；您可以根据自由软件基金会发布的GNU通用公共许可证的条款和条件进行分发或修改，版本为2。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
