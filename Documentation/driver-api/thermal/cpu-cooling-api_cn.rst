=======================
CPU散热APIs使用说明
=======================

撰写者：Amit Daniel Kachhap <amit.kachhap@linaro.org>

更新日期：2015年1月6日

版权所有 © 2012 三星电子有限公司 (http://www.samsung.com)

0. 引言
===============

通用的CPU散热（频率限制）为调用者提供了注册/注销API。将散热设备绑定到阈值点的工作留给用户完成。注册API会返回散热设备指针。

1. CPU散热APIs
===================

1.1 cpufreq 注册/注销APIs
--------------------------------------------

    ::

    struct thermal_cooling_device
    *cpufreq_cooling_register(struct cpumask *clip_cpus)

    此接口函数以名称 "thermal-cpufreq-%x" 注册cpufreq散热设备。此API支持多个实例的cpufreq散热设备。
clip_cpus:
    频率约束将会发生的CPU的cpumask。
::

    struct thermal_cooling_device
    *of_cpufreq_cooling_register(struct cpufreq_policy *policy)

    此接口函数以名称 "thermal-cpufreq-%x" 并通过设备树节点链接的方式注册cpufreq散热设备，以便通过热管理设备树代码进行绑定。此API支持多个实例的cpufreq散热设备。
policy:
    CPUFreq策略。
::

    void cpufreq_cooling_unregister(struct thermal_cooling_device *cdev)

    此接口函数注销名称为 "thermal-cpufreq-%x" 的散热设备。
cdev: 需要注销的散热设备指针。
2. 功率模型
===============

功率API注册函数为CPU提供了一个简单的功率模型。当前功率按动态功率计算（目前不支持静态功率）。此功率模型要求使用内核的opp库注册CPU的操作点，并将 `cpufreq_frequency_table` 分配给CPU的 `struct device`。如果你使用CONFIG_CPUFREQ_DT配置，则 `cpufreq_frequency_table` 应该已经分配给了CPU设备。
处理器的动态功耗取决于许多因素。对于特定的处理器实现，主要因素包括：

- 处理器运行并消耗动态功耗的时间与处于空闲状态时功耗几乎可以忽略的时间之间的比例。这里我们将之称为“利用率”。
- 电压和频率水平是由于DVFS（动态电压和频率调节）的结果。DVFS级别是决定功耗的主要因素。
- 在运行时间中，“执行”行为（指令类型、内存访问模式等）通常会导致次级变化。在极端情况下，这种变化可能很显著，但通常其影响远小于上述因素。
动态功耗模型可以表示为：

  Pdyn = f(run) * Voltage^2 * Frequency * Utilisation

这里的f(run)代表描述的执行行为及其结果的单位为瓦特/赫兹/伏特^2（通常用毫瓦/兆赫兹/微伏特^2来表示）。

对于f(run)的详细行为可以在运行时进行建模。然而，在实践中，这样的在线模型依赖于许多特定于实现的处理器支持和特性化因素。因此，在最初的实现中，这部分贡献被简化为代表一个常数系数。这是一种与对总体功耗变化相对贡献相一致的简化方法。
在这个简化的表示中，我们的模型变为：

  Pdyn = Capacitance * Voltage^2 * Frequency * Utilisation

其中`capacitance`是一个常数，代表了一个指示性的运行时间动态功耗系数，基本单位为毫瓦/兆赫兹/微伏特^2。对于移动CPU来说，典型值可能在100到500之间。作为参考，ARM的Juno开发平台中的SoC的大致值为：Cortex-A57集群为530，Cortex-A53集群为140。
