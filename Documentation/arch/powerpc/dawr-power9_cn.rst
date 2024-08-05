POWER9上的DAWR问题
=====================

在较旧的POWER9处理器上，数据地址监视寄存器（DAWR）如果指向缓存抑制（CI）内存，则可能会导致系统停止检查。目前Linux没有方法来区分配置DAWR时的CI内存，因此在受影响的系统中，将禁用DAWR。

受影响的处理器修订版本
============================

此问题仅存在于修订版本小于v2.3的处理器上。可以在`/proc/cpuinfo`中找到修订版本的信息：

    processor       : 0
    cpu             : POWER9, 支持altivec
    clock           : 3800.000000MHz
    revision        : 2.3 (pvr 004e 1203)

在存在该问题的系统上，将按如下所述禁用DAWR。

技术细节：
==================

DAWR可以通过六种不同的方式设置：
1) ptrace
2) h_set_mode(DAWR)
3) h_set_dabr()
4) kvmppc_set_one_reg()
5) xmon

对于ptrace，我们通过PPC_PTRACE_GETHWDBGINFO调用告知在POWER9上不存在断点。这会导致GDB回退到软件模拟监视点（速度较慢）。
h_set_mode(DAWR)和h_set_dabr()现在将在POWER9主机上向客户机返回错误。当前的Linux客户机会忽略这个错误，因此它们将无法获取DAWR。
kvmppc_set_one_reg()将在vcpu中存储值，但在POWER9硬件上不会真正设置它。这样做是为了确保从POWER8迁移到POWER9时不出现问题，代价是迁移过程中会默默地丢失DAWR。
对于xmon，'bd'命令将在P9上返回错误。

对用户的影响
======================

对于在POWER9裸金属服务器上使用GDB监视点（即'watch'命令），GDB将接受该命令。不幸的是，由于没有硬件支持监视点，GDB将通过软件模拟监视点，这会使运行变得非常缓慢。
同样，对于任何在POWER9主机上启动的客户机，监视点将失败并且GDB将回退到软件模拟。
如果客户机在POWER8主机上启动，GDB将接受监视点并配置硬件以使用DAWR。这将以全速运行，因为它可以使用硬件模拟。不幸的是，如果该客户机迁移到POWER9主机，监视点将在POWER9上丢失。对监视点位置的加载和存储操作将不会被GDB捕获。监视点会被记住，所以如果客户机迁回到POWER8主机，它将重新开始工作。
强制启用 DAWR
=======================
内核（自大约 v5.2 版本起）提供了一个选项，可以强制启用 DAWR，方法是：

  `echo Y > /sys/kernel/debug/powerpc/dawr_enable_dangerous`

这会在包括 POWER9 在内的系统上启用 DAWR。
这是一个危险的设置，请自行承担风险使用。
某些用户可能不介意因用户操作不当导致系统崩溃（例如，在单用户/桌面系统中），他们非常希望启用 DAWR。此选项允许他们强制启用 DAWR。
此标志也可以用于禁用对 DAWR 的访问。一旦取消此设置，所有对 DAWR 的访问都应立即被清除，并且您的机器将再次免受崩溃威胁。
用户空间可能会因为切换此选项而感到困惑。如果在获取断点数量（通过 PTRACE_GETHWDBGINFO）和设置断点之间强制启用了 DAWR 或禁用了 DAWR，用户空间将获得一个不一致的视图。对于客户机同样适用。
要在 KVM 客户机中启用 DAWR，需要在主机和客户机中都强制启用 DAWR。由于这个原因，在 POWERVM 上无法工作，因为它不允许 HCALL 正常运行。如果虚拟机监视器不支持写入 DAWR，则向 dawr_enable_dangerous 文件写入 'Y' 将会失败。
要验证 DAWR 是否正常工作，可以运行以下内核自检程序：

  `tools/testing/selftests/powerpc/ptrace/ptrace-hwbreak.c`

任何错误、失败或跳过的情况都表明存在问题。
