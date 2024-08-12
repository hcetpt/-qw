USB3 调试端口
=============

:作者: 卢宝璐 <baolu.lu@linux.intel.com>
:日期: 2017年3月

概述
=====

这是一个关于如何在 x86 系统上使用 USB3 调试端口的指南。
在使用基于 USB3 调试端口的任何内核调试功能之前，您需要:

    1) 检查您的系统中是否有可用的 USB3 调试端口；
    2) 确定哪个端口用于调试目的；
    3) 准备一根 USB 3.0 超高速 A-to-A 调试线缆。

介绍
=====

xHCI 调试能力 (DbC) 是 xHCI 主控制器提供的一个可选但独立的功能。xHCI 规范在第 7.6 节描述了 DbC。
当 DbC 初始化并启用时，它将通过调试端口（通常是第一个 USB3 超速端口）呈现一个调试设备。该调试设备完全符合 USB 框架，并在调试目标（被调试的系统）和调试主机之间提供相当于非常高速的全双工串行连接。

早期 printk
===========

DbC 设计用于记录早期 printk 消息。此功能的一个用途是内核调试。例如，当您的机器在常规控制台代码初始化之前很早就崩溃了。
其他用途包括更简单的、无锁的记录，而不是一个完整的 printk 控制台驱动程序和 klogd。
在调试目标系统上，您需要定制一个启用了 CONFIG_EARLY_PRINTK_USB_XDBC 的调试内核。并且，添加以下内核启动参数:

    "earlyprintk=xdbc"

如果您的系统中有多个 xHCI 控制器，您可以在该内核参数后附加一个主控制器索引。这个索引从 0 开始。
当前设计不支持 DbC 运行时挂起/恢复。因此，最好通过添加以下内核启动参数来禁用 USB 子系统的运行时电源管理:

    "usbcore.autosuspend=-1"

在启动调试目标之前，您应该将调试端口连接到调试主机上的 USB 端口（根端口或任何外部集线器的端口）。用于连接这两个端口的线缆应该是 USB 3.0 超速 A-to-A 调试线缆。
在调试目标早期引导期间，DbC 将被检测和初始化。初始化后，调试主机应该能够枚举调试目标中的调试设备。调试主机随后将调试设备与 usb_debug 驱动模块绑定，并创建 /dev/ttyUSB 设备。
如果调试设备枚举过程顺利进行，您应该能够在调试主机上看到以下内核消息:

    # tail -f /var/log/kern.log
    [ 1815.983374] usb 4-3: 新的 SuperSpeed USB 设备编号为 4，使用 xhci_hcd
    [ 1815.999595] usb 4-3: LPM 退出延迟为零，禁用 LPM
这段文本描述了Linux系统中通过USB调试桥接控制器(DbC)进行调试的过程。以下是翻译后的中文内容：

[ 1815.999899] usb 4-3: 发现新的USB设备，idVendor=1d6b, idProduct=0004
	[ 1815.999902] usb 4-3: 新的USB设备字符串：制造商=1，产品=2，序列号=3
	[ 1815.999903] usb 4-3: 产品名: Remote GDB
	[ 1815.999904] usb 4-3: 制造商: Linux
	[ 1815.999905] usb 4-3: 序列号: 0001
	[ 1816.000240] usb_debug 4-3:1.0: 检测到xhci_dbc转换器
	[ 1816.000360] usb 4-3: xhci_dbc转换器现已连接至ttyUSB0

您可以使用任何通信程序（例如minicom）来读取和查看这些消息。下面是一些简单的bash脚本示例，可以帮助您检查设置是否正确：
.. code-block:: sh

	===== bash脚本开始 =============
	#!/bin/bash

	while true ; do
		while [ ! -d /sys/class/tty/ttyUSB0 ] ; do
			:
		done
	cat /dev/ttyUSB0
	done
	===== bash脚本结束 ===============

串行TTY
========

DbC支持已被添加到xHCI驱动中。您可以在运行时获得由DbC提供的调试设备。
为了使用这个功能，您需要确保内核已配置支持USB_XHCI_DBGCAP。在xHCI设备节点下的一个sysfs属性用于启用或禁用DbC，默认情况下，DbC是禁用的：

	root@target:/sys/bus/pci/devices/0000:00:14.0# cat dbc
	禁用

使用以下命令启用DbC：

	root@target:/sys/bus/pci/devices/0000:00:14.0# echo 启用 > dbc

您随时可以检查DbC的状态：

	root@target:/sys/bus/pci/devices/0000:00:14.0# cat dbc
	启用

使用USB 3.0超高速A-to-A调试电缆将调试目标连接到调试主机。您可以看到在调试目标上创建了/dev/ttyDBC0。您将看到以下内核日志消息：

	root@target: tail -f /var/log/kern.log
	[  182.730103] xhci_hcd 0000:00:14.0: DbC连接成功
	[  191.169420] xhci_hcd 0000:00:14.0: DbC配置完成
	[  191.169597] xhci_hcd 0000:00:14.0: DbC现已连接至/dev/ttyDBC0

相应地，DbC的状态已经提升为：

	root@target:/sys/bus/pci/devices/0000:00:14.0# cat dbc
	配置完成

在调试主机上，您会看到调试设备已被枚举。您将看到以下内核日志消息：

	root@host: tail -f /var/log/kern.log
	[   79.454780] usb 2-2.1: 新的SuperSpeed USB设备编号3使用xhci_hcd
	[   79.475003] usb 2-2.1: LPM退出延迟被置零，禁用LPM
	[   79.475389] usb 2-2.1: 发现新的USB设备，idVendor=1d6b, idProduct=0010
	[   79.475390] usb 2-2.1: 新的USB设备字符串：制造商=1，产品=2，序列号=3
	[   79.475391] usb 2-2.1: 产品名: Linux USB调试目标
	[   79.475392] usb 2-2.1: 制造商: Linux基金会
	[   79.475393] usb 2-2.1: 序列号: 0001

调试设备现在可以工作了。您可以使用任何通信或调试程序在主机与目标之间进行通信。
