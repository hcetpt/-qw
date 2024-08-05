======================
ARM Linux 内核内存布局
======================

		Russell King <rmk@arm.linux.org.uk>

			2005年11月17日 (2.6.15版本)

本文档描述了Linux内核为ARM处理器所使用的虚拟内存布局。它指出了哪些区域可供平台使用，哪些区域被通用代码使用。
ARM CPU能够寻址的最大虚拟内存空间为4GB，并且这个空间必须在用户空间进程、内核和硬件设备之间共享。
随着ARM架构的成熟，有必要预留某些虚拟内存区域以供新功能使用；因此，随着时间的推移，本文档可能会预留更多的虚拟内存空间。
============= ============= ===================================================
起始地址	结束地址	用途
============= ============= ===================================================
ffff8000	ffffffff	用于 copy_user_page 和 clear_user_page
对于SA11xx和Xscale，这用于
				设置一个小型缓存映射
ffff4000	ffffffff	ARMv6及以后版本CPU上的缓存别名
ffff1000	ffff7fff	保留
平台不得使用此地址范围
ffff0000	ffff0fff	CPU向量页
如果CPU支持向量重定位（控制寄存器V位）
				CPU向量将映射在这里。

fffe0000	fffeffff	Xscale缓存刷新区域。这在
				proc-xscale.S中用于刷新整个数据缓存。（Xscale没有TCM。）

fffe8000	fffeffff	具有
				安装在CPU内部的数据紧耦合存储器(DTCM)平台的DTCM映射区域。
以下是提供的英文描述翻译成中文的内容：

`fffe0000` 至 `fffe7fff`：对于内部集成了 ITCM 的平台，这部分区域用于 ITCM 的映射。

`ffc80000` 至 `feffffff`：固定映射区域。通过 `fix_to_virt()` 提供的地址将位于这个区域内。

`ffc00000` 至 `ffc7ffff`：保护区域。

`ff800000` 至 `ffbfffff`：固件提供的设备树（DT）Blob 永久、固定的只读映射。

`fee00000` 至 `feffffff`：PCI I/O 空间的映射。这部分是 vmalloc 空间内的静态映射。

`VMALLOC_START` 至 `VMALLOC_END-1`：vmalloc() / ioremap() 的空间。
由 vmalloc 或 ioremap 返回的内存将被动态放置在这个区域内。特定于机器的静态映射也位于这里，通过 iotable_init() 实现。
`VMALLOC_START` 是基于 `high_memory` 变量的值确定的，而 `VMALLOC_END` 等于 `0xff800000`。

`PAGE_OFFSET` 至 `high_memory-1`：内核直接映射的 RAM 区域。
这部分映射了平台的 RAM，并且通常以一对一的关系映射平台的所有 RAM。

`PKMAP_BASE` 至 `PAGE_OFFSET-1`：永久内核映射。
这是一种将 HIGHMEM 页面映射到内核空间的方法。
MODULES_VADDR	MODULES_END-1	内核模块空间  
				通过insmod插入的内核模块  
				使用动态映射放置在这里
TASK_SIZE	MODULES_VADDR-1	当使用KASan时的KASan影子内存  
从MODULES_VADDR到内存顶部的范围  
				在此处以每字节1位的方式进行阴影处理
00001000	TASK_SIZE-1	用户空间映射  
				每个线程的映射通过mmap()系统调用  
				放置在这里
00000000	00000fff	CPU向量页/空指针陷阱  
				不支持向量重映射的CPU将它们的向量页放在这里。  
				内核和用户空间中的NULL指针引用也通过此映射捕获
=============== =============== ===============================================

请注意，与上述区域冲突的映射可能会导致内核无法启动，或者可能在运行时导致内核（最终）崩溃。
由于未来的CPU可能会影响内核映射布局，用户程序不得访问未在其0x0001000至TASK_SIZE地址范围内映射的任何内存。如果他们希望访问这些区域，必须使用open()和mmap()自行设置映射。
