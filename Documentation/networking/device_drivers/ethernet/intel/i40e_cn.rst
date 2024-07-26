... SPDX 许可证标识符：GPL-2.0+ 

================================================================= 
针对 Intel® 以太网控制器 700 系列的 Linux 基础驱动程序 
================================================================= 

Intel 40 千兆位 Linux 驱动程序  
版权所有 (c) 1999-2018 Intel 公司  
内容  
========  

- 概览
- 识别您的适配器
- Intel® 以太网流控制器
- 额外配置
- 已知问题
- 支持

可以使用 ethtool、lspci 和 ifconfig 获取驱动程序信息。  
有关更新 ethtool 的说明，请参阅本文档后面部分的“额外配置”。  
对于与硬件要求相关的问题，请参考随附 Intel 适配器提供的文档。列出的所有硬件要求均适用于 Linux。  
识别您的适配器  
========================  

本驱动程序与基于以下设备的产品兼容：  

 * Intel® 以太网控制器 X710
 * Intel® 以太网控制器 XL710
 * Intel® 以太网网络连接 X722
 * Intel® 以太网控制器 XXV710

为了获得最佳性能，请确保在您的设备上安装了最新的 NVM/固件。  
有关如何识别您的适配器以及最新 NVM/固件映像和 Intel 网络驱动程序的信息，请参阅 Intel 支持网站：  
https://www.intel.com/support  

SFP+ 和 QSFP+ 设备  
----------------------  

有关支持的媒体信息，请参阅此文档：  
https://www.intel.com/content/dam/www/public/us/en/documents/release-notes/xl710-ethernet-controller-feature-matrix.pdf  

**注意**：基于 Intel® 以太网控制器 700 系列的某些适配器仅支持 Intel 以太网光学模块。对于这些适配器，不支持其他模块且无法正常工作。在所有情况下，Intel 建议使用 Intel 以太网光学模块；其他模块可能能够工作但未经过 Intel 的验证。请向 Intel 查询支持的媒体类型。  
**注意**：对于基于 Intel® 以太网控制器 700 系列的连接，支持取决于您的系统主板。请咨询供应商了解详情。  
**注意**：在没有足够气流来冷却适配器和光学模块的系统中，您必须使用高温光学模块。
### 虚拟函数（VFs）
-----------------------
使用 sysfs 来启用 VFs。例如：

```shell
# echo $num_vf_enabled > /sys/class/net/$dev/device/sriov_numvfs  # 启用 VFs
# echo 0 > /sys/class/net/$dev/device/sriov_numvfs  # 禁用 VFs
```

例如，以下指令将配置 PF（物理功能）eth0 和第一个 VF 在 VLAN 10 上：

```shell
$ ip link set dev eth0 vf 0 vlan 10
```

### VLAN 标签数据包导向
------------------------
允许您将具有特定 VLAN 标签的所有数据包发送到特定的 SR-IOV 虚拟函数（VF）。此外，此功能允许您指定某个 VF 为可信的，并允许该可信 VF 请求物理功能（PF）上的选择性混杂模式。
要设置一个 VF 为可信或不可信，进入以下命令在 Hypervisor 中：

```shell
# ip link set dev eth0 vf 1 trust [on|off]
```

一旦 VF 被指定为可信，使用下面的命令在 VM 中将 VF 设置为混杂模式：

```shell
对于所有混杂模式：
# ip link set eth2 promisc on
其中 eth2 是 VM 中的 VF 接口

对于多播混杂模式：
# ip link set eth2 allmulticast on
其中 eth2 是 VM 中的 VF 接口
```

**注意**：默认情况下，ethtool 私有标志 `vf-true-promisc-support` 设置为 "off"，意味着 VF 的混杂模式是有限的。为了将 VF 的混杂模式设置为真正的混杂模式并允许 VF 查看所有入站流量，请使用以下命令：

```shell
# ethtool -set-priv-flags p261p1 vf-true-promisc-support on
```

`vf-true-promisc-support` 私有标志并不开启混杂模式；相反，它指定了当您使用上面的 ip link 命令启用混杂模式时，您将获得哪种类型的混杂模式（有限的或真正的）。请注意这是一个影响整个设备的全局设置。然而，`vf-true-promisc-support` 私有标志只对设备的第一个 PF 可见。PF 保持有限的混杂模式（除非处于 MFP 模式），无论 `vf-true-promisc-support` 设置如何。
现在在 VF 接口上添加一个 VLAN 接口：

```shell
# ip link add link eth2 name eth2.100 type vlan id 100
```

请注意，您设置 VF 为混杂模式和添加 VLAN 接口的顺序无关紧要（您可以先做任何一个）。在这个例子中最终结果是 VF 将获得所有带有 VLAN 100 标签的流量。

### 英特尔® 以太网流导向器
-------------------------------
英特尔以太网流导向器执行以下任务：

- 根据它们的流将接收的数据包导向不同的队列
- 允许对平台中的流路由进行严格控制
- 匹配流与 CPU 内核以确定流亲和性
- 支持多个参数用于灵活的流分类和负载均衡（仅在 SFP 模式下）

**注**：Linux i40e 驱动程序支持以下流类型：IPv4、TCPv4 和 UDPv4。对于给定的流类型，它支持 IP 地址（源或目的）以及 UDP/TCP 端口（源和目的）的有效组合。例如，您可以仅提供源 IP 地址、源 IP 地址和目的端口，或者这四个参数中的任何组合。

**注**：Linux i40e 驱动程序允许您根据用户定义的可灵活调整的两字节模式和偏移量过滤流量，使用 ethtool 的 user-def 和 mask 字段。仅支持 L3 和 L4 流类型用于用户定义的可灵活调整的过滤器。对于给定的流类型，您必须清除所有英特尔以太网流导向器过滤器才能更改输入集（对于该流类型）。
要启用或禁用Intel以太网流导向器的ntuple过滤功能：

  # ethtool -K ethX ntuple <on|off>

当禁用ntuple过滤器时，所有用户编程的过滤器都会从驱动程序缓存和硬件中清除。重新启用ntuple时必须重新添加所有需要的过滤器。
要添加一个将数据包导向队列2的过滤器，请使用-U或-N开关：

  # ethtool -N ethX flow-type tcp4 src-ip 192.168.10.1 dst-ip \
  192.168.10.2 src-port 2000 dst-port 2001 action 2 [loc 1]

仅使用源和目标IP地址设置过滤器：

  # ethtool -N ethX flow-type tcp4 src-ip 192.168.10.1 dst-ip \
  192.168.10.2 action 2 [loc 1]

查看当前存在的过滤器列表：

  # ethtool <-u|-n> ethX

应用定向路由（ATR）完美过滤器
--------------------------------
当内核处于多传输队列模式时，默认情况下会启用ATR。
当TCP/IP流开始时会添加一条ATR Intel以太网流导向器过滤规则，并在流结束时删除该规则。当通过ethtool（侧边过滤器）添加TCP/IP Intel以太网流导向器规则时，驱动程序会关闭ATR。要重新启用ATR，可以使用ethtool -K选项禁用侧边过滤器。例如：

  ethtool -K [adapter] ntuple [off|on]

如果在重新启用ATR之后重新启用侧边过滤器，则ATR保持启用状态，直到添加TCP/IP流。当删除所有TCP/IP侧边规则时，ATR会自动重新启用。
匹配ATR规则的数据包会被计数到ethtool中的fdir_atr_match统计信息中，也可以用于验证是否仍存在ATR规则。
侧边完美过滤器
--------------------
侧边完美过滤器用于将符合指定特性的流量导向特定队列。它们通过ethtool的ntuple接口启用。要添加一个新的过滤器，请使用以下命令：

  ethtool -U <device> flow-type <type> src-ip <ip> dst-ip <ip> src-port <port> \
  dst-port <port> action <queue>

其中：
  <device> - 要编程的以太网设备
  <type> - 可以是ip4、tcp4、udp4或sctp4
  <ip> - 要匹配的IP地址
  <port> - 要匹配的端口号
  <queue> - 将流量导向的队列（-1丢弃匹配的流量）

使用以下命令显示所有活动过滤器：

  ethtool -u <device>

使用以下命令删除过滤器：

  ethtool -U <device> delete <N>

其中<N>是在打印所有活动过滤器时显示的过滤器ID，也可能在添加过滤器时使用"loc <N>"指定
下面的例子匹配从192.168.0.1发送的TCP流量，端口5300，指向192.168.0.5，端口80，并将其发送到队列7：

  ethtool -U enp130s0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.0.5 \
  src-port 5300 dst-port 80 action 7

