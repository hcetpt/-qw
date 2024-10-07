.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

******************************
单平面格式结构
******************************

.. tabularcolumns:: |p{4.0cm}|p{2.6cm}|p{10.7cm}|

.. c:type:: v4l2_pix_format

.. cssclass:: longtable

.. flat-table:: 结构 v4l2_pix_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``width``
      - 图像宽度（像素）
* - __u32
      - ``height``
      - 图像高度（像素）。如果 ``field`` 是 ``V4L2_FIELD_TOP``、``V4L2_FIELD_BOTTOM`` 或 ``V4L2_FIELD_ALTERNATE`` 中的一个，则高度指的是场中的行数，否则它指的是帧中的行数（对于隔行格式，帧的高度是场高度的两倍）
* - :cspan:`2` 应用程序设置这些字段以请求图像大小，驱动程序返回最接近的可能值。在平面格式的情况下，“width” 和 “height” 适用于最大的平面。为了避免歧义，驱动程序必须返回向上取整到任何较小平面的缩放因子的倍数的值。例如，当图像格式为 YUV 4:2:0 时，“width” 和 “height” 必须是二的倍数。
对于包含流内部分辨率信息的压缩格式，在输入到状态化的 mem2mem 解码器时，这些字段可以设为零，以便依赖解码器检测正确的值。更多细节见 :ref:`decoder` 和格式描述。
对于状态化 mem2mem 编码器的 CAPTURE 端的压缩格式，这些字段必须为零，因为编码大小预期由编码器根据 OUTPUT 端自行计算。更多细节见 :ref:`encoder` 和格式描述。
* - __u32
      - ``pixelformat``
      - 像素格式或压缩类型，由应用程序设置
这是小端模式的 :ref:`四个字符代码 <v4l2-fourcc>`。V4L2 在 :ref:`pixfmt-rgb` 中定义了标准的 RGB 格式，在 :ref:`yuv-formats` 中定义了 YUV 格式，并在 :ref:`reserved-formats` 中定义了保留代码。
    * - __u32
      - ``field``
      - 场顺序，来自枚举 :c:type:`v4l2_field`
视频图像通常是隔行扫描的。应用程序可以请求捕获或输出顶部场、底部场、隔行或逐行存储在一个缓冲区中或交替存储在单独的缓冲区中。驱动程序返回实际选择的场顺序。
关于场的更多细节见 :ref:`field-order`。
* - __u32
      - ``bytesperline``
      - 相邻两行左边缘像素之间的字节数距离
* - :cspan:`2`

	应用程序和驱动程序都可以设置此字段以请求在每行末尾添加填充字节。然而，驱动程序可能会忽略应用程序请求的值，返回 `width` 倍的每个像素字节数或硬件所需的更大值。这意味着应用程序可以将此字段设置为零以获得一个合理的默认值。
视频硬件可能会访问填充字节，因此它们必须位于可访问的内存中。考虑在图像的最后一行之后的填充字节跨越系统页面边界的情况。
输入设备可能会写入填充字节，其值是未定义的。
输出设备会忽略填充字节的内容。
当图像格式为平面（planar）时，`bytesperline` 值适用于第一平面，并且对于其他平面按与 `width` 字段相同的因子进行除法。例如，YUV 4:2:0 图像的 Cb 和 Cr 平面每行后面的填充字节数量是 Y 平面的一半。为了避免歧义，驱动程序必须返回一个向上取整到比例因子倍数的 `bytesperline` 值。
对于压缩格式，`bytesperline` 值没有意义。在这种情况下，应用程序和驱动程序必须将其设置为 0。
* - __u32
      - ``sizeimage``
      - 缓冲区大小（以字节为单位），用于保存完整的图像，由驱动程序设置。通常这是 `bytesperline` 乘以 `height`。当图像包含可变长度的压缩数据时，这是编解码器支持最坏情况压缩场景所需的字节数。
驱动程序将为未压缩图像设置该值。
客户端可以在带有 `V4L2_FMT_FLAG_COMPRESSED` 标志的可变长度压缩数据上设置 `sizeimage` 字段，但驱动程序可能会忽略它并自行设置该值，或者根据对齐要求或最小/最大尺寸要求修改提供的值。
如果客户端希望将此操作留给驱动程序，则应将 `sizeimage` 设置为 0。

* - `__u32`
      - `colorspace`
      - 图像颜色空间，取自枚举类型 `v4l2_colorspace`
这些信息补充了 `pixelformat`，对于捕获流必须由驱动程序设置，对于输出流则由应用程序设置。参见 :ref:`colorspaces`。如果应用程序设置了标志 `V4L2_PIX_FMT_FLAG_SET_CSC`，则应用程序可以在捕获流中设置该字段以请求特定的颜色空间来处理捕获的图像数据。如果驱动程序无法处理请求的转换，则会返回另一个支持的颜色空间。
驱动程序通过在枚举期间设置标志 `V4L2_FMT_FLAG_CSC_COLORSPACE` 来表明支持颜色空间转换。参见 :ref:`fmtdesc-flags`。
* - `__u32`
      - `priv`
      - 此字段表示结构体 `v4l2_pix_format` 的其余字段（也称为扩展字段）是否有效。当设置为 `V4L2_PIX_FMT_PRIV_MAGIC` 时，表示扩展字段已正确初始化。当设置为其他任何值时，表示扩展字段包含未定义的值。
