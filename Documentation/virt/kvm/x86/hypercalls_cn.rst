SPDX 许可证标识符: GPL-2.0

===================
Linux KVM Hypercall
===================

X86:
KVM Hypercalls 使用一个三字节序列，包含 vmcall 或 vmmcall 指令。虚拟机监控器可以将其替换为保证支持的指令。
最多可以在 rbx、rcx、rdx 和 rsi 中分别传递四个参数。
超调用编号应放置在 rax 中，返回值也将放置在 rax 中。除非特定超调用明确说明，否则不会破坏其他寄存器。

S390:
R2-R7 用于传递参数 1-6。此外，R1 用于超调用编号。返回值将写入 R2。
S390 使用诊断（diagnose）指令作为超调用（0x500），并结合 R1 中的超调用编号。
有关 KVM 支持的 S390 诊断调用的更多信息，请参阅 Documentation/virt/kvm/s390/s390-diag.rst。

PowerPC:
它使用 R3-R10，并且超调用编号在 R11 中。R4-R11 用作输出寄存器。
返回值放置在 R3 中。
KVM 超调用使用 4 字节的操作码，在设备树的 /hypervisor 节点中通过 'hypercall-instructions' 属性进行修补。
更多信息请参阅 Documentation/virt/kvm/ppc-pv.rst。

MIPS:
KVM 超调用使用代码为 0 的 HYPCALL 指令，并且超调用编号在 $2（v0）中。最多可以在 $4-$7（a0-a3）中放置四个参数，并且返回值放置在 $2（v0）中。
KVM Hypercalls 文档
============================

每个 hypercall 的模板如下：
1. Hypercall 名称
2. 架构
3. 状态（已弃用、已过时、活跃）
4. 目的

1. KVM_HC_VAPIC_POLL_IRQ
------------------------

- **架构**：x86
- **状态**：活跃
- **目的**：触发 guest 退出，以便在重新进入时主机可以检查是否有待处理的中断

2. KVM_HC_MMU_OP
----------------

- **架构**：x86
- **状态**：已弃用
- **目的**：支持 MMU 操作，如写入 PTE、刷新 TLB、释放 PT

3. KVM_HC_FEATURES
------------------

- **架构**：PPC
- **状态**：活跃
- **目的**：向 guest 暴露 hypercall 的可用性。在 x86 平台上，使用 `cpuid` 列出可用的 hypercall。在 PPC 上，可以使用基于设备树的查找（这也是 EPAPR 规定的方法），或者使用 KVM 特定的枚举机制（即此 hypercall）

4. KVM_HC_PPC_MAP_MAGIC_PAGE
----------------------------

- **架构**：PPC
- **状态**：活跃
- **目的**：为了使 hypervisor 和 guest 之间能够通信，存在一个共享页面，其中包含部分 supervisor 可见的寄存器状态。guest 可以通过此 hypercall 将此共享页面映射到内存中，从而访问其 supervisor 寄存器

5. KVM_HC_KICK_CPU
------------------

- **架构**：x86
- **状态**：活跃
- **目的**：用于唤醒处于 HLT 状态的 vcpu 的 hypercall
- **使用示例**：
  - 一个半虚拟化 guest 的 vcpu 在 guest 内核模式下忙等待某个事件发生（例如，自旋锁变得可用）时，如果忙等时间超过某个阈值，则可以执行 HLT 指令。执行 HLT 指令会导致 hypervisor 将 vcpu 置于睡眠状态，直到发生适当的事件。同一个 guest 的另一个 vcpu 可以通过发出 KVM_HC_KICK_CPU hypercall 来唤醒处于睡眠状态的 vcpu，并指定要唤醒的 vcpu 的 APIC ID（a1）。hypercall 中的另一个参数（a0）供将来使用

6. KVM_HC_CLOCK_PAIRING
-----------------------

- **架构**：x86
- **状态**：活跃
- **目的**：用于同步主机和 guest 时钟
- **使用**：
  - a0：主机将 `struct kvm_clock_offset` 结构复制到的 guest 物理地址
### a1: clock_type，仅支持KVM_CLOCK_PAIRING_WALLCLOCK (0) （对应主机的CLOCK_REALTIME时钟）

```
struct kvm_clock_pairing {
    __s64 sec;
    __s64 nsec;
    __u64 tsc;
    __u32 flags;
    __u32 pad[9];
};
```

其中：
* `sec`：从clock_type时钟获取的秒数
* `nsec`：从clock_type时钟获取的纳秒数
* `tsc`：用于计算`sec/nsec`对的guest TSC值
* `flags`：标志位，目前未使用（0）

此超调用允许guest计算跨主机和guest的精确时间戳。guest可以使用返回的TSC值来计算其时钟在相同瞬间的CLOCK_REALTIME。
如果主机不使用TSC时钟源，或者时钟类型不同于KVM_CLOCK_PAIRING_WALLCLOCK，则返回KVM_EOPNOTSUPP。

### 6. KVM_HC_SEND_IPI
-------------------

**架构**: x86  
**状态**: 活跃  
**目的**: 向多个vCPUs发送IPI  

- `a0`: 目标APIC ID位图的低部分
- `a1`: 目标APIC ID位图的高部分
- `a2`: 位图中的最低APIC ID
- `a3`: APIC ICR

此超调用允许guest发送多播IPI，在64位模式下每个超调用最多支持128个目标，在32位模式下每个超调用最多支持64个vCPUs。目标由前两个参数（`a0`和`a1`）中的位图表示。`a0`的第0位对应第三个参数（`a2`）中的APIC ID，第1位对应`a2+1`，依此类推。

返回成功传递IPI的CPU数量。

### 7. KVM_HC_SCHED_YIELD
-------------------

**架构**: x86  
**状态**: 活跃  
**目的**: 当目标vCPU被抢占时使用的超调用

- `a0`: 目标APIC ID

**使用示例**: 在向多个vCPUs发送call-function IPI时，如果任何目标vCPU被抢占，则执行yield操作。
### KVM_HC_MAP_GPA_RANGE
-------------------------
**架构**: x86  
**状态**: 活跃  
**目的**: 请求 KVM 映射具有指定属性的 GPA 范围  

- `a0`: 客户物理地址（GPA）的起始页
- `a1`: 页数（必须是连续的 GPA 空间，以 4KB 为单位）
- `a2`: 属性

其中 `'属性'` 包含：
    * 位 3:0 - 首选页面大小编码：0 = 4KB, 1 = 2MB, 2 = 1GB, 等等...
    * 位 4 - 明文 = 0, 加密 = 1
    * 位 63:5 - 保留（必须为零）

**实现说明**: 此超调用通过 `KVM_CAP_EXIT_HYPERCALL` 功能在用户空间中实现。用户空间必须在向客户机 CPUID 中宣传 `KVM_FEATURE_HC_MAP_GPA_RANGE` 之前启用该功能。此外，如果客户机支持 `KVM_FEATURE_MIGRATION_CONTROL`，用户空间还必须设置一个 MSR 过滤器来处理对 `MSR_KVM_MIGRATION_CONTROL` 的写入。
