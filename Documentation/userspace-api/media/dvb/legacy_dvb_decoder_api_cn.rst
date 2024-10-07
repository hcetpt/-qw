.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later 或 GPL-2.0

.. _legacy_dvb_decoder_api:

============================
遗留的 DVB MPEG 解码器 API
============================

.. _legacy_dvb_decoder_notes:

一般说明
=============

此 API 最初是为 DVB 设计的，因此仅限于在这些数字电视广播系统中使用的 :ref:`legacy_dvb_decoder_formats`。为了克服这一限制，设计了更为灵活的 :ref:`V4L2 <v4l2spec>` API 来取代这部分 DVB API。尽管如此，仍有一些项目是基于此 API 构建的。为了确保兼容性，此 API 保持不变。

.. 注意:: 在新的驱动程序中 **不要** 使用此 API！

    对于音频和视频，请使用 :ref:`V4L2 <v4l2spec>` 和 ALSA API。
    管道应使用 :ref:`媒体控制器 API <media_controller>` 进行设置。
    
    实际上，解码器似乎被区别对待。应用程序通常知道正在使用哪个解码器或专门为此类解码器编写。由于已知这些能力，因此很少使用查询功能。

.. _legacy_dvb_decoder_formats:

数据格式
=============

此 API 是为 DVB 及其兼容的广播系统设计的。因此，唯一支持的数据格式是 ISO/IEC 13818-1 兼容的 MPEG 流。根据所用解码器的不同，支持的有效载荷可能会有所不同。
时间戳始终是ITU T-REC-H.222.0/ISO/IEC 13818-1中定义的MPEG PTS，除非另有说明。
对于存储录制内容，通常使用TS流，较少情况下使用PES。
这两种变体通常都可以接受用于播放，但可能取决于驱动程序。

目录
=================

.. toctree::
    :maxdepth: 2

    legacy_dvb_video
    legacy_dvb_audio
    legacy_dvb_osd

（注：`.. toctree::` 和其下的条目是用来生成目录结构的伪代码，通常在文档生成工具中使用。这里直接保留了原文格式。）
