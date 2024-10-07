SPDX 许可声明标识符: GPL-2.0

=================
启动时追踪
=================

:作者: Masami Hiramatsu <mhiramat@kernel.org>

概述
========

启动时追踪允许用户使用 ftrace 的全部功能（包括按事件过滤和操作、直方图、kprobe 事件和合成事件以及追踪实例）来追踪启动过程，包括设备初始化。由于内核命令行不足以控制这些复杂功能，因此使用 bootconfig 文件来描述追踪功能编程。

启动配置中的选项
==========================

以下是启动配置文件 [1]_ 中可用于启动时追踪的选项列表。所有选项均以 "ftrace." 或 "kernel." 前缀开头。有关以 "kernel." 前缀开始的选项，请参阅内核参数 [2]_。
.. [1] 参见 :ref:`Documentation/admin-guide/bootconfig.rst <bootconfig>`
.. [2] 参见 :ref:`Documentation/admin-guide/kernel-parameters.rst <kernelparameters>`

Ftrace 全局选项
---------------------

Ftrace 全局选项在启动配置中带有 "kernel." 前缀，这意味着这些选项作为内核传统命令行的一部分传递。

kernel.tp_printk
    在 printk 缓冲区上输出 trace-event 数据
kernel.dump_on_oops [= 模式]
    在 Oops 时转储 ftrace。如果 MODE = 1 或省略，则在所有 CPU 上转储跟踪缓冲区；如果 MODE = 2，则仅在一个触发 Oops 的 CPU 上转储缓冲区
kernel.traceoff_on_warning
    如果发生 WARN_ON() 则停止追踪
kernel.fgraph_max_depth = 最大深度
    设置 fgraph 追踪器的最大深度为 MAX_DEPTH
kernel.fgraph_filters = 过滤器[, 过滤器2...]
    添加 fgraph 追踪函数过滤器
kernel.fgraph_notraces = 过滤器[, 过滤器2...]
    添加 fgraph 非追踪函数过滤器
Ftrace 每实例选项
---------------------------

这些选项可以用于每个实例，包括全局的 ftrace 节点。

`ftrace.[instance.INSTANCE.]options = OPT1[, OPT2[...]]`
   启用给定的 ftrace 选项。

`ftrace.[instance.INSTANCE.]tracing_on = 0|1`
   在启动时启用或禁用此实例上的跟踪（你可以通过“traceon”事件触发器来启用它）。

`ftrace.[instance.INSTANCE.]trace_clock = CLOCK`
   将给定的 `CLOCK` 设置为 ftrace 的 trace_clock。

`ftrace.[instance.INSTANCE.]buffer_size = SIZE`
   配置 ftrace 缓冲区大小为 `SIZE`。你可以使用 “KB” 或 “MB” 表示该 `SIZE`。

`ftrace.[instance.INSTANCE.]alloc_snapshot`
   分配快照缓冲区。

`ftrace.[instance.INSTANCE.]cpumask = CPUMASK`
   将 `CPUMASK` 设置为跟踪的 CPU 掩码。

`ftrace.[instance.INSTANCE.]events = EVENT[, EVENT2[...]]`
   在启动时启用给定的事件。你可以在 `EVENT` 中使用通配符。

`ftrace.[instance.INSTANCE.]tracer = TRACER`
   在启动时将 `TRACER` 设置为当前跟踪器。（例如：function）

`ftrace.[instance.INSTANCE.]ftrace.filters`
   这将接收一个跟踪函数过滤规则数组。

`ftrace.[instance.INSTANCE.]ftrace.notraces`
   这将接收一个非跟踪函数过滤规则数组。
Ftrace 每事件选项
------------------------

这些选项用于设置每事件的选项：
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.enable
   启用 GROUP:EVENT 的追踪
ftrace.[instance.INSTANCE.]event.GROUP.enable
   启用 GROUP 内的所有事件追踪
ftrace.[instance.INSTANCE.]event.enable
   启用所有事件追踪
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.filter = FILTER
   为 GROUP:EVENT 设置 FILTER 规则
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.actions = ACTION[, ACTION2[...]]
   为 GROUP:EVENT 设置 ACTIONs
ftrace.[instance.INSTANCE.]event.kprobes.EVENT.probes = PROBE[, PROBE2[...]]
   根据 PROBEs 定义新的 kprobe 事件。可以在一个事件上定义多个探针，但这些探针必须具有相同类型的参数。此选项仅适用于组名为 "kprobes" 的事件
ftrace.[instance.INSTANCE.]event.synthetic.EVENT.fields = FIELD[, FIELD2[...]]
   使用 FIELDs 定义新的合成事件。每个字段应为 "类型 变量名"
请注意，kprobe 和合成事件定义可以写在 instance 节点下，但这些定义在其他实例中也是可见的。因此，请注意避免事件名称冲突。

Ftrace 直方图选项
------------------------

由于将直方图操作作为字符串写入每事件操作选项太长，所以在每事件的 'hist' 子键下提供了树状选项来处理直方图操作。有关每个参数的详细信息，请参阅事件直方图文档（Documentation/trace/histogram.rst）

ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]keys = KEY1[, KEY2[...]]
   设置直方图的关键参数。（必需）
   'N' 是一个数字字符串，用于表示多个直方图。如果事件只有一个直方图，则可以省略它。
