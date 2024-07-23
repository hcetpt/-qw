标题：=====================
rtla-timerlat-hist
=====================

------------------------------------------------
操作系统定时器延迟的直方图
------------------------------------------------

:手册章节: 1

概要
========
**rtla timerlat hist** [*选项*] ..

描述
===========
.. 包含:: common_timerlat_description.rst

**rtla timerlat hist** 显示每个追踪事件发生的直方图。
此工具使用周期性信息，当使用 **-T** 选项时，
**osnoise:** 的追踪点会被启用。

选项
=======

.. 包含:: common_timerlat_options.rst

.. 包含:: common_hist_options.rst

.. 包含:: common_options.rst

.. 包含:: common_timerlat_aa.rst

示例
=======
在下面的示例中，**rtla timerlat hist** 被设置为运行 *10* 分钟，
在 *0-4* 号CPU上运行，仅 *跳过零* 行。此外，**rtla timerlat
hist** 将改变 *timerlat* 线程的优先级，在 *SCHED_DEADLINE* 优先级下运行，
每个 *1ms* 周期内有 *100us* 运行时间。*1ms* 周期也被传递给 *timerlat* 追踪器。
禁用自动分析以减少开销 ::

  [root@alien ~]# timerlat hist -d 10m -c 0-4 -P d:100us:1ms -p 1000 --no-aa
  # RTLA 定时器延迟直方图
  # 时间单位是微秒（us）
  # 持续时间:   0 00:10:00
  Index   IRQ-000   Thr-000   IRQ-001   Thr-001   IRQ-002   Thr-002   IRQ-003   Thr-003   IRQ-004   Thr-004
  0        276489         0    206089         0    466018         0    481102         0    205546         0
  1        318327     35487    388149     30024     94531     48382     83082     71078    388026     55730
  2          3282    122584      4019    126527     28231    109012     23311     89309      4568     98739
  3           940     11815       837      9863      6209     16227      6895     17196       910      9780
  4           444     17287       424     11574      2097     38443      2169     36736       462     13476
  ... （省略部分数据）

查看更多
========
**rtla-timerlat**(1), **rtla-timerlat-top**(1)

*timerlat* 追踪器文档: <https://www.kernel.org/doc/html/latest/trace/timerlat-tracer.html>

作者
======
由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>
