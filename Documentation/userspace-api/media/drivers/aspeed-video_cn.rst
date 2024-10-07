SPDX 许可证标识符: GPL-2.0

.. include:: <isonum.txt>

ASPEED 视频驱动程序
===================

ASPEED 视频引擎在 AST2400/2500/2600 系统级芯片 (SoC) 上支持高性能视频压缩，并提供广泛的视频质量和压缩比选项。所采用的压缩算法是一种改进的 JPEG 算法。此 IP 中有两种类型的压缩：
* JPEG JFIF 标准模式：用于单帧和管理压缩
* ASPEED 专有模式：用于多帧和差分压缩
支持两遍（高质量）视频压缩方案（ASPEED 专利待审）。提供视觉无损视频压缩质量或减少局域网 KVM 应用中的网络平均负载。
可以通过 `VIDIOC_S_FMT` 来选择所需的格式。`V4L2_PIX_FMT_JPEG` 表示 JPEG JFIF 标准模式；`V4L2_PIX_FMT_AJPG` 表示 ASPEED 专有模式。
更多关于 ASPEED 视频硬件操作的详细信息可以在 SDK 用户指南的 *第 6.2.16 章 KVM 视频驱动程序* 中找到，该文档可在 `github <https://github.com/AspeedTech-BMC/openbmc/releases/>`__ 上获取。

ASPEED 视频驱动程序实现了以下特定于驱动程序的控制：

``V4L2_CID_ASPEED_HQ_MODE``
---------------------------
启用/禁用 ASPEED 的高质量模式。这是一个私有控制，可用于启用 ASPEED 专有模式下的高质量。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 4

    * - ``(0)``
      - 禁用 ASPEED 高质量模式
    * - ``(1)``
      - 启用 ASPEED 高质量模式

``V4L2_CID_ASPEED_HQ_JPEG_QUALITY``
-----------------------------------
定义 ASPEED 高质量模式的质量。这是一个私有控制，如果启用了高质量模式，可以用来决定压缩质量。值越高，质量越好，文件大小也越大。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 4

    * - ``(1)``
      - 最小值
    * - ``(12)``
      - 最大值
    * - ``(1)``
      - 步长
    * - ``(1)``
      - 默认值

**版权** © 2022 ASPEED Technology Inc
