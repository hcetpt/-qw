SPDX 许可证标识符: GPL-2.0

====================================
虚拟路由与转发 (VRF)
====================================

VRF 设备
==============

VRF 设备结合 IP 规则提供了在 Linux 网络堆栈中创建虚拟路由和转发域（通常称为 VRF，具体来说是 VRF-lite）的能力。一个应用场景是多租户问题，在这种情况下每个租户拥有自己的唯一路由表，并且至少需要不同的默认网关。
进程可以通过将套接字绑定到 VRF 设备而成为“VRF 意识”的。通过该套接字的报文将使用与 VRF 设备关联的路由表。VRF 设备实现的一个重要特点是它只影响第三层及以上，因此第二层工具（例如 LLDP）不受影响（即它们不需要在每个 VRF 中运行）。设计还允许使用更高优先级的 IP 规则（基于策略的路由，PBR）优先于 VRF 设备规则，以便按需引导特定流量。
此外，VRF 设备允许 VRF 在命名空间内嵌套。例如网络命名空间在设备层提供网络接口的分离，接口上的 VLAN 提供第二层的分离，然后 VRF 设备提供第三层的分离。

设计
------
VRF 设备与一个关联的路由表一起创建。随后网络接口被绑定到 VRF 设备上，如下图所示：

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

从绑定的设备收到的报文在 IPv4 和 IPv6 处理堆栈中切换到 VRF 设备，给人一种报文流经 VRF 设备的印象。类似地，在出口时，路由规则用于将报文发送到 VRF 设备驱动程序，然后再通过实际接口发送出去。这使得在 VRF 设备上使用 tcpdump 可以捕获进入和离开 VRF 的所有报文。同样，可以使用 VRF 设备应用 netfilter 和 tc 规则，以指定适用于整个 VRF 域的规则。
.. [1] 处于转发状态的报文不会流经设备，因此这些报文不会被 tcpdump 看到。我们将在未来的版本中重新审视这一限制。
.. [2] 入站 iptables 支持 PREROUTING，其中 skb->dev 设置为真实的入站设备；对于 INPUT 和 PREROUTING 规则，skb->dev 都设置为 VRF 设备。对于出站，POSTROUTING 和 OUTPUT 规则可以使用 VRF 设备或真实出站设备编写。

设置
-----
1. 创建 VRF 设备并将其与 FIB 表关联：
例如，
```
ip link add vrf-blue type vrf table 10
ip link set dev vrf-blue up
```

2. 一条 l3mdev FIB 规则将查找定向到与设备关联的表。
对于所有 VRF，一条 l3mdev 规则就足够了。当第一个设备创建时，VRF 设备会为 IPv4 和 IPv6 添加 l3mdev 规则，默认优先级为 1000。用户可以根据需要删除此规则并添加具有不同优先级的规则或安装每个 VRF 的规则。
在 4.8 内核之前，每个 VRF 设备都需要 iif 和 oif 规则：
```
ip ru add oif vrf-blue table 10
ip ru add iif vrf-blue table 10
```

3. 设置表（以及因此 VRF 的默认路由）的默认路由：
```
ip route add table 10 unreachable default metric 4278198272
```

这个较高的度量值确保了不可达的默认路由可以被路由协议套件覆盖。FRRouting 将内核度量解释为组合的管理距离（最高字节）和优先级（较低的三个字节）。因此上述度量值转换为 [255/8192]。
4. 将L3接口绑定到VRF设备:

       使用以下命令将eth1绑定到vrf-blue:

       ip link set dev eth1 master vrf-blue

   当设备被绑定后，其本地和直连路由会自动移至与VRF设备相关的路由表。任何依赖于已绑定设备的其他路由将会被丢弃，并需要重新插入到VRF的FIB表中。
IPv6的sysctl选项keep_addr_on_down可以被启用以保留IPv6全局地址在VRF绑定变化时不变:

       sysctl -w net.ipv6.conf.all.keep_addr_on_down=1

5. 向关联表添加额外的VRF路由:

       使用如下命令添加路由到表10：

       ip route add table 10 ...

应用
-----
需要在VRF内工作的应用程序需要将其套接字绑定到VRF设备上:

    setsockopt(sd, SOL_SOCKET, SO_BINDTODEVICE, dev, strlen(dev)+1);

或者使用cmsg和IP_PKTINFO指定输出设备。
默认情况下，未绑定套接字的端口绑定范围仅限于默认VRF。也就是说，它们不会与绑定到l3mdev的接口收到的数据包匹配，并且进程可以在不同的l3mdev上绑定相同的端口。
运行在默认VRF上下文中的TCP和UDP服务（即，未绑定到任何VRF设备）可以通过启用sysctl选项tcp_l3mdev_accept和udp_l3mdev_accept跨所有VRF域工作:

    sysctl -w net.ipv4.tcp_l3mdev_accept=1
    sysctl -w net.ipv4.udp_l3mdev_accept=1

这些选项默认是禁用的，以便VRF内的套接字仅用于处理该VRF内的数据包。对于RAW套接字也有一个类似的选项，默认是启用的，这是为了向后兼容。
这允许例如旧版本的ping工具在指定设备的同时不在VRF中执行。此选项可以禁用，以便只有绑定到VRF的RAW套接字才能处理VRF上下文中的数据包，并且默认VRF中的数据包只由未绑定到任何VRF的套接字处理:

    sysctl -w net.ipv4.raw_l3mdev_accept=0

可以在VRF设备上的netfilter规则用来限制对运行在默认VRF上下文中的服务的访问。

在使用VRF感知的应用程序（同时在VRF内外创建套接字的应用程序）与设置`net.ipv4.tcp_l3mdev_accept=1`一起时，虽然可行，但在某些情况下可能会导致问题。使用该sysctl值时，处理VRF流量的监听套接字选择是未指定的；也就是说，可能使用绑定到VRF的套接字或未绑定的套接字来接受来自VRF的新连接。这种有些出乎意料的行为可能导致问题，如果套接字配置了额外选项（如TCP MD5密钥），并期望VRF流量仅由绑定到VRF的套接字处理，就像在`net.ipv4.tcp_l3mdev_accept=0`的情况下一样。最后提醒一下，无论选择哪个监听套接字，基于入站接口建立的套接字都会根据前面所述创建在VRF中。

---

使用iproute2管理VRF
=====================
从版本4.7开始，iproute2支持vrf关键字。为保持向后兼容性，这里列出两种命令形式——包含vrf关键字的和较早形式不包含它的。
1. 创建VRF

   实例化VRF设备并将其与表关联起来:

       $ ip link add dev NAME type vrf table ID

   从版本4.8开始，内核支持l3mdev FIB规则，在其中单一规则覆盖所有VRF。l3mdev规则会在首次创建设备时为IPv4和IPv6创建。
2. 列出VRF

   列出已经创建的VRF:

       $ ip [-d] link show type vrf
	 注意：-d选项用于显示表id

   例如:

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


   或者简要输出:

       $ ip -br link show type vrf
       mgmt         UP             72:b3:ba:91:e2:24 <NOARP,MASTER,UP,LOWER_UP>
       red          UP             b6:6f:6e:f6:da:73 <NOARP,MASTER,UP,LOWER_UP>
       blue         UP             36:62:e8:7d:bb:8c <NOARP,MASTER,UP,LOWER_UP>
       green        UP             e6:28:b8:63:70:bb <NOARP,MASTER,UP,LOWER_UP>

3. 将网络接口分配给VRF

   网络接口通过将网卡绑定到VRF设备来分配给VRF:

       $ ip link set dev NAME master NAME

   绑定后，直连和本地路由会自动移动到与VRF设备相关的表中。
1. 将网络接口添加到 VRF 示例命令：

       ```bash
       $ ip link set dev eth0 master mgmt
       ```

