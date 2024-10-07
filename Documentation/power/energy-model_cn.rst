SPDX 许可证标识符: GPL-2.0

=======================
设备的能耗模型
=======================

1. 概览
-----------

能耗模型（EM）框架充当了驱动程序和内核子系统之间的接口。驱动程序了解设备在不同性能级别下的功耗，而内核子系统希望利用这些信息做出节能决策。

关于设备功耗的信息来源可能因平台而异。在某些情况下，可以通过设备树数据来估计这些功耗成本；在其他情况下，固件可能更清楚；或者用户空间可能是最佳选择，等等。为了避免每个客户端子系统单独重新实现对每种可能信息源的支持，EM 框架作为抽象层，标准化了内核中功耗成本表的格式，从而避免了重复工作。

功耗值可以表示为微瓦或“抽象尺度”。多个子系统可能会使用 EM，并且系统集成商需要确保功耗值尺度类型的要求得到满足。一个例子可以在《节能调度器文档》（Documentation/scheduler/sched-energy.rst）中找到。对于一些子系统（如温度控制或功率限制），如果功耗值用“抽象尺度”表示，可能会导致问题。这些子系统更关心过去使用的功率估计，因此可能需要实际的微瓦值。这些要求的一个例子可以在《智能功率分配》（Documentation/driver-api/thermal/power_allocator.rst）中找到。

内核子系统可以实现自动检测以检查 EM 注册设备是否具有不一致的尺度（基于 EM 内部标志）。重要的是要记住，当功耗值用“抽象尺度”表示时，无法推导出实际的能量（微焦耳）。

下图展示了一个示例：驱动程序（此处是 ARM 特定的，但方法适用于任何架构）向 EM 框架提供功耗成本，感兴趣的客户端从其中读取数据：

```
       +---------------+  +-----------------+  +---------------+
       | Thermal (IPA) |  | Scheduler (EAS) |  |     Other     |
       +---------------+  +-----------------+  +---------------+
               |                   | em_cpu_energy()   |
               |                   | em_cpu_get()      |
               +---------+         |         +---------+
                         |         |         |
                         v         v         v
                        +---------------------+
                        |    Energy Model     |
                        |     Framework       |
                        +---------------------+
                           ^       ^       ^
                           |       |       | em_dev_register_perf_domain()
                +----------+       |       +---------+
                |                  |                 |
        +---------------+  +---------------+  +--------------+
        |  cpufreq-dt   |  |   arm_scmi    |  |    Other     |
        +---------------+  +---------------+  +--------------+
                ^                  ^                 ^
                |                  |                 |
        +--------------+   +---------------+  +--------------+
        | Device Tree  |   |   Firmware    |  |      ?       |
        +--------------+   +---------------+  +--------------+
```

对于 CPU 设备，EM 框架按系统中的“性能域”管理功耗成本表。性能域是一组一起调整性能的 CPU。性能域通常与 CPUFreq 策略一一对应。性能域中的所有 CPU 必须具有相同的微架构。不同性能域中的 CPU 可以有不同的微架构。

为了更好地反映由于静态功耗（泄漏）引起的功耗变化，EM 支持运行时修改功耗值。该机制依赖于 RCU 来释放可修改的 EM perf_state 表内存。其用户（任务调度器）也使用 RCU 来访问此内存。EM 框架提供了用于分配/释放新内存以供可修改 EM 表使用的 API。
旧的内存会自动通过RCU回调机制释放，当给定的EM运行时表实例不再有所有者时。这是通过kref机制进行跟踪的。在运行时提供新EM的设备驱动程序应在不再需要时调用EM API安全地释放它。EM框架将在可能的情况下处理清理工作。

希望修改EM值的内核代码使用互斥锁来防止并发访问。因此，当设备驱动程序尝试修改EM时，必须在睡眠上下文中运行。

