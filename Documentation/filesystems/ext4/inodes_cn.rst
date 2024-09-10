SPDX 许可证标识符: GPL-2.0

索引节点
--------

在标准的 UNIX 文件系统中，inode 存储与文件相关的所有元数据（时间戳、块映射、扩展属性等），而不是目录项。要查找与文件关联的信息，必须遍历目录文件以找到与该文件关联的目录项，然后加载 inode 以找到该文件的元数据。ext4 为了性能原因似乎稍微取了个巧，在目录项中存储了一个文件类型的副本（通常存储在 inode 中）。（将这一切与 FAT 文件系统进行比较，FAT 将所有文件信息直接存储在目录项中，但不支持硬链接，并且由于其简单的块分配器和广泛使用链表，通常比 ext4 更频繁地执行磁盘寻道。）

inode 表是一个由 `struct ext4_inode` 组成的线性数组。该表的大小被设置为至少可以存储 `sb.s_inode_size * sb.s_inodes_per_group` 字节。包含某个 inode 的块组编号可以通过 `(inode_number - 1) / sb.s_inodes_per_group` 来计算，而该组内的偏移量则是 `(inode_number - 1) % sb.s_inodes_per_group`。没有编号为 0 的 inode。
inode 校验和是根据文件系统 UUID、inode 编号和 inode 结构本身计算得出的。
inode 表项在 `struct ext4_inode` 中的布局如下：
.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1
   :class: longtable

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le16
     - i_mode
     - 文件模式。参见下面的 i_mode_ 表格
* - 0x2
     - __le16
     - i_uid
     - 所有者 UID 的低 16 位
* - 0x4
     - __le32
     - i_size_lo
     - 文件大小的低 32 位（以字节为单位）
* - 0x8
     - __le32
     - i_atime
     - 最后访问时间，从纪元开始的秒数。然而，如果设置了 EA_INODE inode 标志，则此 inode 存储一个扩展属性值，此字段包含该值的校验和
* - 0xC
     - __le32
     - i_ctime
     - 最后修改 inode 时间，从纪元开始的秒数。然而，如果设置了 EA_INODE inode 标志，则此 inode 存储一个扩展属性值，此字段包含该属性值引用计数的低 32 位
* - 0x10
     - __le32
     - i_mtime
     - 数据最后修改时间，从纪元开始的秒数。然而，如果设置了 EA_INODE inode 标志，则此 inode 存储一个扩展属性值，此字段包含拥有该扩展属性的 inode 编号
* - 0x14
     - __le32
     - i_dtime
     - 删除时间，从纪元开始的秒数
* - 0x18
     - __le16
     - i_gid
     - GID 的低 16 位
* - 0x1A
     - __le16
     - i_links_count
     - 硬链接计数。通常情况下，ext4 不允许一个inode有超过 65,000 个硬链接。这适用于文件和目录，意味着一个目录中不能有超过 64,998 个子目录（每个子目录的 '..' 入口算作一个硬链接，目录本身的 '.' 入口也一样）。启用 DIR_NLINK 特性后，ext4 通过将此字段设置为 1 来表示硬链接数量未知，从而支持超过 64,998 个子目录。
* - 0x1C
     - __le32
     - i_blocks_lo
     - “块”计数的低 32 位。如果文件系统没有设置 huge_file 特性标志，则文件占用 `i_blocks_lo` 个 512 字节的块。如果设置了 huge_file 并且 `inode.i_flags` 中未设置 EXT4_HUGE_FILE_FL，则文件占用 `i_blocks_lo + (i_blocks_hi << 32)` 个 512 字节的块。如果设置了 huge_file 并且 `inode.i_flags` 中设置了 EXT4_HUGE_FILE_FL，则该文件占用 `(i_blocks_lo + i_blocks_hi) << 32` 个文件系统块。
* - 0x20
     - __le32
     - i_flags
     - inode 标志。参见下面的 i_flags_ 表格
* - 0x24
     - 4 字节
     - i_osd1
     - 更多细节请参见 i_osd1_ 表格
* - 0x28
     - 60 字节
     - i_block[EXT4_N_BLOCKS=15]
     - 块映射或范围树。参见“inode.i_block 的内容”部分
* - 0x64
     - __le32
     - i_generation
     - 文件版本（用于 NFS）
* - 0x68
     - __le32
     - i_file_acl_lo
     - 扩展属性块的低 32 位。ACL 当然是许多可能的扩展属性之一；我认为这个字段名称是由于扩展属性最初被用于 ACL。
