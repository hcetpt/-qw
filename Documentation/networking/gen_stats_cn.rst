### SPDX 许可证标识符：GPL-2.0

===============================================
通用网络统计信息供 netlink 用户使用
===============================================

统计计数器被分组到结构体中：

==================== ===================== =====================
结构                  TLV 类型              描述
==================== ===================== =====================
gnet_stats_basic      TCA_STATS_BASIC       基本统计
gnet_stats_rate_est   TCA_STATS_RATE_EST    速率估算器
gnet_stats_queue      TCA_STATS_QUEUE       队列统计
无                    TCA_STATS_APP         应用程序特定
==================== ===================== =====================

### 收集：
-----------

声明你需要的统计结构体，例如：

```c
struct mystruct {
    struct gnet_stats_basic bstats;
    struct gnet_stats_queue qstats;
    // ...
};
```

更新统计信息，仅在 `dequeue()` 方法中（当拥有 `qdisc->running`）：

```c
mystruct->bstats.packet++;
mystruct->qstats.backlog += skb->pkt_len;
```

### 导出至用户空间（转储）：
---------------------------

```c
void my_dumping_routine(struct sk_buff *skb, ...)
{
    struct gnet_dump dump;

    if (gnet_stats_start_copy(skb, TCA_STATS2, &mystruct->lock, &dump,
                              TCA_PAD) < 0)
        goto rtattr_failure;

    if (gnet_stats_copy_basic(&dump, &mystruct->bstats) < 0 ||
        gnet_stats_copy_queue(&dump, &mystruct->qstats) < 0 ||
        gnet_stats_copy_app(&dump, &xstats, sizeof(xstats)) < 0)
        goto rtattr_failure;

    if (gnet_stats_finish_copy(&dump) < 0)
        goto rtattr_failure;
    // ...
}
```

### TCA_STATS/TCA_XSTATS 向后兼容性：
--------------------------------------------

先前使用 `struct tc_stats` 和 xstats 的用户可以通过调用兼容性包装函数来保持向后兼容性，以继续提供现有的 TLV 类型：

```c
void my_dumping_routine(struct sk_buff *skb, ...)
{
    if (gnet_stats_start_copy_compat(skb, TCA_STATS2, TCA_STATS,
                                     TCA_XSTATS, &mystruct->lock, &dump,
                                     TCA_PAD) < 0)
        goto rtattr_failure;
    // ...
}
```

一个 `struct tc_stats` 将在 `gnet_stats_copy_*` 调用期间填充，并附加到 `skb`。如果 `gnet_stats_copy_app` 被调用，则会提供 TCA_XSTATS。

### 锁定：
--------

在写入之前获取锁，并在所有统计信息被写入后释放锁。在发生错误时总是释放锁。你有责任确保锁已被初始化。

### 速率估算器：
---------------

0) 准备一个估算属性。这很可能是在用户空间完成的。此类 TLV 的值应包含一个 `tc_estimator` 结构。通常，此类 TLV 需要对齐到 32 位，因此需要适当地设置长度等。估算间隔和 ewma 日志需要转换为适当的值。建议使用 `tc_estimator.c` 中的 `tc_setup_estimator()` 作为转换例程。它做了一些巧妙的事情。它接受一个微秒时间间隔、一个也以微秒为单位的时间常数以及一个待填充的 `struct tc_estimator`。返回的 `tc_estimator` 可以传输到内核。将此类结构通过类型为 `TCA_RATE` 的 TLV 传递给内核中的代码。
在内核中设置时：

1) 确保首先设置基本统计和速率统计。
2) 确保已初始化用于设置此类统计的统计锁。
以下是给定文本的中文翻译：

3) 现在初始化一个新的估算器:

```c
int ret = gen_new_estimator(my_basicstats, my_rate_est_stats,
                            mystats_lock, attr_with_tcestimator_struct);

if (ret == 0)
    成功
else
    失败
```

从现在开始，每次你导出 `my_rate_est_stats` 的内容时，它都将包含最新的信息。
一旦完成使用，调用 `gen_kill_estimator(my_basicstats, my_rate_est_stats)`。确保在调用此函数时 `my_basicstats` 和 `my_rate_est_stats` 仍然有效（即仍然存在）。

作者：
--------
- Thomas Graf <tgraf@suug.ch>
- Jamal Hadi Salim <hadi@cyberus.ca>
