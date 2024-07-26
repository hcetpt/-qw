SPDX 许可证标识符: GPL-2.0

==============================
如何编写 Linux 的 PCI 驱动程序
==============================

:作者: - Martin Mares <mj@ucw.cz>
          - Grant Grundler <grundler@parisc-linux.org>

PCI 的世界广阔且充满了（大部分是不愉快的）惊喜。由于每个 CPU 架构实现了不同的芯片组，而 PCI 设备又有不同的需求（或者说，“特性”），结果就是 Linux 内核中的 PCI 支持并不像人们希望的那样简单。这篇简短的文章试图向所有潜在的驱动程序作者介绍 Linux 为 PCI 设备驱动提供的 API。
一个更完整的资源是 Jonathan Corbet、Alessandro Rubini 和 Greg Kroah-Hartman 共同编写的《Linux 设备驱动程序》第三版。
LDD3 可以免费获取（遵循 Creative Commons 许可证）：
https://lwn.net/Kernel/LDD3/
但是，请记住所有文档都可能随时间“老化”。
如果本文描述的内容与实际不符，请参考源代码。
关于 Linux PCI API 的问题、评论或补丁，请发送到
"Linux PCI" <linux-pci@atrey.karlin.mff.cuni.cz> 邮件列表。

PCI 驱动程序的结构
========================

PCI 驱动程序通过 `pci_register_driver()` “发现”系统中的 PCI 设备。实际上，事情发生的顺序正好相反：当 PCI 通用代码发现了一个新设备时，与该设备“描述”匹配的驱动程序将会被通知。具体细节如下。
`pci_register_driver()`将大部分设备探测工作留给PCI层，并支持设备的在线插入和移除（因此可以在单一驱动中支持热插拔PCI、CardBus和Express-Card）。

调用`pci_register_driver()`需要传递一个函数指针表，这决定了驱动程序的高级结构。一旦驱动程序了解了一个PCI设备并取得了所有权，通常需要执行以下初始化步骤：

  - 启用设备
  - 请求MMIO/IOP资源
  - 设置DMA掩码大小（适用于一致性和流式DMA）
  - 分配并初始化共享控制数据（使用`pci_allocate_coherent()`）
  - 访问设备配置空间（如果需要）
  - 注册IRQ处理器（使用`request_irq()`）
  - 初始化非PCI部分（例如LAN/SCSI等芯片的部分）
  - 启用DMA/处理引擎

当不再使用设备，或者模块需要卸载时，驱动程序需要执行以下步骤：

  - 禁止设备生成IRQ
  - 释放IRQ（使用`free_irq()`）
  - 停止所有DMA活动
  - 释放DMA缓冲区（包括流式和一致性）
  - 从其他子系统注销（例如scsi或netdev）
  - 释放MMIO/IOP资源
  - 禁用设备

这些主题中的大多数在接下来的部分中都有覆盖，其他未提及的内容可以参考LDD3或<linux/pci.h>。
如果PCI子系统没有配置（即CONFIG_PCI没有设置），下面描述的大多数PCI函数定义为内联函数，通常是空的或者只返回适当的错误代码，以避免在驱动程序中出现大量的条件编译指令。

### `pci_register_driver()`调用

PCI设备驱动程序在其初始化期间通过指向描述驱动程序的结构（`struct pci_driver`）来调用`pci_register_driver()`。

.. kernel-doc:: include/linux/pci.h
   :functions: pci_driver

ID表是一个以全零项结束的`struct pci_device_id`条目数组。建议使用静态const定义。
.. kernel-doc:: include/linux/mod_devicetable.h
   :functions: pci_device_id

大多数驱动程序只需要使用`PCI_DEVICE()`或`PCI_DEVICE_CLASS()`来设置pci_device_id表。
新的PCI ID可以在运行时动态添加到设备驱动程序的pci_ids表中，如下所示：

```bash
echo "vendor device subvendor subdevice class class_mask driver_data" > \
/sys/bus/pci/drivers/{driver}/new_id
```

