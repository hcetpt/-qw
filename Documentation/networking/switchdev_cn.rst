.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>
.. _switchdev:

===============================================
以太网交换设备驱动模型 (switchdev)
===============================================

版权所有 |copy| 2014 Jiri Pirko <jiri@resnulli.us>

版权所有 |copy| 2014-2015 Scott Feldman <sfeldma@gmail.com>

以太网交换设备驱动模型 (switchdev) 是一个内核驱动模型，用于卸载内核中的转发（数据）平面。

图1是一个框图，显示了使用数据中心级交换ASIC芯片的示例设置中switchdev模型的组件。其他设置如SR-IOV或软交换机（如OVS）也是可能的。
::


			     用户空间工具

       用户空间                      |
      +-------------------------------------------------------------------+
       内核                          | Netlink
				    |
		     +--------------+-------------------------------+
		     |         网络栈                        |
		     |           (Linux)                    |
		     |                                      |
		     +--------------------------------------+

			   sw1p2     sw1p4     sw1p6
		      sw1p1  +  sw1p3  +  sw1p5  +          eth1
			+    |    +    |    +    |            +
			|    |    |    |    |    |            |
		     +--+----+----+----+----+----+---+  +-----+-----+
		     |         交换驱动                  |  |    管理   |
		     |        (本文档)                   |  |   驱动  |
		     |                                   |  |           |
		     +--------------+----------------+  +-----------+
				    |
       内核                          | 硬件总线 (例如 PCI)
      +-------------------------------------------------------------------+
       硬件                          |
		     +--------------+----------------+
		     |         交换设备 (sw1)             |
		     |  +----+                       +--------+
		     |  |    v 卸载的数据路径           | 管理端口
		     |  |    |                       |
		     +--|----|----+----+----+----+---+
			|    |    |    |    |    |
			+    +    +    +    +    +
		       p1   p2   p3   p4   p5   p6

			     前面板端口


				    图 1
包含文件
-------------

::

    #include <linux/netdevice.h>
    #include <net/switchdev.h>

配置
-------------

在驱动程序的Kconfig中使用 "depends NET_SWITCHDEV" 以确保为该驱动程序构建switchdev模型支持。

交换端口
------------

在switchdev驱动初始化时，驱动程序将为每个枚举的物理交换端口分配并注册一个 `struct net_device` （使用 `register_netdev()`），称为端口 `net_device`。端口 `net_device` 是物理端口的软件表示，并提供了控制流量从控制器（内核）到网络以及更高层次结构（如桥接、绑定、VLAN、隧道和三层路由器）的锚点。使用标准 `net_device` 工具（如 iproute2、ethtool 等），端口 `net_device` 还可以向用户提供交换端口的物理属性访问，如 PHY 链路状态和 I/O 统计信息。

目前，除了端口 `net_device` 外，没有更高级别的内核对象来表示交换机。所有的switchdev驱动操作都是 `net_device` 操作或switchdev操作。

交换管理端口不在switchdev驱动模型范围内。通常，管理端口不参与卸载的数据平面，并且在管理端口设备上加载了一个不同的驱动程序，如NIC驱动。

交换ID
^^^^^^^^^

switchdev驱动必须实现 `net_device` 操作 `ndo_get_port_parent_id`，对于交换机上的每个端口返回相同的物理ID。此ID必须在同一系统中的不同交换机之间是唯一的。在不同系统中的交换机之间，ID不必唯一。

交换ID用于定位交换机上的端口，并确定聚合端口是否属于同一交换机。
端口网络设备命名
^^^^^^^^^^^^^^^^^^

应使用 Udev 规则来命名端口网络设备，使用端口的某些唯一属性作为键，例如端口的 MAC 地址或端口的 PHYS 名称。不鼓励在驱动程序中硬编码内核网络设备名称；让内核选择默认的网络设备名称，并让 Udev 根据端口属性设置最终名称。
使用端口 PHYS 名称（通过 ndo_get_phys_port_name 获取）作为键对于根据外部配置动态命名的端口特别有用。例如，如果一个物理 40G 端口被逻辑地拆分为 4 个 10G 端口，产生 4 个端口网络设备，设备可以使用端口 PHYS 名称给每个端口分配一个唯一名称。Udev 规则如下：

