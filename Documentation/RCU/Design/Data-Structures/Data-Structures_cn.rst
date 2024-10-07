==============================================
TREE_RCU数据结构之旅 [LWN.net]
==============================================

2016年12月18日

本文由Paul E. McKenney撰写

简介
================

本文档描述了RCU的主要数据结构及其相互之间的关系。

数据结构关系
================

RCU本质上是一个大型的状态机，其数据结构以一种方式维护状态，使得RCU读取器能够极其快速地执行，同时也能高效且高度可扩展地处理由更新者请求的RCU宽限期。
RCU更新者的效率和可扩展性主要通过一个组合树来提供，如下图所示：

.. kernel-figure:: BigTreeClassicRCU.svg

此图显示了一个包含“rcu_node”结构树的“rcu_state”结构。每个“rcu_node”树的叶节点最多关联有16个“rcu_data”结构，因此共有“NR_CPUS”数量的“rcu_data”结构，每个可能的CPU对应一个这样的结构。
如果需要的话，这个结构在启动时会进行调整，以处理常见的“nr_cpu_ids”远小于“NR_CPUs”的情况。
例如，许多Linux发行版将“NR_CPUs”设置为4096，这导致了一个三级的“rcu_node”树。
如果实际硬件只有16个CPU，RCU将在启动时进行调整，从而形成只有一个节点的“rcu_node”树。
此组合树的目的在于允许每CPU事件（如静默状态、动态空闲转换和CPU热插拔操作）被高效且可扩展地处理。
静默状态由每个CPU的“rcu_data”结构记录，而其他事件则由叶级“rcu_node”结构记录。
所有这些事件在树的每一层进行合并，直到最终在树根的“rcu_node”结构处完成宽限期。
一旦每个CPU（或者，在“CONFIG_PREEMPT_RCU”情况下，任务）都经过了一个静默状态，就可以在根部完成一个宽限期。
一旦宽限期完成，该事实的记录会向下传播到树中。

如图所示，在一个64位系统上，具有64个叶节点的两层树可以容纳1,024个CPU，根节点的扇出为64，叶节点的扇出为16。

+-----------------------------------------------------------------------+
| **快速测验**：                                                         |
+-----------------------------------------------------------------------+
| 为什么叶节点的扇出不是64？                                             |
+-----------------------------------------------------------------------+
| **答案**：                                                             |
+-----------------------------------------------------------------------+
| 因为影响叶级 `rcu_node` 结构的事件类型比树的更高层级更多。因此，如果 |
| 叶级 `rcu_node` 结构的扇出是64，则这些结构的 `->structures` 上的竞争 |
| 过于激烈。在各种系统的实验表明，对于 `rcu_node` 树的叶节点，扇出为16 |
| 是合适的。                                                             |
|                                                                        |
| 当然，如果系统拥有数百或数千个CPU，可能会发现非叶级 `rcu_node` 结构 |
| 的扇出也需要减少。这种减少可以在必要时轻松执行。与此同时，如果你正 |
| 在使用这样的系统，并且遇到非叶级 `rcu_node` 结构上的竞争问题，可以  |
| 使用 `CONFIG_RCU_FANOUT` 内核配置参数根据需要减少非叶级的扇出。     |
|                                                                        |
| 对于具有强烈NUMA特性的系统构建的内核可能也需要调整 `CONFIG_RCU_FANOUT` |
| 以使 `rcu_node` 结构的域与硬件边界对齐。然而，迄今为止还没有这种需  |
| 要。                                                                   |
+-----------------------------------------------------------------------+

如果你的系统有超过1,024个CPU（或在32位系统上有超过512个CPU），则RCU会自动增加树的层级。
例如，如果你疯狂到构建一个64位系统，拥有65,536个CPU，RCU将配置 `rcu_node` 树如下：

.. kernel-figure:: HugeTreeClassicRCU.svg

目前，RCU允许最多四层树，在64位系统上可容纳多达4,194,304个CPU，而在32位系统上则为524,288个CPU。
另一方面，你可以将 `CONFIG_RCU_FANOUT` 和 `CONFIG_RCU_FANOUT_LEAF` 设置为小至2，这将导致使用四层树进行16个CPU的测试。这对于在小型测试机器上测试大型系统的能力非常有用。
这种多级组合树使我们能够在RCU宽限期检测本质上是一个全局操作的情况下，获得分区带来的大部分性能和扩展性好处。关键在于，只有报告静默状态的最后一个CPU需要推进到树的下一级 `rcu_node` 结构。这意味着在叶级 `rcu_node` 结构中，每十六次访问中只有一次会向上推进。对于内部 `rcu_node` 结构，情况更为极端：每六十四次访问中只有一次会向上推进。由于绝大多数CPU不会向上推进，锁竞争在整个树中大致保持恒定。无论系统中有多少个CPU，每个宽限期内最多只有64个静默状态报告会一直推进到根 `rcu_node` 结构，从而确保该根 `rcu_node` 结构上的锁竞争保持在一个可接受的低水平。
实际上，组合树像一个大的减震器一样，无论系统负载如何，都能在所有树层上控制锁竞争。

RCU更新器通过注册RCU回调来等待正常的宽限期，这可以通过直接调用 `call_rcu()` 或间接通过 `synchronize_rcu()` 等方法实现。RCU回调由 `rcu_head` 结构表示，在等待宽限期期间被排队在 `rcu_data` 结构上，如以下图所示：

.. kernel-figure:: BigTreePreemptRCUBHdyntickCB.svg

此图展示了 `TREE_RCU` 和 `PREEMPT_RCU` 的主要数据结构之间的关系。较小的数据结构将在使用它们的算法中介绍。

请注意，上图中的每个数据结构都有自己的同步机制：
1. 每个 `rcu_state` 结构有一个锁和一个互斥锁，某些字段受相应根 `rcu_node` 结构锁保护。
2. 每个 `rcu_node` 结构有一个自旋锁。
3. `rcu_data` 中的字段专属于相应的CPU，尽管少数字段可以被其他CPU读写。
需要注意的是，不同的数据结构在任何时候对RCU的状态可能有非常不同的理解。举个例子，特定RCU宽限期的开始或结束意识会在数据结构中缓慢传播。这种缓慢传播对于RCU具有良好的读取侧性能是绝对必要的。如果这种分散的实现对你来说显得陌生，一个有用的技巧是将这些数据结构的每个实例视为不同的人，每个人对现实都有略有不同的看法。这些数据结构的一般作用如下：

