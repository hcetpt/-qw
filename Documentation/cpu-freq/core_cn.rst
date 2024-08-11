SPDX 许可证标识符: GPL-2.0

=============================================================
CPUFreq 核心及 CPUFreq 通知器的一般描述
=============================================================

作者:
	- Dominik Brodowski  <linux@brodo.de>
	- David Kimdon <dwhedon@debian.org>
	- Rafael J. Wysocki <rafael.j.wysocki@intel.com>
	- Viresh Kumar <viresh.kumar@linaro.org>

.. 目录:

   1.  CPUFreq 核心与接口
   2.  CPUFreq 通知器
   3.  通过运行性能点 (OPP) 生成 CPUFreq 表格

1. 一般信息
======================

CPUFreq 核心代码位于 drivers/cpufreq/cpufreq.c。此 cpufreq 代码为 CPUFreq 架构驱动程序（这些代码负责实际的频率转换）以及“通知器”提供了标准化的接口。通知器是指那些需要被策略更改（例如，ACPI 等热管理模块）或所有频率变化（例如，计时代码）告知的设备驱动程序或内核其他部分，甚至可能需要强制执行某些速度限制（例如 ARM 架构上的 LCD 驱动程序）。此外，在这里也会在频率变化时更新内核中的“常量” loops_per_jiffy。
对 cpufreq 策略的引用计数由 cpufreq_cpu_get 和 cpufreq_cpu_put 完成，这确保了 cpufreq 驱动程序正确地注册到核心，并且在调用 cpufreq_put_cpu 之前不会卸载。这也确保了在使用过程中相应的 cpufreq 策略不会被释放。

2. CPUFreq 通知器
====================

CPUFreq 通知器遵循标准的内核通知器接口
有关通知器的详细信息，请参阅 linux/include/linux/notifier.h
有两种不同的 CPUFreq 通知器：策略通知器和过渡通知器

2.1 CPUFreq 策略通知器
----------------------------

当创建或删除一个新策略时会通知这些通知器
阶段是在通知器的第二个参数中指定的。当首次创建策略时，阶段是 CPUFREQ_CREATE_POLICY；当删除策略时，阶段是 CPUFREQ_REMOVE_POLICY
第三个参数是一个 `void *` 指针，指向一个包含多个值的 struct cpufreq_policy 结构体，包括 min 和 max（新策略的下限和上限频率，单位为 kHz）

2.2 CPUFreq 过渡通知器
--------------------------------

对于策略中的每个在线 CPU，当 CPUfreq 驱动程序切换 CPU 核心频率并且此更改没有任何外部影响时，这些通知器会被通知两次
第二个参数指定了阶段 - CPUFREQ_PRECHANGE 或 CPUFREQ_POSTCHANGE
第三个参数是一个 `struct cpufreq_freqs` 结构体，包含以下值：

======	======================================
Policy	指向 `struct cpufreq_policy` 的指针
Old	旧的频率
New	新的频率
Flags	CPUFreq 驱动程序的标志
======	======================================

3. 使用 Operating Performance Point (OPP) 生成 CPUFreq 表格
==================================================================
关于 OPP 的详细信息，请参阅 `Documentation/power/opp.rst`

`dev_pm_opp_init_cpufreq_table` —
此函数提供了一个现成的转换例程，用于将 OPP 层内部关于可用频率的信息转换为可以方便地提供给 CPUFreq 的格式。
.. Warning::

   不要在中断上下文中使用此函数。
示例：

```c
soc_pm_init()
{
	/* 执行一些操作 */
	r = dev_pm_opp_init_cpufreq_table(dev, &freq_table);
	if (!r)
		policy->freq_table = freq_table;
	/* 执行其他操作 */
}
```

.. note::

   此函数仅在同时启用了 `CONFIG_CPU_FREQ` 和 `CONFIG_PM_OPP` 的情况下可用。

`dev_pm_opp_free_cpufreq_table`
释放由 `dev_pm_opp_init_cpufreq_table` 分配的表格。
