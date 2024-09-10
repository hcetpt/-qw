SPDX 许可证标识符: GPL-2.0

========
ORANGEFS
========

OrangeFS 是一个LGPL用户空间横向扩展并行存储系统。它非常适合 HPC（高性能计算）、BigData（大数据）、流媒体视频、基因组学和生物信息学等大规模存储问题。
OrangeFS 最初名为 PVFS，由 Walt Ligon 和 Eric Blumer 在 1993 年作为研究并行程序的 I/O 模式的 NASA 授予项目的一部分开发，用于并行虚拟机 (PVM) 的并行文件系统。
OrangeFS 的特点包括：

  * 将文件数据分布在多个文件服务器之间
  * 支持多个客户端同时访问
  * 使用本地文件系统和访问方法在服务器上存储文件数据和元数据
  * 用户空间实现易于安装和维护
  * 直接支持 MPI
  * 无状态

邮件列表归档
=====================

http://lists.orangefs.org/pipermail/devel_lists.orangefs.org/

邮件列表提交
=====================

devel@lists.orangefs.org

文档
=============

http://www.orangefs.org/documentation/

在单个服务器上运行 ORANGEFS
===================================

OrangeFS 通常在包含多个服务器和客户端的大规模环境中运行，但可以在单台机器上运行完整的文件系统以进行开发和测试。
在 Fedora 上安装 orangefs 和 orangefs-server：

    dnf -y install orangefs orangefs-server

在 /etc/orangefs/orangefs.conf 中有一个示例服务器配置文件。如果需要，请将 localhost 更改为您的主机名。
为了生成一个用于运行 xfstests 的文件系统，请参见下面的说明。
在 /etc/pvfs2tab 中有一个示例客户端配置文件。它是一行。如果需要，请取消注释并更改主机名。这控制使用 libpvfs2 的客户端。这不控制 pvfs2-client-core。
创建文件系统：

    pvfs2-server -f /etc/orangefs/orangefs.conf

启动服务器：

    systemctl start orangefs-server

测试服务器：

    pvfs2-ping -m /pvfsmnt

启动客户端。在此之前的某个时刻必须编译内核模块或加载该模块：

    systemctl start orangefs-client

挂载文件系统：

    mount -t pvfs2 tcp://localhost:3334/orangefs /pvfsmnt

用户空间文件系统源码
===========================

http://www.orangefs.org/download

版本 2.9.3 之前的 OrangeFS 不兼容内核客户端的上游版本。

在单个服务器上构建 ORANGEFS
====================================

当无法从发行版包安装 OrangeFS 时，可以从源代码构建。
如果您不介意让文件散落在 /usr/local 中，可以省略 --prefix。截至版本 2.9.6，OrangeFS 默认使用 Berkeley DB，我们可能很快会将默认值更改为 LMDB：

    ./configure --prefix=/opt/ofs --with-db-backend=lmdb --disable-usrint

    make

    make install

通过运行 pvfs2-genconfig 并指定目标配置文件来创建 OrangeFS 配置文件。Pvfs2-genconfig 会引导您完成配置过程。通常，默认设置就足够了，但在涉及主机名的问题时，请使用您的服务器的主机名，而不是“localhost”：

    /opt/ofs/bin/pvfs2-genconfig /etc/pvfs2.conf

创建 /etc/pvfs2tab 文件（localhost 即可）：

    echo tcp://localhost:3334/orangefs /pvfsmnt pvfs2 defaults,noauto 0 0 > /etc/pvfs2tab

如果需要，请创建在 tab 文件中指定的挂载点：

    mkdir /pvfsmnt

引导服务器：

    /opt/ofs/sbin/pvfs2-server -f /etc/pvfs2.conf

启动服务器：

    /opt/ofs/sbin/pvfs2-server /etc/pvfs2.conf

现在服务器应该正在运行。Pvfs2-ls 是一个简单的测试，以验证服务器是否正在运行：

    /opt/ofs/bin/pvfs2-ls /pvfsmnt

如果一切正常，加载内核模块并启用客户端核心：

    /opt/ofs/sbin/pvfs2-client -p /opt/ofs/sbin/pvfs2-client-core

