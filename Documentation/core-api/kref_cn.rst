为内核对象添加引用计数器（krefs）
=====================================

:作者: Corey Minyard <minyard@acm.org>
:作者: Thomas Hellstrom <thellstrom@vmware.com>

很多内容是从Greg Kroah-Hartman在2004年的OLS论文和关于krefs的演讲中摘录的，这些资料可以在以下链接找到：

  - http://www.kroah.com/linux/talks/ols_2004_kref_paper/Reprint-Kroah-Hartman-OLS2004.pdf
  - http://www.kroah.com/linux/talks/ols_2004_kref_talk/

简介
====

krefs允许您为对象添加引用计数器。如果您有被多处使用并传递的对象，并且没有引用计数器，那么您的代码几乎肯定是存在问题的。如果您需要引用计数器，krefs是首选方式。
要使用一个kref，可以在数据结构中像下面这样添加它：

```c
    struct my_data
    {
        struct kref refcount;
    };
```

kref可以在数据结构中的任何位置出现。
初始化
========

在分配内存后必须初始化kref。为此，请按如下方式调用`kref_init`：

```c
    struct my_data *data;

    data = kmalloc(sizeof(*data), GFP_KERNEL);
    if (!data)
        return -ENOMEM;
    kref_init(&data->refcount);
```

这将kref中的引用计数设置为1。
kref规则
========

一旦您有了初始化的kref，就必须遵循以下规则：

1) 如果您创建了一个非临时性的指针副本，特别是如果该副本可以传递给另一个执行线程，则必须在传递之前使用`kref_get()`递增引用计数：

```c
    kref_get(&data->refcount);
```

如果您已经有一个指向kref化的结构的有效指针（引用计数不能减至零），则可以在不加锁的情况下这样做。
2) 当您不再需要一个指针时，必须调用`kref_put()`：

```c
    kref_put(&data->refcount, data_release);
```

如果这是指向该指针的最后一个引用，则会调用释放例程。如果代码从未试图在未持有有效指针的情况下获取kref化结构的有效指针，则可以在不加锁的情况下安全地进行此操作。
3) 如果代码试图在未持有有效指针的情况下获取对kref化结构的引用，则必须确保在`kref_get()`期间无法发生`kref_put()`，并且该结构在此期间必须保持有效。
这段代码和描述主要展示了如何使用`kref`机制来管理数据引用计数，特别是在多线程环境下。下面是该段落的中文翻译：

例如，如果你分配了一些数据并将其传递给另一个线程进行处理：

```c
void data_release(struct kref *ref)
{
    struct my_data *data = container_of(ref, struct my_data, refcount);
    kfree(data);
}

void more_data_handling(void *cb_data)
{
    struct my_data *data = cb_data;
    // 在这里对 data 进行操作
    kref_put(&data->refcount, data_release);
}

int my_data_handler(void)
{
    int rv = 0;
    struct my_data *data;
    struct task_struct *task;
    data = kmalloc(sizeof(*data), GFP_KERNEL);
    if (!data)
        return -ENOMEM;
    kref_init(&data->refcount);

    kref_get(&data->refcount);
    task = kthread_run(more_data_handling, data, "more_data_handling");
    if (task == ERR_PTR(-ENOMEM)) {
        rv = -ENOMEM;
        kref_put(&data->refcount, data_release);
        goto out;
    }
    // 在这里对 data 进行操作
out:
    kref_put(&data->refcount, data_release);
    return rv;
}
```

这样无论两个线程处理数据的顺序如何，`kref_put()` 都能正确判断何时数据不再被引用，并释放它。`kref_get()` 不需要加锁，因为我们已经拥有了一个有效的指针并且持有其引用计数。`kref_put()` 也不需要加锁，因为没有其他地方试图在不持有指针的情况下获取数据。
在上面的例子中，无论成功还是失败路径下 `kref_put()` 都会被调用两次。这是必要的，因为引用计数在 `kref_init()` 和 `kref_get()` 中分别增加了一次。

注意规则1中的“之前”是非常重要的。你不应该做如下操作：

```c
task = kthread_run(more_data_handling, data, "more_data_handling");
if (task == ERR_PTR(-ENOMEM)) {
    rv = -ENOMEM;
    goto out;
} else
    /* 错误错误错误 - 获取是在传递后 */
    kref_get(&data->refcount);
```

不要假设你知道自己在做什么并使用上述结构。首先，你可能真的不知道自己在做什么。其次，即使你知道自己在做什么（有些情况下涉及锁定时，上述操作可能是合法的），其他人可能不懂，会修改或复制你的代码。这是一种不好的编程风格，不应该这样做。

有些情况下可以优化获取和释放操作。例如，如果你完成了一个对象的操作并将其加入队列或传递给其他地方，没有必要先获取再释放：

```c
// 多余的获取和释放
kref_get(&obj->ref);
enqueue(obj);
kref_put(&obj->ref, obj_cleanup);
```

只需要执行入队操作即可。在这里加上注释是有帮助的：

```c
enqueue(obj);
// 我们完成了对 obj 的操作，因此我们将引用计数交给队列。之后不要再触碰 obj!
```

最后一个规则（规则3）是最难处理的。例如，如果你有一个由多个使用`kref`管理的对象组成的列表，并且你想获取第一个对象。你不能简单地从列表中取出第一个对象并调用 `kref_get()`。这违反了规则3，因为你此时并不持有有效的指针。你需要添加一个互斥锁（或其他类型的锁）。
例如：

