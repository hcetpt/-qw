异构内存管理（HMM）
=====================================

提供基础设施和辅助功能，将非传统内存（如板载GPU内存）集成到常规内核路径中。这一核心在于为这种内存提供专门的`struct page`（详见本文档第5至7节）。
HMM还提供了可选的SVM（共享虚拟内存）辅助功能，即允许设备透明地访问与CPU一致的程序地址，这意味着任何有效的CPU指针也是设备的有效指针。这在简化使用高级异构计算时变得必不可少，其中GPU、DSP或FPGA用于代表进程执行各种计算。
本文档分为以下部分：在第一部分中，我阐述了使用特定于设备的内存分配器所面临的问题。第二部分介绍了许多平台固有的硬件限制。第三部分概述了HMM的设计。第四部分解释了CPU页表镜像的工作原理以及HMM在此上下文中的作用。第五部分讨论了内核内部如何表示设备内存。最后，最后一节介绍了一种新的迁移辅助功能，可以利用设备的DMA引擎。
.. contents:: :local:

使用特定于设备的内存分配器的问题
====================================================

拥有大量板载内存（几GB）的设备，如GPU，历史上是通过专用驱动程序API来管理其内存的。
这导致由设备驱动程序分配和管理的内存与常规应用程序内存（私有匿名内存、共享内存或普通文件支持的内存）之间产生了脱节。从这里开始，我将这种情况称为分割地址空间。而我所说的共享地址空间是指相反的情况：即任何应用程序内存区域都可以被设备透明地使用。

分割地址空间之所以发生是因为设备只能访问通过特定于设备的API分配的内存。这意味着从设备的角度来看，程序中的所有内存对象并不平等，这使得依赖广泛库集的大程序变得复杂。

具体来说，这意味着想要利用像GPU这样的设备的代码需要在通用分配内存（如malloc、mmap私有、mmap共享）和通过设备驱动程序API分配的内存（这最终也会映射为设备文件的mmap）之间复制对象。
对于平面数据集（数组、网格、图像等），这并不是太难实现，但对于复杂数据集（列表、树等），则很难正确处理。复制一个复杂数据集需要重新映射其每个元素之间的指针关系。这容易出错，并且由于存在重复的数据集和地址，程序调试变得更加困难。

分割地址空间也意味着库无法透明地使用来自核心程序或其他库的数据，因此每个库可能需要使用特定于设备的内存分配器来复制其输入数据集。大型项目会因此受到影响，并因各种内存拷贝而浪费资源。
将每个库API复制以接受或输出由每个特定设备分配器分配的内存并不是一个可行的选择。这将导致库入口点的组合性爆炸。
最终，随着高级语言构造（在C++以及其他语言中）的发展，编译器现在可以在程序员不知情的情况下利用GPU和其他设备。一些编译器识别的模式只有在共享地址空间下才能实现。对于所有其他模式而言，使用共享地址空间也是更合理的。

I/O总线、设备内存特性
========================

I/O总线由于几个限制而削弱了共享地址空间。大多数I/O总线仅允许设备对主存进行基本的内存访问；甚至缓存一致性也往往是可选的。CPU从设备内存中访问数据受到的限制更多。通常情况下，这种访问并不具有缓存一致性。
如果我们只考虑PCIE总线，那么设备可以通过IOMMU访问主存，并与CPU保持缓存一致性。然而，它只允许设备在主存上执行有限的原子操作。相反方向的情况更糟：CPU只能访问设备内存的一小部分范围，并且不能在其上执行原子操作。因此，从内核的角度来看，设备内存不能被视为常规内存。
另一个限制因素是带宽（通过PCIE 4.0和16条通道约为32GB/s）。这比最快的GPU内存（1TB/s）低33倍。
最后一个限制是延迟。设备从主存访问数据的延迟比设备访问自身内存时的延迟高出一个数量级。
一些平台正在开发新的I/O总线或对PCIE进行修改，以解决其中的一些限制（如OpenCAPI、CCIX）。它们主要允许CPU和设备之间的双向缓存一致性，并支持架构所支持的所有原子操作。遗憾的是，并非所有平台都在遵循这一趋势，一些主要架构仍缺乏硬件解决方案来应对这些问题。
因此，为了使共享地址空间有意义，我们不仅必须允许设备访问任何内存，还必须允许任何内存迁移到设备内存中，同时设备正在使用这些内存时阻止CPU访问（在迁移过程中）。

共享地址空间与迁移
=====================

HMM旨在提供两个主要功能。第一个是通过复制CPU页表到设备页表中来共享地址空间，使得在进程地址空间中的任何有效主存地址指向相同的物理内存。
为了实现这一点，HMM提供了一组辅助工具来填充设备页表，同时跟踪CPU页表更新。设备页表更新不像CPU页表更新那样简单。要更新设备页表，必须分配一个缓冲区（或使用预先分配的缓冲池），并在其中写入特定于GPU的命令来执行更新（取消映射、缓存失效等）。这些操作不能通过通用代码为所有设备完成。因此，HMM提供了辅助工具来抽象出所有可以通用的部分，而将具体的硬件细节留给设备驱动程序处理。
第二个机制是HMM提供的新型ZONE_DEVICE内存，允许为设备内存的每一页分配一个`struct page`。这些页面很特殊，因为CPU无法映射它们。然而，这允许使用现有的迁移机制将主内存迁移到设备内存，并且从CPU的角度来看，一切就像一个被交换到磁盘的页面。使用`struct page`提供了与现有内存管理（mm）机制最简单、最干净的集成。再次强调，HMM仅提供帮助功能：一是为设备内存热插拔新的ZONE_DEVICE内存；二是执行迁移。至于迁移什么和何时迁移的策略决策则留给设备驱动程序处理。

请注意，任何对设备页面的CPU访问都会触发页面错误并迁回主内存。例如，当支持某个CPU地址A的页面从主内存迁移到设备页面时，任何对地址A的CPU访问都会触发页面错误并开始迁回主内存的过程。

通过这两个特性，HMM不仅允许设备镜像进程地址空间并保持CPU和设备页表同步，还通过迁移当前正在被设备使用的数据集部分来利用设备内存。

地址空间镜像实现和API
======================

地址空间镜像的主要目标是允许复制一段CPU页表到设备页表中；HMM帮助保持两者的同步。希望镜像进程地址空间的设备驱动程序必须首先注册一个`mmu_interval_notifier`：

```c
int mmu_interval_notifier_insert(struct mmu_interval_notifier *interval_sub,
				 struct mm_struct *mm, unsigned long start,
				 unsigned long length,
				 const struct mmu_interval_notifier_ops *ops);
```

在`ops->invalidate()`回调期间，设备驱动程序必须执行范围更新动作（标记范围为只读，或完全解除映射等）。设备必须在驱动程序回调返回之前完成更新。

当设备驱动程序想要填充一段虚拟地址范围时，可以使用：

```c
int hmm_range_fault(struct hmm_range *range);
```

这将在缺失或只读条目上触发页面错误（如果请求写访问）。页面错误使用通用内存页面错误代码路径，就像CPU页面错误一样。使用模式如下：

```c
int driver_populate_range(...)

{
      struct hmm_range range;
      ..
      range.notifier = &interval_sub;
      range.start = ...;
      range.end = ...;
      range.hmm_pfns = ...;

      if (!mmget_not_zero(interval_sub->notifier.mm))
          return -EFAULT;

 again:
      range.notifier_seq = mmu_interval_read_begin(&interval_sub);
      mmap_read_lock(mm);
      ret = hmm_range_fault(&range);
      if (ret) {
          mmap_read_unlock(mm);
          if (ret == -EBUSY)
                 goto again;
          return ret;
      }
      mmap_read_unlock(mm);

      take_lock(driver->update);
      if (mmu_interval_read_retry(&ni, range.notifier_seq)) {
          release_lock(driver->update);
          goto again;
      }

      /* 使用pfns数组内容更新设备页表，在update锁保护下 */

      release_lock(driver->update);
      return 0;
}
```

`driver->update`锁是在其`invalidate()`回调中获取的同一个锁。在调用`mmu_interval_read_retry()`之前必须持有该锁，以避免与并发CPU页表更新的竞争条件。

利用default_flags和pfn_flags_mask
==================================

`hmm_range`结构中有两个字段，`default_flags`和`pfn_flags_mask`，用于指定整个范围的故障或快照策略，而无需为pfns数组中的每个条目单独设置。

例如，如果设备驱动程序希望为具有至少读权限的范围内的所有页面设置：

```c
    range->default_flags = HMM_PFN_REQ_FAULT;
    range->pfn_flags_mask = 0;
```

然后按上述方法调用`hmm_range_fault()`。这将使范围内所有页面至少具有读权限。

现在假设驱动程序希望做同样的事情，但范围内的某一页需要写权限。此时驱动程序设置：

```c
    range->default_flags = HMM_PFN_REQ_FAULT;
    range->pfn_flags_mask = HMM_PFN_REQ_WRITE;
    range->pfns[index_of_write] = HMM_PFN_REQ_WRITE;
```

这样，HMM将使所有页面至少具有读权限（即有效），而对于地址等于`range->start + (index_of_write << PAGE_SHIFT)`的页面，则会以写权限触发页面错误，即如果CPU PTE没有设置写权限，那么HMM将调用`handle_mm_fault()`。