借助可运行时修改的EM，我们从“单一且在整个运行期间静态的EM”（系统属性）设计转变为“单一可在运行时根据负载变化的EM”（系统和负载属性）设计。

还可以修改每个EM性能状态下的CPU性能值。因此，可以完全根据负载或系统属性改变完整的功率和性能配置文件（这是一个指数曲线）。

2. 核心API
------------

2.1 配置选项
^^^^^^^^^^^^^^^^^^

必须启用CONFIG_ENERGY_MODEL才能使用EM框架。

2.2 性能域注册
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

“高级”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

“高级”EM之所以得名是因为允许驱动程序提供更精确的功耗模型。它不仅限于框架中实现的一些数学公式（如“简单”EM的情况）。它可以更好地反映为每个性能状态执行的实际功耗测量结果。因此，在考虑EM静态功耗（泄漏）的情况下，应优先选择此注册方法。
驱动程序应通过调用以下API将性能域注册到EM框架中：

```c
int em_dev_register_perf_domain(struct device *dev, unsigned int nr_states,
		struct em_data_callback *cb, cpumask_t *cpus, bool microwatts);
```

驱动程序必须提供一个回调函数，返回每个性能状态下的<频率，功耗>元组。驱动程序提供的回调函数可以自由地从任何相关位置（DT、固件等）获取数据，并采取任何认为必要的手段。仅对于CPU设备，驱动程序必须使用cpumask指定性能域中的CPU。对于非CPU设备，最后一个参数必须设置为NULL。
最后一个参数“microwatts”很重要，必须设置正确的值。使用EM的内核子系统可能会依赖此标志来检查所有EM设备是否使用相同的单位。如果存在不同的单位，这些子系统可能会决定返回警告/错误，停止工作或引发恐慌。
请参阅第3节以了解实现此回调的驱动程序示例，或参阅第2.4节以获取有关此API的更多文档。

使用DT注册EM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

EM也可以通过OPP框架和DT中的“operating-points-v2”信息进行注册。DT中的每个OPP条目都可以扩展一个包含微瓦特功耗值的属性“opp-microwatt”。此OPP DT属性允许平台注册反映总功耗（静态+动态）的EM功耗值。这些功耗值可能直接来自实验和测量。
“人工”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

有一个选项可供缺少关于每个性能状态下详细功耗知识的驱动程序提供自定义回调。回调.get_cost()是可选的，并提供EAS使用的“成本”值。
这对于仅提供不同类型CPU之间相对效率信息的平台非常有用，可以利用这些信息来创建一个抽象的功耗模型。但即便是一个抽象的功耗模型，在考虑到输入功率值大小限制的情况下，有时也难以实现。`.get_cost()`允许提供反映CPU效率的“成本”值。这将使提供的EAS（Energy Aware Scheduling）信息与EM（Energy Model）内部公式计算出的“成本”值之间的关系有所不同。为了在这样的平台上注册EM，驱动程序必须将`microwatts`标志设置为0，并提供`.get_power()`回调和`.get_cost()`回调。EM框架将在注册过程中正确处理此类平台。对于此类平台，会设置一个标志`EM_PERF_DOMAIN_ARTIFICIAL`。其他使用EM的框架需要特别注意并正确测试和处理这个标志。

“简单”EM的注册
~~~~~~~~~~~~~~~~~~~~~~~~~~~

“简单”EM使用框架辅助函数`cpufreq_register_em_with_opp()`进行注册。它实现了紧贴数学公式的功耗模型：
\[ \text{Power} = C \times V^2 \times f \]

通过这种方法注册的EM可能无法准确反映实际设备的物理特性，例如当静态功耗（泄漏）非常重要时。

2.3 访问性能域
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

