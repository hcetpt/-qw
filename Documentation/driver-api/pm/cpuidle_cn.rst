SPDX 许可声明标识符: GPL-2.0
.. include:: <isonum.txt>

========================
CPU 空闲时间管理
========================

:版权所有: |copy| 2019 英特尔公司

:作者: Rafael J. Wysocki <rafael.j.wysocki@intel.com>


CPU 空闲时间管理系统
=======================

每当系统中的一个逻辑 CPU（硬件线程或处理器核心等执行指令的实体）在中断或类似唤醒事件后处于空闲状态，即除了与之关联的特殊“空闲”任务外没有其他任务可以运行时，就有机会为所属的处理器节省能量。这可以通过使空闲的逻辑 CPU 停止从内存中获取指令，并将依赖于它的处理器的一些功能单元置于低功耗的空闲状态来实现。然而，在理论上，可能有多种不同的空闲状态可以在这种情况下使用，因此需要找到最合适的空闲状态（从内核的角度来看），并要求处理器进入该特定的空闲状态。这就是内核中称为 `CPUIdle` 的 CPU 空闲时间管理系统的作用。
`CPUIdle` 的设计是模块化的，并基于代码重复避免的原则，因此原则上不依赖于硬件或平台设计细节的通用代码与与硬件交互的代码是分开的。通常，它被分为三个功能单元类别：负责选择要求处理器进入的空闲状态的 *控制器*、将控制器决策传递给硬件的 *驱动程序* 以及为它们提供共同框架的 *核心*。

CPU 空闲时间控制器
=======================

一个 CPU 空闲时间 (`CPUIdle`) 控制器是一组策略代码，当系统中的一个逻辑 CPU 被发现处于空闲状态时会被调用。其作用是选择一个空闲状态要求处理器进入以节省一些能量。
`CPUIdle` 控制器是通用的，每个都可以用于任何Linux内核可以运行的硬件平台上。因此，它们操作的数据结构也不能依赖于任何硬件架构或平台设计细节。
控制器本身由一个 struct cpuidle_governor 对象表示，其中包含四个回调指针：:c:member:`enable`、:c:member:`disable`、:c:member:`select`、:c:member:`reflect`，一个下面描述的 :c:member:`rating` 字段，以及用于识别它的名称（字符串）。
为了让控制器可用，这个对象需要通过调用 :c:func:`cpuidle_register_governor()` 并将指向它的指针作为参数来注册到 `CPUIdle` 核心中。如果成功，这会导致核心将控制器添加到可用控制器的全局列表中，并且如果它是列表中唯一的一个（也就是说，列表之前是空的），或者其 :c:member:`rating` 字段的值大于当前使用的控制器相应字段的值，或者新控制器的名称作为 ``cpuidle.governor=`` 命令行参数的值传递给内核，则从那时起将使用新的控制器（一次只能使用一个 `CPUIdle` 控制器）。此外，用户空间可以通过 `sysfs` 在运行时选择要使用的 `CPUIdle` 控制器。
一旦注册，`CPUIdle` 控制器就不能被注销，因此实际上不能将它们放入可加载的内核模块中。
`CPUIdle` 控制器和核心之间的接口由四个回调组成：

:c:member:`enable`
	::

	  int (*enable) (struct cpuidle_driver *drv, struct cpuidle_device *dev);

此回调的作用是为由 ``dev`` 参数所指向的 struct cpuidle_device 对象表示的（逻辑）CPU 准备控制器。``drv`` 参数所指向的 struct cpuidle_driver 对象代表了将与该 CPU 使用的 `CPUIdle` 驱动程序（其中包括处理器可以被要求进入的空闲状态列表）。
它可能会失败，在这种情况下，它应返回一个负的错误代码，这会导致内核在 `CPUIdle` 代替运行特定于体系结构的默认空闲 CPU 代码，直到再次为该 CPU 调用 ``->enable()`` 控制器回调。
`:c:member:`disable`
	::

	  void (*disable) (struct cpuidle_driver *drv, struct cpuidle_device *dev);

被调用来让管理器停止处理由`dev`参数指向的`struct cpuidle_device`对象所表示的（逻辑）CPU。
它预期会撤销`->enable()`回调在上次为该目标CPU调用时所做的任何更改，释放该回调分配的所有内存等。

`:c:member:`select`
	::

	  int (*select) (struct cpuidle_driver *drv, struct cpuidle_device *dev,
	                 bool *stop_tick);

