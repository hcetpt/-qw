.. _whatisrcu_doc:

什么是RCU？ -- “读、复制、更新”
======================================

请注意，“什么是RCU？”系列文章是开始学习RCU的一个极佳起点：

| 1. RCU的基本概念：https://lwn.net/Articles/262464/
| 2. RCU是什么？第二部分：使用方法：https://lwn.net/Articles/263130/
| 3. RCU第三部分：RCU API：https://lwn.net/Articles/264090/
| 4. RCU API，2010年版：https://lwn.net/Articles/418853/
| 2010年的大API表格：https://lwn.net/Articles/419086/
| 5. RCU API，2014年版：https://lwn.net/Articles/609904/
| 2014年的大API表格：https://lwn.net/Articles/609973/
| 6. RCU API，2019年版：https://lwn.net/Articles/777036/
| 2019年的大API表格：https://lwn.net/Articles/777165/

对于偏好视频的读者：

| 1. 解开RCU的神秘面纱：基础篇：https://www.linuxfoundation.org/webinars/unraveling-rcu-usage-mysteries
| 2. 解开RCU的神秘面纱：更多用例：https://www.linuxfoundation.org/webinars/unraveling-rcu-usage-mysteries-additional-use-cases

什么是RCU？

RCU（Read-Copy-Update）是一种同步机制，在Linux内核2.5开发期间引入，旨在优化读多写少的情况。尽管RCU实际上非常简单，但要有效利用它需要你以不同的方式思考代码。另一个问题是错误地认为存在一种“正确的方法”来描述和使用RCU。相反，经验表明，不同的人必须根据自己的经验和使用场景采取不同的路径来理解RCU。本文档提供了几种不同的路径，如下所示：

:ref:`1. RCU概览 <1_whatisRCU>`

:ref:`2. RCU的核心API是什么？<2_whatisRCU>`

:ref:`3. 核心RCU API的一些示例用途 <3_whatisRCU>`

:ref:`4. 如果我的更新线程不能阻塞怎么办？<4_whatisRCU>`

:ref:`5. RCU的一些简单实现 <5_whatisRCU>`

:ref:`6. 与读写锁的类比 <6_whatisRCU>`

:ref:`7. 与引用计数的类比 <7_whatisRCU>`

:ref:`8. 完整的RCU API列表 <8_whatisRCU>`

:ref:`9. 快速测验的答案 <9_whatisRCU>`

偏好从概念概述开始的人应该关注第1节，虽然大多数读者在某个时刻都会从中受益。偏好从API开始的人应该关注第2节。偏好从示例用法开始的人应该关注第3和4节。需要理解RCU实现的人应该关注第5节，然后深入研究内核源代码。偏好通过类比进行推理的人应该关注第6和7节。第8节作为docbook API文档的索引，第9节是传统的答案键。因此，请从对你最有意义的部分开始，并根据你的学习偏好进行选择。如果你需要了解所有内容，可以阅读全文——但如果你真的是那种人，你已经浏览过源代码，因此根本不需要这份文档。;)

.. _1_whatisRCU:

1. RCU概览
------------

RCU的基本思想是将更新分为“移除”和“回收”两个阶段。移除阶段会从数据结构中移除对数据项的引用（可能通过替换为新版本的数据项），并且可以在读取者并行运行时执行。之所以能够在读取者并行运行时安全地执行移除阶段，是因为现代CPU的语义保证了读取者要么看到旧版本的数据结构，要么看到新版本的数据结构，而不是部分更新的引用。回收阶段负责回收（例如释放）在移除阶段从数据结构中移除的数据项。由于回收数据项可能会中断任何同时引用这些数据项的读取者，因此回收阶段必须等到读取者不再持有这些数据项的引用后才能开始。将更新分为移除和回收两个阶段允许更新者立即执行移除阶段，并延迟回收阶段直到所有在移除阶段活跃的读取者完成，这可以通过阻塞直到它们完成或注册一个回调函数在它们完成后被调用来实现。只需要考虑在移除阶段活跃的读取者，因为任何在移除阶段之后开始的读取者将无法获得已移除数据项的引用，因此不会受到回收阶段的影响。

因此，典型的RCU更新序列大致如下：

a. 移除指向数据结构的指针，以便后续的读取者无法获得其引用。
b. 等待所有之前的读取者完成它们的RCU读侧临界区。
c. 此时不会有任何读取者持有该数据结构的引用，因此现在可以安全地回收（例如，使用kfree()）。

步骤(b)是RCU延迟销毁的关键思想。能够等待所有读取者完成的能力使得RCU读取者可以使用更轻量级的同步机制，在某些情况下甚至完全不需要同步。相比之下，在更传统的基于锁的方案中，读取者必须使用重量级的同步机制来防止更新者在他们下面删除数据结构。这是因为基于锁的更新者通常会在原地更新数据项，并且必须排除读取者。相比之下，RCU更新者通常利用现代CPU上对单个对齐指针的写入操作是原子的事实，允许在不干扰读取者的情况下原子插入、移除和替换链式结构中的数据项。并发的RCU读取者可以继续访问旧版本，并且可以避免原子操作、内存屏障和通信缓存未命中等在当今SMP计算机系统中非常昂贵的操作，即使在没有锁竞争的情况下也是如此。
在上述的三步流程中，更新器同时执行移除和回收步骤，但在许多情况下，由完全不同的线程来执行回收操作更为有利，就像在Linux内核的目录项缓存（dcache）中的情况一样。即使同一个线程执行更新步骤（如上文所述的步骤(a)）和回收步骤（如上文所述的步骤(c)），通常将它们分开考虑也是有帮助的。例如，RCU读取器和更新器之间无需直接通信，但RCU提供了隐式低开销的通信机制，即在步骤(b)中实现。

那么，在读者不执行任何同步操作的情况下，回收器如何知道读者已经完成呢？继续阅读，了解RCU的API是如何使这一过程变得简单的。

.. _2_whatisRCU:

2. RCU的核心API是什么？
------------------------------

RCU的核心API非常小：

