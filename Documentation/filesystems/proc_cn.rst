.. SPDX 许可声明标识符: GPL-2.0

====================
/proc 文件系统
====================

=====================  =======================================  ================
/proc/sys              Terrehon Bowden <terrehon@pacbell.net>,  1999年10月7日
                       Bodo Bauer <bb@ricochet.net>
2.4.x 更新           Jorge Nerin <comandante@zaralinux.com>   2000年11月14日
移动 /proc/sys         Shen Feng <shen@cn.fujitsu.com>          2009年4月1日
修复/更新 1.1部分      Stefani Seibold <stefani@seibold.net>    2009年6月9日
=====================  =======================================  ================


.. 目录

  0     序言
  0.1	简介/致谢
  0.2	法律声明

  1	收集系统信息
  1.1	特定于进程的子目录
  1.2	内核数据
  1.3	/proc/ide 中的 IDE 设备
  1.4	/proc/net 中的网络信息
  1.5	SCSI 信息
  1.6	/proc/parport 中的并口信息
  1.7	/proc/tty 中的 TTY 信息
  1.8	/proc/stat 中的杂项内核统计信息
  1.9	Ext4 文件系统参数

  2	修改系统参数

  3	每个进程的参数
  3.1	/proc/<pid>/oom_adj & /proc/<pid>/oom_score_adj - 调整 oom-killer 的评分
  3.2	/proc/<pid>/oom_score - 显示当前 oom-killer 的评分
  3.3	/proc/<pid>/io - 显示 I/O 统计字段
  3.4	/proc/<pid>/coredump_filter - 核心转储过滤设置
  3.5	/proc/<pid>/mountinfo - 挂载信息
  3.6	/proc/<pid>/comm  & /proc/<pid>/task/<tid>/comm
  3.7   /proc/<pid>/task/<tid>/children - 任务子任务信息
  3.8   /proc/<pid>/fdinfo/<fd> - 打开文件的信息
  3.9   /proc/<pid>/map_files - 内存映射文件的信息
  3.10  /proc/<pid>/timerslack_ns - 任务的 timerslack 值
  3.11	/proc/<pid>/patch_state - 实时补丁操作状态
  3.12	/proc/<pid>/arch_status - 任务架构特定信息
  3.13  /proc/<pid>/fd - 打开文件的符号链接列表

  4	配置 procfs
  4.1	挂载选项

  5	文件系统行为

序言
=======

0.1 简介/致谢
------------------------

本文档是即将（或希望如此）发布的关于 SuSE Linux 发行版的一本书的一部分。由于 /proc 文件系统没有完整的文档，我们在编写这些章节时使用了许多自由可用的资源，因此我们认为将这份工作回馈给 Linux 社区是公平的。这份工作基于 2.2.* 内核版本，并且即将推出的 2.4.* 版本。遗憾的是它仍然不完整，但我们希望它会有所帮助。据我们所知，这是第一份关于 /proc 文件系统的“一站式”文档。它专注于 Intel x86 硬件，因此如果你在寻找 PPC、ARM、SPARC、AXP 等特性，你可能不会找到你需要的内容。它也只涵盖了 IPv4 网络，不包括 IPv6 以及其他协议——抱歉。但是欢迎添加和打补丁，并且如果发送给我们的话，我们将把它们添加到这个文档中。
我们想感谢 Alan Cox、Rik van Riel 和 Alexey Kuznetsov 以及许多其他人为编译这份文档提供的帮助。我们还想特别感谢 Andi Kleen 提供的文档，我们在此文档中大量依赖了他的文档，以及他提供的额外信息。感谢所有为 Linux 内核贡献源代码或文档的人，帮助创建了这样一个优秀的软件……:)
如果您有任何评论、更正或补充，请不要犹豫，联系 Bodo Bauer 至 bb@ricochet.net。我们将很高兴将其添加到此文档中。
此文档的最新版本可在线获取：https://www.kernel.org/doc/html/latest/filesystems/proc.html

如果上述链接无法访问，您可以尝试联系内核邮件列表至 linux-kernel@vger.kernel.org 或者尝试联系我至 comandante@zaralinux.com
0.2 法律声明
---------------

我们不对本文档的正确性做出保证，如果您因为错误的文档而抱怨您的系统出了问题，我们不会承担责任。
第一章：收集系统信息
========================================

本章内容
---------------
* 探讨 /proc 这个伪文件系统及其提供运行中的 Linux 系统信息的能力
* 考察 /proc 的结构
* 揭示有关内核和正在系统上运行的进程的各种信息

------------------------------------------------------------------------------

/proc 文件系统作为内核内部数据结构的一个接口。它可以用来获取有关系统的数据，并在运行时更改某些内核参数（sysctl）。
首先，我们将查看 /proc 中只读的部分。在第二章中，我们将向您展示如何使用 /proc/sys 来更改设置。
1.1 特定于进程的子目录
-----------------------------------

/proc 目录包含（除其他外）系统上每个进程的一个子目录，该子目录以进程ID（PID）命名
链接 'self' 指向读取文件系统的进程。每个进程子目录包含表 1-1 中列出的条目。

注意，打开的 `/proc/<pid>` 或其任何文件或子目录的文件描述符不会阻止 `<pid>` 在该进程退出后被其他进程复用。对已退出进程的打开的 `/proc/<pid>` 文件描述符执行的操作不会作用于内核可能通过随机分配给 `<pid>` 的任何新进程。相反，这些文件描述符上的操作通常会以 `ESRCH` 错误失败。

.. table:: 表 1-1：/proc 中特定于进程的条目

 =============  ===============================================================
 File		Content
 =============  ===============================================================
 clear_refs	清除在 smaps 输出中显示的引用页面位
 cmdline	命令行参数
 cpu	当前和上次执行的 CPU（2.4）（SMP）
 cwd	指向当前工作目录的链接
 environ	环境变量值
 exe	指向此进程可执行文件的链接
 fd	包含所有文件描述符的目录
 maps	到可执行文件和库文件的内存映射（2.4）
 mem	此进程占用的内存
 root	指向此进程根目录的链接
 stat	进程状态
 statm	进程内存状态信息
 status	以人类可读的形式表示的进程状态
 wchan	当 CONFIG_KALLSYMS=y 时存在：它显示进程阻塞在哪个内核函数符号中——或者如果没有阻塞则为 "0"
 pagemap	页表
 stack	报告完整的堆栈跟踪，启用 CONFIG_STACKTRACE 配置
 smaps	基于 maps 的扩展，显示每个映射的内存消耗及其关联的标志
 smaps_rollup	进程所有映射累积的 smaps 统计数据。这可以从 smaps 导出，但更快且更方便
 numa_maps	基于 maps 的扩展，显示每个映射的内存局部性和绑定策略以及内存使用量（按页计算）
 =============  ==============================================================

例如，要获取进程的状态信息，只需读取 `/proc/PID/status` 文件：

```
> cat /proc/self/status
Name:   cat
State:  R (running)
Tgid:   5452
Pid:    5452
PPid:   743
TracerPid:      0					(2.4)
Uid:    501     501     501     501
Gid:    100     100     100     100
FDSize: 256
Groups: 100 14 16
Kthread:    0
VmPeak:     5004 kB
VmSize:     5004 kB
VmLck:         0 kB
VmHWM:       476 kB
VmRSS:       476 kB
RssAnon:             352 kB
RssFile:             120 kB
RssShmem:              4 kB
VmData:      156 kB
VmStk:        88 kB
VmExe:        68 kB
VmLib:      1412 kB
VmPTE:        20 kb
VmSwap:        0 kB
HugetlbPages:          0 kB
CoreDumping:    0
THP_enabled:	  1
Threads:        1
SigQ:   0/28578
SigPnd: 0000000000000000
ShdPnd: 0000000000000000
SigBlk: 0000000000000000
SigIgn: 0000000000000000
SigCgt: 0000000000000000
CapInh: 00000000fffffeff
CapPrm: 0000000000000000
CapEff: 0000000000000000
CapBnd: ffffffffffffffff
CapAmb: 0000000000000000
NoNewPrivs:     0
Seccomp:        0
Speculation_Store_Bypass:       thread vulnerable
SpeculationIndirectBranch:      conditional enabled
voluntary_ctxt_switches:        0
nonvoluntary_ctxt_switches:     1
```

这几乎与使用 `ps` 命令查看的信息相同。实际上，`ps` 使用 `proc` 文件系统来获取信息。但是，通过读取 `/proc/PID/status` 文件可以获得更详细的进程视图。其字段在表 1-2 中进行了说明。

`statm` 文件包含有关进程内存使用的更详细信息。其七个字段在表 1-3 中进行了解释。`stat` 文件包含有关进程本身的详细信息。其字段在表 1-4 中进行了解释（对于 SMP CONFIG 用户）。

为了使账务处理具有可扩展性，与 RSS 相关的信息以异步方式处理，因此其值可能不太准确。要查看某个时刻的精确快照，可以查看 `/proc/<pid>/smaps` 文件并扫描页表。虽然这样做较慢，但非常精确。

.. table:: 表 1-2：状态字段的内容（截至 4.19）

 ==========================  ===================================================
 Field                       Content
 ==========================  ===================================================
 Name                        可执行文件名
 Umask                       文件模式创建掩码
 State                       状态（R 表示运行中，S 表示休眠，D 表示不可中断等待，Z 表示僵尸，T 表示被追踪或停止）
 Tgid                        线程组 ID
 Ngid                        NUMA 组 ID（无则为 0）
 Pid                         进程 ID
 PPid                        父进程的进程 ID
 TracerPid                   追踪此进程的进程的 PID（如果没有，或追踪器位于当前 PID 命名空间之外，则为 0）
 Uid                         实际、有效、保存集和文件系统 UID
 Gid                         实际、有效、保存集和文件系统 GID
 FDSize                      当前分配的文件描述符槽的数量
 Groups                      辅助组列表
 NStgid                      后代命名空间线程组 ID 层次结构
 NSpid                       后代命名空间进程 ID 层次结构
 NSpgid                      后代命名空间进程组 ID 层次结构
 NSsid                       后代命名空间会话 ID 层次结构
 Kthread                     内核线程标志，1 表示是，0 表示否
 VmPeak                      虚拟内存峰值大小
 VmSize                      总程序大小
 VmLck                       锁定内存大小
 VmPin                       固定内存大小
 VmHWM                       居民集大小峰值（“高水位”）
 VmRSS                       内存部分大小。它包含以下三个部分（VmRSS = RssAnon + RssFile + RssShmem）
 RssAnon                     居民匿名内存大小
 RssFile                     居民文件映射大小
 RssShmem                    居民共享内存大小（包括 SysV shm、tmpfs 映射和共享匿名映射）
 VmData                      私有数据段大小
 VmStk                       栈段大小
 VmExe                       文本段大小
 VmLib                       共享库代码大小
 VmPTE                       页表项大小
 VmSwap                      用于匿名私有数据的交换使用量（不包括共享内存交换使用量）
 HugetlbPages                巨型页内存部分大小
 CoreDumping                 此进程的内存正在被转储（杀死进程可能导致核心转储损坏）
 THP_enabled                 此进程允许使用 THP（如果设置了 PR_SET_THP_DISABLE，则返回 0）
 Threads                     线程数量
 SigQ                        排队信号数/最大排队数
 SigPnd                      线程待处理信号位图
 ShdPnd                      进程共享待处理信号位图
 SigBlk                      被阻塞信号位图
 SigIgn                      被忽略信号位图
 SigCgt                      被捕获信号位图
 CapInh                      可继承能力位图
 CapPrm                      允许的能力位图
 CapEff                      有效能力位图
 CapBnd                      能力边界集位图
 CapAmb                      环境能力位图
 NoNewPrivs                  no_new_privs，如 prctl(PR_GET_NO_NEW_PRIV, ...)
 Seccomp                     seccomp 模式，如 prctl(PR_GET_SECCOMP, ...)
 Speculation_Store_Bypass    投机存储绕过缓解状态
 SpeculationIndirectBranch   间接分支推测模式
 Cpus_allowed                此进程可以在其上运行的 CPU 集合掩码
 Cpus_allowed_list           同上，但在“列表格式”
 Mems_allowed                此进程可以访问的内存节点集合掩码
 Mems_allowed_list           同上，但在“列表格式”
 voluntary_ctxt_switches     自愿上下文切换次数
 nonvoluntary_ctxt_switches  非自愿上下文切换次数
 ==========================  ===================================================

