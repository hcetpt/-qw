=======================
直接文件访问
=======================

动机
----------

页面缓存通常用于缓冲对文件的读写操作。
它还用于通过调用mmap将页面映射到用户空间。
对于类似内存的块设备，页面缓存页面将是原始存储的多余副本。`DAX`代码通过直接对存储设备进行读写消除了额外的副本。
对于文件映射，存储设备被直接映射到用户空间。

使用方法
-----

如果您有一个支持`DAX`的块设备，您可以像往常一样在其上创建一个文件系统。目前`DAX`代码仅支持与内核`PAGE_SIZE`相等的块大小的文件，因此在创建文件系统时可能需要指定块大小。
目前有5个文件系统支持`DAX`：ext2、ext4、xfs、virtiofs和erofs。启用`DAX`的方式各有不同。

在ext2和erofs上启用`DAX`
------------------------------

当挂载文件系统时，在命令行中使用`-o dax`选项，或者在`/etc/fstab`中的选项添加`dax`。这适用于在文件系统内的所有文件上启用`DAX`。这相当于下面的`-o dax=always`行为。

在xfs和ext4上启用`DAX`
----------------------------

总结
-------

1. 内核中存在一个文件访问模式标志`S_DAX`，对应于statx标志`STATX_ATTR_DAX`。关于此访问模式的详细信息，请参阅statx(2)的手册页。
2. 存在一个持久性标志`FS_XFLAG_DAX`，可以应用于普通文件和目录。这个提示性标志可以在任何时候设置或清除，但这样做不会立即影响`S_DAX`状态。
3. 如果在目录上设置了持久的 `FS_XFLAG_DAX` 标志，该标志将被随后在此目录中创建的所有普通文件和子目录继承。在父目录设置或清除此标志时已存在的文件和子目录不会受到此修改的影响。

4. 存在一些 DAX 挂载选项可以覆盖 `FS_XFLAG_DAX` 以设置 `S_DAX` 标志。假设底层存储支持 `DAX`，以下规则适用：

    ``-o dax=inode`` 表示“遵循 `FS_XFLAG_DAX`”，这是默认值。
    
    ``-o dax=never`` 表示“从不设置 `S_DAX`，忽略 `FS_XFLAG_DAX`。”

    ``-o dax=always`` 表示“始终设置 `S_DAX`，忽略 `FS_XFLAG_DAX`。”

    ``-o dax`` 是一个遗留选项，等同于 ``dax=always``。

.. warning::

      选项 ``-o dax`` 可能会在将来被移除，因此建议使用 ``-o dax=always`` 来指定这种行为。

.. note::

      即使文件系统使用 DAX 选项挂载，对 `FS_XFLAG_DAX` 的修改及其继承行为仍然保持不变。然而，在内核中的 `S_DAX` 状态（`S_DAX`）将在文件系统重新挂载为 dax=inode 并且 inode 被从内核内存中驱逐后才会被覆盖。

5. 可以通过以下方式更改 `S_DAX` 策略：

    a) 在创建文件之前根据需要设置父目录的 `FS_XFLAG_DAX` 标志
    
    b) 设置适当的 dax="foo" 挂载选项
    
    c) 更改现有普通文件和目录上的 `FS_XFLAG_DAX` 标志。这有一些运行时约束和限制，如下文 6) 所述

6. 当通过切换持久的 `FS_XFLAG_DAX` 标志来更改 `S_DAX` 策略时，现有普通文件的变化只有在所有进程关闭这些文件后才会生效。

详情
----

有两个与文件相关的 DAX 标志。一个是持久的 inode 设置 (`FS_XFLAG_DAX`)，另一个是表示功能活动状态的易失性标志 (`S_DAX`)。

`FS_XFLAG_DAX` 在文件系统内部得以保留。这个持久配置设置可以通过 `FS_IOC_FS`[`GS`]`ETXATTR` ioctl（参见 ioctl_xfs_fsgetxattr(2)）或类似 'xfs_io' 的工具进行设置、清除和查询。

新文件和目录在创建时会自动从其父目录继承 `FS_XFLAG_DAX`。因此，在目录创建时设置 `FS_XFLAG_DAX` 可用于为整个子树设置默认行为。
为了澄清继承关系，以下是三个示例：

示例 A：

```shell
mkdir -p a/b/c
xfs_io -c 'chattr +x' a
mkdir a/b/c/d
mkdir a/e

------[结果]------

支持 DAX：a, e
不支持 DAX：b, c, d
```

示例 B：

```shell
mkdir a
xfs_io -c 'chattr +x' a
mkdir -p a/b/c/d

------[结果]------

支持 DAX：a, b, c, d
不支持 DAX：
```

示例 C：

```shell
mkdir -p a/b/c
xfs_io -c 'chattr +x' c
mkdir a/b/c/d

------[结果]------

支持 DAX：c, d
不支持 DAX：a, b
```

当前启用状态（`S_DAX`）在内核将文件inode实例化到内存时设置。它是基于底层介质的支持、`FS_XFLAG_DAX`的值以及文件系统的DAX挂载选项来确定的。可以使用`statx`查询`S_DAX`。
.. note::
   只有普通文件才会设置`S_DAX`标志，因此`statx`永远不会指示目录上设置了`S_DAX`。

即使底层介质不支持DAX和/或文件系统被挂载选项覆盖，设置`FS_XFLAG_DAX`标志（具体地或通过继承）也会发生。

在virtiofs上启用DAX
-------------------
virtiofs上的DAX语义基本上等同于ext4和xfs，唯一的区别是当指定`-o dax=inode`时，virtiofs客户端通过FUSE协议从virtiofs服务器获取是否启用DAX的提示，而不是持久化的`FS_XFLAG_DAX`标志。也就是说，是否启用DAX完全由virtiofs服务器决定，而virtiofs服务器本身可能会采用各种算法来做出这个决定，例如依赖于主机上的持久化`FS_XFLAG_DAX`标志。

仍然可以在客户机内部设置或清除持久化的`FS_XFLAG_DAX`标志，但不能保证相应的文件会启用或禁用DAX。客户机内的用户仍需要调用`statx(2)`并检查`statx`标志`STATX_ATTR_DAX`以查看该文件是否启用了DAX。

块驱动编写者实现建议
---------------------
要在您的块驱动中支持`DAX`，请实现`direct_access`块设备操作。它用于将扇区号（以512字节扇区为单位表示）转换为标识内存物理页的页帧号（pfn），并返回一个可用于访问内存的内核虚拟地址。
`direct_access`方法接受一个表示请求字节数的`size`参数。该函数应返回在该偏移处可连续访问的字节数。如果发生错误，也可以返回负的errno值。

为了支持此方法，存储必须始终对CPU字节可访问。如果您的设备使用分页技术通过较小窗口暴露大量内存，则无法实现`direct_access`。同样，如果您的设备偶尔会使CPU停滞较长时间，也不应尝试实现`direct_access`。

以下是一些可供参考的块设备：
- brd：基于RAM的块设备驱动
- dcssblk：s390 dcss块设备驱动
- pmem：NVDIMM持久内存驱动

文件系统编写者实现建议
--------------------------
文件系统支持包括：

* 添加支持以设置i_flags中的`S_DAX`标志来标记inode为支持`DAX`
* 实现->read_iter和->write_iter操作，在inode具有`S_DAX`标志时使用:c:func:`dax_iomap_rw()`
* 实现针对`DAX`文件的mmap文件操作，设置`VMA`上的`VM_MIXEDMAP`和`VM_HUGEPAGE`标志，并设置vm_ops以包含处理fault, pmd_fault, page_mkwrite, pfn_mkwrite的处理器。这些处理器应调用:c:func:`dax_iomap_fault()`，传递适当的fault大小和iomap操作。
* 调用 :c:func:`iomap_zero_range()` 并传递适当的 iomap 操作，而不是为 `DAX` 文件使用 :c:func:`block_truncate_page()`
* 确保在读取、写入、截断和页面错误之间有足够的锁定

分配块的 iomap 处理器必须确保已分配的块被清零并转换为已写入的范围，然后再返回，以避免通过 mmap 暴露未初始化的数据
以下文件系统可用于参考：

.. seealso::

  ext2: 参见文档/文件系统/ext2.rst

.. seealso::

  xfs: 参见文档/管理员指南/xfs.rst

.. seealso::

  ext4: 参见文档/文件系统/ext4/

处理介质错误
---------------------

libnvdimm 子系统为每个 pmem 块设备存储已知介质错误位置的记录（在 gendisk->badblocks 中）。如果我们在此类位置发生错误，或一个尚未发现的潜在错误位置，应用程序可以期望接收到 `SIGBUS`。Libnvdimm 还允许通过简单地写入受影响的扇区（通过 pmem 驱动程序，并且如果底层 NVDIMM 支持由 ACPI 定义的清除毒药 DSM）来清除这些错误。
由于 `DAX` IO 通常不经过 `driver/bio` 路径，因此应用程序或系统管理员可以选择从先前的 `备份/内置` 冗余中恢复丢失的数据，方法如下：

1. 删除受影响的文件，并从备份中恢复（系统管理员途径）：
   这将释放文件系统中被该文件使用的块，在下次分配时它们将首先被清零，这会通过驱动程序完成，并清除坏扇区
2. 截断或打孔包含坏块的部分文件（至少整个对齐的扇区需要被打孔，但不必一定是整个文件系统块）
这些是两种基本路径，允许 `DAX` 文件系统在出现介质错误时继续运行。将来可以在这些基础上构建更强大的错误恢复机制，例如通过 DM 在块层提供的冗余/镜像，或者另外，在文件系统级别。这些必须依赖于上述两条原则，即错误清除可以通过发送 IO 通过驱动程序完成，或者通过驱动程序进行清零。

不足之处
------------

即使内核或其模块存储在支持 `DAX` 的块设备上的文件系统上，它们仍然会被复制到 RAM 中
DAX 代码在具有虚拟映射缓存的架构上无法正确工作，如 ARM、MIPS 和 SPARC
对通过 `DAX` 文件映射的用户内存范围调用 :c:func:`get_user_pages()` 会在没有描述这些页的 `struct page` 时失败。一些设备驱动程序通过为受驱动程序控制的页面添加可选的 `struct page` 支持来解决此问题（参见 `drivers/nvdimm` 中的 `CONFIG_NVDIMM_PFN` 作为如何实现这一点的例子）。在非 `struct page` 情况下，从非 `DAX` 文件对这些内存范围进行 `O_DIRECT` 读/写将会失败

.. note::

  对 `DAX` 文件的 `O_DIRECT` 读/写确实有效，关键是正在访问的内存。在非 `struct page` 情况下，其他无法正常工作的功能包括 RDMA、:c:func:`sendfile()` 和 :c:func:`splice()`。
