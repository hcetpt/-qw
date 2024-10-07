SPDX 许可证标识符: GPL-2.0+

=================================================================
Intel(R) 以太网控制器 700 系列的 Linux 基础驱动程序
=================================================================

Intel 40 千兆以太网 Linux 驱动程序  
版权所有 (c) 1999-2018 Intel 公司  
内容
========

- 概览
- 识别您的适配器
- Intel(R) 以太网流控制器
- 额外配置
- 已知问题
- 支持

可以使用 ethtool、lspci 和 ifconfig 获取驱动程序信息。
更新 ethtool 的说明可以在本文档后面的“额外配置”部分找到。
有关硬件要求的问题，请参阅随附的 Intel 适配器文档。列出的所有硬件要求适用于 Linux。

识别您的适配器
========================
该驱动程序兼容以下设备：

 * Intel(R) 以太网控制器 X710
 * Intel(R) 以太网控制器 XL710
 * Intel(R) 以太网连接 X722
 * Intel(R) 以太网控制器 XXV710

为了获得最佳性能，请确保安装了最新版本的 NVM/FW。
有关如何识别您的适配器以及最新版本的 NVM/FW 映像和 Intel 网络驱动程序的信息，请参阅 Intel 支持网站：
https://www.intel.com/support

SFP+ 和 QSFP+ 设备
----------------------
有关支持介质的信息，请参阅此文档：
https://www.intel.com/content/dam/www/public/us/en/documents/release-notes/xl710-ethernet-controller-feature-matrix.pdf

注意：基于 Intel(R) 以太网控制器 700 系列的某些适配器仅支持 Intel 以太网光学模块。在这些适配器上，其他模块不受支持且无法正常工作。在所有情况下，Intel 建议使用 Intel 以太网光学模块；其他模块可能可以工作，但未经过 Intel 的验证。
请与 Intel 联系以获取支持的介质类型。
注意：对于基于 Intel(R) 以太网控制器 700 系列的连接，支持取决于您的系统主板。请参阅供应商获取详细信息。
注意：在没有足够气流来冷却适配器和光学模块的系统中，必须使用高温光学模块。
虚拟函数（VFs）
-----------------------
使用 sysfs 启用 VFs。例如：

```
# echo $num_vf_enabled > /sys/class/net/$dev/device/sriov_numvfs # 启用 VFs
# echo 0 > /sys/class/net/$dev/device/sriov_numvfs # 禁用 VFs
```

例如，以下指令将配置 PF eth0 和 VLAN 10 上的第一个 VF：

```
$ ip link set dev eth0 vf 0 vlan 10
```

VLAN 标签数据包导向
------------------------
允许您将具有特定 VLAN 标签的所有数据包发送到特定的 SR-IOV 虚拟函数（VF）。此外，此功能允许您将特定的 VF 指定为可信，并允许该可信 VF 请求物理功能（PF）上的选择性混杂模式。
要在 Hypervisor 中将 VF 设置为可信或不可信，请输入以下命令：

```
# ip link set dev eth0 vf 1 trust [on|off]
```

一旦 VF 被指定为可信，使用以下命令在 VM 中将 VF 设置为混杂模式：

```
对于全混杂模式：
# ip link set eth2 promisc on
其中 eth2 是 VM 中的 VF 接口

对于多播混杂模式：
# ip link set eth2 allmulticast on
其中 eth2 是 VM 中的 VF 接口
```

注意：默认情况下，ethtool 的私有标志 vf-true-promisc-support 被设置为 "off"，这意味着 VF 的混杂模式是有限制的。要将 VF 的混杂模式设置为真正的混杂模式，并允许 VF 查看所有入站流量，请使用以下命令：

```
# ethtool -set-priv-flags p261p1 vf-true-promisc-support on
```

vf-true-promisc-support 私有标志不会启用混杂模式；相反，它指定了当您使用上面的 ip link 命令启用混杂模式时，您将获得哪种类型的混杂模式（有限制的或真正的）。请注意，这是一个影响整个设备的全局设置。但是，vf-true-promisc-support 私有标志仅对设备的第一个 PF 可见。无论 vf-true-promisc-support 设置如何，PF 仍然处于有限混杂模式（除非它处于 MFP 模式）。

现在在 VF 接口上添加一个 VLAN 接口：

