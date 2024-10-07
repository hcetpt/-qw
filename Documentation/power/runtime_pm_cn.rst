==================================
I/O 设备的运行时电源管理框架
==================================

(C) 2009-2011 Rafael J. Wysocki <rjw@sisk.pl>，Novell Inc
(C) 2010 Alan Stern <stern@rowland.harvard.edu>

(C) 2014 Intel Corp., Rafael J. Wysocki <rafael.j.wysocki@intel.com>

1. 引言
===============

I/O 设备的运行时电源管理（运行时 PM）支持在电源管理核心（PM 核心）级别通过以下方式提供：

* 电源管理工作队列 `pm_wq`，在此队列中，总线类型和设备驱动程序可以放入它们与 PM 相关的工作项。强烈建议使用 `pm_wq` 来排队所有与运行时 PM 相关的工作项，因为这允许它们与系统范围内的电源转换（挂起到内存、休眠和从系统睡眠状态恢复）同步。`pm_wq` 在 `include/linux/pm_runtime.h` 中声明，并在 `kernel/power/main.c` 中定义。
* `struct device` 的 `power` 成员中的多个运行时 PM 字段（该结构类型为 `struct dev_pm_info`，在 `include/linux/pm.h` 中定义），可用于同步运行时 PM 操作。
* `struct dev_pm_ops` 中的三个设备运行时 PM 回调函数（在 `include/linux/pm.h` 中定义）。
* 在 `drivers/base/power/runtime.c` 中定义的一组辅助函数，可用于执行运行时 PM 操作，使 PM 核心负责它们之间的同步。鼓励总线类型和设备驱动程序使用这些函数。

`struct dev_pm_ops` 中的运行时 PM 回调函数、`struct dev_pm_info` 中的设备运行时 PM 字段以及为运行时 PM 提供的核心辅助函数如下所述。

2. 设备运行时 PM 回调函数
==============================

在 `struct dev_pm_ops` 中定义了三个设备运行时 PM 回调函数：

```c
struct dev_pm_ops {
    ...
    int (*runtime_suspend)(struct device *dev);
    int (*runtime_resume)(struct device *dev);
    int (*runtime_idle)(struct device *dev);
    ...
};
```

`->runtime_suspend()`、`->runtime_resume()` 和 `->runtime_idle()` 回调函数由 PM 核心为设备的子系统执行，该子系统可能是以下两种情况之一：

1. 如果设备的 PM 域对象 `dev->pm_domain` 存在，则为设备的 PM 域。
2. 如果 `dev->type` 和 `dev->type->pm` 都存在，则为设备的类型。
3. 如果设备同时存在 `dev->class` 和 `dev->class->pm`，则使用设备的类（`Device class`）。
4. 如果设备同时存在 `dev->bus` 和 `dev->bus->pm`，则使用设备的总线类型（`Bus type`）。

如果根据上述规则选择的子系统没有提供相关的回调函数，则 PM 核心将直接调用存储在 `dev->driver->pm` 中的相应驱动回调（如果存在的话）。

PM 核心始终按照上述顺序检查要使用的回调函数，因此从高到低的回调优先级顺序为：PM 域、设备类型、设备类和总线类型。此外，高优先级的回调将始终优先于低优先级的回调。以下将 PM 域、总线类型、设备类型和设备类的回调称为子系统级回调。

默认情况下，回调函数总是在开启中断的情况下由进程上下文调用。然而，`pm_runtime_irq_safe()` 辅助函数可以用来告诉 PM 核心，在禁用中断的原子上下文中运行 `->runtime_suspend()`、`->runtime_resume()` 和 `->runtime_idle()` 回调是安全的。这意味着这些回调函数不能阻塞或休眠，但也意味着可以在中断处理程序或一般原子上下文中使用第 4 节末尾列出的同步辅助函数。

如果存在子系统级挂起回调，则该回调完全负责根据需要处理设备的挂起，这可能包括执行设备驱动程序自身的 `->runtime_suspend()` 回调（从 PM 核心的角度来看，只要子系统级挂起回调知道如何处理设备，就不必在设备驱动程序中实现 `->runtime_suspend()` 回调）。

* 一旦子系统级挂起回调（或者直接调用的驱动挂起回调）成功完成，PM 核心将认为设备已被挂起，但这并不意味着设备已进入低功耗状态。其含义应该是设备不会处理数据，也不会与 CPU 和内存通信，直到执行相应的恢复回调为止。成功执行挂起回调后，设备的运行时 PM 状态为“挂起”。
* 如果挂起回调返回 `-EBUSY` 或 `-EAGAIN`，则设备的运行时 PM 状态保持为“活动”，这意味着设备必须在此之后完全可用。
* 如果挂起回调返回除 `-EBUSY` 和 `-EAGAIN` 之外的错误代码，PM 核心将视为致命错误，并拒绝运行第 4 节描述的辅助函数，直到设备状态直接设置为“活动”或“挂起”（PM 核心为此提供了特殊的辅助函数）。

特别是，如果驱动程序需要远程唤醒功能（即允许设备请求更改其电源状态的硬件机制，例如 PCI PME）才能正常工作，并且 `device_can_wakeup()` 返回 `false`，则 `->runtime_suspend()` 应返回 `-EBUSY`。另一方面，如果 `device_can_wakeup()` 返回 `true` 并且设备在执行挂起回调期间进入低功耗状态，则期望启用远程唤醒功能。通常，所有在运行时进入低功耗状态的输入设备都应启用远程唤醒功能。
子系统级恢复回调（如果存在）**完全负责**根据需要处理设备的恢复，这可能包括执行设备驱动程序自身的 `->runtime_resume()` 回调（从电源管理核心的角度来看，在设备驱动程序中实现 `->runtime_resume()` 回调并不是必须的，只要子系统级恢复回调知道如何处理设备即可）。

