======  
hwpoison  
======  

什么是hwpoison？
=================

未来的Intel CPU支持从某些内存错误（“MCA恢复”）中恢复。这需要操作系统声明一个页面为“有毒”，杀死与之关联的进程，并避免在未来使用它。这个补丁集在虚拟内存管理器（VM）中实现了必要的基础设施。引用概述注释如下：

> 高级机器检查处理器。处理硬件报告的被损坏的页面，通常由于2位ECC内存或缓存故障引起。
>
> 这个机制主要关注后台检测到的被损坏的页面。当当前CPU尝试消费这些损坏时，可以立即将正在运行的进程杀死。这意味着如果因为某种原因无法处理该错误，可以直接忽略它，因为尚未发生任何数据损坏。反之，当这种情况发生时，将触发另一次机器检查。
>
> 处理各种状态下的页面缓存页。这里棘手的部分在于我们可以在异步于其他VM用户的情况下访问任何页面，因为内存故障可能随时、随地发生，可能会违反他们的一些假设。因此，这段代码必须非常谨慎。通常情况下，它会尝试使用正常的锁规则，即获取标准锁，即使这意味着错误处理可能需要花费相当长的时间。
>
> 在这里进行的一些操作相对低效且具有非线性算法复杂度，因为数据结构尚未针对这种情况进行优化。特别是VMA到进程的映射。由于这种情况预计很少出现，我们希望可以容忍这一点。
>
> 这段代码包括mm/memory-failure.c中的高级处理器、一个新的页面有毒标志以及虚拟内存管理器中处理有毒页面的各种检查。
>
> 当前的主要目标是KVM客户机，但它适用于所有类型的应用程序。KVM支持需要较新的QEMU-KVM版本。
>
> 为了KVM用途，需要一种新的信号类型，以便KVM能够将机器检查注入客户机，并带有正确的地址。理论上，这也允许其他应用程序处理内存故障。预期大多数应用程序不会这样做，但一些非常专业化的应用程序可能会这么做。
故障恢复模式
======================

内存故障恢复可以处于两种（实际上是三种）模式中：

`vm.memory_failure_recovery` sysctl 设置为零：
    所有内存故障都会导致系统崩溃。不尝试恢复。

早期终止
    （可全局或按进程控制）
    在检测到错误时立即向应用程序发送 SIGBUS。
    这允许能够以温和方式处理内存错误的应用程序（例如，丢弃受影响的对象）。
    这是 KVM qemu 使用的模式。

晚期终止
    当应用程序访问到损坏页面时发送 SIGBUS。
    这最适合那些不知道内存错误的应用程序，并且是默认模式。
    注意某些页面始终按照晚期终止的方式处理。

用户控制
============

`vm.memory_failure_recovery`
    请参阅 sysctl.txt。

`vm.memory_failure_early_kill`
    全局启用早期终止模式。

`PR_MCE_KILL`
    设置早期/晚期终止模式或恢复系统默认值。

参数1：`PR_MCE_KILL_CLEAR`：
    恢复系统默认值。
参数1：`PR_MCE_KILL_SET`：
    参数2 定义了特定于线程的模式。

    `PR_MCE_KILL_EARLY`：
        早期终止。
    `PR_MCE_KILL_LATE`：
        晚期终止。
    `PR_MCE_KILL_DEFAULT`：
        使用全局系统默认值。

    如果希望有一个专门的线程来代表进程处理 SIGBUS(BUS_MCEERR_AO)，则应在指定的线程上调用 `prctl(PR_MCE_KILL_EARLY)`。否则，SIGBUS 将发送给主线程。

`PR_MCE_KILL_GET`
    返回当前模式。

测试
=======

* 使用 `madvise(MADV_HWPOISON, ...)`（作为 root 用户）- 在进程中注入错误页面进行测试。

* 通过 debugfs `/sys/kernel/debug/hwpoison/` 中的 hwpoison-inject 模块

  `corrupt-pfn`
    在写入此文件的 PFN 处注入 hwpoison 错误。这进行了一些早期过滤，以避免在测试套件中意外地损坏页面。
  `unpoison-pfn`
    软件取消写入此文件的 PFN 处的 hwpoison。这样页面可以再次被使用。这仅适用于 Linux 注入的故障，而不适用于真实的内存故障。一旦发生任何硬件内存故障，此功能将被禁用。

注意这些注入接口在不同内核版本间可能会改变。

  `corrupt-filter-dev-major`, `corrupt-filter-dev-minor`
    只处理与由块设备主次号定义的文件系统相关的页面。-1U 是通配符值。这应仅用于带有模拟注入的测试。
  `corrupt-filter-memcg`
    限制注入到属于 memgroup 的页面。通过 memcg 的inode号指定。
示例：
```
    mkdir /sys/fs/cgroup/mem/hwpoison

    usemem -m 100 -s 1000 &
    echo `jobs -p` > /sys/fs/cgroup/mem/hwpoison/tasks

    memcg_ino=$(ls -id /sys/fs/cgroup/mem/hwpoison | cut -f1 -d' ')
    echo $memcg_ino > /debug/hwpoison/corrupt-filter-memcg

    page-types -p `pidof init`   --hwpoison  # 不应有任何操作
    page-types -p `pidof usemem` --hwpoison  # 毒害其页面
```

  `corrupt-filter-flags-mask`, `corrupt-filter-flags-value`
    当指定了掩码和值时，只有当 `(page_flags & mask) == value` 时才毒害页面。这允许对多种类型的页面进行压力测试。页面标志与 `/proc/kpageflags` 中的一致。标志位定义在 `include/linux/kernel-page-flags.h` 中，并在 `Documentation/admin-guide/mm/pagemap.rst` 中进行了说明。

* 架构特定的 MCE 注入器

  x86 有 `mce-inject` 和 `mce-test`。

  `mce-test` 中有一些可移植的 hwpoison 测试程序，详见以下内容。
参考资料
==========

http://halobates.de/mce-lc09-2.pdf  
LinuxCon 09 的概述演示文稿

git://git.kernel.org/pub/scm/utils/cpu/mce/mce-test.git  
测试套件（tsrc 中包含特定于 hwpoison 的可移植测试）

git://git.kernel.org/pub/scm/utils/cpu/mce/mce-inject.git  
特定于 x86 的注入器

限制
===========
- 并非所有页面类型都受支持，而且将来也不会支持。大多数内核内部对象无法恢复，目前仅支持 LRU 页面
---
Andi Kleen, 2009年10月
