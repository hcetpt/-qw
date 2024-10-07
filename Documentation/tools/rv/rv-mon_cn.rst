.. SPDX-License-Identifier: GPL-2.0

======
rv-mon
======
-----------------------
列出可用的监视器
-----------------------

:手册章节: 1

概要
========

**rv mon** [*-h*] **monitor_name** [*-h*] [*监视器选项*]

描述
===========

**rv mon** 命令运行名为 *monitor_name* 的监视器。每个监视器都有自己的选项集。使用 **rv list** 命令可以显示所有可用的监视器。
选项
=======

**-h**, **--help**

        打印帮助菜单
可用的监视器
==================

**rv** 工具提供了一组监视器的接口。使用 **rv list** 命令列出所有可用的监视器。每个监视器都有自己的选项集。查看 **rv-mon**-*monitor_name* 的手册页以了解每个特定监视器的详细信息。此外，运行 **rv mon** **monitor_name** **-h** 可以显示带有可用选项的帮助菜单。
参见
========

**rv**(1), **rv-mon**(1)

Linux 内核 *RV* 文档:
<https://www.kernel.org/doc/html/latest/trace/rv/index.html>

作者
======

由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>

.. include:: common_appendix.rst
