===========================================
Seccomp BPF（使用过滤器的安全计算）
===========================================

介绍
============

大量的系统调用暴露给每个用户空间进程，其中许多在整个进程生命周期中从未被使用。随着系统调用的变更和发展，发现并修复了漏洞。某些用户空间应用程序通过减少可用的系统调用集而受益。这样可以减少暴露给应用程序的内核表面。系统调用过滤旨在用于这些应用程序。Seccomp过滤提供了一种机制，允许进程为传入的系统调用指定一个过滤器。该过滤器表示为一个Berkeley包过滤器（BPF）程序，就像套接字过滤器一样，只是操作的数据与所进行的系统调用相关：系统调用编号和系统调用参数。这使得能够使用一种历史悠久且暴露于用户空间的过滤器程序语言来表达性地过滤系统调用。此外，BPF使Seccomp用户不可能受到常见的检查时间使用时间（TOCTOU）攻击的影响。BPF程序不允许对指针进行解引用，这将所有过滤器限制为仅直接评估系统调用参数。
它不是什么
=============

系统调用过滤不是一个沙箱。它提供了一个明确的机制来最小化暴露的内核表面。其目的是作为沙箱开发人员使用的工具。除此之外，逻辑行为和信息流策略应通过其他系统加固技术和可能选择的LSM来管理。表达式动态过滤提供了进一步的选择（例如避免病理性大小或选择socketcall()中的哪些多路复用系统调用是允许的），这可能会被错误地认为是一种更完整的沙箱解决方案。
使用方法
=====

增加了一个额外的Seccomp模式，并使用与严格的Seccomp相同的prctl(2)调用来启用。如果架构具有``CONFIG_HAVE_ARCH_SECCOMP_FILTER``，则可以按如下方式添加过滤器：

``PR_SET_SECCOMP``：
现在接受一个额外的参数，该参数指定使用BPF程序的新过滤器
BPF程序将在struct seccomp_data上执行，反映系统调用编号、参数和其他元数据。然后，BPF程序必须返回一个可接受的值以通知内核应采取的操作
使用方法如下：

```
	prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, prog);
```

'prog'参数是指向struct sock_fprog的指针，其中包含过滤程序。如果程序无效，则调用将返回-1并将errno设置为``EINVAL``。
如果@prog允许``fork``/``clone``和``execve``，任何子进程将受限于与父进程相同的过滤器和系统调用ABI。
在使用之前，任务必须调用``prctl(PR_SET_NO_NEW_PRIVS, 1)``或在其命名空间中以``CAP_SYS_ADMIN``权限运行。如果没有满足这些条件，则返回``-EACCES``。此要求确保过滤程序不能应用于具有更高权限的子进程。
此外，如果 `prctl(2)` 被附加的过滤器允许，则可以增加额外的过滤层，这将增加评估时间，但可以在进程执行期间进一步减少攻击面。

上述调用在成功时返回 0，在出错时返回非零值。
返回值
=============

一个 seccomp 过滤器可能返回以下任何值。如果有多个过滤器存在，对于给定系统调用的评估，将始终使用优先级最高的返回值。（例如，`SECCOMP_RET_KILL_PROCESS` 将始终具有最高优先级。）

按优先级顺序排列如下：

`SECCOMP_RET_KILL_PROCESS`：
	导致整个进程立即退出而不执行系统调用。任务的退出状态（`status & 0x7f`）将是 `SIGSYS`，而不是 `SIGKILL`。
`SECCOMP_RET_KILL_THREAD`：
	导致任务立即退出而不执行系统调用。任务的退出状态（`status & 0x7f`）将是 `SIGSYS`，而不是 `SIGKILL`。
`SECCOMP_RET_TRAP`：
	导致内核向触发任务发送 `SIGSYS` 信号而不执行系统调用。`siginfo->si_call_addr` 将显示系统调用指令的地址，而 `siginfo->si_syscall` 和 `siginfo->si_arch` 将指示尝试了哪个系统调用。程序计数器将如同系统调用已经发生一样（即不会指向系统调用指令）。返回值寄存器将包含架构相关的值——如果恢复执行，应将其设置为合理值。（这种架构依赖性是因为用 `-ENOSYS` 替换它可能会覆盖一些有用的信息。）

	返回值中的 `SECCOMP_RET_DATA` 部分将作为 `si_errno` 传递。
由 seccomp 触发的 `SIGSYS` 将具有 `SYS_SECCOMP` 的 `si_code`。
`SECCOMP_RET_ERRNO`：
	导致将返回值的低 16 位作为 `errno` 传递给用户空间而不执行系统调用。
`SECCOMP_RET_USER_NOTIF`：
	导致在用户空间通知文件描述符上发送 `struct seccomp_notif` 消息，如果已附加该文件描述符，否则返回 `-ENOSYS`。请参见下面关于如何处理用户通知的讨论。
`SECCOMP_RET_TRACE`：
	当返回此值时，内核将在执行系统调用之前尝试通知基于 `ptrace()` 的跟踪器。如果没有跟踪器存在，则返回 `-ENOSYS` 给用户空间，并且不执行系统调用。
如果跟踪器使用 `ptrace(PTRACE_SETOPTIONS)` 请求 `PTRACE_O_TRACESECCOMP`，则会通知跟踪器。跟踪器将被通知 `PTRACE_EVENT_SECCOMP`，并且 BPF 程序返回值中的 `SECCOMP_RET_DATA` 部分将通过 `PTRACE_GETEVENTMSG` 可供跟踪器使用。
追踪器可以通过将系统调用编号更改为-1来跳过系统调用。或者，追踪器也可以通过更改系统调用编号为一个有效的系统调用编号来改变请求的系统调用。如果追踪器请求跳过系统调用，则该系统调用将返回追踪器放入返回值寄存器中的值。

在通知追踪器之后，不会再次运行seccomp检查。（这意味着基于seccomp的沙箱在没有极度小心的情况下，绝对不能允许使用ptrace，即使是对其他沙箱中的进程也不行；追踪器可以利用此机制逃脱。）

``SECCOMP_RET_LOG``：
导致系统调用在记录后被执行。应用程序开发人员应使用此选项来了解其应用程序需要哪些系统调用，而无需多次迭代测试和开发周期来构建列表。
此操作只有在“actions_logged”sysctl字符串中包含"log"时才会被记录。

``SECCOMP_RET_ALLOW``：
导致系统调用被执行。
如果有多个过滤器存在，对于给定系统调用的评估结果将始终使用最高优先级的值。优先级仅根据``SECCOMP_RET_ACTION``掩码确定。当多个过滤器返回相同优先级的值时，只会返回最近安装的过滤器的``SECCOMP_RET_DATA``。

陷阱
====
使用过程中最大的陷阱是在不检查架构值的情况下对系统调用编号进行过滤。为什么？因为在支持多种系统调用调用约定的任何架构上，系统调用编号可能会根据特定的调用而有所不同。如果不同调用约定中的编号重叠，则过滤器中的检查可能会被滥用。一定要检查架构值！

示例
====
``samples/seccomp/``目录包含一个x86特定的示例和一个更高层次的宏接口示例，用于生成BPF程序。
用户空间通知
=============
``SECCOMP_RET_USER_NOTIF``返回码让seccomp过滤器能够将特定的系统调用传递给用户空间处理。这对于希望拦截某些特定系统调用（如``mount()``、``finit_module()``等）并改变其行为的应用程序（例如容器管理器）可能是有用的。
要获取通知文件描述符，请使用``seccomp()``系统调用的``SECCOMP_FILTER_FLAG_NEW_LISTENER``参数：

```c
fd = seccomp(SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_NEW_LISTENER, &prog);
```