挂载您的文件系统：

    mount -t pvfs2 tcp://`hostname`:3334/orangefs /pvfsmnt

运行 xfstests
=================

使用 xfstests 时，使用临时文件系统是有用的。这可以通过仅使用一个服务器来实现。
在服务器配置文件 `/etc/orangefs/orangefs.conf` 中复制 `FileSystem` 部分的第二个副本。将名称改为 `scratch`，并将 ID 改为与第一个 `FileSystem` 部分不同的 ID（通常选择 2）。

这样就有了两个 `FileSystem` 部分：`orangefs` 和 `scratch`。这些更改应在创建文件系统之前完成：

```sh
pvfs2-server -f /etc/orangefs/orangefs.conf
```

要运行 xfstests，请创建 `/etc/xfsqa.config` 文件：

```sh
TEST_DIR=/orangefs
TEST_DEV=tcp://localhost:3334/orangefs
SCRATCH_MNT=/scratch
SCRATCH_DEV=tcp://localhost:3334/scratch
```

然后可以运行 xfstests：

```sh
./check -pvfs2
```

选项
====

以下挂载选项被接受：

  acl  
    允许在文件和目录上使用访问控制列表。
intr  
    内核客户端和用户空间文件系统之间的一些操作是可中断的，例如调试级别的变化和可调参数的设置。
local_lock  
    启用从“这个”内核的角度来看的 POSIX 锁定。默认的文件操作锁动作为返回 ENOSYS。如果文件系统挂载时带有 `-o local_lock` 选项，则会启用 POSIX 锁定。
分布式锁定正在开发中。

调试
=====

如果你想查看特定源文件（例如 inode.c）中的调试（GOSSIP）语句，请将其发送到 syslog：

```sh
echo inode > /sys/kernel/debug/orangefs/kernel-debug
```

关闭调试（默认）：

```sh
echo none > /sys/kernel/debug/orangefs/kernel-debug
```

从多个源文件进行调试：

```sh
echo inode,dir > /sys/kernel/debug/orangefs/kernel-debug
```

所有调试：

```sh
echo all > /sys/kernel/debug/orangefs/kernel-debug
```

获取所有调试关键字的列表：

```sh
cat /sys/kernel/debug/orangefs/debug-help
```

内核模块与用户空间之间的协议
==============================

Orangefs 是一个用户空间文件系统及其关联的内核模块。从现在起，我们将仅称其用户空间部分为“用户空间”。Orangefs 源自 PVFS，并且用户空间代码仍然使用 PVFS 的函数和变量名。用户空间对许多重要的结构进行了 typedef。内核模块中的函数和变量名已转换为“orangefs”，并且根据 Linux 编码风格，避免使用 typedef，因此与用户空间结构对应的内核模块结构没有进行 typedef。
内核模块实现了一个伪设备，用户空间可以从中读取和写入。用户空间还可以通过该伪设备使用ioctl来操作内核模块。

### Bufmap

在启动时，用户空间分配了两个页面大小对齐的（使用posix_memalign）锁定内存缓冲区，一个用于I/O操作，另一个用于readdir操作。I/O缓冲区的大小为41943040字节，readdir缓冲区的大小为4194304字节。每个缓冲区包含逻辑块或分区，并且每个缓冲区的指针被添加到其自己的PVFS_dev_map_desc结构中，该结构还描述了缓冲区的总大小以及分区的大小和数量。

指向I/O缓冲区的PVFS_dev_map_desc结构的指针通过ioctl发送到内核模块中的映射例程。该结构通过copy_from_user从用户空间复制到内核空间，并用于初始化内核模块的“bufmap”（struct orangefs_bufmap），其中包含：

  * `refcnt` —— 引用计数器
  * `desc_size` —— PVFS2_BUFMAP_DEFAULT_DESC_SIZE（4194304）—— I/O缓冲区的分区大小，代表文件系统的块大小，并用于super块中的`s_blocksize`
  * `desc_count` —— PVFS2_BUFMAP_DEFAULT_DESC_COUNT（10）—— I/O缓冲区中的分区数量
  * `desc_shift` —— log2(`desc_size`)，用于super块中的`s_blocksize_bits`
  * `total_size` —— I/O缓冲区的总大小
  * `page_count` —— I/O缓冲区中的4096字节页面数量
  * `page_array` —— 指向`page_count * (sizeof(struct page*))`字节的kcalloced内存。这些内存作为I/O缓冲区中每个页面的指针数组，通过调用get_user_pages获取
  * `desc_array` —— 指向`desc_count * (sizeof(struct orangefs_bufmap_desc))`字节的kcalloced内存。这些内存进一步初始化如下：

      `user_desc` 是内核中I/O缓冲区的ORANGEFS_dev_map_desc结构的副本。`user_desc->ptr` 指向I/O缓冲区
  ::

      ```
      pages_per_desc = bufmap->desc_size / PAGE_SIZE
      offset = 0

      bufmap->desc_array[0].page_array = &bufmap->page_array[offset]
      bufmap->desc_array[0].array_count = pages_per_desc = 1024
      bufmap->desc_array[0].uaddr = (user_desc->ptr) + (0 * 1024 * 4096)
      offset += 1024
      ```
```c
bufmap->desc_array[9].page_array = &bufmap->page_array[offset];
bufmap->desc_array[9].array_count = pages_per_desc = 1024;
bufmap->desc_array[9].uaddr = (user_desc->ptr) + (9 * 1024 * 4096);
offset += 1024;

* buffer_index_array - 一个大小为 desc_count 的整数数组，用于指示哪些 IO 缓冲区的分区可以使用。
* buffer_index_lock - 一个自旋锁，用于在更新时保护 buffer_index_array。
* readdir_index_array - 一个包含五个元素（ORANGEFS_READDIR_DEFAULT_DESC_COUNT）的整数数组，用于指示哪些 readdir 缓冲区的分区可以使用。
* readdir_index_lock - 一个自旋锁，用于在更新时保护 readdir_index_array。

操作
------

内核模块在需要与用户空间通信时构建一个“op”（struct orangefs_kernel_op_s）。op 的一部分包含“upcall”，表达向用户空间的请求。op 的另一部分最终包含“downcall”，表达请求的结果。slab 分配器用于保持 op 结构体的缓存。在初始化时，内核模块定义并初始化了一个请求列表和一个进行中的哈希表，以跟踪任意时刻正在进行的所有 op。op 是有状态的：

* 未知
    - op 刚刚被初始化。
* 等待
    - op 在请求列表中（向上传递）。
* 进行中
    - op 正在处理中（等待 downcall）。
* 已服务
    - op 已收到匹配的 downcall；一切正常。
* 已清除
    - op 必须启动一个定时器，因为客户端核心在服务 op 之前异常退出。
* 放弃
    - 提交者已放弃等待它。

当某个任意的用户空间程序需要对 Orangefs 执行文件系统操作（如 readdir、I/O、创建等）时，会初始化一个 op 结构，并标记一个区分性的 ID 号。填充 op 的 upcall 部分，并将 op 传递给“service_operation”函数。
```
服务操作将操作（op）的状态更改为“等待”，将其添加到请求列表中，并通过等待队列触发Orangefs文件操作的poll函数。用户空间会轮询伪设备，从而了解到需要读取的上层请求。当触发Orangefs文件操作的read函数时，会在请求列表中查找一个看似准备处理的操作。该操作将从请求列表中移除，其标签和填充好的上层结构通过copy_to_user复制回用户空间。如果这些（以及一些额外协议）中的任何copy_to_user失败，则将操作的状态设置为“等待”，并将操作重新添加到请求列表中。否则，将操作的状态更改为“进行中”，并根据其标签将其哈希并放置到in_progress哈希表相应索引位置的末尾。

当用户空间组装好对上层请求的响应后，它将包含区分标签的响应写回到伪设备的一系列io_vec中。这将触发Orangefs文件操作的write_iter函数来查找具有相关标签的操作，并将其从in_progress哈希表中移除。只要操作的状态不是“已取消”或“放弃”，则将其状态设置为“已处理”。文件操作的write_iter函数返回到等待的vfs，并通过wait_for_matching_downcall返回到服务操作。服务操作带着操作的下层部分（即对上层请求的响应）返回给调用者。

“客户端核心”是内核模块与用户空间之间的桥梁。客户端核心是一个守护进程，并且有一个关联的看门狗守护进程。如果客户端核心被信号通知死亡，看门狗守护进程将重启客户端核心。尽管客户端核心会“立即”重启，但在这种事件发生期间仍有一段时间是客户端核心死亡的。一个死亡的客户端核心无法被Orangefs文件操作的poll函数触发。在“死亡期”内通过服务操作的操作可能会在等待队列上超时，并尝试一次回收它们。显然，如果客户端核心长时间处于死亡状态，任意尝试使用Orangefs的用户空间进程将受到负面影响。无法处理的等待操作将从请求列表中移除，并将其状态设置为“放弃”。无法处理的进行中操作将从in_progress哈希表中移除，并将其状态设置为“放弃”。

readdir和I/O操作在其有效负载方面是非典型的。
- `readdir` 操作使用两个预分配的分区内存缓冲区中较小的一个。`readdir` 缓冲区仅对用户空间可用。内核模块在启动 `readdir` 操作之前获取一个空闲分区的索引。用户空间将结果存入该索引分区，然后写回到 PVFS 设备。
- I/O（读和写）操作使用两个预分配的分区内存缓冲区中较大的一个。I/O 缓冲区可同时被用户空间和内核模块访问。内核模块在启动 I/O 操作之前获取一个空闲分区的索引。内核模块将写入数据存入该索引分区，供用户空间直接消费。用户空间将读取请求的结果存入该索引分区，供内核模块直接消费。

对内核请求的所有响应都封装在 `pvfs2_downcall_t` 结构体中。除了其他几个成员外，`pvfs2_downcall_t` 包含一个联合体，每个结构体与特定的响应类型相关联。联合体之外的几个成员如下：

```
int32_t type;
    - 操作类型
int32_t status;
    - 操作返回码
int64_t trailer_size;
    - 除非是 `readdir` 操作，否则为 0
char *trailer_buf;
    - 初始化为 NULL，在 `readdir` 操作期间使用
```

对于任何特定的响应，联合体内适当的成员会被填充。

- `PVFS2_VFS_OP_FILE_IO`
    填充 `pvfs2_io_response_t`

- `PVFS2_VFS_OP_LOOKUP`
    填充 `PVFS_object_kref`

- `PVFS2_VFS_OP_CREATE`
    填充 `PVFS_object_kref`

- `PVFS2_VFS_OP_SYMLINK`
    填充 `PVFS_object_kref`

- `PVFS2_VFS_OP_GETATTR`
    填充 `PVFS_sys_attr_s`（包含大量内核不需要的信息）
    当对象是一个符号链接时，填充字符串以表示链接目标
### PVFS2_VFS_OP_MKDIR
填充一个 `PVFS_object_kref` 结构体。

### PVFS2_VFS_OP_STATFS
填充一个 `pvfs2_statfs_response_t` 结构体，其中包含一些无用的信息。我们很难及时获取分布式网络文件系统的这些统计信息。

### PVFS2_VFS_OP_FS_MOUNT
填充一个 `pvfs2_fs_mount_response_t` 结构体，它类似于 `PVFS_object_kref`，但成员的顺序不同，并且 `__pad1` 被替换为 `id`。

### PVFS2_VFS_OP_GETXATTR
填充一个 `pvfs2_getxattr_response_t` 结构体。

### PVFS2_VFS_OP_LISTXATTR
填充一个 `pvfs2_listxattr_response_t` 结构体。

### PVFS2_VFS_OP_PARAM
填充一个 `pvfs2_param_response_t` 结构体。

### PVFS2_VFS_OP_PERF_COUNT
填充一个 `pvfs2_perf_count_response_t` 结构体。

### PVFS2_VFS_OP_FSKEY
填充一个 `pvfs2_fs_key_response_t` 结构体。

