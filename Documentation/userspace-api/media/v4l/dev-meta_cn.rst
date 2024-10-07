SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _metadata:

******************
元数据接口
******************

元数据指的是补充视频帧的任何非图像数据，这些数据提供了额外的信息。这可能包括在图像上计算的统计数据、图像源或设备提供的帧捕获参数，或者特定于设备的参数以指定设备如何处理图像。此接口旨在用于用户空间与硬件之间的元数据传输及控制该操作。

元数据接口实现在视频设备节点上。设备可以专门用于元数据，也可以根据其报告的功能同时支持视频和元数据。
查询功能
=====================

支持元数据捕获接口的设备节点会在通过 :c:func:`VIDIOC_QUERYCAP` ioctl 返回的 :c:type:`v4l2_capability` 结构体的 `device_caps` 字段中设置 `V4L2_CAP_META_CAPTURE` 标志。该标志表示设备可以将元数据捕获到内存中。类似地，支持元数据输出接口的设备节点会在 `device_caps` 字段中设置 `V4L2_CAP_META_OUTPUT` 标志。该标志表示设备可以从内存读取元数据。

至少需要支持一种读/写或流式输入/输出方法。
数据格式协商
=======================

元数据设备使用 :ref:`format` ioctl 来选择捕获格式。元数据缓冲区内容格式绑定到所选格式。除了基本的 :ref:`format` ioctl 外，还必须支持 :c:func:`VIDIOC_ENUM_FMT` ioctl。

为了使用 :ref:`format` ioctl，应用程序需要将 :c:type:`v4l2_format` 结构体的 `type` 字段设置为 `V4L2_BUF_TYPE_META_CAPTURE` 或 `V4L2_BUF_TYPE_META_OUTPUT`，并根据所需的操作使用 `fmt` 联合中的 :c:type:`v4l2_meta_format` 的 `meta` 成员。驱动程序和应用程序都必须将 :c:type:`v4l2_format` 结构体的其余部分设置为 0。

按行捕获元数据的设备在 :c:func:`VIDIOC_ENUM_FMT` 中设置了 `struct v4l2_fmtdesc` 的 `V4L2_FMT_FLAG_META_LINE_BASED` 标志。此类设备通常也可以 :ref:`捕获图像数据 <capture>`。这主要涉及从其他设备（如相机传感器）接收数据的设备。

.. c:type:: v4l2_meta_format

.. tabularcolumns:: |p{1.4cm}|p{2.4cm}|p{13.5cm}|

.. flat-table:: struct v4l2_meta_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``dataformat``
      - 数据格式，由应用程序设置。这是一个小端字节序的 :ref:`四个字符代码 <v4l2-fourcc>`。V4L2 在 :ref:`meta-formats` 中定义了元数据格式。
* - __u32
      - ``buffersize``
      - 所需数据的最大缓冲区大小（以字节为单位）。该值由驱动程序设置。
* - __u32
      - ``width``
      - 以数据单元为单位的一行元数据的宽度。当 `v4l2_fmtdesc` 结构体中的标志 `V4L2_FMT_FLAG_META_LINE_BASED` 被设置时有效，否则为零。参见 `VIDIOC_ENUM_FMT` 函数。
* - __u32
      - ``height``
      - 元数据的行数。当 `v4l2_fmtdesc` 结构体中的标志 `V4L2_FMT_FLAG_META_LINE_BASED` 被设置时有效，否则为零。参见 `VIDIOC_ENUM_FMT` 函数。
* - __u32
      - ``bytesperline``
      - 两行连续元数据之间的字节偏移量。当 `v4l2_fmtdesc` 结构体中的标志 `V4L2_FMT_FLAG_META_LINE_BASED` 被设置时有效，否则为零。参见 `VIDIOC_ENUM_FMT` 函数。
