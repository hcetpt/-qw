### SPDX 许可证标识符：GPL-2.0

=======================
设备的能耗模型
=======================

1. 概览
-----------

能耗模型（EM）框架作为接口存在，它连接了解设备在不同性能级别下功耗的驱动程序与希望利用这些信息来做出节能决策的内核子系统。关于设备功耗的信息来源可能因平台而异。
在某些情况下，可以通过设备树数据来估算这些功耗成本。在其他情况下，固件可能更清楚。或者，用户空间可能处于最佳位置。如此等等。为了避免每个客户端子系统单独重新实现对每种可能信息源的支持，EM框架作为抽象层介入，以标准化内核中功耗成本表的格式，从而避免重复工作。
功耗值可以表示为微瓦或“抽象尺度”。
多个子系统可能会使用EM，并且由系统集成商确保功耗值尺度类型的要求得到满足。一个例子可以在《节能调度器文档》中找到：`Documentation/scheduler/sched-energy.rst`。对于像热管理和电源限制这样的某些子系统而言，如果功耗值表示为“抽象尺度”，可能会出现问题。
这些子系统更关心过去使用的功率估计值，因此可能需要真实的微瓦数。这些要求的一个例子可以在《智能电源分配》中找到：`Documentation/driver-api/thermal/power_allocator.rst`。
内核子系统可以实现自动检测以检查注册到EM的设备是否具有不一致的尺度（基于EM内部标志）。
重要的是要记住，当功耗值表示为“抽象尺度”时，无法推导出真实的能量（微焦耳）。
下面的图示例展示了驱动程序（这里特定于ARM，但该方法适用于任何架构）向EM框架提供功耗成本，以及感兴趣的客户端从其中读取数据的情况：

```
       +---------------+  +-----------------+  +---------------+
       | 热管理 (IPA)  |  | 调度器 (EAS)    |  | 其他          |
       +---------------+  +-----------------+  +---------------+
               |                   | em_cpu_energy()   |
               |                   | em_cpu_get()      |
               +---------+         |         +---------+
                         |         |         |
                         v         v         v
                        +---------------------+
                        |    能耗模型         |
                        |     框架           |
                        +---------------------+
                           ^       ^       ^
                           |       |       | em_dev_register_perf_domain()
                +----------+       |       +---------+
                |                  |                 |
        +---------------+  +---------------+  +--------------+
        |  cpufreq-dt   |  |   arm_scmi    |  |    其他      |
        +---------------+  +---------------+  +--------------+
                ^                  ^                 ^
                |                  |                 |
        +--------------+   +---------------+  +--------------+
        | 设备树      |   |   固件        |  |      ?       |
        +--------------+   +---------------+  +--------------+
```

对于CPU设备，EM框架按系统的“性能域”管理功耗成本表。性能域是一组一起调整性能的CPU。性能域通常与CPUFreq策略一对一映射。性能域中的所有CPU都必须具有相同的微架构。不同性能域中的CPU可以有不同的微架构。
为了更好地反映由于静态功耗（泄漏）引起的功耗变化，EM支持运行时修改功耗值。这种机制依赖于RCU来释放可修改的EM perf_state表内存。其使用者，任务调度器，也使用RCU来访问此内存。EM框架提供了用于为可修改的EM表分配/释放新内存的API。
旧的内存会自动通过RCU回调机制释放，当给定的EM运行时表实例不再有所有者时。这是通过kref机制进行跟踪的。在运行时提供新的EM的设备驱动程序，在不再需要它时，应该调用EM API来安全地释放它。EM框架会在可能的情况下处理清理工作。

希望修改EM值的内核代码使用互斥锁来防止并发访问。因此，当设备驱动程序试图修改EM时，必须在可睡眠上下文中运行。

借助可运行时修改的EM，我们从“单一且在整个运行时静态的EM”（系统属性）设计转变为“单一EM可以根据工作负载等在运行时更改”的设计（系统和工作负载属性）。

也可以为每个EM的性能状态修改CPU性能值。因此，可以按照工作负载或系统属性等，改变完整的功率和性能配置文件（这是一条指数曲线）。

2. 核心APIs
------------

2.1 配置选项
^^^^^^^^^^^^^^

必须启用CONFIG_ENERGY_MODEL才能使用EM框架。

2.2 性能域的注册
^^^^^^^^^^^^^^^^^^^

### “高级”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

“高级”EM之所以如此命名是因为驱动程序被允许提供更精确的功耗模型。它不限于框架中实现的一些数学公式（如“简单”EM情况）。它可以更好地反映为每个性能状态执行的实际功耗测量。因此，如果考虑EM静态功耗（泄漏）很重要，则应优先选择此注册方法。

预期驱动程序通过调用以下API将性能域注册到EM框架中：

```c
int em_dev_register_perf_domain(struct device *dev, unsigned int nr_states,
		struct em_data_callback *cb, cpumask_t *cpus, bool microwatts);
```

