=======================
电源限制框架
=======================

电源限制框架提供了一个内核与用户空间之间的一致接口，允许电源限制驱动程序以统一的方式将设置暴露给用户空间。

术语
====

该框架通过 sysfs 将电源限制设备暴露给用户空间，形式为一个对象树。树的根级对象代表“控制类型”，这些类型对应不同的电源限制方法。例如，intel-rapl 控制类型代表 Intel 的“运行平均功率限制”（RAPL）技术，而 'idle-injection' 控制类型则对应使用空闲注入来控制功率。
电源区域代表系统中可以被控制和监控的不同部分，它们根据所属控制类型的电源限制方法进行控制和监控。每个电源区域包含用于监控功率的属性以及表示为功率约束的控制。如果系统中由不同电源区域表示的部分是分层的（即，一个较大的部分由多个具有各自电源控制的小部分组成），那么这些电源区域也可以组织成层次结构，其中父电源区域包含多个子区域，以此反映系统的电源控制拓扑结构。在这种情况下，可以通过父电源区域对一组设备一起应用电源限制，并且如果需要更精细的控制，则可以通过子区域来实现。

示例 sysfs 接口树如下所示：

```
/sys/devices/virtual/powercap
└──intel-rapl
    ├──intel-rapl:0
    │   ├──constraint_0_name
    │   ├──constraint_0_power_limit_uw
    │   ├──constraint_0_time_window_us
    │   ├──constraint_1_name
    │   ├──constraint_1_power_limit_uw
    │   ├──constraint_1_time_window_us
    │   ├──device -> ../../intel-rapl
    │   ├──energy_uj
    │   ├──intel-rapl:0:0
    │   │   ├──constraint_0_name
    │   │   ├──constraint_0_power_limit_uw
    │   │   ├──constraint_0_time_window_us
    │   │   ├──constraint_1_name
    │   │   ├──constraint_1_power_limit_uw
    │   │   ├──constraint_1_time_window_us
    │   │   ├──device -> ../../intel-rapl:0
    │   │   ├──energy_uj
    │   │   ├──max_energy_range_uj
    │   │   ├──name
    │   │   ├──enabled
    │   │   ├──power
    │   │   │   ├──async
    │   │   │   []
    │   │   ├──subsystem -> ../../../../../../class/power_cap
    │   │   └──uevent
    │   ├──intel-rapl:0:1
    │   │   ├──constraint_0_name
    │   │   ├──constraint_0_power_limit_uw
    │   │   ├──constraint_0_time_window_us
    │   │   ├──constraint_1_name
    │   │   ├──constraint_1_power_limit_uw
    │   │   ├──constraint_1_time_window_us
    │   │   ├──device -> ../../intel-rapl:0
    │   │   ├──energy_uj
    │   │   ├──max_energy_range_uj
    │   │   ├──name
    │   │   ├──enabled
    │   │   ├──power
    │   │   │   ├──async
    │   │   │   []
    │   │   ├──subsystem -> ../../../../../../class/power_cap
    │   │   └──uevent
    │   ├──max_energy_range_uj
    │   ├──max_power_range_uw
    │   ├──name
    │   ├──enabled
    │   ├──power
    │   │   ├──async
    │   │   []
    │   ├──subsystem -> ../../../../../class/power_cap
    │   ├──enabled
    │   ├──uevent
    ├──intel-rapl:1
    │   ├──constraint_0_name
    │   ├──constraint_0_power_limit_uw
    │   ├──constraint_0_time_window_us
    │   ├──constraint_1_name
    │   ├──constraint_1_power_limit_uw
    │   ├──constraint_1_time_window_us
    │   ├──device -> ../../intel-rapl
    │   ├──energy_uj
    │   ├──intel-rapl:1:0
    │   │   ├──constraint_0_name
    │   │   ├──constraint_0_power_limit_uw
    │   │   ├──constraint_0_time_window_us
    │   │   ├──constraint_1_name
    │   │   ├──constraint_1_power_limit_uw
    │   │   ├──constraint_1_time_window_us
    │   │   ├──device -> ../../intel-rapl:1
    │   │   ├──energy_uj
    │   │   ├──max_energy_range_uj
    │   │   ├──name
    │   │   ├──enabled
    │   │   ├──power
    │   │   │   ├──async
    │   │   │   []
    │   │   ├──subsystem -> ../../../../../../class/power_cap
    │   │   └──uevent
    │   ├──intel-rapl:1:1
    │   │   ├──constraint_0_name
    │   │   ├──constraint_0_power_limit_uw
    │   │   ├──constraint_0_time_window_us
    │   │   ├──constraint_1_name
    │   │   ├──constraint_1_power_limit_uw
    │   │   ├──constraint_1_time_window_us
    │   │   ├──device -> ../../intel-rapl:1
    │   │   ├──energy_uj
    │   │   ├──max_energy_range_uj
    │   │   ├──name
    │   │   ├──enabled
    │   │   ├──power
    │   │   │   ├──async
    │   │   │   []
    │   │   ├──subsystem -> ../../../../../../class/power_cap
    │   │   └──uevent
    │   ├──max_energy_range_uj
    │   ├──max_power_range_uw
    │   ├──name
    │   ├──enabled
    │   ├──power
    │   │   ├──async
    │   │   []
    │   ├──subsystem -> ../../../../../class/power_cap
    │   ├──uevent
    ├──power
    │   ├──async
    │   []
    ├──subsystem -> ../../../../class/power_cap
    ├──enabled
    └──uevent
```

上述示例展示了 Intel RAPL 技术的应用情况，Intel RAPL 技术在 Intel® IA-64 和 IA-32 处理器架构中可用。这里有一个名为 intel-rapl 的控制类型，包含两个电源区域 intel-rapl:0 和 intel-rapl:1，分别代表 CPU 包。每个电源区域包含两个子区域 intel-rapl:j:0 和 intel-rapl:j:1（j = 0, 1），分别代表给定 CPU 包中的“核心”和“非核心”部分。所有区域和子区域都包含能量监控属性（energy_uj、max_energy_range_uj）和约束属性（constraint_*），允许应用控制（包电源区域中的约束适用于整个 CPU 包，子区域约束仅适用于给定包的相应部分）。由于 Intel RAPL 不提供瞬时功率值，因此没有 power_uw 属性。

此外，每个电源区域还包含一个 name 属性，允许识别该区域所代表的系统部分。
例如：
```
cat /sys/class/power_cap/intel-rapl/intel-rapl:0/name
```

输出：
```
package-0
```

根据不同的电源区域，Intel RAPL 技术允许每个电源区域应用一个或多个约束，如短期、长期和峰值功率，带有不同的时间窗口。所有区域都包含表示约束名称、功率限制和时间窗口大小的属性。注意，时间窗口不适用于峰值功率。这里的 constraint_j_* 属性对应第 j 个约束（j = 0,1,2）。
例如：
```
constraint_0_name
constraint_0_power_limit_uw
constraint_0_time_window_us
constraint_1_name
constraint_1_power_limit_uw
constraint_1_time_window_us
constraint_2_name
constraint_2_power_limit_uw
constraint_2_time_window_us
```

电源区域属性
=============

监控属性
----------

`energy_uj`（可读写）
当前能量计数器，单位为微焦耳。写入 "0" 重置
如果计数器无法重置，则此属性只读

`max_energy_range_uj`（只读）
上述能量计数器的范围，单位为微焦耳
```plaintext
power_uw (ro)
    当前功率（微瓦）
max_power_range_uw (ro)
    上述功率值的范围（微瓦）
name (ro)
    该功率区域的名称
某些领域可能同时具有功率范围和能量计数范围；然而，只需要其中之一。

约束条件
-----------

constraint_X_power_limit_uw (rw)
    功率限制（微瓦），适用于由"constraint_X_time_window_us"指定的时间窗口
constraint_X_time_window_us (rw)
    时间窗口（微秒）
constraint_X_name (ro)
    约束条件的可选名称

constraint_X_max_power_uw (ro)
    允许的最大功率（微瓦）
constraint_X_min_power_uw (ro)
    允许的最小功率（微瓦）
constraint_X_max_time_window_us (ro)
    允许的最大时间窗口（微秒）
constraint_X_min_time_window_us (ro)
    允许的最小时问窗口（微秒）
```
除 power_limit_uw 和 time_window_us 之外的其他字段均为可选字段。

公共区域和控制类型属性
------------------------

enabled (rw)：在区域级别或使用特定控制类型为所有区域启用/禁用控制

功耗上限客户端驱动程序接口
==========================

API 概览：
- 调用 powercap_register_control_type() 注册控制类型对象
- 调用 powercap_register_zone() 注册一个功耗区域（在给定的控制类型下），可以作为一个顶级功耗区域，或者作为先前已注册的另一个功耗区域的子区域
- 在调用 powercap_register_zone() 注册该区域之前，必须定义功耗区域中的约束数量及其相应的回调函数
- 要释放功耗区域，请调用 powercap_unregister_zone()
- 要释放控制类型对象，请调用 powercap_unregister_control_type()

详细的 API 可以通过在 include/linux/powercap.h 上使用 kernel-doc 生成。