```shell
SUBSYSTEM=="net", ACTION=="add", ATTR{phys_switch_id}=="<phys_switch_id>", \
    ATTR{phys_port_name}!="", NAME="swX$attr{phys_port_name}"
```

建议的命名约定为 "swXpYsZ"，其中 X 是交换机的名称或 ID，Y 是端口的名称或 ID，Z 是子端口的名称或 ID。例如，sw1p1s0 表示交换机 1 上端口 1 的子端口 0。

端口特性
^^^^^^^^^^^^^

NETIF_F_NETNS_LOCAL

如果交换机设备驱动程序（和设备）仅支持默认网络命名空间（netns）的卸载，则驱动程序应设置此特性标志以防止端口网络设备移出默认 netns。一个支持 netns 的驱动程序/设备不会设置此标志，并负责分区硬件以保持 netns 包含。这意味着硬件不能将一个命名空间中的端口流量转发到另一个命名空间中的端口。

端口拓扑
^^^^^^^^^^^^^

表示物理交换机端口的网络设备可以组织成更高层次的交换结构。默认的结构是独立的路由器端口，用于卸载三层（L3）转发。两个或多个端口可以绑定在一起形成链路聚合组（LAG）。两个或多个端口（或 LAG）可以通过桥接连接来桥接二层（L2）网络。VLAN 可以应用于细分 L2 网络。可以在端口上构建 L2-over-L3 隧道。这些结构使用标准的 Linux 工具（如桥接驱动程序、绑定/团队驱动程序以及基于 netlink 的工具如 iproute2）构建而成。
通过监控 NETDEV_CHANGEUPPER 通知，交换机设备驱动程序可以了解特定端口在拓扑中的位置。例如，一个端口移动到绑定时会看到其上级主设备的变化。如果该绑定移动到桥接设备中，绑定的上级主设备也会改变。依此类推。驱动程序通过注册网络设备事件并在 NETDEV_CHANGEUPPER 事件上采取行动来跟踪这些变化，从而了解端口在整个拓扑中的位置。

二层转发卸载
---------------------

目标是从内核卸载二层（L2）数据转发路径到交换机设备，通过将桥接 FDB 条目镜像到设备。一个 FDB 条目是一个包含 {端口, MAC, VLAN} 的转发目的地元组。
为了卸载 L2 桥接，交换机设备驱动程序/设备应支持：

- 在桥接端口上安装静态 FDB 条目
- 从设备学习或忘记源 MAC/VLAN 的通知
- 端口上的生成树协议（STP）状态变化
- VLAN 泛洪多播/广播和未知单播包

静态 FDB 条目
^^^^^^^^^^^^^^

实现了 `ndo_fdb_add`、`ndo_fdb_del` 和 `ndo_fdb_dump` 操作的驱动程序能够支持以下命令，该命令添加一个静态桥接 FDB 条目：

```shell
bridge fdb add dev DEV ADDRESS [vlan VID] [self] static
```

（"static" 关键字是非可选的：如果没有指定，默认情况下条目为 "local"，这意味着它不应该被转发）

"self" 关键字（因为它是隐含的所以是可选的）的作用是指示内核通过 `DEV` 设备自身的 `ndo_fdb_add` 实现来完成操作。如果 `DEV` 是一个桥接端口，这将绕过桥接，从而导致软件数据库与硬件数据库不同步。
为了避免这种情况，可以使用 "master" 关键字：

```shell
bridge fdb add dev DEV ADDRESS [vlan VID] master static
```

上述命令指示内核查找 `DEV` 的主接口，并通过该接口的 `ndo_fdb_add` 方法完成操作。
这次，桥接设备会生成一个 `SWITCHDEV_FDB_ADD_TO_DEVICE` 通知，端口驱动程序可以处理并用它来编程其硬件表。这样，软件和硬件数据库都将包含这个静态 FDB 条目。
注释：对于卸载Linux桥接的新switchdev驱动程序，不建议实现`ndo_fdb_add`和`ndo_fdb_del`桥接绕过方法：所有静态FDB条目应使用“master”标志添加到桥接端口。`ndo_fdb_dump`是一个例外，如果设备没有用于通知操作系统新学习或遗忘的动态FDB地址的中断，则可以实现它以可视化硬件表。在这种情况下，硬件FDB可能包含软件FDB中没有的条目，实现`ndo_fdb_dump`是查看这些条目的唯一方式。

