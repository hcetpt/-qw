SPDX 许可证标识符: GPL-2.0

============
NET_FAILOVER
============

概述
========

`net_failover` 驱动程序通过 API 提供了一种自动故障转移机制，用于创建和销毁一个故障转移主网络设备，并管理一个主用和备用从属网络设备。这些设备通过通用的故障转移基础设施注册。故障转移网络设备充当主设备并控制两个从设备。原始准虚拟接口注册为“备用”从属网络设备，而具有相同 MAC 地址的直通/VF 设备则注册为“主用”从属网络设备。“备用”和“故障转移”网络设备都与同一个“pci”设备相关联。用户通过“故障转移”网络设备访问网络接口。“故障转移”网络设备默认选择“主用”网络设备进行传输，当该设备可用且链路正常运行时。

这可用于准虚拟驱动程序以启用替代低延迟数据路径。当 VF 被拔出时，它还允许通过故障转移到准虚拟数据路径来实现由虚拟机监控程序控制的 VM 直接连接 VF 的实时迁移。
virtio-net 加速数据路径：STANDBY 模式
=============================================

`net_failover` 以透明方式为启用了 virtio-net 的虚拟机提供由虚拟机监控程序控制的加速数据路径，无需或仅需最小的客户空间更改。

为此，虚拟机监控程序需要在 virtio-net 接口上启用 VIRTIO_NET_F_STANDBY 特性，并为 virtio-net 和 VF 接口分配相同的 MAC 地址。

以下是一个示例 libvirt XML 片段，展示了这样的配置：
::

  <interface type='network'>
    <mac address='52:54:00:00:12:53'/>
    <source network='enp66s0f0_br'/>
    <target dev='tap01'/>
    <model type='virtio'/>
    <driver name='vhost' queues='4'/>
    <link state='down'/>
    <teaming type='persistent'/>
    <alias name='ua-backup0'/>
  </interface>
  <interface type='hostdev' managed='yes'>
    <mac address='52:54:00:00:12:53'/>
    <source>
      <address type='pci' domain='0x0000' bus='0x42' slot='0x02' function='0x5'/>
    </source>
    <teaming type='transient' persistent='ua-backup0'/>
  </interface>

在此配置中，第一个设备定义是针对 virtio-net 接口的，这表示该接口始终插接。这是通过带有必需属性 type 值为 'persistent' 的 `teaming` 标签指定的。virtio-net 设备的链路状态设置为 'down'，以确保“故障转移”网络设备优先选择 VF 直通设备进行常规通信。在实时迁移期间，将使 virtio-net 设备 UP 以实现不间断通信。

第二个设备定义是针对 VF 直通接口的。这里的 `teaming` 标签提供了类型为 'transient'，表示该设备可能会周期性地被拔出。还提供了一个附加属性——`persistent`，指向为 virtio-net 设备声明的别名名称。

使用上述配置启动 VM 将在 VM 中创建以下三个接口：
::

  4: ens10: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
      link/ether 52:54:00:00:12:53 brd ff:ff:ff:ff:ff:ff
      inet 192.168.12.53/24 brd 192.168.12.255 scope global dynamic ens10
         valid_lft 42482sec preferred_lft 42482sec
      inet6 fe80::97d8:db2:8c10:b6d6/64 scope link
         valid_lft forever preferred_lft forever
  5: ens10nsby: <BROADCAST,MULTICAST> mtu 1500 qdisc fq_codel master ens10 state DOWN group default qlen 1000
      link/ether 52:54:00:00:12:53 brd ff:ff:ff:ff:ff:ff
  7: ens11: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq master ens10 state UP group default qlen 1000
      link/ether 52:54:00:00:12:53 brd ff:ff:ff:ff:ff:ff

这里，ens10 是“故障转移”主接口，ens10nsby 是从属“备用”virtio-net 接口，ens11 是从属“主用”VF 直通接口。

需要注意的一点是，某些用户空间网络配置守护进程（如 systemd-networkd、ifupdown 等）不理解“net_failover”设备；因此，在首次启动时，VM 可能会同时为“故障转移”设备和 VF 分配 IP 地址（可能是相同的也可能是不同的），从而导致 DHCP 服务器分配问题。
这将导致无法连接到虚拟机（VM）。因此，可能需要对这些网络配置守护进程进行一些调整，以确保IP地址仅在“failover”设备上接收。
以下是使用Debian云镜像中找到的`cloud-ifupdown-helper`脚本时应用的补丁片段：

```
@@ -27,6 +27,8 @@ do_setup() {
       local working="$cfgdir/.$INTERFACE"
       local final="$cfgdir/$INTERFACE"

  +    if [ -d "/sys/class/net/${INTERFACE}/master" ]; then exit 0; fi
  +
       if ifup --no-act "$INTERFACE" > /dev/null 2>&1; then
           # 接口已经被ifupdown识别，无需生成配置
           log "Skipping configuration generation for $INTERFACE"
```

具有SR-IOV VF和处于STANDBY模式的virtio-net的虚拟机实时迁移
==================================================================

`net_failover`还支持通过自动切换到半虚拟化数据路径来实现带有直接挂载SR-IOV VF设备的虚拟机的由hypervisor控制的实时迁移，当VF被拔出时。

以下是一个示例脚本，展示了从源hypervisor启动实时迁移的步骤。注意：假设虚拟机连接到了一个名为`br0`的软件桥接器，该桥接器上有一个VF与其关联，并且还有一个连接到虚拟机的vnet设备。这不是传递给虚拟机的那个VF（在vf.xml文件中可见）。

```
# cat vf.xml
<interface type='hostdev' managed='yes'>
  <mac address='52:54:00:00:12:53'/>
  <source>
    <address type='pci' domain='0x0000' bus='0x42' slot='0x02' function='0x5'/>
  </source>
  <teaming type='transient' persistent='ua-backup0'/>
</interface>

# 源hypervisor migrate.sh
#!/bin/bash

DOMAIN=vm-01
PF=ens6np0
VF=ens6v1             # 与桥接器关联的VF
VF_NUM=1
TAP_IF=vmtap01        # 虚拟机中的virtio-net接口
VF_XML=vf.xml

MAC=52:54:00:00:12:53
ZERO_MAC=00:00:00:00:00:00

# 设置virtio-net接口为开启状态
virsh domif-setlink $DOMAIN $TAP_IF up

# 移除传递给虚拟机的VF
virsh detach-device --live --config $DOMAIN $VF_XML

ip link set $PF vf $VF_NUM mac $ZERO_MAC

# 添加FDB条目以使流量继续通过VF -> br0 -> vnet接口路径到达虚拟机
bridge fdb add $MAC dev $VF
bridge fdb add $MAC dev $TAP_IF master

# 迁移虚拟机
virsh migrate --live --persistent $DOMAIN qemu+ssh://$REMOTE_HOST/system

# 在迁移完成后清理FDB条目
bridge fdb del $MAC dev $VF
bridge fdb del $MAC dev $TAP_IF master
```

在目标hypervisor上，在迁移开始之前创建了一个共享桥接器`br0`，并且将目标PF上的一个VF添加到该桥接器。同样，添加了相应的FDB条目。
以下脚本在迁移完成后会在目标虚拟化管理程序上执行，重新将VF连接到VM并关闭virtio-net接口：

```bash
# reattach-vf.sh
#!/bin/bash

bridge fdb del 52:54:00:00:12:53 dev ens36v0
bridge fdb del 52:54:00:00:12:53 dev vmtap01 master
virsh attach-device --config --live vm01 vf.xml
virsh domif-setlink vm01 vmtap01 down
```
