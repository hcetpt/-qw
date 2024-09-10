SPDX 许可证标识符: GPL-2.0

===========================
Ramfs、rootfs 和 initramfs
===========================

2005年10月17日

:作者: Rob Landley <rob@landley.net>

什么是 Ramfs？
--------------

Ramfs 是一个非常简单的文件系统，它将 Linux 的磁盘缓存机制（页面缓存和目录项缓存）作为动态可调整大小的基于 RAM 的文件系统导出。
通常所有文件都会被 Linux 缓存在内存中。从后端存储（通常是文件系统挂载的块设备）读取的数据页会被保留以备再次使用，但会标记为干净（可释放），以防虚拟内存系统需要这些内存用于其他用途。同样，写入文件的数据在写入后端存储后会被标记为干净，但为了缓存目的而保留在内存中，直到虚拟内存系统重新分配这些内存。类似地，目录项缓存（dentry cache）极大地加快了对目录的访问速度。

对于 Ramfs 来说，没有后端存储。写入 Ramfs 的文件会像往常一样分配目录项和页面缓存，但由于没有地方可以写入，这意味着这些页面永远不会被标记为干净，因此虚拟内存系统在回收内存时无法释放它们。
实现 Ramfs 所需的代码量非常小，因为所有的工作都是由现有的 Linux 缓存基础设施完成的。基本上，你是在将磁盘缓存作为一个文件系统挂载。由于这个原因，Ramfs 不是一个可以通过 menuconfig 移除的可选组件，因为移除它几乎不会节省空间。

Ramfs 和 Ramdisk：
------------------

较旧的“RAM 磁盘”机制是通过一块 RAM 区域创建一个合成块设备，并将其用作文件系统的后端存储。这个块设备是固定大小的，所以挂载在其上的文件系统也是固定大小的。使用 RAM 磁盘还需要不必要的从假块设备复制内存到页面缓存（以及复制修改后的数据回去），同时还要创建和销毁目录项。此外，还需要一个文件系统驱动程序（如 ext2）来格式化和解释这些数据。

与 Ramfs 相比，这浪费了内存（和内存总线带宽），给 CPU 增加了不必要的工作负载，并且污染了 CPU 缓存。（有一些技巧可以通过操作页表来避免这种复制，但这些技巧非常复杂，结果证明其开销与复制相当。）

更重要的是，Ramfs 所做的所有工作无论如何都要发生，因为所有的文件访问都通过页面缓存和目录项缓存进行。RAM 磁盘实际上是多余的；Ramfs 在内部更简单。

另一个使 RAM 磁盘变得半过时的原因是引入了回环设备（loopback devices），提供了一种更灵活和方便的方式来创建合成块设备，现在是从文件而不是从内存块创建。

详见 losetup (8)。

Ramfs 和 Tmpfs：
----------------

Ramfs 的一个缺点是你可以在其中不断写入数据，直到填满所有内存，而虚拟内存系统无法释放这些数据，因为它认为文件应该写入后端存储（而不是交换空间），但 Ramfs 没有后端存储。正因为如此，只有 root 用户（或受信任的用户）才应被允许写入 Ramfs 挂载点。
一个名为 tmpfs 的 ramfs 派生文件系统被创建，以添加大小限制，并且能够将数据写入交换空间。普通用户可以被允许对 tmpfs 挂载进行写访问。更多信息请参阅 Documentation/filesystems/tmpfs.rst。

什么是 rootfs？
----------------

rootfs 是 ramfs（如果启用了 tmpfs，则为 tmpfs）的一个特殊实例，在 2.6 系统中始终存在。由于与无法终止 init 进程的原因相似，您不能卸载 rootfs；内核不是编写专门的代码来检查并处理空列表，而是通过确保某些列表不会为空来简化工作。大多数系统只是在 rootfs 上挂载另一个文件系统并忽略它。一个空的 ramfs 实例占用的空间非常小。如果启用了 CONFIG_TMPFS，rootfs 将默认使用 tmpfs 而不是 ramfs。要强制使用 ramfs，请在内核命令行中添加 "rootfstype=ramfs"。

什么是 initramfs？
-------------------

所有 2.6 版本的 Linux 内核都包含一个压缩过的“cpio”格式归档文件，该文件在内核启动时被提取到 rootfs 中。提取后，内核会检查 rootfs 是否包含一个名为 “init” 的文件，如果有，则将其作为 PID 1 执行。这个 init 进程负责完成系统的其余启动过程，包括定位和挂载实际的根设备（如果有）。如果在嵌入式 cpio 归档文件被提取到 rootfs 后没有发现 init 程序，内核将退回到旧代码以定位和挂载根分区，然后执行 /sbin/init 的某个变体。

这一切与旧版 initrd 有几点不同：

- 旧版 initrd 总是一个单独的文件，而 initramfs 归档文件是链接到 Linux 内核镜像中的。（目录 `linux-*/usr` 专门用于在构建过程中生成此归档文件。）

- 旧版 initrd 文件是一个压缩的文件系统映像（某种需要内核内置驱动程序的文件格式，如 ext2），而新的 initramfs 归档文件是一个压缩的 cpio 归档文件（类似于 tar 但更简单，参见 cpio(1) 和 Documentation/driver-api/early-userspace/buffer-format.rst）。内核的 cpio 提取代码不仅极其小巧，还是 __init 文本和数据，可以在启动过程中丢弃。

- 旧版 initrd 运行的程序（称为 /initrd，而非 /init）执行一些设置后会返回到内核，而 initramfs 的 init 程序不期望返回到内核。（如果 /init 需要交接控制权，它可以使用新根设备覆盖 / 并执行另一个 init 程序。参见下面的 switch_root 工具。）

- 在切换到另一个根设备时，initrd 会调用 pivot_root 并卸载 ramdisk。但是 initramfs 就是 rootfs：您既不能对 rootfs 使用 pivot_root，也不能卸载它。相反，删除 rootfs 中的所有内容以释放空间（find -xdev / -exec rm '{}' ';'），用新根覆盖 rootfs（cd /newmount; mount --move . /; chroot .），并将 stdin/stdout/stderr 连接到新的 /dev/console，并执行新的 init。由于这是一个非常挑剔的过程（并且涉及删除命令前才能运行它们），klibc 包引入了一个辅助程序（utils/run_init.c）来为您完成所有这些操作。大多数其他包（如 busybox）已将此命令命名为 "switch_root"。

填充 initramfs：
-------------------

2.6 内核构建过程总是会创建一个压缩的 cpio 格式的 initramfs 归档文件，并将其链接到最终的内核二进制文件中。默认情况下，此归档文件是空的（在 x86 上占用 134 字节）。
配置选项 `CONFIG_INITRAMFS_SOURCE`（在 menuconfig 中的 General Setup 下，位于 usr/Kconfig 文件中）可用于指定 initramfs 归档文件的来源，该来源将自动合并到生成的二进制文件中。此选项可以指向一个现有的压缩过的 cpio 归档文件、包含待归档文件的目录或如下所示的文本文件规范：

```
dir /dev 755 0 0
nod /dev/console 644 0 0 c 5 1
nod /dev/loop0 644 0 0 b 7 0
dir /bin 755 1000 1000
slink /bin/sh busybox 777 0 0
file /bin/busybox initramfs/busybox 755 0 0
dir /proc 755 0 0
dir /sys 755 0 0
dir /mnt 755 0 0
file /init initramfs/init.sh 755 0 0
```

运行 "usr/gen_init_cpio"（在内核编译之后）以获取上述文件格式的使用说明。
配置文件的一个优点是不需要根权限即可设置新归档文件中的权限或创建设备节点。（注意这两个示例中的 "file" 条目期望在名为 "initramfs" 的目录中找到名为 "init.sh" 和 "busybox" 的文件。详见 Documentation/driver-api/early-userspace/early_userspace_support.rst。）

