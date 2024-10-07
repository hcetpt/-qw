SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_ENUM_DV_TIMINGS:

**********************************************************************
ioctl VIDIOC_ENUM_DV_TIMINGS, VIDIOC_SUBDEV_ENUM_DV_TIMINGS
**********************************************************************

名称
====
VIDIOC_ENUM_DV_TIMINGS - VIDIOC_SUBDEV_ENUM_DV_TIMINGS - 列出支持的数字视频时序

概要
====
.. c:macro:: VIDIOC_ENUM_DV_TIMINGS

``int ioctl(int fd, VIDIOC_ENUM_DV_TIMINGS, struct v4l2_enum_dv_timings *argp)``

.. c:macro:: VIDIOC_SUBDEV_ENUM_DV_TIMINGS

``int ioctl(int fd, VIDIOC_SUBDEV_ENUM_DV_TIMINGS, struct v4l2_enum_dv_timings *argp)``

参数
====
``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_enum_dv_timings` 的指针

描述
====
尽管某些数字视频(DV)接收器或发射器支持广泛的时序，但其他设备仅支持有限数量的时序。通过此 ioctl，应用程序可以列出已知支持的时序。调用 :ref:`VIDIOC_DV_TIMINGS_CAP` 来检查是否还支持其他标准或不在此列表中的自定义时序。
为了查询可用的时序，应用程序初始化 ``index`` 字段，将 ``pad`` 字段设置为 0，并清零结构体 :c:type:`v4l2_enum_dv_timings` 中的保留数组，然后使用指向该结构体的指针对视频节点调用 ``VIDIOC_ENUM_DV_TIMINGS`` ioctl。驱动程序会填充结构体的其余部分，如果索引超出范围则返回 ``EINVAL`` 错误代码。为了枚举所有支持的 DV 时序，应用程序应从索引 0 开始，每次递增 1 直到驱动程序返回 ``EINVAL``。
.. note::
   驱动程序在切换视频输入或输出后可能会枚举不同的 DV 时序集合。

当驱动程序实现了该功能时，可以通过直接在子设备节点上调用 ``VIDIOC_SUBDEV_ENUM_DV_TIMINGS`` ioctl 来查询子设备的 DV 时序。DV 时序特定于输入（对于 DV 接收器）或输出（对于 DV 发射器），应用程序必须在结构体 :c:type:`v4l2_enum_dv_timings` 的 ``pad`` 字段中指定所需的端口编号。
尝试在不支持时序的端口上枚举时序将返回 ``EINVAL`` 错误代码
.. c:type:: v4l2_enum_dv_timings

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 v4l2_enum_dv_timings
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 数字视频时序的编号，由应用程序设置
* - __u32
      - ``pad``
      - 由媒体控制器 API 报告的端口号。此字段仅在操作子设备节点时使用。当操作视频节点时，应用程序必须将此字段设置为零
* - __u32
      - ``reserved``\ [2]
      - 保留以供将来扩展。驱动程序和应用程序必须将数组清零
* - 结构 :c:type:`v4l2_dv_timings`
      - ``timings``
      - 时序设置

返回值
======

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。

EINVAL
    结构 :c:type:`v4l2_enum_dv_timings` 的 ``index`` 超出了范围或 ``pad`` 编号无效
ENODATA
    对于此输入或输出不支持数字视频预设
