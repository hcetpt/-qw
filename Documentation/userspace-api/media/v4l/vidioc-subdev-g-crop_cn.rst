SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_G_CROP:

************************************************
ioctl VIDIOC_SUBDEV_G_CROP, VIDIOC_SUBDEV_S_CROP
************************************************

名称
====

VIDIOC_SUBDEV_G_CROP - VIDIOC_SUBDEV_S_CROP - 获取或设置子设备端口的裁剪矩形

概要
========

.. c:macro:: VIDIOC_SUBDEV_G_CROP

``int ioctl(int fd, VIDIOC_SUBDEV_G_CROP, struct v4l2_subdev_crop *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_CROP

``int ioctl(int fd, VIDIOC_SUBDEV_S_CROP, const struct v4l2_subdev_crop *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_crop` 的指针
描述
===========

.. note::

    这是一个 :ref:`已废弃` 的接口，未来可能会被移除。它已被 :ref:`选择 API <VIDIOC_SUBDEV_G_SELECTION>` 替代。不会再接受对 :c:type:`v4l2_subdev_crop` 结构的新扩展。
为了获取当前的裁剪矩形，应用程序需要将一个结构体 :c:type:`v4l2_subdev_crop` 的 ``pad`` 字段设置为媒体 API 报告的期望端口号，并将 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``。然后调用 ``VIDIOC_SUBDEV_G_CROP`` ioctl，传入指向该结构体的指针。如果输入参数无效或在指定端口上不支持裁剪，则驱动程序会填充 ``rect`` 字段成员或返回 ``EINVAL`` 错误码。
为了更改当前的裁剪矩形，应用程序需要设置 ``pad`` 和 ``which`` 字段以及 ``rect`` 字段的所有成员。然后通过指向该结构体的指针调用 ``VIDIOC_SUBDEV_S_CROP`` ioctl。驱动程序会验证请求的裁剪矩形，根据硬件能力进行调整，并配置设备。返回时，struct :c:type:`v4l2_subdev_crop` 包含的内容应与 ``VIDIOC_SUBDEV_G_CROP`` 调用返回的结果相同。
应用程序可以通过将 ``which`` 设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 来查询设备的能力。在这种情况下，驱动程序不会将 '尝试' 裁剪矩形应用于设备，而是像处理活动裁剪矩形一样处理它们，并将其存储在子设备文件句柄中。因此，两个应用程序查询同一个子设备时不会相互干扰。
如果子设备节点是以只读模式注册的，则只有当 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 时，对 ``VIDIOC_SUBDEV_S_CROP`` 的调用才是有效的，否则将返回错误，并将 errno 变量设置为 ``-EPERM``。
驱动程序不应仅因为请求的裁剪矩形不符合设备能力就返回错误。相反，它们应该修改裁剪矩形以匹配硬件能够提供的结果。修改后的格式应尽可能接近原始请求。

.. c:type:: v4l2_subdev_crop

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_subdev_crop
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pad``
      - 由媒体框架报告的端口号
* - __u32
      - ``which``
      - 要获取或设置的裁剪矩形，取自枚举
	:ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - 结构 :c:type:`v4l2_rect`
      - ``rect``
      - 裁剪矩形边界，以像素为单位
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\ [7]
      - 为将来扩展保留。应用程序和驱动程序必须将数组设置为零

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在
:ref:`通用错误码 <gen-errors>` 章节中描述。

EBUSY
    裁剪矩形无法更改，因为当前pad处于忙碌状态。这可能是由于pad上有活动的视频流。在尝试重新执行ioctl之前必须先执行其他操作来解决这个问题。仅由 ``VIDIOC_SUBDEV_S_CROP`` 返回。

EINVAL
    结构 :c:type:`v4l2_subdev_crop` 的 ``pad`` 引用了不存在的pad，
    或者 ``which`` 字段具有不支持的值，或者给定的子设备pad不支持裁剪

EPERM
    在只读子设备上调用了 ``VIDIOC_SUBDEV_S_CROP`` ioctl，并且 ``which`` 字段被设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``
