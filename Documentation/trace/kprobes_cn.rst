=======================
内核探针（Kprobes）
=======================

:作者: Jim Keniston <jkenisto@us.ibm.com>
:作者: Prasanna S Panchamukhi <prasanna.panchamukhi@gmail.com>
:作者: Masami Hiramatsu <mhiramat@kernel.org>

.. 目录

  1. 概念：Kprobes 和 返回探针
  2. 支持的架构
  3. 配置 Kprobes
  4. API 参考
  5. Kprobes 功能和限制
  6. 探针开销
  7. 待办事项
  8. Kprobes 示例
  9. Kretprobes 示例
  10. 已弃用的功能
  附录 A: Kprobes 的 debugfs 接口
  附录 B: Kprobes 的 sysctl 接口
  附录 C: 参考资料

概念：Kprobes 和 返回探针
=========================================

Kprobes 允许您动态地进入任何内核例程，并非破坏性地收集调试和性能信息。您可以在几乎任何内核代码地址处设置断点 [1]，指定一个在断点命中时调用的处理程序。
.. [1] 内核的某些部分无法设置断点，请参阅 :ref:`kprobes_blacklist`

目前有两种类型的探针：Kprobes 和 Kretprobes（也称为返回探针）。Kprobe 可以插入到内核中的几乎所有指令上。当指定函数返回时，返回探针会被触发。
通常情况下，基于 Kprobes 的工具化被封装为一个内核模块。该模块的初始化函数安装（“注册”）一个或多个探针，而退出函数则取消注册它们。注册函数如 register_kprobe() 指定了探针的插入位置以及探针命中时应调用的处理程序。
还有用于批量注册/取消注册一组探针的 `register_/unregister_*probes()` 函数。当需要一次取消注册大量探针时，这些函数可以加快取消注册过程。
接下来的四个小节解释了不同类型的探针是如何工作的，以及跳转优化是如何进行的。它们解释了一些为了更好地使用 Kprobes 所需了解的内容——例如 pre_handler 和 post_handler 之间的区别，以及如何使用 kretprobe 的 maxactive 和 nmissed 字段。但如果您急于开始使用 Kprobes，您可以直接跳到 :ref:`kprobes_archs_supported`。
Kprobe 如何工作？
-----------------------

当一个 kprobe 被注册时，Kprobes 会复制被探测的指令，并用断点指令（例如，在 i386 和 x86_64 上是 int3）替换被探测指令的第一个字节。
当 CPU 遇到断点指令时，会发生陷阱，CPU 的寄存器将被保存，控制权通过 notifier_call_chain 机制传递给 Kprobes。Kprobes 执行与 kprobe 关联的 “pre_handler”，并将 kprobe 结构和保存的寄存器地址传递给处理程序。
接下来，Kprobes 单步执行其复制的被探测指令。（如果直接单步执行实际的指令，那么 Kprobes 将不得不暂时移除断点指令。这会在一小段时间内打开一个窗口，使得另一个 CPU 可能直接越过探针点。）
在指令单步执行之后，Kprobes 执行与 kprobe 关联的 “post_handler”（如果有）。
然后继续执行探针点后面的指令。
更改执行路径
-----------------------

由于 kprobes 可以探测正在运行的内核代码，因此它可以更改寄存器集，包括指令指针。这种操作需要极其小心，比如保持栈帧、恢复执行路径等。由于它是在运行中的内核上进行操作，并且需要对计算机架构和并发计算有深入的理解，很容易导致错误。
如果你在 `pre_handler` 中更改了指令指针（并设置了其他相关寄存器），则必须返回 `!0`，以便 kprobes 停止单步执行并直接返回到给定地址。
这也意味着不应再调用 `post_handler`。
请注意，在使用 TOC（Table of Contents）进行函数调用的一些架构上，此操作可能会更复杂，因为你需要为模块中的函数设置一个新的 TOC，并在返回时恢复旧的 TOC。

返回探针
-------------

返回探针是如何工作的？
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

当你调用 `register_kretprobe()` 时，Kprobes 在函数入口处建立一个 kprobe。当被探测的函数被调用且命中这个探针时，Kprobes 会保存返回地址的副本，并将返回地址替换为“弹射垫”（trampoline）的地址。弹射垫是一段任意代码——通常是 nop 指令。
在启动时，Kprobes 注册一个位于弹射垫上的 kprobe。
当被探测的函数执行其返回指令时，控制权传递给弹射垫，从而命中该探针。Kprobes 的弹射垫处理程序调用与 kretprobe 关联的用户指定的返回处理程序，然后将保存的指令指针设置为保存的返回地址，执行将在从陷阱返回时继续。
在被探测的函数执行期间，其返回地址存储在一个名为 kretprobe_instance 的对象中。在调用 `register_kretprobe()` 之前，用户通过设置 kretprobe 结构体中的 `maxactive` 字段来指定可以同时探测的指定函数实例数量。`register_kretprobe()` 预先分配指定数量的 kretprobe_instance 对象。
例如，如果函数是非递归的，并且在持有自旋锁的情况下被调用，则 `maxactive = 1` 应该就足够了。如果函数是非递归的并且永远不会释放 CPU（例如，通过信号量或抢占），则 `NR_CPUS` 应该足够。如果 `maxactive <= 0`，则将其设置为默认值：`max(10, 2*NR_CPUS)`。
如果你将 `maxactive` 设置得太低，也不是灾难性的；你只是会错过一些探针。在 kretprobe 结构体中，`nmissed` 字段在注册返回探针时被设置为零，并且每当被探测的函数被调用但没有可用的 kretprobe_instance 对象来建立返回探针时，该字段就会递增。
Kretprobe入口处理器
^^^^^^^^^^^^^^^^^^^^^^^

Kretprobes还提供了一个可选的用户指定处理器，该处理器在函数入口处运行。此处理器通过设置kretprobe结构体中的entry_handler字段来指定。每当由kretprobe放置在函数入口处的kprobe被触发时，如果设置了用户定义的entry_handler，则会调用它。如果entry_handler返回0（成功），则保证在函数返回时调用相应的返回处理器。如果entry_handler返回非零错误，Kprobes将保持返回地址不变，并且对于特定函数实例而言，kretprobe将不再起作用。多个入口和返回处理器的调用是通过与它们相关联的唯一kretprobe_instance对象进行匹配的。此外，用户还可以指定每个返回实例的私有数据作为每个kretprobe_instance对象的一部分。当需要在对应的用户入口和返回处理器之间共享私有数据时，这一点特别有用。每个私有数据对象的大小可以在注册kretprobe时通过设置kretprobe结构体中的data_size字段来指定。这些数据可以通过每个kretprobe_instance对象的data字段访问。如果探测到函数入口但没有可用的kretprobe_instance对象，则除了递增nmissed计数外，还会跳过用户entry_handler的调用。
.. _kprobes_jump_optimization:

跳转优化如何工作？
--------------------------------

如果你的内核是以CONFIG_OPTPROBES=y编译的（目前这个标志在x86/x86-64、非抢占式内核上自动设置为'y'），并且“debug.kprobes_optimization”内核参数设置为1（参见sysctl(8)），Kprobes会尝试通过使用跳转指令而不是断点指令来减少探针命中开销。
初始化一个Kprobe
^^^^^^^^^^^^^

当一个探针注册时，在尝试这种优化之前，Kprobes会在指定地址插入一个普通的基于断点的kprobe。因此，即使无法优化某个特定的探针点，也会有一个探针在那里。
安全检查
^^^^^^^^^^^^

在优化一个探针之前，Kprobes会执行以下安全检查：

- Kprobes验证将被跳转指令替换的区域（“优化区域”）完全位于一个函数内部。（跳转指令是多字节的，因此可能会覆盖多个指令。）

- Kprobes分析整个函数并验证没有跳转到优化区域。具体来说：

  - 函数中没有间接跳转；
  - 函数中没有会导致异常的指令（因为由异常触发的修复代码可能会跳回到优化区域——Kprobes检查异常表以验证这一点）；
  - 没有近跳转到优化区域（除了到第一个字节之外）；
- 对于优化区域中的每条指令，Kprobes验证该指令可以在线外执行。
准备绕行缓冲区
^^^^^^^^^^^^^^^^^^^^^^^

接下来，Kprobes准备一个“绕行”缓冲区，其中包含以下指令序列：

- 将CPU寄存器压入堆栈的代码（模拟断点陷阱）
- 调用trampoline代码，该代码调用用户的探针处理器
### 代码恢复寄存器
- 优化区域的指令
- 跳回到原始执行路径

#### 优化前
^^^^^^^^^^^^^^^^

在准备完绕行缓冲区后，Kprobes 会验证以下情况是否都不存在：

- 探针具有后处理函数
- 优化区域内其他指令被探测
- 探针已禁用
在上述任何一种情况下，Kprobes 都不会开始优化探针。由于这些是暂时性的情况，如果情况发生变化，Kprobes 会再次尝试优化它。
如果可以优化探针，Kprobes 将该探针加入到优化队列中，并触发 kprobe-optimizer 工作队列来优化它。如果在优化完成之前被优化点命中，Kprobes 通过将 CPU 的指令指针设置为绕行缓冲区中的复制代码来恢复对原始指令路径的控制——从而至少避免了单步执行。

#### 优化
^^^^^^^^^^^^

Kprobe-optimizer 不会立即插入跳转指令；相反，它首先调用 synchronize_rcu() 来确保安全，因为有可能在执行优化区域的过程中中断 CPU [3]。众所周知，synchronize_rcu() 可以确保所有在调用 synchronize_rcu() 时活跃的中断已完成，但前提是 CONFIG_PREEMPT=n。因此，这个版本的探针优化仅支持 CONFIG_PREEMPT=n 的内核 [4]。
之后，Kprobe-optimizer 调用 stop_machine() 使用 text_poke_smp() 替换优化区域中的跳转指令。

#### 反优化
^^^^^^^^^^^^^^

当一个优化过的探针被注销、禁用或被另一个探针阻塞时，它会被反优化。如果这种情况发生在优化完成之前，探针只是从优化队列中移除。如果优化已经完成，则使用 text_poke_smp() 用原始代码（除了第一个字节中的 int3 断点）替换跳转。
请想象一下，第2条指令被中断后，优化器在中断处理程序运行时用跳转地址替换了第2条指令。当中断返回到原始地址时，没有有效的指令，从而导致意外的结果。

这种优化安全性检查可以被替换为ksplice用于支持CONFIG_PREEMPT=y内核的停止机器（stop-machine）方法。

极客注意事项：
跳转优化改变了kprobe的pre_handler行为。
如果没有优化，pre_handler可以通过修改regs->ip并返回1来改变内核的执行路径。然而，当探测点被优化时，这种修改将被忽略。因此，如果你想调整内核的执行路径，你需要使用以下技术之一来抑制优化：

- 为kprobe的post_handler指定一个空函数；
或者

- 执行`sysctl -w debug.kprobes_optimization=n`。

.. _kprobes_blacklist:

黑名单
------

Kprobes可以探测大部分内核代码，但不能探测自身。这意味着有些函数是kprobes无法探测的。探测这些函数可能会导致递归陷阱（例如双重故障），或者嵌套的探测处理器可能永远不会被调用。Kprobes以黑名单的形式管理这些函数。如果你想将某个函数加入黑名单，只需（1）包含linux/kprobes.h，并且（2）使用NOKPROBE_SYMBOL()宏来指定黑名单中的函数。Kprobes会检查给定的探测地址是否在黑名单中，如果该地址在黑名单中，则拒绝注册。

.. _kprobes_archs_supported:

支持的架构
==========

Kprobes和返回探测器在以下架构上实现：

- i386（支持跳转优化）
- x86_64（AMD-64, EM64T）（支持跳转优化）
- ppc64
- sparc64（返回探测器尚未实现）
- arm
- ppc
- mips
- s390
- parisc
- loongarch
- riscv

配置Kprobes
===========

在使用make menuconfig/xconfig/oldconfig配置内核时，请确保将CONFIG_KPROBES设置为"y"，并在“通用架构相关选项”下查找“Kprobes”。为了能够加载和卸载基于Kprobes的仪器模块，请确保“可加载模块支持”（CONFIG_MODULES）和“模块卸载”（CONFIG_MODULE_UNLOAD）也被设置为"y"。
```plaintext
同时确保将 CONFIG_KALLSYMS 甚至可能是 CONFIG_KALLSYMS_ALL 设置为 "y"，因为 kallsyms_lookup_name() 被内核中的 kprobe 地址解析代码使用。
如果需要在函数中间插入探针，你可能会发现“编译带有调试信息的内核”（CONFIG_DEBUG_INFO）是有用的，这样你可以使用 "objdump -d -l vmlinux" 查看源代码到目标代码的映射。

API 参考
=================

Kprobes API 包括每种类型的探针的“注册”函数和“注销”函数。API 还包括用于注册和注销探针数组的 "register_*probes" 和 "unregister_*probes" 函数。以下是这些函数及其关联的探针处理器的简短、迷你手册页规范。请参阅 samples/kprobes/ 子目录中的文件以获取示例。

register_kprobe
-------------------

```
#include <linux/kprobes.h>
int register_kprobe(struct kprobe *kp);
```

在地址 kp->addr 设置一个断点。当触发断点时，Kprobes 会调用 kp->pre_handler。在单步执行被探测的指令后，Kprobe 会调用 kp->post_handler。任何或全部处理器可以为 NULL。如果 kp->flags 设置了 KPROBE_FLAG_DISABLED，则该 kp 将被注册但处于禁用状态，因此其处理器不会被触发，直到调用 enable_kprobe(kp)。
.. note::
   
   1. 引入 "symbol_name" 字段到 struct kprobe 后，探针点地址的解析现在由内核处理。
   下面的代码现在可以工作：
   
   ```
   kp.symbol_name = "symbol_name";
   ```

   （64位 PowerPC 的复杂性，例如函数描述符，会被透明地处理）

   2. 如果已知符号中安装探针点的偏移量，请使用 struct kprobe 的 "offset" 字段。此字段用于计算探针点位置。
   3. 指定 kprobe 的 "symbol_name" 或 "addr" 中的一个即可。如果两者都指定，kprobe 注册将会失败，并返回 -EINVAL。
   4. 对于 CISC 架构（如 i386 和 x86_64），kprobes 代码不会验证 kprobe.addr 是否位于指令边界上。谨慎使用 "offset"。
```
`register_kprobe()` 成功时返回 0，否则返回一个负的 `errno` 值。

用户的预处理器（`kp->pre_handler`）：

```c
#include <linux/kprobes.h>
#include <linux/ptrace.h>
int pre_handler(struct kprobe *p, struct pt_regs *regs);
```

当 `p` 指向与断点关联的 `kprobe` 结构，且 `regs` 指向包含在触发断点时保存的寄存器值的结构时调用。除非你是 Kprobes 高手，否则在这里返回 0。

用户的后处理器（`kp->post_handler`）：

```c
#include <linux/kprobes.h>
#include <linux/ptrace.h>
void post_handler(struct kprobe *p, struct pt_regs *regs,
		  unsigned long flags);
```

`p` 和 `regs` 的描述与 `pre_handler` 中的一致。`flags` 总是为零。

`register_kretprobe`
-------------------

```c
#include <linux/kprobes.h>
int register_kretprobe(struct kretprobe *rp);
```

为地址为 `rp->kp.addr` 的函数设置返回探针。当该函数返回时，Kprobes 会调用 `rp->handler`。

在调用 `register_kretprobe()` 之前，你必须适当设置 `rp->maxactive`；详情请参阅“返回探针是如何工作的？”。

`register_kretprobe()` 成功时返回 0，否则返回一个负的 `errno` 值。

用户的返回探针处理器（`rp->handler`）：

```c
#include <linux/kprobes.h>
#include <linux/ptrace.h>
int kretprobe_handler(struct kretprobe_instance *ri,
			      struct pt_regs *regs);
```

`regs` 的描述与 `kprobe.pre_handler` 中的一致。`ri` 指向 `kretprobe_instance` 对象，其中以下字段可能感兴趣：

- `ret_addr`：返回地址
- `rp`：指向对应的 `kretprobe` 对象
- `task`：指向对应的 `task_struct` 对象
- `data`：指向每个返回实例的私有数据；详情请参阅“Kretprobe 入口处理器”

`regs_return_value(regs)` 宏提供了一个简单的抽象来从架构定义的寄存器中提取返回值。

处理器的返回值目前被忽略。

`unregister_*probe`
------------------

```c
#include <linux/kprobes.h>
void unregister_kprobe(struct kprobe *kp);
void unregister_kretprobe(struct kretprobe *rp);
```

移除指定的探针。可以在探针注册后的任何时候调用卸载函数。
.. 注意::

   如果这些函数发现错误的探针（例如未注册的探针），它们会清除探针的 addr 字段。

register_*probes
----------------

::

	#include <linux/kprobes.h>
	int register_kprobes(struct kprobe **kps, int num);
	int register_kretprobes(struct kretprobe **rps, int num);

注册指定数组中的 num 个探针。如果在注册过程中发生任何错误，所有已注册的探针（直到错误探针为止）都会被安全地注销，然后 register_*probes 函数返回。
- kps/rps：指向 ``*probe`` 数据结构的指针数组
- num：数组项的数量

.. 注意::

   在使用这些函数之前，您必须分配（或定义）一个指针数组，并设置所有数组项。

unregister_*probes
------------------

::

	#include <linux/kprobes.h>
	void unregister_kprobes(struct kprobe **kps, int num);
	void unregister_kretprobes(struct kretprobe **rps, int num);

一次性移除指定数组中的 num 个探针。

.. 注意::

   如果这些函数在指定数组中发现一些错误的探针（例如未注册的探针），它们会清除那些错误探针的 addr 字段。然而，数组中的其他探针会被正确地注销。

disable_*probe
--------------

::

	#include <linux/kprobes.h>
	int disable_kprobe(struct kprobe *kp);
	int disable_kretprobe(struct kretprobe *rp);

暂时禁用指定的 ``*probe``。您可以使用 enable_*probe() 重新启用它。您必须指定已注册的探针。

enable_*probe
-------------

::

	#include <linux/kprobes.h>
	int enable_kprobe(struct kprobe *kp);
	int enable_kretprobe(struct kretprobe *rp);

启用由 disable_*probe() 禁用的 ``*probe``。您必须指定已注册的探针。

Kprobes 特性与限制
==================

Kprobes 允许多个探针位于同一地址。此外，如果有后处理函数（post_handler）的探针点不能被优化。因此，如果您在一个优化的探针点安装了一个带有 post_handler 的 kprobe，该探针点将自动取消优化。
一般来说，你可以在内核的任何地方安装探针。
特别是，你可以对中断处理程序进行探测。已知的例外情况在本节中讨论。
如果你尝试在实现 Kprobes 的代码中（主要是 kernel/kprobes.c 和 `arch/*/kernel/kprobes.c`，还包括诸如 do_page_fault 和 notifier_call_chain 等函数）安装探针，register_*probe 函数将返回 -EINVAL。
如果你在一个可内联的函数中安装探针，Kprobes 不会试图追踪该函数的所有内联实例并在那里安装探针。GCC 可能会在没有被请求的情况下内联一个函数，因此如果看不到预期的探针命中，请记住这一点。
探针处理器可以修改被探测函数的环境——例如，通过修改内核数据结构或修改 pt_regs 结构的内容（这些内容在从断点返回时会被恢复）。因此，Kprobes 可以用来安装补丁或注入故障进行测试。当然，Kprobes 没有办法区分故意注入的故障和意外发生的故障。不要酒后使用探针。
Kprobes 不会阻止探针处理器互相干扰——例如，探测 printk() 并从探针处理器中调用 printk()。如果一个探针处理器命中了另一个探针，那么第二个探针的处理器不会在这个实例中运行，并且第二个探针的 kprobe.nmissed 成员会被递增。
自 Linux v2.6.15-rc1 起，不同的 CPU 上可以并发运行多个处理器（或同一处理器的多个实例）。
Kprobes 在注册和注销期间之外不使用互斥锁或分配内存。
探针处理器是在禁用抢占或禁用中断的状态下运行的，这取决于架构和优化状态。（例如，在 x86/x86-64 上，kretprobe 处理器和优化过的 kprobe 处理器在不断开中断的情况下运行。无论如何，你的处理器不应让出 CPU（例如，尝试获取信号量或等待 I/O）。
由于返回探针是通过替换返回地址为 trampoline 地址来实现的，因此堆栈回溯和对 __builtin_return_address() 的调用通常会返回 trampoline 的地址，而不是实际的返回地址，对于 kretprobed 函数来说尤其如此。
据我们所知，`__builtin_return_address()` 仅用于仪器校准和错误报告。

如果函数调用次数与返回次数不匹配，则在该函数上注册返回探针可能会产生不理想的结果。在这种情况下，会打印一行：
```
kretprobe BUG!: Processing kretprobe d000000000041aa8 @ c00000000004f48c
```
通过这些信息，可以关联到导致问题的确切 kretprobe 实例。我们已经覆盖了 `do_exit()` 的情况。`do_execve()` 和 `do_fork()` 不是问题。我们目前不知道其他可能导致此问题的具体情况。

如果在进入或退出某个函数时，CPU 运行在一个不同于当前任务的栈上，在该函数上注册返回探针可能会产生不理想的结果。因此，Kprobes 在 x86_64 版本的 `__switch_to()` 中不支持返回探针（或 kprobes），注册函数会返回 `-EINVAL`。

在 x86/x86-64 上，由于 Kprobes 的跳转优化广泛修改了指令，因此有一些优化限制。为了说明这一点，我们引入一些术语。想象一个包含两个 2 字节指令和一个 3 字节指令的 3 指令序列：

```
        IA
        |
    [-2][-1][0][1][2][3][4][5][6][7]
        [ins1][ins2][  ins3 ]
        [<-     DCR       ->]
        [<- JTPR ->]

ins1: 第一条指令
ins2: 第二条指令
ins3: 第三条指令
IA: 插入地址
JTPR: 跳转目标禁止区域
DCR: 绕道代码区域
```

DCR 中的指令会被复制到 kprobe 的离线缓冲区中，因为 DCR 中的字节会被一个 5 字节的跳转指令替换。因此有以下几个限制：
a) DCR 中的指令必须可重定位
b) DCR 中的指令不能包含调用指令
c) JTPR 不应被任何跳转或调用指令作为目标
d) DCR 不能跨越函数边界

无论如何，这些限制由内核中的指令解码器进行检查，因此您无需担心这些问题。
探针开销
==============

在2005年使用的典型CPU上，kprobe命中需要0.5到1.0微秒来处理。具体来说，一个反复命中相同探针点并每次触发简单处理器的基准测试报告每秒100万到200万次命中，这取决于架构。return-probe命中通常比kprobe命中慢50%-75%。当在一个函数上设置了return探针时，在该函数入口处添加一个kprobe基本上不会增加额外开销。

以下是不同架构下的样本开销数据（单位：微秒）：

  k = kprobe；r = return probe；kr = kprobe + return probe 在同一个函数上

  i386: Intel Pentium M, 1495 MHz, 2957.31 BOGOMIPS
  k = 0.57 微秒；r = 0.92；kr = 0.99

  x86_64: AMD Opteron 246, 1994 MHz, 3971.48 BOGOMIPS
  k = 0.49 微秒；r = 0.80；kr = 0.82

  ppc64: POWER5 (gr), 1656 MHz (禁用了SMT，每个物理CPU有1个虚拟CPU)
  k = 0.77 微秒；r = 1.26；kr = 1.45

优化后的探针开销
------------------------

通常，优化后的kprobe命中需要0.07到0.1微秒来处理。以下是x86架构下的样本开销数据（单位：微秒）：

  k = 未优化的kprobe，b = 增强版（跳过单步），o = 优化的kprobe，
  r = 未优化的kretprobe，rb = 增强版kretprobe，ro = 优化的kretprobe

  i386: Intel(R) Xeon(R) E5410, 2.33GHz, 4656.90 BOGOMIPS
  k = 0.80 微秒；b = 0.33；o = 0.05；r = 1.10；rb = 0.61；ro = 0.33

  x86-64: Intel(R) Xeon(R) E5410, 2.33GHz, 4656.90 BOGOMIPS
  k = 0.99 微秒；b = 0.43；o = 0.06；r = 1.24；rb = 0.68；ro = 0.30

