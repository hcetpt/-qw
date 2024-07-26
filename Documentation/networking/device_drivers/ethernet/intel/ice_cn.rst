... SPDX 许可证标识符: GPL-2.0+ 

=================================================================
Intel(R) 以太网控制器 800 系列的 Linux 基础驱动程序
=================================================================

Intel ice Linux 驱动程序
版权所有 (c) 2018-2021 英特尔公司
内容
========

- 概述
- 识别您的适配器
- 重要说明
- 额外功能与配置
- 性能优化

与此驱动程序关联的虚拟功能 (VF) 驱动程序为 iavf。
可以通过 ethtool 和 lspci 获取驱动程序信息。
有关硬件要求的问题，请参阅随附的 Intel 适配器文档。列出的所有硬件要求均适用于 Linux 使用。
此驱动程序支持 XDP（快速数据路径）和 AF_XDP 零拷贝。请注意，对于大于 3KB 的帧大小，XDP 将被阻止。

识别您的适配器
========================
要了解如何识别您的适配器以及获取最新的 Intel 网络驱动程序，请访问 Intel 支持网站：
https://www.intel.com/support


重要说明
===============

在接收压力下可能会出现丢包
-------------------------------------------
基于 Intel(R) 以太网控制器 800 系列的设备设计时考虑到了 PCIe 和 DMA 事务中的有限系统延迟容忍度。
如果这些事务的时间超过可容忍的延迟，可能会影响数据包在设备及其关联内存中缓冲的时间长度，从而可能导致数据包丢失。这些数据包丢失通常在标准工作负载下对吞吐量和性能的影响不大。
如果这些数据包丢失似乎影响了您的工作负载，以下措施可能会改善情况：

1) 确保系统的物理内存处于高性能配置状态，如同平台供应商推荐的那样。常见的建议是所有通道都安装单个 DIMM 模块。
2) 在系统的 BIOS/UEFI 设置中选择“性能”配置文件。
### 3) 您的发行版可能提供诸如“tuned”之类的工具，这些工具可以帮助调整内核设置以针对不同的工作负载实现更好的标准设置。
配置 SR-IOV 以提高网络安全性
--------------------------------
在虚拟化环境中，在支持 SR-IOV 的 Intel® 以太网网络适配器上，虚拟功能（VF）可能会遭受恶意行为的影响。软件生成的第二层帧，如 IEEE 802.3x（链路流控制）、IEEE 802.1Qbb（基于优先级的流控）等类型的数据包，并不常见且可能导致主机与虚拟交换机之间的流量被抑制，进而降低性能。为了解决此问题并确保隔离不必要的数据流，请从物理功能（PF）的管理接口配置所有启用了 SR-IOV 的端口进行 VLAN 标签处理。这种配置允许丢弃意外或潜在恶意的帧。

请参阅本 README 后面的“在启用了 SR-IOV 的适配器端口上配置 VLAN 标签”部分获取配置指令。

不要在有活动虚拟机绑定的虚拟功能上卸载端口驱动
---------------------------------------------------------
如果一个虚拟功能（VF）与一个活动虚拟机（VM）绑定，则不要卸载该端口的驱动程序。这样做会导致端口看似挂起。一旦虚拟机关闭或以其他方式释放了 VF，命令才会完成执行。

附加功能和配置
==================