```
# ip link add link eth2 name eth2.100 type vlan id 100
```

请注意，将 VF 设置为混杂模式和添加 VLAN 接口的顺序无关紧要（您可以先做任何一个）。在这个示例中，最终结果是 VF 将获取所有带有 VLAN 100 标签的流量。

英特尔® 以太网流导向器
-------------------------------
英特尔以太网流导向器执行以下任务：

- 根据其流将接收的数据包导向到不同的队列
- 允许平台上的流路由进行紧密控制
- 匹配流与 CPU 核心以实现流亲和力
- 支持多种参数以实现灵活的流分类和负载均衡（仅在 SFP 模式下）

注意：Linux i40e 驱动支持以下流类型：IPv4、TCPv4 和 UDPv4。对于给定的流类型，它支持有效的 IP 地址组合（源地址或目标地址）和 UDP/TCP 端口（源端口和目标端口）。例如，您可以只提供源 IP 地址、源 IP 地址和目标端口，或者这四个参数中的任意组合。

注意：Linux i40e 驱动允许您使用 ethtool 的用户定义和掩码字段，根据用户定义的可变两字节模式和偏移量过滤流量。仅支持 L3 和 L4 流类型用于用户定义的灵活过滤器。对于给定的流类型，在更改输入集之前，必须清除所有英特尔以太网流导向器过滤器。
启用或禁用Intel以太网流导向器：

  # ethtool -K ethX ntuple <on|off>

当禁用ntuple过滤器时，所有用户编程的过滤器都会从驱动程序缓存和硬件中清除。重新启用ntuple时，必须重新添加所有需要的过滤器。
要添加一个将数据包导向队列2的过滤器，请使用-U或-N开关：

  # ethtool -N ethX flow-type tcp4 src-ip 192.168.10.1 dst-ip 192.168.10.2 src-port 2000 dst-port 2001 action 2 [loc 1]

仅使用源IP地址和目标IP地址设置过滤器：

  # ethtool -N ethX flow-type tcp4 src-ip 192.168.10.1 dst-ip 192.168.10.2 action 2 [loc 1]

查看当前存在的过滤器列表：

  # ethtool <-u|-n> ethX

应用目标路由（ATR）完美过滤器
---------------------------------
当内核处于多发送队列模式时，默认情况下ATR是启用的。
当一个TCP/IP流开始时，会添加一个ATR Intel以太网流导向器过滤规则，并在流结束时删除该规则。当通过ethtool（旁路过滤器）添加TCP/IP Intel以太网流导向器规则时，驱动程序会关闭ATR。要重新启用ATR，可以使用ethtool -K选项禁用旁路功能。例如：

  ethtool -K [adapter] ntuple [off|on]

如果在重新启用ATR之后再次启用旁路功能，则ATR会保持启用状态，直到添加一个TCP/IP流。当所有TCP/IP旁路规则被删除后，ATR会自动重新启用。
匹配ATR规则的数据包会在ethtool的fdir_atr_match统计信息中计数，也可以用于验证是否仍然存在ATR规则。
旁路完美过滤器
-----------------------
旁路完美过滤器用于定向符合特定特征的流量。它们是通过ethtool的ntuple接口启用的。要添加一个新的过滤器，请使用以下命令：

  ethtool -U <device> flow-type <type> src-ip <ip> dst-ip <ip> src-port <port> dst-port <port> action <queue>

其中：
  <device> - 要编程的以太网设备
  <type> - 可以是ip4、tcp4、udp4或sctp4
  <ip> - 要匹配的IP地址
  <port> - 要匹配的端口号
  <queue> - 要定向流量的目标队列（-1丢弃匹配流量）

使用以下命令显示所有活动过滤器：

  ethtool -u <device>

使用以下命令删除一个过滤器：

  ethtool -U <device> delete <N>

其中<N>是在打印所有活动过滤器时显示的过滤器ID，也可以在添加过滤器时使用“loc <N>”指定。
以下示例匹配从192.168.0.1发出的TCP流量，端口为5300，目标为192.168.0.5，端口为80，并将其发送到队列7：

  ethtool -U enp130s0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.0.5 src-port 5300 dst-port 80 action 7

对于每个flow-type，编程的过滤器必须具有相同的匹配输入集。例如，执行以下两个命令是可以接受的：

  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.5 src-port 55 action 10

