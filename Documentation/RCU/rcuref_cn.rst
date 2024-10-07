SPDX 许可证标识符: GPL-2.0

====================================================================
用于受 RCU 保护的列表/数组元素的引用计数设计
====================================================================

请注意，如果您需要结合使用引用计数和 RCU，percpu-ref 功能很可能是您的首选。请参阅 include/linux/percpu-refcount.h 获取更多信息。然而，在那些不常见的情况下，如果 percpu-ref 会消耗过多内存，请继续阅读。

对于由传统读写自旋锁或信号量保护的列表中的元素进行引用计数是非常直接的：

代码清单 A::

    1.					    2
add()				    search_and_reference()
    {					    {
	alloc_object				read_lock(&list_lock);
	...					search_for_element
	atomic_set(&el->rc, 1);			atomic_inc(&el->rc);
	write_lock(&list_lock);			 ..
add_element				read_unlock(&list_lock);
	...					..
write_unlock(&list_lock);	   }
    }

    3.					    4
release_referenced()		    delete()
    {					    {
	...					write_lock(&list_lock);
	if(atomic_dec_and_test(&el->rc))	..
kfree(el);
	...					remove_element
    }						write_unlock(&list_lock);
						..
if (atomic_dec_and_test(&el->rc))
						    kfree(el);
						..
}

如果将这个列表/数组通过 RCU 改为无锁化处理，即在 add() 和 delete() 中将 write_lock() 更改为 spin_lock()，并将 search_and_reference() 中的 read_lock() 更改为 rcu_read_lock()，那么 search_and_reference() 中的 atomic_inc() 可能会保留一个已经被从列表/数组中删除的元素的引用。在这种情况下，请改用 atomic_inc_not_zero()，如下所示：

代码清单 B::

    1.					    2
add()				    search_and_reference()
    {					    {
	alloc_object				rcu_read_lock();
	...					search_for_element
	atomic_set(&el->rc, 1);			if (!atomic_inc_not_zero(&el->rc)) {
	spin_lock(&list_lock);			    rcu_read_unlock();
						    return FAIL;
	add_element				}
	...					..
```c
// 解锁自旋锁和RCU读锁
spin_unlock(&list_lock);  
rcu_read_unlock();

}  // 结束括号
}

// 释放引用对象并删除
release_referenced()          delete()
{                            {
...                          spin_lock(&list_lock);
if (atomic_dec_and_test(&el->rc))     ..
   call_rcu(&el->head, el_free);   remove_element
...                          spin_unlock(&list_lock);
}                           ..
if (atomic_dec_and_test(&el->rc))
                            call_rcu(&el->head, el_free);
..
}

// 有时候，在更新（写）流中需要获取元素的引用。在这种情况下，使用 atomic_inc_not_zero() 可能有些过度，因为我们已经持有了更新侧的自旋锁。因此，可以改为使用 atomic_inc()。
// 在 search_and_reference() 的代码路径中处理“FAIL”并不总是方便。在这样的情况下，可以将 atomic_dec_and_test() 从 delete() 移动到 el_free() 中，如下所示：

// 代码清单 C:

// 添加
1.                          2.
add()                          search_and_reference()
{                              {
  alloc_object                    rcu_read_lock();
  ...                            search_for_element
  atomic_set(&el->rc, 1);        atomic_inc(&el->rc);
  spin_lock(&list_lock);         ..
  add_element                     rcu_read_unlock();
  ...                            }
  spin_unlock(&list_lock);       4
}                              delete()
  3.                          {
  release_referenced()            spin_lock(&list_lock);
  {                              ..
  ...                            remove_element
  if (atomic_dec_and_test(&el->rc))  spin_unlock(&list_lock);
      kfree(el);                  ..
  }                             ..
}
```

这段代码展示了在不同场景下如何处理元素引用的增加和减少，并展示了如何将某些操作移动以简化流程。
```c
...					call_rcu(&el->head, el_free);
}						..
5.					    }
void el_free(struct rcu_head *rhp)
{
    release_referenced();
}
```

关键点在于，通过 `add()` 添加的初始引用直到移除操作后经过一个宽限期才被移除。这意味着 `search_and_reference()` 无法找到这个元素，因此 `el->rc` 的值不会增加。因此，一旦它变为零，就没有读者能够或将来能够引用该元素。因此，可以安全地释放该元素。这也保证了，如果任何读者找到了该元素，该读者可以安全地获取一个引用而无需检查引用计数器的值。

清单 C 中基于 RCU 的模式相对于清单 B 中的模式的一个明显优势是，即使对于同一个对象并发调用了 `delete()`，任何调用 `search_and_reference()` 找到该对象的情况都将成功获得对该对象的引用。

同样，清单 B 和 C 相对于清单 A 的一个明显优势是，即使有任意大量的调用 `search_and_reference()` 在查找 `delete()` 被调用的对象，`delete()` 的调用也不会被延迟。相反，唯一被延迟的是 `kfree()` 的最终调用，在现代计算机系统上，即使是小型系统，这通常也不是问题。

在 `delete()` 可以睡眠的情况下，可以从 `delete()` 中调用 `synchronize_rcu()`，从而使 `el_free()` 被合并到 `delete()` 中，如下所示：

```c
delete()
{
    spin_lock(&list_lock);
    ..
    remove_element
    spin_unlock(&list_lock);
    ..
    synchronize_rcu();
    if (atomic_dec_and_test(&el->rc))
        kfree(el);
    ..
}
```

作为内核中的其他示例，清单 C 中的模式用于 `struct pid` 的引用计数，而清单 B 中的模式用于 `struct posix_acl`。
