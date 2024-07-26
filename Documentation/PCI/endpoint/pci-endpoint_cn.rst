### SPDX 许可证标识符：GPL-2.0

#### 作者：Kishon Vijay Abraham I <kishon@ti.com>

本文档是使用 PCI 终端框架的指南，用于创建终端控制器驱动程序、终端功能驱动程序，并利用 configfs 接口将功能驱动程序绑定到控制器驱动程序。

## 引言

Linux 拥有一个全面的 PCI 子系统来支持以根复合模式运行的 PCI 控制器。该子系统能够扫描 PCI 总线、分配内存资源和中断资源、加载 PCI 驱动程序（基于供应商 ID 和设备 ID）、支持热插拔、电源管理、高级错误报告和虚拟通道等其他服务。
然而，一些片上系统 (SoC) 中集成的 PCI 控制器 IP 可以在根复合模式或终端模式下运行。PCI 终端框架将在 Linux 中增加终端模式的支持。这有助于在 EP 系统中运行 Linux，该系统可以有广泛的用途，例如测试或验证、协处理器加速器等。

## PCI 终端核心

PCI 终端核心层包含三个组件：终端控制器库、终端功能库以及用于将终端功能与终端控制器绑定的 configfs 层。

### PCI 终端控制器 (EPC) 库

EPC 库为能在终端模式下运行的控制器提供 API，并为实现特定终端功能的功能驱动程序/库提供 API。

#### PCI 控制器驱动程序的 API

本节列出了 PCI 终端核心为 PCI 控制器驱动程序提供的 API：

* `devm_pci_epc_create()` / `pci_epc_create()`

   PCI 控制器驱动程序应实现以下操作：

     * `write_header`：用于填充配置空间头部的操作
     * `set_bar`：用于配置 BAR 的操作
     * `clear_bar`：用于重置 BAR 的操作
     * `alloc_addr_space`：用于在 PCI 控制器地址空间中分配的操作
     * `free_addr_space`：用于释放已分配地址空间的操作
     * `raise_irq`：用于触发传统、MSI 或 MSI-X 中断的操作
     * `start`：用于启动 PCI 链路的操作
     * `stop`：用于停止 PCI 链路的操作

   PCI 控制器驱动程序可以通过调用 `devm_pci_epc_create()` / `pci_epc_create()` 来创建一个新的 EPC 设备。

* `devm_pci_epc_destroy()` / `pci_epc_destroy()`

   PCI 控制器驱动程序可以使用 `devm_pci_epc_destroy()` 或 `pci_epc_destroy()` 销毁通过 `devm_pci_epc_create()` 或 `pci_epc_create()` 创建的 EPC 设备。

* `pci_epc_linkup()`

   为了通知所有链接到该 EPC 设备的功能设备已经与主机建立了连接，PCI 控制器驱动程序应调用 `pci_epc_linkup()`。

* `pci_epc_mem_init()`

   初始化用于分配 EPC 地址空间的 `pci_epc_mem` 结构。
* `pci_epc_mem_exit()`

  清理在 `pci_epc_mem_init()` 中分配的 `pci_epc_mem` 结构。

PCI 终端功能驱动程序的 EPC API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

本节列出了 PCI 终端核心为 PCI 终端功能驱动程序提供的 API。

* `pci_epc_write_header()`

  PCI 终端功能驱动程序应使用 `pci_epc_write_header()` 将标准配置头写入终端控制器。

* `pci_epc_set_bar()`

  PCI 终端功能驱动程序应使用 `pci_epc_set_bar()` 来配置基址寄存器 (Base Address Register)，以便主机分配 PCI 地址空间。通常，功能驱动程序的寄存器空间通过此 API 进行配置。

* `pci_epc_clear_bar()`

  PCI 终端功能驱动程序应使用 `pci_epc_clear_bar()` 来重置 BAR。

* `pci_epc_raise_irq()`

  PCI 终端功能驱动程序应使用 `pci_epc_raise_irq()` 来触发传统中断、MSI 或 MSI-X 中断。