但是，执行接下来的两个命令是不可接受的，因为第一个指定了src-ip，而第二个指定了dst-ip：

  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  ethtool -U enp130s0 flow-type ip4 dst-ip 192.168.0.5 src-port 55 action 10

第二个命令将以错误失败。您可以在同一设备上使用不同的值编程多个具有相同字段的过滤器，但不能在同一设备上编程两个具有不同匹配字段的tcp4过滤器。
i40e驱动程序不支持对字段的部分子集进行匹配，因此不支持部分掩码字段。
驱动程序还支持在数据包有效载荷内匹配用户定义的数据。
此灵活数据使用ethtool命令中的"user-def"字段以如下方式指定：

+----------------------------+--------------------------+
| 31    28    24    20    16 | 15    12    8    4    0  |
+----------------------------+--------------------------+
| 进入数据包有效载荷的偏移量 | 2字节的灵活数据          |
+----------------------------+--------------------------+

例如，

  ... user-def 0x4FFFF ..
告诉过滤器查找有效载荷中的第4个字节，并将该值与0xFFFF进行匹配。偏移量基于有效载荷的开头，而不是数据包的开头。因此，

  flow-type tcp4 ... user-def 0x8BEAF ..
会匹配 TCP/IPv4 数据包中，在 TCP/IPv4 负载的第 8 个字节处具有值 0xBEAF 的数据包。
请注意，ICMP 头部被视为 4 字节头部和 4 字节负载。
因此，要匹配负载的第一个字节，实际上需要在偏移量上加上 4 字节。
还需注意的是，ip4 过滤器同时匹配 ICMP 帧和原始（未知）ip4 帧，其中负载将是 IP4 帧的 L3 负载。
最大偏移量为 64。硬件只会从负载中读取最多 64 字节的数据。
偏移量必须是偶数，因为灵活数据长度为 2 字节，并且必须对齐到数据包负载的第 0 字节。
用户定义的灵活偏移量也被视为输入集的一部分，不能单独为同一类型的多个过滤器编程。但是，灵活数据不是输入集的一部分，多个过滤器可以使用相同的偏移量但匹配不同的数据。
为了创建将流量导向特定虚拟功能（Virtual Function）的过滤器，请使用“action”参数。指定该动作为一个 64 位值，其中低 32 位表示队列编号，而接下来的 8 位表示哪个虚拟功能（VF）。
请注意，0 表示物理功能（PF），所以虚拟功能标识符偏移了 1。例如：

  ... action 0x800000002 ..
表示将流量导向虚拟功能 7（8 减 1）中的队列 2。
请注意，这些过滤器不会破坏内部路由规则，也不会将原本不会发送到指定虚拟功能的流量进行路由。

设置 link-down-on-close 私有标志
-------------------------------------
当 link-down-on-close 私有标志设置为“on”时，使用 ifconfig ethX down 命令关闭接口时，端口的链路将会断开。
使用 `ethtool` 查看和设置 `link-down-on-close`，如下所示：

```
ethtool --show-priv-flags ethX
ethtool --set-priv-flags ethX link-down-on-close [on|off]
```

查看链路消息
---------------------
如果操作系统限制了系统消息，则控制台不会显示链路消息。为了在控制台上看到网络驱动的链路消息，请输入以下命令将 `dmesg` 设置为 8：

```
dmesg -n 8
```

**注意：** 此设置不会在重启后保存。

巨型帧（Jumbo Frames）
-------------------------
通过将最大传输单元（MTU）更改为大于默认值 1500 的值来启用巨型帧支持。
使用 `ifconfig` 命令增加 MTU 大小。例如，输入以下命令，其中 `<x>` 是接口编号：

```
ifconfig eth<x> mtu 9000 up
```

或者，可以使用 `ip` 命令如下：

```
ip link set mtu 9000 dev eth<x>
ip link set up dev eth<x>
```

此设置不会在重启后保存。可以通过在以下文件中添加 `MTU=9000` 来使设置永久生效：

```
/etc/sysconfig/network-scripts/ifcfg-eth<x> // 对于 RHEL
/etc/sysconfig/network/<config_file> // 对于 SLES
```

**注意：** 巨型帧的最大 MTU 设置为 9702。这个值与最大巨型帧大小 9728 字节相匹配。

