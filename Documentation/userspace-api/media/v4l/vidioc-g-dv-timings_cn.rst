SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_DV_TIMINGS:

**********************************************
ioctl VIDIOC_G_DV_TIMINGS, VIDIOC_S_DV_TIMINGS
**********************************************

名称
====

VIDIOC_G_DV_TIMINGS - VIDIOC_S_DV_TIMINGS - VIDIOC_SUBDEV_G_DV_TIMINGS - VIDIOC_SUBDEV_S_DV_TIMINGS - 获取或设置输入或输出的 DV 时序

概要
========

.. c:macro:: VIDIOC_G_DV_TIMINGS

``int ioctl(int fd, VIDIOC_G_DV_TIMINGS, struct v4l2_dv_timings *argp)``

.. c:macro:: VIDIOC_S_DV_TIMINGS

``int ioctl(int fd, VIDIOC_S_DV_TIMINGS, struct v4l2_dv_timings *argp)``

.. c:macro:: VIDIOC_SUBDEV_G_DV_TIMINGS

``int ioctl(int fd, VIDIOC_SUBDEV_G_DV_TIMINGS, struct v4l2_dv_timings *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_DV_TIMINGS

``int ioctl(int fd, VIDIOC_SUBDEV_S_DV_TIMINGS, struct v4l2_dv_timings *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_dv_timings` 的指针

描述
===========

为了设置输入或输出的 DV 时序，应用程序使用 :ref:`VIDIOC_S_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` ioctl。为了获取当前时序信息，应用程序使用 :ref:`VIDIOC_G_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` ioctl。详细的时序信息通过结构体 struct :c:type:`v4l2_dv_timings` 填充。这些 ioctl 接受指向 struct :c:type:`v4l2_dv_timings` 结构体的指针作为参数。如果 ioctl 不被支持或时序值不正确，驱动程序会返回 ``EINVAL`` 错误码。在只读模式下注册的子设备节点上调用 ``VIDIOC_SUBDEV_S_DV_TIMINGS`` 是不允许的，会返回错误并设置 errno 变量为 ``-EPERM``。
``linux/v4l2-dv-timings.h`` 头文件可以用来获取 :ref:`cea861` 和 :ref:`vesadmt` 标准中的格式时序。如果当前输入或输出不支持 DV 时序（例如，如果 :ref:`VIDIOC_ENUMINPUT` 没有设置 ``V4L2_IN_CAP_DV_TIMINGS`` 标志），则返回 ``ENODATA`` 错误码。

返回值
============

成功时返回 0，出错时返回 -1 并适当设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
    此 ioctl 不被支持，或者 :ref:`VIDIOC_S_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` 参数不合适
ENODATA
    输入或输出不支持数字视频时序
EBUSY
    设备忙，因此不能改变时序
EPERM
    在只读子设备上调用了 ``VIDIOC_SUBDEV_S_DV_TIMINGS``
```markdown
.. c:type:: v4l2_bt_timings

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_bt_timings
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``width``
      - 活动视频的宽度（像素）
    * - __u32
      - ``height``
      - 活动视频帧的高度（行数）。对于交错格式，每个场的活动视频高度为 ``height`` / 2
    * - __u32
      - ``interlaced``
      - 进步（``V4L2_DV_PROGRESSIVE``）或交错（``V4L2_DV_INTERLACED``）
    * - __u32
      - ``polarities``
      - 这是一个位掩码，定义了同步信号的极性。位 0 （``V4L2_DV_VSYNC_POS_POL``）表示垂直同步极性，位 1 （``V4L2_DV_HSYNC_POS_POL``）表示水平同步极性。如果该位被设置（1），则为正极性；如果被清除（0），则为负极性
    * - __u64
      - ``pixelclock``
      - 像素时钟（赫兹）。例如：74.25 MHz -> 74250000
    * - __u32
      - ``hfrontporch``
      - 水平前廊（像素）
    * - __u32
      - ``hsync``
      - 水平同步长度（像素）
    * - __u32
      - ``hbackporch``
      - 水平后廊（像素）
    * - __u32
      - ``vfrontporch``
      - 垂直前廊（行数）。对于交错格式，这指的是奇数场（即场 1）
    * - __u32
      - ``vsync``
      - 垂直同步长度（行数）。对于交错格式，这指的是奇数场（即场 1）
    * - __u32
      - ``vbackporch``
      - 垂直后廊（行数）。对于交错格式，这指的是奇数场（即场 1）
    * - __u32
      - ``il_vfrontporch``
      - 交错格式中偶数场（即场 2）的垂直前廊（行数）。对于进步格式必须为 0
    * - __u32
      - ``il_vsync``
      - 交错格式中偶数场（即场 2）的垂直同步长度（行数）。对于进步格式必须为 0
    * - __u32
      - ``il_vbackporch``
      - 交错格式中偶数场（即场 2）的垂直后廊（行数）。对于进步格式必须为 0
```
* - __u32
  - ``standards``
  - 此格式所属的视频标准。这将由驱动程序填充。应用程序必须将其设置为 0。参见 :ref:`dv-bt-standards` 获取标准列表。
* - __u32
  - ``flags``
  - 提供更多格式信息的多个标志位。参见 :ref:`dv-bt-flags` 获取标志位描述。
* - struct :c:type:`v4l2_fract`
  - ``picture_aspect``
  - 如果像素不是正方形，则为图像宽高比。仅在设置了 ``V4L2_DV_FL_HAS_PICTURE_ASPECT`` 标志时有效。
* - __u8
  - ``cea861_vic``
  - 根据CEA-861标准的视频识别码。仅在设置了 ``V4L2_DV_FL_HAS_CEA861_VIC`` 标志时有效。
* - __u8
  - ``hdmi_vic``
  - 根据HDMI标准的视频识别码。仅在设置了 ``V4L2_DV_FL_HAS_HDMI_VIC`` 标志时有效。
* - __u8
  - ``reserved[46]``
  - 预留以备将来扩展。驱动程序和应用程序必须将数组设置为零。

.. tabularcolumns:: |p{3.5cm}|p{3.5cm}|p{7.0cm}|p{3.1cm}|

.. c:type:: v4l2_dv_timings

.. flat-table:: struct v4l2_dv_timings
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 如 :ref:`dv-timing-types` 所列的DV定时类型。
* - union {
      - (匿名)
    * - struct :c:type:`v4l2_bt_timings`
      - ``bt``
      - 根据BT.656/1120规范定义的定时。
    * - __u32
      - ``reserved``\ [32]
      -
    * - }
      -

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. _dv-timing-types:

.. flat-table:: DV Timing 类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - 定时类型
      - 值
      - 描述
    * -
      -
      -
    * - ``V4L2_DV_BT_656_1120``
      - 0
      - BT.656/1120 定时

.. tabularcolumns:: |p{6.5cm}|p{11.0cm}|

.. cssclass:: longtable

.. _dv-bt-standards:

.. flat-table:: DV BT 定时标准
    :header-rows:  0
    :stub-columns: 0

    * - 定时标准
      - 描述
    * - ``V4L2_DV_BT_STD_CEA861``
      - 定时遵循 CEA-861 数字电视配置文件标准。
    * - ``V4L2_DV_BT_STD_DMT``
      - 定时遵循 VESA 离散监视器定时标准。
    * - ``V4L2_DV_BT_STD_CVT``
      - 定时遵循 VESA 协调视频定时标准。
    * - ``V4L2_DV_BT_STD_GTF``
      - 定时遵循 VESA 通用定时公式标准。
    * - ``V4L2_DV_BT_STD_SDI``
      - 定时遵循 SDI 定时标准。
在这个格式中，没有任何水平同步信号/门廊。
总消隐时间必须仅设置在垂直同步或水平同步字段中。

.. tabularcolumns:: |p{7.7cm}|p{9.8cm}|

.. cssclass:: longtable

.. _dv-bt-flags:

.. flat-table:: DV BT 定时标志
    :header-rows:  0
    :stub-columns: 0

    * - 标志
      - 描述
    * - ``V4L2_DV_FL_REDUCED_BLANKING``
      - CVT/GTF 特定：该定时使用了减少的消隐时间（CVT）或“次级 GTF”曲线（GTF）。在这两种情况下，水平和/或垂直消隐间隔被缩短，允许在同一带宽下实现更高的分辨率。这是一个只读标志，应用程序不应设置此标志。
    * - ``V4L2_DV_FL_CAN_REDUCE_FPS``
      - CEA-861 特定：对于 CEA-861 格式，如果帧率是六的倍数，则设置此标志。这些格式可以以 1/1.001 的速度可选地播放，以便与使用 29.97 帧每秒帧率的标准（如 NTSC 和 PAL-M）兼容。如果发射器不能生成这样的频率，则该标志也会被清除。这是一个只读标志，应用程序不应设置此标志。
    * - ``V4L2_DV_FL_REDUCED_FPS``
      - CEA-861 特定：仅对设置了 ``V4L2_DV_FL_CAN_DETECT_REDUCED_FPS`` 的视频发射器或视频接收器有效。否则，此标志将被清除。它也仅对设置了 ``V4L2_DV_FL_CAN_REDUCE_FPS`` 标志的格式有效，对于其他格式，驱动程序会清除该标志。
        如果应用程序为发射器设置了此标志，则用于设置发射器的像素时钟将除以 1.001，使其与 NTSC 帧率兼容。如果发射器无法生成这样的频率，则该标志会被清除。
        如果视频接收器检测到格式使用了降低的帧率，则会设置此标志以向应用程序发出信号。
    * - ``V4L2_DV_FL_HALF_LINE``
      - 仅适用于隔行扫描格式：如果设置，则场 1（即奇数场）的垂直前消隐实际上比半行长，场 2（即偶数场）的垂直后消隐实际上比半行短，因此每个场具有完全相同的半行数。是否能检测或使用半行取决于硬件。
    * - ``V4L2_DV_FL_IS_CE_VIDEO``
      - 如果设置，则这是消费电子（CE）视频格式。
        这种格式与其他格式（通常称为 IT 格式）的区别在于，默认情况下，如果使用 R'G'B' 编码，则 R'G'B' 值使用有限范围（即 16-235），而不是全范围（即 0-255）。CEA-861 中定义的所有格式（除了 640x480p59.94 格式）都是 CE 格式。
* - ``V4L2_DV_FL_FIRST_FIELD_EXTRA_LINE``
  - 某些格式（如 SMPTE-125M）具有奇数总高度的交错信号。对于这些格式，如果设置了此标志，则第一场包含额外的一行。否则，是第二场包含额外的一行。
* - ``V4L2_DV_FL_HAS_PICTURE_ASPECT``
  - 如果设置了此标志，则 picture_aspect 字段有效。否则，默认像素为正方形，因此图像宽高比等于宽度与高度的比例。
* - ``V4L2_DV_FL_HAS_CEA861_VIC``
  - 如果设置了此标志，则 cea861_vic 字段有效，并且包含符合 CEA-861 标准的视频识别码。
* - ``V4L2_DV_FL_HAS_HDMI_VIC``
  - 如果设置了此标志，则 hdmi_vic 字段有效，并且包含符合 HDMI 标准（HDMI 厂商特定 InfoFrame）的视频识别码。
* - ``V4L2_DV_FL_CAN_DETECT_REDUCED_FPS``
  - CEA-861 特定：仅对视频接收器有效，发射器会清除该标志。
  - 如果设置了此标志，则硬件可以检测常规帧率与减少 1000/1001 的帧率之间的差异。例如：60 Hz 与 59.94 Hz、30 Hz 与 29.97 Hz 或 24 Hz 与 23.976 Hz。
