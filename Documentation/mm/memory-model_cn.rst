SPDX 许可证标识符：GPL-2.0

=====================
物理内存模型
=====================

系统中的物理内存可以通过不同的方式寻址。最简单的情况是物理内存从地址 0 开始，并连续扩展到最大地址。然而，这个范围内可能包含一些 CPU 无法访问的小空洞。因此，可能会有多个完全独立地址的连续范围。另外，别忘了 NUMA（非统一内存访问），其中不同的内存库连接到不同的 CPU。

Linux 使用两种内存模型之一来抽象这种多样性：FLATMEM 和 SPARSEMEM。每个架构定义了它支持哪些内存模型，默认的内存模型是什么，以及是否可以手动覆盖该默认值。

所有内存模型都使用 `struct page` 来跟踪物理页框的状态，并将其组织在一个或多个数组中。无论选择哪种内存模型，物理页框号（PFN）与其对应的 `struct page` 都存在一对一的映射。每个内存模型定义了 `pfn_to_page` 和 `page_to_pfn` 辅助函数，允许从 PFN 转换为 `struct page` 及其反向转换。

FLATMEM
=======

最简单的内存模型是 FLATMEM。此模型适用于非 NUMA 系统，且物理内存是连续的或基本连续的。

在 FLATMEM 内存模型中，有一个全局的 `mem_map` 数组，用于映射整个物理内存。对于大多数架构，空洞也有 `mem_map` 数组中的条目。对应于这些空洞的 `struct page` 对象永远不会被完全初始化。

为了分配 `mem_map` 数组，特定架构的设置代码应该调用 `free_area_init` 函数。然而，在调用 `memblock_free_all` 函数之前，映射数组是不可用的，该函数将所有内存交给页面分配器。

一个架构可以释放 `mem_map` 数组中不覆盖实际物理页的部分。在这种情况下，特定架构的 `pfn_valid` 实现应该考虑 `mem_map` 中的空洞。

在 FLATMEM 模型中，PFN 和 `struct page` 之间的转换非常直接：`PFN - ARCH_PFN_OFFSET` 是 `mem_map` 数组的一个索引。
`ARCH_PFN_OFFSET` 定义了物理内存起始地址不同于 0 的系统的第一个页框号。

SPARSEMEM
=========

SPARSEMEM 是 Linux 中最灵活的内存模型，并且是唯一支持多种高级功能（如物理内存的热插拔、非易失性内存设备的替代内存映射以及大型系统内存映射的延迟初始化）的内存模型。

SPARSEMEM 模型将物理内存表示为一系列区段。一个区段由 `struct mem_section` 表示，其中包含 `section_mem_map`，逻辑上是一个指向 `struct page` 数组的指针。然而，它存储了一些有助于管理区段的特殊信息。区段大小和最大区段数由每个支持 SPARSEMEM 的架构定义的常量 `SECTION_SIZE_BITS` 和 `MAX_PHYSMEM_BITS` 指定。虽然 `MAX_PHYSMEM_BITS` 是架构支持的实际物理地址宽度，但 `SECTION_SIZE_BITS` 是一个任意值。

最大区段数表示为 `NR_MEM_SECTIONS`，定义如下：

\[ NR\_MEM\_SECTIONS = 2 ^ {(MAX\_PHYSMEM\_BITS - SECTION\_SIZE\_BITS)} \]

`mem_section` 对象被组织成一个二维数组 `mem_sections`。这个数组的大小和位置取决于 `CONFIG_SPARSEMEM_EXTREME` 和最大可能的区段数：

* 当 `CONFIG_SPARSEMEM_EXTREME` 被禁用时，`mem_sections` 数组是静态的，有 `NR_MEM_SECTIONS` 行。每一行包含一个 `mem_section` 对象。
* 当 `CONFIG_SPARSEMEM_EXTREME` 被启用时，`mem_sections` 数组是动态分配的。每一行包含 `PAGE_SIZE` 大小的 `mem_section` 对象，行数根据所有内存区段进行计算。

