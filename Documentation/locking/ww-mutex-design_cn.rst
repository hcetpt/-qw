======================================
伤口/等待 死锁预防互斥锁设计
======================================

请先阅读mutex-design.rst，因为它同样适用于等待/伤口互斥锁（WW-Mutexes）
WW-Mutexes 的动机
-------------------------

GPU 执行的操作通常涉及许多缓冲区。这些缓冲区可以在不同的上下文/进程之间共享，存在于不同的内存域中（例如 VRAM 与系统内存），等等。通过 PRIME/dmabuf，它们甚至可以在不同设备之间共享。因此，在某些情况下，驱动程序需要等待缓冲区变得可用。如果你考虑在缓冲区互斥锁上等待其变得可用，这会带来一个问题，即无法保证所有上下文中缓冲区在 execbuf/批处理中的出现顺序相同。这是因为用户空间直接控制这一点，并且是应用程序执行的一系列 GL 调用的结果。这可能导致死锁。当你考虑到内核可能需要在 GPU 操作缓冲区之前将其迁移到 VRAM 中时，问题变得更复杂，这反过来可能需要驱逐其他一些缓冲区（你不想驱逐那些已经排队到 GPU 的缓冲区）。但对于简化理解这个问题，你可以忽略这一点。

TTM 图形子系统为解决这个问题提出了一种非常简单的算法。对于每个需要锁定的缓冲区组（execbuf），调用者将从全局计数器分配一个唯一的预订 ID/票号。在锁定与 execbuf 相关的所有缓冲区时，如果发生死锁，则拥有最低预订票号（即最旧的任务）的那个将获胜，而拥有较高预订 ID（即较新的任务）的那个将解锁它已经锁定的所有缓冲区，然后再尝试一次。

在 RDBMS 文献中，预订票号与事务相关联，处理死锁的方法称为 Wait-Die。这个名字基于锁定线程遇到已锁定的互斥锁时的动作：

- 如果持有锁的事务较新，则锁定事务等待；
- 如果持有锁的事务较旧，则锁定事务回退并死亡。因此称为 Wait-Die。

还有一种名为 Wound-Wait 的算法：
- 如果持有锁的事务较新，锁定事务将“伤害”持有锁的事务，请求其死亡；
- 如果持有锁的事务较旧，它则等待另一个事务。因此称为 Wound-Wait。
两种算法都是公平的，因为事务最终都会成功。然而，与Wait-Die相比，Wound-Wait算法通常被认为会产生较少的回退，但另一方面，在从回退中恢复时，Wound-Wait涉及的工作量比Wait-Die更多。Wound-Wait还是一个抢占式算法，即事务可以被其他事务“打伤”，这需要一种可靠的方法来检测被打伤的状态并抢占正在运行的事务。需要注意的是，这与进程抢占不同。当一个Wound-Wait事务在受到伤害后返回-EDEADLK时，该事务被视为被抢占。

概念
----

与普通的互斥锁相比，Wound-Wait互斥锁的锁接口中出现了两个额外的概念/对象：

获取上下文：为了确保最终向前进展，重要的是尝试获取锁的任务不要获取新的预留ID，而是保持开始获取锁时所获得的那个ID。这个票据存储在获取上下文中。此外，获取上下文还跟踪调试状态以捕捉Wound-Wait互斥锁接口的滥用。获取上下文代表一个事务。
W/W类：与普通互斥锁不同，对于Wound-Wait互斥锁，锁类需要显式指定，因为需要初始化获取上下文。锁类还指定了使用哪种算法：Wound-Wait或Wait-Die。

此外，还有三类不同的Wound-Wait锁获取函数：

* 使用上下文进行正常的锁获取，使用ww_mutex_lock。
* 在争夺锁的任务刚刚释放所有已获取锁后，对争夺锁进行慢路径锁获取。这些函数带有_slow后缀。
从简单的语义角度来看，_slow函数不是严格必需的，因为在释放所有其他已获取锁之后，对争夺锁调用正常的ww_mutex_lock函数也会正确工作。毕竟，如果没有获取其他Wound-Wait互斥锁，则不存在死锁的潜在风险，因此ww_mutex_lock调用会阻塞而不会提前返回-EDEADLK。_slow函数的优势在于接口安全性：
  * ww_mutex_lock具有__must_check int返回类型，而ww_mutex_lock_slow具有void返回类型。请注意，由于Wound-Wait代码无论如何都需要循环/重试，因此__must_check不会导致虚假警告，即使第一次锁操作永远不会失败。
  * 当启用完整调试时，ww_mutex_lock_slow检查所有已获取的Wound-Wait互斥锁是否已被释放（防止死锁），并确保我们在争夺锁上阻塞（防止通过-EDEADLK慢路径旋转直到争夺锁可以被获取）。
