SuperH接口指南
=======================

:作者: Paul Mundt

.. toctree::
    :maxdepth: 1

    启动
    新机器
    寄存器库

    特性

内存管理
=================

SH-4
----

存储队列API
~~~~~~~~~~~~~~~

.. kernel-doc:: arch/sh/kernel/cpu/sh4/sq.c
   :export:

特定于机器的接口
===========================

mach-dreamcast
--------------

.. kernel-doc:: arch/sh/boards/mach-dreamcast/rtc.c
   :internal:

mach-x3proto
------------

.. kernel-doc:: arch/sh/boards/mach-x3proto/ilsel.c
   :export:

总线
======

Maple
-----

.. kernel-doc:: drivers/sh/maple/maple.c
   :export:
