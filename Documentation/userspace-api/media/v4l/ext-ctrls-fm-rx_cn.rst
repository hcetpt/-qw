SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _fm-rx-controls:

*******************************
FM 接收器控制参考
*******************************

FM 接收器（FM_RX）类包括了具有 FM 接收功能的设备的常用控制。

.. _fm-rx-control-id:

FM_RX 控制 ID
=============

``V4L2_CID_FM_RX_CLASS (class)``
    FM_RX 类描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回此类控制的描述。
``V4L2_CID_RDS_RECEPTION (boolean)``
    启用或禁用无线电调谐器的 RDS 接收。
``V4L2_CID_RDS_RX_PTY (integer)``
    获取 RDS 节目类型字段。该字段编码了多达 31 种预定义的节目类型。
``V4L2_CID_RDS_RX_PS_NAME (string)``
    获取节目服务名称（PS_NAME）。它用于接收器上的静态显示。这是听众识别和选择节目服务的主要帮助。在 :ref:`iec62106` 的附录 E 中，RDS 规范对节目服务名称字符串的正确字符编码进行了完整描述。根据 RDS 规范，PS 通常是一个八字符文本。然而，也有可能找到能够滚动 8 x N 字符长度字符串的接收器。因此，此控制必须以 8 个字符为单位进行配置。结果是它必须始终包含一个长度为 8 的倍数的字符串。
``V4L2_CID_RDS_RX_RADIO_TEXT (string)``
    获取广播文本信息。这是一个关于正在播放内容的文字描述。RDS 广播文本可以在广播商希望传输更长的 PS 名称、与节目相关的信息或其他文字时使用。在这种情况下，RadioText 可以作为 ``V4L2_CID_RDS_RX_PS_NAME`` 的补充。广播文本字符串的编码也在 :ref:`iec62106` 的附录 E 中进行了完整描述。广播文本字符串的长度取决于所使用的 RDS 块，可以是 32（2A 块）或 64（2B 块）。然而，也有可能找到能够滚动 32 x N 或 64 x N 字符长度字符串的接收器。因此，此控制必须以 32 或 64 个字符为单位进行配置。结果是它必须始终包含一个长度为 32 或 64 的倍数的字符串。
``V4L2_CID_RDS_RX_TRAFFIC_ANNOUNCEMENT (boolean)``
    如果设置，则正在进行交通公告。
``V4L2_CID_RDS_RX_TRAFFIC_PROGRAM (boolean)``
    如果设置，则当前调谐的节目携带交通公告。
``V4L2_CID_RDS_RX_MUSIC_SPEECH (boolean)``
    如果设置，则该频道播放音乐。如果清除，则播放语音。如果发射器不区分这两种情况，则默认为设置状态。
``V4L2_CID_TUNE_DEEMPHASIS``
    （枚举）

enum v4l2_deemphasis -
    配置接收时的去加重值。对广播应用去加重滤波器以增强高频音频频率。根据地区不同，使用的时间常数为 50 微秒或 75 微秒。枚举 v4l2_deemphasis 定义了可能的去加重值。具体如下：

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_DEEMPHASIS_DISABLED``
      - 不应用去加重
    * - ``V4L2_DEEMPHASIS_50_uS``
      - 使用 50 微秒的去加重
* - ``V4L2_DEEMPHASIS_75_uS``
  - 使用 75 微秒的去加重
