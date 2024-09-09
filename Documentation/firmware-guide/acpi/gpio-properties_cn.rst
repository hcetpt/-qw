SPDX 许可证标识符: GPL-2.0

======================================
与 GPIO 相关的 DSD 设备属性
======================================

随着 ACPI 5.1 的发布，_DSD 配置对象最终允许为 GPIO（以及其他一些资源）命名，这些 GPIO 是由 _CRS 返回的。之前，我们只能使用整数索引来查找相应的 GPIO，这非常容易出错（例如，它依赖于 _CRS 输出的顺序）。通过 _DSD，我们现在可以使用名称而不是整数索引来查询 GPIO，如下 ASL 示例所示：

```asl
// 带有复位和关机 GPIO 的蓝牙设备
Device (BTH)
{
    Name (_HID, ...)

    Name (_CRS, ResourceTemplate ()
    {
        GpioIo (Exclusive, PullUp, 0, 0, IoRestrictionOutputOnly, "\\_SB.GPO0", 0, ResourceConsumer) { 15 }
        GpioIo (Exclusive, PullUp, 0, 0, IoRestrictionOutputOnly, "\\_SB.GPO0", 0, ResourceConsumer) { 27, 31 }
    })

    Name (_DSD, Package ()
    {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "reset-gpios", Package () { ^BTH, 1, 1, 0 } },
            Package () { "shutdown-gpios", Package () { ^BTH, 0, 0, 0 } },
        }
    })
}
```

支持的 GPIO 属性格式如下：

```asl
Package () { "name", Package () { ref, index, pin, active_low }}
```

- `ref`: 包含 GpioIo()/GpioInt() 资源的设备，通常就是该设备本身（在我们的例子中是 BTH）。
- `index`: 在 _CRS 中 GpioIo()/GpioInt() 资源的索引，从零开始计数。
- `pin`: GpioIo()/GpioInt() 资源中的引脚编号。通常这是零。
- `active_low`: 如果设置为 1，则表示该 GPIO 为低电平有效。

由于 ACPI GpioIo() 资源没有字段说明它是高电平还是低电平有效，因此可以通过 `active_low` 参数来设置。将其设置为 1 表示该 GPIO 为低电平有效。

注意：对于 GpioInt() 资源，_DSD 中的 `active_low` 没有意义，必须设置为 0。GpioInt() 资源有自己的方式定义这一点。

在我们的蓝牙示例中，“reset-gpios” 指的是第二个 GpioIo() 资源中的第二个引脚，GPIO 编号为 31。

不幸的是，GpioIo() 资源并没有显式提供输出引脚的初始状态，驱动程序在初始化时应该使用这个状态。Linux 尝试在这里使用常识，并根据偏置和极性设置推导出状态。下表显示了期望的状态：

| Pull Bias | Polarity | 请求的... |
|-----------|----------|------------|
| 隐式      |          |            |
|-----------|----------|------------|
| **默认**  | x        | 如是（假设固件已为我们配置好）|
|-----------|----------|------------|
| 显式      |          |            |
|-----------|----------|------------|
| **无**    | x        | 如是（假设固件已为我们配置好，且没有 Pull Bias）|
|-----------|----------|------------|
| **上拉**  | x (无 _DSD) | 作为高电平，假设非活动 |
|           | 低       | 作为高电平，假设活动    |
|-----------|----------|------------|
| **下拉**  | x (无 _DSD) | 作为低电平，假设非活动 |
|           | 高       | 作为低电平，假设活动    |
|-----------|----------|------------|

因此，在上面的例子中，两个 GPIO 由于偏置设置是显式的并且存在 _DSD，将被视为高电平有效，Linux 将会将引脚配置为这种状态，直到驱动程序重新编程它们。
可以在GPIO数组中留下空位。这对于某些情况非常有用，例如在SPI主机控制器中，一些片选信号可能实现为GPIO，而另一些则为原生信号。例如，一个SPI主机控制器可以将片选0和片选2实现为GPIO，而片选1则为原生信号：

```acpi
Package () {
    "cs-gpios",
    Package () {
        ^GPIO, 19, 0, 0, // 片选0：GPIO
        0,               // 片选1：原生信号
        ^GPIO, 20, 0, 0, // 片选2：GPIO
    }
}
```

需要注意的是，历史上ACPI没有定义GPIO极性的手段，因此`SPISerialBus()`资源在每个芯片的基础上定义极性。为了避免一系列的取反操作，假设GPIO极性为高电平有效。即使在涉及_DSD()的情况下（参见上述示例），GPIO片选极性也必须定义为高电平有效以避免歧义。

其他支持的属性
===============

以下Device Tree兼容设备属性也被_DSD设备属性支持用于GPIO控制器：

- gpio-hog
- output-high
- output-low
- input
- line-name

示例：

```acpi
Name (_DSD, Package () {
    // _DSD 层次属性扩展UUID
    ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
    Package () {
        Package () { "hog-gpio8", "G8PU" }
    }
})

Name (G8PU, Package () {
    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
    Package () {
        Package () { "gpio-hog", 1 },
        Package () { "gpios", Package () { 8, 0 } },
        Package () { "output-high", 1 },
        Package () { "line-name", "gpio8-pullup" },
    }
})
```

- gpio-line-names

`gpio-line-names`声明是一个字符串列表（“名称”），描述GPIO控制器/扩展器中的每条线/引脚。此列表包含在一个包中，并且必须插入到ACPI表中的GPIO控制器声明中（通常在DSDT内）。`gpio-line-names`列表必须遵循以下规则（参见示例）：

  - 列表中的第一个名称对应GPIO控制器/扩展器的第一条线/引脚
  - 列表中的名称必须连续（不允许有空位）
  - 列表可以不完整并可以在最后一个GPIO线之前结束；换句话说，不需要填充所有GPIO线
  - 允许使用空名称（两个双引号``""``对应一个空名称）
  - 同一GPIO控制器/扩展器内的名称必须唯一

16条线的GPIO控制器示例，具有两个空名称的不完整列表：

```acpi
Package () {
    "gpio-line-names",
    Package () {
        "pin_0",
        "pin_1",
        "",
        "",
        "pin_3",
        "pin_4_push_button",
    }
}
```

运行时，上述声明产生的结果如下（使用“libgpiod”工具）：

```
root@debian:~# gpioinfo gpiochip4
gpiochip4 - 16 lines:
        line   0:      "pin_0"       unused   input  active-high
        line   1:      "pin_1"       unused   input  active-high
        line   2:      unnamed       unused   input  active-high
        line   3:      unnamed       unused   input  active-high
        line   4:      "pin_3"       unused   input  active-high
        line   5: "pin_4_push_button" unused input active-high
        line   6:      unnamed       unused   input  active-high
        line   7       unnamed       unused   input  active-high
        line   8:      unnamed       unused   input  active-high
        line   9:      unnamed       unused   input  active-high
        line  10:      unnamed       unused   input  active-high
        line  11:      unnamed       unused   input  active-high
        line  12:      unnamed       unused   input  active-high
        line  13:      unnamed       unused   input  active-high
        line  14:      unnamed       unused   input  active-high
        line  15:      unnamed       unused   input  active-high
root@debian:~# gpiofind pin_4_push_button
gpiochip4 5
root@debian:~#
```

另一个示例：

```acpi
Package () {
    "gpio-line-names",
    Package () {
        "SPI0_CS_N", "EXP2_INT", "MUX6_IO", "UART0_RXD",
        "MUX7_IO", "LVL_C_A1", "MUX0_IO", "SPI1_MISO",
    }
}
```

更多关于这些属性的信息请参阅Documentation/devicetree/bindings/gpio/gpio.txt。

ACPI GPIO映射由驱动程序提供
================================

有些系统中的ACPI表不包含_DSD但提供了带有GpioIo()/GpioInt()资源的_CRS，并且设备驱动程序仍然需要与它们一起工作。
在这种情况下，ACPI设备标识对象（如_HID、_CID、_CLS、_SUB、_HRV），可供驱动程序使用来识别设备，并且这应该足以确定GpioIo()/GpioInt()资源返回的所有GPIO线的意义和用途。换句话说，一旦驱动程序识别了设备，它就应该知道如何使用GpioIo()/GpioInt()资源。完成这一过程后，它可以简单地为其要使用的GPIO线分配名称，并向GPIO子系统提供这些名称与其对应的ACPI GPIO资源之间的映射关系。
为此，驱动程序需要定义一个映射表，作为struct acpi_gpio_mapping对象数组，每个对象包含一个名称、指向行数据（struct acpi_gpio_params对象数组）的指针以及该数组的大小。每个struct acpi_gpio_params对象包含三个字段：crs_entry_index、line_index和active_low，分别表示目标GpioIo()/GpioInt()资源在_CRS中的索引（从零开始）、该资源中目标线的索引（从零开始）以及该线的低电平有效标志，这与上面指定的_DSD GPIO属性格式类似。
对于前面讨论的蓝牙设备示例，相关数据结构如下所示：

```c
static const struct acpi_gpio_params reset_gpio = { 1, 1, false };
static const struct acpi_gpio_params shutdown_gpio = { 0, 0, false };

static const struct acpi_gpio_mapping bluetooth_acpi_gpios[] = {
    { "reset-gpios", &reset_gpio, 1 },
    { "shutdown-gpios", &shutdown_gpio, 1 },
    { }
};
```

接下来，需要将映射表作为第二个参数传递给acpi_dev_add_driver_gpios()或其托管版本，以便将其注册到由第一个参数指向的ACPI设备对象。这应在驱动程序的.probe()函数中完成。
在移除时，驱动程序应通过调用acpi_dev_remove_driver_gpios()取消注册其GPIO映射表，该表之前已注册到相应的ACPI设备对象上。

使用_CRS回退
================

如果设备没有_DSD或驱动程序未创建ACPI GPIO映射，则Linux GPIO框架会拒绝返回任何GPIO。这是因为驱动程序不知道它实际得到了什么。例如，如果我们有一个像下面这样的设备：

```acpi
Device (BTH)
{
    Name (_HID, ...)

    Name (_CRS, ResourceTemplate () {
        GpioIo (Exclusive, PullNone, 0, 0, IoRestrictionNone,
                "\\_SB.GPO0", 0, ResourceConsumer) { 15 }
        GpioIo (Exclusive, PullNone, 0, 0, IoRestrictionNone,
                "\\_SB.GPO0", 0, ResourceConsumer) { 27 }
    })
}
```

驱动程序可能会期望在执行以下操作时得到正确的GPIO：

```c
desc = gpiod_get(dev, "reset", GPIOD_OUT_LOW);
if (IS_ERR(desc))
    ...error handling..
```

但由于无法知道“reset”与_CRS中的GpioIo()之间的映射关系，desc将持有ERR_PTR(-ENOENT)。
驱动程序作者可以通过显式传递映射来解决这个问题（这是推荐的方法，并在上述章节中有文档说明）。
ACPI GPIO 映射表不应污染那些不知道其正在服务的确切设备的驱动程序。这意味着 ACPI GPIO 映射表几乎不与 ACPI ID 和特定对象关联，如上一章所述。

获取 GPIO 描述符
=================

有两种主要方法从 ACPI 获取 GPIO 资源：

```c
desc = gpiod_get(dev, connection_id, flags);
desc = gpiod_get_index(dev, connection_id, index, flags);
```

这里可以考虑两种不同情况，即提供了连接 ID 的情况和未提供的情况。
情况 1：

```c
desc = gpiod_get(dev, "non-null-connection-id", flags);
desc = gpiod_get_index(dev, "non-null-connection-id", index, flags);
```

情况 2：

```c
desc = gpiod_get(dev, NULL, flags);
desc = gpiod_get_index(dev, NULL, index, flags);
```

情况 1 假定相应的 ACPI 设备描述必须定义了设备属性，并且在其他情况下会阻止获取任何 GPIO 资源。
情况 2 明确告诉 GPIO 核心在 _CRS 中查找资源。
需要注意的是，在情况 1 和情况 2 中，假设提供了两个版本的 ACPI 设备描述并且驱动程序中没有映射，则 `gpiod_get_index()` 将返回不同的资源。因此，特定驱动程序需要按照上一章所述仔细处理这些资源。
