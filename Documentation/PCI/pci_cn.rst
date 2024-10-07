SPDX 许可证标识符: GPL-2.0

==============================
如何编写 Linux PCI 驱动程序
==============================

:作者: - Martin Mares <mj@ucw.cz>
          - Grant Grundler <grundler@parisc-linux.org>

PCI 的世界非常广阔，充满了（大多是不愉快的）惊喜。由于每个 CPU 架构实现不同的芯片组，并且 PCI 设备有不同的要求（或者说，“特性”），结果是 Linux 内核中的 PCI 支持并不像人们希望的那样简单。这篇短文试图向所有潜在的驱动程序作者介绍 Linux 的 PCI 设备驱动程序 API。
更完整的资源是 Jonathan Corbet、Alessandro Rubini 和 Greg Kroah-Hartman 编写的《Linux 设备驱动程序》第三版。
《Linux 设备驱动程序》第三版可以从以下网址免费获取（在 Creative Commons 许可证下）：
https://lwn.net/Kernel/LDD3/
但是，请记住所有文档都有“老化”的风险。
如果描述的情况与实际不符，请参考源代码。
请将关于 Linux PCI API 的问题、评论和补丁发送到 “Linux PCI” <linux-pci@atrey.karlin.mff.cuni.cz> 邮件列表。

PCI 驱动程序结构
========================
PCI 驱动程序通过 `pci_register_driver()` 发现系统中的 PCI 设备。
实际上，情况正好相反。当 PCI 通用代码发现一个新设备时，具有匹配“描述”的驱动程序将会被通知。
下面会详细介绍这一过程。
`pci_register_driver()` 大部分设备探测工作交由 PCI 层处理，并支持设备的在线插入和移除（从而在一个驱动中支持热插拔 PCI、CardBus 和 Express-Card）。

`pci_register_driver()` 调用需要传入一个函数指针表，这决定了驱动程序的高层结构。
一旦驱动程序知晓并接管了一个 PCI 设备，通常需要执行以下初始化步骤：

- 启用设备
- 请求 MMIO/IOP 资源
- 设置 DMA 掩码大小（对于一致性和流式 DMA）
- 分配并初始化共享控制数据（`pci_allocate_coherent()`）
- 访问设备配置空间（如果需要）
- 注册中断处理程序（`request_irq()`）
- 初始化非 PCI 部分（例如 LAN/SCSI 等芯片的部分）
- 启用 DMA/处理引擎

当不再使用该设备时，或者模块需要卸载时，驱动程序需要采取以下步骤：

- 禁止设备生成中断
- 释放中断（`free_irq()`）
- 停止所有 DMA 活动
- 释放 DMA 缓冲区（包括流式和一致性）
- 从其他子系统注销（例如 scsi 或 netdev）
- 释放 MMIO/IOP 资源
- 禁用设备

这些主题中的大部分在后续章节中有详细说明。其余内容可以参考 LDD3 或 `<linux/pci.h>`。
如果 PCI 子系统没有配置（`CONFIG_PCI` 没有设置），则下面描述的大多数 PCI 函数定义为内联函数，要么完全为空，要么只返回适当的错误代码以避免驱动程序中的大量 `#ifdef`。

`pci_register_driver()` 调用
==========================

PCI 设备驱动程序在其初始化期间通过指向描述驱动程序的结构（`struct pci_driver`）来调用 `pci_register_driver()`：

```plaintext
.. kernel-doc:: include/linux/pci.h
   :functions: pci_driver
```

ID 表是一个 `struct pci_device_id` 入口数组，以全零入口结束。通常推荐使用静态常量定义。
```plaintext
.. kernel-doc:: include/linux/mod_devicetable.h
   :functions: pci_device_id
```

大多数驱动程序只需要 `PCI_DEVICE()` 或 `PCI_DEVICE_CLASS()` 来设置 `pci_device_id` 表。
新的 PCI ID 可以在运行时添加到设备驱动程序的 `pci_ids` 表中，如下所示：

```plaintext
echo "vendor device subvendor subdevice class class_mask driver_data" > \
/sys/bus/pci/drivers/{driver}/new_id
```

所有字段都作为十六进制值传递（不带前导 0x）。vendor 和 device 字段是必需的，其他字段是可选的。用户只需传递必要的可选字段：

- subvendor 和 subdevice 字段默认为 PCI_ANY_ID（FFFFFFFF）
- class 和 classmask 字段默认为 0
- driver_data 默认为 0UL
- override_only 字段默认为 0
请注意，`driver_data` 必须与驱动程序中定义的任何 `pci_device_id` 条目所使用的值匹配。这意味着如果所有 `pci_device_id` 条目都有一个非零的 `driver_data` 值，则 `driver_data` 字段是必需的。一旦添加，驱动程序的探测例程将被调用以处理其（新更新的）`pci_ids` 列表中的所有未声明的 PCI 设备。

