SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：MC

.. _media_ioc_request_alloc:

*******************************
ioctl MEDIA_IOC_REQUEST_ALLOC
*******************************

名称
====

MEDIA_IOC_REQUEST_ALLOC - 分配请求

概要
========

.. c:macro:: MEDIA_IOC_REQUEST_ALLOC

``int ioctl(int fd, MEDIA_IOC_REQUEST_ALLOC, int *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向一个整数的指针

描述
===========

如果媒体设备支持 :ref:`请求 <media-request-api>`，则可以使用此 ioctl 来分配请求。如果不支持，则将 ``errno`` 设置为 ``ENOTTY``。请求是通过返回到 ``*argp`` 的文件描述符来访问的。
如果请求成功分配，则该请求文件描述符可以传递给以下 ioctl：
:ref:`VIDIOC_QBUF <VIDIOC_QBUF>`，
:ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`，
:ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 和
:ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`
此外，可以通过调用 :ref:`MEDIA_REQUEST_IOC_QUEUE` 来排队请求，并通过调用 :ref:`MEDIA_REQUEST_IOC_REINIT` 来重新初始化请求。
最后，可以对文件描述符进行 :ref:`轮询 <request-func-poll>` 来等待请求完成。
请求将一直保持分配状态，直到所有与其相关的文件描述符被 :c:func:`close()` 关闭，并且驱动程序不再内部使用该请求。更多详细信息，请参阅 :ref:`这里 <media-request-life-time>`。

返回值
============

成功时返回 0，错误时返回 -1 并设置适当的 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。

ENOTTY
    驱动程序不支持请求