驱动程序必须提供一个回调函数，返回每个性能状态的<频率，功耗>元组。驱动程序提供的回调函数可以自由地从任何相关位置（设备树、固件等）获取数据，并采用认为必要的任何方式。仅对于CPU设备，驱动程序必须使用cpumask指定性能域中的CPU。对于非CPU设备，最后一个参数必须设置为NULL。

最后一个参数'microwatts'非常重要，需要设置正确的值。使用EM的内核子系统可能依赖这个标志来检查所有EM设备是否使用相同的单位。如果有不同的单位，这些子系统可能会决定返回警告/错误、停止工作或触发panic。

参见第3节了解实现此回调的驱动程序示例，或者参阅第2.4节以获取更多关于此API的文档。

### 使用设备树(Devicetree)注册EM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EM也可以通过OPP框架和设备树中的信息“operating-points-v2”进行注册。设备树中的每个OPP条目可以通过包含微瓦特功耗值的属性“opp-microwatt”进行扩展。这个OPP设备树属性允许平台注册反映总功耗（静态+动态）的EM功耗值。这些功耗值可能直接来自实验和测量。

### “人工”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

有一个选项是为缺少每个性能状态详细功耗知识的驱动程序提供自定义回调。回调.get_cost()是可选的，它提供EAS使用的“成本”值。
这对于仅提供不同类型CPU之间相对效率信息的平台非常有用，可以利用这些信息来创建抽象的功耗模型。但即使是一个抽象的功耗模型，在考虑到输入功率值大小限制的情况下有时也难以适用。`.get_cost()`允许提供反映CPU效率的“成本”值。这将允许提供与EM内部公式计算出的“成本”值所强制的关系不同的EAS信息。为了在这样的平台上注册EM，驱动程序必须将`microwatts`标志设置为0，并提供`.get_power()`回调以及`.get_cost()`回调。EM框架将在注册时正确处理这种平台。对于此类平台会设置一个标志`EM_PERF_DOMAIN_ARTIFICIAL`。其他使用EM的框架应当特别注意并妥善测试和处理此标志。
### “简单”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~

“简单”EM使用框架辅助函数`cpufreq_register_em_with_opp()`进行注册。它实现了一个与数学公式紧密相关的功耗模型：
```
Power = C * V^2 * f
```
通过这种方法注册的EM可能无法准确反映真实设备的物理特性，例如当静态功耗（泄漏）非常重要时。
### 2.3 访问性能域
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

有两种API函数提供了访问能量模型的方式：`em_cpu_get()`接受CPU ID作为参数，而`em_pd_get()`则接受设备指针作为参数。取决于子系统将使用哪个接口，但对于CPU设备而言，这两个函数返回相同的性能域。
对CPU的能量模型感兴趣的子系统可以使用`em_cpu_get()` API获取该信息。能量模型表在性能域创建时一次性分配，并且在内存中保持不变。
可以通过`em_cpu_energy()` API估计性能域消耗的能量。该估计假设使用了schedutil CPUfreq管理器（针对CPU设备）。目前，这种计算尚未为其他类型的设备提供。
关于上述API的更多详细信息可以在`<linux/energy_model.h>`中找到或参见第2.5节。

### 2.4 运行时修改
^^^^^^^^^^^^^^^^^^^^^^^^^

希望在运行时更新EM的驱动程序应使用以下专用函数来分配修改后的EM的新实例。API如下所示：
```c
struct em_perf_table __rcu *em_table_alloc(struct em_perf_domain *pd);
```
这允许分配一个包含新EM表及其所需的RCU和kref结构的结构体，以便EM框架使用。`struct em_perf_table` 包含一个数组`struct em_perf_state state[]`，这是一个按升序排列的性能状态列表。这个列表必须由希望更新EM的设备驱动程序填充。`struct em_perf_state`的内容也必须由驱动程序填充。
以下是使用RCU指针交换执行EM更新的API：
```c
int em_dev_update_perf_domain(struct device *dev,
            struct em_perf_table __rcu *new_table);
```
驱动程序必须提供已分配和初始化的新EM `struct em_perf_table` 的指针。这个新的EM将在EM框架内安全地使用，并将对内核中的其他子系统（如热管理和电源限制）可见。
此API的主要设计目标是快速并且避免在运行时进行额外的计算或内存分配。如果设备驱动程序中已经存在预计算的EM，则应当能够以较低的性能开销直接重用它们。
为了释放之前由驱动程序提供的EM（例如，当模块被卸载时），需要调用以下API：
```c
void em_table_free(struct em_perf_table __rcu *table);
```
这将使EM框架能够在没有其他子系统使用的情况下安全地释放内存，例如EAS。
为了在其他子系统（如热管理、功耗上限等）中使用功耗值，需要调用一个API来保护读取者并确保EM表数据的一致性：

```c
struct em_perf_state *em_perf_state_from_pd(struct em_perf_domain *pd);
```

