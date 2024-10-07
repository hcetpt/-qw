SPDX 许可声明标识符：GFDL-1.1-no-invariants-or-later
C 命名空间：V4L

.. _VIDIOC_OVERLAY:

********************
ioctl VIDIOC_OVERLAY
********************

名称
====

VIDIOC_OVERLAY - 启动或停止视频覆盖层

概要
====

.. c:macro:: VIDIOC_OVERLAY

``int ioctl(int fd, VIDIOC_OVERLAY, const int *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向一个整数的指针

描述
====

此 ioctl 是 :ref:`video overlay <overlay>` 输入/输出方法的一部分。
应用程序调用 :ref:`VIDIOC_OVERLAY` 来启动或停止覆盖层。它需要一个指向整数的指针，该指针必须由应用程序设置为零以停止覆盖层，设置为一以启动覆盖层。
驱动程序不支持带有 ``V4L2_BUF_TYPE_VIDEO_OVERLAY`` 的 :ref:`VIDIOC_STREAMON` 或 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>`。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的错误代码。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    覆盖层参数尚未设置。详见 :ref:`overlay` 中必要的步骤。
