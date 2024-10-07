SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _radio:

***************
无线电接口
***************

此接口适用于 AM 和 FM（模拟）无线电接收器和发射器。
通常，V4L2 无线电设备通过名为 `/dev/radio` 和 `/dev/radio0` 到 `/dev/radio63` 的字符设备特殊文件访问，主设备号为 81，次设备号为 64 到 127。
查询功能
=====================

支持无线电接口的设备会在通过 `VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构体的 `capabilities` 字段中设置 `V4L2_CAP_RADIO` 和 `V4L2_CAP_TUNER` 或 `V4L2_CAP_MODULATOR` 标志。其他功能标志组合保留用于未来的扩展。
补充功能
======================

无线电设备可以支持 :ref:`controls <control>`，并且必须支持 :ref:`tuner or modulator <tuner>` ioctl。
它们不支持视频输入或输出、音频输入或输出、视频标准、裁剪和缩放、压缩和流参数以及覆盖 ioctl。所有其他 ioctl 和 I/O 方法保留用于未来的扩展。
编程
===========

无线电设备可能有几个音频控制（如 :ref:`control` 中所述），例如音量控制，可能还有自定义控制。
此外，所有无线电设备都有一个调谐器或调制器（在 :ref:`tuner` 中讨论），索引号为零，用于选择无线电频率并确定是否接收到/发出单声道或 FM 立体声节目。驱动程序会根据所选频率自动在 AM 和 FM 之间切换。`VIDIOC_G_TUNER <VIDIOC_G_TUNER>` 或 `VIDIOC_G_MODULATOR <VIDIOC_G_MODULATOR>` ioctl 报告支持的频率范围。
