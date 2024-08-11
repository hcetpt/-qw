Linux 内核 API
====================

列表管理函数
=========================

.. kernel-doc:: include/linux/list.h
   :internal:

基本 C 库函数
=========================

编写驱动程序时，通常不能使用来自 C 库的例程。一些函数被发现非常有用，并在下面列出。这些函数的行为可能与 ANSI 定义的行为略有不同，这些偏差会在文中注明。

字符串转换
------------------

.. kernel-doc:: lib/vsprintf.c
   :export:

.. kernel-doc:: include/linux/kstrtox.h
   :functions: kstrtol kstrtoul

.. kernel-doc:: lib/kstrtox.c
   :export:

.. kernel-doc:: lib/string_helpers.c
   :export:

字符串操作
-------------------

.. kernel-doc:: include/linux/fortify-string.h
   :internal:

.. kernel-doc:: lib/string.c
   :export:

.. kernel-doc:: include/linux/string.h
   :internal:

.. kernel-doc:: mm/util.c
   :functions: kstrdup kstrdup_const kstrndup kmemdup kmemdup_nul memdup_user vmemdup_user strndup_user memdup_user_nul

基本内核库函数
==============================

Linux 内核提供了更多基本的实用函数。

位操作
--------------

.. kernel-doc:: include/asm-generic/bitops/instrumented-atomic.h
   :internal:

.. kernel-doc:: include/asm-generic/bitops/instrumented-non-atomic.h
   :internal:

.. kernel-doc:: include/asm-generic/bitops/instrumented-lock.h
   :internal:

位图操作
-----------------

.. kernel-doc:: lib/bitmap.c
   :doc: bitmap introduction

.. kernel-doc:: include/linux/bitmap.h
   :doc: declare bitmap

.. kernel-doc:: include/linux/bitmap.h
   :doc: bitmap overview

.. kernel-doc:: include/linux/bitmap.h
   :doc: bitmap bitops

.. kernel-doc:: lib/bitmap.c
   :export:

.. kernel-doc:: lib/bitmap.c
   :internal:

.. kernel-doc:: include/linux/bitmap.h
   :internal:

命令行解析
--------------------

.. kernel-doc:: lib/cmdline.c
   :export:

错误指针
--------------

.. kernel-doc:: include/linux/err.h
   :internal:

排序
-------

.. kernel-doc:: lib/sort.c
   :export:

.. kernel-doc:: lib/list_sort.c
   :export:

文本搜索
--------------

.. kernel-doc:: lib/textsearch.c
   :doc: ts_intro

.. kernel-doc:: lib/textsearch.c
   :export:

.. kernel-doc:: include/linux/textsearch.h
   :functions: textsearch_find textsearch_next textsearch_get_pattern textsearch_get_pattern_len

CRC 和数学函数
===============================

算术溢出检查
----------------------------

.. kernel-doc:: include/linux/overflow.h
   :internal:

CRC 函数
-------------

.. kernel-doc:: lib/crc4.c
   :export:

.. kernel-doc:: lib/crc7.c
   :export:

.. kernel-doc:: lib/crc8.c
   :export:

.. kernel-doc:: lib/crc16.c
   :export:

.. kernel-doc:: lib/crc32.c

.. kernel-doc:: lib/crc-ccitt.c
   :export:

.. kernel-doc:: lib/crc-itu-t.c
   :export:

以 2 为底的对数和幂函数
------------------------------

.. kernel-doc:: include/linux/log2.h
   :internal:

整数对数和幂函数
-------------------------------

.. kernel-doc:: include/linux/int_log.h

.. kernel-doc:: lib/math/int_pow.c
   :export:

.. kernel-doc:: lib/math/int_sqrt.c
   :export:

除法函数
------------------

.. kernel-doc:: include/asm-generic/div64.h
   :functions: do_div

.. kernel-doc:: include/linux/math64.h
   :internal:

.. kernel-doc:: lib/math/gcd.c
   :export:

UUID/GUID
---------

.. kernel-doc:: lib/uuid.c
   :export:

内核 IPC 设施
=====================

IPC 实用工具
-------------

.. kernel-doc:: ipc/util.c
   :internal:

先进先出缓冲区 (FIFO)
===========

kfifo 接口
---------------

.. kernel-doc:: include/linux/kfifo.h
   :internal:

中继接口支持
=======================

中继接口支持旨在提供一个有效的机制，用于工具和设施将大量数据从内核空间传递到用户空间。

中继接口
---------------

.. kernel-doc:: kernel/relay.c
   :export:

.. kernel-doc:: kernel/relay.c
   :internal:

模块支持
==============

内核模块自动加载
--------------------------

.. kernel-doc:: kernel/module/kmod.c
   :export:

模块调试
----------------

.. kernel-doc:: kernel/module/stats.c
   :doc: module debugging statistics overview

dup_failed_modules — 跟踪重复失败的模块
****************************************************

