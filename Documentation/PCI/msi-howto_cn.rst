SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

==========================
MSI 驱动程序指南 HOWTO
==========================

:作者: Tom L Nguyen；Martine Silbermann；Matthew Wilcox

:版权: 2003, 2008 Intel 公司

关于本指南
================

本指南描述了消息信号中断（MSIs）的基础知识、使用 MSI 相对于传统中断机制的优势、如何将您的驱动程序更改为使用 MSI 或 MSI-X，以及如果设备不支持 MSIs 时的一些基本诊断方法。

什么是 MSIs？
==============

消息信号中断是一种设备写入特定地址的操作，该操作会导致 CPU 收到一个中断。
MSI 功能最初在 PCI 2.2 中被指定，并在 PCI 3.0 中进行了增强，允许每个中断单独屏蔽。PCI 3.0 还引入了 MSI-X 功能。MSI-X 支持比 MSI 更多的设备中断，并允许独立配置中断。
设备可能同时支持 MSI 和 MSI-X，但一次只能启用其中一个。

为什么使用 MSIs？
=============

使用 MSIs 可以带来三个方面的优势，超过传统的基于引脚的中断：

1. 基于引脚的 PCI 中断通常由多个设备共享。
   为了支持这一点，内核必须调用与每个中断相关的中断处理程序，这会导致整个系统的性能下降。而 MSIs 永远不会共享，因此不会出现这个问题。

2. 当设备将数据写入内存并触发基于引脚的中断时，有可能中断会在所有数据到达内存之前就到达（在 PCI-PCI 桥接器后面的设备上这种情况更常见）。为了确保所有数据都已到达内存，中断处理程序必须读取引发中断的设备上的寄存器。PCI 事务排序规则要求所有数据必须先到达内存，然后才能从寄存器返回值。
   使用 MSIs 可以避免这个问题，因为生成中断的写入操作不能超越数据写入，所以在中断发生时，驱动程序知道所有数据都已经到达内存。

3. PCI 设备每个功能只能支持一个基于引脚的中断。
经常情况下，驱动程序需要查询设备以确定发生了什么事件，这会减慢常见情况下的中断处理速度。通过使用MSI（消息信号中断），设备可以支持更多的中断，使每个中断都可以针对不同的目的进行专门化。一种可能的设计是将不常见的条件（如错误）分配给单独的中断，从而允许驱动程序更高效地处理常规的中断处理路径。其他可能的设计包括为网卡中的每个数据包队列或存储控制器中的每个端口分配一个中断。

如何使用MSI
===========

PCI设备默认初始化为使用引脚中断。设备驱动程序必须设置设备以使用MSI或MSI-X。并非所有机器都正确支持MSI，对于这些机器，下面描述的API将简单地失败，并且设备将继续使用引脚中断。

包含内核对MSI的支持
-------------------

为了支持MSI或MSI-X，内核必须启用CONFIG_PCI_MSI选项。这个选项仅在某些架构上可用，并且可能依赖于其他一些选项也已设置。例如，在x86架构中，还必须启用X86_UP_APIC或SMP才能看到CONFIG_PCI_MSI选项。

使用MSI
-------

大部分工作已经在PCI层完成。驱动程序只需请求PCI层为该设备设置MSI功能即可。

要自动使用MSI或MSI-X中断向量，请使用以下函数：

```c
int pci_alloc_irq_vectors(struct pci_dev *dev, unsigned int min_vecs,
        unsigned int max_vecs, unsigned int flags);
```

此函数为PCI设备分配最多`max_vecs`个中断向量。它返回分配的向量数量或负数错误码。如果设备要求最少数量的向量，驱动程序可以传递一个设置为该限制的`min_vecs`参数，如果无法满足最小数量的向量，则PCI核心将返回-ENOSPC。

`flags`参数用于指定设备和驱动程序可以使用的中断类型（PCI_IRQ_INTX、PCI_IRQ_MSI、PCI_IRQ_MSIX）。也可以使用方便的简写（PCI_IRQ_ALL_TYPES）来请求任何可能的中断类型。如果设置了PCI_IRQ_AFFINITY标志，则`pci_alloc_irq_vectors()`将在可用的CPU之间分散中断。

要获取传递给`request_irq()`和`free_irq()`的Linux IRQ编号以及向量，请使用以下函数：

```c
int pci_irq_vector(struct pci_dev *dev, unsigned int nr);
```

在移除设备之前，应使用以下函数释放任何已分配的资源：

```c
void pci_free_irq_vectors(struct pci_dev *dev);
```

如果设备同时支持MSI-X和MSI功能，此API将优先使用MSI-X设施。MSI-X支持1到2048之间的任意数量的中断。相比之下，MSI被限制为最多32个中断（并且必须是2的幂）。此外，MSI中断向量必须连续分配，因此系统可能无法为MSI分配与MSI-X相同数量的向量。在某些平台上，MSI中断必须全部针对同一组CPU，而MSI-X中断可以针对不同的CPU。

如果设备既不支持MSI-X也不支持MSI，它将回退到单个传统的IRQ向量。
MSI 或 MSI-X 中断的典型用法是分配尽可能多的中断向量，通常达到设备支持的最大限制。如果 `nvec` 大于设备支持的数量，则会自动将其限制为支持的最大值，因此无需事先查询支持的向量数量：

```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_ALL_TYPES);
if (nvec < 0)
    goto out_err;
```

如果驱动程序无法或不愿意处理可变数量的 MSI 中断，可以通过将特定数量的中断传递给 `pci_alloc_irq_vectors()` 函数的 `min_vecs` 和 `max_vecs` 参数来请求特定数量的中断：

```c
ret = pci_alloc_irq_vectors(pdev, nvec, nvec, PCI_IRQ_ALL_TYPES);
if (ret < 0)
    goto out_err;
```

上述请求类型的最显著例子是为设备启用单个 MSI 模式。这可以通过将两个 1 作为 `min_vecs` 和 `max_vecs` 传递来实现：

```c
ret = pci_alloc_irq_vectors(pdev, 1, 1, PCI_IRQ_ALL_TYPES);
if (ret < 0)
    goto out_err;
```

某些设备可能不支持使用传统的线中断，在这种情况下，驱动程序可以指定仅接受 MSI 或 MSI-X：

```c
nvec = pci_alloc_irq_vectors(pdev, 1, nvec, PCI_IRQ_MSI | PCI_IRQ_MSIX);
if (nvec < 0)
    goto out_err;
```

### 过时的 API

以下用于启用和禁用 MSI 或 MSI-X 中断的老 API 不应用于新的代码中：

- `pci_enable_msi()` （已弃用）
- `pci_disable_msi()` （已弃用）
- `pci_enable_msix_range()` （已弃用）
- `pci_enable_msix_exact()` （已弃用）
- `pci_disable_msix()` （已弃用）

此外，还有提供支持的 MSI 或 MSI-X 向量数量的 API：`pci_msi_vec_count()` 和 `pci_msix_vec_count()`。通常应避免使用这些 API，而是让 `pci_alloc_irq_vectors()` 自动限制向量数量。如果您有合法的特殊用途情况，可能需要重新考虑这个决定，并添加一个处理 MSI 和 MSI-X 的透明函数 `pci_nr_irq_vectors()`。

### 使用 MSI 时的注意事项

#### 自旋锁

大多数设备驱动程序都有一个每个设备的自旋锁，该锁在中断处理程序中被获取。对于基于引脚的中断或单个 MSI，不需要禁用中断（Linux 保证同一个中断不会重新进入）。如果设备使用多个中断，驱动程序必须在持有锁时禁用中断。如果设备发送不同的中断，驱动程序将会尝试递归获取自旋锁，从而导致死锁。这种死锁可以通过使用 `spin_lock_irqsave()` 或 `spin_lock_irq()` 来避免，这些函数禁用本地中断并获取锁（详见 `Documentation/kernel-hacking/locking.rst`）。

### 如何判断设备是否启用了 MSI/MSI-X

使用 `lspci -v`（作为 root 用户）可能会显示一些具有“MSI”、“Message Signalled Interrupts”或“MSI-X”功能的设备。这些功能都有一个“Enable”标志，后面跟着 “+”（启用）或 “-”（禁用）。

### MSI 特殊情况

已知有几个 PCI 芯片组或设备不支持 MSI。PCI 栈提供了三种禁用 MSI 的方法：

1. 全局禁用
2. 在特定桥接器后面的设备上禁用
3. 在单个设备上禁用

#### 全局禁用 MSI

一些主机芯片组不正确地支持 MSI。如果我们幸运的话，制造商知道这一点，并且已经在 ACPI FADT 表中指明了。在这种情况下，Linux 会自动禁用所有设备上的 MSI。

有些主板没有在表中包含这些信息，所以我们必须自己检测它们。完整的列表可以在 `drivers/pci/quirks.c` 文件中的 `quirk_disable_all_msi()` 函数附近找到。

如果您有一块主板在使用 MSI 时存在问题，可以在内核命令行中传递 `pci=nomsi` 来禁用所有设备上的 MSI。最好报告问题到 `linux-pci@vger.kernel.org`，包括完整的 `lspci -v` 输出，以便我们可以在内核中添加特殊情况。

#### 在桥接器后面的设备上禁用 MSI

一些 PCI 桥接器无法正确地在总线之间路由 MSI。在这种情况下，必须禁用桥接器后面所有设备上的 MSI。

有些桥接器允许您通过更改其 PCI 配置空间中的某些位来启用 MSI（尤其是 HyperTransport 芯片组，如 nVidia nForce 和 Serverworks HT2000）。与主机芯片组一样，Linux 大部分都知道这些情况，并会在能够的情况下自动启用 MSI。
如果你有一个 Linux 未知的桥接设备，你可以使用已知有效的方法在配置空间中启用 MSI（消息信号中断），然后通过以下命令在该桥接设备上启用 MSI：

```
echo 1 > /sys/bus/pci/devices/$bridge/msi_bus
```

其中 `$bridge` 是你所启用的桥接设备的 PCI 地址（例如 0000:00:0e.0）。要禁用 MSI，可以用 0 替换 1。更改这个值时需要谨慎，因为它可能会破坏该桥接设备下所有设备的中断处理。

再次，请将任何需要特殊处理的桥接设备通知到 linux-pci@vger.kernel.org。
单个设备禁用 MSI
-------------------

一些设备已知存在 MSI 实现错误。通常这种情况会在单独的设备驱动程序中处理，但偶尔也需要通过特殊设置来处理。某些驱动程序有一个选项可以禁用 MSI 的使用。虽然这对驱动程序作者来说是一个方便的变通方法，但这不是好的做法，不应该效仿。

查找设备上 MSI 被禁用的原因
------------------------------

从以上三个部分可以看出，MSI 可能未被启用的原因有很多。你的第一步应该是仔细检查 dmesg 日志以确定你的机器是否启用了 MSI。你还应该检查 `.config` 文件以确保启用了 `CONFIG_PCI_MSI` 配置项。
然后，运行 `lspci -t` 可以列出设备上方的桥接设备。读取 `/sys/bus/pci/devices/*/msi_bus` 文件可以告诉你 MSI 是否被启用（1）或禁用（0）。如果在属于 PCI 根设备和目标设备之间的任何桥接设备的 `msi_bus` 文件中发现 0，则表示 MSI 被禁用。
还值得检查设备驱动程序是否支持 MSI。例如，它可能包含带有 PCI_IRQ_MSI 或 PCI_IRQ_MSIX 标志的对 `pci_alloc_irq_vectors()` 的调用。

设备驱动程序 MSI(-X) API 列表
==============================

PCI/MSI 子系统有一个专门的 C 文件用于导出其设备驱动程序 API — `drivers/pci/msi/api.c`。以下函数是导出的：

.. kernel-doc:: drivers/pci/msi/api.c
   :export:
