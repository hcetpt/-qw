操作性能点（OPP）库
==========================

（版权所有）2009-2010，Nishanth Menon <nm@ti.com>，德克萨斯仪器公司

.. 目录

  1. 引言
  2. 初始OPP列表注册
  3. OPP搜索函数
  4. OPP可用性控制函数
  5. OPP数据检索函数
  6. 数据结构

1. 引言
==================

1.1 什么是操作性能点（OPP）？
-----------------------------------

当今复杂的片上系统（SoC）由多个协同工作的子模块组成。
在运行各种使用案例的操作系统中，并非SoC中的所有模块都需要始终以最高性能频率运行。为了实现这一点，SoC中的子模块被分组为域，允许某些域在较低电压和频率下运行，而其他域则在更高的电压/频率对下运行。
每个域支持的由频率和电压对组成的离散元组集被称为操作性能点或OPPs。
例如：

考虑一个支持以下特性的MPU设备：
{300MHz，在最低1V电压下}，{800MHz，在最低1.2V电压下}，
{1GHz，在最低1.3V电压下}

我们可以将这些表示为以下{Hz, uV}元组的三个OPP：

- {300000000, 1000000}
- {800000000, 1200000}
- {1000000000, 1300000}

1.2 操作性能点库
------------------------------

OPP库提供了一组辅助函数来组织和查询OPP信息。该库位于drivers/opp/目录中，其头文件位于include/linux/pm_opp.h。可以通过从电源管理menuconfig菜单启用CONFIG_PM_OPP来启用OPP库。某些SoC，如德克萨斯仪器公司的OMAP框架，可以选择在特定的OPP下引导，无需cpufreq。
OPP库的典型用法如下所示：

(用户) -> 注册一组默认OPP -> (库)
SoC框架 -> 在必要情况下修改某些OPP -> OPP层
          -> 查询以搜索/检索信息 ->

OPP层期望每个域都由一个唯一的设备指针表示。SoC框架向OPP层为每个设备注册一组初始OPP。这个列表预计是一个最优的小数量，通常每个设备大约有5个。
这个初始列表包含一组OPP，框架预期它们可以默认安全地在系统中启用。
关于OPP可用性的说明
^^^^^^^^^^^^^^^^^^^^^^^^

随着系统的运行，SoC框架可能会根据各种外部因素选择使每个设备上的某些OPP可用或不可用。示例用法：热管理或其他异常情况，其中SoC框架可能选择禁用更高频率的OPP，以安全地继续操作，直到可能重新启用该OPP。
OPP库在其实现中促进了这一概念。以下操作函数仅在可用的opp上运行：
dev_pm_opp_find_freq_{ceil, floor}，dev_pm_opp_get_voltage，dev_pm_opp_get_freq，dev_pm_opp_get_opp_count
dev_pm_opp_find_freq_exact旨在用于查找opp指针，然后可用于dev_pm_opp_enable/disable函数，以根据需要使一个opp可用
警告：如果调用了dev_pm_opp_enable/disable函数，则OPP库的用户应使用get_opp_count刷新其可用性计数，触发这些操作的确切机制或通知其他依赖子系统（如cpufreq）的机制留给使用OPP库的具体SoC框架自行决定。在这些操作的情况下，需要同样小心地刷新cpufreq表。
### 2. 初始 OPP 列表注册

SoC 实现通过反复调用 `dev_pm_opp_add` 函数，为每个设备添加 OPP。预期 SoC 框架将以最优方式注册 OPP 条目 - 典型数量少于 5 个。由注册 OPP 生成的列表在整个设备运行期间由 OPP 库维护。SoC 框架随后可以使用 `dev_pm_opp_enable` / `disable` 函数动态控制 OPP 的可用性。

#### `dev_pm_opp_add`
为特定域（由设备指针表示）添加一个新的 OPP。
OPP 通过频率和电压定义。一旦添加，OPP 被假定为可用，其可用性的控制可以通过 `dev_pm_opp_enable/disable` 函数进行。OPP 库内部在 `dev_pm_opp` 结构中存储和管理这些信息。
此函数可能被 SoC 框架用于根据 SoC 使用环境的需求定义一个最优列表。

**警告：**
不要在中断上下文中使用此函数。

示例：
```c
soc_pm_init()
{
    /* 执行一些操作 */
    r = dev_pm_opp_add(mpu_dev, 1000000, 900000);
    if (!r) {
        pr_err("%s: 无法注册 mpu opp(%d)\n", r);
        goto no_cpufreq;
    }
    /* 执行 cpufreq 相关操作 */
no_cpufreq:
    /* 执行剩余操作 */
}
```

### 3. OPP 搜索函数

如 cpufreq 等高级框架基于频率工作。为了将频率映射回相应的 OPP，OPP 库提供了方便的函数来搜索由 OPP 库内部管理的 OPP 列表。如果找到匹配项，这些搜索函数返回代表 opp 的匹配指针，否则返回错误。这些错误应通过标准错误检查（如 `IS_ERR()`）处理，并由调用者采取适当行动。
调用这些函数的程序在使用 OPP 后应当调用 `dev_pm_opp_put()`。否则，OPP 的内存永远不会被释放，导致内存泄漏。

#### `dev_pm_opp_find_freq_exact`
基于 *精确* 频率和可用性搜索 OPP。此函数特别适用于使默认不可用的 OPP 可用。
示例：当 SoC 框架检测到可以提供更高频率的情况时，它可使用此函数查找 OPP，在实际调用 `dev_pm_opp_enable` 使其可用之前：

```c
opp = dev_pm_opp_find_freq_exact(dev, 1000000000, false);
dev_pm_opp_put(opp);
/* 不要操作指针...只是做一下合理性检查... */
if (IS_ERR(opp)) {
    pr_err("频率未禁用!\n");
    /* 触发适当的操作... */
} else {
    dev_pm_opp_enable(dev,1000000000);
}
```
**注：**
这是唯一一个在 OPP 不可用时也操作的搜索函数。

#### `dev_pm_opp_find_freq_floor`
搜索 *至多* 提供频率的可用 OPP。此函数在寻找较低匹配或按频率递减顺序操作 OPP 信息时非常有用。
### 示例：查找设备的最高 OPP

```
freq = ULONG_MAX;
opp = dev_pm_opp_find_freq_floor(dev, &freq);
dev_pm_opp_put(opp);
```

`dev_pm_opp_find_freq_ceil`
搜索可用的 OPP，其频率至少为提供的频率。此函数在寻找更高的匹配项或按频率递增顺序操作 OPP 信息时非常有用。
#### 示例 1：查找设备的最低 OPP

```
freq = 0;
opp = dev_pm_opp_find_freq_ceil(dev, &freq);
dev_pm_opp_put(opp);
```

#### 示例 2：SoC cpufreq_driver->target 的简化实现

```c
soc_cpufreq_target(..)
{
    /* 执行策略检查等操作 */
    /* 根据请求找到最佳频率匹配 */
    opp = dev_pm_opp_find_freq_ceil(dev, &freq);
    dev_pm_opp_put(opp);
    if (!IS_ERR(opp))
        soc_switch_to_freq_voltage(freq);
    else
        /* 当无法满足请求时执行其他操作 */
    /* 执行其他操作 */
}
```

### 4. OPP 可用性控制函数

默认注册到 OPP 库的 OPP 列表可能不适用于所有情况。OPP 库提供了一组函数来修改 OPP 列表中 OPP 的可用性。这使得 SoC 框架能够对哪些 OPP 组可用于操作进行精细的动态控制。

这些函数旨在暂时移除 OPP，例如在温度考虑的情况下（例如，在温度下降之前不要使用 OPPx）。

**警告**：
不要在中断上下文中使用这些函数。

`dev_pm_opp_enable`
使一个 OPP 可用于操作。
#### 示例：假设 1GHz OPP 只有当 SoC 温度低于某个阈值时才可用。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp < temp_low_thresh) {
    /* 如果 1GHz 已禁用，则启用 */
    opp = dev_pm_opp_find_freq_exact(dev, 1000000000, false);
    dev_pm_opp_put(opp);
    /* 仅做错误检查 */
    if (!IS_ERR(opp))
        ret = dev_pm_opp_enable(dev, 1000000000);
    else
        goto try_something_else;
}
```

`dev_pm_opp_disable`
使一个 OPP 不可用于操作。
#### 示例：假设如果温度超过阈值，则禁用 1GHz OPP。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp > temp_high_thresh) {
    /* 如果 1GHz 已启用，则禁用 */
    opp = dev_pm_opp_find_freq_exact(dev, 1000000000, true);
    dev_pm_opp_put(opp);
    /* 仅做错误检查 */
    if (!IS_ERR(opp))
        ret = dev_pm_opp_disable(dev, 1000000000);
    else
        goto try_something_else;
}
```

### 5. OPP 数据检索函数

由于 OPP 库抽象了 OPP 信息，因此需要一组函数从 `dev_pm_opp` 结构中提取信息。一旦通过搜索函数获取了 OPP 指针，SoC 框架可以使用以下函数检索 OPP 层中的信息。

