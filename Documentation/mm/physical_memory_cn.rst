SPDX 许可证标识符: GPL-2.0

===============
物理内存
===============

Linux 可用于广泛的架构，因此需要一种与架构无关的抽象来表示物理内存。本章描述了用于管理运行系统中物理内存的数据结构。
在内存管理中的第一个主要概念是 `非统一内存访问 (NUMA) <https://en.wikipedia.org/wiki/Non-uniform_memory_access>`_。
在多核和多插槽机器中，内存可能会被划分为多个内存库，访问这些内存库的成本取决于它们与处理器的距离。例如，每个 CPU 可能会分配一个内存库，或者靠近外围设备的位置会有适合直接内存访问（DMA）的内存库。
每个这样的内存库被称为节点，在 Linux 中通过 `struct pglist_data` 结构来表示，即使是在统一内存访问（UMA）架构下也是如此。这个结构总是通过其类型定义 `pg_data_t` 来引用。对于特定节点的 `pg_data_t` 结构可以通过 `NODE_DATA(nid)` 宏来引用，其中 `nid` 是该节点的 ID。

对于 NUMA 架构，节点结构会在启动过程中由特定于架构的代码早期分配。通常，这些结构会被分配在它们所代表的内存库中。对于 UMA 架构，只有一个静态的 `pg_data_t` 结构，称为 `contig_page_data` 被使用。节点将在章节 :ref:`Nodes <nodes>` 中进一步讨论。

整个物理地址空间被划分为一个或多个称为区域的块，这些区域代表内存内的范围。这些范围通常是由访问物理内存的架构约束决定的。
节点内对应特定区域的内存范围由 `struct zone` 描述，并类型定义为 `zone_t`。每个区域都有以下类型之一：
* `ZONE_DMA` 和 `ZONE_DMA32` 历史性地表示外围设备可以直接访问的内存，这些设备无法访问所有可寻址内存。多年来已经有更好的、更健壮的接口来获取具有 DMA 特定要求的内存（参见 Documentation/core-api/dma-api.rst），但 `ZONE_DMA` 和 `ZONE_DMA32` 仍然表示那些访问受限的内存范围。
根据架构的不同，可以使用 `CONFIG_ZONE_DMA` 和 `CONFIG_ZONE_DMA32` 配置选项在构建时禁用这些区域类型中的任何一个，甚至两个都禁用。一些 64 位平台可能需要这两个区域，因为它们支持具有不同 DMA 寻址限制的外围设备。
* `ZONE_NORMAL` 用于内核始终可以访问的正常内存。如果 DMA 设备支持向所有可寻址内存进行传输，则可以在这个区域中的页面上执行 DMA 操作。`ZONE_NORMAL` 始终启用。
* `ZONE_HIGHMEM` 是物理内存中未被永久映射到内核页表的部分。这个区域中的内存只能通过临时映射被内核访问。这个区域仅在某些 32 位架构上可用，并且通过 `CONFIG_HIGHMEM` 启用。
``ZONE_MOVABLE`` 用于普通可访问内存，就像 ``ZONE_NORMAL`` 一样。
不同之处在于 ``ZONE_MOVABLE`` 中大多数页面的内容是可以移动的。这意味着这些页面的虚拟地址不会改变，但它们的内容可以在不同的物理页之间移动。通常在内存热插拔期间会填充 ``ZONE_MOVABLE``，但在启动时也可以使用 ``kernelcore``、``movablecore`` 和 ``movable_node`` 内核命令行参数之一来填充。详情请参阅 `Documentation/mm/page_migration.rst` 和 `Documentation/admin-guide/mm/memory-hotplug.rst`。

``ZONE_DEVICE`` 表示驻留在设备（如 PMEM 和 GPU）上的内存。它与 RAM 区域类型有不同的特性，并且存在是为了为设备驱动程序识别的物理地址范围提供 :ref:`struct page <Pages>` 和内存映射服务。``ZONE_DEVICE`` 可以通过配置选项 `CONFIG_ZONE_DEVICE` 启用。
需要注意的是，许多内核操作只能使用 ``ZONE_NORMAL`` 进行，因此这是性能最关键的一个区域。区域将在 :ref:`Zones <zones>` 部分进一步讨论。
节点和区域范围之间的关系由固件报告的物理内存图、内存寻址的架构约束以及内核命令行中的某些参数决定。
例如，在具有 2 GB 内存的 x86 UMA 机器上，使用 32 位内核时，整个内存都位于节点 0 上，并且有三个区域：``ZONE_DMA``、``ZONE_NORMAL`` 和 ``ZONE_HIGHMEM``：

```
  0                                                            2G
  +-------------------------------------------------------------+
  |                            node 0                           |
  +-------------------------------------------------------------+

  0         16M                    896M                        2G
  +----------+-----------------------+--------------------------+
  | ZONE_DMA |      ZONE_NORMAL      |       ZONE_HIGHMEM       |
  +----------+-----------------------+--------------------------+
```

在禁用 ``ZONE_DMA`` 并启用 ``ZONE_DMA32`` 的情况下，并且使用 ``movablecore=80%`` 参数启动的情况下，在具有 16 GB 内存并均匀分配到两个节点的 arm64 机器上，节点 0 将有 ``ZONE_DMA32``、``ZONE_NORMAL`` 和 ``ZONE_MOVABLE``，而节点 1 将有 ``ZONE_NORMAL`` 和 ``ZONE_MOVABLE``：

```
  1G                                9G                         17G
  +--------------------------------+ +--------------------------+
  |              node 0            | |          node 1          |
  +--------------------------------+ +--------------------------+

  1G       4G        4200M          9G          9320M          17G
  +---------+----------+-----------+ +------------+-------------+
  |  DMA32  |  NORMAL  |  MOVABLE  | |   NORMAL   |   MOVABLE   |
  +---------+----------+-----------+ +------------+-------------+
```

内存银行可能属于交错节点。在下面的例子中，x86 机器有 16 GB 内存分布在 4 个内存银行中，偶数银行属于节点 0，奇数银行属于节点 1：

```
  0              4G              8G             12G            16G
  +-------------+ +-------------+ +-------------+ +-------------+
  |    node 0   | |    node 1   | |    node 0   | |    node 1   |
  +-------------+ +-------------+ +-------------+ +-------------+

  0   16M      4G
  +-----+-------+ +-------------+ +-------------+ +-------------+
  | DMA | DMA32 | |    NORMAL   | |    NORMAL   | |    NORMAL   |
  +-----+-------+ +-------------+ +-------------+ +-------------+
```

在这种情况下，节点 0 跨度从 0 到 12 GB，节点 1 跨度从 4 到 16 GB。
.. _nodes:

节点
====

正如我们所提到的，每个内存节点都由一个 `pg_data_t` 描述，它是 `struct pglist_data` 的类型定义。在分配页面时，默认情况下 Linux 使用节点本地分配策略，从最接近运行 CPU 的节点分配内存。由于进程倾向于在同一 CPU 上运行，因此很可能使用当前节点的内存。分配策略可以由用户控制，具体描述请参阅 `Documentation/admin-guide/mm/numa_memory_policy.rst`。
大多数 NUMA 架构维护一个指向节点结构的指针数组。实际结构在引导过程中由架构特定代码解析固件报告的物理内存图时进行分配。节点初始化的主要工作稍后通过 `free_area_init()` 函数完成，该函数在 :ref:`Initialization <initialization>` 部分中有详细描述。
除了节点结构外，内核还维护了一个名为 `node_states` 的 `nodemask_t` 位掩码数组。该数组中的每个位掩码表示一组具有特定特性的节点，这些特性由 `enum node_states` 定义：

``N_POSSIBLE``
  该节点有可能在某个时刻上线
``N_ONLINE``
节点在线

``N_NORMAL_MEMORY``
节点具有常规内存

``N_HIGH_MEMORY``
节点具有常规或高内存。当禁用 ``CONFIG_HIGHMEM`` 时，等同于 ``N_NORMAL_MEMORY``

``N_MEMORY``
节点具有内存（常规、高、可移动）

``N_CPU``
节点有一个或多个 CPU

对于每个具有上述属性的节点，在 ``node_states[<property>]`` 位掩码中与节点 ID 对应的位会被设置。
例如，对于具有常规内存和 CPU 的节点 2，位 2 将在以下位掩码中被设置：

``node_states[N_POSSIBLE]``
``node_states[N_ONLINE]``
``node_states[N_NORMAL_MEMORY]``
``node_states[N_HIGH_MEMORY]``
``node_states[N_MEMORY]``
``node_states[N_CPU]``

关于节点掩码可以执行的各种操作，请参阅 ``include/linux/nodemask.h``。
其中，节点掩码用于提供节点遍历的宏，如 ``for_each_node()`` 和 ``for_each_online_node()``。
例如，要为每个在线节点调用函数 foo() ：

```c
for_each_online_node(nid) {
    pg_data_t *pgdat = NODE_DATA(nid);

    foo(pgdat);
}
```

节点结构
--------------

节点结构 ``struct pglist_data`` 在 ``include/linux/mmzone.h`` 中声明。以下是该结构的一些字段的简要描述：

通用部分
~~~~~~~

``node_zones``
  该节点的区域列表。并不是所有区域都会被填充，但这包含完整的列表。它由该节点的 `node_zonelists` 以及其它节点的 `node_zonelists` 引用。

``node_zonelists``
  所有节点中的所有区域的列表。这个列表定义了分配时偏好的区域顺序。`node_zonelists` 由 `mm/page_alloc.c` 中的 `build_zonelists()` 函数在核心内存管理结构初始化期间设置。

``nr_zones``
  该节点中已填充的区域数量

``node_mem_map``
  对于使用 FLATMEM 内存模型的 UMA 系统，节点 0 的 `node_mem_map` 是一个表示每个物理帧的 `struct page` 数组。
``node_page_ext``
  对于使用FLATMEM内存模型的UMA系统，0号节点的`node_page_ext`是一个结构体页面扩展的数组。仅在启用`CONFIG_PAGE_EXTENSION`配置选项的内核中可用。

``node_start_pfn``
  该节点起始页框的页框编号（Page Frame Number）。

``node_present_pages``
  该节点中存在的物理页面总数。

``node_spanned_pages``
  物理页面范围的总大小，包括空洞。

``node_size_lock``
  一个保护定义节点范围字段的锁。仅当启用了`CONFIG_MEMORY_HOTPLUG`或`CONFIG_DEFERRED_STRUCT_PAGE_INIT`配置选项中的至少一个时才定义。

`pgdat_resize_lock()` 和 `pgdat_resize_unlock()` 提供了对`node_size_lock`的操作，而无需检查`CONFIG_MEMORY_HOTPLUG`或`CONFIG_DEFERRED_STRUCT_PAGE_INIT`是否启用。

``node_id``
  节点的节点ID（NID），从0开始。

``totalreserve_pages``
  这是每个节点保留的页面数量，这些页面不可用于用户空间分配。

``first_deferred_pfn``
  如果在大型机器上延迟了内存初始化，则这是需要初始化的第一个PFN。仅在启用`CONFIG_DEFERRED_STRUCT_PAGE_INIT`配置选项时定义。

``deferred_split_queue``
  每个节点的延迟拆分的巨大页面队列。仅在启用`CONFIG_TRANSPARENT_HUGEPAGE`配置选项时定义。

``__lruvec``
  每个节点的lruvec，包含LRU列表及其相关参数。仅在禁用内存cgroup时使用。不应直接访问，应使用`mem_cgroup_lruvec()`来查找lruvecs。
重新获取控制
~~~~~~~~~~~~~~~

另见文档：Documentation/mm/page_reclaim.rst
``kswapd``
  每个节点的 kswapd 内核线程实例
``kswapd_wait``, ``pfmemalloc_wait``, ``reclaim_wait``
  用于同步内存回收任务的工作队列

``nr_writeback_throttled``
  等待脏页被清理时被节流的任务数量
``nr_reclaim_start``
  在回收过程中因等待写回而被节流期间写入的页面数量
``kswapd_order``
  控制 kswapd 尝试回收的顺序

``kswapd_highest_zoneidx``
  kswapd 进行回收的最高区域索引

``kswapd_failures``
  kswapd 无法回收任何页面的运行次数

``min_unmapped_pages``
  不能被回收的最小未映射文件支持页面数量。由 `vm.min_unmapped_ratio` sysctl 确定。仅在启用 `CONFIG_NUMA` 时定义
``min_slab_pages``
  不能被回收的最小 SLAB 页面数量。由 `vm.min_slab_ratio` sysctl 确定。仅在启用 `CONFIG_NUMA` 时定义

``flags``
  控制回收行为的标志
压缩控制
~~~~~~~~~~~~~~~~~~

``kcompactd_max_order``
  kcompactd 应该尝试实现的页面顺序
``kcompactd_highest_zoneidx``
  kcompactd 进行压缩的最高区域索引
``kcompactd_wait``
  用于同步内存压缩任务的工作队列
``kcompactd``
每个节点的 kcompactd 内核线程实例

``proactive_compact_trigger``
确定是否启用了主动压缩。由 ``vm.compaction_proactiveness`` sysctl 控制

统计信息
~~~~~~~~~~

``per_cpu_nodestats``
每个 CPU 的节点虚拟内存统计信息

``vm_stat``
节点的虚拟内存统计信息

.. _zones:

区域
=====

.. 注意::

   本节尚未完成。请列出并描述相应的字段

.. _pages:

页面
=====

.. 注意::

   本节尚未完成。请列出并描述相应的字段

.. _folios:

页集
======

.. 注意::

   本节尚未完成。请列出并描述相应的字段

.. _initialization:

初始化
==============

.. 注意::

   本节尚未完成。请列出并描述相应的字段
