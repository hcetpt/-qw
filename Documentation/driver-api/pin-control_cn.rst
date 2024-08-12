===============================
PINCTRL (引脚控制) 子系统
===============================

本文档概述了 Linux 中的引脚控制子系统。

此子系统涉及：

- 列举和命名可控制的引脚

- 引脚、焊盘、触点（等）的多路复用，详情请参见下文

- 引脚、焊盘、触点（等）的配置，例如由软件控制的偏置以及针对特定驱动模式的引脚配置，如上拉、下拉、开漏、负载电容等
顶层接口
===================

定义：

- 一个**PIN 控制器**是一个硬件部件，通常是一组寄存器，能够控制**PINs**。它可能能够为单个引脚或一组引脚进行多路复用、偏置、设置负载电容、设置驱动强度等。
- **PINs** 等同于焊盘、触点、球或其他您想要控制的封装输入或输出线，并通过范围 0..maxpin 内的无符号整数表示。这个编号空间是每个 PIN 控制器本地的，因此系统中可能存在多个这样的编号空间。这个引脚空间可能是稀疏的 —— 即可能存在没有引脚存在的空缺编号。
当一个 PIN 控制器实例化时，它将向引脚控制框架注册一个描述符，该描述符包含一个引脚描述符数组，描述了该特定引脚控制器处理的所有引脚。
以下是一个从下面看的 PGA（引脚网格阵列）芯片的例子：

        A   B   C   D   E   F   G   H

   8    o   o   o   o   o   o   o   o

   7    o   o   o   o   o   o   o   o

   6    o   o   o   o   o   o   o   o

   5    o   o   o   o   o   o   o   o

   4    o   o   o   o   o   o   o   o

   3    o   o   o   o   o   o   o   o

   2    o   o   o   o   o   o   o   o

   1    o   o   o   o   o   o   o   o

为了注册一个引脚控制器并命名这个封装上的所有引脚，我们可以在我们的驱动程序中这样做：

.. code-block:: c

	#include <linux/pinctrl/pinctrl.h>

	const struct pinctrl_pin_desc foo_pins[] = {
		PINCTRL_PIN(0, "A8"),
		PINCTRL_PIN(1, "B8"),
		PINCTRL_PIN(2, "C8"),
		..
		PINCTRL_PIN(61, "F1"),
		PINCTRL_PIN(62, "G1"),
		PINCTRL_PIN(63, "H1"),
	};

	static struct pinctrl_desc foo_desc = {
		.name = "foo",
		.pins = foo_pins,
		.npins = ARRAY_SIZE(foo_pins),
		.owner = THIS_MODULE,
	};

	int __init foo_init(void)
	{
		int error;

		struct pinctrl_dev *pctl;

		error = pinctrl_register_and_init(&foo_desc, <PARENT>, NULL, &pctl);
		if (error)
			return error;

		return pinctrl_enable(pctl);
	}

为了启用引脚控制子系统及其 PINMUX 和 PINCONF 子组以及选定的驱动程序，您需要从您的机器的 Kconfig 条目中选择它们，因为这些与它们所使用的机器紧密集成。请参阅 `arch/arm/mach-ux500/Kconfig` 以获取示例。
引脚通常具有比这更复杂的名字。您可以在您的芯片数据手册中找到这些名字。请注意，核心 pinctrl.h 文件提供了一个名为 `PINCTRL_PIN()` 的高级宏来创建结构条目。如您所见，引脚是从左上角的 0 到右下角的 63 进行编号的。
这种编号方式是任意选择的，在实践中，您需要考虑您的编号系统，以便与驱动程序中的寄存器布局等相匹配，否则代码可能会变得复杂。您还必须考虑与 PIN 控制器可能处理的 GPIO 范围的偏移量匹配。
对于具有 467 个焊盘而不是实际引脚的封装，编号方式将如下所示，沿着芯片边缘走动，这似乎也是业界标准（所有这些焊盘都有名称）：


     0 ..... 104
   466        105
     .
### 数组示例：
358        224  
    357 .... 225  

### 引脚组
#### 

许多控制器需要处理一组引脚，因此引脚控制器子系统有一种机制来枚举引脚组并检索属于特定组的实际枚举引脚。例如，假设我们有一组引脚在{0, 8, 16, 24}上处理SPI接口，并且有一组引脚在{24, 25}上处理I2C接口。
这些组可以通过实现一些通用的`pinctrl_ops`接口像下面这样呈现给引脚控制子系统：

```c
#include <linux/pinctrl/pinctrl.h>

static const unsigned int spi0_pins[] = {0, 8, 16, 24};
static const unsigned int i2c0_pins[] = {24, 25};

static const struct pingroup foo_groups[] = {
    PINCTRL_PINGROUP("spi0_grp", spi0_pins, ARRAY_SIZE(spi0_pins)),
    PINCTRL_PINGROUP("i2c0_grp", i2c0_pins, ARRAY_SIZE(i2c0_pins)),
};

static int foo_get_groups_count(struct pinctrl_dev *pctldev)
{
    return ARRAY_SIZE(foo_groups);
}

static const char *foo_get_group_name(struct pinctrl_dev *pctldev,
                                      unsigned int selector)
{
    return foo_groups[selector].name;
}

static int foo_get_group_pins(struct pinctrl_dev *pctldev,
                              unsigned int selector,
                              const unsigned int **pins,
                              unsigned int *npins)
{
    *pins = foo_groups[selector].pins;
    *npins = foo_groups[selector].npins;
    return 0;
}

static struct pinctrl_ops foo_pctrl_ops = {
    .get_groups_count = foo_get_groups_count,
    .get_group_name = foo_get_group_name,
    .get_group_pins = foo_get_group_pins,
};

static struct pinctrl_desc foo_desc = {
    ...
    .pctlops = &foo_pctrl_ops,
};
```

引脚控制子系统将调用`.get_groups_count()`函数来确定合法选择器的总数，然后它将调用其他函数来获取组的名称和引脚。维护组的数据结构由驱动程序负责，这只是个简单的例子——实际上你可能需要在你的组结构中有更多的条目，例如与每个组相关的特定寄存器范围等。

### 引脚配置
#### 

引脚有时可以以各种方式通过软件进行配置，这主要与它们作为输入或输出时的电子特性有关。例如，你可以使一个输出引脚处于高阻抗（Hi-Z）状态，或者“三态”意味着它实际上是断开连接的。你可能能够使用某种电阻值将输入引脚连接到VDD或GND，以便当没有东西驱动与其相连的线路时，或当其未连接时，该引脚有一个稳定值——即上拉和下拉。
引脚配置可以通过向映射表中添加配置条目来编程；参见下面的`板/机器配置`部分。
配置参数的格式和含义，如上面的`PLATFORM_X_PULL_UP`，完全由引脚控制器驱动程序定义。
引脚配置驱动程序通过以下方式实现在引脚控制器操作中的回调来更改引脚配置：

