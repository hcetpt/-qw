使用RCU保护读多写少的链表
=============================================

RCU最常见的用途之一是保护读多写少的链表（在list.h中的`struct list_head`）。这种方法的一个主要优势是所需的所有内存排序都由链表宏提供。本文档描述了几个基于链表的RCU用例。

当持有rcu_read_lock()迭代链表时，写入者可以修改该链表。读者可以保证看到在获取rcu_read_lock()之前添加到链表中并在释放rcu_read_unlock()时仍在链表中的所有元素。对于在此期间添加或移除的元素，读者可能会看到也可能不会看到。如果写入者调用了list_replace_rcu()，读者可能看到旧元素或新元素；他们不会同时看到两者，也不会一个也看不到。

示例1：读多写少的链表：延迟销毁
-------------------------------------------------

内核中广泛使用的RCU链表用例是对系统中所有进程进行无锁迭代。“task_struct::tasks”表示链接所有进程的链表节点。可以在任何链表添加或移除的同时并行遍历此列表。

遍历链表使用的是`for_each_process()`，它由以下两个宏定义：

```c
#define next_task(p) \
    list_entry_rcu((p)->tasks.next, struct task_struct, tasks)

#define for_each_process(p) \
    for (p = &init_task ; (p = next_task(p)) != &init_task ; )
```

遍历所有进程列表的代码通常如下：

```c
rcu_read_lock();
for_each_process(p) {
    /* 对p执行某些操作 */
}
rcu_read_unlock();
```

从任务列表中移除进程的简化且高度内联的代码如下：

```c
void release_task(struct task_struct *p)
{
    write_lock(&tasklist_lock);
    list_del_rcu(&p->tasks);
    write_unlock(&tasklist_lock);
    call_rcu(&p->rcu, delayed_put_task_struct);
}
```

当进程退出时，`release_task()`通过`__exit_signal()`和`__unhash_process()`在`tasklist_lock`写入锁保护下调用`list_del_rcu(&p->tasks)`。`list_del_rcu()`调用将任务从所有任务列表中移除。`tasklist_lock`防止并发的链表添加/移除导致链表损坏。使用`for_each_process()`的读者不受`tasklist_lock`保护。为了防止读者注意到链表指针的变化，在一个或多个优雅周期后通过`call_rcu()`调用`delayed_put_task_struct()`来延迟释放`task_struct`对象。这种延迟销毁确保任何遍历链表的读者都会看到有效的`p->tasks.next`指针，并且删除/释放可以在遍历链表的同时进行。

这种模式也称为**存在锁**，因为RCU会等到所有现有读者完成后再调用`delayed_put_task_struct()`回调函数，从而保证正在讨论的`task_struct`对象在所有可能引用该对象的RCU读者完成之前一直存在。

示例2：读取侧操作在解锁后执行：没有就地更新
----------------------------------------------------------------------

一些读写锁用例在持有读取侧锁时计算一个值，但在释放该锁后继续使用该值。这些用例通常是转换为RCU的好候选者。一个突出的例子涉及网络数据包路由。

由于数据包路由数据跟踪计算机外部设备的状态，因此有时会包含陈旧的数据。因此，一旦计算出路由路径，就没有必要在整个传输过程中保持路由表静态不变。毕竟，你可以随意保持路由表静态不变，但这并不能阻止外部互联网发生变化，真正重要的是外部互联网的状态。此外，路由条目通常是添加或删除的，而不是就地修改的。这是一个罕见的例子，光速有限和原子非零大小实际上有助于减轻同步负担。

一个简单的RCU用例例子可以在系统调用审计支持中找到。例如，一个读写锁实现的`audit_filter_task()`函数可能是这样的：

```c
static enum audit_state audit_filter_task(struct task_struct *tsk, char **key)
{
    struct audit_entry *e;
    enum audit_state   state;

    read_lock(&auditsc_lock);
    /* 注意：audit_filter_mutex 由调用者持有。 */
    list_for_each_entry(e, &audit_tsklist, list) {
        if (audit_filter_rules(tsk, &e->rule, NULL, &state)) {
            if (state == AUDIT_STATE_RECORD)
                *key = kstrdup(e->rule.filterkey, GFP_ATOMIC);
            read_unlock(&auditsc_lock);
            return state;
        }
    }
    read_unlock(&auditsc_lock);
    return AUDIT_BUILD_CONTEXT;
}
```

这里在锁保护下搜索列表，但在返回相应值之前释放锁。当对这个值采取行动时，列表可能已经被修改。这合乎逻辑，因为在关闭审计时，多审计几个系统调用是可以接受的。
这意味着RCU可以很容易地应用于读取侧，如下所示：

