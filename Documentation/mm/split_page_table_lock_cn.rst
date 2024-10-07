分割页表锁
=====================

最初，mm->page_table_lock自旋锁保护了mm_struct中的所有页表。但这种方法由于锁的高竞争性导致多线程应用程序的页面错误处理可扩展性较差。为了提高可扩展性，引入了分割页表锁。使用分割页表锁时，我们为每个表提供单独的锁以序列化对表的访问。目前，我们为PTE和PMD表使用分割锁。更高层次表的访问由mm->page_table_lock保护。有用于锁定/解锁表和其他访问函数的帮助器：

- pte_offset_map_lock()
映射PTE并获取PTE表锁，返回指向PTE及其PTE表锁的指针，如果没有PTE表则返回NULL；
- pte_offset_map_nolock()
映射PTE，返回指向PTE及其PTE表锁的指针（未获取），如果没有PTE表则返回NULL；
- pte_offset_map()
映射PTE，返回指向PTE的指针，如果没有PTE表则返回NULL；
- pte_unmap()
取消映射PTE表；
- pte_unmap_unlock()
解锁并取消映射PTE表；
- pte_alloc_map_lock()
如果需要分配PTE表并获取其锁，返回指向PTE及其锁的指针，如果分配失败则返回NULL；
- pmd_lock()
获取PMD表锁，返回指向已获取锁的指针；
- pmd_lockptr()
返回指向PMD表锁的指针；

对于PTE表的分割页表锁在编译时启用，如果CONFIG_SPLIT_PTLOCK_CPUS（通常为4）小于或等于NR_CPUS。如果禁用分割锁，则所有表都由mm->page_table_lock保护。如果对PTE表启用了分割锁，并且架构支持（见下文），则PMD表的分割页表锁也启用。

HugeTLB与分割页表锁
=================================

HugeTLB可以支持多种页面大小。我们仅在PMD级别使用分割锁，而不是PUD。
HugeTLB特定的帮助器：

- huge_pte_lock()
获取PMD_SIZE页面的PMD分割锁，否则获取mm->page_table_lock；
- huge_pte_lockptr()
返回指向表锁的指针；

架构对分割页表锁的支持
===================================================

无需特别启用PTE分割页表锁：所需的一切都由pagetable_pte_ctor()和pagetable_pte_dtor()完成，这两个函数必须在PTE表分配/释放时调用。
确保架构不使用slab分配器进行页表分配：slab使用page->slab_cache来管理其页面
此字段与page->ptl共享存储空间
只有当您有超过两级页表时，PMD分割锁才有意义。
PMD 分离锁启用需要在分配 PMD 表时调用 `pagetable_pmd_ctor()`，并在释放时调用 `pagetable_pmd_dtor()`。

分配通常发生在 `pmd_alloc_one()` 中，释放则发生在 `pmd_free()` 和 `pmd_free_tlb()` 中。但请确保覆盖所有 PMD 表的分配/释放路径，例如，在 X86_PAE 的 `pgd_alloc()` 中预分配一些 PMD。

完成上述所有步骤后，可以设置 `CONFIG_ARCH_ENABLE_SPLIT_PMD_PTLOCK`。

注意：`pagetable_pte_ctor()` 和 `pagetable_pmd_ctor()` 可能会失败——必须妥善处理这种情况。

`page->ptl`
===========

`page->ptl` 用于访问分离页表锁，其中 `page` 是包含该表的 `struct page`。它与 `page->private`（以及其他几个字段）共享存储空间。

为了避免增加 `struct page` 的大小并获得最佳性能，我们使用了一个技巧：

- 如果 `spinlock_t` 的大小不超过 `long` 的大小，我们就使用 `page->ptr` 作为自旋锁，这样可以避免间接访问并节省一个缓存行。
- 如果 `spinlock_t` 的大小大于 `long` 的大小，我们使用 `page->ptl` 作为指向 `spinlock_t` 的指针，并动态分配自旋锁。这允许在启用 `DEBUG_SPINLOCK` 或 `DEBUG_LOCK_ALLOC` 时使用分离锁，但需要额外的一个缓存行用于间接访问。

在 `pagetable_pte_ctor()` 中为 PTE 表分配 `spinlock_t`，在 `pagetable_pmd_ctor()` 中为 PMD 表分配 `spinlock_t`。

请注意，永远不要直接访问 `page->ptl` —— 应使用适当的辅助函数。
