SPDX 许可证标识符: GPL-2.0

=====================================================
sysfs - 用于导出内核对象的文件系统
=====================================================

Patrick Mochel <mochel@osdl.org>

Mike Murphy <mamurph@cs.clemson.edu>

:修订日期: 2011年8月16日
:原始日期: 2003年1月10日

它是什么
~~~~~~~~~~

sysfs 是一个基于 RAM 的文件系统，最初基于 ramfs。它提供了一种将内核数据结构、其属性以及它们之间的链接导出到用户空间的方法。
sysfs 本质上与 kobject 基础架构紧密相关。请阅读 `Documentation/core-api/kobject.rst` 获取更多关于 kobject 接口的信息。

使用 sysfs
~~~~~~~~~~~

如果定义了 CONFIG_SYSFS，则 sysfs 总是被编译进内核。你可以通过以下命令来挂载它：

```
mount -t sysfs sysfs /sys
```

目录创建
~~~~~~~~~~~~~~~~~~

对于每个注册到系统的 kobject，都会在 sysfs 中为其创建一个目录。该目录作为 kobject 父对象的子目录，向用户空间表达内部对象层次结构。sysfs 中的顶级目录代表对象层次结构的共同祖先；即这些对象所属的子系统。
sysfs 内部在与目录关联的 kernfs_node 对象中存储指向实现该目录的 kobject 的指针。在过去，此 kobject 指针曾被 sysfs 用于在文件打开或关闭时直接对 kobject 进行引用计数。
在当前的 sysfs 实现中，kobject 的引用计数仅由函数 sysfs_schedule_callback() 直接修改。

属性
~~~~~~~~~~

属性可以以普通文件的形式在文件系统中为 kobject 导出。sysfs 将文件 I/O 操作转发到为这些属性定义的方法，从而提供读写内核属性的方法。
属性应为 ASCII 文本文件，最好每个文件只包含一个值。虽然注意到在一个文件中只包含一个值可能不是最高效的，但社会上接受的是表达相同类型的值数组。
混合类型、表示多行数据和进行花哨的数据格式化是极其不受欢迎的。这样做可能会使你公开受到羞辱，并且你的代码可能在没有通知的情况下被重写。
属性定义如下：

```c
struct attribute {
    char                    *name;
    struct module           *owner;
    umode_t                 mode;
};

int sysfs_create_file(struct kobject *kobj, const struct attribute *attr);
void sysfs_remove_file(struct kobject *kobj, const struct attribute *attr);
```

一个裸属性没有任何读取或写入属性值的方法。子系统被鼓励定义自己的属性结构，并为特定对象类型添加和移除属性的包装函数。
例如，驱动模型定义了 `struct device_attribute` 如下：

```c
struct device_attribute {
    struct attribute        attr;
    ssize_t (*show)(struct device *dev, struct device_attribute *attr, char *buf);
    ssize_t (*store)(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);
};

int device_create_file(struct device *, const struct device_attribute *);
void device_remove_file(struct device *, const struct device_attribute *);
```

它还定义了一个用于定义设备属性的帮助宏：

```c
#define DEVICE_ATTR(_name, _mode, _show, _store) \
struct device_attribute dev_attr_##_name = __ATTR(_name, _mode, _show, _store)
```

例如，声明：

```c
static DEVICE_ATTR(foo, S_IWUSR | S_IRUGO, show_foo, store_foo);
```

等同于：

```c
static struct device_attribute dev_attr_foo = {
    .attr = {
        .name = "foo",
        .mode = S_IWUSR | S_IRUGO,
    },
    .show = show_foo,
    .store = store_foo,
};
```

请注意，在 `include/linux/kernel.h` 中提到，“OTHER_WRITABLE？通常认为这是一个坏主意。”因此尝试将 sysfs 文件设置为对所有人可写的模式将会失败，并会退回到“其他人”模式下的只读（RO）模式。
对于常见的用例，`sysfs.h` 提供了一些方便的宏来简化属性定义，并使代码更简洁和易读。上述情况可以简化为：

```c
static struct device_attribute dev_attr_foo = __ATTR_RW(foo);
```

可用的帮助宏列表如下：

