===========================
硬件自旋锁框架
===========================

简介
============

硬件自旋锁模块为异构处理器之间的同步和互斥提供硬件支持，这些处理器不运行在单一的共享操作系统下。例如，OMAP4具有两个Cortex-A9、两个Cortex-M3和一个C64x+ DSP，每个处理器运行不同的操作系统（主处理器A9通常运行Linux，而从处理器M3和DSP运行某种形式的RTOS）。一个通用的硬件自旋锁框架允许平台无关的驱动程序使用硬件自旋锁设备来访问远程处理器之间共享的数据结构，否则它们没有其他机制来实现同步和互斥操作。这对于进程间通信是必要的：在OMAP4上，主机将CPU密集型多媒体任务卸载到远程M3和/或C64x+从处理器（通过称为Syslink的IPC子系统）。为了实现基于消息的快速通信，需要最小的内核支持，以便将来自远程处理器的消息传递给相应的用户进程。这种通信基于远程处理器之间共享的简单数据结构，并使用硬件自旋锁模块进行同步（远程处理器直接将新消息放入此共享数据结构中）。一个通用的硬件自旋锁接口使得可以有通用的、平台无关的驱动程序。

用户API
========

::

  struct hwspinlock *hwspin_lock_request(void);

动态分配一个硬件自旋锁并返回其地址，如果没有可用的未使用的硬件自旋锁，则返回NULL。使用此API的用户通常希望在使用前与远程核心通信锁的ID以实现同步。应从进程上下文调用（可能会睡眠）。
::

  struct hwspinlock *hwspin_lock_request_specific(unsigned int id);

分配一个特定的硬件自旋锁ID并返回其地址，如果该硬件自旋锁已被使用则返回NULL。通常板级代码会调用此函数以预留特定的硬件自旋锁ID用于预定义的目的。
应从进程上下文中调用（可能会休眠）：

```c
int of_hwspin_lock_get_id(struct device_node *np, int index);
```

获取 OF phandle 基础的特定锁的全局锁 ID
此函数为硬件自旋锁模块的数据表用户提供了获取特定硬件自旋锁的全局锁 ID 的方法，以便可以使用正常的 `hwspin_lock_request_specific()` API 请求该锁。
函数在成功时返回一个锁 ID 编号，在硬件自旋锁设备尚未注册到核心时返回 `-EPROBE_DEFER`，或者返回其他错误值。
应从进程上下文中调用（可能会休眠）：

```c
int hwspin_lock_free(struct hwspinlock *hwlock);
```

释放先前分配的硬件自旋锁；成功时返回 0，失败时返回适当的错误代码（例如，如果硬件自旋锁已经释放，则返回 `-EINVAL`）。
应从进程上下文中调用（可能会休眠）：

```c
int hwspin_lock_timeout(struct hwspinlock *hwlock, unsigned int timeout);
```

带超时限制锁定先前分配的硬件自旋锁（超时时间以毫秒为单位）。如果硬件自旋锁已被占用，函数将忙等待直到其被释放，但在超时后放弃。
当此函数成功返回时，抢占被禁用，因此调用者不应休眠，并建议尽快释放硬件自旋锁，以减少远程内核对硬件互连的轮询。
成功时返回 0，否则返回适当的错误代码（最显著的是，如果超时后硬件自旋锁仍然繁忙，则返回 `-ETIMEDOUT`）。
函数永远不会睡眠
::

  int hwspin_lock_timeout_irq(struct hwspinlock *hwlock, unsigned int timeout);

锁定一个先前分配的硬件自旋锁，超时限制（以毫秒为单位）。如果硬件自旋锁已经被占用，该函数将忙等待直到其被释放，但在超时后会放弃。当此函数成功返回时，抢占和局部中断已被禁用，因此调用者不应睡眠，并建议尽快释放硬件自旋锁。
成功返回0，否则返回适当的错误代码（最明显的是-ETIMEDOUT，表示在超时后硬件自旋锁仍然被占用）。
该函数永远不会睡眠
::

  int hwspin_lock_timeout_irqsave(struct hwspinlock *hwlock, unsigned int timeout, unsigned long *flags);

