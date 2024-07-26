SPDX 许可证标识符: GPL-2.0

===================
PCI 测试用户手册
===================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

本文档是一份指南，旨在帮助用户使用 pci-epf-test 功能驱动程序和 pci_endpoint_test 主机驱动程序来进行 PCI 测试。下面分别给出了主机侧和终端侧需要遵循的步骤。

终端设备
===============

终端控制器设备
---------------------------

要查找系统中的终端控制器设备列表，请执行以下命令:

	# ls /sys/class/pci_epc/
	  51000000.pcie_ep

如果启用了 PCI_ENDPOINT_CONFIGFS:

	# ls /sys/kernel/config/pci_ep/controllers
	  51000000.pcie_ep


终端功能驱动程序
-------------------------

要查找系统中的终端功能驱动程序列表，请执行以下命令:

	# ls /sys/bus/pci-epf/drivers
	  pci_epf_test

如果启用了 PCI_ENDPOINT_CONFIGFS:

	# ls /sys/kernel/config/pci_ep/functions
	  pci_epf_test


创建 pci-epf-test 设备
----------------------------

可以使用 configfs 来创建 PCI 终端功能设备。为了创建 pci-epf-test 设备，可以使用以下命令:

	# mount -t configfs none /sys/kernel/config
	# cd /sys/kernel/config/pci_ep/
	# mkdir functions/pci_epf_test/func1

上面的 "mkdir func1" 命令创建了一个将由 pci_epf_test 驱动程序探测的 pci-epf-test 功能设备。
PCI 终端框架会在目录中填充以下可配置字段:

	# ls functions/pci_epf_test/func1
	  baseclass_code	interrupt_pin	progif_code	subsys_id
	  cache_line_size	msi_interrupts	revid		subsys_vendorid
	  deviceid          	msix_interrupts	subclass_code	vendorid

当设备绑定到驱动程序时，PCI 终端功能驱动程序会为这些条目填充默认值。pci-epf-test 驱动程序会将 vendorid 设置为 0xffff 并将 interrupt_pin 设置为 0x0001:

	# cat functions/pci_epf_test/func1/vendorid
	  0xffff
	# cat functions/pci_epf_test/func1/interrupt_pin
	  0x0001


配置 pci-epf-test 设备
-------------------------------

用户可以使用 configfs 条目来配置 pci-epf-test 设备。为了改变 vendorid 和功能设备使用的 MSI 中断数量，可以使用以下命令:

	# echo 0x104c > functions/pci_epf_test/func1/vendorid
	# echo 0xb500 > functions/pci_epf_test/func1/deviceid
	# echo 16 > functions/pci_epf_test/func1/msi_interrupts
	# echo 8 > functions/pci_epf_test/func1/msix_interrupts


将 pci-epf-test 设备绑定到 EP 控制器
--------------------------------------------

为了让终端功能设备变得有用，它必须与一个 PCI 终端控制器驱动程序绑定。使用 configfs 将功能设备绑定到系统中存在的某个控制器驱动程序:

	# ln -s functions/pci_epf_test/func1 controllers/51000000.pcie_ep/

完成上述步骤后，PCI 终端已准备好与主机建立连接。
开始连接
--------------

为了让终端设备与主机建立连接，_start_ 字段应该被填充为 '1':

	# echo 1 > controllers/51000000.pcie_ep/start


根复合体设备
==================

lspci 输出
------------

请注意，这里列出的设备对应于在第 1.4 节中填充的值:

	00:00.0 PCI 桥接器: Texas Instruments 设备 8888 (版本 01)
	01:00.0 未分配类别 [ff00]: Texas Instruments 设备 b500


使用终端测试功能设备
-----------------------------------

可以在 tools/pci/ 目录下找到添加的 pcitest.sh 脚本来运行所有默认的 PCI 终端测试。为了编译这个工具，可以使用以下命令:

	# cd <kernel-dir>
	# make -C tools/pci

或者如果你希望在你的系统中编译并安装:

	# cd <kernel-dir>
	# make -C tools/pci install

工具和脚本将会位于 <rootfs>/usr/bin/ 中。

pcitest.sh 输出
~~~~~~~~~~~~~~~~~
::

	# pcitest.sh
	BAR 测试

	BAR0:           OKAY
	BAR1:           OKAY
	BAR2:           OKAY
	BAR3:           OKAY
	BAR4:           NOT OKAY
	BAR5:           NOT OKAY

	中断测试

	设置中断类型为传统:         OKAY
	传统中断:     NOT OKAY
	设置中断类型为 MSI:            OKAY
	MSI1:           OKAY
	MSI2:           OKAY
	...
	MSI17:          NOT OKAY
	MSI18:          NOT OKAY
	...
	设置中断类型为 MSI-X:          OKAY
	MSI-X1:         OKAY
	MSI-X2:         OKAY
	...
	MSI-X9:         NOT OKAY
	MSI-X10:        NOT OKAY
	...
	MSI-X2048:      NOT OKAY

	读取测试

	设置中断类型为 MSI:            OKAY
	读取 (      1 字节):           OKAY
	读取 (   1024 字节):           OKAY
	读取 (   1025 字节):           OKAY
	读取 (1024000 字节):           OKAY
	读取 (1024001 字节):           OKAY

	写入测试

	写入 (      1 字节):          OKAY
	写入 (   1024 字节):          OKAY
	写入 (   1025 字节):          OKAY
	写入 (1024000 字节):          OKAY
	写入 (1024001 字节):          OKAY

	复制测试

	复制 (      1 字节):           OKAY
	复制 (   1024 字节):           OKAY
	复制 (   1025 字节):           OKAY
	复制 (1024000 字节):           OKAY
	复制 (1024001 字节):           OKAY
