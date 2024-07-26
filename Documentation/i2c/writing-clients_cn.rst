实施 I2C 设备驱动程序
==================================

这是一个小型指南，为那些想要为 I2C 或 SMBus 设备编写内核驱动程序的人准备的，使用 Linux 作为协议主机/主控（而非从机）。为了设置一个驱动程序，你需要做几件事。有些是可选的，并且有些事情可以以稍微不同或完全不同的方式完成。将此视为指导而不是规则手册！

一般说明
==========

尽量保持内核命名空间尽可能干净。最好的方法是对所有全局符号使用唯一前缀。对于导出的符号这一点尤为重要，但对非导出的符号也最好这样做。在这个教程中我们将使用 `foo_` 前缀。
驱动程序结构
=============

通常情况下，你会实现一个单一的驱动程序结构并从中实例化所有客户端。记住，驱动程序结构包含通用访问例程，并且除了你提供的数据字段外应进行零初始化。客户端结构保存设备特定的信息，如驱动模型设备节点及其 I2C 地址。
```c
static struct i2c_device_id foo_idtable[] = {
	{ "foo", my_id_for_foo },
	{ "bar", my_id_for_bar },
	{ }
};

MODULE_DEVICE_TABLE(i2c, foo_idtable);

static struct i2c_driver foo_driver = {
	.driver = {
		.name	= "foo",
		.pm	= &foo_pm_ops,	/* 可选 */
	},

	.id_table	= foo_idtable,
	.probe		= foo_probe,
	.remove		= foo_remove,

	.shutdown	= foo_shutdown,	/* 可选 */
	.command	= foo_command,	/* 可选，已废弃 */
};
```
`name` 字段是驱动程序名称，不应包含空格。它应该与模块名称匹配（如果驱动程序可以被编译为模块），尽管你可以使用 `MODULE_ALIAS`（在这个例子中传递 "foo"）为模块添加另一个名称。如果驱动程序名称不匹配模块名称，则该模块不会自动加载（热插拔/冷插拔）
所有其他字段都是用于回调函数，这些将在下面解释。

额外的客户端数据
==================

每个客户端结构都有一个特殊的 `data` 字段，它可以指向任何结构。你应该利用这个来存储设备特定的数据：
```c
/* 存储值 */
void i2c_set_clientdata(struct i2c_client *client, void *data);

/* 获取值 */
void *i2c_get_clientdata(const struct i2c_client *client);
```
请注意，从内核 2.6.34 开始，你不再需要在 `remove()` 中或将 `probe()` 设置为 NULL。当发生这些情况时 i2c-core 会自动这样做。这也是核心唯一触及该字段的时候。

访问客户端
=============

假设我们有一个有效的客户端结构。在某个时刻，我们需要从客户端收集信息或向客户端写入新信息。
我发现定义 `foo_read` 和 `foo_write` 函数来做这件事是有用的。
对于某些情况，直接调用 I2C 函数可能更容易，但许多芯片都有一种寄存器值的概念，可以很容易地封装起来。
以下函数是简单的示例，不应直接复制：

```c
int foo_read_value(struct i2c_client *client, u8 reg)
{
    if (reg < 0x10) /* 字节大小的寄存器 */
        return i2c_smbus_read_byte_data(client, reg);
    else            /* 字长大小的寄存器 */
        return i2c_smbus_read_word_data(client, reg);
}

int foo_write_value(struct i2c_client *client, u8 reg, u16 value)
{
    if (reg == 0x10) /* 无法写入 - 驱动错误！ */
        return -EINVAL;
    else if (reg < 0x10) /* 字节大小的寄存器 */
        return i2c_smbus_write_byte_data(client, reg, value);
    else                /* 字长大小的寄存器 */
        return i2c_smbus_write_word_data(client, reg, value);
}
```

### 探测与绑定

Linux 的 I2C 栈最初是为了支持 PC 主板上的硬件监控芯片而编写的，因此包含了一些更适合 SMBus（以及 PC）而非 I2C 的假设。其中一个假设是大多数适配器和设备驱动程序都支持 SMBUS_QUICK 协议来探测设备的存在。另一个假设是设备及其驱动程序可以仅通过这些探测原语进行充分配置。随着 Linux 和其 I2C 栈在嵌入式系统和复杂的组件（如 DVB 适配器）中得到更广泛的应用，这些假设变得越来越有问题。对于那些会发出中断的 I2C 设备的驱动程序来说，它们需要更多的（且不同类型的）配置信息；对于处理无法通过协议探测区分的芯片变体或需要一些特定于电路板的信息才能正确运行的驱动程序来说，也是如此。

