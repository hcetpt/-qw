### 异常、中断、系统调用和KVM的进入/退出处理

所有执行域之间的转换都需要状态更新，这些更新受到严格的顺序约束。以下情况需要进行状态更新：

  * 锁依赖（Lockdep）
  * RCU / 上下文跟踪
  * 抢占计数器
  * 跟踪（Tracing）
  * 时间核算

更新顺序取决于转换类型，并在下面针对不同类型的转换部分中解释：`系统调用`_、`KVM`_、`中断和常规异常`_、`NMI和类似NMI的异常`_

#### 不可仪器化代码 - noinstr

大多数仪器化设施依赖于RCU，因此，在RCU开始监视之前的进入代码以及RCU停止监视之后的退出代码中禁止使用仪器化。此外，许多架构必须保存和恢复寄存器状态，这意味着例如，在断点进入代码中的一个断点会覆盖初始断点的调试寄存器。
这样的代码必须标记为'noinstr'属性，将该代码放置在一个特殊区域，该区域对仪器化和调试工具不可访问。一些函数可以部分地被仪器化，这可以通过标记它们为noinstr并在其中使用instrumentation_begin()和instrumentation_end()来标记可仪器化的代码范围来处理：

```c
noinstr void entry(void)
{
    handle_entry();     // <-- 必须是'noinstr'或'__always_inline'
    ..
instrumentation_begin();
    handle_context();   // <-- 可仪器化的代码
    instrumentation_end();

    ..
    handle_exit();      // <-- 必须是'noinstr'或'__always_inline'
}
```

这允许通过objtool在支持的架构上验证'noinstr'限制。
从可仪器化的上下文中调用不可仪器化的函数没有限制，这对于保护可能导致故障的状态切换等操作非常有用。

所有在RCU状态转换之前和之后的不可仪器化的进入/退出代码段必须在中断被禁用的情况下运行。

### 系统调用

系统调用的进入代码始于汇编代码，并在建立低级架构特定状态和栈帧后调用到低级C代码。此低级C代码不应被仪器化。从低级汇编代码调用的一个典型的系统调用处理函数如下所示：

```c
noinstr void syscall(struct pt_regs *regs, int nr)
{
    arch_syscall_enter(regs);
    nr = syscall_enter_from_user_mode(regs, nr);

    instrumentation_begin();
    if (!invoke_syscall(regs, nr) && nr != -1)
        result_reg(regs) = __sys_ni_syscall(regs);
    instrumentation_end();

    syscall_exit_to_user_mode(regs);
}
```

syscall_enter_from_user_mode()首先调用enter_from_user_mode()，它按以下顺序建立状态：

  * 锁依赖
  * RCU / 上下文跟踪
  * 跟踪

然后调用各种入口工作函数，如ptrace、seccomp、审计、系统调用跟踪等。完成所有这些之后，可以调用可仪器化的invoke_syscall函数。可仪器化的代码段结束后，调用syscall_exit_to_user_mode()。

syscall_exit_to_user_mode()处理返回用户空间前所需的所有工作，如跟踪、审计、信号、任务工作等。之后，它调用exit_to_user_mode()，后者再次按相反顺序处理状态转换：

  * 跟踪
  * RCU / 上下文跟踪
  * 锁依赖

syscall_enter_from_user_mode()和syscall_exit_to_user_mode()也作为细粒度子函数提供，以供架构代码在各个步骤之间需要做额外工作的场合使用。在这种情况下，它必须确保在进入时首先调用enter_from_user_mode()，并在退出时最后调用exit_to_user_mode()。

不要嵌套系统调用。嵌套系统调用会导致RCU和/或上下文跟踪打印警告信息。
进入或退出客户模式非常类似于系统调用。从主机内核的角度来看，当进入客户模式时，CPU进入用户空间；在退出时返回到内核。

`kvm_guest_enter_irqoff()` 是 `exit_to_user_mode()` 的KVM特定变体，而 `kvm_guest_exit_irqoff()` 是 `enter_from_user_mode()` 的KVM变体。状态操作具有相同的顺序性。

针对客户模式的任务处理工作是通过 `vcpu_run()` 循环边界上的 `xfer_to_guest_mode_handle_work()` 来单独完成的，这是返回用户空间时所处理工作的一部分。

不要嵌套KVM的进入/退出转换，因为这样做没有意义。

### 中断和常规异常

中断的进入与退出处理比系统调用和KVM转换稍微复杂一些。

- 如果在CPU执行用户空间代码时发生中断，则其进入和退出处理与系统调用完全相同。
- 如果中断在CPU执行内核空间代码时发生，则其进入与退出处理略有不同。RCU状态仅在中断在CPU空闲任务上下文中被触发时更新。否则，RCU已经在监视中。无论条件如何，都必须更新锁依赖性和跟踪。
- `irqentry_enter()` 和 `irqentry_exit()` 提供了实现这些功能的方法。

