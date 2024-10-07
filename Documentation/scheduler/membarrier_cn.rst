SPDX 许可证标识符：GPL-2.0

========================
membarrier() 系统调用
========================

MEMBARRIER_CMD_{PRIVATE,GLOBAL}_EXPEDITED - 架构要求
==================================================

在更新 rq->curr 之前的内存屏障
----------------------------------------

命令 MEMBARRIER_CMD_PRIVATE_EXPEDITED 和 MEMBARRIER_CMD_GLOBAL_EXPEDITED 要求每个架构在从用户空间返回后，在更新 rq->curr 之前必须有一个完整的内存屏障。这个屏障由序列 rq_lock(); smp_mb__after_spinlock() 在 __schedule() 中隐含。该屏障与 membarrier 系统调用退出附近的完整屏障相匹配，参见 membarrier_{private,global}_expedited()。

在更新 rq->curr 之后的内存屏障
---------------------------------------

命令 MEMBARRIER_CMD_PRIVATE_EXPEDITED 和 MEMBARRIER_CMD_GLOBAL_EXPEDITED 要求每个架构在更新 rq->curr 之后，在返回用户空间之前必须有一个完整的内存屏障。各架构提供此屏障的方法如下：

- alpha、arc、arm、hexagon、mips 依赖于 finish_lock_switch() 中 spin_unlock() 隐含的完整屏障。
- arm64 依赖于 switch_to() 隐含的完整屏障。
- powerpc、riscv、s390、sparc、x86 依赖于 switch_mm() 隐含的完整屏障（如果 mm 不为 NULL）；否则它们依赖于 mmdrop() 隐含的完整屏障。在 powerpc 和 riscv 上，switch_mm() 依赖于 membarrier_arch_switch_mm()。

该屏障与 membarrier 系统调用入口附近的完整屏障相匹配，参见 membarrier_{private,global}_expedited()。