- `__ATTR_RO(name)`：假设默认的 `name_show` 方法，并设置权限模式为 0444
- `__ATTR_WO(name)`：假设只有 `name_store` 方法，并限制为仅 root 可写权限（模式 0200）
- `__ATTR_RO_MODE(name, mode)`：用于更严格的只读访问；目前唯一用例是 EFI 系统资源表（见 `drivers/firmware/efi/esrt.c`）
- `__ATTR_RW(name)`：假设默认的 `name_show` 和 `name_store` 方法，并设置权限模式为 0644
- `__ATTR_NULL`：将名称设置为 NULL，并用作列表的结束标志（见 `kernel/workqueue.c`）

子系统特定的回调函数
~~~~~~~~~~~~~~~~~~~~~~~~

当一个子系统定义了一种新的属性类型时，它必须实现一组 sysfs 操作来转发读取和写入调用到属性所有者的 `show` 和 `store` 方法：

```c
struct sysfs_ops {
    ssize_t (*show)(struct kobject *, struct attribute *, char *);
    ssize_t (*store)(struct kobject *, struct attribute *, const char *, size_t);
};
```

[ 子系统应该已经定义了一个 `struct kobj_type` 作为此类的描述符，其中存储了 `sysfs_ops` 指针。更多信息请参阅 kobject 文档。]

当文件被读取或写入时，sysfs 会调用相应的方法。该方法然后将通用的 `struct kobject` 和 `struct attribute` 指针转换为相应的指针类型，并调用关联的方法。例如：

```c
#define to_dev_attr(_attr) container_of(_attr, struct device_attribute, attr)

static ssize_t dev_attr_show(struct kobject *kobj, struct attribute *attr, char *buf)
{
    struct device_attribute *dev_attr = to_dev_attr(attr);
    struct device *dev = kobj_to_dev(kobj);
    ssize_t ret = -EIO;

    if (dev_attr->show)
        ret = dev_attr->show(dev, dev_attr, buf);
    if (ret >= (ssize_t)PAGE_SIZE) {
        printk(KERN_ERR "dev_attr_show: %pS returned bad count\n", dev_attr->show);
    }
    return ret;
}
```

读取/写入属性数据
~~~~~~~~~~~~~~~~~~~~~~~~

为了读取或写入属性，在声明属性时必须指定 `show()` 或 `store()` 方法。这些方法类型的定义应尽可能简单，类似于设备属性的方法定义：

```c
ssize_t (*show)(struct device *dev, struct device_attribute *attr, char *buf);
ssize_t (*store)(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);
```

也就是说，它们应该只接受一个对象、一个属性和一个缓冲区作为参数。sysfs 分配一个大小为 `PAGE_SIZE` 的缓冲区，并将其传递给方法。sysfs 在每次读取或写入时恰好调用一次该方法。这迫使方法实现遵循以下行为：

- 在 `read(2)` 时，`show()` 方法应该填满整个缓冲区。请注意，一个属性通常只导出一个值或一系列相似的值，因此这不应该很昂贵。这允许用户空间任意进行部分读取和在整个文件中前进查找。如果用户空间回退到零位置或使用带有偏移量 '0' 的 `pread(2)`，`show()` 方法将再次被调用并重新填充缓冲区。
- 在 `write(2)` 时，sysfs 期望在第一次写入时传递整个缓冲区。sysfs 然后将整个缓冲区传递给 `store()` 方法。在存储时会在数据后面添加终止的空字符。这使得像 `sysfs_streq()` 这样的函数可以安全使用。在写入 sysfs 文件时，用户空间进程应首先读取整个文件，修改要更改的值，然后将整个缓冲区写回。
属性方法实现应在读取和写入值时操作相同的缓冲区

其他注意事项：

- 写入操作会使 show() 方法重新准备，无论当前文件位置如何
- 缓冲区的长度总是 PAGE_SIZE 字节。在 x86 平台上，这是 4096 字节
- show() 方法应返回打印到缓冲区中的字节数
- show() 在格式化要返回给用户空间的值时，只能使用 sysfs_emit() 或 sysfs_emit_at()
- store() 应返回从缓冲区中使用的字节数。如果整个缓冲区已被使用，则直接返回 count 参数
- show() 和 store() 始终可以返回错误。如果遇到无效值，请确保返回错误
- 传递给方法的对象将通过 sysfs 引用计数其嵌入对象来固定在内存中。然而，该对象所表示的实际实体（例如设备）可能并不存在。如有必要，请确保有检查方法

