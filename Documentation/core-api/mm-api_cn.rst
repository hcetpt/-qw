内存管理APIs
======================

用户空间内存访问
========================

.. kernel-doc:: arch/x86/include/asm/uaccess.h
   :internal:

.. kernel-doc:: arch/x86/lib/usercopy_32.c
   :export:

.. kernel-doc:: mm/gup.c
   :functions: get_user_pages_fast

.. _mm-api-gfp-flags:

内存分配控制
==========================

.. kernel-doc:: include/linux/gfp_types.h
   :doc: 页面流动性和放置提示

.. kernel-doc:: include/linux/gfp_types.h
   :doc: 水位线修饰符

.. kernel-doc:: include/linux/gfp_types.h
   :doc: 回收修饰符

.. kernel-doc:: include/linux/gfp_types.h
   :doc: 有用的GFP标志组合

Slab缓存
==============

.. kernel-doc:: include/linux/slab.h
   :internal:

.. kernel-doc:: mm/slub.c
   :export:

.. kernel-doc:: mm/slab_common.c
   :export:

.. kernel-doc:: mm/util.c
   :functions: kfree_const kvmalloc_node kvfree

虚拟连续映射
=============================

.. kernel-doc:: mm/vmalloc.c
   :export:

文件映射和页面缓存
===========================

文件映射
-------

.. kernel-doc:: mm/filemap.c
   :export:

预读取
---------

.. kernel-doc:: mm/readahead.c
   :doc: 预读取概述

.. kernel-doc:: mm/readahead.c
   :export:

写回
---------

.. kernel-doc:: mm/page-writeback.c
   :export:

截断
--------

.. kernel-doc:: mm/truncate.c
   :export:

.. kernel-doc:: include/linux/pagemap.h
   :internal:

内存池
============

.. kernel-doc:: mm/mempool.c
   :export:

DMA池
=========

.. kernel-doc:: mm/dmapool.c
   :export:

更多内存管理函数
=================================

.. kernel-doc:: mm/memory.c
   :export:

.. kernel-doc:: mm/page_alloc.c
.. kernel-doc:: mm/mempolicy.c
.. kernel-doc:: include/linux/mm_types.h
   :internal:
.. kernel-doc:: include/linux/mm_inline.h
.. kernel-doc:: include/linux/page-flags.h
.. kernel-doc:: include/linux/mm.h
   :internal:
.. kernel-doc:: include/linux/page_ref.h
.. kernel-doc:: include/linux/mmzone.h
.. kernel-doc:: mm/util.c
   :functions: folio_mapping

.. kernel-doc:: mm/rmap.c
.. kernel-doc:: mm/migrate.c
.. kernel-doc:: mm/mmap.c
.. kernel-doc:: mm/kmemleak.c
.. kernel-doc:: mm/memremap.c
.. kernel-doc:: mm/hugetlb.c
.. kernel-doc:: mm/swap.c
.. kernel-doc:: mm/zpool.c
.. kernel-doc:: mm/memcontrol.c
.. #kernel-doc:: mm/memory-tiers.c (编译警告)
.. kernel-doc:: mm/shmem.c
.. kernel-doc:: mm/migrate_device.c
.. #kernel-doc:: mm/nommu.c (其他文件中重复的kernel-doc)
.. kernel-doc:: mm/mapping_dirty_helpers.c
.. #kernel-doc:: mm/memory-failure.c (编译警告)
.. kernel-doc:: mm/percpu.c
.. kernel-doc:: mm/maccess.c
.. kernel-doc:: mm/vmscan.c
.. kernel-doc:: mm/memory_hotplug.c
.. kernel-doc:: mm/mmu_notifier.c
.. kernel-doc:: mm/balloon_compaction.c
.. kernel-doc:: mm/huge_memory.c
.. kernel-doc:: mm/io-mapping.c
