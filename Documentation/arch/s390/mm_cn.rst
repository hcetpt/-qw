### SPDX 许可证标识符: GPL-2.0

#### 内存管理

##### 虚拟内存布局

**注释:**

- 虚拟内存布局设置中的一些方面尚未明确（页表层级的数量、对齐方式、DMA内存）。
- 在虚拟内存布局中的未使用间隙可能存在也可能不存在，这取决于特定系统的配置方式。
- 对于未使用的间隙不创建页表。
- 虚拟内存区域被 KASAN 工具跟踪或不跟踪，以及 KASAN 的影子内存仅在启用了 CONFIG_KASAN 配置选项时才创建。

```
=============================================================================
|   物理地址       |    虚拟地址     | VM 区域描述
=============================================================================
+-- 0 ------------+-- 0 ------------+
|                | S390_lowcore    | 低地址内存
|                +-- 8 KB ---------+
|                |                |
|                |                |
|                | ... 未使用间隙 | KASAN 不跟踪
|                |                |
+-- AMODE31_START+-- AMODE31_START+ .amode31 随机物理/虚拟起始
|.amode31 文本/数据|.amode31 文本/数据| KASAN 不跟踪
+-- AMODE31_END ---+-- AMODE31_END ---+ .amode31 随机物理/虚拟结束（<2GB）
|                |                |
|                |                |
+-- __kaslr_offset_phys         | 内核随机物理起始
|                |                |
| 内核文本/数据  |                |
|                |                |
+----------------+                | 内核物理结束
|                |                |
|                |                |
|                |                |
|                |                |
|                +-- ident_map_size+                |
|                |                |
|                | ... 未使用间隙 | KASAN 不跟踪
|                |                |
|                +-- __identity_base + 身份映射起始（>= 2GB）
|                |                |
| 身份            | 物理 == 虚拟 - __identity_base
| 映射            | 虚拟 == 物理 + __identity_base
|                |                |
|                |                | KASAN 跟踪
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
|                |                |
+---- vmemmap ----+ 'struct page' 数组起始
|                |
| 虚拟映射        |
| 内存映射        | KASAN 不跟踪
|                |
+-- __abs_lowcore --+
|                |
| 绝对 Lowcore    | KASAN 不跟踪
|                |
+-- __memcpy_real_area
|                |
| 实际内存复制    | KASAN 不跟踪
|                |
+-- VMALLOC_START --+ vmalloc 区域起始
|                | KASAN 不跟踪 或者
| vmalloc 区域    | 如果 CONFIG_KASAN_VMALLOC=y，则 KASAN 浅填充
|                |
+-- MODULES_VADDR --+ 模块区域起始
|                | 每个模块分配 KASAN 或者
| 模块区域        | 如果 CONFIG_KASAN_VMALLOC=y，则 KASAN 浅填充
|                |
+-- __kaslr_offset -+ 内核随机虚拟起始
|                | 物理 == (kvirt - __kaslr_offset) + __kaslr_offset_phys
| 内核文本/数据  |
|                | KASAN 跟踪
+-- 内核 .bss 结束 + 内核随机虚拟结束
|                |
| ... 未使用间隙 | KASAN 不跟踪
|                |
+----------------+ UltraVisor 安全存储限制
|                |
| ... 未使用间隙 | KASAN 不跟踪
|                |
+KASAN_SHADOW_START+ KASAN 影子内存起始
|                |
| KASAN 影子     | KASAN 不跟踪
|                |
+----------------+ ASCE 限制
```
