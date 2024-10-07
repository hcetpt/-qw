.. SPDX 许可证标识符: GPL-2.0

==========================================
Broadcom RoboSwitch 以太网交换机驱动程序
==========================================

Broadcom RoboSwitch 以太网交换机家族被广泛应用于各种 xDSL 路由器、电缆调制解调器和其他多媒体设备中。
实际实现支持 BCM5325E、BCM5365、BCM539x、BCM53115 和 BCM53125 以及 BCM63XX 系列设备。
实现细节
======================

该驱动程序位于 ``drivers/net/dsa/b53/`` 中，并且作为 DSA 驱动程序实现；请参阅 ``Documentation/networking/dsa/dsa.rst`` 了解有关子系统的详细信息及其提供的功能。
如果可能，交换机会配置为启用一个特定于 Broadcom 的 4 字节交换标签，该标签会在每个转发到 CPU 接口的报文中插入。相反，CPU 网络接口应在进入 CPU 端口的报文中插入类似的标签。标签格式在 ``net/dsa/tag_brcm.c`` 中描述。
设备的配置取决于是否支持标签功能。
带有标签支持的配置
----------------------------------

希望使用基于标签的配置。这种配置不仅限于 b53 DSA 驱动程序，而且与所有支持标签功能的 DSA 驱动程序兼容。
请参见 :ref:`dsa-tagged-configuration`
不带标签支持的配置
-------------------------------------

较旧的型号（5325、5365）支持不同的标签格式，目前尚未支持。539x 和 531x5 需要管理模式和一些特殊处理，这也尚未支持。在这种情况下，标签支持被禁用，交换机需要不同的配置。
配置略有不同，请参考 :ref:`dsa-vlan-configuration`
b53 在所有 VLAN 中标记 CPU 端口，因为如果不这样做，任何 PVID 未标记的 VLAN 配置实际上会改变 CPU 端口的默认 PVID 并使其变为未标记状态，这是不希望的。

与 :ref:`dsa-vlan-configuration` 中描述的配置不同，在单端口和网关配置中，必须从用户界面配置中移除默认 VLAN 1，而在桥接示例中无需添加额外的 VLAN 配置。

单端口
~~~~~~~
配置只能通过 VLAN 标记和桥接设置来完成。
默认情况下，数据包被标记为 VID 1：

```sh
# 在 CPU 端口上标记流量
ip link add link eth0 name eth0.1 type vlan id 1
ip link add link eth0 name eth0.2 type vlan id 2
ip link add link eth0 name eth0.3 type vlan id 3

# 必须在用户端口之前启动传输接口
ip link set eth0 up
ip link set eth0.1 up
ip link set eth0.2 up
ip link set eth0.3 up

# 启动用户接口
ip link set wan up
ip link set lan1 up
ip link set lan2 up

# 创建桥接设备
ip link add name br0 type bridge

# 激活 VLAN 过滤
ip link set dev br0 type bridge vlan_filtering 1

# 将端口添加到桥接设备
ip link set dev wan master br0
ip link set dev lan1 master br0
ip link set dev lan2 master br0

# 在端口上标记流量
bridge vlan add dev lan1 vid 2 pvid untagged
bridge vlan del dev lan1 vid 1
bridge vlan add dev lan2 vid 3 pvid untagged
bridge vlan del dev lan2 vid 1

# 配置 VLAN
ip addr add 192.0.2.1/30 dev eth0.1
ip addr add 192.0.2.5/30 dev eth0.2
ip addr add 192.0.2.9/30 dev eth0.3

# 启动桥接设备
ip link set br0 up
```

桥接
~~~~~~

```sh
# 在 CPU 端口上标记流量
ip link add link eth0 name eth0.1 type vlan id 1

# 必须在用户端口之前启动传输接口
ip link set eth0 up
ip link set eth0.1 up

# 启动用户接口
ip link set wan up
ip link set lan1 up
ip link set lan2 up

# 创建桥接设备
ip link add name br0 type bridge

# 激活 VLAN 过滤
ip link set dev br0 type bridge vlan_filtering 1

# 将端口添加到桥接设备
ip link set dev wan master br0
ip link set dev lan1 master br0
ip link set dev lan2 master br0
ip link set eth0.1 master br0

# 配置桥接设备
ip addr add 192.0.2.129/25 dev br0

# 启动桥接设备
ip link set dev br0 up
```

网关
~~~~~~~

```sh
# 在 CPU 端口上标记流量
ip link add link eth0 name eth0.1 type vlan id 1
ip link add link eth0 name eth0.2 type vlan id 2

# 必须在用户端口之前启动传输接口
ip link set eth0 up
ip link set eth0.1 up
ip link set eth0.2 up

# 启动用户接口
ip link set wan up
ip link set lan1 up
ip link set lan2 up

# 创建桥接设备
ip link add name br0 type bridge

# 激活 VLAN 过滤
ip link set dev br0 type bridge vlan_filtering 1

# 将端口添加到桥接设备
ip link set dev wan master br0
ip link set eth0.1 master br0
ip link set dev lan1 master br0
ip link set dev lan2 master br0

# 在端口上标记流量
bridge vlan add dev wan vid 2 pvid untagged
bridge vlan del dev wan vid 1

# 配置 VLAN
ip addr add 192.0.2.1/30 dev eth0.2
ip addr add 192.0.2.129/25 dev br0

# 启动桥接设备
ip link set br0 up
```