ethtool
-------
驱动程序使用 ethtool 接口来进行驱动配置、诊断以及显示统计信息。为此功能需要最新版本的 ethtool。您可以在以下网址下载：[https://kernel.org/pub/software/network/ethtool/](https://kernel.org/pub/software/network/ethtool/)

**注意：** ethtool 中的 `rx_bytes` 值与 Netdev 中的 `rx_bytes` 值不符，因为设备会剥离 4 字节的 CRC。两个 `rx_bytes` 值之间的差异将是接收数据包数乘以 4 字节 CRC 的结果。例如，如果接收的数据包数为 10 个，而 Netdev（软件统计）显示的 `rx_bytes` 值为 “X”，则 ethtool（硬件统计）将显示 `rx_bytes` 值为 “X + 40”（4 字节 CRC × 10 个数据包）。

查看连接消息
--------------
如果发行版限制系统消息，则不会在控制台上显示连接消息。要查看网络驱动的连接消息，请将 dmesg 设置为 8，方法如下：

```bash
# dmesg -n 8
```

**注意：** 此设置不会跨重启保存。

动态设备个性化
-----------------
动态设备个性化（DDP）允许您通过在运行时应用配置文件包来更改设备的数据包处理管道。配置文件可用于添加对新协议的支持、更改现有协议或更改默认设置。DDP 配置文件还可以在无需重新启动系统的情况下回滚。
DDP 包在设备初始化期间加载。驱动程序会在固件根目录（通常为 `/lib/firmware/` 或 `/lib/firmware/updates/`）中查找 `intel/ice/ddp/ice.pkg`，并检查其中是否包含有效的 DDP 包文件。

**注释：** 您的发行版很可能已经提供了最新的 DDP 文件，但如果缺少 `ice.pkg` 文件，您可以在 `linux-firmware` 存储库或从 intel.com 找到它。

如果驱动程序无法加载 DDP 包，则设备将进入安全模式。安全模式禁用了高级和性能特性，仅支持基本流量和最小功能，例如更新 NVM 或下载新的驱动程序或 DDP 包。安全模式仅适用于受影响的物理功能（PF），不会影响其他任何 PF。有关 DDP 和安全模式的更多详细信息，请参阅“Intel(R) 以太网适配器和设备用户指南”。

**注释：**

- 如果遇到 DDP 包文件的问题，您可能需要下载更新的驱动程序或 DDP 包文件。请参阅日志消息获取更多信息。
- `ice.pkg` 文件是对默认 DDP 包文件的符号链接。
- 如果已有任何 PF 驱动程序加载，则无法更新 DDP 包。要覆盖一个包，请卸载所有 PF，然后使用新包重新加载驱动程序。
- 只有每个设备首次加载的 PF 才能为此设备下载包。

您可以在同一系统中的不同物理设备上安装特定的 DDP 包文件。要安装特定的 DDP 包文件：

1. 下载您设备所需的 DDP 包文件。
2. 将文件重命名为 `ice-xxxxxxxxxxxxxxxx.pkg`，其中 `'xxxxxxxxxxxxxxxx'` 是您希望下载此包的设备的唯一 64 位 PCI Express 设备序列号（十六进制）。文件名必须包括完整的序列号（包括前导零），并且全部为小写。例如，如果 64 位序列号是 `b887a3ffffca0568`，则文件名应为 `ice-b887a3ffffca0568.pkg`。
为了从 PCI 总线地址找到序列号，您可以使用以下命令：

   ```
   # lspci -vv -s af:00.0 | grep -i Serial
   Capabilities: [150 v1] Device Serial Number b8-87-a3-ff-ff-ca-05-68
   ```

使用以下命令可以格式化序列号，去除破折号：

   ```
   # lspci -vv -s af:00.0 | grep -i Serial | awk '{print $7}' | sed s/-//g
   b887a3ffffca0568
   ```

3. 将重命名后的 DDP 包文件复制到 `/lib/firmware/updates/intel/ice/ddp/`。如果该目录还不存在，请在复制文件之前创建它。
4. 卸载设备上的所有PF（物理功能）。
5. 使用新的软件包重新加载驱动程序。
注意事项：如果存在特定于设备的DDP（设备专有包）文件，则会覆盖默认DDP包文件（ice.pkg）的加载。

英特尔® 以太网流导向器
------------------------
英特尔以太网流导向器执行以下任务：

- 根据数据包的流向将其导向不同的队列。
- 允许对平台中的流量路由进行精确控制。
- 匹配流量与CPU核心，以实现流量亲和性。

注意事项：此驱动程序支持以下类型的流量：

- IPv4
- TCPv4
- UDPv4
- SCTPv4
- IPv6
- TCPv6
- UDPv6
- SCTPv6

每种流量类型都支持有效的IP地址组合（源或目标）以及UDP/TCP/SCTP端口（源和目标）。您可以只提供源IP地址、源IP地址和目标端口，或者这四个参数的任意组合。

注意事项：此驱动程序允许您根据用户定义的可灵活调整的两字节模式及偏移量来过滤流量，使用ethtool的用户定义字段和掩码字段。仅支持L3和L4流量类型的用户定义的可灵活调整的过滤器。对于给定的流量类型，在更改输入集（对于该流量类型）之前，必须清除所有英特尔以太网流导向器过滤器。

流导向器过滤器
-----------------
流导向器过滤器用于导向匹配指定特性的流量。这些过滤器通过ethtool的ntuple接口启用。要启用或禁用英特尔以太网流导向器及其过滤器，请执行以下命令：

  # ethtool -K <ethX> ntuple <off|on>

注意事项：当您禁用ntuple过滤器时，所有用户编程的过滤器都会从驱动程序缓存和硬件中被清除。重新启用ntuple时，需要重新添加所有必要的过滤器。

要显示所有活动过滤器，请执行以下命令：

  # ethtool -u <ethX>

要添加一个新的过滤器，请执行以下命令：

  # ethtool -U <ethX> flow-type <type> src-ip <ip> [m <ip_mask>] dst-ip <ip>
  [m <ip_mask>] src-port <port> [m <port_mask>] dst-port <port> [m <port_mask>]
  action <queue>

其中：
  <ethX> - 要编程的以太网设备
  <type> - 可以是ip4, tcp4, udp4, sctp4, ip6, tcp6, udp6, sctp6
  <ip> - 要匹配的IP地址
  <ip_mask> - 要屏蔽的IPv4地址
  注意：这些过滤器使用反向掩码
  <port> - 要匹配的端口号
  <port_mask> - 用于屏蔽的16位整数
  注意：这些过滤器使用反向掩码
  <queue> - 要导向的数据队列（-1表示丢弃匹配的流量）

要删除一个过滤器，请执行以下命令：

  # ethtool -U <ethX> delete <N>

其中<N>是在打印所有活动过滤器时显示的过滤器ID，也可能在添加过滤器时使用"loc <N>"指定了该ID。

示例：

要添加一个将数据包导向队列2的过滤器，请执行以下命令：

  # ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
  192.168.10.2 src-port 2000 dst-port 2001 action 2 [loc 1]

仅使用源和目标IP地址设置过滤器，请执行以下命令：

  # ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
  192.168.10.2 action 2 [loc 1]

基于用户定义的模式和偏移量设置过滤器，请执行以下命令：

  # ethtool -U <ethX> flow-type tcp4 src-ip 192.168.10.1 dst-ip \
  192.168.10.2 user-def 0x4FFFF action 2 [loc 1]

其中用户定义字段的值包含偏移量（4字节）和模式（0xffff）。
为了匹配从 192.168.0.1 的端口 5300 发送到 192.168.0.5 的端口 80 的 TCP 流量，并将其发送到队列 7：

  # ethtool -U enp130s0 flow-type tcp4 src-ip 192.168.0.1 dst-ip 192.168.0.5
  src-port 5300 dst-port 80 action 7

为了添加一个具有部分掩码的源 IP 子网的 TCPv4 过滤器：

  # ethtool -U <ethX> flow-type tcp4 src-ip 192.168.0.0 m 0.255.255.255 dst-ip
  192.168.5.12 src-port 12600 dst-port 31 action 12

注释：

对于每种流类型，编程的过滤器必须具有相同的匹配输入集。例如，发出以下两个命令是可以接受的：

  # ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  # ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.5 src-port 55 action 10

然而，发出下面这两个命令是不可接受的，因为第一个指定了 src-ip 而第二个指定了 dst-ip：

  # ethtool -U enp130s0 flow-type ip4 src-ip 192.168.0.1 src-port 5300 action 7
  # ethtool -U enp130s0 flow-type ip4 dst-ip 192.168.0.5 src-port 55 action 10

第二个命令将因错误而失败。你可以为同一字段编程多个过滤器并使用不同的值，但是在一台设备上，你不能为两种具有不同匹配字段的 tcp4 过滤器编程。
ice 驱动不支持对字段的子部分进行匹配，因此不支持部分掩码字段。
灵活字节流导向过滤器
----------------------
驱动程序还支持在数据包的有效负载内匹配用户定义的数据。这种灵活的数据通过 ethtool 命令中的 "user-def" 字段以如下方式指定：

.. 表格::

    ============================== ============================
    ``31    28    24    20    16`` ``15    12    8    4    0``
    ``进入数据包有效负载的偏移量`` ``2 字节的灵活数据``
    ============================== ============================

例如，

::

  ... user-def 0x4FFFF ..
告诉过滤器查找有效负载中第 4 个字节，并将该值与 0xFFFF 匹配。偏移量基于有效负载的开始位置，而不是数据包的开始位置。因此

::

  flow-type tcp4 ... user-def 0x8BEAF ..
将会匹配那些在 TCP/IPv4 数据包的有效负载中第 8 个字节处具有值 0xBEAF 的 TCP/IPv4 数据包。
需要注意的是，ICMP 头被视为 4 字节的头部和 4 字节的有效负载。因此，要匹配有效负载的第一个字节，实际上需要在偏移量上加上 4 字节。此外，请注意 ip4 过滤器同时匹配 ICMP 帧以及原始（未知）ip4 帧，在这些帧中有效负载将是 IP4 帧的 L3 有效负载。
最大偏移量是 64。硬件只会从有效负载中读取最多 64 字节的数据。偏移量必须是偶数，因为灵活数据长度为 2 字节，并且必须与数据包有效负载的字节 0 对齐。
用户定义的灵活偏移量也被认为是输入集的一部分，不能为同一类型的多个过滤器单独编程。但是，灵活数据不是输入集的一部分，多个过滤器可以使用相同的偏移量但匹配不同的数据。
RSS 哈希流配置
--------------
允许您为每种流类型设置哈希字节数，并且可以组合一个或多个选项来配置接收端扩展（RSS）的哈希字节。

```
# ethtool -N <ethX> rx-flow-hash <type> <option>
```

其中 `<type>` 是：
- tcp4    表示 TCP 过 IPv4
- udp4    表示 UDP 过 IPv4
- gtpc4   表示 GTP-C 过 IPv4
- gtpc4t  表示 GTP-C (包括 TEID) 过 IPv4
- gtpu4   表示 GTP-U 过 IPv4
- gtpu4e  表示 GTP-U 和扩展头过 IPv4
- gtpu4u  表示 GTP-U PSC 上行链路过 IPv4
- gtpu4d  表示 GTP-U PSC 下行链路过 IPv4
- tcp6    表示 TCP 过 IPv6
- udp6    表示 UDP 过 IPv6
- gtpc6   表示 GTP-C 过 IPv6
- gtpc6t  表示 GTP-C (包括 TEID) 过 IPv6
- gtpu6   表示 GTP-U 过 IPv6
- gtpu6e  表示 GTP-U 和扩展头过 IPv6
- gtpu6u  表示 GTP-U PSC 上行链路过 IPv6
- gtpu6d  表示 GTP-U PSC 下行链路过 IPv6

而 `<option>` 可以是一个或多个：
- s     基于接收数据包的 IP 源地址进行哈希
- d     基于接收数据包的 IP 目的地址进行哈希
- f     基于接收数据包的第 4 层头部的第 0 和第 1 字节进行哈希
- n     基于接收数据包的第 4 层头部的第 2 和第 3 字节进行哈希
- e     基于接收数据包中的 GTP 包的 TEID (4 字节) 进行哈希

加速接收流导向 (aRFS)
-----------------------
基于 Intel(R) 以太网控制器 800 系列的设备支持物理功能 (PF) 上的加速接收流导向 (aRFS)。aRFS 是一种负载均衡机制，它允许将数据包导向到正在运行或消耗该流中数据包的应用程序所在的同一 CPU。

注意事项：

- 使用 aRFS 需要通过 ethtool 启用 ntuple 过滤。
- aRFS 支持以下类型的包：
    - TCP 过 IPv4 和 IPv6
    - UDP 过 IPv4 和 IPv6
    - 非分段包
- aRFS 仅支持 Flow Director 过滤器，这些过滤器包含源/目标 IP 地址和源/目标端口。
- aRFS 和 ethtool 的 ntuple 接口都使用设备的 Flow Director。aRFS 和 ntuple 功能可以共存，但如果 aRFS 和 ntuple 请求之间存在冲突，则可能会遇到意外的结果。有关更多信息，请参阅“Intel(R) 以太网 Flow Director”。
设置 aRFS（自适应接收流散列）：

1. 使用 `ethtool` 启用 Intel 网络适配器的 Flow Director 和 ntuple 过滤器：
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

4. 禁用 IRQ 平衡守护进程（这仅是临时停止服务，直到下一次重启）
   ```
   # systemctl stop irqbalance
   ```

5. 配置中断亲和性
   查看 ``/Documentation/core-api/irq/irq-affinity.rst``

使用 `ethtool` 禁用 aRFS：
```
# ethtool -K <ethX> ntuple off
```

**注意：** 此命令将禁用 ntuple 过滤器并清除软件和硬件中的所有 aRFS 过滤器。

示例使用案例：

1. 将服务器应用程序设置在所需的 CPU 上（例如，CPU 4）
   ```
   # taskset -c 4 netserver
   ```

2. 使用 netperf 将来自客户端的流量路由到配置了 aRFS 的服务器上的 CPU 4。此示例使用 IPv4 上的 TCP
   ```
   # netperf -H <主机IPv4地址> -t TCP_STREAM
   ```

启用虚拟功能（VFs）
---------------------
使用 sysfs 来启用虚拟功能（VF）
例如，可以创建 4 个 VFs 如下：
```
# echo 4 > /sys/class/net/<ethX>/device/sriov_numvfs
```

要禁用 VFs，请向同一文件写入 0：
```
# echo 0 > /sys/class/net/<ethX>/device/sriov_numvfs
```

ice 驱动程序的最大 VFs 数量总共为 256 个（所有端口）。要检查每个 PF 支持多少个 VFs，请使用以下命令：
```
# cat /sys/class/net/<ethX>/device/sriov_totalvfs
```

**注释：** 当链路聚合（LAG）/绑定处于活动状态时，不能使用 SR-IOV，反之亦然。为了强制执行这一点，驱动程序会检查这种互斥关系。

显示 PF 上的 VF 统计信息
----------------------------
使用以下命令来显示 PF 及其 VFs 的统计信息：
```
# ip -s link show dev <ethX>
```

**注释：** 由于可能的 VFs 数量最大，此命令的输出可能会非常大。
PF 驱动程序将显示 PF 及所有已配置 VF 的部分统计信息。PF 总是为每个可能的 VF 打印一个统计信息块，并且对于所有未配置的 VF 显示零。
### 在SR-IOV启用的适配器端口上配置VLAN标记
----------------------------------------------------------------
要为SR-IOV启用的适配器上的端口配置VLAN标记，请使用以下命令。VLAN配置应在VF驱动加载或虚拟机启动之前完成。VF不会意识到在发送时插入并在接收帧时移除的VLAN标签（有时称为“端口VLAN”模式）：
```
# ip link set dev <ethX> vf <id> vlan <vlan id>
```

例如，下面的命令将配置PF eth0和VLAN 10上的第一个VF：
```
# ip link set dev eth0 vf 0 vlan 10
```

### 如果端口断开连接时启用VF链接
---------------------------------------------------------------------------------
如果物理功能(PF)链接已关闭，你可以从主机PF强制任何绑定到PF的虚拟功能(VF)链接打开。
例如，要强制PF eth0绑定的VF 0链接打开：
```
# ip link set eth0 vf 0 state enable
```

注意：如果该命令不起作用，可能不被你的系统支持。

### 为VF设置MAC地址
--------------------------------------------------------------------
要更改指定VF的MAC地址：
```
# ip link set <ethX> vf 0 mac <address>
```

例如：
```
# ip link set <ethX> vf 0 mac 00:01:02:03:04:05
```

此设置将持续到PF重新加载为止。
**注意**：从主机为VF分配MAC地址会禁用随后在VM内部更改MAC地址的请求。这是一种安全特性。VM不会意识到这一限制，因此如果尝试在VM内部进行更改，则会触发MDD事件。

### 可信VF与VF混杂模式
---------------------------------------------------------------------
此功能允许你将特定的VF指定为可信，并允许该可信VF向物理功能(PF)请求选择性混杂模式。
要在Hypervisor中将VF设置为可信或不可信，输入以下命令：
```
# ip link set dev <ethX> vf 1 trust [on|off]
```

**注意**：重要的是在设置混杂模式之前将VF设置为可信。
如果不信任VM，PF将忽略来自VF的混杂模式请求。如果VF驱动加载后VM变为可信，则必须发出新请求以将VF设置为混杂模式。
一旦VF被指定为可信，使用以下命令在VM中将VF设置为混杂模式。
对于全混杂模式：
```
# ip link set <ethX> promisc on
```
其中`<ethX>`是VM中的VF接口。

对于多播混杂模式：
```
# ip link set <ethX> allmulticast on
```
其中`<ethX>`是VM中的VF接口。

**注意**：默认情况下，ethtool私有标志`vf-true-promisc-support`设置为"off"，这意味着VF的混杂模式将受到限制。要将VF的混杂模式设置为真正的混杂模式并允许VF查看所有传入流量，请使用以下命令：
```
# ethtool --set-priv-flags <ethX> vf-true-promisc-support on
```

`vf-true-promisc-support`私有标志不会启用混杂模式；相反，它指定了使用上述ip link命令启用混杂模式时将获得哪种类型的混杂模式（受限或真正）。请注意，这是一个影响整个设备的全局设置。但是，`vf-true-promisc-support`私有标志仅对设备的第一个PF可见。无论`vf-true-promisc-support`设置如何，PF都保持在受限混杂模式下。
接下来，在VF接口上添加一个VLAN接口。例如：

  # ip link add link eth2 name eth2.100 type vlan id 100

请注意，将VF设置为混杂模式和添加VLAN接口的顺序无关紧要（您可以先做任何一个）。在这个例子中，结果是VF将接收到所有带有VLAN 100标签的流量。

### VF的恶意驱动检测(MDD)

一些Intel以太网设备使用恶意驱动检测(MDD)来检测来自VF的恶意流量，并在VF驱动重置前禁用Tx/Rx队列或丢弃违规数据包。您可以通过dmesg命令查看PF系统日志中的MDD消息。
- 如果PF驱动记录了来自VF的MDD事件，请确认安装了正确的VF驱动。
- 要恢复功能，您可以手动重新加载VF或虚拟机，或者启用自动VF重置。
- 当启用了自动VF重置时，当检测到接收路径上的MDD事件时，PF驱动会立即重置VF并重新启用队列。
- 如果禁用了自动VF重置，当检测到MDD事件时，PF不会自动重置VF。

要启用或禁用自动VF重置，请使用以下命令：

  # ethtool --set-priv-flags <ethX> mdd-auto-reset-vf on|off

### VF的MAC和VLAN反欺骗功能

当VF接口上的恶意驱动尝试发送欺骗性数据包时，硬件会将其丢弃并不进行传输。

注意：此功能可以针对特定的VF禁用：

  # ip link set <ethX> vf <vf id> spoofchk {off|on}

### 巨型帧支持

巨型帧支持通过将最大传输单元(MTU)更改为大于默认值1500的值来实现。
使用ifconfig命令增加MTU大小。例如，输入以下内容，其中<ethX>是接口编号：

  # ifconfig <ethX> mtu 9000 up

或者，您可以使用ip命令如下：

  # ip link set mtu 9000 dev <ethX>
  # ip link set up dev <ethX>

此设置不会在重启后保存。

注意：巨型帧的最大MTU设置为9702。这对应于最大巨型帧大小9728字节。
注释：此驱动程序将尝试使用多个页面大小的缓冲区来接收每个巨型数据包。这有助于避免在分配接收数据包时出现缓冲区资源不足的问题。
注释：使用巨型帧时，丢包可能会对吞吐量产生更大的影响。如果您在启用巨型帧后观察到性能下降，启用流控制可能会缓解该问题。
速度和双工配置
-------------------
针对速度和双工配置问题，您需要区分基于铜线的适配器和基于光纤的适配器。
默认模式下，使用铜线连接的Intel® 以太网网络适配器会尝试与链接伙伴自动协商以确定最佳设置。如果适配器无法使用自动协商与链接伙伴建立链接，则可能需要手动将适配器及其链接伙伴配置为相同的设置才能建立链接并传输数据包。通常仅当尝试与不支持自动协商或已被强制设定为特定速度或双工模式的旧式交换机链接时才需要这样做。您的链接伙伴必须匹配您选择的设置。1Gbps及以上的速度不能被强制设置。使用自动协商广告设置来手动设置1Gbps及以上设备。
速度、双工以及自动协商广告是通过`ethtool`实用工具进行配置的。为了获取最新版本，请从此网站下载并安装`ethtool`：

   https://kernel.org/pub/software/network/ethtool/

要查看您的设备支持的速度配置，请运行以下命令：

  # ethtool <ethX>

警告：只有经验丰富的网络管理员应手动强制设置速度和双工或更改自动协商广告。交换机上的设置必须始终与适配器设置匹配。如果将适配器配置得与交换机不同，适配器性能可能会受到影响或适配器可能无法正常工作。
数据中心桥接（DCB）
----------------------
注释：内核假设TC0可用，并且如果TC0不可用，将在设备上禁用优先级流控制（PFC）。要解决这个问题，在设置交换机上的DCB时请确保TC0已启用。
DCB是在硬件中实现的一种配置服务质量机制。它使用VLAN优先级标签（802.1p）过滤流量。这意味着有8种不同的优先级可以将流量过滤进去。它还启用了优先级流控制（802.1Qbb），可以在网络压力期间限制或消除丢弃的数据包数量。可以为这些优先级中的每一个分配带宽，这是在硬件级别（802.1Qaz）执行的。
DCB通常使用DCBX协议（802.1Qaz）在网络中配置，这是一种LLDP（802.1AB）的特例。`ice`驱动程序支持以下两种互斥的DCBX支持变体：

1) 基于固件的LLDP代理
2) 基于软件的LLDP代理

在基于固件的模式中，固件拦截所有LLDP流量并透明地处理DCBX协商。在这种模式下，适配器处于“愿意”DCBX模式，从链接伙伴（通常是交换机）接收DCB设置。本地用户只能查询协商后的DCB配置。有关在交换机上配置DCBX参数的信息，请参阅交换机制造商的文档。
在基于软件的模式中，LLDP流量被转发到网络堆栈和用户空间，其中软件代理可以处理它。在这种模式下，适配器可以处于“愿意”或“不愿意”的DCBX模式，并且DCB配置既可以本地查询也可以设置。这种模式要求禁用基于固件的LLDP代理。
注释：

- 您可以使用`ethtool`的私有标志来启用和禁用基于固件的LLDP代理。有关更多信息，请参阅本README中的“FW-LLDP（基于固件的链路层发现协议）”部分。
在基于软件的 DCBX 模式中，您可以使用与 Linux 内核的 DCB Netlink API 接口的软件 LLDP/DCBX 代理来配置 DCB 参数。我们建议在运行于软件模式时使用 OpenLLDP 作为 DCBX 代理。更多信息，请参阅 OpenLLDP 的手册页和 https://github.com/intel/openlldp

- 驱动程序实现了 DCB Netlink 接口层，允许用户空间与驱动程序进行通信并查询端口的 DCB 配置。
- 不支持带有 DCB 的 iSCSI。

