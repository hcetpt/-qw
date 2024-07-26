调节器机器驱动接口
====================

调节器机器驱动接口旨在为特定于板卡/机器的初始化代码提供配置调节器子系统的功能。
考虑以下机器示例：

```
调节器-1 -+-> 调节器-2 --> [消费者 A @ 1.8 - 2.0V]
           |
           +-> [消费者 B @ 3.3V]
```

消费者A与B的驱动程序必须映射到正确的调节器，以便能够控制它们的电源供应。这种映射可以通过在机器初始化代码中为每个调节器创建一个`struct regulator_consumer_supply`结构体来实现。

例如，在上述机器上：

```c
static struct regulator_consumer_supply regulator1_consumers[] = {
	REGULATOR_SUPPLY("Vcc", "consumer B"),
};

static struct regulator_consumer_supply regulator2_consumers[] = {
	REGULATOR_SUPPLY("Vcc", "consumer A"),
};
```

这将调节器-1映射到消费者B的“Vcc”供电，并将调节器-2映射到消费者A的“Vcc”供电。
现在可以定义每个调节器电源域的`struct regulator_init_data`来注册约束条件。此结构还映射了消费者与其供电调节器之间的关系：

```c
static struct regulator_init_data regulator1_data = {
	.constraints = {
		.name = "Regulator-1",
		.min_uV = 3300000,
		.max_uV = 3300000,
		.valid_modes_mask = REGULATOR_MODE_NORMAL,
	},
	.num_consumer_supplies = ARRAY_SIZE(regulator1_consumers),
	.consumer_supplies = regulator1_consumers,
};
```

`name`字段应该设置为对板卡有用的描述性名称，用于配置其他调节器的电源供应，并且用于日志记录和其他诊断输出。通常，原理图中用于电源轨的名称是一个不错的选择。如果没有提供名称，则子系统会自行选择一个名称。
调节器-1向调节器-2供电。这种关系必须向核心注册，以确保当消费者A启用其电源（即调节器-2）时，调节器-1也被启用。通过`supply_regulator`字段设置供电调节器：

```c
static struct regulator_init_data regulator2_data = {
	.supply_regulator = "Regulator-1",
	.constraints = {
		.min_uV = 1800000,
		.max_uV = 2000000,
		.valid_ops_mask = REGULATOR_CHANGE_VOLTAGE,
		.valid_modes_mask = REGULATOR_MODE_NORMAL,
	},
	.num_consumer_supplies = ARRAY_SIZE(regulator2_consumers),
	.consumer_supplies = regulator2_consumers,
};
```

最后，必须按照常规方式注册调节器设备：

```c
static struct platform_device regulator_devices[] = {
	{
		.name = "regulator",
		.id = DCDC_1,
		.dev = {
			.platform_data = &regulator1_data,
		},
	},
	{
		.name = "regulator",
		.id = DCDC_2,
		.dev = {
			.platform_data = &regulator2_data,
		},
	},
};

/* 注册调节器 1 设备 */
platform_device_register(&regulator_devices[0]);

/* 注册调节器 2 设备 */
platform_device_register(&regulator_devices[1]);
```
