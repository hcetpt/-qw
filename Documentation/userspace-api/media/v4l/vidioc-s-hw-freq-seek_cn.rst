SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

c 命名空间:: V4L

.. _VIDIOC_S_HW_FREQ_SEEK:

***************************
ioctl VIDIOC_S_HW_FREQ_SEEK
***************************

名称
====

VIDIOC_S_HW_FREQ_SEEK - 执行硬件频率搜索

概要
========

.. c:macro:: VIDIOC_S_HW_FREQ_SEEK

``int ioctl(int fd, VIDIOC_S_HW_FREQ_SEEK, struct v4l2_hw_freq_seek *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_hw_freq_seek` 的指针
描述
===========

从当前频率开始执行硬件频率搜索。为此，应用程序需要初始化结构体 :c:type:`v4l2_hw_freq_seek` 中的 `tuner`、`type`、`seek_upward`、`wrap_around`、`spacing`、`rangelow` 和 `rangehigh` 字段，并将 `reserved` 数组清零，然后通过指向该结构体的指针调用 `VIDIOC_S_HW_FREQ_SEEK` ioctl。

`rangelow` 和 `rangehigh` 字段可以设置为非零值，以指示驱动程序搜索特定频段。如果结构体 :c:type:`v4l2_tuner` 的 `capability` 字段设置了 `V4L2_TUNER_CAP_HWSEEK_PROG_LIM` 标志，则这些值必须位于 :ref:`VIDIOC_ENUM_FREQ_BANDS` 返回的一个频段内。如果没有设置 `V4L2_TUNER_CAP_HWSEEK_PROG_LIM` 标志，则这些值必须与 :ref:`VIDIOC_ENUM_FREQ_BANDS` 返回的一个频段完全匹配。如果调谐器的当前频率不在选定的频段内，则在开始搜索之前会将其限制在此频段内。

如果返回错误，则恢复原始频率。
此 ioctl 在设置了 `V4L2_CAP_HW_FREQ_SEEK` 功能的情况下受支持。
如果从非阻塞文件句柄调用此 ioctl，则返回 `EAGAIN` 错误代码且不进行搜索。

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_hw_freq_seek

.. flat-table:: struct v4l2_hw_freq_seek
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``tuner``
      - 调谐器索引号。这是结构体 :c:type:`v4l2_input` 的 `tuner` 字段和结构体 :c:type:`v4l2_tuner` 的 `index` 字段中的相同值。
    * - __u32
      - ``type``
      - 调谐器类型。这是结构体 :c:type:`v4l2_tuner` 的 `type` 字段中的相同值。参见 :c:type:`v4l2_tuner_type`。
    * - __u32
      - ``seek_upward``
      - 如果非零，则从当前频率向上搜索，否则向下搜索。
    * - __u32
      - ``wrap_around``
      - 如果非零，在到达频率范围的末端时循环搜索，否则停止搜索。结构体 :c:type:`v4l2_tuner` 的 `capability` 字段将告诉您硬件支持的情况。
* - __u32
      - ``spacing``
      - 如果非零，定义硬件寻道分辨率（单位为 Hz）。驱动程序会选择设备支持的最接近的值。
      如果 `spacing` 为零，则使用一个合理的默认值。
* - __u32
      - ``rangelow``
      - 如果非零，表示要搜索频段中的最低可调频率（单位为 62.5 kHz），或者如果结构体
	:c:type:`v4l2_tuner` 的 ``capability`` 字段设置了
	``V4L2_TUNER_CAP_LOW`` 标志，则单位为 62.5 Hz；或者如果结构体
	:c:type:`v4l2_tuner` 的 ``capability`` 字段设置了
	``V4L2_TUNER_CAP_1HZ`` 标志，则单位为 1 Hz。如果 ``rangelow`` 为零，则使用一个合理的默认值。
* - __u32
      - ``rangehigh``
      - 如果非零，表示要搜索频段中的最高可调频率（单位为 62.5 kHz），或者如果结构体
	:c:type:`v4l2_tuner` 的 ``capability`` 字段设置了
	``V4L2_TUNER_CAP_LOW`` 标志，则单位为 62.5 Hz；或者如果结构体
	:c:type:`v4l2_tuner` 的 ``capability`` 字段设置了
	``V4L2_TUNER_CAP_1HZ`` 标志，则单位为 1 Hz。如果 ``rangehigh`` 为零，则使用一个合理的默认值。
* - __u32
      - ``reserved``\ [5]
      - 保留以供将来扩展。应用程序必须将数组设置为零。

返回值
======

成功时返回 0，出错时返回 -1，并且设置 `errno` 变量以指示错误原因。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EINVAL
    调谐器索引越界、`wrap_around` 值不受支持或 `type`、`rangelow` 或 `rangehigh` 字段中的某个值错误。
EAGAIN
    在非阻塞模式下尝试调用 `VIDIOC_S_HW_FREQ_SEEK`。
ENODATA
    硬件寻道未找到任何频道。
EBUSY
    另一个硬件寻道正在进行中。
当然，请提供您需要翻译的文本。
