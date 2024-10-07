SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _rf-tuner-controls:

**************************
RF 调谐器控制参考
**************************

RF 调谐器 (RF_TUNER) 类别包括了具有 RF 调谐器功能设备的常见控制。在此上下文中，RF 调谐器是指天线和解调器之间的无线电接收电路。它从天线接收射频 (RF) 信号，并将接收到的信号转换为较低的中频 (IF) 或基带频率 (BB)。能够输出基带信号的调谐器通常被称为零中频 (Zero-IF) 调谐器。旧的调谐器通常是金属盒内的简单 PLL 调谐器，而新的调谐器是高度集成的芯片，没有金属盒，称为“硅调谐器”。这些控制主要适用于具有丰富新特性的硅调谐器，因为旧的调谐器没有太多可调节的功能。

更多关于 RF 调谐器的信息，请参见维基百科上的 `调谐器（无线电）<http://en.wikipedia.org/wiki/Tuner_(radio)>`__ 和 `射频前端<http://en.wikipedia.org/wiki/RF_front_end>`__。

.. _rf-tuner-control-id:

RF_TUNER 控制 ID
====================

``V4L2_CID_RF_TUNER_CLASS (类别)``
    RF_TUNER 类别的描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回该控制类别的描述。
``V4L2_CID_RF_TUNER_BANDWIDTH_AUTO (布尔值)``
    启用/禁用调谐器无线频道带宽配置。在自动模式下，带宽配置由驱动程序完成。
``V4L2_CID_RF_TUNER_BANDWIDTH (整数)``
    调谐器信号路径中的滤波器用于根据接收方的需求过滤信号。当驱动程序配置滤波器以满足所需的带宽要求时使用。当未设置 V4L2_CID_RF_TUNER_BANDWIDTH_AUTO 时使用。单位为 Hz。范围和步长取决于驱动程序。
``V4L2_CID_RF_TUNER_LNA_GAIN_AUTO (布尔值)``
    启用/禁用低噪声放大器 (LNA) 的自动增益控制 (AGC)。
``V4L2_CID_RF_TUNER_MIXER_GAIN_AUTO (布尔值)``
    启用/禁用混频器的自动增益控制 (AGC)。
``V4L2_CID_RF_TUNER_IF_GAIN_AUTO (布尔值)``
    启用/禁用中频 (IF) 的自动增益控制 (AGC)。
``V4L2_CID_RF_TUNER_RF_GAIN (整数)``
    射频放大器是接收信号路径中的第一个放大器，紧接在天线输入之后。本文档中 LNA 增益与 RF 增益的区别在于 LNA 增益集成在调谐器芯片内，而 RF 增益是单独的芯片。同一设备中可能同时存在 RF 和 LNA 增益控制。范围和步长取决于驱动程序。
``V4L2_CID_RF_TUNER_LNA_GAIN (整数)``
    低噪声放大器 (LNA) 增益是 RF 调谐器信号路径中的第一个增益级。它位于调谐器天线输入附近。当未设置 V4L2_CID_RF_TUNER_LNA_GAIN_AUTO 时使用。请参见 V4L2_CID_RF_TUNER_RF_GAIN 了解 RF 增益和 LNA 增益之间的区别。范围和步长取决于驱动程序。
``V4L2_CID_RF_TUNER_MIXER_GAIN (整数)``
    混频器增益是 RF 调谐器信号路径中的第二个增益级。它位于混频器内部，在 RF 信号被混频器下变频的地方。当未设置 V4L2_CID_RF_TUNER_MIXER_GAIN_AUTO 时使用。
``V4L2_CID_RF_TUNER_IF_GAIN (整数)``
    IF 增益是 RF 调谐器信号路径上的最后一个增益阶段。它位于 RF 调谐器的输出端。它控制中频输出或基带输出的信号电平。在未设置 ``V4L2_CID_RF_TUNER_IF_GAIN_AUTO`` 时使用。范围和步长是驱动程序特定的。

``V4L2_CID_RF_TUNER_PLL_LOCK (布尔)``
    合成器的 PLL 是否锁定？当设置该控制时，RF 调谐器正在接收给定的频率。这是一个只读控制。
