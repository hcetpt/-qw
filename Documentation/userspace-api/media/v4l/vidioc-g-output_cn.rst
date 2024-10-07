SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_OUTPUT:

**************************************
ioctl VIDIOC_G_OUTPUT, VIDIOC_S_OUTPUT
**************************************

名称
====

VIDIOC_G_OUTPUT - VIDIOC_S_OUTPUT - 查询或选择当前视频输出

概要
====

.. c:macro:: VIDIOC_G_OUTPUT

``int ioctl(int fd, VIDIOC_G_OUTPUT, int *argp)``

.. c:macro:: VIDIOC_S_OUTPUT

``int ioctl(int fd, VIDIOC_S_OUTPUT, int *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向包含输出索引的整数指针

描述
====

为了查询当前视频输出，应用程序调用 :ref:`VIDIOC_G_OUTPUT <VIDIOC_G_OUTPUT>` ioctl，并传入一个指向整数的指针，驱动程序将在此整数中存储输出编号，就像在结构 :c:type:`v4l2_output` 的 ``index`` 字段中一样。此 ioctl 只有在没有视频输出时会失败，并返回 ``EINVAL`` 错误代码。

为了选择一个视频输出，应用程序将所需输出的编号存储在一个整数中，并使用指向该整数的指针调用 :ref:`VIDIOC_S_OUTPUT <VIDIOC_G_OUTPUT>` ioctl。可能会有副作用。例如，输出可能支持不同的视频标准，因此驱动程序可能会隐式地切换当前标准。由于这些可能的副作用，应用程序必须在查询或协商任何其他参数之前选择一个输出。

关于视频输出的信息可以通过 :ref:`VIDIOC_ENUMOUTPUT` ioctl 获取。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    视频输出的编号超出范围，或者根本没有视频输出
