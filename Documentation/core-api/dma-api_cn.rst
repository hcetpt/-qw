============================================
使用通用设备进行动态DMA映射
============================================

:作者: James E.J. Bottomley <James.Bottomley@HansenPartnership.com>

本文档描述了DMA API。若要了解更温和的API介绍（以及实际示例），请参阅Documentation/core-api/dma-api-howto.rst。
此API分为两部分。第一部分描述基本API；第二部分描述了支持非一致性内存机器的扩展。除非您确定您的驱动程序必须支持非一致性平台（这通常仅限于遗留平台），否则您应该只使用第一部分中描述的API。

第一部分 - dma_API
-------------------

为了使用dma_API，您需要`#include <linux/dma-mapping.h>`。这提供了`dma_addr_t`类型和下面描述的接口。
`dma_addr_t`可以保存平台上的任何有效DMA地址。它可以提供给设备作为DMA源或目标使用。CPU不能直接引用`dma_addr_t`，因为可能需要在它的物理地址空间与DMA地址空间之间进行转换。

第一部分a - 使用大型DMA一致缓冲区
------------------------------------------

```
void *
dma_alloc_coherent(struct device *dev, size_t size,
                   dma_addr_t *dma_handle, gfp_t flag)
```

一致性内存是指设备或处理器写入的数据可以立即被处理器或设备读取而无需担心缓存效果的内存。（但是，在告知设备读取该内存之前，您可能需要确保清空处理器的写缓冲区。）

此函数分配一个大小为<size>字节的一致性内存区域。
它返回指向所分配区域（在处理器虚拟地址空间内）的指针，如果分配失败则返回NULL。
它还返回一个<dma_handle>，该句柄可以转换为与总线宽度相同的无符号整数，并提供给设备作为该区域的DMA地址基址。
注意：在某些平台上，一致性内存可能很昂贵，并且最小分配长度可能与一页一样大，因此您应尽可能合并对一致性内存的请求。
最简单的方法是使用dma_pool调用（见下文）。
### 参数说明：标志(flag)参数（仅适用于`dma_alloc_coherent()`）
允许调用者为分配指定`GFP_`标志（参见`kmalloc()`）（实现可以选择忽略那些影响返回内存位置的标志，例如GFP_DMA）

```c
void
dma_free_coherent(struct device *dev, size_t size, void *cpu_addr,
                  dma_addr_t dma_handle)
```

释放之前分配的一致性内存区域。`dev`、`size`和`dma_handle`必须与传递给`dma_alloc_coherent()`的相同。`cpu_addr`必须是`dma_alloc_coherent()`返回的虚拟地址。
注意与它们的同系列分配函数不同的是，这些函数只能在IRQ启用的情况下被调用。

#### 部分Ib - 使用小DMA一致性缓冲区

为了使用这部分DMA API，你需要包含 `<linux/dmapool.h>`。

许多驱动程序需要大量的小DMA一致性内存区域来作为DMA描述符或I/O缓冲区。与其使用`dma_alloc_coherent()`以一页或更多为单位进行分配，你可以使用DMA池。这些工作方式类似于`struct kmem_cache`，不同之处在于它们使用DMA一致性分配器而不是`__get_free_pages()`。此外，它们还理解常见的硬件对齐要求，比如队列头需要按N字节边界对齐：

```c
struct dma_pool *
dma_pool_create(const char *name, struct device *dev,
                size_t size, size_t align, size_t alloc);
```

`dma_pool_create()`初始化一个用于特定设备的DMA一致性缓冲区池。它必须在一个可以睡眠的上下文中被调用。
“name”用于诊断（如同`struct kmem_cache`的名字）；`dev`和`size`与你传递给`dma_alloc_coherent()`的相同。设备对此类数据的硬件对齐要求为“align”（以字节表示，并且必须是2的幂）。如果你的设备没有跨越边界限制，则为`alloc`传递0；传递4096表示从该池中分配的内存不能跨越4千字节的边界。

```c
void *
dma_pool_zalloc(struct dma_pool *pool, gfp_t mem_flags,
                dma_addr_t *handle)
```

这个函数封装了`dma_pool_alloc()`，并在分配尝试成功时将返回的内存清零。

```c
void *
dma_pool_alloc(struct dma_pool *pool, gfp_t gfp_flags,
               dma_addr_t *dma_handle);
```

这个函数从池中分配内存；返回的内存会满足创建时指定的大小和对齐要求。传递`GFP_ATOMIC`以防止阻塞，或者如果允许（不在中断处理程序中，不持有SMP锁），则传递`GFP_KERNEL`以允许阻塞。像`dma_alloc_coherent()`一样，这个函数返回两个值：一个可用于CPU的地址和一个可用于池设备的DMA地址。

```c
void
dma_pool_free(struct dma_pool *pool, void *vaddr,
              dma_addr_t addr);
```

这个函数将内存放回池中。`pool`是你传递给`dma_pool_alloc()`的池；CPU (`vaddr`) 和 DMA 地址是当该函数分配要释放的内存时返回的。

```c
void
dma_pool_destroy(struct dma_pool *pool);
```

`dma_pool_destroy()`释放池的资源。它必须在一个可以睡眠的上下文中被调用。确保在销毁池之前已经将所有分配的内存释放回池中。
### 第一部分Ic - DMA地址限制

:::

```c
int
dma_set_mask_and_coherent(struct device *dev, u64 mask)
```

检查掩码是否可行，并在可行的情况下更新设备的流式传输和一致性DMA掩码参数。
返回值：成功时返回0，失败时返回负数错误代码。

:::

```c
int
dma_set_mask(struct device *dev, u64 mask)
```

检查掩码是否可行，并在可行的情况下更新设备参数。
返回值：成功时返回0，失败时返回负数错误代码。

:::

```c
int
dma_set_coherent_mask(struct device *dev, u64 mask)
```

检查掩码是否可行，并在可行的情况下更新设备参数。
返回值：成功时返回0，失败时返回负数错误代码。

:::

```c
u64
dma_get_required_mask(struct device *dev)
```

此API返回平台为了高效运行所必需的掩码。通常这意味着返回的掩码是最小必需的，以覆盖所有内存。检查所需掩码为具有可变描述符大小的驱动程序提供了使用较小描述符的机会（如果需要的话）。
请求所需掩码不会改变当前掩码。如果你想利用它，应该调用`dma_set_mask()`来将掩码设置为返回的值。

:::

```c
size_t
dma_max_mapping_size(struct device *dev);
```

返回设备映射的最大尺寸。映射函数（如`dma_map_single()`、`dma_map_page()`等）的尺寸参数不应大于返回的值。

:::

```c
size_t
dma_opt_mapping_size(struct device *dev);
```

返回设备映射的最大最优尺寸。
在某些情况下，映射较大的缓冲区可能需要更长的时间。此外，对于高频率且生命周期较短的流式传输映射，映射操作所花费的前置时间可能会占据总请求生命周期的相当一部分。因此，如果分割较大的请求不会带来显著的性能损失，则建议设备驱动程序将总的DMA流式传输映射长度限制为返回值：

```c
bool
dma_need_sync(struct device *dev, dma_addr_t dma_addr);
```

如果需要通过`dma_sync_single_for_{device,cpu}`调用来转移内存所有权，则返回%true；如果这些调用可以省略，则返回%false。

```c
unsigned long
dma_get_merge_boundary(struct device *dev);
```

返回DMA合并边界。如果设备无法合并任何DMA地址段，则该函数返回0。

### 部分ID - 流式DMA映射

```c
dma_addr_t
dma_map_single(struct device *dev, void *cpu_addr, size_t size,
               enum dma_data_direction direction)
```

映射一段处理器虚拟内存，以便设备能够访问，并返回该内存的DMA地址。
方向参数可以自由转换类型，但是`dma_API`使用了一个强类型的枚举器来表示其方向：

| 枚举值            | 描述                                         |
|-------------------|----------------------------------------------|
| `DMA_NONE`        | 没有方向（用于调试）                         |
| `DMA_TO_DEVICE`   | 数据从内存流向设备                           |
| `DMA_FROM_DEVICE` | 数据从设备流向内存                           |
| `DMA_BIDIRECTIONAL`| 方向未知                                     |

**注意：**

并非机器中的所有内存区域都可以通过此API进行映射。此外，连续的内核虚拟空间可能不是物理上连续的。由于此API没有提供任何分散/聚集能力，如果用户尝试映射一个非物理连续的内存块，它将会失败。因此，要被此API映射的内存应该来自那些保证其物理连续性的来源（例如kmalloc）。

进一步地，内存的DMA地址必须位于设备的`dma_mask`内（`dma_mask`是一个位掩码，表示设备可寻址的区域，即如果内存的DMA地址与`dma_mask`进行按位与运算后仍等于该DMA地址，则表明设备可以对该内存执行DMA操作）。为了确保kmalloc分配的内存位于`dma_mask`内，驱动程序可以指定各种平台相关的标志来限制分配的DMA地址范围（例如，在x86上，GFP_DMA保证位于前16MB可用的DMA地址范围内，这是ISA设备的要求）。

请注意，如果平台具有IOMMU（一种将I/O DMA地址映射到物理内存地址的设备），则上述关于物理连续性和`dma_mask`的约束可能不适用。然而，为了保证可移植性，设备驱动程序编写者不能假设存在这样的IOMMU。

**警告：**

内存一致性是以称为缓存行宽度的粒度运行的。为了使通过此API映射的内存正确运行，映射的区域必须正好位于缓存行边界开始和结束（以防止两个独立映射的区域共享同一个缓存行）。由于缓存行大小可能在编译时不知道，API不会强制执行这一要求。因此，建议那些没有特别小心地在运行时确定缓存行大小的驱动程序编写者仅映射那些开始和结束于页边界的虚拟区域（这些区域也保证是缓存行边界）。
### DMA_TO_DEVICE 同步

DMA_TO_DEVICE 的同步必须在软件最后一次修改内存区域后，并在将其传递给设备之前完成。一旦使用此原语，被此原语覆盖的内存应被视为只读，由设备处理。如果设备在任何时刻可能写入它，则应设置为 DMA_BIDIRECTIONAL（见下文）。

### DMA_FROM_DEVICE 同步

DMA_FROM_DEVICE 的同步必须在驱动程序访问可能被设备更改的数据之前完成。这部分内存应该被驱动程序视为只读。如果驱动程序需要在任何时刻写入它，则应设置为 DMA_BIDIRECTIONAL（见下文）。

### DMA_BIDIRECTIONAL 需要特殊处理

这意味着驱动程序不确定内存是否在传递给设备前被修改过，也不确定设备是否会修改它。因此，你必须总是同步双向内存两次：一次是在内存传递给设备之前（以确保所有内存更改都从处理器中刷新），另一次是在数据可能被设备使用后访问之前（以确保任何处理器缓存行都已更新为设备可能更改的数据）。

### 函数定义

#### `dma_unmap_single`

```c
void
dma_unmap_single(struct device *dev, dma_addr_t dma_addr, size_t size,
                 enum dma_data_direction direction)
```

取消映射先前映射的区域。传递的所有参数必须与映射API传递（和返回）的相同。

#### `dma_map_page` 和 `dma_unmap_page`

```c
dma_addr_t
dma_map_page(struct device *dev, struct page *page,
             unsigned long offset, size_t size,
             enum dma_data_direction direction)

void
dma_unmap_page(struct device *dev, dma_addr_t dma_address, size_t size,
               enum dma_data_direction direction)
```

用于页面的映射和取消映射的API。关于其他映射API的所有注意事项和警告同样适用于此。此外，虽然提供了 `<offset>` 和 `<size>` 参数来执行部分页面映射，但建议除非你确实了解缓存宽度，否则不要使用这些参数。

