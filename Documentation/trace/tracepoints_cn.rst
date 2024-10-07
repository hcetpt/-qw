使用 Linux 内核追踪点
======================

作者：Mathieu Desnoyers

本文档介绍了 Linux 内核追踪点及其用法。它提供了如何在内核中插入追踪点以及将探测函数连接到这些追踪点的示例，并给出了一些探测函数的示例。

追踪点的目的
------------
代码中的一个追踪点提供了一个调用函数（探测器）的钩子，你可以在运行时提供这个函数。一个追踪点可以是“开启”状态（有一个探测器与之连接）或“关闭”状态（没有探测器连接）。当一个追踪点处于“关闭”状态时，除了增加一点时间开销（检查分支条件）和空间开销（在被监控函数末尾添加几个字节的函数调用，并在单独的部分添加数据结构）外，它不会产生任何影响。当一个追踪点处于“开启”状态时，每次执行追踪点时，都会在调用者的执行上下文中调用你提供的函数。当提供的函数结束执行后，它会返回调用者（从追踪点位置继续执行）。

你可以在代码的重要位置放置追踪点。它们是轻量级的钩子，可以传递任意数量的参数，这些参数的原型在头文件中的追踪点声明中描述。
它们可用于跟踪和性能核算。

使用方法
-------
使用追踪点需要两个元素：

- 在头文件中定义的追踪点
- 在 C 代码中的追踪点语句

为了使用追踪点，你需要包含 `linux/tracepoint.h` 文件。例如，在 `include/trace/events/subsys.h` 中：

```c
#undef TRACE_SYSTEM
#define TRACE_SYSTEM subsys

#if !defined(_TRACE_SUBSYS_H) || defined(TRACE_HEADER_MULTI_READ)
#define _TRACE_SUBSYS_H

#include <linux/tracepoint.h>

DECLARE_TRACE(subsys_eventname,
              TP_PROTO(int firstarg, struct task_struct *p),
              TP_ARGS(firstarg, p));

#endif /* _TRACE_SUBSYS_H */

/* 这部分必须位于保护之外 */
#include <trace/define_trace.h>
```

在 `subsys/file.c`（其中必须添加追踪语句）中：

```c
#include <trace/events/subsys.h>

#define CREATE_TRACE_POINTS
DEFINE_TRACE(subsys_eventname);

void somefct(void)
{
    ..
    trace_subsys_eventname(arg, task);
    ..
}
```

其中：
- `subsys_eventname` 是你事件的唯一标识符

  - `subsys` 是你的子系统的名称
- `eventname` 是要追踪的事件名称
- `TP_PROTO(int firstarg, struct task_struct *p)` 是此追踪点调用的函数原型
- `TP_ARGS(firstarg, p)` 是参数名称，与原型中的相同
- 如果在多个源文件中使用该头文件，`#define CREATE_TRACE_POINTS` 应仅出现在一个源文件中

将一个函数（探针）连接到一个追踪点是通过 `register_trace_subsys_eventname()` 提供特定追踪点的探针（要调用的函数）来完成的。移除一个探针是通过 `unregister_trace_subsys_eventname()` 来完成的；这会移除该探针。在模块退出函数结束之前必须调用 `tracepoint_synchronize_unregister()` 以确保没有调用者仍在使用该探针。这一点加上在探针调用周围禁用了抢占，确保了探针移除和模块卸载的安全性。

追踪点机制支持插入同一个追踪点的多个实例，但在整个内核中必须为给定的追踪点定义一个单一的定义，以确保不会发生类型冲突。使用原型对追踪点进行命名转换，以确保类型正确。探针类型的正确性验证由编译器在注册时完成。追踪点可以放在内联函数、内联静态函数、展开循环以及常规函数中。

这里建议使用 “subsys_event” 的命名方案作为一种约定，旨在限制冲突。追踪点名称在整个内核中是全局唯一的：无论它们是在核心内核映像中还是在模块中，都被认为是相同的。

如果需要在内核模块中使用追踪点，则可以使用 `EXPORT_TRACEPOINT_SYMBOL_GPL()` 或 `EXPORT_TRACEPOINT_SYMBOL()` 导出定义的追踪点。

如果需要为追踪点参数做一些工作，并且这些工作仅用于追踪点，那么可以在以下形式的 if 语句中将其封装起来：

```c
if (trace_foo_bar_enabled()) {
    int i;
    int tot = 0;

    for (i = 0; i < count; i++)
        tot += calculate_nuggets();

    trace_foo_bar(tot);
}
```

所有 `trace_<tracepoint>()` 调用都有一个对应的 `trace_<tracepoint>_enabled()` 函数定义，该函数在追踪点启用时返回 true，在未启用时返回 false。`trace_<tracepoint>()` 应始终位于 `if (trace_<tracepoint>_enabled())` 块中，以防止追踪点启用与检查之间的竞态条件。
使用 `trace_<tracepoint>_enabled()` 的优点在于，它利用了 tracepoint 的静态键（static_key），使得 if 语句可以通过跳转标签实现，并避免条件分支。

.. note:: 便利的宏 `TRACE_EVENT` 提供了一种替代的方式来定义 tracepoint。可以参考以下一系列文章以获取更多详细信息：http://lwn.net/Articles/379903、http://lwn.net/Articles/381064 和 http://lwn.net/Articles/383362

如果你需要从头文件中调用一个 tracepoint，不建议直接调用或使用 `trace_<tracepoint>_enabled()` 函数调用，因为当一个头文件被包含在设置了 `CREATE_TRACE_POINTS` 的文件中时，tracepoint 可能会产生副作用。此外，`trace_<tracepoint>()` 并不是很小的内联函数，如果被其他内联函数使用，可能会导致内核膨胀。相反，应该包含 `tracepoint-defs.h` 并使用 `tracepoint_enabled()`。

在 C 文件中：

```c
void do_trace_foo_bar_wrapper(args)
{
    trace_foo_bar(args);
}
```

在头文件中：

```c
DECLARE_TRACEPOINT(foo_bar);

static inline void some_inline_function()
{
    [..]
    if (tracepoint_enabled(foo_bar))
        do_trace_foo_bar_wrapper(args);
    [..]
}
```
