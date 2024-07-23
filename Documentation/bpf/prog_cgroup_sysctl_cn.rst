SPDX 许可证标识符：(LGPL-2.1 或 BSD-2-Clause)

===========================
BPF_PROG_TYPE_CGROUP_SYSCTL
===========================

本文档描述了 `BPF_PROG_TYPE_CGROUP_SYSCTL` 程序类型，它为 cgroup-bpf 提供了 sysctl 的挂钩。
该挂钩必须附加到 cgroup，并且每当该 cgroup 内的进程尝试从 proc 中读取或写入 sysctl 旋钮时都会被调用。

1. 附着类型
**************

使用 `BPF_CGROUP_SYSCTL` 附着类型将 `BPF_PROG_TYPE_CGROUP_SYSCTL` 程序附加到 cgroup。

2. 上下文
**********

`BPF_PROG_TYPE_CGROUP_SYSCTL` 为 BPF 程序提供了以下上下文访问权限：

    struct bpf_sysctl {
        __u32 write;
        __u32 file_pos;
    };

* `write` 指示是否正在读取（`0`）或写入（`1`）sysctl 值。此字段只读。
* `file_pos` 指示访问 sysctl 的文件位置，无论是读取还是写入。此字段可读写。向该字段写入会设置 sysctl proc 文件中 `read(2)` 将从中读取或 `write(2)` 将写入的起始位置。即使当用户空间在 `file_pos > 0` 时调用，将零写入该字段也可用于通过 `bpf_sysctl_set_new_value()` 在 `write(2)` 上覆盖整个 sysctl 值。向该字段写入非零值可用于从指定的 `file_pos` 开始访问 sysctl 值的一部分。并非所有 sysctl 都支持 `file_pos != 0` 的访问，例如对数字 sysctl 条目的写入必须始终位于文件位置 `0`。参见 `kernel.sysctl_writes_strict` sysctl。

有关如何访问上下文字段的更多详细信息，请参阅 `linux/bpf.h`_。

3. 返回代码
**************

`BPF_PROG_TYPE_CGROUP_SYSCTL` 程序必须返回以下返回代码之一：

* `0` 表示“拒绝访问 sysctl”；
* `1` 表示“继续访问”
如果程序返回 `0`，用户空间将从 `read(2)` 或 `write(2)` 获取 `-1` 并且 `errno` 将设置为 `EPERM`。

4. 辅助函数
**********

由于 sysctl 旋钮由名称和值表示，sysctl 特定的 BPF 辅助函数专注于提供对这些属性的访问：

* `bpf_sysctl_get_name()` 以在 `/proc/sys` 中可见的形式获取 sysctl 名称到由 BPF 程序提供的缓冲区；

* `bpf_sysctl_get_current_value()` 获取当前由 sysctl 持有的字符串值到由 BPF 程序提供的缓冲区。此辅助函数在从 sysctl 的 `read(2)` 和写入 sysctl 的 `write(2)` 中都可用；

* `bpf_sysctl_get_new_value()` 在实际写入之前获取当前正被写入 sysctl 的新字符串值。此辅助函数仅在 `ctx->write == 1` 时可用；

* `bpf_sysctl_set_new_value()` 在实际写入之前覆盖当前正被写入 sysctl 的新字符串值。sysctl 值将从当前 `ctx->file_pos` 开始被覆盖。如果需要覆盖整个值，BPF 程序可以在调用辅助函数前将 `file_pos` 设置为零。此辅助函数仅在 `ctx->write == 1` 时可用。由辅助函数设置的新字符串值将由内核以与用户空间传递的等效字符串相同的方式处理和验证。

BPF 程序看到的 sysctl 值与用户空间在 proc 文件系统中看到的一样，即为字符串。由于许多 sysctl 值表示整数或整数向量，可以使用以下辅助函数从字符串中获取数值：

* `bpf_strtol()` 将字符串的初始部分转换为长整型，类似于用户空间的 `strtol(3)`_；
* `bpf_strtoul()` 将字符串的初始部分转换为无符号长整型，类似于用户空间的 `strtoul(3)`_；

有关此处描述的辅助函数的更多详细信息，请参阅 `linux/bpf.h`_。
5. 示例
***********

请参阅`test_sysctl_prog.c`_，这是一个C语言编写的BPF程序示例，该程序访问sysctl名称和值，解析字符串值以获取整数向量，并使用结果来决定是否允许或拒绝访问sysctl。

6. 注意事项
********

``BPF_PROG_TYPE_CGROUP_SYSCTL``旨在在**受信任的**root环境中使用，例如，用于监控sysctl的使用情况，或者捕获一个在独立cgroup中作为root运行的应用程序试图设置的不合理值。
由于在`sys_read` / `sys_write`时调用`task_dfl_cgroup(current)`，其返回的结果可能与`sys_open`时不同，即，在proc文件系统中打开sysctl文件的过程可能与尝试从中读取或写入的过程不同，而这两个过程可能运行在不同的cgroup中。这意味着``BPF_PROG_TYPE_CGROUP_SYSCTL``不应该被用作一种安全机制来限制sysctl的使用。
如同任何cgroup-bpf程序一样，如果一个在cgroup中作为root运行的应用程序不应被允许卸载/替换管理员附加的BPF程序，则需要额外注意。

.. 链接
.. _linux/bpf.h: ../../include/uapi/linux/bpf.h
.. _strtol(3): http://man7.org/linux/man-pages/man3/strtol.3p.html
.. _strtoul(3): http://man7.org/linux/man-pages/man3/strtoul.3p.html
.. _test_sysctl_prog.c:
   ../../tools/testing/selftests/bpf/progs/test_sysctl_prog.c

请注意，上述链接和文档可能需要根据实际环境进行适当调整或查阅。
