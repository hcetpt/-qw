========================
ftrace - 函数追踪器
========================

版权所有 2008 红帽公司
:作者:   Steven Rostedt <srostedt@redhat.com>
:许可:  GNU 自由文档许可证，版本 1.2
         （同时在 GPL v2 下授权）
:原始审阅者:  Elias Oltmanns, Randy Dunlap, Andrew Morton,
              John Kacur 和 David Teigland
- 编写于：2.6.28-rc2
- 更新于：3.10
- 更新于：4.13 - 版权所有 2017 VMware Inc. Steven Rostedt
- 转换为 rst 格式 - Changbin Du <changbin.du@intel.com>

简介
------------

ftrace 是一个内部追踪器，旨在帮助开发者和系统设计者了解内核内部发生的情况。它可以用于调试或分析发生在用户空间之外的延迟和性能问题。尽管 ftrace 通常被认为是函数追踪器，但实际上它是一个包含多种追踪工具的框架。其中包括用于检查中断禁用与启用之间、抢占以及任务从唤醒到实际调度之间发生情况的延迟追踪。ftrace 最常见的用途之一是事件追踪。内核中有数百个静态事件点，可以通过 tracefs 文件系统启用这些事件点来查看内核某些部分正在发生的情况。更多信息请参见 events.rst。

实现细节
----------------------

有关架构移植和其他详细信息，请参见 Documentation/trace/ftrace-design.rst。
文件系统
------------

Ftrace 使用 tracefs 文件系统来保存控制文件以及显示输出的文件。
当 tracefs 被配置到内核中（选择任何 ftrace 选项都会实现这一点）时，目录 `/sys/kernel/tracing` 将被创建。要挂载这个目录，你可以在你的 `/etc/fstab` 文件中添加如下内容：

```
tracefs       /sys/kernel/tracing       tracefs defaults        0       0
```

或者你也可以在运行时挂载它：

```
mount -t tracefs nodev /sys/kernel/tracing
```

为了更快地访问该目录，你可以创建一个软链接指向它：

```
ln -s /sys/kernel/tracing /tracing
```

.. 注意::

  在 4.1 版本之前，所有的 ftrace 控制文件都在 debugfs 文件系统中，通常位于 `/sys/kernel/debug/tracing`。
为了向后兼容，在挂载 debugfs 文件系统时，
  tracefs 文件系统将自动挂载到：

  `/sys/kernel/debug/tracing`

  tracefs 文件系统中的所有文件也将位于该 debugfs 文件系统目录中。

.. 注意::

  选择任何 ftrace 选项也会创建 tracefs 文件系统。
本文档其余部分将假设你已经进入 ftrace 目录 (`cd /sys/kernel/tracing`) 并且只关注该目录内的文件，而不会用扩展的 `/sys/kernel/tracing` 路径名来分散注意力。
就是这样！（假设你已经在内核中配置了 ftrace）

挂载 tracefs 后，你将能够访问 ftrace 的控制和输出文件。以下是一些关键文件的列表：

注意：所有时间值以微秒为单位
current_tracer:

	用于设置或显示当前已配置的跟踪器。更改当前跟踪器会清除环形缓冲区的内容以及“快照”缓冲区。
available_tracers:

	包含已编译到内核中的不同类型的跟踪器。通过将它们的名字回显到 `current_tracer` 中可以配置这些跟踪器。
tracing_on:

	用于设置或显示是否启用了对跟踪环形缓冲区的写入。向此文件中回显 0 来禁用跟踪器，或者回显 1 来启用它。注意，这仅禁用对环形缓冲区的写入，跟踪开销可能仍然存在。
内核函数 `tracing_off()` 可以在内核内部使用来禁用对环形缓冲区的写入，这将使该文件变为 "0"。用户空间可以通过向该文件中回显 "1" 来重新启用跟踪。
注意，函数和事件触发器 "traceoff" 也会将此文件设置为零并停止跟踪。用户空间也可以通过此文件重新启用跟踪：

- 这个文件以人类可读的格式保存跟踪输出（如下所述）。使用带有 O_TRUNC 标志打开此文件进行写入会清除环形缓冲区的内容。
- 注意，这个文件不是一个消费者。如果未启用跟踪（没有运行追踪器或 tracing_on 为零），每次读取时它都会产生相同的输出。当跟踪启用时，由于尝试在不消费的情况下读取整个缓冲区，可能会产生不一致的结果。

trace_pipe：

- 输出与 "trace" 文件相同，但此文件旨在用于实时流式传输跟踪数据。从这个文件读取数据时会阻塞直到获取到新数据。与 "trace" 文件不同，此文件是一个消费者。这意味着从这个文件读取数据会导致顺序读取显示更当前的数据。一旦从这个文件中读取了数据，它就被消费掉，并且在顺序读取时不会再次读取。而 "trace" 文件是静态的，如果没有追踪器添加更多数据，每次读取时它都会显示相同的信息。

trace_options：

- 此文件允许用户控制上述输出文件中显示的数据量。还可以修改追踪器或事件的工作方式（如堆栈跟踪、时间戳等）的选项。

options：

- 这是一个目录，其中包含所有可用跟踪选项的文件（同样也在 trace_options 中）。也可以通过向具有相应选项名称的文件写入 "1" 或 "0" 来设置或清除选项。

tracing_max_latency：

- 一些追踪器记录最大延迟。例如，中断被禁用的最大时间。最大时间会保存在此文件中。最大跟踪信息也将存储并通过 "trace" 显示。只有当延迟大于此文件中的值（以微秒为单位）时，才会记录新的最大跟踪信息。
通过在此文件中记录一个时间点，除非延迟大于此文件中的时间，否则不会记录任何延迟。
`tracing_thresh:`

某些延迟追踪器会在延迟大于此文件中的数值时记录一条追踪信息。
仅当文件包含一个大于0的数值（以微秒为单位）时有效。

`buffer_percent:`

这是环形缓冲区需要填满的程度的水印值，以便唤醒等待者。也就是说，如果应用程序对某个每核的 `trace_pipe_raw` 文件进行阻塞读系统调用，它将一直阻塞，直到环形缓冲区中的数据量达到由 `buffer_percent` 指定的数量时才会唤醒读者。这也控制了在这个文件上的 `splice` 系统调用如何被阻塞：

- `0` —— 表示只要环形缓冲区中有任何数据就立即唤醒。
- `50` —— 表示大约一半的环形缓冲区子缓冲区被填满时唤醒。
- `100` —— 表示在环形缓冲区完全填满并即将开始覆盖旧数据时才阻塞。

`buffer_size_kb:`

这设置了或显示每个CPU缓冲区所持有的千字节数。默认情况下，每个CPU的跟踪缓冲区大小相同。显示的数字是单个CPU缓冲区的大小，而不是所有缓冲区的总大小。跟踪缓冲区是以页的形式分配的（内核用于分配的一块内存，通常大小为4KB）。可能会多分配几个页来容纳缓冲区管理的元数据。如果最后分配的一个页有足够的空间容纳更多的字节，则会使用该页的剩余部分，使得实际分配的大小大于请求或显示的大小。（注意，由于缓冲区管理的元数据，大小可能不是页大小的倍数。）

各个CPU的缓冲区大小可能不同（参见下面的 “per_cpu/cpu0/buffer_size_kb”），如果它们不同，此文件将显示“X”。

`buffer_total_size_kb:`

这显示所有跟踪缓冲区的总合并大小。
`buffer_subbuf_size_kb`：

此选项用于设置或显示子缓冲区的大小。环形缓冲区被分割成若干个相同大小的“子缓冲区”。一个事件不能大于子缓冲区的大小。通常，子缓冲区的大小等于架构的页面大小（在x86上为4K）。子缓冲区的开头还包含元数据，这也限制了事件的大小。这意味着当子缓冲区为页面大小时，任何事件都不能超过页面大小减去子缓冲区元数据的大小。

注意：`buffer_subbuf_size_kb` 是用户指定子缓冲区最小大小的一种方式。内核可能会根据实现细节将其设置得更大，或者如果内核无法处理请求，则直接失败该操作。

更改子缓冲区的大小可以让事件大于页面大小。

注意：在更改子缓冲区大小时，会停止追踪，并且环形缓冲区和快照缓冲区中的所有数据将被丢弃。

`free_buffer`：

如果一个进程正在进行追踪，并且希望在该进程完成时（即使被信号杀死）缩小“释放”环形缓冲区，可以使用此文件。关闭此文件时，环形缓冲区将被调整到其最小大小。

如果有一个正在追踪的进程同时打开此文件，当该进程退出时，它对此文件的文件描述符将被关闭，从而释放环形缓冲区。

如果设置了 `disable_on_free` 选项，也可能停止追踪。

`tracing_cpumask`：

这是一个掩码，允许用户仅在指定的CPU上进行追踪。

格式是一个表示CPU的十六进制字符串。

`set_ftrace_filter`：

当配置了动态ftrace（参见下面的“动态ftrace”部分），代码会被动态修改（代码文本重写），以禁用调用函数分析器（mcount）。这使得可以在几乎不损失性能的情况下配置追踪。这也具有一个副作用，即启用或禁用特定函数的追踪。向此文件中输入函数名称将限制追踪仅针对这些函数。
这会影响追踪器的 "function" 和 "function_graph" 功能，从而也影响函数剖析（参见 "function_profile_enabled"）
在 "available_filter_functions" 中列出的函数是可以写入此文件的内容。
此接口还允许使用命令。详情请参阅 "Filter commands" 部分。
为了提高速度，由于处理字符串可能相当耗费资源，并且需要检查所有注册到追踪的函数，因此可以在此文件中写入索引。写入一个数字（从 "1" 开始）将选择 "available_filter_functions" 文件中相应行位置的函数。
set_ftrace_notrace：

此设置的效果与 set_ftrace_filter 相反。任何添加到这里的函数都不会被追踪。如果某个函数同时存在于 set_ftrace_filter 和 set_ftrace_notrace 中，则该函数将不会被追踪。
set_ftrace_pid：

仅追踪在此文件中列出 PID 的线程。
如果设置了 "function-fork" 选项，则当在此文件中列出 PID 的任务进行 fork 时，子进程的 PID 将自动添加到此文件中，并且子进程也将被函数追踪器追踪。此选项还会导致退出的任务的 PID 从此文件中移除。
set_ftrace_notrace_pid：

使函数追踪器忽略在此文件中列出 PID 的线程。
如果设置了 "function-fork" 选项，则当在此文件中列出 PID 的任务进行 fork 时，子进程的 PID 将自动添加到此文件中，并且子进程也不会被函数追踪器追踪。此选项还会导致退出的任务的 PID 从此文件中移除。
如果一个 PID 同时存在于此文件和 "set_ftrace_pid" 中，则此文件优先，线程将不会被追踪。
### set_event_pid:

仅追踪此文件中列出的 PID 对应的任务的事件。
注意：`sched_switch` 和 `sched_wake_up` 也会追踪此文件中列出的事件。
要使具有父任务 PID 的子任务在 fork 时自动添加其 PID，请启用 “event-fork” 选项。该选项还会在任务退出时从文件中移除任务的 PID。

### set_event_notrace_pid:

不追踪此文件中列出的 PID 对应的任务的事件。
注意：`sched_switch` 和 `sched_wakeup` 会追踪未在此文件中列出的线程，即使某个线程的 PID 在文件中，但如果 `sched_switch` 或 `sched_wakeup` 事件还需要追踪其他应该被追踪的线程时，它们仍然会被追踪。
要使具有父任务 PID 的子任务在 fork 时自动添加其 PID，请启用 “event-fork” 选项。该选项还会在任务退出时从文件中移除任务的 PID。

### set_graph_function:

此文件中列出的函数将导致函数图追踪器仅追踪这些函数及其调用的函数。（更多详细信息请参阅“动态 ftrace”部分）
注意：`set_ftrace_filter` 和 `set_ftrace_notrace` 仍会影响被追踪的函数。

### set_graph_notrace:

类似于 `set_graph_function`，但会在命中函数时禁用函数图追踪，直到退出该函数为止。
这使得可以忽略由特定函数调用的函数的追踪。
### 可用的过滤函数 (`available_filter_functions`):

这些是 ftrace 已经处理并可以跟踪的函数。
这些函数名可以传递给以下命令：
- `set_ftrace_filter`
- `set_ftrace_notrace`
- `set_graph_function`
- `set_graph_notrace`

（有关更多详细信息，请参阅下面的“动态 ftrace”部分。）

### 可用的过滤函数地址 (`available_filter_functions_addrs`):

与 `available_filter_functions` 类似，但显示每个函数的地址。
显示的地址是补丁站点地址，可能与 `/proc/kallsyms` 中的地址不同。

### 动态 ftrace 总信息 (`dyn_ftrace_total_info`):

此文件用于调试目的。它显示了已经被转换为 nop 并可用于跟踪的函数数量。

### 启用的函数 (`enabled_functions`):

此文件主要用于调试 ftrace，但也可用于查看是否有任何函数附加了回调。
不仅追踪基础设施使用 ftrace 函数追踪工具，其他子系统也可能使用。此文件显示所有已附加回调的函数及其附加的回调数量。
请注意，一个回调可能会调用多个未在此计数中列出的函数。
如果回调注册了带有 “保存寄存器” 属性的函数进行跟踪（因此会有更多的开销），则会在该函数返回寄存器的同一行显示 ‘R’。
如果回调注册了带有 “修改 IP” 属性的函数进行跟踪（因此可以改变 `regs->ip`），则会在该函数可以被覆盖的同一行显示 ‘I’。
如果附加了非 ftrace 的 trampoline（例如 BPF），则会显示 ‘D’。
注意，普通的 ftrace 跳板（trampoline）也可以被附加，但每次只能有一个“直接”跳板被附加到一个给定的函数上。
某些架构不能调用直接跳板，而是将 ftrace ops 函数位于函数入口点之上。在这种情况下会显示一个‘O’。
如果一个函数在过去曾经被附加了“ip 修改”或“直接”调用，将会显示一个‘M’。这个标志永远不会被清除。它用于判断一个函数是否曾被 ftrace 基础设施修改过，并可用于调试。
如果架构支持的话，还会显示由该函数直接调用的回调函数。如果计数大于 1，则很可能是 ftrace_ops_list_func()。
如果一个函数的回调跳转到一个特定于该回调的跳板，并且该跳板不是标准跳板，则也会打印出该跳板的地址及其所调用的函数。

touched_functions：

此文件包含所有通过 ftrace 基础设施附加上函数回调的函数。其格式与 enabled_functions 相同，但显示所有曾经被追踪过的函数。
要查看任何曾被 “ip modify” 或直接跳板修改过的函数，可以执行以下命令：

`grep ' M ' /sys/kernel/tracing/touched_functions`

function_profile_enabled：

当设置为启用时，将会启用所有带有函数追踪器的函数，或者如果配置了函数图追踪器（function graph tracer）。它会保持一个函数调用次数的直方图，并且如果配置了函数图追踪器，还将跟踪在这些函数中花费的时间。直方图内容可以在以下文件中显示：

`trace_stat/function<cpu>` （如 function0, function1 等）

trace_stat：

一个包含不同追踪统计信息的目录。

kprobe_events：

启用动态跟踪点。详见 kprobetrace.rst。

kprobe_profile：

动态跟踪点统计信息。详见 kprobetrace.rst。
max_graph_depth:
  
  与函数图追踪器一起使用。这是它将追踪到的函数的最大深度。
  将此值设置为一，将仅显示从用户空间调用的第一个内核函数。

printk_formats:

  这是用于读取原始格式文件的工具。如果环形缓冲区中的事件引用了一个字符串，则只会在缓冲区中记录该字符串的指针，而不是字符串本身。这会阻止工具知道该字符串是什么。此文件显示了字符串及其地址，使工具能够将指针映射到实际的字符串。

saved_cmdlines:

  在跟踪事件中，默认情况下仅记录任务的PID，除非事件明确保存了任务的命令名（comm）。Ftrace会缓存PID到命令名的映射，试图在事件输出中显示命令名。如果一个命令名对应的PID没有列出，则输出中会显示`<...>`。

  如果选项“record-cmd”被设置为“0”，则在记录期间不会保存任务的命令名。默认情况下，此选项是启用的。

saved_cmdlines_size:

  默认情况下，会保存128个命令名（参见上面的“saved_cmdlines”）。要增加或减少缓存的命令名数量，请在此文件中输入要缓存的命令名数量。

saved_tgids:

  如果启用了“record-tgid”选项，则每次调度上下文切换时，都会在表中保存任务的任务组ID（TGID），该表将线程的PID映射到其TGID。默认情况下，“record-tgid”选项是禁用的。

snapshot:

  此选项显示“快照”缓冲区，并允许用户对当前运行的跟踪进行快照。
  更多详细信息请参见下面的“快照”部分。

stack_max_size:

  当激活栈追踪器时，此选项会显示遇到的最大栈大小。
  更多详细信息请参见下面的“栈追踪”部分。
stack_trace:

	当激活堆栈追踪器时，这会显示遇到的最大堆栈的回溯信息。
请参见下面的“堆栈追踪”部分。

stack_trace_filter:

	这类似于“set_ftrace_filter”，但它限制了堆栈追踪器检查的函数范围。

trace_clock:

	每当事件被记录到环形缓冲区中时，都会添加一个“时间戳”。此时间戳来自指定的时钟。默认情况下，ftrace 使用“本地”时钟。这个时钟非常快且严格按每个 CPU 运行，但在某些系统上它可能与其他 CPU 的时钟不同步。换句话说，本地时钟可能与其他 CPU 上的本地时钟不同步。
常用的时钟示例如下：

	# cat trace_clock
	[local] global counter x86-tsc

	方括号中的时钟是当前生效的时钟。

local:
	默认时钟，但可能在不同 CPU 之间不同步。

global:
	这个时钟与所有 CPU 同步，但可能比本地时钟稍慢一些。

counter:
	这不是一个时钟，而是一个实际的原子计数器。它逐个递增，但与所有 CPU 同步。当你需要知道不同 CPU 上事件发生的准确顺序时，这很有用。

uptime:
	这使用 jiffies 计数器，并且时间戳相对于启动以来的时间。

perf:
	这使得 ftrace 使用与 perf 相同的时钟。
最终，perf 将能够读取 ftrace 缓冲区，并且这将有助于交错数据。
x86-tsc：
		架构可以定义自己的时钟。例如，x86 在这里使用其自身的 TSC（时间戳计数器）周期时钟。

ppc-tb：
		这使用 PowerPC 的时间基准寄存器值。
		该时钟在 CPU 之间是同步的，并且如果已知 tb_offset，也可以用于关联跨虚拟机/来宾的事件。

mono：
		这使用快速单调时钟（CLOCK_MONOTONIC），它是单调的，并且会受到 NTP 速率调整的影响。

mono_raw：
		这是原始单调时钟（CLOCK_MONOTONIC_RAW），它是单调的，但不受任何速率调整的影响，并且以与硬件时钟源相同的速率滴答。

boot：
		这是启动时钟（CLOCK_BOOTTIME），基于快速单调时钟，但也考虑了暂停期间的时间。由于时钟访问设计用于在暂停路径中进行跟踪，因此如果在更新快速单调时钟之前访问时钟，则可能会有一些副作用。在这种情况下，时钟更新似乎比正常情况下稍早发生。
		此外，在 32 位系统上，64 位启动偏移量可能会看到部分更新。这些效应很少见，并且后处理应该能够处理它们。更多信息请参阅 ktime_get_boot_fast_ns() 函数中的注释。

tai：
		这是 TAI 时钟（CLOCK_TAI），源自于墙钟时间。然而，这个时钟不会经历由 NTP 插入闰秒导致的不连续性和向后跳变。由于时钟访问设计用于跟踪，因此可能会有一些副作用。在内部 TAI 偏移量更新时（例如，由于设置系统时间或使用带有偏移的 adjtimex()），时钟访问可能会产生错误的读数。
		这些效应很少见，并且后处理应该能够处理它们。更多信息请参阅 ktime_get_tai_fast_ns() 函数中的注释。

要设置一个时钟，只需将时钟名称回显到此文件：

	  # echo global > trace_clock

		设置时钟会清除环形缓冲区的内容以及“快照”缓冲区。
### trace_marker:

这个文件对于同步用户空间与内核中发生的事件非常有用。将字符串写入此文件将会被记录到ftrace缓冲区中。

在应用程序启动时打开此文件，并仅引用该文件描述符，这在应用中非常有用：

```c
void trace_write(const char *fmt, ...)
{
    va_list ap;
    char buf[256];
    int n;

    if (trace_fd < 0)
        return;

    va_start(ap, fmt);
    n = vsnprintf(buf, 256, fmt, ap);
    va_end(ap);

    write(trace_fd, buf, n);
}
```

开始：

```c
trace_fd = open("trace_marker", O_WRONLY);
```

注意：写入`trace_marker`文件还可以触发写入`/sys/kernel/tracing/events/ftrace/print/trigger`的事件触发器。详见《Documentation/trace/events.rst》中的“事件触发器”部分以及《Documentation/trace/histogram.rst》（第3节）中的示例。

### trace_marker_raw:

这个类似于`trace_marker`，但用于写入二进制数据，工具可以用来解析`trace_pipe_raw`中的数据。

### uprobe_events:

在程序中添加动态追踪点。
详见《uprobetracer.rst》。

### uprobe_profile:

Uprobe统计信息。详见《uprobetrace.txt》。

### instances:

这是一种创建多个追踪缓冲区的方法，不同的事件可以在不同的缓冲区中记录。
详见下面的“实例”部分。

### events:

这是追踪事件目录。它包含编译到内核中的事件追踪点（也称为静态追踪点）。它展示了存在的事件追踪点及其按系统分组的方式。各级别的“enable”文件可以通过写入“1”来启用这些追踪点。
详见《events.rst》获取更多信息。

### set_event:

通过将事件回显到此文件中，可以启用该事件。
详见《events.rst》获取更多信息。

### available_events:

可以启用的事件列表。
请参阅 events.rst 获取更多信息
timestamp_mode：

某些追踪器可能会更改记录跟踪事件到事件缓冲区时使用的时间戳模式。不同模式的事件可以在同一个缓冲区内共存，但记录事件时生效的模式决定了该事件使用哪种时间戳模式。默认的时间戳模式是 'delta'。
常用的追踪时间戳模式：

```
# cat timestamp_mode
[delta] absolute

方括号中的时间戳模式表示当前生效的模式。
delta：默认时间戳模式 — 时间戳是一个相对于每个缓冲区的时间差
absolute：时间戳是一个完整的绝对时间戳，而不是相对于某个值的时间差。因此它占用更多空间且效率较低
hwlat_detector：

硬件延迟检测器的目录
请参阅下面的“硬件延迟检测器”部分
per_cpu：

这是一个包含每个CPU追踪信息的目录
per_cpu/cpu0/buffer_size_kb：

ftrace缓冲区是按每个CPU定义的。也就是说，每个CPU都有一个单独的缓冲区，以允许原子写入，并避免缓存冲突。这些缓冲区可能具有不同的大小。此文件类似于 buffer_size_kb 文件，但它仅显示或设置特定CPU（此处为cpu0）的缓冲区大小。
per_cpu/cpu0/trace：

这与 “trace” 文件类似，但它仅显示特定CPU的数据。如果对此文件进行写入操作，只会清除特定CPU的缓冲区。
`per_cpu/cpu0/trace_pipe`

这与“trace_pipe”文件类似，是一种消耗性读取，但它只会显示（并消耗）特定CPU的数据。

`per_cpu/cpu0/trace_pipe_raw`

对于能够解析ftrace环形缓冲区二进制格式的工具，可以使用`trace_pipe_raw`文件直接从环形缓冲区中提取数据。通过使用`splice()`系统调用，可以快速将缓冲区数据传输到文件或网络，其中服务器正在收集这些数据。
与`trace_pipe`类似，这是一个消耗性读取器，多次读取总是会产生不同的数据。

`per_cpu/cpu0/snapshot:`

这与主“snapshot”文件类似，但只会快照当前CPU（如果支持）。它只显示给定CPU的快照内容，如果写入该文件，则只会清除该CPU的缓冲区。

`per_cpu/cpu0/snapshot_raw:`

类似于`trace_pipe_raw`，但会从给定CPU的快照缓冲区中读取二进制格式数据。

`per_cpu/cpu0/stats:`

这显示了关于环形缓冲区的某些统计信息：

- `entries`: 仍然在缓冲区中的事件数量。
- `overrun`: 当缓冲区满时由于覆盖而丢失的事件数量。
- `commit overrun`: 应始终为零。
  如果在一个嵌套事件中发生了如此多的事件（环形缓冲区是可重入的），以至于填满缓冲区并开始丢弃事件，则会设置此值。
- `bytes`: 实际读取的字节数（未被覆盖的字节数）。
最旧事件时间戳（oldest event ts）：
		缓冲区中的最旧时间戳

当前时间戳（now ts）：
		当前时间戳

丢失的事件（dropped events）：
		由于禁用覆盖选项而丢失的事件
已读事件（read events）：
		已读取的事件数量

追踪器
--------

以下是可配置的当前追踪器列表：

- "function"（函数）

	用于追踪所有内核函数的函数调用追踪器。

- "function_graph"（函数图）

	与函数追踪器类似，但函数追踪器仅在函数入口处进行探测，而函数图追踪器则在函数的入口和出口处都进行追踪。它提供了绘制类似于C语言源代码的函数调用图的能力。

- "blk"（块）

	块追踪器。由blktrace用户应用程序使用的追踪器。

- "hwlat"（硬件延迟）

	硬件延迟追踪器用于检测硬件是否产生延迟。请参阅下面的“硬件延迟检测器”部分。

- "irqsoff"（中断关闭）

	追踪禁用中断的区域，并保存最长的最大延迟的追踪记录。参见tracing_max_latency。当记录新的最大值时，会替换旧的追踪记录。最好启用latency-format选项来查看此追踪记录，当选择追踪器时，该选项会自动启用。

- "preemptoff"（抢占关闭）

	与irqsoff类似，但追踪并记录抢占被禁用的时间。
"preemptirqsoff"

类似于 irqsoff 和 preemptoff，但跟踪并记录中断和/或抢占被禁用的最长时间。

"wakeup"

跟踪并记录最高优先级任务在被唤醒后重新调度所需的最长延迟。

"wakeup_rt"

仅跟踪实时（RT）任务从唤醒到调度所需的最长延迟（与当前的"wakeup"相同）。这对于关注实时任务唤醒时延的人非常有用。

"wakeup_dl"

跟踪并记录SCHED_DEADLINE任务从唤醒到调度所需的最长延迟（与"wakeup"和"wakeup_rt"相同）。

"mmiotrace"

这是一种特殊的追踪器，用于追踪二进制模块。它会追踪模块对硬件的所有调用，包括所有写入和读取I/O的操作。

"branch"

此追踪器可以在追踪内核中的可能（likely）和不可能（unlikely）调用时进行配置。当一个可能或不可能分支被命中时，它会追踪该分支是否正确地预测了结果。

"nop"

这是“不追踪任何内容”的追踪器。要移除所有追踪器，只需将"nop"写入current_tracer。

错误条件
---------

对于大多数ftrace命令，失败模式是显而易见的，并通过标准返回码进行通信。
对于其他更复杂的命令，可以通过 `tracing/error_log` 文件获取扩展的错误信息。对于支持这一功能的命令，在发生错误后读取 `tracing/error_log` 文件将显示更多关于问题详情的信息（如果信息可用）。`tracing/error_log` 文件是一个循环错误日志文件，记录了最近8个失败命令的ftrace错误。

扩展的错误信息和使用示例如下所示：

```
# echo xxx > /sys/kernel/tracing/events/sched/sched_wakeup/trigger
echo: write error: Invalid argument

# cat /sys/kernel/tracing/error_log
[ 5348.887237] location: error: Couldn't yyy: zzz
      Command: xxx
               ^
[ 7517.023364] location: error: Bad rrr: sss
      Command: ppp qqq
                   ^

# 清除错误日志，可以向其中写入空字符串：
# echo > /sys/kernel/tracing/error_log
```

使用追踪器的例子
-------------------

以下是一些典型的使用追踪器的例子，仅通过 tracefs 接口控制（不使用任何用户空间工具）。

输出格式
--------------

以下是 `trace` 文件的输出格式示例：

```
# tracer: function
#
# entries-in-buffer/entries-written: 140080/250280   #P:4
#
#                              _-----=> irqs-off
#                             / _----=> need-resched
#                            | / _---=> hardirq/softirq
#                            || / _--=> preempt-depth
#                            ||| /     delay
#           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
#              | |       |   ||||       |         |
              bash-1977  [000] .... 17284.993652: sys_close <-system_call_fastpath
              bash-1977  [000] .... 17284.993653: __close_fd <-sys_close
              bash-1977  [000] .... 17284.993653: _raw_spin_lock <-__close_fd
              sshd-1974  [003] .... 17284.993653: __srcu_read_unlock <-fsnotify
              bash-1977  [000] .... 17284.993654: add_preempt_count <-_raw_spin_lock
              bash-1977  [000] ...1 17284.993655: _raw_spin_unlock <-__close_fd
              bash-1977  [000] ...1 17284.993656: sub_preempt_count <-_raw_spin_unlock
              bash-1977  [000] .... 17284.993657: filp_close <-__close_fd
              bash-1977  [000] .... 17284.993657: dnotify_flush <-filp_close
              sshd-1974  [003] .... 17284.993658: sys_select <-system_call_fastpath
              ...
```

在输出的头部会打印追踪器的名称（本例中是“function”）。然后显示缓冲区中的事件数量以及总共写入的条目数量。两者的差值表示由于缓冲区满而丢失的事件数量（250280 - 140080 = 110200 个事件丢失）。
头部解释了事件的内容。任务名 “bash”，任务 PID “1977”，运行所在的 CPU “000”，延迟格式（如下解释），时间戳以 `<秒>.<微秒>` 格式表示，被追踪的函数名 “sys_close” 以及调用该函数的父函数 “system_call_fastpath”。时间戳表示函数进入的时间。

延迟追踪格式
--------------------

当启用延迟格式选项或设置了一个延迟追踪器时，追踪文件会提供更多信息来查看为什么会出现延迟。以下是一个典型的追踪示例：

```
# tracer: irqsoff
#
# irqsoff latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 259 us, #4/4, CPU#2 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: ps-6143 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: __lock_task_sighand
#  => ended at:   _raw_spin_unlock_irqrestore
#
#
#                  _------=> CPU#            
#                 / _-----=> irqs-off        
#                | / _----=> need-resched    
#                || / _---=> hardirq/softirq 
#                ||| / _--=> preempt-depth   
#                |||| /     delay             
#  cmd     pid   ||||| time  |   caller      
#     \   /      |||||  \    |   /           
        ps-6143    2d...    0us!: trace_hardirqs_off <-__lock_task_sighand
        ps-6143    2d..1  259us+: trace_hardirqs_on <-_raw_spin_unlock_irqrestore
        ps-6143    2d..1  263us+: time_hardirqs_on <-_raw_spin_unlock_irqrestore
        ps-6143    2d..1  306us : <stack trace>
   => trace_hardirqs_on_caller
   => trace_hardirqs_on
   => _raw_spin_unlock_irqrestore
   => do_task_stat
   => proc_tgid_stat
   => proc_single_show
   => seq_read
   => vfs_read
   => sys_read
   => system_call_fastpath
```

这表明当前的追踪器是“irqsoff”，追踪中断禁用的时间。它给出了追踪版本（不变）以及执行时所用内核版本（3.8）。然后显示最大延迟时间（259 微秒）。显示的追踪条目数和总数都是4（#4/4）。
VP、KP、SP 和 HP 始终为零，并保留用于将来使用。
#P 是在线 CPU 的数量（#P:4）。
任务是在延迟发生时运行的进程。（ps pid: 6143）
导致延迟的开始和结束点（中断分别被禁用和启用的函数）：

  - __lock_task_sighand 是中断被禁用的地方
```plaintext
_raw_spin_unlock_irqrestore 是中断再次被启用的地方。
头信息之后的几行是跟踪记录本身。头部信息解释了各项的含义。

cmd: 追踪记录中进程的名称
pid: 该进程的PID
CPU#: 进程运行所在的CPU
irqs-off: 如果中断被禁用，则显示'd'；否则显示'.'
.. caution:: 如果架构不支持读取 irq flags 变量的方法，这里将始终显示'X'
need-resched:
	- 'N' 同时设置了 TIF_NEED_RESCHED 和 PREEMPT_NEED_RESCHED，
	- 'n' 只设置了 TIF_NEED_RESCHED，
	- 'p' 只设置了 PREEMPT_NEED_RESCHED，
	- '.' 否则
hardirq/softirq:
	- 'Z' - NMI 发生在硬中断中
	- 'z' - NMI 正在运行
	- 'H' - 硬中断发生在软中断中
	- 'h' - 硬中断正在运行
	- 's' - 软中断正在运行
	- '.' - 正常上下文
```
### preempt-depth: preempt_disabled 的级别

上述内容主要对内核开发者有意义。

时间：
当启用 latency-format 选项时，跟踪文件的输出包含相对于跟踪开始的时间戳。这与禁用 latency-format 时的输出不同，后者包含绝对时间戳。

延迟：
这只是为了更好地引起注意，并且需要修复为仅相对于同一 CPU。
标记由当前跟踪和下一个跟踪之间的差异决定：
- '$' - 大于 1 秒
- '@' - 大于 100 毫秒
- '*' - 大于 10 毫秒
- '#' - 大于 1000 微秒
- '!' - 大于 100 微秒
- '+' - 大于 10 微秒
- ' ' - 小于或等于 10 微秒

其余部分与 'trace' 文件相同。
请注意，latency 跟踪器通常以回溯结束，以便轻松找到发生延迟的位置。

### trace_options

`trace_options` 文件（或 `options` 目录）用于控制在跟踪输出中打印的内容或操作跟踪器。
要查看可用的选项，只需执行以下命令：

```
cat trace_options
print-parent
nosym-offset
nosym-addr
noverbose
noraw
nohex
nobin
noblock
nofields
trace_printk
annotate
nouserstacktrace
nosym-userobj
noprintk-msg-only
context-info
nolatency-format
record-cmd
norecord-tgid
overwrite
nodisable_on_free
irq-info
markers
noevent-fork
function-trace
nofunction-fork
nodisplay-graph
nostacktrace
nobranch
```

要禁用某个选项，在该选项前加上 "no" 并执行以下命令：

```
echo noprint-parent > trace_options
```

要启用某个选项，去掉 "no"：

```
echo sym-offset > trace_options
```

以下是可用的选项：

  print-parent
在函数跟踪中，显示调用者（父级）函数以及被跟踪的函数。
例如：
```
print-parent:
bash-4000  [01]  1477.606694: simple_strtoul <-kstrtoul

noprint-parent:
bash-4000  [01]  1477.606694: simple_strtoul
```

  sym-offset
不仅显示函数名称，还显示函数中的偏移量。例如，不是只看到 "ktime_get"，而是看到 "ktime_get+0xb/0x20"。
### sym-offset:
```plaintext
sym-offset:
    bash-4000  [01]  1477.606694: simple_strtoul+0x6/0xa0
```

### sym-addr
这将同时显示函数地址和函数名称：
```plaintext
sym-addr:
    bash-4000  [01]  1477.606694: simple_strtoul <c0339346>
```

### verbose
当启用 latency-format 选项时，此选项处理跟踪文件：
```plaintext
bash  4000 1 0 00000000 00010a95 [58127d26] 1720.415ms \
(+0.000ms): simple_strtoul (kstrtoul)
```

### raw
这将显示原始数字。此选项最适合用于能够更好地转换原始数字的用户应用程序，而不是在内核中完成转换。
```plaintext
raw
```

### hex
类似于 raw，但数字将以十六进制格式显示。
```plaintext
hex
```

### bin
这将以原始二进制格式打印数据。
```plaintext
bin
```

### block
设置后，在对 trace_pipe 进行轮询时不会阻塞读取操作。
```plaintext
block
```

### fields
按其类型描述的方式打印字段。此选项比使用 hex、bin 或 raw 更好，因为它能更好地解析事件内容。
```plaintext
fields
```

### trace_printk
可以禁用 trace_printk() 将内容写入缓冲区。
```plaintext
trace_printk
```

### annotate
当 CPU 缓冲区已满时，有时会让人感到困惑。一个 CPU 缓冲区最近有很多事件，因此时间框架较短，而另一个 CPU 可能只有少量事件，从而保留了更早的事件。当报告跟踪信息时，它会首先显示最早的事件，看起来好像只有一个 CPU 在运行（具有最早事件的那个 CPU）。当设置了 annotate 选项时，它会显示新 CPU 缓冲区开始的时间：
```plaintext
annotate
```
示例：
```plaintext
<idle>-0     [001] dNs4 21169.031481: wake_up_idle_cpu <-add_timer_on
<idle>-0     [001] dNs4 21169.031482: _raw_spin_unlock_irqrestore <-add_timer_on
<idle>-0     [001] .Ns4 21169.031484: sub_preempt_count <-_raw_spin_unlock_irqrestore
##### CPU 2 buffer started ####
<idle>-0     [002] .N.1 21169.031484: rcu_idle_exit <-cpu_idle
<idle>-0     [001] .Ns3 21169.031484: _raw_spin_unlock <-clocksource_watchdog
<idle>-0     [001] .Ns3 21169.031485: sub_preempt_count <-_raw_spin_unlock
```

### userstacktrace
此选项会改变跟踪记录。它会在每次跟踪事件之后记录当前用户空间线程的堆栈跟踪。
```plaintext
userstacktrace
```

### sym-userobj
当启用了用户堆栈跟踪时，查找地址所属的对象，并打印相对地址。当 ASLR 启用时，这特别有用，否则在应用程序不再运行后，您将无法解析地址到对象/文件/行。
```plaintext
sym-userobj
```
示例：
```plaintext
a.out-1623  [000] 40874.465068: /root/a.out[+0x480] <-/root/a.out[+0x494] <- /root/a.out[+0x4a8] <- /lib/libc-2.7.so[+0x1e1a6]
```

### printk-msg-only
当设置了此选项时，trace_printk() 只会显示格式，而不显示参数（如果使用了 trace_bprintk() 或 trace_bputs() 来保存 trace_printk() 的结果）。
```plaintext
printk-msg-only
```
### context-info
仅显示事件数据。隐藏comm、PID、时间戳、CPU和其他有用的数据。

### latency-format
此选项会改变跟踪输出。当启用时，跟踪会显示关于延迟的附加信息，具体描述见“延迟跟踪格式”。

### pause-on-trace
设置后，打开跟踪文件进行读取时，会暂停向环形缓冲区写入（如同将`tracing_on`设置为0）。这模拟了原始的跟踪文件行为。当文件关闭后，跟踪将会再次启用。

### hash-ptr
设置后，在事件打印格式中的`%p`会显示哈希后的指针值而不是实际地址。
这对于找出跟踪日志中哪个哈希值对应于实际值非常有用。

### record-cmd
当任何事件或跟踪器启用时，会在`sched_switch`跟踪点启用一个钩子来填充包含映射PID和comm的缓存。但这可能会导致一些开销，如果你只关心PID而不关心任务名称，禁用此选项可以降低跟踪的影响。详见“saved_cmdlines”。

### record-tgid
当任何事件或跟踪器启用时，会在`sched_switch`跟踪点启用一个钩子来填充映射线程组ID（TGID）到PID的缓存。详见“saved_tgids”。

### overwrite
此选项控制当跟踪缓冲区满时的行为。如果设置为“1”（默认），则最旧的事件会被丢弃并覆盖。如果设置为“0”，则最新的事件会被丢弃。
(请参见 per_cpu/cpu0/stats 以获取 overrun 和 dropped 的信息)

disable_on_free
当 free_buffer 被关闭时，跟踪将停止（将 tracing_on 设置为 0）

irq-info
显示中断、抢占计数和需要重新调度的数据
禁用时，跟踪输出如下所示：

```
# tracer: function
#
# entries-in-buffer/entries-written: 144405/9452052   #P:4
#
#           TASK-PID   CPU#      TIMESTAMP  FUNCTION
#              | |       |          |         |
        <idle>-0     [002]  23636.756054: ttwu_do_activate.constprop.89 <-try_to_wake_up
        <idle>-0     [002]  23636.756054: activate_task <-ttwu_do_activate.constprop.89
        <idle>-0     [002]  23636.756055: enqueue_task <-activate_task
```

markers
当设置时，trace_marker 可写（仅限 root 用户）
禁用时，写入 trace_marker 将返回 EINVAL 错误

event-fork
当设置时，具有在 set_event_pid 中列出的 PID 的任务在其 fork 时会将其子任务的 PID 添加到 set_event_pid 中。同样，当具有在 set_event_pid 中列出的 PID 的任务退出时，其 PID 将从文件中移除
这也会影响 set_event_notrace_pid 中列出的 PID

function-trace
如果启用此选项（默认已启用），则延迟跟踪器将启用函数跟踪。当禁用此选项时，延迟跟踪器不会跟踪函数。这在进行延迟测试时减少了跟踪器的开销

function-fork
当设置时，具有在 set_ftrace_pid 中列出的 PID 的任务在其 fork 时会将其子任务的 PID 添加到 set_ftrace_pid 中。同样，当具有在 set_ftrace_pid 中列出的 PID 的任务退出时，其 PID 将从文件中移除
这也会影响 set_ftrace_notrace_pid 中列出的 PID

display-graph
当设置时，延迟跟踪器（如 irqsoff、wakeup 等）将使用函数图跟踪而不是函数跟踪
堆栈跟踪（Stack Trace）
当设置后，在记录任何跟踪事件后会记录一个堆栈跟踪。

分支（Branch）
启用追踪器的分支跟踪。这将同时启用分支追踪和当前设置的追踪器。与“nop”追踪器一起启用此功能等同于仅启用“branch”追踪器。

提示：一些追踪器有自己的选项。这些选项仅在追踪器处于活动状态时出现在此文件中。它们始终出现在选项目录中。

以下是针对不同追踪器的具体选项：

函数追踪器（Function Tracer）的选项：

  func_stack_trace
当设置后，每次记录函数时都会记录一个堆栈跟踪。注意！在启用此选项之前，请限制被记录的函数数量，使用“set_ftrace_filter”，否则系统性能将会严重下降。记得在清除函数过滤器之前禁用此选项。

函数图追踪器（Function Graph Tracer）的选项：

由于函数图追踪器具有稍微不同的输出格式，因此它有自己的选项来控制显示的内容。
funcgraph-overrun
当设置后，在每个被追踪的函数之后会显示“overrun”。overrun是指调用堆栈深度大于为每个任务预留的深度时的情况。
每个任务都有一个固定大小的数组来追踪调用图中的函数。如果调用深度超过了这个数组的大小，该函数将不会被追踪。
overrun是指因超过这个数组而错过的函数数量。
funcgraph-cpu
当设置后，显示发生追踪的CPU编号。
funcgraph-overhead
当设置后，如果函数执行时间超过某个阈值，则显示延迟标记。具体阈值请参见上面标题描述中的“delay”部分。
### funcgraph-proc
与其他追踪器不同，默认情况下不会显示进程的命令行，而是在上下文切换期间仅在追踪任务进入和退出时显示。启用此选项后，每个进程的命令行将在每一行中显示。

### funcgraph-duration
在每个函数结束（返回）时，会以微秒为单位显示该函数执行的时间。

### funcgraph-abstime
当设置此选项时，每行将显示时间戳。

### funcgraph-irqs
当禁用此选项时，不会追踪在中断中发生的函数。

### funcgraph-tail
当设置此选项时，返回事件将包含所代表的函数。默认情况下，此选项是关闭的，并且仅显示一个闭合的大括号 "}" 作为函数的返回。

### funcgraph-retval
当设置此选项时，将打印每个被追踪函数的返回值，并以等号 "=" 后跟随。默认情况下，此选项是关闭的。

### funcgraph-retval-hex
当设置此选项时，返回值将以十六进制格式打印。如果未设置此选项且返回值是一个错误代码，则将以有符号十进制格式打印；否则也将以十六进制格式打印。默认情况下，此选项是关闭的。

### sleep-time
当运行函数图追踪器时，包括任务调度出去的时间。
启用后，将把任务调度出去的时间计入函数调用的一部分。

### graph-time
当使用函数图追踪器运行函数剖析器时，包括调用嵌套函数所需的时间。当未设置此选项时，报告的函数时间仅包括该函数本身的执行时间，而不包括它所调用的其他函数的时间。
### blk tracer 的选项：

#### blk_classic
显示更简约的输出。

#### irqsoff
当中断被禁用时，CPU无法响应任何其他外部事件（除了 NMI 和 SMI）。这会阻止定时器中断触发或鼠标中断通知内核新的鼠标事件。结果是反应时间的延迟。
`irqsoff` 跟踪器记录中断被禁用的时间。当达到新的最大延迟时，跟踪器保存导致该延迟点的跟踪信息，因此每次达到新的最大值时，旧的保存的跟踪信息将被丢弃，新的跟踪信息将被保存。
要重置最大值，可以执行以下操作：
```
# echo 0 > options/function-trace
# echo irqsoff > current_tracer
# echo 1 > tracing_on
# echo 0 > tracing_max_latency
# ls -ltr
[...]
# echo 0 > tracing_on
# cat trace
# tracer: irqsoff
#
# irqsoff latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 16 us, #4/4, CPU#0 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: swapper/0-0 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: run_timer_softirq
#  => ended at:   run_timer_softirq
#
#
#                  _------=> CPU#
#                 / _-----=> irqs-off
#                | / _----=> need-resched
#                || / _---=> hardirq/softirq
#                ||| / _--=> preempt-depth
#                |||| /     delay
#  cmd     pid   ||||| time  |   caller
#     \   /      |||||  \    |   /
<idle>-0       0d.s2    0us+: _raw_spin_lock_irq <-run_timer_softirq
<idle>-0       0dNs3   17us : _raw_spin_unlock_irq <-run_timer_softirq
<idle>-0       0dNs3   17us+: trace_hardirqs_on <-run_timer_softirq
<idle>-0       0dNs3   25us : <stack trace>
=> _raw_spin_unlock_irq
=> run_timer_softirq
=> __do_softirq
=> call_softirq
=> do_softirq
=> irq_exit
=> smp_apic_timer_interrupt
=> apic_timer_interrupt
=> rcu_idle_exit
=> cpu_idle
=> rest_init
=> start_kernel
=> x86_64_start_reservations
=> x86_64_start_kernel
```

这里我们看到有一个 16 微秒的延迟（这是非常好的）。`run_timer_softirq` 中的 `_raw_spin_lock_irq` 禁用了中断。16 微秒和显示的时间戳 25 微秒之间的差异是因为在记录最大延迟时间和记录导致该延迟的功能之间，时钟被递增了。

注意上述示例中没有设置 `function-trace`。如果我们设置了 `function-trace`，我们会得到一个更大的输出：
```
with echo 1 > options/function-trace

# tracer: irqsoff
#
# irqsoff latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 71 us, #168/168, CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: bash-2042 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: ata_scsi_queuecmd
#  => ended at:   ata_scsi_queuecmd
#
#
#                  _------=> CPU#
#                 / _-----=> irqs-off
#                | / _----=> need-resched
#                || / _---=> hardirq/softirq
#                ||| / _--=> preempt-depth
#                |||| /     delay
#  cmd     pid   ||||| time  |   caller
#     \   /      |||||  \    |   /
bash-2042    3d...    0us : _raw_spin_lock_irqsave <-ata_scsi_queuecmd
bash-2042    3d...    0us : add_preempt_count <-_raw_spin_lock_irqsave
bash-2042    3d..1    1us : ata_scsi_find_dev <-ata_scsi_queuecmd
bash-2042    3d..1    1us : __ata_scsi_find_dev <-ata_scsi_find_dev
bash-2042    3d..1    2us : ata_find_dev.part.14 <-__ata_scsi_find_dev
bash-2042    3d..1    2us : ata_qc_new_init <-__ata_scsi_queuecmd
bash-2042    3d..1    3us : ata_sg_init <-__ata_scsi_queuecmd
bash-2042    3d..1    4us : ata_scsi_rw_xlat <-__ata_scsi_queuecmd
bash-2042    3d..1    4us : ata_build_rw_tf <-ata_scsi_rw_xlat
[...]
bash-2042    3d..1   67us : delay_tsc <-__delay
bash-2042    3d..1   67us : add_preempt_count <-delay_tsc
bash-2042    3d..2   67us : sub_preempt_count <-delay_tsc
bash-2042    3d..1   67us : add_preempt_count <-delay_tsc
bash-2042    3d..2   68us : sub_preempt_count <-delay_tsc
bash-2042    3d..1   68us+: ata_bmdma_start <-ata_bmdma_qc_issue
bash-2042    3d..1   71us : _raw_spin_unlock_irqrestore <-ata_scsi_queuecmd
bash-2042    3d..1   71us : _raw_spin_unlock_irqrestore <-ata_scsi_queuecmd
bash-2042    3d..1   72us+: trace_hardirqs_on <-ata_scsi_queuecmd
bash-2042    3d..1  120us : <stack trace>
=> _raw_spin_unlock_irqrestore
=> ata_scsi_queuecmd
=> scsi_dispatch_cmd
=> scsi_request_fn
=> __blk_run_queue_uncond
=> __blk_run_queue
=> blk_queue_bio
=> submit_bio_noacct
=> submit_bio
=> submit_bh
=> __ext3_get_inode_loc
=> ext3_iget
=> ext3_lookup
=> lookup_real
=> __lookup_hash
=> walk_component
=> lookup_last
=> path_lookupat
=> filename_lookup
=> user_path_at_empty
=> user_path_at
=> vfs_fstatat
=> vfs_stat
=> sys_newstat
=> system_call_fastpath
```

这里我们追踪了一个 71 微秒的延迟。但我们也看到了在此期间调用的所有函数。请注意，通过启用函数跟踪，我们增加了额外的开销。这种开销可能会延长延迟时间。但无论如何，此跟踪提供了非常有用的调试信息。

如果我们更喜欢函数图输出而不是函数，我们可以设置 `display-graph` 选项：
```
with echo 1 > options/display-graph

# tracer: irqsoff
#
# irqsoff latency trace v1.1.5 on 4.20.0-rc6+
# --------------------------------------------------------------------
# latency: 3751 us, #274/274, CPU#0 | (M:desktop VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: bash-1507 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: free_debug_processing
#  => ended at:   return_to_handler
#
#
#                                       _-----=> irqs-off
#                                      / _----=> need-resched
#                                     | / _---=> hardirq/softirq
#                                     || / _--=> preempt-depth
#                                     ||| /
#   REL TIME      CPU  TASK/PID       ||||     DURATION                  FUNCTION CALLS
#      |          |     |    |        ||||      |   |                     |   |   |   |
          0 us |   0)   bash-1507    |  d... |   0.000 us    |  _raw_spin_lock_irqsave();
          0 us |   0)   bash-1507    |  d..1 |   0.378 us    |    do_raw_spin_trylock();
          1 us |   0)   bash-1507    |  d..2 |               |    set_track() {
          2 us |   0)   bash-1507    |  d..2 |               |      save_stack_trace() {
          2 us |   0)   bash-1507    |  d..2 |               |        __save_stack_trace() {
          3 us |   0)   bash-1507    |  d..2 |               |          __unwind_start() {
          3 us |   0)   bash-1507    |  d..2 |               |            get_stack_info() {
          3 us |   0)   bash-1507    |  d..2 |   0.351 us    |              in_task_stack();
          4 us |   0)   bash-1507    |  d..2 |   1.107 us    |            }
[...]
       3750 us |   0)   bash-1507    |  d..1 |   0.516 us    |      do_raw_spin_unlock();
       3750 us |   0)   bash-1507    |  d..1 |   0.000 us    |  _raw_spin_unlock_irqrestore();
       3764 us |   0)   bash-1507    |  d..1 |   0.000 us    |  tracer_hardirqs_on();
      bash-1507    0d..1 3792us : <stack trace>