锁定一个先前分配的硬件自旋锁，超时限制（以毫秒为单位）。如果硬件自旋锁已经被占用，该函数将忙等待直到其被释放，但在超时后会放弃。当此函数成功返回时，抢占已禁用，局部中断已禁用，并且它们的先前状态保存在给定的标志变量中。调用者不应睡眠，并建议尽快释放硬件自旋锁。
成功返回0，否则返回适当的错误代码（最明显的是-ETIMEDOUT，表示在超时后硬件自旋锁仍然被占用）。
该函数永远不会睡眠
::

  int hwspin_lock_timeout_raw(struct hwspinlock *hwlock, unsigned int timeout);

锁定一个先前分配的硬件自旋锁，超时限制（以毫秒为单位）。如果硬件自旋锁已经被占用，该函数将忙等待直到其被释放，但在超时后会放弃。
注意事项：用户必须使用互斥锁（mutex）或自旋锁（spinlock）保护获取硬件锁的例程，以避免死锁。这样可以在硬件锁下执行一些耗时的操作或可睡眠的操作。

成功返回0，否则返回适当的错误代码（特别是如果在超时后硬件自旋锁仍然忙碌，则返回-ETIMEDOUT）。该函数永远不会睡眠。

```
int hwspin_lock_timeout_in_atomic(struct hwspinlock *hwlock, unsigned int to);
```

带超时限制（以毫秒为单位指定）锁定先前分配的硬件自旋锁。如果硬件自旋锁已经被占用，该函数将忙等待直到其释放，但在超时时间到达时放弃尝试。

此函数只能在原子上下文中调用，并且超时值不应超过几毫秒。成功返回0，否则返回适当的错误代码（特别是如果在超时后硬件自旋锁仍然忙碌，则返回-ETIMEDOUT）。该函数永远不会睡眠。

```
int hwspin_trylock(struct hwspinlock *hwlock);
```

尝试锁定先前分配的硬件自旋锁，但如果已经被占用则立即失败。

成功返回后，抢占被禁用，因此调用者不应睡眠，并建议尽快释放硬件自旋锁，以减少远程内核对硬件互联的轮询。成功返回0，否则返回适当的错误代码（特别是如果硬件自旋锁已经被占用，则返回-EBUSY）。
该函数永远不会休眠。

```c
int hwspin_trylock_irq(struct hwspinlock *hwlock);
```

尝试锁定先前分配的硬件自旋锁，但如果已被占用则立即失败。
从该函数成功返回后，抢占和本地中断被禁用，因此调用者不得休眠，并建议尽快释放硬件自旋锁。
成功时返回0，否则返回适当的错误代码（最常见的是如果硬件自旋锁已被占用，则返回-EBUSY）。
该函数永远不会休眠。

```c
int hwspin_trylock_irqsave(struct hwspinlock *hwlock, unsigned long *flags);
```

尝试锁定先前分配的硬件自旋锁，但如果已被占用则立即失败。
从该函数成功返回后，抢占被禁用，本地中断被禁用，并且其先前状态被保存在给定的标志占位符中。调用者不得休眠，并建议尽快释放硬件自旋锁。
成功时返回0，否则返回适当的错误代码（最常见的是如果硬件自旋锁已被占用，则返回-EBUSY）。
该函数永远不会休眠。

```c
int hwspin_trylock_raw(struct hwspinlock *hwlock);
```

尝试锁定先前分配的硬件自旋锁，但如果已被占用则立即失败。
警告：用户必须使用互斥锁（mutex）或自旋锁（spinlock）保护获取硬件锁的过程，以避免死锁。这样可以在硬件锁下执行一些耗时的操作或可睡眠的操作。
成功返回0，否则返回适当的错误代码（特别是如果硬件自旋锁已被占用，则返回-EBUSY）。此函数永远不会睡眠。

