### GPIO 驱动接口

=====================

本文档旨在为GPIO芯片驱动程序的编写者提供指导。
每个GPIO控制器驱动程序都需要包含以下头文件，该文件定义了用于定义GPIO驱动程序的结构体：

```c
#include <linux/gpio/driver.h>
```

### GPIO 的内部表示

一个GPIO芯片可以处理一条或多条GPIO线路。要被视为GPIO芯片，这些线路必须符合通用输入/输出（General Purpose Input/Output）的定义。如果线路不是通用目的，则不应视为GPIO，也不应由GPIO芯片处理。使用情况是指示性的：系统中的某些线路可能被称为GPIO，但服务于非常特定的目的，因此不符合通用I/O的标准。另一方面，LED驱动器线路可能被用作GPIO，并且仍然应该由GPIO芯片驱动程序处理。
在GPIO驱动程序内部，单个GPIO线路通过它们的硬件编号来标识，有时也称为“偏移量”，这是一个从0到n-1的唯一数字，其中n是芯片管理的GPIO数量。
硬件GPIO编号应该是对硬件直观的某个值，例如，如果一个系统使用内存映射的一组I/O寄存器，其中32条GPIO线路由32位寄存器中的一位表示，那么使用硬件偏移量0..31来表示这些线路是有意义的，对应于寄存器中的比特位0..31。
这个数字完全是内部使用的：特定GPIO线路的硬件编号永远不会在驱动程序外部可见。
除了这个内部编号之外，每条GPIO线路还需要在整数GPIO命名空间中有一个全局编号，以便与旧版GPIO接口一起使用。因此，每个芯片必须有一个“基”编号（可以自动分配），对于每条GPIO线路，其全局编号将是(基+硬件编号)。虽然整数表示被认为已经过时，但它仍然有很多用户，因此需要维护。
例如，一个平台可以使用全局编号32-159来表示GPIO，控制器定义了128个GPIO，基地址为32；而另一个平台使用全局编号0..63，由一组GPIO控制器处理，64-79由另一种类型的GPIO控制器处理，在特定的主板上使用80-95处理FPGA。旧版编号不必连续；这两个平台也可以使用2000-2063来标识I2C GPIO扩展器银行中的GPIO线路。
### 控制器驱动程序：`gpio_chip`
=============================

在gpiolib框架中，每个GPIO控制器都被封装为一个“struct gpio_chip”（参见<linux/gpio/driver.h>以获取其完整定义），包含了对该类型控制器通用的成员，这些成员应由驱动代码分配：

- 设置GPIO线路方向的方法
- 访问GPIO线路值的方法
- 为给定GPIO线路设置电气配置的方法
- 返回与给定GPIO线路关联的IRQ编号的方法
- 标记表明其方法是否允许睡眠
- 可选的线路名称数组以识别线路
- 可选的调试文件系统转储方法（显示额外的状态信息）
- 可选的基础编号（如果省略将自动分配）
- 使用平台数据进行诊断和GPIO芯片映射的可选标签

实现`gpio_chip`的代码应该支持控制器的多个实例，最好使用驱动模型。这段代码将配置每个`gpio_chip`并调用`gpiochip_add_data()`或`devm_gpiochip_add_data()`。移除GPIO控制器应该很少发生；当不可避免时，请使用`gpiochip_remove()`。
通常情况下，`gpio_chip`是实例特定结构的一部分，其中包括GPIO接口未暴露的状态，如寻址、电源管理和更多内容。
像音频编解码器这样的芯片会有复杂的非GPIO状态。
任何debugfs转储方法通常应忽略那些未被请求的行。它们可以使用`gpiochip_is_requested()`函数，该函数在GPIO线被请求时返回与之关联的标签或NULL。

实时考虑：如果GPIO驱动程序预计会在实时内核中的原子上下文中调用GPIO API（例如，在硬中断处理程序和类似的上下文中），那么它在其`gpio_chip`实现中（`.get/.set`和方向控制回调）不应使用`spinlock_t`或任何可睡眠API（如PM运行时）。通常情况下，这不应该需要。

### GPIO电气配置

通过使用`.set_config()`回调，可以为GPIO线配置多种电气工作模式。目前此API支持设置：

- 防抖动
- 单端模式（开漏/开源）
- 上拉和下拉电阻的启用

这些设置如下所述。

`.set_config()`回调使用了与通用引脚控制驱动相同的枚举器和配置语义。这不是巧合：可以将`.set_config()`赋值给函数`gpiochip_generic_config()`，这样会导致调用`pinctrl_gpio_set_config()`，最终进入GPIO控制器背后的引脚控制后端，通常是更接近实际引脚的位置。这样，引脚控制器就可以管理下面列出的GPIO配置。

如果使用了引脚控制后端，则GPIO控制器或硬件描述需要提供“GPIO范围”，将GPIO线偏移量映射到引脚控制器上的引脚编号，以便它们能正确地相互参照。

#### 支持防抖动的GPIO线

防抖动是为引脚设置的一种配置，表明该引脚连接到了机械开关或按钮等可能产生弹跳的设备。弹跳意味着由于机械原因，线路会快速地在高电平和低电平之间短暂切换。这可能导致线路值不稳定或中断频繁触发，除非线路进行了防抖动处理。

实际上，防抖动涉及在线路发生事件时设置一个定时器，稍等片刻后再重新采样线路，以确定其是否仍保持相同的值（高或低）。这也可以通过一个巧妙的状态机来重复，等待线路稳定下来。无论是哪种情况，它都会设置一定的毫秒数用于防抖动，或者只是简单的“开启/关闭”模式，如果该时间不可配置的话。

#### 支持开漏/开源的GPIO线

开漏（CMOS）或开集（TTL）意味着线路不会主动被驱动至高电平：相反，你提供漏极/集电极作为输出，因此当晶体管未打开时，它将对外部电源呈现高阻抗（三态）。

**CMOS配置**          **TTL配置**

```
     ||--- out              +--- out
 in ----||                   |/
     ||--+         in ----|
         |                |\
        GND                 GND
```

这种配置通常用于实现以下两种目的之一：

- 电平转换：使输出达到高于硅片所在逻辑电平的电平。
- 在I/O线上实现逆向线或操作，例如GPIO线，使得线路上的任一驱动级都可以将其驱动至低电平，即使线路上的其他输出同时将其驱动至高电平。一个特殊情况是在I2C总线上的SCL和SDA线，该总线定义上就是一种线或总线。

这两种用途都需要线路配备上拉电阻。这个电阻会使线路倾向于高电平，除非线路上的任一晶体管主动将其拉低。
线上的电平将上升到上拉电阻的VDD电平，这可能高于晶体管支持的电平，从而实现向更高VDD电平的电平转换。
集成电子设备通常具有CMOS“图腾柱”形式的输出驱动级，包括一个N-MOS和一个P-MOS晶体管，其中一个将线路驱动为高电平，另一个将其驱动为低电平。这被称为推挽输出。“图腾柱”的结构如下：

                     VDD
                      |
            OD    ||--+
         +--/ ---o||     P-MOS-FET
         |        ||--+
    IN --+            +----- out
         |        ||--+
         +--/ ----||     N-MOS-FET
            OS    ||--+
                      |
                     GND

所需的输出信号（例如直接来自某个GPIO输出寄存器）到达IN。标记为“OD”和“OS”的开关通常是闭合的，形成推挽电路。
考虑标记为“OD”和“OS”的小型“开关”，它们在输入分叉后使能或禁用P-MOS或N-MOS晶体管。如你所见，如果这些开关打开，则任一晶体管都将完全失效。此时图腾柱被分成两半，并呈现高阻抗状态，而不是主动地将线路驱动为高电平或低电平。这通常是软件控制的开漏/开源工作方式。
一些GPIO硬件以开漏/开源配置出现。有些是硬连线的线路，无论怎样都只能支持开漏或开源：那里只有一个晶体管。有些则是软件可配置的：通过切换寄存器中的位，可以将输出配置为开漏或开源，实际上是在上面的示意图中打开标记为“OD”和“OS”的开关。
通过禁用P-MOS晶体管，输出可以在GND和高阻抗（开漏）之间驱动；通过禁用N-MOS晶体管，输出可以在VDD和高阻抗（开源）之间驱动。在第一种情况下，需要在线路出口处使用一个上拉电阻来完成电路；在第二种情况下，则需要一个下拉电阻。
支持开漏或开源或两者兼有的硬件可以在gpio_chip中实现一个特殊的回调.set_config()，该回调接收一个通用的pinconf打包值，指示是否将线路配置为开漏、开源或推挽。这将响应于在机器文件中设置的GPIO_OPEN_DRAIN或GPIO_OPEN_SOURCE标志，或者从其他硬件描述中获取。
如果硬件无法配置这种状态，即GPIO硬件不支持硬件级别的开漏/开源，GPIO库将使用一种技巧：当线路被设置为输出时，如果线路被标记为开漏，并且IN输出值为低，则会像往常一样被驱动为低电平。但如果IN输出值设置为高，则不会被驱动为高电平，而是切换为输入模式，因为输入模式等同于高阻抗，从而实现了某种“开漏模拟”：从电气行为上看将是相同的，除了在切换线路模式时可能出现的硬件故障。
对于开源配置，采用相同的原则，只是不主动驱动线路为低电平，而是设置为输入模式。

带有上拉/下拉电阻支持的GPIO线路
-----------------------------------

GPIO线路可以通过.set_config()回调支持上拉/下拉。这意味着GPIO线路的输出端有可用的上拉或下拉电阻，并且这个电阻是软件可控的。
在离散设计中，上拉或下拉电阻仅仅是焊接在电路板上。这不是我们在软件中处理或建模的内容。对于这些线路，你最关心的是它们很可能被配置为开漏或开源（参见上述部分）。
`.set_config()` 回调只能开启或关闭上拉或下拉功能，并且不会对所使用的电阻值有任何语义上的理解。它只会切换寄存器中的某个位以启用或禁用上拉或下拉。
如果GPIO线路支持为上拉或下拉电阻设置不同的电阻值，那么 `.set_config()` 回调将不够用。对于这些复杂的情况，需要实现一个组合的GPIO芯片和引脚控制器，因为引脚控制器的引脚配置接口支持更灵活的电气特性控制，并能处理不同的上拉或下拉电阻值。

提供中断的GPIO驱动
=====================

通常情况下，GPIO驱动（即GPIO芯片）也会提供中断，大多数情况下是从上级中断控制器级联下来的，在一些特殊情况下，GPIO逻辑与SoC的主要中断控制器融为一体。
GPIO模块中的中断部分是使用 `irq_chip` 实现的，使用头文件 `<linux/irq.h>`。因此这种组合驱动同时利用了两个子系统：GPIO和中断。
任何中断消费者都可以从任何一个 `irqchip` 请求中断，即使该 `irqchip` 是一个组合的GPIO+中断驱动。基本前提是 `gpio_chip` 和 `irq_chip` 是相互独立的，并且各自独立提供服务。
`gpiod_to_irq()` 只是一个用于确定特定GPIO线路的中断的便利函数，不应该依赖于在使用中断之前已经调用了此函数。
始终在GPIO和 `irq_chip` API的相关回调中准备好硬件并使其处于可工作状态。不要依赖于 `gpiod_to_irq()` 已经被首先调用。
我们可以将GPIO中断芯片分为两大类：

- 级联中断芯片：这意味着GPIO芯片有一个公共的中断输出线，当该芯片上的任意启用的GPIO线路触发时，这个中断输出线会被激活。中断输出线然后会被路由到上一级的父中断控制器，最简单的情况下就是系统的主中断控制器。这通过一个 `irqchip` 来模拟，该 `irqchip` 会检查GPIO控制器内部的位来确定哪个线路触发了中断。驱动程序的 `irqchip` 部分需要检查寄存器来确定这一点，并且很可能还需要通过清除某个位（有时是隐式的，仅通过读取状态寄存器）来确认正在处理中断，此外它经常还需要设置配置，比如边沿敏感性（上升沿或下降沿，或者高电平/低电平中断等）。
- 分层中断芯片：这意味着每个GPIO线路都有一个专门的中断线连接至上一级的父中断控制器。无需询问GPIO硬件来确定哪个线路触发了中断，但是可能仍然需要确认中断并设置配置，如边沿敏感性。
实时考虑因素：一个符合实时要求的GPIO驱动在其 `irqchip` 实现中不应使用 `spinlock_t` 或任何可睡眠的API（例如PM运行时）。
### 翻译

#### Spinlock_t 应替换为 raw_spinlock_t。
- `spinlock_t` 应该被 `raw_spinlock_t` 替换。[1]
- 如果必须使用可睡眠 API，则可以从 `.irq_bus_lock()` 和 `.irq_bus_unlock()` 回调中进行，因为这些是中断控制器上唯一的慢路径回调。如果需要，创建这些回调。[2]

### 级联 GPIO 中断控制器
----------------------

级联 GPIO 中断控制器通常属于以下三类：

- **链式级联 GPIO 中断控制器**：这类通常是嵌入在系统芯片（SoC）中的类型。这意味着对于 GPIO 的快速中断处理程序会在父中断处理程序的链式调用中被调用，最常见的父中断处理程序是系统中断控制器。这意味着 GPIO 中断控制器的处理程序将立即由父中断控制器调用，同时禁用中断。GPIO 中断控制器最终将在其中断处理程序中调用如下序列：
  
  ```c
  static irqreturn_t foo_gpio_irq(int irq, void *data)
      chained_irq_enter(...);
      generic_handle_irq(...);
      chained_irq_exit(...);
  ```

  链式 GPIO 中断控制器通常不能在 `struct gpio_chip` 中设置 `.can_sleep` 标志，因为所有操作都是直接在回调中完成的：无法使用像 I2C 这样的慢速总线通信。
  实时考虑：请注意，链式中断处理器在实时内核（-RT）中不会被强制转换为线程模式。因此，在链式中断处理器中不能使用 `spinlock_t` 或任何可睡眠 API（如 PM 运行时）。
  如果需要（并且无法将其转换为嵌套线程化的 GPIO 中断控制器，请参见下文），链式中断处理器可以转换为通用中断处理器，这样它就会在实时内核中成为线程化中断处理器，在非实时内核中成为硬中断处理器（例如，参见 [3]）。
  `generic_handle_irq()` 预期在禁用中断的情况下被调用，因此如果它从一个被强制转换为线程的中断处理程序中调用，中断核心会发出警告。可以使用“伪”原始锁来绕过这个问题：
  
  ```c
  raw_spinlock_t wa_lock;
  static irqreturn_t omap_gpio_irq_handler(int irq, void *gpiobank)
      unsigned long wa_lock_flags;
      raw_spin_lock_irqsave(&bank->wa_lock, wa_lock_flags);
      generic_handle_irq(irq_find_mapping(bank->chip.irq.domain, bit));
      raw_spin_unlock_irqrestore(&bank->wa_lock, wa_lock_flags);
  ```

- **通用链式 GPIO 中断控制器**：这些与“链式 GPIO 中断控制器”相同，但不使用链式中断处理器。相反，GPIO 中断通过使用 `request_irq()` 配置的通用中断处理器进行分发。
  GPIO 中断控制器最终将在其中断处理程序中调用如下序列：
  
  ```c
  static irqreturn_t gpio_rcar_irq_handler(int irq, void *dev_id)
      for each detected GPIO IRQ
          generic_handle_irq(...);
  ```

  实时考虑：这种类型的处理器在实时内核（-RT）中会被强制转换为线程模式，结果是中断核心会警告 `generic_handle_irq()` 在中断启用的情况下被调用。可以应用与“链式 GPIO 中断控制器”相同的解决方法。

