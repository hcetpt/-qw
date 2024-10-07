SPDX 许可证标识符: GPL-2.0

===================================================================
PCI 非透明桥接 (NTB) 终端功能 (EPF) 用户指南
===================================================================

:作者: Frank Li <Frank.Li@nxp.com>

本文档旨在帮助用户使用 pci-epf-vntb 功能驱动程序和 ntb_hw_epf 主机驱动程序实现 NTB 功能。以下是在主机侧和 EP 侧需遵循的步骤列表。有关使用可配置终端的 NTB 硬件配置和内部结构，请参见 Documentation/PCI/endpoint/pci-vntb-function.rst。

终端设备
===============

终端控制器设备
---------------------------

要查找系统中的终端控制器设备列表，请执行以下命令：

        # ls /sys/class/pci_epc/
          5f010000.pcie_ep

如果启用了 PCI_ENDPOINT_CONFIGFS ：

        # ls /sys/kernel/config/pci_ep/controllers
          5f010000.pcie_ep

终端功能驱动程序
-------------------------

要查找系统中的终端功能驱动程序列表，请执行以下命令：

	# ls /sys/bus/pci-epf/drivers
	pci_epf_ntb  pci_epf_test  pci_epf_vntb

如果启用了 PCI_ENDPOINT_CONFIGFS ：

	# ls /sys/kernel/config/pci_ep/functions
	pci_epf_ntb  pci_epf_test  pci_epf_vntb

创建 pci-epf-vntb 设备
----------------------------

可以使用 configfs 创建 PCI 终端功能设备。为了创建 pci-epf-vntb 设备，可以使用以下命令：

	# mount -t configfs none /sys/kernel/config
	# cd /sys/kernel/config/pci_ep/
	# mkdir functions/pci_epf_vntb/func1

上述 "mkdir func1" 命令将创建由 pci_epf_vntb 驱动程序探测的 pci-epf-vntb 功能设备。
PCI 终端框架会填充该目录以下可配置字段：

	# ls functions/pci_epf_vntb/func1
	baseclass_code    deviceid          msi_interrupts    pci-epf-ntb.0
	progif_code       secondary         subsys_id         vendorid
	cache_line_size   interrupt_pin     msix_interrupts   primary
	revid             subclass_code     subsys_vendor_id

当设备绑定到驱动程序时，PCI 终端功能驱动程序会用默认值填充这些条目。pci-epf-vntb 驱动程序会将 vendorid 设置为 0xffff 并将 interrupt_pin 设置为 0x0001 ：

	# cat functions/pci_epf_vntb/func1/vendorid
	0xffff
	# cat functions/pci_epf_vntb/func1/interrupt_pin
	0x0001

配置 pci-epf-vntb 设备
-------------------------------

用户可以通过其 configfs 条目来配置 pci-epf-vntb 设备。为了更改 vendorid 和 deviceid，可以使用以下命令：

	# echo 0x1957 > functions/pci_epf_vntb/func1/vendorid
	# echo 0x0809 > functions/pci_epf_vntb/func1/deviceid

PCI 终端框架还会在功能属性目录中自动创建一个子目录。此子目录具有与功能设备名称相同的名称，并且填充了以下可以由用户配置的 NTB 特定属性：

	# ls functions/pci_epf_vntb/func1/pci_epf_vntb.0/
	db_count    mw1         mw2         mw3         mw4         num_mws
	spad_count

下面是一个 NTB 功能示例配置：

	# echo 4 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/db_count
	# echo 128 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/spad_count
	# echo 1 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/num_mws
	# echo 0x100000 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/mw1

虚拟 NTB 驱动程序用于虚拟 PCI 总线的一个示例配置如下：

	# echo 0x1957 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vntb_vid
	# echo 0x080A > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vntb_pid
	# echo 0x10 > functions/pci_epf_vntb/func1/pci_epf_vntb.0/vbus_number

将 pci-epf-ntb 设备绑定到 EP 控制器
--------------------------------------------

NTB 功能设备应连接到连接到主机的 PCI 终端控制器
# ln -s controllers/5f010000.pcie_ep functions/pci-epf-ntb/func1/primary

完成上述步骤后，PCI 终端控制器就准备好了与主机建立连接。
启动连接
--------------

为了使终端设备与主机建立连接，_start_ 字段应填充为 '1'。对于 NTB，两个 PCI 终端控制器都应与主机建立连接（imx8 不需要这一步骤）：

	# echo 1 > controllers/5f010000.pcie_ep/start

根复合体设备
==================

主机侧的 lspci 输出
-------------------------

注意，此处列出的设备对应于“创建 pci-epf-ntb 设备”部分中填充的值：

	# lspci
        00:00.0 PCI 桥接器: Freescale Semiconductor Inc 设备 0000 (版本 01)
        01:00.0 内存: Freescale Semiconductor Inc 设备 0809

终端设备 / 虚拟 PCI 总线
=================================

EP 侧 / 虚拟 PCI 总线的 lspci 输出
-----------------------------------------

注意，此处列出的设备对应于“创建 pci-epf-ntb 设备”部分中填充的值：

        # lspci
        10:00.0 未分配类别 [ffff]: Dawicontrol Computersysteme GmbH 设备 1234 (版本 ff)

使用 ntb_hw_epf 设备
-----------------------

主机侧软件遵循 Linux 中的标准 NTB 软件架构。所有现有的客户端 NTB 工具，如 NTB 传输客户端、NTB 网络设备、NTB Ping Pong 测试客户端和 NTB 工具测试客户端都可以与 NTB 功能设备一起使用。
有关 NTB 的更多信息，请参阅 :doc:`非透明桥接 <../../driver-api/ntb>`
