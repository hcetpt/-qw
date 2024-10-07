==============================
Linux 安全模块：面向Linux的通用安全钩子
==============================

:作者: Stephen Smalley  
:作者: Timothy Fraser  
:作者: Chris Vance  

.. note::

   本书中描述的API已经过时。

引言
============

2001年3月，美国国家安全局（NSA）在2.5版Linux内核峰会上介绍了一种增强安全性的Linux（SELinux）。SELinux是一种在Linux内核中实现灵活且细粒度的强制访问控制的方法，最初是作为特定的内核补丁来实现的。其他几个安全项目（如RSBAC、Medusa）也开发了适用于Linux内核的灵活访问控制系统，还有各种项目为Linux开发了特定的访问控制模型（如LIDS、DTE、SubDomain）。每个项目都开发并维护了自己的内核补丁以支持其安全需求。

在回应NSA的演讲时，Linus Torvalds发表了一些评论，描述了一个他愿意考虑纳入主流Linux内核的安全框架。他描述了一个通用框架，该框架提供了一组用于控制内核对象操作的安全钩子，以及一组内核数据结构中的不透明安全字段，用于维护安全属性。这种框架可以被可加载的内核模块用来实现任何所需的安全模型。Linus还提出了将Linux权限代码迁移到这样一个模块的可能性。

WireX启动了Linux安全模块（LSM）项目来开发这样的框架。LSM是由包括Immunix、SELinux、SGI和Janus在内的多个安全项目以及Greg Kroah-Hartman和James Morris等个人共同开发的，目的是开发一个实现此框架的Linux内核补丁。这项工作于2003年12月被纳入主流。本技术报告提供了该框架及其能力安全模块的概述。

LSM框架
=============

LSM框架提供了一个通用的内核框架以支持安全模块。特别是，LSM框架主要专注于支持访问控制模块，尽管未来的开发可能会涉及其他安全需求，如沙箱。就其本身而言，该框架并不提供任何额外的安全性；它仅提供支持安全模块的基础设施。LSM框架是可选的，需要启用`CONFIG_SECURITY`。权限逻辑是以安全模块的形式实现的。

此权限模块在`LSM权限模块`_中有进一步讨论。

LSM框架包括内核数据结构中的安全字段，并在内核代码的关键点调用钩子函数来管理这些安全字段并执行访问控制。它还增加了注册安全模块的功能。接口`/sys/kernel/security/lsm`报告系统上活动的安全模块列表，用逗号分隔。
LSM 安全字段仅仅是 `void*` 指针。
这些数据被称为 blob（二进制大对象），可以由框架或使用它的各个安全模块管理。
被多个安全模块使用的安全 blob 通常由框架进行管理。

对于进程和程序执行的安全信息，安全字段包含在 `struct task_struct` 和 `struct cred` 中。
对于文件系统安全信息，一个安全字段包含在 `struct super_block` 中。
对于管道、文件和套接字的安全信息，安全字段包含在 `struct inode` 和 `struct file` 中。
对于 System V IPC 安全信息，安全字段被添加到 `struct kern_ipc_perm` 和 `struct msg_msg` 中；
此外，`struct msg_msg`、`struct msg_queue` 和 `struct shmid_kernel` 的定义被移到了头文件中（`include/linux/msg.h` 和 `include/linux/shm.h`）以允许安全模块使用这些定义。
对于数据包和网络设备的安全信息，安全字段被添加到了 `struct sk_buff` 和 `struct scm_cookie` 中。
与其它安全模块数据不同的是，这里使用的是一个 32 位整数。安全模块需要将这些值映射或关联到实际的安全属性上。

LSM 钩子函数被维护在一个列表中。每个钩子都有一个列表，并且按照 `CONFIG_LSM` 规定的顺序调用。
每个钩子的详细文档都包含在 `security/security.c` 源文件中。
LSM框架提供了对通用安全模块堆叠的近似实现。它定义了`security_add_hooks()`函数，每个安全模块通过该函数传递一个`:c:type:`struct security_hooks_list <security_hooks_list>`结构体，这些结构体会被添加到列表中。

LSM框架没有提供移除已注册钩子的机制。虽然SELinux安全模块实现了自我移除的方式，但这一功能已被弃用。

这些钩子可以分为两大类：用于管理安全字段的钩子和用于执行访问控制的钩子。第一类钩子的例子包括`security_inode_alloc()`和`security_inode_free()`。这些钩子用于为inode对象分配和释放安全结构。

第二类钩子的一个例子是`security_inode_permission()`钩子。这个钩子在访问inode时检查权限。

### LSM能力模块

POSIX.1e的能力逻辑作为一个安全模块存储在文件`security/commoncap.c`中。能力模块使用`:c:type:`lsm_info`描述中的order字段来标识其为第一个注册的安全模块。

与其它模块不同，能力安全模块不使用通用的安全数据块。这主要是基于历史原因，并且出于开销、复杂性和性能方面的考虑。
