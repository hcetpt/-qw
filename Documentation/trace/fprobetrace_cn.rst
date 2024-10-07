SPDX 许可声明：GPL-2.0

==========================
基于 Fprobe 的事件追踪
==========================

.. 作者: Masami Hiramatsu <mhiramat@kernel.org>

概述
--------

Fprobe 事件与 kprobe 事件类似，但仅限于在函数的入口和出口进行探测。对于许多只追踪某些特定函数的应用场景来说，这已经足够了。
本文档还涵盖了追踪点探测事件（tprobe），因为这也仅在追踪点入口处工作。用户可以追踪追踪点参数的一部分，或者不带追踪事件的追踪点，这些在 tracefs 中并未暴露出来。
与其他动态事件一样，Fprobe 事件和追踪点探测事件是通过 tracefs 上的 `dynamic_events` 接口文件定义的。

Fprobe 事件概览
-------------------------
::

  f[:[GRP1/][EVENT1]] SYM [FETCHARGS]                       : 在函数入口处进行探测
  f[MAXACTIVE][:[GRP1/][EVENT1]] SYM%return [FETCHARGS]     : 在函数出口处进行探测
  t[:[GRP2/][EVENT2]] TRACEPOINT [FETCHARGS]                : 在追踪点进行探测

 GRP1           : Fprobe 的组名。如果省略，则使用 "fprobes"
 GRP2           : Tprobe 的组名。如果省略，则使用 "tracepoints"
 EVENT1         : Fprobe 的事件名。如果省略，则事件名为 "SYM__entry" 或 "SYM__exit"
 EVENT2         : Tprobe 的事件名。如果省略，则事件名与 "TRACEPOINT" 相同，但如果 "TRACEPOINT" 以数字字符开头，则使用 "_TRACEPOINT"
 MAXACTIVE      : 指定函数同时可以探测的最大实例数，或 0 表示默认值，具体定义见 Documentation/trace/fprobe.rst

 FETCHARGS      : 参数。每个探测器最多可以有 128 个参数
 ARG           : 使用 BTF 获取 "ARG" 函数参数（仅适用于函数入口或追踪点）。（\*1）
  @ADDR         : 获取 ADDR 处的内存（ADDR 应位于内核中）
  @SYM[+|-offs] : 获取 SYM +|- offs 处的内存（SYM 应为数据符号）
  $stackN       : 获取栈的第 N 个条目（N >= 0）
  $stack        : 获取栈地址
 $argN         : 获取函数的第 N 个参数。（N >= 1）（\*2）
  $retval       : 获取返回值。（\*3）
  $comm         : 获取当前任务的 comm
+|-[u]OFFS(FETCHARG) : 从 FETCHARG +|- OFFS 地址处获取内存。(注4)(注5)
  \IMM          : 将一个立即值存储到参数中
NAME=FETCHARG : 将 NAME 设置为 FETCHARG 的参数名称
FETCHARG:TYPE : 将 TYPE 设置为 FETCHARG 的类型。目前支持的基本类型有
                  (u8/u16/u32/u64/s8/s16/s32/s64)，十六进制类型
                  (x8/x16/x32/x64)，"char"，"string"，"ustring"，"symbol"，"symstr"
                  和位字段
(注1) 这仅在启用 BTF 时可用
(注2) 仅适用于函数入口的探针（offs == 0）。注意，这种参数访问是尽力而为的，
        因为根据参数类型，它可能通过栈传递。但这里只支持通过寄存器传递的参数
(注3) 仅适用于返回探针。注意这也是尽力而为的。根据返回值类型，它可能通过一对寄存器传递。
        但这里只访问一个寄存器
(注4) 这对于获取数据结构中的字段非常有用
(注5) "u" 表示用户空间引用

