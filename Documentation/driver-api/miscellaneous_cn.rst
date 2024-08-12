平行端口设备
=====================

.. kernel-doc:: include/linux/parport.h
   :internal:

.. kernel-doc:: drivers/parport/ieee1284.c
   :export:

.. kernel-doc:: drivers/parport/share.c
   :export:

.. kernel-doc:: drivers/parport/daisy.c
   :internal:

16x50 UART 驱动程序
=================

.. kernel-doc:: drivers/tty/serial/8250/8250_core.c
   :export:

请参阅 serial/driver.rst 获取相关 API 信息
脉冲宽度调制 (PWM)
============================

脉冲宽度调制是一种主要用于控制供给电气设备的电力的技术。
PWM 框架为 PWM 信号的提供者和消费者提供了抽象层。一个提供一个或多个 PWM 信号的控制器被注册为 :c:type:`struct pwm_chip <pwm_chip>`。提供者需要将此结构嵌入到驱动程序特定的结构中。
此结构包含描述特定芯片的字段。
一个芯片暴露一个或多个 PWM 信号源，每个信号源都作为一个 :c:type:`struct pwm_device <pwm_device>` 被暴露。可以对 PWM 设备执行操作以控制信号的周期、占空比、极性和活动状态。
请注意，PWM 设备是独占资源：它们始终只能同时被一个消费者使用。

.. kernel-doc:: include/linux/pwm.h
   :internal:

.. kernel-doc:: drivers/pwm/core.c
   :export:
