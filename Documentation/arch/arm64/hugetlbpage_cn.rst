 HugeTLBpage 在 ARM64 上的应用

 Hugepage 依赖于高效利用 TLB（Translation Lookaside Buffer）来提高地址转换的性能。其好处取决于以下两个因素：

  - Hugepage 的大小
  - TLB 支持的条目大小

ARM64 端口支持两种类型的 Hugepage：
1) 在 PUD/PMD 层级上的块映射
--------------------------------------

这些是常规的 Hugepage，其中 PMD 或 PUD 页表条目指向一块内存。无论 TLB 支持的条目大小如何，块映射减少了用于转换 Hugepage 地址所需的页表遍历深度。
2) 使用连续位
---------------------------

架构在翻译表条目中提供了一个连续位（D4.5.3, ARM DDI 0487C.a），该位向 MMU（Memory Management Unit）提示这是一个连续的条目集的一部分，可以被缓存在一个 TLB 条目中。
在 Linux 中，连续位用于增加 PMD 和 PTE（最后一级）的映射大小。支持的连续条目的数量随页大小和页表层级的不同而不同。
以下是支持的 Hugepage 大小：

  ====== ========   ====    ========    ===
  -      CONT PTE    PMD    CONT PMD    PUD
  ====== ========   ====    ========    ===
  4K:         64K     2M         32M     1G
  16K:         2M    32M          1G
  64K:         2M   512M         16G
  ====== ========   ====    ========    ===

注：表格中的“CONT PTE”、“PMD”、“CONT PMD”和“PUD”分别代表使用连续位的页表末级（Page Table Entry）、页中间目录（Page Middle Directory）、使用连续位的页中间目录以及页上级目录（Page Upper Directory）。
