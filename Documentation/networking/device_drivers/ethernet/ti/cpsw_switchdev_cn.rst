SPDX 许可证标识符: GPL-2.0

======================================================
基于 Texas Instruments CPSW switchdev 的以太网驱动程序
======================================================

:版本: 2.0

端口重命名
=============

在旧版本的 udev 中，将 ethX 重命名为 swXpY 不会自动支持。

为了通过 udev 进行重命名，请执行如下操作：

    ip -d link show dev sw0p1 | grep switchid

    SUBSYSTEM=="net", ACTION=="add", ATTR{phys_switch_id}==<switchid>, \
	    ATTR{phys_port_name}!="", NAME="sw0$attr{phys_port_name}"


双 MAC 模式
=============

- 新的 (cpsw_new.c) 驱动程序默认处于双-emac 模式，因此作为两个独立的网络接口工作。与传统 CPSW 驱动程序的主要区别包括：

 - 优化的混杂模式：除了启用 ALLMULTI（当前端口）之外还启用了 P0_UNI_FLOOD（两个端口），而不是 ALE_BYPASS
所以，在混杂模式下的端口仍保持多播和 VLAN 过滤的可能性，这在端口加入到同一个桥接器时提供了显著的好处，但无需启用“交换机”模式，或者加入到不同的桥接器。
- 禁用端口上的学习功能，因为它对于隔离端口没有太大意义——硬件中没有转发功能。
- 启用了对 devlink 的基本支持：
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

devlink 配置参数
==================

请参阅文档：Documentation/networking/devlink/ti-cpsw-switch.rst

双 MAC 模式的桥接
=====================

双_MAC_模式需要为内部目的预留两个 VID，默认等于 CPSW 端口号。因此，必须将桥接配置为不识别 VLAN 的模式或调整 default_pvid 的值：

	ip link add name br0 type bridge
	ip link set dev br0 type bridge vlan_filtering 0
	echo 0 > /sys/class/net/br0/bridge/default_pvid
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

或者：

	ip link add name br0 type bridge
	ip link set dev br0 type bridge vlan_filtering 0
	echo 100 > /sys/class/net/br0/bridge/default_pvid
	ip link set dev br0 type bridge vlan_filtering 1
	ip link set dev sw0p1 master br0
	ip link set dev sw0p2 master br0

启用“交换机”
=================

可以通过将 devlink 驱动程序参数 "switch_mode" 配置为 1/true 来启用交换机模式：

	devlink dev param set platform/48484000.switch \
	name switch_mode value 1 cmode runtime

这可以在端口的 netdev 设备状态为 UP/DOWN 的情况下完成，但在加入桥接之前端口的 netdev 设备必须处于 UP 状态以避免覆盖桥接配置，因为当第一个端口的状态更改为 UP 时，CPSW 交换机驱动程序会完全重新加载其配置。
当两个接口都加入桥接后 - CPSW 交换机驱动程序将启用带有 offload_fwd_mark 标志的数据包标记，除非 "ale_bypass=0"

所有配置都是通过 switchdev API 实现的
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

	[*] if vlan_filtering=1. where default_pvid=1

注意：步骤 [*] 是必需的
启用/禁用 STP
==================

::

	ip link set dev BRDEV type bridge stp_state 1/0

VLAN 配置
==================

::

  bridge vlan add dev br0 vid 1 pvid untagged self <---- 将 CPU 端口添加到 VLAN 1

注意：此步骤对于桥接/default_pvid 是必需的
添加额外的 VLAN
==================

 1. 未标记（untagged）：

	bridge vlan add dev sw0p1 vid 100 pvid untagged master
	bridge vlan add dev sw0p2 vid 100 pvid untagged master
	bridge vlan add dev br0 vid 100 pvid untagged self <---- 将 CPU 端口添加到 VLAN100

 2. 标记（tagged）：

	bridge vlan add dev sw0p1 vid 100 master
	bridge vlan add dev sw0p2 vid 100 master
	bridge vlan add dev br0 vid 100 pvid tagged self <---- 将 CPU 端口添加到 VLAN100

FDBs
----

FDBs 在检测到后会自动添加到相应的交换机端口。

手动添加 FDBs ：

    bridge fdb add aa:bb:cc:dd:ee:ff dev sw0p1 master vlan 100
    bridge fdb add aa:bb:cc:dd:ee:fe dev sw0p2 master <---- 添加到所有 VLAN

MDBs
----

MDBs 在检测到后会自动添加到相应的交换机端口。

手动添加 MDBs ：

  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent vid 100
  bridge mdb add dev br0 port sw0p1 grp 239.1.1.1 permanent <---- 添加到所有 VLAN

多播泛洪
==================
CPU 端口的多播泛洪始终启用。

在交换机端口上开启/关闭泛洪：
bridge link set dev sw0p1 mcast_flood on/off

访问端口和 trunk 端口
=====================

::

 bridge vlan add dev sw0p1 vid 100 pvid untagged master
 bridge vlan add dev sw0p2 vid 100 master


 bridge vlan add dev br0 vid 100 self
 ip link add link br0 name br0.100 type vlan id 100

注意：仅在 Bridge 设备本身设置 PVID 对默认 VLAN （default_pvid）有效
NFS
===

要使 NFS 正常工作，唯一的方法是在需要进行影响连接性的交换机配置时切换到最小环境根目录下运行。
假设您使用 eth1 接口启动 NFS（该脚本有些简陋，仅用于证明可以实现 NFS）
setup.sh:::

	```sh
	#!/bin/sh
	mkdir proc
	mount -t proc none /proc
	ifconfig br0  > /dev/null
	if [ $? -ne 0 ]; then
		echo "设置网桥"
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

run_nfs.sh:::

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

	运行 ./run_nfs.sh
	```

这里对原始脚本进行了简单的翻译，保持了原有的结构和命令。请注意，脚本中的某些命令可能需要根据实际环境进行调整才能正确运行。