1. `rcu_state`: 这个结构形成了`rcu_node`和`rcu_data`结构之间的连接，跟踪宽限期，作为CPU热插拔事件导致的回调函数的短期存储库，维护`rcu_barrier()`状态，跟踪加速宽限期状态，并在宽限期过长时用于强制静默状态。
2. `rcu_node`: 这个结构形成了从叶节点到根节点的静默状态信息传播树，并且也从根节点到叶节点传播宽限期信息。它提供了本地副本的宽限期状态，以便以同步的方式访问这些信息而不受全局锁定带来的可扩展性限制。在`CONFIG_PREEMPT_RCU`内核中，它管理当前RCU读取侧临界区中被阻塞的任务列表。在`CONFIG_PREEMPT_RCU`和`CONFIG_RCU_BOOST`配置下，它管理每个`rcu_node`的优先级提升内核线程（kthreads）及其状态。最后，它记录CPU热插拔状态，以确定在特定宽限期内应忽略哪些CPU。
3. `rcu_data`: 这个每CPU的结构是检测静默状态和RCU回调排队的核心。它还跟踪其与相应叶节点`rcu_node`结构的关系，以更高效地向上传播静默状态到`rcu_node`组合树。与`rcu_node`结构类似，它提供了本地副本的宽限期信息，允许相应的CPU以同步方式免费访问这些信息。最后，这个结构记录对应CPU过去的动态空闲状态并跟踪统计信息。
4. `rcu_head`: 这个结构表示RCU回调，并且是唯一由RCU用户分配和管理的结构。`rcu_head`结构通常嵌入在RCU保护的数据结构中。

如果你只需要了解RCU的数据结构是如何关联的，那么你已经完成了。否则，以下各节将提供更多关于`rcu_state`、`rcu_node`和`rcu_data`数据结构的详细信息。

`rcu_state` 结构
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`rcu_state`结构是代表系统中RCU状态的基础结构。这个结构形成了`rcu_node`和`rcu_data`结构之间的连接，跟踪宽限期，包含用于与CPU热插拔事件同步的锁，并维护当宽限期过长时用于强制静默状态的状态。

下面讨论了`rcu_state`结构的一些字段，单独或成组地进行讨论。更多专业字段将在它们使用的讨论中涉及。

与`rcu_node`和`rcu_data`结构的关系
'''''''''''''''''''''''''''''''''''''''''''''''

`rcu_state`结构的这一部分声明如下：

::

    1   struct rcu_node node[NUM_RCU_NODES];
    2   struct rcu_node *level[NUM_RCU_LVLS + 1];
    3   struct rcu_data __percpu *rda;

+-----------------------------------------------------------------------+
| **快速问答**：                                                        |
+-----------------------------------------------------------------------+
| 等一下！你说`rcu_node`结构形成了一棵树，但它们被声明为一个平坦数组！为什么？ |
+-----------------------------------------------------------------------+
| **答案**：                                                            |
+-----------------------------------------------------------------------+
| 树在数组中布局。数组中的第一个节点是头部，接下来的一组节点是头部节点的子节点，以此类推，直到数组的最后一组节点是叶子节点。 |
| 请参阅以下图示来了解其工作原理。                                      |
+-----------------------------------------------------------------------+

`rcu_node`树嵌入在`->node[]`数组中，如以下图所示：

.. kernel-figure:: TreeMapping.svg

这种映射的一个有趣结果是，树的广度优先遍历可以通过简单的数组线性扫描来实现，实际上`rcu_for_each_node_breadth_first()`宏就是这样做的。该宏在宽限期的开始和结束时使用。

`->level`数组的每个条目引用树中相应层级的第一个`rcu_node`结构，例如，如下所示：

.. kernel-figure:: TreeMappingLevel.svg

数组的第零个元素引用根`rcu_node`结构，第一个元素引用根`rcu_node`的第一个子节点，最后第二个元素引用第一个叶子`rcu_node`结构。

无论如何，如果你绘制的树是树形而不是数组形，很容易绘制出平面表示：

.. kernel-figure:: TreeLevel.svg

最后，`->rda`字段引用指向相应CPU的`rcu_data`结构的每CPU指针。

所有这些字段在初始化完成后都是常量，因此不需要保护。
### 宽限期追踪

这部分 `rcu_state` 结构体的声明如下：

```
    1   unsigned long gp_seq;
```

RCU 的宽限期是编号的，`->gp_seq` 字段包含当前宽限期的序列号。最低两位表示当前宽限期的状态，其中零表示尚未开始，一表示正在进行中。换句话说，如果 `->gp_seq` 的最低两位为零，则 RCU 处于空闲状态。其他任何值都表示存在问题。该字段由根 `rcu_node` 结构体中的 `->lock` 字段保护。

在 `rcu_node` 和 `rcu_data` 结构体中也有 `->gp_seq` 字段。`rcu_state` 结构体中的字段代表最新值，而其他结构体中的字段则用于分布式检测宽限期的开始和结束。这些值从 `rcu_state` 流向 `rcu_node`（从树的根到叶），再到 `rcu_data`。

#### 杂项

这部分 `rcu_state` 结构体的声明如下：

```
    1   unsigned long gp_max;
    2   char abbr;
    3   char *name;
```

`->gp_max` 字段跟踪最长宽限期的持续时间（以时钟节拍为单位）。它受根 `rcu_node` 的 `->lock` 字段保护。

`->name` 和 `->abbr` 字段区分抢占式 RCU（“rcu_preempt” 和 “p”）和非抢占式 RCU（“rcu_sched” 和 “s”）。这些字段用于诊断和跟踪目的。

### `rcu_node` 结构体

`rcu_node` 结构体形成一个组合树，该树从叶节点向根节点传播静默状态信息，并且从根节点向下传播宽限期信息。它们提供了本地副本的宽限期状态，以便以同步方式访问这些信息而不受全局锁定带来的可扩展性限制。在 `CONFIG_PREEMPT_RCU` 内核中，它们管理在当前 RCU 读侧临界区中被阻塞的任务列表。在 `CONFIG_PREEMPT_RCU` 和 `CONFIG_RCU_BOOST` 配置下，它们管理每个 `rcu_node` 的优先级提升内核线程（kthreads）及其状态。最后，它们记录 CPU 热插拔状态，以确定在给定宽限期内应忽略哪些 CPU。

下面将分别讨论 `rcu_node` 结构体的各个字段。

#### 连接到组合树

这部分 `rcu_node` 结构体的声明如下：

```
    1   struct rcu_node *parent;
    2   u8 level;
    3   u8 grpnum;
    4   unsigned long grpmask;
    5   int grplo;
    6   int grphi;
```

`->parent` 指针引用树中上一级的 `rcu_node`，对于根 `rcu_node` 则为 `NULL`。RCU 实现大量使用此字段将静默状态向上推送到树中。`->level` 字段给出树中的层级，其中根节点位于第零层，其子节点位于第一层，依此类推。`->grpnum` 字段给出该节点在其父节点子节点中的位置，因此在 32 位系统上这个数字范围在 0 到 31 之间，在 64 位系统上范围在 0 到 63 之间。`->level` 和 `->grpnum` 字段仅在初始化期间和跟踪时使用。`->grpmask` 字段是 `->grpnum` 的位掩码对应项，因此始终只有一个位被设置。此掩码用于清除其父节点位掩码中对应的位，这些位掩码将在后面描述。最后，`->grplo` 和 `->grphi` 字段分别包含由该 `rcu_node` 结构体服务的最低编号和最高编号的 CPU。

所有这些字段都是常量，因此不需要任何同步。
同步
'''''''''''''''

