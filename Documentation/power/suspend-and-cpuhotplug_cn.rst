标题：挂起代码（S3）与CPU热插拔基础设施的交互

（C）2011 - 2014 Srivatsa S. Bhat <srivatsa.bhat@linux.vnet.ibm.com>

一、CPU热插拔与挂起到RAM之间的差异

常规的CPU热插拔代码与挂起到RAM基础设施内部使用它的方式有何不同？它们在何处共享通用代码？

好吧，一张图胜过千言万语……所以接下来是ASCII艺术图示：）

[此图描绘了内核中当前的设计，并仅专注于涉及冷冻器和CPU热插拔的交互，同时也试图解释所涉及的锁定机制。它概述了参与的通知过程。
但请注意，在这里，仅展示了调用路径，旨在描述它们在何处采取不同的路径以及在何处共享代码。
当常规的CPU热插拔和挂起到RAM相互竞争时的情况并未在此图中描绘。]

在高层次上，挂起-恢复周期如下所示：

|冷冻任务| -> |禁用非引导CPU| -> |执行挂起| -> |启用非引导CPU| -> |解冻任务|

更多细节如下：

                                挂起调用路径
                                --------------

                                  写入'mem'到
                                /sys/power/state
                                    sysfs文件
                                        |
                                        v
                               获取system_transition_mutex锁
                                        |
                                        v
                             发送PM_SUSPEND_PREPARE
                                   通知
                                        |
                                        v
                                   冻结任务
                                        |
                                        |
                                        v
                              freeze_secondary_cpus()
                                   /* 开始 */
                                        |
                                        v
                            获取cpu_add_remove_lock
                                        |
                                        v
                             遍历当前
                                   在线的CPU
                                        |
                                        |
                                        |                ----------
                                        v                          | L
             ======>               _cpu_down()                     |
            |              [这会在关闭CPU前获取cpuhotplug.lock             |
  共享    |               并在完成后释放]             |
   代码     |            在此过程中，当显著事件发生时，          |
            |            通过运行所有注册的回调发送通知。      |
             ======>     |                          | O
                                        |                          |
                                        |                          |
                                        v                          |
                            记录这些CPU在                | O
                                frozen_cpus掩码         ----------
                                        |
                                        v
                           禁用常规CPU热插拔
                        通过增加cpu_hotplug_disabled
                                        |
                                        v
                            释放cpu_add_remove_lock
                                        |
                                        v
                       /* freeze_secondary_cpus()完成 */
                                        |
                                        v
                                   执行挂起


恢复回来的过程类似，对应的操作（按照恢复期间的执行顺序）包括：

* thaw_secondary_cpus()，其中包括：
   |  获取cpu_add_remove_lock
   |  减少cpu_hotplug_disabled，从而启用常规CPU热插拔
   |  调用_cpu_up() [对于frozen_cpus掩码中的所有CPU，循环调用]
   |  释放cpu_add_remove_lock
   v

* 解冻任务
* 发送PM_POST_SUSPEND通知
* 释放system_transition_mutex锁

值得注意的是，system_transition_mutex锁在我们刚开始挂起时即被获取，并且只有在完整周期（即挂起+恢复）结束后才被释放。

常规CPU热插拔的调用路径同样如此：

                                常规CPU热插拔调用路径
                                ----------------------------

                                写入0（或1）到
                       /sys/devices/system/cpu/cpu*/online
                                    sysfs文件
                                        |
                                        |
                                        v
                                    cpu_down()
                                        |
                                        v
                           获取cpu_add_remove_lock
                                        |
                                        v
                          如果cpu_hotplug_disabled > 0
                                优雅地返回
                                        |
                                        |
                                        v
             ======>                _cpu_down()
            |              [这会在关闭CPU前获取cpuhotplug.lock
  共享    |               并在完成后释放]
   代码     |            在此过程中，当显著事件发生时，
            |            通过运行所有注册的回调发送通知。
             ======>    |
|
                                        |
                                        v
                          释放cpu_add_remove_lock
                               [就这样！对于
                              常规CPU热插拔]

从两个图中可以看出（标记为“共享代码”的部分），常规CPU热插拔和挂起代码路径在_cpu_down()和_cpu_up()函数处汇合。它们在传递给这些函数的参数上有所不同，在常规CPU热插拔期间，为'tasks_frozen'参数传递0。但在挂起期间，由于在非引导CPU下线或上线时任务已经冻结，因此以'tasks_frozen'参数设置为1调用_cpu_*()函数。

重要文件和函数/入口点：
-------------------------------------------
- kernel/power/process.c : freeze_processes(), thaw_processes()
- kernel/power/suspend.c : suspend_prepare(), suspend_enter(), suspend_finish()
- kernel/cpu.c: cpu_[up|down](), _cpu_[up|down](),
  [disable|enable]_nonboot_cpus()

