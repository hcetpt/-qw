============= 
rtla-timerlat 
============= 

-------------------------------------------
测量操作系统定时器延迟
-------------------------------------------

:手册章节: 1

概要
======
**rtla timerlat** [*模式*] ..

描述
===========

.. include:: common_timerlat_description.rst

*timerlat* 追踪器以两种方式输出信息。它周期性地在定时器 *IRQ* 处理程序和 *线程* 处理程序中打印定时器延迟。它还通过 **osnoise:** 追踪点为每个噪声提供信息。**rtla timerlat top** 模式显示来自 *timerlat* 追踪器的周期性输出摘要。**rtla hist hist** 模式显示每个追踪事件发生的直方图。更多详情，请参阅各自的手册页。

模式
=====
**top**

        打印来自 *timerlat* 追踪器的摘要
**hist**

        打印 *timerlat* 样本的直方图
如果没有给定 *模式*, 将调用 top 模式，传递参数

选项
=======
**-h**, **--help**

        显示帮助文本
其他选项，请参见对应模式的手册页

参考
========
**rtla-timerlat-top**(1), **rtla-timerlat-hist**(1)

*timerlat* 追踪器文档: <https://www.kernel.org/doc/html/latest/trace/timerlat-tracer.html>

作者
======
由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>

.. include:: common_appendix.rst
