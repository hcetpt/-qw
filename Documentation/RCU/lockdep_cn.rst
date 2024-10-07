.. SPDX许可证标识符: GPL-2.0

========================
RCU和锁依赖（lockdep）检查
========================

所有版本的RCU都提供了锁依赖检查功能，这意味着锁依赖能够感知到每个任务何时进入或离开任何类型的RCU读侧临界区。每种RCU版本分别进行跟踪（但请注意，在2.6.32及更早版本中并非如此）。这使得锁依赖的跟踪可以包含RCU状态，有时在调试死锁等问题时有所帮助。

此外，RCU提供了以下用于检查锁依赖状态的基本函数：

- `rcu_read_lock_held()` 用于标准RCU
- `rcu_read_lock_bh_held()` 用于RCU-bh
- `rcu_read_lock_sched_held()` 用于RCU-sched
- `rcu_read_lock_any_held()` 用于标准RCU、RCU-bh和RCU-sched中的任意一种
- `srcu_read_lock_held()` 用于SRCU
- `rcu_read_lock_trace_held()` 用于RCU任务追踪

这些函数是保守的，因此如果它们不确定（例如，如果未设置CONFIG_DEBUG_LOCK_ALLOC），则会返回1。这防止了当禁用锁依赖时出现如`WARN_ON(!rcu_read_lock_held())`这样的误报。

另外，一个独立的内核配置参数`CONFIG_PROVE_RCU`启用了对`rcu_dereference()`基本函数的检查：

- `rcu_dereference(p)`:
  检查RCU读侧临界区是否已正确进入
rcu_dereference_bh(p):
	检查RCU-bh读侧临界区
rcu_dereference_sched(p):
	检查RCU-sched读侧临界区
srcu_dereference(p, sp):
	检查SRCU读侧临界区
rcu_dereference_check(p, c):
	使用显式检查表达式"c"，并结合rcu_read_lock_held()。这在由RCU读取者和更新者调用的代码中很有用。
rcu_dereference_bh_check(p, c):
	使用显式检查表达式"c"，并结合rcu_read_lock_bh_held()。这在由RCU-bh读取者和更新者调用的代码中很有用。
rcu_dereference_sched_check(p, c):
	使用显式检查表达式"c"，并结合rcu_read_lock_sched_held()。这在由RCU-sched读取者和更新者调用的代码中很有用。
srcu_dereference_check(p, c):
	使用显式检查表达式"c"，并结合srcu_read_lock_held()。这在由SRCU读取者和更新者调用的代码中很有用。
rcu_dereference_raw(p):
	不进行检查。（谨慎使用，甚至不使用）
rcu_dereference_raw_check(p):
	完全不进行锁依赖检查。（谨慎使用，甚至不使用）
rcu_dereference_protected(p, c):
	使用显式检查表达式"c"，并省略所有屏障和编译器约束。当数据结构不会改变时，例如仅由更新者调用的代码中，这是有用的。
rcu_access_pointer(p):
	返回指针的值并省略所有屏障，但保留防止复制或合并的编译器约束。当测试指针本身的值（例如与NULL比较）时，这是有用的。

rcu_dereference_check()的检查表达式可以是任何布尔表达式，但通常包括一个锁依赖表达式。对于一个较为复杂的示例，考虑以下情况：

``` 
file = rcu_dereference_check(fdt->fd[fd],
				 lockdep_is_held(&files->file_lock) ||
				 atomic_read(&files->count) == 1);
```

此表达式以RCU安全的方式获取指针"fdt->fd[fd]"，并且如果配置了CONFIG_PROVE_RCU，则验证此表达式用于：

1. 在RCU读侧临界区内（隐式），或者
2. 持有files->file_lock的情况下，或者
3. 在未共享的files_struct上使用。
在情况(1)中，指针以RCU安全的方式被拾取，用于普通的RCU读侧临界区；在情况(2)中，`->file_lock`阻止任何更改的发生；最后，在情况(3)中，当前任务是唯一访问`file_struct`的任务，同样阻止任何更改的发生。如果上述语句仅从更新器代码中调用，则可以改写为如下形式：

```c
file = rcu_dereference_protected(fdt->fd[fd],
                                 lockdep_is_held(&files->file_lock) ||
                                 atomic_read(&files->count) == 1);
```

这将验证上述情况#2和#3，并且进一步地，除非满足这两个条件中的一个，否则lockdep会在RCU读侧临界区内使用时发出警告。因为`rcu_dereference_protected()`省略了所有屏障和编译器约束，所以它生成的代码比其他形式的`rcu_dereference()`更好。另一方面，如果RCU保护的指针或其指向的RCU保护的数据可以在并发中改变，则使用`rcu_dereference_protected()`是非法的。

与`rcu_dereference()`一样，当启用lockdep时，RCU列表和hlist遍历原语会检查是否在RCU读侧临界区内调用。然而，可以传递一个lockdep表达式作为额外的可选参数。在这种情况下，这些遍历原语只有在lockdep表达式为假并且它们从RCU读侧临界区外调用时才会发出警告。

例如，`workqueue`中的`for_each_pwq()`宏旨在在RCU读侧临界区内或持有`wq->mutex`的情况下使用。因此，其实现如下：

```c
#define for_each_pwq(pwq, wq) \
    list_for_each_entry_rcu((pwq), &(wq)->pwqs, pwqs_node, \
                             lock_is_held(&(wq->mutex).dep_map))
```
