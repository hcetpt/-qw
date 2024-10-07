SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

=============================================
Chelsio N210 10Gb 以太网网络控制器
=============================================

Linux 驱动程序发布说明

版本 2.1.1

2005年6月20日

.. 目录

简介
特点
性能
驱动程序消息
已知问题
支持

简介
============

本文档描述了适用于 Chelsio 10Gb 以太网网络控制器的 Linux 驱动程序。该驱动程序支持 Chelsio N210 网卡，并且向后兼容 Chelsio N110 型号的 10Gb 网卡。

特点
========

自适应中断（adaptive-rx）
---------------------------------

此功能提供了一种自适应算法，用于调整中断聚合参数，使驱动程序能够根据不同的网络负载动态调整延迟设置，从而在各种类型的网络负载下实现最高性能。
用于控制此功能的接口是 ethtool。请参阅 ethtool 的手册页获取更多使用信息。
默认情况下，adaptive-rx 是禁用的。
要启用 adaptive-rx，请执行以下命令：

```
ethtool -C <interface> adaptive-rx on
```

要禁用 adaptive-rx，请使用 ethtool 执行以下命令：

```
ethtool -C <interface> adaptive-rx off
```

禁用 adaptive-rx 后，定时器延迟值将被设置为 50 微秒。
您可以在禁用 adaptive-rx 后设置定时器延迟值：

```
ethtool -C <interface> rx-usecs <microseconds>
```

例如，在 eth0 上将定时器延迟值设置为 100 微秒：

```
ethtool -C eth0 rx-usecs 100
```

您也可以在禁用 adaptive-rx 时提供一个定时器延迟值：

```
ethtool -C <interface> adaptive-rx off rx-usecs <microseconds>
```

如果禁用了 adaptive-rx 并指定了定时器延迟值，则定时器将被设置为指定的值，直到用户更改或重新启用 adaptive-rx。
要查看 adaptive-rx 的状态和定时器延迟值，请执行以下命令：

```
ethtool -c <interface>
```

TCP 分段卸载（TSO）支持
-----------------------------------------

此功能，也称为“大包发送”，使得系统的协议栈可以将出站 TCP 处理的部分任务卸载到网络接口卡上，从而减少系统 CPU 利用率并提高性能。
用于控制此功能的接口是 ethtool 版本 1.8 或更高版本。
请参阅 ethtool 的手册页获取更多使用信息。
默认情况下，TSO 是启用的。
### 禁用TSO：

```
ethtool -K <interface> tso off
```

### 启用TSO：

```
ethtool -K <interface> tso on
```

### 查看TSO状态：

```
ethtool -k <interface>
```

### 性能
####

以下信息提供了一个示例，说明如何更改系统参数以进行“性能调优”以及使用哪些值。您可能需要或不需要更改这些系统参数，这取决于您的服务器/工作站应用程序。Chelsio Communications 不保证这样做，并且这样做是“您自担风险”。Chelsio 对数据丢失或设备损坏不承担任何责任。
您的发行版可能有不同的方法，或者您可能更喜欢其他方法。这些命令仅作为示例提供，并非绝对的。
进行任何以下系统更改都只会持续到您重新启动系统为止。您可能希望编写一个在启动时运行的脚本，其中包含您系统的最佳设置。

#### 设置PCI延迟计时器：

```
setpci -d 1425::0x0c.l=0x0000F800
```

#### 禁用TCP时间戳：

```
sysctl -w net.ipv4.tcp_timestamps=0
```

#### 禁用SACK：

```
sysctl -w net.ipv4.tcp_sack=0
```

#### 设置大量传入连接请求：

```
sysctl -w net.ipv4.tcp_max_syn_backlog=3000
```

#### 设置最大接收套接字缓冲区大小：

```
sysctl -w net.core.rmem_max=1024000
```

#### 设置最大发送套接字缓冲区大小：

```
sysctl -w net.core.wmem_max=1024000
```

#### 将smp_affinity（在多处理器系统上）设置为单个CPU：

```
echo 1 > /proc/irq/<中断编号>/smp_affinity
```

#### 设置默认接收套接字缓冲区大小：

```
sysctl -w net.core.rmem_default=524287
```

#### 设置默认发送套接字缓冲区大小：

```
sysctl -w net.core.wmem_default=524287
```

#### 设置最大选项内存缓冲区：

```
sysctl -w net.core.optmem_max=524287
```

#### 设置最大积压（未处理的数据包数之前内核丢弃）：

```
sysctl -w net.core.netdev_max_backlog=300000
```

#### 设置TCP读缓冲区（最小/默认/最大）：

```
sysctl -w net.ipv4.tcp_rmem="10000000 10000000 10000000"
```

#### 设置TCP写缓冲区（最小/压力/最大）：

```
sysctl -w net.ipv4.tcp_wmem="10000000 10000000 10000000"
```

#### 设置TCP缓冲空间（最小/压力/最大）：

```
sysctl -w net.ipv4.tcp_mem="10000000 10000000 10000000"
```

#### 单个连接的TCP窗口大小：

接收缓冲区（RX_WINDOW）大小必须至少等于发送方和接收方之间通信链路的带宽-延迟乘积。由于RTT的变化，您可能希望将缓冲区大小增加到带宽-延迟乘积的两倍。参考W. Richard Stevens所著的《TCP/IP详解卷1：协议》第289页。
在10Gb速度下，使用以下公式：

```
RX_WINDOW >= 1.25MBytes * RTT(毫秒)
例如RTT为100微秒：RX_WINDOW = (1,250,000 * 0.1) = 125,000
```

256KB至512KB的RX_WINDOW大小应该足够了。
设置最小、最大和默认接收缓冲区（RX_WINDOW）大小：

```
sysctl -w net.ipv4.tcp_rmem="<最小> <默认> <最大>"
```

#### 多个连接的TCP窗口大小：
接收缓冲区（RX_WINDOW）大小可以像单个连接一样计算，但应除以连接数量。较小的窗口可防止拥塞并更好地控制速率，尤其是在MAC级别流控不起作用或不受支持的情况下。可能需要实验来获得正确的值。此方法作为正确接收缓冲区大小的起点提供。
设置最小、最大和默认接收缓冲区（RX_WINDOW）大小的方式与单个连接相同。

### 驱动程序消息
####

以下消息是最常见的日志消息，可以在 `/var/log/messages` 中找到。
驱动程序启动：

```
Chelsio Network Driver - 版本 2.1.1
```

NIC 检测到：

```
eth#: Chelsio N210 1x10GBaseX NIC (版本#)，PCIX 133MHz/64位
```

链路激活：

```
eth#: 链路已激活，10 Gbps，全双工
```

链路断开：

```
eth#: 链路已断开
```

### 已知问题
####

这些问题是在测试过程中发现的。以下信息提供了问题的解决方法。在某些情况下，这个问题是Linux本身或特定Linux发行版和/或硬件平台固有的。
1. 在多处理器（SMP）系统中出现大量的TCP重传
在具有多个CPU的系统上，网络控制器的中断（IRQ）可能会绑定到一个以上的CPU。这将导致如果数据包被拆分到不同的CPU上并在与预期不同的顺序中重新组装时出现TCP重传。

为了消除TCP重传，请将特定中断的`smp_affinity`设置为单个CPU。您可以通过使用`ifconfig`命令来找到N110/N210上使用的中断（IRQ）：

```
ifconfig <dev_name> | grep Interrupt
```

将`smp_affinity`设置为单个CPU：
```
echo 1 > /proc/irq/<interrupt_number>/smp_affinity
```

强烈建议不要在您的系统上运行`irqbalance`守护进程，因为这会更改您已应用的任何`smp_affinity`设置。`irqbalance`守护程序每10秒运行一次，并将中断绑定到由守护程序确定的负载最少的CPU。要禁用此守护程序，请执行以下操作：
```
chkconfig --level 2345 irqbalance off
```

默认情况下，某些Linux发行版启用了内核功能`irqbalance`，其功能与`irqbalance`守护程序相同。要禁用此功能，请在引导加载程序中添加以下行：
```
noirqbalance
```

例如，使用Grub引导加载程序：
```
title Red Hat Enterprise Linux AS (2.4.21-27.ELsmp)
root (hd0,0)
kernel /vmlinuz-2.4.21-27.ELsmp ro root=/dev/hda3 noirqbalance
initrd /initrd-2.4.21-27.ELsmp.img
```

