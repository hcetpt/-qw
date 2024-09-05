.. SPDX-License-Identifier: GPL-2.0

============================================================
使用 Linux 内核转储测试模块 (LKDTM) 触发崩溃
============================================================

lkdtm 模块提供了一个接口，可以在预定义的代码位置中断（通常导致崩溃）内核，以评估内核异常处理的可靠性，并测试使用不同转储解决方案获得的崩溃转储。该模块使用 KPROBE 对触发位置进行仪器化，但也可以通过 debugfs 直接触发内核，而无需 KPROBE 支持。
您可以选择触发位置（"崩溃点名称"）和操作类型（"崩溃点类型"），方法是在插入模块时通过模块参数设置，或者通过 debugfs 接口设置。
用法如下：

```
insmod lkdtm.ko [recur_count={>0}] cpoint_name=<> cpoint_type=<>
            [cpoint_count={>0}]
```

`recur_count`
    栈溢出测试中的递归级别。默认情况下，此值根据内核配置动态计算，目的是刚好足够耗尽内核栈。该值可以通过 `/sys/module/lkdtm/parameters/recur_count` 查看。

`cpoint_name`
    在内核中触发动作的位置。它可以是以下之一：INT_HARDWARE_ENTRY、INT_HW_IRQ_EN、INT_TASKLET_ENTRY、FS_SUBMIT_BH、MEM_SWAPOUT、TIMERADD、SCSI_QUEUE_RQ 或 DIRECT。

`cpoint_type`
    表示在触发崩溃点时应采取的操作。这些选项有很多，最好直接从 debugfs 查询。一些常见的选项包括 PANIC、BUG、EXCEPTION、LOOP 和 OVERFLOW。
    完整列表可以查看 `/sys/kernel/debug/provoke-crash/DIRECT` 的内容。

`cpoint_count`
    表示触发动作之前要触发崩溃点的次数。默认值为 10（除了 DIRECT，它总是立即触发）。

您还可以通过挂载 debugfs 并将类型写入 `<debugfs>/provoke-crash/<crashpoint>` 来诱导故障。例如：

```
mount -t debugfs debugfs /sys/kernel/debug
echo EXCEPTION > /sys/kernel/debug/provoke-crash/INT_HARDWARE_ENTRY
```

特殊的文件 `DIRECT` 可以在没有 KPROBE 仪器化的情况下直接触发动作。当模块为不支持 KPROBE 的内核构建时，这是唯一可用的模式：

```
# 与其让一个 BUG 杀死你的 shell，不如让它杀死 "cat"：
cat <(echo WRITE_RO) >/sys/kernel/debug/provoke-crash/DIRECT
```
