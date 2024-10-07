SPDX 许可声明标识符: GPL-2.0

===================================
Linux 以太网绑定驱动程序 HOWTO
===================================

最新更新：2011年4月27日

初始发布：Thomas Davis <tadavis at lbl.gov>

修正和高可用性扩展：2000/10/03-15：

  - Willy Tarreau <willy at meta-x.org>
  - Constantine Gavrilov <const-g at xpert.com>
  - Chad N. Tindel <ctindel at ieee dot org>
  - Janice Girouard <girouard at us dot ibm dot com>
  - Jay Vosburgh <fubar at us dot ibm dot com>

2005年2月由Jay Vosburgh重新组织和更新
添加Sysfs信息：2006/04/24

  - Mitch Williams <mitch.a.williams at intel.com>

简介
============

Linux 绑定驱动程序提供了一种将多个网络接口聚合为一个逻辑上的“绑定”接口的方法。绑定接口的行为取决于所选择的模式；通常来说，这些模式提供了热备用或负载均衡服务。此外，还可以进行链路完整性监控。绑定驱动最初来自Donald Becker为内核2.0编写的Beowulf补丁。从那时起，该驱动程序已经发生了很大的变化，早期版本的工具（如extreme-linux和Beowulf站点提供的工具）将无法与当前版本的驱动程序兼容。对于新版本的驱动程序、更新的用户空间工具以及寻求帮助的对象，请参阅本文档末尾的链接。
.. 目录

   1. 绑定驱动程序安装

   2. 绑定驱动程序选项

   3. 配置绑定设备
   3.1 使用Sysconfig支持进行配置
   3.1.1 使用DHCP与Sysconfig
   3.1.2 使用Sysconfig配置多个绑定
   3.2 使用Initscripts支持进行配置
   3.2.1 使用DHCP与Initscripts
   3.2.2 使用Initscripts配置多个绑定
   3.3 使用Ifenslave手动配置绑定
   3.3.1 手动配置多个绑定
   3.4 使用Sysfs手动配置绑定
   3.5 使用Interfaces支持进行配置
   3.6 在特殊情况下覆盖配置
   3.7 以更安全的方式配置802.3ad模式下的LACP

   4. 查询绑定配置
   4.1 绑定配置
   4.2 网络配置

   5. 交换机配置

   6. 802.1q VLAN支持

   7. 链路监控
   7.1 ARP监控操作
   7.2 配置多个ARP目标
   7.3 MII监控操作

   8. 潜在的问题来源
   8.1 路由冒险
   8.2 以太网设备重命名
   8.3 Miimon缓慢或未检测到链路故障

   9. SNMP代理

   10. 混杂模式

   11. 配置绑定以实现高可用性
   11.1 单个交换机拓扑中的高可用性
   11.2 多个交换机拓扑中的高可用性
   11.2.1 多个交换机拓扑中的HA绑定模式选择
   11.2.2 多个交换机拓扑中的HA链路监控

   12. 配置绑定以实现最大吞吐量
   12.1 单个交换机拓扑中的最大吞吐量
   12.1.1 单个交换机拓扑中的MT绑定模式选择
   12.1.2 单个交换机拓扑中的MT链路监控
   12.2 多个交换机拓扑中的最大吞吐量
   12.2.1 多个交换机拓扑中的MT绑定模式选择
   12.2.2 多个交换机拓扑中的MT链路监控

   13. 交换机行为问题
   13.1 链路建立和故障切换延迟
   13.2 重复的传入数据包

   14. 特定硬件的考虑因素
   14.1 IBM BladeCenter

   15. 常见问题解答

   16. 资源和链接

1. 绑定驱动程序安装
==============================

大多数流行的发行版内核都已包含绑定驱动程序作为模块。如果您的发行版没有，或者您需要从源代码编译绑定驱动程序（例如，从kernel.org配置和安装主线内核），则需要执行以下步骤：

1.1 配置并构建带有绑定功能的内核
-----------------------------------------------

当前版本的绑定驱动程序位于最新内核源码的`drivers/net/bonding`子目录中（可以在http://kernel.org获取）。大多数自行构建内核的用户将希望使用来自kernel.org的最新内核。使用“make menuconfig”（或“make xconfig”或“make config”）配置内核，然后在“网络设备支持”部分选择“绑定驱动程序支持”。建议将驱动程序配置为模块，因为目前这是向驱动程序传递参数或配置多个绑定设备的唯一方法。构建并安装新的内核和模块。

1.2 绑定控制工具
---------------------------

建议通过iproute2（netlink）或sysfs配置绑定，旧的ifenslave控制工具已过时。

2. 绑定驱动程序选项
=========================

绑定驱动程序的选项可以在加载时作为参数传递给绑定模块，也可以通过sysfs指定。
模块选项可以作为命令行参数传递给 `insmod` 或 `modprobe` 命令，但通常指定在 `/etc/modprobe.d/*.conf` 配置文件中，或者在特定发行版的配置文件中（其中一些在下一部分中有详细说明）。关于 sysfs 的绑定支持详情，请参见下面的“通过 Sysfs 手动配置绑定”部分。可用的绑定驱动程序参数如下。如果未指定参数，则使用默认值。在最初配置绑定时，建议在另一个窗口中运行 `tail -f /var/log/messages` 来监控绑定驱动程序的错误信息。

至关重要的是，必须指定 `miimon` 或 `arp_interval` 和 `arp_ip_target` 参数，否则在网络链路故障期间会发生严重的网络性能下降。极少有设备不支持至少 `miimon`，因此没有理由不使用它。

接受文本值的选项将接受文本名称或为了向后兼容性而接受选项值。例如，“mode=802.3ad” 和 “mode=4” 设置了相同的模式。

参数如下：

### active_slave

- 指定对于支持它的模式（主动备份、负载平衡 ALB 和负载平衡 TLB）的新活动从设备。可能的值是当前从属接口的名称，或空字符串。如果给出名称，则从设备及其链路必须处于活动状态才能被选为新的活动从设备。如果指定空字符串，则清除当前活动从设备，并自动选择新的活动从设备。
注意：此选项仅通过 sysfs 接口可用。没有与此名称对应的模块参数。
此选项的正常值是当前活动从设备的名称，或者如果没有活动从设备或当前模式不使用活动从设备，则为空字符串。

### ad_actor_sys_prio

- 在 AD 系统中，此参数指定系统优先级。允许的范围是 1 到 65535。如果未指定该值，则默认为 65535。
此参数仅在 802.3ad 模式下有效，并且可通过 Sysfs 接口访问。
### ad_actor_system

在 AD 系统中，此参数指定了协议数据包交换（LACPDUs）中的参与者 MAC 地址。该值不能是多播地址。如果指定全零 MAC 地址，则 bonding 将内部使用 bond 本身的 MAC 地址。建议为该 MAC 设置本地管理位，但驱动程序不强制执行这一点。如果没有指定该值，则系统默认使用主接口的 MAC 地址作为参与者的系统地址。

此参数仅在 802.3ad 模式下有效，并且可通过 SysFs 接口访问。

### ad_select

此参数指定了要使用的 802.3ad 聚合选择逻辑。可能的值及其效果如下：

- **stable 或 0**

  活动聚合器由最大的聚合带宽选择。
  只有当活动聚合器的所有从属接口都失效或活动聚合器没有从属接口时才会重新选择活动聚合器。

  这是默认值。

- **bandwidth 或 1**

  活动聚合器由最大的聚合带宽选择。重新选择会在以下情况下发生：

  - 从属接口被添加到或从 bond 中移除
  - 任何从属接口的链路状态发生变化
  - 任何从属接口的 802.3ad 关联状态发生变化
  - bond 的管理状态变为 UP

- **count 或 2**

  活动聚合器由最多的端口（从属接口）数选择。重新选择的情况与“bandwidth”设置相同。

带宽和数量选择策略允许在部分活动聚合器故障时进行 802.3ad 聚合的故障切换。这确保了具有最高可用性（无论是带宽还是端口数量）的聚合器始终处于活动状态。

此选项是在 bonding 版本 3.4.0 中添加的。

### ad_user_port_key

在 AD 系统中，端口密钥分为三个部分，如下所示：

| 位数 | 用途       |
|------|------------|
| 00   | 全双工/半双工 |
| 01-05| 速度       |
| 06-15| 用户定义    |

此参数定义了端口密钥的高 10 位。取值范围为 0 到 1023。如果不指定，默认值为 0。

此参数仅在 802.3ad 模式下有效，并且可通过 SysFs 接口访问。
`all_slaves_active`

指定是否丢弃（0）或传递（1）在非活动端口上接收到的重复帧。
通常情况下，链路聚合会丢弃在非活动端口上接收到的重复帧，这对大多数用户来说是可取的。但在某些情况下，允许传递这些重复帧也是有用的。
默认值为0（丢弃在非活动端口上接收到的重复帧）。

`arp_interval`

指定ARP链路监控的频率（以毫秒为单位）。
ARP监控通过定期检查从属设备来确定它们是否最近发送或接收了流量（具体标准取决于链路聚合模式和从属设备的状态）。通过ARP探测生成定期流量，这些探测的目标地址由`arp_ip_target`选项指定。
此行为可以通过下面的`arp_validate`选项进行修改。
如果在与以太通道兼容的模式（模式0和2）中使用ARP监控，则交换机应配置为均匀分布所有链路的流量。如果交换机被配置为以XOR方式分配数据包，则所有来自ARP目标的回复将只在一个链路上接收，这可能导致其他团队成员失败。不应将ARP监控与miimon一起使用。值为0表示禁用ARP监控。默认值为0。
`arp_ip_target`

当`arp_interval`大于0时，指定要使用的IP地址作为ARP监控的对等点。这些是用于检测到目标链接健康状况的ARP请求的目标。
这些值应以ddd.ddd.ddd.ddd格式指定。多个IP地址之间必须用逗号分隔。至少需要一个IP地址才能使ARP监控功能正常工作。可以指定的最大目标数量为16个。默认值是没有IP地址。
`ns_ip6_target`

当`arp_interval`大于0时，指定要使用的IPv6地址作为IPv6监控的对等点。这些是用于检测到目标链接健康状况的NS请求的目标。
指定这些值的格式为 `ffff:ffff::ffff:ffff`。多个IPv6地址之间必须用逗号分隔。为了使NS/NA监控功能正常工作，至少需要提供一个IPv6地址。可以指定的最大目标数量为16个。默认值是没有IPv6地址。
arp_validate

指定是否在支持ARP监控的任何模式下验证ARP探测和响应，或者是否应将非ARP流量过滤（忽略）以用于链路监控目的。
可能的值包括：

- `none` 或 `0`

    不进行任何验证或过滤
- `active` 或 `1`

    仅对活动从设备进行验证
- `backup` 或 `2`

    仅对备份从设备进行验证
- `all` 或 `3`

    对所有从设备进行验证
- `filter` 或 `4`

    对所有从设备应用过滤，不进行验证
- `filter_active` 或 `5`

    对所有从设备应用过滤，仅对活动从设备进行验证
- `filter_backup` 或 `6`

    对所有从设备应用过滤，仅对备份从设备进行验证
验证：

启用验证后，ARP监控器会检查传入的ARP请求和响应，并且只有在接收到适当的ARP流量时才会认为某个从设备是可用的。
对于活动从设备（slave），验证检查会确认ARP回复是由`arp_ip_target`生成的。由于备用从设备通常不会收到这些回复，因此对备用从设备执行的验证是基于通过活动从设备发送出去的广播ARP请求。有可能某些交换机或网络配置会导致备用从设备接收不到ARP请求的情况；在这种情况下，必须禁用备用从设备的验证。

对备用从设备进行ARP请求的验证主要是帮助bonding决定在活动从设备发生故障时哪些从设备更有可能正常工作，但这并不能真正保证如果被选为下一个活动从设备时备用从设备一定能够工作。

在多个bonding主机通过一个共同的交换机同时向一个或多个目标发送ARP的情况下，验证是有用的。如果交换机与目标之间的链路失败（但交换机本身没有故障），由多个bonding实例生成的探测流量会使标准的ARP监视器误认为链路仍然可用。使用验证可以解决这个问题，因为ARP监视器只会考虑与其自身bonding实例相关的ARP请求和回复。

过滤：

启用过滤后，ARP监视器只使用接收到的ARP数据包来判断链路的可用性。非ARP数据包会被正常传递，但在确定从设备是否可用时不会被计算在内。
过滤操作仅考虑接收到的ARP数据包（无论源地址或目的地址）来判断从设备是否收到了用于链路可用性检测的流量。
在网络中存在大量第三方广播流量的情况下，过滤是有用的，因为这些流量可能会使标准的ARP监视器误认为链路仍然可用。使用过滤可以解决这个问题，因为只有ARP流量才会被用于链路可用性的检测。
此选项是在bonding版本3.1.0中添加的。

`arp_all_targets`

