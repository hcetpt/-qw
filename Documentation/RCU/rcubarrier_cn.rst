RCU 和不可卸载的模块
==========================

[最初发表于 LWN 2007年1月14日：http://lwn.net/Articles/217484/]

RCU 更新者有时会使用 `call_rcu()` 来启动一个异步等待优雅期的结束。这个原语需要一个指向 RCU 保护的数据结构内的 `rcu_head` 结构体指针，以及另一个指向稍后可能被调用以释放该结构体的函数指针。删除 IRQ 上下文中链表中的元素 p 的代码可能如下所示：

```c
list_del_rcu(p);
call_rcu(&p->rcu, p_callback);
```

由于 `call_rcu()` 从不阻塞，因此可以在 IRQ 上下文中安全地使用此代码。`p_callback()` 函数可以定义如下：

```c
static void p_callback(struct rcu_head *rp)
{
    struct pstruct *p = container_of(rp, struct pstruct, rcu);

    kfree(p);
}
```

卸载使用 `call_rcu()` 的模块
-------------------------------------

但如果 `p_callback()` 函数定义在一个不可卸载的模块中呢？

如果我们卸载模块时有一些 RCU 回调尚未完成，那么执行这些回调的 CPU 在稍后被调用时将会非常失望，如图所示：http://lwn.net/images/ns/kernel/rcu-drop.jpg
我们可能会尝试在模块退出路径中放置一个 `synchronize_rcu()`，但这还不够。尽管 `synchronize_rcu()` 确实等待了一个优雅期的结束，但它并不等待回调完成。有人可能会尝试连续多次调用 `synchronize_rcu()`，但这仍然不能保证有效。如果 RCU 回调负载非常重，则某些回调可能会被推迟，以便其他处理能够继续进行。例如，在实时内核中，这样的推迟是必需的，以避免过高的调度延迟。

rcu_barrier()
-------------

这种情况可以通过 `rcu_barrier()` 原语来处理。`rcu_barrier()` 不是等待一个优雅期的结束，而是等待所有未完成的 RCU 回调完成。请注意，`rcu_barrier()` **不** 暗示 `synchronize_rcu()`，特别是如果没有任何 RCU 回调排队，`rcu_barrier()` 有权立即返回，而无需等待任何东西，更不用说等待一个优雅期了。
使用 `rcu_barrier()` 的伪代码如下：

1. 阻止任何新的 RCU 回调被发布。
2. 执行 `rcu_barrier()`。
3. 允许模块被卸载。

对于 SRCU，还有一个 `srcu_barrier()` 函数，并且当然必须将 `srcu_barrier()` 的类型与 `call_srcu()` 的类型匹配。如果你的模块使用多个 `srcu_struct` 结构体，则在卸载该模块时还必须使用多次 `srcu_barrier()` 调用。例如，如果它使用 `call_rcu()`、`call_srcu()` 对 `srcu_struct_1` 和 `call_srcu()` 对 `srcu_struct_2`，则在卸载时需要以下三行代码：

```c
1 rcu_barrier();
2 srcu_barrier(&srcu_struct_1);
3 srcu_barrier(&srcu_struct_2);
```

如果延迟至关重要，可以使用工作队列并发运行这三项功能。
一个古老的 rcutorture 模块版本在其退出函数中使用了 `rcu_barrier()`，如下所示：

```c
 1  static void
 2  rcu_torture_cleanup(void)
 3  {
 4    int i;
 5    
 6    fullstop = 1;
 7    if (shuffler_task != NULL) {
 8      VERBOSE_PRINTK_STRING("Stopping rcu_torture_shuffle task");
 9      kthread_stop(shuffler_task);
10    }
11    shuffler_task = NULL;
12    
13    if (writer_task != NULL) {
14      VERBOSE_PRINTK_STRING("Stopping rcu_torture_writer task");
15      kthread_stop(writer_task);
16    }
17    writer_task = NULL;
18    
19    if (reader_tasks != NULL) {
20      for (i = 0; i < nrealreaders; i++) {
21        if (reader_tasks[i] != NULL) {
22          VERBOSE_PRINTK_STRING(
23            "Stopping rcu_torture_reader task");
24          kthread_stop(reader_tasks[i]);
25        }
26        reader_tasks[i] = NULL;
27      }
28      kfree(reader_tasks);
29      reader_tasks = NULL;
30    }
31    rcu_torture_current = NULL;
32    
33    if (fakewriter_tasks != NULL) {
34      for (i = 0; i < nfakewriters; i++) {
35        if (fakewriter_tasks[i] != NULL) {
36          VERBOSE_PRINTK_STRING(
37            "Stopping rcu_torture_fakewriter task");
38          kthread_stop(fakewriter_tasks[i]);
39        }
40        fakewriter_tasks[i] = NULL;
41      }
42      kfree(fakewriter_tasks);
43      fakewriter_tasks = NULL;
44    }
35    
36    if (stats_task != NULL) {
37      VERBOSE_PRINTK_STRING("Stopping rcu_torture_stats task");
38      kthread_stop(stats_task);
39    }
40    stats_task = NULL;
41    
42    /* 等待所有 RCU 回调完成。 */
43    rcu_barrier();
44    
45    rcu_torture_stats_print(); /* 在统计线程停止之后！ */
46    
47    if (cur_ops->cleanup != NULL)
48      cur_ops->cleanup();
49    if (atomic_read(&n_rcu_torture_error))
50      rcu_torture_print_module_parms("测试结束：失败");
51    else
52      rcu_torture_print_module_parms("测试结束：成功");
53  }
```

第 6 行设置了一个全局变量，以防止任何 RCU 回调再次调用自己。在大多数情况下这并不是必要的，因为 RCU 回调很少包含对 `call_rcu()` 的调用。然而，rcutorture 模块是一个例外，因此需要设置这个全局变量。
第 7 到 50 行停止了与 rcutorture 模块相关的所有内核任务。因此，一旦执行到达第 53 行时，将不会再有新的 rcutorture RCU 回调被调度。`rcu_barrier()` 调用等待所有已存在的回调完成。
然后第 55 到 62 行打印状态并进行特定操作的清理，并返回，允许模块卸载操作完成。

.. _rcubarrier_quiz_1:

快速测验 #1：
还有其他需要 `rcu_barrier()` 的情况吗？

:ref:`快速测验 #1 的答案 <answer_rcubarrier_quiz_1>`

你的模块可能有其他复杂性。例如，如果你的模块从定时器中调用 `call_rcu()`，你需要首先避免发送新的定时器，取消（或等待）所有已发送的定时器，然后再调用 `rcu_barrier()` 来等待任何剩余的 RCU 回调完成。
当然，如果模块使用 `call_rcu()`，则需要在卸载之前调用 `rcu_barrier()`。同样，如果模块使用 `call_srcu()`，则需要在卸载之前在同一 `srcu_struct` 结构上调用 `srcu_barrier()`。如果模块同时使用 `call_rcu()` 和 `call_srcu()`，则需要调用 `rcu_barrier()` 和 `srcu_barrier()`。
实现 `rcu_barrier()`
--------------------------

Dipankar Sarma 实现的 `rcu_barrier()` 利用了 RCU 回调一旦排队就不会重新排序的事实。他的实现是在每个 CPU 的回调队列上排队一个 RCU 回调，然后等待它们全部开始执行，此时可以保证所有更早的 RCU 回调已完成。
`rcu_barrier()` 的原始代码大致如下：

```c
 1  void rcu_barrier(void)
 2  {
 3    BUG_ON(in_interrupt());
 4    /* 获取 cpucontrol 互斥锁以保护 CPU 热插拔 */
 5    mutex_lock(&rcu_barrier_mutex);
 6    init_completion(&rcu_barrier_completion);
 7    atomic_set(&rcu_barrier_cpu_count, 1);
 8    on_each_cpu(rcu_barrier_func, NULL, 0, 1);
 9    if (atomic_dec_and_test(&rcu_barrier_cpu_count))
10      complete(&rcu_barrier_completion);
11    wait_for_completion(&rcu_barrier_completion);
12    mutex_unlock(&rcu_barrier_mutex);
13  }
```

第 3 行验证调用者是否处于进程上下文，第 5 和 12 行使用 `rcu_barrier_mutex` 确保一次只有一个 `rcu_barrier()` 使用全局的完成和计数器，这些计数器在第 6 和 7 行初始化。第 8 行使每个 CPU 调用 `rcu_barrier_func()`，如下面所示。注意 `on_each_cpu()` 参数列表中的最后一个 "1" 确保所有对 `rcu_barrier_func()` 的调用都将在 `on_each_cpu()` 返回前完成。第 9 行从 `rcu_barrier_cpu_count` 中减去初始计数，如果该计数现在为零，则第 10 行完成完成事件，防止第 11 行阻塞。无论如何，第 11 行随后（如果需要）等待完成事件。
.. _rcubarrier_quiz_2:

快速测验 #2：
为什么第 8 行不将 `rcu_barrier_cpu_count` 初始化为零，从而避免第 9 和 10 行的需要？

:ref:`快速测验 #2 的答案 <answer_rcubarrier_quiz_2>`

这段代码在 2008 年进行了重写，并在此后多次修改，但这仍然给出了大致思路。
`rcu_barrier_func()` 在每个 CPU 上运行，在那里它调用 `call_rcu()` 来排队一个 RCU 回调，如下所示：

```c
 1  static void rcu_barrier_func(void *notused)
 2  {
 3    int cpu = smp_processor_id();
 4    struct rcu_data *rdp = &per_cpu(rcu_data, cpu);
 5    struct rcu_head *head;
 6    
 7    head = &rdp->barrier;
 8    atomic_inc(&rcu_barrier_cpu_count);
 9    call_rcu(head, rcu_barrier_callback);
10  }
```

第 3 和 4 行定位 RCU 内部的每个 CPU 的 `rcu_data` 结构，其中包含了稍后调用 `call_rcu()` 所需的 `struct rcu_head`。第 7 行获取指向该 `struct rcu_head` 的指针，第 8 行递增全局计数器。此计数器稍后将由回调递减。第 9 行在当前 CPU 的队列上注册 `rcu_barrier_callback()`。
`rcu_barrier_callback()` 函数只是原子地递减 `rcu_barrier_cpu_count` 变量，并在其达到零时完成完成事件，如下所示：

```c
 1  static void rcu_barrier_callback(struct rcu_head *notused)
 2  {
 3    if (atomic_dec_and_test(&rcu_barrier_cpu_count))
 4      complete(&rcu_barrier_completion);
 5  }
```

.. _rcubarrier_quiz_3:

快速测验 #3：
如果 CPU 0 的 `rcu_barrier_func()` 立即执行（从而使 `rcu_barrier_cpu_count` 增加到 1），但其他 CPU 的 `rcu_barrier_func()` 调用延迟了一个完整的优雅周期，这会不会导致 `rcu_barrier()` 过早返回？

:ref:`快速测验 #3 的答案 <answer_rcubarrier_quiz_3>`

当前的 `rcu_barrier()` 实现更加复杂，因为需要避免干扰空闲 CPU（特别是在电池供电系统上），并且需要在实时系统中尽量减少干扰非空闲 CPU。
此外，还进行了大量的优化。然而，上述代码说明了相关概念。

rcu_barrier() 概述
---------------------

rcu_barrier() 原语相对较少使用，因为大多数使用 RCU 的代码位于核心内核中而不是模块中。但是，如果你从一个不可卸载的模块使用 RCU，则需要使用 rcu_barrier() 以确保模块可以安全地卸载。

快速测验答案
-------------------------

.. _answer_rcubarrier_quiz_1:

快速测验 #1:
    是否还有其他情况下可能需要 rcu_barrier()？

答案:
    有趣的是，rcu_barrier() 最初并不是为模块卸载实现的。Nikita Danilov 在一个文件系统中使用 RCU，导致在卸载文件系统时出现类似情况。Dipankar Sarma 编写了 rcu_barrier()，以便 Nikita 可以在卸载文件系统的过程中调用它。
    很久之后，当我在实现 rcutorture 时遇到了 RCU 模块卸载的问题，并发现 rcu_barrier() 同样解决了这个问题。
:ref:`返回快速测验 #1 <rcubarrier_quiz_1>`

.. _answer_rcubarrier_quiz_2:

快速测验 #2:
    为什么第 8 行不将 rcu_barrier_cpu_count 初始化为零，从而避免需要第 9 和 10 行？

答案:
    假设第 8 行所示的 on_each_cpu() 函数被延迟执行，使得 CPU 0 的 rcu_barrier_func() 已经执行并且相应的宽限期已经过去，而 CPU 1 的 rcu_barrier_func() 还没有开始执行。这会导致 rcu_barrier_cpu_count 被递减到零，从而使第 11 行的 wait_for_completion() 立即返回，未能等待 CPU 1 的回调函数被调用。
    注意，当 rcu_barrier() 代码最初在 2005 年添加时，这不是一个问题。这是因为 on_each_cpu() 禁用了抢占，这充当了一个 RCU 读取侧临界区，从而防止了 CPU 0 的宽限期在 on_each_cpu() 处理所有 CPU 之前完成。然而，随着可抢占 RCU 的引入，rcu_barrier() 不再在可抢占内核中的非抢占区域等待，这项任务由新的 rcu_barrier_sched() 函数来完成。
    然而，随着大约在 v4.20 版本左右的 RCU 版本整合，这种可能性再次被排除，因为整合后的 RCU 再次在非抢占区域等待。
    尽管如此，额外的计数仍然是个好主意。依赖于实现中的这些偶然性可能会在实现改变时导致以后的意外错误。
:ref:`返回快速测验 #2 <rcubarrier_quiz_2>`

.. _answer_rcubarrier_quiz_3:

快速测验 #3:
    如果 CPU 0 的 rcu_barrier_func() 立即执行（从而将 rcu_barrier_cpu_count 增加到值 1），但其他 CPU 的 rcu_barrier_func() 调用被延迟了一个完整的宽限期？这是否会导致 rcu_barrier() 提前返回？

答案:
    这种情况不会发生。原因是 on_each_cpu() 的最后一个参数，等待标志，被设置为 "1"。这个标志传递给 smp_call_function() 并进一步传递给 smp_call_function_on_cpu()，使后者自旋直到跨 CPU 调用的 rcu_barrier_func() 完成。这本身会防止在非 CONFIG_PREEMPTION 内核上完成宽限期，因为每个 CPU 必须经历上下文切换（或其他静止状态）才能完成宽限期。然而，在 CONFIG_PREEMPTION 内核中，这种情况是没有用的。
因此，在调用 smp_call_function() 期间以及在本地调用 rcu_barrier_func() 期间，on_each_cpu() 禁用了抢占。由于最近的 RCU 实现将禁用抢占的代码区域视为 RCU 的读取侧临界区，这会阻止宽限期完成。这意味着所有 CPU 在第一个 rcu_barrier_callback() 可能执行之前都已执行了 rcu_barrier_func()，从而防止 rcu_barrier_cpu_count 过早地变为零。

但如果 on_each_cpu() 今后决定不再禁用抢占，这可能是出于实时延迟考虑，那么将 rcu_barrier_cpu_count 初始化为一将会解决问题。

:ref:`返回快速测验 #3 <rcubarrier_quiz_3>`
