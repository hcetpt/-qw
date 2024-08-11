=========================
内核中的CPU热插拔
=========================

:日期: 2021年9月
:作者: Sebastian Andrzej Siewior <bigeasy@linutronix.de>,
         Rusty Russell <rusty@rustcorp.com.au>,
         Srivatsa Vaddagiri <vatsa@in.ibm.com>,
         Ashok Raj <ashok.raj@intel.com>,
         Joel Schopp <jschopp@austin.ibm.com>,
	 Thomas Gleixner <tglx@linutronix.de>

简介
============

现代系统架构的进步已经引入了处理器中先进的错误报告和校正能力。有一些OEM支持NUMA硬件，这些硬件也支持热插拔，其中物理节点的插入和移除需要CPU热插拔的支持。这些进步要求内核可利用的CPU可以在配置原因或RAS目的下被移除，以使有问题的CPU脱离系统的执行路径。因此，在Linux内核中需要CPU热插拔的支持。
CPU热插拔支持的一个更为新颖的应用是在SMP的挂起恢复支持中的使用。双核心和HT技术使得即使是笔记本电脑也能运行SMP内核，而这些内核以前并不支持这些方法。
命令行开关
=====================
``maxcpus=n``
  将启动时的CPU数量限制为*n*。例如，如果你有四个CPU，并使用`maxcpus=2`，那么只会启动两个。你可以选择在稍后将其他CPU上线。
``nr_cpus=n``
  限制内核支持的CPU总数。如果这里提供的数字低于物理可用的CPU数量，则那些CPU以后不能被上线。
``possible_cpus=n``
  此选项设置`cpu_possible_mask`中的`possible_cpus`位数
此选项仅限于X86和S390架构。
``cpu0_hotplug``
  允许关闭CPU0
此选项仅限于X86架构。
CPU映射
========

``cpu_possible_mask``
  可能出现的所有CPU的位图。这用于为那些不打算随着CPU的增加或移除而增长或缩小的每CPU变量分配启动时间内存。
一旦在启动时的发现阶段设置后，该映射是静态的，即任何时候都不会添加或移除位。提前准确地根据您的系统需求对其进行修剪可以节省一些启动时间内存。

`cpu_online_mask`
在线CPU的位图。它在`__cpu_up()`中设置，在一个CPU可供内核调度使用并准备好接收来自设备的中断之后。当一个CPU使用`__cpu_disable()`关闭时，该位图会被清除，在此之前所有操作系统服务（包括中断）都会迁移到另一个目标CPU上。

`cpu_present_mask`
当前系统中存在的CPU的位图。它们并非全部都在线。当物理热插拔由相关子系统（如ACPI）处理时，该映射可能会发生变化，新的位将根据事件是热添加还是热移除而被添加或移除。目前尚无锁定规则。典型用法是在启动时初始化拓扑结构，此时热插拔处于禁用状态。

实际上您不需要操纵任何系统CPU映射。对于大多数用途来说，它们应该是只读的。在设置每个CPU资源时，几乎总是使用`cpu_possible_mask`或者`for_each_possible_cpu()`进行迭代。要迭代自定义CPU映射，可以使用宏`for_each_cpu()`。
永远不要使用除了`cpumask_t`之外的其他类型来表示CPU的位图。

使用CPU热插拔
==============

需要启用内核选项`CONFIG_HOTPLUG_CPU`。目前它在多种架构上可用，包括ARM、MIPS、PowerPC和X86。配置通过sysfs接口完成：

```
$ ls -lh /sys/devices/system/cpu
total 0
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu0
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu1
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu2
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu3
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu4
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu5
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu6
drwxr-xr-x  9 root root    0 Dec 21 16:33 cpu7
drwxr-xr-x  2 root root    0 Dec 21 16:33 hotplug
-r--r--r--  1 root root 4.0K Dec 21 16:33 offline
-r--r--r--  1 root root 4.0K Dec 21 16:33 online
-r--r--r--  1 root root 4.0K Dec 21 16:33 possible
-r--r--r--  1 root root 4.0K Dec 21 16:33 present
```

