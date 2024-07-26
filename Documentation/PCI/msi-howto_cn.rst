### SPDX 许可证标识符：GPL-2.0
### 包含：<isonum.txt>

==========================
MSI 驱动程序指南 HOWTO
==========================

**作者**：Tom L Nguyen；Martine Silbermann；Matthew Wilcox

**版权所有**：2003, 2008 Intel 公司

关于本指南
================

本指南介绍了消息指示中断（MSIs）的基础知识，使用MSI相较于传统中断机制的优势，如何修改驱动程序以使用MSI或MSI-X，以及如果设备不支持MSIs时的一些基本诊断方法。

什么是 MSIs？
==============

消息指示中断是一种由设备向特殊地址写入信息，从而触发CPU接收中断的方式。
MSI功能最初在PCI 2.2规范中被定义，并在PCI 3.0中得到增强，允许每个中断单独屏蔽。PCI 3.0还引入了MSI-X功能，它支持比MSI更多的每个设备的中断数，并且允许独立配置这些中断。
设备可能同时支持MSI和MSI-X，但每次只能启用其中一个。

为什么使用 MSIs？
=============

使用MSIs相较于传统的基于引脚的中断有三个主要优势：

1. 基于引脚的PCI中断通常被多个设备共享。为了支持这一点，内核必须调用与每个中断相关的所有中断处理程序，这导致整个系统的性能下降。而MSIs永远不会被共享，因此不会出现这个问题。
2. 当一个设备将数据写入内存并随后引发基于引脚的中断时，可能会在所有数据到达内存之前就收到中断（对于位于PCI-PCI桥后面的设备这种情况更可能发生）。为了确保所有数据都已到达内存，中断处理程序必须读取引发中断的设备上的寄存器。PCI事务排序规则要求所有的数据必须在寄存器返回值之前到达内存。使用MSIs可以避免这个问题，因为生成中断的写操作不能先于数据写操作完成，所以当中断发生时，驱动程序已经知道所有数据都已经到达内存。
3. PCI设备每项功能只能支持单个基于引脚的中断。
通常情况下，驱动程序需要查询设备以确定发生了什么事件，这会减慢常见情况下的中断处理速度。使用MSI（消息信号中断）时，一个设备可以支持更多的中断，使得每个中断都可以针对不同的目的进行专门化。一种可能的设计是将不常见的状况（如错误）分配给单独的中断，这样可以让驱动程序更高效地处理常规的中断路径。其他可能的设计包括为网卡中的每个数据包队列或存储控制器中的每个端口分配一个中断。

如何使用MSI
=============

PCI设备初始化时默认使用基于引脚的中断。驱动程序必须设置设备使用MSI或MSI-X。并非所有机器都正确支持MSI，并且对于那些不支持的机器，下面描述的API将会失败，设备将继续使用基于引脚的中断。

包含内核对MSI的支持
------------------------

为了支持MSI或MSI-X，内核必须在编译时启用CONFIG_PCI_MSI选项。此选项仅在某些架构上可用，并且可能依赖于其他一些选项也被设置。例如，在x86架构中，您还必须启用X86_UP_APIC或SMP选项才能看到CONFIG_PCI_MSI选项。

使用MSI
---------

大多数繁重的工作已经在PCI层完成。驱动程序只需请求PCI层为该设备设置MSI功能即可。

要自动使用MSI或MSI-X中断向量，可以使用以下函数：

```c
int pci_alloc_irq_vectors(struct pci_dev *dev, unsigned int min_vecs,
                          unsigned int max_vecs, unsigned int flags);
```

此函数为PCI设备分配最多`max_vecs`个中断向量。它返回已分配的向量数量或负数表示错误。如果设备需要最少数量的向量，则驱动程序可以通过设置`min_vecs`参数为此限制，并且PCI核心会在无法满足最小向量数量时返回-ENOSPC。

`flags`参数用于指定设备和驱动程序可以使用的中断类型（PCI_IRQ_INTX, PCI_IRQ_MSI, PCI_IRQ_MSIX）。还提供了一个方便的简写（PCI_IRQ_ALL_TYPES），用于请求任何可能类型的中断。如果设置了PCI_IRQ_AFFINITY标志，则`pci_alloc_irq_vectors()`将在可用的CPU之间分散这些中断。

要获取传递给`request_irq()`和`free_irq()`以及向量的Linux IRQ编号，请使用以下函数：

```c
int pci_irq_vector(struct pci_dev *dev, unsigned int nr);
```

在移除设备之前，应使用以下函数释放任何已分配的资源：

```c
void pci_free_irq_vectors(struct pci_dev *dev);
```

如果设备同时支持MSI-X和MSI功能，此API将优先使用MSI-X功能。MSI-X支持从1到2048之间的任意数量的中断。相比之下，MSI被限制为最多32个中断（并且必须是2的幂）。此外，MSI中断向量必须连续分配，因此系统可能无法为MSI分配与MSI-X一样多的向量。在某些平台上，MSI中断必须全部指向同一组CPU，而MSI-X中断可以分别指向不同的CPU。

如果设备既不支持MSI-X也不支持MSI，那么它将回退到单一的传统IRQ向量。
MSI 或 MSI-X 中断的典型使用方式是分配尽可能多的中断向量，很可能达到设备支持的上限。如果 `nvec` 大于设备支持的数量，它将自动限制到支持的最大值，因此无需预先查询支持的向量数：

```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_ALL_TYPES);
if (nvec < 0)
    goto out_err;
```

如果驱动程序无法或不愿意处理可变数量的MSI中断，可以通过将特定的中断数量传递给 `pci_alloc_irq_vectors()` 函数作为 'min_vecs' 和 'max_vecs' 参数来请求特定数量的中断：

```c
ret = pci_alloc_irq_vectors(pdev, nvec, nvec, PCI_IRQ_ALL_TYPES);
if (ret < 0)
    goto out_err;
```

最典型的例子就是为设备启用单个MSI模式。这可以通过传递两个1作为 'min_vecs' 和 'max_vecs' 来实现：

```c
ret = pci_alloc_irq_vectors(pdev, 1, 1, PCI_IRQ_ALL_TYPES);
if (ret < 0)
    goto out_err;
```

某些设备可能不支持使用传统的线路中断，在这种情况下，驱动程序可以指定只接受MSI或MSI-X：

```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_MSI | PCI_IRQ_MSIX);
if (nvec < 0)
    goto out_err;
```

### 传统API

以下用于启用和禁用MSI或MSI-X中断的老式API不应在新代码中使用：

- `pci_enable_msi()` （已废弃）
- `pci_disable_msi()` （已废弃）
- `pci_enable_msix_range()` （已废弃）
- `pci_enable_msix_exact()` （已废弃）
- `pci_disable_msix()` （已废弃）

此外，还有一些提供支持的MSI或MSI-X向量数量的API：`pci_msi_vec_count()` 和 `pci_msix_vec_count()`。通常应避免使用这些API，而让 `pci_alloc_irq_vectors()` 自动限制向量的数量。如果你有一个合理的特殊情况需要获取向量的数量，我们可能需要重新考虑这个决定，并添加一个透明处理MSI和MSI-X的 `pci_nr_irq_vectors()` 辅助函数。

### 使用MSIs时的注意事项

#### 旋转锁

大多数设备驱动程序都有一个每个设备的旋转锁，在中断处理程序中会获取这个锁。对于基于引脚的中断或单个MSI，没有必要禁用中断（Linux保证相同的中断不会被重复进入）。如果设备使用多个中断，驱动程序必须在持有锁的同时禁用中断。如果设备发送不同的中断，驱动程序将会死锁，试图递归获取旋转锁。可以通过使用 `spin_lock_irqsave()` 或 `spin_lock_irq()` 来避免这样的死锁，这两种方法会禁用本地中断并获取锁（参见Documentation/kernel-hacking/locking.rst）。

### 如何判断设备是否启用了MSI/MSI-X

使用 `lspci -v`（作为root用户）可能会显示一些具有“MSI”、“消息触发中断”或“MSI-X”能力的设备。这些能力各自都有一个“Enable”标志，后面跟着 "+"（启用）或 "-"（禁用）。

### MSI的特殊情形

已知有几个PCI芯片组或设备不支持MSIs。
PCI堆栈提供了三种禁用MSIs的方式：

1. 全局禁用
2. 在特定桥接器后面的设备上禁用
3. 在单个设备上禁用

#### 全局禁用MSIs

有些主机芯片组根本不正确地支持MSIs。如果我们幸运的话，制造商知道这一点，并且已经在ACPI FADT表中指明了。在这种情况下，Linux会自动禁用所有设备上的MSIs。
有些主板没有在这个表中包含这些信息，所以我们必须自己检测它们。这些主板的完整列表可以在drivers/pci/quirks.c中的 `quirk_disable_all_msi()` 函数附近找到。
如果你的主板在使用MSIs时存在问题，你可以在内核命令行中传递 `pci=nomsi` 来禁用所有设备上的MSIs。为了你的最佳利益，你应该向 linux-pci@vger.kernel.org 报告这个问题，包括完整的 `lspci -v` 输出，以便我们可以将特殊情形添加到内核中。

#### 禁用桥接器后面的MSIs

有些PCI桥接器不能正确地在总线间路由MSIs。
在这种情况下，必须禁用桥接器后面所有设备上的MSIs。
有些桥接器允许你通过改变其PCI配置空间中的某些位来启用MSIs（特别是HyperTransport芯片组，如nVidia nForce和Serverworks HT2000）。与主机芯片组一样，Linux大多了解这些情况，并会在可能的情况下自动启用MSIs。
如果你有一座Linux未知的桥接器，你可以使用你所知可行的方法在配置空间中启用MSI，然后通过以下方式在该桥接器上启用MSI：

       在 `/sys/bus/pci/devices/$bridge/msi_bus` 中写入 `1`

其中 `$bridge` 是你已启用的桥接器的PCI地址（例如 `0000:00:0e.0`）
要禁用MSI，写入 `0` 而不是 `1`。更改此值时应谨慎，因为这可能会导致该桥接器下所有设备的中断处理出现问题。
再次，请将任何需要特殊处理的桥接器通知至 `linux-pci@vger.kernel.org`
单个设备上禁用MSI
------------------------------

一些设备已知具有错误的MSI实现。通常这是在单独的设备驱动程序中处理的，但偶尔需要通过特殊处理来解决。某些驱动程序有一个选项可以禁用MSI的使用。虽然这对驱动程序作者来说是一个方便的解决办法，但这不是好的做法，不应该被效仿。
查找设备上MSI被禁用的原因
------------------------------

从上面三个部分可以看出，对于给定设备MSI可能未启用的原因有很多。你的第一步应该是仔细检查dmesg以确定是否为你的机器启用了MSI。你也应该检查你的 `.config` 文件确保你已经启用了 `CONFIG_PCI_MSI`。
然后，`lspci -t` 可以提供设备上方的桥接器列表。读取 `/sys/bus/pci/devices/*/msi_bus` 将会告诉你MSI是启用状态（`1`）还是禁用状态（`0`）。如果在属于从PCI根到设备之间的任何桥接器的 `msi_bus` 文件中找到 `0`，则MSI被禁用。
同时，也值得检查设备驱动程序以查看它是否支持MSI
例如，它可能包含带有 `PCI_IRQ_MSI` 或 `PCI_IRQ_MSIX` 标志调用 `pci_alloc_irq_vectors()` 的代码
设备驱动程序MSI(-X) API列表
==========================

PCI/MSI子系统有一个专用的C文件用于其导出的设备驱动程序API——`drivers/pci/msi/api.c`。以下是一些导出的函数：

.. kernel-doc:: drivers/pci/msi/api.c
   :export:
