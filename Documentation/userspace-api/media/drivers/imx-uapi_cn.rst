SPDX 许可证标识符: GPL-2.0

=========================
i.MX 视频采集驱动程序
=========================

事件
======

.. _imx_api_ipuX_csiY:

ipuX_csiY
---------

当启用第二个 IDMAC 源端口时，此子设备可以生成以下事件：

- V4L2_EVENT_IMX_FRAME_INTERVAL_ERROR

用户应用程序可以从 ipuX_csiY 子设备节点订阅此事件。该事件由帧间隔监视器（FIM）生成，详见下文。

控制
========

.. _imx_api_FIM:

ipuX_csiY 中的帧间隔监视器（FIM）
-----------------------------------

adv718x 解码器在 NTSC/PAL 信号重新同步期间偶尔会发送错误字段（视频行过少或过多）。在这种情况下，IPU 会触发一个机制来通过每帧增加一行虚拟线来重新建立垂直同步。这会导致图像滚动，并且可能需要很长时间才能恢复稳定图像。有时这种机制根本不起作用，导致永久性分裂图像（一帧包含两个连续捕获图像的行）。

实验发现，在图像滚动期间，帧间隔（两次 EOF 之间的时间差）会低于当前标准下的标称值，大约减少了一个帧时间（60 微秒），并保持这个值直到滚动停止。

尽管不清楚这一现象的原因（IPU 虚拟线机制应该会在每个帧中增加一行时间而不是固定值），但我们可以利用帧间隔监视器（FIM）来检测这些错误字段。如果 FIM 检测到不良帧间隔，ipuX_csiY 子设备将发送 V4L2_EVENT_IMX_FRAME_INTERVAL_ERROR 事件。用户空间可以通过 ipuX_csiY 子设备设备节点注册 FIM 事件通知。

当收到此事件时，用户空间可以重新启动流传输以纠正滚动/分裂图像。

ipuX_csiY 子设备包括自定义控件，用于调整 FIM 的一些参数。如果在流传输过程中更改了其中一个控件，FIM 将重置并继续使用新设置。

- V4L2_CID_IMX_FIM_ENABLE

启用/禁用 FIM。
- V4L2_CID_IMX_FIM_NUM

在与传感器报告的标称帧间隔进行比较之前，平均多少个帧间隔测量值。这可以减少由于中断延迟引起的噪声。
- V4L2_CID_IMX_FIM_TOLERANCE_MIN

如果平均间隔超出标称值的这个数量（微秒），则发送 V4L2_EVENT_IMX_FRAME_INTERVAL_ERROR 事件。
- V4L2_CID_IMX_FIM_TOLERANCE_MAX

如果任何间隔高于此值，则丢弃这些样本，不计入平均值。这可用于丢弃因高系统负载引起的极高间隔错误。
### V4L2_CID_IMX_FIM_NUM_SKIP

在 FIM 重置或流重启后开始平均间隔之前要跳过的帧数。

### V4L2_CID_IMX_FIM_ICAP_CHANNEL / V4L2_CID_IMX_FIM_ICAP_EDGE

这些控制将配置一个输入捕获通道作为测量帧间隔的方法。这种方法优于默认的通过 EOF 中断来测量帧间隔的方法，因为它不会受到中断延迟引入的不确定性误差的影响。
输入捕获需要硬件支持。必须将 VSYNC 信号路由到 i.MX6 的某个输入捕获通道引脚上。
`V4L2_CID_IMX_FIM_ICAP_CHANNEL` 配置使用哪个 i.MX6 输入捕获通道。这必须是 0 或 1。
`V4L2_CID_IMX_FIM_ICAP_EDGE` 配置触发输入捕获事件的信号边沿。默认情况下，输入捕获方法是禁用的，值为 `IRQ_TYPE_NONE`。将此控制设置为 `IRQ_TYPE_EDGE_RISING`、`IRQ_TYPE_EDGE_FALLING` 或 `IRQ_TYPE_EDGE_BOTH` 以启用输入捕获，并根据给定的信号边沿触发。

当输入捕获被禁用时，帧间隔将通过 EOF 中断来测量。

### 文件列表
```
drivers/staging/media/imx/
include/media/imx.h
include/linux/imx-media.h
```

### 作者
- Steve Longerbeam <steve_longerbeam@mentor.com>
- Philipp Zabel <kernel@pengutronix.de>
- Russell King <linux@armlinux.org.uk>

### 版权
版权所有 © 2012-2017 Mentor Graphics Inc
