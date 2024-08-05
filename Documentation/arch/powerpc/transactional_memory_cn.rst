事务内存支持
============================

对于此特性的 POWER 内核支持目前仅限于支持用户程序使用。内核本身当前并未使用这一特性。本文件旨在总结 Linux 如何支持它以及您可以从用户程序中期待何种行为。

基本概述
==============

硬件事务内存（Hardware Transactional Memory）在 POWER8 处理器上得到支持，它是一种启用不同形式原子内存访问的特性。提供了一些新的指令来界定事务；事务保证要么原子完成，要么回滚并撤销任何部分更改。

一个简单的事务如下所示：

```
begin_move_money:
    tbegin
    beq   abort_handler

    ld    r4, SAVINGS_ACCT(r3)
    ld    r5, CURRENT_ACCT(r3)
    subi  r5, r5, 1
    addi  r4, r4, 1
    std   r4, SAVINGS_ACCT(r3)
    std   r5, CURRENT_ACCT(r3)

    tend

    b     continue

  abort_handler:
    ... 测试异常失败 ...
/* 如果事务因与他人冲突而失败，则重试该事务：*/
    b     begin_move_money
```

`tbegin` 指令表示起始点，`tend` 表示结束点。在这两点之间，处理器处于“事务”状态；只要没有与其他系统中的事务性或非事务性访问发生冲突，所有内存引用都将一次性完成。在这个例子中，如果没有任何其他处理器访问了 `SAVINGS_ACCT(r3)` 或 `CURRENT_ACCT(r3)`，那么事务将像正常直线代码一样完成；一次原子操作将资金从当前账户转移到储蓄账户。尽管使用了普通的 `ld/std` 指令（请注意没有 `lwarx/stwcx`），但 `SAVINGS_ACCT(r3)` 和 `CURRENT_ACCT(r3)` 要么同时更新，要么都不更新。

如果在此期间事务访问的位置发生了冲突，CPU 将终止事务。寄存器和内存状态将回滚到 `tbegin` 处的状态，并且控制将从 `tbegin+4` 继续。第二次时将跳转到 `abort_handler`；中止处理程序可以检查失败的原因，并尝试重试。

被检查点化的寄存器包括所有的 GPRs、FPRs、VRs/VSRs、LR、CCR/CR、CTR、FPCSR 以及其他一些状态/标志寄存器；具体细节请参阅 ISA 文档。

事务中止原因
============================

- 与其他处理器使用的缓存行冲突
- 信号
- 上下文切换
- 有关会导致事务中止的所有情况，请参阅 ISA 文档以获取完整文档

系统调用
========

在活动事务中进行的系统调用不会执行，内核会以失败码 `TM_CAUSE_SYSCALL | TM_CAUSE_PERSISTENT` 中止该事务。
从挂起的事务内部发起的系统调用会像平常一样执行，内核并不会明确地将该事务标记为失败。然而，内核为了执行系统调用所做的事情可能导致硬件将该事务标记为失败。系统调用在挂起模式下执行，因此任何副作用都会是持久的，与事务的成功或失败无关。内核不对哪些系统调用会影响事务成功提供任何保证。
在活动事务中依赖通过库函数发起的系统调用来中止事务时必须小心。库函数可能会缓存值（这可能给人一种成功的假象）或执行导致事务在进入内核之前就失败的操作（这可能导致不同的失败代码）。例如glibc中的`getpid()`和懒惰符号解析。
信号
======
在事务期间传递信号（无论是同步还是异步）提供了第二个线程状态（ucontext/mcontext），以表示第二个事务性寄存器状态。信号传递的`treclaim`捕获了两个寄存器状态，因此信号会中止事务。通常传递给信号处理程序的ucontext_t代表了检查点/原始寄存器状态；信号看起来是在`tbegin+4`处出现的。
如果信号处理程序的ucontext结构体中的uc_link被设置，则已传递了第二个ucontext。为了未来的兼容性，应该检查MSR.TS字段来确定事务性状态——如果是这样，那么ucontext结构体uc->uc_link中的第二个ucontext代表了在信号发生时活跃的事务性寄存器状态。
对于64位进程，uc->uc_mcontext.regs->msr是一个完整的64位MSR，其TS字段显示了事务模式。
对于32位进程，mcontext的MSR寄存器只有32位；最上面的32位存储在第二个ucontext的MSR中，即在uc->uc_link->uc_mcontext.regs->msr中。最高字包含了事务状态TS。
但是，基本的信号处理程序不需要了解事务，并且简单地从处理程序返回就能正确处理事务：

事务感知型信号处理程序可以从第二个ucontext读取事务性寄存器状态。这对于崩溃处理程序来说是必要的，例如，确定导致SIGSEGV的指令地址。
示例信号处理程序如下：

```c
void crash_handler(int sig, siginfo_t *si, void *uc)
{
  ucontext_t *ucp = uc;
  ucontext_t *transactional_ucp = ucp->uc_link;

  if (ucp->uc_link) {
    u64 msr = ucp->uc_mcontext.regs->msr;
    /* 可能有事务性ucontext！ */
#ifndef __powerpc64__
    msr |= ((u64)transactional_ucp->uc_mcontext.regs->msr) << 32;
#endif
    if (MSR_TM_ACTIVE(msr)) {
       /* 是的，我们在一个事务中崩溃了。哎呀。 */
   fprintf(stderr, "需要重启的事务位于0x%llx，但引发崩溃的指令位于0x%llx\n",
                           ucp->uc_mcontext.regs->nip,
                           transactional_ucp->uc_mcontext.regs->nip);
    }
  }

  fix_the_problem(ucp->dar);
}
```

