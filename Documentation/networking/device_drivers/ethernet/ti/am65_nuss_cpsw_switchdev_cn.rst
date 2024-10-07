SPDX许可证标识符: GPL-2.0

===================================================================
德州仪器K3 AM65 CPSW NUSS基于switchdev的以太网驱动程序
===================================================================

:版本: 1.0

端口重命名
===========

为了通过udev进行重命名，请执行以下命令:

```
ip -d link show dev sw0p1 | grep switchid
```

```
SUBSYSTEM=="net", ACTION=="add", ATTR{phys_switch_id}==<switchid>, \
    ATTR{phys_port_name}!="", NAME="sw0$attr{phys_port_name}"
```

多MAC模式
=========

- 驱动程序默认在多MAC模式下运行，因此作为N个独立的网络接口工作。

Devlink配置参数
================

请参阅Documentation/networking/devlink/am65-nuss-cpsw-switch.rst

启用“交换机”模式
=================

可以通过将devlink驱动程序参数“switch_mode”设置为1/true来启用交换机模式:

```
devlink dev param set platform/c000000.ethernet \
name switch_mode value true cmode runtime
```

这可以在端口的netdev设备处于UP/DOWN状态时完成，但在加入桥接之前，端口的netdev设备必须处于UP状态，以避免覆盖桥接配置，因为CPSW交换机驱动程序会在第一个端口变为UP状态时完全重新加载其配置。
当两个接口都加入到桥接后，CPSW交换机驱动程序将启用带有offload_fwd_mark标志的报文标记。
所有配置都是通过switchdev API实现的。

桥接设置
========

```
devlink dev param set platform/c000000.ethernet \
name switch_mode value true cmode runtime
```

```
ip link add name br0 type bridge
ip link set dev br0 type bridge ageing_time 1000
ip link set dev sw0p1 up
ip link set dev sw0p2 up
ip link set dev sw0p1 master br0
ip link set dev sw0p2 master br0
```

```
[*] bridge vlan add dev br0 vid 1 pvid untagged self
```

```
[*] 如果vlan_filtering=1，则默认_pvid=1
```

注意：[*]步骤是强制性的。

启用/禁用STP
============

```
ip link set dev BRDEV type bridge stp_state 1/0
```

VLAN配置
========

```
bridge vlan add dev br0 vid 1 pvid untagged self <---- 将CPU端口添加到VLAN 1
```

注意：此步骤对于桥接/默认_pvid是强制性的。

添加额外的VLAN
=============

1. 未标记:

```
bridge vlan add dev sw0p1 vid 100 pvid untagged master
bridge vlan add dev sw0p2 vid 100 pvid untagged master
bridge vlan add dev br0 vid 100 pvid untagged self <---- 将CPU端口添加到VLAN 100
```

2. 标记:

```
bridge vlan add dev sw0p1 vid 100 master
bridge vlan add dev sw0p2 vid 100 master
bridge vlan add dev br0 vid 100 pvid tagged self <---- 将CPU端口添加到VLAN 100
```

FDB
---

FDB会在检测到时自动添加到相应的交换端口。

手动添加FDB:

```
bridge fdb add aa:bb:cc:dd:ee:ff dev sw0p1 master vlan 100
bridge fdb add aa:bb:cc:dd:ee:fe dev sw0p2 master <---- 添加到所有VLAN
```

MDB
---

MDB会在检测到时自动添加到相应的交换端口。

手动添加MDB:

```
bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent vid 100
bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent <---- 添加到所有VLAN
```

组播泛洪
=======

CPU端口mcast_flooding始终开启。

在交换端口上启用/禁用泛洪:
```
bridge link set dev sw0p1 mcast_flood on/off
```

访问端口和中继端口
==================

```
bridge vlan add dev sw0p1 vid 100 pvid untagged master
bridge vlan add dev sw0p2 vid 100 master
```

```
bridge vlan add dev br0 vid 100 self
ip link add link br0 name br0.100 type vlan id 100
```

注意：在桥接设备本身设置PVID仅适用于默认VLAN（默认_pvid）。