.. kernel-doc:: kernel/module/stats.c
   :doc: dup_failed_modules — 跟踪重复失败的模块

模块统计 debugfs 计数器
**********************************

.. kernel-doc:: kernel/module/stats.c
   :doc: module statistics debugfs counters

模块间支持
--------------------

更多信息请参阅 kernel/module/ 中的文件。

硬件接口
===================

DMA 通道
------------

.. kernel-doc:: kernel/dma.c
   :export:

资源管理
--------------------

.. kernel-doc:: kernel/resource.c
   :internal:

.. kernel-doc:: kernel/resource.c
   :export:

MTRR 处理
-------------

.. kernel-doc:: arch/x86/kernel/cpu/mtrr/mtrr.c
   :export:

安全框架
==================

.. kernel-doc:: security/security.c
   :internal:

.. kernel-doc:: security/inode.c
   :export:

审计接口
================

.. kernel-doc:: kernel/audit.c
   :export:

.. kernel-doc:: kernel/auditsc.c
   :internal:

.. kernel-doc:: kernel/auditfilter.c
   :internal:

会计框架
====================

.. kernel-doc:: kernel/acct.c
   :internal:

块设备
=============

.. kernel-doc:: include/linux/bio.h
.. kernel-doc:: block/blk-core.c
   :export:

.. kernel-doc:: block/blk-core.c
   :internal:

.. kernel-doc:: block/blk-map.c
   :export:

.. kernel-doc:: block/blk-sysfs.c
   :internal:

.. kernel-doc:: block/blk-settings.c
   :export:

.. kernel-doc:: block/blk-flush.c
   :export:

.. kernel-doc:: block/blk-lib.c
   :export:

.. kernel-doc:: block/blk-integrity.c
   :export:

.. kernel-doc:: kernel/trace/blktrace.c
   :internal:

.. kernel-doc:: block/genhd.c
   :internal:

.. kernel-doc:: block/genhd.c
   :export:

.. kernel-doc:: block/bdev.c
   :export:

字符设备
============

.. kernel-doc:: fs/char_dev.c
   :export:

时钟框架
===============

时钟框架定义了编程接口来支持系统时钟树的软件管理。此框架广泛用于 SoC 平台，以支持电源管理和可能需要自定义时钟速率的各种设备。请注意，这些“时钟”与时间跟踪或实时时钟（RTCs）无关，后者各自具有单独的框架。这些 :c:type:`struct clk <clk>` 实例可以用来管理例如用于向外围设备或总线输入和输出比特的 96 MHz 信号，或者在系统硬件中触发同步状态机转换。
电源管理通过明确的软件时钟门控支持：未使用的时钟被禁用，因此系统不会浪费电力改变未处于活动状态的晶体管的状态。在某些系统上，这可能由硬件时钟门控支持，在这种情况下，时钟被门控但没有在软件中禁用。芯片的部分区域虽然通电但没有时钟，可能能够保留其最后状态。这种低功耗状态通常称为“保留模式”。此模式仍然会遭受泄漏电流，特别是在更精细的电路几何结构中，但对于 CMOS 电路来说，大部分功率是由时钟状态变化所消耗的。
电源感知驱动程序仅在其管理的设备处于活动使用状态时启用其时钟。此外，系统休眠状态通常根据哪些时钟域处于活动状态而有所不同：虽然“待机”状态可能允许从几个活动域唤醒，但“mem”（挂起到 RAM）状态可能需要更全面地关闭来自更高速 PLL 和振荡器的时钟，从而限制可能的唤醒事件源的数量。驱动程序的挂起方法可能需要了解目标休眠状态上的系统特定时钟约束。
一些平台支持可编程时钟发生器。这些可以被各种类型的外部芯片使用，如其他 CPU、多媒体编解码器和对接口时钟有严格要求的设备。
.. kernel-doc:: include/linux/clk.h
   :internal:

同步原语
==========================

读取复制更新 (RCU)
----------------------

.. kernel-doc:: include/linux/rcupdate.h

.. kernel-doc:: kernel/rcu/tree.c

.. kernel-doc:: kernel/rcu/tree_exp.h

.. kernel-doc:: kernel/rcu/update.c

.. kernel-doc:: include/linux/srcu.h

.. kernel-doc:: kernel/rcu/srcutree.c

.. kernel-doc:: include/linux/rculist_bl.h

.. kernel-doc:: include/linux/rculist.h

.. kernel-doc:: include/linux/rculist_nulls.h

.. kernel-doc:: include/linux/rcu_sync.h

.. kernel-doc:: kernel/rcu/sync.c

.. kernel-doc:: kernel/rcu/tasks.h

.. kernel-doc:: kernel/rcu/tree_stall.h

.. kernel-doc:: include/linux/rcupdate_trace.h

.. kernel-doc:: include/linux/rcupdate_wait.h

.. kernel-doc:: include/linux/rcuref.h

.. kernel-doc:: include/linux/rcutree.h
