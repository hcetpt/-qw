SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_SLICED_VBI_CAP:

*******************************
ioctl VIDIOC_G_SLICED_VBI_CAP
*******************************

名称
====

VIDIOC_G_SLICED_VBI_CAP - 查询切片 VBI 能力

概要
========

.. c:macro:: VIDIOC_G_SLICED_VBI_CAP

``int ioctl(int fd, VIDIOC_G_SLICED_VBI_CAP, struct v4l2_sliced_vbi_cap *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_sliced_vbi_cap` 的指针
描述
===========

为了查询一个切片 VBI 捕获或输出设备支持哪些数据服务，应用程序需要初始化结构体 :c:type:`v4l2_sliced_vbi_cap` 的 ``type`` 字段，清空 ``reserved`` 数组，并调用 :ref:`VIDIOC_G_SLICED_VBI_CAP <VIDIOC_G_SLICED_VBI_CAP>` ioctl。驱动程序将填充剩余字段或在不支持切片 VBI API 或 ``type`` 无效时返回 ``EINVAL`` 错误代码。
.. note::

   ``type`` 字段是在 Linux 2.6.19 中添加的，ioctl 从只读变为写读。
.. c:type:: v4l2_sliced_vbi_cap

.. tabularcolumns:: |p{1.4cm}|p{4.4cm}|p{4.5cm}|p{3.6cm}|p{3.6cm}|

.. flat-table:: 结构体 v4l2_sliced_vbi_cap
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 3 2 2 2

    * - __u16
      - ``service_set``
      - :cspan:`2` 驱动程序支持的所有数据服务的集合
等于 ``service_lines`` 数组所有元素的并集
* - __u16
      - ``service_lines``\ [2][24]
      - :cspan:`2` 此数组中的每个元素包含一组硬件可以在特定扫描线上查找或插入的数据服务。数据服务定义在 :ref:`vbi-services`
数组索引映射到 ITU-R 行号\ [#f1]_ 如下：
    * -
      -
      - 元素
      - 525 行系统
      - 625 行系统
    * -
      -
      - ``service_lines``\ [0][1]
      - 1
      - 1
    * -
      -
      - ``service_lines``\ [0][23]
      - 23
      - 23
    * -
      -
      - ``service_lines``\ [1][1]
      - 264
      - 314
    * -
      -
      - ``service_lines``\ [1][23]
      - 286
      - 336
    * -
    * -
      -
      - :cspan:`2` 硬件每帧可以捕获或输出的 VBI 行数，或者它可以在给定行上识别的服务数量可能有限制。例如，在 PAL 行 16 上，硬件可能能够查找 VPS 或 Teletext 信号，但不能同时查找两者。应用程序可以使用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 来了解这些限制，具体如 :ref:`sliced` 所述
* -
    * -
      -
      - :cspan:`2` 驱动程序必须将 ``service_lines`` [0][0] 和 ``service_lines``\ [1][0] 设置为零
* - __u32
      - ``type``
      - 数据流类型，参见 :c:type:`v4l2_buf_type`。应该是 ``V4L2_BUF_TYPE_SLICED_VBI_CAPTURE`` 或 ``V4L2_BUF_TYPE_SLICED_VBI_OUTPUT``
* - `__u32`
  - `reserved`\ [3]
  - :cspan:`2` 此数组保留用于将来扩展
  应用程序和驱动程序必须将其设置为零
.. [#f1]

   参见 :ref:`vbi-525` 和 :ref:`vbi-625`
.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{3.9cm}|p{1.0cm}|p{2.0cm}|p{3.0cm}|p{7.0cm}|

.. _vbi-services:

.. flat-table:: 分割 VBI 服务
    :header-rows:  1
    :stub-columns: 0
    :widths:       2 1 1 2 2

    * - 符号
      - 值
      - 引用
      - 行，通常
      - 载荷
    * - ``V4L2_SLICED_TELETEXT_B``（Teletext 系统 B）
      - 0x0001
      - :ref:`ets300706`，

	:ref:`itu653`
      - PAL/SECAM 行 7-22，320-335（第二场 7-22）
      - Teletext 数据包的最后 42 字节，共 45 字节，不包括时钟跑入和帧代码，先传输最低有效位
* - ``V4L2_SLICED_VPS``
      - 0x0400
      - :ref:`ets300231`
      - PAL 行 16
      - 根据 ETS 300 231 图 9 的第 3 到第 15 字节，先传输最低有效位
* - ``V4L2_SLICED_CAPTION_525``
      - 0x1000
      - :ref:`cea608`
      - NTSC 行 21，284（第二场 21）
      - 包括奇偶校验位的两个字节按传输顺序排列，先传输最低有效位
* - ``V4L2_SLICED_WSS_625``
      - 0x4000
      - :ref:`en300294`，

	:ref:`itu1119`
      - PAL/SECAM 行 23
      - 参见下面的 :ref:`v4l2-sliced-vbi-cap-wss-625-payload`
* - ``V4L2_SLICED_VBI_525``
      - 0x1000
      - :cspan:`2` 适用于 525 行系统的服务集
* - ``V4L2_SLICED_VBI_625``
      - 0x4401
      - :cspan:`2` 适用于 625 行系统的服务集
.. raw:: latex

    \normalsize

.. _v4l2-sliced-vbi-cap-wss-625-payload:

V4L2_SLICED_VBI_CAP 的 WSS_625 载荷
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``V4L2_SLICED_WSS_625`` 的载荷为：

	    +-----+------------------+-----------------------+
	    | 字节 |        0         |           1           |
	    +-----+--------+---------+-----------+-----------+
	    |      | MSB    | LSB     | MSB       | LSB       |
	    |      +-+-+-+--+--+-+-+--+--+-+--+---+---+--+-+--+
	    | 位   |7|6|5|4 | 3|2|1|0 | x|x|13|12 | 11|10|9|8 |
	    +-----+-+-+-+--+--+-+-+--+--+-+--+---+---+--+-+--+

返回值
======

成功时返回 0，错误时返回 -1，并根据情况设置 `errno` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
`type` 字段中的值是错误的。
