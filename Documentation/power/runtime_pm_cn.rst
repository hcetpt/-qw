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
* 一组在 drivers/base/power/runtime.c 中定义的帮助函数，可用于执行运行时 PM 操作，而 PM 核心则负责处理这些操作之间的同步。鼓励总线类型和设备驱动程序使用这些函数。
在 'struct dev_pm_ops' 中的运行时 PM 回调，'struct dev_pm_info' 中的设备运行时 PM 字段以及为运行时 PM 提供的核心帮助函数将在下文进行描述。

2. 设备运行时 PM 回调
==============================

在 'struct dev_pm_ops' 中定义了三个设备运行时 PM 回调：

```c
struct dev_pm_ops {
    ...
    int (*runtime_suspend)(struct device *dev);
    int (*runtime_resume)(struct device *dev);
    int (*runtime_idle)(struct device *dev);
    ...
};
```

->runtime_suspend()，->runtime_resume() 和 ->runtime_idle() 回调由 PM 核心针对设备的子系统执行，该子系统可能是以下之一：

  1. 如果设备的 PM 域对象（dev->pm_domain）存在，则是设备的 PM 域。
  2. 如果 dev->type 和 dev->type->pm 都存在，则是设备的类型。
根据上述内容，翻译如下：

3. 如果`dev->class`和`dev->class->pm`都存在，则为设备的类（Device Class）。
4. 如果`dev->bus`和`dev->bus->pm`都存在，则为设备的总线类型（Bus Type）。

如果根据以上规则选择的子系统没有提供相关的回调函数，电源管理（PM）核心将直接调用存储在`dev->driver->pm`中的相应驱动回调（如果存在）。

PM核心总是按照上面给出的顺序检查要使用的回调函数，因此回调函数的优先级从高到低依次是：PM域、设备类型、设备类和总线类型。此外，高优先级的回调函数总是会优先于低优先级的回调函数。接下来提到的PM域、总线类型、设备类型和设备类的回调函数统称为子系统级别的回调函数。

默认情况下，回调函数总是在中断启用的情况下以进程上下文被调用。但是，可以使用`pm_runtime_irq_safe()`辅助函数告诉PM核心对于给定设备来说，在中断禁用的原子上下文中运行`->runtime_suspend()`、`->runtime_resume()`和`->runtime_idle()`回调函数是安全的。这意味着这些回调函数本身不能阻塞或睡眠，但这也意味着可以在中断处理程序中或一般地在原子上下文中使用第4节末尾列出的同步辅助函数来处理该设备。

如果存在子系统级别的挂起回调函数，它将完全负责根据需要处理设备的挂起操作，这可能包括执行设备驱动程序自身的`->runtime_suspend()`回调函数（从PM核心的角度来看，只要子系统级别的挂起回调函数知道如何处理设备，就不需要在设备驱动程序中实现`->runtime_suspend()`回调函数）。

* 一旦子系统级别的挂起回调函数（或直接调用的驱动挂起回调函数）成功完成对给定设备的操作，PM核心认为该设备已处于挂起状态，但这并不一定意味着设备已被置于低功耗状态。然而，它应该意味着设备不会处理数据且不会与CPU和RAM通信，直到相应的恢复回调函数被执行。设备在成功执行挂起回调函数后其运行时PM状态变为“挂起”。
* 如果挂起回调函数返回-EBUSY或-EAGAIN，设备的运行时PM状态保持为“活动”，这意味着设备之后必须完全可用。
* 如果挂起回调函数返回除-EBUSY和-EAGAIN之外的错误代码，PM核心将其视为致命错误，并拒绝为该设备运行第4节中描述的辅助函数，除非其状态被直接设置为“活动”或“挂起”（PM核心为此提供了专用的辅助函数）。

