添加一个新的系统调用
========================

本文档描述了在 Linux 内核中添加新的系统调用所需的过程，除了在 :ref:`Documentation/process/submitting-patches.rst <submittingpatches>` 中提供的常规提交建议外。系统调用的替代方案
------------------------

在添加新的系统调用时，首先需要考虑的是是否存在更合适的替代方案。尽管系统调用是最传统且最明显的用户空间与内核之间的交互点，但还有其他可能性——选择最适合您接口的方式。
- 如果涉及的操作可以被设计成类似文件系统的对象，那么创建一个新的文件系统或设备可能更有意义。这也有助于将新功能封装到一个内核模块中，而不是要求它必须集成到主内核中。
- 如果新功能涉及内核通知用户空间某些事件的发生，则返回相关对象的新文件描述符可以让用户空间使用 `poll`/`select`/`epoll` 来接收这些通知。
- 然而，那些无法映射为 `read(2)`/`write(2)` 类似操作的则需要通过 `ioctl(2)` 请求来实现，这可能导致一个较为不透明的API。
- 如果你只是公开运行时的系统信息，那么在 sysfs（参见 `Documentation/filesystems/sysfs.rst`）或者 `/proc` 文件系统中添加一个新节点可能更为合适。然而，访问这些机制需要相关的文件系统已经被挂载，而这在某些情况下可能不是始终成立的（例如，在命名空间/沙盒/chroot环境中）。避免向 debugfs 添加任何 API，因为它不被认为是面向用户空间的“生产级”接口。
- 如果操作是针对特定文件或文件描述符的，那么增加一个 `fcntl(2)` 命令选项可能更为合适。然而，`fcntl(2)` 是一个多路复用的系统调用，隐藏了很多复杂性，因此这个选项最适合于新功能与现有 `fcntl(2)` 功能非常相似的情况，或者新功能非常简单（例如，获取/设置与文件描述符相关的简单标志）。
- 如果操作是针对特定任务或进程的，那么增加一个 `prctl(2)` 命令选项可能更为合适。同 `fcntl(2)` 一样，这是一个复杂的多路复用器，因此最好保留给与现有 `prctl()` 命令近似的功能或获取/设置与进程相关的简单标志。

设计 API：为扩展做规划
------------------------------

一个新的系统调用是内核API的一部分，并且需要无限期地支持。因此，明确地在内核邮件列表上讨论接口是一个非常好的主意，并且重要的是要为未来的接口扩展做好规划。
系统调用表中充斥着历史遗留的例子，这些例子没有考虑到未来的扩展性，以及相应的后续系统调用——如`eventfd`/`eventfd2`、`dup2`/`dup3`、`inotify_init`/`inotify_init1`、`pipe`/`pipe2`、`renameat`/`renameat2`——因此，从内核的历史中学习，从一开始就规划好扩展性。

对于只需要几个参数的简单系统调用，允许未来扩展的首选方式是在系统调用中包含一个标志参数。为了确保用户空间程序在不同内核版本间可以安全地使用标志，检查标志值是否包含任何未知标志，并如果存在则拒绝系统调用（通过`EINVAL`）：

    if (flags & ~(THING_FLAG1 | THING_FLAG2 | THING_FLAG3))
        return -EINVAL;

（如果没有使用任何标志值，检查标志参数是否为零。）

对于涉及更多参数的更复杂的系统调用，更倾向于将大部分参数封装到一个通过指针传递的结构体中。这样的结构体可以通过在结构体中包含一个大小参数来应对未来的扩展：

    struct xyzzy_params {
        u32 size; /* 用户空间设置 p->size = sizeof(struct xyzzy_params) */
        u32 param_1;
        u64 param_2;
        u64 param_3;
    };

只要任何随后添加的字段，比如`param_4`，设计得使其零值给出先前的行为，那么这允许两个方向的版本不匹配：

 - 为了处理较新的用户空间程序调用较老的内核，内核代码应检查超出其期望的结构体大小的任何内存是否为零（实际上检查`param_4 == 0`）
- 为了处理较旧的用户空间程序调用较新的内核，内核代码可以将较小的结构体实例零填充（实际上设置`param_4 = 0`）
参见`perf_event_open(2)`手册页和`perf_copy_attr()`函数（在`kernel/events/core.c`中）作为此方法的一个示例。

设计API：其他考虑

如果你的新系统调用允许用户空间引用内核对象，它应该使用文件描述符作为该对象的句柄——不要在内核已经具有使用文件描述符的机制和明确定义的语义时发明新的用户空间对象句柄类型。
如果你的新`xyzzy(2)`系统调用确实返回一个新的文件描述符，那么标志参数应该包括一个与在新FD上设置`O_CLOEXEC`等效的值。这使得用户空间能够关闭`xyzzy()`和调用`fcntl(fd, F_SETFD, FD_CLOEXEC)`之间的时间窗口，在此期间另一个线程中的意外`fork()`和`execve()`可能会泄露描述符给被exec的程序。（然而，抵制住重用`O_CLOEXEC`常量的实际值的诱惑，因为它是架构特定的，并且是`O_*`标志的命名空间的一部分，这个空间相当满。）

如果你的系统调用返回一个新的文件描述符，你也应该考虑在该文件描述符上使用`poll(2)`家族系统调用意味着什么。使文件描述符准备好读取或写入是内核向用户空间指示相应内核对象上发生事件的正常方式。

如果你的新`xyzzy(2)`系统调用涉及文件名参数：

    int sys_xyzzy(const char __user *path, ..., unsigned int flags);

你也应该考虑`xyzzyat(2)`版本是否更合适：

    int sys_xyzzyat(int dfd, const char __user *path, ..., unsigned int flags);

这为用户空间指定文件提供了更多灵活性；特别是它允许用户空间使用`AT_EMPTY_PATH`标志请求对已打开的文件描述符的功能，有效地提供了一个`fxyzzy(3)`操作：

 - `xyzzyat(AT_FDCWD, path, ..., 0)`相当于`xyzzy(path,...)`
 - `xyzzyat(fd, "", ..., AT_EMPTY_PATH)`相当于`fxyzzy(fd, ...)`

（有关\*at()调用的理由的更多细节，请参阅`openat(2)`手册页；有关`AT_EMPTY_PATH`的示例，请参阅`fstatat(2)`手册页。）

如果你的新`xyzzy(2)`系统调用涉及描述文件内偏移的参数，使其类型为`loff_t`，以便即使在32位架构上也能支持64位偏移。
如果你的新`xyzzy(2)`系统调用涉及特权功能，它需要由适当的Linux能力位控制（通过调用`capable()`进行检查），如`capabilities(7)`手册页所述。选择控制相关功能的现有能力位，但尽量避免将大量仅模糊相关的功能组合在同一个位下，因为这违背了能力的目的，即分割root的权力。特别地，避免为已经过于通用的`CAP_SYS_ADMIN`能力添加新用途。
如果你的新`xyzzy(2)`系统调用操纵除了调用进程之外的进程，它应该受到限制（通过调用`ptrace_may_access()`），这样只有具有与目标进程相同权限或具有必要能力的调用进程才能操纵目标进程。
最后，要注意的是，一些非x86架构在系统调用参数显式为64位时，如果它们落在奇数位置（即参数1、3、5），会更容易处理，以允许使用连续的32位寄存器对。 （如果参数是通过指针传递的结构体的一部分，则不需要担心这个问题。）

提出API

为了让新系统调用易于审查，最好将补丁集分成独立的部分。这些应至少包括以下项作为单独的提交（每项下面有更详细的描述）：

 - 系统调用的核心实现，连同原型、通用编号、Kconfig更改和回退存根实现
- 将新系统调用针对特定架构的连线，通常是x86（包括所有x86_64、x86_32和x32）。
新系统调用演示，通过用户空间的一个自测程序在 ``tools/testing/selftests/`` 中进行。
新系统调用的手册页草案，可以是封面信中的纯文本形式，或者是对（独立的）man-pages仓库的一块补丁。
对于新系统调用提案，如同内核API的任何变更一样，应当始终抄送给 linux-api@vger.kernel.org。
通用系统调用实现
-------------------

