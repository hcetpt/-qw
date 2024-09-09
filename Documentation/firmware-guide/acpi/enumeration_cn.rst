SPDX 许可证标识符: GPL-2.0

=============================
基于 ACPI 的设备枚举
=============================

ACPI 5 引入了一组新的资源（UartTSerialBus、I2cSerialBus、SpiSerialBus、GpioIo 和 GpioInt），这些资源可用于枚举串行总线控制器后面的从设备。此外，我们开始看到一些集成在 SoC/Chipset 中的外设仅出现在 ACPI 命名空间中。这些通常是通过内存映射寄存器访问的设备。

为了支持这一点并尽可能重用现有的驱动程序，我们决定如下：

  - 没有总线连接资源的设备表示为平台设备。
  - 在实际总线后面的设备，如果存在连接资源，则表示为 `struct spi_device` 或 `struct i2c_client`。请注意，标准 UART 不是总线，因此没有 `struct uart_device`，尽管其中一些可能由 `struct serdev_device` 表示。

由于 ACPI 和设备树都表示设备及其资源的树形结构，此实现尽可能遵循设备树的方式。

ACPI 实现枚举总线后面的设备（平台、SPI、I2C，在某些情况下还包括 UART），创建物理设备，并将它们绑定到 ACPI 命名空间中的 ACPI 句柄。

这意味着当 `ACPI_HANDLE(dev)` 返回非 NULL 时，该设备是从 ACPI 命名空间枚举出来的。这个句柄可以用来提取其他设备特定的配置。下面有一个例子。

平台总线支持
====================

由于我们使用平台设备来表示未连接到任何物理总线的设备，我们只需要为设备实现一个平台驱动程序并添加支持的 ACPI ID。如果同一 IP 模块用于其他非 ACPI 平台，驱动程序可能直接可用或需要进行一些小的修改。

为现有驱动程序添加 ACPI 支持应该相当简单。以下是最简单的示例：

```c
static const struct acpi_device_id mydrv_acpi_match[] = {
	/* ACPI IDs here */
	{}
};
MODULE_DEVICE_TABLE(acpi, mydrv_acpi_match);

static struct platform_driver my_driver = {
	..
	.driver = {
		.acpi_match_table = mydrv_acpi_match,
	},
};
```

如果驱动程序需要执行更复杂的初始化操作，例如获取和配置 GPIO，它可以获取其 ACPI 句柄并从 ACPI 表格中提取这些信息。
ACPI设备对象
==============

一般来说，在使用ACPI作为平台固件与操作系统之间接口的系统中，设备可以分为两类：一类是可以通过定义在其所在总线上的协议（例如PCI配置空间）进行本机发现和枚举的设备，无需平台固件的帮助；另一类是需要由平台固件描述以便被发现的设备。对于任何已知于平台固件的设备，无论其属于哪一类，都可以在ACPI命名空间中有相应的ACPI设备对象，在这种情况下，Linux内核将根据该对象为该设备创建一个`struct acpi_device`对象。这些`struct acpi_device`对象从不用于绑定本机可发现设备的驱动程序，因为这些设备由其他类型的设备对象（例如PCI设备的`struct pci_dev`）表示，并且由设备驱动程序绑定（此时对应的`struct acpi_device`对象用作有关设备配置的附加信息来源）。此外，核心ACPI设备枚举代码会为大多数通过平台固件帮助发现和枚举的设备创建`struct platform_device`对象，这些平台设备对象可以像处理本机可枚举设备那样由平台驱动程序绑定。因此，从逻辑上讲，将驱动程序绑定到`struct acpi_device`对象通常是无效的，包括那些通过平台固件帮助发现的设备的驱动程序。

历史上，一些通过平台固件帮助枚举的设备实现了直接绑定到`struct acpi_device`对象的ACPI驱动程序，但不建议任何新的驱动程序这样做。如前所述，通常为这些设备创建平台设备对象（尽管有少数例外情况在这里无关紧要），因此应使用平台驱动程序来处理它们，即使在这种情况下对应的ACPI设备对象是设备配置信息的唯一来源。对于每个具有相应`struct acpi_device`对象的设备，`ACPI_COMPANION()`宏返回指向它的指针，因此总是可以通过这种方式获取存储在ACPI设备对象中的设备配置信息。因此，`struct acpi_device`可以被视为内核与ACPI命名空间之间接口的一部分，而其他类型的设备对象（例如`struct pci_dev`或`struct platform_device`）则用于与其他系统的交互。