4. 显示分配给 VRF 的设备

   要显示已分配给特定 VRF 的设备，需要在 `ip` 命令中加上 `master` 选项：

       ```bash
       $ ip link show vrf NAME
       $ ip link show master NAME
       ```

   例如：

       ```bash
       $ ip link show vrf red
       3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP mode DEFAULT group default qlen 1000
	   link/ether 02:00:00:00:02:02 brd ff:ff:ff:ff:ff:ff
       4: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master red state UP mode DEFAULT group default qlen 1000
	   link/ether 02:00:00:00:02:03 brd ff:ff:ff:ff:ff:ff
       7: eth5: <BROADCAST,MULTICAST> mtu 1500 qdisc noop master red state DOWN mode DEFAULT group default qlen 1000
	   link/ether 02:00:00:00:02:06 brd ff:ff:ff:ff:ff:ff
       ```

   或者使用简短的输出格式：

       ```bash
       $ ip -br link show vrf red
       eth1             UP             02:00:00:00:02:02 <BROADCAST,MULTICAST,UP,LOWER_UP>
       eth2             UP             02:00:00:00:02:03 <BROADCAST,MULTICAST,UP,LOWER_UP>
       eth5             DOWN           02:00:00:00:02:06 <BROADCAST,MULTICAST>
       ```

5. 显示 VRF 的邻接表项

   若要列出与 VRF 设备绑定的设备相关的邻接表项，请在 `ip` 命令中加上 `master` 选项：

       ```bash
       $ ip [-6] neigh show vrf NAME
       $ ip [-6] neigh show master NAME
       ```

   例如：

       ```bash
       $ ip neigh show vrf red
       10.2.1.254 dev eth1 lladdr a6:d9:c7:4f:06:23 REACHABLE
       10.2.2.254 dev eth2 lladdr 5e:54:01:6a:ee:80 REACHABLE

       $ ip -6 neigh show vrf red
       2002:1::64 dev eth1 lladdr a6:d9:c7:4f:06:23 REACHABLE
       ```

6. 显示 VRF 的地址信息

   若要显示与 VRF 关联的接口的地址信息，请在 `ip` 命令中加上 `master` 选项：

       ```bash
       $ ip addr show vrf NAME
       $ ip addr show master NAME
       ```

   例如：

       ```bash
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

   或者以简短格式输出：

       ```bash
       $ ip -br addr show vrf red
       eth1             UP             10.2.1.2/24 2002:1::2/120 fe80::ff:fe00:202/64
       eth2             UP             10.2.2.2/24 2002:2::2/120 fe80::ff:fe00:203/64
       eth5             DOWN
       ```

7. 显示 VRF 的路由信息

   要显示 VRF 的路由信息，使用 `ip` 命令来显示与该 VRF 设备关联的路由表：

       ```bash
       $ ip [-6] route show vrf NAME
       $ ip [-6] route show table ID
       ```

   例如：

       ```bash
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

8. 查找 VRF 中的路由

   可以为 VRF 执行路由查找测试：

       ```bash
       $ ip [-6] route get vrf NAME ADDRESS
       $ ip [-6] route get oif NAME ADDRESS
       ```

   例如：

       ```bash
       $ ip route get 10.2.1.40 vrf red
       10.2.1.40 dev eth1  table red  src 10.2.1.2
           cache

       $ ip -6 route get 2002:1::32 vrf red
       2002:1::32 from :: dev eth1  table red  proto kernel  src 2002:1::2  metric 256  pref medium
       ```

9. 从 VRF 中移除网络接口

   通过解除网络接口与 VRF 设备的绑定关系，可以将其从 VRF 中移除：

       ```bash
       $ ip link set dev NAME nomaster
       ```

   连接的路由将被移回默认表，并且本地条目将被移至本地表。
   
   例如：

       ```bash
       $ ip link set dev eth0 nomaster
       ```

---

本示例中使用的命令：

     ```bash
     cat >> /etc/iproute2/rt_tables.d/vrf.conf <<EOF
     1  mgmt
     10 red
     66 blue
     81 green
     EOF
     ```

     ```bash
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
     ```

     ```bash
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

     来自 `/etc/network/interfaces` 的接口地址配置：
     
     ```bash
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
