平台设备和驱动程序
============================

请参阅 `<linux/platform_device.h>` 以获取与平台总线相关的驱动程序模型接口：`platform_device` 和 `platform_driver`。这种伪总线用于连接那些基础设施最少的总线上的设备，例如用于集成外围设备到许多片上系统处理器中的总线，或者某些“传统”的PC互连；与像PCI或USB这样的大型正式规范的总线相反。
平台设备
~~~~~~~~~~
平台设备通常是系统中作为独立实体出现的设备。这包括传统的基于端口的设备和到外围总线的主机桥接器，以及大多数集成到片上系统平台的控制器。它们通常具有的共同特点是能够直接从CPU总线进行寻址。很少情况下，一个`platform_device`可能会通过某种其他类型的总线段连接；但其寄存器仍然可以直接寻址。

平台设备被赋予一个名称，用于驱动绑定，并且有一系列资源列表，如地址和中断请求（IRQs）：

```c
struct platform_device {
    const char    *name;
    u32           id;
    struct device dev;
    u32           num_resources;
    struct resource *resource;
};
```

平台驱动程序
~~~~~~~~~~
平台驱动程序遵循标准驱动程序模型约定，在该模型中，发现/枚举由驱动程序外部处理，而驱动程序提供`probe()`和`remove()`方法。它们使用标准约定支持电源管理和关机通知：

```c
struct platform_driver {
    int (*probe)(struct platform_device *);
    void (*remove)(struct platform_device *);
    void (*shutdown)(struct platform_device *);
    int (*suspend)(struct platform_device *, pm_message_t state);
    int (*resume)(struct platform_device *);
    struct device_driver driver;
    const struct platform_device_id *id_table;
    bool prevent_deferred_probe;
    bool driver_managed_dma;
};
```

需要注意的是，`probe()`通常应该验证指定的设备硬件确实存在；有时平台设置代码不能确定这一点。探测可以使用设备资源，包括时钟，以及设备的`platform_data`。

平台驱动程序以常规方式注册自己：

```c
int platform_driver_register(struct platform_driver *drv);
```

或者，在已知设备不可热插拔的情况下，为了减少驱动程序运行时内存占用，可以在初始化部分放置`probe()`例程：

```c
int platform_driver_probe(struct platform_driver *drv,
                          int (*probe)(struct platform_device *));
```

内核模块可以由多个平台驱动程序组成。平台核心提供了帮助程序来注册和注销一组驱动程序：

```c
int __platform_register_drivers(struct platform_driver * const *drivers,
                                unsigned int count, struct module *owner);
void platform_unregister_drivers(struct platform_driver * const *drivers,
                                 unsigned int count);
```

如果其中一个驱动程序未能注册，则所有注册到那一点的驱动程序将按相反顺序取消注册。注意有一个方便的宏来传递`THIS_MODULE`作为所有者参数：

```c
#define platform_register_drivers(drivers, count)
```

设备枚举
~~~~~~~~~~
一般来说，特定于平台的（并且往往是板级特定的）设置代码将注册平台设备：

```c
int platform_device_register(struct platform_device *pdev);
```

```c
int platform_add_devices(struct platform_device **pdevs, int ndev);
```

一般规则是仅注册实际存在的设备，但在某些情况下可能会注册额外的设备。例如，一个内核可能配置为与一个外部网络适配器一起工作，而这个适配器在所有板子上可能都没有安装，或者类似地与一个集成控制器一起工作，而一些板子可能没有将任何外围设备连接到该控制器。

在某些情况下，引导固件会导出描述给定板上安装的设备的表。如果没有这样的表，系统设置代码往往只能为特定的目标板构建内核。这种特定于板的内核在嵌入式系统开发中很常见。

在许多情况下，与平台设备关联的内存和IRQ资源不足以让设备的驱动程序正常工作。板级设置代码通常会使用设备的`platform_data`字段来提供额外的信息。

嵌入式系统经常需要一个或多个时钟为平台设备供电，这些时钟通常在真正需要之前保持关闭状态（以节省电力）。

系统设置也会将这些时钟与设备相关联，以便在需要时调用`clk_get(&pdev->dev, clock_name)`可以返回它们。

遗留驱动程序：设备探测
~~~~~~~~~~~~~~~~~~~~~~~~
有些驱动程序并未完全转换到驱动程序模型，因为它们承担了非驱动程序的角色：驱动程序注册自己的平台设备，而不是将其留给系统基础设施处理。这样的驱动程序无法热插拔或冷插拔，因为这些机制要求设备创建位于与驱动程序不同的系统组件中。

