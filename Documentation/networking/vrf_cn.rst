SPDX 许可证标识符: GPL-2.0

====================================
虚拟路由和转发（VRF）
====================================

VRF 设备
==============

VRF 设备结合 IP 规则提供了在 Linux 网络栈中创建虚拟路由和转发域（即 VRF，具体为 VRF-lite）的能力。一个应用场景是多租户问题，每个租户都有自己的独立路由表，并且至少需要不同的默认网关。
进程可以通过将套接字绑定到 VRF 设备来实现“VRF 意识”。通过该套接字的数据包将使用与 VRF 设备关联的路由表。VRF 设备实现的一个重要特点是它只影响第三层及以上的功能，因此第二层工具（例如 LLDP）不会受到影响（也就是说它们不需要在每个 VRF 中运行）。设计还允许使用更高优先级的 IP 规则（基于策略的路由，PBR）优先于 VRF 设备规则，从而引导特定流量。
此外，VRF 设备允许 VRF 嵌套在命名空间内。例如，网络命名空间在网络设备层面上提供隔离，接口上的 VLAN 提供第二层隔离，然后 VRF 设备提供第三层隔离。

设计
------
一个 VRF 设备与其关联的路由表一起创建。随后网络接口被绑定到 VRF 设备上：

	 +-----------------------------+
	 |           vrf-blue          |  ====> 路由表 10
	 +-----------------------------+
	    |        |            |
	 +------+ +------+     +-------------+
	 | eth1 | | eth2 | ... |    bond1    |
	 +------+ +------+     +-------------+
				  |       |
			      +------+ +------+
			      | eth8 | | eth9 |
			      +------+ +------+

从绑定设备接收的数据包会被切换到 VRF 设备，在 IPv4 和 IPv6 处理堆栈中，给人一种数据包流经 VRF 设备的印象。同样地，在出口时，路由规则用于将数据包发送到 VRF 设备驱动程序，然后再通过实际接口发送出去。这使得在 VRF 设备上使用 tcpdump 可以捕获进出整个 VRF 的所有数据包\[1\]。类似地，可以使用 VRF 设备应用 netfilter\[2\] 和 tc 规则，指定适用于整个 VRF 域的规则。
\[1\] 转发状态中的数据包不会流经设备，因此这些数据包无法被 tcpdump 捕获。我们将在未来的版本中解决这一限制。
\[2\] 在入口处 iptables 支持 PREROUTING，skb->dev 设置为实际的入口设备，并且支持 INPUT 和 PREROUTING 规则，skb->dev 设置为 VRF 设备。对于出口，POSTROUTING 和 OUTPUT 规则可以使用 VRF 设备或实际出口设备编写。

设置
-----
1. 创建一个与 FIB 表关联的 VRF 设备：
例如：
```
ip link add vrf-blue type vrf table 10
ip link set dev vrf-blue up
```

2. 使用 l3mdev FIB 规则将查找指向与设备关联的表
单个 l3mdev 规则对所有 VRF 都足够。当第一个设备创建时，VRF 设备会为 IPv4 和 IPv6 添加 l3mdev 规则，默认优先级为 1000。用户可以根据需要删除该规则并添加具有不同优先级或每个 VRF 的规则。
在内核版本 4.8 之前，每个 VRF 设备都需要 iif 和 oif 规则：
```
ip ru add oif vrf-blue table 10
ip ru add iif vrf-blue table 10
```

3. 设置表的默认路由（因此也是 VRF 的默认路由）：
```
ip route add table 10 unreachable default metric 4278198272
```
这个高度量值确保了默认不可达路由可以被路由协议套件覆盖。FRRouting 将内核度量解释为组合的管理距离（最高字节）和优先级（最低 3 字节）。因此上述度量值转换为 [255/8192]。
4. 将 L3 接口绑定到 VRF 设备：

       ip link set dev eth1 master vrf-blue

   被绑定的设备的本地和直连路由将自动移动到与 VRF 设备关联的路由表中。任何依赖于被绑定设备的额外路由将被丢弃，并需要在绑定后重新插入到 VRF 的 FIB 表中。
IPv6 的 sysctl 选项 `keep_addr_on_down` 可以启用，以便在 VRF 绑定更改时保留 IPv6 全局地址：

       sysctl -w net.ipv6.conf.all.keep_addr_on_down=1

5. 添加额外的 VRF 路由到关联的路由表：

       ip route add table 10 ..

