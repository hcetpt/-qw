SPDX 许可证标识符: GPL-2.0+ 

=================================================================
Linux 基础驱动程序适用于 Intel(R) 以太网控制器 800 系列
=================================================================

Intel ice Linux 驱动程序
版权所有 (c) 2018-2021 Intel Corporation
内容
========

- 概述
- 识别您的适配器
- 重要说明
- 额外功能与配置
- 性能优化

此驱动程序相关的虚拟函数 (VF) 驱动程序为 iavf
可以通过 ethtool 和 lspci 获取驱动程序信息
关于硬件需求的问题，请参阅随附的 Intel 适配器文档。所有列出的硬件需求均适用于 Linux
此驱动程序支持 XDP（Express Data Path）和 AF_XDP 零拷贝。请注意，对于大于 3KB 的帧大小，XDP 将被阻止。

识别您的适配器
========================
有关如何识别您的适配器的信息以及最新的 Intel 网络驱动程序，请访问 Intel 支持网站：
https://www.intel.com/support

重要说明
===============

在接收压力下可能会发生丢包
-------------------------------------------
基于 Intel(R) 以太网控制器 800 系列的设备设计用于容忍 PCIe 和 DMA 事务期间有限的系统延迟
如果这些事务的时间超过容忍的延迟，可能会影响数据包在设备及其关联内存中缓冲的时间，从而导致丢包。这些丢包通常不会在标准工作负载下对吞吐量和性能产生明显影响
如果这些丢包似乎影响了您的工作负载，以下方法可能会改善情况：

1) 确保您的系统的物理内存处于高性能配置，如平台供应商推荐的那样。常见建议是在所有通道上使用单个 DIMM 模块
2) 在系统的 BIOS/UEFI 设置中选择“性能”配置文件
3) 您的发行版可能提供像“tuned”这样的工具，这些工具可以帮助调整内核设置以实现不同工作负载下的更佳标准设置。

配置 SR-IOV 以提高网络安全性
--------------------------------
在虚拟化环境中，对于支持 SR-IOV 的 Intel(R) 以太网适配器，在虚拟功能（VF）上可能会受到恶意行为的影响。软件生成的二层帧，如 IEEE 802.3x（链路流控制）、IEEE 802.1Qbb（基于优先级的流控制）等，是不期望出现的，并且可能会限制主机与虚拟交换机之间的流量，从而降低性能。为了解决这个问题，并确保隔离未预期的流量流，请从 PF 的管理接口配置所有启用 SR-IOV 的端口进行 VLAN 标记。这种配置允许丢弃意外的、潜在恶意的帧。

请参阅本 README 后面的“在启用 SR-IOV 的适配器端口上配置 VLAN 标记”部分以获取配置说明。

不要在有活动虚拟机（VM）绑定到虚拟功能（VF）的情况下卸载端口驱动程序
-------------------------------------------------------------
如果一个虚拟功能（VF）绑定了一个活动的虚拟机（VM），则不要卸载该端口的驱动程序。这样做会导致端口似乎挂起。一旦虚拟机关闭或释放 VF，命令将完成。

附加功能和配置
======================

ethtool
-------
驱动程序使用 ethtool 接口进行配置和诊断，以及显示统计信息。此功能需要最新版本的 ethtool。您可以在这里下载：https://kernel.org/pub/software/network/ethtool/

注意：由于设备会剥离 4 字节的 CRC，因此 ethtool 的 rx_bytes 值与 Netdev 的 rx_bytes 值不匹配。两个 rx_bytes 值之间的差异将是接收包数量乘以 4 字节 CRC 的结果。例如，如果接收到 10 个包，而 Netdev（软件统计）显示的 rx_bytes 值为“X”，那么 ethtool（硬件统计）显示的 rx_bytes 值将是“X + 40”（4 字节 CRC × 10 个包）。

查看链路消息
---------------------
如果发行版限制了系统消息，则不会在控制台上显示链路消息。为了在控制台上看到网络驱动程序的链路消息，请将 dmesg 设置为 8，方法如下：

  # dmesg -n 8

注意：此设置不会在重新启动后保存。

动态设备个性化
----------------------
动态设备个性化（DDP）允许您通过在运行时应用配置文件包来改变设备的数据包处理管道。配置文件可以用于添加对新协议的支持、更改现有协议或更改默认设置。DDP 配置文件还可以在不重启系统的情况下回滚。
DDP 包在设备初始化期间加载。驱动程序会在固件根目录（通常为 `/lib/firmware/` 或 `/lib/firmware/updates/`）中查找 `intel/ice/ddp/ice.pkg`，并检查它是否包含一个有效的 DDP 包文件。

**注意：** 您的发行版应该已经提供了最新的 DDP 文件，但如果缺少 `ice.pkg` 文件，您可以在 `linux-firmware` 仓库或 intel.com 上找到它。

如果驱动程序无法加载 DDP 包，设备将进入安全模式。安全模式禁用高级和性能功能，仅支持基本流量和最小功能，例如更新 NVM 或下载新的驱动程序或 DDP 包。安全模式仅适用于受影响的物理功能（PF），不会影响其他 PF。有关 DDP 和安全模式的更多详细信息，请参阅“Intel(R) 以太网适配器和设备用户指南”。

