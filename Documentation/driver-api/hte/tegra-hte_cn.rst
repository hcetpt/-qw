### SPDX 许可证标识符: GPL-2.0+

HTE 内核提供程序驱动程序
==========================

描述
-----------
Nvidia Tegra HTE 提供程序（也称为 GTE，通用时间戳引擎）驱动程序实现了两个 GTE 实例：1) GPIO GTE 和 2) LIC（传统中断控制器）IRQ GTE。这两个 GTE 实例均从系统计数器 TSC 获取时间戳，TSC 的时钟频率为 31.25 MHz，驱动程序在将时钟滴答率转换为纳秒并将其存储为时间戳值之前执行此操作。

GPIO GTE
--------

此 GTE 实例实时地对 GPIO 进行时间戳。为了实现这一点，GPIO 需要配置为输入模式。只有始终开启（AON）的 GPIO 控制器实例支持实时的时间戳 GPIO，因为它与 GPIO GTE 紧密关联。为此，GPIOLIB 添加了以下两个可选 API。GPIO GTE 代码同时支持内核空间和用户空间的消费者。内核空间的消费者可以直接与 HTE 子系统通信，而用户空间消费者的请求则通过 GPIOLIB CDEV 框架传递给 HTE 子系统。`Documentation/devicetree/bindings/timestamp` 中描述的 hte 设备树绑定提供了如何请求一个 GPIO 线路的示例。
请参阅 `gpiod_enable_hw_timestamp_ns()` 和 `gpiod_disable_hw_timestamp_ns()`。
对于用户空间的消费者，必须在 IOCTL 调用中指定 `GPIO_V2_LINE_FLAG_EVENT_CLOCK_HTE` 标志。参考 `tools/gpio/gpio-event-mon.c`，它返回以纳秒为单位的时间戳。

LIC（传统中断控制器）IRQ GTE
-----------------------------------------

此 GTE 实例实时地对 LIC IRQ 线路进行时间戳。`Documentation/devicetree/bindings/timestamp` 中描述的 hte 设备树绑定提供了如何请求一个 IRQ 线路的示例。由于它与 IRQ GTE 提供者之间是一对一映射，因此消费者只需指定他们感兴趣的 IRQ 编号即可。当前，在 HTE 框架中，此 GTE 实例不支持用户空间消费者。

这两个 IRQ 和 GPIO GTE 实例的提供程序源代码位于 `drivers/hte/hte-tegra194.c`。测试驱动程序 `drivers/hte/hte-tegra194-test.c` 展示了如何使用 HTE API 来处理 IRQ 和 GPIO GTE。
