SPDX 许可证标识符: GPL-2.0

.. _内核破解锁类型:

==========================
锁类型及其规则
==========================

介绍
============

内核提供了多种锁定原语，这些原语可以分为三类：

- 睡眠锁
- CPU 局部锁
- 自旋锁

本文档概念性地描述了这些锁类型，并提供了它们嵌套的规则，包括在 PREEMPT_RT 下使用的规则。

锁类别
======

睡眠锁
-------

睡眠锁只能在可抢占的任务上下文中获取。
尽管实现允许从其他上下文调用 try_lock()，但需要仔细评估 unlock() 和 try_lock() 的安全性。此外，还需要评估这些原语的调试版本。简而言之，除非别无选择，否则不要从其他上下文获取睡眠锁。

睡眠锁类型：
- mutex
- rt_mutex
- semaphore
- rw_semaphore
- ww_mutex
- percpu_rw_semaphore

在 PREEMPT_RT 内核上，以下锁类型会被转换为睡眠锁：
- local_lock
- spinlock_t
- rwlock_t

CPU 局部锁
----------

- local_lock

在非 PREEMPT_RT 内核上，local_lock 函数是围绕禁用抢占和中断的原语的包装器。与其它锁定机制不同，禁用抢占或中断纯粹是 CPU 局部并发控制机制，不适合用于跨 CPU 的并发控制。

自旋锁
------

- raw_spinlock_t
- 位自旋锁

在非 PREEMPT_RT 内核上，以下锁类型也是自旋锁：
- spinlock_t
- rwlock_t

自旋锁隐式禁用抢占，并且锁/解锁函数可以带有后缀来应用进一步的保护措施：

 ===================  ====================================================
 _bh()                禁用/启用后半部分（软中断）
 _irq()               禁用/启用中断
 _irqsave/restore()   保存并禁用/恢复中断禁用状态
 ===================  ====================================================

所有者语义
===========

上述锁类型（除了信号量）具有严格的持有者语义：

获取锁的上下文（任务）必须释放该锁。

rw_semaphores 提供了一个特殊的接口，允许读取者释放锁。

rtmutex
=======

实时互斥锁（RT-mutexes）是支持优先级继承（PI）的互斥锁。
在非 PREEMPT_RT 内核上，由于抢占和中断禁用区段的存在，PI 有局限性。
即使在 PREEMPT_RT 内核上，PI 也无法抢占禁用了抢占或中断的代码区域。相反，PREEMPT_RT 内核在可抢占的任务上下文中执行大多数这样的代码区域，特别是中断处理程序和软中断。这种转换使得 spinlock_t 和 rwlock_t 可以通过 RT-mutex 实现。

信号量
======

信号量是一种计数信号量的实现。
信号量通常用于序列化和等待，但新的用例应改用独立的序列化和等待机制，例如互斥锁（mutexes）和完成事件（completions）。

信号量与PREEMPT_RT
-----------------

PREEMPT_RT没有改变信号量的实现，因为计数信号量没有所有者的概念，从而阻止了PREEMPT_RT为信号量提供优先级继承。毕竟，未知的所有者无法被提升优先级。因此，在信号量上阻塞可能导致优先级反转。

读写信号量（rw_semaphore）
=========================

读写信号量是一种允许多个读者和单个写入者的锁定机制。在非PREEMPT_RT内核中，其实现是公平的，从而防止写入者饥饿。

读写信号量默认遵循严格的所有者语义，但存在一些特殊用途的接口，允许读者在非所有者的情况下释放锁。这些接口的工作不依赖于内核配置。

读写信号量与PREEMPT_RT
--------------------------

PREEMPT_RT内核将读写信号量映射到基于rt_mutex的实现，从而改变了其公平性：

由于一个读写信号量的写入者不能将其优先级授予多个读者，因此被抢占的低优先级读者将继续持有其锁，从而导致高优先级写入者饥饿。相反，由于读者可以将其优先级授予写入者，被抢占的低优先级写入者将提升其优先级直到释放锁，从而防止该写入者使读者饥饿。

局部锁（local_lock）
===================

局部锁为通过禁用抢占或中断来保护的关键部分提供了命名作用域。
在非PREEMPT_RT内核中，局部锁操作映射到抢占和中断禁用及启用的基本函数：

