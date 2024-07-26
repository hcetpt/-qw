### SPDX 许可证标识符: GPL-2.0

#### Devlink Trap

##### 背景

能够卸载内核数据路径并执行诸如桥接和路由等功能的设备还必须能够将特定的数据包发送到内核（即，CPU）进行处理。例如，作为多播感知桥接器运行的设备必须能够将IGMP成员报告发送到内核以供桥接模块处理；如果不处理这些数据包，桥接模块将无法填充其多播数据桥接表（MDB）。另一个例子是作为路由器运行的设备接收到一个TTL为1的IP数据包，在对数据包进行路由后，该设备必须将其发送给内核以便它也能进行路由并生成ICMP时间超过错误数据报。如果不允许内核自己路由这类数据包，像`traceroute`这样的工具将无法工作。

发送某些数据包到内核进行处理的基本能力被称为“数据包捕获”。

##### 概览

`devlink-trap`机制允许有能力的设备驱动程序向`devlink`注册它们支持的数据包捕获，并向`devlink`报告被捕获的数据包以进行进一步分析。当接收到被捕获的数据包时，`devlink`会对每个捕获的数据包进行计数和字节统计，并可能通过netlink事件将数据包及其提供的所有元数据（如捕获原因、时间戳、输入端口等）报告给用户空间。这对于丢弃捕获（参见“捕获类型”）特别有用，因为它可以让用户获得原本不可见的数据包丢弃的更多信息。

下图提供了一个关于`devlink-trap`的大致概述：

```
                                   Netlink事件：带有元数据的数据包
                                                   或最近丢弃的汇总
                                  ^
                                  |
          用户空间                |
         +---------------------------------------------------+
          内核                    |
                                  |
                          +-------+--------+
                          |                |
                          | 丢弃监控器     |
                          |                |
                          +-------^--------+
                                  |
                                  | 非控制捕获
                                  |
                             +----+----+
                             |         |      内核的接收路径
                             | devlink |      （非丢弃捕获）
                             |         |
                             +----^----+      ^
                                  |           |
                                  +-----------+
                                  |
                          +-------+-------+
                          |               |
                          | 设备驱动程序 |
                          |               |
                          +-------^-------+
          内核                    |
         +---------------------------------------------------+
          硬件                    |
                                  | 被捕获的数据包
                                  |
                               +--+---+
                               |      |
                               | ASIC |
                               |      |
                               +------+
```

##### 捕获类型

`devlink-trap`机制支持以下几种数据包捕获类型：

- `丢弃`：被底层设备丢弃的数据包。这些数据包仅由`devlink`处理，不会注入到内核的接收路径中。可以更改捕获动作（参见“捕获动作”）。
- `异常`：由于异常情况（如TTL错误、缺少邻居条目等），底层设备没有按照预期转发数据包，并将其捕获到控制平面以解决。这些数据包由`devlink`处理并注入到内核的接收路径中。不允许更改此类捕获的动作，因为这可能会轻易破坏控制平面。
* ``control``: 被捕获的数据包被设备捕获，因为这些是控制平面正常运作所需的控制数据包。例如，ARP 请求和 IGMP 查询数据包。这些数据包被注入到内核的接收路径中，但不会报告给内核的丢弃监控器。不允许更改此类捕获的动作，因为它很容易破坏控制平面。
  
.. _Trap-Actions:

捕获动作
============

``devlink-trap`` 机制支持以下数据包捕获动作：

  * ``trap``: 数据包的唯一副本被发送到 CPU。
  * ``drop``: 数据包由底层设备丢弃，并且不将副本发送到 CPU。
  * ``mirror``: 数据包由底层设备转发，并将副本发送到 CPU。
通用数据包捕获
==================

通用数据包捕获用于描述那些捕获定义明确的数据包或因定义明确的条件（如 TTL 错误）而被捕获的数据包。这类捕获可以被多个设备驱动共享，并且其描述必须添加到下表中：

