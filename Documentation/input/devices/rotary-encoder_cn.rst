===============================================
旋转编码器 - 一个用于连接GPIO设备的通用驱动
===============================================

:作者: Daniel Mack <daniel@caiaq.de>, 2009年2月

功能
----

旋转编码器是通过两根线连接到CPU或其他外围设备的装置。输出信号相位差为90度，通过检测下降沿和上升沿可以确定旋转方向。
一些编码器在稳定状态下两个输出都处于低电平，而另一些编码器在稳定状态下也可能两个输出都处于高电平（半周期模式），还有一些在所有步骤中都有稳定状态（四分之一周期模式）。
这两个输出的相位图如下所示::

                  _____       _____       _____
                 |     |     |     |     |     |
  通道A  ____|     |_____|     |_____|     |____

                 :  :  :  :  :  :  :  :  :  :  :  :
            __       _____       _____       _____
              |     |     |     |     |     |     |
  通道B   |_____|     |_____|     |_____|     |__

                 :  :  :  :  :  :  :  :  :  :  :  :
  事件           a  b  c  d  a  b  c  d  a  b  c  d

                |<-------->|
	          一步

                |<-->|
	          一步（半周期模式）

                |<>|
	          一步（四分之一周期模式）

更多信息，请参见
	https://en.wikipedia.org/wiki/Rotary_encoder

事件/状态机
------------

在半周期模式下，状态a) 和 c) 用于根据上一个稳定状态来确定旋转方向。事件在状态b) 和 d) 中报告，前提是新的稳定状态与上一个不同（即旋转过程中没有中途反转）。
否则，以下规则适用：

a) 通道A上升沿，通道B处于低电平状态
	此状态用于识别顺时针旋转

b) 通道B上升沿，通道A处于高电平状态
	进入此状态时，编码器进入“预设”状态，这意味着它已经看到了一步转换的一半
c) 通道A下降沿，通道B处于高电平状态
	此状态用于识别逆时针旋转

d) 通道B下降沿，通道A处于低电平状态
	停车位置。如果编码器进入此状态，则应已完成一个完整的转换，除非它在一半处翻转。“预设”状态会告诉我们是否发生了这种情况

平台要求
---------

由于该驱动程序没有硬件相关的调用，因此所使用的平台必须支持gpiolib。另一个要求是中断必须能够在上升沿和下降沿触发。

板载集成
---------

要在您的系统中使用此驱动程序，请注册一个名为“rotary-encoder”的平台设备，并关联IRQ和一些特定的平台数据。因为该驱动程序使用通用设备属性，可以通过设备树、ACPI或静态板文件来完成，如下面的例子所示：

::

	/* 板级支持文件示例 */

	#include <linux/input.h>
	#include <linux/gpio/machine.h>
	#include <linux/property.h>

	#define GPIO_ROTARY_A 1
	#define GPIO_ROTARY_B 2

	static struct gpiod_lookup_table rotary_encoder_gpios = {
		.dev_id = "rotary-encoder.0",
		.table = {
			GPIO_LOOKUP_IDX("gpio-0",
					GPIO_ROTARY_A, NULL, 0, GPIO_ACTIVE_LOW),
			GPIO_LOOKUP_IDX("gpio-0",
					GPIO_ROTARY_B, NULL, 1, GPIO_ACTIVE_HIGH),
			{ },
		},
	};

	static const struct property_entry rotary_encoder_properties[] = {
		PROPERTY_ENTRY_U32("rotary-encoder,steps-per-period", 24),
		PROPERTY_ENTRY_U32("linux,axis",		      ABS_X),
		PROPERTY_ENTRY_U32("rotary-encoder,relative_axis",    0),
		{ },
	};

	static const struct software_node rotary_encoder_node = {
		.properties = rotary_encoder_properties,
	};

	static struct platform_device rotary_encoder_device = {
		.name		= "rotary-encoder",
		.id		= 0,
	};

	..
gpiod_add_lookup_table(&rotary_encoder_gpios);
	device_add_software_node(&rotary_encoder_device.dev, &rotary_encoder_node);
	platform_device_register(&rotary_encoder_device);

	..

请查阅设备树绑定文档以了解驱动程序支持的所有属性。