.. table:: 表 1-3：statm 字段的内容（截至 2.6.8-rc3）

 ======== ===============================	==============================
 Field    Content
 ======== ===============================	==============================
 size     总程序大小（按页计算）		（与 status 中的 VmSize 相同）
 resident 居民内存部分大小（按页计算）	（与 status 中的 VmRSS 相同）
 shared   共享页数量		（即由文件支持的，与 status 中的 RssFile+RssShmem 相同）
 trs      代码页数量		（不包括库；已损坏，包括数据段）
 lrs      库页数量		（在 2.6 上始终为 0）
 drs      数据/栈页数量		（包括库；已损坏，包括库文本）
 dt       脏页数量		（在 2.6 上始终为 0）
 ======== ===============================	==============================

.. table:: 表 1-4：stat 字段的内容（截至 2.6.30-rc7）

  ============= ===============================================================
  Field         Content
  ============= ===============================================================
  pid           进程 ID
  tcomm         可执行文件名
  state         状态（R 表示运行中，S 表示休眠，D 表示不可中断等待，Z 表示僵尸，T 表示被追踪或停止）
  ppid          父进程的进程 ID
  pgrp          进程的进程组
  sid           会话 ID
  tty_nr        进程使用的终端
  tty_pgrp      终端的进程组
  flags         任务标志
  min_flt       次级错误数
  cmin_flt      子进程的次级错误数
  maj_flt       主错误数
  cmaj_flt      子进程的主错误数
  utime         用户模式时间片
  stime         内核模式时间片
  cutime        子进程的用户模式时间片
  cstime        子进程的内核模式时间片
  priority      优先级
  nice          优先级调整级别
  num_threads   线程数
  it_real_value	（已废弃，始终为 0）
  start_time    系统启动后进程开始的时间
  vsize         虚拟内存大小
  rss           居民集内存大小
  rsslim        当前居民集的字节限制
  start_code    程序文本可以运行的地址之上
  end_code      程序文本可以运行的地址之下
  start_stack   主进程栈的起始地址
  esp           ESP 的当前值
  eip           EIP 的当前值
  pending       待处理信号位图
  blocked       被阻塞信号位图
  sigign        被忽略信号位图
  sigcatch      被捕获信号位图
  0		（占位符，曾经是 wchan 地址，使用 /proc/PID/wchan 替代）
  0             （占位符）
  0             （占位符）
  exit_signal   退出时发送给父线程的信号
  task_cpu      任务调度所在的 CPU
  rt_priority   实时优先级
  policy        调度策略（参阅 sched_setscheduler 手册页）
  blkio_ticks   等待块 I/O 的时间
  gtime         任务的虚拟机时间
  cgtime        任务子进程的虚拟机时间
  start_data    程序数据+bss 的地址之上
  end_data      程序数据+bss 的地址之下
  start_brk     程序堆可以用 brk() 扩展的地址之上
  arg_start     程序命令行的地址之上
  arg_end       程序命令行的地址之下
  env_start     程序环境变量的地址之上
  env_end       程序环境变量的地址之下
  exit_code     线程的退出码，以 waitpid 系统调用的形式报告
  ============= ===============================================================

`/proc/PID/maps` 文件包含当前映射的内存区域及其访问权限。
其格式如下：

```
address           perms offset  dev   inode      pathname

08048000-08049000 r-xp 00000000 03:00 8312       /opt/test
08049000-0804a000 rw-p 00001000 03:00 8312       /opt/test
0804a000-0806b000 rw-p 00000000 00:00 0          [heap]
a7cb1000-a7cb2000 ---p 00000000 00:00 0
a7cb2000-a7eb2000 rw-p 00000000 00:00 0
a7eb2000-a7eb3000 ---p 00000000 00:00 0
a7eb3000-a7ed5000 rw-p 00000000 00:00 0
a7ed5000-a8008000 r-xp 00000000 03:00 4222       /lib/libc.so.6
a8008000-a800a000 r--p 00133000 03:00 4222       /lib/libc.so.6
a800a000-a800b000 rw-p 00135000 03:00 4222       /lib/libc.so.6
a800b000-a800e000 rw-p 00000000 00:00 0
a800e000-a8022000 r-xp 00000000 03:00 14462      /lib/libpthread.so.0
a8022000-a8023000 r--p 00013000 03:00 14462      /lib/libpthread.so.0
a8023000-a8024000 rw-p 00014000 03:00 14462      /lib/libpthread.so.0
a8024000-a8027000 rw-p 00000000 00:00 0
a8027000-a8043000 r-xp 00000000 03:00 8317       /lib/ld-linux.so.2
a8043000-a8044000 r--p 0001b000 03:00 8317       /lib/ld-linux.so.2
a8044000-a8045000 rw-p 0001c000 03:00 8317       /lib/ld-linux.so.2
aff35000-aff4a000 rw-p 00000000 00:00 0          [stack]
fffce000-fffff000 r-xp 00000000 00:00 0          [vdso]
```

其中 "address" 是进程占用的地址空间，"perms" 是一组权限：

r = 可读
w = 可写
x = 可执行
s = 共享
p = 私有（写时复制）

"offset" 是映射中的偏移量，"dev" 是设备（主:次），而 "inode" 是该设备上的 inode。0 表示没有 inode 与此内存区域相关联，如 BSS（未初始化的数据）。
"pathname" 显示了与此映射相关联的文件名。如果映射未与任何文件关联：

 ===================        ===========================================
 [heap]                     程序的堆
 [stack]                    主进程的栈
 [vdso]                     “虚拟动态共享对象”，内核系统调用处理器
 [anon:<name>]              用户空间命名的私有匿名映射
 [anon_shmem:<name>]        用户空间命名的匿名共享内存映射
 ===================        ===========================================

或者如果为空，则映射是匿名的。
`/proc/PID/smaps` 是基于 `maps` 的扩展，显示每个进程映射的内存消耗情况。对于每个映射（即虚拟内存区或VMA），有一系列行，如下所示：

    08048000-080bc000 r-xp 00000000 03:02 13130      /bin/bash

    Size:               1084 kB
    KernelPageSize:        4 kB
    MMUPageSize:           4 kB
    Rss:                 892 kB
    Pss:                 374 kB
    Pss_Dirty:             0 kB
    Shared_Clean:        892 kB
    Shared_Dirty:          0 kB
    Private_Clean:         0 kB
    Private_Dirty:         0 kB
    Referenced:          892 kB
    Anonymous:             0 kB
    KSM:                   0 kB
    LazyFree:              0 kB
    AnonHugePages:         0 kB
    ShmemPmdMapped:        0 kB
    Shared_Hugetlb:        0 kB
    Private_Hugetlb:       0 kB
    Swap:                  0 kB
    SwapPss:               0 kB
    KernelPageSize:        4 kB
    MMUPageSize:           4 kB
    Locked:                0 kB
    THPeligible:           0
    VmFlags: rd ex mr mw me dw

这些行中的第一行显示了 `/proc/PID/maps` 中映射的信息。随后的行显示了映射的大小（size）；支持VMA时分配的每页大小（KernelPageSize），通常与页表条目中的大小相同；MMU在支持VMA时使用的页大小（大多数情况下与KernelPageSize相同）；当前驻留在RAM中的映射部分（RSS）；进程对此映射的比例份额（PSS）；以及映射中干净和脏的共享和私有页面数量。

“比例集大小”（PSS）是一个进程中在内存中的页面数，其中每个页面被其共享进程的数量除以。因此，如果一个进程拥有1000个仅属于自己的页面，并且与另一个进程共享1000个页面，那么它的PSS将是1500。“Pss_Dirty”是PSS中包含脏页面的部分。（“Pss_Clean”未列出，但可以通过从“Pss”中减去“Pss_Dirty”来计算得出。）

请注意，即使一个页面是MAP_SHARED映射的一部分，但只有一个pte映射，即当前仅由一个进程使用，也会被视为私有而不是共享。

“Referenced” 表示当前标记为已引用或访问的内存量。
“Anonymous” 显示不属于任何文件的内存量。即使与文件关联的映射也可能包含匿名页面：当使用MAP_PRIVATE并且页面被修改时，文件页面会被替换为私有匿名副本。
“KSM” 报告了多少页面是KSM页面。注意，KSM放置的零页面不包括在内，只有实际的KSM页面。
“LazyFree” 显示通过madvise(MADV_FREE)标记的内存量。使用madvise()并不会立即释放内存。如果内存是干净的，它会在内存压力下被释放。请注意，由于当前实现中的优化，打印的值可能低于实际值。如果不希望这种情况，请提交错误报告。
“AnonHugePages” 显示由透明大页支持的内存量。
"ShmemPmdMapped" 显示由大页支持的共享（shmem/tmpfs）内存的数量。

"Shared_Hugetlb" 和 "Private_Hugetlb" 显示由 hugetlbfs 页面支持的内存数量，这些内存由于历史原因不计入 "RSS" 或 "PSS" 字段。并且这些也不包括在 {Shared,Private}_{Clean,Dirty} 字段中。

"Swap" 显示了多少本应匿名的内存在交换区中使用。

对于 shmem 映射，"Swap" 还包括基础 shmem 对象中已映射（且未被写时复制替换）部分的大小在交换区中的使用情况。

"SwapPss" 显示该映射的比例交换份额。与 "Swap" 不同的是，这并不考虑基础 shmem 对象中已交换出去的页面。

"Locked" 表示映射是否被锁定在内存中。

"THPeligible" 表示映射是否有资格分配任何当前启用的大页（THP）自然对齐的页面。如果符合条件则为 1，否则为 0。

"VmFlags" 字段值得单独描述。这个成员以两个字母编码的方式表示特定虚拟内存区域相关的内核标志。代码如下：

    ==    =======================================
    rd    可读
    wr    可写
    ex    可执行
    sh    共享
    mr    可读
    mw    可写
    me    可执行
    ms    可共享
    gd    栈段向下增长
    pf    纯 PFN 范围
    dw    禁用对该映射文件的写入
    lo    页面被锁定在内存中
    io    内存映射的 I/O 区域
    sr    提供了顺序读取建议
    rr    提供了随机读取建议
    dc    分叉时不复制区域
    de    在重映射时不扩展区域
    ac    区域是可计费的
    nr    不为该区域预留交换空间
    ht    区域使用大页 TLB 页面
    sf    同步页面错误
    ar    架构特定标志
    wf    分叉时擦除
    dd    不将区域包含在核心转储中
    sd    软脏标志
    mm    混合映射区域
    hg    大页建议标志
    nh    无大页建议标志
    mg    可合并建议标志
    bt    arm64 BTI 保护页面
    mt    arm64 MTE 分配标签已启用
    um    userfaultfd 缺失跟踪
    uw    userfaultfd 写保护跟踪
    ss    阴影栈页面
    sl    密封
    ==    =======================================

请注意，并不能保证每个标志及其相关助记符将在所有后续内核版本中都存在。事情会有所变化，标志可能会消失或新增。其含义在未来也可能会发生变化。因此，每个使用这些标志的消费者必须关注每个具体的内核版本以获取确切的语义。
此文件仅在启用了 CONFIG_MMU 内核配置选项时才存在。

注意：读取 /proc/PID/maps 或 /proc/PID/smaps 是本质上是有竞争条件的（只有在单次读取调用中才能获得一致的输出）。
这通常在内存映射被修改时进行部分读取这些文件时出现。尽管存在竞态条件，我们仍提供以下保证：

1) 映射地址永远不会回退，这意味着不会有两个区域重叠。
2) 如果某个虚拟地址在整个`smaps`或`maps`遍历过程中有内容，则会有相应的输出。

`/proc/PID/smaps_rollup` 文件包含与`/proc/PID/smaps`相同的字段，但其值是进程所有映射的相应值之和。此外，它还包含以下字段：

- Pss_Anon
- Pss_File
- Pss_Shmem

它们代表匿名、文件和共享内存页面的比例份额，如上文所述。由于每个映射都会标识其所含页面的类型（匿名、文件或共享内存），因此在`smaps`中省略了这些字段。因此，`smaps_rollup`中的所有信息都可以从`smaps`中推导出来，但代价要高得多。

`/proc/PID/clear_refs` 用于重置与进程相关的物理和虚拟页面上的 PG_Referenced 和 ACCESSED/YOUNG 标志，并重置 pte 上的软脏位（详情见 `Documentation/admin-guide/mm/soft-dirty.rst`）。

要清除与进程相关的所有页面的标志：
```
> echo 1 > /proc/PID/clear_refs
```

要清除与进程相关的匿名页面的标志：
```
> echo 2 > /proc/PID/clear_refs
```

要清除与进程相关的文件映射页面的标志：
```
> echo 3 > /proc/PID/clear_refs
```

要清除软脏位：
```
> echo 4 > /proc/PID/clear_refs
```

要将进程的最高驻留集大小（“最高水位线”）重置为当前值：
```
> echo 5 > /proc/PID/clear_refs
```

写入 `/proc/PID/clear_refs` 的任何其他值都不会产生效果。

`/proc/pid/pagemap` 提供了 PFN，可以使用 `/proc/kpageflags` 查找页面标志，并使用 `/proc/kpagecount` 查找页面映射次数。详细解释见 `Documentation/admin-guide/mm/pagemap.rst`。

`/proc/pid/numa_maps` 是基于 `maps` 的扩展，显示了内存局部性和绑定策略以及每个映射的内存使用量（以页面为单位）。输出遵循一个通用格式，其中映射细节按空格分隔，每行表示一个文件映射：

```
address   policy    mapping details
```

例如：
```
00400000 default file=/usr/local/bin/app mapped=1 active=0 N3=1 kernelpagesize_kB=4
00600000 default file=/usr/local/bin/app anon=1 dirty=1 N3=1 kernelpagesize_kB=4
3206000000 default file=/lib64/ld-2.12.so mapped=26 mapmax=6 N0=24 N3=2 kernelpagesize_kB=4
320621f000 default file=/lib64/ld-2.12.so anon=1 dirty=1 N3=1 kernelpagesize_kB=4
3206220000 default file=/lib64/ld-2.12.so anon=1 dirty=1 N3=1 kernelpagesize_kB=4
3206221000 default anon=1 dirty=1 N3=1 kernelpagesize_kB=4
3206800000 default file=/lib64/libc-2.12.so mapped=59 mapmax=21 active=55 N0=41 N3=18 kernelpagesize_kB=4
320698b000 default file=/lib64/libc-2.12.so
3206b8a000 default file=/lib64/libc-2.12.so anon=2 dirty=2 N3=2 kernelpagesize_kB=4
3206b8e000 default file=/lib64/libc-2.12.so anon=1 dirty=1 N3=1 kernelpagesize_kB=4
3206b8f000 default anon=3 dirty=3 active=1 N3=3 kernelpagesize_kB=4
7f4dc10a2000 default anon=3 dirty=3 N3=3 kernelpagesize_kB=4
7f4dc10b4000 default anon=2 dirty=2 active=1 N3=2 kernelpagesize_kB=4
7f4dc1200000 default file=/anon_hugepage\040(deleted) huge anon=1 dirty=1 N3=1 kernelpagesize_kB=2048
7fff335f0000 default stack anon=3 dirty=3 N3=3 kernelpagesize_kB=4
7fff3369d000 default mapped=1 mapmax=35 active=0 N3=1 kernelpagesize_kB=4
```

其中：
- "address" 是映射的起始地址；
- "policy" 报告设置给映射的 NUMA 内存策略（参见 `Documentation/admin-guide/mm/numa_memory_policy.rst`）；
- "mapping details" 总结了映射数据，如映射类型、页面使用计数器、节点局部性页面计数器（N0 == node0, N1 == node1, ...）和支持映射的内核页面大小（以 KB 为单位）。

### 1.2 内核数据

与进程条目类似，内核数据文件提供了有关运行内核的信息。获取这些信息所用的文件包含在 `/proc` 中，并列于表 1-5。并非所有这些文件都会出现在您的系统中。这取决于内核配置和已加载的模块。

| 文件     | 内容                                                                 |
|----------|----------------------------------------------------------------------|
| allocinfo | 内存分配剖析信息                                                     |
| apm      | 高级电源管理信息                                                     |
| bootconfig | 从引导配置获得的内核命令行；如果引导加载程序中有内核参数，则会有一行<br>"# Parameters from bootloader:"，后跟一行包含这些参数，前缀为"# "。(5.5) |
| buddyinfo | 内核内存分配器信息（见正文）(2.5)                                    |
| bus       | 包含特定总线信息的目录                                               |
| cmdline   | 从引导加载程序和嵌入内核镜像中的内核命令行                           |
| cpuinfo   | 关于 CPU 的信息                                                      |
| devices   | 可用设备（块设备和字符设备）                                          |
| dma       | 使用的 DMA 通道                                                      |
| filesystems | 支持的文件系统                                                       |
| driver    | 各种驱动程序，目前有 rtc (2.4)                                       |
| execdomains | 与安全相关的 execdomains (2.4)                                      |
| fb        | 帧缓冲设备 (2.4)                                                     |
| fs        | 文件系统参数，目前有 nfs/exports (2.4)                               |
| ide       | 包含关于 IDE 子系统的目录                                             |
| interrupts | 中断使用情况                                                         |
| iomem     | 内存映射 (2.4)                                                       |
| ioports   | I/O 端口使用情况                                                     |
| irq       | 中断到 CPU 亲和性的掩码 (2.4)(SMP?)                                   |
| isapnp    | ISA 即插即用 (Plug&Play) 信息 (2.4)                                  |
| kcore     | 内核核心镜像（可以是 ELF 或 A.OUT（在 2.4 中已弃用））                 |
| kmsg      | 内核消息                                                             |
| ksyms     | 内核符号表                                                           |
| loadavg   | 最近 1 分钟、5 分钟和 15 分钟的负载平均值；当前可运行进程数（正在运行或在就绪队列中）；系统中的总进程数；最后创建的 PID。 |
所有字段由一个空格分隔，除了“当前可运行的进程数”和“系统中的总进程数”，它们由斜杠（'/'）分隔。示例：0.61 0.61 0.55 3/828 22084  
locks        内核锁  
meminfo      内存信息  
misc         其他信息  
modules      已加载模块列表  
mounts       已挂载的文件系统  
net          网络信息（见正文）  
pagetypeinfo 分配器附加页面信息（见正文）（2.5）  
partitions   系统已知分区表  
pci          过时的PCI总线信息（新方法 -> /proc/bus/pci，由lspci解耦）（2.4）  
rtc          实时时钟  
scsi         SCSI信息（见正文）  
slabinfo     Slab池信息  
softirqs     softirq使用情况  
stat         总体统计信息  
swaps        交换空间利用率  
sys          见第2章  
sysvipc      SysVIPC资源信息（消息、信号量、共享内存）（2.4）  
tty          终端驱动信息  
uptime       自启动以来的墙钟时间和所有CPU的组合空闲时间  
version      内核版本  
video        视频资源的bttv信息（2.4）  
vmallocinfo  显示vmalloc的区域  

你可以通过查看文件 /proc/interrupts 来检查当前使用的中断及其用途：

  > cat /proc/interrupts
             CPU0
    0:    8728810          XT-PIC  定时器
    1:        895          XT-PIC  键盘
    2:          0          XT-PIC  级联
    3:     531695          XT-PIC  aha152x
    4:    2014133          XT-PIC  串口
    5:      44401          XT-PIC  pcnet_cs
    8:          2          XT-PIC  RTC
   11:          8          XT-PIC  i82365
   12:     182918          XT-PIC  PS/2 鼠标
   13:          1          XT-PIC  FPU
   14:    1232265          XT-PIC  IDE0
   15:          7          XT-PIC  IDE1
  NMI:          0

在2.4.*版本中，此文件添加了几行内容 LOC & ERR（这是SMP机器的输出）：

  > cat /proc/interrupts

             CPU0       CPU1
    0:    1243498    1214548    IO-APIC-edge  定时器
    1:       8949       8958    IO-APIC-edge  键盘
    2:          0          0          XT-PIC  级联
    5:      11286      10161    IO-APIC-edge  声卡
    8:          1          0    IO-APIC-edge  RTC
    9:      27422      27407    IO-APIC-edge  3c503
   12:     113645     113873    IO-APIC-edge  PS/2 鼠标
   13:          0          0          XT-PIC  FPU
   14:      22491      24012    IO-APIC-edge  IDE0
   15:       2183       2415    IO-APIC-edge  IDE1
   17:      30564      30414   IO-APIC-level  eth0
   18:        177        164   IO-APIC-level  bttv
  NMI:    2457961    2457959
  LOC:    2457882    2457881
  ERR:       2155

NMI 在这种情况下增加是因为每个定时器中断都会生成一个 NMI（不可屏蔽中断），该中断用于 NMI Watchdog 检测死锁。
LOC 是每个 CPU 的内部 APIC 的本地中断计数器。
ERR 在 IO-APIC 总线错误的情况下增加（该总线连接SMP系统的CPU）。这意味着检测到一个错误，IO-APIC会自动重试传输，因此不应是一个大问题，但你应该阅读SMP-FAQ。
在2.6.2*版本中，/proc/interrupts 又被扩展了。这次的目标是显示系统中使用的每一个IRQ向量，而不仅仅是那些被认为是“最重要的”。新的向量包括：

THR
  当机器检查阈值计数器（通常用于计算内存或缓存中的ECC校正错误）超过可配置阈值时触发的中断。仅在某些系统上可用。
TRM
  当CPU温度超过阈值时触发的热事件中断。当温度降至正常时，也可能生成此中断。
SPU
  一些I/O设备在APIC能够完全处理之前就触发并撤销的中断。因此，APIC看到了中断，但不知道它来自哪个设备。在这种情况下，APIC将生成一个IRQ向量为0xff的中断。这可能也由芯片组错误生成。
RES, CAL, TLB
  调度、调用和TLB刷新中断是由OS根据需要从一个CPU发送到另一个CPU的。通常，这些统计信息用于内核开发人员和感兴趣的用户来确定给定类型的中断发生次数。