```c
static enum audit_state audit_filter_task(struct task_struct *tsk, char **key)
{
    struct audit_entry *e;
    enum audit_state   state;

    rcu_read_lock();
    /* 注意：audit_filter_mutex 由调用者持有。 */
    list_for_each_entry_rcu(e, &audit_tsklist, list) {
        if (audit_filter_rules(tsk, &e->rule, NULL, &state)) {
            if (state == AUDIT_STATE_RECORD)
                *key = kstrdup(e->rule.filterkey, GFP_ATOMIC);
            rcu_read_unlock();
            return state;
        }
    }
    rcu_read_unlock();
    return AUDIT_BUILD_CONTEXT;
}
```

`read_lock()` 和 `read_unlock()` 调用分别被替换为 `rcu_read_lock()` 和 `rcu_read_unlock()`，`list_for_each_entry()` 被替换为 `list_for_each_entry_rcu()`。`*_rcu()` 列表遍历原语添加了 `READ_ONCE()` 和诊断检查，以防止在RCU读取侧临界区外的不正确使用。

对更新侧的更改也是直接的。一个读写锁可能像下面这样用于简化版本的 `audit_del_rule()` 和 `audit_add_rule()` 中的删除和插入：

```c
static inline int audit_del_rule(struct audit_rule *rule, struct list_head *list)
{
    struct audit_entry *e;

    write_lock(&auditsc_lock);
    list_for_each_entry(e, list, list) {
        if (!audit_compare_rule(rule, &e->rule)) {
            list_del(&e->list);
            write_unlock(&auditsc_lock);
            return 0;
        }
    }
    write_unlock(&auditsc_lock);
    return -EFAULT;      /* 没有匹配规则 */
}

static inline int audit_add_rule(struct audit_entry *entry, struct list_head *list)
{
    write_lock(&auditsc_lock);
    if (entry->rule.flags & AUDIT_PREPEND) {
        entry->rule.flags &= ~AUDIT_PREPEND;
        list_add(&entry->list, list);
    } else {
        list_add_tail(&entry->list, list);
    }
    write_unlock(&auditsc_lock);
    return 0;
}
```

以下是这两个函数的RCU等价版本：

```c
static inline int audit_del_rule(struct audit_rule *rule, struct list_head *list)
{
    struct audit_entry *e;

    /* 由于这是唯一的删除例程，因此这里不需要使用 _rcu 迭代器。 */
    list_for_each_entry(e, list, list) {
        if (!audit_compare_rule(rule, &e->rule)) {
            list_del_rcu(&e->list);
            call_rcu(&e->rcu, audit_free_rule);
            return 0;
        }
    }
    return -EFAULT;      /* 没有匹配规则 */
}

static inline int audit_add_rule(struct audit_entry *entry, struct list_head *list)
{
    if (entry->rule.flags & AUDIT_PREPEND) {
        entry->rule.flags &= ~AUDIT_PREPEND;
        list_add_rcu(&entry->list, list);
    } else {
        list_add_tail_rcu(&entry->list, list);
    }
    return 0;
}
```

通常情况下，`write_lock()` 和 `write_unlock()` 将被 `spin_lock()` 和 `spin_unlock()` 替换。但在这种情况下，所有调用者都持有 `audit_filter_mutex`，因此不需要额外的锁定。因此可以消除 `auditsc_lock`，因为使用RCU消除了写入者排除读者的需求。

`list_del()`、`list_add()` 和 `list_add_tail()` 原语被替换为 `list_del_rcu()`、`list_add_rcu()` 和 `list_add_tail_rcu()`。

`*_rcu()` 列表操作原语添加了弱序CPU所需的内存屏障。`list_del_rcu()` 原语省略了会导致并发读者失败的指针毒化调试辅助代码。

因此，当读者能够容忍陈旧数据，并且条目要么添加要么删除（没有就地修改）时，使用RCU变得非常容易！

### 示例3：处理就地更新

系统调用审计代码不会就地更新审计规则。但是，如果这样做的话，使用读写锁的代码可能会如下所示（假设只更新 `field_count`，否则需要填充新增字段）：

```c
static inline int audit_upd_rule(struct audit_rule *rule, struct list_head *list, __u32 newaction, __u32 newfield_count)
{
    struct audit_entry *e;
    struct audit_entry *ne;

    write_lock(&auditsc_lock);
    /* 注意：audit_filter_mutex 由调用者持有。 */
    list_for_each_entry(e, list, list) {
        if (!audit_compare_rule(rule, &e->rule)) {
            e->rule.action = newaction;
            e->rule.field_count = newfield_count;
            write_unlock(&auditsc_lock);
            return 0;
        }
    }
    write_unlock(&auditsc_lock);
    return -EFAULT;      /* 没有匹配规则 */
}
```

RCU版本创建一个副本，更新该副本，然后用新更新的条目替换旧条目。这种允许在制作副本进行更新的同时允许并发读取的操作序列正是RCU（读-复制-更新）得名的原因。

RCU版本的 `audit_upd_rule()` 如下所示：

```c
static inline int audit_upd_rule(struct audit_rule *rule, struct list_head *list, __u32 newaction, __u32 newfield_count)
{
    struct audit_entry *e;
    struct audit_entry *ne;

    list_for_each_entry(e, list, list) {
        if (!audit_compare_rule(rule, &e->rule)) {
            ne = kmalloc(sizeof(*entry), GFP_ATOMIC);
            if (ne == NULL)
                return -ENOMEM;
            audit_copy_rule(&ne->rule, &e->rule);
            ne->rule.action = newaction;
            ne->rule.field_count = newfield_count;
            list_replace_rcu(&e->list, &ne->list);
            call_rcu(&e->rcu, audit_free_rule);
            return 0;
        }
    }
    return -EFAULT;      /* 没有匹配规则 */
}
```

这同样假定调用者持有 `audit_filter_mutex`。通常情况下，写锁将变为自旋锁。

`update_lsm_rule()` 也做了类似的事情，对于那些希望查看实际Linux内核代码的人来说。

在 `openswitch` 驱动中的 *连接跟踪表* 代码中也可以找到这种模式的应用，例如在 `ct_limit_set()` 中。该表持有连接跟踪条目，并且有一个最大条目的限制。每个区域都有一个这样的表，因此每个区域有一个 *限制*。这些区域通过哈希表映射到它们的限制，哈希链使用RCU管理的hlist。当设置一个新的限制时，分配一个新的限制对象，并调用 `ct_limit_set()` 使用 `list_replace_rcu()` 替换旧的限制对象。然后在宽限期后使用 `kfree_rcu()` 释放旧的限制对象。

### 示例4：消除陈旧数据

上述审计示例容忍陈旧数据，大多数跟踪外部状态的算法也是如此。毕竟，从外部状态变化到Linux意识到这个变化之间存在延迟，因此如前所述，少量额外的RCU引起的陈旧性通常不是问题。
然而，在许多情况下，陈旧数据是无法容忍的。Linux 内核中的一个例子是 System V IPC（参见 ipc/shm.c 中的 shm_lock() 函数）。这段代码在每个条目的自旋锁下检查一个 *deleted* 标志，并且如果该标志被设置，则假装该条目不存在。为了使这种技术有用，搜索函数必须在返回时持有每个条目的自旋锁，正如 shm_lock() 实际上所做的那样。

快速测验：
为了使删除标志技术有用，为什么在从搜索函数返回时需要持有每个条目的锁？

:ref:`快速测验答案 <quick_quiz_answer>`

如果系统调用审计模块将来需要拒绝陈旧数据，一种实现方法是在 `audit_entry` 结构中添加一个 `deleted` 标志和一个 `lock` 自旋锁，并修改 `audit_filter_task()` 如下：

```c
static enum audit_state audit_filter_task(struct task_struct *tsk)
{
    struct audit_entry *e;
    enum audit_state state;

    rcu_read_lock();
    list_for_each_entry_rcu(e, &audit_tsklist, list) {
        if (audit_filter_rules(tsk, &e->rule, NULL, &state)) {
            spin_lock(&e->lock);
            if (e->deleted) {
                spin_unlock(&e->lock);
                rcu_read_unlock();
                return AUDIT_BUILD_CONTEXT;
            }
            rcu_read_unlock();
            if (state == AUDIT_STATE_RECORD)
                *key = kstrdup(e->rule.filterkey, GFP_ATOMIC);
            return state;
        }
    }
    rcu_read_unlock();
    return AUDIT_BUILD_CONTEXT;
}
```

`audit_del_rule()` 函数需要在自旋锁下设置 `deleted` 标志如下：

```c
static inline int audit_del_rule(struct audit_rule *rule, struct list_head *list)
{
    struct audit_entry *e;

    /* 无需使用 _rcu 迭代器，因为这是唯一的删除例程。 */
    list_for_each_entry(e, list, list) {
        if (!audit_compare_rule(rule, &e->rule)) {
            spin_lock(&e->lock);
            list_del_rcu(&e->list);
            e->deleted = 1;
            spin_unlock(&e->lock);
            call_rcu(&e->rcu, audit_free_rule);
            return 0;
        }
    }
    return -EFAULT;  /* 没有匹配规则 */
}
```

