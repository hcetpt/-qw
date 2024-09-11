创建输入设备驱动程序
=================================

最简单的示例
~~~~~~~~~~~~~~~~~~~~

以下是一个非常简单的输入设备驱动程序示例。该设备只有一个按钮，并且该按钮在I/O端口BUTTON_PORT上可访问。当按下或释放时，会发生BUTTON_IRQ中断。驱动程序可能如下所示：

```c
#include <linux/input.h>
#include <linux/module.h>
#include <linux/init.h>

#include <asm/irq.h>
#include <asm/io.h>

static struct input_dev *button_dev;

static irqreturn_t button_interrupt(int irq, void *dummy)
{
    input_report_key(button_dev, BTN_0, inb(BUTTON_PORT) & 1);
    input_sync(button_dev);
    return IRQ_HANDLED;
}

static int __init button_init(void)
{
    int error;

    if (request_irq(BUTTON_IRQ, button_interrupt, 0, "button", NULL)) {
        printk(KERN_ERR "button.c: Can't allocate irq %d\n", BUTTON_IRQ);
        return -EBUSY;
    }

    button_dev = input_allocate_device();
    if (!button_dev) {
        printk(KERN_ERR "button.c: Not enough memory\n");
        error = -ENOMEM;
        goto err_free_irq;
    }

    button_dev->evbit[0] = BIT_MASK(EV_KEY);
    button_dev->keybit[BIT_WORD(BTN_0)] = BIT_MASK(BTN_0);

    error = input_register_device(button_dev);
    if (error) {
        printk(KERN_ERR "button.c: Failed to register device\n");
        goto err_free_dev;
    }

    return 0;

err_free_dev:
    input_free_device(button_dev);
err_free_irq:
    free_irq(BUTTON_IRQ, button_interrupt);
    return error;
}

static void __exit button_exit(void)
{
    input_unregister_device(button_dev);
    free_irq(BUTTON_IRQ, button_interrupt);
}

module_init(button_init);
module_exit(button_exit);
```

示例的工作原理
~~~~~~~~~~~~~~~~~~~~~

首先需要包含`<linux/input.h>`文件，它与输入子系统接口。这提供了所有必需的定义。
在_init函数中，该函数在加载模块或启动内核时被调用，它获取所需的资源（还应检查设备是否存在）。
然后通过`input_allocate_device()`分配一个新的输入设备结构并设置输入位字段。这样，设备驱动程序告诉输入系统的其他部分它的身份——这个输入设备可以生成或接受哪些事件。我们的示例设备只能生成EV_KEY类型事件，并且只有BTN_0事件代码。因此我们只设置这两个位。我们也可以使用：
```c
set_bit(EV_KEY, button_dev->evbit);
set_bit(BTN_0, button_dev->keybit);
```
但是当涉及到多个位时，第一种方法往往更短。
然后示例驱动程序通过调用：
```c
input_register_device(button_dev);
```
将输入设备结构注册到输入驱动程序的链表中，并调用设备处理模块的_connect函数来告知它们出现了一个新的输入设备。`input_register_device()`可能会休眠，因此不能从中断或持有自旋锁的情况下调用。
在使用过程中，唯一使用的驱动程序函数是：
```c
button_interrupt()
```
每当来自按钮的中断发生时，该函数会检查其状态并通过：
```c
input_report_key()
```
调用向输入系统报告状态。不需要检查中断例程是否没有向输入系统报告两个相同的值事件（例如按下、按下），因为`input_report_*`函数会自行检查。
然后有：
```c
input_sync()
```
调用来告诉接收事件的人我们已发送完整的报告。
在单按钮情况下，这似乎并不重要，但对于鼠标移动来说非常重要，因为你不想单独解释X和Y值，因为这会导致不同的移动。

`dev->open()` 和 `dev->close()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果驱动程序必须反复轮询设备，因为它没有来自设备的中断，并且轮询过于昂贵而无法一直进行，或者如果设备使用了有价值的资源（例如中断），它可以使用open和close回调来知道何时停止轮询或释放中断，以及何时必须恢复轮询或重新获取中断。为此，我们需要在示例驱动程序中添加以下内容：
```c
static int button_open(struct input_dev *dev)
{
    if (request_irq(BUTTON_IRQ, button_interrupt, 0, "button", NULL)) {
        printk(KERN_ERR "button.c: Can't allocate irq %d\n", BUTTON_IRQ);
        return -EBUSY;
    }

    return 0;
}

static void button_close(struct input_dev *dev)
{
    free_irq(BUTTON_IRQ, button_interrupt);
}

static int __init button_init(void)
{
    ..
    button_dev->open = button_open;
    button_dev->close = button_close;
    ..
}
```

请注意，输入核心跟踪设备的用户数量，并确保仅在第一个用户连接到设备时调用`dev->open()`，并且在最后一个用户断开连接时调用`dev->close()`。对这两个回调的调用是串行化的。
`open()` 回调函数在成功时应返回 0，在失败时返回任何非零值。`close()` 回调函数（它是空类型）必须总是成功。

抑制输入设备
~~~~~~~~~~~~~~

抑制一个设备意味着忽略来自该设备的输入事件。因此，这涉及到维护与输入处理程序的关系——这些关系可能是已经存在的，也可能是设备处于抑制状态时需要建立的新关系。
如果一个设备被抑制，那么没有输入处理程序会接收到它的事件。
由于没有任何处理程序希望接收来自设备的事件，可以通过在抑制和解除抑制操作时调用设备的 `close()`（如果有用户）和 `open()`（如果有用户）来进一步利用这一点。实际上，`close()` 的含义是停止向输入核心提供事件，而 `open()` 的含义是开始向输入核心提供事件。
在抑制设备时（如果有用户）调用设备的 `close()` 方法可以让驱动程序节省电力。这可以通过直接关闭设备电源或释放驱动程序在 `open()` 中获得的运行时 PM 引用来实现，前提是驱动程序使用了运行时 PM。
抑制和解除抑制与输入处理程序打开和关闭设备的操作是正交的。用户空间可能希望在任何处理程序与设备匹配之前预先抑制设备。
抑制和解除抑制与设备作为唤醒源也是正交的。设备作为唤醒源的作用是在系统休眠时，而不是在系统运行时。驱动程序如何编程其抑制、休眠和作为唤醒源之间的交互是特定于驱动程序的。
以网络设备为例——将网络接口关闭并不意味着不能通过这个接口通过局域网唤醒系统。因此，可能存在即使在被抑制时也应该被视为唤醒源的输入驱动程序。实际上，在许多 I2C 输入设备中，它们的中断被声明为唤醒中断，并且其处理发生在驱动程序的核心部分，这部分并不知道输入特有的抑制（也不应该知道）。包含多个接口的复合设备可以按接口逐个抑制，例如抑制一个接口不应影响设备作为唤醒源的能力。
如果一个设备在被抑制时仍要被视为唤醒源，则在编程其 `suspend()` 时需要特别注意，因为它可能需要调用设备的 `open()`。根据 `close()` 对该设备的具体含义，不在休眠前调用 `open()` 可能会导致无法提供任何唤醒事件。设备无论如何都会进入休眠状态。
基本事件类型
~~~~~~~~~~~~~~~~~

最简单的事件类型是`EV_KEY`，用于处理按键和按钮。它通过以下函数报告给输入系统：

```c
input_report_key(struct input_dev *dev, int code, int value)
```

有关`code`的允许值（从0到`KEY_MAX`），请参见`uapi/linux/input-event-codes.h`。`value`被解释为布尔值，即任何非零值表示按键按下，零值表示按键释放。输入代码仅在值发生变化时生成事件。

除了`EV_KEY`之外，还有另外两种基本事件类型：`EV_REL`和`EV_ABS`。它们分别用于处理设备提供的相对值和绝对值。例如，鼠标X轴的移动就是一个相对值。鼠标将其报告为相对于上次位置的变化，因为它没有绝对坐标系可以工作。绝对事件则适用于操纵杆和数位板等设备——这些设备是在绝对坐标系中工作的。

让设备报告`EV_REL`类型的按键与`EV_KEY`一样简单；只需设置相应的位，并调用如下函数：

```c
input_report_rel(struct input_dev *dev, int code, int value)
```

事件仅在值非零时生成。

然而，`EV_ABS`需要一些特别的处理。在调用`input_register_device`之前，必须为设备的每个绝对轴填充`input_dev`结构中的附加字段。如果我们的按钮设备还具有`ABS_X`轴，则：

```c
button_dev.absmin[ABS_X] = 0;
button_dev.absmax[ABS_X] = 255;
button_dev.absfuzz[ABS_X] = 4;
button_dev.absflat[ABS_X] = 8;
```

或者，可以直接使用：

```c
input_set_abs_params(button_dev, ABS_X, 0, 255, 4, 8);
```

这种设置适用于操纵杆X轴，最小值为0，最大值为255（操纵杆必须能够达到这个值，偶尔超过也没问题，但必须始终能到达最小和最大值），数据噪声在±4范围内，中心平坦区域大小为8。

如果不关心`absfuzz`和`absflat`，可以将它们设置为零，这意味着该设备非常精确且总是返回到中心位置（如果有中心位置的话）。

`BITS_TO_LONGS()`、`BIT_WORD()`、`BIT_MASK()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`bitops.h`中的这三个宏有助于某些位字段计算：

