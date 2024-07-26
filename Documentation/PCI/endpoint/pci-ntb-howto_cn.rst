SPDX 许可证标识符: GPL-2.0

===================================================================
PCI 非透明桥接 (NTB) 终端功能 (EPF) 用户指南
===================================================================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

本文档是指导用户使用 pci-epf-ntb 功能驱动程序和 ntb_hw_epf 主机驱动程序以实现 NTB 功能性的指南。在主机侧和终端侧需要遵循的步骤如下所示。有关使用可配置终端的 NTB 硬件配置和内部结构，请参见 Documentation/PCI/endpoint/pci-ntb-function.rst。

终端设备
===============

终端控制器设备
---------------------------

要实现 NTB 功能性，至少需要两个终端控制器设备。
要查找系统中终端控制器设备的列表，请执行以下命令:

	# ls /sys/class/pci_epc/
	2900000.pcie-ep  2910000.pcie-ep

如果启用了 PCI_ENDPOINT_CONFIGFS:

	# ls /sys/kernel/config/pci_ep/controllers
	2900000.pcie-ep  2910000.pcie-ep


终端功能驱动程序
-------------------------

要查找系统中终端功能驱动程序的列表，请执行以下命令:

	# ls /sys/bus/pci-epf/drivers
	pci_epf_ntb   pci_epf_ntb

如果启用了 PCI_ENDPOINT_CONFIGFS:

	# ls /sys/kernel/config/pci_ep/functions
	pci_epf_ntb   pci_epf_ntb


创建 pci-epf-ntb 设备
----------------------------

可以使用 configfs 创建 PCI 终端功能设备。要创建 pci-epf-ntb 设备，可以使用以下命令:

	# mount -t configfs none /sys/kernel/config
	# cd /sys/kernel/config/pci_ep/
	# mkdir functions/pci_epf_ntf/func1

上述 "mkdir func1" 命令将创建一个由 pci_epf_ntb 驱动程序探测的 pci-epf-ntb 功能设备。
PCI 终端框架会用以下可配置字段填充该目录:

	# ls functions/pci_epf_ntb/func1
	baseclass_code    deviceid          msi_interrupts    pci-epf-ntb.0
	progif_code       secondary         subsys_id         vendorid
	cache_line_size   interrupt_pin     msix_interrupts   primary
	revid             subclass_code     subsys_vendor_id

当设备绑定到驱动程序时，PCI 终端功能驱动程序会为这些条目填充默认值。pci-epf-ntb 驱动程序会将 vendorid 设置为 0xffff 并将 interrupt_pin 设置为 0x0001:

	# cat functions/pci_epf_ntb/func1/vendorid
	0xffff
	# cat functions/pci_epf_ntb/func1/interrupt_pin
	0x0001


配置 pci-epf-ntb 设备
-------------------------------

用户可以通过其 configfs 条目来配置 pci-epf-ntb 设备。为了更改 vendorid 和 deviceid，可以使用以下命令:

	# echo 0x104c > functions/pci_epf_ntb/func1/vendorid
	# echo 0xb00d > functions/pci_epf_ntb/func1/deviceid

PCI 终端框架还会在功能属性目录中自动创建一个子目录。此子目录与功能设备名称相同，并填充了以下可以由用户配置的 NTB 特定属性:

	# ls functions/pci_epf_ntb/func1/pci_epf_ntb.0/
	db_count    mw1         mw2         mw3         mw4         num_mws
	spad_count

下面是一个 NTB 功能示例配置:

	# echo 4 > functions/pci_epf_ntb/func1/pci_epf_ntb.0/db_count
	# echo 128 > functions/pci_epf_ntb/func1/pci_epf_ntb.0/spad_count
	# echo 2 > functions/pci_epf_ntb/func1/pci_epf_ntb.0/num_mws
	# echo 0x100000 > functions/pci_epf_ntb/func1/pci_epf_ntb.0/mw1
	# echo 0x100000 > functions/pci_epf_ntb/func1/pci_epf_ntb.0/mw2

将 pci-epf-ntb 设备绑定到 EP 控制器
--------------------------------------------

NTB 功能设备应连接到两个 PCI 终端控制器，这两个控制器分别连接到两台主机。使用 NTB 功能设备中的 'primary' 和 'secondary' 条目将一个 PCI 终端控制器连接到主接口，另一个 PCI 终端控制器连接到次接口:

	# ln -s controllers/2900000.pcie-ep/ functions/pci-epf-ntb/func1/primary
	# ln -s controllers/2910000.pcie-ep/ functions/pci-epf-ntb/func1/secondary

完成以上步骤后，两个 PCI 终端控制器都已准备好与主机建立链接。
开始链接
--------------

为了让终端设备与主机建立链接，应将 _start_ 字段设置为 '1'。对于 NTB，两个 PCI 终端控制器都应与主机建立链接:

	# echo 1 > controllers/2900000.pcie-ep/start
	# echo 1 > controllers/2910000.pcie-ep/start


根复合体设备
==================

lspci 输出
------------

请注意，这里列出的设备对应于“创建 pci-epf-ntb 设备”部分中填写的值:

	# lspci
	0000:00:00.0 PCI 桥接器: Texas Instruments 设备 b00d
	0000:01:00.0 RAM 内存: Texas Instruments 设备 b00d


使用 ntb_hw_epf 设备
-----------------------

主机软件遵循 Linux 中标准的 NTB 软件架构。
所有现有的客户端 NTB 工具（如 NTB 传输客户端、NTB 网络设备、NTB Ping Pong 测试客户端和 NTB 工具测试客户端）都可以与 NTB 功能设备一起使用。
有关 NTB 的更多信息，请参阅 :doc:`非透明桥接 <../../driver-api/ntb>`
