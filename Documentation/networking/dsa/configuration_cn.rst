SPDX 许可证标识符: GPL-2.0

=======================================
从用户空间配置 DSA 交换机
=======================================

目前，DSA 交换机的配置尚未集成到主要的用户空间网络配置套件中，因此必须手动执行。

.. _dsa-config-showcases:

配置示例
-----------------------

要配置 DSA 交换机，需要执行一系列命令。在此文档中，我们以几个常见的配置场景作为示例：

*单端口*
  每个交换机端口作为一个独立的可配置以太网端口。

*桥接*
  所有交换机端口都属于一个可配置的以太网桥。

*网关*
  除一个上行端口外的所有交换机端口都属于一个可配置的以太网桥。
  上行端口作为一个独立的可配置以太网端口。
所有配置都是使用 iproute2 工具完成的，该工具可以从 https://www.kernel.org/pub/linux/utils/net/iproute2/ 获取。

通过 DSA，交换机的每个端口都被处理成一个标准的 Linux 以太网接口。CPU 端口是连接到以太网 MAC 芯片的交换机端口。相应的 Linux 以太网接口被称为通道接口。所有其他相应的 Linux 接口被称为用户接口。用户接口依赖于通道接口处于活动状态才能发送或接收数据包。在内核版本 5.12 之前，用户必须显式管理通道接口的状态。从内核版本 5.12 开始，行为如下：

- 当 DSA 用户接口被激活时，通道接口会自动被激活。
- 当通道接口被关闭时，所有 DSA 用户接口也会自动关闭。

在此文档中，使用了以下以太网接口：

*eth0*
  通道接口

*eth1*
  另一个通道接口

*lan1*
  一个用户接口

*lan2*
  另一个用户接口

*lan3*
  第三个用户接口

*wan*
  专门用于上行流量的用户接口

可以以类似的方式配置更多的以太网接口。
配置的 IP 地址和网络为：

*单端口*
  * lan1: 192.0.2.1/30 (192.0.2.0 - 192.0.2.3)
  * lan2: 192.0.2.5/30 (192.0.2.4 - 192.0.2.7)
  * lan3: 192.0.2.9/30 (192.0.2.8 - 192.0.2.11)

*桥接*
  * br0: 192.0.2.129/25 (192.0.2.128 - 192.0.2.255)

*网关*
  * br0: 192.0.2.129/25 (192.0.2.128 - 192.0.2.255)
  * wan: 192.0.2.1/30 (192.0.2.0 - 192.0.2.3)

.. _dsa-tagged-configuration:

支持标签的配置
----------------------------------

大多数 DSA 交换机都支持基于标签的配置，并且这是首选方案。这些交换机能够对进出的数据包进行标记，而无需使用基于 VLAN 的配置。
*单端口*
  .. code-block:: sh

    # 配置每个接口
    ip addr add 192.0.2.1/30 dev lan1
    ip addr add 192.0.2.5/30 dev lan2
    ip addr add 192.0.2.9/30 dev lan3

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up

    # 启用用户接口
    ip link set lan1 up
    ip link set lan2 up
    ip link set lan3 up

*桥接*
  .. code-block:: sh

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up

    # 启用用户接口
    ip link set lan1 up
    ip link set lan2 up
    ip link set lan3 up

    # 创建桥接
    ip link add name br0 type bridge

    # 将端口添加到桥接
    ip link set dev lan1 master br0
    ip link set dev lan2 master br0
    ip link set dev lan3 master br0

    # 配置桥接
    ip addr add 192.0.2.129/25 dev br0

    # 启用桥接
    ip link set dev br0 up

*网关*
  .. code-block:: sh

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up

    # 启用用户接口
    ip link set wan up
    ip link set lan1 up
    ip link set lan2 up

    # 配置上行端口
    ip addr add 192.0.2.1/30 dev wan

    # 创建桥接
    ip link add name br0 type bridge

    # 将端口添加到桥接
    ip link set dev lan1 master br0
    ip link set dev lan2 master br0

    # 配置桥接
    ip addr add 192.0.2.129/25 dev br0

    # 启用桥接
    ip link set dev br0 up

.. _dsa-vlan-configuration:

不支持标签协议的配置
---------------------

少数交换机无法使用标签协议（DSA_TAG_PROTO_NONE）。这些交换机可以通过基于VLAN的配置进行设置。
*单端口*
  配置只能通过VLAN标签和桥接设置来完成
