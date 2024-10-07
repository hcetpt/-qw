SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _cec-intro:

简介
============

HDMI 连接器提供了一个引脚用于 Consumer Electronics Control（消费电子控制，简称 CEC）协议。此协议允许通过 HDMI 线缆连接的不同设备之间进行通信。CEC 版本 1.4 的协议定义在 HDMI 1.4a 规范 (:ref:`hdmi`) 的补充材料 1（CEC）和补充材料 2（HEAC 或 HDMI 以太网及音频回传通道）中，而 CEC 版本 2.0 中添加的扩展则定义在 HDMI 2.0 规范 (:ref:`hdmi2`) 的第 11 章中。比特率非常低（实际上每秒不超过 36 字节），并且基于旧的 SCART 连接器中使用的古老的 AV.link 协议。该协议与复杂的鲁布·戈德堡装置相似，是一种低级和高级消息的混合体。某些消息，特别是那些作为 CEC 上层的 HEAC 协议的一部分的消息，需要由内核处理，而其他消息可以由内核或用户空间处理。

此外，CEC 可以在 HDMI 接收器、发射器以及具有 HDMI 输入和输出并仅控制 CEC 引脚的 USB 设备中实现。支持 CEC 的驱动程序将创建一个 CEC 设备节点（/dev/cecX），以便用户空间能够访问 CEC 适配器。:ref:`CEC_ADAP_G_CAPS` ioctl 命令会告诉用户空间它被允许执行的操作。

为了检查支持情况并测试功能，建议下载 `v4l-utils <https://git.linuxtv.org/v4l-utils.git/>`_ 包。它提供了三个处理 CEC 的工具：

- cec-ctl：CEC 的瑞士军刀。允许您配置、传输和监控 CEC 消息。
- cec-compliance：对远程 CEC 设备进行 CEC 合规性测试，以确定其 CEC 实现的合规程度。
- cec-follower：模拟一个 CEC 跟随者。