注释：默认情况下，桥接不会过滤VLAN，仅桥接未标记的流量。要启用VLAN支持，请打开VLAN过滤：

```sh
echo 1 >/sys/class/net/<bridge>/bridge/vlan_filtering
```

已学习/遗忘的源MAC/VLAN的通知
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

交换设备将学习/遗忘入站数据包的源MAC地址/VLAN，并通知交换驱动程序相应的mac/vlan/port元组。交换驱动程序反过来将使用switchdev通知器调用通知桥接驱动程序：

```c
err = call_switchdev_notifiers(val, dev, info, extack);
```

其中val在学习时为SWITCHDEV_FDB_ADD，在遗忘时为SWITCHDEV_FDB_DEL，而info指向一个struct switchdev_notifier_fdb_info。在SWITCHDEV_FDB_ADD时，桥接驱动程序将在桥接FDB中安装FDB条目并将其标记为NTF_EXT_LEARNED。iproute2桥接命令会将这些条目标记为"offload"：

```sh
$ bridge fdb
52:54:00:12:35:01 dev sw1p1 master br0 permanent
00:02:00:00:02:00 dev sw1p1 master br0 offload
00:02:00:00:02:00 dev sw1p1 self
52:54:00:12:35:02 dev sw1p2 master br0 permanent
00:02:00:00:03:00 dev sw1p2 master br0 offload
00:02:00:00:03:00 dev sw1p2 self
33:33:00:00:00:01 dev eth0 self permanent
01:00:5e:00:00:01 dev eth0 self permanent
33:33:ff:00:00:00 dev eth0 self permanent
01:80:c2:00:00:0e dev eth0 self permanent
33:33:00:00:00:01 dev br0 self permanent
01:00:5e:00:00:01 dev br0 self permanent
33:33:ff:12:35:01 dev br0 self permanent
```

应使用桥接命令禁用桥接上的端口学习：

```sh
bridge link set dev DEV learning off
```

应在设备端口上启用学习以及learning_sync：

```sh
bridge link set dev DEV learning on self
bridge link set dev DEV learning_sync on self
```

learning_sync属性使学习/遗忘的FDB条目与桥接FDB同步。虽然可以在设备端口和桥接端口上同时启用学习并禁用learning_sync，但这不是最优方案。

为了支持学习功能，驱动程序实现了switchdev操作`switchdev_port_attr_set`用于`SWITCHDEV_ATTR_PORT_ID_{PRE}_BRIDGE_FLAGS`。

FDB老化
^^^^^^^^^^

桥接将跳过带有NTF_EXT_LEARNED标记的FDB条目的老化，由端口驱动程序/设备负责老化这些条目。如果端口设备支持老化，当FDB条目到期时，它将通知驱动程序，进而通知桥接使用SWITCHDEV_FDB_DEL。如果设备不支持老化，驱动程序可以使用垃圾收集定时器来监控FDB条目。过期的条目将使用SWITCHDEV_FDB_DEL通知桥接。请参阅rocker驱动程序作为运行老化定时器的示例。

为了保持NTF_EXT_LEARNED条目“存活”，驱动程序应通过调用`call_switchdev_notifiers(SWITCHDEV_FDB_ADD, ...)`刷新FDB条目。该通知将重置FDB条目的最后使用时间为当前时间。驱动程序应对刷新通知进行速率限制，例如每秒不超过一次。（最后使用时间可通过`bridge -s fdb`选项查看）

端口上的STP状态变化
^^^^^^^^^^^^^^^^^^^^^^^^

内部或使用第三方STP协议实现（如mstpd），桥接驱动程序维护端口的STP状态，并将使用switchdev操作`switchdev_attr_port_set`针对`SWITCHDEV_ATTR_PORT_ID_STP_UPDATE`通知交换驱动程序端口上的STP状态变化。

状态之一为BR_STATE_*。交换驱动程序可以使用STP状态更新来更新端口的入站数据包过滤列表。例如，如果端口处于DISABLED状态，则不应有任何数据包通过；但如果端口变为BLOCKED状态，则允许STP BPDUs和其他IEEE 01:80:c2:xx:xx:xx链路本地多播数据包通过。

请注意，STP BPDUs是未标记的，且STP状态适用于端口上的所有VLAN，因此应在端口上的未标记和标记VLAN上一致地应用数据包过滤规则。

泛洪L2域
^^^^^^^^^^^^^^^^^^

对于给定的L2 VLAN域，如果端口当前的STP状态允许，交换设备应向域内的所有端口泛洪多播/广播和未知单播数据包。交换驱动程序知道哪些端口属于哪个VLAN L2域，可以编程交换设备进行泛洪。数据包可能被发送到端口网卡以供桥接驱动程序处理。桥接不应再次泛洪设备已经泛洪过的相同端口，否则会有重复的数据包。

为了避免重复的数据包，交换驱动程序应通过设置skb->offload_fwd_mark位来标记数据包已转发。桥接驱动程序将使用入站桥接端口的标记对skb进行标记，并阻止其通过具有相同标记的任何桥接端口转发。
交换设备可能不处理泛洪（flooding），而是将数据包上推到桥接驱动程序进行泛洪。这并不是理想的方案，因为在第二层（L2）域中端口数量会扩展，而硬件设备在泛洪数据包方面比软件更高效。
如果设备支持，可以将泛洪控制卸载到设备上，防止某些网络设备（netdevs）对没有FDB条目的单播流量进行泛洪。

### IGMP Snooping
^^^^^^^^^^^^^^^

为了支持IGMP监听，端口网络设备应将所有IGMP加入和离开消息捕获到桥接驱动程序。
桥接多播模块会在每次多播组发生变化时（无论是静态配置还是动态加入/离开）通知端口网络设备。
硬件实现应该只将注册的多播流量转发到已配置的端口。

### L3 路由卸载
------------------

卸载L3路由要求设备通过内核编程FIB条目，并由设备执行FIB查找和转发。设备会对FIB条目进行最长前缀匹配（LPM），找到与路由前缀匹配的FIB条目，并将数据包转发到相应的下一跳（nexthop）出口端口。
为了编程设备，驱动程序需要使用`register_fib_notifier`注册一个FIB通知器处理器。可用的事件如下：

| 事件               | 描述                                                         |
|--------------------|--------------------------------------------------------------|
| FIB_EVENT_ENTRY_ADD | 用于向设备添加新的FIB条目或修改设备上的现有条目               |
| FIB_EVENT_ENTRY_DEL | 用于删除FIB条目                                               |
| FIB_EVENT_RULE_ADD  | 用于传播FIB规则更改                                           |
| FIB_EVENT_RULE_DEL  | 用于传播FIB规则更改                                           |

`FIB_EVENT_ENTRY_ADD` 和 `FIB_EVENT_ENTRY_DEL` 事件传递以下结构：

```c
struct fib_entry_notifier_info {
    struct fib_notifier_info info; /* 必须是第一个成员 */
    u32 dst;
    int dst_len;
    struct fib_info *fi;
    u8 tos;
    u8 type;
    u32 tb_id;
    u32 nlflags;
};
```

用于在表`tb_id`上添加/修改/删除IPv4目标地址`dst`和前缀长度`dest_len`。`*fi`结构包含有关路由及其下一跳的详细信息。`*dev`是路由下一跳列表中提到的端口网络设备之一。
卸载到设备的路由在`ip route`列表中带有“offload”标记：

```
$ ip route show
default via 192.168.0.2 dev eth0
11.0.0.0/30 dev sw1p1  proto kernel  scope link  src 11.0.0.2 offload
11.0.0.4/30 via 11.0.0.1 dev sw1p1  proto zebra  metric 20 offload
11.0.0.8/30 dev sw1p2  proto kernel  scope link  src 11.0.0.10 offload
11.0.0.12/30 via 11.0.0.9 dev sw1p2  proto zebra  metric 20 offload
12.0.0.2  proto zebra  metric 30 offload
    nexthop via 11.0.0.1  dev sw1p1 weight 1
    nexthop via 11.0.0.9  dev sw1p2 weight 1
12.0.0.3 via 11.0.0.1 dev sw1p1  proto zebra  metric 20 offload
12.0.0.4 via 11.0.0.9 dev sw1p2  proto zebra  metric 20 offload
192.168.0.0/24 dev eth0  proto kernel  scope link  src 192.168.0.15
```