* - 0x6C
     - __le32
     - i_size_high / i_dir_acl
     - 文件/目录大小的高 32 位。在 ext2/3 中，这个字段名为 i_dir_acl，尽管它通常被设置为零且从未使用过。
* - 0x70
     - __le32
     - i_obso_faddr
     - （已废弃）片段地址
* - 0x74
     - 12 字节
     - i_osd2
     - 更多详情请参见表 i_osd2_
* - 0x80
     - __le16
     - i_extra_isize
     - 该inode的大小 - 128。或者，原始ext2 inode之后的扩展inode字段的大小，包括这个字段
* - 0x82
     - __le16
     - i_checksum_hi
     - inode校验和的高16位
* - 0x84
     - __le32
     - i_ctime_extra
     - 额外的更改时间位。这提供了亚秒级精度。参见inode时间戳部分
* - 0x88
     - __le32
     - i_mtime_extra
     - 额外的修改时间位。这提供了亚秒级精度
* - 0x8C
     - __le32
     - i_atime_extra
     - 额外的访问时间位。这提供了亚秒级精度
* - 0x90
     - __le32
     - i_crtime
     - 文件创建时间，自纪元以来的秒数
* - 0x94
     - __le32
     - i_crtime_extra
     - 额外的文件创建时间位。这提供了亚秒级精度
* - 0x98
     - __le32
     - i_version_hi
     - 版本号的高32位
* - 0x9C
     - __le32
     - i_projid
     - 项目ID
```markdown
.. _i_mode:

`i_mode` 的值是由以下标志组合而成的：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - S_IXOTH（其他人可执行）
   * - 0x2
     - S_IWOTH（其他人可写入）
   * - 0x4
     - S_IROTH（其他人可读取）
   * - 0x8
     - S_IXGRP（组成员可执行）
   * - 0x10
     - S_IWGRP（组成员可写入）
   * - 0x20
     - S_IRGRP（组成员可读取）
   * - 0x40
     - S_IXUSR（所有者可执行）
   * - 0x80
     - S_IWUSR（所有者可写入）
   * - 0x100
     - S_IRUSR（所有者可读取）
   * - 0x200
     - S_ISVTX（粘滞位）
   * - 0x400
     - S_ISGID（设置GID）
   * - 0x800
     - S_ISUID（设置UID）
   * -
     - 这些是互斥的文件类型：
   * - 0x1000
     - S_IFIFO（FIFO）
   * - 0x2000
     - S_IFCHR（字符设备）
   * - 0x4000
     - S_IFDIR（目录）
   * - 0x6000
     - S_IFBLK（块设备）
   * - 0x8000
     - S_IFREG（普通文件）
   * - 0xA000
     - S_IFLNK（符号链接）
   * - 0xC000
     - S_IFSOCK（套接字）

.. _i_flags:

`i_flags` 字段是由这些值组合而成的：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - 此文件需要安全删除（EXT4_SECRM_FL）。 （未实现）
   * - 0x2
     - 应该保留此文件，以便在需要时进行恢复（EXT4_UNRM_FL）。 （未实现）
   * - 0x4
     - 文件已压缩（EXT4_COMPR_FL）。 （实际未实现）
   * - 0x8
     - 对文件的所有写入必须同步（EXT4_SYNC_FL）
   * - 0x10
     - 文件不可更改（EXT4_IMMUTABLE_FL）
   * - 0x20
     - 文件只能追加（EXT4_APPEND_FL）
   * - 0x40
     - dump(1) 工具不应备份此文件（EXT4_NODUMP_FL）
   * - 0x80
     - 不更新访问时间（EXT4_NOATIME_FL）
   * - 0x100
     - 脏压缩文件（EXT4_DIRTY_FL）。 （未使用）
   * - 0x200
     - 文件有一个或多个压缩簇（EXT4_COMPRBLK_FL）。 （未使用）
   * - 0x400
     - 不压缩文件（EXT4_NOCOMPR_FL）。 （未使用）
   * - 0x800
     - 加密的inode（EXT4_ENCRYPT_FL）。此位值之前是EXT4_ECOMPR_FL（压缩错误），但从未使用过
   * - 0x1000
     - 目录具有哈希索引（EXT4_INDEX_FL）
   * - 0x2000
     - AFS魔法目录（EXT4_IMAGIC_FL）
   * - 0x4000
     - 文件数据必须始终通过日志写入（EXT4_JOURNAL_DATA_FL）
   * - 0x8000
     - 文件尾部不应合并（EXT4_NOTAIL_FL）。 （ext4未使用）
   * - 0x10000
     - 所有目录条目数据应同步写入（参见 `dirsync`）（EXT4_DIRSYNC_FL）
```
* - 0x20000
     - 目录层次结构的顶部（EXT4_TOPDIR_FL）
