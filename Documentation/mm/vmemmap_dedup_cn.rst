SPDX 许可证标识符：GPL-2.0

=========================================
为 HugeTLB 和设备 DAX 设计的 vmemmap 膳食
=========================================

HugeTLB
=======

本节旨在解释 HugeTLB Vmemmap 优化（HVO）的工作原理。`struct page` 结构用于描述一个物理页框。默认情况下，页框与其对应的 `struct page` 存在一对一映射关系。HugeTLB 页由多个基本页大小的页组成，并且得到了许多架构的支持。有关更多详细信息，请参阅 Documentation/admin-guide/mm/hugetlbpage.rst。在 x86-64 架构中，目前支持 2MB 和 1GB 大小的 HugeTLB 页。由于 x86 上的基本页大小为 4KB，因此 2MB 的 HugeTLB 页包含 512 个基本页，而 1GB 的 HugeTLB 页包含 262144 个基本页。对于每个基本页，都有一个相应的 `struct page`。

在 HugeTLB 子系统中，只有前 4 个 `struct page` 用于包含关于 HugeTLB 页的独特信息。`__NR_USED_SUBPAGE` 提供了这个上限。剩余 `struct page` 中唯一“有用”的信息是 compound_head 字段，而此字段对于所有尾页都是相同的。

通过移除冗余的 `struct page`，可以将内存返还给 buddy 分配器以作其他用途。不同架构支持不同大小的 HugeTLB 页。例如，下表列出了 x86 和 arm64 架构支持的 HugeTLB 页大小。因为 arm64 支持 4K、16K 和 64K 基本页，并且支持连续条目，所以它支持多种 HugeTLB 页大小。

+--------------+-----------+-----------------------------------------------+
| 架构         | 页大小   | HugeTLB 页大小                                |
+--------------+-----------+-----------+-----------+-----------+-----------+
| x86-64       | 4KB       | 2MB       | 1GB       |            |            |
+--------------+-----------+-----------+-----------+-----------+-----------+
|              | 4KB       | 64KB      | 2MB       | 32MB      | 1GB       |
|              +-----------+-----------+-----------+-----------+-----------+
| arm64        | 16KB      | 2MB       | 32MB      | 1GB       |            |
|              +-----------+-----------+-----------+-----------+-----------+
|              | 64KB      | 2MB       | 512MB     | 16GB      |            |
+--------------+-----------+-----------+-----------+-----------+-----------+

当系统启动时，每个 HugeTLB 页都有多个 `struct page` 结构，其大小（单位：页）如下所示：

   struct_size = HugeTLB_Size / PAGE_SIZE * sizeof(struct page) / PAGE_SIZE

其中 HugeTLB_Size 是 HugeTLB 页的大小。我们知道 HugeTLB 页的大小总是 PAGE_SIZE 的 n 倍。因此我们可以得出以下关系：

   HugeTLB_Size = n * PAGE_SIZE

然后：

   struct_size = n * PAGE_SIZE / PAGE_SIZE * sizeof(struct page) / PAGE_SIZE
               = n * sizeof(struct page) / PAGE_SIZE

我们可以在 pud/pmd 级别使用巨大的映射来处理 HugeTLB 页。
对于 pmd 级别的 HugeTLB 页映射，则：

   struct_size = n * sizeof(struct page) / PAGE_SIZE
               = PAGE_SIZE / sizeof(pte_t) * sizeof(struct page) / PAGE_SIZE
               = sizeof(struct page) / sizeof(pte_t)
               = 64 / 8
               = 8 (页)

其中 n 表示一页可以包含多少个 pte 条目。因此 n 的值为 (PAGE_SIZE / sizeof(pte_t))。
此优化仅支持 64 位系统，因此 sizeof(pte_t) 的值为 8。此外，此优化也仅适用于 `struct page` 的大小为 2 的幂的情况。在大多数情况下，`struct page` 的大小为 64 字节（例如
x86-64 和 arm64）。因此，如果我们使用页中目录表（pmd）级别的映射来处理一个 HugeTLB 页面，其 `struct page` 结构的大小为 8 个页框，具体大小取决于基础页的大小。
对于 pud 级别映射的 HugeTLB 页面，情况如下：

   struct_size = PAGE_SIZE / sizeof(pmd_t) * struct_size(pmd)
               = PAGE_SIZE / 8 * 8 (pages)
               = PAGE_SIZE (pages)

其中，struct_size(pmd) 是 pmd 级别映射的 HugeTLB 页面的 `struct page` 结构的大小。
例如：在 x86_64 架构上，一个 2MB 的 HugeTLB 页面包含 8 个页框，而 1GB 的 HugeTLB 页面包含 4096 个页框。
接下来，我们以 pmd 级别映射的 HugeTLB 页面为例，展示这种优化的内部实现。一个 pmd 映射的 HugeTLB 页面关联了 8 个 `struct page` 结构。优化前的情况如下：

    HugeTLB                  struct pages(8 pages)         page frame(8 pages)
 +-----------+ ---virt_to_page---> +-----------+   mapping to   +-----------+
 |           |                     |     0     | -------------> |     0     |
 |           |                     +-----------+                +-----------+
 |           |                     |     1     | -------------> |     1     |
 |           |                     +-----------+                +-----------+
 |           |                     |     2     | -------------> |     2     |
 |           |                     +-----------+                +-----------+
 |           |                     |     3     | -------------> |     3     |
 |           |                     +-----------+                +-----------+
 |           |                     |     4     | -------------> |     4     |
 |    PMD    |                     +-----------+                +-----------+
 |   level   |                     |     5     | -------------> |     5     |
 |  mapping  |                     +-----------+                +-----------+
 |           |                     |     6     | -------------> |     6     |
 |           |                     +-----------+                +-----------+
 |           |                     |     7     | -------------> |     7     |
 |           |                     +-----------+                +-----------+
 |           |
 |           |
 |           |
 +-----------+

