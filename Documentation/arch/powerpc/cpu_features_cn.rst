=============  
CPU特性
=============

霍利斯·布兰查德 <hollis@austin.ibm.com>
2002年6月5日

本文档描述了PPC Linux内核中使用的一种系统（包括自修改代码），该系统支持各种PowerPC CPU，而无需在编译时进行选择。
在启动过程的早期阶段，ppc32内核会检测当前的CPU类型，并相应地选择一组特性。一些示例包括Altivec支持、指令和数据缓存分离以及CPU是否支持DOZE和NAP睡眠模式。
特征集的检测很简单。可以在arch/powerpc/kernel/cputable.c中找到处理器列表。PVR寄存器被屏蔽并与列表中的每个值进行比较。如果找到匹配项，则将cur_cpu_spec的cpu_features赋给该处理器的特征位掩码，并调用一个__setup_cpu函数。
C代码可以通过测试'cur_cpu_spec[smp_processor_id()]->cpu_features'来检查特定的特征位。在很多地方都会这样做，例如在ppc_setup_l2cr()中。
在汇编语言中实现cpufeatures稍微复杂一些。有几个路径对性能至关重要，如果添加数组索引、结构间接引用和条件分支，它们的性能会受到影响。为了避免性能损失但仍允许运行时（而非编译时）选择CPU，未使用的代码被替换为'nop'指令。这种nop替换基于CPU 0的能力，因此一个多处理器系统如果有非相同的处理器则无法工作（但这样的系统可能本来就存在其他问题）。
在检测到处理器类型后，内核通过写入nop覆盖不应使用的代码段。使用cpufeatures只需要2个宏（在arch/powerpc/include/asm/cputable.h中定义），如head.S所示：
转移至处理程序::

	#ifdef CONFIG_ALTIVEC
	BEGIN_FTR_SECTION
		mfspr	r22,SPRN_VRSAVE		/* 如果是G4，保存vrsave寄存器的值 */
		stw	r22,THREAD_VRSAVE(r23)
	END_FTR_SECTION_IFSET(CPU_FTR_ALTIVEC)
	#endif /* CONFIG_ALTIVEC */

如果CPU 0支持Altivec，那么代码保持不变。如果不支持，则两个指令都被替换为nop。
END_FTR_SECTION宏有两种更简单的变体：END_FTR_SECTION_IFSET和END_FTR_SECTION_IFCLR。它们分别用于测试标志是否设置（在cur_cpu_spec[0]->cpu_features中）或清除。这两种宏应该在大多数情况下使用。
END_FTR_SECTION宏的实现方式是在'__ftr_fixup' ELF部分存储有关此代码的信息。当do_cpu_ftr_fixups（arch/powerpc/kernel/misc.S）被调用时，它将遍历__ftr_fixup中的记录，并且如果所需的特性不存在，则从每个BEGIN_FTR_SECTION到END_FTR_SECTION循环写入nop。