当驱动程序退出时，只需调用 `pci_unregister_driver()`，PCI 层会自动为由该驱动程序处理的所有设备调用移除钩子函数。

### 驱动程序功能/数据的“属性”

------------------------------------------------------

请在适当的地方标记初始化和清理函数（相应的宏在 `<linux/init.h>` 中定义）：

======		=================================================
__init		初始化代码。在驱动程序初始化后会被丢弃
__exit		退出代码。对于非模块化驱动程序会被忽略
======		=================================================

关于何时何地使用上述属性的提示：
- `module_init()` 和 `module_exit()` 函数（以及仅从这些函数调用的所有初始化函数）应标记为 `__init` / `__exit`
- 不要标记 `struct pci_driver`
- 如果不确定应该使用哪个标记，请不要标记该函数。与其错误地标记函数，不如不标记

如何手动查找 PCI 设备
=====================

PCI 驱动程序应该有充分的理由不使用 `pci_register_driver()` 接口来搜索 PCI 设备。
PCI 设备由多个驱动程序控制的主要原因是单个 PCI 设备实现了多种不同的硬件服务。例如，组合的串行/并行端口/软盘控制器。

可以使用以下结构进行手动搜索：

通过供应商和设备 ID 搜索：

```c
struct pci_dev *dev = NULL;
while ((dev = pci_get_device(VENDOR_ID, DEVICE_ID, dev)) != NULL)
    configure_device(dev);
```

通过类 ID 搜索（以类似的方式迭代）：

```c
pci_get_class(CLASS_ID, dev)
```

同时通过供应商/设备 ID 和子系统供应商/设备 ID 搜索：

```c
pci_get_subsys(VENDOR_ID, DEVICE_ID, SUBSYS_VENDOR_ID, SUBSYS_DEVICE_ID, dev)
```

您可以使用常量 PCI_ANY_ID 作为 VENDOR_ID 或 DEVICE_ID 的通配符替换。这允许搜索特定供应商的所有设备。

这些函数是热插拔安全的。它们会增加返回的 pci_dev 的引用计数。您必须在某个时刻（可能是在模块卸载时）通过调用 pci_dev_put() 减少这些设备的引用计数。

设备初始化步骤
===========================

如引言中所述，大多数 PCI 驱动程序需要以下步骤来初始化设备：

  - 启用设备
  - 请求 MMIO/IOP 资源
  - 设置 DMA 掩码大小（对于一致性和流式 DMA）
  - 分配并初始化共享控制数据（pci_allocate_coherent()）
  - 访问设备配置空间（如果需要）
  - 注册中断处理程序（request_irq()）
  - 初始化非 PCI（即 LAN/SCSI 等芯片的部分）
  - 启用 DMA/处理引擎

驱动程序可以在任何时候访问 PCI 配置空间寄存器（嗯，几乎任何时候。当运行 BIST 时，配置空间可能会消失……但这只会导致 PCI 总线主控中止，并且配置读取将返回垃圾数据）

启用 PCI 设备
---------------------
在访问任何设备寄存器之前，驱动程序需要通过调用 pci_enable_device() 来启用 PCI 设备。这将执行以下操作：

  - 如果设备处于挂起状态，则将其唤醒，
  - 分配设备的 I/O 和内存区域（如果 BIOS 没有这样做）
  - 分配一个 IRQ（如果 BIOS 没有这样做）

注意：
   pci_enable_device() 可能会失败！请检查返回值。
.. warning::
   操作系统BUG：在启用资源之前我们不检查资源分配。如果在调用 `pci_enable_device()` 之前先调用 `pci_request_resources()`，这个顺序会更合理。
   目前，设备驱动程序无法检测到两个设备被分配了相同地址范围的情况。这不是一个常见的问题，并且不太可能很快得到修复。
   这个问题以前讨论过，但在 2.6.19 版本中仍未更改：
   <https://lore.kernel.org/r/20060302180025.GC28895@flint.arm.linux.org.uk/>

`pci_set_master()` 通过设置 PCI_COMMAND 寄存器中的总线主控位来启用 DMA。如果 BIOS 设置了一个无效的延迟计时器值，它也会修复该值。`pci_clear_master()` 通过清除总线主控位来禁用 DMA。
如果 PCI 设备可以使用 PCI 写无效事务（PCI Memory-Write-Invalidate），请调用 `pci_set_mwi()`。这会启用 PCI_COMMAND 中的 Mem-Wr-Inval 位，并确保缓存行大小寄存器设置正确。
检查 `pci_set_mwi()` 的返回值，因为并非所有架构或芯片组都支持 Memory-Write-Invalidate。或者，如果 Mem-Wr-Inval 是可选的但不是必需的，可以调用 `pci_try_set_mwi()` 来让系统尽力启用 Mem-Wr-Inval。

请求 MMIO/IOP 资源
--------------------------
内存（MMIO）和 I/O 端口地址不应直接从 PCI 设备配置空间读取。应使用 `pci_dev` 结构中的值，因为 PCI “总线地址” 可能已被特定架构/芯片组的内核支持重映射为 “主机物理” 地址。
有关如何访问设备寄存器或设备内存，请参阅 `Documentation/driver-api/io-mapping.rst`。
设备驱动程序需要调用 `pci_request_region()` 来验证没有其他设备已经在使用相同的地址资源。
相反地，驱动程序应在调用 `pci_disable_device()` 之后调用 `pci_release_region()`。
这样做的目的是防止两个设备在同一地址范围内发生冲突。
提示:
请参阅上面的OS BUG注释。目前（2.6.19），驱动程序只能在调用pci_enable_device()之后确定MMIO和I/O端口资源的可用性。
通用的pci_request_region()函数包括request_mem_region()（用于MMIO范围）和request_region()（用于I/O端口范围）。
对于那些不通过“正常”PCI BAR描述的地址资源，请使用这些函数。
另请参阅下面的pci_request_selected_regions()。
设置DMA掩码大小
---------------------
注意:
如果以下内容有任何不清楚的地方，请参考Documentation/core-api/dma-api.rst。本节只是提醒驱动程序需要指示设备的DMA能力，并不是DMA接口的权威来源。
所有驱动程序都应该明确指示PCI总线主控器的DMA能力（例如32位或64位）。对于具有超过32位总线主控器能力以流式传输数据的设备，驱动程序需要通过调用dma_set_mask()并传入适当的参数来“注册”这种能力。通常情况下，这允许在系统物理内存高于4G地址时更高效地进行DMA操作。
所有PCI-X和PCIe兼容设备的驱动程序必须调用dma_set_mask()，因为它们是64位DMA设备。
同样，如果设备可以直接寻址系统内存中物理地址高于4G的“一致内存”，驱动程序也必须通过调用dma_set_coherent_mask()来“注册”这种能力。
这同样包括所有PCI-X和PCIe兼容设备的驱动程序。
许多64位“PCI”设备（在PCI-X之前）和一些PCI-X设备可以对有效负载（“流式”）数据进行64位DMA，但不能对控制（“一致”）数据进行64位DMA。
设置共享控制数据
-------------------------
一旦DMA掩码设置完毕，驱动程序就可以分配“一致性”（也称为共享）内存。有关DMA API的完整描述，请参阅Documentation/core-api/dma-api.rst。本节只是提醒在启用设备的DMA之前需要完成此步骤。
初始化设备寄存器
---------------------------
某些驱动程序可能需要编程特定的“功能”字段或初始化其他“厂商特定”的寄存器或重置它们。
例如，清除挂起的中断。
注册IRQ处理程序
--------------------
尽管调用request_irq()是这里描述的最后一步，但这通常只是初始化设备的另一个中间步骤。
此步骤可以推迟到设备被打开使用时再执行。
所有IRQ线程的中断处理程序都应使用IRQF_SHARED标志进行注册，并使用devid将IRQ映射到设备（请记住所有PCI IRQ线都可以共享）。
request_irq()会将一个中断处理程序和设备句柄与一个中断编号关联起来。历史上中断编号代表从PCI设备到中断控制器的IRQ线。
通过MSI和MSI-X（下文详述），中断编号是一个CPU“向量”。
request_irq()还会启用中断。确保在注册中断处理程序之前设备已处于静止状态且没有挂起的中断。
MSI和MSI-X是PCI功能。两者都是“消息触发中断”，通过DMA写入本地APIC向CPU传递中断。
MSI（消息信号中断）和MSI-X之间的根本区别在于多个“向量”是如何分配的。MSI要求连续的向量块，而MSI-X可以分配几个单独的向量。

可以通过在调用`request_irq()`之前，使用`pci_alloc_irq_vectors()`函数并传递`PCI_IRQ_MSI`和/或`PCI_IRQ_MSIX`标志来启用MSI功能。这会导致PCI支持将CPU向量数据编程到PCI设备的能力寄存器中。许多架构、芯片组或BIOS不支持MSI或MSI-X，因此仅使用`PCI_IRQ_MSI`和`PCI_IRQ_MSIX`标志调用`pci_alloc_irq_vectors`会失败，所以请尽量同时指定`PCI_IRQ_INTX`。

