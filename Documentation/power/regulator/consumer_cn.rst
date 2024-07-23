监管器消费者驱动接口
==============================

本文本描述了消费者设备驱动程序的监管器接口。
请参阅overview.txt，了解本文中使用的术语描述。
1. 消费者监管器访问（静态与动态驱动）
======================================================

消费者驱动可以通过调用以下方法获取其供电监管器：

    regulator = regulator_get(dev, "Vcc");

消费者传入其结构体device指针和电源供应ID。核心通过查询特定于机器的查找表来找到正确的监管器。
如果查找成功，此调用将返回指向为该消费者供电的struct regulator的指针。
为了释放监管器，消费者驱动应调用：

    regulator_put(regulator);

一个消费者可以由多个监管器供电，例如，编解码器消费者可能同时需要模拟和数字供电：

    digital = regulator_get(dev, "Vcc");  /* 数字核心 */
    analog = regulator_get(dev, "Avdd");  /* 模拟 */

监管器访问函数regulator_get()和regulator_put()通常会在你的设备驱动的probe()和remove()函数中分别被调用。
2. 监管器输出启用与禁用（静态与动态驱动）
===============================================================

消费者可以通过调用以下方法启用其电源：

    int regulator_enable(regulator);

注意：
   在调用regulator_enable()之前，电源可能已经被启用。这可能发生在消费者共享监管器或者监管器已被引导加载程序或内核板初始化代码预先启用的情况下。

消费者可以通过调用以下方法确定监管器是否已启用：

    int regulator_is_enabled(regulator);

当监管器被启用时，此调用将返回大于零的值。

不再需要时，消费者可以通过调用以下方法禁用其电源：

    int regulator_disable(regulator);

注意：
   如果电源与其他消费者共享，则此操作可能不会禁用电源。只有在启用引用计数为零时，监管器才会被禁用。

最后，在紧急情况下，可以强制关闭监管器：

    int regulator_force_disable(regulator);

注意：
   这将立即且强制地关闭监管器输出。所有消费者都将断电。
3. 调压器电压控制与状态（动态驱动程序）
=======================================================

一些消费型驱动程序需要能够动态地改变其供电电压以匹配系统的工作点。例如，CPUfreq驱动程序可以随频率调整电压来节省电力，SD卡驱动程序可能需要选择正确的卡片电压等。
消费者可以通过调用以下函数来控制其供电电压：

```
int regulator_set_voltage(regulator, min_uV, max_uV);
```

其中min_uV和max_uV是以微伏为单位的最小和最大可接受电压。
注意：此函数可以在调压器启用或禁用时调用。如果在启用状态下调用，则电压会立即变化；否则，电压配置会改变，并且当调压器下次启用时，物理上设置电压。
调压器配置的输出电压可通过以下函数获取：

```
int regulator_get_voltage(regulator);
```

注意：
  get_voltage()无论调压器是否启用都会返回配置的输出电压，不应用于确定调压器输出状态。然而，这可以与is_enabled()结合使用，以确定调压器的物理输出电压。

4. 调压器电流限制控制与状态（动态驱动程序）
=============================================================

一些消费型驱动程序需要能够动态地改变其供电电流限制以匹配系统的工作点。例如，LCD背光驱动器可以改变电流限制以调整背光亮度，USB驱动器在供电时可能想要将限制设置为500mA等。
消费者可以通过调用以下函数来控制其供电电流限制：

```
int regulator_set_current_limit(regulator, min_uA, max_uA);
```

其中min_uA和max_uA是以微安为单位的最小和最大可接受电流限制。
注意：
  此函数可以在调压器启用或禁用时调用。如果在启用状态下调用，则电流限制会立即变化；否则，电流限制配置会改变，并且当调压器下次启用时，物理上设置电流限制。
调压器的电流限制可通过以下函数获取：

```
int regulator_get_current_limit(regulator);
```

注意：
  get_current_limit()无论调压器是否启用都会返回电流限制，不应用于确定调压器的电流负载。

5. 调压器工作模式控制与状态（动态驱动程序）
==============================================================

一些消费者可以通过改变其供电调压器的工作模式，在消费者的工作状态发生变化时进一步节省系统电力。例如，消费者驱动程序处于空闲状态，随后消耗更少的电流。

调压器工作模式可以间接或直接改变
间接工作模式控制
消费者驱动程序可以请求更改其电源调节器的工作模式，方法是调用：

```c
int regulator_set_load(struct regulator *regulator, int load_uA);
```

这将导致内核重新计算调节器上的总负载（基于其所有消费者），并在必要和允许的情况下更改工作模式，以最佳匹配当前的操作负载。
load_uA值可以从消费者的规格书中确定。例如，大多数规格书有表格显示在某些情况下消耗的最大电流。

大多数消费者将使用间接操作模式控制，因为他们不知道调节器或调节器是否与其他消费者共享。

直接操作模式控制
------------------

定制或紧密耦合的驱动程序可能希望根据它们的操作点直接控制调节器的操作模式。这可以通过调用实现：

```c
int regulator_set_mode(struct regulator *regulator, unsigned int mode);
unsigned int regulator_get_mode(struct regulator *regulator);
```

直接模式仅由那些*知道*调节器并且不与其他消费者共享调节器的消费者使用。

6. 调节器事件
=============

调节器可以向消费者通知外部事件。在调节器压力或故障条件下，消费者可能会收到事件。
消费者可以通过调用表达对调节器事件的兴趣：

```c
int regulator_register_notifier(struct regulator *regulator,
					struct notifier_block *nb);
```

消费者可以通过调用取消兴趣：

```c
int regulator_unregister_notifier(struct regulator *regulator,
					  struct notifier_block *nb);
```

调节器使用内核通知框架将其事件发送给感兴趣的消费者。

7. 调节器直接寄存器访问
=======================

某些类型的电源管理硬件或固件设计为需要对调节器进行低级硬件访问，无需内核参与。此类设备的例子包括：

- 具有电压控制振荡器和控制逻辑的时钟源，通过I2C改变供电电压以达到所需的输出时钟频率
- 在过温条件下可以发出任意I2C交易以执行系统关机的热管理固件

为了设置此类设备/固件，需要配置各种参数，如调节器的I2C地址、各种调节器寄存器的地址等。调节器框架提供了以下帮助函数来查询这些细节。

特定于总线的详细信息，如I2C地址或传输速率由regmap框架处理。要获取调节器的regmap（如果支持），请使用：

```c
struct regmap *regulator_get_regmap(struct regulator *regulator);
```

要获取调节器的电压选择寄存器的硬件寄存器偏移量和位掩码，请使用：

```c
int regulator_get_hardware_vsel_register(struct regulator *regulator,
						 unsigned *vsel_reg,
						 unsigned *vsel_mask);
```

要将调节器框架中的电压选择代码（用于regulator_list_voltage）转换为可以直接写入电压选择寄存器的硬件特定电压选择器，请使用：

```c
int regulator_list_hardware_vsel(struct regulator *regulator,
					 unsigned selector);
```

为了访问用于启用/禁用调节器的硬件，消费者必须使用regulator_get_exclusive()，因为它无法在存在多个消费者的情况下工作。要启用/禁用调节器，请使用：

```c
int regulator_hardware_enable(struct regulator *regulator, bool enable);
```
