SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===========================================
PCI Express 端口总线驱动程序指南 HOWTO
===========================================

:作者: Tom L Nguyen tom.l.nguyen@intel.com 11/03/2004
:版权所有: © 2004 Intel Corporation

关于本指南
================

本指南描述了 PCI Express 端口总线驱动程序的基础，并提供了如何使服务驱动程序在 PCI Express 端口总线驱动程序中注册/注销的相关信息。

什么是 PCI Express 端口总线驱动程序
=======================================

一个 PCI Express 端口是一个逻辑 PCI-PCI 桥接结构。PCI Express 端口有两种类型：根端口和交换端口。根端口从 PCI Express 根复合体发起 PCI Express 链路，而交换端口则将 PCI Express 链路连接到内部逻辑 PCI 总线。具有代表交换机内部路由逻辑的次级总线的交换端口称为交换机的上游端口。交换机的下游端口是从交换机的内部路由总线到表示从 PCI Express 交换机发出的下游 PCI Express 链路的总线的桥接器。
一个 PCI Express 端口可以根据其端口类型提供多达四种不同的功能，在本文档中称为服务。这些服务包括原生热插拔支持（HP）、电源管理事件支持（PME）、高级错误报告支持（AER）和虚拟通道支持（VC）。这些服务可以由单一复杂的驱动程序处理，也可以分别分配并由相应的服务驱动程序处理。

为什么使用 PCI Express 端口总线驱动程序？
========================================

在现有的 Linux 内核中，Linux 设备驱动模型允许物理设备仅被单一驱动程序处理。PCI Express 端口是一个带有多种不同服务的 PCI-PCI 桥接设备。为了保持清晰简单的解决方案，每种服务都可能拥有自己的软件服务驱动程序。在这种情况下，多个服务驱动程序将竞争同一 PCI-PCI 桥接设备。
例如，如果 PCI Express 根端口原生热插拔服务驱动程序首先加载，则它会声明一个 PCI-PCI 桥接根端口。因此，内核不会为该根端口加载其他服务驱动程序。换句话说，使用当前的驱动程序模型，不可能让多个服务驱动程序同时加载并在 PCI-PCI 桥接设备上运行。
要实现多个服务驱动程序同时运行，需要有一个 PCI Express 端口总线驱动程序，该驱动程序管理所有存在的 PCI Express 端口，并根据需求将所有提供的服务请求分发给对应的服务驱动程序。使用 PCI Express 端口总线驱动程序的一些关键优势如下：

  - 允许多个服务驱动程序在同一 PCI-PCI 桥接端口设备上同时运行
- 允许以独立的阶段方法实现服务驱动程序
- 允许单个服务驱动程序在多个 PCI-PCI 桥接端口设备上运行
- 管理和分配 PCI-PCI 桥接端口设备的资源给请求的服务驱动程序
配置 PCI Express 端口总线驱动程序与服务驱动程序
==================================================

在内核中包含 PCI Express 端口总线驱动程序支持
--------------------------------------------------

将 PCI Express 端口总线驱动程序包含到内核中取决于内核配置中是否包含了 PCI Express 支持。当内核配置中启用了 PCI Express 支持时，内核会自动将 PCI Express 端口总线驱动程序作为内核驱动程序的一部分包含进来。

启用服务驱动程序支持
----------------------

PCI 设备驱动程序基于 Linux 设备驱动模型实现。所有的服务驱动程序都是 PCI 设备驱动程序。如上所述，一旦内核加载了 PCI Express 端口总线驱动程序，则无法再加载任何服务驱动程序。为了满足 PCI Express 端口总线驱动程序模型的要求，现有的服务驱动程序需要进行一些最小化更改，这些更改不会影响现有服务驱动程序的功能性。

服务驱动程序需要使用下面两个 API 来向 PCI Express 端口总线驱动程序注册其服务（参见第 5.2.1 和 5.2.2 节）。重要的是，在调用这些 API 之前，服务驱动程序必须初始化 `pcie_port_service_driver` 数据结构，该数据结构包含在头文件 `/include/linux/pcieport_if.h` 中。否则会导致身份不匹配，这会阻止 PCI Express 端口总线驱动程序加载服务驱动程序。