```c
#include <linux/pinctrl/pinconf.h>
#include <linux/pinctrl/pinctrl.h>

#include "platform_x_pindefs.h"

static int foo_pin_config_get(struct pinctrl_dev *pctldev,
                              unsigned int offset,
                              unsigned long *config)
{
    struct my_conftype conf;

    /* ... 找到引脚@offset的设置 ... */

    *config = (unsigned long) conf;
}

static int foo_pin_config_set(struct pinctrl_dev *pctldev,
                              unsigned int offset,
                              unsigned long config)
{
    struct my_conftype *conf = (struct my_conftype *) config;

    switch (*conf) {
        case PLATFORM_X_PULL_UP:
            ...
            break;
    }
}

static int foo_pin_config_group_get(struct pinctrl_dev *pctldev,
                                    unsigned selector,
                                    unsigned long *config)
{
    ...
}
```
```c
static int foo_pin_config_group_set(struct pinctrl_dev *pctldev,
					 unsigned selector,
					 unsigned long config)
{
	..
}

static struct pinconf_ops foo_pconf_ops = {
	.pin_config_get = foo_pin_config_get,
	.pin_config_set = foo_pin_config_set,
	.pin_config_group_get = foo_pin_config_group_get,
	.pin_config_group_set = foo_pin_config_group_set,
};

/* 针对某些引脚控制器处理的引脚配置操作 */
static struct pinctrl_desc foo_desc = {
	..
	.confops = &foo_pconf_ops,
};

// 与GPIO子系统的交互
// =================================

// GPIO驱动程序可能需要在同一物理引脚上执行各种类型的相同操作，这些引脚也已注册为引脚控制器的引脚。
// 首先，这两个子系统可以完全独立地使用，请参阅名为`来自驱动程序的引脚控制请求`_和
// `同时需要引脚控制和GPIO的驱动程序`_的部分以获取详细信息。但在某些情况下，需要在引脚和GPIO之间进行跨子系统的映射
// 由于引脚控制器子系统中的引脚空间是针对特定引脚控制器本地化的，我们需要一个映射，以便引脚控制子系统能够确定哪个引脚控制器
// 处理某个GPIO引脚的控制。因为单个引脚控制器可能复用了多个GPIO范围（通常SoC具有一个引脚集，
// 但内部有多个GPIO硅块，每个都建模为struct gpio_chip），可以将任意数量的GPIO范围添加到引脚控制器实例中，如下所示：

.. code-block:: c

	#include <linux/gpio/driver.h>
	#include <linux/pinctrl/pinctrl.h>

	struct gpio_chip chip_a;
	struct gpio_chip chip_b;

	static struct pinctrl_gpio_range gpio_range_a = {
		.name = "chip a",
		.id = 0,
		.base = 32,
		.pin_base = 32,
		.npins = 16,
		.gc = &chip_a,
	};

	static struct pinctrl_gpio_range gpio_range_b = {
		.name = "chip b",
		.id = 0,
		.base = 48,
		.pin_base = 64,
		.npins = 8,
		.gc = &chip_b;
	};

	int __init foo_init(void)
	{
		struct pinctrl_dev *pctl;
		..
		pinctrl_add_gpio_range(pctl, &gpio_range_a);
		pinctrl_add_gpio_range(pctl, &gpio_range_b);
		..
	}

// 因此，这个复杂的系统有一个引脚控制器处理两个不同的GPIO芯片。“chip a”有16个引脚，“chip b”有8个引脚。“chip a”和“chip b”有不同的`pin_base`，
// 这意味着GPIO范围的起始引脚编号。GPIO范围“chip a”从GPIO基址32开始，实际的引脚范围也从32开始。但是“chip b”的GPIO范围和引脚范围有不同的起始偏移量。
// “chip b”的GPIO范围从GPIO编号48开始，而“chip b”的引脚范围从64开始。我们可以使用这个`pin_base`将GPIO编号转换为实际的引脚编号。

// 它们映射在全球GPIO引脚空间中如下：

chip a:
 - GPIO范围 : [32 .. 47]
 - 引脚范围  : [32 .. 47]
chip b:
 - GPIO范围 : [48 .. 55]
 - 引脚范围  : [64 .. 71]

// 上述示例假设GPIO与引脚之间的映射是线性的。如果映射是稀疏或杂乱无章的，则可以在范围内编码任意引脚编号，如下所示：

.. code-block:: c

	static const unsigned int range_pins[] = { 14, 1, 22, 17, 10, 8, 6, 2 };

	static struct pinctrl_gpio_range gpio_range = {
		.name = "chip",
		.id = 0,
		.base = 32,
		.pins = &range_pins,
		.npins = ARRAY_SIZE(range_pins),
		.gc = &chip,
	};

// 在这种情况下，`pin_base`属性将被忽略。如果已知引脚组的名称，可以使用函数`pinctrl_get_group_pins()`初始化上述结构中的pins和npins元素，
// 例如对于引脚组"foo"：

.. code-block:: c

	pinctrl_get_group_pins(pctl, "foo", &gpio_range.pins, &gpio_range.npins);

// 当调用引脚控制子系统中的GPIO专用函数时，将使用这些范围通过检查和匹配所有控制器上的引脚来查找相应的引脚控制器。找到处理匹配范围的引脚控制器后，
// 将在其上调用GPIO专用函数。
```
以上是您提供的代码和文档的中文翻译。
对于所有涉及引脚偏置、引脚复用等功能，引脚控制器子系统将从传递进来的GPIO编号查找对应的引脚编号，并使用范围的内部信息来检索一个引脚编号。之后，该子系统将其传递给引脚控制驱动程序，以便驱动程序能够在其处理的编号范围内获得一个引脚编号。此外，它还会传递范围ID值，以便引脚控制器知道它应该处理哪个范围。
调用`pinctrl_add_gpio_range()`从引脚控制器驱动程序中是过时的做法。请参阅`Documentation/devicetree/bindings/gpio/gpio.txt`中的第2.1节以了解如何绑定引脚控制器和GPIO驱动程序。
PINMUX接口

这些调用使用pinmux_*命名前缀。不应有其他调用使用此前缀。
什么是引脚复用？