**注意事项：**

- 如果遇到 DDP 包文件的问题，可能需要下载更新的驱动程序或 DDP 包文件。请查看日志消息以获取更多信息。
- `ice.pkg` 文件是默认 DDP 包文件的符号链接。
- 如果任何 PF 驱动程序已加载，则无法更新 DDP 包。要覆盖包，请卸载所有 PF，然后使用新包重新加载驱动程序。
- 只有每个设备的第一个加载的 PF 才能为该设备下载包。

您可以在同一系统中的不同物理设备上安装特定的 DDP 包文件。要安装特定的 DDP 包文件：

1. 下载您设备所需的 DDP 包文件。
2. 将文件重命名为 `ice-xxxxxxxxxxxxxxxx.pkg`，其中 `'xxxxxxxxxxxxxxxx'` 是您希望下载包的设备的唯一 64 位 PCI Express 设备序列号（十六进制表示）。文件名必须包含完整的序列号（包括前导零），并且全部为小写。例如，如果 64 位序列号为 `b887a3ffffca0568`，则文件名为 `ice-b887a3ffffca0568.pkg`。

要从 PCI 总线地址找到序列号，可以使用以下命令：
```
# lspci -vv -s af:00.0 | grep -i Serial
Capabilities: [150 v1] Device Serial Number b8-87-a3-ff-ff-ca-05-68
```

您可以使用以下命令格式化序列号，去除破折号：
```
# lspci -vv -s af:00.0 | grep -i Serial | awk '{print $7}' | sed s/-//g
b887a3ffffca0568
```

3. 将重命名的 DDP 包文件复制到 `/lib/firmware/updates/intel/ice/ddp/`。如果目录尚不存在，请在复制文件之前创建该目录。
4. 卸载设备上的所有 PF（物理功能）
5. 使用新的软件包重新加载驱动程序
注意：特定设备的 DDP 软件包文件会覆盖默认的 DDP 软件包文件（ice.pkg）

Intel® 以太网流导向器
-------------------------
Intel 以太网流导向器执行以下任务：

- 根据数据流将接收的数据包定向到不同的队列
- 允许对平台中的流路由进行严格控制
- 匹配流和 CPU 核心，实现流亲和性

注意：此驱动程序支持以下流类型：

- IPv4
- TCPv4
- UDPv4
- SCTPv4
- IPv6
- TCPv6
- UDPv6
- SCTPv6

每种流类型都支持有效的 IP 地址组合（源或目标）以及 UDP/TCP/SCTP 端口（源和目标）。您可以仅提供源 IP 地址、源 IP 地址和目标端口，或这四个参数的任意组合。

注意：此驱动程序允许您使用 ethtool 的用户定义字段和掩码来过滤流量。仅支持 L3 和 L4 流类型的用户定义灵活过滤器。对于给定的流类型，在更改输入集之前，必须清除所有 Intel 以太网流导向器过滤器。
流导向器过滤器
-----------------
流导向器过滤器用于引导符合指定特征的流量。它们通过 ethtool 的 ntuple 接口启用。要启用或禁用 Intel 以太网流导向器及其过滤器，请执行以下命令：

```
# ethtool -K <ethX> ntuple <off|on>
```

注意：当您禁用 ntuple 过滤器时，所有用户编程的过滤器都会从驱动程序缓存和硬件中清除。重新启用 ntuple 时，必须重新添加所有所需的过滤器。
显示所有活动过滤器：

```
# ethtool -u <ethX>
```

添加新过滤器：

```
# ethtool -U <ethX> flow-type <type> src-ip <ip> [m <ip_mask>] dst-ip <ip>
[m <ip_mask>] src-port <port> [m <port_mask>] dst-port <port> [m <port_mask>]
action <queue>
```

其中：
- `<ethX>` 是要编程的以太网设备
- `<type>` 可以是 ip4、tcp4、udp4、sctp4、ip6、tcp6、udp6、sctp6
- `<ip>` 是要匹配的 IP 地址
- `<ip_mask>` 是用于掩码的 IPv4 地址
注意：这些过滤器使用反向掩码
- `<port>` 是要匹配的端口号
- `<port_mask>` 是用于掩码的 16 位整数
注意：这些过滤器使用反向掩码
- `<queue>` 是要引导流量的方向（-1 丢弃匹配的流量）

删除过滤器：

```
# ethtool -U <ethX> delete <N>
```

其中 `<N>` 是打印所有活动过滤器时显示的过滤器 ID，也可以在添加过滤器时使用 "loc <N>" 指定。
示例：

添加一个将数据包导向队列 2 的过滤器：

```
# ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
192.168.10.2 src-port 2000 dst-port 2001 action 2 [loc 1]
```

仅使用源 IP 地址和目标 IP 地址设置过滤器：

```
# ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
192.168.10.2 action 2 [loc 1]
```

根据用户定义的模式和偏移量设置过滤器：

```
# ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
192.168.10.2 user-def 0x4FFFF action 2 [loc 1]
```

其中 `user-def` 字段的值包含偏移量（4 字节）和模式（0xffff）。
为了匹配从192.168.0.1的端口5300发送到192.168.0.5的端口80的TCP流量，并将其发送到队列7：

