添加一个新的系统调用
========================

本文档描述了在 Linux 内核中添加新的系统调用所需的过程，除了在 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 中提供的常规提交建议外。系统调用的替代方案
------------------------

在添加新的系统调用时，首先需要考虑的是是否存在更合适的替代方案。尽管系统调用是最传统且最明显的用户空间与内核之间的交互点，但还有其他可能性——选择最适合您接口的方式：
- 如果涉及的操作可以被设计成类似文件系统的对象，那么创建一个新的文件系统或设备可能更有意义。这也有助于将新功能封装到一个内核模块中，而不是要求它被构建到主内核中。
- 如果新功能涉及内核通知用户空间某些事件的发生，则返回相关对象的新文件描述符可以让用户空间使用 `poll`/`select`/`epoll` 来接收该通知。
- 然而，那些不能映射为 `read(2)`/`write(2)` 类似操作的则必须作为 `ioctl(2)` 请求实现，这可能导致较为晦涩的API。
- 如果只是暴露运行时系统信息，那么在 sysfs（参见 `Documentation/filesystems/sysfs.rst`）或者 `/proc` 文件系统中新增一个节点可能更为合适。然而，访问这些机制需要相关的文件系统已挂载，而这可能并非总是可行（例如，在命名空间/沙箱/chroot 环境中）。避免向 debugfs 添加任何 API，因为这不被认为是面向用户空间的“生产”接口。
- 如果操作特定于某个文件或文件描述符，那么新增一个 `fcntl(2)` 命令选项可能更合适。然而，`fcntl(2)` 是一个多路复用的系统调用，隐藏了许多复杂性，因此这个选项最好用于与现有 `fcntl(2)` 功能相似的新功能，或者新功能非常简单（例如，获取/设置与文件描述符相关的简单标志）。
- 如果操作特定于某个任务或进程，那么新增一个 `prctl(2)` 命令选项可能更合适。与 `fcntl(2)` 类似，这个系统调用是一个复杂的多路复用器，因此最好保留给与现有 `prctl()` 命令接近的功能或获取/设置与进程相关的简单标志。

设计 API：规划扩展性
------------------------------

一个新的系统调用是内核 API 的一部分，并需要无限期地支持下去。因此，明确讨论该接口并在内核邮件列表上进行讨论是一个非常好的主意，并且重要的是要为未来的接口扩展做计划。
### 从历史中学习并为扩展做好准备

系统调用表充满了未能预见未来扩展需求的历史例子，以及相应的后续系统调用——例如 `eventfd`/`eventfd2`、`dup2`/`dup3`、`inotify_init`/`inotify_init1`、`pipe`/`pipe2`、`renameat`/`renameat2` ——因此要从内核的历史中吸取教训，并从一开始就为扩展性做好规划。

对于只需要几个参数的简单系统调用，推荐的方法是在系统调用中包含一个标志参数。为了确保用户空间程序可以在不同内核版本间安全地使用这些标志，需要检查标志值是否包含未知标志，并在存在未知标志时拒绝该系统调用（返回 `EINVAL`）：

```c
if (flags & ~(THING_FLAG1 | THING_FLAG2 | THING_FLAG3))
    return -EINVAL;
```

如果没有使用任何标志值，应检查标志参数是否为零。

对于更复杂的系统调用，涉及较多参数的情况，推荐将大部分参数封装到一个通过指针传递的结构体中。这样的结构体可以通过包含一个大小参数来应对未来的扩展：

```c
struct xyzzy_params {
    u32 size; /* 用户空间设置 p->size = sizeof(struct xyzzy_params) */
    u32 param_1;
    u64 param_2;
    u64 param_3;
};
```

只要随后添加的字段（如 `param_4`）设计为零值表示先前的行为，则可以支持两个方向上的版本不匹配：

- 为了处理较新的用户空间程序调用较旧的内核，内核代码应该检查超出其期望的结构体大小的任何内存是否为零（实际上是在检查 `param_4 == 0`）
- 为了处理较旧的用户空间程序调用较新的内核，内核代码可以对较小的结构体实例进行零扩展（实际上设置了 `param_4 = 0`）

参见 `perf_event_open(2)` 和 `perf_copy_attr()` 函数（位于 `kernel/events/core.c`）作为此方法的一个示例。

### 设计API：其他考虑

如果你的新系统调用允许用户空间引用内核对象，应该使用文件描述符作为该对象的句柄——不要发明新的用户空间对象句柄类型，当内核已经具备使用文件描述符的机制和明确语义时。

如果你的新 `xyzzy(2)` 系统调用返回一个新的文件描述符，那么标志参数应该包括一个与设置 `O_CLOEXEC` 相当的值。这使得用户空间能够在 `xyzzy()` 和调用 `fcntl(fd, F_SETFD, FD_CLOEXEC)` 之间关闭时间窗口，在此期间，另一个线程中的意外 `fork()` 和 `execve()` 可能会泄露描述符给执行的程序。

如果你的系统调用返回一个新的文件描述符，还应考虑使用 `poll(2)` 系列系统调用对该文件描述符意味着什么。使文件描述符准备好读取或写入是内核通常用来向用户空间指示对应内核对象上发生事件的方式。

如果你的新 `xyzzy(2)` 系统调用涉及到一个文件名参数：

```c
int sys_xyzzy(const char __user *path, ..., unsigned int flags);
```

还应考虑 `xyzzyat(2)` 版本是否更为合适：

```c
int sys_xyzzyat(int dfd, const char __user *path, ..., unsigned int flags);
```

这为用户空间指定文件提供了更多灵活性；特别是它允许用户空间使用 `AT_EMPTY_PATH` 标志请求已打开文件描述符的功能，有效地提供了一个免费的 `fxyzzy(3)` 操作：

- `xyzzyat(AT_FDCWD, path, ..., 0)` 等效于 `xyzzy(path,...)`
- `xyzzyat(fd, "", ..., AT_EMPTY_PATH)` 等效于 `fxyzzy(fd, ...)`

（关于 \*at() 调用的原理详情，请参阅 `openat(2)` 手册页；关于 `AT_EMPTY_PATH` 的示例，请参阅 `fstatat(2)` 手册页。）

如果你的新 `xyzzy(2)` 系统调用涉及到描述文件内的偏移量的参数，应将其类型设为 `loff_t`，以便在 32 位架构上也能支持 64 位偏移量。

如果你的新 `xyzzy(2)` 系统调用涉及到特权功能，它需要由适当的 Linux 权限位控制（通过调用 `capable()` 进行检查），具体描述参见 `capabilities(7)` 手册页。选择控制相关功能的现有权限位，但尽量避免将许多只有微弱关联的功能组合在同一个位下，因为这违背了权限的目的——即分割 root 的权力。特别地，应避免为已经过于通用的 `CAP_SYS_ADMIN` 权限添加新用途。

如果你的新 `xyzzy(2)` 系统调用操纵的是除调用进程之外的其他进程，应该受到限制（通过调用 `ptrace_may_access()`），使得只有具有与目标进程相同权限或者必要权限的调用进程才能操纵目标进程。

最后，要注意一些非 x86 架构在 64 位参数显式位于奇数位置（即参数 1、3、5）时更容易处理，以允许使用连续的 32 位寄存器对。如果参数是通过指针传递的结构体的一部分，则不需要担心这个问题。

### 提出API

为了使新系统调用易于审查，最好将补丁集分成独立的部分。至少应包括以下项作为单独的提交（每项下面有更详细的描述）：

- 系统调用的核心实现，包括原型、通用编号、Kconfig 更改和回退存根实现。
- 为特定架构（通常是 x86，包括所有 x86_64、x86_32 和 x32）连接新系统调用。
新系统调用演示，通过用户空间的一个自测程序在 ``tools/testing/selftests/`` 中进行。
新系统调用的手册页草案，可以是封面信中的纯文本形式，或者是对（独立的）手册页仓库的一块补丁。
对于内核API的任何变更，包括新的系统调用提案，都应该抄送给 linux-api@vger.kernel.org。

### 通用系统调用实现

为你的新 `xyzzy(2)` 系统调用设置的主要入口点将被称为 `sys_xyzzy()`，但你应该使用适当的 `SYSCALL_DEFINEn()` 宏来添加这个入口点而不是直接定义。这里的 'n' 表示系统调用参数的数量，宏接受系统调用名称及参数类型和名称作为参数。使用此宏可以让有关新系统调用的元数据可供其他工具使用。

新入口点还需要一个函数原型，位于 `include/linux/syscalls.h` 中，并标记为 `asmlinkage` 来匹配系统调用的调用方式：

```c
asmlinkage long sys_xyzzy(...);
```

