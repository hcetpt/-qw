======================
操作性能点 (OPP) 库
======================

(C) 2009-2010 Nishanth Menon <nm@ti.com>, 德州仪器公司

.. 目录

  1. 引言
  2. 初始 OPP 列表注册
  3. OPP 搜索函数
  4. OPP 可用性控制函数
  5. OPP 数据检索函数
  6. 数据结构

1. 引言
===============

1.1 什么是操作性能点 (OPP)?
---------------------------------

当今复杂的片上系统 (SoC) 包含多个子模块协同工作。
在执行各种使用案例的操作系统中，并非所有 SoC 中的模块都需要始终以最高性能频率运行。为了实现这一点，SoC 中的子模块被分组到域中，允许某些域以较低的电压和频率运行，而其他域则以更高的电压/频率对运行。
由每个域支持的一系列离散的频率和电压对被称为操作性能点 (OPP)。
例如：

考虑一个支持以下性能的微处理器单元 (MPU) 设备：
{300MHz 在最低1V电压下}、{800MHz 在最低1.2V电压下}、{1GHz 在最低1.3V电压下}。

我们可以将这些表示为三个 OPP，如下所示的 {Hz, uV} 元组：

- {300000000, 1000000}
- {800000000, 1200000}
- {1000000000, 1300000}

1.2 操作性能点库
-----------------------------------

OPP 库提供了一组辅助函数来组织和查询 OPP 信息。该库位于 `drivers/opp/` 目录中，其头文件位于 `include/linux/pm_opp.h`。可以通过从电源管理菜单配置启用 CONFIG_PM_OPP 来启用 OPP 库。某些 SoC（如德州仪器的 OMAP 框架）允许选择性地在特定 OPP 下启动，无需 cpufreq。
OPP 库的典型使用情况如下：

(用户) -> 注册一组默认 OPP -> (库)
SoC 框架 -> 根据需要修改某些 OPP -> OPP 层
         -> 查询以搜索/检索信息 ->

OPP 层期望每个域都由一个唯一的设备指针表示。SoC 框架为每个设备向 OPP 层注册一组初始 OPP。此列表预期是一个最优的小数量，通常每个设备大约为 5 个。
此初始列表包含框架预期系统默认安全启用的一组 OPP。
关于 OPP 可用性的注释
^^^^^^^^^^^^^^^^^^^^^^^^

随着系统的运行，SoC 框架可能会根据各种外部因素选择使每个设备上的某些 OPP 可用或不可用。示例用途：热管理或其他特殊情况，在这些情况下，SoC 框架可能会选择禁用较高的频率 OPP 以安全地继续运行，直到可能重新启用 OPP。
OPP 库在其实现中促进了这一概念。以下操作函数仅在可用 OPP 上操作：
dev_pm_opp_find_freq_{ceil, floor}、dev_pm_opp_get_voltage、dev_pm_opp_get_freq、dev_pm_opp_get_opp_count
dev_pm_opp_find_freq_exact 旨在用于查找 OPP 指针，然后可以使用 dev_pm_opp_enable/disable 函数按需使 OPP 可用。
警告：如果调用了 dev_pm_opp_enable/disable 函数，则 OPP 库的用户应使用 get_opp_count 刷新其可用性计数。触发这些操作的确切机制或通知其他依赖子系统（如 cpufreq）的机制留给使用 OPP 库的具体 SoC 框架自行决定。在进行这些操作时，需要注意刷新 cpufreq 表。
### 2. 初始 OPP 列表注册
================================
SoC 实现通过迭代调用 `dev_pm_opp_add` 函数来为每个设备添加 OPP。预期 SoC 框架将以最优方式注册 OPP 条目——典型的数量少于 5 个。通过注册 OPP 生成的列表在整个设备运行过程中由 OPP 库维护。SoC 框架随后可以使用 `dev_pm_opp_enable`/`disable` 函数动态控制 OPP 的可用性。

`dev_pm_opp_add`
    为特定域（由设备指针表示）添加一个新的 OPP。
    
    OPP 通过频率和电压定义。一旦添加，假设 OPP 是可用的，并且可以通过 `dev_pm_opp_enable`/`disable` 函数来控制其可用性。OPP 库内部在 `dev_pm_opp` 结构体中存储并管理这些信息。
    
    此函数可被 SoC 框架用于根据 SoC 使用环境的需求定义一个最优列表。
    
**警告：**
    不要在中断上下文中使用此函数。
    
示例：

```c
soc_pm_init()
{
    /* 做一些事情 */
    r = dev_pm_opp_add(mpu_dev, 1000000, 900000);
    if (!r) {
        pr_err("%s: 无法注册 mpu opp(%d)\n", r);
        goto no_cpufreq;
    }
    /* 处理 cpufreq 相关的事情 */
no_cpufreq:
    /* 处理剩余的事情 */
}
```

### 3. OPP 搜索函数
=======================
高级框架（如 cpufreq）基于频率操作。为了将频率映射回相应的 OPP，OPP 库提供了方便的函数来搜索由 OPP 库内部管理的 OPP 列表。如果找到匹配项，则这些搜索函数返回代表 opp 的匹配指针；否则返回错误。这些错误应通过标准错误检查（如 `IS_ERR()`）处理，并采取适当的行动。
调用这些函数的程序应在使用 OPP 后调用 `dev_pm_opp_put()`。否则，OPP 的内存永远不会释放，导致内存泄漏。

