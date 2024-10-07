SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUM_FRAMEINTERVALS:

********************************
ioctl VIDIOC_ENUM_FRAMEINTERVALS
********************************

名称
====

VIDIOC_ENUM_FRAMEINTERVALS - 列出帧间隔

概要
========

.. c:macro:: VIDIOC_ENUM_FRAMEINTERVALS

``int ioctl(int fd, VIDIOC_ENUM_FRAMEINTERVALS, struct v4l2_frmivalenum *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_frmivalenum` 的指针，该结构体包含像素格式和大小，并接收帧间隔
描述
===========

此 ioctl 允许应用程序列出设备支持的给定像素格式和帧大小的所有帧间隔。
支持的像素格式和帧大小可以通过使用 :ref:`VIDIOC_ENUM_FMT` 和 :ref:`VIDIOC_ENUM_FRAMESIZES` 函数获得。
返回值和 ``v4l2_frmivalenum.type`` 字段的内容取决于设备支持的帧间隔类型。以下是针对不同情况的函数语义：

-  **离散型：** 如果给定的索引值（从零开始）有效，则函数返回成功。应用程序应每次调用时将索引递增一，直到返回 ``EINVAL``。驱动程序会将 `v4l2_frmivalenum.type` 字段设置为 `V4L2_FRMIVAL_TYPE_DISCRETE`。联合体中只有 `discrete` 成员有效。
-  **逐步型：** 如果给定的索引值为零，则函数返回成功，对于其他任何索引值则返回 ``EINVAL``。驱动程序会将 ``v4l2_frmivalenum.type`` 字段设置为 ``V4L2_FRMIVAL_TYPE_STEPWISE``。联合体中只有 ``stepwise`` 成员有效。
-  **连续型：** 这是逐步型的一个特殊情况。如果给定的索引值为零，则函数返回成功，对于其他任何索引值则返回 ``EINVAL``。驱动程序会将 ``v4l2_frmivalenum.type`` 字段设置为 ``V4L2_FRMIVAL_TYPE_CONTINUOUS``。联合体中只有 ``stepwise`` 成员有效，且 ``step`` 值被设置为 1。

当应用程序以索引零调用此函数时，必须检查 ``type`` 字段以确定设备支持的帧间隔枚举类型。只有对于 ``V4L2_FRMIVAL_TYPE_DISCRETE`` 类型才有意义增加索引值以接收更多的帧间隔。

.. note::

   返回帧间隔的顺序没有特殊含义。特别是它不能说明潜在的默认帧间隔。
应用程序可以假设枚举数据在没有应用程序自身任何交互的情况下不会改变。这意味着如果应用程序在运行帧间隔枚举时没有执行其他ioctl调用，那么枚举数据是一致的。
.. note::

   **帧间隔和帧率：** V4L2 API 使用帧间隔而不是帧率。给定帧间隔后，帧率可以通过以下方式计算：

   ::

       帧率 = 1 / 帧间隔

结构体
======

在下面的结构体中，*IN* 表示需要由应用程序填充的值，*OUT* 表示由驱动程序填充的值。应用程序应该将所有成员清零，除了 *IN* 字段。

.. c:type:: v4l2_frmival_stepwise

.. flat-table:: struct v4l2_frmival_stepwise
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct :c:type:`v4l2_fract`
      - ``min``
      - 最小帧间隔 [秒]
* - struct :c:type:`v4l2_fract`
      - ``max``
      - 最大帧间隔 [秒]
* - struct :c:type:`v4l2_fract`
      - ``step``
      - 帧间隔步长 [秒]

.. c:type:: v4l2_frmivalenum

.. tabularcolumns:: |p{4.9cm}|p{3.3cm}|p{9.1cm}|

.. flat-table:: struct v4l2_frmivalenum
    :header-rows:  0
    :stub-columns: 0

    * - __u32
      - ``index``
      - IN: 给定帧间隔在枚举中的索引
* - __u32
      - ``pixel_format``
      - IN: 枚举帧间隔所对应的像素格式
* - __u32
      - ``width``
      - IN: 枚举帧间隔所对应的帧宽度
* - __u32
      - ``height``
      - IN: 枚举帧间隔所对应的帧高度
* - __u32
      - ``type``
      - OUT: 设备支持的帧间隔类型
* - union {
      - (匿名)
      - OUT: 给定索引的帧间隔
* - struct :c:type:`v4l2_fract`
      - ``discrete``
      - 帧间隔 [秒]
* - struct :c:type:`v4l2_frmival_stepwise`
      - ``stepwise``
      -
    * - }
      -
      -
* - __u32
      - ``reserved[2]``
      - 保留空间以备将来使用。必须由驱动程序和应用程序清零

枚举
====

.. c:type:: v4l2_frmivaltypes

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. flat-table:: 枚举 v4l2_frmivaltypes
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_FRMIVAL_TYPE_DISCRETE``
      - 1
      - 离散帧间隔
* - ``V4L2_FRMIVAL_TYPE_CONTINUOUS``
      - 2
      - 连续帧间隔
* - ``V4L2_FRMIVAL_TYPE_STEPWISE``
      - 3
      - 逐步定义的帧间隔

返回值
============

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。
