标题：将驱动程序移植到新驱动模型
=============================

作者：Patrick Mochel

日期：2003年1月7日


概述

请参阅 `Documentation/driver-api/driver-model/*.rst` 以了解各种驱动类型和概念的定义。
将设备驱动程序移植到新模型的大部分工作发生在总线驱动层。这是有意为之，目的是最小化对内核驱动程序的负面影响，并允许逐步过渡总线驱动程序。
简而言之，驱动模型由一组可以嵌入在更大的、特定于总线的对象中的对象组成。这些通用对象中的字段可以替代特定于总线的对象中的字段。
这些通用对象必须向驱动模型的核心注册。通过这样做，它们将通过 sysfs 文件系统导出。可以通过以下命令挂载 sysfs ：

    # mount -t sysfs sysfs /sys



过程

步骤 0: 阅读 include/linux/device.h 来了解对象和函数的定义。
步骤 1: 注册总线驱动
- 为总线驱动定义一个 `struct bus_type` ：

        struct bus_type pci_bus_type = {
              .name           = "pci",
        };

- 注册总线类型
这应该在总线类型的初始化函数中完成，通常是 `module_init()` 或等效函数：

        static int __init pci_driver_init(void)
        {
                return bus_register(&pci_bus_type);
        }

        subsys_initcall(pci_driver_init);

如果总线驱动可以编译为模块，则可以在适当时候取消注册总线类型：

         bus_unregister(&pci_bus_type);

- 导出总线类型供其他代码使用
其他代码可能需要引用总线类型，因此需要在一个共享头文件中声明它并导出符号。
从 include/linux/pci.h ：

  extern struct bus_type pci_bus_type;

从上述代码所在的文件中：

  EXPORT_SYMBOL(pci_bus_type);

- 这样做会导致总线在 `/sys/bus/pci/` 下显示，并有两个子目录：`devices` 和 `drivers` ：

        # tree -d /sys/bus/pci/
        /sys/bus/pci/
        |-- devices
        `-- drivers



步骤 2: 注册设备
`struct device` 表示单个设备。它主要包含描述该设备与其他实体关系的元数据。
在总线特定的设备类型中嵌入通用结构设备：

```c
struct pci_dev {
           ..
    struct device dev;            /* 通用设备接口 */
           ..
};
```

建议不要将通用设备作为 `struct` 中的第一个成员，以防止程序员无脑地在这两种对象类型之间进行类型转换。相反，应该创建宏或内联函数来进行类型转换：

```c
#define to_pci_dev(n) container_of(n, struct pci_dev, dev)

或者

static inline struct pci_dev * to_pci_dev(struct kobject * kobj)
{
    return container_of(kobj, struct pci_dev, dev);
}
```

这允许编译器验证操作的类型安全性（这是好的）。

- 在注册时初始化设备
当设备被发现或与总线类型注册时，总线驱动程序应初始化通用设备。最重要的初始化内容是 `bus_id`、`parent` 和 `bus` 字段。
- `bus_id` 是一个包含设备在总线上地址的 ASCII 字符串。这个字符串的格式取决于具体的总线类型。这是在 sysfs 中表示设备所必需的。
- `parent` 是设备的物理父设备。重要的是总线驱动程序必须正确设置该字段。
- 驱动模型维护了一个用于电源管理的设备有序列表。这个列表必须按顺序排列以保证设备在它们的物理父设备之前关闭，反之亦然。
- 这个列表的顺序由已注册设备的父设备决定。
- 此外，设备的 sysfs 目录的位置依赖于设备的父设备。sysfs 导出的目录结构反映了设备层次结构。准确地设置父设备可以确保 sysfs 准确地表示这个层次结构。
设备的总线字段是指向该设备所属总线类型的指针。此字段应设置为之前声明并初始化的总线类型。
可选地，总线驱动程序可以设置设备的名称和释放字段。
名称字段是一个描述设备的ASCII字符串，例如

     “ATI Technologies Inc Radeon QD”

释放字段是一个回调函数，当设备被移除且所有对该设备的引用都被释放时，由驱动模型核心调用。稍后将详细介绍这一点。
- 注册设备
一旦通用设备完成初始化，就可以通过以下方式注册到驱动模型核心：

       device_register(&dev->dev);

稍后可以通过以下方式取消注册：

       device_unregister(&dev->dev);

这应该发生在支持热插拔设备的总线上。
如果总线驱动程序取消注册一个设备，不应立即释放它。而应等待驱动模型核心调用设备的释放方法后，再释放特定于总线的对象
（可能有其他代码当前正在引用设备结构，在这种情况下释放设备是不礼貌的）
当设备注册后，会在sysfs中创建一个目录。
PCI树在sysfs中的样子如下：

    /sys/devices/pci0/
    |-- 00:00.0
    |-- 00:01.0
    |   `-- 01:00.0
    |-- 00:02.0
    |   `-- 02:1f.0
    |       `-- 03:00.0
    |-- 00:1e.0
    |   `-- 04:04.0
    |-- 00:1f.0
    |-- 00:1f.1
    |   |-- ide0
    |   |   |-- 0.0
    |   |   `-- 0.1
    |   `-- ide1
    |       `-- 1.0
    |-- 00:1f.2
    |-- 00:1f.3
    `-- 00:1f.5

同时，在总线的'devices'目录中会创建指向物理层次结构中设备目录的符号链接：

    /sys/bus/pci/devices/
    |-- 00:00.0 -> ../../../devices/pci0/00:00.0
    |-- 00:01.0 -> ../../../devices/pci0/00:01.0
    |-- 00:02.0 -> ../../../devices/pci0/00:02.0
    |-- 00:1e.0 -> ../../../devices/pci0/00:1e.0
    |-- 00:1f.0 -> ../../../devices/pci0/00:1f.0
    |-- 00:1f.1 -> ../../../devices/pci0/00:1f.1
    |-- 00:1f.2 -> ../../../devices/pci0/00:1f.2
    |-- 00:1f.3 -> ../../../devices/pci0/00:1f.3
    |-- 00:1f.5 -> ../../../devices/pci0/00:1f.5
    |-- 01:00.0 -> ../../../devices/pci0/00:01.0/01:00.0
    |-- 02:1f.0 -> ../../../devices/pci0/00:02.0/02:1f.0
    |-- 03:00.0 -> ../../../devices/pci0/00:02.0/02:1f.0/03:00.0
    `-- 04:04.0 -> ../../../devices/pci0/00:1e.0/04:04.0

步骤 3：注册驱动程序
`struct device_driver` 是一个简单的驱动结构，其中包含一组驱动模型核心可能调用的操作。
### 在特定于总线的驱动程序中嵌入结构体 `device_driver`

与设备类似，可以做如下定义：

```c
struct pci_driver {
           ..
    struct device_driver    driver;
};
```

### 初始化通用驱动结构

当驱动程序注册到总线上（例如执行 `pci_register_driver()`）时，初始化必要的字段，如名称和总线字段。

### 注册驱动程序

初始化通用驱动后，调用以下函数来向核心注册驱动程序：

```c
driver_register(&drv->driver);
```

当驱动程序从总线上注销时，通过以下方式从核心注销它：

```c
driver_unregister(&drv->driver);
```

请注意，这将阻塞直到所有对驱动程序的引用消失。通常情况下，不会有任何引用存在。

### Sysfs 表示

驱动程序通过其所在总线的 `drivers` 目录在 sysfs 中导出。例如：

```shell
/sys/bus/pci/drivers/
|-- 3c59x
|-- Ensoniq AudioPCI
|-- agpgart-amdk7
|-- e100
`-- serial
```

### 步骤 4：为驱动程序定义通用方法
### 结构体 `device_driver` 定义了一组操作，这些操作由驱动模型核心调用。这些操作大多数可能与总线已经为驱动程序定义的操作相似，但参数不同。

要强制总线上的每个驱动同时将其驱动转换为通用格式是困难且繁琐的。相反，总线驱动应该定义通用方法的单个实例，并将调用转发到特定于总线的驱动程序。例如：

```c
static int pci_device_remove(struct device *dev)
{
    struct pci_dev *pci_dev = to_pci_dev(dev);
    struct pci_driver *drv = pci_dev->driver;

    if (drv) {
        if (drv->remove)
            drv->remove(pci_dev);
        pci_dev->driver = NULL;
    }
    return 0;
}
```

在注册之前，应使用这些方法初始化通用驱动：

```c
/* 初始化通用驱动字段 */
drv->driver.name = drv->name;
drv->driver.bus = &pci_bus_type;
drv->driver.probe = pci_device_probe;
drv->driver.resume = pci_device_resume;
drv->driver.suspend = pci_device_suspend;
drv->driver.remove = pci_device_remove;

/* 向核心注册 */
driver_register(&drv->driver);
```

理想情况下，总线只应在字段未设置时初始化它们。这允许驱动程序实现自己的通用方法。

### 第五步：支持通用驱动绑定

该模型假设设备或驱动可以随时动态地与总线注册。当注册发生时，设备必须绑定到一个驱动，或者驱动必须绑定到所有它支持的设备。

一个驱动通常包含一个列表，列出它支持的设备ID。总线驱动比较这些ID与注册在其上的设备ID。

设备ID的格式和比较语义是特定于总线的，因此通用模型不尝试对它们进行泛化。相反，总线可以提供一个在 `struct bus_type` 中的方法来进行比较：

```c
int (*match)(struct device *dev, struct device_driver *drv);
```

`match` 应当在驱动支持设备时返回正值，在不支持时返回零。如果确定给定驱动是否支持设备是不可能的，它也可能返回错误码（例如 `-EPROBE_DEFER`）。

当设备注册时，会遍历总线的驱动列表，并对每个驱动调用 `bus->match()` 直到找到匹配。

当驱动注册时，会遍历总线的设备列表，并对每个尚未被驱动声称的设备调用 `bus->match()`。

当设备成功绑定到驱动时，`device->driver` 被设置，设备被添加到驱动的设备列表中，并在驱动的 sysfs 目录中创建指向设备物理目录的符号链接，如下所示：

```
/sys/bus/pci/drivers/
|-- 3c59x
|   `-- 00:0b.0 -> ../../../../devices/pci0/00:0b.0
|-- Ensoniq AudioPCI
|-- agpgart-amdk7
|   `-- 00:00.0 -> ../../../../devices/pci0/00:00.0
|-- e100
|   `-- 00:0c.0 -> ../../../../devices/pci0/00:0c.0
`-- serial
```

这种驱动绑定机制应该取代总线当前使用的现有驱动绑定机制。
步骤 6：提供热插拔回调功能
每当有设备通过驱动程序模型核心注册时，都会调用用户空间程序 `/sbin/hotplug` 来通知用户空间。
用户可以定义在设备插入或移除时执行的操作。
驱动程序模型核心通过环境变量向用户空间传递多个参数，包括：

- ACTION: 设置为 'add' 或 'remove'
- DEVPATH: 设置为设备在 sysfs 中的物理路径
总线驱动程序还可以提供额外的参数供用户空间使用。为此，总线必须在 `struct bus_type` 中实现 'hotplug' 方法：

        int (*hotplug) (struct device *dev, char **envp,
                         int num_envp, char *buffer, int buffer_size);

这会在执行 `/sbin/hotplug` 之前立即调用。

步骤 7：清理总线驱动程序
通用总线、设备和驱动程序结构提供了几个字段，这些字段可以替代总线驱动程序私有定义的那些字段。
- 设备列表
`struct bus_type` 包含一个所有已与该总线类型注册的设备的列表。这包括该总线类型所有实例上的所有设备。
可以移除总线内部使用的列表，转而使用这个列表。
核心提供了一个迭代器来访问这些设备：

```c
int bus_for_each_dev(struct bus_type *bus, struct device *start,
                     void *data, int (*fn)(struct device *, void *));
```

- **驱动程序列表**
`struct bus_type` 还包含一个所有已注册驱动程序的列表。总线驱动程序内部维护的一个驱动程序列表可能会被通用版本取代。
驱动程序可以像设备一样进行迭代：

```c
int bus_for_each_drv(struct bus_type *bus, struct device_driver *start,
                     void *data, int (*fn)(struct device_driver *, void *));
```

请参阅 `drivers/base/bus.c` 获取更多信息。

- **读写信号量（rwsem）**

`struct bus_type` 包含一个读写信号量（rwsem），用于保护对设备和驱动程序列表的所有核心访问。这个读写信号量可以在总线驱动程序内部使用，并且在访问总线维护的设备或驱动程序列表时应该使用它。

- **设备和驱动程序字段**
`struct device` 和 `struct device_driver` 中的一些字段与这些对象的总线特定表示中的字段重复。可以自由地移除这些总线特定的字段，转而使用通用的字段。不过需要注意的是，这可能意味着需要修复所有引用了总线特定字段的驱动程序（尽管这些更改通常只需要一行代码）。