退出时的函数参数
--------------------------
可以在退出探针中使用 $arg<N> fetcharg 访问函数参数。这有助于记录函数参数和返回值，并
跟踪结构字段的变化（用于调试函数是否正确更新了给定的数据结构）
请参见下面的 :ref:`示例<fprobetrace_exit_args_sample>` 了解其工作原理。
BTF 参数
-------------

BTF（BPF 类型格式）参数允许用户通过名称而不是 ``$argN`` 来追踪函数和追踪点的参数。如果内核配置了 CONFIG_BPF_SYSCALL 和 CONFIG_DEBUG_INFO_BTF，此功能可用。

如果用户仅指定 BTF 参数，则事件的参数名称也会自动设置为给定名称。例如：

```
# echo 'f:myprobe vfs_read count pos' >> dynamic_events
# cat dynamic_events
f:fprobes/myprobe vfs_read count=count pos=pos
```

它还会根据 BTF 信息选择获取类型。例如，在上面的例子中，`count` 是无符号长整型，而 `pos` 是一个指针。因此，两者都会转换为 64 位无符号长整型，但只有 `pos` 使用 `%Lx` 打印格式：

```
# cat events/fprobes/myprobe/format
name: myprobe
ID: 1313
format:
    field:unsigned short common_type;	offset:0;	size:2;	signed:0;
    field:unsigned char common_flags;	offset:2;	size:1;	signed:0;
    field:unsigned char common_preempt_count;	offset:3;	size:1;	signed:0;
    field:int common_pid;	offset:4;	size:4;	signed:1;

    field:unsigned long __probe_ip;	offset:8;	size:8;	signed:0;
    field:u64 count;	offset:16;	size:8;	signed:0;
    field:u64 pos;	offset:24;	size:8;	signed:0;

print fmt: "(%lx) count=%Lu pos=0x%Lx", REC->__probe_ip, REC->count, REC->pos
```

如果用户不确定参数名称，`$arg*` 将很有帮助。`$arg*` 会扩展为函数或追踪点的所有函数参数。例如：

```
# echo 'f:myprobe vfs_read $arg*' >> dynamic_events
# cat dynamic_events
f:fprobes/myprobe vfs_read file=file buf=buf count=count pos=pos
```

BTF 还会影响 `$retval`。如果用户没有设置任何类型，`$retval` 的类型会自动从 BTF 中选取。如果函数返回 `void`，则会拒绝 `$retval`。

您可以使用允许运算符 `->`（对于指针类型）和点运算符 `.`（对于数据结构类型）来访问数据结构的数据字段。例如：

```
# echo 't sched_switch preempt prev_pid=prev->pid next_pid=next->pid' >> dynamic_events
```

字段访问运算符 `->` 和 `.` 可以组合使用来访问更深的成员和其他由成员指向的结构成员，例如 `foo->bar.baz->qux`。如果有非命名联合成员，您可以直接像 C 代码那样访问它。例如：

```
struct {
	union {
		int a;
		int b;
	};
} *foo;
```

要访问 `a` 和 `b`，可以使用 `foo->a` 和 `foo->b`。这种数据字段访问也可以用于通过 `$retval` 访问返回值，例如 `$retval->name`。

对于这些 BTF 参数和字段，`:string` 和 `:ustring` 会改变行为。如果这些用于 BTF 参数或字段，它会检查 BTF 类型是否为 `char *` 或 `char []`。如果不是，则会拒绝应用字符串类型。此外，借助 BTF 支持，您无需使用内存解引用运算符（`+0(PTR)`）来访问 `PTR` 指向的字符串。它会根据 BTF 类型自动添加内存解引用运算符。例如：

```
# echo 't sched_switch prev->comm:string' >> dynamic_events
# echo 'f getname_flags%return $retval->name:string' >> dynamic_events
```

`prev->comm` 是数据结构中的嵌入式字符数组，而 `$retval->name` 是数据结构中的字符指针。但在两种情况下，都可以使用 `:string` 类型来获取字符串。

使用示例
--------------