#### 设备/驱动绑定

系统基础设施（通常是特定于电路板的初始化代码或启动固件）报告存在的 I2C 设备。例如，可能有一个表格，在内核中或由引导加载程序提供，用于标识 I2C 设备，并将它们与有关 IRQ 和其他接线工件、芯片类型等特定于电路板的配置信息关联起来。这可以用来为每个 I2C 设备创建 i2c_client 对象。
使用这种绑定模型的 I2C 设备驱动程序的工作方式与其他任何 Linux 驱动程序一样：它们提供一个 probe() 方法来绑定这些设备，以及一个 remove() 方法来解绑。

```c
static int foo_probe(struct i2c_client *client);
static void foo_remove(struct i2c_client *client);
```

请注意，i2c_driver 不会创建这些客户端句柄。该句柄可以在 foo_probe() 中使用。如果 foo_probe() 报告成功（零而不是负状态码），则它可以保存该句柄并在 foo_remove() 返回前使用它。这种绑定模型被大多数 Linux 驱动程序采用。

探针函数在 id_table 的 name 字段中的条目与设备名称匹配时被调用。如果探针函数需要这个条目，它可以通过以下方式获取：

```c
const struct i2c_device_id *id = i2c_match_id(foo_idtable, client);
```

#### 设备创建

如果您确切知道某个 I2C 设备连接到了给定的 I2C 总线上，您可以通过简单地填充一个包含设备地址和驱动程序名称的 i2c_board_info 结构，并调用 i2c_new_client_device() 来实例化该设备。这将创建设备，然后驱动核心将负责找到正确的驱动程序并调用其 probe() 方法。
如果一个驱动程序支持不同的设备类型，您可以使用 type 字段指定您想要的类型。您还可以根据需要指定一个 IRQ 和平台数据。
有时您知道一个设备连接到了给定的 I2C 总线上，但您不知道它的确切地址。这种情况发生在电视适配器上，同一个驱动程序支持数十种略有不同的型号，而 I2C 设备地址从一种型号到另一种型号都在变化。在这种情况下，您可以使用 i2c_new_scanned_device() 变体，它类似于 i2c_new_client_device()，只是它接受一个额外的可能的 I2C 地址列表进行探测。为列表中第一个响应的地址创建设备。如果您期望在地址范围内存在多个设备，只需调用多次 i2c_new_scanned_device() 即可。
对 i2c_new_client_device() 或 i2c_new_scanned_device() 的调用通常发生在 I2C 总线驱动程序中。您可能希望保留返回的 i2c_client 引用以供后续使用。

#### 设备检测

设备检测机制伴随着许多缺点。
你需要一种可靠的方式来识别支持的设备（通常使用特定于设备的、专用的识别寄存器），否则可能会发生误检测，事情会迅速出错。请记住，I2C协议并不包含任何标准的方法来检测给定地址上是否存在芯片，更不用说识别设备的标准方法了。更糟糕的是，总线传输缺乏语义，这意味着相同的传输可能被一个芯片视为读操作，而被另一个芯片视为写操作。正因为如此，设备检测被认为是一种遗留机制，不应该在新代码中使用。

### 设备删除

通过`i2c_new_client_device()`或`i2c_new_scanned_device()`创建的每个I2C设备都可以通过调用`i2c_unregister_device()`进行注销。如果你不显式调用它，在底层I2C总线本身被移除之前，它会被自动调用，因为在设备驱动模型中，设备不能在其父设备之后存活。

### 初始化驱动

当内核启动时，或者当你的foo驱动模块被插入时，你需要做一些初始化工作。幸运的是，通常只需注册驱动模块就足够了：
```c
static int __init foo_init(void)
{
    return i2c_add_driver(&foo_driver);
}
module_init(foo_init);

static void __exit foo_cleanup(void)
{
    i2c_del_driver(&foo_driver);
}
module_exit(foo_cleanup);
```

`module_i2c_driver()`宏可以用来简化上述代码：
```c
module_i2c_driver(foo_driver);
```

请注意，某些函数被标记为`__init`。这些函数可以在内核启动（或模块加载）完成后被移除。同样地，被标记为`__exit`的函数在构建到内核时会被编译器丢弃，因为它们永远不会被调用。

### 驱动信息

```c
/* 替换你自己的姓名和电子邮件地址 */
MODULE_AUTHOR("Frodo Looijaard <frodol@dds.nl>");
MODULE_DESCRIPTION("Barf Inc. Foo I2C Devices Driver");

/* 允许一些非GPL许可证类型 */
MODULE_LICENSE("GPL");
```

### 功率管理

如果你的I2C设备在进入系统低功耗状态时需要特殊处理——比如将收发器置于低功耗模式，或者激活系统唤醒机制——可以通过实现驱动的`dev_pm_ops`中的相应回调（如suspend和resume）来完成。
这些是标准的驱动模型调用，其工作方式与其他任何驱动堆栈相同。这些调用可以休眠，并且可以使用I2C消息传递到正在挂起或恢复的设备（因为当这些调用发出时，它们的父I2C适配器处于活动状态，并且中断仍然启用）。

### 系统关机

如果你的I2C设备在系统关闭或重启（包括kexec）时需要特殊处理——比如关闭某些功能——可以使用shutdown()方法。
再次强调，这是一个标准的驱动模型调用，其工作方式与其他任何驱动堆栈相同：这些调用可以休眠，并且可以使用I2C消息传递。
命令功能
================

支持一种通用的类似于ioctl的回调函数调用。你很少会需要这个功能，而且它的使用已经被废弃了，因此新的设计不应该再使用它。

发送与接收
=====================

如果你想与你的设备进行通信，有几种不同的函数可以实现这一点。你可以在 `<linux/i2c.h>` 中找到所有这些函数。
如果你可以选择普通的I2C通信或SMBus级别的通信，请使用后者。所有的适配器都理解SMBus级别的命令，但只有部分适配器理解纯I2C通信！

纯I2C通信
-----------------------

```
int i2c_master_send(struct i2c_client *client, const char *buf, int count);
int i2c_master_recv(struct i2c_client *client, char *buf, int count);
```

这些函数从/向一个客户端读取/写入一些字节。客户端已经包含了I2C地址，所以你不需要包含它。第二个参数包含要读取/写入的字节，第三个参数表示要读取/写入的字节数（必须小于缓冲区的长度，同时应该小于64K，因为`msg.len`是u16类型）。返回值为实际读取/写入的字节数。
```
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msg, int num);
```

这可以发送一系列消息。每个消息可以是一个读取或写入操作，并且它们可以以任何方式混合。交易被合并：交易之间不会发出停止条件。`i2c_msg`结构体为每个消息包含客户端地址、消息的字节数以及消息数据本身。

你可以阅读文件`i2c-protocol.rst`获取关于实际I2C协议的更多信息。

SMBus通信
-------------------

```
s32 i2c_smbus_xfer(struct i2c_adapter *adapter, u16 addr, unsigned short flags, char read_write, u8 command, int size, union i2c_smbus_data *data);
```

这是通用的SMBus函数。下面列出的所有函数都是基于它实现的。永远不要直接使用这个函数！

```
s32 i2c_smbus_read_byte(struct i2c_client *client);
s32 i2c_smbus_write_byte(struct i2c_client *client, u8 value);
s32 i2c_smbus_read_byte_data(struct i2c_client *client, u8 command);
s32 i2c_smbus_write_byte_data(struct i2c_client *client, u8 command, u8 value);
s32 i2c_smbus_read_word_data(struct i2c_client *client, u8 command);
s32 i2c_smbus_write_word_data(struct i2c_client *client, u8 command, u16 value);
s32 i2c_smbus_read_block_data(struct i2c_client *client, u8 command, u8 *values);
s32 i2c_smbus_write_block_data(struct i2c_client *client, u8 command, u8 length, const u8 *values);
s32 i2c_smbus_read_i2c_block_data(struct i2c_client *client, u8 command, u8 length, u8 *values);
s32 i2c_smbus_write_i2c_block_data(struct i2c_client *client, u8 command, u8 length, const u8 *values);
```

以下函数之前被从i2c-core中移除，因为它们没有用户，但如果需要的话以后可能会重新添加：

```
s32 i2c_smbus_write_quick(struct i2c_client *client, u8 value);
s32 i2c_smbus_process_call(struct i2c_client *client, u8 command, u16 value);
s32 i2c_smbus_block_process_call(struct i2c_client *client, u8 command, u8 length, u8 *values);
```

所有这些事务在失败时返回一个负的errno值。“写”事务在成功时返回0；“读”事务返回读取的值，除了块事务，它们返回读取值的数量。块缓冲区的长度不必超过32字节。

你可以阅读文件`smbus-protocol.rst`来获取更多关于实际SMBus协议的信息。

通用函数
========================

下面是所有未提及过的通用函数列表：

```
/* 对于特定适配器返回其适配器编号 */
int i2c_adapter_id(struct i2c_adapter *adap);
```
