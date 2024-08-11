### SPDX 许可证标识符: GPL-2.0
### 版权所有 (C) 2023, Google LLC

#### 内核地址检查器 (KASAN)

##### 概述

内核地址检查器 (KASAN) 是一个动态内存安全错误检测器，旨在发现越界访问和释放后使用等类型的错误。
KASAN 包含三种模式：

1. 通用 KASAN
2. 软件标签型 KASAN
3. 硬件标签型 KASAN

**通用 KASAN**，通过配置 `CONFIG_KASAN_GENERIC` 启用，适用于调试，类似于用户空间的 ASan。此模式支持多种 CPU 架构，但存在显著的性能和内存开销。

**软件标签型 KASAN**（简称 SW_TAGS KASAN），通过配置 `CONFIG_KASAN_SW_TAGS` 启用，既可用于调试也可用于狗粮测试，类似于用户空间的 HWASan。此模式仅支持 arm64 架构，适度的内存开销使其适用于内存受限设备的真实工作负载测试。

**硬件标签型 KASAN**（简称 HW_TAGS KASAN），通过配置 `CONFIG_KASAN_HW_TAGS` 启用，适用于现场内存错误检测或作为安全缓解措施。此模式仅在支持 MTE（内存标记扩展）的 arm64 CPU 上可用，具有较低的内存和性能开销，因此可以在生产环境中使用。

有关每种 KASAN 模式的内存和性能影响的详细信息，请参阅相应的 Kconfig 选项描述。

通常将 **通用 KASAN** 和 **软件标签型 KASAN** 称为软件模式；而将 **软件标签型 KASAN** 和 **硬件标签型 KASAN** 称为基于标签的模式。

##### 支持

**架构**

- 通用 KASAN 支持 x86_64、arm、arm64、powerpc、riscv、s390、xtensa 和 loongarch 架构；
- 基于标签的 KASAN 模式仅支持 arm64 架构。

**编译器**

软件 KASAN 模式利用编译时插桩来在每次内存访问前插入有效性检查，因此需要编译器版本提供相应支持。硬件标签型模式依赖硬件进行这些检查，但仍需要支持内存标记指令的编译器版本。
泛型KASAN需要GCC版本8.3.0或更高版本，或者内核支持的任何Clang版本。软件标签基KASAN需要GCC 11+版本，或者内核支持的任何Clang版本。硬件标签基KASAN需要GCC 10+版本或Clang 12+版本。

内存类型：
----------

泛型KASAN支持在所有类型的内存中找到错误，包括slab、page_alloc、vmap、vmalloc、stack和全局内存。

软件标签基KASAN支持在slab、page_alloc、vmalloc和stack类型的内存中查找错误。

硬件标签基KASAN支持在slab、page_alloc和非执行的vmalloc类型的内存中查找错误。

对于slab类型内存，两种软件KASAN模式都支持SLUB和SLAB分配器，而硬件标签基KASAN仅支持SLUB。

使用方法：
----------

要启用KASAN，请在内核配置中设置：

    CONFIG_KASAN=y

并选择`CONFIG_KASAN_GENERIC`(启用泛型KASAN)、`CONFIG_KASAN_SW_TAGS`(启用软件标签基KASAN) 或 `CONFIG_KASAN_HW_TAGS`(启用硬件标签基KASAN)。对于软件模式，还需选择`CONFIG_KASAN_OUTLINE` 和 `CONFIG_KASAN_INLINE`。这两种都是编译器插入类型，前者生成的二进制文件较小，而后者速度可能快至两倍。
为了在报告中包含受影响的内存块对象的分配和释放堆栈跟踪，请启用``CONFIG_STACKTRACE``。为了在报告中包含受影响的物理页的分配和释放堆栈跟踪，请启用``CONFIG_PAGE_OWNER``，并在启动时使用``page_owner=on``参数。

启动参数
~~~~~~~~

KASAN 受通用的``panic_on_warn``命令行参数的影响。
当启用此参数后，在打印错误报告之后，KASAN 会使内核崩溃。
默认情况下，KASAN 仅对第一次非法内存访问打印错误报告。
通过使用``kasan_multi_shot``，KASAN 将对每次非法访问打印一份报告。这实际上禁用了针对 KASAN 报告的``panic_on_warn``参数。
另外，无论``panic_on_warn``设置如何，可以通过使用``kasan.fault=``启动参数来控制崩溃和报告行为：

- ``kasan.fault=report``、``=panic``或``=panic_on_write``可以控制是仅打印 KASAN 报告、使内核崩溃还是仅在非法写入时使内核崩溃（默认：``report``）。即使启用了``kasan_multi_shot``，也会发生崩溃。需要注意的是，在异步模式下使用基于硬件标签的 KASAN 时，``kasan.fault=panic_on_write``总是会在异步检查的访问（包括读取）时引发崩溃。
软件和基于硬件标签的 KASAN 模式（请参阅下面关于各种模式的部分）支持更改堆栈跟踪收集行为：

- ``kasan.stacktrace=off``或``=on``可以禁用或启用分配和释放堆栈跟踪的收集（默认：``on``）
- ``kasan.stack_ring_size=<条目数量>``指定了堆栈环中的条目数量（默认：``32768``）
基于硬件标签的 KASAN 模式旨在用于生产环境中作为一种安全缓解措施。因此，它还支持额外的启动参数，这些参数允许完全禁用 KASAN 或控制其功能：

- ``kasan=off``或``=on``可以控制是否启用 KASAN（默认：``on``）
- ``kasan.mode=sync``、``=async``或``=asymm``可以控制 KASAN 是否配置为同步、异步或不对称执行模式（默认：``sync``）
同步模式：当发生标签检查错误时，立即检测到非法访问。
异步模式：非法访问的检测被延迟。当发生标签检查错误时，信息会被存储在硬件中（对于arm64架构，存储在TFSR_EL1寄存器中）。内核会周期性地检查硬件，并仅在这类检查期间报告标签错误。
不对称模式：读取操作时非法访问被同步检测，写入操作时则被异步检测。
- `kasan.vmalloc=off` 或 `=on` 分别禁用或启用对vmalloc分配的标记（默认值：`on`）
- `kasan.page_alloc.sample=<采样间隔>` 设置每N次`page_alloc`分配进行一次标记，其中N是`sample`参数的值，且分配的顺序等于或大于`kasan.page_alloc.sample.order`指定的顺序（默认值：`1`，即对所有此类分配进行标记）
此参数旨在缓解KASAN引入的性能开销。
请注意，启用此参数会使基于硬件标签的KASAN跳过通过采样选择的分配的检查，因此可能会遗漏这些分配中的非法访问。为了准确检测bug，请使用默认值。
- `kasan.page_alloc.sample.order=<最小分配顺序>` 指定受采样影响的分配的最小顺序（默认值：`3`）
仅当`kasan.page_alloc.sample`设置为大于`1`的值时适用。
此参数旨在只允许对大型`page_alloc`分配进行采样，因为这类分配是造成性能开销的最大来源。
错误报告
~~~~~~~~~~~~~

一个典型的 KASAN 报告看起来像这样：

    ==================================================================
    BUG: KASAN: 在 kmalloc_oob_right+0xa8/0xbc [kasan_test] 中的 slab 越界
    任务 insmod/2760 在地址 ffff8801f44ec37b 进行了大小为 1 的写入

    CPU: 1 PID: 2760 Comm: insmod 未被污染 4.19.0-rc3+ #698
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.10.2-1 04/01/2014
    调用追踪：
     dump_stack+0x94/0xd8
     print_address_description+0x73/0x280
     kasan_report+0x144/0x187
     __asan_report_store1_noabort+0x17/0x20
     kmalloc_oob_right+0xa8/0xbc [kasan_test]
     kmalloc_tests_init+0x16/0x700 [kasan_test]
     do_one_initcall+0xa5/0x3ae
     do_init_module+0x1b6/0x547
     load_module+0x75df/0x8070
     __do_sys_init_module+0x1c6/0x200
     __x64_sys_init_module+0x6e/0xb0
     do_syscall_64+0x9f/0x2c0
     entry_SYSCALL_64_after_hwframe+0x44/0xa9
    RIP: 0033:0x7f96443109da
    RSP: 002b:00007ffcf0b51b08 EFLAGS: 00000202 ORIG_RAX: 00000000000000af
    RAX: ffffffffffffffda RBX: 000055dc3ee521a0 RCX: 00007f96443109da
    RDX: 00007f96445cff88 RSI: 0000000000057a50 RDI: 00007f9644992000
    RBP: 000055dc3ee510b0 R08: 0000000000000003 R09: 0000000000000000
    R10: 00007f964430cd0a R11: 0000000000000202 R12: 00007f96445cff88
    R13: 000055dc3ee51090 R14: 0000000000000000 R15: 0000000000000000

    由任务 2760 分配：
     save_stack+0x43/0xd0
     kasan_kmalloc+0xa7/0xd0
     kmem_cache_alloc_trace+0xe1/0x1b0
     kmalloc_oob_right+0x56/0xbc [kasan_test]
     kmalloc_tests_init+0x16/0x700 [kasan_test]
     do_one_initcall+0xa5/0x3ae
     do_init_module+0x1b6/0x547
     load_module+0x75df/0x8070
     __do_sys_init_module+0x1c6/0x200
     __x64_sys_init_module+0x6e/0xb0
     do_syscall_64+0x9f/0x2c0
     entry_SYSCALL_64_after_hwframe+0x44/0xa9

    由任务 815 释放：
     save_stack+0x43/0xd0
     __kasan_slab_free+0x135/0x190
     kasan_slab_free+0xe/0x10
     kfree+0x93/0x1a0
     umh_complete+0x6a/0xa0
     call_usermodehelper_exec_async+0x4c3/0x640
     ret_from_fork+0x35/0x40

    错误的地址属于位于 ffff8801f44ec300 的对象
     它属于大小为 128 字节的缓存 kmalloc-128
    错误的地址位于 128 字节区域 [ffff8801f44ec300, ffff8801f44ec380) 内部 123 字节处
    错误的地址属于页面：
    page:ffffea0007d13b00 count:1 mapcount:0 mapping:ffff8801f7001640 index:0x0
    标志: 0x200000000000100(slab)
    原始: 0200000000000100 ffffea0007d11dc0 0000001a0000001a ffff8801f7001640
    原始: 0000000000000000 0000000080150015 00000001ffffffff 0000000000000000
    页面已转储，因为：KASAN 检测到非法访问

    错误地址周围的内存状态：
     ffff8801f44ec200: fc fc fc fc fc fc fc fc fb fb fb fb fb fb fb fb
     ffff8801f44ec280: fb fb fb fb fb fb fb fb fc fc fc fc fc fc fc fc
    >ffff8801f44ec300: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 03
                                                                    ^
     ffff8801f44ec380: fc fc fc fc fc fc fc fc fb fb fb fb fb fb fb fb
     ffff8801f44ec400: fb fb fb fb fb fb fb fb fc fc fc fc fc fc fc fc
    ==================================================================

报告标题总结了发生了什么类型的错误以及是什么类型的访问导致了该错误。随后是错误访问的堆栈跟踪、被访问内存被分配的位置的堆栈跟踪（如果访问的是 slab 对象），以及对象被释放的位置的堆栈跟踪（如果是使用后释放错误报告）。接下来是被访问的 slab 对象的描述和有关被访问内存页面的信息。
最后，报告显示了被访问地址周围的内存状态。
内部地，KASAN 为每个内存粒度单独跟踪内存状态，这可能是 8 或 16 字节对齐，取决于 KASAN 模式。报告中内存状态部分的每个数字都表示一个围绕被访问地址的内存粒度的状态。
对于通用 KASAN，每个内存粒度的大小为 8 字节。每个粒度的状态编码在一个阴影字节中。这些 8 字节可以是可访问的、部分可访问的、已释放的或是一个红色区域的一部分。KASAN 使用以下编码方式对每个阴影字节进行编码：00 表示对应内存区域的所有 8 字节都是可访问的；数字 N (1 <= N <= 7) 表示前 N 个字节是可访问的，而其他 (8 - N) 个字节则不是；任何负值都表示整个 8 字节的词是不可访问的。KASAN 使用不同的负值来区分不同种类的不可访问内存，如红色区域或已释放的内存（参见 mm/kasan/kasan.h）。
在上面的报告中，箭头指向阴影字节 `03`，这意味着被访问的地址是部分可访问的。
对于基于标签的 KASAN 模式，此报告的最后一节显示了被访问地址周围的内存标签（参见 `实现细节`_ 部分）。
请注意，KASAN 错误标题（如“slab 越界”或“使用后释放”）是尽力而为的：KASAN 根据其有限的信息打印最可能的错误类型。实际的错误类型可能不同。
通用 KASAN 还会报告最多两个辅助调用堆栈跟踪。这些堆栈跟踪指向与对象交互但不在错误访问堆栈跟踪中的代码位置。目前，这包括 call_rcu() 和工作队列的排队操作。

