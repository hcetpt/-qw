SPDX 许可证标识符: GPL-2.0

============
Devlink Trap
============

背景
======

能够卸载内核数据路径并执行如桥接和路由等功能的设备，还必须能够将特定的数据包发送到内核（即CPU）进行处理。例如，作为多播感知桥接器运行的设备必须能够将IGMP成员报告发送到内核以供桥接模块处理。如果不处理这些数据包，桥接模块将无法填充其MDB。另一个例子是作为路由器运行的设备，在收到一个TTL为1的IP数据包后，必须将其发送到内核以便由内核路由并生成ICMP超时错误数据报。如果让内核自己不路由这种数据包的话，像“traceroute”这样的工具将无法工作。发送某些数据包到内核进行处理的基本能力被称为“数据包捕获”。

概述
======

“devlink-trap”机制允许有能力的设备驱动程序向“devlink”注册它们支持的数据包捕获，并将捕获的数据包报告给“devlink”以进一步分析。当接收到捕获的数据包时，“devlink”会对每个捕获的数据包进行计数，并可能通过netlink事件将数据包连同所有提供的元数据（如捕获原因、时间戳、输入端口）报告给用户空间。这对于丢包捕获尤其有用（见：Trap-Types），因为它允许用户获得对那些原本不可见的丢包的更多可见性。

下图提供了“devlink-trap”的总体概述：

```
                                    Netlink事件：带有元数据的数据包
                                                   或最近丢包的汇总
                                  ^
                                  |
         用户空间                |
        +---------------------------------------------------+
         内核                   |
                                  |
                          +-------+--------+
                          |                |
                          | 丢包监控器     |
                          |                |
                          +-------^--------+
                                  |
                                  | 非控制捕获
                                  |
                             +----+----+
                             |         |      内核的接收路径
                             | devlink |      （非丢包捕获）
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
         内核                   |
        +---------------------------------------------------+
         硬件                  |
                                  | 捕获的数据包
                                  |
                               +--+---+
                               |      |
                               | ASIC |
                               |      |
                               +------+
```

.. _Trap-Types:

捕获类型
=======

“devlink-trap”机制支持以下数据包捕获类型：

  * “丢包”：底层设备丢弃了捕获的数据包。这些数据包仅由“devlink”处理，不会注入到内核的接收路径中。捕获操作（参见：Trap-Actions）可以更改。
  * “异常”：由于异常情况（例如TTL错误、邻居条目缺失等），底层设备未能按预期转发数据包，并将其捕获到控制平面进行解决。这些数据包由“devlink”处理并注入内核的接收路径。不允许更改此类捕获的操作，因为这很容易破坏控制平面。
``control``：被设备捕获的数据包是因为这些数据包是控制平面正常运行所需的控制数据包。例如，ARP 请求和 IGMP 查询数据包。这些数据包被注入内核的接收路径中，但不会上报给内核丢弃监控器。更改此类陷阱的操作是不允许的，因为这可能会轻易破坏控制平面。

.. _Trap-Actions:

### 捕获动作

`devlink-trap`机制支持以下数据包捕获动作：

  * ``trap``：唯一的数据包副本被发送到CPU。
  * ``drop``：数据包由底层设备丢弃，并且不将副本发送到CPU。
  * ``mirror``：数据包由底层设备转发，并且副本被发送到CPU。

### 通用数据包捕获

通用数据包捕获用于描述捕获明确定义的数据包或由于明确定义条件（例如TTL错误）而被捕获的数据包。这类捕获可以被多个设备驱动程序共享，并且其描述必须添加到下表中：