所有字段都作为十六进制值（无前导0x）传递。vendor和device字段是必需的，其他字段是可选的。用户只需传递必要的可选字段：

  - subvendor和subdevice字段默认为PCI_ANY_ID（FFFFFFFF）
  - class和classmask字段默认为0
  - driver_data默认为0UL
  - override_only字段默认为0
请注意，`driver_data` 必须与驱动程序中定义的任何 `pci_device_id` 条目中的值匹配。这意味着如果所有 `pci_device_id` 条目都有非零的 `driver_data` 值，则 `driver_data` 字段是强制性的。
一旦添加后，对于其（新更新的）`pci_ids` 列表中列出的任何未声明的 PCI 设备，将调用驱动程序探测例程。
当驱动程序退出时，只需调用 `pci_unregister_driver()`，PCI 层会自动为驱动程序处理的所有设备调用移除钩子。

**驱动程序功能/数据的“属性”**

----------------------------------------------------------------------

请在适当的地方标记初始化和清理函数（相应的宏定义在 `<linux/init.h>` 中）：

	======		=================================================
	__init		初始化代码。在驱动程序初始化后被丢弃
__exit		退出代码。对于非模块化驱动程序会被忽略
======		=================================================

何时何地使用上述属性的小贴士：
	- `module_init()` 和 `module_exit()` 函数（以及仅从这些函数调用的所有
	  初始化函数）
	  应该标记为 `__init` / `__exit`
- 不要标记 `struct pci_driver`
- 如果不确定使用哪种标记，请不要标记该函数
不标记函数总比错误地标记函数好
如何手动查找 PCI 设备
========================

PCI 驱动程序应该有充分的理由不使用 `pci_register_driver()` 接口来搜索 PCI 设备。
PCI 设备由多个驱动程序控制的主要原因是单个 PCI 设备实现了几种不同的硬件服务。

例如，一个集成的串行/并行端口/软盘控制器。

可以使用以下结构进行手动搜索：

通过供应商和设备ID进行搜索：

```c
struct pci_dev *dev = NULL;
while ((dev = pci_get_device(VENDOR_ID, DEVICE_ID, dev)) != NULL)
    configure_device(dev);
```

通过类ID进行搜索（以类似方式迭代）：

```c
pci_get_class(CLASS_ID, dev)
```

同时通过供应商/设备ID以及子系统供应商/设备ID进行搜索：

```c
pci_get_subsys(VENDOR_ID, DEVICE_ID, SUBSYS_VENDOR_ID, SUBSYS_DEVICE_ID, dev)
```

您可以使用常量 `PCI_ANY_ID` 作为 `VENDOR_ID` 或 `DEVICE_ID` 的通配符替换。这允许您搜索特定供应商的任何设备。

这些函数支持热插拔安全。它们会增加返回的 `pci_dev` 的引用计数。您最终需要（可能在模块卸载时）通过调用 `pci_dev_put()` 来减少这些设备的引用计数。

设备初始化步骤
================

如介绍中所述，大多数 PCI 驱动程序需要以下步骤来初始化设备：

  - 启用设备
  - 请求 MMIO/IOP 资源
  - 设置 DMA 掩码大小（对于一致性和流式 DMA）
  - 分配并初始化共享控制数据（`pci_allocate_coherent()`）
  - 访问设备配置空间（如果需要）
  - 注册中断处理程序（`request_irq()`）
  - 初始化非 PCI（即 LAN/SCSI 等芯片的部分）
  - 启用 DMA/处理引擎

驱动程序可以在任何时候访问 PCI 配置空间寄存器
（好吧，几乎任何时候。当运行内置自检时，配置空间可能会消失……但这只会导致 PCI 总线主控器中止，并且配置读取将返回无效值）

启用 PCI 设备
---------------------
在接触任何设备寄存器之前，驱动程序需要通过调用 `pci_enable_device()` 来启用 PCI 设备。这将会：

  - 如果设备处于挂起状态，则将其唤醒，
  - 分配设备的 I/O 和内存区域（如果 BIOS 没有这样做的话），
  - 分配一个 IRQ（如果 BIOS 没有这样做的话）

