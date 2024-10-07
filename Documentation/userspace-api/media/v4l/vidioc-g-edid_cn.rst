SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_EDID:

******************************************************************************
ioctl VIDIOC_G_EDID, VIDIOC_S_EDID, VIDIOC_SUBDEV_G_EDID, VIDIOC_SUBDEV_S_EDID
******************************************************************************

名称
====

VIDIOC_G_EDID - VIDIOC_S_EDID - VIDIOC_SUBDEV_G_EDID - VIDIOC_SUBDEV_S_EDID - 获取或设置视频接收器/发射器的 EDID

概要
========

.. c:macro:: VIDIOC_G_EDID

``int ioctl(int fd, VIDIOC_G_EDID, struct v4l2_edid *argp)``

.. c:macro:: VIDIOC_S_EDID

``int ioctl(int fd, VIDIOC_S_EDID, struct v4l2_edid *argp)``

.. c:macro:: VIDIOC_SUBDEV_G_EDID

``int ioctl(int fd, VIDIOC_SUBDEV_G_EDID, struct v4l2_edid *argp)``

.. c:macro:: VIDIOC_SUBDEV_S_EDID

``int ioctl(int fd, VIDIOC_SUBDEV_S_EDID, struct v4l2_edid *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_edid` 的指针

描述
===========

这些 ioctl 可用于获取或设置与视频输入（来自接收器）或输出（来自发射设备）相关的 EDID。它们可以用于子设备节点（/dev/v4l-subdevX）或视频节点（/dev/videoX）。
当与视频节点一起使用时，``pad`` 字段表示视频捕获设备的输入索引或视频输出设备的输出索引，这与 :ref:`VIDIOC_ENUMINPUT` 和 :ref:`VIDIOC_ENUMOUTPUT` 分别返回的一致。当与子设备节点一起使用时，``pad`` 字段表示子设备的输入或输出端口。如果给定的 ``pad`` 值没有 EDID 支持，则将返回 ``EINVAL`` 错误代码。
为了获取 EDID 数据，应用程序需要填写 ``pad``、``start_block``、``blocks`` 和 ``edid`` 字段，清零 ``reserved`` 数组，并调用 :ref:`VIDIOC_G_EDID <VIDIOC_G_EDID>`。当前从 ``start_block`` 开始的大小为 ``blocks`` 的 EDID 将被放置在 ``edid`` 所指向的内存中。``edid`` 指针必须指向至少 ``blocks`` * 128 字节大小的内存（一个块的大小是 128 字节）。
如果实际的块数少于指定的数量，那么驱动程序会将 ``blocks`` 设置为实际的块数。如果没有可用的 EDID 块，则设置错误代码 ``ENODATA``。
如果块需要从接收端获取，那么此调用将阻塞直到它们被读取。
如果在调用 :ref:`VIDIOC_G_EDID <VIDIOC_G_EDID>` 时将 ``start_block`` 和 ``blocks`` 都设置为 0，那么驱动程序会将 ``blocks`` 设置为可用的 EDID 块总数，并且在不复制任何数据的情况下返回 0。这是发现有多少 EDID 块的一个简单方法。
.. note::

   如果完全没有可用的 EDID 块，那么驱动程序会将 ``blocks`` 设置为 0 并返回 0。

为了设置接收器的 EDID 块，应用程序需要填写 ``pad``、``blocks`` 和 ``edid`` 字段，并将 ``start_block`` 设置为 0，并清零 ``reserved`` 数组。不可能只设置部分 EDID，要么全部设置要么不设置。只有对于接收器来说设置 EDID 数据才有意义，因为对于发射器来说没有意义。
驾驶员假定完整的EDID被传递进来。如果EDID块多于硬件所能处理的数量，则不会写入EDID，而是设置错误代码`E2BIG`，并将`blocks`设置为硬件支持的最大数量。如果`start_block`的值不是0，则设置错误代码`EINVAL`。
要禁用一个EDID，将`blocks`设置为0。根据硬件的不同，这将使热插拔引脚处于低电平，并/或阻止源读取EDID数据。无论如何，最终结果是相同的：EDID不再可用。

.. c:type:: v4l2_edid

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构 v4l2_edid
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pad``
      - 获取/设置EDID块的pad。当与视频设备节点一起使用时，该pad代表由:ref:`VIDIOC_ENUMINPUT`和:ref:`VIDIOC_ENUMOUTPUT`返回的输入或输出索引
* - __u32
      - ``start_block``
      - 从这个块开始读取EDID。设置EDID时必须为0
* - __u32
      - ``blocks``
      - 要获取或设置的块数。必须小于或等于256（根据标准定义的最大块数）。当你设置EDID且`blocks`为0时，则禁用或擦除EDID
* - __u32
      - ``reserved``\[5\]
      - 保留用于将来扩展。应用程序和驱动程序必须将数组设置为零
* - __u8 *
      - ``edid``
      - 指向包含EDID的内存。最小大小为`blocks` * 128

返回值
======

成功时返回0，出错时返回-1，并且设置`errno`变量为适当的值。通用错误代码在:ref:`通用错误代码<gen-errors>`章节中描述。

``ENODATA``
    EDID数据不可用

``E2BIG``
    提供的EDID数据超过了硬件能处理的数量
当然，请提供您需要翻译的文本。
