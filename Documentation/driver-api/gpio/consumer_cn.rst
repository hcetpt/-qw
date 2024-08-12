GPIO描述符消费者接口
==========================

本文件描述了GPIO框架的消费者接口。
GPIO消费者的指导方针
============================

无法在没有标准GPIO调用的情况下工作的驱动程序应该具有依赖于GPIOLIB或选择GPIOLIB的Kconfig条目。允许驱动程序获取和使用GPIO的函数可通过包含以下文件获得：

	#include <linux/gpio/consumer.h>

当GPIOLIB被禁用时，头文件中为所有函数提供了静态内联存根。当调用这些存根时，它们会发出警告。这些存根用于两种情况：

- 简单的编译覆盖测试（例如COMPILE_TEST）——当前平台是否启用或选择GPIOLIB并不重要，因为我们无论如何都不会执行系统
- 真正可选的GPIOLIB支持——驱动程序在某些编译时配置下对某些系统实际上不使用GPIO，但在其他编译时配置下将使用它。在这种情况下，消费者必须确保不调用这些函数，否则用户可能会遇到可能令人感到不安的控制台警告
结合真正可选的GPIOLIB使用与调用`[devm_]gpiod_get_optional()`是*不好的主意*，这会导致奇怪的错误消息。使用带有可选GPIOLIB的普通获取函数：当您这样做时，应该期望一些开放式的错误处理编码
所有与基于描述符的GPIO接口一起工作的函数都以`gpiod_`为前缀。`gpio_`前缀用于遗留接口。内核中的其他任何函数都不应使用这些前缀。强烈不建议使用遗留函数，新代码应仅使用<linux/gpio/consumer.h>和描述符
获取和释放GPIO
======================

通过基于描述符的接口，GPIO通过一个不透明且不可伪造的句柄来标识，该句柄必须通过调用其中一个gpiod_get()函数来获取。像许多其他内核子系统一样，gpiod_get()需要传入将使用GPIO的设备以及请求的GPIO所要完成的功能：

    struct gpio_desc *gpiod_get(struct device *dev, const char *con_id,
				 enum gpiod_flags flags)

如果一个功能通过组合使用几个GPIO来实现（例如，一个简单的LED设备显示数字），可以指定额外的索引参数：

    struct gpio_desc *gpiod_get_index(struct device *dev,
				       const char *con_id, unsigned int idx,
				       enum gpiod_flags flags)

对于DeviceTree情况下con_id参数的更详细描述，请参阅Documentation/driver-api/gpio/board.rst

flags参数用于可选地指定GPIO的方向和初始值。可取的值包括：

* GPIOD_ASIS或0表示根本不初始化GPIO。稍后必须使用专用函数设置方向
* GPIOD_IN表示将GPIO初始化为输入
* GPIOD_OUT_LOW表示将GPIO初始化为输出，值为0
* GPIOD_OUT_HIGH表示将GPIO初始化为输出，值为1
* GPIOD_OUT_LOW_OPEN_DRAIN与GPIOD_OUT_LOW相同，但还强制线路电学上使用开漏方式
* GPIOD_OUT_HIGH_OPEN_DRAIN 与 GPIOD_OUT_HIGH 相同，但同时也强制线路采用开漏输出方式。
请注意初始值是*逻辑*上的，并且实际的物理线路电平取决于线路是否配置为高电平有效或低电平有效（参见 :ref:`active_low_semantics`）。
最后两个标志用于必须使用开漏输出的情况，例如 I2C：如果线路在映射中尚未配置为开漏输出（参见 board.rst），那么无论如何都会强制使用开漏输出，并会打印一条警告信息，提示需要更新板卡配置以匹配使用情况。
这两个函数要么返回一个有效的 GPIO 描述符，要么返回一个可以通过 IS_ERR() 检查的错误代码（它们永远不会返回 NULL 指针）。-ENOENT 只有在没有任何 GPIO 被分配给设备/功能/索引三元组时才会返回，其他错误代码则用于已分配 GPIO 但在尝试获取时发生错误的情况。这对于区分简单的错误和可选 GPIO 参数不存在的情况非常有用。对于 GPIO 可选的常见模式，可以使用 gpiod_get_optional() 和 gpiod_get_index_optional() 函数。如果没有 GPIO 分配给请求的功能，这些函数将返回 NULL：