#### `dma_map_resource` 和 `dma_unmap_resource`

```c
dma_addr_t
dma_map_resource(struct device *dev, phys_addr_t phys_addr, size_t size,
                 enum dma_data_direction dir, unsigned long attrs)

void
dma_unmap_resource(struct device *dev, dma_addr_t addr, size_t size,
                   enum dma_data_direction dir, unsigned long attrs)
```

用于MMIO资源的映射和取消映射的API。关于其他映射API的所有注意事项和警告同样适用于此。此API仅应用于映射设备MMIO资源，不允许映射RAM。

#### `dma_mapping_error`

```c
int
dma_mapping_error(struct device *dev, dma_addr_t dma_addr)
```

在某些情况下，`dma_map_single()`、`dma_map_page()` 和 `dma_map_resource()` 可能无法创建映射。驱动程序可以通过使用 `dma_mapping_error()` 检查返回的DMA地址来检查这些错误。非零返回值意味着无法创建映射，驱动程序应采取适当行动（例如减少当前DMA映射使用或延迟并稍后再试）。

#### `dma_map_sg`

```c
int
dma_map_sg(struct device *dev, struct scatterlist *sg,
           int nents, enum dma_data_direction direction)
```

返回：映射的DMA地址段数（这可能比传入的 `<nents>` 短，如果散列/聚集列表的一些元素在物理上或虚拟上相邻，并且IOMMU用单个条目映射它们）。请注意，如果已经映射过sg，则不能再次映射它。映射过程允许破坏sg中的信息。
如同其他的映射接口，`dma_map_sg()` 也可能失败。当它失败时，会返回0，此时驱动程序必须采取适当的措施。对于块设备驱动来说，关键在于必须做些什么：即使中止请求或触发 oops（内核错误）也比什么都不做而导致文件系统损坏要好。
在使用分散列表时，您会像下面这样使用生成的映射：

```c
int i, count = dma_map_sg(dev, sglist, nents, direction);
struct scatterlist *sg;

for_each_sg(sglist, sg, count, i) {
    hw_address[i] = sg_dma_address(sg);
    hw_len[i] = sg_dma_len(sg);
}
```

其中 `nents` 是 `sglist` 中的条目数量。
实现可以自由地将连续的多个 `sglist` 条目合并为一个（例如，通过 IOMMU 或者如果多页恰好物理上连续），并返回实际映射到的 `sg` 条目的数量。如果失败，则返回0。
然后你应该循环 `count` 次（注意：这可能少于 `nents` 次），并使用 `sg_dma_address()` 和 `sg_dma_len()` 宏来访问之前 `sg->address` 和 `sg->length` 的内容。

```c
void
dma_unmap_sg(struct device *dev, struct scatterlist *sg,
             int nents, enum dma_data_direction direction)
```

取消先前映射的分散/聚集列表。所有参数都必须与传递给分散/聚集映射 API 的参数相同。

请注意：`<nents>` 必须是你传递的原始数字，而不是返回的 DMA 地址条目的数量。

```c
void
dma_sync_single_for_cpu(struct device *dev, dma_addr_t dma_handle,
                        size_t size,
                        enum dma_data_direction direction)

void
dma_sync_single_for_device(struct device *dev, dma_addr_t dma_handle,
                           size_t size,
                           enum dma_data_direction direction)

void
dma_sync_sg_for_cpu(struct device *dev, struct scatterlist *sg,
                    int nents,
                    enum dma_data_direction direction)

void
dma_sync_sg_for_device(struct device *dev, struct scatterlist *sg,
                       int nents,
                       enum dma_data_direction direction)
```

同步单个连续的或分散/聚集映射供 CPU 和设备使用。使用 `sync_sg` API 时，所有参数必须与传递给分散/聚集映射 API 的参数相同。使用 `sync_single` API 时，您可以使用 `dma_handle` 和 `size` 参数来进行部分同步，这些参数不必与传递给单个映射 API 的参数完全相同。