**注意：**
`pci_enable_device()` 可能会失败！请检查返回值。
.. warning::
   **操作系统BUG：** 在启用资源之前，我们没有检查资源分配。如果在调用 `pci_enable_device()` 之前调用 `pci_request_resources()`，这样的顺序将更有意义。
   
   目前，设备驱动程序无法检测到当两个设备被分配了相同的地址范围时出现的错误。这不是一个常见问题，并且不太可能在短期内得到修复。
   
   这个问题以前讨论过，但在 2.6.19 版本中还没有改变：
   https://lore.kernel.org/r/20060302180025.GC28895@flint.arm.linux.org.uk/

`pci_set_master()` 通过设置 PCI_COMMAND 寄存器中的总线主控位来启用 DMA。如果 BIOS 设置了一个无效的延迟计时器值，它也会对其进行修正。`pci_clear_master()` 通过清除总线主控位来禁用 DMA。
   
   如果 PCI 设备可以使用 PCI 写回无效事务（PCI Memory-Write-Invalidate），则应调用 `pci_set_mwi()`。这会启用 Mem-Wr-Inval 的 PCI_COMMAND 位，并确保缓存行大小寄存器被正确设置。
   
   检查 `pci_set_mwi()` 的返回值，因为并非所有架构或芯片组都支持写回无效操作。或者，如果写回无效操作是可选而非必需的功能，可以调用 `pci_try_set_mwi()` 让系统尽力启用该功能。

请求 MMIO/IOP 资源
----------------------
不应直接从 PCI 设备配置空间读取内存（MMIO）和 I/O 端口地址。应该使用 `pci_dev` 结构体中的值，因为 PCI “总线地址” 可能已经被特定于架构/芯片组的内核支持映射到了“主机物理”地址。

请参阅 `Documentation/driver-api/io-mapping.rst` 了解如何访问设备寄存器或设备内存。

设备驱动程序需要调用 `pci_request_region()` 来确认没有其他设备正在使用相同的地址资源。

相反地，在调用 `pci_disable_device()` 之后，驱动程序应调用 `pci_release_region()`。

这样做的目的是防止两个设备在同一地址范围内发生冲突。
提示:
参见上面的OS BUG注释。当前版本（2.6.19），驱动程序只能在调用`pci_enable_device()`之后确定MMIO和I/O端口资源的可用性。
`pci_request_region()`的通用版本是`request_mem_region()`（用于MMIO范围）和`request_region()`（用于I/O端口范围）。
对于不是由“常规”PCI BAR描述的地址资源，请使用这些函数。
另请参阅下面的`pci_request_selected_regions()`。
设置DMA掩码大小
---------------------
注意:
如果以下内容难以理解，请参考`Documentation/core-api/dma-api.rst`。本节仅作为提醒，即驱动程序需要指示设备的DMA能力，并非DMA接口的权威来源。
虽然所有驱动程序都应明确指示PCI总线主控器的能力（例如32位或64位），但对于具有超过32位总线主控器能力以流式传输数据的设备，驱动程序需要通过调用`dma_set_mask()`并提供适当的参数来“注册”此能力。通常，在系统物理内存高于4GB地址的情况下，这可以实现更高效的DMA操作。
所有PCI-X和PCIe兼容设备的驱动程序必须调用`dma_set_mask()`，因为它们是64位DMA设备。
同样，如果设备可以直接寻址系统物理内存中4GB以上地址的“一致性内存”，驱动程序也必须通过调用`dma_set_coherent_mask()`来“注册”此能力。
这也包括所有PCI-X和PCIe兼容设备的驱动程序。
许多64位“PCI”设备（在PCI-X之前）和一些PCI-X设备对于负载（“流式”）数据具有64位DMA能力，但对控制（“一致性”）数据不具备这种能力。
设置共享控制数据
-------------------------
一旦DMA屏蔽被设置，驱动程序就可以分配“一致性”（也称为共享）内存。关于DMA API的完整描述，请参阅Documentation/core-api/dma-api.rst。本节仅作为提醒，在启用设备上的DMA之前需要完成此步骤。
初始化设备寄存器
---------------------------
某些驱动程序可能需要对特定的“能力”字段进行编程，或者初始化或重置其他“厂商特定”的寄存器。
例如，清除挂起的中断。
注册IRQ处理程序
--------------------
虽然调用request_irq()是这里描述的最后一步，但这通常只是初始化设备的另一个中间步骤。
此步骤可以推迟到设备被打开使用时再执行。
所有IRQ线程的中断处理程序都应使用IRQF_SHARED进行注册，并使用设备ID来映射IRQ到设备（请记住，所有的PCI IRQ线都可以共享）。
request_irq()会将一个中断处理程序和设备句柄与一个中断编号关联起来。从历史上看，中断编号代表了从PCI设备到中断控制器的IRQ线。
对于MSI和MSI-X（下文有更多介绍），中断编号是一个CPU“向量”。
request_irq()还会启用中断。在注册中断处理程序之前，请确保设备处于静止状态并且没有挂起的中断。
MSI和MSI-X是PCI功能。两者都是“消息指示中断”，通过DMA写入本地APIC向CPU发送中断。
MSI 和 MSI-X 之间的根本区别在于如何分配多个“向量”。MSI 需要连续的向量块，而 MSI-X 可以分配几个独立的向量。

