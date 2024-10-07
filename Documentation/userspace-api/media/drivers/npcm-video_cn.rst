SPDX 许可声明标识符: GPL-2.0

.. include:: <isonum.txt>

NPCM 视频驱动程序
=================

此驱动程序用于控制 Nuvoton NPCM 系统级芯片 (SoC) 上的视频采集/差异化 (VCD) 引擎和编码压缩引擎 (ECE)。VCD 可以从数字视频输入中捕获一帧，并在内存中比较两帧，而 ECE 可以将帧数据压缩为 HEXTILE 格式。

驱动程序特定的控制项
------------------------

V4L2_CID_NPCM_CAPTURE_MODE
~~~~~~~~~~~~~~~~~~~~~~~~~~

VCD 引擎支持两种模式：

- COMPLETE 模式：

  将下一整帧捕获到内存中。
- DIFF 模式：

  将传入的帧与存储在内存中的帧进行比较，并更新内存中的差异帧。

应用程序可以使用 `V4L2_CID_NPCM_CAPTURE_MODE` 控制来设置 VCD 模式，通过不同的控制值（枚举类型 v4l2_npcm_capture_mode）：

- `V4L2_NPCM_CAPTURE_MODE_COMPLETE`：将 VCD 设置为 COMPLETE 模式。
- `V4L2_NPCM_CAPTURE_MODE_DIFF`：将 VCD 设置为 DIFF 模式。

V4L2_CID_NPCM_RECT_COUNT
~~~~~~~~~~~~~~~~~~~~~~~~

如果使用 V4L2_PIX_FMT_HEXTILE 格式，VCD 将捕获帧数据，然后 ECE 将数据压缩为 HEXTILE 矩形并按照远程帧缓冲协议定义的布局将其存储在 V4L2 视频缓冲区中：
::

           （RFC 6143，https://www.rfc-editor.org/rfc/rfc6143.html#section-7.6.1）

           +--------------+--------------+-------------------+
           | 字节数       | 类型 [值]     | 描述               |
           +--------------+--------------+-------------------+
           | 2            | U16          | X 坐标             |
           | 2            | U16          | Y 坐标             |
           | 2            | U16          | 宽度               |
           | 2            | U16          | 高度               |
           | 4            | S32          | 编码类型 (5)       |
           +--------------+--------------+-------------------+
           |             HEXTILE 矩形数据               |
           +--------------------------------------------+

应用程序可以通过 VIDIOC_DQBUF 获取视频缓冲区，然后调用 `V4L2_CID_NPCM_RECT_COUNT` 控制来获取该缓冲区中的 HEXTILE 矩形数量。

参考文献
----------
include/uapi/linux/npcm-video.h

**版权** |copy| 2022 Nuvoton Technologies