* 只获取单个Wound-Wait互斥锁的函数，这产生了与普通互斥锁完全相同的语义。这是通过使用NULL上下文调用ww_mutex_lock实现的。
再次说明，这并不是严格要求的。但通常你只需要获取一个锁，在这种情况下设置获取上下文是没有意义的（因此最好避免获取死锁避免票）。
当然，所有处理由于信号导致唤醒的常用变体也都是提供的。

用法
-----

算法（Wait-Die vs Wound-Wait）的选择是通过使用 DEFINE_WW_CLASS()（Wound-Wait） 或 DEFINE_WD_CLASS()（Wait-Die）来实现的。
作为一个粗略的经验法则，如果预期同时竞争的事务数量通常较小，并且希望减少回滚的数量，则应使用 Wound-Wait。

在同一 w/w 类中获取锁有三种不同的方法。方法 #1 和 #2 的通用定义如下：

```c
static DEFINE_WW_CLASS(ww_class);

struct obj {
    struct ww_mutex lock;
    /* 对象数据 */
};

struct obj_entry {
    struct list_head head;
    struct obj *obj;
};
```

方法 1：使用不允许重新排序的 execbuf->buffers 列表。这在已经跟踪所需对象列表的情况下很有用。
此外，锁辅助函数可以将-EALREADY 返回码传播给调用者，作为某个对象在列表中重复出现的信号。这对于从用户空间输入构建的列表尤其有用，ABI 要求用户空间没有重复条目（例如，对于 GPU 命令缓冲区提交 ioctl）：

```c
int lock_objs(struct list_head *list, struct ww_acquire_ctx *ctx) {
    struct obj *res_obj = NULL;
    struct obj_entry *contended_entry = NULL;
    struct obj_entry *entry;

    ww_acquire_init(ctx, &ww_class);

  retry:
    list_for_each_entry (entry, list, head) {
        if (entry->obj == res_obj) {
            res_obj = NULL;
            continue;
        }
        ret = ww_mutex_lock(&entry->obj->lock, ctx);
        if (ret < 0) {
            contended_entry = entry;
            goto err;
        }
    }

    ww_acquire_done(ctx);
    return 0;

  err:
    list_for_each_entry_continue_reverse (entry, list, head)
        ww_mutex_unlock(&entry->obj->lock);

    if (res_obj)
        ww_mutex_unlock(&res_obj->lock);

    if (ret == -EDEADLK) {
        /* 我们在序列号竞争中失败了，加锁并重试 */
        ww_mutex_lock_slow(&contended_entry->obj->lock, ctx);
        res_obj = contended_entry->obj;
        goto retry;
    }
    ww_acquire_fini(ctx);

    return ret;
}
```

方法 2：使用可以重新排序的 execbuf->buffers 列表。与方法 1 相同的重复条目检测语义使用 -EALREADY 返回码。但是列表重新排序允许编写更符合习惯的代码：

```c
int lock_objs(struct list_head *list, struct ww_acquire_ctx *ctx) {
    struct obj_entry *entry, *entry2;

    ww_acquire_init(ctx, &ww_class);

    list_for_each_entry (entry, list, head) {
        ret = ww_mutex_lock(&entry->obj->lock, ctx);
        if (ret < 0) {
            entry2 = entry;

            list_for_each_entry_continue_reverse (entry2, list, head)
                ww_mutex_unlock(&entry2->obj->lock);

            if (ret != -EDEADLK) {
                ww_acquire_fini(ctx);
                return ret;
            }

            /* 我们在序列号竞争中失败了，加锁并重试 */
            ww_mutex_lock_slow(&entry->obj->lock, ctx);

            /*
             * 将 buf 移到列表头部，这会将 buf->next 指向第一个未锁定的条目，
             * 重启 for 循环
             */
            list_del(&entry->head);
            list_add(&entry->head, list);
        }
    }

    ww_acquire_done(ctx);
    return 0;
}
```

解锁对于方法 #1 和 #2 都是相同的：

```c
void unlock_objs(struct list_head *list, struct ww_acquire_ctx *ctx) {
    struct obj_entry *entry;

    list_for_each_entry (entry, list, head)
        ww_mutex_unlock(&entry->obj->lock);

    ww_acquire_fini(ctx);
}
```

方法 3 在对象列表是临时构建而不是预先构建的情况下非常有用，例如调整图中的边时，每个节点都有自己的 ww_mutex 锁，并且只有在持有所有相关节点的锁时才能更改边。w/w 互斥锁在这种情况下非常适合，原因如下：

- 它们可以以任意顺序获取锁，这使我们能够从一个起点开始遍历图，并迭代地发现新的边并锁定这些边连接的节点。
- 由于 -EALREADY 返回码表明已持有一个给定的对象，因此无需额外的记录来打破图中的循环或跟踪已持有的锁（当使用多个节点作为起点时）。
请注意，这种方法在两个重要方面与上述方法不同：

