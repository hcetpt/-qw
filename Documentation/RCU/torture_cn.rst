SPDX 许可证标识符: GPL-2.0

==========================
RCU 折磨测试操作
==========================

CONFIG_RCU_TORTURE_TEST
=======================

CONFIG_RCU_TORTURE_TEST 配置选项适用于所有 RCU 实现。它创建了一个名为 rcutorture 的内核模块，可以加载该模块来运行折磨测试。测试会周期性地通过 printk() 输出状态信息，这些信息可以通过 dmesg 命令（可能需要搜索 "torture"）查看。当模块被加载时，测试开始；当模块卸载时，测试停止。模块参数在 Documentation/admin-guide/kernel-parameters.txt 中以 "rcutorture." 为前缀。
输出
======

统计输出如下所示：

```
rcu-torture:--- Start of test: nreaders=16 nfakewriters=4 stat_interval=30 verbose=0 test_no_idle_hz=1 shuffle_interval=3 stutter=5 irqreader=1 fqs_duration=0 fqs_holdoff=0 fqs_stutter=3 test_boost=1/0 test_boost_interval=7 test_boost_duration=4
rcu-torture: rtc:           (null) ver: 155441 tfle: 0 rta: 155441 rtaf: 8884 rtf: 155440 rtmbe: 0 rtbe: 0 rtbke: 0 rtbre: 0 rtbf: 0 rtb: 0 nt: 3055767
rcu-torture: Reader Pipe:  727860534 34213 0 0 0 0 0 0 0 0 0
rcu-torture: Reader Batch:  727877838 17003 0 0 0 0 0 0 0 0 0
rcu-torture: Free-Block Circulation:  155440 155440 155440 155440 155440 155440 155440 155440 155440 155440 0
rcu-torture:--- End of test: SUCCESS: nreaders=16 nfakewriters=4 stat_interval=30 verbose=0 test_no_idle_hz=1 shuffle_interval=3 stutter=5 irqreader=1 fqs_duration=0 fqs_holdoff=0 fqs_stutter=3 test_boost=1/0 test_boost_interval=7 test_boost_duration=4
```

大多数系统上，命令 "dmesg | grep torture:" 可以提取这些信息。在更复杂的配置中，可能需要使用其他命令来访问 RCU 折磨测试使用的 printk() 输出。这些 printk() 使用 KERN_ALERT，因此应该很明显。;-)

第一行和最后一行显示了 rcutorture 模块的参数，最后一行显示了 "SUCCESS" 或 "FAILURE"，这是根据 rcutorture 自动判断 RCU 是否正确运行的结果。条目解释如下：

* "rtc"：当前对读者可见的结构体的十六进制地址。
* "ver"：自启动以来，RCU 写入任务更改对读者可见的结构体的次数。
* "tfle"：如果非零，则表示包含要放入 "rtc" 区域的结构体的 "折折磨列表" 已为空。这种情况很重要，因为它可能会误导你认为 RCU 正常工作，而实际上并非如此。 :-/
* "rta"：从折磨列表分配的结构体数量。
* "rtaf"：由于列表为空而导致的分配失败次数。这个值不为零是正常的，但如果它是 "rta" 值的一个大比例，则不好。
* "rtf"：释放到折磨列表的结构体数量。
* "rtmbe"：非零值表示 rcutorture 认为 rcu_assign_pointer() 和 rcu_dereference() 没有正常工作。此值应为零。
* “rtbe”：非零值表示rcu_barrier()函数族中的某个函数工作不正常。
* “rtbke”：rcutorture无法创建用于强制RCU优先级反转的实时kthreads。此值应为零。
* “rtbre”：尽管rcutorture成功创建了用于强制RCU优先级反转的kthreads，但无法将它们设置为实时优先级级别1。此值应为零。
* “rtbf”：RCU优先级提升未能解决RCU优先级反转的次数。
* “rtb”：rcutorture尝试强制RCU优先级反转条件的次数。如果您通过“test_boost”模块参数测试RCU优先级提升，此值应为非零。
* “nt”：rcutorture在定时器处理程序内运行RCU读取侧代码的次数。如果指定了“irqreader”模块参数，此值应为非零。
* “Reader Pipe”：读者所见结构的“年龄”直方图。如果除了前两个条目之外还有其他非零条目，则表明RCU存在问题。rcutorture会打印错误标志字符串“!!!”，以确保您注意到这一点。新分配的结构的年龄为零，在从读者可见性中移除后变为1，并且随后每个宽限期递增一次——并在经过（RCU_TORTURE_PIPE_LEN-2）个宽限期后被释放。
上面显示的输出来自一个正确工作的RCU。如果您想看看它在出错时的样子，请自己破坏它。;-)

* “Reader Batch”：另一个关于读者所见结构“年龄”的直方图，但它是基于计数器翻转（或批次），而不是基于宽限期。合法的非零条目的数量仍然是两个。提供这个单独视图的原因是，有时让第三个条目在“Reader Batch”列表中出现比在“Reader Pipe”列表中更容易。
* “Free-Block 流通”：显示达到管道中某个点的折磨结构的数量。第一个元素应与分配的结构数量紧密对应，第二个元素应与已从读者视图中移除的数量相对应，其余所有但最后一个元素应对应于通过宽限期的相应次数。最后一个条目应为零，因为只有在某个折磨结构的计数器以某种方式超出其应有的范围时才会递增。
不同的 RCU 实现可以提供特定于实现的附加信息。例如，Tree SRCU 提供了以下附加行：

```
srcud-torture: Tree SRCU 每个 CPU(idx=0): 0(35,-21) 1(-4,24) 2(1,1) 3(-26,20) 4(28,-47) 5(-9,4) 6(-10,14) 7(-14,11) T(1,6)
```

此行显示了每个 CPU 的计数器状态，在这种情况下是使用动态分配的 `srcu_struct`（因此使用 "srcud-" 而不是 "srcu-"）。括号中的数字是对应 CPU 的“旧”和“当前”计数器的值。“idx”值将“旧”和“当前”值映射到底层数组，并且在调试时很有用。最后的“T”条目包含计数器的总计。

特定内核构建上的使用
=================

有时希望对特定内核构建上的 RCU 进行折磨测试，例如，在准备将该内核构建投入生产时。在这种情况下，应使用 `CONFIG_RCU_TORTURE_TEST=m` 来编译内核，以便使用 `modprobe` 启动测试并使用 `rmmod` 终止测试。例如，可以使用以下脚本对 RCU 进行折磨测试：

```sh
#!/bin/sh

modprobe rcutorture
sleep 3600
rmmod rcutorture
dmesg | grep torture:
```

输出可以通过手动检查“!!!”错误标志。当然，也可以创建一个更复杂的脚本来自动检查此类错误。“rmmod”命令会强制打印出“SUCCESS”，“FAILURE”或“RCU_HOTPLUG”的指示。前两个不言自明，而最后一个则表示虽然没有 RCU 失败，但检测到了 CPU 热插拔问题。

主线内核上的使用
================

当使用 `rcutorture` 测试 RCU 本身的变化时，通常需要构建多个内核来测试该变化在相关 Kconfig 选项组合及相关的内核引导参数下的表现。在这种情况下，使用 `modprobe` 和 `rmmod` 可能既耗时又容易出错。因此，提供了 `tools/testing/selftests/rcutorture/bin/kvm.sh` 脚本用于主线测试 x86、arm64 和 powerpc 架构。默认情况下，它将在一个使用自动生成的 initrd 提供最小用户空间的来宾操作系统中运行由 `tools/testing/selftests/rcutorture/configs/rcu/CFLIST` 指定的一系列测试，每个测试运行 30 分钟。测试完成后，分析生成的构建产物和控制台输出以查找错误，并总结运行结果。

在更大的系统上，可以通过向 `kvm.sh` 传递 `--cpus` 参数来加速 `rcutorture` 测试。例如，在 64 核系统上，`--cpus 43` 将使用最多 43 个 CPU 并行运行测试，截至第 5.4 版，这可以在两批中完成所有场景，将完成时间从大约八小时缩短到大约一小时（不包括构建十六个内核的时间）。`--dryrun sched` 参数不会运行测试，而是告诉您如何将测试调度成批次。这在确定 `--cpus` 参数中指定多少个 CPU 时非常有用。

并非所有的更改都需要运行所有场景。例如，对 Tree SRCU 的更改可能仅使用 `--configs` 参数运行 `SRCU-N` 和 `SRCU-P` 场景，如下所示：`"--configs 'SRCU-N SRCU-P'"`。
大型系统可以运行多个完整场景集的副本，例如，一个具有448个硬件线程的系统可以同时运行五个完整的场景集实例。要实现这一点：

