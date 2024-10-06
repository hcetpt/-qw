实时补丁模块的 ELF 格式
===========================

本文档概述了实时补丁模块必须遵循的 ELF 格式要求。

.. 目录

.. contents:: :local:

1. 背景和动机
============================

以前，实时补丁需要独立的架构特定代码来写入重定位。然而，模块加载器中已经存在用于写入重定位的架构特定代码，因此这种旧方法产生了冗余代码。为了避免复制代码并重新实现模块加载器已经可以做的事情，实时补丁利用了模块加载器中现有的代码来执行所有架构特定的重定位工作。具体来说，实时补丁重用了模块加载器中的 apply_relocate_add() 函数来写入重定位。本文档中描述的补丁模块 ELF 格式使实时补丁能够做到这一点。希望这将使实时补丁更容易移植到其他架构，并减少将实时补丁移植到特定架构所需的架构特定代码量。由于 apply_relocate_add() 需要访问模块的节头表、符号表和重定位节索引，因此实时补丁模块保留了 ELF 信息（见第 5 节）。实时补丁管理自己的重定位节和符号，这些在本文档中有所描述。用于标记实时补丁符号和重定位节的 ELF 常量是从 glibc 定义的操作系统特定范围内选择的。

为什么实时补丁需要写入自己的重定位？
-----------------------------------------------------
一个典型的实时补丁模块包含修补过的函数版本，这些函数可能引用非导出的全局符号和未包含的局部符号。针对这些类型的符号的重定位不能保持原样，因为内核模块加载器无法解析它们并因此会拒绝实时补丁模块。此外，在补丁模块加载时我们不能应用影响尚未加载的模块的重定位（例如，对尚未加载的驱动程序进行的修补）。以前，实时补丁通过在生成的补丁模块 ELF 输出中嵌入特殊的 "dynrela"（动态 rela）节来解决这个问题。使用这些 dynrela 节，实时补丁可以根据符号的作用域及其所属模块来解析符号，并手动应用动态重定位。然而这种方法要求实时补丁提供架构特定的代码来写入这些重定位。在新的格式中，实时补丁用 SHT_RELA 重定位节替换了 dynrela 节，并且重定位引用的符号是特殊的实时补丁符号（见第 2 和 3 节）。架构特定的实时补丁重定位代码被替换为调用 apply_relocate_add()。

2. 实时补丁 modinfo 字段
==========================

实时补丁模块必须具有 "livepatch" 的 modinfo 属性。
请参阅 samples/livepatch/ 中的示例实时补丁模块以了解如何设置。
用户可以通过使用 'modinfo' 命令并查找 "livepatch" 字段的存在来识别实时补丁模块。此字段也由内核模块加载器用来识别实时补丁模块。
示例：
--------

**Modinfo 输出：**

::

	% modinfo livepatch-meminfo.ko
	filename:		livepatch-meminfo.ko
	livepatch:		Y
	license:		GPL
	depends:
	vermagic:		4.3.0+ SMP mod_unload

3. 实时补丁重定位节
================================

实时补丁模块管理自己的 ELF 重定位节，以便在适当的时间对模块以及内核（vmlinux）应用重定位。例如，如果补丁模块修补了一个当前未加载的驱动程序，那么实时补丁将在驱动程序加载时应用相应的实时补丁重定位节。
每个“对象”（例如 vmlinux 或一个模块）在补丁模块中可能有多个实时补丁重定位节与之关联（例如同一对象中多个函数的修补）。实时补丁重定位节与其所应用的目标节（通常是函数的文本节）之间是一对一的对应关系。实时补丁模块也可能没有实时补丁重定位节，如示例实时补丁模块所示（见 samples/livepatch）。
由于实时补丁模块保留了ELF信息（见第5节），通过传递适当的节索引给`apply_relocate_add()`函数，可以简单地应用实时补丁重定位节，该函数随后使用这个索引来访问重定位节并应用重定位。
每个在实时补丁重定位节中引用的符号都是一个实时补丁符号。在实时补丁调用`apply_relocate_add()`之前，必须先解析这些符号。更多信息请参阅第3节。