```sh
# ethtool -U enp130s0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.0.5 src-port 5300 dst-port 80 action 7
```

为了添加一个具有部分掩码的源IP子网的TCPv4过滤器：

```sh
# ethtool -U <ethX> flow-type tcp4 src-ip 192.168.0.0 m 0.255.255.255 dst-ip 192.168.5.12 src-port 12600 dst-port 31 action 12
```

注意事项：

对于每种流类型，编程的过滤器必须具有相同的匹配输入集。例如，以下两个命令是可以接受的：

```sh
# ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
# ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.5 src-port 55 action 10
```

但是，下面两个命令是不可接受的，因为第一个指定了源IP地址，而第二个指定了目标IP地址：

```sh
# ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
# ethtool -U enp130s0 flow-type ip4 dst-ip 192.168.0.5 src-port 55 action 10
```

第二个命令将会报错。你可以使用相同的字段编程多个过滤器，但使用不同的值。然而，在一个设备上，你不能为两种不同的匹配字段编程两个TCPv4过滤器。ice驱动不支持对字段的部分匹配，因此不支持部分掩码字段。

灵活字节流过滤器
----------------
驱动程序还支持匹配用户定义的数据包负载中的数据。这种灵活数据可以通过ethtool命令中的"user-def"字段来指定，如下所示：

```
============================ ============================
31    28    24    20    16   15    12    8    4    0
进入数据包负载的偏移量      2字节的灵活数据
============================ ============================
```

例如，

```
... user-def 0x4FFFF ..
```

告诉过滤器在负载中查找4个字节，并将该值与0xFFFF进行匹配。偏移量基于负载的开始位置，而不是整个数据包的开始位置。因此，

```
flow-type tcp4 ... user-def 0x8BEAF ..
```

将匹配TCP/IPv4数据包，这些数据包在TCP/IPv4负载中的第8个字节处的值为0xBEAF。

请注意，ICMP头部被视为4字节的头部和4字节的负载。因此，要匹配负载的第一个字节，实际上需要将偏移量加上4字节。此外，请注意ip4过滤器会匹配ICMP帧以及raw（未知）的ip4帧，其中负载将是IP4帧的L3负载。

最大偏移量为64。硬件只会从负载中读取最多64字节的数据。偏移量必须是偶数，因为灵活数据长度为2字节，并且必须与数据包负载的字节0对齐。

用户定义的灵活偏移量也被视为输入集的一部分，不能为同一类型的多个过滤器单独编程。但是，灵活数据不是输入集的一部分，多个过滤器可以使用相同的偏移量，但匹配不同的数据。
RSS Hash Flow
-------------
允许您为每种流类型设置哈希字节数，并且可以组合一个或多个选项来配置接收端扩展（RSS）哈希字节。

```
# ethtool -N <ethX> rx-flow-hash <type> <option>
```

其中 `<type>` 是：
- tcp4 表示 TCP over IPv4
- udp4 表示 UDP over IPv4
- gtpc4 表示 GTP-C over IPv4
- gtpc4t 表示 GTP-C (包含 TEID) over IPv4
- gtpu4 表示 GTP-U over IPv4
- gtpu4e 表示 GTP-U 和扩展头 over IPv4
- gtpu4u 表示 GTP-U PSC 上行 over IPv4
- gtpu4d 表示 GTP-U PSC 下行 over IPv4
- tcp6 表示 TCP over IPv6
- udp6 表示 UDP over IPv6
- gtpc6 表示 GTP-C over IPv6
- gtpc6t 表示 GTP-C (包含 TEID) over IPv6
- gtpu6 表示 GTP-U over IPv6
- gtpu6e 表示 GTP-U 和扩展头 over IPv6
- gtpu6u 表示 GTP-U PSC 上行 over IPv6
- gtpu6d 表示 GTP-U PSC 下行 over IPv6

并且 `<option>` 可以是一个或多个：
- s 在接收到的数据包的 IP 源地址上进行哈希
- d 在接收到的数据包的 IP 目标地址上进行哈希
- f 在接收到的数据包的第 4 层头部的第 0 和第 1 字节上进行哈希
- n 在接收到的数据包的第 4 层头部的第 2 和第 3 字节上进行哈希
- e 在接收到的数据包的 GTP 包的 TEID (4 字节) 上进行哈希

加速接收流调度 (aRFS)
----------------------
基于 Intel(R) Ethernet Controller 800 系列的设备支持在 PF 上实现加速接收流调度 (aRFS)。aRFS 是一种负载均衡机制，允许将数据包定向到运行或消耗该流中数据包的应用程序所在的同一 CPU。

注意事项：

- aRFS 需要通过 ethtool 启用 ntuple 过滤
- aRFS 仅支持以下数据包类型：
  - TCP over IPv4 和 IPv6
  - UDP over IPv4 和 IPv6
  - 非分片数据包
- aRFS 仅支持 Flow Director 过滤器，这些过滤器包括源/目标 IP 地址和源/目标端口
- aRFS 和 ethtool 的 ntuple 接口都使用设备的 Flow Director。aRFS 和 ntuple 功能可以共存，但如果 aRFS 和 ntuple 请求之间存在冲突，可能会导致意外结果。请参阅“Intel(R) Ethernet Flow Director”获取更多信息。
设置 aRFS：

1. 使用 ethtool 启用 Intel Ethernet Flow Director 和 ntuple 过滤器：
   ```
   # ethtool -K <ethX> ntuple on
   ```

2. 设置全局流表中的条目数量。例如：
   ```
   # NUM_RPS_ENTRIES=16384
   # echo $NUM_RPS_ENTRIES > /proc/sys/net/core/rps_sock_flow_entries
   ```

3. 设置每个队列流表中的条目数量。例如：
   ```
   # NUM_RX_QUEUES=64
   # for file in /sys/class/net/$IFACE/queues/rx-*/rps_flow_cnt; do
   # echo $(($NUM_RPS_ENTRIES/$NUM_RX_QUEUES)) > $file;
   # done
   ```

4. 禁用 IRQ 平衡守护进程（这仅在下次重启前暂时停止服务）
   ```
   # systemctl stop irqbalance
   ```

5. 配置中断亲和性
   查看 `/Documentation/core-api/irq/irq-affinity.rst`

使用 ethtool 禁用 aRFS：
```
# ethtool -K <ethX> ntuple off
```

**注意：** 此命令将禁用 ntuple 过滤器，并清除软件和硬件中的任何 aRFS 过滤器。

示例用例：

1. 将服务器应用程序设置在指定的 CPU 上（例如，CPU 4）
   ```
   # taskset -c 4 netserver
   ```

2. 使用 netperf 将流量从客户端路由到配置了 aRFS 的服务器上的 CPU 4。此示例使用 IPv4 上的 TCP
   ```
   # netperf -H <Host IPv4 Address> -t TCP_STREAM
   ```

启用虚拟功能（VFs）：
---------------------
使用 sysfs 启用虚拟功能（VF）。例如，可以创建 4 个 VF 如下所示：
```
# echo 4 > /sys/class/net/<ethX>/device/sriov_numvfs
```

要禁用 VFs，请向同一文件写入 0：
```
# echo 0 > /sys/class/net/<ethX>/device/sriov_numvfs
```

ice 驱动程序支持的最大 VF 数量为 256 个（所有端口）。要检查每个 PF 支持多少个 VF，请使用以下命令：
```
# cat /sys/class/net/<ethX>/device/sriov_totalvfs
```

**注意：** 当链路聚合（LAG）/绑定处于活动状态时，不能使用 SR-IOV，反之亦然。为了强制这一点，驱动程序会检查这种互斥性。

显示 PF 上的 VF 统计信息：
-----------------------------
使用以下命令显示 PF 及其 VFs 的统计信息：
```
# ip -s link show dev <ethX>
```

**注意：** 由于可能的 VF 数量最大，此命令的输出可能会非常大。
PF 驱动程序将显示 PF 和所有已配置 VF 的部分统计信息。PF 总是会为每个可能的 VF 打印一个统计块，并且对于所有未配置的 VF 显示零值。
在SR-IOV启用的适配器端口上配置VLAN标记  
--------------------------------------------------------

要为SR-IOV启用适配器上的端口配置VLAN标记，请使用以下命令。VLAN配置应在VF驱动加载或虚拟机启动之前完成。VF不会意识到发送时插入并在接收帧时移除的VLAN标签（有时称为“端口VLAN”模式）：

```shell
# ip link set dev <ethX> vf <id> vlan <vlan id>
```

例如，以下命令将配置PF eth0及其第一个VF以VLAN 10：

```shell
# ip link set dev eth0 vf 0 vlan 10
```

如果端口断开连接时启用VF链接
----------------------------------------------

如果物理功能（PF）链接已断开，您可以强制任何绑定到PF的虚拟功能（VF）链接（从主机PF）处于活动状态。例如，要强制绑定到PF eth0的VF 0链接处于活动状态：

```shell
# ip link set eth0 vf 0 state enable
```

注意：如果该命令不起作用，可能是因为您的系统不支持此操作。

设置VF的MAC地址
-------------------------------

要更改指定VF的MAC地址：

```shell
# ip link set <ethX> vf 0 mac <address>
```

例如：

```shell
# ip link set <ethX> vf 0 mac 00:01:02:03:04:05
```

此设置将持续到PF重新加载为止。

注意：从主机分配一个MAC地址给VF将会禁用后续在VM内部请求更改MAC地址的操作。这是出于安全考虑。VM不会意识到这一限制，因此如果在VM中尝试更改MAC地址，将会触发MDD事件。

可信VF和VF混杂模式
-------------------------------

此功能允许您将特定的VF指定为可信，并允许该可信VF请求在物理功能（PF）上启用选择性混杂模式。要在Hypervisor中将VF设置为可信或非可信，请输入以下命令：

```shell
# ip link set dev <ethX> vf 1 trust [on|off]
```

注意：在设置混杂模式之前必须先将VF设置为可信。如果VM不可信，则PF会忽略来自VF的混杂模式请求。如果在VF驱动加载后VM变为可信，则必须重新请求将VF设置为混杂模式。

一旦VF被指定为可信，可以在VM中使用以下命令将VF设置为混杂模式：