=> free_debug_processing
=> __slab_free
=> kmem_cache_free
=> vm_area_free
=> remove_vma
=> exit_mmap
=> mmput
=> begin_new_exec
=> load_elf_binary
=> search_binary_handler
=> __do_execve_file.isra.32
=> __x64_sys_execve
=> do_syscall_64
=> entry_SYSCALL_64_after_hwframe
```

#### preemptoff
当抢占被禁用时，我们可能能够接收中断，但任务不能被抢占，并且高优先级的任务必须等待抢占再次启用才能抢占低优先级的任务。
`preemptoff` 跟踪器跟踪禁用抢占的地方。像 `irqsoff` 跟踪器一样，它记录抢占被禁用的最大延迟。`preemptoff` 跟踪器的控制类似于 `irqsoff` 跟踪器：
```
# echo 0 > options/function-trace
# echo preemptoff > current_tracer
# echo 1 > tracing_on
# echo 0 > tracing_max_latency
# ls -ltr
[...]
# echo 0 > tracing_on
# cat trace
# tracer: preemptoff
#
# preemptoff latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 46 us, #4/4, CPU#1 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: sshd-1991 (uid:0 nice:0 policy:0 rt_prio:0)
#    -----------------
#  => started at: do_IRQ
#  => ended at:   do_IRQ
#
#
#                  _------=> CPU#
#                 / _-----=> irqs-off
#                | / _----=> need-resched
#                || / _---=> hardirq/softirq
#                ||| / _--=> preempt-depth
#                |||| /     delay
#  cmd     pid   ||||| time  |   caller
#     \   /      |||||  \    |   /
sshd-1991    1d.h.    0us+: irq_enter <-do_IRQ
sshd-1991    1d..1   46us : irq_exit <-do_IRQ
sshd-1991    1d..1   47us+: trace_preempt_on <-do_IRQ
sshd-1991    1d..1   52us : <stack trace>
=> sub_preempt_count
=> irq_exit
=> do_IRQ
=> ret_from_intr
```

这里有一些变化。当有中断到来时（注意 'h'），抢占被禁用，并在退出时启用。
但我们也看到，在进入抢占关闭部分和离开这部分时，中断已经被禁用（'d'）。我们不知道在这期间或稍后中断是否被启用。
```plaintext
# tracer: preemptoff
#
# preemptoff latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# 延迟：83 微秒，#241/241，CPU#1 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | 任务：bash-1994（uid:0 nice:0 策略:0 实时优先级:0）
#    -----------------
#  => 开始于：wake_up_new_task
#  => 结束于：task_rq_unlock
#
#
#                  _------=> CPU#
#                 / _-----=> irqs-off        
#                | / _----=> 需要重新调度    
#                || / _---=> 硬中断/软中断 
#                ||| / _--=> 抢占深度   
#                |||| /     延迟             
#  命令     进程ID   ||||| 时间  |   调用者      
#     \   /      |||||  \    |   /           
      bash-1994    1d..1    0微秒 : _raw_spin_lock_irqsave <-wake_up_new_task
      bash-1994    1d..1    0微秒 : select_task_rq_fair <-select_task_rq
      bash-1994    1d..1    1微秒 : __rcu_read_lock <-select_task_rq_fair
      bash-1994    1d..1    1微秒 : source_load <-select_task_rq_fair
      bash-1994    1d..1    1微秒 : source_load <-select_task_rq_fair
  [...]
      bash-1994    1d..1   12微秒 : irq_enter <-smp_apic_timer_interrupt
      bash-1994    1d..1   12微秒 : rcu_irq_enter <-irq_enter
      bash-1994    1d..1   13微秒 : add_preempt_count <-irq_enter
      bash-1994    1d.h1   13微秒 : exit_idle <-smp_apic_timer_interrupt
      bash-1994    1d.h1   13微秒 : hrtimer_interrupt <-smp_apic_timer_interrupt
      bash-1994    1d.h1   13微秒 : _raw_spin_lock <-hrtimer_interrupt
      bash-1994    1d.h1   14微秒 : add_preempt_count <-_raw_spin_lock
      bash-1994    1d.h2   14微秒 : ktime_get_update_offsets <-hrtimer_interrupt
  [...]
      bash-1994    1d.h1   35微秒 : lapic_next_event <-clockevents_program_event
      bash-1994    1d.h1   35微秒 : irq_exit <-smp_apic_timer_interrupt
      bash-1994    1d.h1   36微秒 : sub_preempt_count <-irq_exit
      bash-1994    1d..2   36微秒 : do_softirq <-irq_exit
      bash-1994    1d..2   36微秒 : __do_softirq <-call_softirq
      bash-1994    1d..2   36微秒 : __local_bh_disable <-__do_softirq
      bash-1994    1d.s2   37微秒 : add_preempt_count <-_raw_spin_lock_irq
      bash-1994    1d.s3   38微秒 : _raw_spin_unlock <-run_timer_softirq
      bash-1994    1d.s3   39微秒 : sub_preempt_count <-_raw_spin_unlock
      bash-1994    1d.s2   39微秒 : call_timer_fn <-run_timer_softirq
  [...]
      bash-1994    1dNs2   81微秒 : cpu_needs_another_gp <-rcu_process_callbacks
      bash-1994    1dNs2   82微秒 : __local_bh_enable <-__do_softirq
      bash-1994    1dNs2   82微秒 : sub_preempt_count <-__local_bh_enable
      bash-1994    1dN.2   82微秒 : idle_cpu <-irq_exit
      bash-1994    1dN.2   83微秒 : rcu_irq_exit <-irq_exit
      bash-1994    1dN.2   83微秒 : sub_preempt_count <-irq_exit
      bash-1994    1.N.1   84微秒 : _raw_spin_unlock_irqrestore <-task_rq_unlock
      bash-1994    1.N.1   84微秒+ : trace_preempt_on <-task_rq_unlock
      bash-1994    1.N.1  104微秒 : <堆栈跟踪>
   => sub_preempt_count
   => _raw_spin_unlock_irqrestore
   => task_rq_unlock
   => wake_up_new_task
   => do_fork
   => sys_clone
   => stub_clone


以上是一个带有函数跟踪的preemptoff跟踪示例。我们看到在此期间没有禁用中断。
irq_enter代码告诉我们进入了一个中断'h'。在此之前，被跟踪的函数仍然显示它不在中断中，
但我们可以从这些函数本身看出情况并非如此。
preemptirqsoff
--------------

了解长时间禁用中断或抢占的位置是有帮助的。但有时我们想知道何时禁用了抢占和/或中断。
考虑以下代码：

    local_irq_disable();
    call_function_with_irqs_off();
    preempt_disable();
    call_function_with_irqs_and_preemption_off();
    local_irq_enable();
    call_function_with_preemption_off();
    preempt_enable();

irqsoff跟踪器将记录call_function_with_irqs_off()和
call_function_with_irqs_and_preemption_off()的总长度。
preemptoff跟踪器将记录call_function_with_irqs_and_preemption_off()和
call_function_with_preemption_off()的总长度。
但这两种跟踪器都不会跟踪中断和/或抢占禁用的时间。这个总时间是我们不能进行调度的时间。
为了记录这段时间，请使用preemptirqsoff跟踪器。
再次，使用此跟踪器类似于使用irqsoff和preemptoff跟踪器：
::

  # echo 0 > options/function-trace
  # echo preemptirqsoff > current_tracer
  # echo 1 > tracing_on
  # echo 0 > tracing_max_latency
  # ls -ltr
  [...]
  # echo 0 > tracing_on
  # cat trace
  # tracer: preemptirqsoff
  #
  # preemptirqsoff latency trace v1.1.5 on 3.8.0-test+
  # --------------------------------------------------------------------
  # 延迟：100 微秒，#4/4，CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
  #    -----------------
  #    | 任务：ls-2230（uid:0 nice:0 策略:0 实时优先级:0）
  #    -----------------
  #  => 开始于：ata_scsi_queuecmd
  #  => 结束于：ata_scsi_queuecmd
  #
  #
  #                  _------=> CPU#            
  #                 / _-----=> irqs-off        
  #                | / _----=> 需要重新调度    
  #                || / _---=> 硬中断/软中断 
  #                ||| / _--=> 抢占深度   
  #                |||| /     延迟             
  #  命令     进程ID   ||||| 时间  |   调用者      
  #     \   /      |||||  \    |   /           
        ls-2230    3d...    0微秒+ : _raw_spin_lock_irqsave <-ata_scsi_queuecmd
        ls-2230    3...1  100微秒 : _raw_spin_unlock_irqrestore <-ata_scsi_queuecmd
        ls-2230    3...1  101微秒+ : trace_preempt_on <-ata_scsi_queuecmd
        ls-2230    3...1  111微秒 : <堆栈跟踪>
   => sub_preempt_count
   => _raw_spin_unlock_irqrestore
   => ata_scsi_queuecmd
   => scsi_dispatch_cmd
   => scsi_request_fn
   => __blk_run_queue_uncond
   => __blk_run_queue
   => blk_queue_bio
   => submit_bio_noacct
   => submit_bio
   => submit_bh
   => ext3_bread
   => ext3_dir_bread
   => htree_dirblock_to_tree
   => ext3_htree_fill_tree
   => ext3_readdir
   => vfs_readdir
   => sys_getdents
   => system_call_fastpath


trace_hardirqs_off_thunk在x86上由汇编代码调用，当汇编代码中禁用中断时。如果没有函数跟踪，我们不知道抢占点内是否启用了中断。我们确实看到它是以抢占启用开始的。
以下是一个带有函数跟踪的跟踪示例：

  # tracer: preemptirqsoff
  #
  # preemptirqsoff latency trace v1.1.5 on 3.8.0-test+
  # --------------------------------------------------------------------
  # 延迟：161 微秒，#339/339，CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
  #    -----------------
  #    | 任务：ls-2269（uid:0 nice:0 策略:0 实时优先级:0）
  #    -----------------
  #  => 开始于：schedule
  #  => 结束于：mutex_unlock
  #
  #
  #                  _------=> CPU#            
  #                 / _-----=> irqs-off        
  #                | / _----=> 需要重新调度    
  #                || / _---=> 硬中断/软中断 
  #                ||| / _--=> 抢占深度   
  #                |||| /     延迟             
  #  命令     进程ID   ||||| 时间  |   调用者      
  #     \   /      |||||  \    |   /           
  kworker/-59      3...1    0微秒 : __schedule <-schedule
  kworker/-59      3d..1    0微秒 : rcu_preempt_qs <-rcu_note_context_switch
  kworker/-59      3d..1    1微秒 : add_preempt_count <-_raw_spin_lock_irq
  kworker/-59      3d..2    1微秒 : deactivate_task <-__schedule
  kworker/-59      3d..2    1微秒 : dequeue_task <-deactivate_task
  kworker/-59      3d..2    2微秒 : update_rq_clock <-dequeue_task
  kworker/-59      3d..2    2微秒 : dequeue_task_fair <-dequeue_task
  kworker/-59      3d..2    2微秒 : update_curr <-dequeue_task_fair
  kworker/-59      3d..2    2微秒 : update_min_vruntime <-update_curr
  kworker/-59      3d..2    3微秒 : cpuacct_charge <-update_curr
  kworker/-59      3d..2    3微秒 : __rcu_read_lock <-cpuacct_charge
  kworker/-59      3d..2    3微秒 : __rcu_read_unlock <-cpuacct_charge
  kworker/-59      3d..2    3微秒 : update_cfs_rq_blocked_load <-dequeue_task_fair
  kworker/-59      3d..2    4微秒 : clear_buddies <-dequeue_task_fair
  kworker/-59      3d..2    4微秒 : account_entity_dequeue <-dequeue_task_fair
  kworker/-59      3d..2    4微秒 : update_min_vruntime <-dequeue_task_fair
  kworker/-59      3d..2    4微秒 : update_cfs_shares <-dequeue_task_fair
  kworker/-59      3d..2    5微秒 : hrtick_update <-dequeue_task_fair
  kworker/-59      3d..2    5微秒 : wq_worker_sleeping <-__schedule
  kworker/-59      3d..2    5微秒 : kthread_data <-wq_worker_sleeping
  kworker/-59      3d..2    5微秒 : put_prev_task_fair <-__schedule
  kworker/-59      3d..2    6微秒 : pick_next_task_fair <-pick_next_task
  kworker/-59      3d..2    6微秒 : clear_buddies <-pick_next_task_fair
  kworker/-59      3d..2    6微秒 : set_next_entity <-pick_next_task_fair
  kworker/-59      3d..2    6微秒 : update_stats_wait_end <-set_next_entity
        ls-2269    3d..2    7微秒 : finish_task_switch <-__schedule
        ls-2269    3d..2    7微秒 : _raw_spin_unlock_irq <-finish_task_switch
        ls-2269    3d..2    8微秒 : do_IRQ <-ret_from_intr
        ls-2269    3d..2    8微秒 : irq_enter <-do_IRQ
        ls-2269    3d..2    8微秒 : rcu_irq_enter <-irq_enter
        ls-2269    3d..2    9微秒 : add_preempt_count <-irq_enter
        ls-2269    3d.h2    9微秒 : exit_idle <-do_IRQ
  [...]
        ls-2269    3d.h3   20微秒 : sub_preempt_count <-_raw_spin_unlock
        ls-2269    3d.h2   20微秒 : irq_exit <-do_IRQ
        ls-2269    3d.h2   21微秒 : sub_preempt_count <-irq_exit
        ls-2269    3d..3   21微秒 : do_softirq <-irq_exit
        ls-2269    3d..3   21微秒 : __do_softirq <-call_softirq
        ls-2269    3d..3   21微秒+ : __local_bh_disable <-__do_softirq
        ls-2269    3d.s4   29微秒 : sub_preempt_count <-_local_bh_enable_ip
        ls-2269    3d.s5   29微秒 : sub_preempt_count <-_local_bh_enable_ip
        ls-2269    3d.s5   31微秒 : do_IRQ <-ret_from_intr
        ls-2269    3d.s5   31微秒 : irq_enter <-do_IRQ
        ls-2269    3d.s5   31微秒 : rcu_irq_enter <-irq_enter
  [...]
        ls-2269    3d.s5   31微秒 : rcu_irq_enter <-irq_enter
        ls-2269    3d.s5   32微秒 : add_preempt_count <-irq_enter
        ls-2269    3d.H5   32微秒 : exit_idle <-do_IRQ
        ls-2269    3d.H5   32微秒 : handle_irq <-do_IRQ
        ls-2269    3d.H5   32微秒 : irq_to_desc <-handle_irq
        ls-2269    3d.H5   33微秒 : handle_fasteoi_irq <-handle_irq
  [...]
        ls-2269    3d.s5  158微秒 : _raw_spin_unlock_irqrestore <-rtl8139_poll
        ls-2269    3d.s3  158微秒 : net_rps_action_and_irq_enable.isra.65 <-net_rx_action
        ls-2269    3d.s3  159微秒 : __local_bh_enable <-__do_softirq
        ls-2269    3d.s3  159微秒 : sub_preempt_count <-__local_bh_enable
        ls-2269    3d..3  159微秒 : idle_cpu <-irq_exit
        ls-2269    3d..3  159微秒 : rcu_irq_exit <-irq_exit
        ls-2269    3d..3  160微秒 : sub_preempt_count <-irq_exit
        ls-2269    3d...  161微秒 : __mutex_unlock_slowpath <-mutex_unlock
        ls-2269    3d...  162微秒+ : trace_hardirqs_on <-mutex_unlock
        ls-2269    3d...  186微秒 : <堆栈跟踪>
   => __mutex_unlock_slowpath
   => mutex_unlock
   => process_output
   => n_tty_write
   => tty_write
   => vfs_write
   => sys_write
   => system_call_fastpath

这是一个有趣的跟踪示例。它始于kworker运行并调度出去，然后ls接管。但ls释放了rq锁并启用了中断（但未启用抢占）后，一个中断触发了。当中断完成时，开始运行软中断。
但在软中断运行时，另一个中断触发了。
当中断在软中断内部运行时，注释为'H'。
```
人们通常感兴趣的跟踪案例之一是任务从被唤醒到实际运行所需的时间。对于非实时任务，这个时间可能是任意的，但对其进行跟踪仍然很有意义。

不使用函数跟踪的情况下：

```shell
# echo 0 > options/function-trace
# echo wakeup > current_tracer
# echo 1 > tracing_on
# echo 0 > tracing_max_latency
# chrt -f 5 sleep 1
# echo 0 > tracing_on
# cat trace
# tracer: wakeup
#
# wakeup latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 15 us, #4/4, CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: kworker/3:1H-312 (uid:0 nice:-20 policy:0 rt_prio:0)
#    -----------------
#
#                  _------=> CPU#
#                 / _-----=> irqs-off
#                | / _----=> need-resched
#                || / _---=> hardirq/softirq
#                ||| / _--=> preempt-depth
#                |||| /     delay
#  cmd     pid   ||||| time  |   caller
#     \   /      |||||  \    |   /
<idle>-0       3dNs7    0us :      0:120:R   + [003]   312:100:R kworker/3:1H
<idle>-0       3dNs7    1us+: ttwu_do_activate.constprop.87 <-try_to_wake_up
<idle>-0       3d..3   15us : __schedule <-schedule
<idle>-0       3d..3   15us :      0:120:R ==> [003]   312:100:R kworker/3:1H
```

跟踪器仅跟踪系统中优先级最高的任务，以避免跟踪普通情况。这里我们可以看到，具有-20优先级（即优先级很高）的`kworker`从被唤醒到运行只用了15微秒。非实时任务并不那么有趣。更有趣的跟踪是专注于实时任务。

### 实时任务的唤醒（wakeup_rt）

在实时环境中，了解最高优先级任务从被唤醒到执行所需的时间非常重要。这通常被称为“调度延迟”。需要强调的是，这是针对实时任务的。了解非实时任务的调度延迟也很重要，但平均调度延迟对非实时任务更有意义。工具如LatencyTop更适合此类测量。

实时环境关注的是最坏情况下的延迟，即事件发生的最长延迟，而不是平均延迟。我们可能有一个非常快的调度器，但它偶尔会有较大的延迟，这对实时任务来说并不理想。`wakeup_rt`跟踪器旨在记录实时任务的最坏情况唤醒。不记录非实时任务是因为跟踪器只记录一个最坏情况，而追踪不可预测的非实时任务会覆盖实时任务的最坏情况延迟（只需运行普通的唤醒跟踪器一段时间就能看到这种效果）。

由于此跟踪器只处理实时任务，因此我们将以不同于之前跟踪器的方式运行它。我们不会执行`ls`命令，而是将在`chrt`下运行`sleep 1`，这会改变任务的优先级：

```shell
# echo 0 > options/function-trace
# echo wakeup_rt > current_tracer
# echo 1 > tracing_on
# echo 0 > tracing_max_latency
# chrt -f 5 sleep 1
# echo 0 > tracing_on
# cat trace
# tracer: wakeup
#
# tracer: wakeup_rt
#
# wakeup_rt latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 5 us, #4/4, CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: sleep-2389 (uid:0 nice:0 policy:1 rt_prio:5)
#    -----------------
#
#                  _------=> CPU#
#                 / _-----=> irqs-off
#                | / _----=> need-resched
#                || / _---=> hardirq/softirq
#                ||| / _--=> preempt-depth
#                |||| /     delay
#  cmd     pid   ||||| time  |   caller
#     \   /      |||||  \    |   /
<idle>-0       3d.h4    0us :      0:120:R   + [003]  2389: 94:R sleep
<idle>-0       3d.h4    1us+: ttwu_do_activate.constprop.87 <-try_to_wake_up
<idle>-0       3d..3    5us : __schedule <-schedule
<idle>-0       3d..3    5us :      0:120:R ==> [003]  2389: 94:R sleep
```

在这个空闲系统上运行时，我们看到进行任务切换仅用了5微秒。请注意，由于调度中的跟踪点位于实际“切换”之前，因此当记录的任务即将调度时，我们会停止跟踪。如果我们在调度器末尾添加一个新的标记，这一点可能会改变。
请注意，记录的任务是 'sleep'，其 PID 为 2389，并且具有 rt_prio 值 5。这个优先级是用户空间优先级，而不是内核内部优先级。策略中 1 表示 SCHED_FIFO，2 表示 SCHED_RR。

注意，跟踪数据显示的是内部优先级（99 - rt_prio）：

```
<idle>-0       3d..3    5us :      0:120:R ==> [003]  2389: 94:R sleep
```

`0:120:R` 表示空闲进程以优先级 0（120 - 120）运行，并处于运行状态 'R'。`sleep` 任务被调度进来，PID 为 2389: 94:R。这里的优先级是内核的 rtprio（99 - 5 = 94），并且它也处于运行状态。

使用 `chrt -r 5` 和函数跟踪设置来执行相同的操作：

```
echo 1 > options/function-trace

# tracer: wakeup_rt
#
# wakeup_rt latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 29 us, #85/85, CPU#3 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: sleep-2448 (uid:0 nice:0 policy:1 rt_prio:5)
#    -----------------
#
#                  _------=> CPU#            
#                 / _-----=> irqs-off        
#                | / _----=> need-resched    
#                || / _---=> hardirq/softirq 
#                ||| / _--=> preempt-depth   
#                |||| /     delay             
#  cmd     pid   ||||| time  |   caller      
#     \   /      |||||  \    |   /           
<idle>-0       3d.h4    1us+:      0:120:R   + [003]  2448: 94:R sleep
<idle>-0       3d.h4    2us : ttwu_do_activate.constprop.87 <-try_to_wake_up
<idle>-0       3d.h3    3us : check_preempt_curr <-ttwu_do_wakeup
<idle>-0       3d.h3    3us : resched_curr <-check_preempt_curr
<idle>-0       3dNh3    4us : task_woken_rt <-ttwu_do_wakeup
<idle>-0       3dNh3    4us : _raw_spin_unlock <-try_to_wake_up
<idle>-0       3dNh3    4us : sub_preempt_count <-_raw_spin_unlock
<idle>-0       3dNh2    5us : ttwu_stat <-try_to_wake_up
<idle>-0       3dNh2    5us : _raw_spin_unlock_irqrestore <-try_to_wake_up
<idle>-0       3dNh2    6us : sub_preempt_count <-_raw_spin_unlock_irqrestore
<idle>-0       3dNh1    6us : _raw_spin_lock <-__run_hrtimer
<idle>-0       3dNh1    6us : add_preempt_count <-_raw_spin_lock
<idle>-0       3dNh2    7us : _raw_spin_unlock <-hrtimer_interrupt
<idle>-0       3dNh2    7us : sub_preempt_count <-_raw_spin_unlock
<idle>-0       3dNh1    7us : tick_program_event <-hrtimer_interrupt
<idle>-0       3dNh1    7us : clockevents_program_event <-tick_program_event
<idle>-0       3dNh1    8us : ktime_get <-clockevents_program_event
<idle>-0       3dNh1    8us : lapic_next_event <-clockevents_program_event
<idle>-0       3dNh1    8us : irq_exit <-smp_apic_timer_interrupt
<idle>-0       3dNh1    9us : sub_preempt_count <-irq_exit
<idle>-0       3dN.2    9us : idle_cpu <-irq_exit
<idle>-0       3dN.2    9us : rcu_irq_exit <-irq_exit
<idle>-0       3dN.2   10us : rcu_eqs_enter_common.isra.45 <-rcu_irq_exit
<idle>-0       3dN.2   10us : sub_preempt_count <-irq_exit
<idle>-0       3.N.1   11us : rcu_idle_exit <-cpu_idle
<idle>-0       3dN.1   11us : rcu_eqs_exit_common.isra.43 <-rcu_idle_exit
<idle>-0       3.N.1   11us : tick_nohz_idle_exit <-cpu_idle
<idle>-0       3dN.1   12us : menu_hrtimer_cancel <-tick_nohz_idle_exit
<idle>-0       3dN.1   12us : ktime_get <-tick_nohz_idle_exit
<idle>-0       3dN.1   12us : tick_do_update_jiffies64 <-tick_nohz_idle_exit
<idle>-0       3dN.1   13us : cpu_load_update_nohz <-tick_nohz_idle_exit
<idle>-0       3dN.1   13us : _raw_spin_lock <-cpu_load_update_nohz
<idle>-0       3dN.1   13us : add_preempt_count <-_raw_spin_lock
<idle>-0       3dN.2   13us : __cpu_load_update <-cpu_load_update_nohz
<idle>-0       3dN.2   14us : sched_avg_update <-__cpu_load_update
<idle>-0       3dN.2   14us : _raw_spin_unlock <-cpu_load_update_nohz
<idle>-0       3dN.2   14us : sub_preempt_count <-_raw_spin_unlock
<idle>-0       3dN.1   15us : calc_load_nohz_stop <-tick_nohz_idle_exit
<idle>-0       3dN.1   15us : touch_softlockup_watchdog <-tick_nohz_idle_exit
<idle>-0       3dN.1   15us : hrtimer_cancel <-tick_nohz_idle_exit
<idle>-0       3dN.1   15us : hrtimer_try_to_cancel <-hrtimer_cancel
<idle>-0       3dN.1   16us : lock_hrtimer_base.isra.18 <-hrtimer_try_to_cancel
<idle>-0       3dN.1   16us : _raw_spin_lock_irqsave <-lock_hrtimer_base.isra.18
<idle>-0       3dN.1   16us : add_preempt_count <-_raw_spin_lock_irqsave
<idle>-0       3dN.2   17us : __remove_hrtimer <-remove_hrtimer.part.16
<idle>-0       3dN.2   17us : hrtimer_force_reprogram <-__remove_hrtimer
<idle>-0       3dN.2   17us : tick_program_event <-hrtimer_force_reprogram
<idle>-0       3dN.2   18us : clockevents_program_event <-tick_program_event
<idle>-0       3dN.2   18us : ktime_get <-clockevents_program_event
<idle>-0       3dN.2   18us : lapic_next_event <-clockevents_program_event
<idle>-0       3dN.2   19us : _raw_spin_unlock_irqrestore <-hrtimer_try_to_cancel
<idle>-0       3dN.2   19us : sub_preempt_count <-_raw_spin_unlock_irqrestore
<idle>-0       3dN.1   19us : hrtimer_forward <-tick_nohz_idle_exit
<idle>-0       3dN.1   20us : ktime_add_safe <-hrtimer_forward
<idle>-0       3dN.1   20us : ktime_add_safe <-hrtimer_forward
<idle>-0       3dN.1   20us : hrtimer_start_range_ns <-hrtimer_start_expires.constprop.11
<idle>-0       3dN.1   20us : __hrtimer_start_range_ns <-hrtimer_start_range_ns
<idle>-0       3dN.1   21us : lock_hrtimer_base.isra.18 <-__hrtimer_start_range_ns
<idle>-0       3dN.1   21us : _raw_spin_lock_irqsave <-lock_hrtimer_base.isra.18
<idle>-0       3dN.1   21us : add_preempt_count <-_raw_spin_lock_irqsave
<idle>-0       3dN.2   22us : ktime_add_safe <-__hrtimer_start_range_ns
<idle>-0       3dN.2   22us : enqueue_hrtimer <-__hrtimer_start_range_ns
<idle>-0       3dN.2   22us : tick_program_event <-__hrtimer_start_range_ns
<idle>-0       3dN.2   23us : clockevents_program_event <-tick_program_event
<idle>-0       3dN.2   23us : ktime_get <-clockevents_program_event
<idle>-0       3dN.2   23us : lapic_next_event <-clockevents_program_event
<idle>-0       3dN.2   24us : _raw_spin_unlock_irqrestore <-__hrtimer_start_range_ns
<idle>-0       3dN.2   24us : sub_preempt_count <-_raw_spin_unlock_irqrestore
<idle>-0       3dN.1   24us : account_idle_ticks <-tick_nohz_idle_exit
<idle>-0       3dN.1   24us : account_idle_time <-account_idle_ticks
<idle>-0       3.N.1   25us : sub_preempt_count <-cpu_idle
<idle>-0       3.N..   25us : schedule <-cpu_idle
<idle>-0       3.N..   25us : __schedule <-preempt_schedule
<idle>-0       3.N..   26us : add_preempt_count <-__schedule
<idle>-0       3.N.1   26us : rcu_note_context_switch <-__schedule
<idle>-0       3.N.1   26us : rcu_sched_qs <-rcu_note_context_switch
<idle>-0       3dN.1   27us : rcu_preempt_qs <-rcu_note_context_switch
<idle>-0       3.N.1   27us : _raw_spin_lock_irq <-__schedule
<idle>-0       3dN.1   27us : add_preempt_count <-_raw_spin_lock_irq
<idle>-0       3dN.2   28us : put_prev_task_idle <-__schedule
<idle>-0       3dN.2   28us : pick_next_task_stop <-pick_next_task
<idle>-0       3dN.2   28us : pick_next_task_rt <-pick_next_task
<idle>-0       3dN.2   29us : dequeue_pushable_task <-pick_next_task_rt
<idle>-0       3d..3   29us : __schedule <-preempt_schedule
<idle>-0       3d..3   30us :      0:120:R ==> [003]  2448: 94:R sleep
```

即使启用了函数跟踪，这个跟踪也不是很大，所以我包含了整个跟踪。
中断发生时系统处于空闲状态。在调用 `task_woken_rt()` 之前某处设置了 `NEED_RESCHED` 标志，这由第一个出现的 'N' 标志表示。

延迟跟踪和事件
--------------------------
由于函数跟踪可能会导致更大的延迟，但如果不了解延迟内的具体情况，很难知道是什么原因导致的。这里有一个折衷方案，即启用事件：

```
# echo 0 > options/function-trace
# echo wakeup_rt > current_tracer
# echo 1 > events/enable
# echo 1 > tracing_on
# echo 0 > tracing_max_latency
# chrt -f 5 sleep 1
# echo 0 > tracing_on
# cat trace
# tracer: wakeup_rt
#
# wakeup_rt latency trace v1.1.5 on 3.8.0-test+
# --------------------------------------------------------------------
# latency: 6 us, #12/12, CPU#2 | (M:preempt VP:0, KP:0, SP:0 HP:0 #P:4)
#    -----------------
#    | task: sleep-5882 (uid:0 nice:0 policy:1 rt_prio:5)
#    -----------------
#
#                  _------=> CPU#            
#                 / _-----=> irqs-off        
#                | / _----=> need-resched    
#                || / _---=> hardirq/softirq 
#                ||| / _--=> preempt-depth   
#                |||| /     delay             
#  cmd     pid   ||||| time  |   caller      
#     \   /      |||||  \    |   /           
<idle>-0       2d.h4    0us :      0:120:R   + [002]  5882: 94:R sleep
<idle>-0       2d.h4    0us : ttwu_do_activate.constprop.87 <-try_to_wake_up
<idle>-0       2d.h4    1us : sched_wakeup: comm=sleep pid=5882 prio=94 success=1 target_cpu=002
<idle>-0       2dNh2    1us : hrtimer_expire_exit: hrtimer=ffff88007796feb8
<idle>-0       2.N.2    2us : power_end: cpu_id=2
<idle>-0       2.N.2    3us : cpu_idle: state=4294967295 cpu_id=2
<idle>-0       2dN.3    4us : hrtimer_cancel: hrtimer=ffff88007d50d5e0
<idle>-0       2dN.3    4us : hrtimer_start: hrtimer=ffff88007d50d5e0 function=tick_sched_timer expires=34311211000000 softexpires=34311211000000
<idle>-0       2.N.2    5us : rcu_utilization: Start context switch
<idle>-0       2.N.2    5us : rcu_utilization: End context switch
<idle>-0       2d..3    6us : __schedule <-schedule
<idle>-0       2d..3    6us :      0:120:R ==> [002]  5882: 94:R sleep
```

硬件延迟检测器
-------------------------
硬件延迟检测器通过启用 "hwlat" 跟踪器来执行。
注意，此跟踪器会影响系统的性能，因为它会周期性地使一个 CPU 不断忙于禁用中断：

```
# echo hwlat > current_tracer
# sleep 100
# cat trace
# tracer: hwlat
#
# entries-in-buffer/entries-written: 13/13   #P:8
#
#                              _-----=> irqs-off
#                             / _----=> need-resched
#                            | / _---=> hardirq/softirq
#                            || / _--=> preempt-depth
#                            ||| /     delay
#           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
#              | |       |   ||||       |         |
             <...>-1729  [001] d...   678.473449: #1     inner/outer(us):   11/12    ts:1581527483.343962693 count:6
             <...>-1729  [004] d...   689.556542: #2     inner/outer(us):   16/9     ts:1581527494.889008092 count:1
             <...>-1729  [005] d...   714.756290: #3     inner/outer(us):   16/16    ts:1581527519.678961629 count:5
             <...>-1729  [001] d...   718.788247: #4     inner/outer(us):    9/17    ts:1581527523.889012713 count:1
             <...>-1729  [002] d...   719.796341: #5     inner/outer(us):   13/9     ts:1581527524.912872606 count:1
             <...>-1729  [006] d...   844.787091: #6     inner/outer(us):    9/12    ts:1581527649.889048502 count:2
             <...>-1729  [003] d...   849.827033: #7     inner/outer(us):   18/9     ts:1581527654.889013793 count:1
             <...>-1729  [007] d...   853.859002: #8     inner/outer(us):    9/12    ts:1581527658.889065736 count:1
             <...>-1729  [001] d...   855.874978: #9     inner/outer(us):    9/11    ts:1581527660.861991877 count:1
             <...>-1729  [001] d...   863.938932: #10    inner/outer(us):    9/11    ts:1581527668.970010500 count:1 nmi-total:7 nmi-count:1
             <...>-1729  [007] d...   878.050780: #11    inner/outer(us):    9/12    ts:1581527683.385002600 count:1 nmi-total:5 nmi-count:1
             <...>-1729  [007] d...   886.114702: #12    inner/outer(us):    9/12    ts:1581527691.385001600 count:1
