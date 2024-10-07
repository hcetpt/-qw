SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_FBUF:

**********************************
ioctl VIDIOC_G_FBUF, VIDIOC_S_FBUF
**********************************

名称
====

VIDIOC_G_FBUF - VIDIOC_S_FBUF - 获取或设置帧缓冲区覆盖参数

概述
========

.. c:macro:: VIDIOC_G_FBUF

``int ioctl(int fd, VIDIOC_G_FBUF, struct v4l2_framebuffer *argp)``

.. c:macro:: VIDIOC_S_FBUF

``int ioctl(int fd, VIDIOC_S_FBUF, const struct v4l2_framebuffer *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_framebuffer` 的指针

描述
===========

应用程序可以使用 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>` 和 :ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>` ioctl 来获取和设置
:ref:`Video Overlay <overlay>` 或 :ref:`Video Output Overlay <osd>` (OSD) 的帧缓冲区参数。覆盖类型由设备类型（捕获或输出设备）隐含，并且可以通过 :ref:`VIDIOC_QUERYCAP` ioctl 确定。一个 ``/dev/videoN`` 设备不应同时支持两种类型的覆盖。
V4L2 API 区分破坏性和非破坏性覆盖。破坏性覆盖将捕获的视频图像复制到图形卡的视频内存中。非破坏性覆盖将视频图像混合到 VGA 信号或图形到视频信号中。*Video Output Overlays* 总是非破坏性的。
破坏性覆盖支持已被移除：现代 GPU 和 CPU 已不再需要这种功能，而且它一直是一个非常危险的功能。
为了获取当前参数，应用程序通过指向结构体 :c:type:`v4l2_framebuffer` 的指针调用 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>` ioctl。驱动程序会填充该结构体的所有字段，或者在不支持覆盖时返回 EINVAL 错误代码。
为了设置 *Video Output Overlay* 的参数，应用程序必须初始化结构体 :c:type:`v4l2_framebuffer` 的 ``flags`` 字段。由于帧缓冲区是在电视卡上实现的，因此所有其他参数都由驱动程序确定。当应用程序使用指向此结构体的指针调用 :ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>` 时，驱动程序会为覆盖做准备，并像 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>` 一样返回帧缓冲区参数，或者返回错误代码。
为了设置 *Video Capture Overlay* 的参数，应用程序必须初始化 ``flags`` 字段、``fmt`` 子结构，并调用 :ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>`。同样地，驱动程序会为覆盖做准备，并像 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>` 一样返回帧缓冲区参数，或者返回错误代码。

.. tabularcolumns:: |p{3.5cm}|p{3.5cm}|p{3.5cm}|p{6.6cm}|

.. c:type:: v4l2_framebuffer

.. cssclass:: longtable

.. flat-table:: struct v4l2_framebuffer
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 1 2

    * - __u32
      - ``capability``
      -
      - 驱动程序设置的覆盖能力标志，参见 :ref:`framebuffer-cap`
    * - __u32
      - ``flags``
      -
      - 应用程序和驱动程序设置的覆盖控制标志，参见 :ref:`framebuffer-flags`
    * - void *
      - ``base``
      -
      - 帧缓冲区的物理基地址，即帧缓冲区左上角像素的地址
对于 :ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>`，此字段不再受支持，并且内核将始终将其设置为 NULL。

对于 *视频输出覆盖层*，驱动程序将返回一个有效的基地址，以便应用程序可以找到对应的 Linux 帧缓冲设备（参见 :ref:`osd`）。对于 *视频捕获覆盖层*，此字段将始终为 NULL。

* - 结构
      - ``fmt``
      -
      - 帧缓冲的布局
* -
      - __u32
      - ``width``
      - 像素宽度
* -
      - __u32
      - ``height``
      - 像素高度
* -
      - __u32
      - ``pixelformat``
      - 帧缓冲的像素格式
* -
      -
      -
      - 对于 *非破坏性视频覆盖层*，此字段仅定义了结构 :c:type:`v4l2_window` 的 ``chromakey`` 字段的格式
* -
      -
      -
      - 对于 *视频输出覆盖层*，驱动程序必须返回一个有效的格式
* -
      -
      -
      - 通常这是一个 RGB 格式（例如 :ref:`V4L2_PIX_FMT_RGB565 <V4L2-PIX-FMT-RGB565>`），但也允许 YUV 格式（仅当使用色键时才允许打包的 YUV 格式，不包括 ``V4L2_PIX_FMT_YUYV`` 和 ``V4L2_PIX_FMT_UYVY``）和 ``V4L2_PIX_FMT_PAL8`` 格式。当应用程序请求压缩格式时，驱动程序的行为是未定义的。有关像素格式的信息，请参阅 :ref:`pixfmt`
* -
      - 枚举 :c:type:`v4l2_field`
      - ``field``
      - 驱动程序和应用程序应忽略此字段。如果适用，可以通过使用结构 :c:type:`v4l2_window` 的 ``field`` 字段和 ioctl :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 来选择场顺序。
* -
      - __u32
      - ``bytesperline``
      - 两行相邻像素最左侧之间的字节距离
* - :cspan:`3`

    此字段对于*非破坏性视频覆盖*无关
对于*视频输出覆盖*，驱动程序必须返回一个有效值
视频硬件可能会访问填充字节，因此它们必须位于可访问的内存中。例如，在图像的最后一行之后的填充字节跨越系统页边界的情况。捕获设备可能会写入填充字节，其值是未定义的。输出设备忽略填充字节的内容
当图像格式为平面时，``bytesperline`` 值适用于第一个平面，并且对于其他平面按与 ``width`` 字段相同的因子进行划分。例如，YUV 4:2:0 图像的 Cb 和 Cr 平面每行后面的填充字节数量是 Y 平面的一半。为了避免歧义，驱动程序必须返回一个向上取整到比例因子倍数的 ``bytesperline`` 值
* -
      - __u32
      - ``sizeimage``
      - 此字段对于*非破坏性视频覆盖*无关
对于*视频输出覆盖*，驱动程序必须返回一个有效的格式
与 ``base`` 一起，定义了驱动程序可访问的帧缓冲区内存
* -
      - enum :c:type:`v4l2_colorspace`
      - ``colorspace``
      - 此信息补充了 ``pixelformat``，并且必须由驱动程序设置，参见 :ref:`colorspaces`
* -
      - __u32
      - ``priv``
      - 预留。驱动程序和应用程序必须将此字段设为零
```markdown
.. tabularcolumns:: |p{7.4cm}|p{1.6cm}|p{8.3cm}|

.. _framebuffer-cap:

.. flat-table:: 帧缓冲区功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_FBUF_CAP_EXTERNOVERLAY``
      - 0x0001
      - 设备支持非破坏性覆盖。当驱动程序清除此标志时，仅支持破坏性覆盖。目前还没有同时支持破坏性和非破坏性覆盖的驱动程序。实际上，视频输出覆盖总是非破坏性的。
* - ``V4L2_FBUF_CAP_CHROMAKEY``
      - 0x0002
      - 设备支持通过色键裁剪图像。也就是说，只有在VGA或视频信号呈现特定颜色时，图像像素才会替换这些像素。对于破坏性覆盖，色键没有意义。
* - ``V4L2_FBUF_CAP_LIST_CLIPPING``
      - 0x0004
      - 设备支持使用裁剪矩形列表进行裁剪。请注意，这已不再受支持。
* - ``V4L2_FBUF_CAP_BITMAP_CLIPPING``
      - 0x0008
      - 设备支持使用位掩码进行裁剪。请注意，这已不再受支持。
* - ``V4L2_FBUF_CAP_LOCAL_ALPHA``
      - 0x0010
      - 设备支持使用帧缓冲区或VGA信号的alpha通道进行裁剪/混合。对于破坏性覆盖，alpha混合没有意义。
* - ``V4L2_FBUF_CAP_GLOBAL_ALPHA``
      - 0x0020
      - 设备支持使用全局alpha值进行alpha混合。对于破坏性覆盖，alpha混合没有意义。
* - ``V4L2_FBUF_CAP_LOCAL_INV_ALPHA``
      - 0x0040
      - 设备支持使用帧缓冲区或VGA信号的反转alpha通道进行裁剪/混合。对于破坏性覆盖，alpha混合没有意义。
```
* - ``V4L2_FBUF_CAP_SRC_CHROMAKEY``
  - 0x0080
  - 设备支持源色键。具有色键颜色的视频像素将被帧缓冲区像素替换，这与 ``V4L2_FBUF_CAP_CHROMAKEY`` 恰好相反。

.. tabularcolumns:: |p{7.4cm}|p{1.6cm}|p{8.3cm}|

.. _framebuffer-flags:

.. cssclass:: longtable

.. flat-table:: 帧缓冲标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_FBUF_FLAG_PRIMARY``
      - 0x0001
      - 帧缓冲是主要的图形表面。换句话说，覆盖是破坏性的。通常，任何不具备 ``V4L2_FBUF_CAP_EXTERNOVERLAY`` 能力的驱动程序都会设置此标志，否则会清除该标志。
* - ``V4L2_FBUF_FLAG_OVERLAY``
      - 0x0002
      - 如果为视频捕获设备设置了此标志，则驱动程序将初始覆盖大小设置为覆盖整个帧缓冲大小，否则使用现有的覆盖大小（由 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 设置）。只有 bttv 视频捕获驱动程序支持此标志。对于捕获设备使用此标志已被弃用。无法检测哪些驱动程序支持此标志，因此设置覆盖大小的唯一可靠方法是通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`。如果为视频输出设备设置了此标志，则视频输出覆盖窗口相对于帧缓冲区的左上角，并且受帧缓冲区大小限制。如果未设置此标志，则视频输出覆盖窗口相对于视频输出显示。
* - ``V4L2_FBUF_FLAG_CHROMAKEY``
      - 0x0004
      - 使用色键。色键颜色由结构 :c:type:`v4l2_window` 中的 ``chromakey`` 字段确定，并通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 协商，详见 :ref:`overlay` 和 :ref:`osd`。
* - :cspan:`2` 没有标志来启用使用剪辑矩形列表或位图进行裁剪。这些方法通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 协商，详见 :ref:`overlay` 和 :ref:`osd`。
* - ``V4L2_FBUF_FLAG_LOCAL_ALPHA``
      - 0x0008
      - 使用帧缓冲区的 Alpha 通道对帧缓冲区像素和视频图像进行裁剪或混合。混合函数为：output = framebuffer pixel * alpha + video pixel * (1 - alpha)。实际的 Alpha 深度取决于帧缓冲区像素格式。
* - ``V4L2_FBUF_FLAG_GLOBAL_ALPHA``
      - 0x0010
      - 使用全局 Alpha 值将帧缓冲区与视频图像混合。混合函数为：output = (framebuffer pixel * alpha + video pixel * (255 - alpha)) / 255。Alpha 值由结构 :c:type:`v4l2_window` 中的 ``global_alpha`` 字段确定，并通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 协商，详见 :ref:`overlay` 和 :ref:`osd`。
* - ``V4L2_FBUF_FLAG_LOCAL_INV_ALPHA``
      - 0x0020
      - 类似于 ``V4L2_FBUF_FLAG_LOCAL_ALPHA``，使用帧缓冲区的 Alpha 通道对帧缓冲区像素和视频图像进行裁剪或混合，但使用反转的 Alpha 值。混合函数为：output = framebuffer pixel * (1 - alpha) + video pixel * alpha。实际的 Alpha 深度取决于帧缓冲区像素格式。
* - ``V4L2_FBUF_FLAG_SRC_CHROMAKEY``
      - 0x0040
      - 使用源色键。源色键颜色由结构 :c:type:`v4l2_window` 中的 ``chromakey`` 字段确定，并通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 协商，详见 :ref:`overlay` 和 :ref:`osd`。两种色键相互排斥，因此使用相同的 ``chromakey`` 字段。

返回值
======

成功时返回 0，出错时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EPERM
只有特权用户才能调用 :ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>` 来协商破坏性覆盖的参数。

EINVAL
:ref:`VIDIOC_S_FBUF <VIDIOC_G_FBUF>` 的参数不适用。