| 局部锁操作                | 映射的基本函数               |
|--------------------------|-----------------------------|
| local_lock(&llock)       | preempt_disable()           |
| local_unlock(&llock)     | preempt_enable()            |
| local_lock_irq(&llock)   | local_irq_disable()         |
| local_unlock_irq(&llock) | local_irq_enable()          |
| local_lock_irqsave(&llock)| local_irq_save()            |
| local_unlock_irqrestore(&llock)| local_irq_restore() |

局部锁的命名作用域相比常规基本函数具有两个优势：

- 锁的名字允许静态分析，并且清楚地表明了保护范围；而常规基本函数是没有范围和透明度的。
- 如果启用了lockdep，则局部锁会获得一个锁图（lockmap），允许验证保护的正确性。这可以检测出某些情况下，例如使用preempt_disable()作为保护机制的函数从中断或软中断上下文调用的情况。此外，lockdep_assert_held(&llock)与其他任何锁定原语一样工作。
### local_lock 和 PREEMPT_RT

PREEMPT_RT 内核将 `local_lock` 映射到每个 CPU 的 `spinlock_t`，从而改变了语义：

- 所有对 `spinlock_t` 的更改同样适用于 `local_lock`

### `local_lock` 使用

在非 PREEMPT_RT 内核中，当禁用抢占或中断是保护每个 CPU 数据结构的适当并发控制形式时，应使用 `local_lock`。

在 PREEMPT_RT 内核中，由于特定于 PREEMPT_RT 的 `spinlock_t` 语义，`local_lock` 不适合用于保护抢占或中断。

### `raw_spinlock_t` 和 `spinlock_t`

#### `raw_spinlock_t`

`raw_spinlock_t` 是所有内核（包括 PREEMPT_RT 内核）中的严格自旋锁实现。仅在真正关键的核心代码、低级中断处理以及需要禁用抢占或中断的地方（例如安全访问硬件状态）使用 `raw_spinlock_t`。有时，当临界区非常小以避免 RT 互斥锁开销时，也可以使用 `raw_spinlock_t`。

#### `spinlock_t`

`spinlock_t` 的语义会根据 PREEMPT_RT 状态发生变化。

在非 PREEMPT_RT 内核中，`spinlock_t` 映射到 `raw_spinlock_t` 并具有完全相同的语义。

### `spinlock_t` 和 PREEMPT_RT

在 PREEMPT_RT 内核中，`spinlock_t` 映射到基于 `rt_mutex` 的单独实现，从而改变了语义：

- 抢占不会被禁用。
- 对于 `spin_lock` 和 `spin_unlock` 操作的与硬中断相关的后缀（_irq, _irqsave / _irqrestore）不会影响 CPU 的中断禁用状态。
- 与软中断相关的后缀（_bh()）仍然会禁用软中断处理器。

在非 PREEMPT_RT 内核中，禁用抢占以达到这种效果。
PREEMPT_RT 内核使用每个 CPU 的锁进行序列化，以保持抢占功能启用。该锁会禁用软中断处理器，并且由于任务抢占而防止重新进入。

PREEMPT_RT 内核保留了所有其他 `spinlock_t` 的语义：

- 持有 `spinlock_t` 的任务不会迁移。非 PREEMPT_RT 内核通过禁用抢占避免迁移。PREEMPT_RT 内核则禁用迁移，这确保了指向每个 CPU 变量的指针即使在任务被抢占时仍然有效。
- 在获取自旋锁时，任务状态被保存，确保任务状态规则适用于所有内核配置。非 PREEMPT_RT 内核不改变任务状态。然而，如果任务在获取锁时阻塞，PREEMPT_RT 必须更改任务状态。因此，在阻塞前保存当前任务状态，相应的锁唤醒恢复它，如下所示：

```plaintext
task->state = TASK_INTERRUPTIBLE
lock()
  block()
    task->saved_state = task->state
    task->state = TASK_UNINTERRUPTIBLE
    schedule()
                    lock wakeup
                      task->state = task->saved_state
```

其他类型的唤醒通常会无条件地将任务状态设置为 RUNNING，但这在这里不起作用，因为任务必须一直阻塞直到锁可用。因此，当非锁唤醒试图唤醒一个等待自旋锁的任务时，它将保存的状态设置为 RUNNING。然后，当锁获取完成时，锁唤醒将任务状态设置为保存的状态，即设置为 RUNNING：

