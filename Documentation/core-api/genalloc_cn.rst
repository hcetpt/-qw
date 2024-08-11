### genalloc/genpool 子系统
==============================

内核中有多个内存分配子系统，每个子系统都针对特定的需求。然而，有时候内核开发者需要为某一特定范围的专用内存实现一个新的分配器；通常这类内存位于某个设备上。该设备驱动程序的作者当然可以编写一个小分配器来完成任务，但这会导致内核中充斥着大量未经充分测试的分配器。早在2005年，Jes Sorensen从sym53c8xx_2驱动程序中提取了一个这样的分配器，并将其作为一个通用模块发布_，用于创建即兴的内存分配器。这段代码在2.6.13版本中被合并；自那以后，它已经经过了相当大的修改。
.. _发布: https://lwn.net/Articles/125842/

使用此分配器的代码应该包含 `<linux/genalloc.h>`。行动始于使用以下之一创建一个池：

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_create		 

.. kernel-doc:: lib/genalloc.c
   :functions: devm_gen_pool_create

调用 `gen_pool_create()` 将创建一个池。分配的粒度由 `min_alloc_order` 设置；它是一个以2为底的对数，类似于页分配器使用的数字，但它指的是字节而非页面。因此，如果 `min_alloc_order` 被设置为3，则所有分配都将是8字节的倍数。增加 `min_alloc_order` 可以减少跟踪池中内存所需的内存。参数 `nid` 指定了哪些NUMA节点将用于分配维护结构；如果调用者不关心这个值，它可以是-1。
“管理”接口 `devm_gen_pool_create()` 将池与特定设备绑定。除此之外，当给定的设备被销毁时，它会自动清理池。
关闭池的操作如下：

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_destroy

值得注意的是，如果从给定池中仍有未释放的分配，此函数将采取极端措施调用 `BUG()`，导致整个系统崩溃。您已得到警告。
新创建的池没有可分配的内存。在这种状态下它是相当无用的，因此通常首先要做的是向池添加内存。这可以通过以下之一完成：

.. kernel-doc:: include/linux/genalloc.h
   :functions: gen_pool_add

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_add_owner

调用 `gen_pool_add()` 将把起始于 `addr`（在内核虚拟地址空间中）的 `size` 字节的内存放入给定池中，再次使用 `nid` 作为辅助内存分配的节点ID。`gen_pool_add_virt()` 变体将一个显式的物理地址与内存关联起来；这仅在池将用于DMA分配时才需要。
从池中分配内存（和释放内存）的函数如下：

.. kernel-doc:: include/linux/genalloc.h
   :functions: gen_pool_alloc

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_dma_alloc

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_free_owner

如预期的那样，`gen_pool_alloc()` 会从给定池中分配 `size` 字节。`gen_pool_dma_alloc()` 变体为DMA操作分配内存，并将关联的物理地址返回到由 `dma` 指向的空间中。这只有在使用 `gen_pool_add_virt()` 添加内存时才能工作。请注意，此函数偏离了通常的genpool模式，即使用 `unsigned long` 值来表示内核地址；它返回一个 `void *`。
这一切看起来相对简单；事实上，一些开发者显然发现它太简单了。毕竟，上述接口没有提供控制分配函数如何选择要返回的具体内存段的方式。如果需要这种控制，以下函数可能会引起兴趣：

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_alloc_algo_owner

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_set_algo

使用 `gen_pool_alloc_algo()` 进行的分配指定了一个用于选择要分配的内存的算法；默认算法可以用 `gen_pool_set_algo()` 设置。`data` 值传递给算法；大多数算法忽略它，但偶尔也需要它。自然地，您可以编写一个特殊用途的算法，但也有一套现成可用的算法：

- `gen_pool_first_fit` 是一个简单的首次适应分配器；如果没有指定其他算法，这是默认算法
- `gen_pool_first_fit_align` 强制分配具有特定的对齐方式（通过 `data` 中的 `genpool_data_align` 结构传递）
- `gen_pool_first_fit_order_align` 根据大小的顺序对分配进行对齐。例如，一个 60 字节的分配将因此变为 64 字节对齐。
- `gen_pool_best_fit`，正如人们所期望的那样，是一个简单的最佳匹配分配器。
- `gen_pool_fixed_alloc` 在池内的特定偏移量处进行分配（通过数据参数中的 `genpool_data_fixed` 结构传递）。如果指定的内存不可用，则分配失败。
还有一些其他函数，主要用于查询池中的可用空间或遍历内存块等目的。然而，大多数用户应该不需要超出上面描述的功能。希望更多人了解这个模块能够有助于防止将来编写特殊用途的内存分配器。

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_virt_to_phys

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_for_each_chunk

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_has_addr

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_avail

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_size

.. kernel-doc:: lib/genalloc.c
   :functions: gen_pool_get

.. kernel-doc:: lib/genalloc.c
   :functions: of_gen_pool_get
