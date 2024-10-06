Futex 重新排队 PI
================

从非 PI futex 向 PI futex 重新排队任务需要特殊处理以确保底层的 rt_mutex 在有等待者的情况下永远不会没有所有者；否则会破坏 PI 提升逻辑[参见 rt-mutex-design.rst]。为了简洁起见，本文档中将此操作称为“requeue_pi”。优先级继承（Priority Inheritance）在本文档中简称为“PI”。
动机
----------

如果没有 requeue_pi，glibc 实现的 pthread_cond_broadcast() 必须唤醒所有等待在 pthread_condvar 上的任务，并让它们尝试以经典的“群牛效应”方式自行确定哪个任务首先运行。理想情况下，应仅唤醒优先级最高的等待者，其余任务则依赖于解锁与 condvar 关联的互斥锁时的自然唤醒机制。
考虑简化的 glibc 调用示例：

	/* 调用者必须锁定互斥锁 */
	pthread_cond_wait(cond, mutex)
	{
		lock(cond->__data.__lock);
		unlock(mutex);
		do {
			unlock(cond->__data.__lock);
			futex_wait(cond->__data.__futex);
			lock(cond->__data.__lock);
		} while(...)
		unlock(cond->__data.__lock);
		lock(mutex);
	}

	pthread_cond_broadcast(cond)
	{
		lock(cond->__data.__lock);
		unlock(cond->__data.__lock);
		futex_requeue(cond->data.__futex, cond->mutex);
	}

一旦 pthread_cond_broadcast() 重新排队了任务，cond->mutex 就有了等待者。请注意，pthread_cond_wait() 仅在返回用户空间后才尝试锁定互斥锁。这会导致底层的 rt_mutex 有等待者但没有所有者，从而破坏前述的 PI 提升算法。

为了支持 PI 意识的 pthread_condvar，内核需要能够将任务重新排队到 PI futex。这意味着在成功的 futex_wait 系统调用之后，调用者返回用户空间时已经持有 PI futex。glibc 实现可以修改如下：

	/* 调用者必须锁定互斥锁 */
	pthread_cond_wait_pi(cond, mutex)
	{
		lock(cond->__data.__lock);
		unlock(mutex);
		do {
			unlock(cond->__data.__lock);
			futex_wait_requeue_pi(cond->__data.__futex);
			lock(cond->__data.__lock);
		} while(...)
		unlock(cond->__data.__lock);
		/* 内核为我们获取了互斥锁 */
	}

	pthread_cond_broadcast_pi(cond)
	{
		lock(cond->__data.__lock);
		unlock(cond->__data.__lock);
		futex_requeue_pi(cond->data.__futex, cond->mutex);
	}

实际的 glibc 实现可能会检测 PI 并在现有调用内部进行必要的更改，而不是为 PI 场景创建新的调用。对于 pthread_cond_timedwait() 和 pthread_cond_signal() 也需要类似的更改。
实现
--------------

为了确保 rt_mutex 在有等待者的情况下有所有者，重新排队代码和等待代码都需要能够在返回用户空间之前获取 rt_mutex。

重新排队代码不能简单地唤醒等待者并让其自己获取 rt_mutex，因为这会在重新排队调用返回用户空间和等待者醒来开始运行之间打开一个竞争窗口。在无竞争的情况下尤其如此。

解决方案涉及两个新的 rt_mutex 辅助函数：rt_mutex_start_proxy_lock() 和 rt_mutex_finish_proxy_lock()，它们允许重新排队代码代表等待者获取无竞争的 rt_mutex，并将等待者排队到有竞争的 rt_mutex 上。

两个新的系统调用提供了内核<->用户接口来实现 requeue_pi：FUTEX_WAIT_REQUEUE_PI 和 FUTEX_CMP_REQUEUE_PI。

FUTEX_WAIT_REQUEUE_PI 由等待者（pthread_cond_wait() 和 pthread_cond_timedwait()）调用来阻塞初始 futex 并等待被重新排队到 PI 意识的 futex。其实现是 futex_wait() 和 futex_lock_pi() 高速碰撞的结果，并添加了一些额外的逻辑来检查额外的唤醒场景。

FUTEX_CMP_REQUEUE_PI 由唤醒者（pthread_cond_broadcast() 和 pthread_cond_signal()）调用来重新排队并可能唤醒等待任务。内部上，这个系统调用仍然由 futex_requeue 处理（通过传递 requeue_pi=1）。在重新排队之前，futex_requeue() 试图代表最高优先级的等待者获取重新排队目标 PI futex。如果可以，则唤醒该等待者。futex_requeue() 然后继续将剩余的 nr_wake+nr_requeue 个任务重新排队到 PI futex，在每次重新排队之前调用 rt_mutex_start_proxy_lock() 来准备任务作为底层 rt_mutex 的等待者。此时也有可能获取锁，如果是这样，则唤醒下一个等待者来完成锁的获取。
FUTEX_CMP_REQUEUE_PI 接受 nr_wake 和 nr_requeue 作为参数，但它们的和才是真正重要的。futex_requeue() 将唤醒或重新排队最多 nr_wake + nr_requeue 个任务。它只会唤醒它能够获取锁的任务数量，在大多数情况下这应该是 0，因为良好的编程实践要求调用 pthread_cond_broadcast() 或 pthread_cond_signal() 的程序在调用之前先获取互斥锁。FUTEX_CMP_REQUEUE_PI 要求 nr_wake 必须为 1。对于广播（broadcast），nr_requeue 应该是 INT_MAX；对于信号（signal），nr_requeue 应该是 0。