特别是，如果驱动程序需要远程唤醒功能（即允许设备请求改变其功耗状态的硬件机制，例如PCI PME）以便正常工作，并且`device_can_wakeup()`返回“false”表示该设备，则`->runtime_suspend()`应回返-EBUSY。另一方面，如果`device_can_wakeup()`对于该设备返回“true”，并且在执行挂起回调函数期间将设备置于低功耗状态，则预期会为设备启用远程唤醒功能。一般来说，对于所有在运行时置于低功耗状态的输入设备，都应该启用远程唤醒功能。
子系统级恢复回调（如果存在）**全权负责**根据需要处理设备的恢复，这可能包括执行设备驱动程序自身的 `->runtime_resume()` 回调，但也可能不包括（从电源管理核心的角度来看，在设备驱动程序中实现 `->runtime_resume()` 回调并非必须，只要子系统级恢复回调知道如何处理该设备即可）。
* 一旦子系统级恢复回调（或直接调用的驱动程序恢复回调）成功完成，电源管理核心认为该设备已完全可用，这意味着该设备**必须**能够按需完成 I/O 操作。此时，设备的运行时电源状态为“活动”。
* 如果恢复回调返回错误代码，电源管理核心将此视为致命错误，并会拒绝为该设备运行第 4 节中描述的帮助函数，直到其状态被直接设置为“活动”或“挂起”（通过电源管理核心为此目的提供的特殊帮助函数）。
空闲回调（如果存在，则是子系统级的，否则为驱动程序级别的）由电源管理核心在设备看似空闲时执行，这是通过两个计数器指示给电源管理核心的：设备的使用计数器和设备的“活动”子设备计数器。
* 如果使用电源管理核心提供的帮助函数减少这些计数器中的任何一个，并且结果等于零，则检查另一个计数器。如果那个计数器也等于零，则电源管理核心将使用该设备作为参数执行空闲回调。
空闲回调所执行的操作完全取决于具体的子系统（或驱动程序），但预期并推荐的操作是检查设备是否可以挂起（即所有必要的挂起条件是否满足），并在那种情况下为设备排队一个挂起请求。如果没有空闲回调，或者回调返回 0，则电源管理核心将尝试对设备进行运行时挂起，同时也尊重配置了自动挂起的设备。本质上这意味着调用 `__pm_runtime_autosuspend()`（请注意，驱动程序需要更新设备最后忙标记 `pm_runtime_mark_last_busy()` 来控制在这种情况下延迟）。为了阻止这种情况（例如，如果回调例程已经开始了一个延时挂起），该例程必须返回一个非零值。负的错误返回码会被电源管理核心忽略。
电源管理核心提供的帮助函数（第 4 节中描述的），保证对于单个设备的运行时电源管理回调满足以下约束：

1. 回调互斥（例如，禁止与 `->runtime_resume()` 或同一设备的另一个 `->runtime_suspend()` 实例并行执行 `->runtime_suspend()`），例外情况是 `->runtime_suspend()` 或 `->runtime_resume()` 可以与 `->runtime_idle()` 并行执行（尽管当其他回调正在为同一设备执行时，`->runtime_idle()` 不会被启动）。
2. `->runtime_idle()` 和 `->runtime_suspend()` 只能针对“活动”设备执行（即，电源管理核心只会为运行时电源状态为“活动”的设备执行 `->runtime_idle()` 或 `->runtime_suspend()`）。
3. `->runtime_idle()` 和 `->runtime_suspend()` 只能针对使用计数器为零的设备以及“活动”子设备计数器为零或“power.ignore_children”标志被设置的设备执行。
4. `->runtime_resume()` 只能针对“挂起”设备执行（即，电源管理核心只会为运行时电源状态为“挂起”的设备执行 `->runtime_resume()`）。
此外，由PM核心提供的辅助函数遵循以下规则：

  * 如果将要执行`->runtime_suspend()`或有执行它的待处理请求，对于同一设备将不会执行`->runtime_idle()`。
  * 执行或调度执行`->runtime_suspend()`的请求将取消任何执行`->runtime_idle()`的待处理请求，对于同一设备。
  * 如果`->runtime_resume()`将要执行或有执行它的待处理请求，其他回调函数将不会被同一设备调用。
  * 执行`->runtime_resume()`的请求将取消任何待处理或已调度的执行其他回调函数的请求，对于同一设备，除了已调度的自动挂起操作。
3. 运行时PM设备字段
======================
以下运行时PM设备字段存在于`struct dev_pm_info`中，如在include/linux/pm.h中定义的那样：

  `struct timer_list suspend_timer;`
    - 用于调度（延迟）挂起和自动挂起请求的定时器

  `unsigned long timer_expires;`
    - 定时器过期时间，以jiffies为单位（如果这个值不同于零，则定时器正在运行，并将在那时过期，否则定时器没有运行）

  `struct work_struct work;`
    - 用于排队请求的工作结构（即pm_wq中的工作项）

  `wait_queue_head_t wait_queue;`
    - 如果任何一个辅助函数需要等待另一个完成，则使用的等待队列

  `spinlock_t lock;`
    - 用于同步的锁

  `atomic_t usage_count;`
    - 设备的使用计数器

  `atomic_t child_count;`
    - 设备的“活动”子设备的数量

  `unsigned int ignore_children;`
    - 如果设置，则忽略child_count的值（但仍然更新它）

  `unsigned int disable_depth;`
    - 用于禁用辅助函数（如果这个等于零则它们正常工作）；初始值为1（即运行时PM最初对所有设备都是禁用的）

  `int runtime_error;`
    - 如果设置，则发生了一个致命错误（其中一个回调返回了错误码，如第二节所述），因此辅助函数将无法工作直到此标志被清除；这是失败回调返回的错误码

  `unsigned int idle_notification;`
    - 如果设置，则`->runtime_idle()`正在执行

  `unsigned int request_pending;`
    - 如果设置，则存在一个待处理的请求（即已排入pm_wq的工作项）

  `enum rpm_request request;`
    - 待处理的请求类型（如果request_pending设置有效）

  `unsigned int deferred_resume;`
    - 如果设置，则当`->runtime_suspend()`正在为此设备执行而`->runtime_resume()`即将运行且等待挂起完成不实际时；意味着“一旦你完成了挂起就启动恢复”

  `enum rpm_status runtime_status;`
    - 设备的运行时PM状态；此字段的初始值是RPM_SUSPENDED，这意味着每个设备最初都被PM核心视为“挂起”，不管其真实的硬件状态如何

  `enum rpm_status last_status;`
    - 禁用运行时PM之前捕获的设备的最后运行时PM状态（最初无效，当disable_depth为0时无效）

  `unsigned int runtime_auto;`
    - 如果设置，则表明用户空间允许设备驱动程序通过/sys/devices/.../power/control接口实时管理设备的电源；只能通过pm_runtime_allow()和pm_runtime_forbid()辅助函数修改

  `unsigned int no_callbacks;`
    - 表明设备不使用运行时PM回调（见第8节）；只能由pm_runtime_no_callbacks()辅助函数修改

  `unsigned int irq_safe;`
    - 表明`->runtime_suspend()`和`->runtime_resume()`回调将在持有自旋锁并禁用中断的情况下被调用

  `unsigned int use_autosuspend;`
    - 表明设备的驱动程序支持延迟自动挂起（见第9节）；只能由pm_runtime_use_autosuspend()和pm_runtime_dont_use_autosuspend()辅助函数修改

  `unsigned int timer_autosuspends;`
    - 表明PM核心应该尝试在定时器过期时进行自动挂起而非正常的挂起

  `int autosuspend_delay;`
    - 要用于自动挂起的延迟时间（以毫秒为单位）

  `unsigned long last_busy;`
    - 上次为该设备调用pm_runtime_mark_last_busy()辅助函数的时间（以jiffies为单位）；用于计算自动挂起的空闲周期

以上所有字段都是`struct device`中的'power'成员的部分。
4. 运行时PM设备辅助函数
=======================
以下运行时PM辅助函数在drivers/base/power/runtime.c和include/linux/pm_runtime.h中定义：

  `void pm_runtime_init(struct device *dev);`
    - 初始化设备运行时PM字段在`struct dev_pm_info`中

  `void pm_runtime_remove(struct device *dev);`
    - 确保在从设备层次结构中移除设备后禁用设备的运行时PM

  `int pm_runtime_idle(struct device *dev);`
    - 执行设备的子系统级idle回调；失败时返回错误码，其中-EINPROGRESS表示`->runtime_idle()`已经在执行；如果没有回调或者回调返回0，则运行pm_runtime_autosuspend(dev)并返回其结果

  `int pm_runtime_suspend(struct device *dev);`
    - 执行设备的子系统级挂起回调；成功返回0，设备的运行时PM状态已经是'suspended'返回1，或者失败时返回错误码，其中-EAGAIN或-EBUSY意味着将来安全地再次尝试挂起设备，-EACCES意味着'power.disable_depth'不等于0

  `int pm_runtime_autosuspend(struct device *dev);`
    - 与pm_runtime_suspend()相同，但考虑到自动挂起延迟；如果pm_runtime_autosuspend_expiration()说延迟尚未过期，则为适当的时间安排自动挂起并返回0

  `int pm_runtime_resume(struct device *dev);`
    - 执行设备的子系统级恢复回调；成功返回0，设备的运行时PM状态已经是'active'（也包括'power.disable_depth'非零，但状态在从0变为1时是'active'的情况）返回1，或者失败时返回错误码，其中-EAGAIN意味着将来可能安全地再次尝试恢复设备，但还应检查'power.runtime_error'，-EACCES意味着无法运行回调，因为'power.disable_depth'不同于0

  `int pm_runtime_resume_and_get(struct device *dev);`
    - 运行pm_runtime_resume(dev)，如果成功，增加设备的使用计数器；返回pm_runtime_resume的结果

  `int pm_request_idle(struct device *dev);`
    - 提交执行设备子系统级idle回调的请求（该请求由pm_wq中的工作项表示）；成功返回0，或者如果没有排队请求则返回错误码

  `int pm_request_autosuspend(struct device *dev);`
    - 当自动挂起延迟过期时安排执行设备的子系统级挂起回调；如果延迟已经过期，则立即排队工作项

  `int pm_schedule_suspend(struct device *dev, unsigned int delay);`
    - 在将来调度执行设备的子系统级挂起回调，其中'delay'是在pm_wq中排队挂起工作项前等待的时间，以毫秒为单位（如果'delay'为零，则立即排队工作项）；成功返回0，设备的PM运行时状态已经是'suspended'返回1，或者如果未安排请求（或者'delay'为0时未排队）则返回错误码；如果`->runtime_suspend()`的执行已经安排并且尚未过期，则新的'delay'值将作为等待时间

  `int pm_request_resume(struct device *dev);`
    - 提交执行设备子系统级恢复回调的请求（该请求由pm_wq中的工作项表示）；成功返回0，设备的运行时PM状态已经是'active'返回1，或者如果没有排队请求则返回错误码

  `void pm_runtime_get_noresume(struct device *dev);`
    - 增加设备的使用计数器

  `int pm_runtime_get(struct device *dev);`
    - 增加设备的使用计数器，运行pm_request_resume(dev)并返回其结果

  `int pm_runtime_get_sync(struct device *dev);`
    - 增加设备的使用计数器，运行pm_runtime_resume(dev)并返回其结果；
      注意，在错误情况下不会减少设备的使用计数器，所以考虑使用pm_runtime_resume_and_get()代替它，特别是如果其返回值被调用者检查的话，这可能会导致更清晰的代码
  `int pm_runtime_get_if_in_use(struct device *dev);`
    - 如果'power.disable_depth'非零返回-EINVAL；否则，如果运行时PM状态是RPM_ACTIVE且运行时PM使用计数器非零，则增加计数器并返回1；否则返回0而不改变计数器

  `int pm_runtime_get_if_active(struct device *dev);`
    - 如果'power.disable_depth'非零返回-EINVAL；否则，如果运行时PM状态是RPM_ACTIVE，则增加计数器并返回1；否则返回0而不改变计数器

  `void pm_runtime_put_noidle(struct device *dev);`
    - 减少设备的使用计数器

  `int pm_runtime_put(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_request_idle(dev)并返回其结果

  `int pm_runtime_put_autosuspend(struct device *dev);`
    - 目前与__pm_runtime_put_autosuspend()相同，但在未来也会调用pm_runtime_mark_last_busy()，不要使用！

  `int __pm_runtime_put_autosuspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_request_autosuspend(dev)并返回其结果

  `int pm_runtime_put_sync(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_idle(dev)并返回其结果

  `int pm_runtime_put_sync_suspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_suspend(dev)并返回其结果

  `int pm_runtime_put_sync_autosuspend(struct device *dev);`
    - 减少设备的使用计数器；如果结果为0，则运行pm_runtime_autosuspend(dev)并返回其结果

  `void pm_runtime_enable(struct device *dev);`
    - 减少设备的'power.disable_depth'字段；如果该字段等于零，则运行时PM辅助函数可以为设备执行子系统级回调（见第2节）

  `int pm_runtime_disable(struct device *dev);`
    - 增加设备的'power.disable_depth'字段（如果该字段之前的值为零，则阻止子系统级运行时PM回调为设备运行），确保设备上所有的待处理运行时PM操作要么完成要么被取消；如果有待处理的恢复请求并且有必要执行设备的子系统级恢复回调来满足该请求，则返回1，否则返回0

  `int pm_runtime_barrier(struct device *dev);`
    - 检查是否有待处理的恢复请求，如果有，则恢复它（同步），取消任何其他的待处理运行时PM请求，并等待所有正在进行的运行时PM操作完成；如果有待处理的恢复请求并且有必要执行设备的子系统级恢复回调来满足该请求，则返回1，否则返回0

  `void pm_suspend_ignore_children(struct device *dev, bool enable);`
    - 设置/取消设置设备的power.ignore_children标志

  `int pm_runtime_set_active(struct device *dev);`
    - 清除设备的'power.runtime_error'标志，将设备的运行时PM状态设置为'active'并根据情况更新其父设备的'active'子设备计数器（只有当'power.runtime_error'设置或'power.disable_depth'大于零时才有效使用此函数）；如果设备有一个不是active的父设备并且该父设备的'power.ignore_children'标志未设置，则会失败并返回错误码

  `void pm_runtime_set_suspended(struct device *dev);`
    - 清除设备的'power.runtime_error'标志，将设备的运行时PM状态设置为'suspended'并根据情况更新其父设备的'active'子设备计数器（只有当'power.runtime_error'设置或'power.disable_depth'大于零时才有效使用此函数）

  `bool pm_runtime_active(struct device *dev);`
    - 如果设备的运行时PM状态是'active'或其'power.disable_depth'字段不等于零，则返回真，否则返回假

  `bool pm_runtime_suspended(struct device *dev);`
    - 如果设备的运行时PM状态是'suspended'且其'power.disable_depth'字段等于零，则返回真，否则返回假

  `bool pm_runtime_status_suspended(struct device *dev);`
    - 如果设备的运行时PM状态是'suspended'返回真

  `void pm_runtime_allow(struct device *dev);`
    - 为设备设置power.runtime_auto标志并减少其使用计数器（由/sys/devices/.../power/control接口使用，有效地允许设备在运行时进行电源管理）

  `void pm_runtime_forbid(struct device *dev);`
    - 为设备取消设置power.runtime_auto标志并增加其使用计数器（由/sys/devices/.../power/control接口使用，有效地防止设备在运行时进行电源管理）

  `void pm_runtime_no_callbacks(struct device *dev);`
    - 为设备设置power.no_callbacks标志并从/sys/devices/.../power删除运行时PM属性（或在设备注册时阻止添加它们）

  `void pm_runtime_irq_safe(struct device *dev);`
    - 为设备设置power.irq_safe标志，导致运行时PM回调在禁用中断的情况下被调用

  `bool pm_runtime_is_irq_safe(struct device *dev);`
    - 如果为设备设置了power.irq_safe标志，导致运行时PM回调在禁用中断的情况下被调用，则返回真

  `void pm_runtime_mark_last_busy(struct device *dev);`
    - 将power.last_busy字段设置为当前时间

  `void pm_runtime_use_autosuspend(struct device *dev);`
    - 设置power.use_autosuspend标志，启用自动挂起延迟；如果该标志先前被清除且power.autosuspend_delay为负，则调用pm_runtime_get_sync

  `void pm_runtime_dont_use_autosuspend(struct device *dev);`
    - 清除power.use_autosuspend标志，禁用自动挂起延迟；如果该标志先前设置且power.autosuspend_delay为负，则减少设备的使用计数器并调用pm_runtime_idle

  `void pm_runtime_set_autosuspend_delay(struct device *dev, int delay);`
    - 将power.autosuspend_delay值设置为'delay'（以毫秒为单位）；如果'delay'为负数，则禁止运行时挂起；如果设置了power.use_autosuspend，可能会调用pm_runtime_get_sync，或者根据power.autosuspend_delay是否从负值变为正值或相反，可能会减少设备的使用计数器并调用pm_runtime_idle；如果未设置power.use_autosuspend，则调用pm_runtime_idle

  `unsigned long pm_runtime_autosuspend_expiration(struct device *dev);`
    - 根据power.last_busy和power.autosuspend_delay计算当前自动挂起延迟周期将何时过期；如果延迟时间为1000毫秒或更多，则过期时间向上舍入到最近的秒；如果延迟周期已经过期或未设置power.use_autosuspend则返回0，否则返回过期时间，以jiffies为单位

可以在中断上下文中安全地执行以下辅助函数：

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
======================================
最初，对于所有设备都禁用了运行时PM，这意味着大多数在第4节中描述的运行时PM辅助函数将在调用pm_runtime_enable()之前为设备返回-EAGAIN
此外，所有设备的初始运行时PM状态是'suspended'，但这不一定反映设备的实际物理状态
因此，如果设备最初是活动的（即它可以处理I/O），则必须在其运行时PM状态变为'active'，借助pm_runtime_set_active()，才能调用pm_runtime_enable()为设备
但是，如果设备有一个父设备且父设备的运行时PM是启用的，那么对于设备调用pm_runtime_set_active()将会影响父设备，除非父设备的'power.ignore_children'标志被设置。也就是说，在这种情况下，只要子设备的状态是'active'，即使子设备的运行时PM仍然禁用（即还没有为子设备调用pm_runtime_enable()，或者已经为子设备调用了pm_runtime_disable()），父设备将无法使用PM核心的辅助函数在运行时进行挂起。出于这个原因，一旦为设备调用了pm_runtime_set_active()，就应该尽快为它调用pm_runtime_enable()，或者借助pm_runtime_set_suspended()将其运行时PM状态变回'suspended'。
如果设备的默认初始运行时PM状态（即'suspended'）反映了设备的实际状态，那么其总线类型或驱动程序的`->probe()`回调可能需要使用PM核心的帮助函数之一（在第4节中描述）来唤醒它。在这种情况下，应使用`pm_runtime_resume()`。当然，为此目的，需要通过调用`pm_runtime_enable()`提前启用设备的运行时PM。

请注意，如果设备可能在`probe`过程中执行运行时PM调用（例如，如果它注册了一个可能回叫的子系统），则配对的`pm_runtime_get_sync()`调用和`pm_runtime_put()`调用将确保设备在`probe`过程中不会再次休眠。这种情况可能发生在诸如网络设备层等系统中。

在`->probe()`完成后，可能希望使设备进入挂起状态。因此，驱动程序核心使用异步`pm_request_idle()`来提交一个请求，在那时为设备执行子系统级别的空闲回调。利用运行时自动挂起功能的驱动程序可能希望在从`->probe()`返回之前更新最后忙碌标记。

此外，驱动程序核心防止运行时PM回调与`__device_release_driver()`中的总线通知回调竞争，这是必要的，因为某些子系统使用通知器来执行影响运行时PM功能的操作。它是通过在`driver_sysfs_remove()`和`BUS_NOTIFY_UNBIND_DRIVER`通知之前调用`pm_runtime_get_sync()`来实现这一点的。这会在设备处于挂起状态时恢复设备，并阻止它在此类例程执行期间再次被挂起。

为了允许总线类型和驱动程序通过在其`->remove()`例程中调用`pm_runtime_suspend()`将设备置于挂起状态，驱动程序核心在`__device_release_driver()`中运行`BUS_NOTIFY_UNBIND_DRIVER`通知后执行`pm_runtime_put_sync()`。这要求总线类型和驱动程序使其`->remove()`回调避免直接与运行时PM竞争，但它也允许在驱动程序移除过程中更灵活地处理设备。

驱动程序应在`->remove()`回调中撤销在`->probe()`中所做的运行时PM更改。通常这意味着调用`pm_runtime_disable()`、`pm_runtime_dont_use_autosuspend()`等。

用户空间可以通过将设备的`/sys/devices/.../power/control`属性值更改为"on"来有效地禁止该设备的驱动程序在运行时进行电源管理，这会导致调用`pm_runtime_forbid()`。原则上，此机制也可由驱动程序用来有效地关闭设备的运行时电源管理，直到用户空间将其打开。

具体来说，在初始化过程中，驱动程序可以确保设备的运行时PM状态为'active'，并调用`pm_runtime_forbid()`。然而，请注意，如果用户空间已故意将`/sys/devices/.../power/control`的值更改为"auto"以允许驱动程序在运行时进行电源管理，驱动程序通过这种方式使用`pm_runtime_forbid()`可能会混淆用户空间。

6. 运行时PM与系统睡眠
=============================

运行时PM与系统睡眠（即，系统挂起和休眠，也称为挂起到RAM和挂起到磁盘）以几种方式相互作用。如果设备在系统睡眠开始时是活动的，一切都很简单。但如果设备已经处于挂起状态会发生什么？

对于运行时PM和系统睡眠，设备可能有不同的唤醒设置。
例如，可能允许在运行时挂起（runtime suspend）中启用远程唤醒功能，但在系统睡眠状态下则不允许（`device_may_wakeup(dev)` 返回 'false'）。当这种情况发生时，子系统级别的系统挂起回调负责更改设备的唤醒设置（它可能会将此任务留给设备驱动程序的系统挂起例程处理）。为了实现这一目标，可能需要先恢复设备然后再将其挂起。如果驱动程序为运行时挂起和系统睡眠使用不同的电源级别或其他设置，则情况也是如此。
在系统恢复过程中，最简单的做法是将所有设备恢复到全功率状态，即使它们在系统挂起开始之前已经被挂起了。这样做的原因有几个，包括：

  * 设备可能需要切换电源级别、唤醒设置等。
  * 远程唤醒事件可能已被固件丢失。
  * 设备的子设备可能需要设备处于全功率状态才能自行恢复。
  * 驱动程序对设备状态的理解可能与设备的实际物理状态不符。这可能会发生在从休眠中恢复的过程中。
  * 可能需要重置设备。
  * 即使设备已被挂起，但如果其使用计数器大于0，则很可能不久后就需要进行运行时恢复。

如果设备在系统挂起开始前已被挂起，并且在恢复过程中被恢复到全功率状态，则必须更新其运行时电源管理（PM）状态以反映实际的系统睡眠后状态。这样做的方法是：

   - `pm_runtime_disable(dev);`
   - `pm_runtime_set_active(dev);`
   - `pm_runtime_enable(dev);`

电源管理核心总是在调用`->suspend()`回调之前增加运行时使用计数器，并在调用`->resume()`回调之后减少它。因此，像这样暂时禁用运行时PM不会导致任何运行时挂起尝试永久丢失。如果在`->resume()`回调返回后使用计数变为零，则会像往常一样调用`->runtime_idle()`回调。
然而，在某些系统上，系统睡眠并非通过全局固件或硬件操作进入。相反，内核以协调的方式直接将所有硬件组件置于低功耗状态。然后，系统睡眠状态实际上是由硬件组件最终所处的状态决定的，并且该系统由硬件中断或完全由内核控制的类似机制唤醒。因此，内核永远不会失去控制，并且它确切地知道所有设备在恢复时的状态。如果存在这种情况，并且上述列出的情况均未发生（特别是如果系统不是从休眠中唤醒），那么将那些在系统挂起开始前已被挂起的设备留在挂起状态可能是更高效的。
为实现这一目标，PM（电源管理）核心提供了一种机制，允许在设备层次结构的不同级别之间进行一定程度的协调。具体来说，如果系统挂起 `.prepare()` 回调函数为某个设备返回一个正数，这表明PM核心该设备似乎处于运行时挂起状态，并且其状态良好，因此可以在所有子设备也保持运行时挂起的情况下让该设备保持在运行时挂起状态。如果发生这种情况，PM核心将不会为这些设备执行任何系统挂起和恢复回调函数，除了 `.complete()` 回调函数，该回调函数则完全负责根据需要处理设备。这仅适用于与休眠无关的系统挂起转换（更多信息请参阅Documentation/driver-api/pm/devices.rst）。
PM核心尽力通过以下操作来减少运行时PM与系统挂起/恢复（以及休眠）回调函数之间的竞争条件的可能性：

  * 在系统挂起过程中，在执行子系统级别的 `.prepare()` 回调函数之前，对每个设备调用 `pm_runtime_get_noresume()`；并且在执行子系统级别的 `.suspend()` 回调函数之前，对每个设备调用 `pm_runtime_barrier()`。此外，在执行子系统级别的 `.suspend_late()` 回调函数之前，PM核心还为每个设备调用 `__pm_runtime_disable()`，其中第二个参数为`false`。
  * 在系统恢复过程中，在执行子系统级别的 `.resume_early()` 回调函数之后，以及在执行子系统级别的 `.complete()` 回调函数之后，为每个设备调用 `pm_runtime_enable()` 和 `pm_runtime_put()`。

7. 通用子系统回调
==============================

子系统可能希望通过使用PM核心提供的通用电源管理回调函数来节省代码空间，这些回调函数定义在`driver/base/power/generic_ops.c`中：

  * `int pm_generic_runtime_suspend(struct device *dev);` - 调用此设备驱动程序提供的`->runtime_suspend()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_runtime_resume(struct device *dev);` - 调用此设备驱动程序提供的`->runtime_resume()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_suspend(struct device *dev);` - 如果设备尚未在运行时挂起，则调用其驱动程序提供的`->suspend()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_suspend_noirq(struct device *dev);` - 如果`pm_runtime_suspended(dev)`返回“false”，则调用设备驱动程序提供的`->suspend_noirq()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_resume(struct device *dev);` - 调用此设备驱动程序提供的`->resume()`回调函数，并在成功后将设备的运行时PM状态更改为“活动”。
  * `int pm_generic_resume_noirq(struct device *dev);` - 调用此设备驱动程序提供的`->resume_noirq()`回调函数。
  * `int pm_generic_freeze(struct device *dev);` - 如果设备尚未在运行时挂起，则调用其驱动程序提供的`->freeze()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_freeze_noirq(struct device *dev);` - 如果`pm_runtime_suspended(dev)`返回“false”，则调用设备驱动程序提供的`->freeze_noirq()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_thaw(struct device *dev);` - 如果设备尚未在运行时挂起，则调用其驱动程序提供的`->thaw()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_thaw_noirq(struct device *dev);` - 如果`pm_runtime_suspended(dev)`返回“false”，则调用设备驱动程序提供的`->thaw_noirq()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_poweroff(struct device *dev);` - 如果设备尚未在运行时挂起，则调用其驱动程序提供的`->poweroff()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_poweroff_noirq(struct device *dev);` - 如果`pm_runtime_suspended(dev)`返回“false”，则调用设备驱动程序提供的`->poweroff_noirq()`回调函数并返回其结果，如果没有定义，则返回0。
  * `int pm_generic_restore(struct device *dev);` - 调用此设备驱动程序提供的`->restore()`回调函数，并在成功后将设备的运行时PM状态更改为“活动”。
  * `int pm_generic_restore_noirq(struct device *dev);` - 调用此设备驱动程序提供的`->restore_noirq()`回调函数。

如果子系统没有为其`->runtime_idle()`、`->runtime_suspend()`、`->runtime_resume()`、`->suspend()`、`->suspend_noirq()`、`->resume()`、`->resume_noirq()`、`->freeze()`、`->freeze_noirq()`、`->thaw()`、`->thaw_noirq()`、`->poweroff()`、`->poweroff_noirq()`、`->restore()`、`->restore_noirq()`在子系统级别的`dev_pm_ops`结构中提供自己的回调函数，则PM核心将使用这些函数作为默认值。
希望使用相同的函数作为系统挂起、冻结、断电和运行时挂起回调函数，以及类似地用于系统恢复、解冻、恢复和运行时恢复的设备驱动程序可以借助在`include/linux/pm.h`中定义的`UNIVERSAL_DEV_PM_OPS`宏来实现这一点（可能将其最后一个参数设置为`NULL`）。

8. “无回调”设备
========================

某些“设备”只是其父设备的逻辑子设备，无法独立进行电源管理。（原型示例是一个USB接口。整个USB设备可以进入低功耗模式或发送唤醒请求，但单个接口不可能做到这一点。）这些设备的驱动程序不需要运行时PM回调函数；如果存在这些回调函数，`->runtime_suspend()`和`->runtime_resume()`总是会返回0而不做其他任何事情，并且`->runtime_idle()`总是会调用`pm_runtime_suspend()`。
子系统可以通过调用`pm_runtime_no_callbacks()`告诉PM核心关于这些设备的信息。这应该在设备结构初始化之后并在注册之前完成（尽管在设备注册之后也可以）。该例程将设置设备的`power.no_callbacks`标志，并防止创建非调试运行时PM sysfs属性。
当设置了`power.no_callbacks`时，PM核心将不会调用`->runtime_idle()`、`->runtime_suspend()`或`->runtime_resume()`回调函数。相反，它将假设挂起和恢复总是成功的，并且空闲设备应被挂起。
因此，PM核心永远不会直接告知设备的子系统或驱动程序有关运行时电源变化的信息。相反，设备的父设备的驱动程序必须负责在父设备的电源状态发生变化时通知设备的驱动程序。
请注意，在某些情况下，子系统或驱动程序可能不希望为它们的设备调用`pm_runtime_no_callbacks()`。这可能是因为需要实现一部分运行时电源管理（PM）回调，或者一个依赖于平台的PM域将被附加到该设备上，又或者设备是通过供应商设备链接进行电源管理的。出于这些原因，并为了避免在子系统或驱动程序中出现大量的模板代码，PM核心允许取消分配运行时PM回调。更确切地说，如果一个回调指针为NULL，PM核心将像存在一个回调并返回0那样处理。

9. 自动延时挂起（Autosuspend）

改变设备的电源状态并非没有成本；它既需要时间也消耗能量。只有当有理由认为设备将在低功耗状态下停留一段时间时，才应将其置于低功耗状态。一种常见的启发式方法是：一段时间未使用的设备很可能仍将保持未使用状态；按照这个建议，驱动程序不应允许设备在达到一定的空闲时间之前进入运行时挂起状态。即使这种启发式方法最终并不总是最优的，但它仍能防止设备在低功耗和全功率状态之间过快地“弹跳”。

“自动延时挂起”（Autosuspend）这一术语是一个历史遗留。它并不意味着设备会自动挂起（子系统或驱动程序仍然需要调用适当的PM例程）；而是意味着运行时挂起将自动延迟直到达到期望的空闲时间。

空闲时间基于`power.last_busy`字段来确定。驱动程序应在执行I/O操作后调用`pm_runtime_mark_last_busy()`以更新此字段，通常是在调用`__pm_runtime_put_autosuspend()`之前。期望的空闲时间长度取决于策略。子系统可以通过调用`pm_runtime_set_autosuspend_delay()`初始设置此长度，但在设备注册之后，此长度应由用户空间控制，使用`/sys/devices/.../power/autosuspend_delay_ms`属性。

为了使用自动延时挂起，子系统或驱动程序必须调用`pm_runtime_use_autosuspend`（最好是在注册设备之前），此后它们应该使用各种`*_autosuspend()`辅助函数而不是非自动延时挂起的对应函数：

- 而不是：`pm_runtime_suspend` 使用：`pm_runtime_autosuspend`
- 而不是：`pm_schedule_suspend` 使用：`pm_request_autosuspend`
- 而不是：`pm_runtime_put` 使用：`__pm_runtime_put_autosuspend`
- 而不是：`pm_runtime_put_sync` 使用：`pm_runtime_put_sync_autosuspend`

驱动程序也可以继续使用非自动延时挂起的辅助函数；它们将正常工作，这意味着有时会考虑自动延时挂起的时间（参见`pm_runtime_idle`）。

在某些情况下，驱动程序或子系统可能希望阻止设备立即自动延时挂起，即使使用计数器为零且自动延时挂起的时间已经过去。如果`->runtime_suspend()`回调返回`-EAGAIN`或`-EBUSY`，并且下一个自动延时挂起的时间在未来（如果回调调用了`pm_runtime_mark_last_busy()`通常是这种情况），PM核心将自动重新安排自动延时挂起。`->runtime_suspend()`回调本身不能执行这种重新安排，因为在设备正在挂起期间（即，当回调正在运行时）不接受任何类型的挂起请求。

该实现在中断上下文中非常适合异步使用。
然而，这样的使用不可避免地涉及到竞态条件，因为PM核心无法同步`->runtime_suspend()`回调与I/O请求的到来。
这段代码示例展示了如何在驱动程序中处理同步问题，使用私有锁来确保数据的一致性和正确性。下面是翻译后的中文版本：

```plaintext
// 这种同步必须由驱动程序处理，使用其私有锁
这里是一个示意性的伪代码示例：

void foo_read_or_write(struct foo_priv *foo, void *data)
{
    lock(&foo->private_lock);
    add_request_to_io_queue(foo, data);
    if (++foo->num_pending_requests == 1)
        pm_runtime_get(&foo->dev);
    if (!foo->is_suspended)
        foo_process_next_request(foo);
    unlock(&foo->private_lock);
}

void foo_io_completion(struct foo_priv *foo, void *req)
{
    lock(&foo->private_lock);
    if (--foo->num_pending_requests == 0) {
        pm_runtime_mark_last_busy(&foo->dev);
        __pm_runtime_put_autosuspend(&foo->dev);
    } else {
        foo_process_next_request(foo);
    }
    unlock(&foo->private_lock);
    /* 将 req 结果返回给用户 ... */
}

int foo_runtime_suspend(struct device *dev)
{
    struct foo_priv *foo = container_of(dev, ...);
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
    struct foo_priv *foo = container_of(dev, ...);

    lock(&foo->private_lock);
    /* ... 恢复设备 ... */
    foo->is_suspended = 0;
    pm_runtime_mark_last_busy(&foo->dev);
    if (foo->num_pending_requests > 0)
        foo_process_next_request(foo);
    unlock(&foo->private_lock);
    return 0;
}

// 关键点是，在 foo_io_completion() 请求自动暂停后，
// foo_runtime_suspend() 回调可能与 foo_read_or_write() 竞争。
// 因此，foo_runtime_suspend() 必须在允许继续暂停之前检查是否有待处理的 I/O 请求（同时持有私有锁）。
此外，power.autosuspend_delay 字段可以随时被用户空间更改。
如果驱动程序关心这一点，它可以在持有其私有锁的情况下，在 ->runtime_suspend() 回调中调用
pm_runtime_autosuspend_expiration()。如果该函数返回非零值，则表示延迟尚未到期，回调应返回 -EAGAIN。
```
```

请注意，以上代码中的 `...` 表示省略的部分，实际实现时需要根据具体需求填写这些部分的内容。
```
