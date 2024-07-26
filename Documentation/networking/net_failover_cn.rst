SPDX 许可证标识符: GPL-2.0

================
NET_FAILOVER
================

概述
=====

Net_failover 驱动程序通过 API 提供了一种自动故障转移机制，用于创建和销毁故障转移主网络设备，并管理一个主用和一个备用的从属网络设备，这些设备是通过通用的故障转移基础设施注册的。故障转移网络设备充当主设备并控制两个从属设备。原始的准虚拟接口被注册为“备用”从属网络设备，而具有相同 MAC 地址的直通（passthru）/VF 设备则被注册为“主用”从属网络设备。这两个“备用”和“故障转移”网络设备都与同一个“pci”设备关联。用户通过“故障转移”网络设备访问网络接口。“故障转移”网络设备在“主用”网络设备可用且链路正常运行时将其作为默认传输选择。

这可以被准虚拟驱动程序用来启用一种替代低延迟数据路径。它还允许在 VF 被拔出时通过故障转移到准虚拟数据路径来实现由虚拟机监控器控制的 VM 实时迁移。

virtio-net 加速的数据路径：STANDBY 模式
=============================================

Net_failover 以透明方式使虚拟机监控器能够为启用了 virtio-net 的 VM 提供加速的数据路径，几乎不需要或无需对客户机用户空间进行更改。
为了支持这一点，虚拟机监控器需要在 virtio-net 接口上启用 VIRTIO_NET_F_STANDBY 特性，并为 virtio-net 和 VF 接口分配相同的 MAC 地址。
以下是一个 libvirt XML 示例片段，显示了这样的配置：
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

在此配置中，第一个设备定义是针对 virtio-net 接口的，该接口作为“持久化”设备，表明此接口将始终插入。这是通过带有必需属性 type 的值为“persistent”的“teaming”标签指定的。virtio-net 设备的链路状态设置为“down”，以确保“故障转移”网络设备优先选择 VF 直通设备来进行常规通信。在实时迁移期间，virtio-net 设备将被激活以允许不间断通信。
第二个设备定义是针对 VF 直通接口。在这里，“teaming”标签提供了类型“transient”，表明该设备可能会周期性地被拔出。提供了一个额外的属性——“persistent”，指向为 virtio-net 设备声明的别名名称。
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

这里，ens10 是“故障转移”主接口，ens10nsby 是“备用”从属 virtio-net 接口，而 ens11 是“主用”从属 VF 直通接口。
值得注意的是，一些用户空间网络配置守护进程（如 systemd-networkd、ifupdown 等）可能不理解“net_failover”设备；因此，在首次启动时，VM 可能会同时为“故障转移”设备和 VF 从 DHCP 服务器获取 IP 地址（相同或不同）。
这会导致无法连接到虚拟机（VM）。因此，可能需要对这些网络配置守护进程进行一些调整，以确保IP地址仅在“故障转移”设备上被接收。
下面是与Debian云镜像中找到的`cloud-ifupdown-helper`脚本一起使用的补丁片段示例：

:: 

  @@ -27,6 +27,8 @@ do_setup() {
       local working="$cfgdir/.$INTERFACE"
       local final="$cfgdir/$INTERFACE"

  +    if [ -d "/sys/class/net/${INTERFACE}/master" ]; then exit 0; fi
  +
       if ifup --no-act "$INTERFACE" > /dev/null 2>&1; then
           # 接口已被ifupdown识别，无需生成配置
           log "Skipping configuration generation for $INTERFACE"

具有SR-IOV VF和处于STANDBY模式下的virtio-net的虚拟机的实时迁移
=================================================================================

`net_failover`还支持具有直接连接的SR-IOV VF设备的虚拟机的由管理程序控制的实时迁移，通过在VF拔除时自动故障转移到半虚拟化数据路径实现。
以下是一个示例脚本，显示了从源管理程序启动实时迁移的步骤。注意：假设虚拟机连接到了一个名为`br0`的软件桥接器，该桥接器包含一个附加到它的VF以及连接到虚拟机的vnet设备。这不是传递给虚拟机的那个VF（如`vf.xml`文件所示）。

::

  # cat vf.xml
  <interface type='hostdev' managed='yes'>
    <mac address='52:54:00:00:12:53'/>
    <source>
      <address type='pci' domain='0x0000' bus='0x42' slot='0x02' function='0x5'/>
    </source>
    <teaming type='transient' persistent='ua-backup0'/>
  </interface>

  # 源管理程序migrate.sh
  #!/bin/bash

  DOMAIN=vm-01
  PF=ens6np0
  VF=ens6v1             # 连接到桥接器的VF
VF_NUM=1
  TAP_IF=vmtap01        # 虚拟机中的virtio-net接口
VF_XML=vf.xml

  MAC=52:54:00:00:12:53
  ZERO_MAC=00:00:00:00:00:00

  # 设置virtio-net接口为启用状态
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

在目标管理程序上，在开始迁移之前创建了一个共享的桥接器`br0`，并从目标PF添加了一个VF到该桥接器。同样地，添加了一个适当的FDB条目。
以下脚本在迁移完成后会在目标虚拟化管理程序上执行，它会重新将VF连接到虚拟机并关闭virtio-net接口：

```bash
# reattach-vf.sh
#!/bin/bash

# 从ens36v0删除指定的MAC地址条目
bridge fdb del 52:54:00:00:12:53 dev ens36v0
# 从vmtap01（其为主设备）删除指定的MAC地址条目
bridge fdb del 52:54:00:00:12:53 dev vmtap01 master
# 将vf.xml文件中定义的VF重新连接到vm01虚拟机，并且该操作同时适用于运行中的虚拟机和配置文件
virsh attach-device --config --live vm01 vf.xml
# 设置vm01虚拟机的vmtap01接口为down状态
virsh domif-setlink vm01 vmtap01 down
```