`dev_pm_opp_get_voltage`
获取由 opp 指针表示的电压。
#### 示例：在 cpufreq 转换到不同频率时，SoC 框架需要使用调节器框架设置由 OPP 表示的电压到提供该电压的电源管理芯片。

```c
soc_switch_to_freq_voltage(freq)
{
    /* 执行操作 */
    opp = dev_pm_opp_find_freq_ceil(dev, &freq);
    v = dev_pm_opp_get_voltage(opp);
    dev_pm_opp_put(opp);
    if (v)
        regulator_set_voltage(.., v);
    /* 执行其他操作 */
}
```

`dev_pm_opp_get_freq`
获取由 opp 指针表示的频率。
#### 示例：假设 SoC 框架使用几个辅助函数，我们可以传递 opp 指针而不是处理大量的数据参数。

```c
soc_cpufreq_target(..)
{
    /* 执行操作.. */
    max_freq = ULONG_MAX;
    max_opp = dev_pm_opp_find_freq_floor(dev, &max_freq);
    requested_opp = dev_pm_opp_find_freq_ceil(dev, &freq);
    if (!IS_ERR(max_opp) && !IS_ERR(requested_opp))
        r = soc_test_validity(max_opp, requested_opp);
    dev_pm_opp_put(max_opp);
    dev_pm_opp_put(requested_opp);
    /* 执行其他操作 */
}

soc_test_validity(..)
{
    if (dev_pm_opp_get_voltage(max_opp) < dev_pm_opp_get_voltage(requested_opp))
        return -EINVAL;
    if (dev_pm_opp_get_freq(max_opp) < dev_pm_opp_get_freq(requested_opp))
        return -EINVAL;
    /* 执行操作.. */
}
```

`dev_pm_opp_get_opp_count`
获取设备可用的 OPP 数量。
#### 示例：假设 SoC 中的协处理器需要知道表格中的可用频率，主处理器可以如下通知：

```c
soc_notify_coproc_available_frequencies()
{
    /* 执行操作 */
    num_available = dev_pm_opp_get_opp_count(dev);
    speeds = kcalloc(num_available, sizeof(u32), GFP_KERNEL);
    /* 按递增顺序填充表格 */
    freq = 0;
    while (!IS_ERR(opp = dev_pm_opp_find_freq_ceil(dev, &freq))) {
        speeds[i] = freq;
        freq++;
        i++;
        dev_pm_opp_put(opp);
    }

    soc_notify_coproc(AVAILABLE_FREQs, speeds, num_available);
    /* 执行其他操作 */
}
```

### 6. 数据结构

通常，SoC 包含多个可变电压域。每个域由一个设备指针表示。OPP 与之的关系如下所示：

```
SoC
   |- device 1
   |  |- opp 1 (可用性, 频率, 电压)
   |  |- opp 2 ...
```
...以此类推，代表其他设备和 OPP。
OPP (Operating Performance Point)库维护了一个内部列表，该列表由SoC（System on Chip）框架填充，并通过上述描述的多种函数进行访问。然而，表示实际OPPs和域的结构体是OPP库自身的内部部分，以允许在不同系统间提供适当的抽象并可重用。

`struct dev_pm_opp`
这是OPP库使用的内部数据结构，用于表示一个OPP。除了频率、电压和可用性信息外，它还包含OPP库操作所需的内部管理信息。此结构体的指针被提供给用户（如SoC框架），用作与OPP层交互时OPP的标识符。

**警告：**
用户不应解析或修改`struct dev_pm_opp`指针。一个实例的默认值由`dev_pm_opp_add`填充，但OPP的可用性可以通过`dev_pm_opp_enable`和`dev_pm_opp_disable`函数进行修改。

`struct device`
这用于向OPP层标识一个域。设备的性质及其实现留给OPP库的用户，例如SoC框架。

总体上，从简化的视角看，数据结构操作如下所示：

- 初始化/修改：
```
+-----+        /- dev_pm_opp_enable
dev_pm_opp_add --> | opp | <-------
  |         +-----+        \- dev_pm_opp_disable
  \-------> domain_info(device)
```

- 搜索函数：
```
               /-- dev_pm_opp_find_freq_ceil  ---\   +-----+
domain_info<---- dev_pm_opp_find_freq_exact -----> | opp |
               \-- dev_pm_opp_find_freq_floor ---/   +-----+
```

- 获取函数：
```
+-----+     /- dev_pm_opp_get_voltage
| opp | <---
+-----+     \- dev_pm_opp_get_freq

domain_info <- dev_pm_opp_get_opp_count
```

这些函数允许用户查询和操作OPP库中存储的信息，如查找特定频率的OPP，获取OPP的电压或频率，以及获取域中的OPP数量。
