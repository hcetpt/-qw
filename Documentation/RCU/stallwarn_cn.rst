SPDX 许可证标识符: GPL-2.0

==============================
使用 RCU 的 CPU 停滞检测器
==============================

本文档首先讨论了 RCU 的 CPU 停滞检测器能够发现的问题类型，然后讨论了可以用来微调检测器操作的内核参数和 Kconfig 选项。最后，本文档解释了停滞检测器的“splat”格式。

什么会导致 RCU CPU 停滞警告？
===================================

你的内核打印出了一个 RCU CPU 停滞警告。接下来的问题是“是什么导致了这个问题？”以下问题可能导致 RCU CPU 停滞警告：

- 一个 CPU 在 RCU 读侧临界区中循环
- 一个 CPU 在中断被禁用的情况下循环
- 一个 CPU 在抢占被禁用的情况下循环
- 一个 CPU 在下半部被禁用的情况下循环
- 对于 !CONFIG_PREEMPTION 内核，一个 CPU 在内核中的任何地方循环而没有可能调用 schedule()。如果在内核中的循环确实是预期且期望的行为，你可能需要添加一些 cond_resched() 调用
- 使用过慢的控制台连接启动 Linux，无法跟上启动时的控制台消息速率。例如，115Kbaud 的串行控制台可能远远跟不上启动时的消息速率，并且经常会导致 RCU CPU 停滞警告消息。特别是如果你添加了调试用的 printk() 调用
- 任何阻止 RCU 的恩典期 kthreads 运行的情况
这可能会导致“所有 QS 已见”的控制台日志消息
该消息将包含 kthread 上次运行的时间及其预期运行频率的信息。这也可能导致控制台日志消息“rcu_.*kthread starved for”，其中将包含额外的调试信息。
- 在一个启用了 CONFIG_PREEMPTION 的内核中，一个CPU密集型的实时任务可能会在RCU读侧临界区中间抢占一个低优先级的任务。如果这个低优先级的任务不允许在其他任何CPU上运行，那么下一个RCU优雅周期将永远无法完成，最终会导致系统内存耗尽并挂起。在系统耗尽内存的过程中，你可能会看到停顿警告信息。

- 在一个启用了 CONFIG_PREEMPT_RT 的内核中，一个优先级高于RCU软中断线程的CPU密集型实时任务。这会阻止RCU回调被调用，并且在一个启用了 CONFIG_PREEMPT_RCU 的内核中，还会进一步阻止RCU优雅周期的完成。无论如何，系统最终会耗尽内存并挂起。在启用了 CONFIG_PREEMPT_RCU 的情况下，你可能会看到停顿警告信息。
你可以使用 rcutree.kthread_prio 内核启动参数来提高RCU的kthread调度优先级，这有助于避免这个问题。但是，请注意这样做可能会增加系统的上下文切换率，从而降低性能。

- 一个处理时间超过相邻两次中断之间的时间间隔的周期性中断。这会阻止RCU的kthread和软中断处理程序运行。
请注意，某些高开销的调试选项（例如函数图跟踪器）可能会导致中断处理程序比正常情况下花费更长时间，进而导致RCU CPU停顿警告。

- 在快速系统上测试工作负载，将停顿警告超时调整到刚好避免RCU CPU停顿警告的程度，然后在同一台慢速系统上运行相同的工作负载和相同的停顿警告超时。请注意，热节流和按需管理器可能会导致同一系统有时快有时慢！

- 硬件或软件问题导致在一个未处于dyntick-idle模式的CPU上关闭了调度时钟中断。这个问题确实发生过，并且最有可能导致启用了 CONFIG_NO_HZ_COMMON=n 的内核出现RCU CPU停顿警告。

- 硬件或软件问题导致基于时间的唤醒无法发生。这些问题可能包括配置错误或有缺陷的定时器硬件、中断或异常路径中的bug（无论是硬件、固件还是软件）、Linux定时器子系统中的bug、调度器中的bug，甚至包括RCU本身的bug。这也可能导致控制台日志消息“rcu_.*timer wakeup didn't happen for”，其中包含额外的调试信息。

