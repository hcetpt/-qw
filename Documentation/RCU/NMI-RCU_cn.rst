使用RCU保护动态NMI处理程序
=========================================

尽管RCU通常用于保护读取为主的的数据结构，但也可以使用RCU提供动态非屏蔽中断（NMI）处理程序以及动态IRQ处理程序。本文档描述了如何做到这一点，并且松散地参考了Zwane Mwaikambo在旧版本“arch/x86/kernel/traps.c”中的NMI计时器工作。相关的代码段如下所示，每个代码段后面都有简短的解释：

```c
static int dummy_nmi_callback(struct pt_regs *regs, int cpu)
{
    return 0;
}
```

`dummy_nmi_callback()` 函数是一个“虚拟”的NMI处理程序，它什么也不做，只是返回零，表示它没有执行任何操作，允许NMI处理程序采取默认的机器特定动作：

```c
static nmi_callback_t nmi_callback = dummy_nmi_callback;
```

`nmi_callback` 变量是一个指向当前NMI处理程序的全局函数指针：

```c
void do_nmi(struct pt_regs * regs, long error_code)
{
    int cpu;

    nmi_enter();

    cpu = smp_processor_id();
    ++nmi_count(cpu);

    if (!rcu_dereference_sched(nmi_callback)(regs, cpu))
        default_do_nmi(regs);

    nmi_exit();
}
```

`do_nmi()` 函数处理每个NMI。它首先像硬件中断那样禁用抢占，然后递增每个CPU的NMI计数。接着调用存储在 `nmi_callback` 函数指针中的NMI处理程序。如果该处理程序返回零，则 `do_nmi()` 调用 `default_do_nmi()` 函数来处理特定于机器的NMI。最后恢复抢占。

理论上，`rcu_dereference_sched()` 是不需要的，因为这段代码只运行在i386上，理论上也不需要 `rcu_dereference_sched()`。然而，在实践中，它是一个很好的文档辅助工具，特别是对于那些试图在Alpha系统或具有激进优化编译器的系统上实现类似功能的人。

快速问答：
为什么在Alpha系统上 `rcu_dereference_sched()` 可能是必要的，即使由指针引用的代码是只读的？

:ref:`快速问答答案 <answer_quick_quiz_NMI>`

回到关于NMI和RCU的讨论：

```c
void set_nmi_callback(nmi_callback_t callback)
{
    rcu_assign_pointer(nmi_callback, callback);
}
```

`set_nmi_callback()` 函数注册一个NMI处理程序。请注意，任何要被回调使用的数据必须在调用 `set_nmi_callback()` 之前初始化。在不按顺序写入架构的情况下，`rcu_assign_pointer()` 确保NMI处理程序看到已初始化的值：

```c
void unset_nmi_callback(void)
{
    rcu_assign_pointer(nmi_callback, dummy_nmi_callback);
}
```

此函数注销一个NMI处理程序，恢复原始的虚拟NMI处理程序。但是，可能有另一个CPU上的NMI处理程序正在执行。因此，在所有其他CPU完成执行之前，我们不能释放旧NMI处理程序使用的所有数据结构。

一种实现方法是通过 `synchronize_rcu()`，例如：

```c
unset_nmi_callback();
synchronize_rcu();
	kfree(my_nmi_data);
```

这是因为（截至v4.20）`synchronize_rcu()` 阻塞直到所有CPU完成它们正在执行的任何抢占禁用的代码段。
由于NMI处理程序禁用了抢占，`synchronize_rcu()` 保证不会在所有正在进行的NMI处理程序退出前返回。因此，在 `synchronize_rcu()` 返回后立即释放处理程序的数据是安全的。

重要说明：为了使这有效，所涉及的架构必须在NMI进入和退出时分别调用 `nmi_enter()` 和 `nmi_exit()`。

.. _answer_quick_quiz_NMI:

快速问答答案：
为什么在Alpha系统上 `rcu_dereference_sched()` 可能是必要的，即使由指针引用的代码是只读的？

调用 `set_nmi_callback()` 的代码可能已经初始化了一些新NMI处理程序将要使用的一些数据。在这种情况下，`rcu_dereference_sched()` 是必需的，否则某个CPU在设置新处理程序之后立刻接收到一个NMI时，可能会看到指向新NMI处理程序的指针，但看到的是处理程序数据的老版本。

同样的问题也可能发生在使用具有激进指针值推测优化的编译器的其他CPU上。（但请不要这样做！）

更重要的是，`rcu_dereference_sched()` 让阅读代码的人清楚指针是由RCU-sched保护的。