文件`offline`、`online`、`possible`、`present`分别代表CPU映射
每个CPU文件夹包含一个`online`文件，用于控制逻辑上的开启（1）和关闭（0）状态。要逻辑关闭CPU4：

```
$ echo 0 > /sys/devices/system/cpu/cpu4/online
  smpboot: CPU 4 is now offline
```

一旦CPU被关闭，它就会从`/proc/interrupts`、`/proc/cpuinfo`中移除，并且也不应该在`top`命令中显示可见。要使CPU4重新上线：

```
$ echo 1 > /sys/devices/system/cpu/cpu4/online
smpboot: Booting Node 0 Processor 4 APIC 0x1
```

CPU再次变得可用。这应该适用于所有CPU，但通常CPU0是特殊的，不包含在CPU热插拔中。

CPU热插拔协调
===============

离线情况
---------

一旦CPU被逻辑关闭，已注册的热插拔状态的拆卸回调将被调用，从`CPUHP_ONLINE`开始，终止于状态`CPUHP_OFFLINE`。这包括：

* 如果任务因挂起操作而冻结，则`cpuhp_tasks_frozen`将被设置为真
* 所有进程会从这个即将离线的CPU迁移到新CPU上
新CPU是从每个进程当前的cpuset中选择的，这可能是所有在线CPU的一个子集。
* 所有针对该CPU的中断都会迁移到一个新的CPU上
* 定时器也会迁移到一个新的CPU上
* 当所有服务迁移完成后，内核会调用架构特定的例程 `__cpu_disable()` 来执行架构特定的清理工作

### CPU 热插拔API

#### CPU热插拔状态机

CPU热插拔使用了一个简单的状态机，其状态空间从CPUHP_OFFLINE到CPUHP_ONLINE是线性的。每个状态都有启动和关闭回调。
- 当一个CPU上线时，启动回调按顺序依次被调用，直到达到CPUHP_ONLINE状态。这些回调也可以在设置状态的回调或向多实例状态添加一个实例时被调用。
- 当一个CPU下线时，关闭回调按相反的顺序依次被调用，直到达到CPUHP_OFFLINE状态。这些回调也可以在移除状态的回调或从多实例状态中移除一个实例时被调用。
- 如果使用场景只需要热插拔操作的一个方向（CPU上线或CPU下线）的回调，则在设置状态时可以将不需要的另一个回调设为NULL。

状态空间分为三个部分：

* **准备阶段**

  准备阶段覆盖的状态空间是从CPUHP_OFFLINE到CPUHP_BRINGUP_CPU。
  - 在CPU上线操作中，准备阶段中的启动回调会在CPU启动前被调用。而在CPU下线操作中，关闭回调会在CPU变得无法正常运行后被调用。
  - 这些回调是在控制CPU上被调用的，因为它们显然不能在热插拔的CPU上运行——该CPU要么尚未启动，要么已经变得无法正常运行。
  - 启动回调用于设置使CPU成功上线所需的资源。而关闭回调则用于释放资源或将待处理的工作迁移到在线CPU上，在热插拔的CPU变得无法正常运行之后。
  - 允许启动回调失败。如果一个回调失败，CPU上线操作会被中止，并且CPU会被还原到之前的状态（通常是CPUHP_OFFLINE）。
本节中的关闭回调不允许失败。

* 启动阶段 (STARTING)

  启动阶段涵盖了从 CPUHP_BRINGUP_CPU + 1 到 CPUHP_AP_ONLINE 的状态空间。
  在早期的 CPU 设置代码中，当执行 CPU 上线操作时，会在这个热插拔的 CPU 上、在中断被禁用的情况下调用此阶段的启动回调。
  在 CPU 下线操作即将完全关闭 CPU 前，也会在中断被禁用的情况下调用此阶段的关闭回调。
  此阶段中的回调不允许失败。
  这些回调用于低级硬件初始化/关闭以及核心子系统的操作。

