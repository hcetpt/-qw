GPIO Sysfs 用户空间接口
==================================

.. 警告::
   该 API 已被 `chardev.rst` 取代，ABI 文档已移至 `Documentation/ABI/obsolete/sysfs-gpio`
   新的开发应使用 `chardev.rst`，现有开发也应尽快迁移，因为此 API 将在未来被移除。
   在迁移期间，此接口将继续得到维护，但新功能将只添加到新的 API 中。

废弃的 sysfs ABI
----------------------
使用 "gpiolib" 实现框架的平台可以选择配置一个用于 GPIO 的 sysfs 用户界面。这与 debugfs 接口不同，因为它提供了对 GPIO 方向和值的控制，而不仅仅是显示 GPIO 状态摘要。此外，它可以在生产系统上存在，而无需调试支持。

根据系统的硬件文档，用户空间可以知道例如 GPIO #23 控制着用于保护闪存中引导加载程序段的写保护线。系统升级过程可能需要临时解除这种保护，首先导入一个 GPIO，然后改变其输出状态，然后再更新代码并重新启用写保护。在正常使用中，GPIO #23 从未被触及，内核也没有必要了解它。

同样，根据适当的硬件文档，在某些系统上，用户空间 GPIO 可以用来确定标准内核不知道的系统配置数据。对于某些任务，简单的用户空间 GPIO 驱动程序可能是系统真正需要的全部内容。

.. 注意::
   不要滥用 sysfs 来控制已经有合适内核驱动程序的硬件。

请阅读 `Documentation/driver-api/gpio/drivers-on-gpio.rst`
   以避免在用户空间重新发明内核轮子。

我是认真的。

Sysfs 中的路径
--------------
`/sys/class/gpio` 中有三种类型的条目：

- 控制接口，用于获取用户空间对 GPIO 的控制；

- GPIO 本身；以及

- GPIO 控制器（`gpio_chip` 实例）。
这是除了标准文件之外，还包括“device”符号链接。
控制接口是只写的：

    /sys/class/gpio/

	"export"..
用户空间可以通过将GPIO编号写入此文件，请求内核将GPIO的控制权导出到用户空间
示例： "echo 19 > export" 将为GPIO #19创建一个名为“gpio19”的节点（如果该GPIO没有被内核代码请求的话）

"unexport"..
撤销将GPIO导出到用户空间的效果
示例： "echo 19 > unexport" 将移除通过"export"文件导出的名为“gpio19”的节点

GPIO信号的路径类似于/sys/class/gpio/gpio42/（对于GPIO #42），并具有以下读写属性：

    /sys/class/gpio/gpioN/

	"direction"..
读取时显示为"in"或"out"。通常可以写入。写入"out"时，默认初始化值为低电平。为了确保无故障操作，可以写入"low"和"high"来配置GPIO作为输出，并设置初始值。
注意，如果内核不支持更改GPIO的方向，或者是由未明确允许用户空间重新配置GPIO方向的内核代码导出，则此属性**将不存在**。
"值"（`value`）...
读取为 0（非激活）或 1（激活）。如果 GPIO 被配置为输出，可以写入这个值；任何非零值都被视为激活。

如果引脚可以配置为生成中断的中断源，并且已经被配置为生成中断（参见“边沿”描述），则可以在该文件上使用 `poll(2)` 进行轮询，当触发中断时，`poll(2)` 将返回。如果你使用 `poll(2)`，请设置事件 `POLLPRI` 和 `POLLERR`。如果你使用 `select(2)`，请将文件描述符设置在 `exceptfds` 中。`poll(2)` 返回后，使用 `pread(2)` 在偏移量为零的位置读取值。或者，可以通过将 `lseek(2)` 设置到 sysfs 文件的开头并读取新值，或者关闭文件并重新打开以读取值。

"边沿"（`edge`）...
读取为 "none"、"rising"、"falling" 或 "both"。写入这些字符串来选择将使 `poll(2)` 在 “值” 文件上返回的信号边沿。

此文件仅在引脚可以配置为生成中断的输入引脚时存在。

"低电平激活"（`active_low`）...
读取为 0（假）或 1（真）。写入任何非零值以反转值属性的读写。现有的和后续的 `poll(2)` 支持通过边沿属性对“上升沿”和“下降沿”的配置将遵循此设置。

GPIO 控制器的路径类似于 `/sys/class/gpio/gpiochip42/`（对于实现从编号 #42 开始的 GPIO 的控制器），具有以下只读属性：

    /sys/class/gpio/gpiochipN/

- "基地址"（`base`）..
与 N 相同，由该芯片管理的第一个 GPIO。

- "标签"（`label`）..
提供的用于诊断（并不总是唯一）

`ngpio`..
表示这个设备管理了多少个GPIO（范围从N到N+ngpio-1）

板载文档通常会覆盖哪些GPIO被用于什么目的。然而，这些编号并不总是稳定的；在一个子卡上的GPIO可能会根据所使用的基板或者堆栈中的其他卡片而有所不同。在这样的情况下，您可能需要使用gpiochip节点（可能结合原理图）来确定某个信号对应的正确GPIO编号。

内核代码导出
--------------
内核代码可以显式地管理已经通过`gpio_request()`请求的GPIO的导出：

```c
/* 将GPIO导出到用户空间 */
int gpiod_export(struct gpio_desc *desc, bool direction_may_change);

/* 反向操作gpiod_export() */
void gpiod_unexport(struct gpio_desc *desc);

/* 创建一个指向已导出GPIO节点的sysfs链接 */
int gpiod_export_link(struct device *dev, const char *name,
		      struct gpio_desc *desc);
```

在内核驱动程序请求了一个GPIO之后，只有通过`gpiod_export()`才能使其在sysfs接口中可用。驱动程序可以控制信号方向是否允许改变。这有助于防止用户空间代码意外破坏重要的系统状态。

这种显式的导出有助于调试（使某些类型的实验更容易），或提供一个始终存在的接口，适合作为板级支持包的一部分进行文档说明。

在GPIO被导出之后，`gpiod_export_link()`允许从sysfs的其他部分创建指向GPIO sysfs节点的符号链接。驱动程序可以利用这一点，在它们自己的sysfs设备下以描述性的名称提供该接口。
