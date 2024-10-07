SPDX 许可证标识符: GPL-2.0

eBPF 系统调用
-------------

作者: 
- Alexei Starovoitov <ast@kernel.org>
- Joe Stringer <joe@wand.net.nz>
- Michael Kerrisk <mtk.manpages@gmail.com>

关于 bpf 系统调用的主要信息可以在 `man-pages`_ 中的 `bpf(2)`_ 找到。
bpf() 子命令参考
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/uapi/linux/bpf.h
   :doc: eBPF 系统调用前言

.. kernel-doc:: include/uapi/linux/bpf.h
   :doc: eBPF 系统调用命令

.. 链接:
.. _man-pages: https://www.kernel.org/doc/man-pages/
.. _bpf(2): https://man7.org/linux/man-pages/man2/bpf.2.html
