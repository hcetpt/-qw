Linux 内核追踪点 API
===============================

:作者: Jason Baron
:作者: William Cohen

简介
============

追踪点是在内核中战略位置设置的静态探测点。"探测器"通过回调机制与这些追踪点进行注册和注销。这些"探测器"是严格类型化的函数，它们接收由每个追踪点定义的独特参数集。通过这种简单的回调机制，"探测器"可以用来剖析、调试以及理解内核的行为。有许多工具提供了一套使用"探测器"的框架。这些工具包括Systemtap、ftrace 和 LTTng。

追踪点在多个头文件中通过各种宏定义。因此，本文档的目的在于清晰地列出可用的追踪点。其意图不仅在于了解现有的追踪点，还在于了解未来可能添加追踪点的位置。

API 中提供的函数形式为：
``trace_追踪点名称(函数参数)``。这些是代码中随处可见的追踪点回调。关于如何在这些回调点注册和注销探测器的信息可以在 ``Documentation/trace/*`` 目录中找到。

中断请求 (IRQ)
===

.. kernel-doc:: include/trace/events/irq.h
   :internal:

信号量 (SIGNAL)
======

.. kernel-doc:: include/trace/events/signal.h
   :internal:

块 I/O
========

.. kernel-doc:: include/trace/events/block.h
   :internal:

工作队列 (Workqueue)
=========

.. kernel-doc:: include/trace/events/workqueue.h
   :internal:
