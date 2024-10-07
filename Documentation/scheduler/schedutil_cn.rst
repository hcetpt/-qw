Schedutil
=========

.. note::

   以下假设频率与工作能力之间存在线性关系，我们知道这是有缺陷的，但这是目前最佳的可用近似方法。

PELT（Per Entity Load Tracking）
===============================

通过PELT，我们跟踪各个调度实体（从单个任务到任务组切片再到CPU运行队列）的一些指标。为此，我们使用指数加权移动平均值（EWMA），每个周期（1024微秒）会衰减，使得y^32 = 0.5。也就是说，最近的32毫秒贡献了一半，而历史上的其余部分贡献了另一半。具体来说：

  ewma_sum(u) := u_0 + u_1*y + u_2*y^2 + ...
  ewma(u) = ewma_sum(u) / ewma_sum(1)

由于这本质上是一个无限几何级数的进展，结果是可以组合的，即ewma(A) + ewma(B) = ewma(A+B)。这一特性是关键的，因为它允许在任务迁移时重新组合这些平均值。
请注意，被阻塞的任务仍然对聚合值（任务组切片和CPU运行队列）有所贡献，这反映了它们在恢复运行时的预期贡献。
使用这种方法，我们跟踪两个关键指标：'running'和'runnable'。'running'反映了一个实体在CPU上花费的时间，而'runnable'反映了一个实体在运行队列上花费的时间。当只有一个任务时，这两个指标是相同的，但一旦出现对CPU的竞争，'running'将会减少以反映每个任务在CPU上所占的时间比例，而'runnable'将会增加以反映竞争程度。
更多细节请参见：kernel/sched/pelt.c

频率/CPU不变性
==========================

因为消耗1GHz下50%的CPU与消耗2GHz下50%的CPU是不同的，同样，在LITTLE CPU上运行50%与在big CPU上运行50%也是不同的，因此我们允许架构通过两个比率来调整时间差，一个是动态电压和频率缩放（DVFS）比率，另一个是微架构比率。
对于简单的DVFS架构（软件完全控制的情况下），我们可以简单地计算比率为：

	    f_cur
  r_dvfs := -----
            f_max

对于更动态的系统（硬件控制DVFS），我们使用硬件计数器（如Intel APERF/MPERF、ARMv8.4-AMU）来提供这个比率。
对于Intel，我们使用：

	   APERF
  f_cur := ----- * P0
	   MPERF

	     4C-turbo；如果可用且turbo启用
  f_max := { 1C-turbo；如果turbo启用
	     P0；否则

                    f_cur
  r_dvfs := min( 1, ----- )
                    f_max

我们选择4C turbo而非1C turbo是为了使其稍微更加可持续。
r_cpu是根据当前CPU的最高性能级别与系统中其他任何CPU的最高性能级别的比率来确定的。
r_tot = r_dvfs * r_cpu

结果是上述的 'running' 和 'runnable' 指标变得与 DVFS 和 CPU 类型无关。换句话说，我们可以在不同的 CPU 之间传递和比较这些指标。更多细节请参见：

- kernel/sched/pelt.h: update_rq_clock_pelt()
- arch/x86/kernel/smpboot.c: "APERF/MPERF 频率比计算"
- Documentation/scheduler/sched-capacity.rst: "1. CPU 容量 + 2. 任务利用率"

UTIL_EST
========

由于周期性任务在睡眠时其平均值会衰减，尽管当它们运行时预期的利用率相同，但它们在再次运行后会经历 DVFS 的上升阶段。为了缓解这一问题（默认启用选项），UTIL_EST 在任务出队时使用无限脉冲响应 (IIR) 指数加权移动平均 (EWMA) 来驱动 'running' 值——此时它最高。UTIL_EST 过滤器会立即增加并在减少时衰减。进一步地，在运行队列范围内维护了一个可运行任务的总和：

  util_est := \Sum_t max( t_running, t_util_est_ewma )

更多细节请参见：kernel/sched/fair.c: util_est_dequeue()

UCLAMP
======

可以为每个 CFS 或 RT 任务设置有效的 u_min 和 u_max 限制；运行队列会为所有运行任务保持这些限制的最大聚合值。更多细节请参见：include/uapi/linux/sched/types.h

Schedutil / DVFS
================

每当调度器负载跟踪更新（任务唤醒、任务迁移、时间进展）时，我们会调用 schedutil 更新硬件 DVFS 状态。基础是 CPU 运行队列的 'running' 指标，根据上述内容，这是 CPU 的频率不变利用率估计。从这里我们计算所需的频率如下：

             max( running, util_est ); 如果启用了 UTIL_EST
  u_cfs := { running;                否则

               clamp( u_cfs + u_rt , u_min, u_max ); 如果启用了 UCLAMP_TASK
  u_clamp := { u_cfs + u_rt;                 否则

  u := u_clamp + u_irq + u_dl;      [近似，请参见源代码获取更多细节]

  f_des := min( f_max, 1.25 u * f_max )

XXX IO-wait: 当更新是由于任务从 I/O 完成中唤醒时，我们将 'u' 提升

此频率随后用于选择一个 P-state/OPP 或直接转换为对硬件的 CPPC 样式请求。由于这些回调直接来自调度器，因此 DVFS 硬件交互应该是“快速”且非阻塞的。Schedutil 支持限速 DVFS 请求，以便在硬件交互缓慢且昂贵的情况下使用，这会降低有效性。更多信息请参见：kernel/sched/cpufreq_schedutil.c

NOTES
=====

- 在低负载场景下，DVFS 最相关的地方，'running' 数值将紧密反映利用率
- 在饱和场景中，任务迁移会导致一些瞬时下降。假设我们有一个被4个任务占满的CPU，当我们把一个任务迁移到空闲的CPU上时，原来的CPU的“运行”值会变为0.75，而新的CPU会增加0.25的负载。这是不可避免的，但随着时间的推移，这种情况会得到修正。XXX 由于没有空闲时间，我们是否仍能保证达到 f_max？

- 上述大部分内容是关于避免DVFS（动态电压和频率调节）的瞬时下降，以及独立的DVFS域在负载转移时需要重新学习/提升频率的问题。
