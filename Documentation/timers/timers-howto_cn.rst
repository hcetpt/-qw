### 延迟 — 关于各种内核延迟/休眠机制的信息

本文旨在回答一个常见的问题：“正确的延迟方法是什么？”

这个问题通常由需要处理硬件延迟的驱动程序编写者提出，而他们可能对Linux内核的内部工作原理并不十分熟悉。

#### 插入延迟

首先，也是最重要的一点，你需要问自己：“我的代码是否在原子上下文中？”紧接着应该问：“它真的需要在原子上下文中延迟吗？”如果答案是肯定的……

##### 原子上下文：
    你必须使用`*delay`系列函数。这些函数使用jiffies来估计时钟速度，并忙等待足够的循环周期以实现所需的延迟：

    ndelay(unsigned long nsecs)  
    udelay(unsigned long usecs)  
    mdelay(unsigned long msecs)

    udelay通常是首选API；在许多非PC设备上，ndelay级别的精度可能并不存在。
    mdelay是udelay的宏包装器，用于处理传递给udelay的大参数。
    一般来说，不建议使用mdelay，并且应重构代码以允许使用msleep。

##### 非原子上下文：
    你应该使用`*sleep[_range]`系列函数。
    这里有几个选项，虽然它们都可能正确工作，但使用“正确的”休眠函数将有助于调度器、电源管理和提高你的驱动程序质量。

    -- 通过忙等待循环支持：

        udelay(unsigned long usecs)

    -- 通过高精度定时器（hrtimers）支持：

        usleep_range(unsigned long min, unsigned long max)

    -- 通过jiffies/传统定时器支持：

        msleep(unsigned long msecs)  
        msleep_interruptible(unsigned long msecs)

    与`*delay`系列不同，每个调用的底层机制各不相同，因此有一些需要注意的细节。

##### 休眠几微秒（< ~10us？）：
    * 使用udelay

    - 为什么不使用usleep？
        在较慢的系统上（嵌入式系统或可能是降速的PC），设置usleep的hrtimers开销可能不值得。这种评估显然取决于具体情况，但这是需要注意的一点。

##### 休眠几十微秒到几十毫秒（10us - 20ms）：
    * 使用usleep_range

    - 为什么不使用msleep（1ms - 20ms）？
        最初解释在这里：
            https://lore.kernel.org/r/15327.1186166232@lwn.net

        msleep(1~20)可能不会按调用者的意图工作，并且通常会睡得更久（对于1~20ms范围内的任何值，实际休眠时间约为20ms）。在许多情况下，这不是期望的行为。
    - 为什么没有“usleep”？/ 什么是好的范围？
        由于usleep_range基于hrtimers构建，唤醒将非常精确（接近精确），因此简单的usleep函数可能会引入大量不必要的中断。
随着区间（range）的引入，调度器可以自由地将你的唤醒与因其他原因发生的任何其他唤醒合并，或者在最坏的情况下，为你的上限触发一个中断。你提供的区间越大，不触发中断的可能性就越大；这应该与你特定代码路径所能接受的最大延迟/性能进行权衡。这里的精确容差是非常具体的情况，因此由调用者来确定合理的区间。

对于较长毫秒级的睡眠（10ms以上）
    * 使用msleep或可能的msleep_interruptible

    - 它们有什么区别？
        msleep将当前任务设置为TASK_UNINTERRUPTIBLE状态，而msleep_interruptible则将当前任务设置为TASK_INTERRUPTIBLE状态后再安排睡眠。简而言之，两者的区别在于睡眠是否可以通过信号提前结束。一般来说，除非你知道你需要可中断变体，否则直接使用msleep即可。

灵活的睡眠（任意延迟，不可中断）
    * 使用fsleep
