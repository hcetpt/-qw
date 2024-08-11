======================
Linux 下的缓存和 TLB 刷新
======================

:作者: David S. Miller <davem@redhat.com>

本文档描述了由 Linux 内存管理子系统调用的缓存/TLB 刷新接口。它逐一列举每个接口，描述其预期用途以及调用接口后期望产生的副作用。
下面描述的副作用是针对单处理器实现及其在该单个处理器上的作用。多处理器情况是简单扩展，即只需将定义扩展到所有处理器上都会发生特定接口的副作用。不要因此认为多处理器下的缓存/TLB刷新必然低效；实际上，在这一领域存在许多优化的可能性。例如，如果能证明用户地址空间从未在一个 CPU 上执行过（参见 `mm_cpumask()`），则无需为该 CPU 执行此地址空间的刷新。

首先介绍 TLB 刷新接口，因为它们较为简单。“TLB”在 Linux 中被抽象为 CPU 用来缓存从软件页表获取的虚拟->物理地址转换的东西。这意味着如果软件页表发生变化，则“TLB”缓存中可能存在陈旧的转换。

因此，当软件页表发生变化时，内核将在页表变化之后调用以下刷新方法之一：

1) ``void flush_tlb_all(void)``

这是最严重的刷新操作。运行此接口后，任何之前的页表修改都将对 CPU 可见。
通常在内核页表发生变化时调用，因为这类转换具有全局性质。
2) ``void flush_tlb_mm(struct mm_struct *mm)``

此接口将整个用户地址空间从 TLB 中清除。运行后，必须确保地址空间 `mm` 的任何之前页表修改对 CPU 可见。也就是说，运行后，TLB 中不会有 `mm` 的条目。
此接口用于处理整个地址空间的页表操作，如 fork 和 exec 操作期间发生的情况。
3) ``void flush_tlb_range(struct vm_area_struct *vma,
   unsigned long start, unsigned long end)``

这里我们正从 TLB 中清除特定范围的（用户）虚拟地址转换。运行后，必须确保地址空间 `vma->vm_mm` 在 `start` 到 `end-1` 范围内的任何之前页表修改对 CPU 可见。也就是说，运行后，对于虚拟地址范围 `start` 到 `end-1` 内的 `mm`，TLB 中不会有条目。
"vma" 是用于该区域的后端存储。
主要用于 munmap() 类型的操作。
提供的接口希望目标平台能找到一种足够高效的方法来从TLB中移除多个页面大小的转换，而不是让内核为每个可能被修改的条目调用`flush_tlb_page`（参见下文）。

4) `void flush_tlb_page(struct vm_area_struct *vma, unsigned long addr)`

这次我们需要从TLB中移除PAGE_SIZE大小的转换。`vma`是Linux用来跟踪进程映射区域的支撑结构，地址空间可通过`vma->vm_mm`获得。此外，可以通过测试`(vma->vm_flags & VM_EXEC)`来判断该区域是否可执行（因此在分隔式TLB设置中可能存在于“指令TLB”中）。
运行此接口后，必须确保对地址空间`vma->vm_mm`中用户虚拟地址`addr`所做的任何先前页表修改对CPU可见。也就是说，在运行之后，对于虚拟地址`addr`，TLB中将不再有针对`vma->vm_mm`的条目。
这主要用于处理故障。

5) `void update_mmu_cache_range(struct vm_fault *vmf, 
   struct vm_area_struct *vma, unsigned long address, pte_t *ptep, 
   unsigned int nr)`

每次页错误处理结束时，都会调用此例程以告知架构特定代码，在地址空间“vma->vm_mm”中，从虚拟地址“address”开始连续的“nr”个页面现在在软件页表中已有转换信息。
此例程也在其他地方被调用，此时传递一个NULL的“vmf”。
目标平台可以根据需要自由使用这些信息。
例如，它可以利用这个事件来预加载软件管理的TLB配置中的TLB转换。
sparc64平台目前就是这样做的。
接下来是缓存刷新接口。通常情况下，当Linux更改现有的虚拟到物理映射值时，操作序列会采取以下形式之一：

1) `flush_cache_mm(mm);`
    `change_all_page_tables_of(mm);`
    `flush_tlb_mm(mm);`

2) `flush_cache_range(vma, start, end);`
    `change_range_of_page_tables(mm, start, end);`
    `flush_tlb_range(vma, start, end);`

3) `flush_cache_page(vma, addr, pfn);`
    `set_pte(pte_pointer, new_pte_val);`
    `flush_tlb_page(vma, addr);`

缓存级别刷新总是最先进行，因为这样可以正确处理那些要求在刷新虚拟地址的缓存时，该虚拟地址必须存在有效的虚拟到物理转换的系统。HyperSparc CPU就是具有这种特性的CPU之一。
下面的缓存刷新例程只需要处理对于特定 CPU 必要程度的缓存刷新。主要地，这些例程必须为那些具有虚拟索引缓存的 CPU 实现，这些缓存会在虚拟到物理地址转换被更改或移除时进行刷新。因此，例如，IA32 处理器中的物理索引物理标记缓存无需实现这些接口，因为这些缓存是完全同步的，并且不依赖于转换信息。

以下是逐个介绍的例程：

1) `void flush_cache_mm(struct mm_struct *mm)`

    此接口将整个用户地址空间从缓存中刷新出去。也就是说，在运行后，与 'mm' 相关的缓存行将不存在。
    此接口用于处理整个地址空间的页表操作，例如在进程退出和执行新进程 (`exit` 和 `exec`) 时发生的情况。

2) `void flush_cache_dup_mm(struct mm_struct *mm)`

    此接口将整个用户地址空间从缓存中刷新出去。也就是说，在运行后，与 'mm' 相关的缓存行将不存在。
    此接口用于处理整个地址空间的页表操作，例如在进程复制 (`fork`) 时发生的情况。
    这个选项与 `flush_cache_mm` 分开提供，以便为虚拟索引物理标记 (VIPT) 缓存提供一些优化的可能性。

3) `void flush_cache_range(struct vm_area_struct *vma, unsigned long start, unsigned long end)`

    在这里，我们正从缓存中刷新一个特定范围的（用户）虚拟地址。在运行后，对于 'vma->vm_mm' 的 'start' 到 'end-1' 范围内的虚拟地址，在缓存中将没有相应的条目。
    "vma" 是用于该区域的后端存储。
    主要用于 `munmap()` 类型的操作。
    提供此接口的目的是希望移植能够找到一种足够高效的方法来从缓存中移除多个页面大小的区域，而不是让内核对每个可能被修改的条目调用 `flush_cache_page`（见下文）。
4) ``void flush_cache_page(struct vm_area_struct *vma, unsigned long addr, unsigned long pfn)``

这次我们需要从缓存中移除一个大小为PAGE_SIZE的地址范围。`vma`是Linux用来跟踪进程映射区域（mmap'd）的支撑结构，地址空间可以通过`vma->vm_mm`获得。此外，可以测试`(vma->vm_flags & VM_EXEC)`来判断这个区域是否可执行（在“哈佛”类型的缓存布局中，这会影响到“指令缓存”）。`pfn`表示物理页框（将此值左移`PAGE_SHIFT`位以获取物理地址），`addr`映射到这个物理页框。正是这个映射需要从缓存中移除。
运行后，对于虚拟地址`addr`（其映射到`pfn`）在`vma->vm_mm`中的缓存条目将不存在。
这主要用在错误处理过程中。

5) ``void flush_cache_kmaps(void)``

如果平台使用了高内存(highmem)，则需要实现这个例程。它将在所有kmaps失效之前被调用。
运行后，对于内核虚拟地址范围`PKMAP_ADDR(0)`到`PKMAP_ADDR(LAST_PKMAP)`在缓存中将没有条目。
这个函数应该实现在`asm/highmem.h`中。

6) ``void flush_cache_vmap(unsigned long start, unsigned long end)``
   ``void flush_cache_vunmap(unsigned long start, unsigned long end)``

在这两个接口中，我们正从缓存中清除特定范围（内核）的虚拟地址。运行后，在虚拟地址范围`start`到`end-1`之间，内核地址空间在缓存中将没有条目。
这两个函数中的第一个是在`vmap_range()`安装页面表项之后被调用的。第二个是在`vunmap_range()`删除页面表项之前被调用的。
还存在另一类与CPU缓存相关的问题，目前需要一套完全不同的接口来妥善处理。
最大的问题是处理器数据缓存中的虚拟别名问题。
您的端口是否容易在 D 缓存中出现虚拟别名问题？
如果您的 D 缓存是基于虚拟索引的，其大小大于 `PAGE_SIZE`，并且不会阻止同一物理地址的多个缓存行同时存在，那么您就有这个问题。
如果您端口的 D 缓存存在此问题，请首先正确定义 `asm/shmparam.h` 中的 `SHMLBA`，它应该基本上等于您的虚拟寻址 D 缓存的大小（或如果大小可变，则为可能的最大值）。此设置将强制 SYSv IPC 层仅允许用户进程在该值的倍数处映射共享内存。
.. note::
  
  这并不能解决共享内存映射的问题，可以参考sparc64端口的一种解决方案（特别是SPARC_FLAG_MMAPSHARED）。
接下来，您需要解决所有其他情况下的 D 缓存别名问题。请记住，对于给定页面映射到某个用户地址空间的情况，总是至少还有一个映射，即内核在其从 `PAGE_OFFSET` 开始的线性映射中的映射。因此，一旦第一个用户将给定物理页面映射到其地址空间中，由此可以推断出 D 缓存别名问题有可能存在，因为内核已经在这个虚拟地址上映射了这个页面。
``void copy_user_page(void *to, void *from, unsigned long addr, struct page *page)``
  ``void clear_user_page(void *to, unsigned long addr, struct page *page)``

