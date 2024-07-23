...SPDX 许可证标识符：GPL-2.0

=======================
设备的能耗模型
=======================

1. 概览
-----------

能耗模型（EM）框架充当了驱动程序与内核子系统之间的接口，这些驱动程序了解设备在不同性能级别下的功耗，而内核子系统则希望使用这些信息来做出节能决策。
关于设备功耗的信息来源可能在不同平台之间差异很大。在某些情况下，这些功耗成本可以使用设备树数据进行估算。在其他情况下，固件可能更了解情况。或者，用户空间可能处于最佳位置。诸如此类。为了避免每个客户端子系统单独重新实现对每种可能信息源的支持，EM框架作为抽象层介入，标准化了内核中功耗成本表的格式，从而避免了重复工作。
功耗值可以用微瓦或“抽象比例尺”表示。
多个子系统可能会使用EM，并且系统集成商需要确保功耗值比例尺类型的要求得到满足。一个例子可以在《节能感知调度器文档》中找到：Documentation/scheduler/sched-energy.rst。对于像热管理和功率限制这样的某些子系统，用“抽象比例尺”表示的功耗值可能会引起问题。这些子系统更关心过去使用的功率估计，因此可能需要实际的微瓦数。这些要求的一个示例可以在《智能功率分配》中找到：Documentation/driver-api/thermal/power_allocator.rst。
内核子系统可以实现自动检测，以检查EM注册设备是否存在不一致的比例尺（基于EM内部标志）。
重要的是要记住，当功耗值以“抽象比例尺”表示时，无法推导出真实的能量（微焦耳）。
下图描绘了一个示例，其中驱动程序（此处是特定于Arm的，但方法适用于任何架构）向EM框架提供功耗成本，而感兴趣的客户端从框架读取数据：

       +---------------+  +-----------------+  +---------------+
       | 热管理（IPA）|  | 调度器（EAS）|  | 其他 |
       +---------------+  +-----------------+  +---------------+
               |                   | em_cpu_energy()   |
               |                   | em_cpu_get()      |
               +---------+         |         +---------+
                         |         |         |
                         v         v         v
                        +---------------------+
                        |    能耗模型     |
                        |     框架       |
                        +---------------------+
                           ^       ^       ^
                           |       |       | em_dev_register_perf_domain()
                +----------+       |       +---------+
                |                  |                 |
        +---------------+  +---------------+  +--------------+
        |  cpufreq-dt   |  |   arm_scmi    |  |    其他     |
        +---------------+  +---------------+  +--------------+
                ^                  ^                 ^
                |                  |                 |
        +--------------+   +---------------+  +--------------+
        | 设备树  |   |   固件    |  |      ?       |
        +--------------+   +---------------+  +--------------+

对于CPU设备，EM框架按系统中的“性能域”管理功耗成本表。性能域是一组一起调整性能的CPU。性能域通常与CPUFreq策略一一对应。性能域内的所有CPU都必须具有相同的微架构。不同性能域中的CPU可以有不同的微架构。
为了更好地反映由于静态功率（泄漏）引起的功率变化，EM支持运行时修改功率值。该机制依赖于RCU来释放可修改的EM perf_state表内存。其用户，任务调度器，也使用RCU来访问此内存。EM框架提供了用于为可修改的EM表分配和释放新内存的API。
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

“高级”EM之所以如此命名是因为驱动程序被允许提供更精确的功耗模型。它不限于框架中实现的一些数学公式（如“简单”EM的情况）。它可以更好地反映为每个性能状态执行的实际功耗测量。因此，在考虑EM静态功耗（泄漏）重要的情况下，应优先选择此注册方法。

预期驱动程序通过调用以下API将性能域注册到EM框架中：

```c
int em_dev_register_perf_domain(struct device *dev, unsigned int nr_states,
		struct em_data_callback *cb, cpumask_t *cpus, bool microwatts);
```

驱动程序必须提供一个回调函数，返回每个性能状态下的<频率，功耗>元组。驱动程序提供的回调函数可以自由地从任何相关位置（设备树、固件等）获取数据，并采用认为必要的任何方式。仅对于CPU设备，驱动程序必须使用cpumask指定性能域中的CPU。对于非CPU设备，最后一个参数必须设置为NULL。

最后一个参数'microwatts'非常重要，需要设置正确的值。使用EM的内核子系统可能会依赖这个标志来检查所有EM设备是否使用相同的单位。如果存在不同的单位，这些子系统可能会决定返回警告/错误、停止工作或引发恐慌。

请参阅第3节了解实现此回调的驱动程序示例，或第2.4节了解有关此API的更多文档。

### 使用设备树注册EM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EM还可以使用OPP框架和设备树中的信息“operating-points-v2”进行注册。设备树中的每个OPP条目都可以扩展一个包含微瓦特功耗值的属性"opp-microwatt"。这个OPP设备树属性允许平台注册反映总功耗（静态+动态）的EM功耗值。这些功耗值可能直接来自实验和测量。

### “人工”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

有一个选项可供那些缺乏关于每个性能状态详细功耗知识的驱动程序提供自定义回调。回调.get_cost()是可选的，它提供了EAS使用的“成本”值。
这对于仅提供不同类型CPU之间相对效率信息的平台非常有用，人们可以利用这些信息来创建一个抽象的功率模型。但是，即使是一个抽象的功率模型，在给定输入功率值大小限制的情况下有时也难以适应。`.get_cost()`允许提供反映CPU效率的“成本”值。这将允许提供与EM内部公式计算的“成本”值所强制的关系不同的EAS信息。为了在这样的平台上注册EM，驱动程序必须将`microwatts`标志设置为0，提供`.get_power()`回调，并提供`.get_cost()`回调。EM框架将在注册时妥善处理此类平台。为此类平台设置了EM_PERF_DOMAIN_ARTIFICIAL标志。使用EM的其他框架应特别注意，正确测试和处理此标志。

“简单”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~
使用框架辅助函数`cpufreq_register_em_with_opp()`注册“简单”EM。它实现了一个紧密绑定于数学公式的功率模型：
```
Power = C * V^2 * f
```
通过这种方法注册的EM可能无法准确反映真实设备的物理特性，例如当静态功率（泄漏）很重要时。
### 2.3 访问性能域
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

有两种API函数提供了对能源模型的访问：`em_cpu_get()`，它以CPU ID作为参数；以及`em_pd_get()`，以设备指针作为参数。具体使用哪个接口取决于子系统，但在CPU设备的情况下，这两个函数返回相同的性能域。
对CPU的能源模型感兴趣的子系统可以使用`em_cpu_get()` API检索。能源模型表在性能域创建时一次性分配，并保持在内存中不被触碰。
可以通过`em_cpu_energy()` API估计性能域消耗的能量。这一估算假设在CPU设备上使用了schedutil CPUfreq控制器。目前，对于其他类型的设备尚未提供这种计算。
关于上述API的更多详细信息可以在`<linux/energy_model.h>`或第2.5节中找到。

### 2.4 运行时修改
^^^^^^^^^^^^^^^^^^^^^^^^^

希望在运行时更新EM的驱动程序应使用以下专用函数来分配修改后的EM的新实例。下面列出了API：
```c
struct em_perf_table __rcu *em_table_alloc(struct em_perf_domain *pd);
```
这允许分配一个包含新EM表的结构，同时包含EM框架所需的RCU和kref。`struct em_perf_table`包含数组`struct em_perf_state state[]`，这是按升序排列的性能状态列表。该列表必须由想要更新EM的设备驱动程序填充。`struct em_perf_state`中的内容也必须由驱动程序填充。
以下是使用RCU指针交换进行EM更新的API：
```c
int em_dev_update_perf_domain(struct device *dev,
		struct em_perf_table __rcu *new_table);
```
驱动程序必须提供指向已分配并初始化的新EM `struct em_perf_table`的指针。这个新的EM将在EM框架内安全地使用，并对内核中的其他子系统（如热管理和电源限制）可见。
此API的主要设计目标是快速且避免在运行时进行额外的计算或内存分配。如果设备驱动程序中可用预计算的EM，则应该能够以较低的性能开销简单地重用它们。
为了释放由驱动程序（例如在模块卸载时）提供的EM，需要调用以下API：
```c
void em_table_free(struct em_perf_table __rcu *table);
```
这将允许EM框架在没有其他子系统使用时安全地移除内存，例如EAS。
为了在其他子系统（如热管理，功耗上限）中使用功率值，需要调用一个API，该API保护读取者并确保能量模型(EM)表数据的一致性：

