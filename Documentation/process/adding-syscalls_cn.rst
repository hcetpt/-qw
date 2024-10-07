.. _addsyscalls:

添加一个新的系统调用
========================

本文档描述了向 Linux 内核添加一个新系统调用所需的过程，除此之外还需遵循
:ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 中的常规提交建议。
系统调用替代方案
------------------------

在添加新的系统调用时，首先需要考虑是否有其他替代方案可能更合适。尽管系统调用是最传统且最明显的用户空间与内核之间的交互方式，但还有其他可能性——选择最适合您接口的方式：
- 如果涉及的操作可以被设计成类似文件系统的对象，那么创建一个新的文件系统或设备可能更有意义。这也有助于将新功能封装到一个内核模块中，而不是必须将其构建到主内核中。
- 如果新功能涉及内核通知用户空间某些事件的发生，则返回相关对象的新文件描述符可以让用户空间使用 ``poll``/``select``/``epoll`` 来接收该通知。
- 然而，那些无法映射为 :manpage:`read(2)`/:manpage:`write(2)` 类似操作的功能必须实现为 :manpage:`ioctl(2)` 请求，这可能导致一个较为晦涩的API。
- 如果只是暴露运行时的系统信息，那么在 sysfs（参见 ``Documentation/filesystems/sysfs.rst``）或 ``/proc`` 文件系统中添加一个新节点可能更合适。然而，访问这些机制需要相关的文件系统已挂载，这在某些情况下可能不总是可行（例如，在命名空间/沙箱/chroot环境中）。避免在 debugfs 中添加任何API，因为这不是一个面向用户的“生产”接口。
- 如果操作是针对特定文件或文件描述符的，那么增加一个 :manpage:`fcntl(2)` 命令选项可能更合适。然而，:manpage:`fcntl(2)` 是一个多路复用系统调用，隐藏了很多复杂性，因此此选项最好用于与现有 :manpage:`fcntl(2)` 功能非常相似的新功能，或者新功能非常简单（例如，获取/设置与文件描述符相关的简单标志）。
- 如果操作是针对特定任务或进程的，那么增加一个 :manpage:`prctl(2)` 命令选项可能更合适。与 :manpage:`fcntl(2)` 类似，这个系统调用也是一个复杂的多路复用器，因此最好仅用于接近现有 ``prctl()`` 命令的模拟或获取/设置与进程相关的简单标志。

设计API：规划扩展性
-----------------------------------------
一个新的系统调用成为内核API的一部分，并且需要永久支持。因此，明确地在内核邮件列表上讨论接口是非常有必要的，并且重要的是要为未来的接口扩展做好规划。
（系统调用表中充满了未这样做的历史示例，以及相应的后续系统调用——`eventfd`/`eventfd2`、`dup2`/`dup3`、`inotify_init`/`inotify_init1`、`pipe`/`pipe2`、`renameat`/`renameat2`——因此从内核的历史中吸取教训，并从一开始就计划扩展。）

对于只需要几个参数的简单系统调用，允许未来扩展的最佳方式是在系统调用中包含一个标志参数。为了确保用户空间程序在不同内核版本间可以安全使用这些标志，请检查标志值是否包含任何未知标志，并在包含未知标志时拒绝系统调用（通过`EINVAL`）：

    if (flags & ~(THING_FLAG1 | THING_FLAG2 | THING_FLAG3))
        return -EINVAL;

（如果还没有使用任何标志值，请检查标志参数是否为零。）

对于涉及更多参数的复杂系统调用，最好将大部分参数封装到一个结构体中，该结构体通过指针传递。这样的结构体可以通过在结构体中包含一个大小参数来应对未来的扩展：

    struct xyzzy_params {
        u32 size; /* 用户空间设置 p->size = sizeof(struct xyzzy_params) */
        u32 param_1;
        u64 param_2;
        u64 param_3;
    };

只要随后添加的字段（如`param_4`）设计为零值时恢复以前的行为，这就可以支持两个方向上的版本不匹配：

- 为了处理较新的用户空间程序调用旧内核的情况，内核代码应检查超出其期望结构大小的任何内存是否为零（实际上检查`param_4 == 0`）
- 为了处理较旧的用户空间程序调用新内核的情况，内核代码可以将较小的结构实例扩展为零（实际上设置`param_4 = 0`）

参见`perf_event_open(2)`手册页和`perf_copy_attr()`函数（位于`kernel/events/core.c`）作为这种方法的一个例子。

设计API：其他考虑
-----------------------

如果你的新系统调用允许用户空间引用一个内核对象，则应使用文件描述符作为该对象的句柄——不要在内核已经有机制和明确定义的语义用于文件描述符的情况下发明一种新的用户空间对象句柄。
如果你的新`xyzzy(2)`系统调用返回一个新的文件描述符，则标志参数应包括一个等同于在新文件描述符上设置`O_CLOEXEC`的值。这使得用户空间可以在`xyzzy()`和调用`fcntl(fd, F_SETFD, FD_CLOEXEC)`之间关闭时间窗口，在此期间另一个线程中的意外`fork()`和`execve()`可能会泄露一个描述符给被执行的程序。（然而，抵制重用`O_CLOEXEC`常量实际值的诱惑，因为它是架构特定的，并且是相当满的`O_*`标志命名空间的一部分。）

如果你的系统调用返回一个新的文件描述符，你也应该考虑对该文件描述符使用`poll(2)`家族系统调用的意义。使文件描述符准备好读取或写入是内核通常用来指示用户空间相关内核对象上发生事件的方式。
如果你的新`xyzzy(2)`系统调用涉及一个文件名参数：

    int sys_xyzzy(const char __user *path, ..., unsigned int flags);

你也应该考虑是否更合适的版本是`xyzzyat(2)`：

    int sys_xyzzyat(int dfd, const char __user *path, ..., unsigned int flags);

这为用户空间指定文件提供了更多的灵活性；特别是它允许用户空间使用`AT_EMPTY_PATH`标志请求已打开文件描述符的功能，有效地提供了一个免费的`fxyzzy(3)`操作：

- `xyzzyat(AT_FDCWD, path, ..., 0)`等同于`xyzzy(path,...)`
- `xyzzyat(fd, "", ..., AT_EMPTY_PATH)`等同于`fxyzzy(fd, ...)`

（有关\*at()调用的理由的更多详细信息，请参阅`openat(2)`手册页；有关`AT_EMPTY_PATH`的例子，请参阅`fstatat(2)`手册页。）

如果你的新`xyzzy(2)`系统调用涉及描述文件内的偏移量的参数，使其类型为`loff_t`以便即使在32位架构上也能支持64位偏移量。
如果你的新`xyzzy(2)`系统调用涉及特权功能，则需要由适当的Linux能力位控制（通过调用`capable()`检查），如`capabilities(7)`手册页所述。选择一个已经管理类似功能的现有能力位，但尽量避免将大量仅仅稍微相关的功能合并到同一个位下，因为这违背了能力的目的，即拆分root的权限。特别地，避免为已经过于通用的`CAP_SYS_ADMIN`能力添加新的用途。
如果你的新`xyzzy(2)`系统调用操纵除调用进程之外的进程，应限制（通过调用`ptrace_may_access()`）只有具有与目标进程相同权限或具有必要能力的调用进程才能操纵目标进程。
最后，注意一些非x86架构在处理显式64位参数时更容易处理，如果这些参数位于奇数位置（即参数1、3、5），以允许使用连续的32位寄存器对。 （如果参数是通过指针传递的结构体的一部分，则此问题不适用。）

提议API
-----------------

为了使新的系统调用易于审查，最好将补丁集分成独立的部分。这些部分至少应包括以下项作为单独的提交（每个项下面有进一步描述）：

- 系统调用的核心实现，包括原型、通用编号、Kconfig更改和回退存根实现
- 某一特定架构（通常是x86，包括所有x86_64、x86_32和x32）的新系统调用的实现
### 新系统调用演示

- 在 `tools/testing/selftests/` 中通过自测展示新系统调用在用户空间的使用方法。
- 新系统调用的手册页草稿，可以是封面信中的纯文本，也可以是对（独立的）手册页仓库的一次补丁。