* 一旦子系统级恢复回调（或直接调用的驱动程序恢复回调）成功完成，电源管理核心认为该设备已完全可用，这意味着设备必须能够按需完成 I/O 操作。此时设备的运行时电源状态为 'active'。
* 如果恢复回调返回错误代码，电源管理核心会将其视为致命错误，并拒绝为该设备运行第 4 节所述的帮助函数，直到其状态直接设置为 'active' 或 'suspended'（通过电源管理核心为此目的提供的特殊帮助函数）。

空闲回调（如果存在，则是子系统级的，否则是驱动程序的）由电源管理核心在设备看似空闲时执行，这是通过两个计数器来指示的：设备的使用计数器和设备的 'active' 子设备计数器。

* 如果这些计数器中的任何一个使用电源管理核心提供的帮助函数递减并发现其等于零，则检查另一个计数器。如果那个计数器也等于零，则电源管理核心将使用该设备作为参数执行空闲回调。

空闲回调执行的操作完全取决于特定的子系统（或驱动程序），但预期且推荐的操作是检查设备是否可以被挂起（即所有必要的条件都满足以挂起设备），并在这种情况下排队一个挂起请求。如果没有空闲回调，或者回调返回 0，则电源管理核心将尝试执行设备的运行时挂起，同时也尊重配置为自动挂起的设备。本质上这意味着调用 `__pm_runtime_autosuspend()`（请注意，驱动程序需要更新设备的最后繁忙标记 `pm_runtime_mark_last_busy()` 来控制在此情况下的延迟）。为了避免这种情况（例如，如果回调例程已启动了延迟挂起），例程必须返回非零值。负的错误返回码会被电源管理核心忽略。

电源管理核心提供的帮助函数（第 4 节描述的），保证了以下约束条件针对单个设备的运行时电源管理回调得以满足：

1. 回调互斥（例如，禁止与 `->runtime_resume()` 或另一个实例的 `->runtime_suspend()` 并行执行 `->runtime_suspend()`，例外情况是 `->runtime_suspend()` 或 `->runtime_resume()` 可以与 `->runtime_idle()` 并行执行（尽管当其他任何回调正在为同一设备执行时，`->runtime_idle()` 不会被启动））。
2. `->runtime_idle()` 和 `->runtime_suspend()` 只能对 'active' 设备执行（即电源管理核心只会为那些运行时电源状态为 'active' 的设备执行 `->runtime_idle()` 或 `->runtime_suspend()`）。
3. `->runtime_idle()` 和 `->runtime_suspend()` 只能对使用计数器等于零且 'active' 子设备计数器等于零或 'power.ignore_children' 标志被设置的设备执行。
4. `->runtime_resume()` 只能对 'suspended' 设备执行（即电源管理核心只会为那些运行时电源状态为 'suspended' 的设备执行 `->runtime_resume()`）。
此外，PM 核心提供的辅助函数遵循以下规则：

  * 如果即将执行 `->runtime_suspend()` 或有请求待执行，则不会为同一设备执行 `->runtime_idle()`。
  * 请求执行或调度执行 `->runtime_suspend()` 将取消任何待执行的 `->runtime_idle()` 请求。
  * 如果即将执行 `->runtime_resume()` 或有请求待执行，则不会为同一设备执行其他回调。
  * 请求执行 `->runtime_resume()` 将取消任何待执行或已调度的其他回调请求（除了已调度的自动挂起）。

