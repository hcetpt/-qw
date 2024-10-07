=======================
内核同页合并（Kernel Samepage Merging）
=======================

KSM 是一种节省内存的去重功能，通过 CONFIG_KSM=y 启用，并在 Linux 内核 2.6.32 中添加。其实现见 `mm/ksm.c`，更多详细信息参见 [lwn.net/Articles/306704/](http://lwn.net/Articles/306704/) 和 [lwn.net/Articles/330589/](https://lwn.net/Articles/330589/)

KSM 的用户空间接口描述见 `Documentation/admin-guide/mm/ksm.rst`

设计
======

概述
--------

.. kernel-doc:: mm/ksm.c
   :DOC: 概述

逆向映射
-------
KSM 在稳定树中维护 KSM 页面的逆向映射信息。
如果一个 KSM 页面被少于 `max_page_sharing` 个 VMA 共享，则该稳定树节点指向一个 `struct ksm_rmap_item` 列表，并且 KSM 页面的 `page->mapping` 指向该稳定树节点。
当共享超过这个阈值时，KSM 会在稳定树中增加一个维度。树节点变成一条“链”，链接一个或多个“副本”。每个“副本”保存一个 KSM 页面的逆向映射信息，并且 `page->mapping` 指向那个“副本”。
每条“链”和所有链接到“链”的“副本”都强制保持不变性，即它们表示相同的内容，即使每个“副本”将由不同的 KSM 页面拷贝指向该内容。
这样，与无限逆向映射列表相比，稳定树查找的计算复杂度不会受到影响。仍然强制要求稳定树本身不能有 KSM 页面内容的重复。
`max_page_sharing` 强制的去重限制是为了避免虚拟内存的 rmap 列表变得过大。rmap 遍历具有 O(N) 复杂度，其中 N 是共享页面的 rmap_items（即虚拟映射）的数量，这反过来又被 `max_page_sharing` 限制。因此，这有效地将线性的 O(N) 计算复杂度从 rmap 遍历上下文分散到不同的 KSM 页面上。ksmd 对稳定节点“链”的遍历也是 O(N)，但 N 是稳定节点“副本”的数量，而不是 rmap_items 的数量，因此对 ksmd 性能没有显著影响。实际上，最佳的稳定节点“副本”候选将在“副本”列表的头部被保留并找到。
`max_page_sharing` 的高值会导致更快的内存合并（因为会有更少的稳定节点副本排队在稳定节点链->hlist 中进行剪枝检查），并以更高的去重率为代价，但会导致最坏情况下的 rmap 遍历变慢，这可能发生在交换、压缩、NUMA 平衡和页面迁移期间。
`stable_node_dups/stable_node_chains` 的比例也受 `max_page_sharing` 可调参数的影响，高比例可能表明稳定节点副本中的碎片化问题，可以通过引入 ksmd 中的碎片化算法来解决，这些算法会重新分配 rmap_items 从一个稳定节点副本到另一个稳定节点副本，以便释放带有少量 rmap_items 的稳定节点“副本”，但这可能会增加 ksmd 的 CPU 使用率，并可能减慢应用程序对 KSM 页面的只读计算。
整个稳定节点“链”中的稳定节点“副本”列表会定期扫描以剪枝过时的稳定节点。
此类扫描的频率由 `stable_node_chains_prune_millisecs` sysfs 可调参数定义。
参考
---------
.. kernel-doc:: mm/ksm.c
   :functions: mm_slot ksm_scan stable_node rmap_item

--
Izik Eidus,
Hugh Dickins, 2009年11月17日
