使用 ftrace 挂钩函数
=========================

.. 版权所有 2017 VMware Inc
..   作者：Steven Rostedt <srostedt@goodmis.org>
..  许可证：GNU 自由文档许可证，版本 1.2
..               （同时在GPL v2下授权）

为 4.14 编写

介绍
============

ftrace 基础设施最初是为了在函数开始处附加回调以记录和追踪内核流程而创建的。但函数开始处的回调可以有其他用途，例如实时内核修补或安全监控。本文档描述了如何使用 ftrace 实现自己的函数回调。

ftrace 上下文
==================
.. 警告::

  在内核中的几乎任何函数上添加回调带有风险。回调可能在任何上下文中被调用（正常、软中断、硬中断和 NMI）。回调也可能在进入空闲状态之前、在 CPU 启动和关闭期间或转到用户空间时被调用。
这要求对回调内部的操作格外小心。回调可能会在RCU保护范围之外被调用。
有帮助函数来防止递归，并确保RCU正在监视。这些将在下面解释。

ftrace_ops 结构体
=======================

要注册一个函数回调，需要一个 ftrace_ops。这个结构体用于告诉 ftrace 应该调用哪个函数作为回调，以及回调将执行哪些保护措施而不需 ftrace 处理。

在向 ftrace 注册 ftrace_ops 时，只需设置一个字段：

.. 代码块:: c

  struct ftrace_ops ops = {
          .func			= my_callback_func,
          .flags			= MY_FTRACE_FLAGS,
          .private			= any_private_data_structure,
  };

其中 .flags 和 .private 是可选的，只有 .func 是必需的。
要启用追踪，请调用::

    register_ftrace_function(&ops);

要禁用追踪，请调用::

    unregister_ftrace_function(&ops);

上述操作通过包含头文件定义::

    #include <linux/ftrace.h>

在调用 register_ftrace_function() 并返回之前，已注册的回调将在某个时间开始被调用。回调开始被调用的确切时间取决于架构和服务调度。如果回调必须在某一确切时刻开始，则回调本身需要处理任何同步问题。
unregister_ftrace_function() 将保证在返回后不再调用回调。请注意，为了保证这一点，unregister_ftrace_function() 可能需要一些时间才能完成。
回调函数
=====================

截至 v4.14，回调函数的原型如下：

```c
void callback_func(unsigned long ip, unsigned long parent_ip,
                   struct ftrace_ops *op, struct pt_regs *regs);
```

- `ip`
    这是被跟踪函数的指令指针（即 fentry 或 mcount 在函数中的位置）。
- `parent_ip`
    这是调用被跟踪函数的函数的指令指针（即函数调用发生的位置）。
- `op`
    这是指向用于注册回调的 ftrace_ops 结构体的指针。可以通过私有指针将数据传递给回调。
- `regs`
    如果在 ftrace_ops 结构体中设置了 FTRACE_OPS_FL_SAVE_REGS 或 FTRACE_OPS_FL_SAVE_REGS_IF_SUPPORTED 标志，则此指针指向的 pt_regs 结构体就像在函数开始处放置了一个断点一样。否则它要么包含垃圾数据，要么为 NULL。

保护你的回调函数
=====================

由于函数可以从任何地方被调用，并且被回调函数调用的函数也可能被跟踪并再次调用同一个回调函数，因此必须使用递归保护。有两个辅助函数可以帮助实现这一点。如果你从以下代码开始：

```c
int bit;

bit = ftrace_test_recursion_trylock(ip, parent_ip);
if (bit < 0)
    return;
```

并在结束时添加以下代码：

```c
ftrace_test_recursion_unlock(bit);
```

那么在这两段代码之间的部分将是安全的，即使它最终调用了回调正在跟踪的函数。注意，如果 ftrace_test_recursion_trylock() 成功，它会禁用抢占，并且 ftrace_test_recursion_unlock() 会再次启用抢占（如果之前已启用）。指令指针（ip）及其父指针（parent_ip）会被传递给 ftrace_test_recursion_trylock() 以记录递归发生的位置（如果 CONFIG_FTRACE_RECORD_RECURSION 被设置）。

或者，如果在 ftrace_ops 上设置了 FTRACE_OPS_FL_RECURSION 标志（如下面解释），则会使用一个辅助跳板来测试回调函数的递归，无需进行递归测试。但这需要额外的函数调用，增加了少许开销。

如果你的回调函数访问了任何需要 RCU 保护的数据或临界区，最好确保 RCU 正在“观察”，否则该数据或临界区将不会得到预期的保护。在这种情况下，可以添加以下代码：

```c
if (!rcu_is_watching())
    return;
```

或者，如果在 ftrace_ops 上设置了 FTRACE_OPS_FL_RCU 标志（如下面解释），则会使用一个辅助跳板来测试回调函数的 rcu_is_watching，无需进行其他测试。但这需要额外的函数调用，增加了少许开销。
ftrace FLAGS
============

ftrace_ops 标志全部在 `include/linux/ftrace.h` 中定义并进行了文档说明。有些标志用于 ftrace 的内部基础设施，但用户应该了解的标志如下：

FTRACE_OPS_FL_SAVE_REGS
如果回调函数需要读取或修改传递给回调函数的 `pt_regs`，则必须设置此标志。在一个不支持将 `pt_regs` 传递给回调函数的架构上注册带有此标志的 ftrace_ops 将会失败。

FTRACE_OPS_FL_SAVE_REGS_IF_SUPPORTED
与 `SAVE_REGS` 类似，但在一个不支持将寄存器传递给回调函数的架构上注册 ftrace_ops 不会因设置了此标志而失败。但是，回调函数必须检查 `regs` 是否为 NULL 以确定该架构是否支持它。