以下是一个在 `vfs_read()` 函数入口和出口添加 fprobe 事件的示例，并使用 BTF 参数：

```
# echo 'f vfs_read $arg*' >> dynamic_events
# echo 'f vfs_read%return $retval' >> dynamic_events
# cat dynamic_events
f:fprobes/vfs_read__entry vfs_read file=file buf=buf count=count pos=pos
f:fprobes/vfs_read__exit vfs_read%return arg1=$retval
# echo 1 > events/fprobes/enable
# head -n 20 trace | tail
#           TASK-PID     CPU#  |||||  TIMESTAMP  FUNCTION
#              | |         |   |||||     |         |
               sh-70      [000] ...1.   335.883195: vfs_read__entry: (vfs_read+0x4/0x340) file=0xffff888005cf9a80 buf=0x7ffef36c6879 count=1 pos=0xffffc900005aff08
               sh-70      [000] .....   335.883208: vfs_read__exit: (ksys_read+0x75/0x100 <- vfs_read) arg1=1
               sh-70      [000] ...1.   335.883220: vfs_read__entry: (vfs_read+0x4/0x340) file=0xffff888005cf9a80 buf=0x7ffef36c6879 count=1 pos=0xffffc900005aff08
               sh-70      [000] .....   335.883224: vfs_read__exit: (ksys_read+0x75/0x100 <- vfs_read) arg1=1
               sh-70      [000] ...1.   335.883232: vfs_read__entry: (vfs_read+0x4/0x340) file=0xffff888005cf9a80 buf=0x7ffef36c687a count=1 pos=0xffffc900005aff08
               sh-70      [000] .....   335.883237: vfs_read__exit: (ksys_read+0x75/0x100 <- vfs_read) arg1=1
               sh-70      [000] ...1.   336.050329: vfs_read__entry: (vfs_read+0x4/0x340) file=0xffff888005cf9a80 buf=0x7ffef36c6879 count=1 pos=0xffffc900005aff08
               sh-70      [000] .....   336.050343: vfs_read__exit: (ksys_read+0x75/0x100 <- vfs_read) arg1=1
```

您可以看到所有函数参数和返回值都被记录为有符号整数。