### 运行时电源管理设备字段
在 `struct dev_pm_info` 中定义了以下设备运行时电源管理字段，如 `include/linux/pm.h` 中所定义：

  * `struct timer_list suspend_timer;` - 用于调度延迟挂起和自动挂起请求的定时器。
  * `unsigned long timer_expires;` - 定时器到期时间（以滴答为单位），如果此值非零则定时器正在运行且将在该时间到期，否则定时器未运行。
  * `struct work_struct work;` - 用于排队请求的工作结构（即 pm_wq 中的工作项）。
  * `wait_queue_head_t wait_queue;` - 如果任何辅助函数需要等待另一个完成时使用的等待队列。
  * `spinlock_t lock;` - 用于同步的锁。
  * `atomic_t usage_count;` - 设备的使用计数。
  * `atomic_t child_count;` - 设备的“活跃”子设备数量。
  * `unsigned int ignore_children;` - 如果设置，则忽略 child_count 的值（但仍会更新）。
  * `unsigned int disable_depth;` - 用于禁用辅助函数（若为零则它们正常工作）；初始值为 1（即运行时电源管理最初对所有设备禁用）。
  * `int runtime_error;` - 如果设置，则发生致命错误（其中一个回调返回错误代码），因此辅助函数将无法工作直到此标志被清除；这是失败回调返回的错误代码。
  * `unsigned int idle_notification;` - 如果设置，则正在执行 `->runtime_idle()`。
  * `unsigned int request_pending;` - 如果设置，则有请求待处理（即 pm_wq 中排队的工作项）。
  * `enum rpm_request request;` - 待处理请求的类型（仅当 request_pending 设置时有效）。
  * `unsigned int deferred_resume;` - 若 `->runtime_resume()` 即将运行而 `->runtime_suspend()` 正在为此设备执行并且等待挂起完成不切实际时设置；意味着“一旦完成挂起立即开始恢复”。
  * `enum rpm_status runtime_status;` - 设备的运行时电源管理状态；此字段的初始值为 RPM_SUSPENDED，这意味着每个设备最初都被电源管理核心视为“挂起”，无论其实际硬件状态如何。
  * `enum rpm_status last_status;` - 在禁用运行时电源管理之前捕获的设备的最后运行时电源管理状态（初始无效，当 disable_depth 为 0 时无效）。
  * `unsigned int runtime_auto;` - 如果设置，则表示用户空间允许设备驱动程序通过 `/sys/devices/.../power/control` 接口在运行时进行电源管理；只能通过 pm_runtime_allow() 和 pm_runtime_forbid() 辅助函数修改。
  * `unsigned int no_callbacks;` - 表示设备不使用运行时电源管理回调；只能由 pm_runtime_no_callbacks() 辅助函数修改。
  * `unsigned int irq_safe;` - 表示 `->runtime_suspend()` 和 `->runtime_resume()` 回调将在持有自旋锁且中断关闭的情况下调用。
  * `unsigned int use_autosuspend;` - 表示设备驱动程序支持延迟自动挂起；只能由 pm_runtime_use_autosuspend() 和 pm_runtime_dont_use_autosuspend() 辅助函数修改。
  * `unsigned int timer_autosuspends;` - 表示电源管理核心应在定时器到期时尝试进行自动挂起而不是普通挂起。
  * `int autosuspend_delay;` - 要用于自动挂起的延迟时间（毫秒）。
  * `unsigned long last_busy;` - 上次调用 pm_runtime_mark_last_busy() 函数的时间（以滴答为单位）；用于计算自动挂起的空闲期。

以上所有字段都是 `struct device` 中 `power` 成员的一部分。