应用程序
------
在 VRF 中工作的应用程序需要将其套接字绑定到 VRF 设备：

    setsockopt(sd, SOL_SOCKET, SO_BINDTODEVICE, dev, strlen(dev)+1);

或者使用 cmsg 和 IP_PKTINFO 指定输出设备。
默认情况下，未绑定套接字的端口绑定范围仅限于默认 VRF。也就是说，它不会匹配通过 L3MDEV 绑定接口到达的数据包，并且进程可以绑定到同一个 L3MDEV。
运行在默认 VRF 上下文中的 TCP 和 UDP 服务（即，未绑定到任何 VRF 设备）可以通过启用 `tcp_l3mdev_accept` 和 `udp_l3mdev_accept` sysctl 选项跨所有 VRF 域工作：

    sysctl -w net.ipv4.tcp_l3mdev_accept=1
    sysctl -w net.ipv4.udp_l3mdev_accept=1

这些选项默认是禁用的，以便仅选择 VRF 中的套接字来处理 VRF 数据包。对于 RAW 套接字有一个类似选项，默认情况下为了向后兼容而启用。
这是为了使用 cmsg 和 IP_PKTINFO 指定输出设备，但使用未绑定到相应 VRF 的套接字。这允许例如较旧的 ping 实现指定设备但不在 VRF 中执行。此选项可以禁用，以便只有绑定到 VRF 的 RAW 套接字才能处理 VRF 上下文中的数据包，并且默认 VRF 中的数据包只能由未绑定到任何 VRF 的套接字处理：

    sysctl -w net.ipv4.raw_l3mdev_accept=0

可以在 VRF 设备上使用 netfilter 规则来限制对运行在默认 VRF 上下文中的服务的访问。
在启用 `net.ipv4.tcp_l3mdev_accept=1` 的情况下使用 VRF 意识的应用程序（同时在 VRF 内外创建套接字的应用程序）是可能的，但在某些情况下可能会导致问题。在这种 sysctl 设置下，哪个监听套接字将被选中来处理 VRF 流量是未指定的；即，一个绑定到 VRF 的套接字或未绑定的套接字都可能用于接受来自 VRF 的新连接。这种有些出乎意料的行为可能导致问题，如果套接字配置了额外选项（例如 TCP MD5 密钥），并期望 VRF 流量仅由绑定到 VRF 的套接字处理，就像 `net.ipv4.tcp_l3mdev_accept=0` 所做的那样。最后提醒一下，无论选择哪个监听套接字，基于入站接口建立的套接字将在 VRF 中创建，如前所述。

---

使用 iproute2 处理 VRF
======================
从版本 4.7 开始，iproute2 支持 vrf 关键字。为了向后兼容，本节列出了两种命令——带 vrf 关键字的和不带的。
1. 创建 VRF

   要实例化一个 VRF 设备并将其与一个表关联：

       $ ip link add dev NAME type vrf table ID

   从版本 4.8 开始，内核支持 l3mdev FIB 规则，其中单个规则覆盖所有 VRF。在首次创建设备时为 IPv4 和 IPv6 创建 l3mdev 规则。
2. 列出 VRF

   要列出已创建的 VRF：

       $ ip [-d] link show type vrf
       注意：需要 -d 选项才能显示表 ID

   例如：

       $ ip -d link show type vrf
       11: mgmt: <NOARP,MASTER,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
	   link/ether 72:b3:ba:91:e2:24 brd ff:ff:ff:ff:ff:ff promiscuity 0
	   vrf table 1 addrgenmode eui64
       12: red: <NOARP,MASTER,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
	   link/ether b6:6f:6e:f6:da:73 brd ff:ff:ff:ff:ff:ff promiscuity 0
	   vrf table 10 addrgenmode eui64
       13: blue: <NOARP,MASTER,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
	   link/ether 36:62:e8:7d:bb:8c brd ff:ff:ff:ff:ff:ff promiscuity 0
	   vrf table 66 addrgenmode eui64
       14: green: <NOARP,MASTER,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000
	   link/ether e6:28:b8:63:70:bb brd ff:ff:ff:ff:ff:ff promiscuity 0
	   vrf table 81 addrgenmode eui64

   或者简短输出：

       $ ip -br link show type vrf
       mgmt         UP             72:b3:ba:91:e2:24 <NOARP,MASTER,UP,LOWER_UP>
       red          UP             b6:6f:6e:f6:da:73 <NOARP,MASTER,UP,LOWER_UP>
       blue         UP             36:62:e8:7d:bb:8c <NOARP,MASTER,UP,LOWER_UP>
       green        UP             e6:28:b8:63:70:bb <NOARP,MASTER,UP,LOWER_UP>

