SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _codec-controls:

**************************
Codec 控制参考手册
**************************

下面描述了所有属于 Codec 控制类的控制项。首先是通用控制项，然后是特定硬件的控制项。
.. note::

   这些控制适用于所有编解码器，而不仅仅是 MPEG。定义以 `V4L2_CID_MPEG/V4L2_MPEG` 开头，因为这些控制最初是为了 MPEG 编码器设计的，后来扩展到覆盖所有的编码格式。

通用 Codec 控制
======================

.. _mpeg-control-id:

Codec 控制 ID
-------------

``V4L2_CID_CODEC_CLASS (class)``
    Codec 类别描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回此控制类别的描述。此描述可以用于 GUI 中的标签页标题，例如

.. _v4l2-mpeg-stream-type:

``V4L2_CID_MPEG_STREAM_TYPE``
    (枚举类型)

枚举 `v4l2_mpeg_stream_type` -
    MPEG-1、-2 或 -4 输出流类型。这里不能假设任何内容。每个硬件 MPEG 编码器支持不同的 MPEG 流类型子集。此控制特定于复用的 MPEG 流。目前定义的流类型包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_STREAM_TYPE_MPEG2_PS``
      - MPEG-2 节目流
    * - ``V4L2_MPEG_STREAM_TYPE_MPEG2_TS``
      - MPEG-2 传输流
    * - ``V4L2_MPEG_STREAM_TYPE_MPEG1_SS``
      - MPEG-1 系统流
    * - ``V4L2_MPEG_STREAM_TYPE_MPEG2_DVD``
      - MPEG-2 DVD 兼容流
    * - ``V4L2_MPEG_STREAM_TYPE_MPEG1_VCD``
      - MPEG-1 VCD 兼容流
    * - ``V4L2_MPEG_STREAM_TYPE_MPEG2_SVCD``
      - MPEG-2 SVCD 兼容流

``V4L2_CID_MPEG_STREAM_PID_PMT (integer)``
    MPEG 传输流中的节目映射表包 ID（默认为 16）

``V4L2_CID_MPEG_STREAM_PID_AUDIO (integer)``
    MPEG 传输流中的音频包 ID（默认为 256）

``V4L2_CID_MPEG_STREAM_PID_VIDEO (integer)``
    MPEG 传输流中的视频包 ID（默认为 260）

``V4L2_CID_MPEG_STREAM_PID_PCR (integer)``
    携带 PCR 字段的 MPEG 传输流包 ID（默认为 259）

``V4L2_CID_MPEG_STREAM_PES_ID_AUDIO (integer)``
    MPEG PES 的音频 ID

``V4L2_CID_MPEG_STREAM_PES_ID_VIDEO (integer)``
    MPEG PES 的视频 ID

.. _v4l2-mpeg-stream-vbi-fmt:

``V4L2_CID_MPEG_STREAM_VBI_FMT``
    (枚举类型)

枚举 `v4l2_mpeg_stream_vbi_fmt` -
    有些卡可以在 MPEG 流中嵌入 VBI 数据（如字幕、电传）。此控制选择是否应嵌入 VBI 数据以及如果嵌入的话使用哪种方法。可能的 VBI 格式取决于驱动程序。目前定义的 VBI 格式类型包括：