一些架构（如 x86）有自己的架构特定的系统调用表，但许多其他架构共享一个通用系统调用表。通过向 `include/uapi/asm-generic/unistd.h` 文件中添加条目来将你的新系统调用添加到通用列表中：

```c
#define __NR_xyzzy 292
__SYSCALL(__NR_xyzzy, sys_xyzzy)
```

同时更新 `__NR_syscalls` 计数以反映新增加的系统调用，并注意如果在同一合并窗口中添加了多个新的系统调用，你的新系统调用编号可能需要调整以解决冲突。

文件 `kernel/sys_ni.c` 提供了一个每个系统调用的回退存根实现，返回 `-ENOSYS`。也在这里添加你的新系统调用：

```c
COND_SYSCALL(xyzzy);
```

你的新内核功能及其控制的系统调用通常应该是可选的，因此在 `init/Kconfig`（通常是这里）中添加一个 `CONFIG` 选项。对于新的 `CONFIG` 选项通常要遵循以下规则：

- 包含由该选项控制的新功能和系统调用的描述
- 如果应该隐藏于普通用户，则使该选项依赖于 `EXPERT`
- 在 Makefile 中使任何实现该功能的新源文件依赖于 `CONFIG` 选项（例如 `obj-$(CONFIG_XYZZY_SYSCALL) += xyzzy.o`）
- 双重检查确保关闭新 `CONFIG` 选项时内核仍然能够构建

总结一下，你需要一个包含以下内容的提交：

- 新功能的 `CONFIG` 选项，通常位于 `init/Kconfig` 中
- 入口点的 `SYSCALL_DEFINEn(xyzzy, ...)` 
- 对应的原型在 `include/linux/syscalls.h` 中
- 通用表条目在 `include/uapi/asm-generic/unistd.h` 中
- 回退存根在 `kernel/sys_ni.c` 中

### x86 系统调用实现

为了在 x86 平台上设置你的新系统调用，你需要更新主系统调用表。假设你的新系统调用没有特殊之处（见下文），这涉及到在 `arch/x86/entry/syscalls/syscall_64.tbl` 中的“common”条目（用于 x86_64 和 x32）：

```plaintext
333   common   xyzzy     sys_xyzzy
```

以及在 `arch/x86/entry/syscalls/syscall_32.tbl` 中的 “i386” 条目：

```plaintext
380   i386     xyzzy     sys_xyzzy
```

这些数字可能会因为相关合并窗口中的冲突而发生变化。
### 兼容性系统调用（通用）

对于大多数系统调用，即使用户空间程序本身是32位的，也可以调用相同的64位实现；即使系统调用的参数包含一个显式的指针，这也被透明地处理。然而，存在几种情况需要一个兼容层来应对32位与64位之间的大小差异。

第一种情况是如果64位内核也支持32位用户空间程序，并因此需要解析可能包含32位或64位值的（`__user`）内存区域。特别是，当系统调用参数是以下情况时需要这样做：

- 指向指针的指针
- 指向包含指针的结构体（例如 `struct iovec __user *`）
- 指向可变大小整型（`time_t`、`off_t`、`long`等）
- 指向包含可变大小整型的结构体

第二种需要兼容层的情况是如果系统调用的一个参数具有在32位架构上也是明确64位的类型，例如`loff_t`或`__u64`。在这种情况下，从32位应用程序到达64位内核的值将被分成两个32位值，然后需要在兼容层中重新组合。

（注意：指向明确64位类型的指针作为系统调用参数**不需要**兼容层；例如，`splice(2)`的类型为`loff_t __user *`的参数不会触发对`compat_`系统调用的需求。）

兼容版本的系统调用称为`compat_sys_xyzzy()`，并使用`COMPAT_SYSCALL_DEFINEn()`宏添加，类似于SYSCALL_DEFINEn。这个版本的实现运行在64位内核的一部分，但期望接收32位参数值，并执行所需的操作来处理这些值。（通常，`compat_sys_`版本会将这些值转换为64位版本，并调用`sys_`版本，或者两者都调用一个共同的内部实现函数。）

兼容入口点还需要一个相应的函数原型，在`include/linux/compat.h`中，标记为asmlinkage以匹配系统调用的调用方式：

```c
asmlinkage long compat_sys_xyzzy(...);
```