- 由于对象列表是动态构建的（并且在因 -EDEADLK 死锁条件重试时可能会有所不同），因此不需要在未锁定时将任何对象保留在持久列表上。因此，我们可以将 list_head 移到对象本身。
- 另一方面，动态对象列表构建也意味着 -EALREADY 返回码不能被传播。
请注意，方法#1和#2可以与方法#3结合使用，例如，首先使用上述方法之一锁定从用户空间传递的一组起始节点。然后使用下面的方法#3锁定受操作影响的任何其他对象。回退/重试过程会稍微复杂一些，因为当动态锁定步骤遇到-EDEADLK时，我们还需要解锁所有用固定列表获取的对象。但是w/w互斥锁调试检查将捕获这些情况下的任何接口误用。

另外，方法#3不能在锁获取步骤中失败，因为它不会返回-EALREADY。当然，在使用_interruptible变体的情况下会有所不同，但这超出了这些示例的范围：

```c
struct obj {
    struct ww_mutex ww_mutex;
    struct list_head locked_list;
};

static DEFINE_WW_CLASS(ww_class);

void __unlock_objs(struct list_head *list)
{
    struct obj *entry, *temp;

    list_for_each_entry_safe(entry, temp, list, locked_list) {
        /* 需要在解锁之前执行此操作，因为只有当前锁持有者才能使用对象 */
        list_del(&entry->locked_list);
        ww_mutex_unlock(entry->ww_mutex);
    }
}

void lock_objs(struct list_head *list, struct ww_acquire_ctx *ctx)
{
    struct obj *obj;

    ww_acquire_init(ctx, &ww_class);

retry:
    /* 重新初始化循环开始状态 */
    loop {
        /* 遍历图并决定锁定哪些对象的魔法代码 */

        ret = ww_mutex_lock(obj->ww_mutex, ctx);
        if (ret == -EALREADY) {
            /* 我们已经有了这个锁，继续下一个对象 */
            continue;
        }
        if (ret == -EDEADLK) {
            __unlock_objs(list);

            ww_mutex_lock_slow(obj, ctx);
            list_add(&entry->locked_list, list);
            goto retry;
        }

        /* 锁定了一个新对象，将其添加到列表中 */
        list_add_tail(&entry->locked_list, list);
    }

    ww_acquire_done(ctx);
    return 0;
}

void unlock_objs(struct list_head *list, struct ww_acquire_ctx *ctx)
{
    __unlock_objs(list);
    ww_acquire_fini(ctx);
}

方法4：只锁定单个对象。在这种情况下，死锁检测和预防显然是多余的，因为仅获取一个锁是不可能在一个类内产生死锁的。为了简化这种情况，可以使用NULL上下文的w/w互斥锁API。

实现细节
-------------

设计：
^^^^^^^

`ww_mutex`目前封装了一个`struct mutex`，这意味着对于普通的互斥锁没有额外开销，因为普通的互斥锁更为常见。因此，如果未使用等待/回滚互斥锁，则代码大小只会略有增加。
我们为等待队列维护以下不变性：

1. 具有获取上下文的等待者按戳记顺序排序；没有获取上下文的等待者以FIFO顺序交错。
2. 对于Wait-Die，具有上下文的等待者中只有第一个可能已经获取了其他锁（ctx->acquired > 0）。请注意，这个等待者可能位于列表中没有上下文的其他等待者之后。
Wound-Wait抢占是通过懒惰抢占方案实现的：仅在存在新的锁竞争并且有可能发生死锁的情况下才检查事务的受伤状态。在这种情况下，如果事务受伤，它会后退，清除受伤状态并重试。这样实现抢占的一个好处是受伤的事务可以在重启事务前识别出需要等待的竞争锁。仅仅盲目地重启事务很可能会使事务再次陷入需要后退的情况。
通常情况下，并不期望出现太多竞争。这些锁通常用于设备资源的序列化访问，因此优化的重点应放在无竞争的情况下。
锁依赖：
^^^^^^^^

已特别注意尽可能警告API滥用的所有情况。某些常见的API滥用会在CONFIG_DEBUG_MUTEXES下被捕捉到，但推荐使用CONFIG_PROVE_LOCKING。
将发出警告的一些错误包括：
- 忘记调用`ww_acquire_fini`或`ww_acquire_init`
- 在`ww_acquire_done`之后尝试锁定更多互斥锁
```
尝试在-EDEADLK之后锁定错误的互斥锁，并解锁所有互斥锁  
尝试在-EDEADLK之后、解锁所有互斥锁之前锁定正确的互斥锁  
在返回-EDEADLK之前调用ww_mutex_lock_slow  
使用错误的解锁函数解锁互斥锁  
在同一上下文中两次调用ww_acquire_*中的一个函数  
为互斥锁使用与ww_acquire_ctx不同的ww_class  
可能导致死锁的常规锁依赖错误  
一些可能导致死锁的锁依赖错误：
   - 在未对第一个ww_acquire_ctx调用ww_acquire_fini之前，调用ww_acquire_init初始化第二个ww_acquire_ctx  
- 可能发生的‘常规’死锁

FIXME：
  一旦我们实现了TASK_DEADLOCK任务状态标志魔法，更新此部分
当然，请提供您需要翻译的文本。
