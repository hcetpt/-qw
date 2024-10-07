.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_STD:

******************************************************************************
ioctl VIDIOC_G_STD, VIDIOC_S_STD, VIDIOC_SUBDEV_G_STD, VIDIOC_SUBDEV_S_STD
******************************************************************************

名称
====

VIDIOC_G_STD - VIDIOC_S_STD - VIDIOC_SUBDEV_G_STD - VIDIOC_SUBDEV_S_STD - 查询或选择当前输入的视频标准

概要
====

.. c:macro:: VIDIOC_G_STD

``int ioctl(int fd, VIDIOC_G_STD, v4l2_std_id *argp)``

.. c:macro:: VIDIOC_S_STD

``int ioctl(int fd, VIDIOC_S_STD, const v4l2_std_id *argp)``

.. c:macro:: VIDIOC_SUBDEV_G_STD

``int ioctl(int fd, VIDIOC_SUBDEV_G_STD, v4l2_std_id *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_STD

``int ioctl(int fd, VIDIOC_SUBDEV_S_STD, const v4l2_std_id *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_std_id` 的指针

描述
====

为了查询和选择当前的视频标准，应用程序可以使用 :ref:`VIDIOC_G_STD <VIDIOC_G_STD>` 和 :ref:`VIDIOC_S_STD <VIDIOC_G_STD>` ioctl 命令，这些命令接受一个指向 :ref:`v4l2_std_id <v4l2-std-id>` 类型的指针作为参数。:ref:`VIDIOC_G_STD <VIDIOC_G_STD>` 可以返回一个标志或一组标志，就像在结构 :c:type:`v4l2_standard` 字段 ``id`` 中那样。这些标志必须是明确的，即它们只出现在一个枚举的结构 :c:type:`v4l2_standard` 中。:ref:`VIDIOC_S_STD <VIDIOC_G_STD>` 接受一个或多个标志，由于这是一个写入专用的 ioctl 命令，它不会像 :ref:`VIDIOC_G_STD <VIDIOC_G_STD>` 那样返回实际的新标准。如果没有给出任何标志或者当前输入不支持请求的标准，驱动程序将返回一个 ``EINVAL`` 错误代码。当设置的标准有歧义时，驱动程序可能会返回 ``EINVAL`` 或者选择任何一个请求的标准。如果当前输入或输出不支持标准视频定时（例如，如果 :ref:`VIDIOC_ENUMINPUT` 没有设置 ``V4L2_IN_CAP_STD`` 标志），则返回 ``ENODATA`` 错误代码。
在以只读模式注册的子设备节点上调用 ``VIDIOC_SUBDEV_S_STD`` 是不允许的。将返回错误，并将 errno 变量设置为 ``-EPERM``。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    :ref:`VIDIOC_S_STD <VIDIOC_G_STD>` 参数不合适
ENODATA
    此输入或输出不支持标准视频定时
EPERM
    在只读子设备上调用了 ``VIDIOC_SUBDEV_S_STD``
