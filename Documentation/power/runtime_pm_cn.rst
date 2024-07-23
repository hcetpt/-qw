======================================
I/O 设备的运行时电源管理框架
======================================

(C) 2009-2011 拉斐尔·J·维索基 <rjw@sisk.pl>，Novell Inc
(C) 2010 艾伦·斯特恩 <stern@rowland.harvard.edu>

(C) 2014 Intel Corp.，拉斐尔·J·维索基 <rafael.j.wysocki@intel.com>

1. 引言
===============

I/O 设备的运行时电源管理（运行时 PM）支持在电源管理核心（PM 核心）级别通过以下方式提供：

* 电源管理工作队列 pm_wq，总线类型和设备驱动程序可以在其中放置他们的 PM 相关的工作项。强烈建议使用 pm_wq 来排队所有与运行时 PM 相关的工作项，因为这可以使其与系统范围内的电源转换（挂起到内存、休眠以及从系统睡眠状态恢复）同步。pm_wq 在 include/linux/pm_runtime.h 中声明，并在 kernel/power/main.c 中定义。
* 'struct device' 的 'power' 成员中的多个运行时 PM 字段（该结构为 'struct dev_pm_info' 类型，在 include/linux/pm.h 中定义），这些字段可用于相互间同步运行时 PM 操作。
* 'struct dev_pm_ops' 中的三个设备运行时 PM 回调（在 include/linux/pm.h 中定义）
* 在 drivers/base/power/runtime.c 中定义的一组辅助函数，可用于执行运行时 PM 操作，而 PM 核心则负责处理它们之间的同步。鼓励总线类型和设备驱动程序使用这些函数。
在 'struct dev_pm_ops' 中提供的运行时 PM 回调、'struct dev_pm_info' 中的设备运行时 PM 字段以及为运行时 PM 提供的核心辅助函数将在下面进行描述。

2. 设备运行时 PM 回调
==============================

在 'struct dev_pm_ops' 中定义了三个设备运行时 PM 回调如下：

```c
struct dev_pm_ops {
	..
	int (*runtime_suspend)(struct device *dev);
	int (*runtime_resume)(struct device *dev);
	int (*runtime_idle)(struct device *dev);
	..
};
```

PM 核心会为设备的子系统执行 ->runtime_suspend()、->runtime_resume() 和 ->runtime_idle() 回调，该子系统可能是以下之一：

  1. 设备的 PM 域，如果设备的 PM 域对象 dev->pm_domain 存在
  2. 设备的类型，如果同时存在 dev->type 和 dev->type->pm
根据上述规则选择的子系统如果没有提供相关的回调函数，电源管理（PM）核心将直接调用存储在`dev->driver->pm`中的相应驱动程序回调（如果存在）。PM核心总是按照上述给定的顺序检查应使用哪个回调，因此从高到低的回调优先级顺序为：PM域、设备类型、类和总线类型。此外，高优先级的回调将始终优先于低优先级的回调。以下将PM域、总线类型、设备类型和类的回调统称为子系统级回调。

默认情况下，回调函数总是在中断启用的情况下在进程上下文中被调用。然而，`pm_runtime_irq_safe()`辅助函数可以用于告知PM核心，对于给定设备，运行`->runtime_suspend()`、`->runtime_resume()`和`->runtime_idle()`回调在原子上下文且中断禁用时是安全的。这意味着相关回调函数不得阻塞或睡眠，但也意味着第4节末尾列出的同步辅助函数可用于该设备在中断处理器中或通常在原子上下文中使用。

如果存在子系统级挂起回调，则其完全负责根据需要处理设备的挂起，这可能包括执行设备驱动程序自身的`->runtime_suspend()`回调（从PM核心的角度来看，在设备驱动程序中实现`->runtime_suspend()`回调并非必要，只要子系统级挂起回调知道如何处理设备即可）。

一旦子系统级挂起回调（或直接调用的驱动程序挂起回调）成功完成给定设备的处理，PM核心将认为该设备已处于挂起状态，但这并不意味着它已被置于低功耗状态。然而，它应该意味着，直到为其执行适当的恢复回调之前，该设备不会处理数据，也不会与CPU和RAM进行通信。在成功执行挂起回调后，设备的运行时PM状态为“挂起”。

如果挂起回调返回-EBUSY或-EAGAIN，设备的运行时PM状态保持为“活动”，这意味着之后设备必须完全可操作。

如果挂起回调返回除-EBUSY和-EAGAIN之外的错误代码，PM核心将其视为致命错误，并将拒绝为该设备运行第4节中描述的辅助函数，直到其状态直接设置为“活动”或“挂起”（PM核心为此提供了特殊的辅助函数）。

