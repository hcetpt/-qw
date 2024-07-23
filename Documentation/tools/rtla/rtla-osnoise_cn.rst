==================
rtla-osnoise
==================

------------------------------------------------------------------
测量操作系统噪声
------------------------------------------------------------------

:手册章节: 1

概要
========

**rtla osnoise** [*模式*] ..

描述
===========

.. include:: common_osnoise_description.rst

"osnoise"追踪器以两种方式输出信息。它会周期性地打印出操作系统噪声的摘要，包括干扰源发生的计数器。它还通过**osnoise:**追踪点为每种噪声提供信息。**rtla osnoise top**模式显示来自"osnoise"追踪器的周期性摘要的信息。**rtla osnoise hist**模式使用**osnoise:**追踪点来显示噪声的信息。更多详细信息，请参阅相应的手册页。
模式
=====

**top**

        打印"osnoise"追踪器的摘要
**hist**

        打印"osnoise"样本的直方图
如果没有给出模式，则调用top模式，并传递参数
选项
=======

**-h**, **--help**

        显示帮助文本
对于其他选项，请参见对应模式的手册页
参考
========
**rtla-osnoise-top**(1), **rtla-osnoise-hist**(1)

"osnoise"追踪器文档: <https://www.kernel.org/doc/html/latest/trace/osnoise-tracer.html>

作者
======
由Daniel Bristot de Oliveira编写 <bristot@kernel.org>

.. include:: common_appendix.rst