被调用来为持有`dev`参数所指向的`struct cpuidle_device`对象所表示的（逻辑）CPU的处理器选择一个空闲状态。
考虑的空闲状态列表由`drv`参数指向的`struct cpuidle_driver`对象（代表了要与当前CPU一起使用的`CPUIdle`驱动程序）中持有的`struct cpuidle_state`对象数组`:c:member:`states`表示。此回调返回的值被视为对该数组的索引（除非它是一个负错误码）。
`stop_tick`参数用于指示是否在要求处理器进入选定的空闲状态之前停止调度器的tick。当它指向的`bool`变量（在调用此回调前设置为`true`）被清除为`false`时，处理器将被要求在不阻止给定CPU上的调度器tick的情况下进入选定的空闲状态（然而，如果该CPU上的tick已经被停止，则在要求处理器进入空闲状态之前不会重启它）。
此回调是强制性的（即，在`struct cpuidle_governor`中的`:c:member:`select`回调指针对于管理器注册成功必须不是`NULL`）。

`:c:member:`reflect`
	::

	  void (*reflect) (struct cpuidle_device *dev, int index);

被调用来允许管理器评估由`->select()`回调（上次调用时）做出的空闲状态选择的准确性，并可能利用该结果来提高未来空闲状态选择的准确性。
此外，`CPUIdle`管理器需要在选择空闲状态时考虑处理器唤醒延迟的电源管理质量服务（PM QoS）约束。为了获取给定CPU当前有效的PM QoS唤醒延迟约束，`CPUIdle`管理器应该将CPU编号传递给`:c:func:`cpuidle_governor_latency_req()`。然后，管理器的`->select()`回调不得返回其`:c:member:`exit_latency`值大于该函数返回数字的空闲状态的索引。

### CPU 空闲时间管理驱动程序

#### 概述

CPU空闲时间管理（`CPUIdle`）驱动程序为`CPUIdle`的其他部分和硬件之间提供接口。
首先，`CPUIdle`驱动程序必须填充代表它的`struct cpuidle_driver`对象中包含的`struct cpuidle_state`对象的`:c:member:`states`数组。从今以后，此数组将代表所有由给定驱动程序处理的逻辑CPU可以请求处理器硬件进入的可用空闲状态列表。
`:c:member:`states`数组中的条目应按照struct cpuidle_state中`:c:member:`target_residency`字段的值升序排列（也就是说，索引0应当对应具有最小`:c:member:`target_residency`值的空闲状态）。[由于`:c:member:`target_residency`值预期反映由持有该值的struct cpuidle_state对象所表示的空闲状态的“深度”，因此这种排序顺序应该与按空闲状态“深度”升序排列相同。]

现有`CPUIdle`管理器用于与空闲状态选择相关的计算时会使用struct cpuidle_state中的三个字段：

`:c:member:`target_residency`
    包括进入该空闲状态所需时间在内的在此空闲状态下至少需要花费的最小时间，以节省比在相同时间内保持较浅的空闲状态所能节省更多的能量，单位为微秒。
`:c:member:`exit_latency`
    请求处理器进入此空闲状态的CPU从该空闲状态唤醒后开始执行第一条指令所需的最长时间，单位为微秒。
`:c:member:`flags`
    表示空闲状态特性的标志。目前，管理器仅使用`CPUIDLE_FLAG_POLLING`标志，如果给定的对象不代表真实的空闲状态，而是一个可以用来避免请求处理器进入任何空闲状态的软件“循环”的接口，则设置该标志。[还有其他标志被`CPUIdle`核心在特殊情况下使用。]

struct cpuidle_state中的`:c:member:`enter`回调指针不得为`NULL`，指向请求处理器进入特定空闲状态时要执行的例程：

```
void (*enter) (struct cpuidle_device *dev, struct cpuidle_driver *drv,
               int index);
```

前两个参数分别指向代表运行此回调函数的逻辑CPU的struct cpuidle_device对象和代表驱动程序本身的struct cpuidle_driver对象，最后一个参数是驱动程序`:c:member:`states`数组中代表请求处理器进入的空闲状态的struct cpuidle_state条目的索引。
类似的`->enter_s2idle()`回调在struct cpuidle_state中仅用于实现系统级的空闲挂起电源管理功能。与`->enter()`的不同之处在于，它在任何时刻（即使是暂时）都不能重新启用中断或尝试更改时钟事件设备的状态，而`->enter()`回调可能会这样做。
填充完`:c:member:`states`数组后，必须将其中的有效条目数量存储在代表该驱动程序的struct cpuidle_driver对象的`:c:member:`state_count`字段中。此外，如果`:c:member:`states`数组中的任何条目代表“耦合”空闲状态（即只有当多个相关联的逻辑CPU处于空闲状态时才能请求的空闲状态），则struct cpuidle_driver中的`:c:member:`safe_state_index`字段需要是指向非“耦合”空闲状态（即只有一个逻辑CPU空闲时也可以请求的空闲状态）的索引。
除此之外，如果给定的`CPUIdle`驱动程序仅处理系统中的一组逻辑CPU子集，则其struct cpuidle_driver对象的`:c:member:`cpumask`字段必须指向将由其处理的CPU集合（掩码）。
`CPUIdle`驱动程序只有在注册之后才能使用。如果没有“耦合”空闲状态条目在驱动程序的`:c:member:`states`数组中，可以通过将驱动程序的struct cpuidle_driver对象传递给`:c:func:`cpuidle_register_driver()`来实现注册。否则，应使用`:c:func:`cpuidle_register()`进行此操作。
然而，在注册驱动程序之后还需要通过`:c:func:`cpuidle_register_device()`为所有将由给定`CPUIdle`驱动程序处理的逻辑CPU注册struct cpuidle_device对象。`:c:func:`cpuidle_register_driver()`不像`:c:func:`cpuidle_register()`那样自动完成这项工作。因此，使用`:c:func:`cpuidle_register_driver()`进行自身注册的驱动程序还必须负责按需注册struct cpuidle_device对象，因此通常建议在所有情况下都使用`:c:func:`cpuidle_register()`来注册`CPUIdle`驱动程序。
注册struct cpuidle_device对象会导致创建`CPUIdle`的`sysfs`接口，并调用管理器的`->enable()`回调函数以代表该逻辑CPU，因此必须在注册处理该CPU的驱动程序之后进行。
`CPUIdle` 驱动程序和 `struct cpuidle_device` 对象可以在不再需要时进行注销，这允许与它们相关的一些资源被释放。由于它们之间的依赖关系，在调用 `cpuidle_unregister_driver()` 来注销驱动程序之前，必须通过 `cpuidle_unregister_device()` 函数的帮助来注销所有表示由给定 `CPUIdle` 驱动程序处理的 CPU 的 `struct cpuidle_device` 对象。或者，可以调用 `cpuidle_unregister()` 函数来注销一个 `CPUIdle` 驱动程序及其处理的所有 CPU 的 `struct cpuidle_device` 对象。

`CPUIdle` 驱动程序可以响应运行时系统配置的变化，这些变化会导致可用处理器空闲状态列表的修改（例如，当系统的电源从交流电切换到电池或反过来时）。在收到此类更改的通知后，期望 `CPUIdle` 驱动程序调用 `cpuidle_pause_and_lock()` 函数暂时关闭 `CPUIdle`，然后对所有受该更改影响的 CPU 的 `struct cpuidle_device` 对象调用 `cpuidle_disable_device()` 函数。接下来，它可以按照新系统配置更新其 `states` 数组，为所有相关的 `struct cpuidle_device` 对象调用 `cpuidle_enable_device()` 函数，并调用 `cpuidle_resume_and_unlock()` 函数以再次启用 `CPUIdle` 的使用。
