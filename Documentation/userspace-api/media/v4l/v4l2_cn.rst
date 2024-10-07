.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later
.. include:: <isonum.txt>

.. _v4l2spec:

############################
第一部分 - Linux视频API
############################

本部分描述了Linux视频API版本2（V4L2 API）规范
**修订版 4.5**

.. toctree::
    :caption: 目录
    :numbered:
    :maxdepth: 5

    common
    pixfmt
    io
    devices
    libv4l
    compat
    user-func
    common-defs
    videodev
    capture-example
    v4l2grab-example
    biblio


**********************
修订和版权
**********************

作者，按字母顺序：

- Ailus, Sakari <sakari.ailus@iki.fi>

  - 子设备选择API
- Carvalho Chehab, Mauro <mchehab+samsung@kernel.org>

  - 文档化libv4l，设计并添加了v4l2grab示例，遥控器章节
- Dirks, Bill

  - V4L2 API和文档的原始作者
- Figa, Tomasz <tfiga@chromium.org>

  - 文档化内存到内存解码接口
- 文档化内存到内存编码接口
- H Schimek, Michael <mschimek@gmx.at>

  - V4L2 API和文档的原始作者
- Karicheri, Muralidharan <m-karicheri2@ti.com>

  - 文档化数字视频时序API
- Osciak, Pawel <posciak@chromium.org>

  - 文档化内存到内存解码接口
- 文档化内存到内存编码接口
- Osciak, Pawel <pawel@osciak.com>

  - 设计并记录了多平面API
- Palosaari, Antti <crope@iki.fi>

  - SDR API
- Ribalda, Ricardo

  - 引入HSV格式及其他一些小改动
- Rubli, Martin

  - 设计并记录了VIDIOC_ENUM_FRAMESIZES和VIDIOC_ENUM_FRAMEINTERVALS的ioctl
- Walls, Andy <awalls@md.metrocast.net>

  - 在此规范中记录了场同步的V4L2_MPEG_STREAM_VBI_FMT_IVTV MPEG流嵌入切片VBI数据格式
- Verkuil, Hans <hverkuil@xs4all.nl>

  - 设计并记录了VIDIOC_LOG_STATUS ioctl、扩展控制ioctl、大部分切片VBI API、MPEG编码器和解码器API及DV时序API
**版权** |copy| 1999-2018：Bill Dirks, Michael H. Schimek, Hans Verkuil, Martin Rubli, Andy Walls, Muralidharan Karicheri, Mauro Carvalho Chehab, Pawel Osciak, Sakari Ailus & Antti Palosaari, Tomasz Figa

除非明确声明为GPL，否则本部分中的编程示例可以不受限制地使用和分发
****************
修订历史
****************

:revision: 4.10 / 2016-07-15 (*rr*)

引入HSV格式
:revision: 4.5 / 2015-10-29 (*rr*)

扩展VIDIOC_G_EXT_CTRLS；用一个新的包含ctrl_class和which的联合体替换ctrl_class。Which用于选择控制的当前值或默认值
:revision: 4.4 / 2015-05-26 (*ap*)

将V4L2_TUNER_ADC重命名为V4L2_TUNER_SDR。添加了V4L2_CID_RF_TUNER_RF_GAIN控制。为软件定义无线电（SDR）接口增加了发射支持
修订版：4.1 / 2015-02-13 (*mcc*)

修复媒体控制器设备节点的文档，并添加对 DVB 设备节点的支持。添加对调谐器子设备的支持。
修订版：3.19 / 2014-12-05 (*hv*)

重写了颜色空间章节，添加了新的枚举类型 `v4l2_ycbcr_encoding` 和 `v4l2_quantization` 字段到结构体 `v4l2_pix_format`、`v4l2_pix_format_mplane` 和 `v4l2_mbus_framefmt`。
修订版：3.17 / 2014-08-04 (*lp, hv*)

扩展了结构体 `v4l2_pix_format`。添加了格式标志。添加了复合控制类型和 VIDIOC_QUERY_EXT_CTRL。
修订版：3.15 / 2014-02-03 (*hv, ap*)

更新了“常用 API 元素”的多个部分：“打开和关闭设备”、“查询功能”、“应用程序优先级”、“视频输入和输出”、“音频输入和输出”、“调谐器和调制器”、“视频标准”以及“数字视频（DV）定时”。添加了 SDR API。
修订版：3.14 / 2013-11-25 (*rr*)

将 v4l2_rect 中的宽度和高度设置为无符号整数。
修订版：3.11 / 2013-05-26 (*hv*)

移除了过时的 VIDIOC_DBG_G_CHIP_IDENT ioctl。
修订版：3.10 / 2013-03-25 (*hv*)

移除了过时且未使用的 DV_PRESET ioctl：VIDIOC_G_DV_PRESET、VIDIOC_S_DV_PRESET、VIDIOC_QUERY_DV_PRESET 和 VIDIOC_ENUM_DV_PRESET。移除相关的 v4l2_input/output 能力标志 V4L2_IN_CAP_PRESETS 和 V4L2_OUT_CAP_PRESETS。添加了 VIDIOC_DBG_G_CHIP_INFO。
修订版：3.9 / 2012-12-03 (*sa, sn*)

在 v4l2_buffer 中添加了时间戳类型。添加了 V4L2_EVENT_CTRL_CH_RANGE 控制事件变化标志。
修订版：3.6 / 2012-07-02 (*hv*)

添加了 VIDIOC_ENUM_FREQ_BANDS。
修订版本：3.5 / 2012-05-07 (*sa, sn, hv*)

新增了 V4L2_CTRL_TYPE_INTEGER_MENU 和 V4L2 子设备选择 API。
改进了对 V4L2_CID_COLORFX 控制的描述，并新增了 V4L2_CID_COLORFX_CBCR 控制。新增了以下相机控制：
V4L2_CID_AUTO_EXPOSURE_BIAS，
V4L2_CID_AUTO_N_PRESET_WHITE_BALANCE，
V4L2_CID_IMAGE_STABILIZATION，V4L2_CID_ISO_SENSITIVITY，
V4L2_CID_ISO_SENSITIVITY_AUTO，V4L2_CID_EXPOSURE_METERING，
V4L2_CID_SCENE_MODE，V4L2_CID_3A_LOCK，
V4L2_CID_AUTO_FOCUS_START，V4L2_CID_AUTO_FOCUS_STOP，
V4L2_CID_AUTO_FOCUS_STATUS 和 V4L2_CID_AUTO_FOCUS_RANGE。新增了 VIDIOC_ENUM_DV_TIMINGS、VIDIOC_QUERY_DV_TIMINGS 和 VIDIOC_DV_TIMINGS_CAP。

修订版本：3.4 / 2012-01-25 (*sn*)

新增了 JPEG 压缩控制类。<jpeg-controls>

修订版本：3.3 / 2012-01-11 (*hv*)

在 struct v4l2_capabilities 中新增了 device_caps 字段。

修订版本：3.2 / 2011-08-26 (*hv*)

新增了 V4L2_CTRL_FLAG_VOLATILE。

修订版本：3.1 / 2011-06-27 (*mcc, po, hv*)

说明了 VIDIOC_QUERYCAP 现在返回的是每个子系统的版本而不是每个驱动程序的版本。标准化了无效 ioctl 的错误代码。新增了 V4L2_CTRL_TYPE_BITMASK。

修订版本：2.6.39 / 2011-03-01 (*mcc, po*)

从 videodev2.h 头文件中移除了 VIDIOC_*_OLD，并更新以反映最新变化。新增了多平面 API。<planar-apis>

修订版本：2.6.37 / 2010-08-06 (*hv*)

移除了过时的 vtx（视频文本）API。

修订版本：2.6.33 / 2009-12-03 (*mk*)

新增了数字视频定时 API 的文档。

修订版本：2.6.32 / 2009-08-31 (*mcc*)

从现在起，修订版本将与内核版本匹配，其中 V4L2 API 变更将被 Linux 内核使用。同时新增了遥控器章节。

修订版本：0.29 / 2009-08-26 (*ev*)

新增了字符串控制和 FM 发射器控制的文档。
修订版本：0.28 / 2009-08-26 (*gl*)

添加了 V4L2_CID_BAND_STOP_FILTER 的文档

修订版本：0.27 / 2009-08-15 (*mcc*)

添加了 libv4l 和遥控器的文档；添加了 v4l2grab 和 keytable 应用示例

修订版本：0.26 / 2009-07-23 (*hv*)

最终确定了 RDS 捕获 API。添加了调制器和 RDS 编码器功能。添加了字符串控制的支持

修订版本：0.25 / 2009-01-18 (*hv*)

添加了像素格式 VYUY、NV16 和 NV61，并更改了调试 ioctl 命令 VIDIOC_DBG_G/S_REGISTER 和 VIDIOC_DBG_G_CHIP_IDENT。添加了相机控制 V4L2_CID_ZOOM_ABSOLUTE、V4L2_CID_ZOOM_RELATIVE、V4L2_CID_ZOOM_CONTINUOUS 和 V4L2_CID_PRIVACY

修订版本：0.24 / 2008-03-04 (*mhs*)