### 运行时电源管理设备辅助函数
以下运行时电源管理辅助函数定义在 `drivers/base/power/runtime.c` 和 `include/linux/pm_runtime.h` 中：

  * `void pm_runtime_init(struct device *dev);` - 初始化 `struct dev_pm_info` 中的设备运行时电源管理字段。
  * `void pm_runtime_remove(struct device *dev);` - 确保移除设备后设备的运行时电源管理将被禁用。
  * `int pm_runtime_idle(struct device *dev);` - 执行设备的子系统级空闲回调；失败时返回错误代码，其中 -EINPROGRESS 表示 `->runtime_idle()` 已经在执行；如果没有回调或回调返回 0，则运行 pm_runtime_autosuspend(dev) 并返回其结果。
  * `int pm_runtime_suspend(struct device *dev);` - 执行设备的子系统级挂起回调；成功返回 0，设备的运行时电源管理状态已经是“挂起”返回 1，失败返回错误代码，其中 -EAGAIN 或 -EBUSY 表示将来可以安全地再次尝试挂起设备，-EACCES 表示 `power.disable_depth` 不等于 0。
  * `int pm_runtime_autosuspend(struct device *dev);` - 与 pm_runtime_suspend() 相同，但考虑自动挂起延迟；如果 pm_runtime_autosuspend_expiration() 表示延迟尚未到期，则为适当时间安排自动挂起并返回 0。
  * `int pm_runtime_resume(struct device *dev);` - 执行设备的子系统级恢复回调；成功返回 0，设备的运行时电源管理状态已经是“活跃”返回 1（同样，如果 `power.disable_depth` 不为零，但在从 0 变为 1 时状态为“活跃”也会返回 1），失败返回错误代码，其中 -EAGAIN 表示将来可以安全地再次尝试恢复设备，但应检查 `power.runtime_error`，-EACCES 表示回调无法运行，因为 `power.disable_depth` 不等于 0。
  * `int pm_runtime_resume_and_get(struct device *dev);` - 运行 pm_runtime_resume(dev)，如果成功则递增设备的使用计数；返回 pm_runtime_resume 的结果。
  * `int pm_request_idle(struct device *dev);` - 提交执行设备子系统级空闲回调的请求（该请求表示为 pm_wq 中的工作项）；成功返回 0，否则返回错误代码。
  * `int pm_request_autosuspend(struct device *dev);` - 当自动挂起延迟到期时调度执行设备的子系统级挂起回调；如果延迟已经到期，则立即排队工作项。
  * `int pm_schedule_suspend(struct device *dev, unsigned int delay);` - 在未来调度执行设备的子系统级挂起回调，其中 `delay` 是在 pm_wq 中排队挂起工作项前等待的时间（毫秒）（如果 `delay` 为零，则立即排队工作项）；成功返回 0，设备的 PM 运行时状态已经是“挂起”返回 1，如果请求未被调度（或 `delay` 为 0 时未被排队）则返回错误代码；如果 `->runtime_suspend()` 的执行已调度且未到期，则新值 `delay` 将作为等待时间。
  * `int pm_request_resume(struct device *dev);` - 提交执行设备子系统级恢复回调的请求（该请求表示为 pm_wq 中的工作项）；成功返回 0，设备的运行时电源管理状态已经是“活跃”返回 1，否则返回错误代码。
  * `void pm_runtime_get_noresume(struct device *dev);` - 递增设备的使用计数。
  * `int pm_runtime_get(struct device *dev);` - 递增设备的使用计数，运行 pm_request_resume(dev) 并返回其结果。
  * `int pm_runtime_get_sync(struct device *dev);` - 递增设备的使用计数，运行 pm_runtime_resume(dev) 并返回其结果；请注意，在错误时不减少设备的使用计数，因此建议使用 pm_runtime_resume_and_get() 代替它，特别是如果调用者检查其返回值，这可能会产生更清晰的代码。
  * `int pm_runtime_get_if_in_use(struct device *dev);` - 如果 `power.disable_depth` 不为零返回 -EINVAL；否则，如果运行时电源管理状态为 RPM_ACTIVE 且运行时电源管理使用计数不为零，则递增计数并返回 1；否则返回 0 并且不改变计数。
  * `int pm_runtime_get_if_active(struct device *dev);` - 如果 `power.disable_depth` 不为零返回 -EINVAL；否则，如果运行时电源管理状态为 RPM_ACTIVE，则递增计数并返回 1；否则返回 0 并且不改变计数。
  * `void pm_runtime_put_noidle(struct device *dev);` - 减少设备的使用计数。
  * `int pm_runtime_put(struct device *dev);` - 减少设备的使用计数；如果结果为 0 则运行 pm_request_idle(dev) 并返回其结果。
  * `int pm_runtime_put_autosuspend(struct device *dev);` - 目前与 __pm_runtime_put_autosuspend() 做同样的事情，但将来还将调用 pm_runtime_mark_last_busy()，请勿使用！
  * `int __pm_runtime_put_autosuspend(struct device *dev);` - 减少设备的使用计数；如果结果为 0 则运行 pm_request_autosuspend(dev) 并返回其结果。
  * `int pm_runtime_put_sync(struct device *dev);` - 减少设备的使用计数；如果结果为 0 则运行 pm_runtime_idle(dev) 并返回其结果。
  * `int pm_runtime_put_sync_suspend(struct device *dev);` - 减少设备的使用计数；如果结果为 0 则运行 pm_runtime_suspend(dev) 并返回其结果。
  * `int pm_runtime_put_sync_autosuspend(struct device *dev);` - 减少设备的使用计数；如果结果为 0 则运行 pm_runtime_autosuspend(dev) 并返回其结果。
  * `void pm_runtime_enable(struct device *dev);` - 减少设备的 `power.disable_depth` 字段；如果该字段为零，则运行时电源管理辅助函数可以为设备执行第 2 节中描述的子系统级回调。
  * `int pm_runtime_disable(struct device *dev);` - 增加设备的 `power.disable_depth` 字段（如果该字段的值之前为零，则防止为设备运行子系统级运行时电源管理回调），确保设备上所有待处理的运行时电源管理操作要么完成要么取消；如果有一个恢复请求待处理且有必要执行子系统级恢复回调来满足该请求则返回 1，否则返回 0。
  * `int pm_runtime_barrier(struct device *dev);` - 检查设备是否有恢复请求待处理，并在该情况下同步恢复它，取消任何其他待处理的运行时电源管理请求并等待所有正在进行的运行时电源管理操作完成；如果有一个恢复请求待处理且有必要执行子系统级恢复回调来满足该请求则返回 1，否则返回 0。
  * `void pm_suspend_ignore_children(struct device *dev, bool enable);` - 设置或取消设置设备的 `power.ignore_children` 标志。
  * `int pm_runtime_set_active(struct device *dev);` - 清除设备的 `power.runtime_error` 标志，将设备的运行时电源管理状态设置为“活跃”并根据需要更新其父设备的“活跃”子设备计数（只有在 `power.runtime_error` 设置或 `power.disable_depth` 大于零时才有效使用此函数）；如果设备有未激活的父设备且未设置 `power.ignore_children` 标志，则失败并返回错误代码。
  * `void pm_runtime_set_suspended(struct device *dev);` - 清除设备的 `power.runtime_error` 标志，将设备的运行时电源管理状态设置为“挂起”并根据需要更新其父设备的“活跃”子设备计数（只有在 `power.runtime_error` 设置或 `power.disable_depth` 大于零时才有效使用此函数）。
  * `bool pm_runtime_active(struct device *dev);` - 如果设备的运行时电源管理状态为“活跃”或其 `power.disable_depth` 字段不等于零，则返回真，否则返回假。
  * `bool pm_runtime_suspended(struct device *dev);` - 如果设备的运行时电源管理状态为“挂起”且其 `power.disable_depth` 字段等于零，则返回真，否则返回假。
  * `bool pm_runtime_status_suspended(struct device *dev);` - 如果设备的运行时电源管理状态为“挂起”则返回真。
  * `void pm_runtime_allow(struct device *dev);` - 为设备设置 `power.runtime_auto` 标志并减少其使用计数（用于 `/sys/devices/.../power/control` 接口有效地允许设备在运行时进行电源管理）。
  * `void pm_runtime_forbid(struct device *dev);` - 为设备取消设置 `power.runtime_auto` 标志并增加其使用计数（用于 `/sys/devices/.../power/control` 接口有效地阻止设备在运行时进行电源管理）。
  * `void pm_runtime_no_callbacks(struct device *dev);` - 为设备设置 `power.no_callbacks` 标志并从 `/sys/devices/.../power` 中删除运行时电源管理属性（或在注册设备时阻止添加这些属性）。
  * `void pm_runtime_irq_safe(struct device *dev);` - 为设备设置 `power.irq_safe` 标志，导致运行时电源管理回调在中断关闭的情况下调用。
  * `bool pm_runtime_is_irq_safe(struct device *dev);` - 如果为设备设置了 `power.irq_safe` 标志（导致运行时电源管理回调在中断关闭的情况下调用）则返回真。
  * `void pm_runtime_mark_last_busy(struct device *dev);` - 将 `power.last_busy` 字段设置为当前时间。
  * `void pm_runtime_use_autosuspend(struct device *dev);` - 设置 `power.use_autosuspend` 标志，启用自动挂起延迟；如果该标志先前已被清除且 `power.autosuspend_delay` 为负，则调用 pm_runtime_get_sync。
  * `void pm_runtime_dont_use_autosuspend(struct device *dev);` - 取消设置 `power.use_autosuspend` 标志，禁用自动挂起延迟；如果该标志先前已设置且 `power.autosuspend_delay` 为负，则减少设备的使用计数并调用 pm_runtime_idle。
  * `void pm_runtime_set_autosuspend_delay(struct device *dev, int delay);` - 将 `power.autosuspend_delay` 值设置为 `delay`（以毫秒为单位）；如果 `delay` 为负数则阻止运行时挂起；如果 `power.use_autosuspend` 设置，pm_runtime_get_sync 可能会被调用或设备的使用计数可能减少并调用 pm_runtime_idle，具体取决于 `power.autosuspend_delay` 是否从负数变为非负数或相反；如果 `power.use_autosuspend` 未设置，则调用 pm_runtime_idle。
  * `unsigned long pm_runtime_autosuspend_expiration(struct device *dev);` - 根据 `power.last_busy` 和 `power.autosuspend_delay` 计算当前自动挂起延迟周期的到期时间；如果延迟时间为 1000 毫秒或更大，则到期时间向上取整到最近的秒；如果延迟周期已经到期或 `power.use_autosuspend` 未设置则返回 0，否则返回到期时间（以滴答为单位）。

