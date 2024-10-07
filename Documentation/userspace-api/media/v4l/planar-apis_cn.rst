SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _planar-apis:

*****************************
单平面和多平面 API
*****************************

某些设备要求每个输入或输出视频帧的数据放置在不连续的内存缓冲区中。在这种情况下，一个视频帧需要使用多个内存地址来寻址，即每个“平面”一个指针。平面是当前帧的一个子缓冲区。关于此类格式的例子，请参见 :ref:`pixfmt`。
最初，V4L2 API 不支持多平面缓冲区，并引入了一系列扩展来处理它们。这些扩展构成了所谓的“多平面 API”。V4L2 API 的一些调用和结构根据是否使用单平面 API 或多平面 API 而有不同的解释。应用程序可以通过将其相应的缓冲类型传递给 ioctl 调用来选择使用其中之一。多平面缓冲类型的后缀带有 `_MPLANE` 字符串。有关可用多平面缓冲类型的列表，请参见枚举 :c:type:`v4l2_buf_type`。

多平面格式
====================

多平面 API 引入了新的多平面格式。这些格式使用了一组独立的 FourCC 代码。重要的是要区分多平面 API 和多平面格式。多平面 API 调用也可以处理所有单平面格式（只要它们是在多平面 API 结构中传递的），而单平面 API 不能处理多平面格式。

区分单平面和多平面 API 的调用
===========================================================

:ref:`VIDIOC_QUERYCAP <VIDIOC_QUERYCAP>`
    新增了两个额外的多平面功能。可以将它们与非多平面功能一起设置，以用于同时处理单平面和多平面格式的设备。
:ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>`，:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`，:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>`
    新增了描述多平面格式的结构：struct :c:type:`v4l2_pix_format_mplane` 和 struct :c:type:`v4l2_plane_pix_format`。
    驱动程序可以定义新的多平面格式，它们具有与现有单平面格式不同的 FourCC 代码。
:ref:`VIDIOC_QBUF <VIDIOC_QBUF>`，:ref:`VIDIOC_DQBUF <VIDIOC_QBUF>`，:ref:`VIDIOC_QUERYBUF <VIDIOC_QUERYBUF>`
    新增了一个描述平面的结构 :c:type:`v4l2_plane`。这种结构的数组通过新字段 `m.planes` 在 struct :c:type:`v4l2_buffer` 中传递。
:ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>`
    将按请求分配多平面缓冲区。
