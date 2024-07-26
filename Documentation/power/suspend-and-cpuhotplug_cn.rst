### 暂停代码（S3）与CPU热插拔基础设施的交互

**版权所有 © 2011 - 2014 Srivatsa S. Bhat <srivatsa.bhat@linux.vnet.ibm.com>**

#### I. CPU热插拔与挂起到内存之间的区别

常规的CPU热插拔代码与挂起到内存（Suspend-to-RAM）基础设施内部使用的方式有何不同？它们在哪些地方共享相同的代码？

一张图胜过千言万语……下面是ASCII艺术图示： 

[此图描绘了内核中当前的设计，并仅关注涉及冻结器和CPU热插拔的交互，同时也尝试解释其中涉及的锁。它概述了所涉及的通知过程。但请注意，这里仅展示了调用路径，旨在描述它们在何处分道扬镳、何处共享代码。当常规CPU热插拔与挂起到内存竞合时的情况在此未被描绘。]

从高层次上讲，挂起-恢复周期如下所示：

```
|冻结任务| -> |禁用非启动CPU| -> |执行挂起| -> |启用非启动CPU| -> |解冻任务|
```

更详细的过程如下：

##### 挂起调用路径
```
                                挂起调用路径
                                -----------------
                                  将'mem'写入
                                /sys/power/state
                                    sysfs 文件
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
            |              [此函数在下线CPU之前获取cpuhotplug.lock             |
  共享    |               并在完成后释放]             |
   代码     |               当它执行时，会在发生显著事件时发送通知，       |
            |            通过运行所有已注册的回调函数。      |
             ======>     |
                                        |                          | O
                                        |                          |
                                        |                          |
                                        v                          |
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
```

恢复时的流程类似，对应的步骤（按照恢复时的执行顺序）包括：

* thaw_secondary_cpus()，涉及：
   ```
   |  获取cpu_add_remove_lock
   |  减少cpu_hotplug_disabled，从而启用常规CPU热插拔
   |  调用_cpu_up() [对于frozen_cpus掩码中的所有CPU，在循环中调用]
   |  释放cpu_add_remove_lock
   ```

* 解冻任务
* 发送PM_POST_SUSPEND通知
* 释放system_transition_mutex锁

需要注意的是，system_transition_mutex锁在开始挂起时即被获取，并且只有在整个周期（即挂起+恢复）完成后才被释放。

##### 常规CPU热插拔调用路径
```
                          常规CPU热插拔调用路径
                          -----------------------------

                                将0（或1）写入
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
            |              [此函数在下线CPU之前获取cpuhotplug.lock
  共享    |               并在完成后释放]
   代码     |               当它执行时，会在发生显著事件时发送通知，
            |           通过运行所有已注册的回调函数。
             ======>    |
|
                                        |
                                        v
                          释放cpu_add_remove_lock
                               [这就是全部！对于
                              常规CPU热插拔]
```

如上图所示，常规CPU热插拔与挂起代码路径在_cpu_down()和_cpu_up()函数处会合。它们在传递给这些函数的参数上有差异，在常规CPU热插拔期间，为'tasks_frozen'参数传递0。但在挂起期间，由于任务在非启动CPU离线或上线前已经被冻结，因此调用_cpu_*()函数时将'tasks_frozen'参数设置为1。

**重要文件和函数/入口点：**
- `kernel/power/process.c` : `freeze_processes()`，`thaw_processes()`
- `kernel/power/suspend.c` : `suspend_prepare()`，`suspend_enter()`，`suspend_finish()`
- `kernel/cpu.c`: `cpu_[up|down]()`， `_cpu_[up|down]()`，`[disable|enable]_nonboot_cpus()`


#### II. CPU热插拔涉及的问题

存在一些有趣的情况，涉及到CPU热插拔和CPU上的微码更新，如下讨论：

[请记住，内核使用定义在`drivers/base/firmware_loader/main.c`中的`request_firmware()`函数从用户空间请求微码映像]


a. **当所有的CPU都相同：**

   这是最常见的情况，也是最直接的：我们想要将相同的微码修订版应用于每个CPU。例如，在x86架构中，`arch/x86/kernel/microcode_core.c`中定义的`collect_cpu_info()`函数有助于发现CPU类型，并据此应用正确的微码修订版。但需要注意的是，内核不会为所有CPU维护一个共同的微码映像，以便处理下面情况'b'。

b. **当某些CPU与其他CPU不同：**

   在这种情况下，我们可能需要对不同的CPU应用不同的微码修订版。因此，内核会为每个CPU维护一份正确的微码映像（在适当识别CPU类型/型号后，使用诸如`collect_cpu_info()`等函数）。
### c. 当CPU在物理上热拔除，并且新的（可能是不同类型的）CPU被热插入系统时：

在当前内核设计中，每当一个CPU在常规的CPU热插拔操作中被下线时，接收到CPU_DEAD通知（由CPU热插拔代码发送）后，微码更新驱动程序的回调函数会释放该CPU的微码图像在内核中的副本。
因此，当一个新的CPU上线时，由于内核发现它没有微码图像，就会重新进行CPU类型/型号的检测，并向用户空间请求适用于该CPU的正确微码图像，随后将其应用到CPU上。
例如，在x86架构中，mc_cpu_callback()函数（即注册用于CPU热插拔事件的微码更新驱动程序的回调函数）会调用microcode_update_cpu()函数。在这种情况下，如果内核中没有有效的微码图像，则会调用microcode_init_cpu()函数而不是microcode_resume_cpu()函数。这样可以确保执行CPU类型/型号的检测，并将正确的微码应用于CPU。
### d. 在挂起/休眠期间处理微码更新：

严格来说，在不涉及物理移除或插入CPU的CPU热插拔操作中，CPU在下线时实际上并不会完全断电。它们只是进入可能的最低C状态。
因此，在这种情况下，当CPU重新上线时，没有必要重新应用微码，因为它们在CPU下线操作期间不会丢失微码图像。
这是在从挂起恢复时通常遇到的情况。
然而，在休眠的情况下，所有CPU都会完全断电，所以在恢复时有必要为所有CPU重新应用微码图像。
【请注意，我们不期望有人会在挂起-恢复或休眠-恢复周期之间物理地拔出节点并插入不同类型的CPU。】

然而，在当前内核设计中，在作为挂起/休眠周期一部分的CPU下线操作期间（设置cpuhp_tasks_frozen），内核中现有的微码图像副本不会被释放。
而在CPU上线操作期间（恢复/启动时），由于内核发现它已经拥有所有CPU的微码图像副本，它只需将这些图像应用到CPU上，避免了对CPU类型/型号的任何重新检测以及验证微码修订版本是否适合CPU的需求（基于上述假设，即物理CPU热插拔不会在挂起/恢复或休眠/恢复周期之间进行）。

### III. 已知问题
#### ===============

是否存在已知的问题，当常规的CPU热插拔和挂起相互竞争时？

是的，以下是这些问题：

1. 在调用常规CPU热插拔时，传递给_cpu_down()和_cpu_up()函数的'tasks_frozen'参数总是0。
这可能并不能反映系统的真实当前状态，因为任务可能已被如正在进行的挂起操作之类的外部事件冻结。因此，cpuhp_tasks_frozen 变量将不会反映出被冻结的状态，并且评估该变量的 CPU 热插拔回调可能会执行错误的代码路径。
1. 如果普通的 CPU 热插拔压力测试恰好与冷冻器发生竞态条件，因为同时有一个正在进行的挂起操作，那么我们可能会遇到以下情况：

    * 一个常规的 CPU 在线操作继续从用户空间进入内核的过程，因为冷冻过程尚未开始。
* 接着，冷冻器开始工作并冻结用户空间。
* 如果 CPU 在线操作此时还没有完成微码更新等操作，它现在将开始在 TASK_UNINTERRUPTIBLE 状态下等待被冻结的用户空间，以便获取微码图像。
* 现在冷冻器继续尝试冻结剩余的任务。但由于上述的等待，冷冻器将无法冻结 CPU 在线热插拔任务，从而导致任务冻结失败。
由于这次任务冻结失败，挂起操作被中止。
