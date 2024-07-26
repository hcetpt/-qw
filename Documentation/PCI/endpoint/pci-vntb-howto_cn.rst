SPDX 许可证标识符: GPL-2.0

===================================================================
PCI 非透明桥接 (NTB) 终端功能 (EPF) 用户指南
===================================================================

:作者: Frank Li <Frank.Li@nxp.com>

本文档是帮助用户使用 pci-epf-vntb 功能驱动程序和 ntb_hw_epf 主机驱动程序来实现 NTB 功能的指南。下面给出了主机侧和终端侧需要遵循的一系列步骤。有关使用可配置终端的 NTB 硬件配置和内部结构，请参阅 Documentation/PCI/endpoint/pci-vntb-function.rst。

终端设备
===============

终端控制器设备
---------------------------

要查找系统中的终端控制器设备列表，可以执行以下命令:

        # ls /sys/class/pci_epc/
          5f010000.pcie_ep

如果启用了 PCI_ENDPOINT_CONFIGFS：

        # ls /sys/kernel/config/pci_ep/controllers
          5f010000.pcie_ep

终端功能驱动程序
-------------------------

要查找系统中的终端功能驱动程序列表，可以执行以下命令:

	# ls /sys/bus/pci-epf/drivers
	pci_epf_ntb  pci_epf_test  pci_epf_vntb

如果启用了 PCI_ENDPOINT_CONFIGFS：

	# ls /sys/kernel/config/pci_ep/functions
	pci_epf_ntb  pci_epf_test  pci_epf_vntb


创建 pci-epf-vntb 设备
----------------------------

可以使用 configfs 创建 PCI 终端功能设备。要创建 pci-epf-vntb 设备，可以使用以下命令:

	# mount -t configfs none /sys/kernel/config
	# cd /sys/kernel/config/pci_ep/
	# mkdir functions/pci_epf_vntb/func1

上述 "mkdir func1" 命令将创建一个 pci-epf-vntb 功能设备，该设备将被 pci_epf_vntb 驱动程序探测。
PCI 终端框架会用以下可配置字段填充目录:

	# ls functions/pci_epf_ntb/func1
	baseclass_code    deviceid          msi_interrupts    pci-epf-ntb.0
	progif_code       secondary         subsys_id         vendorid
	cache_line_size   interrupt_pin     msix_interrupts   primary
	revid             subclass_code     subsys_vendor_id

当设备绑定到驱动程序时，PCI 终端功能驱动程序会用默认值填充这些条目。pci-epf-vntb 驱动程序会将 vendorid 设置为 0xffff 并将 interrupt_pin 设置为 0x0001:

	# cat functions/pci_epf_vntb/func1/vendorid
	0xffff
	# cat functions/pci_epf_vntb/func1/interrupt_pin
	0x0001


配置 pci-epf-vntb 设备
-------------------------------

用户可以通过其 configfs 条目来配置 pci-epf-vntb 设备。为了更改 vendorid 和 deviceid，可以使用以下命令:

	# echo 0x1957 > functions/pci_epf_vntb/func1/vendorid
	# echo 0x0809 > functions/pci_epf_vntb/func1/deviceid

PCI 终端框架还会在功能属性目录中自动创建一个子目录。这个子目录与功能设备名称相同，并填充了以下 NTB 特定的可由用户配置的属性:

	# ls functions/pci_epf_vntb/func1/pci_epf_vntb.0/
	db_count    mw1         mw2         mw3         mw4         num_mws
	spad_count

一个 NTB 功能的示例配置如下所示:

	# echo 4 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/db_count
	# echo 128 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/spad_count
	# echo 1 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/num_mws
	# echo 0x100000 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/mw1

虚拟 PCI 总线的虚拟 NTB 驱动程序的示例配置如下:

	# echo 0x1957 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vntb_vid
	# echo 0x080A > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vntb_pid
	# echo 0x10 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vbus_number

将 pci-epf-ntb 设备绑定到 EP 控制器
--------------------------------------------

NTB 功能设备应该连接到与主机相连的 PCI 终端控制器
# ln -s controllers/5f010000.pcie_ep functions/pci-epf-ntb/func1/primary

完成上述步骤后，PCI 终端控制器已准备好与主机建立链接
开始链接
--------------

为了让终端设备与主机建立链接，应将 _start_ 字段设置为 '1'。对于 NTB，两个 PCI 终端控制器都应该与主机建立链接（imx8 不需要此步骤）:

	# echo 1 > controllers/5f010000.pcie_ep/start

根复合设备
==================

主机侧的 lspci 输出
-------------------------

请注意，这里列出的设备对应于“创建 pci-epf-ntb 设备”部分中填充的值:

	# lspci
        00:00.0 PCI 桥接器: Freescale Semiconductor Inc 设备 0000 (修订版 01)
        01:00.0 RAM 存储器: Freescale Semiconductor Inc 设备 0809

终端设备 / 虚拟 PCI 总线
=================================

终端侧 / 虚拟 PCI 总线的 lspci 输出
-----------------------------------------

请注意，这里列出的设备对应于“创建 pci-epf-ntb 设备”部分中填充的值:

        # lspci
        10:00.0 未分配类 [ffff]: Dawicontrol Computersysteme GmbH 设备 1234 (修订版 ff)

使用 ntb_hw_epf 设备
-----------------------

主机软件遵循 Linux 中的标准 NTB 软件架构
所有现有的客户端 NTB 工具，如 NTB 传输客户端和 NTB 网络设备、NTB Ping Pong 测试客户端和 NTB 工具测试客户端都可以与 NTB 功能设备一起使用。
有关 NTB 的更多信息，请参见
:doc:`非透明桥接 <../../driver-api/ntb>`
