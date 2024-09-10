SPDX 许可证标识符: GPL-2.0

超级块
------

超级块记录了关于包含文件系统的各种信息，例如块计数、inode 计数、支持的特性、维护信息等。如果启用了 `sparse_super` 特性标志，则仅在组号为 0 或 3、5、7 的幂次的组中保留超级块和组描述符的冗余副本。如果没有启用该标志，则在所有组中都保留冗余副本。

超级块校验和是针对包括文件系统 UUID 在内的超级块结构进行计算的。

ext4 超级块在 `struct ext4_super_block` 中的布局如下：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - s_inodes_count
     - 总的 inode 数量
* - 0x4
     - __le32
     - s_blocks_count_lo
     - 总的块数量
* - 0x8
     - __le32
     - s_r_blocks_count_lo
     - 只有超级用户可以分配的块数量
* - 0xC
     - __le32
     - s_free_blocks_count_lo
     - 空闲块数量
* - 0x10
     - __le32
     - s_free_inodes_count
     - 空闲 inode 数量
* - 0x14
     - __le32
     - s_first_data_block
     - 第一个数据块。对于 1k 块大小的文件系统，这至少应该是 1；对于其他块大小，通常是 0
* - 0x18
     - __le32
     - s_log_block_size
     - 块大小 = 2 ^ (10 + s_log_block_size)
* - 0x1C
     - __le32
     - s_log_cluster_size
     - 如果启用了 bigalloc，簇大小为 2^(10 + s_log_cluster_size) 块。否则 s_log_cluster_size 必须等于 s_log_block_size
* - 0x20
     - __le32
     - s_blocks_per_group
     - 每组的块数
* - 0x24
     - __le32
     - s_clusters_per_group
     - 如果启用了 bigalloc，则每组的簇数。否则 s_clusters_per_group 必须等于 s_blocks_per_group
* - 0x28
     - __le32
     - s_inodes_per_group
     - 每组的inode数
* - 0x2C
     - __le32
     - s_mtime
     - 挂载时间，自纪元以来的秒数
* - 0x30
     - __le32
     - s_wtime
     - 写入时间，自纪元以来的秒数
* - 0x34
     - __le16
     - s_mnt_count
     - 自上次 fsck 以来的挂载次数
* - 0x36
     - __le16
     - s_max_mnt_count
     - 需要进行 fsck 的最大挂载次数
* - 0x38
     - __le16
     - s_magic
     - 魔术签名，值为 0xEF53
* - 0x3A
     - __le16
     - s_state
     - 文件系统状态。更多信息请参见 super_state_
* - 0x3C
     - __le16
     - s_errors
     - 发现错误时的行为。更多信息请参见 super_errors_
* - 0x3E
     - __le16
     - s_minor_rev_level
     - 次要修订级别
* - 0x40
     - __le32
     - s_lastcheck
     - 上次检查的时间，自纪元以来的秒数
* - 0x44
     - __le32
     - s_checkinterval
     - 检查之间的最大时间间隔，以秒为单位
* - 0x48
     - __le32
     - s_creator_os
     - 创建者操作系统。更多信息请参见 super_creator_ 表
* - 0x4C
     - __le32
     - s_rev_level
     - 修订级别。更多信息请参见 super_revision_ 表
* - 0x50
     - __le16
     - s_def_resuid
     - 预留块的默认用户ID
* - 0x52
     - __le16
     - s_def_resgid
     - 预留块的默认组ID
* -
     -
     -
     - 这些字段仅适用于 EXT4_DYNAMIC_REV 超级块

注意：兼容特性集与不兼容特性集之间的区别在于，如果内核不知道不兼容特性集中设置的某个位，则应拒绝挂载该文件系统。
e2fsck 的要求更为严格；如果它不知道兼容或不兼容特性集中的某个特性，则必须终止运行，并且不得尝试处理其不了解的内容。
* - 0x54
     - __le32
     - s_first_ino
     - 第一个非预留inode
* - 0x58
     - __le16
     - s_inode_size
     - inode结构的大小，以字节为单位
