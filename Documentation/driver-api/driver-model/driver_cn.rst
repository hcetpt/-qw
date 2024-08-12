设备驱动程序
=============

请参阅 `struct device_driver` 的内核文档。
分配
~~~~~~~~~~

设备驱动程序是静态分配的结构。虽然一个系统中可能存在多个由驱动程序支持的设备，但 `struct device_driver` 表示的是整个驱动程序（而非特定的设备实例）。
初始化
~~~~~~~~~~~~~~

驱动程序必须至少初始化名称和总线字段。还应初始化 `devclass` 字段（当它可用时），以便在内部获得正确的链接。还应尽可能多地初始化回调函数，尽管每个回调都是可选的。
声明
~~~~~~~~~~~

如上所述，`struct device_driver` 对象是静态分配的。下面是 eepro100 驱动程序的一个示例声明。此声明仅为假设性的；它依赖于驱动程序完全转换为新模型的情况： 

```c
static struct device_driver eepro100_driver = {
         .name		= "eepro100",
         .bus		= &pci_bus_type,

         .probe		= eepro100_probe,
         .remove		= eepro100_remove,
         .suspend		= eepro100_suspend,
         .resume		= eepro100_resume,
  };
```

大多数驱动程序无法完全转换为新模型，因为它们所属的总线具有特定于总线的结构和特定于总线的字段，这些字段无法进行泛化处理。
最常见的例子就是设备ID结构。通常，驱动程序会定义一个支持的设备ID数组。这些结构的格式以及比较设备ID的语义是完全特定于总线的。将它们定义为特定于总线的实体会牺牲类型安全性，因此我们保留了特定于总线的结构。
特定于总线的驱动程序应该在其定义中包含一个通用的 `struct device_driver`。像这样：

```c
struct pci_driver {
         const struct pci_device_id *id_table;
         struct device_driver	  driver;
};
```

包含特定于总线字段的定义看起来像这样（再次使用 eepro100 驱动程序为例）：

```c
static struct pci_driver eepro100_driver = {
         .id_table       = eepro100_pci_tbl,
         .driver	       = {
		.name		= "eepro100",
		.bus		= &pci_bus_type,
		.probe		= eepro100_probe,
		.remove		= eepro100_remove,
		.suspend	= eepro100_suspend,
		.resume		= eepro100_resume,
         },
};
```

一些人可能会觉得嵌套结构初始化的语法有些笨拙甚至有点丑陋。到目前为止，这是我们找到的最好的实现方法。
注册
~~~~~~~~~~~~

```c
int driver_register(struct device_driver *drv);
```

驱动程序在启动时注册该结构。对于没有特定于总线字段的驱动程序（即没有特定于总线的驱动程序结构），它们可以使用 `driver_register` 并传递指向其 `struct device_driver` 对象的指针。
然而，大多数驱动程序将具有特定于总线的结构，并需要使用类似 `pci_driver_register` 的方式向总线注册。
重要的是，驱动程序应尽早注册其驱动程序结构。与核心的注册会初始化 `struct device_driver` 对象中的几个字段，包括引用计数和锁。这些字段被假定始终有效，并可能被设备模型核心或总线驱动程序使用。
过渡总线驱动程序
~~~~~~~~~~~~~~~~~~~~~~

通过定义包装函数，可以更轻松地过渡到新模型。驱动程序可以完全忽略通用结构，并让总线包装器填充字段。对于回调函数，总线可以定义通用回调函数，将调用转发给驱动程序的特定于总线的回调函数。
此解决方案仅打算作为临时措施。为了在驱动程序中获取类信息，无论如何都需要修改这些驱动程序。因为将驱动程序转换为新模型可以减少一些基础架构的复杂性和代码大小，因此建议在添加类信息时进行转换。

### 访问

一旦对象注册后，就可以访问该对象的通用字段，如锁和设备列表：

```c
int driver_for_each_dev(struct device_driver *drv, void *data,
			 int (*callback)(struct device *dev, void *data));
```

`devices`字段是一个已绑定到驱动程序的所有设备的列表。LDM核心提供了一个辅助函数来操作驱动程序控制的所有设备。这个辅助函数在每次节点访问时锁定驱动程序，并在访问每个设备时进行适当的引用计数。

### sysfs

当驱动程序注册时，在其总线目录下创建一个sysfs目录。在这个目录中，驱动程序可以向用户空间导出接口以全局控制驱动程序的操作；例如，在驱动程序中切换调试输出。

这个目录的一个未来特性将是“devices”目录。这个目录将包含指向它支持的设备目录的符号链接。

### 回调

```c
int	(*probe)	(struct device *dev);
```

`probe()`回调是在任务上下文中被调用的，此时总线的rwsem被锁定，并且驱动程序部分地与设备绑定。驱动程序通常使用`container_of()`将“dev”转换为总线特定类型，既在`probe()`中也用于其他例程。这种类型经常提供设备资源数据，如`pci_dev.resource[]`或`platform_device.resources`，这与`dev->platform_data`一起用于初始化驱动程序。