```

上面的输出在表头部分是相同的。所有事件都会禁用中断 'd'。在 FUNCTION 标题下有：

 #1
 这是记录的事件计数，这些事件大于 tracing_threshold（见下文）。
内部/外部（us）： 11/11

这显示了两个数字，分别表示“内部延迟”和“外部延迟”。测试在一个循环中运行，并检查两次时间戳。在两个时间戳之间检测到的延迟是“内部延迟”，而在上一个时间戳与下一个时间戳之间检测到的延迟是“外部延迟”。

时间戳：1581527483.343962693

这是记录窗口中第一个延迟的绝对时间戳。

计数：6

这是在窗口期间检测到延迟的次数。

NMI总数：7 NMI计数：1

在支持NMI的架构中，如果测试过程中有NMI进来，则NMI所花费的时间将以微秒为单位报告在“NMI总数”中。
所有有NMI的架构在测试过程中如果有NMI进来都会显示“NMI计数”。

硬件延迟文件：

tracing_threshold
此值会自动设置为“10”，代表10微秒。这是需要被检测到的延迟阈值，只有当超过这个阈值时，才会记录追踪信息。
注意，当硬件延迟追踪器结束（另一个追踪器写入“current_tracer”）时，原始的tracing_threshold值会被放回此文件中。

hwlat_detector/width
测试运行时禁用中断的时间长度。

hwlat_detector/window
测试运行窗口的时间长度。也就是说，测试将在每个“窗口”微秒内运行“宽度”微秒。

tracing_cpumask
当测试开始时，创建一个内核线程来运行测试。该线程将在tracing_cpumask中列出的CPU之间交替运行，每次周期（一个“窗口”）。为了限制测试只在特定的CPU上运行，请在此文件中设置相应的掩码。

功能
------

这个追踪器是函数追踪器。可以通过调试文件系统启用函数追踪器。确保设置了ftrace_enabled；否则，这个追踪器将不起作用（nop）。
参见“ftrace_enabled”部分

```
# sysctl kernel.ftrace_enabled=1
# echo function > current_tracer
# echo 1 > tracing_on
# usleep 1
# echo 0 > tracing_on
# cat trace
# tracer: function
#
# entries-in-buffer/entries-written: 24799/24799   #P:4
#
#                              _-----=> irqs-off
#                             / _----=> need-resched
#                            | / _---=> hardirq/softirq
#                            || / _--=> preempt-depth
#                            ||| /     delay
#           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
#              | |       |   ||||       |         |
              bash-1994  [002] ....  3082.063030: mutex_unlock <-rb_simple_write
              bash-1994  [002] ....  3082.063031: __mutex_unlock_slowpath <-mutex_unlock
              bash-1994  [002] ....  3082.063031: __fsnotify_parent <-fsnotify_modify
              bash-1994  [002] ....  3082.063032: fsnotify <-fsnotify_modify
              bash-1994  [002] ....  3082.063032: __srcu_read_lock <-fsnotify
              bash-1994  [002] ....  3082.063032: add_preempt_count <-__srcu_read_lock
              bash-1994  [002] ...1  3082.063032: sub_preempt_count <-__srcu_read_lock
              bash-1994  [002] ....  3082.063033: __srcu_read_unlock <-fsnotify
  [...]
```

注意：函数跟踪器使用环形缓冲区来存储上述条目。最新的数据可能会覆盖最旧的数据。
有时仅使用`echo`停止跟踪是不够的，因为跟踪可能会覆盖您想要记录的数据。出于这个原因，有时直接从程序禁用跟踪更好。这可以让你在碰到你感兴趣的那部分时停止跟踪。要从C程序中直接禁用跟踪，可以使用如下代码片段：

```c
int trace_fd;
[...]
int main(int argc, char *argv[]) {
[...]
trace_fd = open(tracing_file("tracing_on"), O_WRONLY);
[...]
if (condition_hit()) {
write(trace_fd, "0", 1);
}
[...]
}
```

单线程跟踪
------------------

通过写入`set_ftrace_pid`，你可以跟踪一个单一的线程。例如：

```
# cat set_ftrace_pid
no pid
# echo 3111 > set_ftrace_pid
# cat set_ftrace_pid
3111
# echo function > current_tracer
# cat trace | head
# tracer: function
#
#           TASK-PID    CPU#    TIMESTAMP  FUNCTION
#              | |       |          |         |
      yum-updatesd-3111  [003]  1637.254676: finish_task_switch <-thread_return
      yum-updatesd-3111  [003]  1637.254681: hrtimer_cancel <-schedule_hrtimeout_range
      yum-updatesd-3111  [003]  1637.254682: hrtimer_try_to_cancel <-hrtimer_cancel
      yum-updatesd-3111  [003]  1637.254683: lock_hrtimer_base <-hrtimer_try_to_cancel
      yum-updatesd-3111  [003]  1637.254685: fget_light <-do_sys_poll
      yum-updatesd-3111  [003]  1637.254686: pipe_poll <-do_sys_poll
# echo > set_ftrace_pid
# cat trace |head
# tracer: function
#
#           TASK-PID    CPU#    TIMESTAMP  FUNCTION
#              | |       |          |         |
##### CPU 3 buffer started ####
      yum-updatesd-3111  [003]  1701.957688: free_poll_entry <-poll_freewait
      yum-updatesd-3111  [003]  1701.957689: remove_wait_queue <-free_poll_entry
      yum-updatesd-3111  [003]  1701.957691: fput <-free_poll_entry
      yum-updatesd-3111  [003]  1701.957692: audit_syscall_exit <-sysret_audit
      yum-updatesd-3111  [003]  1701.957693: path_put <-audit_syscall_exit
```

如果你想在执行过程中跟踪一个函数，可以使用类似下面的简单程序：

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#define _STR(x) #x
#define STR(x) _STR(x)
#define MAX_PATH 256

const char *find_tracefs(void)
{
       static char tracefs[MAX_PATH+1];
       static int tracefs_found;
       char type[100];
       FILE *fp;

       if (tracefs_found)
               return tracefs;

       if ((fp = fopen("/proc/mounts","r")) == NULL) {
               perror("/proc/mounts");
               return NULL;
       }

       while (fscanf(fp, "%*s %" STR(MAX_PATH) "s %99s %*s %*d %*d\n", tracefs, type) == 2) {
               if (strcmp(type, "tracefs") == 0)
                       break;
       }
       fclose(fp);

       if (strcmp(type, "tracefs") != 0) {
               fprintf(stderr, "tracefs not mounted");
               return NULL;
       }

       strcat(tracefs, "/tracing/");
       tracefs_found = 1;

       return tracefs;
}

const char *tracing_file(const char *file_name)
{
       static char trace_file[MAX_PATH+1];
       snprintf(trace_file, MAX_PATH, "%s/%s", find_tracefs(), file_name);
       return trace_file;
}

int main (int argc, char **argv)
{
    if (argc < 1)
            exit(-1);

    if (fork() > 0) {
            int fd, ffd;
            char line[64];
            int s;

            ffd = open(tracing_file("current_tracer"), O_WRONLY);
            if (ffd < 0)
                    exit(-1);
            write(ffd, "nop", 3);

            fd = open(tracing_file("set_ftrace_pid"), O_WRONLY);
            s = sprintf(line, "%d\n", getpid());
            write(fd, line, s);

            write(ffd, "function", 8);

            close(fd);
            close(ffd);

            execvp(argv[1], argv+1);
    }

    return 0;
}
```

或者使用以下简单的脚本！

```bash
#!/bin/bash

tracefs=`sed -ne 's/^tracefs \(.*\) tracefs.*/\1/p' /proc/mounts`
echo 0 > $tracefs/tracing_on
echo $$ > $tracefs/set_ftrace_pid
echo function > $tracefs/current_tracer
echo 1 > $tracefs/tracing_on
exec "$@"
```

函数图跟踪器
---------------------------

此跟踪器与函数跟踪器相似，不同之处在于它会在函数进入和退出时进行探测。这是通过在每个`task_struct`中使用动态分配的返回地址栈实现的。当函数进入时，跟踪器会覆盖被跟踪函数的返回地址以设置自定义探针。因此，原始的返回地址会被存储在`task_struct`中的返回地址栈上。

对函数两端进行探测带来了特殊的功能，如：

- 测量函数的执行时间
- 提供可靠的调用栈以绘制函数调用图

此跟踪器在多种情况下非常有用：

- 你想找出奇怪内核行为的原因，并需要详细查看任何区域（或特定区域）
- 你在经历奇怪的延迟，但很难找到其来源
- 你想快速找出某个特定函数所走的路径
- 你只是想窥视正在运行的内核，看看里面发生了什么

```
# tracer: function_graph
#
# CPU  DURATION                  FUNCTION CALLS
# |     |   |                     |   |   |   |

   0)               |  sys_open() {
   0)               |    do_sys_open() {
   0)               |      getname() {
   0)               |        kmem_cache_alloc() {
   0)   1.382 us    |          __might_sleep();
   0)   2.478 us    |        }
   0)               |        strncpy_from_user() {
   0)               |          might_fault() {
   0)   1.389 us    |            __might_sleep();
   0)   2.553 us    |          }
   0)   3.807 us    |        }
   0)   7.876 us    |      }
   0)               |      alloc_fd() {
   0)   0.668 us    |        _spin_lock();
   0)   0.570 us    |        expand_files();
   0)   0.586 us    |        _spin_unlock();
```

有几列可以动态启用/禁用。你可以根据需要使用任意组合的选项：
- 默认启用执行函数所在的CPU编号。有时最好只跟踪一个CPU（参见`tracing_cpumask`文件），或者有时你会在CPU切换时看到无序的函数调用
- 隐藏：`echo nofuncgraph-cpu > trace_options`
    - 显示：`echo funcgraph-cpu > trace_options`

- 函数执行时间（持续时间）默认显示在函数结束括号行上，或者在叶子函数的情况下与当前函数在同一行显示。默认启用。
```plaintext
- 隐藏：echo nofuncgraph-duration > trace_options
- 显示：echo funcgraph-duration > trace_options

- 当达到持续时间阈值时，开销字段在持续时间字段之前
- 隐藏：echo nofuncgraph-overhead > trace_options
- 显示：echo funcgraph-overhead > trace_options
- 依赖于：funcgraph-duration

例如：
```
```
3) # 1837.709 us |          } /* __switch_to */
3)               |          finish_task_switch() {
3)   0.313 us    |            _raw_spin_unlock_irq();
3)   3.177 us    |          }
3) # 1889.063 us |        } /* __schedule */
3) ! 140.417 us  |      } /* __schedule */
3) # 2034.948 us |    } /* schedule */
3) * 33998.59 us |  } /* schedule_preempt_disabled */

...

1)   0.260 us    |              msecs_to_jiffies();
1)   0.313 us    |              __rcu_read_unlock();
1) + 61.770 us   |            }
1) + 64.479 us   |          }
1)   0.313 us    |          rcu_bh_qs();
1)   0.313 us    |          __local_bh_enable();
1) ! 217.240 us  |        }
1)   0.365 us    |        idle_cpu();
1)               |        rcu_irq_exit() {
1)   0.417 us    |          rcu_eqs_enter_common.isra.47();
1)   3.125 us    |        }
1) ! 227.812 us  |      }
1) ! 457.395 us  |    }
1) @ 119760.2 us |  }

...

2)               |    handle_IPI() {
1)   6.979 us    |                  }
2)   0.417 us    |      scheduler_ipi();
1)   9.791 us    |                }
1) + 12.917 us   |              }
2)   3.490 us    |    }
1) + 15.729 us   |            }
1) + 18.542 us   |          }
2) $ 3594274 us  |  }
```

标志：
```
+ 表示函数执行超过 10 微秒
! 表示函数执行超过 100 微秒
# 表示函数执行超过 1000 微秒
* 表示函数执行超过 10 毫秒
@ 表示函数执行超过 100 毫秒
$ 表示函数执行超过 1 秒
```

- 任务/PID 字段显示执行该函数的线程命令行和 PID，默认情况下是隐藏的
- 隐藏：echo nofuncgraph-proc > trace_options
- 显示：echo funcgraph-proc > trace_options

例如：
```
# tracer: function_graph
#
# CPU  TASK/PID        DURATION                  FUNCTION CALLS
# |    |    |           |   |                     |   |   |   |
0)    sh-4802     |               |                  d_free() {
0)    sh-4802     |               |                    call_rcu() {
0)    sh-4802     |               |                      __call_rcu() {
0)    sh-4802     |   0.616 us    |                        rcu_process_gp_end();
0)    sh-4802     |   0.586 us    |                        check_for_new_grace_period();
0)    sh-4802     |   2.899 us    |                      }
0)    sh-4802     |   4.040 us    |                    }
0)    sh-4802     |   5.151 us    |                  }
0)    sh-4802     | + 49.370 us   |                }
```

- 绝对时间字段是由系统时钟提供的自启动以来的时间戳，在每个函数的进入和退出时都会给出这个时间戳的一次快照

- 隐藏：echo nofuncgraph-abstime > trace_options
- 显示：echo funcgraph-abstime > trace_options

例如：
```
#
#      TIME       CPU  DURATION                  FUNCTION CALLS
#       |         |     |   |                     |   |   |   |
360.774522 |   1)   0.541 us    |                                          }
360.774522 |   1)   4.663 us    |                                        }
360.774523 |   1)   0.541 us    |                                        __wake_up_bit();
360.774524 |   1)   6.796 us    |                                      }
360.774524 |   1)   7.952 us    |                                    }
360.774525 |   1)   9.063 us    |                                  }
360.774525 |   1)   0.615 us    |                                  journal_mark_dirty();
360.774527 |   1)   0.578 us    |                                  __brelse();
360.774528 |   1)               |                                  reiserfs_prepare_for_journal() {
360.774528 |   1)               |                                    unlock_buffer() {
360.774529 |   1)               |                                      wake_up_bit() {
360.774529 |   1)               |                                        bit_waitqueue() {
360.774530 |   1)   0.594 us    |                                          __phys_addr();
```

如果某个函数的开始不在跟踪缓冲区中，则该函数名称始终显示在闭合括号之后。
可以在跟踪缓冲区中的函数名称后启用闭合括号后的函数名称显示，以便更容易地使用 grep 搜索函数持续时间。
```
默认情况下是禁用的。
- 隐藏：`echo nofuncgraph-tail > trace_options`
  - 显示：`echo funcgraph-tail > trace_options`

  在没有启用 `funcgraph-tail` 的情况下（默认）的例子如下：

    0)               |      putname() {
    0)               |        kmem_cache_free() {
    0)   0.518 us    |          __phys_addr();
    0)   1.757 us    |        }
    0)   2.861 us    |      }

  启用 `funcgraph-tail` 的例子如下：

    0)               |      putname() {
    0)               |        kmem_cache_free() {
    0)   0.518 us    |          __phys_addr();
    0)   1.757 us    |        } /* kmem_cache_free() */
    0)   2.861 us    |      } /* putname() */

每个被跟踪函数的返回值可以在等号“=”后面显示。当遇到系统调用失败时，这有助于快速定位首次返回错误代码的函数。
- 隐藏：`echo nofuncgraph-retval > trace_options`
  - 显示：`echo funcgraph-retval > trace_options`

  启用 `funcgraph-retval` 的例子如下：

    1)               |    cgroup_migrate() {
    1)   0.651 us    |      cgroup_migrate_add_task(); /* = 0xffff93fcfd346c00 */
    1)               |      cgroup_migrate_execute() {
    1)               |        cpu_cgroup_can_attach() {
    1)               |          cgroup_taskset_first() {
    1)   0.732 us    |            cgroup_taskset_next(); /* = 0xffff93fc8fb20000 */
    1)   1.232 us    |          } /* cgroup_taskset_first = 0xffff93fc8fb20000 */
    1)   0.380 us    |          sched_rt_can_attach(); /* = 0x0 */
    1)   2.335 us    |        } /* cpu_cgroup_can_attach = -22 */
    1)   4.369 us    |      } /* cgroup_migrate_execute = -22 */
    1)   7.143 us    |    } /* cgroup_migrate = -22 */

上述例子表明，`cpu_cgroup_can_attach` 函数首先返回了错误代码 -22，然后我们可以阅读该函数的代码以找到根本原因。
当 `funcgraph-retval-hex` 选项未设置时，返回值将以智能方式显示。具体来说，如果它是错误代码，则将以有符号十进制格式打印，否则将以十六进制格式打印。
- 智能：`echo nofuncgraph-retval-hex > trace_options`
  - 十六进制：`echo funcgraph-retval-hex > trace_options`

  启用 `funcgraph-retval-hex` 的例子如下：

    1)               |      cgroup_migrate() {
    1)   0.651 us    |        cgroup_migrate_add_task(); /* = 0xffff93fcfd346c00 */
    1)               |        cgroup_migrate_execute() {
    1)               |          cpu_cgroup_can_attach() {
    1)               |            cgroup_taskset_first() {
    1)   0.732 us    |              cgroup_taskset_next(); /* = 0xffff93fc8fb20000 */
    1)   1.232 us    |            } /* cgroup_taskset_first = 0xffff93fc8fb20000 */
    1)   0.380 us    |            sched_rt_can_attach(); /* = 0x0 */
    1)   2.335 us    |          } /* cpu_cgroup_can_attach = 0xffffffea */
    1)   4.369 us    |        } /* cgroup_migrate_execute = 0xffffffea */
    1)   7.143 us    |      } /* cgroup_migrate = 0xffffffea */

目前，在使用 `funcgraph-retval` 选项时存在一些限制，这些限制将在未来得到解决：
- 即使函数的返回类型为 `void`，仍然会打印一个返回值，可以忽略它。
- 即使返回值存储在多个寄存器中，也只会记录和打印第一个寄存器中的值。

例如，在 x86 架构中，eax 和 edx 用于存储 64 位返回值，其中低 32 位保存在 eax 中，高 32 位保存在 edx 中。但是，只会记录和打印 eax 中的值。
- 在某些过程调用标准（如 arm64 的 AAPCS64）中，当类型小于通用寄存器（GPR）时，由消费者负责进行缩小处理，并且高位可能包含未知值。

因此，建议检查代码中的这种情况。例如，当在一个 64 位 GPR 中使用 u8 时，位 [63:8] 可能包含任意值，尤其是在较大类型被截断（显式或隐式）时。

以下是几个具体的情况来说明这一点：

**案例一**：

函数 `narrow_to_u8` 定义如下：

```c
u8 narrow_to_u8(u64 val)
{
    // 隐式截断
    return val;
}
```

可能编译为：

```
narrow_to_u8:
    <... ftrace instrumentations ...>
    RET
```

如果你传递 0x123456789abcdef 给这个函数并希望将其缩小，它可能会被记录为 0x123456789abcdef 而不是 0xef。
**案例二**：

函数 `error_if_not_4g_aligned` 定义如下：

```c
int error_if_not_4g_aligned(u64 val)
{
    if (val & GENMASK(31, 0))
        return -EINVAL;

    return 0;
}
```

它可能被编译为：

```assembly
error_if_not_4g_aligned:
    CBNZ    w0, .Lnot_aligned
    RET     // 位[31:0]为零，位[63:32]未知
.Lnot_aligned:
    MOV    x0, #-EINVAL
    RET
```

当传递值 `0x2_0000_0000` 给该函数时，返回值可能会记录为 `0x2_0000_0000` 而不是 `0`。

你可以使用 `trace_printk()` 对特定函数添加注释。例如，如果你想在 `__might_sleep()` 函数内部添加注释，只需包含 `<linux/ftrace.h>` 并在 `__might_sleep()` 内部调用 `trace_printk()`：

```c
trace_printk("我是一条评论！\n");
```

这将产生如下输出：

```
1)               |             __might_sleep() {
1)               |                /* 我是一条评论！ */
1)   1.449 us    |             }
```

你可以在接下来的“动态 ftrace”部分中找到其他有用的特性，例如仅追踪特定的函数或任务。

### 动态 ftrace

如果设置了 `CONFIG_DYNAMIC_FTRACE`，则系统在禁用函数追踪时几乎不会产生开销。其工作原理是 `mcount` 函数调用（放置在每个内核函数的开始处，由 gcc 的 `-pg` 选项生成）最初指向一个简单的返回语句。（启用 FTRACE 将会在编译内核时包含 `-pg` 选项。）

在编译时，每个 C 文件对象都会通过 `scripts` 目录中的 `recordmcount` 程序处理。该程序会解析 C 对象中的 ELF 头以查找所有调用 `mcount` 的位置。从 gcc 版本 4.6 开始，对于 x86 架构增加了 `-mfentry` 选项，该选项调用的是 `__fentry__` 而不是 `mcount`，且在创建栈帧之前调用。
请注意，并非所有部分都被追踪。它们可以通过 `notrace` 或其他方式阻止，所有内联函数也不会被追踪。检查 `available_filter_functions` 文件以查看哪些函数可以被追踪。

创建了一个名为 `__mcount_loc` 的节，其中包含了 `.text` 段中所有 `mcount`/`fentry` 调用位置的引用。

`recordmcount` 程序将这个节重新链接回原始对象。内核最终链接阶段会将所有这些引用添加到一个单一表中。

在启动时，在 SMP 初始化之前，动态 ftrace 代码会扫描此表并将所有位置更新为 NOP 操作。同时记录这些位置，并将其添加到 `available_filter_functions` 列表中。模块在加载和执行之前会被处理，当模块卸载时，也会从 ftrace 函数列表中移除其函数。这是自动完成的，模块作者无需担心这一点。

当启用追踪时，修改函数追踪点的过程取决于架构。旧方法是使用 `kstop_machine` 来防止 CPU 执行被修改的代码（这可能导致 CPU 执行不可预测的操作，特别是在修改的代码跨越缓存或页面边界的情况下），并将 NOP 修补回调。但这次，它们不再调用 `mcount`（只是一个函数存根）。现在它们调用 ftrace 基础设施。

修改函数追踪点的新方法是在要修改的位置设置断点，同步所有 CPU，修改未被断点覆盖的指令部分。再次同步所有 CPU，然后移除断点并替换为最终版本的 ftrace 调用位置。

一些架构甚至不需要进行同步操作，可以直接将新代码覆盖在旧代码上，而不会遇到其他 CPU 同时执行的问题。
记录被追踪函数的一个特殊副作用是我们现在可以选择性地决定追踪哪些函数，并将哪些函数的mcount调用保持为nop（无操作）。
使用两个文件，一个用于启用追踪，另一个用于禁用追踪。这两个文件分别是：

  set_ftrace_filter

和

  set_ftrace_notrace

一个可以添加到这些文件中的可用函数列表如下所示：

   available_filter_functions

::

  # cat available_filter_functions
  put_prev_task_idle
  kmem_cache_create
  pick_next_task_rt
  cpus_read_lock
  pick_next_task_fair
  mutex_lock
  [...]

如果我只对sys_nanosleep和hrtimer_interrupt感兴趣：

::

  # echo sys_nanosleep hrtimer_interrupt > set_ftrace_filter
  # echo function > current_tracer
  # echo 1 > tracing_on
  # usleep 1
  # echo 0 > tracing_on
  # cat trace
  # tracer: function
  #
  # entries-in-buffer/entries-written: 5/5   #P:4
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
            usleep-2665  [001] ....  4186.475355: sys_nanosleep <-system_call_fastpath
            <idle>-0     [001] d.h1  4186.475409: hrtimer_interrupt <-smp_apic_timer_interrupt
            usleep-2665  [001] d.h1  4186.475426: hrtimer_interrupt <-smp_apic_timer_interrupt
            <idle>-0     [003] d.h1  4186.475426: hrtimer_interrupt <-smp_apic_timer_interrupt
            <idle>-0     [002] d.h1  4186.475427: hrtimer_interrupt <-smp_apic_timer_interrupt

要查看正在追踪的函数，可以使用以下命令：

::

  # cat set_ftrace_filter
  hrtimer_interrupt
  sys_nanosleep

这可能还不够。过滤器还支持glob(7)匹配模式：
``<match>*``
	将匹配以<match>开头的函数
``*<match>``
	将匹配以<match>结尾的函数
``*<match>*``
	将匹配包含<match>的函数
``<match1>*<match2>``
	将匹配以<match1>开头且以<match2>结尾的函数

注意：
	最好使用引号来包围通配符，否则shell可能会将其扩展为本地目录中文件的名字
::

  # echo 'hrtimer_*' > set_ftrace_filter

结果如下：

::

  # tracer: function
  #
  # entries-in-buffer/entries-written: 897/897   #P:4
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
            <idle>-0     [003] dN.1  4228.547803: hrtimer_cancel <-tick_nohz_idle_exit
            <idle>-0     [003] dN.1  4228.547804: hrtimer_try_to_cancel <-hrtimer_cancel
            <idle>-0     [003] dN.2  4228.547805: hrtimer_force_reprogram <-__remove_hrtimer
            <idle>-0     [003] dN.1  4228.547805: hrtimer_forward <-tick_nohz_idle_exit
            <idle>-0     [003] dN.1  4228.547805: hrtimer_start_range_ns <-hrtimer_start_expires.constprop.11
            <idle>-0     [003] d..1  4228.547858: hrtimer_get_next_event <-get_next_timer_interrupt
            <idle>-0     [003] d..1  4228.547859: hrtimer_start <-__tick_nohz_idle_enter
            <idle>-0     [003] d..2  4228.547860: hrtimer_force_reprogram <-__rem

注意到我们丢失了sys_nanosleep

::

  # cat set_ftrace_filter
  hrtimer_run_queues
  hrtimer_run_pending
  hrtimer_init
  hrtimer_cancel
  hrtimer_try_to_cancel
  hrtimer_forward
  hrtimer_start
  hrtimer_reprogram
  hrtimer_force_reprogram
  hrtimer_get_next_event
  hrtimer_interrupt
  hrtimer_nanosleep
  hrtimer_wakeup
  hrtimer_get_remaining
  hrtimer_get_res
  hrtimer_init_sleeper

这是因为'>'和'>>'的行为类似于bash中的行为
要重写过滤器，请使用'>'
要追加到过滤器，请使用'>>'

要清除过滤器以便再次记录所有函数：

 ::

  # echo > set_ftrace_filter
  # cat set_ftrace_filter
  #

再次，我们现在想要追加

 ::

  # echo sys_nanosleep > set_ftrace_filter
  # cat set_ftrace_filter
  sys_nanosleep
  # echo 'hrtimer_*' >> set_ftrace_filter
  # cat set_ftrace_filter
  hrtimer_run_queues
  hrtimer_run_pending
  hrtimer_init
  hrtimer_cancel
  hrtimer_try_to_cancel
  hrtimer_forward
  hrtimer_start
  hrtimer_reprogram
  hrtimer_force_reprogram
  hrtimer_get_next_event
  hrtimer_interrupt
  sys_nanosleep
  hrtimer_nanosleep
  hrtimer_wakeup
  hrtimer_get_remaining
  hrtimer_get_res
  hrtimer_init_sleeper

set_ftrace_notrace会阻止这些函数被追踪

 ::

  # echo '*preempt*' '*lock*' > set_ftrace_notrace

结果如下：

 ::

  # tracer: function
  #
  # entries-in-buffer/entries-written: 39608/39608   #P:4
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
              bash-1994  [000] ....  4342.324896: file_ra_state_init <-do_dentry_open
              bash-1994  [000] ....  4342.324897: open_check_o_direct <-do_last
              bash-1994  [000] ....  4342.324897: ima_file_check <-do_last
              bash-1994  [000] ....  4342.324898: process_measurement <-ima_file_check
              bash-1994  [000] ....  4342.324898: ima_get_action <-process_measurement
              bash-1994  [000] ....  4342.324898: ima_match_policy <-ima_get_action
              bash-1994  [000] ....  4342.324899: do_truncate <-do_last
              bash-1994  [000] ....  4342.324899: setattr_should_drop_suidgid <-do_truncate
              bash-1994  [000] ....  4342.324899: notify_change <-do_truncate
              bash-1994  [000] ....  4342.324900: current_fs_time <-notify_change
              bash-1994  [000] ....  4342.324900: current_kernel_time <-current_fs_time
              bash-1994  [000] ....  4342.324900: timespec_trunc <-current_fs_time

我们可以看到不再有lock或preempt的追踪

通过索引选择函数过滤器
-------------------------------

由于字符串处理较为昂贵（需要查找函数地址才能与传入的字符串进行比较），也可以使用索引来启用函数。这对于一次性设置数千个特定函数的情况非常有用。通过传递一系列数字，不会发生任何字符串处理。相反，将选择内部数组（对应于“available_filter_functions”文件中的函数）中特定位置的函数。

 ::

  # echo 1 > set_ftrace_filter

将选择“available_filter_functions”中列出的第一个函数

 ::

  # head -1 available_filter_functions
  trace_initcall_finish_cb

  # cat set_ftrace_filter
  trace_initcall_finish_cb

  # head -50 available_filter_functions | tail -1
  x86_pmu_commit_txn

  # echo 1 50 > set_ftrace_filter
  # cat set_ftrace_filter
  trace_initcall_finish_cb
  x86_pmu_commit_txn

动态ftrace与函数图追踪器
------------------------------

尽管上述内容适用于函数追踪器和函数图追踪器，但函数图追踪器具有一些特殊的特性。
如果你只想追踪一个函数及其所有子函数，只需要将其名称写入 `set_graph_function` 中：

```
echo __do_fault > set_graph_function
```

这将生成 `__do_fault()` 函数的如下“扩展”追踪记录：

```
   0)               |  __do_fault() {
   0)               |    filemap_fault() {
   0)               |      find_lock_page() {
   0)   0.804 us    |        find_get_page();
   0)               |        __might_sleep() {
   0)   1.329 us    |        }
   0)   3.904 us    |      }
   0)   4.979 us    |    }
   0)   0.653 us    |    _spin_lock();
   0)   0.578 us    |    page_add_file_rmap();
   0)   0.525 us    |    native_set_pte_at();
   0)   0.585 us    |    _spin_unlock();
   0)               |    unlock_page() {
   0)   0.541 us    |      page_waitqueue();
   0)   0.639 us    |      __wake_up_bit();
   0)   2.786 us    |    }
   0) + 14.237 us   |  }
   0)               |  __do_fault() {
   0)               |    filemap_fault() {
   0)               |      find_lock_page() {
   0)   0.698 us    |        find_get_page();
   0)               |        __might_sleep() {
   0)   1.412 us    |        }
   0)   3.950 us    |      }
   0)   5.098 us    |    }
   0)   0.631 us    |    _spin_lock();
   0)   0.571 us    |    page_add_file_rmap();
   0)   0.526 us    |    native_set_pte_at();
   0)   0.586 us    |    _spin_unlock();
   0)               |    unlock_page() {
   0)   0.533 us    |      page_waitqueue();
   0)   0.638 us    |      __wake_up_bit();
   0)   2.793 us    |    }
   0) + 14.012 us   |  }
```

你也可以同时扩展多个函数：

```
echo sys_open > set_graph_function
echo sys_close >> set_graph_function
```

如果想回到追踪所有函数的状态，可以通过以下命令清除这个特殊的过滤器：

```
echo > set_graph_function
```

### ftrace_enabled

注意，`sysctl ftrace_enable` 是一个用于控制函数追踪的大开关。默认情况下它是启用的（当内核启用了函数追踪）。如果禁用它，则所有的函数追踪都会被禁用。这不仅包括 ftrace 的函数追踪，还包括其他任何用途（如 perf、kprobes、堆栈追踪、性能分析等）。如果设置了 `FTRACE_OPS_FL_PERMANENT` 标志的回调已注册，则不能禁用此功能。

请谨慎禁用此功能。
可以通过以下命令禁用或启用它：

```
sysctl kernel.ftrace_enabled=0
sysctl kernel.ftrace_enabled=1
```

或者

```
echo 0 > /proc/sys/kernel/ftrace_enabled
echo 1 > /proc/sys/kernel/ftrace_enabled
```

### 过滤命令

`set_ftrace_filter` 接口支持一些命令。追踪命令的格式如下：

```
<function>:<command>:<parameter>
```

支持以下命令：

- `mod`：
  此命令允许按模块进行函数过滤。参数定义了模块。例如，如果只想要追踪 `ext3` 模块中的 `write*` 函数，可以运行：

  ```
  echo 'write*:mod:ext3' > set_ftrace_filter
  ```

  此命令与基于函数名的过滤方式交互相同。因此，在不同模块中添加更多函数可以通过追加（`>>`）到过滤文件实现。通过在命令前加上 `!` 来移除特定模块的函数：

  ```
  echo '!writeback*:mod:ext3' >> set_ftrace_filter
  ```

  `mod` 命令支持模块通配符。禁用除特定模块外的所有函数追踪：

  ```
  echo '!*:mod:!ext3' >> set_ftrace_filter
  ```

  禁用所有模块的追踪，但仍追踪内核：

  ```
  echo '!*:mod:*' >> set_ftrace_filter
  ```

  只启用内核的过滤：

  ```
  echo '*write*:mod:!*' >> set_ftrace_filter
  ```

  启用模块通配符的过滤：

  ```
  echo '*write*:mod:*snd*' >> set_ftrace_filter
  ```

- `traceon/traceoff`：
  这些命令会在指定函数被调用时启动或关闭追踪。参数确定了追踪系统启动和关闭的次数。如果没有指定次数，则没有限制。例如，要禁用首次触发 `__schedule_bug` 时的追踪，可以运行：

  ```
  echo '__schedule_bug:traceoff:5' > set_ftrace_filter
  ```

  要始终禁用 `__schedule_bug` 触发时的追踪：

  ```
  echo '__schedule_bug:traceoff' > set_ftrace_filter
  ```

  这些命令无论是否追加到 `set_ftrace_filter` 文件都是累积的。要移除一个命令，可以在其前加上 `!` 并去掉参数：

  ```
  echo '!__schedule_bug:traceoff:0' > set_ftrace_filter
  ```

  上述命令会移除带有计数器的 `__schedule_bug` 的 `traceoff` 命令。要移除不带计数器的命令：

  ```
  echo '!__schedule_bug:traceoff' > set_ftrace_filter
  ```

- `snapshot`：
  当函数被调用时触发快照：

  ```
  echo 'native_flush_tlb_others:snapshot' > set_ftrace_filter
  ```

  只触发一次快照：

  ```
  echo 'native_flush_tlb_others:snapshot:1' > set_ftrace_filter
  ```

  移除上述命令：

  ```
  echo '!native_flush_tlb_others:snapshot' > set_ftrace_filter
  echo '!native_flush_tlb_others:snapshot:0' > set_ftrace_filter
  ```

- `enable_event/disable_event`：
  这些命令可以启用或禁用一个追踪事件。注意，由于函数追踪回调非常敏感，当这些命令注册时，追踪点会被激活，但以“软”模式禁用。也就是说，追踪点会被调用，但不会被追踪。只要存在触发该事件的命令，该事件追踪点就会保持这种模式：

  ```
  echo 'try_to_wake_up:enable_event:sched:sched_switch:2' > set_ftrace_filter
  ```

  格式为：

  ```
  <function>:enable_event:<system>:<event>[:count]
  <function>:disable_event:<system>:<event>[:count]
  ```

  移除事件命令：

  ```
  echo '!try_to_wake_up:enable_event:sched:sched_switch:0' > set_ftrace_filter
  echo '!schedule:disable_event:sched:sched_switch' > set_ftrace_filter
  ```

- `dump`：
  当函数被调用时，会将 ftrace 环形缓冲区的内容输出到控制台。这对于调试很有用，当你需要在某个函数被调用时输出追踪信息时尤其有用。也许这是一个在三重故障发生前被调用的函数，不允许你获取常规的转储。

- `cpudump`：
  当函数被调用时，会将当前 CPU 的 ftrace 环形缓冲区的内容输出到控制台。与 `dump` 命令不同，它只输出执行触发转储的函数的 CPU 的环形缓冲区内容。

- `stacktrace`：
  当函数被调用时，记录一个堆栈跟踪。

### trace_pipe

`trace_pipe` 输出的内容与 `trace` 文件相同，但对追踪的影响不同。每次从 `trace_pipe` 读取的内容都会被消费掉。这意味着后续读取的内容会有所不同。追踪是实时的：

```
# echo function > current_tracer
# cat trace_pipe > /tmp/trace.out &
[1] 4153
# echo 1 > tracing_on
# usleep 1
# echo 0 > tracing_on
# cat trace
# tracer: function
#
# entries-in-buffer/entries-written: 0/0   #P:4
#
#                              _-----=> irqs-off
#                             / _----=> need-resched
#                            | / _---=> hardirq/softirq
#                            || / _--=> preempt-depth
#                            ||| /     delay
#           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
#              | |       |   ||||       |         |
#
# cat /tmp/trace.out
             bash-1994  [000] ....  5281.568961: mutex_unlock <-rb_simple_write
             bash-1994  [000] ....  5281.568963: __mutex_unlock_slowpath <-mutex_unlock
             bash-1994  [000] ....  5281.568963: __fsnotify_parent <-fsnotify_modify
             bash-1994  [000] ....  5281.568964: fsnotify <-fsnotify_modify
             bash-1994  [000] ....  5281.568964: __srcu_read_lock <-fsnotify
             bash-1994  [000] ....  5281.568964: add_preempt_count <-__srcu_read_lock
             bash-1994  [000] ...1  5281.568965: sub_preempt_count <-__srcu_read_lock
             bash-1994  [000] ....  5281.568965: __srcu_read_unlock <-fsnotify
             bash-1994  [000] ....  5281.568967: sys_dup2 <-system_call_fastpath
```

注意，读取 `trace_pipe` 文件会阻塞直到有更多的输入。这与 `trace` 文件相反。如果任何进程打开了 `trace` 文件进行读取，实际上会禁用追踪并阻止新的条目被添加。`trace_pipe` 文件没有这个限制。
跟踪条目
------------

过多或过少的数据在诊断内核问题时可能会带来麻烦。文件`buffer_size_kb`用于修改内部跟踪缓冲区的大小。列出的数字表示每个CPU可以记录的条目数量。要了解完整大小，请将可能的CPU数量乘以条目数：
::

  # cat buffer_size_kb
  1408（单位：千字节）

或者直接读取`buffer_total_size_kb`：
::

  # cat buffer_total_size_kb 
  5632

要修改缓冲区，只需回显一个数字（以1024字节为单位）：
::

  # echo 10000 > buffer_size_kb
  # cat buffer_size_kb
  10000（单位：千字节）

它会尝试分配尽可能多的空间。如果你分配得太多，可能会导致内存不足错误：
::

  # echo 1000000000000 > buffer_size_kb
  -bash: echo: 写入错误：无法分配内存
  # cat buffer_size_kb
  85

每个CPU的缓冲区也可以单独更改：
::

  # echo 10000 > per_cpu/cpu0/buffer_size_kb
  # echo 100 > per_cpu/cpu1/buffer_size_kb

当每个CPU的缓冲区不同时，顶级的`buffer_size_kb`将显示一个X：
::

  # cat buffer_size_kb
  X

这时`buffer_total_size_kb`就变得有用：
::

  # cat buffer_total_size_kb 
  12916

写入顶级的`buffer_size_kb`将使所有缓冲区再次保持一致。
快照
-------
`CONFIG_TRACER_SNAPSHOT`使所有非延迟追踪器都可以使用通用快照功能。（记录最大延迟的延迟追踪器如“irqsoff”或“wakeup”不能使用此功能，因为这些追踪器已经内部使用了快照机制。）

快照可以在特定时间点保留当前的跟踪缓冲区而不停止追踪。Ftrace会用备用缓冲区替换当前缓冲区，并继续在新的当前缓冲区中进行追踪（即之前的备用缓冲区）。
以下`tracefs`中的文件与该功能相关：

  快照：

  此文件用于获取快照并读取快照输出。向此文件回显1以分配一个备用缓冲区并获取快照（交换），然后从该文件中以与“trace”相同的格式读取快照（在“文件系统”部分中描述）。读取快照和追踪可以并行执行。当备用缓冲区被分配后，回显0将其释放，回显其他（正数）值则清除快照内容。
更多细节如下表所示：
+--------------+------------+------------+------------+
| 状态\输入 |     0      |     1      |    else    |
+==============+============+============+============+
| 未分配 | (不做任何事) | 分配+交换 | (不做任何事) |
+--------------+------------+------------+------------+
| 已分配 |    释放    |    交换    |   清除    |
+--------------+------------+------------+------------+

以下是使用快照功能的一个示例：
::

  # echo 1 > events/sched/enable
  # echo 1 > snapshot
  # cat snapshot
  # tracer: nop
  #
  # entries-in-buffer/entries-written: 71/71   #P:8
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
            <idle>-0     [005] d...  2440.603828: sched_switch: prev_comm=swapper/5 prev_pid=0 prev_prio=120   prev_state=R ==> next_comm=snapshot-test-2 next_pid=2242 next_prio=120
             sleep-2242  [005] d...  2440.603846: sched_switch: prev_comm=snapshot-test-2 prev_pid=2242 prev_prio=120   prev_state=R ==> next_comm=kworker/5:1 next_pid=60 next_prio=120
  [...]
          <idle>-0     [002] d...  2440.707230: sched_switch: prev_comm=swapper/2 prev_pid=0 prev_prio=120 prev_state=R ==> next_comm=snapshot-test-2 next_pid=2229 next_prio=120  

  # cat trace  
  # tracer: nop
  #
  # entries-in-buffer/entries-written: 77/77   #P:8
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
            <idle>-0     [007] d...  2440.707395: sched_switch: prev_comm=swapper/7 prev_pid=0 prev_prio=120 prev_state=R ==> next_comm=snapshot-test-2 next_pid=2243 next_prio=120
   snapshot-test-2-2229  [002] d...  2440.707438: sched_switch: prev_comm=snapshot-test-2 prev_pid=2229 prev_prio=120 prev_state=S ==> next_comm=swapper/2 next_pid=0 next_prio=120
  [...]

如果你试图在当前追踪器是延迟追踪器之一的情况下使用此快照功能，你将得到以下结果：
::

  # echo wakeup > current_tracer
  # echo 1 > snapshot
  bash: echo: 写入错误：设备或资源忙
  # cat snapshot
  cat: snapshot: 设备或资源忙

实例
---------
在`tracefs`追踪目录中，有一个名为“instances”的目录。
此目录可以使用 `mkdir` 创建新的子目录，并使用 `rmdir` 删除子目录。在此目录中使用 `mkdir` 创建的子目录在创建后将已经包含文件和其他子目录。

```
# mkdir instances/foo
# ls instances/foo
buffer_size_kb  buffer_total_size_kb  events  free_buffer  per_cpu
set_event  snapshot  trace  trace_clock  trace_marker  trace_options
trace_pipe  tracing_on
```

如您所见，新目录看起来与追踪目录本身非常相似。事实上，它们非常相似，只是缓冲区和事件与主目录以及其他创建的实例无关。新目录中的文件与追踪目录中同名的文件功能相同，只是使用的缓冲区是独立且全新的。这些文件只影响各自的缓冲区，而不影响主缓冲区，除了 `trace_options` 文件。目前，`trace_options` 文件对所有实例和顶层缓冲区的影响是一样的，但未来版本可能会改变这一点，即选项可能会变得仅对其所在实例有效。

请注意，这里没有函数追踪器文件、`current_tracer` 或 `available_tracers` 文件。这是因为当前缓冲区只能启用事件。

```
# mkdir instances/foo
# mkdir instances/bar
# mkdir instances/zoot
# echo 100000 > buffer_size_kb
# echo 1000 > instances/foo/buffer_size_kb
# echo 5000 > instances/bar/per_cpu/cpu1/buffer_size_kb
# echo function > current_trace
# echo 1 > instances/foo/events/sched/sched_wakeup/enable
# echo 1 > instances/foo/events/sched/sched_wakeup_new/enable
# echo 1 > instances/foo/events/sched/sched_switch/enable
# echo 1 > instances/bar/events/irq/enable
# echo 1 > instances/zoot/events/syscalls/enable
# cat trace_pipe
CPU:2 [LOST 11745 EVENTS]
              bash-2044  [002] .... 10594.481032: _raw_spin_lock_irqsave <-get_page_from_freelist
              bash-2044  [002] d... 10594.481032: add_preempt_count <-_raw_spin_lock_irqsave
              bash-2044  [002] d..1 10594.481032: __rmqueue <-get_page_from_freelist
              bash-2044  [002] d..1 10594.481033: _raw_spin_unlock <-get_page_from_freelist
              bash-2044  [002] d..1 10594.481033: sub_preempt_count <-_raw_spin_unlock
              bash-2044  [002] d... 10594.481033: get_pageblock_flags_group <-get_pageblock_migratetype
              bash-2044  [002] d... 10594.481034: __mod_zone_page_state <-get_page_from_freelist
              bash-2044  [002] d... 10594.481034: zone_statistics <-get_page_from_freelist
              bash-2044  [002] d... 10594.481034: __inc_zone_state <-zone_statistics
              bash-2044  [002] d... 10594.481034: __inc_zone_state <-zone_statistics
              bash-2044  [002] .... 10594.481035: arch_dup_task_struct <-copy_process
  [...]

  # cat instances/foo/trace_pipe
              bash-1998  [000] d..4   136.676759: sched_wakeup: comm=kworker/0:1 pid=59 prio=120 success=1 target_cpu=000
              bash-1998  [000] dN.4   136.676760: sched_wakeup: comm=bash pid=1998 prio=120 success=1 target_cpu=000
            <idle>-0     [003] d.h3   136.676906: sched_wakeup: comm=rcu_preempt pid=9 prio=120 success=1 target_cpu=003
            <idle>-0     [003] d..3   136.676909: sched_switch: prev_comm=swapper/3 prev_pid=0 prev_prio=120 prev_state=R ==> next_comm=rcu_preempt next_pid=9 next_prio=120
       rcu_preempt-9     [003] d..3   136.676916: sched_switch: prev_comm=rcu_preempt prev_pid=9 prev_prio=120 prev_state=S ==> next_comm=swapper/3 next_pid=0 next_prio=120
              bash-1998  [000] d..4   136.677014: sched_wakeup: comm=kworker/0:1 pid=59 prio=120 success=1 target_cpu=000
              bash-1998  [000] dN.4   136.677016: sched_wakeup: comm=bash pid=1998 prio=120 success=1 target_cpu=000
              bash-1998  [000] d..3   136.677018: sched_switch: prev_comm=bash prev_pid=1998 prev_prio=120 prev_state=R+ ==> next_comm=kworker/0:1 next_pid=59 next_prio=120
       kworker/0:1-59    [000] d..4   136.677022: sched_wakeup: comm=sshd pid=1995 prio=120 success=1 target_cpu=001
       kworker/0:1-59    [000] d..3   136.677025: sched_switch: prev_comm=kworker/0:1 prev_pid=59 prev_prio=120 prev_state=S ==> next_comm=bash next_pid=1998 next_prio=120
  [...]

  # cat instances/bar/trace_pipe
       migration/1-14    [001] d.h3   138.732674: softirq_raise: vec=3 [action=NET_RX]
            <idle>-0     [001] dNh3   138.732725: softirq_raise: vec=3 [action=NET_RX]
              bash-1998  [000] d.h1   138.733101: softirq_raise: vec=1 [action=TIMER]
              bash-1998  [000] d.h1   138.733102: softirq_raise: vec=9 [action=RCU]
              bash-1998  [000] ..s2   138.733105: softirq_entry: vec=1 [action=TIMER]
              bash-1998  [000] ..s2   138.733106: softirq_exit: vec=1 [action=TIMER]
              bash-1998  [000] ..s2   138.733106: softirq_entry: vec=9 [action=RCU]
              bash-1998  [000] ..s2   138.733109: softirq_exit: vec=9 [action=RCU]
              sshd-1995  [001] d.h1   138.733278: irq_handler_entry: irq=21 name=uhci_hcd:usb4
              sshd-1995  [001] d.h1   138.733280: irq_handler_exit: irq=21 ret=unhandled
              sshd-1995  [001] d.h1   138.733281: irq_handler_entry: irq=21 name=eth0
              sshd-1995  [001] d.h1   138.733283: irq_handler_exit: irq=21 ret=handled
  [...]

  # cat instances/zoot/trace
  # tracer: nop
  #
  # entries-in-buffer/entries-written: 18996/18996   #P:4
  #
  #                              _-----=> irqs-off
  #                             / _----=> need-resched
  #                            | / _---=> hardirq/softirq
  #                            || / _--=> preempt-depth
  #                            ||| /     delay
  #           TASK-PID   CPU#  ||||    TIMESTAMP  FUNCTION
  #              | |       |   ||||       |         |
              bash-1998  [000] d...   140.733501: sys_write -> 0x2
              bash-1998  [000] d...   140.733504: sys_dup2(oldfd: a, newfd: 1)
              bash-1998  [000] d...   140.733506: sys_dup2 -> 0x1
              bash-1998  [000] d...   140.733508: sys_fcntl(fd: a, cmd: 1, arg: 0)
              bash-1998  [000] d...   140.733509: sys_fcntl -> 0x1
              bash-1998  [000] d...   140.733510: sys_close(fd: a)
              bash-1998  [000] d...   140.733510: sys_close -> 0x0
              bash-1998  [000] d...   140.733514: sys_rt_sigprocmask(how: 0, nset: 0, oset: 6e2768, sigsetsize: 8)
              bash-1998  [000] d...   140.733515: sys_rt_sigprocmask -> 0x0
              bash-1998  [000] d...   140.733516: sys_rt_sigaction(sig: 2, act: 7fff718846f0, oact: 7fff71884650, sigsetsize: 8)
              bash-1998  [000] d...   140.733516: sys_rt_sigaction -> 0x0

可以看到，顶级追踪缓冲区的追踪信息仅显示函数追踪。`foo` 实例则显示唤醒和任务切换。

要移除这些实例，只需删除其对应的目录：
```
# rmdir instances/foo
# rmdir instances/bar
# rmdir instances/zoot

注意，如果某个进程在一个实例目录中打开了一个追踪文件，则 `rmdir` 命令会因 `EBUSY` 而失败。

堆栈跟踪
---------
由于内核具有固定大小的堆栈，因此在函数中浪费堆栈空间是非常重要的问题。内核开发者必须意识到他们在堆栈上分配的内容。如果分配过多，系统可能会面临堆栈溢出的风险，从而导致系统崩溃。
有一些工具可以检查这一点，通常是通过定期中断来检查使用情况。但如果能够在每次函数调用时进行检查，将会非常有用。由于 ftrace 提供了函数追踪器，它使得在每次函数调用时检查堆栈大小变得方便。这可以通过启用堆栈追踪实现。
`CONFIG_STACK_TRACER` 启用了 ftrace 的堆栈追踪功能。
要启用它，请向 `/proc/sys/kernel/stack_tracer_enabled` 写入 `1`。
# echo 1 > /proc/sys/kernel/stack_tracer_enabled

您也可以在内核命令行中启用它来追踪启动期间内核的栈大小，方法是在内核命令行参数中添加 "stacktrace"。
运行几分钟后，输出看起来像这样：

```
# cat stack_max_size
2928

# cat stack_trace
          深度    大小   位置    （共18条记录）
          -----    ----   --------
 0)     2928     224   update_sd_lb_stats+0xbc/0x4ac
 1)     2704     160   find_busiest_group+0x31/0x1f1
 2)     2544     256   load_balance+0xd9/0x662
 3)     2288      80   idle_balance+0xbb/0x130
 4)     2208     128   __schedule+0x26e/0x5b9
 5)     2080      16   schedule+0x64/0x66
 6)     2064     128   schedule_timeout+0x34/0xe0
 7)     1936     112   wait_for_common+0x97/0xf1
 8)     1824      16   wait_for_completion+0x1d/0x1f
 9)     1808     128   flush_work+0xfe/0x119
10)     1680      16   tty_flush_to_ldisc+0x1e/0x20
11)     1664      48   input_available_p+0x1d/0x5c
12)     1616      48   n_tty_poll+0x6d/0x134
13)     1568      64   tty_poll+0x64/0x7f
14)     1504     880   do_select+0x31e/0x511
15)      624     400   core_sys_select+0x177/0x216
16)      224      96   sys_select+0x91/0xb9
17)      128     128   system_call_fastpath+0x16/0x1b
```

注意，如果 gcc 使用了 `-mfentry`，函数会在设置栈帧之前被追踪。这意味着当使用 `-mfentry` 时，叶子级别的函数不会被栈追踪器测试。
目前，仅在 x86 架构上 gcc 4.6.0 及以上版本使用 `-mfentry`。

更多详情可以在源代码中的 `kernel/trace/*.c` 文件中找到。