对于全混杂模式：

```shell
# ip link set <ethX> promisc on
```

其中 `<ethX>` 是VM中的VF接口。

对于多播混杂模式：

```shell
# ip link set <ethX> allmulticast on
```

其中 `<ethX>` 是VM中的VF接口。

注意：默认情况下，ethtool私有标志 `vf-true-promisc-support` 设置为 “off”，这意味着VF的混杂模式是有限制的。要将VF的混杂模式设置为真正的混杂模式并允许VF查看所有入站流量，请使用以下命令：

```shell
# ethtool --set-priv-flags <ethX> vf-true-promisc-support on
```

`vf-true-promisc-support` 私有标志并不会启用混杂模式；相反，它指定了当您使用上面的ip link命令启用混杂模式时，您将获得哪种类型的混杂模式（有限或真正）。请注意，这是一个影响整个设备的全局设置。然而，`vf-true-promisc-support` 私有标志仅对设备的第一个PF可见。无论 `vf-true-promisc-support` 的设置如何，PF都将保持在有限混杂模式。
接下来，在VF接口上添加一个VLAN接口。例如：

  # ip link add link eth2 name eth2.100 type vlan id 100

请注意，将VF设置为混杂模式和添加VLAN接口的顺序无关紧要（您可以先做任何一项）。在这个示例中，结果是VF将接收到所有带有VLAN 100标签的流量。

恶意驱动检测（MDD）功能
-----------------------------
一些Intel以太网设备使用恶意驱动检测（MDD）来检测来自VF的恶意流量，并在检测到恶意流量时禁用Tx/Rx队列或丢弃违规数据包，直到VF驱动程序重置。您可以通过dmesg命令查看PF系统日志中的MDD消息。
- 如果PF驱动记录了来自VF的MDD事件，请确认安装了正确的VF驱动程序。
- 要恢复功能，您可以手动重新加载VF或VM，或者启用自动VF重置。
- 当启用了自动VF重置时，PF驱动将在检测到接收路径上的MDD事件时立即重置VF并重新启用队列。
- 如果禁用了自动VF重置，则PF不会在检测到MDD事件时自动重置VF。

要启用或禁用自动VF重置，请使用以下命令：

  # ethtool --set-priv-flags <ethX> mdd-auto-reset-vf on|off

VF的MAC和VLAN防欺骗功能
-------------------------------------
当虚拟功能（VF）接口上的恶意驱动尝试发送欺骗数据包时，硬件会丢弃该数据包而不进行传输。
注意：此功能可以针对特定VF禁用：

  # ip link set <ethX> vf <vf id> spoofchk {off|on}

巨型帧支持
--------------
通过将最大传输单元（MTU）更改为大于默认值1500的值来启用巨型帧支持。
使用ifconfig命令增加MTU大小。例如，输入以下内容，其中<ethX>是接口编号：

  # ifconfig <ethX> mtu 9000 up

或者，您可以使用ip命令如下：

  # ip link set mtu 9000 dev <ethX>
  # ip link set up dev <ethX>

此设置不会跨重启保存。
注意：巨型帧的最大MTU设置为9702。这对应于9728字节的最大巨型帧大小。
**注释：** 此驱动程序将尝试使用多个页面大小的缓冲区来接收每个巨型帧。这有助于在分配接收数据包时避免缓冲区饥饿问题。

**注释：** 使用巨型帧时，丢包可能会对吞吐量产生更大的影响。如果您在启用巨型帧后发现性能下降，启用流量控制可能会缓解这个问题。

### 速度和双工配置
-------------------

在解决速度和双工配置问题时，您需要区分基于铜缆的适配器和基于光纤的适配器。

默认模式下，使用铜缆连接的英特尔® 以太网网络适配器将尝试与其链路伙伴自动协商以确定最佳设置。如果适配器无法通过自动协商与链路伙伴建立链接，则可能需要手动配置适配器和链路伙伴以相同的设置来建立链接并传输数据包。这通常仅在尝试与不支持自动协商或已被强制为特定速度或双工模式的旧交换机建立链接时需要。您的链路伙伴必须匹配您选择的设置。1Gbps及以上的速度不能被强制。使用自动协商广告设置手动设置1Gbps及以上设备。

速度、双工和自动协商广告是通过`ethtool`工具进行配置的。最新版本可以从以下网站下载和安装：

```
https://kernel.org/pub/software/network/ethtool/
```

要查看您的设备支持的速度配置，请运行以下命令：

```
# ethtool <ethX>
```

**警告：** 只有经验丰富的网络管理员应手动强制速度和双工或更改自动协商广告设置。交换机上的设置必须始终与适配器设置相匹配。如果适配器配置与交换机不同，适配器性能可能会受到影响，或者适配器可能无法正常工作。

### 数据中心桥接（DCB）
-----------------------

**注释：** 内核假定TC0可用，并且如果TC0不可用则会禁用优先级流控（PFC）。为了解决这个问题，在设置交换机上的DCB时，请确保TC0已启用。

DCB 是硬件中实现的一种配置服务质量的方法。它使用VLAN优先级标签（802.1p）来过滤流量。这意味着可以将流量过滤到8个不同的优先级。它还启用了优先级流控（802.1Qbb），可以在网络压力期间限制或消除丢包数量。带宽可以分配给这些优先级中的每一个，这是在硬件级别（802.1Qaz）上执行的。

