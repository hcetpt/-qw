### SPDX 许可证标识符: GPL-2.0

### 编写Virtio驱动程序

#### 简介
本文档旨在为需要编写新的Virtio驱动程序或理解现有驱动程序基本要素的驱动程序开发人员提供基本指导。有关Virtio的一般概述，请参阅 :ref:`Linux上的Virtio <virtio>`。

#### 驱动程序框架
最起码，一个Virtio驱动程序需要在Virtio总线上注册，并根据设备规范配置设备的virtqueues。驱动程序侧的virtqueue配置必须与设备中的virtqueue定义相匹配。一个基本的驱动程序骨架可能如下所示：

```c
#include <linux/virtio.h>
#include <linux/virtio_ids.h>
#include <linux/virtio_config.h>
#include <linux/module.h>

/* 设备私有数据（每个设备一份） */
struct virtio_dummy_dev {
    struct virtqueue *vq;
};

static void virtio_dummy_recv_cb(struct virtqueue *vq)
{
    struct virtio_dummy_dev *dev = vq->vdev->priv;
    char *buf;
    unsigned int len;

    while ((buf = virtqueue_get_buf(dev->vq, &len)) != NULL) {
        /* 处理接收到的数据 */
    }
}

static int virtio_dummy_probe(struct virtio_device *vdev)
{
    struct virtio_dummy_dev *dev = NULL;

    /* 初始化设备数据 */
    dev = kzalloc(sizeof(struct virtio_dummy_dev), GFP_KERNEL);
    if (!dev)
        return -ENOMEM;

    /* 设备有一个virtqueue */
    dev->vq = virtio_find_single_vq(vdev, virtio_dummy_recv_cb, "input");
    if (IS_ERR(dev->vq)) {
        kfree(dev);
        return PTR_ERR(dev->vq);
    }

    vdev->priv = dev;

    /* 从这一点开始，设备可以通知并接收回调 */
    virtio_device_ready(vdev);

    return 0;
}

static void virtio_dummy_remove(struct virtio_device *vdev)
{
    struct virtio_dummy_dev *dev = vdev->priv;

    /* 禁用vq中断：等同于 vdev->config->reset(vdev) */
    virtio_reset_device(vdev);

    /* 分离未使用的缓冲区 */
    while ((buf = virtqueue_detach_unused_buf(dev->vq)) != NULL) {
        kfree(buf);
    }

    /* 移除virtqueues */
    vdev->config->del_vqs(vdev);

    kfree(dev);
}

static const struct virtio_device_id id_table[] = {
    { VIRTIO_ID_DUMMY, VIRTIO_DEV_ANY_ID },
    { 0 },
};

static struct virtio_driver virtio_dummy_driver = {
    .driver.name =  KBUILD_MODNAME,
    .id_table =     id_table,
    .probe =        virtio_dummy_probe,
    .remove =       virtio_dummy_remove,
};

module_virtio_driver(virtio_dummy_driver);
MODULE_DEVICE_TABLE(virtio, id_table);
MODULE_DESCRIPTION("虚拟设备示例驱动程序");
MODULE_LICENSE("GPL");
```

这里的设备ID `VIRTIO_ID_DUMMY`是一个占位符，Virtio驱动程序应仅添加那些在规范中定义的设备。设备ID至少需要在添加到该文件之前在Virtio规范中保留。
如果你的驱动程序在其`init`和`exit`方法中不需要执行任何特殊操作，则可以使用module_virtio_driver()辅助函数来减少样板代码的数量。
`probe`方法在这种情况下执行最小的驱动设置（即为设备数据分配内存），并初始化virtqueue。virtio_device_ready()用于启用virtqueue，并通知设备驱动程序已准备好管理设备（"DRIVER_OK"）。无论如何，在`probe`返回后，virtqueues将由核心自动启用。

#### 发送和接收数据
上面的代码中的virtio_dummy_recv_cb()回调将在设备完成处理描述符或描述符链并通知驱动程序之后被触发，无论是读取还是写入。然而，这只是Virtio设备-驱动程序通信过程的后半部分，因为无论数据传输的方向如何，通信总是由驱动程序启动。
为了配置从驱动程序到设备的缓冲区传输，首先你需要将缓冲区（打包为`scatterlists`）添加到适当的virtqueue，可以使用virtqueue_add_inbuf()、virtqueue_add_outbuf()或virtqueue_add_sgs()之一，具体取决于你是否需要添加一个输入`scatterlist`（供设备填充）、一个输出`scatterlist`（供设备消费）或多`scatterlist`。然后，一旦virtqueue设置好，调用virtqueue_kick()发送一个通知，该通知将由实现设备的hypervisor处理：
```c
struct scatterlist sg[1];
sg_init_one(sg, buffer, BUFLEN);
virtqueue_add_inbuf(dev->vq, sg, 1, buffer, GFP_ATOMIC);
virtqueue_kick(dev->vq);
```
然后，在设备读取或写入由驱动程序准备的缓冲区并通知回驱动程序之后，驱动程序可以调用virtqueue_get_buf()来读取设备产生的数据（如果virtqueue是用输入缓冲区设置的）或者简单地回收这些缓冲区，如果它们已经被设备消费了：

#### 参考资料
_[1]_ Virtio 规范 v1.2: https://docs.oasis-open.org/virtio/virtio/v1.2/virtio-v1.2.html

同时请检查是否有更新版本的规范。
