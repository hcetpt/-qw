=========================================
Uprobe-tracer：基于Uprobe的事件追踪
=========================================

:作者: Srikar Dronamraju

概述
--------
基于Uprobe的追踪事件类似于基于Kprobe的追踪事件。
要启用此功能，请使用CONFIG_UPROBE_EVENTS=y编译内核。
与Kprobe事件追踪器类似，不需要通过current_tracer激活。相反，可以通过/sys/kernel/tracing/uprobe_events添加探针点，并通过/sys/kernel/tracing/events/uprobes/<EVENT>/enable启用它。
但是，与Kprobe事件追踪器不同的是，Uprobe事件接口需要用户计算对象中探针点的偏移量。
您也可以使用/sys/kernel/tracing/dynamic_events代替uprobe_events。该接口将提供对其他动态事件的统一访问。

Uprobe_tracer概览
-------------------------
::

  p[:[GRP/][EVENT]] PATH:OFFSET [FETCHARGS] : 设置一个Uprobe
  r[:[GRP/][EVENT]] PATH:OFFSET [FETCHARGS] : 设置一个返回Uprobe（uretprobe）
  p[:[GRP/][EVENT]] PATH:OFFSET%return [FETCHARGS] : 设置一个返回Uprobe（uretprobe）
  -:[GRP/][EVENT]                           : 清除Uprobe或uretprobe事件

  GRP           : 组名。如果省略，默认值为"uprobes"
  EVENT         : 事件名。如果省略，则根据PATH+OFFSET生成事件名
  PATH          : 可执行文件或库的路径
  OFFSET        : 插入探针的位置偏移量
  OFFSET%return : 插入返回探针的位置偏移量
FETCHARGS     : 参数。每个探测器可以有最多128个参数。
%REG          : 获取寄存器 REG 的值
   @ADDR      : 获取内存地址 ADDR 处的值（ADDR 应该在用户空间）
   @+OFFSET   : 获取文件 PATH 同一文件中 OFFSET 地址处的内存值
   $stackN    : 获取栈中的第 N 个条目（N >= 0）
   $stack     : 获取栈地址
   $retval    : 获取返回值。（仅适用于返回探测器）
   $comm      : 获取当前任务的名称
+|-[u]OFFS(FETCHARG) : 在 FETCHARG 地址基础上加或减 OFFS 后获取内存值。（适用于数据结构字段）（对于 kprobe 事件，前缀 "u" 将被忽略，因为 uprobes 只能访问用户空间内存）
   \IMM       : 将立即值存储到参数中
NAME=FETCHARG     : 将 FETCHARG 的参数名称设置为 NAME
FETCHARG:TYPE     : 将 FETCHARG 的类型设置为 TYPE。目前支持的基本类型有（u8/u16/u32/u64/s8/s16/s32/s64），十六进制类型（x8/x16/x32/x64），"string" 和位字段。

（注释 1）仅适用于返回探测器
（注释 2）这在获取数据结构字段时很有用
（注释 3）与 kprobe 事件不同，前缀 "u" 将被忽略，因为 uprobes 事件只能访问用户空间内存

类型
-----
几种类型的参数支持获取。Uprobe 跟踪器将根据给定的类型访问内存。前缀 's' 和 'u' 分别表示这些类型是有符号和无符号的。'x' 前缀表示它是无符号的。跟踪的参数将以十进制（'s' 和 'u'）或十六进制（'x'）形式显示。如果没有指定类型，则根据架构使用 'x32' 或 'x64'（例如，x86-32 使用 x32，x86-64 使用 x64）。
字符串类型是一种特殊类型，它从用户空间获取一个以空字符结尾的字符串。
位字段是另一种特殊类型，它需要三个参数：位宽、位偏移和容器大小（通常为32）。语法如下：

```
b<位宽>@<位偏移>/<容器大小>
```

对于`$comm`，默认类型是“字符串”；其他任何类型都是无效的。

### 事件分析
你可以通过`/sys/kernel/tracing/uprobe_profile`检查每个事件的探针命中总数。第一列是文件名，第二列是事件名称，第三列是探针命中的次数。

### 使用示例
* 添加一个探针作为新的uprobe事件，向`uprobe_events`写入一个新的定义（在可执行文件`/bin/bash`的偏移量0x4245c0处设置一个uprobe）：

  ```
  echo 'p /bin/bash:0x4245c0' > /sys/kernel/tracing/uprobe_events
  ```

* 添加一个探针作为新的uretprobe事件：

  ```
  echo 'r /bin/bash:0x4245c0' > /sys/kernel/tracing/uprobe_events
  ```

* 取消已注册的事件：

  ```
  echo '-:p_bash_0x4245c0' >> /sys/kernel/tracing/uprobe_events
  ```

* 打印已注册的事件：

  ```
  cat /sys/kernel/tracing/uprobe_events
  ```

* 清除所有事件：

  ```
  echo > /sys/kernel/tracing/uprobe_events
  ```

下面的例子展示了如何在探测文本地址时转储指令指针和%ax寄存器。探测`/bin/zsh`中的`zfree`函数：

  ```
  # cd /sys/kernel/tracing/
  # cat /proc/`pgrep zsh`/maps | grep /bin/zsh | grep r-xp
  00400000-0048a000 r-xp 00000000 08:03 130904 /bin/zsh
  # objdump -T /bin/zsh | grep -w zfree
  0000000000446420 g    DF .text  0000000000000012  Base        zfree
  ```

0x46420 是 `zfree` 在对象 `/bin/zsh` 中的偏移量，该对象加载在 0x00400000 处。因此设置uprobe的命令如下：

  ```
  # echo 'p:zfree_entry /bin/zsh:0x46420 %ip %ax' > uprobe_events
  ```

对于uretprobe的命令如下：

  ```
  # echo 'r:zfree_exit /bin/zsh:0x46420 %ip %ax' >> uprobe_events
  ```

注意：用户需要显式计算对象中探针点的偏移量。

我们可以通过查看`uprobe_events`文件来查看已注册的事件：

  ```
  # cat uprobe_events
  p:uprobes/zfree_entry /bin/zsh:0x00046420 arg1=%ip arg2=%ax
  r:uprobes/zfree_exit /bin/zsh:0x00046420 arg1=%ip arg2=%ax
  ```

事件的格式可以通过查看文件`events/uprobes/zfree_entry/format`来查看：

  ```
  # cat events/uprobes/zfree_entry/format
  name: zfree_entry
  ID: 922
  format:
       field:unsigned short common_type;         offset:0;  size:2; signed:0;
       field:unsigned char common_flags;         offset:2;  size:1; signed:0;
       field:unsigned char common_preempt_count; offset:3;  size:1; signed:0;
       field:int common_pid;                     offset:4;  size:4; signed:1;
       field:int common_padding;                 offset:8;  size:4; signed:1;

       field:unsigned long __probe_ip;           offset:12; size:4; signed:0;
       field:u32 arg1;                           offset:16; size:4; signed:0;
       field:u32 arg2;                           offset:20; size:4; signed:0;

  print fmt: "(%lx) arg1=%lx arg2=%lx", REC->__probe_ip, REC->arg1, REC->arg2
  ```

定义之后，默认情况下每个事件都是禁用的。为了追踪这些事件，你需要启用它们：

  ```
  # echo 1 > events/uprobes/enable
  ```

开始追踪，休眠一段时间后停止追踪：

  ```
  # echo 1 > tracing_on
  # sleep 20
  # echo 0 > tracing_on
  ```

你也可以通过以下命令禁用事件：

  ```
  # echo 0 > events/uprobes/enable
  ```

你还可以通过`/sys/kernel/tracing/trace`查看追踪的信息：

  ```
  # cat trace
  # tracer: nop
  #
  #           TASK-PID    CPU#    TIMESTAMP  FUNCTION
  #              | |       |          |         |
                 zsh-24842 [006] 258544.995456: zfree_entry: (0x446420) arg1=446420 arg2=79
                 zsh-24842 [007] 258545.000270: zfree_exit:  (0x446540 <- 0x446420) arg1=446540 arg2=0
                 zsh-24842 [002] 258545.043929: zfree_entry: (0x446420) arg1=446420 arg2=79
                 zsh-24842 [004] 258547.046129: zfree_exit:  (0x446540 <- 0x446420) arg1=446540 arg2=0
  ```

输出显示uprobe被触发，进程ID为24842，指令指针为0x446420，%ax寄存器的内容为79。uretprobe被触发，指令指针为0x446540，对应的功能入口为0x446420。