.. tabularcolumns:: |p{6.6 cm}|p{10.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_STREAM_VBI_FMT_NONE``
      - MPEG 流中没有 VBI
    * - ``V4L2_MPEG_STREAM_VBI_FMT_IVTV``
      - 私有包中的 VBI，IVTV 格式（在内核源文件 `Documentation/userspace-api/media/drivers/cx2341x-uapi.rst` 中有详细说明）

.. _v4l2-mpeg-audio-sampling-freq:

``V4L2_CID_MPEG_AUDIO_SAMPLING_FREQ``
    (枚举类型)

枚举 `v4l2_mpeg_audio_sampling_freq` -
    MPEG 音频采样频率。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_SAMPLING_FREQ_44100``
      - 44.1 kHz
    * - ``V4L2_MPEG_AUDIO_SAMPLING_FREQ_48000``
      - 48 kHz
    * - ``V4L2_MPEG_AUDIO_SAMPLING_FREQ_32000``
      - 32 kHz

.. _v4l2-mpeg-audio-encoding:

``V4L2_CID_MPEG_AUDIO_ENCODING``
    (枚举类型)

枚举 `v4l2_mpeg_audio_encoding` -
    MPEG 音频编码。此控制特定于复用的 MPEG 流。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_ENCODING_LAYER_1``
      - MPEG-1/2 Layer I 编码
    * - ``V4L2_MPEG_AUDIO_ENCODING_LAYER_2``
      - MPEG-1/2 Layer II 编码
    * - ``V4L2_MPEG_AUDIO_ENCODING_LAYER_3``
      - MPEG-1/2 Layer III 编码
    * - ``V4L2_MPEG_AUDIO_ENCODING_AAC``
      - MPEG-2/4 AAC（高级音频编码）
    * - ``V4L2_MPEG_AUDIO_ENCODING_AC3``
      - AC-3 即 ATSC A/52 编码

.. _v4l2-mpeg-audio-l1-bitrate:

``V4L2_CID_MPEG_AUDIO_L1_BITRATE``
    (枚举类型)

枚举 `v4l2_mpeg_audio_l1_bitrate` -
    MPEG-1/2 Layer I 比特率。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_32K``
      - 32 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_64K``
      - 64 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_96K``
      - 96 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_128K``
      - 128 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_160K``
      - 160 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_192K``
      - 192 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_224K``
      - 224 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_256K``
      - 256 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_288K``
      - 288 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_320K``
      - 320 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_352K``
      - 352 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_384K``
      - 384 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_416K``
      - 416 kbit/s
    * - ``V4L2_MPEG_AUDIO_L1_BITRATE_448K``
      - 448 kbit/s

.. _v4l2-mpeg-audio-l2-bitrate:

``V4L2_CID_MPEG_AUDIO_L2_BITRATE``
    (枚举类型)

枚举 `v4l2_mpeg_audio_l2_bitrate` -
    MPEG-1/2 Layer II 比特率。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_32K``
      - 32 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_48K``
      - 48 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_56K``
      - 56 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_64K``
      - 64 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_80K``
      - 80 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_96K``
      - 96 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_112K``
      - 112 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_128K``
      - 128 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_160K``
      - 160 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_192K``
      - 192 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_224K``
      - 224 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_256K``
      - 256 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_320K``
      - 320 kbit/s
    * - ``V4L2_MPEG_AUDIO_L2_BITRATE_384K``
      - 384 kbit/s

.. _v4l2-mpeg-audio-l3-bitrate:

``V4L2_CID_MPEG_AUDIO_L3_BITRATE``
    (枚举类型)

枚举 `v4l2_mpeg_audio_l3_bitrate` -
    MPEG-1/2 Layer III 比特率。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_32K``
      - 32 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_40K``
      - 40 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_48K``
      - 48 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_56K``
      - 56 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_64K``
      - 64 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_80K``
      - 80 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_96K``
      - 96 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_112K``
      - 112 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_128K``
      - 128 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_160K``
      - 160 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_192K``
      - 192 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_224K``
      - 224 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_256K``
      - 256 kbit/s
    * - ``V4L2_MPEG_AUDIO_L3_BITRATE_320K``
      - 320 kbit/s

``V4L2_CID_MPEG_AUDIO_AAC_BITRATE (integer)``
    AAC 比特率（每秒比特数）

.. _v4l2-mpeg-audio-ac3-bitrate:

``V4L2_CID_MPEG_AUDIO_AC3_BITRATE``
    (枚举类型)

枚举 `v4l2_mpeg_audio_ac3_bitrate` -
    AC-3 比特率。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_32K``
      - 32 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_40K``
      - 40 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_48K``
      - 48 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_56K``
      - 56 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_64K``
      - 64 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_80K``
      - 80 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_96K``
      - 96 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_112K``
      - 112 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_128K``
      - 128 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_160K``
      - 160 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_192K``
      - 192 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_224K``
      - 224 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_256K``
      - 256 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_320K``
      - 320 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_384K``
      - 384 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_448K``
      - 448 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_512K``
      - 512 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_576K``
      - 576 kbit/s
    * - ``V4L2_MPEG_AUDIO_AC3_BITRATE_640K``
      - 640 kbit/s

.. _v4l2-mpeg-audio-mode:

``V4L2_CID_MPEG_AUDIO_MODE``
    (枚举类型)

枚举 `v4l2_mpeg_audio_mode` -
    MPEG 音频模式。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_MODE_STEREO``
      - 双声道
    * - ``V4L2_MPEG_AUDIO_MODE_JOINT_STEREO``
      - 联合双声道
    * - ``V4L2_MPEG_AUDIO_MODE_DUAL``
      - 双语
    * - ``V4L2_MPEG_AUDIO_MODE_MONO``
      - 单声道

.. _v4l2-mpeg-audio-mode-extension:

``V4L2_CID_MPEG_AUDIO_MODE_EXTENSION``
    (枚举类型)

枚举 `v4l2_mpeg_audio_mode_extension` -
    联合双声道音频模式扩展。在 Layer I 和 II 中它们指示哪些子带处于强度立体声中。所有其他子带都是以立体声编码的。Layer III 目前不支持。可能的值包括：

.. tabularcolumns:: |p{9.1cm}|p{8.4cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_MODE_EXTENSION_BOUND_4``
      - 子带 4-31 在强度立体声中
    * - ``V4L2_MPEG_AUDIO_MODE_EXTENSION_BOUND_8``
      - 子带 8-31 在强度立体声中
    * - ``V4L2_MPEG_AUDIO_MODE_EXTENSION_BOUND_12``
      - 子带 12-31 在强度立体声中
    * - ``V4L2_MPEG_AUDIO_MODE_EXTENSION_BOUND_16``
      - 子带 16-31 在强度立体声中

.. _v4l2-mpeg-audio-emphasis:

``V4L2_CID_MPEG_AUDIO_EMPHASIS``
    (枚举类型)

枚举 `v4l2_mpeg_audio_emphasis` -
    音频强调。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_EMPHASIS_NONE``
      - 无
    * - ``V4L2_MPEG_AUDIO_EMPHASIS_50_DIV_15_uS``
      - 50/15 微秒强调
    * - ``V4L2_MPEG_AUDIO_EMPHASIS_CCITT_J17``
      - CCITT J.17

.. _v4l2-mpeg-audio-crc:

``V4L2_CID_MPEG_AUDIO_CRC``
    (枚举类型)

枚举 `v4l2_mpeg_audio_crc` -
    CRC 方法。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_CRC_NONE``
      - 无
    * - ``V4L2_MPEG_AUDIO_CRC_CRC16``
      - 16 位奇偶校验

``V4L2_CID_MPEG_AUDIO_MUTE (boolean)``
    捕获时静音音频。这不是通过静音音频硬件来实现的，这仍然会产生轻微的嘶嘶声，而是在编码器本身中实现，确保了一个固定且可重复的音频比特流。0 = 不静音，1 = 静音

.. _v4l2-mpeg-audio-dec-playback:

``V4L2_CID_MPEG_AUDIO_DEC_PLAYBACK``
    (枚举类型)

枚举 `v4l2_mpeg_audio_dec_playback` -
    确定单声道音频如何播放。可能的值包括：

.. tabularcolumns:: |p{9.8cm}|p{7.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_AUTO``
      - 自动确定最佳播放模式
    * - ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_STEREO``
      - 双声道播放
    * - ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_LEFT``
      - 左声道播放
    * - ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_RIGHT``
      - 右声道播放
    * - ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_MONO``
      - 单声道播放
* ``V4L2_MPEG_AUDIO_DEC_PLAYBACK_SWAPPED_STEREO``
  - 左右声道交换的立体声播放
.. _v4l2-mpeg-audio-dec-multilingual-playback:

``V4L2_CID_MPEG_AUDIO_DEC_MULTILINGUAL_PLAYBACK``
    (枚举类型)

enum v4l2_mpeg_audio_dec_playback -
    确定多语言音频应该如何播放
.. _v4l2-mpeg-video-encoding:

``V4L2_CID_MPEG_VIDEO_ENCODING``
    (枚举类型)

enum v4l2_mpeg_video_encoding -
    MPEG视频编码方法。此控制仅适用于复用的MPEG流。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_ENCODING_MPEG_1``
      - MPEG-1 视频编码
    * - ``V4L2_MPEG_VIDEO_ENCODING_MPEG_2``
      - MPEG-2 视频编码
    * - ``V4L2_MPEG_VIDEO_ENCODING_MPEG_4_AVC``
      - MPEG-4 AVC (H.264) 视频编码


.. _v4l2-mpeg-video-aspect:

``V4L2_CID_MPEG_VIDEO_ASPECT``
    (枚举类型)

enum v4l2_mpeg_video_aspect -
    视频宽高比。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_ASPECT_1x1``
    * - ``V4L2_MPEG_VIDEO_ASPECT_4x3``
    * - ``V4L2_MPEG_VIDEO_ASPECT_16x9``
    * - ``V4L2_MPEG_VIDEO_ASPECT_221x100``


``V4L2_CID_MPEG_VIDEO_B_FRAMES (整型)``
    B帧数量（默认2）

``V4L2_CID_MPEG_VIDEO_GOP_SIZE (整型)``
    GOP大小（默认12）

``V4L2_CID_MPEG_VIDEO_GOP_CLOSURE (布尔型)``
    GOP闭合（默认1）

``V4L2_CID_MPEG_VIDEO_PULLDOWN (布尔型)``
    启用3:2下拉（默认0）

.. _v4l2-mpeg-video-bitrate-mode:

``V4L2_CID_MPEG_VIDEO_BITRATE_MODE``
    (枚举类型)

enum v4l2_mpeg_video_bitrate_mode -
    视频比特率模式。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_BITRATE_MODE_VBR``
      - 可变比特率
    * - ``V4L2_MPEG_VIDEO_BITRATE_MODE_CBR``
      - 恒定比特率
    * - ``V4L2_MPEG_VIDEO_BITRATE_MODE_CQ``
      - 恒定质量

``V4L2_CID_MPEG_VIDEO_BITRATE (整型)``
    平均视频比特率（每秒比特数）
``V4L2_CID_MPEG_VIDEO_BITRATE_PEAK (整型)``
    峰值视频比特率（每秒比特数）。必须大于或等于平均视频比特率。如果视频比特率模式设置为恒定比特率，则忽略该值。
``V4L2_CID_MPEG_VIDEO_CONSTANT_QUALITY (整型)``
    恒定质量级别控制。当``V4L2_CID_MPEG_VIDEO_BITRATE_MODE``值为``V4L2_MPEG_VIDEO_BITRATE_MODE_CQ``时适用。有效范围是1到100，其中1表示最低质量，100表示最高质量。编解码器将决定适当的量化参数和比特率以生成请求的帧质量。

``V4L2_CID_MPEG_VIDEO_FRAME_SKIP_MODE (枚举类型)``

enum v4l2_mpeg_video_frame_skip_mode -
    指示在什么条件下编解码器应该跳过帧。如果编码一帧会导致编码流超出某个数据限制，则会跳过该帧。可能的值为：

.. tabularcolumns:: |p{8.2cm}|p{9.3cm}|

.. raw:: latex

    \small

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_FRAME_SKIP_MODE_DISABLED``
      - 帧跳过模式已禁用
    * - ``V4L2_MPEG_VIDEO_FRAME_SKIP_MODE_LEVEL_LIMIT``
      - 帧跳过模式启用，并且缓冲区限制由所选级别定义，具体由标准规定
    * - ``V4L2_MPEG_VIDEO_FRAME_SKIP_MODE_BUF_LIMIT``
      - 帧跳过模式启用，并且缓冲区限制由 :ref:`VBV (MPEG1/2/4) <v4l2-mpeg-video-vbv-size>` 或 :ref:`CPB (H264) 缓冲区大小 <v4l2-mpeg-video-h264-cpb-size>` 控制

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_TEMPORAL_DECIMATION (整型)``
    对于每个捕获的帧，跳过随后的这些帧（默认0）
``V4L2_CID_MPEG_VIDEO_MUTE (布尔型)``
    在捕获时将视频静音为固定颜色。这对于测试很有用，可以生成固定的视频比特流。0 = 不静音，1 = 静音。
``V4L2_CID_MPEG_VIDEO_MUTE_YUV (整型)``
    设置视频的“静音”颜色。提供的32位整数按以下方式解释（位0是最不重要的位）：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 位0:7
      - V 色度信息
    * - 位8:15
      - U 色度信息
    * - 位16:23
      - Y 亮度信息
    * - 位24:31
      - 必须为零

.. _v4l2-mpeg-video-dec-pts:

``V4L2_CID_MPEG_VIDEO_DEC_PTS (整型64位)``
    此只读控件返回当前显示帧的33位视频呈现时间戳（Presentation Time Stamp），定义见ITU T-REC-H.222.0和ISO/IEC 13818-1。这是与 :ref:`VIDIOC_DECODER_CMD` 中使用的相同PTS。
.. _v4l2-mpeg-video-dec-frame:

``V4L2_CID_MPEG_VIDEO_DEC_FRAME (整型64位)``
    此只读控件返回当前显示（解码）帧的帧计数器。每当解码器启动时，该值会被重置为0。
``V4L2_CID_MPEG_VIDEO_DEC_CONCEAL_COLOR (整型64位)``
    此控件设置YUV色彩空间中的隐藏颜色。它描述了在参考帧丢失的情况下客户端偏好的错误隐藏颜色。解码器应使用首选颜色填充参考缓冲区，并用于未来的解码。此控件使用每通道16位。

适用于解码器

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * -
      - 8位格式
      - 10位格式
      - 12位格式
    * - Y 亮度
      - 位0:7
      - 位0:9
      - 位0:11
    * - Cb 色度
      - 位16:23
      - 位16:25
      - 位16:27
    * - Cr 色度
      - 位32:39
      - 位32:41
      - 位32:43
    * - 必须为零
      - 位48:63
      - 位48:63
      - 位48:63

``V4L2_CID_MPEG_VIDEO_DECODER_SLICE_INTERFACE (布尔型)``
    如果启用，则解码器期望每个缓冲区接收一个切片，否则解码器期望每个缓冲区接收一帧。
适用于所有编解码器的解码器
``V4L2_CID_MPEG_VIDEO_DEC_DISPLAY_DELAY_ENABLE (布尔型)``
    如果启用了显示延迟，则解码器在处理一定数量的输出缓冲区后被迫返回一个CAPTURE缓冲区（解码后的帧）。可以通过``V4L2_CID_MPEG_VIDEO_DEC_DISPLAY_DELAY``设置延迟。此功能可用于生成视频缩略图等。
适用于解码器
``V4L2_CID_MPEG_VIDEO_DEC_DISPLAY_DELAY (整数)``
    解码器的显示延迟值。解码器被强制在设定的“显示延迟”帧数后返回一个解码后的帧。如果这个数值较低，可能会导致返回的帧不在显示顺序中，此外硬件可能仍然会使用返回的缓冲区作为后续帧的参考图像。

``V4L2_CID_MPEG_VIDEO_AU_DELIMITER (布尔)``
    如果启用，则会生成AUD（访问单元分隔符）NALU。这有助于在不完全解析每个NALU的情况下找到帧的起始位置。适用于H264和HEVC编码器。

``V4L2_CID_MPEG_VIDEO_H264_VUI_SAR_ENABLE (布尔)``
    启用在视频可用性信息中写入样本宽高比。适用于H264编码器。

.. _v4l2-mpeg-video-h264-vui-sar-idc:

``V4L2_CID_MPEG_VIDEO_H264_VUI_SAR_IDC``
    （枚举）

枚举 `v4l2_mpeg_video_h264_vui_sar_idc` - H.264编码中的VUI样本宽高比指示符。值定义在标准表E-1中。适用于H264编码器。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_UNSPECIFIED``
      - 未指定
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_1x1``
      - 1x1
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_12x11``
      - 12x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_10x11``
      - 10x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_16x11``
      - 16x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_40x33``
      - 40x33
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_24x11``
      - 24x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_20x11``
      - 20x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_32x11``
      - 32x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_80x33``
      - 80x33
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_18x11``
      - 18x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_15x11``
      - 15x11
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_64x33``
      - 64x33
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_160x99``
      - 160x99
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_4x3``
      - 4x3
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_3x2``
      - 3x2
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_2x1``
      - 2x1
    * - ``V4L2_MPEG_VIDEO_H264_VUI_SAR_IDC_EXTENDED``
      - 扩展SAR

``V4L2_CID_MPEG_VIDEO_H264_VUI_EXT_SAR_WIDTH (整数)``
    H.264 VUI编码中的扩展样本宽高比宽度。适用于H264编码器。

``V4L2_CID_MPEG_VIDEO_H264_VUI_EXT_SAR_HEIGHT (整数)``
    H.264 VUI编码中的扩展样本宽高比高度。适用于H264编码器。

.. _v4l2-mpeg-video-h264-level:

``V4L2_CID_MPEG_VIDEO_H264_LEVEL``
    （枚举）

枚举 `v4l2_mpeg_video_h264_level` - H264视频基本流的级别信息。
适用于H264编码器。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_1_0``
      - Level 1.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_1B``
      - Level 1B
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_1_1``
      - Level 1.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_1_2``
      - Level 1.2
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_1_3``
      - Level 1.3
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_2_0``
      - Level 2.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_2_1``
      - Level 2.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_2_2``
      - Level 2.2
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_3_0``
      - Level 3.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_3_1``
      - Level 3.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_3_2``
      - Level 3.2
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_4_0``
      - Level 4.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_4_1``
      - Level 4.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_4_2``
      - Level 4.2
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_5_0``
      - Level 5.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_5_1``
      - Level 5.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_5_2``
      - Level 5.2
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_6_0``
      - Level 6.0
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_6_1``
      - Level 6.1
    * - ``V4L2_MPEG_VIDEO_H264_LEVEL_6_2``
      - Level 6.2

.. _v4l2-mpeg-video-mpeg2-level:

``V4L2_CID_MPEG_VIDEO_MPEG2_LEVEL``
    （枚举）

枚举 `v4l2_mpeg_video_mpeg2_level` — MPEG2基本流的级别信息。适用于MPEG2编解码器。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_MPEG2_LEVEL_LOW``
      - Low Level（LL）
    * - ``V4L2_MPEG_VIDEO_MPEG2_LEVEL_MAIN``
      - Main Level（ML）
    * - ``V4L2_MPEG_VIDEO_MPEG2_LEVEL_HIGH_1440``
      - High-1440 Level（H-14）
    * - ``V4L2_MPEG_VIDEO_MPEG2_LEVEL_HIGH``
      - High Level（HL）

.. _v4l2-mpeg-video-mpeg4-level:

``V4L2_CID_MPEG_VIDEO_MPEG4_LEVEL``
    （枚举）

枚举 `v4l2_mpeg_video_mpeg4_level` — MPEG4基本流的级别信息。适用于MPEG4编码器。可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_0``
      - Level 0
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_0B``
      - Level 0b
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_1``
      - Level 1
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_2``
      - Level 2
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_3``
      - Level 3
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_3B``
      - Level 3b
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_4``
      - Level 4
    * - ``V4L2_MPEG_VIDEO_MPEG4_LEVEL_5``
      - Level 5

.. _v4l2-mpeg-video-h264-profile:

``V4L2_CID_MPEG_VIDEO_H264_PROFILE``
    （枚举）

枚举 `v4l2_mpeg_video_h264_profile` — H264的配置文件信息。适用于H264编码器。可能的值为：

.. raw:: latex

    \small

.. tabularcolumns:: |p{10.2cm}|p{7.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_BASELINE``
      - 基线配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_CONSTRAINED_BASELINE``
      - 约束基线配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_MAIN``
      - 主配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_EXTENDED``
      - 扩展配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH``
      - 高配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_10``
      - 高10配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_422``
      - 高422配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_444_PREDICTIVE``
      - 高444预测配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_10_INTRA``
      - 高10帧内配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_422_INTRA``
      - 高422帧内配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_HIGH_444_INTRA``
      - 高444帧内配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_CAVLC_444_INTRA``
      - CAVLC 444帧内配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_SCALABLE_BASELINE``
      - 可扩展基线配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_SCALABLE_HIGH``
      - 可扩展高配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_SCALABLE_HIGH_INTRA``
      - 可扩展高帧内配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_STEREO_HIGH``
      - 立体高配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_MULTIVIEW_HIGH``
      - 多视图高配置文件
    * - ``V4L2_MPEG_VIDEO_H264_PROFILE_CONSTRAINED_HIGH``
      - 约束高配置文件

.. raw:: latex

    \normalsize

.. _v4l2-mpeg-video-mpeg2-profile:

``V4L2_CID_MPEG_VIDEO_MPEG2_PROFILE``
    （枚举）

枚举 `v4l2_mpeg_video_mpeg2_profile` — MPEG2的配置文件信息。适用于MPEG2编解码器。可能的值为：

.. raw:: latex

    \small

.. tabularcolumns:: |p{10.2cm}|p{7.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_SIMPLE``
      - 简单配置文件（SP）
    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_MAIN``
      - 主配置文件（MP）
    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_SNR_SCALABLE``
      - SNR可扩展配置文件（SNR）
    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_SPATIALLY_SCALABLE``
      - 空间可扩展配置文件（Spt）
    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_HIGH``
      - 高配置文件（HP）
    * - ``V4L2_MPEG_VIDEO_MPEG2_PROFILE_MULTIVIEW``
      - 多视图配置文件（MVP）

.. raw:: latex

    \normalsize

.. _v4l2-mpeg-video-mpeg4-profile:

``V4L2_CID_MPEG_VIDEO_MPEG4_PROFILE``
    （枚举）

枚举 `v4l2_mpeg_video_mpeg4_profile` — MPEG4的配置文件信息。适用于MPEG4编码器。可能的值为：

.. raw:: latex

    \small

.. tabularcolumns:: |p{11.8cm}|p{5.7cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_MPEG4_PROFILE_SIMPLE``
      - 简单配置文件
    * - ``V4L2_MPEG_VIDEO_MPEG4_PROFILE_ADVANCED_SIMPLE``
      - 高级简单配置文件
    * - ``V4L2_MPEG_VIDEO_MPEG4_PROFILE_CORE``
      - 核心配置文件
    * - ``V4L2_MPEG_VIDEO_MPEG4_PROFILE_SIMPLE_SCALABLE``
      - 简单可扩展配置文件
    * - ``V4L2_MPEG_VIDEO_MPEG4_PROFILE_ADVANCED_CODING_EFFICIENCY``
      - 高级编码效率配置文件

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_MAX_REF_PIC (integer)``
    编码时使用的参考图片的最大数量。适用于编码器

.. _v4l2-mpeg-video-multi-slice-mode:

``V4L2_CID_MPEG_VIDEO_MULTI_SLICE_MODE``
    （枚举）

枚举 `v4l2_mpeg_video_multi_slice_mode` — 确定编码器如何处理将帧分割成片。适用于编码器。可能的值为：

.. tabularcolumns:: |p{9.6cm}|p{7.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_MULTI_SLICE_MODE_SINGLE``
      - 每帧一个片
    * - ``V4L2_MPEG_VIDEO_MULTI_SLICE_MODE_MAX_MB``
      - 每个片设置最大宏块数的多片
    * - ``V4L2_MPEG_VIDEO_MULTI_SLICE_MODE_MAX_BYTES``
      - 每个片设置最大字节数的多片

``V4L2_CID_MPEG_VIDEO_MULTI_SLICE_MAX_MB (integer)``
    片中的最大宏块数。当 `V4L2_CID_MPEG_VIDEO_MULTI_SLICE_MODE` 设置为 `V4L2_MPEG_VIDEO_MULTI_SLICE_MODE_MAX_MB` 时使用。适用于编码器

``V4L2_CID_MPEG_VIDEO_MULTI_SLICE_MAX_BYTES (integer)``
    片的最大大小（以字节为单位）。当 `V4L2_CID_MPEG_VIDEO_MULTI_SLICE_MODE` 设置为 `V4L2_MPEG_VIDEO_MULTI_SLICE_MODE_MAX_BYTES` 时使用。适用于编码器
``V4L2_CID_MPEG_VIDEO_H264_LOOP_FILTER_MODE``
    (枚举类型)

`v4l2_mpeg_video_h264_loop_filter_mode` 枚举类型 —
    H264 编码器的环路滤波模式。可能的值如下：

.. raw:: latex

    \small

.. tabularcolumns:: |p{13.5cm}|p{4.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_LOOP_FILTER_MODE_ENABLED``
      - 环路滤波器启用
* - ``V4L2_MPEG_VIDEO_H264_LOOP_FILTER_MODE_DISABLED``
      - 环路滤波器禁用
* - ``V4L2_MPEG_VIDEO_H264_LOOP_FILTER_MODE_DISABLED_AT_SLICE_BOUNDARY``
      - 在片边界处禁用环路滤波器
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_H264_LOOP_FILTER_ALPHA (整数)``
    H264 标准中定义的环路滤波器 alpha 系数
该值对应于 `slice_alpha_c0_offset_div2` 片头字段，范围应为 -6 到 +6（包括两端）。实际的 alpha 偏移 `FilterOffsetA` 是该值的两倍。
适用于 H264 编码器。

``V4L2_CID_MPEG_VIDEO_H264_LOOP_FILTER_BETA (整数)``
    H264 标准中定义的环路滤波器 beta 系数
该值对应于 `slice_beta_offset_div2` 片头字段，范围应为 -6 到 +6（包括两端）。实际的 beta 偏移 `FilterOffsetB` 是该值的两倍。
适用于 H264 编码器。

.. _v4l2-mpeg-video-h264-entropy-mode:

``V4L2_CID_MPEG_VIDEO_H264_ENTROPY_MODE``
    (枚举类型)

`v4l2_mpeg_video_h264_entropy_mode` 枚举类型 —
    H264 的熵编码模式（CABAC/CAVALC）。适用于 H264 编码器。可能的值如下：

.. tabularcolumns:: |p{9.0cm}|p{8.5cm}|


.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_ENTROPY_MODE_CAVLC``
      - 使用 CAVLC 熵编码
``V4L2_MPEG_VIDEO_H264_ENTROPY_MODE_CABAC``
   - 使用CABAC熵编码

``V4L2_CID_MPEG_VIDEO_H264_8X8_TRANSFORM (布尔值)``
   - 启用H264的8x8变换。适用于H264编码器。

``V4L2_CID_MPEG_VIDEO_H264_CONSTRAINED_INTRA_PREDICTION (布尔值)``
   - 启用H264的约束内预测。适用于H264编码器。

``V4L2_CID_MPEG_VIDEO_H264_CHROMA_QP_INDEX_OFFSET (整数)``
   - 指定应添加到亮度量化参数以确定色度量化参数的偏移量。适用于H264编码器。

``V4L2_CID_MPEG_VIDEO_CYCLIC_INTRA_REFRESH_MB (整数)``
   - 循环内宏块刷新。这是每帧刷新的连续宏块数量。每一帧都会刷新一组连续的宏块，直到完成一个循环并从帧的顶部重新开始。将此控制设置为零意味着不刷新宏块。请注意，当“V4L2_CID_MPEG_VIDEO_INTRA_REFRESH_PERIOD”控制设置为非零值时，此控制不会生效。
   - 适用于H264、H263和MPEG4编码器。

``V4L2_CID_MPEG_VIDEO_INTRA_REFRESH_PERIOD_TYPE (枚举)``
   
   枚举 `v4l2_mpeg_video_intra_refresh_period_type` - 
   - 设置帧内刷新类型。整个帧的刷新周期由“V4L2_CID_MPEG_VIDEO_INTRA_REFRESH_PERIOD”指定。
   - 如果没有这个控制，则使用的刷新类型是未定义的，并且由驱动程序决定。
   - 适用于H264和HEVC编码器。可能的值包括：

   .. tabularcolumns:: |p{9.6cm}|p{7.9cm}|

   .. flat-table::
       :header-rows:  0
       :stub-columns: 0

       * - ``V4L2_MPEG_VIDEO_INTRA_REFRESH_PERIOD_TYPE_RANDOM``
         - 整个帧在指定周期后随机完全刷新。
       * - ``V4L2_MPEG_VIDEO_INTRA_REFRESH_PERIOD_TYPE_CYCLIC``
         - 整个帧的宏块在指定周期后按循环顺序完全刷新。
``V4L2_CID_MPEG_VIDEO_INTRA_REFRESH_PERIOD (整数)``
    宏块内刷新周期。此设置定义了刷新整个帧的周期。换句话说，这定义了整个帧进行内刷新的帧数。例如：将周期设置为1意味着整个帧将被刷新；将周期设置为2意味着在帧X中一半的宏块将被内刷新，而在帧X+1中另一半的宏块将被刷新，依此类推。将周期设置为0表示未指定周期。
请注意，如果客户端将此控制设置为非零值，则应忽略 ``V4L2_CID_MPEG_VIDEO_CYCLIC_INTRA_REFRESH_MB`` 控制。适用于H264和HEVC编码器。

``V4L2_CID_MPEG_VIDEO_FRAME_RC_ENABLE (布尔)``
    帧级速率控制启用。如果禁用此控制，则每种帧类型的量化参数是恒定的，并通过相应的控制（如 ``V4L2_CID_MPEG_VIDEO_H263_I_FRAME_QP``）设置。如果启用了帧速率控制，则量化参数将调整以满足选定的比特率。量化参数的最小值和最大值可以通过相应的控制（如 ``V4L2_CID_MPEG_VIDEO_H263_MIN_QP``）设置。适用于编码器。

``V4L2_CID_MPEG_VIDEO_MB_RC_ENABLE (布尔)``
    宏块级速率控制启用。适用于MPEG4和H264编码器。

``V4L2_CID_MPEG_VIDEO_MPEG4_QPEL (布尔)``
    MPEG4的四分之一像素运动估计。适用于MPEG4编码器。

``V4L2_CID_MPEG_VIDEO_H263_I_FRAME_QP (整数)``
    H263中的I帧的量化参数。有效范围：从1到31。

``V4L2_CID_MPEG_VIDEO_H263_MIN_QP (整数)``
    H263的最小量化参数。有效范围：从1到31。

``V4L2_CID_MPEG_VIDEO_H263_MAX_QP (整数)``
    H263的最大量化参数。有效范围：从1到31。
``V4L2_CID_MPEG_VIDEO_H263_P_FRAME_QP (整数)``
    H263 编码中 P 帧的量化参数。有效范围：从 1 到 31。

``V4L2_CID_MPEG_VIDEO_H263_B_FRAME_QP (整数)``
    H263 编码中 B 帧的量化参数。有效范围：从 1 到 31。

``V4L2_CID_MPEG_VIDEO_H264_I_FRAME_QP (整数)``
    H264 编码中 I 帧的量化参数。有效范围：从 0 到 51。

``V4L2_CID_MPEG_VIDEO_H264_MIN_QP (整数)``
    H264 编码中的最小量化参数。有效范围：从 0 到 51。

``V4L2_CID_MPEG_VIDEO_H264_MAX_QP (整数)``
    H264 编码中的最大量化参数。有效范围：从 0 到 51。

``V4L2_CID_MPEG_VIDEO_H264_P_FRAME_QP (整数)``
    H264 编码中 P 帧的量化参数。有效范围：从 0 到 51。

``V4L2_CID_MPEG_VIDEO_H264_B_FRAME_QP (整数)``
    H264 编码中 B 帧的量化参数。有效范围：从 0 到 51。

``V4L2_CID_MPEG_VIDEO_H264_I_FRAME_MIN_QP (整数)``
    H264 编码中 I 帧的最小量化参数，用于限制 I 帧的质量范围。有效范围：从 0 到 51。如果同时设置了 `V4L2_CID_MPEG_VIDEO_H264_MIN_QP`，量化参数应选择以满足两者的要求。

``V4L2_CID_MPEG_VIDEO_H264_I_FRAME_MAX_QP (整数)``
    H264 编码中 I 帧的最大量化参数，用于限制 I 帧的质量范围。有效范围：从 0 到 51。如果同时设置了 `V4L2_CID_MPEG_VIDEO_H264_MAX_QP`，量化参数应选择以满足两者的要求。

``V4L2_CID_MPEG_VIDEO_H264_P_FRAME_MIN_QP (整数)``
    H264 编码中 P 帧的最小量化参数，用于限制 P 帧的质量范围。有效范围：从 0 到 51。如果同时设置了 `V4L2_CID_MPEG_VIDEO_H264_MIN_QP`，量化参数应选择以满足两者的要求。
``V4L2_CID_MPEG_VIDEO_H264_P_FRAME_MAX_QP (整数)``
    H264 P 帧的最大量化参数，用于限制 P 帧的质量范围。有效范围：0 到 51。如果也设置了 V4L2_CID_MPEG_VIDEO_H264_MAX_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_H264_B_FRAME_MIN_QP (整数)``
    H264 B 帧的最小量化参数，用于限制 B 帧的质量范围。有效范围：0 到 51。如果也设置了 V4L2_CID_MPEG_VIDEO_H264_MIN_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_H264_B_FRAME_MAX_QP (整数)``
    H264 B 帧的最大量化参数，用于限制 B 帧的质量范围。有效范围：0 到 51。如果也设置了 V4L2_CID_MPEG_VIDEO_H264_MAX_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_MPEG4_I_FRAME_QP (整数)``
    MPEG4 I 帧的量化参数。有效范围：1 到 31。

``V4L2_CID_MPEG_VIDEO_MPEG4_MIN_QP (整数)``
    MPEG4 的最小量化参数。有效范围：1 到 31。

``V4L2_CID_MPEG_VIDEO_MPEG4_MAX_QP (整数)``
    MPEG4 的最大量化参数。有效范围：1 到 31。

``V4L2_CID_MPEG_VIDEO_MPEG4_P_FRAME_QP (整数)``
    MPEG4 P 帧的量化参数。有效范围：1 到 31。

``V4L2_CID_MPEG_VIDEO_MPEG4_B_FRAME_QP (整数)``
    MPEG4 B 帧的量化参数。有效范围：1 到 31。

.. _v4l2-mpeg-video-vbv-size:

``V4L2_CID_MPEG_VIDEO_VBV_SIZE (整数)``
    视频缓冲验证器（Video Buffer Verifier）大小，单位为千字节，用作帧跳过的限制。VBV 在标准中定义为一种验证生成的流能够成功解码的方法。标准将其描述为“与编码器输出概念上连接的一个假设解码器的一部分”。其目的是提供对编码器或编辑过程可能产生的数据速率变化的约束。
适用于MPEG1、MPEG2、MPEG4编码器

.. _v4l2-mpeg-video-vbv-delay:

``V4L2_CID_MPEG_VIDEO_VBV_DELAY (整数)``
    设置用于VBV缓冲区控制的初始延迟（毫秒）
.. _v4l2-mpeg-video-hor-search-range:

``V4L2_CID_MPEG_VIDEO_MV_H_SEARCH_RANGE (整数)``
    水平搜索范围定义了在参考图片中搜索和匹配当前宏块（MB）的最大水平搜索区域（像素）。此V4L2控制宏用于设置视频编码器中运动估计模块的水平搜索范围。
.. _v4l2-mpeg-video-vert-search-range:

``V4L2_CID_MPEG_VIDEO_MV_V_SEARCH_RANGE (整数)``
    垂直搜索范围定义了在参考图片中搜索和匹配当前宏块（MB）的最大垂直搜索区域（像素）。此V4L2控制宏用于设置视频编码器中运动估计模块的垂直搜索范围。
.. _v4l2-mpeg-video-force-key-frame:

``V4L2_CID_MPEG_VIDEO_FORCE_KEY_FRAME (按钮)``
    强制下一个排队缓冲区生成关键帧。适用于编码器。这是一个通用的、与编解码器无关的关键帧控制。
.. _v4l2-mpeg-video-h264-cpb-size:

``V4L2_CID_MPEG_VIDEO_H264_CPB_SIZE (整数)``
    编码图像缓冲区大小（千字节），用作帧跳过的限制。CPB在H264标准中被定义为验证生成的流能够成功解码的一种手段。适用于H264编码器。
``V4L2_CID_MPEG_VIDEO_H264_I_PERIOD (整数)``
    H264中开放GOP内I帧之间的周期。在开放GOP的情况下，这是两个I帧之间的周期。IDR（即时解码刷新）帧之间的周期由GOP_SIZE控制给出。IDR帧是一个I帧，在该帧之后不再引用任何先前的帧。这意味着可以从一个IDR帧重新开始流，而无需存储或解码任何先前的帧。适用于H264编码器。
.. _v4l2-mpeg-video-header-mode:

``V4L2_CID_MPEG_VIDEO_HEADER_MODE``
    （枚举）

枚举 `v4l2_mpeg_video_header_mode` —
    确定头部是否作为第一个缓冲区单独返回，还是与第一帧一起返回。适用于编码器。
可能的值包括：

.. raw:: latex

    \small

.. tabularcolumns:: |p{10.3cm}|p{7.2cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEADER_MODE_SEPARATE``
      - 流头部将单独在第一个缓冲区中返回
``V4L2_MPEG_VIDEO_HEADER_MODE_JOINED_WITH_1ST_FRAME``
- 流的头部与第一个编码帧一起返回

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_REPEAT_SEQ_HEADER (布尔值)``
- 重复视频序列头。重复这些头信息使随机访问视频流更加容易。适用于MPEG1、2和4编码器

``V4L2_CID_MPEG_VIDEO_DECODER_MPEG4_DEBLOCK_FILTER (布尔值)``
- 启用MPEG4解码器的去块后处理滤波器。适用于MPEG4解码器

``V4L2_CID_MPEG_VIDEO_MPEG4_VOP_TIME_RES (整数)``
- MPEG4的vop_time_increment_resolution值。适用于MPEG4编码器

``V4L2_CID_MPEG_VIDEO_MPEG4_VOP_TIME_INC (整数)``
- MPEG4的vop_time_increment值。适用于MPEG4编码器

``V4L2_CID_MPEG_VIDEO_H264_SEI_FRAME_PACKING (布尔值)``
- 启用编码比特流中帧打包补充增强信息的生成。帧打包SEI消息包含用于3D观看的L和R平面的排列方式。适用于H264编码器

``V4L2_CID_MPEG_VIDEO_H264_SEI_FP_CURRENT_FRAME_0 (布尔值)``
- 将当前帧设置为帧0在帧打包SEI中。适用于H264编码器

.. _v4l2-mpeg-video-h264-sei-fp-arrangement-type:

``V4L2_CID_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE``
- （枚举）

枚举 `v4l2_mpeg_video_h264_sei_fp_arrangement_type` - H264 SEI的帧打包排列类型。适用于H264编码器。可能的值包括：

.. raw:: latex

    \small

.. tabularcolumns:: |p{12cm}|p{5.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_CHEKERBOARD``
      - 像素交替来自L和R
``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_COLUMN``
    - L和R按列交织
``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_ROW``
    - L和R按行交织
``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_SIDE_BY_SIDE``
    - L在左边，R在右边
``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_TOP_BOTTOM``
    - L在上面，R在下面
``V4L2_MPEG_VIDEO_H264_SEI_FP_ARRANGEMENT_TYPE_TEMPORAL``
    - 每帧一个视图
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_H264_FMO (布尔值)``
    启用编码比特流中的灵活宏块排序。这是一种用于重组图像中宏块顺序的技术。适用于H264编码器。
.. _v4l2-mpeg-video-h264-fmo-map-type:

``V4L2_CID_MPEG_VIDEO_H264_FMO_MAP_TYPE``
   (枚举类型)

枚举 `v4l2_mpeg_video_h264_fmo_map_type` -
    当使用FMO时，映射类型将图像划分为不同的宏块扫描模式。适用于H264编码器。可能的值为：

.. raw:: latex

    \small

.. tabularcolumns:: |p{12.5cm}|p{5.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_INTERLEAVED_SLICES``
      - 切片按宏块的运行长度顺序依次交织
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_SCATTERED_SLICES``
      - 根据编解码器双方已知的数学函数散布宏块
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_FOREGROUND_WITH_LEFT_OVER``
      - 宏块按照矩形区域或感兴趣区域进行排列
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_BOX_OUT``
      - 切片组从中心向外以循环方式增长
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_RASTER_SCAN``
      - 切片组从左到右以光栅扫描模式增长
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_WIPE_SCAN``
      - 切片组从上到下以擦拭扫描模式增长
* - ``V4L2_MPEG_VIDEO_H264_FMO_MAP_TYPE_EXPLICIT``
      - 用户定义的地图类型
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_H264_FMO_SLICE_GROUP (integer)``
    FMO中的切片组数量。适用于H264编码器
.. _v4l2-mpeg-video-h264-fmo-change-direction:

``V4L2_CID_MPEG_VIDEO_H264_FMO_CHANGE_DIRECTION``
    (枚举)

enum v4l2_mpeg_video_h264_fmo_change_dir -
    指定光栅和擦拭地图中切片组变化的方向。适用于H264编码器。可能的值为：

.. tabularcolumns:: |p{9.6cm}|p{7.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_FMO_CHANGE_DIR_RIGHT``
      - 光栅扫描或向右擦拭
* - ``V4L2_MPEG_VIDEO_H264_FMO_CHANGE_DIR_LEFT``
      - 反向光栅扫描或向左擦拭
``V4L2_CID_MPEG_VIDEO_H264_FMO_CHANGE_RATE (integer)``
    指定光栅和擦拭地图中第一个切片组的大小
适用于H264编码器
``V4L2_CID_MPEG_VIDEO_H264_FMO_RUN_LENGTH (integer)``
    指定交错地图中连续宏块的数量
适用于H264编码器
``V4L2_CID_MPEG_VIDEO_H264_ASO (boolean)``
    在编码比特流中启用任意切片排序
适用于H264编码器
``V4L2_CID_MPEG_VIDEO_H264_ASO_SLICE_ORDER (整型)``
    指定ASO中的切片顺序。适用于H264编码器。
    提供的32位整数解释如下（位0为最低有效位）：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 位0:15
      - 切片ID
    * - 位16:32
      - 切片位置或顺序


``V4L2_CID_MPEG_VIDEO_H264_HIERARCHICAL_CODING (布尔型)``
    启用H264分层编码。适用于H264编码器。

.. _v4l2-mpeg-video-h264-hierarchical-coding-type:

``V4L2_CID_MPEG_VIDEO_H264_HIERARCHICAL_CODING_TYPE``
    （枚举）

枚举 `v4l2_mpeg_video_h264_hierarchical_coding_type` - 
    指定分层编码类型。适用于H264编码器。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_H264_HIERARCHICAL_CODING_B``
      - 分层B编码
    * - ``V4L2_MPEG_VIDEO_H264_HIERARCHICAL_CODING_P``
      - 分层P编码

``V4L2_CID_MPEG_VIDEO_H264_HIERARCHICAL_CODING_LAYER (整型)``
    指定分层编码层数。适用于H264编码器。

``V4L2_CID_MPEG_VIDEO_H264_HIERARCHICAL_CODING_LAYER_QP (整型)``
    指定每层的用户定义的QP值。适用于H264编码器。提供的32位整数解释如下（位0为最低有效位）：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 位0:15
      - QP值
    * - 位16:32
      - 层号

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L0_BR (整型)``
    指示H264编码器分层编码层0的比特率（bps）。

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L1_BR (整型)``
    指示H264编码器分层编码层1的比特率（bps）。

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L2_BR (整型)``
    指示H264编码器分层编码层2的比特率（bps）。

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L3_BR (整型)``
    指示H264编码器分层编码层3的比特率（bps）。

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L4_BR (整型)``
    指示H264编码器分层编码层4的比特率（bps）。
``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L5_BR (整数)``
    指示 H264 编码器中第 5 层分级编码的比特率（bps）。

``V4L2_CID_MPEG_VIDEO_H264_HIER_CODING_L6_BR (整数)``
    指示 H264 编码器中第 6 层分级编码的比特率（bps）。

``V4L2_CID_FWHT_I_FRAME_QP (整数)``
    FWHT 中 I 帧的量化参数。有效范围：从 1 到 31。

``V4L2_CID_FWHT_P_FRAME_QP (整数)``
    FWHT 中 P 帧的量化参数。有效范围：从 1 到 31。

``V4L2_CID_MPEG_VIDEO_AVERAGE_QP (整数)``
    这个只读控制返回当前编码帧的平均 QP 值。该值适用于最近弹出的捕获缓冲区（VIDIOC_DQBUF）。其有效范围取决于编码格式和参数。
- 对于 H264，有效范围是从 0 到 51。
- 对于 HEVC，对于 8 位的有效范围是从 0 到 51，对于 10 位的有效范围是从 0 到 63。
- 对于 H263 和 MPEG4，有效范围是从 1 到 31。
- 对于 VP8，有效范围是从 0 到 127。
- 对于 VP9，有效范围是从 0 到 255。
如果编解码器的 MIN_QP 和 MAX_QP 已设置，则 QP 将满足两个要求。编解码器应始终使用指定的范围，而不是硬件自定义范围。适用于编码器。

.. raw:: latex

    \normalsize


MFC 5.1 MPEG 控制
=====================

以下 MPEG 类控制处理的是与三星 S5P 系列 SoC 中存在的多格式编解码器 5.1 设备相关的 MPEG 解码和编码设置。
.. _mfc51-control-id:

MFC 5.1 控制 ID
-------------------

``V4L2_CID_MPEG_MFC51_VIDEO_DECODER_H264_DISPLAY_DELAY_ENABLE (布尔型)``
    如果启用了显示延迟，则解码器在处理一定数量的输出缓冲区后，将被迫返回一个捕获缓冲区（解码帧）。可以通过 ``V4L2_CID_MPEG_MFC51_VIDEO_DECODER_H264_DISPLAY_DELAY`` 设置延迟值。此功能可用于生成视频缩略图。适用于 H264 解码器。
.. note::

       此控制已废弃。请改用标准的 ``V4L2_CID_MPEG_VIDEO_DEC_DISPLAY_DELAY_ENABLE`` 控制。
``V4L2_CID_MPEG_MFC51_VIDEO_DECODER_H264_DISPLAY_DELAY (整型)``
    H264 解码器的显示延迟值。解码器将在设定的“显示延迟”帧数之后返回一个解码帧。如果这个数字较低，可能会导致返回的帧顺序错误，并且硬件可能仍然将返回的缓冲区作为后续帧的参考图像使用。
.. note::

       此控制已废弃。请改用标准的 ``V4L2_CID_MPEG_VIDEO_DEC_DISPLAY_DELAY`` 控制。
``V4L2_CID_MPEG_MFC51_VIDEO_H264_NUM_REF_PIC_FOR_P (整型)``
    用于编码 P 图像的参考图片数量。适用于 H264 编码器。
``V4L2_CID_MPEG_MFC51_VIDEO_PADDING (布尔值)``
    编码器中的填充启用 - 使用颜色而不是重复的边界像素。适用于编码器。
``V4L2_CID_MPEG_MFC51_VIDEO_PADDING_YUV (整数)``
    编码器中的填充颜色。适用于编码器。提供的 32 位整数按以下方式解释（位 0 = 最低位）：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 位 0:7
      - V 色度信息
    * - 位 8:15
      - U 色度信息
    * - 位 16:23
      - Y 亮度信息
    * - 位 24:31
      - 必须为零

``V4L2_CID_MPEG_MFC51_VIDEO_RC_REACTION_COEFF (整数)``
    MFC 速率控制的反应系数。适用于编码器。

.. note::

   1. 仅当帧级 RC 启用时有效
   2. 对于严格的 CBR，该字段必须很小（例如 2 ~ 10）。对于 VBR，该字段必须很大（例如 100 ~ 1000）
   3. 不建议使用大于 FRAME_RATE * (10^9 / BIT_RATE) 的数值

``V4L2_CID_MPEG_MFC51_VIDEO_H264_ADAPTIVE_RC_DARK (布尔值)``
    黑暗区域的自适应速率控制。仅当 H.264 和宏块级 RC 启用时有效（``V4L2_CID_MPEG_VIDEO_MB_RC_ENABLE``）。适用于 H264 编码器。

``V4L2_CID_MPEG_MFC51_VIDEO_H264_ADAPTIVE_RC_SMOOTH (布尔值)``
    平滑区域的自适应速率控制。仅当 H.264 和宏块级 RC 启用时有效（``V4L2_CID_MPEG_VIDEO_MB_RC_ENABLE``）。适用于 H264 编码器。

``V4L2_CID_MPEG_MFC51_VIDEO_H264_ADAPTIVE_RC_STATIC (布尔值)``
    静态区域的自适应速率控制。仅当 H.264 和宏块级 RC 启用时有效（``V4L2_CID_MPEG_VIDEO_MB_RC_ENABLE``）。适用于 H264 编码器。

``V4L2_CID_MPEG_MFC51_VIDEO_H264_ADAPTIVE_RC_ACTIVITY (布尔值)``
    活动区域的自适应速率控制。仅当 H.264 和宏块级 RC 启用时有效（``V4L2_CID_MPEG_VIDEO_MB_RC_ENABLE``）。适用于 H264 编码器。
``V4L2_CID_MPEG_MFC51_VIDEO_FRAME_SKIP_MODE``
    (枚举)

    .. note::

       此控制已废弃。请改用标准的
       ``V4L2_CID_MPEG_VIDEO_FRAME_SKIP_MODE`` 控制。
       
枚举 `v4l2_mpeg_mfc51_video_frame_skip_mode` -
    指定在何种条件下编码器应该跳过帧。如果编码一个帧会导致编码流超过所选的数据限制，则该帧将被跳过。可能的值为：

.. tabularcolumns:: |p{9.4cm}|p{8.1cm}|

.. raw:: latex

    \small

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_MFC51_VIDEO_FRAME_SKIP_MODE_DISABLED``
      - 禁用帧跳过模式
* - ``V4L2_MPEG_MFC51_VIDEO_FRAME_SKIP_MODE_LEVEL_LIMIT``
      - 启用帧跳过模式，缓冲区限制由所选级别定义，并由标准规定
* - ``V4L2_MPEG_MFC51_VIDEO_FRAME_SKIP_MODE_BUF_LIMIT``
      - 启用帧跳过模式，缓冲区限制由 VBV (MPEG1/2/4) 或 CPB (H264) 缓冲区大小控制设置

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_MFC51_VIDEO_RC_FIXED_TARGET_BIT (整数)``
    启用固定目标比特率的速率控制。如果启用此设置，则编码器的速率控制逻辑会计算一个 GOP 的平均比特率，并将其保持在或低于设定的目标比特率。否则，速率控制逻辑会计算整个流的平均比特率，并将其保持在或低于设定的比特率。在第一种情况下，整个流的平均比特率会小于设定的比特率。这是因为在较小数量的帧上进行平均计算造成的。另一方面，启用此设置可以确保流满足严格的带宽约束。适用于编码器。

.. _v4l2-mpeg-mfc51-video-force-frame-type:

``V4L2_CID_MPEG_MFC51_VIDEO_FORCE_FRAME_TYPE``
    (枚举)

枚举 `v4l2_mpeg_mfc51_video_force_frame_type` -
    强制下一个排队缓冲区的帧类型。适用于编码器。可能的值为：

.. tabularcolumns:: |p{9.9cm}|p{7.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_MFC51_FORCE_FRAME_TYPE_DISABLED``
      - 禁用特定帧类型的强制
* - ``V4L2_MPEG_MFC51_FORCE_FRAME_TYPE_I_FRAME``
      - 强制 I 帧
* - ``V4L2_MPEG_MFC51_FORCE_FRAME_TYPE_NOT_CODED``
      - 强制非编码帧

CX2341x MPEG 控制
==================

以下 MPEG 类别控制与 Conexant CX23415 和 CX23416 MPEG 编码芯片特有的 MPEG 编码设置有关。

.. _cx2341x-control-id:

CX2341x 控制 ID
-------------------

.. _v4l2-mpeg-cx2341x-video-spatial-filter-mode:

``V4L2_CID_MPEG_CX2341X_VIDEO_SPATIAL_FILTER_MODE``
    (枚举)

枚举 `v4l2_mpeg_cx2341x_video_spatial_filter_mode` -
    设置空间滤波模式（默认值为 `MANUAL`）。可能的值为：

.. tabularcolumns:: |p{11.5cm}|p{6.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_CX2341X_VIDEO_SPATIAL_FILTER_MODE_MANUAL``
      - 手动选择滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_SPATIAL_FILTER_MODE_AUTO``
      - 自动选择滤波器

``V4L2_CID_MPEG_CX2341X_VIDEO_SPATIAL_FILTER (整数 (0-15))``
    空间滤波器设置。0 = 关闭，15 = 最大。（默认值为 0。）

.. _luma-spatial-filter-type:

``V4L2_CID_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE``
    (枚举)

枚举 `v4l2_mpeg_cx2341x_video_luma_spatial_filter_type` -
    选择亮度空间滤波器使用的算法（默认值为 `1D_HOR`）。可能的值为：

.. tabularcolumns:: |p{13.1cm}|p{4.4cm}|

.. raw:: latex

    \footnotesize

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE_OFF``
      - 无滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE_1D_HOR``
      - 一维水平
    * - ``V4L2_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE_1D_VERT``
      - 一维垂直
    * - ``V4L2_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE_2D_HV_SEPARABLE``
      - 二维可分离
    * - ``V4L2_MPEG_CX2341X_VIDEO_LUMA_SPATIAL_FILTER_TYPE_2D_SYM_NON_SEPARABLE``
      - 二维对称不可分离

.. raw:: latex

    \normalsize

.. _chroma-spatial-filter-type:

``V4L2_CID_MPEG_CX2341X_VIDEO_CHROMA_SPATIAL_FILTER_TYPE``
    (枚举)

枚举 `v4l2_mpeg_cx2341x_video_chroma_spatial_filter_type` -
    选择色度空间滤波器使用的算法（默认值为 `1D_HOR`）。可能的值为：

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{11.0cm}|p{6.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_CX2341X_VIDEO_CHROMA_SPATIAL_FILTER_TYPE_OFF``
      - 无滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_CHROMA_SPATIAL_FILTER_TYPE_1D_HOR``
      - 一维水平

.. raw:: latex

    \normalsize

.. _v4l2-mpeg-cx2341x-video-temporal-filter-mode:

``V4L2_CID_MPEG_CX2341X_VIDEO_TEMPORAL_FILTER_MODE``
    (枚举)

枚举 `v4l2_mpeg_cx2341x_video_temporal_filter_mode` -
    设置时间滤波模式（默认值为 `MANUAL`）。可能的值为：

.. raw:: latex

    \footnotesize

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_CX2341X_VIDEO_TEMPORAL_FILTER_MODE_MANUAL``
      - 手动选择滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_TEMPORAL_FILTER_MODE_AUTO``
      - 自动选择滤波器

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_CX2341X_VIDEO_TEMPORAL_FILTER (整数 (0-31))``
    时间滤波器设置。0 = 关闭，31 = 最大。（默认值为全尺寸捕获时为 8，缩放捕获时为 0。）

.. _v4l2-mpeg-cx2341x-video-median-filter-type:

``V4L2_CID_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE``
    (枚举)

枚举 `v4l2_mpeg_cx2341x_video_median_filter_type` -
    中值滤波器类型（默认值为 `OFF`）。可能的值为：

.. raw:: latex

    \small

.. tabularcolumns:: |p{11.0cm}|p{6.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE_OFF``
      - 无滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE_HOR``
      - 水平滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE_VERT``
      - 垂直滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE_HOR_VERT``
      - 水平和垂直滤波器
    * - ``V4L2_MPEG_CX2341X_VIDEO_MEDIAN_FILTER_TYPE_DIAG``
      - 对角线滤波器

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_CX2341X_VIDEO_LUMA_MEDIAN_FILTER_BOTTOM (整数 (0-255))``
    亮度中值滤波器开启的阈值（默认值为 0）

``V4L2_CID_MPEG_CX2341X_VIDEO_LUMA_MEDIAN_FILTER_TOP (整数 (0-255))``
    亮度中值滤波器关闭的阈值（默认值为 255）

``V4L2_CID_MPEG_CX2341X_VIDEO_CHROMA_MEDIAN_FILTER_BOTTOM (整数 (0-255))``
    色度中值滤波器开启的阈值（默认值为 0）

``V4L2_CID_MPEG_CX2341X_VIDEO_CHROMA_MEDIAN_FILTER_TOP (整数 (0-255))``
    色度中值滤波器关闭的阈值（默认值为 255）

``V4L2_CID_MPEG_CX2341X_STREAM_INSERT_NAV_PACKETS (布尔)``
    CX2341X MPEG 编码器可以在每四个视频帧之间插入一个空的 MPEG-2 PES 包。包大小为 2048 字节，包括 `packet_start_code_prefix` 和 `stream_id` 字段。`stream_id` 为 0xBF（私有流 2）。有效载荷由 0x00 字节组成，由应用程序填充。0 = 不插入，1 = 插入包
VPX 控制参考
=====================

VPX 控制包括 VPx 视频编解码器的编码参数控制。
.. _vpx-control-id:

VPX 控制 ID
--------------

.. _v4l2-vpx-num-partitions:

``V4L2_CID_MPEG_VIDEO_VPX_NUM_PARTITIONS``
    (枚举)

`enum v4l2_vp8_num_partitions` — 在 VP8 编码器中使用的令牌分区数量。可能的值有：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_CID_MPEG_VIDEO_VPX_1_PARTITION``
      - 1 个系数分区
    * - ``V4L2_CID_MPEG_VIDEO_VPX_2_PARTITIONS``
      - 2 个系数分区
    * - ``V4L2_CID_MPEG_VIDEO_VPX_4_PARTITIONS``
      - 4 个系数分区
    * - ``V4L2_CID_MPEG_VIDEO_VPX_8_PARTITIONS``
      - 8 个系数分区

``V4L2_CID_MPEG_VIDEO_VPX_IMD_DISABLE_4X4 (布尔)``
    设置此选项可防止在帧内模式决策中使用 4x4 帧内模式。

.. _v4l2-vpx-num-ref-frames:

``V4L2_CID_MPEG_VIDEO_VPX_NUM_REF_FRAMES``
    (枚举)

`enum v4l2_vp8_num_ref_frames` — 编码 P 帧时参考图片的数量。可能的值有：

.. tabularcolumns:: |p{7.5cm}|p{7.5cm}|

.. raw:: latex

    \small

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_CID_MPEG_VIDEO_VPX_1_REF_FRAME``
      - 搜索最近编码的帧
    * - ``V4L2_CID_MPEG_VIDEO_VPX_2_REF_FRAME``
      - 将在最近编码的帧、金色帧和交替参考（altref）帧之间搜索两个帧。编码实现将决定选择哪两个帧
* - ``V4L2_CID_MPEG_VIDEO_VPX_3_REF_FRAME``
      - 将搜索最近编码的帧、金色帧和 altref 帧
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_VPX_FILTER_LEVEL (整数)``
    表示环路滤波器级别。环路滤波器级别的调整是通过相对于基线环路滤波器值的一个增量值来完成的。

``V4L2_CID_MPEG_VIDEO_VPX_FILTER_SHARPNESS (整数)``
    此参数影响环路滤波器。任何大于零的值都会削弱环路滤波器的去块效应。

``V4L2_CID_MPEG_VIDEO_VPX_GOLDEN_FRAME_REF_PERIOD (整数)``
    设置金色帧的刷新周期。周期以帧数定义。对于值为 'n' 的情况，从第一个关键帧开始，每隔第 n 帧将被用作金色帧。例如，在编码序列 0, 1, 2, 3, 4, 5, 6, 7 中，如果设置金色帧刷新周期为 4，则帧 0, 4, 8 等将被用作金色帧，因为帧 0 总是一个关键帧。

.. _v4l2-vpx-golden-frame-sel:

``V4L2_CID_MPEG_VIDEO_VPX_GOLDEN_FRAME_SEL``
    (枚举)

`enum v4l2_vp8_golden_frame_sel` — 选择用于编码的金色帧。可能的值有：

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{8.6cm}|p{8.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_CID_MPEG_VIDEO_VPX_GOLDEN_FRAME_USE_PREV``
      - 使用第 (n-2) 帧作为金色帧，当前帧索引为 'n'
* - ``V4L2_CID_MPEG_VIDEO_VPX_GOLDEN_FRAME_USE_REF_PERIOD``
      - 使用由 `V4L2_CID_MPEG_VIDEO_VPX_GOLDEN_FRAME_REF_PERIOD` 指定的前一个特定帧作为金色帧
```raw:: latex

    \normalsize
```

``V4L2_CID_MPEG_VIDEO_VPX_MIN_QP (integer)``
    VP8 的最小量化参数
``V4L2_CID_MPEG_VIDEO_VPX_MAX_QP (integer)``
    VP8 的最大量化参数
``V4L2_CID_MPEG_VIDEO_VPX_I_FRAME_QP (integer)``
    VP8 的 I 帧量化参数
``V4L2_CID_MPEG_VIDEO_VPX_P_FRAME_QP (integer)``
    VP8 的 P 帧量化参数

.. _v4l2-mpeg-video-vp8-profile:

``V4L2_CID_MPEG_VIDEO_VP8_PROFILE``
    (枚举)

枚举 `v4l2_mpeg_video_vp8_profile` -
    此控制允许选择 VP8 编码器的配置文件
这也用于枚举 VP8 编码器或解码器支持的配置文件
可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_VP8_PROFILE_0``
      - 配置文件 0
    * - ``V4L2_MPEG_VIDEO_VP8_PROFILE_1``
      - 配置文件 1
    * - ``V4L2_MPEG_VIDEO_VP8_PROFILE_2``
      - 配置文件 2
    * - ``V4L2_MPEG_VIDEO_VP8_PROFILE_3``
      - 配置文件 3

.. _v4l2-mpeg-video-vp9-profile:

``V4L2_CID_MPEG_VIDEO_VP9_PROFILE``
    (枚举)

枚举 `v4l2_mpeg_video_vp9_profile` -
    此控制允许选择 VP9 编码器的配置文件
这也用于枚举 VP9 编码器或解码器支持的配置文件
可能的值为：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_VP9_PROFILE_0``
      - 配置文件 0
    * - ``V4L2_MPEG_VIDEO_VP9_PROFILE_1``
      - 配置文件 1
    * - ``V4L2_MPEG_VIDEO_VP9_PROFILE_2``
      - 配置文件 2
    * - ``V4L2_MPEG_VIDEO_VP9_PROFILE_3``
      - 配置文件 3

.. _v4l2-mpeg-video-vp9-level:

``V4L2_CID_MPEG_VIDEO_VP9_LEVEL (enum)``
    
枚举 `v4l2_mpeg_video_vp9_level` -
    此控制允许选择 VP9 编码器的级别
这也用于枚举 VP9 编码器或解码器支持的级别
更多信息可以在以下网址找到：
    `webmproject <https://www.webmproject.org/vp9/levels/>`__。可能的值包括：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_1_0``
      - 级别 1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_1_1``
      - 级别 1.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_2_0``
      - 级别 2
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_2_1``
      - 级别 2.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_3_0``
      - 级别 3
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_3_1``
      - 级别 3.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_4_0``
      - 级别 4
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_4_1``
      - 级别 4.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_5_0``
      - 级别 5
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_5_1``
      - 级别 5.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_5_2``
      - 级别 5.2
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_6_0``
      - 级别 6
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_6_1``
      - 级别 6.1
    * - ``V4L2_MPEG_VIDEO_VP9_LEVEL_6_2``
      - 级别 6.2

高效率视频编码（HEVC/H.265）控制参考
===========================================

HEVC/H.265 控制包括 HEVC/H.265 视频编解码器的编码参数控制。

.. _hevc-control-id:

HEVC/H.265 控制 ID
----------------------

``V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP (整数)``
    HEVC 的最小量化参数
有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63
``V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP (整数)``
    HEVC 的最大量化参数
有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63
``V4L2_CID_MPEG_VIDEO_HEVC_I_FRAME_QP (整数)``
    HEVC 中 I 帧的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]
``V4L2_CID_MPEG_VIDEO_HEVC_P_FRAME_QP (整数)``
    HEVC 中 P 帧的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]
``V4L2_CID_MPEG_VIDEO_HEVC_B_FRAME_QP (整数)``
    HEVC 中 B 帧的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

``V4L2_CID_MPEG_VIDEO_HEVC_I_FRAME_MIN_QP (整数)``
    HEVC I 帧的最小量化参数，用于限制 I 帧的质量范围。有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63。
    如果也设置了 V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_HEVC_I_FRAME_MAX_QP (整数)``
    HEVC I 帧的最大量化参数，用于限制 I 帧的质量范围。有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63。
    如果也设置了 V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_HEVC_P_FRAME_MIN_QP (整数)``
    HEVC P 帧的最小量化参数，用于限制 P 帧的质量范围。有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63。
    如果也设置了 V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_HEVC_P_FRAME_MAX_QP (整数)``
    HEVC P 帧的最大量化参数，用于限制 P 帧的质量范围。有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63。
    如果也设置了 V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP，则应选择量化参数以满足两个要求。

``V4L2_CID_MPEG_VIDEO_HEVC_B_FRAME_MIN_QP (整数)``
    HEVC B 帧的最小量化参数，用于限制 B 帧的质量范围。有效范围：对于 8 位是从 0 到 51，对于 10 位是从 0 到 63。
如果设置了 `V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP`，量化参数应选择以满足以下两个要求：
``V4L2_CID_MPEG_VIDEO_HEVC_B_FRAME_MAX_QP (整数)``
    HEVC B帧的最大量化参数，用于限制B帧的质量范围。有效范围：对于8位是从0到51，对于10位是从0到63。
如果还设置了 `V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP`，量化参数应选择以满足以下两个要求：
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_QP (布尔)``
    HIERARCHICAL_QP 允许主机通过 HIERARCHICAL_QP_LAYER 指定每个时间层的量化参数值。这仅在 HIERARCHICAL_CODING_LAYER 大于1时有效。将控制值设置为1启用各层的QP值设置。
.. _v4l2-hevc-hier-coding-type:

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_TYPE``
    （枚举）

枚举 `v4l2_mpeg_video_hevc_hier_coding_type` —
    选择编码的分层类型。可能的值包括：

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{8.2cm}|p{9.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEVC_HIERARCHICAL_CODING_B``
      - 使用B帧进行分层编码
* - ``V4L2_MPEG_VIDEO_HEVC_HIERARCHICAL_CODING_P``
      - 使用P帧进行分层编码
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_LAYER (整数)``
    选择分层编码层。在正常编码（非分层编码）中，应为零。可能的值是[0, 6]。
0表示分层编码层0，1表示分层编码层1，以此类推。
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L0_QP (整数)``
    指示分层编码层0的量化参数。
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L1_QP (整数)``
    指示分层编码第 1 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L2_QP (整数)``
    指示分层编码第 2 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L3_QP (整数)``
    指示分层编码第 3 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L4_QP (整数)``
    指示分层编码第 4 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L5_QP (整数)``
    指示分层编码第 5 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L6_QP (integer)``
    指示分层编码第 6 层的量化参数
有效范围：[V4L2_CID_MPEG_VIDEO_HEVC_MIN_QP, V4L2_CID_MPEG_VIDEO_HEVC_MAX_QP]

.. _v4l2-hevc-profile:

``V4L2_CID_MPEG_VIDEO_HEVC_PROFILE``
    (枚举)

枚举 v4l2_mpeg_video_hevc_profile -
    选择 HEVC 编码器所需的配置文件
.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{9.0cm}|p{8.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEVC_PROFILE_MAIN``
      - 主配置文件
* - ``V4L2_MPEG_VIDEO_HEVC_PROFILE_MAIN_STILL_PICTURE``
      - 主静态图片配置文件
* - ``V4L2_MPEG_VIDEO_HEVC_PROFILE_MAIN_10``
      - 主 10 配置文件
.. raw:: latex

    \normalsize


.. _v4l2-hevc-level:

``V4L2_CID_MPEG_VIDEO_HEVC_LEVEL``
    (枚举)

枚举 v4l2_mpeg_video_hevc_level -
    选择 HEVC 编码器所需的级别
==================================	=========
``V4L2_MPEG_VIDEO_HEVC_LEVEL_1``	级别 1.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_2``	级别 2.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_2_1``	级别 2.1
``V4L2_MPEG_VIDEO_HEVC_LEVEL_3``	级别 3.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_3_1``	级别 3.1
``V4L2_MPEG_VIDEO_HEVC_LEVEL_4``	级别 4.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_4_1``	级别 4.1
``V4L2_MPEG_VIDEO_HEVC_LEVEL_5``	级别 5.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_5_1``	级别 5.1
``V4L2_MPEG_VIDEO_HEVC_LEVEL_5_2``	级别 5.2
``V4L2_MPEG_VIDEO_HEVC_LEVEL_6``	级别 6.0
``V4L2_MPEG_VIDEO_HEVC_LEVEL_6_1``	级别 6.1
``V4L2_MPEG_VIDEO_HEVC_LEVEL_6_2``	级别 6.2
==================================	=========

``V4L2_CID_MPEG_VIDEO_HEVC_FRAME_RATE_RESOLUTION (integer)``
    指示在一秒钟内均匀分布的子间隔数，称为刻度。这是一个 16 位无符号整数，最大值为 0xffff，最小值为 1

.. _v4l2-hevc-tier:

``V4L2_CID_MPEG_VIDEO_HEVC_TIER``
    (枚举)

枚举 v4l2_mpeg_video_hevc_tier -
    TIER_FLAG 指定 HEVC 编码图像的层级信息。层级是为了处理最大比特率不同的应用程序而设置的。将此标志设置为 0 表示选择主层级，将此标志设置为 1 表示高层级。高层级适用于需要高比特率的应用程序
==================================	==========
``V4L2_MPEG_VIDEO_HEVC_TIER_MAIN``	主层级
``V4L2_MPEG_VIDEO_HEVC_TIER_HIGH`` 高等级
==================================	==========


``V4L2_CID_MPEG_VIDEO_HEVC_MAX_PARTITION_DEPTH (整数)``
    选择 HEVC 最大编码单元深度
.. _v4l2-hevc-loop-filter-mode:

``V4L2_CID_MPEG_VIDEO_HEVC_LOOP_FILTER_MODE``
    (枚举)

枚举 `v4l2_mpeg_video_hevc_loop_filter_mode` —
    HEVC 编码器的环路滤波模式。可能的值包括：

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{12.1cm}|p{5.4cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEVC_LOOP_FILTER_MODE_DISABLED``
      - 环路滤波禁用
* - ``V4L2_MPEG_VIDEO_HEVC_LOOP_FILTER_MODE_ENABLED``
      - 环路滤波启用
* - ``V4L2_MPEG_VIDEO_HEVC_LOOP_FILTER_MODE_DISABLED_AT_SLICE_BOUNDARY``
      - 在片边界处禁用环路滤波
.. raw:: latex

    \normalsize


``V4L2_CID_MPEG_VIDEO_HEVC_LF_BETA_OFFSET_DIV2 (整数)``
    选择 HEVC 环路滤波 beta 偏移量。有效范围为 [-6, +6]
``V4L2_CID_MPEG_VIDEO_HEVC_LF_TC_OFFSET_DIV2 (整数)``
    选择 HEVC 环路滤波 tc 偏移量。有效范围为 [-6, +6]
.. _v4l2-hevc-refresh-type:

``V4L2_CID_MPEG_VIDEO_HEVC_REFRESH_TYPE``
    (枚举)

枚举 `v4l2_mpeg_video_hevc_hier_refresh_type` —
    选择 HEVC 编码器的刷新类型
主机需要在 `V4L2_CID_MPEG_VIDEO_HEVC_REFRESH_PERIOD` 中指定周期
.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{6.2cm}|p{11.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEVC_REFRESH_NONE``
      - 使用 B 帧进行分层编码
* - ``V4L2_MPEG_VIDEO_HEVC_REFRESH_CRA``
      - 使用 CRA（Clean Random Access Unit）图像编码
* - ``V4L2_MPEG_VIDEO_HEVC_REFRESH_IDR``
      - 使用 IDR（Instantaneous Decoding Refresh）图像编码
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_HEVC_REFRESH_PERIOD (整数)``
    选择 HEVC 编码器的刷新周期
    这指定了两个 CRA/IDR 图像之间的 I 图像数量
    这仅在 REFRESH_TYPE 不为 0 时有效

``V4L2_CID_MPEG_VIDEO_HEVC_LOSSLESS_CU (布尔)``
    指示 HEVC 无损编码。将其设置为 0 禁用无损编码，设置为 1 启用无损编码。

``V4L2_CID_MPEG_VIDEO_HEVC_CONST_INTRA_PRED (布尔)``
    指示 HEVC 编码器的恒定帧内预测。指定受约束的帧内预测，在这种情况下，使用残差数据和相邻帧内 LCU 的解码样本进行最大编码单元（LCU）的帧内预测。将该值设置为 1 启用恒定帧内预测，设置为 0 禁用恒定帧内预测。

``V4L2_CID_MPEG_VIDEO_HEVC_WAVEFRONT (布尔)``
    指示 HEVC 编码器的波阵面并行处理。将其设置为 0 禁用此功能，设置为 1 启用波阵面并行处理。

``V4L2_CID_MPEG_VIDEO_HEVC_GENERAL_PB (布尔)``
    将其值设置为 1 启用 HEVC 编码器的 P 帧和 B 帧组合。

``V4L2_CID_MPEG_VIDEO_HEVC_TEMPORAL_ID (布尔)``
    指示 HEVC 编码器的时间标识符，通过将其值设置为 1 来启用。
``V4L2_CID_MPEG_VIDEO_HEVC_STRONG_SMOOTHING (布尔)``
    设置为 1 时，表示在 CVS 中的帧内预测滤波过程中有条件地使用双线性插值。设置为 0 时，表示在 CVS 中不使用双线性插值。

``V4L2_CID_MPEG_VIDEO_HEVC_MAX_NUM_MERGE_MV_MINUS1 (整数)``
    表示合并候选运动向量的最大数量。
    取值范围从 0 到 4。

``V4L2_CID_MPEG_VIDEO_HEVC_TMV_PREDICTION (布尔)``
    表示启用 HEVC 编码器的时间运动矢量预测。设置为 1 启用预测，设置为 0 禁用预测。

``V4L2_CID_MPEG_VIDEO_HEVC_WITHOUT_STARTCODE (布尔)``
    指定 HEVC 是否生成一个长度字段大小的流而不是起始码模式。长度字段的大小可以通过 `V4L2_CID_MPEG_VIDEO_HEVC_SIZE_OF_LENGTH_FIELD` 控制来配置。设置该值为 0 禁用无起始码模式编码，设置为 1 启用无起始码模式编码。

.. _v4l2-hevc-size-of-length-field:

``V4L2_CID_MPEG_VIDEO_HEVC_SIZE_OF_LENGTH_FIELD``
(枚举)

枚举 `v4l2_mpeg_video_hevc_size_of_length_field` —— 指示长度字段的大小。
当启用 `WITHOUT_STARTCODE_ENABLE` 时有效。

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{5.5cm}|p{12.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_MPEG_VIDEO_HEVC_SIZE_0``
      - 生成起始码模式（正常）
    * - ``V4L2_MPEG_VIDEO_HEVC_SIZE_1``
      - 代替起始码模式生成长度字段，长度为 1
    * - ``V4L2_MPEG_VIDEO_HEVC_SIZE_2``
      - 代替起始码模式生成长度字段，长度为 2
* - ``V4L2_MPEG_VIDEO_HEVC_SIZE_4``
  - 生成长度字段的大小而不是起始码模式，长度为4
.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L0_BR (整数)``
    指示HEVC编码器的层次编码层0的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L1_BR (整数)``
    指示HEVC编码器的层次编码层1的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L2_BR (整数)``
    指示HEVC编码器的层次编码层2的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L3_BR (整数)``
    指示HEVC编码器的层次编码层3的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L4_BR (整数)``
    指示HEVC编码器的层次编码层4的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L5_BR (整数)``
    指示HEVC编码器的层次编码层5的比特率
``V4L2_CID_MPEG_VIDEO_HEVC_HIER_CODING_L6_BR (整数)``
    指示HEVC编码器的层次编码层6的比特率
``V4L2_CID_MPEG_VIDEO_REF_NUMBER_FOR_PFRAMES (整数)``
    选择HEVC编码器所需的P帧参考图像的数量
P帧可以使用1或2帧作为参考
``V4L2_CID_MPEG_VIDEO_PREPEND_SPSPPS_TO_IDR (整数)``
    表示是否在每个IDR帧前生成SPS和PPS。将其设置为0会禁用在每个IDR帧前生成SPS和PPS。将其设置为1会启用在每个IDR帧前生成SPS和PPS。
