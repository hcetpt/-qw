SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_MODULATOR:

********************************************
ioctl VIDIOC_G_MODULATOR, VIDIOC_S_MODULATOR
********************************************

名称
====

VIDIOC_G_MODULATOR - VIDIOC_S_MODULATOR - 获取或设置调制器属性

概述
========

.. c:macro:: VIDIOC_G_MODULATOR

``int ioctl(int fd, VIDIOC_G_MODULATOR, struct v4l2_modulator *argp)``

.. c:macro:: VIDIOC_S_MODULATOR

``int ioctl(int fd, VIDIOC_S_MODULATOR, const struct v4l2_modulator *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_modulator` 的指针
描述
===========

为了查询调制器的属性，应用程序需要初始化结构体 :c:type:`v4l2_modulator` 的 `index` 字段，并将 `reserved` 数组清零，然后使用指向该结构体的指针调用 :ref:`VIDIOC_G_MODULATOR <VIDIOC_G_MODULATOR>` ioctl。驱动程序会填充结构体的其余部分，或者在索引超出范围时返回一个 `EINVAL` 错误码。为了枚举所有调制器，应用程序应从索引为零开始，每次递增一，直到驱动程序返回 `EINVAL`。

调制器有两个可写属性：音频调制集和射频。要更改已调制的音频子通道，应用程序需要初始化 `index` 和 `txsubchans` 字段以及 `reserved` 数组，并调用 :ref:`VIDIOC_S_MODULATOR <VIDIOC_G_MODULATOR>` ioctl。如果请求无法满足，驱动程序可以选择不同的音频调制方式。然而这是一个只写 ioctl，不会返回实际选择的音频调制方式。

:ref:`SDR <sdr>` 特定的调制器类型是 `V4L2_TUNER_SDR` 和 `V4L2_TUNER_RF`。对于 SDR 设备，`txsubchans` 字段必须初始化为零。在此上下文中，“调制器”指的是 SDR 发射器。

要更改射频，可以使用 :ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl。

.. tabularcolumns:: |p{2.9cm}|p{2.9cm}|p{5.8cm}|p{2.9cm}|p{2.4cm}|

.. c:type:: v4l2_modulator

.. flat-table:: struct v4l2_modulator
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2 1 1

    * - __u32
      - ``index``
      - 标识调制器，由应用程序设置
    * - __u8
      - ``name``\ [32]
      - 调制器的名称，是一个以 NUL 结尾的 ASCII 字符串
此信息旨在供用户使用
    * - __u32
      - ``capability``
      - 调制器功能标志。此字段目前没有定义任何标志，相应地使用结构体 :c:type:`v4l2_tuner` 中的调谐器标志。音频标志表示编码音频子通道的能力。例如，当前视频标准的变化不会影响这些标志。
* - `__u32`
  - `rangelow`
  - 最低可调频率，单位为 62.5 KHz；如果设置了 `capability` 标志 `V4L2_TUNER_CAP_LOW`，则单位为 62.5 Hz；如果设置了 `capability` 标志 `V4L2_TUNER_CAP_1HZ`，则单位为 1 Hz
* - `__u32`
  - `rangehigh`
  - 最高可调频率，单位为 62.5 KHz；如果设置了 `capability` 标志 `V4L2_TUNER_CAP_LOW`，则单位为 62.5 Hz；如果设置了 `capability` 标志 `V4L2_TUNER_CAP_1HZ`，则单位为 1 Hz
* - `__u32`
  - `txsubchans`
  - 通过此字段，应用程序可以确定音频子载波应如何调制。它包含一组标志，如 :ref:`modulator-txsubchans` 中定义的那样。
  .. note::
     调谐器 `rxsubchans` 标志被重用，但语义不同。假设视频输出设备具有 1 到 3 个通道的模拟或 PCM 音频输入。`txsubchans` 标志选择一个或多个通道进行调制，并结合一些音频子程序指示符，例如立体声导频音。
* - `__u32`
  - `type`
  - :cspan:`2` 调制器类型，参见 :c:type:`v4l2_tuner_type`
* - `__u32`
  - `reserved[3]`
  - 为未来扩展保留。驱动程序和应用程序必须将数组设置为零。

.. tabularcolumns:: |p{6.0cm}|p{2.0cm}|p{9.3cm}|

.. cssclass:: longtable

.. _modulator-txsubchans:

.. flat-table:: 调制器音频传输标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_TUNER_SUB_MONO`
      - 0x0001
      - 当输入有多个通道时，将通道 1 调制为单声道音频，或者对通道 1 和 2 进行混缩。此标志不与 `V4L2_TUNER_SUB_STEREO` 或 `V4L2_TUNER_SUB_LANG1` 结合使用。
* - `V4L2_TUNER_SUB_STEREO`
      - 0x0002
      - 将通道 1 和 2 调制为立体声音频信号的左右通道。当输入只有一个通道或两个通道且同时设置了 `V4L2_TUNER_SUB_SAP` 时，通道 1 被编码为左右通道。此标志不与 `V4L2_TUNER_SUB_MONO` 或 `V4L2_TUNER_SUB_LANG1` 结合使用。如果驱动程序不支持立体声，则应回退到单声道。
* - `V4L2_TUNER_SUB_LANG1`
      - 0x0008
      - 将通道 1 和 2 调制为双语音频信号的主要语言和次要语言。当输入只有一个通道时，该通道用于两种语言。无法仅编码主要语言或次要语言。此标志不与 `V4L2_TUNER_SUB_MONO`、`V4L2_TUNER_SUB_STEREO` 或 `V4L2_TUNER_SUB_SAP` 结合使用。如果硬件不支持相应的音频矩阵或当前视频标准不允许双语音频，:ref:`VIDIOC_S_MODULATOR <VIDIOC_G_MODULATOR>` ioctl 应返回 `EINVAL` 错误代码，并且驱动程序应回退到单声道或立体声模式。
* - ``V4L2_TUNER_SUB_LANG2``
      - 0x0004
      - 效果与 ``V4L2_TUNER_SUB_SAP`` 相同
* - ``V4L2_TUNER_SUB_SAP``
      - 0x0004
      - 当与 ``V4L2_TUNER_SUB_MONO`` 结合使用时，第一个声道编码为单声道音频，最后一个声道编码为第二音频节目（Second Audio Program）。当输入只有一个声道时，该声道用于所有音频轨道。当输入有三个声道时，单声道音轨是第一和第二声道的混音。当与 ``V4L2_TUNER_SUB_STEREO`` 结合使用时，第一和第二声道编码为左、右立体声音频，第三声道编码为第二音频节目。当输入只有两个声道时，第一个声道编码为左右声道，第二个声道编码为第二音频节目。当输入只有一个声道时，该声道用于所有音频轨道。无法仅编码第二音频节目。此标志必须与 ``V4L2_TUNER_SUB_MONO`` 或 ``V4L2_TUNER_SUB_STEREO`` 结合使用。如果硬件不支持相应的音频矩阵，或者当前视频标准不允许第二音频节目，则 ``VIDIOC_S_MODULATOR`` ioctl 应返回一个 ``EINVAL`` 错误代码，并且驱动程序应回退到单声道或立体声模式。
* - ``V4L2_TUNER_SUB_RDS``
      - 0x0010
      - 启用FM发射器的RDS编码

返回值
======

成功时返回0，失败时返回-1，并设置 ``errno`` 变量以表示适当的错误。通用错误代码在《通用错误代码》章节中有描述。

EINVAL
    结构 :c:type:`v4l2_modulator` 的 ``index`` 越界
