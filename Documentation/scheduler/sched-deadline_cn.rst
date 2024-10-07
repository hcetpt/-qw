========================
截止任务调度
========================

.. 目录

    0. 警告
    1. 概览
    2. 调度算法
      2.1 主要算法
      2.2 带宽回收
    3. 实时任务的调度
      3.1 定义
      3.2 单处理器系统的可调度性分析
      3.3 多处理器系统的可调度性分析
      3.4 与 SCHED_DEADLINE 参数的关系
    4. 带宽管理
      4.1 系统范围设置
      4.2 任务接口
      4.3 默认行为
      4.4 sched_yield() 的行为
    5. 任务的 CPU 亲和性
      5.1 SCHED_DEADLINE 和 cpusets 的使用说明
    6. 未来计划
    A. 测试套件
    B. 最小化的 main()

0. 警告
======

 修改这些设置可能会导致系统行为不可预测甚至不稳定。对于 -rt（组）调度，假设根用户知道自己在做什么。

1. 概览
======

 SCHED_DEADLINE 策略包含在 sched_dl 调度类中，基本上是 Earliest Deadline First (EDF) 调度算法的实现，并增加了常带宽服务器（CBS）机制，使得任务之间的行为可以相互隔离。

2. 调度算法
===========

2.1 主要算法
--------------

 SCHED_DEADLINE [18] 使用三个参数：“运行时间”、“周期”和“截止时间”，来调度任务。一个 SCHED_DEADLINE 任务应该每“周期”微秒获得“运行时间”微秒的执行时间，并且这些“运行时间”微秒在周期开始后的“截止时间”微秒内可用。为了实现这种行为，每次任务唤醒时，调度器都会根据保证（使用 CBS[2,3] 算法）计算一个“调度截止时间”。然后使用 EDF[1] 根据这些调度截止时间对任务进行调度（选择调度截止时间最早的任执行）。需要注意的是，如果采用适当的“准入控制”策略（见“4. 带宽管理”部分），任务实际上会在“截止时间”内获得“运行时间”的时间单位（显然，如果系统过载，这一保证无法得到尊重）。

总结一下，CBS[2,3] 算法为任务分配调度截止时间，以确保每个任务在每个周期内最多运行其运行时间，避免不同任务之间的干扰（带宽隔离），而 EDF[1] 算法则选择调度截止时间最早的下一个任务执行。由于这一特性，不符合“传统”实时任务模型的任务（见第 3 节）也可以有效使用新策略。

具体来说，CBS 算法按照以下方式为任务分配调度截止时间：

  - 每个 SCHED_DEADLINE 任务由“运行时间”、“截止时间”和“周期”参数描述；

  - 任务的状态由“调度截止时间”和“剩余运行时间”两个参数描述，这两个参数初始值都设为 0；

  - 当 SCHED_DEADLINE 任务唤醒（准备执行）时，调度器检查如下条件是否满足：

                 剩余运行时间                  运行时间
        ----------------------------------    >    ---------
        调度截止时间 - 当前时间                   周期

    如果调度截止时间小于当前时间，或者此条件成立，则调度截止时间和剩余运行时间重新初始化为：

         调度截止时间 = 当前时间 + 截止时间
         剩余运行时间 = 运行时间

    否则，调度截止时间和剩余运行时间保持不变；

  - 当 SCHED_DEADLINE 任务执行了一段时间 t 时，其剩余运行时间减少为：

         剩余运行时间 = 剩余运行时间 - t

    （技术上，运行时间在每次滴答或任务被取消调度/抢占时减少）；

  - 当剩余运行时间变为小于等于 0 时，任务被认为“节流”（在实时文献中也称为“耗尽”），直到其调度截止时间之前不能被调度。该任务的“补充时间”（见下一项）设置为当前调度截止时间的值；

  - 当当前时间等于节流任务的补充时间时，调度截止时间和剩余运行时间更新为：

         调度截止时间 = 调度截止时间 + 周期
         剩余运行时间 = 剩余运行时间 + 运行时间

sched_attr 的 sched_flags 字段中的 SCHED_FLAG_DL_OVERRUN 标志允许任务通过发送 SIGXCPU 信号了解运行时间超限情况。