``rcu_node`` 结构的这个字段声明如下：

::

     1   raw_spinlock_t lock;

该字段用于保护此结构中的其他字段，除非另有说明。也就是说，出于跟踪目的，可以在不加锁的情况下访问此结构中的所有字段。是的，这可能会导致跟踪混乱，但比起因不确定性错误而消失，一些跟踪混乱还是可以接受的。
.. _grace-period-tracking-1:

优雅周期跟踪
'''''''''''''''''''''

``rcu_node`` 结构的这部分声明如下：

::

     1   unsigned long gp_seq;
     2   unsigned long gp_seq_needed;

``rcu_node`` 结构的 ``->gp_seq`` 字段与 ``rcu_state`` 结构中同名的字段相对应。它们每个可能落后于其对应的 ``rcu_state`` 字段一步。如果某个 ``rcu_node`` 结构的 ``->gp_seq`` 字段的最低两位为零，则表明该 ``rcu_node`` 结构认为 RCU 处于空闲状态。
每个 ``rcu_node`` 结构的 ``->gp_seq`` 字段在每个优雅周期的开始和结束时更新。
``->gp_seq_needed`` 字段记录了对应 ``rcu_node`` 结构所见的最远的优雅周期请求。当 ``->gp_seq`` 字段的值等于或超过 ``->gp_seq_needed`` 字段的值时，请求被认为已满足。
+-----------------------------------------------------------------------+
| **快速问答**：                                                        |
+-----------------------------------------------------------------------+
| 假设这个 ``rcu_node`` 结构很长时间没有看到请求。``->gp_seq`` 字段的循环不会导致问题吗？ |
+-----------------------------------------------------------------------+
| **答案**：                                                            |
+-----------------------------------------------------------------------+
| 不会，因为如果 ``->gp_seq_needed`` 字段落后于 ``->gp_seq`` 字段，它将在优雅周期结束时更新。因此，即使有循环，模运算比较始终能得到正确答案。             |
+-----------------------------------------------------------------------+

静默状态跟踪
''''''''''''''''''''''''

这些字段管理静默状态在组合树中的传播
``rcu_node`` 结构的这部分字段声明如下：

::

     1   unsigned long qsmask;
     2   unsigned long expmask;
     3   unsigned long qsmaskinit;
     4   unsigned long expmaskinit;

``->qsmask`` 字段跟踪当前正常优雅周期下此 ``rcu_node`` 结构的哪些子节点仍需要报告静默状态。这些子节点会在相应的位上有一个值 1。需要注意的是，叶子 ``rcu_node`` 结构应视为其子节点为 ``rcu_data`` 结构。
类似地，``->expmask`` 字段跟踪当前加速优雅周期下此 ``rcu_node`` 结构的哪些子节点仍需要报告静默状态。加速优雅周期具有与正常优雅周期相同的概念属性，但加速实现接受极高的 CPU 开销以获得更低的优雅周期延迟，例如，消耗几十微秒的 CPU 时间将优雅周期从毫秒级缩短到几十微秒。``->qsmaskinit`` 字段跟踪此 ``rcu_node`` 结构的哪些子节点覆盖至少一个在线 CPU。
此掩码用于初始化 ``->qsmask``，而 ``->expmaskinit`` 用于初始化 ``->expmask``，分别在正常优雅周期和加速优雅周期的开始。
+-----------------------------------------------------------------------+
| **快速问答**：                                                        |
+-----------------------------------------------------------------------+
| 为什么这些位掩码需要锁定保护？难道你没听说过原子指令吗？            |
+-----------------------------------------------------------------------+
| **答案**：                                                            |
+-----------------------------------------------------------------------+
| 无锁优雅周期计算！多么诱人的可能性！但请考虑以下事件序列：             |
|                                                                       |
| #. CPU 0 已经处于 dyntick-idle 模式一段时间。当它醒来时，注意到当前 RCU 优雅周期需要它报告，因此设置了调度时钟中断可以找到的标志。 |
| #. 同时，CPU 1 正在运行 ``force_quiescent_state()``，并注意到 CPU 0 处于 dyntick-idle 模式，这被视为扩展静默状态。              |
| #. CPU 0 的调度时钟中断在 RCU 读端临界区中间触发，并注意到 RCU 核心需要某些操作，因此开始处理 RCU 软中断。                       |
| #. CPU 0 的软中断处理程序执行完毕，正准备向上报告其静默状态。                                   |
| #. 但是 CPU 1 抢先一步，完成当前优雅周期并开始一个新的优雅周期。                                  |
| #. CPU 0 现在为错误的优雅周期报告其静默状态。那个优雅周期可能会在 RCU 读端临界区之前结束。如果发生这种情况，灾难将随之而来。       |
|                                                                       |
| 因此，锁定绝对必要，以便协调位清除与 ``->gp_seq`` 中优雅周期序列号的更新。                           |
+-----------------------------------------------------------------------+

阻塞任务管理
'''''''''''''''''''''''

``PREEMPT_RCU`` 允许任务在其 RCU 读端临界区中途被抢占，并且这些任务必须显式跟踪。
关于为何以及如何进行跟踪的具体细节将在另一篇关于 RCU 读端处理的文章中详细讨论。目前，只需知道 ``rcu_node`` 结构跟踪它们即可。
```
1   struct list_head blkd_tasks;
2   struct list_head *gp_tasks;
3   struct list_head *exp_tasks;
4   bool wait_blkd_tasks;
```

``->blkd_tasks`` 字段是被阻塞和抢占任务列表的头。随着任务在 RCU 读端临界区中进行上下文切换，其 `task_struct` 结构通过 `task_struct` 的 `->rcu_node_entry` 字段被加入到对应 CPU 上执行出站上下文切换的叶 `rcu_node` 结构的 `->blkd_tasks` 列表头部。当这些任务退出它们的 RCU 读端临界区时，它们会从该列表中移除自己。因此，这个列表按时间逆序排列，如果其中一个任务阻塞了当前的优雅周期，则所有后续任务也必须阻塞同一个优雅周期。因此，指向该列表的一个指针足以跟踪所有阻塞特定优雅周期的任务。正常优雅周期的指针存储在 `->gp_tasks` 中，快速优雅周期的指针存储在 `->exp_tasks` 中。如果没有任何优雅周期正在进行或没有阻塞任务阻止优雅周期完成，则这两个字段为 `NULL`。如果这两个指针中的任何一个引用了一个从 `->blkd_tasks` 列表中移除自己的任务，那么该任务必须将指针推进到列表中的下一个任务，或者如果没有后续任务则将指针设置为 `NULL`。

例如，假设任务 T1、T2 和 T3 都绑定到了系统中编号最大的 CPU 上。如果任务 T1 在 RCU 读端临界区中被阻塞，然后开始一个快速优雅周期，接着任务 T2 在 RCU 读端临界区中被阻塞，然后开始一个正常优雅周期，最后任务 T3 在 RCU 读端临界区中被阻塞，那么最后一个叶 `rcu_node` 结构的阻塞任务列表状态如下所示：

.. kernel-figure:: blkd_task.svg

任务 T1 阻塞了两个优雅周期，任务 T2 只阻塞了正常优雅周期，而任务 T3 不阻塞任何优雅周期。请注意，这些任务在恢复执行后不会立即从列表中移除自己。相反，它们会一直留在列表中直到它们执行结束 RCU 读端临界区的最外层 `rcu_read_unlock()`。

``->wait_blkd_tasks`` 字段指示当前优雅周期是否等待一个被阻塞的任务。

### `rcu_node` 数组的大小

``rcu_node`` 数组通过一系列 C 预处理表达式来确定大小，如下所示：

```c
1 #ifdef CONFIG_RCU_FANOUT
2 #define RCU_FANOUT CONFIG_RCU_FANOUT
3 #else
4 # ifdef CONFIG_64BIT
5 # define RCU_FANOUT 64
6 # else
7 # define RCU_FANOUT 32
8 # endif
9 #endif
10
11 #ifdef CONFIG_RCU_FANOUT_LEAF
12 #define RCU_FANOUT_LEAF CONFIG_RCU_FANOUT_LEAF
13 #else
14 # ifdef CONFIG_64BIT
15 # define RCU_FANOUT_LEAF 64
16 # else
17 # define RCU_FANOUT_LEAF 32
18 # endif
19 #endif
20
21 #define RCU_FANOUT_1        (RCU_FANOUT_LEAF)
22 #define RCU_FANOUT_2        (RCU_FANOUT_1 * RCU_FANOUT)
23 #define RCU_FANOUT_3        (RCU_FANOUT_2 * RCU_FANOUT)
24 #define RCU_FANOUT_4        (RCU_FANOUT_3 * RCU_FANOUT)
25
26 #if NR_CPUS <= RCU_FANOUT_1
27 #  define RCU_NUM_LVLS        1
28 #  define NUM_RCU_LVL_0        1
29 #  define NUM_RCU_NODES        NUM_RCU_LVL_0
30 #  define NUM_RCU_LVL_INIT    { NUM_RCU_LVL_0 }
31 #  define RCU_NODE_NAME_INIT  { "rcu_node_0" }
32 #  define RCU_FQS_NAME_INIT   { "rcu_node_fqs_0" }
33 #  define RCU_EXP_NAME_INIT   { "rcu_node_exp_0" }
34 #elif NR_CPUS <= RCU_FANOUT_2
35 #  define RCU_NUM_LVLS        2
36 #  define NUM_RCU_LVL_0        1
37 #  define NUM_RCU_LVL_1        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_1)
38 #  define NUM_RCU_NODES        (NUM_RCU_LVL_0 + NUM_RCU_LVL_1)
39 #  define NUM_RCU_LVL_INIT    { NUM_RCU_LVL_0, NUM_RCU_LVL_1 }
40 #  define RCU_NODE_NAME_INIT  { "rcu_node_0", "rcu_node_1" }
41 #  define RCU_FQS_NAME_INIT   { "rcu_node_fqs_0", "rcu_node_fqs_1" }
42 #  define RCU_EXP_NAME_INIT   { "rcu_node_exp_0", "rcu_node_exp_1" }
43 #elif NR_CPUS <= RCU_FANOUT_3
44 #  define RCU_NUM_LVLS        3
45 #  define NUM_RCU_LVL_0        1
46 #  define NUM_RCU_LVL_1        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_2)
47 #  define NUM_RCU_LVL_2        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_1)
48 #  define NUM_RCU_NODES        (NUM_RCU_LVL_0 + NUM_RCU_LVL_1 + NUM_RCU_LVL_2)
49 #  define NUM_RCU_LVL_INIT    { NUM_RCU_LVL_0, NUM_RCU_LVL_1, NUM_RCU_LVL_2 }
50 #  define RCU_NODE_NAME_INIT  { "rcu_node_0", "rcu_node_1", "rcu_node_2" }
51 #  define RCU_FQS_NAME_INIT   { "rcu_node_fqs_0", "rcu_node_fqs_1", "rcu_node_fqs_2" }
52 #  define RCU_EXP_NAME_INIT   { "rcu_node_exp_0", "rcu_node_exp_1", "rcu_node_exp_2" }
53 #elif NR_CPUS <= RCU_FANOUT_4
54 #  define RCU_NUM_LVLS        4
55 #  define NUM_RCU_LVL_0        1
56 #  define NUM_RCU_LVL_1        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_3)
57 #  define NUM_RCU_LVL_2        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_2)
58 #  define NUM_RCU_LVL_3        DIV_ROUND_UP(NR_CPUS, RCU_FANOUT_1)
59 #  define NUM_RCU_NODES        (NUM_RCU_LVL_0 + NUM_RCU_LVL_1 + NUM_RCU_LVL_2 + NUM_RCU_LVL_3)
60 #  define NUM_RCU_LVL_INIT    { NUM_RCU_LVL_0, NUM_RCU_LVL_1, NUM_RCU_LVL_2, NUM_RCU_LVL_3 }
61 #  define RCU_NODE_NAME_INIT  { "rcu_node_0", "rcu_node_1", "rcu_node_2", "rcu_node_3" }
62 #  define RCU_FQS_NAME_INIT   { "rcu_node_fqs_0", "rcu_node_fqs_1", "rcu_node_fqs_2", "rcu_node_fqs_3" }
63 #  define RCU_EXP_NAME_INIT   { "rcu_node_exp_0", "rcu_node_exp_1", "rcu_node_exp_2", "rcu_node_exp_3" }
64 #else
65 # error "CONFIG_RCU_FANOUT insufficient for NR_CPUS"
66 #endif
```

