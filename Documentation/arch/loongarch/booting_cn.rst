SPDX 许可证标识符: GPL-2.0

=======================
启动 Linux/LoongArch
=======================

:作者: 司彦腾 <siyanteng@loongson.cn>
:日期:   2022年11月18日

从启动加载器传递到内核的信息
============================================

LoongArch 支持 ACPI 和 FDT。需要传递给内核的信息包括内存映射（memmap）、初始 RAM 磁盘（initrd）、命令行，可选地还包括 ACPI/FDT 表等。
内核在 `kernel_entry` 上接收到以下参数：

      - a0 = efi_boot: `efi_boot` 是一个标志，指示此启动环境是否完全符合 UEFI 标准
- a1 = cmdline: `cmdline` 指向内核命令行
- a2 = systemtable: `systemtable` 指向 EFI 系统表
此时涉及的所有指针都处于物理地址中
Linux/LoongArch 内核镜像的头部
=======================================

Linux/LoongArch 内核镜像是 EFI 镜像。作为 PE 文件，它们有一个结构化的 64 字节头部如下所示:

	u32 MZ_MAGIC                /* "MZ", MS-DOS 头部 */
	u32 res0 = 0                /* 保留 */
	u64 kernel_entry            /* 内核入口点 */
	u64 _end - _text            /* 内核镜像实际大小 */
	u64 load_offset             /* 内核镜像加载偏移量，从 RAM 开始位置计算 */
	u64 res1 = 0                /* 保留 */
	u64 res2 = 0                /* 保留 */
	u64 res3 = 0                /* 保留 */
	u32 LINUX_PE_MAGIC          /* 魔术数字 */
	u32 pe_header - _head       /* PE 头部的偏移量 */
