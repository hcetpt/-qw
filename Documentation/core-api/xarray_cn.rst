### SPDX 许可证标识符: GPL-2.0+

#### XArray

##### 作者: Matthew Wilcox

**概述**

XArray 是一种抽象数据类型，其行为类似于一个非常大的指针数组。它满足了许多与哈希表或传统可扩展数组相同的需求。与哈希表不同的是，它允许您以缓存高效的方式访问下一个或前一个条目。与可扩展数组相比，无需复制数据或更改内存管理单元（MMU）映射来扩展数组。它比双向链表更节省内存、更容易并行化且对缓存更友好。它利用 RCU（Read-Copy-Update）在不加锁的情况下执行查找操作。

XArray 在使用的索引密集聚类时实现效率较高；将对象进行哈希处理并使用该哈希值作为索引将不会表现良好。XArray 针对较小的索引进行了优化，但在较大的索引下仍具有良好的性能。如果您的索引可能大于 `ULONG_MAX`，那么 XArray 不适合您。XArray 最重要的用户是页缓存。

可以在 XArray 中直接存储正常的指针。这些指针必须是 4 字节对齐的，这是从 `kmalloc()` 和 `alloc_page()` 返回的任何指针的真实情况。但对于任意用户空间指针或函数指针来说则不是这样。您可以存储指向静态分配对象的指针，只要这些对象的对齐方式至少为 4 字节即可。

您还可以在 XArray 中存储介于 0 和 `LONG_MAX` 之间的整数，但首先需要使用 `xa_mk_value()` 将其转换为条目。
当从 XArray 中检索条目时，可以通过调用 `xa_is_value()` 检查是否为值条目，并通过调用 `xa_to_value()` 将其转换回整数。

一些用户希望标记他们存储在 XArray 中的指针。可以调用 `xa_tag_pointer()` 来创建带有标签的条目，使用 `xa_untag_pointer()` 将带标签的条目转回未带标签的指针，以及使用 `xa_pointer_tag()` 获取条目的标签。带标签的指针使用了区分值条目和普通指针相同的位，因此您必须决定是要在特定的 XArray 中存储值条目还是带标签的指针。

XArray 不支持存储 `IS_ERR()` 指针，因为其中一些与值条目或内部条目冲突。

XArray 的一个不寻常的功能是能够创建占据一系列索引的条目。一旦存储后，查询该范围内的任何索引都将返回与查询该范围内其他任何索引相同的条目。向任何索引存储都会存储到所有这些索引。多索引条目可以被显式地拆分为较小的条目，或者将 `NULL` 存储到任何条目中将导致 XArray 忽略该范围。

**常规 API**

首先初始化 XArray，对于静态分配的 XArray 使用 `DEFINE_XARRAY()`，对于动态分配的 XArray 使用 `xa_init()`。新初始化的 XArray 在每个索引处包含一个 `NULL` 指针。
然后，您可以使用 `xa_store()` 设置条目，并使用 `xa_load()` 获取条目。`xa_store` 会用新条目覆盖任何现有条目，并返回该索引处之前存储的条目。您可以使用 `xa_erase()` 替代带有 `NULL` 条目的 `xa_store()` 调用。从未被存储过的条目、已被删除的条目以及最近存储为 `NULL` 的条目之间没有区别。

您可以通过使用 `xa_cmpxchg()` 条件性地替换索引处的条目。与 `cmpxchg()` 类似，只有当该索引处的条目具有“旧”值时才会成功。它也会返回该索引处的条目；如果返回的条目与传入的“旧”条目相同，则说明 `xa_cmpxchg()` 成功。

如果您希望仅在当前索引处的条目为空 (`NULL`) 时才存储新的条目到该索引，可以使用 `xa_insert()`，它会在条目非空时返回 `-EBUSY`。

您可以通过调用 `xa_extract()` 将条目从 XArray 复制到普通数组中。或者，您可以使用 `xa_for_each()`、`xa_for_each_start()` 或 `xa_for_each_range()` 遍历 XArray 中存在的所有条目。
您可能更倾向于使用 `xa_find()` 或 `xa_find_after()` 移动到 XArray 中下一个存在的条目。

调用 `xa_store_range()` 可以在一系列索引中存储相同的条目。如果您这样做，某些其他操作的行为可能会略有不同。例如，在一个索引处标记条目可能导致其他一些索引处的条目也被标记，但并非全部。在一个索引处存储可能会导致通过其他一些索引检索的条目发生变化，但并非全部。

有时，您需要确保随后对 `xa_store()` 的调用不需要分配内存。`xa_reserve()` 函数将在指定索引处存储预留条目。常规 API 的用户将看到此条目包含 `NULL`。如果您不打算使用预留条目，可以调用 `xa_release()` 删除未使用的条目。如果在此期间其他用户已向该条目进行了存储，则 `xa_release()` 不会执行任何操作；如果您希望该条目变为 `NULL`，则应使用 `xa_erase()`。
在预留条目上使用 `xa_insert()` 将失败。

如果数组中的所有条目都是 `NULL`，`xa_empty()` 函数将返回 `true`。

最后，您可以通过调用 `xa_destroy()` 从 XArray 中移除所有条目。如果 XArray 的条目是指针，您可能希望先释放这些条目。您可以通过使用 `xa_for_each()` 迭代器遍历 XArray 中的所有现有条目来实现这一点。
### 搜索标记
------------

数组中的每个条目都与三个称为“标记”的位相关联。
每个标记可以独立于其他标记被设置或清除。你可以使用`xa_for_each_marked()`迭代器来遍历带有标记的条目。你可以通过使用`xa_get_mark()`来查询一个条目上是否设置了标记。如果条目不是`NULL`，你可以使用`xa_set_mark()`在它上面设置标记，并通过调用`xa_clear_mark()`来移除条目上的标记。你可以通过调用`xa_marked()`来询问XArray中是否有任何条目设置了特定的标记。从XArray中删除一个条目会导致与该条目相关的所有标记被清除。
在一个多索引条目上的任何索引处设置或清除标记将影响由该条目覆盖的所有索引。查询任何索引上的标记都会返回相同的结果。
没有办法遍历未标记的条目；数据结构不允许以高效的方式实现这一点。目前没有迭代器可以搜索位的逻辑组合（例如，遍历所有同时设置了`XA_MARK_1`和`XA_MARK_2`的条目，或者遍历所有设置了`XA_MARK_0`或`XA_MARK_2`的条目）。如果出现用户需求，可以添加这些功能。

### 分配XArray
------------------

如果你使用`DEFINE_XARRAY_ALLOC()`定义XArray，或者在初始化时通过向`xa_init_flags()`传递`XA_FLAGS_ALLOC`标志来初始化它，XArray会跟踪条目是否正在使用。
你可以调用`xa_alloc()`来在XArray中未使用的索引处存储条目。如果你需要在中断上下文中修改数组，可以使用`xa_alloc_bh()`或`xa_alloc_irq()`在分配ID时禁用中断。
使用`xa_store()`、`xa_cmpxchg()`或`xa_insert()`也会标记条目为已分配。与普通XArray不同的是，存储`NULL`也会标记条目为正在使用，类似于`xa_reserve()`。
要释放一个条目，请使用`xa_erase()`（或者如果你想仅当条目是`NULL`时才释放它，则使用`xa_release()`）。
默认情况下，从0开始分配最低的空闲条目。如果你想从1开始分配条目，使用`DEFINE_XARRAY_ALLOC1()`或`XA_FLAGS_ALLOC1`会更有效。如果你想分配ID直到某个最大值，然后循环回到最低的空闲ID，你可以使用`xa_alloc_cyclic()`。
你不能在分配内存的 XArray 中使用 `XA_MARK_0` 这个标记，因为这个标记被用来跟踪某个条目是否为空闲。其他的标记可供你使用。
内存分配
---------

函数 `xa_store()`、`xa_cmpxchg()`、`xa_alloc()`、`xa_reserve()` 和 `xa_insert()` 接受一个 `gfp_t` 参数，用于在 XArray 需要分配内存来存储该条目时使用。如果条目将被删除，则不需要进行内存分配，指定的 GFP 标志会被忽略。有可能无法分配到内存，特别是当你传递了一组限制性的 GFP 标志。在这种情况下，这些函数会返回一个特殊值，你可以通过 `xa_err()` 函数将其转换为一个错误号。如果你不需要确切知道发生了哪个错误，使用 `xa_is_err()` 方法会稍微更高效一些。
锁定
------

当你使用正常API时，你无需担心锁定问题。XArray 使用 RCU 和内部自旋锁来进行访问同步：

无需锁定：
 * `xa_empty()`
 * `xa_marked()`

获取 RCU 读锁：
 * `xa_load()`
 * `xa_for_each()`
 * `xa_for_each_start()`
 * `xa_for_each_range()`
 * `xa_find()`
 * `xa_find_after()`
 * `xa_extract()`
 * `xa_get_mark()`

内部获取 `xa_lock`：
 * `xa_store()`
 * `xa_store_bh()`
 * `xa_store_irq()`
 * `xa_insert()`
 * `xa_insert_bh()`
 * `xa_insert_irq()`
 * `xa_erase()`
 * `xa_erase_bh()`
 * `xa_erase_irq()`
 * `xa_cmpxchg()`
 * `xa_cmpxchg_bh()`
 * `xa_cmpxchg_irq()`
 * `xa_store_range()`
 * `xa_alloc()`
 * `xa_alloc_bh()`
 * `xa_alloc_irq()`
 * `xa_reserve()`
 * `xa_reserve_bh()`
 * `xa_reserve_irq()`
 * `xa_destroy()`
 * `xa_set_mark()`
 * `xa_clear_mark()`

假设调用时已持有 `xa_lock`：
 * `__xa_store()`
 * `__xa_insert()`
 * `__xa_erase()`
 * `__xa_cmpxchg()`
 * `__xa_alloc()`
 * `__xa_set_mark()`
 * `__xa_clear_mark()`

如果你想利用这个锁来保护存储在 XArray 中的数据结构，你可以在调用 `xa_load()` 之前调用 `xa_lock()`，然后在调用 `xa_unlock()` 之前对找到的对象增加引用计数。这将防止其他存储操作在查找对象和增加引用计数之间移除该对象。你也可以使用 RCU 来避免引用已释放的内存，但这超出了本文档的范围。
XArray 在修改数组时不会禁用中断或软中断。从中断或软中断上下文中安全地读取 XArray 是可以的，因为 RCU 锁提供了足够的保护。
例如，如果你想在进程上下文中存储 XArray 的条目，然后在软中断上下文中删除它们，你可以这样做：

```c
void foo_init(struct foo *foo)
{
    xa_init_flags(&foo->array, XA_FLAGS_LOCK_BH);
}

int foo_store(struct foo *foo, unsigned long index, void *entry)
{
    int err;

    xa_lock_bh(&foo->array);
    err = xa_err(__xa_store(&foo->array, index, entry, GFP_KERNEL));
    if (!err)
        foo->count++;
    xa_unlock_bh(&foo->array);
    return err;
}

/* foo_erase() 只在软中断上下文中调用 */
void foo_erase(struct foo *foo, unsigned long index)
{
    xa_lock(&foo->array);
    __xa_erase(&foo->array, index);
    foo->count--;
    xa_unlock(&foo->array);
}
```

如果你打算从中断或软中断上下文中修改 XArray，你需要使用 `xa_init_flags()` 初始化数组，并传递 `XA_FLAGS_LOCK_IRQ` 或 `XA_FLAGS_LOCK_BH`。
上面的例子还展示了一个常见的模式，即希望扩展 `xa_lock` 在存储一侧的作用范围以保护与数组相关的某些统计信息。
与中断上下文共享 XArray 也是可能的，可以在中断处理程序和进程上下文中都使用 `xa_lock_irqsave()`，或者在进程上下文中使用 `xa_lock_irq()`，而在中断处理程序中使用 `xa_lock()`。一些更常见的模式有辅助函数，如 `xa_store_bh()`、`xa_store_irq()`、`xa_erase_bh()`、`xa_erase_irq()`、`xa_cmpxchg_bh()` 和 `xa_cmpxchg_irq()`。

有时你需要用互斥锁保护对 XArray 的访问，因为该锁位于锁定层次结构中的另一个互斥锁之上。但这并不意味着你可以不获取 `xa_lock` 就使用像 `__xa_erase()` 这样的函数；`xa_lock` 用于锁定依赖性验证，并且将来可能会用于其他目的。

`__xa_set_mark()` 和 `__xa_clear_mark()` 函数也可用于在查找条目并希望原子性地设置或清除标记的情况下。在这种情况下，使用高级 API 可能更高效，因为它可以避免两次遍历树。

### 高级 API

高级 API 提供了更多的灵活性和更好的性能，但代价是接口更难使用且安全措施较少。高级 API 不会为你执行任何锁定操作，你在修改数组时必须使用 `xa_lock`。你可以在对数组进行只读操作时选择使用 `xa_lock` 或 RCU 锁。你可以在同一个数组上混合使用高级和常规操作；实际上，常规 API 是基于高级 API 实现的。只有拥有与 GPL 兼容许可证的模块才能使用高级 API。

高级 API 基于 `xa_state`。这是一个使用 `XA_STATE()` 宏在栈上声明的不透明数据结构。此宏初始化 `xa_state`，以便开始遍历 XArray。它用作游标以保持在 XArray 中的位置，并允许你组合各种操作而无需每次都从头开始。`xa_state` 的内容受到 `rcu_read_lock()` 或 `xas_lock()` 的保护。如果你需要释放保护状态和树的任一锁，必须调用 `xas_pause()`，以便后续调用不会依赖未受保护的状态部分。

`xa_state` 也用于存储错误。你可以通过调用 `xas_error()` 来获取错误。所有操作都会检查 `xa_state` 是否处于错误状态，因此无需在每次调用后检查错误；你可以连续调用多个函数并在适当的时候检查错误。目前 XArray 代码本身生成的唯一错误是 `ENOMEM` 和 `EINVAL`，但它支持任意错误，以防你需要自己调用 `xas_set_err()`。

如果 `xa_state` 持有一个 `ENOMEM` 错误，调用 `xas_nomem()` 将尝试使用指定的 gfp 标志分配更多内存，并将其缓存在 `xa_state` 中以备下次尝试。其思路是你获取 `xa_lock`，尝试执行操作并释放锁。操作在持有锁的情况下尝试分配内存，但更有可能失败。一旦你释放了锁，`xas_nomem()` 可以更努力地尝试分配更多内存。如果值得重试操作（即存在内存错误并且分配了更多内存），它将返回 `true`。如果它之前已分配内存，且该内存未被使用，并且没有错误（或不是 `ENOMEM` 的错误），那么它将释放之前分配的内存。

### 内部条目

XArray 保留了一些条目供自身使用。这些条目不会通过常规 API 暴露出来，但在使用高级 API 时可以看到它们。通常最好的处理方式是将它们传递给 `xas_retry()`，如果返回 `true` 则重试操作。
下面是提供的英文内容翻译成中文的结果：

... flat-table::
   :widths: 1 1 6

   * - 名称
     - 测试
     - 使用情况

   * - 节点
     - xa_is_node()
     - 表示一个 XArray 节点。在使用多索引 xa_state 时可能会可见。
* - 同级节点
     - xa_is_sibling()
     - 多索引条目的非规范条目。该值指示此节点中哪个槽位包含规范条目。
* - 重试
     - xa_is_retry()
     - 此条目当前正由持有 xa_lock 的线程进行修改。包含此条目的节点可能在本 RCU 周期结束时被释放。您应从数组头部重新开始查找。
* - 零
     - xa_is_zero()
     - 零条目通过常规 API 显示为 `NULL`，但占用 XArray 中的一个条目，可用于为将来使用预留索引。这用于为分配的条目（其值为 `NULL`）分配 XArray。
其他内部条目将来可能会添加。尽可能地，它们将由 xas_retry() 处理。
附加功能
------------------------

函数 xas_create_range() 分配存储范围中每个条目的所有必要内存。如果无法分配内存，则会在 xa_state 中设置 ENOMEM。
您可以使用 xas_init_marks() 来重置条目上的标记到其默认状态。这通常是清除所有标记，除非 XArray 标记有 `XA_FLAGS_TRACK_FREE`，在这种情况下，标记 0 被设置，而所有其他标记被清除。使用 xas_store() 替换一个条目时不会重置该条目上的标记；如果您希望重置这些标记，应该显式执行。
函数 xas_load() 尽可能地遍历 xa_state 到达目标条目。如果您已知 xa_state 已经遍历到了目标条目，并且需要检查该条目是否发生了变化，可以使用 xas_reload() 来节省一次函数调用。
如果您需要在 XArray 中移动到不同的索引，请调用 xas_set()。这会将光标重置到树的顶部，通常会使下一次操作遍历光标到达树中的期望位置。如果您想移动到下一个或前一个索引，可以调用 xas_next() 或 xas_prev()。设置索引不会使光标在数组中移动，因此不需要持有锁；而移动到下一个或前一个索引则需要。
您可以使用 xas_find() 搜索下一个存在的条目。这相当于 xa_find() 和 xa_find_after() 的组合；如果光标已经遍历到了某个条目，则它会找到当前引用条目之后的下一个条目。如果没有，则返回位于 xa_state 索引处的条目。在大多数情况下，使用 xas_next_entry() 而不是 xas_find() 移动到下一个存在的条目可以节省一次函数调用，代价是生成更多的内联代码。
`xas_find_marked()` 函数也类似。如果 `xa_state` 尚未遍历，则如果该索引处的条目被标记，它将返回 `xa_state` 中索引对应的条目；否则，它会返回 `xa_state` 引用的条目之后的第一个已标记条目。`xas_next_marked()` 函数相当于 `xas_next_entry()`。

在使用 `xas_for_each()` 或 `xas_for_each_marked()` 遍历 XArray 的一个范围时，可能需要暂时停止遍历。为此，存在 `xas_pause()` 函数。当你完成必要的工作并希望继续时，`xa_state` 处于适当的状态，可以从你上次处理的条目之后继续遍历。如果你在遍历时禁用了中断，那么每 `XA_CHECK_SCHED` 个条目后暂停遍历并重新启用中断是一种良好的做法。

`xas_get_mark()`、`xas_set_mark()` 和 `xas_clear_mark()` 函数要求 `xa_state` 游标移动到 XArray 中适当的位置；如果你刚调用过 `xas_pause()` 或 `xas_set()`，它们将不执行任何操作。

你可以通过调用 `xas_set_update()` 来设置一个回调函数，每次 XArray 更新节点时都会调用这个函数。这被页缓存工作集代码用来维护其仅包含影子条目的节点列表。

### 多索引条目

XArray 能够将多个索引绑定在一起，使得对一个索引的操作会影响所有索引。例如，在任何一个索引中存储数据将改变从任何索引检索的条目的值。在任何一个索引上设置或清除标记也将设置或清除所有绑定在一起的索引上的标记。当前实现只允许绑定以二的幂次方对齐的范围；例如，可以将索引 64-127 绑定在一起，但不能绑定 2-6。这可能会节省大量的内存；例如，将 512 个条目绑定在一起可以节省超过 4kB 的内存。

可以通过使用 `XA_STATE_ORDER()` 或 `xas_set_order()` 然后调用 `xas_store()` 来创建多索引条目。

使用多索引 `xa_state` 调用 `xas_load()` 会将 `xa_state` 移动到树中的正确位置，但返回值没有意义，可能是内部条目或 `NULL`，即使在范围内有存储的条目也是如此。调用 `xas_find_conflict()` 会返回范围内的第一个条目，如果没有条目则返回 `NULL`。`xas_for_each_conflict()` 迭代器会遍历与指定范围重叠的所有条目。

如果 `xas_load()` 遇到多索引条目，`xa_state` 中的 `xa_index` 不会被更改。当遍历 XArray 或调用 `xas_find()` 时，如果初始索引位于多索引条目的中间，它不会被修改。随后的调用或迭代将索引移动到范围内的第一个索引。
每个条目只会返回一次，无论它占据了多少个索引。
使用 xas_next() 或 xas_prev() 在一个多索引的 xa_state 上是不被支持的。在这类多索引条目上使用这两个函数中的任何一个都会显示出兄弟条目；这些应该由调用者跳过。
将 ``NULL`` 存储到一个多索引条目的任何索引中将会把该条目在所有索引处设置为 ``NULL`` 并解除绑定。通过在不持有 xa_lock 的情况下调用 xas_split_alloc()，然后获取锁并调用 xas_split()，可以将一个多索引条目分割成占据较小范围的条目。

函数和结构体
=============

.. kernel-doc:: include/linux/xarray.h
.. kernel-doc:: lib/xarray.c
