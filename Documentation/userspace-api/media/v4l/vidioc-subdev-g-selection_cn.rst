.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_G_SELECTION:

**************************************************************************************************
ioctl VIDIOC_SUBDEV_G_SELECTION, VIDIOC_SUBDEV_S_SELECTION
**************************************************************************************************

名称
====

VIDIOC_SUBDEV_G_SELECTION - VIDIOC_SUBDEV_S_SELECTION - 获取或设置子设备端口上的选择矩形

概要
========

.. c:macro:: VIDIOC_SUBDEV_G_SELECTION

``int ioctl(int fd, VIDIOC_SUBDEV_G_SELECTION, struct v4l2_subdev_selection *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_SELECTION

``int ioctl(int fd, VIDIOC_SUBDEV_S_SELECTION, struct v4l2_subdev_selection *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_selection` 的指针

描述
===========

选择用于配置子设备执行的各种影响图像大小的图像处理功能。这目前包括裁剪、缩放和组合。选择 API 取代了 :ref:`旧的子设备裁剪 API <VIDIOC_SUBDEV_G_CROP>`。裁剪 API 的所有功能，以及更多功能，都由选择 API 支持。有关每个选择目标如何影响子设备内部图像处理管道的更多信息，请参见 :ref:`subdev`。
如果子设备节点是以只读模式注册的，则对 ``VIDIOC_SUBDEV_S_SELECTION`` 的调用仅在 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_TRY`` 时有效，否则将返回错误，并将 errno 变量设置为 ``-EPERM``。

选择目标类型
--------------------------

选择目标有两种类型：实际和边界。实际目标是配置硬件的目标。BOUNDS 目标将返回一个包含所有可能实际矩形的矩形。

发现支持的功能
------------------------------

为了发现哪些目标被支持，用户可以在这些目标上执行 ``VIDIOC_SUBDEV_G_SELECTION``。任何不支持的目标将返回 ``EINVAL``。

选择目标和标志在 :ref:`v4l2-selections-common` 中有详细说明。

.. c:type:: v4l2_subdev_selection

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_subdev_selection
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``which``
      - 活动选择或尝试选择，来自枚举 :ref:`v4l2_subdev_format_whence <v4l2-subdev-format-whence>`
* - __u32
      - ``pad``
      - 由媒体框架报告的填充编号
* - __u32
      - ``target``
      - 目标选择矩形。参见 :ref:`v4l2-selections-common`
* - __u32
      - ``flags``
      - 标志。参见 :ref:`v4l2-selection-flags`
* - struct :c:type:`v4l2_rect`
      - ``r``
      - 选择矩形，以像素为单位
* - __u32
      - ``stream``
      - 流标识符
* - __u32
      - ``reserved``\[7\]
      - 为将来扩展保留。应用程序和驱动程序必须将数组设置为零

返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EBUSY
    由于当前填充处于忙碌状态，无法更改选择矩形。例如，这可能是由于填充上的活动视频流导致的。在执行其他操作来解决问题之前不应重试此 ioctl。仅由 ``VIDIOC_SUBDEV_S_SELECTION`` 返回。

EINVAL
    结构 :c:type:`v4l2_subdev_selection` 的 ``pad`` 引用了一个不存在的填充，或者 ``which`` 字段具有不受支持的值，或者给定子设备垫上不支持所选目标。

EPERM
    在只读子设备上调用了 ``VIDIOC_SUBDEV_S_SELECTION`` ioctl 并且 ``which`` 字段设置为 ``V4L2_SUBDEV_FORMAT_ACTIVE``。
