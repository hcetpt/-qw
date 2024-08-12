=============  
GPIO 映射  
=============  

本文档解释了如何将 GPIO 分配给特定的设备和功能。所有平台都可以启用 GPIO 库，但如果平台严格要求必须存在 GPIO 功能，则需要从其 Kconfig 中选择 GPIOLIB。GPIO 的映射方式取决于平台用来描述其硬件布局的方式。目前，可以通过设备树、ACPI 和平台数据来定义映射。

### 设备树
---
在设备树中可以很容易地将 GPIO 映射到设备和功能上。具体的映射方法取决于提供 GPIO 的 GPIO 控制器，请参阅您控制器的设备树绑定。

GPIO 映射是在消费设备节点中定义的，通过一个名为 `<function>-gpios` 的属性，其中 `<function>` 是驱动程序通过 `gpiod_get()` 请求的功能。例如：

```plaintext
foo_device {
    compatible = "acme,foo";
    ...
    led-gpios = <&gpio 15 GPIO_ACTIVE_HIGH>, /* 红色 */
                <&gpio 16 GPIO_ACTIVE_HIGH>, /* 绿色 */
                <&gpio 17 GPIO_ACTIVE_HIGH>; /* 蓝色 */

    power-gpios = <&gpio 1 GPIO_ACTIVE_LOW>;
};
```

命名为 `<function>-gpio` 的属性也被认为是有效的，旧的绑定使用它，但仅出于兼容性的原因支持，并且不应该用于新的绑定，因为它已被废弃。

此属性将使 GPIO 15、16 和 17 对驱动程序可用，作为 "led" 功能，而 GPIO 1 则作为 "power" GPIO：

```c
struct gpio_desc *red, *green, *blue, *power;

red = gpiod_get_index(dev, "led", 0, GPIOD_OUT_HIGH);
green = gpiod_get_index(dev, "led", 1, GPIOD_OUT_HIGH);
blue = gpiod_get_index(dev, "led", 2, GPIOD_OUT_HIGH);

power = gpiod_get(dev, "power", GPIOD_OUT_HIGH);
```

LED GPIO 将是高电平有效，而电源 GPIO 将是低电平有效（即 `gpiod_is_active_low(power)` 将返回真）。

`gpiod_get()` 函数的第二个参数，即 con_id 字符串，必须是设备树中使用的 GPIO 后缀的 `<function>` 前缀（"gpios" 或 "gpio"，由 gpiod 函数内部自动查找）。以上面的 "led-gpios" 示例为例，使用前缀（不包括 "-"）作为 con_id 参数：“led”。

内部，GPIO 子系统使用在 con_id 中传递的字符串为 GPIO 后缀（"gpios" 或 "gpio"）添加前缀以得到结果字符串 (`snprintf(... "%s-%s", con_id, gpio_suffixes[])`)。

### ACPI
---
ACPI 也以类似设备树的方式支持 GPIO 的功能名称。
上述的设备树（DT）示例可以通过使用在ACPI 5.1中引入的 _DSD（设备特定数据）转换为等效的ACPI描述，如下所示:

	Device (FOO) {
		Name (_CRS, ResourceTemplate () {
			GpioIo (Exclusive, PullUp, 0, 0, IoRestrictionOutputOnly,
				"\\_SB.GPI0", 0, ResourceConsumer) { 15 } // 红色
			GpioIo (Exclusive, PullUp, 0, 0, IoRestrictionOutputOnly,
				"\\_SB.GPI0", 0, ResourceConsumer) { 16 } // 绿色
			GpioIo (Exclusive, PullUp, 0, 0, IoRestrictionOutputOnly,
				"\\_SB.GPI0", 0, ResourceConsumer) { 17 } // 蓝色
			GpioIo (Exclusive, PullNone, 0, 0, IoRestrictionOutputOnly,
				"\\_SB.GPI0", 0, ResourceConsumer) { 1 } // 电源
		})

		Name (_DSD, Package () {
			ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
			Package () {
				Package () {
					"led-gpios",
					Package () {
						^FOO, 0, 0, 1,
						^FOO, 1, 0, 1,
						^FOO, 2, 0, 1,
					}
				},
				Package () { "power-gpios", Package () { ^FOO, 3, 0, 0 } },
			}
		})
	}

关于ACPI GPIO绑定的更多信息，请参阅 `Documentation/firmware-guide/acpi/gpio-properties.rst`。

平台数据
---------
最后，可以使用平台数据将GPIO与设备和功能绑定。希望这样做的板级文件需要包含以下头文件：

	#include <linux/gpio/machine.h>

通过查找表中的gpiod_lookup结构实例来映射GPIO。定义了两个宏以帮助声明此类映射：

	GPIO_LOOKUP(key, chip_hwnum, con_id, flags)
	GPIO_LOOKUP_IDX(key, chip_hwnum, con_id, idx, flags)

其中

  - key是提供GPIO的gpiod_chip实例的标签，或GPIO线名
  - chip_hwnum是芯片内部GPIO的硬件编号，或U16_MAX表示key是一个GPIO线名
  - con_id是从设备角度看的GPIO功能名称。它可以为NULL，在这种情况下它将匹配任何功能
  - idx是在功能内的GPIO索引
  - flags定义了以下属性：
	* GPIO_ACTIVE_HIGH - GPIO线为高电平有效
	* GPIO_ACTIVE_LOW - GPIO线为低电平有效
	* GPIO_OPEN_DRAIN - GPIO线设置为开漏
	* GPIO_OPEN_SOURCE - GPIO线设置为开源
	* GPIO_PERSISTENT - 在挂起/恢复期间GPIO线保持其值且具有持久性
	* GPIO_TRANSITORY - 在挂起/恢复期间GPIO线可能失去其电气状态，是非持久性的

未来，这些标志可能会扩展以支持更多属性。
请注意：
  1. GPIO线名不保证全局唯一，因此将使用找到的第一个匹配项
  2. GPIO_LOOKUP()仅仅是GPIO_LOOKUP_IDX()的一个快捷方式，其中idx=0
然后可以按照以下方式定义查找表，空条目定义其结束。表的'dev_id'字段是将使用这些GPIO的设备标识符。它可以为NULL，在这种情况下它将与调用gpiod_get()时传入NULL设备相匹配
.. code-block:: c

        struct gpiod_lookup_table gpios_table = {
                .dev_id = "foo.0",
                .table = {
                        GPIO_LOOKUP_IDX("gpio.0", 15, "led", 0, GPIO_ACTIVE_HIGH),
                        GPIO_LOOKUP_IDX("gpio.0", 16, "led", 1, GPIO_ACTIVE_HIGH),
                        GPIO_LOOKUP_IDX("gpio.0", 17, "led", 2, GPIO_ACTIVE_HIGH),
                        GPIO_LOOKUP("gpio.0", 1, "power", GPIO_ACTIVE_LOW),
                        { },
                },
        };

然后板级代码可以如下添加该表：

	gpiod_add_lookup_table(&gpios_table);

控制"foo.0"的驱动程序将能够如下获取其GPIO：

	struct gpio_desc *red, *green, *blue, *power;

	red = gpiod_get_index(dev, "led", 0, GPIOD_OUT_HIGH);
	green = gpiod_get_index(dev, "led", 1, GPIOD_OUT_HIGH);
	blue = gpiod_get_index(dev, "led", 2, GPIOD_OUT_HIGH);

	power = gpiod_get(dev, "power", GPIOD_OUT_HIGH);

由于"led" GPIO被映射为高电平有效，此示例将把它们的信号切换到1，即启用LED。而对于"power" GPIO，它被映射为低电平有效，其实际信号在执行完这段代码后将是0。与传统的整型GPIO接口不同，低电平有效的特性在映射时处理，并对GPIO消费者透明。
一系列函数如gpiod_set_value()可用于处理新的描述符导向接口。
使用平台数据的板卡还可以通过定义GPIO独占表来独占GPIO线路。
```c
// 以下是一个示例结构体数组，用于表示GPIO资源的独占使用
struct gpiod_hog gpio_hog_table[] = {
        // 请求名为"gpio.0"的GPIO，设置其序号为10，用户标签为"foo"，
        // 指定其工作模式为低电平有效，并将输出状态设为高电平。
        GPIO_HOG("gpio.0", 10, "foo", GPIO_ACTIVE_LOW, GPIOD_OUT_HIGH),
        // 结束标志
        { }
};
```

上述结构体数组可以如下方式添加到板级支持包（board code）中：

```c
gpiod_add_hogs(gpio_hog_table);
```

当GPIO控制器创建时，这些GPIO将会被立即独占使用；如果GPIO控制器在此之前已创建，则在注册hog表时进行独占使用。

### 引脚数组

除了逐一请求分配给某个功能的引脚外，设备还可以请求一组这样的引脚。这些引脚映射到设备的方式决定了该数组是否符合快速位图处理的要求。如果符合，位图可以直接通过get/set数组函数在调用者和相应的GPIO芯片的.get/set_multiple()回调之间传递。

为了满足快速位图处理的要求，数组必须满足以下条件：

- 数组成员0的硬件引脚编号也必须是0；
- 属于与成员0相同芯片的连续数组成员的硬件引脚编号也必须与其数组索引相匹配。

如果不满足上述要求，为了避免属于同一芯片但未按硬件顺序排列的连续引脚被分开处理，不会启用快速位图处理路径。

如果数组适用于快速位图处理路径，那么不属于与成员0相同芯片的引脚以及索引与硬件引脚编号不一致的引脚，无论输入还是输出，都会从快速路径中排除。此外，开漏和开源类型的引脚也会从快速位图输出处理中排除。
