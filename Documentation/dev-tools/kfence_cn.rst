### SPDX 许可证标识符：GPL-2.0
### 版权所有 (C) 2020，Google LLC

#### 内核 Electric-Fence（KFENCE）
==================================

内核 Electric-Fence（KFENCE）是一种低开销的基于采样的内存安全错误检测器。KFENCE 能够检测堆越界访问、释放后使用以及无效释放等错误。
KFENCE 被设计用于在生产环境中启用，并且具有接近零的性能开销。与 KASAN 相比，KFENCE 在性能和精度之间做了权衡。KFENCE 设计的主要动机是，在足够长的总运行时间内，KFENCE 能够检测到通常不被非生产性测试负载覆盖的代码路径中的错误。当该工具部署到大量机器上时，可以快速达到足够的总运行时间。

##### 使用方法
------------------

要启用 KFENCE，请配置内核如下：

    CONFIG_KFENCE=y

要构建带有 KFENCE 支持但默认禁用的内核（要启用，请将 `kfence.sample_interval` 设置为非零值），请配置内核如下：

    CONFIG_KFENCE=y
    CONFIG_KFENCE_SAMPLE_INTERVAL=0

KFENCE 提供了其他几个配置选项来定制其行为（有关详细信息，请参阅 `lib/Kconfig.kfence` 中的相关帮助文本）。

##### 性能调优
-------------------

最重要的参数是 KFENCE 的采样间隔，可以通过内核启动参数 `kfence.sample_interval`（以毫秒为单位）进行设置。采样间隔决定了堆分配多长时间被 KFENCE 守护一次。默认值可以通过 Kconfig 选项 `CONFIG_KFENCE_SAMPLE_INTERVAL` 进行配置。设置 `kfence.sample_interval=0` 可以禁用 KFENCE。

采样间隔控制了一个定时器，该定时器设置 KFENCE 分配。默认情况下，为了保持实际采样间隔的可预测性，常规定时器还会在系统完全空闲时导致 CPU 唤醒。这在电力受限的系统上可能是不希望发生的。启动参数 `kfence.deferrable=1` 则会切换到一个“可延迟”定时器，该定时器不会强迫空闲系统的 CPU 唤醒，但可能导致不可预测的采样间隔。这个默认值可以通过 Kconfig 选项 `CONFIG_KFENCE_DEFERRABLE` 进行配置。

**警告：**
   当使用可延迟定时器时，KUnit 测试套件很可能失败，因为目前它会导致非常不可预测的采样间隔。

KFENCE 的内存池大小是固定的，如果内存池耗尽，则不再发生进一步的 KFENCE 分配。通过 `CONFIG_KFENCE_NUM_OBJECTS`（默认值为 255），可以控制可用的受保护对象的数量。每个对象需要 2 页内存，一页用于对象本身，另一页作为保护页；对象页与保护页交错排列，因此每个对象页都被两个保护页包围。

KFENCE 内存池的总内存可以计算为：

    ( 对象数量 + 1 ) * 2 * PAGE_SIZE

使用默认配置，并假设页面大小为 4 KiB，结果是为 KFENCE 内存池分配了 2 MiB 的内存。

注意：在支持大页的架构上，KFENCE 将确保内存池使用 `PAGE_SIZE` 大小的页。这将导致额外的页表被分配。
错误报告
~~~~~~~~~~~~~

典型的越界访问看起来像这样：

    ==================================================================
    BUG: KFENCE: 在 test_out_of_bounds_read+0xa6/0x234 中检测到越界读取

    在 0xffff8c3f2e291fff 处检测到越界读取（距 kfence-#72 左侧 1B）:
     test_out_of_bounds_read+0xa6/0x234
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    kfence-#72: 0xffff8c3f2e292000-0xffff8c3f2e29201f，大小=32，缓存=kmalloc-32

    由任务 484 在 CPU 0 上于 32.919330s 分配：
     test_alloc+0xfe/0x738
     test_out_of_bounds_read+0x9b/0x234
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    CPU: 0 PID: 484 Comm: kunit_try_catch 未被篡改 5.13.0-rc3+ #7
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.14.0-2 04/01/2014
    ==================================================================

