======================
函数追踪器设计
======================

:作者: Mike Frysinger

.. 注意::
    本文档已过时。下面的一些描述与当前实现不匹配。

简介
------------

在这里，我们将介绍公共函数追踪代码所依赖的架构组件，以确保其正常工作。内容将逐步递增复杂度，以便您可以从简单的开始，并至少获得基本功能。请注意，这里仅关注架构实现细节。如果您希望了解更详细的特性说明，请参阅common ftrace.txt文件。
理想情况下，所有希望在内核中支持追踪同时保持性能的人都应实现动态ftrace支持。

前提条件
------------

Ftrace依赖于以下功能的实现：
  - STACKTRACE_SUPPORT - 实现save_stack_trace()
  - TRACE_IRQFLAGS_SUPPORT - 实现include/asm/irqflags.h

HAVE_FUNCTION_TRACER
--------------------

您需要实现mcount和ftrace_stub函数
确切的mcount符号名称取决于您的工具链。有些称为"mcount"，"_mcount"，甚至是"__mcount"。您可以通过运行类似下面的命令来找出具体名称：

	$ echo 'main(){}' | gcc -x c -S -o - - -pg | grep mcount
	        call    mcount

我们假设符号为"mcount"，以便在示例中保持简单明了。
请记住，在mcount函数内部生效的ABI是高度架构/工具链特定的。在这方面我们无法提供帮助，抱歉。请查阅一些旧文档或找一个比您熟悉的人讨论。通常，寄存器使用（参数/临时等）在此阶段是一个主要问题，特别是关于mcount调用的位置（函数前导/后置）。您可能也想看看glibc是如何为您的架构实现mcount函数的，这可能是（半）相关的。
mcount函数应该检查函数指针ftrace_trace_function是否被设置为ftrace_stub。如果设置了，则无需做任何事情，立即返回。如果没有设置，则以相同的方式调用该函数，就像mcount函数通常调用__mcount_internal一样——第一个参数是从哪个地址返回（frompc），第二个参数是调整后的返回地址（selfpc）（去除了嵌入函数中的mcount调用大小）。
例如，如果函数foo()调用了bar()，当bar()函数调用mcount()时，mcount()传递给追踪器的参数如下：

  - "frompc" - bar()用于返回到foo()的地址
  - "selfpc" - bar()的地址（进行mcount大小调整）

此外，请记住这个mcount函数会被大量调用，因此优化默认无追踪的情况有助于在禁用追踪时系统的顺畅运行。因此，mcount函数的开始通常是检查后立即返回的最小化处理。这也意味着代码流通常应保持线性（即在nop情况下没有分支）。当然这是优化建议而非硬性要求。
以下是伪代码，可以帮助理解（这些函数实际上应在汇编语言中实现）：

	void ftrace_stub(void)
	{
		return;
	}

	void mcount(void)
	{
		/* 保存初始检查所需的任何基本状态 */

		extern void (*ftrace_trace_function)(unsigned long, unsigned long);
		if (ftrace_trace_function != ftrace_stub)
			goto do_trace;

		/* 恢复任何基本状态 */

		return;

	do_trace:

		/* 保存ABI所需的全部状态（参见上段文字） */

		unsigned long frompc = ...;
		unsigned long selfpc = <返回地址> - MCOUNT_INSN_SIZE;
		ftrace_trace_function(frompc, selfpc);

		/* 恢复ABI所需的所有状态 */
	}

别忘了为模块导出mcount！

	extern void mcount(void);
	EXPORT_SYMBOL(mcount);

HAVE_FUNCTION_GRAPH_TRACER
--------------------------

深呼吸……是时候做一些实际的工作了。在这里，您需要更新mcount函数以检查ftrace图函数指针，并且实现一些函数来保存（劫持）并恢复返回地址。
mcount 函数应该检查函数指针 ftrace_graph_return（与 ftrace_stub 比较）和 ftrace_graph_entry（与 ftrace_graph_entry_stub 比较）。如果这两个中的任何一个没有设置为相关的 stub 函数，则应调用特定于架构的函数 ftrace_graph_caller，该函数反过来调用特定于架构的函数 prepare_ftrace_return。这些函数名称严格来说不是必需的，但为了在架构端口之间保持一致性——便于比较和对比，你应该使用它们。

传递给 prepare_ftrace_return 的参数与传递给 ftrace_trace_function 的参数略有不同。第二个参数 "selfpc" 是相同的，但第一个参数应该是指向 "frompc" 的指针。通常这位于栈上。这使得函数可以暂时劫持返回地址，使其指向特定于架构的函数 return_to_handler。该函数将简单地调用通用函数 ftrace_return_to_handler，然后该函数会返回原始返回地址，这样你可以返回到原始调用点。

以下是更新后的 mcount 伪代码：

