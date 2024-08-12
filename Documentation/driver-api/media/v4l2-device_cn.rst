SPDX 许可证标识符: GPL-2.0

V4L2 设备实例
--------------

每个设备实例由一个 `struct v4l2_device` 表示。
非常简单的设备可以直接分配这个结构体，但大多数情况下，您会将此结构体嵌入到一个更大的结构体中。
您必须通过调用以下函数来注册设备实例：

	:c:func:`v4l2_device_register <v4l2_device_register>`
	(dev, :c:type:`v4l2_dev <v4l2_device>`)

注册将会初始化 :c:type:`v4l2_device` 结构体。如果
dev->driver_data 字段为 ``NULL``，它将会链接到
:c:type:`v4l2_dev <v4l2_device>` 参数。
希望与媒体设备框架集成的驱动程序需要手动设置
dev->driver_data 指向包含 `struct v4l2_device` 实例的驱动程序特定设备结构。
这是通过在注册 V4L2 设备实例之前调用 `dev_set_drvdata()` 实现的。
它们还必须设置 `struct v4l2_device` 的 mdev 字段指向一个正确初始化和注册的 :c:type:`media_device` 实例。
如果 :c:type:`v4l2_dev <v4l2_device>`\ ->name 为空，则会将其设置为从 dev 导出的值（确切地说是驱动程序名称后跟 bus_id）。
如果您在调用 :c:func:`v4l2_device_register` 之前设置它，则它将保持不变。
如果 dev 为 ``NULL``，则在调用
:c:func:`v4l2_device_register` 之前 **必须** 设置
:c:type:`v4l2_dev <v4l2_device>`\ ->name。
您可以使用 :c:func:`v4l2_device_set_name` 根据驱动程序名称和驱动程序全局的 atomic_t 实例设置名称。
这将生成类似 "ivtv0"、"ivtv1" 等名称。如果名称以数字结尾，则会在数字前插入破折号："cx18-0"、"cx18-1" 等。
此函数返回实例编号。
第一个 `dev` 参数通常是 `pci_dev`、`usb_interface` 或 `platform_device` 的 `struct device` 指针。
dev 为 ``NULL`` 的情况很少见，但在 ISA 设备或一个设备创建多个 PCI 设备的情况下会发生，
从而无法将 :c:type:`v4l2_dev <v4l2_device>` 关联到特定父级。
您还可以提供一个 `notify()` 回调函数，子设备可以调用它来通知您发生的事件。是否需要设置此回调取决于子设备。子设备支持的任何通知都必须在 `include/media/subdevice.h` 中的一个头文件中定义。
V4L2 设备通过调用以下函数进行注销：

    :c:func:`v4l2_device_unregister` 
    (:c:type:`v4l2_dev <v4l2_device>`)

如果 `dev->driver_data` 字段指向 `v4l2_dev <v4l2_device>` 类型，则会将其重置为 `NULL`。注销还会自动从设备中注销所有子设备。
如果您有一个热插拔设备（例如 USB 设备），当发生断开连接时，父设备将变为无效。由于 `v4l2_device` 包含指向该父设备的指针，因此也必须将其清空以标记父设备已消失。为此，请调用：

    :c:func:`v4l2_device_disconnect`
    (:c:type:`v4l2_dev <v4l2_device>`)

这不会注销子设备，因此您仍然需要调用 :c:func:`v4l2_device_unregister` 函数来完成注销。如果您的驱动程序不是热插拔的，则无需调用 :c:func:`v4l2_device_disconnect`。
有时您需要遍历由特定驱动程序注册的所有设备。通常，当多个设备驱动程序使用相同的硬件时会出现这种情况。例如，`ivtvfb` 驱动程序是一个使用 `ivtv` 硬件的帧缓冲区驱动程序。对于 ALSA 驱动程序来说也是如此。
您可以按照以下方式遍历所有已注册的设备：

```c
static int callback(struct device *dev, void *p)
{
    struct v4l2_device *v4l2_dev = dev_get_drvdata(dev);

    /* 测试此设备是否已经初始化 */
    if (v4l2_dev == NULL)
        return 0;
    ..
    return 0;
}

int iterate(void *p)
{
    struct device_driver *drv;
    int err;

    /* 在 PCI 总线上找到名为 'ivtv' 的驱动
    pci_bus_type 是一个全局变量。对于 USB 总线请使用 usb_bus_type。 */
    drv = driver_find("ivtv", &pci_bus_type);
    /* 遍历所有 ivtv 设备实例 */
    err = driver_for_each_device(drv, NULL, p, callback);
    put_driver(drv);
    return err;
}
```

有时您需要维护一个正在运行的设备实例计数器。这通常用于将设备实例映射到模块选项数组的索引。
推荐的方法如下：

```c
static atomic_t drv_instance = ATOMIC_INIT(0);

static int drv_probe(struct pci_dev *pdev, const struct pci_device_id *pci_id)
{
    ..
```
```state->instance = atomic_inc_return(&drv_instance) - 1;```

如果你有多个设备节点，那么对于热插拔设备来说，在何时安全地取消注册 `v4l2_device` 类型可能会变得困难。为此，`v4l2_device` 类型提供了引用计数支持。每当调用 `video_register_device` 函数时，引用计数会增加；每当一个设备节点被释放时，引用计数会减少。当引用计数达到零时，将调用 `v4l2_device` 的 release() 回调函数。你可以在那里执行最终的清理工作。

如果有其他设备节点（例如 ALSA）创建，你也可以通过手动调用来增加和减少引用计数：

    `v4l2_device_get` (`v4l2_dev <v4l2_device>` 类型)
或：

    `v4l2_device_put` (`v4l2_dev <v4l2_device>` 类型)

由于初始引用计数为 1，因此还需要在“断开连接”(`disconnect()`) 回调（对于 USB 设备）或“移除”(`remove()`) 回调（例如 PCI 设备）中调用 `v4l2_device_put`，否则引用计数永远不会达到 0。

`v4l2_device` 函数和数据结构
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. kernel-doc:: include/media/v4l2-device.h
```

这段代码和文档说明主要讲述了 Linux 内核中 Video for Linux 2 (V4L2) 子系统中的 `v4l2_device` 类型如何使用引用计数来管理设备节点的注册与注销过程。这有助于确保在所有相关设备节点都被释放后，才能安全地进行最终的清理操作。
