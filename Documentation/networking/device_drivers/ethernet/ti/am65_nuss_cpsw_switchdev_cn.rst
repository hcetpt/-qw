SPDX 许可证标识符: GPL-2.0

===================================================================
基于 Texas Instruments K3 AM65 CPSW NUSS 的交换设备型以太网驱动
===================================================================

:版本: 1.0

端口重命名
=============

为了通过 udev 进行重命名，请执行如下操作:: 

    ip -d link show dev sw0p1 | grep switchid

    SUBSYSTEM=="net", ACTION=="add", ATTR{phys_switch_id}==<switchid>, \
	    ATTR{phys_port_name}!="", NAME="sw0$attr{phys_port_name}"


多 MAC 模式
==============

- 驱动默认运行在多 MAC 模式下，因此它像 N 个独立的网络接口一样工作。
Devlink 配置参数
=================

请参阅 Documentation/networking/devlink/am65-nuss-cpsw-switch.rst

启用“交换”模式
=================

可以通过配置 devlink 驱动参数 "switch_mode" 为 1/true 来启用交换模式:: 

        devlink dev param set platform/c000000.ethernet \
        name switch_mode value true cmode runtime

这可以在端口的网络设备处于 UP 或 DOWN 状态时完成，但在将端口加入桥接器之前，这些端口的网络设备必须处于 UP 状态，以避免覆盖桥接器配置。因为当第一个端口状态变为 UP 时，CPSW 交换驱动会完全重新加载其配置。
当两个接口都加入了桥接器后，CPSW 交换驱动将会启用带有 offload_fwd_mark 标志的包标记功能。
所有配置均通过 switchdev API 实现。
桥接器设置
============

:: 

        devlink dev param set platform/c000000.ethernet \
        name switch_mode value true cmode runtime

	ip link add name br0 type bridge
	ip link set dev br0 type bridge ageing_time 1000
	ip link set dev sw0p1 up
	ip link set dev sw0p2 up
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

	[*] bridge vlan add dev br0 vid 1 pvid untagged self

	[*] 如果 vlan_filtering=1，其中默认 pvid=1

	注意：步骤 [*] 是必需的。
启用/禁用 STP
===============

:: 

	ip link set dev BRDEV type bridge stp_state 1/0

VLAN 配置
==================

:: 

  bridge vlan add dev br0 vid 1 pvid untagged self <---- 将 CPU 端口添加到 VLAN 1

注意：对于桥接器/默认 pvid，此步骤是必需的。
添加额外的 VLAN
===============

 1. 未标记 (untagged)::

	bridge vlan add dev sw0p1 vid 100 pvid untagged master
	bridge vlan add dev sw0p2 vid 100 pvid untagged master
	bridge vlan add dev br0 vid 100 pvid untagged self <---- 将 CPU 端口添加到 VLAN 100

 2. 带标记 (tagged)::

	bridge vlan add dev sw0p1 vid 100 master
	bridge vlan add dev sw0p2 vid 100 master
	bridge vlan add dev br0 vid 100 pvid tagged self <---- 将 CPU 端口添加到 VLAN 100

FDB 表项
------

FDB 表项会在检测到后自动添加到适当的交换端口。

手动添加 FDB 表项:: 

    bridge fdb add aa:bb:cc:dd:ee:ff dev sw0p1 master vlan 100
    bridge fdb add aa:bb:cc:dd:ee:fe dev sw0p2 master <---- 添加到所有 VLAN

MDB 表项
------

MDB 表项会在检测到后自动添加到适当的交换端口。

手动添加 MDB 表项:: 

  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent vid 100
  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent <---- 添加到所有 VLAN

组播泛洪
==================

CPU 端口上的组播泛洪始终开启。

在交换端口上打开/关闭泛洪:
bridge link set dev sw0p1 mcast_flood on/off

接入和中继端口
=====================

:: 

 bridge vlan add dev sw0p1 vid 100 pvid untagged master
 bridge vlan add dev sw0p2 vid 100 master


 bridge vlan add dev br0 vid 100 self
 ip link add link br0 name br0.100 type vlan id 100

注意：仅当设置 Bridge 设备本身的 PVID 时，该操作才适用于默认 VLAN (default_pvid)。
