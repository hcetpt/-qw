### SPDX 许可证标识符: GPL-2.0

### _linux文档_

==============================
Linux 内核文档
==============================

这是内核文档体系的顶层。如同内核本身一样，内核文档也是一个持续发展的工程；特别是在我们努力将众多分散的文档整合为一个连贯整体的过程中，这一点尤为明显。请注意，我们欢迎对文档进行改进；如果您想提供帮助，请加入 vger.kernel.org 上的 linux-doc 邮件列表。
与开发社区合作
======================================

这些指南对于与内核开发社区互动以及将您的工作并入主线至关重要。
.. toctree::
   :maxdepth: 1

   开发流程 <process/development-process>
   提交补丁 <process/submitting-patches>
   行为准则 <process/code-of-conduct>
   维护者手册 <maintainer/index>
   所有开发流程文档 <process/index>

内部 API 手册
====================

这些手册适用于那些需要与内核其他部分交互的开发者。
.. toctree::
   :maxdepth: 1

   核心 API <core-api/index>
   驱动程序 API <driver-api/index>
   子系统 <subsystem-apis>
   锁定 <locking/index>

开发工具和流程
===============================

这些手册包含了所有内核开发者可能需要了解的各种有用信息。
.. toctree::
   :maxdepth: 1

   许可规则 <process/license-rules>
   编写文档 <doc-guide/index>
   开发工具 <dev-tools/index>
   测试指南 <dev-tools/testing-overview>
   黑客指南 <kernel-hacking/index>
   跟踪 <trace/index>
   故障注入 <fault-injection/index>
   实时补丁 <livepatch/index>
   Rust 语言支持 <rust/index>

面向用户的文档
===========================

以下手册是为内核的使用者编写的——那些希望在特定系统上让内核发挥最佳性能或寻求了解内核用户空间 API 的应用程序开发者。
.. toctree::
   :maxdepth: 1

   系统管理 <admin-guide/index>
   构建系统 <kbuild/index>
   报告问题 <admin-guide/reporting-issues.rst>
   用户空间工具 <tools/index>
   用户空间 API <userspace-api/index>

另见：`Linux 手册页 <https://www.kernel.org/doc/man-pages/>`_ ，它们独立于内核自身的文档维护。
固件相关文档
==============================
以下内容包含了关于内核对平台固件期望的信息。
.. toctree::
   :maxdepth: 1

   固件 <firmware-guide/index>
   固件与设备树 <devicetree/index>

架构特异文档
===================================

.. toctree::
   :maxdepth: 2

   CPU 架构 <arch/index>

其他文档
===================

还有一些未分类的文档似乎不适合放在文档体系的其他部分，或者需要一些调整和/或转换为 reStructuredText 格式，或者仅仅是过于陈旧。
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
