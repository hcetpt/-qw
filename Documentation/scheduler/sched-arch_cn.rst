CPU调度程序实现提示（针对特定架构的代码）

Nick Piggin, 2005

上下文切换
==========
1. 运行队列锁定
默认情况下，switch_to 架构函数是在运行队列被锁定的情况下调用的。这通常不是问题，除非 switch_to 需要获取运行队列锁。这通常是由于上下文切换中的唤醒操作。
为了请求调度器在运行队列未锁定的情况下调用 switch_to，你必须在头文件中（通常是定义 switch_to 的头文件）使用 `#define __ARCH_WANT_UNLOCKED_CTXSW`。
未锁定的上下文切换在 CONFIG_SMP 情况下只会对核心调度器实现引入非常轻微的性能损失。

CPU 空闲
========
你的 cpu_idle 例程需要遵守以下规则：

1. 现在空闲例程期间应该禁用抢占。仅在调用 schedule() 时启用，然后再次禁用。
2. need_resched/TIF_NEED_RESCHED 只会被设置，并且直到正在运行的任务调用 schedule() 之前都不会被清除。空闲线程只需查询 need_resched，而不能设置或清除它。
3. 当 cpu_idle 发现 (need_resched() == 'true') 时，应调用 schedule()。否则不应调用 schedule()。
4. 在检查 need_resched 时唯一需要禁用中断的情况是我们即将让处理器休眠直到下一个中断（这不会提供对 need_resched 的保护，而是防止丢失一个中断）：
   
   4a. 这种类型的休眠常见的问题是：

       ```
           local_irq_disable();
           if (!need_resched()) {
               local_irq_enable();
               *** 此处到达重新调度中断 ***
               __asm__("sleep until next interrupt");
           }
       ```

5. TIF_POLLING_NRFLAG 可以由不需要中断来唤醒的空闲例程设置，当 need_resched 变为高电平时。
换句话说，它们必须周期性地轮询 need_resched，尽管可以合理地执行一些后台工作或进入低 CPU 优先级。
- 5a. 如果设置了 TIF_POLLING_NRFLAG，并且我们确实决定进入中断睡眠，则需要先清除它，然后发出内存屏障（接着如第 3 条所述，在禁用中断的情况下测试 need_resched）。

arch/x86/kernel/process.c 中有轮询和睡眠空闲函数的例子。
可能的架构问题
=======================

我找到的可能的架构问题（以及尝试修复或未修复的问题）：

sparc - 此时中断已开启(？)，将 local_irq_save 更改为 _disable
- 待办事项：需要次级 CPU 禁用抢占（参见 #1）