`pcie_port_service_register`
~~~~~~~~~~~~~~~~~~~~~~~~~~~
```c
int pcie_port_service_register(struct pcie_port_service_driver *new)
```

此 API 替代了 Linux 驱动模型中的 `pci_register_driver` API。服务驱动程序应在模块初始化时始终调用 `pcie_port_service_register`。需要注意的是，加载服务驱动程序后，像 `pci_enable_device(dev)` 和 `pci_set_master(dev)` 这样的调用不再必要，因为这些操作由 PCI 端口总线驱动程序执行。

`pcie_port_service_unregister`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```c
void pcie_port_service_unregister(struct pcie_port_service_driver *new)
```

`pcie_port_service_unregister` 替代了 Linux 驱动模型中的 `pci_unregister_driver`。当模块退出时，服务驱动程序始终应调用它。

示例代码
~~~~~~~~
下面是用于初始化端口服务驱动程序数据结构的示例服务驱动程序代码：
```c
static struct pcie_port_service_id service_id[] = { {
  .vendor = PCI_ANY_ID,
  .device = PCI_ANY_ID,
  .port_type = PCIE_RC_PORT,
  .service_type = PCIE_PORT_SERVICE_AER,
}, { /* end: all zeroes */ }
};

static struct pcie_port_service_driver root_aerdrv = {
  .name          = (char *)device_name,
  .id_table      = &service_id[0],

  .probe         = aerdrv_load,
  .remove        = aerdrv_unload,

  .suspend       = aerdrv_suspend,
  .resume        = aerdrv_resume,
};
```

下面是注册/注销服务驱动程序的示例代码：
```c
static int __init aerdrv_service_init(void)
{
  int retval = 0;

  retval = pcie_port_service_register(&root_aerdrv);
  if (!retval) {
    /*
    * 修复我
    */
  }
  return retval;
}

static void __exit aerdrv_service_exit(void)
{
  pcie_port_service_unregister(&root_aerdrv);
}

module_init(aerdrv_service_init);
module_exit(aerdrv_service_exit);
```

可能的资源冲突
=================
由于允许 PCI-PCI 桥接端口设备的所有服务驱动程序同时运行，以下列出了一些可能的资源冲突及其建议解决方案：
### MSI 和 MSI-X 向量资源

一旦在设备上启用了 MSI 或 MSI-X 中断，它将保持在此模式下直到再次禁用。由于同一 PCI-PCI 桥接端口的服务驱动程序共享相同的物理设备，如果某个服务驱动程序启用或禁用了 MSI/MSI-X 模式，则可能会导致不可预测的行为。
为了避免这种情况，所有服务驱动程序均不允许在其设备上切换中断模式。PCI Express 端口总线驱动程序负责确定中断模式，并且这应当对服务驱动程序透明。服务驱动程序只需知道分配给 `struct pcie_device` 结构体中 `irq` 字段的向量 IRQ，该值会在 PCI Express 端口总线驱动程序探测每个服务驱动程序时传递。服务驱动程序应使用 `(struct pcie_device*)dev->irq` 来调用 `request_irq/free_irq`。此外，中断模式存储在 `struct pcie_device` 的 `interrupt_mode` 字段中。

### PCI 内存/IO 映射区域

PCI Express 功率管理（PME）、高级错误报告（AER）、热插拔（HP）和虚拟通道（VC）的服务驱动程序访问 PCI Express 端口上的 PCI 配置空间。在所有情况下，所访问的寄存器都是相互独立的。此补丁假设所有服务驱动程序都会表现良好，不会覆盖其他服务驱动程序的配置设置。

### PCI 配置寄存器

除了 PCI Express 能力结构外，每个服务驱动程序都在自己的能力结构上运行其 PCI 配置操作；PCI Express 能力结构被多个驱动程序（包括服务驱动程序）共享。
RMW 能力访问器（`pcie_capability_clear_and_set_word()`、`pcie_capability_set_word()` 和 `pcie_capability_clear_word()`）保护一组选定的 PCI Express 能力寄存器（链路控制寄存器和根控制寄存器）。对这些寄存器的任何更改都应使用 RMW 访问器来避免并发更新引起的问题。对于受保护寄存器的最新列表，请参阅 `pcie_capability_clear_and_set_word()`。
