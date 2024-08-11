### 本地原子操作的语义和行为

==================================

**作者：** Mathieu Desnoyers

本文档解释了本地原子操作的目的、如何为特定架构实现它们以及如何正确使用它们。同时，它还强调了在内存写入顺序重要的情况下，跨CPU读取这些本地变量时必须采取的预防措施。
**注：**

请注意，基于`local_t`的操作不推荐用于通用内核。除非有特殊用途，请使用`this_cpu`操作。内核中大多数`local_t`的使用已经被`this_cpu`操作所取代。`this_cpu`操作将重定位与`local_t`类似的语义结合到一条指令中，生成更紧凑且执行更快的代码。

#### 本地原子操作的目的

本地原子操作旨在提供快速且高度可重入的每CPU计数器。通过移除通常用于跨CPU同步所需的LOCK前缀和内存屏障，它们最小化了标准原子操作的性能成本。

快速的每CPU原子计数器在很多情况下都很有用：它不需要禁用中断来保护中断处理程序，并允许在NMI处理器中使用一致的计数器。特别是对于跟踪目的和各种性能监控计数器来说尤其有用。

本地原子操作仅保证数据所有者CPU对变量修改的原子性。因此，必须确保只有一个CPU写入`local_t`数据。这可以通过使用每个CPU的数据并在抢占安全上下文中对其进行修改来完成。然而，允许从任何CPU读取`local_t`数据；此时，相对于其他内存写入，它看起来像是乱序写入。

#### 对于特定架构的实现

可以通过稍微修改标准原子操作来实现：只需保留它们的UP变体。通常意味着去除LOCK前缀（在i386和x86_64上）和任何SMP同步屏障。如果架构在SMP和UP之间没有不同的行为，则在架构的`local.h`中包含`asm-generic/local.h`就足够了。

`local_t`类型被定义为一个不透明的`signed long`类型，通过在结构内部嵌入一个`atomic_long_t`来实现。这样做的目的是使得从该类型到`long`的转换失败。定义如下：

```c
typedef struct { atomic_long_t a; } local_t;
```

#### 使用本地原子操作时应遵循的规则

* 由本地操作触碰的变量必须是每个CPU的变量。
* **只有**这些变量的所有者CPU才能写入它们。
* 该CPU可以从任何上下文（进程、中断、软中断、NMI等）使用本地操作来更新其`local_t`变量。
* 在进程上下文中使用本地操作时，必须禁用抢占（或中断），以确保进程不会在获取每个CPU变量和实际执行本地操作之间迁移到不同的CPU。
使用局部操作
==============

当在中断上下文中使用局部操作时，在主线内核中无需特别注意，因为它们将在本地CPU上运行，并且抢占已经禁用。然而，我建议仍然明确禁用抢占，以确保其在-rt内核上仍能正确工作。

读取局部CPU变量将提供该变量的当前副本。

由于对 `"long"` 对齐变量的更新总是原子性的，这些变量可以从任何CPU读取。由于写入CPU没有执行内存同步，因此在读取某些其他CPU的变量时可能会读取到过期的变量副本。

如何使用局部原子操作
======================

```
#include <linux/percpu.h>
#include <asm/local.h>

static DEFINE_PER_CPU(local_t, counters) = LOCAL_INIT(0);
```

计数
=====

在可抢占上下文中，使用 `get_cpu_var()` 和 `put_cpu_var()` 包围局部原子操作：这可以确保在访问每个CPU变量时禁用了抢占。例如：

```c
local_inc(&get_cpu_var(counters));
put_cpu_var(counters);
```

如果你已经在安全的抢占上下文中，你可以使用 `this_cpu_ptr()` 替代：

```c
local_inc(this_cpu_ptr(&counters));
```

读取计数器
===========

这些局部计数器可以从其他CPU读取来汇总计数。请注意，通过 local_read 跨CPU看到的数据相对于拥有数据的CPU上的其他内存写入来说必须被视为无序的：

```c
long sum = 0;
for_each_online_cpu(cpu)
        sum += local_read(&per_cpu(counters, cpu));
```

如果你想使用远程 local_read 来在CPU之间同步对资源的访问，则必须在写入CPU和读取CPU上分别显式使用 `smp_wmb()` 和 `smp_rmb()` 内存屏障。例如，如果你使用 `local_t` 变量作为缓冲区中已写入字节数的计数器，则缓冲区写入与计数器递增之间应有一个 `smp_wmb()`，同样计数器读取与缓冲区读取之间也应有一个 `smp_rmb()`。

下面是一个使用 `local.h` 实现基本每CPU计数器的示例模块：

```c
/* test-local.c
 *
 * 示例模块用于演示 local.h 的使用
*/

#include <asm/local.h>
#include <linux/module.h>
#include <linux/timer.h>

static DEFINE_PER_CPU(local_t, counters) = LOCAL_INIT(0);

static struct timer_list test_timer;

/* 在每个CPU上调用的IPI（中断处理程序）*/
static void test_each(void *info)
{
        /* 从非可抢占上下文递增计数器 */
        printk("在 cpu %d 上递增\n", smp_processor_id());
        local_inc(this_cpu_ptr(&counters));

        /* 这是如果在可抢占上下文中递增变量的样子（它禁用了抢占）:
         *
         * local_inc(&get_cpu_var(counters));
         * put_cpu_var(counters);
         */
}

static void do_test_timer(unsigned long data)
{
        int cpu;

        /* 递增计数器 */
        on_each_cpu(test_each, NULL, 1);
        /* 读取所有计数器 */
        printk("从 CPU %d 读取计数器\n", smp_processor_id());
        for_each_online_cpu(cpu) {
                printk("读取: CPU %d, 计数值 %ld\n", cpu,
                       local_read(&per_cpu(counters, cpu)));
        }
        mod_timer(&test_timer, jiffies + 1000);
}

static int __init test_init(void)
{
        /* 初始化将递增计数器的定时器 */
        timer_setup(&test_timer, do_test_timer, 0);
        mod_timer(&test_timer, jiffies + 1);

        return 0;
}

static void __exit test_exit(void)
{
        timer_shutdown_sync(&test_timer);
}

module_init(test_init);
module_exit(test_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Mathieu Desnoyers");
MODULE_DESCRIPTION("Local Atomic Operations");
```