```c
struct gpio_desc *gpiod_get_optional(struct device *dev,
                                      const char *con_id,
                                      enum gpiod_flags flags)

struct gpio_desc *gpiod_get_index_optional(struct device *dev,
                                            const char *con_id,
                                            unsigned int index,
                                            enum gpiod_flags flags)
```

需要注意的是，与 gpiolib API 的其余部分不同，gpio_get*_optional() 函数（及其管理变体）在禁用 gpiolib 支持时也会返回 NULL。
这对驱动程序作者来说是有帮助的，因为他们不需要特别处理 -ENOSYS 返回码。然而，系统集成商应该小心确保在需要 gpiolib 的系统上启用它。
对于使用多个 GPIO 的函数，所有这些都可以通过一次调用来获得：

```c
struct gpio_descs *gpiod_get_array(struct device *dev,
                                    const char *con_id,
                                    enum gpiod_flags flags)
```

此函数返回一个包含描述符数组的 struct gpio_descs 结构。它还包含指向 gpiolib 私有结构的指针，如果将其传递回 get/set 数组函数，则可能加快 I/O 处理速度：

```c
struct gpio_descs {
    struct gpio_array *info;
    unsigned int ndescs;
    struct gpio_desc *desc[];
}
```

如果没有 GPIO 分配给请求的功能，以下函数将返回 NULL 而不是 -ENOENT：

```c
struct gpio_descs *gpiod_get_array_optional(struct device *dev,
                                             const char *con_id,
                                             enum gpiod_flags flags)
```

也定义了这些函数的设备管理变体：

```c
struct gpio_desc *devm_gpiod_get(struct device *dev, const char *con_id,
                                 enum gpiod_flags flags)

struct gpio_desc *devm_gpiod_get_index(struct device *dev,
                                       const char *con_id,
                                       unsigned int idx,
                                       enum gpiod_flags flags)

struct gpio_desc *devm_gpiod_get_optional(struct device *dev,
                                          const char *con_id,
                                          enum gpiod_flags flags)

struct gpio_desc *devm_gpiod_get_index_optional(struct device *dev,
                                                const char *con_id,
                                                unsigned int index,
                                                enum gpiod_flags flags)

struct gpio_descs *devm_gpiod_get_array(struct device *dev,
                                        const char *con_id,
                                        enum gpiod_flags flags)

struct gpio_descs *devm_gpiod_get_array_optional(struct device *dev,
                                                 const char *con_id,
                                                 enum gpiod_flags flags)
```

可以使用 gpiod_put() 函数来释放 GPIO 描述符：

```c
void gpiod_put(struct gpio_desc *desc)
```

对于 GPIO 数组，可以使用此函数：

```c
void gpiod_put_array(struct gpio_descs *descs)
```

在调用这些函数后，严格禁止使用描述符。
也不允许从使用 gpiod_get_array() 获取的数组中单独释放描述符（使用 gpiod_put()）。

设备管理变体如下：

```c
void devm_gpiod_put(struct device *dev, struct gpio_desc *desc)

void devm_gpiod_put_array(struct device *dev, struct gpio_descs *descs)
```

**使用 GPIO**

**设置方向**
-----------------
驱动程序使用 GPIO 的第一步是设置其方向。如果没有给 gpiod_get*() 提供任何方向设置标志，则可以通过调用其中一个 gpiod_direction_*() 函数来完成此操作：

```c
int gpiod_direction_input(struct gpio_desc *desc)
int gpiod_direction_output(struct gpio_desc *desc, int value)
```

