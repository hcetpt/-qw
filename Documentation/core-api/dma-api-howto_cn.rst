动态DMA映射指南
=========================

:作者: David S. Miller <davem@redhat.com>
:作者: Richard Henderson <rth@cygnus.com>
:作者: Jakub Jelinek <jakub@redhat.com>

本指南是为设备驱动程序编写者介绍如何使用DMA API，并提供示例伪代码。对于API的简洁描述，请参阅 `Documentation/core-api/dma-api.rst`。
CPU和DMA地址
=====================

DMA API涉及几种不同类型的地址，理解它们之间的区别非常重要。
内核通常使用虚拟地址。任何由`kmalloc()`、`vmalloc()`及其类似接口返回的地址都是虚拟地址，可以存储在`void *`中。
虚拟内存系统（如TLB、页表等）将虚拟地址转换为CPU物理地址，这些地址以"phys_addr_t"或"resource_size_t"存储。内核以物理地址管理像寄存器这样的设备资源。这些就是/proc/iomem中的地址。物理地址对驱动程序来说不是直接有用的；它必须使用`ioremap()`来映射空间并产生一个虚拟地址。
I/O设备使用第三种类型的地址：“总线地址”。如果设备具有MMIO地址的寄存器，或者它通过DMA读取或写入系统内存，则设备使用的地址是总线地址。在某些系统中，总线地址与CPU物理地址相同，但在一般情况下并非如此。IOMMU和主机桥接器可以在物理地址和总线地址之间产生任意映射。
从设备的角度来看，DMA使用总线地址空间，但它可能被限制在这个空间的一个子集内。例如，即使系统支持主内存和PCI BAR的64位地址，它也可能使用IOMMU使得设备只需要使用32位DMA地址。
以下是一张图示和一些例子：

```
               CPU                  CPU                  Bus
             Virtual              Physical             Address
             Address              Address               Space
              Space                Space

            +-------+             +------+             +------+
            |       |             |MMIO  |   Offset    |      |
            |       |  Virtual    |Space |   applied   |      |
          C +-------+ --------> B +------+ ----------> +------+ A
            |       |  mapping    |      |   by host   |      |
  +-----+   |       |             |      |   bridge    |      |   +--------+
  |     |   |       |             +------+             |      |   |        |
  | CPU |   |       |             | RAM  |             |      |   | Device |
  |     |   |       |             |      |             |      |   |        |
  +-----+   +-------+             +------+             +------+   +--------+
            |       |  Virtual    |Buffer|   Mapping   |      |
          X +-------+ --------> Y +------+ <---------- +------+ Z
            |       |  mapping    | RAM  |   by IOMMU
            |       |             |      |
            |       |             |      |
            |       |             |      |
            +-------+             +------+
```

在枚举过程中，内核了解到I/O设备及其MMIO空间以及连接它们到系统的主机桥接器。例如，如果PCI设备有一个BAR，内核会从BAR中读取总线地址（A），并将其转换为CPU物理地址（B）。地址B存储在struct resource中，并通常通过/proc/iomem公开。当驱动程序声明一个设备时，它通常使用`ioremap()`将物理地址B映射到虚拟地址（C）。然后它可以使用例如`ioread32(C)`来访问位于总线地址A的设备寄存器。
如果设备支持DMA，驱动程序将使用`kmalloc()`或类似的接口设置缓冲区，这将返回一个虚拟地址（X）。虚拟内存系统将X映射到系统RAM中的物理地址（Y）。驱动程序可以使用虚拟地址X来访问缓冲区，但设备本身不能，因为DMA不经过CPU的虚拟内存系统。
在一些简单的系统中，设备可以直接对物理地址Y进行DMA操作。但在许多其他系统中，存在IOMMU硬件将DMA地址转换为物理地址，例如，它将Z转换为Y。这是DMA API存在的部分原因：驱动程序可以将虚拟地址X传递给`dma_map_single()`这样的接口，该接口会设置所需的IOMMU映射并返回DMA地址Z。然后驱动程序告诉设备对Z进行DMA操作，而IOMMU将其映射到系统RAM中地址Y处的缓冲区。
为了使Linux能够使用动态DMA映射，它需要驱动程序的帮助，即必须考虑到DMA地址应该仅在实际使用时进行映射，并且在DMA传输后解除映射。
以下的API当然也适用于没有此类硬件的平台。
请注意，DMA API与任何总线兼容，不受底层微处理器架构的影响。您应当使用通用的DMA API而非特定于总线的DMA API，也就是说，应当使用`dma_map_*()`接口而不是`pci_map_*()`接口。
首先，请确保您的驱动程序中包含了：

	#include <linux/dma-mapping.h>

这部分提供了`dma_addr_t`类型的定义。这种类型可以保存平台上任何有效的DMA地址，并应在持有从DMA映射函数返回的DMA地址时始终使用它。
哪些内存可以用于DMA？
=======================

您需要了解的第一点是哪些内核内存可以使用DMA映射功能。之前有一套不成文的规定，本节尝试将这些规定明确地记录下来。
如果您通过页分配器（例如`__get_free_page*()`）或通用内存分配器（例如`kmalloc()`或`kmem_cache_alloc()`）获取内存，则可以使用这些函数返回的地址进行DMA操作。
这意味着您不能使用`vmalloc()`返回的内存/地址进行DMA。理论上，可以对`vmalloc()`区域映射的底层内存进行DMA操作，但这需要遍历页表来获取物理地址，并且需要使用类似`__va()`的方法将每个页面转换回内核地址。（注：待我们整合Gerd Knorr提供的通用代码后，请更新此处说明。）

这条规则还意味着您不能使用内核镜像地址（数据/文本/BSS段中的项）、模块镜像地址或堆栈地址进行DMA。这些地址可能被映射在与物理内存完全不同的地方。即使这些类别的内存能够在物理上支持DMA，也需要确保I/O缓冲区是缓存行对齐的。否则，在具有DMA不一致缓存的CPU上，可能会出现缓存行共享问题（数据损坏），因为CPU可能写入一个字，而DMA写入同一缓存行中的另一个字，其中一个可能被覆盖。

此外，这也意味着您不能直接使用`kmap()`调用返回的地址进行DMA操作。这与使用`vmalloc()`类似。
对于块I/O和网络缓冲区呢？块I/O和网络子系统会确保它们使用的缓冲区是适合进行DMA读写的。
DMA寻址能力
==================

默认情况下，内核假定您的设备支持32位的DMA寻址。对于64位能力的设备，需要增加寻址范围；而对于有限制的设备，则需要减少寻址范围。
关于PCI的一个特别说明：PCI-X规范要求PCI-X设备支持所有事务的64位寻址（DAC）。至少有一个平台（SGI SN2）当IO总线处于PCI-X模式时，要求使用64位一致性分配才能正确运行。
为了确保正确运行，您必须设置DMA掩码以告知内核您的设备的DMA寻址能力。
这通过调用`dma_set_mask_and_coherent()`函数来完成：

```c
int dma_set_mask_and_coherent(struct device *dev, u64 mask);
```

此函数将同时为流式和一致性API设置掩码。如果您有一些特殊需求，则可以使用以下两个独立的调用代替：

- 流式映射的设置通过调用`dma_set_mask()`进行：
  
  ```c
  int dma_set_mask(struct device *dev, u64 mask);
  ```

- 一致性分配的设置通过调用`dma_set_coherent_mask()`进行：

  ```c
  int dma_set_coherent_mask(struct device *dev, u64 mask);
  ```

在这里，`dev`是指向您的设备的设备结构的指针，而`mask`是一个位掩码，描述了您的设备支持的地址中的哪些位。通常，您的设备的设备结构嵌入在您设备的特定总线设备结构中。例如，对于PCI设备（`pdev`是指向PCI设备结构的指针），`&pdev->dev`是指向该设备的设备结构的指针。

这些调用通常返回零，表示根据您提供的地址掩码，您的设备可以在该机器上正常执行DMA操作，但如果掩码太小以至于无法在给定系统上支持，则可能会返回错误。如果返回非零值，那么您的设备无法在这个平台上正确地执行DMA操作，尝试这样做会导致未定义的行为。除非`dma_set_mask`系列函数已经成功返回，否则您不应在此设备上使用DMA。

这意味着在失败的情况下，您有两种选择：

1. 如果可能的话，使用某种非DMA模式进行数据传输。
2. 忽略此设备，并不对其进行初始化。

建议您的驱动程序在设置DMA掩码失败时打印一条内核KERN_WARNING消息。这样，如果您的驱动程序用户报告性能不佳或设备甚至未被检测到，您可以要求他们提供内核消息以找出确切原因。

一个24位寻址设备可能会这样做：

```c
if (dma_set_mask_and_coherent(dev, DMA_BIT_MASK(24))) {
    dev_warn(dev, "mydev: No suitable DMA available\n");
    goto ignore_this_device;
}
```

一个标准的64位寻址设备可能会这样做：

```c
dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64))
```

`dma_set_mask_and_coherent()`在DMA_BIT_MASK(64)时永远不会返回失败。典型的错误代码如下所示：

```c
/* 错误的代码 */
if (dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64)))
    dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32))
```

当掩码大于32时，`dma_set_mask_and_coherent()`永远不会返回失败。因此，典型的代码应该是这样的：

```c
/* 推荐的代码 */
if (support_64bit)
    dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64));
else
    dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));
```

如果设备仅支持一致性分配中32位寻址的描述符，但支持流式映射的完整64位，那么它看起来可能是这样的：

```c
if (dma_set_mask(dev, DMA_BIT_MASK(64))) {
    dev_warn(dev, "mydev: No suitable DMA available\n");
    goto ignore_this_device;
}
```

一致性掩码始终能够设置与流式掩码相同或更小的掩码。但是，在罕见情况下，如果设备驱动程序只使用一致性分配，那么需要检查`dma_set_coherent_mask()`的返回值。

最后，如果您的设备只能驱动地址最低24位，您可能会这样做：

```c
if (dma_set_mask(dev, DMA_BIT_MASK(24))) {
    dev_warn(dev, "mydev: 24-bit DMA addressing not available\n");
    goto ignore_this_device;
}
```

当`dma_set_mask()`或`dma_set_mask_and_coherent()`成功并返回零时，内核会保存您提供的这个掩码。内核将在您进行DMA映射时使用这些信息。
这里有一个我们已知的情况，值得在文档中提及。如果你的设备支持多种功能（例如声卡同时提供播放和录音功能），并且这些不同的功能具有不同的DMA地址限制，你可能希望分别探测每个掩码，并仅提供机器能够处理的功能。重要的是，最后一次对`dma_set_mask()`的调用应使用最具体的掩码。

以下是实现这一过程的伪代码示例：

	#define PLAYBACK_ADDRESS_BITS	DMA_BIT_MASK(32)
	#define RECORD_ADDRESS_BITS	DMA_BIT_MASK(24)

	struct my_sound_card *card;
	struct device *dev;

	..
	if (!dma_set_mask(dev, PLAYBACK_ADDRESS_BITS)) {
		card->playback_enabled = 1;
	} else {
		card->playback_enabled = 0;
		dev_warn(dev, "%s: 播放功能因DMA限制而禁用\n",
		       card->name);
	}
	if (!dma_set_mask(dev, RECORD_ADDRESS_BITS)) {
		card->record_enabled = 1;
	} else {
		card->record_enabled = 0;
		dev_warn(dev, "%s: 录音功能因DMA限制而禁用\n",
		       card->name);
	}

这里以声卡为例，因为这类PCI设备往往采用ISA芯片加上PCI前端的方式，从而保留了ISA总线下16MB的DMA地址限制。

### DMA映射类型

有两种类型的DMA映射：

- **一致性DMA映射**：通常在驱动初始化时进行映射，在结束时取消映射，并且硬件应保证设备与CPU可以并行访问数据，并且能够看到对方所做的更新，无需任何显式的软件刷新。
可以将“一致性”理解为“同步”或“一致”。
当前默认是在DMA空间的低32位返回一致性内存。然而，为了未来的兼容性，你应该即使在这种默认情况下也设置一致性掩码。
对于一致性映射使用的良好示例包括：

	- 网络卡DMA环描述符
- SCSI适配器邮箱命令数据结构
- 在主内存中执行的设备固件微代码
这些示例共同要求的一点是：任何CPU向内存的写操作都必须立即对设备可见，反之亦然。一致性映射保证了这一点。
...重要...

一致DMA内存并不排除使用正确的内存屏障。CPU可能会对一致内存的写入操作进行重排序，就像它对普通内存那样。示例：如果设备查看描述符的第一个字之前更新第二个字很重要，你必须做类似下面的操作：

```plaintext
desc->word0 = address;
wmb();
desc->word1 = DESC_VALID;
```

为了在所有平台上获得正确的行为。
此外，在某些平台上，你的驱动可能需要像刷新PCI桥中的写缓冲区那样刷新CPU写缓冲区（例如，在写入寄存器值后读取该寄存器的值）。

- 流式DMA映射通常是为一次DMA传输而映射，之后立即取消映射（除非你使用下面的dma_sync_*），并且硬件可以针对顺序访问进行优化。
可以将“流式”理解为“异步”或“不在一致性域内”。

流式映射适用于以下情况的好例子包括：
  
  - 设备发送/接收的网络缓冲区
  - SCSI设备写入/读取的文件系统缓冲区

设计这种映射类型的接口时考虑到了实现可以根据硬件允许的性能优化进行操作。因此，在使用此类映射时，你必须明确自己想要发生什么。

两种类型的DMA映射都没有来自底层总线的对齐限制，尽管某些设备可能有这样的限制。
此外，具有非DMA一致性缓存的系统在底层缓冲区不与其它数据共享缓行时工作得更好。

使用一致DMA映射
==================

要分配和映射大的（大约为PAGE_SIZE大小）一致DMA区域，你应该这样做：

```plaintext
dma_addr_t dma_handle;

cpu_addr = dma_alloc_coherent(dev, size, &dma_handle, gfp);
```

其中`dev`是一个`struct device *`。这可以在带有GFP_ATOMIC标志的中断上下文中调用。
大小（size）是你希望分配的区域长度，单位是字节。
此例程将为该区域分配RAM，其作用类似于
__get_free_pages()（但接受大小而非页序）。如果你的
驱动程序需要小于一个页面大小的区域，你可能更倾向于使用
下面描述的dma_pool接口。
默认情况下，一致DMA映射接口返回的是可由32位地址访问的DMA地址。
即使设备通过DMA掩码表明它可以访问高32位，
一致分配也仅在通过dma_set_coherent_mask()显式更改了一致DMA掩码后才会
返回大于32位的DMA地址。dma_pool接口同样如此。
dma_alloc_coherent()返回两个值：你可以从CPU访问的虚拟地址和传给
卡的dma句柄。
CPU虚拟地址和DMA地址都
保证对齐到最小PAGE_SIZE顺序，该顺序大于或等于所请求的大小。这种不变性存在（例如）
以确保如果你分配一个小于或等于64千字节的块，你收到的缓冲区范围不会跨越64K边界。
要取消映射并释放此类DMA区域，请调用：

	dma_free_coherent(dev, size, cpu_addr, dma_handle);

其中dev、size与上述调用相同，cpu_addr和
dma_handle是dma_alloc_coherent()返回给你的值。
此函数不得在中断上下文中调用。
如果你的驱动程序需要大量较小的内存区域，你可以编写
自定义代码来细分由dma_alloc_coherent()返回的页面，
或者你可以使用dma_pool API来实现这一点。dma_pool就像
kmem_cache一样，但它使用dma_alloc_coherent()，而不是__get_free_pages()。
此外，它理解常见的硬件对齐约束，
比如队列头需要对齐在N字节边界上。
这样创建一个dma_pool：

	struct dma_pool *pool;

	pool = dma_pool_create(name, dev, size, align, boundary);

“name”用于诊断（就像kmem_cache的名字一样）；dev和size
如上所述。“align”是该类型数据对于设备硬件的对齐要求（以字节表示，必须是2的幂）。
如果你的设备没有边界跨越限制，则传0作为boundary；
传递4096表示从这个池分配的内存不能跨越4K字节边界（但在那种情况下，直接使用dma_alloc_coherent()可能更好）。
从DMA池分配内存如下所示：

```c
cpu_addr = dma_pool_alloc(pool, flags, &dma_handle);
```

其中，如果允许阻塞（即不在中断处理程序中，也不持有SMP锁），`flags` 应设置为 `GFP_KERNEL`；否则，应设置为 `GFP_ATOMIC`。与 `dma_alloc_coherent()` 类似，此函数返回两个值：`cpu_addr` 和 `dma_handle`。

释放从DMA池分配的内存如下所示：

```c
dma_pool_free(pool, cpu_addr, dma_handle);
```

其中，`pool` 是传递给 `dma_pool_alloc()` 的参数，而 `cpu_addr` 和 `dma_handle` 是 `dma_pool_alloc()` 返回的值。此函数可以在中断上下文中调用。

销毁一个DMA池的方法如下：

```c
dma_pool_destroy(pool);
```

在销毁DMA池之前，请确保已通过调用 `dma_pool_free()` 释放了该池中分配的所有内存。此函数不能在中断上下文中调用。

### DMA 方向

本文档后续部分所述接口需要一个DMA方向参数，这是一个整数，可取以下值之一：

- `DMA_BIDIRECTIONAL`
- `DMA_TO_DEVICE`
- `DMA_FROM_DEVICE`
- `DMA_NONE`

如果你知道确切的DMA方向，应该提供它。

- `DMA_TO_DEVICE` 表示“从主存到设备”。
- `DMA_FROM_DEVICE` 表示“从设备到主存”。

这些值表示数据在DMA传输过程中的移动方向。

强烈建议你尽可能精确地指定这个方向。

如果你确实无法确定DMA传输的方向，可以指定 `DMA_BIDIRECTIONAL`。这意味着DMA可以在任一方向上进行。平台保证你可以合法地指定这个值，并且它可以工作，但这可能会以牺牲性能为代价。

`DMA_NONE` 这个值主要用于调试。你可以在确定精确方向之前将它保存在数据结构中，这有助于检测方向跟踪逻辑未能正确设置的情况。

除了潜在的平台特定优化之外，精确指定这个值的另一个好处是便于调试。一些平台实际上具有一个写权限标志，DMA映射可以被标记，类似于用户程序地址空间中的页面保护。当DMA控制器硬件检测到权限设置被违反时，这类平台可以在内核日志中报告错误。
### 只有流式映射指定了方向，一致性映射
隐式地具有一个方向属性设置为
DMA_BIDIRECTIONAL
SCSI 子系统会告诉您在驱动程序正在处理的 SCSI 命令的
'sc_data_direction' 成员中使用的方向
对于网络驱动程序来说，这是一件相对简单的事情。对于发送数据包，
使用 DMA_TO_DEVICE 方向指示符进行映射和取消映射。对于接收数据包，
则相反，使用 DMA_FROM_DEVICE 方向指示符进行映射和取消映射。

### 使用流式 DMA 映射
流式 DMA 映射例程可以从中断上下文中调用。每种映射/取消映射都有两个版本：一种用于映射/取消映射单个内存区域，另一种用于映射/取消映射分散列表。
为了映射一个单独的区域，您可以这样做：

```c
struct device *dev = &my_dev->dev;
dma_addr_t dma_handle;
void *addr = buffer->ptr;
size_t size = buffer->len;

dma_handle = dma_map_single(dev, addr, size, direction);
if (dma_mapping_error(dev, dma_handle)) {
    /*
     * 减少当前 DMA 映射使用量，
     * 延迟并稍后重试或
     * 重置驱动程序
*/
    goto map_error_handling;
}
```

然后取消映射它：

```c
dma_unmap_single(dev, dma_handle, size, direction);
```

您应该在调用 `dma_map_single()` 后调用 `dma_mapping_error()`，因为该函数可能失败并返回错误。这样做可以确保映射代码能在所有 DMA 实现上正确工作，而不依赖于底层实现的具体细节。使用返回的地址而不检查错误可能会导致从恐慌到静默数据损坏的各种故障。`dma_map_page()` 也是如此。
当 DMA 操作完成时，您应该调用 `dma_unmap_single()`，例如，在告知 DMA 转移完成的中断中。

使用 CPU 指针进行单个映射有一个缺点：您不能通过这种方式引用 HIGHMEM 内存。因此，有一对类似于 `dma_{map,unmap}_single()` 的映射/取消映射接口。这些接口处理的是页/偏移量对而不是 CPU 指针。

具体而言：

```c
struct device *dev = &my_dev->dev;
dma_addr_t dma_handle;
struct page *page = buffer->page;
unsigned long offset = buffer->offset;
size_t size = buffer->len;

dma_handle = dma_map_page(dev, page, offset, size, direction);
if (dma_mapping_error(dev, dma_handle)) {
    /*
     * 减少当前 DMA 映射使用量，
     * 延迟并稍后重试或
     * 重置驱动程序
*/
    goto map_error_handling;
}
```
这段代码和描述可以翻译为：

`dma_unmap_page(dev, dma_handle, size, direction);`

这里的 "offset" 指的是在给定页内的字节偏移量。
你应该调用 `dma_mapping_error()`，因为 `dma_map_page()` 可能会失败并返回错误，如在 `dma_map_single()` 的讨论中所述。
当 DMA 活动结束时，你应该调用 `dma_unmap_page()`，例如，在中断通知你 DMA 传输已完成时。
使用分散/聚集列表(scatter/gather lists)时，你可以通过以下方式映射从多个区域收集的区域：

```c
int i;
int count = dma_map_sg(dev, sglist, nents, direction);
struct scatterlist *sg;

for_each_sg(sglist, sg, count, i) {
    hw_address[i] = sg_dma_address(sg);
    hw_len[i] = sg_dma_len(sg);
}
```

其中 `nents` 是 `sglist` 中的条目数量。
实现可以自由地将连续的 `sglist` 条目合并为一个（例如，如果 DMA 映射是以 `PAGE_SIZE` 粒度进行的，则可以在满足第一个条目在页边界结束且第二个条目在页边界开始的情况下将它们合并为一个——实际上这对于那些无法进行分散/聚集或具有非常有限的分散/聚集条目数量的卡来说是一个巨大的优势），并且返回实际映射的 `sg` 条目的数量。失败时返回 0。
然后你应该循环 `count` 次（注意：这可能少于 `nents` 次），并使用 `sg_dma_address()` 和 `sg_dma_len()` 宏来访问之前示例中的 `sg->address` 和 `sg->length`。
要取消映射分散/聚集列表，只需调用：

```c
dma_unmap_sg(dev, sglist, nents, direction);
```

再次强调，确保 DMA 活动已经完成。
**注意**:

`dma_unmap_sg` 调用中的 'nents' 参数必须与你在 `dma_map_sg` 调用中传递的相同，它不应该是指 `dma_map_sg` 返回的 'count' 值。
每次 `dma_map_{single,sg}()` 调用都应该有一个对应的 `dma_unmap_{single,sg}()` 调用，因为 DMA 地址空间是一种共享资源，并且如果你消耗了所有的 DMA 地址可能会导致机器无法使用。
如果你需要多次使用相同的流式 DMA 区域并在 DMA 传输之间接触数据，那么缓冲区需要正确同步，以便 CPU 和设备能够看到最新和正确的 DMA 缓冲区副本。
因此，首先，只需使用 `dma_map_{single,sg}()` 映射它，在每次 DMA 传输后调用： 

```c
dma_sync_single_for_cpu(dev, dma_handle, size, direction);
```

或者：

```c
dma_sync_sg_for_cpu(dev, sglist, nents, direction);
```

根据实际情况选择。然后，如果你想让设备再次访问 DMA 区域，在完成对数据的 CPU 访问后，并在实际将缓冲区交给硬件之前调用：

```c
dma_sync_single_for_device(dev, dma_handle, size, direction);
```

或者：

```c
dma_sync_sg_for_device(dev, sglist, nents, direction);
```

根据实际情况选择。**注意**：

        对于 `dma_sync_sg_for_cpu()` 和 `dma_sync_sg_for_device()` 的 `nents` 参数必须与传递给 `dma_map_sg()` 的相同。它 _不是_ `dma_map_sg()` 返回的计数。
