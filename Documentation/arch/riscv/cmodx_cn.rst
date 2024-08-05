### SPDX 许可证标识符：GPL-2.0

==============================================================================
RISC-V Linux 中的指令并发修改与执行 (CMODX)
==============================================================================

CMODX 是一种编程技术，其中程序执行自身修改过的指令。在 RISC-V 硬件上，指令存储和指令缓存（icache）之间不能保证同步。因此，程序必须使用非特权 `fence.i` 指令自行强制同步。然而，默认的 Linux ABI 禁止用户空间应用程序中使用 `fence.i`。在任何时刻，调度器都可能将一个任务迁移到一个新的 hart 上。如果迁移发生在用户空间通过 `fence.i` 同步了 icache 和指令存储之后，新 hart 上的 icache 将不再干净。这是由于 `fence.i` 只会影响调用它的 hart。因此，任务迁移到的新 hart 可能没有同步指令存储和 icache。

解决此问题有两种方法：使用 `riscv_flush_icache()` 系统调用或使用 `PR_RISCV_SET_ICACHE_FLUSH_CTX` prctl() 并在用户空间发出 `fence.i`。系统调用执行一次性 icache 刷新操作。prctl 改变 Linux ABI，允许用户空间发出 icache 刷新操作。

顺便说一下，“延迟” icache 刷新有时可以在内核中触发。截至本文撰写时，这仅发生在 `riscv_flush_icache()` 系统调用期间和内核使用 `copy_to_user_page()` 时。这些延迟刷新只会在 hart 使用的内存映射发生变化时发生。如果 prctl() 的上下文导致 icache 刷新，则此延迟 icache 刷新将被跳过，因为它是冗余的。因此，在 prctl() 上下文中使用 `riscv_flush_icache()` 系统调用时，不会产生额外的刷新。

#### prctl() 接口
---------------------

使用 `PR_RISCV_SET_ICACHE_FLUSH_CTX` 作为第一个参数调用 prctl()。其余参数将被委托给下面详细描述的 `riscv_set_icache_flush_ctx` 函数。
.. kernel-doc:: arch/riscv/mm/cacheflush.c
	:identifiers: riscv_set_icache_flush_ctx

#### 示例用法：

以下文件旨在相互编译和链接。`modify_instruction()` 函数将带有 0 的加法替换为带有 1 的加法，使 `get_value()` 中的指令序列从返回零变为返回一。
cmodx.c::

	```c
	#include <stdio.h>
	#include <sys/prctl.h>

	extern int get_value();
	extern void modify_instruction();

	int main()
	{
		int value = get_value();
		printf("修改前的值: %d\n", value);

		// 在 modify_instruction 内部第一次调用 fence.i 之前调用 prctl
		prctl(PR_RISCV_SET_ICACHE_FLUSH_CTX, PR_RISCV_CTX_SW_FENCEI_ON, PR_RISCV_SCOPE_PER_PROCESS);
		modify_instruction();
		// 在进程内部最后一次调用 fence.i 之后调用 prctl
		prctl(PR_RISCV_SET_ICACHE_FLUSH_CTX, PR_RISCV_CTX_SW_FENCEI_OFF, PR_RISCV_SCOPE_PER_PROCESS);

		value = get_value();
		printf("修改后的值: %d\n", value);
		return 0;
	}
	```

cmodx.S::

	```assembly
	.option norvc

	.text
	.global modify_instruction
	modify_instruction:
	lw a0, new_insn
	lui a5,%hi(old_insn)
	sw  a0,%lo(old_insn)(a5)
	fence.i
	ret

	.section modifiable, "awx"
	.global get_value
	get_value:
	li a0, 0
	old_insn:
	addi a0, a0, 0
	ret

	.data
	new_insn:
	addi a0, a0, 1
	```
