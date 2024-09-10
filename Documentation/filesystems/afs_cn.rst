SPDX 许可证标识符: GPL-2.0

====================
kAFS：AFS 文件系统
====================

.. 目录：

- 概览
- 使用方法
- 挂载点
- 动态根目录
- proc 文件系统
- 单元数据库
- 安全性
- @sys 替换

概览
========

此文件系统提供了一个相对简单的安全 AFS 文件系统驱动程序。它仍在开发中，尚未提供全部功能。它目前支持的功能包括：

 (*) 安全（目前仅支持 AFS kaserver 和 KerberosIV 票据）
(*) 文件读写
(*) 自动挂载
(*) 本地缓存（通过 fscache）
它目前还不支持以下 AFS 功能：

(*) pioctl() 系统调用
编译
===========

文件系统应该通过启用以下内核配置选项来激活：

	CONFIG_AF_RXRPC		- RxRPC 协议传输
	CONFIG_RXKAD		- RxRPC Kerberos 安全处理程序
	CONFIG_AFS_FS		- AFS 文件系统

此外，可以启用以下选项以帮助调试：

	CONFIG_AF_RXRPC_DEBUG	- 允许启用 AF_RXRPC 调试
	CONFIG_AFS_DEBUG	- 允许启用 AFS 调试

它们允许通过修改以下文件中的掩码来动态启用调试消息：

	/sys/module/af_rxrpc/parameters/debug
	/sys/module/kafs/parameters/debug

使用
=====

在插入驱动模块时，必须指定根单元以及一组卷位置服务器的 IP 地址：

	modprobe rxrpc
	modprobe kafs rootcell=cambridge.redhat.com:172.16.18.73:172.16.18.91

第一个模块是 AF_RXRPC 网络协议驱动。这提供了 RxRPC 远程操作协议，并且也可以从用户空间访问。详见：

	Documentation/networking/rxrpc.rst

第二个模块是 Kerberos RxRPC 安全驱动，第三个模块是 AFS 文件系统的实际文件系统驱动。
加载模块后，可以通过以下过程添加更多模块：

	echo add grand.central.org 18.9.48.14:128.2.203.61:130.237.48.87 >/proc/fs/afs/cells

其中，“add”命令的参数是一个单元的名称和该单元中的一组卷位置服务器，后者用冒号分隔。
文件系统可以通过类似以下命令的方式挂载到任何位置：

	mount -t afs "%cambridge.redhat.com:root.afs." /afs
	mount -t afs "#cambridge.redhat.com:root.cell." /afs/cambridge
	mount -t afs "#root.afs." /afs
	mount -t afs "#root.cell." /afs/cambridge

其中初始字符是井号或百分号，取决于您是否确定要使用 R/W 卷（百分号）还是更倾向于使用 R/O 卷但愿意使用 R/W 卷（井号）。
卷的名称可以附加 ".backup" 或 ".readonly" 后缀，以指定仅连接这些类型的卷。
单元名称是可选的，如果在挂载时不提供，则将在 modprobe 期间指定的单元中查找命名的卷。
可以通过 /proc 添加额外的单元（参见后面的章节）。
挂载点
===========

AFS 有一个挂载点的概念。在 AFS 的术语中，这些是特殊格式的符号链接（与传递给 mount 的“设备名称”相同形式）。kAFS 将这些呈现为具有跟随链接功能的目录（即符号链接语义）。如果有人尝试访问它们，它们将自动在该位置挂载目标卷（如果可能的话）。
自动挂载的文件系统将在最后一次使用后大约二十分钟后自动卸载。或者，可以使用`umount()`系统调用来直接卸载它们。
手动卸载AFS卷将首先删除该卷上的所有空闲子挂载。如果所有子挂载都被删除，则请求的卷也将被卸载；否则会返回错误EBUSY。
管理员可以通过执行以下命令尝试一次性卸载挂载在/afs下的整个AFS树：

	umount /afs

动态根目录
==========

有一个挂载选项可以创建一个仅用于动态查找且无需服务器的挂载。例如，可以通过以下命令创建这样的挂载：

	mount -t afs none /afs -o dyn

这将创建一个根目录为空目录的挂载。尝试在此目录中查找名称将会创建一个挂载点来查找具有相同名称的单元，例如：

	ls /afs/grand.central.org/

proc 文件系统
=============

AFS模块创建了一个“/proc/fs/afs/”目录并填充了内容：

  (*) “cells”文件列出了当前已知的单元及其使用计数：

	[root@andromeda ~]# cat /proc/fs/afs/cells
	USE NAME
	  3 cambridge.redhat.com

  (*) 每个单元下有一个目录，其中包含列出该单元内已知的卷位置服务器、卷和活动服务器的文件：

	[root@andromeda ~]# cat /proc/fs/afs/cambridge.redhat.com/servers
	USE ADDR            STATE
	  4 172.16.18.91        0
	[root@andromeda ~]# cat /proc/fs/afs/cambridge.redhat.com/vlservers
	ADDRESS
	172.16.18.91
	[root@andromeda ~]# cat /proc/fs/afs/cambridge.redhat.com/volumes
	USE STT VLID[0]  VLID[1]  VLID[2]  NAME
	  1 Val 20000000 20000001 20000002 root.afs

单元数据库
==========

文件系统维护了一个内部数据库，记录了它所知道的所有单元以及这些单元的卷位置服务器的IP地址。系统所属的单元会在通过modprobe加载时通过“rootcell=”参数添加到数据库中，或者如果编译到内核中，则通过内核命令行上的“kafs.rootcell=”参数添加。
可以通过类似以下命令的方式进一步添加其他单元：

	echo add CELLNAME VLADDR[:VLADDR][:VLADDR]... >/proc/fs/afs/cells
	echo add grand.central.org 18.9.48.14:128.2.203.61:130.237.48.87 >/proc/fs/afs/cells

目前没有其他单元数据库操作可用。

安全性
======

安全操作需要通过klog程序获取密钥。一个非常基础的klog程序可以在以下链接找到：

	https://people.redhat.com/~dhowells/rxrpc/klog.c

应该通过以下命令编译它：

	make klog LDLIBS="-lcrypto -lcrypt -lkrb4 -lkeyutils"

然后以如下方式运行：

	./klog

假设成功，这将添加一个类型为RxRPC、名为服务和单元的密钥，例如：“afs@<cellname>”。可以通过keyctl程序或cat /proc/keys查看密钥：

	[root@andromeda ~]# keyctl show
	Session Keyring
	       -3 --alswrv      0     0  keyring: _ses.3268
		2 --alswrv      0     0   \_ keyring: _uid.0
	111416553 --als--v      0     0   \_ rxrpc: afs@CAMBRIDGE.REDHAT.COM

目前用户名、域、密码和提议的票据生命周期是编译到程序中的。
在使用AFS设施之前不需要获取密钥，但如果未获取密钥，则所有操作都将受ACL中的匿名用户部分控制。
如果获取了密钥，则持有该密钥的所有AFS操作（包括挂载和自动挂载）都将用该密钥进行保护。
如果使用特定密钥打开文件，然后将文件描述符传递给没有该密钥的过程（可能是通过AF_UNIX套接字），那么对文件的操作将使用打开文件时使用的密钥进行。

@sys 替换
=========

可以通过向/proc/fs/afs/sysname写入列表来配置当前网络命名空间最多16个@sys替换：

	[root@andromeda ~]# echo foo amd64_linux_26 >/proc/fs/afs/sysname

或者通过写入空列表来完全清除：

	[root@andromeda ~]# echo >/proc/fs/afs/sysname

可以通过以下命令检索当前网络命名空间的当前列表：

	[root@andromeda ~]# cat /proc/fs/afs/sysname
	foo
	amd64_linux_26

当@sys被替换时，将按照给定顺序尝试列表中的每个元素。
默认情况下，列表将包含一个符合“<arch>_linux_26”模式的项目，其中amd64表示x86_64。
当然，请提供您需要翻译的文本。
