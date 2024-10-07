SPDX 许可证标识符: GPL-2.0

=================================================
使用 RCU hlist_nulls 来保护列表和对象
=================================================

本节描述了如何使用 hlist_nulls 来保护主要为只读的链表和通过 SLAB_TYPESAFE_BY_RCU 分配的对象。请先阅读 listRCU.rst 中的基本概念。
使用 'nulls'
=============

使用特殊标记（称为 'nulls'）是一种方便的方法来解决以下问题：
没有 'nulls'，一个典型的通过 SLAB_TYPESAFE_BY_RCU kmem_cache 分配的对象管理的 RCU 链表可以使用以下算法。以下示例假设 'obj' 是指向此类对象的指针，并具有以下类型：

```
struct object {
    struct hlist_node obj_node;
    atomic_t refcnt;
    unsigned int key;
};
```

1) 查找算法
-------------------

```
begin:
rcu_read_lock();
obj = lockless_lookup(key);
if (obj) {
    if (!try_get_ref(obj)) { // 可能会失败，对于已释放的对象
        rcu_read_unlock();
        goto begin;
    }
    /*
     * 由于写入者可能会删除对象，并且在 RCU 宽限期之前重用这些对象，
     * 因此在获取对象引用后必须检查 key。
     */
    if (obj->key != key) { // 不是我们预期的对象
        put_ref(obj);
        rcu_read_unlock();
        goto begin;
    }
}
rcu_read_unlock();
```

请注意，lockless_lookup(key) 不能使用传统的 hlist_for_each_entry_rcu()，而应使用带有额外内存屏障的版本 (smp_rmb())。

```
lockless_lookup(key)
{
    struct hlist_node *node, *next;
    for (pos = rcu_dereference((head)->first);
         pos && ({ next = pos->next; smp_rmb(); prefetch(next); 1; }) &&
         ({ obj = hlist_entry(pos, typeof(*obj), obj_node); 1; });
         pos = rcu_dereference(next))
        if (obj->key == key)
            return obj;
    return NULL;
}
```

请注意，传统的 hlist_for_each_entry_rcu() 缺少这个 smp_rmb()：

```
struct hlist_node *node;
for (pos = rcu_dereference((head)->first);
     pos && ({ prefetch(pos->next); 1; }) &&
     ({ obj = hlist_entry(pos, typeof(*obj), obj_node); 1; });
     pos = rcu_dereference(pos->next))
    if (obj->key == key)
        return obj;
return NULL;
```

引用 Corey Minyard 的话：

“如果对象在计算哈希值和访问 next 字段之间从一个列表移动到另一个列表，并且该对象移动到了新列表的末尾，遍历将无法在应该完成的列表上正确完成，因为该对象位于新列表的末尾，而且没有办法判断它在新列表上并重新开始列表遍历。我认为可以通过在检查 key 之前预取 'next' 字段（带适当的屏障）来解决这个问题。”

2) 插入算法
----------------------

我们需要确保读取者不能读取新的 'obj->obj_node.next' 值和 'obj->key' 的旧值。否则，一个项目可以从一个链中删除，并插入到另一个链中。如果新链在移动前是空的，则 'next' 指针为 NULL，无锁读取器无法检测到它错过了原始链中的后续项。

```
/*
 * 请注意，新插入是在列表头部进行的，而不是中间或末尾
 */
obj = kmem_cache_alloc(...);
lock_chain(); // 通常是一个自旋锁
obj->key = key;
atomic_set_release(&obj->refcnt, 1); // key 在 refcnt 之前设置
hlist_add_head_rcu(&obj->obj_node, list);
unlock_chain(); // 通常是一个自旋解锁
```


3) 删除算法
--------------------

这里没有什么特别之处，我们可以使用标准的 RCU hlist 删除。
但请注意，由于 SLAB_TYPESAFE_BY_RCU，被删除的对象可以非常快地被重用（在 RCU 宽限期结束之前）。

```
if (put_last_reference_on(obj) {
    lock_chain(); // 通常是一个自旋锁
    hlist_del_init_rcu(&obj->obj_node);
    unlock_chain(); // 通常是一个自旋解锁
    kmem_cache_free(cachep, obj);
}
```

--------------------------------------------------------------------------

避免额外的 smp_rmb()
========================

使用 hlist_nulls 我们可以在 lockless_lookup() 中避免额外的 smp_rmb()。
例如，如果我们选择将哈希表每个槽的槽号作为 'nulls' 的链尾标记，我们可以通过检查最终的 'nulls' 值来检测竞争（某个写入者执行了删除操作或将对象移到了另一个链）。如果最终的 'nulls' 值不是槽号，则我们必须从头开始重新查找。如果对象移到了同一链中，那么读取者并不关心：偶尔重新扫描列表也不会造成伤害。
请注意，使用 hlist_nulls 意味着 'struct object' 中 'obj_node' 字段的类型变为 'struct hlist_nulls_node'。
### 查找算法
```c
head = &table[slot];
begin:
rcu_read_lock();
hlist_nulls_for_each_entry_rcu(obj, node, head, obj_node) {
  if (obj->key == key) {
    if (!try_get_ref(obj)) { // 可能会失败，对于即将释放的对象
      rcu_read_unlock();
      goto begin;
    }
    if (obj->key != key) { // 不是我们期望的对象
      put_ref(obj);
      rcu_read_unlock();
      goto begin;
    }
    goto out;
  }
}

// 如果在此次查找结束时得到的 nulls 值不是预期值，则必须重新开始查找
// 我们可能遇到了一个被移动到另一个链表中的项
if (get_nulls_value(node) != slot) {
  put_ref(obj);
  rcu_read_unlock();
  goto begin;
}
obj = NULL;

out:
rcu_read_unlock();
```

### 插入算法
```c
// 和上面的查找算法类似，但使用 hlist_nulls_add_head_rcu() 而不是 hlist_add_head_rcu()
// 新插入的操作是在链表头部进行的，而不是中间或末尾

obj = kmem_cache_alloc(cachep);
lock_chain(); // 通常是一个自旋锁
obj->key = key;
atomic_set_release(&obj->refcnt, 1); // key 在 refcnt 之前设置
/*
 * 以 RCU 方式插入 obj（读者可能正在遍历链表）
*/
hlist_nulls_add_head_rcu(&obj->obj_node, list);
unlock_chain(); // 通常是一个自旋解锁
```
