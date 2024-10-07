###############
Timerlat Tracer
###############

Timerlat tracer 的目的是帮助抢占式内核开发者找到实时线程唤醒延迟的来源。与 cyclictest 类似，tracer 设置了一个周期性定时器来唤醒一个线程。然后该线程计算一个“唤醒延迟”值，即当前时间与定时器设置的绝对到期时间之间的差值。Timerlat 的主要目标是通过追踪方式帮助内核开发者。

使用方法
--------

将 ASCII 文本 "timerlat" 写入追踪系统的 current_tracer 文件（通常挂载在 /sys/kernel/tracing）
例如：

```
[root@f32 ~]# cd /sys/kernel/tracing/
[root@f32 tracing]# echo timerlat > current_tracer
```

可以通过读取追踪文件来跟踪：

```
[root@f32 tracing]# cat trace
# tracer: timerlat
#
#                               _-----=> irqs-off
#                              / _----=> need-resched
#                             | / _---=> hardirq/softirq
#                             || / _--=> preempt-depth
#                             || /
#                             ||||             ACTIVATION
#         TASK-PID      CPU# ||||   TIMESTAMP    ID            CONTEXT                LATENCY
#            | |         |   ||||      |         |                  |                       |
          <idle>-0       [000] d.h1    54.029328: #1     context    irq timer_latency       932 ns
           <...>-867     [000] ....    54.029339: #1     context thread timer_latency     11700 ns
          <idle>-0       [001] dNh1    54.029346: #1     context    irq timer_latency      2833 ns
           <...>-868     [001] ....    54.029353: #1     context thread timer_latency      9820 ns
          <idle>-0       [000] d.h1    54.030328: #2     context    irq timer_latency       769 ns
           <...>-867     [000] ....    54.030330: #2     context thread timer_latency      3070 ns
          <idle>-0       [001] d.h1    54.030344: #2     context    irq timer_latency       935 ns
           <...>-868     [001] ....    54.030347: #2     context thread timer_latency      4351 ns
```