### 固件链路层发现协议 (FW-LLDP)

--------------------------------------

使用 ethtool 更改 FW-LLDP 设置。FW-LLDP 设置是按端口的，并且会在重启后保留设置。

要启用 LLDP:

```shell
# ethtool --set-priv-flags <ethX> fw-lldp-agent on
```

要禁用 LLDP:

```shell
# ethtool --set-priv-flags <ethX> fw-lldp-agent off
```

要检查当前的 LLDP 设置:

```shell
# ethtool --show-priv-flags <ethX>
```

**注意：** 必须启用 UEFI HII “LLDP Agent” 属性以使此设置生效。如果“LLDP AGENT”被设置为禁用，则无法从操作系统中启用它。

### 流量控制

-------------------

可以使用 ethtool 配置以太网流量控制（IEEE 802.3x），以启用接收和发送暂停帧。当启用了发送功能时，在接收数据包缓冲区越过预设阈值时会生成暂停帧。当启用了接收功能时，接收到暂停帧时，传输单元会根据指定的时间延迟停止工作。

**注意：** 必须有一个具备流量控制能力的链路伙伴。
默认情况下，流量控制是禁用的。

使用 ethtool 更改流量控制设置。
要启用或禁用接收 (Rx) 或发送 (Tx) 流量控制:

```shell
# ethtool -A <ethX> rx <on|off> tx <on|off>
```

**注意：** 此命令仅在禁用了自动协商的情况下启用或禁用流量控制。如果启用了自动协商，此命令将更改用于与链路伙伴自动协商的参数。
注释：流控制自动协商是链路自动协商的一部分。根据您的设备，您可能无法更改自动协商设置。

注释：

- ice驱动程序需要在端口和链路伙伴上都启用流控制。如果任一侧禁用了流控制，则在大量流量的情况下端口可能会出现挂起的情况。
- 在禁用DCB后，您可能会遇到链路级别流控制（LFC）的问题。LFC状态可能显示为已启用但流量并未暂停。要解决此问题，请使用ethtool禁用并重新启用LFC：

  # ethtool -A <ethX> rx off tx off  
  # ethtool -A <ethX> rx on tx on

NAPI
----

此驱动程序支持NAPI（接收轮询模式）。更多信息请参阅 :ref:`Documentation/networking/napi.rst <napi>`。

MACVLAN
-------
此驱动程序支持MACVLAN。可以通过检查MACVLAN驱动程序是否已加载来测试内核对MACVLAN的支持。您可以运行 'lsmod | grep macvlan' 来查看MACVLAN驱动程序是否已加载或运行 'modprobe macvlan' 来尝试加载MACVLAN驱动程序。