`hmm_range_fault`完成后，标志位将设置为页表的当前状态，即如果页面可写，则将设置`HMM_PFN_VALID | HMM_PFN_WRITE`。
从核心内核的角度表示和管理设备内存
==================================

为了支持设备内存，尝试了多种不同的设计方案。最初的设计使用了一个特定于设备的数据结构来保存迁移内存的信息，并且HMM（硬件内存管理）在内存管理代码的多个地方进行了挂钩处理，以处理任何对由设备内存支持的地址的访问。结果发现，这种方案几乎复制了`struct page`中的大多数字段，并且需要更新许多内核代码路径以理解这种新型内存。

大多数内核代码路径从来不会尝试访问页面背后的内存，而只关心`struct page`的内容。因此，HMM转而直接使用`struct page`来表示设备内存，这使得大多数内核代码路径无需意识到这种差异。我们只需要确保没有人尝试从CPU侧映射这些页面。

迁移到和从设备内存迁移
======================

由于CPU不能直接访问设备内存，设备驱动程序必须使用硬件DMA或特定于设备的加载/存储指令来迁移数据。`migrate_vma_setup()`、`migrate_vma_pages()` 和 `migrate_vma_finalize()` 函数设计的目的是使编写驱动程序更加容易，并将通用代码集中化。

在将页面迁移到设备私有内存之前，需要创建特殊的设备私有`struct page`。这些特殊页将作为特殊的“交换”页表条目，这样如果CPU进程试图访问已迁移到设备私有内存的页面时会触发错误。

这些可以使用以下方式分配和释放：

```c
struct resource *res;
struct dev_pagemap pagemap;

res = request_free_mem_region(&iomem_resource, /* 字节数 */, "驱动程序资源名称");
pagemap.type = MEMORY_DEVICE_PRIVATE;
pagemap.range.start = res->start;
pagemap.range.end = res->end;
pagemap.nr_range = 1;
pagemap.ops = &device_devmem_ops;
memremap_pages(&pagemap, numa_node_id());

memunmap_pages(&pagemap);
release_mem_region(pagemap.range.start, range_len(&pagemap.range));
```

当资源可以与`struct device`关联时，还可以使用`devm_request_free_mem_region()`、`devm_memremap_pages()`、`devm_memunmap_pages()` 和 `devm_release_mem_region()`。

整体迁移步骤类似于在系统内存内迁移NUMA页面（参见Documentation/mm/page_migration.rst），但这些步骤被拆分到设备驱动程序特定代码和共享通用代码中：

1. `mmap_read_lock()`

   设备驱动程序需要将一个`struct vm_area_struct`传递给`migrate_vma_setup()`，因此在迁移期间需要持有`mmap_read_lock()` 或 `mmap_write_lock()`。
2. `migrate_vma_setup(struct migrate_vma *args)`

   设备驱动程序初始化`struct migrate_vma`字段，并将指针传递给`migrate_vma_setup()`。`args->flags`字段用于过滤哪些源页面应被迁移。例如，设置`MIGRATE_VMA_SELECT_SYSTEM`只会迁移系统内存，而设置`MIGRATE_VMA_SELECT_DEVICE_PRIVATE`只会迁移位于设备私有内存中的页面。如果设置了后一个标志，则使用`args->pgmap_owner`字段来识别属于该驱动程序的设备私有页面。这避免了尝试迁移其他设备中位于设备私有内存中的页面。

目前，只有匿名私有VMA范围可以从系统内存迁移到设备私有内存，反之亦然。
`migrate_vma_setup()`所做的第一步之一是通过调用`mmu_notifier_invalidate_range_start()`和`mmu_notifier_invalidate_range_end()`来使其他设备的MMU失效，以便在填充`args->src`数组时进行页表遍历，从而获取要迁移的PFN。
```invalidate_range_start()``` 回调函数会收到一个 ```struct mmu_notifier_range``` 结构体，其中的 ```event``` 字段被设置为 ```MMU_NOTIFY_MIGRATE```，而 ```owner``` 字段则被设置为传递给 ```migrate_vma_setup()``` 的 ```args->pgmap_owner``` 字段。这使得设备驱动程序可以跳过无效化回调，并仅对实际迁移的设备私有MMU映射进行无效化处理。

更多解释请参见下一节。

在遍历页表时，如果遇到 ```pte_none()``` 或 ```is_zero_pfn()``` 条目，则会在 ```args->src``` 数组中存储一个有效的“零”PFN。这使得驱动程序可以选择分配设备私有内存并清空它，而不是复制一页全是零的数据。有效的系统内存或设备私有结构页的PTE条目将通过 ```lock_page()``` 锁定，隔离出LRU（如果是系统内存的话，因为设备私有页面不在LRU上），从进程中解除映射，并插入一个特殊的迁移PTE来替代原来的PTE。

