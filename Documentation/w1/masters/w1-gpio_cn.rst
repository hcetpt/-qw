============= 
内核驱动 w1-gpio 
============= 

**作者:** Ville Syrjala <syrjala@sci.fi>

**描述**

这是一个使用 GPIO 接口来控制线路的 1-Wire 总线主设备驱动。该驱动通过机器描述符表指定 GPIO 引脚。此外，也可以通过设备树定义主设备，详情参见 `Documentation/devicetree/bindings/w1/w1-gpio.yaml`。

**示例（mach-at91）**
-------------------

```c
#include <linux/gpio/machine.h>
#include <linux/w1-gpio.h>

static struct gpiod_lookup_table foo_w1_gpiod_table = {
	.dev_id = "w1-gpio",
	.table = {
		GPIO_LOOKUP_IDX("at91-gpio", AT91_PIN_PB20, NULL, 0,
			GPIO_ACTIVE_HIGH|GPIO_OPEN_DRAIN),
	},
};

static struct w1_gpio_platform_data foo_w1_gpio_pdata = {
	.ext_pullup_enable_pin	= -EINVAL,
};

static struct platform_device foo_w1_device = {
	.name			= "w1-gpio",
	.id			= -1,
	.dev.platform_data	= &foo_w1_gpio_pdata,
};

...
at91_set_GPIO_periph(foo_w1_gpio_pdata.pin, 1);
at91_set_multi_drive(foo_w1_gpio_pdata.pin, 1);
gpiod_add_lookup_table(&foo_w1_gpiod_table);
platform_device_register(&foo_w1_device);
```
以上代码展示了如何为 at91 平台配置和注册一个 w1-gpio 设备。