.. list-table:: 通用数据包捕获列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``source_mac_is_multicast``
     - ``drop``
     - 捕获设备决定丢弃的具有多播源MAC地址的入站数据包。
   * - ``vlan_tag_mismatch``
     - ``drop``
     - 捕获设备决定丢弃的VLAN标签不匹配的入站数据包：入站桥接端口未配置PVID，且数据包未标记或优先级标记。
   * - ``ingress_vlan_filter``
     - ``drop``
     - 捕获设备决定丢弃的带有未在入站桥接端口上配置的VLAN标签的入站数据包。
   * - ``ingress_spanning_tree_filter``
     - ``drop``
     - 捕获设备决定丢弃的入站桥接端口STP状态不是“转发”的入站数据包。
   * - ``port_list_is_empty``
     - ``drop``
     - 捕获设备决定丢弃的需要泛洪（如未知单播、未注册多播）但没有可泛洪端口的数据包。
   * - ``port_loopback_filter``
     - ``drop``
     - 捕获设备决定丢弃的经过二层转发后唯一应传输的端口是接收端口的数据包。
   * - ``blackhole_route``
     - ``drop``
     - 捕获设备决定丢弃的命中黑洞路由的数据包。
   * - ``ttl_value_is_too_small``
     - ``exception``
     - 捕获设备应该转发的TTL值减小为0或更小的单播数据包。
   * - ``tail_drop``
     - ``drop``
     - 捕获设备决定丢弃的无法入列到已满的传输队列中的数据包。
   * - ``non_ip``
     - ``drop``
     - 捕获设备决定丢弃的需要进行三层查找但不是IP或MPLS数据包的数据包。
   * - ``uc_dip_over_mc_dmac``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且具有单播目的IP和多播目的MAC的数据包。
   * - ``dip_is_loopback_address``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且目的IP为回环地址（即127.0.0.0/8和::1/128）的数据包。
   * - ``sip_is_mc``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且源IP为多播（即224.0.0.0/8和ff::/8）的数据包。
   * - ``sip_is_loopback_address``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且源IP为回环地址（即127.0.0.0/8和::1/128）的数据包。
   * - ``ip_header_corrupted``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且IP头损坏（如错误校验和、错误IP版本或太短的互联网头长度[IHL]）的数据包。
   * - ``ipv4_sip_is_limited_bc``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且源IP为有限广播（即255.255.255.255/32）的数据包。
   * - ``ipv6_mc_dip_reserved_scope``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且IPv6多播目的IP具有保留范围（即ffx0::/16）的IPv6数据包。
   * - ``ipv6_mc_dip_interface_local_scope``
     - ``drop``
     - 捕获设备决定丢弃的需要路由且IPv6多播目的IP具有接口本地范围（即ffx1::/16）的IPv6数据包。
   * - ``mtu_value_is_too_small``
     - ``exception``
     - 捕获应该由设备路由但大于出口接口MTU的数据包。
   * - ``unresolved_neigh``
     - ``exception``
     - 捕获路由后未找到匹配的IP邻居的数据包。
   * - ``mc_reverse_path_forwarding``
     - ``exception``
     - 捕获多播路由期间未能通过反向路径转发（RPF）检查的多播IP数据包。
   * - ``reject_route``
     - ``exception``
     - 捕获命中拒绝路由（如“不可达”、“禁止”）的数据包。
   * - ``ipv4_lpm_miss``
     - ``exception``
     - 捕获未匹配任何路由的单播IPv4数据包。
   * - ``ipv6_lpm_miss``
     - ``exception``
     - 捕获未匹配任何路由的单播IPv6数据包。
   * - ``non_routable_packet``
     - ``drop``
     - 捕获设备决定丢弃的不应路由的数据包。例如，IGMP查询可以在二层被设备泛洪并到达路由器。这种数据包不应被路由，而是应被丢弃。
   * - ``decap_error``
     - ``exception``
     - 捕获设备决定丢弃的因解封装失败（如数据包太短、VXLAN头中设置了保留位）的NVE和IPinIP数据包。
   * - ``overlay_smac_is_mc``
     - ``drop``
     - 捕获设备决定丢弃的叠加源MAC为多播的NVE数据包。
   * - ``ingress_flow_action_drop``
     - ``drop``
     - 捕获处理入站流操作丢弃时丢弃的数据包。
   * - ``egress_flow_action_drop``
     - ``drop``
     - 捕获处理出站流操作丢弃时丢弃的数据包。
   * - ``stp``
     - ``control``
     - 捕获STP数据包。
   * - ``lacp``
     - ``control``
     - 捕获LACP数据包。
   * - ``lldp``
     - ``control``
     - 捕获LLDP数据包。
   * - ``igmp_query``
     - ``control``
     - 捕获IGMP成员查询数据包。
   * - ``igmp_v1_report``
     - ``control``
     - 捕获IGMP版本1成员报告数据包。
   * - ``igmp_v2_report``
     - ``control``
     - 捕获IGMP版本2成员报告数据包。
   * - ``igmp_v3_report``
     - ``control``
     - 捕获IGMP版本3成员报告数据包。
   * - ``igmp_v2_leave``
     - ``control``
     - 捕获IGMP版本2离开组数据包。
   * - ``mld_query``
     - ``control``
     - 捕获MLD多播监听查询数据包。
   * - ``mld_v1_report``
     - ``control``
     - 捕获MLD版本1多播监听报告数据包。
   * - ``mld_v2_report``
     - ``control``
     - 捕获MLD版本2多播监听报告数据包。
   * - ``mld_v1_done``
     - ``control``
     - 捕获MLD版本1多播监听完成数据包。
   * - ``ipv4_dhcp``
     - ``control``
     - 捕获IPv4 DHCP数据包。
   * - ``ipv6_dhcp``
     - ``control``
     - 捕获IPv6 DHCP数据包。
   * - ``arp_request``
     - ``control``
     - 捕获ARP请求数据包。
   * - ``arp_response``
     - ``control``
     - 捕获ARP响应数据包。
   * - ``arp_overlay``
     - ``control``
     - 捕获到达覆盖网络的NVE解封装后的ARP数据包。例如，当需要解析的地址为本地地址时。
   * - ``ipv6_neigh_solicit``
     - ``control``
     - 捕获IPv6邻居请求数据包。
   * - ``ipv6_neigh_advert``
     - ``control``
     - 捕获IPv6邻居通告数据包。
   * - ``ipv4_bfd``
     - ``control``
     - 捕获IPv4 BFD数据包。
   * - ``ipv6_bfd``
     - ``control``
     - 捕获IPv6 BFD数据包。
   * - ``ipv4_ospf``
     - ``control``
     - 捕获IPv4 OSPF数据包。
   * - ``ipv6_ospf``
     - ``control``
     - 捕获IPv6 OSPF数据包。
   * - ``ipv4_bgp``
     - ``control``
     - 捕获IPv4 BGP数据包。
   * - ``ipv6_bgp``
     - ``control``
     - 捕获IPv6 BGP数据包。
   * - ``ipv4_vrrp``
     - ``control``
     - 捕获IPv4 VRRP数据包。
   * - ``ipv6_vrrp``
     - ``control``
     - 捕获IPv6 VRRP数据包。
   * - ``ipv4_pim``
     - ``control``
     - 捕获IPv4 PIM数据包。
   * - ``ipv6_pim``
     - ``control``
     - 捕获IPv6 PIM数据包。
   * - ``uc_loopback``
     - ``control``
     - 捕获需要通过接收的同一层3接口路由的单播数据包。这些数据包由内核路由，但也可能生成ICMP重定向数据包。
   * - ``local_route``
     - ``control``
     - 捕获命中本地路由并需要本地交付的单播数据包。
   * - ``external_route``
     - ``control``
     - 捕获应通过外部接口（如管理接口）路由的数据包，该接口不属于与入站接口相同的设备（如交换ASIC）。
   * - ``ipv6_uc_dip_link_local_scope``
     - ``control``
     - 捕获需要路由且目的IP地址具有链路本地范围（即fe80::/10）的单播IPv6数据包。此捕获允许设备驱动程序避免编程链路本地路由，但仍接收本地交付的数据包。
   * - ``ipv6_dip_all_nodes``
     - ``control``
     - 捕获目的IP地址为“所有节点地址”（即ff02::1）的IPv6数据包。
   * - ``ipv6_dip_all_routers``
     - ``control``
     - 捕获目的IP地址为“所有路由器地址”（即ff02::2）的IPv6数据包。
   * - ``ipv6_router_solicit``
     - ``control``
     - 捕获IPv6路由器请求数据包。
   * - ``ipv6_router_advert``
     - ``control``
     - 捕获IPv6路由器通告数据包。
   * - ``ipv6_redirect``
     - ``control``
     - 捕获IPv6重定向消息数据包。
   * - ``ipv4_router_alert``
     - ``control``
     - 捕获需要路由且包含路由器警告选项的IPv4数据包。这些数据包需要本地交付到设置了IP_ROUTER_ALERT套接字选项的原始套接字。
   * - ``ipv6_router_alert``
     - ``control``
     - 捕获需要路由且在其逐跳扩展头中包含路由器警告选项的IPv6数据包。这些数据包需要本地交付到设置了IPV6_ROUTER_ALERT套接字选项的原始套接字。
   * - ``ptp_event``
     - ``control``
     - 捕获PTP时间关键事件消息（同步、延迟请求、Pdelay_Req和Pdelay_Resp）。
   * - ``ptp_general``
     - ``control``
     - 捕获PTP一般消息（通告、跟随、延迟响应、Pdelay_Resp跟随、管理和信令）。
   * - ``flow_action_sample``
     - ``control``
     - 捕获处理流动作采样时采样的数据包（如通过tc的采样动作）。
   * - ``flow_action_trap``
     - ``control``
     - 捕获处理流动作捕获时记录的数据包（如通过tc的捕获动作）。
   * - ``early_drop``
     - ``drop``
     - 捕获由于随机早期检测（RED）算法导致的丢弃的数据包（即早期丢弃）。
   * - ``vxlan_parsing``
     - ``drop``
     - 捕获由于VXLAN头解析错误导致的丢弃的数据包，可能是由于数据包截断或I标志未设置。
   * - ``llc_snap_parsing``
     - ``drop``
     - 捕获由于LLC+SNAP头解析错误导致的丢弃的数据包。
   * - ``vlan_parsing``
     - ``drop``
     - 捕获由于VLAN头解析错误导致的丢弃的数据包。可能包括意外的数据包截断。
* - ``pppoe_ppp_parsing``
  - ``drop``
  - 捕获因PPPoE+PPP报头解析错误而丢弃的报文
这可能包括发现会话ID为0xFFFF（保留且不可用）、PPPoE长度大于接收到的帧或该类型报头上的任何常见错误。
* - ``mpls_parsing``
  - ``drop``
  - 捕获因MPLS报头解析错误而丢弃的报文
这可能包括意外的报头截断。
* - ``arp_parsing``
  - ``drop``
  - 捕获因ARP报头解析错误而丢弃的报文
* - ``ip_1_parsing``
  - ``drop``
  - 捕获因第一个IP报头解析错误而丢弃的报文
此报文捕获可能包括未通过IP校验和检查、报头长度检查（至少20字节）的报文，这些报文可能会因为报文截断而导致总长度字段超过接收的报文长度等。
* - ``ip_n_parsing``
  - ``drop``
  - 捕获因最后一个IP报头（在IP over IP隧道中的内部报头）解析错误而丢弃的报文。与``ip_1_parsing``捕获相同常见的错误检查。
* - ``gre_parsing``
  - ``drop``
  - 捕获因GRE报头解析错误而丢弃的报文
* - ``udp_parsing``
  - ``drop``
  - 捕获因UDP报头解析错误而丢弃的报文
此报文捕获可能包括校验和错误、不正确的UDP长度检测（小于8字节）或报头截断检测。
* - ``tcp_parsing``
  - ``drop``
  - 捕获因TCP报头解析错误而丢弃的报文
这可能包括TCP校验和错误、SYN、FIN和/或RESET的不正确组合等。
* - ``ipsec_parsing``
  - ``drop``
  - 捕获因IPSEC报头解析错误而丢弃的报文
* - ``sctp_parsing``
  - ``drop``
  - 捕获因SCTP报头解析错误而丢弃的报文
这意味着使用了端口号0或报头被截断。
* - ``dccp_parsing``
  - ``drop``
  - 捕获因DCCP报头解析错误而丢弃的报文
* - ``gtp_parsing``
  - ``drop``
  - 捕获因GTP报头解析错误而丢弃的报文
* - ``esp_parsing``
  - ``drop``
  - 捕获因ESP报头解析错误而丢弃的报文
* - ``blackhole_nexthop``
  - ``drop``
  - 捕获设备决定丢弃的报文，这些报文命中了黑洞下一跳
* - ``dmac_filter``
  - ``drop``
  - 捕获设备决定丢弃的入站报文，因为目标MAC地址未配置在MAC表中且接口不是处于混杂模式
* - ``eapol``
  - ``control``
  - 捕获“局域网上的可扩展身份验证协议”（EAPOL）报文，其在IEEE 802.1X中指定
* - ``locked_port``
  - ``drop``
  - 捕获设备决定丢弃的报文，因为它们未能通过锁定桥接端口检查。即，通过锁定端口接收到的报文，其{SMAC, VID}不符合指向端口的FDB条目。

### 驱动程序特定的报文捕获

设备驱动程序可以注册驱动程序特定的报文捕获，但这些必须明确记录。此类捕获可能对应于设备特定的异常，并有助于调试由这些异常导致的报文丢弃。以下列表包含各种设备驱动程序注册的驱动程序特定捕获描述链接：

  * 文档/网络/devlink/netdevsim.rst
  * 文档/网络/devlink/mlxsw.rst
  * 文档/网络/devlink/prestera.rst

