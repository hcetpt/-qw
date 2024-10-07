SPDX 许可证标识符: GPL-2.0

=========================================================
基于 D-Link DL2000 的千兆以太网适配器安装
=========================================================

2002年5月23日

.. 目录

 - 兼容性列表
 - 快速安装
 - 编译驱动程序
 - 安装驱动程序
 - 选项参数
 - 配置脚本示例
 - 故障排除

兼容性列表
==================

适配器支持：

- D-Link DGE-550T 千兆以太网适配器
- D-Link DGE-550SX 千兆以太网适配器
- 基于 D-Link DL2000 的千兆以太网适配器
该驱动支持 Linux 内核 2.4.7 及以上版本。我们在以下环境中进行了测试：
- Red Hat v6.2（更新内核到 2.4.7）
- Red Hat v7.0（更新内核到 2.4.7）
- Red Hat v7.1（内核 2.4.7）
- Red Hat v7.2（内核 2.4.7-10）

快速安装
=============

按照以下命令安装 Linux 驱动程序：

    1. make all
    2. insmod dl2k.ko
    3. ifconfig eth0 up 10.xxx.xxx.xxx netmask 255.0.0.0
			^^^^^^^^^^^^^^^\	    ^^^^^^^^\
					IP		     子网掩码

现在 eth0 应该已经激活，你可以通过“ping”进行测试或使用“ifconfig”获取更多信息。如果测试成功，请继续下一步：
4. ``cp dl2k.ko /lib/modules/`uname -r`/kernel/drivers/net``
5. 在 /etc/modprobe.d/dl2k.conf 中添加以下行：

	alias eth0 dl2k

6. 运行 ``depmod`` 更新模块索引
7. 运行 ``netconfig`` 或 ``netconf`` 创建配置脚本 ifcfg-eth0，位于 /etc/sysconfig/network-scripts 或手动创建它
[参见 - 配置脚本示例]
8. 驱动程序将在下次启动时自动加载和配置

编译驱动程序
====================

在 Linux 中，NIC 驱动程序通常作为可加载模块进行配置。
构建单体（monolithic）内核的方法已过时。尽管可以将驱动程序编译为单体内核的一部分，但这种做法是不推荐的。
本节的剩余部分假设驱动程序是作为一个可加载模块构建的。

在Linux环境中，最好从源代码重新编译驱动程序，而不是依赖预编译版本。这种方法提供了更好的可靠性，因为预编译的驱动程序可能依赖于某些库或内核特性，而这些库或内核特性可能不在特定的Linux安装中存在。

构建Linux设备驱动程序所需的三个文件是dl2k.c、dl2k.h和Makefile。为了编译，Linux安装必须包含gcc编译器、内核源码和内核头文件。该Linux驱动支持2.4.7及更高版本的内核。将文件复制到一个目录，并输入以下命令来编译和链接驱动程序：

CD-ROM驱动
--------------

::

    [root@XXX /] mkdir cdrom
    [root@XXX /] mount -r -t iso9660 -o conv=auto /dev/cdrom /cdrom
    [root@XXX /] cd root
    [root@XXX /root] mkdir dl2k
    [root@XXX /root] cd dl2k
    [root@XXX dl2k] cp /cdrom/linux/dl2k.tgz /root/dl2k
    [root@XXX dl2k] tar xfvz dl2k.tgz
    [root@XXX dl2k] make all

软盘驱动
--------------

::

    [root@XXX /] cd root
    [root@XXX /root] mkdir dl2k
    [root@XXX /root] cd dl2k
    [root@XXX dl2k] mcopy a:/linux/dl2k.tgz /root/dl2k
    [root@XXX dl2k] tar xfvz dl2k.tgz
    [root@XXX dl2k] make all

安装驱动程序
==============

手动安装
--------------

一旦驱动程序被编译完成，它必须被加载、启用并绑定到协议栈以建立网络连接。要加载一个模块，请输入以下命令：

```
insmod dl2k.o
```

或者

```
insmod dl2k.o <可选参数>
```

例如：

```
insmod dl2k.o media=100mbps_hd
```

或者

```
insmod dl2k.o media=3
```

或者

```
insmod dl2k.o media=3,2 ; 对于两张网卡
```

请参考下面列出的Linux设备驱动程序支持的命令行参数列表。
`insmod` 命令只会加载驱动程序并给它分配一个如eth0、eth1等的名字。要使NIC进入工作状态，需要发出以下命令：

```
ifconfig eth0 up
```

最后，要将驱动程序绑定到活动协议（例如Linux中的TCP/IP），请输入以下命令：

```
ifup eth0
```

请注意，这只有在系统能够找到包含必要网络信息的配置脚本时才有意义。下面会给出一个示例。
卸载驱动程序的命令如下：

```
ifdown eth0
ifconfig eth0 down
rmmod dl2k.o
```

以下是列出当前已加载模块和查看当前网络配置的命令：