成功时返回值为零，否则返回负的 errno 值。应该检查返回值，因为 get/set 调用不会返回错误，并且可能会出现误配置。通常，您应该从任务上下文中发出这些调用。但是，对于支持自旋锁安全的 GPIO，在启用任务之前使用它们是可以的，作为早期板卡设置的一部分。
对于输出 GPIO，提供的值将成为初始输出值。这有助于避免系统启动期间信号的毛刺。
驱动程序还可以查询 GPIO 的当前方向：

```c
int gpiod_get_direction(const struct gpio_desc *desc)
```

此函数在无错误情况下返回 0 表示输出，1 表示输入，或在出错时返回错误代码。
请注意，GPIO没有默认的方向设置。因此，**在未先设置方向的情况下使用GPIO是非法的，并会导致不确定的行为！**

---

### 旋锁安全的GPIO访问

大多数GPIO控制器可以通过内存读/写指令进行访问。这些操作不需要睡眠，并且可以在硬（非线程化的）中断处理程序和其他类似上下文中安全地执行。
使用以下函数从原子上下文访问GPIO：

```c
int gpiod_get_value(const struct gpio_desc *desc);
void gpiod_set_value(struct gpio_desc *desc, int value);
```

这些值是布尔类型的，0表示非激活状态，非0表示激活状态。当读取输出引脚的值时，返回的应该是引脚上的实际值。这可能与指定的输出值不一致，因为可能存在诸如开漏信号和输出延迟等问题。
get/set调用不会返回错误，因为“无效GPIO”应该已经由`gpiod_direction_*()`提前报告。然而，请注意，并非所有平台都能读取输出引脚的值；对于不能读取的平台，应始终返回0。
此外，在无法安全地不睡眠访问的GPIO上使用这些调用（参见下文）是一个错误。

### 可能需要睡眠的GPIO访问

一些GPIO控制器必须通过基于消息的总线如I2C或SPI进行访问。读写这些GPIO值的命令需要等待以获取发送命令并接收响应的优先权。这需要睡眠，而这是不能在中断处理程序中完成的。
支持这种类型GPIO的平台通过以下函数来区分它们与其他GPIO：

```c
int gpiod_cansleep(const struct gpio_desc *desc)
```

若要访问此类GPIO，定义了一组不同的访问器：

```c
int gpiod_get_value_cansleep(const struct gpio_desc *desc)
void gpiod_set_value_cansleep(struct gpio_desc *desc, int value)
```

访问此类GPIO需要一个可以睡眠的上下文，例如线程化中断处理程序，并且必须使用这些带有`cansleep()`后缀的访问器，而不是无睡眠的访问器。
除了这些访问器可能会睡眠以及能够在硬中断处理程序中无法访问的GPIO上工作之外，这些调用与旋锁安全的调用作用相同。

---

### 低电平有效和开漏语义

为了确保消费者不必关心物理线路电平，所有的`gpiod_set_value_xxx()`和`gpiod_set_array_value_xxx()`函数都使用*逻辑*值进行操作。这意味着它们会考虑低电平有效的属性。

也就是说，它们会检查GPIO是否配置为低电平有效，如果是，则在驱动物理线路电平之前对传递的值进行调整。
同样适用于开漏或开源输出线：这些线不会主动将输出驱动为高电平（开漏）或低电平（开源），它们只是将输出切换到高阻态。用户不必关心这一点。（详细信息请参阅 driver.rst 中关于开漏的描述。）

通过这种方式，所有 gpiod_set_(array)_value_xxx() 函数都将参数 "value" 解释为 "有效" ("1") 或 "无效" ("0")。物理线路电平将相应地被驱动。

举例来说，如果为专用 GPIO 设置了低电平有效属性，并且 gpiod_set_(array)_value_xxx() 传递了 "有效" ("1")，那么物理线路电平将被驱动至低电平。
总结如下：

  * 函数（示例）                 线路属性          物理线路
  * gpiod_set_raw_value(desc, 0); 不关心             低
  * gpiod_set_raw_value(desc, 1); 不关心             高
  * gpiod_set_value(desc, 0);     默认（高电平有效） 低
  * gpiod_set_value(desc, 1);     默认（高电平有效） 高
  * gpiod_set_value(desc, 0);     低电平有效         高
  * gpiod_set_value(desc, 1);     低电平有效         低
  * gpiod_set_value(desc, 0);     开漏               低
  * gpiod_set_value(desc, 1);     开漏               高阻态
  * gpiod_set_value(desc, 0);     开源               高阻态
  * gpiod_set_value(desc, 1);     开源               高

