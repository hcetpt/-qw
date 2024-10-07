SPDX 许可证标识符: GPL-2.0

=================
KVM 特定的 MSRs
=================

:作者: Glauber Costa <glommer@redhat.com>，红帽公司，2010年

KVM 使用了一些自定义的 MSRs 来处理某些请求。
自定义 MSRs 有一个保留的范围，从 0x4b564d00 到 0x4b564dff。此区域之外还有一些 MSRs，但它们已被弃用，并且不鼓励使用。

自定义 MSR 列表
----------------

当前支持的自定义 MSR 列表如下：

MSR_KVM_WALL_CLOCK_NEW：
	0x4b564d00

数据：
	一个 4 字节对齐的物理地址，该地址指向一个必须在客户机内存中的区域。这个内存区域应该包含以下结构的一个副本：

	```c
	 struct pvclock_wall_clock {
		u32   version;
		u32   sec;
		u32   nsec;
	} __attribute__((__packed__));
	```

其数据将由虚拟机监视器填充。虚拟机监视器仅保证在 MSR 写入时更新这些数据。
希望可靠地多次查询此信息的用户需要多次写入此 MSR。字段的含义如下：

version：
	客户机必须在获取时间信息之前和之后检查版本，并确保它们都是相等且为偶数。
奇数版本表示正在进行更新。
sec：
	启动时的墙钟秒数。
nsec：
	启动时的墙钟纳秒数。
为了获取当前的墙钟时间，需要将系统时间（从 MSR_KVM_SYSTEM_TIME_NEW 中获取）加上。
请注意，尽管 MSRs 是每个 CPU 的实体，但此特定 MSR 的效果是全局性的。
在使用此 MSR 之前，必须通过 0x4000001 cpuid 叶子中的第 3 位来检查其可用性。
MSR_KVM_SYSTEM_TIME_NEW:
	0x4b564d01

数据：
	这是一个4字节对齐的物理地址，该地址指向位于客户机RAM中的内存区域，并且在第0位有一个启用位。此内存预期存储以下结构的副本：

```c
struct pvclock_vcpu_time_info {
	u32   version;
	u32   pad0;
	u64   tsc_timestamp;
	u64   system_time;
	u32   tsc_to_system_mul;
	s8    tsc_shift;
	u8    flags;
	u8    pad[2];
} __attribute__((__packed__)); /* 32 字节 */
```

此结构的数据将由虚拟机监控程序定期填充。每个VCPU只需要一次写入或注册。更新此结构的时间间隔是任意的，取决于实现。

虚拟机监控程序可以在任何时间更新此结构，直到有值为bit0 == 0的内容被写入。

字段含义如下：

- `version`：客户机必须在获取时间信息前后检查版本号，并确保它们都是相等且为偶数。奇数版本表示正在更新中。
- `tsc_timestamp`：当前VCPU在此结构更新时的TSC值。客户机可以从当前TSC减去这个值来得出自上次结构更新以来经过的时间。
- `system_time`：主机的单调时间概念，包括睡眠时间。单位为纳秒。
- `tsc_to_system_mul`：用于将与TSC相关的量转换为纳秒的乘数。
- `tsc_shift`：用于将与TSC相关的量转换为纳秒的移位。这个移位可以确保与`tsc_to_system_mul`的乘法不会溢出。正数值表示左移，负数值表示右移。从TSC到纳秒的转换涉及额外的32位右移。利用这些信息，客户机可以通过以下方式计算每核的时间：

```c
time = (current_tsc - tsc_timestamp);
if (tsc_shift >= 0)
    time <<= tsc_shift;
else
    time >>= -tsc_shift;
time = (time * tsc_to_system_mul) >> 32;
time = time + system_time;
```

- `flags`：此字段中的位表示客户机和虚拟机监控程序之间协调的扩展功能。特定标志的可用性需要在`0x40000001` cpuid叶中进行检查。当前的标志包括：

| flag位 | cpuid位 | 含义 |
|--------|---------|------|
|        |         | 跨多个CPU的时间测量保证单调性 |
|    0   |     24  |      |
|        |         | 客户机VCPU已被主机暂停           |
|    1   |    N/A  | 参见api.txt中的4.70章节          |

此MSR的可用性必须通过`0x4000001` cpuid叶中的第3位进行检查，才能使用。
### MSR_KVM_WALL_CLOCK:
#### 地址：0x11

数据和功能：
与 MSR_KVM_WALL_CLOCK_NEW 相同。建议使用后者。
此模型特定寄存器（MSR）超出保留的 KVM 范围，未来可能会被移除。其使用已过时。
在使用前，必须通过 CPUID 叶子 0x4000001 的第 0 位检查此 MSR 是否可用。