- 一个低级别的内核问题，要么未能调用 rcu_eqs_enter(true)、rcu_eqs_exit(true)、ct_idle_enter()、ct_idle_exit()、ct_irq_enter() 或 ct_irq_exit() 中的一个变体，要么调用了其中一个变体太多次。
历史上，最常见的问题是遗漏了 `irq_enter()` 或 `irq_exit()` 的调用，而这两个函数分别会调用 `ct_irq_enter()` 和 `ct_irq_exit()`。使用 `CONFIG_RCU_EQS_DEBUG=y` 编译内核可以帮助追踪这些类型的问题，这些问题有时会在架构特定的代码中出现。

- RCU 实现中的一个错误。
- 硬件故障。这种情况虽然不太可能，但在大型数据中心中并不少见。在几十年前的一个典型案例中，一台正在运行的系统的 CPU 发生故障，变得无响应，但没有立即崩溃。这导致了一系列的 RCU CPU 停滞警告，最终发现是 CPU 故障。

RCU、RCU-sched、RCU-tasks 和 RCU-tasks-trace 实现中有 CPU 停滞警告。请注意，SRCU 没有 CPU 停滞警告。

请注意，RCU 只有在进行宽限期时才能检测到 CPU 停滞。没有宽限期，就没有 CPU 停滞警告。

为了诊断停滞的原因，请检查堆栈跟踪。有问题的函数通常位于堆栈的顶部。

如果你有一系列来自单个长时间停滞的警告，比较堆栈跟踪通常有助于确定停滞发生的位置，这通常是在堆栈中保持不变的部分中最接近顶部的函数。

如果你能够可靠地触发停滞，ftrace 非常有帮助。RCU 错误通常可以通过 `CONFIG_RCU_TRACE` 和 RCU 的事件跟踪来调试。关于 RCU 事件跟踪的信息，请参阅 `include/trace/events/rcu.h`。
调整 RCU CPU 停滞检测器
======================================

`rcuupdate.rcu_cpu_stall_suppress` 模块参数禁用 RCU 的 CPU 停滞检测器，该检测器用于检测导致 RCU 宽限期过度延迟的条件。此模块参数默认启用 CPU 停滞检测，但可以通过启动时参数或通过 sysfs 在运行时覆盖。

停滞检测器对“过度延迟”的定义由一组内核配置变量和 C 预处理宏控制：

### CONFIG_RCU_CPU_STALL_TIMEOUT
该内核配置参数定义了 RCU 从宽限期开始到发出 CPU 停滞警告的时间间隔。这个时间通常是 21 秒。
此配置参数可以通过 `/sys/module/rcupdate/parameters/rcu_cpu_stall_timeout` 在运行时更改，但在每个周期开始时才会检查。
因此，如果你在一个 40 秒的停滞中已经过去了 10 秒，将此 sysfs 参数设置为（例如）5 秒将会缩短下一个停滞的超时时间，或者在当前停滞中的下一个警告（前提是停滞持续足够长）。它不会影响当前停滞的下一个警告的时间。

停滞警告信息可以通过 `/sys/module/rcupdate/parameters/rcu_cpu_stall_suppress` 完全启用或禁用。

### CONFIG_RCU_EXP_CPU_STALL_TIMEOUT
与 `CONFIG_RCU_CPU_STALL_TIMEOUT` 参数相同，但仅适用于快速宽限期。此参数定义了 RCU 从快速宽限期开始到发出 CPU 停滞警告的时间间隔。在 Android 设备上，这个时间通常是 20 毫秒。零值会导致使用 `CONFIG_RCU_CPU_STALL_TIMEOUT` 的值（转换为毫秒）。
此配置参数可以通过 `/sys/module/rcupdate/parameters/rcu_exp_cpu_stall_timeout` 在运行时更改，但在每个周期开始时才会检查。如果你正处于一个当前的停滞周期，将其设置为新值会改变下一个停滞的超时时间。
停滞警告信息可以通过 `/sys/module/rcupdate/parameters/rcu_cpu_stall_suppress` 完全启用或禁用。

### RCU_STALL_DELAY_DELTA
尽管 lockdep 设施非常有用，但它确实增加了一些开销。因此，在 `CONFIG_PROVE_RCU` 下，`RCU_STALL_DELAY_DELTA` 宏允许在发出 RCU CPU 停滞警告消息之前额外等待五秒钟。（这是一个 C 预处理宏，不是内核配置参数。）

### RCU_STALL_RAT_DELAY
CPU 停滞检测器试图让出现问题的 CPU 打印自己的警告，因为这通常会提供更好的堆栈跟踪质量。
然而，如果出现问题的 CPU 在指定的 `RCU_STALL_RAT_DELAY` 中没有检测到自己的停滞，则其他 CPU 将发出警告。此延迟通常设置为两个滴答。 （这是一个 C 预处理宏，不是内核配置参数。）

### rcupdate.rcu_task_stall_timeout
此启动/sysfs 参数控制 RCU-tasks 和 RCU-tasks-trace 的停滞警告间隔。零或更小的值会抑制 RCU-tasks 的停滞警告。正数设置停滞警告间隔（以秒为单位）。RCU-tasks 的停滞警告以以下行开头：

    INFO: rcu_tasks detected stalls on tasks:

然后继续输出每个导致当前 RCU-tasks 宽限期停滞的任务的 `sched_show_task()` 输出。
RCU-tasks-trace 停滞警告的开始（并持续）情况类似：

		INFO: rcu_tasks_trace 检测到任务上的停滞

解读 RCU 的 CPU 停滞检测器“Splats”
===================================

对于非 RCU-tasks 版本的 RCU，当某个 CPU 检测到其他 CPU 出现停滞时，它会打印类似以下的消息：

	INFO: rcu_sched 检测到 CPU/task 上的停滞：
	2-...: （落后 3 个 GP）idle=06c/0/0 softirq=1453/1455 fqs=0
	16-...: （当前 GP 无中断）idle=81c/0/0 softirq=764/764 fqs=0
	（由 32 检测，t=2603 jiffies, g=7075, q=625）

此消息表示 CPU 32 检测到 CPU 2 和 CPU 16 都导致了停滞，并且该停滞影响到了 RCU-sched。此消息通常会跟着每个 CPU 的堆栈转储。请注意，PREEMPT_RCU 构建不仅会被任务所停滞，还会被 CPU 所停滞，并且这些任务将通过 PID 表示，例如 “P3421”。甚至可能出现一个 rcu_state 停滞是由 CPU 和任务共同引起的，在这种情况下，所有有问题的 CPU 和任务都会在列表中被指出。有时，CPU 会检测到自身停滞，这将导致自我检测到的停滞。

CPU 2 的 “(3 GPs behind)” 表明该 CPU 在过去三个 GP 中没有与 RCU 核心进行交互。相反，CPU 16 的 “(0 ticks this GP)” 表明该 CPU 在当前停滞的 GP 中没有处理任何调度时钟中断。

消息中的 “idle=” 部分显示了 dyntick-idle 状态。
第一个 “/” 前面的十六进制数字是 dynticks 计数器的低阶 12 位，如果 CPU 处于 dyntick-idle 模式，则该值为偶数，否则为奇数。两个 “/” 之间的十六进制数字是嵌套值，如果处于空闲循环（如上所示），则为较小的非负数，否则为非常大的正数。最后一个 “/” 后面的数字是 NMI 嵌套值，通常为较小的非负数。

消息中的 “softirq=” 部分跟踪停滞 CPU 执行的 RCU 软中断处理器的数量。 “/” 前面的数字是在此 CPU 最后一次注意到 GP 开始时自启动以来执行的数量，可能是当前（停滞的）GP，也可能是更早的 GP（例如，如果 CPU 可能在较长时间内处于 dyntick-idle 模式）。 “/” 后面的数字是从启动到当前时间执行的数量。如果这个数字在重复的停滞警告消息中保持不变，可能表明 RCU 的软中断处理器无法在此 CPU 上执行。这可能会发生在停滞的 CPU 以关闭中断的方式自旋时，或者在 -rt 内核中，高优先级进程使 RCU 的软中断处理器饥饿。

“fqs=” 显示了自上次 CPU 注意到 GP 开始以来，GP kthread 在此 CPU 上进行了多少次强制静默状态空闲/离线检测。

