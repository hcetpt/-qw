使用交换文件进行软件挂起(swsusp)
===============================================

	(C) 2006 Rafael J. Wysocki <rjw@sisk.pl>

Linux 内核处理交换文件的方式几乎与处理交换分区相同，这两种类型的交换区域之间只有两个区别：
(1) 交换文件不必连续，
(2) 交换文件的头部不在持有该文件的分区的第一个块中。
从swsusp的角度来看，(1)不是问题，因为这已经由处理交换的代码解决，但(2)必须被考虑在内。

原则上，可以通过适当的文件系统驱动程序确定交换文件头部的位置。然而，不幸的是，这需要持有交换文件的文件系统被挂载，如果这个文件系统是日志式的，那么在从磁盘恢复时就不能被挂载。因此，为了识别交换文件，swsusp使用持有该文件的分区名称和交换文件头部相对于分区开始处的偏移量。为了方便起见，这个偏移量以<页面大小>为单位表示。

为了使用交换文件与swsusp，你需要：

1) 创建交换文件并使其活跃，例如：::

    # dd if=/dev/zero of=<swap_file_path> bs=1024 count=<swap_file_size_in_k>
    # mkswap <swap_file_path>
    # swapon <swap_file_path>

2) 使用一个应用程序，通过FIBMAP ioctl映射交换文件并确定文件的交换头部位置，作为从持有交换文件的分区开始的<页面大小>单位的偏移量。
3) 在内核命令行中添加以下参数：::

    resume=<swap_file_partition> resume_offset=<swap_file_offset>

其中<swap_file_partition>是放置交换文件的分区，<swap_file_offset>是由第2步中的应用程序确定的交换头部的偏移量（当然，这一步可以由同一应用程序自动完成，该应用程序使用FIBMAP ioctl确定交换文件头部的偏移量）

或者

使用用户空间挂起应用，通过Documentation/power/userland-swsusp.rst中描述的SNAPSHOT_SET_SWAP_AREA ioctl设置分区和偏移量（这是唯一允许从initrd或initramfs镜像启动恢复的方法）
现在，swsusp将以与使用交换分区相同的方式使用交换文件。特别是，交换文件必须处于活动状态（即在/proc/swaps中），以便用于挂起。
请注意，如果用于挂起的交换文件被删除并重新创建，其头部的位置可能与之前不同。因此，每当这种情况发生时，必须更新"resume_offset="内核命令行参数的值。