对于每种flow-type，编程的过滤器都必须具有相同的匹配输入集。例如，发出以下两个命令是可以接受的：

  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.5 src-port 55 action 10

然而，发出以下两个命令是不可接受的，因为第一个指定了src-ip而第二个指定了dst-ip：

  ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  ethtool -U enp130s0 flow-type ip4 dst-ip 192.168.0.5 src-port 55 action 10

第二个命令将以错误失败。您可以为相同的字段编程多个过滤器，使用不同的值，但在一个设备上，您不能编程两个具有不同匹配字段的tcp4过滤器。
i40e驱动程序不支持对字段的子部分进行匹配，因此不支持部分掩码字段。
驱动程序还支持匹配包负载内的用户定义的数据
此灵活数据可通过ethtool命令的"user-def"字段以以下方式指定：

+----------------------------+--------------------------+
| 31    28    24    20    16 | 15    12    8    4    0  |
+----------------------------+--------------------------+
| 包负载中的偏移量           | 2字节的灵活数据          |
+----------------------------+--------------------------+

例如，

::

  ... user-def 0x4FFFF ..

告诉过滤器查找负载中的第4个字节，并将该值与0xFFFF进行匹配。偏移量基于负载的开始位置，而不是包的开始位置。因此，

::

  flow-type tcp4 ... user-def 0x8BEAF ..
将匹配那些在 TCP/IPv4 负载的第 8 个字节处具有值 0xBEAF 的 TCP/IPv4 数据包。
需要注意的是，ICMP 头部被视为 4 字节头部和 4 字节负载。因此，为了匹配负载的第一个字节，实际上必须在偏移量上加上 4 字节。
同样需要注意的是，ip4 过滤器既匹配 ICMP 帧也匹配原始（未知）的 ip4 帧，在这些帧中，负载将是 IP4 帧的第三层负载。
最大偏移量是 64。硬件仅从负载读取最多 64 字节的数据。偏移量必须是偶数，因为灵活数据长度为 2 字节，并且必须与数据包负载的第 0 字节对齐。
用户定义的灵活偏移量也被视为输入集的一部分，不能为同一类型的多个过滤器单独编程。然而，灵活数据不是输入集的一部分，多个过滤器可以使用相同的偏移量但匹配不同的数据。
要创建将流量导向特定虚拟功能的过滤器，请使用 "action" 参数。指定该操作为一个 64 位值，其中较低的 32 位表示队列编号，而接下来的 8 位表示哪个虚拟功能（VF）。
需要注意的是，0 表示物理功能（PF），因此虚拟功能标识符偏移了 1。例如：

  ... action 0x800000002 ..
表示将流量导向虚拟功能 7（8 减 1）的该 VF 的第 2 队列。
需要注意的是，这些过滤器不会破坏内部路由规则，也不会将原本不应发送到指定虚拟功能的流量进行路由。

设置 link-down-on-close 私有标志
------------------------------------
当将 link-down-on-close 私有标志设置为 "on" 时，当使用 ifconfig ethX down 命令关闭接口时，端口的链路将会断开。
使用`ethtool`查看和设置链接关闭时的链接状态，如下所示：

  `ethtool --show-priv-flags ethX`
  `ethtool --set-priv-flags ethX link-down-on-close [on|off]`

查看链接消息
---------------------
如果发行版限制了系统消息，则不会在控制台上显示链接消息。为了在您的控制台上看到网络驱动程序的链接消息，请通过输入以下命令将`dmesg`设置为8：

  `dmesg -n 8`

**注意**：此设置不会跨重启保存。
巨型帧
------------
通过将最大传输单元（MTU）更改为大于默认值1500的值来启用巨型帧支持。
使用`ifconfig`命令增加MTU大小。例如，输入以下内容，其中`<x>`是接口编号：

  `ifconfig eth<x> mtu 9000 up`

或者，您也可以使用`ip`命令如下所示：

  `ip link set mtu 9000 dev eth<x>`
  `ip link set up dev eth<x>`

此设置不会跨重启保存。可以通过在文件中添加`MTU=9000`来使设置更改永久生效：

  `/etc/sysconfig/network-scripts/ifcfg-eth<x>` // 对于RHEL
  `/etc/sysconfig/network/<config_file>` // 对于SLES

