SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: MC

.. _媒体功能ioctl:

*************
媒体 ioctl()
*************

名称
====

media-ioctl — 控制媒体设备

概要
========

.. code-block:: c

    #include <sys/ioctl.h>

``int ioctl(int fd, int request, void *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``request``
    在 media.h 头文件中定义的媒体 ioctl 请求代码，例如 MEDIA_IOC_SETUP_LINK
``argp``
    指向请求特定结构的指针

描述
===========

:ref:`ioctl() <媒体功能ioctl>` 函数用于操作媒体设备参数。参数 ``fd`` 必须是一个打开的文件描述符。
ioctl 的 ``request`` 代码指定了要调用的媒体函数。该代码编码了参数是输入、输出还是读写参数，并且指定了参数 ``argp`` 的字节大小。
与媒体 ioctl 请求及其参数相关的宏和结构定义位于 media.h 头文件中。所有媒体 ioctl 请求、它们相应的函数及参数在 :ref:`媒体用户功能` 中指定。
返回值
============

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误码在 :ref:`通用错误码 <通用错误码>` 章节中描述。
特定请求的错误码在各个请求的描述中列出。
当一个带有输出或读写参数的 ioctl 调用失败时，该参数保持不变。
