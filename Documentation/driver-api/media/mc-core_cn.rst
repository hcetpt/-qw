SPDX 许可证标识符: GPL-2.0

媒体控制器设备
------------------------

媒体控制器
~~~~~~~~~~~~~

媒体控制器用户空间 API 在 :ref:`媒体控制器 uAPI 书籍 <media_controller>` 中有详细文档。本文档重点介绍媒体框架的内核端实现。
抽象媒体设备模型
^^^^^^^^^^^^^^^^^^^^^^^^^^^

发现设备内部拓扑结构并在运行时对其进行配置是媒体框架的目标之一。为了实现这一目标，硬件设备被建模为由实体通过端口连接而成的有向图。
一个实体是一个基本的媒体硬件构建块。它可以对应于各种逻辑块，例如物理硬件设备（例如 CMOS 传感器）、逻辑硬件设备（SoC 图像处理管道中的一个构建块）、DMA 通道或物理连接器。
一个端口是实体与其他实体交互的连接端点。实体产生的数据（不仅限于视频）从该实体的输出流向一个或多个实体输入。端口不应与芯片边界处的物理引脚混淆。
一条链路是从两个端口之间的有向点对点连接，这些端口可以位于同一个实体上，也可以位于不同的实体上。数据从源端口流向汇端口。

媒体设备
^^^^^^^^^^^^

一个媒体设备由一个 `struct media_device` 实例表示，该实例在 "include/media/media-device.h" 中定义。
该结构的分配由媒体设备驱动程序处理，通常是将其嵌入到更大的驱动程序特定结构中。
驱动程序通过调用 `media_device_init()` 函数初始化媒体设备实例。初始化媒体设备实例后，需要通过宏 `media_device_register()` 调用 `__media_device_register()` 来注册它，并通过调用 `media_device_unregister()` 来注销它。初始化过的媒体设备最终必须通过调用 `media_device_cleanup()` 来清理。
请注意，不允许注销未先注册的媒体设备实例，也不允许清理未先初始化的媒体设备实例。

实体
^^^^^^^^

实体由一个 `struct media_entity` 实例表示，该实例在 "include/media/media-entity.h" 中定义。该结构通常被嵌入到更高级别的结构中，例如 `v4l2_subdev` 或 `video_device` 实例，尽管驱动程序可以直接分配实体。
驱动程序通过调用函数 :c:func:`media_entity_pads_init()` 来初始化实体的端口。
驱动程序通过调用函数 :c:func:`media_device_register_entity()` 将实体注册到多媒体设备，
并通过调用函数 :c:func:`media_device_unregister_entity()` 来取消注册。

接口
^^^^^^^^^^

接口由一个 `struct media_interface` 实例表示，该实例在
``include/media/media-entity.h`` 中定义。目前，只定义了一种类型的接口：设备节点。此类接口由
`struct media_intf_devnode` 表示。
驱动程序通过调用函数 :c:func:`media_devnode_create()` 来初始化和创建设备节点接口，
并通过调用 :c:func:`media_devnode_remove()` 来移除它们。

端口
^^^^

端口由一个 `struct media_pad` 实例表示，该实例在
``include/media/media-entity.h`` 中定义。每个实体将其端口存储在一个由实体驱动管理的端口数组中。
驱动程序通常将该数组嵌入到特定于驱动的结构体中。
端口通过其所属的实体和它在端口数组中的0为基点的索引来标识。
这些信息都存储在 `struct media_pad` 中，使得 `struct media_pad` 指针成为存储和传递链接引用的标准方式。
端口具有描述端口能力和状态的标志：
``MEDIA_PAD_FL_SINK`` 表明该端口支持接收数据；
``MEDIA_PAD_FL_SOURCE`` 表明该端口支持输出数据。
### 注释：

对于每个端口（pad），必须且只能设置`MEDIA_PAD_FL_SINK`或`MEDIA_PAD_FL_SOURCE`中的一个。

### 链接
#### ^^^^^

链接由一个`struct media_link`实例表示，定义在`include/media/media-entity.h`中。存在两种类型的链接：

1. **端口到端口的链接**：
   
   通过它们的端口（PADs）将两个实体关联起来。每个实体都有一个指向所有起始于或指向其任何端口的链接的列表。
   因此，给定的链接会被存储两次，一次在源实体中，一次在目标实体中。
   驱动程序通过调用`:c:func:'media_create_pad_link()'`来创建端口到端口的链接，并通过调用`:c:func:'media_entity_remove_links()'`来移除链接。

2. **接口到实体的链接**：

   将一个接口与一个实体关联起来。
   驱动程序通过调用`:c:func:'media_create_intf_link()'`来创建接口到实体的链接，并通过调用`:c:func:'media_remove_intf_links()'`来移除链接。

### 注释：

链接只能在两端都已经创建之后才能创建。

链接具有描述链接能力和状态的标志。有效值在`:c:func:'media_create_pad_link()'`和`:c:func:'media_create_intf_link()'`中有描述。

### 图遍历
#### ^^^^^^^^^^^^

媒体框架提供了用于遍历图中实体的API。
为了遍历属于媒体设备的所有实体，驱动程序可以使用`media_device_for_each_entity`宏，该宏定义在`include/media/media-device.h`中。
```c
// 定义一个指向 media_entity 的指针
struct media_entity *entity;

// 遍历 media_device 中的所有 entity
media_device_for_each_entity(entity, mdev) {
    // entity 会依次指向每一个 entity
    ..
}
```

驱动可能还需要遍历从给定 entity 出发，通过启用的链接可以到达的所有图中的 entity。为了这个目的，媒体框架提供了一个深度优先的图遍历 API。
**注意：**

   不支持包含循环（无论是有向还是无向）的图。为了避免无限循环，图遍历代码将最大深度限制为 `MEDIA_ENTITY_ENUM_MAX_DEPTH`，目前定义为 16。
驱动通过调用函数 :c:func:`media_graph_walk_start()` 来启动图遍历。

由调用者提供的图结构被初始化以从给定的 entity 开始图遍历。
然后驱动可以通过调用函数 :c:func:`media_graph_walk_next()` 来获取下一个 entity。

当图遍历完成时，该函数将返回 `NULL`。
图遍历可以在任何时候中断。不需要清理函数调用，图结构可以正常释放。
辅助函数可用于在两个给定的 pad 之间查找链接，或者通过启用的链接找到与另一个 pad 相连的 pad（:c:func:`media_entity_find_link()`、:c:func:`media_pad_remote_pad_first()`、:c:func:`media_entity_remote_source_pad_unique()` 和 :c:func:`media_pad_remote_pad_unique()`）。

### 使用计数和电源管理
由于驱动在电源管理方面存在巨大差异，媒体控制器不实现电源管理。但是，`struct media_entity` 包含一个 `use_count` 字段，媒体驱动可以使用它来跟踪每个实体的用户数量以满足电源管理需求。
字段 :c:type:`media_entity<media_entity>`.\ ``use_count`` 由媒体驱动拥有，实体驱动不应触及该字段。访问该字段必须受到 :c:type:`media_device`.\ ``graph_mutex`` 锁的保护。

### 链接设置
链接属性可以通过调用 :c:func:`media_entity_setup_link()` 在运行时进行修改。
管道和媒体流
^^^^^^^^^^^^^^^^^^^^^^^^^^^

媒体流是一系列像素或元数据的流动，这些像素或元数据源自一个或多个源设备（如传感器），并通过媒体实体的端口流向最终的目标。在传输过程中，这些数据可以被设备修改（例如，进行缩放或像素格式转换），也可以被分成多条支流，或者将多条支流合并。
媒体管道是一组相互依赖的媒体流。这种依赖关系可能是由硬件造成的（例如，如果第一条流已经启用，则无法更改第二条流的配置）或是由驱动程序根据软件设计造成的。最常见的情况是，一个媒体管道只包含一条不会分叉的流。
开始流传输时，驱动程序必须通知管道中的所有实体，以防止在流传输过程中修改链路状态，这可以通过调用 :c:func:`media_pipeline_start()` 函数来实现。
该函数会将管道中所有端口标记为正在流传输状态。
由 `pipe` 参数指向的 `struct media_pipeline` 实例将存储在管道中的每个端口中。驱动程序应在更高层次的管道结构中嵌入 `struct media_pipeline`，然后可以通过 `struct media_pad` 的 `pipe` 字段访问管道。
对 :c:func:`media_pipeline_start()` 的调用可以嵌套进行。
对于所有嵌套调用，管道指针必须相同。
:c:func:`media_pipeline_start()` 可能会返回错误。在这种情况下，它会自行清理所做的任何更改。
停止流传输时，驱动程序必须通过调用 :c:func:`media_pipeline_stop()` 来通知各实体。
如果有多个 :c:func:`media_pipeline_start()` 调用，则需要同样数量的 :c:func:`media_pipeline_stop()` 调用来停止流传输。
`:c:type:`media_entity` 的 `pipe` 字段在最后一次嵌套停止调用时被重置为 `NULL`。

默认情况下，如果链路的任一端是流实体，则配置链路将以 `-EBUSY` 失败。可以在流过程中修改的链路必须标记为 `MEDIA_LNK_FL_DYNAMIC` 标志。

如果需要禁止对流实体执行其他操作（例如更改实体的配置参数），驱动程序可以明确检查 `media_entity` 的 `stream_count` 字段来确定实体是否处于流状态。进行此操作时必须持有媒体设备的图形互斥锁。

### 链路验证

链路验证由 `:c:func:`media_pipeline_start()` 对于管道中具有接收垫的所有实体执行。使用 `:c:type:`media_entity` 的 `link_validate()` 回调函数来进行这一目的。在 `link_validate()` 回调函数中，实体驱动程序应检查连接实体的源垫和其自身接收垫的属性是否匹配。匹配的实际含义取决于实体的类型（最终取决于硬件的特性）。

子系统应通过提供特定于子系统的辅助函数以方便获取常用信息的方式来促进链路验证，并最终提供一种使用驱动程序特定回调的方法。

### 媒体控制器设备分配器API

当媒体设备属于一个以上的驱动程序时，使用共享的结构化设备作为查找键来分配共享媒体设备。

共享媒体设备应保持注册状态直到最后一个驱动程序取消注册它。此外，在所有引用都被释放后，媒体设备也应被释放。每个驱动程序在探测期间分配媒体设备时会获得对媒体设备的引用。如果媒体设备已经分配，分配API将增加引用计数并返回现有的媒体设备。驱动程序在其断开连接例程中调用 `:c:func:`media_device_delete()` 时，将引用放回。

媒体设备从kref put处理程序中被取消注册并清理，以确保媒体设备保持注册状态直到最后一个驱动程序取消注册该媒体设备。

#### **驱动程序使用**

驱动程序应使用适当的媒体核心例程来管理共享媒体设备的生命周期，处理以下两种状态：
1. 分配 -> 注册 -> 删除
2. 获取已注册设备的引用 -> 删除

调用 `:c:func:`media_device_delete()` 例程以确保正确处理共享媒体设备的删除。

#### **驱动程序探测：**
调用 `:c:func:`media_device_usb_allocate()` 来分配或获取引用
如果媒体设备节点尚未注册，则调用 `:c:func:`media_device_register()`。

#### **驱动程序断开连接：**
调用 `:c:func:`media_device_delete()` 来释放媒体设备。释放工作由kref put处理程序处理。
翻译成中文:

API 定义
^^^^^^^^^^^^^^^

.. 内核文档:: include/media/media-device.h

.. 内核文档:: include/media/media-devnode.h

.. 内核文档:: include/media/media-entity.h

.. 内核文档:: include/media/media-request.h

.. 内核文档:: include/media/media-dev-allocator.h

这里的 ".. kernel-doc::" 部分表示对内核中的特定文件的引用，可以理解为是对这些文件的文档说明。在中文版中可以保持不变，因为这是一种标记语法，并非直接的英文文本。如果你需要一个更符合中文语境的解释版本，可以考虑这样翻译：

API 定义
^^^^^^^^^^^^^^^

.. 内核文档:: include/media/media-device.h

.. 内核文档:: include/media/media-devnode.h

.. 内核文档:: include/media/media-entity.h

.. 内核文档:: include/media/media-request.h

.. 内核文档:: include/media/media-dev-allocator.h

这里的 ".. 内核文档::" 表示对内核中特定文件的引用和文档说明。
