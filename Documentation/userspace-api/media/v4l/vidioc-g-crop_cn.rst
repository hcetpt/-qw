SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_CROP:

**********************************
ioctl VIDIOC_G_CROP, VIDIOC_S_CROP
**********************************

名称
====

VIDIOC_G_CROP - VIDIOC_S_CROP - 获取或设置当前裁剪矩形

概述
========

.. c:macro:: VIDIOC_G_CROP

``int ioctl(int fd, VIDIOC_G_CROP, struct v4l2_crop *argp)``

.. c:macro:: VIDIOC_S_CROP

``int ioctl(int fd, VIDIOC_S_CROP, const struct v4l2_crop *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 struct :c:type:`v4l2_crop` 的指针
描述
===========

为了查询裁剪矩形的大小和位置，应用程序将一个 struct :c:type:`v4l2_crop` 结构中的 ``type`` 字段设置为相应的缓冲区（流）类型，并使用指向该结构的指针调用 :ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` ioctl。驱动程序会填充结构的其余部分，或者如果裁剪不被支持则返回 ``EINVAL`` 错误代码。

为了更改裁剪矩形，应用程序需要初始化 struct :c:type:`v4l2_crop` 中的 ``type`` 和名为 ``c`` 的子结构体 :c:type:`v4l2_rect`，并使用指向该结构的指针调用 :ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` ioctl。
驱动程序首先根据硬件限制调整请求的尺寸，即由捕获/输出窗口给出的边界，并将其四舍五入到最接近的水平和垂直偏移、宽度和高度的可能值。特别是，驱动程序必须将裁剪矩形的垂直偏移量四舍五入到帧行模数二的位置，以防止场序混乱。
其次，驱动程序根据保持当前水平和垂直缩放因子的同时调整图像大小（缩放过程的相反矩形，取决于数据方向，是源还是目标）到最接近的可能大小。
最后，驱动程序使用实际的裁剪和图像参数编程硬件。:ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` 是只写 ioctl，不会返回实际参数。为了查询这些参数，应用程序必须调用 :ref:`VIDIOC_G_CROP <VIDIOC_G_CROP>` 和 :ref:`VIDIOC_G_FMT`。当参数不合适时，应用程序可以修改裁剪或图像参数并重复这个循环直到协商出满意的参数为止。
如果裁剪不被支持，则不改变任何参数，:ref:`VIDIOC_S_CROP <VIDIOC_G_CROP>` 返回 ``EINVAL`` 错误代码。
.. c:type:: v4l2_crop

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_crop
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 数据流的类型，由应用程序设置。只有以下类型在此处有效：``V4L2_BUF_TYPE_VIDEO_CAPTURE``, ``V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE``,
	``V4L2_BUF_TYPE_VIDEO_OUTPUT``, ``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`` 和
	``V4L2_BUF_TYPE_VIDEO_OVERLAY``。参见 :c:type:`v4l2_buf_type` 和下面的注释
* - struct :c:type:`v4l2_rect`
      - ``c``
      - 裁剪矩形。使用的坐标系统与 struct :c:type:`v4l2_cropcap` ``bounds`` 相同
.. 注意::
   对于多平面缓冲区类型（``V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`` 和 ``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE``）
   此API在如何填充 :c:type:`v4l2_crop` 的 ``type`` 字段方面存在混乱。一些驱动程序只接受带有 ``_MPLANE`` 的缓冲区类型，
   而其他驱动程序只接受非多平面的缓冲区类型（即不带 ``_MPLANE`` 的）。

从内核 4.13 开始，两种变体都被允许。

返回值
======

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

ENODATA
    此输入或输出不支持裁剪操作。
