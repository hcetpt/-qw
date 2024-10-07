SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUMOUTPUT:

**************************
ioctl VIDIOC_ENUMOUTPUT
**************************

名称
====

VIDIOC_ENUMOUTPUT - 列出视频输出

概览
========

.. c:macro:: VIDIOC_ENUMOUTPUT

``int ioctl(int fd, VIDIOC_ENUMOUTPUT, struct v4l2_output *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_output` 的指针
描述
===========

为了查询视频输出的属性，应用程序需要初始化结构体 :c:type:`v4l2_output` 的 ``index`` 字段，并通过指向该结构体的指针调用 :ref:`VIDIOC_ENUMOUTPUT`。
驱动程序会填充其余字段或在索引超出范围时返回 ``EINVAL`` 错误码。为了枚举所有输出，应用程序应从索引零开始，每次递增一，直到驱动程序返回 ``EINVAL``。

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_output

.. flat-table:: struct v4l2_output
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 标识输出，由应用程序设置
    * - __u8
      - ``name``\ [32]
      - 视频输出的名称，一个以空字符终止的ASCII字符串，例如："Vout"。此信息旨在供用户使用，最好是设备本身的连接器标签
    * - __u32
      - ``type``
      - 输出类型，参见 :ref:`output-type`
    * - __u32
      - ``audioset``
      - 驱动程序可以枚举最多32个视频和音频输出。此字段显示了如果当前选择的视频输出是该输出时，可以选择的音频输出。它是一个位掩码
      - 最低位对应音频输出0，最高位对应输出31。可以设置任意数量的位，也可以不设置任何位
      - 如果驱动程序没有枚举音频输出，则不应设置任何位。应用程序不应将其解释为缺乏音频支持。驱动程序可能会自动选择音频输出而不进行枚举
有关音频输出及其选择当前输出的详细信息，请参见 :ref:`audio`

* - __u32
  - ``modulator``
  - 输出设备可以有零个或多个RF调制器。当 ``type`` 是 ``V4L2_OUTPUT_TYPE_MODULATOR`` 时，这是一个RF连接器，此字段标识调制器。它对应于结构 :c:type:`v4l2_modulator` 字段 ``index``。关于调制器的详细信息，请参见 :ref:`tuner`
* - :ref:`v4l2_std_id <v4l2-std-id>`
  - ``std``
  - 每个视频输出支持一种或多种不同的视频标准。此字段是一组所有支持的标准。有关视频标准及其切换方式的详细信息，请参见 :ref:`standard`
* - __u32
  - ``capabilities``
  - 此字段提供输出的能力。请参见 :ref:`output-capabilities` 了解标志
* - __u32
  - ``reserved``\ [3]
  - 预留用于将来扩展。驱动程序必须将数组设置为零

.. tabularcolumns:: |p{7.5cm}|p{0.6cm}|p{9.2cm}|

.. _output-type:

.. flat-table:: 输出类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_OUTPUT_TYPE_MODULATOR``
      - 1
      - 此输出是一个模拟电视调制器
* - ``V4L2_OUTPUT_TYPE_ANALOG``
      - 2
      - 任何非调制器视频输出，例如复合视频、S-视频、HDMI。“_TYPE_ANALOG”的命名是历史遗留的，今天我们会称之为“_TYPE_VIDEO”
* - ``V4L2_OUTPUT_TYPE_ANALOGVGAOVERLAY``
      - 3
      - 视频输出将被复制到一个 :ref:`video overlay <overlay>`

.. tabularcolumns:: |p{6.4cm}|p{2.4cm}|p{8.5cm}|

.. _output-capabilities:

.. flat-table:: 输出能力
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_OUT_CAP_DV_TIMINGS``
      - 0x00000002
      - 此输出支持通过使用 ``VIDIOC_S_DV_TIMINGS`` 设置视频定时
* - ``V4L2_OUT_CAP_STD``
      - 0x00000004
      - 此输出支持使用 ``VIDIOC_S_STD`` 设置电视制式
* - ``V4L2_OUT_CAP_NATIVE_SIZE``
      - 0x00000008
      - 此输出支持使用 ``V4L2_SEL_TGT_NATIVE_SIZE`` 选择目标来设置原生尺寸，详见 :ref:`v4l2-selections-common`

返回值
======

成功时返回 0，失败时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
    结构体 :c:type:`v4l2_output` 的 ``index`` 超出了范围