注释：

- 在passthru模式下，您只能设置一个MACVLAN设备。它将继承底层物理功能（PF）设备的MAC地址。

IEEE 802.1ad (QinQ) 支持
---------------------------
IEEE 802.1ad标准，非正式地称为QinQ，允许在一个以太网帧中包含多个VLAN ID。VLAN ID有时被称为“标签”，因此多个VLAN ID被称为“标签堆栈”。标签堆栈允许L2隧道以及在特定VLAN ID内隔离流量等功能。

注释：

- 不支持802.1ad (QinQ)数据包的接收校验和卸载和VLAN加速。
- 除非使用以下命令禁用VLAN剥离，否则不会接收0x88A8流量：

  # ethtool -K <ethX> rxvlan off

- 0x88A8/0x8100双层VLAN不能与在同一端口上配置的0x8100或0x8100/0x8100 VLAN一起使用。如果配置了0x8100 VLAN，则不会接收0x88A8/0x8100流量。
- 虚拟功能（VF）仅当满足以下条件时才能传输0x88A8/0x8100（即802.1ad/802.1Q）流量：

    1) 虚拟功能（VF）未分配端口VLAN
2) 从 PF 禁用了 spoofchk。如果你启用了 spoofchk，VF 将不会传输 0x88A8/0x8100 流量。
- 当在 SR-IOV 模式下启用了 VF 真正的混杂模式（vf-true-promisc-support）和双层 VLAN 时，VF 可能无法接收到基于内部 VLAN 标头的所有网络流量。
以下是配置 802.1ad (QinQ) 的示例：

  ```
  # ip link add link eth0 eth0.24 type vlan proto 802.1ad id 24
  # ip link add link eth0.24 eth0.24.371 type vlan proto 802.1Q id 371
  ```

  其中 "24" 和 "371" 是示例 VLAN ID。
无状态卸载隧道/覆盖
-------------------
支持的隧道和覆盖包括 VXLAN、GENEVE 等，具体取决于硬件和软件配置。无状态卸载默认是启用的。
要查看所有卸载当前的状态，请执行以下命令：

  ```
  # ethtool -k <ethX>
  ```

UDP 分段卸载
-------------
允许适配器将负载最大为 64K 的 UDP 数据包分段卸载到有效的以太网帧中。由于适配器硬件完成数据分段的速度远快于操作系统软件，此功能可能会提高传输性能。
此外，适配器可能使用更少的 CPU 资源。
**注意：**

- 发送 UDP 数据包的应用程序必须支持 UDP 分段卸载。
要启用或禁用 UDP 分段卸载，请执行以下命令：

  ```
  # ethtool -K <ethX> tx-udp-segmentation [off|on]
  ```

GNSS 模块
---------
需要编译内核时包含 CONFIG_GNSS=y 或 CONFIG_GNSS=m 配置项。
允许用户读取来自 GNSS 硬件模块的消息并写入支持的命令。如果该模块物理存在，则会生成一个 GNSS 设备：
``/dev/gnss<id>``
写入命令的协议依赖于 GNSS 硬件模块，因为驱动程序通过 I2C 接口将原始字节写入 GNSS 对象。有关配置详情，请参阅 GNSS 硬件模块文档。
固件 (FW) 日志记录
---------------------
驱动程序仅通过 PF 0 上的 debugfs 接口支持 FW 日志记录。在 NIC 上运行的 FW 必须支持 FW 日志记录；如果 FW 不支持 FW 日志记录，则 'fwlog' 文件不会在 ice debugfs 目录中创建。

模块配置
~~~~~~~~~~~~
固件日志记录按每个模块进行配置。每个模块都可以独立于其他模块设置值（除非指定了 'all' 模块）。这些模块将在 'fwlog/modules' 目录下实例化。
用户可以通过向模块文件写入来设置模块的日志级别，例如：

  # echo <log_level> > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/<module>

其中

* log_level 是下面描述的一个名称。每个级别都包括来自前一个/更低级别的消息

      *   none
      *   error
      *   warning
      *   normal
      *   verbose

* module 是代表要接收事件的模块的名称。模块名称有

      *   general
      *   ctrl
      *   link
      *   link_topo
      *   dnl
      *   i2c
      *   sdp
      *   mdio
      *   adminq
      *   hdma
      *   lldp
      *   dcbx
      *   dcb
      *   xlr
      *   nvm
      *   auth
      *   vpd
      *   iosf
      *   parser
      *   sw
      *   scheduler
      *   txq
      *   rsvd
      *   post
      *   watchdog
      *   task_dispatch
      *   mng
      *   synce
      *   health
      *   tsdrv
      *   pfreg
      *   mdlver
      *   all

'all' 这个名称是特殊的，允许用户将所有模块设置为指定的日志级别或读取所有模块的日志级别。

配置模块的示例用法
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

要将单个模块设置为 'verbose'：

  # echo verbose > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/link

要设置多个模块，可以多次发出命令：

  # echo verbose > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/link
  # echo warning > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/ctrl
  # echo none > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/dcb

要将所有模块设置为相同的值：

  # echo normal > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/all

要读取特定模块的日志级别（例如 'general' 模块）：

  # cat /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/general

要读取所有模块的日志级别：

  # cat /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/modules/all

启用 FW 日志
~~~~~~~~~~~~~~~
配置模块会指示 FW 配置的模块应生成驱动程序感兴趣的事件，但这 **并不会** 将事件发送给驱动程序，直到向 FW 发送启用消息。为此，用户可以向 'fwlog/enable' 写入 1（启用）或 0（禁用）。一个示例是：

  # echo 1 > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/enable