.. list-table:: 通用数据包捕获列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``source_mac_is_multicast``
     - ``drop``
     - 捕获设备决定丢弃的具有多播源 MAC 的传入数据包。
   * - ``vlan_tag_mismatch``
     - ``drop``
     - 捕获设备决定丢弃的 VLAN 标签不匹配的传入数据包：入端口未配置 PVID，而数据包未标记或仅标记优先级。
   * - ``ingress_vlan_filter``
     - ``drop``
     - 捕获设备决定丢弃的带有未在入端口上配置的 VLAN 标签的传入数据包。
   * - ``ingress_spanning_tree_filter``
     - ``drop``
     - 捕获设备决定丢弃的入端口 STP 状态不是“转发”的传入数据包。
   * - ``port_list_is_empty``
     - ``drop``
     - 捕获设备决定丢弃的需要泛洪（例如，未知单播、未注册多播）但没有可泛洪端口的数据包。
   * - ``port_loopback_filter``
     - ``drop``
     - 捕获设备决定丢弃的经过二层转发后，唯一应该传输的端口即为接收该数据包的端口的数据包。
   * - ``blackhole_route``
     - ``drop``
     - 捕获设备决定丢弃的命中黑洞路由的数据包。
   * - ``ttl_value_is_too_small``
     - ``exception``
     - 捕获设备应转发但 TTL 减至 0 或更低的单播数据包。
   * - ``tail_drop``
     - ``drop``
     - 捕获设备决定丢弃的无法加入已满的传输队列的数据包。
   * - ``non_ip``
     - ``drop``
     - 捕获设备决定丢弃的需进行三层查找但非 IP 或 MPLS 数据包。
   * - ``uc_dip_over_mc_dmac``
     - ``drop``
     - 捕获设备决定丢弃的需路由且具有单播目标 IP 和多播目标 MAC 的数据包。
   * - ``dip_is_loopback_address``
     - ``drop``
     - 捕获设备决定丢弃的需路由且目标 IP 是回环地址（即，127.0.0.0/8 和 ::1/128）的数据包。
   * - ``sip_is_mc``
     - ``drop``
     - 捕获设备决定丢弃的需路由且源 IP 是多播（即，224.0.0.0/8 和 ff::/8）的数据包。
   * - ``sip_is_loopback_address``
     - ``drop``
     - 捕获设备决定丢弃的需路由且源 IP 是回环地址（即，127.0.0.0/8 和 ::1/128）的数据包。
   * - ``ip_header_corrupted``
     - ``drop``
     - 捕获设备决定丢弃的需路由且 IP 头被破坏（如错误校验和、错误 IP 版本或过短的互联网头部长度 IHL）的数据包。
   * - ``ipv4_sip_is_limited_bc``
     - ``drop``
     - 捕获设备决定丢弃的需路由且源 IP 是有限广播（即，255.255.255.255/32）的数据包。
   * - ``ipv6_mc_dip_reserved_scope``
     - ``drop``
     - 捕获设备决定丢弃的需路由且 IPv6 多播目标 IP 具有保留作用域（即，ffx0::/16）的 IPv6 数据包。
   * - ``ipv6_mc_dip_interface_local_scope``
     - ``drop``
     - 捕获设备决定丢弃的需路由且 IPv6 多播目标 IP 具有接口本地作用域（即，ffx1::/16）的 IPv6 数据包。
   * - ``mtu_value_is_too_small``
     - ``exception``
     - 捕获应由设备路由但大于出口接口 MTU 的数据包。
   * - ``unresolved_neigh``
     - ``exception``
     - 捕获路由后未找到匹配 IP 邻居的数据包。
   * - ``mc_reverse_path_forwarding``
     - ``exception``
     - 捕获多播路由过程中未能通过反向路径转发（RPF）检查的多播 IP 数据包。
   * - ``reject_route``
     - ``exception``
     - 捕获命中拒绝路由（即，“不可达”，“禁止”）的数据包。
   * - ``ipv4_lpm_miss``
     - ``exception``
     - 捕获未匹配任何路由的单播 IPv4 数据包。
   * - ``ipv6_lpm_miss``
     - ``exception``
     - 捕获未匹配任何路由的单播 IPv6 数据包。
   * - ``non_routable_packet``
     - ``drop``
     - 捕获设备决定丢弃的不应被路由的数据包。例如，IGMP 查询可以由设备在第二层泛洪并到达路由器。这样的数据包不应该被路由，而是被丢弃。
   * - ``decap_error``
     - ``exception``
     - 捕获设备决定丢弃的因解封装失败（如数据包太短，VXLAN 头部中的保留位设置等）的 NVE 和 IPinIP 数据包。
   * - ``overlay_smac_is_mc``
     - ``drop``
     - 捕获设备决定丢弃的覆盖层源 MAC 是多播的 NVE 数据包。
   * - ``ingress_flow_action_drop``
     - ``drop``
     - 捕获处理入端流动作丢弃时丢弃的数据包。
   * - ``egress_flow_action_drop``
     - ``drop``
     - 捕获处理出端流动作丢弃时丢弃的数据包。
   * - ``stp``
     - ``control``
     - 捕获 STP 数据包。
   * - ``lacp``
     - ``control``
     - 捕获 LACP 数据包。
   * - ``lldp``
     - ``control``
     - 捕获 LLDP 数据包。
   * - ``igmp_query``
     - ``control``
     - 捕获 IGMP 成员查询数据包。
   * - ``igmp_v1_report``
     - ``control``
     - 捕获 IGMP 第 1 版成员报告数据包。
   * - ``igmp_v2_report``
     - ``control``
     - 捕获 IGMP 第 2 版成员报告数据包。
   * - ``igmp_v3_report``
     - ``control``
     - 捕获 IGMP 第 3 版成员报告数据包。
   * - ``igmp_v2_leave``
     - ``control``
     - 捕获 IGMP 第 2 版离开组数据包。
   * - ``mld_query``
     - ``control``
     - 捕获 MLD 多播监听查询数据包。
   * - ``mld_v1_report``
     - ``control``
     - 捕获 MLD 第 1 版多播监听报告数据包。
   * - ``mld_v2_report``
     - ``control``
     - 捕获 MLD 第 2 版多播监听报告数据包。
   * - ``mld_v1_done``
     - ``control``
     - 捕获 MLD 第 1 版多播监听完成数据包。
   * - ``ipv4_dhcp``
     - ``control``
     - 捕获 IPv4 DHCP 数据包。
   * - ``ipv6_dhcp``
     - ``control``
     - 捕获 IPv6 DHCP 数据包。
   * - ``arp_request``
     - ``control``
     - 捕获 ARP 请求数据包。
   * - ``arp_response``
     - ``control``
     - 捕获 ARP 响应数据包。
   * - ``arp_overlay``
     - ``control``
     - 捕获达到覆盖网络的 NVE 解封装后的 ARP 数据包。这在需要解析的地址是一个本地地址的情况下是必需的。
   * - ``ipv6_neigh_solicit``
     - ``control``
     - 捕获 IPv6 邻居请求数据包。
   * - ``ipv6_neigh_advert``
     - ``control``
     - 捕获 IPv6 邻居通告数据包。
   * - ``ipv4_bfd``
     - ``control``
     - 捕获 IPv4 BFD 数据包。
   * - ``ipv6_bfd``
     - ``control``
     - 捕获 IPv6 BFD 数据包。
   * - ``ipv4_ospf``
     - ``control``
     - 捕获 IPv4 OSPF 数据包。
   * - ``ipv6_ospf``
     - ``control``
     - 捕获 IPv6 OSPF 数据包。
   * - ``ipv4_bgp``
     - ``control``
     - 捕获 IPv4 BGP 数据包。
   * - ``ipv6_bgp``
     - ``control``
     - 捕获 IPv6 BGP 数据包。
   * - ``ipv4_vrrp``
     - ``control``
     - 捕获 IPv4 VRRP 数据包。
   * - ``ipv6_vrrp``
     - ``control``
     - 捕获 IPv6 VRRP 数据包。
   * - ``ipv4_pim``
     - ``control``
     - 捕获 IPv4 PIM 数据包。
   * - ``ipv6_pim``
     - ``control``
     - 捕获 IPv6 PIM 数据包。
   * - ``uc_loopback``
     - ``control``
     - 捕获需通过同一三层接口路由并从该接口收到的单播数据包。这类数据包由内核路由，但也可能生成 ICMP 重定向数据包。
   * - ``local_route``
     - ``control``
     - 捕获命中本地路由并需本地传送的单播数据包。
   * - ``external_route``
     - ``control``
     - 捕获需通过不属于同一设备（如交换 ASIC）的外部接口（如管理接口）路由的数据包。
   * - ``ipv6_uc_dip_link_local_scope``
     - ``control``
     - 捕获需路由且目标 IP 地址具有链路本地作用域（即，fe80::/10）的单播 IPv6 数据包。此捕获允许设备驱动避免编程链路本地路由，但仍接收本地传送的数据包。
   * - ``ipv6_dip_all_nodes``
     - ``control``
     - 捕获目标 IP 地址为“所有节点地址”（即，ff02::1）的 IPv6 数据包。
   * - ``ipv6_dip_all_routers``
     - ``control``
     - 捕获目标 IP 地址为“所有路由器地址”（即，ff02::2）的 IPv6 数据包。
   * - ``ipv6_router_solicit``
     - ``control``
     - 捕获 IPv6 路由请求数据包。
   * - ``ipv6_router_advert``
     - ``control``
     - 捕获 IPv6 路由通告数据包。
   * - ``ipv6_redirect``
     - ``control``
     - 捕获 IPv6 重定向消息数据包。
   * - ``ipv4_router_alert``
     - ``control``
     - 捕获需路由且包含路由器警报选项的 IPv4 数据包。这类数据包需本地传送到设置了 IP_ROUTER_ALERT 套接字选项的原始套接字。
   * - ``ipv6_router_alert``
     - ``control``
     - 捕获需路由且在其逐跳扩展头中包含路由器警报选项的 IPv6 数据包。这类数据包需本地传送到设置了 IPV6_ROUTER_ALERT 套接字选项的原始套接字。
   * - ``ptp_event``
     - ``control``
     - 捕获 PTP 时间关键事件消息（Sync, Delay_req, Pdelay_Req 和 Pdelay_Resp）。
   * - ``ptp_general``
     - ``control``
     - 捕获 PTP 一般消息（Announce, Follow_Up, Delay_Resp, Pdelay_Resp_Follow_Up, 管理和信号）。
   * - ``flow_action_sample``
     - ``control``
     - 捕获在处理流动作采样（例如，通过 tc 的采样动作）时采样的数据包。
   * - ``flow_action_trap``
     - ``control``
     - 捕获在处理流动作捕获（例如，通过 tc 的捕获动作）时记录的数据包。
   * - ``early_drop``
     - ``drop``
     - 捕获因随机早期检测（RED）算法而导致的早期丢弃的数据包。
   * - ``vxlan_parsing``
     - ``drop``
     - 捕获因 VXLAN 头解析错误而丢弃的数据包，可能是由于数据包截断或 I 标志未设置等原因。
   * - ``llc_snap_parsing``
     - ``drop``
     - 捕获因 LLC+SNAP 头解析错误而丢弃的数据包。
   * - ``vlan_parsing``
     - ``drop``
     - 捕获因 VLAN 头解析错误而丢弃的数据包。可能包括意外的数据包截断。
