==================================
内核锁折磨测试操作
==================================

CONFIG_LOCK_TORTURE_TEST
========================

CONFIG_LOCK_TORTURE_TEST 配置选项提供了一个内核模块，用于对核心内核锁定原语进行折磨测试。如果需要的话，可以在要测试的运行内核上事后构建这个名为 'locktorture' 的内核模块。测试会定期通过 printk() 输出状态信息，这些信息可以通过 dmesg（可能需要 grep "torture"）来查看。当模块加载时测试开始，并在模块卸载时停止。该程序基于 RCU 的折磨测试方法（通过 rcutorture）。  

这种折磨测试包括创建多个内核线程，这些线程获取锁并在特定时间内保持锁，从而模拟不同的临界区行为。通过增加临界区保持时间或创建更多 kthreads 来模拟锁上的竞争。

模块参数
=================

此模块具有以下参数：

Locktorture 特定参数
--------------------

nwriters_stress
		  用于施加独占锁所有权（写入者）压力的内核线程数量。默认值是在线 CPU 数量的两倍。
nreaders_stress
		  用于施加共享锁所有权（读取者）压力的内核线程数量。默认值与写入锁的数量相同。如果用户没有指定 nwriters_stress，则读取者和写入者的数量将为在线 CPU 的数量。
torture_type
		  要折磨的锁类型。默认情况下，仅折磨自旋锁。此模块可以折磨以下类型的锁，其字符串值如下：

		     - "lock_busted":
				模拟一个有缺陷的锁实现
- "spin_lock":
				spin_lock() 和 spin_unlock() 对
- "spin_lock_irq":
				spin_lock_irq() 和 spin_unlock_irq() 对
- "rw_lock":
				read/write lock() 和 unlock() 的 rwlock 对
- "rw_lock_irq":
				read/write lock_irq() 和 unlock_irq()
				rwlock 对
- "mutex_lock":
				mutex_lock() 和 mutex_unlock() 对
```markdown
- "rtmutex_lock":
    rtmutex_lock() 和 rtmutex_unlock() 的配对
内核必须设置 CONFIG_RT_MUTEXES=y

- "rwsem_lock":
    读/写 down() 和 up() 信号量的配对
折磨测试框架（RCU + 锁）

---

shutdown_secs
    运行测试的秒数，之后终止测试并关闭系统。默认值为零，这会禁用测试终止和系统关机
此功能对于自动化测试很有用

onoff_interval
    每次尝试执行随机选择的CPU热插拔操作之间的秒数。默认值为零，这会禁用CPU热插拔。在
    CONFIG_HOTPLUG_CPU=n 内核中，locktorture 会默默地拒绝执行任何CPU热插拔操作，无论
    onoff_interval 设置为何值
onoff_holdoff
    开始执行CPU热插拔操作前等待的秒数。通常仅在locktorture被编入内核并在启动时自动运行的情况下使用，
    此时为了避免启动代码因CPU的插入和移除而混淆，该参数是有用的。只有当启用CONFIG_HOTPLUG_CPU时，
    该参数才有意义

stat_interval
    统计信息相关printk()之间的时间间隔
默认情况下，locktorture每60秒报告一次统计信息
将时间间隔设置为零会使统计信息仅在模块卸载时打印
```
### stutter
在暂停相同时间之前运行测试的时长。默认值为“stutter=5”，即以（大约）五秒的间隔运行和暂停。
指定“stutter=0”会使测试连续运行而不暂停。

### shuffle_interval
保持测试线程与特定CPU子集关联的秒数，默认为3秒。
与`test_no_idle_hz`结合使用。

### verbose
启用通过`printk()`进行的详细调试打印，默认已启用。这些额外信息主要与高层次错误和主‘torture’框架中的报告相关。

### 统计信息
统计信息以如下格式打印：

```
spin_lock-torture: Writes:  Total: 93746064  Max/Min: 0/0   Fail: 0
     (A)		    (B)		   (C)		  (D)	       (E)
```

  (A): 正在折磨的锁类型 —— `torture_type` 参数
  (B): 写入锁获取次数。如果处理的是读写原语，则会打印第二行“Reads”统计数据。
  (C): 锁被获取的次数。
  (D): 线程未能获取锁的最大和最小次数。
  (E): 如果获取锁时有错误，其值为true/false。这应该仅在锁定原语实现中存在bug时为正；否则，锁不应失败（例如，`spin_lock()`）。
当然，上述情况同样适用于（C）。一个虚拟的例子是“lock_busted”类型。

用法
=====

以下脚本可用于测试锁：

```sh
#!/bin/sh

modprobe locktorture
sleep 3600
rmmod locktorture
dmesg | grep torture:
```

输出可以手动检查是否存在“!!!”错误标志。当然，也可以创建一个更复杂的脚本来自动检测此类错误。“rmmod”命令会强制打印出“SUCCESS”、“FAILURE”或“RCU_HOTPLUG”的指示信息。前两种情况很容易理解，而最后一种表示虽然没有锁定失败，但检测到了CPU热插拔问题。

另见：Documentation/RCU/torture.rst
