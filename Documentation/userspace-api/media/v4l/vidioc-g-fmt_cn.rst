SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_FMT:

************************************************
ioctl VIDIOC_G_FMT, VIDIOC_S_FMT, VIDIOC_TRY_FMT
************************************************

名称
====

VIDIOC_G_FMT - VIDIOC_S_FMT - VIDIOC_TRY_FMT - 获取或设置数据格式，尝试一种格式

概要
====

.. c:macro:: VIDIOC_G_FMT

``int ioctl(int fd, VIDIOC_G_FMT, struct v4l2_format *argp)``

.. c:macro:: VIDIOC_S_FMT

``int ioctl(int fd, VIDIOC_S_FMT, struct v4l2_format *argp)``

.. c:macro:: VIDIOC_TRY_FMT

``int ioctl(int fd, VIDIOC_TRY_FMT, struct v4l2_format *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_format` 结构体的指针
描述
===========

这些 ioctl 用于协商驱动程序和应用程序之间交换的数据（通常是图像格式）格式。为了查询当前参数，应用程序将 :c:type:`v4l2_format` 结构体中的 `type` 字段设置为相应的缓冲区（流）类型。例如，视频捕获设备使用 `V4L2_BUF_TYPE_VIDEO_CAPTURE` 或 `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`。当应用程序通过指向该结构体的指针调用 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl 时，驱动程序会填充 `fmt` 联合中的相应成员。对于视频捕获设备，这将是 struct :c:type:`v4l2_pix_format` 的 `pix` 成员或 struct :c:type:`v4l2_pix_format_mplane` 的 `pix_mp` 成员。如果请求的缓冲区类型不受支持，驱动程序将返回 `EINVAL` 错误码。

为了更改当前格式参数，应用程序需要初始化 `type` 字段和 `fmt` 联合中相应成员的所有字段。详细信息请参阅 :ref:`devices` 中各种设备类型的文档。良好的做法是首先查询当前参数，并仅修改不适合应用程序的参数。当应用程序通过指向 :c:type:`v4l2_format` 结构体的指针调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 时，驱动程序会根据硬件能力检查并调整参数。除非 `type` 字段无效，否则驱动程序不应返回错误码。这是一种了解设备能力并接近应用程序和驱动程序都可接受的参数的方法。成功后，驱动程序可能会编程硬件、分配资源并总体上准备数据交换。最后，:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 将返回当前格式参数，就像 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 所做的那样。非常简单且不可变的设备甚至可以忽略所有输入并始终返回默认参数。然而，所有与应用程序交换数据的 V4L2 设备都必须实现 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl。当请求的缓冲区类型不受支持时，驱动程序在 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 尝试时返回 `EINVAL` 错误码。当 I/O 已经进行中或由于其他原因资源不可用时，驱动程序返回 `EBUSY` 错误码。

:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` ioctl 与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 类似，但有一个例外：它不会改变驱动程序状态。它可以在任何时候被调用，从不返回 `EBUSY`。此功能旨在协商参数，了解硬件限制，而无需禁用 I/O 或可能耗时的硬件准备工作。尽管强烈推荐，但驱动程序不需要实现此 ioctl。

:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` 返回的格式必须与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 对于相同的输入或输出返回的格式相同。

.. c:type:: v4l2_format

.. tabularcolumns::  |p{7.4cm}|p{4.4cm}|p{5.5cm}|

.. flat-table:: struct v4l2_format
    :header-rows:  0
    :stub-columns: 0

    * - __u32
      - ``type``
      - 数据流类型，参见 :c:type:`v4l2_buf_type`
* - union {
      - ``fmt``
    * - struct :c:type:`v4l2_pix_format`
      - ``pix``
      - 图像格式定义，参见 :ref:`pixfmt`，由视频捕获和输出设备使用
* - 结构体 :c:type:`v4l2_pix_format_mplane`
      - ``pix_mp``
      - 图像格式的定义，详见 :ref:`pixfmt`，用于支持 :ref:`多平面版本API<planar-apis>` 的视频采集和输出设备
* - 结构体 :c:type:`v4l2_window`
      - ``win``
      - 图像覆盖层的定义，详见 :ref:`overlay`，用于视频覆盖层设备
* - 结构体 :c:type:`v4l2_vbi_format`
      - ``vbi``
      - 原始VBI（垂直消隐区间）采集或输出参数。详细讨论见 :ref:`raw-vbi`。用于原始VBI采集和输出设备
* - 结构体 :c:type:`v4l2_sliced_vbi_format`
      - ``sliced``
      - 切片VBI采集或输出参数。详见 :ref:`sliced`。用于切片VBI采集和输出设备
* - 结构体 :c:type:`v4l2_sdr_format`
      - ``sdr``
      - 数据格式的定义，详见 :ref:`pixfmt`，用于SDR（软件定义无线电）采集和输出设备
* - 结构体 :c:type:`v4l2_meta_format`
      - ``meta``
      - 元数据格式的定义，详见 :ref:`meta-formats`，用于元数据采集设备
* - __u8
      - ``raw_data``\[200\]
      - 为将来扩展保留的位置标记
* - }
      -

返回值
======

成功时返回0，失败时返回-1，并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。
EINVAL
    结构体 :c:type:`v4l2_format` 的 ``type`` 字段无效或请求的缓冲区类型不被支持
EBUSY
    设备正忙且无法更改格式。这可能是因为设备正在流传输或已分配或排队到驱动程序的缓冲区。仅适用于 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`
当然，请提供你需要翻译的文本。