DCB 通常使用DCBX协议（802.1Qaz）在网络中进行配置，该协议是LLDP（802.1AB）的一个特例。`ice`驱动程序支持以下互斥的DCBX支持变体：

1. 基于固件的LLDP代理
2. 基于软件的LLDP代理

在基于固件的模式下，固件拦截所有LLDP流量并透明地处理DCBX协商。在这种模式下，适配器处于“愿意”DCBX模式，从链路伙伴（通常是交换机）接收DCB设置。本地用户只能查询协商后的DCB配置。有关在交换机上配置DCBX参数的信息，请参阅交换机制造商的文档。

在基于软件的模式下，LLDP流量被转发到网络堆栈和用户空间，其中软件代理可以处理它。在这种模式下，适配器可以处于“愿意”或“不愿意”的DCBX模式，并且DCB配置可以本地查询和设置。此模式要求禁用基于固件的LLDP代理。

**注释：**

- 您可以使用`ethtool`私有标志启用和禁用基于固件的LLDP代理。更多信息请参考本README中的“FW-LLDP（基于固件的链路层发现协议）”部分。
在基于软件的 DCBX 模式中，您可以使用与 Linux 内核 DCB Netlink API 交互的软件 LLDP/DCBX 代理来配置 DCB 参数。我们建议在运行软件模式时使用 OpenLLDP 作为 DCBX 代理。更多信息，请参阅 OpenLLDP 的手册页和 https://github.com/intel/openlldp。

- 驱动程序实现了 DCB Netlink 接口层，以便用户空间可以与驱动程序通信并查询端口的 DCB 配置。
- 不支持带有 DCB 的 iSCSI。

### 固件链路层发现协议（FW-LLDP）
-----------------------------------

使用 ethtool 更改 FW-LLDP 设置。FW-LLDP 设置是按端口进行的，并且在重启后仍然保留。

要启用 LLDP：

```sh
# ethtool --set-priv-flags <ethX> fw-lldp-agent on
```

要禁用 LLDP：

```sh
# ethtool --set-priv-flags <ethX> fw-lldp-agent off
```

要检查当前的 LLDP 设置：

```sh
# ethtool --show-priv-flags <ethX>
```

**注意**：您必须启用 UEFI HII 的“LLDP Agent”属性才能使此设置生效。如果“LLDP AGENT”被设置为禁用，则无法从操作系统中启用它。

### 流量控制
-------------

可以通过 ethtool 配置以太网流量控制（IEEE 802.3x），以启用接收和发送暂停帧。当启用发送时，在接收数据包缓冲区超过预定义阈值时会生成暂停帧。当启用接收时，接收到暂停帧时，发送单元将停止指定的时间延迟。

**注意**：您必须有一个支持流量控制的链路伙伴。默认情况下，流量控制是禁用的。使用 ethtool 更改流量控制设置。

要启用或禁用 Rx 或 Tx 流量控制：

```sh
# ethtool -A <ethX> rx <on|off> tx <on|off>
```

**注意**：此命令仅在禁用自动协商时启用或禁用流量控制。如果启用了自动协商，此命令将更改与链路伙伴自动协商使用的参数。
注释：流控制自动协商是链路自动协商的一部分。根据您的设备，您可能无法更改自动协商设置。

注释：

- ice 驱动程序要求端口和链路对端都启用流控制。如果任一侧禁用了流控制，在高流量情况下端口可能会出现挂起现象。
- 在禁用 DCB 后，您可能会遇到链路级别流控制（LFC）的问题。LFC 状态可能显示为已启用，但实际上流量并未暂停。要解决此问题，请使用 ethtool 禁用并重新启用 LFC：

  ```
  # ethtool -A <ethX> rx off tx off
  # ethtool -A <ethX> rx on tx on
  ```

NAPI
----

该驱动程序支持 NAPI（接收轮询模式）。更多信息请参阅 :ref:`Documentation/networking/napi.rst <napi>`。

MACVLAN
-------

该驱动程序支持 MACVLAN。可以通过检查 MACVLAN 驱动程序是否加载来测试内核对 MACVLAN 的支持。您可以运行 `lsmod | grep macvlan` 查看 MACVLAN 驱动程序是否已加载，或者运行 `modprobe macvlan` 尝试加载 MACVLAN 驱动程序。

注释：

- 在 passthru 模式下，您只能设置一个 MACVLAN 设备。它将继承底层 PF（物理功能）设备的 MAC 地址。

IEEE 802.1ad (QinQ) 支持
---------------------------

IEEE 802.1ad 标准，非正式地称为 QinQ，允许在一个以太网帧中包含多个 VLAN ID。VLAN ID 有时被称为“标签”，因此多个 VLAN ID 被称为“标签堆栈”。标签堆栈允许 L2 隧道化，并能够在一个特定的 VLAN ID 内隔离流量等用途。

注释：

- 不支持 802.1ad (QinQ) 数据包的接收校验和卸载和 VLAN 加速。
- 除非使用以下命令禁用 VLAN 剥离，否则不会接收到 0x88A8 流量：

  ```
  # ethtool -K <ethX> rxvlan off
  ```

