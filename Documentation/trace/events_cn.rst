事件追踪
==========

:作者: Theodore Ts'o
:更新者: Li Zefan 和 Tom Zanussi

1. 引言
========

追踪点（参见Documentation/trace/tracepoints.rst）可以在不创建自定义内核模块的情况下使用事件追踪基础设施来注册探测函数。并非所有追踪点都可以通过事件追踪系统进行追踪；内核开发人员必须提供代码片段，以定义如何将追踪信息保存到追踪缓冲区以及如何打印追踪信息。

2. 使用事件追踪
==================

2.1 通过'set_event'接口
-------------------------------

可用于追踪的事件可以在文件/sys/kernel/tracing/available_events中找到。
要启用某个特定事件（例如'sched_wakeup'），只需将其写入/sys/kernel/tracing/set_event。例如：

	# echo sched_wakeup >> /sys/kernel/tracing/set_event

.. 注意:: 使用'>>'是必要的，否则它会首先禁用所有事件。
要禁用一个事件，将事件名称写入set_event文件，并在前面加上感叹号：

	# echo '!sched_wakeup' >> /sys/kernel/tracing/set_event

要禁用所有事件，将空行写入set_event文件：

	# echo > /sys/kernel/tracing/set_event

要启用所有事件，将`*:*`或`*:`写入set_event文件：

	# echo *:* > /sys/kernel/tracing/set_event

事件按子系统组织，如ext4、irq、sched等，完整的事件名称形式为：<子系统>:<事件>。子系统名称是可选的，但在available_events文件中显示。可以通过`<子系统>:*`语法指定子系统中的所有事件；例如，要启用所有irq事件，可以使用命令：

	# echo 'irq:*' > /sys/kernel/tracing/set_event

2.2 通过'enable'切换
------------------------------

可用的事件也列在/sys/kernel/tracing/events/目录层次结构中。
要启用事件'sched_wakeup'：

	# echo 1 > /sys/kernel/tracing/events/sched/sched_wakeup/enable

要禁用它：

	# echo 0 > /sys/kernel/tracing/events/sched/sched_wakeup/enable

要启用sched子系统中的所有事件：

	# echo 1 > /sys/kernel/tracing/events/sched/enable

要启用所有事件：

	# echo 1 > /sys/kernel/tracing/events/enable

读取这些enable文件时，有四种结果：

- 0 - 所有受此文件影响的事件都已禁用
- 1 - 所有受此文件影响的事件都已启用
- X - 启用和禁用的事件混合
- ? - 此文件不受任何事件影响

2.3 引导选项
----------------

为了便于早期引导调试，使用引导选项：

	trace_event=[事件列表]

事件列表是一个由逗号分隔的事件列表。有关事件格式，请参阅第2.1节。

3. 定义一个事件启用的追踪点
=================================

参见samples/trace_events提供的示例。

4. 事件格式
==============

每个追踪事件都有一个与之关联的'format'文件，其中包含对日志事件中每个字段的描述。这些信息可用于解析二进制追踪流，也是查找可用于事件过滤器（参见第5节）的字段名称的地方。它还显示了用于文本模式下打印事件的格式字符串，以及用于性能分析的事件名称和ID。
每个事件都有一组“common”字段与其关联；这些是带有“common_”前缀的字段。其他字段因事件而异，对应于该事件的TRACE_EVENT定义中定义的字段。
格式中的每个字段具有以下形式：

     字段:字段类型 字段名; 偏移量:N; 大小:N;

其中偏移量是字段在追踪记录中的偏移量，大小是以字节为单位的数据项大小。
例如，以下是`sched_wakeup`事件显示的信息：

	# cat /sys/kernel/tracing/events/sched/sched_wakeup/format

名称: sched_wakeup  
ID: 60  
格式:  
	field: unsigned short common_type; offset:0; size:2;  
	field: unsigned char common_flags; offset:2; size:1;  
	field: unsigned char common_preempt_count; offset:3; size:1;  
	field: int common_pid; offset:4; size:4;  
	field: int common_tgid; offset:8; size:4;  

	field: char comm[TASK_COMM_LEN]; offset:12; size:16;  
	field: pid_t pid; offset:28; size:4;  
	field: int prio; offset:32; size:4;  
	field: int success; offset:36; size:4;  
	field: int cpu; offset:40; size:4;  

打印格式: "task %s:%d [%d] success=%d [%03d]", REC->comm, REC->pid, REC->prio, REC->success, REC->cpu

此事件包含10个字段，前5个是通用字段，后5个是特定于事件的字段。除了`comm`是一个字符串外，其余所有字段都是数值型，这对于事件过滤非常重要。

### 5. 事件过滤
#### 5.1 表达式语法