这也假设调用者持有 `audit_filter_mutex`。请注意，这个示例假设条目仅添加和删除。还需要额外的机制来正确处理 `audit_upd_rule()` 执行的就地更新。例如，`audit_upd_rule()` 需要在执行 `list_replace_rcu()` 时同时持有旧 `audit_entry` 和其替换项的锁。

示例 5：跳过陈旧对象
----------------------

对于某些用例，通过在读取时跳过陈旧对象可以提高读者性能，其中陈旧对象是指那些将在一个或多个宽限期后被移除和销毁的对象。一个这样的例子可以在 timerfd 子系统中找到。当 `CLOCK_REALTIME` 时钟被重新编程（例如由于设置了系统时间）时，所有依赖于该时钟的已编程 `timerfds` 都会被触发，并且等待它们的过程会提前唤醒。为此，所有这些定时器在 `timerfd_setup_cancel()` 中被添加到 RCU 管理的 `cancel_list` 中：

```c
static void timerfd_setup_cancel(struct timerfd_ctx *ctx, int flags)
{
    spin_lock(&ctx->cancel_lock);
    if ((ctx->clockid == CLOCK_REALTIME || ctx->clockid == CLOCK_REALTIME_ALARM) &&
        (flags & TFD_TIMER_ABSTIME) && (flags & TFD_TIMER_CANCEL_ON_SET)) {
        if (!ctx->might_cancel) {
            ctx->might_cancel = true;
            spin_lock(&cancel_lock);
            list_add_rcu(&ctx->clist, &cancel_list);
            spin_unlock(&cancel_lock);
        }
    } else {
        __timerfd_remove_cancel(ctx);
    }
    spin_unlock(&ctx->cancel_lock);
}
```

当 `timerfd` 被释放（文件描述符关闭）时，`timerfd` 对象的 `might_cancel` 标志将被清除，对象从 `cancel_list` 中移除并销毁，如简化后的 `timerfd_release()` 版本所示：

```c
int timerfd_release(struct inode *inode, struct file *file)
{
    struct timerfd_ctx *ctx = file->private_data;

    spin_lock(&ctx->cancel_lock);
    if (ctx->might_cancel) {
        ctx->might_cancel = false;
        spin_lock(&cancel_lock);
        list_del_rcu(&ctx->clist);
        spin_unlock(&cancel_lock);
    }
    spin_unlock(&ctx->cancel_lock);

    if (isalarm(ctx))
        alarm_cancel(&ctx->t.alarm);
    else
        hrtimer_cancel(&ctx->t.tmr);
    kfree_rcu(ctx, rcu);
    return 0;
}
```

如果 `CLOCK_REALTIME` 时钟被设置（例如由时间服务器设置），则 hrtimer 框架会调用 `timerfd_clock_was_set()`，遍历 `cancel_list` 并唤醒等待 `timerfd` 的进程。在迭代 `cancel_list` 时，会检查 `might_cancel` 标志以跳过陈旧对象：

```c
void timerfd_clock_was_set(void)
{
    ktime_t moffs = ktime_mono_to_real(0);
    struct timerfd_ctx *ctx;
    unsigned long flags;

    rcu_read_lock();
    list_for_each_entry_rcu(ctx, &cancel_list, clist) {
        if (!ctx->might_cancel)
            continue;
        spin_lock_irqsave(&ctx->wqh.lock, flags);
        if (ctx->moffs != moffs) {
            ctx->moffs = KTIME_MAX;
            ctx->ticks++;
            wake_up_locked_poll(&ctx->wqh, EPOLLIN);
        }
        spin_unlock_irqrestore(&ctx->wqh.lock, flags);
    }
    rcu_read_unlock();
}
```

关键点在于，因为 RCU 保护的 `cancel_list` 遍历与对象添加和移除并发进行，有时遍历可能会访问已被从列表中移除的对象。在这个示例中，使用一个标志来跳过这些对象。

总结
----

可以容忍陈旧数据的以读为主的基于列表的数据结构最适合使用 RCU。最简单的情况是条目要么添加要么从数据结构中删除（或就地原子修改），但非原子的就地修改可以通过复制、更新副本然后用副本替换原始项来处理。如果不能容忍陈旧数据，则可以使用 *deleted* 标志结合每个条目的自旋锁，以便让搜索函数拒绝新删除的数据。

:ref:`快速测验答案 <quick_quiz_answer>`

为了使删除标志技术有用，为什么在从搜索函数返回时需要持有每个条目的锁？

如果搜索函数在返回前释放了每个条目的锁，那么调用者无论如何都会处理陈旧数据。如果处理陈旧数据真的没问题，那么就不需要 *deleted* 标志。如果处理陈旧数据确实是一个问题，那么你需要在整个使用返回值的代码中持有每个条目的锁。

:ref:`回到快速测验 <quick_quiz>`
