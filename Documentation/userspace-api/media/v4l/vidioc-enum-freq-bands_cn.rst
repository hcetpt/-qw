.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUM_FREQ_BANDS:

****************************
ioctl VIDIOC_ENUM_FREQ_BANDS
****************************

名称
====

VIDIOC_ENUM_FREQ_BANDS - 列出支持的频率波段

概要
========

.. c:macro:: VIDIOC_ENUM_FREQ_BANDS

``int ioctl(int fd, VIDIOC_ENUM_FREQ_BANDS, struct v4l2_frequency_band *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_frequency_band` 结构体的指针
描述
===========

枚举调谐器或调制器所支持的频率波段。为此，应用程序需要初始化结构体 :c:type:`v4l2_frequency_band` 的 ``tuner``、``type`` 和 ``index`` 字段，并清空 ``reserved`` 数组，然后使用指向该结构体的指针调用 :ref:`VIDIOC_ENUM_FREQ_BANDS` ioctl。如果相应调谐器/调制器的 ``V4L2_TUNER_CAP_FREQ_BANDS`` 能力被设置，则支持此 ioctl。
.. tabularcolumns:: |p{2.9cm}|p{2.9cm}|p{5.8cm}|p{2.9cm}|p{2.4cm}|

.. c:type:: v4l2_frequency_band

.. flat-table:: struct v4l2_frequency_band
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2 1 1

    * - __u32
      - ``tuner``
      - 调谐器或调制器的索引号。这与结构体 :c:type:`v4l2_input` 的 ``tuner`` 字段以及结构体 :c:type:`v4l2_tuner` 的 ``index`` 字段相同，或者与结构体 :c:type:`v4l2_output` 的 ``modulator`` 字段和结构体 :c:type:`v4l2_modulator` 的 ``index`` 字段相同。
    * - __u32
      - ``type``
      - 调谐器类型。这与结构体 :c:type:`v4l2_tuner` 的 ``type`` 字段中的值相同。对于 ``/dev/radioX`` 设备节点，此字段必须设置为 ``V4L2_TUNER_RADIO``；对于其他设备节点，必须设置为 ``V4L2_TUNER_ANALOG_TV``。对于调制器（目前仅支持无线电调制器），设置此字段为 ``V4L2_TUNER_RADIO``。参见 :c:type:`v4l2_tuner_type`
    * - __u32
      - ``index``
      - 标识频率波段，由应用程序设置
    * - __u32
      - ``capability``
      - :cspan:`2` 此频率波段的调谐器/调制器能力标志，参见 :ref:`tuner-capability`。对于选定的调谐器/调制器，所有频率波段的 ``V4L2_TUNER_CAP_LOW`` 或 ``V4L2_TUNER_CAP_1HZ`` 能力标志必须相同。因此，要么所有波段都具有该能力标志，要么没有任何波段具有该能力标志
    * - __u32
      - ``rangelow``
      - :cspan:`2` 以 62.5 kHz 为单位的最低可调频率，如果设置了 ``capability`` 标志 ``V4L2_TUNER_CAP_LOW``，则以 62.5 Hz 为单位。当设置了 ``capability`` 标志 ``V4L2_TUNER_CAP_1HZ`` 时，使用 1 Hz 单位
    * - __u32
      - ``rangehigh``
      - :cspan:`2` 以 62.5 kHz 为单位的最高可调频率，如果设置了 ``capability`` 标志 ``V4L2_TUNER_CAP_LOW``，则以 62.5 Hz 为单位。当设置了 ``capability`` 标志 ``V4L2_TUNER_CAP_1HZ`` 时，使用 1 Hz 单位
    * - __u32
      - ``modulation``
      - :cspan:`2` 此频率波段支持的调制系统。参见 :ref:`band-modulation`
.. note::

    目前每个频段仅支持一种调制系统。如果需要支持多种调制系统，还需要做更多的工作。如果您需要这种功能，请联系 linux-media 邮件列表（`https://linuxtv.org/lists.php <https://linuxtv.org/lists.php>`__）。

* - __u32
      - ``reserved``\[9\]
      - 保留以供将来扩展
应用程序和驱动程序必须将数组设置为零

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _band-modulation:

.. flat-table:: 频段调制系统
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_BAND_MODULATION_VSB``
      - 0x02
      - 残余边带调制，用于模拟电视
* - ``V4L2_BAND_MODULATION_FM``
      - 0x04
      - 频率调制，常用于模拟广播
* - ``V4L2_BAND_MODULATION_AM``
      - 0x08
      - 幅度调制，常用于模拟广播

返回值
======

成功时返回 0，出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`通用错误码 <gen-errors>` 章节中描述。

EINVAL
    调谐器 ``tuner`` 或索引 ``index`` 越界或类型字段 ``type`` 错误
