SPDX 许可证标识符：GPL-2.0

eBPF 用户空间 API
==================

eBPF 是一种内核机制，用于在 Linux 内核中提供一个沙箱运行环境，以便在不修改内核源代码或加载内核模块的情况下进行运行时扩展和仪器化。eBPF 程序可以附加到各种内核子系统，包括网络、跟踪和 Linux 安全模块（LSM）。
关于 eBPF 的内部内核文档，请参阅 Documentation/bpf/index.rst
.. toctree::
   :maxdepth: 1

   syscall
