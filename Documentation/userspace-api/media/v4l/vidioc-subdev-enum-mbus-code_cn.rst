SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_ENUM_MBUS_CODE:

**********************************
ioctl VIDIOC_SUBDEV_ENUM_MBUS_CODE
**********************************

名称
====

VIDIOC_SUBDEV_ENUM_MBUS_CODE - 列出媒体总线格式

概要
========

.. c:macro:: VIDIOC_SUBDEV_ENUM_MBUS_CODE

``int ioctl(int fd, VIDIOC_SUBDEV_ENUM_MBUS_CODE, struct v4l2_subdev_mbus_code_enum * argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_mbus_code_enum` 的指针

描述
===========

此调用用于应用程序访问选定端口的媒体总线格式列表。
这些枚举由驱动程序定义，并使用结构体 :c:type:`v4l2_subdev_mbus_code_enum` 中的 ``index`` 字段进行索引。
每个枚举都从 ``index`` 为 0 开始，最低的无效索引标志着枚举的结束。
因此，为了枚举给定子设备端口上可用的媒体总线格式，
需要初始化 ``pad`` 和 ``which`` 字段为所需的值，并将 ``index`` 设置为 0。
然后通过指向该结构体的指针调用 :ref:`VIDIOC_SUBDEV_ENUM_MBUS_CODE` ioctl。
成功调用后，``code`` 字段会被填充为一个媒体总线代码值。
重复增加 ``index`` 直到收到 ``EINVAL`` 错误。
``EINVAL`` 表示 ``pad`` 无效或在此端口上没有更多的代码可用。
驾驶员在同一个pad的不同索引处不得返回相同的`code`值。

可用的媒体总线格式可能依赖于子设备其他端口上的当前“尝试”格式，以及当前活动的链接。
更多关于尝试格式的信息，请参阅 :ref:`VIDIOC_SUBDEV_G_FMT`。
.. c:type:: v4l2_subdev_mbus_code_enum

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 v4l2_subdev_mbus_code_enum
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pad``
      - 媒体控制器API报告的端口号。由应用程序填充。
* - __u32
      - ``index``
      - 属于给定端口的枚举中的媒体总线代码索引。由应用程序填充。
* - __u32
      - ``code``
      - 媒体总线格式代码，如 :ref:`v4l2-mbus-format` 中定义。由驱动程序填充。
* - __u32
      - ``which``
      - 要枚举的媒体总线格式代码，来自枚举 :ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - __u32
      - ``flags``
      - 请参阅 :ref:`v4l2-subdev-mbus-code-flags`
    * - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\[6\]
      - 为将来扩展保留。应用程序和驱动程序必须将数组设置为零。
.. raw:: latex

   \footnotesize

.. tabularcolumns:: |p{8.8cm}|p{2.2cm}|p{6.3cm}|

.. _v4l2-subdev-mbus-code-flags:

.. flat-table:: 子设备媒体总线编码枚举标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - V4L2_SUBDEV_MBUS_CODE_CSC_COLORSPACE
      - 0x00000001
      - 驱动程序允许应用程序尝试更改默认的颜色空间编码。应用程序可以在调用 ioctl :ref:`VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` 时设置 :ref:`V4L2_MBUS_FRAMEFMT_SET_CSC <mbus-framefmt-set-csc>` 来请求配置子设备的颜色空间。
参见 :ref:`v4l2-mbus-format` 了解如何执行此操作。
* - V4L2_SUBDEV_MBUS_CODE_CSC_XFER_FUNC
      - 0x00000002
      - 驱动程序允许应用程序尝试更改默认的变换函数。应用程序可以在调用 ioctl :ref:`VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` 时设置 :ref:`V4L2_MBUS_FRAMEFMT_SET_CSC <mbus-framefmt-set-csc>` 来请求配置子设备的变换函数。
参见 :ref:`v4l2-mbus-format` 了解如何执行此操作。
* - V4L2_SUBDEV_MBUS_CODE_CSC_YCBCR_ENC
      - 0x00000004
      - 驱动程序允许应用程序尝试更改默认的 Y'CbCr 编码。应用程序可以在调用 ioctl :ref:`VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` 时设置 :ref:`V4L2_MBUS_FRAMEFMT_SET_CSC <mbus-framefmt-set-csc>` 来请求配置子设备的 Y'CbCr 编码。
参见 :ref:`v4l2-mbus-format` 了解如何执行此操作。
* - V4L2_SUBDEV_MBUS_CODE_CSC_HSV_ENC
      - 0x00000004
      - 驱动程序允许应用程序尝试更改默认的 HSV 编码。应用程序可以在调用 ioctl :ref:`VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` 时设置 :ref:`V4L2_MBUS_FRAMEFMT_SET_CSC <mbus-framefmt-set-csc>` 来请求配置子设备的 HSV 编码。
参见 :ref:`v4l2-mbus-format` 了解如何执行此操作。
* - V4L2_SUBDEV_MBUS_CODE_CSC_QUANTIZATION
      - 0x00000008
      - 驱动程序允许应用程序尝试更改默认的量化。应用程序可以在调用 ioctl :ref:`VIDIOC_SUBDEV_S_FMT <VIDIOC_SUBDEV_G_FMT>` 时设置 :ref:`V4L2_MBUS_FRAMEFMT_SET_CSC <mbus-framefmt-set-csc>` 来请求配置子设备的量化。
参见 :ref:`v4l2-mbus-format` 了解如何执行此操作。
参见 :ref:`v4l2-mbus-format` 了解如何操作
.. raw:: latex

   \normalsize

返回值
======

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量为适当的错误代码。通用的错误代码在
:ref:`Generic Error Codes <gen-errors>` 章节中有描述。
EINVAL
    结构体 :c:type:`v4l2_subdev_mbus_code_enum` 中的 ``pad`` 引用了不存在的端口，或者 ``which`` 字段包含了一个不支持的值，或者 ``index`` 字段越界。
