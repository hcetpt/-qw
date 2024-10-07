透明大页支持
============================

本文档描述了透明大页（THP）支持的设计原则及其与内存管理系统其他部分的交互。

设计原则
==================

- “优雅降级”：没有透明大页知识的内存管理组件会降级为将大页PMD映射拆分成页表项（PTES），并在必要时分割一个透明大页。因此，这些组件可以继续在常规页面或常规页表项（PTE）映射上工作。
- 如果由于内存碎片化导致大页分配失败，则应优雅地分配常规页面，并且在同一VMA中混合使用，不会出现任何失败或显著延迟，并且用户空间不会察觉。
- 如果某些任务退出并且有更多的大页变得可用（无论是立即通过伙伴系统还是通过虚拟内存），由常规页面支持的客户物理内存应自动迁移到大页上（通过khugepaged）。
- 它不需要内存预留，并且反过来尽可能使用大页（唯一可能的预留在于kernelcore=，以避免不可移动的页面导致所有内存碎片化，但这种调整并不特定于透明大页支持，而是一个适用于内核中所有动态高阶分配的一般特性）。

get_user_pages 和 follow_page
==============================

如果get_user_pages和follow_page运行在一个大页上，它们将像在hugetlbfs上一样返回头部或尾部页面。大多数GUP用户只关心页面的实际物理地址及其临时锁定以便在I/O完成后释放，所以他们永远不会注意到页面是巨大的。但是，如果任何驱动程序要篡改尾部页面的页面结构（如检查page->mapping或其他仅与头部页面相关而不是尾部页面相关的位），则应更新为跳转到检查头部页面。获取任何头部/尾部页面的引用将防止页面被任何人分割。
.. 注意::
   这些并不是对GUP API的新约束，并且它们与适用于hugetlbfs的约束相同，因此任何能够处理hugetlbfs上的GUP的驱动程序也将很好地适用于基于透明大页支持的映射。

优雅降级
==================

遍历页表但不知道巨大PMD的代码可以简单地调用split_huge_pmd(vma, pmd, addr)，其中pmd是由pmd_offset返回的。只需grep“pmd_offset”并添加split_huge_pmd（如果缺少的话，在pmd_offset返回pmd后）。由于优雅降级设计，通过一行代码更改，您可以避免编写数百甚至数千行复杂的代码来使您的代码具有大页意识。
如果您不是在遍历页表，但在代码中遇到了无法本机处理的物理大页，可以通过调用split_huge_page(page)将其拆分。这是Linux虚拟内存管理器在尝试交换出大页之前所做的事情。split_huge_page()可能会失败，如果页面被锁定，您必须正确处理这种情况。
以下是一行代码更改即可使mremap.c具有透明大页意识的例子：

```
diff --git a/mm/mremap.c b/mm/mremap.c
--- a/mm/mremap.c
+++ b/mm/mremap.c
@@ -41,6 +41,7 @@ static pmd_t *get_old_pmd(struct mm_stru
			return NULL;

		pmd = pmd_offset(pud, addr);
	+	split_huge_pmd(vma, pmd, addr);
		if (pmd_none_or_clear_bad(pmd))
			return NULL;
```

大页感知代码中的锁定
==============================

我们希望尽可能多的代码具备大页感知能力，因为调用split_huge_page()或split_huge_pmd()有开销。
为了使页表遍历具备大PMD感知能力，您需要做的就是对pmd_offset返回的PMD调用pmd_trans_huge()。您必须持有mmap_lock以读（或写）模式，以确保khugepaged不会在您下方创建一个巨大的PMD（khugepaged的collapse_huge_page以写模式持有mmap_lock加上anon_vma锁）。如果pmd_trans_huge返回false，您只需回退到旧的代码路径。如果pmd_trans_huge返回true，则必须获取页表锁（pmd_lock()）并重新运行pmd_trans_huge。获取页表锁将防止巨大的PMD在您下方转换为常规PMD（split_huge_pmd可以与页表遍历并行运行）。如果第二次pmd_trans_huge返回false，则应放弃页表锁并像以前一样回退到旧代码。否则，您可以继续处理巨大的PMD和大页。一旦完成，您可以放弃页表锁。

引用计数和透明大页
====================================

THP上的引用计数主要与复合页面上的引用计数一致：

  - get_page()/put_page()和GUP操作于folio->_refcount
- 尾部页面中的->_refcount始终为零：get_page_unless_zero()在尾部页面上永远不能成功
### PMD 条目的整体映射/取消映射以及 THP 的增加/减少
- 对于整个 THP 的 PMD 条目进行映射/取消映射时，需要增加/减少 `folio->_entire_mapcount`，同时增加/减少 `folio->_large_mapcount`。当 `_entire_mapcount` 从 -1 变为 0 或从 0 变为 -1 时，还需要增加/减少 `folio->_nr_pages_mapped` 的值（使用 ENTIRELY_MAPPED）。

### 单个页面的映射/取消映射及 PTE 条目的增加/减少
- 对于单个页面的 PTE 条目进行映射/取消映射时，需要增加/减少 `page->_mapcount`，同时增加/减少 `folio->_large_mapcount`。当 `page->_mapcount` 从 -1 变为 0 或从 0 变为 -1 时，还需要增加/减少 `folio->_nr_pages_mapped` 的值，因为这表示通过 PTE 映射的页面数量。

### `split_huge_page` 内部处理
`split_huge_page` 需要在清除所有页面结构中的 PG_head/tail 标记之前，将头部页面的引用计数分配给尾部页面。对于由页表条目获取的引用计数，这很容易实现，但我们没有足够的信息来分配任何额外的固定（例如来自 `get_user_pages`）。因此，`split_huge_page()` 拒绝拆分被固定的大型页面：它期望子页面的 `mapcount` 之和等于页面总数加一（调用 `split_huge_page` 必须有一个对头部页面的引用）。

### 使用迁移条目稳定匿名页面的 `_refcount` 和 `_mapcount`
`split_huge_page` 使用迁移条目来稳定匿名页面的 `_refcount` 和 `_mapcount`。文件页面则直接取消映射。

### 防止物理内存扫描器访问
我们对物理内存扫描器也是安全的：扫描器唯一合法获取页面引用的方式是通过 `get_page_unless_zero()`。
- 所有尾部页面在 `atomic_add()` 之前都有零 `_refcount` 值。这防止了扫描器在此时获取尾部页面的引用。在 `atomic_add()` 之后，我们不再关心 `_refcount` 的值。我们已经知道应该从头部页面解除多少引用。
- 对于头部页面，`get_page_unless_zero()` 将成功，并且我们不介意这一点。拆分后，引用将保留在头部页面上。

### 注意 `split_huge_pmd()` 的引用计数没有限制
`split_huge_pmd()` 在引用计数方面没有任何限制：可以在任何时候拆分 PMD 并且永远不会失败。

### 部分取消映射与 `deferred_split_folio()`
#### 部分取消映射和延迟拆分
部分取消映射 THP（通过 `munmap()` 或其他方式）不会立即释放内存。相反，我们在 `folio_remove_rmap_*()` 中检测到 THP 的一个子页面未被使用，并在内存压力出现时将其排队以进行拆分。拆分会释放未使用的子页面。

### 立即拆分页面不是选项
由于检测部分取消映射的位置存在锁定上下文问题，立即拆分页面不是一个可行的选择。此外，在许多情况下，部分取消映射发生在进程退出时（如果 THP 跨越 VMA 边界）。
`deferred_split_folio()` 函数用于将一个 folio 排队以待分割。
实际的分割操作将在我们通过收缩器（shrinker）接口遇到内存压力时进行。