* - 0x5A
     - __le16
     - s_block_group_nr
     - 此超级块所在的块组编号
* - 0x5C
     - __le32
     - s_feature_compat
     - 兼容特性集标志。即使内核不理解某个标志，它仍然可以读写这个文件系统；fsck不应该这样做。更多信息请参见super_compat_表
* - 0x60
     - __le32
     - s_feature_incompat
     - 不兼容特性集。如果内核或fsck不理解这些位中的某一位，它应该停止。更多信息请参见super_incompat_表
* - 0x64
     - __le32
     - s_feature_ro_compat
     - 只读兼容特性集。如果内核不理解这些位中的某一位，它仍然可以只读挂载。更多信息请参见super_rocompat_表
* - 0x68
     - __u8
     - s_uuid[16]
     - 卷的128位UUID
* - 0x78
     - char
     - s_volume_name[16]
     - 卷标签
* - 0x88
     - char
     - s_last_mounted[64]
     - 文件系统上次挂载的目录
* - 0xC8
     - __le32
     - s_algorithm_usage_bitmap
     - 用于压缩（在e2fsprogs/Linux中未使用）
   * -
     -
     -
     - 性能提示。只有当EXT4_FEATURE_COMPAT_DIR_PREALLOC标志开启时，才应进行目录预分配
* - 0xCC
     - __u8
     - s_prealloc_blocks
     - 为...文件尝试预分配的块数？（在e2fsprogs/Linux中未使用）
   * - 0xCD
     - __u8
     - s_prealloc_dir_blocks
     - 为目录预分配的块数。（在e2fsprogs/Linux中未使用）
   * - 0xCE
     - __le16
     - s_reserved_gdt_blocks
     - 为将来文件系统扩展预留的GDT条目数量
* -
     -
     -
     - 日志记录支持仅在设置了EXT4_FEATURE_COMPAT_HAS_JOURNAL标志时有效
* - 0xD0
     - __u8
     - s_journal_uuid[16]
     - 日志超级块的UUID
   * - 0xE0
     - __le32
     - s_journal_inum
     - 日志文件的inode编号
* - 0xE4
     - __le32
     - s_journal_dev
     - 如果设置了外部日志功能标志，则为日志文件的设备编号
* - 0xE8
     - __le32
     - s_last_orphan
     - 孤儿inode列表的起始位置
* - 0xEC
     - __le32
     - s_hash_seed[4]
     - HTREE哈希种子
* - 0xFC
     - __u8
     - s_def_hash_version
     - 目录哈希使用的默认哈希算法。更多信息请参见super_def_hash_
* - 0xFD
     - __u8
     - s_jnl_backup_type
     - 如果此值为0或EXT3_JNL_BACKUP_BLOCKS（1），则``s_jnl_blocks``字段包含inode的``i_block[]``数组和``i_size``的副本
* - 0xFE
     - __le16
     - s_desc_size
     - 如果设置了64位不兼容特性标志，则组描述符的大小，以字节为单位
* - 0x100
     - __le32
     - s_default_mount_opts
     - 默认挂载选项。更多信息请参见super_mountopts_表
* - 0x104
     - __le32
     - s_first_meta_bg
     - 如果启用了 meta_bg 特性，则为第一个元数据块组
* - 0x108
     - __le32
     - s_mkfs_time
     - 文件系统创建的时间，自纪元以来的秒数
* - 0x10C
     - __le32
     - s_jnl_blocks[17]
     - 日志inode的 ``i_block[]`` 数组的备份，在前15个元素中，第16和17个元素分别是 i_size_high 和 i_size
* -
     -
     -
     - 仅当设置了 EXT4_FEATURE_COMPAT_64BIT 时，64位支持才有效
* - 0x150
     - __le32
     - s_blocks_count_hi
     - 块计数的高32位
* - 0x154
     - __le32
     - s_r_blocks_count_hi
     - 预留块计数的高32位
* - 0x158
     - __le32
     - s_free_blocks_count_hi
     - 空闲块计数的高32位
* - 0x15C
     - __le16
     - s_min_extra_isize
     - 所有inode至少有 # 字节
* - 0x15E
     - __le16
     - s_want_extra_isize
     - 新的inode应该预留 # 字节
* - 0x160
     - __le32
     - s_flags
     - 各种标志。更多信息请参见 super_flags_ 表格
* - 0x164
     - __le16
     - s_raid_stride
     - RAID步长。这是在切换到下一个磁盘之前从磁盘读取或写入的逻辑块数量。这会影响文件系统元数据的位置，希望能使RAID存储更快。

* - 0x166
     - __le16
     - s_mmp_interval
     - 多挂载防护（MMP）检查等待的秒数。理论上，MMP是一种机制，用于记录超级块中的主机和设备是否已挂载文件系统，以防止多次挂载。此功能似乎尚未实现。

* - 0x168
     - __le64
     - s_mmp_block
     - 多挂载防护数据所在的块号

* - 0x170
     - __le32
     - s_raid_stripe_width
     - RAID条带宽度。这是在返回当前磁盘之前从磁盘读取或写入的逻辑块数量。该值用于块分配器尝试减少RAID5/6中的读-修改-写操作次数。

* - 0x174
     - __u8
     - s_log_groups_per_flex
     - 每个灵活块组的大小为2 ^ `s_log_groups_per_flex`

* - 0x175
     - __u8
     - s_checksum_type
     - 元数据校验和算法类型。唯一有效的值是1（crc32c）

* - 0x176
     - __le16
     - s_reserved_pad
     -

* - 0x178
     - __le64
     - s_kbytes_written
     - 自文件系统创建以来写入的KiB数量

* - 0x180
     - __le32
     - s_snapshot_inum
     - 当前活动快照的inode编号。（在e2fsprogs/Linux中未使用）

* - 0x184
     - __le32
     - s_snapshot_id
     - 当前活动快照的顺序ID。（在e2fsprogs/Linux中未使用）

* - 0x188
     - __le64
     - s_snapshot_r_blocks_count
     - 为当前活动快照的未来使用预留的块数量。（在e2fsprogs/Linux中未使用）

* - 0x190
     - __le32
     - s_snapshot_list
     - 在线快照列表头部的inode编号。（在e2fsprogs/Linux中未使用）

* - 0x194
     - __le32
     - s_error_count
     - 观察到的错误数量

* - 0x198
     - __le32
     - s_first_error_time
     - 首次发生错误的时间，自纪元开始以来的秒数

* - 0x19C
     - __le32
     - s_first_error_ino
     - 首次错误涉及的inode
* - 0x1A0
     - __le64
     - s_first_error_block
     - 首次错误涉及的块号
* - 0x1A8
     - __u8
     - s_first_error_func[32]
     - 发生错误的函数名称
* - 0x1C8
     - __le32
     - s_first_error_line
     - 发生错误的行号
* - 0x1CC
     - __le32
     - s_last_error_time
     - 最近一次错误发生的时间（自纪元以来的秒数）
* - 0x1D0
     - __le32
     - s_last_error_ino
     - 最近一次错误涉及的inode号
* - 0x1D4
     - __le32
     - s_last_error_line
     - 最近一次错误发生的行号
* - 0x1D8
     - __le64
     - s_last_error_block
     - 最近一次错误涉及的块号
* - 0x1E0
     - __u8
     - s_last_error_func[32]
     - 最近一次错误发生的函数名称
* - 0x200
     - __u8
     - s_mount_opts[64]
     - 挂载选项的ASCII字符串
* - 0x240
     - __le32
     - s_usr_quota_inum
     - 用户`quota`文件的inode号
* - 0x244
     - __le32
     - s_grp_quota_inum
     - 组 `quota <quota>` 文件的inode编号
* - 0x248
     - __le32
     - s_overhead_blocks
     - 文件系统中的开销块/簇数。（嗯？这个字段始终为零，这意味着内核会动态计算它。）
* - 0x24C
     - __le32
     - s_backup_bgs[2]
     - 包含超级块备份的块组（如果启用了sparse_super2）
