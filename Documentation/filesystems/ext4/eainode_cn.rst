SPDX 许可证标识符: GPL-2.0

大型扩展属性值
------------------

为了使 ext4 能够存储无法放入inode或附加到inode的单个扩展属性块中的扩展属性值，EA_INODE 特性允许我们将值存储在普通文件inode的数据块中。这个“EA inode”仅从扩展属性名称索引链接，并且不应出现在目录项中。inode 的 i_atime 字段用于存储 xattr 值的校验和；而 i_ctime/i_version 存储一个 64 位引用计数，这使得多个拥有inode之间可以共享大型 xattr 值。为了与该特性的旧版本保持向后兼容，i_mtime/i_generation *可能* 存储指向 **一个** 拥有inode的inode号和 i_generation 的反向引用（在 EA inode 未被多个inode引用的情况下），以验证访问的 EA inode 是正确的。