```c
int hwspin_trylock_in_atomic(struct hwspinlock *hwlock);
```

尝试锁定之前分配的硬件自旋锁，但如果已经被占用则立即失败。
此函数只能在原子上下文中调用。成功返回0，否则返回适当的错误代码（特别是如果硬件自旋锁已被占用，则返回-EBUSY）。此函数永远不会睡眠。

```c
void hwspin_unlock(struct hwspinlock *hwlock);
```

解锁之前已锁定的硬件自旋锁。总是成功，并且可以从任何上下文调用（该函数永远不会睡眠）。

注意：
代码**永远**不应解锁一个已经解锁的硬件自旋锁（没有对此进行保护）。

```c
void hwspin_unlock_irq(struct hwspinlock *hwlock);
```

解锁之前已锁定的硬件自旋锁并启用本地中断。
```
void hwspin_unlock_irqrestore(struct hwspinlock *hwlock, unsigned long *flags);

此函数用于解锁之前已锁定的硬件自旋锁（hwspinlock）。
调用者**永远**不应解锁一个已经处于未锁定状态的硬件自旋锁。
这样做被认为是错误（没有对此进行保护）。
当此函数成功返回时，抢占和本地中断将被启用。此函数不会睡眠。

::

  void hwspin_unlock_irqrestore(struct hwspinlock *hwlock, unsigned long *flags);

解锁之前已锁定的硬件自旋锁
调用者**永远**不应解锁一个已经处于未锁定状态的硬件自旋锁。
这样做被认为是错误（没有对此进行保护）。
当此函数成功返回时，抢占将被重新启用，并恢复在给定标志中保存的本地中断状态。此函数不会睡眠。

::

  void hwspin_unlock_raw(struct hwspinlock *hwlock);

解锁之前已锁定的硬件自旋锁
调用者**永远**不应解锁一个已经处于未锁定状态的硬件自旋锁。
这样做被认为是错误（没有对此进行保护）
```
此函数永远不会睡眠
::

  void hwspin_unlock_in_atomic(struct hwspinlock *hwlock);

解锁先前已锁定的 hwspinlock
调用者**永远**不应解锁一个已经解锁的 hwspinlock
这样做被认为是错误（没有对此进行保护）
此函数永远不会睡眠
::

  int hwspin_lock_get_id(struct hwspinlock *hwlock);

获取给定 hwspinlock 的 ID 号。当 hwspinlock 动态分配时需要这个 ID：在它能够与远程 CPU 实现互斥之前，应将 ID 号传递给要同步的远程任务
返回 hwspinlock 的 ID 号，如果 hwlock 为 null，则返回 -EINVAL
典型用法
=============

::

	#include <linux/hwspinlock.h>
	#include <linux/err.h>

	int hwspinlock_example1(void)
	{
		struct hwspinlock *hwlock;
		int ret;

		/* 动态分配一个 hwspinlock */
		hwlock = hwspin_lock_request();
		if (!hwlock)
			..

		id = hwspin_lock_get_id(hwlock);
		/* 可能需要现在将 id 传递给远程处理器 */

		/* 获取锁，如果已被占用则自旋 1 秒 */
		ret = hwspin_lock_timeout(hwlock, 1000);
		if (ret)
			..

		/*
		 * 我们获取了锁，现在做我们的事情，但不要休眠
		 */

		/* 释放锁 */
		hwspin_unlock(hwlock);

		/* 释放锁资源 */
		ret = hwspin_lock_free(hwlock);
		if (ret)
			..
	}
