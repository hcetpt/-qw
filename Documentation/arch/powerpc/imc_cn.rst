SPDX 许可证标识符: GPL-2.0
.. _imc:

===================================
IMC（内存内收集计数器）
===================================

Anju T Sudhakar, 2019年5月10日

.. contents::
    :depth: 3


基本概述
==============

IMC（内存内收集计数器）是一种硬件监控设施，它在Nest级别（这些位于芯片上但不在核心内）、核心级别和线程级别收集大量的硬件性能事件。
Nest PMU（性能监控单元）计数器由运行在OCC（片上控制器）复杂体内的Nest IMC微代码处理。该微代码收集计数器数据并将Nest IMC计数器数据移动到内存中。
核心级和线程级的IMC PMU计数器在核心内部处理。核心级PMU计数器向我们提供每个核心的IMC计数器的数据，而线程级PMU计数器则提供每个CPU线程的IMC计数器的数据。
OPAL从IMC目录获取IMC PMU和受支持事件的信息，并通过设备树传递给内核。事件信息包含：

- 事件名称
- 事件偏移量
- 事件描述

还可能包括：

- 事件缩放比例
- 事件单位

某些PMU可能对所有受支持的事件具有共同的缩放比例和单位值。在这种情况下，这些事件的缩放比例和单位属性必须从PMU继承。
内存中的事件偏移量是计数器数据累积的位置。
IMC目录可在以下位置找到：
	https://github.com/open-power/ima-catalog

内核在设备树中的`imc-counters`设备节点发现IMC计数器信息，该节点具有兼容字段`ibm,opal-in-memory-counters`。从设备树中，内核解析PMU及其事件信息，并在内核中注册PMU及其属性。

IMC示例使用
=================

.. code-block:: sh

  # perf list
  [...]
  nest_mcs01/PM_MCS01_64B_RD_DISP_PORT01/            [Kernel PMU event]
  nest_mcs01/PM_MCS01_64B_RD_DISP_PORT23/            [Kernel PMU event]
  [...]
  core_imc/CPM_0THRD_NON_IDLE_PCYC/                  [Kernel PMU event]
  core_imc/CPM_1THRD_NON_IDLE_INST/                  [Kernel PMU event]
  [...]
  thread_imc/CPM_0THRD_NON_IDLE_PCYC/                [Kernel PMU event]
  thread_imc/CPM_1THRD_NON_IDLE_INST/                [Kernel PMU event]

要查看芯片级别的`nest_mcs0/PM_MCS_DOWN_128B_DATA_XFER_MC0/`数据：

.. code-block:: sh

  # ./perf stat -e "nest_mcs01/PM_MCS01_64B_WR_DISP_PORT01/" -a --per-socket

要查看核心0的非空闲指令：

.. code-block:: sh

  # ./perf stat -e "core_imc/CPM_NON_IDLE_INST/" -C 0 -I 1000

要查看"make"命令的非空闲周期：

.. code-block:: sh

  # ./perf stat -e "thread_imc/CPM_NON_IDLE_PCYC/" make


IMC跟踪模式
===============

POWER9支持两种IMC模式：积累模式和跟踪模式。在积累模式下，事件计数在系统内存中积累，虚拟机监视器随后定期或根据请求读取已发布的计数。在IMC跟踪模式下，64位跟踪SCOM值被初始化为事件信息。跟踪SCOM中的CPMCxSEL和CPMC_LOAD指定要监控的事件和采样持续时间。每当CPMCxSEL发生溢出时，硬件会捕获程序计数器以及事件计数，并将其写入由LDBAR指向的内存中。
LDBAR是一个每线程的64位特殊用途寄存器，其中包含指示硬件是否配置为积累模式或跟踪模式的位。
LDBAR寄存器布局
---------------------

  +-------+----------------------+
  | 0     | 启用/禁用            |
  +-------+----------------------+
  | 1     | 0: 积累模式          |
  |       +----------------------+
  |       | 1: 跟踪模式          |
  +-------+----------------------+
  | 2:3   | 保留                |
  +-------+----------------------+
  | 4-6   | PB作用域             |
  +-------+----------------------+
  | 7     | 保留                |
  +-------+----------------------+
  | 8:50  | 计数器地址           |
  +-------+----------------------+
  | 51:63 | 保留                |
  +-------+----------------------+

TRACE_IMC_SCOM位表示
---------------------------------

  +-------+------------+
  | 0:1   | SAMPSEL    |
  +-------+------------+
  | 2:33  | CPMC_LOAD  |
  +-------+------------+
  | 34:40 | CPMC1SEL   |
  +-------+------------+
  | 41:47 | CPMC2SEL   |
  +-------+------------+
  | 48:50 | BUFFERSIZE |
  +-------+------------+
  | 51:63 | 保留       |
  +-------+------------+

CPMC_LOAD包含采样持续时间。SAMPSEL和CPMCxSEL确定要计数的事件。BUFFERSIZE指示内存范围。每次溢出时，硬件捕获程序计数器以及事件计数并更新内存，并重新加载CMPC_LOAD值以供下次采样使用。IMC硬件不支持异常，因此如果内存缓冲区达到尾端，则会安静地循环。
目前，跟踪模式下监控的事件被固定为周期。

Trace IMC 示例用法
==================

.. code-block:: sh

  # perf list
  [....]
  trace_imc/trace_cycles/                            [Kernel PMU 事件]

要使用 trace-imc 事件记录一个应用程序/进程：

.. code-block:: sh

  # perf record -e trace_imc/trace_cycles/ yes > /dev/null
  [ perf record: 被唤醒 1 次以写入数据 ]
  [ perf record: 捕获并写入了 0.012 MB 的 perf.data（21 个样本） ]

生成的 `perf.data` 可以通过 perf 报告来读取。
使用 IMC 跟踪模式的好处
================================

由于 IMC 跟踪模式会快照程序计数器并更新内存，因此避免了处理 PMI（性能监控中断）。这种方式还使操作系统能够在没有 PMI 处理开销的情况下实时进行指令采样。
使用 `perf top` 时带有与不带 trace-imc 事件的性能数据
在执行 `perf top` 命令但不使用 trace-imc 事件时的 PMI 中断计数
.. code-block:: sh

  # grep PMI /proc/interrupts
  PMI:          0          0          0          0   性能监控中断
  # ./perf top
  ..
# grep PMI /proc/interrupts
  PMI:      39735       8710      17338      17801   性能监控中断
  # ./perf top -e trace_imc/trace_cycles/
  ..
# grep PMI /proc/interrupts
  PMI:      39735       8710      17338      17801   性能监控中断


也就是说，在使用 `trace_imc` 事件时，PMI 中断计数不会增加。