### MSR_KVM_SYSTEM_TIME:
#### 地址：0x12

数据和功能：
与 MSR_KVM_SYSTEM_TIME_NEW 相同。建议使用后者。
此模型特定寄存器（MSR）超出保留的 KVM 范围，未来可能会被移除。其使用已过时。
在使用前，必须通过 CPUID 叶子 0x4000001 的第 0 位检查此 MSR 是否可用。

检测 kvmclock 存在性的建议算法如下：

```c
if (!kvm_para_available()) {   // 参见 cpuid.txt
    return NON_PRESENT;
}

flags = cpuid_eax(0x40000001);
if (flags & 3) {
    msr_kvm_system_time = MSR_KVM_SYSTEM_TIME_NEW;
    msr_kvm_wall_clock = MSR_KVM_WALL_CLOCK_NEW;
    return PRESENT;
} else if (flags & 0) {
    msr_kvm_system_time = MSR_KVM_SYSTEM_TIME;
    msr_kvm_wall_clock = MSR_KVM_WALL_CLOCK;
    return PRESENT;
} else {
    return NON_PRESENT;
}
```

### MSR_KVM_ASYNC_PF_EN:
#### 地址：0x4b564d02

数据：
异步页面故障（APF）控制 MSR

- 位 63-6 表示一个 64 字节对齐的物理地址，该地址指向一个位于客体内存中的 64 字节内存区域。此内存区域应包含以下结构：

  ```c
  struct kvm_vcpu_pv_apf_data {
      /* 用于通过 #PF 传递的 '页面不存在' 事件 */
      __u32 flags;

      /* 用于通过中断通知传递的 '页面就绪' 事件 */
      __u32 token;

      __u8 pad[56];
  };
  ```

- MSR 的位 5-4 保留且应为零。当 vcpu 启用异步页面故障时，位 0 设置为 1；否则设置为 0。
- 位 1 设置为 1 表示当 vcpu 处于 cpl == 0 时可以注入异步页面故障。位 2 设置为 1 表示异步页面故障作为 #PF VM 退出传递到 L1。位 2 仅在 CPUID 中存在 KVM_FEATURE_ASYNC_PF_VMEXIT 时才能设置。位 3 启用基于中断的 '页面就绪' 事件传递。位 3 仅在 CPUID 中存在 KVM_FEATURE_ASYNC_PF_INT 时才能设置。
- 当前所有 '页面不存在' 事件都作为合成的 #PF 异常传递。在传递这些事件时，APF CR2 寄存器包含一个将在缺失页面可用时用于通知客体的令牌。此外，为了区分真实的 #PF 和 APF，64 字节内存位置的前 4 字节（'flags'）将在注入时由虚拟机监视器写入。目前仅支持 'flags' 的第一位，当其设置为 1 时，表示客体正在处理异步 '页面不存在' 事件。如果在页面故障期间 APF 'flags' 为 '0'，则表示这是常规的页面故障。客体应在处理完 #PF 异常后清除 'flags'，以便可以传递下一个事件。
注意，由于APF的“页面不存在”事件使用与常规页面错误相同的异常向量，因此在执行可能生成正常页面错误的操作之前，客户机必须将“flags”重置为“0”。

64字节内存位置（称为“令牌”）中的第4至第7字节将在APF“页面就绪”事件注入时由虚拟机监视器写入。这些字节的内容是一个先前通过CR2传递的“页面不存在”事件中的令牌。该事件表明页面现在可用。

客户机应在处理完“页面就绪”事件后将“令牌”写为“0”，并在清除该位置后将“1”写入MSR_KVM_ASYNC_PF_ACK；写入MSR会强制KVM重新扫描其队列并传递下一个待处理的通知。

注意，为了在MSR_KVM_ASYNC_PF_EN中启用APF机制或防止注入中断#0，需要先写入指定“页面就绪”APF传递中断向量的MSR_KVM_ASYNC_PF_INT寄存器。如果CPUID中存在KVM_FEATURE_ASYNC_PF_INT，则该MSR是可用的。

注意，之前“页面就绪”事件是通过与“页面不存在”事件相同的#PF异常传递的，但现在这种方式已被弃用。如果未设置位3（基于中断的传递），则不会传递APF事件。

如果在有未完成的APF事件时禁用APF，这些事件将不会被传递。

目前，“页面就绪”APF事件将始终在同一vCPU上传递，就像“页面不存在”事件一样，但客户机不应依赖这一点。

MSR_KVM_STEAL_TIME：
0x4b564d03

数据：
指向一个64字节对齐的物理地址，该地址位于客户机RAM内，并且位0包含一个启用位。此内存应包含以下结构的副本：