2.2 带宽回收
--------------

 截止任务的带宽回收基于 GRUB（贪婪回收未用带宽）算法 [15, 16, 17]，当设置了 SCHED_FLAG_RECLAIM 标志时启用。

下图展示了 GRUB 处理的任务状态名称：

                             ------------
                 (d)        |   Active   |
              ------------->|            |
              |             | Contending |
              |              ------------
              |                A      |
          ----------           |      |
         |          |          |      |
         | Inactive |          |(b)   | (a)
         |          |          |      |
          ----------           |      |
              A                |      V
              |              ------------
              |             |   Active   |
              --------------|     Non    |
                 (c)        | Contending |
                             ------------

 任务可以处于以下状态之一：

  - ActiveContending：如果任务准备好执行（或正在执行）；

  - ActiveNonContending：如果任务刚刚阻塞且尚未超过 0-lag 时间；

  - Inactive：如果任务阻塞且已超过 0-lag 时间。
状态转换：

  (a) 当任务阻塞时，它不会立即进入非活动状态，因为其带宽不能立即回收而不破坏实时保证。因此，它进入一个过渡状态称为 ActiveNonContending。调度器设置“非活动定时器”，在 0-lag 时间触发，此时可以在不破坏实时保证的情况下回收任务带宽。

  对于进入 ActiveNonContending 状态的任务，0-lag 时间计算如下：

                        (运行时间 * dl_period)
             截止时间 - ---------------------
                             dl_runtime

  其中运行时间是剩余运行时间，而 dl_runtime 和 dl_period 是预留参数；
(b) 如果任务在非活动定时器触发之前唤醒，任务重新进入 ActiveContending 状态，并取消“非活动定时器”。
此外，如果任务在不同的运行队列上被唤醒，则需要将该任务的利用率从之前的运行队列的活动利用率中移除，并添加到新的运行队列的活动利用率中。

为了避免任务在一个运行队列上被唤醒的同时，“非活动计时器”在另一个CPU上运行所带来的竞态条件，使用了“dl_non_contending”标志来表示任务不在任何运行队列上但仍然是活跃状态（因此，当任务阻塞时设置该标志，在“非活动计时器”触发或任务被唤醒时清除该标志）。

(c) 当“非活动计时器”触发时，任务进入非活动状态，其利用率从运行队列的活动利用率中移除。

(d) 当一个非活动状态的任务被唤醒时，它进入活跃竞争状态，并将其利用率添加到所加入的运行队列的活动利用率中。

对于每个运行队列，GRUB算法跟踪两种不同的带宽：

- 活动带宽（running_bw）：这是所有处于活跃状态（即活跃竞争或活跃非竞争状态）的任务带宽之和；

- 总带宽（this_bw）：这是属于该运行队列的所有任务的带宽之和，包括处于非活动状态的任务。

- 最大可用带宽（max_bw）：这是截止期限任务可使用的最大带宽，目前设定为实时容量。

算法通过减少非活动状态任务的带宽来回收带宽。具体做法是按如下公式递减执行任务Ti的运行时间：

          dq = -(max{ Ui, (Umax - Uinact - Uextra) } / Umax) dt

其中：

- Ui 是任务Ti的带宽；
- Umax 是最大可回收利用率（受实时节流限制）；
- Uinact 是每个运行队列的非活动利用率，计算方式为（this_bq - running_bw）；
- Uextra 是每个运行队列的额外可回收利用率（受实时节流限制）。

现在我们来看一个简单的例子，有两个截止期限任务，运行时间为4，周期为8（即带宽为0.5）：

         A            任务 T1
         |
         |                               |
         |                               |
         |--------                       |----
         |       |                       V
         |---|---|---|---|---|---|---|---|--------->t
         0   1   2   3   4   5   6   7   8

         A            任务 T2
         |
         |                               |
         |                               |
         |       ------------------------|
         |       |                       V
         |---|---|---|---|---|---|---|---|--------->t
         0   1   2   3   4   5   6   7   8

         A            running_bw
         |
       1 -----------------               ------
         |               |               |
      0.5-               -----------------
         |                               |
         |---|---|---|---|---|---|---|---|--------->t
         0   1   2   3   4   5   6   7   8

- 时间 t = 0：

  两个任务都准备好执行，因此处于活跃竞争状态。
  假设任务T1是第一个开始执行的任务。