**注意**：巨型帧的最大MTU设置为9702。此值与9728字节的最大巨型帧大小相匹配。
**注意**：此驱动程序会尝试使用多个页面大小的缓冲区来接收每个巨型数据包。这应该有助于避免在分配接收数据包时出现缓冲区饥饿问题。
ethtool
-------
该驱动程序利用`ethtool`接口进行驱动程序配置和诊断，以及显示统计信息。为此功能需要最新版本的`ethtool`。可以在以下网址下载：
https://www.kernel.org/pub/software/network/ethtool/

支持的`ethtool`命令和过滤选项
----------------------------------------------------
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

f 基于接收数据包第四层头部的第0和第1字节进行哈希
在第四层报头的第2和第3个字节上进行哈希运算  
速度与双工配置  
----------------  
处理速度和双工配置问题时，你需要区分基于铜线的适配器和基于光纤的适配器。  
默认模式下，使用铜线连接的Intel® 以太网网络适配器会尝试与其链路伙伴自动协商以确定最佳设置。如果适配器无法通过自动协商与其链路伙伴建立连接，则可能需要手动将适配器及其链路伙伴配置为相同的设置来建立连接并传输数据包。这通常只在尝试与不支持自动协商或已被强制到特定速度或双工模式的旧式交换机建立连接时才需要。你的链路伙伴必须匹配你选择的设置。对于1Gbps及更高的速度，不能强制设置。使用自动协商广告设置手动设置1Gbps及更高带宽的设备。  
**注意**：你不能为基于Intel® 以太网网络适配器XXV710的设备设置速度。  
速度、双工以及自动协商广告是通过`ethtool`工具配置的。  
**警告**：只有经验丰富的网络管理员才能强制设置速度和双工或者手动更改自动协商广告。交换机上的设置必须始终与适配器设置相匹配。如果你的适配器配置与交换机不同，适配器性能可能会受到影响，甚至可能无法正常运行。  
然而，使用基于光纤连接的Intel® 以太网网络适配器不会尝试与其链路伙伴自动协商，因为这些适配器仅在全双工模式下运行，并且仅在其本机速度下工作。  
NAPI  
----  
NAPI（接收轮询模式）在i40e驱动程序中得到支持。  
更多信息请参阅 :ref:`Documentation/networking/napi.rst <napi>`  
流控制  
------------  
可以使用`ethtool`配置以太网流控（IEEE 802.3x），以启用i40e接收和发送暂停帧。当启用发送时，在接收数据包缓冲区跨越预定义阈值时生成暂停帧。当启用接收时，接收到暂停帧时，发送单元会在指定的时间延迟内停止工作。
注释：您必须拥有支持流控制的链路伙伴。
流控制默认是开启的。
使用 `ethtool` 来更改流控制设置。
要启用或禁用接收（Rx）或发送（Tx）流控制：

  `ethtool -A eth? rx <on|off> tx <on|off>`

注释：此命令仅在禁用了自动协商的情况下启用或禁用流控制。如果启用了自动协商，此命令会更改与链路伙伴进行自动协商时使用的参数。
要启用或禁用自动协商：

  `ethtool -s eth? autoneg <on|off>`

注释：流控制自动协商是链接自动协商的一部分。根据您的设备，您可能无法更改自动协商设置。
接收侧扩展（RSS）哈希流
-------------------------
允许您为每种流类型设置哈希字节，并为接收侧扩展（RSS）哈希字节配置设置一个或多个选项的任意组合。

  `# ethtool -N <dev> rx-flow-hash <type> <option>`

其中 `<type>` 是：
  `tcp4` 表示 TCP 过 IPv4
  `udp4` 表示 UDP 过 IPv4
  `tcp6` 表示 TCP 过 IPv6
  `udp6` 表示 UDP 过 IPv6
而 `<option>` 包括一个或多个以下选项：
  `s` 根据接收数据包的 IP 源地址进行哈希
  `d` 根据接收数据包的 IP 目标地址进行哈希
  `f` 根据接收数据包第 4 层头部的第 0 和第 1 字节进行哈希
  `n` 根据接收数据包第 4 层头部的第 2 和第 3 字节进行哈希
### MAC 和 VLAN 防伪造功能
当恶意驱动程序试图发送伪造的数据包时，硬件会丢弃该数据包，不进行传输。
**注释：**此功能可以为特定的虚拟功能（VF）禁用：

  ```
  ip link set <pf dev> vf <vf id> spoofchk {off|on}
  ```

