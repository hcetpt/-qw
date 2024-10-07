内存管理文档
===============================

本指南旨在帮助您理解 Linux 的内存管理系统。如果您只是想了解如何分配内存，请参阅 :ref:`memory_allocation`。如需了解控制和调优指南，请参阅 :doc:`管理员指南 <../admin-guide/mm/index>`。

.. toctree::
   :maxdepth: 1

   物理内存
   页表
   进程地址空间
   引导内存
   页分配
   vmalloc
   slab
   高内存
   页回收
   交换
   页缓存
   shmfs
   oom

未分类文档
======================

这些文档是关于 Linux 内存管理 (MM) 子系统内部细节的集合，内容包括从笔记到邮件列表回复的各种描述数据结构和算法的内容。所有这些都应该被整合进上述结构化的文档中，或者在完成其使命后删除。

.. toctree::
   :maxdepth: 1

   活动内存管理
   分配分析
   架构页表助手
   平衡
   damon/index
   免费页面报告
   hmm
   硬件损坏
   hugetlbfs 预留
   ksm
   内存模型
   mmu 通知器
   多代 LRU
   numa
   超量承诺会计
   页迁移
   页碎片
   页所有者
   页表检查
   重映射文件页
   slub
   分割页表锁
   跨巨大页
   不可驱逐 LRU
   vmalloc 内核栈
   vmemmap 去重
   z3fold
   zsmalloc