指定为了使ARP监视器认为一个从设备是可用的，需要有多少个`arp_ip_target`是可以到达的。
此选项仅影响启用了`arp_validation`的主-备模式下的从设备。
可能的值包括：
- `any` 或 `0`：当任何一个`arp_ip_target`可以到达时才认为从设备是可用的。
- `all` 或 `1`：当所有`arp_ip_target`都可以到达时才认为从设备是可用的。

`arp_missed_max`

指定在一个接口被ARP监视器标记为不可用之前，连续失败的`arp_interval`监控次数。
这意味着在连续达到指定次数的ARP监控失败之后，接口将被标记为不可用。
为了提供有序的故障转移语义，允许备用接口进行额外的一次监控检查（即，在被标记为故障之前必须失败 arp_missed_max + 1 次）。
默认值是 2，允许的范围是 1 - 255。

coupled_control

    指定在 802.3ad 模式下，LACP 状态机的 MUX 是否应该有独立的收集和分发状态。
这是通过实现 IEEE 802.1AX-2008 第 5.4.15 节中规定的每个独立控制状态机来实现的，此外还有现有的耦合控制状态机。
默认值是 1。此设置不会分离收集和分发状态，保持耦合控制中的连接。

downdelay

    指定在检测到链路故障后禁用从属接口之前等待的时间（以毫秒为单位）。此选项仅对 miimon 链路监控有效。downdelay 值应该是 miimon 值的倍数；如果不是，则会被向下取整到最近的倍数。默认值是 0。

fail_over_mac

    指定在主动-备用模式下是否应将所有从属接口设置为相同的 MAC 地址（传统行为），或者启用时根据所选策略对绑定的 MAC 地址进行特殊处理。
可能的值如下：

    none 或 0

        此设置禁用 fail_over_mac，并且在绑定时将所有主动-备用绑定的从属接口设置为相同的 MAC 地址。这是默认设置。
    
    active 或 1

        “active” fail_over_mac 策略表示绑定的 MAC 地址始终应为主动从属接口的 MAC 地址。从属接口的 MAC 地址不会改变；相反，在故障转移期间绑定的 MAC 地址会改变。
此策略对于那些永远不能更改其 MAC 地址的设备或拒绝带有自身源 MAC 的传入广播（这会干扰 ARP 监控）的设备非常有用。
这项策略的缺点是，网络中的每个设备都必须通过免费ARP（gratuitous ARP）进行更新，而传统方法只需要更新交换机或一组交换机（通常对于任何流量，而不仅仅是ARP流量，如果交换机通过监听传入流量来更新其表项的话）。如果免费ARP丢失，通信可能会中断。

当此策略与mii监视器一起使用时，那些在能够实际传输和接收之前就声明链路已建立的设备特别容易丢失免费ARP，并且可能需要一个适当的updelay设置。

“跟随”故障转移MAC地址策略使得绑定接口的MAC地址按常规方式选择（通常是第一个加入绑定的从设备的MAC地址）。然而，在备份角色中，第二个及后续的从设备不会被设置为这个MAC地址；从设备在故障转移时会被编程为绑定接口的MAC地址（而原先活跃的从设备将获得新活跃从设备的MAC地址）。
此策略对于多端口设备非常有用，因为这些设备在多个端口被设置为相同的MAC地址时可能会变得混乱或性能下降。
默认策略是“无”，除非第一个从设备无法更改其MAC地址，在这种情况下，默认选择“活动”策略。
只有在网络绑定中没有从设备时，才能通过sysfs修改此选项。
此选项是在绑定版本3.2.0中添加的。“跟随”策略是在绑定版本3.3.0中添加的。

lacp_active
指定是否周期性发送LACPDU帧。
off 或 0
LACPDU帧作为“仅在被询问时才发言”的机制。
on 或 1  
LACPDU 帧会沿着配置的链路周期性发送。更多详情请参阅 `lacp_rate`。

默认值为 on。
```
lacp_rate
```

此选项用于指定在 802.3ad 模式下请求对端传输 LACPDU 数据包的速率。可能的值有：

- slow 或 0：请求对端每 30 秒传输一次 LACPDUs
- fast 或 1：请求对端每 1 秒传输一次 LACPDUs

默认值为 slow。
```
max_bonds
```

此选项用于指定为当前实例创建的绑定设备数量。例如，如果 `max_bonds` 设置为 3，并且绑定驱动尚未加载，则将创建 `bond0`、`bond1` 和 `bond2`。默认值为 1。设置为 0 将加载绑定驱动，但不会创建任何设备。
```
miimon
```

此选项用于指定 MII 链路监控频率（以毫秒为单位）。这决定了多久检查一次每个从属链路的状态以检测链路故障。设置为 0 表示禁用 MII 链路监控。100 是一个很好的起点。下面的 `use_carrier` 选项会影响链路状态的确定方式。更多信息请参阅高可用性部分。如果未设置 `arp_interval`，默认值为 100。
```
min_links
```

此选项用于指定在激活载体之前必须处于活动状态的最小链路数。类似于思科 EtherChannel 的 min-links 功能。这允许设置成员端口在标记绑定设备为活动状态前所需的最小数量。这对于确保在切换之前至少有最低带宽的链路处于活动状态的情况非常有用。此选项仅影响 802.3ad 模式。

默认值为 0。这意味着只要存在一个活动的聚合器，无论该聚合器中有多少可用链路，都会激活载体（对于 802.3ad 模式）。需要注意的是，因为没有至少一个可用链路的情况下聚合器不能处于活动状态，因此将此选项设置为 0 或 1 具有相同的效果。
```
mode
```

此选项用于指定一种绑定策略。默认值为 balance-rr（轮询）。可能的值有：

- balance-rr 或 0：轮询策略：按照顺序从第一个可用从属链路发送数据包到最后一个。这种模式提供了负载均衡和容错能力。
主动-备份或1

- 主动-备份策略：仅有一个从设备处于活动状态。只有当活动的从设备出现故障时，另一个从设备才会成为活动设备。为避免混淆交换机，绑定的MAC地址只在一个端口（网络适配器）上对外可见。

在2.6.2版本或更高版本的绑定中，当在主动-备份模式下发生故障切换时，绑定将在新的活动从设备上发送一个或多个免费ARP。

对于绑定主接口及其上方配置的每个VLAN接口，将发出一个免费ARP，前提是该接口至少配置了一个IP地址。为VLAN接口发出的免费ARP将带有相应的VLAN ID。

这种模式提供了容错能力。下面文档中的“主选项”会影响此模式的行为。

平衡异或或2

- 异或策略：根据选定的传输哈希策略进行传输。默认策略是一个简单的[(源MAC地址与目标MAC地址异或后再与数据包类型ID异或)取模于从设备数量]。可以通过下面描述的xmit_hash_policy选项选择其他传输策略。

这种模式提供了负载均衡和容错能力。

广播或3

- 广播策略：通过所有从设备接口传输所有内容。这种模式提供了容错能力。

802.3ad或4

- IEEE 802.3ad动态链路聚合。创建具有相同速度和双工设置的聚合组。根据802.3ad规范利用活动聚合器中的所有从设备。

出站流量的从设备选择是根据传输哈希策略进行的，该策略可以通过xmit_hash_policy选项从默认的简单异或策略更改。请注意，并非所有传输策略都符合802.3ad标准的要求，特别是在标准第43.2.4节关于数据包顺序错误的要求方面。不同的实现对不符合标准的容忍度各不相同。

先决条件：

1. 基础驱动程序中支持使用ethtool获取每个从设备的速度和双工设置。
2. 支持 IEEE 802.3ad 动态链路聚合的交换机
大多数交换机需要某种类型的配置来启用 802.3ad 模式。

- `balance-tlb` 或 5

  自适应传输负载均衡：不需要特殊交换机支持的通道绑定。
  在 `tlb_dynamic_lb=1` 模式下，根据每个从设备当前的负载（相对于速度计算）分配传出流量。
  在 `tlb_dynamic_lb=0` 模式下，禁用基于当前负载的负载均衡，并仅使用哈希分布进行负载分配。
  接收流量由当前的从设备接收。
  如果接收的从设备发生故障，则另一个从设备会接管故障接收从设备的 MAC 地址。

前提条件：
- 基础驱动程序中支持 ethtool 以获取每个从设备的速度。

- `balance-alb` 或 6

  自适应负载均衡：包括 `balance-tlb` 加上 IPv4 流量的接收负载均衡（RLB），不需要特殊交换机支持。接收负载均衡通过 ARP 协商实现。
  绑定驱动程序会拦截本地系统发出的 ARP 回复，并将源硬件地址替换为绑定中的一个从设备的独特硬件地址，从而使不同的对等端使用不同的硬件地址与服务器通信。
接收由服务器创建的连接所产生的流量也是均衡的。当本地系统发送ARP请求时，绑定驱动程序会复制并保存来自ARP数据包的对等体IP信息。当ARP回复从对等体到达时，其硬件地址被检索，并且绑定驱动程序向这个对等体发起一个ARP回复，将其分配给绑定中的某个从设备。使用ARP协商进行负载均衡的一个问题是，每次广播ARP请求时都会使用绑定的硬件地址。因此，对等体会学习到绑定的硬件地址，接收流量的均衡将退化为当前的从设备。这通过向所有对等体发送更新（ARP回复），使用它们各自分配的硬件地址来实现，从而使流量重新分布。当新的从设备加入绑定或不活动的从设备重新激活时，接收流量也会重新分布。接收负载在绑定中最高速度的从设备之间按顺序（轮询）分配。

当链路重新连接或新的从设备加入绑定时，通过向每个客户端发起具有选定MAC地址的ARP回复，接收流量会在绑定中的所有活动从设备之间重新分布。updelay参数（如下详细说明）必须设置为等于或大于交换机转发延迟的值，以便发送给对等体的ARP回复不会被交换机阻止。

先决条件：

1. 基础驱动程序支持通过ethtool获取每个从设备的速度。
2. 基础驱动程序支持在设备打开状态下设置硬件地址。这是必需的，以确保始终有一个从设备使用绑定的硬件地址（curr_active_slave），同时每个绑定中的从设备都有一个唯一的硬件地址。如果curr_active_slave失败，则其硬件地址将与新选择的curr_active_slave交换。

num_grat_arp, num_unsol_na

指定在故障转移事件后要发出的对等体通知（免费ARP和未请求的IPv6邻居通告）的数量。一旦新的从设备上的链路建立（可能立即），就会在绑定设备及其每个VLAN子设备上发送对等体通知。如果数量大于1，则按照peer_notif_delay指定的速率重复这一过程。
有效范围是0 - 255；默认值是1。这些选项仅影响主动-备份模式。这些选项分别是在绑定版本3.3.0和3.4.0中添加的。
从Linux 3.0和绑定版本3.7.1开始，这些通知由ipv4和ipv6代码生成，重复次数不能独立设置。

packets_per_slave

指定在切换到下一个从设备之前通过一个从设备传输的数据包数量。当设置为0时，则随机选择一个从设备。
有效范围是0 - 65535；默认值是1。此选项仅在balance-rr模式下生效。

peer_notif_delay

指定在故障转移事件后每次对等体通知（免费ARP和未请求的IPv6邻居通告）之间的延迟（毫秒）。
这个延迟应该是MII链路监控间隔（miimon）的倍数。
有效范围是0-300000。默认值为0，这意味着与MII链路监控间隔的值相匹配。

prio
从设备优先级。数值越高表示优先级越高。
主设备具有最高优先级。此选项也遵循primary_reselect规则。
此选项只能通过netlink配置，并且仅在active-backup(1)、balance-tlb (5)和balance-alb (6)模式下有效。
有效值范围是一个32位有符号整数。
默认值为0。

primary
一个字符串（如eth0、eth2等），指定哪个从设备是主设备。
指定的设备只要可用就始终作为活动从设备。只有当主设备离线时才会使用备用设备。当某个从设备比其他设备更优时，例如某个从设备具有更高的吞吐量时，这很有用。
primary选项仅在active-backup(1)、balance-tlb (5)和balance-alb (6)模式下有效。

primary_reselect
指定主从设备的重新选择策略。这影响了在活动从设备发生故障或主设备恢复时如何选择主从设备成为活动从设备。此选项旨在防止主从设备和其他从设备之间的频繁切换。可能的值包括：

always 或 0（默认）
主从设备只要恢复就会成为活动从设备。
better or 1

当主从设备重新启动时，如果其速度和双工模式优于当前活动从设备的速度和双工模式，则该主从设备将成为活动从设备。

failure or 2

只有在当前活动从设备发生故障且主从设备已启动的情况下，主从设备才会成为活动从设备。

primary_reselect 设置在以下两种情况下会被忽略：

- 如果没有从设备处于活动状态，则第一个恢复的从设备将被设为活动从设备。
- 在最初设置为从设备时，主从设备始终会被设为活动从设备。

通过 sysfs 更改 primary_reselect 策略会立即根据新的策略选择最佳活动从设备。这可能会或可能不会导致活动从设备的更改，具体情况而定。

此选项是在绑定版本 3.6.0 中添加的。

tlb_dynamic_lb

指定是否在 tlb 或 alb 模式下启用流的动态重排。此值对其他模式无影响。

tlb 模式的默认行为是根据当前负载在各个从设备之间重排活动流。这提供了良好的负载均衡特性，但也可能导致数据包重排序。如果重排序是一个问题，可以使用此变量禁用流重排，并仅依赖哈希分布提供的负载均衡。

xmit-hash-policy 可用于选择适当的哈希算法。

sysfs 条目可用于按绑定设备更改设置，初始值来自模块参数。只有在绑定设备处于关闭状态时才允许更改 sysfs 条目。
默认值为“1”，这会启用流量重排，而值“0”则禁用它。此选项是在bonding驱动程序3.7.1版本中添加的。

`updelay`

指定在检测到链路恢复后等待重新启用从设备的时间（以毫秒为单位）。此选项仅对miimon链路监控器有效。`updelay`的值应是miimon值的倍数；如果不是，则会被向下取整至最接近的倍数值。默认值为0。

`use_carrier`

指定miimon是否使用MII或ETHTOOL的ioctl调用与netif_carrier_ok()来确定链路状态。MII或ETHTOOL的ioctl调用效率较低，并且在内核中使用了已弃用的调用序列。netif_carrier_ok()依赖于设备驱动程序维护其状态（通过netif_carrier_on/off）；截至本文撰写时，大多数但并非所有设备驱动程序都支持此功能。
如果bonding坚持认为链路处于活动状态但实际上不应该如此，可能是因为您的网络设备驱动程序不支持netif_carrier_on/off。netif_carrier的默认状态是“链路活动”，因此如果驱动程序不支持netif_carrier，看起来链路总是处于活动状态。在这种情况下，将`use_carrier`设置为0会使bonding回退到使用MII/ETHTOOL ioctl方法来确定链路状态。
值1启用netif_carrier_ok()的使用，值0则使用已弃用的MII/ETHTOOL ioctl调用。默认值为1。

`xmit_hash_policy`

选择用于在balance-xor、802.3ad和tlb模式下选择从设备的传输哈希策略。可能的值包括：

`layer2`

使用硬件MAC地址和数据包类型ID字段的异或运算生成哈希值。公式为：

哈希值 = 源MAC[5] 异或 目标MAC[5] 异或 数据包类型ID  
从设备编号 = 哈希值 mod 从设备数量

此算法将把流向特定网络对等方的所有流量分配到同一个从设备上。此算法符合802.3ad标准。

`layer2+3`

此策略结合使用第二层和第三层协议信息生成哈希值。
使用硬件MAC地址和IP地址的异或运算生成哈希值。公式为：

哈希值 = 源MAC[5] 异或 目标MAC[5] 异或 数据包类型ID  
哈希值 = 哈希值 异或 源IP 异或 目标IP  
哈希值 = 哈希值 异或 (哈希值右移16位)  
哈希值 = 哈希值 异或 (哈希值右移8位)  
然后将哈希值模从设备数量

如果协议为IPv6，则首先使用ipv6_addr_hash对源地址和目标地址进行哈希运算。
此算法将把流向特定网络对等方的所有流量分配到同一个从设备上。对于非IP流量，公式与`layer2`传输哈希策略相同。
此策略旨在提供比仅使用第二层更为均衡的流量分布，特别是在需要通过第三层网关设备来访问大多数目的地的环境中。

此算法符合802.3ad标准。
第三层+第四层

此策略在可用的情况下利用上层协议信息生成哈希值。这允许流向特定网络对等体的流量可以分布在多个链路中，尽管单个连接不会跨越多个链路。
对于未分片的TCP和UDP数据包，其哈希计算公式为：

    哈希值 = 源端口，目的端口（如报头所示）
    哈希值 = 哈希值 XOR 源IP XOR 目的IP
    哈希值 = 哈希值 XOR (哈希值右移16位)
    哈希值 = 哈希值 XOR (哈希值右移8位)
    哈希值 = 哈希值右移1位
    然后将哈希值对从属链路数量取模

如果协议是IPv6，则首先使用ipv6_addr_hash函数对源地址和目的地址进行哈希处理。
对于已分片的TCP或UDP数据包以及所有其他IPv4和IPv6协议流量，忽略源端口和目的端口信息。对于非IP流量，其哈希计算公式与第二层传输哈希策略相同。
此算法不完全符合802.3ad标准。包含已分片和未分片数据包的单一TCP或UDP会话将看到数据包分布在两个接口上。这可能导致数据包乱序交付。大多数流量类型不会遇到这种情况，因为TCP很少分片流量，而大多数UDP流量并不涉及长时间的会话。其他实现可能能够容忍这种不符合性，也可能不能。

封装第二层+第三层

此策略使用与第二层+第三层相同的公式，但它依赖于skb_flow_dissect来获取报头字段，如果使用了封装协议，则可能会使用内部报头。例如，这对于隧道用户来说会提高性能，因为数据包将根据封装流进行分配。

封装第三层+第四层

此策略使用与第三层+第四层相同的公式，但它依赖于skb_flow_dissect来获取报头字段，如果使用了封装协议，则可能会使用内部报头。例如，这对于隧道用户来说会提高性能，因为数据包将根据封装流进行分配。

VLAN+源MAC

此策略使用非常基础的VLAN ID和源MAC哈希来进行基于VLAN的负载均衡，并在一条链路故障时进行切换。预期的应用场景是为多个虚拟机共享一个绑定，每个虚拟机都配置了自己的VLAN，以提供类似LACP的功能，但无需LACP兼容的交换硬件。
哈希值的计算公式如下：

    hash = (VLAN ID) XOR (源MAC供应商) XOR (源MAC设备)

默认值为layer2。此选项是在bonding版本2.6.3中添加的。在更早版本的bonding中，此参数不存在，并且layer2策略是唯一的策略。layer2+3值是在bonding版本3.2.2中添加的。

重发IGMP

指定在故障转移事件发生后要发送的IGMP成员报告的数量。故障转移后立即发送一个成员报告，随后的报文将在每个200毫秒的时间间隔内发送。
有效范围是0到255；默认值为1。设置为0将阻止在故障转移事件响应时发送IGMP成员报告。
此选项适用于以下bonding模式：balance-rr（0）、active-backup（1）、balance-tlb（5）和balance-alb（6），因为在这些模式下，故障转移可能会切换IGMP流量从一个从属接口到另一个。因此，必须重新发送IGMP报告以使交换机通过新选择的从属接口转发传入的IGMP流量。
此选项是在bonding版本3.7.0中添加的。

lp_interval

指定bonding驱动程序向每个从属接口的对等交换机发送学习报文之间的秒数。
有效范围是1到0x7fffffff；默认值为1。此选项仅在balance-tlb和balance-alb模式下生效。

3. 配置Bonding设备
==============================

您可以使用发行版的网络初始化脚本或手动使用iproute2或sysfs接口来配置bonding。发行版通常使用三种包之一进行网络初始化脚本：initscripts、sysconfig或interfaces。
这些包的较新版本支持bonding，而较旧版本则不支持。
我们将首先描述使用支持bonding的initscripts、sysconfig和interfaces版本配置bonding的选项，然后提供在没有网络初始化脚本支持的情况下启用bonding的信息（即，initscripts或sysconfig的较旧版本）。
如果你不确定你的发行版使用的是 `sysconfig`、`initscripts` 还是 `interfaces`，或者不知道它是否足够新，请不要担心。确定这一点相当简单。

首先，在 `/etc/network` 目录下查找一个名为 `interfaces` 的文件。
如果这个文件存在于你的系统中，那么你的系统使用的是 `interfaces`。请参阅“带有 `interfaces` 支持的配置”。

否则，执行以下命令：

	$ rpm -qf /sbin/ifup

它会返回一行文本，以 “initscripts” 或 “sysconfig” 开头，后面跟着一些数字。这是提供网络初始化脚本的包。
接下来，为了确定你的安装是否支持绑定（bonding），执行以下命令：

	$ grep ifenslave /sbin/ifup

如果这返回了任何匹配项，则表明你的 `initscripts` 或 `sysconfig` 支持绑定。

### 3.1 带有 `sysconfig` 支持的配置
------------------------

这一节适用于使用带有绑定支持的 `sysconfig` 版本的发行版，例如 SuSE Linux Enterprise Server 9。
SuSE SLES 9 的网络配置系统确实支持绑定，但是截至本文撰写时，YaST 系统配置前端没有提供任何用于管理绑定设备的方法。
然而，可以手动管理绑定设备，具体步骤如下：
首先，如果这些设备尚未配置，请配置从设备（slave devices）。在 SLES 9 上，最简单的方法是运行 `yast2` 配置工具。目标是为每个从设备创建一个 `ifcfg-id` 文件。最简单的方法是将这些设备配置为使用 DHCP（这只是为了创建 `ifcfg-id` 文件；下面会提到一些关于 DHCP 的问题）。每个设备的配置文件名称形式如下：

    ifcfg-id-xx:xx:xx:xx:xx:xx

其中，“xx”部分会被该设备的永久 MAC 地址的数字替换。
一旦创建了 ifcfg-id-xx:xx:xx:xx:xx:xx 文件集，就需要编辑从设备（MAC 地址对应于从设备的 MAC 地址）的配置文件。在编辑之前，文件将包含多行内容，看起来类似于这样：

```
BOOTPROTO='dhcp'
STARTMODE='on'
USERCTL='no'
UNIQUE='XNzu.WeZGOGF+4wE'
_nm_name='bus-pci-0001:61:01.0'
```

将 BOOTPROTO 和 STARTMODE 行更改为以下内容：

```
BOOTPROTO='none'
STARTMODE='off'
```

不要更改 UNIQUE 或 _nm_name 行。删除其他所有行（如 USERCTL 等）。

一旦修改了 ifcfg-id-xx:xx:xx:xx:xx:xx 文件，就可以创建绑定设备本身的配置文件了。这个文件名为 ifcfg-bondX，其中 X 是要创建的绑定设备的编号，从 0 开始。第一个这样的文件是 ifcfg-bond0，第二个是 ifcfg-bond1，依此类推。sysconfig 网络配置系统能够正确启动多个绑定实例。

ifcfg-bondX 文件的内容如下：

```
BOOTPROTO="static"
BROADCAST="10.0.2.255"
IPADDR="10.0.2.10"
NETMASK="255.255.0.0"
NETWORK="10.0.2.0"
REMOTE_IPADDR=""
STARTMODE="onboot"
BONDING_MASTER="yes"
BONDING_MODULE_OPTS="mode=active-backup miimon=100"
BONDING_SLAVE0="eth0"
BONDING_SLAVE1="bus-pci-0000:06:08.1"
```

将示例中的 BROADCAST、IPADDR、NETMASK 和 NETWORK 值替换为适合您网络的实际值。

STARTMODE 指定了设备上线的时间。可能的值如下：

| 值       | 描述                                                                                     |
|----------|------------------------------------------------------------------------------------------|
| onboot   | 设备在启动时启动。如果您不确定，这可能是您想要的选项。                                     |
| manual   | 只有当手动调用 ifup 时才启动设备。如果由于某些原因不希望设备在启动时自动启动，可以配置为这种方式。 |
| hotplug  | 设备由热插拔事件启动。这不是绑定设备的有效选择。                                           |
| off 或 ignore | 忽略设备配置。                                                                            |

BONDING_MASTER='yes' 表明该设备是一个绑定主设备。唯一有用的值是 "yes"。

BONDING_MODULE_OPTS 的内容提供给此设备的绑定模块实例。在这里指定绑定模式、链路监控等选项。不要包括 max_bonds 参数；如果您有多个绑定设备，这会混淆配置系统。
最后，为每个从设备提供一个 `BONDING_SLAVEn="slave device"` 的配置项，其中 "n" 是一个递增的值，对应于每个从设备。"slave device" 可以是接口名称（例如 "eth0"），也可以是网络设备的设备标识符。接口名称更容易查找，但 ethN 名称在启动时可能会改变（如果序列中的某个早期设备出现故障）。设备标识符（如上面示例中的 bus-pci-0000:06:08.1）指定了物理网络设备，并且只有在网络设备的总线位置改变（例如，从一个 PCI 插槽移到另一个插槽）时才会改变。上面的示例中每种类型都使用了一个，而大多数配置会选择一种类型用于所有从设备。

当所有配置文件修改或创建完成后，必须重启网络以使配置更改生效。可以通过以下命令实现：

    # /etc/init.d/network restart

请注意，网络控制脚本（/sbin/ifdown）会在网络关闭处理过程中卸载 bonding 模块，因此如果模块参数已更改，则无需手动卸载模块。

另外，在撰写本文时，YaST/YaST2 不会管理 bonding 设备（它们不会在列出的网络设备中显示 bonding 接口）。需要手动编辑配置文件以更改 bonding 配置。

关于 ifcfg 文件格式的其他通用选项和详细信息可以在示例 ifcfg 模板文件中找到：

    /etc/sysconfig/network/ifcfg.template

请注意，模板没有记录上述各种 ``BONDING_*`` 设置，但描述了其他许多选项。

3.1.1 在 Sysconfig 中使用 DHCP
--------------------------------

在 Sysconfig 下，将设备配置为 BOOTPROTO='dhcp' 将使其向 DHCP 查询其 IP 地址信息。在撰写本文时，这不适用于 bonding 设备；脚本试图在添加任何从设备之前获取设备地址。由于没有活动的从设备，DHCP 请求不会发送到网络。

3.1.2 使用 Sysconfig 配置多个 bonding 设备
---------------------------------------------

Sysconfig 网络初始化系统能够处理多个 bonding 设备。只需要为每个 bonding 实例提供适当配置的 ifcfg-bondX 文件（如上所述）。不要为任何 bonding 实例指定 "max_bonds" 参数，因为这会导致 Sysconfig 混乱。如果您需要具有相同参数的多个 bonding 设备，请创建多个 ifcfg-bondX 文件。

由于 Sysconfig 脚本在 ifcfg-bondX 文件中提供了 bonding 模块选项，因此不需要将它们添加到系统的 `/etc/modules.d/*.conf` 配置文件中。

3.2 使用支持 Initscripts 的配置
-----------------------------------

本节适用于使用较新版本的 initscripts 并支持 bonding 的发行版，例如 Red Hat Enterprise Linux 3 或更高版本、Fedora 等。在这些系统上，网络初始化脚本了解 bonding，并可以配置为控制 bonding 设备。请注意，旧版本的 initscripts 包对 bonding 的支持程度较低；在适用的情况下会进行说明。

这些发行版不会自动加载网络适配器驱动程序，除非 ethX 设备配置了 IP 地址。由于这个限制，用户必须手动配置一个网络脚本文件，用于所有将成为 bondX 链路成员的物理适配器。网络脚本文件位于目录中：

/etc/sysconfig/network-scripts

文件名必须以 "ifcfg-eth" 开头，并以适配器的物理编号结尾。例如，eth0 的脚本名为 /etc/sysconfig/network-scripts/ifcfg-eth0。
将以下文本放入文件中：

	DEVICE=eth0
	USERCTL=no
	ONBOOT=yes
	MASTER=bond0
	SLAVE=yes
	BOOTPROTO=none

`DEVICE=`行对于每个ethX设备都不同，并且必须与文件名称对应，例如，ifcfg-eth1 必须有 `DEVICE=eth1`。`MASTER=` 行的设置也将取决于您选择的最终绑定接口名称。与其他网络设备一样，这些通常从0开始，并且每个设备递增一个数字，即第一个绑定实例是 bond0，第二个是 bond1，依此类推。
接下来，创建一个绑定网络脚本。此脚本的文件名为 `/etc/sysconfig/network-scripts/ifcfg-bondX`，其中 X 是绑定编号。对于 bond0，文件名为 "ifcfg-bond0"；对于 bond1，文件名为 "ifcfg-bond1"，以此类推。在该文件中，放置以下文本：

	DEVICE=bond0
	IPADDR=192.168.1.1
	NETMASK=255.255.255.0
	NETWORK=192.168.1.0
	BROADCAST=192.168.1.255
	ONBOOT=yes
	BOOTPROTO=none
	USERCTL=no

请确保更改网络特定行（IPADDR、NETMASK、NETWORK 和 BROADCAST）以匹配您的网络配置。
对于较新版本的 initscripts（如 Fedora 7 或更高版本以及 Red Hat Enterprise Linux 5 或更高版本），可以并且确实更优选地在 ifcfg-bond0 文件中指定绑定选项，例如：

  BONDING_OPTS="mode=active-backup arp_interval=60 arp_ip_target=192.168.1.254"

这将使用指定的选项配置绑定。BONDING_OPTS 中指定的选项与绑定模块参数相同，但使用旧版 initscripts（版本小于 8.57（Fedora 8）和 8.45.19（Red Hat Enterprise Linux 5.2））时，arp_ip_target 字段有所不同。使用旧版本时，每个目标应作为单独的选项包含，并且应在前面加上 '+' 以表示应将其添加到查询目标列表中，例如：

    arp_ip_target=+192.168.1.1 arp_ip_target=+192.168.1.2

这是指定多个目标的正确语法。当通过 BONDING_OPTS 指定选项时，不需要编辑 `/etc/modprobe.d/*.conf`。
对于不支持 BONDING_OPTS 的更旧版本的 initscripts，需要根据您的发行版编辑 `/etc/modprobe.d/*.conf`，以便在 bond0 接口启动时加载绑定模块并选择其选项。`/etc/modprobe.d/*.conf` 中的以下行将加载绑定模块，并选择其选项：

	alias bond0 bonding
	options bond0 mode=balance-alb miimon=100

将示例参数替换为适用于您配置的一组选项。
最后，以 root 用户身份运行 “/etc/rc.d/init.d/network restart”。这将重启网络子系统，您的绑定链接现在应该已经启动并运行。

### 3.2.1 使用 initscripts 配置 DHCP
---------------------------------

较新版本的 initscripts（已报告的版本包括 Fedora Core 3 和 Red Hat Enterprise Linux 4 及更高版本）支持通过 DHCP 分配 IP 信息给绑定设备。
要为 DHCP 配置绑定，请按照上述方法进行配置，只是将 “BOOTPROTO=none” 替换为 “BOOTPROTO=dhcp”，并添加一行 “TYPE=Bonding”。请注意，TYPE 值区分大小写。

### 3.2.2 使用 initscripts 配置多个绑定
--------------------------------------------

Fedora 7 和 Red Hat Enterprise Linux 5 中包含的 initscripts 包通过简单地在 ifcfg-bondX 中指定适当的 BONDING_OPTS= 来支持多个绑定接口，其中 X 是绑定编号。此支持要求内核中的 sysfs 支持，并且需要版本 3.0.0 或更高版本的绑定驱动程序。其他配置可能不支持此方法来指定多个绑定接口；对于这些情况，请参见下面的“手动配置多个绑定”部分。

### 3.3 使用 iproute2 手动配置绑定
-----------------------------------

本节适用于那些网络初始化脚本（sysconfig 或 initscripts 包）没有具体绑定知识的发行版。一个这样的发行版是 SuSE Linux Enterprise Server 版本 8。
这些系统的通用方法是将绑定模块参数放入 `/etc/modprobe.d/` 目录中的配置文件（根据所安装的发行版进行适当配置），然后在系统的全局初始化脚本中添加 `modprobe` 和/或 `ip link` 命令。全局初始化脚本的名称有所不同；对于 sysconfig，它是 `/etc/init.d/boot.local`，而对于 initscripts，则是 `/etc/rc.d/rc.local`。例如，如果你想创建两个 e100 设备（假定为 eth0 和 eth1）的简单绑定，并使其在重启后仍然生效，编辑相应的文件（`/etc/init.d/boot.local` 或 `/etc/rc.d/rc.local`），并添加以下内容：

```
modprobe bonding mode=balance-alb miimon=100
modprobe e100
ifconfig bond0 192.168.1.1 netmask 255.255.255.0 up
ip link set eth0 master bond0
ip link set eth1 master bond0
```

请将示例中的绑定模块参数和 bond0 网络配置（如 IP 地址、子网掩码等）替换为适合你配置的相应值。

不幸的是，这种方法无法提供对绑定设备上的 `ifup` 和 `ifdown` 脚本的支持。要重新加载绑定配置，需要运行初始化脚本，例如：

```
# /etc/init.d/boot.local
```

或者：

```
# /etc/rc.d/rc.local
```

在这种情况下，可能希望创建一个单独的脚本来仅初始化绑定配置，然后从 `boot.local` 中调用该脚本。这允许在不重新运行整个全局初始化脚本的情况下启用绑定。

要关闭绑定设备，首先需要将绑定设备本身标记为关闭状态，然后卸载相应的设备驱动模块。对于上面的例子，可以执行以下操作：

```
# ifconfig bond0 down
# rmmod bonding
# rmmod e100
```

同样，出于方便考虑，可能希望创建一个包含这些命令的脚本。

### 3.3.1 手动配置多个绑定

本节包含有关配置具有不同选项的多个绑定设备的信息，适用于那些网络初始化脚本缺乏支持多个绑定的系统。

如果你需要多个绑定设备，但所有都使用相同的选项，你可能希望使用上述文档中的 "max_bonds" 模块参数。

为了创建具有不同选项的多个绑定设备，最好使用 sysfs 导出的绑定参数，如下文所述。

对于没有 sysfs 支持的绑定版本，唯一的方法是在加载绑定驱动时多次加载。请注意，当前版本的 sysconfig 网络初始化脚本会自动处理这种情况；如果你的发行版使用这些脚本，则无需特别操作。如果你不确定自己的网络初始化脚本，请参阅上述“配置绑定设备”部分。

要加载多个实例的模块，需要为每个实例指定不同的名称（模块加载系统要求每个加载的模块，即使多次加载同一模块，也必须有唯一的名称）。这可以通过在 `/etc/modprobe.d/*.conf` 中提供多组绑定选项来实现，例如：

``` 
alias bond0 bonding
options bond0 -o bond0 mode=balance-rr miimon=100

alias bond1 bonding
options bond1 -o bond1 mode=balance-alb miimon=50
```

这将加载两次绑定模块。第一个实例命名为 "bond0" 并以 balance-rr 模式创建 bond0 设备，miimon 设置为 100。第二个实例命名为 "bond1" 并以 balance-alb 模式创建 bond1 设备，miimon 设置为 50。

在某些情况下（通常在较旧的发行版中），上述方法不起作用，第二个绑定实例从未看到其选项。在这种情况下，可以将第二行选项替换为：

```
install bond1 /sbin/modprobe --ignore-install bonding -o bond1 mode=balance-alb miimon=50
```

此步骤可重复任意次数，每次替换为一个新的唯一名称。
已经观察到某些由 Red Hat 提供的内核无法在加载时重命名模块（即 "-o bond1" 部分）。尝试将此选项传递给 modprobe 将产生“操作不允许”错误。这个问题已经在一些 Fedora Core 内核上被报告，并且在 RHEL 4 上也观察到了。对于表现出此问题的内核，将无法配置具有不同参数的多个网卡绑定（因为这些是旧版本内核，并且也不支持 sysfs）。

3.4 通过 Sysfs 手动配置网卡绑定
------------------------------------------

从版本 3.0.0 开始，可以使用 sysfs 接口来配置网卡绑定。此接口允许在不卸载模块的情况下动态配置系统中的所有绑定，并且还允许在运行时添加和删除绑定。尽管 ifenslave 不再必需，但它仍然得到支持。

使用 sysfs 接口可以让您在不重新加载模块的情况下使用具有不同配置的多个绑定。即使当网卡绑定被编译进内核时，这也允许您使用多个具有不同配置的绑定。

要以这种方式配置网卡绑定，必须挂载 sysfs 文件系统。本文档中的示例假设您使用的是 sysfs 的标准挂载点，例如 /sys。如果您的 sysfs 文件系统挂载在其他位置，则需要相应地调整示例路径。

创建和销毁绑定
-----------------

要添加一个新的绑定 foo：

```
# echo +foo > /sys/class/net/bonding_masters
```

要移除一个现有的绑定 bar：

```
# echo -bar > /sys/class/net/bonding_masters
```

要显示所有现有的绑定：

```
# cat /sys/class/net/bonding_masters
```

**注意：**

由于 sysfs 文件大小限制为 4KB，如果您的绑定数量超过几百个，这个列表可能会被截断。这在正常运行条件下不太可能发生。

添加和移除从属接口
--------------------------

可以使用文件 `/sys/class/net/<bond>/bonding/slaves` 来将接口绑定到某个绑定。该文件的语义与 `bonding_masters` 文件相同。

要将接口 eth0 绑定到绑定 bond0：

```
# ifconfig bond0 up
# echo +eth0 > /sys/class/net/bond0/bonding/slaves
```

要从绑定 bond0 中释放从属接口 eth0：

```
# echo -eth0 > /sys/class/net/bond0/bonding/slaves
```

当一个接口被绑定到一个绑定时，在 sysfs 文件系统中会在这两者之间创建符号链接。在这种情况下，您将获得 `/sys/class/net/bond0/slave_eth0` 指向 `/sys/class/net/eth0`，以及 `/sys/class/net/eth0/master` 指向 `/sys/class/net/bond0`。

