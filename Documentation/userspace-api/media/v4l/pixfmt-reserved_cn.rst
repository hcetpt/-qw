.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _pixfmt-reserved:

***************************
保留的格式标识符
***************************

这些格式不由本规范定义，仅列出以供参考并避免命名冲突。如果您希望注册自己的格式，请发送电子邮件至 linux-media 邮件列表 `https://linuxtv.org/lists.php <https://linuxtv.org/lists.php>`__，以便将其包含在 ``videodev2.h`` 文件中。如果您希望与其它开发者共享您的格式，请添加一个指向您的文档的链接，并将副本发送到 linux-media 邮件列表，以便在此部分中包含。如果您认为您的格式应列在标准格式部分，请在 linux-media 邮件列表上提出建议。

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. raw:: latex

    \small

.. _reserved-formats:

.. flat-table:: 保留的图像格式
    :header-rows:  1
    :stub-columns: 0
    :widths:       3 1 4

    * - 标识符
      - 代码
      - 详细信息
    * .. _V4L2-PIX-FMT-DV:

      - ``V4L2_PIX_FMT_DV``
      - 'dvsd'
      - 未知
    * .. _V4L2-PIX-FMT-ET61X251:

      - ``V4L2_PIX_FMT_ET61X251``
      - 'E625'
      - ET61X251 驱动程序的压缩格式
    * .. _V4L2-PIX-FMT-HI240:

      - ``V4L2_PIX_FMT_HI240``
      - 'HI24'
      - BTTV 驱动程序使用的 8 位 RGB 格式
    * .. _V4L2-PIX-FMT-CPIA1:

      - ``V4L2_PIX_FMT_CPIA1``
      - 'CPIA'
      - gspca cpia1 驱动程序使用的 YUV 格式
    * .. _V4L2-PIX-FMT-JPGL:

      - ``V4L2_PIX_FMT_JPGL``
      - 'JPGL'
      - Divio 网络摄像头 NW 80x 使用的 JPEG-Light 格式（Pegasus 无损 JPEG）
    * .. _V4L2-PIX-FMT-SPCA501:

      - ``V4L2_PIX_FMT_SPCA501``
      - 'S501'
      - gspca 驱动程序使用的每行 YUYV 格式
    * .. _V4L2-PIX-FMT-SPCA505:

      - ``V4L2_PIX_FMT_SPCA505``
      - 'S505'
      - gspca 驱动程序使用的每行 YYUV 格式
    * .. _V4L2-PIX-FMT-SPCA508:

      - ``V4L2_PIX_FMT_SPCA508``
      - 'S508'
      - gspca 驱动程序使用的每行 YUVY 格式
    * .. _V4L2-PIX-FMT-SPCA561:

      - ``V4L2_PIX_FMT_SPCA561``
      - 'S561'
      - gspca 驱动程序使用的压缩 GBRG 拜耳格式
    * .. _V4L2-PIX-FMT-PAC207:

      - ``V4L2_PIX_FMT_PAC207``
      - 'P207'
      - gspca 驱动程序使用的压缩 BGGR 拜耳格式
* .. _V4L2-PIX-FMT-MR97310A:

      - ``V4L2_PIX_FMT_MR97310A``
      - 'M310'
      - gspca 驱动程序使用的压缩 BGGR 拜耳格式

* .. _V4L2-PIX-FMT-JL2005BCD:

      - ``V4L2_PIX_FMT_JL2005BCD``
      - 'JL20'
      - gspca 驱动程序使用的 JPEG 压缩 RGGB 拜耳格式

* .. _V4L2-PIX-FMT-OV511:

      - ``V4L2_PIX_FMT_OV511``
      - 'O511'
      - gspca 驱动程序使用的 OV511 JPEG 格式

* .. _V4L2-PIX-FMT-OV518:

      - ``V4L2_PIX_FMT_OV518``
      - 'O518'
      - gspca 驱动程序使用的 OV518 JPEG 格式

* .. _V4L2-PIX-FMT-PJPG:

      - ``V4L2_PIX_FMT_PJPG``
      - 'PJPG'
      - gspca 驱动程序使用的 Pixart 73xx JPEG 格式

