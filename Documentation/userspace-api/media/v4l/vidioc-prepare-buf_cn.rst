SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_PREPARE_BUF:

************************
ioctl VIDIOC_PREPARE_BUF
************************

名称
====

VIDIOC_PREPARE_BUF - 准备一个缓冲区用于 I/O 操作

概要
========

.. c:macro:: VIDIOC_PREPARE_BUF

``int ioctl(int fd, VIDIOC_PREPARE_BUF, struct v4l2_buffer *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_buffer` 结构体的指针
描述
===========

应用程序可以选择性地调用 :ref:`VIDIOC_PREPARE_BUF` ioctl，将缓冲区的所有权传递给驱动程序，在实际使用 :ref:`VIDIOC_QBUF <VIDIOC_QBUF>` ioctl 将其入队之前，为未来的 I/O 操作做准备。这样的准备工作可能包括缓存失效或清理。提前进行这些操作可以在实际 I/O 过程中节省时间。
:c:type:`v4l2_buffer` 结构体在 :ref:`buffer` 中定义。
返回值
============

成功时返回 0，失败时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EBUSY
    文件 I/O 正在进行中
EINVAL
    缓冲区的 ``type`` 不受支持，或者 ``index`` 越界，或者尚未分配任何缓冲区，或者 ``userptr`` 或 ``length`` 无效
