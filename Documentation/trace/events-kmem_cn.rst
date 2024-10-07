子系统跟踪点：kmem
============================

kmem跟踪系统捕获内核中与对象和页面分配相关的事件。大致来说，有五个主要的子标题：
- 小未知类型对象的slab分配（kmalloc）
- 小已知类型对象的slab分配
- 页面分配
- 每CPU分配器活动
- 外部碎片

本文档描述了每个跟踪点及其可能的用途。

1. 小未知类型对象的slab分配
===================================================
::

  kmalloc		call_site=%lx ptr=%p bytes_req=%zu bytes_alloc=%zu gfp_flags=%s
  kmalloc_node	call_site=%lx ptr=%p bytes_req=%zu bytes_alloc=%zu gfp_flags=%s node=%d
  kfree		call_site=%lx ptr=%p

这些事件的高频率活动可能表明特定缓存是有必要的，特别是在kmalloc slab页面因分配模式而产生大量内部碎片的情况下。通过关联kmalloc和kfree，可以识别内存泄漏及其分配位置。

2. 小已知类型对象的slab分配
=================================================
::

  kmem_cache_alloc	call_site=%lx ptr=%p bytes_req=%zu bytes_alloc=%zu gfp_flags=%s
  kmem_cache_alloc_node	call_site=%lx ptr=%p bytes_req=%zu bytes_alloc=%zu gfp_flags=%s node=%d
  kmem_cache_free		call_site=%lx ptr=%p

这些事件的使用类似于与kmalloc相关的事件，但更有可能将事件定位到特定的缓存。在撰写本文时，尚无法获取正在分配的slab信息，但可以通过调用位置（call_site）推断出该信息。

3. 页面分配
==================
::

  mm_page_alloc		  page=%p pfn=%lu order=%d migratetype=%d gfp_flags=%s
  mm_page_alloc_zone_locked page=%p pfn=%lu order=%u migratetype=%d cpu=%d percpu_refill=%d
  mm_page_free		  page=%p pfn=%lu order=%d
  mm_page_free_batched	  page=%p pfn=%lu order=%d cold=%d

这四个事件处理页面分配和释放。mm_page_alloc是页面分配器活动的一个简单指标。页面可以从每CPU分配器（高性能）或伙伴分配器分配。
如果页面直接从伙伴分配器分配，则触发mm_page_alloc_zone_locked事件。此事件很重要，因为大量的活动意味着zone->lock上的高活动度。获取这个锁会通过禁用中断、弄脏CPU之间的缓存行以及串行化许多CPU来影响性能。
当页面由调用者直接释放时，仅触发mm_page_free事件。此处大量的活动可能表明调用者应将其活动批处理。
当页面以批处理方式释放时，也触发mm_page_free_batched事件。一般来说，批量从LRU锁上取下页面，并使用页面列表批量释放。此处大量的活动可能表明系统面临内存压力，并且也可能表明lruvec->lru_lock上的争用。

4. 每CPU分配器活动
=============================
::

  mm_page_alloc_zone_locked	page=%p pfn=%lu order=%u migratetype=%d cpu=%d percpu_refill=%d
  mm_page_pcpu_drain		page=%p pfn=%lu order=%d cpu=%d migratetype=%d

页面分配器前面有一个每CPU页面分配器。它只用于order-0页面，减少了zone->lock上的争用，并减少了对struct page的写入操作。
当每个CPU的列表为空或分配了错误类型的页面时，`zone->lock`将被获取一次，并重新填充每个CPU的列表。触发的事件是`mm_page_alloc_zone_locked`，对于每次分配的页面都会触发该事件，并且事件会表明是否是为了`percpu_refill`。

当每个CPU的列表过于满时，会释放一些页面，每释放一个页面都会触发一个`mm_page_pcpu_drain`事件。
这些事件的独立性使得可以在分配和释放之间追踪页面。连续发生的多个排空或填充事件意味着`zone->lock`被获取了一次。大量的每个CPU的填充和排空事件可能表明CPU之间存在不平衡，过多的工作集中在某一处。这也可能表明每个CPU的列表应该具有更大的大小。最后，一个CPU上的大量填充和另一个CPU上的大量排空可能是由于CPU之间的写操作导致大量缓存行反弹的原因，值得通过某种算法改变来调查是否可以在同一CPU上分配和释放页面。

5. 外部碎片化
==============

```
mm_page_alloc_extfrag	page=%p pfn=%lu alloc_order=%d fallback_order=%d pageblock_order=%d alloc_migratetype=%d fallback_migratetype=%d fragmenting=%d change_ownership=%d
```

外部碎片化会影响高阶分配是否成功。对于某些类型的硬件，这很重要，尽管在可能的情况下会避免这种情况。如果系统使用了大页面并且需要能够在系统生命周期中调整池的大小，那么这个值就很重要。

大量此类事件的发生表明内存正在碎片化，并且高阶分配将在未来的某个时刻开始失败。减少此类事件发生的一种方法是增加`min_free_kbytes`的大小，增量为`3 * pageblock_size * nr_online_nodes`，其中`pageblock_size`通常是默认的大页面大小。
