```SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

=============================
挂起/休眠通知器
=============================

:版权所有: |copy| 2016 Intel 公司

:作者: Rafael J. Wysocki <rafael.j.wysocki@intel.com>


有一些操作，子系统或驱动程序可能希望在休眠/挂起之前或恢复/恢复之后执行，但这些操作需要系统完全功能正常，因此驱动程序和子系统的 `->suspend()` 和 `->resume()` 或甚至 `->prepare()` 和 `->complete()` 回调不适合此目的。例如，设备驱动程序可能希望在恢复/恢复后上传固件到它们的设备，但它们不能通过从其 `->resume()` 或 `->complete()` 回调例程中调用 :c:func:`request_firmware()` 来实现（此时用户空间进程已被冻结）。解决方案可能是，在进程被冻结前将固件加载到内存中，并从那里在 `->resume()` 常规中上传。可以使用挂起/休眠通知器来实现这一点。有此类需求的子系统或驱动程序可以注册挂起通知器，这些通知器会在以下事件发生时由电源管理(PM)核心调用：

``PM_HIBERNATION_PREPARE``
    系统即将进入休眠状态，任务将立即被冻结。这与下面的 `PM_SUSPEND_PREPARE` 不同，因为在这种情况下，在通知器和“冻结”过渡的 PM 回调被调用之间会进行额外的工作。
``PM_POST_HIBERNATION``
    系统内存状态已从休眠映像恢复或休眠期间发生了错误。设备恢复回调已被执行并且任务已被解冻。
``PM_RESTORE_PREPARE``
    系统即将恢复一个休眠映像。如果一切顺利，恢复的映像内核将发出 `PM_POST_HIBERNATION` 通知。
``PM_POST_RESTORE``
    在从休眠恢复过程中发生了错误。设备恢复回调已被执行并且任务已被解冻。
``PM_SUSPEND_PREPARE``
    系统正在准备挂起。
``PM_POST_SUSPEND``
    系统刚刚恢复或挂起期间发生了错误。设备恢复回调已被执行并且任务已被解冻。

通常假设，无论通知器为 `PM_HIBERNATION_PREPARE` 执行什么操作，都应在 `PM_POST_HIBERNATION` 中撤销。类似地，为 `PM_SUSPEND_PREPARE` 执行的操作应在 `PM_POST_SUSPEND` 中逆转。
```
此外，如果对于 `PM_HIBERNATION_PREPARE` 或 `PM_SUSPEND_PREPARE` 事件中的任何一个通知器失败，那么已经成功处理该事件的通知器将会被调用以处理 `PM_POST_HIBERNATION` 或 `PM_POST_SUSPEND`。

休眠和挂起通知器是在持有 :c:data:`pm_mutex` 锁的情况下被调用的。
它们按照常规方式定义，但其最后一个参数是无意义的（它总是 NULL）。

要注册和/或注销一个挂起通知器，请使用 :c:func:`register_pm_notifier()` 和 :c:func:`unregister_pm_notifier()` 函数（这两个函数都在 :file:`include/linux/suspend.h` 中定义）。如果你不需要注销通知器，也可以使用在 :file:`include/linux/suspend.h` 中定义的 :c:func:`pm_notifier()` 宏。
