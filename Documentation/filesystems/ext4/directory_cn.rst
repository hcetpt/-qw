SPDX 许可证标识符: GPL-2.0

目录条目
--------------

在 ext4 文件系统中，一个目录基本上是一个将任意字节串（通常是 ASCII 编码）映射到文件系统上的inode编号的平面文件。在整个文件系统中，可以有许多目录条目引用同一个inode编号——这些被称为硬链接，这也是为什么硬链接不能引用其他文件系统上的文件的原因。因此，通过读取与特定目录条目相关的数据块来找到目录条目。

线性（经典）目录
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

默认情况下，每个目录以一种“几乎线性”的数组形式列出其条目。之所以说是“几乎”，是因为从内存的角度来看它并不是线性的，因为目录条目不会跨越文件系统块。因此，更准确地说，目录是一系列数据块，并且每个块包含一个线性的目录条目数组。每个块内数组的结束标志是到达该块的末尾；块中的最后一个条目具有记录长度，该长度一直延伸到块的末尾。整个目录的结束标志则是到达文件的末尾。未使用的目录条目通过inode = 0表示。默认情况下，文件系统使用 `struct ext4_dir_entry_2` 来表示目录条目，除非没有设置“filetype”特性标志，在这种情况下使用 `struct ext4_dir_entry`。

原始目录条目的格式是 `struct ext4_dir_entry`，其最大长度为263字节，但实际存储时需要参考 `dirent.rec_len` 来确定确切长度。
以下是 `struct ext4_dir_entry` 的结构：
.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - inode
     - 此目录条目指向的inode编号
* - 0x4
     - __le16
     - rec_len
     - 此目录条目的长度。必须是4的倍数
* - 0x6
     - __le16
     - name_len
     - 文件名长度
* - 0x8
     - char
     - name[EXT4_NAME_LEN]
     - 文件名

由于文件名不能超过255字节，新的目录条目格式缩短了name_len字段，并利用该空间添加了一个文件类型标志，可能是为了避免在遍历目录树时加载所有inode。此格式为 `ext4_dir_entry_2`，其最大长度也是263字节，但实际存储时需要参考 `dirent.rec_len` 来确定确切长度。
以下是 `struct ext4_dir_entry_2` 的结构：
.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - inode
     - 此目录条目指向的inode编号
* - 0x4
     - __le16
     - rec_len
     - 该目录项的长度
* - 0x6
     - __u8
     - name_len
     - 文件名的长度
* - 0x7
     - __u8
     - file_type
     - 文件类型代码，参见下方的 ftype_ 表格
* - 0x8
     - char
     - name[EXT4_NAME_LEN]
     - 文件名

.. _ftype:

目录文件类型为以下值之一：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0
     - 未知
* - 0x1
     - 普通文件
* - 0x2
     - 目录
* - 0x3
     - 字符设备文件
* - 0x4
     - 块设备文件
* - 0x5
     - FIFO
* - 0x6
    - 套接字
* - 0x7
    - 符号链接

为了支持既加密又大小写折叠的目录，我们必须在目录项中也包含哈希信息。我们除了点（`.`）和双点（`..`）条目保持不变外，在`ext4_dir_entry_2`之后追加`ext4_extended_dir_entry_2`。该结构紧跟在`name`之后，并包含在`rec_len`列出的大小内。如果一个目录项使用了这种扩展，则其大小最多可达271字节。

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - hash
     - 目录名称的哈希值
   * - 0x4
     - __le32
     - minor_hash
     - 目录名称的次级哈希值

为了在这类经典的目录块中添加校验和，每个叶块的末尾放置了一个伪`struct ext4_dir_entry`来保存校验和。目录项长度为12字节。inode编号和name_len字段设置为零，以欺骗旧软件忽略看似空的目录项，校验和存储在通常存放名称的位置。该结构为`struct ext4_dir_entry_tail`：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 大小
     - 名称
     - 描述
   * - 0x0
     - __le32
     - det_reserved_zero1
     - inode编号，必须为零
* - 0x4
     - __le16
     - det_rec_len
     - 该目录项的长度，必须为12
* - 0x6
     - __u8
     - det_reserved_zero2
     - 文件名长度，必须为零
* - 0x7
     - __u8
     - det_reserved_ft
     - 文件类型，必须为0xDE
* - 0x8
     - __le32
     - det_checksum
     - 目录叶块校验和

叶目录块校验和是根据文件系统UUID、目录的inode编号、目录的inode生成编号以及整个目录项块（但不包括伪目录项）计算得出的。

哈希树目录
~~~~~~~~~~~

线性数组的目录项对于性能来说不是很好，因此ext3中增加了一项新功能，通过目录项名称的哈希提供更快（但奇特）的平衡树。如果inode中设置了EXT4_INDEX_FL (0x1000)标志，则该目录使用哈希b树（htree）来组织和查找目录项。为了与ext2向后兼容只读模式，此树实际上隐藏在目录文件内部，伪装成“空”的目录数据块！之前提到过，线性目录项表的结束由指向inode 0的条目表示；这一特性被利用来欺骗旧的线性扫描算法，使其认为目录块的其余部分为空，从而继续进行处理。
树的根始终位于目录的第一个数据块中。根据ext2的习惯，'.' 和 '..' 条目必须出现在这个第一块的开头，因此它们被作为两个 `struct ext4_dir_entry_2` 放在这里，并且不存储在树中。根节点的其余部分包含有关树的元数据，最后是一个哈希->块映射，用于查找htree中较低层级的节点。如果 `dx_root.info.indirect_levels` 不为零，则htree有两个层级；根节点映射指向的数据块是一个内部节点，该内部节点通过次要哈希进行索引。此树中的内部节点包含一个清空的 `struct ext4_dir_entry_2`，后面跟着一个次要哈希->块映射，用于查找叶节点。叶节点包含所有 `struct ext4_dir_entry_2` 的线性数组；这些条目（假设）具有相同的哈希值。如果有溢出，条目会简单地溢出到下一个叶节点，并且在内部节点映射中将我们带到下一个叶节点的哈希值的最低有效位会被设置。

要以htree的形式遍历目录，代码计算所需文件名的哈希值并使用它来找到相应的块号。如果树是扁平的，该块是一个可以搜索的目录条目的线性数组；否则，计算文件名的次要哈希值，并将其用于第二个块来找到相应的第三个块号。那个第三个块号将是一个目录条目的线性数组。

要以线性数组的形式遍历目录（如旧代码所做的那样），代码只需读取目录中的每个数据块。用于htree的块将看起来没有任何条目（除了 '.' 和 '..'），因此只有叶节点才会显得有实际内容。

htree的根位于 `struct dx_root` 中，其长度等于一个数据块的长度：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 类型
     - 名称
     - 描述
   * - 0x0
     - __le32
     - dot.inode
     - 此目录的inode编号
* - 0x4
     - __le16
     - dot.rec_len
     - 该记录的长度，12
* - 0x6
     - u8
     - dot.name_len
     - 名称的长度，1
* - 0x7
     - u8
     - dot.file_type
     - 此条目的文件类型，0x2（目录）（如果启用了特性标志）
* - 0x8
     - char
     - dot.name[4]
     - “.\0\0\0”
   * - 0xC
     - __le32
     - dotdot.inode
     - 父目录的inode编号
* - 0x10
     - __le16
     - dotdot.rec_len
     - block_size - 12。记录长度足够长以覆盖所有htree数据
* - 0x12
     - u8
     - dotdot.name_len
     - 名称的长度，2
* - 0x13
     - u8
     - dotdot.file_type
     - 此条目的文件类型，0x2（目录）（如果启用了特性标志）
* - 0x14
     - char
     - dotdot_name[4]
     - “..\0\0”
* - 0x18
     - __le32
     - struct dx_root_info.reserved_zero
     - 零
* - 0x1C
     - u8
     - struct dx_root_info.hash_version
     - 哈希类型，参见下方的 dirhash_ 表
* - 0x1D
     - u8
     - struct dx_root_info.info_length
     - 树信息的长度，0x8
* - 0x1E
     - u8
     - struct dx_root_info.indirect_levels
     - htree 的深度。如果启用了 INCOMPAT_LARGEDIR 特性，则不能大于 3；否则不能大于 2
* - 0x1F
     - u8
     - struct dx_root_info.unused_flags
     -
* - 0x20
     - __le16
     - limit
     - 能够跟随此头的最大 dx_entries 数量，加上 1 作为头本身
* - 0x22
     - __le16
     - count
     - 实际跟随此头的 dx_entries 数量，加上 1 作为头本身
* - 0x24
     - __le32
     - block
     - 与哈希值为 0 对应的块号（在目录文件内）
* - 0x28
     - struct dx_entry
     - entries[0]
     - 在剩余的数据块中尽可能多的 8 字节 `struct dx_entry`

.. _dirhash:

目录哈希是以下值之一：

.. list-table::
   :widths: 16 64
   :header-rows: 1

   * - 值
     - 描述
   * - 0x0
     - 传统
* - 0x1
     - 半个 MD4
* - 0x2
     - Tea
* - 0x3
     - 传统，未签名
* - 0x4
     - 半个 MD4，未签名
* - 0x5
     - Tea，未签名
* - 0x6
     - Siphash

htree 的内部节点记录为 `struct dx_node`，这也是一个数据块的完整长度：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 类型
     - 名称
     - 描述
   * - 0x0
     - __le32
     - fake.inode
     - 零值，使这个条目看起来未被使用
* - 0x4
     - __le16
     - fake.rec_len
     - 块的大小，以隐藏所有的 dx_node 数据
* - 0x6
     - u8
     - name_len
     - 零。这个“未使用”的目录条目没有名称
* - 0x7
     - u8
     - file_type
     - 零。这个“未使用”的目录条目没有文件类型
* - 0x8
     - __le16
     - limit
     - 可以跟随此头的 dx_entries 的最大数量，加上 1 作为头本身
* - 0xA
     - __le16
     - count
     - 实际跟随此头的 dx_entries 数量，加上 1 作为头本身
* - 0xE
     - __le32
     - block
     - 与本块最低哈希值对应的块号（在目录文件内的编号）。这个值存储在父块中
* - 0x12
     - struct dx_entry
     - entries[0]
     - 在数据块剩余部分能容纳的尽可能多的 8 字节 `struct dx_entry`
存在于 `struct dx_root` 和 `struct dx_node` 中的哈希映射被记录为 `struct dx_entry`，长度为 8 字节：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 类型
     - 名称
     - 描述
   * - 0x0
     - __le32
     - hash
     - 哈希码
* - 0x4
     - __le32
     - block
     - 下一个节点在 htree 中的块号（在目录文件内，不是文件系统块）

如果你觉得这一切非常巧妙且奇特，作者也是这么认为的。

如果启用了元数据校验和，则目录块的最后 8 字节（恰好是一个 dx_entry 的长度）用于存储一个 `struct dx_tail`，其中包含校验和。`dx_root` 或 `dx_node` 结构中的 `limit` 和 `count` 条目会根据需要进行调整，以便将 dx_tail 放入块中。如果没有空间放置 dx_tail，用户将被通知运行 e2fsck -D 重建目录索引（这将确保有足够的空间用于校验和）。`dx_tail` 结构的长度为 8 字节，如下所示：

.. list-table::
   :widths: 8 8 24 40
   :header-rows: 1

   * - 偏移量
     - 类型
     - 名称
     - 描述
   * - 0x0
     - u32
     - dt_reserved
     - 零
* - 0x4
     - __le32
     - dt_checksum
     - htree 目录块的校验和

校验和是基于 FS UUID、htree 索引头（dx_root 或 dx_node）、所有正在使用的 htree 索引（dx_entry）以及尾部块（dx_tail）计算得出的。
当然，请提供您需要翻译的文本。
