SPDX 许可证标识符: GPL-2.0

视频设备的内部表示
=======================

实际的设备节点在 `/dev` 目录中是通过 `video_device` 结构体 (`v4l2-dev.h`) 创建的。这个结构体既可以动态分配，也可以嵌入到一个更大的结构体中。
要动态分配它，请使用 `video_device_alloc` 函数：

```c
struct video_device *vdev = video_device_alloc();

if (vdev == NULL)
    return -ENOMEM;

vdev->release = video_device_release;
```

如果你将它嵌入到一个更大的结构体中，那么你必须为 `release()` 回调设置你自己的函数：

```c
struct video_device *vdev = &my_vdev->vdev;

vdev->release = my_vdev_release;
```

`release()` 回调必须被设置，并且当最后一个视频设备用户退出时会被调用。
默认的 `video_device_release` 回调当前仅调用 `kfree` 来释放已分配的内存。
还有一个 `video_device_release_empty` 函数，它什么也不做（为空），如果结构体是嵌入式的，并且在释放时不需要做任何事情，则应使用此函数。
你还应该设置 `video_device` 的以下字段：

- `video_device`->v4l2_dev: 必须设置为父 `v4l2_device` 设备
- `video_device`->name: 设置为描述性和唯一的名称
- `video_device`->vfl_dir: 对于捕获设备将其设置为 `VFL_DIR_RX` (`VFL_DIR_RX` 的值为 0，因此这通常是默认值)，对于输出设备将其设置为 `VFL_DIR_TX`，对于内存到内存 (codec) 设备将其设置为 `VFL_DIR_M2M`
- `video_device`->fops: 设置为 `v4l2_file_operations` 结构体
- `video_device`->ioctl_ops: 如果你使用 `v4l2_ioctl_ops` 来简化 ioctl 的维护（强烈推荐使用这种方法，并且将来可能会成为强制要求！），则将其设置为你自己的 `v4l2_ioctl_ops` 结构体。`video_device`->vfl_type 和 `video_device`->vfl_dir 字段用于禁用与类型/方向组合不匹配的操作。例如，对于非 VBI 节点禁用 VBI 操作，对于捕获设备禁用输出操作。这使得可以为 VBI 和视频节点提供单一的 `v4l2_ioctl_ops` 结构体
- `video_device`->lock: 如果你想在驱动程序中处理所有锁定，则保留为 `NULL`。否则，为其提供一个指向 `mutex_lock` 结构体的指针，在调用 `video_device`->unlocked_ioctl 文件操作之前，该锁将由内核获取并在之后释放。有关更多详细信息，请参阅下一节。
- :c:type:`video_device`->queue: 指向与该设备节点相关的 `vb2_queue` 结构体的指针。
  如果 `queue` 不是 `NULL`，且 `queue->lock` 也不是 `NULL`，那么 `queue->lock` 将用于排队 ioctls（如 `VIDIOC_REQBUFS`、`CREATE_BUFS`、`QBUF`、`DQBUF`、`QUERYBUF`、`PREPARE_BUF`、`STREAMON` 和 `STREAMOFF`）而不是使用上面提到的锁。
  这样一来，:ref:`vb2 <vb2_framework>` 排队框架就不必等待其他 ioctl。此队列指针还被 :ref:`vb2 <vb2_framework>` 辅助函数用于检查排队所有权（即调用它的文件句柄是否有权执行操作）。
- :c:type:`video_device`->prio: 用于跟踪优先级。用于实现 `VIDIOC_G_PRIORITY` 和 `VIDIOC_S_PRIORITY`。
  如果留为 `NULL`，则会使用 :c:type:`v4l2_device` 中的 `struct v4l2_prio_state`。如果你希望为每个（组）设备节点设置单独的优先级状态，则可以将其指向你自己的 `struct v4l2_prio_state`。
