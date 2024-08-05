===== 端口 =====

摘自列表存档：http://lists.arm.linux.org.uk/pipermail/linux-arm-kernel/2001-July/004064.html

初始定义
--------

以下符号定义依赖于您了解 __virt_to_phys() 对您的机器执行的转换。此宏将传递的虚拟地址转换为物理地址。通常，它是这样的：

        物理地址 = 虚拟地址 - PAGE_OFFSET + PHYS_OFFSET


解压缩器符号
-------------

ZTEXTADDR
解压缩器的起始地址。在这里讨论虚拟或物理地址没有意义，因为在调用解压缩器代码时MMU将是关闭状态。通常，您会在该地址调用内核以启动其引导过程。这不一定必须位于RAM中，它可以位于闪存或其他只读或可读写的寻址介质中。
ZBSSADDR
解压缩器零初始化工作区的起始地址
这必须指向RAM。解压缩器会为您零初始化这部分区域。同样，MMU将被关闭。
ZRELADDR
这是解压后的内核将被写入并最终执行的地址。以下约束必须有效：

        __virt_to_phys(TEXTADDR) == ZRELADDR

内核的初始部分经过精心编码以实现位置无关性。
INITRD_PHYS
初始RAM磁盘的物理地址。仅在使用 bootpImage 功能时相关（这仅适用于旧版 struct param_struct）
INITRD_VIRT
初始RAM磁盘的虚拟地址。以下约束必须有效：

        __virt_to_phys(INITRD_VIRT) == INITRD_PHYS

PARAMS_PHYS
struct param_struct 或标签列表的物理地址，向内核提供关于其执行环境的各种参数

内核符号
--------

PHYS_OFFSET
第一块RAM的物理起始地址
PAGE_OFFSET
第一块RAM的虚拟起始地址。在内核引导阶段，虚拟地址 PAGE_OFFSET 将映射到物理地址 PHYS_OFFSET，以及您提供的任何其他映射
这应该与 TASK_SIZE 的值相同
TASK_SIZE
用户进程的最大字节数。由于用户空间始终从零开始，这是用户进程可以访问的最大地址加1。用户空间堆栈从这个地址向下增长
任何低于 `TASK_SIZE` 的虚拟地址都被认为是用户进程区域，因此由内核按进程动态管理。我将此称为用户段。

高于 `TASK_SIZE` 的一切对所有进程都是通用的。我将其称为内核段。
（换句话说，你不能在 `TASK_SIZE` 以下设置 I/O 映射，因此也就没有 `PAGE_OFFSET`）

`TEXTADDR`
内核的虚拟起始地址，通常为 `PAGE_OFFSET + 0x8000`。
这是内核镜像最终所在的位置。对于最新内核而言，
它必须位于一个128MB区域内的32768字节处。早期内核在此处的限制为256MB。

`DATAADDR`
内核数据段的虚拟地址。使用解压缩器时不得定义该值。

`VMALLOC_START` / `VMALLOC_END`
界定 `vmalloc()` 区域的虚拟地址。此区域内不得存在任何静态映射；`vmalloc` 将会覆盖它们。
这些地址也必须位于内核段中（参见上述内容）。
通常情况下，`vmalloc()` 区域从最后一个虚拟RAM地址（通过变量 `high_memory` 找到）之上 `VMALLOC_OFFSET` 字节处开始。

`VMALLOC_OFFSET`
通常被纳入 `VMALLOC_START` 中以在虚拟RAM和 `vmalloc` 区域之间留出空隙的偏移量。我们这样做是为了能够捕获越界内存访问（例如，某些操作超出已映射内存范围的末尾写入）。通常设置为8MB。
特定架构的宏定义
----------------------------

BOOT_MEM(pram, pio, vio)
  `pram` 指定了 RAM 的物理起始地址。必须始终存在，并且应该与 PHYS_OFFSET 相同。
`pio` 是包含用于与 arch/arm/kernel/debug-armv.S 中调试宏配合使用的 I/O 区域的 8MB 区域的物理地址。
`vio` 是 8MB 调试区域的虚拟地址。
期望架构特定代码在后续部分通过 MAPIO 函数重新初始化调试区域。
BOOT_PARAMS
  与 PARAMS_PHYS 相同，参见 PARAMS_PHYS。
FIXUP(func)
  机器特定的修复程序，在内存子系统被初始化之前运行。
MAPIO(func)
  机器特定的函数，用于映射 I/O 区域（包括上面提到的调试区域）。
INITIRQ(func)
  机器特定的函数，用于初始化中断。