```
lsmod
ifconfig
```

自动化安装
--------------

本节描述了如何安装驱动程序，使其在启动时自动加载和配置。以下说明基于Red Hat 6.0/7.0发行版，但也可以轻松移植到其他发行版。

Red Hat v6.x/v7.x
-----------------

1. 将dl2k.o复制到网络模块目录，通常为/lib/modules/2.x.x-xx/net 或 /lib/modules/2.x.x/kernel/drivers/net。
2. 定位引导模块配置文件，通常位于/etc/modprobe.d/目录。添加以下行：

   ```
   alias ethx dl2k
   options dl2k <可选参数>
   ```

   其中ethx如果是唯一的以太网适配器，则为eth0；如果有另一个以太网适配器，则为eth1等。请参考上一节中的表来获取可选参数列表。
3. 定位网络配置脚本，通常位于/etc/sysconfig/network-scripts目录，并创建一个名为ifcfg-ethx的配置脚本，其中包含网络信息。
4. 注意对于大多数Linux发行版，包括Red Hat，都提供了一个带有图形用户界面的配置工具来执行上述步骤2和3。

参数描述
============

您可以不使用任何额外参数安装此驱动程序。但是，如果您希望拥有更丰富的功能，则需要设置额外参数。下面是Linux设备驱动程序支持的命令行参数列表。
===============================   ==============================================
mtu=packet_size			  指定最大数据包大小。默认值为1500
media=media_type		  指定网卡运行的媒体类型
autosense	自动检测活动媒体
===========	=========================
				  10mbps_hd	10Mbps半双工
10mbps_fd	10Mbps全双工
100mbps_hd	100Mbps半双工
100mbps_fd	100Mbps全双工
1000mbps_fd	1000Mbps全双工
1000mbps_hd	1000Mbps半双工
0		自动检测活动媒体
1. 10 Mbps 半双工
2. 10 Mbps 全双工
3. 100 Mbps 半双工
4. 100 Mbps 全双工
5. 1000 Mbps 半双工
6. 1000 Mbps 全双工
=========================
默认情况下，网卡以自动感应模式运行
1000Mbps全双工 (fd) 和 1000Mbps半双工 (hd) 类型仅适用于光纤适配器
vlan=n 指定VLAN ID。如果vlan=0，则禁用虚拟局域网（VLAN）功能
jumbo=[0|1] 指定巨型帧支持。如果jumbo=1，则网卡接受巨型帧。默认情况下，此功能是禁用的
巨型帧通常能提高千兆网络的性能。
此功能需要远程设备支持巨型帧。

rx_coalesce=m：每次中断处理的接收帧数
rx_timeout=n：接收DMA等待中断的时间

如果设置 rx_coalesce > 0，硬件仅在接收到 m 帧或达到 n * 640 纳秒的超时时才触发中断。在接收到 m 帧之前，硬件不会触发接收中断。

适当设置 rx_coalesce 和 rx_timeout 可以减少拥塞和过载，这通常是高速网络中的瓶颈。

例如，rx_coalesce=10 rx_timeout=800，即硬件仅在接收到 10 帧或超时 512 微秒时触发一次中断。

tx_coalesce=n：每次中断处理的发送帧数
设置 n > 1 可以减少中断次数，通常会降低高速网卡的性能。默认值为 16。
```tx_flow=[1|0]				指定Tx流控制。如果tx_flow=0，
					  则禁用Tx流控制，否则驱动程序
					  自动检测
rx_flow=[1|0]				指定Rx流控制。如果rx_flow=0，
					  则启用Rx流控制，否则驱动程序
					  自动检测
==================================   =============================================

配置脚本示例
=============
下面是一个简单的配置脚本示例：

    DEVICE=eth0
    USERCTL=no
    ONBOOT=yes
    BOOTPROTO=none
    BROADCAST=207.200.5.255
    NETWORK=207.200.5.0
    NETMASK=255.255.255.0
    IPADDR=207.200.5.2

故障排除
=========
问题1：源文件中的每一行后面都有^ M
确保所有文件都是Unix文件格式（没有LF）。尝试以下shell命令来转换文件：

    cat dl2k.c | col -b > dl2k.tmp
    mv dl2k.tmp dl2k.c

或者：

    cat dl2k.c | tr -d "\r" > dl2k.tmp
    mv dl2k.tmp dl2k.c

问题2：找不到头文件（``*.h``）？

    要编译驱动程序，你需要内核头文件。安装内核源代码后，头文件通常位于/usr/src/linux/include中，这是Makefile中默认配置的包含目录。对于某些发行版，在/usr/src/include/linux和/usr/src/include/asm中有一个头文件副本，你可以将Makefile中的INCLUDEDIR改为/usr/include而不必安装内核源代码。
注意，RH 7.0在/usr/include中未提供正确的头文件，
    包含这些文件会导致生成错误版本的驱动程序。
```
