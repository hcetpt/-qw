SPDX 许可证标识符: GPL-2.0

=====================================================
网卡特性混乱及其生存之道
=====================================================

作者:
 Michał Mirosław <mirq-linux@rere.qmqm.pl>

第一部分：特性集
====================

那些只需要接收和发送数据包的时代早已过去。如今的设备添加了多种特性和漏洞（即：卸载），这些特性可以减轻操作系统在生成和校验校验和、分割数据包以及分类数据包等方面的负担。在 Linux 内核领域，这些能力和它们的状态通常被称为 netdev 特性。目前有三个与驱动程序相关的特性集，还有一个由网络核心内部使用的特性集：

1. `netdev->hw_features` 集合包含用户请求下可能被改变状态（启用或禁用）的特性。这个集合应该在 `ndo_init` 回调中初始化，并且之后不再更改。
2. `netdev->features` 集合包含当前为设备启用的特性。这个集合只应由网络核心或在 `ndo_set_features` 回调中的错误路径中更改。
3. `netdev->vlan_features` 集合包含子 VLAN 设备继承状态的特性（限制 `netdev->features` 集合）。目前它用于所有VLAN设备，无论标签是在硬件还是软件中剥离或插入。
4. `netdev->wanted_features` 集合包含用户请求的特性集合。这个集合在 `ndo_fix_features` 回调中过滤，每当它或某些设备特定条件发生变化时。这个集合是网络核心内部使用的，不应在驱动程序中引用。

第二部分：控制已启用的特性
=====================================

当需要更改当前特性集(`netdev->features`)时，将计算新的集合并通过调用 `ndo_fix_features` 回调和 `netdev_fix_features()` 来过滤。如果结果集合与当前集合不同，则将其传递给 `ndo_set_features` 回调函数（如果回调返回成功），并替换存储在 `netdev->features` 中的值。之后会发出 `NETDEV_FEAT_CHANGE` 通知，只要当前集合可能发生了变化。
以下事件会触发重新计算：
1. 设备注册后，`ndo_init` 返回成功
2. 用户请求更改特性状态
3. 调用了 `netdev_update_features()` 

`ndo_*_features` 回调是在持有 `rtnl_lock` 的情况下调用的。缺少的回调被视为总是返回成功。
想要触发重新计算的驱动程序必须通过在持有 `rtnl_lock` 的情况下调用 `netdev_update_features()` 来实现。这不应在 `ndo_*_features` 回调中完成。除了通过 `ndo_fix_features` 回调之外，驱动程序不应修改 `netdev->features`。
### 第三部分：实现提示
==============================

 * `ndo_fix_features`：

在此函数中应解决所有特性之间的依赖关系。通过网络核心强加的限制（如在`netdev_fix_features()`中编码的），可以进一步减少结果集。当某个特性的依赖关系未满足时，更安全的做法是禁用该特性而不是强制依赖。此回调不应修改硬件或驱动程序的状态（应保持无状态）。它可能在连续的`ndo_set_features`调用之间被多次调用。
此回调不得更改包含在`NETIF_F_SOFT_FEATURES`或`NETIF_F_NEVER_CHANGE`集合中的特性。唯一例外是`NETIF_F_VLAN_CHALLENGED`，但需要注意的是，这种更改不会影响已配置的VLAN。

 * `ndo_set_features`：

硬件应重新配置以匹配传递的特性集。除非发生无法在`ndo_fix_features`中可靠检测到的错误条件，否则不应更改特性集。在这种情况下，回调应更新`netdev->features`以匹配实际的硬件状态。
返回的错误不会（也不能）传播到任何地方，除了dmesg。
注意：成功返回值为零，大于零表示静默错误。

### 第四部分：特性
=================

当前特性列表请参见`include/linux/netdev_features.h`
本节描述了其中一些特性的语义。
* 发送校验和

详细描述请参见`include/linux/skbuff.h`顶部的注释。
注意：`NETIF_F_HW_CSUM`是`NETIF_F_IP_CSUM`和`NETIF_F_IPV6_CSUM`的超集。这意味着设备可以在包内的任意位置填充TCP/UDP样式的校验和，无论包头如何。
* 传输TCP分段卸载

NETIF_F_TSO_ECN 表示硬件能够正确地分割带有 CWR 标志位的数据包，无论是针对 TCPv4（当启用 NETIF_F_TSO 时）还是 TCPv6（NETIF_F_TSO6）。

* 传输UDP分段卸载

NETIF_F_GSO_UDP_L4 接受一个带有超过 gso_size 的负载的单个 UDP 首部。在分段过程中，它会在 gso_size 边界处分割负载，并复制网络和 UDP 首部（如果小于 gso_size，则修正最后一个首部）。

* 从高端内存进行传输DMA

在相关的平台上，NETIF_F_HIGHDMA 表示 ndo_start_xmit 可以处理位于高端内存中的 skb 分片。

* 传输散集

以下特性表示 ndo_start_xmit 可以处理分片的 skb：
NETIF_F_SG —— 分页的 skb（skb_shinfo()->frags），NETIF_F_FRAGLIST —— 链接的 skb（skb->next/prev 列表）。

* 软件特性

包含在 NETIF_F_SOFT_FEATURES 中的特性是网络堆栈的特性。驱动程序不应根据这些特性改变行为。

* LLTX 驱动程序（硬件驱动程序已弃用）

NETIF_F_LLTX 适用于那些完全不需要锁定的驱动程序，例如软件隧道。
这也用于一些实现了自己的锁定机制的老式驱动程序中，对于新的（硬件）驱动程序不要使用此特性。

* 局域网命名空间本地设备

对于不允许在网络命名空间之间移动的设备（例如回环设备），会设置 NETIF_F_NETNS_LOCAL。
在驱动程序中不要使用此特性。

* 不支持VLAN

对于无法处理 VLAN 头部的设备，应设置 NETIF_F_VLAN_CHALLENGED。某些驱动程序设置此标志是因为其网卡无法处理更大的 MTU。
[待修复：这些情况可以通过在VLAN代码中只允许减小MTU的VLAN来解决。不过这可能并不实用。]

*  rx-fcs

此选项要求网卡（NIC）在skb数据末尾附加以太网帧校验和（FCS）。这样可以让嗅探器和其他工具读取网卡在接收数据包时记录的CRC值。
*  rx-all

此选项要求网卡接收所有可能的数据帧，包括有错误的数据帧（例如错误的FCS等）。当需要嗅探一个存在坏包的链路时，这可能会有所帮助。某些网卡如果同时设置为普通混杂模式（PROMISC模式），可能会接收到更多的数据包。
*  rx-gro-hw

此选项要求网卡启用硬件GRO（通用接收卸载）。硬件GRO基本上是TSO的反向操作，并且通常比硬件LRO更为严格。通过硬件GRO合并的包流必须能够通过GSO或TSO重新分段为原始的包流。硬件GRO依赖于RXCSUM，因为每个被硬件成功合并的包都必须由硬件验证其校验和。
* hsr-tag-ins-offload

此选项应设置为自动插入HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备。
* hsr-tag-rm-offload

此选项应设置为自动移除HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备。
* hsr-fwd-offload

此选项应设置为能够在硬件中从一个端口转发到另一个端口的HSR（高可用无缝冗余）帧的设备。
* hsr-dup-offload

此选项应设置为自动在硬件中复制出站HSR（高可用无缝冗余）或PRP（并行冗余协议）标签帧的设备。
