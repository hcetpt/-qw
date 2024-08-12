MEN 变色龙总线
=============

.. 目录
   ================
   1. 引言
      1.1 本文档的范围
      1.2 当前实现的限制
   2. 架构
      2.1 MEN 变色龙总线
      2.2 载体设备
      2.3 解析器
   3. 资源管理
      3.1 内存资源
      3.2 中断请求（IRQ）
   4. 编写 MCB 驱动程序
      4.1 驱动程序结构
      4.2 探测与连接
      4.3 初始化驱动程序
      4.4 使用直接内存访问（DMA）

引言
============

本文档描述了MEN 变色龙总线（在本文档中称为 MCB）的架构和实现。
### 1.1 本文档的范围

本文档旨在提供当前实现的一个简要概述，并不意味着完全描述基于 MCB 的设备的所有可能性。
### 1.2 当前实现的限制

当前实现仅限于使用单一内存资源并共享 PCI 传统中断的 PCI 和 PCIe 基础载体设备。未实现的功能包括：

- 多资源 MCB 设备，如 VME 控制器或 M-Module 载体
- 需要另一个 MCB 设备的 MCB 设备，例如用于 DMA 控制器的缓冲区描述符的 SRAM 或视频控制器的视频内存
- 对于拥有一个（或多个）每 MCB 设备中断的载体设备，如支持 MSI 或 MSI-X 的 PCIe 载体设备，每个载体的中断域

架构
============

MCB 可分为三个功能块：

- MEN 变色龙总线本身，
- MCB 载体设备驱动程序
- 变色龙表解析器
#### MEN 变色龙总线

MEN 变色龙总线是一个人造的总线系统，它连接到由 MEN Mikro Elektronik GmbH 生产的一些硬件上的变色龙 FPGA 设备。这些设备是通过某种形式的 PCI 或 PCIe 链路连接的多功能 FPGA 实现，并且每个 FPGA 都包含一个头部部分来描述 FPGA 的内容。头部列出了设备 ID、PCI BAR、从 PCI BAR 开始的偏移量、FPGA 中的大小、中断编号以及其他当前 MCB 实现尚未处理的一些属性。
#### 载体设备

载体设备只是实际物理总线上变色龙 FPGA 所连接的一种抽象。一些 IP 核驱动可能需要与载体设备的特性进行交互（例如查询 PCI 设备的中断编号）。为了提供对真实硬件总线的抽象，MCB 载体设备提供了回调方法，将驱动程序的 MCB 函数调用转换为与硬件相关的函数调用。例如，载体设备可以实现 `get_irq()` 方法，该方法可以转换为对硬件总线的查询，以确定设备应使用的中断编号。
#### 解析器

解析器读取变色龙设备的前 512 字节并解析变色龙表。目前，解析器仅支持变色龙表的变色龙 v2 变体，但很容易适应支持旧版或未来可能的变体。在解析表条目时，会分配新的 MCB 设备，并根据变色龙表中的资源分配为其分配资源。完成资源分配后，MCB 设备将在 MCB 上注册，从而在 Linux 内核的驱动核心上注册。

资源管理
============

当前实现为每个 MCB 设备分配一个内存资源和一个中断请求（IRQ）资源。但这一点将来可能会发生变化。
内存资源
------------

每个MCB设备恰好有一个内存资源，可以从MCB总线上请求。这个内存资源是MCB设备在载体内的物理地址，并且打算传递给`ioremap()`及其相关函数使用。内核已经通过调用`request_mem_region()`请求了这个资源。

中断请求（IRQs）
--------

每个MCB设备恰好有一个IRQ资源，可以从MCB总线上请求。如果载体设备驱动程序实现了`->get_irq()`回调方法，则会返回由载体设备分配的IRQ编号，否则将返回Chameleon表中的IRQ编号。这个编号适合传递给`request_irq()`。

编写一个MCB驱动
=====================

驱动结构
--------------------

每个MCB驱动都有一个结构来标识设备驱动以及设备ID，这些ID用来识别FPGA中的IP Core。驱动结构还包含了在驱动探查和从系统移除时执行的回调方法:

```c
static const struct mcb_device_id foo_ids[] = {
	{ .device = 0x123 },
	{ }
};
MODULE_DEVICE_TABLE(mcb, foo_ids);

static struct mcb_driver foo_driver = {
	driver = {
		.name = "foo-bar",
		.owner = THIS_MODULE,
	},
	probe = foo_probe,
	remove = foo_remove,
	id_table = foo_ids,
};
```

探查与附加
------------------

当加载了一个驱动并且找到了它所服务的MCB设备时，MCB核心会调用驱动的探查回调方法。当驱动从系统中移除时，MCB核心会调用驱动的移除回调方法:

```c
static int foo_probe(struct mcb_device *mdev, const struct mcb_device_id *id);
static void foo_remove(struct mcb_device *mdev);
```

初始化驱动
-------------------

当内核启动或您的foo驱动模块被插入时，您需要进行驱动初始化。通常只需向MCB核心注册您的驱动模块即可:

```c
static int __init foo_init(void)
{
	return mcb_register_driver(&foo_driver);
}
module_init(foo_init);

static void __exit foo_exit(void)
{
	mcb_unregister_driver(&foo_driver);
}
module_exit(foo_exit);
```

可以使用`module_mcb_driver()`宏来简化上述代码:

```c
module_mcb_driver(foo_driver);
```

使用DMA
---------

为了利用内核的DMA-API功能，您需要使用载体设备的`struct device`。幸运的是，`struct mcb_device`嵌入了一个指向载体设备用于DMA目的的指针(`->dma_dev`):

```c
int ret = dma_set_mask_and_coherent(&mdev->dma_dev, DMA_BIT_MASK(dma_bits));
if (ret)
        /* 处理错误 */
```