特别地，如果驱动程序要求远程唤醒功能（即允许设备请求改变其电源状态的硬件机制，例如PCI PME）以正常工作，并且`device_can_wakeup()`对于该设备返回‘false’，那么`->runtime_suspend()`应回返-EBUSY。另一方面，如果`device_can_wakeup()`对于该设备返回‘true’并且在执行挂起回调期间设备被置于低功耗状态，则预期会为该设备启用远程唤醒。通常，所有在运行时置于低功耗状态的输入设备都应启用远程唤醒。
子系统级恢复回调（如果存在）对按照适当方式处理设备的恢复负有**全责**，这可能包括但不必一定执行设备驱动程序自身的`->runtime_resume()`回调（从电源管理核心的角度来看，在设备驱动程序中实现`->runtime_resume()`回调并非必要，只要子系统级恢复回调知道如何处理设备即可）。

一旦子系统级恢复回调（或直接调用的驱动程序恢复回调）成功完成，电源管理核心将视该设备为完全可操作状态，这意味着设备**必须**能够根据需要完成I/O操作。此时，设备的运行时电源管理状态为'活动'。

如果恢复回调返回错误代码，电源管理核心将此视为致命错误，并会拒绝为该设备运行第4节中描述的辅助函数，直到其状态被直接设置为'活动'或'挂起'（通过电源管理核心为此目的提供的特殊辅助函数）。

当设备看似处于空闲状态时，电源管理核心将执行空闲回调（如果存在子系统级的，则执行子系统级的，否则执行驱动程序级别的）。设备是否空闲由两个计数器指示：设备使用计数器和设备的'活动'子设备计数器。

如果使用电源管理核心提供的辅助函数减少这些计数器中的任何一个，并且结果等于零，则检查另一个计数器。如果那个计数器也等于零，电源管理核心将用设备作为参数执行空闲回调。

空闲回调执行的动作完全取决于具体子系统（或驱动程序），但预期并推荐的行动是检查设备是否可以被挂起（即所有必要的挂起条件是否满足），并在那种情况下为设备排队一个挂起请求。如果没有空闲回调，或者回调返回0，则电源管理核心将尝试进行设备的运行时挂起，同时也尊重配置了自动挂起的设备。本质上这意味着调用`__pm_runtime_autosuspend()`（请注意，驱动程序需要更新设备最后繁忙标记`pm_runtime_mark_last_busy()`以控制在这种情况下延迟）。为了阻止这种情况（例如，如果回调例程已开始延迟挂起），例程必须返回非零值。负错误返回代码将被电源管理核心忽略。

电源管理核心提供的辅助函数，如第4节所述，确保了以下约束对于单个设备的运行时电源管理回调得到满足：

1. 回调互斥（例如，禁止并行执行`->runtime_suspend()`与`->runtime_resume()`或同一设备的另一个`->runtime_suspend()`实例），例外情况是`->runtime_suspend()`或`->runtime_resume()`可以在`->runtime_idle()`并行执行（尽管在为同一设备执行其他任何回调时不会启动`->runtime_idle()`）。
2. 只能对'活动'设备执行`->runtime_idle()`和`->runtime_suspend()`（即电源管理核心仅对运行时电源管理状态为'活动'的设备执行`->runtime_idle()`或`->runtime_suspend()`）。
3. 只能对使用计数器等于零并且其'活动'子设备计数器等于零或其'power.ignore_children'标志被设置的设备执行`->runtime_idle()`和`->runtime_suspend()`。
4. 只能对'挂起'设备执行`->runtime_resume()`（即电源管理核心仅对运行时电源管理状态为'挂起'的设备执行`->runtime_resume()`）。
此外，由PM核心提供的辅助函数遵循以下规则：

* 如果即将执行`->runtime_suspend()`或有执行它的待处理请求，对于同一设备将不会执行`->runtime_idle()`。
* 执行或调度执行`->runtime_suspend()`的请求会取消针对同一设备执行`->runtime_idle()`的所有待处理请求。
* 如果即将执行`->runtime_resume()`或有执行它的待处理请求，其他回调函数将不会为同一设备执行。
* 执行`->runtime_resume()`的请求会取消针对同一设备执行其他回调的任何待处理或已计划的请求，除了计划中的自动暂停。

3. 运行时PM设备字段
===========================

如在include/linux/pm.h中定义的，以下运行时PM设备字段存在于'struct dev_pm_info'中：

`struct timer_list suspend_timer;`
    - 用于调度（延迟）挂起和自动挂起请求的定时器

`unsigned long timer_expires;`
    - 定时器过期时间，以滴答为单位（如果这与零不同，则定时器正在运行，并将在该时间过期；否则，定时器未运行）

`struct work_struct work;`
    - 用于排队请求（即pm_wq中的工作项）的工作结构

`wait_queue_head_t wait_queue;`
    - 如果任一辅助函数需要等待另一个完成，则使用的等待队列

`spinlock_t lock;`
    - 用于同步的锁

`atomic_t usage_count;`
    - 设备的使用计数器

`atomic_t child_count;`
    - 设备的“活跃”子设备数量

`unsigned int ignore_children;`
    - 如果设置，则child_count值被忽略（但仍更新）

`unsigned int disable_depth;`
    - 用于禁用辅助函数（如果等于零则正常工作）；其初始值为1（即，运行时PM最初对所有设备禁用）

`int runtime_error;`
    - 如果设置，则发生了致命错误（其中一个回调返回了如第2节所述的错误代码），因此辅助函数将无法工作直到此标志被清除；这是失败回调返回的错误代码

`unsigned int idle_notification;`
    - 如果设置，`->runtime_idle()`正在执行

`unsigned int request_pending;`
    - 如果设置，存在一个待处理请求（即，已排入pm_wq的工作项）

`enum rpm_request request;`
    - 待处理的请求类型（如果request_pending设置有效）

`unsigned int deferred_resume;`
    - 如果`->runtime_resume()`即将在设备上运行而`->runtime_suspend()`正在为该设备执行，并且等待挂起完成并不实际，则设置；意味着“一旦你已挂起就立即开始恢复”

`enum rpm_status runtime_status;`
    - 设备的运行时PM状态；此字段的初始值为RPM_SUSPENDED，这意味着每个设备最初都被PM核心视为“挂起”，无论其真实的硬件状态如何

`enum rpm_status last_status;`
    - 禁用运行时PM前捕获的设备的最后一个运行时PM状态（最初无效，当disable_depth为0时无效）

`unsigned int runtime_auto;`
    - 如果设置，表示用户空间允许设备驱动程序通过/sys/devices/.../power/control接口在运行时管理设备的电源；它只能通过pm_runtime_allow()和pm_runtime_forbid()辅助函数修改

`unsigned int no_callbacks;`
    - 表示设备不使用运行时PM回调（参见第8节）；只能通过pm_runtime_no_callbacks()辅助函数修改

`unsigned int irq_safe;`
    - 表示`->runtime_suspend()`和`->runtime_resume()`回调将在自旋锁持有和中断禁用的情况下调用

`unsigned int use_autosuspend;`
    - 表示设备的驱动支持延迟自动挂起（参见第9节）；只能通过pm_runtime{_dont}_use_autosuspend()辅助函数修改

`unsigned int timer_autosuspends;`
    - 表示PM核心应在定时器过期时尝试进行自动挂起而非正常挂起

`int autosuspend_delay;`
    - 要用于自动挂起的延迟时间（以毫秒为单位）

`unsigned long last_busy;`
    - 上次调用pm_runtime_mark_last_busy()辅助函数为此设备的时间；用于计算自动挂起的空闲周期

以上所有字段都是'struct device'的'power'成员的成员。

4. 运行时PM设备辅助函数
=====================================

以下运行时PM辅助函数定义在drivers/base/power/runtime.c和include/linux/pm_runtime.h中：

`void pm_runtime_init(struct device *dev);`
    - 初始化设备运行时PM字段在'struct dev_pm_info'中

`void pm_runtime_remove(struct device *dev);`
    - 确保在从设备层次结构中删除设备后，设备的运行时PM将被禁用

`int pm_runtime_idle(struct device *dev);`
    - 执行设备的子系统级空闲回调；失败时返回错误代码，其中-EINPROGRESS表示`->runtime_idle()`已经在执行；如果没有回调或回调返回0，则运行pm_runtime_autosuspend(dev)并返回其结果

`int pm_runtime_suspend(struct device *dev);`
    - 执行设备的子系统级挂起回调；成功返回0，设备的运行时PM状态已经为“挂起”返回1，或失败时返回错误代码，其中-EAGAIN或-EBUSY意味着将来安全地再次尝试挂起设备，-EACCES意味着'power.disable_depth'不等于0

`int pm_runtime_autosuspend(struct device *dev);`
    - 除考虑自动挂起延迟外，与pm_runtime_suspend()相同；如果pm_runtime_autosuspend_expiration()说延迟尚未过期，则计划在适当时间进行自动挂起，并返回0

`int pm_runtime_resume(struct device *dev);`
    - 执行设备的子系统级恢复回调；成功返回0，设备的运行时PM状态已经是“活动”返回1（也如果'power.disable_depth'非零，但状态在从0变为1时是“活动”），或失败时返回错误代码，其中-EAGAIN意味着可能安全地再次尝试将来恢复设备，但应另外检查'power.runtime_error'，-EACCES意味着由于'power.disable_depth'不等于0，无法运行回调

`int pm_runtime_resume_and_get(struct device *dev);`
    - 运行pm_runtime_resume(dev)，如果成功，则增加设备的使用计数器；返回pm_runtime_resume的结果

`int pm_request_idle(struct device *dev);`
    - 提交执行设备的子系统级空闲回调的请求（该请求由pm_wq中的工作项表示）；成功返回0，或如果请求未排队则返回错误代码

`int pm_request_autosuspend(struct device *dev);`
    - 当自动挂起延迟过期时，安排执行设备的子系统级挂起回调；如果延迟已经过期，则立即排队工作项

`int pm_schedule_suspend(struct device *dev, unsigned int delay);`
    - 在未来安排执行设备的子系统级挂起回调，其中'delay'是在pm_wq中排队挂起工作项之前要等待的时间，以毫秒为单位（如果'delay'为零，则立即排队工作项）；成功返回0，设备的PM运行时状态已经为“挂起”返回1，或如果请求未被安排（或'delay'为0时未排队）则返回错误代码；如果`->runtime_suspend()`的执行已经安排并且尚未过期，则新'delay'值将用作要等待的时间

`int pm_request_resume(struct device *dev);`
    - 提交执行设备的子系统级恢复回调的请求（该请求由pm_wq中的工作项表示）；成功返回0，设备的运行时PM状态已经为“活动”返回1，或如果请求未排队则返回错误代码

`void pm_runtime_get_noresume(struct device *dev);`
    - 增加设备的使用计数器

`int pm_runtime_get(struct device *dev);`
    - 增加设备的使用计数器，运行pm_request_resume(dev)并返回其结果

`int pm_runtime_get_sync(struct device *dev);`
    - 增加设备的使用计数器，运行pm_runtime_resume(dev)并返回其结果；
    注意，它不会在错误时降低设备的使用计数器，因此考虑使用pm_runtime_resume_and_get()代替它，特别是在其返回值由调用者检查时，因为这可能会导致更干净的代码
`int pm_runtime_get_if_in_use(struct device *dev);`
    - 如果'power.disable_depth'非零则返回-EINVAL；否则，如果运行时PM状态为RPM_ACTIVE且运行时PM使用计数器非零，则增加计数器并返回1；否则不改变计数器返回0

`int pm_runtime_get_if_active(struct device *dev);`
    - 如果'power.disable_depth'非零则返回-EINVAL；否则，如果运行时PM状态为RPM_ACTIVE，则增加计数器并返回1；否则不改变计数器返回0

`void pm_runtime_put_noidle(struct device *dev);`
    - 减少设备的使用计数器

`int pm_runtime_put(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_request_idle(dev)并返回其结果

`int pm_runtime_put_autosuspend(struct device *dev);`
    - 目前与__pm_runtime_put_autosuspend()相同，但在未来，也将调用pm_runtime_mark_last_busy()，不要使用！

`int __pm_runtime_put_autosuspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_request_autosuspend(dev)并返回其结果

`int pm_runtime_put_sync(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_idle(dev)并返回其结果

`int pm_runtime_put_sync_suspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_suspend(dev)并返回其结果

`int pm_runtime_put_sync_autosuspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_autosuspend(dev)并返回其结果

`void pm_runtime_enable(struct device *dev);`
    - 减少设备的'power.disable_depth'字段；如果该字段等于零，运行时PM辅助函数可以为设备执行子系统级回调，如第2节所述

`int pm_runtime_disable(struct device *dev);`
    - 增加设备的'power.disable_depth'字段（如果该字段的值以前为零，这将阻止子系统级运行时PM回调为设备运行），确保设备上所有待处理的运行时PM操作要么完成要么取消；如果有待处理的恢复请求并且有必要为满足该请求而执行设备的子系统级恢复回调，则返回1，否则返回0

`int pm_runtime_barrier(struct device *dev);`
    - 检查设备是否有待处理的恢复请求并在此情况下恢复它（同步），取消任何其他待处理的运行时PM请求，并等待所有正在进行的设备上的运行时PM操作完成；如果有待处理的恢复请求并且有必要为满足该请求而执行设备的子系统级恢复回调，则返回1，否则返回0

`void pm_suspend_ignore_children(struct device *dev, bool enable);`
    - 设置/取消设置设备的power.ignore_children标志

`int pm_runtime_set_active(struct device *dev);`
    - 清除设备的'power.runtime_error'标志，将设备的运行时PM状态设置为'活动'，并根据需要更新其父级的'活动'子设备计数器（只有在'power.runtime_error'设置或'power.disable_depth'大于零时才有效使用此函数）；如果设备有一个不是活动的父设备，并且其'power.ignore_children'标志未设置，它将失败并返回错误代码

`void pm_runtime_set_suspended(struct device *dev);`
    - 清除设备的'power.runtime_error'标志，将设备的运行时PM状态设置为'挂起'，并根据需要更新其父级的'活动'子设备计数器（只有在'power.runtime_error'设置或'power.disable_depth'大于零时才有效使用此函数）

`bool pm_runtime_active(struct device *dev);`
    - 如果设备的运行时PM状态为'活动'或其'power.disable_depth'字段不等于零，则返回真，否则返回假

`bool pm_runtime_suspended(struct device *dev);`
    - 如果设备的运行时PM状态为'挂起'且其'power.disable_depth'字段等于零，则返回真，否则返回假

`bool pm_runtime_status_suspended(struct device *dev);`
    - 如果设备的运行时PM状态为'挂起'，则返回真

`void pm_runtime_allow(struct device *dev);`
    - 为设备设置power.runtime_auto标志并减少其使用计数器（由/sys/devices/.../power/control接口使用，有效地允许设备在运行时进行电源管理）

`void pm_runtime_forbid(struct device *dev);`
    - 对于设备取消设置power.runtime_auto标志并增加其使用计数器（由/sys/devices/.../power/control接口使用，有效地阻止设备在运行时进行电源管理）

`void pm_runtime_no_callbacks(struct device *dev);`
    - 为设备设置power.no_callbacks标志并从/sys/devices/.../power移除运行时PM属性（或防止在注册设备时添加它们）

`void pm_runtime_irq_safe(struct device *dev);`
    - 为设备设置power.irq_safe标志，导致运行时PM回调在中断关闭的情况下调用

`bool pm_runtime_is_irq_safe(struct device *dev);`
    - 如果为设备设置了power.irq_safe标志，导致运行时PM回调在中断关闭的情况下调用，则返回真

`void pm_runtime_mark_last_busy(struct device *dev);`
    - 将power.last_busy字段设置为当前时间

`void pm_runtime_use_autosuspend(struct device *dev);`
    - 设置power.use_autosuspend标志，启用自动挂起延迟；如果该标志以前被清除且power.autosuspend_delay为负数，则调用pm_runtime_get_sync

`void pm_runtime_dont_use_autosuspend(struct device *dev);`
    - 取消设置power.use_autosuspend标志，禁用自动挂起延迟；如果该标志以前设置且power.autosuspend_delay为负数，则减少设备的使用计数器并调用pm_runtime_idle

`void pm_runtime_set_autosuspend_delay(struct device *dev, int delay);`
    - 将power.autosuspend_delay值设置为'delay'（以毫秒为单位表达）；如果'delay'为负数，则运行时挂起被阻止；如果power.use_autosuspend设置，pm_runtime_get_sync可能被调用或设备的使用计数器可能被减少并调用pm_runtime_idle，取决于power.autosuspend_delay是否更改为或从负数值；如果power.use_autosuspend未设置，则调用pm_runtime_idle

`unsigned long pm_runtime_autosuspend_expiration(struct device *dev);`
    - 根据power.last_busy和power.autosuspend_delay计算当前自动挂起延迟周期将过期的时间；如果延迟时间为1000毫秒或更大，则过期时间四舍五入到最接近的秒；如果延迟周期已经过期或未设置power.use_autosuspend，则返回0，否则返回到期时间，以滴答为单位

从中断上下文中执行以下辅助函数是安全的：

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

如果为设备调用了pm_runtime_irq_safe()，则以下辅助函数也可以在中断上下文中使用：

- pm_runtime_idle()
- pm_runtime_suspend()
- pm_runtime_autosuspend()
- pm_runtime_resume()
- pm_runtime_get_sync()
- pm_runtime_put_sync()
- pm_runtime_put_sync_suspend()
- pm_runtime_put_sync_autosuspend()

5. 运行时PM初始化、设备探测和移除
========================================================

最初，运行时PM对所有设备都禁用，这意味着在为设备调用pm_runtime_enable()之前，第4节中描述的大多数运行时PM辅助函数将返回-EAGAIN
除此之外，所有设备的初始运行时PM状态为“挂起”，但不一定反映设备的实际物理状态
因此，如果设备最初处于活动状态（即，它可以处理I/O），其运行时PM状态必须在调用pm_runtime_enable()之前通过pm_runtime_set_active()的帮助更改为“活动”。然而，如果设备有父设备且父设备的运行时PM已启用，则除非父设备的'power.ignore_children'标志设置，否则调用pm_runtime_set_active()将影响父设备。也就是说，在这种情况下，只要子设备的状态为“活动”，即使子设备的运行时PM仍然禁用（即尚未为子设备调用pm_runtime_enable()或已为子设备调用pm_runtime_disable()），父设备将无法使用PM核心的辅助函数在运行时进行挂起。出于这个原因，一旦为设备调用了pm_runtime_set_active()，应尽快为设备调用pm_runtime_enable()或使用pm_runtime_set_suspended()将其运行时PM状态更改回“挂起”。
如果设备的默认初始运行时PM状态（即'suspended'）反映了设备的实际状态，其总线类型或驱动程序的->probe()回调可能需要使用PM核心在第4节中描述的其中一个辅助函数来唤醒它。在这种情况下，应使用pm_runtime_resume()。当然，为此，设备的运行时PM必须通过调用pm_runtime_enable()提前启用。

请注意，如果设备可能在探测过程中执行pm_runtime调用（例如，如果它注册了一个可能会回叫的子系统），那么pm_runtime_get_sync()调用与pm_runtime_put()调用配对将是合适的，以确保设备在探测过程中不会再次进入睡眠状态。这可能发生在如网络设备层等系统中。

一旦->probe()完成，可能希望暂停设备。
因此，驱动核心使用异步pm_request_idle()提交请求，在那时执行设备的子系统级空闲回调。利用运行时自动暂停功能的驱动可能希望在从->probe()返回前更新最后忙碌标记。

此外，驱动核心防止运行时PM回调与__device_release_driver()中的总线通知器回调竞态，这是必要的，因为一些子系统使用通知器来执行影响运行时PM功能的操作。它通过在driver_sysfs_remove()和BUS_NOTIFY_UNBIND_DRIVER通知前调用pm_runtime_get_sync()来实现这一点。这会唤醒处于暂停状态的设备，并阻止它在这些例程执行期间再次被暂停。

为了允许总线类型和驱动通过在其->remove()例程中调用pm_runtime_suspend()将设备置于暂停状态，驱动核心在__device_release_driver()中运行BUS_NOTIFY_UNBIND_DRIVER通知后执行pm_runtime_put_sync()。这要求总线类型和驱动使其->remove()回调避免直接与运行时PM竞态，但同时也允许在处理设备的驱动移除期间有更多灵活性。

驱动程序在->remove()回调中应撤销在->probe()中所做的运行时PM更改。通常这意味着调用pm_runtime_disable()、pm_runtime_dont_use_autosuspend()等。

用户空间可以通过将设备的/sys/devices/.../power/control属性值更改为"on"，有效地禁止设备驱动程序在运行时进行电源管理，这会导致调用pm_runtime_forbid()。原则上，此机制也可由驱动程序使用，以有效地关闭设备的运行时电源管理，直到用户空间将其打开。
具体而言，在初始化期间，驱动程序可以确保设备的运行时PM状态为'active'，并调用pm_runtime_forbid()。然而，应该注意的是，如果用户空间已经故意将/sys/devices/.../power/control的值更改为"auto"，以允许驱动程序在运行时进行电源管理，驱动程序以这种方式使用pm_runtime_forbid()可能会混淆用户。

6. 运行时PM与系统休眠
==========================

运行时PM与系统休眠（即，系统挂起和休眠，也称为挂起到RAM和挂起到磁盘）在几个方面相互作用。如果设备在系统休眠开始时是活动的，一切都简单明了。但如果设备已经处于暂停状态呢？

设备对于运行时PM和系统休眠可能有不同的唤醒设置。
例如，可能允许在运行时挂起（runtime suspend）中启用远程唤醒功能，但在系统睡眠状态下则不允许（`device_may_wakeup(dev)` 返回 'false'）。当这种情况发生时，子系统级别的系统挂起回调负责更改设备的唤醒设置（它可能会将此任务留给设备驱动程序的系统挂起例程处理）。为了实现这一目标，可能需要先恢复设备再重新将其置于挂起状态。如果驱动程序为运行时挂起和系统睡眠使用不同的电源级别或其他设置，情况也是如此。

在系统恢复过程中，最简单的方法是将所有设备恢复到全功率状态，即使它们在系统挂起开始之前已经被挂起了。这样做的原因有多个，包括：

  * 设备可能需要切换电源级别、唤醒设置等。
  * 远程唤醒事件可能已被固件丢失。
  * 设备的子设备可能需要设备处于全功率状态才能自行恢复。
  * 驱动程序对设备状态的理解可能与设备的实际物理状态不一致。这可能发生在从休眠中恢复时。
  * 可能需要重置设备。
  * 即使设备被挂起，但如果其使用计数器大于0，则很可能在不久的将来无论如何都需要进行运行时恢复。

如果设备在系统挂起开始之前就已经被挂起，并且在恢复过程中被恢复到全功率状态，那么其运行时电源管理状态必须更新以反映实际的系统睡眠后状态。为此可以执行以下操作：

- `pm_runtime_disable(dev);`
- `pm_runtime_set_active(dev);`
- `pm_runtime_enable(dev);`

电源管理核心总是在调用 `->suspend()` 回调之前增加运行时使用计数器，并在调用 `->resume()` 回调之后减少该计数器。因此，像这样暂时禁用运行时电源管理不会导致任何运行时挂起尝试永久丢失。如果 `->resume()` 回调返回后使用计数变为零，则将像往常一样调用 `->runtime_idle()` 回调。

然而，在某些系统上，系统睡眠并不是通过全局固件或硬件操作进入的。相反，内核会直接协调地将所有硬件组件置于低功耗状态。然后，系统睡眠状态实际上是由硬件组件最终所处的状态决定的，并且系统是从该状态通过硬件中断或完全由内核控制的类似机制唤醒的。因此，内核从未放弃控制权，并且在恢复过程中所有设备的状态都是精确已知的。如果存在这种情况，并且上述列出的情况均未发生（特别是如果系统不是从休眠中唤醒），那么让那些在系统挂起开始之前就已经被挂起的设备保持挂起状态可能更为高效。
为实现此目标，PM（电源管理）核心提供了一种机制，允许在设备层次结构的不同级别之间进行一定程度的协调。具体而言，如果系统挂起.prepare()回调函数为某个设备返回一个正数，这向PM核心表明该设备似乎处于运行时挂起状态且其状态良好，因此只要其所有后代设备也保持在运行时挂起状态，则可以将其留在运行时挂起状态。如果发生这种情况，PM核心将不会对所有这些设备执行任何系统挂起和恢复回调，除了.complete()回调，它完全负责以适当方式处理设备。这仅适用于与休眠无关的系统挂起转换（更多信息请参阅Documentation/driver-api/pm/devices.rst）

PM核心通过以下操作尽力减少运行时PM与系统挂起/恢复（以及休眠）回调之间的竞态条件：

1. 在系统挂起时，对于每个设备，在执行子系统级.prepare()回调之前立即调用pm_runtime_get_noresume()，并且在执行子系统级.suspend()回调之前立即调用pm_runtime_barrier()。此外，在执行子系统级.suspend_late()回调之前，PM核心对每个设备调用__pm_runtime_disable()，第二个参数为'false'
2. 在系统恢复时，对于每个设备，在执行子系统级.resume_early()回调之后立即调用pm_runtime_enable()和pm_runtime_put()，分别在执行子系统级.complete()回调之后立即调用。

7. 泛型子系统回调

子系统可能希望通过使用PM核心提供的泛型电源管理回调集来节省代码空间，这些回调定义在driver/base/power/generic_ops.c中：

   `int pm_generic_runtime_suspend(struct device *dev);` - 调用此设备驱动程序提供的->runtime_suspend()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_runtime_resume(struct device *dev);` - 调用此设备驱动程序提供的->runtime_resume()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_suspend(struct device *dev);` - 如果设备尚未运行时挂起，调用其驱动程序提供的->suspend()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_suspend_noirq(struct device *dev);` - 如果pm_runtime_suspended(dev)返回"false"，调用设备驱动程序提供的->suspend_noirq()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_resume(struct device *dev);` - 调用此设备驱动程序提供的->resume()回调，并在成功后将设备的运行时PM状态更改为'活动'

   `int pm_generic_resume_noirq(struct device *dev);` - 调用此设备驱动程序提供的->resume_noirq()回调

   `int pm_generic_freeze(struct device *dev);` - 如果设备尚未运行时挂起，调用其驱动程序提供的->freeze()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_freeze_noirq(struct device *dev);` - 如果pm_runtime_suspended(dev)返回"false"，调用设备驱动程序提供的->freeze_noirq()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_thaw(struct device *dev);` - 如果设备尚未运行时挂起，调用其驱动程序提供的->thaw()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_thaw_noirq(struct device *dev);` - 如果pm_runtime_suspended(dev)返回"false"，调用设备驱动程序提供的->thaw_noirq()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_poweroff(struct device *dev);` - 如果设备尚未运行时挂起，调用其驱动程序提供的->poweroff()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_poweroff_noirq(struct device *dev);` - 如果pm_runtime_suspended(dev)返回"false"，运行设备驱动程序提供的->poweroff_noirq()回调并返回其结果，或如果未定义则返回0

   `int pm_generic_restore(struct device *dev);` - 调用此设备驱动程序提供的->restore()回调并在成功后将设备的运行时PM状态更改为'活动'

   `int pm_generic_restore_noirq(struct device *dev);` - 调用设备驱动程序提供的->restore_noirq()回调