这意味着您可以快速判断一个接口是否已被绑定，方法是查看 `master` 符号链接。因此：
```
# echo -eth0 > /sys/class/net/eth0/master/bonding/slaves
```
将从其绑定的任何绑定中释放 eth0，无论绑定接口的名称是什么。
更改网卡绑定的配置
-------------------------------
可以通过操作位于 `/sys/class/net/<bond name>/bonding` 目录下的文件来单独配置每个网卡绑定。

这些文件名直接对应于本文档其他地方描述的命令行参数，并且除了 `arp_ip_target` 外，它们接受相同的值。要查看当前设置，只需使用 `cat` 命令读取相应的文件。
下面给出一些示例；对于每个参数的具体用法指南，请参阅本文档中的相应部分。
配置 `bond0` 使用 `balance-alb` 模式：

	# ifconfig bond0 down
	# echo 6 > /sys/class/net/bond0/bonding/mode
	- 或者 -
	# echo balance-alb > /sys/class/net/bond0/bonding/mode

.. 注意::
   
   在更改模式之前，绑定接口必须处于关闭状态。
启用 `bond0` 的 MII 监控，间隔为 1 秒：

	# echo 1000 > /sys/class/net/bond0/bonding/miimon

.. 注意::
   
   如果启用了 ARP 监控，在启用 MII 监控时会将其禁用，反之亦然。
添加 ARP 目标地址：

	# echo +192.168.0.100 > /sys/class/net/bond0/bonding/arp_ip_target
	# echo +192.168.0.101 > /sys/class/net/bond0/bonding/arp_ip_target

.. 注意::
   
   最多可以指定 16 个目标地址。
移除一个 ARP 目标：

	# echo -192.168.0.100 > /sys/class/net/bond0/bonding/arp_ip_target

配置学习包发送的间隔：

	# echo 12 > /sys/class/net/bond0/bonding/lp_interval

.. 注意::
   
   `lp_interval` 是绑定驱动程序向每个从属交换机发送学习包之间的时间间隔（以秒为单位）。默认间隔是 1 秒。
示例配置
---------------------
我们从第 3.3 节中展示的相同示例开始，通过 sysfs 执行，而不使用 `ifenslave`。
为了创建两个 `e100` 设备（假定为 `eth0` 和 `eth1`）的简单绑定，并使其在重启后仍然生效，编辑相应的文件（如 `/etc/init.d/boot.local` 或 `/etc/rc.d/rc.local`），并添加以下内容：

	modprobe bonding
	modprobe e100
	echo balance-alb > /sys/class/net/bond0/bonding/mode
	ifconfig bond0 192.168.1.1 netmask 255.255.255.0 up
	echo 100 > /sys/class/net/bond0/bonding/miimon
	echo +eth0 > /sys/class/net/bond0/bonding/slaves
	echo +eth1 > /sys/class/net/bond0/bonding/slaves

为了添加第二个绑定，其中包含两个 `e1000` 接口，并采用 `active-backup` 模式以及 ARP 监控，需在初始化脚本中添加以下行：

	modprobe e1000
	echo +bond1 > /sys/class/net/bonding_masters
	echo active-backup > /sys/class/net/bond1/bonding/mode
	ifconfig bond1 192.168.2.1 netmask 255.255.255.0 up
	echo +192.168.2.100 > /sys/class/net/bond1/bonding/arp_ip_target
	echo 2000 > /sys/class/net/bond1/bonding/arp_interval
	echo +eth2 > /sys/class/net/bond1/bonding/slaves
	echo +eth3 > /sys/class/net/bond1/bonding/slaves

3.5 支持接口的配置
-----------------------------------------

此节适用于使用 `/etc/network/interfaces` 文件来描述网络接口配置的发行版，尤其是 Debian 及其衍生版本。
Debian 中的 `ifup` 和 `ifdown` 命令不支持绑定功能。需要安装 `ifenslave-2.6` 包来提供绑定支持。安装该包后，将提供 `bond-*` 选项用于 `/etc/network/interfaces` 文件中。
请注意，`ifenslave-2.6` 包将加载绑定模块，并在适当情况下使用 `ifenslave` 命令。
示例配置
----------------------

在 `/etc/network/interfaces` 中，以下段落将配置处于主备模式的 bond0，并指定 eth0 和 eth1 作为从设备：

```plaintext
auto bond0
iface bond0 inet dhcp
    bond-slaves eth0 eth1
    bond-mode active-backup
    bond-miimon 100
    bond-primary eth0 eth1
```

如果上述配置不起作用，那么您的系统可能使用了 upstart 进行系统启动。这在最近版本的 Ubuntu 中尤为常见。在 `/etc/network/interfaces` 中的以下段落将在这些系统上产生相同的效果：

```plaintext
auto bond0
iface bond0 inet dhcp
    bond-slaves none
    bond-mode active-backup
    bond-miimon 100

auto eth0
iface eth0 inet manual
    bond-master bond0
    bond-primary eth0 eth1

auto eth1
iface eth1 inet manual
    bond-master bond0
    bond-primary eth0 eth1
```

有关 `/etc/network/interfaces` 中支持的所有 `bond-*` 选项及适用于特定发行版的一些高级示例，请参阅 `/usr/share/doc/ifenslave-2.6` 目录中的文件。

3.6 特殊情况下的配置覆盖
----------------------------------------------

当使用 bonding 驱动程序时，发送帧所使用的物理端口通常由 bonding 驱动程序选择，与用户或系统管理员无关。输出端口是根据选定的 bonding 模式策略来选择的。然而，在某些情况下，将特定类别的流量导向特定的物理接口以实现稍微复杂的策略是有帮助的。例如，要通过一个绑定接口访问一个 Web 服务器，其中 eth0 连接到私有网络而 eth1 通过公共网络连接，则可能希望优先通过 eth0 发送此类流量，仅在 eth0 不可用时才使用 eth1，而其他所有流量都可以安全地通过任一接口发送。这样的配置可以通过 Linux 内置的流量控制工具来实现。

默认情况下，bonding 驱动程序是多队列感知的，并且在驱动程序初始化时会创建 16 个队列（详见 `Documentation/networking/multiqueue.rst`）。如果需要更多或更少的队列，可以使用模块参数 `tx_queues` 来更改这个值。由于分配是在模块初始化时完成的，因此没有相应的 sysfs 参数。

文件 `/proc/net/bonding/bondX` 的输出已发生变化，现在为每个从设备打印出队列 ID：

```plaintext
Bonding Mode: fault-tolerance (active-backup)
Primary Slave: None
Currently Active Slave: eth0
MII Status: up
MII Polling Interval (ms): 0
Up Delay (ms): 0
Down Delay (ms): 0

Slave Interface: eth0
MII Status: up
Link Failure Count: 0
Permanent HW addr: 00:1a:a0:12:8f:cb
Slave queue ID: 0

Slave Interface: eth1
MII Status: up
Link Failure Count: 0
Permanent HW addr: 00:1a:a0:12:8f:cc
Slave queue ID: 2
```

可以通过以下命令设置从设备的队列 ID：

```plaintext
# echo "eth1:2" > /sys/class/net/bond0/bonding/queue_id
```

任何需要设置队列 ID 的接口都应通过多次调用类似上述命令的方式，直到为所有接口设置正确的优先级为止。在允许通过 initscripts 配置的发行版中，可以在 `BONDING_OPTS` 中添加多个 `queue_id` 参数以设置所有所需的从设备队列。

这些队列 ID 可以与 `tc` 工具结合使用，配置一个多队列 qdisc 和过滤器，以便将某些流量偏移到特定的从设备。例如，假设我们希望在上述配置中将所有发往 192.168.1.100 的流量强制通过 bond0 接口中的 eth1 发送，以下命令可以实现这一目标：

```plaintext
# tc qdisc add dev bond0 handle 1 root multiq

# tc filter add dev bond0 protocol ip parent 1: prio 1 u32 match ip \
    dst 192.168.1.100 action skbedit queue_mapping 2
```

这些命令告诉内核在 bond0 接口上附加一个多队列队列纪律并过滤其上的排队流量，使得目标 IP 地址为 192.168.1.100 的数据包其输出队列映射值被重写为 2。

此值随后传递给驱动程序，导致正常的输出路径选择策略被覆盖，选择 qid 2，即 eth1。

需要注意的是，qid 值从 1 开始。qid 0 是保留的，用于指示驱动程序应该执行正常的输出策略选择。简单地将从设备的 qid 设置为 0 的好处之一是，现在 bonding 驱动程序具有多队列感知能力。这种感知能力允许在从设备以及绑定设备上放置 tc 过滤器，而 bonding 驱动程序只是作为选择从设备上的输出队列而不是输出端口的选择的通道。

此功能首次出现在 bonding 驱动程序版本 3.7.0 中，并且输出从设备选择的支持仅限于轮询和主备模式。

3.7 以更安全的方式配置 802.3ad 模式的 LACP
----------------------------------------------------------

当使用 802.3ad bonding 模式时，Actor（主机）和 Partner（交换机）之间交换 LACPDUs。这些 LACPDUs 无法被嗅探，因为它们的目标是链路本地 MAC 地址（交换机/网桥不应转发）。然而，大多数值很容易预测或仅仅是机器的 MAC 地址（这可以轻易地被同一层内的所有其他主机知道）。这意味着同一 L2 域中的其他机器可以伪造其他主机的 LACPDU 包发送到交换机，从而可能造成混乱，例如从交换机的角度来看加入另一台机器的聚合，从而接收该主机的部分传入流量或自己伪造该主机的流量（甚至可能成功终止部分流量）。尽管这种情况不太可能发生，但可以通过简单配置几个 bonding 参数来避免这种可能性：

(a) `ad_actor_system`：您可以设置一个随机 MAC 地址，用于这些 LACPDU 交换。该值不能为 NULL 或多播地址。同时建议设置本地管理位。以下 Shell 脚本生成一个随机 MAC 地址：

```plaintext
# sys_mac_addr=$(printf '%02x:%02x:%02x:%02x:%02x:%02x' \
    $(( (RANDOM & 0xFE) | 0x02 )) \
    $(( RANDOM & 0xFF )) \
    $(( RANDOM & 0xFF )) \
    $(( RANDOM & 0xFF )) \
    $(( RANDOM & 0xFF )) \
    $(( RANDOM & 0xFF )))
# echo $sys_mac_addr > /sys/class/net/bond0/bonding/ad_actor_system
```

(b) `ad_actor_sys_prio`：随机化系统优先级。默认值为 65535，但系统可以取值 1 到 65535。以下 Shell 脚本生成随机优先级并设置它：

```plaintext
# sys_prio=$(( 1 + RANDOM + RANDOM ))
# echo $sys_prio > /sys/class/net/bond0/bonding/ad_actor_sys_prio
```

(c) `ad_user_port_key`：使用端口密钥的用户部分。默认情况下保持为空。这是端口密钥的高 10 位，取值范围为 0 到 1023。以下 Shell 脚本生成这 10 位并设置它：

```plaintext
# usr_port_key=$(( RANDOM & 0x3FF ))
# echo $usr_port_key > /sys/class/net/bond0/bonding/ad_user_port_key
```

4 查询 bonding 配置
==================

4.1 Bonding 配置
-------------------------

每个 bonding 设备在 `/proc/net/bonding` 目录下都有一个只读文件。文件内容包括关于 bonding 配置、选项和每个从设备状态的信息。
例如，在使用参数 `mode=0` 和 `miimon=1000` 加载驱动程序后，`/proc/net/bonding/bond0` 的内容通常如下所示：

```
以太网通道绑定驱动程序：2.6.1（2004年10月29日）
绑定模式：负载平衡（轮询）
当前活动从设备：eth0
MII 状态：正常
MII 检查间隔（毫秒）：1000
启动延迟（毫秒）：0
关闭延迟（毫秒）：0

从设备接口：eth1
MII 状态：正常
链路故障计数：1

从设备接口：eth0
MII 状态：正常
链路故障计数：1
```

具体的格式和内容会根据绑定配置、状态以及绑定驱动程序的版本而变化。

### 4.2 网络配置

可以使用 `ifconfig` 命令检查网络配置。绑定设备将设置 `MASTER` 标志；绑定从设备将设置 `SLAVE` 标志。`ifconfig` 输出不包含哪些从设备与哪些主设备关联的信息。在下面的例子中，`bond0` 接口是主设备（`MASTER`），而 `eth0` 和 `eth1` 是从设备（`SLAVE`）。请注意所有 `bond0` 的从设备除了 TLB 和 ALB 模式外，都具有与 `bond0` 相同的 MAC 地址（`HWaddr`），这两种模式要求每个从设备有唯一的 MAC 地址：

```
# /sbin/ifconfig
bond0     链接封装：以太网  硬件地址：00:C0:F0:1F:37:B4
          IP 地址：XXX.XXX.XXX.YYY  广播地址：XXX.XXX.XXX.255  子网掩码：255.255.252.0
          启动 广播 运行 主设备 多播  MTU：1500  度量：1
          接收数据包：7224794 错误：0 丢弃：0 超时：0 帧错误：0
          发送数据包：3286647 错误：1 丢弃：0 超时：1 载波错误：0
          碰撞：0 发送队列长度：0

eth0      链接封装：以太网  硬件地址：00:C0:F0:1F:37:B4
          启动 广播 运行 从设备 多播  MTU：1500  度量：1
          接收数据包：3573025 错误：0 丢弃：0 超时：0 帧错误：0
          发送数据包：1643167 错误：1 丢弃：0 超时：1 载波错误：0
          碰撞：0 发送队列长度：100
          中断：10 基地址：0x1080

eth1      链接封装：以太网  硬件地址：00:C0:F0:1F:37:B4
          启动 广播 运行 从设备 多播  MTU：1500  度量：1
          接收数据包：3651769 错误：0 丢弃：0 超时：0 帧错误：0
          发送数据包：1643480 错误：0 丢弃：0 超时：0 载波错误：0
          碰撞：0 发送队列长度：100
          中断：9 基地址：0x1400
```

### 5. 交换机配置

对于本节，“交换机”指的是绑定设备直接连接的系统（即，电缆另一端插入的地方）。这可能是一个实际的专用交换机设备，也可能是一台普通的系统（例如，另一台运行 Linux 的计算机）。

- 主备模式（active-backup）、负载均衡 TLB 模式（balance-tlb）和负载均衡 ALB 模式（balance-alb）不需要对交换机进行任何特定配置。
- 802.3ad 模式需要交换机将相应的端口配置为 802.3ad 聚合。具体配置方法因交换机而异，但例如 Cisco 3550 系列交换机需要首先将相应的端口组合在一个以太通道实例中，然后将该以太通道设置为“lacp”模式以启用 802.3ad（而不是标准的以太通道）。
- 轮询模式（balance-rr）、XOR 模式（balance-xor）和广播模式（broadcast）通常需要交换机将相应的端口组合在一起。这种组合的命名因交换机而异，可能是“以太通道”（如上述 Cisco 示例）、“链路组”或其他类似变体。对于这些模式，每个交换机还将有自己的配置选项来指定交换机到绑定设备的传输策略。典型的选择包括 MAC 地址或 IP 地址的 XOR。两个对等设备的传输策略不必匹配。对于这三种模式，绑定模式实际上选择了一个以太通道组的传输策略；所有三种模式都可以与其他以太通道组互操作。

### 6. 802.1q VLAN 支持

可以通过 8021q 驱动程序在绑定接口上配置 VLAN 设备。但是，默认情况下只有来自 8021q 驱动程序并通过绑定传递的数据包会被标记。例如，绑定的自动生成的数据包，如学习数据包或 ALB 模式或 ARP 监控机制生成的 ARP 数据包，会在内部由绑定自身进行标记。因此，绑定必须“学习”在其上方配置的 VLAN ID，并使用这些 ID 来标记自动生成的数据包。

为了简化和支持能够进行 VLAN 硬件加速卸载的适配器的使用，绑定接口声明自己完全支持硬件卸载功能，它接收 `add_vid` 和 `kill_vid` 通知来收集必要的信息，并将这些操作传播到从设备。在混合适配器类型的情况下，应该通过无法卸载的适配器传输的硬件加速标记数据包会被绑定驱动程序“取消加速”，从而使 VLAN 标签位于常规位置。

VLAN 接口必须仅在至少绑定一个从设备之后添加到绑定接口之上。绑定接口在第一个从设备加入之前具有硬件地址 00:00:00:00:00:00。

如果在第一次绑定之前创建了 VLAN 接口，它将获取全零硬件地址。一旦第一个从设备附加到绑定，绑定设备本身将获取从设备的硬件地址，然后可用作 VLAN 设备。
此外，请注意，如果所有从设备从仍然包含一个或多个VLAN接口的链路聚合中释放，可能会出现类似的问题。当添加新的从设备时，链路聚合接口将从第一个从设备获取其硬件地址，这可能与VLAN接口的硬件地址不匹配（VLAN接口的硬件地址最终是从早期的一个从设备复制过来的）。

要确保在所有从设备被移除后VLAN设备使用正确的硬件地址，有两种方法：

1. 移除所有VLAN接口然后重新创建它们。
2. 设置链路聚合接口的硬件地址，使其与VLAN接口的硬件地址相匹配。

请注意，更改VLAN接口的硬件地址会将底层设备（即链路聚合接口）设置为混杂模式，这可能不是你想要的结果。

7. 链路监控
===========

目前，链路聚合驱动支持两种监控从设备链路状态的方案：ARP监控和MII监控。

由于链路聚合驱动本身的实现限制，目前无法同时启用ARP和MII监控。

7.1 ARP监控操作
-----------------

ARP监控如其名称所示：它向网络上的一个或多个指定对等系统发送ARP查询，并通过响应来判断链路是否正常工作。这可以提供一些保证，即流量实际上正在流向本地网络中的一个或多个对等系统。

7.2 配置多个ARP目标
--------------------

虽然ARP监控只需一个目标即可完成，但在高可用性环境中，监控多个目标是有用的。仅有一个目标的情况下，该目标本身可能会断开连接或出现问题，导致其对ARP请求无响应。增加额外的目标（或多个目标）可以提高ARP监控的可靠性。

多个ARP目标必须用逗号分隔，如下所示：

```
# 示例：具有三个目标的ARP监控选项
alias bond0 bonding
options bond0 arp_interval=60 arp_ip_target=192.168.0.1,192.168.0.3,192.168.0.9
```

对于单个目标，选项应类似于以下格式：

```
# 示例：具有一个目标的ARP监控选项
alias bond0 bonding
options bond0 arp_interval=60 arp_ip_target=192.168.0.100
```

7.3 MII监控操作
-----------------

MII监控只监控本地网络接口的载波状态。它通过以下三种方式之一来实现：依赖设备驱动程序维护其载波状态、查询设备的MII寄存器或通过ethtool查询设备。

如果use_carrier模块参数为1（默认值），则MII监控将依赖于驱动程序提供的载波状态信息（通过netif_carrier子系统）。如上所述，在use_carrier参数说明中，如果MII监控未能检测到设备的载波丢失（例如，当物理断开电缆时），可能是驱动程序不支持netif_carrier。

如果use_carrier设置为0，则MII监控将首先通过ioctl查询设备的MII寄存器并检查链路状态。如果该请求失败（不仅仅是返回载波已断开），MII监控将尝试通过ethtool ETHTOOL_GLINK请求获取相同的信息。如果这两种方法都失败（即，驱动程序既不支持也不正确处理MII寄存器和ethtool请求），则MII监控将假定链路是正常的。
### 8. 潜在的麻烦来源
=================================

#### 8.1 路由中的冒险
配置绑定时，重要的是从设备不应该有超越主设备路由的路由（或者通常来说，不应该有任何路由）。例如，假设绑定设备 bond0 有两个从设备 eth0 和 eth1，并且路由表如下所示：

```
内核 IP 路由表
目的地     网关           子网掩码             标志   MSS 窗口 irtt 接口
10.0.0.0    0.0.0.0        255.255.0.0          U      40 0      0  eth0
10.0.0.0    0.0.0.0        255.255.0.0          U      40 0      0  eth1
10.0.0.0    0.0.0.0        255.255.0.0          U      40 0      0  bond0
127.0.0.0   0.0.0.0        255.0.0.0            U      40 0      0  lo
```

这种路由配置可能会更新驱动程序中的接收/发送时间（这是 ARP 监控所需的），但可能会绕过绑定驱动程序（因为发往网络 10 的其他主机的出站流量会使用 eth0 或 eth1 而不是 bond0）。ARP 监控（和 ARP 本身）可能会被此配置搞糊涂，因为 ARP 请求（由 ARP 监控生成）将在一个接口上发送（bond0），但相应的回复将出现在另一个接口上（eth0）。这个回复对 ARP 来说像是一个未请求的 ARP 回复（因为 ARP 是基于接口匹配的），因此会被丢弃。MII 监控不受路由表状态的影响。

解决方法是确保从设备没有自己的路由，如果由于某种原因它们必须有，则这些路由不应超越其主设备的路由。这通常应该是这样，但不寻常的配置或错误的手动或自动静态路由添加可能会导致问题。

#### 8.2 以太网设备重命名
在那些网络配置脚本不直接将物理设备与网络接口名称关联的系统中（使得相同的物理设备始终具有相同的“ethX”名称），可能需要在 `/etc/modprobe.d/` 中的配置文件中添加一些特殊逻辑。
例如，给定一个包含以下内容的 `modules.conf`：

```conf
alias bond0 bonding
options bond0 mode=some-mode miimon=50
alias eth0 tg3
alias eth1 tg3
alias eth2 e1000
alias eth3 e1000
```

如果 eth0 和 eth1 都不是 bond0 的从设备，那么当 bond0 接口启动时，设备可能会重新排序。这是因为绑定首先加载，然后是其从设备的驱动程序。由于没有其他驱动程序加载，当 e1000 驱动程序加载时，它将为设备分配 eth0 和 eth1，但绑定配置试图将 eth2 和 eth3 设置为从设备（这些设备稍后可能被分配给 tg3 设备）。

添加以下内容：

```conf
add above bonding e1000 tg3
```

这会使 modprobe 在加载 bonding 时按顺序加载 e1000 和 tg3。此命令在 `modules.conf` 手册页中有完整文档。

在使用 modprobe 的系统中也会出现类似的问题。在这种情况下，可以在 `/etc/modprobe.d/` 中的配置文件中添加以下内容：

```conf
softdep bonding pre: tg3 e1000
```

这将在加载 bonding 之前加载 tg3 和 e1000 模块。有关此内容的完整文档可以在 `modprobe.d` 和 `modprobe` 手册页中找到。

#### 8.3 MII 监控器检测链路失败非常慢或无法检测到链路失败
默认情况下，绑定启用了 `use_carrier` 选项，该选项指示绑定信任驱动程序来维护载波状态。
如上文选项部分所述，某些驱动程序不支持 netif_carrier_on/_off 链路状态跟踪系统。在启用 use_carrier 的情况下，bonding（绑定）将始终认为这些链路是正常的，无论它们的实际状态如何。此外，还有一些驱动程序虽然支持 netif_carrier，但不会实时维护它，例如仅以固定间隔轮询链路状态。在这种情况下，miimon 将检测到故障，但需要经过一段时间。如果发现 miimon 在检测链路故障时非常缓慢，请尝试指定 use_carrier=0，看看这是否能改善故障检测时间。如果这样做确实有效，则可能是该驱动程序在固定间隔检查载波状态，但没有缓存 MII 寄存器值（因此直接查询寄存器的方法 use_carrier=0 起作用）。如果 use_carrier=0 不能改善故障切换，则可能是驱动程序缓存了寄存器，或者问题出现在其他地方。
另外，请记住 miimon 只检查设备的载波状态。它无法确定交换机其他端口上的设备状态或交换机在维持载波的同时拒绝传输的情况。

### 9. SNMP 代理

如果运行 SNMP 代理，bonding 驱动应该在任何参与绑定的网络驱动之前加载。这是因为接口索引（ipAdEntIfIndex）会关联到具有相同 IP 地址的第一个找到的接口。也就是说，每个 IP 地址只有一个 ipAdEntIfIndex。例如，如果 eth0 和 eth1 是 bond0 的从设备，并且 eth0 的驱动在 bonding 驱动之前加载，则 IP 地址的接口将与 eth0 接口相关联。下面显示了这种配置，IP 地址 192.168.1.1 的接口索引为 2，在 ifDescr 表中对应 eth0：
```
interfaces.ifTable.ifEntry.ifDescr.1 = lo
interfaces.ifTable.ifEntry.ifDescr.2 = eth0
interfaces.ifTable.ifEntry.ifDescr.3 = eth1
interfaces.ifTable.ifEntry.ifDescr.4 = eth2
interfaces.ifTable.ifEntry.ifDescr.5 = eth3
interfaces.ifTable.ifEntry.ifDescr.6 = bond0
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.10.10.10.10 = 5
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.192.168.1.1 = 2
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.10.74.20.94 = 4
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.127.0.0.1 = 1
```

通过在任何参与绑定的网络驱动之前加载 bonding 驱动可以避免这个问题。下面是首先加载 bonding 驱动的例子，IP 地址 192.168.1.1 正确地关联到了 ifDescr.2：
```
interfaces.ifTable.ifEntry.ifDescr.1 = lo
interfaces.ifTable.ifEntry.ifDescr.2 = bond0
interfaces.ifTable.ifEntry.ifDescr.3 = eth0
interfaces.ifTable.ifEntry.ifDescr.4 = eth1
interfaces.ifTable.ifEntry.ifDescr.5 = eth2
interfaces.ifTable.ifEntry.ifDescr.6 = eth3
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.10.10.10.10 = 6
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.192.168.1.1 = 2
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.10.74.20.94 = 5
ip.ipAddrTable.ipAddrEntry.ipAdEntIfIndex.127.0.0.1 = 1
```

尽管一些发行版可能不会在 ifDescr 中报告接口名称，但 IP 地址和 IfIndex 之间的关联仍然存在，SNMP 功能如 Interface_Scan_Next 会报告这种关联。

### 10. 混杂模式

在运行网络监控工具（如 tcpdump）时，通常会启用混杂模式，以便看到所有流量（而不仅仅是本地主机的目标流量）。bonding 驱动处理对绑定主设备（例如 bond0）的混杂模式更改，并将其设置传播到从设备。
对于 balance-rr、balance-xor、broadcast 和 802.3ad 模式，混杂模式设置会传播到所有从设备。
对于主动备份（active-backup）、负载平衡TLB（balance-tlb）和负载平衡ALB（balance-alb）模式，混杂模式设置仅传播到活动从设备。
对于balance-tlb模式，活动从设备是当前接收入站流量的从设备。
对于balance-alb模式，活动从设备被用作“主设备”。此从设备用于特定于模式的控制流量、发送未分配的对等点或在网络负载不平衡时使用。
对于主动备份、负载平衡TLB和负载平衡ALB模式，当活动从设备发生变化时（例如，由于链路故障），混杂模式设置将传播到新的活动从设备。

11. 配置高可用性（HA）绑定
============================

高可用性指的是通过冗余或备份设备、链路或交换机来提供最大网络可用性的配置。其目标是在任何情况下都能保证网络连接的最大可用性（即网络始终正常工作），尽管其他配置可能提供更高的吞吐量。

11.1 单交换机拓扑中的高可用性
--------------------------------

如果两个主机（或一个主机与一个单交换机）通过多个物理链路直接连接，则在优化最大带宽时不会影响可用性。在这种情况下，只有一个交换机（或对等点），因此如果它出现故障，没有其他选择可以切换。此外，绑定负载均衡模式支持对其成员进行链路监控，因此如果个别链路出现故障，负载将在剩余设备之间重新平衡。
有关配置单个对等设备的绑定以实现最大吞吐量的信息，请参阅第12节“配置绑定以实现最大吞吐量”。

11.2 多交换机拓扑中的高可用性
--------------------------------

在具有多个交换机的情况下，绑定配置和网络结构会发生显著变化。在多交换机拓扑中，网络可用性和可用带宽之间存在权衡。
以下是一个配置示例，旨在最大化网络的可用性：

```
		|                                     |
		|port3                           port3|
	  +-----+----+                          +-----+----+
	  |          |port2       ISL      port2|          |
	  | switch A +--------------------------+ switch B |
	  |          |                          |          |
	  +-----+----+                          +-----++---+
		|port1                           port1|
		|             +-------+               |
		+-------------+ host1 +---------------+
			 eth0 +-------+ eth1
```

在此配置中，两个交换机之间有一条链路（ISL，或交换机间链路），并且每个交换机都有多个端口连接到外部世界（每个交换机上的“port3”）。理论上，这种配置可以扩展到第三个交换机。

11.2.1 多交换机拓扑中的HA绑定模式选择
--------------------------------------

在上述拓扑中，当优化可用性时，主动备份（active-backup）和广播模式是唯一有用的绑定模式；其他模式要求所有链路都终止在同一对等点上，才能合理地工作。
### 主动-备份模式：
这是通常首选的模式，尤其是在交换机之间有ISL且协同工作良好的情况下。如果网络配置中某个交换机专门作为备份（例如容量较低、成本较高等），则可以使用主选项以确保在首选链路可用时始终使用该链路。

### 广播模式：
这种模式实际上是一种特殊用途模式，仅适用于非常具体的需求。例如，如果两个交换机没有连接（没有ISL），并且它们后面的网络完全独立。在这种情况下，如果需要某些特定的单向流量能够到达两个独立网络，则广播模式可能是合适的。

### 11.2.2 多交换机拓扑中的HA链路监控选择
---

链路监控的选择最终取决于您的交换机。如果交换机能够在其他故障发生时可靠地关闭端口，则MII或ARP监控都应有效。例如，在上述示例中，如果“port3”链路在远端出现故障，MII监控无法直接检测到这一点。而ARP监控可以在port3的远端设置一个目标，从而在不需要交换机支持的情况下检测到该故障。

然而，在多交换机拓扑中，ARP监控通常能提供更高的可靠性来检测端到端连接故障（这些故障可能是由任何组件因任何原因无法传输数据造成的）。此外，ARP监控应该配置多个目标（至少为网络中的每个交换机配置一个目标）。这样无论哪个交换机处于活动状态，ARP监控都有一个合适的目标进行查询。

此外，近期许多交换机支持一种称为“链路故障切换”的功能。这是一种当另一个交换机端口的状态变为不可用（或可用）时，导致特定交换机端口的状态也相应地变为不可用（或可用）的功能。其目的是将逻辑上“外部”端口的链路故障传播到逻辑上“内部”的端口，这些端口可以通过miimon进行监控。链路故障切换的可用性和配置因交换机而异，但在使用合适的交换机时，这可以作为ARP监控的一个可行替代方案。

### 12. 配置绑定以实现最大吞吐量
#### 12.1 在单一交换机拓扑中最大化吞吐量

在单一交换机配置中，最佳方法来最大化吞吐量取决于应用程序和网络环境。各种负载均衡模式在不同环境中各有优劣，具体如下：

为了讨论方便，我们将拓扑分为两类。根据大多数流量的目的地，我们可以将其分为“网关”配置或“本地”配置。

在网关配置中，“交换机”主要作为路由器，大部分流量通过此路由器传输到其他网络。例如：

```
+----------+                     +----------+
|          |eth0            port1|          | to other networks
| Host A   +---------------------+ router   +------------------->
|          +---------------------+          | Hosts B and C are out
|          |eth1            port2|          | here somewhere
+----------+                     +----------+
```

路由器可以是专用路由器设备，也可以是充当网关的另一台主机。对于我们的讨论，重要的一点是Host A的大部分流量将通过路由器传输到其他网络，然后才能到达其最终目的地。

在网关网络配置中，尽管Host A可能与其他许多系统通信，但所有流量都将通过本地网络上的另一个对等设备——路由器发送和接收。
请注意，两个系统通过多个物理链路直接连接的情况，在配置绑定时，与网关配置相同。在这种情况下，所有流量的目的地实际上是“网关”本身，而不是网关之外的其他网络。

在本地配置中，“交换机”主要作为交换机工作，大多数流量通过此交换机到达同一网络上的其他站。例如：

```
    +----------+            +----------+       +--------+
    |          |eth0   port1|          +-------+ Host B |
    |  Host A  +------------+  switch  |port3  +--------+
    |          +------------+          |                  +--------+
    |          |eth1   port2|          +------------------+ Host C |
    +----------+            +----------+port4             +--------+
```

再次说明，交换机可以是专用的交换设备，也可以是充当网关的另一台主机。对于我们讨论的重点在于，来自主机A的大多数流量目的地是同一本地网络上的其他主机（例如上述示例中的主机B和C）。

总之，在网关配置中，无论最终目的地如何，绑定设备的进出流量都将到达网络上的同一个MAC级别对等体（即网关本身，也就是路由器）。而在本地配置中，流量直接流向最终目的地，因此每个目的地（如主机B、主机C）将通过其各自的MAC地址直接寻址。

区分网关配置和本地网络配置很重要，因为许多可用的负载均衡模式使用本地网络源和目的的MAC地址来做出负载均衡决策。下面描述了每种模式的行为。

12.1.1 单交换机拓扑下的MT绑定模式选择
------------------------------------------

这种配置最容易设置和理解，尽管您需要决定哪种绑定模式最适合您的需求。每种模式的权衡如下：

balance-rr：
此模式是唯一允许单个TCP/IP连接跨多个接口条带化流量的模式。因此，这是唯一允许单个TCP/IP流利用多个接口吞吐量的模式。然而，这样做会带来一些代价：条带化通常会导致对等系统接收到错序的数据包，从而触发TCP/IP拥塞控制系统，通常表现为重传数据段。
可以通过调整net.ipv4.tcp_reordering sysctl参数来改变TCP/IP的拥塞限制。默认值通常是3。但请注意，TCP堆栈能够自动增加该值，当它检测到重排序时。
请注意，错序交付的数据包比例变化很大，并且不大可能是零。重排序的程度取决于多种因素，包括网络接口、交换机和配置的拓扑结构。一般而言，高速网络卡会产生更多的重排序（由于诸如包聚合等因素），并且“多对多”的拓扑结构比“多慢对一快”的配置会有更高的重排序率。
许多交换机不支持任何条带化流量的模式（而是根据IP或MAC级别的地址选择端口）；对于这些设备，特定连接通过交换机流向balance-rr绑定的流量不会利用超过一个接口的带宽。
如果您使用的是TCP/IP之外的协议，例如UDP，并且您的应用程序可以容忍错序交付，则此模式可以允许单个流数据报性能随着接口的增加而接近线性扩展。
此模式要求交换机适当配置“etherchannel”或“trunking”。

active-backup：
在此网络拓扑中，active-backup模式的优势不大，因为所有非活动备份设备都连接到与主设备相同的对等体。在这种情况下，带有链路监控的负载均衡模式将提供相同的网络可用性，但具有更高的可用带宽。另一方面，active-backup模式不需要任何交换机配置，因此如果可用硬件不支持任何负载均衡模式，则可能具有价值。
### balance-xor:
此模式将限制流量，使得发往特定对等点的数据包始终通过同一接口发送。由于目标是由涉及的MAC地址确定的，因此该模式最适合在“本地”网络配置中使用（如上所述），所有目的地都在同一个本地网络内。如果所有流量都通过单个路由器传输（即“网关”网络配置，如上所述），则该模式可能不是最佳选择。
与balance-rr一样，交换机端口需要配置为“etherchannel”或“trunking”。

### broadcast:
像active-backup一样，在这种网络拓扑中，此模式并没有太多优势。

### 802.3ad:
此模式对于这种网络拓扑来说是一个不错的选择。802.3ad模式是IEEE标准，因此实现802.3ad的所有对等点都应该能够良好互操作。802.3ad协议包括自动配置聚合，因此通常只需要少量手动配置交换机（通常是指定一组设备可用于802.3ad）。802.3ad标准还要求帧按照顺序传输（在一定范围内），因此一般来说单个连接不会看到数据包的乱序。802.3ad模式也有一些缺点：标准要求聚合中的所有设备以相同的速度和双工模式运行。此外，与其他bonding负载均衡模式（除了balance-rr）一样，没有单个连接能利用超过单个接口带宽的情况。
此外，Linux bonding 802.3ad实现通过对等点（使用MAC地址和包类型ID的XOR运算）分配流量，因此在“网关”配置中，所有传出流量通常会使用同一个设备。传入流量也可能最终在一个设备上，但这是由对等点的802.3ad实现的平衡策略决定的。在“本地”配置中，流量将在聚合中的设备之间分配。
最后，802.3ad模式强制使用MII监控，因此在这种模式下ARP监控不可用。

### balance-tlb:
balance-tlb模式根据对等点平衡传出流量。
由于平衡是根据MAC地址进行的，在“网关”配置中（如上所述），此模式会将所有流量发送到一个单一设备。然而，在“本地”网络配置中，此模式以一种稍微智能的方式在多个本地网络对等点之间平衡设备，因此数学上不幸运的MAC地址（即XOR结果相同的地址）不会全部集中在单个接口上。
与802.3ad不同，接口可以有不同的速度，并且不需要特殊配置交换机。不利之处在于，在此模式下所有传入流量都通过单一接口到达，此模式需要slave接口的网络设备驱动程序支持某些ethtool功能，并且ARP监控不可用。

### balance-alb:
此模式具有balance-tlb的所有功能（和限制），并且更多。
它具备balance-tlb的所有功能（和限制），并能够平衡来自本地网络对等点的传入流量（如上所述的Bonding Module Options部分）。
### 该模式的唯一额外缺点是网络设备驱动程序必须支持在设备打开时更改硬件地址。

#### 12.1.2 单交换机拓扑中的MT链路监控
------------------------------------

选择链路监控方式可能很大程度上取决于你选择使用的模式。更高级的负载均衡模式不支持ARP监控，因此只能使用MII监控（MII监控不能提供与ARP监控相同的端到端保证）。

#### 12.2 多交换机拓扑中的最大吞吐量
-------------------------------------

多个交换机可以用于优化吞吐量，当它们并行配置在一个隔离网络中，连接两台或多台系统时，例如：

```
		       +-----------+
		       |  Host A   |
		       +-+---+---+-+
			 |   |   |
		+--------+   |   +---------+
		|            |             |
	 +------+---+  +-----+----+  +-----+----+
	 | Switch A |  | Switch B |  | Switch C |
	 +------+---+  +-----+----+  +-----+----+
		|            |             |
		+--------+   |   +---------+
			 |   |   |
		       +-+---+---+-+
		       |  Host B   |
		       +-----------+
```

