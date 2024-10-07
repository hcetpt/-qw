SPDX 许可证标识符: GPL-2.0

=================
PCI 测试功能
=================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

传统上，PCI 根复合体（RC）一直使用标准的 PCI 卡（如以太网 PCI 卡、USB PCI 卡或 SATA PCI 卡）进行验证。然而，随着 Linux 内核中 EP-core 的加入，现在可以配置一个能够在 EP 模式下工作的 PCI 控制器作为测试设备。PCI 终端测试设备是一个虚拟设备（在软件中定义），用于测试终端功能，并作为其他 PCI 终端设备的示例驱动程序（使用 EP 框架）。PCI 终端测试设备具有以下寄存器：

1) PCI_ENDPOINT_TEST_MAGIC  
2) PCI_ENDPOINT_TEST_COMMAND  
3) PCI_ENDPOINT_TEST_STATUS  
4) PCI_ENDPOINT_TEST_SRC_ADDR  
5) PCI_ENDPOINT_TEST_DST_ADDR  
6) PCI_ENDPOINT_TEST_SIZE  
7) PCI_ENDPOINT_TEST_CHECKSUM  
8) PCI_ENDPOINT_TEST_IRQ_TYPE  
9) PCI_ENDPOINT_TEST_IRQ_NUMBER  

* PCI_ENDPOINT_TEST_MAGIC

此寄存器用于测试 BAR0。将已知模式写入并从 MAGIC 寄存器读回以验证 BAR0。
* PCI_ENDPOINT_TEST_COMMAND

此寄存器由主机驱动程序用来指示终端设备需要执行的功能。
========	================================================================
位字段	描述
========	================================================================
位 0		引发传统中断请求（IRQ）
位 1		引发 MSI 中断请求（IRQ）
位 2		引发 MSI-X 中断请求（IRQ）
位 3		读取命令（从 RC 缓冲区读取数据）
位 4		写入命令（向 RC 缓冲区写入数据）
位 5		复制命令（从一个 RC 缓冲区复制数据到另一个 RC 缓冲区）
========	================================================================

* PCI_ENDPOINT_TEST_STATUS

此寄存器反映了 PCI 终端设备的状态。
========	==============================
位字段	描述
========	==============================
位 0		读取成功
位 1		读取失败
位 2		写入成功
位 3		写入失败
位 4		复制成功
位 5		复制失败
位 6		已触发中断请求（IRQ）
位 7		源地址无效
位 8		目标地址无效
========	==============================

* PCI_ENDPOINT_TEST_SRC_ADDR

此寄存器包含 COPY/READ 命令的源地址（RC 缓冲区地址）。
* PCI_ENDPOINT_TEST_DST_ADDR

此寄存器包含 COPY/WRITE 命令的目标地址（RC 缓冲区地址）。
* PCI_ENDPOINT_TEST_IRQ_TYPE

此寄存器包含由 READ/WRITE/COPY 和引发中断（IRQ）命令触发的中断类型（传统/MSI）。可能的类型如下：
======	==
传统	0
MSI	1
MSI-X	2
======	==

* PCI_ENDPOINT_TEST_IRQ_NUMBER

此寄存器包含触发的中断 ID。
可接受的值：

======	===========
传统模式	0
MSI	[1 .. 32]
MSI-X	[1 .. 2048]
======	===========

注：这里“Legacy”通常指的是传统的、非现代的技术或方法，在不同的上下文中可能有不同的翻译。在这个表格中，为了更清晰地表达，我将其翻译为“传统模式”。如果你有更具体的上下文或者偏好其他翻译，请告诉我。