内核不依赖外部的 cpio 工具。如果您指定了一个目录而不是配置文件，内核的构建基础设施会从该目录生成一个配置文件（usr/Makefile 调用 usr/gen_initramfs.sh），并使用该配置文件打包该目录（将其传递给 usr/gen_init_cpio，该工具由 usr/gen_init_cpio.c 创建）。内核的构建时 cpio 创建代码是完全自包含的，内核的引导时提取器也是（显然）自包含的。

唯一可能需要安装外部 cpio 工具的情况是创建或提取您自己的预准备好的 cpio 文件以供内核构建使用（而不是配置文件或目录）。
以下命令行可以从 cpio 映像中提取组件文件（无论是通过上述脚本还是内核构建）：

```
cpio -i -d -H newc -F initramfs_data.cpio --no-absolute-filenames
```

以下 shell 脚本可以创建一个预构建的 cpio 归档文件，用于替代上述配置文件：

```sh
#!/bin/sh

# Copyright 2006 Rob Landley <rob@landley.net> and TimeSys Corporation
# Licensed under GPL version 2

if [ $# -ne 2 ]
then
    echo "usage: mkinitramfs directory imagename.cpio.gz"
    exit 1
fi

if [ -d "$1" ]
then
    echo "creating $2 from $1"
    (cd "$1"; find . | cpio -o -H newc | gzip) > "$2"
else
    echo "First argument must be a directory"
    exit 1
fi
```

**注意：**

cpio 手册页中包含了一些错误建议，如果遵循这些建议，可能会破坏您的 initramfs 归档文件。它说“生成文件名列表的一种典型方法是使用 find 命令；您应该给 find 提供 -depth 选项，以尽量减少不可写或不可搜索目录中的权限问题。”在创建 initramfs.cpio.gz 映像时不要这样做，这不会起作用。Linux 内核的 cpio 提取器不会在不存在的目录中创建文件，因此目录条目必须先于进入这些目录的文件条目。
上述脚本按正确的顺序处理它们。

外部 initramfs 映像：
----------------------

如果内核启用了 initrd 支持，则也可以将外部 cpio.gz 归档文件传递给 2.6 内核，以代替 initrd。在这种情况下，内核将自动检测类型（initramfs，而非 initrd），并在尝试运行 /init 之前将外部 cpio 归档文件提取到根文件系统中。
这具有 initramfs 的内存效率优势（没有 ramdisk 块设备），但又保持了 initrd 的单独打包特性（这对于希望在 initramfs 中运行非 GPL 代码而不与 GPL 授权的 Linux 内核二进制文件混合的人来说非常有用）。
还可以用来补充内核内置的 initramfs 映像。外部归档文件中的文件将覆盖内置 initramfs 归档文件中的任何冲突文件。一些发行版也倾向于在不重新编译的情况下，使用任务特定的 initramfs 映像来定制单个内核映像。

initramfs 的内容：
-------------------

initramfs 归档文件是一个完整的自包含根文件系统。
如果你还不清楚需要哪些共享库、设备和路径来启动一个最小的根文件系统，以下是一些参考链接：

- https://www.tldp.org/HOWTO/Bootdisk-HOWTO/
- https://www.tldp.org/HOWTO/From-PowerUp-To-Bash-Prompt-HOWTO.html
- http://www.linuxfromscratch.org/lfs/view/stable/

"klibc" 包（https://www.kernel.org/pub/linux/libs/klibc）旨在提供一个小型的 C 库，用于静态链接早期用户空间代码，并附带一些相关工具。它是 BSD 许可证的。我自己使用的是 uClibc（https://www.uclibc.org） 和 busybox（https://www.busybox.net），它们分别是 LGPL 和 GPL 许可证的。（计划在 busybox 1.3 版本中包含一个自包含的 initramfs 包。）

理论上你可以使用 glibc，但其并不适合这种小型嵌入式用途。（一个使用 glibc 静态链接的“hello world”程序超过 400KB。而使用 uClibc 只有 7KB。另外需要注意的是，即使其他部分是静态链接的，glibc 也会动态打开 libnss 进行名称查找。）

一个好的第一步是让 initramfs 运行一个静态链接的“hello world”程序作为 init，并在如 qemu（www.qemu.org）或 User Mode Linux 等模拟器下测试，如下所示：

```sh
cat > hello.c << EOF
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    printf("Hello world!\n");
    sleep(999999999);
}
EOF
gcc -static hello.c -o init
echo init | cpio -o -H newc | gzip > test.cpio.gz
# 使用 initrd 加载机制测试外部 initramfs
qemu -kernel /boot/vmlinuz -initrd test.cpio.gz /dev/zero
```

调试常规根文件系统时，能够以“init=/bin/sh”启动是非常有用的。对于 initramfs 来说，等价的命令是“rdinit=/bin/sh”，同样非常有用。

为什么选择 cpio 而不是 tar？
---------------------------------

这个决定是在 2001 年 12 月做出的。讨论始于这里：

  http://www.uwsg.iu.edu/hypermail/linux/kernel/0112.2/1538.html

并引发了第二个关于 tar 和 cpio 的讨论，从这里开始：

  http://www.uwsg.iu.edu/hypermail/linux/kernel/0112.2/1587.html

简要总结如下（但这并不能代替阅读上述讨论）：

1) cpio 是一个标准。它已经有几十年的历史（起源于 AT&T），并且已经在 Linux 中广泛使用（例如在 RPM 和 Red Hat 的设备驱动磁盘中）。这里有一篇 1996 年的 Linux Journal 文章介绍了它：

      http://www.linuxjournal.com/article/1213

尽管 cpio 没有 tar 流行，主要是因为传统的 cpio 命令行工具需要极其复杂的命令行参数。但这与存档格式本身无关，而且还有替代工具，例如：

     http://freecode.com/projects/afio

2) 内核选择的 cpio 存档格式比各种 tar 存档格式更简单和干净（因此更容易创建和解析）。完整的 initramfs 存档格式在 buffer-format.txt 中解释，在 usr/gen_init_cpio.c 中创建，并在 init/initramfs.c 中提取。这三者加起来总共不到 26KB 的人类可读文本。
3) GNU 项目标准化 tar 大约和 Windows 标准化 zip 一样相关。Linux 不属于两者中的任何一个，可以自由地做出自己的技术决策。
4) 由于这是内核内部格式，本来可以是一个全新的格式。无论如何，内核提供了创建和提取此格式的工具。使用现有标准是优选的，但并非必要。
5) Al Viro 做出了这个决定（引用：“tar 非常丑陋，不会在内核层面得到支持”）：

      http://www.uwsg.iu.edu/hypermail/linux/kernel/0112.2/1540.html

并解释了他的理由：

     - http://www.uwsg.iu.edu/hypermail/linux/kernel/0112.2/1550.html
     - http://www.uwsg.iu.edu/hypermail/linux/kernel/0112.2/1638.html

最重要的是，他设计并实现了 initramfs 代码。

未来方向：
----------

目前（2.6.16），initramfs 总是被编译进内核，但并不总是被使用。如果 initramfs 中没有 /init 程序，内核会回退到遗留的引导代码。回退代码是遗留代码，用于确保平稳过渡，并允许早期引导功能逐渐转移到“早期用户空间”（即 initramfs）。

向早期用户空间的迁移是必要的，因为找到并挂载实际的根设备非常复杂。根分区可以跨越多个设备（RAID 或单独的日志）。它们可能位于网络上（需要 DHCP、设置特定的 MAC 地址、登录服务器等）。它们可能位于可移动介质上，具有动态分配的主要/次要编号，并且需要完整的 udev 实现来解决持久命名问题。它们可能是压缩的、加密的、写时复制的、循环挂载的、奇怪分区的等等。

这种复杂性（不可避免地包括策略）应该由用户空间处理。klibc 和 busybox/uClibc 正在开发简单的 initramfs 包，以便放入内核构建中。
klibc 包现在已经纳入 Andrew Morton 的 2.6.17-mm 树中。
内核当前的早期引导代码（如分区检测等）可能会迁移到默认的 initramfs 中，该 initramfs 将由内核构建自动创建并使用。
