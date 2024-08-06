==========================
内核驱动 i2c-mux-gpio
==========================

作者: Peter Korsgaard <peter.korsgaard@barco.com>

描述
-----------

i2c-mux-gpio 是一个 I2C 复用器驱动程序，它提供从主 I2C 总线访问 I2C 总线段的功能，并通过 GPIO 引脚控制硬件复用器。例如：

```
----------              ----------  总线段 1   - - - - -
 |          | SCL/SDA    |          |-------------- |           |
 |          |------------|          |
 |          |            |          | 总线段 2 |           |
 |  Linux   | GPIO 1..N  |   复用器 |---------------   设备
 |          |------------|          |             |           |
 |          |            |          | 总线段 M
 |          |            |          |---------------|           |
  ----------              ----------                  - - - - -
```

主 I2C 总线的 SCL/SDA 根据 GPIO 引脚 1..N 的设置被复用到总线段 1..M。
使用
-----

i2c-mux-gpio 使用平台总线，因此你需要提供一个 `struct platform_device`，其中 `platform_data` 指向一个包含主总线的 I2C 适配器编号、要创建的总线段数量以及用于控制它的 GPIO 引脚的 `struct i2c_mux_gpio_platform_data` 结构体。详细信息请参阅 `include/linux/platform_data/i2c-mux-gpio.h`。例如，对于一个通过 3 个 GPIO 引脚控制的 4 个总线段的复用器，代码可能如下所示：

```c
#include <linux/platform_data/i2c-mux-gpio.h>
#include <linux/platform_device.h>

static const unsigned myboard_gpiomux_gpios[] = {
	AT91_PIN_PC26, AT91_PIN_PC25, AT91_PIN_PC24
};

static const unsigned myboard_gpiomux_values[] = {
	0, 1, 2, 3
};

static struct i2c_mux_gpio_platform_data myboard_i2cmux_data = {
	.parent		= 1,
	.base_nr	= 2, /* 可选 */
	.values		= myboard_gpiomux_values,
	.n_values	= ARRAY_SIZE(myboard_gpiomux_values),
	.gpios		= myboard_gpiomux_gpios,
	.n_gpios	= ARRAY_SIZE(myboard_gpiomux_gpios),
	.idle		= 4, /* 可选 */
};

static struct platform_device myboard_i2cmux = {
	.name		= "i2c-mux-gpio",
	.id		= 0,
	.dev		= {
		.platform_data	= &myboard_i2cmux_data,
	},
};
```

如果你在注册时不知道绝对 GPIO 引脚编号，你可以提供芯片名称（`.chip_name`）和相对 GPIO 引脚编号，i2c-mux-gpio 驱动将为你完成工作，包括如果 GPIO 芯片当时不可用时延迟探测。

设备注册
-------------------

当你注册你的 i2c-mux-gpio 设备时，应该将它使用的任何 GPIO 引脚的编号作为设备 ID 传递。这保证了每个实例都有不同的 ID。
或者，如果你不需要稳定的设备名称，你可以简单地将 `PLATFORM_DEVID_AUTO` 作为设备 ID 传递，那么平台核心将会为你的设备分配一个动态 ID。如果你在注册时不知道绝对 GPIO 引脚编号，这是唯一的选择。
