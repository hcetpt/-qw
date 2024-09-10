SPDX 许可证标识符: GPL-2.0

================
uevents 和 GFS2
================

在 GFS2 文件系统挂载期间，会生成多个 uevent。本文档解释了这些事件的含义及其用途（由 gfs2-utils 中的 gfs_controld 使用）。

GFS2 uevents 列表
======================

1. ADD
------

ADD 事件在挂载时发生。它始终是新创建的文件系统生成的第一个 uevent。如果挂载成功，将跟随一个 ONLINE uevent；如果不成功，则跟随一个 REMOVE uevent。
ADD uevent 包含两个环境变量：SPECTATOR=[0|1] 和 RDONLY=[0|1]，它们分别指定了观众模式（只读挂载且没有分配日志）和只读模式（分配了日志）的状态。

2. ONLINE
---------

ONLINE uevent 在成功挂载或重新挂载后生成。它具有与 ADD uevent 相同的环境变量。ONLINE uevent 及其两个环境变量（SPECTATOR 和 RDONLY）是相对较新的添加（自 2.6.32-rc+ 版本起），旧内核不会生成这些 uevent。

3. CHANGE
---------

CHANGE uevent 用于两个地方。其中一个是在第一个节点成功挂载文件系统时报告（FIRSTMOUNT=Done）。这是 gfs_controld 用来指示其他集群节点可以挂载该文件系统的信号。
另一个 CHANGE uevent 用于通知某个文件系统日志完成恢复。它有两个环境变量，JID= 指定了刚刚恢复的日志 ID，RECOVERY=[Done|Failed] 表示操作是否成功。这些 uevent 在每次日志恢复时都会生成，无论是在初始挂载过程中还是作为 gfs_controld 通过 /sys/fs/gfs2/<fsname>/lock_module/recovery 文件请求特定日志恢复的结果。
由于早期版本的 gfs_controld 使用 CHANGE uevent 时未检查环境变量来发现状态，我们无法为其添加更多功能，否则可能会导致使用旧版用户工具的人破坏他们的集群。因此，在添加新的成功挂载或重新挂载的 uevent 时使用了 ONLINE uevent。

4. OFFLINE
----------

OFFLINE uevent 仅因文件系统错误而生成，并用于“撤回”机制的一部分。目前这并没有提供关于错误的具体信息，这是一个需要修复的问题。
5. 移除 (REMOVE)
----------------

移除 (REMOVE) 事件是在挂载失败结束时或卸载文件系统结束时生成的。所有移除 (REMOVE) 事件之前至少会有一个针对同一文件系统的添加 (ADD) 事件。与其他 uevent 不同，移除 (REMOVE) 事件是由内核的 kobject 子系统自动生成的。

所有 GFS2 uevent 的通用信息（uevent 环境变量）
=================================================

1. 锁表 (LOCKTABLE)=
----------------------

锁表 (LOCKTABLE) 是一个字符串，由挂载命令行（locktable=）或通过 fstab 提供。它用作文件系统标签，并提供锁管理器 lock_dlm 挂载以加入集群所需的信息。

2. 锁协议 (LOCKPROTO)=
-----------------------

锁协议 (LOCKPROTO) 是一个字符串，其值取决于挂载命令行或通过 fstab 设置的内容。它可以是 lock_nolock 或 lock_dlm。未来可能会支持其他锁管理器。

3. 日志 ID (JOURNALID)=
------------------------

如果文件系统使用了日志（对于旁观者挂载不会分配日志），则此值将给出在所有 GFS2 uevent 中的日志数字 ID。

4. UUID=
----------

在 gfs2-utils 的最新版本中，mkfs.gfs2 会在文件系统的超级块中写入一个 UUID。如果存在，该 UUID 将包含在与文件系统相关的每个 uevent 中。
