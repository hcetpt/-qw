引用计数在 PNFS 中的应用
==========================

存在几个相互关联的缓存。我们有布局，它可以引用多个设备，每个设备又可以引用多个数据服务器。每个数据服务器可以被多个设备引用，每个设备可以被多个布局引用。为了理清这一切，我们需要使用引用计数。

`struct pnfs_layout_hdr`
======================

网络传输中的命令 LAYOUTGET 对应于 `struct pnfs_layout_segment`，通常通过变量名 `lseg` 引用。每个 `nfs_inode` 可能包含指向这些布局段缓存的指针，类型为 `struct pnfs_layout_hdr`。我们对指向该 inode 的头部进行引用计数，在每个引用它的未完成的 RPC 调用（如 LAYOUTGET、LAYOUTRETURN 和 LAYOUTCOMMIT）中，以及在每个内部持有的 `lseg` 中。

每个头部（当非空时）也会放入与 `struct nfs_client` （`cl_layouts`）关联的列表中。放入这个列表不会增加引用计数，因为布局由 `lseg` 保持，而 `lseg` 将其保留在列表中。

`deviceid_cache`
==============

`lsegs` 引用设备 ID，这些设备 ID 是按每个 `nfs_client` 和布局驱动类型解析的。设备 ID 存储在一个 RCU 缓存中（`struct nfs4_deviceid_cache`）。缓存本身在每个挂载中被引用。条目（`struct nfs4_deviceid`）在其生命周期内被每个引用它们的 `lseg` 持有。

使用 RCU 是因为设备 ID 基本上是一个一次写入多次读取的数据结构。哈希表大小为 32 个桶需要更好的理由，但考虑到我们可以有多个文件系统中的设备 ID，并且每个 `nfs_client` 可以有多个文件系统，这似乎是合理的。

哈希码是从 nfsd 代码库复制的。关于哈希算法及其变体的讨论可以在 [这里](http://groups.google.com/group/comp.lang.c/browse_thread/thread/9522965e2b8d3809) 找到。

数据服务器缓存
=================

文件驱动设备引用数据服务器，这些数据服务器保存在一个模块级别的缓存中。它的引用在整个设备 ID 指向它的生命周期内持有。
lseg
====

`lseg` 维护一个额外的引用，该引用对应于 `NFS_LSEG_VALID` 标志，并将其保留在 `pnfs_layout_hdr` 的列表中。当最后一个 `lseg` 从 `pnfs_layout_hdr` 的列表中移除时，会设置 `NFS_LAYOUT_DESTROYED` 标志，阻止任何新的 `lseg` 被添加到布局驱动程序中。

布局驱动程序
============

PNFS 使用所谓的布局驱动程序。STD 定义了四种基本的布局类型：“文件”、“对象”、“块”和“flexfiles”。对于这些类型中的每一种，都有一个带有通用函数向量表的布局驱动程序，这些驱动程序被 NFS 客户端的 PNFS 核心调用以实现不同的布局类型。
- 文件布局驱动程序代码位于：`fs/nfs/filelayout/..` 目录下
- 块布局驱动程序代码位于：`fs/nfs/blocklayout/..` 目录下
- Flexfiles 布局驱动程序代码位于：`fs/nfs/flexfilelayout/..` 目录下

块布局设置
==========

待办事项：记录块布局驱动程序的设置需求