上述IRQ向量仅在相关时显示。例如，在x86_64平台上不存在阈值向量。其他向量在系统为单处理器时被抑制。截至本文撰写时，只有i386和x86_64平台支持新的IRQ向量显示。
值得一提的是，在2.4版本中引入了 /proc/irq 目录。
它可以用来设置IRQ与CPU的亲和性。这意味着你可以将一个IRQ“绑定”到单个CPU上，或者排除某个CPU处理IRQ。`irq`子目录的内容包括每个IRQ的一个子目录，以及两个文件：`default_smp_affinity` 和 `prof_cpu_mask`。例如：

  ```
  > ls /proc/irq/
  0  10  12  14  16  18  2  4  6  8  prof_cpu_mask
  1  11  13  15  17  19  3  5  7  9  default_smp_affinity
  > ls /proc/irq/0/
  smp_affinity
  ```

`smp_affinity` 是一个位掩码，用于指定哪些CPU可以处理该IRQ。你可以通过以下命令来设置它：

  ```
  > echo 1 > /proc/irq/10/smp_affinity
  ```

这表示只有第一个CPU会处理该IRQ，但你也可以输入5，这意味着只有第一个和第三个CPU可以处理该IRQ。

每个`smp_affinity`文件的默认内容是相同的：

  ```
  > cat /proc/irq/0/smp_affinity
  ffffffff
  ```

还有一个替代接口 `smp_affinity_list`，允许指定CPU范围而不是位掩码：

  ```
  > cat /proc/irq/0/smp_affinity_list
  1024-1031
  ```

`default_smp_affinity` 掩码适用于所有未激活的IRQ，这些IRQ尚未被分配或激活，因此没有对应的 `/proc/irq/[0-9]*` 目录。

在SMP系统中，`node` 文件显示使用该IRQ的设备报告自己所连接的节点。此硬件位置信息不包括任何可能的驱动程序位置偏好。

`prof_cpu_mask` 指定了哪些CPU由系统范围内的性能分析器进行分析。默认值为 `ffffffff`（如果只有32个CPU的话）。

IRQ 的路由由IO-APIC处理，并且在所有允许处理它的CPU之间以轮询的方式进行。通常内核比你知道的信息更多，做得也更好，因此默认设置对大多数人来说是最好的选择。[注意，这仅适用于支持“轮询”中断分配的IO-APIC。]

在 `/proc` 中还有三个重要的子目录：`net`、`scsi` 和 `sys`。一般规则是这些目录的内容，甚至它们的存在，取决于你的内核配置。如果没有启用SCSI，则 `scsi` 目录可能不存在。同样，当内核支持网络功能时，`net` 目录才会存在。

`slabinfo` 文件提供了关于内存使用的 slab 级别信息。Linux 在2.2版本中使用 slab 池来进行页面级别的内存管理。常用对象有自己的 slab 池（如网络缓冲区、目录缓存等）。
```plaintext
> cat /proc/buddyinfo

节点 0，区域 DMA        0      4      5      4      4      3 ..
节点 0，区域 Normal      1      0      0      1    101      8 ..
节点 0，区域 HighMem     2      0      0      1      1      0 ..
外部碎片化在某些工作负载下是一个问题，buddyinfo 是诊断这些问题的有用工具。buddyinfo 可以帮助你了解可以安全分配的内存块大小，或者为什么之前的分配失败。
每一列代表特定大小页面的数量。例如，在 ZONE_DMA 中有 0 块 2^0 * PAGE_SIZE 大小的页面，4 块 2^1 * PAGE_SIZE 大小的页面，在 ZONE_NORMAL 中有 101 块 2^4 * PAGE_SIZE 大小的页面等。
关于外部碎片化的更多信息可以在 pagetypeinfo 中找到：

> cat /proc/pagetypeinfo
页面块顺序：9
每个块中的页面数：512

不同迁移类型的空闲页面数量（按顺序）：
节点 0，区域 DMA，类型 不可移动     0      0      0      1      1      1      1      1      1      1      0
节点 0，区域 DMA，类型 可回收       0      0      0      0      0      0      0      0      0      0      0
节点 0，区域 DMA，类型 可移动       1      1      2      1      2      1      1      0      1      0      2
节点 0，区域 DMA，类型 预留         0      0      0      0      0      0      0      0      0      1      0
节点 0，区域 DMA，类型 隔离         0      0      0      0      0      0      0      0      0      0      0
节点 0，区域 DMA32，类型 不可移动  103     54     77      1      1      1     11      8      7      1      9
节点 0，区域 DMA32，类型 可回收     0      0      2      1      0      0      0      0      1      0      0
节点 0，区域 DMA32，类型 可移动   169    152    113     91     77     54     39     13      6      1    452
节点 0，区域 DMA32，类型 预留         1      2      2      2      2      0      1      1      1      1      0
节点 0，区域 DMA32，类型 隔离         0      0      0      0      0      0      0      0      0      0      0

不同类型页面块的数量：
节点 0，区域 DMA                2            0            5            1            0
节点 0，区域 DMA32             41            6          967            2            0

内核中的碎片避免通过将不同迁移类型的页面分组到相同的连续内存区域（称为页面块）中来实现。
一个页面块通常是默认的大页大小，例如在 X86-64 上为 2MB。通过根据页面是否能够移动来分组，内核可以在页面块内重新获取页面以满足高阶分配需求。
pagetypeinfo 从页面块大小信息开始，然后提供与 buddyinfo 类似的信息，但按迁移类型拆分，并以每种类型的页面块数量结束。
如果 min_free_kbytes 已正确调整（推荐使用 libhugetlbfs 的 hugeadm 工具 https://github.com/libhugetlbfs/libhugetlbfs/），则可以根据当前时间点估计可以分配的大页数量。所有“可移动”块都应该是可分配的，除非内存已被锁定。一些“可回收”块也应该是可分配的，尽管可能需要释放大量文件系统元数据才能实现这一点。

allocinfo
~~~~~~~~~

提供了代码库中所有位置的内存分配信息。代码中的每次分配都由其源文件、行号、模块（如果是来自可加载模块）和调用分配的函数标识。报告了每个位置分配的字节数和调用次数。第一行表示文件版本，第二行是文件中的字段列表。
```
示例输出：

```shell
> tail -n +3 /proc/allocinfo | sort -rn
127664128    31168 mm/page_ext.c:270 func:alloc_page_ext
56373248     4737 mm/slub.c:2259 func:alloc_slab_page
14880768     3633 mm/readahead.c:247 func:page_cache_ra_unbounded
14417920     3520 mm/mm_init.c:2530 func:alloc_large_system_hash
13377536      234 block/blk-mq.c:3421 func:blk_mq_alloc_rqs
11718656     2861 mm/filemap.c:1919 func:__filemap_get_folio
9192960     2800 kernel/fork.c:307 func:alloc_thread_stack_node
4206592        4 net/netfilter/nf_conntrack_core.c:2567 func:nf_ct_alloc_hashtable
4136960     1010 drivers/staging/ctagmod/ctagmod.c:20 [ctagmod] func:ctagmod_start
3940352      962 mm/memory.c:4214 func:alloc_anon_folio
2894464    22613 fs/kernfs/dir.c:615 func:__kernfs_new_node
..
```

`/proc/meminfo`
~~~~~~~~~~~~~~

提供了有关内存分配和使用的详细信息。这些信息因架构和编译选项而异。某些计数器可能会重叠。非重叠计数器报告的内存可能不会加总到总体内存使用量，并且在某些工作负载下，差异可能相当大。在许多情况下，可以使用特定子系统的接口来获取额外的内存使用情况，例如 `/proc/net/sockstat` 可用于查看 TCP 内存分配。

示例输出：
```shell
> cat /proc/meminfo

MemTotal:       32858820 kB
MemFree:        21001236 kB
MemAvailable:   27214312 kB
Buffers:          581092 kB
Cached:          5587612 kB
SwapCached:            0 kB
Active:          3237152 kB
Inactive:        7586256 kB
Active(anon):      94064 kB
Inactive(anon):  4570616 kB
Active(file):    3143088 kB
Inactive(file):  3015640 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Zswap:              1904 kB
Zswapped:           7792 kB
Dirty:                12 kB
Writeback:             0 kB
AnonPages:       4654780 kB
Mapped:           266244 kB
Shmem:              9976 kB
KReclaimable:     517708 kB
Slab:             660044 kB
SReclaimable:     517708 kB
SUnreclaim:       142336 kB
KernelStack:       11168 kB
PageTables:        20540 kB
SecPageTables:         0 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:    16429408 kB
Committed_AS:    7715148 kB
VmallocTotal:   34359738367 kB
VmallocUsed:       40444 kB
VmallocChunk:          0 kB
Percpu:            29312 kB
EarlyMemtestBad:       0 kB
HardwareCorrupted:     0 kB
AnonHugePages:   4149248 kB
ShmemHugePages:        0 kB
ShmemPmdMapped:        0 kB
FileHugePages:         0 kB
FilePmdMapped:         0 kB
CmaTotal:              0 kB
CmaFree:               0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
DirectMap4k:      401152 kB
DirectMap2M:    10008576 kB
DirectMap1G:    24117248 kB
```

- `MemTotal`: 总可用 RAM（即物理 RAM 减去一些预留位和内核二进制代码）
- `MemFree`: 总空闲 RAM。在高内存系统中，这是 LowFree 和 HighFree 的总和。
- `MemAvailable`: 估计可用于启动新应用程序而不进行交换的内存数量。该值由 MemFree、SReclaimable、文件 LRU 列表的大小以及每个区域的低水位线计算得出。
  该估计考虑了系统需要一些页面缓存才能正常运行，并且并非所有可回收的 slab 都是可回收的，因为有些项正在使用中。这些因素的影响会因系统而异。
- `Buffers`: 相对临时存储的原始磁盘块，通常不应变得非常大（约 20MB 左右）。
- `Cached`: 从磁盘读取文件的内存缓存（即页面缓存）以及 tmpfs 和 shmem。
  不包括 SwapCached。
- `SwapCached`: 曾经被交换出去，现在又交换回来但仍然保留在交换文件中的内存（如果需要内存，则不需要再次交换出去，因为已经在交换文件中。这节省了 I/O 操作）。
- `Active`: 最近使用过的内存，通常除非绝对必要，否则不会被回收。
- `Inactive`: 较长时间未使用的内存，更适合被回收用于其他用途。
- `Unevictable`: 分配给用户空间且不可回收的内存，例如锁定的页面、ramfs 支持页面、秘密 memfd 页面等。
Mlocked  
使用 mlock() 锁定的内存

HighTotal, HighFree  
Highmem 是指物理内存中超过约 860MB 的部分  
Highmem 区域用于用户空间程序或页面缓存。内核必须使用技巧访问这部分内存，因此访问速度比低内存（lowmem）慢

LowTotal, LowFree  
低内存（lowmem）可以用于高内存（highmem）的所有用途，但也可以供内核用于其自身数据结构。包括 Slab 中分配的所有内容。当低内存不足时会发生严重问题

SwapTotal  
可用交换空间总量

SwapFree  
从 RAM 中移出并临时存储在磁盘上的内存

Zswap  
被 zswap 后端消耗的内存（压缩后的大小）

Zswapped  
存储在 zswap 中的匿名内存量（原始大小）

Dirty  
等待写回磁盘的内存

Writeback  
正在积极写回磁盘的内存

AnonPages  
映射到用户空间页表中的非文件支持的页面

Mapped  
已经被内存映射的文件，例如库

Shmem  
共享内存（shmem）和 tmpfs 使用的总内存

KReclaimable  
内核在内存压力下尝试回收的分配。包括 SReclaimable（如下），以及其他带有收缩器的直接分配

Slab  
内核数据结构缓存

SReclaimable  
Slab 的一部分，可能会被回收，例如缓存

SUnreclaim  
Slab 的一部分，在内存压力下无法回收

KernelStack  
所有任务的内核栈消耗的内存

PageTables  
用户空间页表消耗的内存

SecPageTables  
二级页表消耗的内存，目前包括 x86 和 arm64 上的 KVM MMU 和 IOMMU 分配

NFS_Unstable  
始终为零。之前计算过已写入服务器但未提交到稳定存储的页面

Bounce  
块设备“弹跳缓冲区”使用的内存

WritebackTmp  
FUSE 用于临时写回缓冲区的内存

CommitLimit  
基于过度承诺比率（'vm.overcommit_ratio'），这是当前系统上可分配的内存总量。只有在启用严格的过度承诺会计（模式 2 在 'vm.overcommit_memory' 中）时才会遵守此限制。计算 CommitLimit 的公式如下：

                CommitLimit = ([总 RAM 页数] - [总巨大 TLB 页数]) * 过度承诺比率 / 100 + [总交换页数]

              例如，在一个具有 1GB 物理 RAM 和 7GB 交换空间且 `vm.overcommit_ratio` 为 30 的系统上，将得到 7.3GB 的 CommitLimit

更多详情，请参阅 mm/overcommit-accounting 中的内存过度承诺文档
已提交内存 (Committed_AS)
当前系统分配的内存总量
已提交的内存是所有由进程分配的内存之和，即使这些内存尚未被使用。如果一个进程通过 `malloc()` 分配了 1GB 的内存，但只使用了其中的 300MB，那么该进程将显示为使用了 1GB 的内存。这 1GB 是虚拟内存管理系统已经“承诺”的内存，可以在任何时候被分配的应用程序使用。如果系统启用了严格的过度分配模式（`vm.overcommit_memory` 设置为模式 2），则超出 `CommitLimit` 的分配将不被允许。这在需要保证进程在成功分配内存后不会因内存不足而失败时非常有用。

VmallocTotal
vmalloc 虚拟地址空间的总大小

VmallocUsed
已使用的 vmalloc 区域大小

VmallocChunk
vmalloc 区域中最大的连续空闲块大小

PerCPU
分配给 Per-CPU 分配器的内存，用于支持 Per-CPU 分配。此统计数据不包括元数据的成本

EarlyMemtestBad
早期内存测试识别出的损坏内存大小（以千字节为单位）。如果未运行内存测试，则此字段将不会显示。大小永远不会向下舍入到 0 千字节。这意味着如果报告为 0 千字节，可以安全地假设至少进行了一次内存测试，并且没有发现任何损坏的字节

HardwareCorrupted
内核识别出的损坏内存大小（以千字节为单位）

AnonHugePages
映射到用户空间页表中的非文件支持的大页面

ShmemHugePages
共享内存（shmem）和使用大页面分配的 tmpfs 所占用的内存

ShmemPmdMapped
使用大页面映射到用户空间的共享内存

FileHugePages
使用大页面分配的文件系统数据（页缓存）所占用的内存

FilePmdMapped
使用大页面映射到用户空间的页缓存

CmaTotal
为连续内存分配器（CMA）预留的内存总量

CmaFree
CMA 预留内存中剩余的自由内存

HugePages_Total, HugePages_Free, HugePages_Rsvd, HugePages_Surp, Hugepagesize, Hugetlb
请参阅 `Documentation/admin-guide/mm/hugetlbpage.rst`

DirectMap4k, DirectMap2M, DirectMap1G
内核对 RAM 的身份映射所使用的分页表大小的详细信息

vmallocinfo
提供有关 vmalloc/vmap 区域的信息。每行表示一个区域，包含区域的虚拟地址范围、字节大小、创建者的调用信息以及根据区域类型的不同可选信息：

 =========  =======================================================
 pages=nr   页面数量
 phys=addr  如果指定了物理地址
 ioremap    I/O 映射（ioremap() 和相关函数）
 vmalloc    vmalloc() 区域
 vmap       vmap() 映射的页面
 user       VM_USERMAP 区域
 vpages     用于页面指针缓冲区的 vmalloc（巨大区域）
 N<node>=nr （仅在 NUMA 内核上）
              在内存节点 <node> 上分配的页面数量
 =========  =======================================================

示例输出：
```
> cat /proc/vmallocinfo
0xffffc20000000000-0xffffc20000201000 2101248 alloc_large_system_hash+0x204 ../0x2c0 pages=512 vmalloc N0=128 N1=128 N2=128 N3=128
0xffffc20000201000-0xffffc20000302000 1052672 alloc_large_system_hash+0x204 ..
```
```
0x2c0 页数=256 vmalloc N0=64 N1=64 N2=64 N3=64
0xffffc20000302000-0xffffc20000304000    8192 acpi_tb_verify_table+0x21/0x4f..
物理地址=7fee8000 ioremap
0xffffc20000304000-0xffffc20000307000   12288 acpi_tb_verify_table+0x21/0x4f..
物理地址=7fee7000 ioremap
0xffffc2000031d000-0xffffc2000031f000    8192 init_vdso_vars+0x112/0x210
0xffffc2000031f000-0xffffc2000032b000   49152 cramfs_uncompress_init+0x2e ..
/0x80 页数=11 vmalloc N0=3 N1=3 N2=2 N3=3
0xffffc2000033a000-0xffffc2000033d000   12288 sys_swapon+0x640/0xac0      
页数=2 vmalloc N1=2
0xffffc20000347000-0xffffc2000034c000   20480 xt_alloc_table_info+0xfe ..
/0x130 [x_tables] 页数=4 vmalloc N0=4
0xffffffffa0000000-0xffffffffa000f000   61440 sys_init_module+0xc27/0x1d00 ..
页数=14 vmalloc N2=14
0xffffffffa000f000-0xffffffffa0014000   20480 sys_init_module+0xc27/0x1d00 ..
页数=4 vmalloc N1=4
0xffffffffa0014000-0xffffffffa0017000   12288 sys_init_module+0xc27/0x1d00 ..
页数=2 vmalloc N1=2
0xffffffffa0017000-0xffffffffa0022000   45056 sys_init_module+0xc27/0x1d00 ..
页数=10 vmalloc N0=10

软中断
~~~~~~~~

提供自启动以来每个CPU服务的软中断处理程序计数
```
```bash
> cat /proc/softirqs
		  CPU0       CPU1       CPU2       CPU3
	HI:          0          0          0          0
    TIMER:       27166      27120      27097      27034
    NET_TX:          0          0          0         17
    NET_RX:         42          0          0         39
    BLOCK:           0          0        107       1121
    TASKLET:         0          0          0        290
    SCHED:       27035      26983      26971      26746
    HRTIMER:         0          0          0          0
	RCU:      1678       1769       2178       2250
```

### 1.3 网络信息在 `/proc/net` 目录下
--------------------------------

`/proc/net` 子目录遵循通常的模式。表 1-8 显示了如果你配置内核支持 IPv6，则可以获取的额外值。表 1-9 列出了文件及其含义。

#### 表 1-8：`/proc/net` 下的 IPv6 信息

| 文件       | 内容                                       |
|------------|--------------------------------------------|
| udp6       | UDP 套接字（IPv6）                         |
| tcp6       | TCP 套接字（IPv6）                         |
| raw6       | 原始设备统计（IPv6）                       |
| igmp6      | 本主机加入的 IP 组播地址（IPv6）            |
| if_inet6   | IPv6 接口地址列表                          |
| ipv6_route | 内核的 IPv6 路由表                        |
| rt6_stats  | 全局 IPv6 路由表统计                       |
| sockstat6  | 套接字统计（IPv6）                         |
| snmp6      | SNMP 数据（IPv6）                          |

#### 表 1-9：`/proc/net` 下的网络信息

| 文件          | 内容                                               |
|---------------|----------------------------------------------------|
| arp           | 内核 ARP 表                                        |
| dev           | 带有统计信息的网络设备                              |
| dev_mcast     | 设备监听的第 2 层组播组（接口索引、标签、引用数量、绑定地址数量） |
| dev_stat      | 网络设备状态                                       |
| ip_fwchains   | 防火墙链链接                                       |
| ip_fwnames    | 防火墙链名称                                       |
| ip_masq       | 包含伪装表的目录                                   |
| ip_masquerade | 主要的伪装表                                       |
| netstat       | 网络统计                                           |
| raw           | 原始设备统计                                       |
| route         | 内核路由表                                         |
| rpc           | 包含 RPC 信息的目录                                 |
| rt_cache      | 路由缓存                                           |
| snmp          | SNMP 数据                                          |
| sockstat      | 套接字统计                                         |
| softnet_stat  | 在线 CPU 的每个 CPU 的入站数据包队列统计           |
| tcp           | TCP 套接字                                         |
| udp           | UDP 套接字                                         |
| unix          | UNIX 域套接字                                      |
| wireless      | 无线接口数据（如 Wavelan 等）                      |
| igmp          | 本主机加入的 IP 组播地址                            |
| psched        | 全局数据包调度参数                                  |
| netlink       | PF_NETLINK 套接字列表                               |
| ip_mr_vifs    | 组播虚拟接口列表                                    |
| ip_mr_cache   | 组播路由缓存列表                                    |

你可以使用这些信息查看系统中有哪些网络设备以及通过这些设备传输了多少流量：

```bash
> cat /proc/net/dev
Inter-|Receive                                                   |[..]
face |bytes    packets errs drop fifo frame compressed multicast|[..]
lo:  908188   5596     0    0    0     0          0         0 [..]
ppp0:15475140  20721   410    0    0   410          0         0 [..]
eth0:  614530   7085     0    0    0     0          0         1 [..]
[...] Transmit
[..] bytes    packets errs drop fifo colls carrier compressed
[..]  908188     5596    0    0    0     0       0          0
[..] 1375103    17405    0    0    0     0       0          0
[..] 1703981     5535    0    0    0     3       0          0
```

此外，每个通道绑定接口都有自己的目录。例如，bond0 设备将有一个名为 `/proc/net/bond0/` 的目录。它将包含与该绑定相关的特定信息，如当前的从属设备、从属设备的链路状态以及从属设备链路失败的次数。
### 1.4 SCSI 信息
-------------

如果你的系统中有一个SCSI或ATA主机适配器，你将在 `/proc/scsi` 目录下找到一个以该适配器驱动程序命名的子目录。在 `/proc/scsi` 下你还可以看到所有已识别的SCSI设备的列表：

```
> cat /proc/scsi/scsi
附带的设备：
Host: scsi0 Channel: 00 Id: 00 Lun: 00
Vendor: IBM      Model: DGHS09U          Rev: 03E0
Type:   Direct-Access                    ANSI SCSI revision: 03
Host: scsi0 Channel: 00 Id: 06 Lun: 00
Vendor: PIONEER  Model: CD-ROM DR-U06S   Rev: 1.04
Type:   CD-ROM                           ANSI SCSI revision: 02
```

以驱动程序命名的目录包含系统中每个适配器的一个文件。这些文件包含有关控制器的信息，包括使用的中断和IO地址范围。显示的信息量取决于你使用的适配器。下面的例子展示了Adaptec AHA-2940 SCSI适配器的输出：

