SPDX 许可证标识符: GPL-2.0

==============
KVM CPUID 位
==============

:作者: Glauber Costa <glommer@gmail.com>

在 KVM 主机上运行的客户机可以通过 `cpuid` 检查其某些特性。这并不总是保证有效，因为用户空间可以在启动客户机之前屏蔽掉一些或所有与 KVM 相关的 `cpuid` 特性。
KVM 的 `cpuid` 函数如下：

函数: KVM_CPUID_SIGNATURE (0x40000000)

返回值为:

   eax = 0x40000001
   ebx = 0x4b4d564b
   ecx = 0x564b4d56
   edx = 0x4d

请注意，ebx、ecx 和 edx 中的值对应字符串 "KVMKVMKVM"。
eax 中的值对应此叶节点中最大的 `cpuid` 函数，并将在未来添加更多功能时更新。
请注意，旧主机将 eax 值设置为 0x0。这应被解释为该值为 0x40000001。
此函数查询 KVM `cpuid` 叶节点的存在。

函数: 定义 KVM_CPUID_FEATURES (0x40000001)

返回值为:

          ebx, ecx
          eax = 各个 (1 << flag) 的或运算结果

其中 `flag` 定义如下：

| 标志 | 值 | 含义 |
| --- | --- | --- |
| KVM_FEATURE_CLOCKSOURCE | 0 | kvmclock 可用在 msrs 0x11 和 0x12 上 |
| KVM_FEATURE_NOP_IO_DELAY | 1 | 不需要对 PIO 操作执行延迟 |
| KVM_FEATURE_MMU_OP | 2 | 已弃用 |
| KVM_FEATURE_CLOCKSOURCE2 | 3 | kvmclock 可用在 msrs 0x4b564d00 和 0x4b564d01 上 |
| KVM_FEATURE_ASYNC_PF | 4 | 异步 pf 可通过写入 msr 0x4b564d02 来启用 |
| KVM_FEATURE_STEAL_TIME | 5 | 通过写入 msr 0x4b564d03 可以启用偷取时间 |
| KVM_FEATURE_PV_EOI | 6 | 通过写入 msr 0x4b564d04 可以启用半虚拟化中断结束处理程序 |
| KVM_FEATURE_PV_UNHALT | 7 | 客户机在启用半虚拟化自旋锁支持前检查此特性位 |
| KVM_FEATURE_PV_TLB_FLUSH | 9 | 客户机在启用半虚拟化 TLB 刷新前检查此特性位 |
| KVM_FEATURE_ASYNC_PF_VMEXIT | 10 | 半虚拟化异步 PF VM 退出可通过在写入 msr 0x4b564d02 时设置第 2 位来启用 |
| KVM_FEATURE_PV_SEND_IPI | 11 | 客户机在启用半虚拟化发送 IPI 前检查此特性位 |
| KVM_FEATURE_POLL_CONTROL | 12 | 通过写入 msr 0x4b564d05 可以禁用主机侧在 HLT 上的轮询 |
| KVM_FEATURE_PV_SCHED_YIELD | 13 | 客户机在使用半虚拟化调度让出前检查此特性位 |
| KVM_FEATURE_ASYNC_PF_INT | 14 | 客户机在使用第二个异步 pf 控制 msr 0x4b564d06 和异步 pf 确认 msr 0x4b564d07 前检查此特性位 |
| KVM_FEATURE_MSI_EXT_DEST_ID | 15 | 客户机在使用 MSI 地址位 11-5 中的扩展目的地 ID 位前检查此特性位 |
| KVM_FEATURE_HC_MAP_GPA_RANGE | 16 | 客户机在使用映射 GPA 范围超调用来通知页面状态更改前检查此特性位 |
| KVM_FEATURE_MIGRATION_CONTROL | 17 | 客户机在使用 MSR_KVM_MIGRATION_CONTROL 前检查此特性位 |
| KVM_FEATURE_CLOCKSOURCE_STABLE_BIT | 24 | 如果没有预期的每核 warp，则主机会在 kvmclock 中发出警告 |

:: 

      edx = 各个 (1 << flag) 的或运算结果

其中 `flag` 在此处定义如下：

| 标志 | 值 | 含义 |
| --- | --- | --- |
| KVM_HINTS_REALTIME | 0 | 客户机检查此特性位以确定 vCPU 永远不会被抢占，从而允许优化 |
