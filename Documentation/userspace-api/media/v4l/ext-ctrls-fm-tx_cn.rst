SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _fm-tx-controls:

********************************
FM 发射器控制参考
********************************

FM 发射器（FM_TX）类包括了具备 FM 发射功能的设备常用特性的控制。目前，此类包含音频压缩、导频音生成、音频偏移限制、RDS 传输和调谐功率等功能。
.. _fm-tx-control-id:

FM_TX 控制 ID
==============

``V4L2_CID_FM_TX_CLASS (class)``
    FM_TX 类描述符。对这个控制进行 :ref:`VIDIOC_QUERYCTRL` 调用将返回此控制类的描述。

``V4L2_CID_RDS_TX_DEVIATION (integer)``
    配置 RDS 信号频率偏移水平（单位：赫兹）。范围和步长由驱动程序决定。

``V4L2_CID_RDS_TX_PI (integer)``
    设置用于传输的 RDS 节目识别字段。

``V4L2_CID_RDS_TX_PTY (integer)``
    设置用于传输的 RDS 节目类型字段。这可以编码多达 31 种预定义的节目类型。

``V4L2_CID_RDS_TX_PS_NAME (string)``
    设置用于传输的节目服务名称（PS_NAME）。其目的是在接收器上静态显示。这是听众识别和选择节目服务的主要辅助工具。在 :ref:`iec62106` 的附录 E 中，RDS 规范详细描述了节目服务名称字符串的正确字符编码。根据 RDS 规范，PS 通常是一个八字符的文本。然而，也可以找到能够滚动显示 8 x N 字符串的接收器。因此，这个控制必须以 8 个字符为步长进行配置。结果是它必须始终包含长度为 8 的倍数的字符串。

``V4L2_CID_RDS_TX_RADIO_TEXT (string)``
    设置用于传输的广播文本信息。这是一个正在播放内容的文字描述。当广播者希望传输更长的 PS 名称、与节目相关的信息或其他任何文本时，可以使用 RDS 广播文本。在这种情况下，应与 ``V4L2_CID_RDS_TX_PS_NAME`` 一起使用。广播文本字符串的编码也在 :ref:`iec62106` 的附录 E 中进行了详述。广播文本字符串的长度取决于所使用的 RDS 块，可能是 32（2A 块）或 64（2B 块）。然而，也可以找到能够滚动显示 32 x N 或 64 x N 字符串的接收器。因此，这个控制必须以 32 或 64 个字符为步长进行配置。结果是它必须始终包含长度为 32 或 64 的倍数的字符串。

``V4L2_CID_RDS_TX_MONO_STEREO (boolean)``
    设置解码器识别码中的单声道/立体声位。如果设置，则音频是以立体声录制的。
``V4L2_CID_RDS_TX_ARTIFICIAL_HEAD (布尔)``
    设置解码器识别码中的“人工头”位。如果设置，则表示音频是使用人工头录制的。
``V4L2_CID_RDS_TX_COMPRESSED (布尔)``
    设置解码器识别码中的“压缩”位。如果设置，则表示音频是经过压缩的。
``V4L2_CID_RDS_TX_DYNAMIC_PTY (布尔)``
    设置解码器识别码中的“动态PTY”位。如果设置，则表示PTY码会动态切换。
``V4L2_CID_RDS_TX_TRAFFIC_ANNOUNCEMENT (布尔)``
    如果设置，则表示正在进行交通公告。
``V4L2_CID_RDS_TX_TRAFFIC_PROGRAM (布尔)``
    如果设置，则表示当前调谐的节目包含交通公告。
``V4L2_CID_RDS_TX_MUSIC_SPEECH (布尔)``
    如果设置，则表示该频道播放音乐。如果没有设置，则表示该频道播放讲话。如果发射机不区分这两种情况，那么应将其设置为音乐。
``V4L2_CID_RDS_TX_ALT_FREQS_ENABLE (布尔)``
    如果设置，则发送备用频率。
``V4L2_CID_RDS_TX_ALT_FREQS (__u32 数组)``
    备用频率以千赫兹为单位。RDS标准允许定义最多25个频率。驱动程序可能支持较少的频率，请检查数组大小。
``V4L2_CID_AUDIO_LIMITER_ENABLED (布尔)``
    启用或禁用音频偏差限制功能。当试图最大化音频音量、最小化接收机产生的失真并防止过调制时，此限制器非常有用。
``V4L2_CID_AUDIO_LIMITER_RELEASE_TIME (整数)``
    设置音频偏差限制功能的释放时间。单位为微秒。步长和范围取决于具体的驱动程序。
``V4L2_CID_AUDIO_LIMITER_DEVIATION (integer)``
    配置音频频率偏差级别，单位为Hz。范围和步长取决于驱动程序。

``V4L2_CID_AUDIO_COMPRESSION_ENABLED (boolean)``
    启用或禁用音频压缩功能。此功能通过固定增益放大阈值以下的信号，并按阈值与增益之比压缩阈值以上的音频信号。

``V4L2_CID_AUDIO_COMPRESSION_GAIN (integer)``
    设置音频压缩功能的增益。这是一个dB值。范围和步长取决于驱动程序。

``V4L2_CID_AUDIO_COMPRESSION_THRESHOLD (integer)``
    设置音频压缩功能的阈值水平。这是一个dB值。范围和步长取决于驱动程序。

``V4L2_CID_AUDIO_COMPRESSION_ATTACK_TIME (integer)``
    设置音频压缩功能的启动时间。这是一个微秒值。范围和步长取决于驱动程序。

``V4L2_CID_AUDIO_COMPRESSION_RELEASE_TIME (integer)``
    设置音频压缩功能的释放时间。这是一个微秒值。范围和步长取决于驱动程序。

``V4L2_CID_PILOT_TONE_ENABLED (boolean)``
    启用或禁用导频音生成功能。

``V4L2_CID_PILOT_TONE_DEVIATION (integer)``
    配置导频音频率偏差级别。单位为Hz。范围和步长取决于驱动程序。

``V4L2_CID_PILOT_TONE_FREQUENCY (integer)``
    配置导频音频率值。单位为Hz。范围和步长取决于驱动程序。

``V4L2_CID_TUNE_PREEMPHASIS``
    (枚举)

    枚举 `v4l2_preemphasis` - 
    配置广播的预加重值。预加重滤波器应用于广播以增强高频音频。根据地区不同，使用的常数为50或75微秒。枚举 `v4l2_preemphasis` 定义了可能的预加重值。具体如下：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_PREEMPHASIS_DISABLED``
      - 不应用预加重
* - ``V4L2_PREEMPHASIS_50_uS``
      - 使用 50 微秒的预加重
* - ``V4L2_PREEMPHASIS_75_uS``
      - 使用 75 微秒的预加重
``V4L2_CID_TUNE_POWER_LEVEL (整型)``
    设置信号传输的输出功率级别。单位为 dBuV。范围和步长取决于驱动程序。
``V4L2_CID_TUNE_ANTENNA_CAPACITOR (整型)``
    如果设置为零，则手动或自动选择天线调谐电容器的值。单位、范围和步长取决于驱动程序。
关于 RDS 规范的更多详细信息，请参阅 :ref:`iec62106` 文档，来自 CENELEC。
