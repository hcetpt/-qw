SPDX 许可声明标识符: GPL-2.0

块组描述符
-----------------------

文件系统中的每个块组都有一个这样的描述符与之关联。如上文布局部分所述，如果存在组描述符，则它们是块组中的第二项。标准配置是每个块组包含一组完整的块组描述符表，除非设置了 sparse_super 特性标志。
请注意，组描述符记录了位图和inode表的位置（即它们可以浮动）。这意味着在一个块组内，唯一具有固定位置的数据结构是超级块和组描述符表。flex_bg 机制利用这一特性将几个块组合并成一个 flex 组，并将所有组的位图和inode表布局在 flex 组的第一个组中的一段连续空间内。
如果设置了 meta_bg 特性标志，则几个块组合并为一个元组。需要注意的是，在 meta_bg 情况下，较大的元组内的第一个和最后两个块组仅包含元组内部组的描述符。
flex_bg 和 meta_bg 看起来不是互斥的特性。
在 ext2、ext3 以及未启用 64 位特性的 ext4 中，块组描述符长度仅为 32 字节，因此结束于 bg_checksum。在启用了 64 位特性的 ext4 文件系统中，块组描述符扩展到至少下面描述的 64 字节；其大小存储在超级块中。
如果 gdt_csum 设置且 metadata_csum 未设置，则块组校验和为 FS UUID、组号和组描述符结构的 crc16 校验和。如果设置了 metadata_csum，则块组校验和为 FS UUID、组号和组描述符结构校验和的低 16 位。块位图和inode位图的校验和都是基于 FS UUID、组号和整个位图计算得出的。
块组描述符的布局在 `struct ext4_group_desc` 中如下所示：
.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - bg_block_bitmap_lo
     - 块位图位置的低 32 位
* - 0x4
     - __le32
     - bg_inode_bitmap_lo
     - inode 位图位置的低 32 位
* - 0x8
     - __le32
     - bg_inode_table_lo
     - inode 表位置的低 32 位
* - 0xC
     - __le16
     - bg_free_blocks_count_lo
     - 空闲块计数的低16位
* - 0xE
     - __le16
     - bg_free_inodes_count_lo
     - 空闲inode计数的低16位
* - 0x10
     - __le16
     - bg_used_dirs_count_lo
     - 目录计数的低16位
* - 0x12
     - __le16
     - bg_flags
     - 块组标志。参见下面的bgflags_表
* - 0x14
     - __le32
     - bg_exclude_bitmap_lo
     - 快照排除位图位置的低32位
* - 0x18
     - __le16
     - bg_block_bitmap_csum_lo
     - 块位图校验和的低16位
* - 0x1A
     - __le16
     - bg_inode_bitmap_csum_lo
     - inode位图校验和的低16位
* - 0x1C
     - __le16
     - bg_itable_unused_lo
     - 未使用inode计数的低16位。如果设置，我们无需扫描该组inode表中的第
       ``(sb.s_inodes_per_group - gdt.bg_itable_unused)`` 个条目之后的内容
* - 0x1E
     - __le16
     - bg_checksum
     - 组描述符校验和；如果启用了RO_COMPAT_GDT_CSUM特性，则为
       crc16(sb_uuid + group_num + bg_desc)，或者如果启用了
       RO_COMPAT_METADATA_CSUM特性，则为
       crc32c(sb_uuid + group_num + bg_desc) & 0xFFFF。在计算crc16校验和时，
       bg_desc中的bg_checksum字段会被跳过，并且如果使用crc32c校验和，则将其设为零
* -
     -
     -
     - 这些字段仅在启用64位特性且s_desc_size > 32时存在
* - 0x20
     - __le32
     - bg_block_bitmap_hi
     - 块位图位置的高32位
* - 0x24
     - __le32
     - bg_inode_bitmap_hi
     - 索引节点位图位置的高32位
* - 0x28
     - __le32
     - bg_inode_table_hi
     - 索引节点表位置的高32位
* - 0x2C
     - __le16
     - bg_free_blocks_count_hi
     - 可用块计数的高16位
* - 0x2E
     - __le16
     - bg_free_inodes_count_hi
     - 可用索引节点计数的高16位
* - 0x30
     - __le16
     - bg_used_dirs_count_hi
     - 目录计数的高16位
* - 0x32
     - __le16
     - bg_itable_unused_hi
     - 未使用索引节点计数的高16位
* - 0x34
     - __le32
     - bg_exclude_bitmap_hi
     - 快照排除位图位置的高32位
* - 0x38
     - __le16
     - bg_block_bitmap_csum_hi
     - 块位图校验和的高16位
* - 0x3A
     - __le16
     - bg_inode_bitmap_csum_hi
     - 索引节点位图校验和的高16位
* - 0x3C
* - __u32
* - bg_reserved
* - 填充至 64 字节

.. _bgflags:

块组标志可以是以下任意组合：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x1
     - 索引节点表和位图未初始化（EXT4_BG_INODE_UNINIT）
* - 0x2
     - 数据块位图未初始化（EXT4_BG_BLOCK_UNINIT）
* - 0x4
     - 索引节点表已清零（EXT4_BG_INODE_ZEROED）