2. 在运行`insmod`之后，驱动程序被加载，但错误的网络接口被激活而没有运行`ifup`
当使用2.4.x内核（包括RHEL内核）时，Linux内核会调用一个名为“hotplug”的脚本。这个脚本主要用于在插入USB设备时自动将其激活，然而，该脚本还会在加载内核模块后尝试自动激活网络接口。hotplug脚本通过扫描`/etc/sysconfig/network-scripts`目录下的`ifcfg-eth#`配置文件来查找`HWADDR=<mac_address>`。

如果hotplug脚本在任何`ifcfg-eth#`文件中找不到`HWADDR`，它将以下一个可用的接口名称激活设备。如果此接口已经为其他网络卡配置，则新的接口将具有不正确的IP地址和网络设置。

要解决此问题，可以在网络控制器的接口配置文件中添加`HWADDR=<mac_address>`键。

要禁用此“hotplug”功能，可以将驱动程序（模块名称）添加到位于`/etc/hotplug`中的“黑名单”文件中。需要注意的是，这种方法对网络设备不起作用，因为`net.agent`脚本不使用黑名单文件。只需移除或重命名位于`/etc/hotplug`目录下的`net.agent`脚本来禁用此功能。

3. 在AMD Opteron系统上带有HyperTransport PCI-X Tunnel芯片组的情况下，在进行大量多连接流量传输时传输协议（TP）挂起
如果您的AMD Opteron系统使用了AMD-8131 HyperTransport PCI-X Tunnel芯片组，您可能会遇到使用133MHz PCI-X卡时AMD识别出的“133-Mhz Mode Split Completion Data Corruption”错误。

AMD表示，“在非常特定的条件下，AMD-8131 PCI-X Tunnel可以通过拆分完成周期向以133 MHz运行的PCI-X卡提供陈旧数据”，从而导致数据损坏。
AMD提供了三种解决此问题的方法，然而Chelsio推荐第一种选项以获得最佳性能：

对于133MHz的二级总线操作，请通过BIOS配置编程PCI-X卡，将事务长度和未完成事务的数量限制如下：

数据长度（字节）：1k

允许的最大未完成事务数：2

请参阅AMD 8131-HT/PCI-X 错误报告 26310 Rev 3.08 2004年8月，第56节，“133-MHz模式分割完成数据损坏”，以获取更多关于此错误及其建议的解决方法的信息。

可能在AMD推荐的PCI-X设置之外进行尝试，例如增加数据长度至2k字节以提高性能。如果您使用这些设置遇到问题，请恢复到“安全”设置，并在提交错误报告或请求支持之前重现该问题。
.. 注意::

    大多数系统的默认设置是8个未完成事务和2k字节的数据长度。
4. 在多处理器系统中，已经注意到处理10Gb网络的应用程序可能会在CPU之间切换，导致性能下降和/或不稳定。
如果在SMP系统上进行性能测量，建议您运行最新版本的netperf-2.4.0+或使用诸如Tim Hockin的procstate工具（如runon）进行绑定
<http://www.hockin.org/~thockin/procstate/>
将netserver和netperf（或其他应用程序）绑定到特定的CPU会对性能测量产生显著影响。
您可能需要实验性地确定将应用程序绑定到哪个CPU以实现系统最佳性能。
如果您正在开发设计用于10Gb网络的应用程序，请考虑查看内核函数sched_setaffinity与sched_getaffinity来绑定您的应用程序。
如果您只是运行用户空间的应用程序如ftp、telnet等，您可以尝试使用Tim Hockin提供的procstate工具中的runon工具。您也可以尝试将接口绑定到特定的CPU：runon 0 ifup eth0。

支持
====

如果您在软件或硬件方面遇到问题，请通过电子邮件联系我们的客户支持团队support@chelsio.com或访问我们的网站http://www.chelsio.com

----------------------------------------------------------------------------------------------

::

Chelsio Communications
370 San Aleso Ave
Suite 100
Sunnyvale, CA 94085
http://www.chelsio.com

本程序为自由软件；您可以根据GNU通用公共许可证第2版重新分发或修改它，该许可证由自由软件基金会发布。
您应该已随本程序收到一份 GNU 通用公共许可证；如果没有，请写信至自由软件基金会，地址如下：
自由软件基金会（Free Software Foundation, Inc.）
59 Temple Place - Suite 330
波士顿，马萨诸塞州 02111-1307
美国

本软件按“现状”提供，没有任何明示或暗示的保证，包括但不限于适销性和适用于特定目的的隐含保证。

版权所有 © 2003-2005 Chelsio Communications。保留所有权利。