此函数返回一个指向`em_perf_state`结构体的指针，该结构体是一个按升序排列的性能状态数组。
此函数必须在RCU读锁部分（即在`rcu_read_lock()`之后）调用。当不再需要EM表时，则需要调用`rcu_read_unlock()`。这样EM就能安全地使用RCU读取部分，并保护用户。它还允许EM框架管理内存并释放它。更多关于如何使用它的细节可以在示例驱动程序的第3.2节中找到。
对于设备驱动程序，有一个专用的API来计算`em_perf_state::cost`值：

```c
int em_dev_compute_costs(struct device *dev, struct em_perf_state *table, int nr_states);
```

这些来自EM的“成本”值会被EAS使用。新的EM表应该与条目数量和设备指针一起传递。如果成本值计算正确，该函数的返回值为0。
此函数还会为每个性能状态设置正确的无效性，并相应地更新`em_perf_state::flags`。
然后，可以将准备好的新EM表传递给`em_dev_update_perf_domain()`函数，以允许其被使用。
更多关于上述API的信息可以在`<linux/energy_model.h>`中或在第3.2节中的示例代码中找到，该代码展示了设备驱动程序中更新机制的简单实现。

### 2.5 此API描述详情

此处省略了具体的内核文档说明，请参阅相关内核文档。

### 3. 示例

#### 3.1 具有EM注册功能的示例驱动

CPUFreq框架支持一个专门的回调函数来为特定CPU(s)的“策略”对象注册EM：`cpufreq_driver::register_em()`。
对于特定驱动程序，必须正确实现该回调函数，因为框架会在设置过程中适时调用它。
本节提供了一个简单的CPUFreq驱动程序示例，该驱动程序使用（假定的）“foo”协议在能源模型框架中注册性能域。该驱动程序实现了一个`est_power()`函数，用于提供给EM框架。

```c
// -> drivers/cpufreq/foo_cpufreq.c

static int est_power(struct device *dev, unsigned long *mW, unsigned long *KHz) {
    long freq, power;

    // 使用'foo'协议获取频率上限
    freq = foo_get_freq_ceil(dev, *KHz);
    if (freq < 0)
        return freq;

    // 估计设备在相关频率下的功耗成本
    power = foo_estimate_power(dev, freq);
    if (power < 0)
        return power;

    // 将值返回给EM框架
    *mW = power;
    *KHz = freq;

    return 0;
}

static void foo_cpufreq_register_em(struct cpufreq_policy *policy) {
    struct em_data_callback em_cb = EM_DATA_CB(est_power);
    struct device *cpu_dev;
    int nr_opp;

    cpu_dev = get_cpu_device(cpumask_first(policy->cpus));

    // 查找此策略的OPP数量
    nr_opp = foo_get_nr_opp(policy);

    // 注册新的性能域
    em_dev_register_perf_domain(cpu_dev, nr_opp, &em_cb, policy->cpus, true);
}

static struct cpufreq_driver foo_cpufreq_driver = {
    .register_em = foo_cpufreq_register_em,
};
```

#### 3.2 具有EM修改功能的示例驱动

本节提供了一个简单的热管理驱动程序示例，用于修改EM。
该驱动程序实现了`foo_thermal_em_update()`函数。驱动程序会周期性地被唤醒以检查温度并修改EM数据。

```c
// -> drivers/soc/example/example_em_mod.c

static void foo_get_new_em(struct foo_context *ctx) {
    struct em_perf_table __rcu *em_table;
    struct em_perf_state *table, *new_table;
    struct device *dev = ctx->dev;
    struct em_perf_domain *pd;
    unsigned long freq;
    int i, ret;

    pd = em_pd_get(dev);
    if (!pd)
        return;

    em_table = em_table_alloc(pd);
    if (!em_table)
        return;

    new_table = em_table->state;

    rcu_read_lock();
    table = em_perf_state_from_pd(pd);
    for (i = 0; i < pd->nr_perf_states; i++) {
        freq = table[i].frequency;
        foo_get_power_perf_values(dev, freq, &new_table[i]);
    }
    rcu_read_unlock();

    // 计算EAS所需的“cost”值
    ret = em_dev_compute_costs(dev, table, pd->nr_perf_states);
    if (ret) {
        dev_warn(dev, "EM: compute costs failed %d\n", ret);
        em_free_table(em_table);
        return;
    }

    ret = em_dev_update_perf_domain(dev, em_table);
    if (ret) {
        dev_warn(dev, "EM: update failed %d\n", ret);
        em_free_table(em_table);
        return;
    }

    // 由于是一次性更新，释放使用计数器
}
```
```
45         * EM框架将在需要时稍后释放该表
46         */
47         em_table_free(em_table);
48     }
49

50         /*
51         * 定期调用的函数，用于检查温度并在需要时更新EM
52         */
53         static void foo_thermal_em_update(struct foo_context *ctx)
54         {
55             struct device *dev = ctx->dev;
56             int cpu;

57             ctx->temperature = foo_get_temp(dev, ctx);
58             if (ctx->temperature < FOO_EM_UPDATE_TEMP_THRESHOLD)
59                 return;

60             foo_get_new_em(ctx);
61         }
