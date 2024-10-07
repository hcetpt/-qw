使用交换文件与软件挂起（swsusp）
===============================================

	(C) 2006 Rafael J. Wysocki <rjw@sisk.pl>

Linux 内核处理交换文件的方式几乎与处理交换分区相同，这两种类型的交换区域之间只有两个区别：
(1) 交换文件不必连续，
(2) 交换文件的头部不在保存该文件的分区的第一个块中。
从 swsusp 的角度来看，(1) 不是一个问题，因为这已经由处理交换的代码解决了，但 (2) 必须加以考虑。
原则上，可以借助适当的文件系统驱动程序确定交换文件头部的位置。然而不幸的是，这要求包含交换文件的文件系统必须被挂载，并且如果这个文件系统是日志记录的，则在从磁盘恢复时不能挂载它。因此，为了识别交换文件，swsusp 使用保存该文件的分区名称以及交换文件头部相对于该分区起始位置的偏移量。出于方便考虑，此偏移量以 `<PAGE_SIZE>` 单位表示。

为了使用交换文件与 swsusp 配合工作，你需要执行以下步骤：

1) 创建交换文件并使其处于活动状态，例如：::

    # dd if=/dev/zero of=<swap_file_path> bs=1024 count=<swap_file_size_in_k>
    # mkswap <swap_file_path>
    # swapon <swap_file_path>

2) 使用一个应用程序通过 FIBMAP ioctl 映射交换文件并确定文件交换头部的位置，作为从保存交换文件的分区开始处的偏移量（以 `<PAGE_SIZE>` 单位表示）。
3) 在内核命令行中添加以下参数：::

    resume=<swap_file_partition> resume_offset=<swap_file_offset>

其中 `<swap_file_partition>` 是保存交换文件的分区，而 `<swap_file_offset>` 是由第 2 步中的应用程序确定的交换头部偏移量（当然，此步骤可以通过使用 FIBMAP ioctl 确定交换文件头部偏移量的同一应用程序自动完成）。

或者

使用用户空间挂起应用程序通过 Documentation/power/userland-swsusp.rst 中描述的 SNAPSHOT_SET_SWAP_AREA ioctl 设置分区和偏移量（这是唯一允许从 initrd 或 initramfs 图像启动恢复的方法）。
现在，swsusp 将以与使用交换分区相同的方式使用交换文件。特别是，交换文件必须处于活动状态（即存在于 /proc/swaps 中），才能用于挂起。
请注意，如果用于挂起的交换文件被删除并重新创建，其头部的位置可能与之前不同。因此，每次发生这种情况时，必须更新内核命令行参数 `"resume_offset="` 的值。