在活动事务中接收到信号时，我们需要小心处理栈。有可能栈在tbegin之后又回退了。
最明显的情况是在一个函数内部调用了tbegin，而这个函数在tend之前就返回了。在这种情况下，栈是检查点事务性内存状态的一部分。如果我们非事务性地或在挂起状态下覆盖这部分栈，就会有问题，因为如果我们收到一个事务中止信号，程序计数器和栈指针将会回到tbegin的位置，但我们内存中的栈将不再有效。
为了避免这种情况，在活跃的事务中接收信号时，我们需要使用检查点状态的栈指针，而不是推测状态的栈指针。这确保了信号上下文（在挂起时写入）将被写入到回滚所需的栈之下。由于触发了内存回收，所以从`tbegin`到接收到信号之间写入的任何内存都会被回滚。
对于非事务内存或挂起模式下接收的信号，我们使用正常的/非检查点的栈指针。
在信号处理程序内发起并在返回内核时被挂起的任何事务都将被回收并丢弃。

### 内核使用的失败原因代码
这些定义在 `<asm/reg.h>` 中，并区分了内核中止一个事务的不同原因：

| 原因代码 | 描述 |
| --- | --- |
| `TM_CAUSE_RESCHED` | 线程被重新调度 |
| `TM_CAUSE_TLBI` | 软件TLB无效化 |
| `TM_CAUSE_FAC_UNAV` | 浮点/向量/VSX不可用陷阱 |
| `TM_CAUSE_SYSCALL` | 活跃事务中的系统调用 |
| `TM_CAUSE_SIGNAL` | 发送信号 |
| `TM_CAUSE_MISC` | 目前未使用 |
| `TM_CAUSE_ALIGNMENT` | 对齐错误 |
### TM_CAUSE_EMULATE       触及内存的模拟

这些可以在用户程序的中止处理程序中作为TEXASR[0:7]进行检查。如果第7位被设置，表示该错误被视为持续性的。例如，TM_CAUSE_ALIGNMENT 将是持续性的，而 TM_CAUSE_RESCHED 则不是。
### GDB

目前 GDB 和 ptrace 并不支持事务内存（TM）功能。如果在事务执行期间停止，则看起来事务刚刚开始（呈现的是检查点状态）。之后无法继续该事务，并将采用失败处理路径。此外，事务中的第二个寄存器状态将无法访问。目前可以在使用 TM 的程序上使用 GDB，但在事务内的部分则无法合理使用。
### POWER9

POWER9 上的 TM 存在存储完整寄存器状态的问题。这一问题在以下提交中有描述：

```
commit 4bb3c7a0208fc13ca70598efd109901a7cd45ae7  
Author: Paul Mackerras <paulus@ozlabs.org>  
Date:   Wed Mar 21 21:32:01 2018 +1100  
KVM: PPC: Book3S HV: 绕过 POWER9 中的事务内存缺陷
```

为了应对这个问题，不同的 POWER9 芯片以不同方式启用 TM：
- 在 POWER9N DD2.01 及以下版本中，TM 被禁用。即 HWCAP2[PPC_FEATURE2_HTM] 未被设置。
- 在 POWER9N DD2.1 中，固件配置 TM 总是在发生 tm 暂停时终止事务。因此，tsuspend 将导致事务被终止并回滚。内核异常也将导致事务终止和回滚，并且异常不会发生。如果用户空间构造了一个启用 TM 暂停的 sigcontext，则该 sigcontext 将被内核拒绝。此模式通过设置 HWCAP2[PPC_FEATURE2_HTM_NO_SUSPEND] 向用户宣传，而 HWCAP2[PPC_FEATURE2_HTM] 在此模式下未被设置。
- 在 POWER9N DD2.2 及以上版本中，KVM 和 POWERVM 为来宾模拟 TM（如提交 4bb3c7a0208f 所述），因此来宾启用 TM，即 HWCAP2[PPC_FEATURE2_HTM] 对于来宾用户空间已设置。大量使用 TM 暂停（tsuspend 或内核暂停）的来宾会导致进入虚拟机监视器的陷阱，从而导致性能下降。主机用户空间禁用了 TM，即 HWCAP2[PPC_FEATURE2_HTM] 未被设置。（虽然我们可能会在未来某个时候在主机用户空间上下文切换中实现这种模拟）
- POWER9C DD1.2 及以上版本仅与 POWERVM 配合使用，因此 Linux 仅作为来宾运行。在这些系统上，TM 的模拟方式类似于 POWER9N DD2.2。
- 从 POWER8 迁移到 POWER9 将在 POWER9N DD2.2 和 POWER9C DD1.2 上工作。由于早期的 POWER9 处理器不支持 TM 模拟，因此不支持从 POWER8 到这些 POWER9 处理器的迁移。
### 内核实现
#### h/rfid mtmsrd 特性

根据ISA的定义，rfid具有一种在早期异常处理中非常有用的特点。当处于用户空间事务中并通过某种异常进入内核时，MSR最终会变成TM=0和TS=01（即TM关闭但TM挂起）。通常情况下，内核需要更改MSR中的某些位，并通过执行rfid来实现这一点。在这种情况下，rfid可以使SRR0的TM=0和TS=00（即TM关闭且非事务性），而结果MSR将保留之前TM=0和TS=01的状态（即保持挂起状态）。这是架构上的一个特性，因为这通常是一个从TS=01到TS=00的转换（即从挂起到非事务性），这是一个非法的转换。
该特性在rfid的定义中被描述为：

  如果 (MSR 29:31 ≠ 0b010 | SRR1 29:31 ≠ 0b000)，则
     MSR 29:31 <- SRR1 29:31

hrfid和mtmsrd具有相同的特点。
Linux内核在其早期异常处理中利用了这一特点。