```plaintext
task->state = TASK_INTERRUPTIBLE
lock()
  block()
    task->saved_state = task->state
    task->state = TASK_UNINTERRUPTIBLE
    schedule()
                    non lock wakeup
                      task->saved_state = TASK_RUNNING

                    lock wakeup
                      task->state = task->saved_state
```

这确保了实际的唤醒不会丢失。

### `rwlock_t`

`rwlock_t` 是一种允许多个读者和单个写者的锁机制。非 PREEMPT_RT 内核实现 `rwlock_t` 作为自旋锁，相应的 `spinlock_t` 后缀规则也适用。该实现在公平性方面是合理的，从而防止写者饥饿。

### `rwlock_t` 和 PREEMPT_RT

PREEMPT_RT 内核将 `rwlock_t` 映射到基于 `rt_mutex` 的单独实现，从而改变了语义：

- 所有的 `spinlock_t` 改变也适用于 `rwlock_t`。
- 由于 `rwlock_t` 的写者无法将其优先级授予多个读者，被抢占的低优先级读者将继续持有其锁，从而导致高优先级写者饥饿。相反，由于读者可以将其优先级授予写者，被抢占的低优先级写者将提升其优先级直到释放锁，从而防止该写者饿死读者。

### PREEMPT_RT 注意事项

#### RT 上的本地锁

PREEMPT_RT 内核上将 `local_lock` 映射到 `spinlock_t` 有几个影响。例如，在非 PREEMPT_RT 内核上以下代码序列按预期工作：

```c
local_lock_irq(&local_lock);
raw_spin_lock(&lock);
```

并且完全等价于：

```c
raw_spin_lock_irq(&lock);
```

但在 PREEMPT_RT 内核上此代码序列会失效，因为 `local_lock_irq()` 映射到每个 CPU 的 `spinlock_t`，既不禁止中断也不禁止抢占。以下代码序列在 PREEMPT_RT 和非 PREEMPT_RT 内核上都完美正确：

```c
local_lock_irq(&local_lock);
spin_lock(&lock);
```

另一个关于本地锁的注意事项是每个 `local_lock` 都有一个特定的保护范围。因此，以下替换是错误的：

```c
func1()
{
  local_irq_save(flags);    -> local_lock_irqsave(&local_lock_1, flags);
  func3();
  local_irq_restore(flags); -> local_unlock_irqrestore(&local_lock_1, flags);
}

func2()
{
  local_irq_save(flags);    -> local_lock_irqsave(&local_lock_2, flags);
  func3();
  local_irq_restore(flags); -> local_unlock_irqrestore(&local_lock_2, flags);
}

func3()
{
  lockdep_assert_irqs_disabled();
  access_protected_data();
}
```

在非 PREEMPT_RT 内核上这是正确的，但在 PREEMPT_RT 内核上 `local_lock_1` 和 `local_lock_2` 是不同的，不能序列化 `func3()` 的调用者。另外，在 PREEMPT_RT 内核上 `lockdep` 断言会被触发，因为 `local_lock_irqsave()` 不会禁用中断。正确的替换是：

```c
func1()
{
  local_irq_save(flags);    -> local_lock_irqsave(&local_lock, flags);
  func3();
  local_irq_restore(flags); -> local_unlock_irqrestore(&local_lock, flags);
}

func2()
{
  local_irq_save(flags);    -> local_lock_irqsave(&local_lock, flags);
  func3();
  local_irq_restore(flags); -> local_unlock_irqrestore(&local_lock, flags);
}

func3()
{
  lockdep_assert_held(&local_lock);
  access_protected_data();
}
```

### `spinlock_t` 和 `rwlock_t`

`spinlock_t` 和 `rwlock_t` 在 PREEMPT_RT 内核上的语义变化有几个影响。例如，在非 PREEMPT_RT 内核上以下代码序列按预期工作：

```c
local_irq_disable();
spin_lock(&lock);
```

并且完全等价于：

```c
spin_lock_irq(&lock);
```

同样的规则也适用于 `rwlock_t` 和 `_irqsave()` 后缀变体。
在 PREEMPT_RT 内核上此代码序列会失效，因为 RT-mutex 需要一个可抢占的上下文。取而代之的是使用 `spin_lock_irq()` 或 `spin_lock_irqsave()` 及其解锁对应函数。在需要将中断禁用和锁定分开的情况下，PREEMPT_RT 提供了一个本地锁机制。获取本地锁会将任务固定在一个 CPU 上，允许获取像每个 CPU 中断禁用锁这样的锁。然而，这种方法应仅在绝对必要时使用。
一个典型的场景是在线程上下文中保护每个CPU的变量：

```c
struct foo *p = get_cpu_ptr(&var1);
spin_lock(&p->lock);
p->count += this_cpu_read(var2);
```

这段代码在非PREEMPT_RT内核上是正确的，但在PREEMPT_RT内核上会出问题。PREEMPT_RT特定的自旋锁语义更改不允许获取`p->lock`，因为`get_cpu_ptr()`隐式地禁用了抢占。以下替换可以在两种内核上工作：

```c
struct foo *p;
migrate_disable();
p = this_cpu_ptr(&var1);
spin_lock(&p->lock);
p->count += this_cpu_read(var2);
```

`migrate_disable()`确保任务被固定在当前CPU上，从而保证对`var1`和`var2`的每个CPU访问保持在同一CPU上，而任务仍然可被抢占。

然而，对于以下场景，`migrate_disable()`的替换是无效的：

```c
func()
{
  struct foo *p;
  migrate_disable();
  p = this_cpu_ptr(&var1);
  p->val = func2();
}
```

这会出问题，因为`migrate_disable()`不能防止抢占任务中的重入。对于这种情况，正确的替换是：

```c
func()
{
  struct foo *p;
  local_lock(&foo_lock);
  p = this_cpu_ptr(&var1);
  p->val = func2();
}
```

在非PREEMPT_RT内核上，这通过禁用抢占来防止重入。在PREEMPT_RT内核上，这是通过获取底层每个CPU的自旋锁`raw_spinlock_t`实现的。

### 原子自旋锁 `raw_spinlock_t`
获取`raw_spinlock_t`会禁用抢占，并可能禁用中断，因此临界区必须避免获取常规的`spinlock_t`或`rwlock_t`，例如，临界区必须避免分配内存。因此，在非PREEMPT_RT内核上，以下代码可以完美运行：

```c
raw_spin_lock(&lock);
p = kmalloc(sizeof(*p), GFP_ATOMIC);
```

但这段代码在PREEMPT_RT内核上会失败，因为内存分配器是完全可抢占的，因此不能从真正原子的上下文调用。然而，在持有常规非原子自旋锁时调用内存分配器是完全可以的，因为它们在PREEMPT_RT内核上不会禁用抢占：

```c
spin_lock(&lock);
p = kmalloc(sizeof(*p), GFP_ATOMIC);
```

### 位自旋锁 `bit spinlocks`
PREEMPT_RT无法替换位自旋锁，因为单个位太小，无法容纳RT互斥锁。因此，位自旋锁的语义在PREEMPT_RT内核上得以保留，这意味着针对`raw_spinlock_t`的注意事项也适用于位自旋锁。
某些位自旋锁在使用位替换为常规`spinlock_t`，以便支持PREEMPT_RT，使用条件编译（#ifdef）代码更改。相比之下，对于`spinlock_t`的替换不需要使用位的更改。
相反，头文件中的条件和核心锁定实现使得编译器可以透明地进行替换。

### 锁类型嵌套规则
最基础的规则如下：

- 同一锁类别（睡眠、CPU本地、自旋）的锁类型只要遵守通用锁排序规则以防止死锁，可以任意嵌套。
- 睡眠锁类型不能嵌套在CPU本地和自旋锁类型中。
- CPU本地和自旋锁类型可以嵌套在睡眠锁类型中。
- 自旋锁类型可以嵌套在所有锁类型中。

这些约束在PREEMPT_RT和其他情况下都适用。
由于PREEMPT_RT将`spinlock_t`和`rwlock_t`的锁类别从自旋改为睡眠，并用每个CPU的自旋锁替换`local_lock`，因此它们不能在持有原始自旋锁时获取。这导致了以下嵌套顺序：

1. 睡眠锁
2. `spinlock_t`, `rwlock_t`, `local_lock`
3. `raw_spinlock_t` 和 位自旋锁

如果违反这些约束，无论是在PREEMPT_RT还是其他情况下，`lockdep`都会发出警告。
当然，请提供您需要翻译的文本。
