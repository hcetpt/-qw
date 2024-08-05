======================
s390 SCSI 卸载工具 (zfcpdump)
======================

系统 z 机器（z900 或更高版本）提供了在 SCSI 磁盘上创建系统卸载的支持。卸载过程由启动一个卸载工具触发，该工具需要创建当前（可能已崩溃）的 Linux 映像的卸载。为了不使用卸载工具的数据覆盖崩溃的 Linux 的内存，硬件会在加载卸载工具之前保存部分内存加上引导 CPU 的寄存器集。存在一个 SCLP 硬件接口以获取保存后的内存。目前保存了 32MB。

这个 zfcpdump 实现包括一个 Linux 卸载内核与用户空间的卸载工具，它们一起被加载到 32MB 以下的保存内存区域中。zfcpdump 使用 zipl（包含在 s390-tools 包中）安装在一个 SCSI 磁盘上，使设备可引导。Linux 系统的操作员可以通过启动含有 zfcpdump 的 SCSI 磁盘来触发 SCSI 卸载。

用户空间卸载工具通过 /proc/vmcore 接口访问崩溃系统的内存。此接口以 ELF 核心转储格式导出崩溃系统的内存和寄存器。当 /proc/vmcore 需要数据时，将创建 SCLP 请求来获取硬件保存的内存。对于未被硬件缓存的部分，可以直接从实际内存复制。

要构建一个支持卸载的内核，需要设置内核配置选项 CONFIG_CRASH_DUMP。

要获取有效的 zfcpdump 内核配置，请使用 "make zfcpdump_defconfig"。

s390 zipl 工具会在以下位置查找 zfcpdump 内核和可选的 initrd/initramfs：

* 内核： <zfcpdump 目录>/zfcpdump.image
* ramdisk： <zfcpdump 目录>/zfcpdump.rd

zfcpdump 目录在 s390-tools 包中定义。

zfcpdump 的用户空间应用程序可以位于 initramfs 或 initrd 中。它也可以包含在内置内核的 initramfs 中。该应用程序从 /proc/vmcore 或 zcore/mem 读取，并将系统卸载写入 SCSI 磁盘。

s390-tools 包版本 1.24.0 及以上版本构建了一个带有用户空间应用程序的外部 zfcpdump initramfs，该程序将卸载写入 SCSI 分区。

有关如何使用 zfcpdump 的更多信息，请参阅 IBM 知识中心提供的 s390 “使用卸载工具” 书籍：
https://www.ibm.com/support/knowledgecenter/linuxonibm/liaaf/lnz_r_dt.html