### 3.1 实时补丁重定位节格式
实时补丁重定位节必须标记为SHF_RELA_LIVEPATCH节标志。具体定义请参阅include/uapi/linux/elf.h。模块加载器会识别此标志，并在加载补丁模块时避免应用这些重定位节。这些节还必须标记为SHF_ALLOC，以防止模块加载器在加载模块时丢弃它们（即它们将与其它SHF_ALLOC节一起被复制到内存中）。

实时补丁重定位节名称必须遵循以下格式：

```
.klp.rela.objname.section_name
^        ^^     ^ ^          ^
|________||_____| |__________|
     [A]      [B]        [C]
```

[A]
  重定位节名称前缀为字符串".klp.rela."

[B]
  紧跟前缀之后是该重定位节所属的对象名称（例如"vmlinux"或模块名称）

[C]
  此重定位节所适用的实际节名称

### 示例：
#### 实时补丁重定位节名称：

```
.klp.rela.ext4.text.ext4_attr_store
.klp.rela.vmlinux.text.cmdline_proc_show
```

#### `readelf --sections`输出示例（用于修补vmlinux和模块9p、btrfs、ext4）：

```
Section Headers:
[Nr] Name                          Type                    Address          Off    Size   ES Flg Lk Inf Al
[省略]
[29] .klp.rela.9p.text.caches.show RELA                    0000000000000000 002d58 0000c0 18 AIo 64   9  8
[30] .klp.rela.btrfs.text.btrfs.feature.attr.show RELA     0000000000000000 002e18 000060 18 AIo 64  11  8
[省略]
[34] .klp.rela.ext4.text.ext4.attr.store RELA              0000000000000000 002fd8 0000d8 18 AIo 64  13  8
[35] .klp.rela.ext4.text.ext4.attr.show RELA               0000000000000000 0030b0 000150 18 AIo 64  15  8
[36] .klp.rela.vmlinux.text.cmdline.proc.show RELA         0000000000000000 003200 000018 18 AIo 64  17  8
[37] .klp.rela.vmlinux.text.meminfo.proc.show RELA         0000000000000000 003218 0000f0 18 AIo 64  19  8
[省略]
```

[*]
  实时补丁重定位节是SHT_RELA节，但具有几个特殊特性。注意它们标记了SHF_ALLOC（"A"），以便在模块加载到内存时不会被丢弃，并且还标记了SHF_RELA_LIVEPATCH标志（"o" - 操作系统特定标志）

#### `readelf --relocs`输出示例（用于补丁模块）：

```
Relocation section '.klp.rela.btrfs.text.btrfs_feature_attr_show' at offset 0x2ba0 contains 4 entries:
Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
000000000000001f  0000005e00000002 R_X86_64_PC32          0000000000000000 .klp.sym.vmlinux.printk,0 - 4
0000000000000028  0000003d0000000b R_X86_64_32S           0000000000000000 .klp.sym.btrfs.btrfs_ktype,0 + 0
0000000000000036  0000003b00000002 R_X86_64_PC32          0000000000000000 .klp.sym.btrfs.can_modify_feature.isra.3,0 - 4
000000000000004c  0000004900000002 R_X86_64_PC32          0000000000000000 .klp.sym.vmlinux.snprintf,0 - 4
[省略]
```

[*]
  每个由重定位引用的符号都是一个实时补丁符号

