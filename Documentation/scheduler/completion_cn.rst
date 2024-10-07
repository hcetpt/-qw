完成事件 - “等待完成”屏障APIs
================================

简介：
------

如果你有一个或多个线程必须等待某些内核活动达到某个点或特定状态，完成事件可以为这个问题提供一种无竞争的解决方案。从语义上讲，它们有点类似于`pthread_barrier()`，并且具有类似的应用场景。完成事件是一种代码同步机制，相较于锁/信号量的误用和忙循环，它更为优选。任何时候当你想到使用`yield()`或某些奇怪的`msleep(1)`循环来允许其他操作继续时，你可能需要考虑使用`wait_for_completion*()`调用和`complete()`。

使用完成事件的优势在于它们具有明确且集中的目的，这使得代码的意图非常容易理解；同时，它们还导致更高效的代码，因为所有线程都可以继续执行直到实际需要结果，并且等待和信号发送都通过低级调度器的睡眠/唤醒设施实现得非常高效。

完成事件是基于Linux调度器的等待队列和唤醒基础设施构建的。等待队列上的线程所等待的事件被简化为`struct completion`中的一个简单标志，恰当地命名为“done”。

由于完成事件与调度相关，因此相关代码可以在`kernel/sched/completion.c`中找到。

使用方法：
----------

使用完成事件主要有三个部分：

- 初始化`struct completion`同步对象。
- 通过调用`wait_for_completion()`的一个变体进行等待。
- 通过调用`complete()`或`complete_all()`进行信号发送。

还有一些辅助函数用于检查完成事件的状态。

需要注意的是，虽然初始化必须首先进行，但等待和信号发送的部分可以以任意顺序发生。即一个线程完全可以在另一个线程检查是否需要等待之前就将完成事件标记为“done”。

要使用完成事件，你需要包含`<linux/completion.h>`并创建一个静态或动态类型的`struct completion`变量，该结构只有两个字段：

```c
struct completion {
    unsigned int done;
    wait_queue_head_t wait;
};
```

这提供了`->wait`等待队列，用于放置任务以进行等待（如果有的话），以及`->done`标志，用于指示是否已完成。

完成事件应该命名以指明正在同步的事件。
一个很好的例子是：

```c
wait_for_completion(&early_console_added);

complete(&early_console_added);
```

良好的、直观的命名（一如既往）有助于代码的可读性。将完成事件命名为“complete”并不具有帮助性，除非其目的非常明显。

初始化完成事件：
-------------------

动态分配的完成事件对象最好嵌入到那些在整个函数/驱动程序生命周期内确保存活的数据结构中，以防止异步 `complete()` 调用导致的竞争情况发生。

在使用 `_timeout()` 或 `_killable()` / `_interruptible()` 变体的 `wait_for_completion()` 函数时，需要特别注意确保在所有相关活动（`complete()` 或 `reinit_completion()`）完成之前不进行内存释放，即使这些等待函数由于超时或信号触发而提前返回。

动态分配的完成事件对象的初始化是通过调用 `init_completion()` 完成的：

```c
init_completion(&dynamic_object->done);
```

在这个调用中，我们初始化了等待队列，并将 `->done` 设置为 0，即“未完成”或“未结束”。

重初始化函数 `reinit_completion()` 仅将 `->done` 字段重置为 0（“未完成”），而不触及等待队列。

调用该函数的代码必须确保没有并行发生的竞争 `wait_for_completion()` 调用。

对同一个完成事件对象重复调用 `init_completion()` 很可能是错误的，因为它会将队列重新初始化为空队列，排队的任务可能会“丢失”——在这种情况下应使用 `reinit_completion()`，但要注意其他竞争情况。

对于静态声明和初始化，有宏可供使用。

对于文件作用域内的静态（或全局）声明，可以使用 `DECLARE_COMPLETION()`：

