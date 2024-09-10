SPDX 许可证标识符: GPL-2.0

==========================
KSMBD - SMB3 内核服务器
==========================

KSMBD 是一个在内核空间中实现 SMB3 协议的 Linux 内核服务器，用于通过网络共享文件。
KSMBD 架构
==================

与性能相关的子集操作位于内核空间，而那些与性能无关的操作则位于用户空间。因此，历史上导致许多缓冲区溢出问题和危险安全漏洞的 DCE/RPC 管理以及用户账户管理均作为 `ksmbd.mountd` 在用户空间中实现。与性能相关的文件操作（如打开、读取、写入和关闭等）则在内核空间（ksmbd）中进行。这也便于所有文件操作与 VFS 接口的集成。
ksmbd（内核守护进程）
---------------------

当服务器守护进程启动时，它会在初始化时启动一个分叉线程（ksmbd/接口名称），并打开专用端口 445 来监听 SMB 请求。每当有新的客户端发起请求时，分叉线程会接受客户端连接，并为该客户端与服务器之间的专用通信通道分叉一个新的线程。这允许并行处理来自客户端的 SMB 请求（命令），同时也允许新客户端建立新的连接。每个实例以 `ksmbd/1~n(端口号)` 的形式命名，以指示已连接的客户端。根据 SMB 请求类型，每个新线程可以决定将命令传递给用户空间 (`ksmbd.mountd`)，目前 DCE/RPC 命令被识别为通过用户空间处理。为了进一步利用 Linux 内核，选择将命令作为工作项处理，并在 ksmbd-io kworker 线程的处理器中执行。这允许内核根据负载增加额外的工作线程，反之亦然，如果负载减少则销毁多余的线程。因此，在与客户端建立连接后，专用的 `ksmbd/1..n(端口号)` 完全接管接收和解析 SMB 命令的任务。每个接收到的命令并行处理，即可以有多个客户端命令并行处理。接收到每个命令后，为每个命令准备一个独立的内核工作项，然后进一步排队由 ksmbd-io kworkers 处理。因此，每个 SMB 工作项都会排队到 kworkers 中。这使得内核能够优化地管理负载均衡，并通过并行处理客户端命令来优化客户端性能。
ksmbd.mountd（用户空间守护进程）
--------------------------------

`ksmbd.mountd` 是一个用户空间进程，用于传输使用 `ksmbd.adduser` （用户空间工具的一部分）注册的用户账户和密码。此外，它允许将从 `smb.conf` 解析出的共享信息参数传递给内核中的 KSMBD。对于执行部分，它有一个持续运行并与内核接口通过 netlink 套接字连接的守护进程，等待请求（dcerpc 和共享/用户信息）。它处理 RPC 调用（至少几十个）中最重要的一些文件服务器调用，例如 `NetShareEnum` 和 `NetServerGetInfo`。完整的 DCE/RPC 响应在用户空间中准备，并传递给关联的内核线程供客户端使用。
KSMBD 功能状态
====================

============================== =================================================
功能名称                     状态
============================== =================================================
方言支持                      支持。SMB2.1、SMB3.0 和 SMB3.1.1 方言
                               （有意排除了存在安全漏洞的 SMB1 方言）
自动协商                      支持
复合请求（Compound Request）              支持
Oplock 缓存机制（Oplock Cache Mechanism）         支持
SMB2 租约（v1 租约）          支持
目录租约（v2 租约）           支持
多信用（Multi-credits）                  支持
NTLM/NTLMv2                    支持
HMAC-SHA256 签名（HMAC-SHA256 Signing）            支持
安全协商（Secure negotiate）               支持
签名更新（Signing Update）                 支持
预认证完整性（Pre-authentication integrity）   支持
SMB3 加密（CCM, GCM）          支持。支持 CCM/GCM128 和 CCM/GCM256
SMB Direct（RDMA）              支持
SMB3 多通道                     部分支持。计划在未来实现重放/重试机制
接收端扩展模式                  支持
SMB3.1.1 POSIX 扩展            支持
ACLs                           部分支持。仅支持 DACLs，SACLs（审计）计划未来支持。对于所有权（SIDs），ksmbd 生成随机子认证值（然后存储到磁盘上），并使用从 inode 获取的 uid/gid 作为本地域 SID 的 RID
当前的 ACL 实现仅限于独立服务器，不支持域成员
正在与 Samba 工具集成，以允许未来支持作为域成员运行
Kerberos                       支持
持久句柄 v1, v2                计划未来支持
持久句柄                        计划未来支持
### SMB2 通知                    计划在未来实现
稀疏文件支持                  支持
DCE/RPC 支持                  部分支持。通过 `ksmbd.mountd` 的 netlink 接口处理了一些必需的调用（如 `NetShareEnumAll`, `NetServerGetInfo`, `SAMR`, `LSARPC`），以支持文件服务器。正在研究通过 upcall 与 Samba 工具和库进行进一步集成，以支持更多的 DCE/RPC 管理调用（以及未来对 Witness 协议的支持等）。
ksmbd/nfsd 互操作性          计划在未来实现。ksmbd 支持的功能包括租约、通知、ACL 和共享模式。
SMB3.1.1 压缩                 计划在未来实现
基于 QUIC 的 SMB3.1.1         计划在未来实现
RDMA 上的签名/加密            计划在未来实现
SMB3.1.1 GMAC 签名支持        计划在未来实现
==================================

### 如何运行
####

1. 下载 ksmbd-tools（https://github.com/cifsd-team/ksmbd-tools/releases）并编译它们：
- 参阅 README（https://github.com/cifsd-team/ksmbd-tools/blob/master/README.md），了解如何使用 `ksmbd.mountd`、`adduser`、`addshare` 和 `control` 工具。

```
$ ./autogen.sh
$ ./configure --with-rundir=/run
$ make && sudo make install
```

2. 创建 `/usr/local/etc/ksmbd/ksmbd.conf` 文件，并在 `ksmbd.conf` 文件中添加 SMB 共享：
- 参阅 ksmbd-utils 中的 `ksmbd.conf.example`，查看 `ksmbd.conf` 的手册页以详细了解如何配置共享。
```
man ksmbd.conf

3. 创建用于SMB共享的用户名/密码
- 参见 ksmbd.adduser 的手册页
$ man ksmbd.adduser
     $ sudo ksmbd.adduser -a <输入用于SMB共享访问的用户名>

4. 在构建内核后插入 ksmbd.ko 模块。如果 ksmbd 已经内置到内核中，则无需加载模块
- 在 menuconfig 中设置 ksmbd（例如：$ make menuconfig）
       [*] 网络文件系统  --->
           <M> SMB3 服务器支持（实验性）

	$ sudo modprobe ksmbd.ko

5. 启动 ksmbd 用户空间守护进程

	$ sudo ksmbd.mountd

6. 使用 SMB3 客户端（cifs.ko 或 samba 中的 smbclient）从 Windows 或 Linux 访问共享

关闭 KSMBD
==========

1. 终止用户空间和内核空间的守护进程
	# sudo ksmbd.control -s

如何开启调试打印
=================

每一层
/sys/class/ksmbd-control/debug

1. 开启所有组件的打印
	# sudo ksmbd.control -d "all"

2. 开启某个组件的打印（smb, auth, vfs, oplock, ipc, conn, rdma）
	# sudo ksmbd.control -d "smb"

3. 显示已启用的打印内容
# cat /sys/class/ksmbd-control/debug
	  [smb] auth vfs oplock ipc conn [rdma]

4. 禁用打印：
	如果您再次尝试选定的组件，它将被禁用，没有方括号
```
