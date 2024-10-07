==================
OSNOISE 跟踪器
==================

在高性能计算（HPC）的背景下，操作系统噪声（*osnoise*）指的是由于操作系统内部活动导致的应用程序干扰。在 Linux 环境下，非屏蔽中断（NMIs）、中断请求（IRQs）、软中断（SoftIRQs）以及其他系统线程都可能对系统造成噪声。此外，与硬件相关的任务也可能引起噪声，例如，通过软件管理中断（SMIs）。hwlat_detector 是用来识别最复杂的噪声源——即“硬件噪声”的工具之一。简而言之，hwlat_detector 创建一个周期性运行的线程。在每个周期开始时，该线程会禁用中断并开始采样。运行过程中，hwlatd 线程会在循环中读取时间。由于中断被禁用，线程、IRQs 和 SoftIRQs 无法干扰 hwlatd 线程。因此，任何两次不同时间读取之间的时间间隔差异要么是由于 NMI 引起的，要么就是由硬件本身引起的。在周期结束时，hwlatd 会启用中断并报告所观察到的最大时间间隔。它还会打印出 NMI 发生次数计数器。如果输出没有报告 NMI 执行情况，则用户可以得出结论：延迟是由硬件引起的。hwlat 通过观察 NMI 的进入和退出来检测 NMI 的执行。

osnoise 跟踪器利用了 hwlat_detector 的类似循环机制，但允许抢占、SoftIRQs 和 IRQs 启用，从而允许所有 *osnoise* 源在其执行期间发挥作用。采用与 hwlat 相同的方法，osnoise 记录任何干扰源的进入和退出点，并增加每核干扰计数器。对于 NMI、IRQs、SoftIRQs 和线程，每当工具观察到这些干扰的进入事件时，相应的干扰计数器就会增加。当发生噪声且没有操作系统级别的干扰时，硬件噪声计数器会增加，指向硬件相关噪声。这样，osnoise 可以记录任何干扰源。在周期结束时，osnoise 跟踪器会打印所有噪声的总和、最大单个噪声、线程可用的 CPU 百分比以及噪声源的计数器。

使用方法
--------

将 ASCII 文本 "osnoise" 写入跟踪系统的 current_tracer 文件（通常挂载在 /sys/kernel/tracing）

例如：

```
[root@f32 ~]# cd /sys/kernel/tracing/
[root@f32 tracing]# echo osnoise > current_tracer
```

可以通过读取 trace 文件来跟踪结果：

```
[root@f32 tracing]# cat trace
# tracer: osnoise
#
#                                _-----=> irqs-off
#                               / _----=> need-resched
#                              | / _---=> hardirq/softirq
#                              || / _--=> preempt-depth                            MAX
#                              || /                                             SINGLE     Interference counters:
#                              ||||               RUNTIME      NOISE   % OF CPU  NOISE    +-----------------------------+
#           TASK-PID      CPU# ||||   TIMESTAMP    IN US       IN US  AVAILABLE  IN US     HW    NMI    IRQ   SIRQ THREAD
#              | |         |   ||||      |           |             |    |            |      |      |      |      |      |
                   <...>-859     [000] ....    81.637220: 1000000        190  99.98100       9     18      0   1007     18      1
                   <...>-860     [001] ....    81.638154: 1000000        656  99.93440      74     23      0   1006     16      3
                   <...>-861     [002] ....    81.638193: 1000000       5675  99.43250     202      6      0   1013     25     21
                   <...>-862     [003] ....    81.638242: 1000000        125  99.98750      45      1      0   1011     23      0
                   <...>-863     [004] ....    81.638260: 1000000       1721  99.82790     168      7      0   1002     49     41
                   <...>-864     [005] ....    81.638286: 1000000        263  99.97370      57      6      0   1006     26      2
                   <...>-865     [006] ....    81.638302: 1000000        109  99.98910      21      3      0   1006     18      1
                   <...>-866     [007] ....    81.638326: 1000000       7816  99.21840     107      8      0   1016     39     19
```

除了常规的跟踪字段（从 TASK-PID 到 TIMESTAMP），跟踪器还会在每个周期结束时为正在运行 osnoise/ 线程的每个 CPU 打印一条消息。osnoise 特定的字段报告如下：

