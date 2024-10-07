.. SPDX 许可证标识符: GPL-2.0

============
简介
============

本文档涵盖了视频和广播流设备使用的 Linux 内核到用户空间的 API，包括视频摄像头、模拟和数字电视接收卡、AM/FM 接收卡、软件定义无线电 (SDR)、流捕获和输出设备、编解码器设备及遥控器。一个典型的媒体设备硬件如图 :ref:`typical_media_device` 所示。

.. _typical_media_device:

.. kernel-figure:: typical_media_device.svg
    :alt: typical_media_device.svg
    :align: center

    典型的媒体设备

媒体基础设施 API 被设计用于控制此类设备。它分为五个部分：
1. 第一部分 :ref:`v4l2spec` 涵盖了广播、视频捕获和输出、摄像头、模拟电视设备和编解码器。
2. 第二部分 :ref:`dvbapi` 涵盖了通过多种数字电视标准进行数字电视和互联网接收所用的 API。虽然称为 DVB API，但实际上它涵盖了多个不同的视频标准，包括 DVB-T/T2、DVB-S/S2、DVB-C、ATSC、ISDB-T、ISDB-S、DTMB 等。支持的标准完整列表可以在 :c:type:`fe_delivery_system` 中找到。
3. 第三部分 :ref:`remote_controllers` 涵盖了遥控器 API。
4. 第四部分 :ref:`media_controller` 涵盖了媒体控制器 API。
5. 第五部分 :ref:`cec` 涵盖了 CEC（消费电子控制）API。

还应注意的是，媒体设备也可能包含音频组件，如混音器、PCM 捕获、PCM 播放等，这些组件通过 ALSA API 进行控制。更多详细信息和最新的开发代码，请参阅：`https://linuxtv.org <https://linuxtv.org>`__。为了讨论改进、报告问题、发送新驱动程序等，请发送邮件至：`Linux Media 邮件列表 (LMML) <http://vger.kernel.org/vger-lists.html#linux-media>`__。
