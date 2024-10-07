===============================================
Linux 安全模块：Linux 的通用安全挂钩
===============================================

:作者: Stephen Smalley
:作者: Timothy Fraser
:作者: Chris Vance

.. note::

   本书中描述的 API 已过时

简介
============

2001 年 3 月，国家安全局（NSA）在 2.5 版本的 Linux 内核峰会上介绍了一种增强型 Linux 安全（SELinux）。SELinux 是在 Linux 内核中实现的一种灵活且细粒度的非自主访问控制方法，最初是作为特定的内核补丁来实现的。其他几个安全项目（例如 RSBAC、Medusa）也开发了适用于 Linux 内核的灵活访问控制架构，并且一些项目为 Linux 开发了特定的访问控制模型（例如 LIDS、DTE、SubDomain）。每个项目都开发并维护了自己的内核补丁以支持其安全需求。

在回应 NSA 的介绍时，Linus Torvalds 提出了一系列评论，描述了一个他愿意考虑纳入主流 Linux 内核的安全框架。他描述了一个通用框架，该框架提供了一组安全挂钩来控制对内核对象的操作以及一组内核数据结构中的不透明安全字段以维护安全属性。然后可以使用这种框架由可加载的内核模块来实现任何所需的安全模型。Linus 还提出了将 Linux 权限代码迁移到此类模块的可能性。

WireX 启动了 Linux 安全模块（LSM）项目来开发这样的框架。LSM 是多个安全项目的联合开发努力，包括 Immunix、SELinux、SGI 和 Janus，以及几位个人，包括 Greg Kroah-Hartman 和 James Morris，目的是开发一个实现该框架的 Linux 内核补丁。这项工作于 2003 年 12 月被纳入主流。本技术报告提供了对该框架和权限安全模块功能的概述。

LSM 框架
=============

LSM 框架提供了一个通用的内核框架来支持安全模块。特别是，LSM 框架主要关注支持访问控制模块，尽管未来的发展可能会解决其他安全需求，例如沙箱化。仅凭自身，该框架并不提供任何额外的安全性；它只是提供了支持安全模块的基础设施。LSM 框架是可选的，需要启用 `CONFIG_SECURITY`。权限逻辑是作为安全模块实现的。

此权限模块在 `LSM 权限模块`_ 中进一步讨论。

LSM 框架包括内核数据结构中的安全字段，并在内核代码的关键点调用挂钩函数来管理这些安全字段并执行访问控制。它还增加了注册安全模块的功能。接口 `/sys/kernel/security/lsm` 报告系统上活动的安全模块列表，以逗号分隔的形式呈现。
LSM 安全字段仅仅是 `void*` 指针。
这些数据被称为 blob，可以由框架或使用它的各个安全模块管理。
被多个安全模块使用的安全 blob 通常由框架进行管理。

对于进程和程序执行的安全信息，安全字段包含在 `struct task_struct` 和 `struct cred` 中。
对于文件系统安全信息，一个安全字段包含在 `struct super_block` 中。
对于管道、文件和套接字的安全信息，安全字段包含在 `struct inode` 和 `struct file` 中。
对于 System V IPC 安全信息，安全字段被添加到 `struct kern_ipc_perm` 和 `struct msg_msg` 中；
此外，`struct msg_msg`、`struct msg_queue` 和 `struct shmid_kernel` 的定义被移到了相应的头文件（`include/linux/msg.h` 和 `include/linux/shm.h`）中，以便让安全模块能够使用这些定义。
对于包和网络设备的安全信息，安全字段被添加到了 `struct sk_buff` 和 `struct scm_cookie` 中。
与其它安全模块的数据不同，这里使用的数据是一个 32 位整数。安全模块需要将这些值映射或以其他方式关联到实际的安全属性上。

LSM 钩子（hooks）被维护在一个列表中。每个钩子都有一个列表，并且按照 CONFIG_LSM 规定的顺序调用这些钩子。
每个钩子的详细文档都包含在 `security/security.c` 源文件中。
LSM框架提供了对通用安全模块堆叠的近似实现。它定义了`security_add_hooks()`，每个安全模块通过该函数传递一个`:c:type:'struct security_hooks_list<security_hooks_list>'`，这些钩子会被添加到列表中。

LSM框架没有提供移除已注册钩子的机制。然而，SELinux安全模块实现了一种自我移除的方式，但这一功能已被弃用。

这些钩子可以分为两大类：一类用于管理安全字段的钩子，另一类用于执行访问控制的钩子。第一类钩子的例子包括`security_inode_alloc()`和`security_inode_free()`。这些钩子用于为inode对象分配和释放安全结构。

第二类钩子的一个例子是`security_inode_permission()`钩子。这个钩子在访问inode时检查权限。

### LSM能力模块

POSIX.1e的能力逻辑作为一个安全模块存储在文件`security/commoncap.c`中。该能力模块使用`:c:type:'lsm_info'`描述中的order字段来标识其为第一个被注册的安全模块。

与其它模块不同的是，能力安全模块不使用通用安全blob。这是基于历史原因以及开销、复杂性和性能方面的考虑。
