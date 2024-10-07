SPDX 许可声明标识符: GPL-2.0

=====================================
虚拟映射内核栈支持
=====================================

:作者: Shuah Khan <skhan@linuxfoundation.org>

.. contents:: :local:

概述
--------

这是从代码和最初引入 `虚拟映射内核栈功能 <https://lwn.net/Articles/694348/>` 的补丁系列中收集的信息。

介绍
------------

内核栈溢出往往难以调试，并使内核容易受到攻击。问题可能在稍后出现，使得隔离和查找根本原因变得困难。具有保护页的虚拟映射内核栈可以在内核栈溢出时立即捕获异常，而不是导致难以诊断的损坏。通过配置选项 `HAVE_ARCH_VMAP_STACK` 和 `VMAP_STACK` 可以启用对具有保护页的虚拟映射栈的支持。此功能会在栈溢出时引发可靠的故障。溢出后的栈跟踪的可用性及对溢出的响应取决于具体架构。
.. note::
        截至本文撰写之时，arm64、powerpc、riscv、s390、um 和 x86 支持 `VMAP_STACK`
`HAVE_ARCH_VMAP_STACK`
--------------------

能够支持虚拟映射内核栈的架构应该启用此布尔配置选项。要求如下：

- `vmalloc` 空间必须足够大以容纳许多内核栈。这可能会排除许多32位架构。
- 在 `vmalloc` 空间中的栈需要可靠地工作。例如，如果 `vmap` 页表是按需创建的，则要么这种机制能够在栈指向未填充页表的虚拟地址时正常工作，要么架构代码（如 `switch_to()` 和 `switch_mm()`）需要确保在使用可能未填充的栈运行之前填充栈的页表项。
- 如果栈溢出到保护页中，应发生合理的情况。“合理”的定义是灵活的，但立即重启而不记录任何信息是不友好的。
`VMAP_STACK`
----------

当启用时，布尔配置选项 `VMAP_STACK` 分配虚拟映射的任务栈。此选项依赖于 `HAVE_ARCH_VMAP_STACK`。
- 如果您希望使用带有保护页的虚拟映射内核栈，请启用此选项。这会在内核栈溢出时立即捕获异常，而不是导致难以诊断的损坏。
.. note::

        使用此功能与 KASAN 需要架构支持使用真实的影子内存支持虚拟映射，并且必须启用 `KASAN_VMALLOC`。
.. note::

   VMAP_STACK 已启用，因此无法对栈上分配的数据执行 DMA 操作。

内核配置选项和依赖关系不断变化。请参考最新的代码库：

`Kconfig <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/arch/Kconfig>`

分配
------

当创建一个新的内核线程时，会从页级分配器中分配虚拟连续的内存页面作为线程栈。这些页面被映射到具有 PAGE_KERNEL 保护的连续内核虚拟空间中。

alloc_thread_stack_node() 调用 __vmalloc_node_range() 来分配带有 PAGE_KERNEL 保护的栈。
- 分配的栈会被缓存并在稍后由新线程重用，因此在分配/释放栈给任务时需要手动进行 memcg 会计操作。
因此，__vmalloc_node_range 是在没有 __GFP_ACCOUNT 的情况下调用的。
- vm_struct 会被缓存，以便在中断上下文中启动线程释放时能够找到它。free_thread_stack() 可以在中断上下文中被调用。
- 在 arm64 上，所有 VMAP 的栈需要具有相同的对齐方式，以确保 VMAP 栈溢出检测能够正确工作。架构特定的 vmap 栈分配器负责处理这一细节。
- 这不涉及中断栈——根据原始补丁所述。

线程栈的分配是由 clone()、fork()、vfork() 和 kernel_thread() 通过 kernel_clone() 发起的。以下是一些搜索代码库以了解何时以及如何分配线程栈的提示：
大部分代码位于：
`kernel/fork.c <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/kernel/fork.c>`
task_struct 中的 stack_vm_area 指针跟踪了虚拟分配的栈，并且非空的 stack_vm_area 指针表示启用了虚拟映射的内核栈。
```c
struct vm_struct *stack_vm_area;
```

### 栈溢出处理

前导和尾随保护页有助于检测栈溢出。当栈溢出进入保护页时，处理程序必须小心不要再次溢出栈。当处理程序被调用时，很可能已经几乎没有栈空间了。
在 x86 上，这是通过处理双故障栈上的页面错误来指示内核栈溢出来实现的。

### 使用保护页测试 VMAP 分配

我们如何确保 VMAP_STACK 实际上是使用前导和尾随保护页进行分配的？以下 lkdtm 测试可以帮助检测任何退化：
```c
void lkdtm_STACK_GUARD_PAGE_LEADING();
void lkdtm_STACK_GUARD_PAGE_TRAILING();
```

### 结论

- 每个 CPU 的 vmalloced 栈缓存似乎比高阶栈分配稍微快一些，至少在缓存命中时是这样。
- THREAD_INFO_IN_TASK 完全消除了架构特定的 thread_info，并将 thread_info（仅包含标志）和 'int cpu' 嵌入到 task_struct 中。
- 只要任务结束（无需等待 RCU），就可以立即释放线程栈；如果使用了 vmapped 栈，则可以在同一 CPU 上缓存整个栈以供重用。
