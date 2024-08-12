串行外设接口 (SPI)
==================

SPI 是“串行外设接口”的简称，在嵌入式系统中广泛使用，因为它是一种简单而高效的接口：基本上是一个多路复用的移位寄存器。它的三条信号线分别用于时钟（SCK，通常在1-20 MHz范围内）、“主出从入”（MOSI）数据线和“主入从出”（MISO）数据线。SPI是全双工协议；对于每个通过MOSI线移出的比特（每个时钟一个比特），另一个比特会从MISO线上移入。这些比特被组装成不同大小的数据块，并传输到系统内存。通常还有一条低电平有效的片选线（nCS）；对于每个外设通常需要四条信号线，有时还包括中断信号。

这里列出的SPI总线设施提供了一个通用接口来声明SPI总线和设备、根据标准的Linux驱动模型管理它们并执行输入/输出操作。目前仅支持“主端”接口，即Linux与SPI外设通信而不实现这样的外设本身。（为了支持SPI从设备的实现，接口必然看起来有所不同。）

编程接口围绕两种类型的驱动程序和两种类型的设备构建。一个“控制器驱动程序”抽象了控制器硬件，它可以像一组GPIO引脚那样简单，也可以像连接在SPI移位寄存器另一侧的一对FIFO与双DMA引擎那样复杂（以最大化吞吐量）。此类驱动程序在它们所在的总线（通常是平台总线）和SPI之间架起桥梁，并将其设备的SPI一侧暴露为 :c:type:`struct spi_controller <spi_controller>`。SPI设备是该主设备的子设备，表示为 :c:type:`struct spi_device <spi_device>`，并从 :c:type:`struct spi_board_info <spi_board_info>` 描述符中创建，这些描述符通常由特定于板卡的初始化代码提供。:c:type:`struct spi_driver <spi_driver>` 被称为“协议驱动程序”，并使用标准驱动模型调用来绑定到 `spi_device`。

I/O模型是一组排队的消息。协议驱动程序提交一个或多个 :c:type:`struct spi_message <spi_message>` 对象，这些对象会被异步处理和完成。（但是也存在同步包装器。）消息由一个或多个 :c:type:`struct spi_transfer <spi_transfer>` 对象构成，每个对象封装一个全双工SPI传输。由于不同的芯片采用非常不同的策略来使用通过SPI传输的比特，因此需要多种协议调整选项。
.. kernel-doc:: include/linux/spi/spi.h
   :internal:

.. kernel-doc:: drivers/spi/spi.c
   :functions: spi_register_board_info

.. kernel-doc:: drivers/spi/spi.c
   :export:
