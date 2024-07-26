... SPDX 许可证标识符: GPL-2.0+ 

================================
Flexcan CAN 控制器驱动程序
================================

作者: Marc Kleine-Budde <mkl@pengutronix.de>,
Dario Binacchi <dario.binacchi@amarulasolutions.com>

启用/禁用 RTR 帧接收
==========================

对于大多数 Flexcan IP 核心，该驱动程序支持两种接收模式：

- FIFO（先进先出）
- 邮箱

较旧的 Flexcan 核心（集成到 i.MX25、i.MX28、i.MX35 和 i.MX53 SOC 中）只有在控制器配置为 RX-FIFO 模式时才会接收 RTR 帧。
RX FIFO 模式使用一个硬件 FIFO，其深度为 6 个 CAN 帧，而邮箱模式使用一个软件 FIFO，其深度最多可达 62 个 CAN 帧。借助更大的缓冲区，在系统负载较高情况下，邮箱模式表现更好。

由于接收 RTR 帧是 CAN 标准的一部分，所有 Flexcan 核心都默认处于能够接收 RTR 帧的状态。

通过“rx-rtr”私有标志可以在牺牲接收 RTR 消息的能力的情况下放弃接收 RTR 帧的能力。这种权衡在某些使用案例中是有益的。

"rx-rtr" 开启
  接收 RTR 帧。（默认）

  CAN 控制器可以并且将会接收 RTR 帧。
在某些 IP 核心上，控制器无法在性能更好的“RX 邮箱”模式下接收 RTR 帧，而将使用“RX FIFO”模式。

"rx-rtr" 关闭
  放弃接收 RTR 帧的能力。（并非所有 IP 核心均支持）

  此模式激活“RX 邮箱模式”以获得更好的性能，在某些 IP 核心上无法再接收 RTR 帧。
只有在接口关闭的情况下才能更改此设置：

    ip link set dev can0 down
    ethtool --set-priv-flags can0 rx-rtr {off|on}
    ip link set dev can0 up