- `BITS_TO_LONGS(x)` — 返回x位位字段数组的长度（以长整型为单位）
- `BIT_WORD(x)` — 返回位x在数组中的索引（以长整型为单位）
- `BIT_MASK(x)` — 返回位x在长整型中的索引

`id*` 和 `name` 字段
~~~~~~~~~~~~~~~~~~~~~~~

在注册输入设备之前，输入设备驱动程序应设置`dev->name`。这是一个像“Generic button device”这样的字符串，包含设备的用户友好名称。

`id*`字段包含设备的总线ID（PCI、USB等）、供应商ID和设备ID。总线ID定义在`input.h`中，供应商ID和设备ID定义在`pci_ids.h`、`usb_ids.h`等头文件中。这些字段应在注册设备之前由输入设备驱动程序设置。

`idtype`字段可用于存储特定于输入设备驱动程序的信息。
ID 和 name 字段可以通过 evdev 接口传递到用户空间。

keycode、keycodemax 和 keycodesize 字段
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

这三个字段应由具有密集键位图的输入设备使用。
- `keycode` 是一个数组，用于将扫描码映射到输入系统键码。
- `keycodemax` 应包含该数组的大小，而 `keycodesize` 则表示数组中每个条目的大小（以字节为单位）。
- 用户空间可以使用 `EVIOCGKEYCODE` 和 `EVIOCSKEYCODE` 的 ioctl 调用通过相应的 evdev 接口查询和修改当前扫描码到键码的映射。
- 当设备填充了上述三个字段时，驱动程序可以依赖内核提供的默认实现来设置和查询键码映射，即 `dev->getkeycode()` 和 `dev->setkeycode()`。

`getkeycode()` 和 `setkeycode()` 回调允许驱动程序覆盖输入核心提供的默认键码/键码大小/键码最大值映射机制，并实现稀疏键码映射。

键自动重复
~~~~~~~~~~~~~~

... 很简单。它由 `input.c` 模块处理。不使用硬件自动重复，因为许多设备上没有这个功能，即使有这个功能，有时也会出现问题（例如：东芝笔记本电脑的键盘）。要为您的设备启用自动重复，只需在 `dev->evbit` 中设置 `EV_REP`。所有其他操作都将由输入系统处理。

其他事件类型及处理输出事件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

目前的其他事件类型包括：

- `EV_LED` —— 用于键盘上的 LED 灯。
- `EV_SND` —— 用于键盘蜂鸣声。
它们与例如关键事件非常相似，但方向相反——从系统到输入设备驱动程序。如果你的输入设备驱动程序能够处理这些事件，它必须设置 `evbit` 中相应的位，并且还要设置回调函数：

    button_dev->event = button_event;

    int button_event(struct input_dev *dev, unsigned int type,
                     unsigned int code, int value)
    {
        if (type == EV_SND && code == SND_BELL) {
            outb(value, BUTTON_BELL);
            return 0;
        }
        return -1;
    }

这个回调函数可能从一个中断或 BH（虽然这不是硬性规定）中被调用，因此不能休眠，并且完成时间不能太长。
