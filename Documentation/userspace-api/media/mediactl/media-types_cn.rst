SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _media-controller-types:

表示媒体图元素的类型和标志
=================================

..  tabularcolumns:: |p{8.2cm}|p{9.3cm}|

.. _media-entity-functions:
.. _MEDIA-ENT-F-UNKNOWN:
.. _MEDIA-ENT-F-V4L2-SUBDEV-UNKNOWN:
.. _MEDIA-ENT-F-IO-V4L:
.. _MEDIA-ENT-F-IO-VBI:
.. _MEDIA-ENT-F-IO-SWRADIO:
.. _MEDIA-ENT-F-IO-DTV:
.. _MEDIA-ENT-F-DTV-DEMOD:
.. _MEDIA-ENT-F-TS-DEMUX:
.. _MEDIA-ENT-F-DTV-CA:
.. _MEDIA-ENT-F-DTV-NET-DECAP:
.. _MEDIA-ENT-F-CONN-RF:
.. _MEDIA-ENT-F-CONN-SVIDEO:
.. _MEDIA-ENT-F-CONN-COMPOSITE:
.. _MEDIA-ENT-F-CAM-SENSOR:
.. _MEDIA-ENT-F-FLASH:
.. _MEDIA-ENT-F-LENS:
.. _MEDIA-ENT-F-ATV-DECODER:
.. _MEDIA-ENT-F-TUNER:
.. _MEDIA-ENT-F-IF-VID-DECODER:
.. _MEDIA-ENT-F-IF-AUD-DECODER:
.. _MEDIA-ENT-F-AUDIO-CAPTURE:
.. _MEDIA-ENT-F-AUDIO-PLAYBACK:
.. _MEDIA-ENT-F-AUDIO-MIXER:
.. _MEDIA-ENT-F-PROC-VIDEO-COMPOSER:
.. _MEDIA-ENT-F-PROC-VIDEO-PIXEL-FORMATTER:
.. _MEDIA-ENT-F-PROC-VIDEO-PIXEL-ENC-CONV:
.. _MEDIA-ENT-F-PROC-VIDEO-LUT:
.. _MEDIA-ENT-F-PROC-VIDEO-SCALER:
.. _MEDIA-ENT-F-PROC-VIDEO-STATISTICS:
.. _MEDIA-ENT-F-PROC-VIDEO-ENCODER:
.. _MEDIA-ENT-F-PROC-VIDEO-DECODER:
.. _MEDIA-ENT-F-PROC-VIDEO-ISP:
.. _MEDIA-ENT-F-VID-MUX:
.. _MEDIA-ENT-F-VID-IF-BRIDGE:
.. _MEDIA-ENT-F-DV-DECODER:
.. _MEDIA-ENT-F-DV-ENCODER:

.. cssclass:: longtable

.. flat-table:: 媒体实体功能
    :header-rows:  0
    :stub-columns: 0

    *  -  ``MEDIA_ENT_F_UNKNOWN`` 和
	  ``MEDIA_ENT_F_V4L2_SUBDEV_UNKNOWN``
       -  未知实体。这通常表明驱动程序没有正确初始化该实体，这是一个内核错误

    *  -  ``MEDIA_ENT_F_IO_V4L``
       -  数据流输入和/或输出实体

    *  -  ``MEDIA_ENT_F_IO_VBI``
       -  V4L VBI 流输入或输出实体

    *  -  ``MEDIA_ENT_F_IO_SWRADIO``
       -  V4L 软件数字无线电（SDR）流输入或输出实体

    *  -  ``MEDIA_ENT_F_IO_DTV``
       -  DVB 数字电视流输入或输出实体

    *  -  ``MEDIA_ENT_F_DTV_DEMOD``
       -  数字电视解调器实体

    *  -  ``MEDIA_ENT_F_TS_DEMUX``
       -  MPEG 传输流解复用实体。可以在硬件上实现或在内核空间通过 Linux DVB 子系统实现

    *  -  ``MEDIA_ENT_F_DTV_CA``
       -  数字电视条件接收模块（CAM）实体

    *  -  ``MEDIA_ENT_F_DTV_NET_DECAP``
       -  数字电视网络 ULE/MLE 解封装实体。可以在硬件上实现或在内核空间实现

    *  -  ``MEDIA_ENT_F_CONN_RF``
       -  射频（RF）信号连接器

    *  -  ``MEDIA_ENT_F_CONN_SVIDEO``
       -  S-视频信号连接器

    *  -  ``MEDIA_ENT_F_CONN_COMPOSITE``
       -  RGB 复合信号连接器

    *  -  ``MEDIA_ENT_F_CAM_SENSOR``
       -  摄像头视频传感器实体

    *  -  ``MEDIA_ENT_F_FLASH``
       -  闪光控制器实体

    *  -  ``MEDIA_ENT_F_LENS``
       -  镜头控制器实体

    *  -  ``MEDIA_ENT_F_ATV_DECODER``
       -  模拟视频解码器，视频解码器的基本功能是从多种来源（如广播、DVD 播放器、摄像机和录像机）接受模拟视频，并将其分离为亮度和色度部分，然后以某种数字视频标准输出，附带适当的同步信号
*  -  ``MEDIA_ENT_F_TUNER``
    - 数字电视、模拟电视、收音机和/或软件无线电调谐器，包含一个将射频（RF）信号转换为中频（IF）的锁相环（PLL）调谐阶段。现代调谐器内部有用于音频和视频的IF-PLL解码器，但旧型号则在独立实体中实现这些阶段。
*  -  ``MEDIA_ENT_F_IF_VID_DECODER``
    - IF-PLL视频解码器。它接收来自PLL的IF并解码模拟电视视频信号。这通常出现在一些非常旧的模拟调谐器上，如飞利浦MK3设计。它们都包含tda9887（或某些软件兼容的类似芯片，如tda9885）。这些设备使用与调谐器PLL不同的I2C地址。
*  -  ``MEDIA_ENT_F_IF_AUD_DECODER``
    - IF-PLL音频解码器。它接收来自PLL的IF并解码模拟电视音频信号。这通常出现在一些非常旧的模拟硬件上，如Micronas msp3400、飞利浦tda9840、tda985x等。这些设备使用与调谐器PLL不同的I2C地址，并应与IF-PLL视频解码器一起控制。
*  -  ``MEDIA_ENT_F_AUDIO_CAPTURE``
    - 音频捕获功能实体
*  -  ``MEDIA_ENT_F_AUDIO_PLAYBACK``
    - 音频播放功能实体
*  -  ``MEDIA_ENT_F_AUDIO_MIXER``
    - 音频混音功能实体
*  -  ``MEDIA_ENT_F_PROC_VIDEO_COMPOSER``
    - 视频合成器（混合器）。能够进行视频合成的实体至少需要有两个输入端口和一个输出端口，并且能够将输入视频帧合成到输出视频帧上。合成可以采用阿尔法混合、颜色键控、光栅操作（ROP）、拼接或其他方法来完成。
*  -  ``MEDIA_ENT_F_PROC_VIDEO_PIXEL_FORMATTER``
    - 视频像素格式化器。能够进行像素格式化的实体至少需要有一个输入端口和一个输出端口。读取像素格式化器从内存中读取像素，并执行解包、裁剪、颜色键控、阿尔法乘法和像素编码转换的子集。写入像素格式化器执行抖动、像素编码转换和打包，并将像素写入内存。
*  -  ``MEDIA_ENT_F_PROC_VIDEO_PIXEL_ENC_CONV``
    - 视频像素编码转换器。能够进行像素编码转换的实体至少需要有一个输入端口和一个输出端口，并将从其输入端口接收到的像素编码转换为不同编码的输出。像素编码转换包括但不限于RGB与HSV之间的转换、RGB与YUV之间的转换以及CFA（拜耳）与RGB之间的转换。
