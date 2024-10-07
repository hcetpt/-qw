SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

**************************
多平面格式结构
**************************

`v4l2_plane_pix_format` 结构体定义了多平面格式中每个平面的大小和布局。`v4l2_pix_format_mplane` 结构体包含所有平面的通用信息（如图像宽度和高度），以及一个 `v4l2_plane_pix_format` 结构体数组，描述该格式的所有平面。

.. tabularcolumns:: |p{1.4cm}|p{4.0cm}|p{11.9cm}|

.. c:type:: v4l2_plane_pix_format

.. flat-table:: struct v4l2_plane_pix_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``sizeimage``
      - 在此平面上所需的图像数据的最大字节数，由驱动程序设置。当图像由长度可变的压缩数据组成时，这是编解码器支持最坏情况压缩场景所需的字节数。
        对于未压缩的图像，驱动程序会设置该值。
        客户端可以在带有 ``V4L2_FMT_FLAG_COMPRESSED`` 标志的 :ref:`VIDIOC_ENUM_FMT` 中设置 `sizeimage` 字段，但驱动程序可以忽略它并自行设置该值，或者根据对齐要求或最小/最大尺寸要求修改提供的值。
        如果客户端希望让驱动程序处理这个值，则应将 `sizeimage` 设置为 0。
    * - __u32
      - ``bytesperline``
      - 相邻两行中最左侧像素之间的字节距离。参见 `v4l2_pix_format` 结构体。
    * - __u16
      - ``reserved[6]``
      - 保留以供将来扩展。应由驱动程序和应用程序清零。

.. raw:: latex

    \small

.. tabularcolumns:: |p{4.4cm}|p{5.6cm}|p{7.3cm}|

.. c:type:: v4l2_pix_format_mplane

.. flat-table:: struct v4l2_pix_format_mplane
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``width``
      - 图像宽度（以像素为单位）。参见 `v4l2_pix_format` 结构体。
    * - __u32
      - ``height``
      - 图像高度（以像素为单位）。参见 `v4l2_pix_format` 结构体。
    * - __u32
      - ``pixelformat``
      - 像素格式。可以使用单平面或多平面的四个字符代码。
* - `__u32`
  - `field`
  - 场顺序，取自枚举 `v4l2_field`
  参见结构体 `v4l2_pix_format`

* - `__u32`
  - `colorspace`
  - 颜色空间编码，取自枚举 `v4l2_colorspace`
  参见结构体 `v4l2_pix_format`

* - 结构体 `v4l2_plane_pix_format`
  - `plane_fmt[VIDEO_MAX_PLANES]`
  - 描述该像素格式所包含每个平面格式的结构体数组。此数组中有效条目的数量需要放在 `num_planes` 字段中

* - `__u8`
  - `num_planes`
  - 该格式的平面（即独立内存缓冲区）数量以及 `plane_fmt` 数组中的有效条目数量

* - `__u8`
  - `flags`
  - 应用程序或驱动程序设置的标志，参见 `format-flags`

* - 联合体 {
  - （匿名）
  * - `__u8`
    - `ycbcr_enc`
    - Y'CbCr 编码，取自枚举 `v4l2_ycbcr_encoding`
    参见结构体 `v4l2_pix_format`

  * - `__u8`
    - `hsv_enc`
    - HSV 编码，取自枚举 `v4l2_hsv_encoding`
参见结构体 :c:type:`v4l2_pix_format`
* - `__u8`
      - ``quantization``
      - 量化范围，取自枚举 :c:type:`v4l2_quantization`
* - `__u8`
      - ``xfer_func``
      - 转换函数，取自枚举 :c:type:`v4l2_xfer_func`
* - `__u8`
      - ``reserved[7]``
      - 为将来扩展保留。驱动程序和应用程序应将其清零

.. raw:: latex

    \normalsize