可以在中断上下文中安全执行以下辅助函数：

- pm_request_idle()
- pm_request_autosuspend()
- pm_schedule_suspend()
- pm_request_resume()
- pm_runtime_get_noresume()
- pm_runtime_get()
- pm_runtime_put_noidle()
- pm_runtime_put()
- pm_runtime_put_autosuspend()
- __pm_runtime_put_autosuspend()
- pm_runtime_enable()
- pm_suspend_ignore_children()
- pm_runtime_set_active()
- pm_runtime_set_suspended()
- pm_runtime_suspended()
- pm_runtime_mark_last_busy()
- pm_runtime_autosuspend_expiration()

如果已为设备调用 pm_runtime_irq_safe()，则还可以在中断上下文中使用以下辅助函数：

- pm_runtime_idle()
- pm_runtime_suspend()
- pm_runtime_autosuspend()
- pm_runtime_resume()
- pm_runtime_get_sync()
- pm_runtime_put_sync()
- pm_runtime_put_sync_suspend()
- pm_runtime_put_sync_autosuspend()

### 运行时电源管理初始化、设备探测和移除
最初，所有设备的运行时电源管理都处于禁用状态，这意味着第 4 节中描述的大多数运行时电源管理辅助函数在调用 pm_runtime_enable() 之前都会返回 -EAGAIN。
此外，所有设备的初始运行时电源管理状态为“挂起”，但这不一定反映设备的实际物理状态。
因此，如果设备最初是活跃的（即它可以处理 I/O），则必须在其运行时电源管理状态变为“活跃”，并在调用 pm_runtime_enable() 之前借助 pm_runtime_set_active() 更改设备的运行时电源管理状态。
然而，如果设备有父设备且父设备的运行时电源管理已启用，则除非父设备的 `power.ignore_children` 标志设置，否则调用 pm_runtime_set_active() 将影响父设备。也就是说，在这种情况下，只要子设备的状态为“活跃”，即使子设备的运行时电源管理仍然禁用（即尚未调用 pm_runtime_enable() 或已调用 pm_runtime_disable()），父设备也无法使用电源管理核心的辅助函数在运行时进行挂起。因此，一旦调用 pm_runtime_set_active()，则应尽快调用 pm_runtime_enable()，或者借助 pm_runtime_set_suspended() 将其运行时电源管理状态变回“挂起”。
如果设备的默认初始运行时PM（电源管理）状态（即'suspended'）反映了设备的实际状态，则其总线类型或驱动程序的`->probe()`回调可能需要使用PM核心的辅助函数之一（在第4节中描述）将其唤醒。在这种情况下，应使用`pm_runtime_resume()`。当然，为此目的，必须通过调用`pm_runtime_enable()`提前启用设备的运行时PM。

注意，如果设备可能在`probe`过程中执行`pm_runtime`调用（例如，如果它注册了一个可能回调的子系统），则`pm_runtime_get_sync()`与`pm_runtime_put()`配对调用将确保设备在`probe`期间不会重新进入睡眠状态。这在网络设备层等系统中可能发生。

在`->probe()`完成后，可能希望让设备进入暂停状态。因此，驱动程序核心使用异步`pm_request_idle()`提交请求，在该时刻执行设备的子系统级空闲回调。使用运行时自动暂停功能的驱动程序可能希望在返回`->probe()`之前更新最后的忙碌标记。

此外，驱动程序核心防止运行时PM回调与`__device_release_driver()`中的总线通知器回调竞争，这是必要的，因为一些子系统使用通知器来执行影响运行时PM功能的操作。通过在`driver_sysfs_remove()`和`BUS_NOTIFY_UNBIND_DRIVER`通知之前调用`pm_runtime_get_sync()`来实现这一点。如果设备处于暂停状态，这会恢复设备，并防止这些例程执行时再次暂停。

为了允许总线类型和驱动程序通过在它们的`->remove()`例程中调用`pm_runtime_suspend()`将设备置于暂停状态，驱动程序核心在`__device_release_driver()`中运行`BUS_NOTIFY_UNBIND_DRIVER`通知之后执行`pm_runtime_put_sync()`。这要求总线类型和驱动程序使它们的`->remove()`回调避免直接与运行时PM竞争，但也为处理设备在其驱动程序移除期间提供了更多的灵活性。

在`->remove()`回调中，驱动程序应撤销在`->probe()`中所做的运行时PM更改。通常这意味着调用`pm_runtime_disable()`、`pm_runtime_dont_use_autosuspend()`等。

用户空间可以通过将设备的`/sys/devices/.../power/control`属性值更改为"on"，有效地禁止其驱动程序在运行时进行电源管理，这会导致`pm_runtime_forbid()`被调用。原则上，驱动程序也可以使用此机制有效地关闭设备的运行时电源管理，直到用户空间将其打开。具体来说，在初始化过程中，驱动程序可以确保设备的运行时PM状态为'active'并调用`pm_runtime_forbid()`。然而，如果用户空间已经有意地将`/sys/devices/.../power/control`的值更改为"auto"以允许驱动程序在运行时进行电源管理，则驱动程序可能会通过这种方式使用`pm_runtime_forbid()`引起混淆。

### 运行时PM与系统休眠

运行时PM与系统休眠（即系统挂起和休眠，也称为挂起到RAM和挂起到磁盘）在几个方面相互作用。如果设备在系统休眠开始时是活动的，那么一切都很简单。但如果设备已经处于暂停状态呢？

设备可能具有不同的运行时PM和系统休眠唤醒设置。
例如，远程唤醒功能可能允许在运行时挂起期间启用，但在系统休眠期间不允许（`device_may_wakeup(dev)` 返回 `false`）。在这种情况下，子系统级别的系统挂起回调函数负责更改设备的唤醒设置（它可以将此任务交给设备驱动程序的系统挂起例程来处理）。可能需要先恢复设备然后再将其挂起才能完成这一操作。如果驱动程序为运行时挂起和系统休眠使用不同的电源级别或其他设置，情况也是如此。

在系统恢复过程中，最简单的方法是将所有设备恢复到全功率状态，即使它们在系统挂起开始之前已经被挂起了。这样做的原因有几个，包括：

- 设备可能需要切换电源级别、唤醒设置等。
- 远程唤醒事件可能被固件丢失。
- 设备的子设备可能需要设备处于全功率状态才能恢复自己。
- 驱动程序对设备状态的理解可能与设备的实际物理状态不一致。这可能会在从休眠恢复时发生。
- 设备可能需要重置。
- 即使设备已被挂起，但如果其使用计数器大于 0，则很可能在不久的将来需要运行时恢复。

如果设备在系统挂起开始之前已被挂起，并且在恢复过程中恢复到全功率状态，则其运行时电源管理（PM）状态需要更新以反映实际的系统休眠后状态。具体做法如下：

```c
- pm_runtime_disable(dev);
- pm_runtime_set_active(dev);
- pm_runtime_enable(dev);
```

电源管理核心总是在调用 `->suspend()` 回调函数之前增加运行时使用计数器，并在调用 `->resume()` 回调函数之后减少它。因此，像这样暂时禁用运行时电源管理不会导致任何运行时挂起尝试永久丢失。如果在 `->resume()` 回调函数返回后使用计数器变为零，将像往常一样调用 `->runtime_idle()` 回调函数。

然而，在某些系统中，系统休眠不是通过全局固件或硬件操作进入的。相反，所有硬件组件都是通过内核协调的方式直接进入低功耗状态。然后，系统的休眠状态实际上是由硬件组件最终进入的状态决定的，并且系统会通过硬件中断或类似机制从该状态唤醒，完全由内核控制。因此，内核从未放弃控制权，并且恢复过程中所有设备的状态都是精确已知的。如果这种情况发生，并且上述列出的情况都没有出现（特别是系统不是从休眠中唤醒），则让那些在系统挂起前已被挂起的设备保持挂起状态可能会更高效。
为此，PM（电源管理）核心提供了一种机制，允许在设备层次结构的不同级别之间进行一些协调。具体来说，如果系统挂起.prepare()回调函数为某个设备返回一个正数，这表明PM核心该设备似乎处于运行时挂起状态，并且其状态良好，因此可以在所有子设备也保持运行时挂起的情况下将其保留在运行时挂起状态。如果发生这种情况，PM核心将不会执行这些设备的任何系统挂起和恢复回调，除了.complete()回调，该回调完全负责根据需要处理设备。这仅适用于与休眠无关的系统挂起转换（更多信息请参阅Documentation/driver-api/pm/devices.rst）。

PM核心通过以下操作尽可能减少运行时电源管理和系统挂起/恢复（以及休眠）回调之间的竞争条件：

  * 在系统挂起期间，对于每个设备，在执行子系统级.prepare()回调之前调用pm_runtime_get_noresume()，并在执行子系统级.suspend()回调之前调用pm_runtime_barrier()。此外，PM核心在执行子系统级.suspend_late()回调之前，为每个设备以“false”作为第二个参数调用__pm_runtime_disable()

  * 在系统恢复期间，对于每个设备，在执行子系统级.resume_early()回调之后调用pm_runtime_enable()和pm_runtime_put()，以及在执行子系统级.complete()回调之后调用它们

