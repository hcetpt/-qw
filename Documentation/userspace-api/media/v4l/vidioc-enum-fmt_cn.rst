SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _VIDIOC_ENUM_FMT:

*********************
ioctl VIDIOC_ENUM_FMT
*********************

名称
====

VIDIOC_ENUM_FMT - 列出图像格式

概要
====

.. c:macro:: VIDIOC_ENUM_FMT

``int ioctl(int fd, VIDIOC_ENUM_FMT, struct v4l2_fmtdesc *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_fmtdesc` 的指针
描述
===========

为了列出图像格式，应用程序需要初始化结构体 :c:type:`v4l2_fmtdesc` 中的 ``type``、``mbus_code`` 和 ``index`` 字段，并使用指向该结构体的指针调用 :ref:`VIDIOC_ENUM_FMT` ioctl。驱动程序将填充结构体的其余部分或返回一个 ``EINVAL`` 错误代码。所有格式都可以从索引为零开始逐个递增直到返回 ``EINVAL`` 来进行枚举。如果适用，驱动程序应当按照优先级顺序返回格式，其中优先级较高的格式（即具有较低的 ``index`` 值）会先于优先级较低的格式被返回。

根据 ``V4L2_CAP_IO_MC`` :ref:`功能 <device-capabilities>`，``mbus_code`` 字段的处理方式不同：

1) 如果没有设置 ``V4L2_CAP_IO_MC``（也称为“视频节点为中心”的驱动程序）

   应用程序应将 ``mbus_code`` 字段初始化为零，而驱动程序应忽略该字段的值。
   驱动程序应当枚举所有图像格式。
   .. note::
   
      在切换输入或输出后，枚举的图像格式列表可能会有所不同。

2) 如果设置了 ``V4L2_CAP_IO_MC``（也称为“MC为中心”的驱动程序）

   如果 ``mbus_code`` 字段为零，则应枚举所有图像格式；
   如果 ``mbus_code`` 字段被初始化为一个有效的（非零的）:ref:`媒体总线格式代码 <v4l2-mbus-pixelcode>`，则驱动程序应仅枚举能够生成（对于视频输出设备）或能从中生成（对于视频捕获设备）该媒体总线代码的图像格式。如果驱动程序不支持该 ``mbus_code``，则应返回 ``EINVAL``。
   无论 ``mbus_code`` 字段的值如何，枚举的图像格式不应依赖于视频设备或设备管道的活动配置。

.. c:type:: v4l2_fmtdesc

.. cssclass:: longtable

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_fmtdesc
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 格式在枚举中的编号，由应用程序设置
这与“pixelformat”字段无关。

* - `__u32`
      - `type`
      - 数据流类型，由应用程序设置。这里只允许以下类型：
        `V4L2_BUF_TYPE_VIDEO_CAPTURE`、
        `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`、
        `V4L2_BUF_TYPE_VIDEO_OUTPUT`、
        `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`、
        `V4L2_BUF_TYPE_VIDEO_OVERLAY`、
        `V4L2_BUF_TYPE_SDR_CAPTURE`、
        `V4L2_BUF_TYPE_SDR_OUTPUT`、
        `V4L2_BUF_TYPE_META_CAPTURE` 和
        `V4L2_BUF_TYPE_META_OUTPUT`
    参见 :c:type:`v4l2_buf_type`
* - `__u32`
      - `flags`
      - 参见 :ref:`fmtdesc-flags`
* - `__u8`
      - `description`\ [32]
      - 格式的描述，一个以NUL终止的ASCII字符串。此信息旨在供用户使用，例如：“YUV 4:2:2”
* - `__u32`
      - `pixelformat`
      - 图像格式标识符。这是一个四字符代码，由v4l2_fourcc()宏计算得出：

    * - :cspan:`2`

        .. _v4l2-fourcc:

        ``#define v4l2_fourcc(a,b,c,d)``

        ``(((__u32)(a)<<0)|((__u32)(b)<<8)|((__u32)(c)<<16)|((__u32)(d)<<24))``

        此规范在 :ref:`pixfmt` 中已经定义了多种图像格式。
.. 注意::

       这些代码与Windows世界中使用的代码不同。
* - `__u32`
      - `mbus_code`
      - 限制枚举格式的媒体总线代码，由应用程序设置。仅适用于宣传了 `V4L2_CAP_IO_MC` 能力的驱动程序 :ref:`<device-capabilities>`，否则应为0。
* - `__u32`
      - `reserved`\ [3]
      - 保留用于将来扩展。驱动程序必须将数组设为零。

.. tabularcolumns:: |p{8.4cm}|p{1.8cm}|p{7.1cm}|

.. cssclass:: longtable

.. _fmtdesc-flags:

.. flat-table:: 图像格式描述标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_FMT_FLAG_COMPRESSED`
      - 0x0001
      - 这是一个压缩格式
* - `V4L2_FMT_FLAG_EMULATED`
      - 0x0002
      - 此格式不是设备原生支持的，而是通过软件（通常是libv4l2）模拟的，在可能的情况下尽量使用原生格式以获得更好的性能
* - ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``
      - 0x0004
      - 对于这种压缩字节流格式（即编码格式），其硬件解码器能够解析连续的字节流。应用程序无需自行解析字节流以查找帧/场之间的边界。
此标志只能与``V4L2_FMT_FLAG_COMPRESSED``标志结合使用，因为这仅适用于压缩格式。此标志仅对有状态的解码器有效。
* - ``V4L2_FMT_FLAG_DYN_RESOLUTION``
      - 0x0008
      - 对于这种压缩字节流格式（即编码格式），设备支持动态分辨率切换。当检测到视频参数发生变化时，它将通过事件``V4L2_EVENT_SOURCE_CHANGE``通知用户。
此标志只能与``V4L2_FMT_FLAG_COMPRESSED``标志结合使用，因为这仅适用于压缩格式。此标志仅对有状态的编解码器有效。
* - ``V4L2_FMT_FLAG_ENC_CAP_FRAME_INTERVAL``
      - 0x0010
      - 硬件编码器支持独立设置``CAPTURE``编码帧间隔和``OUTPUT``原始帧间隔。
通过使用:ref:`VIDIOC_S_PARM <VIDIOC_G_PARM>`设置``OUTPUT``原始帧间隔也会将``CAPTURE``编码帧间隔设置为相同的值。
如果设置了此标志，则可以随后将``CAPTURE``编码帧间隔设置为不同的值。这通常用于离线编码场景中，其中``OUTPUT``原始帧间隔用于预留硬件编码器资源，而``CAPTURE``编码帧间隔是嵌入在编码视频流中的实际帧率。
此标志只能与``V4L2_FMT_FLAG_COMPRESSED``标志结合使用，因为这仅适用于压缩格式。此标志仅对有状态的编码器有效。
* - ``V4L2_FMT_FLAG_CSC_COLORSPACE``
      - 0x0020
      - 驱动程序允许应用程序尝试更改默认的颜色空间。此标志仅对采集设备相关。
应用程序可以在调用:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl时设置:ref:`V4L2_PIX_FMT_FLAG_SET_CSC <v4l2-pix-fmt-flag-set-csc>`来请求配置采集设备的颜色空间。
* - ``V4L2_FMT_FLAG_CSC_XFER_FUNC``
      - 0x0040
      - 驱动程序允许应用程序尝试更改默认的传输函数。此标志仅对采集设备有效。
      应用程序在调用带有 :ref:`V4L2_PIX_FMT_FLAG_SET_CSC <v4l2-pix-fmt-flag-set-csc>` 标志的 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 时，可以请求配置采集设备的传输函数。

* - ``V4L2_FMT_FLAG_CSC_YCBCR_ENC``
      - 0x0080
      - 驱动程序允许应用程序尝试更改默认的 Y'CbCr 编码。此标志仅对采集设备有效。
      应用程序在调用带有 :ref:`V4L2_PIX_FMT_FLAG_SET_CSC <v4l2-pix-fmt-flag-set-csc>` 标志的 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 时，可以请求配置采集设备的 Y'CbCr 编码。

* - ``V4L2_FMT_FLAG_CSC_HSV_ENC``
      - 0x0080
      - 驱动程序允许应用程序尝试更改默认的 HSV 编码。此标志仅对采集设备有效。
      应用程序在调用带有 :ref:`V4L2_PIX_FMT_FLAG_SET_CSC <v4l2-pix-fmt-flag-set-csc>` 标志的 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 时，可以请求配置采集设备的 HSV 编码。

* - ``V4L2_FMT_FLAG_CSC_QUANTIZATION``
      - 0x0100
      - 驱动程序允许应用程序尝试更改默认的量化。此标志仅对采集设备有效。
      应用程序在调用带有 :ref:`V4L2_PIX_FMT_FLAG_SET_CSC <v4l2-pix-fmt-flag-set-csc>` 标志的 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 时，可以请求配置采集设备的量化。

* - ``V4L2_FMT_FLAG_META_LINE_BASED``
      - 0x0200
      - 元数据格式基于行。在这种情况下，:c:type:`v4l2_meta_format` 的 `width`、`height` 和 `bytesperline` 字段是有效的。缓冲区由 `height` 行组成，每行包含 `width` 个数据单元，并且每两行之间的偏移量（以字节为单位）为 `bytesperline`。

返回值
======
成功时返回 0，失败时返回 -1 并设置相应的 `errno` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中进行了描述。
### EINVAL
`:c:type:' `v4l2_fmtdesc` 结构体中的 ``type`` 不被支持，或者 ``index`` 超出了范围。

如果设置了 `V4L2_CAP_IO_MC` 并且指定的 ``mbus_code`` 不被支持，则也返回此错误代码。