这（在成功时）将返回一个过滤器的监听文件描述符，然后可以通过``SCM_RIGHTS``或类似方式传递。请注意，过滤器文件描述符对应于特定的过滤器，而不是特定的任务。因此，如果此任务进行fork操作，两个任务的通知都将出现在同一个过滤器文件描述符上。读写过滤器文件描述符也是同步的，因此过滤器文件描述符可以安全地有多个读者。
seccomp通知文件描述符的接口由两个结构组成：

```c
struct seccomp_notif_sizes {
    __u16 seccomp_notif;
    __u16 seccomp_notif_resp;
    __u16 seccomp_data;
};

struct seccomp_notif {
    __u64 id;
    __u32 pid;
    __u32 flags;
    struct seccomp_data data;
};

struct seccomp_notif_resp {
    __u64 id;
    __s64 val;
    __s32 error;
    __u32 flags;
};
```

``struct seccomp_notif_sizes``结构可用于确定用于seccomp通知的各种结构的大小。由于``struct seccomp_data``的大小在未来可能会发生变化，因此代码应使用：

```c
struct seccomp_notif_sizes sizes;
seccomp(SECCOMP_GET_NOTIF_SIZES, 0, &sizes);
```

来确定分配各种结构所需的大小。请参阅``samples/seccomp/user-trap.c``以获取示例。
用户可以通过 `ioctl(SECCOMP_IOCTL_NOTIF_RECV)`（或 `poll()`）在 seccomp 通知文件描述符上读取以接收一个 `struct seccomp_notif`，该结构包含五个成员：结构的输入长度、每个过滤器唯一的 `id`、触发此请求的任务的 `pid`（如果任务位于监听者不可见的 pid 命名空间中，则可能为 0）。通知还包含传递给 seccomp 的 `data` 和一个过滤器标志。在调用 ioctl 之前，应将结构清零。

然后用户空间可以根据这些信息做出决策，并通过 `ioctl(SECCOMP_IOCTL_NOTIF_SEND)` 发送响应，指示应返回给用户空间的内容。`struct seccomp_notif_resp` 中的 `id` 成员应与 `struct seccomp_notif` 中的 `id` 相同。

用户空间还可以通过 `ioctl(SECCOMP_IOCTL_NOTIF_ADDFD)` 向通知进程添加文件描述符。`struct seccomp_notif_addfd` 中的 `id` 成员应与 `struct seccomp_notif` 中的 `id` 相同。`newfd_flags` 标志可用于设置文件描述符上的标志（如 O_CLOEXEC）。如果监视器希望使用特定编号注入文件描述符，则可以使用 `SECCOMP_ADDFD_FLAG_SETFD` 标志，并将 `newfd` 成员设置为要使用的特定编号。如果该文件描述符已经在通知进程中打开，则会被替换。监视器也可以添加一个文件描述符，并通过使用 `SECCOMP_ADDFD_FLAG_SEND` 标志原子地响应，返回值将是注入的文件描述符编号。

通知进程可能会被抢占，导致通知被中断。当尝试代表通知进程执行长时间运行且通常可重试的操作（如挂载文件系统）时，这可能会有问题。或者，在安装过滤器时，可以设置 `SECCOMP_FILTER_FLAG_WAIT_KILLABLE_RECV` 标志。此标志使得当用户通知被监视器接收时，通知进程将忽略非致命信号，直到响应被发送。在通知被用户空间接收之前发送的信号将按常规处理。

值得注意的是，`struct seccomp_data` 包含系统调用的寄存器参数值，但不包含指向内存的指针。任务的内存可通过 `ptrace()` 或 `/proc/pid/mem` 访问，适合具有适当权限的跟踪器。然而，为了避免本文档前面提到的 TOCTOU 问题，从跟踪进程的内存中读取的所有参数应在任何策略决策之前读入跟踪器的内存中。这样可以在系统调用参数上进行原子决策。

### Sysctls

Seccomp 的 sysctl 文件位于 `/proc/sys/kernel/seccomp/` 目录中。以下是该目录中每个文件的描述：

`actions_avail`：
    一个只读的有序列表，列出了 seccomp 返回值（参见上面的 `SECCOMP_RET_*` 宏），形式为字符串。从左到右的顺序是从最严格的返回值到最宽松的返回值。
    列表表示内核支持的 seccomp 返回值集。用户空间程序可以使用此列表来确定在程序构建时 `seccomp.h` 中找到的动作是否与当前运行内核实际支持的动作集不同。

`actions_logged`：
    一个可读写的有序列表，列出了允许记录的 seccomp 返回值（参见上面的 `SECCOMP_RET_*` 宏）。写入文件时不需要有序形式，但从文件读取的内容将按照 `actions_avail` sysctl 的相同顺序排列。
``allow`` 字符串在 `actions_logged` sysctl 中不被接受，因为无法记录 `SECCOMP_RET_ALLOW` 操作。尝试将 `allow` 写入 sysctl 将导致返回 `EINVAL`。

添加架构支持
=============

请参见 `arch/Kconfig` 获取权威要求。一般来说，如果一个架构同时支持 `ptrace_event` 和 `seccomp`，那么只需进行少量修正即可支持 `seccomp` 过滤：支持 `SIGSYS` 并检查 `seccomp` 返回值。然后，必须在其特定架构的 `Kconfig` 中添加 `CONFIG_HAVE_ARCH_SECCOMP_FILTER`。

注意事项
=======

vDSO 可以使某些系统调用完全在用户空间中运行，在不同机器上运行程序时可能会导致意外情况。为了在 x86 上最小化这些意外情况，请确保将 `/sys/devices/system/clocksource/clocksource0/current_clocksource` 设置为类似 `acpi_pm` 的值。

在 x86-64 上，默认启用了 vsyscall 模拟。（vsyscalls 是 vDSO 调用的遗留变体。）目前，模拟的 vsyscalls 会遵守 seccomp 规则，但存在一些特殊情况：

- 返回值为 `SECCOMP_RET_TRAP` 时，将设置一个指向给定调用的 vsyscall 入口的 `si_call_addr`，而不是 `syscall` 指令后的地址。任何希望重启调用的代码应意识到（a）已经模拟了一个 `ret` 指令，并且（b）尝试恢复系统调用将再次触发标准的 vsyscall 模拟安全检查，使得恢复系统调用基本没有意义。
- 返回值为 `SECCOMP_RET_TRACE` 时，将像往常一样向跟踪器发送信号，但系统调用不能通过 `orig_rax` 寄存器更改为另一个系统调用。只能将其更改为 -1 以跳过当前模拟的调用。其他任何更改可能会终止进程。
跟踪器看到的 `rip` 值将是系统调用入口地址；这与正常行为不同。跟踪器不得修改 `rip` 或 `rsp`。（不要依赖其他更改来终止进程）
它们可能有效。例如，在某些内核上，选择仅存在于未来内核中的系统调用会被正确模拟（通过返回 `-ENOSYS`）。

要检测这种特殊行为，请检查 `addr & ~0x0C00 == 0xFFFFFFFFFF600000`。（对于 `SECCOMP_RET_TRACE`，使用 `rip`；对于 `SECCOMP_RET_TRAP`，使用 `siginfo->si_call_addr`。）不要检查其他条件：未来的内核可能会改进 vsyscall 模拟，并且在 vsyscall=native 模式下的当前内核表现会有所不同，但在这些情况下，`0xF...F600{0,4,8,C}00` 地址处的指令不会是系统调用。

请注意，现代系统不太可能使用 vsyscalls —— 它们是一个遗留功能，并且比标准系统调用慢得多。新代码将使用 vDSO，而通过 vDSO 发出的系统调用与正常系统调用无异。
