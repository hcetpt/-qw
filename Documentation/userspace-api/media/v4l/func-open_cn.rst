SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-open:

***********
V4L2 open()
***********

名称
====

v4l2-open — 打开一个 V4L2 设备

概要
========

.. code-block:: c

    #include <fcntl.h>

.. c:function:: int open(const char *device_name, int flags)

参数
=========

``device_name``
    要打开的设备
``flags``
    打开标志。访问模式必须为 ``O_RDWR``。这只是技术上的要求，输入设备仍然只支持读取，输出设备只支持写入。
当给出 ``O_NONBLOCK`` 标志时，:c:func:`read()` 函数和 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 在没有数据可用或驱动程序输出队列中没有缓冲区时将返回 ``EAGAIN`` 错误代码，否则这些函数将阻塞直到有数据可用。所有与应用程序交换数据的 V4L2 驱动程序都必须支持 ``O_NONBLOCK`` 标志。
其他标志没有效果。

描述
===========

为了打开一个 V4L2 设备，应用程序需要调用 :c:func:`open()` 并传入所需的设备名。这个函数没有副作用；所有的数据格式参数、当前输入或输出、控制值或其他属性保持不变。在加载驱动程序后的第一次 :c:func:`open()` 调用时，它们将重置为默认值，驱动程序永远不会处于未定义状态。

返回值
============

成功时，:c:func:`open()` 返回新的文件描述符。出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码。
可能的错误码包括：

EACCES
    调用者没有权限访问该设备
EBUSY
    驱动程序不支持多次打开，且设备已被使用
ENODEV
    未找到设备或设备已被移除
ENOMEM
    没有足够的内核内存来完成请求
EMFILE
进程已经打开的最大文件数已达上限

ENFILE
系统上打开的文件总数已达到限制
