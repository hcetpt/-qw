SPDX 许可证标识符: GPL-2.0

=====================
Devpts 文件系统
=====================

每次挂载 devpts 文件系统现在都是独立的，因此在一个挂载点分配的伪终端（pty）及其索引与其他所有挂载点中的伪终端及其索引是相互独立的。
所有 devpts 文件系统的挂载都会创建一个权限为 ``0000`` 的 ``/dev/pts/ptmx`` 节点。
为了保持向后兼容性，当打开一个 ptmx 设备节点（即通过 ``mknod name c 5 2`` 创建的任何节点）时，会在这个设备节点所在目录中查找名为 ``pts`` 的 devpts 实例。

作为选项，可以将指向 ``/dev/pts/ptmx`` 的符号链接放置在 ``/dev/ptmx`` 或将 ``/dev/pts/ptmx`` 绑定挂载到 ``/dev/ptmx``。如果选择以这种方式使用 devpts 文件系统，则应使用 ``ptmxmode=0666`` 挂载 devpts，或者调用 ``chmod 0666 /dev/pts/ptmx``。

所有实例中的 pty 对总数由以下 sysctl 限制：

```
kernel.pty.max = 4096 - 全局限制
kernel.pty.reserve = 1024 - 为从初始挂载命名空间挂载的文件系统预留
kernel.pty.nr - 当前 pty 数量
```

可以通过添加挂载选项 ``max=<count>`` 来设置每个实例的限制。
此功能是在内核 3.4 中与 ``sysctl kernel.pty.reserve`` 一起引入的。
在早于 3.4 的内核版本中，sysctl ``kernel.pty.max`` 作为每个实例的限制。
