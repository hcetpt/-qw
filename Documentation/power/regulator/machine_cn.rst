调节器机器驱动接口
=====================

调节器机器驱动接口旨在为特定于板卡/机器的初始化代码提供配置，以设置调节器子系统。
考虑以下机器示例：

```
调节器-1 -+-> 调节器-2 --> [消费者A @ 1.8 - 2.0V]
           |
           +-> [消费者B @ 3.3V]
```

消费者A和B的驱动程序必须映射到正确的调节器，以便控制其电源。在机器初始化代码中，通过为每个调节器创建一个`struct regulator_consumer_supply`结构体来实现这种映射：

```c
struct regulator_consumer_supply {
    const char *dev_name;     // 消费者 dev_name()
    const char *supply;       // 消费者的供电 - 如 "vcc"
};
```

例如，对于上述机器：

```c
static struct regulator_consumer_supply regulator1_consumers[] = {
    REGULATOR_SUPPLY("Vcc", "consumer B"),
};

static struct regulator_consumer_supply regulator2_consumers[] = {
    REGULATOR_SUPPLY("Vcc", "consumer A"),
};
```

这将调节器-1映射到消费者B的'Vcc'供电，并将调节器-2映射到消费者A的'Vcc'供电。

现在可以通过定义每个调节器电源域的`struct regulator_init_data`结构体来注册约束。这个结构体也映射了消费者到他们的供电调节器：

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

名称字段应设置为对板卡配置其他调节器的供电有用的描述性内容，以及用于日志记录和其他诊断输出。通常，在原理图中用于供电轨的名称是一个不错的选择。如果没有提供名称，则子系统将选择一个。

调节器-1向调节器-2供电。这种关系必须向核心注册，以便当消费者A启用其供电（调节器-2）时，调节器-1也被启用。供电调节器由下面的`supply_regulator`字段设置：

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

最后，必须以常规方式注册调节器设备：

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
// 注册调节器1设备
platform_device_register(&regulator_devices[0]);

// 注册调节器2设备
platform_device_register(&regulator_devices[1]);
```
