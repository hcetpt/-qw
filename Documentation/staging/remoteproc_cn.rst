远程处理器框架
==========================

简介
============

现代SoC（系统级芯片）通常包含异构的远程处理器设备，这些设备可能在非对称多处理（AMP）配置中运行不同的操作系统实例。无论是Linux还是任何其他实时操作系统的实例，例如OMAP4就具有双Cortex-A9、双Cortex-M3和一个C64x+ DSP。在一个典型的配置中，双Cortex-A9以SMP（对称多处理）配置运行Linux，而其他三个核心（两个M3核心和一个DSP）则以AMP配置各自运行自己的RTOS实例。

远程处理器框架允许不同平台/架构控制这些远程处理器（如上电、加载固件、断电），同时抽象掉硬件差异，因此整个驱动程序不需要重复编写。此外，该框架还为支持这种通信方式的远程处理器添加了rpmsg virtio设备。这样一来，特定平台的远程处理器驱动程序只需提供一些低级处理函数，然后所有rpmsg驱动程序就可以直接工作。（有关基于virtio的rpmsg总线及其驱动程序的更多信息，请参阅Documentation/staging/rpmsg.rst）

现在也可以注册其他类型的virtio设备。固件只需公布它们支持哪种virtio设备类型，然后远程处理器框架就会添加这些设备。这使得可以在最小的开发成本下重用现有的virtio驱动程序，并与远程处理器后端结合使用。

用户API
========

::

  int rproc_boot(struct rproc *rproc)

启动一个远程处理器（即加载其固件并上电等）。如果远程处理器已经上电，则此函数立即返回（成功）。
成功时返回0，否则返回适当的错误值。
注意：要使用此函数，您应该已经有一个有效的rproc句柄。有几种方法可以干净地实现这一点（如devres、pdata、remoteproc_rpmsg.c中的做法，或者如果这种方法变得普遍，我们也可以考虑使用dev_archdata）。

::

  int rproc_shutdown(struct rproc *rproc)

关闭一个远程处理器（之前通过rproc_boot()启动过的）。
如果`@rproc`仍被其他用户使用，那么此函数只会递减电源引用计数并退出，而不会真正关闭设备。
成功时返回0，否则返回适当的错误值。
每次调用`rproc_boot()`最终都必须伴随一次`rproc_shutdown()`的调用。冗余调用`rproc_shutdown()`是一个错误。
..注意::
我们没有递减`rproc`的引用计数，只递减了电源引用计数。这意味着在`rproc_shutdown()`返回后，`@rproc`句柄仍然有效，用户可以在需要时继续使用它进行后续的`rproc_boot()`操作。

```c
struct rproc *rproc_get_by_phandle(phandle phandle)
```

通过设备树phandle查找一个`rproc`句柄。成功时返回`rproc`句柄，失败时返回NULL。此函数会增加远程处理器的引用计数，因此在不再需要`rproc`时，始终应使用`rproc_put()`将其引用计数递减回去。
典型用法
==========

```c
#include <linux/remoteproc.h>

/* 假设我们有一个有效的'rproc'句柄 */
int dummy_rproc_example(struct rproc *my_rproc)
{
    int ret;

    /* 让我们启动远程处理器 */
    ret = rproc_boot(my_rproc);
    if (ret) {
        /*
         * 出现了问题。处理它并离开
         */
    }

    /*
     * 我们的远程处理器现在已启动... 给它一些工作
     */

    /* 现在让我们关闭它 */
    rproc_shutdown(my_rproc);
}
```

实现者的API
============

```c
struct rproc *rproc_alloc(struct device *dev, const char *name,
                          const struct rproc_ops *ops,
                          const char *firmware, int len)
```

分配一个新的远程处理器句柄，但不立即注册。必需的参数包括底层设备、此远程处理器的名称、平台特定的操作处理器、用于启动该rproc的固件名称以及分配的rproc驱动程序所需的私有数据长度（以字节为单位）。
此函数应在初始化远程处理器期间由rproc实现者使用。
使用此函数创建`rproc`句柄并在准备就绪后，实现者应调用`rproc_add()`来完成远程处理器的注册。
成功时返回新的 `rproc`，失败时返回 `NULL`

.. note::
  
  **永远不要**直接释放 `@rproc`，即使它还没有被注册。相反，当你需要撤销 `rproc_alloc()` 的操作时，请使用 `rproc_free()`：
  
  ::

    void rproc_free(struct rproc *rproc)

  释放由 `rproc_alloc` 分配的 `rproc` 句柄。
  此函数本质上是撤销 `rproc_alloc()` 的操作，通过减少 `rproc` 的引用计数。它并不会直接释放 `rproc`；只有在没有其他引用指向 `rproc` 并且其引用计数降为零的情况下才会释放。

  ::

    int rproc_add(struct rproc *rproc)

  在使用 `rproc_alloc()` 分配后，将 `@rproc` 注册到远程处理器框架中。
  这是由平台特定的 `rproc` 实现调用的，每当探测到一个新的远程处理器设备时都会调用此函数。
  成功时返回 0，否则返回适当的错误代码。
  注意：此函数会启动一个异步固件加载上下文，该上下文会查找 `rproc` 固件支持的 virtio 设备。
  如果找到这些 virtio 设备，它们将被创建并添加。因此，注册这个远程处理器可能会导致更多的 virtio 驱动程序被探测。

  ::

    int rproc_del(struct rproc *rproc)

  撤销 `rproc_add()` 的操作。
此函数应在特定平台的 rproc 实现决定移除 rproc 设备时调用。它仅应在先前成功调用 `rproc_add()` 后调用。
在 `rproc_del()` 返回后，`@rproc` 仍然有效，并且应通过调用 `rproc_free()` 减少其最后一个引用计数。
成功返回 0，如果 `@rproc` 无效则返回 `-EINVAL`。

```c
void rproc_report_crash(struct rproc *rproc, enum rproc_crash_type type)
```

报告一个远程处理器的崩溃

每当特定平台的 rproc 实现检测到崩溃时，必须调用此函数。非远程处理器驱动程序不应调用此函数。此函数可以从原子/中断上下文调用。

实现回调
==========

这些回调应由特定平台的远程处理器驱动程序提供：

```c
/**
 * struct rproc_ops - 平台特定设备处理函数
 * @start: 开启设备并启动它
 * @stop: 关闭设备
 * @kick: 触发一个虚拟队列（参数中给出虚拟队列ID）
 */
struct rproc_ops {
	int (*start)(struct rproc *rproc);
	int (*stop)(struct rproc *rproc);
	void (*kick)(struct rproc *rproc, int vqid);
};
```

每个远程处理器实现至少应提供 `->start` 和 `->stop` 处理函数。如果还需要 rpmsg/virtio 功能，则还应提供 `->kick` 处理函数。
`->start()` 处理函数接收一个 rproc 句柄，然后应开启设备并启动它（使用 `rproc->priv` 访问平台特定的私有数据）。
启动地址（如果需要的话），可以在 `rproc->bootaddr` 中找到（远程处理器核心会将 ELF 入口点放在这里）。
成功时返回 0，失败时返回适当的错误代码。
`->stop()` 处理函数接收一个 rproc 句柄并关闭设备。
成功时返回 0，失败时返回适当的错误代码。
### `kick()` 处理程序

`kick()` 处理程序接收一个远程处理器句柄 (`rproc handle`) 和一个新消息被放置的虚拟队列索引。实现时应该中断远程处理器，并告知它有未处理的消息。通知远程处理器具体查看哪个虚拟队列索引是可选的：遍历现有的虚拟队列并查找已使用的环中的新缓冲区是相对简单且成本不高的。

### 二进制固件结构

目前，remoteproc 支持 ELF32 和 ELF64 格式的固件二进制文件。然而，预计将来我们希望支持的其他平台/设备可能会基于不同的二进制格式。当这些用例出现时，我们将不得不将二进制格式与框架核心解耦，以便在不重复通用代码的情况下支持多种二进制格式。

当解析固件时，其各个段将根据指定的设备地址（可能是物理地址，如果远程处理器直接访问内存）加载到内存中。

除了标准的 ELF 段外，大多数远程处理器还会包含一个特殊的部分，我们称之为“资源表”。资源表包含远程处理器启动前所需的一些系统资源，例如物理连续内存的分配或某些片上外设的 IOMMU 映射。

只有在满足所有资源表中的要求后，remotecore 才会启动设备。

除了系统资源外，资源表还可能包含一些资源条目，用于发布远程处理器支持的功能或配置信息，例如跟踪缓冲区和支持的 virtio 设备（及其配置）。

