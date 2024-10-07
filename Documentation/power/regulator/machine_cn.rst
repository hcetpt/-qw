电压调节器设备驱动接口
=======================

电压调节器设备驱动接口旨在为特定板卡/设备的初始化代码配置电压调节子系统。考虑以下设备：

```
电压调节器-1 -+-> 电压调节器-2 --> [消费者A @ 1.8 - 2.0V]
               |
               +-> [消费者B @ 3.3V]
```

消费者A和B的驱动程序必须映射到正确的电压调节器，以便控制其电源供应。这可以通过在机器初始化代码中创建 `struct regulator_consumer_supply` 结构体来实现：

```c
struct regulator_consumer_supply {
    const char *dev_name;     /* 消费者 dev_name() */
    const char *supply;       /* 消费者的电源供应 - 例如 "vcc" */
};
```

例如，对于上述设备：

```c
static struct regulator_consumer_supply regulator1_consumers[] = {
    REGULATOR_SUPPLY("vcc", "consumer B"),
};

static struct regulator_consumer_supply regulator2_consumers[] = {
    REGULATOR_SUPPLY("vcc", "consumer A"),
};
```

这将电压调节器-1映射到消费者B的“vcc”电源供应，并将电压调节器-2映射到消费者A的“vcc”电源供应。

现在可以定义每个电压调节器的 `struct regulator_init_data` 来注册约束条件。此结构体还映射了消费者与其电源调节器的关系：

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

名称字段应设置为对板卡有描述性的内容，用于其他调节器的电源配置以及日志和其他诊断输出。通常，在原理图中使用的电源轨名称是一个不错的选择。如果没有提供名称，则子系统会自动选择一个名称。

电压调节器-1向电压调节器-2供电。这种关系必须注册到核心，以便当消费者A启用其电源（电压调节器-2）时，电压调节器-1也被启用。电源调节器由下面的 `supply_regulator` 字段设置：

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

最后，必须以常规方式注册电压调节器设备：

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

/* 注册电压调节器1设备 */
platform_device_register(&regulator_devices[0]);

/* 注册电压调节器2设备 */
platform_device_register(&regulator_devices[1]);
```
