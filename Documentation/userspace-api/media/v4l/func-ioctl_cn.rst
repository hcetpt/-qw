SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-ioctl:

************
V4L2 ioctl()
************

名称
====

v4l2-ioctl - 配置 V4L2 设备

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
    在 ``videodev2.h`` 头文件中定义的 V4L2 ioctl 请求代码，例如 VIDIOC_QUERYCAP
``argp``
    指向函数参数的指针，通常是一个结构体
描述
===========

:ref:`ioctl() <func-ioctl>` 函数用于配置 V4L2 设备。参数 ``fd`` 必须是打开的文件描述符。ioctl 请求 ``request`` 编码了参数是输入、输出还是读写参数，并且包含了以字节为单位的参数 ``argp`` 的大小。指定 V4L2 ioctl 请求的宏和定义位于 ``videodev2.h`` 头文件中。应用程序应使用自己的副本，而不是包含系统上编译时内核源代码中的版本。所有 V4L2 ioctl 请求及其相应的函数和参数在 :ref:`user-func` 中指定。
返回值
============

成功时返回 0，错误时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
当一个带有输出或读写参数的 ioctl 请求失败时，该参数保持不变。
