.. SPDX-License-Identifier: GPL-2.0
.. Copyright © 2017-2020 Mickaël Salaün <mic@digikod.net>
.. Copyright © 2019-2020 ANSSI

==================================
Landlock LSM：内核文档
==================================

:作者: Mickaël Salaün
:日期: 2022年12月

Landlock 的目标是创建有范围的访问控制（即沙箱）。为了增强整个系统的安全性，此功能应可供任何进程使用，包括非特权进程。由于这样的进程可能被破坏或植入后门（即不可信），因此 Landlock 的功能必须从内核和其他进程的角度来看是安全的。因此，Landlock 的接口必须暴露最小的攻击面。

Landlock 被设计为可在遵循系统安全策略（由其他访问控制机制（例如 DAC、LSM）强制执行）的情况下供非特权进程使用。实际上，一个 Landlock 规则不应干扰系统上强制执行的其他访问控制，而只能增加更多限制。
任何用户都可以在其进程中强制执行 Landlock 规则集。这些规则集将与继承的规则集合并并进行评估，以确保仅能添加更多约束。

用户空间文档可在此处找到：
Documentation/userspace-api/landlock.rst

安全访问控制的指导原则
===========================================

* Landlock 规则应专注于对内核对象的访问控制，而不是系统调用过滤（即系统调用参数），这是 seccomp-bpf 的目的。
* 为了避免多种侧信道攻击（例如安全策略泄露、基于 CPU 的攻击），Landlock 规则不应能够通过编程方式与用户空间通信。
* 内核访问检查不应减慢未沙箱化进程的访问请求。
* 与 Landlock 操作相关的计算（例如强制执行规则集）只应影响请求它们的进程。
* 由沙箱化进程直接从内核获取的资源（例如文件描述符）无论由哪个进程使用，都应保留其在获取资源时的受限访问权限。

参见 `文件描述符访问权限`_
设计选择
==============

inode 访问权限
-------------------

所有访问权限都与 inode 相关联，并且决定了通过该 inode 可以访问的内容。
读取目录内容并不意味着有权读取该目录中列出的 inode 的内容。确实，文件名是相对于其父目录的，而一个 inode 可以通过多个文件名（硬链接）来引用。能够删除一个文件只直接影响到目录本身，而不是被删除的 inode。这就是为什么 ``LANDLOCK_ACCESS_FS_REMOVE_FILE`` 或 ``LANDLOCK_ACCESS_FS_REFER`` 不允许绑定到文件上，而只能绑定到目录上的原因。

文件描述符访问权限
------------------------

在打开文件时会检查并绑定文件描述符的访问权限。其基本原理是在相同 Landlock 域下执行等效的操作序列应产生相同的结果。
以 ``LANDLOCK_ACCESS_FS_TRUNCATE`` 权限为例，如果相关文件层次结构不授予此类访问权限，则即使允许打开文件进行写入，也不一定允许对生成的文件描述符使用 :manpage:`ftruncate`。以下操作序列具有相同的语义，因此应该产生相同的结果：

* ``truncate(path);``
* ``int fd = open(path, O_WRONLY); ftruncate(fd); close(fd);``

类似于文件访问模式（例如 ``O_RDWR``），文件描述符上的 Landlock 访问权限即使在它们在进程间传递（例如通过 Unix 域套接字）时也会保留。因此，即使接收进程没有被 Landlock 沙箱化，这些访问权限也会被强制执行。确实，这是为了在整个系统中保持一致的访问控制，并避免通过文件描述符传递带来的意外绕过（即困惑副手攻击）。

测试
=====

用于向后兼容性、ptrace 限制和文件系统支持的用户空间测试可以在这里找到：`tools/testing/selftests/landlock/`_

内核结构
==========

对象
--------------

.. kernel-doc:: security/landlock/object.h
    :identifiers:

文件系统
--------------

.. kernel-doc:: security/landlock/fs.h
    :identifiers:

规则集和域
------------------

域是一个与一组主体（即任务凭证）相关的只读规则集。每次将规则集强加给任务时，都会复制当前域，并将规则集导入新域作为新的一层规则。确实，在一个域中，每个规则都与一个层级别相关联。要授予对对象的访问权限，每个层至少需要有一条规则允许对该对象执行请求的操作。然后，任务只能转移到一个新的域，该域是当前域的约束与任务提供的规则集之间的交集。
对于自我沙箱化的任务来说，主体的定义是隐式的，这使得推理变得更加容易，并有助于避免陷阱。
.. kernel-doc:: security/landlock/ruleset.h
    :identifiers:

.. 链接
.. _tools/testing/selftests/landlock/: https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/landlock/
