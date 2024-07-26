SPDX 许可证标识符: GPL-2.0

==========
batman-adv
==========

Batman advanced 是一种无线网络的新方法，它不再基于 IP 进行操作。与使用 UDP 数据包交换信息并设置路由表的 batman 守护进程不同，batman-advanced 只在 ISO/OSI 第二层上运行，并且使用和路由（更准确地说是桥接）以太网帧。它模拟了所有参与节点的虚拟网络交换机。因此所有节点都表现为链路本地，这意味着网络中的任何变化都不会影响更高层的操作协议。你几乎可以在 batman advanced 上运行任何协议，一些显著的例子包括：IPv4、IPv6、DHCP、IPX。
Batman advanced 被实现为一个 Linux 内核驱动程序，以将开销降到最低。它不依赖于任何其他网络驱动程序，并且可以在 WiFi 以及以太网局域网、VPN 等等（任何具有以太网风格第二层的东西）上使用。
配置
=============

将 batman-adv 模块加载到你的内核中：

  $ insmod batman-adv.ko

模块现在正在等待激活。你必须添加一些接口供 batman-adv 运行。可以使用 iproute2 工具 `ip` 创建 batman-adv 的软接口：

  $ ip link add name bat0 type batadv

要激活给定的接口，只需将其附加到 `bat0` 接口：

  $ ip link set dev eth0 master bat0

对所有希望添加的接口重复此步骤。现在 batman-adv 开始使用/广播这些接口。
要停用一个接口，需要将其从 "bat0" 接口分离：

  $ ip link set dev eth0 nomaster

也可以使用 batctl 的接口子命令完成相同的操作：

  batctl -m bat0 interface create
  batctl -m bat0 interface add -M eth0

要分离 eth0 并销毁 bat0：

  batctl -m bat0 interface del -M eth0
  batctl -m bat0 interface destroy

每个 batadv 网状接口、VLAN 和硬接口都有额外的设置，可以使用 batctl 修改。有关详细信息，请参阅其手册。
例如，你可以检查当前的起源者间隔（确定 batman-adv 发送其广播数据包频率的毫秒值）：

  $ batctl -M bat0 orig_interval
  1000

还可以更改该值：

  $ batctl -M bat0 orig_interval 3000

在非常移动的场景下，你可能希望将起源者间隔调整为较低的值。这将使网状网络对拓扑变化更加敏感，但也会增加开销。
有关当前状态的信息可以通过 batadv 泛型 netlink 家族访问。batctl 通过其调试表子命令提供人类可读的版本。
使用
=====

为了利用新创建的网状网络，batman advanced 提供了一个新的接口 "bat0"，你应该从此使用它。所有添加到 batman advanced 的接口都不再相关，因为 batman 会为你处理它们。基本上，通过使用 batman 接口传递数据，batman 会确保数据到达目的地。
"bat0" 接口可以像任何其他常规接口一样使用。它需要一个 IP 地址，该地址可以静态配置或动态获取（通过使用 DHCP 或类似服务）：

  NodeA: ip link set up dev bat0
  NodeA: ip addr add 192.168.0.1/24 dev bat0

  NodeB: ip link set up dev bat0
  NodeB: ip addr add 192.168.0.2/24 dev bat0
  NodeB: ping 192.168.0.1

注意：为了避免问题，请删除先前分配给现在由 batman advanced 使用的接口的所有 IP 地址，例如：

  $ ip addr flush dev eth0

日志记录/调试
=================

所有错误消息、警告和信息消息都会发送到内核日志。根据你的操作系统发行版，你可以通过多种方式阅读它。尝试使用命令：`dmesg`、`logread`，或者查看文件 `/var/log/kern.log` 或 `/var/log/syslog`。所有 batman-adv 消息都以 "batman-adv:" 前缀。所以要只看这些消息，可以尝试：

  $ dmesg | grep batman-adv

在调查网状网络问题时，有时有必要看到更详细的调试消息。这必须在编译 batman-adv 模块时启用。当作为内核的一部分构建 batman-adv 时，使用 "make menuconfig" 并启用选项 `B.A.T.M.A.N. debugging` (`CONFIG_BATMAN_ADV_DEBUG=y`)。
可以通过 perf 架构访问这些额外的调试消息：

  $ trace-cmd stream -e batadv:batadv_dbg

额外的调试输出默认是禁用的。可以在运行时启用它：

  $ batctl -m bat0 loglevel routes tt

这将启用当路由和转发表项发生变化时的调试消息。
可以通过 ethtool 获取不同类型的数据包进入和离开 batman-adv 模块的计数器：

  $ ethtool --statistics bat0

batctl
======

由于 batman advanced 在第二层上运行，所有参与虚拟交换机的主机对于第二层以上的所有协议都是完全透明的。因此，常用的诊断工具不会按预期工作。为了解决这些问题，创建了 batctl。目前，batctl 包含 ping、traceroute、tcpdump 和内核模块设置的接口。
更多信息，请参阅手册页（`man batctl`）。
batctl 可在 https://www.open-mesh.org/ 获取。

联系方式
========

欢迎给我们发送意见、经验、问题等任何反馈：

IRC：
  在 ircs://irc.hackint.org/ 上的 #batadv 频道
邮件列表：
  b.a.t.m.a.n@lists.open-mesh.org （可选订阅地址为 https://lists.open-mesh.org/mailman3/postorius/lists/b.a.t.m.a.n.lists.open-mesh.org/）

您也可以直接联系作者：

* Marek Lindner <mareklindner@neomailbox.ch>
* Simon Wunderlich <sw@simonwunderlich.de>
