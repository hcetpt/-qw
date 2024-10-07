SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_JPEGCOMP:

******************************************
ioctl VIDIOC_G_JPEGCOMP, VIDIOC_S_JPEGCOMP
******************************************

名称
====

VIDIOC_G_JPEGCOMP - VIDIOC_S_JPEGCOMP

概要
========

.. c:macro:: VIDIOC_G_JPEGCOMP

``int ioctl(int fd, VIDIOC_G_JPEGCOMP, v4l2_jpegcompression *argp)``

.. c:macro:: VIDIOC_S_JPEGCOMP

``int ioctl(int fd, VIDIOC_S_JPEGCOMP, const v4l2_jpegcompression *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_jpegcompression` 的指针
描述
===========

这些 ioctl 已经**废弃**。新的驱动程序和应用程序应使用 :ref:`JPEG 类控件 <jpeg-controls>` 来控制图像质量和 JPEG 标记。

Ronald Bultje 进一步解释道：

APP 是一些应用程序特定的信息。应用程序可以自行设置它，并且它将存储在 JPEG 编码字段中（例如，在 AVI 中的交织信息）。COM 也是类似的，但它是指注释，如“由我编码”等。
`jpeg_markers` 描述了是否应该将霍夫曼表、量化表以及重启间隔信息（所有这些是 JPEG 特定的内容）存储在 JPEG 编码字段中。这些定义了 JPEG 字段是如何编码的。如果你省略它们，应用程序会假定你使用的是标准编码。通常你确实希望添加它们。
.. tabularcolumns:: |p{1.2cm}|p{3.0cm}|p{13.1cm}|

.. c:type:: v4l2_jpegcompression

.. flat-table:: 结构体 v4l2_jpegcompression
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - int
      - ``quality``
      - 废弃。如果驱动程序暴露了 :ref:`V4L2_CID_JPEG_COMPRESSION_QUALITY <jpeg-quality-control>` 控件，则应用程序应使用该控件并忽略此字段
    * - int
      - ``APPn``
      -
    * - int
      - ``APP_len``
      -
    * - char
      - ``APP_data``\[60\]
      -
    * - int
      - ``COM_len``
      -
    * - char
      - ``COM_data``\[60\]
      -
    * - __u32
      - ``jpeg_markers``
      - 参见 :ref:`jpeg-markers`。废弃。如果驱动程序暴露了 :ref:`V4L2_CID_JPEG_ACTIVE_MARKER <jpeg-active-marker-control>` 控件，则应用程序应使用该控件并忽略此字段
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _jpeg-markers:

.. flat-table:: JPEG 标记标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_JPEG_MARKER_DHT``
      - (1<<3)
      - 定义霍夫曼表
    * - ``V4L2_JPEG_MARKER_DQT``
      - (1<<4)
      - 定义量化表
    * - ``V4L2_JPEG_MARKER_DRI``
      - (1<<5)
      - 定义重启间隔
    * - ``V4L2_JPEG_MARKER_COM``
      - (1<<6)
      - 注释段
    * - ``V4L2_JPEG_MARKER_APP``
      - (1<<7)
      - 应用段，驱动程序将始终使用 APP0

返回值
============

成功时返回 0，失败时返回 -1 并且设置 `errno` 变量以指示错误原因。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。