对于具有不同中断处理程序（MSI/MSI-X和传统INTx）的驱动程序，应在调用`pci_alloc_irq_vectors`之后，根据`pci_dev`结构中的`msi_enabled`和`msix_enabled`标志选择合适的处理程序。

使用MSI至少有两个非常好的理由：

1. MNI本质上是一个独占的中断向量。
这意味着中断处理程序不需要验证其设备是否引起了中断。
2. MNI避免了DMA/IRQ竞争条件。当MSI被传送时，主机内存中的DMA保证对主机CPU可见。这对数据一致性以及避免陈旧控制数据非常重要。
这一保证使得驱动程序可以省略MMIO读取以刷新DMA流。

参见`drivers/infiniband/hw/mthca/`或`drivers/net/tg3.c`中的MSI/MSI-X使用示例。

PCI设备关闭
============

当卸载PCI设备驱动程序时，通常需要执行以下步骤：

- 禁用设备生成IRQ的功能
- 释放IRQ（`free_irq()`）
- 停止所有DMA活动
- 释放DMA缓冲区（包括流式和一致的）
- 从其他子系统注销（例如scsi或netdev）
- 禁用设备响应MMIO/IO端口地址
- 释放MMIO/IO端口资源

停止设备上的IRQ
----------------
具体如何操作取决于芯片/设备。如果不这样做，在共享IRQ的情况下，可能会导致“尖叫中断”。

当共享IRQ处理程序被“解钩”后，仍然使用相同IRQ线的剩余设备仍需要IRQ保持启用状态。因此，如果被“解钩”的设备激活IRQ线，系统将假定是剩余设备之一激活了IRQ线。由于没有其他设备处理IRQ，系统将“挂起”，直到决定IRQ不会被处理并屏蔽IRQ（100,000次迭代后）。一旦共享IRQ被屏蔽，剩余设备将无法正常工作。这不是一个好的情况。
这是另一个使用MSI或MSI-X的理由（如果可用的话）。
MSI和MSI-X被定义为独占中断，因此不会受到“尖叫中断”问题的影响。

释放IRQ
---------------
一旦设备处于静止状态（没有更多的IRQ），可以调用free_irq()函数。
该函数会在处理完任何待处理的IRQ后返回控制权，“解除”驱动程序的IRQ处理程序与该IRQ的关联，并最终在无人使用的情况下释放IRQ。

停止所有DMA活动
---------------------
在尝试释放DMA控制数据之前，极其重要的是先停止所有DMA操作。否则可能会导致内存损坏、系统挂起，甚至在某些芯片组上引发严重崩溃。
在停止IRQ之后停止DMA可以避免IRQ处理程序重新启动DMA引擎的情况。
尽管这一步听起来显而易见且简单，但过去有几个“成熟的”驱动程序并没有正确执行这一步骤。

释放DMA缓冲区
-------------------
一旦DMA停止，首先清理流式DMA。
即，取消映射数据缓冲区并将其返回给“上游”所有者（如果有）。
然后清理包含控制数据的“一致”缓冲区。
查看Documentation/core-api/dma-api.rst以获取取消映射接口的详细信息
从其他子系统注销
-----------------
大多数底层PCI设备驱动程序支持其他一些子系统，如USB、ALSA、SCSI、NetDev、InfiniBand等。确保您的驱动程序不会丢失来自其他子系统的资源。
如果发生这种情况，通常的症状是在子系统试图调用已卸载的驱动程序时出现Oops（恐慌）。
禁用设备对MMIO/IO端口地址的响应
--------------------------------------
调用io_unmap()来取消映射MMIO或IO端口资源，然后调用pci_disable_device()。
这是与pci_enable_device()相对称的操作。
在调用pci_disable_device()之后不要访问设备寄存器。
释放MMIO/IO端口资源
---------------------
调用pci_release_region()来标记MMIO或IO端口范围为可用。
不这样做通常会导致无法重新加载驱动程序。
如何访问PCI配置空间
=====================
您可以使用`pci_(read|write)_config_(byte|word|dword)`来访问由`struct pci_dev *`表示的设备的配置空间。所有这些函数在成功时返回0，失败时返回一个错误代码（`PCIBIOS_...`），可以通过pcibios_strerror转换为文本字符串。大多数驱动程序期望对有效PCI设备的访问不会失败。
如果您没有可用的struct pci_dev，可以调用`pci_bus_(read|write)_config_(byte|word|dword)`来访问该总线上的指定设备和功能。
如果你需要访问配置头的标准部分中的字段，请使用在 `<linux/pci.h>` 中声明的位置和位的符号名称。
如果你需要访问扩展PCI功能寄存器，只需调用 `pci_find_capability()` 来查找特定的功能，它会为你找到相应的寄存器块。

