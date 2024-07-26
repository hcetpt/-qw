======================
Linux 安全模块：为 Linux 提供通用安全钩子
======================

:作者: Stephen Smalley
:作者: Timothy Fraser
:作者: Chris Vance

.. note::

   本书中描述的 API 已过时。

简介
============

2001 年 3 月，美国国家安全局（NSA）在 2.5 版本的 Linux 内核峰会上发表了一次关于增强型安全 Linux（SELinux）的演讲。SELinux 是在 Linux 内核中实现灵活和精细的非任意访问控制的一种方式，最初是作为一个特定的内核补丁来实现的。其他几个安全项目（例如 RSBAC、Medusa）也为 Linux 内核开发了灵活的访问控制架构，并且一些项目还为 Linux 开发了特定的访问控制模型（例如 LIDS、DTE、SubDomain）。每个项目都开发并维护了自己的内核补丁以支持其安全需求。

针对 NSA 的演讲，Linus Torvalds 发表了一系列评论，描述了一个他愿意考虑加入主流 Linux 内核的安全框架。他描述了一个通用框架，它提供了一组安全钩子来控制内核对象上的操作，以及一组内核数据结构中的不透明安全字段以维护安全属性。这个框架可以被可加载的内核模块使用，以实现任何所需的模型。Linus 还提出了将 Linux 权限代码迁移到这样一个模块的可能性。

WireX 启动了 Linux 安全模块（LSM）项目来开发这样一个框架。LSM 项目是由多个安全项目共同开发的，包括 Immunix、SELinux、SGI 和 Janus，以及几位个人开发者，如 Greg Kroah-Hartman 和 James Morris。他们共同开发了一个实现该框架的 Linux 内核补丁。这项工作于 2003 年 12 月被合并到了主流版本中。这份技术报告概述了该框架及其权限安全模块的能力。

LSM 框架
============

LSM 框架提供了一个通用的内核框架来支持安全模块。具体而言，LSM 框架主要关注支持访问控制模块，尽管未来的开发可能会涉及其他安全需求，比如沙箱化。就其本身而言，该框架并不提供额外的安全性；它仅仅提供了支持安全模块的基础设施。LSM 框架是可选的，需要启用 `CONFIG_SECURITY`。权限逻辑作为安全模块实现。

此权限模块将在 `LSM 权限模块`_ 中进一步讨论。

LSM 框架在内核数据结构中包含了安全字段，并在内核代码的关键点调用钩子函数来管理这些安全字段并执行访问控制。它还添加了注册安全模块的功能。

接口 `/sys/kernel/security/lsm` 报告系统上激活的安全模块列表，以逗号分隔的形式呈现。
LSM 安全字段仅仅是 `void*` 指针。这些数据被称为 blob（二进制大对象），可能由框架管理，也可能由使用它的各个安全模块管理。被多个安全模块使用的安全 blob 通常由框架管理。

对于进程和程序执行安全信息，安全字段包含在 `struct task_struct` 和 `struct cred` 中。

对于文件系统安全信息，一个安全字段包含在 `struct super_block` 中。

对于管道、文件和套接字安全信息，安全字段包含在 `struct inode` 和 `struct file` 中。

对于 System V IPC 安全信息，安全字段被添加到了 `struct kern_ipc_perm` 和 `struct msg_msg` 中；此外，`struct msg_msg`、`struct msg_queue` 和 `struct shmid_kernel` 的定义被移动到头文件中（如 `include/linux/msg.h` 和 `include/linux/shm.h` 所示），以便安全模块可以使用这些定义。

对于数据包和网络设备安全信息，安全字段被添加到了 `struct sk_buff` 和 `struct scm_cookie` 中。与其它安全模块数据不同的是，这里使用的是一个 32 位整数。安全模块需要将这些值映射或以其他方式与实际的安全属性关联起来。

LSM 钩子被维护在列表中。每个钩子都有一个列表，并且按照 CONFIG_LSM 指定的顺序调用这些钩子。

每个钩子的详细文档都包含在 `security/security.c` 源文件中。
LSM框架提供了对通用安全模块堆叠的近似实现。它定义了`security_add_hooks()`，每个安全模块通过该函数传递一个`:c:type:'struct security_hooks_list<security_hooks_list>'`类型的结构体，这些结构体会被添加到列表中。
LSM框架没有提供移除已注册钩子的机制。虽然SELinux安全模块实现了一种自我移除的方式，但这一特性已经被废弃。
这些钩子可以大致分为两类：一类用于管理安全字段的钩子和另一类用于执行访问控制的钩子。第一类钩子的例子包括`security_inode_alloc()`和`security_inode_free()`，这些钩子用于为inode对象分配和释放安全结构。
第二类钩子的一个例子是`security_inode_permission()`钩子，这个钩子在访问inode时检查权限。

### LSM能力模块

POSIX.1e的能力逻辑作为一个安全模块进行维护，存储在文件`security/commoncap.c`中。能力模块使用`:c:type:'lsm_info'`描述中的order字段来标识其作为第一个被注册的安全模块。
与其它模块不同的是，能力安全模块不使用通用安全数据块。这主要是基于历史原因，以及出于开销、复杂性和性能方面的考虑。