* - 0x254
     - __u8
     - s_encrypt_algos[4]
     - 正在使用的加密算法。任何时候最多可以使用四种算法；有效的算法代码见下面的super_encrypt_表
* - 0x258
     - __u8
     - s_encrypt_pw_salt[16]
     - 用于加密的string2key算法的盐值
* - 0x268
     - __le32
     - s_lpf_ino
     - lost+found的inode编号
* - 0x26C
     - __le32
     - s_prj_quota_inum
     - 跟踪项目配额的inode
* - 0x270
     - __le32
     - s_checksum_seed
     - 用于metadata_csum计算的校验和种子。此值为crc32c(~0, $orig_fs_uuid)
* - 0x274
     - __u8
     - s_wtime_hi
     - s_wtime字段的高8位
* - 0x275
     - __u8
     - s_mtime_hi
     - s_mtime字段的高8位
* - 0x276
     - __u8
     - s_mkfs_time_hi
     - s_mkfs_time字段的高8位
* - 0x277
     - __u8
     - s_lastcheck_hi
     - s_lastcheck字段的高8位
* - 0x278
     - __u8
     - s_first_error_time_hi
     - s_first_error_time字段的高8位
* - 0x279
     - __u8
     - s_last_error_time_hi
     - `s_last_error_time` 字段的高 8 位
* - 0x27A
     - __u8
     - s_pad[2]
     - 零填充
* - 0x27C
     - __le16
     - s_encoding
     - 文件名字符集编码
* - 0x27E
     - __le16
     - s_encoding_flags
     - 文件名字符集编码标志
* - 0x280
     - __le32
     - s_orphan_file_inum
     - 孤儿文件的inode编号
* - 0x284
     - __le32
     - s_reserved[94]
     - 填充到块末尾
* - 0x3FC
     - __le32
     - s_checksum
     - 超级块校验和
.. _super_state:

超级块状态是以下几种组合之一：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0001
     - 干净卸载
   * - 0x0002
     - 检测到错误
   * - 0x0004
     - 正在恢复孤儿文件

.. _super_errors:

超级块错误策略是以下几种之一：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 1
     - 继续
   * - 2
     - 只读重新挂载
   * - 3
     - 引发系统崩溃

.. _super_creator:

文件系统的创建者是以下几种之一：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0
     - Linux
   * - 1
     - Hurd
   * - 2
     - Masix
   * - 3
     - FreeBSD
   * - 4
     - Lites

.. _super_revision:

超级块修订版本是以下几种之一：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0
     - 原始格式
   * - 1
     - 带动态inode大小的v2格式

请注意，`EXT4_DYNAMIC_REV` 指的是修订版本1或更高版本的文件系统。

.. _super_compat:

超级块兼容特性字段是以下任一特性的组合：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - 目录预分配（COMPAT_DIR_PREALLOC）
* - 0x2
     - “imagic inodes”。代码中不清楚这是什么功能（COMPAT_IMAGIC_INODES）
* - 0x4
     - 拥有日志 (COMPAT_HAS_JOURNAL)
* - 0x8
     - 支持扩展属性 (COMPAT_EXT_ATTR)
* - 0x10
     - 为文件系统扩展预留了 GDT 块 (COMPAT_RESIZE_INODE)。需要 RO_COMPAT_SPARSE_SUPER
* - 0x20
     - 拥有目录索引 (COMPAT_DIR_INDEX)
* - 0x40
     - “懒惰 BG”。未在 Linux 内核中使用，似乎是用于未初始化的块组？(COMPAT_LAZY_BG)
* - 0x80
     - “排除inode”。未使用。(COMPAT_EXCLUDE_INODE)
* - 0x100
     - “排除位图”。似乎用于指示快照相关排除位图的存在？未在内核或 e2fsprogs 中定义 (COMPAT_EXCLUDE_BITMAP)
* - 0x200
     - 稀疏超级块，版本2。如果设置了此标志，则 SB 字段 s_backup_bgs 指向包含备份超级块的两个块组 (COMPAT_SPARSE_SUPER2)
* - 0x400
     - 支持快速提交。尽管快速提交块与旧版本不兼容，但日志中并不总是存在快速提交块。如果日志中存在快速提交块，则设置 JBD2 不兼容特性 (JBD2_FEATURE_INCOMPAT_FAST_COMMIT) (COMPAT_FAST_COMMIT)
* - 0x1000
     - 孤儿文件分配。这是用于更高效地跟踪已解除链接但仍打开的inode的特殊文件。当文件中有任何条目时，我们还会设置适当的只读兼容特性 (RO_COMPAT_ORPHAN_PRESENT)

.. _super_incompat:

超级块不兼容特性字段是以下任一特性的组合：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - 压缩 (INCOMPAT_COMPRESSION)
* - 0x2
     - 目录条目记录文件类型。参见下方的ext4_dir_entry_2（INCOMPAT_FILETYPE）
* - 0x4
     - 文件系统需要恢复（INCOMPAT_RECOVER）
* - 0x8
     - 文件系统有一个独立的日志设备（INCOMPAT_JOURNAL_DEV）
* - 0x10
     - 元数据块组。参见此功能的早期讨论（INCOMPAT_META_BG）
* - 0x40
     - 此文件系统中的文件使用扩展（extent）（INCOMPAT_EXTENTS）
* - 0x80
     - 启用2^64个区块大小的文件系统（INCOMPAT_64BIT）
* - 0x100
     - 多挂载保护（INCOMPAT_MMP）
* - 0x200
     - 灵活的块组。参见此功能的早期讨论（INCOMPAT_FLEX_BG）
* - 0x400
     - 索引节点可用于存储大型扩展属性值（INCOMPAT_EA_INODE）
* - 0x1000
     - 目录条目中包含数据（INCOMPAT_DIRDATA）。 （尚未实现？）
* - 0x2000
     - 元数据校验和种子存储在超级块中。此功能允许管理员在文件系统挂载时更改元数据校验和文件系统的UUID；没有它，校验和定义要求重写所有元数据块（INCOMPAT_CSUM_SEED）
* - 0x4000
     - 大目录 >2GB 或 3 级 htree (INCOMPAT_LARGEDIR)。在此功能之前，目录不能大于 4GiB，并且 htree 的深度不能超过 2 层。如果启用了此功能，则目录可以大于 4GiB 并具有最大 3 层的 htree 深度。
* - 0x8000
     - 数据在inode中 (INCOMPAT_INLINE_DATA)
* - 0x10000
     - 文件系统中有加密的inode (INCOMPAT_ENCRYPT)

.. _super_rocompat:

超级块只读兼容特性字段是以下各项的组合：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - 稀疏超级块。参见前面关于此特性的讨论 (RO_COMPAT_SPARSE_SUPER)
* - 0x2
     - 此文件系统用于存储大于 2GiB 的文件 (RO_COMPAT_LARGE_FILE)
* - 0x4
     - 内核或 e2fsprogs 中未使用 (RO_COMPAT_BTREE_DIR)
* - 0x8
     - 此文件系统的文件大小以逻辑块为单位表示，而不是 512 字节扇区。这意味着这是一个非常大的文件！(RO_COMPAT_HUGE_FILE)
   * - 0x10
     - 组描述符有校验和。除了检测损坏外，这对于使用未初始化组进行懒惰格式化也很有用 (RO_COMPAT_GDT_CSUM)
* - 0x20
     - 表示旧的 ext3 32,000 子目录限制不再适用 (RO_COMPAT_DIR_NLINK)。如果目录的 i_links_count 超过 64,999，则将其设置为 1
* - 0x40
     - 表示此文件系统上存在大inode (RO_COMPAT_EXTRA_ISIZE)
* - 0x80
     - 此文件系统有一个快照 (RO_COMPAT_HAS_SNAPSHOT)
* - 0x100
     - `配额 <Quota>`__ (RO_COMPAT_QUOTA)
* - 0x200
     - 该文件系统支持“大分配”，这意味着文件扩展区是以块簇为单位进行跟踪，而不是以块为单位（RO_COMPAT_BIGALLOC）
* - 0x400
     - 该文件系统支持元数据校验和（RO_COMPAT_METADATA_CSUM；意味着也支持RO_COMPAT_GDT_CSUM，尽管GDT_CSUM不应被设置）
* - 0x800
     - 文件系统支持副本。此功能既不在内核中也不在e2fsprogs中。（RO_COMPAT_REPLICA）
* - 0x1000
     - 只读文件系统映像；内核不会将此映像挂载为读写，并且大多数工具会拒绝向该映像写入（RO_COMPAT_READONLY）
* - 0x2000
     - 文件系统跟踪项目配额。（RO_COMPAT_PROJECT）
* - 0x8000
     - 文件系统上可能存在验证节点。（RO_COMPAT_VERITY）
* - 0x10000
     - 表示孤儿文件可能包含有效的孤儿条目，因此在挂载文件系统时需要清理这些条目（RO_COMPAT_ORPHAN_PRESENT）

.. _super_def_hash:

``s_def_hash_version``字段如下所示：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0
     - 传统
* - 0x1
     - 半MD4
* - 0x2
     - 茶
* - 0x3
     - 传统，未签名
* - 0x4
     - 半MD4，未签名
* - 0x5
     - 未签名的茶
.. _super_mountopts:

``s_default_mount_opts`` 字段可以是以下任意组合：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0001
     - 在（重新）挂载时打印调试信息。（EXT4_DEFM_DEBUG）
   * - 0x0002
     - 新文件采用包含目录的 gid（而不是当前进程的 fsgid）。 （EXT4_DEFM_BSDGROUPS）
   * - 0x0004
     - 支持用户空间提供的扩展属性。 （EXT4_DEFM_XATTR_USER）
   * - 0x0008
     - 支持 POSIX 访问控制列表（ACL）。 （EXT4_DEFM_ACL）
   * - 0x0010
     - 不支持 32 位 UID。 （EXT4_DEFM_UID16）
   * - 0x0020
     - 所有数据和元数据都提交到日志。（EXT4_DEFM_JMODE_DATA）
   * - 0x0040
     - 所有数据在元数据提交到日志之前被刷新到磁盘。（EXT4_DEFM_JMODE_ORDERED）
   * - 0x0060
     - 数据顺序不受保护；数据可以在元数据写入之后写入。（EXT4_DEFM_JMODE_WBACK）
   * - 0x0100
     - 禁用写入刷新。（EXT4_DEFM_NOBARRIER）
   * - 0x0200
     - 跟踪文件系统中哪些块是元数据，因此不应作为数据块使用。此选项预计在 3.18 版本默认启用。（EXT4_DEFM_BLOCK_VALIDITY）
   * - 0x0400
     - 启用 DISCARD 支持，通知存储设备某些块变为未使用的状态。（EXT4_DEFM_DISCARD）
   * - 0x0800
     - 禁用延迟分配。（EXT4_DEFM_NODELALLOC）

.. _super_flags:

``s_flags`` 字段可以是以下任意组合：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0001
     - 使用已签名目录哈希
* - 0x0002
     - 使用未签名目录哈希
* - 0x0004
     - 用于测试开发代码

.. _super_encrypt:

``s_encrypt_algos`` 列表可以包含以下任何项：

.. list-table::
   :widths: 8 72
   :header-rows: 1

   * - 值
     - 描述
   * - 0
     - 无效算法（ENCRYPTION_MODE_INVALID）
* - 1
     - 256 位 AES 在 XTS 模式下（ENCRYPTION_MODE_AES_256_XTS）
* - 2
     - 256 位 AES 在 GCM 模式下（ENCRYPTION_MODE_AES_256_GCM）
* - 3
     - 256 位 AES 在 CBC 模式下（ENCRYPTION_MODE_AES_256_CBC）

超级块的总大小为 1024 字节。
当然，请提供您需要翻译的文本。