在最后一次 DMA 传输后调用其中一个 DMA 反映射例程 `dma_unmap_{single,sg}()`。如果你从第一次 `dma_map_*()` 调用到 `dma_unmap_*()` 之间没有触碰数据，则你根本不需要调用 `dma_sync_*()` 例程。
下面是伪代码，展示了一个你需要使用 `dma_sync_*()` 接口的情况：

```c
my_card_setup_receive_buffer(struct my_card *cp, char *buffer, int len)
{
    dma_addr_t mapping;

    mapping = dma_map_single(cp->dev, buffer, len, DMA_FROM_DEVICE);
    if (dma_mapping_error(cp->dev, mapping)) {
        /*
         * 减少当前 DMA 映射使用，
         * 延迟并稍后重试或
         * 重置驱动程序
*/
        goto map_error_handling;
    }

    cp->rx_buf = buffer;
    cp->rx_len = len;
    cp->rx_dma = mapping;

    give_rx_buf_to_card(cp);
}

//...

my_card_interrupt_handler(int irq, void *devid, struct pt_regs *regs)
{
    struct my_card *cp = devid;

    //...

    if (read_card_status(cp) == RX_BUF_TRANSFERRED) {
        struct my_card_header *hp;

        /* 检查头部以确定我们是否希望
         * 接受数据。但是先同步
         * DMA 传输与 CPU，以便我们看到更新的内容
*/
        dma_sync_single_for_cpu(&cp->dev, cp->rx_dma,
                                cp->rx_len,
                                DMA_FROM_DEVICE);

        /* 现在检查缓冲区是安全的。 */
        hp = (struct my_card_header *) cp->rx_buf;
        if (header_is_ok(hp)) {
            dma_unmap_single(&cp->dev, cp->rx_dma, cp->rx_len,
                             DMA_FROM_DEVICE);
            pass_to_upper_layers(cp->rx_buf);
            make_and_setup_new_rx_buf(cp);
        } else {
            /* CPU 不应写入
             * DMA_FROM_DEVICE 映射区域，
             * 因此这里不需要 dma_sync_single_for_device()。如果
             * 内存被修改，则在双向映射中需要它
*/
            give_rx_buf_to_card(cp);
        }
    }
}

处理错误
==========

一些架构上的 DMA 地址空间是有限的，可以通过以下方式判断分配失败：

- 检查 `dma_alloc_coherent()` 是否返回 `NULL` 或者 `dma_map_sg` 返回 `0`

- 使用 `dma_mapping_error()` 检查从 `dma_map_single()` 和 `dma_map_page()` 返回的 `dma_addr_t` ：

```c
dma_addr_t dma_handle;

