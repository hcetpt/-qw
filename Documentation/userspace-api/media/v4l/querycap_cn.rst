SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _querycap:

*********************
查询功能
*********************

由于 V4L2 覆盖了各种不同的设备，并非所有 API 方面都同样适用于所有类型的设备。此外，相同类型的设备也有不同的功能，本规范允许省略一些复杂且不太重要的 API 部分。:ref:`VIDIOC_QUERYCAP` ioctl 可用于检查内核设备是否与本规范兼容，并查询设备所支持的 :ref:`函数 <devices>` 和 :ref:`I/O 方法 <io>`。

从内核版本 3.1 开始，:ref:`VIDIOC_QUERYCAP` 将返回驱动程序使用的 V4L2 API 版本，这通常与内核版本相匹配。无需使用 :ref:`VIDIOC_QUERYCAP` 来检查是否支持特定的 ioctl，V4L2 核心现在会在驱动程序不支持某个 ioctl 时返回 ``ENOTTY``。

其他特性可以通过调用相应的 ioctl 进行查询，例如，可以使用 :ref:`VIDIOC_ENUMINPUT` 来了解设备上的视频连接器的数量、类型和名称。尽管抽象是此 API 的主要目标之一，:ref:`VIDIOC_QUERYCAP` ioctl 也允许特定于驱动程序的应用程序可靠地识别驱动程序。

所有 V4L2 驱动程序必须支持 :ref:`VIDIOC_QUERYCAP`。应用程序在打开设备后应始终调用此 ioctl。
