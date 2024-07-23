SPDX 许可证标识符：GPL-2.0

.. _linux_doc:

==============================
Linux 内核文档
==============================

这是内核文档树的顶级目录。与内核本身一样，内核文档也是一项持续进行的工作；特别是当我们努力将众多分散的文档整合成一个连贯的整体时更是如此。请注意，我们欢迎对文档进行改进；如果您想提供帮助，请加入在 vger.kernel.org 的 linux-doc 邮件列表。
与开发社区合作
======================================

与内核开发社区互动和使您的工作进入上游的关键指南
.. toctree::
   :maxdepth: 1

   开发过程 <process/development-process>
   提交补丁 <process/submitting-patches>
   行为准则 <process/code-of-conduct>
   维护者手册 <maintainer/index>
   所有开发过程文档 <process/index>


内部 API 手册
====================

为与内核其余部分接口工作的开发者提供的手册
.. toctree::
   :maxdepth: 1

   核心 API <core-api/index>
   驱动程序 API <driver-api/index>
   子系统 <subsystem-apis>
   锁定 <locking/index>

开发工具和流程
===============================

所有内核开发者可能需要的各种其他手册，包含有用的信息
.. toctree::
   :maxdepth: 1

   许可规则 <process/license-rules>
   编写文档 <doc-guide/index>
   开发工具 <dev-tools/index>
   测试指南 <dev-tools/testing-overview>
   黑客指南 <kernel-hacking/index>
   追踪 <trace/index>
   故障注入 <fault-injection/index>
   实时补丁 <livepatch/index>
   Rust <rust/index>


面向用户文档
===========================

以下手册是为内核的使用者编写的——那些试图让其在特定系统上达到最优运行状态的人以及寻求了解内核用户空间 API 的应用开发者
.. toctree::
   :maxdepth: 1

   管理 <admin-guide/index>
   构建系统 <kbuild/index>
   报告问题 <admin-guide/reporting-issues.rst>
   用户空间工具 <tools/index>
   用户空间 API <userspace-api/index>

另见：`Linux 手册页 <https://www.kernel.org/doc/man-pages/>`_ ，它们与内核本身的文档分开维护
固件相关文档
==============================
以下是关于内核对平台固件期望的信息
.. toctree::
   :maxdepth: 1

   固件 <firmware-guide/index>
   固件与设备树 <devicetree/index>


架构特定文档
===================================

.. toctree::
   :maxdepth: 2

   CPU 架构 <arch/index>


其他文档
===================

有一些未分类的文档似乎不适合放在文档的其他部分，或者可能需要一些调整和/或转换为 reStructuredText 格式，或者仅仅是过时了
.. toctree::
   :maxdepth: 1

   未分类文档 <staging/index>


翻译
============

.. toctree::
   :maxdepth: 2

   翻译 <translations/index>

索引和表格
==================

* :ref:`genindex`
