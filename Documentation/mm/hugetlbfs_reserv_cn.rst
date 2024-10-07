### Hugetlbfs 预留

#### 概述
在《Documentation/admin-guide/mm/hugetlbpage.rst》中描述的巨页通常是为应用程序预先分配的。如果虚拟内存区域（VMA）指示要使用巨页，则这些巨页会在页面错误时实例化到任务的地址空间中。如果在页面错误时没有巨页存在，任务会收到SIGBUS信号并通常会异常终止。巨页支持添加不久后，人们发现最好在mmap()时检测巨页不足的情况。其想法是：如果没有足够的巨页来覆盖映射，那么mmap()将会失败。这最初是通过在mmap()时进行简单的检查来实现的，以确定是否有足够的空闲巨页来覆盖映射。像内核中的大多数代码一样，这部分代码随着时间的推移不断进化。然而，基本的想法是在mmap()时“预留”巨页，以确保该映射中的页面错误时有足够的巨页可用。下面的描述试图说明在v4.10内核中如何处理巨页预留。

#### 受众
此描述主要针对修改hugetlbfs代码的内核开发者。

### 数据结构

#### resv_huge_pages
这是全局（每个hstate）的已预留巨页计数。已预留的巨页仅对预留它们的任务可用。因此，通常可用的巨页数量计算为（`free_huge_pages - resv_huge_pages`）。

#### 预留映射
预留映射由以下结构描述：

```c
struct resv_map {
    struct kref refs;
    spinlock_t lock;
    struct list_head regions;
    long adds_in_progress;
    struct list_head region_cache;
    long region_cache_count;
};
```

系统中的每个巨页映射都有一个预留映射。
`resv_map`内的`regions`列表描述了映射内的区域。一个区域由以下结构描述：

```c
struct file_region {
    struct list_head link;
    long from;
    long to;
};
```

`file_region`结构中的`from`和`to`字段是映射中的巨页索引。根据映射类型的不同，`reserv_map`中的一个区域可能表示该范围内存在预留，或不存在预留。

#### MAP_PRIVATE 预留标志
这些标志存储在预留映射指针的最低位上：
```
#define HPAGE_RESV_OWNER    (1UL << 0)
```
表示此任务拥有与映射相关的预留。
```
#define HPAGE_RESV_UNMAPPED (1UL << 1)
```
表示原始映射此范围（并创建预留）的任务（父任务）由于复制失败而从当前任务（子任务）中取消映射了一个页面。

#### 页面标志
`PagePrivate`页面标志用于指示当巨页被释放时必须恢复巨页预留。更多细节将在“释放巨页”部分讨论。
预订映射位置（私有或共享）
============================================

一个巨大的页面映射或段落要么是私有的，要么是共享的。如果是私有的，则通常仅对单个地址空间（任务）可用。如果是共享的，则可以映射到多个地址空间（任务）。对于这两种类型的映射而言，预订映射的位置和语义差异显著。位置上的差异如下：

- 对于私有映射，预订映射挂载在VMA结构上。具体来说，位于`vma->vm_private_data`。这个预订映射是在创建映射（mmap(MAP_PRIVATE)）时创建的。
- 对于共享映射，预订映射挂载在inode上。具体来说，在`inode->i_mapping->private_data`。由于共享映射总是由hugetlbfs文件系统中的文件支持，因此hugetlbfs代码确保每个inode都包含一个预订映射。因此，当inode被创建时，预订映射也被分配。

创建预订
=====================
当创建由大页支持的共享内存段（shmget(SHM_HUGETLB)）或通过mmap(MAP_HUGETLB)创建映射时，会创建预订。这些操作最终导致调用`hugetlb_reserve_pages()`函数：

```c
int hugetlb_reserve_pages(struct inode *inode,
                          long from, long to,
                          struct vm_area_struct *vma,
                          vm_flags_t vm_flags)
```

`hugetlb_reserve_pages()`首先检查是否在shmget()或mmap()调用中指定了NORESERVE标志。如果指定了NORESERVE，则此例程会立即返回，因为不需要任何预订。
参数'from'和'to'是映射或底层文件中的大页索引。对于shmget()，'from'始终为0，而'to'对应于段/映射的长度。对于mmap()，可以通过offset参数来指定进入底层文件的偏移量。在这种情况下，'from'和'to'参数已根据此偏移量进行了调整。
私有映射和共享映射之间的一个主要区别在于预订映射中表示预订的方式：
- 对于共享映射，预订映射中的条目表示存在或曾经存在相应的页面预订。随着预订被消耗，预订映射不会被修改。
- 对于私有映射，预订映射中没有条目表示存在相应的页面预订。随着预订被消耗，条目会被添加到预订映射中。因此，预订映射也可以用来确定哪些预订已经被消耗。
对于私有映射，`hugetlb_reserve_pages()`创建预订映射并将其挂载在VMA结构上。此外，设置HPAGE_RESV_OWNER标志以指示该VMA拥有这些预订。
### 预留图的查询

预留图用于确定当前映射/段需要多少个大页预留。对于私有映射，这个值始终是从`to - from`。然而，对于共享映射，可能存在某些预留已经在`to - from`范围内。关于如何实现这一点，请参阅章节 :ref:`预留图修改 <resv_map_modifications>`。

映射可能与一个子池关联。如果是这样，则会查询子池以确保有足够的空间用于映射。有可能子池已经预留了一些可以用于映射的空间。更多详细信息，请参阅章节 :ref:`子池预留 <sub_pool_resv>`。

在查询了预留图和子池之后，所需的新预留数量已知。此时调用`hugetlb_acct_memory()`函数来检查并获取请求的数量。`hugetlb_acct_memory()`会调用一些可能分配和调整多余页面计数的函数。然而，在这些函数中，代码仅仅是检查是否有足够的空闲大页来满足预留需求。如果有，则全局预留计数`resv_huge_pages`会被调整，类似于以下操作：

```c
if (resv_needed <= (resv_huge_pages - free_huge_pages))
    resv_huge_pages += resv_needed;
```

请注意，当检查和调整这些计数器时，持有全局锁`hugetlb_lock`。

如果有足够的空闲大页，并且全局计数`resv_huge_pages`被调整，则与映射相关的预留图将被修改以反映这些预留。在共享映射的情况下，将存在一个包含范围`from - to`的`file_region`。对于私有映射，不会对预留图进行任何修改，因为没有条目即表示存在预留。

如果`hugetlb_reserve_pages()`成功，则全局预留计数和与映射相关的预留图将根据需要进行修改，以确保在范围`from - to`内存在预留。

.. _consume_resv:

### 消耗预留/分配大页

当与预留相关的大页被分配并在相应映射中实例化时，预留将被消耗。分配在`alloc_hugetlb_folio()`函数中执行：

```c
struct folio *alloc_hugetlb_folio(struct vm_area_struct *vma,
                                  unsigned long addr, int avoid_reserve)
```

`alloc_hugetlb_folio`接收一个VMA指针和一个虚拟地址，因此它可以查询预留图来确定是否存在预留。此外，`alloc_hugetlb_folio`接受参数`avoid_reserve`，该参数指示即使看起来预留已被设置，也不应使用预留。`avoid_reserve`参数通常在写时复制（Copy on Write）和页面迁移（Page Migration）中使用，其中正在为现有页面分配额外的副本。

辅助函数`vma_needs_reservation()`被调用来确定在映射(vma)中是否存在预留。有关此函数的详细信息，请参阅章节 :ref:`预留图辅助函数 <resv_map_helpers>`。

从`vma_needs_reservation()`返回的值通常是0或1。0表示存在预留，1表示不存在预留。

如果不存在预留，并且映射关联了一个子池，则会查询子池以确定它是否包含预留。
如果子池中包含预留空间，则其中一个可以用于此次分配。然而，在所有情况下，avoid_reserve 参数会覆盖使用预留空间进行分配的行为。在确定是否存在可用于分配的预留空间之后，将调用函数 dequeue_huge_page_vma()。此函数接受两个与预留空间相关的参数：