* - ``pppoe_ppp_parsing``
     - ``drop``
     - 捕获因PPPoE+PPP头部解析错误而丢弃的数据包
这可能包括发现会话ID为0xFFFF（这是预留的，不可使用）、PPPoE长度大于接收到的帧或此类型头部的任何常见错误
   * - ``mpls_parsing``
     - ``drop``
     - 捕获因MPLS头部解析错误而丢弃的数据包
这可能包括意外的头部截断
   * - ``arp_parsing``
     - ``drop``
     - 捕获因ARP头部解析错误而丢弃的数据包
   * - ``ip_1_parsing``
     - ``drop``
     - 捕获因第一个IP头部解析错误而丢弃的数据包
这个数据包捕获可能包括未通过IP校验和检查、头部长度检查（至少20字节）的数据包，这些数据包可能因截断导致总长度字段超过了接收到的数据包长度等
   * - ``ip_n_parsing``
     - ``drop``
     - 捕获因最后一个IP头部（在IP over IP隧道情况下为内部头部）解析错误而丢弃的数据包
这里执行与ip_1_parsing捕获相同的常见错误检查
   * - ``gre_parsing``
     - ``drop``
     - 捕获因GRE头部解析错误而丢弃的数据包
   * - ``udp_parsing``
     - ``drop``
     - 捕获因UDP头部解析错误而丢弃的数据包
