SPDX 许可证标识符: GPL-2.0

================================
优化的 MPEG 文件系统 (OMFS)
================================

概述
========

OMFS 是由 SonicBlue 为 ReplayTV DVR 和 Rio Karma MP3 播放器创建的文件系统。该文件系统基于扩展，使用 2k 到 8k 的块大小，并具有基于哈希的目录。此文件系统驱动程序可用于读取和写入这些设备的磁盘。
请注意，不建议将此文件系统用于您自己的流媒体设备的一般文件系统。原生 Linux 文件系统的性能可能会更好。
更多信息请访问：

    http://linux-karma.sf.net/

包括 mkomfs 和 omfsck 在内的各种工具都包含在 omfsprogs 中，可在以下网址获取：

    https://bobcopeland.com/karma/

其 README 文件中包含了说明。

选项
=======

OMFS 支持以下挂载时选项：

    ============   ========================================
    uid=n          将所有文件的所有者设为指定用户
    gid=n          将所有文件的组所有者设为指定组
    umask=xxx      将权限掩码设为 xxx
    fmask=xxx      将文件的掩码设为 xxx
    dmask=xxx      将目录的掩码设为 xxx
    ============   ========================================

磁盘格式
===========

OMFS 区分了“sysblocks”和普通数据块。sysblock 组包含超级块信息、文件元数据、目录结构以及扩展。每个 sysblock 都有一个包含整个 sysblock 的 CRC 的头部，并且可以在磁盘上的后续块中镜像。一个 sysblock 可能比一个数据块更小，但由于它们都通过相同的 64 位块号进行寻址，因此较小的 sysblock 中剩余的空间是未使用的。
sysblock 头部信息如下：

    struct omfs_header {
	    __be64 h_self;                  /* 该位置所在的文件系统块 */
	    __be32 h_body_size;             /* 头部后有用数据的大小 */
	    __be16 h_crc;                   /* h_body_size 字节的 crc-ccitt */
	    char h_fill1[2];
	    u8 h_version;                   /* 版本，始终为 1 */
	    char h_type;                    /* OMFS_INODE_X */
	    u8 h_magic;                     /* OMFS_IMAGIC */
	    u8 h_check_xor;                 /* 该字节之前的头部字节的异或 */
	    __be32 h_fill2;
    };

文件和目录都用 omfs_inode 表示：

    struct omfs_inode {
	    struct omfs_header i_head;      /* 头部 */
	    __be64 i_parent;                /* 包含此索引节点的父节点 */
	    __be64 i_sibling;               /* 哈希桶中的下一个索引节点 */
	    __be64 i_ctime;                 /* 创建时间，以毫秒为单位 */
	    char i_fill1[35];
	    char i_type;                    /* OMFS_[DIR,FILE] */
	    __be32 i_fill2;
	    char i_fill3[64];
	    char i_name[OMFS_NAMELEN];      /* 文件名 */
	    __be64 i_size;                  /* 文件大小，以字节为单位 */
    };

OMFS 中的目录实现为一个大的哈希表。文件名经过哈希处理后被添加到从 OMFS_DIR_START 开始的桶列表中。查找需要对文件名进行哈希处理，然后通过 i_sibling 指针遍历，直到找到匹配的 i_name。空桶由全 1 的块指针（~0）表示。
文件是一个 omfs_inode 结构后面跟着一个从 OMFS_EXTENT_START 开始的扩展表：

    struct omfs_extent_entry {
	    __be64 e_cluster;               /* 一组块的起始位置 */
	    __be64 e_blocks;                /* e_cluster 后的块数 */
    };

    struct omfs_extent {
	    __be64 e_next;                  /* 下一个扩展表位置 */
	    __be32 e_extent_count;          /* 此表中的总扩展数 */
	    __be32 e_fill;
	    struct omfs_extent_entry e_entry;       /* 扩展条目的开始 */
    };

每个扩展包含块偏移量和分配给扩展的块数。每个表中的最后一个扩展是一个终止扩展，其中 e_cluster 为 ~0，e_blocks 为表中块数的按位取反。
如果此表溢出，则会写入一个延续索引节点，并由 e_next 指向。这些节点有头部但缺少其余的索引节点结构。
