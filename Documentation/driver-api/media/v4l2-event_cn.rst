### SPDX 许可证标识符: GPL-2.0

#### V4L2 事件
##### 

V4L2 事件提供了一种通用的方法来将事件传递到用户空间。驱动程序必须使用 `v4l2_fh` 类型才能支持 V4L2 事件。

事件是按文件句柄订阅的。一个事件规范包括一个“类型”，并可选地与通过“id”字段标识的对象关联。如果未使用，则“id”为 0。因此，一个事件可以通过“(类型, id)”元组唯一标识。

`v4l2_fh` 结构体在其 `subscribed` 字段中有一个已订阅事件的列表。

当用户订阅一个事件时，一个 `v4l2_subscribed_event` 结构体会被添加到 `v4l2_fh->subscribed` 中，每订阅一个事件就会添加一个这样的结构体。

每个 `v4l2_subscribed_event` 结构体以一个 `v4l2_kevent` 环形缓冲区结束，该缓冲区的大小由调用 `v4l2_event_subscribe` 函数的调用者给出。这个环形缓冲区用于存储驱动程序引发的所有事件。

因此，每一个“(类型, ID)”事件元组都会有其自己的 `v4l2_kevent` 环形缓冲区。这保证了如果驱动程序在短时间内生成大量一种类型的事件，则不会覆盖另一种类型的事件。

但是，如果你收到的某种类型的事件数量超过了 `v4l2_kevent` 环形缓冲区的大小，那么最旧的事件将会被删除，并添加新的事件。

`v4l2_kevent` 结构体链接到了 `v4l2_fh` 结构体中的 “available” 列表中，这样 `VIDIOC_DQEVENT` 就会知道先解除队列哪个事件。

最后，如果事件订阅与特定对象（例如 V4L2 控制）相关联，则该对象也需要了解这一点，以便能够由该对象触发事件。因此，“node”字段可以用来将 `v4l2_subscribed_event` 结构体链接到此类对象的列表中。
因此，总结如下：

- `struct v4l2_fh` 包含两个列表：一个是“已订阅”的事件列表，另一个是“可用”的事件列表。
- `struct v4l2_subscribed_event` 包含一个特定类型被触发（挂起）事件的环形缓冲区。
- 如果 `struct v4l2_subscribed_event` 与某个特定对象关联，则该对象将有一个内部的 `struct v4l2_subscribed_event` 列表，以便知道谁向该对象订阅了事件。
此外，内部的 `struct v4l2_subscribed_event` 具有 `merge()` 和 `replace()` 的回调函数，这些回调函数可以由驱动程序设置。当一个新的事件被触发而没有更多空间时，会调用这些回调函数。
- `replace()` 回调允许你用新事件的负载替换旧事件的负载，并将旧负载中相关数据合并到取代它的新负载中。当此事件类型的环形缓冲区大小为一（即只能存储一个事件）时会调用它。
- `merge()` 回调允许你将最老的事件负载合并到次老的事件负载中。当环形缓冲区的大小大于一时会调用它。
这样就不会丢失状态信息，只是丢失了导致该状态的中间步骤。
一个很好的例子是在 v4l2-event.c 中的 `ctrls_replace()` 和 `ctrls_merge()` 回调函数，用于控制事件。
.. note::
    这些回调函数可能在中断上下文中被调用，因此必须快速执行。
为了将事件排队到视频设备，驱动程序应调用：

`:c:func` `v4l2_event_queue <v4l2_event_queue>` 
(`:c:type` `vdev <video_device>` , `:c:type` `ev <v4l2_event>`)

驱动程序的唯一责任是填充类型和数据字段。
其他字段将由V4L2填充。
事件订阅
~~~~~~~~~

订阅一个事件是通过：

    :c:func:`v4l2_event_subscribe <v4l2_event_subscribe>`
    (:c:type:`fh <v4l2_fh>`, :c:type:`sub <v4l2_event_subscription>` ,
    elems, :c:type:`ops <v4l2_subscribed_event_ops>`)

此函数用于实现 :c:type:`video_device`->
:c:type:`ioctl_ops <v4l2_ioctl_ops>`-> ``vidioc_subscribe_event``,
但是驱动程序必须首先检查是否能够产生具有指定事件ID的事件，然后应该调用
:c:func:`v4l2_event_subscribe` 来订阅该事件。
参数elems是该事件事件队列的大小。如果它为0，
那么框架将填入一个默认值（这取决于事件类型）。
参数ops允许驱动程序指定一些回调函数：

.. tabularcolumns:: |p{1.5cm}|p{16.0cm}|

======== ==============================================================
回调     描述
======== ==============================================================
add      当一个新的监听器添加时被调用（对于同一事件的重复订阅只会导致此回调被调用一次）
del      当一个监听器停止监听时被调用
replace  将事件 'old' 替换为事件 'new'
merge    将事件 'old' 合并到事件 'new' 中
======== ==============================================================

所有4个回调都是可选的，如果你不想指定任何回调函数，
参数ops本身可以为 ``NULL``。
取消订阅事件
~~~~~~~~~~~~~~

取消订阅一个事件是通过：

    :c:func:`v4l2_event_unsubscribe <v4l2_event_unsubscribe>`
    (:c:type:`fh <v4l2_fh>`, :c:type:`sub <v4l2_event_subscription>`)

此函数用于实现 :c:type:`video_device`->
:c:type:`ioctl_ops <v4l2_ioctl_ops>`-> ``vidioc_unsubscribe_event``.
除非驱动程序想要参与取消订阅的过程，否则它可以调用 :c:func:`v4l2_event_unsubscribe` 直接取消订阅。
特殊的类型 ``V4L2_EVENT_ALL`` 可以用来取消订阅所有事件。驱动程序可能需要特别处理这种情况。
检查是否有待处理的事件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

检查是否有待处理的事件是通过：

    :c:func:`v4l2_event_pending <v4l2_event_pending>`
    (:c:type:`fh <v4l2_fh>`)

此函数返回待处理事件的数量。在实现poll时非常有用。
### 事件如何工作

事件通过`poll`系统调用传递到用户空间。驱动程序可以使用`:c:type:`v4l2_fh`->wait`（一个`wait_queue_head_t`类型）作为`poll_wait()`的参数。

存在标准事件和私有事件。新的标准事件必须使用最小可用的事件类型。驱动程序必须从它们自己的类开始分配事件，起始位置是类基地址。类基地址是`V4L2_EVENT_PRIVATE_START`加上n乘以1000，其中n是最小可用数字。类中的第一个事件类型保留供将来使用，因此第一个可用的事件类型是“类基地址+1”。

关于如何使用V4L2事件的一个示例可以在OMAP 3 ISP驱动程序(``drivers/media/platform/ti/omap3isp``)中找到。

子设备可以直接通过`V4L2_DEVICE_NOTIFY_EVENT`向`:c:type:`v4l2_device`通知函数发送事件。这允许桥接器将发送事件的子设备映射到与该子设备相关的需要被告知此类事件的视频节点。

### V4L2事件函数和数据结构

更多细节请参阅内核文档：`include/media/v4l2-event.h`