dma_handle = dma_map_single(dev, addr, size, direction);
if (dma_mapping_error(dev, dma_handle)) {
    /*
     * 减少当前 DMA 映射使用，
     * 延迟并稍后重试或
     * 重置驱动程序
*/
    //...
```
以上内容已经翻译为中文。
### 错误处理示例

#### 示例 1：

```c
dma_addr_t dma_handle1;
dma_addr_t dma_handle2;

dma_handle1 = dma_map_single(dev, addr, size, direction);
if (dma_mapping_error(dev, dma_handle1)) {
    // 减少当前 DMA 映射的使用，延迟并稍后重试或重置驱动程序
    goto map_error_handling1;
}
dma_handle2 = dma_map_single(dev, addr, size, direction);
if (dma_mapping_error(dev, dma_handle2)) {
    // 减少当前 DMA 映射的使用，延迟并稍后重试或重置驱动程序
    goto map_error_handling2;
}

// ...

map_error_handling2:
    dma_unmap_single(dma_handle1);
map_error_handling1:
```

#### 示例 2：

```c
// 如果在循环中分配缓冲区，则在检测到映射错误时取消映射所有已映射的缓冲区
dma_addr_t dma_addr;
dma_addr_t array[DMA_BUFFERS];
int save_index = 0;

for (i = 0; i < DMA_BUFFERS; i++) {

    // ...
dma_addr = dma_map_single(dev, addr, size, direction);
    if (dma_mapping_error(dev, dma_addr)) {
        // 减少当前 DMA 映射的使用，延迟并稍后重试或重置驱动程序
        goto map_error_handling;
    }
    array[i].dma_addr = dma_addr;
    save_index++;
}

// ...

map_error_handling:

for (i = 0; i < save_index; i++) {

    // ...
dma_unmap_single(array[i].dma_addr);
}
```

### 网络驱动程序必须调用 `dev_kfree_skb()` 来释放套接字缓冲区，并在 DMA 映射在发送钩子 (`ndo_start_xmit`) 失败时返回 `NETDEV_TX_OK`。这意味着，在失败的情况下，套接字缓冲区将被丢弃。

### SCSI 驱动程序必须在 DMA 映射在队列命令钩子中失败时返回 `SCSI_MLQUEUE_HOST_BUSY`。这意味着 SCSI 子系统会在稍后将命令再次传递给驱动程序。
优化取消映射状态空间消耗
========================================

在许多平台上，dma_unmap_{single,page}() 实际上是一个空操作（no-op）。
因此，记录映射地址和长度会浪费空间。与其用 ifdefs 等填充驱动程序来“解决”这个问题（这将违背可移植 API 的初衷），不如使用下面提供的功能。

实际上，我们不逐一描述这些宏，而是通过一些示例代码进行转换：

1) 在状态保存结构中使用 DEFINE_DMA_UNMAP_{ADDR,LEN}
例如，之前是：

```c
    struct ring_state {
        struct sk_buff *skb;
        dma_addr_t mapping;
        __u32 len;
    };
```

之后变为：

```c
    struct ring_state {
        struct sk_buff *skb;
        DEFINE_DMA_UNMAP_ADDR(mapping);
        DEFINE_DMA_UNMAP_LEN(len);
    };
```

2) 使用 dma_unmap_{addr,len}_set() 来设置这些值
例如，之前是：

```c
    ringp->mapping = FOO;
    ringp->len = BAR;
```

之后变为：

```c
    dma_unmap_addr_set(ringp, mapping, FOO);
    dma_unmap_len_set(ringp, len, BAR);
```

3) 使用 dma_unmap_{addr,len}() 来访问这些值
例如，之前是：

```c
    dma_unmap_single(dev, ringp->mapping, ringp->len,
                     DMA_FROM_DEVICE);
```

之后变为：

```c
    dma_unmap_single(dev,
                     dma_unmap_addr(ringp, mapping),
                     dma_unmap_len(ringp, len),
                     DMA_FROM_DEVICE);
```

这应该很容易理解。我们分别处理 ADDR 和 LEN，因为实现可能只需要地址就能执行取消映射操作。

平台问题
===============

如果你只编写适用于 Linux 的驱动程序，并不维护内核架构端口，则可以跳过到“结束”部分。
1) 散列列表结构要求
如果架构支持 IOMMUs（包括软件 IOMMU），则需要启用 CONFIG_NEED_SG_DMA_LENGTH。
2) ARCH_DMA_MINALIGN

架构必须确保通过 `kmalloc` 分配的缓冲区是 DMA 安全的。驱动程序和子系统依赖于此。如果某个架构不是完全的 DMA 一致性（即硬件不能保证 CPU 缓存中的数据与主存中的数据相同），则必须设置 `ARCH_DMA_MINALIGN`，以使内存分配器确保 `kmalloc` 分配的缓冲区不会与其他缓冲区共享同一个缓存行。例如，可以参考 `arch/arm/include/asm/cache.h`。
请注意，`ARCH_DMA_MINALIGN` 关注的是 DMA 内存对齐约束。您无需担心架构的数据对齐约束（例如关于 64 位对象的对齐约束）。

结束语
======

如果没有众多个人提供的反馈和建议，本文档及其所描述的 API 不会是现在的形式。我们特别想要提及以下几位（排名不分先后）：

- Russell King <rmk@arm.linux.org.uk>
- Leo Dagum <dagum@barrel.engr.sgi.com>
- Ralf Baechle <ralf@oss.sgi.com>
- Grant Grundler <grundler@cup.hp.com>
- Jay Estabrook <Jay.Estabrook@compaq.com>
- Thomas Sailer <sailer@ife.ee.ethz.ch>
- Andrea Arcangeli <andrea@suse.de>
- Jens Axboe <jens.axboe@oracle.com>
- David Mosberger-Tang <davidm@hpl.hp.com>
