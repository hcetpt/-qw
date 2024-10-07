==============================
不可驱逐的LRU基础设施
==============================

.. contents:: 目录


简介
============

本文档描述了Linux内存管理器的“不可驱逐的LRU”基础设施及其用于管理多种类型的“不可驱逐”的页。本文档试图提供该机制的整体理由以及驱动实现的一些设计决策的理由。后者的理由在实现描述的上下文中进行讨论。诚然，通过阅读代码可以获得实现细节——“它做了什么？”——希望下面的描述通过回答“为什么这样做？”来增加价值。
不可驱逐的LRU
===================

不可驱逐的LRU设施添加了一个额外的LRU列表以跟踪不可驱逐的页，并将这些页隐藏起来不被vmscan扫描。这一机制基于Red Hat的Larry Woodman提出的一片补丁，用以解决Linux中与页回收相关的几个可扩展性问题。这些问题已在大型内存x86_64系统的客户站点上观察到。

举个例子来说明这一点，在一个非NUMA的x86_64平台上，如果主内存为128GB，则单个节点中将有超过3200万个4K页。当其中大部分页由于某种原因不可驱逐时，vmscan会花费大量时间扫描LRU列表寻找少量可驱逐的页。这可能导致所有CPU连续数小时或数天地花费100%的时间在vmscan上，导致系统完全无响应。

不可驱逐列表解决了以下几类不可驱逐的页：

 * 被ramfs拥有的页
* 使用noswap挂载选项由tmpfs拥有的页
* 映射到使用SHM_LOCK锁定的共享内存区域的页
* 映射到VM_LOCKED（通过mlock()锁定）虚拟地址空间的页

该基础设施未来也可能能够处理其他使页不可驱逐的情况，无论是按定义还是按实际情况。
不可驱逐的LRU页列表
------------------------------

不可驱逐的LRU页列表其实是一个谎言。它从来不是一个LRU排序的列表，而是作为LRU排序的匿名和文件、活跃和非活跃页列表的伴生列表；而现在它甚至不是一个页列表。但遵循熟悉的惯例，在本文档和源码中，我们常常将其想象为第五个LRU页列表。
不可驱逐的LRU基础设施由每个节点上的额外LRU列表（称为“不可驱逐”列表）和一个关联的页志标志`PG_unevictable`组成，该标志表示该页志正在被不可驱逐列表管理。

`PG_unevictable`标志类似于并且与`PG_active`标志互斥，因为它指示当`PG_lru`设置时，页志位于哪个LRU列表上。

不可驱逐的LRU基础设施以几种原因为了将不可驱逐的页志保持在类似LRU的列表中：

1. 我们可以“像处理系统中的其他页志一样处理不可驱逐的页志——这意味着我们可以使用相同的代码来操作它们，相同的代码来隔离它们（用于迁移等），相同的代码来跟踪统计数据等...”[Rik van Riel]

2. 我们希望能够在节点之间迁移不可驱逐的页志以进行内存碎片整理、工作负载管理和内存热插拔。Linux内核只能迁移能够成功从LRU列表中隔离出来的页志（或“可移动”页面：在此不考虑）。如果我们不在类似LRU的列表中维护页志，而是放在其他地方，在那里它们可以通过`folio_isolate_lru()`检测到，我们将阻止它们的迁移。

不可驱逐列表不会区分文件支持的和交换支持的匿名页志。这种区分仅在这些页志实际上是可驱逐的情况下才重要。

不可驱逐列表受益于最初由Christoph Lameter提出并发布的每个节点LRU列表和统计信息的“数组化”。

### 内存控制组交互

不可驱逐的LRU设施通过扩展`lru_list`枚举与内存控制组[即内存控制器；参见Documentation/admin-guide/cgroup-v1/memory.rst]进行交互。
由于每个节点LRU列表的“数组化”，内存控制器数据结构自动获得了每个节点的不可驱逐列表（每个`lru_list`枚举元素一个）。内存控制器跟踪页面在不可驱逐列表上的进出情况。

当一个内存控制组面临内存压力时，控制器不会尝试回收不可驱逐列表上的页面。这有几个效果：

1. 因为这些页面在不可驱逐列表上是“隐藏”的，回收过程可以更高效，只处理那些有机会被回收的页面。

2. 另一方面，如果控制组中分配给的页面中有太多不可驱逐的页面，则控制组任务的工作集中可驱逐的部分可能无法适应可用内存。这可能导致控制组出现颠簸或触发OOM杀死任务。

### 标记地址空间为不可驱逐

对于如ramfs这样的设施，附着在地址空间上的任何页面都不应被驱逐。为了防止任何此类页面被驱逐，提供了地址空间标志`AS_UNEVICTABLE`，文件系统可以使用一些包装函数来操纵它：

* `void mapping_set_unevictable(struct address_space *mapping);`

  将地址空间标记为完全不可驱逐。
``void mapping_clear_unevictable(struct address_space *mapping);``

将地址空间标记为可驱逐的。

``int mapping_unevictable(struct address_space *mapping);``

查询地址空间，并在完全不可驱逐时返回真值。

这些函数目前在内核中有三个使用场景：

1. 由ramfs在其inode创建时标记其地址空间，并且该标记在整个inode生命周期中保持不变。
2. 由SYSV SHM在其地址空间被SHM_LOCK锁定时进行标记，直到调用SHM_UNLOCK为止。
   需要注意的是，SHM_LOCK不要求将已交换出的页面换入内存；如果应用程序希望确保页面在内存中，则必须手动访问这些页面。
3. 由i915驱动程序在其地址空间被固定时进行标记，直到取消固定。i915驱动程序标记的不可驱逐内存的大致大小可以通过debugfs/dri/0/i915_gem_objects中的受限制对象大小来查看。

检测不可驱逐页面
-------------------

mm/internal.h中的folio_evictable()函数通过上述查询函数（参见 :ref:`Marking address spaces unevictable <mark_addr_space_unevict>` 部分）检查AS_UNEVICTABLE标志，以确定一个folio是否可驱逐。

对于那些在填充后被标记为不可驱逐的地址空间（例如SHM区域），锁操作（如SHM_LOCK）可以是懒惰的，并不需要像mlock()那样填充该区域的页表，也不需要特别努力地将SHM_LOCK区域内的任何页面推送到不可驱逐列表。相反，当vmscan在回收扫描过程中遇到这些folio时会处理这些事务。

在解锁操作（如SHM_UNLOCK）时，解锁器（如shmctl()）必须扫描该区域中的页面，并在没有其他条件保持它们不可驱逐的情况下“营救”它们脱离不可驱逐列表。如果一个不可驱逐的区域被销毁，在释放过程中也会“营救”这些页面脱离不可驱逐列表。

此外，folio_evictable()还会通过调用folio_test_mlocked()来检查已被mlock锁定的folio。当一个folio被错误地加载到VM_LOCKED VMA或在被设置为VM_LOCKED的VMA中找到时，会设置此标记。
### Vmscan 对不可驱逐页表的处理
---------------------------------------

如果在故障路径中移除了不可驱逐的页表，或者在 `mlock()` 或 `mmap()` 时将其移到不可驱逐列表中，那么 vmscan 只会在这些页表再次变得可驱逐（例如通过 `munlock()`）并从不可驱逐列表中“解救”出来后才会遇到这些页表。然而，在某些情况下，为了方便，我们可能会决定将不可驱逐的页表留在常规的活动/非活动 LRU 列表中让 vmscan 处理。vmscan 在所有 `shrink_{active|inactive|page}_list()` 函数中检查此类页表，并会“移除”遇到的此类页表：也就是说，它会将这些页表转移到当前扫描的内存 cgroup 和节点的不可驱逐列表中。

在某些情况下，一个页表可能映射到一个 VM_LOCKED 的 VMA 中，但该页表没有设置 mlocked 标志。这样的页表将会一直到达 `shrink_active_list()` 或 `shrink_page_list()`，并在 vmscan 遍历 `folio_referenced()` 或 `try_to_unmap()` 中的反向映射时被检测到。当该页表被缩减器释放时，它会被移到不可驱逐列表中。

要“移除”一个不可驱逐的页表，vmscan 只需在释放页表锁之后使用 `folio_putback_lru()` 将该页表放回 LRU 列表中——这是 `folio_isolate_lru()` 的逆操作。由于解锁后可能导致页表变得可驱逐的状态发生变化，`__pagevec_lru_add_fn()` 会在将页表放入不可驱逐列表之前重新检查其不可驱逐状态。

### MLOCKED 页
===============

不可驱逐页表列表对于 `mlock()` 也非常有用，除了用于 ramfs 和 SYSV SHM。请注意，`mlock()` 只在 CONFIG_MMU=y 的情况下可用；而在 NOMMU 情况下，所有映射实际上都是 mlocked 的。

### 历史
-------

“不可驱逐的 mlocked 页”基础设施基于 Nick Piggin 最初发布的一个 RFC 补丁 “mm: mlocked pages off LRU”。Nick 发布了他的补丁作为替代 Christoph Lameter 发布的一个补丁以实现相同的目标：隐藏 mlocked 页不受 vmscan 管理。

在 Nick 的补丁中，他使用了 `struct page` 的 LRU 列表链接字段作为一个计数器来记录映射该页的 VM_LOCKED VMA 数量（Rik van Riel 在三年前也有同样的想法）。但是，这种使用链接字段作为计数的方式阻止了页面在 LRU 列表上的管理，因此 mlocked 页无法迁移，因为 `isolate_lru_page()` 无法检测到它们，并且 LRU 列表链接字段也不可用于迁移子系统。

Nick 解决了这个问题，通过在尝试隔离 mlocked 页之前将其放回 LRU 列表中，从而放弃了 VM_LOCKED VMA 的计数。当 Nick 的补丁与不可驱逐 LRU 工作整合时，计数被替换为在 munlocking 时遍历反向映射来确定是否还有其他 VM_LOCKED VMA 映射该页。

然而，每次 munlock 时遍历反向映射既丑陋又低效，并且可能导致文件 rmap 锁上的灾难性竞争，尤其是在许多进程试图退出时。在 5.18 版本中，保持不可驱逐 LRU 列表链接字段中的 mlock_count 的想法被重新启用并投入使用，而不会阻止 mlocked 页的迁移。这就是为什么“不可驱逐 LRU 列表”现在不能是一个页面链表的原因；但实际上并没有使用那个链表——尽管它的大小仍然被维护用于 meminfo。

### 基本管理
-------------

mlocked 页——映射到 VM_LOCKED VMA 的页——是一类不可驱逐的页。当这样的页被内存管理系统“注意到”时，该页会被标记为 PG_mlocked 标志。这可以通过 PageMlocked() 函数进行操作。
当一个PG_mlocked页面被添加到LRU时，它会被放置在不可驱逐列表中。这样的页面可以在多个地方被内存管理“注意到”：

1. 在处理mlock()、mlock2()和mlockall()系统调用时；
2. 在处理带有MAP_LOCKED标志的mmap()系统调用时；
3. 在一个已经通过mlockall()调用并设置了MCL_FUTURE标志的任务中进行mmap时；
4. 在故障路径中或当VM_LOCKED堆栈段扩展时；
5. 如上所述，在尝试通过folio_referenced()或try_to_unmap释放VM_LOCKED VMA中的页面时。

当mlocked页面解锁并从不可驱逐列表中解救出来的情况如下：

1. 通过munlock()或munlockall()系统调用解锁其映射范围；
2. 从最后一个映射该页面的VM_LOCKED VMA中被munmap()移除，包括在任务退出时的unmap；
3. 当页面从最后一个映射文件的VM_LOCKED VMA中被截断时；
4. 在页面在VM_LOCKED VMA中被复制写时。

### mlock()、mlock2()、mlockall() 系统调用处理

mlock()、mlock2() 和 mlockall() 系统调用处理器会对调用指定范围内每个VMA调用mlock_fixup()。对于mlockall()而言，这是任务的整个活动地址空间。需要注意的是，mlock_fixup()用于锁定和解锁内存范围。如果对已经VM_LOCKED的VMA调用mlock()或对非VM_LOCKED的VMA调用munlock()，则被视为无效操作，mlock_fixup()会直接返回。

如果VMA通过了下面“过滤特殊VMA”部分描述的一些过滤条件，mlock_fixup()将尝试与邻近的VMA合并或将VMA的一部分分离出来，如果范围没有覆盖整个VMA的话。然后通过mlock_vma_pages_range()经由walk_page_range()经由mlock_pte_range()经由mlock_folio()标记已经在VMA中的所有页面为mlocked。

在系统调用返回之前，do_mlock() 或 mlockall() 会调用__mm_populate()通过get_user_pages()加载剩余的页面，并在加载过程中将其标记为mlocked。

需要注意的是，被锁定的VMA可能被映射为PROT_NONE。在这种情况下，get_user_pages()将无法加载这些页面。这没问题。如果这些页面最终被加载到了这个VM_LOCKED VMA中，它们将在故障路径中被处理——这也是mlock2()的MLOCK_ONFAULT区域的处理方式。

对于每个需要加载到VMA中的PTE（或PMD），页添加rmap函数会调用mlock_vma_folio()，当VMA是VM_LOCKED时（除非它是透明大页的部分PTE映射），mlock_vma_folio()会调用mlock_folio()。或者当是一个新分配的匿名页面时，folio_add_lru_vma()会调用mlock_new_folio()：类似于mlock_folio()，但由于这个页面被独占持有并且已知不在LRU上，因此可以做出更好的判断。

mlock_folio()立即设置PG_mlocked，然后将页面放入CPU的mlock folio批处理队列，以便在lru_lock下批量完成其余工作。__mlock_folio()设置PG_unevictable，初始化mlock_count并将页面移动到不可驱逐状态（“不可驱逐LRU”，但使用mlock_count代替LRU链接）。如果页面已经是PG_lru、PG_unevictable和PG_mlocked，则只需递增mlock_count。

但在实践中，这可能不理想：页面可能尚未在LRU上，或者可能暂时从LRU隔离。在这种情况下，不能修改mlock_count字段，但会在__munlock_folio()将页面返回到“LRU”时将其设置为0。为了防止页面无限期地处于不可驱逐状态，总是将mlock_count保持在低位，以便在munlock时页面能被解救到可驱逐LRU，如果vmscan在VM_LOCKED VMA中找到它，稍后可能会再次mlock。

### 过滤特殊VMA

mlock_fixup()过滤了几类“特殊”VMA：

1. 设置了VM_IO或VM_PFNMAP的VMA完全被跳过。这些映射后面的页面本质上已经被固定，因此无需标记为mlocked。无论如何，大多数页面没有struct page来标记页面。由于这一点，get_user_pages()将为这些VMA失败，因此没有尝试访问它们的意义。
2) 映射了 hugetlbfs 页面的 VMAs 已经有效地被固定在内存中。我们既不需要也不希望对这些页面使用 mlock()。但是，__mm_populate() 包含了 hugetlbfs 范围，分配了巨大的页面并填充了 PTEs。

3) 设置了 VM_DONTEXPAND 的 VMAs 通常是用户空间对内核页面的映射，例如 VDSO 页面、relay 通道页面等。这些页面本质上是不可驱逐的，并且不在 LRU 列表上管理。__mm_populate() 包含了这些范围，如果还未填充，则填充相应的 PTEs。

4) 设置了 VM_MIXEDMAP 的 VMAs 并没有标记为 VM_LOCKED，但 __mm_populate() 仍然包含了这些范围，如果还未填充，则填充相应的 PTEs。

需要注意的是，对于所有这些特殊的 VMAs，mlock_fixup() 都不会设置 VM_LOCKED 标志。因此，在 munlock()、munmap() 或任务退出时，我们不必处理它们。mlock_fixup() 也不会将这些 VMAs 计入任务的 "locked_vm" 中。

### munlock()/munlockall() 系统调用处理
-------------------------------------------

munlock() 和 munlockall() 系统调用由与 mlock()、mlock2() 和 mlockall() 相同的 mlock_fixup() 函数处理。

如果调用 munlock 解锁一个已经解锁的 VMA，mlock_fixup() 将直接返回。

由于上述的 VMA 过滤机制，任何“特殊”VMA 都不会设置 VM_LOCKED 标志。因此，这些 VMA 在 munlock 时会被忽略。

如果 VMA 设置了 VM_LOCKED，mlock_fixup() 再次尝试合并或拆分指定的范围。然后通过 mlock_vma_pages_range() 经过 walk_page_range() 经过 mlock_pte_range() 最终通过 munlock_folio() 解锁 VMA 中的所有页面——这与锁定 VMA 范围时使用的函数相同，只是带有新的标志表明这是在执行 munlock() 操作。

munlock_folio() 使用 mlock pagevec 批量处理要在 lru_lock 下进行的工作，由 __munlock_folio() 完成。__munlock_folio() 减少 folio 的 mlock_count，当该计数达到 0 时，清除 mlocked 标志和不可驱逐标志，并将 folio 从不可驱逐状态移动到不活跃的 LRU。

但在实践中，这可能无法理想地工作：folio 可能还没有到达“不可驱逐的 LRU”，或者它可能暂时被隔离了。在这种情况下，其 mlock_count 字段是不可用的，必须假设为 0，以便 folio 被恢复到可驱逐的 LRU，然后如果 vmscan 发现它在一个 VM_LOCKED 的 VMA 中，也许会再次被 mlock。
迁移锁定页面
-----------------------

正在迁移的页面已被从LRU列表中隔离，并在整个页面解除映射、更新页面地址空间条目并复制内容和状态的过程中保持锁定，直到页表项被替换为指向新页面的条目。Linux支持迁移锁定（mlocked）页面和其他不可驱逐（unevictable）页面。当旧页面从最后一个VM_LOCKED VMA中解除映射时，会清除PG_mlocked标志；当新页面在VM_LOCKED VMA中替换迁移条目时，会设置PG_mlocked标志。如果页面因被锁定而不可驱逐，则在设置或清除PG_mlocked的同时也会跟随设置或清除PG_unevictable；但如果页面因其他原因不可驱逐，则需显式复制PG_unevictable。需要注意的是，页面迁移可能会与同一页面的锁定（mlock）或解锁（munlock）发生竞争。但由于页面迁移需要解除所有旧页面的PTE映射（包括VM_LOCKED中的munlock），然后再映射新页面（包括VM_LOCKED中的mlock），因此这通常不是问题。页表锁提供了足够的同步。

然而，由于mlock_vma_pages_range()首先会在任何页面锁定之前将VMA标记为VM_LOCKED，如果其中一个页面在mlock_pte_range()处理到它之前被迁移了，则会导致mlock_count计数重复。为了避免这种情况，mlock_vma_pages_range()会暂时将VMA标记为VM_IO，以便mlock_vma_folio()跳过它。

为了完成页面迁移，我们会在之后将旧页面和新页面重新放回LRU列表中。成功时，释放迁移过程中持有的引用计数后，会释放“不需要”的页面——即成功时的旧页面或失败时的新页面。

压缩锁定页面
------------------------

可以扫描内存映射以查找可压缩区域，默认行为是允许移动不可驱逐页面。/proc/sys/vm/compact_unevictable_allowed 控制这一行为（详见Documentation/admin-guide/sysctl/vm.rst）。压缩工作主要由页面迁移代码处理，与上述迁移锁定页面的工作流程相同。

锁定透明大页
-------------------------------

一个透明大页由LRU列表上的单一条目表示。因此，我们只能将整个复合页面设为不可驱逐，而不能单独设置子页面。

如果用户尝试锁定大页的一部分，并且没有用户锁定整个大页，我们希望其余部分仍然可以回收。
我们不能仅在部分 mlock() 时分割页面，因为 split_huge_page() 可能会失败，并且我们不希望引入新的间歇性失败模式。我们通过将 PTE-mlocked 的大页面保留在可回收的 LRU 列表上来处理这个问题：位于 VM_LOCKED VMA 边界的 PMD 将被拆分为一个 PTE 表。这样，大页面对 vmscan 是可访问的。在内存压力下，该页面将被拆分，属于 VM_LOCKED VMAs 的子页面将被移到不可回收的 LRU 列表中，其余部分可以被回收。

/proc/meminfo 中的 Unevictable 和 Mlocked 数量不包括那些仅由 VM_LOCKED VMAs 中的 PTE 映射的透明大页的部分。

mmap(MAP_LOCKED) 系统调用处理
-------------------------------------

除了 mlock()、mlock2() 和 mlockall() 系统调用之外，应用程序还可以通过向 mmap() 调用提供 MAP_LOCKED 标志来请求锁定一段内存。然而，这里有一个重要且微妙的区别：如果范围无法被换入（例如因为 mm_populate 失败）则 mmap() + mlock() 会失败并返回 ENOMEM，而 mmap(MAP_LOCKED) 不会失败。映射区域仍具有锁定区域的属性——页面不会被换出——但仍然可能发生重大页故障以换入内存。

此外，任何扩展堆的 mmap() 调用或 brk() 调用，如果任务之前使用带有 MCL_FUTURE 标志的 mlockall() 调用，则新映射的内存会被 mlock。在不可回收/mlock 更改之前，内核只是调用 make_pages_present() 来分配页面并填充页表。

要在不可回收/mlock 基础设施下锁定一段内存，mmap() 处理程序和任务地址空间扩展函数会调用 populate_vma_page_range() 并指定要锁定的 VMA 和地址范围。

munmap()/exit()/exec() 系统调用处理
-------------------------------------------

当通过显式的 munmap() 调用或退出（exit）或执行（exec）处理中的内部卸映射来卸载已锁定的内存区域时，我们必须解锁这些页面，如果我们正在移除最后一个映射这些页面的 VM_LOCKED VMA。
在不可驱逐（unevictable）/锁定内存（mlock）更改之前，锁定内存（mlocking）并没有以任何方式标记页面，因此解除映射（unmapping）它们不需要任何处理。

对于每个从VMA（Virtual Memory Area）解除映射的PTE（或PMD），`folio_remove_rmap_*()`会调用`munlock_vma_folio()`，而当VMA被设置为`VM_LOCKED`时（除非它是透明大页的一部分的PTE映射），`munlock_vma_folio()`会进一步调用`munlock_folio()`。
`munlock_folio()`使用mlock pagevec来批量处理需要在`lru_lock`下完成的工作。`__munlock_folio()`会递减`folio`的`mlock_count`，当该计数达到0时，清除`mlocked`标志和`unevictable`标志，并将`folio`从不可驱逐状态移动到非活跃LRU（Least Recently Used）列表中。

但实际上，这可能无法理想地工作：`folio`可能尚未到达“不可驱逐LRU”，或者它可能暂时与其隔离。在这种情况下，其`mlock_count`字段是不可用的，并且必须假定为0：以便将`folio`恢复到可驱逐LRU中，然后如果vmscan在`VM_LOCKED` VMA中找到它，也许稍后会再次将其锁定。

### 截断锁定页面

文件截断或打孔操作强制从用户空间解除映射已删除的页面；截断甚至会解除映射并删除任何从现在要截断的文件页面通过Copy-On-Write复制的私有匿名页面。
锁定的页面可以通过这种方式解除锁定并删除：类似于`munmap()`，对于每个从VMA解除映射的PTE（或PMD），`folio_remove_rmap_*()`会调用`munlock_vma_folio()`，而当VMA被设置为`VM_LOCKED`时（除非它是透明大页的一部分的PTE映射），`munlock_vma_folio()`会进一步调用`munlock_folio()`。
然而，如果有竞争的`munlock()`调用，由于`mlock_vma_pages_range()`通过清除VMA上的`VM_LOCKED`标志开始解除锁定，在解除锁定所有页面之前，如果其中一个页面在`mlock_pte_range()`到达之前已被截断或打孔解除映射，则不会被识别为此VMA的锁定页面，并且不会从`mlock_count`中减去。在这种罕见的情况下，页面可能会在完全解除映射之后仍然显示为`PG_mlocked`：并且留给`release_pages()`（或`__page_cache_release()`）在释放前清除它并更新统计信息（这一事件在`/proc/vmstat`中的`unevictable_pgs_cleared`计数，通常为0）。

### `shrink_*_list()`中的页面回收

vmscan的`shrink_active_list()`会剔除任何明显不可驱逐的页面——即`!page_evictable(page)`的页面——并将这些页面转移到不可驱逐列表。
但是，`shrink_active_list()`只能看到那些已经进入活动/非活跃LRU列表的不可驱逐页面。注意，这些页面没有设置`PG_unevictable`标志——否则它们将位于不可驱逐列表上，`shrink_active_list()`将永远看不到它们。

一些这样的位于LRU列表上的不可驱逐页面的例子包括：

1. 在首次分配时被放置在LRU列表上的ramfs页面。
(2) 被 SHM_LOCK 锁定的共享内存页面。shmctl(SHM_LOCK) 不会尝试分配或触发共享内存区域中的页面故障。这种情况发生在应用程序在锁定段后首次访问页面时。

(3) 仍然映射到 VM_LOCKED VMAs 的页面，这些页面应该被标记为 mlocked，但由于某些事件导致 mlock_count 过低，因此过早地被 munlocked。

vmscan 的 shrink_inactive_list() 和 shrink_page_list() 也会将发现在非活动列表上的明显不可驱逐的页面转移到相应的内存 cgroup 和节点不可驱逐列表。

rmap 的 folio_referenced_one() 函数通过 vmscan 的 shrink_active_list() 或 shrink_page_list() 调用，并且 rmap 的 try_to_unmap_one() 函数通过 shrink_page_list() 调用，检查 (3) 仍然映射到 VM_LOCKED VMAs 的页面，并调用 mlock_vma_folio() 来修正它们。当这些页面由收缩器释放时，它们会被转移到不可驱逐列表中。
