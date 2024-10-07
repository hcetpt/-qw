SPDX 许可证标识符: GPL-2.0

=================
以太网桥接
=================

介绍
============

IEEE 802.1Q-2022（桥接和桥接网络）标准定义了计算机网络中桥接设备的操作。在这个标准的上下文中，桥接设备是一种连接两个或多个网络段并在 OSI（开放系统互连）模型的数据链路层（第2层）操作的设备。桥接设备的主要功能是根据目标 MAC（媒体访问控制）地址过滤并转发不同段之间的帧。

桥接 kAPI
===========

以下是桥接代码的一些核心结构。请注意，kAPI 是 *不稳定的*，随时可能会发生变化。
.. kernel-doc:: net/bridge/br_private.h
   :identifiers: net_bridge_vlan

桥接 uAPI
===========

现代 Linux 桥接 uAPI 通过 Netlink 接口访问。下面列出了一些文件，其中定义了桥接和桥接端口的 Netlink 属性。
桥接 Netlink 属性
-------------------------

.. kernel-doc:: include/uapi/linux/if_link.h
   :doc: 桥接枚举定义

桥接端口 Netlink 属性
------------------------------

.. kernel-doc:: include/uapi/linux/if_link.h
   :doc: 桥接端口枚举定义

桥接 sysfs
------------

sysfs 接口已被弃用，如果添加新的选项不应再进行扩展。

STP
===

Linux 桥接驱动程序中的 STP（生成树协议）实现是一个关键特性，它有助于防止以太网网络中的环路和广播风暴，通过识别和禁用冗余链路来实现。在 Linux 桥接环境中，STP 对网络稳定性和可用性至关重要。

STP 是一个在 OSI 模型数据链路层（第2层）运行的协议。它最初由 IEEE 802.1D 开发，并已演变为多个版本，包括快速生成树协议（RSTP）和多生成树协议（MSTP）。
`Multiple Spanning Tree Protocol (MSTP)
<https://lore.kernel.org/netdev/20220316150857.2442916-1-tobias@waldekranz.com/>`_

2004 年发布的 802.1D 标准移除了原始的生成树协议，而是包含了快速生成树协议（RSTP）。到 2014 年，所有由 IEEE 802.1D 定义的功能已经被合并到 IEEE 802.1Q（桥接和桥接网络）或 IEEE 802.1AC（MAC 服务定义）中。802.1D 在 2022 年被正式废除。

桥接端口和 STP 状态
---------------------------

在 STP 的上下文中，桥接端口可以处于以下状态之一：
  * 阻塞：端口对数据流量禁用，仅监听来自其他设备的 BPDU（桥接协议数据单元）以确定网络拓扑。
  * 监听：端口开始参与 STP 过程并监听 BPDU。
  * 学习：端口继续监听 BPDU 并开始从传入帧中学习 MAC 地址，但不转发数据帧。
* 转发：端口完全运行正常，并转发BPDU和数据帧
* 禁用：端口被管理性禁用，不参与STP进程。数据帧的转发也被禁用

根桥与收敛
-------------

在Linux网络和以太网桥接的上下文中，根桥是在桥接网络中指定的一个交换机，作为生成树算法创建无环拓扑的参考点。

以下是STP的工作原理及根桥的选择过程：

1. 桥优先级：每个运行生成树协议的桥都有一个可配置的桥优先级值。数值越低，优先级越高。默认情况下，桥优先级设置为一个标准值（例如，32768）。
2. 桥ID：桥ID由两个部分组成：桥优先级和桥的MAC地址。它在网络中唯一标识每个桥。桥ID用于比较不同桥的优先级。
3. 桥选举：当网络启动时，所有桥最初都假设自己是根桥。它们开始向邻居发送桥协议数据单元（BPDU），包含其桥ID和其他信息。
4. BPDU比较：桥通过交换BPDU来确定根桥。每个桥检查收到的BPDU，包括桥优先级和桥ID，以确定是否需要调整自身的优先级。具有最低桥ID的桥将成为根桥。
5. 根桥通告：一旦确定了根桥，它将向网络中的其他所有桥发送包含根桥信息的BPDU。这些信息用于其他桥计算到根桥的最短路径，并因此创建一个无环拓扑。
6. 转发端口：在根桥被选定并建立生成树拓扑后，每个桥接器会确定其哪些端口应处于转发状态（用于数据流量），哪些端口应处于阻塞状态（用于防止环路）。根桥的所有端口都处于转发状态，而其他桥接器则有一些端口处于阻塞状态以避免环路。

7. 根端口：在根桥被选定并建立生成树拓扑后，每个非根桥处理接收到的 BPDU，并根据接收到的 BPDU 中的信息确定哪个端口到根桥的距离最短。这个端口被指定为根端口，并且处于转发状态，允许它积极地转发网络流量。

8. 指定端口：指定端口是非根桥通过该端口向指定网段转发流量的端口。指定端口被置于转发状态。非根桥上的所有其他未被指定用于特定网段的端口则被置于阻塞状态以防止网络环路。

STP（生成树协议）通过计算最短路径并禁用冗余链路来确保网络收敛。当网络拓扑发生变化（例如链路故障）时，STP 会重新计算网络拓扑以恢复连接同时避免环路。正确配置 STP 参数（如桥优先级）会影响网络性能、路径选择以及哪座桥成为根桥。

用户空间 STP 辅助程序
----------------------

用户空间 STP 辅助程序 `bridge-stp` 是一个用于控制是否使用用户模式生成树的程序。当在桥上启用或禁用 STP 时（通过 `brctl stp <bridge> <on|off>` 或 `ip link set <bridge> type bridge stp_state <0|1>`），内核会调用 `/sbin/bridge-stp <bridge> <start|stop>`。如果该命令返回 0，则内核启用用户 STP 模式；如果返回任何其他值，则启用内核 STP 模式。

VLAN
====

局域网（LAN）是一种覆盖小地理区域的网络，通常位于单个建筑物或校园内。LAN 用于将计算机、服务器、打印机和其他网络设备连接在一个局部区域内。LAN 可以是有线的（使用以太网电缆）或无线的（使用 Wi-Fi）。

虚拟局域网（VLAN）是对物理网络进行逻辑分割以形成多个隔离的广播域。VLAN 用于将单一物理局域网划分为多个虚拟局域网，使得不同组的设备可以像在独立的物理网络上一样进行通信。

常见的 VLAN 实现有两种：IEEE 802.1Q 和 IEEE 802.1ad（也称为 QinQ）。IEEE 802.1Q 是一种以太网网络中的 VLAN 标签标准。它允许网络管理员在物理网络上创建逻辑 VLAN 并对以太网帧添加 VLAN 信息，即 VLAN 标签帧。IEEE 802.1ad，通常称为 QinQ 或双重 VLAN，是 IEEE 802.1Q 标准的扩展。QinQ 允许在单个以太网帧中叠加多个 VLAN 标签。Linux 桥接器支持 IEEE 802.1Q 和 `IEEE 802.1AD <https://lore.kernel.org/netdev/1402401565-15423-1-git-send-email-makita.toshiaki@lab.ntt.co.jp/>`_ 协议的 VLAN 标签。

默认情况下，桥接器上的 VLAN 过滤功能是禁用的。启用桥接器上的 VLAN 过滤功能后，它将开始根据目标 MAC 地址和 VLAN 标签（两者都必须匹配）将帧转发到适当的目的地。
### 多播
#####

Linux 桥接驱动程序支持多播功能，允许其处理互联网组管理协议（IGMP）或多播监听发现（MLD）消息，并高效转发多播数据包。桥接驱动程序支持 IGMPv2/IGMPv3 和 MLDv1/MLDv2。

### 多播监听
####

多播监听是一种网络技术，允许网络交换机在局域网（LAN）中智能地管理多播流量。交换机维护一个多播组表，记录多播组地址与加入这些组的主机所在端口之间的关联。该组表根据收到的 IGMP/MLD 消息动态更新。通过多播监听收集到的多播组信息，交换机优化了多播流量的转发。它不会盲目地将多播流量广播到所有端口，而是仅根据目标 MAC 地址向订阅相应目标多播组的端口发送多播流量。

创建时，默认情况下 Linux 桥接设备启用了多播监听。它维护一个多播转发数据库（MDB），跟踪端口和组的关系。

### IGMPv3/MLDv2 EHT 支持
####

Linux 桥接驱动程序支持 IGMPv3/MLDv2 EHT（显式主机跟踪），该功能由 `474ddb37fa3a ("net: bridge: multicast: add EHT allow/block handling") <https://lore.kernel.org/netdev/20210120145203.1109140-1-razor@blackwall.org/>` 添加。

显式主机跟踪使设备能够跟踪加入特定组或频道的每个单独主机。显式主机跟踪的主要好处是允许主机离开多播组或频道时最小化离开延迟。从主机想要离开到设备停止转发流量之间的时间称为 IGMP 离开延迟。配置了 IGMPv3 或 MLDv2 并启用显式跟踪的设备可以在最后一个请求接收流量的主机表示不再希望接收流量时立即停止转发流量。因此，离开延迟仅受多路访问网络中的包传输延迟和设备处理时间限制。

