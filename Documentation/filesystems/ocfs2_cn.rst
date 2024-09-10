SPDX 许可证标识符: GPL-2.0

================
OCFS2 文件系统
================

OCFS2 是一种通用的基于扩展的共享磁盘集群文件系统，与 ext3 有许多相似之处。它支持 64 位 inode 编号，并具有自动扩展的元数据组，这可能也使其适用于非集群环境。
您需要安装 ocfs2-tools 软件包以获取 "mount.ocfs2" 和 "ocfs2_hb_ctl"。

项目网页:    http://ocfs2.wiki.kernel.org
工具 Git 仓库:      https://github.com/markfasheh/ocfs2-tools
OCFS2 邮件列表: https://subspace.kernel.org/lists.linux.dev.html

所有代码版权归 2005 年 Oracle 所有，除非另有说明
致谢
=======

大量代码取自 ext3 和其他项目
作者按字母顺序排列：

- Joel Becker   <joel.becker@oracle.com>
- Zach Brown    <zach.brown@oracle.com>
- Mark Fasheh   <mfasheh@suse.com>
- Kurt Hackel   <kurt.hackel@oracle.com>
- Tao Ma        <tao.ma@oracle.com>
- Sunil Mushran <sunil.mushran@oracle.com>
- Manish Singh  <manish.singh@oracle.com>
- Tiger Yang    <tiger.yang@oracle.com>

注意事项
=======

OCFS2 尚不支持的功能：

- 目录更改通知（F_NOTIFY）
- 分布式缓存（F_SETLEASE/F_GETLEASE/break_lease）

挂载选项
=============

OCFS2 支持以下挂载选项：

(*) == 默认

======================= ========================================================
barrier=1		启用或禁用屏障。barrier=0 禁用，barrier=1 启用
errors=remount-ro(*)	在出现错误时将文件系统重新挂载为只读
errors=panic		如果发生错误，则使机器崩溃并停止运行
intr		(*)	允许信号中断集群操作
nointr			不允许信号中断集群操作
noatime			不更新访问时间
relatime(*)		如果之前的访问时间（atime）早于修改时间（mtime）或更改时间（ctime），则更新atime
strictatime		始终更新atime，但最小更新间隔由atime_quantum指定
atime_quantum=60(*)	除非自上次更新以来经过了指定秒数，否则OCFS2不会更新atime
			设置为零以始终更新atime。此选项需要与strictatime一起使用
data=ordered	(*)	所有数据在元数据提交到日志之前被强制直接写入主文件系统
data=writeback		不保留数据顺序，数据可能在其元数据已提交到日志之后写入主文件系统
preferred_slot=0(*)	在挂载期间，尝试首先使用此文件系统槽位。如果该槽位已被其他节点占用，则选择找到的第一个空槽位。无效值将被忽略
commit=nrsec	(*)	可以告诉OCFS2每隔'nrsec'秒同步其所有数据和元数据。默认值是5秒
这意味着如果你断电，你可能会丢失最多最近5秒的工作（但是由于日志记录，你的文件系统不会损坏）。这个默认值（或任何较小的值）会影响性能，但对于数据安全有好处
将其设置为0的效果与保持默认值（5秒）相同
将其设置为非常大的值会提高性能
localalloc=8(*)    允许自定义本地分配大小（以MB为单位）。如果值过大，文件系统会默默地将其恢复为默认值。
localflocks    禁用集群感知的flock
inode64    表示允许Ocfs2在文件系统的任何位置创建inode，包括那些会导致inode编号占用超过32位重要性的位置
user_xattr(*)    启用扩展用户属性
nouser_xattr    禁用扩展用户属性
acl    启用POSIX访问控制列表支持
noacl    (*)    禁用POSIX访问控制列表支持
resv_level=2(*)    设置分配预留的激进程度。有效值范围是0（关闭预留）到8（预留最大空间）
dir_resv_level=    (*)    默认情况下，目录预留会随文件预留一起缩放——用户很少需要更改此值。如果分配预留被关闭，此选项将无效。
```
coherency=full  (*)	不允许并发的 O_DIRECT 写操作，集群inode锁将被获取以强制其他节点丢弃缓存，因此即使对于 O_DIRECT 写操作也能保证完整的集群一致性
coherency=buffered	允许节点间并发的 O_DIRECT 写操作而不使用 EX 锁，这在冒着其他节点数据陈旧的风险下获得了高性能
journal_async_commit	提交块可以不等待描述符块就写入磁盘。如果启用，较老的内核将无法挂载该设备。这将内部启用 'journal_checksum'
```
