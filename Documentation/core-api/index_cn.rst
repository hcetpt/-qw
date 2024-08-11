核心API文档
======================

这是核心内核API手册的开端。对于此手册文档的转换（及编写！）工作我们深表感谢！

核心工具
==============

本节包含通用和“核心中的核心”文档。首先是大量从docbook时期遗留下来的kerneldoc信息的大杂烩；将来某天如果有人愿意投入精力，应该将其拆分。
.. toctree::
   :maxdepth: 1

   kernel-api
   workqueue
   watch_queue
   printk-basics
   printk-formats
   printk-index
   symbol-namespaces
   asm-annotations

数据结构与低级工具
=======================================

在整个内核中被广泛使用的库功能
.. toctree::
   :maxdepth: 1

   kobject
   kref
   assoc_array
   xarray
   maple_tree
   idr
   circular-buffers
   rbtree
   generic-radix-tree
   packing
   this_cpu_ops
   timekeeping
   errseq
   wrappers/atomic_t
   wrappers/atomic_bitops
   floating-point

低级入口与出口
========================

.. toctree::
   :maxdepth: 1

   entry

并发原语
======================

Linux如何防止一切同时发生。请参阅Documentation/locking/index.rst以获取更多相关文档
.. toctree::
   :maxdepth: 1

   refcount-vs-atomic
   irq/index
   local_ops
   padata
   ../RCU/index
   wrappers/memory-barriers.rst

低级硬件管理
=============================

缓存管理、管理CPU热插拔等
.. toctree::
   :maxdepth: 1

   cachetlb
   cpu_hotplug
   memory-hotplug
   genericirq
   protection-keys

内存管理
=================

如何在内核中分配和使用内存。请注意，关于内存管理的更多文档可以在Documentation/mm/index.rst中找到
.. toctree::
   :maxdepth: 1

   memory-allocation
   unaligned-memory-access
   dma-api
   dma-api-howto
   dma-attributes
   dma-isa-lpc
   swiotlb
   mm-api
   genalloc
   pin_user_pages
   boot-time-mm
   gfp_mask-from-fs-io

内核调试接口
===============================

.. toctree::
   :maxdepth: 1

   debug-objects
   tracepoint
   debugging-via-ohci1394

其他所有内容
===============

不符合其他分类或尚未归类的文档
.. toctree::
   :maxdepth: 1

   librs
   netlink

.. only:: subproject and html

   索引
   =======

   * :ref:`genindex`
