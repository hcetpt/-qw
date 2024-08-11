============================
使用 ISA 和 LPC 设备的 DMA
============================

:作者: Pierre Ossman <drzeus@drzeus.cx>

本文档描述了如何使用旧的 ISA DMA 控制器进行 DMA 传输。尽管 ISA 在今天几乎已经过时，但 LPC 总线仍然使用相同的 DMA 系统，因此它将在一段时间内继续存在。
头文件和依赖项
------------------------

为了执行 ISA 风格的 DMA，您需要包含两个头文件：

```c
#include <linux/dma-mapping.h>
#include <asm/dma.h>
```

第一个是用于将虚拟地址转换为总线地址的通用 DMA API（详细信息请参阅 `Documentation/core-api/dma-api.rst`）。第二个包含了特定于 ISA DMA 传输的例程。由于并非所有平台都支持此功能，请确保构建您的 Kconfig 文件依赖于 `ISA_DMA_API`（而不是 `ISA`），以防止在不支持的平台上尝试编译您的驱动程序。
缓冲区分配
-----------------

ISA DMA 控制器对于可以访问的内存有一些非常严格的要求，所以在分配缓冲区时必须格外小心
（通常您需要为 DMA 传输分配一个特殊的缓冲区，而不是直接从您的常规数据结构中进行传输。）

DMA 可用的地址空间是最低的 16 MB 的 _物理_ 内存
而且传输块不能跨越页面边界（这取决于您使用的通道，页面边界通常是 64 或 128 KiB）
为了分配满足所有这些要求的一段内存，您需要向 `kmalloc` 传递标志 `GFP_DMA`
不幸的是，可用于 ISA DMA 的内存资源非常稀缺，除非您在启动过程中分配内存，否则最好也传递 `__GFP_RETRY_MAYFAIL` 和 `__GFP_NOWARN` 来让分配器尝试得更努力一些
（这种稀缺性还意味着您应该尽早分配缓冲区，并且直到驱动程序卸载之前不要释放它。）

地址转换
-------------------

要将虚拟地址转换为总线地址，请使用正常的 DMA API。不要使用 `isa_virt_to_bus()`，即使它能实现相同的功能。原因在于 `isa_virt_to_bus()` 函数会要求 Kconfig 依赖于 `ISA`，而不仅仅是 `ISA_DMA_API`，而这实际上是你所需要的全部。记住，尽管 DMA 控制器起源于 ISA，但它也被用于其他地方
注意：x86_64 架构在其 ISA 相关的 DMA API 中曾存在问题，但现在已被修复。如果您的架构存在问题，请修复 DMA API 而不是退回到 ISA 函数。
通道
------

一个标准的 ISA DMA 控制器有 8 个通道。较低的四个用于
8 位数据传输，而较高的四个则用于 16 位数据传输
（实际上，DMA 控制器实际上是两个独立的控制器，其中
第 4 通道被用来为第二个控制器（0-3）提供 DMA 访问权限。
这意味着在四个 16 位通道中只有三个是可以使用的。）

这些资源的分配方式与所有基本资源类似：

```c
extern int request_dma(unsigned int dmanr, const char * device_id);
extern void free_dma(unsigned int dmanr);
```

是否能够使用 16 位或 8 位的数据传输并不是由
驱动程序作者决定的，而是取决于硬件支持的情况。请查阅您的
规格说明或测试不同的通道。

数据传输
----------

接下来是重要的部分，即实际的 DMA 数据传输。:)

在使用任何 ISA DMA 操作之前，您需要使用 `claim_dma_lock()` 获取 DMA 锁。
原因是某些 DMA 操作是非原子性的，因此一次只能有一个驱动程序
操作寄存器。
首次使用 DMA 控制器时，应调用 `clear_dma_ff()`。这会清除 DMA
控制器内部的一个寄存器，该寄存器用于非原子性操作。只要您
（和其他所有人）使用锁定函数，那么您只需重置一次这个寄存器。
接着，您告诉控制器打算进行数据传输的方向，使用 `set_dma_mode()` 函数。
目前，您可以选择 `DMA_MODE_READ` 和 `DMA_MODE_WRITE` 两种模式。
设置数据传输的起始地址（对于 16 位传输，该地址必须是 16 位对齐的）
以及要传输的字节数。请注意，这里是“字节”。DMA 常规函数将处理
所有必要的转换以符合 DMA 控制器的要求。
最后一步是启用 DMA 通道并释放 DMA 锁。
一旦 DMA 传输完成（或超时），您应该再次禁用通道。您还应该检查
`get_dma_residue()` 来确保所有数据都已传输完成。
示例： 

```c
int flags, residue;

flags = claim_dma_lock();

clear_dma_ff();

set_dma_mode(channel, DMA_MODE_WRITE);
set_dma_addr(channel, phys_addr);
set_dma_count(channel, num_bytes);

dma_enable(channel);

release_dma_lock(flags);

while (!device_done());

flags = claim_dma_lock();

dma_disable(channel);

residue = dma_get_residue(channel);
if (residue != 0)
	printk(KERN_ERR "driver: Incomplete DMA transfer! "
			"%d bytes left!\n", residue);

release_dma_lock(flags);
```

挂起/恢复
--------------

确保在 DMA 传输正在进行时机器不会进入挂起状态是驱动程序的责任。
此外，在系统挂起时所有的 DMA 设置都会丢失，因此如果您的驱动程序依赖于
DMA 控制器处于特定状态，则在恢复时必须重新设置这些寄存器。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