此外，这里还有一个在 `sched_switch` 追踪点上启用追踪事件的示例。为了比较结果，这同样启用了 `sched_switch` 追踪事件。
```sh
# echo 't sched_switch $arg*' >> dynamic_events
# echo 1 > events/sched/sched_switch/enable
# echo 1 > events/tracepoints/sched_switch/enable
# echo > trace
# head -n 20 trace | tail
#           TASK-PID     CPU#  |||||  TIMESTAMP  FUNCTION
#              | |         |   |||||     |         |
               sh-70      [000] d..2.  3912.083993: sched_switch: prev_comm=sh prev_pid=70 prev_prio=120 prev_state=S ==> next_comm=swapper/0 next_pid=0 next_prio=120
               sh-70      [000] d..3.  3912.083995: sched_switch: (__probestub_sched_switch+0x4/0x10) preempt=0 prev=0xffff88800664e100 next=0xffffffff828229c0 prev_state=1
           <idle>-0       [000] d..2.  3912.084183: sched_switch: prev_comm=swapper/0 prev_pid=0 prev_prio=120 prev_state=R ==> next_comm=rcu_preempt next_pid=16 next_prio=120
           <idle>-0       [000] d..3.  3912.084184: sched_switch: (__probestub_sched_switch+0x4/0x10) preempt=0 prev=0xffffffff828229c0 next=0xffff888004208000 prev_state=0
      rcu_preempt-16      [000] d..2.  3912.084196: sched_switch: prev_comm=rcu_preempt prev_pid=16 prev_prio=120 prev_state=I ==> next_comm=swapper/0 next_pid=0 next_prio=120
      rcu_preempt-16      [000] d..3.  3912.084196: sched_switch: (__probestub_sched_switch+0x4/0x10) preempt=0 prev=0xffff888004208000 next=0xffffffff828229c0 prev_state=1026
           <idle>-0       [000] d..2.  3912.085191: sched_switch: prev_comm=swapper/0 prev_pid=0 prev_prio=120 prev_state=R ==> next_comm=rcu_preempt next_pid=16 next_prio=120
           <idle>-0       [000] d..3.  3912.085191: sched_switch: (__probestub_sched_switch+0x4/0x10) preempt=0 prev=0xffffffff828229c0 next=0xffff888004208000 prev_state=0

如您所见，`sched_switch` 的跟踪事件显示了*已处理*的参数，而另一方面，`sched_switch` 的跟踪点探测事件显示了*原始*的参数。这意味着您可以访问由 `prev` 和 `next` 参数指向的任务结构中的任何字段值。
例如，通常 `task_struct::start_time` 不会被跟踪，但通过此跟踪探测事件，您可以跟踪该字段如下所示：

```sh
# echo 't sched_switch comm=next->comm:string next->start_time' > dynamic_events
# head -n 20 trace | tail
#           TASK-PID     CPU#  |||||  TIMESTAMP  FUNCTION
#              | |         |   |||||     |         |
               sh-70      [000] d..3.  5606.686577: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="rcu_preempt" usage=1 start_time=245000000
      rcu_preempt-16      [000] d..3.  5606.686602: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="sh" usage=1 start_time=1596095526
               sh-70      [000] d..3.  5606.686637: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="swapper/0" usage=2 start_time=0
           <idle>-0       [000] d..3.  5606.687190: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="rcu_preempt" usage=1 start_time=245000000
      rcu_preempt-16      [000] d..3.  5606.687202: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="swapper/0" usage=2 start_time=0
           <idle>-0       [000] d..3.  5606.690317: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="kworker/0:1" usage=1 start_time=137000000
      kworker/0:1-14      [000] d..3.  5606.690339: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="swapper/0" usage=2 start_time=0
           <idle>-0       [000] d..3.  5606.692368: sched_switch: (__probestub_sched_switch+0x4/0x10) comm="kworker/0:1" usage=1 start_time=137000000

.. _fprobetrace_exit_args_sample:

返回探测允许我们访问某些函数的结果，这些函数返回错误代码，并且其结果是通过函数参数传递的，例如一个结构初始化函数。
例如，`vfs_open()` 会将文件结构链接到inode并更新模式。您可以通过返回探测来跟踪这些更改：

```sh
# echo 'f vfs_open mode=file->f_mode:x32 inode=file->f_inode:x64' >> dynamic_events
# echo 'f vfs_open%%return mode=file->f_mode:x32 inode=file->f_inode:x64' >> dynamic_events
# echo 1 > events/fprobes/enable
# cat trace
              sh-131     [006] ...1.  1945.714346: vfs_open__entry: (vfs_open+0x4/0x40) mode=0x2 inode=0x0
              sh-131     [006] ...1.  1945.714358: vfs_open__exit: (do_open+0x274/0x3d0 <- vfs_open) mode=0x4d801e inode=0xffff888008470168
             cat-143     [007] ...1.  1945.717949: vfs_open__entry: (vfs_open+0x4/0x40) mode=0x1 inode=0x0
             cat-143     [007] ...1.  1945.717956: vfs_open__exit: (do_open+0x274/0x3d0 <- vfs_open) mode=0x4a801d inode=0xffff888005f78d28
             cat-143     [007] ...1.  1945.720616: vfs_open__entry: (vfs_open+0x4/0x40) mode=0x1 inode=0x0
             cat-143     [007] ...1.  1945.728263: vfs_open__exit: (do_open+0x274/0x3d0 <- vfs_open) mode=0xa800d inode=0xffff888004ada8d8

您可以看到，在 `vfs_open()` 中 `file::f_mode` 和 `file::f_inode` 已经被更新。
```