**注意：** 此驱动程序将尝试使用多个页面大小的缓冲区来接收每个巨型数据包。这有助于避免分配接收数据包时出现缓冲区饥饿问题。

ethtool
-------
该驱动程序利用 ethtool 接口进行配置、诊断以及显示统计信息。此功能需要最新版本的 ethtool。下载地址为：
https://www.kernel.org/pub/software/network/ethtool/

支持的 ethtool 命令和过滤选项
--------------------------------
-n --show-nfc
  获取接收网络流分类配置
rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6
  获取指定网络流量类型的哈希选项
-N --config-nfc
  配置接收网络流分类
rx-flow-hash tcp4|udp4|ah4|esp4|sctp4|tcp6|udp6|ah6|esp6|sctp6 m|v|t|s|d|f|n|r..
  配置指定网络流量类型的哈希选项
udp4 UDP over IPv4
udp6 UDP over IPv6

f 在接收数据包的第 4 层头部的前两个字节上进行哈希
在接收数据包的第四层头部的第2和第3个字节上进行哈希运算

速度和双工配置
----------------
在处理速度和双工配置问题时，需要区分基于铜线的适配器和基于光纤的适配器。

默认模式下，使用铜线连接的Intel® 以太网网络适配器将尝试与其链路伙伴自动协商以确定最佳设置。如果适配器无法通过自动协商与链路伙伴建立连接，则可能需要手动配置适配器及其链路伙伴到相同的设置，以便建立连接并传输数据包。这通常只在尝试连接不支持自动协商或已被强制到特定速度或双工模式的旧交换机时才需要。您的链路伙伴必须匹配您选择的设置。1 Gbps及以上的速度不能被强制设置。使用自动协商广告设置来手动设置1 Gbps及以上的设备。

注意：您不能为基于Intel® 以太网网络适配器XXV710的设备设置速度。

速度、双工和自动协商广告设置是通过ethtool工具进行配置的。

警告：只有经验丰富的网络管理员才能手动强制速度和双工或更改自动协商广告设置。交换机上的设置必须始终与适配器设置相匹配。如果您将适配器配置得与交换机不同，适配器性能可能会下降或无法正常运行。

然而，使用光纤连接的Intel® 以太网网络适配器不会尝试与其链路伙伴自动协商，因为这些适配器仅在全双工模式下运行，并且仅在其本机速度下工作。

NAPI
----
NAPI（接收轮询模式）在i40e驱动程序中得到支持。
更多信息请参阅 :ref:`Documentation/networking/napi.rst <napi>`。

流量控制
---------
可以使用ethtool配置以太网流量控制（IEEE 802.3x），以启用i40e接收和发送暂停帧。当启用发送时，如果接收数据包缓冲区超过预定义的阈值，则生成暂停帧。当启用接收时，接收到暂停帧时，发送单元将停止指定的时间延迟。
注意：您必须拥有支持流控制的链路伙伴
流控制默认是开启的
使用 `ethtool` 来更改流控制设置
要启用或禁用接收（Rx）或发送（Tx）流控制，请执行：

  `ethtool -A eth? rx <on|off> tx <on|off>`

注意：此命令仅在禁用了自动协商的情况下启用或禁用流控制。如果启用了自动协商，此命令将更改与链路伙伴进行自动协商时使用的参数。
要启用或禁用自动协商，请执行：

  `ethtool -s eth? autoneg <on|off>`

注意：流控制自动协商是链路自动协商的一部分。根据您的设备，您可能无法更改自动协商设置。

RSS Hash 流
-----------
允许您为每种流类型设置哈希字节，并且可以组合一个或多个选项来配置接收端扩展（RSS）哈希字节

  `# ethtool -N <dev> rx-flow-hash <type> <option>`

其中 `<type>` 是：
  tcp4   表示 TCP 过 IPv4
  udp4   表示 UDP 过 IPv4
  tcp6   表示 TCP 过 IPv6
  udp6   表示 UDP 过 IPv6
而 `<option>` 是以下的一个或多个：
  s     基于接收包的 IP 源地址进行哈希
  d     基于接收包的 IP 目标地址进行哈希
  f     基于接收包第 4 层头部的第 0 和第 1 字节进行哈希
  n     基于接收包第 4 层头部的第 2 和第 3 字节进行哈希
MAC 和 VLAN 防欺骗功能
----------------------------------
当恶意驱动程序尝试发送伪造的数据包时，硬件会丢弃该数据包而不进行传输。
注意：此功能可以为特定的虚拟功能（VF）禁用：

  ip link set <pf dev> vf <vf id> spoofchk {off|on}

IEEE 1588 精确时间协议（PTP）硬件时钟（PHC）
------------------------------------------------------------
精确时间协议（PTP）用于同步计算机网络中的时钟。支持此驱动程序的不同 Intel 设备对 PTP 的支持程度不同。使用 "ethtool -T <netdev name>" 获取设备支持的 PTP 功能列表。
IEEE 802.1ad（QinQ）支持
---------------------------
IEEE 802.1ad 标准，俗称 QinQ，允许在单个以太网帧中包含多个 VLAN ID。VLAN ID 有时被称为“标签”，因此多个 VLAN ID 被称为“标签堆栈”。标签堆栈允许 L2 隧道，并且能够在特定的 VLAN ID 内隔离流量等用途。
以下是配置 802.1ad（QinQ）的示例：

  ip link add link eth0 eth0.24 type vlan proto 802.1ad id 24
  ip link add link eth0.24 eth0.24.371 type vlan proto 802.1Q id 371

其中“24”和“371”是示例 VLAN ID。
注意：
  对于 802.1ad（QinQ）数据包，不支持接收校验和卸载、云过滤器和 VLAN 加速。
VXLAN 和 GENEVE Overlay 硬件卸载
--------------------------------------
虚拟可扩展局域网（VXLAN）允许您通过第 3 层网络扩展第 2 层网络，这在虚拟化或云计算环境中可能很有用。某些 Intel(R) 以太网网络设备执行 VXLAN 处理，将其从操作系统中卸载。这减少了 CPU 利用率。
VXLAN 卸载由 ethtool 提供的 Tx 和 Rx 校验和卸载选项控制。也就是说，如果启用了 Tx 校验和卸载，并且适配器具有此功能，则 VXLAN 卸载也被启用。
对 VXLAN 和 GENEVE 硬件卸载的支持取决于内核对该硬件卸载功能的支持。
每个端口的多个功能
---------------------------
基于 Intel 以太网控制器 X710/XL710 的一些适配器支持在单个物理端口上实现多个功能。通过系统设置/BIOS 配置这些功能。
最小 TX 带宽是分配给分区的保证最小数据传输带宽，以全物理端口链路速度的百分比表示。分区获得的带宽永远不会低于您指定的水平。
最小带宽值的范围为：
1 到 ((100 减去物理端口上的分区数) 加 1)
例如，如果一个物理端口有 4 个分区，则范围为：
1 到 ((100 - 4) + 1 = 97)

最大带宽百分比代表分配给分区的最大传输带宽占整个物理端口链路速度的百分比。可接受的值范围是 1-100。此值用于限制，以防某个特定功能占用端口 100% 的带宽（如果有可用带宽）。所有最大带宽值之和不受限制，因为任何情况下都不会使用超过端口 100% 的带宽。

注意：X710/XXV710 设备在启用每端口多功能（MFP）和 SR-IOV 时无法启用最大虚拟功能（VF）数量（64）。i40e 会记录一条错误信息“添加 vsi 失败，VF N，aq_err 16”。为了绕过该问题，请启用少于 64 个虚拟功能（VF）。

数据中心桥接（DCB）
-------------------------
DCB 是硬件中实现的一种配置服务质量机制。它使用 VLAN 优先级标签（802.1p）来过滤流量。这意味着可以将流量过滤到 8 个不同的优先级中。它还启用了优先流控制（802.1Qbb），可以在网络压力期间限制或消除丢包数量。可以为这些优先级分配带宽，并且在硬件级别上强制执行（802.1Qaz）。
适配器固件根据 802.1AB 和 802.1Qaz 分别实现了 LLDP 和 DCBX 协议代理。基于固件的 DCBX 代理仅运行在愿意模式下，并可以从支持 DCBX 的对等体接收设置。通过 dcbtool/lldptool 配置 DCBX 参数不受支持。

注意：可以通过设置私有标志 disable-fw-lldp 来禁用固件 LLDP。
i40e 驱动程序实现了 DCB netlink 接口层，允许用户空间与驱动程序通信并查询端口的 DCB 配置。

注意：
内核假定 TC0 可用，并且如果 TC0 不可用，则会在设备上禁用优先流控制（PFC）。要修复此问题，请确保在设置交换机上的 DCB 时启用 TC0。

中断速率限制
-----------------------
有效范围：0-235（0=无限制）

Intel(R) Ethernet Controller XL710 系列支持一种中断速率限制机制。用户可以通过 ethtool 控制中断之间的微秒数。
语法如下：

```
# ethtool -C ethX rx-usecs-high N
```

0-235 微秒的范围提供了每秒 4,310 到 250,000 次中断的有效范围。rx-usecs-high 的值可以独立于同一 ethtool 命令中的 rx-usecs 和 tx-usecs 设置，并且也独立于自适应中断调节算法。底层硬件支持 4 微秒的粒度，因此相邻的值可能导致相同的中断速率。

一个可能的用例如下：

```
# ethtool -C ethX adaptive-rx off adaptive-tx off rx-usecs-high 20 rx-usecs 5 tx-usecs 5
```

上述命令会禁用自适应中断调节，并允许在指示接收或发送完成之前最多等待 5 微秒。
然而，这并没有导致每秒多达200,000次的中断，而是通过`rx-usecs-high`参数将每秒的总中断限制在50,000次。

性能优化
========================
驱动程序默认设置旨在适应各种工作负载，但如果需要进一步优化，我们建议尝试以下设置：

注意：为了在处理小（64字节）帧大小时获得更好的性能，请在BIOS中启用超线程以增加系统中的逻辑核心数量，并相应地增加适配器可用的队列数量。

虚拟化环境
------------------------
1. 使用附带的`virt_perf_default`脚本或以root用户运行以下命令来禁用两端的XPS：

  ```
  for file in `ls /sys/class/net/<ethX>/queues/tx-*/xps_cpus`;
  do echo 0 > $file; done
  ```

2. 在虚拟机中使用适当机制（如vcpupin）将CPU绑定到单个lcpu上，并确保使用包含在设备`local_cpulist`中的CPU集：`/sys/class/net/<ethX>/device/local_cpulist`

3. 在虚拟机中配置尽可能多的Rx/Tx队列。不要依赖默认设置为1的队列数。

非虚拟化环境
---------------------------
通过禁用`irqbalance`服务并使用附带的`set_irq_affinity`脚本来将适配器的IRQ绑定到特定的核心。请参阅脚本的帮助文本以获取更多选项。
- 以下设置将在所有核心之间均匀分布IRQ：

  ```
  # scripts/set_irq_affinity -x all <interface1> , [ <interface2>, ... ]
  ```

- 以下设置将IRQ分布在与适配器位于同一NUMA节点的所有核心上：

  ```
  # scripts/set_irq_affinity -x local <interface1> ,[ <interface2>, ... ]
  ```

对于非常CPU密集的工作负载，我们建议将IRQ绑定到所有核心。

对于IP转发：使用ethtool禁用自适应ITR并降低每个队列的Rx和Tx中断。
- 将`rx-usecs`和`tx-usecs`设置为125将把每个队列的中断限制在每秒约8000次：
  
  ```
  # ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 125 \
    tx-usecs 125
  ```

为了降低CPU利用率：使用ethtool禁用自适应ITR并降低每个队列的Rx和Tx中断。
将 `rx-usecs` 和 `tx-usecs` 设置为 250 将限制每个队列每秒的中断次数约为 4000 次。

:: 

  # ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 250 \
    tx-usecs 250

为了降低延迟：禁用自适应 ITR 和 ITR，通过 ethtool 将 Rx 和 Tx 设置为 0。

:: 

  # ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 0 \
    tx-usecs 0

应用设备队列（ADq）
-------------------
应用设备队列（ADq）允许您将一个或多个队列专用于特定的应用程序。这可以减少指定应用程序的延迟，并允许按应用程序限制 Tx 流量。按照以下步骤设置 ADq：

1. 创建流量类别（TCs）。每个接口最多可创建 8 个 TCs。
   `shaper bw_rlimit` 参数是可选的。
   示例：设置两个 TCs，分别为 tc0 和 tc1，各包含 16 个队列，并将 tc0 的最大 Tx 速率设为 1Gbps，tc1 设为 3Gbps。

   ::

     # tc qdisc add dev <interface> root mqprio num_tc 2 map 0 0 0 0 1 1 1 1 \
       queues 16@0 16@16 hw 1 mode channel shaper bw_rlimit min_rate 1Gbit 2Gbit \
       max_rate 1Gbit 3Gbit

   map：将最多 16 个优先级映射到 TCs（例如，map 0 0 0 0 1 1 1 1 将优先级 0-3 映射到 tc0，优先级 4-7 映射到 tc1）。

   queues：对于每个 TC，<队列数>@<偏移量>（例如，queues 16@0 16@16 表示为 tc0 分配 16 个队列，偏移量为 0；为 tc1 分配 16 个队列，偏移量为 16。所有 TCs 的总队列数的最大值为 64 或核心数，取较小者）。

   hw 1 mode channel：在 mqprio 中，使用 'channel' 并将 'hw' 设置为 1 是一种新的硬件卸载模式，该模式充分利用了 mqprio 选项、TCs、队列配置和 QoS 参数。
   shaper bw_rlimit：为每个 TC 设置最小和最大带宽速率。总量必须等于或小于端口速度。
   例如：min_rate 1Gbit 3Gbit：使用网络监控工具（如 `ifstat` 或 `sar -n DEV [interval] [number of samples]`）验证带宽限制。

2. 在接口上启用 HW TC 卸载：

   # ethtool -K <interface> hw-tc-offload on

3. 将 TC 应用于接口的入站（RX）流：

   # tc qdisc add dev <interface> ingress

注意事项：
- 所有 tc 命令都应从 iproute2 <pathtoiproute2>/tc/ 目录运行。
- ADq 与云过滤器不兼容
- 当使用 mqprio 配置 TC 时，不支持通过 ethtool（ethtool -L）设置通道
- 必须使用最新版本的 iproute2
- 需要 NVM 版本 6.01 或更高版本
- 启用以下任一功能时，无法启用 ADq：数据中心桥接 (DCB)、每个端口的多个功能 (MFP) 或旁路过滤器
- 如果其他驱动程序（例如 DPDK）设置了云过滤器，则无法启用 ADq
- 不支持隧道过滤器。如果在非隧道模式下接收到封装数据包，则将对内部报头进行过滤
例如，在非隧道模式下的 VXLAN 流量中，PCTYPE 被识别为 VXLAN 封装的数据包，外部报头被忽略。因此，匹配的是内部报头
- 如果 PF 上的一个 TC 过滤器匹配了通过 VF（在 PF 上）的流量，则该流量将被路由到 PF 的相应队列，并且不会传递给 VF。此类流量会在 TCP/IP 栈的更高层被丢弃，因为它不匹配 PF 地址数据
- 如果流量匹配多个指向不同 TC 的 TC 过滤器，则该流量会被复制并发送到所有匹配的 TC 队列
硬件交换机在匹配多个过滤器时会将数据包镜像到 VSI 列表中
已知问题/故障排除
============================

**注意：** 基于 Intel(R) Ethernet Network Connection X722 的 1 Gb 设备不支持以下功能：

  * 数据中心桥接 (DCB)
  * QoS
  * VMQ
  * SR-IOV
  * 任务封装卸载（VXLAN、NVGRE）
  * 能效以太网 (EEE)
  * 自动介质检测

设备驱动程序和 DPDK 共享设备时的意外问题
------------------------------------------------
当 i40e 设备处于多驱动模式且内核驱动程序和 DPDK 驱动程序共享该设备时，可能会出现意外问题。这是因为多个驱动程序之间没有同步对全局 NIC 资源的访问。任何对全局 NIC 配置的更改（写入全局寄存器、通过 AQ 设置全局配置或更改交换模式）都会影响设备上的所有端口和驱动程序。加载 DPDK 时使用 "multi-driver" 模块参数可能会缓解部分问题。

在设置交换机上的 DCB 时必须启用 TC0
---------------------------------------------------
内核假定 TC0 是可用的，并且如果 TC0 不可用，则会在设备上禁用优先流控制 (PFC)。为了解决这个问题，请确保在设置交换机上的 DCB 时启用 TC0。

支持
======
有关一般信息，请访问 Intel 支持网站：
https://www.intel.com/support/

如果在受支持的内核上使用受支持的适配器时发现发布的源代码存在问题，请将与问题相关的确切信息发送至 intel-wired-lan@lists.osuosl.org。