一个非常简单的（且天真的）设备属性实现如下：

```c
static ssize_t show_name(struct device *dev, struct device_attribute *attr, char *buf)
{
    return sysfs_emit(buf, "%s\n", dev->name);
}

static ssize_t store_name(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    snprintf(dev->name, sizeof(dev->.name), "%.*s",
             (int)min(count, sizeof(dev->name) - 1), buf);
    return count;
}

static DEVICE_ATTR(name, S_IRUGO, show_name, store_name);
```

（请注意，实际实现不允许用户空间设置设备名称。）

顶级目录布局
~~~~~~~~~~~~~~

sysfs 目录结构揭示了内核数据结构之间的关系
顶层 sysfs 目录如下所示：

```
block/
bus/
class/
dev/
devices/
firmware/
fs/
hypervisor/
kernel/
module/
net/
power/
```

`devices/` 包含设备树的文件系统表示。它直接映射到内部内核设备树，后者是一个 `struct device` 的层次结构。
`bus/` 包含内核中各种总线类型的平面目录布局。每个总线的目录包含两个子目录：

- `devices/`
- `drivers/`

`devices/` 包含系统中发现的每个设备的符号链接，这些链接指向根目录下的设备目录。
`drivers/` 包含该特定总线上加载的每个设备驱动程序的一个目录（假设驱动程序不跨越多个总线类型）。
`fs/` 包含一些文件系统的目录。目前，每个希望导出属性的文件系统都必须在 `fs/` 下创建自己的层次结构（参见 `./fuse.rst` 以获取示例）。
`module/` 包含所有已加载系统模块的参数值和状态信息，包括内置模块和可加载模块。
`dev/` 包含两个目录：`char/` 和 `block/`。在这两个目录中，有名为 `<major>:<minor>` 的符号链接。这些符号链接指向给定设备的 `sysfs` 目录。`/sys/dev` 提供了一种快速查找从 `stat(2)` 操作结果获取的设备 `sysfs` 接口的方法。

关于驱动模型特定功能的更多信息可以在 `Documentation/driver-api/driver-model/` 中找到。
待办事项：完成这一部分。

当前接口
~~~~~~~~

以下接口层当前存在于 `sysfs` 中：
设备（`include/linux/device.h`）
--------------------------------
结构：

```c
struct device_attribute {
    struct attribute attr;
    ssize_t (*show)(struct device *dev, struct device_attribute *attr, char *buf);
    ssize_t (*store)(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);
};
```

声明：

```c
DEVICE_ATTR(_name, _mode, _show, _store);
```

创建/移除：

```c
int device_create_file(struct device *dev, const struct device_attribute *attr);
void device_remove_file(struct device *dev, const struct device_attribute *attr);
```

总线驱动程序（`include/linux/device.h`）
-----------------------------------------
结构：

```c
struct bus_attribute {
    struct attribute attr;
    ssize_t (*show)(const struct bus_type *, char *buf);
    ssize_t (*store)(const struct bus_type *, const char *buf, size_t count);
};
```

声明：

```c
static BUS_ATTR_RW(name);
static BUS_ATTR_RO(name);
static BUS_ATTR_WO(name);
```

创建/移除：

```c
int bus_create_file(struct bus_type *, struct bus_attribute *);
void bus_remove_file(struct bus_type *, struct bus_attribute *);
```

设备驱动程序（`include/linux/device.h`）
---------------------------------------
结构：

```c
struct driver_attribute {
    struct attribute attr;
    ssize_t (*show)(struct device_driver *, char *buf);
    ssize_t (*store)(struct device_driver *, const char *buf, size_t count);
};
```

声明：

```c
DRIVER_ATTR_RO(_name)
DRIVER_ATTR_RW(_name)
```

创建/移除：

```c
int driver_create_file(struct device_driver *, const struct driver_attribute *);
void driver_remove_file(struct device_driver *, const struct driver_attribute *);
```

文档
~~~~~~~~~~~~~
`sysfs` 目录结构及其每个目录中的属性定义了内核与用户空间之间的 ABI。对于任何 ABI 来说，保持这个 ABI 稳定并妥善记录是非常重要的。所有新的 `sysfs` 属性必须在 `Documentation/ABI` 中进行记录。更多信息请参阅 `Documentation/ABI/README`。
