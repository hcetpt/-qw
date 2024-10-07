SPDX 许可证标识符: GPL-2.0

==================================
Fprobe - 函数入口/出口探针
==================================

.. 作者: Masami Hiramatsu <mhiramat@kernel.org>

介绍
============

Fprobe 是一种基于 ftrace 的函数入口/出口探针机制。如果你只需要在函数的入口和出口附加回调，而不是使用 ftrace 的全部功能，那么你可以使用 fprobe。与 kprobes 和 kretprobes 相比，fprobe 在使用单个处理器对多个函数进行插桩时提供了更快的速度。本文档描述了如何使用 fprobe。

Fprobe 的用法
===================

Fprobe 是 ftrace（+ 类似于 kretprobe 的返回回调）的一个包装器，用于在多个函数的入口和出口附加回调。用户需要设置 `struct fprobe` 并将其传递给 `register_fprobe()`。通常，`fprobe` 数据结构如下初始化：

.. 代码块:: c

    struct fprobe fp = {
            .entry_handler  = my_entry_callback,
            .exit_handler   = my_exit_callback,
    };

为了启用 fprobe，可以调用 `register_fprobe()`、`register_fprobe_ips()` 或者 `register_fprobe_syms()` 中的一个。这些函数以不同类型的参数注册 fprobe。
`register_fprobe()` 通过函数名称过滤器启用 fprobe。
例如，这将在除 "func2()" 之外的所有 "func*()" 函数上启用 @fp ：

  `register_fprobe(&fp, "func*", "func2");`

`register_fprobe_ips()` 通过 ftrace 位置地址启用 fprobe。
例如，
.. 代码块:: c

    unsigned long ips[] = { 0x.... };

    register_fprobe_ips(&fp, ips, ARRAY_SIZE(ips));

而 `register_fprobe_syms()` 通过符号名称启用 fprobe。
例如
```c
char syms[] = {"func1", "func2", "func3"};

register_fprobe_syms(&fp, syms, ARRAY_SIZE(syms));
```

要禁用（从函数中移除）这个 fprobe，可以调用：

```c
unregister_fprobe(&fp);
```

你可以临时（软）禁用 fprobe：

```c
disable_fprobe(&fp);
```

然后通过以下方式恢复：

```c
enable_fprobe(&fp);
```

上述功能定义在包含的头文件中：

```c
#include <linux/fprobe.h>
```

与 ftrace 类似，在调用 `register_fprobe()` 后，注册的回调函数会在该函数返回前开始被调用。详见 :file:`Documentation/trace/ftrace.rst`

此外，`unregister_fprobe()` 保证在该函数返回后，进入和退出处理程序将不再被函数调用，就像 `unregister_ftrace_function()` 一样。

### fprobe 进入/退出处理程序

进入/退出回调函数的原型如下：

```c
int entry_callback(struct fprobe *fp, unsigned long entry_ip, unsigned long ret_ip, struct pt_regs *regs, void *entry_data);

void exit_callback(struct fprobe *fp, unsigned long entry_ip, unsigned long ret_ip, struct pt_regs *regs, void *entry_data);
```

注意，`@entry_ip` 在函数入口时保存，并传递给退出处理程序。
如果进入回调函数返回非零值，则相应的退出回调将被取消。
- `@fp`：这是与此处理程序相关的 `fprobe` 数据结构的地址。你可以将 `fprobe` 嵌入到你的数据结构中，并通过 `container_of()` 宏从 `@fp` 获取它。`@fp` 必须不为 NULL。
- `@entry_ip`：这是被跟踪函数的 ftrace 地址（进入和退出）。注意这可能不是函数的实际入口地址，而是 ftrace 被插入的地址。
- `@ret_ip`：这是被跟踪函数将返回到的返回地址，位于调用者处的某个位置。此地址可以在进入和退出时使用。
- `@regs`：这是 `pt_regs` 数据结构，在进入和退出时获取。注意 `@regs` 的指令指针可能与 `entry_handler` 中的 `@entry_ip` 不同。如果你需要跟踪的指令指针，请使用 `@entry_ip`。另一方面，在 `exit_handler` 中，`@regs` 的指令指针设置为当前返回地址。
@entry_data
这是用于在入口和出口处理器之间共享数据的本地存储。
此存储默认为NULL。如果用户在注册fprobe时指定了`exit_handler`字段和`entry_data_size`字段，则会分配此存储，并将其传递给`entry_handler`和`exit_handler`。

与kprobes共享回调
=================

由于fprobe（以及ftrace）的递归安全性与kprobes略有不同，因此如果用户希望在同一代码中运行fprobe和kprobes，可能会导致问题。
kprobes具有每个CPU上的`current_kprobe`变量，该变量可以在所有情况下保护kprobe处理器免于递归。另一方面，fprobe仅使用ftrace_test_recursion_trylock()。这允许中断上下文在fprobe用户处理器运行时调用另一个（或相同的）fprobe。
如果通用回调代码有自己的递归检测机制，或者能够在不同的上下文中（正常/中断/NMI）处理递归，这不是问题。
但如果它依赖于`current_kprobe`递归锁，则必须检查kprobe_running()并使用kprobe_busy_*() API。
fprobe有一个FPROBE_FL_KPROBE_SHARED标志来实现这一点。如果你的通用回调代码将与kprobes共享，请在注册fprobe之前设置FPROBE_FL_KPROBE_SHARED，如下所示：

```c
fprobe.flags = FPROBE_FL_KPROBE_SHARED;
register_fprobe(&fprobe, "func*", NULL);
```

这将保护你的通用回调不被嵌套调用。

错过的计数器
=============

fprobe数据结构包含一个与kprobes相同的`fprobe::nmissed`计数器字段。
此计数器会在以下情况增加：

- fprobe无法获取ftrace_recursion锁。这通常意味着由其他ftrace用户跟踪的函数从entry_handler中调用。
- 由于缺少rethook（用于钩住函数返回的影子栈），fprobe无法设置函数退出。

无论哪种情况，`fprobe::nmissed`字段都会增加。因此，在前一种情况下，将跳过入口和出口回调；在后一种情况下，将跳过出口回调，但两种情况下计数器都会增加1。
请注意，如果你在注册fprobe时将FTRACE_OPS_FL_RECURSION和/或FTRACE_OPS_FL_RCU设置到`fprobe::ops::flags`（ftrace_ops::flags），则此计数器可能无法正确工作，因为ftrace会跳过增加计数器的fprobe函数。
函数和结构体
========================

.. kernel-doc:: include/linux/fprobe.h
.. kernel-doc:: kernel/trace/fprobe.c

请注意，这里的“.. kernel-doc::”似乎是用于某种文档生成工具的指令，而不是实际的代码或文本内容。如果你需要进一步的帮助或具体的文档格式，请告知。