```c
static DECLARE_COMPLETION(setup_done);
DECLARE_COMPLETION(setup_done);
```

请注意，在这种情况下，完成事件在启动时（或模块加载时）被初始化为“未完成”，因此不需要 `init_completion()` 调用。

当在一个函数内部声明局部变量作为完成事件时，则初始化应始终显式使用 `DECLARE_COMPLETION_ONSTACK()`，不仅为了满足锁依赖（lockdep），也是为了表明有限的作用域已被考虑且是有意为之：

```c
DECLARE_COMPLETION_ONSTACK(setup_done)
```

请注意，当将完成事件对象作为局部变量使用时，必须非常清楚函数栈的短暂生命周期：在所有活动（如等待线程）停止且完成事件对象完全不再使用之前，函数不能返回到调用上下文。
再次强调：特别是当使用某些等待API变体（具有更复杂的结果）时，例如超时或信号量（_timeout()、_killable() 和 _interruptible() 变体），等待可能会在对象仍被其他线程使用时提前完成——而从 wait_on_completion*() 调用函数返回会释放函数栈，并且如果在其他线程中执行 complete() 操作，则会导致微妙的数据损坏。简单的测试可能不会触发这些竞争条件。

如果有疑问，请使用动态分配的完成对象，最好嵌入到一些生命周期较长的对象中，该对象的生命周期远超过任何使用完成对象的辅助线程的生命周期，或者有一个锁或其他同步机制来确保不会在一个已释放的对象上调用 complete()。

在栈上简单地声明 DECLARE_COMPLETION() 会触发锁依赖警告。

等待完成：
-----------

为了让一个线程等待某个并发活动结束，它会调用 wait_for_completion() 函数来等待初始化的完成结构体：

```c
void wait_for_completion(struct completion *done)
```

一个典型的使用场景如下：

```plaintext
CPU#1                       CPU#2

struct completion setup_done;

init_completion(&setup_done);
initialize_work(..., &setup_done, ...);

/* 运行不相关的代码 */     /* 执行设置 */

wait_for_completion(&setup_done);    complete(&setup_done);
```

这并不意味着 wait_for_completion() 和 complete() 的调用顺序有任何特定要求——如果 complete() 在 wait_for_completion() 之前调用，则等待方会在所有依赖项满足后立即继续；否则，它将阻塞直到通过 complete() 信号完成。

注意，wait_for_completion() 调用了 spin_lock_irq()/spin_unlock_irq()，因此只有在你知道中断已启用的情况下才能安全调用。

从关闭中断的原子上下文调用它会导致难以检测的中断错误启用。

默认行为是在没有超时的情况下等待，并将任务标记为不可中断。wait_for_completion() 及其变体仅在进程上下文中是安全的（因为它们可以睡眠），但在原子上下文、中断上下文、中断禁用或抢占禁用的情况下是不安全的——请参阅下面的 try_wait_for_completion() 以处理原子/中断上下文中的完成情况。

由于所有 wait_for_completion() 变体都可能（显然）根据所等待活动的性质长时间阻塞，因此在大多数情况下你可能不想在持有互斥锁的情况下调用此函数。

可用的 wait_for_completion*() 变体：
--------------------------------------

以下变体都会返回状态，通常（或所有情况下）应检查此状态——在故意不检查状态的情况下，你可能需要做一个注释解释原因（例如，参见 arch/arm/kernel/smp.c:__cpu_up()）。

一个常见的问题是返回类型的不干净赋值，因此请注意将返回值赋给适当类型的变量。
检查返回值的具体含义也被发现相当不准确，例如像下面这样的构造：

```c
if (!wait_for_completion_interruptible_timeout(...))
```

... 在成功完成和被中断的情况下会执行相同的代码路径 —— 这可能不是你想要的结果：

```c
int wait_for_completion_interruptible(struct completion *done)
```

