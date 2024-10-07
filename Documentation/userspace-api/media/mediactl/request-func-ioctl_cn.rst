SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：MC

.. _请求功能ioctl:

***************
请求 ioctl()
***************

名称
====

request-ioctl - 控制请求文件描述符

概要
====

.. code-block:: c

    #include <sys/ioctl.h>

    ``int ioctl(int fd, int cmd, void *argp)``

参数
=========

``fd``
    由 :ref:`MEDIA_IOC_REQUEST_ALLOC` 返回的文件描述符
``cmd``
    在 media.h 头文件中定义的请求 ioctl 命令代码，例如 :ref:`MEDIA_REQUEST_IOC_QUEUE`
``argp``
    指向特定于请求的结构体的指针

描述
===========

:ref:`ioctl() <请求功能ioctl>` 函数用于操作请求参数。参数 ``fd`` 必须是一个打开的文件描述符。
ioctl 的 ``cmd`` 代码指定了要调用的请求函数。它编码了参数是输入、输出还是读/写参数，并且包含了以字节为单位的参数 ``argp`` 的大小。
指定请求 ioctl 命令及其参数的宏和结构体定义位于 media.h 头文件中。所有请求 ioctl 命令及其相应的函数和参数在 :ref:`媒体用户函数` 中进行了说明。

返回值
============

成功时返回 0，错误时返回 -1 并设置适当的 ``errno`` 变量。通用错误码在 :ref:`通用错误码` 章节中有描述。
特定命令的错误码在各个命令描述中列出。
当一个带有输出或读/写参数的 ioctl 调用失败时，该参数将保持不变。
