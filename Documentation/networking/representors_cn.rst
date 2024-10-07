SPDX 许可证标识符: GPL-2.0
.. _representors:

=============================
网络功能表示器
=============================

本文档描述了用于控制 SmartNIC 内部交换的表示器网卡的语义和用法。对于与之密切相关的物理（多端口）交换机上的端口表示器，请参阅 :ref:`Documentation/networking/switchdev.rst <switchdev>`
动机
--------

自2010年代中期以来，网卡开始提供比传统的SR-IOV方法（基于简单的MAC/VLAN交换模型）更为复杂的虚拟化能力。这导致人们希望将软件定义的网络（如OpenVSwitch）卸载到这些网卡上，以指定每个功能的网络连接性。由此产生的设计被称为SmartNIC或DPUs。
网络功能表示器将标准的Linux网络堆栈引入到了虚拟交换机和IOV设备中。就像Linux控制的交换机的每个物理端口都有一个独立的netdev一样，虚拟交换机的每个虚拟端口也有一个独立的netdev。
当系统启动且在任何卸载配置之前，所有来自虚拟功能的数据包都会通过表示器出现在PF的网络堆栈中。因此，PF始终可以自由地与虚拟功能通信。
PF可以在表示器、上行链路或任何其他netdev之间配置标准的Linux转发（路由、桥接、TC分类器）。
因此，表示器既是控制平面对象（在管理命令中代表功能），也是数据平面对象（虚拟管道的一端）。
作为虚拟链路的终点，表示器可以像其他任何netdevice一样进行配置；在某些情况下（例如链路状态），被表示器会跟随表示器的配置，而在其他情况下则有单独的API来配置被表示器。
定义
--------

本文档使用术语“switchdev功能”来指代具有设备上虚拟交换机管理控制权的PCIe功能。
通常，这将是PF，但理论上NIC也可以配置为将这些管理权限授予VF或SF（子功能）。
根据NIC的设计，一个多端口NIC可能有一个针对整个设备的switchdev功能，或者每个物理网络端口都有一个独立的虚拟交换机，从而拥有一个独立的switchdev功能。
如果网卡支持嵌套交换机，那么可能为每个嵌套交换机提供单独的 `switchdev` 函数，在这种情况下，每个 `switchdev` 函数只应为其直接管理的（子）交换机端口创建表示器（representor）。
“被表示对象”（representee）是表示器所代表的对象。例如，在VF表示器的情况下，被表示对象就是相应的VF。

表示器的作用是什么？
---------------------------

表示器主要有三个作用：

1. 用于配置被表示对象看到的网络连接，例如链路的上下状态、MTU等。例如，将表示器设置为UP状态时，应该使被表示对象看到链路上事件/载波检测事件。
2. 提供未命中虚拟交换机中任何卸载快速路径规则的数据包的慢路径。在表示器网卡上发送的数据包应该传递给被表示对象；被表示对象发送的数据包如果没有匹配任何交换规则，则应该在表示器网卡上接收。（也就是说，表示器与被表示对象之间存在一个虚拟管道，类似于veth对。）
   这使得软件交换实现（如OpenVSwitch或Linux桥接）能够在被表示对象和网络其他部分之间转发数据包。
3. 作为切换规则（如TC过滤器）引用被表示对象的句柄，允许这些规则被卸载。

第2点和第3点的结合意味着无论TC过滤器是否被卸载，其行为（除了性能外）应该是相同的。例如，在软件中，一个TC规则应用于该表示器网卡收到的数据包；而在硬件卸载模式下，它则应用于被表示对象VF发出的数据包。相反地，镜像出口重定向到一个VF表示器，在硬件中对应于直接交付给被表示对象VF。

哪些功能需要有表示器？
-----------------------------------------

基本上，对于设备内部交换机上的每个虚拟端口，都应该有一个表示器。
一些厂商选择省略上行链路和物理网络端口的表示器，这可以简化使用（上行链路网卡实际上成为物理端口的表示器），但这不适用于具有多个端口或上行链路的设备。
因此，以下各项都应具有代理设备（representor）：

- 属于 switchdev 功能的 VFs
- 本地 PCIe 控制器上的其他 PFs，以及属于它们的任何 VFs
- 设备上外部 PCIe 控制器上的 PFs 和 VFs（例如，在智能网卡内的任何嵌入式系统级芯片中）
- 具有其他身份的 PFs 和 VFs，包括网络块设备（如由远程/分布式存储支持的 vDPA virtio-blk PF），但前提是（且仅当）它们的网络访问是通过虚拟交换端口实现的。注意，即使被代理设备没有 netdev，这些功能也可能需要一个代理设备
- 属于上述任何 PF 或 VF 的子功能（SFs），如果它们有自己的交换端口（而不是使用其父 PF 的端口）
- 设备上的任何加速器或插件，只要它们通过虚拟交换端口连接到网络，即使它们没有对应的 PCIe PF 或 VF

这样可以通过代理设备的 TC 规则来控制 NIC 的所有交换行为。

常见的误解是将虚拟端口与 PCIe 虚拟功能及其 netdev 混为一谈。虽然在简单情况下，VF 网络设备和 VF 代理设备之间存在一对一的关系，但在更复杂的设备配置中可能不会遵循这一点。

如果一个 PCIe 功能没有通过内部交换机进行网络访问（即使是间接通过该功能所提供的服务的硬件实现），那么它不应该有一个代理设备（即使它有一个 netdev）。

这样的功能没有用于配置或作为虚拟管道另一端的交换机虚拟端口。
代表端口代表的是虚拟端口，而不是PCIe功能或“最终用户”的网络设备。

#. 这里的概念是设备中的硬件IP堆栈执行块DMA请求与网络数据包之间的转换，因此只有网络数据包通过虚拟端口传输到交换机上。IP堆栈所“看到”的网络访问可以通过tc规则进行配置；例如，其流量可能全部被封装在一个特定的VLAN或VxLAN中。然而，由于块设备作为块设备本身不是网络实体，因此任何所需的块设备配置都不适合使用代表端口，而应使用其他通道，如devlink。

与此相反，在virtio-blk实现中，DMA请求被原封不动地转发到另一个PF，该PF的驱动程序然后在软件中发起和终止IP流量；在这种情况下，DMA流量不会通过虚拟交换机，因此virtio-blk PF不应拥有代表端口。

如何创建代表端口？
--------------------

连接到switchdev功能的驱动实例应该为交换机上的每个虚拟端口创建一个纯软件的网络设备，该设备以某种形式的内核引用方式关联到switchdev功能自身的网络设备或驱动私有数据（`netdev_priv()`）。

这可能是通过在探测时枚举端口、动态响应端口的创建和销毁事件，或者两者的组合来实现。

代表端口网络设备的操作通常涉及通过switchdev功能来执行。例如，`ndo_start_xmit()` 可能会将数据包通过连接到switchdev功能的硬件TX队列发送出去，并通过数据包元数据或队列配置将其标记为传送给被代表端口。

如何识别代表端口？
--------------------

代表端口网络设备不应直接引用PCIe设备（例如通过 `net_dev->dev.parent` / `SET_NETDEV_DEV()`），无论是被代表端口还是switchdev功能本身的PCIe设备。

取而代之的是，驱动程序应使用 `SET_NETDEV_DEVLINK_PORT` 宏，在注册网络设备之前为其分配一个devlink端口实例；内核使用devlink端口提供 `phys_switch_id` 和 `phys_port_name` 的sysfs节点。

（一些遗留驱动程序直接实现了 `ndo_get_port_parent_id()` 和 `ndo_get_phys_port_name()`，但这些方法已被弃用。）有关此API的详细信息，请参阅 :ref:`Documentation/networking/devlink/devlink-port.rst <devlink_port>`。
预计用户空间会使用这些信息（例如通过 udev 规则）为网卡构建一个适当的信息性名称或别名。例如，如果 switchdev 函数是 `eth4`，那么具有 `phys_port_name` 为 `p0pf1vf2` 的 representor 可能会被重命名为 `eth4pf1vf2rep`。目前尚无针对非 PCIe 功能（例如加速器和插件）的 representor 命名约定。

Representor 如何与 TC 规则互动？
------------------------------------

