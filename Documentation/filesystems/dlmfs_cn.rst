.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

=====
DLMFS
=====

一个通过虚拟文件系统实现的最小化 DLM 用户空间接口。
dlmfs 是与 OCFS2 一起构建的，因为它需要大部分 OCFS2 的基础设施。
:项目网页:    http://ocfs2.wiki.kernel.org
:工具网页:      https://github.com/markfasheh/ocfs2-tools
:OCFS2 邮件列表: https://subspace.kernel.org/lists.linux.dev.html

所有代码版权 2005 Oracle，除非另有说明。
致谢
=======

部分代码取自 ramfs，该代码版权 © 2000 Linus Torvalds 和 Transmeta Corp
Mark Fasheh <mark.fasheh@oracle.com>

注意事项
=======
- 目前它只支持 OCFS2 DLM，尽管其他 DLM 实现的支持不应是大问题。
挂载选项
=============
无

用法
=====

如果您对 OCFS2 感兴趣，请参阅 ocfs2.txt。本文档其余部分将面向那些希望使用 dlmfs 进行易于设置和使用的用户空间集群锁定的人。
设置
=====

dlmfs 要求 OCFS2 集群基础设施就位。请从上述网址下载 ocfs2-tools 并配置一个集群。
您需要在一个所有锁空间中的节点都能访问的卷上启动心跳。最简单的方法是通过 ocfs2_hb_ctl（随 ocfs2-tools 发布）。目前，它要求有一个 OCFS2 文件系统以便自动找到心跳区域，但最终会支持针对原始磁盘的心跳。
请参阅随 ocfs2-tools 发布的 ocfs2_hb_ctl 和 mkfs.ocfs2 手册页。
一旦心跳开始，可以在 DLM 锁“域”中轻松创建/销毁锁，并访问其中的锁。
锁定
=======

用户可以通过标准文件系统调用访问dlmfs，也可以使用与ocfs2-tools一起分发的'libo2dlm'。'libo2dlm'抽象了文件系统调用，并提供了一个更传统的锁定API。
dlmfs会自动处理锁缓存，因此对于已经获取的锁再次请求不会生成新的DLM调用。假设用户空间程序自行处理本地锁定。
支持两种级别的锁——共享读取和独占。
还支持尝试锁定（Trylock）操作。
有关libo2dlm接口的信息，请参见随ocfs2-tools分发的o2dlm.h。
锁值块（LVB）可以通过read(2)和write(2)针对通过open(2)获得的文件描述符进行读写。目前支持的最大LVB长度为64字节（尽管这是OCFS2 DLM的限制）。通过这种机制，dlmfs用户可以在节点之间共享少量数据。
mkdir(2)信号指示dlmfs加入一个域（该域将具有与创建目录相同的名字）。

rmdir(2)信号指示dlmfs离开该域。

给定域中的锁由域目录内的常规inode表示。对它们进行锁定是通过open(2)系统调用来完成的。
除非被指示执行尝试锁定操作，否则open(2)调用不会返回，直到您的锁被授予或发生错误。如果锁定成功，您将获得一个文件描述符。
使用O_CREAT标志的open(2)来确保资源inode被创建——dlmfs不会自动为现有的锁资源创建inode。

============  ===========================
Open Flag     锁请求类型
============  ===========================
O_RDONLY      共享读取
O_RDWR        独占
============  ===========================

============  ===========================
Open Flag     结果锁定行为
============  ===========================
O_NONBLOCK    尝试锁定操作
============  ===========================

您必须确切地提供O_RDONLY或O_RDWR中的一个。
如果同时提供了 O_NONBLOCK，并且 trylock 操作有效但无法锁定资源，则 open(2) 将返回 ETXTBUSY。
close(2) 会释放与文件描述符相关的锁。
传递给 mkdir(2) 或 open(2) 的模式会在本地生效。chown 也在本地支持。这意味着您可以使用它们来限制仅在本地节点上通过 dlmfs 访问资源。
资源 LVB 可以通过 read(2) 系统调用以共享读取或独占模式从文件描述符中读取。只有在以独占模式打开时，才能通过 write(2) 进行写入。
一旦写入，LVB 将对获取了只读或更高级别锁的其他节点可见。

参考
======
http://opendlm.sourceforge.net/cvsmirror/opendlm/docs/dlmbook_final.pdf

有关 VMS 分布式锁定 API 的更多信息，请参阅上述链接。