如果至少有一个设备卸载了FIB条目，则设置“offload”标志。
XXX：添加/修改/删除IPv6 FIB API

### 下一跳解析
^^^^^^^^^^^^^^^^^^

FIB条目的下一跳列表包含下一跳元组（网关，dev），但为了让交换设备能够正确地将数据包转发到目标MAC地址，下一跳网关必须解析为邻居的MAC地址。邻居MAC地址的发现通过ARP（或ND）过程完成，并可通过arp_tbl邻居表获得。为了解析路由的下一跳网关，驱动程序应触发内核的邻居解析过程。请参见rocker驱动中的rocker_port_ipv4_resolve()函数示例。
司机可以通过使用 netevent 通知器 `NETEVENT_NEIGH_UPDATE` 来监控 arp_tbl 的更新。设备可以随着 arp_tbl 更新而被配置为具有已解析的下一跳。司机实现了 `ndo_neigh_destroy` 方法来知道何时从端口清除 arp_tbl 邻居条目。

设备驱动预期行为
-------------------

下面定义了一系列行为，启用 switchdev 的网络设备必须遵守：

无配置状态
^^^^^^^^^^^^^^^^^^^^^^^^

当驱动程序启动时，网络设备必须完全运行，并且底层驱动程序必须配置网络设备，使其能够发送和接收此网络设备的流量，并将其正确地与其他网络设备/端口分离（例如：通常在交换ASIC中）。实现这一点的方法高度依赖于硬件，但一个简单的解决方案是使用每个端口的VLAN标识符，除非有更好的机制可用（例如：每个网络端口的专有元数据）。网络设备必须能够运行完整的IP协议栈，包括组播、DHCP、IPv4/6等。如有必要，应配置适当的过滤器（如VLAN、组播、单播等）。底层设备驱动程序必须有效地配置类似于在这些 switchdev 网络设备上启用 IGMP 路由侦听时所做的配置，并尽可能早地在硬件中过滤未请求的组播。

在配置网络设备上的VLAN时，所有VLAN都必须正常工作，无论其他网络设备的状态如何（例如：其他端口属于执行入站VID检查的VLAN感知桥接）。详情见下文。
如果设备实现了例如VLAN过滤，则将接口置于混杂模式应该允许接收所有VLAN标签（包括那些不在过滤器中的）。

桥接交换端口
^^^^^^^^^^^^^^^^^^^^

当启用 switchdev 的网络设备作为桥接成员添加时，它不应干扰任何非桥接网络设备的功能，并且它们应继续像普通网络设备一样运行。根据以下桥接配置选项，预期的行为已记录。

桥接VLAN过滤
^^^^^^^^^^^^^^^^^^^^^

Linux 桥接允许配置 VLAN 过滤模式（静态，在设备创建时，动态，在运行时），这必须由底层 switchdev 网络设备/硬件遵循：
- 关闭VLAN过滤：桥接严格不识别VLAN，并且其数据路径将处理所有以太网帧，就像它们没有打上VLAN标签一样。桥接VLAN数据库仍然可以修改，但在关闭VLAN过滤的情况下，这些修改不应产生影响。带有VID的帧进入设备，该VID未编程到桥接/交换机的VLAN表中，必须转发，并且可以使用VLAN设备进行处理（见下文）。
- 打开VLAN过滤：桥接是VLAN感知的，并且带有VID的帧进入设备，该VID未编程到桥接/交换机的VLAN表中，必须丢弃（严格的VID检查）。
当在桥接端口成员上的 switchdev 网络设备上配置了 VLAN 设备（例如：sw0p1.100）时，必须保留软件网络堆栈的行为，如果无法实现，则应拒绝该配置。
- 当禁用 VLAN 过滤时，桥接器将处理该端口的所有入站流量，除了那些带有 VLAN ID 的流量，这些流量是发往 VLAN 上层接口的。VLAN 上层接口（消耗 VLAN 标签）甚至可以添加到第二个桥接器中，该桥接器包括其他交换端口或软件接口。确保属于 VLAN 上层接口的流量转发域得到妥善管理的一些方法如下：

    * 如果可以按 VLAN 管理转发目标，硬件可以被配置为映射所有流量，除了那些带有属于 VLAN 上层接口的 VID 的数据包，到一个内部 VID，该内部 VID 对应于无标签的数据包，并且覆盖整个不感知 VLAN 的桥接器的所有端口。与 VLAN 上层接口对应的 VID 覆盖该 VLAN 接口的物理端口以及可能与其桥接的其他端口。
