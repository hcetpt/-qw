SPDX 许可证标识符: GPL-2.0

======================================================
基于 Texas Instruments CPSW 的 switchdev 以太网驱动程序
======================================================

:版本: 2.0

端口重命名
=============

在旧版本的 udev 中，自动支持将 ethX 重命名为 swXpY 将不会得到支持。

为了通过 udev 进行重命名，请执行以下操作::

    ip -d link show dev sw0p1 | grep switchid

    SUBSYSTEM=="net", ACTION=="add", ATTR{phys_switch_id}==<switchid>, \
	    ATTR{phys_port_name}!="", NAME="sw0$attr{phys_port_name}"


双 MAC 模式
=============

- 新的（cpsw_new.c）驱动程序默认在双 EMAC 模式下运行，因此作为两个独立的网络接口工作。与传统 CPSW 驱动的主要区别在于：

 - 优化的混杂模式：除了启用当前端口上的 ALLMULTI 外，还启用了 P0_UNI_FLOOD（两个端口），而不是 ALE_BYPASS。
 因此，在混杂模式下的端口仍然可以进行组播和 VLAN 过滤，这在端口加入相同的桥接时提供了显著的好处，但无需启用“交换”模式，或加入不同的桥接。
- 在端口上禁用学习功能，因为对于隔离的端口来说意义不大——硬件中没有转发功能。
- 启用了基本的 devlink 支持。
::

	devlink dev show
		platform/48484000.switch

	devlink dev param show
	platform/48484000.switch:
	name switch_mode type driver-specific
	values:
		cmode runtime value false
	name ale_bypass type driver-specific
	values:
		cmode runtime value false

Devlink 配置参数
=================

参见文档：Documentation/networking/devlink/ti-cpsw-switch.rst

双 MAC 模式的桥接
=====================

双 MAC 模式需要为内部用途保留两个 VID，默认等于 CPSW 端口号。因此，桥接必须配置为不感知 VLAN 模式或调整默认 PVID。例如::

	ip link add name br0 type bridge
	ip link set dev br0 type bridge vlan_filtering 0
	echo 0 > /sys/class/net/br0/bridge/default_pvid
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

或者::

	ip link add name br0 type bridge
	ip link set dev br0 type bridge vlan_filtering 0
	echo 100 > /sys/class/net/br0/bridge/default_pvid
	ip link set dev br0 type bridge vlan_filtering 1
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

启用“交换”
=================

可以通过将 devlink 驱动参数“switch_mode”设置为 1/true 来启用交换模式::

	devlink dev param set platform/48484000.switch \
	name switch_mode value 1 cmode runtime

无论端口的网络设备处于 UP/DOWN 状态，都可以执行此操作，但在加入桥接之前，端口的网络设备必须处于 UP 状态，以避免覆盖桥接配置，因为 CPSW 交换驱动会在第一个端口状态变为 UP 时完全重新加载其配置。
当两个接口都加入桥接后，除非设置“ale_bypass=0”，否则 CPSW 交换驱动会启用带有 offload_fwd_mark 标志的数据包标记。

所有配置都是通过 switchdev API 实现的。
桥接设置
============

::

	devlink dev param set platform/48484000.switch \
	name switch_mode value 1 cmode runtime

	ip link add name br0 type bridge
	ip link set dev br0 type bridge ageing_time 1000
	ip link set dev sw0p1 up
	ip link set dev sw0p2 up
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

	[*] bridge vlan add dev br0 vid 1 pvid untagged self

	[*] 如果 vlan_filtering=1，则 default_pvid=1

注意：步骤 [*] 是必需的。
启用/禁用 STP
=================

::

	ip link set dev BRDEV type bridge stp_state 1/0

VLAN 配置
==================

::

  bridge vlan add dev br0 vid 1 pvid untagged self <---- 将 CPU 端口添加到 VLAN 1

注意：此步骤对于桥接/default_pvid 是必需的。
添加额外的 VLAN
==================

1. 未标记（untagged）::

	bridge vlan add dev sw0p1 vid 100 pvid untagged master
	bridge vlan add dev sw0p2 vid 100 pvid untagged master
	bridge vlan add dev br0 vid 100 pvid untagged self <---- 将 CPU 端口添加到 VLAN100

2. 标记（tagged）::

	bridge vlan add dev sw0p1 vid 100 master
	bridge vlan add dev sw0p2 vid 100 master
	bridge vlan add dev br0 vid 100 pvid tagged self <---- 将 CPU 端口添加到 VLAN100

FDBs
----

FDBs 会在检测到时自动添加到相应的交换端口。

手动添加 FDBs::

    bridge fdb add aa:bb:cc:dd:ee:ff dev sw0p1 master vlan 100
    bridge fdb add aa:bb:cc:dd:ee:fe dev sw0p2 master <---- 添加到所有 VLAN

MDBs
----

MDBs 会在检测到时自动添加到相应的交换端口。

手动添加 MDBs::

  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent vid 100
  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent <---- 添加到所有 VLAN

组播泛洪
==================
CPU 端口的组播泛洪始终开启。

在交换端口上启用/禁用泛洪：
bridge link set dev sw0p1 mcast_flood on/off

访问端口和 trunk 端口
=====================

::

 bridge vlan add dev sw0p1 vid 100 pvid untagged master
 bridge vlan add dev sw0p2 vid 100 master


 bridge vlan add dev br0 vid 100 self
 ip link add link br0 name br0.100 type vlan id 100

注意：在桥接设备本身设置 PVID 只对默认 VLAN（default_pvid）有效。
NFS
===

唯一能让 NFS 工作的方法是在需要更改影响连接性的交换配置时切换到一个最小环境。
假设你是通过 `eth1` 接口启动 NFS（该脚本有些粗糙，只是为了证明NFS是可行的）
`setup.sh` 脚本如下：

```sh
#!/bin/sh
mkdir proc
mount -t proc none /proc
ifconfig br0 > /dev/null
if [ $? -ne 0 ]; then
    echo "设置桥接设备"
    ip link add name br0 type bridge
    ip link set dev br0 type bridge ageing_time 1000
    ip link set dev br0 type bridge vlan_filtering 1

    ip link set eth1 down
    ip link set eth1 name sw0p1
    ip link set dev sw0p1 up
    ip link set dev sw0p2 up
    ip link set dev sw0p2 master br0
    ip link set dev sw0p1 master br0
    bridge vlan add dev br0 vid 1 pvid untagged self
    ifconfig sw0p1 0.0.0.0
    udhcpc -i br0
fi
umount /proc
```

`run_nfs.sh` 脚本如下：

```sh
#!/bin/sh
mkdir /tmp/root/bin -p
mkdir /tmp/root/lib -p

cp -r /lib/ /tmp/root/
cp -r /bin/ /tmp/root/
cp /sbin/ip /tmp/root/bin
cp /sbin/bridge /tmp/root/bin
cp /sbin/ifconfig /tmp/root/bin
cp /sbin/udhcpc /tmp/root/bin
cp /path/to/setup.sh /tmp/root/bin
chroot /tmp/root/ busybox sh /bin/setup.sh

./run_nfs.sh
```

注意：在实际使用时，请根据实际情况调整路径和命令。例如，确保 `/path/to/setup.sh` 是正确的路径。
