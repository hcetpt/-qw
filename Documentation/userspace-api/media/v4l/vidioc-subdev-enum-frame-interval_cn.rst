SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL:

***************************************
ioctl VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL
***************************************

名称
====

VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL - 列出帧间隔

概要
========

.. c:macro:: VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL

``int ioctl(int fd, VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL, struct v4l2_subdev_frame_interval_enum * argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_subdev_frame_interval_enum` 结构体的指针
描述
===========

此 ioctl 使应用程序能够枚举给定子设备端口上的可用帧间隔。帧间隔仅对那些能够独立控制其帧周期的子设备有意义。这包括，例如，图像传感器和电视调谐器。
对于图像传感器的常见用例，子设备输出端口上的可用帧间隔取决于同一端口上的帧格式和大小。因此，应用程序在枚举帧间隔时必须指定所需的格式和大小。
为了枚举帧间隔，应用程序需要初始化结构 :c:type:`v4l2_subdev_frame_interval_enum` 中的 ``index``、``pad``、``which``、``code``、``width`` 和 ``height`` 字段，并使用指向该结构的指针调用 :ref:`VIDIOC_SUBDEV_ENUM_FRAME_INTERVAL` ioctl。如果输入字段中的任何一个无效，则驱动程序会填充其余部分或返回 EINVAL 错误代码。所有帧间隔都可以从索引零开始并逐个递增直到返回 ``EINVAL``。
可用帧间隔可能依赖于子设备其他端口上的当前“尝试”格式以及当前活动链接。有关“尝试”格式的更多信息，请参阅 :ref:`VIDIOC_SUBDEV_G_FMT`。
支持帧间隔枚举 ioctl 的子设备应在单个端口上实现它。在同一子设备的多个端口上支持它的行为是未定义的。

.. c:type:: v4l2_subdev_frame_interval_enum

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_subdev_frame_interval_enum
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 枚举中的格式编号，由应用程序设置
    * - __u32
      - ``pad``
      - 由媒体控制器 API 报告的端口号
* - __u32
      - ``code``
      - 媒体总线格式代码，如 :ref:`v4l2-mbus-format` 中定义的
* - __u32
      - ``width``
      - 帧宽度，以像素为单位
* - __u32
      - ``height``
      - 帧高度，以像素为单位
* - struct :c:type:`v4l2_fract`
      - ``interval``
      - 相邻视频帧之间的周期，以秒为单位
* - __u32
      - ``which``
      - 要枚举的帧间隔，来自枚举 :ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\[7\]
      - 保留供将来扩展使用。应用程序和驱动程序必须将数组设置为零

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量。通用错误码在
:ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    结构体 :c:type:`v4l2_subdev_frame_interval_enum` 的 ``pad`` 引用了不存在的 pad，或者 ``which`` 字段包含不支持的值，或者 ``code``、``width`` 或 ``height`` 字段对于给定的 pad 是无效的，或者 ``index`` 字段越界。