如果子系统没有为->runtime_idle()，->runtime_suspend()，->runtime_resume()，->suspend()，->suspend_noirq()，->resume()，->resume_noirq()，->freeze()，->freeze_noirq()，->thaw()，->thaw_noirq()，->poweroff()，->poweroff_noirq()，->restore()，->restore_noirq()在子系统级dev_pm_ops结构中提供自己的回调，PM核心将使用这些函数作为默认值

希望使用相同功能作为系统挂起、冻结、断电和运行时挂起回调，以及类似地用于系统恢复、解冻、恢复和运行时恢复的设备驱动程序，可以借助于在include/linux/pm.h中定义的UNIVERSAL_DEV_PM_OPS宏实现这一点（可能将其最后一个参数设置为NULL）

8. "无回调"设备

某些"设备"只是其父设备的逻辑子设备，无法独立进行电源管理。（原型示例是一个USB接口。整个USB设备可以进入低功耗模式或发送唤醒请求，但单个接口都无法做到。）这些设备的驱动程序无需运行时PM回调；如果存在这些回调，->runtime_suspend()和->runtime_resume()将始终返回0而不做其他任何事情，而->runtime_idle()将始终调用pm_runtime_suspend()

子系统可以通过调用pm_runtime_no_callbacks()告诉PM核心关于这些设备的信息。这应在设备结构初始化后且在注册之前完成（尽管在设备注册后也可以）。该例程将设置设备的power.no_callbacks标志并阻止非调试运行时PM sysfs属性的创建