- :c:type:`video_device`->dev_parent: 只有在使用 `NULL` 作为父 `device` 结构体注册了 `v4l2_device` 时才设置它。这种情况发生在单个硬件设备拥有多个共享同一 `v4l2_device` 核心的 PCI 设备的情况下。
  `cx88` 驱动程序就是一个例子：一个核心 `v4l2_device` 结构体，但它同时被一个原始视频 PCI 设备（cx8800）和一个 MPEG PCI 设备（cx8802）使用。由于 `v4l2_device` 不能同时关联到两个 PCI 设备，因此它被设置为没有父设备。但是，在初始化 `struct video_device` 时，你知道要使用哪个父 PCI 设备，因此将 `dev_device` 设置为正确的 PCI 设备。
  如果你使用了 :c:type:`v4l2_ioctl_ops`，则应在你的 :c:type:`v4l2_file_operations` 结构体中将 :c:type:`video_device`->unlocked_ioctl 设置为 :c:func:`video_ioctl2`。
  在某些情况下，你可能希望告诉内核忽略你在 :c:type:`v4l2_ioctl_ops` 中指定的某个函数。你可以通过在调用 :c:func:`video_register_device` 之前调用以下函数来标记此类 ioctl：

    :c:func:`v4l2_disable_ioctl <v4l2_disable_ioctl>`
    (:c:type:`vdev <video_device>`, cmd)

  这种情况通常出现在基于外部因素（例如使用的卡片类型）需要禁用 :c:type:`v4l2_ioctl_ops` 中的某些功能时，而无需创建新的结构体。
`:c:type:`v4l2_file_operations` 结构体是 `file_operations` 的一个子集。
主要的区别在于省略了 inode 参数，因为它从未被使用过。
如果需要与媒体框架进行集成，你必须通过调用 `:c:func:`media_entity_pads_init` 来初始化嵌入在 `:c:type:`video_device` 结构体中的 `:c:type:`media_entity` 结构体（entity 字段）：

```c
struct media_pad *pad = &my_vdev->pad;
int err;

err = media_entity_pads_init(&vdev->entity, 1, pad);
```

pads 数组必须在此之前已经初始化。无需手动设置 `struct media_entity` 类型和名称字段
当视频设备打开/关闭时，实体的引用将自动获取/释放。

### ioctl 和锁定

V4L 核心提供了可选的锁定服务。主要的服务是在 `struct video_device` 中的 `lock` 字段，它是一个指向互斥锁的指针。
如果你设置了这个指针，那么它将被 `unlocked_ioctl` 使用来序列化所有的 ioctl。
如果你使用了 `<vb2_framework>` 视频缓冲框架，则还有一个可以设置的锁：`:c:type:`video_device`->queue->lock。如果设置了这个锁，那么将使用此锁而不是 `:c:type:`video_device`->lock 来序列化所有的队列 ioctl（参见前文列出的所有这些 ioctl）。
为队列 ioctl 使用不同的锁的优势在于对于某些驱动程序（尤其是 USB 驱动程序），某些命令如设置控制可能会花费很长时间，因此你需要为缓冲队列 ioctl 使用一个单独的锁。这样可以避免你的 `VIDIOC_DQBUF` 因驱动程序忙于改变例如网络摄像头曝光而阻塞。
当然，你可以始终自己处理所有锁定，方法是将两个锁指针都设置为 `NULL`。
在 `<vb2_framework>` 框架的情况下，你可能需要实现 `wait_prepare()` 和 `wait_finish()` 回调函数以解锁/锁定，如果适用的话。
如果你使用 `queue->lock` 指针，那么你可以使用辅助函数 :c:func:`vb2_ops_wait_prepare` 和 :c:func:`vb2_ops_wait_finish`。
热插拔断开连接的实现也应该在调用 `v4l2_device_disconnect` 之前从 :c:type:`video_device` 获取锁。如果你同时也在使用 :c:type:`video_device`->queue->lock，那么你必须首先锁定 :c:type:`video_device`->queue->lock 然后是 :c:type:`video_device`->lock。这样可以确保当你调用 :c:func:`v4l2_device_disconnect` 时没有 ioctl 在运行。

### 视频设备注册

---

接下来你需要使用 :c:func:`video_register_device` 来注册视频设备，这将为你创建字符设备。

```c
err = video_register_device(vdev, VFL_TYPE_VIDEO, -1);
if (err) {
    video_device_release(vdev); /* 或者 kfree(my_vdev); */
    return err;
}
```

如果 :c:type:`v4l2_device` 的父设备有一个非 `NULL` 的 `mdev` 字段，则视频设备实体将自动与媒体设备注册。

注册哪个设备取决于类型参数。以下是一些存在的类型：

| :c:type:`vfl_devnode_type` | 设备名称 | 用途 |
|---------------------------|----------|------|
| `VFL_TYPE_VIDEO`          | `/dev/videoX` | 用于视频输入/输出设备 |
| `VFL_TYPE_VBI`            | `/dev/vbiX` | 用于垂直空白数据（例如，字幕、电传文字） |
| `VFL_TYPE_RADIO`          | `/dev/radioX` | 用于无线电调谐器 |
| `VFL_TYPE_SUBDEV`         | `/dev/v4l-subdevX` | 用于 V4L2 子设备 |
| `VFL_TYPE_SDR`            | `/dev/swradioX` | 用于软件定义无线电（SDR）调谐器 |
| `VFL_TYPE_TOUCH`          | `/dev/v4l-touchX` | 用于触摸传感器 |

最后一个参数为你提供了一定程度上对设备节点号的控制（即 `videoX` 中的 `X`）。通常你会传递 `-1` 让 V4L2 框架选择第一个空闲的数字。但有时用户想要选择一个特定的节点号。常见的做法是允许用户通过驱动模块选项来选择一个特定的设备节点号。这个数字然后被传递给此函数，并且 `video_register_device` 将尝试选择该设备节点号。如果该数字已被占用，那么将选择下一个空闲的设备节点号，并将警告发送到内核日志中。

另一种情况是当一个驱动创建多个设备时。在这种情况下，将不同的视频设备放在不同的范围内可能是有用的。例如，视频捕获设备从 0 开始，视频输出设备从 16 开始。因此，你可以使用最后一个参数来指定最小设备节点号，而 V4L2 框架将尝试选择等于或大于你所传递的值的第一个空闲数字。如果失败，则它只会选择第一个空闲的数字。
由于在这种情况下您并不关心无法选择指定设备节点编号的警告，因此您可以调用函数 :c:func:`video_register_device_no_warn`。
每当创建一个设备节点时，也会为您创建一些属性。如果您查看 ``/sys/class/video4linux``，会看到设备列表。进入例如 `video0`，您将看到 'name'、'dev_debug' 和 'index' 属性。其中 'name' 属性对应 `video_device` 结构体中的 'name' 字段。'dev_debug' 属性可用于启用核心调试功能。有关此方面的更详细信息，请参阅下一节。
'index' 属性是设备节点的索引：对于每次调用 :c:func:`video_register_device()`，该索引都会递增 1。您注册的第一个视频设备节点的索引始终为 0。
用户可以设置 udev 规则来利用 'index' 属性创建花哨的设备名称（例如，将 MPEG 视频捕获设备节点命名为 '``mpegX``'）。
在设备成功注册之后，您可以使用以下字段：

- :c:type:`video_device`->vfl_type: 传递给 :c:func:`video_register_device` 的设备类型
- :c:type:`video_device`->minor: 分配的设备次号
- :c:type:`video_device`->num: 设备节点编号（即 ``videoX`` 中的 X）
- :c:type:`video_device`->index: 设备索引编号
如果注册失败，你需要调用
:c:func:`video_device_release` 来释放分配的 :c:type:`video_device`
结构体，或者如果你的结构体中嵌入了 :c:type:`video_device`，则释放你自己的结构体。如果注册失败，``vdev->release()`` 回调将永远不会被调用，并且你不应该尝试注销设备。

### 视频设备调试
----------------------

为每个视频、VBI、无线电或软件无线电设备创建的 'dev_debug' 属性位于 ``/sys/class/video4linux/<devX>/`` 中，允许您记录文件操作。
这是一个位掩码，可以设置以下位：

.. tabularcolumns:: |p{5ex}|L|

===== ==================================================================================================
Mask  描述
===== ==================================================================================================
0x01  记录 ioctl 的名称和错误代码。VIDIOC_(D)QBUF ioctl 只有在同时设置了 0x08 位时才记录
0x02  记录 ioctl 的名称、参数和错误代码。VIDIOC_(D)QBUF ioctl 只有在同时设置了 0x08 位时才记录
0x04  记录文件操作：打开、释放、读取、写入、内存映射 (mmap) 和获取未映射区域 (get_unmapped_area)。读取和写入操作只有在同时设置了 0x08 位时才记录
0x08  记录读取和写入文件操作以及 VIDIOC_QBUF 和 VIDIOC_DQBUF ioctl
0x10  记录 poll 文件操作
0x20  在控制操作中记录错误和消息
===== ==================================================================================================

### 视频设备清理
--------------------

当需要移除视频设备节点时（无论是驱动程序卸载期间还是因为 USB 设备断开连接），你应该使用下面的方法来注销它们：

	:c:func:`video_unregister_device`
	(:c:type:`vdev <video_device>`);

这将从 sysfs 中移除设备节点（导致 udev 从 ``/dev`` 中移除它们）。
在 :c:func:`video_unregister_device` 返回后，不能再进行新的打开操作。
然而，在USB设备的情况下，某些应用程序可能仍然打开这些设备节点之一。因此，在注销后，除了释放操作外，所有文件操作都将返回错误。
当最后一个使用视频设备节点的用户退出时，则会调用 `vdev->release()` 回调函数，你可以在其中进行最终清理工作。
不要忘记如果已经初始化了与视频设备关联的媒体实体，则需要对其进行清理：

    :c:func:`media_entity_cleanup <media_entity_cleanup>`
    (&vdev->entity);

这可以在释放回调函数中完成。
辅助函数
---------

有一些有用的辅助函数：

- 文件和 :c:type:`video_device` 私有数据

你可以使用以下函数设置/获取 `video_device` 结构中的驱动程序私有数据：

    :c:func:`video_get_drvdata <video_get_drvdata>`
    (:c:type:`vdev <video_device>`);

    :c:func:`video_set_drvdata <video_set_drvdata>`
    (:c:type:`vdev <video_device>`);

请注意，你可以在调用 :c:func:`video_register_device` 之前安全地调用 :c:func:`video_set_drvdata`。
而这个函数：

    :c:func:`video_devdata <video_devdata>`
    (struct file *file);

将返回与 `file` 结构相关的 `video_device`。
:c:func:`video_devdata` 函数结合了 :c:func:`video_get_drvdata` 和 :c:func:`video_devdata` 的功能：

    :c:func:`video_drvdata <video_drvdata>`
    (struct file *file);

你可以通过以下方式从 `video_device` 结构转换到 `v4l2_device` 结构：

    .. code-block:: c

        struct v4l2_device *v4l2_dev = vdev->v4l2_dev;

- 设备节点名称

可以使用以下函数检索 :c:type:`video_device` 节点的内核名称：

    :c:func:`video_device_node_name <video_device_node_name>`
    (:c:type:`vdev <video_device>`);

该名称被用户空间工具（如 udev）作为提示使用。应尽可能使用此函数代替访问 `video_device::num` 和 `video_device::minor` 字段。

`video_device` 函数和数据结构
-----------------------------------

.. kernel-doc:: include/media/v4l2-dev.h
