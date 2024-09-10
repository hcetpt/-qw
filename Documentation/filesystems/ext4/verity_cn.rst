Verity 文件
-----------

ext4 支持 fs-verity，这是一种文件系统特性，为单个只读文件提供基于 Merkle 树的哈希。大多数 fs-verity 的功能对于所有支持它的文件系统都是通用的；详见 :ref:`Documentation/filesystems/fsverity.rst <fsverity>` 中的 fs-verity 文档。然而，verity 元数据在磁盘上的布局是特定于文件系统的。在 ext4 中，verity 元数据存储在文件数据本身的末尾之后，格式如下：

- 填充到下一个 65536 字节边界。此填充实际上不必分配在磁盘上，即可以是一个空洞。
- 如 :ref:`Documentation/filesystems/fsverity.rst <fsverity_merkle_tree>` 所述的 Merkle 树，树层按从根到叶的顺序存储，并且每个层级内的树块按自然顺序存储。
- 填充到下一个文件系统块边界。
- 如 :ref:`Documentation/filesystems/fsverity.rst <fsverity_descriptor>` 所述的 verity 描述符，可选附加签名块。
- 填充到下一个距离文件系统块边界 4 字节的位置。
- verity 描述符的大小（以字节为单位），作为一个 4 字节的小端整数。

设置 EXT4_VERITY_FL 的 Verity 索引节点必须使用扩展（extent），即必须设置 EXT4_EXTENTS_FL 并且不能设置 EXT4_INLINE_DATA_FL。它们可以设置 EXT4_ENCRYPT_FL，在这种情况下，数据本身和 verity 元数据都会被加密。Verity 文件不能在 verity 元数据之后分配块。
Verity和DAX不兼容，尝试在同一个文件上同时设置这两个标志将会失败。
