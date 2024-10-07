SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _rds:

*************
RDS 接口
*************

无线电数据系统（Radio Data System）通过广播节目的不可听音频副载波以二进制格式传输补充信息，例如电台名称或旅行信息。此接口旨在用于能够接收和/或传输 RDS 信息的设备。更多信息请参阅核心 RDS 标准 :ref:`iec62106` 和 RBDS 标准 :ref:`nrsc4`。
.. note::

   值得注意的是，在美国使用的 RBDS 标准几乎与 RDS 标准相同。任何 RDS 解码器/编码器也可以处理 RBDS。只是某些字段的含义略有不同。更多信息请参阅 RBDS 标准。

RBDS 标准还规定了对 MMBS（Modified Mobile Broadcast System）的支持。这是一种似乎已被废弃的专有格式。
RDS 接口不支持此格式。如果需要 MMBS（或所谓的“E 块”）的支持，请联系 linux-media 邮件列表：
`https://linuxtv.org/lists.php <https://linuxtv.org/lists.php>`__
查询能力
=====================

支持 RDS 捕获 API 的设备会在由 :ref:`VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 的 `capabilities` 字段中设置 `V4L2_CAP_RDS_CAPTURE` 标志。任何支持 RDS 的调谐器都会在结构体 :c:type:`v4l2_tuner` 的 `capability` 字段中设置 `V4L2_TUNER_CAP_RDS` 标志。如果驱动程序仅传递 RDS 块而不解释数据，则应设置 `V4L2_TUNER_CAP_RDS_BLOCK_IO` 标志，详见 :ref:`阅读 RDS 数据 <reading-rds-data>`。为了将来使用，还定义了 `V4L2_TUNER_CAP_RDS_CONTROLS` 标志。然而，目前还没有支持该功能的无线电调谐器驱动程序。如果您计划编写此类驱动程序，请在 linux-media 邮件列表上讨论：
`https://linuxtv.org/lists.php <https://linuxtv.org/lists.php>`__
是否检测到 RDS 信号可以通过查看结构体 :c:type:`v4l2_tuner` 的 `rxsubchans` 字段来确定：如果检测到 RDS 数据，`V4L2_TUNER_SUB_RDS` 将会被设置。
支持 RDS 输出 API 的设备会在由 :ref:`VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 的 `capabilities` 字段中设置 `V4L2_CAP_RDS_OUTPUT` 标志。任何支持 RDS 的调制器都会在结构体 :c:type:`v4l2_modulator` 的 `capability` 字段中设置 `V4L2_TUNER_CAP_RDS` 标志。为了启用 RDS 传输，必须在结构体 :c:type:`v4l2_modulator` 的 `txsubchans` 字段中设置 `V4L2_TUNER_SUB_RDS` 位。如果驱动程序仅传递 RDS 块而不解释数据，则应设置 `V4L2_TUNER_CAP_RDS_BLOCK_IO` 标志。如果调谐器能够处理诸如节目识别码和无线电文本等 RDS 实体，则应设置 `V4L2_TUNER_CAP_RDS_CONTROLS` 标志，详见 :ref:`写入 RDS 数据 <writing-rds-data>` 和 :ref:`FM 发射机控制参考 <fm-tx-controls>`
.. _reading-rds-data:

读取 RDS 数据
================

可以使用 :c:func:`read()` 函数从无线电设备读取 RDS 数据。数据以三个字节一组的形式打包。
.. _writing-rds-data:

写入 RDS 数据
================

可以使用 :c:func:`write()` 函数向无线电设备写入 RDS 数据。数据以三个字节一组的形式打包，如下所示：

RDS 数据结构
==================

.. c:type:: v4l2_rds_data

.. flat-table:: struct v4l2_rds_data
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 5

    * - __u8
      - ``lsb``
      - RDS 块的最低有效字节
    * - __u8
      - ``msb``
      - RDS 块的最高有效字节
    * - __u8
      - ``block``
      - 块描述

.. _v4l2-rds-block:

.. tabularcolumns:: |p{2.9cm}|p{14.6cm}|

.. flat-table:: 块描述
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 5

    * - 位 0-2
      - 接收数据的块（又称偏移量）
* - 位 3-5
      - 已弃用。目前与位 0-2 相同。请勿使用这些位

* - 位 6
      - 校正位。指示该数据块中的错误已被纠正

* - 位 7
      - 错误位。指示在接收此数据块时发生了无法校正的错误

.. _v4l2-rds-block-codes:

.. tabularcolumns:: |p{6.4cm}|p{2.0cm}|p{1.2cm}|p{7.0cm}|

.. flat-table:: 块定义
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 1 5

    * - V4L2_RDS_BLOCK_MSK
      -
      - 7
      - 获取块 ID 的位 0-2 的掩码

* - V4L2_RDS_BLOCK_A
      -
      - 0
      - 块 A

* - V4L2_RDS_BLOCK_B
      -
      - 1
      - 块 B

* - V4L2_RDS_BLOCK_C
      -
      - 2
      - 块 C

* - V4L2_RDS_BLOCK_D
      -
      - 3
      - 块 D

* - V4L2_RDS_BLOCK_C_ALT
      -
      - 4
      - 块 C'

* - V4L2_RDS_BLOCK_INVALID
      - 只读
      - 7
      - 无效块
* - V4L2_RDS_BLOCK_CORRECTED
      - 只读
      - 0x40
      - 检测到但已纠正的比特错误
* - V4L2_RDS_BLOCK_ERROR
      - 只读
      - 0x80
      - 发生了无法纠正的错误
