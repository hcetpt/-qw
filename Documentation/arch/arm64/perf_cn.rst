SPDX 许可证标识符: GPL-2.0

.. _perf_index:

====
Perf
====

Perf 事件属性
=====================

:作者: Andrew Murray <andrew.murray@arm.com>
:日期: 2019-03-06

exclude_user
------------

此属性排除用户空间
用户空间总是在 EL0 上运行，因此此属性将排除 EL0。

exclude_kernel
--------------

此属性排除内核
内核在带有 VHE 的 EL2 和没有 VHE 的 EL1 上运行。来宾内核始终在 EL1 上运行。
对于主机，此属性将排除 EL1，并且如果系统具有 VHE，则还会排除 EL2。
对于来宾，此属性将排除 EL1。请注意，EL2 在来宾内部永远不会被计算在内。

exclude_hv
----------

此属性排除虚拟机监视器（Hypervisor）
对于 VHE 主机，此属性被忽略，因为我们认为主机内核就是虚拟机监视器。
对于非 VHE 主机，此属性会排除 EL2，因为我们认为虚拟机监视器是任何在 EL2 运行的代码，这主要用于来宾/主机之间的转换。
对于来宾，此属性没有效果。请注意，EL2 在来宾内部永远不会被计算在内。
这些属性分别排除 KVM 主机和客户机。
KVM 主机可能在 EL0（用户空间）、EL1（非 VHE 内核）以及 EL2（VHE
内核或非 VHE 虚拟机监视器）上运行。
KVM 客户机可能在 EL0（用户空间）和 EL1（内核）上运行。
由于主机和客户机之间异常级别的重叠，我们不能完全依赖 PMU 的硬件异常过滤 —— 因此我们必须在进入和退出客户机时启用/禁用计数。这在 VHE 和非 VHE 系统上执行的方式不同。
对于非 VHE 系统，我们在 exclude_host 时排除 EL2 —— 在进入和退出客户机时，我们会根据 exclude_host 和 exclude_guest 属性适当地禁用/启用事件。
对于 VHE 系统，我们在 exclude_guest 时排除 EL1，并且在 exclude_host 时排除 EL0 和 EL2。在进入和退出客户机时，我们会根据 exclude_host 和 exclude_guest 属性修改事件以适当地包含/排除 EL0。
上述声明同样适用于在非 VHE 客户机中使用这些属性的情况；然而请注意，在客户机内部 EL2 永远不会被计数。

准确性
-------
在非 VHE 主机上，我们在 EL2 上的主机/客户机转换的入口/出口处启用/禁用计数器 —— 但是在这之间有一段时间间隔：即在启用/禁用计数器与进入/退出客户机之间。我们能够通过为 exclude_host 排除 EL2 来消除在计算客户机事件时边界上的主机事件被计数的情况。然而当使用 !exclude_hv 时，在进入/退出客户机时会有一个短暂的盲区窗口，其中主机事件没有被捕获。
在 VHE 系统上，没有盲区窗口。

Perf 用户空间 PMU 硬件计数器访问
=============================

概述
-----
Perf 用户空间工具依赖于 PMU 来监控事件。它为硬件计数器提供了一层抽象，因为底层实现取决于 CPU。
Arm64允许用户空间工具直接访问存储硬件计数器值的寄存器。
这特别针对自我监控任务，以通过直接访问寄存器而非通过内核来减少开销。
如何操作
--------
关注点在于armv8的PMUv3，它确保了对pmu寄存器的访问被启用，并且用户空间可以访问相关的信息以便使用它们。
为了能够访问硬件计数器，必须首先全局启用sysctl kernel/perf_user_access：

.. code-block:: sh

  echo 1 > /proc/sys/kernel/perf_user_access

要使用perf工具接口打开事件，需要设置config1:1属性位：sys_perf_event_open系统调用将返回一个文件描述符(fd)，随后可以使用mmap系统调用来获取包含有关事件信息的内存页。PMU驱动程序使用这个页面向用户暴露硬件计数器的索引和其他必要数据。通过这个索引，用户可以使用`mrs`指令访问PMU寄存器。
只有在序列锁不变的情况下，对PMU寄存器的访问才是有效的。
特别是，每当序列锁改变时，PMSELR_EL0寄存器都会被清零。
用户空间访问在libperf中通过perf_evsel__mmap()和perf_evsel__read()函数得到支持。参见`tools/lib/perf/tests/test-evsel.c`中的示例。
关于异构系统
--------------
在像big.LITTLE这样的异构系统上，只有当任务被固定到同构核心子集上，并且通过指定"type"属性打开相应的PMU实例时，才能启用用户空间的PMU计数器访问。
在这种情况下不支持通用事件类型的使用。
请参阅`tools/perf/arch/arm64/tests/user-events.c`中的示例。可以使用perf工具运行它，以检查从用户空间正确访问寄存器的功能：

.. code-block:: sh

  perf test -v user

关于链式事件与计数器大小
-----------------------------
用户可以请求32位(config1:0 == 0)或64位(config1:0 == 1)的计数器以及用户空间访问权限。如果请求64位计数器而硬件不支持64位计数器，则sys_perf_event_open系统调用将会失败。不支持链式事件与用户空间计数器访问结合使用。如果在具有64位计数器的硬件上请求32位计数器，那么用户空间必须将从计数器读取的高32位视为未知。用户页中的'pmc_width'字段将指示计数器的有效宽度，并应根据需要用于屏蔽高位。
事件计数阈值
==========================================

概述
--------

FEAT_PMUv3_TH（Armv8.8）允许PMU计数器仅在事件计数满足指定的阈值条件时递增。例如，如果将`threshold_compare`设置为2（“大于等于”），并且将阈值设置为2，则PMU计数器现在仅在单个处理器周期中某个事件会使PMU计数器增加2或更多时才递增。
要在通过阈值条件后递增1而不是该周期上事件的数量，请在命令行中添加`threshold_count`选项。

如何操作
------

以下是用于控制此功能的参数：

.. list-table::
   :header-rows: 1

   * - 参数
     - 描述
   * - threshold
     - 事件的阈值。值为0表示禁用阈值，并且其他参数无效。
   * - threshold_compare
     - 使用的比较函数，支持以下值：
       |
       | 0: 不等于
       | 1: 等于
       | 2: 大于等于
       | 3: 小于
   * - threshold_count
     - 如果设置了此选项，在通过阈值条件后递增1，而不是本周期事件的值。
阈值、threshold_compare和threshold_count的值可以针对每个事件提供，例如：

.. code-block:: sh

  perf stat -e stall_slot/threshold=2,threshold_compare=2/ \
            -e dtlb_walk/threshold=10,threshold_compare=3,threshold_count/

在这个例子中，stall_slot事件将在每个周期中发生2个或更多的停顿时按2或更多递增。而dtlb_walk将在每个周期中dtlb走查次数少于10时递增1。
支持的最大阈值可以通过读取每个PMU的caps获得，例如：

.. code-block:: sh

  cat /sys/bus/event_source/devices/armv8_pmuv3/caps/threshold_max

  0x000000ff

如果给定的值高于这个值，则打开事件会导致错误。最高可能的最大值是4095，因为阈值配置字段限制为12位，并且Perf工具会拒绝解析更高的值。
如果不支持FEAT_PMUv3_TH，那么threshold_max将读取为0，并且尝试设置阈值也会导致错误。即使主机运行在具有该特性的硬件上，aarch32客人机上的threshold_max也会读取为0。
