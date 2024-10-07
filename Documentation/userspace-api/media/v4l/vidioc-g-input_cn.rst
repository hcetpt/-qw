SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_INPUT:

************************************
ioctl VIDIOC_G_INPUT, VIDIOC_S_INPUT
************************************

名称
====

VIDIOC_G_INPUT - VIDIOC_S_INPUT - 查询或选择当前视频输入

概要
====

.. c:macro:: VIDIOC_G_INPUT

``int ioctl(int fd, VIDIOC_G_INPUT, int *argp)``

.. c:macro:: VIDIOC_S_INPUT

``int ioctl(int fd, VIDIOC_S_INPUT, int *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向包含输入索引的整数指针
描述
===========

为了查询当前视频输入，应用程序需要调用 :ref:`VIDIOC_G_INPUT <VIDIOC_G_INPUT>` ioctl，并提供一个指向整数的指针。驱动程序将输入编号存储在这个整数中，类似于 :c:type:`v4l2_input` 结构中的 ``index`` 字段。当没有视频输入时，此 ioctl 将返回 ``EINVAL``。

为了选择一个视频输入，应用程序需要在整数中存储所需的输入编号，并通过指向该整数的指针调用 :ref:`VIDIOC_S_INPUT <VIDIOC_G_INPUT>` ioctl。可能会有副作用。例如，不同的输入可能支持不同的视频标准，因此驱动程序可能会隐式地切换当前标准。由于这些可能的副作用，应用程序必须在查询或协商任何其他参数之前选择一个输入。

关于视频输入的信息可以通过 :ref:`VIDIOC_ENUMINPUT` ioctl 获得。
返回值
============

成功时返回 0，错误时返回 -1 并设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

EINVAL
    视频输入的编号超出范围
