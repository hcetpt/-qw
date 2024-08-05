==============================
ARM Linux 内核初始化参数
==============================

以下文档描述了内核初始化参数结构，通常称为`struct param_struct`，该结构被大多数ARM Linux架构使用。
此结构用于从内核加载器向Linux内核传递初始化参数，并且可能在内核初始化过程中短暂存在。一般而言，除了在`arch/arm/kernel/setup.c:setup_arch()`之外，不应引用它。
下面列出了许多参数，并对它们进行了描述：

 page_size
   此参数必须设置为机器的页面大小，并将由内核进行检查。
nr_pages
   这是系统中内存页的总数。如果内存分段，则应包含系统中的总页数。
   如果系统包含独立的VRAM，此值不应包括这些信息。
ramdisk_size
   此项现已废弃，不应再使用。
flags
   各种内核标志，包括：

    =====   ========================
    第0位   1 = 以只读方式挂载根分区
    第1位   未使用
    第2位   0 = 加载ramdisk
    第3位   0 = 提示输入ramdisk
    =====   ========================

 rootdev
   作为根文件系统的设备的主要/次要编号对。
video_num_cols / video_num_rows
   这两个值一起描述了哑终端（dummy console）或VGA控制台字符大小。它们不应用于其他任何目的。
   通常最好将其设置为标准VGA或与您的fbcon显示等效的字符大小。这样可以确保所有启动消息正确显示。
video_x / video_y
   这描述了VGA控制台上光标的位置，除此之外未被使用。（不应用于其他类型的控制台，也不应用于其他用途）
以下是提供的英文术语及其翻译：

- `memc_control_reg`: MEMC 控制寄存器，用于 Acorn Archimedes 和 Acorn A5000 基础机器的 MEMC 芯片控制寄存器。可能在不同的架构中使用方式不同。
- `sounddefault`: Acorn 机器默认的声音设置。可能在不同的架构中使用方式不同。
- `adfsdrives`: ADFS/MFM 磁盘的数量。可能在不同的架构中使用方式不同。
- `bytes_per_char_h` / `bytes_per_char_v`: 这些设置现在已经过时，不应再使用。
- `pages_in_bank[4]`: 系统内存中每个内存库（bank）的页数（用于 RiscPC）。此值旨在用于从处理器角度看物理内存不连续的系统中。
- `pages_in_vram`: VRAM 中的页数（用于 Acorn RiscPC）。如果无法从硬件获取视频 RAM 的大小，加载程序也可能使用这个值。
- `initrd_start` / `initrd_size`: 描述初始 ramdisk 在内核虚拟地址空间中的起始地址和大小。
- `rd_start`: ramdisk 镜像在软盘上的扇区起始地址。
- `system_rev`: 系统修订号。
翻译如下：

- `system_serial_low` / `system_serial_high`
   系统64位序列号

- `mem_fclk_21285`
   这是外部振荡器到21285（脚桥）的速度，它控制着内存总线、定时器和串行端口的速度。
   根据CPU的速度，其值可以在0-66 MHz之间。如果没有传递参数或传递的值为零，则在21285架构上默认值为50 MHz。

- `paths[8][128]`
   这些现在已过时，不应再使用。

- `commandline`
   内核命令行参数。详细信息可在其他地方找到。
