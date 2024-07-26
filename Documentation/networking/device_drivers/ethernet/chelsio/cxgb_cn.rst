### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

=============================================
Chelsio N210 10Gb 以太网网络控制器
=============================================

Linux 驱动发布说明

版本 2.1.1

2005年6月20日

.. 目录

简介
特点
性能
驱动消息
已知问题
支持


简介
============

本文档描述了Chelsio 10Gb 以太网网络控制器的Linux驱动。此驱动支持Chelsio N210 网卡，并且与Chelsio N110 型号的10Gb 网卡向后兼容。
特点
========

自适应中断（自适应-rx）
---------------------------------

此功能提供了一种自适应算法，用于调整中断合并参数，使驱动能够动态地调整延迟设置，在不同类型的网络负载下实现最高性能。
用于控制此功能的接口是ethtool。请参阅ethtool的手册页获取更多信息。
默认情况下，自适应-rx被禁用。
要启用自适应-rx，请执行如下命令:

      ethtool -C <接口名> adaptive-rx on

要禁用自适应-rx，请使用ethtool执行如下命令:

      ethtool -C <接口名> adaptive-rx off

禁用自适应-rx之后，计时器延迟值将被设置为50微秒。
您可以在禁用自适应-rx之后设置计时器延迟值:

      ethtool -C <接口名> rx-usecs <微秒数>

例如，将eth0上的计时器延迟值设置为100微秒:

      ethtool -C eth0 rx-usecs 100

您也可以在禁用自适应-rx的同时提供一个计时器延迟值:

      ethtool -C <接口名> adaptive-rx off rx-usecs <微秒数>

如果自适应-rx被禁用并且指定了计时器延迟值，计时器将被设置为指定的值，直到用户更改或重新启用自适应-rx。
要查看自适应-rx的状态和计时器延迟值:

      ethtool -c <接口名>

TCP 分段卸载（TSO）支持
-----------------------------------------

此功能，也称为“大包发送”，允许系统的协议栈将出站TCP处理的部分任务卸载到网络接口卡上，从而减少系统CPU利用率并提高性能。
用于控制此功能的接口是ethtool版本1.8或更高版本。
请参阅ethtool的手册页获取更多信息。
默认情况下，TSO是启用的。
禁用TSO（TCP分段卸载）:

      使用 ethtool -K <interface> tso off

启用TSO（TCP分段卸载）:

      使用 ethtool -K <interface> tso on

查看TSO的状态:

      使用 ethtool -k <interface>

性能
====

以下信息提供了一个示例，说明如何更改系统参数以进行“性能调优”以及使用哪些值。您可能需要或不需要根据您的服务器/工作站应用程序更改这些系统参数。Chelsio Communications 不以任何方式保证这样做，并且这样做风险自负。Chelsio 对数据丢失或设备损坏不负任何责任。
您的发行版可能有其他方法，或者您可能更喜欢其他方法。这些命令仅作为示例提供，并非权威指导。
执行以下任何系统更改都只会持续到您重启系统为止。您可能希望编写一个在启动时运行的脚本，其中包含您系统的最佳设置。
设置PCI延迟计时器:

      使用 setpci -d 1425:: 0x0c.l=0x0000F800

禁用TCP时间戳:

      使用 sysctl -w net.ipv4.tcp_timestamps=0

禁用SACK:

      使用 sysctl -w net.ipv4.tcp_sack=0

设置较大的传入连接请求数量:

      使用 sysctl -w net.ipv4.tcp_max_syn_backlog=3000

设置最大接收套接字缓冲区大小:

      使用 sysctl -w net.core.rmem_max=1024000

设置最大发送套接字缓冲区大小:

      使用 sysctl -w net.core.wmem_max=1024000

将smp_affinity（在多处理器系统上）设置为单个CPU:

      使用 echo 1 > /proc/irq/<中断编号>/smp_affinity

设置默认接收套接字缓冲区大小:

      使用 sysctl -w net.core.rmem_default=524287

设置默认发送套接字缓冲区大小:

      使用 sysctl -w net.core.wmem_default=524287

设置最大选项内存缓冲区:

      使用 sysctl -w net.core.optmem_max=524287

设置最大积压（未处理的数据包之前内核丢弃的数量）:

      使用 sysctl -w net.core.netdev_max_backlog=300000

设置TCP读缓冲区（最小/默认/最大）:

      使用 sysctl -w net.ipv4.tcp_rmem="10000000 10000000 10000000"

设置TCP写缓冲区（最小/压力/最大）:

      使用 sysctl -w net.ipv4.tcp_wmem="10000000 10000000 10000000"

设置TCP缓冲空间（最小/压力/最大）:

      使用 sysctl -w net.ipv4.tcp_mem="10000000 10000000 10000000"

TCP窗口大小对于单一连接：

   接收缓冲区（RX_WINDOW）的大小必须至少与发送者和接收者之间的通信链路的带宽-延迟产品一样大。由于RTT的变化，您可能希望将缓冲区大小增加到带宽-延迟产品的两倍。参考W. Richard Stevens的《TCP/IP详解，第一卷：协议》第289页。
在10Gb速度下，使用以下公式：

       RX_WINDOW >= 1.25MB * RTT(以毫秒为单位)
       例如对于100微秒的RTT: RX_WINDOW = (1,250,000 * 0.1) = 125,000

   RX_WINDOW大小256KB - 512KB应该足够了
设置最小、最大和默认接收缓冲区（RX_WINDOW）大小:

       使用 sysctl -w net.ipv4.tcp_rmem="<min> <default> <max>"

TCP窗口大小对于多个连接：
   接收缓冲区（RX_WINDOW）的大小可以像单一连接一样计算，但应除以连接数。较小的窗口可以防止拥塞并有助于更好地控制速率，特别是在MAC级别流控制工作不佳或不受支持的情况下。可能需要试验来获得正确的值。此方法提供了正确接收缓冲区大小的起点。
设置最小、最大和默认接收缓冲区（RX_WINDOW）大小与单一连接相同。

驱动程序消息
==============

以下是syslog记录中最常见的消息。这些可以在/var/log/messages中找到。
驱动程序已启动:

     Chelsio网络驱动程序 - 版本 2.1.1

检测到的NIC:

     eth#: Chelsio N210 1x10GBaseX NIC (rev #), PCIX 133MHz/64位

链接已建立:

     eth#: 链接已以10 Gbps的速度建立，全双工

链接已断开:

     eth#: 链接已断开

已知问题
========

这些问题是在测试中发现的。以下信息提供了解决问题的方法。在某些情况下，这个问题是Linux或特定Linux发行版及/或硬件平台固有的。
1. 多处理器（SMP）系统上的大量TCP重传
在一个具有多个CPU的系统上，网络控制器的中断（IRQ）可能会绑定到一个以上的CPU。这会导致TCP重传问题，如果数据包被分割并分配给不同的CPU，并以与预期不同的顺序重新组装。

为了消除TCP重传问题，需要将特定中断的`smp_affinity`设置为单一CPU。你可以通过以下命令找到N110/N210上使用的中断（IRQ）：

```bash
ifconfig <dev_name> | grep Interrupt
```

设置`smp_affinity`为单一CPU：

```bash
echo 1 > /proc/irq/<interrupt_number>/smp_affinity
```

强烈建议不要在你的系统上运行`irqbalance`守护进程，因为它会改变你已经应用的任何`smp_affinity`设置。
`irqbalance`守护进程每10秒运行一次，并将中断绑定到由守护程序确定负载最低的CPU。要禁用此守护进程，请执行：

```bash
chkconfig --level 2345 irqbalance off
```

默认情况下，一些Linux发行版启用了内核功能`irqbalance`，其功能与`irqbalance`守护程序相同。要禁用此功能，请在引导加载器中添加以下行：

```bash
noirqbalance
```

例如使用Grub引导加载器：

```bash
title Red Hat Enterprise Linux AS (2.4.21-27.ELsmp)
root (hd0,0)
kernel /vmlinuz-2.4.21-27.ELsmp ro root=/dev/hda3 noirqbalance
initrd /initrd-2.4.21-27.ELsmp.img
```

### 2. 在运行`insmod`后，驱动程序被加载，但错误的网络接口被启动而没有运行`ifup`
在使用2.4.x内核时，包括RHEL内核，Linux内核会调用名为“hotplug”的脚本。此脚本主要用于自动启动插入的USB设备，但是该脚本也会尝试在网络模块加载后自动启动网络接口。`hotplug`脚本通过扫描/etc/sysconfig/network-scripts目录下的ifcfg-eth#配置文件来实现这一点，寻找HWADDR=<mac_address>。

如果`hotplug`脚本未能在任何ifcfg-eth#文件中找到HWADDR，则它将以下一个可用的接口名称启动设备。如果这个接口已经被配置为另一个网络卡，那么你的新接口将有不正确的IP地址和网络设置。

要解决这个问题，可以在网络控制器的接口配置文件中添加HWADDR=<mac_address>键。

要禁用此“hotplug”功能，可以将驱动程序（模块名）添加到位于/etc/hotplug的“黑名单”文件中。需要注意的是，这对于网络设备不起作用，因为net.agent脚本不使用黑名单文件。简单地移除或重命名位于/etc/hotplug中的net.agent脚本来禁用此功能。

### 3. 在基于AMD Opteron的系统上，使用HyperTransport PCI-X Tunnel芯片组，在进行大量多连接流量时传输协议（TP）挂起
如果你的AMD Opteron系统使用了AMD-8131 HyperTransport PCI-X Tunnel芯片组，当你使用133MHz PCI-X卡时，可能会遇到AMD识别出的“133MHz模式分段完成数据损坏”bug。

AMD指出：“在非常特定的情况下，AMD-8131 PCI-X Tunnel可能会向以133MHz运行的PCI-X卡提供过时的数据”，从而导致数据损坏。
AMD提供了此问题的三种解决方法，然而Chelsio建议使用第一种方案以获得最佳性能表现：

对于133MHz的辅助总线操作，请通过BIOS配置编程PCI-X卡来限制事务长度和未决事务的数量如下：

   数据长度（字节）：1K

   允许的最大未决事务数：2

请参阅AMD 8131-HT/PCI-X 错误列表26310 Rev 3.08 2004年8月版，第56节“133MHz模式分割完成数据损坏”以获取更多关于该错误及AMD建议的解决方法的信息。
可能在AMD推荐的PCI-X设置之外进行尝试，例如将数据长度增加到2K字节以提高性能。如果这些设置存在问题，请恢复到“安全”设置并重现问题后再提交错误报告或寻求支持。
.. 注意::

    大多数系统的默认设置是8个未决事务和2K字节的数据长度。
4. 在多处理器系统中，已经注意到处理10Gb网络的应用程序可能会在CPU之间切换，导致性能下降或不稳定。
如果在SMP系统上进行性能测量，建议您运行最新版本的netperf-2.4.0及以上版本或者使用诸如Tim Hockin的procstate工具集（runon）这样的绑定工具：
<http://www.hockin.org/~thockin/procstate/>
将netserver和netperf（或其他应用程序）绑定到特定的CPU会对性能测量产生显著影响。
您可能需要试验将应用程序绑定到哪个CPU才能为您的系统实现最佳性能。
如果您正在开发旨在用于10Gb网络的应用程序，请考虑查看内核函数sched_setaffinity和sched_getaffinity来绑定您的应用程序。
如果您仅运行用户空间的应用程序，如ftp、telnet等，可以尝试使用Tim Hockin提供的procstate工具集中的runon工具。您还可以尝试将接口绑定到特定的CPU：runon 0 ifup eth0

支持
=====

如果您在软件或硬件方面遇到问题，请通过电子邮件联系我们的客户支持团队support@chelsio.com或访问我们的网站http://www.chelsio.com

----------------------------------------------------------------------------------------------

::

Chelsio Communications
370 San Aleso Ave
Suite 100
Sunnyvale, CA 94085
http://www.chelsio.com

本程序是自由软件；您可以根据GNU通用公共许可证（版本2）重新分发和/或修改它，该许可证由自由软件基金会发布。
您应该已随本程序收到GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会，地址为Inc.，59号圣殿街 - 套间330，马萨诸塞州波士顿，邮编02111-1307，美国
本软件按“现状”提供，不附带任何形式的明示或暗示担保，包括但不限于对适销性和适用于特定目的的暗示担保。
版权所有 |copy| 2003-2005 Chelsio Communications。保留所有权利。
