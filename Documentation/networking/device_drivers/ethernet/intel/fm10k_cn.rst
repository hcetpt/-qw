SPDX 许可声明标识符：GPL-2.0+

=============================================================
基于 Linux 的 Intel(R) 以太网多主机控制器驱动程序
=============================================================

2018年8月20日
版权所有 © 2015-2018 Intel 公司
内容
========
- 识别您的适配器
- 额外配置
- 性能调优
- 已知问题
- 支持

识别您的适配器
========================
本发行版中的驱动程序兼容基于 Intel(R) 以太网多主机控制器的设备。
有关如何识别您的适配器以及最新的 Intel 网络驱动程序的信息，请参阅 Intel 支持网站：
https://www.intel.com/support

流控制
------------
Intel(R) 以太网交换机主机接口驱动程序不支持流控制。它不会发送暂停帧。这可能导致数据包丢失。

虚拟功能（VFs）
-----------------------
使用 sysfs 启用 VFs
有效范围：0-64

例如：

    echo $num_vf_enabled > /sys/class/net/$dev/device/sriov_numvfs //启用 VFs
    echo 0 > /sys/class/net/$dev/device/sriov_numvfs //禁用 VFs

注意：设备和驱动程序都不控制 VFs 如何映射到配置空间。总线布局会因操作系统而异。在支持的操作系统中，您可以检查 sysfs 来找到映射关系。

注意：当启用 SR-IOV 模式时，硬件 VLAN 过滤和 VLAN 标签剥离/插入将保持启用状态。请在添加新的 VLAN 过滤之前删除旧的 VLAN 过滤。例如：

    ip link set eth0 vf 0 vlan 100	// 为 VF 0 设置 VLAN 100
    ip link set eth0 vf 0 vlan 0	// 删除 VLAN 100
    ip link set eth0 vf 0 vlan 200	// 为 VF 0 设置新的 VLAN 200

额外的功能和配置
======================

巨型帧
------------
通过将最大传输单元（MTU）更改为大于默认值 1500 的值来启用巨型帧支持。
使用 ifconfig 命令增加 MTU 大小。例如，输入以下命令，其中 <x> 是接口编号：

    ifconfig eth<x> mtu 9000 up

或者，您可以使用 ip 命令如下：

    ip link set mtu 9000 dev eth<x>
    ip link set up dev eth<x>

此设置不会保存到重新启动。可以通过在以下文件中添加 'MTU=9000' 来使设置永久生效：

- 对于 RHEL：/etc/sysconfig/network-scripts/ifcfg-eth<x>
- 对于 SLES：/etc/sysconfig/network/<config_file>

注意：巨型帧的最大 MTU 设置为 15342。这个值与最大巨型帧大小 15364 字节一致。
注意：此驱动程序将尝试使用多个页面大小的缓冲区来接收每个巨型数据包。这有助于避免分配接收数据包时出现缓冲区饥饿问题。

通用接收卸载（GRO）
--------------------------------
驱动程序支持内核软件实现的 GRO。GRO 已经证明，通过将接收流量合并成更大的数据块，在大量接收负载下可以显著降低 CPU 使用率。GRO 是以前使用的 LRO 接口的进化版本。GRO 能够合并除 TCP 之外的其他协议。它也适用于对 LRO 有问题的配置，例如桥接和 iSCSI。

支持的 ethtool 命令和过滤选项
----------------------------------------------------
-n --show-nfc
  获取接收网络流分类配置
```plaintext
rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6
获取指定网络流量类型的哈希选项

-N --config-nfc
配置接收网络流分类

rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6 m|v|t|s|d|f|n|r
配置指定网络流量类型的哈希选项

- udp4: UDP over IPv4
- udp6: UDP over IPv6
- f 基于接收数据包的第4层头部的字节0和1进行哈希
- n 基于接收数据包的第4层头部的字节2和3进行哈希

已知问题/故障排除
============================

在Linux KVM下的64位Microsoft Windows Server 2012/R2 客户操作系统中启用SR-IOV
-------------------------------------------------------------------------------------
KVM Hypervisor/VMM支持将PCIe设备直接分配给虚拟机。这包括传统的PCIe设备以及基于Intel Ethernet Controller XL710的SR-IOV功能设备。

支持
=======
如需获取一般信息，请访问Intel支持网站：
https://www.intel.com/support/

如果在支持的内核上使用支持的适配器时发现发布的源代码存在问题，请将与问题相关的确切信息发送至 intel-wired-lan@lists.osuosl.org
```
