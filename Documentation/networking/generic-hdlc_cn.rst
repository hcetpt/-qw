SPDX 许可证标识符: GPL-2.0

==================
通用HDLC层
==================

Krzysztof Halasa <khc@pm.waw.pl>

通用HDLC层目前支持：

1. 帧中继（ANSI、CCITT、Cisco 和无LMI）

   - 正常（路由）和以太网桥接（以太网设备仿真）接口可以共享一条PVC
   - ARP支持（内核中没有InARP支持，有一个实验性的InARP用户空间守护进程可供使用，地址为：
     http://www.kernel.org/pub/linux/utils/net/hdlc/）
2. 原始HDLC - 可以是IP（IPv4）接口或以太网设备仿真
3. Cisco HDLC
4. PPP
5. X.25（使用X.25例程）

通用HDLC只是一个协议驱动程序 - 它需要针对特定硬件的低级驱动程序。
使用HDLC或帧中继PVC进行以太网设备仿真是与IEEE 802.1Q（VLAN）和802.1D（以太网桥接）兼容的。
确保加载了hdlc.o和硬件驱动程序。它应该会创建多个“hdlc”（如hdlc0等）网络设备，每个WAN端口一个。您需要“sethdlc”工具，可以从以下地址获取：

	http://www.kernel.org/pub/linux/utils/net/hdlc/

编译sethdlc.c工具：

	gcc -O2 -Wall -o sethdlc sethdlc.c

请确保您正在使用适合您的内核版本的sethdlc。
使用sethdlc来设置物理接口、时钟速率、使用的HDLC模式，并添加任何所需的PVC（如果使用帧中继的话）。
通常您可能需要如下设置：

	sethdlc hdlc0 clock int rate 128000
	sethdlc hdlc0 cisco interval 10 timeout 25

或者：

	sethdlc hdlc0 rs232 clock ext
	sethdlc hdlc0 fr lmi ansi
	sethdlc hdlc0 create 99
	ifconfig hdlc0 up
	ifconfig pvc0 localIP pointopoint remoteIP

在帧中继模式下，在使用PVC设备之前，请先将hdlc主设备设置为up状态（无需分配任何IP地址）。

设置接口：

* v35 | rs232 | x21 | t1 | e1
    - 设置给定端口的物理接口
      如果卡具有软件可选接口
  loopback
    - 激活硬件环回（仅用于测试）
* clock ext
    - RX时钟和TX时钟均为外部
* clock int
    - RX时钟和TX时钟均为内部
* clock txint
    - RX时钟为外部，TX时钟为内部
* clock txfromrx
    - RX时钟为外部，TX时钟从RX时钟导出
* rate
    - 设置时钟速率为bps（仅适用于“int”或“txint”时钟）

设置协议：

* hdlc - 设置原始HDLC（仅IP）模式

  nrz / nrzi / fm-mark / fm-space / manchester - 设置传输码型

  no-parity / crc16 / crc16-pr0（带预置零的CRC16） / crc32-itu

  crc16-itu（带ITU-T多项式的CRC16） / crc16-itu-pr0 - 设置奇偶校验

* hdlc-eth - 使用HDLC的以太网设备仿真。奇偶校验和编码同上
* cisco - 设置Cisco HDLC模式（支持IP、IPv6和IPX）

  interval - 两次保活数据包之间的时间间隔（秒）

  timeout - 收到最后一次保活数据包后认为链路断开的时间（秒）

* ppp - 设置同步PPP模式

* x25 - 设置X.25模式

* fr - 帧中继模式

  lmi ansi / ccitt / cisco / none - LMI（链路管理）类型

  dce - 使用默认DTE（用户端）之外的帧中继DCE（网络端）LMI
这与时钟无关！

- t391 - 链路完整性验证轮询定时器（秒）- 用户
- t392 - 轮询验证定时器（秒）- 网络
- n391 - 完整状态轮询计数器 - 用户
- n392 - 错误阈值 - 用户和网络
- n393 - 监控事件计数 - 用户和网络

帧中继专用：

* create n | delete n - 添加/删除带有DLCI编号n的PVC接口。新创建的接口将命名为pvc0、pvc1等。
* create ether n | delete ether n - 添加一个用于以太网桥接帧的设备。该设备将命名为pvceth0、pvceth1等。

板卡特定问题
--------------

n2.o 和 c101.o 需要参数才能工作：

    insmod n2 hw=io,irq,ram,ports[:io,irq,...]

例如：

    insmod n2 hw=0x300,10,0xD0000,01

或者：

    insmod c101 hw=irq,ram[:irq,...]

例如：

    insmod c101 hw=9,0xdc000

如果这些驱动程序内置于内核中，则需要内核（命令行）参数：

    n2.hw=io,irq,ram,ports:..

或者：

    c101.hw=irq,ram:..

如果您遇到N2、C101或PLX200SYN卡的问题，可以使用“private”命令查看端口的数据包描述符环（在内核日志中）：

    sethdlc hdlc0 private

硬件驱动程序必须使用 #define DEBUG_RINGS 编译。

将这些信息附加到错误报告中会很有帮助。无论如何，请告知我您使用过程中遇到的问题。

获取补丁和其他信息请参阅：
<http://www.kernel.org/pub/linux/utils/net/hdlc/>