所有尾页的 page->compound_head 值是相同的。与 HugeTLB 页面关联的第一个 `struct page` （page 0）包含描述 HugeTLB 所需的 4 个 `struct page` 。剩余的 `struct page` （page 1 到 page 7）仅用于指向 page->compound_head。因此，我们可以将 pages 1 到 7 重新映射到 page 0。每个 HugeTLB 页面只使用一个 `struct page` ，这样可以释放其余的 7 个页面给 buddy 分配器。
优化后的示例如下：

    HugeTLB                  struct pages(8 pages)         page frame(8 pages)
 +-----------+ ---virt_to_page---> +-----------+   mapping to   +-----------+
 |           |                     |     0     | -------------> |     0     |
 |           |                     +-----------+                +-----------+
 |           |                     |     1     | ---------------^ ^ ^ ^ ^ ^ ^
 |           |                     +-----------+                  | | | | | |
 |           |                     |     2     | -----------------+ | | | | |
 |           |                     +-----------+                    | | | | |
 |           |                     |     3     | -------------------+ | | | |
 |           |                     +-----------+                      | | | |
 |           |                     |     4     | ---------------------+ | | |
 |    PMD    |                     +-----------+                        | | |
 |   level   |                     |     5     | -----------------------+ | |
 |  mapping  |                     +-----------+                          | |
 |           |                     |     6     | -------------------------+ |
 |           |                     +-----------+                            |
 |           |                     |     7     | ---------------------------+
 |           |                     +-----------+
 |           |
 |           |
 |           |
 +-----------+

当 HugeTLB 页面被释放到 buddy 系统时，我们应该分配 7 个页面作为 vmemmap 页面，并恢复之前的映射关系。
对于 pud 级别映射的 HugeTLB 页面，情况类似。
我们也可以使用这种方法来释放 (PAGE_SIZE - 1) 个 vmemmap 页面。
除了 pmd 或 pud 级别映射的 HugeTLB 页面外，一些架构（如 aarch64）在转换表条目中提供了连续位，这些位提示 MMU 表示这是可以缓存在单个 TLB 条目中的连续条目之一。
连续位用于在PMD和PTE（最后一级）级别增加映射大小。因此，这种类型的HugeTLB页面仅在其`struct page`结构的大小大于**1**页时才能进行优化。
注意：头部vmemmap页面不会释放给伙伴分配器，并且所有尾部vmemmap页面都映射到头部vmemmap页面帧上。因此，我们可以看到每个HugeTLB页面关联有多个`struct page`结构带有`PG_head`（例如，每2MB HugeTLB页面有8个）。`compound_head()`可以正确处理这种情况。只有一个头部`struct page`，带有`PG_head`的尾部`struct page`是假的头部`struct page`。我们需要一种方法来区分这两种不同类型的`struct page`，以便当参数是带有`PG_head`的尾部`struct page`时，`compound_head()`能够返回真实的头部`struct page`。

设备DAX
=======

设备DAX接口使用了与前一章中解释的相同的尾部去重技术，除了在设备中的vmemmap（altmap）使用的情况。
以下页面大小在DAX中受支持：PAGE_SIZE（x86_64上的4K），PMD_SIZE（x86_64上的2M）和PUD_SIZE（x86_64上的1G）。
关于PowerPC等效细节，请参阅Documentation/arch/powerpc/vmemmap_dedup.rst。

与HugeTLB的区别相对较小。
它只使用3个`struct page`来存储所有信息，而HugeTLB页面使用4个。
由于设备DAX内存不是系统RAM范围的一部分，因此不会重新映射vmemmap。因此，在我们填充这些部分时，尾部去重发生在稍后的阶段。HugeTLB重用代表头部vmemmap页面，而设备DAX重用尾部vmemmap页面。这导致与HugeTLB相比只有大约一半的节省。
去重的尾部页面不是只读映射的。
在填充部分之后，设备DAX看起来如下所示：

```
+-----------+ ---virt_to_page---> +-----------+   mapping to   +-----------+
|           |                     |     0     | -------------> |     0     |
|           |                     +-----------+                +-----------+
|           |                     |     1     | -------------> |     1     |
|           |                     +-----------+                +-----------+
|           |                     |     2     | ----------------^ ^ ^ ^ ^ ^
|           |                     +-----------+                   | | | | |
|           |                     |     3     | ------------------+ | | | |
|           |                     +-----------+                     | | | |
|           |                     |     4     | --------------------+ | | |
|    PMD    |                     +-----------+                       | | |
|   level   |                     |     5     | ----------------------+ | |
|  mapping  |                     +-----------+                         | |
|           |                     |     6     | ------------------------+ |
|           |                     +-----------+                           |
|           |                     |     7     | --------------------------+
|           |                     +-----------+
|           |
|           |
|           |
+-----------+
```
