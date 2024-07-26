SPDX 许可证标识符: GPL-2.0

==================
通用HDLC层
==================

克日什托夫·哈拉萨 <khc@pm.waw.pl>

当前，通用HDLC层支持：

1. 帧中继（ANSI、CCITT、Cisco和无LMI）

   - 正常（路由）和以太网桥接（以太网设备仿真）接口可以共享一条PVC
- ARP支持（内核中没有InARP支持 — 在以下位置提供了一个实验性的InARP用户空间守护进程：
     http://www.kernel.org/pub/linux/utils/net/hdlc/）
2. 原始HDLC —— 可以是IP（IPv4）接口或以太网设备仿真
3. Cisco HDLC
4. PPP
5. X.25（使用X.25例程）

通用HDLC仅是一个协议驱动程序 —— 它需要为您的特定硬件提供低级驱动程序。
以太网设备仿真（使用HDLC或帧中继PVC）与IEEE 802.1Q（VLAN）和802.1D（以太网桥接）兼容。
请确保已加载hdlc.o和硬件驱动程序。它应该会创建多个“hdlc”（如hdlc0等）网络设备，每个WAN端口一个。您需要“sethdlc”工具，可以从以下位置获取：

	http://www.kernel.org/pub/linux/utils/net/hdlc/

编译sethdlc.c工具：

	gcc -O2 -Wall -o sethdlc sethdlc.c

请确保您使用的sethdlc版本与您的内核版本匹配。
使用sethdlc设置物理接口、时钟速率、使用的HDLC模式，并在使用帧中继时添加任何所需的PVC。
通常，您可能需要执行如下操作：

	sethdlc hdlc0 clock int rate 128000
	sethdlc hdlc0 cisco interval 10 timeout 25

或者：

	sethdlc hdlc0 rs232 clock ext
	sethdlc hdlc0 fr lmi ansi
	sethdlc hdlc0 create 99
	ifconfig hdlc0 up
	ifconfig pvc0 localIP pointopoint remoteIP

在帧中继模式下，在使用PVC设备之前，请先将hdlc设备配置为up状态（无需分配任何IP地址）。
设置接口：

* v35 | rs232 | x21 | t1 | e1
    - 设置给定端口的物理接口
      如果该卡具有软件可选择的接口
  loopback
    - 激活硬件环回（仅用于测试）
* clock ext
    - RX时钟和TX时钟均为外部
* clock int
    - RX时钟和TX时钟均为内部
* clock txint
    - RX时钟为外部，TX时钟为内部
* clock txfromrx
    - RX时钟为外部，TX时钟由RX时钟产生
* rate
    - 设置时钟速率（bps），仅适用于“int”或“txint”时钟


设置协议：

* hdlc - 设置原始HDLC（仅IP）模式

  nrz / nrzi / fm-mark / fm-space / manchester - 设置传输编码

  no-parity / crc16 / crc16-pr0（带有预设零的CRC16） / crc32-itu

  crc16-itu（使用ITU-T多项式的CRC16） / crc16-itu-pr0 - 设置奇偶校验

* hdlc-eth - 使用HDLC进行以太网设备仿真。奇偶校验和编码同上
* cisco - 设置Cisco HDLC模式（支持IP、IPv6和IPX）

  interval - 保持活动数据包之间的时间间隔（秒）

  timeout - 最后收到保持活动数据包之后，我们假设链路中断之前的时间（秒）

* ppp - 设置同步PPP模式

* x25 - 设置X.25模式

* fr - 帧中继模式

  lmi ansi / ccitt / cisco / none - LMI（链路管理）类型

  dce - 帧中继DCE（网络）侧LMI，而非默认的DTE（用户）
这段文本涉及网络配置和技术细节，下面是翻译后的中文版本：

这与时钟无关！

- t391 - 链路完整性验证轮询定时器（秒）- 用户
- t392 - 轮询验证定时器（秒）- 网络
- n391 - 完整状态轮询计数器 - 用户
- n392 - 错误阈值 - 用户和网络
- n393 - 监控事件计数 - 用户和网络

仅适用于帧中继：

* 创建 n | 删除 n - 添加/删除具有DLCI编号为n的PVC接口。新创建的接口将被命名为pvc0、pvc1等。
* 创建 ether n | 删除 ether n - 添加一个用于以太网桥接帧的设备。该设备将被命名为pvceth0、pvceth1等。

特定于板卡的问题
------------------

n2.o 和 c101.o 需要参数才能工作：

    insmod n2 hw=io,irq,ram,ports[:io,irq,...]

示例：

    insmod n2 hw=0x300,10,0xD0000,01

或者：

    insmod c101 hw=irq,ram[:irq,...]

示例：

    insmod c101 hw=9,0xdc000

如果这些驱动程序被编译到内核中，则需要在内核命令行参数中指定：

    n2.hw=io,irq,ram,ports:..

或：

    c101.hw=irq,ram:..

如果你遇到关于N2、C101或PLX200SYN卡的问题，可以使用 "private" 命令来查看端口的数据包描述符环（在内核日志中）：

    sethdlc hdlc0 private

硬件驱动程序必须用 `#define DEBUG_RINGS` 编译。
将这些信息附加到错误报告中会很有帮助。无论如何，请告诉我你在使用过程中遇到的问题。
有关补丁和其他信息，请参阅：
<http://www.kernel.org/pub/linux/utils/net/hdlc/>
