SPDX 许可证标识符: GPL-2.0

=====================================================
网卡特性混乱及其生存之道
=====================================================

作者:
 Michał Mirosław <mirq-linux@rere.qmqm.pl>

---

第一部分：特性集
====================

那些网络卡仅仅负责原样接收和发送数据包的日子已经一去不复返了。如今的设备提供了多种特性（以及bug，可以理解为卸载任务）来减轻操作系统在生成和校验校验和、分割数据包、分类数据包等方面的负担。这些能力和它们的状态通常被称为Linux内核中的网卡特性。目前存在三种与驱动程序相关的特性集，以及一个由网络核心内部使用的特性集：

 1. `netdev->hw_features` 集合包含了用户请求下可能被更改（启用或禁用）的特定设备的特性。这个集合应该在 `ndo_init` 回调中初始化，并且之后不应该改变。
 2. `netdev->features` 集合包含了当前为设备启用的特性。这个集合只应由网络核心或者在 `ndo_set_features` 回调的错误路径中更改。
 3. `netdev->vlan_features` 集合包含了子VLAN设备继承特性的状态（限制 `netdev->features` 集合）。这目前用于所有的VLAN设备，无论是在硬件还是软件中剥离或插入标签。
 4. `netdev->wanted_features` 集合包含了用户请求的特性集。当这个集合或某些设备特定条件发生变化时，它将通过 `ndo_fix_features` 回调进行过滤。这个集合是网络核心内部的，不应在驱动程序中引用。

第二部分：控制已启用特性
=====================================

当需要更改当前特性集(`netdev->features`)时，会计算新的特性集并通过调用 `ndo_fix_features` 回调和 `netdev_fix_features()` 来过滤。如果结果集与当前集不同，则将其传递给 `ndo_set_features` 回调，并（如果回调返回成功）替换存储在 `netdev->features` 中的值。在每次当前集可能发生改变后会发出 `NETDEV_FEAT_CHANGE` 通知。

以下事件会触发重新计算：
 1. 设备注册后，在 `ndo_init` 返回成功之后。
 2. 用户请求更改特性状态。
 3. 调用了 `netdev_update_features()`。

`ndo_*_features` 回调是在持有 `rtnl_lock` 的情况下调用的。缺少的回调被视为始终返回成功。

想要触发重新计算的驱动程序必须通过调用 `netdev_update_features()` 并持有 `rtnl_lock` 来实现。这不应该从 `ndo_*_features` 回调中完成。除了通过 `ndo_fix_features` 回调外，驱动程序不应该修改 `netdev->features`。
### 第三部分：实现提示
==============================

 * `ndo_fix_features`:

在此函数中应解决所有特性之间的依赖关系。通过网络核心施加的限制（如在`netdev_fix_features()`中编码的那样），可以进一步减少生成的特性集。当某一特性的依赖条件未满足时，更安全的做法是禁用该特性，而不是强制执行依赖。此回调函数不应修改硬件或驱动程序的状态（应保持无状态）。它可以在连续的`ndo_set_features`调用之间被多次调用。
此回调不得更改包含在`NETIF_F_SOFT_FEATURES`或`NETIF_F_NEVER_CHANGE`集合中的特性。唯一例外是`NETIF_F_VLAN_CHALLENGED`，但需要注意的是，这种更改不会影响已配置的VLAN。
* `ndo_set_features`:

硬件应根据传递的特性集进行重新配置。除非发生无法在`ndo_fix_features`中可靠检测到的错误情况，否则不应更改特性集。在这种情况下，回调函数应更新`netdev->features`以匹配硬件的实际状态。
返回的错误不会（也无法）传播到任何地方，除了`dmesg`。
（注：成功返回值为0，大于0表示静默错误。）

### 第四部分：特性
=================

当前的特性列表，请参见`include/linux/netdev_features.h`
本节描述了其中一些特性的语义
* 发送校验和

对于完整的描述，请参阅`include/linux/skbuff.h`顶部附近的注释。
注意：`NETIF_F_HW_CSUM`是`NETIF_F_IP_CSUM`和`NETIF_F_IPV6_CSUM`的超集。这意味着设备可以在包内的任何位置填充TCP/UDP样式的校验和，无论存在何种头部信息。
* 传输TCP分段卸载

NETIF_F_TSO_ECN 表示硬件能够正确地对带有CWR位的数据包进行拆分，无论是TCPv4（当启用NETIF_F_TSO时）还是TCPv6（NETIF_F_TSO6）
* 传输UDP分段卸载

NETIF_F_GSO_UDP_L4 接受一个负载超过gso_size的单个UDP报头。在分段时，它会在gso_size边界处分割负载，并复制网络和UDP报头（如果小于gso_size，则修复最后一个报头）
* 从高端内存进行传输DMA

在相关平台中，NETIF_F_HIGHDMA 表示 ndo_start_xmit 能够处理位于高端内存中的碎片（skbs）
* 传输散聚操作

以下特性表示 ndo_start_xmit 能够处理分片的skbs：
NETIF_F_SG —— 分页的skbs（skb_shinfo()->frags），NETIF_F_FRAGLIST —— 链接的skbs（skb->next/prev列表）
* 软件特性

包含在NETIF_F_SOFT_FEATURES中的特性是网络堆栈的特性。驱动程序不应根据这些特性改变行为
* LLTX驱动（对于硬件驱动已废弃）

NETIF_F_LLTX 旨在用于那些完全不需要加锁的驱动程序，例如软件隧道。
这也被一些遗留驱动程序使用，它们实现了自己的锁定机制；对于新的（硬件）驱动程序，请不要使用此特性
* 网络命名空间本地设备

对于不允许在网络命名空间之间移动的设备（例如回环设备），会设置 NETIF_F_NETNS_LOCAL
请勿在驱动程序中使用此特性
* 不支持VLAN的设备

对于无法处理VLAN报头的设备，应设置 NETIF_F_VLAN_CHALLENGED。某些驱动程序设置了这个标志，因为其网卡无法处理更大的MTU（最大传输单元）
[待修复：这些问题可以通过在VLAN代码中仅允许使用减小了MTU（最大传输单元）的VLAN来解决。然而这可能并不实用。]

*  rx-fcs

此选项要求网卡（NIC）将以太网帧校验和（FCS）附加到skb数据的末尾。这样可以让嗅探器和其他工具读取网卡接收到数据包时记录的CRC值。

*  rx-all

此选项要求网卡接收所有可能的数据帧，包括错误帧（例如FCS错误等）。当需要嗅探包含有问题数据包的链路时，这会很有帮助。某些网卡如果同时设置为普通混杂模式（PROMISC），可能会接收更多的数据包。

*  rx-gro-hw

此选项要求网卡启用硬件GRO（通用接收卸载）。硬件GRO基本上是TSO的反向操作，并且通常比硬件LRO更严格。通过硬件GRO合并的报文流必须能够通过GSO或TSO重新分段回原始的报文流。硬件GRO依赖于RXCSUM，因为每个被硬件成功合并的包也必须由硬件验证其校验和。

* hsr-tag-ins-offload

此选项应为自动插入HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备设置。

* hsr-tag-rm-offload

此选项应为自动移除HSR（高可用无缝冗余）或PRP（并行冗余协议）标签的设备设置。

* hsr-fwd-offload

此选项应为在硬件层面上从一个端口向另一个端口转发HSR（高可用无缝冗余）帧的设备设置。

* hsr-dup-offload

此选项应为在硬件层面上自动复制出站HSR（高可用无缝冗余）或PRP（并行冗余协议）帧的设备设置。