```c
struct kvm_steal_time {
    __u64 steal;
    __u32 version;
    __u32 flags;
    __u8 preempted;
    __u8 u8_pad[3];
    __u32 pad[11];
}
```

该结构的数据将由虚拟机监视器定期填充。每个VCPU只需要一次写入或注册即可。更新此结构的时间间隔是任意的，并且取决于实现。
虚拟机监视器可以在任何时候根据需要更新此结构，直到写入位0等于0的数据为止。客户机需要确保此结构已初始化为零。

字段含义如下：

version：
序列计数器。换句话说，客户机需要在获取时间信息前后检查此字段，以确保它们都相等并且为偶数。奇数版本表示正在进行的更新。
标志：
	在当前阶段，始终为零。将来可能用于表示此结构中的更改。

抢占时间：
	这个vCPU未运行的时间（以纳秒为单位）。vCPU处于空闲状态的时间不会被报告为抢占时间。
	
被抢占：
	指示拥有此结构的vCPU是否正在运行。非零值表示该vCPU已被抢占。零表示该vCPU未被抢占。注意，如果虚拟化管理程序不支持此字段，则它总是为零。
	
MSR_KVM_EOI_EN：
	0x4b564d04

数据：
	当vCPU上启用了PV中断结束时，第0位为1；禁用时为0。第1位保留，必须为零。当启用PV中断结束（第0位置位）时，第63-2位包含一个4字节对齐的物理地址，指向一个4字节内存区域，该区域必须位于客户机RAM中并且必须被清零。
	在通常情况下，在注入中断时，虚拟化管理程序会写入该4字节内存位置的最低有效位。值为1表示客户机可以跳过向APIC写入EOI（使用MSR或MMIO写入）；相反，只需清除客户机内存中的该位即可发出EOI信号——稍后该位置将由虚拟化管理程序轮询。
	值为0表示需要进行EOI写入。
	对于客户机来说，忽略这种优化并始终执行APIC EOI写入总是安全的。
	虚拟化管理程序保证仅在当前VCPU上下文中修改该最低有效位，这意味着客户机不需要使用锁前缀或内存排序原语来与虚拟化管理程序同步。
	然而，虚拟化管理程序可以在任何时候设置和清除该内存位：因此，为了确保虚拟化管理程序不会在客户机测试该位以检测是否可以跳过EOI APIC写入和客户机清除该位以向虚拟化管理程序发出EOI信号之间的窗口期中断客户机并清除内存区域中的最低有效位，客户机必须使用单个CPU指令同时读取内存区域中的最低有效位并清除它，例如测试并清除或比较并交换。

MSR_KVM_POLL_CONTROL：
	0x4b564d05

	控制主机端的轮询。
数据：
- 位 0 用于启用（1）或禁用（0）主机端 HLT 轮询逻辑
- KVM 客户机可以请求主机不要对 HLT 进行轮询，例如当它们自己正在执行轮询时

MSR_KVM_ASYNC_PF_INT：
- 0x4b564d06

数据：
- 第二个异步页面错误（APF）控制模型特定寄存器（MSR）
- 位 0-7：用于传递“页面就绪”APF 事件的 APIC 向量
- 位 8-63：保留

- 用于异步“页面就绪”通知传递的中断向量
- 在 MSR_KVM_ASYNC_PF_EN 中启用异步页面错误机制之前，必须设置该向量。只有在 CPUID 中存在 KVM_FEATURE_ASYNC_PF_INT 时，此 MSR 才可用

MSR_KVM_ASYNC_PF_ACK：
- 0x4b564d07

数据：
- 异步页面错误（APF）确认
- 当客户机完成“页面就绪”APF 事件处理并清除了 `struct kvm_vcpu_pv_apf_data` 中的 `token` 字段后，应将该 MSR 的第 0 位置为 1，这将导致主机重新扫描其队列并检查是否有更多待处理的通知。只有在 CPUID 中存在 KVM_FEATURE_ASYNC_PF_INT 时，此 MSR 才可用

MSR_KVM_MIGRATION_CONTROL：
- 0x4b564d08

数据：
- 如果 CPUID 中存在 KVM_FEATURE_MIGRATION_CONTROL，则此 MSR 可用。位 0 表示是否允许客户机的实时迁移
- 当启动一个客户机时，如果该客户机具有加密内存，则位 0 将为 0；如果客户机没有加密内存，则位 0 将为 1。如果客户机使用 `KVM_HC_MAP_GPA_RANGE` 超调用来与主机通信页面加密状态，则它可以在此 MSR 中设置位 0 来允许客户机的实时迁移
当然，请提供您需要翻译的文本。