- avoid_reserve，这是传递给 alloc_hugetlb_folio() 的相同值/参数。
- chg，尽管此参数类型为 long，但仅传递 0 或 1 这两个值到 dequeue_huge_page_vma()。如果值为 0，则表示存在一个预留空间（参见“内存策略和预留”部分可能存在的问题）。如果值为 1，则表示不存在预留空间，页面必须从全局空闲池中获取（如果可能的话）。

根据 VMA 的内存策略，搜索相关的空闲列表以查找空闲页面。如果找到一个页面，则在该页面从空闲列表中移除时，free_huge_pages 值会递减。如果页面关联了一个预留空间，则进行以下调整：

```SetPagePrivate(page); /* 表示分配此页面消耗了预留空间，并且如果遇到错误需要释放页面，则恢复预留空间。 */resv_huge_pages--; /* 递减全局预留计数 */```

请注意，如果没有满足 VMA 内存策略的巨页，则尝试使用伙伴分配器分配一个。这涉及到剩余巨页和超额分配的问题，这些问题超出了预留范围。即使分配了一个剩余页面，也会进行相同的基于预留的调整：SetPagePrivate(page) 和 resv_huge_pages--。

在获得新的 hugetlb folio 后，(folio)->_hugetlb_subpool 被设置为页面关联的子池值（如果存在）。当 folio 被释放时，这将用于子池会计处理。

然后调用 vma_commit_reservation() 来根据预留空间的消耗调整预留映射。通常，这涉及确保页面在区域映射的 file_region 结构中得到表示。对于存在预留空间的共享映射，预留映射中已经存在一个条目，因此无需更改。但是，如果共享映射中没有预留空间或这是一个私有映射，则必须创建一个新的条目。

在 alloc_hugetlb_folio() 开始处调用 vma_needs_reservation() 与分配 folio 后调用 vma_commit_reservation() 之间，预留映射可能会发生改变。如果对同一页面在共享映射中调用了 hugetlb_reserve_pages，则预留计数和子池空闲页面计数将相差一个。这种罕见情况可以通过比较 vma_needs_reservation 和 vma_commit_reservation 的返回值来识别。如果检测到这种竞争条件，则调整子池和全局预留计数以进行补偿。有关这些函数的更多信息，请参阅
:ref:`<resv_map_helpers>` 部分。

实例化巨页
===========

巨页分配后，通常会将页面添加到分配任务的页表中。在此之前，共享映射中的页面会被添加到页缓存中，而私有映射中的页面会被添加到匿名反向映射中。在这两种情况下，都会清除 PagePrivate 标志。因此，当实例化的巨页被释放时，不会调整全局预留计数（resv_huge_pages）。

释放巨页
=========

巨页由 free_huge_folio() 释放。它只接收一个指向 folio 的指针，因为它是从通用内存管理代码中调用的。当巨页被释放时，可能需要进行预留会计处理。如果页面与包含预留空间的子池关联，或者页面是在错误路径上被释放并且需要恢复全局预留计数，就会是这种情况。

page->private 字段指向与页面关联的任何子池。
如果设置了 `PagePrivate` 标志，则表示全局预留计数需要调整（参见 :ref:` Consuming Reservations/Allocating a Huge Page <consume_resv>` 部分以了解这些计数是如何设置的）。该例程首先调用 `hugepage_subpool_put_pages()` 来处理页面。如果此例程返回值为 0（这不等于传递的值 1），则表示子池关联有预留，这个新释放的页面必须用于保持子池预留数量高于最小值。因此，在这种情况下会递增全局 `resv_huge_pages` 计数器。如果页面中设置了 `PagePrivate` 标志，全局 `resv_huge_pages` 计数器始终会递增。

.. _sub_pool_resv:

子池预留
====================

每个大页大小都关联有一个 `struct hstate`。`hstate` 跟踪指定大小的所有大页。子池表示 `hstate` 中与挂载的 `hugetlbfs` 文件系统相关联的一组页面的子集。
当挂载 `hugetlbfs` 文件系统时，可以指定一个 `min_size` 选项，表示文件系统所需的最小大页数量。如果指定了此选项，则相应数量的大页将被预留供文件系统使用。这个数量存储在 `struct hugepage_subpool` 的 `min_hpages` 字段中。在挂载时，会调用 `hugetlb_acct_memory(min_hpages)` 来预留指定数量的大页。如果无法预留这些大页，挂载将会失败。
当从子池获取或释放页面时，会调用 `hugepage_subpool_get/put_pages()` 函数。它们执行所有子池的会计操作，并跟踪任何与子池相关的预留。`hugepage_subpool_get/put_pages` 函数接收需要调整子池“已使用页面”计数的大页数量（获取时减少，释放时增加）。通常，它们会返回传递的相同值或如果子池中没有足够的页面则返回错误。
然而，如果子池关联有预留，则可能会返回一个小于传递值的返回值。这个返回值表示需要进行的额外全局池调整的数量。例如，假设一个子池中有 3 个预留的大页，而有人请求 5 个大页。
与子池相关的3个预留页面可以用来满足请求的一部分。但是，必须从全局池中获取另外2个页面。为了将此信息传达给调用者，返回值为2。然后，调用者负责尝试从全局池中获取额外的两个页面。

COW 和 预留
===========

由于共享映射都指向并使用相同的底层页面，COW 的最大预留关注点是私有映射。在这种情况下，两个任务可能指向同一个先前分配的页面。其中一个任务试图写入该页面，因此需要分配一个新的页面，以便每个任务指向各自的页面。

当页面最初被分配时，其预留已经被消耗。当因为 COW 而尝试分配新页面时，可能会没有可用的巨大页面，从而导致分配失败。

当私有映射最初创建时，通过在所有者预留映射指针中的HPAGE_RESV_OWNER位来标记映射的所有者。由于所有者创建了映射，因此所有者拥有与映射相关的所有预留。因此，在发生写入错误且没有页面可用时，对所有者和非所有者的处理会有所不同。

如果故障任务不是所有者，则故障会失败，并且任务通常会收到 SIGBUS 信号。

如果所有者是故障任务，我们希望它成功，因为它拥有原始预留。为此，将页面从非所有者的任务中解除映射。这样，唯一的引用来自所有者的任务。

此外，还会在非所有者任务的预留映射指针中设置 HPAGE_RESV_UNMAPPED 位。如果非所有者任务稍后在一个不在场的页面上发生故障，它可能会收到 SIGBUS 信号。但是，映射/预留的原始所有者将按预期行为运行。

.. _resv_map_modifications:

预留映射修改
============================

以下低级例程用于修改预留映射。通常，这些例程不会直接被调用，而是调用一个预留映射辅助例程，该例程再调用这些低级例程之一。这些低级例程在源代码（mm/hugetlb.c）中有较好的文档说明。这些例程包括：

-  long region_chg(struct resv_map *resv, long f, long t);
-  long region_add(struct resv_map *resv, long f, long t);
-  void region_abort(struct resv_map *resv, long f, long t);
-  long region_count(struct resv_map *resv, long f, long t);

对预留映射的操作通常涉及两个步骤：

1) 调用 region_chg() 来检查预留映射，并确定指定范围 [f, t) 内有多少页面当前未被表示。
   调用代码执行全局检查和分配以确定是否有足够的巨大页面使操作成功。
2) 
  a) 如果操作可以成功，调用 region_add() 实际修改预留映射，对于之前传递给 region_chg() 的相同范围 [f, t) 进行修改。
b) 如果操作无法成功，则对相同的范围 [f, t) 调用 region_abort 来中止该操作。
请注意，这是一个两步过程，其中 region_add() 和 region_abort() 在先前调用 region_chg() 之后保证会成功。region_chg() 负责预先分配任何必要的数据结构以确保后续操作（特别是 region_add()）能够成功。
如上所述，region_chg() 确定范围内当前未在映射中表示的页数。此数字将返回给调用者。region_add() 返回添加到映射中的页数。在大多数情况下，region_add() 的返回值与 region_chg() 的返回值相同。然而，在共享映射的情况下，在调用 region_chg() 和 region_add() 之间可能会对预留映射进行更改。在这种情况下，region_add() 的返回值将不匹配 region_chg() 的返回值。在这种情况下，全局计数和子池会计信息可能是不正确的，并需要调整。调用者的责任是检查这种情况并进行适当的调整。
通常调用 region_del() 来从预留映射中删除区域。它通常在以下情况下调用：

- 当 hugetlbfs 文件系统中的文件被删除时，inode 将被释放并且预留映射将被释放。在释放预留映射之前，必须释放所有单个的 file_region 结构。在这种情况下，region_del 被传递范围 [0, LONG_MAX)。
- 当 hugetlbfs 文件被截断时。在这种情况下，新文件大小之后的所有已分配页必须被释放。此外，预留映射中超过新文件末尾的所有 file_region 条目必须被删除。在这种情况下，region_del 被传递范围 [new_end_of_file, LONG_MAX)。
- 当在 hugetlbfs 文件中打孔时。在这种情况下，从文件中间逐个移除大页。随着这些页面被移除，调用 region_del() 以从预留映射中移除相应的条目。在这种情况下，region_del 被传递范围 [page_idx, page_idx + 1)。

在每种情况下，region_del() 都会返回从预留映射中移除的页数。在极少数情况下，region_del() 可能会失败。这只能发生在打孔的情况下，它必须拆分现有的 file_region 条目但无法分配新的结构。在这种错误情况下，region_del() 将返回 -ENOMEM。问题在于预留映射将指示存在对该页的预留，但是子池和全局预留计数不会反映该预留。为了解决这种情况，调用 hugetlb_fix_reserve_counts() 函数来调整计数器，使其与无法删除的预留映射条目对应。
当取消映射私有大页映射时调用 region_count()。在私有映射中，预留映射中没有条目表示存在一个预留。因此，通过计算预留映射中的条目数量，我们知道消耗了多少预留以及有多少未处理的预留（未处理的 = (end - start) - region_count(resv, start, end)）。由于映射将消失，因此子池和全局预留计数将根据未处理的预留数量减少。
.. _resv_map_helpers:

预留映射辅助函数
===============================

存在多个辅助函数用于查询和修改预留映射。这些函数仅关注特定大页的预留，因此只需传递地址而不是范围。此外，它们还会传递相关的VMA（虚拟内存区域）。从VMA中可以确定映射类型（私有或共享）以及预留映射的位置（inode 或 VMA）。这些函数简单地调用“预留映射修改”部分中描述的基本函数。然而，它们确实考虑了私有和共享映射对于预留映射条目的‘相反’含义，并向调用者隐藏了这一细节：

    long vma_needs_reservation(struct hstate *h,
                               struct vm_area_struct *vma,
                               unsigned long addr)

此函数为指定页面调用region_chg()。如果不存在预留，则返回1；如果存在预留，则返回0。

    long vma_commit_reservation(struct hstate *h,
                                struct vm_area_struct *vma,
                                unsigned long addr)

此函数为指定页面调用region_add()。如同region_chg和region_add的情况一样，此函数应在调用vma_needs_reservation之后调用。它将为页面添加一个预留条目。如果成功添加预留则返回1，否则返回0。应将返回值与前一次调用vma_needs_reservation的返回值进行比较。意外的差异表明在两次调用之间预留映射被修改了。

    void vma_end_reservation(struct hstate *h,
                             struct vm_area_struct *vma,
                             unsigned long addr)

此函数为指定页面调用region_abort()。如同region_chg和region_abort的情况一样，此函数应在调用vma_needs_reservation之后调用。它将终止正在进行的预留添加操作。

    long vma_add_reservation(struct hstate *h,
                             struct vm_area_struct *vma,
                             unsigned long addr)

这是一个特殊的包装函数，用于帮助错误路径中的预留清理工作。它只在restore_reserve_on_error()函数中被调用。此函数与vma_needs_reservation结合使用，试图向预留映射中添加一个预留。它考虑了私有和共享映射的不同预留映射语义。因此，对于共享映射会调用region_add（因为映射中存在的条目表示有预留），而对于私有映射会调用region_del（因为映射中不存在条目表示有预留）。有关错误路径中需要执行的操作，请参阅“错误路径中的预留清理”部分。

错误路径中的预留清理
==================================

如“预留映射辅助函数”部分所述，预留映射的修改分为两步。首先，在分配页面之前调用vma_needs_reservation。如果分配成功，则调用vma_commit_reservation。如果不成功，则调用vma_end_reservation。根据操作的成功或失败调整全局和子池的预留计数，一切顺利。

此外，在实例化大页之后会清除PagePrivate标志，以便最终释放页面时正确计算。然而，在分配大页后但在实例化之前遇到错误的情况并不少见。在这种情况下，页面分配已经消耗了预留，并对相应的子池、预留映射和全局计数进行了调整。如果此时释放页面（在实例化和清除PagePrivate标志之前），则free_huge_folio会增加全局预留计数。但是，预留映射显示该预留已被消耗。这种不一致的状态会导致预留的大页‘泄漏’。全局预留计数将高于应有的数值，并阻止预分配页面的分配。

restore_reserve_on_error()函数尝试处理这种情况。该函数文档较为完善。其意图是将预留映射恢复到页面分配之前的状况。这样，在页面被释放后，预留映射的状态将与全局预留计数相符。

restore_reserve_on_error本身在尝试恢复预留映射条目时可能会遇到错误。在这种情况下，它将简单地清除页面的PagePrivate标志。这样，在页面被释放时不会增加全局预留计数。然而，预留映射将继续显示该预留已被消耗。

仍然可以为该地址分配页面，但不会使用原本预期的预留页面。
有一些代码（最显著的是userfaultfd）无法调用 `restore_reserve_on_error`。在这种情况下，它只是修改了 `PagePrivate`，以便在释放大页时不会泄露预留空间。
预留和内存策略
==============================
当 Git 首次用于管理 Linux 代码时，每个节点的大页列表存在于 `struct hstate` 中。预留的概念是在稍后添加的。

当预留被添加时，并未考虑内存策略。尽管 cpusets 并不完全等同于内存策略，但以下评论总结了预留与 cpusets/内存策略之间的交互关系：

```
/*
 * 当配置了 cpuset 时，它会破坏严格的大页预留机制，因为会计操作是基于全局变量进行的。在存在 cpuset 的情况下，这种预留完全没有意义，因为预留没有检查当前 cpuset 中的页面可用性。应用程序仍然可能因为所在 cpuset 中缺乏空闲的大页而被内核触发 OOM。
* 尝试在 cpuset 下强制执行严格的会计操作几乎是不可能的（或太过复杂），因为 cpuset 太过动态，任务或内存节点可以在 cpuset 之间动态移动。
*
 * 共享大页映射在 cpuset 环境中的语义变化是不可取的。然而，为了保留部分语义，我们退而求其次，检查当前可用的空闲页面作为最佳尝试，并希望尽量减少 cpuset 带来的语义变化的影响。
*/
```

大页预留是为了防止在页面错误时发生意外的页面分配失败（OOM）。然而，如果应用程序使用了 cpusets 或内存策略，则无法保证所需节点上有足够的大页可用。即使有足够的全局预留也是如此。
大页文件系统回归测试
============================

最完整的一组大页测试位于 libhugetlbfs 仓库中。
如果你修改了任何与大页相关的代码，请使用 libhugetlbfs 测试套件来检查回归问题。此外，如果你添加了任何新的大页功能，请向 libhugetlbfs 添加相应的测试。

-- Mike Kravetz, 2017年4月7日
