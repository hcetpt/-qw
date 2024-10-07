.. SPDX-Identifier: GFDL-1.1-no-invariants-or-later

******************
压缩格式
******************

.. _compressed-formats:

.. raw:: latex

    \small

.. tabularcolumns:: |p{5.8cm}|p{1.2cm}|p{10.3cm}|

.. cssclass:: longtable

.. flat-table:: 压缩图像格式
    :header-rows:  1
    :stub-columns: 0
    :widths:       3 1 4

    * - 标识符
      - 代码
      - 详细信息
    * .. _V4L2-PIX-FMT-JPEG:

      - ``V4L2_PIX_FMT_JPEG``
      - 'JPEG'
      - 待定。另见 :ref:`VIDIOC_G_JPEGCOMP <VIDIOC_G_JPEGCOMP>`，:ref:`VIDIOC_S_JPEGCOMP <VIDIOC_G_JPEGCOMP>`
    * .. _V4L2-PIX-FMT-MPEG:

      - ``V4L2_PIX_FMT_MPEG``
      - 'MPEG'
      - MPEG 复用流。实际格式由扩展控制 ``V4L2_CID_MPEG_STREAM_TYPE`` 确定，参见 :ref:`mpeg-control-id`
    * .. _V4L2-PIX-FMT-H264:

      - ``V4L2_PIX_FMT_H264``
      - 'H264'
      - H264 接入单元
解码器期望每个缓冲区有一个接入单元
编码器生成每个缓冲区一个接入单元
如果 :ref:`VIDIOC_ENUM_FMT` 报告了 ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``
那么解码器没有要求，因为它可以从原始字节流中解析所有信息
    * .. _V4L2-PIX-FMT-H264-NO-SC:

      - ``V4L2_PIX_FMT_H264_NO_SC``
      - 'AVC1'
      - 没有起始码的 H264 视频基本流
    * .. _V4L2-PIX-FMT-H264-MVC:

      - ``V4L2_PIX_FMT_H264_MVC``
      - 'M264'
      - H264 MVC 视频基本流
    * .. _V4L2-PIX-FMT-H264-SLICE:

      - ``V4L2_PIX_FMT_H264_SLICE``
      - 'S264'
      - H264 解析的片数据，包括片头，可以包含或不包含起始码，从 H264 比特流中提取
此格式适用于实现了 H264 管道的无状态视频解码器 :ref:`stateless_decoder`
此像素格式有两个修饰符，必须至少设置一次，通过以下控制项：
- ``V4L2_CID_STATELESS_H264_DECODE_MODE``
- ``V4L2_CID_STATELESS_H264_START_CODE``

此外，解码帧所需的元数据必须通过以下控制项传递：
- ``V4L2_CID_STATELESS_H264_SPS``
- ``V4L2_CID_STATELESS_H264_PPS``
- ``V4L2_CID_STATELESS_H264_SCALING_MATRIX``
- ``V4L2_CID_STATELESS_H264_SLICE_PARAMS``
- ``V4L2_CID_STATELESS_H264_DECODE_PARAMS``

具体参见：:ref:`相关Codec控制ID <v4l2-codec-stateless-h264>`

使用此像素格式时，必须提供一个输出缓冲区和一个捕获缓冲区。输出缓冲区必须包含解码完整帧所需的宏块数量，以匹配捕获缓冲区。

此格式的语法在 :ref:`h264` 的第 7.3.2.8 节 “无分区的片层RBSP语法” 及后续章节中有详细说明。

* .. _V4L2-PIX-FMT-H263:

      - ``V4L2_PIX_FMT_H263``
      - 'H263'
      - H263视频基本流
* .. _V4L2-PIX-FMT-SPK:

      - ``V4L2_PIX_FMT_SPK``
      - 'SPK0'
      - Sorenson Spark 是一种用于Flash视频和Adobe Flash文件中的H.263实现
* .. _V4L2-PIX-FMT-MPEG1:

      - ``V4L2_PIX_FMT_MPEG1``
      - 'MPG1'
      - MPEG1图像。每个缓冲区以图片头开始，接着是其他所需头部，并以图片数据结束

如果 :ref:`VIDIOC_ENUM_FMT` 报告了 ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``，则解码器没有任何要求，因为它可以从原始字节流中解析所有信息。
* .. _V4L2-PIX-FMT-MPEG2:

      - ``V4L2_PIX_FMT_MPEG2``
      - 'MPG2'
      - MPEG2图像。每个缓冲区以图片头开始，接着是其他所需头部，并以图片数据结束

如果 :ref:`VIDIOC_ENUM_FMT` 报告了 ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``，则解码器没有任何要求，因为它可以从原始字节流中解析所有信息。
* .. _V4L2-PIX-FMT-MPEG2-SLICE:

      - ``V4L2_PIX_FMT_MPEG2_SLICE``
      - 'MG2S'
      - 从MPEG-2比特流中提取的MPEG-2分片数据
此格式适用于实现了MPEG-2流水线的无状态视频解码器，具体参见 :ref:`stateless_decoder`。
要解码的帧所需的元数据必须通过 ``V4L2_CID_STATELESS_MPEG2_SEQUENCE`` 和 ``V4L2_CID_STATELESS_MPEG2_PICTURE`` 控制传递。
量化矩阵可选地通过 ``V4L2_CID_STATELESS_MPEG2_QUANTISATION`` 控制指定。
详见 :ref:`相关的Codec控制ID <v4l2-codec-stateless-mpeg2>`。
使用此像素格式时，必须提供一个输出缓冲区和一个捕获缓冲区。输出缓冲区必须包含足够数量的宏块以解码完整的对应帧到匹配的捕获缓冲区。

* .. _V4L2-PIX-FMT-MPEG4:

      - ``V4L2_PIX_FMT_MPEG4``
      - 'MPG4'
      - MPEG4视频基本流
* .. _V4L2-PIX-FMT-XVID:

      - ``V4L2_PIX_FMT_XVID``
      - 'XVID'
      - Xvid视频基本流
* .. _V4L2-PIX-FMT-VC1-ANNEX-G:

      - ``V4L2_PIX_FMT_VC1_ANNEX_G``
      - 'VC1G'
      - 符合SMPTE 421M附录G的VC1流
* .. _V4L2-PIX-FMT-VC1-ANNEX-L:

      - ``V4L2_PIX_FMT_VC1_ANNEX_L``
      - 'VC1L'
      - 符合SMPTE 421M附录L的VC1流
* .. _V4L2-PIX-FMT-VP8:

      - ``V4L2_PIX_FMT_VP8``
      - 'VP80'
      - VP8压缩视频帧。编码器每缓冲区生成一个压缩帧，解码器要求每个缓冲区有一个压缩帧
* .. _V4L2-PIX-FMT-VP8-FRAME:

      - ``V4L2_PIX_FMT_VP8_FRAME``
      - 'VP8F'
      - 从容器中提取的包含帧头的VP8解析帧
此格式适用于实现VP8流水线的状态无关视频解码器，具体参见 :ref:`stateless_decoder`
需要通过 ``V4L2_CID_STATELESS_VP8_FRAME`` 控制传递与待解码帧相关的元数据
参见 :ref:`相关Codec控制ID <v4l2-codec-stateless-vp8>`
必须提供一个输出缓冲区和一个捕获缓冲区以使用此像素格式。输出缓冲区必须包含足够的宏块以解码一个完整的对应帧到匹配的捕获缓冲区

* .. _V4L2-PIX-FMT-VP9:

      - ``V4L2_PIX_FMT_VP9``
      - 'VP90'
      - VP9压缩视频帧。编码器为每个缓冲区生成一个压缩帧，解码器也需要一个压缩帧对应一个缓冲区

* .. _V4L2-PIX-FMT-VP9-FRAME:

      - ``V4L2_PIX_FMT_VP9_FRAME``
      - 'VP9F'
      - 从容器中提取的包含帧头的VP9解析帧
此格式适用于实现VP9流水线的状态无关视频解码器，具体参见 :ref:`stateless_decoder`
需要通过 ``V4L2_CID_STATELESS_VP9_FRAME`` 和 ``V4L2_CID_STATELESS_VP9_COMPRESSED_HDR`` 控制传递与待解码帧相关的元数据
参见 :ref:`相关Codec控制ID <v4l2-codec-stateless-vp9>`
必须提供一个输出缓冲区和一个捕获缓冲区以供与该像素格式一起使用。输出缓冲区必须包含适当数量的宏块，以便将完整的对应帧解码到匹配的捕获缓冲区中。

* .. _V4L2-PIX-FMT-HEVC:

      - ``V4L2_PIX_FMT_HEVC``
      - 'HEVC'
      - HEVC/H.265 接入单元（Access Unit）
