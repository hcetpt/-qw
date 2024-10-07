调度程序统计信息
====================

版本16的schedstats更改了'enum cpu_idle_type'内的定义顺序，这改变了show_schedstat()中的[CPU_MAX_IDLE_TYPES]列的顺序。特别是CPU_IDLE和__CPU_NOT_IDLE的位置互换了。数组的大小保持不变。
版本15的schedstats删除了一些sched_yield的计数器：yld_exp_empty、yld_act_empty和yld_both_empty。除此之外，它与版本14相同。
版本14的schedstats包含对sched_domains的支持，该功能在2.6.20内核中实现，尽管它与2.6.13到2.6.19期间内核中的版本12的统计数据相同（版本13从未发布）。一些计数器更适合每个运行队列；其他则适合每个域。请注意，域（及其相关信息）仅在使用CONFIG_SMP配置的机器上相关且可用。
在版本14的schedstat中，为每个列出的cpu提供了至少一个级别的域统计信息，并且可能有多个域。在此实现中，域没有特定的名称，但编号最高的域通常负责在整个机器上的所有cpu之间进行负载均衡，而domain0是最紧密聚焦的域，有时只在一对cpu之间进行负载均衡。目前，没有任何架构需要超过三个级别的域。域统计信息的第一字段是一个位图，表示受该域影响的cpu。
这些字段是计数器，只会递增。使用这些数据的程序需要从基线观察开始，然后在每次后续观察时计算计数器的变化。一个用于许多字段的perl脚本可以在以下网址获取：

    http://eaglet.pdxhosts.com/rick/linux/schedstat/

请注意，任何此类脚本都必须是版本特定的，因为改变版本的主要原因是输出格式的变化。对于希望编写自己脚本的人，这里描述了各个字段。

CPU统计信息
--------------
cpu<N> 1 2 3 4 5 6 7 8 9

第一字段是一个sched_yield()统计信息：

     1) 调用sched_yield()的次数

接下来三个是schedule()统计信息：

     2) 此字段是O(1)调度器中使用的过期计数字段。我们为了ABI兼容性保留了它，但它始终设置为零。
3) 调用schedule()的次数
     4) 调度后处理器处于空闲状态的次数

接下来两个是try_to_wake_up()统计信息：

     5) 调用try_to_wake_up()的次数
     6) 调用try_to_wake_up()以唤醒本地cpu的次数

接下来三个是描述调度延迟的统计信息：

     7) 在此处理器上运行的任务所花费时间的总和（纳秒）
     8) 在此处理器上等待运行的任务所花费时间的总和（纳秒）
     9) 在此cpu上运行的时间片数

域统计信息
-----------------
为每个描述的cpu生成一个域统计信息。（注意，如果没有定义CONFIG_SMP，则不使用任何域，这些行将不会出现在输出中。）

domain<N> <cpumask> 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36

第一字段是一个位图，表示此域操作的cpu
接下来24个是各种sched_balance_rq()统计信息，按空闲类型（空闲、繁忙和新空闲）分组：

    1) 当cpu空闲时，在此域中调用sched_balance_rq()的次数
    2) 当cpu空闲时，在此域中sched_balance_rq()检查但发现负载不需要平衡的次数
    3) 当cpu空闲时，在此域中sched_balance_rq()尝试移动一个或多个任务并失败的次数
    4) 当cpu空闲时，在此域中每次调用sched_balance_rq()时发现的不平衡总和（如果有）
    5) 当cpu空闲时，在此域中调用pull_task()的次数
    6) 即使目标任务在空闲时缓存热，在此域中调用pull_task()的次数
    7) 当cpu空闲时，在此域中调用sched_balance_rq()但未找到更繁忙队列的次数
    8) 当cpu空闲时，在此域中找到更繁忙队列但未找到更繁忙组的次数
    9) 当cpu繁忙时，在此域中调用sched_balance_rq()的次数
    10) 当cpu繁忙时，在此域中sched_balance_rq()检查但发现负载不需要平衡的次数
    11) 当cpu繁忙时，在此域中sched_balance_rq()尝试移动一个或多个任务并失败的次数
    12) 当cpu繁忙时，在此域中每次调用sched_balance_rq()时发现的不平衡总和（如果有）
    13) 当cpu繁忙时，在此域中调用pull_task()的次数
    14) 即使目标任务在繁忙时缓存热，在此域中调用pull_task()的次数
    15) 当cpu繁忙时，在此域中调用sched_balance_rq()但未找到更繁忙队列的次数
    16) 当cpu繁忙时，在此域中找到更繁忙队列但未找到更繁忙组的次数

    17) 当cpu刚刚变为空闲时，在此域中调用sched_balance_rq()的次数
    18) 当cpu刚刚变为空闲时，在此域中sched_balance_rq()检查但发现负载不需要平衡的次数
    19) 当cpu刚刚变为空闲时，在此域中sched_balance_rq()尝试移动一个或多个任务并失败的次数
    20) 当cpu刚刚变为空闲时，在此域中每次调用sched_balance_rq()时发现的不平衡总和（如果有）
    21) 当cpu刚刚变为空闲时，在此域中调用pull_task()的次数
    22) 即使目标任务在刚刚变为空闲时缓存热，在此域中调用pull_task()的次数
    23) 当cpu刚刚变为空闲时，在此域中调用sched_balance_rq()但未找到更繁忙队列的次数
    24) 当cpu刚刚变为空闲时，在此域中找到更繁忙队列但未找到更繁忙组的次数

接下来三个是active_load_balance()统计信息：

    25) 调用active_load_balance()的次数
    26) active_load_balance()尝试移动任务并失败的次数
    27) active_load_balance()成功移动任务的次数

接下来三个是sched_balance_exec()统计信息：

    28) sbe_cnt未使用
    29) sbe_balanced未使用
    30) sbe_pushed未使用

接下来三个是sched_balance_fork()统计信息：

    31) sbf_cnt未使用
    32) sbf_balanced未使用
    33) sbf_pushed未使用

接下来三个是try_to_wake_up()统计信息：

    34) 在此域中try_to_wake_up()唤醒了一个在此域内另一cpu上最后运行的任务的次数
    35) 在此域中try_to_wake_up()由于任务在其自己的cpu上缓存冷而将其移至唤醒cpu的次数
    36) 在此域中try_to_wake_up()启动被动负载均衡的次数

/proc/<pid>/schedstat
---------------------
schedstats还添加了一个新的/proc/<pid>/schedstat文件，以包括进程级别的部分相同信息。此文件中有三个字段对应于该进程：

     1) 在cpu上花费的时间（纳秒）
     2) 在运行队列上等待的时间（纳秒）
     3) 在此cpu上运行的时间片数

可以轻松编写一个程序来利用这些额外字段报告特定进程或一组进程在调度策略下的表现。一个简单版本的此类程序可在以下网址获取：

    http://eaglet.pdxhosts.com/rick/linux/schedstat/v12/latency.c