- **RUNTIME IN US** 报告 osnoise 线程持续循环读取时间的微秒数。
- **NOISE IN US** 报告 osnoise 跟踪器在关联运行时间内观察到的噪声总和（以微秒为单位）。
- **% OF CPU AVAILABLE** 报告在运行时间内 osnoise 线程可用的 CPU 百分比。
- **MAX SINGLE NOISE IN US** 报告在运行时间内观察到的最大单个噪声。
- **Interference counters** 显示在运行时间内每种相应干扰发生的次数。
请注意，上面的例子显示了大量硬件噪声样本。
原因是这个样本是在虚拟机上采集的，宿主机的干扰被检测为硬件干扰。

Tracer 配置
--------------------

Tracer 在 osnoise 目录下有一组选项，它们是：

- osnoise/cpus：osnoise 线程将要执行的 CPU 列表
- osnoise/period_us：osnoise 线程的周期（微秒）
- osnoise/runtime_us：osnoise 线程寻找噪声的时间长度（微秒）
- osnoise/stop_tracing_us：如果发生单个噪声值高于配置值，则停止系统追踪。写入 0 表示禁用此选项
- osnoise/stop_tracing_total_us：如果总噪声值高于配置值，则停止系统追踪。写入 0 表示禁用此选项
- tracing_threshold：两次 time() 读取之间的最小差值，被视为噪声，单位为微秒。设置为 0 时，默认使用目前的值 1 微秒
- osnoise/options：一组可以启用或禁用的开关选项。通过向文件中写入选项名称来启用该选项，或者通过写入带有 "NO_" 前缀的选项名称来禁用该选项。例如，写入 "NO_OSNOISE_WORKLOAD" 将禁用 OSNOISE_WORKLOAD 选项。特殊的 "DEFAULTS" 选项会将所有选项重置为默认值

Tracer 选项
--------------

osnoise/options 文件提供了一组用于 osnoise Tracer 的开关配置选项。这些选项包括：

- DEFAULTS：将选项重置为默认值
- OSNOISE_WORKLOAD：不调度 osnoise 工作负载（详见下面的专用部分）
- PANIC_ON_STOP：如果追踪器停止，则调用 panic()。此选项用于捕获 vmcore
- OSNOISE_PREEMPT_DISABLE：在运行 osnoise 工作负载时禁用抢占，仅允许 IRQ 和与硬件相关的噪声
- OSNOISE_IRQ_DISABLE：在运行 osnoise 工作负载时禁用 IRQ，仅允许 NMI 和与硬件相关的噪声，如 hwlat 追踪器

附加追踪
----------

除了追踪器外，还添加了一组追踪点以帮助识别 osnoise 的来源：
- osnoise:sample_threshold：每当噪声超过可配置的容忍值（tolerance_ns）时打印
- osnoise:nmi_noise：来自 NMI 的噪声，包括持续时间
- osnoise:irq_noise：来自 IRQ 的噪声，包括持续时间
- osnoise:softirq_noise：来自 SoftIRQ 的噪声，包括持续时间
- osnoise:thread_noise：来自线程的噪声，包括持续时间
请注意，所有值都是*净值*。例如，如果在`osnoise`运行时，另一个线程抢占了`osnoise`线程，它将在开始时启动一个`thread_noise`持续时间。然后，中断（IRQ）发生，抢占了`thread_noise`，启动了一个`irq_noise`。当中断执行结束时，它会计算其持续时间，并从`thread_noise`中减去这个持续时间，以避免对中断执行的双重计数。这种逻辑适用于所有噪声源。

以下是一个使用这些追踪点的例子：

```
       osnoise/8-961     [008] d.h.  5789.857532: irq_noise: local_timer:236 start 5789.857529929 duration 1845 ns
       osnoise/8-961     [008] dNh.  5789.858408: irq_noise: local_timer:236 start 578404871 duration 2848 ns
     migration/8-54      [008] d...  5789.858413: thread_noise: migration/8:54 start 5789.858409300 duration 3068 ns
       osnoise/8-961     [008] ....  5789.858413: sample_threshold: start 5789.858404555 duration 8812 ns interferences 2
```

在这个例子中，最后一行报告了一个8微秒的噪声样本，并指出了两次干扰。回溯追踪记录，之前的两条记录是关于定时器中断执行后迁移线程的运行。第一个事件不属于噪声，因为它发生在一毫秒之前。
值得注意的是，追踪点中报告的持续时间之和小于在`sample_threshold`中报告的8微秒。
原因在于任何干扰执行前后都有入口和出口代码开销。这解释了双轨方法：测量线程和追踪。

无工作负载运行osnoise追踪器
-------------------------------

通过设置NO_OSNOISE_WORKLOAD选项启用osnoise追踪器，`osnoise:` 追踪点用于测量任何类型Linux任务的执行时间，不受其他任务的干扰。