“detected by” 行指出了哪个 CPU 检测到了停滞（在这种情况下是 CPU 32），从 GP 开始以来经过了多少个 jiffies（在这种情况下为 2603），GP 序列号（7075），以及估计的所有 CPU 上排队的 RCU 回调总数（在这种情况下为 625）。

如果 GP 结束刚好在停滞警告开始打印时，将会出现一个虚假的停滞警告消息，其中包括以下内容：

	INFO: 停滞在状态转储开始前结束

这种情况很少见，但在实际生活中确实会发生。此外，根据停滞警告和 GP 初始化的交互方式，也可能在这种情况下标记零 jiffies 的停滞。请注意，不使用像 stop_machine() 这样的方法是不可能完全消除这种误报的，而这种方法对于此类问题来说有些过头了。

如果所有 CPU 和任务都已通过静默状态，但 GP 仍然未能结束，停滞警告的 “Splats” 将包括以下内容：

	所有 QS 已经看到，最近一次 rcu_preempt kthread 活动为 23807（4297905177-4297881370），jiffies_till_next_fqs=3，root ->qsmask 0x0

“23807” 表示自 GP kthread 运行以来已经超过 23 千个 jiffies。“jiffies_till_next_fqs” 表示该 kthread 应该运行的频率，即两次强制静默状态扫描之间的时间间隔，在这种情况下为 3，远小于 23807。最后，打印出根 rcu_node 结构的 ->qsmask 字段，通常为零。
如果相关的宽限期kthread在出现停顿警告之前未能运行，就像上面“所有QS已通过”行的情况一样，将会打印以下附加行：

```
rcu_sched kthread 在 23807 个时钟滴答内未获得足够CPU时间！g7075 f0x0 RCU_GP_WAIT_FQS(3) ->state=0x1 ->cpu=5
除非 rcu_sched kthread 获得足够的CPU时间，否则现在预期会发生内存不足（OOM）情况。
```

使宽限期kthread缺乏CPU时间当然会导致即使所有CPU和任务都已通过所需的静默状态，仍会出现RCU CPU停顿警告。其中的“g”数字显示当前的宽限期序列号，“f”前面是发送给宽限期kthread的`->gp_flags`命令，“RCU_GP_WAIT_FQS”表示kthread正在等待一个短暂的超时，“state”前面是`task_struct ->state`字段的值，“cpu”表示宽限期kthread最后在CPU 5上运行。

如果相关宽限期kthread在合理的时间内没有从FQS等待中唤醒，则会打印以下附加行：

```
kthread 定时器唤醒在 23804 个时钟滴答内未发生！g7076 f0x0 RCU_GP_WAIT_FQS(5) ->state=0x402
```

其中的“23804”表示kthread的定时器在超过23000个时钟滴答前已经过期。其余部分与kthread饥饿情况中的含义相似。

此外，还会打印以下行：

```
可能的定时器处理问题出现在 cpu=4 上，timer-softirq=11142
```

这里的“cpu”表示宽限期kthread最后在CPU 4上运行，在那里它排队了FQS定时器。“timer-softirq”后面的数字是cpu 4上的当前`TIMER_SOFTIRQ`计数。如果此值在连续的RCU CPU停顿警告中不变，则进一步怀疑存在定时器问题。

这些消息通常会伴随着涉及停顿的CPU和任务的堆栈转储。这些堆栈跟踪可以帮助您找到停顿的原因，请注意检测停顿的CPU将有一个主要致力于检测停顿的中断帧。

### 同一停顿的多个警告

如果停顿持续足够长的时间，将为该停顿打印多个停顿警告消息。第二个及之后的消息将以更长的间隔打印，因此第一个和第二个消息之间的时间大约是停顿开始到第一个消息之间时间的三倍。比较同一停顿期间不同消息的堆栈转储可能会有所帮助。

### 加速宽限期的停顿警告

如果加速宽限期检测到停顿，它将在dmesg中放置一条类似以下的消息：

```
INFO: rcu_sched 检测到在 CPUs/tasks: { 7-... } 的加速停顿 21119 个时钟滴答 s: 73 root: 0x2/
```