你新提出的 :manpage:`xyzzy(2)` 系统调用的主要入口点将被称为 ``sys_xyzzy()``，但你应该使用适当的 ``SYSCALL_DEFINEn()`` 宏添加此入口点而不是显式地定义它。这里的 'n' 表示系统调用的参数数量，并且宏接受系统调用名称及其参数的 (类型, 名称) 对作为参数。使用这个宏可以让关于新系统调用的元数据为其他工具所用。
新入口点还需要一个对应的函数原型，在 ``include/linux/syscalls.h`` 中声明，并标记为 asmlinkage 来匹配系统调用被调用的方式：

    asmlinkage long sys_xyzzy(...);

一些架构（例如 x86）有自己的特定于架构的系统调用表，但许多其他架构共享一个通用系统调用表。通过向 ``include/uapi/asm-generic/unistd.h`` 中的列表添加条目来将你的新系统调用加入到通用列表中：

    #define __NR_xyzzy 292
    __SYSCALL(__NR_xyzzy, sys_xyzzy)

同时更新 __NR_syscalls 的计数以反映新增加的系统调用，并请注意，如果在同一合并窗口中添加了多个新的系统调用，则你的新系统调用编号可能会被调整以解决冲突。
文件 ``kernel/sys_ni.c`` 提供了一个回退存根实现，为每个系统调用返回 ``-ENOSYS``。也在这里添加你的新系统调用：

    COND_SYSCALL(xyzzy);

通常情况下，你的新内核功能及其控制它的系统调用应该是可选的，因此应该添加一个 ``CONFIG`` 选项（通常添加到 ``init/Kconfig``）。对于新的 ``CONFIG`` 选项，通常包括：

 - 描述由该选项控制的新功能和系统调用
- 如果该选项应隐藏于普通用户，则使其依赖于 EXPERT
- 在 Makefile 中使任何实现该功能的新源文件依赖于 CONFIG 选项（例如：``obj-$(CONFIG_XYZZY_SYSCALL) += xyzzy.o``）
- 双重检查当新的 CONFIG 选项关闭时内核是否仍然能够构建
总结来说，你需要包含以下内容的提交：

 - 新功能的 ``CONFIG`` 选项，通常位于 ``init/Kconfig``
 - 使用 ``SYSCALL_DEFINEn(xyzzy, ...)`` 的入口点
 - 在 ``include/linux/syscalls.h`` 中对应的原型
 - 在 ``include/uapi/asm-generic/unistd.h`` 中的通用表项
 - 在 ``kernel/sys_ni.c`` 中的回退存根

x86 系统调用实现
------------------

为了在 x86 平台上设置你的新系统调用，你需要更新主系统调用表。假设你的新系统调用没有特殊之处（见下文），这涉及到 arch/x86/entry/syscalls/syscall_64.tbl 中的 "common" 入口（用于 x86_64 和 x32）：

    333   common   xyzzy     sys_xyzzy

以及 arch/x86/entry/syscalls/syscall_32.tbl 中的 "i386" 入口：

    380   i386     xyzzy     sys_xyzzy

同样地，这些数字可能会在相关合并窗口中有冲突时发生变化。
### 兼容性系统调用（通用）

对于大多数系统调用，即使用户空间程序本身是32位的，也可以调用相同的64位实现；即使系统调用的参数包含一个显式指针，这也被透明处理。然而，在两种情况下需要一个兼容层来处理32位与64位之间的大小差异：
- 第一种情况是如果64位内核还支持32位用户空间程序，并且因此需要解析可能包含32位或64位值的(``__user``)内存区域。特别是，当系统调用参数是以下情况时需要这样做：
  - 指向指针的指针
  - 指向包含指针的结构体（例如``struct iovec __user *``）
  - 指向可变长度整型（``time_t``、``off_t``、``long``等）
  - 指向包含可变长度整型的结构体
- 第二种需要兼容层的情况是如果系统调用的一个参数具有在32位架构上也是明确64位的类型，例如``loff_t``或``__u64``。在这种情况下，从32位应用程序传到64位内核的值将被拆分为两个32位值，然后需要在兼容层中重新组装。

兼容版本的系统调用称为``compat_sys_xyzzy()``，使用``COMPAT_SYSCALL_DEFINEn()``宏添加，类似于SYSCALL_DEFINEn。这个版本的实现在64位内核中运行，但期望接收32位参数值，并进行必要的处理。（通常，“compat_sys_”版本会将这些值转换为64位版本并调用“sys_”版本，或者两者都调用一个公共的内部实现函数。）

兼容入口点还需要在``include/linux/compat.h``中有相应的函数原型，标记为asmlinkage以匹配系统调用的调用方式：

```c
asmlinkage long compat_sys_xyzzy(...);
```

如果系统调用涉及一个在32位和64位系统上布局不同的结构，比如``struct xyzzy_args``，那么include/linux/compat.h头文件也应该包含该结构的兼容版本（``struct compat_xyzzy_args``），其中每个变量大小字段具有与``struct xyzzy_args``中的类型对应的适当``compat_``类型。“compat_sys_xyzzy()”例程可以使用这个“compat_”结构来解析来自32位调用的参数。
例如，如果``struct xyzzy_args``中有如下字段：

```c
struct xyzzy_args {
    const char __user *ptr;
    __kernel_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```

则``struct compat_xyzzy_args``会有如下定义：

```c
struct compat_xyzzy_args {
    compat_uptr_t ptr;
    compat_long_t varying_val;
    u64 fixed_val;
    /* ... */
};
```

通用系统调用列表也需要调整以允许兼容版本；在``include/uapi/asm-generic/unistd.h``中的条目应该使用``__SC_COMP``而不是``__SYSCALL``：

```c
#define __NR_xyzzy 292
__SC_COMP(__NR_xyzzy, sys_xyzzy, compat_sys_xyzzy)
```

总结，你需要：
- 一个``COMPAT_SYSCALL_DEFINEn(xyzzy, ...)``用于兼容入口点
- 在``include/linux/compat.h``中的相应原型
- （如果需要）32位映射结构在``include/linux/compat.h``中
- 在``include/uapi/asm-generic/unistd.h``中使用``__SC_COMP``而不是``__SYSCALL``的实例

### 兼容性系统调用（x86）

为了将具有兼容版本的系统调用连接到x86架构，需要调整系统调用表中的条目。
首先，在``arch/x86/entry/syscalls/syscall_32.tbl``中的条目增加一列以指示运行在64位内核上的32位用户空间程序应该命中兼容入口点：

```plaintext
380   i386     xyzzy     sys_xyzzy    __ia32_compat_sys_xyzzy
```

其次，你需要确定新的系统调用的x32 ABI版本应该发生什么。这里有选择：参数布局应该要么匹配64位版本要么匹配32位版本。
如果有指向指针的指针涉及，则决定很容易：x32是ILP32，所以布局应该匹配32位版本，并且在``arch/x86/entry/syscalls/syscall_64.tbl``中的条目被拆分以便x32程序命中兼容包装器：

```plaintext
333   64       xyzzy     sys_xyzzy
...
555   x32      xyzzy     __x32_compat_sys_xyzzy
```

如果没有涉及指针，则更倾向于为x32 ABI重用64位系统调用（因此在``arch/x86/entry/syscalls/syscall_64.tbl``中的条目不变）。
无论哪种情况，你应该检查你的参数布局中涉及的类型确实精确地从x32 (-mx32)映射到32位(-m32)或64位(-m64)等价物。
返回其他位置的系统调用
------------------------------

对于大多数系统调用，一旦系统调用完成，用户程序将从它中断的地方继续执行——即下一条指令，堆栈、大部分寄存器以及虚拟内存空间与系统调用之前相同。然而，有些系统调用以不同的方式处理。它们可能返回到不同的位置（如 `rt_sigreturn`），或者改变程序的内存空间（如 `fork`/`vfork`/`clone`），甚至改变程序的架构（如 `execve`/`execveat`）。

为了允许这些操作，内核实现的系统调用可能需要在内核栈上保存和恢复额外的寄存器，以便完全控制系统调用后程序的执行流程和位置。这是架构特定的，但通常涉及到定义汇编入口点来保存/恢复额外的寄存器，并调用真实的系统调用入口点。

对于x86_64架构，这实现在 `arch/x86/entry/entry_64.S` 的 `stub_xyzzy` 入口点中，系统调用表（`arch/x86/entry/syscalls/syscall_64.tbl`）中的条目被调整为匹配如下所示：

    333   common   xyzzy     stub_xyzzy

对于运行在64位内核上的32位程序，通常称为 `stub32_xyzzy` 并实现在 `arch/x86/entry/entry_64_compat.S` 中，在 `arch/x86/entry/syscalls/syscall_32.tbl` 中进行相应的系统调用表调整，例如：

    380   i386     xyzzy     sys_xyzzy    stub32_xyzzy

如果系统调用需要兼容层（如前一节所述），则 `stub32_` 版本需要调用兼容版本 `compat_sys_` 的系统调用而不是原生的64位版本。此外，如果x32 ABI实现不与x86_64版本通用，则其系统调用表也需要调用一个存根，该存根再调用 `compat_sys_` 版本。

为了完整性，设置一个映射使用户模式Linux仍然工作也是好的——其系统调用表将引用 `stub_xyzzy`，但UML构建不包括 `arch/x86/entry/entry_64.S` 实现（因为UML模拟寄存器等）。修复这一点只需在 `arch/x86/um/sys_call_table_64.c` 中添加一个 `#define` 即可：

    #define stub_xyzzy sys_xyzzy

其他细节
-------------

内核的大部分部分以通用的方式处理系统调用，但也有一些特殊情况可能需要针对您的特定系统调用进行更新。
审计子系统就是这样一个特殊案例；它包括（架构特定的）函数，用于分类某些特殊类型的系统调用——具体来说是文件打开（`open`/`openat`）、程序执行（`execve`/`execveat`）或套接字复用（`socketcall`）操作。如果您新的系统调用与这些之一类似，则应更新审计系统。

更一般地说，如果有现有的系统调用与您的新系统调用类似，值得在整个内核中使用grep搜索现有的系统调用来检查是否有其他特殊情况。

测试
-------

显然，新的系统调用应该经过测试；同时也有必要向评审者提供一个演示，展示用户空间程序如何使用该系统调用。一个结合这些目标的好方法是在 `tools/testing/selftests/` 下新建目录并包含一个简单的自测程序。

对于一个新的系统调用，显然不会有libc包装函数，因此测试需要使用 `syscall()` 来调用它；此外，如果系统调用涉及一个新的用户空间可见结构，则需要安装相应的头文件以编译测试。
确保在所有支持的架构上自检能够成功运行。例如，检查当被编译为x86_64（-m64）、x86_32（-m32）和x32（-mx32）ABI程序时，它是否能够工作。
对于新功能进行更广泛和彻底的测试，你也应该考虑将测试添加到Linux测试项目中，或者对于与文件系统相关的更改，将其添加到xfstests项目中。
- https://linux-test-project.github.io/
- git://git.kernel.org/pub/scm/fs/xfs/xfstests-dev.git

手册页
------
所有新的系统调用都应附带完整的手册页，理想情况下使用groff标记，但纯文本也可以。如果使用groff，将预渲染的ASCII版本的手册页包含在补丁集的封面邮件中对审阅者来说会很有帮助。
手册页应抄送给linux-man@vger.kernel.org
更多细节，请参见https://www.kernel.org/doc/man-pages/patches.html

不要在内核中调用系统调用
-----------------------------
如上所述，系统调用是用户空间与内核之间的交互点。因此，像“sys_xyzzy()”或“compat_sys_xyzzy()”这样的系统调用函数只应通过系统调用表从用户空间调用，而不是在内核的其他地方调用。如果系统调用的功能对于在内核内部使用有用，需要在旧的和新的系统调用之间共享，或者需要在系统调用及其兼容变体之间共享，它应通过“辅助”函数（如“ksys_xyzzy()”）实现。这个内核函数然后可以在系统调用存根（“sys_xyzzy()”）、兼容系统调用存根（“compat_sys_xyzzy()”）和其他内核代码中调用。
至少在64位x86上，从v4.17开始，不在内核中调用系统调用函数将成为硬性要求。它为系统调用使用了不同的调用约定，在系统调用包装器中实时解码“struct pt_regs”，然后将处理移交给实际的系统调用函数。
这意味着只有特定系统调用实际需要的参数才会在系统调用入口时传递，而不是一直用随机用户空间内容填充六个CPU寄存器（这可能会在调用链中引起严重问题）。
此外，内核数据和用户数据之间的数据访问规则可能不同。这也是为什么调用“sys_xyzzy()”通常不是一个好主意的另一个原因。
仅在架构特定的覆盖、架构特定的兼容包装器或其他arch/中的代码中允许有此规则的例外。

参考和来源
----------------------
- LWN文章，Michael Kerrisk关于系统调用中flags参数的使用：https://lwn.net/Articles/585415/
- LWN文章，Michael Kerrisk关于如何处理系统调用中的未知标志：https://lwn.net/Articles/588444/
- LWN文章，Jake Edge描述了对64位系统调用参数的限制：https://lwn.net/Articles/311630/
- LWN文章，David Drysdale详细描述了v3.14中系统调用的实现路径：
    - https://lwn.net/Articles/604287/
    - https://lwn.net/Articles/604515/
- 架构特定的系统调用要求在：manpage:`syscall(2)`手册页中讨论：
   http://man7.org/linux/man-pages/man2/syscall.2.html#NOTES
- Linus Torvalds汇总的电子邮件，讨论“ioctl()”的问题：
   https://yarchive.net/comp/linux/ioctl.html
- “如何不发明内核接口”，Arnd Bergmann，
   https://www.ukuug.org/events/linux2007/2007/papers/Bergmann.pdf
- LWN文章，Michael Kerrisk关于避免CAP_SYS_ADMIN的新用途：
   https://lwn.net/Articles/486306/
- Andrew Morton建议所有关于新系统调用的相关信息应在同一邮件线程中：
   https://lore.kernel.org/r/20140724144747.3041b208832bbdf9fbce5d96@linux-foundation.org
- Michael Kerrisk建议新系统调用应附带手册页：
   https://lore.kernel.org/r/CAKgNAkgMA39AfoSoA5Pe1r9N+ZzfYQNvNPvcRN7tOvRb8+v06Q@mail.gmail.com
- Thomas Gleixner建议x86的连线应该在单独的提交中：
   https://lore.kernel.org/r/alpine.DEB.2.11.1411191249560.3909@nanos
- Greg Kroah-Hartman建议新系统调用附带手册页和自检是好的：
   https://lore.kernel.org/r/20140320025530.GA25469@kroah.com
- Michael Kerrisk讨论新系统调用与：manpage:`prctl(2)`扩展之间的区别：
   https://lore.kernel.org/r/CAHO5Pa3F2MjfTtfNxa8LbnkeeU8=YJ+9tDqxZpw7Gz59E-4AUg@mail.gmail.com
- Ingo Molnar建议涉及多个参数的系统调用应将这些参数封装在一个结构中，其中包含一个大小字段以供将来扩展：
   https://lore.kernel.org/r/20150730083831.GA22182@gmail.com
- 由于（重）使用O_*编号空间标志而产生的编号异常：

    - 提交75069f2b5bfb（“vfs：重新编号FMODE_NONOTIFY并添加到唯一性检查”）
    - 提交12ed2e36c98a（“fanotify：FMODE_NONOTIFY和__O_SYNC在sparc冲突”）
    - 提交bb458c644a59（“Safer ABI for O_TMPFILE”）

- Matthew Wilcox关于64位参数限制的讨论：
   https://lore.kernel.org/r/20081212152929.GM26095@parisc-linux.org
- Greg Kroah-Hartman建议应控制未知标志：
   https://lore.kernel.org/r/20140717193330.GB4703@kroah.com
- Linus Torvalds建议x32系统调用应优先与64位版本兼容而非32位版本：
   https://lore.kernel.org/r/CA+55aFxfmwfB7jbbrXxa=K7VBYPfAvmu3XOkGrLbB1UFjX1+Ew@mail.gmail.com