3. 将网络接口分配给 VRF

   通过将 netdevice 绑定到 VRF 设备来分配网络接口：

       $ ip link set dev NAME master NAME

   在绑定时，直连和本地路由将自动移动到与 VRF 设备关联的表中。
例如：

```shell
$ ip link set dev eth0 master mgmt
```

### 4. 显示分配给 VRF 的设备

要显示已分配给特定 VRF 的设备，可以在 `ip` 命令中添加 `master` 选项：

```shell
$ ip link show vrf NAME
$ ip link show master NAME
```

例如：

```shell
$ ip link show vrf red
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP mode DEFAULT group default qlen 1000
    link/ether 02:00:00:00:02:02 brd ff:ff:ff:ff:ff:ff
4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP mode DEFAULT group default qlen 1000
    link/ether 02:00:00:00:02:03 brd ff:ff:ff:ff:ff:ff
7: eth5: <BROADCAST,MULTICAST> mtu 1500 qdisc noop master red state DOWN mode DEFAULT group default qlen 1000
    link/ether 02:00:00:00:02:06 brd ff:ff:ff:ff:ff:ff
```

或者使用简短输出：

```shell
$ ip -br link show vrf red
eth1             UP             02:00:00:00:02:02 <BROADCAST,MULTICAST,UP,LOWER_UP>
eth2             UP             02:00:00:00:02:03 <BROADCAST,MULTICAST,UP,LOWER_UP>
eth5             DOWN           02:00:00:00:02:06 <BROADCAST,MULTICAST>
```

### 5. 显示 VRF 的邻居条目

要列出与 VRF 设备关联的设备的邻居条目，可以在 `ip` 命令中添加 `master` 选项：

```shell
$ ip [-6] neigh show vrf NAME
$ ip [-6] neigh show master NAME
```

例如：

```shell
$ ip neigh show vrf red
10.2.1.254 dev eth1 lladdr a6:d9:c7:4f:06:23 REACHABLE
10.2.2.254 dev eth2 lladdr 5e:54:01:6a:ee:80 REACHABLE

$ ip -6 neigh show vrf red
2002:1::64 dev eth1 lladdr a6:d9:c7:4f:06:23 REACHABLE
```

### 6. 显示 VRF 的地址

要显示与 VRF 关联的接口的地址，可以在 `ip` 命令中添加 `master` 选项：

```shell
$ ip addr show vrf NAME
$ ip addr show master NAME
```

例如：

```shell
$ ip addr show vrf red
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP group default qlen 1000
    link/ether 02:00:00:00:02:02 brd ff:ff:ff:ff:ff:ff
    inet 10.2.1.2/24 brd 10.2.1.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 2002:1::2/120 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::ff:fe00:202/64 scope link
       valid_lft forever preferred_lft forever
4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP group default qlen 1000
    link/ether 02:00:00:00:02:03 brd ff:ff:ff:ff:ff:ff
    inet 10.2.2.2/24 brd 10.2.2.255 scope global eth2
       valid_lft forever preferred_lft forever
    inet6 2002:2::2/120 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::ff:fe00:203/64 scope link
       valid_lft forever preferred_lft forever
7: eth5: <BROADCAST,MULTICAST> mtu 1500 qdisc noop master red state DOWN group default qlen 1000
    link/ether 02:00:00:00:02:06 brd ff:ff:ff:ff:ff:ff
```

或者在简短格式下：

```shell
$ ip -br addr show vrf red
eth1             UP             10.2.1.2/24 2002:1::2/120 fe80::ff:fe00:202/64
eth2             UP             10.2.2.2/24 2002:2::2/120 fe80::ff:fe00:203/64
eth5             DOWN
```

### 7. 显示 VRF 的路由

要显示 VRF 的路由，可以使用 `ip` 命令来显示与 VRF 设备关联的表：

```shell
$ ip [-6] route show vrf NAME
$ ip [-6] route show table ID
```

例如：