DMA支持
==========

通过ACPI枚举的DMA控制器应注册到系统中以提供对其资源的通用访问。例如，希望通过通用API调用`dma_request_chan()`对从设备可访问的驱动程序必须在其probe函数末尾像这样注册：

```c
err = devm_acpi_dma_controller_register(dev, xlate_func, dw);
/* 如果不是CONFIG_ACPI未启用的情况，处理错误 */
```

如果需要，可以实现自定义转换函数（通常`acpi_dma_simple_xlate()`就足够了），该函数将`struct acpi_dma_spec`提供的FixedDMA资源转换为相应的DMA通道。在这种情况下的一段代码可能如下所示：

```c
#ifdef CONFIG_ACPI
struct filter_args {
    /* 提供filter_func所需的信息 */
    ...
};

static bool filter_func(struct dma_chan *chan, void *param)
{
    /* 选择合适的通道 */
    ...
}

static struct dma_chan *xlate_func(struct acpi_dma_spec *dma_spec,
                                   struct acpi_dma *adma)
{
    dma_cap_mask_t cap;
    struct filter_args args;

    /* 准备filter_func的参数 */
    ...
    return dma_request_channel(cap, filter_func, &args);
}
#else
static struct dma_chan *xlate_func(struct acpi_dma_spec *dma_spec,
                                   struct acpi_dma *adma)
{
    return NULL;
}
#endif
```

`dma_request_chan()`将为每个注册的DMA控制器调用`xlate_func()`。在`xlate_func`函数中，必须基于`struct acpi_dma_spec`中的信息和`struct acpi_dma`提供的控制器属性选择合适的通道。
客户必须使用与特定 FixedDMA 资源相对应的字符串参数调用 `dma_request_chan()`。默认情况下，“tx”表示 FixedDMA 资源数组的第一个条目，“rx”表示第二个条目。下表展示了一个布局示例：

```
设备 (I2C0)
{
    ...
方法 (_CRS, 0, NotSerialized)
    {
        名称 (DBUF, ResourceTemplate ()
        {
            FixedDMA (0x0018, 0x0004, Width32bit, _Y48)
            FixedDMA (0x0019, 0x0005, Width32bit, )
        })
    ...
}
}
```

因此，在这个示例中，请求线为 0x0018 的 FixedDMA 是 “tx”，下一个则是 “rx”。

在一些复杂的情况下，客户不幸地需要直接调用 `acpi_dma_request_slave_chan_by_index()` 并通过其索引来选择特定的 FixedDMA 资源。

命名中断
=========

通过 ACPI 列举的驱动程序可以在 ACPI 表中为中断指定名称，这些名称可以用于获取驱动程序中的 IRQ 编号。
中断名称可以列在 `_DSD` 中作为 ‘interrupt-names’。这些名称应该作为一个字符串数组列出，并映射到 ACPI 表中的 `Interrupt()` 资源，对应于它们的索引。
下表展示了其使用的示例：

```
设备 (DEV0) {
    ...
名称 (_CRS, ResourceTemplate() {
            ...
中断 (ResourceConsumer, Level, ActiveHigh, Exclusive) {
                0x20,
                0x24
            }
        })

        名称 (_DSD, Package () {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "interrupt-names", Package () { "default", "alert" } },
            }
        ...
})
}
```

中断名称 ‘default’ 将对应 `Interrupt()` 资源中的 0x20，而 ‘alert’ 对应 0x24。请注意，只有 `Interrupt()` 资源被映射，而不是 `GpioInt()` 或类似的资源。
驱动程序可以通过将 `fwnode` 和中断名称作为参数传递给函数 `fwnode_irq_get_byname()`，以获取对应的 IRQ 编号。

SPI 串行总线支持
==================

SPI 总线后面的从设备会附加一个 `SpiSerialBus` 资源。这些资源由 SPI 核心自动提取，并且一旦总线驱动程序调用 `spi_register_master()` 后，从设备会被枚举。
以下是一个 SPI 从设备的 ACPI 命名空间示例：

```acpi
Device (EEP0)
{
    Name (_ADR, 1)
    Name (_CID, Package () {
        "ATML0025",
        "AT25",
    })
    ..
    Method (_CRS, 0, NotSerialized)
    {
        SPISerialBus(1, PolarityLow, FourWireMode, 8,
            ControllerInitiated, 1000000, ClockPolarityLow,
            ClockPhaseFirst, "\\_SB.PCI0.SPI1",)
    }
    ..
}
```

SPI 设备驱动程序只需像平台设备驱动程序那样添加 ACPI ID。下面是一个例子，我们为 `at25` SPI EEPROM 驱动添加 ACPI 支持（这是为了上述 ACPI 片段）：

```c
static const struct acpi_device_id at25_acpi_match[] = {
    { "AT25", 0 },
    { }
};
MODULE_DEVICE_TABLE(acpi, at25_acpi_match);

static struct spi_driver at25_driver = {
    .driver = {
        ..
    .acpi_match_table = at25_acpi_match,
    },
};
```

请注意，这个驱动程序实际上需要更多信息，如 EEPROM 的页大小等。这些信息可以通过 `_DSD` 方法传递，如下所示：

```acpi
Device (EEP0)
{
    ..
    Name (_DSD, Package ()
    {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () { "size", 1024 },
            Package () { "pagesize", 32 },
            Package () { "address-width", 16 },
        }
    })
}
```

然后，`at25` SPI 驱动程序可以在 `->probe()` 阶段通过调用设备属性 API 获取此配置，如下所示：

```c
err = device_property_read_u32(dev, "size", &size);
if (err)
    ...error handling..

err = device_property_read_u32(dev, "pagesize", &page_size);
if (err)
    ...error handling..

err = device_property_read_u32(dev, "address-width", &addr_width);
if (err)
    ...error handling..
```
I2C串行总线支持
======================

I2C总线控制器后面的从设备只需要像平台和SPI驱动程序那样添加ACPI ID。一旦适配器注册，I2C核心会自动枚举控制器设备后的任何从设备。以下是向现有的mpu3050输入驱动程序添加ACPI支持的示例：

```c
	static const struct acpi_device_id mpu3050_acpi_match[] = {
		{ "MPU3050", 0 },
		{ }
	};
	MODULE_DEVICE_TABLE(acpi, mpu3050_acpi_match);

	static struct i2c_driver mpu3050_i2c_driver = {
		.driver	= {
			.name	= "mpu3050",
			.pm	= &mpu3050_pm,
			.of_match_table = mpu3050_of_match,
			.acpi_match_table = mpu3050_acpi_match,
		},
		.probe		= mpu3050_probe,
		.remove		= mpu3050_remove,
		.id_table	= mpu3050_ids,
	};
	module_i2c_driver(mpu3050_i2c_driver);
```

PWM设备引用
=======================

有时一个设备可以是PWM通道的消费者。显然，操作系统需要知道这一点。为了提供这种映射，引入了一个特殊的属性，例如：

```acpi
    Device (DEV)
    {
        Name (_DSD, Package ()
        {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () { "compatible", Package () { "pwm-leds" } },
            Package () { "label", "alarm-led" },
            Package () { "pwms",
                Package () {
                    "\\_SB.PCI0.PWM",  // <PWM设备引用>
                    0,                 // <PWM索引>
                    600000000,         // <PWM周期>
                    0,                 // <PWM标志>
                }
            }
        })
        ..
}
```

在上述示例中，基于PWM的LED驱动程序引用了\_SB.PCI0.PWM设备的PWM通道0，并设置了初始周期为600毫秒（请注意该值是以纳秒为单位）。

GPIO支持
============

ACPI 5引入了两种新的资源来描述GPIO连接：GpioIo 和 GpioInt。这些资源可用于将设备使用的GPIO编号传递给驱动程序。ACPI 5.1通过_DSD（设备特定数据）扩展了这一功能，使得能够命名GPIO等信息。例如：