希望使用像素格式扩展字段的应用程序必须首先确保设备支持此功能，通过查询设备的 :ref:`V4L2_CAP_EXT_PIX_FORMAT <querycap>` 能力。如果没有设置该能力，则不支持像素格式扩展字段，并且使用这些字段会导致未定义的结果。
要使用扩展字段，应用程序必须将 `priv` 字段设置为 `V4L2_PIX_FMT_PRIV_MAGIC`，初始化所有扩展字段，并将结构体 `v4l2_format` 的 `raw_data` 字段中的未使用字节置零。
当 `priv` 字段未设置为 `V4L2_PIX_FMT_PRIV_MAGIC` 时，驱动程序必须将所有扩展字段视为置零。
返回时，驱动程序必须将 `priv` 字段设置为 `V4L2_PIX_FMT_PRIV_MAGIC` 并将所有扩展字段设置为适用的值。
* - `__u32`
      - `flags`
      - 由应用程序或驱动程序设置的标志，参见 :ref:`format-flags`。
* - union {
      - (匿名结构体)
    * - __u32
      - ``ycbcr_enc``
      - Y'CbCr 编码，来自枚举 :c:type:`v4l2_ycbcr_encoding`
此信息补充了 ``colorspace``，对于捕获流必须由驱动程序设置，对于输出流必须由应用程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 ``V4L2_PIX_FMT_FLAG_SET_CSC``，则应用程序可以为捕获流设置该字段以请求特定的 Y'CbCr 编码。如果驱动程序无法处理请求的转换，则会返回另一个支持的编码。
对于 HSV 像素格式，此字段被忽略。驱动程序通过在枚举期间设置标志 V4L2_FMT_FLAG_CSC_YCBCR_ENC 来指示支持 ycbcr_enc 转换。详见 :ref:`fmtdesc-flags`。
* - __u32
      - ``hsv_enc``
      - HSV 编码，来自枚举 :c:type:`v4l2_hsv_encoding`
此信息补充了 ``colorspace``，对于捕获流必须由驱动程序设置，对于输出流必须由应用程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 ``V4L2_PIX_FMT_FLAG_SET_CSC``，则应用程序可以为捕获流设置该字段以请求特定的 HSV 编码。如果驱动程序无法处理请求的转换，则会返回另一个支持的编码。
对于非 HSV 像素格式，此字段被忽略。驱动程序通过在枚举期间设置标志 V4L2_FMT_FLAG_CSC_HSV_ENC 来指示支持 hsv_enc 转换。详见 :ref:`fmtdesc-flags`。
* - }
      -
    * - __u32
      - ``quantization``
      - 量化范围，来自枚举 :c:type:`v4l2_quantization`
此信息补充了 ``colorspace``，对于捕获流必须由驱动程序设置，对于输出流必须由应用程序设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 ``V4L2_PIX_FMT_FLAG_SET_CSC``，则应用程序可以为捕获流设置该字段以请求特定的量化范围。如果驱动程序无法处理请求的转换，则会返回另一个支持的量化范围。
驱动程序通过在枚举期间设置标志 V4L2_FMT_FLAG_CSC_QUANTIZATION 来指示支持量化转换。详见 :ref:`fmtdesc-flags`。
* - __u32
      - ``xfer_func``
      - 转移函数，来自枚举 :c:type:`v4l2_xfer_func`
此信息补充了“色彩空间”（``colorspace``），必须由驱动程序为捕获流设置，由应用程序为输出流设置，详见 :ref:`colorspaces`。如果应用程序设置了标志 ``V4L2_PIX_FMT_FLAG_SET_CSC``，则应用程序可以为捕获流设置该字段以请求特定的传输函数用于捕获的图像数据。如果驱动程序无法处理所请求的转换，则会返回另一个支持的传输函数。

驱动程序通过在枚举期间设置标志 `V4L2_FMT_FLAG_CSC_XFER_FUNC` 来表明支持 `xfer_func` 转换，在相应的结构体 :c:type:`v4l2_fmtdesc` 中设置。详见 :ref:`fmtdesc-flags`。

.. tabularcolumns:: |p{6.8cm}|p{2.3cm}|p{8.2cm}|

.. _format-flags:

.. flat-table:: 格式标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_PIX_FMT_FLAG_PREMUL_ALPHA``
      - 0x00000001
      - 颜色值被alpha通道值预乘。例如，如果一个半透明的浅蓝色像素用RGBA值（128, 192, 255, 128）表示，则使用预乘颜色表示的相同像素将用RGBA值（64, 96, 128, 128）表示。
    * .. _`v4l2-pix-fmt-flag-set-csc`:

      - ``V4L2_PIX_FMT_FLAG_SET_CSC``
      - 0x00000002
      - 由应用程序设置。仅用于捕获流，并且对输出流忽略。如果设置，则要求设备从接收到的色彩空间转换到请求的色彩空间值。如果色彩学字段（``colorspace``, ``xfer_func``, ``ycbcr_enc``, ``hsv_enc`` 或 ``quantization``）设置为 ``*_DEFAULT``，则该色彩学设置将保持不变。
因此，为了更改量化范围，仅需将 ``quantization`` 字段设置为非默认值（``V4L2_QUANTIZATION_FULL_RANGE`` 或 ``V4L2_QUANTIZATION_LIM_RANGE``），并将所有其他色彩学字段设置为 ``*_DEFAULT``。

要检查当前像素格式下硬件支持哪些转换，请参见 :ref:`fmtdesc-flags`。
