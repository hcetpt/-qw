BPF 文档
========

此目录包含关于 BPF（Berkeley Packet Filter）功能的文档，重点介绍扩展版 BPF（eBPF）。内核侧的文档仍在开发中。
Cilium 项目还维护了一个《BPF 和 XDP 参考指南》_ ，深入介绍了 BPF 架构的技术细节。
.. toctree::
   :maxdepth: 1

   verifier
   libbpf/index
   standardization/index
   btf
   faq
   syscall_api
   helpers
   kfuncs
   cpumasks
   fs_kfuncs
   programs
   maps
   bpf_prog_run
   classic_vs_extended.rst
   bpf_iterators
   bpf_licensing
   test_debug
   clang-notes
   linux-notes
   other
   redirect

.. only::  子项目和 html

   索引
   =======
   
   * :ref:`genindex`

.. 链接:
.. _BPF 和 XDP 参考指南: https://docs.cilium.io/en/latest/bpf/
