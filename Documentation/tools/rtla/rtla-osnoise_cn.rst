==================
rtla-osnoise
==================

------------------------------------------------------------------
测量操作系统噪声
------------------------------------------------------------------

:手册章节: 1

概要
======
**rtla osnoise** [*模式*] ..

描述
===========

.. include:: common_osnoise_description.rst

*osnoise* 跟踪器以两种方式输出信息。它定期打印操作系统的噪声摘要，包括干扰源的发生计数。它还通过 **osnoise:** 跟踪点为每个噪声提供信息。**rtla osnoise top** 模式显示来自 *osnoise* 跟踪器的周期性摘要信息。**rtla osnoise hist** 模式使用 **osnoise:** 跟踪点来显示噪声信息。更多详细信息，请参阅相应手册页。

模式
=====
**top**

        打印 *osnoise* 跟踪器的摘要
**hist**

        打印 *osnoise* 样本的直方图
如果没有指定模式，默认调用 top 模式，并传递参数

选项
=======

**-h**, **--help**

        显示帮助文本
其他选项，请参见相应模式的手册页

参考
========
**rtla-osnoise-top**(1), **rtla-osnoise-hist**(1)

Osnoise跟踪器文档: <https://www.kernel.org/doc/html/latest/trace/osnoise-tracer.html>

作者
======
由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>

.. include:: common_appendix.rst