### 4. 实时补丁符号
实时补丁符号是指由实时补丁重定位节引用的符号。
这些符号是从修补对象的新版本函数中访问的，其地址无法由模块加载器解析（因为它们是本地的或未导出的全局符号）。由于模块加载器只解析导出的符号，并非所有新修补函数引用的符号都已导出，因此引入了实时补丁符号。在某些情况下，我们无法立即知道补丁模块加载时某个符号的地址。例如，当实时补丁修补尚未加载的模块时，相关实时补丁符号会在目标模块加载时简单地解析。无论如何，对于任何实时补丁重定位节，在实时补丁调用`apply_relocate_add()`之前，该节中引用的所有实时补丁符号都必须解析完毕。
实时补丁符号必须标记为SHN_LIVEPATCH，以便模块加载器能够识别并忽略它们。实时补丁模块在其符号表中保留这些符号，并通过`module->symtab`使符号表可访问。
### 4.1 实时补丁模块的符号表
通常，一个模块的符号表（仅包含“核心”符号）的精简副本会通过 `module->symtab` 提供（参见 `kernel/module/kallsyms.c` 中的 `layout_symtab()`）。对于实时补丁模块，加载模块时复制到内存中的符号表必须与编译补丁模块时生成的符号表完全相同。这是因为每个实时补丁重定位节中的重定位条目都是通过它们的符号索引来引用各自的符号，并且原始符号索引（以及因此的 `symtab` 排序）必须保持不变，以便 `apply_relocate_add()` 能够找到正确的符号。

例如，考虑以下特定的重定位条目：

```
重定位节 '.klp.rela.btrfs.text.btrfs_feature_attr_show' 在偏移量 0x2ba0 处包含 4 个条目：
    偏移量               信息              类型                 符号值        符号名 + 增量
000000000000001f  0000005e00000002 R_X86_64_PC32          0000000000000000 .klp.sym.vmlinux.printk,0 - 4

此重定位条目指的是符号 '.klp.sym.vmlinux.printk,0'，符号索引编码在 'Info' 字段中。这里它的符号索引为 0x5e，即十进制数 94，指向符号索引 94。
在该补丁模块对应的符号表中，符号索引 94 指向的就是这个符号：
[省略]
94: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT OS [0xff20] .klp.sym.vmlinux.printk,0
[省略]
```

### 4.2 实时补丁符号格式

实时补丁符号的节索引必须标记为 `SHN_LIVEPATCH`，以便模块加载器能够识别它们并且不尝试解析它们。请参阅 `include/uapi/linux/elf.h` 获取实际定义。

实时补丁符号名称必须符合以下格式：

```
.klp.sym.objname.symbol_name,sympos
^       ^^     ^ ^         ^ ^
|_______||_____| |_________| |
     [A]     [B]       [C]    [D]

[A]
  符号名称前缀为字符串 ".klp.sym."

[B]
  对应对象（即 "vmlinux" 或模块名称）的名称紧跟在前缀之后

[C]
  符号的实际名称

[D]
  符号在对象中的位置（根据 `kallsyms`）
  这用于区分同一对象中的重复符号。符号位置用数值表示（0, 1, 2...）
  唯一符号的位置为 0
```

示例：

**实时补丁符号名称：**

```
.klp.sym.vmlinux.snprintf,0
.klp.sym.vmlinux.printk,0
.klp.sym.btrfs.btrfs_ktype,0
```

**使用 `readelf --symbols` 输出的补丁模块：**

```
符号表 '.symtab' 包含 127 个条目：
     Num:    Value          Size Type    Bind   Vis     Ndx         Name
     [省略]
      73: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT OS [0xff20] .klp.sym.vmlinux.snprintf,0
      74: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT OS [0xff20] .klp.sym.vmlinux.capable,0
      75: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT OS [0xff20] .klp.sym.vmlinux.find_next_bit,0
      76: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT OS [0xff20] .klp.sym.vmlinux.si_swapinfo,0
    [省略]
```

[*]
  注意这些符号的 'Ndx'（节索引）为 `SHN_LIVEPATCH`（0xff20）
  “OS” 表示操作系统特定信息
5. 符号表和 ELF 区段访问
=============================
一个热补丁模块的符号表可以通过 `module->symtab` 访问。
由于 `apply_relocate_add()` 需要访问模块的区段头、符号表和重定位区段索引，因此热补丁模块的 ELF 信息会被保留，并通过模块加载器提供的 `module->klp_info` 进行访问，`module->klp_info` 是一个 `klp_modinfo` 结构体。当一个热补丁模块加载时，这个结构体会由模块加载器填充。
