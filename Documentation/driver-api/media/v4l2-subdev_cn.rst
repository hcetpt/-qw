### SPDX 许可证标识符：GPL-2.0

#### V4L2 子设备
----------------

许多驱动程序需要与子设备进行通信。这些设备可以执行各种任务，但最常见的是处理音频和/或视频的多路复用、编码或解码。对于网络摄像头而言，常见的子设备包括传感器和相机控制器。
通常这些是 I2C 设备，但并不一定如此。为了给驱动程序提供一个与这些子设备一致的接口，创建了 `v4l2_subdev` 结构体（位于 v4l2-subdev.h）。
每个子设备驱动程序都必须有一个 `v4l2_subdev` 结构体。这个结构体可以独立存在用于简单的子设备，或者如果需要存储更多的状态信息，则可以嵌入到更大的结构体中。通常会有一个低级别的设备结构（例如 `i2c_client`），其中包含由内核设置的设备数据。推荐将该指针存储在 `v4l2_subdev` 的私有数据中，使用 `v4l2_set_subdevdata` 函数。这使得从 `v4l2_subdev` 到实际的低级别总线特定设备数据的转换变得容易。
你还需要一种方法来从低级别的结构体转换到 `v4l2_subdev`。对于常见的 `i2c_client` 结构体，使用 `i2c_set_clientdata()` 调用来存储一个 `v4l2_subdev` 指针；对于其他总线，你可能需要使用其他方法。
桥接器也可能需要为每个子设备存储私有数据，如指向桥接器特有子设备私有数据的指针。为此目的，`v4l2_subdev` 结构提供了主机私有数据，可以通过 `v4l2_get_subdev_hostdata` 和 `v4l2_set_subdev_hostdata` 函数访问。
从桥接器驱动程序的角度来看，你加载子设备模块并以某种方式获取 `v4l2_subdev` 指针。对于 I2C 设备来说，这是很容易做到的：你调用 `i2c_get_clientdata()`。对于其他总线，需要做类似的事情。对于 I2C 总线上的子设备，存在辅助函数，可以为你完成大部分复杂的工作。
每个 `v4l2_subdev` 都包含子设备驱动程序可以实现的函数指针（或如果不适用则留空为 `NULL`）。由于子设备可以做很多事情，并且不希望最终得到一个巨大的操作结构体，其中只有少数几个操作被普遍实现，因此根据类别对函数指针进行了排序，每个类别都有自己的操作结构体。
顶层的操作结构体包含指向类别操作结构体的指针，如果子设备驱动程序不支持该类别的任何功能，则这些指针可以为 `NULL`。
看起来是这样的：

```c
typedef struct v4l2_subdev_core_ops {
    int (*log_status)(struct v4l2_subdev *sd);
    int (*init)(struct v4l2_subdev *sd, u32 val);
    // ...
} v4l2_subdev_core_ops;

typedef struct v4l2_subdev_tuner_ops {
    // ...
} v4l2_subdev_tuner_ops;

typedef struct v4l2_subdev_audio_ops {
    // ...
} v4l2_subdev_audio_ops;

typedef struct v4l2_subdev_video_ops {
    // ...
} v4l2_subdev_video_ops;

typedef struct v4l2_subdev_pad_ops {
    // ...
} v4l2_subdev_pad_ops;

typedef struct v4l2_subdev_ops {
    const struct v4l2_subdev_core_ops  *core;
    const struct v4l2_subdev_tuner_ops *tuner;
    const struct v4l2_subdev_audio_ops *audio;
    const struct v4l2_subdev_video_ops *video;
    const struct v4l2_subdev_pad_ops   *pad; // 注意这里应该是 pad 而不是 video
} v4l2_subdev_ops;
```

核心操作对所有子设备都是通用的，而其他类别则根据子设备的不同而实现。例如，视频设备很可能不支持音频操作，反之亦然。
这种设置在保持易于添加新操作和类别的同时限制了函数指针的数量。

子设备驱动程序使用以下方式初始化 `v4l2_subdev` 结构体：

```c
v4l2_subdev_init(sd, &ops);
```
其中 `sd` 是 `v4l2_subdev` 类型，`ops` 是 `v4l2_subdev_ops` 类型。
之后需要为 `sd->name` 设置一个唯一名称，并设置模块所有者。如果你使用 I2C 辅助函数，则这些步骤会自动完成。

如果需要与媒体框架集成，必须通过调用 `media_entity_pads_init` 来初始化嵌入在 `v4l2_subdev` 结构体中的 `media_entity` 结构体（即 `entity` 字段），前提是实体有端口：

```c
struct media_pad *pads = &my_sd->pads;
int err;

err = media_entity_pads_init(&sd->entity, num_pads, pads);
```

端口数组在此之前应该已经被初始化。不需要手动设置 `struct media_entity` 的函数和名称字段，但如需的话必须初始化其修订版本字段。
当子设备节点（如果存在）被打开/关闭时，将自动获取/释放对该实体的引用。
在销毁子设备之前，请不要忘记清理媒体实体：

```c
media_entity_cleanup(&sd->entity);
```

如果子设备驱动程序实现了接收端口（sink pads），子设备驱动程序可以设置 `v4l2_subdev_pad_ops` 类型中的 `link_validate` 字段来提供其自定义的链接验证函数。对于管道中的每个链接，会调用链接接收端的 `link_validate` 垫操作。在这两种情况下，驱动程序仍然负责验证子设备与视频节点之间的格式配置的正确性。
如果没有设置 `link_validate` 操作，则使用默认函数 `v4l2_subdev_link_validate_default`。此函数确保链接的源端和接收端上的宽度、高度以及媒体总线像素码相同。子设备驱动程序也可以自由地使用此函数执行上述提到的检查，除了它们自己的检查之外。

### 子设备注册

目前有两种方式向 V4L2 核心注册子设备。第一种（传统）的方式是由桥接驱动程序注册子设备。当桥接驱动程序拥有有关连接到它的子设备的全部信息，并且确切知道何时注册它们时，就可以这样做。这种情况通常适用于内部子设备，例如系统芯片（SoC）或复杂 PCI(e) 板卡中的视频数据处理单元、USB 摄像头中的摄像头传感器或连接到 SoC 的摄像头传感器，这些传感器会将关于自身的信息传递给桥接驱动程序，通常是在平台数据中。
然而，也存在需要异步于桥接设备注册子设备的情况。例如，在基于 Device Tree 的系统中，子设备的信息独立于桥接设备提供给系统，比如当子设备以 I2C 设备节点的形式在 Device Tree 中定义。在这种情况下使用的 API 在下面进一步描述。
使用这两种注册方法之一仅影响探测过程，无论哪种情况，运行时的桥接器-子设备交互是相同的。

#### 注册同步子设备

在**同步**的情况下，一个设备（桥接）驱动程序需要使用以下函数将 `v4l2_subdev` 与 `v4l2_device` 进行注册：

```c
v4l2_device_register_subdev(v4l2_dev, sd)
```

其中 `v4l2_dev` 是 `v4l2_device` 类型，而 `sd` 是 `v4l2_subdev` 类型。
如果子设备模块在注册前消失，这可能会失败。
成功调用此函数后，`subdev->dev` 字段指向 `v4l2_device`。
如果 `v4l2_device` 父设备有一个非 NULL 的 `mdev` 字段，那么子设备实体将自动与媒体设备进行注册。
您可以使用以下方法取消注册子设备：

	:c:func:`v4l2_device_unregister_subdev <v4l2_device_unregister_subdev>`
	(:c:type:`sd <v4l2_subdev>`)
之后，可以卸载子设备模块，并且
:c:type:`sd <v4l2_subdev>`->dev == ``NULL``
.. _媒体注册异步子设备:

注册异步子设备
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在**异步**情况下，子设备的探测可以独立于桥接驱动程序的可用性进行。子设备驱动程序需要验证是否满足成功探测的所有要求。这可能包括检查主时钟的可用性。如果任何条件未得到满足，驱动程序可能会选择返回``-EPROBE_DEFER``来请求进一步的重新探测尝试。一旦所有条件都得到满足，应使用 :c:func:`v4l2_async_register_subdev` 函数注册子设备。取消注册则通过调用 :c:func:`v4l2_async_unregister_subdev` 进行。以这种方式注册的子设备会被存储在一个全局子设备列表中，以便被桥接驱动程序获取。

驱动程序必须在使用 :c:func:`v4l2_async_register_subdev` 注册子设备之前完成所有子设备初始化工作，包括启用运行时电源管理（PM）。这是因为子设备在注册后立即变得可访问。
异步子设备通知器
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

桥接驱动程序反过来需要注册一个通知器对象。这是通过调用 :c:func:`v4l2_async_nf_register` 完成的。要取消注册通知器，驱动程序需要调用 :c:func:`v4l2_async_nf_unregister`。在释放已取消注册的通知器内存之前，必须通过调用 :c:func:`v4l2_async_nf_cleanup` 来清理它。

在注册通知器之前，桥接驱动程序必须做两件事：首先，通知器必须使用 :c:func:`v4l2_async_nf_init` 进行初始化。其次，桥接驱动程序可以开始形成异步连接描述符列表，这些描述符是桥接设备运行所需的。 :c:func:`v4l2_async_nf_add_fwnode`、:c:func:`v4l2_async_nf_add_fwnode_remote` 和 :c:func:`v4l2_async_nf_add_i2c`

异步连接描述符描述了与尚未被探测的外部子设备之间的连接。基于异步连接，在相关子设备变得可用时，可能会创建媒体数据或辅助链接。对于给定的子设备可能存在一个或多个异步连接，但在添加这些连接到通知器时这一点并不明确。随着匹配的异步子设备被发现，异步连接将逐一绑定。
异步子设备通知器
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

注册异步子设备的驱动程序也可以注册一个异步通知器。这被称为异步子设备通知器，其过程类似于桥接驱动程序的过程，只是通知器是使用 :c:func:`v4l2_async_subdev_nf_init` 进行初始化的。子设备通知器可能仅在 V4L2 设备变得可用之后才能完成，也就是说存在一条路径通过异步子设备和通知器到达一个不是异步子设备通知器的通知器。
为相机传感器驱动程序提供的异步子设备注册帮助函数
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:c:func:`v4l2_async_register_subdev_sensor` 是一个帮助函数，用于传感器驱动程序注册它们自己的异步连接，但它还注册了一个通知器，并进一步为固件中找到的镜头和闪光灯设备注册异步连接。子设备的通知器与异步子设备一起使用 :c:func:`v4l2_async_unregister_subdev` 进行取消注册和清理。
异步子设备通知器示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些函数分配了一个类型为 struct :c:type:`v4l2_async_connection` 的异步连接描述符，该描述符嵌入在一个驱动程序特定的结构体中。&struct :c:type:`v4l2_async_connection` 应该是这个结构体的第一个成员：

.. code-block:: c

    struct my_async_connection {
        struct v4l2_async_connection asc;
        ..
    };

    struct my_async_connection *my_asc;
    struct fwnode_handle *ep;