```c
void mcount(void)
{
    ..
    if (ftrace_trace_function != ftrace_stub)
        goto do_trace;

    #ifdef CONFIG_FUNCTION_GRAPH_TRACER
    extern void (*ftrace_graph_return)(...);
    extern void (*ftrace_graph_entry)(...);
    if (ftrace_graph_return != ftrace_stub ||
        ftrace_graph_entry != ftrace_graph_entry_stub)
        ftrace_graph_caller();
    #endif

    /* 恢复任何裸状态 */
    ..
}
```

以下是新的 ftrace_graph_caller 组装函数的伪代码：

```c
#ifdef CONFIG_FUNCTION_GRAPH_TRACER
void ftrace_graph_caller(void)
{
    /* 保存 ABI 所需的所有状态 */

    unsigned long *frompc = &...;
    unsigned long selfpc = <return address> - MCOUNT_INSN_SIZE;
    /* 传递帧指针是可选的 —— 见下文 */
    prepare_ftrace_return(frompc, selfpc, frame_pointer);

    /* 恢复 ABI 所需的所有状态 */
}
#endif
```

关于如何实现 prepare_ftrace_return()，只需查看 x86 版本即可（传递帧指针是可选的；更多信息请参见下一节）。其中唯一特定于架构的部分是故障恢复表的设置（asm(...) 代码）。其余部分在各架构中应该是相同的。

以下是新的 return_to_handler 组装函数的伪代码。请注意，此处适用的 ABI 与 mcount 代码适用的不同。由于你是在一个函数（尾声之后）返回，你可能可以省略一些保存/恢复的内容（通常是用于传递返回值的寄存器）：

```c
#ifdef CONFIG_FUNCTION_GRAPH_TRACER
void return_to_handler(void)
{
    /* 保存 ABI 所需的所有状态（见上面的段落） */

    void (*original_return_point)(void) = ftrace_return_to_handler();

    /* 恢复 ABI 所需的所有状态 */

    /* 这通常是一个返回或跳转 */
    original_return_point();
}
#endif
```

### HAVE_FUNCTION_GRAPH_FP_TEST
---------------------------

一个架构可以在进入和退出函数时传递一个唯一的值（帧指针）。在退出时，如果该值不匹配，则会使内核崩溃。这主要是对 gcc 生成不良代码的一种合理性检查。如果你的端口在不同的优化级别下 gcc 合理地更新了帧指针，则可以忽略此选项。
然而，支持它并不特别困难。在调用 prepare_ftrace_return() 的汇编代码中，将帧指针作为第三个参数传递。然后，在该函数的 C 版本中，像 x86 端口那样将其传递给 ftrace_push_return_trace() 而不是 0 的 stub 值。
同样地，当你调用 `ftrace_return_to_handler()` 时，传递给它帧指针。

HAVE_SYSCALL_TRACEPOINTS
------------------------
要在一个架构中实现系统调用跟踪，你需要很少的几项内容：
- 支持 `HAVE_ARCH_TRACEHOOK`（参见 `arch/Kconfig`）
- 在 `<asm/unistd.h>` 中有一个 `NR_syscalls` 变量，提供该架构支持的系统调用的数量
- 支持 `TIF_SYSCALL_TRACEPOINT` 线程标志
- 将来自 `ptrace` 的 `trace_sys_enter()` 和 `trace_sys_exit()` 跟踪点调用放在 `ptrace` 系统调用跟踪路径中
- 如果此架构上的系统调用表比一个简单的系统调用地址数组更复杂，则实现 `arch_syscall_addr` 以返回特定系统调用的地址
- 如果系统调用的符号名称与该架构上的函数名称不匹配，则在 `<asm/ftrace.h>` 中定义 `ARCH_HAS_SYSCALL_MATCH_SYM_NAME` 并实现 `arch_syscall_match_sym_name`，使用适当的逻辑返回函数名称是否对应于符号名称
- 标记此架构为 `HAVE_SYSCALL_TRACEPOINTS`

HAVE_FTRACE_MCOUNT_RECORD
-------------------------
更多信息请参见 `scripts/recordmcount.pl`。只需填写架构特定的详细信息，说明如何通过 `objdump` 定位 `mcount` 调用站点的地址。
此选项在未实现动态ftrace的情况下意义不大
HAVE_DYNAMIC_FTRACE
-------------------

首先，你需要 `HAVE_FTRACE_MCOUNT_RECORD` 和 `HAVE_FUNCTION_TRACER`，如果你之前过于急切，请返回去查看相关信息。
一旦这些都处理完毕，你需要实现以下内容：
- asm/ftrace.h:
    - MCOUNT_ADDR
    - ftrace_call_adjust()
    - struct dyn_arch_ftrace{}
