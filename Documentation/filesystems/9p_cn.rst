```
SPDX 许可证标识符: GPL-2.0

=======================================
v9fs: Plan 9 资源共享在 Linux 上的实现
=======================================

关于
====

v9fs 是 Plan 9 的 9p 远程文件系统协议的 Unix 实现。
该软件最初由 Ron Minnich <rminnich@sandia.gov> 和 Maya Gokhale 开发。
后续开发由 Greg Watson <gwatson@lanl.gov> 完成，最近由 Eric Van Hensbergen <ericvh@gmail.com>、Latchesar Ionkov <lucho@ionkov.net> 和 Russ Cox <rsc@swtch.com> 继续进行。
关于 9p 客户端的 Linux 实现及其应用的最佳详细解释可以在以下 USENIX 论文中找到：

   https://www.usenix.org/events/usenix05/tech/freenix/hensbergen.html

其他应用在以下论文中有所描述：

	* XCPU & 集群
	  http://xcpu.org/papers/xcpu-talk.pdf
	* KVMFS：KVM 控制文件系统
	  http://xcpu.org/papers/kvmfs.pdf
	* CellFS：一种针对 Cell BE 的新编程模型
	  http://xcpu.org/papers/cellfs-talk.pdf
	* PROSE I/O：使用 9p 启用应用程序分区
	  http://plan9.escet.urjc.es/iwp9/cready/PROSE_iwp9_2006.pdf
	* VirtFS：一种面向虚拟化的文件系统直通
	  http://goo.gl/3WPDg

使用
====

对于远程文件服务器：

	mount -t 9p 10.10.1.2 /mnt/9

对于 Plan 9 From User Space 应用程序（http://swtch.com/plan9）：

	mount -t 9p `namespace`/acme /mnt/9 -o trans=unix,uname=$USER

对于运行在带有 virtio 传输的 QEMU 主机上的服务器：

	mount -t 9p -o trans=virtio <mount_tag> /mnt/9

其中，mount_tag 是服务器为每个导出挂载点关联的标签。每个 9P 导出都会被客户端视为一个具有关联“mount_tag”属性的 virtio 设备。可用的 mount_tag 可以通过读取 /sys/bus/virtio/drivers/9pnet_virtio/virtio<n>/mount_tag 文件来查看。

选项
====

  ============= ===============================================================
  trans=name    选择一种替代传输方式。当前有效的选项包括：

			========  ============================================
			unix      指定命名管道挂载点
			tcp       指定普通的 TCP/IP 连接
			fd        使用传递的文件描述符进行连接
                                  （参见 rfdno 和 wfdno）
			virtio    连接到下一个可用的 virtio 通道
					（从带有 trans_virtio 模块的 QEMU）
			rdma      连接到指定的 RDMA 通道
			========  ============================================

  uname=name    尝试在远程服务器上以指定用户名称进行挂载。服务器可能会覆盖或忽略此值。某些用户名可能需要认证。
aname=name     aname 指定了当服务器提供多个导出文件系统时要访问的文件树。
cache=mode     指定缓存策略。默认情况下，不使用任何缓存。
             模式可以指定为位掩码或使用预定义的常见“快捷方式”。
             位掩码如下所示（未指定的位保留）：

			==========  ====================================================
			0b00000000  禁用所有缓存，禁用 mmap
			0b00000001  启用文件缓存
			0b00000010  启用元数据缓存
			0b00000100  写回行为（而非写透）
			0b00001000  松散缓存（与服务器无显式一致性）
			0b10000000  启用 fscache 用于持久性缓存
			==========  ====================================================

             当前的快捷方式及其对应的位掩码为：

			=========   ====================================================
			none        0b00000000（无缓存）
			readahead   0b00000001（仅读取提前文件缓存）
			mmap        0b00000101（读取提前加写回文件缓存）
			loose       0b00001111（非一致文件和元数据缓存）
			fscache     0b10001111（持久性松散缓存）
			=========   ====================================================

             注意：目前只有这些快捷方式是经过测试的操作模式，因此使用其他位组合的效果未知。更好的缓存支持正在开发中。
重要提示：松散缓存（以及目前 fscache）不一定在服务器上验证缓存值。换句话说，服务器上的更改不一定反映到客户端系统上。只有在您拥有独占挂载并且服务器不会在您下方修改文件系统的情况下才使用此操作模式。
debug=n       指定调试级别。调试级别是一个位掩码
```
```
=====   ================================
0x01    显示详细的错误信息
0x02    开发者调试（DEBUG_CURRENT）
0x04    显示 9p 跟踪
0x08    显示 VFS 跟踪
0x10    显示 Marshalling 调试
0x20    显示 RPC 调试
0x40    显示传输调试
0x80    显示分配调试
0x100   显示协议消息调试
0x200   显示 Fid 调试
0x400   显示数据包调试
0x800   显示 fscache 跟踪调试
=====   ================================

rfdno=n   用于使用 trans=fd 进行读取的文件描述符

wfdno=n   用于使用 trans=fd 进行写入的文件描述符

msize=n   用于 9p 数据包有效载荷的字节数

port=n    连接到远程服务器的端口

noextend 强制使用传统模式（不支持 9p2000.u 或 9p2000.L 语义）

version=name 选择 9P 协议版本。有效选项是：

========        ==============================
9p2000          传统模式（等同于 noextend）
9p2000.u        使用 9P2000.u 协议
9p2000.L        使用 9P2000.L 协议
========        ==============================

dfltuid 尝试以特定的 uid 挂载

dfltgid 尝试以特定的 gid 挂载

afid    安全通道 — 用于 Plan 9 认证协议

nodevmap 不映射特殊文件 — 将它们表示为普通文件
此功能可用于在主机之间共享设备/命名管道/套接字。
此功能将在以后的版本中扩展

directio 绕过所有读/写操作的页面缓存

ignoreqv 忽略 qid.version==0 作为忽略缓存的标记

noxattr 不提供此挂载上的 xattr 功能

access 有四种访问模式
user
    如果用户首次尝试访问 v9fs 文件系统中的文件，v9fs 会发送一个
    附着命令（Tattach）为该用户
    这是默认模式
<uid>
    仅允许具有 uid=<uid> 的用户访问
    已挂载文件系统上的文件
any
    v9fs 执行单次附着并以一个用户的身份执行所有操作
clien
    在 9p 客户端进行基于 ACL 的访问检查以验证访问权限

cachetag 使用指定的持久缓存标签
现有缓存会话的缓存标签可以在 /sys/fs/9p/caches 中列出
（仅适用于 cache=fscache）
============ ===============================================================

行为
========

本节旨在描述 9p 的“怪癖”，这些可能会与本地文件系统的行为不同：
- 在文件上设置 O_NONBLOCK 将使客户端读取尽快返回，
  一旦服务器返回一些数据，而不是试图用请求的数量或到达文件末尾填充读取缓冲区。

资源
=========

协议规范在 GitHub 上维护：
http://ericvh.github.com/9p-rfc/

9p 客户端和服务器实现列在
http://9p.cat-v.org/implementations

LLNL 正在开发一个 9p2000.L 服务器，可以在以下位置找到：
http://code.google.com/p/diod/

可以通过 v9fs 项目在 SourceForge 上获得用户和开发者邮件列表：
http://sourceforge.net/projects/v9fs
```
新闻和其他信息维护在一个Wiki上（http://sf.net/apps/mediawiki/v9fs/index.php）
错误报告最好通过邮件列表提交
如需了解更多关于 Plan 9 操作系统的信息，请访问 http://plan9.bell-labs.com/plan9

如需了解更多关于 Plan 9 from User Space（移植到 Linux/BSD/OSX 等的 Plan 9 应用程序和库）的信息，请访问 https://9fans.github.io/plan9port/