* - 0x40000
     - 这是一个大文件（EXT4_HUGE_FILE_FL）
* - 0x80000
     - 索引节点使用扩展（EXT4_EXTENTS_FL）
* - 0x100000
     - 验证保护文件（EXT4_VERITY_FL）
* - 0x200000
     - 索引节点在其数据块中存储一个大的扩展属性值（EXT4_EA_INODE_FL）
* - 0x400000
     - 此文件在EOF之后分配了块（EXT4_EOFBLOCKS_FL）（已弃用）
* - 0x01000000
     - 索引节点是快照（`EXT4_SNAPFILE_FL`）。（不在主线版本中）
* - 0x04000000
     - 快照正在被删除（`EXT4_SNAPFILE_DELETED_FL`）。（不在主线版本中）
* - 0x08000000
     - 快照缩小已完成（`EXT4_SNAPFILE_SHRUNK_FL`）。（不在主线版本中）
* - 0x10000000
     - 索引节点有内联数据（EXT4_INLINE_DATA_FL）
* - 0x20000000
     - 创建具有相同项目ID的子项（EXT4_PROJINHERIT_FL）
* - 0x80000000
     - 为ext4库保留（EXT4_RESERVED_FL）
* -
     - 聚合标志：
   * - 0x705BDFFF
     - 用户可见的标志
* - 0x604BC0FF
    - 用户可修改的标志。请注意，虽然可以使用 `setattr` 设置 `EXT4_JOURNAL_DATA_FL` 和 `EXT4_EXTENTS_FL` 标志，但它们并不在内核的 `EXT4_FL_USER_MODIFIABLE` 掩码中，因为这些标志需要以特殊方式处理，并且被排除在直接保存到 `i_flags` 的标志集合之外。

.. _i_osd1:

`osd1` 字段的含义取决于创建者：

Linux:

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - l_i_version
     - inode 版本。但是，如果设置了 EA_INODE inode 标志，则此 inode 存储一个扩展属性值，该字段包含属性值引用计数的高 32 位

Hurd:

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - h_i_translator
     - ??

Masix:

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - m_i_reserved
     - ??

.. _i_osd2:

`osd2` 字段的含义取决于文件系统的创建者：

Linux:

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le16
     - l_i_blocks_high
     - 块计数的高 16 位。请参阅附在 `i_blocks_lo` 上的注释
* - 0x2
     - __le16
     - l_i_file_acl_high
     - 扩展属性块（历史上是文件 ACL 位置）的高 16 位。请参阅下面的扩展属性部分
* - 0x4
     - __le16
     - l_i_uid_high
     - 所有者 UID 的高 16 位
* - 0x6
     - __le16
     - l_i_gid_high
     - GID 的高 16 位
* - 0x8
     - __le16
     - l_i_checksum_lo
     - inode 校验和的低 16 位
* - 0xA
     - __le16
     - l_i_reserved
     - 未使用

Hurd:

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le16
     - h_i_reserved1
     - ??
   * - 0x2
     - __u16
     - h_i_mode_high
     - 文件模式的高 16 位
* - 0x4
     - __le16
     - h_i_uid_high
     - 所有者 UID 的高 16 位
* - 0x6
     - __le16
     - h_i_gid_high
     - GID 的高 16 位
* - 0x8
     - __u32
     - h_i_author
     - 作者代码？

Masix：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le16
     - h_i_reserved1
     - ??
   * - 0x2
     - __u16
     - m_i_file_acl_high
     - 扩展属性块的高 16 位（历史上，文件 ACL 位置）
* - 0x4
     - __u32
     - m_i_reserved2[2]
     - ??

Inode 大小
~~~~~~~~~~

在 ext2 和 ext3 中，inode 结构大小固定为 128 字节（`EXT2_GOOD_OLD_INODE_SIZE`），每个 inode 的磁盘记录大小也为 128 字节。从 ext4 开始，可以在格式化时为文件系统中的所有 inode 分配更大的磁盘 inode，以提供超出原始 ext2 inode 结束位置的空间。磁盘 inode 记录大小记录在超级块中作为 `s_inode_size`。结构 `ext4_inode` 超出原始 128 字节 ext2 inode 的实际使用字节数记录在每个 inode 的 `i_extra_isize` 字段中，这允许 `struct ext4_inode` 在新内核中扩展而无需升级所有磁盘 inode。访问超出 `EXT2_GOOD_OLD_INODE_SIZE` 的字段应验证是否在 `i_extra_isize` 范围内。默认情况下，ext4 inode 记录为 256 字节，并且（截至 2019 年 8 月）inode 结构为 160 字节（`i_extra_isize = 32`）。inode 结构结束位置和 inode 记录结束位置之间的额外空间可用于存储扩展属性。每个 inode 记录可以大到文件系统的块大小，尽管这样做并不高效。

查找 Inode
~~~~~~~~~~

每个块组包含 `sb->s_inodes_per_group` 个 inode。由于定义上 inode 0 不存在，可以使用此公式找到 inode 所在的块组：`bg = (inode_num - 1) / sb->s_inodes_per_group`。特定的 inode 可以在块组的 inode 表中通过 `index = (inode_num - 1) % sb->s_inodes_per_group` 找到。要获取 inode 表内的字节地址，使用 `offset = index * sb->s_inode_size`。

Inode 时间戳
~~~~~~~~~~

在 inode 结构的低 128 字节中记录了四个时间戳——inode 更改时间（ctime）、访问时间（atime）、数据修改时间（mtime）以及删除时间（dtime）。这四个字段是 32 位有符号整数，表示自 Unix 纪元（1970-01-01 00:00:00 GMT）以来的秒数，这意味着这些字段将在 2038 年 1 月溢出。如果文件系统没有 orphan_file 特性，则未链接到任何目录但仍处于打开状态的 inode（孤儿 inode）会将 dtime 字段重用于孤儿列表。超级块字段 `s_last_orphan` 指向孤儿列表中的第一个 inode；dtime 则是下一个孤儿 inode 的编号，如果没有更多孤儿则为零。
如果 inode 结构大小 `sb->s_inode_size` 大于 128 字节并且 `i_inode_extra` 字段足够容纳相应的 `i_[cma]time_extra` 字段，则 ctime、atime 和 mtime inode 字段扩展为 64 位。在这个“额外”的 32 位字段中，低两位用于将 32 位秒字段扩展为 34 位宽；高 30 位用于提供纳秒时间戳精度。因此，时间戳不会在 2446 年 5 月之前溢出。dtime 未扩展。还有一个第五个时间戳来记录 inode 创建时间（crtime）；这个字段是 64 位宽并以与 64 位 [cma]time 相同的方式解码。crtime 和 dtime 都无法通过常规的 stat() 接口访问，但 debugfs 会报告它们。
我们使用 32 位有符号时间值加上（2^32 * （额外纪元位））。
换句话说：

.. list-table::
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - 额外纪元位
     - 32 位时间的 MSB
     - 从 32 位到 64 位 tv_sec 的调整
     - 解码后的 64 位 tv_sec
     - 有效时间范围
   * - 0 0
     - 1
     - 0
     - ``-0x80000000 - -0x00000001``
     - 1901-12-13 至 1969-12-31
   * - 0 0
     - 0
     - 0
     - ``0x000000000 - 0x07fffffff``
     - 1970-01-01 至 2038-01-19
   * - 0 1
     - 1
     - 0x100000000
     - ``0x080000000 - 0x0ffffffff``
     - 2038-01-19 至 2106-02-07
   * - 0 1
     - 0
     - 0x100000000
     - ``0x100000000 - 0x17fffffff``
     - 2106-02-07 至 2174-02-25
   * - 1 0
     - 1
     - 0x200000000
     - ``0x180000000 - 0x1ffffffff``
     - 2174-02-25 至 2242-03-16
   * - 1 0
     - 0
     - 0x200000000
     - ``0x200000000 - 0x27fffffff``
     - 2242-03-16 至 2310-04-04
   * - 1 1
     - 1
     - 0x300000000
     - ``0x280000000 - 0x2ffffffff``
     - 2310-04-04 至 2378-04-22
   * - 1 1
     - 0
     - 0x300000000
     - ``0x300000000 - 0x37fffffff``
     - 2378-04-22 至 2446-05-10

这种编码方式有些奇怪，因为实际上正数值的数量几乎是负数值数量的七倍。在 2038 年之后日期的解码和编码也存在长期问题，在内核 3.12 和 e2fsprogs 1.42.8 中似乎并未修复。64 位内核在 1901 年至 1970 年之间的日期上错误地使用了额外纪元位 1,1。在某个时候，内核将会被修复，e2fsck 将修正这种情况，假设它在 2310 年前运行。