可以使用布尔“过滤表达式”在内核中过滤跟踪事件。一旦事件被记录到跟踪缓冲区，其字段就会与该事件类型的过滤表达式进行比较。如果事件的字段值与过滤器匹配，则会在跟踪输出中显示；如果不匹配，则会被丢弃。如果没有关联过滤器的事件会匹配所有内容，这是默认设置（当没有为事件设置过滤器时）。

一个过滤表达式由一个或多个可以使用逻辑运算符`&&`和`||`组合的“谓词”组成。谓词是将记录事件中的字段值与常数值进行比较的简单子句，并根据是否匹配返回0或1：

	  字段名 关系运算符 值

可以使用括号提供任意逻辑分组，并使用双引号防止shell解释运算符为shell元字符。
用于过滤的字段名可以在跟踪事件的“格式”文件中找到（见第4节）。
关系运算符取决于测试字段的类型：

对于数值字段可用的操作符有：
==, !=, <, <=, >, >=, &

对于字符串字段可用的操作符有：
==, !=, ~

通配符(~)接受通配符(\*, ?)和字符类([)。例如：
  
  prev_comm ~ "*sh"  
  prev_comm ~ "sh*"  
  prev_comm ~ "*sh*"  
  prev_comm ~ "ba*sh"

如果字段是指向用户空间的指针（例如sys_enter_openat中的"filename"），则需要在字段名后加上".ustring"：

  filename.ustring ~ "password"

因为内核需要知道如何从用户空间检索指针指向的内存。
可以将任何长整型转换为函数地址并通过函数名称进行搜索：

  call_site.function == security_prepare_creds

上述操作将在字段"call_site"落在"security_prepare_creds"函数地址范围内时进行过滤。即，它会比较"call_site"的值，并且如果该值大于等于"security_prepare_creds"函数的起始地址并且小于结束地址时，过滤器返回真。
".function"后缀只能附加到长整型大小的值，并且只能用"=="或"!="进行比较。
CPU掩码字段或编码CPU编号的标量字段可以通过用户提供的CPU列表格式的CPU掩码进行过滤。格式如下：

  CPUS{$cpulist}

可用于CPU掩码过滤的操作符有：

& (交集), ==, !=

例如，这将过滤具有.target_cpu字段位于给定CPU掩码中的事件：

  target_cpu & CPUS{17-42}

#### 5.2 设置过滤器

通过将过滤表达式写入给定事件的“filter”文件来设置单个事件的过滤器。
例如：

	# cd /sys/kernel/tracing/events/sched/sched_wakeup
	# echo "common_preempt_count > 4" > filter

稍微复杂一点的例子：

	# cd /sys/kernel/tracing/events/signal/signal_generate
	# echo "((sig >= 10 && sig < 15) || sig == 17) && comm != bash" > filter

如果表达式中有错误，在设置时会收到“无效参数”错误，并且错误字符串以及错误消息可以通过查看过滤器获得，例如：

	# cd /sys/kernel/tracing/events/signal/signal_generate
	# echo "((sig >= 10 && sig < 15) || dsig == 17) && comm != bash" > filter
	-bash: echo: 写入错误：无效参数
	# cat filter
	((sig >= 10 && sig < 15) || dsig == 17) && comm != bash
	^
	parse_error: 未找到字段

目前，错误时的指针符号(`^`)始终出现在过滤字符串的开头；即使没有更准确的位置信息，错误消息仍然有用。

#### 5.2.1 过滤器限制

如果对指向非环形缓冲区字符串的字符串指针(`(char *)`)设置了过滤器，而是指向内核或用户空间的内存，那么出于安全原因，最多只会复制1024字节的内容到临时缓冲区进行比较。如果内存复制出错（指针指向不应访问的内存），则字符串比较将被视为不匹配。
### 5.3 清除过滤器
--------------------

要清除某个事件的过滤器，将一个 `0` 写入该事件的过滤器文件。
要清除子系统中所有事件的过滤器，将一个 `0` 写入该子系统的过滤器文件。

### 5.4 子系统过滤器
---------------------

为了方便起见，可以通过在子系统的根目录下的过滤器文件中写入过滤表达式来批量设置或清除子系统中每个事件的过滤器。需要注意的是，如果子系统中的任何事件缺少子系统过滤器中指定的字段，或者由于其他原因无法应用过滤器，则该事件将保留其之前的设置。这可能会导致过滤器混合的结果（用户可能认为不同的过滤器正在生效），从而导致混乱的跟踪输出。只有那些引用了公共字段的过滤器才能保证成功传播到所有事件。以下是一些子系统过滤器的例子，同时也说明了上述要点：

清除 sched 子系统中所有事件的过滤器：
```
# cd /sys/kernel/tracing/events/sched
# echo 0 > filter
# cat sched_switch/filter
none
# cat sched_wakeup/filter
none
```

使用公共字段为 sched 子系统中的所有事件设置过滤器（所有事件最终具有相同的过滤器）：
```
# cd /sys/kernel/tracing/events/sched
# echo common_pid == 0 > filter
# cat sched_switch/filter
common_pid == 0
# cat sched_wakeup/filter
common_pid == 0
```

尝试使用非公共字段为 sched 子系统中的所有事件设置过滤器（除了具有 prev_pid 字段的事件外，所有事件都保留旧的过滤器）：
```
# cd /sys/kernel/tracing/events/sched
# echo prev_pid == 0 > filter
# cat sched_switch/filter
prev_pid == 0
# cat sched_wakeup/filter
common_pid == 0
```

### 5.5 PID 过滤
-----------------

与顶级事件目录相同目录中的 set_event_pid 文件存在时，会过滤掉未列出在 set_event_pid 文件中的 PID 的所有任务的事件：
```
# cd /sys/kernel/tracing
# echo $$ > set_event_pid
# echo 1 > events/enable
```
这只会跟踪当前任务的事件。
要添加更多 PID 而不丢失已包含的 PID，请使用 `>>`：
```
# echo 123 244 1 >> set_event_pid
```

### 6. 事件触发器
=================

跟踪事件可以有条件地调用“命令”形式的触发器，这些命令有多种形式，并在下面详细描述；例如，在触发跟踪事件时启用或禁用其他跟踪事件或调用堆栈跟踪。每当带有附加触发器的跟踪事件被调用时，与该事件关联的一组触发命令就会被调用。任何给定的触发器还可以有一个与第 5 节（事件过滤）中描述的形式相同的事件过滤器相关联——只有当被调用的事件通过关联的过滤器时，命令才会被调用。如果没有关联过滤器，则始终通过。
通过向特定事件的“trigger”文件写入触发表达式来添加和移除触发器。
一个给定的事件可以有任意数量的触发器与其关联，但受个别命令在此方面的任何限制的影响。
事件触发器是在“软”模式的基础上实现的，这意味着每当一个跟踪事件有一个或多个触发器与之关联时，即使该事件实际上没有启用，而是处于“软”模式下，该事件也会被激活。也就是说，跟踪点会被调用，但不会被跟踪，除非它确实被启用了。这种方案允许即使未启用的事件也能触发，同时也允许使用当前的事件过滤实现来有条件地触发。

事件触发器的语法大致基于`set_ftrace_filter`的“ftrace过滤命令”（详见Documentation/trace/ftrace.rst中的“过滤命令”部分），但两者之间存在重大差异，并且当前实现并不依赖于它，因此在二者之间进行泛化时需谨慎。

注意：
写入`trace_marker`（详见Documentation/trace/ftrace.rst）也可以启用写入`/sys/kernel/tracing/events/ftrace/print/trigger`的触发器。

6.1 表达式语法
---------------------

通过向`trigger`文件回显命令来添加触发器：

```shell
# echo 'command[:count] [if filter]' > trigger
```

通过向`trigger`文件回显相同的命令，但在开头加上'!'来移除触发器：

```shell
# echo '!command[:count] [if filter]' > trigger
```

移除时`[if filter]`部分不会用于匹配命令，因此在'!'命令中省略这部分与包含它效果相同。

为了方便使用，目前向`trigger`文件写入时使用'>'仅添加或移除单个触发器，没有显式的'>>'支持（'>'实际行为像'>>'）或截断支持以移除所有触发器（需要对每个添加的触发器使用'!'）。

6.2 支持的触发器命令
------------------------------

以下命令是支持的：

- enable_event/disable_event

  这些命令可以在触发事件发生时启用或禁用另一个跟踪事件。当这些命令注册时，其他跟踪事件会被激活，但处于“软”模式。也就是说，跟踪点会被调用，但不会被跟踪。
  该事件跟踪点保持在这种模式，直到有有效的触发器可以触发它。

  例如，以下触发器在进入读取系统调用时使kmalloc事件被跟踪，末尾的`:1`指定此启用仅发生一次：

  ```shell
  # echo 'enable_event:kmem:kmalloc:1' > /sys/kernel/tracing/events/syscalls/sys_enter_read/trigger
  ```

  以下触发器在退出读取系统调用时停止跟踪kmalloc事件。每次读取系统调用退出都会发生禁用：

  ```shell
  # echo 'disable_event:kmem:kmalloc' > /sys/kernel/tracing/events/syscalls/sys_exit_read/trigger
  ```

  格式为：

  ```
  enable_event:<system>:<event>[:count]
  disable_event:<system>:<event>[:count]
  ```

  移除上述命令：

  ```shell
  # echo '!enable_event:kmem:kmalloc:1' > /sys/kernel/tracing/events/syscalls/sys_enter_read/trigger
  # echo '!disable_event:kmem:kmalloc' > /sys/kernel/tracing/events/syscalls/sys_exit_read/trigger
  ```

  注意，每个触发事件可以有任意数量的启用/禁用事件触发器，但每个被触发事件只能有一个触发器。例如，`sys_enter_read`可以有触发`kmem:kmalloc`和`sched:sched_switch`的触发器，但不能有两个版本的`kmem:kmalloc`，如`kmem:kmalloc`和`kmem:kmalloc:1`或`kmem:kmalloc if bytes_req == 256`和`kmem:kmalloc if bytes_alloc == 256`（它们可以合并到一个`kmem:kmalloc`的过滤条件上）。

- stacktrace

  此命令在触发事件发生时将堆栈跟踪转储到跟踪缓冲区。
例如，以下触发器每次命中 `kmalloc` 踪点时都会输出堆栈跟踪：

```shell
# echo 'stacktrace' > /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

以下触发器在前五次 `kmalloc` 请求发生且大小 >= 64K 时输出堆栈跟踪：

```shell
# echo 'stacktrace:5 if bytes_req >= 65536' > /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

格式如下：

```shell
stacktrace[:count]
```

要移除上述命令：

```shell
# echo '!stacktrace' > /sys/kernel/tracing/events/kmem/kmalloc/trigger

# echo '!stacktrace:5 if bytes_req >= 65536' > /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

后者也可以通过以下命令更简单地移除（不带过滤器）：

```shell
# echo '!stacktrace:5' > /sys/kernel/tracing/events/kmem/kmalloc/trigger
```

请注意，每个触发事件只能有一个堆栈跟踪触发器。

- 快照（snapshot）

此命令会在触发事件发生时触发快照。
以下命令在每次块请求队列被拔出且深度 > 1 时创建一个快照。如果当时正在追踪一组事件或函数，则快照追踪缓冲区将在触发事件发生时捕获这些事件：

```shell
# echo 'snapshot if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

仅一次快照：

```shell
# echo 'snapshot:1 if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

要移除上述命令：

```shell
# echo '!snapshot if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger

# echo '!snapshot:1 if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

请注意，每个触发事件只能有一个快照触发器。

- 开启/关闭追踪（traceon/traceoff）

这些命令在指定事件发生时开启和关闭追踪。参数确定追踪系统开启和关闭的次数。如果不指定，则没有限制。
以下命令在第一次块请求队列被拔出且深度 > 1 时关闭追踪。如果当时正在追踪一组事件或函数，则可以检查追踪缓冲区以查看导致触发事件的一系列事件：

```shell
# echo 'traceoff:1 if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

当 `nr_rq > 1` 时始终禁用追踪：

```shell
# echo 'traceoff if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

要移除上述命令：

```shell
# echo '!traceoff:1 if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger

# echo '!traceoff if nr_rq > 1' > /sys/kernel/tracing/events/block/block_unplug/trigger
```

请注意，每个触发事件只能有一个 `traceon` 或 `traceoff` 触发器。

- 历史统计（hist）

此命令将事件命中数汇总到一个哈希表中，该哈希表根据一个或多个追踪事件格式字段（或堆栈跟踪）以及从一个或多个追踪事件格式字段和/或事件计数（命中次数）派生的一组运行总计进行键入。
有关详细信息和示例，请参阅 `Documentation/trace/histogram.rst`。

7. 内核追踪事件 API

在大多数情况下，追踪事件的命令行接口已经足够使用。然而，有时应用程序可能需要比简单的命令行表达式所能表达的更复杂的关系，或者组合一系列命令可能过于繁琐。例如，一个应用程序可能需要“监听”追踪流，以便维护内核中的状态机，检测非法内核状态，比如调度程序中的非法状态。
追踪事件子系统提供了一个内核 API，允许模块或其他内核代码生成用户定义的“合成”事件，这些事件可以用来增强现有的追踪流，或者信号表明某个重要状态的发生。
类似的内核 API 也适用于创建 kprobe 和 kretprobe 事件。
合成事件和k/ret/probe事件API都是基于一个较低级别的“dynevent_cmd”事件命令API构建的，该API也适用于更专业的应用，或者作为其他更高层次的跟踪事件API的基础。
为此提供的API如下所述，并允许以下操作：

- 动态创建合成事件定义
- 动态创建kprobe和kretprobe事件定义
- 从内核代码中追踪合成事件
- 低级别的“dynevent_cmd”API

7.1 动态创建合成事件定义
--------------------------------

有几种方法可以从内核模块或其他内核代码中创建新的合成事件。
第一种方法是一步创建事件，使用`synth_event_create()`函数。在这种方法中，需要向`synth_event_create()`提供要创建的事件名称和一个定义字段的数组。如果成功，调用后将存在一个具有该名称和字段的合成事件。例如，要创建一个新的名为“schedtest”的合成事件：

```c
ret = synth_event_create("schedtest", sched_fields,
                         ARRAY_SIZE(sched_fields), THIS_MODULE);
```

在这个示例中，参数`sched_fields`指向一个`struct synth_field_desc`类型的数组，每个元素描述了一个事件字段的类型和名称：

```c
static struct synth_field_desc sched_fields[] = {
    { .type = "pid_t",              .name = "next_pid_field" },
    { .type = "char[16]",           .name = "next_comm_field" },
    { .type = "u64",                .name = "ts_ns" },
    { .type = "u64",                .name = "ts_ms" },
    { .type = "unsigned int",       .name = "cpu" },
    { .type = "char[64]",           .name = "my_string_field" },
    { .type = "int",                .name = "my_int_field" },
};
```

请参阅`synth_field_size()`以了解可用的类型。
如果字段名称包含[n]，则认为该字段是一个静态数组。
如果字段名称包含[]（没有下标），则认为该字段是一个动态数组，它在事件中仅占用所需的存储空间。
由于在为事件分配字段值之前已经预留了事件的空间，因此使用动态数组意味着下面描述的分段内核API不能与动态数组一起使用。但是，其他非分段内核API可以与动态数组一起使用。
如果事件是在模块内部创建的，则必须将模块指针传递给`synth_event_create()`。这将确保当模块被移除时，跟踪缓冲区中不会包含无法读取的事件。
此时，事件对象已准备好用于生成新事件。
第二种方法是分几步创建事件。这种方法允许动态创建事件，并且不需要事先创建和填充字段数组。
要使用这种方法，首先应使用 `synth_event_gen_cmd_start()` 或 `synth_event_gen_cmd_array_start()` 创建一个空的或部分为空的合成事件。对于 `synth_event_gen_cmd_start()`，需要提供事件名称以及一个或多个参数对，每对参数代表一个 `'类型字段名;'` 字段规范。对于 `synth_event_gen_cmd_array_start()`，需要提供事件名称和一个 `struct synth_field_desc` 数组。在调用 `synth_event_gen_cmd_start()` 或 `synth_event_gen_cmd_array_start()` 之前，用户应该使用 `synth_event_cmd_init()` 创建并初始化一个 `dynevent_cmd` 对象。例如，创建一个新的名为 "schedtest" 的合成事件，包含两个字段：

```c
struct dynevent_cmd cmd;
char *buf;

/* 创建一个缓冲区来保存生成的命令 */
buf = kzalloc(MAX_DYNEVENT_CMD_LEN, GFP_KERNEL);

/* 在生成命令之前，初始化 cmd 对象 */
synth_event_cmd_init(&cmd, buf, MAX_DYNEVENT_CMD_LEN);

ret = synth_event_gen_cmd_start(&cmd, "schedtest", THIS_MODULE,
                                "pid_t", "next_pid_field",
                                "u64", "ts_ns");
```

或者，使用包含相同信息的 `struct synth_field_desc` 数组：

```c
ret = synth_event_gen_cmd_array_start(&cmd, "schedtest", THIS_MODULE,
                                      fields, n_fields);
```

一旦创建了合成事件对象，就可以通过逐个添加字段来填充更多字段。使用 `synth_event_add_field()` 添加字段时，需要提供 `dynevent_cmd` 对象、字段类型和字段名称。例如，要添加一个名为 "intfield" 的新整型字段，可以执行以下调用：

```c
ret = synth_event_add_field(&cmd, "int", "intfield");
```

参见 `synth_field_size()` 获取可用类型。如果 `field_name` 包含 `[n]`，则认为该字段是一个数组。
一组字段也可以一次性通过 `add_synth_fields()` 和 `synth_field_desc` 数组添加。例如，这将只添加前四个 `sched_fields`：

```c
ret = synth_event_add_fields(&cmd, sched_fields, 4);
```

如果已经有一个形式为 `'类型字段名'` 的字符串，可以使用 `synth_event_add_field_str()` 直接添加；它也会自动在字符串末尾添加 `;`。

一旦所有字段都已添加，可以通过调用 `synth_event_gen_cmd_end()` 函数最终确定并注册事件：

```c
ret = synth_event_gen_cmd_end(&cmd);
```

此时，事件对象已准备好用于跟踪新的事件。

### 7.2 从内核代码中跟踪合成事件

#### 7.2.1 一次性跟踪合成事件

要一次性跟踪合成事件，可以使用 `synth_event_trace()` 或 `synth_event_trace_array()` 函数。

`synth_event_trace()` 函数接收表示合成事件的 `trace_event_file`（可以通过使用 `trace_get_event_file()` 并传入合成事件名称、系统名称 "synthetic" 和跟踪实例名称（如果使用全局跟踪数组，则为 NULL）来获取），以及可变数量的 `u64` 参数，每个合成事件字段对应一个参数，并且传递值的数量。

例如，要跟踪与上述合成事件定义对应的事件，可以使用如下代码：

```c
ret = synth_event_trace(create_synth_test, 7, /* number of values */
                        444,             /* next_pid_field */
                        (u64)"clackers", /* next_comm_field */
                        1000000,         /* ts_ns */
                        1000,            /* ts_ms */
                        smp_processor_id(),/* cpu */
                        (u64)"Thneed",   /* my_string_field */
                        999);            /* my_int_field */
```

所有值都应转换为 `u64` 类型，字符串值只是指向字符串的指针，也转换为 `u64`。这些指针会将字符串复制到事件中预留的空间。

或者，可以使用 `synth_event_trace_array()` 函数实现相同功能。它接收表示合成事件的 `trace_event_file`（可以通过使用 `trace_get_event_file()` 并传入合成事件名称、系统名称 "synthetic" 和跟踪实例名称（如果使用全局跟踪数组，则为 NULL）来获取），以及一个 `u64` 数组，每个合成事件字段对应一个元素。

例如，要跟踪与上述合成事件定义对应的事件，可以使用如下代码：

```c
u64 vals[7];

vals[0] = 777;                  /* next_pid_field */
vals[1] = (u64)"tiddlywinks";   /* next_comm_field */
vals[2] = 1000000;              /* ts_ns */
vals[3] = 1000;                 /* ts_ms */
vals[4] = smp_processor_id();   /* cpu */
vals[5] = (u64)"thneed";        /* my_string_field */
vals[6] = 398;                  /* my_int_field */
```

`vals` 数组只是一个 `u64` 类型的数组，其数量必须与合成事件中的字段数量匹配，并且顺序也必须与合成事件字段相同。
所有值都应转换为 `u64` 类型，字符串值只是指向字符串的指针，也转换为 `u64`。字符串将使用这些指针复制到事件中预留的空间里。

为了跟踪一个合成事件，需要一个指向跟踪事件文件的指针。可以使用 `trace_get_event_file()` 函数来获取它——它会在给定的跟踪实例中找到该文件（在这种情况下为 `NULL`，因为使用的是顶级跟踪数组），同时防止包含它的实例消失：

```c
schedtest_event_file = trace_get_event_file(NULL, "synthetic", "schedtest");
```

在跟踪事件之前，应以某种方式启用它，否则合成事件实际上不会出现在跟踪缓冲区中。

要从内核启用一个合成事件，可以使用 `trace_array_set_clr_event()` 函数（这不仅限于合成事件，因此确实需要显式指定 `"synthetic"` 系统名称）。

要启用事件，传递 `true`：

```c
trace_array_set_clr_event(schedtest_event_file->tr, "synthetic", "schedtest", true);
```

要禁用它，传递 `false`：

```c
trace_array_set_clr_event(schedtest_event_file->tr, "synthetic", "schedtest", false);
```

最后，可以使用 `synth_event_trace_array()` 实际跟踪事件，之后应该可以在跟踪缓冲区中看到它：

```c
ret = synth_event_trace_array(schedtest_event_file, vals, ARRAY_SIZE(vals));
```

要移除合成事件，应先禁用事件，并使用 `trace_put_event_file()` 将跟踪实例“放回”：

```c
trace_array_set_clr_event(schedtest_event_file->tr, "synthetic", "schedtest", false);
trace_put_event_file(schedtest_event_file);
```

如果这些操作成功，可以调用 `synth_event_delete()` 来移除事件：

```c
ret = synth_event_delete("schedtest");
```

### 7.2.2 分段跟踪合成事件

为了分段跟踪合成事件，可以使用 `synth_event_trace_start()` 函数来“打开”合成事件的跟踪：

```c
struct synth_event_trace_state trace_state;

ret = synth_event_trace_start(schedtest_event_file, &trace_state);
```

它接受代表合成事件的 `trace_event_file` 对象，使用上面描述的相同方法，以及一个指向 `struct synth_event_trace_state` 对象的指针，在使用前会将其清零，并在后续调用之间保持状态。

一旦事件被打开，意味着已在跟踪缓冲区中为其预留了空间，就可以设置各个字段。有两种方法可以这样做：一种是按顺序逐个设置每个字段，不需要查找；另一种是按名称设置，需要查找。权衡在于赋值时的灵活性与每字段查找的成本。

要按顺序逐个设置值而不进行查找，应使用 `synth_event_add_next_val()`。每次调用都传递相同的 `synth_event_trace_state` 对象，这是在 `synth_event_trace_start()` 中使用的，以及要设置的下一个字段的值。设置完每个字段后，“游标”指向下一个字段，随后的调用将继续设置，直到按顺序设置完所有字段。使用这种方法的示例序列（不包括错误处理代码）如下：

```c
/* next_pid_field */
ret = synth_event_add_next_val(777, &trace_state);

/* next_comm_field */
ret = synth_event_add_next_val((u64)"slinky", &trace_state);

/* ts_ns */
ret = synth_event_add_next_val(1000000, &trace_state);

/* ts_ms */
ret = synth_event_add_next_val(1000, &trace_state);

/* cpu */
ret = synth_event_add_next_val(smp_processor_id(), &trace_state);

/* my_string_field */
ret = synth_event_add_next_val((u64)"thneed_2.01", &trace_state);

/* my_int_field */
ret = synth_event_add_next_val(395, &trace_state);
```

要按任意顺序设置值，应使用 `synth_event_add_val()`。每次调用都传递相同的 `synth_event_trace_state` 对象，这是在 `synth_event_trace_start()` 中使用的，以及要设置的字段名称及其值。使用这种方法的示例序列（不包括错误处理代码）如下：

```c
ret = synth_event_add_val("next_pid_field", 777, &trace_state);
ret = synth_event_add_val("next_comm_field", (u64)"silly putty", &trace_state);
ret = synth_event_add_val("ts_ns", 1000000, &trace_state);
ret = synth_event_add_val("ts_ms", 1000, &trace_state);
ret = synth_event_add_val("cpu", smp_processor_id(), &trace_state);
ret = synth_event_add_val("my_string_field", (u64)"thneed_9", &trace_state);
ret = synth_event_add_val("my_int_field", 3999, &trace_state);
```

请注意，`synth_event_add_next_val()` 和 `synth_event_add_val()` 在同一事件跟踪中是不兼容的——可以使用其中一个但不能同时使用两者。

最后，事件不会在实际跟踪之前被“关闭”，这通过 `synth_event_trace_end()` 完成，该函数只接受前面调用中使用的 `struct synth_event_trace_state` 对象：

```c
ret = synth_event_trace_end(&trace_state);
```

请注意，无论任何添加调用是否失败（例如由于传递了无效的字段名称），都必须在最后调用 `synth_event_trace_end()`。

### 7.3 动态创建 kprobe 和 kretprobe 事件定义

为了从内核代码创建 kprobe 或 kretprobe 跟踪事件，可以使用 `kprobe_event_gen_cmd_start()` 或 `kretprobe_event_gen_cmd_start()` 函数。

要创建一个 kprobe 事件，首先应使用 `kprobe_event_gen_cmd_start()` 创建一个空的或部分空的 kprobe 事件。应指定事件名称、探针位置以及代表探针字段的一个或多个参数。在调用 `kprobe_event_gen_cmd_start()` 之前，用户应使用 `kprobe_event_cmd_init()` 创建并初始化一个 `dynevent_cmd` 对象。

例如，创建一个新的具有两个字段的 "schedtest" kprobe 事件：

```c
struct dynevent_cmd cmd;
char *buf;

/* 创建一个用于保存生成命令的缓冲区 */
buf = kzalloc(MAX_DYNEVENT_CMD_LEN, GFP_KERNEL);

/* 在生成命令之前初始化 cmd 对象 */
kprobe_event_cmd_init(&cmd, buf, MAX_DYNEVENT_CMD_LEN);

/*
 * 定义带有前两个 kprobe 字段的 gen_kprobe_test 事件
 */ 
```
```c
ret = kprobe_event_gen_cmd_start(&cmd, "gen_kprobe_test", "do_sys_open",
                                 "dfd=%ax", "filename=%dx");
```

一旦创建了 kprobe 事件对象，就可以为其添加更多字段。可以使用 `kprobe_event_add_fields()` 函数为 `dynevent_cmd` 对象添加变量参数列表中的探测字段。例如，要添加一些额外的字段，可以进行如下调用：

```c
ret = kprobe_event_add_fields(&cmd, "flags=%cx", "mode=+4($stack)");
```

添加所有字段后，应通过调用 `kprobe_event_gen_cmd_end()` 或 `kretprobe_event_gen_cmd_end()` 函数来完成并注册该事件（取决于启动的是 kprobe 还是 kretprobe 命令）：

```c
ret = kprobe_event_gen_cmd_end(&cmd);
```

或者：

```c
ret = kretprobe_event_gen_cmd_end(&cmd);
```

此时，事件对象已准备好用于跟踪新事件。
同样地，也可以使用 `kretprobe_event_gen_cmd_start()` 与探测名称和位置以及诸如 `$retval` 等附加参数来创建一个 kretprobe 事件：

```c
ret = kretprobe_event_gen_cmd_start(&cmd, "gen_kretprobe_test",
                                    "do_sys_open", "$retval");
```

类似于合成事件的情况，可以使用以下代码启用新创建的 kprobe 事件：

```c
gen_kprobe_test = trace_get_event_file(NULL, "kprobes", "gen_kprobe_test");

ret = trace_array_set_clr_event(gen_kprobe_test->tr,
                                "kprobes", "gen_kprobe_test", true);
```

最后，类似于合成事件，可以使用以下代码返回 kprobe 事件文件并删除事件：

```c
trace_put_event_file(gen_kprobe_test);

ret = kprobe_event_delete("gen_kprobe_test");
```

### 7.4 “dynevent_cmd” 低级 API

内核合成事件和 kprobe 接口都是基于更低级别的“dynevent_cmd”接口构建的。此接口旨在提供高级接口（如合成事件和 kprobe 接口）的基础，并且可以作为示例使用。
基本思想很简单，即提供一个通用层，可用于生成跟踪事件命令。生成的命令字符串随后可以传递给已存在于跟踪事件子系统中的命令解析和事件创建代码，以创建相应的跟踪事件。
简而言之，其工作方式是：高级接口代码创建一个 `struct dynevent_cmd` 对象，然后使用 `dynevent_arg_add()` 和 `dynevent_arg_pair_add()` 函数构建命令字符串，最后使用 `dynevent_create()` 函数执行命令。下面详细描述了接口的具体内容。

构建新命令字符串的第一步是创建并初始化一个 `dynevent_cmd` 实例。例如，我们可以在栈上创建一个 `dynevent_cmd` 并初始化它：

```c
struct dynevent_cmd cmd;
char *buf;
int ret;

buf = kzalloc(MAX_DYNEVENT_CMD_LEN, GFP_KERNEL);

dynevent_cmd_init(cmd, buf, maxlen, DYNEVENT_TYPE_FOO,
                  foo_event_run_command);
```

`dynevent_cmd` 初始化需要提供用户指定的缓冲区及其长度（可以使用 `MAX_DYNEVENT_CMD_LEN` —— 它通常太大而不适合放在栈上，因此动态分配），一个 dynevent 类型 ID（用于检查进一步的 API 调用是否适用于正确的命令类型），以及指向特定事件 `run_command()` 回调函数的指针，该回调将被调用来实际执行特定于事件的命令函数。

完成这些操作后，可以通过连续调用参数添加函数来构建命令字符串。
为了添加单个参数，定义并初始化一个 `struct dynevent_arg` 或 `struct dynevent_arg_pair` 对象。以下是最简单的参数添加示例，即简单地将给定字符串追加为命令的一个空格分隔的参数：

```c
struct dynevent_arg arg;

dynevent_arg_init(&arg, NULL, 0);

arg.str = name;

ret = dynevent_arg_add(cmd, &arg);
```

`arg` 对象首先使用 `dynevent_arg_init()` 初始化，在这种情况下参数为 `NULL` 或 `0`，这意味着没有可选的合理性检查函数或在参数末尾追加的分隔符。

以下是一个更复杂的使用“参数对”的示例，用于创建由几个组件组合而成的参数单元，例如 `type field_name;` 参数或简单的表达式参数（如 `flags=%cx`）：

```c
struct dynevent_arg_pair arg_pair;

dynevent_arg_pair_init(&arg_pair, dynevent_foo_check_arg_fn, 0, ';');

arg_pair.lhs = type;
arg_pair.rhs = name;

ret = dynevent_arg_pair_add(cmd, &arg_pair);
```

再次，`arg_pair` 首先初始化，这里使用了一个回调函数来检查参数的合理性（例如，确保两者都不是 `NULL`），以及用于在参数对之间添加运算符（这里没有）和在参数对末尾追加的分隔符（这里是 `;`）。

还有 `dynevent_str_add()` 函数可用于直接添加字符串，无需空格、分隔符或参数检查。
可以进行任意数量的 `dynevent_*_add()` 调用来构建字符串（直到其长度超过 `cmd->maxlen`）。当所有参数都已添加并且命令字符串完整时，剩下的唯一事情就是运行命令，这只需调用 `dynevent_create()` 即可：

```c
ret = dynevent_create(&cmd);
```

此时，如果返回值为 0，则动态事件已创建并准备使用。
请参见 dynevent_cmd 函数定义本身的详细信息以了解 API。 

这里的“dynevent_cmd”是指具体的函数定义，如果你想了解这个API的详细信息，你需要查看这些函数是如何定义的。