该 tracer 在每个 CPU 上创建一个具有实时优先级的内核线程，在每次激活时打印两行信息。第一行是在线程激活前 *hardirq* 上下文中观察到的 *定时器延迟*。第二行是线程观察到的 *定时器延迟*。ACTIVATION ID 字段用于关联 *irq* 执行与其相应的 *thread* 执行。*irq*/*thread* 分割有助于明确高延迟值来自哪个上下文。*irq* 上下文可能因硬件相关操作（如 SMI、NMI、IRQ 或线程屏蔽中断）而延迟。一旦定时器触发，延迟也可能由线程引起的阻塞影响，例如通过 preempt_disable() 延迟调度执行、调度执行或屏蔽中断。线程还可能因其他线程和 IRQ 的干扰而延迟。

Tracer 选项
-------------

Timerlat tracer 基于 osnoise tracer 构建，因此其配置也在 osnoise/config 目录中完成。Timerlat 的配置项包括：

- cpus：将执行 timerlat 线程的 CPU 列表。
- timerlat_period_us：timerlat 线程的周期（微秒）。
- stop_tracing_us：如果 *irq* 上下文中的定时器延迟高于配置值，则停止系统追踪。写入 0 可禁用此选项。
- stop_tracing_total_us：如果 *thread* 上下文中的定时器延迟高于配置值，则停止系统追踪。写入 0 可禁用此选项。
```print_stack: 保存IRQ发生时的堆栈。堆栈在*线程上下文*事件之后打印，或者在遇到*stop_tracing_us*时在IRQ处理程序中打印。
timerlat 和 osnoise
----------------------------

timerlat 还可以利用 osnoise 的跟踪事件。例如：

        [root@f32 ~]# cd /sys/kernel/tracing/
        [root@f32 tracing]# echo timerlat > current_tracer
        [root@f32 tracing]# echo 1 > events/osnoise/enable
        [root@f32 tracing]# echo 25 > osnoise/stop_tracing_total_us
        [root@f32 tracing]# tail -10 trace
             cc1-87882   [005] d..h...   548.771078: #402268 context    irq timer_latency     13585 ns
             cc1-87882   [005] dNLh1..   548.771082: irq_noise: local_timer:236 start 548.771077442 duration 7597 ns
             cc1-87882   [005] dNLh2..   548.771099: irq_noise: qxl:21 start 548.771085017 duration 7139 ns
             cc1-87882   [005] d...3..   548.771102: thread_noise:      cc1:87882 start 548.771078243 duration 9909 ns
      timerlat/5-1035    [005] .......   548.771104: #402268 context thread timer_latency     39960 ns

在这种情况下，导致定时器延迟的根本原因不是单一的，而是多个因素造成的。首先，定时器 IRQ 被延迟了 13 微秒，这可能表明有一个较长的 IRQ 禁用段（参见 IRQ 堆栈跟踪部分）。然后，唤醒 timerlat 线程的定时器中断耗时 7597 纳秒，qxl:21 设备 IRQ 耗时 7139 纳秒。最后，cc1 线程噪声耗时 9909 纳秒才完成上下文切换。这些证据对于开发者来说非常有用，他们可以使用其他跟踪方法来找出如何调试和优化系统。值得注意的是，osnoise 事件报告的 *duration* 值是 *净* 值。例如，thread_noise 不包括由 IRQ 执行引起的开销（实际上占用了 12736 纳秒）。但是，timerlat 跟踪器（timerlat_latency）报告的值是 *毛* 值。
下图说明了一个 CPU 时间线，并展示了 timerlat 跟踪器在顶部观察到的情况以及 osnoise 事件在底部观察到的情况。时间线上每个 "-" 表示大约 1 微秒，时间向右移动 ==>

      外部     定时器 IRQ                     线程
       时钟        延迟                    延迟
       事件        13585 纳秒                  39960 纳秒
         |             ^                         ^
         v             |                         |
         |-------------|                         |
         |-------------+-------------------------|
                       ^                         ^
  ========================================================================
                    [定时器 IRQ]  [设备 IRQ]
  [另一个线程...^       v..^       v.......][定时器lat/线程]  <-- CPU 时间线
  =========================================================================
                    |-------|  |-------|
                            |--^       v-------|
                            |          |       |
                            |          |       + thread_noise: 9909 纳秒
                            |          +-> irq_noise: 6139 纳秒
                            +-> irq_noise: 7597 纳秒

IRQ 堆栈跟踪
---------------------------

当线程噪声是导致定时器延迟的主要因素时，osnoise/print_stack 选项非常有用，例如由于抢占或 IRQ 禁用。例如：

        [root@f32 tracing]# echo 500 > osnoise/stop_tracing_total_us
        [root@f32 tracing]# echo 500 > osnoise/print_stack
        [root@f32 tracing]# echo timerlat > current_tracer
        [root@f32 tracing]# tail -21 per_cpu/cpu7/trace
          insmod-1026    [007] dN.h1..   200.201948: irq_noise: local_timer:236 start 200.201939376 duration 7872 ns
          insmod-1026    [007] d..h1..   200.202587: #29800 context    irq timer_latency      1616 ns
          insmod-1026    [007] dN.h2..   200.202598: irq_noise: local_timer:236 start 200.202586162 duration 11855 ns
          insmod-1026    [007] dN.h3..   200.202947: irq_noise: local_timer:236 start 200.202939174 duration 7318 ns
          insmod-1026    [007] d...3..   200.203444: thread_noise:   insmod:1026 start 200.202586933 duration 838681 ns
      timerlat/7-1001    [007] .......   200.203445: #29800 context thread timer_latency    859978 ns
      timerlat/7-1001    [007] ....1..   200.203446: <堆栈跟踪>
  => timerlat_irq
  => __hrtimer_run_queues
  => hrtimer_interrupt
  => __sysvec_apic_timer_interrupt
  => asm_call_irq_on_stack
  => sysvec_apic_timer_interrupt
  => asm_sysvec_apic_timer_interrupt
  => delay_tsc
  => dummy_load_1ms_pd_init
  => do_one_initcall
  => do_init_module
  => __do_sys_finit_module
  => do_syscall_64
  => entry_SYSCALL_64_after_hwframe

在这种情况下，可以看到线程对 *定时器延迟* 的贡献最大，并且在 timerlat IRQ 处理程序期间保存的堆栈跟踪指向一个名为 dummy_load_1ms_pd_init 的函数，该函数的代码如下（故意设计）：

	static int __init dummy_load_1ms_pd_init(void)
	{
		preempt_disable();
		mdelay(1);
		preempt_enable();
		return 0;
	}

用户空间接口
---------------------------

Timerlat 允许用户空间线程使用 timerlat 架构来测量调度延迟。这个接口可以通过每个 CPU 的文件描述符访问，位于 $tracing_dir/osnoise/per_cpu/cpu$ID/timerlat_fd。此接口在以下条件下可用：

 - 启用了 timerlat 跟踪器
 - 设置了 osnoise 工作负载选项为 NO_OSNOISE_WORKLOAD
 - 用户空间线程绑定到单个处理器
 - 线程打开与其单个处理器关联的文件
 - 每次只有一个线程可以访问文件

如果这些条件中的任何一个不满足，open() 系统调用将会失败。打开文件描述符后，用户空间可以从其中读取数据。read() 系统调用将运行一段 timerlat 代码，该代码将在未来某个时刻启动定时器并等待它，就像常规内核线程一样。当定时器 IRQ 触发时，timerlat IRQ 将执行，报告 IRQ 延迟并唤醒正在 read 中等待的线程。线程会被调度并通过跟踪器报告线程延迟，就像内核线程一样。
```
与内核中的 `timerlat` 不同的是，`timerlat` 在返回到 `read()` 系统调用后，不会重新启动定时器。此时，用户可以运行任何代码。

如果应用程序再次读取 `timerlat` 文件描述符，跟踪器将报告从用户空间返回的延迟，这是总延迟。如果这是工作的结束阶段，可以将其解释为请求的响应时间。

在报告了总延迟之后，`timerlat` 将重新开始循环，启动一个定时器，并进入睡眠状态以等待下一次激活。

如果任何时候某个条件被打破，例如线程在用户空间中迁移，或者 `timerlat` 跟踪器被禁用，那么会向用户空间线程发送 `SIG_KILL` 信号。

下面是一个基本的用户空间代码示例：

```c
int main(void) {
    char buffer[1024];
    int timerlat_fd;
    int retval;
    long cpu = 0;   /* 指定在 CPU 0 上运行 */
    cpu_set_t set;

    CPU_ZERO(&set);
    CPU_SET(cpu, &set);

    if (sched_setaffinity(gettid(), sizeof(set), &set) == -1)
        return 1;

    snprintf(buffer, sizeof(buffer),
             "/sys/kernel/tracing/osnoise/per_cpu/cpu%ld/timerlat_fd",
             cpu);

    timerlat_fd = open(buffer, O_RDONLY);
    if (timerlat_fd < 0) {
        printf("打开 %s 时出错: %s\n", buffer, strerror(errno));
        exit(1);
    }

    for (;;) {
        retval = read(timerlat_fd, buffer, 1024);
        if (retval < 0)
            break;
    }

    close(timerlat_fd);
    exit(0);
}
```