架构特定的部分看起来类似于系统调用处理：

```c
noinstr void interrupt(struct pt_regs *regs, int nr)
{
    arch_interrupt_enter(regs);
    state = irqentry_enter(regs);

    instrumentation_begin();

    irq_enter_rcu();
    invoke_irq_handler(regs, nr);
    irq_exit_rcu();

    instrumentation_end();

    irqentry_exit(regs, state);
}
```

请注意，实际中断处理器的调用是在 `irq_enter_rcu()` 和 `irq_exit_rcu()` 这对函数之间进行的。
`irq_enter_rcu()` 更新抢占计数，使得 `in_hardirq()` 返回 `true`，处理 NOHZ tick 状态和中断时间记账。这意味着在调用 `irq_enter_rcu()` 之前，`in_hardirq()` 返回 `false`。
`irq_exit_rcu()` 处理中断时间记账，撤销抢占计数的更新，并最终处理软中断和 NOHZ tick 状态。
理论上，可以在 `irqentry_enter()` 中更新抢占计数。实际上，将此更新推迟到 `irq_enter_rcu()` 允许跟踪抢占计数代码，同时保持与 `irq_exit_rcu()` 和 `irqentry_exit()` 的对称性，这些将在下一段中描述。唯一的缺点是，在 `irq_enter_rcu()` 之前的早期进入代码必须意识到抢占计数尚未使用 `HARDIRQ_OFFSET` 状态进行更新。
需要注意的是，`irq_exit_rcu()` 必须在处理软中断之前从抢占计数中移除 `HARDIRQ_OFFSET`，因为软中断处理器必须在 BH 上下文中运行，而不是在禁用中断的上下文中运行。此外，`irqentry_exit()` 可能会调度，这也需要 `HARDIRQ_OFFSET` 已从抢占计数中移除。

尽管通常期望中断处理器在禁用本地中断的情况下运行，但从入口/出口的角度来看，中断嵌套很常见。例如，软中断处理发生在启用本地中断的 `irqentry_{enter,exit}()` 块内。虽然不常见，但没有阻止中断处理器重新启用中断的限制。

中断入口/出口代码不必严格处理重入，因为它在禁用本地中断的情况下运行。但是 NMIs 可以随时发生，而且很多入口代码在这两者之间共享。

### NMI 和类似 NMI 的异常

NMIs 和类似 NMI 的异常（机器检查、双重故障、调试中断等）可以击中任何上下文，并且必须格外小心地处理状态。
对于调试异常和机器检查异常的状态变化取决于这些异常是否发生在用户空间（断点或监视点）还是内核模式（代码修补）。从用户空间来看，它们被视为中断；而从内核模式来看，则被视为 NMIs。
NMIs 和其他类似 NMI 的异常处理状态转换时不会区分用户模式和内核模式来源。
入口时的状态更新由 `irqentry_nmi_enter()` 处理，其按以下顺序更新状态：

1. 抢占计数
2. 锁依赖性
3. RCU / 上下文追踪
4. 跟踪

对应的出口操作 `irqentry_nmi_exit()` 按相反的顺序执行逆向操作。
请注意，抢占计数器的更新必须是在进入时的第一个操作和退出时的最后一个操作。原因在于lockdep和RCU都依赖于在这种情况下`in_nmi()`返回真。在NMI进入/退出情况下的抢占计数修改不能被跟踪。
特定架构的代码看起来像这样：

```c
noinstr void nmi(struct pt_regs *regs)
{
	arch_nmi_enter(regs);
	state = irqentry_nmi_enter(regs);

	instrumentation_begin();
	nmi_handler(regs);
	instrumentation_end();

	irqentry_nmi_exit(regs);
}
```

而对于例如调试异常，它可以看起来像这样：

```c
noinstr void debug(struct pt_regs *regs)
{
	arch_nmi_enter(regs);

	debug_regs = save_debug_regs();

	if (user_mode(regs)) {
		state = irqentry_enter(regs);

		instrumentation_begin();
		user_mode_debug_handler(regs, debug_regs);
		instrumentation_end();

		irqentry_exit(regs, state);
	} else {
		state = irqentry_nmi_enter(regs);

		instrumentation_begin();
		kernel_mode_debug_handler(regs, debug_regs);
		instrumentation_end();

		irqentry_nmi_exit(regs, state);
	}
}
```

没有提供一个组合的`irqentry_nmi_if_kernel()`函数，因为上述情况无法以一种与异常无关的方式处理。
NMI可以在任何上下文中发生。例如，在处理NMI时触发的一个类似NMI的异常。因此，NMI入口代码必须是可重入的，并且状态更新需要处理嵌套的情况。
