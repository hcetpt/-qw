运行时验证
====================

运行时验证（RV）是一种轻量级（但严谨的）方法，它通过一种更实用的方法来补充经典的详尽验证技术（例如*模型检测*和*定理证明*），适用于复杂系统。
与依赖系统的精细模型（例如，在指令级别重新实现）不同，RV通过分析系统实际执行的轨迹，并将其与系统行为的形式规范进行比较。
主要优势在于，RV可以在不需重新用建模语言实现整个系统的情况下提供精确的运行时行为信息。
此外，如果有一个高效的监控方法，则可以对系统执行*在线*验证，使系统能够对意外事件作出*反应*，从而避免例如在安全关键系统中的故障传播。

运行时监控器与反应器
=============================

监控器是系统运行时验证的核心部分。监控器位于所需或不希望的行为形式规范与系统实际轨迹之间。
在Linux术语中，运行时验证监控器被封装在*RV监控器*抽象中。一个*RV监控器*包括系统参考模型、一组监控实例（如每CPU监控、每任务监控等），以及将监控器通过跟踪连接到系统的辅助函数，如下图所示：

```
Linux   +---- RV Monitor ----------------------------------+ Formal
  Realm  |                                                  |  Realm
  +-------------------+     +----------------+     +-----------------+
  |   Linux kernel    |     |     Monitor    |     |     Reference   |
  |     Tracing       |  -> |   Instance(s)  | <-  |       Model     |
  | (instrumentation) |     | (verification) |     | (specification) |
  +-------------------+     +----------------+     +-----------------+
         |                          |                       |
         |                          V                       |
         |                     +----------+                 |
         |                     | Reaction |                 |
         |                     +--+--+--+-+                 |
         |                        |  |  |                   |
         |                        |  |  +-> trace output ?  |
         +------------------------|--|----------------------+
                                  |  +----> panic ?
                                  +-------> <user-specified>
```

除了系统验证和监控外，监控器还可以对意外事件作出反应。反应的形式可以从记录事件的发生到强制正确行为，甚至采取极端措施使系统停止以防止故障传播。
在Linux术语中，*反应器*是一种为*RV监控器*提供的反应方法。默认情况下，所有监控器都应该提供其操作的跟踪输出，这本身就是一种反应。此外，其他反应机制可供用户根据需要启用。
有关运行时验证原理及RV应用于Linux的更多信息：

  - Bartocci, Ezio, et al. "Introduction to runtime verification." In: Lectures on Runtime Verification. Springer, Cham, 2018. p. 1-33.
  - Falcone, Ylies, et al. "A taxonomy for classifying runtime verification tools." In: International Conference on Runtime Verification. Springer, Cham, 2018. p. 
```
241-262
德·奥利维拉, 丹尼尔·布里斯托特. *基于自动机的形式分析与实时Linux内核的验证.* 博士论文, 2020年

在线RV监视器
==============

监视器可以分为*离线*和*在线*监视器。*离线*监视器在事件发生后处理系统生成的跟踪记录，通常通过从永久存储系统中读取执行跟踪来完成。*在线*监视器在系统执行期间处理跟踪记录。如果事件处理与系统执行绑定，并且在事件监控过程中阻塞系统，则称其为*同步*监视器。另一方面，*异步*监视器的执行与系统分离。每种类型的监视器都有各自的优势。例如，*离线*监视器可以在不同的机器上执行，但需要将日志保存到文件中的操作。相比之下，*同步在线*方法可以在违规发生的那一刻作出反应。

关于监视器的另一个重要方面是与事件分析相关的开销。如果系统生成事件的频率高于在同一系统中处理这些事件的能力，则只有*离线*方法是可行的。另一方面，如果事件的追踪会导致比简单地由监视器处理事件更高的开销，则*同步在线*监视器会带来更低的开销。

事实上，以下研究显示：

  德·奥利维拉, 丹尼尔·布里斯托特；库奇诺塔, 托马索；德·奥利维拉, 罗穆洛·席尔瓦. *Linux内核的高效形式验证.* 在：软件工程与形式方法国际会议. 斯普林格出版社, 2019年, 第315-332页
表明对于确定性自动机模型，在内核中同步处理事件造成的开销低于将相同事件保存到跟踪缓冲区的开销，甚至不考虑收集用户空间分析所需的跟踪记录。

这促使开发了一个用于在线监视器的内核接口。

有关使用自动机建模Linux内核行为的更多信息，请参见：

  德·奥利维拉, 丹尼尔；德·奥利维拉, 罗穆洛·席尔瓦；库奇诺塔, 托马索. *适用于PREEMPT_RT Linux内核的线程同步模型.* 《系统架构杂志》, 2020年, 第107卷: 101729
用户界面
==========

用户界面类似于追踪界面（有意为之）。当前位于 "/sys/kernel/tracing/rv/"
以下文件/目录目前可用：

**available_monitors**

- 读取列表显示所有可用的监视器，每行一个

例如::

   # cat available_monitors
   wip
   wwnr

**available_reactors**

- 读取显示所有可用的反应器，每行一个
例如::

   # cat available_reactors
   nop
   panic
   printk

**enabled_monitors**：

- 读取列出已启用的监视器，每行一个
- 写入以启用指定的监视器
- 写入带有 '!' 前缀的监视器名称来禁用它
- 截断文件会禁用所有已启用的监视器

例如::

   # cat enabled_monitors
   # echo wip > enabled_monitors
   # echo wwnr >> enabled_monitors
   # cat enabled_monitors
   wip
   wwnr
   # echo '!wip' >> enabled_monitors
   # cat enabled_monitors
   wwnr
   # echo > enabled_monitors
   # cat enabled_monitors
   #

注意可以同时启用多个监视器
**monitoring_on**

这是一个用于监控的开关。类似于追踪接口中的 "tracing_on" 开关。
- 写入 "0" 停止监控
- 写入 "1" 继续监控
- 读取返回当前监控状态

注意这不会禁用已启用的监视器，而是停止每个实体的监视器对系统接收到事件的监控
**reacting_on**

- 写入 "0" 阻止反应发生
- 写入 "1" 启用反应
- 读取返回当前反应状态

**monitors/**

每个监视器在其内部都有自己的目录 "monitors/"。在那里将呈现特定于监视器的文件。“monitors/” 目录类似于 tracefs 中的 “events” 目录
例如::

   # cd monitors/wip/
   # ls
   desc  enable
   # cat desc
   在抢占式每 CPU 测试中唤醒监视器
   # cat enable
   0

**monitors/MONITOR/desc**

- 读取显示监视器 *MONITOR* 的描述

**monitors/MONITOR/enable**

- 写入 "0" 禁用 *MONITOR*
- 写入 "1" 启用 *MONITOR*
- 读取返回 *MONITOR* 的当前状态

**monitors/MONITOR/reactors**

- 列出可用的反应器，并在 "[]" 中显示给定 *MONITOR* 选择的反应器，默认为 nop（无操作）反应器
- 写入反应器名称以将其启用到给定的 MONITOR
例如::

   # cat monitors/wip/reactors
   [nop]
   panic
   printk
   # echo panic > monitors/wip/reactors
   # cat monitors/wip/reactors
   nop
   [panic]
   printk