既然没有非活动任务，其运行时间会以 `dq = -1 dt` 的速率减少。
- 时间 t = 2：

    假设任务 T1 被阻塞
    因此，任务 T1 进入 ActiveNonContending（活跃非竞争）状态。由于其剩余运行时间为 2，其 0-lag 时间为 t = 4
    任务 T2 开始执行，其运行时间仍然以 `dq = -1 dt` 的速率减少，因为没有非活动任务
- 时间 t = 4：

    这是任务 T1 的 0-lag 时间。由于在此期间它没有被唤醒，它进入 Inactive（非活动）状态。其带宽从 running_bw 中移除
    任务 T2 继续执行。然而，其运行时间现在以 `dq = -0.5 dt` 的速率减少，因为 Uinactive = 0.5
    因此，任务 T2 占用了任务 T1 未使用的带宽
- 时间 t = 8：

    任务 T1 被唤醒。它再次进入 ActiveContending（活跃竞争）状态，并且 running_bw 增加

2.3 能效调度
---------------------------

当选择 cpufreq 的 schedutil 管理器时，SCHED_DEADLINE 实现了 GRUB-PA [19] 算法，将 CPU 运行频率降低到仍能确保满足截止时间的最小值。这种行为目前仅在 ARM 架构中实现。

如果改变频率所需的时间与预留周期相当，则需要特别注意。在这种情况下，设置固定的 CPU 频率会导致更少的截止时间错过。

3. 调度实时任务
=============================

..  注意事项 ******************************************************

.. warning::

   本节包含对经典截止时间调度理论及其如何应用于 SCHED_DEADLINE 的（不全面）总结。
读者如果只对如何使用调度策略感兴趣，可以“安全地”跳到第4节。不过，我们强烈建议在满足了测试冲动后回到这里继续阅读，以确保完全理解所有技术细节。
--------------------------------------------------------------------------

没有任何类型的任务不能利用这种新的调度机制，尽管必须指出的是，它特别适合需要对其时间行为提供保证的周期性或偶发性的实时任务，例如多媒体、流媒体、控制应用等。

### 3.1 定义
--------------------------------------------

一个典型的实时任务由一系列计算阶段（任务实例或作业）组成，这些计算阶段以周期性或偶发性的方式被激活。
每个作业 \(J_j\)（其中 \(J_j\) 是任务中的第 \(j\) 个作业）具有以下特征：
- 到达时间 \(r_j\)（作业开始的时间）
- 完成作业所需的计算时间 \(c_j\)
- 绝对截止时间 \(d_j\)，即作业应在该时间内完成

最大执行时间 \(max\{c_j\}\) 被称为该任务的“最坏情况执行时间”（WCET）。
一个实时任务可以是周期性的，周期为 \(P\)，如果 \(r_{j+1} = r_j + P\)；或者偶发性的，最小到达间隔为 \(P\)，如果 \(r_{j+1} \geq r_j + P\)。最终，\(d_j = r_j + D\)，其中 \(D\) 是任务的相对截止时间。
总结来说，一个实时任务可以用以下形式描述：

\[ \text{Task} = (\text{WCET}, D, P) \]

实时任务的利用率定义为其 WCET 与其周期（或最小到达间隔）之间的比率，表示执行任务所需的 CPU 时间比例。
如果总利用率 \(U = \sum(\text{WCET}_i / P_i)\) 大于 \(M\)（其中 \(M\) 等于 CPU 数量），则调度器无法满足所有截止时间。
需要注意的是，总利用率定义为系统中所有实时任务的利用率 \(\text{WCET}_i / P_i\) 的总和。考虑多个实时任务时，第 \(i\) 个任务的参数用下标 “_i” 表示。
此外，如果总利用率大于 \(M\)，则存在实时任务抢占非实时任务的风险。
相反，如果总利用率小于 \(M\)，则非实时任务不会被饿死，并且系统可能能够满足所有截止时间。
事实上，在这种情况下，可以提供一个关于延迟（定义为作业完成时间与绝对截止时间之差与0的最大值）的上限。

更具体地说，可以证明使用全局EDF调度器时，每个任务的最大延迟小于或等于：

((M − 1) · WCET_max − WCET_min) / (M − (M − 2) · U_max) + WCET_max

其中WCET_max = max{WCET_i} 是最大WCET，WCET_min = min{WCET_i} 是最小WCET，而U_max = max{WCET_i/P_i} 是最大利用率[12]。

3.2 单处理器系统的可调度性分析
---------------------------------

如果M=1（单处理器系统），或者在分区调度的情况下（每个实时任务被静态分配到一个且仅一个CPU上），可以正式检查所有截止时间是否都被遵守。

如果对于所有任务都有D_i = P_i，则EDF能够遵守所有在CPU上执行的任务的所有截止时间，当且仅当这些任务的总利用率小于或等于1。

如果某些任务有D_i != P_i，则可以定义任务的密度为WCET_i/min{D_i,P_i}。在这种情况下，EDF能够遵守所有在CPU上执行的任务的所有截止时间，当这些任务的密度之和小于或等于1：

∑(WCET_i / min{D_i, P_i}) ≤ 1

需要注意的是，这个条件只是充分条件，而非必要条件：有些任务集合是可以调度的，但不满足该条件。例如，考虑由Task_1=(50ms,50ms,100ms) 和Task_2=(10ms,100ms,100ms)组成的任务集合，即使

50 / min{50,100} + 10 / min{100, 100} = 50 / 50 + 10 / 100 = 1.1

EDF显然能够调度这两个任务而不错过任何截止时间（Task_1一旦被释放就立即执行，并刚好按时完成；Task_2紧接Task_1之后执行，因此其响应时间不会超过50ms + 10ms = 60ms）。

当然，可以通过测试来精确检查具有D_i != P_i的任务的可调度性（同时满足充分和必要条件），但这不能通过将总利用率或密度与某个常数比较来实现。相反，可以使用所谓的“处理器需求”方法，计算所有任务在一个大小为t的时间间隔内需要的CPU时间总量h(t)，并将这个时间与间隔大小t进行比较。如果对于所有可能的t值，h(t)都小于t（即，任务在一个大小为t的时间间隔内所需的时间少于该间隔的大小），则EDF能够调度这些任务并遵守所有截止时间。由于对所有可能的t值进行这样的检查是不可能的，已经证明[4,5,6]只需要对介于0和最大值L之间的t值进行测试即可。引用的论文包含了所有数学细节，并解释了如何计算h(t)和L。

无论如何，这种分析过于复杂且耗时，无法在线执行。因此，如第4节所述，Linux使用基于任务利用率的接纳测试。

3.3 多处理器系统的可调度性分析
----------------------------------

在具有全局EDF调度的多处理器系统中（非分区系统），基于利用率或密度的可调度性测试是不充分的：可以证明即使D_i = P_i，利用略大于1的任务集合仍可能错过截止时间，无论有多少个CPU。

考虑一个包含M+1个任务的集合{Task_1,...Task_{M+1}}，在一个具有M个CPU的系统上，第一个任务Task_1=(P,P,P)具有周期、相对截止时间和WCET等于P。其余的M个任务Task_i=(e,P-1,P-1)具有任意小的最坏情况执行时间（这里表示为“e”）和比第一个任务更短的周期。因此，如果所有任务都在同一时刻t激活，全局EDF会首先调度这M个任务（因为它们的绝对截止时间为t + P - 1，比Task_1的绝对截止时间t + P要小）。结果，Task_1只能在时间t + e被调度，并将在时间t + e + P完成，超过其绝对截止时间。任务集合的总利用率U = M · e / (P - 1) + P / P = M · e / (P - 1) + 1，对于很小的e值，这可以非常接近1。这就是所谓的“Dhall效应”[7]。注意：Dhall在原始论文中的例子稍微简化了一些（例如，Dhall更正确地计算了lim_{e->0}U）。

对于全局EDF更复杂的可调度性测试已经在实时文献中有所发展[8,9]，但它们不是基于总利用率（或密度）与固定常数的简单比较。如果所有任务都有D_i = P_i，一个充分的可调度性条件可以用简单的方式表达：

∑(WCET_i / P_i) ≤ M - (M - 1) · U_max

其中U_max = max{WCET_i / P_i}[10]。注意，当U_max = 1时，M - (M - 1) · U_max变为M - M + 1 = 1，这个可调度性条件正好确认了Dhall效应。有关多处理器实时调度可调度性测试的更完整综述可以在[11]中找到。
如前所述，确保总利用率小于M并不能保证全局EDF（最早截止时间优先）调度算法能够无遗漏地调度任务（换句话说，全局EDF并不是一个最优的调度算法）。然而，总利用率小于M足以保证非实时任务不会被饿死，并且实时任务的延迟有一个上限[12]（如前所述）。关于实时任务经历的最大延迟的不同界限已在多篇论文中提出[13,14]，但对SCHED_DEADLINE而言重要的理论结果是：如果总利用率小于或等于M，则任务的响应时间是有限的。

### 3.4 与SCHED_DEADLINE参数的关系
-----------------------------------------------

最后，理解SCHED_DEADLINE调度参数（在第2节中描述的运行时间、截止时间和周期）与本节中描述的实时任务参数（WCET、D、P）之间的关系是很重要的。需要注意的是，任务的时间约束由其绝对截止时间d_j = r_j + D表示，而SCHED_DEADLINE根据调度截止时间来调度任务（参见第2节）。
如果使用准入测试以确保调度截止时间得到遵守，则可以使用SCHED_DEADLINE来调度实时任务，从而确保所有任务的工作项截止时间得到遵守。为此，需要设置如下参数：

  - 运行时间 >= WCET
  - 截止时间 = D
  - 周期 <= P

换言之，如果运行时间 >= WCET 且周期 <= P，则调度截止时间和绝对截止时间（d_j）一致，因此适当的准入控制允许遵守该任务的工作项绝对截止时间（这被称为“硬可调度性属性”，是[2]中引理1的扩展）。
需要注意的是，如果运行时间 > 截止时间，则准入控制将肯定会拒绝该任务，因为不可能遵守其时间约束。

### 参考文献：

1 - C. L. Liu 和 J. W. Layland. 在硬实时环境下多程序设计的调度算法。Journal of the Association for Computing Machinery, 20(1), 1973

2 - L. Abeni 和 G. Buttazzo. 在硬实时系统中集成多媒体应用。Proceedings of the 19th IEEE Real-time Systems Symposium, 1998. http://retis.sssup.it/~giorgio/paps/1998/rtss98-cbs.pdf

3 - L. Abeni. 多媒体应用的服务器机制。ReTiS Lab 技术报告。http://disi.unitn.it/~abeni/tr-98-01.pdf

4 - J. Y. Leung 和 M.L. Merril. 关于抢占式调度周期性实时任务的注释。Information Processing Letters, vol. 11, no. 3, pp 115-118, 1980

5 - S. K. Baruah, A. K. Mok 和 L. E. Rosier. 在单处理器上抢占式调度硬实时突发任务。Proceedings of the 11th IEEE Real-time Systems Symposium, 1990

6 - S. K. Baruah, L. E. Rosier 和 R. R. Howell. 关于单处理器上抢占式调度周期性实时任务的算法和复杂性问题。Real-Time Systems Journal, vol. 4, no. 2, pp 301-324, 1990

7 - S. J. Dhall 和 C. L. Liu. 论一个实时调度问题。Operations Research, vol. 26, no. 1, pp 127-140, 1978
8 - T. Baker. 多处理器EDF和截止时间单调调度性分析。第24届IEEE实时系统研讨会论文集，2003年。
9 - T. Baker. 多处理器上EDF调度性分析。《并行与分布式系统》IEEE汇刊，第16卷，第8期，pp. 760-768，2005年。
10 - J. Goossens, S. Funk 和 S. Baruah，多处理器上周期任务系统的优先级驱动调度。《实时系统》期刊，第25卷，第2–3期，pp. 187–205，2003年。
11 - R. Davis 和 A. Burns. 多处理器系统中硬实时调度的综述。ACM计算调查，第43卷，第4期，2011年。
http://www-users.cs.york.ac.uk/~robdavis/papers/MPSurveyv5.0.pdf
12 - U. C. Devi 和 J. H. Anderson. 多处理器下全局EDF调度下的延迟界限。《实时系统》期刊，第32卷，第2期，pp. 133-189，2008年。
13 - P. Valente 和 G. Lipari. 多处理器上由EDF调度的软实时任务的延迟上限。第26届IEEE实时系统研讨会论文集，2005年。
14 - J. Erickson, U. Devi 和 S. Baruah. 全局EDF改进的延迟界限。第22届Euromicro实时系统会议论文集，2010年。
15 - G. Lipari, S. Baruah, 恒定带宽服务器中的未使用带宽贪婪回收，第12届IEEE Euromicro实时系统会议，2000年。
16 - L. Abeni, J. Lelli, C. Scordino, L. Palopoli, SCHED_DEADLINE下的贪婪CPU回收。实时Linux研讨会（RTLWS）论文集，德国杜塞尔多夫，2014年。
17 - L. Abeni, G. Lipari, A. Parri, Y. Sun, 多核CPU回收：并行还是顺序？。第31届年度ACM应用计算研讨会论文集，2016年
18 - J. Lelli, C. Scordino, L. Abeni, D. Faggioli, Linux内核中的截止期调度，软件：实践与经验，46(6): 821-839，2016年6月
19 - C. Scordino, L. Abeni, J. Lelli, Linux内核中的节能实时调度，第33届ACM/SIGAPP应用计算研讨会（SAC 2018），法国波城，2018年4月