```migrate_vma_setup()``` 还会清除 ```args->dst``` 数组。

3. 设备驱动程序分配目标页面并将源页面复制到目标页面

驱动程序会检查每个 ```src``` 条目，查看是否设置了 ```MIGRATE_PFN_MIGRATE``` 位，并跳过那些不迁移的条目。设备驱动程序还可以选择通过不填充该页面的 ```dst``` 数组来跳过迁移该页面。

然后，驱动程序会分配一个设备私有结构页或系统内存页，并使用 ```lock_page()``` 锁定该页，填充 ```dst``` 数组条目：

```dst[i] = migrate_pfn(page_to_pfn(dpage));```

现在，驱动程序知道该页面正在迁移，因此它可以无效化设备私有MMU映射，并将设备私有内存复制到系统内存或另一个设备私有页。核心Linux内核会处理CPU页表的无效化，因此设备驱动程序只需要无效化其自身的MMU映射。

驱动程序可以使用 ```migrate_pfn_to_page(src[i])``` 获取源的 ```struct page```，并选择将源页面复制到目标页面或清空目标设备私有内存（如果指针为 ```NULL``` 表示源页面未在系统内存中填充）。

4. ```migrate_vma_pages()```

这一步是真正执行迁移的地方。
如果源页面是 `pte_none()` 或 `is_zero_pfn()` 页面，那么这就是新分配的页面被插入到 CPU 页表中的地方。

如果一个 CPU 线程在同一页面上发生故障，这可能会失败。但是，页表是锁定的，只有其中一个新页面会被插入。

设备驱动程序会发现 `MIGRATE_PFN_MIGRATE` 位被清除，如果它在这场竞争中失败了。

如果源页面已被锁定、隔离等，现在会将源 `struct page` 信息复制到目标 `struct page` 中，从而在 CPU 侧完成迁移。

5. 设备驱动程序更新仍在迁移中的页面的设备 MMU 页表，并回滚未迁移的页面。
   
   如果 `src` 入口仍然设置有 `MIGRATE_PFN_MIGRATE` 位，设备驱动程序可以更新设备 MMU 并设置写启用位（如果 `MIGRATE_PFN_WRITE` 位已设置）。

6. `migrate_vma_finalize()`

   这一步用新页面的页表项替换特殊的迁移页表项，并释放对源和目标 `struct page` 的引用。

7. `mmap_read_unlock()`

   现在可以释放锁了。

专属访问内存
=============

一些设备具有原子 PTE 位等特性，可用于实现对系统内存的原子访问。为了支持对共享虚拟内存页面的原子操作，该设备需要对该页面进行独占访问，不允许任何来自用户空间的访问。`make_device_exclusive_range()` 函数可用于使某个内存范围对用户空间不可访问。

这会将给定范围内所有页面的映射替换为特殊的交换条目。任何尝试访问这些交换条目的操作都会导致一个故障，该故障通过将条目替换为原始映射来解决。驱动程序会通过 MMU 通知器得知映射已更改，在此之后，它将不再拥有对该页面的独占访问权。独占访问保证持续到驱动程序释放页面锁和页面引用为止，在此之后，任何针对该页面的 CPU 故障都可按描述的方式继续处理。
内存 cgroup (memcg) 和 rss 计数
========================================

目前，设备内存被当作普通的 rss 计数页面来处理（如果设备页面用于匿名用途，则记为匿名；如果用于文件支持的页面，则记为文件；如果用于共享内存，则记为 shmem）。这是一个有意的选择，目的是保持现有应用程序在不知情的情况下使用设备内存时仍能正常运行。
一个缺点是，OOM（Out Of Memory）杀手可能会杀死大量使用设备内存但系统常规内存使用不多的应用程序，从而无法释放太多系统内存。我们希望在决定是否以不同方式计算设备内存之前，收集更多实际经验，了解应用程序和系统在存在设备内存的情况下，在内存压力下的表现。

对于内存 cgroup 也做出了同样的决定。设备内存页面会被计入与普通页面相同的内存 cgroup 中。这简化了设备内存与常规内存之间的迁移。这也意味着从设备内存迁回到常规内存不会因为超出内存 cgroup 限制而失败。我们将在获得更多关于设备内存使用及其对内存资源控制影响的经验之后，重新审视这一选择。

请注意，设备内存永远不能被设备驱动程序或通过 GUP 固定，因此这种内存总是在进程退出时自动释放。如果是共享内存或文件支持的内存，在最后一个引用被撤销时也会释放。
