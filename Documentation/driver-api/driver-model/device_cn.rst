### 基本设备结构

参见 `struct device` 的内核文档。

#### 编程接口
~~~
当总线驱动发现设备时，它使用以下方法将设备注册到核心中：

```c
int device_register(struct device *dev);
```

总线应该初始化以下字段：

- parent
- name
- bus_id
- bus

当设备的引用计数变为0时，该设备从核心中移除。可以使用以下方法调整引用计数：

```c
struct device *get_device(struct device *dev);
void put_device(struct device *dev);
```

如果引用不是已经为0（即设备正在被移除的过程中），`get_device()` 将返回传递给它的 `struct device` 指针。
驱动可以通过以下方式访问设备结构中的锁：

```c
void lock_device(struct device *dev);
void unlock_device(struct device *dev);
```
~~~

#### 属性
~~~
```c
struct device_attribute {
    struct attribute attr;
    ssize_t (*show)(struct device *dev, struct device_attribute *attr, char *buf);
    ssize_t (*store)(struct device *dev, struct device_attribute *attr, const char *buf, size_t count);
};
```
~~~

设备的属性可以通过sysfs由设备驱动导出。更多关于sysfs的信息，请参考文档 `Documentation/filesystems/sysfs.rst`。
如 `Documentation/core-api/kobject.rst` 中所述，必须在生成 KOBJ_ADD uevent 之前创建设备属性。唯一的方法是定义一个属性组。
属性使用一个叫做 `DEVICE_ATTR` 的宏声明：

```c
#define DEVICE_ATTR(name, mode, show, store)
```

示例：
~~~
```c
static DEVICE_ATTR(type, 0444, type_show, NULL);
static DEVICE_ATTR(power, 0644, power_show, power_store);
```
~~~
对于常见的权限值，提供了一些辅助宏，因此上述示例可以简化为：
~~~
```c
static DEVICE_ATTR_RO(type);
static DEVICE_ATTR_RW(power);
```
~~~
这声明了两个名为 `dev_attr_type` 和 `dev_attr_power` 的 `struct device_attribute` 类型的结构体。这些属性可以按如下方式组织为一组：

~~~
```c
static struct attribute *dev_attrs[] = {
    &dev_attr_type.attr,
    &dev_attr_power.attr,
    NULL,
};

static struct attribute_group dev_group = {
    .attrs = dev_attrs,
};

static const struct attribute_group *dev_groups[] = {
    &dev_group,
    NULL,
};
```
~~~
对于单个组的常见情况，提供了一个辅助宏，因此上述两个结构体可以这样声明：

~~~
```c
ATTRIBUTE_GROUPS(dev);
```
~~~
然后，可以通过设置 `struct device` 中的 `group` 指针来将这组属性与设备关联，在调用 `device_register()` 之前：

~~~
```c
dev->groups = dev_groups;
device_register(dev);
```
~~~
`device_register()` 函数会使用 `groups` 指针来创建设备属性，而 `device_unregister()` 函数则会使用这个指针来移除设备属性。

**警告**：虽然内核允许在任何时候对设备调用 `device_create_file()` 和 `device_remove_file()`，但用户空间对属性何时创建有严格期望。当内核中注册新设备时，会生成一个 uevent 来通知用户空间（例如 udev）有一个新设备可用。如果在设备注册后添加属性，则用户空间不会得到通知，并且用户空间将不知道新的属性。
这对于需要在驱动程序探测时为设备发布额外属性的设备驱动程序非常重要。如果设备驱动程序仅仅在其传递的设备结构上调用 `device_create_file()`，那么用户空间永远不会收到关于新属性的通知。