这个数据包捕获可能包括校验和错误、不正确的UDP长度（小于8字节）或头部截断检测
* - ``tcp_parsing``
     - ``drop``
     - 捕获因TCP头部解析错误而丢弃的数据包
这可能包括TCP校验和错误、SYN、FIN和/或重置标志的不当组合等
* - ``ipsec_parsing``
     - ``drop``
     - 捕获因IPSEC头部解析错误而丢弃的数据包
   * - ``sctp_parsing``
     - ``drop``
     - 捕获因SCTP头部解析错误而丢弃的数据包
这意味着使用了端口号0或头部被截断
* - ``dccp_parsing``
     - ``drop``
     - 捕获因DCCP头部解析错误而丢弃的数据包
   * - ``gtp_parsing``
     - ``drop``
     - 捕获因GTP头部解析错误而丢弃的数据包
   * - ``esp_parsing``
     - ``drop``
     - 捕获因ESP头部解析错误而丢弃的数据包
   * - ``blackhole_nexthop``
     - ``drop``
     - 捕获设备决定丢弃的数据包，因为它们命中了一个黑洞下一跳
   * - ``dmac_filter``
     - ``drop``
     - 捕获设备决定丢弃的传入数据包，因为目的MAC地址没有配置在MAC表中且接口不是处于混杂模式
   * - ``eapol``
     - ``control``
     - 捕获“局域网上的可扩展认证协议”（EAPOL）数据包，如IEEE 802.1X中所规定
   * - ``locked_port``
     - ``drop``
     - 捕获设备决定丢弃的数据包，因为它们未能通过锁定桥接端口检查。也就是说，在锁定端口上接收的数据包其{SMAC, VID}与指向该端口的FDB条目不符