这样做的唯一“好”理由是为了处理较旧的系统设计，这些设计像最初的IBM PC一样依赖于错误率高的“硬件探测”模型来进行硬件配置。较新的系统已经很大程度上放弃了这一模型，转而支持动态配置的总线级支持（PCI、USB），或者由引导固件提供的设备表（例如x86上的PNPACPI）。关于什么可能在哪里有太多的冲突选项，即使操作系统做出有根据的猜测，也常常会出错。
这种类型的驱动程序是不被推荐的。如果你正在更新这样的驱动程序，
请尝试将设备枚举移动到一个更合适的位置，即驱动程序之外。这通常意味着清理工作，因为这类驱动程序往往已经具有“正常”模式，例如使用由即插即用（PNP）或平台设备设置创建的设备节点。
即便如此，还是有一些API来支持这些遗留驱动程序。除非是在处理不支持热插拔的驱动程序，否则避免使用这些调用：

```c
struct platform_device *platform_device_alloc(const char *name, int id);
```

你可以使用`platform_device_alloc()`动态分配一个设备，然后通过资源初始化它，并使用`platform_device_register()`进行注册。
更好的解决方案通常是：

```c
struct platform_device *platform_device_register_simple(const char *name, int id, struct resource *res, unsigned int nres);
```

你可以使用`platform_device_register_simple()`作为一步调用来分配并注册一个设备。

### 设备命名和驱动绑定

`platform_device.dev.bus_id` 是设备的标准名称。
它由两个组件构成：

    * `platform_device.name` ... 也用于驱动匹配
* `platform_device.id` ... 设备实例编号，或者"-1"表示只有一个
这些组件会被拼接起来，因此名称/编号为"serial"/0表示`bus_id`为"serial.0"，而"serial/3"表示`bus_id`为"serial.3"；两者都会使用名为"serial"的`platform_driver`。而"my_rtc"/-1则表示`bus_id`为"my_rtc"（没有实例编号），并使用名为"my_rtc"的`platform_driver`。

驱动绑定是由驱动核心自动完成的，在找到设备与驱动之间的匹配后会调用驱动的`probe()`函数。如果`probe()`成功，则驱动和设备像往常一样绑定。有三种不同的方式来找到这样的匹配：

    - 每当一个设备被注册时，都会检查该总线上的驱动以寻找匹配。平台设备应该在系统启动早期就进行注册。
- 当使用`platform_driver_register()`注册驱动时，会检查该总线上所有未绑定的设备以寻找匹配。驱动通常会在启动后期注册，或者通过模块加载。
- 使用`platform_driver_probe()`注册驱动就像使用`platform_driver_register()`一样，只是如果另一个设备注册了，这个驱动不会被再次探测。（这是可以接受的，因为此接口仅用于非热插拔设备。）

### 早期平台设备和驱动

早期平台接口在系统启动早期向平台设备驱动提供平台数据。这段代码建立在`early_param()`命令行解析的基础上，可以在非常早期执行。
示例：“earlyprintk”类的早期串行控制台分为六个步骤实现：

1. 注册早期平台设备数据
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
架构代码使用`early_platform_add_devices()`函数注册平台设备数据。在早期串行控制台的情况下，这应该是串行端口的硬件配置。此时注册的设备稍后将与早期平台驱动程序进行匹配。
2. 解析内核命令行
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
架构代码调用`parse_early_param()`来解析内核命令行。这将执行所有匹配的`early_param()`回调函数。用户指定的早期平台设备将在这一点上被注册。对于早期串行控制台的情况，用户可以在内核命令行中指定端口为"earlyprintk=serial.0"，其中"earlyprintk"是类别字符串，"serial"是平台驱动程序的名称，0是平台设备ID。如果ID为-1，则可以省略点号和ID。
3. 安装属于特定类别的早期平台驱动程序
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
架构代码可以选择性地强制注册属于特定类别的所有早期平台驱动程序，使用`early_platform_driver_register_all()`函数。从第2步来的用户指定设备优先于这些驱动程序。此步骤在串行驱动程序示例中被省略，因为除非用户已经在内核命令行指定了端口，否则早期串行驱动程序代码应被禁用。
4. 早期平台驱动程序注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
使用`early_platform_init()`编译进来的平台驱动程序会自动在第2或第3步中注册。串行驱动程序示例应该使用`early_platform_init("earlyprintk", &platform_driver)`。
5. 探测属于特定类别的早期平台驱动程序
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
架构代码调用`early_platform_driver_probe()`来匹配与特定类别相关联的已注册早期平台设备与已注册的早期平台驱动程序。匹配的设备将会被探测(`probed`)。
这个步骤可以在早期启动过程中的任何时间点执行。对于串行端口案例来说，尽可能早地执行可能比较好。
6. 在早期平台驱动程序探测函数内部
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序代码在早期启动时需要特别注意内存分配和中断注册等问题。`probe()`函数中的代码可以使用`is_early_platform_device()`来检查是否在早期平台设备或常规平台设备的时间被调用。早期串行驱动程序在这个点上执行`register_console()`。

更多信息，请参阅 `<linux/platform_device.h>`。
您没有提供需要翻译的文本。请提供需要翻译成中文的句子或词语。