* 将具有 VLAN 上层接口的桥接端口视为独立端口，并让转发由软件数据路径处理。

- 当启用 VLAN 过滤时，只要桥接器在任何桥接端口上没有现有具有相同 VID 的 VLAN 条目，就可以创建这些 VLAN 设备。这些 VLAN 设备不能被桥接器捆绑，因为它们与桥接器的 VLAN 数据路径处理功能重复/使用场景相同。
同一交换结构中的非桥接网络端口不应受到桥接设备启用 VLAN 过滤的影响。如果 VLAN 过滤设置对整个芯片全局生效，则独立端口应通过在 ethtool 特性中设置 'rx-vlan-filter: on [fixed]' 告知网络堆栈需要 VLAN 过滤。
由于 VLAN 过滤可以在运行时开启/关闭，switchdev 驱动程序必须能够即时重新配置底层硬件以遵守该选项的切换并适当行为。如果无法实现这一点，switchdev 驱动程序也可以拒绝支持运行时动态切换 VLAN 过滤，并要求销毁桥接设备并创建具有不同 VLAN 过滤值的新桥接设备，以确保 VLAN 意识传递到硬件。
即使桥接中的 VLAN 过滤被关闭，底层交换硬件和驱动程序仍然可以配置自身处于 VLAN 意识模式，前提是上述行为得到遵循。
桥接器的 VLAN 协议在决定数据包是否被视为带标签方面起作用：使用 802.1ad 协议的桥接器必须将未标记的 VLAN 数据包以及带有 802.1Q 标头的数据包都视为未标记。
802.1p（VID 0）标记的数据包必须与未标记的数据包一样被设备处理，因为桥接设备不允许在其数据库中操纵 VID 0。
当桥接器启用了 VLAN 过滤并且入站端口上未配置 PVID 时，必须丢弃未标记和 802.1p 标记的数据包。当桥接器启用了 VLAN 过滤并且入站端口上有 PVID 时，必须接受并根据 PVID VLAN 的桥接端口成员关系转发未标记和优先级标记的数据包。当桥接器禁用 VLAN 过滤时，PVID 的存在与否不应影响数据包转发决策。
桥接 IGMP 侦听
^^^^^^^^^^^^^^^^^^^^

Linux 桥接允许配置 IGMP 侦听（静态地，在接口创建时，或动态地，在运行时），底层的 switchdev 网络设备/硬件必须按照以下方式观察：

- 当 IGMP 侦听关闭时，多播流量必须泛洪到同一桥接器内所有具有 mcast_flood=true 的端口。理想情况下，不应向 CPU/管理端口泛洪（除非入站接口具有 IFF_ALLMULTI 或 IFF_PROMISC），并继续通过网络堆栈通知学习多播流量。如果硬件无法做到这一点，则 CPU/管理端口也必须被泛洪，并且多播过滤在软件中进行。
- 当 IGMP 侦听开启时，多播流量必须选择性地流向相应的网络端口（包括 CPU/管理端口）。未知多播流量仅应向连接到多播路由器的端口泛洪（本地设备也可能充当多播路由器）。

交换机必须遵循 RFC 4541 并相应地泛洪多播流量，因为这是 Linux 桥接实现所做的事情。
由于 IGMP 侦听可以在运行时打开或关闭，switchdev 驱动程序必须能够即时重新配置底层硬件以遵守该选项的切换并适当地行为。
switchdev 驱动程序也可以拒绝支持运行时多播侦听开关的动态切换，并要求销毁桥接设备并创建具有不同多播侦听值的新桥接设备。
