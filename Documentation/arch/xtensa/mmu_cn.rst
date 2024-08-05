=============================
MMUv3 初始化序列
=============================

初始化宏 `initialize_mmu` 中的代码设置 MMUv3 内存映射，与 MMUv2 固定内存映射完全相同。根据 `CONFIG_INITIALIZE_XTENSA_MMU_INSIDE_VMLINUX` 符号，这段代码位于它被链接到的地址（符号未定义），或者不在该位置（符号已定义），因此需要是位置无关的。此段代码有以下假设：

  - 此代码片段仅在 MMU v3 上运行。
- TLB 处于复位状态。
- ITLBCFG 和 DTLBCFG 均为零（复位状态）。
- RASID 为 0x04030201（复位状态）。
- PS.RING 为零（复位状态）。
- LITBASE 为零（复位状态，基于 PC 的文字）；要求为位置无关。

TLB 设置遵循以下步骤：
图例：

    - VA = 虚拟地址（最高两个十六进制位）；
    - PA = 物理地址（最高两个十六进制位）；
    - pc = 包含本代码的物理范围；

步骤 2 之后，我们跳转到虚拟地址范围 0x40000000..0x5fffffff 或者 0x00000000..0x1fffffff，具体取决于内核是否加载在 0x40000000 以下或以上。该地址对应本代码中要执行的下一条指令。步骤 4 之后，我们跳转到此代码预期（链接）的地址。
下面的方案假设内核加载在 0x40000000 以下。
默认的 I/O 外设位置在 0xf0000000 以上。可以通过设备树中的简单总线节点的 "ranges" 属性来改变这一点。关于简单总线节点的语法和语义详情，请参阅设备树规范第 4.5 节。以下限制适用：

1. 只考虑顶层的简单总线节点。
2. 只考虑一个（第一个）简单总线节点。
3. 不支持空的 "ranges" 属性。
4. 只考虑 "ranges" 属性中的第一个三元组。
5. 父总线地址值向下取整到最近的 256MB 边界。
6. I/O 区域覆盖父总线地址的整个 256MB 段；忽略 "ranges" 三元组的长度字段。

MMUv3 地址空间布局
============================

默认的 MMUv2 兼容布局:: 

                        符号                   虚拟地址       大小
  +------------------+
  | 用户空间        |                           0x00000000  TASK_SIZE
  +------------------+                           0x40000000
  +------------------+
  | 页表             |  XCHAL_PAGE_TABLE_VADDR   0x80000000  XCHAL_PAGE_TABLE_SIZE
  +------------------+
  | KASAN 阴影映射   |  KASAN_SHADOW_START       0x80400000  KASAN_SHADOW_SIZE
  +------------------+                           0x8e400000
  +------------------+
  | VMALLOC 区域     |  VMALLOC_START            0xc0000000  128MB - 64KB
  +------------------+  VMALLOC_END
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_1           0xc8000000  DCACHE_WAY_SIZE
  | 重映射区域 1     |
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_2                       DCACHE_WAY_SIZE
  | 重映射区域 2     |
  +------------------+
  +------------------+
  | KMAP 区域        |  PKMAP_BASE                           PTRS_PER_PTE *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  |                  |                                       (4MB * DCACHE_N_COLORS)
  +------------------+
  | 原子 KMAP 区域   |  FIXADDR_START                        KM_TYPE_NR *
  |                  |                                       NR_CPUS *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  +------------------+  FIXADDR_TOP              0xcffff000
  +------------------+
  | 缓存 KSEG        |  XCHAL_KSEG_CACHED_VADDR  0xd0000000  128MB
  +------------------+
  | 未缓存 KSEG      |  XCHAL_KSEG_BYPASS_VADDR  0xd8000000  128MB
  +------------------+
  | 缓存 KIO         |  XCHAL_KIO_CACHED_VADDR   0xe0000000  256MB
  +------------------+
  | 未缓存 KIO       |  XCHAL_KIO_BYPASS_VADDR   0xf0000000  256MB
  +------------------+


256MB 缓存 + 256MB 未缓存布局:: 

                        符号                   虚拟地址       大小
  +------------------+
  | 用户空间        |                           0x00000000  TASK_SIZE
  +------------------+                           0x40000000
  +------------------+
  | 页表             |  XCHAL_PAGE_TABLE_VADDR   0x80000000  XCHAL_PAGE_TABLE_SIZE
  +------------------+
  | KASAN 阴影映射   |  KASAN_SHADOW_START       0x80400000  KASAN_SHADOW_SIZE
  +------------------+                           0x8e400000
  +------------------+
  | VMALLOC 区域     |  VMALLOC_START            0xa0000000  128MB - 64KB
  +------------------+  VMALLOC_END
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_1           0xa8000000  DCACHE_WAY_SIZE
  | 重映射区域 1     |
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_2                       DCACHE_WAY_SIZE
  | 重映射区域 2     |
  +------------------+
  +------------------+
  | KMAP 区域        |  PKMAP_BASE                           PTRS_PER_PTE *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  |                  |                                       (4MB * DCACHE_N_COLORS)
  +------------------+
  | 原子 KMAP 区域   |  FIXADDR_START                        KM_TYPE_NR *
  |                  |                                       NR_CPUS *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  +------------------+  FIXADDR_TOP              0xaffff000
  +------------------+
  | 缓存 KSEG        |  XCHAL_KSEG_CACHED_VADDR  0xb0000000  256MB
  +------------------+
  | 未缓存 KSEG      |  XCHAL_KSEG_BYPASS_VADDR  0xc0000000  256MB
  +------------------+
  +------------------+
  | 缓存 KIO         |  XCHAL_KIO_CACHED_VADDR   0xe0000000  256MB
  +------------------+
  | 未缓存 KIO       |  XCHAL_KIO_BYPASS_VADDR   0xf0000000  256MB
  +------------------+


512MB 缓存 + 512MB 未缓存布局:: 

                        符号                   虚拟地址       大小
  +------------------+
  | 用户空间        |                           0x00000000  TASK_SIZE
  +------------------+                           0x40000000
  +------------------+
  | 页表             |  XCHAL_PAGE_TABLE_VADDR   0x80000000  XCHAL_PAGE_TABLE_SIZE
  +------------------+
  | KASAN 阴影映射   |  KASAN_SHADOW_START       0x80400000  KASAN_SHADOW_SIZE
  +------------------+                           0x8e400000
  +------------------+
  | VMALLOC 区域     |  VMALLOC_START            0x90000000  128MB - 64KB
  +------------------+  VMALLOC_END
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_1           0x98000000  DCACHE_WAY_SIZE
  | 重映射区域 1     |
  +------------------+
  | 缓存别名         |  TLBTEMP_BASE_2                       DCACHE_WAY_SIZE
  | 重映射区域 2     |
  +------------------+
  +------------------+
  | KMAP 区域        |  PKMAP_BASE                           PTRS_PER_PTE *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  |                  |                                       (4MB * DCACHE_N_COLORS)
  +------------------+
  | 原子 KMAP 区域   |  FIXADDR_START                        KM_TYPE_NR *
  |                  |                                       NR_CPUS *
  |                  |                                       DCACHE_N_COLORS *
  |                  |                                       PAGE_SIZE
  +------------------+  FIXADDR_TOP              0x9ffff000
  +------------------+
  | 缓存 KSEG        |  XCHAL_KSEG_CACHED_VADDR  0xa0000000  512MB
  +------------------+
  | 未缓存 KSEG      |  XCHAL_KSEG_BYPASS_VADDR  0xc0000000  512MB
  +------------------+
  | 缓存 KIO         |  XCHAL_KIO_CACHED_VADDR   0xe0000000  256MB
  +------------------+
  | 未缓存 KIO       |  XCHAL_KIO_BYPASS_VADDR   0xf0000000  256MB
  +------------------+