- 0x88A8/0x8100 双重 VLAN 不能与同一端口上配置的 0x8100 或 0x8100/0x8100 VLAN 一起使用。如果配置了 0x8100 VLAN，则不会接收到 0x88A8/0x8100 流量。
- VF 只有在满足以下条件时才能传输 0x88A8/0x8100（即 802.1ad/802.1Q）流量：

  1) VF 未分配端口 VLAN。
2) `spoofchk` 已从 PF 禁用。如果您启用 `spoofchk`，VF 将不会传输 0x88A8/0x8100 流量。
- 在 SR-IOV 模式下，当 VF 真正的混杂模式 (`vf-true-promisc-support`) 和双 VLAN 启用时，VF 可能无法接收基于内部 VLAN 标头的所有网络流量。

以下是配置 802.1ad (QinQ) 的示例：

  ```
  # ip link add link eth0 eth0.24 type vlan proto 802.1ad id 24
  # ip link add link eth0.24 eth0.24.371 type vlan proto 802.1Q id 371
  ```

  其中 "24" 和 "371" 是示例 VLAN ID。

无状态卸载（Tunnel/Overlay）
-----------------------------
支持的隧道和覆盖包括 VXLAN、GENEVE 等，具体取决于硬件和软件配置。无状态卸载默认是启用的。
要查看所有卸载的当前状态，请执行以下命令：

  ```
  # ethtool -k <ethX>
  ```

UDP 分段卸载
------------------------
允许适配器将带有最大 64K 负载的 UDP 数据包分段卸载为有效的以太网帧。由于适配器硬件能够比操作系统软件更快地完成数据分段，此功能可能提高传输性能。
此外，适配器可能会使用更少的 CPU 资源。
注意：
- 发送 UDP 数据包的应用程序必须支持 UDP 分段卸载。
要启用或禁用 UDP 分段卸载，请执行以下命令：

  ```
  # ethtool -K <ethX> tx-udp-segmentation [off|on]
  ```

GNSS 模块
-----------
需要编译内核时包含 `CONFIG_GNSS=y` 或 `CONFIG_GNSS=m`。
允许用户读取来自 GNSS 硬件模块的消息并写入支持的命令。如果该模块物理上存在，则会生成一个 GNSS 设备：`/dev/gnss<id>`。
写入命令的协议依赖于 GNSS 硬件模块，因为驱动程序通过 i2c 以原始字节的形式将 GNSS 对象写入接收器。请参阅硬件 GNSS 模块文档获取详细配置信息。
固件（FW）日志记录
---------------------
驱动程序仅通过PF 0上的debugfs接口支持固件日志记录。运行在NIC上的固件必须支持固件日志记录；如果固件不支持固件日志记录，'fwlog'文件将不会在ice debugfs目录中创建。

模块配置
~~~~~~~~~~~~~~~~~~~~
固件日志记录按模块进行配置。每个模块可以独立于其他模块设置值（除非指定了模块'all'）。这些模块将在'fwlog/modules'目录下实例化。用户可以通过写入模块文件来设置模块的日志级别，如下所示：

  # echo <log_level> > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/<module>

其中：
* log_level是一个名称，如下面所述。每个级别包含前一个/更低级别的消息
    * none
    * error
    * warning
    * normal
    * verbose
* module是一个代表接收事件的模块的名称。模块名称包括：
    * general
    * ctrl
    * link
    * link_topo
    * dnl
    * i2c
    * sdp
    * mdio
    * adminq
    * hdma
    * lldp
    * dcbx
    * dcb
    * xlr
    * nvm
    * auth
    * vpd
    * iosf
    * parser
    * sw
    * scheduler
    * txq
    * rsvd
    * post
    * watchdog
    * task_dispatch
    * mng
    * synce
    * health
    * tsdrv
    * pfreg
    * mdlver
    * all

名称'all'是特殊的，允许用户将所有模块设置为指定的日志级别或读取所有模块的日志级别。

示例用法以配置模块
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
要将单个模块设置为'verbose'：
  
  # echo verbose > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/link
  
要设置多个模块，则多次发出命令：
  
  # echo verbose > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/link
  # echo warning > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/ctrl
  # echo none > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/dcb
  
要将所有模块设置为相同的值：
  
  # echo normal > /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/all
  
要读取特定模块（例如模块'general'）的日志级别：
  
  # cat /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/general
  
要读取所有模块的日志级别：
  
  # cat /sys/kernel/debug/ice/0000:18:00.0/fwlog/modules/all

启用固件日志记录
~~~~~~~~~~~~~~~
配置模块会指示固件，配置的模块应生成驱动程序感兴趣的事件，但直到发送启用消息给固件时才会将事件发送到驱动程序。为此，用户可以向'fwlog/enable'写入1（启用）或0（禁用）。示例如下：
  
  # echo 1 > /sys/kernel/debug/ice/0000:18:00.0/fwlog/enable

检索固件日志数据
~~~~~~~~~~~~~~~~~~~~~~
可以通过从'fwlog/data'读取来检索固件日志数据。用户可以向'fwlog/data'写入任何值以清除数据。只有在固件日志记录被禁用时才能清除数据。固件日志数据是一个二进制文件，发送给Intel以帮助调试用户问题。
示例如下：
  
  # cat /sys/kernel/debug/ice/0000:18:00.0/fwlog/data > fwlog.bin
  
清除数据的示例如下：
  
  # echo 0 > /sys/kernel/debug/ice/0000:18:00.0/fwlog/data

更改日志事件发送到驱动程序的频率
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序从管理接收队列（ARQ）接收固件日志数据。通过向'fwlog/nr_messages'写入可以配置固件发送ARQ事件的频率。范围是1-128（1表示推送每个日志消息，128表示仅当最大AQ命令缓冲区满时才推送）。建议的值是10。用户可以通过读取'fwlog/nr_messages'查看配置的值。示例如下：
  
  # echo 50 > /sys/kernel/debug/ice/0000:18:00.0/fwlog/nr_messages

配置用于存储固件日志数据的内存大小
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序在驱动程序内部存储固件日志数据。默认情况下，用于存储数据的内存大小为1MB。某些使用场景可能需要更多或更少的数据，因此用户可以更改分配用于固件日志数据的内存数量。
要更改内存数量，请写入'fwlog/log_size'。值必须是以下之一：128K、256K、512K、1M或2M。必须禁用固件日志记录才能更改值。更改值的示例如下：
  
  # echo 128K > /sys/kernel/debug/ice/0000:18:00.0/fwlog/log_size

性能优化
========================
驱动程序的默认值旨在适应各种工作负载，但如果需要进一步优化，我们建议尝试以下设置。

接收描述符环大小
-----------------------
为了减少接收包丢弃的数量，可以使用ethtool增加每个接收环的接收描述符的数量。
检查接口是否由于缓冲区已满而丢弃接收包（rx_dropped.nic可能意味着没有PCIe带宽）：
  
    # ethtool -S <ethX> | grep "rx_dropped"
  
如果前面的命令显示队列中的丢弃情况，增加描述符的数量可能会有所帮助，使用'ethtool -G'：
  
    # ethtool -G <ethX> rx <N>
    
其中<N>是期望的环条目/描述符的数量。这可以为CPU处理描述符时出现的问题提供临时缓冲。

中断速率限制
-----------------------
此驱动程序支持一种自适应中断节流率（ITR）机制，该机制针对一般工作负载进行了调优。用户可以通过ethtool调整两次中断之间的微秒数来自定义特定工作负载的中断速率控制。
为了手动设置中断率，您必须禁用自适应模式：

```sh
# ethtool -C <ethX> adaptive-rx off adaptive-tx off
```

为了降低CPU利用率：

```sh
禁用自适应ITR并降低Rx和Tx中断。下面的例子会影响指定接口的每个队列。
将rx-usecs和tx-usecs设置为80将会限制每个队列每秒大约12,500次中断：
```

```sh
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 80 tx-usecs 80
```

为了减少延迟：

```sh
禁用自适应ITR，并通过ethtool将rx-usecs和tx-usecs设置为0：
```

```sh
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0
```

每个队列的中断率设置：

```sh
以下示例针对队列1和3，但您可以调整其他队列。
要禁用队列1和3的Rx自适应ITR并将静态Rx ITR设置为10微秒（或大约100,000次中断/秒）：
```

```sh
# ethtool --per-queue <ethX> queue_mask 0xa --coalesce adaptive-rx off rx-usecs 10
```

```sh
要显示队列1和3当前的合并设置：
```

```sh
# ethtool --per-queue <ethX> queue_mask 0xa --show-coalesce
```

使用rx-usecs-high限制中断率：

```sh
有效范围：0-236（0表示不限制）

0到236微秒的有效范围提供了每秒4,237到250,000次中断。rx-usecs-high值可以在同一ethtool命令中独立于rx-usecs和tx-usecs设置，并且也独立于自适应中断调节算法。底层硬件支持4微秒的粒度，因此相邻值可能会导致相同的中断率。
以下命令会禁用自适应中断调节，并允许在指示接收或传输完成前最多5微秒。然而，这不会导致每秒多达200,000次中断，而是通过rx-usecs-high参数将总中断限制为每秒50,000次：
```

```sh
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs-high 20 rx-usecs 5 tx-usecs 5
```

虚拟化环境
----------
除了本节中的其他建议外，以下建议可能有助于优化VM中的性能：
使用适当的机制（如vcpupin），将CPU绑定到单个LCPUs，并确保使用设备local_cpulist中包含的一组CPU：`/sys/class/net/<ethX>/device/local_cpulist`
在VM中配置尽可能多的Rx/Tx队列。（参见iavf驱动程序文档以了解支持的队列数量。）例如：
```sh
# ethtool -L <virt_interface> rx <max> tx <max>
```

支持
====
对于一般信息，请访问Intel支持网站：
https://www.intel.com/support/

如果在受支持的内核上发布的源代码中发现与受支持的适配器相关的问题，请将与问题相关的信息发送至intel-wired-lan@lists.osuosl.org

商标
====
Intel是Intel Corporation或其子公司在美国和其他国家的商标或注册商标。
* 其他名称和品牌可能是他人的财产。
