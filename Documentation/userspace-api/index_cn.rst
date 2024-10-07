=====================================
Linux 内核用户空间 API 指南
=====================================

.. _man-pages: https://www.kernel.org/doc/man-pages/

虽然内核的大部分用户空间 API 在其他地方有文档（特别是在 man-pages_ 项目中），但内核树本身也包含一些用户空间信息。本手册旨在收集这些信息。

系统调用
============

.. toctree::
   :maxdepth: 1

   unshare
   futex2
   ebpf/index
   ioctl/index
   mseal

与安全相关的接口
===========================

.. toctree::
   :maxdepth: 1

   no_new_privs
   seccomp_filter
   landlock
   lsm
   mfd_noexec
   spec_ctrl
   tee

设备和 I/O
==============

.. toctree::
   :maxdepth: 1

   accelerators/ocxl
   dma-buf-alloc-exchange
   gpio/index
   iommu
   iommufd
   media/index
   dcdbas
   vduse
   isapnp

其他内容
==============

.. toctree::
   :maxdepth: 1

   ELF
   netlink/index
   sysfs-platform_profile
   vduse
   futex2
   perf_ring_buffer

.. only::  subproject and html

   索引
   =======

   * :ref:`genindex`