架构设置代码应调用 `sparse_init()` 来初始化内存区段和内存映射。

在 SPARSEMEM 模型中，有两种方式将 PFN 转换为对应的 `struct page`：一种是“经典稀疏”方式，另一种是“稀疏 vmemmap”方式。选择在编译时进行，取决于 `CONFIG_SPARSEMEM_VMEMMAP` 的值。

经典稀疏方式将页面所在的区段编号编码到 `page->flags` 中，并使用 PFN 的高位来访问映射该页框的区段。在区段内部，PFN 是页面数组的索引。

稀疏 vmemmap 方式使用虚拟映射的内存映射来优化 `pfn_to_page` 和 `page_to_pfn` 操作。有一个全局的 `struct page *vmemmap` 指针，指向一个虚拟连续的 `struct page` 对象数组。PFN 是该数组的索引，`struct page` 相对于 `vmemmap` 的偏移量就是该页面的 PFN。

为了使用 vmemmap，架构需要预留一段虚拟地址范围，用于映射包含内存映射的物理页面，并确保 `vmemmap` 指向该范围。此外，架构还应该实现 `vmemmap_populate` 方法，以分配物理内存并为虚拟内存映射创建页表。如果架构对 vmemmap 映射没有特殊要求，可以使用通用内存管理提供的默认方法 `vmemmap_populate_basepages`。
虚拟映射内存图允许将 `struct page` 对象存储在持久内存设备上的预分配存储中。这种存储通过 `struct vmem_altmap` 表示，并最终通过一系列函数调用传递给 `vmemmap_populate()`。`vmemmap_populate()` 的实现可以使用 `vmem_altmap` 和 `vmemmap_alloc_block_buf` 辅助函数在持久内存设备上分配内存图。

**ZONE_DEVICE**
===============
`ZONE_DEVICE` 设施基于 `SPARSEMEM_VMEMMAP` 提供针对设备驱动程序识别的物理地址范围的 `struct page` `mem_map` 服务。`ZONE_DEVICE` 的“设备”特性体现在这些地址范围的页面对象从不标记为在线，且为了保持内存处于活动状态，必须对设备而不是仅仅对页面进行引用。`ZONE_DEVICE` 通过 `devm_memremap_pages` 函数执行足够的内存热插拔操作，以启用特定页框编号 (PFN) 范围的 `pfn_to_page`、`page_to_pfn` 和 `get_user_pages` 服务。由于页面的引用计数永远不会低于 1，因此页面不会被跟踪为自由内存，并且页面的 `struct list_head lru` 空间被重新用于反向引用到映射该内存的主机设备/驱动程序。

虽然 `SPARSEMEM` 将内存表示为多个段的集合（可选地收集到内存块中），但 `ZONE_DEVICE` 用户需要更细粒度地填充 `mem_map`。鉴于 `ZONE_DEVICE` 内存从不标记为在线，因此其内存范围也不会通过 sysfs 内存热插拔 API 在内存块边界暴露出来。实现依赖于这种用户 API 约束的缺失，允许指定小于段大小的内存范围给内存热插拔的上半部分 `arch_add_memory`。子段支持允许跨架构通用的 2MB 对齐粒度用于 `devm_memremap_pages`。

`ZONE_DEVICE` 的用户包括：

* pmem：将平台持久内存映射为直接 I/O 目标，通过 DAX 映射使用。
* hmm：扩展 `ZONE_DEVICE` 以添加 `->page_fault()` 和 `->page_free()` 事件回调，允许设备驱动程序协调与设备内存相关的内存管理事件，通常为 GPU 内存。详见 `Documentation/mm/hmm.rst`。
* p2pdma：创建 `struct page` 对象，使 PCI/-E 拓扑中的对等设备能够协调它们之间的直接 DMA 操作，即绕过主机内存。
