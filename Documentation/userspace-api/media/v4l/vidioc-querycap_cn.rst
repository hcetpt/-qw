SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_QUERYCAP:

*********************
ioctl VIDIOC_QUERYCAP
*********************

名称
====

VIDIOC_QUERYCAP - 查询设备功能

概要
========

.. c:macro:: VIDIOC_QUERYCAP

``int ioctl(int fd, VIDIOC_QUERYCAP, struct v4l2_capability *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_capability` 的指针
描述
===========

所有 V4L2 设备都支持 `VIDIOC_QUERYCAP` ioctl。它用于识别与此规范兼容的内核设备，并获取有关驱动程序和硬件功能的信息。ioctl 需要一个指向 `struct v4l2_capability` 的指针，该指针由驱动程序填充。如果驱动程序不兼容此规范，则 ioctl 将返回 `EINVAL` 错误代码。
.. c:type:: v4l2_capability

.. tabularcolumns:: |p{1.4cm}|p{2.8cm}|p{13.1cm}|

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_capability
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 4 20

    * - __u8
      - ``driver``\ [16]
      - 驱动程序名称，一个唯一的 NUL 终止 ASCII 字符串。例如："bttv"。驱动程序特定的应用程序可以使用此信息来验证驱动程序的身份。它在处理已知错误或在错误报告中识别驱动程序时也非常有用。
        存储固定大小数组中的字符串是不好的做法，但在这里不可避免。驱动程序和应用程序应采取预防措施，以避免超出数组末尾进行读写，并确保字符串正确地以 NUL 终止。
    * - __u8
      - ``card``\ [32]
      - 设备名称，一个 NUL 终止的 UTF-8 字符串。例如："Yoyodyne TV/FM"。一个驱动程序可能支持不同品牌或型号的视频硬件。此信息旨在供用户使用，例如在一个可用设备菜单中。由于同一品牌的多个电视卡可能会被安装并由同一个驱动程序支持，因此这个名称应该与字符设备文件名（例如 `/dev/video2`）或 `bus_info` 字符串结合使用，以避免歧义。
    * - __u8
      - ``bus_info``\ [32]
      - 系统中设备的位置，一个 NUL 终止的 ASCII 字符串。例如："PCI:0000:05:06.0"。此信息旨在供用户使用，以便区分多个相同的设备。如果没有此类信息，则字段必须简单地计数由驱动程序控制的设备（如 "platform:vivid-000"）。`bus_info` 必须以 "PCI:" 开头表示 PCI 板卡，"PCIe:" 表示 PCI Express 板卡，"usb-" 表示 USB 设备，"I2C:" 表示 I2C 设备，"ISA:" 表示 ISA 设备，"parport" 表示并口设备，以及 "platform:" 表示平台设备。
    * - __u32
      - ``version``
      - 驱动程序版本号
从内核 3.1 开始，报告的版本号由 V4L2 子系统根据内核编号方案提供。然而，在某些情况下，例如稳定或经过发行版修改的内核使用了更新内核的 V4L2 栈时，它可能不会总是返回与内核相同的版本。
版本号格式化使用 `KERNEL_VERSION()` 宏。例如，如果媒体栈对应于内核 4.14 中发布的 V4L2 版本，它将等同于：
    * - :cspan:`2`

	``#define KERNEL_VERSION(a,b,c) (((a) << 16) + ((b) << 8) + (c))``

	``__u32 version = KERNEL_VERSION(4, 14, 0);``

	``printf ("Version: %u.%u.%u\n",``

	``(version >> 16) & 0xFF, (version >> 8) & 0xFF, version & 0xFF);``
    * - __u32
      - ``capabilities``
      - 整个物理设备的功能集合，参见 :ref:`device-capabilities`。同一个物理设备可以在 /dev 中导出多个设备（例如 /dev/videoX、/dev/vbiY 和 /dev/radioZ）。`capabilities` 字段应包含各个 V4L2 设备向用户空间导出的所有功能的并集。对于所有这些设备，`capabilities` 字段将返回相同的功能集合。这允许应用程序仅打开其中一个设备（通常是视频设备），并发现是否还支持视频、VBI 和/或无线电功能。
* - `__u32`
  - `device_caps`
  - 打开设备的设备功能，详见 :ref:`device-capabilities`。应包含该特定设备节点可用的功能。例如，一个射频设备的 `device_caps` 仅包含与射频相关的功能，而不包含视频或垂直消隐间隔 (VBI) 功能。只有在 `capabilities` 字段包含 `V4L2_CAP_DEVICE_CAPS` 功能时，才会设置此字段。只有 `capabilities` 字段可以具有 `V4L2_CAP_DEVICE_CAPS` 功能，`device_caps` 永远不会设置 `V4L2_CAP_DEVICE_CAPS`。
* - `__u32`
  - `reserved`\[3\]
  - 预留以供将来扩展使用。驱动程序必须将此数组设为零。

.. tabularcolumns:: |p{7.0cm}|p{2.6cm}|p{7.7cm}|

.. _device-capabilities:

.. cssclass:: longtable

.. flat-table:: 设备功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_CAP_VIDEO_CAPTURE`
      - 0x00000001
      - 设备支持通过 :ref:`Video Capture <capture>` 接口的单平面 API
    * - `V4L2_CAP_VIDEO_CAPTURE_MPLANE`
      - 0x00001000
      - 设备支持通过 :ref:`Video Capture <capture>` 接口的多平面 API (:ref:`planar-apis`)
    * - `V4L2_CAP_VIDEO_OUTPUT`
      - 0x00000002
      - 设备支持通过 :ref:`Video Output <output>` 接口的单平面 API
    * - `V4L2_CAP_VIDEO_OUTPUT_MPLANE`
      - 0x00002000
      - 设备支持通过 :ref:`Video Output <output>` 接口的多平面 API (:ref:`planar-apis`)
    * - `V4L2_CAP_VIDEO_M2M`
      - 0x00008000
      - 设备支持通过视频内存到内存接口的单平面 API
    * - `V4L2_CAP_VIDEO_M2M_MPLANE`
      - 0x00004000
      - 设备支持通过视频内存到内存接口的多平面 API (:ref:`planar-apis`)
    * - `V4L2_CAP_VIDEO_OVERLAY`
      - 0x00000004
      - 设备支持 :ref:`Video Overlay <overlay>` 接口。视频覆盖设备通常直接将捕获的图像存储在显卡的视频内存中，并且具备硬件裁剪和缩放功能
    * - `V4L2_CAP_VBI_CAPTURE`
      - 0x00000010
      - 设备支持 :ref:`Raw VBI Capture <raw-vbi>` 接口，提供 Teletext 和字幕数据
* - ``V4L2_CAP_VBI_OUTPUT``
      - 0x00000020
      - 设备支持 :ref:`原始垂直消隐间隔（VBI）输出 <raw-vbi>` 接口
* - ``V4L2_CAP_SLICED_VBI_CAPTURE``
      - 0x00000040
      - 设备支持 :ref:`分片 VBI 捕获 <sliced>` 接口
* - ``V4L2_CAP_SLICED_VBI_OUTPUT``
      - 0x00000080
      - 设备支持 :ref:`分片 VBI 输出 <sliced>` 接口
* - ``V4L2_CAP_RDS_CAPTURE``
      - 0x00000100
      - 设备支持 :ref:`RDS <rds>` 捕获接口
* - ``V4L2_CAP_VIDEO_OUTPUT_OVERLAY``
      - 0x00000200
      - 设备支持 :ref:`视频输出叠加 <osd>` （OSD）接口。与“视频叠加”接口不同，这是视频输出设备的次要功能，并在输出视频信号上叠加图像。当驱动程序设置此标志时，必须清除 ``V4L2_CAP_VIDEO_OVERLAY`` 标志，反之亦然。[#f1]_
* - ``V4L2_CAP_HW_FREQ_SEEK``
      - 0x00000400
      - 设备支持用于硬件频率搜索的 :ref:`VIDIOC_S_HW_FREQ_SEEK` ioctl
* - ``V4L2_CAP_RDS_OUTPUT``
      - 0x00000800
      - 设备支持 :ref:`RDS <rds>` 输出接口
* - ``V4L2_CAP_TUNER``
      - 0x00010000
      - 设备具有某种调谐器以接收射频调制的视频信号。有关调谐器编程的更多信息，请参阅 :ref:`调谐器`
* - ``V4L2_CAP_AUDIO``
      - 0x00020000
      - 设备具有音频输入或输出。它可能支持 PCM 或压缩格式的音频录制或播放。PCM 音频支持必须实现为 ALSA 或 OSS 接口。有关音频输入和输出的更多信息，请参阅 :ref:`音频`
* - ``V4L2_CAP_RADIO``
      - 0x00040000
      - 这是一个无线电接收器
* - ``V4L2_CAP_MODULATOR``
      - 0x00080000
      - 设备具有某种调制器以发射射频调制的视频/音频信号。有关调制器编程的更多信息，请参阅 :ref:`调谐器`
* - ``V4L2_CAP_SDR_CAPTURE``
      - 0x00100000
      - 设备支持 :ref:`SDR 捕获 <sdr>` 接口
* - ``V4L2_CAP_EXT_PIX_FORMAT``
      - 0x00200000
      - 设备支持结构体 :c:type:`v4l2_pix_format` 的扩展字段
* - ``V4L2_CAP_SDR_OUTPUT``
      - 0x00400000
      - 设备支持 :ref:`SDR 输出 <sdr>` 接口
* - ``V4L2_CAP_META_CAPTURE``
      - 0x00800000
      - 设备支持 :ref:`元数据` 捕获接口
* - ``V4L2_CAP_READWRITE``
      - 0x01000000
      - 设备支持 :c:func:`read()` 和/或 :c:func:`write()` I/O 方法
* - ``V4L2_CAP_STREAMING``
      - 0x04000000
      - 设备支持 :ref:`流式传输 <mmap>` I/O 方法
* - ``V4L2_CAP_META_OUTPUT``
      - 0x08000000
      - 设备支持 :ref:`元数据` 输出接口
* - ``V4L2_CAP_TOUCH``
      - 0x10000000
      - 这是一个触摸设备
* - ``V4L2_CAP_IO_MC``
      - 0x20000000
      - 从用户空间来看，只有一个输入和/或输出。整个视频拓扑配置（包括哪个 I/O 实体被路由到输入/输出）由用户空间通过 Media Controller 配置。参见 :ref:`media_controller`
* - ``V4L2_CAP_DEVICE_CAPS``
  - 0x80000000
  - 驱动程序填充 ``device_caps`` 字段。此功能只能出现在 ``capabilities`` 字段中，而不能出现在 ``device_caps`` 字段中。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。
.. [#f1]
   结构 :c:type:`v4l2_framebuffer` 缺少一个枚举类型 :c:type:`v4l2_buf_type` 的字段，因此覆盖类型由驱动程序的功能隐式决定。