在这种配置中，交换机彼此隔离。使用这种拓扑的一个原因是为一个有许多主机的隔离网络（例如，配置为高性能集群），使用多个较小的交换机比使用单个较大的交换机更具成本效益。例如，在一个有24个主机的网络中，三个24端口的交换机比单个72端口的交换机便宜得多。

如果需要访问网络之外的资源，可以在一台主机上配备另一个连接到外部网络的网络设备；这台主机同时充当网关。

#### 12.2.1 多交换机拓扑中的MT绑定模式选择
-------------------------------------------------------------

实际上，在这种配置中通常使用的绑定模式是balance-rr。历史上，在这种网络配置中，关于乱序报文传递的常见警告可以通过使用不进行任何报文聚合（通过NAPI或设备本身直到收到一定数量的报文后才生成中断）的网络适配器来缓解。在这种情况下使用balance-rr模式，允许两台主机之间的个别连接有效利用超过一个接口的带宽。

#### 12.2.2 多交换机拓扑中的MT链路监控
------------------------------------------------------

实际上，在这种配置中，最常使用的是MII监控，因为性能优先于可用性。ARP监控在此拓扑中可以工作，但随着涉及的系统数量增加，所需的探测量会增加（请记住，网络中的每个主机都配置了绑定），这削弱了其相对于MII监控的优势。

### 13. 交换机行为问题
==========================

#### 13.1 链路建立和故障切换延迟
-------------------------------------------

一些交换机在报告链路上下状态时表现出不良行为。
首先，当链路建立时，某些交换机会指示链路已建立（载波可用），但在一段时间内不会传输数据。这种延迟通常是由于某种自动协商或路由协议造成的，也可能发生在交换机初始化期间（例如，在交换机故障恢复后）。如果你发现这是一个问题，可以指定一个适当的值给updelay绑定模块选项以延迟使用相关接口。
其次，某些交换机在链路状态变化时可能会多次“跳变”链路状态。这种情况最常发生在交换机初始化过程中。同样，适当的updelay值可能有所帮助。
请注意，当一个绑定接口没有活动链接时，驱动程序会立即重用第一个建立的链接，即使指定了updelay参数（在这种情况下，updelay参数会被忽略）。如果有从属接口等待updelay超时到期，则会立即重用最先进入该状态的接口。这减少了网络停机时间，如果updelay值被高估了，并且这种情况仅发生在没有连通性的情况下，忽略updelay不会有额外的惩罚。
除了对切换时间的担忧之外，如果你的交换机需要较长时间才能进入备份模式，可能不希望在链路断开后立即激活备份接口。可以通过设置`downdelay`的bonding模块选项来延迟故障转移。

### 13.2 重复的传入数据包

**注意：** 从版本3.0.2开始，bonding驱动程序中包含了抑制重复数据包的逻辑，这应该可以大大消除这个问题。以下描述保留供参考。

当bonding设备首次使用或在一段时间处于空闲状态之后，观察到短暂的数据包重复现象并不罕见。通过向网络中的其他主机发送“ping”命令，并注意到ping输出标记了重复数据包（通常每个从属接口有一个）可以很容易地观察到这种现象。

例如，在一个有五个从属接口连接到一个交换机的主-备模式bond中，输出可能会如下所示：

```
# ping -n 10.0.4.2
PING 10.0.4.2 (10.0.4.2) from 10.0.3.10 : 56(84) bytes of data
64 bytes from 10.0.4.2: icmp_seq=1 ttl=64 time=13.7 ms
64 bytes from 10.0.4.2: icmp_seq=1 ttl=64 time=13.8 ms (DUP!)
64 bytes from 10.0.4.2: icmp_seq=1 ttl=64 time=13.8 ms (DUP!)
64 bytes from 10.0.4.2: icmp_seq=1 ttl=64 time=13.8 ms (DUP!)
64 bytes from 10.0.4.2: icmp_seq=1 ttl=64 time=13.8 ms (DUP!)
64 bytes from 10.0.4.2: icmp_seq=2 ttl=64 time=0.216 ms
64 bytes from 10.0.4.2: icmp_seq=3 ttl=64 time=0.267 ms
64 bytes from 10.0.4.2: icmp_seq=4 ttl=64 time=0.222 ms
```

这不是因为bonding驱动程序中的错误，而是交换机更新其MAC转发表时的一个副作用。最初，交换机不会将数据包中的MAC地址与特定的交换机端口关联起来，因此它可能会将流量发送到所有端口，直到其MAC转发表更新为止。由于连接到bond的接口可能占用单个交换机上的多个端口，当交换机暂时将流量泛洪到所有端口时，bond设备会接收到多个相同的数据包副本（每个从属设备一个）。

重复数据包的行为依赖于具体的交换机，有些交换机会出现这种情况，而有些则不会。在表现出这种行为的交换机上，可以通过清除MAC转发表（在大多数Cisco交换机上，特权命令`clear mac address-table dynamic`可以实现这一点）来触发这种现象。

### 14. 硬件特定的考虑

本节包含针对特定硬件平台配置bonding的额外信息，以及与特定交换机或其他设备进行接口的信息。

#### 14.1 IBM BladeCenter

这适用于JS20及其类似系统。
在JS20刀片服务器上，绑定驱动程序仅支持balance-rr、active-backup、balance-tlb和balance-alb模式。这主要是由于BladeCenter内部的网络拓扑结构，具体如下：

JS20 网络适配器信息
-------------------

所有JS20服务器都集成了两个Broadcom千兆以太网端口（在主板上）。在BladeCenter机箱中，所有JS20刀片服务器的eth0端口都硬连线到I/O模块#1；类似地，所有eth1端口都硬连线到I/O模块#2。

可以通过安装一个附加的Broadcom扩展卡为JS20提供另外两个千兆以太网端口。这些端口分别为eth2和eth3，并分别连接到I/O模块#3和#4。

每个I/O模块可以包含一个交换模块或直通模块（允许端口直接连接到外部交换机）。某些绑定模式需要特定的BladeCenter内部网络拓扑结构才能正常工作，具体细节如下。

有关BladeCenter网络配置的更多信息可以在两本IBM红书中找到：
- “IBM eServer BladeCenter Networking Options”
- “IBM eServer BladeCenter Layer 2-7 Network Switching”

BladeCenter网络配置
--------------------

由于BladeCenter可以有多种配置方式，这里的讨论将局限于基本配置。

通常情况下，I/O模块#1和#2中使用的是以太网交换模块（ESM）。在这种配置下，JS20的eth0和eth1端口将连接到不同的内部交换机（分别位于各自的I/O模块中）。

直通模块（OPM或CPM，光或铜直通模块）将I/O模块直接连接到外部交换机。通过在I/O模块#1和#2中使用直通模块（PM），JS20的eth0和eth1接口可以重定向到外部，并连接到一个共同的外部交换机。

根据ESM和PM的不同组合，网络在绑定时可能表现为单个交换机拓扑（全部PM）或多交换机拓扑（一个或多个ESM，零个或多个PM）。也可以将ESM相互连接，从而形成类似于“多交换机拓扑中的高可用性”示例中的配置。

特定模式的要求
-------------------

balance-rr模式要求绑定设备使用直通模块，并且所有设备都连接到一个共同的外部交换机。
该交换机必须在相应的端口上配置为“etherchannel”或“trunking”，这是balance-rr模式的常见配置。
平衡模式（balance-alb 和 balance-tlb）可以在交换模块或直通模块（或者两者的混合）下工作。对于这些模式的唯一特定要求是，所有网络接口必须能够到达通过绑定设备发送流量的所有目的地（即，网络必须在BladeCenter外部的某个点汇聚）。
主动-备用模式（active-backup）没有额外的要求。

链路监控问题
----------------------

当安装了以太网交换模块时，只有ARP监控能够可靠地检测到到外部交换机的链路丢失。这并不罕见，但检查BladeCenter机柜会让人误以为“外部”网络端口就是系统的以太网端口，实际上在这类“外部”端口和JS20系统本身的设备之间有一个交换机。MII监控只能检测到ESM与JS20系统之间的链路故障。
当安装了直通模块时，MII监控确实可以检测到“外部”端口的故障，因为该端口直接连接到JS20系统。

其他关注点
--------------

串行-over-网络（SoL）链接仅通过主以太网（eth0）建立，因此任何eth0的链路丢失都会导致失去SoL连接。它不会与其他网络流量一起切换，因为SoL系统不受绑定驱动程序的控制。
可能希望禁用交换机上的生成树协议（无论是内部的以太网交换模块还是外部交换机），以避免使用绑定时出现故障切换延迟问题。

常见问题解答
==============================

1. 它是否支持SMP安全？
-------------------
是的。旧版2.0.xx通道绑定补丁不支持SMP安全。
新驱动程序从一开始就设计为支持SMP安全。

2. 哪种类型的网卡可以使用？
-----------------------------
任何以太网类型的网卡（甚至可以混合使用，例如Intel EtherExpress PRO/100 和 3com 3c905b）。对于大多数模式，设备不必具有相同的速度。
从版本3.2.1开始，绑定还支持主动-备用模式下的Infiniband从设备。
3. 我可以拥有多少个绑定设备？
-------------------------------
没有限制。

4. 一个绑定设备可以有多少个从设备？
-----------------------------
这仅受限于Linux支持的网络接口数量和您可以在系统中安装的网卡数量。

5. 当从设备链路断开时会发生什么？
-----------------------------
如果启用了链路监控，那么故障设备将被禁用。在主备模式下，会切换到备用链路，而在其他模式下则忽略故障链路。链路将继续被监控，并且如果恢复，它将以适当的方式重新加入绑定（具体取决于模式）。请参阅高可用性部分以及每种模式的文档以获取更多信息。
链路监控可以通过设置miimon或arp_interval参数来启用（这些参数在上面的模块参数部分中有描述）。通常，miimon监控底层网络设备感知到的载波状态，而arp监控（arp_interval）则监控与本地网络上另一台主机的连接。
如果没有配置链路监控，绑定驱动程序将无法检测链路故障，并假定所有链路始终可用。这可能会导致数据包丢失，并进而影响性能。具体的性能损失取决于绑定模式和网络配置。

6. 绑定是否可用于高可用性？
-----------------------------
是的。请参阅高可用性部分以获取详细信息。

7. 它适用于哪些交换机/系统？
---------------------------
完整的答案取决于所需的模式。
在基本负载均衡模式（balance-rr 和 balance-xor）中，它适用于支持EtherChannel（也称为Trunking）的任何系统。目前大多数可管理交换机都支持此功能，许多不可管理交换机也支持。
在高级负载均衡模式（balance-tlb 和 balance-alb）中，不需要特殊的交换机要求，但需要支持特定功能的设备驱动程序（这些功能在上面的模块参数部分中有描述）。
在802.3ad模式下，它适用于支持IEEE 802.3ad动态链路聚合的系统。目前大多数可管理交换机和许多不可管理交换机都支持802.3ad。
### 主-备份模式应与任何第二层交换机兼容

8. 哪里获取绑定设备的 MAC 地址？
--------------------------------------

当使用具有固定 MAC 地址的从设备或启用 `fail_over_mac` 选项时，绑定设备的 MAC 地址是从活动从设备获得的。

对于其他配置，如果没有显式配置（使用 `ifconfig` 或 `ip link`），绑定设备的 MAC 地址会从其第一个从设备获取。这个 MAC 地址然后传递给所有后续的从设备，并保持一致（即使第一个从设备被移除）直到绑定设备被关闭或重新配置。

如果你想更改 MAC 地址，可以使用 `ifconfig` 或 `ip link` 设置：

```sh
# ifconfig bond0 hw ether 00:11:22:33:44:55

# ip link set bond0 address 66:77:88:99:aa:bb
```

也可以通过将设备关闭/开启并更改其从设备（或它们的顺序）来更改 MAC 地址：

```sh
# ifconfig bond0 down ; modprobe -r bonding
# ifconfig bond0 .... up
# ifenslave bond0 eth..
```

这种方法会自动从添加的下一个从设备获取地址。

要恢复从设备的 MAC 地址，需要将它们从绑定中分离（使用 `ifenslave -d bond0 eth0`）。绑定驱动程序将恢复从设备在被绑定之前所具有的 MAC 地址。

16. 资源和链接
===============

最新版本的绑定驱动程序可以在最新版本的 Linux 内核中找到，该内核位于 http://kernel.org。

本文档的最新版本可以在最新内核源码中找到（名为 Documentation/networking/bonding.rst）。

关于绑定驱动程序开发的讨论在主要的 Linux 网络邮件列表上进行，该邮件列表托管于 vger.kernel.org。邮件列表地址是：

netdev@vger.kernel.org

管理界面（用于订阅或取消订阅）可以在以下网址找到：

http://vger.kernel.org/vger-lists.html#netdev
