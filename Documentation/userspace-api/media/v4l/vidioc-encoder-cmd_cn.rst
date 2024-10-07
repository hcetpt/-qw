SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. c:namespace:: V4L

.. _VIDIOC_ENCODER_CMD:

************************************************
ioctl VIDIOC_ENCODER_CMD, VIDIOC_TRY_ENCODER_CMD
************************************************

名称
====

VIDIOC_ENCODER_CMD - VIDIOC_TRY_ENCODER_CMD - 执行编码器命令

概述
========

.. c:macro:: VIDIOC_ENCODER_CMD

``int ioctl(int fd, VIDIOC_ENCODER_CMD, struct v4l2_encoder_cmd *argp)``

.. c:macro:: VIDIOC_TRY_ENCODER_CMD

``int ioctl(int fd, VIDIOC_TRY_ENCODER_CMD, struct v4l2_encoder_cmd *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_encoder_cmd` 结构体的指针
描述
===========

这些 ioctl 控制音频/视频（通常是 MPEG-）编码器。
``VIDIOC_ENCODER_CMD`` 向编码器发送一个命令，
``VIDIOC_TRY_ENCODER_CMD`` 可用于尝试一个命令而不实际执行它。
要发送一个命令，应用程序必须初始化一个 :c:type:`v4l2_encoder_cmd` 结构体的所有字段，并通过指向该结构体的指针调用 ``VIDIOC_ENCODER_CMD`` 或 ``VIDIOC_TRY_ENCODER_CMD``。
``cmd`` 字段必须包含命令代码。某些命令使用 ``flags`` 字段来传递额外的信息。
在 STOP 命令之后，:c:func:`read()` 调用将读取驱动程序缓冲区中剩余的数据。当缓冲区为空时，:c:func:`read()` 将返回零，并且下一个 :c:func:`read()` 调用将重新启动编码器。
一个 :c:func:`read()` 或 :ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>` 调用如果编码器尚未启动，则会隐式地发送一个 START 命令给编码器。这适用于 mem2mem 编码器的两个队列。
一个 :c:func:`close()` 或 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 调用对流文件描述符会隐式地立即停止编码器，并丢弃所有缓冲数据。这也适用于 mem2mem 编码器的两个队列。

这些 ioctl 是可选的，不是所有驱动程序都支持它们。它们是在 Linux 2.6.21 中引入的。然而，对于状态化的 mem2mem 编码器来说，它们是强制性的（如在 :ref:`encoder` 中进一步说明）。
```markdown
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_encoder_cmd

.. flat-table:: 结构体 v4l2_encoder_cmd
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``cmd``
      - 编码器命令，参见 :ref:`encoder-cmds`
* - __u32
      - ``flags``
      - 与命令相关的标志，参见 :ref:`encoder-flags`。如果此命令没有定义任何标志，则驱动程序和应用程序必须将该字段设置为零
* - __u32
      - ``data``\[8\]
      - 保留用于将来扩展。驱动程序和应用程序必须将数组设置为零
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _encoder-cmds:

.. flat-table:: 编码器命令
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_ENC_CMD_START``
      - 0
      - 启动编码器。当编码器已经在运行或暂停时，此命令不执行任何操作。此命令没有定义任何标志
对于实现 :ref:`encoder` 的设备，在使用 ``V4L2_ENC_CMD_STOP`` 命令启动排水序列之前，必须完成该命令。在排水序列进行期间尝试调用此命令将触发 ``EBUSY`` 错误代码。更多详情请参见 :ref:`encoder`
* - ``V4L2_ENC_CMD_STOP``
      - 1
      - 停止编码器。当设置了 ``V4L2_ENC_CMD_STOP_AT_GOP_END`` 标志时，编码将继续到当前 *Group Of Pictures* 的结束，否则编码将立即停止。当编码器已经停止时，此命令不执行任何操作
对于实现 :ref:`encoder` 的设备，此命令将启动如 :ref:`encoder` 中所述的排水序列。在这种情况下不接受任何标志或其他参数。在序列完成之前再次尝试调用此命令将触发 ``EBUSY`` 错误代码
* - ``V4L2_ENC_CMD_PAUSE``
      - 2
      - 暂停编码器。当编码器尚未启动时，驱动程序将返回 ``EPERM`` 错误代码。当编码器已经暂停时，此命令不执行任何操作。此命令没有定义任何标志
* - ``V4L2_ENC_CMD_RESUME``
      - 3
      - 在 PAUSE 命令后恢复编码。当编码器尚未启动时，驱动程序将返回 ``EPERM`` 错误代码。当编码器已经在运行时，此命令不执行任何操作。此命令没有定义任何标志
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _encoder-flags:

.. flat-table:: 编码器命令标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_ENC_CMD_STOP_AT_GOP_END``
      - 0x0001
      - 在当前 *Group Of Pictures* 的结束时停止编码，而不是立即停止
```
不适用于 :ref:`编码器`

返回值
======

成功时返回 0，错误时返回 -1 并且设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。

EBUSY
    实现 :ref:`编码器` 的设备的清空序列仍在进行中。在它完成之前不允许发出另一个编码命令。
EINVAL
    ``cmd`` 字段无效。
EPERM
    应用程序在编码器未运行时发送了 PAUSE 或 RESUME 命令。