对于新系统调用提案，如同内核API的任何变更一样，应始终抄送至 `linux-api@vger.kernel.org`。

### 通用系统调用实现

你的新系统调用 `:manpage:xyzzy(2)` 的主要入口点将被命名为 `sys_xyzzy()`，但你应该通过适当的 `SYSCALL_DEFINEn()` 宏来添加这个入口点，而不是显式地添加。其中的 'n' 表示系统调用参数的数量，宏接受系统调用名称以及参数的类型和名称对作为参数。使用此宏可以让有关新系统调用的元数据提供给其他工具使用。

新的入口点还需要一个对应的函数原型，在 `include/linux/syscalls.h` 中标记为 `asmlinkage` 以匹配系统调用的调用方式：

```c
asmlinkage long sys_xyzzy(...);
```

一些架构（例如 x86）有自己的特定于架构的系统调用表，但其他几个架构共享一个通用的系统调用表。通过向 `include/uapi/asm-generic/unistd.h` 中的列表添加条目来将你的新系统调用添加到通用列表中：

```c
#define __NR_xyzzy 292
__SYSCALL(__NR_xyzzy, sys_xyzzy)
```

更新 `__NR_syscalls` 计数以反映新增加的系统调用，并注意如果在同一合并窗口中添加了多个新系统调用，你的新系统调用编号可能会调整以解决冲突。

文件 `kernel/sys_ni.c` 提供了每个系统调用的回退存根实现，返回 `-ENOSYS`。在此处也添加你的新系统调用：

```c
COND_SYSCALL(xyzzy);
```

你的新内核功能及其控制它的系统调用通常应该是可选的，因此应在 `init/Kconfig` 中为其添加一个 `CONFIG` 选项。对于新的 `CONFIG` 选项：

- 包含对由该选项控制的新功能和系统调用的描述；
- 如果应该隐藏普通用户，则使该选项依赖于 `EXPERT`；
- 使实现该功能的任何新源文件依赖于 `CONFIG` 选项（例如 `obj-$(CONFIG_XYZZY_SYSCALL) += xyzzy.o`）；
- 仔细检查关闭新 `CONFIG` 选项后内核是否仍然能够构建。

总结来说，你需要一个包含以下内容的提交：

- 新功能的 `CONFIG` 选项，通常位于 `init/Kconfig` 中；
- 入口点的 `SYSCALL_DEFINEn(xyzzy, ...)`；
- 对应的原型在 `include/linux/syscalls.h` 中；
- 在 `include/uapi/asm-generic/unistd.h` 中的通用表项；
- 在 `kernel/sys_ni.c` 中的回退存根。

### x86 系统调用实现

为了在 x86 平台上设置你的新系统调用，你需要更新主系统调用表。假设你的新系统调用没有特殊之处（见下文），这涉及到在 `arch/x86/entry/syscalls/syscall_64.tbl` 中的一个 “common” 条目（针对 x86_64 和 x32）：

```
333   common   xyzzy     sys_xyzzy
```

以及在 `arch/x86/entry/syscalls/syscall_32.tbl` 中的一个 “i386” 条目：

```
380   i386     xyzzy     sys_xyzzy
```

同样，这些数字如果在相关合并窗口中有冲突，则可能会改变。
兼容性系统调用（通用）
------------------------------------

对于大多数系统调用，即使用户空间程序本身是32位的，也可以调用相同的64位实现；即使系统调用的参数包含一个显式的指针，这也被透明地处理。然而，有几种情况需要一个兼容层来应对32位和64位之间的大小差异。

第一种情况是当64位内核也支持32位用户空间程序时，因此需要解析可能包含32位或64位值的（`__user`）内存区域。特别是，每当系统调用参数为以下情况时：

- 指向指针的指针
- 指向包含指针的结构体（例如 `struct iovec __user *`）
- 指向变长整型类型（`time_t`、`off_t`、`long`等）
- 指向包含变长整型类型的结构体

