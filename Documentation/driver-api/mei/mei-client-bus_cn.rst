### SPDX 许可证标识符: GPL-2.0

==============================================
英特尔® 管理引擎 (ME) 客户端总线 API
==============================================

### 理由
=========

MEI 字符设备对于专用应用程序从用户空间发送和接收数据到英特尔 ME 中的许多固件设备非常有用。然而，对于某些 ME 功能来说，利用现有的软件堆栈并通过现有的内核子系统进行暴露是有意义的。为了无缝地集成到内核设备驱动模型中，我们在 MEI 驱动程序之上添加了内核虚拟总线抽象。这允许为各种 MEI 特性实现独立的 Linux 内核驱动程序，它们位于各自的子系统中。现有设备驱动程序甚至可以通过在现有代码中添加一个 MEI 客户端 (CL) 总线层来重用。

### MEI CL 总线 API
====================

一个 MEI 客户端驱动程序的实现与任何其他现有的基于总线的设备驱动程序非常相似。驱动程序通过 `struct mei_cl_driver` 结构注册为一个 MEI CL 总线驱动程序，该结构定义在 :file:`include/linux/mei_cl_bus.c` 文件中。

```C
struct mei_cl_driver {
        struct device_driver driver;
        const char *name;

        const struct mei_cl_device_id *id_table;

        int (*probe)(struct mei_cl_device *dev, const struct mei_cl_id *id);
        int (*remove)(struct mei_cl_device *dev);
};
```

在 :file:`include/linux/mod_devicetable.h` 中定义的 `mei_cl_device_id` 结构允许驱动程序根据设备名称绑定自身。
```C
struct mei_cl_device_id {
        char name[MEI_CL_NAME_SIZE];
        uuid_le uuid;
        __u8    version;
        kernel_ulong_t driver_info;
};
```

要实际在 ME 客户端总线上注册一个驱动程序，必须调用 :c:func:`mei_cl_add_driver` API。这通常在模块初始化时调用。
一旦驱动程序注册并绑定到设备，驱动程序通常会尝试通过此总线进行一些输入/输出操作，这应该通过 :c:func:`mei_cl_send` 和 :c:func:`mei_cl_recv` 函数完成。更多详细信息请参阅 :ref:`api` 部分。
为了使驱动程序能够接收到待处理流量或事件的通知，驱动程序应该通过 :c:func:`mei_cl_devev_register_rx_cb` 和 :c:func:`mei_cldev_register_notify_cb` 函数注册回调。

#### API:
----
.. kernel-doc:: drivers/misc/mei/bus.c
    :export: drivers/misc/mei/bus.c

### 示例
=======

作为一个理论示例，假设 ME 带有一个名为 "contact" 的 NFC IP。
这个设备的驱动程序初始化和退出例程看起来像这样：

```C
#define CONTACT_DRIVER_NAME "contact"

static struct mei_cl_device_id contact_mei_cl_tbl[] = {
        { CONTACT_DRIVER_NAME, },

        /* 必须是最后一个条目 */
        { }
};
MODULE_DEVICE_TABLE(mei_cl, contact_mei_cl_tbl);

static struct mei_cl_driver contact_driver = {
        .id_table = contact_mei_cl_tbl,
        .name = CONTACT_DRIVER_NAME,

        .probe = contact_probe,
        .remove = contact_remove,
};

static int contact_init(void)
{
        int r;

        r = mei_cl_driver_register(&contact_driver);
        if (r) {
                pr_err(CONTACT_DRIVER_NAME ": driver registration failed\n");
                return r;
        }

        return 0;
}

static void __exit contact_exit(void)
{
        mei_cl_driver_unregister(&contact_driver);
}

module_init(contact_init);
module_exit(contact_exit);
```

简化后的驱动程序探测例程将如下所示：

```C
int contact_probe(struct mei_cl_device *dev, struct mei_cl_device_id *id)
{
        [...]
        mei_cldev_enable(dev);

        mei_cldev_register_rx_cb(dev, contact_rx_cb);

        return 0;
}
```

在探测例程中，驱动程序首先启用 MEI 设备，然后注册一个接收处理器，这相当于注册一个线程化的中断处理器。
处理程序实现通常会调用 :c:func:`mei_cldev_recv` 并处理接收到的数据。
```c
#define MAX_PAYLOAD 128
#define HDR_SIZE 4
static void conntact_rx_cb(struct mei_cl_device *cldev)
{
        struct contact *c = mei_cldev_get_drvdata(cldev);
        unsigned char payload[MAX_PAYLOAD];
        ssize_t payload_sz;

        payload_sz = mei_cldev_recv(cldev, payload,  MAX_PAYLOAD);
        if (payload_sz < HDR_SIZE) {
                return;
        }

        c->process_rx(payload);

}
```

MEI 客户端总线驱动程序
======================
.. toctree::
   :maxdepth: 2

   hdcp
   nfc
```

请注意，上述代码中有一个小错误：`if (payload_sz < HDR_SIZE)` 应该使用 `payload_sz` 而不是 `reply_size`。此外，`conntact_rx_cb` 函数名似乎拼写有误，应该是 `contact_rx_cb`。如果需要，我可以提供修正后的代码。
```
