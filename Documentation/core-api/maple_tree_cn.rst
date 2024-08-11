### SPDX 许可证标识符: GPL-2.0+

####

#### 枫树
####

:作者: Liam R. Howlett

概述
====

枫树是一种B树数据类型，针对存储非重叠区间进行了优化，包括大小为1的区间。该树设计时考虑了易于使用，并不需要用户编写搜索方法。它支持以缓存高效的方式遍历一定范围的条目以及移动到前一个或后一个条目。该树还可以设置为RCU安全的操作模式，允许并发读写。写入者必须同步一个锁，可以是默认的自旋锁，也可以由用户将其设置为其他类型的外部锁。
枫树保持较小的内存占用，并且设计时考虑了现代处理器缓存的高效利用。大多数用户将能够使用正常的API。对于更复杂的情况，存在一个 :ref:`maple-tree-advanced-api`。枫树最重要的用途之一是跟踪虚拟内存区域。
枫树可以存储介于`0`和`ULONG_MAX`之间的值。枫树保留了底部两位为`10`且小于4096（即2、6、10...4094）的值用于内部使用。如果条目可能使用这些保留的条目，则用户可以使用`xa_mk_value()`进行转换，并通过调用`xa_to_value()`将其转换回来。如果用户需要使用保留值，则可以在使用 :ref:`maple-tree-advanced-api`时转换该值，但在正常API中被阻止。
枫树还可以配置为支持搜索给定大小（或更大）的空缺。
预分配节点也支持使用 :ref:`maple-tree-advanced-api`。这对于必须在给定代码段内保证成功存储操作的用户非常有用，当无法分配时。节点的分配相对较小，大约256字节。
.. _maple-tree-normal-api:

正常API
========

首先初始化一个枫树，对于静态分配的枫树可以使用`DEFINE_MTREE()`，对于动态分配的可以使用`mt_init()`。新初始化的枫树包含从范围`0`至`ULONG_MAX`的一个`NULL`指针。目前支持两种类型的枫树：分配树和普通树。普通树具有更高的内部节点分支因子。分配树具有较低的分支因子，但允许用户从`0`向上或从`ULONG_MAX`向下搜索给定大小或更大的空缺。可以通过在初始化树时传入`MT_FLAGS_ALLOC_RANGE`标志来使用分配树。
然后可以使用`mtree_store()`或`mtree_store_range()`设置条目。`mtree_store()`会用新的条目覆盖任何已有的条目，并在成功时返回0，否则返回错误代码。`mtree_store_range()`以相同的方式工作，但接受一个区间。使用`mtree_load()`来检索给定索引处存储的条目。可以使用`mtree_erase()`通过仅知道该区间内的一个值来擦除整个区间，或者使用带有`NULL`条目的`mtree_store()`调用来部分擦除区间或一次性擦除多个区间。
如果你想只在一个区间（或索引）为空的情况下存储一个新的条目，可以使用`mtree_insert_range()`或`mtree_insert()`，它们会在区间不为空时返回-EEXIST。
你可以使用`mt_find()`从某个索引向上搜索一个条目。
你可以通过调用 `mt_for_each()` 来遍历指定范围内的每一项。你必须提供一个临时变量来存储游标。如果你想遍历树中的每一个元素，那么可以使用 `0` 和 `ULONG_MAX` 作为范围。如果调用者在整个遍历过程中会持有锁，那么可以考虑查看 :ref:`maple-tree-advanced-api` 部分中关于 `mas_for_each()` 的API。

有时需要确保下一次对枫树的存储操作不分配内存，在这种情况下，请参阅 :ref:`maple-tree-advanced-api`。

你可以使用 `mtree_dup()` 来复制整个枫树。这种方法比将所有元素逐个插入到新树中更高效。

最后，你可以通过调用 `mtree_destroy()` 来移除枫树中的所有条目。如果枫树的条目是指针，你可能希望先释放这些条目。

### 节点分配

节点分配由内部树代码处理。更多选项请参阅 :ref:`maple-tree-advanced-alloc`。

### 锁定

你无需担心锁定问题。其他选项请参阅 :ref:`maple-tree-advanced-locks`。

枫树使用 RCU 和内部自旋锁来同步访问：

- 使用RCU读锁：
  * `mtree_load()`
  * `mt_find()`
  * `mt_for_each()`
  * `mt_next()`
  * `mt_prev()`

- 内部使用 `ma_lock`：
  * `mtree_store()`
  * `mtree_store_range()`
  * `mtree_insert()`
  * `mtree_insert_range()`
  * `mtree_erase()`
  * `mtree_dup()`
  * `mtree_destroy()`
  * `mt_set_in_rcu()`
  * `mt_clear_in_rcu()`

如果你想要利用内部锁来保护你在枫树中存储的数据结构，你可以在调用 `mtree_load()` 之前调用 `mtree_lock()`，然后在调用 `mtree_unlock()` 之前获取你找到的对象的引用计数。这可以防止在查找对象和增加引用计数之间从树中删除该对象。你也可以使用 RCU 来避免引用已释放的内存，但详细解释超出了本文档的范围。

### 高级API

#### 高级API

高级API提供了更多的灵活性和更好的性能，代价是一个更难使用的接口以及较少的安全保障。

在使用高级API时，你需要自行处理锁定。

你可以使用 `ma_lock`、RCU 或外部锁进行保护。
您可以对同一个数组混合使用高级和普通操作，只要锁定方式兼容即可。`:ref:`maple-tree-normal-api` 是基于高级 API 实现的。
高级 API 主要围绕 `ma_state` 展开，这也是 `mas` 前缀的由来。`ma_state` 结构体跟踪树的操作，以便为内部和外部树用户简化操作。
初始化 Maple 树与`:ref:`maple-tree-normal-api`相同，请参见上述内容。
Maple 状态通过 `mas->index` 和 `mas->last` 分别跟踪范围的开始和结束。
`mas_walk()` 将遍历树到 `mas->index` 所指定的位置，并根据条目的范围设置 `mas->index` 和 `mas->last`。
您可以使用 `mas_store()` 来设置条目。`mas_store()` 会用新条目覆盖任何现有条目，并返回被覆盖的第一个现有条目。
范围作为 Maple 状态的成员传递：`index` 和 `last`。
您可以通过设置 Maple 状态中的 `index` 和 `last` 到期望的范围，使用 `mas_erase()` 来擦除整个范围。这将擦除在该范围内找到的第一个范围，并将 Maple 状态的 `index` 和 `last` 设置为已擦除的范围，然后返回该位置上存在的条目。
您可以使用 `mas_for_each()` 遍历范围内的每个条目。如果您想遍历树的每个元素，则可以使用 `0` 和 `ULONG_MAX` 作为范围。如果需要周期性地释放锁，请参阅锁定部分关于 `mas_pause()` 的说明。
使用maple状态使得`mas_next()`和`mas_prev()`能够像链表一样工作。由于具有如此高的分支因子，缓存优化所带来的好处超过了分摊性能损失。`mas_next()`将返回索引位置之后的下一个条目。`mas_prev()`将返回索引位置之前的上一个条目。`mas_find()`在首次调用时会找到第一个存在于或高于索引的条目，在后续的所有调用中则查找下一个条目。`mas_find_rev()`在首次调用时会找到第一个存在于或低于最后一个索引的条目，在后续的所有调用中则查找前一个条目。
如果用户在操作过程中需要释放锁，则必须使用`mas_pause()`暂停maple状态。
当使用分配树时，提供了一些额外的接口。
如果你想在一个范围内搜索空缺，可以使用`mas_empty_area()`或`mas_empty_area_rev()`。`mas_empty_area()`从给定的最低索引开始寻找空缺直到范围的最大值。`mas_empty_area_rev()`从给定的最高索引开始向下寻找空缺直到范围的下限。
_ :label: maple-tree-advanced-alloc

高级节点分配
--------------

分配通常由树内部处理，但如果需要在写入之前进行分配，则调用`mas_expected_entries()`将为插入提供的范围数量分配最坏情况所需的节点数。这也会使树进入批量插入模式。一旦插入完成，对maple状态调用`mas_destroy()`将释放未使用的分配。
_ :label: maple-tree-advanced-locks

高级锁定
--------------

maple树默认使用自旋锁，但也可以使用外部锁来更新树。要使用外部锁，树必须使用`MT_FLAGS_LOCK_EXTERN`标志初始化，这通常是通过`MTREE_INIT_EXT()`宏完成的，它接受一个外部锁作为参数。
函数和结构体
==================

.. kernel-doc:: include/linux/maple_tree.h
.. kernel-doc:: lib/maple_tree.c