第二种需要兼容层的情况是当系统调用的某个参数具有明确的64位类型，即使在32位架构上也是如此，例如 `loff_t` 或 `__u64`。在这种情况下，从32位应用程序传到64位内核的值将被拆分成两个32位值，然后需要在兼容层中重新组合。（注意指向显式64位类型的指针作为系统调用参数**不需要**兼容层；例如，`splice(2)` 的参数类型为 `loff_t __user *` 就不会触发 `compat_` 系统调用的需求。）

兼容版本的系统调用称为 `compat_sys_xyzzy()`，并使用 `COMPAT_SYSCALL_DEFINEn()` 宏添加，类似于 SYSCALL_DEFINEn。此实现版本作为64位内核的一部分运行，但期望接收32位参数值，并进行必要的处理。（通常，`compat_sys_` 版本会将这些值转换为64位版本，并调用 `sys_` 版本，或者两者都调用一个共同的内部实现函数。）

兼容入口点还需要在 `include/linux/compat.h` 中有一个相应的函数原型，标记为 asmlinkage 以匹配系统调用的调用方式：

```c
asmlinkage long compat_sys_xyzzy(...);
```

如果系统调用涉及一个在32位和64位系统上布局不同的结构体，例如 `struct xyzzy_args`，则 `include/linux/compat.h` 头文件还应该包括该结构体的一个兼容版本（`struct compat_xyzzy_args`），其中每个可变大小字段都有与 `struct xyzzy_args` 中对应的类型相匹配的 `compat_` 类型。`compat_sys_xyzzy()` 函数可以使用这个 `compat_` 结构体来解析来自32位调用的参数。

例如，如果 `struct xyzzy_args` 包含如下字段：

```c
struct xyzzy_args {
    const char __user *ptr;
    __kernel_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```

那么 `struct compat_xyzzy_args` 将包含如下字段：

```c
struct compat_xyzzy_args {
    compat_uptr_t ptr;
    compat_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```

通用系统调用列表也需要调整以适应兼容版本；`include/uapi/asm-generic/unistd.h` 中的条目应使用 `__SC_COMP` 而不是 `__SYSCALL`：

```c
#define __NR_xyzzy 292
__SC_COMP(__NR_xyzzy, sys_xyzzy, compat_sys_xyzzy)
```

总结，你需要：
- 一个用于兼容入口点的 `COMPAT_SYSCALL_DEFINEn(xyzzy, ...)`
- 在 `include/linux/compat.h` 中相应的原型
- （如果需要的话）在 `include/linux/compat.h` 中的32位映射结构体
- 在 `include/uapi/asm-generic/unistd.h` 中使用 `__SC_COMP` 而不是 `__SYSCALL` 的实例

兼容性系统调用（x86）
------------------------------------

要为具有兼容版本的系统调用连接x86架构，需要调整系统调用表中的条目。
首先，在 `arch/x86/entry/syscalls/syscall_32.tbl` 中的条目增加一列，指示在64位内核上运行的32位用户空间程序应命中兼容入口点：

```plaintext
380   i386     xyzzy     sys_xyzzy    __ia32_compat_sys_xyzzy
```

其次，你需要确定新系统调用的x32 ABI版本应该如何处理。这里有两种选择：参数布局应与64位版本或32位版本匹配。
如果涉及指向指针的指针，则决策很简单：x32是ILP32，因此布局应与32位版本匹配，并且 `arch/x86/entry/syscalls/syscall_64.tbl` 中的条目被拆分，以便x32程序命中兼容包装器：

```plaintext
333   64       xyzzy     sys_xyzzy
..
555   x32      xyzzy     __x32_compat_sys_xyzzy
```

如果没有涉及指针，则最好重用64位系统调用作为x32 ABI（因此 `arch/x86/entry/syscalls/syscall_64.tbl` 中的条目保持不变）。
无论哪种情况，你应该检查你的参数布局中涉及的类型确实可以从x32（-mx32）精确映射到32位（-m32）或64位（-m64）等效类型。
系统调用返回其他位置
--------------------------------