### 其他多播功能
####

Linux 桥接还支持 `每 VLAN 多播监听 <https://lore.kernel.org/netdev/20210719170637.435541-1-razor@blackwall.org/>`_，默认情况下是禁用的，但可以启用。此外还支持 `多播路由器发现 <https://lore.kernel.org/netdev/20190121062628.2710-1-linus.luessing@c0d3.blue/>`_，帮助识别多播路由器的位置。

### Switchdev
####

Linux Bridge Switchdev 是 Linux 内核中的一个特性，扩展了传统 Linux 桥接的功能，使其能够更高效地与支持 Switchdev 的硬件交换机配合工作。使用 Linux Bridge Switchdev，某些网络功能如转发、过滤和学习以太网帧可以卸载到硬件交换机上。这种卸载减少了 Linux 内核和 CPU 的负担，从而提高了网络性能并降低了延迟。

要使用 Linux Bridge Switchdev，你需要支持 Switchdev 接口的硬件交换机。这意味着交换机硬件需要具有必要的驱动程序和功能，以便与 Linux 内核协同工作。

更多详细信息，请参阅 :ref:`switchdev` 文档。
### 网络过滤器（Netfilter）

桥接网过滤器模块是一个遗留功能，允许使用iptables和ip6tables对桥接的数据包进行过滤。不建议使用此模块。用户应考虑使用nftables进行数据包过滤。与nftables相比，较旧的ebtables工具功能更为有限，但同样不需要此模块即可正常工作。br_netfilter模块拦截进入桥接设备的数据包，对IPv4和IPv6数据包执行基本的合理性检查，然后假装这些数据包是被路由而不是桥接的。br_netfilter随后从桥接层调用ip和ipv6的netfilter钩子，即ip(6)tables规则集也会看到这些数据包。

br_netfilter也是iptables *physdev*匹配的原因：这个匹配是iptables规则集中可靠地区分路由和桥接数据包的唯一方式。

请注意，ebtables和nftables在没有br_netfilter模块的情况下也能正常工作。iptables/ip6tables/arptables对于桥接流量不起作用，因为它们插在路由栈中。nftables规则在ip/ip6/inet/arp家族中也不会看到由桥接转发的流量，但这正是应该如此的情况。

历史上，ebtables的功能非常有限（现在依然如此），此模块是为了假装数据包被路由并调用ipv4/ipv6的netfilter钩子，从而使用户可以访问功能更丰富的iptables匹配能力（包括conntrack）。nftables没有这种限制，几乎所有功能都与协议族无关。

因此，只有当用户出于某种原因需要使用ip(6)tables来过滤由桥接转发的数据包或NAT桥接流量时，才需要br_netfilter模块。对于纯粹的链路层过滤，此模块不是必需的。

### 其他功能

Linux桥接还支持以下功能：
- `IEEE 802.11 Proxy ARP <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=958501163ddd6ea22a98f94fa0e7ce6d4734e5c4>`
- `媒体冗余协议 (MRP) <https://lore.kernel.org/netdev/20200426132208.3232-1-horatiu.vultur@microchip.com/>`
- `媒体冗余协议 (MRP) LC 模式 <https://lore.kernel.org/r/20201124082525.273820-1-horatiu.vultur@microchip.com>`
- `IEEE 802.1X 端口认证 <https://lore.kernel.org/netdev/20220218155148.2329797-1-schultz.hans+netdev@gmail.com/>`
- `MAC 认证绕过 (MAB) <https://lore.kernel.org/netdev/20221101193922.2125323-2-idosch@nvidia.com/>`

### 常见问题解答

桥接设备的作用是什么？
----------------------

桥接设备透明地在多个网络接口之间转发流量。
用简单的英语来说，这意味着一座桥连接了两个或多个物理以太网网络，从而形成一个更大的（逻辑上的）以太网网络。

它是与L3协议无关的吗？
------------------------------

是的。桥接器能看到所有帧，但它只使用第2层（L2）头部/信息。因此，桥接功能是与协议无关的，并且转发IPX、NetBEUI、IP、IPv6等时不应有任何问题。

联系方式
============

当前代码由Roopa Prabhu（roopa@nvidia.com）和Nikolay Aleksandrov（razor@blackwall.org）维护。关于桥接的错误和改进讨论可以在linux-netdev邮件列表上进行：netdev@vger.kernel.org 和 bridge@lists.linux.dev
该邮件列表对任何感兴趣的人开放：http://vger.kernel.org/vger-lists.html#netdev

外部链接
============

Linux桥接的旧文档位于：
https://wiki.linuxfoundation.org/networking/bridge