```acpi
	Device (DEV)
	{
		Method (_CRS, 0, NotSerialized)
		{
			Name (SBUF, ResourceTemplate()
			{
				// 用于开启/关闭设备
				GpioIo (Exclusive, PullNone, 0, 0, IoRestrictionOutput,
					"\\_SB.PCI0.GPI0", 0, ResourceConsumer) { 85 }

				// 设备中断
				GpioInt (Edge, ActiveHigh, ExclusiveAndWake, PullNone, 0,
					 "\\_SB.PCI0.GPI0", 0, ResourceConsumer) { 88 }
			}

			Return (SBUF)
		}

		// ACPI 5.1 _DSD 用于命名GPIO
		Name (_DSD, Package ()
		{
			ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
			Package ()
			{
				Package () { "power-gpios", Package () { ^DEV, 0, 0, 0 } },
				Package () { "irq-gpios", Package () { ^DEV, 1, 0, 0 } },
			}
		})
		..
}
```

这些GPIO编号是相对于控制器的，路径“\\_SB.PCI0.GPI0”指定了到控制器的路径。为了在Linux中使用这些GPIO，我们需要将它们转换为相应的Linux GPIO描述符。有一个标准的GPIO API用于此目的，详细文档见`Documentation/admin-guide/gpio/`。在上述示例中，我们可以使用如下代码获取两个相应的GPIO描述符：

```c
#include <linux/gpio/consumer.h>
..
struct gpio_desc *irq_desc, *power_desc;

irq_desc = gpiod_get(dev, "irq");
if (IS_ERR(irq_desc))
	/* 处理错误 */

power_desc = gpiod_get(dev, "power");
if (IS_ERR(power_desc))
	/* 处理错误 */

/* 现在我们可以使用GPIO描述符 */
```

还有devm_*版本的函数，可以在设备释放时释放描述符。有关与GPIO相关的_DSD绑定的更多信息，请参阅`Documentation/firmware-guide/acpi/gpio-properties.rst`。
RS-485支持
==============

ACPI _DSD（设备特定数据）可用于描述UART的RS-485能力。
例如：

```acpi
Device (DEV)
{
    ..
// ACPI 5.1 _DSD 用于描述 RS-485 能力
    Name (_DSD, Package ()
    {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package ()
        {
            Package () {"rs485-rts-active-low", Zero},
            Package () {"rs485-rx-active-high", Zero},
            Package () {"rs485-rx-during-tx", Zero},
        }
    })
    ..
}
```

多功能设备 (MFD 设备)
===========

MFD 设备将其子设备注册为平台设备。对于子设备，需要有一个 ACPI 句柄，以便它们可以引用与其相关的 ACPI 命名空间中的部分。在 Linux 的 MFD 子系统中，我们提供了两种方法：

  - 子设备共享父设备的 ACPI 句柄
- MFD 单元可以指定设备的 ACPI ID

对于第一种情况，MFD 驱动程序无需执行任何操作。生成的子平台设备将通过 ACPI_COMPANION() 指向父设备。

如果 ACPI 命名空间中有一个设备可以通过 ACPI ID 或 ACPI ADR 进行匹配，则单元应设置如下：

```c
static struct mfd_cell_acpi_match my_subdevice_cell_acpi_match = {
    .pnpid = "XYZ0001",
    .adr = 0,
};

static struct mfd_cell my_subdevice_cell = {
    .name = "my_subdevice",
    /* 设置相对于父设备的资源 */
    .acpi_match = &my_subdevice_cell_acpi_match,
};
```

ACPI ID "XYZ0001" 将用于查找 MFD 设备下的直接 ACPI 设备，并且如果找到该设备，它将与生成的子平台设备绑定。

设备树命名空间链接设备 ID
====================================

设备树协议使用基于“compatible”属性的设备识别，其值是一个字符串或字符串数组，这些字符串由驱动程序和驱动核心识别为设备标识符。所有这些字符串可以被视为类似于 ACPI/PNP 设备 ID 命名空间的设备识别命名空间。因此，原则上，对于已有设备树（DT）命名空间中存在识别字符串的设备来说，分配一个新的（可能是冗余的）ACPI/PNP 设备 ID 是不必要的，尤其是当这个 ID 仅用于表明某个设备与另一个设备兼容时，假设内核中已经有相应的驱动程序。

在 ACPI 中，名为 _CID（兼容 ID）的设备识别对象用于列出给定设备兼容的其他设备的 ID，但这些 ID 必须属于 ACPI 规范规定的命名空间之一（详见 ACPI 6.0 第 6.1.2 节），而设备树命名空间并不在其中。