当设置power.no_callbacks时，PM核心将不会调用->runtime_idle()，->runtime_suspend()或->runtime_resume()回调。相反，它会假设挂起和恢复总是成功的，闲置设备应被挂起

因此，PM核心永远不会直接告知设备的子系统或驱动程序关于运行时电源变化。相反，设备父设备的驱动程序必须负责在父设备的电源状态发生变化时通知设备驱动程序。
请注意，在某些情况下，子系统或驱动程序可能不希望为它们的设备调用`pm_runtime_no_callbacks()`。这可能是因为需要实现运行时电源管理（PM）回调的一个子集，或者一个平台相关的PM域可能会附加到设备上，或者该设备是通过供应商设备链接进行电源管理的。由于这些原因以及为了避免在子系统或驱动程序中产生样板代码，PM核心允许运行时PM回调被取消分配。更确切地说，如果回调指针为NULL，PM核心将像存在一个回调且其返回值为0那样行动。

9. 自动延时挂起，或自动延时的挂起

更改设备的电源状态并非没有代价；它既需要时间也需要能量。设备只有在有理由认为它将在该状态下持续一段时间时才应进入低功耗状态。一个常见的启发式方法是：一段时间未使用的设备很可能仍将保持未使用状态；遵循这一建议，驱动程序不应允许设备在达到一定最小闲置期之前进入运行时挂起状态。即使这个启发式方法最终并不总是最优的，但它仍能防止设备在低功耗和全功率状态之间过快地“弹跳”。

