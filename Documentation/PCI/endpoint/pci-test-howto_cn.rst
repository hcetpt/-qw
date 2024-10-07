SPDX 许可证标识符: GPL-2.0

===================
PCI 测试用户指南
===================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

本文档旨在帮助用户使用 pci-epf-test 功能驱动程序和 pci_endpoint_test 主机驱动程序进行 PCI 测试。下面列出了主机端和 EP 端需要遵循的步骤。

终端设备
===============

终端控制器设备
---------------------------

要查找系统中的终端控制器设备列表，请执行以下命令：

    # ls /sys/class/pci_epc/
      51000000.pcie_ep

如果启用了 PCI_ENDPOINT_CONFIGFS ：

    # ls /sys/kernel/config/pci_ep/controllers
      51000000.pcie_ep

终端功能驱动程序
-------------------------

要查找系统中的终端功能驱动程序列表，请执行以下命令：

    # ls /sys/bus/pci-epf/drivers
      pci_epf_test

如果启用了 PCI_ENDPOINT_CONFIGFS ：

    # ls /sys/kernel/config/pci_ep/functions
      pci_epf_test

创建 pci-epf-test 设备
----------------------------

可以使用 configfs 创建 PCI 终端功能设备。要创建 pci-epf-test 设备，可以使用以下命令：

    # mount -t configfs none /sys/kernel/config
    # cd /sys/kernel/config/pci_ep/
    # mkdir functions/pci_epf_test/func1

上述 “mkdir func1” 命令会创建一个由 pci_epf_test 驱动程序探测的 pci-epf-test 功能设备。
PCI 终端框架会在目录中填充以下可配置字段：

    # ls functions/pci_epf_test/func1
      baseclass_code interrupt_pin progif_code subsys_id
      cache_line_size msi_interrupts revid subsys_vendorid
      deviceid msix_interrupts subclass_code vendorid

当设备绑定到驱动程序时，PCI 终端功能驱动程序会用默认值填充这些条目。pci-epf-test 驱动程序将 vendorid 设置为 0xffff，并将 interrupt_pin 设置为 0x0001：

    # cat functions/pci_epf_test/func1/vendorid
      0xffff
    # cat functions/pci_epf_test/func1/interrupt_pin
      0x0001

配置 pci-epf-test 设备
-------------------------------

用户可以通过 configfs 条目来配置 pci-epf-test 设备。为了更改 vendorid 和功能设备使用的 MSI 中断数量，可以使用以下命令：

    # echo 0x104c > functions/pci_epf_test/func1/vendorid
    # echo 0xb500 > functions/pci_epf_test/func1/deviceid
    # echo 16 > functions/pci_epf_test/func1/msi_interrupts
    # echo 8 > functions/pci_epf_test/func1/msix_interrupts

绑定 pci-epf-test 设备到 EP 控制器
--------------------------------------------

为了让终端功能设备有用，它必须绑定到 PCI 终端控制器驱动程序。使用 configfs 将功能设备绑定到系统中存在的控制器驱动程序之一：

    # ln -s functions/pci_epf_test/func1 controllers/51000000.pcie_ep/

完成以上步骤后，PCI 终端准备好与主机建立连接。

开始连接
--------------

为了让终端设备与主机建立连接，应将 _start_ 字段设置为 '1'：

    # echo 1 > controllers/51000000.pcie_ep/start

根复合设备
==================

lspci 输出
------------

请注意，这里列出的设备对应于上面 1.4 中填写的值：

    00:00.0 PCI 桥接器: Texas Instruments Device 8888 (rev 01)
    01:00.0 未分配的类 [ff00]: Texas Instruments Device b500

使用终端测试功能设备
-----------------------------------

可以使用添加在 tools/pci/ 目录下的 pcitest.sh 运行所有默认的 PCI 终端测试。要编译此工具，请使用以下命令：

    # cd <kernel-dir>
    # make -C tools/pci

或者如果您希望在系统中编译并安装：

    # cd <kernel-dir>
    # make -C tools/pci install

工具和脚本将位于 <rootfs>/usr/bin/ 中。

pcitest.sh 输出
~~~~~~~~~~~~~~~

    # pcitest.sh
    BAR 测试

    BAR0:           OKAY
    BAR1:           OKAY
    BAR2:           OKAY
    BAR3:           OKAY
    BAR4:           NOT OKAY
    BAR5:           NOT OKAY

    中断测试

    设置中断类型为传统模式:         OKAY
    传统中断:     NOT OKAY
    设置中断类型为 MSI:            OKAY
    MSI1:           OKAY
    MSI2:           OKAY
    MSI3:           OKAY
    MSI4:           OKAY
    MSI5:           OKAY
    MSI6:           OKAY
    MSI7:           OKAY
    MSI8:           OKAY
    MSI9:           OKAY
    MSI10:          OKAY
    MSI11:          OKAY
    MSI12:          OKAY
    MSI13:          OKAY
    MSI14:          OKAY
    MSI15:          OKAY
    MSI16:          OKAY
    MSI17:          NOT OKAY
    MSI18:          NOT OKAY
    MSI19:          NOT OKAY
    MSI20:          NOT OKAY
    MSI21:          NOT OKAY
    MSI22:          NOT OKAY
    MSI23:          NOT OKAY
    MSI24:          NOT OKAY
    MSI25:          NOT OKAY
    MSI26:          NOT OKAY
    MSI27:          NOT OKAY
    MSI28:          NOT OKAY
    MSI29:          NOT OKAY
    MSI30:          NOT OKAY
    MSI31:          NOT OKAY
    MSI32:          NOT OKAY
    设置中断类型为 MSI-X:          OKAY
    MSI-X1:         OKAY
    MSI-X2:         OKAY
    MSI-X3:         OKAY
    MSI-X4:         OKAY
    MSI-X5:         OKAY
    MSI-X6:         OKAY
    MSI-X7:         OKAY
    MSI-X8:         OKAY
    MSI-X9:         NOT OKAY
    MSI-X10:        NOT OKAY
    MSI-X11:        NOT OKAY
    MSI-X12:        NOT OKAY
    MSI-X13:        NOT OKAY
    MSI-X14:        NOT OKAY
    MSI-X15:        NOT OKAY
    MSI-X16:        NOT OKAY
    [...]
    MSI-X2047:      NOT OKAY
    MSI-X2048:      NOT OKAY

    读取测试

    设置中断类型为 MSI:            OKAY
    读取 (1 字节):           OKAY
    读取 (1024 字节):           OKAY
    读取 (1025 字节):           OKAY
    读取 (1024000 字节):           OKAY
    读取 (1024001 字节):           OKAY

    写入测试

    写入 (1 字节):          OKAY
    写入 (1024 字节):          OKAY
    写入 (1025 字节):          OKAY
    写入 (1024000 字节):          OKAY
    写入 (1024001 字节):          OKAY

    复制测试

    复制 (1 字节):           OKAY
    复制 (1024 字节):           OKAY
    复制 (1025 字节):           OKAY
    复制 (1024000 字节):           OKAY
    复制 (1024001 字节):           OKAY