PINMUX，也称为垫片复用、球复用、备用功能或任务模式，是一种方式，芯片供应商在生产某种类型的电气封装时可以使用特定物理引脚（球、垫、针脚等）执行多个互斥的功能，具体取决于应用需求。这里的“应用”通常是指将封装焊接或连接到电子系统的方式，尽管框架也支持在运行时更改功能。
以下是一个PGA（引脚网格阵列）芯片从底部看的例子：

        A   B   C   D   E   F   G   H
      +---+
   8  | o | o   o   o   o   o   o   o
      |   |
   7  | o | o   o   o   o   o   o   o
      |   |
   6  | o | o   o   o   o   o   o   o
      +---+---+
   5  | o | o | o   o   o   o   o   o
      +---+---+               +---+
   4    o   o   o   o   o   o | o | o
                              |   |
   3    o   o   o   o   o   o | o | o
                              |   |
   2    o   o   o   o   o   o | o | o
      +-------+-------+-------+---+---+
   1  | o   o | o   o | o   o | o | o |
      +-------+-------+-------+---+---+

这不是俄罗斯方块游戏。需要思考的游戏是国际象棋。并非所有的PGA/BGA封装都像国际象棋棋盘一样，大型封装根据不同的设计模式可能在某些地方有“空洞”，但我们使用这个简单的例子作为示例。在这些引脚中，有些会被VCC和GND占用以向芯片供电，还有相当多的引脚会被大端口如外部内存接口所占用。剩余的引脚通常会受到引脚复用的影响。
上述8x8 PGA封装会有从0到63的引脚编号分配给其物理引脚。它将使用`pinctrl_register_pins()`和合适的数据集注册引脚名称为 { A1, A2, A3 ... H6, H7, H8 }，如前面所示。
在这个8x8 BGA封装中，引脚 { A8, A7, A6, A5 } 可以用作SPI端口（这四个引脚分别是：CLK, RXD, TXD, FRM）。在这种情况下，引脚B5可以用作通用GPIO引脚。然而，在另一种设置下，引脚 { A5, B5 } 可以用作I2C端口（这两个引脚是：SCL, SDA）。不用说，我们不能同时使用SPI端口和I2C端口。但是，在封装内部，执行SPI逻辑的硅片可以通过替代路由输出到引脚 { G4, G3, G2, G1 }。
在最底部一行的 { A1, B1, C1, D1, E1, F1, G1, H1 } 我们有一个特殊的情况——这是一个外部MMC总线，它可以是2位、4位或8位宽，它将分别消耗2个、4个或8个引脚，因此要么只使用 { A1, B1 }，要么使用 { A1, B1, C1, D1 }，或者全部使用。如果我们使用全部8位，当然就不能在引脚 { G4, G3, G2, G1 } 上使用SPI端口了。
这样，封装内存在的硅片块可以被复用并“复用”到不同的引脚范围上。通常，当代的SoC（系统级芯片）包含多个I2C、SPI、SDIO/MMC等硅片块，这些可以通过引脚复用设置路由到不同的引脚上。
由于通用I/O引脚（GPIO）通常总是短缺的，因此通常可以将几乎任何引脚用作GPIO引脚，只要它当前没有被其他I/O端口使用。
### Pinmux 规范

在针脚控制器子系统中，Pinmux 功能的目的是抽象并为用户选择在机器配置中实例化的设备提供 Pinmux 设置。它借鉴了时钟（clk）、GPIO 和调节器子系统的思路，因此设备可以请求其复用设置，同时也可能为例如 GPIO 请求单个针脚。规范如下：

- **功能（FUNCTIONS）** 可以通过位于内核 `drivers/pinctrl` 目录中的针脚控制子系统内的驱动程序进行切换。针脚控制驱动了解所有可能的功能。例如，在上面的例子中，你可以识别出三个 Pinmux 功能：一个用于 SPI，一个用于 I2C，还有一个用于 MMC。
- **功能（FUNCTIONS）** 假定可以从零开始在一个一维数组中枚举。在这种情况下，数组可能是这样的：{ spi0, i2c0, mmc0 }，代表三种可用的功能。
- **功能（FUNCTIONS）** 与 **针脚组（PIN GROUPS）** 在通用级别上定义——即特定的功能总是与特定的一组针脚组相关联，这可能只是一个针脚组，也可能是多个。在上述例子中，I2C 功能与针脚 { A5, B5 } 关联，这些针脚在控制器针脚空间中被枚举为 { 24, 25 }。
  - SPI 功能与针脚组 { A8, A7, A6, A5 } 和 { G4, G3, G2, G1 } 关联，它们分别被枚举为 { 0, 8, 16, 24 } 和 { 38, 46, 54, 62 }。
  - 同一针脚控制器上的组名必须是唯一的；同一控制器上的两个组不得具有相同的名称。
- **功能（FUNCTION）** 与 **针脚组（PIN GROUP）** 的组合确定了一组针脚的特定功能。功能、针脚组及其机器特定细节的知识存储在 Pinmux 驱动程序内部，而外部只知道枚举值，并且驱动核心可以请求：
  - 某个选择器（>= 0）对应的函数名称。
  - 与某个功能关联的一组组列表。
  - 激活该功能下列表中的某个组。

  如上所述，针脚组本身是自描述的，因此核心将从驱动程序中获取特定组的实际针脚范围。
- **功能（FUNCTIONS）** 和 **组（GROUPS）** 在特定的 **针脚控制器（PIN CONTROLLER）** 上由板级文件、设备树或其他类似的机器配置机制映射到特定设备，类似于调节器如何连接到设备，通常通过名称连接。定义一个针脚控制器、功能和组从而唯一地标识了一组针脚供特定设备使用。（如果一个功能只有一个可用的针脚组，则无需提供组名——核心将简单地选择第一个也是唯一可用的组。）

  在示例情况下，我们可以定义此特定机器应使用带有 pinmux 功能 fspi0 和组 gspi0 的设备 spi0，以及带有功能 fi2c0 和组 gi2c0 的 i2c0，在主针脚控制器上，我们得到这样的映射：

  ```c
  {
    {"map-spi0", spi0, pinctrl0, fspi0, gspi0},
    {"map-i2c0", i2c0, pinctrl0, fi2c0, gi2c0},
  }
  ```

  每个映射都必须分配状态名称、针脚控制器、设备和功能。组不是必需的——如果省略，则核心将选择驱动程序报告的适用于该功能的第一个组，这对于简单情况非常有用。
  可以将多个组映射到相同的设备、针脚控制器和功能组合。这是为了处理在不同配置下特定针脚控制器上的特定功能可能使用不同的针脚集的情况。
对于特定的`PIN CONTROLLER`使用特定的`PIN GROUP`实现特定`FUNCTION`的PINS遵循先到先得的原则。因此，如果其他设备的多路复用设置或GPIO针请求已经占用了您所需的物理针脚，则您将无法使用该针脚。为了获得（激活）一个新的设置，必须首先取消（去激活）旧的设置。
有时文档和硬件寄存器可能以焊盘（或“指”）而非针脚为中心——这些是封装内部硅片上的焊接表面，它们的数量可能与封装下实际的针脚/球数量不完全匹配。选择一个对你有意义的枚举方式。如果你仅能控制某些针脚，那么只定义这些针脚的枚举值也是合理的。
假设：