这两个例程用于在用户匿名或写时复制 (COW) 页面中存储数据。它们允许端口高效地避免用户空间和内核之间的 D 缓存别名问题。
例如，端口可能会在复制过程中暂时将 'from' 和 'to' 映射到内核虚拟地址。这两个页面的虚拟地址选择得当，使得内核的加载/存储指令恰好发生在与用户映射的页面相同的“颜色”的虚拟地址上。sparc64 端口就使用了这种技术。
参数 'addr' 告诉了用户最终将该页面映射到的虚拟地址，而参数 'page' 给出了目标 `struct page` 的指针。
如果没有 D 缓存别名问题，这两个例程可以直接调用 `memcpy` 或 `memset` 并且无需做更多事情。
``void flush_dcache_folio(struct folio *folio)``

当以下情况发生时必须调用此例程：

a) 内核写入位于页缓存页和/或高内存中的页面
b) 内核即将读取页缓存页，并且可能存在该页的用户空间共享/可写映射。注意 `{get,pin}_user_pages{_fast}` 在发现用户地址空间中的任何页面时已经调用了 `flush_dcache_folio`，因此驱动程序代码很少需要考虑这一点
.. note::
  
  此例程只需对可能被映射到用户进程地址空间的页缓存页进行调用。例如，处理页缓存中虚拟文件系统 (VFS) 符号链接的 VFS 层代码完全不需要调用此接口。
短语“内核写入页面缓存中的页面”具体指的是，内核执行存储指令，在该页面的内核虚拟映射中使数据变脏。这里进行刷新很重要，以处理D-cache别名问题，确保这些内核存储操作对用户空间中该页面的映射可见。
相反的情况同样重要，如果有共享+可写的文件映射用户，我们必须确保内核读取这些页面时能看到用户最近进行的存储操作。
如果D-cache别名不是问题，则在此架构上，此例程可以简单地定义为无操作（nop）。
在folio->flags中预留了一个位（PG_arch_1）作为“架构私有”。内核保证对于页面缓存页面，当这样的页面首次进入页面缓存时，它会清除这个位。
这使得这些接口可以被更高效地实现。它允许在没有用户进程映射此页面的情况下，实际的刷新可以被“推迟”（可能无限期）。参见sparc64的flush_dcache_folio和update_mmu_cache_range实现，了解如何进行此类操作的例子。
其想法是，在flush_dcache_folio()时，如果folio_flush_mapping()返回一个映射，并且对该映射调用mapping_mapped()返回%false，就标记架构私有的页面标志位。稍后，在update_mmu_cache_range()中，会检查这个标志位，如果被设置，则执行刷新并清除该标志位。
.. important::
			如果你推迟了刷新，通常很重要的一点是，实际的刷新应发生在使页面变脏的CPU存储操作所在的同一个CPU上。再次参考sparc64，了解如何处理这种情况。
``void copy_to_user_page(struct vm_area_struct *vma, struct page *page,
  unsigned long user_vaddr, void *dst, void *src, int len)``
  ``void copy_from_user_page(struct vm_area_struct *vma, struct page *page,
  unsigned long user_vaddr, void *dst, void *src, int len)``

	当内核需要复制任意数据进出任意用户页面（例如，用于ptrace()）时，它将使用这两个例程。
任何必要的缓存刷新或其他一致性操作应该在这里发生。如果处理器的指令缓存不监视CPU存储操作，很可能你需要为copy_to_user_page()刷新指令缓存。
``void flush_anon_page(struct vm_area_struct *vma, struct page *page,
  unsigned long vmaddr)``

  	当内核需要访问匿名页面的内容时，它调用此函数（目前仅get_user_pages()使用）。注意：flush_dcache_folio()故意不适用于匿名页面。默认实现是一个无操作（nop），并且应该保持这样（对于所有一致性的架构）。对于非一致性的架构，它应该刷新vmaddr处页面的缓存。
```void flush_icache_range(unsigned long start, unsigned long end)```

当内核向其将从中执行的地址存储数据时（例如加载模块时），会调用此函数。
如果指令缓存不监视存储操作，则需要此例程来刷新它。

```void flush_icache_page(struct vm_area_struct *vma, struct page *page)```

flush_icache_page的所有功能都可以在flush_dcache_folio和update_mmu_cache_range中实现。将来，希望完全移除这个接口。
最后一类API是针对内核内部故意设置别名的I/O地址范围。这些别名通过vmap/vmalloc API建立。由于内核I/O通过物理页进行，I/O子系统假定用户映射和内核偏移映射是唯一的别名。但这对于vmap别名来说并不正确，因此内核中任何尝试对vmap区域进行I/O操作的部分必须手动管理一致性。这需要在进行I/O前刷新vmap范围，并在I/O完成后使其无效。

```void flush_kernel_vmap_range(void *vaddr, int size)```

此函数刷新给定虚拟地址范围内在vmap区域中的内核缓存。这是为了确保内核在vmap范围内修改的任何数据都能对物理页可见。设计目的是使该区域安全地进行I/O操作。
请注意，此API不会同时刷新该区域的偏移映射别名。

```void invalidate_kernel_vmap_range(void *vaddr, int size)```

此函数使给定虚拟地址范围内在vmap区域中的缓存无效，防止处理器通过推测性读取数据而使缓存过期，这些数据可能正在对物理页进行I/O操作。这仅对读取vmap区域的数据是必要的。
