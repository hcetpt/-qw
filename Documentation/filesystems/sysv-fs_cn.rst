SPDX 许可证标识符: GPL-2.0

==================
SystemV 文件系统
==================

它实现了以下功能:
  - Xenix 文件系统,
  - SystemV/386 文件系统,
  - Coherent 文件系统

安装步骤:

* 在配置内核时回答“是否支持 System V 和 Coherent 文件系统”的问题时选择'y'
* 要挂载磁盘或分区，请使用以下命令:

    mount [-r] -t sysv 设备 挂载点

  文件系统的类型名:
  
               -t sysv
               -t xenix
               -t coherent

  这些可以互换使用，但后两种最终将被移除。

当前实现中的问题:

- Coherent 文件系统:

  - 目前忽略“空闲列表交错”n:m
- 只识别没有文件系统名称和包名称的文件系统
(请参阅 Coherent 的“man mkfs”以了解这些特性的描述。)

- SystemV Release 2 文件系统:

  超级块仅在第 9、15 和 18 块中搜索，
  这对应于软盘第一磁道的开始。目前不支持硬盘上的此文件系统。
这些文件系统非常相似。以下是与 Minix 文件系统的比较:

* Linux fdisk 报告的分区类型

  - Minix 文件系统     0x81 Linux/Minix
  - Xenix 文件系统     ??
  - SystemV 文件系统   ??
  - Coherent 文件系统  0x08 AIX 可引导

* 块或区域（磁盘上的数据分配单元）的大小

  - Minix 文件系统     1024
  - Xenix 文件系统     1024（也可能是 512）
  - SystemV 文件系统   1024（也可能是 512 和 2048）
  - Coherent 文件系统   512

* 总体布局：所有文件系统都有一个引导块、一个超级块以及用于索引节点和目录/数据的独立区域
在 SystemV Release 2 文件系统（如 Microport）中，第一个磁道是保留的，并且所有块号（包括超级块）都偏移了一个磁道。
* 磁盘上“短”（16位实体）字节序：

  - Minix 文件系统     小端序 0 1
  - Xenix 文件系统     小端序 0 1
  - SystemV 文件系统   小端序 0 1
  - Coherent 文件系统  小端序 0 1

  当然，这仅影响文件系统本身，而不影响其上的文件数据！

* 磁盘上“长”（32位实体）字节序：

  - Minix 文件系统     小端序 0 1 2 3
  - Xenix 文件系统     小端序 0 1 2 3
  - SystemV 文件系统   小端序 0 1 2 3
  - Coherent 文件系统  PDP-11 2 3 0 1

  当然，这也仅影响文件系统本身，而不影响其上的文件数据！

* 磁盘上的索引节点：“短”，0 表示不存在，根目录的索引节点编号为：

  =================================  ==
  Minix 文件系统                            1
  Xenix 文件系统、SystemV 文件系统、Coherent 文件系统   2
  =================================  ==

* 文件硬链接的最大数量：

  ===========  =========
  Minix 文件系统     250
  Xenix 文件系统     ??
  SystemV 文件系统   ??
  Coherent 文件系统  >=10000
  ===========  =========

* 空闲索引节点管理：

  - Minix 文件系统
      位图
  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统
      超级块中缓存了一定数量的空闲索引节点
当缓存耗尽时，使用线性搜索找到新的空闲索引节点。
* 空闲块管理：

  - Minix 文件系统
      使用位图
  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统
      空闲块以“空闲列表”的形式组织。这可能是一个误导性术语，
      因为并不是每个空闲块都包含指向下一个空闲块的指针。实际上，空闲块是以有限大小的块（chunk）形式组织的，并且每隔一段时间一个空闲块会包含指向下一个块中空闲块的指针；第一个这样的块包含指针，依此类推。在Xenix 文件系统和SystemV 文件系统中，该列表以“块号”0终止，在Coherent 文件系统中则以全零块终止。

* 超级块位置：

  ===========  ==========================
  Minix 文件系统     块 1 = 字节 1024..2047
  Xenix 文件系统     块 1 = 字节 1024..2047
  SystemV 文件系统   字节 512..1023
  Coherent 文件系统  块 1 = 字节 512..1023
  ===========  ==========================

* 超级块布局：

  - Minix 文件系统::

                    unsigned short s_ninodes;
                    unsigned short s_nzones;
                    unsigned short s_imap_blocks;
                    unsigned short s_zmap_blocks;
                    unsigned short s_firstdatazone;
                    unsigned short s_log_zone_size;
                    unsigned long s_max_size;
                    unsigned short s_magic;

  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统::

                    unsigned short s_firstdatazone;
                    unsigned long  s_nzones;
                    unsigned short s_fzone_count;
                    unsigned long  s_fzones[NICFREE];
                    unsigned short s_finode_count;
                    unsigned short s_finodes[NICINOD];
                    char           s_flock;
                    char           s_ilock;
                    char           s_modified;
                    char           s_rdonly;
                    unsigned long  s_time;
                    short          s_dinfo[4]; -- 仅限于SystemV 文件系统
                    unsigned long  s_free_zones;
                    unsigned short s_free_inodes;
                    short          s_dinfo[4]; -- 仅限于Xenix 文件系统
                    unsigned short s_interleave_m, s_interleave_n; -- 仅限于Coherent 文件系统
                    char           s_fname[6];
                    char           s_fpack[6];

    接下来它们有很大的不同：

        Xenix 文件系统::

                    char           s_clean;
                    char           s_fill[371];
                    long           s_magic;
                    long           s_type;

        SystemV 文件系统::

                    long           s_fill[12 或 14];
                    long           s_state;
                    long           s_magic;
                    long           s_type;

        Coherent 文件系统::

                    unsigned long  s_unique;

    注意，Coherent 文件系统没有魔法值

* 索引节点布局：

  - Minix 文件系统::

                    unsigned short i_mode;
                    unsigned short i_uid;
                    unsigned long  i_size;
                    unsigned long  i_time;
                    unsigned char  i_gid;
                    unsigned char  i_nlinks;
                    unsigned short i_zone[7+1+1];

  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统::

                    unsigned short i_mode;
                    unsigned short i_nlink;
                    unsigned short i_uid;
                    unsigned short i_gid;
                    unsigned long  i_size;
                    unsigned char  i_zone[3*(10+1+1+1)];
                    unsigned long  i_atime;
                    unsigned long  i_mtime;
                    unsigned long  i_ctime;

* 普通文件的数据块组织方式如下：

  - Minix 文件系统：
  
             - 7 个直接块
             - 1 个间接块（指向块的指针）
             - 1 个双间接块（指向指向块的指针）

  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统：
  
             - 10 个直接块
             - 1 个间接块（指向块的指针）
             - 1 个双间接块（指向指向块的指针）
             - 1 个三间接块（指向指向指向块的指针）

  ===========  ==========   ================
               索引节点大小   每个块中的索引节点数
  ===========  ==========   ================
  Minix 文件系统        32        32
  Xenix 文件系统        64        16
  SystemV 文件系统      64        16
  Coherent 文件系统     64        8
  ===========  ==========   ================

* 磁盘上的目录项：

  - Minix 文件系统::

                    unsigned short inode;
                    char name[14/30];

  - Xenix 文件系统、SystemV 文件系统、Coherent 文件系统::

                    unsigned short inode;
                    char name[14];

  ===========    ==============    =====================
                 目录项大小    每个块中的目录项数
  ===========    ==============    =====================
  Minix 文件系统       16/32             64/32
  Xenix 文件系统       16                64
  SystemV 文件系统     16                64
  Coherent 文件系统    16                32
  ===========    ==============    =====================

* 如何实现符号链接，以便主机fsck不会报错：

  - Minix 文件系统     正常
  - Xenix 文件系统     技巧：作为具有 chmod 1000 权限的普通文件
  - SystemV 文件系统   未知
  - Coherent 文件系统  技巧：作为具有 chmod 1000 权限的普通文件

注释：我们经常提到“块”，但指的是分配单元（区域），而不是磁盘驱动程序意义上的“块”。
