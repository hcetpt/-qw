SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_CROPCAP:

********************
ioctl VIDIOC_CROPCAP
********************

名称
====

VIDIOC_CROPCAP - 获取视频裁剪和缩放能力的信息

概览
========

.. c:macro:: VIDIOC_CROPCAP

``int ioctl(int fd, VIDIOC_CROPCAP, struct v4l2_cropcap *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_cropcap` 结构体的指针
描述
===========

应用程序使用此函数查询裁剪限制、图像的像素宽高比以及计算缩放因子。它们将 v4l2_cropcap 结构体中的 ``type`` 字段设置为相应的缓冲区（流）类型，并用指向该结构体的指针调用 :ref:`VIDIOC_CROPCAP` ioctl。驱动程序填充结构体的其余部分。结果是恒定的，除非切换视频标准。记住这种切换可能在切换视频输入或输出时隐式发生。
此 ioctl 必须在支持裁剪和/或缩放和/或具有非方形像素的视频捕获或输出设备中实现，并且对于覆盖层设备也是如此。

.. c:type:: v4l2_cropcap

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_cropcap
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 数据流的类型，由应用程序设置。这里只有以下类型有效：``V4L2_BUF_TYPE_VIDEO_CAPTURE``、``V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE``、``V4L2_BUF_TYPE_VIDEO_OUTPUT``、``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`` 和 ``V4L2_BUF_TYPE_VIDEO_OVERLAY``。参见 :c:type:`v4l2_buf_type` 和下面的注释
* - struct :ref:`v4l2_rect <v4l2-rect-crop>`
      - ``bounds``
      - 定义了捕获或输出可能发生的窗口，例如这可能排除水平和垂直消隐区域。裁剪矩形不能超过这些限制。宽度和高度以像素定义，驱动程序编写者可以在模拟域中自由选择坐标系的原点和单位
* - struct :ref:`v4l2_rect <v4l2-rect-crop>`
      - ``defrect``
      - 默认裁剪矩形，应当覆盖“整个画面”。假设像素宽高比为 1/1，这可以是一个 640 × 480 的矩形用于 NTSC，一个 768 × 576 的矩形用于 PAL 和 SECAM，并且居中于活动画面区域。使用的坐标系与 ``bounds`` 相同
* - struct :c:type:`v4l2_fract`
      - ``pixelaspect``
      - 当没有应用缩放时的像素宽高比（y / x），实际采样频率与获得方形像素所需的频率之比
当裁剪坐标指的是方形像素时，驱动程序将 ``pixelaspect`` 设置为 1/1。其他常见值有 PAL 和 SECAM 的 54/59，NTSC 的 11/10，根据[:ref:`itu601`]进行采样
.. 注意::
   对于多平面缓冲类型（``V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`` 和 ``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE``）
   此API在如何填充 :c:type:`v4l2_cropcap` 的 ``type`` 字段方面存在混乱。一些驱动程序只接受带 ``_MPLANE`` 的缓冲类型，
   而其他驱动程序只接受非多平面缓冲类型（即不带 ``_MPLANE`` 的类型）。

从内核4.13开始，两种变体都被允许。
.. _v4l2-rect-crop:

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 v4l2_rect
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s32
      - ``left``
      - 矩形左上角的水平偏移量（以像素为单位）
* - __s32
      - ``top``
      - 矩形左上角的垂直偏移量（以像素为单位）
* - __u32
      - ``width``
      - 矩形的宽度（以像素为单位）
* - __u32
      - ``height``
      - 矩形的高度（以像素为单位）

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在
:ref:`通用错误码 <gen-errors>` 章节中描述。
EINVAL
    结构体 :c:type:`v4l2_cropcap` 的 ``type`` 无效
ENODATA
    此输入或输出不支持裁剪