``rcu_node`` 结构的最大层级数目前限制为四层，如第 21-24 行和随后的“if”语句结构所示。对于 32 位系统，这允许最多 16 * 32 * 32 * 32 = 524,288 个 CPU，这应该至少在未来几年内足够使用。对于 64 位系统，允许 16 * 64 * 64 * 64 = 4,194,304 个 CPU，这应该可以支持未来十年左右的时间。这个四层树还允许使用 `CONFIG_RCU_FANOUT=8` 构建的内核支持最多 4096 个 CPU，这可能对具有每个插槽八个 CPU 的非常大的系统有用（但请注意，还没有人展示过由于插槽与 `rcu_node` 边界不一致导致的任何可测量性能下降）。此外，构建具有完整四层 `rcu_node` 树的内核可以更好地测试 RCU 的合并树代码。

``RCU_FANOUT`` 符号控制 `rcu_node` 树的每个非叶节点级别允许的最大子节点数量。如果未指定 `CONFIG_RCU_FANOUT` Kconfig 选项，则根据系统的字长来设置它，这也是 Kconfig 的默认值。

``RCU_FANOUT_LEAF`` 符号控制每个叶 `rcu_node` 结构处理的 CPU 数量。经验表明，允许每个叶 `rcu_node` 结构处理 64 个 CPU（如 64 位系统中 `->qsmask` 字段所允许的那样）会导致对叶 `rcu_node` 结构的 `->lock` 字段的过度争用。因此，默认情况下每个叶 `rcu_node` 结构处理的 CPU 数量限制为 16。如果未指定 `CONFIG_RCU_FANOUT_LEAF`，则选择的值基于系统的字长，与 `CONFIG_RCU_FANOUT` 相同。第 11-19 行执行此计算。

第 21-24 行计算单层（包含一个 `rcu_node` 结构）、两层、三层和四层 `rcu_node` 树分别支持的最大 CPU 数量，给定由 `RCU_FANOUT` 和 `RCU_FANOUT_LEAF` 指定的扇出值。

这些 CPU 数量被保留到 C 预处理器变量 `RCU_FANOUT_1`、`RCU_FANOUT_2`、`RCU_FANOUT_3` 和 `RCU_FANOUT_4` 中。

这些变量用于控制跨越第 26-66 行的 C 预处理器 `#if` 语句，该语句计算树的每一级所需的 `rcu_node` 结构的数量以及所需层级的数量。层级数量被放置在 C 预处理器变量 `NUM_RCU_LVLS` 中，由第 27、35、44 和 54 行设置。树顶层的 `rcu_node` 结构数量始终为 1，并且这个值无条件地放置在 `NUM_RCU_LVL_0` 中，由第 28、36、45 和 55 行设置。其余层级（如果有）的 `rcu_node` 树通过将最大 CPU 数量除以从当前层级到下层支持的扇出并向上取整来计算。这项计算由第 37、46-47 和 56-58 行完成。第 31-33、40-42、50-52 和 62-63 行创建锁依赖锁类名称的初始化器。最后，第 64-66 行在最大 CPU 数量超出指定扇出的情况下产生错误。
```
``rcu_segcblist`` 结构
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``rcu_segcblist`` 结构维护了一个分段的回调列表，如下所示：

::

    1 #define RCU_DONE_TAIL        0
    2 #define RCU_WAIT_TAIL        1
    3 #define RCU_NEXT_READY_TAIL  2
    4 #define RCU_NEXT_TAIL        3
    5 #define RCU_CBLIST_NSEGS     4
    6
    7 struct rcu_segcblist {
    8   struct rcu_head *head;
    9   struct rcu_head **tails[RCU_CBLIST_NSEGS];
   10   unsigned long gp_seq[RCU_CBLIST_NSEGS];
   11   long len;
   12   long len_lazy;
   13 };

分段说明如下：

1. ``RCU_DONE_TAIL``：回调函数的宽限期已结束。这些回调函数已经准备好被调用。
2. ``RCU_WAIT_TAIL``：等待当前宽限期的回调函数。注意，不同的 CPU 可能对当前宽限期有不同的理解，因此需要 ``->gp_seq`` 字段。
3. ``RCU_NEXT_READY_TAIL``：等待下一个宽限期开始的回调函数。
4. ``RCU_NEXT_TAIL``：尚未与任何宽限期关联的回调函数。

``->head`` 指针指向列表中的第一个回调函数，或者如果列表中没有回调函数则为 ``NULL``（这并不意味着列表为空）。

``->tails[]`` 数组中的每个元素引用了对应分段列表中最后一个回调函数的 ``->next`` 指针，或者如果该分段及其所有之前的分段都为空，则引用列表的 ``->head`` 指针。如果对应的分段为空，但某些之前的分段不为空，则数组元素与其前一个元素相同。较旧的回调函数更接近列表头部，而新的回调函数添加到列表尾部。下面的图展示了 ``->head`` 指针、``->tails[]`` 数组和回调函数之间的关系：

.. kernel-figure:: nxtlist.svg

在图中，``->head`` 指针指向列表中的第一个 RCU 回调函数。``->tails[RCU_DONE_TAIL]`` 数组元素指向 ``->head`` 指针本身，表示没有任何回调函数准备就绪。``->tails[RCU_WAIT_TAIL]`` 数组元素指向回调函数 CB 2 的 ``->next`` 指针，表示 CB 1 和 CB 2 都在等待当前的宽限期，尽管可能存在关于哪个宽限期是当前宽限期的不同意见。``->tails[RCU_NEXT_READY_TAIL]`` 数组元素指向与 ``->tails[RCU_WAIT_TAIL]`` 相同的 RCU 回调函数，表示没有回调函数在等待下一个 RCU 宽限期。``->tails[RCU_NEXT_TAIL]`` 数组元素指向 CB 4 的 ``->next`` 指针，表示所有剩余的 RCU 回调函数尚未分配到 RCU 宽限期。请注意，除非回调函数列表为空，否则 ``->tails[RCU_NEXT_TAIL]`` 数组元素始终指向最后一个 RCU 回调函数的 ``->next`` 指针，在这种情况下它指向 ``->head`` 指针。

``->tails[RCU_NEXT_TAIL]`` 数组元素有一个额外的重要特殊情况：当此列表被禁用时，它可以为 ``NULL``。当相应的 CPU 离线或相应的 CPU 的回调函数被卸载到 kthread 时，列表会被禁用，这两者都在其他地方描述过。

CPU 会随着宽限期的推进将回调函数从 ``RCU_NEXT_TAIL`` 移动到 ``RCU_NEXT_READY_TAIL``，再到 ``RCU_WAIT_TAIL``，最后到 ``RCU_DONE_TAIL`` 分段。

``->gp_seq[]`` 数组记录了与列表分段对应的宽限期编号。这使得不同的 CPU 对当前宽限期有不同的理解，但仍能避免提前调用它们的回调函数。特别是，这允许长时间处于空闲状态的 CPU 在重新唤醒后确定哪些回调函数可以被调用。

``->len`` 计数器包含 ``->head`` 中的回调函数数量，而 ``->len_lazy`` 包含那些已知仅释放内存且其调用可以安全延迟的回调函数数量。
...重要...

   是`->len`字段决定了`rcu_segcblist`结构是否有关联的回调函数，而不是`->head`指针。原因是所有准备调用的回调函数（即在`RCU_DONE_TAIL`段中的那些）在回调调用时（`rcu_do_batch`）会一次性提取出来，因此如果`rcu_segcblist`中没有未完成的回调函数，`->head`可能会被设置为NULL。如果必须推迟回调调用，例如因为高优先级进程在这个CPU上刚刚被唤醒，则剩余的回调函数将重新放回`RCU_DONE_TAIL`段，`->head`再次指向该段的起始位置。简而言之，即使CPU一直有回调函数存在，`head`字段也可能短暂地为`NULL`。因此，测试`->head`指针是否为`NULL`是不合适的。
相反，`->len`和`->len_lazy`计数器仅在相应的回调函数被调用后才进行调整。这意味着`->len`计数器为零仅当`rcu_segcblist`结构确实没有回调函数。当然，对`->len`计数器的离CPU采样需要谨慎使用适当的同步机制，例如内存屏障。这种同步可能会稍微复杂一些，特别是在`rcu_barrier()`的情况下。

`rcu_data`结构
~~~~~~~~~~~~~~

`rcu_data`维护了RCU子系统的每个CPU状态。除非另有说明，否则此结构中的字段只能从相应的CPU（和跟踪）访问。此结构是检测静默状态和RCU回调排队的核心。它还跟踪与相应的叶节点`rcu_node`结构的关系，以便更高效地传播静默状态到`rcu_node`组合树。像`rcu_node`结构一样，它提供了本地副本的宽限期信息，允许从相应CPU免费同步访问这些信息。最后，此结构记录了相应CPU过去的动态空闲状态，并跟踪统计信息。接下来的部分将单独讨论`rcu_data`结构的各个字段。

与其他数据结构的连接
'''''''''''''''''''''''''''''''''''

`rcu_data`结构的这一部分如下声明：

::

     1   int cpu;
     2   struct rcu_node *mynode;
     3   unsigned long grpmask;
     4   bool beenonline;

`->cpu`字段包含相应CPU的编号，而`->mynode`字段引用相应的`rcu_node`结构。`->mynode`用于在组合树中传播静默状态。这两个字段是常量，因此不需要同步。

`->grpmask`字段表示对应于此`rcu_data`结构的`->mynode->qsmask`中的位，并且在传播静默状态时也使用该字段。`->beenonline`标志在相应CPU上线时设置，这意味着调试跟踪不必输出任何未设置此标志的`rcu_data`结构。

静默状态和宽限期跟踪
'''''''''''''''''''''''''''''''''''''''''

`rcu_data`结构的这一部分如下声明：

::

     1   unsigned long gp_seq;
     2   unsigned long gp_seq_needed;
     3   bool cpu_no_qs;
     4   bool core_needs_qs;
     5   bool gpwrap;

`->gp_seq`字段是`rcu_state`和`rcu_node`结构中同名字段的对应项。`->gp_seq_needed`字段是`rcu_node`结构中同名字段的对应项。它们可能各自落后其对应的`rcu_node`一个或更多，但在`CONFIG_NO_HZ_IDLE`和`CONFIG_NO_HZ_FULL`内核中，对于处于动态空闲模式的CPU，可以任意滞后（但在退出动态空闲模式时，这些计数器将赶上）。如果给定`rcu_data`结构的`->gp_seq`的最低两位为零，则此`rcu_data`结构认为RCU处于空闲状态。
+-----------------------------------------------------------------------+
| **快速问答**：                                                        |
+-----------------------------------------------------------------------+
| 所有这些宽限期数字的复制只会导致巨大的混乱。为什么不只保留一个全局序列号就完了呢？|
+-----------------------------------------------------------------------+
| **答案**：                                                            |
+-----------------------------------------------------------------------+
| 因为如果只有一个全局序列号，则需要一个全局锁来安全地访问和更新它。如果我们不打算有一个全局锁，就需要仔细管理每个节点上的数字。回想之前快速问答的答案，将先前采样的静默状态应用到错误的宽限期上的后果是非常严重的。|
+-----------------------------------------------------------------------+

`->cpu_no_qs`标志表示CPU尚未通过静默状态，而`->core_needs_qs`标志表示RCU核心需要来自相应CPU的静默状态。

`->gpwrap`字段表示相应CPU保持空闲时间过长，以至于`gp_seq`计数器有溢出的风险，这将导致CPU在其下一次退出空闲时忽略其计数器的值。
RCU 回调处理
'''''''''''''''''''''

在没有 CPU 热插拔事件的情况下，RCU 回调由注册它们的同一个 CPU 调用。这纯粹是一个缓存局部性优化：回调可以并且确实会在除了注册它的 CPU 之外的其他 CPU 上被调用。毕竟，如果注册某个回调的 CPU 在回调能够被调用之前已经下线，那么实际上别无选择。这部分 `rcu_data` 结构体声明如下：

::

    1 struct rcu_segcblist cblist;
    2 long qlen_last_fqs_check;
    3 unsigned long n_cbs_invoked;
    4 unsigned long n_nocbs_invoked;
    5 unsigned long n_cbs_orphaned;
    6 unsigned long n_cbs_adopted;
    7 unsigned long n_force_qs_snap;
    8 long blimit;

`->cblist` 结构是前面描述过的分段回调列表。每当 CPU 注意到另一个 RCU 宽限期已完成时，它会推进其 `rcu_data` 结构中的回调。CPU 通过检测其 `rcu_data` 结构的 `->gp_seq` 字段值与其叶子 `rcu_node` 结构的不同来发现 RCU 宽限期的完成。回想一下，每个 `rcu_node` 结构的 `->gp_seq` 字段在每个宽限期的开始和结束时都会更新。
`->qlen_last_fqs_check` 和 `->n_force_qs_snap` 协调了当回调列表过长时从 `call_rcu()` 及其相关函数强制进入静默状态的操作。
`->n_cbs_invoked`、`->n_cbs_orphaned` 和 `->n_cbs_adopted` 字段分别统计了被调用的回调数量、当前 CPU 下线时发送给其他 CPU 的回调数量以及当其他 CPU 下线时从其他 CPU 接收到的回调数量。`->n_nocbs_invoked` 在 CPU 的回调被卸载到 kthread 时使用。
最后，`->blimit` 计数器是在给定时间可调用的最大 RCU 回调数量。

动态滴答-空闲处理
'''''''''''''''''''''

这部分 `rcu_data` 结构体声明如下：

::

     1   int dynticks_snap;
     2   unsigned long dynticks_fqs;

`->dynticks_snap` 字段用于在强制静默状态时获取相应 CPU 的动态滴答空闲状态快照，因此可以从其他 CPU 访问。最后，`->dynticks_fqs` 字段用于计算该 CPU 被确定为空闲状态的次数，并用于跟踪和调试目的。
这部分 `rcu_data` 结构体声明如下：

::

     1   long dynticks_nesting;
     2   long dynticks_nmi_nesting;
     3   atomic_t dynticks;
     4   bool rcu_need_heavy_qs;
     5   bool rcu_urgent_qs;

这些字段在 `rcu_data` 结构中维护相应 CPU 的动态滴答空闲状态。除非另有说明，这些字段只能从相应 CPU（以及跟踪）访问。
`->dynticks_nesting` 字段计算进程执行的嵌套深度，因此在正常情况下此计数器的值为零或一。NMI、IRQ 和追踪器则由 `->dynticks_nmi_nesting` 字段计数。由于 NMI 无法屏蔽，对该变量的更改必须谨慎进行，使用 Andy Lutomirski 提供的算法。初始的空闲转换增加一次，嵌套转换增加两次，因此五层嵌套表示为 `->dynticks_nmi_nesting` 值为九。因此，这个计数器可以被认为是在计算该 CPU 不能进入动态滴答空闲模式的原因数量，除了进程级别的转换。
然而，事实证明，在非空闲内核上下文中运行时，Linux 内核完全有能力进入永远不会退出的中断处理器，反之亦然。因此，每当 `->dynticks_nesting` 字段从零递增时，`->dynticks_nmi_nesting` 字段将设置为一个较大的正数；而当 `->dynticks_nesting` 字段递减回零时，`->dynticks_nmi_nesting` 字段将设置为零。假设嵌套中断的数量不足以使计数器溢出，则这种方法在对应 CPU 从进程上下文进入空闲循环时每次都会修正 `->dynticks_nmi_nesting` 字段。
`->dynticks` 字段计算相应 CPU 进入和退出动态滴答空闲模式或用户模式的转换次数，因此当 CPU 处于动态滴答空闲模式或用户模式时，该计数器具有偶数值，否则具有奇数值。为了支持用户模式自适应滴答（详见 Documentation/timers/no_hz.rst），需要对用户模式的转换进行计数。
``->rcu_need_heavy_qs`` 字段用于记录 RCU 核心代码确实希望从对应的 CPU 获得一个静默状态，甚至愿意为此调用重量级的 dyntick 计数器操作。此标志由 RCU 的上下文切换和 `cond_resched()` 代码检查，它们会提供短暂的空闲停留时间作为响应。

最后，`->rcu_urgent_qs` 字段用于记录 RCU 核心代码确实希望从对应的 CPU 获得一个静默状态，并且其他字段表示了 RCU 对这个静默状态的迫切程度。此标志由 RCU 的上下文切换路径 (`rcu_note_context_switch`) 和 `cond_resched` 代码检查。

+-----------------------------------------------------------------------+
| **快速问答**：                                                       |
+-----------------------------------------------------------------------+
| 为什么不简单地将 `->dynticks_nesting` 和 `->dynticks_nmi_nesting` 计数器合并成一个简单的计数器来统计对应 CPU 不空闲的原因数量呢？ |
+-----------------------------------------------------------------------+
| **答案**：                                                           |
+-----------------------------------------------------------------------+
| 因为这样做会在中断处理程序永远不返回或能够从伪造的中断返回的情况下失败。 |
+-----------------------------------------------------------------------+

在某些特殊用途的构建中存在额外的字段，并单独讨论。
`rcu_head` 结构体
~~~~~~~~~~~~~~~~~~~~~~~~~~

每个 `rcu_head` 结构体代表一个 RCU 回调。这些结构体通常嵌入在使用异步恩典期算法的 RCU 保护数据结构中。相比之下，在使用阻塞等待 RCU 恩典期算法时，RCU 用户无需提供 `rcu_head` 结构体。
`rcu_head` 结构体具有以下字段：

::

     1   struct rcu_head *next;
     2   void (*func)(struct rcu_head *head);

`->next` 字段用于将 `rcu_head` 结构体链接到 `rcu_data` 结构体中的列表中。`->func` 字段是一个指针，指向当回调准备被调用时应调用的函数，并将 `rcu_head` 结构体的指针传递给该函数。然而，`kfree_rcu()` 使用 `->func` 字段来记录 `rcu_head` 结构体在其包含的 RCU 保护数据结构内的偏移量。
这两个字段都是 RCU 内部使用的。从 RCU 用户的角度来看，此结构体是一个不透明的“饼干”。

+-----------------------------------------------------------------------+
| **快速问答**：                                                       |
+-----------------------------------------------------------------------+
| 鉴于回调函数 `->func` 接收 `rcu_head` 结构体的指针，该函数如何找到包含的 RCU 保护数据结构的起始位置？              |
+-----------------------------------------------------------------------+
| **答案**：                                                           |
+-----------------------------------------------------------------------+
| 实际上，每种类型的 RCU 保护数据结构都有一个单独的回调函数。因此，回调函数可以使用 Linux 内核中的 `container_of()` 宏（或其他软件环境中的指针操作设施）来找到包含结构的起始位置。 |
+-----------------------------------------------------------------------+

`task_struct` 结构体中的 RCU 特定字段
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`CONFIG_PREEMPT_RCU` 实现使用 `task_struct` 结构体中的附加字段：

::

    1 #ifdef CONFIG_PREEMPT_RCU
    2   int rcu_read_lock_nesting;
    3   union rcu_special rcu_read_unlock_special;
    4   struct list_head rcu_node_entry;
    5   struct rcu_node *rcu_blocked_node;
    6 #endif /* #ifdef CONFIG_PREEMPT_RCU */
    7 #ifdef CONFIG_TASKS_RCU
    8   unsigned long rcu_tasks_nvcsw;
    9   bool rcu_tasks_holdout;
   10   struct list_head rcu_tasks_holdout_list;
   11   int rcu_tasks_idle_cpu;
   12 #endif /* #ifdef CONFIG_TASKS_RCU */

`->rcu_read_lock_nesting` 字段记录 RCU 读侧临界区的嵌套级别，而 `->rcu_read_unlock_special` 字段是一个位掩码，记录需要 `rcu_read_unlock()` 进行额外工作的特殊条件。`->rcu_node_entry` 字段用于形成已在一个可抢占 RCU 读侧临界区内阻塞的任务列表，而 `->rcu_blocked_node` 字段引用该任务所属的 `rcu_node` 结构体，或者如果它没有在一个可抢占 RCU 读侧临界区内阻塞则为 `NULL`。

`->rcu_tasks_nvcsw` 字段跟踪当前 tasks-RCU 恩典期开始时此任务经历的自愿上下文切换次数，`->rcu_tasks_holdout` 在当前 tasks-RCU 恩典期等待此任务时被设置，`->rcu_tasks_holdout_list` 是将此任务加入等待列表的列表元素，而 `->rcu_tasks_idle_cpu` 跟踪此空闲任务正在运行的 CPU，但仅当任务当前正在运行时，即 CPU 当前处于空闲状态时。

访问函数
~~~~~~~~~~~~~~~~~~

以下列出显示了 `rcu_get_root()`、`rcu_for_each_node_breadth_first` 和 `rcu_for_each_leaf_node()` 函数和宏：

::

     1 static struct rcu_node *rcu_get_root(struct rcu_state *rsp)
     2 {
     3   return &rsp->node[0];
     4 }
     5
     6 #define rcu_for_each_node_breadth_first(rsp, rnp) \
     7   for ((rnp) = &(rsp)->node[0]; \
     8        (rnp) < &(rsp)->node[NUM_RCU_NODES]; (rnp)++)
     9
    10 #define rcu_for_each_leaf_node(rsp, rnp) \
    11   for ((rnp) = (rsp)->level[NUM_RCU_LVLS - 1]; \
    12        (rnp) < &(rsp)->node[NUM_RCU_NODES]; (rnp)++)

`rcu_get_root()` 仅仅返回指定 `rcu_state` 结构体的 `->node[]` 数组的第一个元素的指针，即根 `rcu_node` 结构体。

如前所述，`rcu_for_each_node_breadth_first()` 宏利用了 `rcu_node` 结构体在 `rcu_state` 结构体的 `->node[]` 数组中的布局，通过简单遍历数组进行广度优先遍历。同样，`rcu_for_each_leaf_node()` 宏只遍历数组的最后一部分，从而只遍历叶节点 `rcu_node` 结构体。
+-----------------------------------------------------------------------+
| **快速测验**：                                                         |
+-----------------------------------------------------------------------+
| 如果 ``rcu_node`` 树只包含一个节点，``rcu_for_each_leaf_node()`` 会做什么？ |
+-----------------------------------------------------------------------+
| **答案**：                                                             |
+-----------------------------------------------------------------------+
| 在单节点情况下，``rcu_for_each_leaf_node()`` 会遍历该单个节点。         |
+-----------------------------------------------------------------------+

总结
~~~~~~~

因此，RCU 的状态由一个 ``rcu_state`` 结构表示，其中包含 ``rcu_node`` 和 ``rcu_data`` 结构的组合树。最后，在 ``CONFIG_NO_HZ_IDLE`` 内核中，每个 CPU 的动态空闲状态通过 ``rcu_data`` 结构中的动态时钟相关字段进行跟踪。如果你读到这里，你已经为阅读本系列其他文章中的代码分析做好了充分准备。

致谢
~~~~~~~~~~~~~~~

我要感谢 Cyrill Gorcunov、Mathieu Desnoyers、Dhaval Giani、Paul Turner、Abhishek Srivastava、Matt Kowalczyk 和 Serge Hallyn 帮助我将本文档整理得更易于阅读。

法律声明
~~~~~~~~~~~~~~~

本作品代表作者的观点，并不一定代表 IBM 的观点。
Linux 是 Linus Torvalds 的注册商标。
其他公司、产品和服务名称可能是他人的商标或服务标志。