```plaintext
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]values = VAL1[, VAL2[...]]
  设置直方图值参数
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]sort = SORT1[, SORT2[...]]
  设置直方图排序参数选项
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]size = NR_ENTRIES
  设置直方图大小（条目数量）
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]name = NAME
  设置直方图名称
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]var.VARIABLE = EXPR
  通过EXPR表达式定义一个新的VARIABLE
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]<pause|continue|clear>
  设置直方图控制参数。您可以设置其中的一个
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]onmatch.[M.]event = GROUP.EVENT
  设置直方图'onmatch'处理程序匹配事件参数
'M' 是一个数字字符串，用于多个'onmatch'处理程序。如果此直方图上只有一个'onmatch'处理程序，则可以省略它
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]onmatch.[M.]trace = EVENT[, ARG1[...]]
  设置'onmatch'时的直方图'trace'操作
EVENT 必须是一个合成事件名称，而ARG1...是该事件的参数。如果设置了'onmatch.event'选项，则这是必须的
```
```plaintext
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]onmax.[M.]var = VAR
  设置直方图 'onmax' 处理器变量参数
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]onchange.[M.]var = VAR
  设置直方图 'onchange' 处理器变量参数
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]<onmax|onchange>.[M.]save = ARG1[, ARG2[...]]
  设置直方图 'save' 动作参数用于 'onmax' 或 'onchange' 处理器
如果设置了 'onmax.var' 或 'onchange.var' 选项，则此选项或下面的 'snapshot' 选项是必需的
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.[N.]<onmax|onchange>.[M.]snapshot
  设置直方图 'snapshot' 动作用于 'onmax' 或 'onchange' 处理器
如果设置了 'onmax.var' 或 'onchange.var' 选项，则此选项或上面的 'save' 选项是必需的
ftrace.[instance.INSTANCE.]event.GROUP.EVENT.hist.filter = FILTER_EXPR
  设置直方图过滤表达式。在 FILTER_EXPR 中不需要使用 'if'
注意，此 'hist' 选项可能会与每个事件的 'actions' 选项冲突，如果 'actions' 选项包含直方图动作

启动时间
==========

所有以 `ftrace` 开头的启动时跟踪选项将在 core_initcall 结束时启用。这意味着您可以从 postcore_initcall 追踪事件。
大多数子系统和架构相关的驱动程序将在之后初始化（arch_initcall 或 subsys_initcall）。因此，您可以使用启动时追踪来追踪这些事件。
```
如果你希望追踪 `core_initcall` 之前的事件，可以使用以 `kernel` 开头的选项。其中一些选项会在 `initcall` 处理之前启用（例如，`kernel.ftrace=function` 和 `kernel.trace_event` 会在 `initcall` 之前启动）。

### 示例

例如，要为每个事件添加过滤器和操作、定义 kprobe 事件以及带有直方图的合成事件，可以编写如下引导配置：

```plaintext
ftrace.event {
        task.task_newtask {
                filter = "pid < 128"
                enable
        }
        kprobes.vfs_read {
                probes = "vfs_read $arg1 $arg2"
                filter = "common_pid < 200"
                enable
        }
        synthetic.initcall_latency {
                fields = "unsigned long func", "u64 lat"
                hist {
                        keys = func.sym, lat
                        values = lat
                        sort = lat
                }
        }
        initcall.initcall_start.hist {
                keys = func
                var.ts0 = common_timestamp.usecs
        }
        initcall.initcall_finish.hist {
                keys = func
                var.lat = common_timestamp.usecs - $ts0
                onmatch {
                        event = initcall.initcall_start
                        trace = initcall_latency, func, $lat
                }
        }
}
```

此外，引导时跟踪支持“实例”节点，这允许我们同时运行多个不同目的的跟踪器。例如，一个跟踪器用于跟踪以 “user_” 开头的函数，另一个跟踪器用于跟踪以 “kernel_” 开头的函数，可以编写如下引导配置：

```plaintext
ftrace.instance {
        foo {
                tracer = "function"
                ftrace.filters = "user_*"
        }
        bar {
                tracer = "function"
                ftrace.filters = "kernel_*"
        }
}
```

实例节点还接受事件节点，因此每个实例可以自定义其事件跟踪。通过触发动作和 kprobe，可以在调用某个函数时跟踪函数图。例如，这将跟踪 pci_proc_init() 中的所有函数调用：

```plaintext
ftrace {
        tracing_on = 0
        tracer = function_graph
        event.kprobes {
                start_event {
                        probes = "pci_proc_init"
                        actions = "traceon"
                }
                end_event {
                        probes = "pci_proc_init%return"
                        actions = "traceoff"
                }
        }
}
```

此引导时跟踪还支持通过引导配置设置的 ftrace 内核参数。例如，以下内核参数：

```plaintext
trace_options=sym-addr trace_event=initcall:* tp_printk trace_buf_size=1M ftrace=function ftrace_filter="vfs*"
```

可以写入引导配置如下：

```plaintext
kernel {
        trace_options = sym-addr
        trace_event = "initcall:*"
        tp_printk
        trace_buf_size = 1M
        ftrace = function
        ftrace_filter = "vfs*"
}
```

请注意，这些参数是以 “kernel” 前缀开始，而不是 “ftrace”。