报告的头部提供了一个涉及访问的函数的简短概述。之后是关于访问及其来源的更详细信息。请注意，只有在使用内核命令行选项 `no_hash_pointers` 时才显示真实的内核地址。
使用后的自由访问报告如下：

    ==================================================================
    BUG: KFENCE: 在 test_use_after_free_read+0xb3/0x143 中检测到使用后的自由读取

    在 0xffff8c3f2e2a0000 处检测到使用后的自由读取（位于 kfence-#79 内）:
     test_use_after_free_read+0xb3/0x143
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    kfence-#79: 0xffff8c3f2e2a0000-0xffff8c3f2e2a001f，大小=32，缓存=kmalloc-32

    由任务 488 在 CPU 2 上于 33.871326s 分配：
     test_alloc+0xfe/0x738
     test_use_after_free_read+0x76/0x143
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    由任务 488 在 CPU 2 上于 33.871358s 释放：
     test_use_after_free_read+0xa8/0x143
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    CPU: 2 PID: 488 Comm: kunit_try_catch 篡改: G    B             5.13.0-rc3+ #7
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.14.0-2 04/01/2014
    ==================================================================

KFENCE 还报告无效的释放操作，如双释放：

    ==================================================================
    BUG: KFENCE: 在 test_double_free+0xdc/0x171 中检测到无效释放

    在 0xffff8c3f2e2a4000 处检测到无效释放（位于 kfence-#81 内）:
     test_double_free+0xdc/0x171
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    kfence-#81: 0xffff8c3f2e2a4000-0xffff8c3f2e2a401f，大小=32，缓存=kmalloc-32

    由任务 490 在 CPU 1 上于 34.175321s 分配：
     test_alloc+0xfe/0x738
     test_double_free+0x76/0x171
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    由任务 490 在 CPU 1 上于 34.175348s 释放：
     test_double_free+0xa8/0x171
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    CPU: 1 PID: 490 Comm: kunit_try_catch 篡改: G    B             5.13.0-rc3+ #7
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.14.0-2 04/01/2014
    ==================================================================

KFENCE 还在对象保护页的另一侧使用基于模式的红色区域来检测对象未受保护一侧的越界写入。这些情况在释放时会被报告：

    ==================================================================
    BUG: KFENCE: 在 test_kmalloc_aligned_oob_write+0xef/0x184 中检测到内存损坏

    在 0xffff8c3f2e33aff9 处检测到损坏的内存 [ 0xac . . . . . . ] （位于 kfence-#156 内）:
     test_kmalloc_aligned_oob_write+0xef/0x184
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    kfence-#156: 0xffff8c3f2e33afb0-0xffff8c3f2e33aff8，大小=73，缓存=kmalloc-96

    由任务 502 在 CPU 7 上于 42.159302s 分配：
     test_alloc+0xfe/0x738
     test_kmalloc_aligned_oob_write+0x57/0x184
     kunit_try_run_case+0x61/0xa0
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x176/0x1b0
     ret_from_fork+0x22/0x30

    CPU: 7 PID: 502 Comm: kunit_try_catch 篡改: G    B             5.13.0-rc3+ #7
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.14.0-2 04/01/2014
    ==================================================================

对于此类错误，显示了发生损坏的地址以及非法写入的字节（相对于该地址的偏移量）；在此表示中，“.” 表示未受影响的字节。在上面的例子中，“0xac”是在偏移量为0的位置写入的非法地址的值，而其余的“.” 表示没有后续字节被触及。请注意，只有当内核启动时使用 `no_hash_pointers` 时才显示实际值；为了避免信息泄露，否则使用“!” 来表示非法写入的字节。
最后，KFENCE 还可能报告对任何受保护页面的非法访问，其中无法确定关联的对象，例如，如果相邻的对象页尚未分配：

    ==================================================================
    BUG: KFENCE: 在 test_invalid_access+0x26/0xe0 中检测到非法读取

    在 0xffffffffb670b00a 处检测到非法读取：
     test_invalid_access+0x26/0xe0
     kunit_try_run_case+0x51/0x85
     kunit_generic_run_threadfn_adapter+0x16/0x30
     kthread+0x137/0x160
     ret_from_fork+0x22/0x30

    CPU: 4 PID: 124 Comm: kunit_try_catch 篡改: G        W         5.8.0-rc6+ #7
    硬件名称: QEMU 标准 PC (i440FX + PIIX, 1996)，BIOS 1.13.0-1 04/01/2014
    ==================================================================

DebugFS 接口
~~~~~~~~~~~~~

一些调试信息通过 debugfs 提供：

* 文件 `/sys/kernel/debug/kfence/stats` 提供运行时统计信息
* 文件 `/sys/kernel/debug/kfence/objects` 提供通过 KFENCE 分配的对象列表，包括已经释放但受保护的对象
实现细节
----------------------

根据采样间隔设置受保护的分配。采样间隔过期后，通过主分配器（SLAB 或 SLUB）进行的下一次分配会从 KFENCE 对象池返回一个受保护的分配（支持的分配大小最大为 PAGE_SIZE）。此时，重置计时器，并且在采样间隔到期后设置下一次分配。
当使用 `CONFIG_KFENCE_STATIC_KEYS=y` 时，KFENCE 分配通过主分配器的快速路径“闸门”进行，依赖于通过静态键基础设施的静态分支。切换静态分支以将分配重定向到 KFENCE。根据采样间隔、目标工作负载和系统架构的不同，这可能比简单的动态分支表现得更好。建议进行仔细的基准测试。
每个 KFENCE 对象都位于一个专用页上，在左或右页边界处随机选择。对象页左侧和右侧的页是“保护页”，其属性被更改为受保护状态，并在任何尝试访问时导致页故障。KFENCE 拦截这些页故障，并通过报告越界访问并标记该页为可访问的方式来优雅地处理故障，从而使出错代码可以（错误地）继续执行（设置 `panic_on_warn` 以代替）。为了检测对象页内的越界写入，KFENCE 还使用了基于模式的红色区域。对于每个对象页，为所有非对象内存设置一个红色区域。对于典型的对齐方式，只需要在未受保护的一侧设置红色区域。因为 KFENCE 必须尊重缓存请求的对齐方式，所以特殊的对齐可能会导致对象两侧出现未受保护的空隙，所有这些空隙都被红色区域覆盖。
下图说明了页面布局：

    ---+-----------+-----------+-----------+-----------+-----------+---
       | xxxxxxxxx | O :       | xxxxxxxxx |       : O | xxxxxxxxx |
       | xxxxxxxxx | B :       | xxxxxxxxx |       : B | xxxxxxxxx |
       | x GUARD x | J : RED-  | x GUARD x | RED-  : J | x GUARD x |
       | xxxxxxxxx | E :  ZONE | xxxxxxxxx |  ZONE : E | xxxxxxxxx |
       | xxxxxxxxx | C :       | xxxxxxxxx |       : C | xxxxxxxxx |
       | xxxxxxxxx | T :       | xxxxxxxxx |       : T | xxxxxxxxx |
    ---+-----------+-----------+-----------+-----------+-----------+---

在释放KFENCE对象后，该对象的页面再次受到保护，并且该对象被标记为已释放。对已释放对象的任何进一步访问都会导致故障，KFENCE会报告使用后释放的访问。已释放的对象被插入到KFENCE空闲列表的尾部，这样最近最少释放的对象将首先被重用，从而增加了检测最近释放的对象使用后释放的可能性。
如果池的利用率达到了75%（默认值）或以上，为了减少池最终完全被已分配对象占据的风险并确保分配的多样性覆盖，KFENCE限制相同来源的当前覆盖分配进一步填充池。一个分配的“来源”基于其部分分配堆栈跟踪。一个副作用是这也限制了相同来源的频繁长期分配（例如，页缓存）永久填充池，这是池变得满载和采样分配率降至零的最常见风险。开始限制当前覆盖分配的阈值可以通过引导参数`kfence.skip_covered_thresh`（池使用率%）进行配置。
接口
------

以下是描述由分配器以及页处理代码用于设置和处理KFENCE分配的函数：
.. kernel-doc:: include/linux/kfence.h
   :functions: is_kfence_address
               kfence_shutdown_cache
               kfence_alloc kfence_free __kfence_free
               kfence_ksize kfence_object_start
               kfence_handle_page_fault

相关工具
------------

在用户空间中，`GWP-ASan <http://llvm.org/docs/GwpAsan.html>`_采用了类似的方法。GWP-ASan同样依赖于保护页和采样策略来大规模检测内存不安全性错误。KFENCE的设计直接受到了GWP-ASan的影响，可以看作是其内核版本。另一种类似的但非采样的方法，同时也启发了“KFENCE”这个名字，可以在用户空间的`Electric Fence Malloc Debugger <https://linux.die.net/man/3/efence>`_中找到。
在内核中，存在多种工具来调试内存访问错误，特别是KASAN能够检测KFENCE能检测的所有错误类型。虽然KASAN更加精确，依赖于编译器插桩，但这带来了性能成本。
值得注意的是，KASAN和KFENCE是互补的，它们针对不同的环境。例如，在存在测试用例或重现器的情况下，KASAN是更好的调试辅助工具：由于使用KFENCE发现错误的机会较低，因此使用KFENCE进行调试需要更多的努力。然而，在无法承受启用KASAN的大规模部署中，使用KFENCE来发现未通过测试用例或模糊测试器执行的代码路径中的错误是有益的。