a. rcu_read_lock()
b. rcu_read_unlock()
c. synchronize_rcu() / call_rcu()
d. rcu_assign_pointer()
e. rcu_dereference()

RCU API还有许多其他成员，但其余部分都可以用这五个核心函数来表示，尽管大多数实现是通过call_rcu()回调API来表示synchronize_rcu()。以下是五个核心RCU API的描述，其他18个将在后续列举。更多信息请参阅内核文档或直接查看函数头注释。

rcu_read_lock()
^^^^^^^^^^^^^^^
    void rcu_read_lock(void);

此时间原语用于通知回收器一个读取器正在进入RCU读侧临界区。在RCU读侧临界区内阻塞是非法的，不过使用CONFIG_PREEMPT_RCU配置编译的内核可以抢占RCU读侧临界区。在RCU读侧临界区内访问的任何RCU保护的数据结构在整个临界区期间都保证不会被回收。可以结合引用计数与RCU一起使用以维持对数据结构的长期引用。

需要注意的是，任何禁用下半部、抢占或中断的操作也会进入RCU读侧临界区。获取自旋锁也会进入RCU读侧临界区，即使对于那些不禁止抢占的自旋锁也是如此，比如在使用CONFIG_PREEMPT_RT=y配置的内核中。

睡眠锁不会进入RCU读侧临界区。

rcu_read_unlock()
^^^^^^^^^^^^^^^^^
    void rcu_read_unlock(void);

此时间原语用于通知回收器一个读取器正在退出RCU读侧临界区。任何启用下半部、抢占或中断的操作也会退出RCU读侧临界区。
释放自旋锁也会退出一个RCU读端临界区。

注意，RCU读端临界区可以嵌套和/或重叠。

`synchronize_rcu()`
```
void synchronize_rcu(void);
```

这个时间原语标记了更新代码的结束和回收代码的开始。它通过阻塞直到所有CPU上的现有RCU读端临界区完成来实现这一点。需要注意的是，`synchronize_rcu()`不一定等待任何在调用`synchronize_rcu()`之后开始的RCU读端临界区完成。例如，考虑以下事件序列：

```
          CPU 0                  CPU 1                 CPU 2
     ----------------- ------------------------- ---------------
1.  rcu_read_lock()
2.                    进入synchronize_rcu()
3.                                               rcu_read_lock()
4.  rcu_read_unlock()
5.                     退出synchronize_rcu()
6.                                              rcu_read_unlock()
```

再次强调，`synchronize_rcu()`仅等待正在进行的RCU读端临界区完成，并不一定等待在调用`synchronize_rcu()`之后开始的任何RCU读端临界区完成。

当然，在最后一个现有RCU读端临界区完成后，`synchronize_rcu()`也不一定会**立即**返回。一方面，可能存在调度延迟。另一方面，许多RCU实现为了提高效率，会批量处理请求，这可能会进一步延迟`synchronize_rcu()`。

由于`synchronize_rcu()`是必须确定读者何时完成的API，因此其实现对RCU至关重要。为了使RCU在除了最极端的读密集型情况之外都有用，`synchronize_rcu()`的开销也必须非常小。

`call_rcu()` API是`synchronize_rcu()`的一种异步回调形式，在后面的章节中有更详细的描述。与其阻塞，不如注册一个函数和参数，在所有正在进行的RCU读端临界区完成后调用这些函数和参数。这种回调变体特别适用于不允许阻塞或更新端性能至关重要的情况。

然而，`call_rcu()` API不应轻易使用，因为使用`synchronize_rcu()` API通常会导致更简单的代码。

此外，`synchronize_rcu()` API具有在宽限期被延迟时自动限制更新率的良好特性。这种特性使得系统在面对拒绝服务攻击时具有韧性。使用`call_rcu()`的代码应该限制更新率以获得同样的韧性。请参阅checklist.rst了解一些限制更新率的方法。

`rcu_assign_pointer()`
```
void rcu_assign_pointer(p, typeof(p) v);
```

是的，`rcu_assign_pointer()`确实是一个宏实现的，尽管能够以这种方式声明一个函数是很酷的（而且有一些关于向C语言添加重载函数的讨论，谁知道呢？）

更新者使用这个空间宏将新值赋给一个受RCU保护的指针，以便安全地将值的变化从更新者传递给读者。这是一个空间宏（而非时间宏）。它不计算为r值，但提供了特定编译器或CPU架构所需的任何编译指令和内存屏障指令。
其排序属性类似于存储-释放操作，即任何用于初始化结构体的先前加载和存储操作都必须在发布指向该结构体的指针之前完成。

同样重要的是，`rcu_assign_pointer()` 用于记录（1）哪些指针受 RCU 保护，（2）特定结构体何时变得可被其他 CPU 访问。尽管如此，`rcu_assign_pointer()` 最常通过诸如 `list_add_rcu()` 这样的 `_rcu` 列表操作原语间接使用。

`rcu_dereference()`
^^^^^^^^^^^^^^^^^^^

```
typeof(p) rcu_dereference(p);
```

与 `rcu_assign_pointer()` 类似，`rcu_dereference()` 必须实现为一个宏。

读取者使用空间 `rcu_dereference()` 宏来获取一个受 RCU 保护的指针，该指针返回一个可以安全解引用的值。请注意，`rcu_dereference()` 实际上并不解引用该指针，而是保护该指针以便后续解引用。它还会执行给定 CPU 架构所需的内存屏障指令。目前，只有 Alpha 需要在 `rcu_dereference()` 中使用内存屏障——在其他 CPU 上，它编译为一个带有 `volatile` 属性的加载指令。然而，主流 C 编译器不尊重地址依赖性，因此 `rcu_dereference()` 使用 `volatile` 类型转换，结合 `rcu_dereference.rst` 中列出的编码指南，防止当前编译器破坏这些依赖性。

常见的编程实践是使用 `rcu_dereference()` 将一个受 RCU 保护的指针复制到一个局部变量中，然后对该局部变量进行解引用，例如：