* `pci_epc_mem_alloc_addr()`

  PCI 终端功能驱动程序应使用 `pci_epc_mem_alloc_addr()` 从 EPC 地址空间中分配内存地址，该地址用于访问根复合体 (RC) 的缓冲区。

* `pci_epc_mem_free_addr()`

  PCI 终端功能驱动程序应使用 `pci_epc_mem_free_addr()` 释放使用 `pci_epc_mem_alloc_addr()` 分配的内存空间。

其他 EPC API
~~~~~~~~~~~~~~

EPC 库还提供了其他 API。这些 API 用于将 EPF 设备与 EPC 设备绑定。可以参考 `pci-ep-cfs.c` 文件来了解如何使用这些 API。

* `pci_epc_get()`

  根据控制器的设备名称获取对 PCI 终端控制器的引用。
* pci_epc_put()

   释放使用 pci_epc_get() 获取的 PCI 终端控制器的引用。

* pci_epc_add_epf()

   向 PCI 终端控制器添加一个 PCI 终端功能。根据规范，一个 PCIe 设备最多可以有 8 个功能。

* pci_epc_remove_epf()

   从 PCI 终端控制器移除 PCI 终端功能。

* pci_epc_start()

   当 PCI 终端功能驱动程序配置好终端功能并希望启动 PCI 链路时，应该调用 pci_epc_start()。

* pci_epc_stop()

   当 PCI 终端功能驱动程序希望停止 PCI 链路时，应该调用 pci_epc_stop()。

PCI 终端功能 (EPF) 库
------------------------

EPF 库提供了 API 供功能驱动程序和 EPC 库使用，以提供终端模式功能。
PCI 终端功能 (EPF) 的 API
~~~~~~~~~~~~~~~~~~~~~~~~~~

本节列出了 PCI 终端核心为 PCI 终端功能驱动程序提供的 API。
* pci_epf_register_driver()

   PCI 终端功能驱动程序应实现以下操作：
     - bind：当 EPC 设备与 EPF 设备绑定时要执行的操作。
     - unbind：当 EPC 设备与 EPF 设备之间的绑定丢失时要执行的操作。
     - linkup：当 EPC 设备与主机系统建立连接时要执行的操作。

   PCI 功能驱动程序然后可以使用 pci_epf_register_driver() 注册 PCI EPF 驱动程序。

* pci_epf_unregister_driver()

   PCI 功能驱动程序可以使用 pci_epf_unregister_driver() 取消注册 PCI EPF 驱动程序。

* pci_epf_alloc_space()

   PCI 功能驱动程序可以使用 pci_epf_alloc_space() 为特定 BAR 分配空间。

* pci_epf_free_space()

   PCI 功能驱动程序可以通过调用 pci_epf_free_space() 释放已分配的空间（使用 pci_epf_alloc_space 分配）。
PCI终端控制器库的APIs
~~~~~~~~~~~~~~~~~~~~~~~~~

本节列出了PCI终端核心提供的API，这些API可供PCI终端控制器库使用。

* `pci_epf_linkup()`

   当EPC设备与主机建立连接时，PCI终端控制器库会调用`pci_epf_linkup()`。
   
其他EPF APIs
~~~~~~~~~~~~~~

EPF库还提供了其他API。这些API用于在EPF设备绑定到EPC设备时通知功能驱动程序。
`pci-ep-cfs.c`可以作为使用这些API的参考。
* `pci_epf_create()`

   通过传递PCI EPF设备的名称来创建一个新的PCI EPF设备。
   此名称将用于将EPF设备绑定到EPF驱动程序。
* `pci_epf_destroy()`

   销毁已创建的PCI EPF设备。
* `pci_epf_bind()`

   当EPF设备已经绑定到EPC设备时，应调用`pci_epf_bind()`。
* `pci_epf_unbind()`

   当EPC设备和EPF设备之间的绑定丢失时，应调用`pci_epf_unbind()`。
