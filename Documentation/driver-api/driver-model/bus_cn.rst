### 总线类型

#### 定义
参见 `struct bus_type` 的内核文档。
```c
int bus_register(struct bus_type *bus);
```

#### 声明
内核中的每种总线类型（如 PCI、USB 等）都应声明一个该类型的静态对象。必须初始化 `name` 字段，并可选择性地初始化 `match` 回调函数：
```c
struct bus_type pci_bus_type = {
        .name       = "pci",
        .match      = pci_bus_match,
};
```
该结构体应在头文件中导出给驱动程序：
```c
extern struct bus_type pci_bus_type;
```

#### 注册
当总线驱动程序初始化时，会调用 `bus_register` 函数。这将初始化总线对象的其余字段，并将其插入到全局总线类型列表中。一旦总线对象注册后，其字段即可被总线驱动程序使用。

#### 回调

##### match()：将驱动程序与设备关联
设备 ID 结构的格式和比较语义本质上是总线特有的。驱动程序通常会声明它们支持的设备的设备 ID 数组，这些数组位于特定于总线的驱动结构中。
`match` 回调函数的目的在于让总线有机会根据比较驱动程序支持的设备 ID 和特定设备的设备 ID 来确定某个驱动是否支持该设备，同时不牺牲总线特性的功能或类型安全。
当驱动程序与总线注册时，会遍历总线的设备列表，并对每个未关联驱动程序的设备调用 `match` 回调函数。

##### 设备和驱动程序列表
设备和驱动程序列表旨在替代许多总线所维护的本地列表。它们分别是 `struct device` 和 `struct device_driver` 类型的列表。总线驱动程序可以自由使用这些列表，但可能需要转换为特定于总线的类型。
LDM 核心提供了用于遍历这些列表的帮助函数：
```c
int bus_for_each_dev(struct bus_type *bus, struct device *start,
                     void *data,
                     int (*fn)(struct device *, void *));

int bus_for_each_drv(struct bus_type *bus, struct device_driver *start,
                     void *data, int (*fn)(struct device_driver *, void *));
```
这些帮助函数遍历相应的列表，并为列表中的每个设备或驱动程序调用回调函数。所有列表访问都是通过获取总线锁（当前为读取锁）来同步的。在调用回调之前，列表中每个对象的引用计数都会增加；在获取下一个对象之后减少。调用回调时不持有锁。

#### sysfs
有一个顶层目录名为 `bus`。
每种总线在其目录下都有一个目录，以及两个默认目录：
```
/sys/bus/pci/
|-- devices
`-- drivers
```
已注册到总线的驱动程序会在总线的驱动程序目录下获得一个目录：
```
/sys/bus/pci/
|-- devices
`-- drivers
    |-- Intel ICH
    |-- Intel ICH Joystick
    |-- agpgart
    `-- e100
```
在发现的每种类型的总线设备在其设备目录中都会有一个指向物理层次结构中设备目录的符号链接：
```
/sys/bus/pci/
|-- devices
|   |-- 00:00.0 -> ../../../root/pci0/00:00.0
|   |-- 00:01.0 -> ../../../root/pci0/00:01.0
|   `-- 00:02.0 -> ../../../root/pci0/00:02.0
`-- drivers
```

#### 导出属性
```c
struct bus_attribute {
    struct attribute attr;
    ssize_t (*show)(const struct bus_type *, char *buf);
    ssize_t (*store)(const struct bus_type *, const char *buf, size_t count);
};
```
总线驱动程序可以使用类似于设备 `DEVICE_ATTR_RW` 宏的 `BUS_ATTR_RW` 宏来导出属性。例如，这样的定义：
```c
static BUS_ATTR_RW(debug);
```
等同于声明：
```c
static bus_attribute bus_attr_debug;
```
然后可以使用以下函数将属性添加到或从总线的 sysfs 目录中移除：
```c
int bus_create_file(struct bus_type *, struct bus_attribute *);
void bus_remove_file(struct bus_type *, struct bus_attribute *);
```