```c
// 返回 ret
return ret;
}

int hwspinlock_example2(void)
{
    struct hwspinlock *hwlock;
    int ret;

    // 分配一个特定的硬件自旋锁ID —— 这通常需要在板级初始化代码中尽早调用
    hwlock = hwspin_lock_request_specific(PREDEFINED_LOCK_ID);
    if (!hwlock)
        // 处理错误情况
        ...

    // 尝试获取锁，但不进行自旋等待
    ret = hwspin_trylock(hwlock);
    if (!ret) {
        pr_info("锁已被占用\n");
        return -EBUSY;
    }

    // 我们已获取了锁，现在可以执行相关操作，但不要睡眠

    // 释放锁
    hwspin_unlock(hwlock);

    // 释放锁资源
    ret = hwspin_lock_free(hwlock);
    if (ret)
        // 处理错误情况
        ...
    return ret;
}

API 为实现者提供
==================

:::

int hwspin_lock_register(struct hwspinlock_device *bank, struct device *dev,
        const struct hwspinlock_ops *ops, int base_id, int num_locks);

此函数应由底层平台特定的实现调用，以注册一个新的硬件自旋锁设备（通常是包含多个锁的一个银行）。应该从进程上下文中调用（此函数可能会休眠）。
成功返回 0，失败则返回相应的错误码。

:::

int hwspin_lock_unregister(struct hwspinlock_device *bank);

此函数应由底层供应商特定的实现调用，以注销一个硬件自旋锁设备（通常是包含多个锁的一个银行）。应该从进程上下文中调用（此函数可能会休眠）。
成功时返回 hwspinlock 的地址，出错时返回 NULL（例如，如果 hwspinlock 仍在使用中）。

重要的结构体
=============

struct hwspinlock_device 是一个通常包含多个硬件锁的设备。它通过 hwspin_lock_register() API 由底层硬件自旋锁实现进行注册。
```

以上是将提供的代码和文档注释翻译成了中文。
```c
/**
 * struct hwspinlock_device - 一个通常包含多个硬件自旋锁的设备
 * @dev: 基础设备，将用于调用运行时电源管理（PM）API
 * @ops: 平台特定的硬件自旋锁处理函数
 * @base_id: 此设备中第一个锁的ID索引
 * @num_locks: 此设备中的锁数量
 * @lock: 动态分配的 'struct hwspinlock' 数组
 */
struct hwspinlock_device {
    struct device *dev;
    const struct hwspinlock_ops *ops;
    int base_id;
    int num_locks;
    struct hwspinlock lock[0];
};

struct hwspinlock_device 包含一个 hwspinlock 结构体数组，每个结构体代表一个单独的硬件锁：

/**
 * struct hwspinlock - 此结构体表示一个单个的硬件自旋锁实例
 * @bank: 拥有此锁的 hwspinlock_device 结构体
 * @lock: 由硬件自旋锁核心初始化和使用
 * @priv: 私有数据，由底层平台特定的硬件自旋锁驱动拥有
 */
struct hwspinlock {
    struct hwspinlock_device *bank;
    spinlock_t lock;
    void *priv;
};

在注册一组锁时，硬件自旋锁驱动只需要设置锁的 priv 成员。其余成员由硬件自旋锁核心自身进行设置和初始化。

实现回调
=========

在 'struct hwspinlock_ops' 中定义了三种可能的回调：

struct hwspinlock_ops {
    int (*trylock)(struct hwspinlock *lock);
    void (*unlock)(struct hwspinlock *lock);
    void (*relax)(struct hwspinlock *lock);
};

前两个回调是必须的：

->trylock() 回调应尝试获取锁，并在失败时返回 0，在成功时返回 1。此回调 **不能** 睡眠。
->unlock() 回调释放锁。它总是成功，并且也不能 **睡眠**。
->relax() 回调是可选的。当在一个锁上自旋时，由硬件自旋锁核心调用，可以被底层实现用来在两次连续调用 ->trylock() 之间强制延迟。此回调 **不能** 睡眠。
```
