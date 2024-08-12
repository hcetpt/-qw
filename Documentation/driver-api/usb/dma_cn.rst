在Linux 2.5内核（及后续版本）中，USB设备驱动程序对DMA用于执行I/O操作的方式有了更多的控制权。相关API的详细信息可以在内核USB编程指南（通过源代码中的kerneldoc获取）中找到。

## API概览

总体来说，USB驱动程序可以继续忽略大多数DMA相关的问题，但它们仍然需要提供适用于DMA的缓冲区（参见`Documentation/core-api/dma-api-howto.rst`）。这就是它们在2.4（及更早版本）内核中的工作方式，或者现在也可以成为DMA感知型驱动程序。

### DMA感知型USB驱动程序：

- 新增的调用允许DMA感知型驱动程序分配DMA缓冲区，并为现有的DMA准备好的缓冲区管理DMA映射（如下所述）。
- URBs有一个额外的“transfer_dma”字段以及一个标志位来指示它是否有效。“Control请求”也有“setup_dma”，但驱动程序不应使用它。

- “usbcore”将映射这个DMA地址，如果DMA感知型驱动程序没有首先这样做并设置`URB_NO_TRANSFER_DMA_MAP`。HCDs不会为URBs管理DMA映射。
- 有一个新的“通用DMA API”，其中部分可用于USB设备驱动程序。绝不要在任何USB接口或设备上使用`dma_set_mask()`；这可能会破坏共享同一总线的所有设备。

## 消除不必要的复制

避免让CPU无谓地复制数据是有益的。这些开销可能会累积起来，而且像缓存污染这样的效应可能会产生微妙的惩罚。
- 如果你一直在从同一个缓冲区进行大量的小数据传输，那么在使用IOMMU来管理DMA映射的系统上，这可能会消耗大量资源。对于每次请求设置和拆除IOMMU映射的成本可能远远高于实际的I/O操作！

  对于这些特定的情况，USB提供了基本的工具来分配成本较低的内存。它们类似于`kmalloc`和`kfree`版本，能够提供正确的地址类型来存储在`urb->transfer_buffer`和`urb->transfer_dma`中。
你可以设置`URB_NO_TRANSFER_DMA_MAP`在`urb->transfer_flags`中：
```c
void *usb_alloc_coherent(struct usb_device *dev, size_t size,
                         int mem_flags, dma_addr_t *dma);
void usb_free_coherent(struct usb_device *dev, size_t size,
                       void *addr, dma_addr_t dma);
```
大多数驱动程序**不应该**使用这些工具；它们不需要使用这种类型的内存（称为“dma-coherent”），并且从`kmalloc`返回的内存就足够用了。
返回的内存缓冲区是“dma-coherent”的；有时你可能需要使用内存屏障来强制一致的内存访问顺序。它不是使用流式DMA映射，因此对于那些在I/O会严重冲击IOMMU映射的系统上进行小规模传输来说是非常合适的。（参见`Documentation/core-api/dma-api-howto.rst`以了解“coherent”和“streaming”DMA映射的定义。）

请求页面大小的1/N（以及请求N个页面）是相当空间效率的。
在大多数系统上，返回的内存将是未缓存的，因为dma-coherent内存的语义要求绕过CPU缓存或使用支持总线监听的缓存硬件。虽然x86硬件支持总线监听，但许多其他系统使用软件来清除缓存行以防止DMA冲突。
一些EHCI控制器上的设备可以处理到/从高端内存的DMA操作。
遗憾的是，当前Linux的DMA基础设施并没有一种合理的方式来暴露这些能力……而且无论如何，HIGHMEM主要是x86_32架构特有的设计缺陷。因此，最佳的做法是确保你永远不会将一个位于高内存区域的缓冲区传递给USB驱动程序。这很容易做到；这是默认行为。只要不覆盖它；例如使用``NETIF_F_HIGHDMA``。
这可能会迫使调用者进行一些中转缓冲操作，即从高内存复制到“正常”的DMA内存。如果你能提出一个好的方法来解决这个问题（对于具有超过1GB内存的x86_32机器），欢迎提交补丁。

处理现有缓冲区
=============================

在被映射到设备的DMA地址空间之前，现有的缓冲区无法直接用于DMA操作。然而，大多数传递给你的驱动程序的缓冲区可以在进行这样的DMA映射后安全地使用。（参见Documentation/core-api/dma-api-howto.rst中的第一部分，标题为“哪些内存可用于DMA？”）

- 当你有了已经被映射给USB控制器的散列列表时，你可以使用新的``usb_sg_*()``函数，它们会将散列列表转换成URBs（USB Request Blocks）：

```c
int usb_sg_init(struct usb_sg_request *io, struct usb_device *dev,
		unsigned pipe, unsigned period, struct scatterlist *sg,
		int nents, size_t length, gfp_t mem_flags);

void usb_sg_wait(struct usb_sg_request *io);

void usb_sg_cancel(struct usb_sg_request *io);
```

当USB控制器不支持DMA时，``usb_sg_init()``会尝试以PIO方式提交URBs，前提是散列列表中的页不在高内存区域，这种情况在现代架构中非常少见。