此外，规范要求所有表示设备的 ACPI 对象必须包含一个 _HID 或 _ADR 识别对象（见 ACPI 6.0 第 6.1 节）。对于不可枚举的总线类型，此对象必须是 _HID，其值也必须来自规范规定的命名空间之一。
特殊的 DT 命名空间链接设备 ID，即 PRP0001，提供了一种方法来在 ACPI 中使用现有的 DT 兼容设备标识，并同时满足 ACPI 规范中的上述要求。具体来说，如果 _HID 返回 PRP0001，ACPI 子系统将查找设备对象的 _DSD 中的“兼容”属性，并使用该属性的值来识别相应的设备，这类似于原始 DT 设备标识算法。如果“兼容”属性不存在或其值无效，则该设备不会被 ACPI 子系统枚举。否则，它将自动作为平台设备进行枚举（除非存在从设备到其父设备的 I2C 或 SPI 链接，在这种情况下，ACPI 核心会将设备枚举留给父设备的驱动程序），并将使用“兼容”属性值中的标识字符串来为设备寻找驱动程序，以及 _CID 列出的设备 ID（如果存在）。

类似地，如果 PRP0001 出现在由 _CID 返回的设备 ID 列表中，则“兼容”属性值（如果存在且有效）列出的标识字符串将用于寻找匹配设备的驱动程序，但在这种情况下，它们相对于 _HID 和 _CID 中其他设备 ID 的优先级取决于 PRP0001 在 _CID 返回包中的位置。具体而言，_HID 返回的并在 _CID 返回包中位于 PRP0001 之前的设备 ID 将首先被检查。同样在这种情况下，设备将被枚举到的总线类型取决于 _HID 返回的设备 ID。

例如，以下 ACPI 示例可用于枚举 lm75 类型的 I2C 温度传感器并使用 Device Tree 命名空间链接将其与驱动程序匹配：

```acpi
Device (TMP0)
{
    Name (_HID, "PRP0001")
    Name (_DSD, Package () {
        ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
        Package () {
            Package () { "compatible", "ti,tmp75" },
        }
    })
    Method (_CRS, 0, Serialized)
    {
        Name (SBUF, ResourceTemplate ()
        {
            I2cSerialBusV2 (0x48, ControllerInitiated,
                400000, AddressingMode7Bit,
                "\\_SB.PCI0.I2C1", 0x00,
                ResourceConsumer, , Exclusive,)
        })
        Return (SBUF)
    }
}
```

定义具有返回 PRP0001 的 _HID 但没有 _DSD 中的“兼容”属性或 _CID 的设备对象是有效的，只要其祖先之一提供了带有有效“兼容”属性的 _DSD。这样的设备对象被视为附加的“块”，为复合祖先设备的驱动程序提供层次配置信息。然而，只有当所有由关联的 _DSD（无论是设备对象本身的 _DSD 还是在上述“复合设备”情况下的祖先 _DSD）返回的属性都可以在 ACPI 环境中使用时，才能从设备对象的 _HID 或 _CID 返回 PRP0001。否则，_DSD 本身被视为无效，因此它返回的“兼容”属性也没有意义。

更多信息请参见 `Documentation/firmware-guide/acpi/DSD-properties-rules.rst`。

### PCI 层次表示

有时根据 PCI 设备在 PCI 总线上的位置来枚举 PCI 设备可能是有用的。例如，某些系统使用直接焊接在主板上的固定位置的 PCI 设备（如以太网、Wi-Fi、串行端口等）。在这种情况下，可以知道 PCI 设备在 PCI 总线拓扑中的位置来引用这些 PCI 设备。

为了标识一个 PCI 设备，需要完整的层次描述，从芯片组根端口到最终设备，经过所有中间的板载桥接器/交换机。
例如，假设我们有一个带有PCIe串口的系统，该串口使用的是焊接在主板上的Exar XR17V3521芯片。这个UART芯片还包含16个GPIO，并且我们希望为这些引脚添加属性`gpio-line-names` [1]_。在这种情况下，针对此组件的`lspci`输出如下：

	07:00.0 Serial controller: Exar Corp. XR17V3521 Dual PCIe UART (rev 03)

