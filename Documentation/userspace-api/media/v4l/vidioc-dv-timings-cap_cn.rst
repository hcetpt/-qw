SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_DV_TIMINGS_CAP:

*********************************************************
ioctl VIDIOC_DV_TIMINGS_CAP, VIDIOC_SUBDEV_DV_TIMINGS_CAP
*********************************************************

名称
====

VIDIOC_DV_TIMINGS_CAP - VIDIOC_SUBDEV_DV_TIMINGS_CAP - 数字视频接收器/发射器的能力

概要
========

.. c:macro:: VIDIOC_DV_TIMINGS_CAP

``int ioctl(int fd, VIDIOC_DV_TIMINGS_CAP, struct v4l2_dv_timings_cap *argp)``

.. c:macro:: VIDIOC_SUBDEV_DV_TIMINGS_CAP

``int ioctl(int fd, VIDIOC_SUBDEV_DV_TIMINGS_CAP, struct v4l2_dv_timings_cap *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_dv_timings_cap` 的指针
描述
===========

为了查询数字视频(DV)接收器/发射器的能力，应用程序需要将 ``pad`` 字段初始化为0，并清空结构体 :c:type:`v4l2_dv_timings_cap` 中的保留数组，然后在视频节点上调用 ``VIDIOC_DV_TIMINGS_CAP`` ioctl，驱动程序将填充该结构。
.. note::

   驱动程序可能在切换视频输入或输出后返回不同的值。

当驱动程序实现了这一功能时，可以通过直接在子设备节点上调用 ``VIDIOC_SUBDEV_DV_TIMINGS_CAP`` ioctl 来查询子设备的 DV 能力。这些能力是特定于输入（对于 DV 接收器）或输出（对于 DV 发射器），应用程序必须在结构体 :c:type:`v4l2_dv_timings_cap` 的 ``pad`` 字段中指定所需的端口编号，并清空 ``reserved`` 数组。尝试查询不支持这些能力的端口会返回 ``EINVAL`` 错误代码。
.. tabularcolumns:: |p{1.2cm}|p{3.2cm}|p{12.9cm}|

.. c:type:: v4l2_bt_timings_cap

.. flat-table:: struct v4l2_bt_timings_cap
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``min_width``
      - 活动视频的最小宽度（像素）
    * - __u32
      - ``max_width``
      - 活动视频的最大宽度（像素）
    * - __u32
      - ``min_height``
      - 活动视频的最小高度（行数）
    * - __u32
      - ``max_height``
      - 活动视频的最大高度（行数）
    * - __u64
      - ``min_pixelclock``
      - 最小像素时钟频率（赫兹Hz）
* - __u64
  - ``max_pixelclock``
  - 最大像素时钟频率（赫兹Hz）
* - __u32
  - ``standards``
  - 硬件支持的视频标准。请参阅 :ref:`dv-bt-standards` 获取标准列表
* - __u32
  - ``capabilities``
  - 多个标志位，提供更多关于硬件功能的信息。请参阅 :ref:`dv-bt-cap-capabilities` 获取标志位描述
* - __u32
  - ``reserved``\[16\]
  - 为未来扩展保留。驱动程序必须将此数组设置为零
表格列定义：|p{4.4cm}|p{3.6cm}|p{9.3cm}|

.. c:type:: v4l2_dv_timings_cap

.. flat-table:: 结构体 v4l2_dv_timings_cap
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - DV定时类型，详见 :ref:`dv-timing-types`
    * - __u32
      - ``pad``
      - 媒体控制器API报告的端口号。仅在子设备节点操作时使用该字段。在视频节点上操作时，应用程序必须将此字段设置为零
    * - __u32
      - ``reserved``\[2\]
      - 为未来扩展保留。驱动程序和应用程序必须将此数组设置为零
    * - union {
      - （匿名）
    * - struct :c:type:`v4l2_bt_timings_cap`
      - ``bt``
      - 硬件的BT.656/1120定时能力
```markdown
* - __u32
  - ``raw_data`` [32]
* - }
  -

.. tabularcolumns:: |p{7.2cm}|p{10.3cm}|

.. _dv-bt-cap-capabilities:

.. flat-table:: DV BT 定时功能
    :header-rows:  0
    :stub-columns: 0

    * - 标志
      - 描述
    * -
      -
    * - ``V4L2_DV_BT_CAP_INTERLACED``
      - 支持隔行扫描格式
* - ``V4L2_DV_BT_CAP_PROGRESSIVE``
      - 支持逐行扫描格式
* - ``V4L2_DV_BT_CAP_REDUCED_BLANKING``
      - CVT/GTF 特定：定时可以使用减少的消隐（CVT）或“次级 GTF”曲线（GTF）
* - ``V4L2_DV_BT_CAP_CUSTOM``
      - 可以支持非标准定时，即不属于 ``standards`` 字段中定义的标准集的定时

返回值
======

成功时返回 0，错误时返回 -1 并设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述。
```
