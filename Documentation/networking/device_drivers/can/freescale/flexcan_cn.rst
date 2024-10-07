SPDX 许可证标识符: GPL-2.0+

=============================
Flexcan CAN 控制器驱动程序
=============================

作者: Marc Kleine-Budde <mkl@pengutronix.de>,
Dario Binacchi <dario.binacchi@amarulasolutions.com>

RTR 帧的接收开关功能
===========================

对于大多数 Flexcan IP 核心，该驱动支持两种接收模式：

- FIFO（先进先出）
- 邮箱模式

较旧的 Flexcan 核心（集成在 i.MX25、i.MX28、i.MX35 和 i.MX53 SOC 中）只有在控制器配置为 RX-FIFO 模式时才能接收到 RTR 帧。
RX FIFO 模式使用硬件 FIFO，深度为 6 个 CAN 帧，而邮箱模式使用软件 FIFO，深度最多可达 62 个 CAN 帧。借助更大的缓冲区，在系统负载较高的情况下，邮箱模式表现更好。

由于 RTR 帧的接收是 CAN 标准的一部分，所有 Flexcan 核心默认都处于可以接收 RTR 帧的状态。
通过使用“rx-rtr”私有标志，可以在放弃接收 RTR 帧的能力的情况下进行权衡。这种权衡在某些用例中是有益的。

"rx-rtr" 开
  接收 RTR 帧。（默认）

  CAN 控制器能够并会接收 RTR 帧。
在某些 IP 核心中，控制器无法在性能更高的“RX 邮箱”模式下接收 RTR 帧，而是会使用“RX FIFO”模式。
"rx-rtr" 关
  放弃接收 RTR 帧的能力。（并非所有 IP 核心都支持）

  此模式激活“RX 邮箱模式”，以获得更好的性能。在某些 IP 核心中，将无法再接收 RTR 帧。
只有在网络接口关闭的情况下才能更改此设置：

    ip link set dev can0 down
    ethtool --set-priv-flags can0 rx-rtr {off|on}
    ip link set dev can0 up