4. 带宽管理
===========

如前所述，为了使-截止期调度有效且有用（即能够在“截止期”内提供“运行时间”时间单位），必须有一种方法来控制分配给各个任务的可用CPU时间片段。这通常称为“接纳控制”，如果不进行这种控制，则无法保证-截止期任务的实际调度。正如第3节所述，正确调度一组实时任务所需的条件是总利用率小于M。在谈论-截止期任务时，这意味着所有任务的运行时间和周期之间的比率之和应小于M。需要注意的是，运行时间/周期的比率等同于传统实时任务的利用率，并且也常被称为“带宽”。

用于控制可分配给-截止期任务的CPU带宽的接口类似于已用于带有实时组调度（即RT节流——参见Documentation/scheduler/sched-rt-group.rst）的-实时任务的接口，并基于位于procfs中的可读/写控制文件（用于系统范围内的设置）。请注意，针对-截止期任务的每组设置（通过cgroupfs控制）尚未定义，因为需要更多讨论以确定如何在任务组级别管理SCHED_DEADLINE带宽。

截止期带宽管理和RT节流的主要区别在于-截止期任务本身具有带宽（而-实时任务没有），因此我们不需要更高层级的节流机制来强制执行所需的带宽。换句话说，这意味着接口参数仅在接纳控制时使用（即用户调用sched_setattr()时）。然后根据实际任务的参数进行调度，以便为SCHED_DEADLINE任务分配CPU带宽时满足其粒度需求。因此，通过这个简单的接口，我们可以对-截止期任务的总利用率设置上限（即，\Sum (runtime_i / period_i) < global_dl_utilization_cap）。

4.1 系统范围内的设置
------------------------

系统范围内的设置配置在/proc虚拟文件系统下
目前，-rt 参数主要用于 -deadline 入口控制，并且 -deadline 运行时间会抵扣 -rt 运行时间。我们意识到这并不是最理想的方案；然而，现阶段有一个较小的接口是更好的选择，以便将来可以轻松地进行更改。理想的情况（见第5部分）是从 -deadline 服务器运行 -rt 任务；在这种情况下，-rt 带宽是 dl_bw 的直接子集。

这意味着，对于包含 M 个 CPU 的根域，只要它们的带宽总和不超过以下值，就可以创建 -deadline 任务：

   M * (sched_rt_runtime_us / sched_rt_period_us)

也可以禁用这种带宽管理逻辑，从而允许系统过载到任意程度。这可以通过将 -1 写入 /proc/sys/kernel/sched_rt_runtime_us 来实现。

4.2 任务接口
------------

要指定一个周期性或偶发性的任务，在每个实例中执行一定量的运行时间，并根据其自身的时间约束紧急性来调度，通常需要一种方式来声明：

  - （最大/典型）实例执行时间，
  - 相邻实例之间的最小间隔，
  - 每个实例必须完成的时间约束

因此：

  * 提供了一个新的 struct sched_attr，包含所有必要的字段；
  * 实现了用于操作它的新调度相关系统调用，即 sched_setattr() 和 sched_getattr()。

出于调试目的，可以通过 /proc/<pid>/sched 获取 SCHED_DEADLINE 任务的剩余运行时间和绝对截止时间（条目 dl.runtime 和 dl.deadline，两个值以纳秒为单位）。从生产代码中获取这些值的程序化方法正在讨论中。

4.3 默认行为
------------

SCHED_DEADLINE 带宽的默认值是 rt_runtime 等于 950000。当 rt_period 等于 1000000 时，默认情况下意味着 -deadline 任务最多可以使用 95%，乘以构成根域的 CPU 数量。

这意味着非 -deadline 任务至少会获得 5% 的 CPU 时间，并且 -deadline 任务将在相对于“deadline”参数的最坏情况延迟下获得其运行时间。如果 “deadline” = “period”，并且使用 cpuset 机制实现分区调度（见第5部分），则这种简单的带宽管理设置能够确定性地保证 -deadline 任务在每个周期内获得其运行时间。

最后，请注意，为了不危及入口控制，-deadline 任务不能进行 fork 操作。

4.4 sched_yield() 的行为
------------------------

当一个 SCHED_DEADLINE 任务调用 sched_yield() 时，它会放弃剩余的运行时间并立即被节流，直到下一个周期，其运行时间将得到补充（一个特殊的标志 dl_yielded 被设置并用于正确处理调用 sched_yield() 后的节流和运行时间补充）。
### 调度行为
`sched_yield()` 的这种行为使得任务恰好在下一个周期的开始时唤醒。此外，在将来带宽回收机制中，这可能很有用，因为 `sched_yield()` 将使剩余运行时间可供其他 SCHED_DEADLINE 任务进行回收。

### 5. 任务的 CPU 亲和性
=====================

- deadline 任务不能有小于其创建时所在整个 root_domain 的亲和性掩码。然而，可以通过 cpuset 设施指定亲和性（详见文档：Documentation/admin-guide/cgroup-v1/cpusets.rst）。

#### 5.1 SCHED_DEADLINE 和 cpusets 指南
------------------------------------

下面是一个简单的配置示例（将一个 deadline 任务绑定到 CPU0），使用 rt-app 创建一个 deadline 任务：

```sh
mkdir /dev/cpuset
mount -t cgroup -o cpuset cpuset /dev/cpuset
cd /dev/cpuset
mkdir cpu0
echo 0 > cpu0/cpuset.cpus
echo 0 > cpu0/cpuset.mems
echo 1 > cpuset.cpu_exclusive
echo 0 > cpuset.sched_load_balance
echo 1 > cpu0/cpuset.cpu_exclusive
echo 1 > cpu0/cpuset.mem_exclusive
echo $$ > cpu0/tasks
rt-app -t 100000:10000:d:0 -D5 # 此时指定任务亲和性实际上是多余的
```

### 6. 未来计划
=====================

仍然缺失的部分包括：

- 获取当前运行时间和绝对截止时间的方法；
- 对 deadline 继承的改进，特别是关于在非交互任务之间保留带宽隔离的可能性的研究，这一方面正在进行理论和实践研究，希望很快能产生一些演示代码；
- 基于 (c)group 的带宽管理，甚至可能是调度；
- 非 root 用户的访问控制（及相关安全问题处理），如何允许非特权用户使用这些机制，并防止非 root 用户“欺骗”系统？

正如已经讨论过的，我们还计划将此工作与 EDF 节流补丁合并[https://lore.kernel.org/r/cover.1266931410.git.fabio@helm.retis]，但目前仍处于合并的初步阶段，我们非常需要反馈来帮助决定其发展方向。

### 附录 A. 测试套件
=====================

SCHED_DEADLINE 策略可以轻松通过两个应用程序进行测试，这两个应用程序是更广泛的 Linux 调度器验证套件的一部分。该套件可在 GitHub 存储库中获取：https://github.com/scheduler-tools

第一个测试应用程序称为 rt-app，可用于启动具有特定参数的多个线程。rt-app 支持 SCHED_{OTHER,FIFO,RR,DEADLINE} 调度策略及其相关参数（例如，niceness、priority、runtime/deadline/period）。rt-app 是一个有价值的工具，因为它可以用来合成某些工作负载（可能模仿实际用例），并评估调度器在这种工作负载下的表现。这样，结果易于重现。

rt-app 可在以下地址获取：https://github.com/scheduler-tools/rt-app

线程参数可以从命令行指定，例如：

```sh
# rt-app -t 100000:10000:d -t 150000:20000:f:10 -D5
```

上述命令创建了两个线程。第一个由 SCHED_DEADLINE 调度，每 100ms 执行 10ms。第二个由 SCHED_FIFO 优先级 10 调度，每 150ms 执行 20ms。测试将持续总共 5 秒钟。

更有趣的是，可以通过 json 文件描述配置，并作为输入传递给 rt-app，例如：

```sh
# rt-app my_config.json
```

使用第二种方法可以指定的参数是命令行选项的超集。请参阅 rt-app 文档以获取更多详细信息 (`<rt-app-sources>/doc/*.json`)。

第二个测试应用程序是对 schedtool 的修改版本，称为 schedtool-dl，可用于为某个 pid/application 设置 SCHED_DEADLINE 参数。schedtool-dl 可在以下地址获取：https://github.com/scheduler-tools/schedtool-dl.git

使用方法非常简单：

```sh
# schedtool -E -t 10000000:100000000 -e ./my_cpuhog_app
```

使用此命令，my_cpuhog_app 将在一个每 100ms 运行 10ms 的 SCHED_DEADLINE 预留时间内运行（注意参数是以微秒表示的）。
你也可以使用 `schedtool` 为一个已经运行的应用程序创建预留，前提是你知道它的进程 ID（pid）：

```bash
# schedtool -E -t 10000000:100000000 my_app_pid
```

附录 B. 最小的 `main()` 函数
===============================

以下提供了一个简单的（丑陋的）自包含代码片段，展示了实时应用程序开发人员如何创建 SCHED_DEADLINE 预留：

```c
#define _GNU_SOURCE
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <linux/unistd.h>
#include <linux/kernel.h>
#include <linux/types.h>
#include <sys/syscall.h>
#include <pthread.h>

#define gettid() syscall(__NR_gettid)

#define SCHED_DEADLINE 6

/* XXX 使用正确的系统调用编号 */
#ifdef __x86_64__
#define __NR_sched_setattr 314
#define __NR_sched_getattr 315
#endif

#ifdef __i386__
#define __NR_sched_setattr 351
#define __NR_sched_getattr 352
#endif

#ifdef __arm__
#define __NR_sched_setattr 380
#define __NR_sched_getattr 381
#endif

static volatile int done;

struct sched_attr {
    __u32 size;

    __u32 sched_policy;
    __u64 sched_flags;

    /* SCHED_NORMAL, SCHED_BATCH */
    __s32 sched_nice;

    /* SCHED_FIFO, SCHED_RR */
    __u32 sched_priority;

    /* SCHED_DEADLINE (nsec) */
    __u64 sched_runtime;
    __u64 sched_deadline;
    __u64 sched_period;
};

int sched_setattr(pid_t pid, const struct sched_attr *attr, unsigned int flags) {
    return syscall(__NR_sched_setattr, pid, attr, flags);
}

int sched_getattr(pid_t pid, struct sched_attr *attr, unsigned int size, unsigned int flags) {
    return syscall(__NR_sched_getattr, pid, attr, size, flags);
}

void *run_deadline(void *data) {
    struct sched_attr attr;
    int x = 0;
    int ret;
    unsigned int flags = 0;

    printf("deadline thread started [%ld]\n", gettid());

    attr.size = sizeof(attr);
    attr.sched_flags = 0;
    attr.sched_nice = 0;
    attr.sched_priority = 0;

    /* 这里创建了一个 10ms/30ms 的预留 */
    attr.sched_policy = SCHED_DEADLINE;
    attr.sched_runtime = 10 * 1000 * 1000;
    attr.sched_period = attr.sched_deadline = 30 * 1000 * 1000;

    ret = sched_setattr(0, &attr, flags);
    if (ret < 0) {
        done = 0;
        perror("sched_setattr");
        exit(-1);
    }

    while (!done) {
        x++;
    }

    printf("deadline thread dies [%ld]\n", gettid());
    return NULL;
}

int main(int argc, char **argv) {
    pthread_t thread;

    printf("main thread [%ld]\n", gettid());

    pthread_create(&thread, NULL, run_deadline, NULL);

    sleep(10);

    done = 1;
    pthread_join(thread, NULL);

    printf("main dies [%ld]\n", gettid());
    return 0;
}
```
