.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_SUBDEV_QUERYCAP:

****************************
ioctl VIDIOC_SUBDEV_QUERYCAP
****************************

名称
====

VIDIOC_SUBDEV_QUERYCAP - 查询子设备的功能

概要
========

.. c:macro:: VIDIOC_SUBDEV_QUERYCAP

``int ioctl(int fd, VIDIOC_SUBDEV_QUERYCAP, struct v4l2_subdev_capability *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_subdev_capability` 的指针

描述
===========

所有 V4L2 子设备都支持 ``VIDIOC_SUBDEV_QUERYCAP`` ioctl。它用于识别与本规范兼容的内核设备，并获取有关驱动程序和硬件功能的信息。ioctl 接受一个指向结构体 :c:type:`v4l2_subdev_capability` 的指针，该指针由驱动程序填充。如果驱动程序不兼容此规范，则 ioctl 返回 ``ENOTTY`` 错误码。
.. tabularcolumns:: |p{1.5cm}|p{2.9cm}|p{12.9cm}|

.. c:type:: v4l2_subdev_capability

.. flat-table:: struct v4l2_subdev_capability
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 4 20

    * - __u32
      - ``version``
      - 驱动程序的版本号
报告的版本由 V4L2 子系统根据内核编号方案提供。然而，在某些情况下（例如，稳定或发行版修改的内核使用了较新内核的 V4L2 堆栈），它可能不会返回与内核相同的版本。
版本号使用 ``KERNEL_VERSION()`` 宏格式化：
    * - :cspan:`2`

	``#define KERNEL_VERSION(a,b,c) (((a) << 16) + ((b) << 8) + (c))``

	``__u32 version = KERNEL_VERSION(0, 8, 1);``

	``printf ("Version: %u.%u.%u\\n",``

	``(version >> 16) & 0xFF, (version >> 8) & 0xFF, version & 0xFF);``
    * - __u32
      - ``capabilities``
      - 打开设备的子设备功能，请参阅 :ref:`subdevice-capabilities`
* - __u32
      - ``reserved``\[14\]
      - 为将来扩展保留。V4L2 核心将其设置为 0
.. tabularcolumns:: |p{6.8cm}|p{2.4cm}|p{8.1cm}|

.. _subdevice-capabilities:

.. cssclass:: longtable

.. flat-table:: 子设备功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - V4L2_SUBDEV_CAP_RO_SUBDEV
      - 0x00000001
      - 子设备设备节点以只读模式注册
对修改设备状态的子设备 ioctl 的访问受到限制。请参阅每个单独子设备 ioctl 的文档，了解适用于只读子设备的具体限制。

返回值
============

成功时返回 0，错误时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
ENOTTY
设备节点不是V4L2子设备