.. code-block:: sh

    # 在CPU端口上标记流量
    ip link add link eth0 name eth0.1 type vlan id 1
    ip link add link eth0 name eth0.2 type vlan id 2
    ip link add link eth0 name eth0.3 type vlan id 3

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up
    ip link set eth0.1 up
    ip link set eth0.2 up
    ip link set eth0.3 up

    # 启用用户接口
    ip link set lan1 up
    ip link set lan2 up
    ip link set lan3 up

    # 创建桥接
    ip link add name br0 type bridge

    # 激活VLAN过滤
    ip link set dev br0 type bridge vlan_filtering 1

    # 将端口添加到桥接
    ip link set dev lan1 master br0
    ip link set dev lan2 master br0
    ip link set dev lan3 master br0

    # 在端口上标记流量
    bridge vlan add dev lan1 vid 1 pvid untagged
    bridge vlan add dev lan2 vid 2 pvid untagged
    bridge vlan add dev lan3 vid 3 pvid untagged

    # 配置VLAN
    ip addr add 192.0.2.1/30 dev eth0.1
    ip addr add 192.0.2.5/30 dev eth0.2
    ip addr add 192.0.2.9/30 dev eth0.3

    # 启用桥接设备
    ip link set br0 up


*桥接*
  .. code-block:: sh

    # 在CPU端口上标记流量
    ip link add link eth0 name eth0.1 type vlan id 1

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up
    ip link set eth0.1 up

    # 启用用户接口
    ip link set lan1 up
    ip link set lan2 up
    ip link set lan3 up

    # 创建桥接
    ip link add name br0 type bridge

    # 激活VLAN过滤
    ip link set dev br0 type bridge vlan_filtering 1

    # 将端口添加到桥接
    ip link set dev lan1 master br0
    ip link set dev lan2 master br0
    ip link set dev lan3 master br0
    ip link set eth0.1 master br0

    # 在端口上标记流量
    bridge vlan add dev lan1 vid 1 pvid untagged
    bridge vlan add dev lan2 vid 1 pvid untagged
    bridge vlan add dev lan3 vid 1 pvid untagged

    # 配置桥接
    ip addr add 192.0.2.129/25 dev br0

    # 启用桥接
    ip link set dev br0 up

*网关*
  .. code-block:: sh

    # 在CPU端口上标记流量
    ip link add link eth0 name eth0.1 type vlan id 1
    ip link add link eth0 name eth0.2 type vlan id 2

    # 对于内核版本早于v5.12的，传输通道接口需要在用户端口之前手动启用
ip link set eth0 up
    ip link set eth0.1 up
    ip link set eth0.2 up

    # 启用用户接口
    ip link set wan up
    ip link set lan1 up
    ip link set lan2 up

    # 创建桥接
    ip link add name br0 type bridge

    # 激活VLAN过滤
    ip link set dev br0 type bridge vlan_filtering 1

    # 将端口添加到桥接
    ip link set dev wan master br0
    ip link set eth0.1 master br0
    ip link set dev lan1 master br0
    ip link set dev lan2 master br0

    # 在端口上标记流量
    bridge vlan add dev lan1 vid 1 pvid untagged
    bridge vlan add dev lan2 vid 1 pvid untagged
    bridge vlan add dev wan vid 2 pvid untagged

    # 配置VLAN
    ip addr add 192.0.2.1/30 dev eth0.2
    ip addr add 192.0.2.129/25 dev br0

    # 启用桥接设备
    ip link set br0 up

转发数据库（FDB）管理
--------------------

现有的DSA交换机没有必要的硬件支持以保持桥接软件FDB与硬件表同步，因此这两个表是分开管理的（`bridge fdb show` 查询两者，并且根据是否使用 `self` 或 `master` 标志，`bridge fdb add` 或 `bridge fdb del` 命令会作用于一个或两个表中的条目）直到内核版本v4.14，DSA仅支持用户空间管理桥接FDB条目使用桥接绕过操作（这不会更新软件FDB，只会更新硬件FDB）使用 `self` 标志（该标志是可选的，可以省略）
翻译如下：

```sh
# 添加桥接FDB条目到swp0端口
bridge fdb add dev swp0 00:01:02:03:04:05 self static
# 或者简写形式
bridge fdb add dev swp0 00:01:02:03:04:05 static
```

由于一个bug，由DSA提供的桥接绕过FDB实现并没有区分`static`和`local`类型的FDB条目（`static`类型用于转发，而`local`类型则用于本地终止，即发送到主机端口）。相反地，所有带有`self`标志的FDB条目（无论是隐式还是显式）都被DSA视为`static`类型，即使它们实际上是`local`类型。
```sh
# 这个命令：
bridge fdb add dev swp0 00:01:02:03:04:05 static
# 对于DSA来说，与这个命令的行为相同：
bridge fdb add dev swp0 00:01:02:03:04:05 local
# 或者简写形式，因为如果没有指定'static'，那么'local'标志是隐式的，它也与以下命令行为相同：
bridge fdb add dev swp0 00:01:02:03:04:05
```

最后一个命令是在使用桥接绕过操作向DSA交换机添加静态桥接FDB条目的不正确方式，并且是由于错误才得以工作。其他驱动程序会将通过相同命令添加的FDB条目视为`local`类型，因此不会转发它，与DSA不同。
在内核版本v4.14到v5.14之间，DSA并行支持了两种向交换机添加桥接FDB条目的模式：上述的桥接绕过，以及一种使用`master`标志的新模式，该模式也会在软件桥中安装FDB条目。
```sh
# 使用'master'标志
bridge fdb add dev swp0 00:01:02:03:04:05 master static
```

