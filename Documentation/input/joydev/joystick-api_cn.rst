.. _joystick-api:

=====================
编程接口
=====================

:作者: Ragnar Hojland Espinosa <ragnar@macula.net> - 1998年8月7日

介绍
============

.. important::
   本文档描述的是旧版的 ``js`` 接口。新客户端建议切换到通用事件（``evdev``）接口。
1.0 驱动程序使用了一种新的基于事件的方法来处理摇杆驱动程序。用户程序不再轮询摇杆值，而是摇杆驱动程序仅报告其状态的任何变化。更多详细信息请参阅摇杆包中的 joystick-api.txt、joystick.h 和 jstest.c 文件。摇杆设备可以以阻塞或非阻塞模式使用，并支持 select() 调用。为了向后兼容，旧版（v0.x）接口仍然被包含在内。任何使用旧接口调用摇杆驱动程序的操作都会返回与旧接口兼容的值。此接口仍然限制为2个轴，尽管驱动程序提供了最多32个轴，但使用它的应用程序通常只解码2个按钮。

初始化
==============

按照通常的语义打开摇杆设备（即使用 open 函数）。由于驱动程序现在报告的是事件而不是轮询变化，在打开之后会立即发出一系列合成事件（JS_EVENT_INIT），你可以通过读取这些事件来获取摇杆的初始状态。默认情况下，设备以阻塞模式打开：

```c
int fd = open ("/dev/input/js0", O_RDONLY);
```

事件读取
=============

```c
struct js_event e;
read (fd, &e, sizeof(e));
```

其中 js_event 的定义如下：

```c
struct js_event {
    __u32 time;     /* 事件时间戳（毫秒） */
    __s16 value;    /* 值 */
    __u8 type;      /* 事件类型 */
    __u8 number;    /* 轴/按钮编号 */
};
```

如果读取成功，它将返回 sizeof(e)，除非你想在一次读取中读取多个事件，如第3.1节所述。

`js_event.type`
-------------

`type` 的可能值为：

```c
#define JS_EVENT_BUTTON         0x01    /* 按钮按下/释放 */
#define JS_EVENT_AXIS           0x02    /* 摇杆移动 */
#define JS_EVENT_INIT           0x80    /* 设备的初始状态 */
```

如上所述，驱动程序在打开时会发出合成的 JS_EVENT_INIT 事件。例如，如果它正在发出一个 INIT BUTTON 事件，则当前的类型值为：

```c
int type = JS_EVENT_BUTTON | JS_EVENT_INIT;    /* 0x81 */
```

如果你选择不区分合成事件和真实事件，你可以关闭 JS_EVENT_INIT 位：

```c
type &= ~JS_EVENT_INIT;              /* 0x01 */
```

`js_event.number`
---------------

`number` 的值对应生成事件的轴或按钮。注意它们分别编号（也就是说，你既有轴 0 也有按钮 0）。一般而言，

        =============== =======
        轴            编号
        =============== =======
        第一轴 X          0
        第一轴 Y          1
        第二轴 X          2
        第二轴 Y          3
        ……以此类推
        =============== =======

方向帽（hats）因摇杆类型而异。有些可以朝8个方向移动，有些只能朝4个方向移动。然而，驱动程序总是将方向帽报告为两个独立的轴，即使硬件不允许独立移动。

`js_event.value`
--------------

对于轴，`value` 是一个介于 -32767 到 +32767 之间的有符号整数，表示摇杆沿该轴的位置。如果你在摇杆处于“中立”位置时没有读取到0，或者它没有覆盖全范围，你应该重新校准它（例如，使用 jscal）。
对于一个按钮，按下事件的`value`为1，释放事件的`value`为0。虽然以下代码可以正常工作，前提是你要单独处理`JS_EVENT_INIT`事件：

```c
if (js_event.type == JS_EVENT_BUTTON) {
    buttons_state ^= (1 << js_event.number);
}
```

但是下面这种写法更安全，因为它不会与驱动程序失去同步。而且你无需在第一段代码中单独编写处理`JS_EVENT_INIT`事件的函数，因此这段代码更简洁：

```c
if ((js_event.type & ~JS_EVENT_INIT) == JS_EVENT_BUTTON) {
    if (js_event.value)
        buttons_state |= (1 << js_event.number);
    else
        buttons_state &= ~(1 << js_event.number);
}
```

`js_event.time`
---------------

事件生成的时间存储在`js_event.time`中。这是一个自过去某个时刻以来以毫秒为单位的时间值。这有助于检测双击、判断轴移动和按钮按下是否同时发生等类似情况。

读取
====

如果你以阻塞模式打开设备，读取操作会一直等待直到有事件生成并被有效读取。如果你不能一直等待（诚然，这是很长一段时间），有两个替代方案：

a) 使用select来等待数据在文件描述符(fd)上可读，或者直到超时。select(2)手册页有一个很好的示例。
b) 以非阻塞模式打开设备（O_NONBLOCK）。

`O_NONBLOCK`
------------

如果在O_NONBLOCK模式下读取返回-1，这并不一定是“真正的”错误（请检查errno(3)）。这可能只是意味着驱动程序队列中没有待读取的事件。你应该读取队列中的所有事件（即，直到你得到-1）。

例如，