如果系统调用涉及一个在32位和64位系统上布局不同的结构，比如`struct xyzzy_args`，那么`include/linux/compat.h`头文件还应该包括该结构的兼容版本（`struct compat_xyzzy_args`），其中每个可变大小字段都有与`struct xyzzy_args`中的类型相对应的适当`compat_`类型。然后`compat_sys_xyzzy()`例程可以使用此`compat_`结构来解析来自32位调用的参数。
例如，如果有字段：
```c
struct xyzzy_args {
    const char __user *ptr;
    __kernel_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```
在`struct xyzzy_args`中，那么`struct compat_xyzzy_args`会有：
```c
struct compat_xyzzy_args {
    compat_uptr_t ptr;
    compat_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```

通用系统调用列表也需要调整以考虑兼容版本；`include/uapi/asm-generic/unistd.h`中的条目应使用`__SC_COMP`而不是`__SYSCALL`：

```c
#define __NR_xyzzy 292
__SC_COMP(__NR_xyzzy, sys_xyzzy, compat_sys_xyzzy)
```

总结，你需要：

- 一个`COMPAT_SYSCALL_DEFINEn(xyzzy, ...)`用于兼容入口点
- 在`include/linux/compat.h`中的相应原型
- （如果需要）32位映射结构在`include/linux/compat.h`中
- 在`include/uapi/asm-generic/unistd.h`中的`__SC_COMP`实例而非`__SYSCALL`

### 兼容性系统调用（x86）

为了设置具有兼容版本的x86架构系统调用，系统调用表中的条目需要进行调整。

首先，`arch/x86/entry/syscalls/syscall_32.tbl`中的条目增加一列来指示32位用户空间程序在64位内核上运行时应该命中兼容入口点：

```c
380   i386     xyzzy     sys_xyzzy    __ia32_compat_sys_xyzzy
```

其次，你需要确定新的系统调用的x32 ABI版本应该如何处理。这里有两种选择：参数的布局应该与64位版本相匹配，或者与32位版本相匹配。
如果涉及指向指针的指针，决定很容易：x32是ILP32，所以布局应该与32位版本相匹配，并且`arch/x86/entry/syscalls/syscall_64.tbl`中的条目被分割以便x32程序命中兼容包装器：

```c
333   64       xyzzy     sys_xyzzy
...
555   x32      xyzzy     __x32_compat_sys_xyzzy
```

如果没有指针参与，则最好重用64位系统调用用于x32 ABI（因此`arch/x86/entry/syscalls/syscall_64.tbl`中的条目不变）。
在任何情况下，你应该检查你参数布局中涉及的类型确实从x32 (-mx32)精确映射到32位 (-m32) 或64位 (-m64) 等效类型。
系统调用返回其他位置
------------------------------

对于大多数系统调用，一旦系统调用完成，用户程序会从暂停的地方继续执行——即下一条指令，堆栈、大部分寄存器以及虚拟内存空间与系统调用前相同。然而，有少数系统调用以不同的方式处理。它们可能会返回到不同的位置（如 `rt_sigreturn`），或者改变程序的内存空间（如 `fork`/`vfork`/`clone`），甚至改变程序的架构（如 `execve`/`execveat`）。
为了支持这些情况，内核实现可能需要在内核栈中保存和恢复额外的寄存器，以便完全控制系统调用后程序的执行位置和方式。这取决于具体的架构，但通常涉及定义汇编入口点来保存/恢复额外的寄存器，并调用真实的系统调用入口点。

对于x86_64架构，这是通过在 `arch/x86/entry/entry_64.S` 中实现一个名为 `stub_xyzzy` 的入口点来实现的，并且系统调用表（`arch/x86/entry/syscalls/syscall_64.tbl`）中的条目会被相应地调整，例如：

    333   common   xyzzy     stub_xyzzy

对于运行在64位内核上的32位程序，通常会有一个名为 `stub32_xyzzy` 的等效版本，并在 `arch/x86/entry/entry_64_compat.S` 中实现，相应的系统调用表调整在 `arch/x86/entry/syscalls/syscall_32.tbl` 中，例如：

    380   i386     xyzzy     sys_xyzzy    stub32_xyzzy

如果系统调用需要兼容层（如上一节所述），那么 `stub32_` 版本需要调用 `compat_sys_` 版本的系统调用，而不是原生的64位版本。此外，如果x32 ABI实现与x86_64版本不一致，则其系统调用表也需要调用一个存根，该存根再调用 `compat_sys_` 版本。