二、CPU热插拔中存在哪些问题？
------------------------------------------------

CPU热插拔和CPU上的微码更新之间存在一些有趣的情况，如下面讨论：

[请记住，内核使用在drivers/base/firmware_loader/main.c中定义的request_firmware()函数从用户空间请求微码映像]

a. 当所有CPU都相同：

   这是最常见的情况，非常直接：我们希望将相同的微码修订版应用到每个CPU上
例如x86，arch/x86/kernel/microcode_core.c中定义的collect_cpu_info()函数有助于发现CPU类型，进而应用正确的微码修订版到它上面
但请注意，内核不会为所有CPU维护一个共同的微码映像，以便处理下面描述的案例'b'
b. 当某些CPU与其他CPU不同时：

   在这种情况下，由于我们可能需要将不同的微码修订版应用于不同的CPU，内核为每个CPU维护正确微码映像的副本（在使用诸如collect_cpu_info()等函数进行适当的CPU类型/模型发现后）。
c. 当一个CPU在物理上热拔除，并且一个新的（可能是不同类型的）CPU被热插拔到系统中：

   在当前内核设计中，每当一个CPU在常规的CPU热插拔操作中下线时，接收到CPU_DEAD通知（由CPU热插拔代码发送），微码更新驱动程序的回调函数会释放内核中该CPU的微码映像副本。
   
   因此，当一个新的CPU上线时，由于内核发现它没有微码映像，它会重新进行CPU类型/模型的发现，然后向用户空间请求适用于该CPU的适当微码映像，随后将该映像应用到CPU上。
   
   例如，在x86架构中，mc_cpu_callback()函数（即注册用于CPU热插拔事件的微码更新驱动程序的回调函数）调用microcode_update_cpu()，在这种情况下，它会调用microcode_init_cpu()，而不是在发现内核没有有效微码映像时调用microcode_resume_cpu()。这确保了CPU类型/模型的发现和正确的微码被应用到CPU上，从用户空间获取后。

d. 在挂起/休眠期间处理微码更新：

   严格来说，在不涉及物理移除或插入CPU的CPU热插拔操作中，CPU实际上在下线时并未真正关机。它们只是进入了尽可能低的C状态。
   
   因此，在这种情况下，当CPU恢复上线时，没有必要重新应用微码，因为它们在CPU下线操作中不会丢失微码映像。
   
   这是在挂起后恢复时通常遇到的情况。然而，在休眠的情况下，由于所有CPU完全关机，在恢复时有必要将微码映像应用于所有CPU。
   
   [我们并不期望有人会在挂起-恢复或休眠/恢复周期之间物理地拔出节点并插入具有不同类型CPU的节点。]

   然而，在当前内核设计中，作为挂起/休眠周期的一部分（cpuhp_tasks_frozen被设置），内核中现有的微码映像副本不会被释放。
   
   并且在CPU上线操作期间（在恢复/重启时），由于内核发现它已经为所有CPU拥有微码映像的副本，它仅将这些映像应用到CPU上，避免了任何CPU类型/模型的重新发现，以及验证微码版本是否适合CPU的需要（基于上述假设，即在挂起/恢复或休眠/恢复周期之间不会执行物理CPU热插拔）。

III. 已知问题
=============

在常规CPU热插拔和挂起相互竞争时，是否存在已知的问题？

是的，以下列出了这些问题：

1. 在调用常规CPU热插拔时，传递给_cpu_down()和_cpu_up()函数的'tasks_frozen'参数总是0。
这可能无法反映系统的真实当前状态，因为任务可能已被带外事件（如正在进行的挂起操作）冻结。因此，cpuhp_tasks_frozen 变量将不会反映出被冻结的状态，并且评估该变量的 CPU 热插拔回调可能会执行错误的代码路径。
1. 如果常规的 CPU 热插拔压力测试恰好与冷冻器发生竞争，原因是在同一时间正在进行挂起操作，那么我们可能会遇到以下情况：

    * 常规的 CPU 在线操作继续从用户空间进入内核的过程，因为冻结尚未开始。
* 接着，冷冻器开始工作并冻结用户空间。
* 如果 CPU 在线操作此时还未完成微码更新，它现在将开始在 TASK_UNINTERRUPTIBLE 状态下等待被冻结的用户空间，以获取微码图像。
* 此时，冷冻器继续尝试冻结剩余的任务。但由于上述提到的等待，冷冻器将无法冻结 CPU 在线热插拔任务，从而导致任务冻结失败。
由于这次任务冻结失败，挂起操作被中止。
