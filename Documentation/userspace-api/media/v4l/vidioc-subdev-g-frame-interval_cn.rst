SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

C 命名空间: V4L

.. _VIDIOC_SUBDEV_G_FRAME_INTERVAL:

********************************************************************
ioctl VIDIOC_SUBDEV_G_FRAME_INTERVAL, VIDIOC_SUBDEV_S_FRAME_INTERVAL
********************************************************************

名称
====

VIDIOC_SUBDEV_G_FRAME_INTERVAL - VIDIOC_SUBDEV_S_FRAME_INTERVAL - 获取或设置子设备端口上的帧间隔

概述
========

.. c:macro:: VIDIOC_SUBDEV_G_FRAME_INTERVAL

``int ioctl(int fd, VIDIOC_SUBDEV_G_FRAME_INTERVAL, struct v4l2_subdev_frame_interval *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_FRAME_INTERVAL

``int ioctl(int fd, VIDIOC_SUBDEV_S_FRAME_INTERVAL, struct v4l2_subdev_frame_interval *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_frame_interval` 的指针
描述
===========

这些 ioctl 用于获取和设置图像管道中特定子设备端口上的帧间隔。帧间隔仅适用于能够独立控制其帧周期的子设备。这包括例如图像传感器和电视调谐器。不支持帧间隔的子设备不得实现这些 ioctl。

为了获取当前帧间隔，应用程序需要将结构体 :c:type:`v4l2_subdev_frame_interval` 的 ``pad`` 字段设置为媒体控制器 API 报告的目标端口号。当它们使用指向此结构体的指针调用 ``VIDIOC_SUBDEV_G_FRAME_INTERVAL`` ioctl 时，驱动程序会填充 ``interval`` 字段中的成员。

为了更改当前帧间隔，应用程序需要同时设置 ``pad`` 字段和 ``interval`` 字段的所有成员。当它们使用指向此结构体的指针调用 ``VIDIOC_SUBDEV_S_FRAME_INTERVAL`` ioctl 时，驱动程序会验证请求的间隔，并根据硬件能力进行调整并配置设备。返回时，结构体 :c:type:`v4l2_subdev_frame_interval` 包含的内容应与通过 ``VIDIOC_SUBDEV_G_FRAME_INTERVAL`` 调用返回的当前帧间隔相同。

如果子设备节点是以只读模式注册的，则只有当 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 时，对 ``VIDIOC_SUBDEV_S_FRAME_INTERVAL`` 的调用才是有效的；否则将返回错误并将 errno 变量设置为 ``-EPERM``。

驱动程序不得仅仅因为请求的间隔不符合设备能力就返回错误。相反，它们必须修改间隔以匹配硬件可以提供的值。修改后的间隔应尽可能接近原始请求。

更改帧间隔不应改变格式。而更改格式可能会改变帧间隔。

支持帧间隔 ioctl 的子设备应仅在一个端口上实现它们。在同一个子设备的多个端口上支持它们的行为是未定义的。

.. c:type:: v4l2_subdev_frame_interval

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_subdev_frame_interval
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pad``
      - 媒体控制器 API 报告的端口号
* - 结构 :c:type:`v4l2_fract`
      - ``interval``
      - 连续视频帧之间的秒数间隔
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``which``
      - 活动或尝试帧间隔，来自枚举
	:ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - __u32
      - ``reserved``\[7\]
      - 为将来扩展保留。应用程序和驱动程序必须将数组设置为零

返回值
======

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EBUSY
    帧间隔无法更改，因为端口当前处于忙碌状态。这可能是由于端口上有活动的视频流导致的。在没有首先执行其他操作来解决问题之前，不应重试此 ioctl。仅由
    ``VIDIOC_SUBDEV_S_FRAME_INTERVAL`` 返回。

EINVAL
    结构 :c:type:`v4l2_subdev_frame_interval` 的 ``pad`` 引用了不存在的端口，或者 ``which`` 字段包含不受支持的值，或者该端口不支持帧间隔

EPERM
    在只读子设备上调用 ``VIDIOC_SUBDEV_S_FRAME_INTERVAL`` ioctl 并且 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``