```c
p = rcu_dereference(head.next);
return p->data;
```

在这种情况下，也可以将这两步合并为一步：

```c
return rcu_dereference(head.next)->data;
```

如果你打算从受 RCU 保护的结构体中获取多个字段，当然推荐使用局部变量。重复调用 `rcu_dereference()` 看起来很丑，并且不能保证在关键区域内发生更新时返回相同的指针，同时在 Alpha CPU 上会产生不必要的开销。

请注意，`rcu_dereference()` 返回的值仅在封闭的 RCU 读端临界区中有效。

例如，以下代码是 **不合法** 的：

```c
rcu_read_lock();
p = rcu_dereference(head.next);
rcu_read_unlock();
x = p->address; /* BUG!!! */
rcu_read_lock();
y = p->data;    /* BUG!!! */
rcu_read_unlock();
```

从一个 RCU 读端临界区持有一个引用到另一个 RCU 读端临界区与从一个基于锁的临界区持有一个引用到另一个基于锁的临界区一样非法！同样，在获取该引用的临界区之外使用该引用也与使用普通锁定一样非法！

与 `rcu_assign_pointer()` 类似，`rcu_dereference()` 的一个重要功能是记录哪些指针受 RCU 保护，特别是标记一个随时可能发生变化的指针，包括在 `rcu_dereference()` 调用之后立即变化。

同样地，像 `rcu_assign_pointer()` 一样，`rcu_dereference()` 通常也是通过 `_rcu` 列表操作原语间接使用的，例如 `list_for_each_entry_rcu()`。

.. [1] 变体 `rcu_dereference_protected()` 可以在没有 RCU 读端临界区的情况下使用，只要其使用受到更新端代码所获取的锁的保护。这个变体避免了在未使用 `rcu_read_lock()` 保护的情况下使用 `rcu_dereference()` 时会发生的锁依赖警告。
使用 `rcu_dereference_protected()` 还有一个优点，即允许编译器进行优化，而这是 `rcu_dereference()` 必须禁止的。`rcu_dereference_protected()` 变体需要一个锁依赖（lockdep）表达式来指示调用者必须获取哪些锁。如果未提供所指示的保护，则会发出锁依赖警告。更多详细信息和示例用法，请参见 `Design/Requirements/Requirements.rst` 和 API 的代码注释。

[2] 如果 `list_for_each_entry_rcu()` 实例可能被更新方代码以及 RCU 读取方代码使用，则可以向其参数列表中添加一个额外的锁依赖表达式。
例如，给定一个额外的 “lock_is_held(&mylock)” 参数，RCU 锁依赖代码仅在该实例在 RCU 读取方临界区之外且没有 mylock 保护的情况下才会抱怨。

下图显示了每个 API 在读取方、更新方和回收方之间的通信情况：

```
    rcu_assign_pointer()
	                          +--------+
    +---------------------->| reader |---------+
    |                       +--------+         |
    |                           |              |
    |                           |              | 保护：
    |                           |              | rcu_read_lock()
    |                           |              | rcu_read_unlock()
    |        rcu_dereference()  |              |
    +---------+                 |              |
    | updater |<----------------+              |
    +---------+                                V
    |                                     +-----------+
    +----------------------------------->| reclaimer |
                                          +-----------+
      延迟：
      synchronize_rcu() & call_rcu()
```

RCU 架构通过观察 `rcu_read_lock()`、`rcu_read_unlock()`、`synchronize_rcu()` 和 `call_rcu()` 调用的时间序列来确定何时 (1) `synchronize_rcu()` 调用可以返回给调用者；(2) `call_rcu()` 回调可以被调用。高效的 RCU 实现大量使用批处理以分摊相应 API 使用的开销。

`rcu_assign_pointer()` 和 `rcu_dereference()` 调用通过存储到和从 RCU 保护指针中的操作来传达空间变化。

Linux 内核中有至少三种 RCU 使用方式。上图显示的是最常见的一种。在更新方，使用的 `rcu_assign_pointer()`、`synchronize_rcu()` 和 `call_rcu()` 原语对于所有三种方式都是相同的。然而，在读取方用于保护的原语根据不同的方式有所不同：

a. `rcu_read_lock()` / `rcu_read_unlock()`
   `rcu_dereference()`

b. `rcu_read_lock_bh()` / `rcu_read_unlock_bh()`
   `local_bh_disable()` / `local_bh_enable()`
   `rcu_dereference_bh()`

c. `rcu_read_lock_sched()` / `rcu_read_unlock_sched()`
   `preempt_disable()` / `preempt_enable()`
   `local_irq_save()` / `local_irq_restore()`
   硬中断进入 / 硬中断退出
   NMI 进入 / NMI 退出
   `rcu_dereference_sched()`

这三种方式分别用于：

a. 应用于普通数据结构的 RCU
b. 应用于可能遭受远程拒绝服务攻击的网络数据结构的 RCU
c. 应用于调度程序和中断/NMI 处理任务的 RCU

再次强调，大多数情况下会使用 (a)。而 (b) 和 (c) 案例对于特殊用途很重要，但相对较少见。SRCU、RCU-Tasks、RCU-Tasks-Rude 和 RCU-Tasks-Trace 各自原语之间也有类似的关系。
### 3. RCU核心API的一些示例用途
-----------------------------------------------

本节展示了如何使用核心RCU API来保护一个指向动态分配结构的全局指针。更多典型的RCU用法可以在`listRCU.rst`和`NMI-RCU.rst`中找到。

```c
struct foo {
    int a;
    char b;
    long c;
};
DEFINE_SPINLOCK(foo_mutex);

struct foo __rcu *gbl_foo;

/*
 * 创建一个新的struct foo，其内容与gbl_foo当前指向的结构相同，
 * 除了字段"a"被替换为"new_a"。将gbl_foo指向新结构，并在经过一个宽限期后释放旧结构。
 *
 * 使用rcu_assign_pointer()确保并发读取者看到新结构的已初始化版本。
 *
 * 使用synchronize_rcu()确保所有可能引用旧结构的读取者完成操作后再释放旧结构。
 */
void foo_update_a(int new_a)
{
    struct foo *new_fp;
    struct foo *old_fp;

    new_fp = kmalloc(sizeof(*new_fp), GFP_KERNEL);
    spin_lock(&foo_mutex);
    old_fp = rcu_dereference_protected(gbl_foo, lockdep_is_held(&foo_mutex));
    *new_fp = *old_fp;
    new_fp->a = new_a;
    rcu_assign_pointer(gbl_foo, new_fp);
    spin_unlock(&foo_mutex);
    synchronize_rcu();
    kfree(old_fp);
}

/*
 * 返回当前gbl_foo结构中的字段"a"的值。使用rcu_read_lock()和rcu_read_unlock()
 * 确保该结构不会在我们访问期间被删除，并使用rcu_dereference()确保我们看到的是
 * 结构的已初始化版本（对于DEC Alpha平台和阅读代码的人非常重要）。
 */
int foo_get_a(void)
{
    int retval;

    rcu_read_lock();
    retval = rcu_dereference(gbl_foo)->a;
    rcu_read_unlock();
    return retval;
}
```

总结如下：

- 使用rcu_read_lock()和rcu_read_unlock()来保护RCU读端临界区。
- 在RCU读端临界区内，使用rcu_dereference()来解引用受RCU保护的指针。
- 使用一些坚实的设计（如锁或信号量）来防止并发更新相互干扰。
- 使用rcu_assign_pointer()来更新受RCU保护的指针。此原语保护并发读取者不受更新者的干扰，
  **而不是保护并发更新不受彼此干扰**！因此，你仍然需要使用锁定（或其他类似机制）来防止
  同时调用rcu_assign_pointer()原语之间的相互干扰。
使用 `synchronize_rcu()` 在从一个 RCU 保护的数据结构中移除数据元素 **之后**，但在 **回收/释放** 数据元素 **之前**，以等待所有可能引用该数据项的 RCU 读侧临界区完成。

请参阅 `checklist.rst` 以获取使用 RCU 时需要遵循的其他规则。更多典型的 RCU 使用示例可以在 `listRCU.rst` 和 `NMI-RCU.rst` 中找到。

.. _4_whatisRCU:

4. 如果我的更新线程不能阻塞怎么办？
--------------------------------------------

在上面的例子中，`foo_update_a()` 阻塞直到一个宽限期结束。
这非常简单，但在某些情况下，我们无法承受等待这么长时间——可能会有其他高优先级的工作要做。
在这种情况下，可以使用 `call_rcu()` 而不是 `synchronize_rcu()`。
`call_rcu()` 的 API 如下所示：

```c
void call_rcu(struct rcu_head *head, rcu_callback_t func);
```

此函数会在一个宽限期结束后调用 `func(head)`。
这个调用可能发生在软中断上下文或进程上下文中，因此该函数不允许阻塞。
`foo` 结构体需要添加一个 `rcu_head` 结构，如下所示：

```c
struct foo {
    int a;
    char b;
    long c;
    struct rcu_head rcu;
};
```

那么 `foo_update_a()` 函数可以这样编写：

```c
/*
 * 创建一个新的 struct foo，除了将字段 "a" 替换为 "new_a" 之外，其余与当前由 gbl_foo 指向的结构相同。
 * 将 gbl_foo 指向新的结构，并在一个宽限期后释放旧的结构。
 *
 * 使用 rcu_assign_pointer() 来确保并发读取者看到新结构的已初始化版本。
 *
 * 使用 call_rcu() 来确保任何可能引用旧结构的读取者在释放旧结构前完成操作。
 */
```
```c
void foo_update_a(int new_a)
{
    struct foo *new_fp;
    struct foo *old_fp;

    new_fp = kmalloc(sizeof(*new_fp), GFP_KERNEL);
    spin_lock(&foo_mutex);
    old_fp = rcu_dereference_protected(gbl_foo, lockdep_is_held(&foo_mutex));
    *new_fp = *old_fp;
    new_fp->a = new_a;
    rcu_assign_pointer(gbl_foo, new_fp);
    spin_unlock(&foo_mutex);
    call_rcu(&old_fp->rcu, foo_reclaim);
}
```

`foo_reclaim()`函数可能如下所示：

```c
void foo_reclaim(struct rcu_head *rp)
{
    struct foo *fp = container_of(rp, struct foo, rcu);

    foo_cleanup(fp->a);

    kfree(fp);
}
```

`container_of()`原语是一个宏，给定一个指向结构体内部字段的指针、结构体类型以及指向该字段的指针，返回指向结构体开头的指针。

使用`call_rcu()`允许`foo_update_a()`的调用者立即重新获得控制权，而无需进一步担心新更新元素的老版本。这也清楚地展示了更新者（即`foo_update_a()`）与回收者（即`foo_reclaim()`）之间的RCU区别。

建议总结与前一节相同，只是我们现在使用的是`call_rcu()`而不是`synchronize_rcu()`：

- 在从RCU保护的数据结构中移除数据元素后，使用`call_rcu()`注册一个回调函数，该回调函数将在所有可能引用该数据项的RCU读侧临界区完成之后被调用。

如果`call_rcu()`的回调仅做`kfree()`操作，可以使用`kfree_rcu()`代替`call_rcu()`以避免编写自己的回调：

```c
kfree_rcu(old_fp, rcu);
```

如果允许偶尔休眠，可以使用单参数形式，省去`struct foo`中的`rcu_head`结构：

```c
kfree_rcu_mightsleep(old_fp);
```

这种变体几乎不会阻塞，但可能会因内存分配失败而调用`synchronize_rcu()`。

再次参见checklist.rst以获取更多关于RCU使用的规则。
.. _5_whatisRCU:

5. RCU有哪些简单的实现？
--------------------------------