*  -  ``MEDIA_ENT_F_PROC_VIDEO_LUT``
    - 视频查找表。具有视频查找表处理能力的实体必须有一个输入端口和一个输出端口。它使用在输入端口接收到的像素值来查找内部表中的条目，并将结果输出到输出端口。
查找处理可以在所有组件上分别进行，或者将它们组合起来进行多维查找。

*  -  ``MEDIA_ENT_F_PROC_VIDEO_SCALER``
    - 视频缩放器。具有视频缩放能力的实体必须至少有一个输入端口和一个输出端口，并将通过输入端口接收到的视频帧缩放到不同的分辨率后输出到输出端口。支持的缩放比例范围因实体而异，并且在水平和垂直方向上的缩放比例可能不同（特别是仅在一个方向上支持缩放）。图像分箱和子采样（有时也称为跳过）被视为缩放操作。

*  -  ``MEDIA_ENT_F_PROC_VIDEO_STATISTICS``
    - 视频统计计算（直方图、3A等）。具有统计计算能力的实体必须有一个输入端口和一个输出端口。它对通过输入端口接收到的视频帧进行统计计算，并将统计结果数据输出到输出端口。

*  -  ``MEDIA_ENT_F_PROC_VIDEO_ENCODER``
    - 视频编码器（MPEG、HEVC、VPx等）。具有视频帧压缩能力的实体。必须有一个输入端口和至少一个输出端口。

*  -  ``MEDIA_ENT_F_PROC_VIDEO_DECODER``
    - 视频解码器（MPEG、HEVC、VPx等）。具有解压压缩视频流为未压缩视频帧的能力的实体。必须有一个输入端口和至少一个输出端口。

*  -  ``MEDIA_ENT_F_PROC_VIDEO_ISP``
    - 图像信号处理器（ISP）设备。ISP通常是一种独特的设备，具有特定的控制接口，这些接口使用自定义的V4L2控制和IOCTLs，以及在元数据缓冲区中提供的参数。

*  -  ``MEDIA_ENT_F_VID_MUX``
    - 视频复用器。具有复用能力的实体必须至少有两个输入端口和一个输出端口，并将从活动输入端口接收到的视频帧传递到输出端口。

*  -  ``MEDIA_ENT_F_VID_IF_BRIDGE``
    - 视频接口桥。视频接口桥实体必须至少有一个输入端口和一个输出端口。它通过输入端口从一种类型的输入视频总线（如HDMI、eDP、MIPI CSI-2等）接收视频帧，并通过输出端口将视频帧输出到另一种类型的输出视频总线（如eDP、MIPI CSI-2、并行等）。

*  -  ``MEDIA_ENT_F_DV_DECODER``
    - 数字视频解码器。视频解码器的基本功能是从各种来源接受数字视频，并以某种数字视频标准输出，并带有适当的时序信号。
*  -  ``MEDIA_ENT_F_DV_ENCODER``
   -  数字视频编码器。视频编码器的基本功能是接收来自某种数字视频标准的具有适当同步信号（通常是一个带有同步信号的并行视频总线）的数字视频，并将其输出到如HDMI或DisplayPort等数字视频输出接口。
   
.. tabularcolumns:: |p{5.5cm}|p{12.0cm}|

.. _media-entity-flag:
.. _MEDIA-ENT-FL-DEFAULT:
.. _MEDIA-ENT-FL-CONNECTOR:

.. flat-table:: 媒体实体标志
    :header-rows:  0
    :stub-columns: 0

    *  -  ``MEDIA_ENT_FL_DEFAULT``
       -  对于其类型来说是默认实体。用于发现默认的音频设备、VBI设备和视频设备，以及默认的摄像头传感器等。
*  -  ``MEDIA_ENT_FL_CONNECTOR``
       -  实体代表一个连接器。

.. tabularcolumns:: |p{6.5cm}|p{6.0cm}|p{4.8cm}|

