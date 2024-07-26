SPDX 许可证标识符: GPL-2.0

=========================================================
基于 D-Link DL2000 的千兆以太网适配器安装指南
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
该驱动程序支持从 Linux 内核 2.4.7 及以后的版本。我们已经在以下环境中进行了测试：
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

现在 eth0 应该处于激活状态，你可以通过“ping”来测试它或者使用“ifconfig”获取更多信息。如果测试成功，继续下一步：
4. `cp dl2k.ko /lib/modules/`uname -r`/kernel/drivers/net``
5. 在 /etc/modprobe.d/dl2k.conf 中添加以下行：

	alias eth0 dl2k

6. 运行 `depmod` 来更新模块索引
7. 运行 `netconfig` 或 `netconf` 来创建配置脚本 ifcfg-eth0，该脚本位于 /etc/sysconfig/network-scripts 目录下，或者手动创建它
[参见 - 配置脚本示例]
8. 下次启动时，驱动程序将自动加载并配置好

编译驱动程序
====================
在 Linux 中，网络接口卡 (NIC) 驱动程序最常见的是作为可加载模块进行配置
构建单体式内核的方法已经过时。虽然可以将驱动程序编译为单体式内核的一部分，但这种做法是不被推荐的
本节的剩余部分假设驱动程序是作为可加载模块构建的。
在 Linux 环境中，从源代码重新编译驱动程序而不是依赖预编译版本是个好主意。这种方法提供了更好的可靠性，因为预编译的驱动程序可能依赖于库或内核特性，而这些特性在给定的 Linux 安装中可能并不存在。
构建 Linux 设备驱动程序所需的三个文件是 dl2k.c、dl2k.h 和 Makefile。为了进行编译，Linux 安装必须包括 gcc 编译器、内核源码和内核头文件。Linux 驱动程序支持 2.4.7 版本的 Linux 内核。将文件复制到一个目录，并输入以下命令来编译和链接驱动程序：

**CD-ROM 驱动**
---------------

```
[root@XXX /] mkdir cdrom
[root@XXX /] mount -r -t iso9660 -o conv=auto /dev/cdrom /cdrom
[root@XXX /] cd root
[root@XXX /root] mkdir dl2k
[root@XXX /root] cd dl2k
[root@XXX dl2k] cp /cdrom/linux/dl2k.tgz /root/dl2k
[root@XXX dl2k] tar xfvz dl2k.tgz
[root@XXX dl2k] make all
```

**软盘驱动**
-------------

```
[root@XXX /] cd root
[root@XXX /root] mkdir dl2k
[root@XXX /root] cd dl2k
[root@XXX dl2k] mcopy a:/linux/dl2k.tgz /root/dl2k
[root@XXX dl2k] tar xfvz dl2k.tgz
[root@XXX dl2k] make all
```

**安装驱动程序**

**手动安装**
--------------

一旦驱动程序被编译完成，就必须将其加载、启用并与协议栈绑定以建立网络连接。要加载一个模块，请输入以下命令：
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
请参考下面列出的由 Linux 设备驱动程序支持的命令行参数列表。
`insmod` 命令仅加载驱动程序并为其分配如 `eth0`, `eth1` 等形式的名称。为了使 NIC 进入操作状态，需要发出以下命令：
```
ifconfig eth0 up
```
最后，为了将驱动程序绑定到活动协议（例如，在 Linux 中为 TCP/IP），请输入以下命令：
```
ifup eth0
```
请注意，只有当系统能够找到包含必要网络信息的配置脚本时，这才有意义。下一段会给出一个示例。
卸载驱动程序的命令如下：
```
ifdown eth0
ifconfig eth0 down
rmmod dl2k.o
```
以下是列出当前已加载模块以及查看当前网络配置的命令：
```
lsmod
ifconfig
```

**自动化安装**
----------------
本节描述了如何安装驱动程序，以便它在启动时自动加载和配置。以下描述基于 Red Hat 6.0/7.0 发行版，但也可以轻松移植到其他发行版。

**Red Hat v6.x/v7.x**
---------------------
1. 将 `dl2k.o` 复制到网络模块目录，通常是 `/lib/modules/2.x.x-xx/net` 或 `/lib/modules/2.x.x/kernel/drivers/net`。
2. 找到引导模块配置文件，通常位于 `/etc/modprobe.d/` 目录。添加以下行：
   ```
   alias ethx dl2k
   options dl2k <可选参数>
   ```
   其中 `ethx` 如果 NIC 是唯一的以太网适配器，则将是 `eth0`；如果已经安装了一个其他的以太网适配器，则将是 `eth1` 等等。参考上一节中的表格获取可选参数列表。
3. 找到网络配置脚本，通常位于 `/etc/sysconfig/network-scripts` 目录，并创建一个名为 `ifcfg-ethx` 的配置脚本，其中包含网络信息。
4. 注意对于大多数 Linux 发行版（包括 Red Hat），提供了一个具有图形用户界面的配置工具来执行上述第 2 步和第 3 步。

**参数说明**
------------
您可以无需任何额外参数安装此驱动程序。但是，如果您想要使用更高级的功能，则需要设置额外的参数。下面是 Linux 设备驱动程序支持的命令行参数列表。
mtu=packet_size          指定最大数据包大小。默认值为1500。
media=media_type         指定网卡运行的媒体类型。
autosense               自动感应活动媒体
=================     ===========================
                      10mbps_hd    10Mbps半双工
10mbps_fd    10Mbps全双工
100mbps_hd   100Mbps半双工
100mbps_fd   100Mbps全双工
1000mbps_fd  1000Mbps全双工
1000mbps_hd  1000Mbps半双工
0            自动感应活动媒体
1.	10 Mbps 半双工
2.	10 Mbps 全双工
3.	100 Mbps 半双工
4.	100 Mbps 全双工
5.	1000 Mbps 半双工
6.	1000 Mbps 全双工
==========	====================================

默认情况下，网卡以自动感应模式运行。
1000Mbps_fd 和 1000Mbps_hd 类型仅
适用于光纤适配器。
vlan=n		指定VLAN ID。如果vlan=0，则
虚拟局域网（VLAN）功能被
禁用。
jumbo=[0|1]	指定巨型帧支持。如果jumbo=1，
则网卡接受巨型帧。默认情况下，此
功能处于禁用状态。
巨型帧（Jumbo frame）通常能提升千兆网络接口的性能。此特性需要远程设备支持巨型帧。

`rx_coalesce=m` 指的是每个中断处理的接收帧的数量。
`rx_timeout=n` 是指接收DMA等待中断的时间。

如果设置 `rx_coalesce > 0`，硬件仅在接收到m个帧或达到n * 640纳秒的超时时间后才产生一个中断。硬件不会在接收到m个帧之前产生接收中断。

适当设置 `rx_coalesce` 和 `rx_timeout` 可以减少拥塞崩溃和过载问题，这些问题通常是高速网络的一个瓶颈。

例如，设置 `rx_coalesce=10` 和 `rx_timeout=800`，意味着硬件仅对接收到的10个帧或512微秒的超时时间产生一个中断。

`tx_coalesce=n` 指的是每个中断处理的发送帧的数量。
设置 `n > 1` 可以减少中断，通常这会降低高速网卡的性能。默认值为16。
### 配置说明

`tx_flow=[1|0]` 指定发送（Tx）流控制。如果 `tx_flow=0`，则禁用发送流控制；否则，驱动程序自动检测。

`rx_flow=[1|0]` 指定接收（Rx）流控制。如果 `rx_flow=0`，则启用接收流控制；否则，驱动程序自动检测。

### 配置脚本示例
以下是一个简单的配置脚本示例：

```sh
DEVICE=eth0
USERCTL=no
ONBOOT=yes
POOTPROTO=none
BROADCAST=207.200.5.255
NETWORK=207.200.5.0
NETMASK=255.255.255.0
IPADDR=207.200.5.2
```

### 故障排除

**问题1：** 源文件中的每一行后面都含有 `^M`。
确保所有文件都是 Unix 文件格式（没有回车换行符 LF）。可以尝试使用以下 shell 命令来转换文件：

```sh
cat dl2k.c | col -b > dl2k.tmp
mv dl2k.tmp dl2k.c
```

或者：

```sh
cat dl2k.c | tr -d "\r" > dl2k.tmp
mv dl2k.tmp dl2k.c
```

**问题2：** 找不到头文件（`*.h`）？

为了编译驱动程序，你需要内核的头文件。在安装了内核源码后，这些头文件通常位于 `/usr/src/linux/include`，这是在 Makefile 中默认设置的包含目录。对于某些发行版，会在 `/usr/src/include/linux` 和 `/usr/src/include/asm` 中有一个头文件的副本，这时你可以将 Makefile 中的 `INCLUDEDIR` 设置为 `/usr/include` 而无需安装内核源码。需要注意的是，RH 7.0 在 `/usr/include` 中提供的头文件并不正确，包含这些文件会导致编译出错误版本的驱动程序。
