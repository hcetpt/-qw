SPDX 许可声明标识符: GPL-2.0

特殊inode
---------

ext4为某些特殊功能预留了一些inode，如下所示：

.. list-table::
   :widths: 6 70
   :header-rows: 1

   * - inode编号
     - 用途
   * - 0
     - 不存在；没有inode 0
   * - 1
     - 缺陷块列表
   * - 2
     - 根目录
   * - 3
     - 用户配额
   * - 4
     - 组配额
   * - 5
     - 引导加载程序
   * - 6
     - 恢复删除目录
   * - 7
     - 预留组描述符inode。（“调整大小inode”）
   * - 8
     - 日志inode
   * - 9
     - “排除”inode，用于快照（？）
   * - 10
     - 副本inode，用于某些非上游特性？
   * - 11
     - 传统的第一个非预留inode。通常这是lost+found目录。参见superblock中的s_first_ino

请注意，还有一些inode从非预留inode编号分配给其他文件系统特性，这些特性不从标准目录层次结构中引用。这些inode通常在superblock中引用。它们是：

.. list-table::
   :widths: 20 50
   :header-rows: 1

   * - superblock字段
     - 描述
   * - s_lpf_ino
     - lost+found目录的inode编号
* - s_prj_quota_inum
     - 用于跟踪项目配额的quota文件的inode编号
   * - s_orphan_file_inum
     - 用于跟踪孤立inode的文件的inode编号
