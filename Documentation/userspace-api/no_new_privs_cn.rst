======================
无新特权标志
======================

`execve` 系统调用可以为新启动的程序授予其父进程所没有的权限。最明显的例子是设置 `setuid/setgid` 的程序和文件功能。为了防止父进程也获得这些权限，内核和用户代码必须小心防止父进程执行任何可能破坏子进程的操作。例如：

- 动态加载器在程序设置为 `setuid` 时会以不同的方式处理 `LD_*` 环境变量。
- 对于没有特权的进程，禁止使用 `chroot`，因为这将允许从继承了 `chroot` 的进程的角度替换 `/etc/passwd` 文件。
- `exec` 代码对 `ptrace` 有特殊处理。

这些都是临时的修复措施。自 Linux 3.5 版本起引入的 `no_new_privs` 标志是一种新的通用机制，使得进程可以在修改其执行环境时保持安全，并且这种修改会持续到 `execve` 调用之后。任何任务都可以设置 `no_new_privs`。一旦设置了该标志位，它将在 `fork`、`clone` 和 `execve` 时继承，并且不能被取消设置。当设置了 `no_new_privs` 后，`execve()` 将保证不会授予执行任何原本无法完成的操作的权限。例如，`setuid` 和 `setgid` 标志将不再改变 UID 或 GID；文件能力也不会增加许可集，并且在 `execve` 之后 SELinux 模块（LSM）也不会放松约束。

要设置 `no_new_privs`，可以使用以下命令：

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

然而，请注意：在 `no_new_privs` 模式下，SELinux 模块也可能不会在 `exec` 时加强约束。（这意味着如果设置一个通用的服务启动器，在 `exec` 守护进程之前设置 `no_new_privs` 可能会干扰基于 SELinux 模块的沙箱。）

请注意，`no_new_privs` 不会阻止不涉及 `execve()` 的特权更改。具有适当特权的任务仍然可以调用 `setuid(2)` 并接收 SCM_RIGHTS 数据报。

目前，`no_new_privs` 主要有两个主要应用场景：

- 在 seccomp 模式 2 沙箱中安装的过滤器会跨越 `execve` 调用并改变新执行程序的行为。因此，只有在设置了 `no_new_privs` 的情况下，非特权用户才被允许安装此类过滤器。
- 单独使用 `no_new_privs` 可以减少非特权用户的攻击面。如果具有给定 UID 的所有正在运行的任务都设置了 `no_new_privs`，那么该 UID 将无法通过直接攻击 `setuid`、`setgid` 和使用文件能力的二进制文件来提升其权限；它需要首先破坏未设置 `no_new_privs` 的东西。

将来，如果设置了 `no_new_privs`，其他潜在危险的内核特性可能会对非特权任务开放。原则上，当设置了 `no_new_privs` 时，`unshare(2)` 和 `clone(2)` 的几个选项将是安全的，并且 `no_new_privs` 加上 `chroot` 远比单独使用 `chroot` 更安全。