这个回调包含了将驱动程序绑定到特定设备的驱动程序特定逻辑。这包括验证设备是否存在、它是驱动程序可以处理的版本、是否可以分配并初始化驱动程序数据结构以及是否可以初始化任何硬件。

驱动程序通常使用`dev_set_drvdata()`存储其状态。

当驱动程序成功地将自身绑定到该设备后，`probe()`返回零，驱动模型代码将完成将驱动程序绑定到该设备的其余部分。

如果驱动程序没有绑定到此设备，则`probe()`可以返回负的errno值，在这种情况下，它应该释放所有分配的资源。

可选地，`probe()`可以返回`-EPROBE_DEFER`，如果驱动程序依赖于尚未可用的资源（例如，由尚未初始化的驱动程序提供的）。驱动程序核心将把设备放到延迟探查列表上，并稍后尝试再次调用它。如果驱动程序必须延迟，它应该尽早返回`-EPROBE_DEFER`，以减少需要撤销并在以后重新执行的设置工作的时间。
:: 
警告::
   - 如果`probe()`已经创建了子设备，则不应返回-EPROBE_DEFER，即使这些子设备随后在清理路径中被移除。如果在注册子设备后返回-EPROBE_DEFER，可能会导致对同一驱动程序的无限循环的`probe()`调用。

void	(*sync_state)	(struct device *dev);

`sync_state`仅针对每个设备调用一次。当该设备的所有消费者设备都已成功探测时会调用它。该设备的消费者列表是通过查看连接该设备与其消费者设备之间的设备链接来获取的。
首次尝试调用`sync_state()`是在`late_initcall_sync()`期间进行的，以便给固件和驱动程序足够的时间将设备相互链接起来。在首次尝试调用`sync_state()`时，如果该时刻该设备的所有消费者都已经成功探测，那么`sync_state()`会立即被调用。如果在首次尝试时该设备没有消费者，这也被视为“该设备的所有消费者都已经探测”，因此`sync_state()`也会立即被调用。
如果在首次尝试调用`sync_state()`时对于某个设备还有尚未成功探测的消费者，那么`sync_state()`的调用会被推迟，并且只在该设备的一个或多个消费者成功探测后重新尝试。如果在重新尝试时，驱动核心发现该设备还有一一个或多个消费者尚未探测，那么`sync_state()`的调用将再次被推迟。
使用`sync_state()`的一个典型场景是让内核干净地接管从引导加载程序管理的设备。例如，如果一个设备被引导加载程序开启并配置到特定的硬件状态，该设备的驱动可能需要保持该设备处于引导配置状态，直到该设备的所有消费者都已探测完毕。一旦所有消费者都已探测完毕，设备的驱动就可以同步设备的硬件状态以匹配所有消费者请求的聚合软件状态。这就是为什么这个函数叫做`sync_state()`。
虽然明显的可以从`sync_state()`中受益的资源包括像电压调节器这样的资源，`sync_state()`也可以用于像IOMMU这样复杂的资源。例如，具有多个消费者（其地址由IOMMU重映射的设备）的IOMMU可能需要保持它们的映射固定在引导配置（或者增加到引导配置），直到所有消费者都已探测。
虽然`sync_state()`的典型用途是让内核干净地接管从引导加载程序管理的设备，但`sync_state()`的使用并不局限于这种情况。在所有消费者探测完毕后采取行动有意义的情况下都可以使用它。

int 	(*remove)	(struct device *dev);

`remove`用于解除驱动与设备的绑定。这可能在设备物理上从系统移除、驱动模块正在卸载、重启序列中或其他情况下被调用。
由驱动确定设备是否存在。它应该释放为该设备分配的所有特定资源；即设备的`driver_data`字段中的任何内容。
如果设备仍然存在，应使设备静默并将其置于支持的低功耗状态。

int	(*suspend)	(struct device *dev, pm_message_t state);

`suspend`用于将设备置于低功耗状态。
```c
/* 
 * resume: 用于将设备从低功耗状态恢复
 */

ssize_t (*resume)(struct device *dev);

/*
 * 属性
 * ~~~~~~
 * 
 * 结构体 driver_attribute 定义如下：
 */
 
struct driver_attribute {
        struct attribute        attr;
        ssize_t (*show)(struct device_driver *driver, char *buf);
        ssize_t (*store)(struct device_driver *, const char *buf, size_t count);
};

/*
 * 设备驱动可以通过它们的 sysfs 目录导出属性。
 * 驱动可以使用 DRIVER_ATTR_RW 和 DRIVER_ATTR_RO 宏来声明属性，
 * 这些宏与 DEVICE_ATTR_RW 和 DEVICE_ATTR_RO 宏工作方式相同。
 * 示例：
 * 
 * DRIVER_ATTR_RW(debug);
 * 
 * 这等同于声明：
 * 
 * struct driver_attribute driver_attr_debug;
 * 
 * 然后可以使用以下函数来向驱动目录中添加或移除该属性：
 * 
 * int driver_create_file(struct device_driver *, const struct driver_attribute *);
 * void driver_remove_file(struct device_driver *, const struct driver_attribute *);
 */
```

以上是将原文翻译成中文的代码注释。
