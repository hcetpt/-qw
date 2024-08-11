SPDX 许可证标识符: (LGPL-2.1 或 BSD-2-Clause)

===========================
BPF_PROG_TYPE_CGROUP_SYSCTL
===========================

本文档描述了 `BPF_PROG_TYPE_CGROUP_SYSCTL` 程序类型，它为 cgroup-bpf 提供了针对 sysctl 的钩子。
该钩子必须附加到一个 cgroup 上，并且每当该 cgroup 内的进程尝试从 proc 中读取或写入 sysctl 旋钮时都会被调用。
1. 附加类型
**************

使用 `BPF_CGROUP_SYSCTL` 附加类型将 `BPF_PROG_TYPE_CGROUP_SYSCTL` 程序附加到 cgroup。
2. 上下文
**********

`BPF_PROG_TYPE_CGROUP_SYSCTL` 为 BPF 程序提供了以下上下文访问权限：

    struct bpf_sysctl {
        __u32 write;
        __u32 file_pos;
    };

* `write` 表明 sysctl 值是正在被读取 (`0`) 还是正在被写入 (`1`)。此字段只读。
* `file_pos` 指示访问 sysctl 时的文件位置，无论是读取还是写入。此字段可读可写。写入此字段会设置 sysctl proc 文件中 `read(2)` 将从中读取或 `write(2)` 将写入的起始位置。向该字段写入零可以用于在 `write(2)` 调用时通过 `bpf_sysctl_set_new_value()` 覆盖整个 sysctl 值，即使用户空间在 `file_pos > 0` 时调用它。向该字段写入非零值可用于从指定的 `file_pos` 开始访问 sysctl 值的一部分。并非所有 sysctl 都支持在 `file_pos != 0` 时进行访问，例如对数字 sysctl 项的写入必须始终位于文件位置 `0`。请参阅 `kernel.sysctl_writes_strict` sysctl 以获取更多信息。
请参阅 `linux/bpf.h`_ 以获取更多关于如何访问上下文字段的详细信息。
3. 返回码
**************

`BPF_PROG_TYPE_CGROUP_SYSCTL` 程序必须返回以下返回码之一：

* `0` 表示“拒绝访问 sysctl”；
* `1` 表示“继续访问”
如果程序返回 `0`，用户空间将从 `read(2)` 或 `write(2)` 获取 `-1` 并且 `errno` 将被设置为 `EPERM`。
4. 辅助函数
**********

由于 sysctl 旋钮由名称和值表示，sysctl 特定的 BPF 辅助函数主要集中在提供对这些属性的访问上：

* `bpf_sysctl_get_name()` 用于获取 sysctl 名称，就像它在 `/proc/sys` 中可见的一样，放入由 BPF 程序提供的缓冲区中；

* `bpf_sysctl_get_current_value()` 用于获取当前由 sysctl 持有的字符串值，放入由 BPF 程序提供的缓冲区中。此辅助函数在从 sysctl `read(2)` 和向 sysctl `write(2)` 时都可用；

* `bpf_sysctl_get_new_value()` 用于获取当前正在写入 sysctl 之前的新的字符串值。此辅助函数仅在 `ctx->write == 1` 时可用；

* `bpf_sysctl_set_new_value()` 用于在实际写入之前覆盖当前正在写入 sysctl 的新字符串值。sysctl 值将从当前 `ctx->file_pos` 开始被覆盖。如果需要覆盖整个值，BPF 程序可以在调用辅助函数之前将 `file_pos` 设置为零。此辅助函数仅在 `ctx->write == 1` 时可用。通过辅助函数设置的新字符串值将被视为与用户空间传递的等效字符串相同，并由内核进行验证。
BPF 程序看到的 sysctl 值与用户空间在 proc 文件系统中看到的方式相同，即为字符串。由于许多 sysctl 值代表整数或整数向量，以下辅助函数可用于从字符串中获取数值：

* `bpf_strtol()` 用于将字符串的初始部分转换为长整数，类似于用户空间中的 `strtol(3)`_；
* `bpf_strtoul()` 用于将字符串的初始部分转换为无符号长整数，类似于用户空间中的 `strtoul(3)`_；

请参阅 `linux/bpf.h`_ 以获取更多关于这里描述的辅助函数的详细信息。
5. 示例
***********

请参阅 `test_sysctl_prog.c`_，这是一个用C语言编写的BPF程序示例，该程序访问sysctl名称和值，解析字符串值以获取整数向量，并利用结果来决定是否允许或拒绝访问sysctl。

6. 注意事项
********

``BPF_PROG_TYPE_CGROUP_SYSCTL`` 预期在**受信任的**根环境中使用，例如用于监控sysctl使用情况或捕获某个作为根用户在独立cgroup中运行的应用程序尝试设置的不合理值。
由于在 `sys_read` / `sys_write` 时调用 `task_dfl_cgroup(current)` 可能会返回与 `sys_open` 时不同的结果，即，在proc文件系统中打开sysctl文件的进程可能与尝试从中读取/写入的进程不同，并且这两个进程可能运行在不同的cgroup中。这意味着 ``BPF_PROG_TYPE_CGROUP_SYSCTL`` 不应作为安全机制来限制sysctl的使用。
对于任何cgroup-bpf程序，如果一个在cgroup中以根用户身份运行的应用程序不应被允许卸载/替换管理员附加的BPF程序，则需要特别注意。
.. 链接
.. _linux/bpf.h: ../../include/uapi/linux/bpf.h
.. _strtol(3): http://man7.org/linux/man-pages/man3/strtol.3p.html
.. _strtoul(3): http://man7.org/linux/man-pages/man3/strtoul.3p.html
.. _test_sysctl_prog.c: 
   ../../tools/testing/selftests/bpf/progs/test_sysctl_prog.c
