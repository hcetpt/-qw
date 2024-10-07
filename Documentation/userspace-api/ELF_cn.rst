SPDX许可证标识符: GPL-2.0

==============================
Linux特有的ELF特殊处理
==============================

定义
====

“第一个”程序头是在文件中偏移量最小的程序头：
e_phoff
“最后一个”程序头是在文件中偏移量最大的程序头：
e_phoff + (e_phnum - 1) * sizeof(Elf_Phdr)

PT_INTERP
=========

第一个PT_INTERP程序头用于定位ELF解释器的文件名。其他PT_INTERP头将被忽略（自Linux 2.4.11起）

PT_GNU_STACK
============

最后一个PT_GNU_STACK程序头定义了用户空间栈的可执行性（自Linux 2.6.6起）。其他PT_GNU_STACK头将被忽略

PT_GNU_PROPERTY
===============

ELF解释器的最后一个PT_GNU_PROPERTY程序头被使用（自Linux 5.8起）。如果解释器没有该头，则使用可执行文件的最后一个PT_GNU_PROPERTY程序头。其他PT_GNU_PROPERTY头将被忽略
