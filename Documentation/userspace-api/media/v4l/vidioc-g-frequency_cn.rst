SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_FREQUENCY:

********************************************
ioctl VIDIOC_G_FREQUENCY, VIDIOC_S_FREQUENCY
********************************************

名称
====

VIDIOC_G_FREQUENCY - VIDIOC_S_FREQUENCY - 获取或设置调谐器或调制器的无线电频率

概要
========

.. c:macro:: VIDIOC_G_FREQUENCY

``int ioctl(int fd, VIDIOC_G_FREQUENCY, struct v4l2_frequency *argp)``

.. c:macro:: VIDIOC_S_FREQUENCY

``int ioctl(int fd, VIDIOC_S_FREQUENCY, const struct v4l2_frequency *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_frequency` 结构体的指针

描述
===========

为了获取当前调谐器或调制器的无线电频率，应用程序需要将一个 :c:type:`v4l2_frequency` 结构体中的 ``tuner`` 字段设置为相应的调谐器或调制器编号（只有输入设备有调谐器，只有输出设备有调制器），清空 ``reserved`` 数组，并使用指向该结构体的指针调用 :ref:`VIDIOC_G_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl。驱动程序会将当前频率存储在 ``frequency`` 字段中。

为了改变当前调谐器或调制器的无线电频率，应用程序需要初始化 :c:type:`v4l2_frequency` 结构体中的 ``tuner``、``type`` 和 ``frequency`` 字段以及 ``reserved`` 数组，并使用指向该结构体的指针调用 :ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl。如果请求的频率无法实现，驱动程序会选择最接近的可能值。然而，:ref:`VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` 是一个只写 ioctl，它不会返回实际的新频率。

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_frequency

.. flat-table:: struct v4l2_frequency
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``tuner``
      - 调谐器或调制器的索引号。这与 :c:type:`v4l2_input` 结构体中的 ``tuner`` 字段、:c:type:`v4l2_tuner` 结构体中的 ``index`` 字段、:c:type:`v4l2_output` 结构体中的 ``modulator`` 字段以及 :c:type:`v4l2_modulator` 结构体中的 ``index`` 字段的值相同。
    * - __u32
      - ``type``
      - 调谐器类型。这与 :c:type:`v4l2_tuner` 结构体中的 ``type`` 字段的值相同。对于 ``/dev/radioX`` 设备节点，此字段必须设置为 ``V4L2_TUNER_RADIO``；对于其他设备，必须设置为 ``V4L2_TUNER_ANALOG_TV``。对于调制器（目前仅支持无线电调制器），请将此字段设置为 ``V4L2_TUNER_RADIO``。参见 :c:type:`v4l2_tuner_type`
    * - __u32
      - ``frequency``
      - 调谐频率，单位为 62.5 kHz，或者如果 :c:type:`v4l2_tuner` 或 :c:type:`v4l2_modulator` 结构体中的 ``capability`` 标志设置了 ``V4L2_TUNER_CAP_LOW``，则单位为 62.5 Hz。如果 ``capability`` 标志设置了 ``V4L2_TUNER_CAP_1HZ``，则使用 1 Hz 单位。
    * - __u32
      - ``reserved``\ [8]
      - 保留用于将来扩展。驱动程序和应用程序必须将数组清零

返回值
============

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    ``tuner`` 索引超出范围或 ``type`` 字段中的值不正确
EBUSY
    正在进行硬件查找
当然，请提供你需要翻译的文本。
