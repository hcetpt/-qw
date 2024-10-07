SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_TUNER:

************************************
ioctl VIDIOC_G_TUNER, VIDIOC_S_TUNER
************************************

名称
====

VIDIOC_G_TUNER - VIDIOC_S_TUNER - 获取或设置调谐器属性

概要
========

.. c:macro:: VIDIOC_G_TUNER

``int ioctl(int fd, VIDIOC_G_TUNER, struct v4l2_tuner *argp)``

.. c:macro:: VIDIOC_S_TUNER

``int ioctl(int fd, VIDIOC_S_TUNER, const struct v4l2_tuner *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_tuner` 的指针
描述
===========

为了查询调谐器的属性，应用程序需要初始化结构体 :c:type:`v4l2_tuner` 的 ``index`` 字段，并清零 ``reserved`` 数组，然后使用指向该结构体的指针调用 ``VIDIOC_G_TUNER`` ioctl。驱动程序会填充结构体的其余部分，或者在索引超出范围时返回一个 ``EINVAL`` 错误码。为了枚举所有调谐器，应用程序应从索引为零开始，每次递增一，直到驱动程序返回 ``EINVAL``。

调谐器有两个可写属性：音频模式和射频。为了改变音频模式，应用程序需要初始化 ``index``、``audmode`` 和 ``reserved`` 字段，并调用 ``VIDIOC_S_TUNER`` ioctl。这不会改变当前的调谐器，因为当前的调谐器是由当前视频输入决定的。如果请求的模式无效或不受支持，驱动程序可以选择不同的音频模式。由于这是一个只写 ioctl，因此它不会返回实际选择的音频模式。

:ref:`SDR <sdr>` 特定的调谐器类型是 ``V4L2_TUNER_SDR`` 和 ``V4L2_TUNER_RF``。对于 SDR 设备，``audmode`` 字段必须初始化为零。在这个上下文中，“调谐器”指的是 SDR 接收器。

为了改变射频，可以使用 :ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl。

.. tabularcolumns:: |p{1.3cm}|p{3.0cm}|p{7.0cm}|p{5.8cm}|

.. c:type:: v4l2_tuner

.. cssclass:: longtable

.. flat-table:: struct v4l2_tuner
    :header-rows:  0
    :stub-columns: 0

    * - __u32
      - ``index``
      - :cspan:`1` 标识调谐器，由应用程序设置
    * - __u8
      - ``name``[32]
      - :cspan:`1`

	调谐器的名称，一个以 NUL 结尾的 ASCII 字符串
此信息旨在供用户使用
* - `__u32`
  - `type`
  - :cspan:`1` 调谐器类型，参见 :c:type:`v4l2_tuner_type`

* - `__u32`
  - `capability`
  - :cspan:`1`

  调谐器功能标志，参见 :ref:`tuner-capability`。音频标志表示解码音频子节目的能力。这些标志不会因为当前视频标准的变化而改变。
  当结构体指的是一个无线电调谐器时，`V4L2_TUNER_CAP_LANG1`、`V4L2_TUNER_CAP_LANG2` 和 `V4L2_TUNER_CAP_NORM` 标志不能使用。
  如果支持多个频率带，则 `capability` 是所有 `v4l2_frequency_band` 结构体中 `capability` 字段的并集。

* - `__u32`
  - `rangelow`
  - :cspan:`1` 最低可调谐频率，单位为 62.5 kHz，或者如果设置了 `capability` 标志 `V4L2_TUNER_CAP_LOW`，则单位为 62.5 Hz，或者如果设置了 `capability` 标志 `V4L2_TUNER_CAP_1HZ`，则单位为 1 Hz。如果支持多个频率带，则 `rangelow` 是所有频率带中的最低频率。

* - `__u32`
  - `rangehigh`
  - :cspan:`1` 最高可调谐频率，单位为 62.5 kHz，或者如果设置了 `capability` 标志 `V4L2_TUNER_CAP_LOW`，则单位为 62.5 Hz，或者如果设置了 `capability` 标志 `V4L2_TUNER_CAP_1HZ`，则单位为 1 Hz。如果支持多个频率带，则 `rangehigh` 是所有频率带中的最高频率。

* - `__u32`
  - `rxsubchans`
  - :cspan:`1`

  某些调谐器或音频解码器可以通过分析音频载波、导频音或其他指示来确定接收到的音频子节目。为了传递这些信息，驱动程序会在该字段中设置 :ref:`tuner-rxsubchans` 中定义的标志。例如：
  * -
    -
    - `V4L2_TUNER_SUB_MONO`
    - 接收单声道音频
  * -
    -
    - `STEREO | SAP`
    - 接收立体声音频和次级音频节目
  * -
    -
    - `MONO | STEREO`
    - 接收单声道或立体声音频，硬件无法区分
  * -
    -
    - `LANG1 | LANG2`
    - 接收双语音频
  * -
    -
    - `MONO | STEREO | LANG1 | LANG2`
    - 接收单声道、立体声或双语音频
  * -
    -
    - :cspan:`1`

  当 `capability` 字段中未设置 `V4L2_TUNER_CAP_STEREO`、`_LANG1`、`_LANG2` 或 `_SAP` 标志时，相应的 `V4L2_TUNER_SUB_` 标志不应在此处设置。
  此字段仅在这是当前视频输入的调谐器或结构体指代的是一个无线电调谐器时有效。

* - `__u32`
  - `audmode`
  - :cspan:`1`

  选定的音频模式，参见 :ref:`tuner-audmode` 以获取有效的值。音频模式不影响音频子节目的检测，并且像一个 :ref:`control` 一样，除非请求的模式无效或不支持，否则不会自动改变。参见 :ref:`tuner-matrix` 以了解选定音频节目与接收音频节目不匹配时可能出现的结果。
  目前这是 `struct v4l2_tuner` 结构体中唯一可以由应用程序更改的字段。
* - `__u32`
      - `signal`
      - :cspan:`1` 如果已知，则为信号强度
范围从 0 到 65535。较高的值表示更好的信号。
* - `__s32`
      - `afc`
      - :cspan:`1` 自动频率控制
当 `afc` 值为负数时，频率过低；当为正数时，频率过高。
* - `__u32`
      - `reserved`[4]
      - :cspan:`1` 保留以供将来扩展
驱动程序和应用程序必须将数组设置为零。

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. c:type:: v4l2_tuner_type

.. flat-table:: 枚举 v4l2_tuner_type
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 6

    * - `V4L2_TUNER_RADIO`
      - 1
      - 调谐器支持广播。
    * - `V4L2_TUNER_ANALOG_TV`
      - 2
      - 调谐器支持模拟电视。
    * - `V4L2_TUNER_SDR`
      - 4
      - 调谐器控制软件定义无线电（SDR）的模数转换（A/D）和/或数模转换（D/A）模块。
    * - `V4L2_TUNER_RF`
      - 5
      - 调谐器控制软件定义无线电（SDR）的射频部分。

.. tabularcolumns:: |p{7.0cm}|p{2.2cm}|p{8.1cm}|

.. _tuner-capability:

.. cssclass:: longtable

.. flat-table:: 调谐器和调制器功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_TUNER_CAP_LOW`
      - 0x0001
      - 当设置时，调谐频率以 62.5 Hz 为单位表达，而不是 62.5 kHz。
    * - `V4L2_TUNER_CAP_NORM`
      - 0x0002
      - 这是一个多标准调谐器；视频标准可以或必须切换。（例如，B/G PAL 调谐器通常不被视为多标准调谐器，因为视频标准是根据频率带自动确定的。）此调谐器支持的视频标准集合可以从指向该调谐器的结构 :c:type:`v4l2_input` 中获得，详细信息请参阅 ioctl :ref:`VIDIOC_ENUMINPUT` 的描述。只有 `V4L2_TUNER_ANALOG_TV` 调谐器可以具备此功能。
    * - `V4L2_TUNER_CAP_HWSEEK_BOUNDED`
      - 0x0004
      - 如果设置，则此调谐器支持硬件搜索功能，在搜索到达频率范围的末端时停止。
    * - `V4L2_TUNER_CAP_HWSEEK_WRAP`
      - 0x0008
      - 如果设置，则此调谐器支持硬件搜索功能，在搜索到达频率范围的末端时循环返回。
* - ``V4L2_TUNER_CAP_STEREO``
      - 0x0010
      - 支持立体声音频接收
* - ``V4L2_TUNER_CAP_LANG1``
      - 0x0040
      - 支持双语音频节目的主要语言接收。双语音频是双通道系统的一项功能，主要音频载波上单声道传输主要语言，第二个载波上单声道传输次要语言。只有``V4L2_TUNER_ANALOG_TV``调谐器可以具备此功能。
* - ``V4L2_TUNER_CAP_LANG2``
      - 0x0020
      - 支持双语音频节目的次要语言接收。只有``V4L2_TUNER_ANALOG_TV``调谐器可以具备此功能。
* - ``V4L2_TUNER_CAP_SAP``
      - 0x0020
      - 支持辅助音频节目的接收。这是伴随NTSC视频标准的BTSC系统的一项功能。两个音频载波可用于主要语言的单声道或立体声传输，第三个独立载波用于次要语言的单声道传输。只有``V4L2_TUNER_ANALOG_TV``调谐器可以具备此功能。
.. note::

	   ``V4L2_TUNER_CAP_LANG2``和``V4L2_TUNER_CAP_SAP``标志是同义词。当调谐器支持``V4L2_STD_NTSC_M``视频标准时，适用``V4L2_TUNER_CAP_SAP``。
* - ``V4L2_TUNER_CAP_RDS``
      - 0x0080
      - 支持RDS捕获。此功能仅适用于无线电调谐器。
* - ``V4L2_TUNER_CAP_RDS_BLOCK_IO``
      - 0x0100
      - RDS数据作为未解析的RDS块传递。
* - ``V4L2_TUNER_CAP_RDS_CONTROLS``
      - 0x0200
      - 硬件解析RDS数据并通过控制设置。
* - ``V4L2_TUNER_CAP_FREQ_BANDS``
      - 0x0400
      - 可以使用:ref:`VIDIOC_ENUM_FREQ_BANDS` ioctl枚举可用的频率带。
* - ``V4L2_TUNER_CAP_HWSEEK_PROG_LIM``
  - 0x0800
  - 使用硬件寻道功能时可编程的搜索范围，请参阅
  :ref:`VIDIOC_S_HW_FREQ_SEEK` 获取详细信息
* - ``V4L2_TUNER_CAP_1HZ``
  - 0x1000
  - 设置后，调谐频率以 1 Hz 为单位表示，而不是 62.5 kHz

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _tuner-rxsubchans:

.. flat-table:: 调谐器音频接收标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_TUNER_SUB_MONO``
      - 0x0001
      - 调谐器接收单声道音频信号
* - ``V4L2_TUNER_SUB_STEREO``
      - 0x0002
      - 调谐器接收立体声音频信号
* - ``V4L2_TUNER_SUB_LANG1``
      - 0x0008
      - 调谐器接收双语音频信号的主要语言。当当前视频标准为 ``V4L2_STD_NTSC_M`` 时，驱动程序必须清除此标志
* - ``V4L2_TUNER_SUB_LANG2``
      - 0x0004
      - 调谐器接收双语音频信号的次要语言（或第二个音频节目）
* - ``V4L2_TUNER_SUB_SAP``
      - 0x0004
      - 调谐器接收第二个音频节目
.. note::

	   ``V4L2_TUNER_SUB_LANG2`` 和 ``V4L2_TUNER_SUB_SAP`` 标志是同义词。当当前视频标准为 ``V4L2_STD_NTSC_M`` 时，适用 ``V4L2_TUNER_SUB_SAP`` 标志
* - ``V4L2_TUNER_SUB_RDS``
      - 0x0010
      - 调谐器接收 RDS 信道

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _tuner-audmode:

.. flat-table:: 调谐器音频模式
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_TUNER_MODE_MONO``
      - 0
      - 播放单声道音频。当调谐器接收到立体声信号时，这是左右声道的降混音。当调谐器接收到双语或 SAP 信号时，此模式选择主要语言
* - ``V4L2_TUNER_MODE_STEREO``
      - 1
      - 播放立体声音频。当调谐器接收到双语音频时，可能会在左右声道播放不同的语言，或者在两个声道上播放主要语言。
在这种模式下播放不同语言的做法已被弃用。新的驱动程序应仅在 ``MODE_LANG1_LANG2`` 模式中执行此操作。
当调谐器接收不到立体声信号或不支持立体声接收时，驱动程序应回退到 ``MODE_MONO`` 模式。
* - ``V4L2_TUNER_MODE_LANG1``
      - 3
      - 播放主要语言，单声道或立体声。只有 ``V4L2_TUNER_ANALOG_TV`` 调谐器支持此模式。
* - ``V4L2_TUNER_MODE_LANG2``
      - 2
      - 播放次要语言，单声道。当调谐器接收到的不是双语音频或辅助音频（SAP），或不支持其接收时，驱动程序应回退到单声道或立体声模式。只有 ``V4L2_TUNER_ANALOG_TV`` 调谐器支持此模式。
* - ``V4L2_TUNER_MODE_SAP``
      - 2
      - 播放第二音频节目（Second Audio Program）。当调谐器接收到的不是双语音频或辅助音频（SAP），或不支持其接收时，驱动程序应回退到单声道或立体声模式。只有 ``V4L2_TUNER_ANALOG_TV`` 调谐器支持此模式。
.. note:: ``V4L2_TUNER_MODE_LANG2`` 和 ``V4L2_TUNER_MODE_SAP`` 是同义词。
* - ``V4L2_TUNER_MODE_LANG1_LANG2``
      - 4
      - 在左声道播放主要语言，在右声道播放次要语言。当调谐器接收到的不是双语音频或辅助音频（SAP）时，应回退到 ``MODE_LANG1`` 或 ``MODE_MONO`` 模式。只有 ``V4L2_TUNER_ANALOG_TV`` 调谐器支持此模式。

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{1.5cm}|p{1.5cm}|p{2.9cm}|p{2.9cm}|p{2.9cm}|p{2.9cm}|

.. _tuner-matrix:

.. flat-table:: 调谐器音频矩阵
    :header-rows:  2
    :stub-columns: 0
    :widths: 7 7 14 14 14 14

    * -
      - :cspan:`4` 选定的 ``V4L2_TUNER_MODE_``
    * - 接收到的 ``V4L2_TUNER_SUB_``
      - ``MONO``
      - ``STEREO``
      - ``LANG1``
      - ``LANG2 = SAP``
      - ``LANG1_LANG2``\ [#f1]_
    * - ``MONO``
      - 单声道
      - 单声道/单声道
      - 单声道
      - 单声道
      - 单声道/单声道
    * - ``MONO | SAP``
      - 单声道
      - 单声道/单声道
      - 单声道
      - SAP
      - 单声道/SAP（首选）或单声道/单声道
    * - ``STEREO``
      - 左右混合
      - 左/右
      - 立体声 左/右（首选）或单声道 左右混合
      - 立体声 左/右（首选）或单声道 左右混合
      - 左/右（首选）或左右混合/左右混合
    * - ``STEREO | SAP``
      - 左右混合
      - 左/右
      - 立体声 左/右（首选）或单声道 左右混合
      - SAP
      - 左右混合/SAP（首选）或左/右或左右混合/左右混合
    * - ``LANG1 | LANG2``
      - 语言 1
      - 语言 1/语言 2（已弃用\ [#f2]_）或语言 1/语言 1
      - 语言 1
      - 语言 2
      - 语言 1/语言 2（首选）或语言 1/语言 1

.. raw:: latex

    \normalsize

返回值
======

成功时返回 0，失败时返回 -1，并且设置 ``errno`` 变量为相应的错误代码。通用错误代码描述参见 :ref:`通用错误代码 <gen-errors>` 章节
EINVAL
    结构 :c:type:`v4l2_tuner` 的 ``index`` 超出了范围
.. [#f1]
   此模式已在 Linux 2.6.17 中添加，可能不被旧版驱动程序支持。

.. [#f2]
   在 ``MODE_STEREO`` 模式下播放两种语言已被弃用。将来，驱动程序在此模式下应仅输出主要语言。
   应用程序应请求 ``MODE_LANG1_LANG2`` 来录制两种语言或立体声信号。