对于大多数系统调用，一旦系统调用完成，用户程序将从它中断的地方继续执行——即在下一条指令处，堆栈和大多数寄存器与系统调用之前相同，并且具有相同的虚拟内存空间。然而，有一些系统调用的工作方式不同。它们可能会返回到不同的位置（如 `rt_sigreturn`），或者改变程序的内存空间（如 `fork`/`vfork`/`clone`）甚至架构（如 `execve`/`execveat`）。为了允许这种情况，内核实现可能需要将额外的寄存器保存并恢复到内核栈中，从而完全控制系统调用之后的执行位置和方式。这是架构特定的，但通常涉及定义汇编入口点来保存/恢复额外的寄存器，并调用实际的系统调用入口点。

对于x86_64架构，这在 `arch/x86/entry/entry_64.S` 中实现为一个名为 `stub_xyzzy` 的入口点，系统调用表（`arch/x86/entry/syscalls/syscall_64.tbl`）中的条目被调整以匹配：

    333   common   xyzzy     stub_xyzzy

对于在64位内核上运行的32位程序，通常称为 `stub32_xyzzy` 并在 `arch/x86/entry/entry_64_compat.S` 中实现，相应的系统调用表调整在 `arch/x86/entry/syscalls/syscall_32.tbl` 中：

    380   i386     xyzzy     sys_xyzzy    stub32_xyzzy

如果系统调用需要兼容层（如前一节所述），则 `stub32_` 版本需要调用 `compat_sys_` 版本的系统调用，而不是原生的64位版本。此外，如果x32 ABI实现与x86_64版本不一致，则其系统调用表也需要调用一个存根，该存根再调用 `compat_sys_` 版本。

为了完整性，最好设置一个映射以使用户模式Linux仍然工作——其系统调用表将引用 `stub_xyzzy`，但UML构建不包括 `arch/x86/entry/entry_64.S` 实现（因为UML模拟寄存器等）。修复此问题只需在 `arch/x86/um/sys_call_table_64.c` 中添加一个宏定义：

    #define stub_xyzzy sys_xyzzy

其他细节
-------------

内核的大部分部分以通用方式处理系统调用，但偶尔会有特殊情况，可能需要针对您的特定系统调用进行更新。审计子系统就是这样一个特殊情况；它包含（架构特定的）函数，这些函数对某些特殊类型的系统调用进行分类——特别是文件打开（`open`/`openat`）、程序执行（`execve`/`execveat`）或套接字多路复用器（`socketcall`）操作。如果您的新系统调用类似于其中的一种，则应更新审计系统。

更一般地说，如果存在一个与您的新系统调用类似的现有系统调用，值得在整个内核中使用grep搜索现有的系统调用来检查是否有其他特殊情况。

测试
-------

显然，新的系统调用应该经过测试；同时也有助于向审查者提供一个演示，展示用户空间程序将如何使用该系统调用。一种结合这两个目标的好方法是在 `tools/testing/selftests/` 下的新目录中包含一个简单的自测程序。

对于一个新的系统调用，显然没有libc包装函数，因此测试需要使用 `syscall()` 来调用它；此外，如果系统调用涉及一个新的用户空间可见结构，则需要安装相应的头文件以编译测试。
确保自检在所有支持的架构上都能成功运行。例如，检查其在编译为x86_64（-m64）、x86_32（-m32）和x32（-mx32）ABI程序时是否能正常工作。
为了更全面和彻底地测试新功能，还应考虑将测试添加到Linux测试项目或对于与文件系统相关的更改，添加到xfstests项目中。
- https://linux-test-project.github.io/
- git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git

### 手册页
所有新的系统调用都应附带完整的手册页，最好是使用groff标记，但纯文本也可以。如果使用groff，则应在补丁集的封面邮件中包含预渲染的ASCII版手册页，以便于审阅者查看。
手册页应抄送给linux-man@vger.kernel.org。
更多详情，请参见https://www.kernel.org/doc/man-pages/patches.html。

### 不要在内核中调用系统调用
如前所述，系统调用是用户空间与内核之间的交互点。因此，系统调用函数（如`sys_xyzzy()`或`compat_sys_xyzzy()`）只能通过系统调用表从用户空间调用，而不能从内核其他地方调用。如果系统调用的功能在内核中有用，需要在旧系统调用和新系统调用之间共享，或者需要在系统调用及其兼容变体之间共享，则应通过“辅助”函数（如`ksys_xyzzy()`）来实现。这个内核函数可以在系统调用存根（`sys_xyzzy()`）、兼容系统调用存根（`compat_sys_xyzzy()`）和其他内核代码中调用。
至少在64位x86上，从v4.17版本开始，不从内核调用系统调用函数将成为硬性要求。它使用不同的系统调用调用约定，在系统调用包装器中实时解码`struct pt_regs`，然后将处理传递给实际的系统调用函数。
这意味着只有特定系统调用所需的参数才会在系统调用入口时传递，而不是每次都填充六个CPU寄存器（这可能会导致严重问题）。
此外，内核数据和用户数据之间的访问规则可能不同。这也是为什么调用`sys_xyzzy()`通常不是一个好主意的原因。
仅允许在特定架构的覆盖、特定架构的兼容包装器或其他arch/目录下的代码中违反此规则。

### 参考资料和来源
- LWN文章：Michael Kerrisk关于系统调用中flags参数的使用：https://lwn.net/Articles/585415/
- LWN文章：Michael Kerrisk关于如何处理未知标志：https://lwn.net/Articles/588444/
- LWN文章：Jake Edge描述64位系统调用参数的约束：https://lwn.net/Articles/311630/
- LWN文章：David Drysdale详细描述v3.14中的系统调用实现路径：
  - https://lwn.net/Articles/604287/
  - https://lwn.net/Articles/604515/
- 特定架构对系统调用的要求在：:manpage:`syscall(2)` 手册页中讨论：http://man7.org/linux/man-pages/man2/syscall.2.html#NOTES
- Linus Torvalds关于`ioctl()`问题的汇总电子邮件：https://yarchive.net/comp/linux/ioctl.html
- “如何不发明内核接口”，Arnd Bergmann：https://www.ukuug.org/events/linux2007/2007/papers/Bergmann.pdf
- LWN文章：Michael Kerrisk关于避免新用法的CAP_SYS_ADMIN：https://lwn.net/Articles/486306/
- Andrew Morton建议所有相关的新系统调用信息应在同一邮件线程中提供：https://lore.kernel.org/r/20140724144747.3041b208832bbdf9fbce5d96@linux-foundation.org
- Michael Kerrisk建议新系统调用应附带手册页：https://lore.kernel.org/r/CAKgNAkgMA39AfoSoA5Pe1r9N+ZzfYQNvNPvcRN7tOvRb8+v06Q@mail.gmail.com
- Thomas Gleixner建议x86初始化应在单独的提交中进行：https://lore.kernel.org/r/alpine.DEB.2.11.1411191249560.3909@nanos
- Greg Kroah-Hartman建议新系统调用应附带手册页和自检：https://lore.kernel.org/r/20140320025530.GA25469@kroah.com
- Michael Kerrisk讨论新系统调用与:manpage:`prctl(2)`扩展的区别：https://lore.kernel.org/r/CAHO5Pa3F2MjfTtfNxa8LbnkeeU8=YJ+9tDqxZpw7Gz59E-4AUg@mail.gmail.com
- Ingo Molnar建议涉及多个参数的系统调用应将这些参数封装在一个结构中，该结构包含一个大小字段以供将来扩展：https://lore.kernel.org/r/20150730083831.GA22182@gmail.com
- 由于重复使用O_*编号空间标志而产生的编号异常：
  - 提交75069f2b5bfb（“vfs: 重新编号FMODE_NONOTIFY并添加唯一性检查”）
  - 提交12ed2e36c98a（“fanotify: FMODE_NONOTIFY和__O_SYNC在sparc中冲突”）
  - 提交bb458c644a59（“更安全的O_TMPFILE ABI”）
- Matthew Wilcox关于64位参数限制的讨论：https://lore.kernel.org/r/20081212152929.GM26095@parisc-linux.org
- Greg Kroah-Hartman建议应监控未知标志：https://lore.kernel.org/r/20140717193330.GB4703@kroah.com
- Linus Torvalds建议x32系统调用应优先兼容64位版本而非32位版本：https://lore.kernel.org/r/CA+55aFxfmwfB7jbbrXxa=K7VBYPfAvmu3XOkGrLbB1UFjX1+Ew@mail.gmail.com