```shell
$ ip route show vrf red
unreachable default  metric 4278198272
broadcast 10.2.1.0 dev eth1  proto kernel  scope link  src 10.2.1.2
10.2.1.0/24 dev eth1  proto kernel  scope link  src 10.2.1.2
local 10.2.1.2 dev eth1  proto kernel  scope host  src 10.2.1.2
broadcast 10.2.1.255 dev eth1  proto kernel  scope link  src 10.2.1.2
broadcast 10.2.2.0 dev eth2  proto kernel  scope link  src 10.2.2.2
10.2.2.0/24 dev eth2  proto kernel  scope link  src 10.2.2.2
local 10.2.2.2 dev eth2  proto kernel  scope host  src 10.2.2.2
broadcast 10.2.2.255 dev eth2  proto kernel  scope link  src 10.2.2.2

$ ip -6 route show vrf red
local 2002:1:: dev lo  proto none  metric 0  pref medium
local 2002:1::2 dev lo  proto none  metric 0  pref medium
2002:1::/120 dev eth1  proto kernel  metric 256  pref medium
local 2002:2:: dev lo  proto none  metric 0  pref medium
local 2002:2::2 dev lo  proto none  metric 0  pref medium
2002:2::/120 dev eth2  proto kernel  metric 256  pref medium
local fe80:: dev lo  proto none  metric 0  pref medium
local fe80:: dev lo  proto none  metric 0  pref medium
local fe80::ff:fe00:202 dev lo  proto none  metric 0  pref medium
local fe80::ff:fe00:203 dev lo  proto none  metric 0  pref medium
fe80::/64 dev eth1  proto kernel  metric 256  pref medium
fe80::/64 dev eth2  proto kernel  metric 256  pref medium
ff00::/8 dev red  metric 256  pref medium
ff00::/8 dev eth1  metric 256  pref medium
ff00::/8 dev eth2  metric 256  pref medium
unreachable default dev lo  metric 4278198272  error -101 pref medium
```

### 8. VRF 路由查找

可以为 VRF 进行路由查找测试：

```shell
$ ip [-6] route get vrf NAME ADDRESS
$ ip [-6] route get oif NAME ADDRESS
```

例如：

```shell
$ ip route get 10.2.1.40 vrf red
10.2.1.40 dev eth1  table red  src 10.2.1.2
    cache

$ ip -6 route get 2002:1::32 vrf red
2002:1::32 from :: dev eth1  table red  proto kernel  src 2002:1::2  metric 256  pref medium
```

### 9. 从 VRF 中移除网络接口

通过解除与 VRF 设备的绑定来将网络接口从 VRF 中移除：

```shell
$ ip link set dev NAME nomaster
```

连接的路由会移动回默认表，本地条目会移动到本地表。

例如：

```shell
$ ip link set dev eth0 nomaster
```

---

此示例中使用的命令：

```shell
cat >> /etc/iproute2/rt_tables.d/vrf.conf <<EOF
1  mgmt
10 red
66 blue
81 green
EOF

function vrf_create
{
    VRF=$1
    TBID=$2

    # 创建 VRF 设备
    ip link add ${VRF} type vrf table ${TBID}

    if [ "${VRF}" != "mgmt" ]; then
        ip route add table ${TBID} unreachable default metric 4278198272
    fi
    ip link set dev ${VRF} up
}

vrf_create mgmt 1
ip link set dev eth0 master mgmt

vrf_create red 10
ip link set dev eth1 master red
ip link set dev eth2 master red
ip link set dev eth5 master red

vrf_create blue 66
ip link set dev eth3 master blue

vrf_create green 81
ip link set dev eth4 master green
```

来自 `/etc/network/interfaces` 的接口地址：

```shell
auto eth0
iface eth0 inet static
   address 10.0.0.2
   netmask 255.255.255.0
   gateway 10.0.0.254

iface eth0 inet6 static
   address 2000:1::2
   netmask 120

auto eth1
iface eth1 inet static
   address 10.2.1.2
   netmask 255.255.255.0

iface eth1 inet6 static
   address 2002:1::2
   netmask 120

auto eth2
iface eth2 inet static
   address 10.2.2.2
   netmask 255.255.255.0

iface eth2 inet6 static
   address 2002:2::2
   netmask 120

auto eth3
iface eth3 inet static
   address 10.2.3.2
   netmask 255.255.255.0

iface eth3 inet6 static
   address 2002:3::2
   netmask 120

auto eth4
iface eth4 inet static
   address 10.2.4.2
   netmask 255.255.255.0

iface eth4 inet6 static
   address 2002:4::2
   netmask 120
```