任何在 representor 上的 TC 规则（在软件 TC 中）都会应用于该 representor 网卡接收到的数据包。因此，如果规则的传输部分对应于虚拟交换机上的另一个端口，则驱动程序可以选择将其卸载到硬件中，应用到代表对象（representee）传输的数据包上。类似地，由于针对 representor 的 TC mirred 出站操作（在软件中）会将数据包发送给 representor（从而间接传递给 representee），硬件卸载应将其解释为向 representee 发送数据包。

举个简单的例子，如果 `PORT_DEV` 是物理端口的 representor 而 `REP_DEV` 是一个 VF 的 representor，以下规则：

```sh
tc filter add dev $REP_DEV parent ffff: protocol ipv4 flower \
    action mirred egress redirect dev $PORT_DEV
tc filter add dev $PORT_DEV parent ffff: protocol ipv4 flower skip_sw \
    action mirred egress mirror dev $REP_DEV
```

意味着所有来自 VF 的 IPv4 数据包都会从物理端口发出，并且所有在物理端口上接收的 IPv4 数据包除了发往 `PORT_DEV` 外，还会被传送给 VF。（注意如果没有第二个规则中的 `skip_sw`，VF 将会收到两份副本，因为 `PORT_DEV` 上的数据包接收会再次触发 TC 规则并镜像到 `REP_DEV`。）

在没有单独端口和上行链路 representor 的设备上，`PORT_DEV` 应该是指向 switchdev 函数自身的上行链路网卡。

当然，如果 NIC 支持的话，规则可以包括修改数据包的操作（例如 VLAN 推入/弹出），这应该由虚拟交换机执行。

隧道封装和解封装要复杂得多，因为它涉及第三个网卡（一个以元数据模式运行的隧道网卡，例如用 `ip link add vxlan0 type vxlan external` 创建的 VxLAN 设备），并且需要绑定一个 IP 地址到底层设备（例如 switchdev 函数的上行链路网卡或端口 representor）。类似如下 TC 规则：

```sh
tc filter add dev $REP_DEV parent ffff: flower \
    action tunnel_key set id $VNI src_ip $LOCAL_IP dst_ip $REMOTE_IP \
                          dst_port 4789 \
    action mirred egress redirect dev vxlan0
tc filter add dev vxlan0 parent ffff: flower enc_src_ip $REMOTE_IP \
    enc_dst_ip $LOCAL_IP enc_key_id $VNI enc_dst_port 4789 \
    action tunnel_key unset action mirred egress redirect dev $REP_DEV
```

其中 `LOCAL_IP` 是绑定到 `PORT_DEV` 的 IP 地址，而 `REMOTE_IP` 是同一子网上的另一个 IP 地址，这意味着 VF 发送的数据包应被 VxLAN 封装并通过物理端口发送（驱动程序需要通过查找 `LOCAL_IP` 的路由来确定目标为 `PORT_DEV`，并执行 ARP/邻居表查询以找到外层以太网帧使用的 MAC 地址），而物理端口上接收到的 UDP 端口为 4789 的 UDP 数据包应被解析为 VxLAN 并在 VSID 匹配 `$VNI` 时解封装并转发给 VF。

如果这一切看起来很复杂，请记住 TC 卸载的“黄金法则”：硬件应确保与数据包通过慢路径、经过软件 TC（忽略任何 `skip_hw` 规则并应用任何 `skip_sw` 规则）并通过 representor 网卡传输或接收相同的结果。

配置 representee 的 MAC 地址
---------------------------------

representee 的链路状态通过 representor 控制。将 representor 设置为 UP 或 DOWN 应该会导致 representee 的链路状态为 ON 或 OFF。
在 representor 上设置 MTU 应该会使 representee 报告相同的 MTU。
（在允许配置独立且不同的MTU和MRU值的硬件上，代表者的MTU应与被代表者的MRU相对应，反之亦然。）

目前没有方法使用代表者来设置被代表者的站点永久MAC地址；其他可用的方法包括：

- 传统的SR-IOV（``ip link set DEVICE vf NUM mac LLADDR``）
- devlink端口功能（详见**devlink-port(8)**和
  :ref:`Documentation/networking/devlink/devlink-port.rst <devlink_port>`）
