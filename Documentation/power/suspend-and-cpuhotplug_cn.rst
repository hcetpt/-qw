### 暂停代码（S3）与CPU热插拔基础设施的交互

(C) 2011 - 2014 Srivatsa S. Bhat <srivatsa.bhat@linux.vnet.ibm.com>

---

#### I. CPU热插拔与挂起到内存之间的区别

常规的CPU热插拔代码与挂起到内存（Suspend-to-RAM）基础设施内部使用的代码有何不同？它们在哪些地方共享相同的代码？

嗯，一张图胜过千言万语……所以接下来是ASCII艺术图：）

[此图展示了内核当前的设计，并且仅关注涉及冻结器和CPU热插拔的交互，同时尝试解释所涉及的锁定机制。它还概述了相关的通知。
请注意，在这里只展示了调用路径，目的是描述它们在何处分叉以及在何处共享代码。
当常规CPU热插拔与挂起到内存相互竞争时的情况在此未展示。]

在高层次上，挂起-恢复周期如下所示：

```
|冻结任务| -> |禁用非启动CPU| -> |执行挂起| -> |启用非启动CPU| -> |解冻任务|
```

更多细节如下：

```
                                 挂起调用路径
                                 -------------

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
                                      遍历当前在线的CPU
                                           |
                                           |                
                                           v                      | L
         ======>               _cpu_down()                         |
        |              [此函数在关闭CPU之前获取cpuhotplug.lock     |
  共享    |               并在完成后释放]                          | O
   代码     |            在此期间，当发生重要事件时发送通知，       |
        |            通过运行所有已注册的回调函数。                 |
         ======>                                                |
                                           |                      | O
                                           |                      |
                                           |                      |
                                           v                      |
                                      记录这些CPU在                | P
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



返回恢复也是类似的，其对应步骤如下（按恢复顺序执行）：

* thaw_secondary_cpus() 包括：
   |  获取cpu_add_remove_lock
   |  减少cpu_hotplug_disabled，从而启用常规CPU热插拔
   |  调用_cpu_up() [对于frozen_cpus掩码中的所有CPU，循环调用]
   |  释放cpu_add_remove_lock
   v

* 解冻任务
* 发送PM_POST_SUSPEND通知
* 释放system_transition_mutex锁

需要注意的是，system_transition_mutex锁在开始挂起时即被获取，并且在整个周期（即挂起+恢复）完成后才释放。
::



                          常规CPU热插拔调用路径
                          -----------------------------

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
                                平稳返回
                                         |
                                         |
                                         v
             ======>                _cpu_down()
            |              [此函数在关闭CPU之前获取cpuhotplug.lock
  共享    |               并在完成后释放]
   代码     |            在此期间，当发生重要事件时发送通知，
            |           通过运行所有已注册的回调函数。
             ======>    
|
                                         |
                                         v
                          释放cpu_add_remove_lock
                               [对于常规CPU热插拔来说，这就完成了！]



从两个图中可以看出（标记为“共享代码”的部分），常规CPU热插拔和挂起代码路径在_cpu_down()和_cpu_up()函数处汇聚。它们在传递给这些函数的参数上有区别，在常规CPU热插拔期间，传递给'tasks_frozen'参数的是0。但在挂起期间，由于在非启动CPU下线或上线时任务已经被冻结，因此调用_cpu_*()函数时将'tasks_frozen'参数设置为1。
[详见下面关于此问题的一些已知问题。]


重要的文件和函数/入口点：
-------------------------------------------
- kernel/power/process.c : freeze_processes(), thaw_processes()
- kernel/power/suspend.c : suspend_prepare(), suspend_enter(), suspend_finish()
- kernel/cpu.c: cpu_[up|down](), _cpu_[up|down](), [disable|enable]_nonboot_cpus()


---

#### II. CPU热插拔存在哪些问题？

涉及CPU热插拔和CPU上的微码更新时存在一些有趣的情况，如下所述：

[请注意，内核使用定义在drivers/base/firmware_loader/main.c中的request_firmware()函数从用户空间请求微码映像]


a. 当所有CPU都相同：

   这是最常见的情况，并且非常直接：我们希望将相同的微码修订版应用于每个CPU。
   以x86为例，定义在arch/x86/kernel/microcode_core.c中的collect_cpu_info()函数有助于发现CPU类型并应用正确的微码修订版。
   但请注意，内核不会为所有CPU维护一个通用的微码映像，以便处理情况'b'。

b. 当某些CPU与其他CPU不同：

   在这种情况下，由于可能需要对不同的CPU应用不同的微码修订版，内核会为每个CPU维护一个正确的微码映像副本（在适当发现CPU类型/型号后，使用如collect_cpu_info()等函数）。
c. 当一个CPU在物理上热拔除，并且一个新的（可能是不同类型）的CPU被热插入到系统中时：

   在当前内核设计中，每当一个CPU在常规的CPU热插拔操作中被下线时，在接收到CPU_DEAD通知（由CPU热插拔代码发送）后，微码更新驱动程序的回调函数会释放该CPU的内核微码副本。
   因此，当新的CPU上线时，由于内核发现它没有微码图像，因此会重新进行CPU类型/型号的检测，并请求用户空间为该CPU提供适当的微码图像，随后将其应用。
   例如，在x86架构中，mc_cpu_callback()函数（即注册用于CPU热插拔事件的微码更新驱动程序的回调）调用microcode_update_cpu()，在这种情况下会调用microcode_init_cpu()而不是microcode_resume_cpu()，当它发现内核没有有效的微码图像时。这确保了在从用户空间获取正确的微码后执行CPU类型/型号检测并将正确的微码应用于CPU。
   
   d. 在挂起/休眠期间处理微码更新：
   
   严格来说，在不涉及物理移除或插入CPU的CPU热插拔操作中，CPU在下线时实际上并不会真正断电。它们只是进入尽可能低的C状态。
   因此，在这种情况下，当CPU重新上线时，没有必要重新应用微码，因为它们在CPU下线操作过程中不会丢失微码图像。
   这是在挂起恢复期间通常遇到的情况。然而，在休眠的情况下，由于所有CPU完全断电，在恢复时需要将微码图像重新应用于所有CPU。
   [请注意，我们不期望有人会在挂起恢复或休眠/恢复周期之间物理地拔出节点并插入不同类型的CPU。]
   
   然而，在当前内核设计中，在作为挂起/休眠周期一部分的CPU下线操作期间（cpuhp_tasks_frozen被设置），内核中的现有微码副本不会被释放。
   并且在CPU上线操作期间（恢复/恢复期间），由于内核发现它已经拥有所有CPU的微码图像副本，因此它只需将它们应用于CPU，避免任何CPU类型/型号的重新检测以及验证微码版本是否正确的需求（基于上述假设，即在挂起/恢复或休眠/恢复周期之间不会进行物理CPU热插拔）。

III. 已知问题
==============
   
   在常规CPU热插拔和挂起相互竞争时是否存在已知问题？

   是的，以下是列出的问题：

   1. 在调用常规CPU热插拔时，传递给_cpu_down()和_cpu_up()函数的'tasks_frozen'参数始终为0。
这可能无法反映系统的真实当前状态，因为任务可能已经被一个带外事件（例如正在进行的挂起操作）冻结。因此，cpuhp_tasks_frozen 变量将不会反映出被冻结的状态，并且评估该变量的 CPU 热插拔回调可能会执行错误的代码路径。

2. 如果在有挂起操作同时进行时，常规的 CPU 热插拔压力测试与冻结器发生竞争，那么我们可能会遇到以下情况：

- 常规的 CPU 在线操作继续从用户空间进入内核，因为冻结尚未开始。
- 接着，冻结器开始工作并冻结用户空间。
- 如果 CPU 在线操作此时还未完成微码更新，则它现在将在 TASK_UNINTERRUPTIBLE 状态下等待被冻结的用户空间，以获取微码映像。
- 现在冻结器继续尝试冻结剩余的任务。但由于上述等待的存在，冻结器将无法冻结 CPU 在线热插拔任务，从而导致任务冻结失败。
- 由于这一任务冻结失败，挂起操作会被中止。