解码器期望每个缓冲区有一个接入单元。
编码器生成每个缓冲区一个接入单元。
如果 :ref:`VIDIOC_ENUM_FMT` 报告了 ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``，
    那么解码器没有要求，因为它可以从原始字节流中解析所有信息。

* .. _V4L2-PIX-FMT-HEVC-SLICE:

      - ``V4L2_PIX_FMT_HEVC_SLICE``
      - 'S265'
      - 从 HEVC 比特流中提取的 HEVC 解析后的片数据（slice data）
此格式适用于实现了 HEVC 管道的状态无关视频解码器（使用 :ref:`mem2mem` 和 :ref:`media-request-api`）
此像素格式有两个修饰符，至少需要通过 ``V4L2_CID_MPEG_VIDEO_HEVC_DECODE_MODE`` 和 ``V4L2_CID_MPEG_VIDEO_HEVC_START_CODE`` 控制设置一次。
与要解码的帧相关的元数据必须通过以下控制传递：
        ``V4L2_CID_MPEG_VIDEO_HEVC_SPS``,
        ``V4L2_CID_MPEG_VIDEO_HEVC_PPS``, 和
        ``V4L2_CID_MPEG_VIDEO_HEVC_SLICE_PARAMS``
请参阅 :ref:`相关的编解码器控制 ID <v4l2-codec-stateless-hevc>`。
与该像素格式相关的缓冲区必须包含适当数量的宏块以解码完整的对应帧。

* .. _V4L2-PIX-FMT-FWHT:

      - ``V4L2_PIX_FMT_FWHT``
      - 'FWHT'
      - 使用基于快速沃尔什-哈达玛变换（Fast Walsh Hadamard Transform）的编解码器的视频基本流。此编解码器由 vicodec（'虚拟编解码器'）驱动实现。更多细节请参阅 codec-fwht.h 头文件。
:ref:`VIDIOC_ENUM_FMT` 报告 ``V4L2_FMT_FLAG_CONTINUOUS_BYTESTREAM``，因为解码器可以从原始字节流中解析所有信息。

* .. _V4L2-PIX-FMT-FWHT-STATELESS:

      - ``V4L2_PIX_FMT_FWHT_STATELESS``
      - 'SFWH'
      - 与 V4L2_PIX_FMT_FWHT 相同的格式，但需要无状态编解码器实现。
解码所需帧的元数据需要通过 ``V4L2_CID_STATELESS_FWHT_PARAMS`` 控制传递。
详见 :ref:`相关的 Codec Control ID <codec-stateless-fwht>`。

* .. _V4L2-PIX-FMT-RV30:

      - ``V4L2_PIX_FMT_RV30``
      - 'RV30'
      - RealVideo（或称为 Real Video）是由 RealNetworks 开发的一系列专有视频压缩格式——具体格式随版本变化。
RealVideo 编码器由四个字符的代码标识。
RV30 对应于 RealVideo 8，怀疑其主要基于早期的 H.264 草案。

* .. _V4L2-PIX-FMT-RV40:

      - ``V4L2_PIX_FMT_RV40``
      - 'RV40'
      - RV40 代表 RealVideo 9 和 RealVideo 10。
RealVideo 9 怀疑基于 H.264。
RealVideo 10，也称为RV9 EHQ，这指的是RV9格式的一个改进的编码器，该编码器与RV9播放器完全向后兼容——格式和解码器没有变化，只有编码器进行了改进。因此，它使用相同的FourCC。

* .. _V4L2-PIX-FMT-AV1-FRAME:

      - ``V4L2_PIX_FMT_AV1_FRAME``
      - 'AV1F'
      - 包含帧头的AV1解析帧，从容器中提取
此格式适用于实现AV1流水线的状态无关视频解码器，并且使用了:ref:`stateless_decoder`。需要通过 ``V4L2_CID_STATELESS_AV1_SEQUENCE``、``V4L2_CID_STATELESS_AV1_FRAME`` 和 ``V4L2_CID_STATELESS_AV1_TILE_GROUP_ENTRY`` 控制来传递与待解码帧相关的元数据。
请参阅:ref:`相关的Codec控制ID <v4l2-codec-stateless-av1>`。

必须提供一个输出缓冲区和一个捕获缓冲区以使用此像素格式。输出缓冲区必须包含适当数量的宏块，以便对整个相应的帧进行解码并与匹配的捕获缓冲区对应。

.. raw:: latex

    \normalsize