可以使用 set_raw/get_raw 函数覆盖这些语义，但应尽可能避免这样做，尤其是对于与系统无关的驱动程序，它们不应需要关心实际物理线路电平，而应关注逻辑值。
访问原始 GPIO 值
-------------------------
存在一些需要管理 GPIO 线路逻辑状态的用户，即无论 GPIO 线路和设备之间有什么东西，他们都需要知道设备实际接收到的值。
以下函数集忽略 GPIO 的低电平有效或开漏属性，并在原始线路值上工作：

	int gpiod_get_raw_value(const struct gpio_desc *desc)
	void gpiod_set_raw_value(struct gpio_desc *desc, int value)
	int gpiod_get_raw_value_cansleep(const struct gpio_desc *desc)
	void gpiod_set_raw_value_cansleep(struct gpio_desc *desc, int value)
	int gpiod_direction_output_raw(struct gpio_desc *desc, int value)

还可以使用以下函数查询和切换 GPIO 的低电平有效状态：

	int gpiod_is_active_low(const struct gpio_desc *desc)
	void gpiod_toggle_active_low(struct gpio_desc *desc)

请注意，这些函数只应在极少数情况下使用；驱动程序不应需要关心物理线路电平或开漏语义。
使用单个函数调用来访问多个 GPIO
-------------------------------------
以下函数获取或设置 GPIO 数组的值：

	int gpiod_get_array_value(unsigned int array_size,
				  struct gpio_desc **desc_array,
				  struct gpio_array *array_info,
				  unsigned long *value_bitmap);
	int gpiod_get_raw_array_value(unsigned int array_size,
				      struct gpio_desc **desc_array,
				      struct gpio_array *array_info,
				      unsigned long *value_bitmap);
	int gpiod_get_array_value_cansleep(unsigned int array_size,
					   struct gpio_desc **desc_array,
					   struct gpio_array *array_info,
					   unsigned long *value_bitmap);
	int gpiod_get_raw_array_value_cansleep(unsigned int array_size,
					   struct gpio_desc **desc_array,
					   struct gpio_array *array_info,
					   unsigned long *value_bitmap);

	int gpiod_set_array_value(unsigned int array_size,
				  struct gpio_desc **desc_array,
				  struct gpio_array *array_info,
				  unsigned long *value_bitmap)
	int gpiod_set_raw_array_value(unsigned int array_size,
				      struct gpio_desc **desc_array,
				      struct gpio_array *array_info,
				      unsigned long *value_bitmap)
	int gpiod_set_array_value_cansleep(unsigned int array_size,
					   struct gpio_desc **desc_array,
					   struct gpio_array *array_info,
					   unsigned long *value_bitmap)
	int gpiod_set_raw_array_value_cansleep(unsigned int array_size,
					       struct gpio_desc **desc_array,
					       struct gpio_array *array_info,
					       unsigned long *value_bitmap)

数组可以是任意一组 GPIO。如果芯片驱动支持，函数将尝试同时访问属于同一组或芯片的 GPIO，这种情况下可以期望显著提高性能。如果无法同时访问，则将按顺序访问 GPIO。
这些函数接受四个参数：

	* array_size	- 元素的数量
	* desc_array	- GPIO 描述符数组
	* array_info	- 从 gpiod_get_array() 获取的可选信息
	* value_bitmap	- 用于存储 GPIO 值的位图（获取）或分配给 GPIO 的值的位图（设置）

