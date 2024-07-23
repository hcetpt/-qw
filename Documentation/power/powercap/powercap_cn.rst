### 功率限制框架

功率限制框架为内核与用户空间之间提供了一致的接口，使得功率限制驱动程序能够以统一的方式将设置暴露给用户空间。

#### 术语

该框架通过sysfs以对象树的形式向用户空间暴露功率限制设备。树的根级别的对象代表“控制类型”，这些类型对应于不同的功率限制方法。例如，“intel-rapl”控制类型代表Intel的“运行平均功率限制”（RAPL）技术，而“idle-injection”控制类型则对应使用空闲注入来控制功率。
功率区域代表系统中可以使用由所属控制类型确定的功率限制方法进行控制和监控的不同部分。它们各自包含用于监控功率的属性以及形式为功率约束的控制。如果系统中由不同功率区域表示的部分具有层次结构（即一个较大的部分由多个较小的部分组成，每个较小的部分都有自己的功率控制），那么这些功率区域也可以组织成一个层次结构，其中一个父级功率区域包含多个子区域等，以此反映系统的功率控制拓扑结构。在这种情况下，可以使用父级功率区域对一组设备一起应用功率限制，并且如果需要更精细的控制，则可以通过子区域来实现。

#### 示例sysfs接口树:

```
/sys/devices/virtual/powercap
└──intel-rapl
    ├──intel-rapl:0
    │   ├──constraint_0_name
    │   ├──constraint_0_power_limit_uw
    │   ├──constraint_0_time_window_us
    │   ├──...
    ├──intel-rapl:1
    │   ├──constraint_0_name
    │   ├──constraint_0_power_limit_uw
    │   ├──constraint_0_time_window_us
    │   ├──...
    ├──power
    │   ├──async
    │   []
    ├──subsystem -> ../../../../class/power_cap
    ├──enabled
    └──uevent
```

上面的例子展示了Intel RAPL技术的使用情况，该技术在Intel® IA-64 和 IA-32处理器架构中可用。有一个名为`intel-rapl`的控制类型，它包含两个功率区域`intel-rapl:0`和`intel-rapl:1`，分别代表CPU包。每个功率区域又包含两个子区域`intel-rapl:j:0`和`intel-rapl:j:1`（j=0,1），分别代表给定CPU包中的“核心”和“非核心”部分。所有区域和子区域都包含了能量监控属性（如`energy_uj`、`max_energy_range_uj`）和约束属性（如`constraint_*`），允许进行控制（在“包”功率区域中的约束应用于整个CPU包，而在子区域中的约束仅应用于给定包的相关部分）。由于Intel RAPL不提供瞬时功率值，因此没有`power_uw`属性。

此外，每个功率区域都包含一个名称属性，允许识别该区域所代表的系统部分。

#### 功率区域属性

##### 监控属性

- `energy_uj` (读写)
  - 当前的能量计数器，单位为微焦耳。写入"0"以重置。
  - 如果计数器无法重置，则此属性只读。
- `max_energy_range_uj` (只读)
  - 上述能量计数器的范围，单位为微焦耳。
以下是给定文本的中文翻译：

`power_uw` (只读)
当前的微瓦功率值。

`max_power_range_uw` (只读)
上述功率值在微瓦中的范围。

`name` (只读)
此功率区域的名称。

可能某些域同时具有功率范围和能量计数器范围；
然而，只需满足其中一个条件即可。

约束
------

`constraint_X_power_limit_uw` (读写)
应适用于由"constraint_X_time_window_us"指定的时间窗口的微瓦功率限制。

`constraint_X_time_window_us` (读写)
以微秒为单位的时间窗口。

`constraint_X_name` (只读)
约束的可选名称。

`constraint_X_max_power_uw`(只读)
允许的最大微瓦功率。

`constraint_X_min_power_uw`(只读)
允许的最小微瓦功率。

`constraint_X_max_time_window_us`(只读)
允许的最大微秒时间窗口。

`constraint_X_min_time_window_us`(只读)
允许的最小微秒时间窗口。
除了`power_limit_uw`和`time_window_us`之外，其他字段都是可选的。

通用区域和控制类型属性：
---------------------------

- `enabled`（读写）：在区域级别或使用控制类型对所有区域启用/禁用控制

功率上限客户端驱动接口：
=====================

API摘要：

- 调用`powercap_register_control_type()`来注册控制类型对象
- 调用`powercap_register_zone()`来注册一个功率区域（在给定的控制类型下），既可以作为顶级功率区域，也可以作为先前注册的另一个功率区域的子区域
- 在调用`powercap_register_zone()`注册该区域之前，必须定义功率区域中的约束数量及其相应的回调函数
- 为了释放功率区域，请调用`powercap_unregister_zone()`
- 为了释放控制类型对象，请调用`powercap_unregister_control_type()`

详细的API可以通过在`include/linux/powercap.h`上使用`kernel-doc`生成。
