**-c**, **--cpus** *cpu-list*

        设置 osnoise 跟踪器在指定的 cpu-list 上运行采样线程

**-H**, **--house-keeping** *cpu-list*

        仅在给定的 cpu-list 上运行 rtla 控制线程

**-d**, **--duration** *time[s|m|h|d]*

        设置会话的持续时间

**-D**, **--debug**

        打印调试信息

**-e**, **--event** *sys:event*

        在跟踪（**-t**）会话中启用一个事件。参数可以是一个特定事件，例如 **-e** *sched:sched_switch*，或者一个系统组的所有事件，例如 **-e** *sched*。允许使用多个 **-e**。只有在设置了 **-t** 或 **-a** 时才有效

**--filter** *<filter>*

        使用 *<filter>* 过滤前面的 **-e** *sys:event* 事件。有关事件过滤的更多信息，请参阅 https://www.kernel.org/doc/html/latest/trace/events.html#event-filtering

**--trigger** *<trigger>*

        启用一个跟踪事件触发器到前面的 **-e** *sys:event* 事件。如果激活了 *hist:* 触发器，输出直方图将自动保存到名为 *system_event_hist.txt* 的文件中。
        
        例如，命令：

                rtla <command> <mode> -t -e osnoise:irq_noise --trigger="hist:key=desc,duration/1000:sort=desc,duration/1000:vals=hitcount"

        将自动将与 *osnoise:irq_noise* 事件相关的直方图内容保存到 *osnoise_irq_noise_hist.txt* 文件中。

        有关事件触发器的更多信息，请参阅 https://www.kernel.org/doc/html/latest/trace/events.html#event-triggers
**-P**, **--priority** *o:prio|r:prio|f:prio|d:runtime:period*

        为osnoise追踪线程设置调度参数，设置优先级的格式如下：

        - *o:prio* - 使用 SCHED_OTHER 并设置优先级为 *prio*；
        - *r:prio* - 使用 SCHED_RR 并设置优先级为 *prio*；
        - *f:prio* - 使用 SCHED_FIFO 并设置优先级为 *prio*；
        - *d:runtime[us|ms|s]:period[us|ms|s]* - 使用 SCHED_DEADLINE 并设置 *runtime* 和 *period*（以纳秒为单位）

**-C**, **--cgroup**\[=*cgroup*\]

        为追踪线程设置 *cgroup*。如果 **-C** 选项没有带参数传递，则追踪线程将继承 **rtla** 的 *cgroup*。否则，线程将被放置在通过该选项传递的 *cgroup* 中。

**--warm-up** *s*

        启动工作负载后，在开始收集数据之前让其运行 *s* 秒，以便系统预热。预热期间生成的统计数据将被丢弃。

**--trace-buffer-size** *kB*

        设置每个 CPU 的追踪缓冲区大小为 *kB*，用于追踪输出。

**-h**, **--help**

        打印帮助菜单。
