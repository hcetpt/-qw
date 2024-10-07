以下是翻译后的中文内容：

SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _v4l2-mbus-format:

媒体总线格式
=============

.. c:type:: v4l2_mbus_framefmt

.. tabularcolumns:: |p{2.0cm}|p{4.0cm}|p{11.3cm}|

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_mbus_framefmt
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``width``
      - 图像宽度（像素）
* - __u32
      - ``height``
      - 图像高度（像素）。如果 ``field`` 是 ``V4L2_FIELD_TOP``、``V4L2_FIELD_BOTTOM`` 或 ``V4L2_FIELD_ALTERNATE`` 中的一个，则高度指的是场中的行数；否则，它指的是帧中的行数（对于隔行扫描格式，帧的高度是场高度的两倍）
* - __u32
      - ``code``
      - 格式代码，取自枚举 :ref:`v4l2_mbus_pixelcode <v4l2-mbus-pixelcode>`
* - __u32
      - ``field``
      - 场顺序，取自枚举 :c:type:`v4l2_field`。详情请参见 :ref:`field-order`。对于元数据媒体总线代码为零
* - __u32
      - ``colorspace``
      - 图像色彩空间，取自枚举 :c:type:`v4l2_colorspace`。必须由驱动程序为子设备设置。如果应用程序设置了标志 ``V4L2_MBUS_FRAMEFMT_SET_CSC``，则应用程序可以在源端口上设置此字段以请求特定的媒体总线数据色彩空间。如果驱动程序无法处理请求的转换，它将返回另一个支持的色彩空间。驱动程序通过在枚举期间设置标志 `V4L2_SUBDEV_MBUS_CODE_CSC_COLORSPACE` 来指示支持色彩空间转换。对于元数据媒体总线代码为零
* - union {
      - （匿名）
    * - __u16
      - ``ycbcr_enc``
      - Y'CbCr 编码，取自枚举 :c:type:`v4l2_ycbcr_encoding`。此信息补充了 ``colorspace`` 并且必须由驱动程序为子设备设置，请参见 :ref:`colorspaces`。如果应用程序设置了标志 ``V4L2_MBUS_FRAMEFMT_SET_CSC``，则应用程序可以在源端口上设置此字段以请求特定的媒体总线数据 Y'CbCr 编码。如果驱动程序无法处理请求的转换，它将返回另一个支持的编码。对于 HSV 媒体总线格式，此字段被忽略。驱动程序通过在枚举期间设置标志 `V4L2_SUBDEV_MBUS_CODE_CSC_YCBCR_ENC` 来指示支持 Y'CbCr 编码转换
参见 :ref:`v4l2-subdev-mbus-code-flags`。对于元数据媒体总线代码，此字段为零。
* - __u16
      - ``hsv_enc``
      - HSV 编码，取自枚举类型 :c:type:`v4l2_hsv_encoding`
此信息补充了 `colorspace` 并且必须由子设备的驱动程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 `V4L2_MBUS_FRAMEFMT_SET_CSC`，则应用程序可以在源垫上设置此字段以请求特定的 HSV 编码。如果驱动程序无法处理所请求的转换，则会返回另一个支持的编码。
对于 Y'CbCr 媒体总线格式，此字段被忽略。驱动程序通过在枚举期间设置相应的结构体 :c:type:`v4l2_subdev_mbus_code_enum` 中的标志 V4L2_SUBDEV_MBUS_CODE_CSC_HSV_ENC 来表明支持 HSV 编码转换。

参见 :ref:`v4l2-subdev-mbus-code-flags`。对于元数据媒体总线代码，此字段为零。
* - }
      -
    * - __u16
      - ``quantization``
      - 量化范围，取自枚举类型 :c:type:`v4l2_quantization`
此信息补充了 `colorspace` 并且必须由子设备的驱动程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 `V4L2_MBUS_FRAMEFMT_SET_CSC`，则应用程序可以在源垫上设置此字段以请求特定的量化范围。如果驱动程序无法处理所请求的转换，则会返回另一个支持的量化范围。
驱动程序通过在枚举期间设置相应的结构体 :c:type:`v4l2_subdev_mbus_code_enum` 中的标志 V4L2_SUBDEV_MBUS_CODE_CSC_QUANTIZATION 来表明支持量化转换。参见 :ref:`v4l2-subdev-mbus-code-flags`。对于元数据媒体总线代码，此字段为零。
* - __u16
      - ``xfer_func``
      - 转换函数，取自枚举类型 :c:type:`v4l2_xfer_func`
此信息补充了 `colorspace` 并且必须由子设备的驱动程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 `V4L2_MBUS_FRAMEFMT_SET_CSC`，则应用程序可以在源垫上设置此字段以请求特定的转换函数。如果驱动程序无法处理所请求的转换，则会返回另一个支持的转换函数。
驾驶员通过在相应的 `v4l2_subdev_mbus_code_enum` 结构体中设置标志 `V4L2_SUBDEV_MBUS_CODE_CSC_XFER_FUNC` 来表明支持转换函数转换。参见 :ref:`v4l2-subdev-mbus-code-flags`。对于元数据媒体总线代码，值为零。

* - `__u16`
      - `flags`
      - 标志 参见 :ref:`v4l2-mbus-framefmt-flags`
    * - `__u16`
      - `reserved`[10]
      - 保留供将来扩展使用。应用程序和驱动程序必须将数组设置为零

.. _v4l2-mbus-framefmt-flags:

.. tabularcolumns:: |p{6.5cm}|p{1.6cm}|p{9.2cm}|

.. flat-table:: v4l2_mbus_framefmt 标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`mbus-framefmt-set-csc`:

      - `V4L2_MBUS_FRAMEFMT_SET_CSC`
      - 0x0001
      - 由应用程序设置。仅用于源端口，并且在接收端口上被忽略。如果设置，则要求子设备执行从接收到的颜色空间到请求的颜色空间的转换。如果色度字段（`colorspace`、`xfer_func`、`ycbcr_enc`、`hsv_enc` 或 `quantization`）设置为 `*_DEFAULT`，则该色度设置将保持不变。
因此，为了改变量化值，只有 `quantization` 字段应设置为非默认值（`V4L2_QUANTIZATION_FULL_RANGE` 或 `V4L2_QUANTIZATION_LIM_RANGE`），而其他所有色度字段应设置为 `*_DEFAULT`。
要检查硬件当前支持哪些转换，请参见 :ref:`v4l2-subdev-mbus-code-flags`。

.. _v4l2-mbus-pixelcode:

媒体总线像素代码
---------------------

媒体总线像素代码描述了图像格式在物理总线上流动的情况（既包括独立物理组件之间也包括 SoC 设备内部）。这不应与描述存储在内存中的图像格式的 V4L2 像素格式混淆。
虽然总线上的图像格式与内存中的图像格式之间存在某种关系（例如，原始 Bayer 图像不会因为存储到内存中就神奇地变成 JPEG），但它们之间并不存在一一对应的关系。
媒体总线像素代码文档描述了并行格式。如果像素数据通过串行总线传输，则使用描述单个时钟周期内传输一个样本的并行格式的媒体总线像素代码。例如，MEDIA_BUS_FMT_BGR888_1X24 和 MEDIA_BUS_FMT_BGR888_3X8 都用于并行总线上传输每样本 8 位的 BGR 数据，而在串行总线上，这种格式的数据仅使用 MEDIA_BUS_FMT_BGR888_1X24 来指代。这是因为这种格式在串行总线上实际上只有一种传输方式。

紧凑的 RGB 格式
^^^^^^^^^^^^^^^^^^

这些格式以红色、绿色和蓝色组件的形式传输像素数据。格式代码包含以下信息：
- 红色、绿色和蓝色组件在像素样本中的顺序编码。可能的值是 RGB 和 BGR。