可以通过在调用 `request_irq()` 之前使用 `pci_alloc_irq_vectors()` 函数并指定 `PCI_IRQ_MSI` 和/或 `PCI_IRQ_MSIX` 标志来启用 MSI 功能。这将导致 PCI 支持程序将 CPU 向量数据编程到 PCI 设备的能力寄存器中。许多架构、芯片组或 BIOS 不支持 MSI 或 MSI-X，因此仅使用 `PCI_IRQ_MSI` 和 `PCI_IRQ_MSIX` 标志调用 `pci_alloc_irq_vectors` 会失败，所以尽量同时指定 `PCI_IRQ_INTX`。

对于拥有不同中断处理器（MSI/MSI-X 和传统 INTx）的驱动程序，应在调用 `pci_alloc_irq_vectors` 之后根据 `pci_dev` 结构中的 `msi_enabled` 和 `msix_enabled` 标志选择正确的处理器。

使用 MSI 的原因至少有两个非常充分的理由：

1. 根据定义，MSI 是一个独占的中断向量。
这意味着中断处理器不需要验证是该设备产生了中断。
2. MSI 避免了 DMA/IRQ 竞态条件。当 MSI 发送时，确保了对主机内存的 DMA 操作对主机 CPU 可见。这对于数据一致性以及避免陈旧的控制数据都非常重要。
这一保证允许驱动程序省略用于刷新 DMA 流的 MMIO 读取操作。

请参阅 `drivers/infiniband/hw/mthca/` 或 `drivers/net/tg3.c` 中 MSI/MSI-X 使用的例子。

PCI 设备关闭
=============

当卸载 PCI 设备驱动程序时，通常需要执行以下步骤中的大部分：

- 禁止设备生成 IRQs
- 释放 IRQ (`free_irq()`)
- 停止所有 DMA 活动
- 释放 DMA 缓冲区（包括流式和一致缓冲区）
- 从其他子系统注销（例如 SCSI 或 netdev）
- 禁止设备响应 MMIO/IO 端口地址
- 释放 MMIO/IO 端口资源

停止设备上的 IRQs
-------------------
如何做到这一点取决于具体的芯片/设备。如果不这样做，则存在“尖叫中断”的可能性（且仅当 IRQ 与另一个设备共享时）。