* .. _V4L2-PIX-FMT-SE401:

      - ``V4L2_PIX_FMT_SE401``
      - 'S401'
      - gspca se401 驱动程序使用的压缩 RGB 格式

* .. _V4L2-PIX-FMT-SQ905C:

      - ``V4L2_PIX_FMT_SQ905C``
      - '905C'
      - gspca 驱动程序使用的压缩 RGGB 拜耳格式

* .. _V4L2-PIX-FMT-MJPEG:

      - ``V4L2_PIX_FMT_MJPEG``
      - 'MJPG'
      - Zoran 驱动程序使用的压缩格式

* .. _V4L2-PIX-FMT-PWC1:

      - ``V4L2_PIX_FMT_PWC1``
      - 'PWC1'
      - PWC 驱动程序的压缩格式

* .. _V4L2-PIX-FMT-PWC2:

      - ``V4L2_PIX_FMT_PWC2``
      - 'PWC2'
      - PWC 驱动程序的压缩格式

* .. _V4L2-PIX-FMT-SN9C10X:

      - ``V4L2_PIX_FMT_SN9C10X``
      - 'S910'
      - SN9C102 驱动程序的压缩格式

* .. _V4L2-PIX-FMT-SN9C20X-I420:

      - ``V4L2_PIX_FMT_SN9C20X_I420``
      - 'S920'
      - gspca sn9c20x 驱动程序的 YUV 4:2:0 格式
* .. _V4L2-PIX-FMT-SN9C2028:

      - ``V4L2_PIX_FMT_SN9C2028``
      - 'SONX'
      - gspca sn9c2028 驱动程序的压缩 GBRG 拜耳格式
* .. _V4L2-PIX-FMT-STV0680:

      - ``V4L2_PIX_FMT_STV0680``
      - 'S680'
      - gspca stv0680 驱动程序的拜耳格式
* .. _V4L2-PIX-FMT-WNVA:

      - ``V4L2_PIX_FMT_WNVA``
      - 'WNVA'
      - 由 Winnov Videum 驱动程序使用，
      `http://www.thedirks.org/winnov/ <http://www.thedirks.org/winnov/>`__
* .. _V4L2-PIX-FMT-TM6000:

      - ``V4L2_PIX_FMT_TM6000``
      - 'TM60'
      - 由 Trident tm6000 使用
* .. _V4L2-PIX-FMT-CIT-YYVYUY:

      - ``V4L2_PIX_FMT_CIT_YYVYUY``
      - 'CITV'
      - 由 Xirlink CIT 使用，常见于 IBM 网络摄像头
每行先是一行 Y，然后是一行 VYUY
* .. _V4L2-PIX-FMT-KONICA420:

      - ``V4L2_PIX_FMT_KONICA420``
      - 'KONI'
      - 由 Konica 网络摄像头使用
每个块包含 256 像素的 YUV420 平面格式
* .. _V4L2-PIX-FMT-YYUV:

      - ``V4L2_PIX_FMT_YYUV``
      - 'YYUV'
      - 未知
* .. _V4L2-PIX-FMT-Y4:

      - ``V4L2_PIX_FMT_Y4``
      - 'Y04 '
      - 旧的 4 位灰度格式。每个字节仅使用最高 4 位，其余位设置为 0
* .. _V4L2-PIX-FMT-Y6:

      - ``V4L2_PIX_FMT_Y6``
      - 'Y06 '
      - 旧的 6 位灰度格式。每个字节仅使用最高 6 位，其余位设置为 0
* .. _V4L2-PIX-FMT-S5C-UYVY-JPG:

      - ``V4L2_PIX_FMT_S5C_UYVY_JPG``
      - 'S5CI'
      - 用于三星 S5C73MX 摄像头的双平面格式。第一平面包含交错的 JPEG 和 UYVY 图像数据，后跟以偏移量数组形式的元数据。实际的指针数组紧跟在交错的 JPEG/UYVY 数据之后，该数组中的条目数等于 UYVY 图像的高度。每个条目是一个 4 字节的大端序无符号整数，并且是到 UYVY 图像单个像素行的偏移量。第一平面可以以 JPEG 或 UYVY 数据块开始。单个 UYVY 块的大小等于 UYVY 图像的宽度乘以 2。JPEG 块的大小取决于图像，并且可能因每行而异。
第二平面从偏移量 4084 字节处开始，包含指向第一平面中指针数组的 4 字节偏移量。此偏移量后跟一个表示指针数组大小的 4 字节值。
第二平面中的所有数字也采用大端字节序。
第二平面中剩余的数据是未定义的。第二平面上的信息可以轻松找到指针数组的位置，这在每一帧中可能不同。对于给定的UYVY图像高度，指针数组的大小是固定的。
为了提取UYVY和JPEG帧，应用程序可以首先将数据指针设置为第一平面的起始位置，然后加上指针表第一个条目的偏移量。这样的指针指示了UYVY图像行的开始位置。整个UYVY行可以复制到一个单独的缓冲区。这些步骤应该针对每一行重复进行，即指针数组中的条目数量。UYVY行之间的任何内容都是JPEG数据，并应连接起来形成JPEG流。

* .. _V4L2-PIX-FMT-MT21C:

      - ``V4L2_PIX_FMT_MT21C``
      - 'MT21'
      - 由Mediatek MT8173、MT8192、MT8195等使用的压缩双平面YVU420格式。该压缩是无损的。此格式与``V4L2_PIX_FMT_MM21``在对齐和分块方面有相似之处。
这是一个不透明的中间格式，MDP硬件必须用于将``V4L2_PIX_FMT_MT21C``转换为``V4L2_PIX_FMT_NV12M``、``V4L2_PIX_FMT_YUV420M``或``V4L2_PIX_FMT_YVU420``。
* .. _V4L2-PIX-FMT-QC08C:

      - ``V4L2_PIX_FMT_QC08C``
      - 'QC08C'
      - 由Qualcomm平台使用的压缩宏块8位YUV420格式。
这是一个不透明的中间格式。所使用的压缩是无损的，并被各种多媒体硬件模块（如GPU、显示控制器、ISP和视频加速器）使用。
它包含四个平面用于逐行视频，八个平面用于隔行视频。
* .. _V4L2-PIX-FMT-QC10C:

      - ``V4L2_PIX_FMT_QC10C``
      - 'QC10C'
      - 由Qualcomm平台使用的压缩宏块10位YUV420格式。
这是一个不透明的中间格式。所使用的压缩是无损的，并被各种多媒体硬件模块（如GPU、显示控制器、ISP和视频加速器）使用。
它包含四个平面，用于逐行视频。
* .. _V4L2-PIX-FMT-AJPG:

      - ``V4L2_PIX_FMT_AJPG``
      - 'AJPG'
      - 由 aspeed-video 驱动在 Aspeed 平台上使用的 ASPEED JPEG 格式，通常适用于远程 KVM
每次帧压缩时，我将比较新帧与前一帧来决定哪些宏块的数据发生了变化，并且仅压缩那些发生变化的宏块
实现基于 AST2600 A3 数据手册第 0.9 版，该手册并未公开。或者您可以参考 SDK 用户指南中的“视频流数据格式 – ASPEED 模式压缩”部分，该文档可在
`github <https://github.com/AspeedTech-BMC/openbmc/releases/>`__ 上获取
解码器的实现可以在以下位置找到：
`aspeed_codec <https://github.com/AspeedTech-BMC/aspeed_codec/>`__
    * .. _V4L2-PIX-FMT-MT2110T:

      - ``V4L2_PIX_FMT_MT2110T``
      - 'MT2110T'
      - 此格式为双平面 10 位瓷砖模式，在对齐和分块方面与 ``V4L2_PIX_FMT_MM21`` 相似。用于 VP9、AV1 和 HEVC
* .. _V4L2-PIX-FMT-MT2110R:

      - ``V4L2_PIX_FMT_MT2110R``
      - 'MT2110R'
      - 此格式为双平面 10 位光栅模式，在对齐和分块方面与 ``V4L2_PIX_FMT_MM21`` 相似。用于 AVC
* .. _V4L2-PIX-FMT-HEXTILE:

      - ``V4L2_PIX_FMT_HEXTILE``
      - 'HXTL'
      - 由 Nuvoton NPCM 视频驱动程序使用的压缩格式。此格式定义在远程帧缓冲协议（RFC 6143 第 7.7.4 节 Hextile 编码）中
.. raw:: latex

    \normalsize