```c
my_asc = v4l2_async_nf_add_fwnode_remote(&notifier, ep,
                                         struct my_async_connection);
fwnode_handle_put(ep);

if (IS_ERR(my_asc))
    return PTR_ERR(my_asc);

// 异步子设备通知器回调
// ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

V4L2 核心随后会使用这些连接描述符来匹配异步注册的子设备。一旦检测到匹配，将会调用 `.bound()` 通知器回调。在所有连接绑定完成后，将调用 `.complete()` 回调。当一个连接从系统中移除时，会调用 `.unbind()` 方法。这三个回调都是可选的。
驱动程序可以在其特定于驱动的 `v4l2_async_connection` 包装器中存储任何类型的自定义数据。如果这些数据中的任何一项在结构体被释放时需要特殊处理，则驱动程序必须实现 `.destroy()` 通知器回调。框架会在释放 `v4l2_async_connection` 类型之前调用它。

// 调用子设备操作
// ~~~~~~~~~~~~~~~~~~~

使用 `v4l2_subdev` 结构的优势在于它是一个通用结构，并且不包含有关底层硬件的任何知识。因此，一个驱动程序可能包含多个通过 I2C 总线使用的子设备，但也有一个通过 GPIO 引脚控制的子设备。这种区别仅在设置设备时才相关，但一旦子设备被注册，它就变得完全透明了。
一旦子设备被注册后，你可以直接调用一个操作函数：

.. code-block:: c

    err = sd->ops->core->g_std(sd, &norm);

但是使用这个宏更简单更好：

.. code-block:: c

    err = v4l2_subdev_call(sd, core, g_std, &norm);

该宏会执行正确的 `NULL` 指针检查，并在 `sd <v4l2_subdev>` 为 `NULL` 时返回 `-ENODEV`，在 `sd <v4l2_subdev>`->core 或 `sd <v4l2_subdev>`->core->g_std 为 `NULL` 时返回 `-ENOIOCTLCMD`，或返回 `sd <v4l2_subdev>`->ops->core->g_std 操作的实际结果。
也可以调用所有的子设备或子设备的子集：

.. code-block:: c

    v4l2_device_call_all(v4l2_dev, 0, core, g_std, &norm);

不支持此操作的任何子设备都会被跳过，错误结果会被忽略。如果你想检查错误，可以这样做：

.. code-block:: c

    err = v4l2_device_call_until_err(v4l2_dev, 0, core, g_std, &norm);

除了 `-ENOIOCTLCMD` 的任何错误都会使循环退出并返回该错误。如果没有发生错误（除了 `-ENOIOCTLCMD`），则返回 0。
这两个调用的第二个参数是一个组 ID。如果是 0，则调用所有子设备。如果不是 0，则只调用那些组 ID 与该值匹配的子设备。在桥接驱动程序注册子设备之前，它可以将 `sd <v4l2_subdev>`->grp_id 设置为所需的任何值（默认是 0）。这个值由桥接驱动程序拥有，而子设备驱动程序永远不会修改或使用它。
组 ID 给桥接驱动程序更多控制如何调用回调。
例如，电路板上可能存在多个音频芯片，每个都能改变音量。但通常当用户想要改变音量时，只会使用其中一个。你可以将该子设备的组 ID 设置为例如 AUDIO_CONTROLLER，并在调用 `v4l2_device_call_all()` 时指定该组 ID 值。这样可以确保它只会传递给需要它的子设备。
如果子设备需要向其 v4l2_device 父设备通知事件，则可以调用 `v4l2_subdev_notify(sd, notification, arg)`。此宏会检查是否有定义 `notify()` 回调，并在没有定义时返回 `-ENODEV`。
否则，返回 `notify()` 调用的结果。
```
V4L2 子设备用户空间 API
-----------------------------

传统上，桥接驱动程序会向用户空间暴露一个或多个视频节点，并通过 :c:type:`v4l2_subdev_ops` 操作来控制子设备，以此响应视频节点操作。这种方式隐藏了底层硬件的复杂性。对于复杂的设备，可能需要比视频节点提供的更细粒度的设备控制。在这种情况下，实现了 :ref:`媒体控制器API <media_controller>` 的桥接驱动程序可以选择直接从用户空间访问子设备的操作。可以在 `/dev` 目录下创建名为 `v4l-subdev`*X* 的设备节点来直接访问子设备。如果子设备支持直接的用户空间配置，则必须在注册前设置 `V4L2_SUBDEV_FL_HAS_DEVNODE` 标志。在注册子设备后，:c:type:`v4l2_device` 驱动程序可以通过调用 :c:func:`v4l2_device_register_subdev_nodes` 为所有带有 `V4L2_SUBDEV_FL_HAS_DEVNODE` 标记的已注册子设备创建设备节点。当子设备被注销时，这些设备节点将自动移除。
该设备节点处理 V4L2 API 的一部分，包括：

- ``VIDIOC_QUERYCTRL``
- ``VIDIOC_QUERYMENU``
- ``VIDIOC_G_CTRL``
- ``VIDIOC_S_CTRL``
- ``VIDIOC_G_EXT_CTRLS``
- ``VIDIOC_S_EXT_CTRLS``
- ``VIDIOC_TRY_EXT_CTRLS``

控制 ioctl 命令与 V4L2 中定义的相同。它们的行为也相同，唯一的例外是它们只处理子设备实现的控制。根据不同的驱动程序，这些控制也可以通过一个（或几个）V4L2 设备节点访问。
- ``VIDIOC_DQEVENT``
- ``VIDIOC_SUBSCRIBE_EVENT``
- ``VIDIOC_UNSUBSCRIBE_EVENT``

事件 ioctl 命令与 V4L2 中定义的相同。它们的行为也相同，唯一的例外是它们只处理由子设备生成的事件。根据不同的驱动程序，这些事件也可以通过一个（或几个）V4L2 设备节点报告。
要支持事件，子设备驱动程序需要在注册子设备之前设置 :c:type:`v4l2_subdev`.flags 的 `V4L2_SUBDEV_FL_HAS_EVENTS` 标志。注册后，可以像往常一样在 :c:type:`v4l2_subdev`.devnode 设备节点上排队事件。
为了正确支持事件，`poll()` 文件操作也被实现。
私有 ioctl 命令

上述列表之外的所有 ioctl 命令都会直接通过核心 ::ioctl 操作传递给子设备驱动程序。
只读子设备用户空间 API
----------------------------------

通过直接调用由 :c:type:`v4l2_subdev_ops` 结构实现的内核 API 来控制其连接的子设备的桥接驱动程序通常不希望用户空间能够通过子设备设备节点更改相同的参数，因此通常不会注册任何
有时候，通过一个只读API向用户空间报告当前子设备配置是有用的，该API不允许应用程序更改设备参数，但允许通过子设备节点接口来检查这些参数。例如，为了基于计算摄影实现摄像头，用户空间需要知道针对每个支持的输出分辨率，摄像头传感器的详细配置（在跳过、合并像素、裁剪和缩放方面）。为了支持这类使用场景，桥接驱动程序可以通过只读API将子设备操作暴露给用户空间。

若要为所有已通过`V4L2_SUBDEV_FL_HAS_DEVNODE`标记注册的子设备创建只读设备节点，`:c:type:`v4l2_device`驱动程序应该调用`:c:func:`v4l2_device_register_ro_subdev_nodes`。

对于通过`:c:func:`v4l2_device_register_ro_subdev_nodes`注册的子设备节点，用户空间应用程序对以下ioctl的访问受到限制：
- `VIDIOC_SUBDEV_S_FMT`，
- `VIDIOC_SUBDEV_S_CROP`，
- `VIDIOC_SUBDEV_S_SELECTION`：

    这些ioctl仅允许在只读子设备节点上使用，且仅限于`:ref:`V4L2_SUBDEV_FORMAT_TRY <v4l2-subdev-format-whence>`格式和选择矩形。
- `VIDIOC_SUBDEV_S_FRAME_INTERVAL`，
- `VIDIOC_SUBDEV_S_DV_TIMINGS`，
- `VIDIOC_SUBDEV_S_STD`：

    这些ioctl不允许在只读子设备节点上使用。

如果ioctl不允许，或者要修改的格式设置为`V4L2_SUBDEV_FORMAT_ACTIVE`，核心会返回负错误代码，并将errno变量设置为`-EPERM`。

### I2C 子设备驱动程序

由于这类驱动程序非常常见，因此提供了特殊的辅助函数来简化其使用（位于`v4l2-common.h`中）。

向I2C驱动程序添加`:c:type:`v4l2_subdev`支持的推荐方法是将`:c:type:`v4l2_subdev`结构体嵌入为每个I2C设备实例创建的状态结构体中。对于非常简单的设备，可能没有状态结构体，在这种情况下可以直接创建`:c:type:`v4l2_subdev`。

一个典型的状态结构体可能如下所示（其中“chipname”被替换为芯片名称）：

```c
struct chipname_state {
    struct v4l2_subdev sd;
    ...  /* 其他状态字段 */
};
```

初始化`:c:type:`v4l2_subdev`结构体的方式如下：

```c
v4l2_i2c_subdev_init(&state->sd, client, subdev_ops);
```

此函数将填充`:c:type:`v4l2_subdev`的所有字段，并确保`:c:type:`v4l2_subdev`和i2c_client相互指向对方。
你也应该添加一个内联辅助函数，用于从一个 `v4l2_subdev` 指针转换到一个 `chipname_state` 结构体：

```c
static inline struct chipname_state *to_state(struct v42_subdev *sd)
{
    return container_of(sd, struct chipname_state, sd);
}
```

使用这个方法从 `v4l2_subdev` 结构体转换到 `i2c_client` 结构体：

```c
struct i2c_client *client = v4l2_get_subdevdata(sd);
```

并且使用这个方法从 `i2c_client` 转换到 `v4l2_subdev` 结构体：

```c
struct v4l2_subdev *sd = i2c_get_clientdata(client);
```

确保当 `remove()` 回调被调用时，调用 `v4l2_device_unregister_subdev(sd)`。这将使子设备从桥接驱动程序中注销。即使子设备从未注册过，这样做也是安全的。
你需要这样做是因为当桥接驱动程序销毁 I2C 适配器时，会调用该适配器上的 I2C 设备的 `remove()` 回调。之后与之对应的 `v4l2_subdev` 结构体就无效了，因此必须先进行注销。从 `remove()` 回调中调用 `v4l2_device_unregister_subdev(sd)` 确保这一过程始终正确完成。
桥接驱动程序也有一些辅助函数可以使用：

```c
struct v4l2_subdev *sd = v4l2_i2c_new_subdev(v4l2_dev, adapter,
                    "module_foo", "chipid", 0x36, NULL);
```

这会加载给定的模块（如果不需要加载任何模块，则可以为 `NULL`），并使用给定的 `i2c_adapter` 和芯片/地址参数调用 `i2c_new_client_device`。如果一切顺利，它将使用 `v4l2_device` 注册子设备。
你也可以使用 `v4l2_i2c_new_subdev` 的最后一个参数来传递一个需要探测的可能的 I2C 地址数组。这些探测地址仅在前一个参数为 0 时使用。非零参数意味着你知道确切的 I2C 地址，在这种情况下不会进行探测。
这两个函数在出现问题时都会返回 `NULL`。
需要注意的是，你传递给 `v4l2_i2c_new_subdev` 的 `chipid` 通常与模块名称相同。它允许你指定芯片变体，例如 "saa7114" 或 "saa7115"。然而一般来说，I2C 驱动程序会自动检测这些信息。
`chipid` 的使用是一个需要在将来更仔细研究的问题。它在不同的 I2C 驱动程序之间有所不同，因此可能会造成混淆。
要查看支持哪些芯片变体，可以在 I2C 驱动程序代码中的 `i2c_device_id` 表中查找。该表列出了所有可能性。
还有一个辅助函数：

`:c:func:`v4l2_i2c_new_subdev_board` 使用一个 `:c:type:`i2c_board_info` 结构体，该结构体传递给 I2C 驱动程序，并替代 irq、platform_data 和 addr 参数。
如果子设备支持 s_config 核心操作，则在设置子设备后会使用 irq 和 platform_data 参数调用该操作。
`:c:func:`v4l2_i2c_new_subdev` 函数将会调用 `:c:func:`v4l2_i2c_new_subdev_board`，内部填充一个 `:c:type:`i2c_board_info` 结构体，使用 `client_type` 和 `addr` 来填充。

集中管理的子设备活动状态
------------------------------

传统上，V4L2 子设备驱动程序维护了内部状态来表示活动设备配置。这通常实现为例如一个 `struct v4l2_mbus_framefmt` 数组，每个 pad 有一个条目，并且对于裁剪和组合矩形同样如此。

除了活动配置之外，每个子设备文件句柄都有一个由 V4L2 核心管理的 `struct v4l2_subdev_state`，其中包含尝试配置。

为了简化子设备驱动程序，V4L2 子设备 API 现在可选地支持一种集中管理的活动配置，表示为 `:c:type:`v4l2_subdev_state`。一个状态实例，包含活动设备配置，存储在子设备本身作为 `:c:type:`v4l2_subdev` 结构的一部分，而核心将一个尝试状态与每个打开的文件句柄相关联，以存储与该文件句柄相关的尝试配置。

子设备驱动程序可以选择加入并使用状态来管理它们的活动配置，方法是在注册子设备之前通过调用 `v4l2_subdev_init_finalize()` 初始化子设备状态。在注销子设备之前，它们还必须调用 `v4l2_subdev_cleanup()` 来释放所有已分配的资源。

核心自动为每个打开的文件句柄分配并初始化一个状态，以存储尝试配置，并在关闭文件句柄时释放它。

使用 `ACTIVE` 和 `TRY` 格式的 V4L2 子设备操作（参见 `<v4l2-subdev-format-whence>`）通过 'state' 参数接收正确的状态进行操作。状态必须由调用者通过调用 `:c:func:`v4l2_subdev_lock_state()` 和 `:c:func:`v4l2_subdev_unlock_state()` 进行锁定和解锁。调用者可以通过 `:c:func:`v4l2_subdev_call_state_active()` 宏来调用子设备操作，从而完成此操作。

不接收状态参数的操作隐式地在子设备活动状态上操作，驱动程序可以通过调用 `:c:func:`v4l2_subdev_lock_and_get_active_state()` 独占访问。子设备活动状态也必须通过调用 `:c:func:`v4l2_subdev_unlock_state()` 来释放。
驱动程序绝不能手动访问存储在:c:type:`v4l2_subdev`或文件句柄中的状态，除非通过指定的辅助函数。虽然V4L2核心会将正确的尝试或活动状态传递给子设备操作，但许多现有设备驱动程序在使用:c:func:`v4l2_subdev_call()`调用操作时传递NULL状态。这种遗留结构会导致问题，特别是对于那些允许V4L2核心管理活动状态的子设备驱动程序，因为它们期望接收到合适的状态作为参数。为了帮助子设备驱动程序转换到受管理的活动状态，而又不必同时转换所有调用者，已在v4l2_subdev_call()中添加了一个额外的包装层，该层通过使用:c:func:`v4l2_subdev_lock_and_get_active_state()`获取并锁定调用者的活动状态来处理NULL情况，并在调用后解锁状态。

实际上，整个子设备状态被分为三个部分：v4l2_subdev_state、子设备控制和子设备驱动程序内部状态。将来这些部分应该合并为一个单一的状态。目前，我们需要一种方法来处理这些部分的锁定。这可以通过共享一个锁来实现。v4l2_ctrl_handler已经通过其'lock'指针支持这一点，状态也采用相同的模型。驱动程序可以在调用v4l2_subdev_init_finalize()之前执行以下操作：

.. code-block:: c

	sd->ctrl_handler->lock = &priv->mutex;
	sd->state_lock = &priv->mutex;

这将在控制和状态之间共享驱动程序的私有互斥量。

流、复用媒体垫和内部路由
---------------------------

子设备驱动程序可以通过设置V4L2_SUBDEV_FL_STREAMS子设备标志并实现对集中管理的子设备活动状态、路由和基于流的配置的支持来实现多路复用流的支持。

V4L2 子设备功能和数据结构
------------------------------

.. kernel-doc:: include/media/v4l2-subdev.h