* 在线阶段 (ONLINE)

  在线阶段涵盖了从 CPUHP_AP_ONLINE + 1 到 CPUHP_ONLINE 的状态空间。
  在 CPU 上线操作期间会调用此阶段热插拔 CPU 上的启动回调。同样地，在 CPU 下线操作期间也会调用相应的关闭回调。
  这些回调是在每个 CPU 热插拔线程的上下文中调用的，该线程绑定于热插拔的 CPU 上，并且在中断和抢占都启用的情况下进行调用。
  这些回调允许失败。如果某个回调失败，则热插拔操作会被中止，并将 CPU 回退到先前的状态。

CPU 上线/下线操作
--------------------

一次成功的上线操作如下所示：

  [CPUHP_OFFLINE]
  [CPUHP_OFFLINE + 1]->启动()         -> 成功
  [CPUHP_OFFLINE + 2]->启动()         -> 成功
  [CPUHP_OFFLINE + 3]                  -> 跳过，因为启动函数为 NULL
  ..
一次成功的上线操作如下所示：

  [CPUHP_BRINGUP_CPU]->startup()       -> 成功
  === PREPARE 阶段结束
  [CPUHP_BRINGUP_CPU + 1]->startup()   -> 成功
  ..
[CPUHP_AP_ONLINE]->startup()         -> 成功
  === STARTUP 阶段结束
  [CPUHP_AP_ONLINE + 1]->startup()     -> 成功
  ..
[CPUHP_ONLINE - 1]->startup()        -> 成功
  [CPUHP_ONLINE]

一次成功的下线操作如下所示：

  [CPUHP_ONLINE]
  [CPUHP_ONLINE - 1]->teardown()       -> 成功
  ..
[CPUHP_AP_ONLINE + 1]->teardown()    -> 成功
  === STARTUP 阶段开始
  [CPUHP_AP_ONLINE]->teardown()        -> 成功
  ..
[CPUHP_BRINGUP_ONLINE - 1]->teardown()
  ..
=== PREPARE 阶段开始
  [CPUHP_BRINGUP_CPU]->teardown()
  [CPUHP_OFFLINE + 3]->teardown()
  [CPUHP_OFFLINE + 2]                  -> 跳过，因为teardown为NULL
  [CPUHP_OFFLINE + 1]->teardown()
  [CPUHP_OFFLINE]

一次失败的上线操作如下所示：

  [CPUHP_OFFLINE]
  [CPUHP_OFFLINE + 1]->startup()       -> 成功
  [CPUHP_OFFLINE + 2]->startup()       -> 成功
  [CPUHP_OFFLINE + 3]                  -> 跳过，因为startup为NULL
  ..
[CPUHP_BRINGUP_CPU]->startup()       -> 成功
  === PREPARE 阶段结束
  [CPUHP_BRINGUP_CPU + 1]->startup()   -> 成功
  ..
[CPUHP_AP_ONLINE]->startup()         -> 成功
  === STARTUP 阶段结束
  [CPUHP_AP_ONLINE + 1]->startup()     -> 成功
  ---
  [CPUHP_AP_ONLINE + N]->startup()     -> 失败
  [CPUHP_AP_ONLINE + (N - 1)]->teardown()
  ..
[CPUHP_AP_ONLINE + 1]->teardown()
  === STARTUP 阶段开始
  [CPUHP_AP_ONLINE]->teardown()
  ..
[CPUHP_BRINGUP_ONLINE - 1]->teardown()
  ..
### 准备阶段开始

  * [CPUHP_BRINGUP_CPU]->teardown()
  * [CPUHP_OFFLINE + 3]->teardown()
  * [CPUHP_OFFLINE + 2]                  -> 跳过，因为teardown为NULL
  * [CPUHP_OFFLINE + 1]->teardown()
  * [CPUHP_OFFLINE]

失败的下线操作看起来是这样的：

  * [CPUHP_ONLINE]
  * [CPUHP_ONLINE - 1]->teardown()       -> 成功
  * ...
  * [CPUHP_ONLINE - N]->teardown()       -> 失败
  * [CPUHP_ONLINE - (N - 1)]->startup()
  * ...
  * [CPUHP_ONLINE - 1]->startup()
  * [CPUHP_ONLINE]

递归失败无法合理处理。请看以下由于失败的下线操作导致的递归失败的例子：

  * [CPUHP_ONLINE]
  * [CPUHP_ONLINE - 1]->teardown()       -> 成功
  * ...
  * [CPUHP_ONLINE - N]->teardown()       -> 失败
  * [CPUHP_ONLINE - (N - 1)]->startup()  -> 成功
  * [CPUHP_ONLINE - (N - 2)]->startup()  -> 失败

CPU热插拔状态机在这里停止，并不再尝试回退，因为这可能会导致无限循环：

  * [CPUHP_ONLINE - (N - 1)]->teardown() -> 成功
  * [CPUHP_ONLINE - N]->teardown()       -> 失败
  * [CPUHP_ONLINE - (N - 1)]->startup()  -> 成功
  * [CPUHP_ONLINE - (N - 2)]->startup()  -> 失败
  * [CPUHP_ONLINE - (N - 1)]->teardown() -> 成功
  * [CPUHP_ONLINE - N]->teardown()       -> 失败

重复以上过程。在这种情况下，CPU留在了以下状态：

  * [CPUHP_ONLINE - (N - 1)]

这样至少可以让系统继续前进，并给用户提供调试甚至解决问题的机会。

### 状态分配

有两种方法来分配CPU热插拔状态：

* **静态分配**

  当子系统或驱动程序有与其他CPU热插拔状态的顺序要求时，必须使用静态分配。例如，在CPU上线操作中，PERF核心启动回调必须在PERF驱动程序启动回调之前调用。而在CPU下线操作中，驱动程序teardown回调必须在核心teardown回调之前调用。这些静态分配的状态在`cpuhp_state`枚举中由常量描述，可以在`include/linux/cpuhotplug.h`找到。
在适当的位置将状态插入到枚举中以满足顺序要求。状态常量必须用于设置和移除状态。
如果状态回调不是在运行时设置的，而是作为`kernel/cpu.c`中的CPU热插拔状态数组初始化器的一部分，则也要求使用静态分配。
* **动态分配**

  如果状态回调没有顺序要求，则推荐使用动态分配。状态号由设置函数分配，并在成功时返回给调用者。
只有`PREPARE`和`ONLINE`部分提供动态分配范围。`STARTING`部分不提供动态分配范围，因为该部分中的大多数回调有明确的顺序要求。

### 设置CPU热插拔状态

核心代码提供了以下函数来设置一个状态：

* `cpuhp_setup_state(state, name, startup, teardown)`
* `cpuhp_setup_state_nocalls(state, name, startup, teardown)`
* `cpuhp_setup_state_cpuslocked(state, name, startup, teardown)`
* `cpuhp_setup_state_nocalls_cpuslocked(state, name, startup, teardown)`

对于驱动程序或子系统有多个实例且需要对每个实例调用相同的CPU热插拔状态回调的情况，CPU热插拔核心提供了多实例支持。与驱动程序特定的实例列表相比，其优点在于实例相关的函数完全针对CPU热插拔操作进行了序列化，并在添加和移除时自动调用状态回调。为了设置此类多实例状态，可使用以下函数：

* `cpuhp_setup_state_multi(state, name, startup, teardown)`

`@state`参数要么是静态分配的状态，要么是动态分配状态的常量——`CPUHP_BP_PREPARE_DYN`、`CPUHP_AP_ONLINE_DYN`——这取决于希望分配动态状态的状态部分（`PREPARE`、`ONLINE`）。
`@name` 参数用于 sysfs 输出和仪器监控。命名规则为 "子系统:模式" 或 "子系统/驱动:模式"，例如 "perf:mode" 或 "perf/x86:mode"。常用的模式名称如下：

======== =======================================================
prepare  适用于 PREPARE 部分中的状态

dead     适用于 PREPARE 部分中不提供启动回调的状态

starting 适用于 STARTING 部分中的状态

dying    适用于 STARTING 部分中不提供启动回调的状态

online   适用于 ONLINE 部分中的状态

offline  适用于 ONLINE 部分中不提供启动回调的状态
======== =======================================================

由于 `@name` 参数仅用于 sysfs 和仪器监控，因此如果其他模式描述符能更好地描述状态的性质，则也可以使用这些描述符。
`@name` 参数的例子有："perf/online"、"perf/x86:prepare"、"RCU/tree:dying"、"sched/waitempty"。

`@startup` 参数是一个指向在 CPU 上线操作期间应调用的回调函数的指针。如果使用位置不需要启动回调，则将指针设置为 NULL。
`@teardown` 参数是一个指向在 CPU 下线操作期间应调用的回调函数的指针。如果使用位置不需要下线回调，则将指针设置为 NULL。
这些函数在处理已安装的回调的方式上有所不同：

  * `cpuhp_setup_state_nocalls()`、`cpuhp_setup_state_nocalls_cpuslocked()` 和 `cpuhp_setup_state_multi()` 仅安装回调函数。

  * `cpuhp_setup_state()` 和 `cpuhp_setup_state_cpuslocked()` 安装回调函数，并针对当前具有比新安装状态高的状态的所有在线 CPU 调用 `@startup` 回调（如果不为空）。根据状态部分的不同，回调函数将在当前 CPU（PREPARE 部分）或每个在线 CPU 的上下文中由 CPU 热插拔线程调用（ONLINE 部分）
如果 CPU N 的回调失败，则会调用 CPU 0 到 N-1 的 `teardown` 回调以回滚操作。状态设置失败，不会安装状态回调，并且在动态分配的情况下，释放分配的状态。
状态设置和回调调用与 CPU 热插拔操作同步。如果设置函数必须从 CPU 热插拔读锁定区域调用，则需要使用 `_cpuslocked()` 变体。这些函数不能从 CPU 热插拔回调内部使用。
函数返回值：
  ======== ===================================================================
  0        静态分配的状态成功设置

  >0       动态分配的状态成功设置
返回的数字是分配的状态编号。如果稍后需要移除状态回调（例如模块移除），则调用者需要保存这个数字，并将其作为状态移除函数的 `@state` 参数使用。对于多实例状态，动态分配的状态编号也作为实例添加/移除操作的 `@state` 参数所需。
<0       操作失败
  ======== ===================================================================

移除 CPU 热插拔状态
--------------------

要移除之前设置的状态，提供了以下函数：

* `cpuhp_remove_state(state)`
* `cpuhp_remove_state_nocalls(state)`
* `cpuhp_remove_state_nocalls_cpuslocked(state)`
* `cpuhp_remove_multi_state(state)`

`@state` 参数要么是静态分配的状态，要么是由 `cpuhp_setup_state*()` 在动态范围内分配的状态编号。如果状态位于动态范围内，则状态编号会被释放并再次可供动态分配。
这些函数在处理已安装的回调的方式上有所不同：

  * `cpuhp_remove_state_nocalls()`、`cpuhp_remove_state_nocalls_cpuslocked()` 和 `cpuhp_remove_multi_state()` 仅移除回调函数。
* `cpuhp_remove_state()` 会移除回调，并对所有当前状态大于被移除状态的在线CPU调用清理回调（如果非NULL）。根据状态部分的不同，回调要么在当前CPU上被调用（PREPARE部分），要么在每个在线CPU的热插拔线程上下文中被调用（ONLINE部分）。
为了完成移除操作，清理回调不应该失败。
状态移除和回调调用是针对CPU热插拔操作进行序列化的。如果移除函数需要从CPU热插拔读锁定区域中调用，则应使用`_cpuslocked()`变体。这些函数不能在CPU热插拔回调内部使用。
如果要移除一个多实例状态，则调用者首先需要移除所有实例。
多实例状态实例管理
------------------------

一旦多实例状态设置好后，可以向该状态添加实例：

  * `cpuhp_state_add_instance(state, node)`
  * `cpuhp_state_add_instance_nocalls(state, node)`

参数`@state`要么是一个静态分配的状态，要么是由`cpuhp_setup_state_multi()`在动态范围内分配的状态编号。参数`@node`是指向嵌入在实例数据结构中的hlist_node的指针。此指针传递给多实例状态回调，并且可以通过回调使用`container_of()`来获取实例。
这些函数在处理安装的回调的方式上有所不同：

  * `cpuhp_state_add_instance_nocalls()`仅将实例添加到多实例状态的节点列表中
* `cpuhp_state_add_instance()`将实例添加并为所有当前状态大于`@state`的在线CPU调用与`@state`关联的启动回调（如果非NULL）。回调仅对要添加的实例进行调用。根据状态部分的不同，回调要么在当前CPU上被调用（PREPARE部分），要么在每个在线CPU的热插拔线程上下文中被调用（ONLINE部分）。
如果CPU N上的回调失败，则会调用CPU 0至N-1的清理回调以回滚操作，函数失败且实例不会被添加到多实例状态的节点列表中
要从状态的节点列表中移除一个实例，可以使用以下函数：

  * `cpuhp_state_remove_instance(state, node)`
  * `cpuhp_state_remove_instance_nocalls(state, node)`

参数与`cpuhp_state_add_instance*()`变体相同。
这些函数在处理已安装的回调方式上有所不同：

* `cpuhp_state_remove_instance_nocalls()` 仅从状态的节点列表中移除实例。
* `cpuhp_state_remove_instance()` 移除实例并调用与 `@state` 关联的拆解回调（如果非 `NULL`），针对所有当前状态大于 `@state` 的在线 CPU。回调仅对要移除的实例进行调用。根据状态部分的不同，回调要么在当前 CPU 上调用（对于 `PREPARE` 部分），要么在每个在线 CPU 的热插拔线程上下文中调用（对于 `ONLINE` 部分）。
为了完成移除操作，拆解回调不应失败。
节点列表的添加/移除操作和回调调用被序列化以防止 CPU 热插拔操作。这些函数不能在 CPU 热插拔回调或 CPU 热插拔读锁定区域内使用。

**示例**

--------

为在线和离线操作通知设置和清理静态分配的状态（位于 `STARTING` 部分）：

```c
int ret = cpuhp_setup_state(CPUHP_SUBSYS_STARTING, "subsys:starting", subsys_cpu_starting, subsys_cpu_dying);
if (ret < 0)
    return ret;
//...
cpuhp_remove_state(CPUHP_SUBSYS_STARTING);
```

为离线操作通知设置和清理动态分配的状态（位于 `ONLINE` 部分）：

```c
int state = cpuhp_setup_state(CPUHP_AP_ONLINE_DYN, "subsys:offline", NULL, subsys_cpu_offline);
if (state < 0)
    return state;
//...
cpuhp_remove_state(state);
```

为在线操作通知（不调用回调）设置和清理动态分配的状态（位于 `ONLINE` 部分）：

```c
int state = cpuhp_setup_state_nocalls(CPUHP_AP_ONLINE_DYN, "subsys:online", subsys_cpu_online, NULL);
if (state < 0)
    return state;
//...
cpuhp_remove_state_nocalls(state);
```

为在线和离线操作通知设置、使用和清理动态分配的多实例状态（位于 `ONLINE` 部分）：

```c
int state = cpuhp_setup_state_multi(CPUHP_AP_ONLINE_DYN, "subsys:online", subsys_cpu_online, subsys_cpu_offline);
if (state < 0)
    return state;
//...
int ret = cpuhp_state_add_instance(state, &inst1->node);
if (ret)
    return ret;
//...
ret = cpuhp_state_add_instance(state, &inst2->node);
if (ret)
    return ret;
//...
```
### 翻译成中文：

```plaintext
// 移除实例状态
cpuhp_remove_instance(state, &inst1->node);
...
cpuhp_remove_instance(state, &inst2->node);
...
remove_multi_state(state);

### 热插拔状态测试
========================

验证自定义状态是否按预期工作的一种方法是关闭一个CPU，然后再将其上线。也可以将CPU置于某个状态（例如 *CPUHP_AP_ONLINE*），然后返回到 *CPUHP_ONLINE*。这会模拟在 *CPUHP_AP_ONLINE* 后的一个状态出现的错误，从而回滚到在线状态。
所有注册的状态都在 `/sys/devices/system/cpu/hotplug/states` 中枚举，如下所示：

$ tail /sys/devices/system/cpu/hotplug/states
138: mm/vmscan:online
139: mm/vmstat:online
140: lib/percpu_cnt:online
141: acpi/cpu-drv:online
142: base/cacheinfo:online
143: virtio/net:online
144: x86/mce:online
145: printk:online
168: sched:active
169: online

要将CPU4回滚到 `lib/percpu_cnt:online` 状态，然后再回到在线状态，只需执行以下命令：

$ cat /sys/devices/system/cpu/cpu4/hotplug/state
169
$ echo 140 > /sys/devices/system/cpu/cpu4/hotplug/target
$ cat /sys/devices/system/cpu/cpu4/hotplug/state
140

需要注意的是，状态140的拆除回调已经被调用。现在让它重新上线：

$ echo 169 > /sys/devices/system/cpu/cpu4/hotplug/target
$ cat /sys/devices/system/cpu/cpu4/hotplug/state
169

如果启用了跟踪事件，可以看到各个步骤：

# TASK-PID   CPU#    TIMESTAMP  FUNCTION
#     | |       |        |         |
bash-394  [001]  22.976: cpuhp_enter: cpu: 0004 target: 140 step: 169 (cpuhp_kick_ap_work)
cpuhp/4-31   [004]  22.977: cpuhp_enter: cpu: 0004 target: 140 step: 168 (sched_cpu_deactivate)
cpuhp/4-31   [004]  22.990: cpuhp_exit:  cpu: 0004  state: 168 step: 168 ret: 0
cpuhp/4-31   [004]  22.991: cpuhp_enter: cpu: 0004 target: 140 step: 144 (mce_cpu_pre_down)
cpuhp/4-31   [004]  22.992: cpuhp_exit:  cpu: 0004  state: 144 step: 144 ret: 0
cpuhp/4-31   [004]  22.993: cpuhp_multi_enter: cpu: 0004 target: 140 step: 143 (virtnet_cpu_down_prep)
cpuhp/4-31   [004]  22.994: cpuhp_exit:  cpu: 0004  state: 143 step: 143 ret: 0
cpuhp/4-31   [004]  22.995: cpuhp_enter: cpu: 0004 target: 140 step: 142 (cacheinfo_cpu_pre_down)
cpuhp/4-31   [004]  22.996: cpuhp_exit:  cpu: 0004  state: 142 step: 142 ret: 0
bash-394  [001]  22.997: cpuhp_exit:  cpu: 0004  state: 140 step: 169 ret: 0
bash-394  [005]  95.540: cpuhp_enter: cpu: 0004 target: 169 step: 140 (cpuhp_kick_ap_work)
cpuhp/4-31   [004]  95.541: cpuhp_enter: cpu: 0004 target: 169 step: 141 (acpi_soft_cpu_online)
cpuhp/4-31   [004]  95.542: cpuhp_exit:  cpu: 0004  state: 141 step: 141 ret: 0
cpuhp/4-31   [004]  95.543: cpuhp_enter: cpu: 0004 target: 169 step: 142 (cacheinfo_cpu_online)
cpuhp/4-31   [004]  95.544: cpuhp_exit:  cpu: 0004  state: 142 step: 142 ret: 0
cpuhp/4-31   [004]  95.545: cpuhp_multi_enter: cpu: 0004 target: 169 step: 143 (virtnet_cpu_online)
cpuhp/4-31   [004]  95.546: cpuhp_exit:  cpu: 0004  state: 143 step: 143 ret: 0
cpuhp/4-31   [004]  95.547: cpuhp_enter: cpu: 0004 target: 169 step: 144 (mce_cpu_online)
cpuhp/4-31   [004]  95.548: cpuhp_exit:  cpu: 0004  state: 144 step: 144 ret: 0
cpuhp/4-31   [004]  95.549: cpuhp_enter: cpu: 0004 target: 169 step: 145 (console_cpu_notify)
cpuhp/4-31   [004]  95.550: cpuhp_exit:  cpu: 0004  state: 145 step: 145 ret: 0
cpuhp/4-31   [004]  95.551: cpuhp_enter: cpu: 0004 target: 169 step: 168 (sched_cpu_activate)
cpuhp/4-31   [004]  95.552: cpuhp_exit:  cpu: 0004  state: 168 step: 168 ret: 0
bash-394  [005]  95.553: cpuhp_exit:  cpu: 0004  state: 169 step: 140 ret: 0

如上所示，CPU4 在时间戳22.996之前下线，并在95.552之前上线。所有被调用的回调及其返回码都可见于跟踪日志中。

### 架构需求
===========================

以下函数和配置是必需的：

``CONFIG_HOTPLUG_CPU``
  这个条目需要在Kconfig中启用

``__cpu_up()``
  架构接口用于启动一个CPU

``__cpu_disable()``
  架构接口用于关闭一个CPU，该例程返回后，不再处理任何中断。这包括定时器的关闭
``__cpu_die()``
  这实际上是确保CPU死亡的。实际上，请查看其他架构实现CPU热插拔的一些示例代码。处理器从特定架构的 `idle()` 循环中被取下。`__cpu_die()` 通常会等待一些 per_cpu 状态被设置，以确保处理器死机例程被正确调用。

### 用户空间通知
=======================

当CPU成功上线或下线时，会发送udev事件。像这样的udev规则：

SUBSYSTEM=="cpu", DRIVERS=="processor", DEVPATH=="/devices/system/cpu/*", RUN+="the_hotplug_receiver.sh"

将接收所有事件。类似以下的脚本可以进一步处理这些事件：

#!/bin/sh

if [ "${ACTION}" = "offline" ]
then
    echo "CPU ${DEVPATH##*/} offline"

elif [ "${ACTION}" = "online" ]
then
    echo "CPU ${DEVPATH##*/} online"

fi

### 系统CPU变化时的内核通知
当系统中的CPU发生变化时，`/sys/devices/system/cpu/crash_hotplug` 文件包含 '1' 如果内核自身更新 kdump 捕获内核的CPU列表（通过elfcorehdr），或者 '0' 如果用户空间必须更新 kdump 捕获内核的CPU列表
可用性取决于 CONFIG_HOTPLUG_CPU 内核配置选项
为了跳过 kdump 对 CPU 热插拔/拔出事件的用户空间处理（即卸载-然后重新加载以获得当前的 CPU 列表），此 sysfs 文件可以在 udev 规则中这样使用：

SUBSYSTEM=="cpu", ATTRS{crash_hotplug}=="1", GOTO="kdump_reload_end"

对于 CPU 热插拔/拔出事件，如果架构支持内核更新 elfcorehdr（其中包含 CPU 列表），则此规则将跳过 kdump 捕获内核的卸载-然后重新加载过程。
```
```
内核内联文档参考
==================

.. kernel-doc:: include/linux/cpuhotplug.h