我们假设可能的功能到针脚组的映射数量受到硬件限制。即我们假设不存在任何功能都能映射到任意针脚的情况，就像电话交换机那样。因此，对于某一特定功能来说，可用的针脚组将被限制在少数几个选项（比如最多八种左右），而不是数百个或任意数量。这是我们通过检查现有pinmux硬件得出的特点，也是必要的假设，因为我们期望pinmux驱动程序向子系统呈现所有可能的功能与针脚组的映射关系。
Pinmux驱动程序
==================

pinmux核心负责防止针脚冲突，并调用pin控制器驱动来执行不同的设置。pinmux驱动程序的责任还包括进一步施加限制（例如根据负载推断电子限制等），以确定所请求的功能是否可以被允许。如果可行，则执行请求的多路复用设置并更新硬件以实现这一操作。
pinmux驱动程序需要提供一些回调函数，其中一些是可选的。通常会实现`.set_mux()`函数，用于向某些特定寄存器写入值以激活某个针脚的特定多路复用设置。
下面是一个简单的示例驱动，它通过设置MUX寄存器中的位0、1、2、3、4或5来选择特定的功能与一组针脚：

```c
#include <linux/pinctrl/pinctrl.h>
#include <linux/pinctrl/pinmux.h>

static const unsigned int spi0_0_pins[] = { 0, 8, 16, 24 };
static const unsigned int spi0_1_pins[] = { 38, 46, 54, 62 };
static const unsigned int i2c0_pins[] = { 24, 25 };
static const unsigned int mmc0_1_pins[] = { 56, 57 };
static const unsigned int mmc0_2_pins[] = { 58, 59 };
static const unsigned int mmc0_3_pins[] = { 60, 61, 62, 63 };

static const struct pingroup foo_groups[] = {
    PINCTRL_PINGROUP("spi0_0_grp", spi0_0_pins, ARRAY_SIZE(spi0_0_pins)),
    PINCTRL_PINGROUP("spi0_1_grp", spi0_1_pins, ARRAY_SIZE(spi0_1_pins)),
    PINCTRL_PINGROUP("i2c0_grp", i2c0_pins, ARRAY_SIZE(i2c0_pins)),
    PINCTRL_PINGROUP("mmc0_1_grp", mmc0_1_pins, ARRAY_SIZE(mmc0_1_pins)),
    PINCTRL_PINGROUP("mmc0_2_grp", mmc0_2_pins, ARRAY_SIZE(mmc0_2_pins)),
    PINCTRL_PINGROUP("mmc0_3_grp", mmc0_3_pins, ARRAY_SIZE(mmc0_3_pins)),
};

static int foo_get_groups_count(struct pinctrl_dev *pctldev)
{
    return ARRAY_SIZE(foo_groups);
}

static const char *foo_get_group_name(struct pinctrl_dev *pctldev,
                                      unsigned int selector)
{
    return foo_groups[selector].name;
}

static int foo_get_group_pins(struct pinctrl_dev *pctldev, unsigned int selector,
                              const unsigned int **pins,
                              unsigned int *npins)
{
    *pins = foo_groups[selector].pins;
    *npins = foo_groups[selector].npins;
    return 0;
}

static struct pinctrl_ops foo_pctrl_ops = {
    .get_groups_count = foo_get_groups_count,
    .get_group_name = foo_get_group_name,
    .get_group_pins = foo_get_group_pins,
};

static const char * const spi0_groups[] = { "spi0_0_grp", "spi0_1_grp" };
static const char * const i2c0_groups[] = { "i2c0_grp" };
static const char * const mmc0_groups[] = { "mmc0_1_grp", "mmc0_2_grp", "mmc0_3_grp" };

static const struct pinfunction foo_functions[] = {
    PINCTRL_PINFUNCTION("spi0", spi0_groups, ARRAY_SIZE(spi0_groups)),
    PINCTRL_PINFUNCTION("i2c0", i2c0_groups, ARRAY_SIZE(i2c0_groups)),
    PINCTRL_PINFUNCTION("mmc0", mmc0_groups, ARRAY_SIZE(mmc0_groups)),
};

static int foo_get_functions_count(struct pinctrl_dev *pctldev)
{
    return ARRAY_SIZE(foo_functions);
}

static const char *foo_get_fname(struct pinctrl_dev *pctldev, unsigned int selector)
{
    return foo_functions[selector].name;
}

static int foo_get_groups(struct pinctrl_dev *pctldev, unsigned int selector,
                          const char * const **groups,
                          unsigned int * const ngroups)
{
    *groups = foo_functions[selector].groups;
    *ngroups = foo_functions[selector].ngroups;
    return 0;
}

static int foo_set_mux(struct pinctrl_dev *pctldev, unsigned int selector,
                       unsigned int group)
{
    u8 regbit = BIT(group);

    writeb((readb(MUX) | regbit), MUX);
    return 0;
}

static struct pinmux_ops foo_pmxops = {
    .get_functions_count = foo_get_functions_count,
    .get_function_name = foo_get_fname,
    .get_function_groups = foo_get_groups,
    .set_mux = foo_set_mux,
    .strict = true,
};

/* Pinmux操作由某个pin控制器处理 */
static struct pinctrl_desc foo_desc = {
    ..
    .pctlops = &foo_pctrl_ops,
    .pmxops = &foo_pmxops,
};

在本示例中，同时激活多路复用0和2，设置位0和2时，共同使用了针脚24，因此会发生冲突。同样的情况也适用于多路复用1和5，它们共享针脚62。
pinmux子系统的美妙之处在于，因为它跟踪所有针脚及其使用者，所以它已经拒绝了不可能的请求，因此驱动程序无需担心这类问题——当它接收到一个选择器时，pinmux子系统确保没有其他设备或GPIO分配正在使用选定的针脚。因此，在控制寄存器中，位0和2，或1和5永远不会同时被设置。
上述所有函数都是pinmux驱动程序必须实现的。
### 引脚控制与GPIO子系统的交互

请注意，以下内容意味着使用案例是通过在`<linux/gpio/consumer.h>`中的API以及使用`gpiod_get()`等函数从Linux内核中使用某个引脚。存在一些情况，您可能正在使用数据手册中称为“GPIO模式”的东西，但实际上这只是为特定设备配置的电气设置。请参阅下面名为`GPIO模式陷阱`的部分以了解更多关于此场景的信息。

公共引脚复用API包含两个函数，分别命名为`pinctrl_gpio_request()`和`pinctrl_gpio_free()`。这两个函数**仅**应由gpiolib基础驱动程序在其`.request()`和`.free()`语义中调用。
同样地，`pinctrl_gpio_direction_input()` / `pinctrl_gpio_direction_output()`也**仅**应在各自的`.direction_input()` / `.direction_output()` gpiolib实现中调用。

**注意**：平台和单个驱动程序**不应**请求控制GPIO引脚（例如，进行复用）。相反，应该实现一个合适的gpiolib驱动程序，并让该驱动程序为其引脚请求适当的复用和其他控制。

函数列表可能会变得很长，特别是如果您可以将每个单独的引脚独立于其他引脚转换为GPIO引脚，并尝试定义每个引脚作为一种功能的方法时。
在这种情况下，对于每种GPIO设置和设备功能，函数数组会达到64条目。

出于这个原因，引脚控制驱动程序可以实现两个函数来仅在一个单独的引脚上启用GPIO：“.gpio_request_enable()”和“.gpio_disable_free()”。

此函数会传入由引脚控制器核心识别的受影响GPIO范围，因此您可以知道哪些GPIO引脚受到请求操作的影响。

如果您的驱动程序需要从框架获得指示以确定GPIO引脚是否用于输入或输出，您可以实现`gpio_set_direction()`函数。如前所述，这应当由gpiolib驱动程序调用，并将受影响的GPIO范围、引脚偏移量和期望的方向传递给此函数。

除了使用这些特殊函数之外，完全允许为每个GPIO引脚使用命名函数，`pinctrl_gpio_request()`将尝试获取函数“gpioN”，其中"N"是全局GPIO引脚编号，前提是未注册特殊的GPIO处理程序。
GPIO模式的陷阱
=============

由于硬件工程师所采用的命名惯例，其中“GPIO”被赋予了与内核处理方式不同的含义，开发人员可能会对数据表中提到的某引脚可以设置为“GPIO模式”感到困惑。看起来，硬件工程师所说的“GPIO模式”并不一定是指内核接口`<linux/gpio/consumer.h>`中所暗示的使用场景：即从内核代码中获取一个引脚，然后监听其输入或驱动高低电平以断言/取消断言某些外部线路。
相反，硬件工程师认为“GPIO模式”意味着可以通过软件控制引脚的一些电气特性，而在该引脚处于其他模式（如为某个设备复用）时则无法进行这种控制。
引脚的GPIO部分及其与特定引脚控制器配置和复用逻辑之间的关系可以有多种构建方式。以下是两个例子：

**示例 (A):**

```
                  引脚配置
                  逻辑寄存器
                  |              +-- SPI
物理引脚 ---- 垫片 ---- 引脚复用器 --+-- I2C
                                        |   +-- mmc
                                        |   +-- GPIO
                                        引脚
                                        复用
                                        逻辑寄存器
```

在此种情况下，无论引脚是否用于GPIO功能，都可以配置一些电气特性。如果你将GPIO复用到引脚上，还可以通过“GPIO”寄存器来驱动其高低电平。
另外，即使引脚由某个特定外设控制，仍然可以应用所需的引脚配置属性。因此，GPIO功能与其他使用该引脚的设备是正交的。
在这种布局下，引脚控制器中与GPIO相关的寄存器（或GPIO硬件模块的寄存器）可能位于仅用于GPIO驱动的单独内存范围内，而处理引脚配置和引脚复用的寄存器范围则放置在不同的内存区域，并且在数据手册中也有独立的部分。
在这样的硬件上，结构体`pinmux_ops`中有一个标志“strict”，用于检查并拒绝同时访问同一引脚的GPIO和引脚复用消费者。pinctrl驱动程序应根据实际情况设置此标志。

**示例 (B):**

```
                  引脚配置
                  逻辑寄存器
                  |              +-- SPI
物理引脚 ---- 垫片 ---- 引脚复用器 --+-- I2C
                  |      |           +-- mmc
                  |      |
                  GPIO   引脚
                              复用
                              逻辑寄存器
```

在此种情况下，GPIO功能始终可以启用，例如，可以使用GPIO输入来“监视”SPI/I2C/MMC信号在传输过程中的情况。通过在GPIO块上执行错误操作很可能会干扰引脚上的通信，因为GPIO功能实际上从未真正断开。GPIO、引脚配置和引脚复用寄存器可能被放置在同一内存范围内，并且在数据手册的同一部分中，尽管这并非必须如此。
在某些引脚控制器中，尽管物理引脚的设计与(B)相同，但GPIO功能仍不能与外设功能同时启用。因此，“strict”标志应该被设置，禁止GPIO和其他复用设备的同时激活。
但从内核的角度来看，这些是硬件的不同方面，应当放在不同的子系统中：

- 控制引脚电气特性的寄存器（或寄存器中的字段），例如偏置和驱动强度，应通过pinctrl子系统暴露，作为“引脚配置”设置。
控制信号多路复用（从诸如I2C、MMC或GPIO等其他硬件模块）到引脚的寄存器（或寄存器内的字段）应通过`pinctrl`子系统暴露，作为多路复用功能。

控制GPIO功能的寄存器（或寄存器内的字段），例如设置GPIO的输出值、读取GPIO的输入值或设置GPIO引脚方向，应通过GPIO子系统暴露，并且如果它们还支持中断功能，则通过`irqchip`抽象层暴露。

根据确切的硬件寄存器设计，GPIO子系统暴露的一些功能可能需要调用`pinctrl`子系统来协调跨硬件模块的寄存器设置。特别是对于具有独立GPIO和引脚控制器硬件模块的硬件，例如GPIO方向由引脚控制器硬件模块中的寄存器确定，而不是GPIO硬件模块。

引脚的电气属性，如偏置和驱动强度，可以放在特定引脚的寄存器中，在所有情况下或者在情况(B)下作为GPIO寄存器的一部分。这并不意味着这些属性必然与Linux内核所称的“GPIO”相关联。

示例：一个引脚通常被多路复用为UART发送线。但在系统休眠期间，我们需要将此引脚置于“GPIO模式”并将其接地。
如果你为这个引脚做一对一映射到GPIO子系统，你可能会开始认为你需要想出一个非常复杂的方案，即该引脚同时用于UART发送和GPIO，你会获取一个引脚控制句柄并将其设置为某种状态以启用UART发送的多路复用，然后将其切换到GPIO模式并使用`gpiod_direction_output()`在休眠时将其拉低，然后在唤醒时再次将其多路复用到UART发送，并且甚至可能在这个周期中包含`gpiod_get()`/`gpiod_put()`。这一切变得非常复杂。

解决方案是不要认为数据手册中所谓的“GPIO模式”必须通过`<linux/gpio/consumer.h>`接口处理。而是将这视为一种特定的引脚配置设置。查看例如`<linux/pinctrl/pinconf-generic.h>`，你会发现文档中有这样的内容：

  `PIN_CONFIG_OUTPUT:`  
     这将配置引脚为输出，使用参数1表示高电平，参数0表示低电平。

因此，完全可以在通常的引脚控制映射中将引脚推入“GPIO模式”并驱动线路低电平。因此，例如你的UART驱动程序可能如下所示：

```c
#include <linux/pinctrl/consumer.h>

struct pinctrl          *pinctrl;
struct pinctrl_state    *pins_default;
struct pinctrl_state    *pins_sleep;

pins_default = pinctrl_lookup_state(uap->pinctrl, PINCTRL_STATE_DEFAULT);
pins_sleep = pinctrl_lookup_state(uap->pinctrl, PINCTRL_STATE_SLEEP);

/* 正常模式 */
retval = pinctrl_select_state(pinctrl, pins_default);

/* 休眠模式 */
retval = pinctrl_select_state(pinctrl, pins_sleep);
```

而你的机器配置可能如下所示：

```c
static unsigned long uart_default_mode[] = {
    PIN_CONF_PACKED(PIN_CONFIG_DRIVE_PUSH_PULL, 0),
};

static unsigned long uart_sleep_mode[] = {
    PIN_CONF_PACKED(PIN_CONFIG_OUTPUT, 0),
};

static struct pinctrl_map pinmap[] __initdata = {
    PIN_MAP_MUX_GROUP("uart", PINCTRL_STATE_DEFAULT, "pinctrl-foo",
                      "u0_group", "u0"),
    PIN_MAP_CONFIGS_PIN("uart", PINCTRL_STATE_DEFAULT, "pinctrl-foo",
                        "UART_TX_PIN", uart_default_mode),
    PIN_MAP_MUX_GROUP("uart", PINCTRL_STATE_SLEEP, "pinctrl-foo",
                      "u0_group", "gpio-mode"),
    PIN_MAP_CONFIGS_PIN("uart", PINCTRL_STATE_SLEEP, "pinctrl-foo",
                        "UART_TX_PIN", uart_sleep_mode),
};

foo_init(void)
{
    pinctrl_register_mappings(pinmap, ARRAY_SIZE(pinmap));
}
```

这里我们想要控制的引脚位于“u0_group”中，有一些名为“u0”的功能可以在这些引脚组上启用，然后一切就像平常的UART业务一样。但也有一个名为“gpio-mode”的功能可以映射到相同的引脚上，以将它们移至GPIO模式。

这样就可以达到所需的效果，而无需与GPIO子系统进行任何不必要的交互。这只是设备进入休眠时使用的电气配置，它可能意味着引脚被设置为数据手册中称为“GPIO模式”的状态，但这不是重点：它仍然是由那个UART设备用来控制那些与该UART驱动程序相关的引脚，将它们置于由UART所需的模式。Linux内核意义上的GPIO只是一条1位线，是一个不同的应用场景。

如何通过寄存器设置来实现推挽和输出低配置以及将“u0”或“gpio-mode”组多路复用到这些引脚上是驱动程序需要解决的问题。
一些数据表可能会更有帮助，将“GPIO模式”称为“低功耗模式”，而不是与GPIO相关的任何内容。从电气角度讲，这通常意味着相同的事情，但在后一种情况下，软件工程师通常会迅速识别出这是某种特定的多路复用或配置，而非与GPIO API相关的内容。
板卡/机器配置
===========================

板卡和机器定义了如何组装一个完整的运行系统，包括GPIO和设备是如何进行多路复用、调节器是如何约束的以及时钟树的结构。当然，引脚多路复用设置也是其中的一部分。
一个机器上的引脚控制器配置看起来很像一个简单的调节器配置，对于上面的例子数组，我们想要在第二个功能映射上启用I2C和SPI：

.. code-block:: c

	#include <linux/pinctrl/machine.h>

	static const struct pinctrl_map mapping[] __initconst = {
		{
			.dev_name = "foo-spi.0",
			.name = PINCTRL_STATE_DEFAULT,
			.type = PIN_MAP_TYPE_MUX_GROUP,
			.ctrl_dev_name = "pinctrl-foo",
			.data.mux.function = "spi0",
		},
		{
			.dev_name = "foo-i2c.0",
			.name = PINCTRL_STATE_DEFAULT,
			.type = PIN_MAP_TYPE_MUX_GROUP,
			.ctrl_dev_name = "pinctrl-foo",
			.data.mux.function = "i2c0",
		},
		{
			.dev_name = "foo-mmc.0",
			.name = PINCTRL_STATE_DEFAULT,
			.type = PIN_MAP_TYPE_MUX_GROUP,
			.ctrl_dev_name = "pinctrl-foo",
			.data.mux.function = "mmc0",
		},
	};

这里的`dev_name`匹配到可以用来查找设备结构的独特设备名称（就像时钟设备或调节器一样）。函数名称必须匹配由处理这个引脚范围的引脚多路复用驱动程序提供的函数。
如你所见，我们可能在系统上有多个引脚控制器，因此我们需要指定其中哪一个包含我们希望映射的函数。
你可以通过以下方式简单地将这个引脚多路复用映射注册到引脚多路复用子系统：

.. code-block:: c

       ret = pinctrl_register_mappings(mapping, ARRAY_SIZE(mapping));

由于上述构造相当常见，有一个辅助宏使得它更加紧凑，假设你想使用`pinctrl-foo`和位置0来进行映射，例如：

.. code-block:: c

	static struct pinctrl_map mapping[] __initdata = {
		PIN_MAP_MUX_GROUP("foo-i2c.0", PINCTRL_STATE_DEFAULT,
				  "pinctrl-foo", NULL, "i2c0"),
	};

映射表中也可能包含引脚配置条目。通常每个引脚/组都有若干个影响它的配置条目，所以映射表中的配置引用了一个配置参数和值的数组。下面是一个使用方便宏的例子：

.. code-block:: c

	static unsigned long i2c_grp_configs[] = {
		FOO_PIN_DRIVEN,
		FOO_PIN_PULLUP,
	};

	static unsigned long i2c_pin_configs[] = {
		FOO_OPEN_COLLECTOR,
		FOO_SLEW_RATE_SLOW,
	};

	static struct pinctrl_map mapping[] __initdata = {
		PIN_MAP_MUX_GROUP("foo-i2c.0", PINCTRL_STATE_DEFAULT,
				  "pinctrl-foo", "i2c0", "i2c0"),
		PIN_MAP_CONFIGS_GROUP("foo-i2c.0", PINCTRL_STATE_DEFAULT,
				      "pinctrl-foo", "i2c0", i2c_grp_configs),
		PIN_MAP_CONFIGS_PIN("foo-i2c.0", PINCTRL_STATE_DEFAULT,
				    "pinctrl-foo", "i2c0scl", i2c_pin_configs),
		PIN_MAP_CONFIGS_PIN("foo-i2c.0", PINCTRL_STATE_DEFAULT,
				    "pinctrl-foo", "i2c0sda", i2c_pin_configs),
	};

最后，有些设备期望映射表包含某些具体命名的状态。当运行在不需要任何引脚控制器配置的硬件上时，映射表仍然必须包含那些命名状态，以明确表示这些状态被提供并且预期为空。表项宏`PIN_MAP_DUMMY_STATE()`用于定义一个命名状态而不导致任何引脚控制器被编程：

.. code-block:: c

	static struct pinctrl_map mapping[] __initdata = {
		PIN_MAP_DUMMY_STATE("foo-i2c.0", PINCTRL_STATE_DEFAULT),
	};


复杂映射
================

由于一个函数可以映射到不同的引脚组，可以指定一个可选的`.group`，如下所示：

.. code-block:: c

	..
{
		.dev_name = "foo-spi.0",
		.name = "spi0-pos-A",
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "spi0",
		.group = "spi0_0_grp",
	},
	{
		.dev_name = "foo-spi.0",
		.name = "spi0-pos-B",
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "spi0",
		.group = "spi0_1_grp",
	},
	..

此示例映射用于在运行时切换SPI0的两个位置，如下面“运行时引脚多路复用”标题下所述。
此外，一个命名状态可能会影响多个引脚组的多路复用，例如，在上面的mmc0示例中，您可以增加扩展mmc0总线从2到4再到8个引脚。如果我们想使用所有三个组总共2+2+4=8个引脚（对于8位MMC总线而言），我们定义映射如下：

.. code-block:: c

	..
{
		.dev_name = "foo-mmc.0",
		.name = "2bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_1_grp",
	},
	{
		.dev_name = "foo-mmc.0",
		.name = "4bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_1_grp",
	},
	{
		.dev_name = "foo-mmc.0",
		.name = "4bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_2_grp",
	},
	{
		.dev_name = "foo-mmc.0",
		.name = "8bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_1_grp",
	},
	{
		.dev_name = "foo-mmc.0",
		.name = "8bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_2_grp",
	},
	{
		.dev_name = "foo-mmc.0",
		.name = "8bit"
		.type = PIN_MAP_TYPE_MUX_GROUP,
		.ctrl_dev_name = "pinctrl-foo",
		.function = "mmc0",
		.group = "mmc0_3_grp",
	},
	..

从设备中获取此映射并使用类似这样的代码（参见下一段）：

.. code-block:: c

	p = devm_pinctrl_get(dev);
	s = pinctrl_lookup_state(p, "8bit");
	ret = pinctrl_select_state(p, s);

或者更简单地说：

.. code-block:: c

	p = devm_pinctrl_get_select(dev, "8bit");

结果是一次激活映射中的最后三条记录。由于它们具有相同的名称、引脚控制器设备、函数和设备，并且允许多个组与单个设备匹配，因此它们都会被选择，引脚多路复用核心会同时使它们全部启用和禁用。
### 驱动程序中的引脚控制请求
=================================

当设备驱动程序正要探测设备时，设备核心将自动尝试在这些设备上发出`pinctrl_get_select_default()`。这样，驱动程序编写者无需添加任何类似下面的样板代码。但是，在进行精细的状态选择并且不使用“默认”状态时，您可能需要在设备驱动程序中处理一些引脚控制句柄和状态。

因此，如果您只是想将某个设备的引脚置于默认状态并完成操作，则除了提供正确的映射表之外，您无需做其他任何事情。设备核心将负责其余的工作。

通常不建议让单个驱动程序获取并启用引脚控制。如果可能的话，请在平台代码或其他可以访问所有受影响的`struct device *`指针的地方处理引脚控制。在某些情况下，当驱动程序需要在运行时在不同的复用映射之间切换时，这是不可能的。

一个典型的例子是，如果驱动程序需要在正常运行和进入睡眠模式之间切换引脚偏置，从`PINCTRL_STATE_DEFAULT`状态切换到`PINCTRL_STATE_SLEEP`状态，以在睡眠模式下重新偏置或甚至重新复用引脚来节省电流。

驱动程序可以请求激活某种控制状态，通常是默认状态，如下所示：

```c
#include <linux/pinctrl/consumer.h>

