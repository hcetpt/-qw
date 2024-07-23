SPDX 许可证标识符: GPL-2.0

=====================================================
网卡特性混乱及其生存之道
=====================================================

作者:
   Michał Mirosław <mirq-linux@rere.qmqm.pl>



第一部分：特性集
====================

那些网络卡仅仅负责原样接收和发送数据包的日子已经一去不复返了。如今的设备提供了多种特性（以及bug，可以理解为卸载任务）来减轻操作系统在生成和校验校验和、分割数据包、分类数据包等方面的负担。这些能力和它们的状态通常被称为Linux内核中的网卡特性。目前存在三种与驱动程序相关的特性集，以及一个由网络核心内部使用的特性集：

 1. `netdev->hw_features` 集合包含了用户请求下可能被更改（启用或禁用）的特定设备的特性。这个集合应该在 `ndo_init` 回调中初始化，并且之后不应该改变。
 2. `netdev->features` 集合包含了当前为设备启用的特性。这个集合只应该在网络核心或者 `ndo_set_features` 回调的错误路径中被修改。
 3. `netdev->vlan_features` 集合包含了子VLAN设备继承特性的状态（限制 `netdev->features` 集合）。这目前用于所有的VLAN设备，无论标签是在硬件还是软件中剥离或插入。
 4. `netdev->wanted_features` 集合包含了用户请求的特性集合。这个集合在 `ndo_fix_features` 回调中过滤，每当它或某些设备特定条件发生变化时。这个集合是网络核心内部的，不应在驱动程序中引用。

第二部分：控制已启用的特性
=====================================

当需要更改当前特性集 (`netdev->features`) 时，会计算新的特性集并通过调用 `ndo_fix_features` 回调和 `netdev_fix_features()` 来过滤。如果结果集与当前集不同，则将其传递给 `ndo_set_features` 回调，并（如果回调返回成功）替换存储在 `netdev->features` 中的值。在每次当前集可能发生改变后会发出 `NETDEV_FEAT_CHANGE` 通知。
以下事件会触发重新计算：
 1. 设备注册后，在 `ndo_init` 返回成功之后。
 2. 用户请求更改特性状态。
 3. 调用了 `netdev_update_features()`。

`ndo_*_features` 回调是在持有 `rtnl_lock` 的情况下调用的。缺少的回调被视为总是返回成功。
想要触发重新计算的驱动程序必须通过调用 `netdev_update_features()` 并持有 `rtnl_lock` 来实现。这不应该从 `ndo_*_features` 回调中完成。除了通过 `ndo_fix_features` 回调外，驱动程序不应该修改 `netdev->features`。
第三部分：实现提示
===============================

 * ndo_fix_features：

在此函数中，应解决所有特性之间的依赖关系。通过网络核心强加的限制（如在netdev_fix_features()中编码的那样），可以进一步减少最终的特性集。当特性的依赖条件未满足时，禁用该特性比强制依赖更安全。此回调不应修改硬件或驱动状态（应为无状态）。它可以在连续的ndo_set_features调用之间被多次调用。
回调不得更改包含在NETIF_F_SOFT_FEATURES或NETIF_F_NEVER_CHANGE集合中的特性。唯一的例外是NETIF_F_VLAN_CHALLENGED，但需要注意的是，变更不会影响已配置的VLAN。
* ndo_set_features：

硬件应根据传递的特性集进行重新配置。除非发生一些无法在ndo_fix_features中可靠检测的错误情况，否则不应改变该集。在这种情况下，回调应更新netdev->features以匹配硬件的实际状态。
返回的错误除了在dmesg中显示外，不会（也无法）传播到任何地方。（注：成功返回值为零，大于零表示静默错误。）

第四部分：特性
=================

要获取当前的特性列表，请参阅include/linux/netdev_features.h
本节描述了其中一些特性的语义
* 发送校验和

有关完整描述，请参阅include/linux/skbuff.h顶部附近的注释
注意：NETIF_F_HW_CSUM是NETIF_F_IP_CSUM和NETIF_F_IPV6_CSUM的超集。这意味着设备可以在数据包的任何位置填充TCP/UDP样式的校验和，无论存在什么头部。
* 传输TCP分段卸载

NETIF_F_TSO_ECN表示硬件能够正确地分割带有CWR位设置的数据包，无论是TCPv4（当启用NETIF_F_TSO时）还是TCPv6（NETIF_F_TSO6）
* 传输UDP分段卸载

NETIF_F_GSO_UDP_L4接受一个其有效载荷超过gso_size的单个UDP头。在分段时，它在gso_size边界上分割有效载荷，并复制网络和UDP头（如果小于gso_size，则修正最后一个头）
* 高内存中的传输DMA

在相关平台中，NETIF_F_HIGHDMA信号表明ndo_start_xmit可以处理高内存中的碎片skb
* 散集传输

以下特性表明ndo_start_xmit可以处理碎片化的skb：
NETIF_F_SG --- 分页skb（skb_shinfo()->frags），NETIF_F_FRAGLIST --- 链接skb（skb->next/prev列表）
* 软件特性

包含在NETIF_F_SOFT_FEATURES中的特性是网络堆栈的特性。驱动程序不应基于它们改变行为
* LLTX驱动程序（对于硬件驱动程序已弃用）

NETIF_F_LLTX旨在被完全不需要锁定的驱动程序使用，例如软件隧道
这也用于一些实现自己锁定的遗留驱动程序中，对于新的（硬件）驱动程序不要使用它
* 网络命名空间本地设备

对于不允许在网络命名空间之间移动的设备（例如环回设备），会设置NETIF_F_NETNS_LOCAL
在驱动程序中不要使用它
* VLAN受限

NETIF_F_VLAN_CHALLENGED应为那些无法处理VLAN头部的设备设置。某些驱动程序设置了这个标志，因为网卡无法处理更大的MTU（最大传输单元）。
[待修复：这些情况可能通过在VLAN代码中仅允许减少MTU的VLAN来解决。然而，这可能并不实用。]

* rx-fcs

此选项要求网络接口卡（NIC）将以太网帧校验和（FCS）附加到skb数据的末尾。这使得嗅探器和其他工具能够读取NIC在接收到数据包时记录的CRC值。

* rx-all

此选项要求NIC接收所有可能的数据帧，包括错误帧（如FCS错误等）。当需要在包含有问题数据包的链路上进行嗅探时，这会很有帮助。某些NIC如果同时置于常规的混杂模式下，可能会接收更多的数据包。

* rx-gro-hw

此选项要求NIC启用硬件GRO（通用接收卸载）。硬件GRO基本上是TSO的完全相反操作，并且通常比硬件LRO更为严格。由硬件GRO合并的包流必须能够通过GSO或TSO重新分段回原始的包流。硬件GRO依赖于RXCSUM，因为每个被硬件成功合并的包都必须由硬件验证其校验和。

* hsr-tag-ins-offload

对于自动插入HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备，应设置此选项。

* hsr-tag-rm-offload

对于自动移除HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备，应设置此选项。

* hsr-fwd-offload

对于在硬件级别从一个端口转发HSR（高可用无缝冗余）帧到另一个端口的设备，应设置此选项。

* hsr-dup-offload

对于在硬件级别自动复制外出的HSR（高可用无缝冗余）或PRP（并行冗余协议）标签帧的设备，应设置此选项。