**注意**：
- 在读取由设备 DMA 写入的数据前（使用 `DMA_FROM_DEVICE` 方向）
- 在写入将被 DMA 写入设备的数据后（使用 `DMA_TO_DEVICE` 方向）
- 在将内存交给设备前后，如果内存是双向的 (`DMA_BIDIRECTIONAL`)，你必须执行这些操作。

更多关于 `dma_map_single()` 的信息：

```c
dma_addr_t
dma_map_single_attrs(struct device *dev, void *cpu_addr, size_t size,
                     enum dma_data_direction dir,
                     unsigned long attrs)

void
dma_unmap_single_attrs(struct device *dev, dma_addr_t dma_addr,
                       size_t size, enum dma_data_direction dir,
                       unsigned long attrs)

int
dma_map_sg_attrs(struct device *dev, struct scatterlist *sgl,
                 int nents, enum dma_data_direction dir,
                 unsigned long attrs)

void
dma_unmap_sg_attrs(struct device *dev, struct scatterlist *sgl,
                   int nents, enum dma_data_direction dir,
                   unsigned long attrs)
```

上述四个函数与没有 `_attrs` 后缀的对应函数相同，只是它们接受了一个可选的 `dma_attrs` 参数。
DMA 属性的解释是架构特定的，并且每个属性都应该在 `Documentation/core-api/dma-attributes.rst` 文件中有详细的说明。
如果 dma_attrs 为 0，这些函数的语义与相应没有 _attrs 后缀的函数相同。因此，dma_map_single_attrs() 通常可以替换 dma_map_single() 等。

作为使用 ``*_attrs`` 函数的一个例子，以下是当为 DMA 映射内存时如何传递属性 DMA_ATTR_FOO 的示例：

```c
#include <linux/dma-mapping.h>
/* DMA_ATTR_FOO 应该在 linux/dma-mapping.h 中定义，并且在 Documentation/core-api/dma-attributes.rst 中有文档说明 */
...
unsigned long attr;
attr |= DMA_ATTR_FOO;
...
n = dma_map_sg_attrs(dev, sg, nents, DMA_TO_DEVICE, attr);
...
```

关心 DMA_ATTR_FOO 的架构会在它们实现的映射和取消映射例程中检查它的存在，例如：

```c
void whizco_dma_map_sg_attrs(struct device *dev, dma_addr_t dma_addr,
			     size_t size, enum dma_data_direction dir,
			     unsigned long attrs)
{
	...
	if (attrs & DMA_ATTR_FOO)
		/* 调整 frobnozzle */
	...
}
```

### 第二部分 - 非一致性 DMA 分配

这些 API 允许分配被保证可以通过传入设备进行 DMA 地址访问的页面，但需要显式管理内核与设备之间的内存所有权。
如果你不了解处理器与 I/O 设备之间缓存行一致性的工作原理，则不应该使用此 API 的这一部分。

```c
struct page *
dma_alloc_pages(struct device *dev, size_t size, dma_addr_t *dma_handle,
		enum dma_data_direction dir, gfp_t gfp)
```

这个例程分配了一个大小为 `<size>` 字节的非一致性内存区域。它返回指向该区域第一个 `struct page` 的指针，如果分配失败则返回 NULL。所得到的 `struct page` 可以用于任何适合 `struct page` 的用途。

它还返回一个 `<dma_handle>`，可以将其转换为与总线宽度相同的无符号整数，并作为该区域的 DMA 地址基提供给设备。
`dir` 参数指定了设备是否读取和/或写入数据，具体细节请参阅 `dma_map_single()`。

`gfp` 参数允许调用者为分配指定“GFP_”标志（参见 `kmalloc()`），但拒绝使用如 GFP_DMA 或 GFP_HIGHMEM 这类用于指定内存区域的标志。

在将内存交给设备之前，需要调用 `dma_sync_single_for_device()`；而在读取设备写入的内存之前，则需要调用 `dma_sync_single_for_cpu()`，这与重用的流式 DMA 映射相同。

```c
void
dma_free_pages(struct device *dev, size_t size, struct page *page,
               dma_addr_t dma_handle, enum dma_data_direction dir)
```

释放之前使用 `dma_alloc_pages()` 分配的内存区域。`dev`、`size`、`dma_handle` 和 `dir` 必须与传递给 `dma_alloc_pages()` 的参数相同。`page` 必须是 `dma_alloc_pages()` 返回的指针。

```c
int
dma_mmap_pages(struct device *dev, struct vm_area_struct *vma,
               size_t size, struct page *page)
```

将 `dma_alloc_pages()` 返回的分配映射到用户地址空间中。`dev` 和 `size` 必须与传递给 `dma_alloc_pages()` 的参数相同。`page` 必须是 `dma_alloc_pages()` 返回的指针。

```c
void *
dma_alloc_noncoherent(struct device *dev, size_t size,
                      dma_addr_t *dma_handle, enum dma_data_direction dir,
                      gfp_t gfp)
```

此函数为 `dma_alloc_pages()` 提供了一个方便的包装器，返回分配内存的内核虚拟地址，而不是页面结构。

```c
void
dma_free_noncoherent(struct device *dev, size_t size, void *cpu_addr,
                     dma_addr_t dma_handle, enum dma_data_direction dir)
```

释放之前使用 `dma_alloc_noncoherent()` 分配的内存区域。
以下是对提供的英文文档的中文翻译：

---

### 函数定义

```c
struct sg_table * 
dma_alloc_noncontiguous(struct device *dev, size_t size,
				enum dma_data_direction dir, gfp_t gfp,
				unsigned long attrs);
```

此函数分配 `<size>` 字节的非一致性且可能非连续的内存。它返回指向描述已分配并进行 DMA 映射内存的 `struct sg_table` 的指针，如果分配失败则返回 `NULL`。所得到的内存可用于结构体页面映射到散列列表中，适合于...

返回的 `sg_table` 结构保证具有 1 个由 `sgt->nents` 指示的单个 DMA 映射段，但它可能有多个由 `sgt->orig_nents` 指示的 CPU 侧段。

`dir` 参数指定设备读取和/或写入数据的方向，具体细节请参阅 `dma_map_single()`。

`gfp` 参数允许调用者为分配指定 `GFP_` 标志（参见 `kmalloc()`），但拒绝使用如 `GFP_DMA` 或 `GFP_HIGHMEM` 这样的标志来指定内存区域。

`attrs` 参数应为 0 或 `DMA_ATTR_ALLOC_SINGLE_PAGES`。

在将内存交给设备之前，需要调用 `dma_sync_sgtable_for_device()`；而在读取设备写入的内存之前，则需要调用 `dma_sync_sgtable_for_cpu()`，就像处理被重用的流式 DMA 映射一样。

---

### 释放内存

```c
void 
dma_free_noncontiguous(struct device *dev, size_t size,
			       struct sg_table *sgt,
			       enum dma_data_direction dir)
```

释放使用 `dma_alloc_noncontiguous()` 之前分配的内存。`dev`、`size` 和 `dir` 必须与传递给 `dma_alloc_noncontiguous()` 的相同。`sgt` 必须是 `dma_alloc_noncontiguous()` 返回的指针。

---

### 创建内核映射

```c
void * 
dma_vmap_noncontiguous(struct device *dev, size_t size,
		struct sg_table *sgt)
```

为通过 `dma_alloc_noncontiguous()` 分配的内存创建一个连续的内核映射。`dev` 和 `size` 必须与传递给 `dma_alloc_noncontiguous()` 的相同。`sgt` 必须是 `dma_alloc_noncontiguous()` 返回的指针。
一旦使用此函数映射了非连续分配的内存，则必须使用 flush_kernel_vmap_range() 和 invalidate_kernel_vmap_range() API 来管理内核映射、设备和用户空间映射（如果存在）之间的一致性。

:: 

    void
    dma_vunmap_noncontiguous(struct device *dev, void *vaddr)