“自动挂起”（autosuspend）一词是一个历史遗留。它并不意味着设备会自动挂起（子系统或驱动程序仍然必须调用相应的PM例程）；相反，它的意思是在达到期望的闲置期之前，运行时挂起将自动延迟。

根据`power.last_busy`字段确定设备是否处于空闲状态。驱动程序应在执行I/O操作后调用`pm_runtime_mark_last_busy()`以更新此字段，通常是在调用`__pm_runtime_put_autosuspend()`之前。期望的空闲期长度取决于策略。子系统可以通过调用`pm_runtime_set_autosuspend_delay()`初始设置此长度，但在设备注册后，此长度应由用户空间控制，使用`/sys/devices/.../power/autosuspend_delay_ms`属性。

为了使用自动延时挂起，子系统或驱动程序必须调用`pm_runtime_use_autosuspend`（最好是在注册设备之前），此后他们应该使用各种`*_autosuspend()`辅助函数而不是非自动延时挂起的对应函数：

- 替代`pm_runtime_suspend` 使用：`pm_runtime_autosuspend`
- 替代`pm_schedule_suspend` 使用：`pm_request_autosuspend`
- 替代`pm_runtime_put` 使用：`__pm_runtime_put_autosuspend`
- 替代`pm_runtime_put_sync` 使用：`pm_runtime_put_sync_autosuspend`

驱动程序也可以继续使用非自动延时的辅助函数；它们将正常工作，这意味着有时会考虑自动延时挂起的时间（参见`pm_runtime_idle`）。

在某些情况下，驱动程序或子系统可能希望阻止设备立即自动挂起，即使使用计数器为零且自动延时挂起的时间已过期。如果`->runtime_suspend()`回调返回`-EAGAIN`或`-EBUSY`，并且下一个自动延时挂起到期时间在未来（如果回调调用了`pm_runtime_mark_last_busy()`，通常就是这种情况），PM核心将自动重新安排自动延时挂起。`->runtime_suspend()`回调不能自行执行此重新调度，因为在设备挂起期间（即，当回调正在运行时）不接受任何形式的挂起请求。

这种实现非常适合于在中断上下文中异步使用。
然而，这样的使用不可避免地涉及到竞态条件，因为PM核心无法同步`->runtime_suspend()`回调与I/O请求的到来。
这段代码和描述主要关注于设备驱动程序中读写操作与电源管理之间的同步，特别是自动挂起（autosuspend）机制。以下是翻译后的中文描述：

这种同步必须由驱动程序使用其私有锁来处理。
以下是一个示意性的伪代码示例：

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
    /* 将 req 结果返回给用户... */
}

int foo_runtime_suspend(struct device *dev)
{
    struct foo_priv *foo = container_of(dev, ...);
    int ret = 0;

    lock(&foo->private_lock);
    if (foo->num_pending_requests > 0) {
        ret = -EBUSY;
    } else {
        /* ... 挂起设备... */
        foo->is_suspended = 1;
    }
    unlock(&foo->private_lock);
    return ret;
}

int foo_runtime_resume(struct device *dev)
{
    struct foo_priv *foo = container_of(dev, ...);

    lock(&foo->private_lock);
    /* ... 恢复设备... */
    foo->is_suspended = 0;
    pm_runtime_mark_last_busy(&foo->dev);
    if (foo->num_pending_requests > 0)
        foo_process_next_request(foo);
    unlock(&foo->private_lock);
    return 0;
}
```

关键点在于，在 `foo_io_completion()` 请求自动挂起后，`foo_runtime_suspend()` 回调可能与 `foo_read_or_write()` 并发执行。因此，`foo_runtime_suspend()` 必须在允许挂起进行之前检查是否有待处理的 I/O 请求（同时持有私有锁）。

此外，`power.autosuspend_delay` 字段可以随时被用户空间更改。如果驱动程序关心这一点，它可以在 `->runtime_suspend()` 回调中，在持有私有锁的情况下调用 `pm_runtime_autosuspend_expiration()` 函数。如果该函数返回非零值，则表示延迟尚未到期，回调应返回 `-EAGAIN`。