有两个API函数提供了访问能效模型的方法：`em_cpu_get()`接受CPU ID作为参数，`em_pd_get()`接受设备指针作为参数。具体使用哪个接口取决于子系统的需求，但在CPU设备情况下，这两个函数返回相同的性能域。
对CPU能效模型感兴趣的子系统可以使用`em_cpu_get()` API获取相关信息。能效模型表在性能域创建时一次性分配，并且在内存中保持不变。
可以通过`em_cpu_energy()` API估计性能域消耗的能量。该估计假设在CPU设备上使用了schedutil CPUfreq管理器。目前，此计算不适用于其他类型的设备。
关于上述API的更多详细信息可以在`<linux/energy_model.h>`或第2.5节中找到。

2.4 运行时修改
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

希望在运行时更新EM的驱动程序应使用以下专用函数来分配新的修改后的EM实例。API如下所示：
```c
struct em_perf_table __rcu *em_table_alloc(struct em_perf_domain *pd);
```

这允许分配一个包含新EM表的结构，并且还包括EM框架所需的RCU和kref。`struct em_perf_table` 包含一个数组 `struct em_perf_state state[]`，其中按升序排列了一系列性能状态。该列表必须由希望更新EM的设备驱动程序填充。`struct em_perf_state`的内容也必须由驱动程序填充。
这是用于通过RCU指针交换来更新EM的API：
```c
int em_dev_update_perf_domain(struct device *dev, struct em_perf_table __rcu *new_table);
```

驱动程序必须提供一个已分配并初始化的新EM `struct em_perf_table` 指针。该新EM将在EM框架内安全地使用，并对内核中的其他子系统（如热管理和电源限制）可见。
此API的主要设计目标是快速执行并避免在运行时进行额外的计算或内存分配。如果设备驱动程序中已有预计算的EM，则应该能够以较低的性能开销重用它们。
为了释放由驱动程序（例如在模块卸载时）提供的EM，需要调用以下API：
```c
void em_table_free(struct em_perf_table __rcu *table);
```

这将允许EM框架在没有其他子系统使用它时安全地移除内存，例如EAS（Energy Aware Scheduling）。
为了在其他子系统（如热管理、功耗限制）中使用功率值，需要调用一个API来保护读取者并提供EM表数据的一致性：

```c
struct em_perf_state *em_perf_state_from_pd(struct em_perf_domain *pd);
```

此函数返回一个指向`struct em_perf_state`的指针，该结构是一个按升序排列的性能状态数组。必须在RCU读锁部分（在rcu_read_lock()之后）调用此函数。当不再需要EM表时，需要调用rcu_read_unlock()。这样，EM安全地使用了RCU读区段，并保护了用户。它还允许EM框架管理内存并释放它。更多关于如何使用它的细节可以在示例驱动程序的第3.2节中找到。

设备驱动程序有一个专门的API用于计算`em_perf_state::cost`值：

```c
int em_dev_compute_costs(struct device *dev, struct em_perf_state *table, int nr_states);
```

这些来自EM的成本值被EAS使用。新的EM表应与条目数量和设备指针一起传递。如果成本值计算正确，函数的返回值为0。该函数还会确保每个性能状态的低效值设置正确，并相应更新`em_perf_state::flags`。

然后，准备好的新EM可以传递给`em_dev_update_perf_domain()`函数以供使用。更多关于上述API的详细信息可以在`<linux/energy_model.h>`或第3.2节中找到，其中包含示例代码展示设备驱动程序中的简单更新机制实现。

### 2.5 API描述详情
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. kernel-doc:: include/linux/energy_model.h
   :internal:

.. kernel-doc:: kernel/power/energy_model.c
   :export:

### 3. 示例
------------

#### 3.1 注册EM的CPUFreq驱动示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CPUFreq框架支持一个专用回调来注册给定CPU(s)“策略”对象的EM：`cpufreq_driver::register_em()`。必须为给定的驱动程序正确实现该回调，因为框架会在设置期间适当时候调用它。

本节提供了一个使用（假）'foo'协议在Energy Model框架中注册性能域的简单CPUFreq驱动示例。该驱动实现了一个`est_power()`函数，用于提供给EM框架：