```c
while (1) {
    while (read (fd, &e, sizeof(e)) > 0) {
        process_event (e);
    }
    /* 当队列为空时返回EAGAIN */
    if (errno != EAGAIN) {
        /* 错误 */
    }
    /* 对已处理的事件做些有趣的事情 */
}
```

清空队列的一个原因是如果队列满了，你会开始丢失事件，因为队列是有限的，旧事件会被新事件覆盖。另一个原因是希望了解所有发生的事件，并不延迟处理。

为什么队列会满？因为你没有清空队列，或者从一次读取到另一次读取之间的时间过长，导致生成了太多无法存储在队列中的事件。请注意，高系统负载可能会进一步延长这些读取之间的间隔。

如果两次读取之间的时间足以填满队列并丢失一个事件，驱动程序将切换到启动模式，并且下次读取时，将生成合成事件（JS_EVENT_INIT），以告知操纵杆的实际状态。

.. note::

   截至版本1.2.8，队列是循环的，能够容纳64个事件。你可以通过增加joystick.h中的JS_BUFF_SIZE并重新编译驱动程序来增加这个大小。
在上述代码中，你可能希望一次读取多个事件，使用典型的 `read(2)` 功能。为此，你可以将上面的 `read` 替换为如下形式：

```c
struct js_event mybuffer[0xff];
int i = read(fd, mybuffer, sizeof(mybuffer));
```

在这种情况下，如果队列为空，`read` 将返回 -1；否则返回其他值，其中读取的事件数为 `i / sizeof(js_event)`。如果缓冲区已满，最好处理这些事件并继续读取直到清空驱动程序队列。

### IOCTLs

摇杆驱动定义了以下 `ioctl(2)` 操作：

```c
#define JSIOCGAXES	/* 获取轴的数量		char	*/
#define JSIOCGBUTTONS	/* 获取按钮的数量	char	*/
#define JSIOCGVERSION	/* 获取驱动版本		int	*/
#define JSIOCGNAME(len) /* 获取标识字符串		char	*/
#define JSIOCSCORR	/* 设置校正值		&js_corr */
#define JSIOCGCORR	/* 获取校正值		&js_corr */
```

例如，要读取轴的数量：

```c
char number_of_axes;
ioctl(fd, JSIOCGAXES, &number_of_axes);
```

### JSIOCGVERSION

`JSIOCGVERSION` 是一种检查运行时驱动是否为 1.0+ 并支持事件接口的好方法。如果不支持，`IOCTL` 将失败。对于编译时决策，可以测试 `JS_VERSION` 符号：

```c
#ifdef JS_VERSION
#if JS_VERSION > 0xsomething
```

### JSIOCGNAME

`JSIOCGNAME(len)` 允许你获取摇杆的名称字符串——与启动时打印的内容相同。`len` 参数是应用程序请求名称时提供的缓冲区长度。它用于避免名称过长导致的溢出：

```c
char name[128];
if (ioctl(fd, JSIOCGNAME(sizeof(name)), name) < 0)
    strscpy(name, "Unknown", sizeof(name));
printf("Name: %s\n", name);
```

### JSIOC[SG]CORR

关于 `JSIOC[SG]CORR` 的用法，建议查看 `jscal.c`。它们通常不需要在普通程序中使用，只在摇杆校准软件（如 `jscal` 或 `kcmjoy`）中使用。这些 `IOCTL` 和数据类型不被认为是 API 的稳定部分，因此可能会在后续版本中无警告地更改。
`JSIOCSCORR` 和 `JSIOCGCORR` 都期望 `&js_corr` 能够保存所有轴的信息。即：`struct js_corr corr[MAX_AXIS];`

`struct js_corr` 定义为：

```c
struct js_corr {
    __s32 coef[8];
    __u16 prec;
    __u16 type;
};
```

其中 `type`：

```c
#define JS_CORR_NONE            0x00    /* 返回原始值 */
#define JS_CORR_BROKEN          0x01    /* 断裂线 */
```

### 向后兼容性

0.x 版本的摇杆驱动 API 相当有限，并且其使用已被弃用。不过，驱动提供了向后兼容性。这里有一个简要总结：

```c
struct JS_DATA_TYPE js;
while (1) {
    if (read(fd, &js, JS_RETURN) != JS_RETURN) {
        /* 错误 */
    }
    usleep(1000);
}
```

从示例可以看出，`read` 立即返回摇杆的实际状态：

```c
struct JS_DATA_TYPE {
    int buttons;    /* 按钮的即时状态 */
    int x;          /* X 轴的即时值 */
    int y;          /* Y 轴的即时值 */
};
```

`JS_RETURN` 定义为：

```c
#define JS_RETURN       sizeof(struct JS_DATA_TYPE)
```

要测试按钮的状态：

```c
first_button_state  = js.buttons & 1;
second_button_state = js.buttons & 2;
```

在最初的 0.x 版本驱动中，轴值没有定义范围，除了值是非负的。1.2.8+ 版本的驱动使用固定的范围报告值：1 是最小值，128 是中心值，255 是最大值。
v0.8.0.2 驱动还为“数字摇杆”（现在称为多系统摇杆）提供了一个接口，在 `/dev/djsX` 下。此驱动并不试图与该接口兼容。

### 最终说明

欢迎评论、补充和特别是纠正。
文档适用于至少 1.2.8 版本的摇杆驱动，最终的文档来源是 “使用源码，卢克”，或者按照你的方便，Vojtech。