特定驱动程序的数据包捕获
===========================

设备驱动程序可以注册特定于驱动程序的数据包捕获，但这些必须明确记录。此类捕获可以对应于特定于设备的异常，并有助于调试由这些异常引起的丢包。以下列表包含了各种设备驱动程序注册的特定于驱动程序捕获描述的链接：

  * 文档/networking/devlink/netdevsim.rst
  * 文档/networking/devlink/mlxsw.rst
  * 文档/networking/devlink/prestera.rst

.. _通用数据包捕获组:

通用数据包捕获组
==================

通用数据包捕获组用于聚合逻辑相关的数据包捕获。这些组允许用户批量操作，例如设置所有成员捕获的动作。此外，“devlink-trap”可以报告每组的数据包和字节数统计信息，如果单独每个捕获的统计信息过于狭窄。这些组的描述必须添加到下表中：

.. list-table:: 通用数据包捕获组列表
   :widths: 10 90

   * - 名称
     - 描述
   * - ``l2_drops``
     - 包含在二层转发（即，桥接）过程中被设备丢弃的数据包捕获
   * - ``l3_drops``
     - 包含在三层转发过程中被设备丢弃的数据包捕获
   * - ``l3_exceptions``
     - 包含在三层转发过程中遇到异常（例如，TTL错误）的数据包捕获
   * - ``buffer_drops``
     - 包含因排队决策而被设备丢弃的数据包捕获
   * - ``tunnel_drops``
     - 包含在隧道封装/解封装过程中被设备丢弃的数据包捕获
   * - ``acl_drops``
     - 包含在ACL处理过程中被设备丢弃的数据包捕获
   * - ``stp``
     - 包含STP数据包的捕获
   * - ``lacp``
     - 包含LACP数据包的捕获
   * - ``lldp``
     - 包含LLDP数据包的捕获
   * - ``mc_snooping``
     - 包含用于多播监听所需的IGMP和MLD数据包的捕获
   * - ``dhcp``
     - 包含DHCP数据包的捕获
   * - ``neigh_discovery``
     - 包含邻居发现数据包（例如，ARP，IPv6 ND）的捕获
   * - ``bfd``
     - 包含BFD数据包的捕获
   * - ``ospf``
     - 包含OSPF数据包的捕获
   * - ``bgp``
     - 包含BGP数据包的捕获
   * - ``vrrp``
     - 包含VRRP数据包的捕获
   * - ``pim``
     - 包含PIM数据包的捕获
   * - ``uc_loopback``
     - 包含单播环回数据包的捕获（即，“uc_loopback”）。这个捕获是单独列出的，因为在例如单臂路由器的情况下它将被持续触发。为了限制对CPU使用率的影响，可以为该组绑定一个低速率的数据包捕获策略器，而不影响其他捕获
   * - ``local_delivery``
     - 包含应通过路由本地交付但不符合更具体的数据包捕获（例如，“ipv4_bgp”）的数据包捕获
   * - ``external_delivery``
     - 包含应通过不属于同一设备（例如，交换ASIC）的外部接口（例如，管理接口）进行路由的数据包捕获
   * - ``ipv6``
     - 包含各种IPv6控制数据包（例如，路由器通告）的捕获
   * - ``ptp_event``
     - 包含PTP时间关键事件消息（同步，延时请求，Pdelay_Req 和 Pdelay_Resp）的捕获
   * - ``ptp_general``
     - 包含PTP一般消息（通告，跟随，延时响应，Pdelay_Resp_Follow_Up，管理和信号）的捕获
   * - ``acl_sample``
     - 包含在ACL处理过程中被设备采样的数据包捕获
   * - ``acl_trap``
     - 包含在ACL处理过程中被设备捕获（记录）的数据包捕获
   * - ``parser_error_drops``
     - 包含在解析过程中被标记为错误的数据包捕获
   * - ``eapol``
     - 包含“局域网上的可扩展认证协议”（EAPOL）数据包的捕获，如IEEE 802.1X中所规定

数据包捕获策略器
==================

如前所述，底层设备可以将某些数据包捕获到CPU进行处理。在大多数情况下，底层设备能够处理比CPU所能处理的高几个数量级的数据包速率。
因此，为了避免底层设备压垮CPU，通常设备包含数据包捕获策略器，能够将捕获的数据包控制在CPU可以处理的速率内。
```markdown
``devlink-trap`` 机制允许具备能力的设备驱动向 ``devlink`` 注册它们支持的数据包陷阱策略。设备驱动可以选择在初始化期间将这些策略与支持的数据包陷阱组（参见 :ref:`通用数据包陷阱组`）关联起来，从而将其默认的控制平面策略暴露给用户空间。
设备驱动应允许用户空间更改策略的参数（例如，速率、突发大小），以及策略与陷阱组之间的关联，这需要实现相关的回调函数。
如果可能的话，设备驱动应该实现一个回调函数，允许用户空间获取因违反配置策略而被策略丢弃的数据包数量。
测试
=====

参见 ``tools/testing/selftests/drivers/net/netdevsim/devlink_trap.sh`` 以获取覆盖核心基础设施的测试。对于任何新功能都应添加测试用例。
设备驱动应专注于测试特定于设备的功能，比如触发支持的数据包陷阱等。
```