### IEEE 1588 精确时间协议（PTP）硬件时钟（PHC）
精确时间协议（PTP）用于同步计算机网络中的时钟。支持此驱动程序的不同 Intel 设备对 PTP 的支持有所不同。使用 "ethtool -T <netdev name>" 获取设备支持的 PTP 功能的明确列表。

### IEEE 802.1ad（QinQ）支持
IEEE 802.1ad 标准，非正式地称为 QinQ，允许在一个以太网帧中包含多个 VLAN ID。VLAN ID 有时被称为“标签”，因此多个 VLAN ID 被称为“标签堆栈”。标签堆栈允许 L2 隧道化，并能够在一个特定的 VLAN ID 内隔离流量等用途。
以下是配置 802.1ad（QinQ）的一些示例：

  ```
  ip link add link eth0 eth0.24 type vlan proto 802.1ad id 24
  ip link add link eth0.24 eth0.24.371 type vlan proto 802.1Q id 371
  ```

其中，“24”和“371”是示例 VLAN ID。
**注释：**
对于 802.1ad（QinQ）数据包，不支持接收校验和卸载、云过滤器和 VLAN 加速。

### VXLAN 和 GENEVE Overlay 硬件卸载
虚拟可扩展局域网（VXLAN）允许您通过三层网络扩展二层网络，这在虚拟化或云计算环境中可能很有用。某些 Intel® 以太网网络设备执行 VXLAN 处理，将其从操作系统卸载。这减少了 CPU 使用率。
VXLAN 卸载由 ethtool 提供的 Tx 和 Rx 校验和卸载选项控制。也就是说，如果启用了 Tx 校验和卸载，并且适配器具有相应的能力，则也启用了 VXLAN 卸载。
VXLAN 和 GENEVE 硬件卸载的支持取决于内核对硬件卸载特性的支持。

### 每端口多个功能
基于 Intel 以太网控制器 X710/XL710 的某些适配器支持在单个物理端口上实现多个功能。通过系统设置/BIOS 配置这些功能。
最小 TX 带宽是分区将接收的保证最小数据传输带宽，以物理端口全链路速度的百分比表示。分配给分区的带宽永远不会低于您指定的水平。
最小带宽值的范围是：
1 到 ((100 减去 物理端口上的分区数) 加上 1)
例如，如果一个物理端口有 4 个分区，则范围为：
1 到 ((100 - 4) + 1 = 97)

最大带宽百分比表示分配给分区的最大传输带宽占物理端口全链接速度的百分比。可接受的数值范围是 1-100。这个值用作限制条件，如果您选择任何特定功能都不能消耗端口 100% 的带宽（如果有可用的话）。所有最大带宽值之和不受限制，因为一个端口的带宽使用不会超过 100%。

**注意：** X710/XXV710 设备在同时启用每个端口的多个功能 (MFP) 和 SR-IOV 时无法启用最大虚拟功能 (VF) 数量（64个）。从 i40e 记录的日志中会出现错误信息 "add vsi failed for VF N, aq_err 16"。要解决此问题，请启用少于 64 个虚拟功能 (VFs)。

**数据中心桥接 (DCB)**
----------------------
DCB 是一种硬件实现的配置服务质量机制。它使用 VLAN 优先级标签 (802.1p) 来过滤流量。这意味着有 8 种不同的优先级来过滤流量。它还启用了优先流控制 (802.1Qbb)，可以在网络压力下限制或消除丢包数量。可以为这些优先级分配带宽，该分配由硬件级别执行 (802.1Qaz)。
适配器固件按照 802.1AB 和 802.1Qaz 标准实现了 LLDP 和 DCBX 协议代理。基于固件的 DCBX 代理仅以愿意模式运行，并能接受来自支持 DCBX 的对等体设置。通过 dcbtool/lldptool 配置 DCBX 参数不被支持。

**注意：** 可以通过设置私有标志 `disable-fw-lldp` 来禁用固件 LLDP 功能。

i40e 驱动程序实现了 DCB netlink 接口层，允许用户空间与驱动程序通信并查询端口的 DCB 配置。

**注意：**
内核假设 TC0 可用，如果 TC0 不可用，则会在设备上禁用优先流控制 (PFC)。要解决这个问题，在交换机上设置 DCB 时请确保启用 TC0。

**中断率限制**
-----------------------
**有效范围：** 0-235 （0=无限制）