struct foo_state {
    struct pinctrl *p;
    struct pinctrl_state *s;
    ..
};

foo_probe()
{
    /* 分配一个名为 "foo" 的状态持有者等 */
    struct foo_state *foo = ...;

    foo->p = devm_pinctrl_get(&device);
    if (IS_ERR(foo->p)) {
        /* FIXME: 在这里清理 "foo" */
        return PTR_ERR(foo->p);
    }

    foo->s = pinctrl_lookup_state(foo->p, PINCTRL_STATE_DEFAULT);
    if (IS_ERR(foo->s)) {
        /* FIXME: 在这里清理 "foo" */
        return PTR_ERR(foo->s);
    }

    ret = pinctrl_select_state(foo->p, foo->s);
    if (ret < 0) {
        /* FIXME: 在这里清理 "foo" */
        return ret;
    }
}
```

此获取/查找/选择/释放序列也可以由总线驱动程序处理，如果您不想让每个驱动程序都处理它，并且您知道您的总线上的布局。

引脚控制API的语义如下：

- `pinctrl_get()` 在进程上下文中调用，以获取给定客户端设备的所有引脚控制信息的句柄。它将从内核内存分配结构来保存引脚复用状态。所有的映射表解析或其他类似的缓慢操作都在这个API内部执行。
- `devm_pinctrl_get()` 是`pinctrl_get()`的一个变体，它会在关联的设备被移除时自动调用`pinctrl_put()`。推荐使用此函数而非普通的`pinctrl_get()`。
- `pinctrl_lookup_state()` 在进程上下文中调用，以获取客户端设备特定状态的句柄。此操作也可能很慢。
- `pinctrl_select_state()` 根据映射表中给定的状态定义对引脚控制器硬件进行编程。理论上，这是一个快速路径操作，因为它只涉及将一些寄存器设置快速写入到硬件中。但是，请注意某些引脚控制器的寄存器可能位于较慢或基于IRQ的总线上，因此客户端设备不应假设它们可以从非阻塞上下文中调用 `pinctrl_select_state()`。
- `pinctrl_put()` 释放与引脚控制器句柄相关联的所有信息。
- `devm_pinctrl_put()` 是 `pinctrl_put()` 的一个变体，可用于显式销毁由 `devm_pinctrl_get()` 返回的引脚控制器对象。然而，由于即使不调用它也会自动清理，因此使用此函数的情况很少见。
`pinctrl_get()` 必须与普通的 `pinctrl_put()` 配对使用。
`pinctrl_get()` 不得与 `devm_pinctrl_put()` 配对使用。
`devm_pinctrl_get()` 可选择性地与 `devm_pinctrl_put()` 配对使用。
`devm_pinctrl_get()` 不得与普通的 `pinctrl_put()` 配对使用。
通常，引脚控制核心处理获取/释放配对，并调用设备驱动程序的簿记操作，如检查可用功能及其关联引脚，而 `pinctrl_select_state()` 将传递给引脚控制器驱动程序，该驱动程序通过快速写入一些寄存器来负责激活和/或停用复用设置。
当你发出 `devm_pinctrl_get()` 调用时，会为你的设备分配引脚，在这之后，你应该能够在debugfs列出的所有引脚中看到这些信息。
注：如果找不到请求的引脚控制句柄，例如如果引脚控制驱动尚未注册，则pinctrl系统将返回“-EPROBE_DEFER”。因此，请确保您的驱动程序中的错误处理路径能够优雅地清理并准备好在启动过程稍后重试探测。

需要同时使用引脚控制和GPIO的驱动
==========================================

再次强调，不建议让驱动自行查找和选择引脚控制状态，但有时这不可避免。
假设您的驱动以如下方式获取其资源：

```c
#include <linux/pinctrl/consumer.h>
#include <linux/gpio/consumer.h>

struct pinctrl *pinctrl;
struct gpio_desc *gpio;

pinctrl = devm_pinctrl_get_select_default(&dev);
gpio = devm_gpiod_get(&dev, "foo");
```

这里我们首先请求一个特定的引脚状态，然后请求使用GPIO "foo"。如果您正交地使用这些子系统，您应该总是先获取到引脚控制句柄，并选择所需的引脚控制状态，然后再请求GPIO。这是一个语义约定，以避免可能会导致电气问题的情况，您肯定希望在GPIO子系统开始处理引脚之前先进行复用和偏置。

上述操作可以隐藏起来：使用设备核心时，引脚控制核心可能在设备探测之前就为引脚设置配置和复用，但仍与GPIO子系统正交。
但是也有情况适合GPIO子系统直接与引脚控制子系统通信，使用后者作为后端。这时GPIO驱动可能调用上文`引脚控制与GPIO子系统的交互`_部分中描述的函数。这仅涉及每个引脚的复用，并且将完全隐藏在gpiod_*()函数命名空间之后。在这种情况下，驱动不需要与引脚控制子系统交互。
如果引脚控制驱动和GPIO驱动处理相同的引脚，并且使用案例涉及复用，除非硬件设计使得GPIO控制器可以通过硬件覆盖引脚控制器的复用状态而无需与引脚控制系统交互，否则您必须像这样实现引脚控制器作为GPIO驱动的后端。

系统引脚控制抢占
==========================

当引脚控制器注册时，引脚控制映射条目可以被核心抢占。这意味着核心会在引脚控制设备注册后立即尝试调用`pinctrl_get()`、`pinctrl_lookup_state()` 和 `pinctrl_select_state()`。

这种情况发生在映射表条目中的客户端设备名称等于引脚控制器设备名称，并且状态名称为`PINCTRL_STATE_DEFAULT`的情况下：

```c
{
	.dev_name = "pinctrl-foo",
	.name = PINCTRL_STATE_DEFAULT,
	.type = PIN_MAP_TYPE_MUX_GROUP,
	.ctrl_dev_name = "pinctrl-foo",
	.function = "power_func",
},
```

由于通常会请求核心抢占主引脚控制器上的几个始终适用的复用设置，因此提供了一个方便的宏用于此目的：

```c
PIN_MAP_MUX_GROUP_HOG_DEFAULT("pinctrl-foo", NULL /* group */,
				       "power_func")
```

这会产生与上述构造相同的结果。

运行时引脚复用
=================

可以在运行时将某个功能复用进或复用出，例如将SPI端口从一组引脚移动到另一组引脚。例如，在上面的例子中，对于spi0，我们可以为同一功能暴露两组不同的引脚，但映射中的名称不同，如上文“高级映射”所述。因此，对于SPI设备，我们有两个名为"pos-A"和"pos-B"的状态。

以下代码段首先为两个组初始化状态对象（在foo_probe()中），然后将功能复用到由组A定义的引脚，最后复用到由组B定义的引脚：

```c
#include <linux/pinctrl/consumer.h>

struct pinctrl *p;
struct pinctrl_state *s1, *s2;

void foo_probe()
{
	/* 设置 */
	p = devm_pinctrl_get(&device);
	if (IS_ERR(p))
		..
```
```c
// 查找名为"pos-A"的状态
s1 = pinctrl_lookup_state(p, "pos-A");
if (IS_ERR(s1)) {
    // 处理错误...
}

// 查找名为"pos-B"的状态
s2 = pinctrl_lookup_state(p, "pos-B");
if (IS_ERR(s2)) {
    // 处理错误...
}
}

void foo_switch(void) {
    // 在位置A上启用
    ret = pinctrl_select_state(p, s1);
    if (ret < 0) {
        // 处理错误...
    }

    // 在位置B上启用
    ret = pinctrl_select_state(p, s2);
    if (ret < 0) {
        // 处理错误...
    }
}

// 上述操作必须在进程上下文中完成。当状态被激活时，将保留相应的引脚，
// 因此，在运行中的系统上，一个特定的引脚可以在不同时间被不同的功能使用。

// 调试文件系统 (Debugfs) 文件
// ==============================

// 这些文件创建在 /sys/kernel/debug/pinctrl 目录下：

// - pinctrl-devices：打印每个引脚控制器设备及其支持的列，这些列表示对 pinmux 和 pinconf 的支持

// - pinctrl-handles：打印每个配置的引脚控制器句柄及其对应的 pinmux 映射

// - pinctrl-maps：打印所有 pinctrl 映射

// 对于每个引脚控制器设备，在 /sys/kernel/debug/pinctrl 目录内创建一个子目录，其中包含以下文件：

// - pins：为注册在引脚控制器上的每个引脚打印一行。pinctrl 驱动程序可能会添加额外的信息，如寄存器内容

// - gpio-ranges：打印映射 gpio 线到控制器上的引脚的范围

// - pingroups：打印所有注册在引脚控制器上的引脚组

// - pinconf-pins：打印每个引脚的引脚配置设置

// - pinconf-groups：按引脚组打印引脚配置设置

// - pinmux-functions：打印每个引脚功能及其对应的引脚组

// - pinmux-pins：遍历所有引脚并打印 mux 所有者、gpio 所有者以及该引脚是否是独占模式

// - pinmux-select：写入此文件以激活一组引脚的功能：

//   示例代码：
//   echo "<group-name function-name>" > pinmux-select
```

这段代码和文档描述了如何在 Linux 内核中管理引脚控制器（pinctrl）的上下文切换，并提供了一些调试文件系统的详细信息。