完整的`lspci`输出（手动缩短）如下：

	00:00.0 Host bridge: Intel Corp... Host Bridge (rev 0d)
	..
00:13.0 PCI bridge: Intel Corp... PCI Express Port A #1 (rev fd)
	00:13.1 PCI bridge: Intel Corp... PCI Express Port A #2 (rev fd)
	00:13.2 PCI bridge: Intel Corp... PCI Express Port A #3 (rev fd)
	00:14.0 PCI bridge: Intel Corp... PCI Express Port B #1 (rev fd)
	00:14.1 PCI bridge: Intel Corp... PCI Express Port B #2 (rev fd)
	..
05:00.0 PCI bridge: Pericom Semiconductor Device 2404 (rev 05)
	06:01.0 PCI bridge: Pericom Semiconductor Device 2404 (rev 05)
	06:02.0 PCI bridge: Pericom Semiconductor Device 2404 (rev 05)
	06:03.0 PCI bridge: Pericom Semiconductor Device 2404 (rev 05)
	07:00.0 Serial controller: Exar Corp. XR17V3521 Dual PCIe UART (rev 03) <-- Exar
	..

总线拓扑结构如下：

	-[0000:00]-+-00.0
	           ..
+-13.0-[01]----00.0
	           +-13.1-[02]----00.0
	           +-13.2-[03]--
	           +-14.0-[04]----00.0
	           +-14.1-[05-09]----00.0-[06-09]--+-01.0-[07]----00.0 <-- Exar
	           |                               +-02.0-[08]----00.0
	           |                               \-03.0-[09]--
	           ..
\-1f.1

为了描述PCI总线上的Exar设备，我们必须从芯片组桥接器（也称为“根端口”）的ACPI名称开始，其地址为：

	Bus: 0 - Device: 14 - Function: 1

要找到此信息，需要拆解BIOS中的ACPI表，特别是DSDT（参见[2]_）：

	mkdir ~/tables/
	cd ~/tables/
	acpidump > acpidump
	acpixtract -a acpidump
	iasl -e ssdt?.* -d dsdt.dat

现在，在dsdt.dsl中，我们需要查找与0x14（设备）和0x01（功能）相关的设备。在这种情况下，我们可以找到以下设备：

	Scope (_SB.PCI0)
	{
	... 其他定义 ...
Device (RP02)
		{
			Method (_ADR, 0, NotSerialized)  // _ADR: 地址
			{
				If ((RPA2 != Zero))
				{
					Return (RPA2) /* \RPA2 */
				}
				Else
				{
					Return (0x00140001)
				}
			}
	... 其他定义 ...
该方法_ADR [3]_返回了我们要找的设备/功能对。利用这些信息并分析上述`lspci`输出（设备列表和设备树），我们可以编写以下Exar PCIe UART的ACPI描述，同时添加其GPIO线名列表：

	Scope (_SB.PCI0.RP02)
	{
		Device (BRG1) // 桥接器
		{
			Name (_ADR, 0x0000)

			Device (BRG2) // 桥接器
			{
				Name (_ADR, 0x00010000)

				Device (EXAR)
				{
					Name (_ADR, 0x0000)

					Name (_DSD, Package ()
					{
						ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
						Package ()
						{
							Package ()
							{
								"gpio-line-names",
								Package ()
								{
									"mode_232",
									"mode_422",
									"mode_485",
									"misc_1",
									"misc_2",
									"misc_3",
									"",
									"",
									"aux_1",
									"aux_2",
									"aux_3",
								}
							}
						}
					})
				}
			}
		}
	}

位置"_SB.PCI0.RP02"是通过在dsdt.dsl表中进行上述调查获得的，而设备名称"BRG1"、"BRG2"和"EXAR"是通过分析Exar UART在PCI总线拓扑中的位置创建的。

参考文献
========

.. [1] Documentation/firmware-guide/acpi/gpio-properties.rst

.. [2] Documentation/admin-guide/acpi/initrd_table_override.rst

.. [3] ACPI 规范版本6.3 - 第6.1.1段 _ADR 地址)
    https://uefi.org/sites/default/files/resources/ACPI_6_3_May16.pdf,
    引用日期：2020-11-18