```c
struct em_perf_state *em_perf_state_from_pd(struct em_perf_domain *pd);
```

此函数返回一个指向`struct em_perf_state`的指针，该结构是一个按升序排列的性能状态数组。
此函数必须在RCU读锁部分（即`rcu_read_lock()`之后）调用。当不再需要EM表时，需调用`rcu_read_unlock()`。这样，EM安全地使用RCU读取部分，保护用户，并允许EM框架管理内存和释放它。如何使用它的更多细节可以在示例驱动程序的第3.2节找到。
对于设备驱动程序计算`em_perf_state::cost`值，有专门的API：

```c
int em_dev_compute_costs(struct device *dev, struct em_perf_state *table,
                         int nr_states);
```

这些从EM获取的“成本”值在EAS中使用。新的EM表应与条目数量和设备指针一起传递。当成本值的计算正确完成时，函数的返回值为0。
该函数还负责为每个性能状态设置正确的效率。它相应更新`em_perf_state::flags`。
然后，准备好的新EM可以传递给`em_dev_update_perf_domain()`函数，从而可以使用它。
关于上述API的更多详细信息可以在`<linux/energy_model.h>`中找到，或者在第3.2节中，示例代码展示了在设备驱动程序中简单实现更新机制。

### 2.5 API描述细节

这部分详细描述了API，具体可见`include/linux/energy_model.h`和`kernel/power/energy_model.c`中的内核文档。

### 3. 示例

#### 3.1 带有EM注册的示例驱动程序

CPUFreq框架支持专用回调以在给定的CPU(s)策略对象上注册EM：`cpufreq_driver::register_em()`。
该回调必须为特定驱动程序正确实现，因为框架会在设置过程中适当时候调用它。
本节提供了一个简单的CPUFreq驱动程序示例，使用（假想的）'foo'协议在能源模型框架中注册性能域。驱动程序实现了一个`est_power()`函数以供EM框架使用：

```c
// -> drivers/cpufreq/foo_cpufreq.c

static int est_power(struct device *dev, unsigned long *mW,
                     unsigned long *KHz) {
    long freq, power;

    // 使用'foo'协议来确定频率上限
    freq = foo_get_freq_ceil(dev, *KHz);
    if (freq < 0)
        return freq;

    // 预估设备在相关频率下的功率消耗
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

    // 找到该策略的OPP数量
    nr_opp = foo_get_nr_opp(policy);

    // 注册新的性能域
    em_dev_register_perf_domain(cpu_dev, nr_opp, &em_cb, policy->cpus, true);
}

static struct cpufreq_driver foo_cpufreq_driver = {
    .register_em = foo_cpufreq_register_em,
};
```

#### 3.2 带有EM修改的示例驱动程序

本节提供了一个简单的热管理驱动程序修改EM的示例。驱动程序实现了`foo_thermal_em_update()`函数。驱动程序会周期性唤醒以检查温度并修改EM数据：

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

    // 计算用于EAS的“成本”值
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

    // 由于是一次性更新，因此可以减少使用计数
}
```
45         * EM框架将在需要时稍后释放该表
46         */
47         em_table_free(em_table);
48     }
49     
50         /*
51         * 定期调用的函数，用于检查温度并
52         * 在需要时更新EM（能量模型）
53         */
54         static void foo_thermal_em_update(struct foo_context *ctx)
55         {
56             struct device *dev = ctx->dev; // 设备结构体指针
57             int cpu;                       // CPU标识符

59             ctx->temperature = foo_get_temp(dev, ctx); // 获取设备温度
60             if (ctx->temperature < FOO_EM_UPDATE_TEMP_THRESHOLD) // 检查温度是否低于更新阈值
61                 return; // 如果低于阈值，则直接返回

63             foo_get_new_em(ctx); // 获取新的能量模型
64         }

这段代码描述了一个在特定条件下更新能量模型（Energy Model）的过程。当设备温度达到或超过预设的阈值`FOO_EM_UPDATE_TEMP_THRESHOLD`时，将触发`foo_get_new_em`函数以获取一个新的能量模型。如果温度低于这个阈值，则不进行任何操作。此外，在代码的开始部分提到了EM框架会在适当的时候释放之前使用的表。