7. 通用子系统回调
==================

子系统可能希望通过使用PM核心提供的通用电源管理回调来节省代码空间，这些回调定义在driver/base/power/generic_ops.c中：

  `int pm_generic_runtime_suspend(struct device *dev);`  
  - 调用此设备驱动程序提供的->runtime_suspend()回调并返回其结果，或未定义时返回0

  `int pm_generic_runtime_resume(struct device *dev);`  
  - 调用此设备驱动程序提供的->runtime_resume()回调并返回其结果，或未定义时返回0

  `int pm_generic_suspend(struct device *dev);`  
  - 如果设备尚未运行时挂起，则调用其驱动程序提供的->suspend()回调并返回其结果，或未定义时返回0

  `int pm_generic_suspend_noirq(struct device *dev);`  
  - 如果pm_runtime_suspended(dev)返回“false”，则调用设备驱动程序提供的->suspend_noirq()回调并返回其结果，或未定义时返回0

  `int pm_generic_resume(struct device *dev);`  
  - 调用此设备驱动程序提供的->resume()回调，如果成功，则将设备的运行时电源管理状态更改为“活动”

  `int pm_generic_resume_noirq(struct device *dev);`  
  - 调用此设备驱动程序提供的->resume_noirq()回调

  `int pm_generic_freeze(struct device *dev);`  
  - 如果设备尚未运行时挂起，则调用其驱动程序提供的->freeze()回调并返回其结果，或未定义时返回0

  `int pm_generic_freeze_noirq(struct device *dev);`  
  - 如果pm_runtime_suspended(dev)返回“false”，则调用设备驱动程序提供的->freeze_noirq()回调并返回其结果，或未定义时返回0

  `int pm_generic_thaw(struct device *dev);`  
  - 如果设备尚未运行时挂起，则调用其驱动程序提供的->thaw()回调并返回其结果，或未定义时返回0

  `int pm_generic_thaw_noirq(struct device *dev);`  
  - 如果pm_runtime_suspended(dev)返回“false”，则调用设备驱动程序提供的->thaw_noirq()回调并返回其结果，或未定义时返回0

  `int pm_generic_poweroff(struct device *dev);`  
  - 如果设备尚未运行时挂起，则调用其驱动程序提供的->poweroff()回调并返回其结果，或未定义时返回0

  `int pm_generic_poweroff_noirq(struct device *dev);`  
  - 如果pm_runtime_suspended(dev)返回“false”，则运行设备驱动程序提供的->poweroff_noirq()回调并返回其结果，或未定义时返回0

  `int pm_generic_restore(struct device *dev);`  
  - 调用此设备驱动程序提供的->restore()回调，如果成功，则将设备的运行时电源管理状态更改为“活动”

  `int pm_generic_restore_noirq(struct device *dev);`  
  - 调用设备驱动程序提供的->restore_noirq()回调

如果子系统没有为其->runtime_idle()、->runtime_suspend()、->runtime_resume()、->suspend()、->suspend_noirq()、->resume()、->resume_noirq()、->freeze()、->freeze_noirq()、->thaw()、->thaw_noirq()、->poweroff()、->poweroff_noirq()、->restore()、->restore_noirq()在子系统级dev_pm_ops结构中提供自己的回调，则PM核心会使用这些函数作为默认值。
希望使用相同函数作为系统挂起、冻结、断电和运行时挂起回调的设备驱动程序，以及类似地用于系统恢复、解冻、恢复和运行时恢复，可以通过include/linux/pm.h中定义的UNIVERSAL_DEV_PM_OPS宏实现这一点（可能将其最后一个参数设置为NULL）

8. “无回调”设备
=================

某些“设备”仅仅是其父设备的逻辑子设备，无法独立进行电源管理。（原型示例是一个USB接口。整个USB设备可以进入低功耗模式或发送唤醒请求，但单个接口无法做到这一点。）这些设备的驱动程序不需要运行时电源管理回调；如果存在回调，->runtime_suspend()和->runtime_resume()将始终返回0而不执行其他任何操作，而->runtime_idle()将始终调用pm_runtime_suspend()。
子系统可以通过调用pm_runtime_no_callbacks()告诉PM核心这些设备。这应在设备结构初始化后并在注册之前完成（尽管在设备注册后也可以）。该例程将设置设备的power.no_callbacks标志，并阻止创建非调试运行时电源管理sysfs属性。
当设置了power.no_callbacks时，PM核心将不会调用->runtime_idle()、->runtime_suspend()或->runtime_resume()回调。相反，它将假设挂起和恢复总是成功的，并且空闲设备应被挂起。
因此，PM核心永远不会直接通知设备的子系统或驱动程序关于运行时电源变化。相反，设备父设备的驱动程序必须负责在父设备的电源状态发生变化时告知设备驱动程序。
请注意，在某些情况下，子系统或驱动程序可能不希望为它们的设备调用 `pm_runtime_no_callbacks()`。这可能是因为需要实现一部分运行时电源管理（PM）回调，或者一个与平台相关的电源域可能会附加到该设备上，又或者设备是通过供应商设备链进行电源管理的。出于这些原因，并为了避免在子系统或驱动程序中出现样板代码，PM 核心允许运行时 PM 回调被取消绑定。更确切地说，如果一个回调指针为 NULL，PM 核心将像存在一个回调并返回 0 一样处理。