```c
-> drivers/cpufreq/foo_cpufreq.c

  01  static int est_power(struct device *dev, unsigned long *mW,
  02                       unsigned long *KHz)
  03  {
  04      long freq, power;
  05
  06      /* 使用'foo'协议获取频率上限 */
  07      freq = foo_get_freq_ceil(dev, *KHz);
  08      if (freq < 0)
  09          return freq;
  10
  11      /* 估计设备在相关频率下的功率成本 */
  12      power = foo_estimate_power(dev, freq);
  13      if (power < 0)
  14          return power;
  15
  16      /* 将值返回给EM框架 */
  17      *mW = power;
  18      *KHz = freq;
  19
  20      return 0;
  21  }
  22
  23  static void foo_cpufreq_register_em(struct cpufreq_policy *policy)
  24  {
  25      struct em_data_callback em_cb = EM_DATA_CB(est_power);
  26      struct device *cpu_dev;
  27      int nr_opp;
  28
  29      cpu_dev = get_cpu_device(cpumask_first(policy->cpus));
  30
  31      /* 查找此策略的OPP数量 */
  32      nr_opp = foo_get_nr_opp(policy);
  33
  34      /* 并注册新的性能域 */
  35      em_dev_register_perf_domain(cpu_dev, nr_opp, &em_cb, policy->cpus,
  36                                  true);
  37  }
  38
  39  static struct cpufreq_driver foo_cpufreq_driver = {
  40      .register_em = foo_cpufreq_register_em,
  41  };
```

#### 3.2 修改EM的示例驱动
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

本节提供了一个简单的热管理驱动修改EM的示例。该驱动实现了一个`foo_thermal_em_update()`函数。驱动定期被唤醒以检查温度并修改EM数据：

```c
-> drivers/soc/example/example_em_mod.c

  01  static void foo_get_new_em(struct foo_context *ctx)
  02  {
  03      struct em_perf_table __rcu *em_table;
  04      struct em_perf_state *table, *new_table;
  05      struct device *dev = ctx->dev;
  06      struct em_perf_domain *pd;
  07      unsigned long freq;
  08      int i, ret;
  09
  10      pd = em_pd_get(dev);
  11      if (!pd)
  12          return;
  13
  14      em_table = em_table_alloc(pd);
  15      if (!em_table)
  16          return;
  17
  18      new_table = em_table->state;
  19
  20      rcu_read_lock();
  21      table = em_perf_state_from_pd(pd);
  22      for (i = 0; i < pd->nr_perf_states; i++) {
  23          freq = table[i].frequency;
  24          foo_get_power_perf_values(dev, freq, &new_table[i]);
  25      }
  26      rcu_read_unlock();
  27
  28      /* 计算EAS的'cost'值 */
  29      ret = em_dev_compute_costs(dev, table, pd->nr_perf_states);
  30      if (ret) {
  31          dev_warn(dev, "EM: compute costs failed %d\n", ret);
  32          em_free_table(em_table);
  33          return;
  34      }
  35
  36      ret = em_dev_update_perf_domain(dev, em_table);
  37      if (ret) {
  38          dev_warn(dev, "EM: update failed %d\n", ret);
  39          em_free_table(em_table);
  40          return;
  41      }
  42
  43      /*
  44       * 由于是一次性更新，减少使用计数
  45       */
  46  }
```
```c
45		 * EM框架将在需要时释放表格
46		 */
47		em_table_free(em_table);
48	}
49
50	/*
51	 * 周期性调用的函数，用于检查温度并在必要时更新EM
52	 */
53	*/
54	static void foo_thermal_em_update(struct foo_context *ctx)
55	{
56		struct device *dev = ctx->dev;
57		int cpu;

58
59		ctx->temperature = foo_get_temp(dev, ctx);
60		if (ctx->temperature < FOO_EM_UPDATE_TEMP_THRESHOLD)
61			return;

62		foo_get_new_em(ctx);
63	}
```
