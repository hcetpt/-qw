SPDX 许可证标识符: GPL-2.0

==========
spu_create
==========

名称
====
       spu_create - 创建一个新的 SPU 上下文


概要
========

       ::

         #include <sys/types.h>
         #include <sys/spu.h>

         int spu_create(const char *pathname, int flags, mode_t mode);

描述
===========
       系统调用 spu_create 用于实现 Cell Broadband Engine 架构的 PowerPC 机器上访问协同处理器单元（SPUs）。它在 pathname 中创建一个新的 SPU 逻辑上下文，并返回一个与之关联的句柄。pathname 必须指向 SPU 文件系统（spufs）挂载点中的一个不存在的目录。当 spu_create 成功时，会在 pathname 处创建一个目录，并填充一些文件。
返回的文件句柄只能传递给 spu_run(2) 或关闭，其他操作未定义。当关闭该句柄时，spufs 中所有相关的目录条目将被移除。当最后一个指向该上下文目录或此文件描述符的文件句柄被关闭时，逻辑 SPU 上下文将被销毁。
参数 flags 可以是零或以下常量中任意位或组合：

       SPU_RAWIO
              允许将 SPU 的某些硬件寄存器映射到用户空间。此标志需要 CAP_SYS_RAWIO 能力，请参阅 capabilities(7)。
mode 参数指定用于在 spufs 中创建新目录的权限。mode 将根据用户的 umask(2) 值进行修改，并用于目录及其包含的文件。文件权限掩码会屏蔽 mode 的更多位，因为它们通常只支持读或写访问。请参见 stat(2) 获取可能的 mode 值的完整列表。
返回值
============
       spu_create 返回一个新的文件描述符。如果出现错误情况，则返回 -1 并将 errno 设置为以下列出的一个错误代码。
错误
======
       EACCES
              当前用户没有对 spufs 挂载点的写入权限。
EEXIST 在给定路径名处已存在一个 SPU 上下文。
EFAULT pathname 不是在当前地址空间中的有效字符串指针。
EINVAL pathname 不是 spufs 挂载点中的目录。
ELOOP 在解析 pathname 时发现了太多的符号链接。
EMFILE 进程已达到其最大打开文件限制
ENAMETOOLONG 路径名太长
ENFILE 系统已达到全局打开文件限制
ENOENT 路径名中的一部分无法解析
ENOMEM 内核无法分配所需的所有资源
ENOSPC 没有足够的SPU资源来创建一个新的上下文，或者已达到用户特定的SPU上下文数量限制
ENOSYS 当前系统不提供此功能，因为硬件不提供SPU，或者spufs模块未加载
ENOTDIR 路径名中的某部分不是目录

注意事项：
spu_create 旨在用于实现更抽象SPU接口的库中，而不是用于常规应用程序。

参见
http://www.bsc.es/projects/deepcomputing/linuxoncell/ 推荐的库
Files
=====
       路径名必须指向 spufs 挂载点之下的位置。按照惯例，它被挂载在 /spu 下。

Conforming to
=============
       此调用是特定于 Linux 的，并且仅由 ppc64 架构实现。使用此系统调用的程序不具备可移植性。

Bugs
====
       代码尚未完全实现此处列出的所有功能。

Author
======
       Arnd Bergmann <arndb@de.ibm.com>

See Also
========
       capabilities(7), close(2), spu_run(2), spufs(7)