取消映射由 dma_vmap_noncontiguous() 返回的内核映射。dev 必须与传递给 dma_alloc_noncontiguous() 的相同。vaddr 必须是由 dma_vmap_noncontiguous() 返回的指针。

::

    int
    dma_mmap_noncontiguous(struct device *dev, struct vm_area_struct *vma,
                           size_t size, struct sg_table *sgt)

将由 dma_alloc_noncontiguous() 分配的内存映射到用户地址空间。dev 和 size 必须与传递给 dma_alloc_noncontiguous() 的相同。sgt 必须是由 dma_alloc_noncontiguous() 返回的指针。

::

    int
    dma_get_cache_alignment(void)

返回处理器缓存对齐值。这是在映射内存或进行部分刷新时必须遵守的绝对最小对齐值和宽度。
.. note:: 

    此 API 可能返回比实际缓存行更大的数字，但它可以保证一个或多个缓存行恰好适合此调用返回的宽度。它也将始终是2的幂，以便于对齐。

第三部分 - 使用 DMA-API 进行驱动程序调试
-------------------------------------------

如上所述的 DMA-API 具有一些限制。例如，DMA 地址必须使用具有相同大小的相应函数释放。随着硬件 IOMMU 的出现，确保驱动程序不违反这些约束变得越来越重要。最坏的情况下，这种违规可能导致数据损坏甚至文件系统被破坏。
为了调试驱动程序并发现 DMA-API 使用中的错误，可以在内核中编译检查代码来告知开发人员这些违规行为。如果你的架构支持，你可以在内核配置中选择“启用 DMA-API 使用的调试”选项。启用此选项会带来性能影响。请不要在生产内核中启用它。
如果你启动了带有此选项的内核，其中将包含一些关于为哪个设备分配了哪些 DMA 内存的记录代码。如果此代码检测到错误，它将在你的内核日志中打印一条警告消息，并附带一些详细信息。一个示例警告消息可能如下所示：

:: 

    WARNING: at /data2/repos/linux-2.6-iommu/lib/dma-debug.c:448
        check_unmap+0x203/0x490()
    Hardware name:
    forcedeth 0000:00:08.0: DMA-API: 设备驱动程序使用错误的函数释放 DMA 内存 [设备地址=0x00000000640444be] [大小=66 字节] [以单个方式映射] [以页方式取消映射]
    Modules linked in: nfsd exportfs bridge stp llc r8169
    Pid: 0, comm: swapper Tainted: G        W  2.6.28-dmatest-09289-g8bb99c0 #1
    Call Trace:
    <IRQ>  [<ffffffff80240b22>] warn_slowpath+0xf2/0x130
    [<ffffffff80647b70>] _spin_unlock+0x10/0x30
    [<ffffffff80537e75>] usb_hcd_link_urb_to_ep+0x75/0xc0
    [<ffffffff80647c22>] _spin_unlock_irqrestore+0x12/0x40
    [<ffffffff8055347f>] ohci_urb_enqueue+0x19f/0x7c0
    [<ffffffff80252f96>] queue_work+0x56/0x60
    [<ffffffff80237e10>] enqueue_task_fair+0x20/0x50
    [<ffffffff80539279>] usb_hcd_submit_urb+0x379/0xbc0
    [<ffffffff803b78c3>] cpumask_next_and+0x23/0x40
    [<ffffffff80235177>] find_busiest_group+0x207/0x8a0
    [<ffffffff8064784f>] _spin_lock_irqsave+0x1f/0x50
    [<ffffffff803c7ea3>] check_unmap+0x203/0x490
    [<ffffffff803c8259>] debug_dma_unmap_page+0x49/0x50
    [<ffffffff80485f26>] nv_tx_done_optimized+0xc6/0x2c0
    [<ffffffff80486c13>] nv_nic_irq_optimized+0x73/0x2b0
    [<ffffffff8026df84>] handle_IRQ_event+0x34/0x70
    [<ffffffff8026ffe9>] handle_edge_irq+0xc9/0x150
    [<ffffffff8020e3ab>] do_IRQ+0xcb/0x1c0
    [<ffffffff8020c093>] ret_from_intr+0x0/0xa
    <EOI> <4>---[ end trace f6435a98e2a38c0e ]---

驱动程序开发人员可以通过跟踪导致此警告的 DMA-API 调用找到驱动程序及其设备。
默认情况下，只有第一个错误会产生警告消息。所有其他错误只会被默默地计数。此限制的存在是为了防止代码淹没你的内核日志。为了支持调试设备驱动程序，这可以通过 debugfs 禁用。有关详细信息，请参见下面的 debugfs 接口文档。
DMA-API 调试代码的 debugfs 目录称为 dma-api/。在此目录中，目前可以找到以下文件：

=============================== ===============================================
dma-api/all_errors		此文件包含一个数值。如果该值不等于零，则调试代码将为它发现的每个错误在内核日志中打印一条警告。请注意此选项，因为它很容易淹没你的日志。
dma-api/disabled	此只读文件包含字符 'Y'  
				如果调试代码被禁用。这可能发生在  
				内存耗尽时或在启动时被禁用。

dma-api/dump		此只读文件包含当前的DMA  
				映射信息。
dma-api/error_count	此文件为只读，显示发现的总错误  
				数量。
dma-api/num_errors	此文件中的数字表示在停止之前将打印到  
				内核日志的警告数量。此数值在系统启动时初始化为一，  
				并且可以通过写入此文件来设置。

dma-api/min_free_entries	此只读文件可以用来获取分配器曾经看到的  
				最小空闲 dma_debug_entries 数量。如果此值降至零，  
				代码将尝试增加 nr_total_entries 来补偿。
dma-api/num_free_entries	分配器中当前空闲的 dma_debug_entries 数量。
dma-api/nr_total_entries	分配器中的总 dma_debug_entries 数量，包括已使用和未使用的。
dma-api/driver_filter		您可以在此文件中写入驱动程序名称来限制  
				仅显示来自该特定驱动程序的调试输出。写入一个空字符串  
				以禁用过滤器并再次查看所有错误。

================================== ==============================================

如果您已将此代码编译到您的内核中，则默认情况下它将被启用。
如果您无论如何想要在没有这些账目记录的情况下启动，您可以在启动参数中提供
'dma_debug=off'。这将禁用 DMA-API 调试功能。
请注意，您不能在运行时再次启用它。您必须重启才能实现。
如果您只想查看特定设备驱动程序的调试消息，您可以指定
dma_debug_driver=<drivername> 参数。这将在启动时启用驱动程序过滤器。之后，调试代码仅会为此驱动程序打印错误。此过滤器可以稍后通过 debugfs 禁用或更改。
当代码在运行时自行禁用时，这很可能是因为它耗尽了`dma_debug_entries`并且无法按需分配更多。在启动时预分配了65536个条目——如果这个数字对你来说太低，可以在启动时使用`dma_debug_entries=<你期望的数字>`来覆盖默认值。请注意，代码是分批分配这些条目的，因此实际预分配的条目数量可能大于请求的数量。每当动态分配的条目数量达到初始预分配的数量时，代码会向内核日志打印信息。这是为了提示可能需要更大的预分配大小，或者如果这种情况持续发生，则可能是驱动程序存在内存映射泄漏。

:: 

    void 
    debug_dma_mapping_error(struct device *dev, dma_addr_t dma_addr);

`dma-debug`接口`debug_dma_mapping_error()`用于调试那些未能检查通过`dma_map_single()`和`dma_map_page()`接口返回地址的DMA映射错误的驱动程序。此接口清除由`debug_dma_map_page()`设置的一个标志，该标志指示驱动程序已经调用了`dma_mapping_error()`。当驱动程序进行反映射时，`debug_dma_unmap()`会检查这个标志；如果该标志仍然被设置，它会打印一条警告消息，其中包含导致反映射操作的调用追踪。此接口可以从`dma_mapping_error()`例程中调用，以启用DMA映射错误检查调试。