### PVFS2_VFS_OP_READDIR
将所有需要表示 `pvfs2_readdir_response_t` 的内容放入由上层调用指定的 `readdir` 缓冲描述符中。

用户空间使用 `writev()` 对 `/dev/pvfs2-req` 进行写操作，以将内核发出的请求的响应传递给内核。
一个 `buffer_list` 包含：

- 指向已准备好的对内核请求的响应（`struct pvfs2_downcall_t`）；
- 在 `readdir` 请求的情况下，还包含指向目标目录中对象描述符缓冲区的指针。

该 `buffer_list` 被发送到执行 `writev` 的函数（`PINT_dev_write_list`）。

`PINT_dev_write_list` 有一个本地的 `iovec` 数组：`struct iovec io_array[10]`。

对于所有响应，`io_array` 的前四个元素初始化如下：

```c
io_array[0].iov_base = 本地变量 "proto_ver"（int32_t）的地址
io_array[0].iov_len = sizeof(int32_t)

io_array[1].iov_base = 全局变量 "pdev_magic"（int32_t）的地址
io_array[1].iov_len = sizeof(int32_t)

io_array[2].iov_base = 参数 "tag"（PVFS_id_gen_t）的地址
io_array[2].iov_len = sizeof(int64_t)

io_array[3].iov_base = 全局变量 vfs_request（vfs_request_t）中的 out_downcall 成员（pvfs2_downcall_t）的地址
io_array[3].iov_len = sizeof(pvfs2_downcall_t)
```

对于 `readdir` 响应，`io_array` 的第五个元素初始化如下：

```c
io_array[4].iov_base = 全局变量 vfs_request 中 out_downcall 成员的 trailer_buf（char *）的内容
io_array[4].iov_len = 全局变量 vfs_request 中 out_downcall 成员的 trailer_size（PVFS_size）的内容
```

Orangefs 利用 dcache 避免向用户空间发送冗余请求。我们通过 `orangefs_inode_getattr` 保持对象 inode 属性的最新状态。`orangefs_inode_getattr` 使用两个参数来决定是否更新一个 inode：`new` 和 `bypass`。

Orangefs 在对象的 inode 中保存私有数据，包括一个短暂的超时值 `getattr_time`，这使得任何迭代的 `orangefs_inode_getattr` 都能知道自上次更新 inode 以来经过了多长时间。当对象不是新的（`new == 0`）并且没有设置绕过标志（`bypass == 0`）时，如果 `getattr_time` 没有超时，`orangefs_inode_getattr` 将不会更新 inode。每次更新 inode 时都会更新 `getattr_time`。

创建新对象（文件、目录、符号链接）包括对其路径名的评估，从而生成一个对象的负目录条目。
一个新的inode被分配并与dentry关联，使其从一个负dentry变为“社会中有生产力的完整成员”。Orangefs通过new_inode()函数从Linux获取新的inode，并通过d_instantiate()将inode与dentry关联起来。

对一个对象的路径名进行解析会得到其对应的dentry。如果没有对应的dentry，则会在dcache中为其创建一个。每当dentry被修改或验证时，Orangefs会在dentry的d_time中存储一个短暂的超时值，并且在该时间内信任这个dentry。Orangefs是一个网络文件系统，对象可能会在任何特定的Orangefs内核模块实例之外发生变化，因此信任dentry是有风险的。不信任dentry的替代方法是从用户空间始终获取所需的信息——至少需要一次往返客户端核心，可能还需要到服务器。从dentry获取信息是廉价的，而从用户空间获取信息则相对昂贵，因此尽可能使用dentry是有动机的。

超时值d_time和getattr_time是以jiffies为单位的，代码设计旨在避免jiffies回绕问题：

    “一般来说，如果时钟可能已经回绕了一次以上，就无法确定过去了多少时间。然而，如果已知时间t1和t2相隔不远，我们可以可靠地计算出它们之间的差值，同时考虑到时钟在这两个时间之间可能已经回绕的可能性。”

——Andy Wang教授的课程笔记
