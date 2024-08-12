### 触发器

#### 结构体和函数

* `struct iio_trigger` — 工业I/O触发设备
* `:c:func:'devm_iio_trigger_alloc` — 资源管理的 `iio_trigger_alloc`
* `:c:func:'devm_iio_trigger_register` — 资源管理的 `iio_trigger_register` 和 `iio_trigger_unregister`
* `:c:func:'iio_trigger_validate_own_device` — 检查一个触发器和I/O设备是否属于同一个设备

在许多情况下，驱动程序能够根据外部事件（触发器）而不是周期性地轮询来捕获数据是非常有用的。一个I/O触发器可以由一个同时拥有基于硬件生成事件（例如数据就绪或阈值超过）的I/O设备的设备驱动提供；或者由一个独立中断源（例如连接到某个外部系统的GPIO线、定时器中断或用户空间写入sysfs中的特定文件）提供的独立驱动程序提供。一个触发器可以为多个传感器启动数据捕获，并且它可能与传感器本身完全无关。

### I/O触发器的sysfs接口

sysfs中有两个位置与触发器相关：

* `/sys/bus/iio/devices/trigger{Y}/*`：一旦I/O触发器注册到I/O核心中，就会创建这个文件，对应索引为Y的触发器。
因为不同类型的触发器差异很大，这里只有少数几个标准属性可以描述：

  * `name`，触发器名称，稍后可用于与设备关联
* `sampling_frequency`，一些基于定时器的触发器使用此属性指定触发调用的频率
* `/sys/bus/iio/devices/iio:device{X}/trigger/*`：一旦设备支持触发缓冲区，就会创建这个目录。我们可以通过将触发器的名称写入`current_trigger`文件来将触发器与我们的设备关联起来。

### I/O触发器设置

让我们来看一个简单的例子，了解如何设置一个触发器以供驱动程序使用：

```c
struct iio_trigger_ops trigger_ops = {
    .set_trigger_state = sample_trigger_state,
    .validate_device = sample_validate_device,
};

struct iio_trigger *trig;

// 首先，为我们的触发器分配内存
trig = iio_trigger_alloc(dev, "trig-%s-%d", name, idx);

// 设置触发器操作字段
trig->ops = &trigger_ops;

// 现在将触发器注册到I/O核心
iio_trigger_register(trig);
```

### I/O触发器操作

* `struct iio_trigger_ops` — I/O触发器的操作结构体
请注意，触发器有一组与其关联的操作：

* `set_trigger_state`，按需开关触发器
* `validate_device`，当当前触发器更改时验证设备

### 更多细节

请参阅：
- `include/linux/iio/trigger.h`
- `drivers/iio/industrialio-trigger.c` （导出文档）
