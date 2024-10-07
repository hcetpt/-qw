.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: MC

.. _媒体函数关闭:

*************
media close()
*************

名称
====

media-close - 关闭媒体设备

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: int close(int fd)

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
描述
===========

关闭媒体设备。与文件描述符相关的资源将被释放。设备配置保持不变。
返回值
============

:c:func:`close()` 在成功时返回 0。如果出错，则返回 -1，并且适当设置 ``errno``。可能的错误代码包括：

EBADF
    ``fd`` 不是一个有效的打开文件描述符