Intel(R) Ethernet Controller XL710 系列支持一种中断率限制机制。用户可以通过 ethtool 控制两次中断之间的微秒数。
命令语法如下：

  # ethtool -C ethX rx-usecs-high N

0-235 微秒的有效范围提供了每秒 4,310 到 250,000 次中断的有效范围。`rx-usecs-high` 的值可以独立于 `rx-usecs` 和 `tx-usecs` 在同一个 ethtool 命令中设置，也独立于自适应中断调节算法。底层硬件支持 4 微秒的粒度，因此相邻的值可能导致相同的中断率。

一个可能的应用示例是：

  # ethtool -C ethX adaptive-rx off adaptive-tx off rx-usecs-high 20 rx-usecs 5 tx-usecs 5

上述命令将禁用自适应中断调节，并允许在指示接收或发送完成之前最多等待 5 微秒。
然而，这并没有导致每秒多达200,000次的中断，而是通过`rx-usecs-high`参数将每秒的总中断次数限制在50,000次。

### 性能优化
====
驱动程序默认设置旨在适应各种工作负载，但如果需要进一步优化，我们建议尝试以下设置：

**注意：**为了在处理小（64字节）帧大小时获得更好的性能，请尝试在BIOS中启用超线程以增加系统中的逻辑核心数量，从而增加适配器可用队列的数量。

### 虚拟化环境
------------------------
1. 使用随附的`virt_perf_default`脚本或作为root用户运行以下命令来禁用两端的XPS：
   ```
   for file in `ls /sys/class/net/<ethX>/queues/tx-*/xps_cpus`;
   do echo 0 > $file; done
   ```

2. 使用适当机制（如vcpupin）在虚拟机中将CPU绑定到单独的本地CPU，并确保使用设备的`local_cpulist`中包含的一组CPU：`/sys/class/net/<ethX>/device/local_cpulist`

3. 在虚拟机中配置尽可能多的Rx/Tx队列。不要依赖默认设置1个队列。

### 非虚拟化环境
-------------------------
通过禁用irqbalance服务并使用随附的`set_irq_affinity`脚本来将适配器的IRQ绑定到特定的核心。请参阅脚本的帮助文本以了解更多信息。

- 下面的设置将在所有核心之间均匀分布IRQs：
  ```
  # scripts/set_irq_affinity -x all <interface1> , [ <interface2>, ... ]
  ```

- 下面的设置将在与适配器同属一个NUMA节点的所有核心之间分布IRQs：
  ```
  # scripts/set_irq_affinity -x local <interface1> ,[ <interface2>, ... ]
  ```

对于非常CPU密集型的工作负载，我们建议将IRQs绑定到所有核心。

对于IP转发：使用ethtool禁用自适应ITR并降低每个队列的Rx和Tx中断。
- 将`rx-usecs`和`tx-usecs`设置为125将限制每秒每队列的中断次数约为8000次：
  ```
  # ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 125 \
    tx-usecs 125
  ```

为了降低CPU利用率：使用ethtool禁用自适应ITR并降低每个队列的Rx和Tx中断。
将 rx-usecs 和 tx-usecs 设置为 250 可以将中断限制在每队列每秒大约 4000 次中断：

```shell
# ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 250 \
    tx-usecs 250
```

为了降低延迟：禁用自适应 ITR 和 ITR，通过 ethtool 将 Rx 和 Tx 设置为 0：
```shell
# ethtool -C <interface> adaptive-rx off adaptive-tx off rx-usecs 0 \
    tx-usecs 0
```

应用设备队列（ADq）
-------------------
应用设备队列（ADq）允许您为特定的应用程序分配一个或多个队列。这可以减少指定应用程序的延迟，并允许按应用程序限制发送流量的速率。请按照以下步骤设置 ADq：

1. 创建流量类别（TC）。每个接口最多可创建 8 个 TC。
   - `shaper bw_rlimit` 参数是可选的。
   - 示例：设置两个 TC，tc0 和 tc1，每个 TC 各有 16 个队列，并且 tc0 的最大发送速率为 1Gbps，tc1 的最大发送速率为 3Gbps：
     ```shell
     # tc qdisc add dev <interface> root mqprio num_tc 2 map 0 0 0 0 1 1 1 1 \
         queues 16@0 16@16 hw 1 mode channel shaper bw_rlimit min_rate 1Gbit 2Gbit \
         max_rate 1Gbit 3Gbit
     ```

   - `map`: 为最多 16 个优先级到 TC 的优先级映射（例如，`map 0 0 0 0 1 1 1 1` 表示优先级 0-3 使用 tc0，而优先级 4-7 使用 tc1）。

   - `queues`: 对于每个 TC，`<队列数>@<偏移量>`（例如，`queues 16@0 16@16` 为 tc0 分配了 16 个队列，起始偏移量为 0；为 tc1 分配了 16 个队列，起始偏移量为 16。所有 TC 的总队列数最大为 64 或者等于核心数，取较小值）。

   - `hw 1 mode channel`: “channel” 加上 `hw` 设置为 1 是 mqprio 中一个新的硬件卸载模式，该模式充分利用 mqprio 选项、TC、队列配置和 QoS 参数。

   - `shaper bw_rlimit`: 对于每个 TC，设置最小和最大带宽速率。所有 TC 的总带宽必须等于或小于端口速度。
     - 例如：`min_rate 1Gbit 3Gbit`：使用网络监控工具如 `ifstat` 或 `sar -n DEV [间隔] [样本数]` 来验证带宽限制。

2. 在接口上启用 HW TC 卸载：
    ```shell
    # ethtool -K <interface> hw-tc-offload on
    ```

3. 将 TC 应用于接口的入站（RX）流：
    ```shell
    # tc qdisc add dev <interface> ingress
    ```

**注意事项**：
- 所有的 tc 命令都应从 iproute2 `<iproute2路径>/tc/` 目录下运行。
- ADq与云过滤器不兼容。
- 当通过mqprio配置TC时，不支持使用ethtool（如ethtool -L）设置通道。
- 您必须使用iproute2的最新版本。
- 需要NVM版本6.01或更高版本。
- 启用ADq时，以下功能不能启用：数据中心桥接（DCB）、每个端口多个功能（MFP）或旁路过滤器。
- 如果其他驱动程序（例如DPDK）设置了云过滤器，则无法启用ADq。
- ADq不支持隧道过滤器。如果在非隧道模式下接收到了封装数据包，则会在内部报头进行过滤。例如，在非隧道模式下的VXLAN流量中，PCTYPE被识别为VXLAN封装的数据包，外部报头将被忽略，因此匹配的是内部报头。
- 如果PF上的TC过滤器匹配了经过VF（在PF上）的流量，该流量将被路由到PF的相应队列，并且不会传递给VF。此类流量最终将在TCP/IP栈的更高级别处被丢弃，因为它不匹配PF地址数据。
- 如果流量匹配了指向不同TC的多个TC过滤器，该流量将被复制并发送到所有匹配的TC队列。当有多个过滤器匹配时，硬件交换机将数据包镜像到VSI列表中。
已知问题/故障排除
============================

**注：** 基于 Intel(R) Ethernet Network Connection X722 的 1Gb 设备不支持以下功能：

  * 数据中心桥接 (DCB)
  * 服务质量 (QoS)
  * 虚拟机队列 (VMQ)
  * 单根 I/O 虚拟化 (SR-IOV)
  * 任务封装卸载 (VXLAN, NVGRE)
  * 能效以太网 (EEE)
  * 自动介质检测

当设备驱动程序和 DPDK 共享一个设备时的意外问题
----------------------------------------------------------------
当 i40e 设备处于多驱动模式且内核驱动程序与 DPDK 驱动程序共享该设备时，可能会出现意外问题。这是因为多个驱动程序之间对全局 NIC 资源的访问未同步。对全局 NIC 配置（写入全局寄存器、通过 AQ 设置全局配置或更改交换模式）所做的任何更改都将影响设备上的所有端口和驱动程序。加载 DPDK 时使用 "multi-driver" 模块参数可以缓解部分问题。

在交换机上设置 DCB 时必须启用 TC0
---------------------------------------------------
内核假设 TC0 可用，并会在 TC0 不可用时禁用优先流控制 (PFC)。为解决此问题，请确保在交换机上设置 DCB 时启用 TC0。

支持
=======
有关一般信息，请访问 Intel 支持网站：
https://www.intel.com/support/

如果在受支持的内核上使用受支持的适配器识别出已发布的源代码中的问题，请将与问题相关的确切信息发送至 intel-wired-lan@lists.osuosl.org。
