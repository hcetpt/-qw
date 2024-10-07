SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_DECODER_CMD:

************************************************
ioctl VIDIOC_DECODER_CMD, VIDIOC_TRY_DECODER_CMD
************************************************

名称
====

VIDIOC_DECODER_CMD - VIDIOC_TRY_DECODER_CMD - 执行解码器命令

概述
========

.. c:macro:: VIDIOC_DECODER_CMD

``int ioctl(int fd, VIDIOC_DECODER_CMD, struct v4l2_decoder_cmd *argp)``

.. c:macro:: VIDIOC_TRY_DECODER_CMD

``int ioctl(int fd, VIDIOC_TRY_DECODER_CMD, struct v4l2_decoder_cmd *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_decoder_cmd` 的指针
描述
===========

这些 ioctl 控制音频/视频（通常是 MPEG-）解码器。
``VIDIOC_DECODER_CMD`` 向解码器发送一个命令，
``VIDIOC_TRY_DECODER_CMD`` 可用于尝试一个命令而不实际执行它。要发送一个命令，应用程序必须初始化结构体 :c:type:`v4l2_decoder_cmd` 的所有字段，并使用指向该结构体的指针调用 ``VIDIOC_DECODER_CMD`` 或 ``VIDIOC_TRY_DECODER_CMD``。
``cmd`` 字段必须包含命令代码。某些命令使用 ``flags`` 字段来提供额外信息。
一个 :c:func:`write()` 或 :ref:`VIDIOC_STREAMON` 调用会在解码器尚未启动时隐式地向解码器发送一个 START 命令。这适用于 mem2mem 解码器的两个队列。
一个 :c:func:`close()` 或 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 调用会向流文件描述符发送一个隐式的立即 STOP 命令给解码器，并丢弃所有缓冲的数据。这也适用于 mem2mem 解码器的两个队列。
原则上，这些 ioctl 是可选的，并非所有驱动程序都支持它们。它们是在 Linux 3.3 中引入的。然而，对于状态化的 mem2mem 解码器来说，它们是强制性的（如在 :ref:`decoder` 中进一步说明）。

.. tabularcolumns:: |p{2.0cm}|p{1.1cm}|p{2.2cm}|p{11.8cm}|

.. c:type:: v4l2_decoder_cmd

.. cssclass:: longtable

.. flat-table:: struct v4l2_decoder_cmd
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 1 1 3

    * - __u32
      - ``cmd``
      -
      - 解码器命令，见 :ref:`decoder-cmds`
* - __u32
      - ``flags``
      -
      - 与命令相关的标志。如果此命令没有定义任何标志，则驱动程序和应用程序必须将此字段设置为零
```markdown
* - union {
      - (匿名)
    * - struct
      - ``start``
      -
      - 包含用于 ``V4L2_DEC_CMD_START`` 命令的附加数据的结构体
* -
      - __s32
      - ``speed``
      - 播放速度和方向。播放速度定义为正常速度的 ``speed``/1000。因此，1000 表示正常播放。负数表示倒播，例如 -1000 表示以正常速度倒播。速度值 -1、0 和 1 具有特殊含义：速度 0 是 1000（正常播放）的简写；速度为 1 时仅前进一帧；速度为 -1 时仅后退一帧。
* -
      - __u32
      - ``format``
      - 格式限制。此字段由驱动程序设置，而非应用程序。可能的值包括 ``V4L2_DEC_START_FMT_NONE``（无格式限制）或 ``V4L2_DEC_START_FMT_GOP``（解码器在完整的 GOP（图像组）上操作）。通常情况下，倒播需要完整的 GOP，然后可以按倒序播放。因此，要实现倒播，应用程序必须向解码器提供视频文件中的最后一个 GOP，然后是之前的 GOP 等等。
* - struct
      - ``stop``
      -
      - 包含用于 ``V4L2_DEC_CMD_STOP`` 命令的附加数据的结构体
* -
      - __u64
      - ``pts``
      - 在此 ``pts`` 处停止播放，或如果播放已超过该时间戳则立即停止。如果希望在最后一帧解码后停止，则将其设为 0。
* - struct
      - ``raw``
    * -
      - __u32
      - ``data``[16]
      - 保留供将来扩展使用。驱动程序和应用程序必须将数组设为零
* - }
      -

.. tabularcolumns:: |p{5.6cm}|p{0.6cm}|p{11.1cm}|

.. cssclass:: longtable

.. _decoder-cmds:

.. flat-table:: 解码器命令
    :header-rows:  0
    :stub-columns: 0
    :widths: 56 6 113

    * - ``V4L2_DEC_CMD_START``
      - 0
      - 启动解码器。当解码器已经在运行或暂停时，此命令只会改变播放速度。这意味着在解码器暂停时调用 ``V4L2_DEC_CMD_START`` 不会恢复解码器。您必须显式调用 ``V4L2_DEC_CMD_RESUME`` 来恢复解码器。此命令有一个标志：``V4L2_DEC_CMD_START_MUTE_AUDIO``。如果设置了该标志，在非标准速度播放时音频将被静音。对于实现了 :ref:`decoder` 的设备，一旦通过 ``V4L2_DEC_CMD_STOP`` 命令启动了排空序列，必须在完成排空序列后再调用此命令。在排空序列进行中尝试调用此命令将触发 ``EBUSY`` 错误代码。此命令也可以用于重启解码器，尤其是在解码器本身隐式停止而未显式调用 ``V4L2_DEC_CMD_STOP`` 的情况下。更多详细信息请参见 :ref:`decoder`。
* - ``V4L2_DEC_CMD_STOP``
      - 1
      - 停止解码器。当解码器已经停止时，此命令不执行任何操作。此命令有两个标志：如果设置了 ``V4L2_DEC_CMD_STOP_TO_BLACK``，则解码器停止解码后会将画面设为黑色。否则，最后的画面将重复显示。如果设置了 ``V4L2_DEC_CMD_STOP_IMMEDIATELY``，则解码器立即停止（忽略 ``pts`` 值），否则将继续解码直到时间戳 >= pts 或直到其内部缓冲区中的待处理数据被完全解码。
```
对于实现了 :ref:`解码器` 的设备，该命令将启动排水序列，具体文档参见 :ref:`解码器`。在这种情况下不接受任何标志或其他参数。在序列完成之前再次尝试调用该命令将触发 ``EBUSY`` 错误代码。

* - ``V4L2_DEC_CMD_PAUSE``
  - 2
  - 暂停解码器。当解码器尚未启动时，驱动程序将返回一个 ``EPERM`` 错误代码。当解码器已经暂停时，此命令不执行任何操作。此命令有一个标志：如果设置了 ``V4L2_DEC_CMD_PAUSE_TO_BLACK``，则在暂停时将解码器输出设置为黑色。
* - ``V4L2_DEC_CMD_RESUME``
  - 3
  - 在 PAUSE 命令后恢复解码。当解码器尚未启动时，驱动程序将返回一个 ``EPERM`` 错误代码。当解码器已经在运行时，此命令不执行任何操作。此命令没有定义任何标志。
* - ``V4L2_DEC_CMD_FLUSH``
  - 4
  - 清空任何待处理的捕获缓冲区。仅对无状态解码器有效。此命令通常用于应用程序到达流末尾且最后一个输出缓冲区设置了 ``V4L2_BUF_FLAG_M2M_HOLD_CAPTURE_BUF`` 标志的情况。这会阻止从队列中删除包含最后一个解码帧的捕获缓冲区。因此，可以使用此命令显式地清空该最终解码帧。如果没有待处理的捕获缓冲区，则此命令不执行任何操作。

返回值
======

成功时返回 0，错误时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。

- **EBUSY**：实现 :ref:`解码器` 的设备的排水序列仍在进行中。在此期间不允许发出另一个解码器命令。
- **EINVAL**：`cmd` 字段无效。
- **EPERM**：应用程序在解码器未运行时发送了 PAUSE 或 RESUME 命令。
当然，请提供你需要翻译的文本。