这表明CPU 7未能响应重新调度IPI。CPU编号后的三个点（".")表示该CPU在线（否则第一个点将是“O”），该CPU在加速宽限期开始时在线（否则第二个点将是“o”），并且自启动以来该CPU至少在线过一次（否则第三个点将是“N”）。"jiffies"前的数字表示加速宽限期已持续了21,119个时钟滴答。“s:”后的数字表示加速宽限期序列计数器为73。最后一个值为奇数表示有一个加速宽限期正在进行。“root:”后的数字是一个位掩码，指示根rcu_node结构的哪些子节点对应于阻止当前加速宽限期的CPU和/或任务。如果树有超过一层，则会为其他rcu_node结构的状态打印额外的十六进制数字。

与正常的宽限期一样，PREEMPT_RCU构建可以被任务以及CPU停顿，并且这些任务将通过PID指示，例如，“P3421”。
完全有可能在同一运行过程中，在正常和快速宽限期期间几乎同时看到停顿警告。
RCU_CPU_STALL_CPUTIME
=====================

在使用CONFIG_RCU_CPU_STALL_CPUTIME=y编译或使用rcupdate.rcu_cpu_stall_cputime=1启动的内核中，每个RCU CPU停顿警告都会提供以下附加信息：

```
rcu:          hardirqs   softirqs   csw/system
rcu:  number:      624         45            0
rcu: cputime:       69          1         2425   ==> 2500(ms)
```

这些统计信息是在采样期间收集的。“number:”行中的值分别表示停顿CPU上的硬中断数、软中断数和上下文切换次数。 “cputime:”行中的前三个值分别表示硬中断、软中断和任务消耗的CPU时间（以毫秒为单位）。最后一个数字是测量间隔，同样以毫秒为单位。由于用户模式任务通常不会导致RCU CPU停顿，因此这些任务通常是内核任务，这就是为什么只考虑系统CPU时间的原因。

采样期间如下所示：

```
|<------------first timeout---------->|<-----second timeout----->|
|<--half timeout-->|<--half timeout-->|                          |
|                  |<--first period-->|                          |
|                  |<-----------second sampling period---------->|
|                  |                  |                          |
             snapshot time point    1st-stall                  2nd-stall
```

以下是四种典型场景的描述：

1. 一个禁用中断循环的CPU
```
rcu:          hardirqs   softirqs   csw/system
rcu:  number:        0          0            0
rcu: cputime:        0          0            0   ==> 2500(ms)
```

由于在整个测量间隔期间禁用了中断，因此没有中断也没有上下文切换。此外，由于通过中断处理程序测量CPU时间消耗，系统CPU消耗被误导性地测量为零。在这种情况下，通常还会在此CPU的摘要行上打印“(0 ticks this GP)”。

2. 一个禁用下半部的CPU
这与前面的例子类似，但硬中断数量和消耗的CPU时间非零，以及内核执行消耗的CPU时间也非零：
```
rcu:          hardirqs   softirqs   csw/system
rcu:  number:      624          0            0
rcu: cputime:       49          0         2446   ==> 2500(ms)
```

软中断数为零表明它们可能已被禁用，例如通过local_bh_disable()。当然，也有可能没有软中断，因为所有可能导致软中断执行的事件都被限制在其他CPU上。在这种情况下，应继续进行诊断，如下一个示例所示。

3. 一个禁用抢占的CPU
这里，只有上下文切换次数为零：
```
rcu:          hardirqs   softirqs   csw/system
rcu:  number:      624         45            0
rcu: cputime:       69          1         2425   ==> 2500(ms)
```

这种情况表明停顿的CPU可能是在禁用抢占的情况下循环的。
4. 没有循环，但存在大量的硬中断和软中断

```
rcu:          硬中断    软中断    上下文切换/系统
rcu:  数量:       xx         xx            0
rcu:  CPU时间:       xx         xx            0   ==> 2500(ms)
```

这里，硬中断的数量和CPU时间都不为零，但是上下文切换次数和内核消耗的CPU时间都为零。软中断的数量和CPU时间通常不为零，但在某些情况下也可能为零，例如当CPU在一个硬中断处理程序中自旋时。

如果这种类型的RCU CPU停顿警告可以复现，可以通过查看 `/proc/interrupts` 或编写代码来追踪每个中断（例如参考 `show_interrupts()` 函数）来缩小问题范围。