RCU的一个好处是它有非常简单的“玩具”实现，这是理解Linux内核中生产质量实现的良好第一步。本节介绍了两个这样的RCU“玩具”实现，一个基于熟悉的锁原语，另一个更接近于“经典”的RCU。两者都过于简单，不适合实际应用，缺乏功能和性能。然而，它们有助于理解RCU的工作原理。请参阅`kernel/rcu/update.c`以获取生产质量的实现，并参阅：

    https://docs.google.com/document/d/1X0lThx8OK0ZgLMqVoXiR4ZrGURHrXK6NyLRbeXe3Xac/edit

以获取描述Linux内核RCU实现的论文。OLS'01和OLS'02论文是一个很好的介绍，而论文提供了截至2004年初当前实现的更多细节。
5A. “玩具”实现#1：锁定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

本节介绍了一个基于熟悉锁原语的RCU“玩具”实现。其开销使其在实际应用中不可行，而且缺乏可扩展性。它也不适合实时使用，因为它允许调度延迟从一个读侧临界区“渗入”到另一个。它还假设了递归读写锁：如果你尝试使用非递归锁并允许嵌套`rcu_read_lock()`调用，可能会导致死锁。

然而，这可能是最容易理解的实现，因此是一个很好的起点。

它极其简单：

```c
static DEFINE_RWLOCK(rcu_gp_mutex);

void rcu_read_lock(void)
{
    read_lock(&rcu_gp_mutex);
}

void rcu_read_unlock(void)
{
    read_unlock(&rcu_gp_mutex);
}

void synchronize_rcu(void)
{
    write_lock(&rcu_gp_mutex);
    smp_mb__after_spinlock();
    write_unlock(&rcu_gp_mutex);
}
```

[你可以忽略`rcu_assign_pointer()`和`rcu_dereference()`而不遗漏太多内容。但这里还是提供简化版本。无论你做什么，请不要在提交使用RCU的补丁时忘记它们！]

```c
#define rcu_assign_pointer(p, v) \
({ \
    smp_store_release(&(p), (v)); \
})

#define rcu_dereference(p) \
({ \
    typeof(p) _________p1 = READ_ONCE(p); \
    (_________p1); \
})
```

`rcu_read_lock()`和`rcu_read_unlock()`原语分别读取获取和释放全局读写锁。`synchronize_rcu()`原语写获取此锁，然后释放它。这意味着一旦`synchronize_rcu()`退出，所有在调用`synchronize_rcu()`之前进行的RCU读侧临界区都保证已完成——否则`synchronize_rcu()`无法写获取锁。`smp_mb__after_spinlock()`将`synchronize_rcu()`提升为完整的内存屏障，符合以下列出的“内存屏障保证”：

    Design/Requirements/Requirements.rst

可以嵌套`rcu_read_lock()`，因为读写锁可以递归获取。请注意，`rcu_read_lock()`不会死锁（这是RCU的一个重要属性）。原因在于唯一可能阻止`rcu_read_lock()`的是`synchronize_rcu()`。
但是 `synchronize_rcu()` 在持有 `rcu_gp_mutex` 时不会获取任何锁，因此不可能出现死锁循环。

.. _quiz_1:

快速问答 #1:
		为什么这个论点是天真的？在使用这种算法的真实世界中的 Linux 内核中，死锁如何发生？如何避免这种死锁？

:ref:`快速问答答案 <9_whatisRCU>`

5B. “玩具”示例 #2：经典 RCU
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
本节介绍了一个基于“经典 RCU”实现的“玩具”版本。该实现性能较差（但仅限于更新操作），并且缺乏热插拔 CPU 和在 CONFIG_PREEMPTION 内核中运行的能力。`rcu_dereference()` 和 `rcu_assign_pointer()` 的定义与前一节相同，因此这里省略了它们。

```c
void rcu_read_lock(void) { }

void rcu_read_unlock(void) { }

void synchronize_rcu(void)
{
    int cpu;

    for_each_possible_cpu(cpu)
        run_on(cpu);
}
```

请注意，`rcu_read_lock()` 和 `rcu_read_unlock()` 完全没有任何作用。
这是非抢占内核中经典 RCU 的一大优势：读端开销为零，至少对于非 Alpha CPU 是如此。
而且 `rcu_read_lock()` 绝对不可能参与任何死锁循环！

`synchronize_rcu()` 的实现只是依次在每个 CPU 上调度自身。`run_on()` 原语可以简单地通过 `sched_setaffinity()` 原语实现。当然，稍微不那么“玩具”的实现会在完成任务后恢复亲和性，而不是让所有任务都运行在最后一个 CPU 上，但当我提到“玩具”时，我是说 **真正的玩具**！

那这到底是怎么工作的呢？

请记住，在 RCU 读端临界区中阻塞是非法的。因此，如果某个 CPU 执行了一次上下文切换，我们知道它必须已经完成了所有先前的 RCU 读端临界区。一旦 **所有** CPU 都执行了一次上下文切换，那么 **所有** 先前的 RCU 读端临界区都将完成。
所以，假设我们从一个结构中移除了一个数据项并调用 `synchronize_rcu()`。一旦 `synchronize_rcu()` 返回，我们可以保证没有 RCU 读端临界区持有对该数据项的引用，因此我们可以安全地回收它。

.. _quiz_2:

快速问答 #2:
		给出一个例子，说明经典 RCU 的读端开销是 **负数** 的。
:ref:`快速问答答案 <9_whatisRCU>`

.. _quiz_3:

快速问答 #3:
		既然在 RCU 读端临界区中阻塞是非法的，那么在 CONFIG_PREEMPT_RT 中，普通的自旋锁可以阻塞，这时该怎么办？
:ref:`快速问答答案 <9_whatisRCU>`

.. _6_whatisRCU:

6. 类比于读写锁
----------------------

虽然 RCU 可以以多种方式使用，但非常常见的 RCU 用法类似于读写锁。下面的统一差异显示了 RCU 和读写锁之间的紧密关系：

```diff
@@ -5,5 +5,5 @@ struct el {
 	int data;
 	/* 其他数据字段 */
 };
-rwlock_t listmutex;
+spinlock_t listmutex;
 struct el head;

@@ -13,15 +14,15 @@
 struct list_head *lp;
 struct el *p;

-	read_lock(&listmutex);
-	list_for_each_entry(p, head, lp) {
+	rcu_read_lock();
+	list_for_each_entry_rcu(p, head, lp) {
 	if (p->key == key) {
 		*result = p->data;
-		read_unlock(&listmutex);
+		rcu_read_unlock();
 		return 1;
 	}
 }
-read_unlock(&listmutex);
+rcu_read_unlock();
 return 0;
}

@@ -29,15 +30,16 @@
 {
 	struct el *p;

-	write_lock(&listmutex);
+	spin_lock(&listmutex);
 	list_for_each_entry(p, head, lp) {
 		if (p->key == key) {
-			list_del(&p->list);
-			write_unlock(&listmutex);
+			list_del_rcu(&p->list);
+			spin_unlock(&listmutex);
+			synchronize_rcu();
 			kfree(p);
 			return 1;
 		}
 	}
-write_unlock(&listmutex);
+	spin_unlock(&listmutex);
 	return 0;
 }
```

或者，对于那些喜欢并排列出的人来说：

```c
1 struct el {                          1 struct el {
2   struct list_head list;             2   struct list_head list;
3   long key;                          3   long key;
4   spinlock_t mutex;                  4   spinlock_t mutex;
5   int data;                          5   int data;
6   /* 其他数据字段 */            6   /* 其他数据字段 */
7 };                                   7 };
8 rwlock_t listmutex;                  8 spinlock_t listmutex;
9 struct el head;                      9 struct el head;
```

```c
1 int search(long key, int *result)    1 int search(long key, int *result)
2 {                                    2 {
3   struct list_head *lp;              3   struct list_head *lp;
4   struct el *p;                      4   struct el *p;
5                                      5
6   read_lock(&listmutex);             6   rcu_read_lock();
7   list_for_each_entry(p, head, lp) { 7   list_for_each_entry_rcu(p, head, lp) {
8     if (p->key == key) {             8     if (p->key == key) {
9       *result = p->data;             9       *result = p->data;
10       read_unlock(&listmutex);      10       rcu_read_unlock();
11       return 1;                     11       return 1;
12     }                               12     }
13   }                                 13   }
14   read_unlock(&listmutex);          14   rcu_read_unlock();
15   return 0;                         15   return 0;
16 }                                   16 }
```

```c
1 int delete(long key)                 1 int delete(long key)
2 {                                    2 {
3   struct el *p;                      3   struct el *p;
4                                      4
5   write_lock(&listmutex);            5   spin_lock(&listmutex);
6   list_for_each_entry(p, head, lp) { 6   list_for_each_entry(p, head, lp) {
7     if (p->key == key) {             7     if (p->key == key) {
8       list_del(&p->list);            8       list_del_rcu(&p->list);
9       write_unlock(&listmutex);      9       spin_unlock(&listmutex);
                                        10       synchronize_rcu();
10       kfree(p);                     11       kfree(p);
11       return 1;                     12       return 1;
12     }                               13     }
13   }                                 14   }
14   write_unlock(&listmutex);         15   spin_unlock(&listmutex);
15   return 0;                         16   return 0;
16 }                                   17 }
```

无论哪种方式，差异都非常小。读端锁定移到了 `rcu_read_lock()` 和 `rcu_read_unlock`，更新端锁定从读写锁改为简单的自旋锁，并且在 `kfree()` 之前有一个 `synchronize_rcu()` 调用。
然而，有一个潜在的问题：读取侧和更新侧的临界区现在可以并发运行。在许多情况下，这不会成为问题，但无论如何都需要仔细检查。例如，如果多个独立的列表更新必须被视为单一的原子更新，则转换为RCU（Read-Copy-Update）将需要特别小心。此外，synchronize_rcu()的存在意味着RCU版本的delete()现在可能会阻塞。如果这是一个问题，有一种基于回调机制的方法永远不会阻塞，即call_rcu()或kfree_rcu()，可以在synchronize_rcu()的地方使用。

.. _7_whatisRCU:

7. 类比引用计数
----------------

读者-写者类比（如前一节所示）并不总是思考如何使用RCU的最佳方式。另一个有用的类比是将RCU视为对所有受RCU保护的对象的有效引用计数。
引用计数通常不阻止被引用对象的值发生改变，但确实防止了类型的变化——特别是当该对象的内存被释放并重新分配用于其他用途时发生的类型变化。一旦获得了对该对象的安全引用，就需要另一种机制来确保对该对象数据的一致访问。这可能涉及获取自旋锁，但在RCU中，典型的做法是使用SMP感知的操作（如smp_load_acquire()）进行读取，使用原子读改写操作进行更新，并提供必要的顺序。RCU提供了许多支持函数，嵌入了所需的操作和顺序，例如前一节中使用的list_for_each_entry_rcu()宏。

更具体地看待引用计数行为是在rcu_read_lock()和rcu_read_unlock()之间，通过rcu_dereference()在标记为`__rcu`的指针上取得的任何引用可以被视为暂时增加了对该对象的引用计数。这防止了对象类型的改变。这意味着什么取决于该类型对象的正常期望，但它通常包括可以安全锁定自旋锁、可以安全操纵正常的引用计数以及可以安全解引用`__rcu`指针。

对于持有RCU引用的对象，我们可能会看到的一些操作包括：

- 复制由对象类型保证稳定的那些数据
- 使用kref_get_unless_zero()或类似方法获取一个长期引用。当然，这可能会失败
### 获取自旋锁并在对象中检查是否仍为预期对象，如果是，则自由地操作它

RCU提供了一个引用，该引用仅防止类型更改。这一点在从带有`SLAB_TYPESAFE_BY_RCU`标记的 slab 缓存分配的对象中尤为明显。RCU 操作可能会返回一个并发释放并重新分配给完全不同的对象（尽管类型相同）的缓存中的对象引用。在这种情况下，RCU 甚至不保护对象身份的变化，只保护其类型。因此，找到的对象可能不是预期的那个，但它将是一个可以安全获取引用的对象（然后可能获取自旋锁），允许后续代码检查身份是否符合预期。虽然很想直接获取自旋锁而不先获取引用，但不幸的是，在`SLAB_TYPESAFE_BY_RCU`对象中的任何自旋锁都必须在每次调用`kmem_cache_alloc()`之后初始化，这使得无引用的自旋锁获取完全不安全。因此，在使用`SLAB_TYPESAFE_BY_RCU`时，请正确使用引用计数（那些愿意在 kmem_cache 构造函数中初始化锁的人也可以使用锁定，包括缓存友好的序列锁定）。

使用传统的引用计数（如 Linux 中的 kref 库实现的那样），通常会在最后一个对象引用被丢弃时运行一些代码。对于 kref，这是传递给 `kref_put()` 的函数。当使用 RCU 时，这种最终化代码不能在所有引用对象的 `__rcu` 指针更新之前运行，并且必须经过一个宽限期。每个剩余的全局可见指针都应被视为潜在的计数引用，而最终化代码通常在所有这些指针都被更改后通过 `call_rcu()` 运行。要在这两种类比之间选择——RCU 作为读写锁和 RCU 作为引用计数系统——考虑受保护事物的规模是有帮助的。读写锁类比着眼于较大的多部分对象，如链表，并展示了 RCU 如何在向列表添加和删除元素时促进并发。引用计数类比则着眼于单个对象，并查看它们如何在其所属的整体中安全访问。

### RCU API 完整列表

RCU API 在 Linux 内核源代码中的 DocBook 格式注释中有详细记录，但有一个完整的 API 列表会更有帮助，因为似乎没有办法在 DocBook 中对它们进行分类。以下是按类别列出的 API：

#### RCU 列表遍历

- `list_entry_rcu`
- `list_entry_lockless`
- `list_first_entry_rcu`
- `list_next_rcu`
- `list_for_each_entry_rcu`
- `list_for_each_entry_continue_rcu`
- `list_for_each_entry_from_rcu`
- `list_first_or_null_rcu`
- `list_next_or_null_rcu`
- `hlist_first_rcu`
- `hlist_next_rcu`
- `hlist_pprev_rcu`
- `hlist_for_each_entry_rcu`
- `hlist_for_each_entry_rcu_bh`
- `hlist_for_each_entry_from_rcu`
- `hlist_for_each_entry_continue_rcu`
- `hlist_for_each_entry_continue_rcu_bh`
- `hlist_nulls_first_rcu`
- `hlist_nulls_for_each_entry_rcu`
- `hlist_bl_first_rcu`
- `hlist_bl_for_each_entry_rcu`

#### RCU 指针/列表更新

- `rcu_assign_pointer`
- `list_add_rcu`
- `list_add_tail_rcu`
- `list_del_rcu`
- `list_replace_rcu`
- `hlist_add_behind_rcu`
- `hlist_add_before_rcu`
- `hlist_add_head_rcu`
- `hlist_add_tail_rcu`
- `hlist_del_rcu`
- `hlist_del_init_rcu`
- `hlist_replace_rcu`
- `list_splice_init_rcu`
- `list_splice_tail_init_rcu`
- `hlist_nulls_del_init_rcu`
- `hlist_nulls_del_rcu`
- `hlist_nulls_add_head_rcu`
- `hlist_bl_add_head_rcu`
- `hlist_bl_del_init_rcu`
- `hlist_bl_del_rcu`
- `hlist_bl_set_first_rcu`

#### RCU

- **关键区域**：`rcu_read_lock`, `rcu_read_unlock`, `rcu_dereference`, `rcu_read_lock_held`, `rcu_dereference_check`, `kfree_rcu`, `rcu_dereference_protected`
- **宽限期**：`synchronize_net`, `synchronize_rcu`, `synchronize_rcu_expedited`
- **屏障**：`rcu_barrier`, `call_rcu`

#### bh

- **关键区域**：`rcu_read_lock_bh`, `rcu_read_unlock_bh`
- **宽限期**：`call_rcu`, `synchronize_rcu`, `synchronize_rcu_expedited`
- **屏障**：`rcu_barrier`

#### sched

- **关键区域**：`rcu_read_lock_sched`, `rcu_read_unlock_sched`, `rcu_read_lock_sched_notrace`, `rcu_read_unlock_sched_notrace`
- **宽限期**：`call_rcu`, `synchronize_rcu`, `synchronize_rcu_expedited`
- **屏障**：`rcu_barrier`

#### RCU-Tasks

- **关键区域**：N/A
- **宽限期**：`call_rcu_tasks`
- **屏障**：`rcu_barrier_tasks`

#### RCU-Tasks-Rude

- **关键区域**：N/A
- **宽限期**：`call_rcu_tasks_rude`
- **屏障**：`rcu_barrier_tasks_rude`

#### RCU-Tasks-Trace

- **关键区域**：`rcu_read_lock_trace`, `rcu_read_unlock_trace`
- **宽限期**：`call_rcu_tasks_trace`, `synchronize_rcu_tasks_trace`
- **屏障**：`rcu_barrier_tasks_trace`

#### SRCU

- **关键区域**：`srcu_read_lock`, `srcu_read_unlock`, `srcu_dereference`, `srcu_read_lock_held`
- **宽限期**：`synchronize_srcu`, `synchronize_srcu_expedited`
- **屏障**：`srcu_barrier`

#### SRCU：初始化/清理

- `DEFINE_SRCU`
- `DEFINE_STATIC_SRCU`
- `init_srcu_struct`
- `cleanup_srcu_struct`

#### 所有：lockdep 检查的 RCU 实用 API

- `RCU_LOCKDEP_WARN`
- `rcu_sleep_check`

#### 所有：未检查的 RCU 保护指针访问

- `rcu_dereference_raw`

#### 所有：禁止解引用的未检查 RCU 保护指针访问

- `rcu_access_pointer`

有关更多信息，请参阅源代码中的注释头（或从中生成的 DocBook 文档）。

然而，鉴于 Linux 内核中有不少于四个 RCU API 家族，如何选择使用哪一个呢？以下列表可能会有所帮助：

1. **读者需要阻塞吗？**
   - 如果是，你需要 SRCU。
   
2. **读者需要阻塞并且你正在做追踪，例如 ftrace 或 BPF 吗？**
   - 如果是，你需要 RCU-tasks、RCU-tasks-rude 和/或 RCU-tasks-trace。
   
3. **关于 -rt 补丁集呢？**
   - 如果读者在非实时内核中需要阻塞，你需要 SRCU。
   - 如果读者在实时内核中获取自旋锁时需要阻塞，但在非实时内核中不需要，那么 SRCU 不是必需的。（-rt 补丁集将自旋锁转换为睡眠锁，因此存在这种区别。）

4. **你需要将 NMI 处理程序、硬中断处理程序以及禁用抢占的代码段视为显式的 RCU 读者吗？**
   - 如果是，RCU-sched 读者是你唯一的选择，但从大约 v4.20 开始你可以使用普通的 RCU 更新原语。
   
5. **你需要即使在软中断垄断一个或多个 CPU 的情况下也能完成 RCU 宽限期吗？**
   - 例如，你的代码是否容易受到基于网络的拒绝服务攻击？
   - 如果是，你应该禁用软中断，例如使用 `rcu_read_lock_bh()`。从大约 v4.20 开始你可以使用普通的 RCU 更新原语。
f. 您的工作负载是否对RCU的正常使用来说过于频繁更新，但又不适合使用其他同步机制？如果是，请考虑使用SLAB_TYPESAFE_BY_RCU（最初名为SLAB_DESTROY_BY_RCU）。但是请注意要小心！

g. 您是否需要在即使处于深度空闲循环中的CPU、进入或退出用户模式执行时，或者在一个离线CPU上也能得到尊重的读侧临界区？如果是，SRCU和RCU任务跟踪是唯一适合您的选择，其中SRCU几乎在所有情况下都更受推荐。

h. 否则，请使用RCU。
当然，这一切的前提是您已经确定RCU确实是您工作的正确工具。
.. _9_whatisRCU:

9. 快速测验答案
--------------------------

快速测验 #1：
为什么这个论点是天真的？在实际的Linux内核中使用这种基于锁的“玩具”RCU算法时，死锁是如何发生的？[指的是基于锁的“玩具”RCU算法。]

答案：
考虑以下事件序列：

1. CPU 0 获取了一个不相关的锁，称为 "problematic_lock"，通过调用 spin_lock_irqsave() 禁用了中断。
2. CPU 1 进入 synchronize_rcu()，写获取 rcu_gp_mutex。
3. CPU 0 进入 rcu_read_lock()，但由于 CPU 1 持有 rcu_gp_mutex 而必须等待。
4. CPU 1 被中断，中断处理程序尝试获取 problematic_lock。

此时系统陷入死锁。
避免这种死锁的一种方法是采用类似 CONFIG_PREEMPT_RT 的方法，其中所有普通的自旋锁变为阻塞锁，并且所有中断处理程序都在特殊任务的上下文中执行。在这种情况下，在步骤 4 中，中断处理程序会被阻塞，从而允许 CPU 1 释放 rcu_gp_mutex，避免死锁的发生。
即使没有发生死锁，这种RCU实现也允许延迟从读者传递给其他读者，通过 synchronize_rcu() 实现。为了看到这一点，考虑任务 A 处于一个RCU读侧临界区（因此读持有 rcu_gp_mutex），任务 B 被阻塞在尝试写获取 rcu_gp_mutex，而任务 C 在 rcu_read_lock() 中被阻塞试图读取 rcu_gp_mutex。任务 A 的RCU读侧延迟间接地通过任务 B 影响了任务 C。
实时RCU实现因此采用了一种基于计数器的方法，其中在RCU读取侧临界区中的任务不会被执行`synchronize_rcu()`的任务阻塞。

快速测验#1:
[:ref:`返回快速测验#1 <quiz_1>`]

快速测验#2:
给出一个经典RCU的读取侧开销为**负数**的例子。
答案:
想象一个单CPU系统，使用非CONFIG_PREEMPTION内核，其中路由表由进程上下文代码使用，但可以由中断上下文代码更新（例如，通过“ICMP REDIRECT”数据包）。通常处理这种情况的方法是在搜索路由表时禁用中断。使用RCU允许取消这种中断禁用。
因此，在没有RCU的情况下，您需要支付禁用中断的成本，而在使用RCU时则不需要。
在这种情况下，可以说RCU的开销相对于单CPU中断禁用方法是负数。其他人可能会认为RCU的开销仅仅是零，并且将中断禁用方案的正开销替换为零开销的RCU方案并不构成负开销。
当然，在实际生活中情况更为复杂。但是，即使是同步原语具有负开销的可能性也是有些出乎意料的。;-)

[:ref:`返回快速测验#2 <quiz_2>`]

快速测验#3:
如果在RCU读取侧临界区中阻塞是非法的，那么在CONFIG_PREEMPT_RT中，当普通自旋锁可以阻塞时，你该怎么办？

答案:
就像CONFIG_PREEMPT_RT允许自旋锁临界区抢占一样，它也允许RCU读取侧临界区的抢占。它还允许在RCU读取侧临界区内自旋锁阻塞。
为什么看起来不一致？因为如果有必要（例如，内存不足时），可以通过优先级提升来保持RCU宽限期短。相比之下，如果阻塞等待网络接收，则无法知道应该提升什么。特别是考虑到我们需要提升的那个进程可能是一个出去买披萨的人。虽然计算机操作的电击棒可能会引起严重关注，但也可能引发严重反对。
此外，计算机怎么知道那个人类去了哪家披萨店？

[:ref:`返回快速测验#3 <quiz_3>`]

致谢

感谢帮助使本文档更易读的人们，包括Jon Walpole、Josh Triplett、Serge Hallyn、Suzanne Wood和Alan Stern。
欲了解更多信息，请访问http://www.rdrop.com/users/paulmck/RCU