CONFIG_KASAN_EXTRA_INFO
~~~~~~~~~~~~~~~~~~~~~~~

启用 CONFIG_KASAN_EXTRA_INFO 允许 KASAN 记录并报告更多信息。当前支持的额外信息包括在分配和释放时的 CPU 编号和时间戳。更多的信息可以帮助找到错误的原因，并将错误与其他系统事件关联起来，代价是使用额外的内存来记录更多信息（更多成本细节参见 CONFIG_KASAN_EXTRA_INFO 的帮助文本）。
下面是启用了 CONFIG_KASAN_EXTRA_INFO 的报告（仅显示不同的部分）：

    ==================================================================
    ..
由任务134在CPU 5上于229.133855秒分配：
    ..
由任务136在CPU 3上于230.199335秒释放：
    ..
==================================================================

实现细节
----------------------

通用KASAN
~~~~~~~~~~~~~

软件KASAN模式使用影子内存来记录每个字节的内存是否安全可访问，并使用编译时插入技术在每次内存访问前插入影子内存检查。
通用KASAN将内核内存的1/8用于其影子内存（例如，在x86_64架构中，16TB覆盖128TB），并使用直接映射和缩放及偏移来将内存地址转换为其对应的影子地址。下面是将地址转换为对应影子地址的函数：

    static inline void *kasan_mem_to_shadow(const void *addr)
    {
	return (void *)((unsigned long)addr >> KASAN_SHADOW_SCALE_SHIFT)
		+ KASAN_SHADOW_OFFSET;
    }

其中 `KASAN_SHADOW_SCALE_SHIFT = 3`
编译时插入技术用于插入内存访问检查。编译器在每次大小为1、2、4、8或16字节的内存访问前插入函数调用（`__asan_load*(addr)`、`__asan_store*(addr)`）。这些函数通过检查相应的影子内存来判断内存访问是否有效。
通过内联插入技术，而不是调用函数，编译器直接插入代码来检查影子内存。此选项显著增大了内核，但相比于轮廓插入内核，它提供了1.1到2倍的性能提升。
通用KASAN是唯一一种通过隔离（参见mm/kasan/quarantine.c中的实现）延迟释放对象重用的模式。

基于软件标签的KASAN
~~~~~~~~~~~~~~~~~~~~~~~~

基于软件标签的KASAN采用软件内存标记方法来检查访问的有效性。目前仅针对arm64架构实现了该方法。
基于软件标签的KASAN利用arm64 CPU的Top Byte Ignore (TBI)特性，在内核指针的最高字节中存储一个指针标签。它使用影子内存来存储与每个16字节内存单元关联的内存标签（因此，它将内核内存的1/16用于影子内存）。
在每次内存分配时，软件标签型KASAN生成一个随机标签，用该标签标记分配的内存，并将相同的标签嵌入返回的指针中。
软件标签型KASAN使用编译时插桩技术，在每次内存访问前插入检查。这些检查确保所访问内存的标签与用于访问该内存的指针的标签相等。如果标签不匹配，软件标签型KASAN会打印错误报告。
软件标签型KASAN还有两种插桩模式（轮廓模式，它会发出回调以检查内存访问；和内联模式，它执行影子内存检查）。在轮廓插桩模式下，从执行访问检查的函数中打印错误报告。在内联插桩模式下，编译器发出`brk`指令，并使用专用的`brk`处理程序来打印错误报告。
软件标签型KASAN使用0xFF作为全匹配指针标签（通过具有0xFF指针标签的指针进行的访问不会被检查）。目前值0xFE被保留用于标记已释放的内存区域。

硬件标签型KASAN
~~~~~~~~~~~~~~~~~~~~~~~~

硬件标签型KASAN在概念上与软件模式类似，但它使用硬件内存标记支持而非编译器插桩技术和影子内存。
硬件标签型KASAN当前仅针对arm64架构实现，并基于ARMv8.5指令集架构引入的arm64内存标记扩展(MTE)和Top Byte Ignore(TBI)。
特殊的arm64指令用于为每次分配指定内存标签
相同的标签也会赋予指向这些分配的指针。在每次内存访问时，硬件确保所访问内存的标签等于用于访问该内存的指针的标签。如果标签不匹配，则会产生故障并打印报告。
硬件标签型KASAN使用0xFF作为全匹配指针标签（通过具有0xFF指针标签的指针进行的访问不会被检查）。目前值0xFE被保留用于标记已释放的内存区域。
如果硬件不支持MTE（早于ARMv8.5），则不会启用硬件标签型KASAN。在这种情况下，所有KASAN引导参数都将被忽略。
请注意，启用 `CONFIG_KASAN_HW_TAGS` 总会导致内核中的 TBI 被启用。即使提供了 `kasan.mode=off` 或者硬件不支持 MTE（但支持 TBI）时也是如此。
基于硬件标签的 KASAN 只报告首次发现的错误。之后，MTE 标签检查会被禁用。

### 阴影内存

本节内容仅适用于软件 KASAN 模式。

内核在地址空间的多个不同部分映射内存。
内核虚拟地址范围很大：没有足够的物理内存来为内核可能访问的每个地址支持一个真实的阴影区域。因此，KASAN 仅对地址空间的某些部分映射真实的阴影。

#### 默认行为

默认情况下，架构只在直线映射（以及可能的其他小区域）上为阴影区域映射真实内存。对于所有其他区域——例如 `vmalloc` 和 `vmemmap` 空间——一个只读页面映射到阴影区域上。这个只读的阴影页面声明所有内存访问都是允许的。

这给模块带来了一个问题：它们不在直线映射中，而是在一个专用的模块空间中。通过挂钩到模块分配器，KASAN 临时地将真实的阴影内存映射到覆盖它们的位置。

这允许检测对模块全局变量的无效访问等。

这也导致了与 `VMAP_STACK` 的不兼容性：如果栈位于 `vmalloc` 空间中，它将被只读页面所遮蔽，当尝试为栈变量设置阴影数据时，内核会发生故障。

#### CONFIG_KASAN_VMALLOC

使用 `CONFIG_KASAN_VMALLOC`，KASAN 可以覆盖 `vmalloc` 空间，代价是更大的内存使用量。目前，x86、arm64、riscv、s390 和 powerpc 支持这一配置。
这是通过接入`vmalloc`和`vmap`实现的，并动态分配真实的影子内存来支持这些映射。
大多数`vmalloc`空间中的映射都很小，通常不需要完整的影子页。因此，为每个映射分配一个完整的影子页将是浪费的。此外，为了确保不同的映射使用不同的影子页，映射必须对齐到`KASAN_GRANULE_SIZE * PAGE_SIZE`。

相反，KASAN在多个映射之间共享支持空间。当`vmalloc`空间中的映射使用影子区域的特定页时，KASAN会分配一个支持页。此页可以被之后的其他`vmalloc`映射共享。
KASAN接入`vmap`基础设施，以便懒惰地清理未使用的影子内存。
为了避免与交换映射相关的困难，KASAN期望覆盖`vmalloc`空间的影子区域部分不会被早期的影子页覆盖，而是保持未映射状态。
这将需要对架构特定代码进行更改。
这允许x86上的`VMAP_STACK`支持，并可简化没有固定模块区域的架构的支持。
对于开发者
--------------

忽略访问
~~~~~~~~~~

软件KASAN模式使用编译器插桩来插入有效性检查。
此类插桩可能与内核的某些部分不兼容，因此需要禁用。
内核的其他部分可能会访问已分配对象的元数据。
通常情况下，KASAN能够检测并报告此类访问行为，但在某些情况下（例如，在内存分配器中），这些访问是合法的。

对于软件KASAN模式，若要为特定文件或目录禁用编译器插入（instrumentation），请在相应的内核Makefile中添加`KASAN_SANITIZE`注释：

- 对于单个文件（例如，main.o）：

```make
KASAN_SANITIZE_main.o := n
```

- 对于一个目录中的所有文件：

```make
KASAN_SANITIZE := n
```

对于软件KASAN模式，若要在函数级别禁用编译器插入，可以使用KASAN特有的`__no_sanitize_address`函数属性或通用的`noinstr`属性。
请注意，无论是在文件级别还是函数级别禁用编译器插入都会使KASAN忽略直接发生在该代码中的访问行为。但这对间接发生的访问行为（通过调用已插入的函数）或硬件标签型KASAN不起作用，因为后者不依赖于编译器插入。

对于软件KASAN模式，若要在当前任务的部分内核代码中禁用KASAN报告，请使用`kasan_disable_current()`和`kasan_enable_current()`将这部分代码括起来。这同样会禁用通过函数调用产生的间接访问的报告。

对于基于标签的KASAN模式，若要禁用访问检查，请使用`kasan_reset_tag()`或`page_kasan_tag_reset()`。请注意，通过`page_kasan_tag_reset()`临时禁用访问检查需要保存和恢复每页的KASAN标签，这可以通过`page_kasan_tag`和`page_kasan_tag_set`实现。

测试
~~~~~

存在KASAN测试用于验证KASAN是否能正常工作以及能否检测到某些类型的内存损坏。这些测试包含两个部分：

1. 与KUnit测试框架集成的测试。启用`CONFIG_KASAN_KUNIT_TEST`。这些测试可以通过多种方式自动运行和部分验证；请参阅下面的说明。
2. 当前与KUnit不兼容的测试。启用`CONFIG_KASAN_MODULE_TEST`，只能作为模块运行。这些测试只能手动验证，即加载内核模块并检查内核日志中的KASAN报告。

每个与KUnit兼容的KASAN测试如果检测到错误则会打印一种或多类KASAN报告。然后，测试会打印其编号和状态。

当测试通过时：
```
ok 28 - kmalloc_double_kzfree
```

当测试因`kmalloc`失败而失败时：
```
# kmalloc_large_oob_right: ASSERTION FAILED at mm/kasan/kasan_test.c:245
Expected ptr is not null, but is
not ok 5 - kmalloc_large_oob_right
```

当测试因缺少KASAN报告而失败时：
```
# kmalloc_double_kzfree: EXPECTATION FAILED at mm/kasan/kasan_test.c:709
KASAN failure expected in "kfree_sensitive(ptr)", but none occurred
not ok 28 - kmalloc_double_kzfree
```

最后，会打印所有KASAN测试的累积状态。如果全部成功：
```
ok 1 - kasan
```

如果其中一项测试失败：
```
not ok 1 - kasan
```

有几种方式可以运行与KUnit兼容的KASAN测试
1. 可加载模块

   启用`CONFIG_KUNIT`后，KASAN-KUnit测试可以构建为可加载模块，并通过使用`insmod`或`modprobe`加载`kasan_test.ko`来运行。
2. 内置

   当`CONFIG_KUNIT`被设置为内置时，KASAN-KUnit 测试也可以被设置为内置。
   在这种情况下，测试将在启动时作为延迟初始化调用运行。
3. 使用 kunit_tool

   当`CONFIG_KUNIT`和`CONFIG_KASAN_KUNIT_TEST`被设置为内置时，还可以使用`kunit_tool`以更易读的方式查看 KUnit 测试结果。这不会打印通过测试的 KASAN 报告。
   有关`kunit_tool`的更多最新信息，请参阅[KUnit 文档](https://www.kernel.org/doc/html/latest/dev-tools/kunit/index.html)。
   
.. _KUnit: https://www.kernel.org/doc/html/latest/dev-tools/kunit/index.html
