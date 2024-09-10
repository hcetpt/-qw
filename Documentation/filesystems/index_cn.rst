文件系统索引

===============================
Linux 内核中的文件系统
===============================

这本仍在开发中的手册，终有一天会提供关于 Linux 虚拟文件系统（VFS）层及其下方的文件系统的综合信息。目前我们有的内容如下：

核心 VFS 文档
======================

请参阅以下手册以了解有关 VFS 层本身及其算法的文档：
.. toctree::
   :maxdepth: 2

   vfs
   path-lookup
   api-summary
   splice
   locking
   directory-locking
   devpts
   dnotify
   fiemap
   files
   locks
   mount_api
   quota
   seq_file
   sharedsubtree
   idmappings
   iomap/index

   automount-support

   caching/index

   porting

文件系统支持层
=========================

以下是文件系统层中用于实现文件系统的支持代码的文档：
.. toctree::
   :maxdepth: 2

   buffer
   journalling
   fscrypt
   fsverity
   netfs_library

文件系统
===========

以下是具体文件系统实现的文档：
.. toctree::
   :maxdepth: 2

   9p
   adfs
   affs
   afs
   autofs
   autofs-mount-control
   bcachefs/index
   befs
   bfs
   btrfs
   ceph
   coda
   configfs
   cramfs
   dax
   debugfs
   dlmfs
   ecryptfs
   efivarfs
   erofs
   ext2
   ext3
   ext4/index
   f2fs
   gfs2
   gfs2-uevents
   gfs2-glocks
   hfs
   hfsplus
   hpfs
   fuse
   fuse-io
   inotify
   isofs
   nilfs2
   nfs/index
   ntfs3
   ocfs2
   ocfs2-online-filecheck
   omfs
   orangefs
   overlayfs
   proc
   qnx6
   ramfs-rootfs-initramfs
   relay
   romfs
   smb/index
   spufs/index
   squashfs
   sysfs
   sysv-fs
   tmpfs
   ubifs
   ubifs-authentication
   udf
   virtiofs
   vfat
   xfs/index
   zonefs
