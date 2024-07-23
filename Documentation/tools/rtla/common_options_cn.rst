**-c**, **--cpus** *cpu-list*

        设置 osnoise 追踪器以在指定的 *cpu-list* 中运行采样线程。

**-H**, **--house-keeping** *cpu-list*

        仅在给定的 *cpu-list* 上运行 rtla 控制线程。

**-d**, **--duration** *time[s|m|h|d]*

        设置会话的持续时间。

**-D**, **--debug**

        打印调试信息。

**-e**, **--event** *sys:event*

        在追踪（**-t**）会话中启用一个事件。参数可以是一个特定事件，例如，**-e** *sched:sched_switch*，或者是一个系统组的所有事件，例如，**-e** *sched*。允许使用多个 **-e**。只有在设置了 **-t** 或 **-a** 时才有效。

**--filter** *<filter>*

        使用 *<filter>* 对上一个 **-e** *sys:event* 事件进行过滤。关于事件过滤的更多信息，请参见 https://www.kernel.org/doc/html/latest/trace/events.html#event-filtering

**--trigger** *<trigger>*

        向上一个 **-e** *sys:event* 启用一个追踪事件触发器。
        如果启用了 *hist:* 触发器，则输出直方图将自动保存到名为 *system_event_hist.txt* 的文件中。
        例如，命令：

        rtla <command> <mode> -t -e osnoise:irq_noise --trigger="hist:key=desc,duration/1000:sort=desc,duration/1000:vals=hitcount"

        将自动将与 *osnoise:irq_noise* 事件关联的直方图内容保存到 *osnoise_irq_noise_hist.txt* 文件中。
        关于事件触发器的更多信息，请参见 https://www.kernel.org/doc/html/latest/trace/events.html#event-triggers
**-P**, **--priority** *o:prio|r:prio|f:prio|d:runtime:period*

设置操作系统噪声追踪线程的调度参数，设置优先级的格式为：

- *o:prio* - 使用SCHED_OTHER与*prio*；
- *r:prio* - 使用SCHED_RR与*prio*；
- *f:prio* - 使用SCHED_FIFO与*prio*；
- *d:runtime[us|ms|s]:period[us|ms|s]* - 使用SCHED_DEADLINE，其中*runtime*和*period*以纳秒为单位

**-C**, **--cgroup** [*=cgroup*]

为追踪器的线程设置*cgroup*。如果**-C**选项在没有参数的情况下传递，则追踪器的线程将继承**rtla**的*cgroup*。否则，线程将被放置在传递给该选项的*cgroup*中。

**--warm-up** *s*

启动工作负载后，让其运行*s*秒再开始收集数据，允许系统预热。预热期间生成的统计数据会被丢弃。

**--trace-buffer-size** *kB*

设置每个CPU的追踪缓冲区大小（以kB为单位）用于追踪输出。

**-h**, **--help**

打印帮助菜单。