描述符数组可以通过 gpiod_get_array() 函数或其变体获得。如果该函数返回的描述符组与所需的 GPIO 组匹配，那么只需使用 gpiod_get_array() 返回的 struct gpio_descs 即可访问这些 GPIO：

	struct gpio_descs *my_gpio_descs = gpiod_get_array(...);
	gpiod_set_array_value(my_gpio_descs->ndescs, my_gpio_descs->desc,
			      my_gpio_descs->info, my_gpio_value_bitmap);

也可以访问完全任意的描述符数组。描述符可能通过任何组合的 gpiod_get() 和 gpiod_get_array() 获得。之后，必须手动设置描述符数组才能传递给上述函数之一。在这种情况下，array_info 应设置为 NULL。
请注意，为了获得最佳性能，属于同一芯片的 GPIO 在描述符数组中应该是连续的。
如果描述符的数组索引与单个芯片上的硬件引脚编号相匹配，则可能会获得更好的性能。如果传递给 get/set 数组函数的数组与从 gpiod_get_array() 获得的数组匹配，并且还传递了与数组关联的 array_info，那么函数可能会采取快速位图处理路径，直接将 value_bitmap 参数传递给芯片的 .get/set_multiple() 回调。这允许利用 GPIO 银行作为数据 I/O 端口而不损失太多性能。
gpiod_get_array_value() 及其变体的成功返回值为 0，错误时为负数。请注意与 gpiod_get_value() 的区别，后者在成功时返回 0 或 1 来表示 GPIO 值。使用数组函数时，GPIO 值存储在 value_array 中，而不是作为返回值传递。
将GPIO映射到IRQ
--------------------
GPIO线路通常可以用作IRQ。你可以通过以下函数获取与给定GPIO对应的IRQ编号：

```c
int gpiod_to_irq(const struct gpio_desc *desc)
```

该函数会返回一个IRQ编号，或者如果无法完成映射（很可能是因为特定的GPIO不能用作IRQ）则返回一个负的errno代码。使用没有通过`gpiod_direction_input()`设置为输入的GPIO，或使用非`gpiod_to_irq()`返回的IRQ编号是未检查的错误。`gpiod_to_irq()`不允许休眠。`gpiod_to_irq()`返回的非错误值可以传递给`request_irq()`或`free_irq()`。它们通常会被存储在平台设备的IRQ资源中，由特定于板卡的初始化代码执行。需要注意的是，IRQ触发选项是IRQ接口的一部分，例如`IRQF_TRIGGER_FALLING`，以及系统唤醒功能。

GPIO与ACPI
==============

在ACPI系统上，GPIO通过设备的_CRS配置对象中列出的GpioIo()/GpioInt()资源描述。这些资源不提供GPIO的连接ID（名称），因此需要额外的机制来实现这一点。
符合ACPI 5.1或更高版本的系统可能提供一个_DSD配置对象，其中可以用于为_CRS中的GpioIo()/GpioInt()资源描述的特定GPIO提供连接ID。如果有这种情况，GPIO子系统将自动处理它。但是，如果没有_DSD，则需要设备驱动程序提供GpioIo()/GpioInt()资源和GPIO连接ID之间的映射。
详细信息请参考Documentation/firmware-guide/acpi/gpio-properties.rst。

与传统GPIO子系统的交互
==========================================
许多内核子系统和驱动程序仍然使用传统的基于整数的接口来处理GPIO。强烈建议更新这些到新的gpiod接口。对于需要同时使用两个接口的情况，下面两个函数允许将GPIO描述符转换为GPIO整数命名空间及反向操作：

```c
int desc_to_gpio(const struct gpio_desc *desc)
struct gpio_desc *gpio_to_desc(unsigned gpio)
```

由`desc_to_gpio()`返回的GPIO编号可以在`desc`不被释放的情况下安全地作为gpio_*()函数的参数使用。
同样地，传递给`gpio_to_desc()`的GPIO编号必须先通过如`gpio_request_one()`等方法正确获取，并且返回的GPIO描述符仅在使用`gpio_free()`释放该GPIO编号之前被认为是有效的。
禁止使用一个API获取的GPIO通过另一个API释放，这会导致未检查的错误。