当共享 IRQ 处理器被“解钩”后，使用相同 IRQ 线路的剩余设备仍然需要保持 IRQ 启用状态。因此如果“解钩”的设备激活 IRQ 线路，系统会假设是剩余的某个设备触发了 IRQ 线路并作出响应。由于没有其他设备处理此 IRQ，系统会“挂起”直到决定 IRQ 不会被处理并屏蔽 IRQ（大约 100,000 次迭代后）。一旦共享 IRQ 被屏蔽，剩余的设备将无法正常工作。这不是一个好的情况。
这是另一个使用MSI或MSI-X的理由，如果可用的话。
MSI和MSI-X被定义为互斥中断，因此
它们不容易受到“尖叫中断”问题的影响。
释放IRQ
------
一旦设备处于静止状态（不再有IRQ），就可以调用free_irq()函数
这个函数会在处理完任何待处理的IRQ后返回控制权，
“解除挂钩”驱动程序的IRQ处理程序与该IRQ的关联，并最终在没有人使用的情况下释放IRQ。
停止所有DMA活动
-----------------
在尝试取消分配DMA控制数据之前极其重要的是要停止所有的DMA操作。如果不这样做可能会导致内存损坏、挂起，以及在某些芯片组上发生硬崩溃。
在停止IRQ之后停止DMA可以避免IRQ处理程序可能重新启动DMA引擎的竞争情况。
虽然这一步听起来显而易见且微不足道，但过去有几个“成熟的”驱动程序并没有正确地执行这一步。
释放DMA缓冲区
-----------------
一旦DMA停止，首先清理流式DMA
即，取消映射数据缓冲区并将其返回给“上游”所有者（如果有）。
然后清理包含控制数据的“一致性”缓冲区。
查看 Documentation/core-api/dma-api.rst 以获取有关取消映射接口的详细信息。
取消在其他子系统的注册
-----------------------------
大多数低级别的 PCI 设备驱动程序支持一些其他的子系统，
如 USB、ALSA、SCSI、NetDev、InfiniBand 等。请确保您的驱动程序不会从这些其他子系统中丢失资源。
如果发生这种情况，通常的症状是在子系统尝试调用已卸载的驱动程序时出现 Oops（恐慌）。
禁用设备对 MMIO/IO 端口地址的响应
----------------------------------------------------
使用 io_unmap() 取消 MMIO 或 IO 端口资源的映射，然后调用 pci_disable_device()。
这是 pci_enable_device() 的对称相反操作。
在调用 pci_disable_device() 后不要访问设备寄存器。
释放 MMIO/IO 端口资源
---------------------------------
调用 pci_release_region() 来标记 MMIO 或 IO 端口范围为可用状态。
如果不这样做，通常会导致无法重新加载驱动程序。
如何访问 PCI 配置空间
==============================
您可以使用 `pci_(read|write)_config_(byte|word|dword)` 来访问由 `struct pci_dev *` 表示的设备的配置空间。
所有这些函数在成功时返回 0 或错误代码 (`PCIBIOS_...`)，这些错误代码可以通过 pcibios_strerror 转换为文本字符串。
大多数驱动程序期望对有效 PCI 设备的访问不会失败。
如果您没有可用的 struct pci_dev，可以调用 `pci_bus_(read|write)_config_(byte|word|dword)` 来访问该总线上的指定设备和功能。
如果你需要访问配置头标准部分中的字段，请使用在 `<linux/pci.h>` 中声明的位置和位的符号名称。
如果你需要访问扩展PCI功能寄存器，只需调用 `pci_find_capability()` 函数来查找特定的功能，它会为你找到相应的寄存器块。

其他有趣的函数
===========================

| 函数名 | 描述 |
| --- | --- |
| `pci_get_domain_bus_and_slot()` | 根据给定的域、总线和插槽编号查找对应的 `pci_dev`。如果找到该设备，则增加其引用计数。 |
| `pci_set_power_state()` | 设置 PCI 功率管理状态（0=D0 ... 3=D3）。 |
| `pci_find_capability()` | 在设备的能力列表中查找指定的功能。 |
| `pci_resource_start()` | 返回给定 PCI 区域的总线起始地址。 |
| `pci_resource_end()` | 返回给定 PCI 区域的总线结束地址。 |
| `pci_resource_len()` | 返回 PCI 区域的字节长度。 |
| `pci_set_drvdata()` | 为 `pci_dev` 设置私有驱动数据指针。 |
| `pci_get_drvdata()` | 返回 `pci_dev` 的私有驱动数据指针。 |
| `pci_set_mwi()` | 启用内存写无效事务。 |
| `pci_clear_mwi()` | 禁用内存写无效事务。 |

杂项提示
==================

当向用户显示 PCI 设备名称时（例如，当驱动程序想要告诉用户已找到什么卡时），请使用 `pci_name(pci_dev)`。
始终通过指向 `pci_dev` 结构体的指针来引用 PCI 设备。
所有 PCI 层函数都使用这种标识方式，这是唯一合理的方式。除了非常特殊的情况外，不要使用总线/插槽/功能编号——在具有多个主总线的系统上，它们的语义可能相当复杂。
不要尝试在你的驱动程序中启用快速连续写操作。总线上所有的设备都需要能够执行此操作，因此这应该由平台和通用代码处理，而不是个别驱动程序。
供应商和设备标识
=================

除非多个驱动程序共享这些标识，否则请不要向`include/linux/pci_ids.h`中添加新的设备或供应商ID。如果这些定义对您的驱动程序有帮助，您可以在驱动程序中添加私有定义，或者直接使用纯十六进制常量。
设备ID是任意的十六进制数字（由供应商控制），通常只在一个位置——`pci_device_id`表中使用。
请务必提交新的供应商/设备ID至 https://pci-ids.ucw.cz/
有一个`pci.ids`文件的镜像位于 https://github.com/pciutils/pciids

过时的函数
===========

在尝试将旧驱动程序移植到新PCI接口时，您可能会遇到一些已经不再使用的函数。这些函数已从内核中移除，因为它们与热插拔、PCI域或合理的锁机制不兼容。

| 过时函数        | 替代函数                          |
|----------------|----------------------------------|
| `pci_find_device()` | 被`pci_get_device()`取代         |
| `pci_find_subsys()` | 被`pci_get_subsys()`取代         |
| `pci_find_slot()`   | 被`pci_get_domain_bus_and_slot()`取代 |
| `pci_get_slot()`    | 被`pci_get_domain_bus_and_slot()`取代 |

传统的PCI设备驱动程序仍然可以遍历PCI设备列表，但这并不鼓励。
内存映射I/O空间与“写入延迟”
=================================

从使用I/O端口空间转换为使用内存映射I/O (MMIO) 空间时，通常需要进行一些额外的更改。特别是，需要处理“写入延迟”。许多驱动程序（例如tg3、acenic、sym53c8xx_2）已经这样做了。I/O端口空间保证写入交易在CPU继续执行其他操作之前到达PCI设备。写入MMIO空间允许CPU在交易到达PCI设备之前继续执行。硬件工程师称这种现象为“写入延迟”，因为写完成是在交易达到目的地之前“发布”给CPU的。
因此，对于时间敏感的代码，应在预期CPU等待执行其他工作的地方添加`readl()`调用。对于I/O端口空间的经典“位敲打”序列如下：

```c
for (i = 8; --i; val >>= 1) {
    outb(val & 1, ioport_reg);      /* 写入位 */
    udelay(10);
}
```

对于MMIO空间，相同的序列应为：

```c
for (i = 8; --i; val >>= 1) {
    writeb(val & 1, mmio_reg);      /* 写入位 */
    readb(safe_mmio_reg);           /* 刷新延迟写入 */
    udelay(10);
}
```

重要的是，“safe_mmio_reg”不应有任何干扰设备正确运行的副作用。
还需要注意的一个情况是在重置PCI设备时。使用PCI配置空间读取来刷新`writel()`调用。这将在所有平台上优雅地处理PCI主中止，如果PCI设备预计不会响应`readl()`调用。大多数x86平台将允许MMIO读取主中止（也称为“软失败”），并返回垃圾值（例如~0）。但许多RISC平台会崩溃（也称为“硬失败”）。