`dev_pm_opp_find_freq_exact`
    根据 *精确* 频率和可用性搜索 OPP。此函数特别适用于启用默认情况下不可用的 OPP。
    
示例：当 SoC 框架检测到可以提供更高频率的情况时，它可以使用此函数找到 OPP，在实际调用 `dev_pm_opp_enable` 之前。

```c
opp = dev_pm_opp_find_freq_exact(dev, 1000000000, false);
dev_pm_opp_put(opp);
/* 不要直接操作指针...只需进行简单的检查... */
if (IS_ERR(opp)) {
    pr_err("频率未禁用!\n");
    /* 触发适当的行动... */
} else {
    dev_pm_opp_enable(dev,1000000000);
}
```

**注释：**
    这是唯一一个可以在不可用 OPP 上操作的搜索函数。

`dev_pm_opp_find_freq_floor`
    搜索可用 OPP，该 OPP 的频率 *至多* 等于提供的频率。此函数在搜索较小匹配或按频率递减顺序操作 OPP 信息时非常有用。
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

默认注册到 OPP 库的 OPP 列表可能不适用于所有情况。OPP 库提供了一系列函数来修改 OPP 列表中的 OPP 的可用性。这允许 SoC 框架对哪些 OPP 组可以运行有精细的动态控制。

这些函数旨在**暂时**在某些情况下（例如基于温度考虑，如不要使用 OPPx 直到温度下降）移除一个 OPP。
**警告**：
不要在中断上下文中使用这些函数。

`dev_pm_opp_enable`
使 OPP 可用于操作。
#### 示例：假设只有当 SoC 温度低于某个阈值时，1GHz OPP 才可用。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp < temp_low_thresh) {
    /* 如果已禁用，则启用 1GHz */
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
使 OPP 不可用于操作。
#### 示例：假设如果温度超过阈值，则禁用 1GHz OPP。SoC 框架实现可能会选择如下操作：

```c
if (cur_temp > temp_high_thresh) {
    /* 如果已启用，则禁用 1GHz */
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

由于 OPP 库抽象了 OPP 信息，因此需要一组函数从 `dev_pm_opp` 结构中提取信息。一旦通过搜索函数获取了 OPP 指针，SoC 框架就可以使用以下函数检索 OPP 层内部表示的信息。

`dev_pm_opp_get_voltage`
检索由 opp 指针表示的电压。
#### 示例：在 cpufreq 转换到不同频率时，SoC 框架需要使用调节器框架设置 OPP 表示的电压到供电管理芯片：

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
检索由 opp 指针表示的频率。
#### 示例：假设 SoC 框架使用几个辅助函数，我们可以传递 opp 指针而不是处理大量的数据参数：

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
检索设备可用的 OPP 数量。
#### 示例：假设 SoC 中的协处理器需要知道可用频率列表，主处理器可以这样通知：

```c
soc_notify_coproc_available_frequencies()
{
    /* 执行一些操作 */
    num_available = dev_pm_opp_get_opp_count(dev);
    speeds = kcalloc(num_available, sizeof(u32), GFP_KERNEL);
    /* 按照递增顺序填充表格 */
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

通常，SoC 包含多个可变电压域。每个域由一个设备指针表示。与 OPP 的关系可以表示如下：

```
SoC
   |- 设备 1
   |    |- OPP 1 (可用性、频率、电压)
   |    |- OPP 2 ...
...
```
OPP (Operating Performance Points) 库维护了一个内部列表，该列表由 SoC (System on Chip) 框架填充，并通过上述描述的各种函数进行访问。然而，表示实际 OPP 和域的结构体是 OPP 库内部的，以便实现适用于跨系统的适当抽象。

`struct dev_pm_opp`
这是 OPP 库使用的内部数据结构，用于表示一个 OPP。除了频率、电压和可用性信息之外，它还包含 OPP 库操作所需的内部管理信息。此结构体的指针会提供给用户（例如 SoC 框架），作为与 OPP 层交互时 OPP 的标识符使用。

**警告：**
用户不应解析或修改 `struct dev_pm_opp` 指针。一个实例的默认值由 `dev_pm_opp_add` 函数填充，但 OPP 的可用性可以通过 `dev_pm_opp_enable` 或 `dev_pm_opp_disable` 函数进行修改。

`struct device`
此结构体用于向 OPP 层标识一个域。设备的特性和其实现留给 OPP 库的用户（如 SoC 框架）自行决定。

总体而言，从简化视角来看，数据结构的操作如下所示：

- **初始化/修改：**
  
  ```
            +-----+        /- dev_pm_opp_enable
  dev_pm_opp_add --> | opp | <-------
    |         +-----+        \- dev_pm_opp_disable
    \-------> domain_info(device)
  ```

- **搜索函数：**

  ```
               /-- dev_pm_opp_find_freq_ceil  ---\   +-----+
  domain_info<---- dev_pm_opp_find_freq_exact -----> | opp |
               \-- dev_pm_opp_find_freq_floor ---/   +-----+
  ```

- **检索函数：**

  ```
  +-----+     /- dev_pm_opp_get_voltage
  | opp | <---
  +-----+     \- dev_pm_opp_get_freq
  ```

  ```
  domain_info <- dev_pm_opp_get_opp_count
  ```