- **嵌套线程化的 GPIO 中断控制器**：这些是片外 GPIO 扩展器和任何位于像 I2C 或 SPI 这样可睡眠总线另一端的 GPIO 中断控制器。
  当然，那些需要慢速总线通信来读取中断状态等信息的驱动程序，这种通信可能会导致其他中断发生，不能在禁用中断的快速中断处理器中处理。相反，它们需要启动一个线程，然后屏蔽父中断线，直到中断被驱动程序处理。此类驱动程序的特点是在其中断处理程序中调用如下内容：
  
  ```c
  static irqreturn_t foo_gpio_irq(int irq, void *data)
      ...
  handle_nested_irq(irq);
  ```

  嵌套线程化 GPIO 中断控制器的特点是它们在 `struct gpio_chip` 中设置 `.can_sleep` 标志为 `true`，表示此芯片在访问 GPIO 时可能会睡眠。
  这种类型的中断控制器本质上是实时容忍的，因为它们已经设置好来处理可睡眠上下文。

### GPIO 中断控制器基础设施助手
----------------------------------------

为了帮助处理 GPIO 中断控制器及其关联的中断域和资源分配回调的设置和管理。这可以通过选择 Kconfig 符号 `GPIOLIB_IRQCHIP` 来激活。如果还选择了符号 `IRQ_DOMAIN_HIERARCHY`，那么也会提供层级助手。大部分开销代码将由 `gpiolib` 管理，假设您的中断与 GPIO 线索引一对一映射：

```csv
GPIO line offset, Hardware IRQ
0,0
1,1
2,2
...,..
```
这段文档主要描述了如何在 Linux 内核中使用 `gpio_irq_chip` 结构来处理 GPIO 中断，并且展示了几个具体的代码示例。下面是该文档的中文翻译：

---

### ngpio-1, ngpio-1

如果某些 GPIO 线没有对应的中断请求（IRQ），可以使用掩码 `valid_mask` 和标志 `need_valid_mask` 在 `gpio_irq_chip` 结构体中屏蔽这些线路，以表明它们对于与 IRQ 关联是无效的。

设置帮助函数的首选方式是在添加 `gpio_chip` 前填充 `struct gpio_irq_chip` 结构体内的内容。如果你这样做，额外的 `irq_chip` 将会在设置其余 GPIO 功能的同时由 gpiolib 设置好。以下是一个使用 `gpio_irq_chip` 的级联中断处理器的典型示例。请注意，掩码/取消掩码（或禁用/启用）函数调用了核心 gpiolib 代码：

```c
/* 典型状态容器 */
struct my_gpio {
    struct gpio_chip gc;
};

static void my_gpio_mask_irq(struct irq_data *d)
{
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    /*
     * 执行必要的操作来屏蔽中断，
     * 然后调用核心代码同步状态
    */

    gpiochip_disable_irq(gc, hwirq);
}

static void my_gpio_unmask_irq(struct irq_data *d)
{
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    gpiochip_enable_irq(gc, hwirq);

    /*
     * 执行必要的操作来取消屏蔽中断，
     * 在调用核心代码同步状态之后
    */
}

/*
 * 静态填充 irq_chip。注意它被声明为 const
 * （进一步通过 IRQCHIP_IMMUTABLE 标志表示），并且
 * GPIOCHIP_IRQ_RESOURCE_HELPER 宏向结构体添加了一些额外的
 * 回调函数
*/
static const struct irq_chip my_gpio_irq_chip = {
    .name          = "my_gpio_irq",
    .irq_ack       = my_gpio_ack_irq,
    .irq_mask      = my_gpio_mask_irq,
    .irq_unmask    = my_gpio_unmask_irq,
    .irq_set_type  = my_gpio_set_irq_type,
    .flags         = IRQCHIP_IMMUTABLE,
    /* 提供 gpio 资源回调函数 */
    GPIOCHIP_IRQ_RESOURCE_HELPERS,
};

int irq; /* 来自平台等 */
struct my_gpio *g;
struct gpio_irq_chip *girq;

/* 获取 gpio_irq_chip 的指针 */
girq = &g->gc.irq;
gpio_irq_chip_set_chip(girq, &my_gpio_irq_chip);
girq->parent_handler = ftgpio_gpio_irq_handler;
girq->num_parents = 1;
girq->parents = devm_kcalloc(dev, 1, sizeof(*girq->parents),
                              GFP_KERNEL);
if (!girq->parents)
    return -ENOMEM;
girq->default_type = IRQ_TYPE_NONE;
girq->handler = handle_bad_irq;
girq->parents[0] = irq;

return devm_gpiochip_add_data(dev, &g->gc, g);
```

帮助程序还支持使用线程化中断。在这种情况下，你只需单独请求中断并继续使用即可：

```c
/* 典型状态容器 */
struct my_gpio {
    struct gpio_chip gc;
};

static void my_gpio_mask_irq(struct irq_data *d)
{
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    /*
     * 执行必要的操作来屏蔽中断，
     * 然后调用核心代码同步状态
    */

    gpiochip_disable_irq(gc, hwirq);
}

static void my_gpio_unmask_irq(struct irq_data *d)
{
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    gpiochip_enable_irq(gc, hwirq);

    /*
     * 执行必要的操作来取消屏蔽中断，
     * 在调用核心代码同步状态之后
    */
}

/*
 * 静态填充 irq_chip。注意它被声明为 const
 * （进一步通过 IRQCHIP_IMMUTABLE 标志表示），并且
 * GPIOCHIP_IRQ_RESOURCE_HELPER 宏向结构体添加了一些额外的
 * 回调函数
*/
static const struct irq_chip my_gpio_irq_chip = {
    .name          = "my_gpio_irq",
    .irq_ack       = my_gpio_ack_irq,
    .irq_mask      = my_gpio_mask_irq,
    .irq_unmask    = my_gpio_unmask_irq,
    .irq_set_type  = my_gpio_set_irq_type,
    .flags         = IRQCHIP_IMMUTABLE,
    /* 提供 gpio 资源回调函数 */
    GPIOCHIP_IRQ_RESOURCE_HELPERS,
};

int irq; /* 来自平台等 */
struct my_gpio *g;
struct gpio_irq_chip *girq;

ret = devm_request_threaded_irq(dev, irq, NULL, irq_thread_fn,
                                IRQF_ONESHOT, "my-chip", g);
if (ret < 0)
    return ret;

/* 获取 gpio_irq_chip 的指针 */
girq = &g->gc.irq;
gpio_irq_chip_set_chip(girq, &my_gpio_irq_chip);
/* 这将让我们在驱动程序中处理父 IRQ */
girq->parent_handler = NULL;
girq->num_parents = 0;
girq->parents = NULL;
girq->default_type = IRQ_TYPE_NONE;
girq->handler = handle_bad_irq;

return devm_gpiochip_add_data(dev, &g->gc, g);
```

帮助程序也支持使用层次中断控制器。在这种情况下，典型的设置看起来像这样：

```c
/* 具有动态 irqchip 的典型状态容器 */
struct my_gpio {
    struct gpio_chip gc;
    struct fwnode_handle *fwnode;
};

static void my_gpio_mask_irq(struct irq_data *d)
{
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    /*
     * 执行必要的操作来屏蔽中断，
     * 然后调用核心代码同步状态
    */
}
```

---

这个翻译试图保持原意和结构，同时确保中文表述通顺。
The provided C code snippet is related to handling interrupts for a custom GPIO (General Purpose Input/Output) chip within the Linux kernel. Below is a translation of the comments and key parts of the code into Chinese, along with explanations where necessary.

```c
// 禁用 GPIO 芯片上的中断
void my_gpio_mask_irq(struct irq_data *d) {
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    gpiochip_disable_irq(gc, hwirq);
    // 在父设备上屏蔽中断
    irq_mask_mask_parent(d);
}

// 解除屏蔽 GPIO 芯片上的中断
static void my_gpio_unmask_irq(struct irq_data *d) {
    struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
    irq_hw_number_t hwirq = irqd_to_hwirq(d);

    gpiochip_enable_irq(gc, hwirq);

    // 执行必要的操作以解除中断的屏蔽，在调用核心代码同步状态之后
    irq_mask_unmask_parent(d);
}

// 静态初始化 IRQ 芯片。注意它被标记为 const（通过 IRQCHIP_IMMUTABLE 标志进一步指示），并且 GPIOCHIP_IRQ_RESOURCE_HELPER 宏向结构体添加了一些额外的回调。
static const struct irq_chip my_gpio_irq_chip = {
    .name          = "my_gpio_irq",
    .irq_ack       = my_gpio_ack_irq,
    .irq_mask      = my_gpio_mask_irq,
    .irq_unmask    = my_gpio_unmask_irq,
    .irq_set_type  = my_gpio_set_irq_type,
    .flags         = IRQCHIP_IMMUTABLE,
    // 提供 GPIO 资源回调函数
    GPIOCHIP_IRQ_RESOURCE_HELPERS,
};

struct my_gpio *g;
struct gpio_irq_chip *girq;

// 获取 gpio_irq_chip 的指针
girq = &g->gc.irq;
gpio_irq_chip_set_chip(girq, &my_gpio_irq_chip);
girq->default_type = IRQ_TYPE_NONE;
girq->handler = handle_bad_irq;
girq->fwnode = g->fwnode;
girq->parent_domain = parent;
girq->child_to_parent_hwirq = my_gpio_child_to_parent_hwirq;

return devm_gpiochip_add_data(dev, &g->gc, g);

// 如你所见，非常相似，但你不需要提供一个父处理程序来处理 IRQ，而是提供一个父 IRQ 域、一个硬件节点以及一个 .child_to_parent_hwirq() 函数，该函数的目的是从子设备（即此 GPIO 芯片）的硬件 IRQ 查找父设备的硬件 IRQ。

// 如果需要将某些 GPIO 线排除在由这些助手处理的 IRQ 域之外，我们可以在调用 devm_gpiochip_add_data() 或 gpiochip_add_data() 之前设置 gpiochip 的 .irq.need_valid_mask。这会分配一个 .irq.valid_mask，其中设置的位数与芯片中的 GPIO 线数量相同，每个位代表线 0..n-1。驱动程序可以通过清除掩码中的位来排除 GPIO 线。掩码可以在作为 struct gpio_irq_chip 的一部分的 init_valid_mask() 回调中填充。

// 使用这些助手时，请记住以下几点：
// - 确保设置 struct gpio_chip 中所有相关成员，以便 irqchip 可以初始化。例如，.dev 和 .can_sleep 应当正确设置。
// - 通常将 gpio_irq_chip.handler 设置为 handle_bad_irq。然后，如果你的 irqchip 是级联的，在 irqchip .set_type() 回调中根据控制器支持的内容和消费者的要求将处理器设置为 handle_level_irq() 和/或 handle_edge_irq()。

// 中断 IRQ 使用的锁定
// -----------------------
// 由于 GPIO 和 irq_chip 是正交的，我们可能会遇到不同使用场景之间的冲突。例如，用于 IRQ 的 GPIO 线应当是一个输入线，对于输出 GPIO 触发中断是没有意义的。
// 如果子系统内部存在对资源（例如某个 GPIO 线和寄存器）使用的竞争，它需要拒绝某些操作并跟踪 gpiolib 子系统内的使用情况。
// 输入 GPIO 可以用作 IRQ 信号。当这种情况发生时，驱动程序被要求标记 GPIO 正在用作 IRQ：

int gpiochip_lock_as_irq(struct gpio_chip *chip, unsigned int offset)

// 这将阻止非 IRQ 相关的 GPIO API 的使用，直到 GPIO IRQ 锁被释放：

void gpiochip_unlock_as_irq(struct gpio_chip *chip, unsigned int offset)

// 当在 GPIO 驱动程序中实现 irqchip 时，这两个函数通常应在 irqchip 的 .startup() 和 .shutdown() 回调中调用。
```

这段代码展示了如何在 Linux 内核中为自定义 GPIO 芯片处理中断，并且提供了详细的注释说明。
使用gpiolib IRQ芯片助手时，这些回调函数会被自动分配。

禁用和启用IRQ
--------------

在某些（边缘）应用场景中，驱动程序可能会将GPIO线用作IRQ的输入，但偶尔会将该线切换为输出驱动，然后再切换回带有中断的输入。这种情况发生在诸如CEC（消费电子控制）等设备上。
当GPIO被用作IRQ信号时，gpiolib还需要知道IRQ是被启用还是禁用。为了通知gpiolib这一点，IRQ芯片驱动应该调用：

  void gpiochip_disable_irq(struct gpio_chip *chip, unsigned int offset)

这允许驱动程序在IRQ被禁用的情况下驱动GPIO作为输出。当再次启用IRQ时，驱动程序应调用：

  void gpiochip_enable_irq(struct gpio_chip *chip, unsigned int offset)

在GPIO驱动程序内部实现IRQ芯片时，这两个函数通常应在来自IRQ芯片的.irq_disable()和.irq_enable()回调函数中调用。
如果IRQ芯片没有声明IRQCHIP_IMMUTABLE，则这些回调函数会被自动分配。这种行为已被弃用，并且正在从内核中移除。

GPIO IRQ芯片的实时兼容性
-----------------------------

任何IRQ芯片提供商都需要仔细调整以支持实时抢占。希望所有GPIO子系统中的IRQ芯片都考虑到这一点，并进行适当的测试以确保它们已启用实时功能。
因此，请注意文档中关于上述实时性的考虑。
以下是在准备驱动程序以实现实时兼容性时需要遵循的检查清单：

- 确保spinlock_t不是IRQ芯片实现的一部分
- 确保不会在IRQ芯片实现中使用可睡眠API
  如果必须使用可睡眠API，可以在.irq_bus_lock()和.irq_bus_unlock()回调中执行这些操作
- 链接GPIO IRQ芯片：确保不要在链接的IRQ处理器中使用spinlock_t或任何可睡眠API
- 通用链接GPIO IRQ芯片：注意对generic_handle_irq()的调用，并应用相应的解决方法
- 链接GPIO IRQ芯片：如果可能的话，去掉链接的IRQ处理器并使用通用IRQ处理器
- regmap_mmio：可以通过设置.disable_locking并在GPIO驱动程序中处理锁定来禁用regmap中的内部锁定
- 使用合适的内核实时测试案例来测试你的驱动程序，包括电平触发和边沿触发的IRQ

* [1] http://www.spinics.net/lists/linux-omap/msg120425.html
* [2] https://lore.kernel.org/r/1443209283-20781-2-git-send-email-grygorii.strashko@ti.com
* [3] https://lore.kernel.org/r/1443209283-20781-3-git-send-email-grygorii.strashko@ti.com

请求自有的GPIO引脚
==================

有时候，允许GPIO芯片驱动程序通过gpiolib API请求其自己的GPIO描述符是有用的。GPIO驱动程序可以使用以下函数来请求和释放描述符：

  struct gpio_desc *gpiochip_request_own_desc(struct gpio_desc *desc,
                                              u16 hwnum,
                                              const char *label,
                                              enum gpiod_flags flags)

  void gpiochip_free_own_desc(struct gpio_desc *desc)

通过gpiochip_request_own_desc()请求的描述符必须使用gpiochip_free_own_desc()释放。
这些函数必须谨慎使用，因为它们不会影响模块的使用计数。不要使用这些函数来请求不属于调用驱动程序的GPIO描述符。
