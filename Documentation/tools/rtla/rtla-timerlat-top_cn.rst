====================
rtla-timerlat-top
====================

-------------------------------------------
测量操作系统定时器延迟
-------------------------------------------

:手册章节: 1

概要
======
**rtla timerlat top** [*选项*] ..

描述
==========

.. include:: common_timerlat_description.rst

**rtla timerlat top** 显示来自 *timerlat* 追踪器的周期性输出摘要。它还通过 **osnoise:** 追踪点提供每个操作系统噪声的信息，这些信息可以通过选项 **-T** 查看。
选项
=======

.. include:: common_timerlat_options.rst

.. include:: common_top_options.rst

.. include:: common_options.rst

.. include:: common_timerlat_aa.rst

**--aa-only** *us*

        设置停止追踪条件并在不收集和显示统计数据的情况下运行
如果系统达到停止追踪条件，则打印自动分析结果。此选项
        对于减少 rtla timerlat 的 CPU 使用率非常有用，可以在没有收集统计信息开销的情况下进行调试。
示例
=======

在下面的示例中，在自动追踪模式下将 timerlat 追踪器分配给 cpus *1-23*，并指示追踪器在发现 *40 us* 或更高的延迟时停止::

  # timerlat -a 40 -c 1-23 -q
                                     定时器延迟
    0 00:00:12   |          中断定时器延迟 (us)        |         线程定时器延迟 (us)
  CPU 计数       |      当前       最小       平均       最大 |      当前       最小       平均       最大
    1 #12322     |        0         0         1        15 |       10         3         9        31
    2 #12322     |        3         0         1        12 |       10         3         9        23
    3 #12322     |        1         0         1        21 |        8         2         8        34
    4 #12322     |        1         0         1        17 |       10         2        11        33
    5 #12322     |        0         0         1        12 |        8         3         8        25
    6 #12322     |        1         0         1        14 |       16         3        11        35
    7 #12322     |        0         0         1        14 |        9         2         8        29
    8 #12322     |        1         0         1        22 |        9         3         9        34
    9 #12322     |        0         0         1        14 |        8         2         8        24
   10 #12322     |        1         0         0        12 |        9         3         8        24
   11 #12322     |        0         0         0        15 |        6         2         7        29
   12 #12321     |        1         0         0        13 |        5         3         8        23
   13 #12319     |        0         0         1        14 |        9         3         9        26
   14 #12321     |        1         0         0        13 |        6         2         8        24
   15 #12321     |        1         0         1        15 |       12         3        11        27
   16 #12318     |        0         0         1        13 |        7         3        10        24
   17 #12319     |        0         0         1        13 |       11         3         9        25
   18 #12318     |        0         0         0        12 |        8         2         8        20
   19 #12319     |        0         0         1        18 |       10         2         9        28
   20 #12317     |        0         0         0        20 |        9         3         8        34
   21 #12318     |        0         0         0        13 |        8         3         8        28
   22 #12319     |        0         0         1        11 |        8         3        10        22
   23 #12320     |       28         0         1        28 |       41         3        11        41
  rtla timerlat 达到停止追踪条件
  ## CPU 23 达到停止追踪条件，正在分析它 ##
  中断处理器延迟:                                        27.49 us (65.52 %)
  中断延迟:                                              28.13 us
  Timerlat 中断持续时间:                                     9.59 us (22.85 %)
  阻塞线程:                                           3.79 us (9.03 %)
                         objtool:49256                       3.79 us
    阻塞线程堆栈跟踪
                -> timerlat_irq
                -> __hrtimer_run_queues
                -> hrtimer_interrupt
                -> __sysvec_apic_timer_interrupt
                -> sysvec_apic_timer_interrupt
                -> asm_sysvec_apic_timer_interrupt
                -> _raw_spin_unlock_irqrestore
                -> cgroup_rstat_flush_locked
                -> cgroup_rstat_flush_irqsafe
                -> mem_cgroup_flush_stats
                -> mem_cgroup_wb_stats
                -> balance_dirty_pages
                -> balance_dirty_pages_ratelimited_flags
                -> btrfs_buffered_write
                -> btrfs_do_write_iter
                -> vfs_write
                -> __x64_sys_pwrite64
                -> do_syscall_64
                -> entry_SYSCALL_64_after_hwframe
  ------------------------------------------------------------------------
    线程延迟:                                          41.96 us (100%)

  系统存在退出空闲状态的延迟！
    从空闲状态的最大中断延迟：17.48 us 在 cpu 4 上
  将追踪保存到 timerlat_trace.txt

在这种情况下，主要因素是处理 **timerlat** 唤醒的 *中断处理器* 所遭受的延迟：*65.52%*。这可能是由于当前线程屏蔽了中断造成的，可以从阻塞线程堆栈跟踪中看到：当前线程 (*objtool:49256*) 通过 mem cgroup 内的 *raw spin lock* 操作禁用了中断，同时在一个 btrfs 文件系统中执行写入系统调用。
原始追踪已保存在文件 **timerlat_trace.txt** 中以供进一步分析。
请注意，**rtla timerlat** 被调度而没有改变 *timerlat* 追踪器线程的优先级。通常来说这是不必要的，因为这些线程默认具有 *FIFO:95* 的优先级，这是实时内核开发者用来分析调度延迟的一个常见优先级。
参见
------
**rtla-timerlat**\(1), **rtla-timerlat-hist**\(1\)

*timerlat* 追踪器文档: <https://www.kernel.org/doc/html/latest/trace/timerlat-tracer.html>

作者
------
由 Daniel Bristot de Oliveira <bristot@kernel.org> 编写

.. include:: common_appendix.rst