其他有趣的函数
===========================

| 函数名 | 描述 |
| --- | --- |
| `pci_get_domain_bus_and_slot()` | 查找对应于给定域、总线和插槽编号的 `pci_dev`。如果找到该设备，则增加其引用计数 |
| `pci_set_power_state()` | 设置 PCI 功率管理状态（0=D0 ... 3=D3） |
| `pci_find_capability()` | 在设备的功能列表中查找指定的功能 |
| `pci_resource_start()` | 返回给定 PCI 区域的总线起始地址 |
| `pci_resource_end()` | 返回给定 PCI 区域的总线结束地址 |
| `pci_resource_len()` | 返回 PCI 区域的字节长度 |
| `pci_set_drvdata()` | 为 `pci_dev` 设置私有驱动数据指针 |
| `pci_get_drvdata()` | 返回 `pci_dev` 的私有驱动数据指针 |
| `pci_set_mwi()` | 启用内存写无效事务 |
| `pci_clear_mwi()` | 禁用内存写无效事务 |

杂项提示
==================

当你向用户显示 PCI 设备名称时（例如，当驱动程序想要告诉用户找到了什么卡），请使用 `pci_name(pci_dev)`。
始终通过指向 `pci_dev` 结构体的指针来引用 PCI 设备。
所有 PCI 层函数都使用这种标识方式，这是唯一合理的方式。除非有非常特殊的目的，否则不要使用总线/插槽/功能编号——在具有多个主总线的系统上，这些编号的语义可能相当复杂。
不要试图在你的驱动程序中启用快速背对背写入。总线上的所有设备都需要能够执行此操作，因此这应该是由平台和通用代码处理的，而不是由各个驱动程序处理。
供应商和设备标识
=================

除非多个驱动程序共享，否则不要将新的设备或供应商ID添加到`include/linux/pci_ids.h`中。如果这些定义对你有帮助，你可以在你的驱动程序中添加私有定义，或者直接使用纯十六进制常量。设备ID是任意的十六进制数字（由供应商控制），通常只在一个位置——`pci_device_id`表中使用。

请提交新的供应商/设备ID到https://pci-ids.ucw.cz/
在https://github.com/pciutils/pciids上有一个`pci.ids`文件的镜像。

过时的功能
==================

当你尝试将旧驱动程序移植到新的PCI接口时，可能会遇到几个过时的函数。由于它们不兼容热插拔、PCI域或合理的锁定机制，因此这些函数已不再存在于内核中。
以下是替代方案：

| 过时函数 | 替代函数 |
| --- | --- |
| `pci_find_device()` | 被`pci_get_device()`取代 |
| `pci_find_subsys()` | 被`pci_get_subsys()`取代 |
| `pci_find_slot()` | 被`pci_get_domain_bus_and_slot()`取代 |
| `pci_get_slot()` | 被`pci_get_domain_bus_and_slot()`取代 |

另一种替代方案是传统的PCI设备驱动程序，它遍历PCI设备列表。虽然这仍然是可能的，但不鼓励这样做。

内存映射I/O空间和“写入延后”
==============================

将驱动程序从使用I/O端口空间转换为使用内存映射I/O (MMIO) 空间通常需要一些额外的更改。特别是，“写入延后”需要处理。许多驱动程序（如tg3、acenics、sym53c8xx_2）已经这样做了。I/O端口空间保证写入事务在CPU继续执行之前到达PCI设备。而写入MMIO空间允许CPU在事务到达PCI设备之前继续执行。硬件工程师称此为“写入延后”，因为写入完成是在事务到达目的地之前“发布”给CPU的。

因此，在时间敏感的代码中，应在预期CPU等待其他工作之前添加`readl()`。对于I/O端口空间，经典的“位敲击”序列如下所示：

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
        readb(safe_mmio_reg);           /* 刷新延后的写入 */
        udelay(10);
}
```

重要的是，“safe_mmio_reg”不应有任何干扰设备正确运行的副作用。

另一个需要注意的情况是在重置PCI设备时。使用PCI配置空间读取来刷新`writel()`。这将在所有平台上优雅地处理PCI主控中止，如果PCI设备预计不会响应`readl()`。大多数x86平台允许MMIO读取主控中止（即“软失败”）并返回垃圾值（例如~0）。但许多RISC平台会崩溃（即“硬失败”）。