待办事项
====

a. SystemTap (http://sourceware.org/systemtap)：提供简化了的基于探针的工具链编程接口。尝试使用它。
b. 为sparc64提供内核return探针支持。
c. 支持其他架构。
d. 用户空间探针。
e. 触发于数据引用的断点探针。

Kprobes 示例
===============

参见samples/kprobes/kprobe_example.c

Kretprobes 示例
==================

参见samples/kprobes/kretprobe_example.c

废弃功能
===================

Jprobes现在是一个废弃的功能。依赖它的用户应该迁移到其他跟踪功能或使用较旧的内核。请考虑将您的工具迁移到以下选项之一：

- 使用trace-event来跟踪目标函数及其参数
  trace-event是一个低开销（如果关闭几乎无可见开销）的静态定义事件接口。您可以定义新事件并通过ftrace或其他任何跟踪工具进行跟踪。
查看以下网址：

    - https://lwn.net/Articles/379903/
    - https://lwn.net/Articles/381064/
    - https://lwn.net/Articles/383362/

- 使用 ftrace 动态事件（kprobe 事件）与 perf-probe
如果你使用调试信息（CONFIG_DEBUG_INFO=y）编译内核，你可以通过 perf-probe 查看哪些寄存器/栈分配给了哪些局部变量或参数，并设置新的事件来跟踪它们。
请参阅以下文档：

  - Documentation/trace/kprobetrace.rst
  - Documentation/trace/events.rst
  - tools/perf/Documentation/perf-probe.txt

kprobes 的 debugfs 接口
=============================

在较新的内核版本（> 2.6.20）中，已注册的 kprobes 列表可以在 /sys/kernel/debug/kprobes/ 目录下查看（假设 debugfs 挂载在 /sys/kernel/debug）。
/sys/kernel/debug/kprobes/list：列出系统上所有已注册的探针：

```
c015d71a  k  vfs_read+0x0
c03dedc5  r  tcp_v4_rcv+0x0
```

第一列提供了插入探针的内核地址。
第二列表示探针类型（k - kprobe 和 r - kretprobe），
而第三列表示探针的符号+offset。
如果被探测的函数属于一个模块，则还会指定模块名称。后续列显示探针状态。如果探针位于不再有效的虚拟地址上（如模块初始化部分、对应于已卸载模块的模块虚拟地址），则这些探针会标记为 [GONE]。如果探针暂时被禁用，则标记为 [DISABLED]。如果探针被优化，则标记为 [OPTIMIZED]。如果探针基于 ftrace，则标记为 [FTRACE]。
/sys/kernel/debug/kprobes/enabled：强制打开/关闭 kprobes
提供了一个全局开关来强制打开或关闭已注册的 kprobes。
默认情况下，所有 kprobes 都是启用的。通过向此文件写入 "0"，所有已注册的探针将被解除武装，直到向此文件写入 "1" 为止。请注意，这个开关只是解除和启动所有 kprobes，并不改变每个探针的禁用状态。这意味着禁用的 kprobes（标记为 [DISABLED]）在使用此开关打开所有 kprobes 时不会被启用。
kprobes 的 sysctl 接口
============================

/proc/sys/debug/kprobes-optimization：打开/关闭 kprobes 优化
当 `CONFIG_OPTPROBES=y` 时，此 sysctl 接口会显示，并提供一个全局强制开启或关闭跳转优化（参见章节 :ref:`kprobes_jump_optimization`）的选项。默认情况下，跳转优化是允许的（开启）。如果您将 "0" 回显到此文件或通过 sysctl 将 "debug.kprobes_optimization" 设置为 0，则所有优化后的探针将被取消优化，并且在此之后注册的所有新探针也不会被优化。请注意，此选项会改变优化状态。这意味着已优化的探针（标记为 [OPTIMIZED]）将被取消优化（[OPTIMIZED] 标签将被移除）。如果再次开启该选项，它们将重新被优化。

参考文献
========

有关 Kprobes 的更多信息，请参阅以下网址：

- https://lwn.net/Articles/132196/
- https://www.kernel.org/doc/ols/2006/ols2006v2-pages-109-124.pdf
