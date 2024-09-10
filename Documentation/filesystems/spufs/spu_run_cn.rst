SPDX 许可证标识符: GPL-2.0

=======
spu_run
=======

名称
====
       spu_run - 执行一个 SPU 上下文

概览
========

       ::

	    #include <sys/spu.h>

	    int spu_run(int fd, unsigned int *npc, unsigned int *event);

描述
===========
       spu_run 系统调用用于在实现 Cell Broadband Engine 架构的 PowerPC 机器上访问协同处理器单元（SPU）。它使用从 spu_create(2) 返回的 fd 来定位特定的 SPU 上下文。当上下文被调度到物理 SPU 时，它将从传递给 npc 的指令指针开始执行。

SPU 代码的执行是同步进行的，这意味着在 SPU 仍在运行时，spu_run 不会返回。如果需要与主 CPU 或其他 SPU 上的其他代码并行执行 SPU 代码，则需要先创建一个新的执行线程，例如使用 pthread_create(3) 调用。

当 spu_run 返回时，当前 SPU 指令指针的值会被写回到 npc，因此您可以再次调用 spu_run 而无需更新指针。

event 可以是一个 NULL 指针或指向一个在 spu_run 返回时被填充的扩展状态码。它可以是以下常量之一：

       SPE_EVENT_DMA_ALIGNMENT
              DMA 对齐错误

       SPE_EVENT_SPE_DATA_SEGMENT
              DMA 分段错误

       SPE_EVENT_SPE_DATA_STORAGE
              DMA 存储错误

       如果将 NULL 作为 event 参数传递，则这些错误会导致向调用进程发送信号。

返回值
============
       spu_run 返回 spu_status 寄存器的值或 -1 表示错误，并将 errno 设置为以下错误代码之一。spu_status 寄存器值包含一个状态码位掩码和一个可选的来自 SPU 停止和信号指令的 14 位代码。状态码的位掩码如下：

       0x02
	      SPU 被停止和信号指令停止
0x04
	      SPU 被 halt 停止
0x08
	      SPU 正在等待一个通道
0x10
	      SPU 处于单步模式
0x20
	      SPU 尝试执行一条无效指令
0x40  
	SPU 尝试访问一个无效的通道

0x3fff0000  
	与该值进行位掩码操作后的结果包含从停止-信号(stop-and-signal)返回的代码

在运行 `spu_run` 时，总是会设置最低八位中的一个或多个位，或者返回错误代码

错误
======
	EAGAIN 或 EWOULDBLOCK  
		fd 处于非阻塞模式，并且 `spu_run` 会阻塞

	EBADF  
		fd 不是一个有效的文件描述符

	EFAULT  
		npc 不是一个有效的指针，或者 status 既不是 NULL 也不是一个有效的指针

	EINTR  
		在 `spu_run` 进行过程中发生了一个信号。如果必要的话，npc 值已更新为新的程序计数器值

	EINVAL  
		fd 不是通过 `spu_create(2)` 返回的文件描述符

	ENOMEM  
		没有足够的内存来处理由 MFC 直接内存访问导致的缺页故障结果

	ENOSYS  
		当前系统不提供此功能，因为硬件不支持 SPU 或者 spufs 模块未加载
笔记
=====
   spu_run 旨在被那些实现更抽象SPU接口的库所使用，而不是被常规应用程序直接使用。
   请参见 http://www.bsc.es/projects/deepcomputing/linuxoncell/ 获取推荐的库。

遵循规范
=============
   此调用是Linux特有的，并且仅由ppc64架构实现。使用此系统调用的程序不具备可移植性。

问题
====
   代码尚未完全实现此处列出的所有功能。

作者
======
   Arnd Bergmann <arndb@de.ibm.com>

参见
========
   capabilities(7), close(2), spu_create(2), spufs(7)
