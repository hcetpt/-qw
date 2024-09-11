编程游戏端口驱动程序
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

基本的经典游戏端口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果游戏端口仅提供inb()/outb()功能，则将其注册到手柄驱动程序所需的代码非常简单：

```c
struct gameport gameport;

gameport.io = MY_IO_ADDRESS;
gameport_register_port(&gameport);
```

确保`struct gameport`在其他所有字段中都初始化为0。游戏端口通用代码将负责其余部分。

如果你的硬件支持多个IO地址，并且你的驱动程序可以选择要编程的硬件地址，那么从更特殊的地址开始是首选的，因为与标准0x201地址冲突的可能性较小。

例如，如果你的驱动程序支持地址0x200、0x208、0x210和0x218，那么0x218将是首选地址。

如果你的硬件支持一个未映射到ISA IO空间（高于0x1000）的游戏端口地址，请使用该地址，并且不要映射ISA镜像。

同时，始终对整个被游戏端口占用的IO空间请求`request_region()`。虽然实际上只使用了一个IO端口，但游戏端口通常会占用从一个到十六个地址的IO空间。

请考虑在`->open()`回调中启用ISA空间映射的IO上的游戏端口——这样它仅在确实有东西使用时才会占用IO空间。再次在`->close()`回调中禁用它。你也可以在`->open()`回调中选择IO地址，这样即使某些可能的地址已被其他游戏端口占用，也不会失败。

内存映射的游戏端口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当游戏端口可以通过MMIO访问时，这种方式是优选的，因为它更快，允许每秒更多的读取操作。注册这样的游戏端口并不像基本的IO端口那样容易，但也不是特别复杂：

```c
struct gameport gameport;

void my_trigger(struct gameport *gameport)
{
    my_mmio = 0xff;
}

unsigned char my_read(struct gameport *gameport)
{
    return my_mmio;
}

gameport.read = my_read;
gameport.trigger = my_trigger;
gameport_register_port(&gameport);
```

.. _gameport_pgm_cooked_mode:

熟数据模式的游戏端口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

有些游戏端口可以以数字形式报告轴值，这意味着驱动程序不必以旧的方式测量它们——游戏端口中内置了ADC。要注册一个熟数据模式的游戏端口：

```c
struct gameport gameport;

int my_cooked_read(struct gameport *gameport, int *axes, int *buttons)
{
    int i;

    for (i = 0; i < 4; i++)
        axes[i] = my_mmio[i];
    buttons[0] = my_mmio[4];
}

int my_open(struct gameport *gameport, int mode)
{
    return -(mode != GAMEPORT_MODE_COOKED);
}

gameport.cooked_read = my_cooked_read;
gameport.open = my_open;
gameport.fuzz = 8;
gameport_register_port(&gameport);
```

这里唯一令人困惑的是fuzz值。通过实验确定，它是ADC数据中的噪声量。完美的游戏端口可以将其设置为零，大多数常见的游戏端口的fuzz值介于8到32之间。参见analog.c和input.c中对fuzz值的处理——fuzz值决定了用于消除数据噪声的高斯滤波窗口的大小。

更复杂的游戏端口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

游戏端口可以同时支持原始模式和熟数据模式。在这种情况下，结合示例1+2或1+3。游戏端口可以支持内部校准——详见下文，以及lightning.c和analog.c中关于其工作原理的说明。如果你的驱动程序支持同时运行多个游戏端口实例，请使用`gameport`结构体中的`->private`成员指向你的数据。

注销游戏端口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

简单：

```c
gameport_unregister_port(&gameport);
```

游戏端口结构体
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```c
struct gameport {
    void *port_data;

    // 驱动程序私有指针，供游戏端口驱动程序自由使用。（不是手柄驱动程序！）
    
    char name[32];

    // 驱动程序名称，由调用gameport_set_name()的驱动程序设置。仅供信息用途。
}
```
```c
char phys[32];

// 由调用gameport_set_phys()设置的游戏端口的物理名称/描述
// 仅用于信息目的

int io;

// 用于原始模式的I/O地址。如果您的游戏端口支持原始模式，您必须设置此值或->read()为某个值

int speed;

// 游戏端口在原始模式下的读取速度，以每秒数千次读取计

int fuzz;

// 如果游戏端口支持烹饪模式，则应将其设置为表示数据中噪声量的值。详见 :ref:`gameport_pgm_cooked_mode`

void (*trigger)(struct gameport *);

// 触发器。此函数应触发ns558的一次性读取。如果设置为NULL，则使用outb(0xff, io)

unsigned char (*read)(struct gameport *);

// 读取按钮和ns558的一次性位。如果设置为NULL，则使用inb(io)代替

int (*cooked_read)(struct gameport *, int *axes, int *buttons);

// 如果游戏端口支持烹饪模式，则应将其指向烹饪读取函数。该函数应将操纵杆轴的四个值填充到axes[0..3]中，并将四个代表按钮的位填充到buttons[0]中

int (*calibrate)(struct gameport *, int *axes, int *max);

// 用于校准ADC硬件的函数。当被调用时，axes[0..3]应由调用者预先填充烹饪数据，max[0..3]应预先填充每个轴的预期最大值。校准函数应设置ADC硬件的灵敏度，使其最大值适合其范围，并重新计算axes[]值以匹配新的灵敏度或将它们重新从硬件中读取，以便提供有效值

int (*open)(struct gameport *, int mode);

// open()有两个用途。首先，驱动程序要么以原始模式打开端口，要么以烹饪模式打开端口，open()回调可以决定支持哪些模式
```
当然，以下是翻译：

其次，资源分配可以在这里进行。端口也可以在这里启用。在调用此函数之前，`gameport` 结构体中的其他字段（特别是 `io` 成员）不必有效。

```
void (*close)(struct gameport *);

Close() 应该释放由 open 分配的资源，可能还会禁用 gameport。
```

```c
struct timer_list poll_timer;
unsigned int poll_interval;     /* 以毫秒为单位 */
spinlock_t timer_lock;
unsigned int poll_cnt;
void (*poll_handler)(struct gameport *);
struct gameport *parent, *child;
struct gameport_driver *drv;
struct mutex drv_mutex;         /* 保护 serio->drv，以便属性可以锁定驱动程序 */
struct device dev;
struct list_head node;

// 供 gameport 层内部使用
```

```
};
```

享受吧！