获取 FW 日志数据
~~~~~~~~~~~~~~~~~~~~~~
可以通过从 'fwlog/data' 读取来获取 FW 日志数据。用户可以向 'fwlog/data' 写入任何值以清除数据。只有在禁用 FW 日志记录时才能清除数据。FW 日志数据是一个二进制文件，发送给 Intel 用于帮助调试用户问题。
读取数据的一个示例：

  # cat /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/data > fwlog.bin

清除数据的一个示例：

  # echo 0 > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/data

更改发送到驱动程序的日志事件频率
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序从管理接收队列 (ARQ) 接收 FW 日志数据。FW 发送 ARQ 事件的频率可以通过写入 'fwlog/nr_messages' 来配置。范围是 1-128（1 表示推送每个日志消息，128 表示仅当最大 AQ 命令缓冲区已满时才推送）。建议值是 10。用户可以通过读取 'fwlog/nr_messages' 查看配置的值。设置值的一个示例：

  # echo 50 > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/nr_messages

配置用于存储 FW 日志数据的内存大小
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序在驱动程序内部存储 FW 日志数据。用于存储数据的内存默认大小为 1MB。某些使用情况可能需要更多或更少的数据，因此用户可以更改分配用于 FW 日志数据的内存量。
要更改内存量，请写入 'fwlog/log_size'。值必须是：128K、256K、512K、1M 或 2M。必须禁用 FW 日志记录才能更改该值。更改值的一个示例：

  # echo 128K > /sys/kernel/debug/ice/0000\:18\:00.0/fwlog/log_size

性能优化
========================
驱动程序的默认设置旨在适应各种工作负载，但如果需要进一步优化，我们建议尝试以下设置。

接收描述符环大小
-----------------------
为了减少接收包丢弃的数量，可以使用 ethtool 增加每个接收环的接收描述符数量。
检查接口是否因为缓冲区已满而丢弃接收包
  (rx_dropped.nic 可能意味着没有 PCIe 带宽)：

    # ethtool -S <ethX> | grep "rx_dropped"

  如果上述命令显示队列中有丢包，可以通过 'ethtool -G' 增加描述符数量：

    # ethtool -G <ethX> rx <N>
    其中 <N> 是所需的环条目/描述符数量

  这可以为处理描述符时产生的延迟提供临时缓冲。

中断速率限制
-----------------------
此驱动程序支持自适应中断节流率 (ITR) 机制，该机制针对一般工作负载进行了调优。用户可以通过 ethtool 调整两次中断之间的微秒数来自定义特定工作负载的中断速率控制。
要手动设置中断率，您必须禁用自适应模式：

  # ethtool -C <ethX> adaptive-rx off adaptive-tx off

为了降低CPU使用率：

  禁用自适应ITR并减少Rx和Tx中断。下面的例子会影响指定接口的每个队列。
将rx-usecs和tx-usecs设置为80会将每个队列的中断限制在大约每秒12,500次：

    # ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 80 tx-usecs 80

为了减少延迟：

  禁用自适应ITR和ITR，通过ethtool将rx-usecs和tx-usecs设置为0：

    # ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0

每个队列的中断率设置：

  下面的例子是针对队列1和3，但您可以调整其他队列。
为了禁用Rx自适应ITR并将静态Rx ITR设置为10微秒或大约每秒100,000次中断，对于队列1和3：

    # ethtool --per-queue <ethX> queue_mask 0xa --coalesce adaptive-rx off rx-usecs 10

  要显示队列1和3当前的合并设置：

    # ethtool --per-queue <ethX> queue_mask 0xa --show-coalesce

使用rx-usecs-high来限定中断率：

  :有效范围：0-236（0=无限制）

   0-236微秒的范围提供了每秒4,237到250,000次中断的有效范围。rx-usecs-high的值可以独立于rx-usecs和tx-usecs在同一ethtool命令中设置，并且也独立于自适应中断调节算法。底层硬件支持4微秒的粒度，因此相邻值可能导致相同的中断率。
以下命令将禁用自适应中断调节，并允许最多5微秒的时间来指示接收或发送完成。然而，这不会导致每秒多达200,000次中断，而是通过rx-usecs-high参数将总中断每秒限制在50,000次：

    # ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs-high 20 rx-usecs 5 tx-usecs 5

虚拟化环境
----------
除了本节中的其他建议外，以下内容可能有助于优化VM中的性能：
使用适当的机制（例如vcpupin）在VM中将CPU绑定到单个LCPUs，确保使用包含在设备的local_cpulist中的CPU集：`/sys/class/net/<ethX>/device/local_cpulist`
在VM中配置尽可能多的Rx/Tx队列（参见iavf驱动程序文档中支持的队列数量）。例如：

    # ethtool -L <virt_interface> rx <max> tx <max>

支持
====
对于一般信息，请访问Intel的支持网站：
https://www.intel.com/support/

如果已发布源代码在受支持的内核上发现有支持适配器的问题，将与问题相关的确切信息发送至intel-wired-lan@lists.osuosl.org
商标
====
Intel是Intel Corporation或其在美国和其他/或国家的子公司的商标或注册商标
* 其他名称和品牌可能是他人的财产。
