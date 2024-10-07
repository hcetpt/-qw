==========================================
操作性能点（OPP）库
==========================================

(C) 2009-2010 Nishanth Menon <nm@ti.com>，德州仪器公司

.. 目录

  1. 引言
  2. 初始OPP列表注册
  3. OPP搜索函数
  4. OPP可用性控制函数
  5. OPP数据检索函数
  6. 数据结构

1. 引言
===============

1.1 什么是操作性能点（OPP）？
-----------------------------------

如今复杂的片上系统（SoC）包含多个子模块协同工作。在一个运行各种用例的操作系统中，并非所有SoC中的模块都需要一直以最高性能频率运行。为了实现这一点，SoC中的子模块被分组成域，允许某些域以较低的电压和频率运行，而其他域则以较高的电压/频率对运行。
一组离散的频率和电压对，即每个域支持的一组特定组合，被称为操作性能点（OPP）。

例如：

假设有一个MPU设备支持以下配置：
{300MHz在最低电压1V}，{800MHz在最低电压1.2V}，{1GHz在最低电压1.3V}

我们可以将这些表示为三个OPP，如下所示的{Hz, uV}元组：

- {300000000, 1000000}
- {800000000, 1200000}
- {1000000000, 1300000}

1.2 操作性能点库
-----------------------------------

OPP库提供了一组辅助函数来组织和查询OPP信息。该库位于`drivers/opp/`目录中，头文件位于`include/linux/pm_opp.h`。可以通过从电源管理的menuconfig菜单启用`CONFIG_PM_OPP`来启用OPP库。某些SoC如德州仪器的OMAP框架允许选择性地在某个OPP下启动，而无需使用cpufreq。

OPP库的典型用法如下：

(用户) -> 注册一组默认的OPP -> (库)
SoC框架 -> 在必要时修改某些OPP -> OPP层
           -> 查询以搜索/检索信息 ->

OPP层期望每个域由一个唯一的设备指针表示。SoC框架向OPP层注册每台设备的一组初始OPP。这个列表通常应该是一个尽可能小的数量，大约每台设备5个。
这个初始列表包含了一组框架期望默认情况下可以安全启用的OPP。

关于OPP可用性的说明
^^^^^^^^^^^^^^^^^^^^^^^^

随着系统的运行，SoC框架可能会根据各种外部因素选择使某些设备上的OPP可用或不可用。示例用法：热管理或其他特殊情况，在这些情况下SoC框架可能选择禁用较高频率的OPP以安全继续运行，直到如果可能的话重新启用该OPP。
OPP库在其实现中促进了这一概念。以下操作函数仅在可用的OPP上操作：
`dev_pm_opp_find_freq_{ceil, floor}`, `dev_pm_opp_get_voltage`, `dev_pm_opp_get_freq`, `dev_pm_opp_get_opp_count`
`dev_pm_opp_find_freq_exact`旨在用于查找OPP指针，然后可以使用`dev_pm_opp_enable/disable`函数根据需要使某个OPP可用。
警告：如果调用了`dev_pm_opp_enable/disable`函数，OPP库的用户应使用`get_opp_count`刷新其可用性计数。触发这些机制或通知其他依赖子系统（如cpufreq）的具体机制由使用OPP库的特定SoC框架自行决定。在进行这些操作时，需要注意刷新cpufreq表。
2. 初始 OPP 列表注册
================================
SoC 实现通过迭代调用 dev_pm_opp_add 函数来为每个设备添加 OPP。预期 SoC 框架将最优地注册 OPP 条目——典型数量少于 5 个。通过注册 OPP 生成的列表在整个设备运行期间由 OPP 库维护。SoC 框架可以随后使用 dev_pm_opp_enable/disable 函数动态控制 OPP 的可用性。

dev_pm_opp_add
	为特定域（由设备指针表示）添加一个新的 OPP。
OPP 使用频率和电压定义。一旦添加，OPP 被认为是可用的，并且可以通过 dev_pm_opp_enable/disable 函数来控制其可用性。OPP 库在内部存储和管理这些信息到 dev_pm_opp 结构体中。
此函数可用于 SoC 框架根据 SoC 使用环境的需求定义一个最优列表。

警告：
	不要在中断上下文中使用此函数。

示例：

```c
soc_pm_init() {
	/* 执行一些操作 */
	r = dev_pm_opp_add(mpu_dev, 1000000, 900000);
	if (!r) {
		pr_err("%s: 无法注册 mpu opp(%d)\n", r);
		goto no_cpufreq;
	}
	/* 执行 cpufreq 相关操作 */
no_cpufreq:
	/* 执行剩余的操作 */
}
```

3. OPP 搜索函数
=======================
高级框架如 cpufreq 基于频率工作。为了将频率映射回相应的 OPP，OPP 库提供了方便的函数来搜索 OPP 库内部管理的 OPP 列表。这些搜索函数在找到匹配项时返回代表该 OPP 的指针，否则返回错误。这些错误应通过标准错误检查（如 IS_ERR()）进行处理，并由调用者采取适当的措施。
调用这些函数的代码应在使用 OPP 后调用 dev_pm_opp_put()。否则，OPP 的内存将永远不会被释放，导致内存泄漏。

dev_pm_opp_find_freq_exact
	基于精确频率和可用性搜索 OPP。此函数特别有用，可以在默认不可用的情况下启用一个 OPP。

示例：当 SoC 框架检测到一种情况，其中可以提供更高的频率时，它可以使用此函数查找 OPP，然后调用 dev_pm_opp_enable 实际启用它：

```c
opp = dev_pm_opp_find_freq_exact(dev, 1000000000, false);
dev_pm_opp_put(opp);
/* 不要操作指针，只做一个简单的检查 */
if (IS_ERR(opp)) {
	pr_err("频率未禁用！\n");
	/* 触发适当的动作 */
} else {
	dev_pm_opp_enable(dev, 1000000000);
}
```

注意：
	这是唯一一个在 OPP 不可用时操作的搜索函数。

dev_pm_opp_find_freq_floor
	搜索可用的 OPP，其频率最多不超过提供的频率。此函数在寻找较低匹配项或按递减顺序操作 OPP 信息时非常有用。
### 示例：查找设备的最高 OPP

```c
freq = ULONG_MAX;
opp = dev_pm_opp_find_freq_floor(dev, &freq);
dev_pm_opp_put(opp);
```

`dev_pm_opp_find_freq_ceil`
---
查找至少为给定频率的可用 OPP。此函数在搜索更高匹配或按频率递增顺序操作 OPP 信息时非常有用。

#### 示例 1：查找设备的最低 OPP

```c
freq = 0;
opp = dev_pm_opp_find_freq_ceil(dev, &freq);
dev_pm_opp_put(opp);
```

#### 示例 2：简化实现 SoC 的 cpufreq_driver->target

```c
soc_cpufreq_target(..)
{
    /* 执行一些策略检查等 */
    /* 查找与请求最匹配的频率 */
    opp = dev_pm_opp_find_freq_ceil(dev, &freq);
    dev_pm_opp_put(opp);
    if (!IS_ERR(opp))
        soc_switch_to_freq_voltage(freq);
    else
        /* 当无法满足请求时做一些处理 */
    /* 执行其他操作 */
}
```

### 4. OPP 可用性控制函数
---
默认注册的 OPP 列表可能不适用于所有情况。OPP 库提供了一组函数来修改 OPP 列表中的 OPP 可用性。这使得 SoC 框架能够对哪些 OPP 组合可用进行精细的动态控制。
这些函数旨在暂时移除一个 OPP，例如在热考虑的情况下（例如，在温度下降之前不要使用 OPPx）。

**警告：**
不要在中断上下文中使用这些函数。

`dev_pm_opp_enable`
---
使一个 OPP 可用。

#### 示例：假设 1GHz OPP 在 SoC 温度低于某个阈值时才可用。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp < temp_low_thresh) {
    /* 如果 1GHz 被禁用，则启用它 */
    opp = dev_pm_opp_find_freq_exact(dev, 1000000000, false);
    dev_pm_opp_put(opp);
    /* 错误检查 */
    if (!IS_ERR(opp))
        ret = dev_pm_opp_enable(dev, 1000000000);
    else
        goto try_something_else;
}
```

`dev_pm_opp_disable`
---
使一个 OPP 不可用。

#### 示例：假设 1GHz OPP 在温度超过阈值时被禁用。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp > temp_high_thresh) {
    /* 如果 1GHz 被启用，则禁用它 */
    opp = dev_pm_opp_find_freq_exact(dev, 1000000000, true);
    dev_pm_opp_put(opp);
    /* 错误检查 */
    if (!IS_ERR(opp))
        ret = dev_pm_opp_disable(dev, 1000000000);
    else
        goto try_something_else;
}
```

### 5. OPP 数据检索函数
---
由于 OPP 库抽象了 OPP 信息，因此需要一组从 `dev_pm_opp` 结构中提取信息的函数。一旦使用搜索函数获取到 OPP 指针，SoC 框架可以使用以下函数来检索 OPP 层中表示的信息。

`dev_pm_opp_get_voltage`
---
获取由 opp 指针表示的电压。

#### 示例：在 cpufreq 转换到不同频率时，SoC 框架需要使用调节器框架将 OPP 表示的电压设置到提供电压的电源管理芯片上：

```c
soc_switch_to_freq_voltage(freq)
{
    /* 执行一些操作 */
    opp = dev_pm_opp_find_freq_ceil(dev, &freq);
    v = dev_pm_opp_get_voltage(opp);
    dev_pm_opp_put(opp);
    if (v)
        regulator_set_voltage(.., v);
    /* 执行其他操作 */
}
```

`dev_pm_opp_get_freq`
---
获取由 opp 指针表示的频率。

#### 示例：假设 SoC 框架使用了一些辅助函数，我们可以传递 opp 指针而不是处理大量数据参数：

```c
soc_cpufreq_target(..)
{
    /* 执行一些操作 */
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
    /* 执行一些操作 */
}
```

`dev_pm_opp_get_opp_count`
---
获取设备可用的 OPP 数量。

#### 示例：假设 SoC 中的一个协处理器需要知道可用频率表，主处理器可以如下通知：

```c
soc_notify_coproc_available_frequencies()
{
    /* 执行一些操作 */
    num_available = dev_pm_opp_get_opp_count(dev);
    speeds = kcalloc(num_available, sizeof(u32), GFP_KERNEL);
    /* 按递增顺序填充表 */
    freq = 0;
    i = 0;
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
---
通常一个 SoC 包含多个可变电压域。每个域由一个设备指针表示。OPP 与其关系可以表示如下：

```
  SoC
   |- device 1
   |  |- opp 1 (可用性，频率，电压)
   |  |- opp 2 ...
```
```
|	`- opp n .
|- device 2
   ..
`- device m

OPP 库维护了一个由 SoC 框架填充并被各种函数访问的内部列表，如上所述。然而，表示实际 OPP 和域的结构是 OPP 库内部的，以便提供适用于跨系统的抽象。

`struct dev_pm_opp`
    OPP 库的内部数据结构，用于表示一个 OPP。除了频率、电压和可用性信息外，它还包含 OPP 库操作所需的内部管理信息。此结构体指针会返回给用户（例如 SoC 框架），用作与 OPP 层交互时 OPP 的标识符。

警告：
    用户不应解析或修改 `struct dev_pm_opp` 指针。实例的默认值由 `dev_pm_opp_add` 填充，但 OPP 的可用性可以通过 `dev_pm_opp_enable` 和 `dev_pm_opp_disable` 函数进行修改。

`struct device`
    用于向 OPP 层标识一个域。设备的性质及其实现由 OPP 库的用户（例如 SoC 框架）自行决定。

总体而言，从简化角度来看，数据结构的操作如下所示：

初始化/修改：
              +-----+        /- dev_pm_opp_enable
  dev_pm_opp_add --> | opp | <-------
    |         +-----+        \- dev_pm_opp_disable
    \-------> domain_info(device)

搜索函数：
               /-- dev_pm_opp_find_freq_ceil  ---\   +-----+
  domain_info<---- dev_pm_opp_find_freq_exact -----> | opp |
               \-- dev_pm_opp_find_freq_floor ---/   +-----+

检索函数：
  +-----+     /- dev_pm_opp_get_voltage
  | opp | <---
  +-----+     \- dev_pm_opp_get_freq

  domain_info <- dev_pm_opp_get_opp_count
```
