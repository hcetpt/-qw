SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_ENUM_FRAME_SIZE:

***********************************
ioctl VIDIOC_SUBDEV_ENUM_FRAME_SIZE
***********************************

名称
====

VIDIOC_SUBDEV_ENUM_FRAME_SIZE - 列出媒体总线帧大小

简介
========

.. c:macro:: VIDIOC_SUBDEV_ENUM_FRAME_SIZE

``int ioctl(int fd, VIDIOC_SUBDEV_ENUM_FRAME_SIZE, struct v4l2_subdev_frame_size_enum * argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_frame_size_enum` 的指针
描述
===========

此 ioctl 允许应用程序访问指定 pad 上子设备支持的帧大小枚举，这些帧大小针对指定的媒体总线格式。
支持的格式可以通过 :ref:`VIDIOC_SUBDEV_ENUM_MBUS_CODE` ioctl 获取。
这些枚举由驱动程序定义，并通过结构体 :c:type:`v4l2_subdev_frame_size_enum` 中的 ``index`` 字段进行索引。
每一对 ``pad`` 和 ``code`` 对应一个单独的枚举。
每个枚举从 ``index`` 为 0 开始，最低的无效索引标记枚举的结束。
因此，为了枚举指定 pad 上允许的帧大小以及使用的特定媒体总线格式，需要初始化 ``pad``、``which`` 和 ``code`` 字段为所需值，并将 ``index`` 设置为 0。
然后使用指向该结构体的指针调用 :ref:`VIDIOC_SUBDEV_ENUM_FRAME_SIZE` ioctl。
成功调用后，将返回最小和最大帧大小。
重复增加`index`，直到收到`EINVAL`
`EINVAL`表示枚举中没有更多的条目，或者输入参数无效
仅支持离散帧大小的子设备（如大多数传感器）将返回一个或多个具有相同最小值和最大值的帧大小
在给定的[最小值，最大值]范围内，并非所有可能的尺寸都需要被支持。例如，使用固定点缩放比例的缩放器可能无法生成最小值和最大值之间的每个帧大小。应用程序必须使用`:ref: VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` ioctl来尝试子设备的确切支持帧大小
可用的帧大小可能取决于子设备其他端口上的当前“尝试”格式，以及当前活动链接和V4L2控制的当前值。有关“尝试”格式的更多信息，请参阅`:ref: VIDIOC_SUBDEV_G_FMT`

.. c:type:: v4l2_subdev_frame_size_enum

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_subdev_frame_size_enum
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 属于给定端口和格式的帧大小在枚举中的索引。由应用程序填写
    * - __u32
      - ``pad``
      - 由媒体控制器API报告的端口号。由应用程序填写
    * - __u32
      - ``code``
      - 媒体总线格式代码，如`:ref: v4l2-mbus-format`中定义。由应用程序填写
    * - __u32
      - ``min_width``
      - 最小帧宽度，以像素为单位。由驱动程序填写
* - __u32
      - ``max_width``
      - 最大帧宽度，以像素为单位。由驱动程序填充
* - __u32
      - ``min_height``
      - 最小帧高度，以像素为单位。由驱动程序填充
* - __u32
      - ``max_height``
      - 最大帧高度，以像素为单位。由驱动程序填充
* - __u32
      - ``which``
      - 要枚举的帧尺寸，取自枚举 :ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\ [7]
      - 保留用于将来扩展。应用程序和驱动程序必须将数组设置为零

返回值
======

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    结构 :c:type:`v4l2_subdev_frame_size_enum` 的 ``pad`` 引用了不存在的端口，或者 ``which`` 字段具有不支持的值，或者 ``code`` 对给定的端口无效，或者 ``index`` 字段超出范围。