自内核版本v5.14起，DSA获得了与软件桥FDB更紧密的集成，并移除了对桥接绕过FDB实现的支持（使用`self`标志）。这导致了以下变化：
```sh
# 这是唯一支持的、与v4.14及以后版本兼容的添加FDB条目的方法：
bridge fdb add dev swp0 00:01:02:03:04:05 master static
# 这个命令不再有bug，并且条目被正确地处理为'local'类型，而不是被转发：
bridge fdb add dev swp0 00:01:02:03:04:05
# 这个命令不再在硬件中安装静态FDB条目：
bridge fdb add dev swp0 00:01:02:03:04:05 static
```

因此，脚本编写者被鼓励在处理DSA交换机接口上的桥接FDB条目时使用`master static`这一组标志。
### 用户端口与CPU端口的亲和性

通常情况下，DSA交换机通过单一以太网接口连接至主机，但在某些情况下，当交换芯片是独立的，硬件设计可能允许使用2个或更多端口连接至主机，以提高终止吞吐量。

DSA可以通过两种方式利用多个CPU端口。首先，可以静态分配某个用户端口相关的终止流量由某个特定的CPU端口处理。这样，用户空间可以实施自定义策略来静态地平衡用户端口间的负载，通过根据可用的CPU端口分散亲和性。
其次，可以在每个数据包的基础上在CPU端口间进行负载均衡，而不是静态地分配用户端口到CPU端口。

这可以通过将DSA通道置于LAG接口（绑定或团队）下来实现。DSA监控此操作并在面向构成LAG从设备的物理DSA通道的CPU端口上创建该软件LAG的镜像。
为了利用多个CPU端口，交换机的固件（设备树）描述必须标记所有CPU端口与其DSA通道之间的链接使用`ethernet`引用/句柄。启动时，仅会使用单个CPU端口和DSA通道——从固件描述中数值上第一个具有`ethernet`属性的端口。用户需要配置系统以便交换机使用其他通道。
DSA使用`rtnl_link_ops`机制（使用"dsa"类型）来允许更改用户端口的DSA通道。`IFLA_DSA_CONDUIT` u32 netlink属性包含了处理每个用户设备的通道设备的ifindex。DSA通道必须基于固件节点信息是一个有效的候选者，或者是一个LAG接口，该接口仅包含有效的候选者作为其从设备。
使用iproute2，可以执行以下操作：

  .. code-block:: sh

    # 查看当前使用的DSA通道
    ip -d link show dev swp0
        (...)
        dsa master eth0

    # 静态CPU端口分配
    ip link set swp0 type dsa master eth1
    ip link set swp1 type dsa master eth0
    ip link set swp2 type dsa master eth1
    ip link set swp3 type dsa master eth0

    # CPU端口在LAG中，使用明确指定的DSA通道
    ip link add bond0 type bond mode balance-xor && ip link set bond0 up
    ip link set eth1 down && ip link set eth1 master bond0
    ip link set swp0 type dsa master bond0
    ip link set swp1 type dsa master bond0
    ip link set swp2 type dsa master bond0
    ip link set swp3 type dsa master bond0
    ip link set eth0 down && ip link set eth0 master bond0
    ip -d link show dev swp0
        (...)
        dsa master bond0

    # CPU端口在LAG中，依赖于DSA通道的隐式迁移
    ip link add bond0 type bond mode balance-xor && ip link set bond0 up
    ip link set eth0 down && ip link set eth0 master bond0
    ip link set eth1 down && ip link set eth1 master bond0
    ip -d link show dev swp0
        (...)
        dsa master bond0

请注意，在CPU端口处于LAG的情况中，并不需要严格使用`IFLA_DSA_CONDUIT` netlink属性，而是DSA会响应当前通道（`eth0`）的`IFLA_MASTER`属性变化，并将所有用户端口迁移到`eth0`的新上层设备`bond0`。同样地，当使用`RTM_DELLINK`删除`bond0`时，DSA会将分配给该接口的用户端口迁移到基于固件描述的第一个符合条件的物理DSA通道（实际上恢复到启动配置）。
因此，在具有超过2个物理CPU端口的设置中，可以混合使用静态用户到CPU端口的分配与DSA通道之间的LAG。但是，无法静态分配一个用户端口到有上层接口的DSA通道（这包括LAG设备——在这种情况下，通道必须是LAG）。
允许更改用户端口的DSA通道（即CPU端口）亲和性，以便根据流量动态重新分配。
允许物理DSA通道随时加入或离开用作DSA通道的LAG接口；但是，除非LAG接口至少有一个物理DSA通道作为从属设备，否则DSA将拒绝将其视为有效的DSA通道候选者。