资源表以以下头结构开始：

```c
/**
 * struct resource_table - 固件资源表头
 * @ver: 版本号
 * @num: 资源条目的数量
 * @reserved: 预留字段（必须为零）
 * @offset: 指向各个资源条目的偏移量数组
 *
 * 由这个结构表达的资源表头包含一个版本号（如果我们需要在未来更改此格式），可用的资源条目数量以及它们在表中的偏移量。
 */
struct resource_table {
    u32 ver;
    u32 num;
    u32 reserved[2];
    u32 offset[0];
} __packed;
```

紧接在该头之后的是资源条目本身，每个条目都以以下资源条目头开始：

```c
/**
 * struct fw_rsc_hdr - 固件资源条目头
 * @type: 资源类型
 * @data: 资源数据
 *
 * 每个资源条目都以一个 `struct fw_rsc_hdr` 头开始，提供其 @type。条目的内容将紧跟在此头之后，并应根据资源类型进行解析。
 */
```

每个资源条目都以 `struct fw_rsc_hdr` 头开始，提供其 `@type`。条目的内容将紧跟在此头之后，并应根据资源类型进行解析。
```c
// 结构体定义
struct fw_rsc_hdr {
	u32 type;    // 资源类型
	u8 data[0];  // 数据
} __packed;

// 一些资源条目只是通知，告知主机特定的远程处理器配置。其他条目要求主机执行某些操作（例如分配系统资源）。有时需要进行协商，固件请求某个资源，并在分配后，主机应提供其详细信息（例如已分配内存区域的地址）。
以下是一些当前支持的资源类型：

/**
 * 枚举 fw_resource_type - 资源条目的类型
 *
 * @RSC_CARVEOUT: 请求分配一个物理连续的内存区域
 * @RSC_DEVMEM: 请求将一个基于内存的外设映射到 IOMMU
 * @RSC_TRACE: 宣布有一个用于记录日志的跟踪缓冲区可用
 * @RSC_VDEV: 声明支持一个 Virtio 设备，并作为其 Virtio 头部
 * @RSC_LAST: 请保持这个值在最后
 * @RSC_VENDOR_START: 厂商特定资源类型的范围开始
 * @RSC_VENDOR_END: 厂商特定资源类型的范围结束
 *
 * 请注意，这些值用作 rproc_handle_rsc 查找表的索引，请确保它们是合理的。此外，@RSC_LAST 用于在访问查找表之前检查索引的有效性，请根据需要更新它。
*/

enum fw_resource_type {
	RSC_CARVEOUT = 0,      // 请求分配一个物理连续的内存区域
	RSC_DEVMEM = 1,        // 请求将一个基于内存的外设映射到 IOMMU
	RSC_TRACE = 2,         // 宣布有一个用于记录日志的跟踪缓冲区可用
	RSC_VDEV = 3,          // 声明支持一个 Virtio 设备，并作为其 Virtio 头部
	RSC_LAST = 4,          // 请保持这个值在最后
	RSC_VENDOR_START = 128,// 厂商特定资源类型的范围开始
	RSC_VENDOR_END = 512,  // 厂商特定资源类型的范围结束
};

// 关于特定资源类型的更多细节，请参阅 include/linux/remoteproc.h 中的相关结构。

我们还期望将来会出现平台特定的资源条目。当这种情况发生时，我们可以轻松地添加一个新的 RSC_PLATFORM 类型，并将这些资源交给平台特定的 rproc 驱动程序来处理。

Virtio 和 remoteproc
=====================

固件应提供关于它支持的 Virtio 设备及其配置的信息：一个 RSC_VDEV 资源条目应指定 Virtio 设备 ID（如 virtio_ids.h 中所示）、Virtio 特性、Virtio 配置空间、vrings 信息等。

当注册一个新的远程处理器时，remoteproc 框架会查找其资源表并注册它支持的 Virtio 设备。固件可以支持任意数量和类型的 Virtio 设备（如果需要的话，单个远程处理器也可以轻松支持多个 rpmsg Virtio 设备）。
```
当然，RSC_VDEV 资源条目仅适用于静态分配 virtio 设备。还将通过 rpmsg 总线实现动态分配（类似于我们已经通过 rpmsg 通道进行动态分配的方式；更多相关信息请参阅 rpmsg.txt）