.. _media-intf-type:
.. _MEDIA-INTF-T-DVB-FE:
.. _MEDIA-INTF-T-DVB-DEMUX:
.. _MEDIA-INTF-T-DVB-DVR:
.. _MEDIA-INTF-T-DVB-CA:
.. _MEDIA-INTF-T-DVB-NET:
.. _MEDIA-INTF-T-V4L-VIDEO:
.. _MEDIA-INTF-T-V4L-VBI:
.. _MEDIA-INTF-T-V4L-RADIO:
.. _MEDIA-INTF-T-V4L-SUBDEV:
.. _MEDIA-INTF-T-V4L-SWRADIO:
.. _MEDIA-INTF-T-V4L-TOUCH:
.. _MEDIA-INTF-T-ALSA-PCM-CAPTURE:
.. _MEDIA-INTF-T-ALSA-PCM-PLAYBACK:
.. _MEDIA-INTF-T-ALSA-CONTROL:
.. _MEDIA-INTF-T-ALSA-COMPRESS:
.. _MEDIA-INTF-T-ALSA-RAWMIDI:
.. _MEDIA-INTF-T-ALSA-HWDEP:
.. _MEDIA-INTF-T-ALSA-SEQUENCER:
.. _MEDIA-INTF-T-ALSA-TIMER:

.. flat-table:: 媒体接口类型
    :header-rows:  0
    :stub-columns: 0

    *  -  ``MEDIA_INTF_T_DVB_FE``
       -  数字电视前端的设备节点接口
       -  通常为 `/dev/dvb/adapter?/frontend?`
    
    *  -  ``MEDIA_INTF_T_DVB_DEMUX``
       -  数字电视解复用器的设备节点接口
       -  通常为 `/dev/dvb/adapter?/demux?`
    
    *  -  ``MEDIA_INTF_T_DVB_DVR``
       -  数字电视DVR的设备节点接口
       -  通常为 `/dev/dvb/adapter?/dvr?`
    
    *  -  ``MEDIA_INTF_T_DVB_CA``
       -  数字电视有条件访问的设备节点接口
       -  通常为 `/dev/dvb/adapter?/ca?`
    
    *  -  ``MEDIA_INTF_T_DVB_NET``
       -  数字电视网络控制的设备节点接口
       -  通常为 `/dev/dvb/adapter?/net?`
    
    *  -  ``MEDIA_INTF_T_V4L_VIDEO``
       -  视频设备的设备节点接口（V4L）
       -  通常为 `/dev/video?`
    
    *  -  ``MEDIA_INTF_T_V4L_VBI``
       -  VBI设备的设备节点接口（V4L）
       -  通常为 `/dev/vbi?`
    
    *  -  ``MEDIA_INTF_T_V4L_RADIO``
       -  广播设备的设备节点接口（V4L）
       -  通常为 `/dev/radio?`
    
    *  -  ``MEDIA_INTF_T_V4L_SUBDEV``
       -  V4L子设备的设备节点接口
       -  通常为 `/dev/v4l-subdev?`
    
    *  -  ``MEDIA_INTF_T_V4L_SWRADIO``
       -  软件定义无线电设备的设备节点接口（V4L）
       -  通常为 `/dev/swradio?`
    
    *  -  ``MEDIA_INTF_T_V4L_TOUCH``
       -  触摸设备的设备节点接口（V4L）
       -  通常为 `/dev/v4l-touch?`
    
    *  -  ``MEDIA_INTF_T_ALSA_PCM_CAPTURE``
       -  ALSA PCM捕获的设备节点接口
       -  通常为 `/dev/snd/pcmC?D?c`
    
    *  -  ``MEDIA_INTF_T_ALSA_PCM_PLAYBACK``
       -  ALSA PCM播放的设备节点接口
       -  通常为 `/dev/snd/pcmC?D?p`
    
    *  -  ``MEDIA_INTF_T_ALSA_CONTROL``
       -  ALSA控制的设备节点接口
       -  通常为 `/dev/snd/controlC?`
    
    *  -  ``MEDIA_INTF_T_ALSA_COMPRESS``
       -  ALSA压缩的设备节点接口
       -  通常为 `/dev/snd/compr?`
    
    *  -  ``MEDIA_INTF_T_ALSA_RAWMIDI``
       -  ALSA Raw MIDI的设备节点接口
       -  通常为 `/dev/snd/midi?`
    
    *  -  ``MEDIA_INTF_T_ALSA_HWDEP``
       -  ALSA硬件依赖的设备节点接口
       -  通常为 `/dev/snd/hwC?D?`
    
    *  -  ``MEDIA_INTF_T_ALSA_SEQUENCER``
       -  ALSA音序器的设备节点接口
       -  通常为 `/dev/snd/seq`
    
    *  -  ``MEDIA_INTF_T_ALSA_TIMER``
       -  ALSA定时器的设备节点接口
       -  通常为 `/dev/snd/timer`