为了完整性，最好设置一个映射，使得用户模式Linux仍然可以工作——其系统调用表将引用 `stub_xyzzy`，但是UML构建不包含 `arch/x86/entry/entry_64.S` 实现（因为UML模拟寄存器等）。解决这个问题只需在 `arch/x86/um/sys_call_table_64.c` 中添加一个 `#define` 即可：

    #define stub_xyzzy sys_xyzzy

其他细节
-------------

内核的大部分部分以通用方式处理系统调用，但偶尔也会有一些特殊情况需要针对特定的系统调用进行更新。
审计子系统就是一个特殊案例；它包括（架构特定的）函数来分类某些特殊类型的系统调用——具体来说是文件打开 (`open`/`openat`)、程序执行 (`execve`/`execveat`) 或者套接字复用 (`socketcall`) 操作。如果你的新系统调用类似于这些之一，那么审计系统应该得到更新。
更普遍地说，如果存在一个与你的新系统调用类似的现有系统调用，值得在整个内核中使用grep搜索现有系统调用来检查是否有其他特殊情况。
测试
-------

显然，一个新的系统调用应当被测试；同时，向评审者提供一个示例来展示用户空间程序如何使用这个系统调用也是有用的。一种结合这两种目标的好方法是在 `tools/testing/selftests/` 目录下包含一个简单的自测程序。
对于新的系统调用，显然没有libc包装函数，因此测试需要使用 `syscall()` 来调用它；另外，如果系统调用涉及到新的用户空间可见结构，则需要安装相应的头文件来编译测试。
确保自检程序在所有支持的架构上都能成功运行。例如，检查它在编译为x86_64 (-m64)、x86_32 (-m32)和x32 (-mx32) ABI程序时是否能正常工作。
对于新功能进行更广泛和彻底的测试，您还应该考虑将测试添加到Linux测试项目中，或者对于与文件系统相关的更改，将其添加到xfstests项目中。
- [https://linux-test-project.github.io/](https://linux-test-project.github.io/)
- [git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git](git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git)

**手册页**
------------

所有新的系统调用都应该附带完整的手册页，理想情况下使用groff标记，但纯文本也可以接受。如果使用grooff，则在提交补丁集的封面邮件中包含预渲染的ASCII版本的手册页对审查者来说是有帮助的。
手册页应抄送给linux-man@vger.kernel.org。
更多详情，请参见[https://www.kernel.org/doc/man-pages/patches.html](https://www.kernel.org/doc/man-pages/patches.html)。

**不要在内核中调用系统调用**
-----------------------------------

如上所述，系统调用是用户空间与内核之间的交互点。因此，像`sys_xyzzy()`或`compat_sys_xyzzy()`这样的系统调用函数只应通过系统调用表从用户空间调用，而不是从内核中的其他地方调用。如果系统调用的功能对于在内核内部使用有用，需要在旧系统调用和新系统调用之间共享，或者需要在系统调用及其兼容变体之间共享，那么应该通过“辅助”函数（如`ksys_xyzzy()`）来实现。这个内核函数可以在系统调用存根（`sys_xyzzy()`）、兼容系统调用存根（`compat_sys_xyzzy()`）和其他内核代码中被调用。
至少在64位x86上，从v4.17开始，不在内核中调用系统调用函数将成为硬性要求。它为系统调用使用了不同的调用约定，在这种约定下，`struct pt_regs`在系统调用包装器中被实时解码，然后将处理权移交给实际的系统调用函数。
这意味着只有那些对于特定系统调用真正需要的参数才会在系统调用入口处传递，而不是一直填充六个CPU寄存器以随机用户空间内容（这可能会导致严重的麻烦）。
此外，对于内核数据和用户数据访问规则可能有所不同。这也是为什么调用`sys_xyzzy()`通常不是一个好主意的另一个原因。
对此规则的例外仅限于架构特定的覆盖、架构特定的兼容性包装器或其他位于arch/目录下的代码。

**参考资料和来源**
----------------------
- LWN文章：Michael Kerrisk关于在系统调用中使用标志参数的文章：[https://lwn.net/Articles/585415/](https://lwn.net/Articles/585415/)
- LWN文章：Michael Kerrisk关于如何处理系统调用中的未知标志的文章：[https://lwn.net/Articles/588444/](https://lwn.net/Articles/588444/)
- LWN文章：Jake Edge关于64位系统调用参数约束的描述：[https://lwn.net/Articles/311630/](https://lwn.net/Articles/311630/)
- LWN文章：David Drysdale详细描述了v3.14中的系统调用实现路径：
  - [https://lwn.net/Articles/604287/](https://lwn.net/Articles/604287/)
  - [https://lwn.net/Articles/604515/](https://lwn.net/Articles/604515/)
- 架构特定的系统调用需求在`syscall(2)`手册页中讨论：[http://man7.org/linux/man-pages/man2/syscall.2.html#NOTES](http://man7.org/linux/man-pages/man2/syscall.2.html#NOTES)
- Linus Torvalds讨论`ioctl()`问题的整理邮件：[https://yarchive.net/comp/linux/ioctl.html](https://yarchive.net/comp/linux/ioctl.html)
- “如何不发明内核接口”，Arnd Bergmann：[https://www.ukuug.org/events/linux2007/2007/papers/Bergmann.pdf](https://www.ukuug.org/events/linux2007/2007/papers/Bergmann.pdf)
- LWN文章：Michael Kerrisk关于避免新的CAP_SYS_ADMIN使用的文章：[https://lwn.net/Articles/486306/](https://lwn.net/Articles/486306/)
- Andrew Morton建议所有与新系统调用相关的信息都应在同一个邮件线程中提供：[https://lore.kernel.org/r/20140724144747.3041b208832bbdf9fbce5d96@linux-foundation.org](https://lore.kernel.org/r/20140724144747.3041b208832bbdf9fbce5d96@linux-foundation.org)
- Michael Kerrisk建议新系统调用应随附手册页：[https://lore.kernel.org/r/CAKgNAkgMA39AfoSoA5Pe1r9N+ZzfYQNvNPvcRN7tOvRb8+v06Q@mail.gmail.com](https://lore.kernel.org/r/CAKgNAkgMA39AfoSoA5Pe1r9N+ZzfYQNvNPvcRN7tOvRb8+v06Q@mail.gmail.com)
- Thomas Gleixner建议x86的配置应该在一个单独的提交中：[https://lore.kernel.org/r/alpine.DEB.2.11.1411191249560.3909@nanos](https://lore.kernel.org/r/alpine.DEB.2.11.1411191249560.3909@nanos)
- Greg Kroah-Hartman建议新系统调用最好附带手册页和自检程序：[https://lore.kernel.org/r/20140320025530.GA25469@kroah.com](https://lore.kernel.org/r/20140320025530.GA25469@kroah.com)
- Michael Kerrisk关于新系统调用与扩展`prctl(2)`的讨论：[https://lore.kernel.org/r/CAHO5Pa3F2MjfTtfNxa8LbnkeeU8=YJ+9tDqxZpw7Gz59E-4AUg@mail.gmail.com](https://lore.kernel.org/r/CAHO5Pa3F2MjfTtfNxa8LbnkeeU8=YJ+9tDqxZpw7Gz59E-4AUg@mail.gmail.com)
- Ingo Molnar建议涉及多个参数的系统调用应将这些参数封装在一个结构体中，其中包含一个大小字段以便未来扩展：[https://lore.kernel.org/r/20150730083831.GA22182@gmail.com](https://lore.kernel.org/r/20150730083831.GA22182@gmail.com)
- 由于重用O_*编号空间标志而产生的编号异常：
  - 提交75069f2b5bfb（"vfs: 重新编号FMODE_NONOTIFY并添加到唯一性检查"）
  - 提交12ed2e36c98a（"fanotify: FMODE_NONOTIFY和__O_SYNC在sparc中冲突"）
  - 提交bb458c644a59（"Safer ABI for O_TMPFILE"）
- Matthew Wilcox关于64位参数限制的讨论：[https://lore.kernel.org/r/20081212152929.GM26095@parisc-linux.org](https://lore.kernel.org/r/20081212152929.GM26095@parisc-linux.org)
- Greg Kroah-Hartman建议应监控未知标志：[https://lore.kernel.org/r/20140717193330.GB4703@kroah.com](https://lore.kernel.org/r/20140717193330.GB4703@kroah.com)
- Linus Torvalds建议x32系统调用应优先兼容64位版本而非32位版本：[https://lore.kernel.org/r/CA+55aFxfmwfB7jbbrXxa=K7VBYPfAvmu3XOkGrLbB1UFjX1+Ew@mail.gmail.com](https://lore.kernel.org/r/CA+55aFxfmwfB7jbbrXxa=K7VBYPfAvmu3XOkGrLbB1UFjX1+Ew@mail.gmail.com)