### 通用报文捕获组

通用报文捕获组用于聚合逻辑相关的报文捕获。这些组允许用户批量操作，如设置所有成员捕获的动作。此外，“devlink-trap”可以报告每组的汇总报文和字节统计信息，在每个捕获统计信息过于狭窄的情况下。这些组的描述必须添加到下表中：

| 名称 | 描述 |
| --- | --- |
| l2_drops | 包含在第二层转发过程中设备丢弃的报文捕获（即，桥接） |
| l3_drops | 包含在第三层转发过程中设备丢弃的报文捕获 |
| l3_exceptions | 包含在第三层转发过程中触发异常（例如，TTL错误）的报文捕获 |
| buffer_drops | 包含由于入队决策而被设备丢弃的报文捕获 |
| tunnel_drops | 包含在隧道封装/解封装过程中设备丢弃的报文捕获 |
| acl_drops | 包含在ACL处理过程中设备丢弃的报文捕获 |
| stp | 包含STP报文捕获 |
| lacp | 包含LACP报文捕获 |
| lldp | 包含LLDP报文捕获 |
| mc_snooping | 包含用于多播监听所需的IGMP和MLD报文捕获 |
| dhcp | 包含DHCP报文捕获 |
| neigh_discovery | 包含邻居发现报文捕获（例如，ARP，IPv6 ND） |
| bfd | 包含BFD报文捕获 |
| ospf | 包含OSPF报文捕获 |
| bgp | 包含BGP报文捕获 |
| vrrp | 包含VRRP报文捕获 |
| pim | 包含PIM报文捕获 |
| uc_loopback | 包含单播报文环回捕获（即，“uc_loopback”）。此捕获单独列出，因为在某些情况下（例如，单臂路由器），它将不断触发。为了限制对CPU使用的影响，可以在不影响其他捕获的情况下将低速率的报文捕获策略绑定到组 |
| local_delivery | 包含应本地交付但在路由后未匹配更具体的报文捕获（例如，“ipv4_bgp”）的报文捕获 |
| external_delivery | 包含应通过外部接口（例如，管理接口）路由而不属于同一设备（例如，交换ASIC）的报文捕获 |
| ipv6 | 包含各种IPv6控制报文（例如，路由器通告）的报文捕获 |
| ptp_event | 包含PTP时间关键事件消息（同步，延迟请求，Pdelay_Req和Pdelay_Resp）的报文捕获 |
| ptp_general | 包含PTP一般消息（公告，Follow_Up，延迟响应，Pdelay_Resp_Follow_Up，管理和信令）的报文捕获 |
| acl_sample | 包含在ACL处理过程中被设备采样的报文捕获 |
| acl_trap | 包含在ACL处理过程中被设备捕获（记录）的报文捕获 |
| parser_error_drops | 包含在解析过程中被设备标记为错误的报文捕获 |
| eapol | 包含“局域网上的可扩展身份验证协议”（EAPOL）报文捕获，其在IEEE 802.1X中指定 |

### 报文捕获策略

如前所述，底层设备可以将某些报文捕获到CPU进行处理。在大多数情况下，底层设备能够处理比CPU高几个数量级的报文率。因此，为了避免底层设备压垮CPU，设备通常包括报文捕获策略，以将捕获的报文限制到CPU可以处理的速率。
``devlink-trap`` 机制允许具备能力的设备驱动程序向 ``devlink`` 注册其支持的报文陷阱策略。设备驱动程序可以选择在初始化期间将这些策略与支持的报文陷阱组（参见 :ref:`Generic-Packet-Trap-Groups`）关联，从而将其默认控制平面策略暴露给用户空间。

设备驱动程序应允许用户空间更改策略的参数（例如，速率、突发大小）以及策略与陷阱组之间的关联，通过实现相关的回调来完成这一功能。

如果可能的话，设备驱动程序应实现一个回调，使用户空间能够检索由于违反配置策略而被丢弃的报文数量。

测试
=====

参见 ``tools/testing/selftests/drivers/net/netdevsim/devlink_trap.sh`` 进行核心基础设施的测试。对于任何新功能，应添加测试用例。

设备驱动程序应专注于测试特定于设备的功能，例如触发支持的报文陷阱。