- asm代码:
    - mcount()（新的存根）
    - ftrace_caller()
    - ftrace_call()
    - ftrace_stub()
- C代码:
    - ftrace_dyn_arch_init()
    - ftrace_make_nop()
    - ftrace_make_call()
    - ftrace_update_ftrace_func()

首先，你需要在你的 asm/ftrace.h 中填写一些架构细节。定义 MCOUNT_ADDR 为你的 mcount 符号地址，如下所示：

    #define MCOUNT_ADDR ((unsigned long)mcount)

由于其他人没有这个函数的声明，你需要这样定义：

    extern void mcount(void);

你还需要辅助函数 ftrace_call_adjust()。大多数人可以这样实现：

    static inline unsigned long ftrace_call_adjust(unsigned long addr)
    {
        return addr;
    }

<待填充详情>

最后，你需要自定义的 dyn_arch_ftrace 结构体。如果在运行时修补任意调用点时需要额外的状态信息，这里就是地方。不过现在，创建一个空结构体：

    struct dyn_arch_ftrace {
        /* 不需要额外数据 */
    };

有了头文件之后，我们可以填充汇编代码了。虽然我们之前已经创建了一个 mcount() 函数，但动态 ftrace 只需要一个存根函数。这是因为 mcount() 只会在启动期间使用，然后所有对它的引用将被修补掉，永远不会再返回。相反，旧 mcount() 的核心部分将用于创建一个新的 ftrace_caller() 函数。由于两者难以合并，很可能最好分别定义两个版本，并通过 #ifdef 分开。同样地，ftrace_stub() 现在将内联到 ftrace_caller() 中。

为了避免进一步混淆，让我们看一下伪代码，以便你可以用汇编实现自己的东西：

    void mcount(void)
    {
        return;
    }

    void ftrace_caller(void)
    {
        /* 保存 ABI 需要的所有状态（参见上面的段落） */

        unsigned long frompc = ...;
        unsigned long selfpc = <return address> - MCOUNT_INSN_SIZE;

    ftrace_call:
        ftrace_stub(frompc, selfpc);

        /* 恢复 ABI 需要的所有状态 */

    ftrace_stub:
        return;
    }

这看起来可能有点奇怪，但请记住，我们将进行多次运行时修补。首先，只有我们实际想要跟踪的函数才会被修补为调用 ftrace_caller()。其次，由于一次只有一个跟踪器处于活动状态，我们将修补 ftrace_caller() 函数本身以调用特定的跟踪器。这就是 ftrace_call 标签的作用。

考虑到这一点，让我们继续进行实际执行运行时修补的 C 代码。你需要一些关于你的架构操作码的知识才能通过下一节。

每个架构都有一个初始化回调函数。如果你需要在早期做一些事情来初始化某些状态，这是时候了。否则，下面这个简单的函数应该对大多数人来说足够了：

    int __init ftrace_dyn_arch_init(void)
    {
        return 0;
    }

有两个函数用于运行时修补任意函数。第一个用于将 mcount 调用点转换为 nop（这有助于我们在不进行跟踪时保持运行时性能）。第二个用于将 mcount 谽用点转换为对任意位置的调用（但通常是 ftracer_caller()）。请参见 linux/ftrace.h 中的函数定义：

    ftrace_make_nop()
    ftrace_make_call()

rec->ip 值是在构建时间由 scripts/recordmcount.pl 收集的 mcount 调用点的地址。

最后一个函数用于修补活动跟踪器。这将修改位于 ftrace_caller() 函数中的 ftrace_call 符号处的汇编代码。因此，你应该在此位置有足够的填充空间来支持你将插入的新函数调用。有些人将使用“调用”类型指令，而另一些人将使用“分支”类型指令。具体而言，该函数是：

    ftrace_update_ftrace_func()

HAVE_DYNAMIC_FTRACE + HAVE_FUNCTION_GRAPH_TRACER
------------------------------------------------

函数图跟踪器需要进行一些调整才能与动态 ftrace 一起工作。基本上，你需要做以下几件事：

- 更新：
    - ftrace_caller()
    - ftrace_graph_call()
    - ftrace_graph_caller()
- 实现：
    - ftrace_enable_ftrace_graph_caller()
    - ftrace_disable_ftrace_graph_caller()

<待填充详情>

注意事项：

- 在 ftrace_call 位置后添加一个 nop 存根，命名为 ftrace_graph_call；存根需要足够大以支持调用 ftrace_graph_caller()
- 更新 ftrace_graph_caller() 以适应新 ftrace_caller() 的调用，因为某些语义可能已改变
- ftrace_enable_ftrace_graph_caller() 将运行时修补 ftrace_graph_call 位置以调用 ftrace_graph_caller()
- ftrace_disable_ftrace_graph_caller() 将运行时修补 ftrace_graph_call 位置以调用 nop
