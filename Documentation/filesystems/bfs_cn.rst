```
SPDX-License标识符: GPL-2.0

========================
BFS 文件系统用于 Linux
========================

BFS 文件系统被 SCO UnixWare 操作系统用于 /stand 分区，该分区通常包含内核映像和启动过程所需的其他一些文件。
为了在 Linux 下访问 /stand 分区，显然需要知道分区号，并且内核必须支持 UnixWare 磁盘分区（CONFIG_UNIXWARE_DISKLABEL 配置选项）。然而，BFS 支持并不依赖于是否具有 UnixWare 磁盘标签支持，因为也可以通过回环设备挂载 BFS 文件系统：

    # losetup /dev/loop0 stand.img
    # mount -t bfs /dev/loop0 /mnt/stand

其中 stand.img 是一个包含 BFS 文件系统映像的文件。
当您使用完毕并卸载后，还需要释放 /dev/loop0 设备：

    # losetup -d /dev/loop0

您可以通过以下命令简化挂载过程：

    # mount -t bfs -o loop stand.img /mnt/stand

这将自动分配第一个可用的回环设备（并在必要时加载 loop.o 内核模块）。如果回环驱动程序没有自动加载，请确保您已编译该模块并且 modprobe 功能正常。请注意，如果您的系统上的 /etc/mtab 文件是到 /proc/mounts 的符号链接，则卸载不会释放 /dev/loopN 设备。您需要手动使用 losetup(8) 的 "-d" 选项来释放它。请阅读 losetup(8) 手册页以获取更多信息。
要在 UnixWare 下创建 BFS 映像，您需要首先确定哪个分区包含它。命令 prtvtoc(1M) 可以帮助您：

    # prtvtoc /dev/rdsk/c0b0t0d0s0

（假设您的根磁盘位于 target=0, lun=0, bus=0, controller=0）。然后查找带有 "STAND" 标签的分区，通常是分区 10。有了这些信息，您可以使用 dd(1) 创建 BFS 映像：

    # umount /stand
    # dd if=/dev/rdsk/c0b0t0d0sa of=stand.img bs=512

以防万一，您可以通过检查魔数来验证是否正确执行了操作：

    # od -Ad -tx4 stand.img | more

前 4 个字节应该是 0x1badface。
如果您有关于此 BFS 实现的任何补丁、问题或建议，请联系作者：

Tigran Aivazian <aivazian.tigran@gmail.com>
```
