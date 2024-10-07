基于 Kprobe 的事件追踪
==========================

:作者: Masami Hiramatsu

概述
--------
这些事件类似于基于 tracepoint 的事件。不过，这些事件是基于 kprobes（包括 kprobe 和 kretprobe）的。因此，它可以探测所有 kprobes 能够探测的位置（这意味着除了带有 __kprobes/nokprobe_inline 注解和标记为 NOKPROBE_SYMBOL 的函数之外的所有函数）。与基于 tracepoint 的事件不同，这种事件可以动态地添加和移除。
要启用此功能，请在编译内核时设置 CONFIG_KPROBE_EVENTS=y。
与事件追踪器类似，这不需要通过 current_tracer 激活。相反，可以通过 /sys/kernel/tracing/kprobe_events 添加探测点，并通过 /sys/kernel/tracing/events/kprobes/<EVENT>/enable 启用它。
您也可以使用 /sys/kernel/tracing/dynamic_events 代替 kprobe_events。该接口将提供对其他动态事件的一致访问。

kprobe_events 简介
-------------------------
::

  p[:[GRP/][EVENT]] [MOD:]SYM[+offs]|MEMADDR [FETCHARGS] : 设置一个探测点
  r[MAXACTIVE][:[GRP/][EVENT]] [MOD:]SYM[+0] [FETCHARGS] : 设置一个返回探测点
  p[:[GRP/][EVENT]] [MOD:]SYM[+0]%return [FETCHARGS] : 设置一个返回探测点
  -:[GRP/][EVENT] : 清除一个探测点

 GRP     : 组名。如果省略，则使用 "kprobes"
 EVENT   : 事件名。如果省略，则根据 SYM+offs 或 MEMADDR 自动生成事件名
 MOD     : 包含给定 SYM 的模块名
 SYM[+offs] : 插入探测点的符号+偏移量
 SYM%return : 符号的返回地址
 MEMADDR : 插入探测点的地址
MAXACTIVE : 可以同时探测的指定函数实例的最大数量，或者为0表示使用默认值（如Documentation/trace/kprobes.rst 第1.3.1节中定义）
FETCHARGS : 参数。每个探针最多可以有128个参数
%REG      : 获取寄存器 REG 的值
  @ADDR    : 获取 ADDR 处的内存内容（ADDR 应位于内核空间）
  @SYM[+|-offs] : 获取 SYM +|- offs 处的内存内容（SYM 应为数据符号）
  $stackN  : 获取栈中的第 N 个条目（N >= 0）
  $stack   : 获取栈地址
$argN     : 获取第 N 个函数参数。（N >= 1）（注1）
  $retval  : 获取返回值。（注2）
  $comm    : 获取当前任务的进程名
+|-[u]OFFS(FETCHARG) : 获取 FETCHARG +|- OFFS 地址处的内存内容。（注3）（注4）
  \IMM     : 将立即数存储到参数中
NAME=FETCHARG : 将 FETCHARG 的名称设置为 NAME
FETCHARG:TYPE : 将 FETCHARG 的类型设置为 TYPE。目前支持的基本类型有（u8/u16/u32/u64/s8/s16/s32/s64）、十六进制类型（x8/x16/x32/x64）、VFS 层常见类型（%pd/%pD）、"char"、"string"、"ustring"、"symbol"、"symstr" 和位字段

（注1）仅适用于函数入口处的探针（offs == 0）。请注意，这种参数访问是尽力而为的，因为根据参数类型的不同，它可能通过栈传递。但这里只支持通过寄存器传递的参数。
（注2）仅适用于返回探针。请注意，这也是尽力而为的。根据返回值类型的不同，它可能通过一对寄存器传递。但这里只访问一个寄存器。
（注3）这对于获取数据结构中的某个字段非常有用。
(\*4) "u" 表示用户空间的间接引用。详见 :ref:`user_mem_access`

在 kretprobe 中访问函数参数
-------------------------------
可以在 kretprobe 中使用 `$arg<N>` fetcharg 访问函数参数。这有助于同时记录函数参数和返回值，并追踪结构字段的差异（用于调试函数是否正确更新给定的数据结构）。
请参阅 fprobe 事件中的 :ref:`示例<fprobetrace_exit_args_sample>` 了解其工作原理。

.. _kprobetrace_types:

类型
-----
支持几种类型的 fetcharg。Kprobe 跟踪器将根据给定的类型访问内存。前缀 's' 和 'u' 分别表示这些类型是有符号和无符号的。'x' 前缀表示它是无符号的。被跟踪的参数将以十进制 ('s' 和 'u') 或十六进制 ('x') 显示。如果没有类型转换，将根据架构使用 'x32' 或 'x64'（例如，x86-32 使用 x32，而 x86-64 使用 x64）。
这些值类型可以是数组。要记录数组数据，可以在基础类型后加上 '[N]'（其中 N 是一个小于 64 的固定数字）
例如，'x16[4]' 表示一个包含 4 个元素的 x16（2 字节十六进制）数组。
请注意，数组仅适用于内存类型 fetcharg，不能应用于寄存器/栈条目等（例如，'$stack1:x8[8]' 是错误的，但 '+8($stack):x8[8]' 是正确的）。

字符类型可用于显示被跟踪参数的字符值。
字符串类型是一种特殊类型，它从内核空间获取一个“以空字符终止”的字符串。这意味着如果字符串容器已经被换出，则会失败并存储 NULL。“ustring”类型是用户空间字符串的替代方案。
详见 :ref:`user_mem_access` 获取更多信息。
字符串数组类型与其他类型略有不同。对于其他基础类型，<base-type>[1] 等于 <base-type>（例如，+0(%di):x32[1] 与 +0(%di):x32 相同）。但是 string[1] 不等于 string。字符串类型本身代表“字符数组”，而字符串数组类型则代表“字符指针数组”。
所以，例如，+0(%di):string[1] 等于 +0(+0(%di)):string。
位字段（Bitfield）是另一种特殊类型，它需要三个参数：位宽、位偏移和容器大小（通常为 32）。语法如下：

b<位宽>@<位偏移>/<容器大小>

符号类型（'symbol'）是 u32 或 u64 类型的别名（取决于 BITS_PER_LONG），它以 "symbol+offset" 的形式显示给定指针。
另一方面，符号字符串类型（'symstr'）将给定地址转换为 "symbol+offset/symbolsize" 格式，并将其存储为以空字符终止的字符串。
使用 'symstr' 类型，您可以使用通配符模式过滤事件中的符号，而无需自己解析符号名称。
对于 $comm，默认类型为 "string"；其他任何类型都是无效的。
VFS 层通用类型（%pd/%pD）是一种特殊类型，可以从结构体 dentry 的地址或结构体 file 的地址中获取 dentry 或文件的名称。

.. _user_mem_access:

### 用户内存访问
------------------
Kprobe 事件支持用户空间内存访问。为此，您可以使用用户空间间接寻址语法或 'ustring' 类型。
用户空间间接寻址语法允许您访问用户空间数据结构中的一个字段。这是通过在间接寻址语法前加上 "u" 前缀来实现的。例如，+u4(%si) 表示它将从寄存器 %si 中的地址读取内存，偏移量为 4，并且预期该内存位于用户空间中。您也可以用这种方式处理字符串，例如 +u0(%si):string 将从寄存器 %si 中的地址读取一个字符串，该字符串预期位于用户空间中。'ustring' 是执行相同任务的一种快捷方式。也就是说，+0(%si):ustring 等同于 +u0(%si):string。
请注意，kprobe-event 提供了用户内存访问语法，但并不透明地使用它。这意味着如果您对用户空间内存使用普通的间接寻址或字符串类型，可能会失败，在某些架构上可能会始终失败。用户必须仔细检查目标数据是在内核空间还是用户空间。

### 每探针事件过滤
-------------------------
每探针事件过滤功能允许您为每个探针设置不同的过滤条件，并告诉您哪些参数将在跟踪缓冲区中显示。如果在 kprobe_events 中 'p:' 或 'r:' 后面指定了事件名称，则会在 tracing/events/kprobes/<EVENT> 目录下添加一个事件，该目录中可以看到 'id'、'enable'、'format'、'filter' 和 'trigger'。
### 启用：
您可以写入1或0来启用或禁用探针。

### 格式：
这显示了此探针事件的格式。

### 过滤：
您可以编写此事件的过滤规则。

### ID：
这显示了此探针事件的ID。

### 触发器：
这允许安装触发命令，当事件被命中时执行（详细信息请参阅Documentation/trace/events.rst，第6节）。

### 事件分析
您可以通过`/sys/kernel/tracing/kprobe_profile`检查总的探针命中次数和未命中次数。
第一列是事件名称，第二列是探针命中次数，第三列是探针未命中次数。

### 内核启动参数
---------------------
通过在启动内核时使用`kprobe_event=`参数，您可以添加并启用新的kprobe事件。该参数接受以分号分隔的kprobe事件，其格式类似于kprobe_events。
不同之处在于，探针定义参数是以逗号分隔而不是空格。例如，在`do_sys_open`上添加`myprobe`事件如下：

```
p:myprobe do_sys_open dfd=%ax filename=%dx flags=%cx mode=+4($stack)
```

对于内核启动参数，应如下所示（只需将空格替换为逗号）：

```
p:myprobe,do_sys_open,dfd=%ax,filename=%dx,flags=%cx,mode=+4($stack)
```

### 使用示例
--------------
要将一个探针作为新事件添加，可以向`kprobe_events`写入一个新的定义，如下所示：

```
echo 'p:myprobe do_sys_open dfd=%ax filename=%dx flags=%cx mode=+4($stack)' > /sys/kernel/tracing/kprobe_events
```

这将在`do_sys_open()`函数顶部设置一个kprobe，并记录前四个参数作为“myprobe”事件。请注意，每个函数参数分配到哪个寄存器/栈条目取决于架构特定的ABI。如果您不确定ABI，请尝试使用perf-tools中的probe子命令（您可以在tools/perf/目录下找到它）。
如本例所示，用户可以选择更熟悉的参数名称。
```sh
echo 'r:myretprobe do_sys_open $retval' >> /sys/kernel/tracing/kprobe_events
```

这行命令在 `do_sys_open()` 函数的返回点设置了一个 kretprobe，并将返回值记录为名为 "myretprobe" 的事件。你可以通过以下路径查看这些事件的格式：
```sh
cat /sys/kernel/tracing/events/kprobes/myprobe/format
```
输出如下：
```sh
name: myprobe
ID: 780
format:
        field:unsigned short common_type;       offset:0;       size:2; signed:0;
        field:unsigned char common_flags;       offset:2;       size:1; signed:0;
        field:unsigned char common_preempt_count;       offset:3; size:1;signed:0;
        field:int common_pid;   offset:4;       size:4; signed:1;

        field:unsigned long __probe_ip; offset:12;      size:4; signed:0;
        field:int __probe_nargs;        offset:16;      size:4; signed:1;
        field:unsigned long dfd;        offset:20;      size:4; signed:0;
        field:unsigned long filename;   offset:24;      size:4; signed:0;
        field:unsigned long flags;      offset:28;      size:4; signed:0;
        field:unsigned long mode;       offset:32;      size:4; signed:0;

print fmt: "(%lx) dfd=%lx filename=%lx flags=%lx mode=%lx", REC->__probe_ip, REC->dfd, REC->filename, REC->flags, REC->mode
```

你可以看到，这个事件有 4 个参数，正如你所指定的表达式所示。

```sh
echo > /sys/kernel/tracing/kprobe_events
```

这行命令会清除所有探针点。
或者，
```sh
echo -:myprobe >> kprobe_events
```

这行命令会选择性地清除探针点。定义之后，默认情况下每个事件都是禁用的。要启用这些事件，你需要执行以下命令：
```sh
echo 1 > /sys/kernel/tracing/events/kprobes/myprobe/enable
echo 1 > /sys/kernel/tracing/events/kprobes/myretprobe/enable
```

使用以下命令在某个时间间隔内开始跟踪：
```sh
# echo 1 > tracing_on
# 打开某个文件...
# echo 0 > tracing_on
```

你可以通过 `/sys/kernel/tracing/trace` 查看跟踪的信息：
```sh
cat /sys/kernel/tracing/trace
```
输出示例：
```sh
# tracer: nop
#
#           TASK-PID    CPU#    TIMESTAMP  FUNCTION
#              | |       |          |         |
             <...>-1447  [001] 1038282.286875: myprobe: (do_sys_open+0x0/0xd6) dfd=3 filename=7fffd1ec4440 flags=8000 mode=0
             <...>-1447  [001] 1038282.286878: myretprobe: (sys_openat+0xc/0xe <- do_sys_open) $retval=fffffffffffffffe
             <...>-1447  [001] 1038282.286885: myprobe: (do_sys_open+0x0/0xd6) dfd=ffffff9c filename=40413c flags=8000 mode=1b6
             <...>-1447  [001] 1038282.286915: myretprobe: (sys_open+0x1b/0x1d <- do_sys_open) $retval=3
             <...>-1447  [001] 1038282.286969: myprobe: (do_sys_open+0x0/0xd6) dfd=ffffff9c filename=4041c6 flags=98800 mode=10
             <...>-1447  [001] 1038282.286976: myretprobe: (sys_open+0x1b/0x1d <- do_sys_open) $retval=3
```

每一行显示了内核触发事件的时间，其中 `<- SYMBOL` 表示内核从 `SYMBOL` 返回（例如 `"sys_open+0x1b/0x1d <- do_sys_open"` 表示内核从 `do_sys_open` 返回到 `sys_open+0x1b`）。
当然，请提供您需要翻译的文本。