添加了像素格式 Y16 和 SBGGR16，新的控制项以及一个相机控制类。移除了 VIDIOC_G/S_MPEGCOMP

修订版本：0.23 / 2007-08-30 (*mhs*)

修正了 VIDIOC_DBG_G/S_REGISTER 中的一个拼写错误。澄清了打包像素格式的字节顺序

修订版本：0.22 / 2007-08-29 (*mhs*)

添加了视频输出叠加接口，新的 MPEG 控制项，V4L2_FIELD_INTERLACED_TB 和 V4L2_FIELD_INTERLACED_BT，VIDIOC_DBG_G/S_REGISTER，VIDIOC\_(TRY\_)ENCODER_CMD，VIDIOC_G_CHIP_IDENT，VIDIOC_G_ENC_INDEX，新的像素格式。在裁剪章节中对 RGB 像素格式以及 mmap()、poll()、select()、read() 和 write() 函数进行了澄清。修复了排版错误

修订版本：0.21 / 2006-12-19 (*mhs*)

修复了 VIDIOC_G_EXT_CTRLS 部分中的一个链接

修订版本：0.20 / 2006-11-24 (*mhs*)

澄清了 struct v4l2_input 和 v4l2_output 中 audioset 字段的目的
修订版本：0.19 / 2006-10-19 (*mhs*)

记录了 V4L2_PIX_FMT_RGB444

修订版本：0.18 / 2006-10-18 (*mhs*)

添加了 Hans Verkuil 对扩展控制的描述。链接了 V4L2_PIX_FMT_MPEG 和 V4L2_CID_MPEG_STREAM_TYPE

修订版本：0.17 / 2006-10-12 (*mhs*)

修正了 V4L2_PIX_FMT_HM12 的描述

修订版本：0.16 / 2006-10-08 (*mhs*)

VIDIOC_ENUM_FRAMESIZES 和 VIDIOC_ENUM_FRAMEINTERVALS 现在是 API 的一部分

修订版本：0.15 / 2006-09-23 (*mhs*)

清理了参考文献，增加了 BT.653 和 BT.1119。对于用户指针 I/O，capture.c/start_capturing() 没有初始化缓冲区索引。记录了 V4L MPEG 和 MJPEG VID_TYPEs 以及 V4L2_PIX_FMT_SBGGR8。更新了保留像素格式列表。请参阅 API 变更的历史章节

修订版本：0.14 / 2006-09-14 (*mr*)

添加了 VIDIOC_ENUM_FRAMESIZES 和 VIDIOC_ENUM_FRAMEINTERVALS 提案，用于数字设备的帧格式枚举

修订版本：0.13 / 2006-04-07 (*mhs*)

修正了 struct v4l2_window clips 的描述。新增了 V4L2_STD_ 和 V4L2_TUNER_MODE_LANG1_LANG2 定义

修订版本：0.12 / 2006-02-03 (*mhs*)

修正了 struct v4l2_captureparm 和 v4l2_outputparm 的描述

修订版本：0.11 / 2006-01-27 (*mhs*)

改进了 struct v4l2_tuner 的描述
修订版本：0.10 / 2006-01-10 (*mhs*)

对 VIDIOC_G_INPUT 和 VIDIOC_S_PARM 的澄清

修订版本：0.9 / 2005-11-27 (*mhs*)

改进了 525 行编号图。Hans Verkuil 和我重写了切片 VBI 部分。他还贡献了一个关于 VIDIOC_LOG_STATUS 的页面。
修复了视频标准选择示例中的 VIDIOC_S_STD 调用。
各种更新

修订版本：0.8 / 2004-10-04 (*mhs*)

某个垃圾片段混入了捕获示例中，已移除。

修订版本：0.7 / 2004-09-19 (*mhs*)

修复了视频标准选择、控制枚举、下采样和宽高比示例。在视频捕获示例中添加了读取和用户指针 I/O。

修订版本：0.6 / 2004-08-01 (*mhs*)

v4l2_buffer 更改，添加了视频捕获示例，进行了各种修正。

修订版本：0.5 / 2003-11-05 (*mhs*)

像素格式勘误。

修订版本：0.4 / 2003-09-17 (*mhs*)

修正了源代码和 Makefile 以生成 PDF 文件。SGML 修复。添加了最新的 API 变更。填补了历史章节中的空白。

修订版本：0.3 / 2003-02-05 (*mhs*)

另一个草稿，更多的修正。
修订版：0.2 / 2003-01-15 (*mhs*)

第二稿，根据 Gerd Knorr 指出的修正意见
:revision: 0.1 / 2002-12-01 (*mhs*)

第一稿，基于 Bill Dirks 的文档和 V4L 邮件列表中的讨论
