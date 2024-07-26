SPDX 许可声明标识符：GPL-2.0+ 

=============================================== 
基于 Intel® 以太网多主机控制器的 Linux 基础驱动程序 
=============================================== 

2018 年 8 月 20 日  
版权所有 © 2015-2018 Intel 公司  
内容  
========  
- 识别您的适配器  
- 额外配置  
- 性能调优  
- 已知问题  
- 支持  

识别您的适配器  
==================  
此版本中的驱动程序与基于 Intel® 以太网多主机控制器的设备兼容。  
有关如何识别您的适配器以及获取最新的 Intel 网络驱动程序的信息，请参考 Intel 支持网站：  
https://www.intel.com/support  

流控制  
------------  
Intel® 以太网交换机主机接口驱动程序不支持流控制。它不会发送暂停帧。这可能导致丢弃数据包。  
虚拟功能 (VFs)  
-----------------------  
使用 sysfs 启用 VFs  
有效范围：0-64  

例如：  

    echo $num_vf_enabled > /sys/class/net/$dev/device/sriov_numvfs //启用 VFs  
    echo 0 > /sys/class/net/$dev/device/sriov_numvfs //禁用 VFs  

注意：既不是设备也不是驱动程序控制 VFs 如何映射到配置空间。总线布局会因操作系统而异。在支持它的操作系统上，您可以检查 sysfs 来找到映射。  
注意：当启用 SR-IOV 模式时，硬件 VLAN 过滤和 VLAN 标签剥离/插入将保持启用状态。请在添加新的 VLAN 过滤器之前删除旧的 VLAN 过滤器。例如：  

    ip link set eth0 vf 0 vlan 100  // 为 VF 0 设置 VLAN 100  
    ip link set eth0 vf 0 vlan 0  // 删除 VLAN 100  
    ip link set eth0 vf 0 vlan 200  // 为 VF 0 设置新的 VLAN 200  

额外特性及配置  
======================  

巨型帧  
------------  
通过将最大传输单元 (MTU) 更改为大于默认值 1500 的值来启用巨型帧支持。  
使用 ifconfig 命令增加 MTU 大小。例如，输入以下命令，其中 <x> 是接口编号：  

    ifconfig eth<x> mtu 9000 up  

或者，您可以使用 ip 命令如下：  

    ip link set mtu 9000 dev eth<x>  
    ip link set up dev eth<x>  

此设置不会跨重启保存。可以通过向以下文件中添加 'MTU=9000' 使设置永久生效：  

- 对于 RHEL：/etc/sysconfig/network-scripts/ifcfg-eth<x>  
- 对于 SLES：/etc/sysconfig/network/<config_file>  

注意：巨型帧的最大 MTU 设置为 15342。该值与最大巨型帧大小 15364 字节一致。  
注意：此驱动程序将尝试使用多个页面大小的缓冲区接收每个巨型数据包。这有助于避免在分配接收数据包时出现缓冲区饥饿问题。  
通用接收卸载 (GRO)  
--------------------------------  
驱动程序支持内核中的软件实现 GRO。GRO 显示出通过将接收 (Rx) 流量合并为较大的数据块可以显著降低在大 Rx 负载下 CPU 的利用率。GRO 是先前使用的 LRO 接口的进化。GRO 可以合并除 TCP 以外的其他协议。它也可以安全地用于对 LRO 有问题的配置，如桥接和 iSCSI。  
支持的 ethtool 命令和过滤选项  
----------------------------------------------------  
-n --show-nfc  
  获取接收网络流分类配置信息
翻译如下：

将 `rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6` 配置为指定网络流量类型的哈希选项。
-N --config-nfc
配置接收网络流分类。
`rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6 m|v|t|s|d|f|n|r`
配置指定网络流量类型的哈希选项。
- udp4: UDP在IPv4之上
- udp6: UDP在IPv6之上
- f 基于接收数据包的第4层报头中的0和1字节进行哈希计算
- n 基于接收数据包的第4层报头中的2和3字节进行哈希计算

已知问题/故障排除
==================

在Linux KVM下的64位Microsoft Windows Server 2012/R2客户操作系统中启用SR-IOV
-------------------------------------------------------------------------------------
KVM Hypervisor/VMM支持将PCIe设备直接分配给虚拟机。这包括传统的PCIe设备，以及基于Intel以太网控制器XL710的SR-IOV兼容设备。

支持
=====
对于一般信息，请访问Intel支持网站：
https://www.intel.com/support/

如果在受支持内核上使用受支持适配器时发布的源代码存在问题，请将与问题相关的确切信息发送至 intel-wired-lan@lists.osuosl.org。