```
> cat /proc/scsi/aic7xxx/0

Adaptec AIC7xxx driver version: 5.1.19/3.2.4
编译选项：
    TCQ 默认启用：禁用
    AIC7XXX_PROC_STATS     ：禁用
    AIC7XXX_RESET_DELAY    ：5
适配器配置：
    SCSI适配器：Adaptec AHA-294X Ultra SCSI 主机适配器
                Ultra Wide 控制器
    PCI MMAPed I/O 基址：0xeb001000
    适配器 SEEPROM 配置：找到了SEEPROM并使用了它
Adaptec SCSI BIOS：启用
                   IRQ: 10
                  SCBs: 活动0，最大活动2，
                        分配15，硬件16，页面255
                 中断：160328
        BIOS 控制字：0x18b6
     适配器控制字：0x005b
     扩展翻译：启用
  断开连接启用标志：0xffff
       Ultra 启用标志：0x0001
   标签队列启用标志：0x0000
  顺序队列标签标志：0x0000
  默认标签队列深度：8
      标签队列按设备数组（针对aic7xxx主机实例0）：
        {255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255}
      实际每设备队列深度（针对aic7xxx主机实例0）：
        {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1}
统计信息：
(scsi0:0:0:0)
    设备使用宽/同步传输，速度为40.0 MB/s，偏移8
    Transinfo 设置：当前(12/8/1/0)，目标(12/8/1/0)，用户(12/15/1/0)
    总传输次数 160151 （74577次读取和85574次写入）
(scsi0:0:6:0)
    设备使用窄/同步传输，速度为5.0 MB/s，偏移15
    Transinfo 设置：当前(50/15/0/0)，目标(50/15/0/0)，用户(50/15/0/0)
    总传输次数 0 （0次读取和0次写入）
```

### 1.5 并行端口信息在 /proc/parport
---------------------------------------

目录 `/proc/parport` 包含关于系统中并行端口的信息。它为每个端口都有一个子目录，以端口号命名（0,1,2,...）。这些目录包含表1-10中所示的四个文件。

.. table:: 表1-10: 文件在 /proc/parport

 ========= ====================================================================
 文件      内容
 ========= ====================================================================
 autoprobe 任何获取到的IEEE-1284设备ID信息
 devices   使用该端口的设备驱动程序列表。当前正在使用该端口的设备名称旁边会有一个+号（可能没有任何+号）
 hardware  并行端口的基本地址、中断线和DMA通道
 irq       该端口使用的parport中断。这个文件是单独的，以便你可以通过写入新值来更改它（中断编号或无）
 ========= ====================================================================

### 1.6 终端信息在 /proc/tty
-------------------------

关于可用和实际使用的终端的信息可以在目录 `/proc/tty` 中找到。在这个目录中你会找到驱动程序和线路规程的条目，如表1-11所示。

.. table:: 表1-11: 文件在 /proc/tty

 ============= ==============================================
 文件          内容
 ============= ==============================================
 drivers       驱动程序及其使用情况的列表
 ldiscs        注册的线路规程
 driver/serial 单个终端线路的使用统计和状态
 ============= ==============================================

要查看当前哪些终端正在使用，可以简单地查看文件 `/proc/tty/drivers`：

```
> cat /proc/tty/drivers
pty_slave            /dev/pts      136   0-255 pty:slave
pty_master           /dev/ptm      128   0-255 pty:master
pty_slave            /dev/ttyp       3   0-255 pty:slave
pty_master           /dev/pty        2   0-255 pty:master
serial               /dev/cua        5   64-67 serial:callout
serial               /dev/ttyS       4   64-67 serial
/dev/tty0            /dev/tty0       4       0 system:vtmaster
/dev/ptmx            /dev/ptmx       5       2 system
/dev/console         /dev/console    5       1 system:console
/dev/tty             /dev/tty        5       0 system:/dev/tty
unknown              /dev/tty        4    1-63 console
```

### 1.7 内核统计信息在 /proc/stat
-------------------------------------------------

关于内核活动的各种信息可以在文件 `/proc/stat` 中找到。此文件中的所有数字都是自系统首次启动以来的累计数。为了快速查看，可以简单地使用 `cat` 命令查看文件内容：

```
> cat /proc/stat
cpu  237902850 368826709 106375398 1873517540 1135548 0 14507935 0 0 0
cpu0 60045249 91891769 26331539 468411416 495718 0 5739640 0 0 0
cpu1 59746288 91759249 26609887 468860630 312281 0 4384817 0 0 0
cpu2 59489247 92985423 26904446 467808813 171668 0 2268998 0 0 0
cpu3 58622065 92190267 26529524 468436680 155879 0 2114478 0 0 0
intr 8688370575 8 3373 0 0 0 0 0 0 1 40791 0 0 353317 0 0 0 0 224789828 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 190974333 41958554 123983334 43 0 224593 0 0 0 <更多0被删除>
ctxt 22848221062
btime 1605316999
processes 746787147
procs_running 2
procs_blocked 0
softirq 12121874454 100099120 3938138295 127375644 2795979 187870761 0 173808342 3072582055 52608 224184354
```

第一条 `"cpu"` 行汇总了所有其他 `"cpuN"` 行的数字。这些数字标识了CPU花费在不同类型工作上的时间。时间单位为USER_HZ（通常是百分之一秒）。各列的含义如下，从左至右：

- user: 在用户模式下执行的正常进程
- nice: 在用户模式下执行的nice进程
- system: 在内核模式下执行的进程
- idle: 无所事事
- iowait: 简而言之，iowait表示等待I/O完成。但有几个问题：

  1. CPU不会等待I/O完成，iowait是一个任务等待I/O完成的时间。当CPU因未完成的任务I/O进入空闲状态时，另一个任务将被调度到这个CPU上。
2. 在一个多核CPU中，等待I/O完成的任务不会在任何CPU上运行，因此每个CPU的iowait很难计算。
3. 在某些条件下，/proc/stat中的iowait字段的值会减少。
因此，从/proc/stat读取的iowait值是不可靠的。

- irq：处理中断
- softirq：处理软中断
- steal：非自愿等待
- guest：运行普通虚拟机
- guest_nice：运行具有nice值的虚拟机

"intr"行显示了自系统启动以来每种可能的系统中断所处理的中断次数。第一列是所有已处理中断的总数，包括未编号的架构特定中断；随后的每一列是特定编号中断的总数。未编号的中断不单独显示，仅汇总到总数中。
"ctxt"行给出了所有CPU上的上下文切换总数。
"btime"行给出了系统启动的时间，以自Unix纪元以来的秒数表示。
"processes"行给出了创建的进程和线程的数量，这包括（但不限于）由fork()和clone()系统调用创建的进程和线程。
"procs_running"行给出了正在运行或准备运行的线程总数（即可运行线程的总数）。
"procs_blocked"行给出了当前被阻塞、等待I/O完成的进程数量。
```markdown
"softirq"行显示了自启动以来每个可能的系统softirq服务的次数。第一列是所有softirq服务的总数；随后的每一列是特定softirq的总次数。

1.8 Ext4 文件系统参数
-------------------------------

已挂载的ext4文件系统的相关信息可以在/proc/fs/ext4中找到。每个已挂载的文件系统都会在/proc/fs/ext4下有一个基于其设备名称的目录（例如，/proc/fs/ext4/hdc 或 /proc/fs/ext4/sda9 或 /proc/fs/ext4/dm-0）。每个设备目录中的文件如表1-12所示。
.. table:: 表1-12：/proc/fs/ext4/<devname>下的文件

 ==============  ==========================================================
 文件            内容
 mb_groups       多块分配器空闲块伙伴缓存的详细信息
 ==============  ==========================================================

1.9 /proc/consoles
-------------------
显示注册的系统控制台行
要查看当前用于系统控制台/dev/console的字符设备行，可以查看文件/proc/consoles的内容：

  > cat /proc/consoles
  tty0                 -WU (ECp)       4:7
  ttyS0                -W- (Ep)        4:64

各列含义如下：

+--------------------+-------------------------------------------------------+
| 设备               | 设备名称                                              |
+====================+=======================================================+
| 操作               | * R = 可执行读操作                                     |
|                    | * W = 可执行写操作                                     |
|                    | * U = 可以解除屏幕保护                                 |
+--------------------+-------------------------------------------------------+
| 标志               | * E = 已启用                                           |
|                    | * C = 首选控制台                                       |
|                    | * B = 主引导控制台                                     |
|                    | * p = 用于printk缓冲区                                 |
|                    | * b = 不是TTY而是一个盲文设备                           |
|                    | * a = 在CPU离线时使用安全                               |
+--------------------+-------------------------------------------------------+
| 主号:次号          | 设备的主要和次要编号，用冒号分隔                       |
+--------------------+-------------------------------------------------------+

总结
-------

/proc文件系统提供了关于运行系统的信息。它不仅允许访问进程数据，还允许通过读取该层次结构中的文件来请求内核状态。/proc目录结构反映了不同类型的信息，并且使查找特定数据变得容易。

第二章：修改系统参数
======================

本章内容
---------------

* 通过写入/proc/sys中的文件来修改内核参数
* 探索修改某些参数的文件
* 回顾/proc/sys文件树

------------------------------------------------------------------------------

/proc的一个非常有趣的部分是/proc/sys目录。这不仅是信息的来源，还可以让你在内核内部改变参数。尝试时务必小心谨慎。你可以优化你的系统，但也会导致系统崩溃。绝不在生产系统上更改内核参数。设置一个开发机器进行测试，确保一切按你希望的方式工作。一旦出错，你可能别无选择只能重启机器。

要更改值，只需将新值回显到文件中即可。这需要root权限。你可以创建自己的引导脚本来每次系统启动时执行这些操作。
/proc/sys中的文件可用于微调和监控Linux内核操作中的各种通用事务。由于某些文件可能会无意中断系统，因此建议在实际调整之前阅读相关文档和源代码。无论如何，在写入任何这些文件时要格外小心。/proc中的条目在2.1.*和2.2内核之间可能会略有不同，如果有疑问，请查阅linux/Documentation目录中的内核文档。
本章主要基于2.2之前的内核文档，并在Linux内核2.2.1版本中成为其一部分。
```
请参阅：Documentation/admin-guide/sysctl/ 目录以获取这些条目的描述。

摘要
------
内核的某些行为可以在运行时进行修改，无需重新编译内核或重启系统。/proc/sys 目录下的文件不仅可以读取，还可以进行修改。您可以使用 `echo` 命令将值写入这些文件，从而改变内核的默认设置。

第3章：按进程参数
==================

3.1 /proc/<pid>/oom_adj & /proc/<pid>/oom_score_adj — 调整 OOM 杀手分数
--------------------------------------------------------------------------------

这些文件可以用来调整用于选择在内存不足（OOM）条件下被杀死的进程的恶劣度评分。

恶劣度评分会给每个候选任务分配一个从 0（永不杀）到 1000（总是杀）之间的值，以此来决定哪个进程成为目标。单位大致是根据当前内存和交换区使用情况估计的允许分配内存的比例。

例如，如果一个任务使用了所有允许的内存，其恶劣度评分为 1000；如果它只使用了一半的允许内存，评分为 500。

“允许”的内存量取决于 OOM 杀手被调用的上下文。如果是由于分配任务的 cgroup 内存耗尽，则允许的内存表示分配给该 cgroup 的内存集合。如果是由于内存策略节点耗尽，则允许的内存表示内存策略节点集合。如果是由于达到内存限制（或交换区限制），则允许的内存是配置的限制。最后，如果是由于整个系统内存耗尽，则允许的内存表示所有可分配资源。

/proc/<pid>/oom_score_adj 的值会在使用之前加到恶劣度评分上。可接受的范围是从 -1000 (OOM_SCORE_ADJ_MIN) 到 +1000 (OOM_SCORE_ADJ_MAX)。这允许用户空间通过始终偏好某个特定任务或完全禁用它来极化 OOM 杀死的偏好。最小可能的值 -1000 相当于完全禁用了对该任务的 OOM 杀死，因为它始终报告的恶劣度评分为 0。

因此，用户空间很容易定义每个任务需要考虑的内存量。例如，设置 /proc/<pid>/oom_score_adj 的值为 +500 大致相当于允许共享相同系统、cgroup、内存策略或内存控制器资源的其他任务使用至少多出 50% 的内存。相反，设置为 -500 大致相当于忽略任务允许使用的 50% 内存，不将其计入评分。

为了与早期内核版本保持向后兼容性，/proc/<pid>/oom_adj 也可以用来调整恶劣度评分。它的可接受值范围是从 -16 (OOM_ADJUST_MIN) 到 +15 (OOM_ADJUST_MAX)，并有一个特殊值 -17 (OOM_DISABLE) 用于完全禁用该任务的 OOM 杀死。其值会线性缩放 /proc/<pid>/oom_score_adj 的值。

/proc/<pid>/oom_score_adj 的值不能低于最后一个具有 CAP_SYS_RESOURCE 权限的进程所设置的值。要降低此值需要 CAP_SYS_RESOURCE 权限。
3.2 /proc/<pid>/oom_score - 显示当前 oom-killer 的评分
-------------------------------------------------------------

此文件可用于检查任何给定 <pid> 的当前 oom-killer 评分。请与 /proc/<pid>/oom_score_adj 一起使用，以调整在内存不足的情况下应该杀死哪个进程。
请注意，导出的值包括 oom_score_adj，因此实际上范围为 [0,2000]。

3.3 /proc/<pid>/io - 显示 IO 统计字段
--------------------------------------

此文件包含每个运行进程的 IO 统计信息。

示例
~~~~~~~

::

    test:/tmp # dd if=/dev/zero of=/tmp/test.dat &
    [1] 3828

    test:/tmp # cat /proc/3828/io
    rchar: 323934931
    wchar: 323929600
    syscr: 632687
    syscw: 632675
    read_bytes: 0
    write_bytes: 323932160
    cancelled_write_bytes: 0

描述
~~~~~~~~~~~

rchar
^^^^^

IO 计数器：读取字符数
此任务导致从存储设备读取的字节数。这仅仅是此进程传递给 read() 和 pread() 的字节总数。
它包括像 tty IO 这样的情况，并且不受实际物理磁盘 IO 是否需要的影响（读操作可能从页面缓存中完成）。

wchar
^^^^^

IO 计数器：写入字符数
此任务导致或将会导致写入磁盘的字节数。与 rchar 类似，这里也有一些注意事项。

syscr
^^^^^

IO 计数器：读取系统调用次数
尝试计算读取 IO 操作的数量，即像 read() 和 pread() 这样的系统调用。

syscw
^^^^^

IO 计数器：写入系统调用次数
尝试计算写入 IO 操作的数量，即像 write() 和 pwrite() 这样的系统调用。

read_bytes
^^^^^^^^^^

IO 计数器：读取字节数
尝试计算此进程实际导致从存储层获取的字节数。在 submit_bio() 层级完成，因此对于基于块的文件系统是准确的。<请稍后添加关于 NFS 和 CIFS 的状态>

write_bytes
^^^^^^^^^^^

IO 计数器：写入字节数
尝试计算此进程导致发送到存储层的字节数。在页变脏时完成。

cancelled_write_bytes
^^^^^^^^^^^^^^^^^^^^^

这里的主要不准确性在于截断。如果一个进程向文件写入了 1MB 数据然后删除了该文件，实际上并不会进行写入操作。但是，它将被记录为导致了 1MB 的写入。
换句话说：这个进程通过截断页缓存导致未发生的字节数。一个任务也可能导致“负”I/O。如果这个任务截断了一些脏页缓存，那么其他任务已经记录在其 `write_bytes` 中的某些 I/O 将不会发生。我们_可以_从截断任务的 `write_bytes` 中减去这部分值，但这样做会导致信息丢失。

注意：

在当前实现状态下，在32位机器上这有点竞争条件问题：如果进程A在进程B更新某个64位计数器时读取进程B的 `/proc/pid/io` 文件，进程A可能会看到一个中间结果。

更多关于此的信息可以在 `Documentation/accounting` 中的任务统计文档中找到。

### 3.4 `/proc/<pid>/coredump_filter` - 核心转储过滤设置
---------------------------------------
当一个进程被转储时，默认情况下所有匿名内存都会写入核心文件，只要核心文件的大小没有限制。但有时我们不想转储某些内存段，例如巨大的共享内存或直接访问内存（DAX）。相反，有时我们希望将基于文件的内存段也保存到核心文件中，而不仅仅是单独的文件。

`/proc/<pid>/coredump_filter` 允许你自定义当 `<pid>` 进程被转储时哪些内存段会被转储。`coredump_filter` 是一个内存类型的位掩码。如果位掩码中的某一位被设置，则相应类型的内存段会被转储；否则它们不会被转储。

支持以下9种内存类型：

  - （位0）匿名私有内存
  - （位1）匿名共享内存
  - （位2）基于文件的私有内存
  - （位3）基于文件的共享内存
  - （位4）基于文件的私有内存区域中的 ELF 头页面（仅在位2未设置时有效）
  - （位5）巨页表（hugetlb）私有内存
  - （位6）巨页表（hugetlb）共享内存
  - （位7）直接访问内存（DAX）私有内存
  - （位8）直接访问内存（DAX）共享内存

请注意，MMIO 页面（如帧缓冲区）永远不会被转储，而 vDSO 页面总是会被转储，无论位掩码的状态如何。

请注意，位0-4不影响巨页表（hugetlb）或直接访问内存（DAX）。巨页表（hugetlb）内存只受位5-6的影响，而直接访问内存（DAX）只受位7-8的影响。

`coredump_filter` 的默认值是 0x33；这意味着所有的匿名内存段、ELF 头页面和巨页表（hugetlb）私有内存都会被转储。

如果你不想转储与进程ID 1234相关联的所有共享内存段，可以向该进程的 `proc` 文件写入 0x31 ：

```
$ echo 0x31 > /proc/1234/coredump_filter
```

当创建新进程时，进程会继承其父进程的位掩码状态。在程序运行前设置 `coredump_filter` 是有用的。
例如：

```
$ echo 0x7 > /proc/self/coredump_filter
$ ./some_program
```

3.5 `/proc/<pid>/mountinfo` - 挂载信息
----------------------------------------

此文件包含以下形式的行：

```
36 35 98:0 /mnt1 /mnt2 rw,noatime master:1 - ext3 /dev/root rw,errors=continue
(1)(2)(3)   (4)   (5)      (6)     (n…m) (m+1)(m+2) (m+3)         (m+4)
```

- (1) 挂载ID：挂载的唯一标识符（卸载后可能会被重用）
- (2) 父级ID：父级ID（或在挂载树顶部时为自身ID）
- (3) 主设备号:次设备号：文件系统上文件的st_dev值
- (4) 根目录：文件系统内的挂载根
- (5) 挂载点：相对于进程根目录的挂载点
- (6) 挂载选项：每个挂载的选项
- (n…m) 可选字段：零个或多个形如"标签[:值]"的字段
- (m+1) 分隔符：标记可选字段的结束
- (m+2) 文件系统类型：形如"type[.subtype]"的文件系统名称
- (m+3) 挂载源：特定于文件系统的附加信息或"none"
- (m+4) 超级块选项：超级块的选项

解析器应忽略所有未识别的可选字段。目前可能的可选字段如下：

- shared:X：挂载在对等组X中共享
- master:X：挂载作为对等组X的从属
- propagate_from:X：挂载作为从属并从对等组X接收传播
- unbindable：挂载不可绑定