这个函数在等待时将任务标记为 `TASK_INTERRUPTIBLE`。如果在等待过程中收到信号，则返回 `-ERESTARTSYS`；否则返回 `0`。

```c
unsigned long wait_for_completion_timeout(struct completion *done, unsigned long timeout)
```

该任务被标记为 `TASK_UNINTERRUPTIBLE`，并且最多等待 `timeout` 轮钟滴答（jiffies）。如果超时则返回 `0`，否则返回剩余的轮钟滴答数（但至少为 `1`）。
建议使用 `msecs_to_jiffies()` 或 `usecs_to_jiffies()` 计算超时时间，以使代码大部分与 HZ 无关。
如果故意忽略返回的超时值，则应该有一个注释解释原因（例如，参见 `drivers/mfd/wm8350-core.c` 中的 `wm8350_read_auxadc()` 函数）。

```c
long wait_for_completion_interruptible_timeout(struct completion *done, unsigned long timeout)
```

此函数传递一个以轮钟滴答为单位的超时时间，并将任务标记为 `TASK_INTERRUPTIBLE`。如果收到信号，则返回 `-ERESTARTSYS`；否则如果超时则返回 `0`，如果完成则返回剩余的轮钟滴答数。
进一步的变体包括 `_killable`，它使用 `TASK_KILLABLE` 作为指定的任务状态，并在中断时返回 `-ERESTARTSYS`，或者在完成时返回 `0`。也有一个 `_timeout` 变体：

```c
long wait_for_completion_killable(struct completion *done)
long wait_for_completion_killable_timeout(struct completion *done, unsigned long timeout)
```

`_io` 变体 `wait_for_completion_io()` 的行为与非 `_io` 变体相同，只是将等待时间记录为“等待 I/O”，这会影响任务在调度/I/O 统计中的记录方式：

```c
void wait_for_completion_io(struct completion *done)
unsigned long wait_for_completion_io_timeout(struct completion *done, unsigned long timeout)
```

### 发送完成信号：
----------------------

希望发送继续条件已满足信号的线程可以调用 `complete()` 来通知一个等待者它可以继续：

```c
void complete(struct completion *done)
```

或者调用 `complete_all()` 来通知所有当前和未来的等待者：

```c
void complete_all(struct completion *done)
```

即使在等待线程开始等待之前就发送了完成信号，该信号也会如预期般工作。这是通过等待线程“消费”（递减）`struct completion` 的 `done` 字段来实现的。等待线程的唤醒顺序是它们入队的顺序（先进先出，FIFO）。
如果多次调用 `complete()`，则允许相应数量的等待者继续 —— 每次调用 `complete()` 都会简单地递增 `done` 字段。多次调用 `complete_all()` 是一个错误。`complete()` 和 `complete_all()` 都可以在 IRQ/原子上下文中安全调用。
任何时候只能有一个线程对特定的 `struct completion` 调用 `complete()` 或 `complete_all()` —— 通过等待队列自旋锁进行序列化。任何并发调用 `complete()` 或 `complete_all()` 很可能是设计上的错误。
从 IRQ 上下文发送完成信号是可以的，因为它会适当地使用 `spin_lock_irqsave()` 和 `spin_unlock_irqrestore()` 进行自旋锁，并且永远不会睡眠。

`try_wait_for_completion()` 和 `completion_done()`：
---------------------------------------------------

`try_wait_for_completion()` 函数不会将线程放入等待队列中，而是如果需要排队（阻塞）线程则返回 `false`，否则消费一个已发布的完成并返回 `true`：

```c
bool try_wait_for_completion(struct completion *done)
```

最后，为了检查完成状态而不对其进行任何更改，可以调用 `completion_done()`，如果没有任何未被等待者消费的已发布完成，则返回 `false`；否则返回 `true`：

```c
bool completion_done(struct completion *done)
```

`try_wait_for_completion()` 和 `completion_done()` 都可以在 IRQ 或原子上下文中安全调用。