```c
// 定义一个互斥锁
static DEFINE_MUTEX(mutex);
// 初始化链表头
static LIST_HEAD(q);
struct my_data // 结构体定义
{
    struct kref refcount; // 引用计数
    struct list_head link; // 链表节点
};

// 获取一个条目
static struct my_data *get_entry()
{
    struct my_data *entry = NULL;
    mutex_lock(&mutex); // 加锁
    if (!list_empty(&q)) // 如果链表不为空
    {
        entry = container_of(q.next, struct my_data, link); // 获取第一个元素
        kref_get(&entry->refcount); // 增加引用计数
    }
    mutex_unlock(&mutex); // 解锁
    return entry;
}

// 释放条目
static void release_entry(struct kref *ref)
{
    struct my_data *entry = container_of(ref, struct my_data, refcount); // 获取my_data结构体指针

    list_del(&entry->link); // 从链表中删除该条目
    kfree(entry); // 释放内存
}

// 减少引用计数并可能释放条目
static void put_entry(struct my_data *entry)
{
    mutex_lock(&mutex); // 加锁
    kref_put(&entry->refcount, release_entry); // 减少引用计数，如果引用计数为0，则调用release_entry释放内存
    mutex_unlock(&mutex); // 解锁
}

// 如果你不希望在整个释放操作期间持有锁，那么kref_put()的返回值是有用的。
// 比如说，在上面的例子中，你不想在持有锁的情况下调用kfree()（因为这样做有点多余）。
// 你可以如下使用kref_put()：

static void release_entry(struct kref *ref)
{
    /* 所有的工作都在kref_put()返回后完成。 */
}

static void put_entry(struct my_data *entry)
{
    mutex_lock(&mutex); // 加锁
    if (kref_put(&entry->refcount, release_entry)) // 减少引用计数
    {
        list_del(&entry->link); // 从链表中删除该条目
        mutex_unlock(&mutex); // 解锁
        kfree(entry); // 释放内存
    }
    else
        mutex_unlock(&mutex); // 解锁
}

// 这种方式在你需要作为释放操作的一部分调用其他可能耗时较长或可能请求相同锁的函数时更为有用。
// 注意，将所有工作放在release例程中仍然是更整洁的选择。
// 上面的例子还可以通过使用kref_get_unless_zero()进行优化：

static struct my_data *get_entry()
{
    struct my_data *entry = NULL;
    mutex_lock(&mutex); // 加锁
    if (!list_empty(&q)) // 如果链表不为空
    {
        entry = container_of(q.next, struct my_data, link); // 获取第一个元素
        if (!kref_get_unless_zero(&entry->refcount)) // 增加引用计数，如果已经是0则返回false
            entry = NULL;
    }
    mutex_unlock(&mutex); // 解锁
    return entry;
}

static void release_entry(struct kref *ref)
{
    struct my_data *entry = container_of(ref, struct my_data, refcount); // 获取my_data结构体指针

    mutex_lock(&mutex); // 加锁
    list_del(&entry->link); // 从链表中删除该条目
    mutex_unlock(&mutex); // 解锁
    kfree(entry); // 释放内存
}

static void put_entry(struct my_data *entry)
{
    kref_put(&entry->refcount, release_entry); // 减少引用计数
}

// 在put_entry()中移除对kref_put()周围的mutex_lock()是有用的，
// 但重要的是kref_get_unless_zero()必须包含在同一关键段内，
// 该关键段用于查找表中的条目，否则kref_get_unless_zero()可能会引用已经释放的内存。

// 注意，不检查kref_get_unless_zero()的返回值是非法的。
// 如果你确定（已经有有效的指针）kref_get_unless_zero()将返回true，则使用kref_get()代替。

// Krefs和RCU

// 函数kref_get_unless_zero也使得可以在上述例子中使用RCU锁进行查找：

struct my_data
{
    struct rcu_head rhead; // RCU头部
    struct kref refcount; // 引用计数
};

static struct my_data *get_entry_rcu()
{
    struct my_data *entry = NULL;
    rcu_read_lock(); // 开始RCU读取锁
    if (!list_empty(&q)) // 如果链表不为空
    {
        entry = container_of(q.next, struct my_data, link); // 获取第一个元素
        if (!kref_get_unless_zero(&entry->refcount)) // 增加引用计数，如果已经是0则返回false
            entry = NULL;
    }
    rcu_read_unlock(); // 结束RCU读取锁
    return entry;
}

static void release_entry_rcu(struct kref *ref)
{
    struct my_data *entry = container_of(ref, struct my_data, refcount); // 获取my_data结构体指针

    mutex_lock(&mutex); // 加锁
    list_del_rcu(&entry->link); // 使用RCU从链表中删除该条目
    mutex_unlock(&mutex); // 解锁
    kfree_rcu(entry, rhead); // 释放内存
}

static void put_entry(struct my_data *entry)
{
    kref_put(&entry->refcount, release_entry_rcu); // 减少引用计数
}

// 请注意，在调用release_entry_rcu之后，struct kref成员需要在有效内存中保留足够长的时间以覆盖一个RCU宽限期。
// 可以通过使用kfree_rcu(entry, rhead)来实现这一点，如上所示，或者在使用kfree之前调用synchronize_rcu()，
// 但请注意，synchronize_rcu()可能会休眠相当长的一段时间。
```
以上是对提供的代码段进行了中文翻译。