```
kvm.sh --cpus 448 --configs '5*CFLIST'
```

另外，这样的系统也可以同时运行56个单个八核场景的实例：

```
kvm.sh --cpus 448 --configs '56*TREE04'
```

或者同时运行两个八核场景各28个实例：

```
kvm.sh --cpus 448 --configs '28*TREE03 28*TREE04'
```

当然，每个并发实例都会使用内存，可以通过`--memory`参数来限制，默认值为512M。较小的内存值可能需要通过下面讨论的`--bootargs`参数禁用回调泛洪测试。
有时额外的调试是有用的，在这种情况下可以使用`kvm.sh`脚本中的`--kconfig`参数，例如，``--kconfig 'CONFIG_RCU_EQS_DEBUG=y'``。此外，还有`--gdb`、`--kasan`和`--kcsan`参数。
请注意，`--gdb`参数将限制您在每次`kvm.sh`运行中只能有一个场景，并且需要在另一个窗口中按照脚本指示运行`gdb`。
内核启动参数也可以提供，例如，用于控制`rcutorture`模块参数。例如，为了测试对RCU的CPU停顿警告代码的更改，可以使用`"--bootargs 'rcutorture.stall_cpu=30'"`。这当然会导致脚本报告失败，即RCU CPU停顿警告。如上所述，减少内存可能需要禁用`rcutorture`的回调泛洪测试：

```
kvm.sh --cpus 448 --configs '56*TREE04' --memory 128M \
    --bootargs 'rcutorture.fwd_progress=0'
```

有时只需要一整套内核构建。这就是`--buildonly`参数的作用。
`--duration`参数可以覆盖默认的30分钟运行时间。例如，`--duration 2d`将运行两天，`--duration 3h`将运行三小时，`--duration 5m`将运行五分钟，而`--duration 45s`将运行45秒。最后一种情况对于追踪罕见的启动时故障很有用。
最后，`--trust-make`参数允许每个内核构建重用前一个内核构建的结果。请注意，如果没有`--trust-make`参数，您的标签文件可能会被破坏。
`kvm.sh`脚本源代码中还记录了更多复杂的参数。
如果运行过程中出现失败，构建时间和运行时间的失败次数将列在 kvm.sh 输出的末尾，你确实应该将其重定向到一个文件中。每次运行的构建产物和控制台输出都保存在 `tools/testing/selftests/rcutorture/res` 目录下的按时间戳命名的子目录中。可以将特定目录提供给 `kvm-find-errors.sh` 脚本，以便循环显示错误摘要和完整的错误日志。例如：

```
tools/testing/selftests/rcutorture/bin/kvm-find-errors.sh \
    tools/testing/selftests/rcutorture/res/2020.01.20-15.54.23
```

然而，直接访问这些文件通常更为方便。一次运行中所有场景相关的文件都存放在顶层目录中（如上例中的 `2020.01.20-15.54.23`），而每个场景相关的文件则存放在以场景命名的子目录中（例如，“TREE04”）。如果某个场景运行了多次（如上面的 `--configs '56*TREE04'`），该场景第二次及之后运行对应的目录会包含一个序列号，例如，“TREE04.2”，“TREE04.3”等。

顶层目录中最常用的文件是 `testid.txt`。如果测试是在 Git 仓库中进行的，那么这个文件包含被测试的提交以及任何未提交的更改的 diff 格式信息。

每个场景运行目录中最常用的文件包括：

- `.config`：此文件包含 Kconfig 选项。
- `Make.out`：此文件包含特定场景的构建输出。
- `console.log`：此文件包含特定场景的控制台输出。此文件可以在内核启动后检查，但如果构建失败，则可能不存在。
- `vmlinux`：此文件包含内核，可用于 `objdump` 和 `gdb` 等工具。

还有一些其他文件可用，但使用频率较低。
许多测试是用于调试 `rcutorture` 本身或其脚本的。截至第 5.4 版，在一个 12 核系统上，默认场景集的成功运行会在运行结束时生成以下摘要：

    SRCU-N ------- 804233 个 GP (148.932/s) [srcu: g10008272 f0x0]
    SRCU-P ------- 202320 个 GP (37.4667/s) [srcud: g1809476 f0x0]
    SRCU-t ------- 1122086 个 GP (207.794/s) [srcu: g0 f0x0]
    SRCU-u ------- 1111285 个 GP (205.794/s) [srcud: g1 f0x0]
    TASKS01 ------- 19666 个 GP (3.64185/s) [tasks: g0 f0x0]
    TASKS02 ------- 20541 个 GP (3.80389/s) [tasks: g0 f0x0]
    TASKS03 ------- 19416 个 GP (3.59556/s) [tasks: g0 f0x0]
    TINY01 ------- 836134 个 GP (154.84/s) [rcu: g0 f0x0] n_max_cbs: 34198
    TINY02 ------- 850371 个 GP (157.476/s) [rcu: g0 f0x0] n_max_cbs: 2631
    TREE01 ------- 162625 个 GP (30.1157/s) [rcu: g1124169 f0x0]
    TREE02 ------- 333003 个 GP (61.6672/s) [rcu: g2647753 f0x0] n_max_cbs: 35844
    TREE03 ------- 306623 个 GP (56.782/s) [rcu: g2975325 f0x0] n_max_cbs: 1496497
    CPU 数量从 16 减少到 12
    TREE04 ------- 246149 个 GP (45.5831/s) [rcu: g1695737 f0x0] n_max_cbs: 434961
    TREE05 ------- 314603 个 GP (58.2598/s) [rcu: g2257741 f0x2] n_max_cbs: 193997
    TREE07 ------- 167347 个 GP (30.9902/s) [rcu: g1079021 f0x0] n_max_cbs: 478732
    CPU 数量从 16 减少到 12
    TREE09 ------- 752238 个 GP (139.303/s) [rcu: g13075057 f0x0] n_max_cbs: 99011

重复运行
========

假设你正在追踪一个罕见的启动失败问题。虽然你可以使用 `kvm.sh`，但这样做会在每次运行时重新构建内核。如果你需要（例如）1000次运行来确信你已经修复了这个错误，那么这些无意义的重新构建可能会变得非常烦人。这就是为什么 `kvm-again.sh` 存在的原因。
假设之前的一次 `kvm.sh` 运行将输出留在了这个目录中：

	tools/testing/selftests/rcutorture/res/2022.11.03-11.26.28

然后可以按如下方式重新运行而不需重新构建：

	kvm-again.sh tools/testing/selftests/rcutorture/res/2022.11.03-11.26.28

原始运行的一些 `kvm.sh` 参数可能会被覆盖，最显著的可能是 `--duration` 和 `--bootargs`。例如：

	kvm-again.sh tools/testing/selftests/rcutorture/res/2022.11.03-11.26.28 \
		--duration 45s

这将重新运行之前的测试，但只持续 45 秒，从而有助于追踪上述罕见的启动失败。

分布式运行
==========

尽管 `kvm.sh` 非常有用，但它的测试仅限于单个系统。使用你喜欢的框架来使（例如）5 个实例的 `kvm.sh` 在你的 5 个系统上运行并不难，但这很可能会不必要的重新构建内核。此外，手动分配所需的 `rcutorture` 场景到可用系统上可能既费时又容易出错。
这就是为什么存在 `kvm-remote.sh` 脚本的原因。
如果你可以执行以下命令：

	ssh system0 date

并且对于 system1、system2、system3、system4 和 system5 也可以执行，并且所有这些系统都有 64 个 CPU，那么你可以输入：

	kvm-remote.sh "system0 system1 system2 system3 system4 system5" \
		--cpus 64 --duration 8h --configs "5*CFLIST"

这将在本地系统上为每个默认场景构建内核，然后将每个场景的五个实例分布在列出的系统上，每个场景运行八小时。在运行结束后，结果将被收集、记录并打印出来。大多数 `kvm.sh` 可以接受的参数都可以传递给 `kvm-remote.sh`，但系统的列表必须放在第一位。
`kvm.sh` 的 `--dryrun scenarios` 参数对于确定一组系统上可以运行多少个场景非常有用。
你还可以像 `kvm.sh` 一样重新运行之前的远程运行：

	kvm-remote.sh "system0 system1 system2 system3 system4 system5" \
		tools/testing/selftests/rcutorture/res/2022.11.03-11.26.28-remote \
		--duration 24h

在这种情况下，大多数 `kvm-again.sh` 参数可以在旧的运行结果目录路径名之后提供。
