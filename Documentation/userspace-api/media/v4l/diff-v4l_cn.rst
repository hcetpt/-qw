SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _v4l-diff:

********************************
V4L 和 V4L2 之间的差异
********************************

Video For Linux API 最初在 Linux 2.1 中引入，以统一并替换由驱动程序编写者在过去几年中独立开发的各种电视和广播设备相关接口。从 Linux 2.5 开始，改进后的 V4L2 API 取代了 V4L API。内核中对旧的 V4L 调用的支持已被移除，但库 :ref:`libv4l` 支持将一个 V4L API 系统调用转换为 V4L2 调用。

打开和关闭设备
===========================

出于兼容性的原因，推荐用于 V4L2 视频捕获、覆盖、广播和原始 VBI 捕获设备的字符设备文件名称并未改变，它们与 V4L 使用的相同。这些名称列于 :ref:`devices` 和下面的 :ref:`v4l-dev`。
V4L2 中已经移除了电传视讯设备（次设备号范围 192-223），并且它们不再存在。现在已经没有硬件来处理纯电传视讯，而是使用原始或切片 VBI。
V4L 的 ``videodev`` 模块会根据加载顺序自动给驱动程序分配次设备号，具体取决于注册的设备类型。我们建议默认情况下 V4L2 驱动程序注册具有相同编号的设备，但系统管理员可以使用驱动程序模块选项分配任意的次设备号。主设备号仍然是 81。

.. _v4l-dev:

.. flat-table:: V4L 设备类型、名称和编号
    :header-rows:  1
    :stub-columns: 0

    * - 设备类型
      - 文件名称
      - 次设备号
    * - 视频捕获和覆盖
      - ``/dev/video`` 和 ``/dev/bttv0``\  [#f1]_，``/dev/video0`` 到 ``/dev/video63``
      - 0-63
    * - 广播接收器
      - ``/dev/radio``\  [#f2]_，``/dev/radio0`` 到 ``/dev/radio63``
      - 64-127
    * - 原始 VBI 捕获
      - ``/dev/vbi``，``/dev/vbi0`` 到 ``/dev/vbi31``
      - 224-255

V4L 禁止（或曾经禁止）对设备文件进行多次打开
V4L2 驱动程序 *可能* 支持多次打开，请参阅 :ref:`open` 获取详细信息及其后果
V4L 驱动程序会对 V4L2 的 ioctl 返回 ``EINVAL`` 错误码

查询功能
=====================

V4L 的 ``VIDIOCGCAP`` ioctl 与 V4L2 的 :ref:`VIDIOC_QUERYCAP` 相当
结构体 ``video_capability`` 中的 ``name`` 字段变成了结构体 :c:type:`v4l2_capability` 中的 ``card``，``type`` 被 ``capabilities`` 替换。注意 V4L2 不区分设备类型，最好将其视为支持一组相关功能的基本视频输入、视频输出和广播设备，例如视频捕获、视频覆盖和 VBI 捕获。详见 :ref:`open`

.. raw:: latex

   \small

.. tabularcolumns:: |p{5.3cm}|p{6.7cm}|p{5.3cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - ``struct video_capability`` ``type``
      - 结构体 :c:type:`v4l2_capability` 的 ``capabilities`` 标志
      - 目的
    * - ``VID_TYPE_CAPTURE``
      - ``V4L2_CAP_VIDEO_CAPTURE``
      - 支持 :ref:`视频捕获 <capture>` 接口
* - ``VID_TYPE_TUNER``
      - ``V4L2_CAP_TUNER``
      - 设备具有调谐器或调制器<ref>`调谐器或调制器 <tuner>`
* - ``VID_TYPE_TELETEXT``
      - ``V4L2_CAP_VBI_CAPTURE``
      - 支持<ref>`原始VBI捕获 <raw-vbi>`接口
* - ``VID_TYPE_OVERLAY``
      - ``V4L2_CAP_VIDEO_OVERLAY``
      - 支持<ref>`视频叠加 <overlay>`接口
* - ``VID_TYPE_CHROMAKEY``
      - 在结构体:c:type:`v4l2_framebuffer`的`capability`字段中的``V4L2_FBUF_CAP_CHROMAKEY``
      - 是否支持色键叠加。有关更多叠加信息，请参阅<ref>`overlay`
* - ``VID_TYPE_CLIPPING``
      - 在结构体:c:type:`v4l2_framebuffer`的`capability`字段中的``V4L2_FBUF_CAP_LIST_CLIPPING``和``V4L2_FBUF_CAP_BITMAP_CLIPPING``
      - 是否支持裁剪叠加图像，详情请参阅<ref>`overlay`
* - ``VID_TYPE_FRAMERAM``
      - 在结构体:c:type:`v4l2_framebuffer`的`capability`字段中未设置``V4L2_FBUF_CAP_EXTERNOVERLAY``
      - 是否支持叠加覆盖帧缓冲区内存，详情请参阅<ref>`overlay`
* - ``VID_TYPE_SCALES``
      - ``-``
      - 此标志表示硬件是否能够缩放图像。V4L2 API通过设置裁剪尺寸和图像大小来隐含地指定缩放因子，分别是通过:ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>`和:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl。驱动程序返回尽可能接近的尺寸。有关裁剪和缩放的更多信息，请参阅:ref:`crop`
* - ``VID_TYPE_MONOCHROME``
      - ``-``
      - 应用程序可以使用:ref:`VIDIOC_ENUM_FMT` ioctl枚举支持的图像格式，以确定设备是否仅支持灰度捕捉。有关图像格式的更多信息，请参阅:ref:`pixfmt`
* - ``VID_TYPE_SUBCAPTURE``
      - ``-``
      - 应用程序可以通过调用:ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` ioctl来确定设备是否支持捕获整个图片的一部分（在V4L2中称为“裁剪”）。如果不支持，则ioctl会返回`EINVAL`错误码。有关裁剪和缩放的更多信息，请参阅:ref:`crop`
* - ``VID_TYPE_MPEG_DECODER``
      - ``-``
      - 应用程序可以使用:ref:`VIDIOC_ENUM_FMT` ioctl枚举支持的图像格式，以确定设备是否支持MPEG流
* - ``VID_TYPE_MPEG_ENCODER``
      - ``-``
      - 参见上文
* - ``VID_TYPE_MJPEG_DECODER``
      - ``-``
      - 参见上文
* - ``VID_TYPE_MJPEG_ENCODER``
      - ``-``
      - 参见上文

.. raw:: latex

   \normalsize

`audios` 字段被 `capabilities` 标志 `V4L2_CAP_AUDIO` 替换，表示设备是否有音频输入或输出。应用程序可以通过 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` ioctl 列举音频输入来确定其数量。音频 ioctl 的描述参见 :ref:`audio`
`maxwidth`、`maxheight`、`minwidth` 和 `minheight` 字段已被移除。通过调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 或 :ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` ioctl 并指定所需的尺寸，可以返回根据当前视频标准、裁剪和缩放限制所能达到的最接近的尺寸。

视频源
======

V4L 提供了 `VIDIOCGCHAN` 和 `VIDIOCSCHAN` ioctl 使用 `video_channel` 结构体来枚举 V4L 设备的视频输入。等效的 V4L2 ioctl 是 :ref:`VIDIOC_ENUMINPUT`、:ref:`VIDIOC_G_INPUT <VIDIOC_G_INPUT>` 和 :ref:`VIDIOC_S_INPUT <VIDIOC_G_INPUT>`，使用 :c:type:`v4l2_input` 结构体，如 :ref:`video` 中所述。
`channel` 字段（用于计数输入）重命名为 `index`，视频输入类型重命名如下：

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - `video_channel` 结构体 `type`
      - :c:type:`v4l2_input` 结构体 `type`
    * - `VIDEO_TYPE_TV`
      - `V4L2_INPUT_TYPE_TUNER`
    * - `VIDEO_TYPE_CAMERA`
      - `V4L2_INPUT_TYPE_CAMERA`

与 `tuners` 字段不同的是，该字段表示此输入的调谐器数量，V4L2 假定每个视频输入最多连接一个调谐器。但是，一个调谐器可以有多个输入，例如 RF 连接器，并且一个设备可以有多个调谐器。如果有的话，与输入相关的调谐器的索引号存储在 :c:type:`v4l2_input` 结构体的 `tuner` 字段中。调谐器的枚举讨论参见 :ref:`tuner`
冗余的 `VIDEO_VC_TUNER` 标志被删除。与调谐器关联的视频输入类型为 `V4L2_INPUT_TYPE_TUNER`。`VIDEO_VC_AUDIO` 标志被 `audioset` 字段替换。V4L2 考虑到最多有 32 个音频输入的设备。`audioset` 字段中的每个设置位代表一个与此视频输入结合的音频输入。有关音频输入及其切换方式的信息，请参见 :ref:`audio`
描述支持的视频标准的 `norm` 字段被 `std` 替换。V4L 规范提到一个标志 `VIDEO_VC_NORM`，表示标准是否可以更改。此标志是后来与 `norm` 字段一起添加的，并且在此期间已被删除。V4L2 对视频标准采取了类似但更全面的方法，更多信息请参见 :ref:`standard`
### 调谐

V4L 的 `VIDIOCGTUNER` 和 `VIDIOCSTUNER` ioctl 以及结构体 `video_tuner` 可用于枚举 V4L 电视或广播设备的调谐器。V4L2 相应的 ioctl 是 :ref:`VIDIOC_G_TUNER <VIDIOC_G_TUNER>` 和 :ref:`VIDIOC_S_TUNER <VIDIOC_G_TUNER>`，使用结构体 :c:type:`v4l2_tuner`。调谐器在 :ref:`tuner` 中有详细介绍。

- 字段 `tuner`（用于计数调谐器）被重命名为 `index`。
- 字段 `name`、`rangelow` 和 `rangehigh` 保持不变。
- 标志 `VIDEO_TUNER_PAL`、`VIDEO_TUNER_NTSC` 和 `VIDEO_TUNER_SECAM`（表示支持的视频标准）被删除。这些信息现在包含在关联的结构体 :c:type:`v4l2_input` 中。
- 对于标志 `VIDEO_TUNER_NORM`（表示是否可以切换视频标准），目前没有替代方案。
- 选择不同视频标准的字段 `mode` 被一组新的 ioctl 和结构体所取代，详情见 :ref:`standard`。
- 由于其普遍性，应提及 BTTV 驱动程序除了支持常规的 `VIDEO_MODE_PAL`（0）、`VIDEO_MODE_NTSC`、`VIDEO_MODE_SECAM` 和 `VIDEO_MODE_AUTO`（3）之外，还支持 N/PAL Argentina、M/PAL、N/PAL 和 NTSC Japan，对应的编号为 3-6（注意这一点）。
- 表示立体声接收的标志 `VIDEO_TUNER_STEREO_ON` 在字段 `rxsubchans` 中变成了 `V4L2_TUNER_SUB_STEREO`。该字段还允许检测单声道和双语音频，详见结构体 :c:type:`v4l2_tuner` 的定义。
- 目前没有替换标志 `VIDEO_TUNER_RDS_ON` 和 `VIDEO_TUNER_MBS_ON` 的方案。
- 标志 `VIDEO_TUNER_LOW` 被重命名为 `V4L2_TUNER_CAP_LOW` 并放在结构体 :c:type:`v4l2_tuner` 的 `capability` 字段中。
- 更改调谐器频率的 ioctl `VIDIOCGFREQ` 和 `VIDIOCSFREQ` 被重命名为 :ref:`VIDIOC_G_FREQUENCY <VIDIOC_G_FREQUENCY>` 和 :ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>`。它们接受指向结构体 :c:type:`v4l2_frequency` 的指针，而不是无符号长整型。

### 图像属性

V4L2 没有 `VIDIOCGPICT` 和 `VIDIOCSPICT` ioctl 及结构体 `video_picture` 的等价物。以下字段被 V4L2 控制所取代，可以通过 ioctl :ref:`VIDIOC_QUERYCTRL`、:ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` 和 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 访问：

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - 结构体 ``video_picture``
      - V4L2 控制 ID
    * - ``brightness``
      - ``V4L2_CID_BRIGHTNESS``
    * - ``hue``
      - ``V4L2_CID_HUE``
    * - ``colour``
      - ``V4L2_CID_SATURATION``
    * - ``contrast``
      - ``V4L2_CID_CONTRAST``
    * - ``whiteness``
      - ``V4L2_CID_WHITENESS``

V4L 图像控制假定范围从 0 到 65535，没有特定的重置值。V4L2 API 允许任意的限制和默认值，可以通过 ioctl :ref:`VIDIOC_QUERYCTRL` 查询。关于控制的一般信息见 :ref:`control`。

视频图像的 `depth`（每像素平均位数）由选定的图像格式隐含。V4L2 假定应用程序能够识别格式并了解图像深度，其他应用程序则无需知道。`palette` 字段移到了结构体 :c:type:`v4l2_pix_format` 中：

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - 结构体 ``video_picture`` ``palette``
      - 结构体 :c:type:`v4l2_pix_format` ``pixfmt``
    * - ``VIDEO_PALETTE_GREY``
      - :ref:`V4L2_PIX_FMT_GREY <V4L2-PIX-FMT-GREY>`
    * - ``VIDEO_PALETTE_HI240``
      - :ref:`V4L2_PIX_FMT_HI240 <pixfmt-reserved>` [#f3]_
    * - ``VIDEO_PALETTE_RGB565``
      - :ref:`V4L2_PIX_FMT_RGB565 <pixfmt-rgb>`
    * - ``VIDEO_PALETTE_RGB555``
      - :ref:`V4L2_PIX_FMT_RGB555 <pixfmt-rgb>`
    * - ``VIDEO_PALETTE_RGB24``
      - :ref:`V4L2_PIX_FMT_BGR24 <pixfmt-rgb>`
    * - ``VIDEO_PALETTE_RGB32``
      - :ref:`V4L2_PIX_FMT_BGR32 <pixfmt-rgb>` [#f4]_
    * - ``VIDEO_PALETTE_YUV422``
      - :ref:`V4L2_PIX_FMT_YUYV <V4L2-PIX-FMT-YUYV>`
    * - ``VIDEO_PALETTE_YUYV``\  [#f5]_
      - :ref:`V4L2_PIX_FMT_YUYV <V4L2-PIX-FMT-YUYV>`
    * - ``VIDEO_PALETTE_UYVY``
      - :ref:`V4L2_PIX_FMT_UYVY <V4L2-PIX-FMT-UYVY>`
    * - ``VIDEO_PALETTE_YUV420``
      - None
    * - ``VIDEO_PALETTE_YUV411``
      - :ref:`V4L2_PIX_FMT_Y41P <V4L2-PIX-FMT-Y41P>` [#f6]_
    * - ``VIDEO_PALETTE_RAW``
      - None [#f7]_
    * - ``VIDEO_PALETTE_YUV422P``
      - :ref:`V4L2_PIX_FMT_YUV422P <V4L2-PIX-FMT-YUV422P>`
    * - ``VIDEO_PALETTE_YUV411P``
      - :ref:`V4L2_PIX_FMT_YUV411P <V4L2-PIX-FMT-YUV411P>` [#f8]_
    * - ``VIDEO_PALETTE_YUV420P``
      - :ref:`V4L2_PIX_FMT_YVU420 <V4L2-PIX-FMT-YVU420>`
    * - ``VIDEO_PALETTE_YUV410P``
      - :ref:`V4L2_PIX_FMT_YVU410 <V4L2-PIX-FMT-YVU410>`

V4L2 图像格式在 :ref:`pixfmt` 中定义。图像格式可以通过 ioctl :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 选择。

### 音频

`VIDIOCGAUDIO` 和 `VIDIOCSAUDIO` ioctl 以及结构体 `video_audio` 用于枚举 V4L 设备的音频输入。V4L2 相应的 ioctl 是 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` 和 :ref:`VIDIOC_S_AUDIO <VIDIOC_G_AUDIO>`，使用结构体 :c:type:`v4l2_audio`，详见 :ref:`audio`。
```plaintext
音频输入数量的“channel number”字段被重命名为“index”。

在“VIDIOCSAUDIO”中，“mode”字段选择“VIDEO_SOUND_MONO”、“VIDEO_SOUND_STEREO”、“VIDEO_SOUND_LANG1”或“VIDEO_SOUND_LANG2”中的一个音频解调模式。当当前音频标准为BTSC时，“VIDEO_SOUND_LANG2”指的是SAP，而“VIDEO_SOUND_LANG1”则无意义。此外，在V4L规范中未记录查询所选模式的方法。在“VIDIOCGAUDIO”中，驱动程序返回此字段中实际接收到的音频节目。在V4L2 API中，这些信息分别存储在结构:c:type:`v4l2_tuner`的“rxsubchans”和“audmode”字段中。有关调谐器的更多信息，请参见:ref:`tuner`。与音频模式相关的是，结构:c:type:`v4l2_audio`还报告了这是单声道还是立体声输入，无论其来源是否是调谐器。

以下字段已被V4L2控制取代，并可通过:ref:`VIDIOC_QUERYCTRL`、:ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>`和:ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl访问：

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - 结构``video_audio``
      - V4L2 控制 ID
    * - ``volume``
      - ``V4L2_CID_AUDIO_VOLUME``
    * - ``bass``
      - ``V4L2_CID_AUDIO_BASS``
    * - ``treble``
      - ``V4L2_CID_AUDIO_TREBLE``
    * - ``balance``
      - ``V4L2_CID_AUDIO_BALANCE``

为了确定哪些控制是由驱动程序支持的，V4L提供了标志“VIDEO_AUDIO_VOLUME”、“VIDEO_AUDIO_BASS”、“VIDEO_AUDIO_TREBLE”和“VIDEO_AUDIO_BALANCE”。在V4L2 API中，:ref:`VIDIOC_QUERYCTRL` ioctl报告相应的控制是否受支持。因此，“VIDEO_AUDIO_MUTABLE”和“VIDEO_AUDIO_MUTE”标志被布尔型的“V4L2_CID_AUDIO_MUTE”控制取代。
所有V4L2控制都有一个“step”属性，取代了结构``video_audio``的“step”字段。假设V4L音频控制的范围从0到65535，没有特定的重置值。V4L2 API允许任意的限制和默认值，这些可以通过:ref:`VIDIOC_QUERYCTRL` ioctl查询。有关控制的一般信息，请参阅:ref:`control`。

帧缓冲覆盖
===========

等效于“VIDIOCGFBUF”和“VIDIOCSFBUF”的V4L2 ioctl分别是:ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>`和:ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>`。结构``video_buffer``的“base”字段保持不变，除了V4L2定义了一个标志来表示非破坏性覆盖而不是“NULL”指针。其他所有字段都移到了结构:c:type:`v4l2_framebuffer`的结构:c:type:`v4l2_pix_format`“fmt”子结构中。“depth”字段被“pixelformat”取代。有关RGB格式及其相应颜色深度的列表，请参见:ref:`pixfmt-rgb`。

代替特殊的ioctl“VIDIOCGWIN”和“VIDIOCSWIN”，V4L2使用通用的数据格式协商ioctl:ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>`和:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`。它们接受指向结构:c:type:`v4l2_format`的指针作为参数。这里的“fmt”联合体成员“win”是一个结构:c:type:`v4l2_window`。

结构``video_window``的“x”、“y”、“width”和“height”字段移动到了结构:c:type:`v4l2_window`的结构:c:type:`v4l2_rect`子结构“w”中。“chromakey”、“clips”和“clipcount”字段保持不变。结构``video_clip``被重命名为结构:c:type:`v4l2_clip`，也包含一个结构:c:type:`v4l2_rect`，但语义仍然相同。

“VIDEO_WINDOW_INTERLACE”标志被删除。取而代之的是，应用程序必须将“field”字段设置为“V4L2_FIELD_ANY”或“V4L2_FIELD_INTERLACED”。“VIDEO_WINDOW_CHROMAKEY”标志移动到了结构:c:type:`v4l2_framebuffer`中，名称改为“V4L2_FBUF_FLAG_CHROMAKEY”。

在V4L中，在“clips”中存储位图指针并设置“clipcount”为“VIDEO_CLIP_BITMAP”（-1）请求使用固定大小位图（1024 × 625位）进行位图裁剪。结构:c:type:`v4l2_window`为此目的有一个单独的“bitmap”指针字段，位图大小由“w.width”和“w.height”决定。

启用或禁用覆盖的ioctl“VIDIOCCAPTURE”被重命名为:ref:`VIDIOC_OVERLAY`。
```
裁剪
========

为了捕获图像的子区域，V4L 定义了 `VIDIOCGCAPTURE` 和 `VIDIOCSCAPTURE` 这两个 ioctl，使用 `video_capture` 结构体。相应的 V4L2 ioctl 是 :ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` 和 :ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>`，使用结构体 :c:type:`v4l2_crop`，以及相关的 :ref:`VIDIOC_CROPCAP` ioctl。这是一个相当复杂的问题，请参见 :ref:`crop` 获取详细信息。`x`、`y`、`width` 和 `height` 字段移动到了结构体 :c:type:`v4l2_rect` 的子结构 `c` 中。`decimation` 字段被删除。在 V4L2 API 中，缩放因子由裁剪矩形的大小和捕获或覆盖图像的大小隐含表示。

`VIDEO_CAPTURE_ODD` 和 `VIDEO_CAPTURE_EVEN` 标志分别用于仅捕获奇数场或偶数场，它们被替换为 `V4L2_FIELD_TOP` 和 `V4L2_FIELD_BOTTOM`，位于结构体 :c:type:`v4l2_pix_format` 和 :c:type:`v4l2_window` 的 `field` 字段中。这些结构体用于通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 选择一个捕获或覆盖格式。

读取图像，内存映射
==============================

使用读方法进行捕获
-------------------------------

使用 :c:func:`read()` 函数从 V4L 或 V4L2 设备读取图像没有本质区别，但 V4L2 驱动程序不需要支持这种方法。应用程序可以通过 :ref:`VIDIOC_QUERYCAP` ioctl 确定该函数是否可用。所有与应用程序交换数据的 V4L2 设备必须支持 :c:func:`select()` 和 :c:func:`poll()` 函数。

为了选择图像格式和大小，V4L 提供了 `VIDIOCSPICT` 和 `VIDIOCSWIN` 这两个 ioctl。V4L2 使用通用的数据格式协商 ioctl :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`。它们接受指向结构体 :c:type:`v4l2_format` 的指针作为参数，在这里使用其 `fmt` 联合中的结构体 :c:type:`v4l2_pix_format`，命名为 `pix`。

有关 V4L2 读接口的更多信息，请参见 :ref:`rw`。

使用内存映射进行捕获
------------------------------

应用程序可以通过将设备内存中的缓冲区（通常是分配在可直接内存访问 (DMA) 的系统内存中的缓冲区）映射到它们的地址空间来读取 V4L 设备的内容。这避免了读方法带来的数据复制开销。V4L2 也支持内存映射，并且有一些不同之处。
.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - V4L
      - V4L2
    * -
      - 必须在分配缓冲区之前通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 选择图像格式。如果没有选择格式，驱动程序可能会使用上一次可能由其他应用程序请求的格式。
    * -
      - 应用程序不能更改缓冲区的数量。这是内置在驱动程序中的，除非在加载驱动程序模块时有一个模块选项来更改数量。
    * - :ref:`VIDIOC_REQBUFS` ioctl 分配所需数量的缓冲区，这是初始化序列中的必经步骤。
* 驱动程序将所有缓冲区映射为一个连续的内存范围。通过 `VIDIOCGMBUF` ioctl 可以查询缓冲区的数量、每个缓冲区相对于虚拟文件起始位置的偏移量以及总体使用的内存大小，这些信息可以作为 `mmap()` 函数的参数。
* 缓冲区单独映射。每个缓冲区的偏移量和大小可以通过 `VIDIOC_QUERYBUF` ioctl 来确定。
* `VIDIOCMCAPTURE` ioctl 用于准备一个缓冲区进行捕获，并确定该缓冲区的图像格式。ioctl 会立即返回，如果未检测到视频信号，则可能会返回 `EAGAIN` 错误代码。当驱动程序支持多个缓冲区时，应用程序可以多次调用此 ioctl，从而实现多个待处理的捕获请求。
* `VIDIOCSYNC` ioctl 会暂停执行，直到特定缓冲区被填满。
* 驱动程序维护输入队列和输出队列。 `VIDIOC_QBUF` ioctl 将任何空缓冲区加入输入队列。已填满的缓冲区则从输出队列中出队。为了等待已填满的缓冲区可用，可以使用 `select()` 或 `poll()` 函数。必须在加入一个或多个缓冲区之后调用 `VIDIOC_STREAMON` ioctl 以开始捕获。其对应操作 `VIDIOC_STREAMOFF` 会停止捕获并从两个队列中出队所有缓冲区。应用程序可以通过 `VIDIOC_ENUMINPUT` ioctl 查询信号状态（如果已知）。

对于内存映射的更深入讨论及示例，请参阅 `mmap`。

读取原始 VBI 数据
==================

最初，V4L API 并未规定原始 VBI 捕获接口，仅保留了设备文件 `/dev/vbi` 用于此目的。唯一支持此接口的驱动是 BTTV 驱动，实际上定义了 V4L VBI 接口。从该设备读取数据会产生具有以下参数的原始 VBI 图像：

.. flat-table::
    :header-rows:  1
    :stub-columns: 0

    * - 结构 :c:type:`v4l2_vbi_format`
      - V4L, BTTV 驱动
    * - sampling_rate
      - 28636363 Hz NTSC（或其他任何 525 行标准）；35468950 Hz PAL 和 SECAM（625 行标准）
    * - offset
      - ?
    * - samples_per_line
      - 2048
    * - sample_format
      - V4L2_PIX_FMT_GREY。最后四个字节（一个机器字节序整数）包含帧计数器
* - start[]
      - 10, 273 NTSC；22, 335 PAL 和 SECAM
    * - count[]
      - 16, 16 [#f9]_
    * - flags
      - 0

V4L 规格中未提及，在 Linux 2.3 中增加了使用结构 `vbi_format` 的 `VIDIOCGVBIFMT` 和 `VIDIOCSVBIFMT` ioctl 来确定 VBI 图像参数。这些 ioctl 与 `raw-vbi` 中指定的 V4L2 VBI 接口部分兼容。不存在 `offset` 字段，`sample_format` 应为 `VIDEO_PALETTE_RAW`，等同于 `V4L2_PIX_FMT_GREY`。其余字段可能等同于结构 :c:type:`v4l2_vbi_format`。
显然，只有 Zoran（ZR 36120）驱动程序实现了这些 ioctl。其语义在两个方面与 V4L2 规定的不同。参数在 `:c:func:`open()` 时被重置，并且如果参数无效，`VIDIOCSVBIFMT` 总是返回一个 `EINVAL` 错误代码。

杂项
=====

V4L2 没有与 `VIDIOCGUNIT` ioctl 相当的接口。应用程序可以通过重新打开设备并请求 VBI 数据来找到与视频捕获设备关联的 VBI 设备（反之亦然）。详情请参阅 :ref:`open`

没有 `VIDIOCKEY` 的替代品，也没有用于微码编程的 V4L 函数。关于 MPEG 压缩和播放设备的新接口，请参阅 :ref:`extended-controls`

.. [#f1]
   根据 Documentation/admin-guide/devices.rst，这些应该是指向 `/dev/video0` 的符号链接。注意原始的 bttv 接口不兼容 V4L 或 V4L2。

.. [#f2]
   根据 `Documentation/admin-guide/devices.rst`，这是指向 `/dev/radio0` 的符号链接。

.. [#f3]
   这是由 BTTV 驱动程序使用的自定义格式，不是 V4L2 标准格式之一。

.. [#f4]
   通常所有 V4L RGB 格式都是小端字节序的，尽管某些驱动程序可能会根据机器字节序进行解释。V4L2 定义了小端字节序、大端字节序和红蓝交换变体。详情请参阅 :ref:`pixfmt-rgb`。

.. [#f5]
   `VIDEO_PALETTE_YUV422` 和 `VIDEO_PALETTE_YUYV` 是相同的格式。一些 V4L 驱动程序响应其中一个，有些则响应另一个。

.. [#f6]
   不要将其与 `V4L2_PIX_FMT_YUV411P` 混淆，后者是一种平面格式。

.. [#f7]
   V4L 解释为：“RAW 捕获（BT848）”。

.. [#f8]
   不要将其与 `V4L2_PIX_FMT_Y41P` 混淆，后者是一种打包格式。
旧的驱动程序版本使用了不同的值，最终添加了自定义的 ``BTTV_VBISIZE`` ioctl 来查询正确的值。
