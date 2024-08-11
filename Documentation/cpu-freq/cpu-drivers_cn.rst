...SPDX许可证识别符：GPL-2.0

===============================================
如何实现新的CPUFreq处理器驱动程序
===============================================

作者：

    - Dominik Brodowski  <linux@brodo.de>
    - Rafael J. Wysocki <rafael.j.wysocki@intel.com>
    - Viresh Kumar <viresh.kumar@linaro.org>

.. 内容目录

   1. 需要做些什么？
   1.1 初始化
   1.2 每个CPU的初始化
   1.3 verify
   1.4 target/target_index 或 setpolicy？
   1.5 target/target_index
   1.6 setpolicy
   1.7 get_intermediate 和 target_intermediate
   2. 频率表辅助函数



1. 需要做些什么？
=================

所以，你刚刚得到了一个新的CPU /芯片组，并且想要为其添加cpufreq支持？太好了。这里有一些关于需要做些什么的提示：

1.1 初始化
----------

首先，在一个__initcall级别7（module_init()）或之后的函数中检查此内核是否在正确的CPU和正确的芯片组上运行。如果是这样，则使用cpufreq_register_driver()通过CPUfreq核心注册一个struct cpufreq_driver。

这个struct cpufreq_driver应该包含什么？

 .name - 这个驱动器的名称
.init - 指向每个策略初始化函数的指针
.verify - 指向“验证”函数的指针
.setpolicy _or_ .fast_switch _or_ .target _or_ .target_index - 见下文了解它们之间的差异
并且可选地

 .flags - 对于cpufreq核心的提示
.driver_data - cpufreq驱动特定的数据
.get_intermediate 和 target_intermediate - 用于在更改CPU频率时切换到稳定频率
.get - 返回CPU当前的频率
.bios_limit - 返回CPU的HW/BIOS最大频率限制
.exit - 在CPU热插拔过程中的CPU_POST_DEAD阶段调用的每个策略清理函数的指针
挂起 - 指向一个每策略挂起函数的指针，该函数在禁用中断并停止策略的调节器之后被调用。

恢复 - 指向一个每策略恢复函数的指针，在重新启动调节器之前被调用。

就绪 - 指向一个每策略就绪函数的指针，在策略完全初始化后被调用。

.attr - 指向一个NULL终止的“struct freq_attr”列表的指针，允许将值导出到sysfs。

.boost_enabled - 如果设置，则启用了提升频率。

.set_boost - 指向一个每策略函数，用于启用/禁用提升频率。

### 1.2 每个CPU初始化

每当设备模型注册新的CPU，或者当cpufreq驱动程序自己注册时，如果CPU上不存在cpufreq策略，则会调用cpufreq_driver.init函数。注意，仅对策略进行一次调用.init()和.exit()，而不是为由策略管理的每个CPU。

它接受一个``struct cpufreq_policy *policy``作为参数。接下来应该做什么？

如果必要的话，请激活您的CPU上的CPUfreq支持。
然后，驱动程序必须填充以下值：

- `policy->cpuinfo.min_freq` 和 `policy->cpuinfo.max_freq`：表示此CPU支持的最小和最大频率（以千赫为单位）。

- `policy->cpuinfo.transition_latency`：表示此CPU在两个频率之间切换所需的时间（以纳秒为单位）。如果适用，请指定CPUFREQ_ETERNAL；否则，请留空。

- `policy->cur`：表示此CPU当前运行的频率（如果适用）。

- `policy->min`, `policy->max`：这些必须包含此CPU的默认策略。稍后，cpufreq_driver.verify和cpufreq_driver.setpolicy或cpufreq_driver.target/target_index将使用这些值被调用。

- `policy->cpus`：更新此字段，以包含与该CPU共享时钟/电压轨道的所有（在线+离线）CPU的掩码（即与之共享时钟/电压轨道的CPU）。

对于设置某些值（cpuinfo.min[max]_freq, policy->min[max]），可以使用频率表辅助工具。有关更多信息，请参阅第2节。

### 1.3 验证

当用户决定设置新策略（由“policy,governor,min,max”组成）时，必须验证此策略，以便更正不兼容的值。为了验证这些值，可以使用cpufreq_verify_within_limits(``struct cpufreq_policy *policy``, ``unsigned int min_freq``, ``unsigned int max_freq``)函数。
请参阅第2节以了解频率表辅助函数的详细信息。
您需要确保至少有一个有效的频率（或工作范围）位于 policy->min 和 policy->max 之间。如果必要，首先增加 policy->max；只有当这样做仍无解时，才降低 policy->min。

1.4 target 或 target_index 或 setpolicy 或 fast_switch？
-------------------------------------------------------------------

大多数 cpufreq 驱动程序乃至大多数 CPU 频率调节算法只允许将 CPU 频率设置为预定义的固定值。对于这些情况，您可以使用 ->target()、->target_index() 或 ->fast_switch() 回调函数。
有些支持 cpufreq 的处理器会自行在一定范围内切换频率。这些应该使用 ->setpolicy() 回调函数。

1.5 target/target_index
------------------------

target_index 调用有两个参数：`struct cpufreq_policy *policy`，以及 `unsigned int` 索引（用于已暴露的频率表）
当被调用时，CPUfreq 驱动程序必须设置新的频率。实际频率应由 freq_table[index].frequency 确定。
在出现错误的情况下，它应当始终恢复到先前的频率（即 policy->restore_freq），即使我们之前已经切换到了一个中间频率。

**废弃**
----------
target 调用有三个参数：`struct cpufreq_policy *policy`、`unsigned int target_frequency` 和 `unsigned int relation`
当被调用时，CPUfreq 驱动程序必须设置新的频率。实际频率应根据以下规则确定：

- 尽量接近 "target_freq"
- policy->min <= new_freq <= policy->max （这一点必须有效！！！）
- 如果 relation==CPUFREQ_REL_L，则尝试选择一个不低于 target_freq 的新频率。（"L 表示最低，但不能低于此"）
- 如果 relation==CPUFREQ_REL_H，则尝试选择一个不高于 target_freq 的新频率。（"H 表示最高，但不能高于此"）

这里再次，频率表辅助函数可能对你有所帮助——请参见第2节以获取详情。

1.6 fast_switch
----------------

此函数用于从调度器上下文中进行频率切换。
并非所有驱动程序都需要实现它，因为在此回调中不允许睡眠。此回调必须高度优化以尽可能快地执行切换。
此函数有两个参数：`struct cpufreq_policy *policy` 和 `unsigned int target_frequency`。

1.7 设置策略 (setpolicy)
---------------------------

设置策略调用仅接受一个 `struct cpufreq_policy *policy` 参数。你需要将处理器或芯片组内部动态频率切换的下限设置为 policy->min，上限设置为 policy->max；如果支持的话，当 policy->policy 为 CPUFREQ_POLICY_PERFORMANCE 时选择性能导向的设置，而当 policy->policy 为 CPUFREQ_POLICY_POWERSAVE 时选择节能导向的设置。请参考 drivers/cpufreq/longrun.c 中的实现。

1.8 获取中间频率 (get_intermediate) 和设置中间目标 (target_intermediate)
---------------------------------------------------------------------------------

仅适用于未设置 target_index() 和 CPUFREQ_ASYNC_NOTIFICATION 的驱动程序。get_intermediate 应返回平台想要切换到的一个稳定的中间频率，而 target_intermediate() 应在跳转到 'index' 对应的频率之前将 CPU 设置为此中间频率。核心会负责发送通知，因此驱动程序无需在 target_intermediate() 或 target_index() 中处理这些通知。
驱动程序可以在不希望为某个目标频率切换到中间频率的情况下从 get_intermediate() 返回 '0'。在这种情况下，核心会直接调用 ->target_index()。
注意：在失败的情况下，->target_index() 应恢复到 policy->restore_freq，因为核心将会发送相应的通知。
2. 频率表助手
==================

由于大多数 cpufreq 处理器只允许设置为几个特定的频率，一个包含一些辅助函数的“频率表”可能有助于简化处理器驱动程序的工作。这样的“频率表”由一系列的 struct cpufreq_frequency_table 元素组成，其中“driver_data”存储驱动程序特有的值，“frequency”中存储对应的频率，并设置了标志位。在表的末尾，需要添加一个 frequency 设置为 CPUFREQ_TABLE_END 的 cpufreq_frequency_table 条目；如果你想跳过表中的某一项，则可以将 frequency 设置为 CPUFREQ_ENTRY_INVALID。这些条目不需要按特定顺序排序，但如果它们是有序的，cpufreq 核心将更快地为它们进行 DVFS（动态电压和频率调节），因为查找最佳匹配项的速度会更快。
如果策略在其 policy->freq_table 字段中包含一个有效的指针，则 cpufreq 表会被核心自动验证。
cpufreq_frequency_table_verify() 确保至少有一个有效频率位于 policy->min 和 policy->max 之间，并且满足所有其他条件。这对于 ->verify 调用非常有用。
`cpufreq_frequency_table_target()` 是针对 `->target` 阶段对应的频率表辅助函数。只需将值传递给此函数，该函数会返回频率表项的索引，该项包含CPU应设置的目标频率。

以下宏可以用作遍历 `cpufreq_frequency_table` 的迭代器：

`cpufreq_for_each_entry(pos, table)` —— 遍历频率表的所有条目。
`cpufreq_for_each_valid_entry(pos, table)` —— 遍历所有条目，排除 `CPUFREQ_ENTRY_INVALID` 频率。

使用参数 "pos" —— 作为循环游标的 `cpufreq_frequency_table *` 和 "table" —— 您想要遍历的 `cpufreq_frequency_table *`。
例如：

```c
struct cpufreq_frequency_table *pos, *driver_freq_table;

cpufreq_for_each_entry(pos, driver_freq_table) {
    /* 对 pos 进行一些操作 */
    pos->frequency = ..;
}
```

如果您需要处理 `pos` 在 `driver_freq_table` 中的位置，请不要通过减去指针来实现，因为这样比较耗时。相反，可以使用宏 `cpufreq_for_each_entry_idx()` 和 `cpufreq_for_each_valid_entry_idx()`。
