SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
c:命名空间:: V4L

.. _VIDIOC_SUBDEV_G_CLIENT_CAP:

************************************************************
ioctl VIDIOC_SUBDEV_G_CLIENT_CAP, VIDIOC_SUBDEV_S_CLIENT_CAP
************************************************************

名称
====

VIDIOC_SUBDEV_G_CLIENT_CAP - VIDIOC_SUBDEV_S_CLIENT_CAP - 获取或设置客户端能力
概要
========

.. c:macro:: VIDIOC_SUBDEV_G_CLIENT_CAP

``int ioctl(int fd, VIDIOC_SUBDEV_G_CLIENT_CAP, struct v4l2_subdev_client_capability *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_CLIENT_CAP

``int ioctl(int fd, VIDIOC_SUBDEV_S_CLIENT_CAP, struct v4l2_subdev_client_capability *argp)``

参数
=========

``fd``
    由 :ref:`open() <func-open>` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_subdev_client_capability` 结构体的指针
描述
===========

这些 ioctl 用于获取和设置客户端（使用子设备 ioctl 的应用程序）的能力。客户端能力存储在打开的子设备节点的文件句柄中，客户端必须为每个打开的子设备分别设置能力。
默认情况下，当打开子设备节点时不会设置任何客户端能力。客户端能力的主要目的是告知内核客户端的行为，主要与保持不同内核和用户空间版本的兼容性有关。
``VIDIOC_SUBDEV_G_CLIENT_CAP`` ioctl 返回与文件句柄 ``fd`` 关联的当前客户端能力。
``VIDIOC_SUBDEV_S_CLIENT_CAP`` ioctl 设置文件句柄 ``fd`` 的客户端能力。新的能力将完全替换当前的能力，因此该 ioctl 也可以用于移除之前设置的能力。
``VIDIOC_SUBDEV_S_CLIENT_CAP`` 修改 :c:type:`v4l2_subdev_client_capability` 结构体以反映已接受的能力。内核不接受某个能力的一个常见情况是内核版本比用户空间使用的头文件版本旧，因此该能力对内核来说是未知的。
.. tabularcolumns:: |p{1.5cm}|p{2.9cm}|p{12.9cm}|

.. c:type:: v4l2_subdev_client_capability

.. flat-table:: struct v4l2_subdev_client_capability
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 4 20

    * - __u64
      - ``capabilities``
      - 打开设备的子设备客户端能力
.. 表格列定义:: |p{6.8cm}|p{2.4cm}|p{8.1cm}|

.. 平坦表格:: 客户端功能
    :表头行:  1

    * - 功能
      - 描述
    * - ``V4L2_SUBDEV_CLIENT_CAP_STREAMS``
      - 客户端了解流。设置此标志可启用带有各种 ioctl 的“流”字段（指的是流编号）。如果未设置（这是默认情况），内核会将“流”字段强制设为 0。
    * - ``V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH``
      - 客户端了解 :c:type:`v4l2_subdev_frame_interval` 的 ``which`` 字段。如果未设置（这是默认情况），内核会将 ``which`` 字段强制设为 ``V4L2_SUBDEV_FORMAT_ACTIVE``。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的错误码。通用错误码在章节 :ref:`通用错误码 <gen-errors>` 中有描述。

ENOIOCTLCMD
   内核不支持此 ioctl。