.. tabularcolumns:: |p{5.5cm}|p{12.0cm}|

.. _media-pad-flag:
.. _MEDIA-PAD-FL-SINK:
.. _MEDIA-PAD-FL-SOURCE:
.. _MEDIA-PAD-FL-MUST-CONNECT:

.. flat-table:: 媒体端口标志
    :header-rows:  0
    :stub-columns: 0

    *  -  ``MEDIA_PAD_FL_SINK``
       -  输入端口，相对于实体而言。输入端口接收数据，并且是链接的目标。
*  -  ``MEDIA_PAD_FL_SOURCE``
       -  输出端口，相对于实体而言。输出端口生成数据，并且是链接的起点。
*  -  ``MEDIA_PAD_FL_MUST_CONNECT``
       -  如果设置了此标志，则该端口要能够流传输必须至少通过一个启用的链接连接。即使没有设置此标志，也可能存在临时原因（例如依赖设备配置）需要启用链接；缺少此标志并不意味着不需要链接。
每个端口中只能设置一个 ``MEDIA_PAD_FL_SINK`` 和 ``MEDIA_PAD_FL_SOURCE`` 标志。

.. tabularcolumns:: |p{5.5cm}|p{12.0cm}|

.. _media-link-flag:
.. _MEDIA-LNK-FL-ENABLED:
.. _MEDIA-LNK-FL-IMMUTABLE:
.. _MEDIA-LNK-FL-DYNAMIC:
.. _MEDIA-LNK-FL-LINK-TYPE:

.. flat-table:: 媒体链接标志
    :header-rows:  0
    :stub-columns: 0

    *  -  ``MEDIA_LNK_FL_ENABLED``
       -  链接已启用并且可以用来传输媒体数据。当两个或多个链接指向同一个输入端口时，一次只能启用其中一个。
*  -  ``MEDIA_LNK_FL_IMMUTABLE``
       -  链接的启用状态在运行时不能修改。不可变链接始终处于启用状态。
*  -  ``MEDIA_LNK_FL_DYNAMIC``
       -  链接的启用状态可以在流传输过程中修改。此标志由驱动程序设置，应用程序只读。
*  -  ``MEDIA_LNK_FL_LINK_TYPE``
   -  这是一个位掩码，用于定义链接的类型。当前支持以下链接类型：

	  .. _MEDIA-LNK-FL-DATA-LINK:

	  ``MEDIA_LNK_FL_DATA_LINK`` 用于表示两个 pad 之间的数据连接
.. _MEDIA-LNK-FL-INTERFACE-LINK:

	  ``MEDIA_LNK_FL_INTERFACE_LINK`` 用于将实体与其接口关联
.. _MEDIA-LNK-FL-ANCILLARY-LINK:

	  ``MEDIA_LNK_FL_ANCILLARY_LINK`` 用于表示两个实体之间的物理关系。该链接可能是不可变的，也可能不是，因此应用程序不应假设任何一种情况