9. 自动延时挂起（Autosuspend）
================================

改变设备的电源状态并不是没有代价的；它既需要时间也需要能量。只有当有理由认为设备将在低功耗状态下保持相当长一段时间时，才应将其置于低功耗状态。一个常见的启发式方法认为，如果设备一段时间内未被使用，则它很可能将继续处于未使用状态；根据这一建议，驱动程序不应允许设备在达到一定最短不活动期之前进入运行时挂起状态。即使这种启发式方法最终并非最优选择，它也能防止设备在低功耗和全功率状态之间频繁切换。

“自动延时挂起”这一术语是一个历史遗留概念。它并不意味着设备会自动挂起（子系统或驱动程序仍需调用相应的 PM 例程），而是意味着运行时挂起将自动延至所需的不活动期结束后才执行。不活动期是基于 `power.last_busy` 字段来确定的。驱动程序应在执行 I/O 操作后调用 `pm_runtime_mark_last_busy()` 来更新此字段，通常是在调用 `__pm_runtime_put_autosuspend()` 之前。所需不活动期的长度是一个策略问题。子系统可以通过调用 `pm_runtime_set_autosuspend_delay()` 初始设置此长度，但在设备注册之后，该长度应由用户空间控制，使用 `/sys/devices/.../power/autosuspend_delay_ms` 属性。

为了使用自动延时挂起，子系统或驱动程序必须调用 `pm_runtime_use_autosuspend`（最好是在注册设备之前），此后应使用各种 `*_autosuspend()` 辅助函数而不是非自动延时挂起的对应函数：

- 替代 `pm_runtime_suspend` 使用：`pm_runtime_autosuspend`;
- 替代 `pm_schedule_suspend` 使用：`pm_request_autosuspend`;
- 替代 `pm_runtime_put` 使用：`__pm_runtime_put_autosuspend`;
- 替代 `pm_runtime_put_sync` 使用：`pm_runtime_put_sync_autosuspend`

驱动程序也可以继续使用非自动延时辅助函数；它们将正常工作，这意味着有时会考虑自动延时挂起（参见 `pm_runtime_idle`）。

在某些情况下，驱动程序或子系统可能希望即使使用计数器为零且自动延时挂起时间已过期，也不立即让设备自动延时挂起。如果 `->runtime_suspend()` 回调返回 `-EAGAIN` 或 `-EBUSY`，并且下一个自动延时挂起时间在未来（如果该回调调用了 `pm_runtime_mark_last_busy()`，通常就是这样），PM 核心将自动重新调度自动延时挂起。`->runtime_suspend()` 回调不能自行完成这种重新调度，因为设备正在挂起期间（即回调运行时）不接受任何形式的挂起请求。

该实现在中断上下文中非常适合异步使用。然而，这种使用不可避免地涉及竞争条件，因为 PM 核心无法同步 `->runtime_suspend()` 回调与 I/O 请求的到来。
这种同步必须由驱动程序通过其私有锁来处理。以下是一个示意性的伪代码示例：

```c
foo_read_or_write(struct foo_priv *foo, void *data)
{
    lock(&foo->private_lock);
    add_request_to_io_queue(foo, data);
    if (++foo->num_pending_requests == 1)
        pm_runtime_get(&foo->dev);
    if (!foo->is_suspended)
        foo_process_next_request(foo);
    unlock(&foo->private_lock);
}

foo_io_completion(struct foo_priv *foo, void *req)
{
    lock(&foo->private_lock);
    if (--foo->num_pending_requests == 0) {
        pm_runtime_mark_last_busy(&foo->dev);
        __pm_runtime_put_autosuspend(&foo->dev);
    } else {
        foo_process_next_request(foo);
    }
    unlock(&foo->private_lock);
    /* 将请求结果返回给用户 ... */
}

int foo_runtime_suspend(struct device *dev)
{
    struct foo_priv *foo = container_of(dev, struct foo_priv, dev);
    int ret = 0;

    lock(&foo->private_lock);
    if (foo->num_pending_requests > 0) {
        ret = -EBUSY;
    } else {
        /* ... 暂停设备 ... */
        foo->is_suspended = 1;
    }
    unlock(&foo->private_lock);
    return ret;
}

int foo_runtime_resume(struct device *dev)
{
    struct foo_priv *foo = container_of(dev, struct foo_priv, dev);

    lock(&foo->private_lock);
    /* ... 恢复设备 ... */
    foo->is_suspended = 0;
    pm_runtime_mark_last_busy(&foo->dev);
    if (foo->num_pending_requests > 0)
        foo_process_next_request(foo);
    unlock(&foo->private_lock);
    return 0;
}
```

关键点是，在 `foo_io_completion()` 请求自动暂停之后，`foo_runtime_suspend()` 回调可能会与 `foo_read_or_write()` 发生竞争。因此，`foo_runtime_suspend()` 必须在持有私有锁的情况下检查是否有待处理的 I/O 请求，然后再允许暂停继续进行。

此外，`power.autosuspend_delay` 字段可以随时被用户空间更改。如果驱动程序关心这一点，它可以在 `->runtime_suspend()` 回调中持有所需的私有锁时调用 `pm_runtime_autosuspend_expiration()`。如果该函数返回非零值，则延迟尚未过期，回调应返回 `-EAGAIN`。
