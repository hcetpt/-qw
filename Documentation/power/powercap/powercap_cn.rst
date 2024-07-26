### 功率限制框架

功率限制框架为内核与用户空间之间提供了一致的接口，使得功率限制驱动程序能够以统一的方式将设置暴露给用户空间。

#### 术语

该框架通过sysfs以对象树的形式向用户空间暴露功率限制设备。树的根级别的对象代表“控制类型”，这些类型对应于不同的功率限制方法。例如，“intel-rapl”控制类型代表Intel的“运行平均功率限制”（RAPL）技术，而“idle-injection”控制类型则对应使用空闲注入来控制功率。
功率区域代表系统中可以使用由所属控制类型确定的功率限制方法进行控制和监控的不同部分。它们各自包含用于监控功率的属性以及以功率约束形式表示的控制。如果系统中由不同功率区域表示的部分具有层次结构（即，一个较大的部分由多个较小的部分组成，每个部分都有自己的功率控制），那么这些功率区域也可以按层次组织，一个父功率区域包含多个子区域等，以此反映系统的功率控制拓扑。在这种情况下，可以通过父功率区域对一组设备一起应用功率限制，如果需要更精细的控制，则可以通过子区域实现。

示例sysfs接口树如下：

```
/sys/devices/virtual/powercap
└──intel-rapl
    ├──intel-rapl:0
    │   ├──constraint_0_name
    │   ├──constraint_0_power_limit_uw
    │   ├──constraint_0_time_window_us
    │   ├──...
    │   ├──intel-rapl:0:0
    │   │   ├──...
    │   ├──intel-rapl:0:1
    │   │   ├──...
    │   ├──...
    ├──intel-rapl:1
    │   ├──...
    │   ├──intel-rapl:1:0
    │   │   ├──...
    │   ├──intel-rapl:1:1
    │   │   ├──...
    │   ├──...
    ├──...
```

上述示例展示了使用Intel RAPL技术的情况，该技术可在Intel® IA-64和IA-32处理器架构中找到。存在一个名为`intel-rapl`的控制类型，其中包含两个功率区域`intel-rapl:0`和`intel-rapl:1`，分别代表CPU包。每个功率区域又包含两个子区域`intel-rapl:j:0`和`intel-rapl:j:1`（j = 0, 1），分别代表给定CPU包中的“核心”和“非核心”部分。所有的区域和子区域都包含能量监控属性（如`energy_uj`, `max_energy_range_uj`）以及约束属性（如`constraint_*`），允许施加控制（在“包”功率区域中的约束应用于整个CPU包，而在子区域中的约束仅应用于给定包的相应部分）。由于Intel RAPL不提供瞬时功率值，因此没有`power_uw`属性。
此外，每个功率区域还包含一个`name`属性，允许识别该区域所代表的系统部分。

例如：

```sh
cat /sys/class/power_cap/intel-rapl/intel-rapl:0/name
```

输出结果为：

```
package-0
```

根据不同的功率区域，Intel RAPL技术允许对每个功率区域应用一个或多个约束，如短期、长期和峰值功率，具有不同的时间窗口。
所有区域都包含表示约束名称、功率限制和时间窗口大小的属性。需要注意的是，时间窗口不适用于峰值功率。这里`constraint_j_*`属性对应第j个约束（j = 0,1,2）。

### 功率区域属性

#### 监控属性

- **energy_uj** (读写)：当前能量计数器，单位为微焦耳。写入“0”以重置。如果无法重置计数器，则此属性只读。
- **max_energy_range_uj** (只读)：上述能量计数器的范围，单位为微焦耳。
以下是提供的英文内容翻译成中文：

`power_uw (ro)`  
当前功率（微瓦）

`max_power_range_uw (ro)`  
上述功率值的范围（微瓦）

`name (ro)`  
此功率区域的名称

可能某些域同时具有功率范围和能量计数器范围；然而，只需满足其中一个条件即可。

**约束条件**
-------------

`constraint_X_power_limit_uw (rw)`  
功率限制（微瓦），适用于由"constraint_X_time_window_us"指定的时间窗口

`constraint_X_time_window_us (rw)`  
时间窗口（微秒）

`constraint_X_name (ro)`  
约束条件的可选名称

`constraint_X_max_power_uw(ro)`  
允许的最大功率（微瓦）

`constraint_X_min_power_uw(ro)`  
允许的最小功率（微瓦）

`constraint_X_max_time_window_us(ro)`  
允许的最大时间窗口（微秒）

`constraint_X_min_time_window_us(ro)`  
允许的最小时间窗口（微秒）
除 `power_limit_uw` 和 `time_window_us` 之外的其他字段均为可选。
通用区域和控制类型属性：
-------------------------------

- `enabled` (读写)：在区域级别或使用特定控制类型对所有区域启用/禁用控制。
电力上限客户端驱动程序接口
==========================

API 概述：

- 调用 `powercap_register_control_type()` 来注册控制类型对象。
- 调用 `powercap_register_zone()` 来注册一个电力区域（在给定的控制类型下），可以作为顶级电力区域，也可以作为之前注册的另一个电力区域的子区域。
- 在调用 `powercap_register_zone()` 注册该区域之前，必须定义电力区域中的约束数量及其对应的回调函数。
- 若要释放电力区域，请调用 `powercap_unregister_zone()`。
- 若要释放控制类型对象，请调用 `powercap_unregister_control_type()`。
详细的 API 可以通过在 `include/linux/powercap.h` 上使用 `kernel-doc` 工具生成。
