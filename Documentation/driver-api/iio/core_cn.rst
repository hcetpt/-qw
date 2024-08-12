核心元素
=============

工业I/O核心提供了一个统一的框架，用于为多种类型的嵌入式传感器编写驱动程序，并为用户空间应用程序操纵传感器提供了标准接口。该实现可以在 :file:`drivers/iio/industrialio-*` 中找到。

工业I/O设备
----------------------

* struct iio_dev - 工业I/O设备
* iio_device_alloc() - 从驱动程序分配一个 :c:type:`iio_dev`
* iio_device_free() - 从驱动程序释放一个 :c:type:`iio_dev`
* iio_device_register() - 在工业I/O子系统中注册一个设备
* iio_device_unregister() - 从工业I/O子系统中注销一个设备

一个工业I/O设备通常对应一个硬件传感器，并为处理设备的驱动程序提供所需的所有信息。首先，让我们看一下嵌入在工业I/O设备中的功能，然后我们将展示设备驱动程序如何利用工业I/O设备。
用户空间应用程序可以通过两种方式与工业I/O驱动程序交互：
1. :file:`/sys/bus/iio/iio:device{X}/`，这代表一个硬件传感器，并将同一芯片的数据通道组合在一起
2. :file:`/dev/iio:device{X}`，用于缓冲数据传输和事件信息检索的字符设备节点接口
一个典型的工业I/O驱动程序会作为 :doc:`I2C <../i2c>` 或 :doc:`SPI <../spi>` 驱动程序注册，并创建两个例程：探测和移除
在探测时：

1. 调用 iio_device_alloc()，它为工业I/O设备分配内存
2. 使用特定于驱动程序的信息初始化工业I/O设备字段（例如 设备名称、设备通道）
3. 调用 iio_device_register()，这会将设备注册到工业I/O核心。调用此函数后，该设备就可以接受来自用户空间应用程序的请求了
在卸载时，我们按照与在`probe`中分配资源相反的顺序释放资源：

1. `iio_device_unregister()`，从IIO核心注销设备
2. `iio_device_free()`，释放为IIO设备分配的内存

IIO设备的sysfs接口
=================

属性是sysfs文件，用于暴露芯片信息，并允许应用程序设置各种配置参数。对于索引为X的设备，其属性可以在`/sys/bus/iio/iio:deviceX/`目录下找到。
常见的属性包括：

* `name`：物理芯片的描述
* `dev`：显示与`/dev/iio:deviceX`节点关联的主要：次要对
* `sampling_frequency_available`：设备可用的离散采样频率值集
* IIO设备的可用标准属性在Linux内核源码中的`Documentation/ABI/testing/sysfs-bus-iio`文件中有详细描述

IIO设备通道
=============

`struct iio_chan_spec` — 单个通道的规格

一个IIO设备通道代表一个数据通道的表现形式。一个IIO设备可以有一个或多个通道。例如：

* 温度传感器有一个表示温度测量值的通道
* 具有两个通道的光线传感器分别表示可见光和红外光谱的测量值
* 加速度计最多可能有3个通道，分别表示X、Y和Z轴上的加速度
IIO 通道由 `struct iio_chan_spec` 描述。
对于上面示例中的温度传感器的热敏电阻驱动程序，必须如下描述其通道：

```c
static const struct iio_chan_spec temp_channel[] = {
        {
            .type = IIO_TEMP,
            .info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED),
        },
};
```

暴露给用户空间的通道 sysfs 属性以位掩码的形式指定。根据它们共享的信息，属性可以设置在以下其中一个掩码中：

* **info_mask_separate**：这些属性将特定于此通道。
* **info_mask_shared_by_type**：这些属性被所有相同类型的通道共享。
* **info_mask_shared_by_dir**：这些属性被所有相同方向的通道共享。
* **info_mask_shared_by_all**：这些属性被所有通道共享。

当每种通道类型有多个数据通道时，我们有两种方式来区分它们：

* 将 `iio_chan_spec` 的 **.modified** 字段设置为 1。使用同一个 `iio_chan_spec` 结构的 **.channel2** 字段指定修饰符，用于指示通道的物理特性，如其方向或频谱响应。例如，一个光线传感器可以有两个通道，一个用于红外光，另一个用于红外和可见光。
* 将 `iio_chan_spec` 的 **.indexed** 字段设置为 1。在这种情况下，该通道只是具有由 **.channel** 字段指定的索引的另一实例。
下面是如何利用通道修饰符的一个例子：

```c
static const struct iio_chan_spec light_channels[] = {
           {
                   .type = IIO_INTENSITY,
                   .modified = 1,
                   .channel2 = IIO_MOD_LIGHT_IR,
                   .info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
                   .info_mask_shared = BIT(IIO_CHAN_INFO_SAMP_FREQ),
           },
           {
                   .type = IIO_INTENSITY,
                   .modified = 1,
                   .channel2 = IIO_MOD_LIGHT_BOTH,
                   .info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
                   .info_mask_shared = BIT(IIO_CHAN_INFO_SAMP_FREQ),
           },
           {
                   .type = IIO_LIGHT,
                   .info_mask_separate = BIT(IIO_CHAN_INFO_PROCESSED),
                   .info_mask_shared = BIT(IIO_CHAN_INFO_SAMP_FREQ),
           },
      }
```

此通道定义将生成两个独立的 sysfs 文件以检索原始数据：

* `/sys/bus/iio/iio:device{X}/in_intensity_ir_raw`
* `/sys/bus/iio/iio:device{X}/in_intensity_both_raw`

一个文件用于处理后的数据：

* `/sys/bus/iio/iio:device{X}/in_illuminance_input`

以及一个共享的 sysfs 文件用于采样频率：

* `/sys/bus/iio/iio:device{X}/sampling_frequency`

下面是如何利用通道索引的一个例子：

```c
static const struct iio_chan_spec light_channels[] = {
           {
                   .type = IIO_VOLTAGE,
		   .indexed = 1,
		   .channel = 0,
		   .info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	   },
           {
	           .type = IIO_VOLTAGE,
                   .indexed = 1,
                   .channel = 1,
                   .info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
           },
   }
```

这将生成两个独立的属性文件以检索原始数据：

* `/sys/bus/iio/devices/iio:device{X}/in_voltage0_raw`，代表通道 0 的电压测量
* `/sys/bus/iio/devices/iio:device{X}/in_voltage1_raw`，代表通道 1 的电压测量

更多详细信息，请参阅：
=================
.. kernel-doc:: include/linux/iio/iio.h
.. kernel-doc:: drivers/iio/industrialio-core.c
   :export:
