### SPDX 许可证标识符：GPL-2.0

#### 内核入口

本文件记录了`arch/x86/entry/entry_64.S`中的一些内核入口。大部分解释改编自Ingo Molnar的一封邮件：

[https://lore.kernel.org/r/20110529191055.GC9835@elte.hu](https://lore.kernel.org/r/20110529191055.GC9835%40elte.hu)

x86架构有多种不同的方式跳转到内核代码。这些入口点大多在`arch/x86/kernel/traps.c`中注册，并且在64位的`arch/x86/entry/entry_64.S`、32位的`arch/x86/entry/entry_32.S`以及最终实现32位兼容系统调用入口点的`arch/x86/entry/entry_64_compat.S`中实现，后者为在64位内核上运行的32位进程提供了执行系统调用的能力。中断描述符表（IDT）向量分配列表可以在`arch/x86/include/asm/irq_vectors.h`中找到。

其中一些入口包括：

- `system_call`：来自64位代码的`syscall`指令。
- `entry_INT80_compat`：来自32位或64位代码的`int 0x80`；无论是哪种情况都是兼容的系统调用。
- `entry_INT80_compat`，`ia32_sysenter`：来自32位代码的`syscall`和`sysenter`。
- `interrupt`：一系列的入口。每个未明确指向其他地方的IDT向量都会设置为`interrupts`数组中的相应值。这些指向一系列神奇生成的函数，这些函数会带着中断编号到达`common_interrupt()`。
- `APIC 中断`：用于如TLB射杀等特殊目的的各种中断。
- 架构定义的异常，例如`divide_error`。

这里存在一些复杂性。不同的x86-64入口有不同的调用约定。`syscall`和`sysenter`指令有着它们自己独特的调用约定。一些IDT入口会在栈上推送一个错误码，而另一些则不会。使用IST备用堆栈机制的IDT入口需要自己的魔法来正确处理堆栈帧。（你可以在AMD APM第二卷第8章和Intel SDM第三卷第6章中找到一些文档。）

处理`swapgs`指令特别棘手。`swapgs`切换gs是内核gs还是用户gs。`swapgs`指令相当脆弱：它必须完美地嵌套并且仅嵌套一层，仅当从用户模式进入内核模式时才应该使用，并且在返回用户空间时也应如此。如果我们稍微弄错了这一点，就会导致崩溃。
因此，在我们已经处于内核模式的次级入口处，不能盲目地使用`SWAPGS`——也不能忘记在没有交换的情况下进行`SWAPGS`。
现在，存在一个次要的复杂性：有一种廉价的方式来检测CPU处于哪种模式，以及一种昂贵的方式。

廉价的方法是从内核栈上的入口帧中获取这些信息，具体从ptregs区域的CS值来判断：

```assembly
xorl %ebx,%ebx
testl $3,CS+8(%rsp)
je error_kernelspace
SWAPGS
```

昂贵（偏执）的方法是读回MSR_GS_BASE的值（这是SWAPGS所修改的）：

```assembly
movl $1,%ebx
movl $MSR_GS_BASE,%ecx
rdmsr
testl %edx,%edx
js 1f   /* 负数 -> 在内核空间 */
SWAPGS
xorl %ebx,%ebx
1: ret
```

如果我们处于中断或类似用户陷阱/门的边界，则可以使用更快的检查方法：栈将是一个可靠的指示器，以判断SWAPGS是否已经完成：如果我们发现我们是一个次级进入中断了内核模式执行，那么我们知道GS基地址已经被切换。如果它表明我们中断了用户空间的执行，那么我们必须执行SWAPGS。
但是，如果我们处于NMI/MCE/DEBUG/等等超级原子进入上下文中，这可能在正常进入将CS写入栈之后立即触发，但在我们执行SWAPGS之前，那么唯一安全的方式来检查GS是较慢的方法：RDMSR。
因此，超级原子进入（除了单独处理的NMI）必须使用带有paranoid=1的idtentry来正确处理gsbase。这触发了三种主要的行为变化：

- 中断进入将使用较慢的gsbase检查
- 从中断用户模式进入将关闭IST栈
- 从中断返回到内核模式不会尝试重新调度

我们尽量只对绝对需要更昂贵的GS基地址检查的向量使用IST入口和偏执的入口代码，并为所有“常规”的入口点生成常规（更快的）paranoid=0变体。