FTRACE_OPS_FL_RECURSION
默认情况下，期望回调函数能够处理递归。但如果回调函数不太关心开销，则可以设置此位，通过调用一个辅助函数来为回调函数添加递归保护，只有在没有发生递归时才会调用回调函数。
注意，如果未设置此标志，并且发生了递归，则可能会导致系统崩溃，并可能通过三重故障（triple fault）重启。
注意，如果设置了此标志，则回调函数将在禁止抢占的情况下始终被调用。如果没有设置此标志，则有可能（但不保证）在可抢占上下文中调用回调函数。

FTRACE_OPS_FL_IPMODIFY
需要设置 `FTRACE_OPS_FL_SAVE_REGS`。如果回调函数要“劫持”被跟踪的函数（即用另一个函数代替被跟踪的函数），则需要设置此标志。这是实时内核补丁所使用的功能。没有此标志，无法修改 `pt_regs->ip`。
注意，每次只能有一个带有 `FTRACE_OPS_FL_IPMODIFY` 标志的 ftrace_ops 注册到任何给定函数上。

FTRACE_OPS_FL_RCU
如果设置了此标志，则回调函数仅会被那些 RCU 正在“观察”的函数调用。如果回调函数执行了任何 `rcu_read_lock()` 操作，则此标志是必需的。
RCU在系统空闲时、CPU下线和重新上线时，以及从内核空间进入用户空间再返回内核空间时会停止监控。在这些转换过程中，可能会执行回调函数，而RCU同步机制不会保护这些回调。

`FTRACE_OPS_FL_PERMANENT`
如果任何ftrace操作设置了这个标志，则通过向proc sysctl的ftrace_enabled写入0来禁用跟踪是不可能的。同样地，如果ftrace_enabled为0，带有该标志的回调也不能被注册。
Livepatch使用这个标志以避免丢失函数重定向，从而保持系统的安全性。

选择要跟踪的函数
==================

如果回调仅在特定函数中调用，则必须设置过滤器。过滤器可以通过函数名或已知的ip地址来添加。
```c
int ftrace_set_filter(struct ftrace_ops *ops, unsigned char *buf,
                      int len, int reset);
```

- `@ops`：要设置过滤器的操作结构体
- `@buf`：包含函数过滤文本的字符串
- `@len`：字符串的长度
- `@reset`：非零值表示在应用此过滤器之前重置所有过滤器

过滤器指定了在启用跟踪时应启用哪些函数。如果`@buf`为NULL且`reset`被设置，则所有函数都将被启用以进行跟踪。`@buf`也可以是一个通配符表达式，以启用所有匹配特定模式的函数。
请参阅 :file:`Documentation/trace/ftrace.rst` 中的过滤命令。

仅跟踪调度函数：

```c
ret = ftrace_set_filter(&ops, "schedule", strlen("schedule"), 0);
```

要添加更多函数，可以多次调用 `ftrace_set_filter()` 并将 @reset 参数设置为零。要移除当前的过滤器集并替换为由 @buf 定义的新函数，请将 @reset 设置为非零值。

移除所有过滤的函数并跟踪所有函数：

```c
ret = ftrace_set_filter(&ops, NULL, 0, 1);
```

有时多个函数具有相同的名称。在这种情况下，可以使用 `ftrace_set_filter_ip()` 来仅跟踪特定函数：

```c
ret = ftrace_set_filter_ip(&ops, ip, 0, 0);
```

虽然 ip 必须是函数中调用 fentry 或 mcount 的位置地址。此函数被 perf 和 kprobes 使用，它们从用户那里获取 ip 地址（通常使用内核的调试信息）。

如果使用通配符来设置过滤器，则可以将函数添加到“notrace”列表中，以防止这些函数调用回调函数。“notrace”列表优先于“filter”列表。如果两个列表都不为空且包含相同的函数，则任何函数都不会调用回调函数。

空的“notrace”列表表示允许由过滤器定义的所有函数被跟踪：

```c
int ftrace_set_notrace(struct ftrace_ops *ops, unsigned char *buf,
                       int len, int reset);
```

这与 `ftrace_set_filter()` 接受相同的参数，但会将找到的函数添加到不进行跟踪的列表中。这是一个与过滤列表分开的列表，并且此函数不会修改过滤列表。

非零的 @reset 将在向其添加与 @buf 匹配的函数之前清除“notrace”列表。

清除“notrace”列表等同于清除过滤列表：

```c
ret = ftrace_set_notrace(&ops, NULL, 0, 1);
```

过滤列表和“notrace”列表可以在任何时候更改。如果只有一组函数应该调用回调函数，最好在注册回调之前设置过滤器。但在注册回调之后也可以进行更改。
如果设置了过滤器，并且 `@reset` 不为零，并且 `@buf` 包含与函数匹配的通配符，则在调用 `ftrace_set_filter()` 期间将发生切换。任何时候都不会有所有函数调用回调。

```c
ftrace_set_filter(&ops, "schedule", strlen("schedule"), 1);

register_ftrace_function(&ops);

msleep(10);

ftrace_set_filter(&ops, "try_to_wake_up", strlen("try_to_wake_up"), 1);
```

这与以下代码不同：

```c
ftrace_set_filter(&ops, "schedule", strlen("schedule"), 1);

register_ftrace_function(&ops);

msleep(10);

ftrace_set_filter(&ops, NULL, 0, 1);

ftrace_set_filter(&ops, "try_to_wake_up", strlen("try_to_wake_up"), 0);
```

因为后者在重置和新设置过滤器之间的一小段时间内，所有函数都会调用回调。
