SPDX 许可证标识符: GPL-2.0

============
Fiemap Ioctl
============

Fiemap ioctl 是用户空间获取文件扩展映射的一种高效方法。与逐块映射（如 bmap）不同，fiemap 返回一系列的扩展。
请求基础
--------------

一个 fiemap 请求被编码在结构体 fiemap 中:: 

  结构体 fiemap{
	__u64 fm_start; /* 开始映射的逻辑偏移量（包含），以字节为单位 */
	__u64 fm_length; /* 用户关心的映射逻辑长度，以字节为单位 */
	__u32 fm_flags; /* 请求的 FIEMAP_FLAG_* 标志（输入/输出） */
	__u32 fm_mapped_extents; /* 映射的扩展数量（输出） */
	__u32 fm_extent_count; /* fm_extents 数组的大小（输入） */
	__u32 fm_reserved;
	结构体 fiemap_extent fm_extents[0]; /* 映射扩展的数组（输出） */
  };

`fm_start` 和 `fm_length` 指定了进程想要映射的文件内的逻辑范围。返回的扩展反映了磁盘上的情况——也就是说，第一个返回的扩展的逻辑偏移量可能在 `fm_start` 之前开始，并且最后一个返回的扩展所覆盖的范围可能在 `fm_length` 之后结束。所有的偏移量和长度都是以字节为单位。
可以在 `fm_flags` 中设置一些标志来修改查找映射的方式。如果内核不理解某些特定的标志，它将返回 EBADR，并且 `fm_flags` 的内容将包含导致错误的标志集合。如果内核兼容所有传递的标志，则 `fm_flags` 的内容将保持不变。
由用户空间决定某个标志的拒绝是否对其操作致命。该方案旨在允许 fiemap 接口在未来扩展而不失去与旧软件的兼容性。
`fm_extent_count` 指定了可以用于返回扩展的 `fm_extents[]` 数组中的元素数量。如果 `fm_extent_count` 为零，则忽略 `fm_extents[]` 数组（不会返回任何扩展），并且 `fm_mapped_extents` 计数将包含保存当前文件映射所需的 `fm_extents[]` 中的扩展数量。请注意，在两次调用 FIEMAP 之间文件可能会发生变化。
以下标志可以在 `fm_flags` 中设置：

FIEMAP_FLAG_SYNC
  如果设置了此标志，内核将在映射扩展之前同步文件。
FIEMAP_FLAG_XATTR
  如果设置了此标志，返回的扩展将描述 inode 扩展属性查找树，而不是其数据树。
扩展映射
--------------

扩展信息通过嵌入的 `fm_extents` 数组返回，用户空间必须与 fiemap 结构体一起分配。`fiemap_extents[]` 数组中的元素数量应通过 `fm_extent_count` 传递。内核映射的扩展数量将通过 `fm_mapped_extents` 返回。如果分配的 `fiemap_extents` 数量少于映射请求范围所需的数量，那么在 `fm_extents[]` 数组中可以映射的最大扩展数量将被返回，并且 `fm_mapped_extents` 将等于 `fm_extent_count`。在这种情况下，数组中的最后一个扩展将不会完成请求的范围，并且不会设置 FIEMAP_EXTENT_LAST 标志（参见下一部分关于扩展标志的内容）。
每个扩展由一个单个的 `fiemap_extent` 结构体描述，该结构体作为 `fm_extents` 的返回结果:: 

    结构体 fiemap_extent{
	    __u64 fe_logical;  /* 扩展开始的逻辑偏移量，以字节为单位 */
	    __u64 fe_physical; /* 扩展开始的物理偏移量，以字节为单位 */
	    __u64 fe_length;   /* 扩展的长度，以字节为单位 */
	    __u64 fe_reserved64[2];
	    __u32 fe_flags;    /* 此扩展的 FIEMAP_EXTENT_* 标志 */
	    __u32 fe_reserved[3];
    };

所有的偏移量和长度都是以字节为单位，并反映磁盘上的情况。扩展的逻辑偏移量在请求之前开始或其逻辑长度超出请求是有效的。除非返回 FIEMAP_EXTENT_NOT_ALIGNED，否则 `fe_logical`、`fe_physical` 和 `fe_length` 将对齐到文件系统的块大小。除了标记为 FIEMAP_EXTENT_MERGED 的扩展外，相邻的扩展不会合并。
`fe_flags` 字段包含描述返回扩展的标志。
一个特殊的标志 `FIEMAP_EXTENT_LAST` 总是设置在文件中的最后一个范围上，以便调用 `fiemap` 的进程可以确定没有更多的范围，而无需再次调用 ioctl。一些标志是有意模糊的，并且在存在更具体的标志时始终被设置。这样，寻找一般属性的程序不必了解所有现有的和未来的标志，这些标志可能暗示该属性。

例如，如果设置了 `FIEMAP_EXTENT_DATA_INLINE` 或 `FIEMAP_EXTENT_DATA_TAIL`，那么也会设置 `FIEMAP_EXTENT_NOT_ALIGNED`。寻找内联或尾部打包数据的程序可以关注特定的标志。然而，对于仅关心不尝试操作未对齐范围的软件，只需关注 `FIEMAP_EXTENT_NOT_ALIGNED`，而不必担心所有现有的和未来的可能暗示未对齐数据的标志。需要注意的是，相反的情况并不成立——`FIEMAP_EXTENT_NOT_ALIGNED` 可以单独出现。

- `FIEMAP_EXTENT_LAST`
  这通常是文件中的最后一个范围。超过此范围的映射尝试可能会返回空值。某些实现会设置此标志以指示这是用户查询范围内（通过 `fiemap->fm_length`）的最后一个范围。
  
- `FIEMAP_EXTENT_UNKNOWN`
  当前未知此范围的位置。这可能表明数据存储在一个无法访问的卷上，或者尚未为文件分配存储空间。
  
- `FIEMAP_EXTENT_DELALLOC`
  这也会设置 `FIEMAP_EXTENT_UNKNOWN`
  延迟分配——虽然此范围内有数据，但其物理位置尚未分配。
  
- `FIEMAP_EXTENT_ENCODED`
  此范围不包含普通的文件系统块，而是经过编码（例如加密或压缩）的。通过块设备进行 I/O 操作读取此范围内的数据将导致不确定的结果。
  注意，在没有文件系统协助的情况下尝试直接更新数据（通过写入指定位置）或在文件系统挂载时使用 FIEMAP 接口返回的信息访问数据总是不确定的。换句话说，用户应用程序只能在文件系统卸载时通过块设备的 I/O 操作读取范围数据，并且只有在 `FIEMAP_EXTENT_ENCODED` 标志未设置时才能这样做；用户应用程序不得在任何其他情况下尝试通过块设备读写文件系统。
  
- `FIEMAP_EXTENT_DATA_ENCRYPTED`
  这也会设置 `FIEMAP_EXTENT_ENCODED`
  此范围内数据已被文件系统加密。
### FIEMAP_EXTENT_NOT_ALIGNED
区间偏移量和长度不保证与块对齐。

### FIEMAP_EXTENT_DATA_INLINE
这也会设置 FIEMAP_EXTENT_NOT_ALIGNED。
数据位于元数据块内。

### FIEMAP_EXTENT_DATA_TAIL
这也会设置 FIEMAP_EXTENT_NOT_ALIGNED。
数据与其他文件的数据打包在同一个块中。

### FIEMAP_EXTENT_UNWRITTEN
未写入的区间 — 区间已分配，但其数据尚未初始化。这意味着如果通过文件系统读取该区间，其数据将全部为零；但如果直接从设备读取，则内容是不确定的。

### FIEMAP_EXTENT_MERGED
当文件系统不支持区间时会设置此标志，即使用基于块的寻址方案。由于将每个块都返回给用户空间效率极低，内核会尝试将大多数相邻块合并为“区间”。

### VFS -> 文件系统实现

希望支持 fiemap 的文件系统必须在其 inode_operations 结构体中实现一个 ->fiemap 回调。fs ->fiemap 调用负责定义其支持的 fiemap 标志，并在发现每个区间时调用一个辅助函数：

```c
struct inode_operations {
    ...
    int (*fiemap)(struct inode *, struct fiemap_extent_info *, u64 start, u64 len);
};
```

->fiemap 接收一个描述 fiemap 请求的 struct fiemap_extent_info：

```c
struct fiemap_extent_info {
    unsigned int fi_flags;         // 从用户传递的标志
    unsigned int fi_extents_mapped; // 已映射的区间数量
    unsigned int fi_extents_max;   // fiemap_extent 数组的大小
    struct fiemap_extent *fi_extents_start; // fiemap_extent 数组的起始地址
};
```

文件系统不应直接访问此结构中的任何内容。文件系统处理器应能容忍信号，并在接收到致命信号后返回 EINTR。
应在 ->fiemap 回调开始时通过 fiemap_prep() 辅助函数进行标志检查：

```c
int fiemap_prep(struct inode *inode, struct fiemap_extent_info *fieinfo,
                u64 start, u64 *len, u32 supported_flags);
```

应将 ioctl_fiemap() 接收到的 fieinfo 结构传递给 fiemap_prep()。文件系统应通过 fs_flags 传递其理解的 fiemap 标志。如果 fiemap_prep 发现无效的用户标志，它会将错误值放入 fieinfo->fi_flags 并返回 -EBADR。如果文件系统从 fiemap_prep() 获取到 -EBADR，应立即退出并返回该错误到 ioctl_fiemap()。此外，还需验证请求范围是否在支持的最大文件大小范围内。

对于请求范围内的每个区间，文件系统应调用辅助函数 fiemap_fill_next_extent()：

```c
int fiemap_fill_next_extent(struct fiemap_extent_info *info, u64 logical,
                            u64 phys, u64 len, u32 flags, u32 dev);
```

fiemap_fill_next_extent() 将使用传递的值填充 fm_extents 数组中的下一个空闲区间。通用区间标志将自动从特定标志设置，以确保用户空间 API 不被破坏。
fiemap_fill_next_extent() 成功时返回 0，当用户提供的 fm_extents 数组已满时返回 1。如果在复制区间到用户内存时遇到错误，将返回 -EFAULT。
当然，请提供你需要翻译的文本。
