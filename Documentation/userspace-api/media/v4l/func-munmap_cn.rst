SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-munmap:

*************
V4L2 munmap()
*************

名称
====

v4l2-munmap —— 取消映射设备内存

概要
========

.. code-block:: c

    #include <unistd.h>
    #include <sys/mman.h>

.. c:function:: int munmap( void *start, size_t length )

参数
=========

``start``
    映射缓冲区的地址，由 :c:func:`mmap()` 函数返回
``length``
    映射缓冲区的长度。这必须与传递给 :c:func:`mmap()` 的值相同，并且对于单平面 API，在结构体 :c:type:`v4l2_buffer` 的 ``length`` 字段中由驱动程序返回；对于多平面 API，在结构体 :c:type:`v4l2_plane` 的 ``length`` 字段中返回。
描述
===========

取消先前通过 :c:func:`mmap()` 函数映射的缓冲区，并在可能的情况下释放它。
返回值
============

如果成功，:c:func:`munmap()` 返回 0；如果失败，则返回 -1 并将 ``errno`` 变量设置为适当的错误代码：

EINVAL
    ``start`` 或 ``length`` 不正确，或者尚未映射任何缓冲区