.. [#] X 是进程根目录下最近的主导对等组。如果X是挂载的直接主对等组，或者在同一根目录下没有主导对等组，则仅存在"master:X"字段，而不存在"propagate_from:X"字段。

关于挂载传播的更多信息，请参阅：

  `Documentation/filesystems/sharedsubtree.rst`

3.6 `/proc/<pid>/comm` 与 `/proc/<pid>/task/<tid>/comm`
--------------------------------------------------------

这些文件提供了一种访问任务的comm值的方法，并允许任务设置其自身的或线程兄弟的comm值。comm值的大小比cmdline值有限制，因此写入任何超过内核TASK_COMM_LEN（目前为16个字符，包括NUL终止符）的内容将导致comm值被截断。

3.7 `/proc/<pid>/task/<tid>/children` - 任务子项信息
----------------------------------------------------------

此文件提供了快速获取由<pid>/<tid>对指向的任务的一级子PID的方法。格式是一个以空格分隔的PID流。
请注意这里的“一级”——如果一个子项有自己的子项，它们将不会在此处列出；需要读取`/proc/<children-pid>/task/<tid>/children`来获取后代。
由于此接口旨在快速且廉价地工作，因此它不保证提供精确的结果，某些子项可能会被跳过，特别是在它们退出后立即打印它们的PID时。如果需要精确的结果，必须停止或冻结正在检查的过程。

3.8 `/proc/<pid>/fdinfo/<fd>` - 打开文件的信息
---------------------------------------------------------------

此文件提供了与打开文件相关联的信息。常规文件至少有四个字段——'pos'、'flags'、'mnt_id'和'ino'。
'pos'表示打开文件的当前偏移量（以十进制形式表示），详情请参见lseek(2)；'flags'表示创建文件时使用的八进制O_xxx掩码（详情请参见open(2)）；'mnt_id'表示包含打开文件的文件系统的挂载ID（详情请参见3.5 `/proc/<pid>/mountinfo`）。'ino'表示文件的inode号。

典型输出如下：

```
pos:	0
flags:	0100002
mnt_id:	19
ino:	63107
```

与文件描述符相关的所有锁也会显示在其fdinfo中：

```
lock:       1: FLOCK  ADVISORY  WRITE 359 00:13:11691 0 EOF
```

诸如eventfd、fsnotify、signalfd、epoll等文件除了常规的pos/flags对之外，还提供了与其所代表对象特有的附加信息。

Eventfd文件
~~~~~~~~~~~~~

```
pos:	0
flags:	04002
mnt_id:	9
ino:	63107
eventfd-count:	5a
```

其中 'eventfd-count' 是计数器的十六进制值。

Signalfd文件
~~~~~~~~~~~~~~

```
pos:	0
flags:	04002
mnt_id:	9
ino:	63107
sigmask:	0000000000000200
```

其中 'sigmask' 是与文件关联的信号掩码的十六进制值。
### Epoll 文件
~~~~~~~~~~~

```
pos:	0
flags:	02
mnt_id:	9
ino:	63107
tfd:        5 events:       1d data: ffffffffffffffff pos:0 ino:61af sdev:7
```

其中 'tfd' 是以十进制形式表示的目标文件描述符编号，'events' 是正在监视的事件掩码，'data' 是与目标相关联的数据（详见 `epoll(7)`）。'pos' 是目标文件当前的偏移量（以十进制形式表示）（详见 `lseek(2)`），'ino' 和 'sdev' 是目标文件所在的inode和设备号（以十六进制形式表示）。

### Fsnotify 文件
~~~~~~~~~~~~~~
对于 inotify 文件，格式如下：

```
pos:	0
flags:	02000000
mnt_id:	9
ino:	63107
inotify wd:3 ino:9e7e sdev:800013 mask:800afce ignored_mask:0 fhandle-bytes:8 fhandle-type:1 f_handle:7e9e0000640d1b6d
```

其中 'wd' 是以十进制形式表示的监视描述符，即目标文件描述符编号，'ino' 和 'sdev' 是目标文件所在的inode和设备号，'mask' 是事件掩码（详见 `inotify(7)`）。所有这些值都以十六进制形式表示。如果内核支持 `exportfs`，则目标文件的路径会编码为一个文件句柄。文件句柄由三个字段 'fhandle-bytes'、'fhandle-type' 和 'f_handle' 组成，所有这些字段都以十六进制形式表示。如果内核不支持 `exportfs`，则不会打印出文件句柄。如果没有附加 inotify 标记，则会省略 'inotify' 行。

### Fanotify 文件
~~~~~~~~~~~~~~
对于 fanotify 文件，格式如下：

```
pos:	0
flags:	02
mnt_id:	9
ino:	63107
fanotify flags:10 event-flags:0
fanotify mnt_id:12 mflags:40 mask:38 ignored_mask:40000003
fanotify ino:4f969 sdev:800013 mflags:0 mask:3b ignored_mask:40000000 fhandle-bytes:8 fhandle-type:1 f_handle:69f90400c275b5b4
```

其中 'fanotify flags' 和 'event-flags' 是在调用 `fanotify_init` 时使用的值，'mnt_id' 是挂载点标识符，'mflags' 是与标记关联的标志值，这些标志值与事件掩码分开跟踪。'ino' 和 'sdev' 是目标inode和设备，'mask' 是事件掩码，'ignored_mask' 是要忽略的事件掩码。所有这些值都以十六进制形式表示。'mflags'、'mask' 和 'ignored_mask' 的结合提供了 `fanotify_mark` 调用中使用的标志和掩码信息（详见 `fsnotify` 手册页）。

前三个行是强制性的并且始终打印，其余部分是可选的，并且可能在没有创建标记的情况下被省略。

### Timerfd 文件
~~~~~~~~~~~~~~

```
pos:	0
flags:	02
mnt_id:	9
ino:	63107
clockid: 0
ticks: 0
settime flags: 01
it_value: (0, 49406829)
it_interval: (1, 0)
```

其中 'clockid' 是时钟类型，'ticks' 是已发生的定时器到期次数（详见 `timerfd_create(2)`）。'settime flags' 是用于设置定时器的标志（以八进制形式表示）（详见 `timerfd_settime(2)`）。'it_value' 是定时器到期前剩余的时间。
`it_interval` 是定时器的时间间隔。请注意，定时器可能使用了 `TIMER_ABSTIME` 选项进行设置，这将在 `settime flags` 中显示，但 `it_value` 仍然表示定时器的剩余时间。

DMA 缓冲区文件
~~~~~~~~~~~~~~

::

    pos: 0
    flags: 04002
    mnt_id: 9
    ino: 63107
    size: 32768
    count: 2
    exp_name: system-heap

其中 `size` 表示 DMA 缓冲区的大小（以字节为单位），`count` 表示 DMA 缓冲区文件的数量，`exp_name` 表示 DMA 缓冲区导出器的名称。

3.9 `/proc/<pid>/map_files` — 内存映射文件信息
----------------------------------------------

此目录包含表示进程维护的内存映射文件的符号链接。示例输出如下：

::

    | lr-------- 1 root root 64 Jan 27 11:24 333c600000-333c620000 -> /usr/lib64/ld-2.18.so
    | lr-------- 1 root root 64 Jan 27 11:24 333c81f000-333c820000 -> /usr/lib64/ld-2.18.so
    | lr-------- 1 root root 64 Jan 27 11:24 333c820000-333c821000 -> /usr/lib64/ld-2.18.so
    | ..
    | lr-------- 1 root root 64 Jan 27 11:24 35d0421000-35d0422000 -> /usr/lib64/libselinux.so.1
    | lr-------- 1 root root 64 Jan 27 11:24 400000-41a000 -> /usr/bin/ls

链接的名称表示内存映射的虚拟地址范围，即 `vm_area_struct::vm_start` 到 `vm_area_struct::vm_end`。`map_files` 的主要目的是快速检索一组内存映射文件，而不是解析 `/proc/<pid>/maps` 或 `/proc/<pid>/smaps`，这两者包含更多的记录。同时，可以从两个进程的列表中打开映射，并通过比较它们的inode编号来确定哪些匿名内存区域实际上是共享的。

3.10 `/proc/<pid>/timerslack_ns` — 任务的 timerslack 值
--------------------------------------------------------

此文件提供了任务的 timerslack 值（以纳秒为单位）。此值指定了正常定时器可以延迟的时间量，以便合并定时器并避免不必要的唤醒。

这允许调整任务的交互性与功耗之间的权衡。
向该文件写入 0 将把任务的 timerslack 设置为默认值。
有效值范围为 0 - ULLONG_MAX。

设置该值的应用程序必须对指定任务具有 PTRACE_MODE_ATTACH_FSCREDS 级别的权限，以更改其 timerslack_ns 值。

3.11 /proc/<pid>/patch_state - 实时补丁操作状态
------------------------------------------------
当启用 CONFIG_LIVEPATCH 时，此文件显示任务的补丁状态。
-1 表示没有补丁正在过渡中。
0 表示补丁正在过渡中且任务未打补丁。如果启用补丁，则任务尚未打补丁；如果禁用补丁，则任务已经取消补丁。
1 表示补丁正在过渡中且任务已打补丁。如果启用补丁，则任务已经打补丁；如果禁用补丁，则任务尚未取消补丁。

3.12 /proc/<pid>/arch_status - 任务架构特定状态
-------------------------------------------------
当启用 CONFIG_PROC_PID_ARCH_STATUS 时，此文件显示任务的架构特定状态。

示例
~~~~~~~

::

 $ cat /proc/6753/arch_status
 AVX512 elapsed_ms:      8

描述
~~~~~~~~~~~

x86 特定条目
~~~~~~~~~~~~~~~~~~~~~

AVX512 elapsed_ms
^^^^^^^^^^^^^^^^^^

如果机器支持 AVX512，则此条目显示自上次记录 AVX512 使用情况以来经过的毫秒数。记录是在任务调度出时尽力而为地进行的。这意味着该值取决于两个因素：

1) 任务在未被调度出的情况下在 CPU 上运行的时间。如果有 CPU 隔离和单个可运行的任务，这可能需要几秒钟。
2) 自从任务上次被调度出以来的时间。根据调度出的原因（时间片耗尽、系统调用等），这可能是任意长的时间。
因此，该值不能被视为精确和权威的信息。使用此信息的应用程序需要了解系统的整体情况，才能确定一个任务是否是真正的 AVX512 用户。通过性能计数器可以获得精确信息。
-1 的特殊值表示没有记录到 AVX512 的使用情况，因此任务很可能不是 AVX512 用户，但根据工作负载和调度情况，这也可能是上述假阴性的情况。
3.13 /proc/<pid>/fd - 打开文件的符号链接列表
-------------------------------------------------------
此目录包含表示进程维护的打开文件的符号链接。示例输出如下：

```
lr-x------ 1 root root 64 Sep 20 17:53 0 -> /dev/null
l-wx------ 1 root root 64 Sep 20 17:53 1 -> /dev/null
lrwx------ 1 root root 64 Sep 20 17:53 10 -> 'socket:[12539]'
lrwx------ 1 root root 64 Sep 20 17:53 11 -> 'socket:[12540]'
lrwx------ 1 root root 64 Sep 20 17:53 12 -> 'socket:[12542]'
```

进程的打开文件数量存储在`/proc/<pid>/fd`的`stat()`输出中的`size`成员中，以便快速访问。

-------------------------------------------------------

第4章：配置procfs
=============================

4.1 挂载选项
---------------------

支持以下挂载选项：

| 选项       | 描述                                                         |
|------------|--------------------------------------------------------------|
| hidepid=   | 设置`/proc/<pid>/`的访问模式                                   |
| gid=       | 设置有权获取进程信息的组                                       |
| subset=    | 仅显示指定的procfs子集                                         |

`hidepid=off`或`hidepid=0`意味着经典模式——任何人都可以访问所有`/proc/<pid>/`目录（默认）。
`hidepid=noaccess`或`hidepid=1`意味着用户不能访问任何非自己拥有的`/proc/<pid>/`目录。敏感文件如`cmdline`、`sched*`和`status`现在对其他用户受到保护。这使得无法得知任何用户是否运行了特定程序（除非该程序通过其行为暴露自己）。作为额外的好处，由于`/proc/<pid>/cmdline`对其他用户不可访问，那些通过程序参数传递敏感信息的编写不佳的程序现在也受到本地窃听者的保护。
`hidepid=invisible`或`hidepid=2`意味着`hidepid=1`加上所有`/proc/<pid>/`对其他用户完全不可见。这并不意味着隐藏某个特定`pid`值的进程是否存在（可以通过其他方式得知，例如使用`kill -0 $PID`），但它隐藏了进程的`uid`和`gid`，这些信息通常可以通过对`/proc/<pid>/`执行`stat()`操作来获取。这大大增加了入侵者收集有关正在运行的进程的信息的难度，包括是否某个守护进程以提升的权限运行，其他用户是否运行了某些敏感程序，其他用户是否运行了任何程序等。
`hidepid=ptraceable`或`hidepid=4`意味着procfs应该只包含调用者能够ptrace的`/proc/<pid>/`目录。
`gid=`定义了一个有权获取通常被`hidepid=`禁止的进程信息的组。如果你使用像identd这样的守护进程，需要获取进程信息，只需将identd添加到这个组中。
`subset=pid` 会隐藏 `procfs` 中与任务无关的所有顶级文件和目录。

第 5 章：文件系统行为
==============================

最初，在引入 PID 命名空间之前，`procfs` 是一个全局文件系统。这意味着系统中只有一个 `procfs` 实例。当添加了 PID 命名空间后，在每个 PID 命名空间内都挂载了一个独立的 `procfs` 实例。因此，`procfs` 的挂载选项在整个命名空间内的所有挂载点上都是全局性的：

```
# grep ^proc /proc/mounts
proc /proc proc rw,relatime,hidepid=2 0 0

# strace -e mount mount -o hidepid=1 -t proc proc /tmp/proc
mount("proc", "/tmp/proc", "proc", 0, "hidepid=1") = 0
+++ exited with 0 +++

# grep ^proc /proc/mounts
proc /proc proc rw,relatime,hidepid=2 0 0
proc /tmp/proc proc rw,relatime,hidepid=2 0 0
```

只有在重新挂载 `procfs` 后，挂载选项才会在所有挂载点上生效：

```
# mount -o remount,hidepid=1 -t proc proc /tmp/proc

# grep ^proc /proc/mounts
proc /proc proc rw,relatime,hidepid=1 0 0
proc /tmp/proc proc rw,relatime,hidepid=1 0 0
```

这种行为与其他文件系统的行为不同。新的 `procfs` 行为更类似于其他文件系统。每次 `procfs` 挂载都会创建一个新的 `procfs` 实例。挂载选项只影响自身的 `procfs` 实例。这意味着现在可以在同一个 PID 命名空间内拥有多个显示不同过滤选项的任务的 `procfs` 实例：

```
# mount -o hidepid=invisible -t proc proc /proc
# mount -o hidepid=noaccess -t proc proc /tmp/proc
# grep ^proc /proc/mounts
proc /proc proc rw,relatime,hidepid=invisible 0 0
proc /tmp/proc proc rw,relatime,hidepid=noaccess 0 0
```
