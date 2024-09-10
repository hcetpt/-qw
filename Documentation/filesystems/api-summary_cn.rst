=============================
Linux 文件系统 API 概览
=============================

本节包含 API 级别的文档，主要来自源代码本身。
Linux 虚拟文件系统 (VFS)
=================

文件系统类型
--------------

.. kernel-doc:: include/linux/fs.h
   :internal:

目录缓存
--------------

.. kernel-doc:: fs/dcache.c
   :export:

.. kernel-doc:: include/linux/dcache.h
   :internal:

索引节点处理
--------------

.. kernel-doc:: fs/inode.c
   :export:

.. kernel-doc:: fs/bad_inode.c
   :export:

注册和超级块
-----------------

.. kernel-doc:: fs/super.c
   :export:

文件锁
------------

.. kernel-doc:: fs/locks.c
   :export:

.. kernel-doc:: fs/locks.c
   :internal:

其他功能
------------

.. kernel-doc:: fs/mpage.c
   :export:

.. kernel-doc:: fs/namei.c
   :export:

.. kernel-doc:: block/bio.c
   :export:

.. kernel-doc:: fs/seq_file.c
   :export:

.. kernel-doc:: fs/filesystems.c
   :export:

.. kernel-doc:: fs/fs-writeback.c
   :export:

.. kernel-doc:: fs/anon_inodes.c
   :export:

.. kernel-doc:: fs/attr.c
   :export:

.. kernel-doc:: fs/d_path.c
   :export:

.. kernel-doc:: fs/dax.c
   :export:

.. kernel-doc:: fs/libfs.c
   :export:

.. kernel-doc:: fs/posix_acl.c
   :export:

.. kernel-doc:: fs/stat.c
   :export:

.. kernel-doc:: fs/sync.c
   :export:

.. kernel-doc:: fs/xattr.c
   :export:

.. kernel-doc:: fs/namespace.c
   :export:

proc 文件系统
==================

sysctl 接口
--------------

.. kernel-doc:: kernel/sysctl.c
   :export:

proc 文件系统接口
------------------

.. kernel-doc:: fs/proc/base.c
   :internal:

基于文件描述符的事件
======================

.. kernel-doc:: fs/eventfd.c
   :export:

eventpoll (epoll) 接口
=======================

.. kernel-doc:: fs/eventpoll.c
   :internal:

导出内核对象的文件系统
========================

.. kernel-doc:: fs/sysfs/file.c
   :export:

.. kernel-doc:: fs/sysfs/symlink.c
   :export:

debugfs 文件系统
==================

debugfs 接口
--------------

.. kernel-doc:: fs/debugfs/inode.c
   :export:

.. kernel-doc:: fs/debugfs/file.c
   :export:
