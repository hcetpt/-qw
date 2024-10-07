SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.dmx

.. _dmx-munmap:

************
DVB munmap()
************

名称
====

dmx-munmap - 取消映射设备内存

.. 警告:: 此 API 仍在试验阶段
概要
========

.. 代码块:: c

    #include <unistd.h>
    #include <sys/mman.h>

.. c:函数:: int munmap( void *start, size_t length )

参数
=========

``start``
    由 :c:func:`mmap()` 函数返回的已映射缓冲区地址
``length``
    已映射缓冲区的长度。这必须与传递给 :c:func:`mmap()` 的值相同
描述
===========

取消先前通过 :c:func:`mmap()` 函数映射的缓冲区，并在可能的情况下释放它
返回值
============

如果 :c:func:`munmap()` 成功，则返回 0；如果失败，则返回 -1 并且设置相应的 ``errno`` 变量：

EINVAL
    ``start`` 或 ``length`` 不正确，或者尚未映射任何缓冲区
