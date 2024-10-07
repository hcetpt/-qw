SPDX许可证标识符: GPL-2.0

===================================================================
KVM（基于内核的虚拟机）API 的权威文档
===================================================================

1. 总体描述
======================

KVM API 是一组用于控制虚拟机各个方面操作的 ioctl。这些 ioctl 属于以下几类：

- 系统 ioctl：这些 ioctl 用于查询和设置影响整个 KVM 子系统的全局属性。此外，系统 ioctl 还用于创建虚拟机。
- 虚拟机（VM）ioctl：这些 ioctl 用于查询和设置影响整个虚拟机的属性，例如内存布局。此外，VM ioctl 还用于创建虚拟 CPU（vCPU）和设备。VM ioctl 必须从创建该 VM 的同一进程（地址空间）中发出。
- 虚拟 CPU（vCPU）ioctl：这些 ioctl 用于查询和设置控制单个虚拟 CPU 操作的属性。vCPU ioctl 应从创建 vCPU 的同一线程发出，除非文档中标明为异步的 vCPU ioctl。否则，在切换线程后的第一个 ioctl 可能会影响性能。
- 设备 ioctl：这些 ioctl 用于查询和设置控制单个设备操作的属性。设备 ioctl 必须从创建 VM 的同一进程（地址空间）中发出。

2. 文件描述符
===================

KVM API 围绕文件描述符展开。初始调用 `open("/dev/kvm")` 会获取对 KVM 子系统的句柄；此句柄可用于发出系统 ioctl。在该句柄上执行 KVM_CREATE_VM ioctl 将创建一个 VM 文件描述符，该描述符可用于发出 VM ioctl。在 VM 文件描述符上执行 KVM_CREATE_VCPU 或 KVM_CREATE_DEVICE ioctl 将创建一个虚拟 CPU 或设备，并返回指向新资源的文件描述符。最后，可以使用 vCPU 或设备文件描述符上的 ioctl 来控制 vCPU 或设备。对于 vCPU，这包括运行来宾代码的重要任务。

通常，文件描述符可以通过 fork() 和 Unix 域套接字的 SCM_RIGHTS 功能在进程之间迁移。但这些技巧在 KVM 中不被支持。虽然它们不会对主机造成损害，但其实际行为不受 KVM API 保证。有关 KVM 支持的 ioctl 使用模型，请参见“总体描述”。

需要注意的是，尽管 VM ioctl 只能从创建 VM 的进程发出，但 VM 的生命周期与其文件描述符相关联，而不是与其创建者（进程）相关。换句话说，直到最后一个对 VM 文件描述符的引用被释放之前，VM 及其资源（包括关联的地址空间）都不会被释放。
例如，如果在 ioctl(KVM_CREATE_VM) 之后发出 fork() 调用，则该虚拟机（VM）不会被释放，直到父进程（原始进程）及其子进程都释放了对该虚拟机文件描述符的引用。
由于一个虚拟机的资源在其文件描述符的最后一个引用被释放之前不会被释放，因此通过 fork()、dup() 等方式创建额外的虚拟机引用而不仔细考虑是强烈不建议的，并且可能会产生不良副作用，例如，当虚拟机关机时，代表虚拟机进程分配的内存可能不会被释放或未被计入。
3. 扩展
==========
截至 Linux 2.6.22，KVM ABI 已经稳定：不允许进行向后不兼容的更改。然而，有一种扩展机制允许查询和使用向后兼容的 API 扩展。
扩展机制并不基于 Linux 版本号。相反，kvm 定义了扩展标识符以及查询特定扩展标识符是否可用的机制。如果可用，则有一组 ioctl 可供应用程序使用。
4. API 描述
=============
本节描述了可用于控制 KVM 客户机的 ioctl。对于每个 ioctl，提供了以下信息及描述：

- 功能：
    - 提供此 ioctl 的 KVM 扩展是什么。可以是 'basic'，这意味着任何支持 API 版本 12 的内核都会提供它（见 4.1 节）；也可以是一个 KVM_CAP_xyz 常量，这意味着需要通过 KVM_CHECK_EXTENSION 检查其可用性（见 4.4 节）；或者 'none'，这意味着虽然不是所有内核都支持此 ioctl，但没有能力位来检查其可用性：对于不支持此 ioctl 的内核，ioctl 返回 -ENOTTY。
- 架构：
    - 支持此 ioctl 的指令集架构。x86 包括 i386 和 x86_64。
- 类型：
    - 系统、vm 或 vcpu。
参数：
    ioctl 接受哪些参数
返回值：
    返回值。一般错误码（如 EBADF、ENOMEM、EINVAL）不详细说明，但具有特定含义的错误会进行说明。

4.1 KVM_GET_API_VERSION
-----------------------

:功能: 基本
:架构: 所有
:类型: 系统 ioctl
:参数: 无
:返回值: 常量 KVM_API_VERSION (=12)

这标识了稳定的 kvm API 版本。预期这个数字不会改变。然而，Linux 2.6.20 和 2.6.21 报告了早期版本；这些版本没有文档支持。应用程序如果发现 KVM_GET_API_VERSION 返回的值不是 12 应该拒绝运行。如果通过此检查，则所有标记为“基本”的 ioctl 都可用。

4.2 KVM_CREATE_VM
-----------------

:功能: 基本
:架构: 所有
:类型: 系统 ioctl
:参数: 机器类型标识符（KVM_VM_*）
:返回值: 可用于控制新虚拟机的 VM 文件描述符
新创建的 VM 没有虚拟 CPU 也没有内存
建议使用 0 作为机器类型

X86:
^^^^

支持的 X86 VM 类型可以通过 KVM_CAP_VM_TYPES 查询。

S390:
^^^^^

为了在 S390 上创建用户控制的虚拟机，请检查 KVM_CAP_S390_UCONTROL 并以特权用户（CAP_SYS_ADMIN）身份使用标志 KVM_VM_S390_UCONTROL。

MIPS:
^^^^^

要在 MIPS 上使用硬件辅助虚拟化（VZ ASE），而不是默认的捕获与模拟实现（这会更改用户模式下的虚拟内存布局），请检查 KVM_CAP_MIPS_VZ 并使用标志 KVM_VM_MIPS_VZ。

ARM64:
^^^^^^

在 arm64 上，默认情况下 VM 的物理地址大小（IPA Size 限制）限制为 40 位。如果主机支持扩展 KVM_CAP_ARM_VM_IPA_SIZE，则可以配置此限制。当支持时，使用 KVM_VM_TYPE_ARM_IPA_SIZE(IPA_Bits) 设置机器类型标识符中的大小，其中 IPA_Bits 是 VM 使用的任何物理地址的最大宽度。IPA_Bits 编码在机器类型标识符的 bit[7-0] 中。
例如，配置一个客户机使用48位物理地址大小：

    vm_fd = ioctl(dev_fd, KVM_CREATE_VM, KVM_VM_TYPE_ARM_IPA_SIZE(48));

请求的大小（IPA_Bits）必须为：

 ==   =========================================================
  0   意味着默认大小，即40位（为了向后兼容）
  N   意味着N位，其中N是一个正整数，并且满足：
      32 <= N <= 主机_IPA_限制
 ==   =========================================================

主机_IPA_限制是在主机上IPA_Bits的最大可能值，并且取决于CPU能力和内核配置。此限制可以通过运行时的`KVM_CHECK_EXTENSION` ioctl()中的`KVM_CAP_ARM_VM_IPA_SIZE`获取。
如果请求的IPA大小（无论是隐式还是显式的）在主机上不受支持，则创建虚拟机将失败。
请注意，配置IPA大小不会影响由客户机CPU在ID_AA64MMFR0_EL1[PARange]中暴露的能力。它只影响阶段2级别的地址转换（从客户机物理地址到主机物理地址的转换）。

4.3 KVM_GET_MSR_INDEX_LIST, KVM_GET_MSR_FEATURE_INDEX_LIST
----------------------------------------------------------

- **功能**：基本功能，KVM_CAP_GET_MSR_FEATURES用于KVM_GET_MSR_FEATURE_INDEX_LIST
- **架构**：x86
- **类型**：系统ioctl
- **参数**：struct kvm_msr_list（输入/输出）
- **返回值**：成功返回0；错误返回-1

错误：

  ======     ============================================================
  EFAULT     无法读取或写入msr索引列表
  E2BIG      msr索引列表太大，无法放入用户指定的数组中
  ======     ============================================================

::

  struct kvm_msr_list {
	__u32 nmsrs; /* 索引数组中的msr数量 */
	__u32 indices[0];
  };

用户填写索引数组的大小（nmsrs），然后KVM会调整nmsrs以反映实际的msr数量，并填充索引数组。
KVM_GET_MSR_INDEX_LIST返回支持的客户机msr列表。此列表随KVM版本和主机处理器的不同而变化，但其他情况下不会改变。
注意：如果KVM指示支持MCE（KVM_CAP_MCE），则MCE银行MSR不会返回在MSR列表中，因为不同的vCPU可以有不同的银行数量，这通过KVM_X86_SETUP_MCE ioctl设置。
KVM_GET_MSR_FEATURE_INDEX_LIST返回可以传递给KVM_GET_MSRS系统ioctl的MSR列表。这允许用户空间探测通过MSR暴露的主机能力和处理器特性（例如，VMX能力）。
此列表也随KVM版本和主机处理器的不同而变化，但其他情况下不会改变。

4.4 KVM_CHECK_EXTENSION
-----------------------

- **功能**：基本功能，KVM_CAP_CHECK_EXTENSION_VM用于vm ioctl
- **架构**：所有架构
- **类型**：系统ioctl，vm ioctl
- **参数**：扩展标识符（KVM_CAP_*）
- **返回值**：不支持返回0；支持返回1（或其他正整数）

该API允许应用程序查询核心KVM API的扩展。用户空间传递一个扩展标识符（一个整数），并接收描述扩展可用性的整数。
通常情况下，0 表示否，1 表示是，但某些扩展可能会在整数返回值中报告其他信息。
基于它们的初始化，不同的虚拟机可能具有不同的功能。因此，建议使用 vm ioctl 查询功能（可通过 KVM_CAP_CHECK_EXTENSION_VM 在 vm 文件描述符上使用）。

4.5 KVM_GET_VCPU_MMAP_SIZE
--------------------------

:功能: 基本
:架构: 所有
:类型: 系统 ioctl
:参数: 无
:返回: vcpu mmap 区域的大小，以字节为单位

KVM_RUN ioctl（参见）通过共享内存区域与用户空间通信。此 ioctl 返回该区域的大小。详细信息请参阅 KVM_RUN 文档。
除了 KVM_RUN 通信区域的大小外，VCPU 文件描述符的其他区域也可以被 mmap，包括：

- 如果 KVM_CAP_COALESCED_MMIO 可用，则在 KVM_COALESCED_MMIO_PAGE_OFFSET * PAGE_SIZE 处的一个页面；由于历史原因，此页面包含在 KVM_GET_VCPU_MMAP_SIZE 的结果中。KVM_CAP_COALESCED_MMIO 尚未文档化。
- 如果 KVM_CAP_DIRTY_LOG_RING 可用，则在 KVM_DIRTY_LOG_PAGE_OFFSET * PAGE_SIZE 处的若干页面。有关 KVM_CAP_DIRTY_LOG_RING 的更多信息，请参阅第 8.3 节。

4.7 KVM_CREATE_VCPU
-------------------

:功能: 基本
:架构: 所有
:类型: vm ioctl
:参数: vcpu id（x86 上的 apic id）
:返回: 成功时返回 vcpu 文件描述符，失败时返回 -1

此 API 向虚拟机添加一个 vcpu。添加的 vcpu 数量不能超过 max_vcpus。
vcpu id 是范围 [0, max_vcpu_id) 内的一个整数。
推荐的最大 vcpu 数量可以通过运行时的 KVM_CHECK_EXTENSION ioctl() 的 KVM_CAP_NR_VCPUS 获取。
最大可能的 max_vcpus 值可以通过运行时的 KVM_CHECK_EXTENSION ioctl() 的 KVM_CAP_MAX_VCPUS 获取。
如果 `KVM_CAP_NR_VCPUS` 不存在，你应该假设 `max_vcpus` 是 4 个 CPU 核心的最大值。
如果 `KVM_CAP_MAX_VCPUS` 不存在，你应该假设 `max_vcpus` 的值与 `KVM_CAP_NR_VCPUS` 返回的值相同。
`max_vcpu_id` 的最大可能值可以通过在运行时使用 `KVM_CHECK_EXTENSION` ioctl() 的 `KVM_CAP_MAX_VCPU_ID` 能力来获取。
如果 `KVM_CAP_MAX_VCPU_ID` 不存在，你应该假设 `max_vcpu_id` 与 `KVM_CAP_MAX_VCPUS` 返回的值相同。
在使用 book3s_hv 模式的 powerpc 上，虚拟 CPU（vcpu）映射到一个或多个虚拟 CPU 核心中的虚拟线程上。（这是因为硬件要求 CPU 核心中的所有硬件线程必须位于同一个分区中。）`KVM_CAP_PPC_SMT` 能力指示每个虚拟核心（vcore）中的 vcpu 数量。通过将 vcpu ID 除以每个 vcore 中的 vcpu 数量来获得 vcore ID。给定 vcore 中的 vcpu 总是彼此位于相同的物理核心中（尽管该物理核心可能会随时间变化）。
用户空间可以通过其 vcpu ID 的分配来控制来宾的线程模式（SMT）。例如，如果用户空间希望单线程来宾 vcpu，则应使所有 vcpu ID 都是每个 vcore 中 vcpu 数量的倍数。
对于使用 S390 用户控制虚拟机创建的虚拟 CPU，可以将生成的 vcpu 文件描述符在页偏移 `KVM_S390_SIE_PAGE_OFFSET` 处进行内存映射，以获取虚拟 CPU 硬件控制块的内存映射。

### 4.8 KVM_GET_DIRTY_LOG (vm ioctl)
---------------------------------

**能力**: 基本  
**架构**: 所有  
**类型**: vm ioctl  
**参数**: struct kvm_dirty_log (输入/输出)  
**返回值**: 成功返回 0，错误返回 -1

```
/* 对于 KVM_GET_DIRTY_LOG */
struct kvm_dirty_log {
	__u32 slot;
	__u32 padding;
	union {
		void __user *dirty_bitmap; /* 每页一个比特位 */
		__u64 padding;
	};
};
```

给定一个内存槽，返回自上次调用此 ioctl 以来被修改过的任何页面的位图。位 0 是内存槽中的第一个页面。确保整个结构被清零以避免填充问题。
如果 `KVM_CAP_MULTI_ADDRESS_SPACE` 可用，则 `slot` 字段的第 16 到 31 位指定要返回脏位图的地址空间。有关 `slot` 字段使用的详细信息，请参阅 `KVM_SET_USER_MEMORY_REGION`。
除非启用了 `KVM_CAP_MANUAL_DIRTY_LOG_PROTECT2`，否则在 ioctl 返回之前会清除脏位图中的比特位。更多详细信息，请参见该能力的描述。
请注意，如果配置了Xen共享信息页，则应始终认为它是脏的。KVM不会显式地将其标记为脏。
### 4.10 KVM_RUN

- **功能**：基本
- **架构**：所有
- **类型**：vCPU ioctl
- **参数**：无
- **返回值**：成功时返回0，错误时返回-1

**错误**：

| 错误码 | 描述 |
| --- | --- |
| EINTR | 有未屏蔽的信号待处理 |
| ENOEXEC | vCPU尚未初始化或来宾试图从设备内存中执行指令（ARM64） |
| ENOSYS | 在没有综合征信息的memslot之外发生数据中止，并且未启用KVM_CAP_ARM_NISV_TO_USER（ARM64） |
| EPERM | SVE特性已设置但未最终确定（ARM64） |

此ioctl用于运行来宾虚拟CPU。虽然没有显式的参数，但可以通过在vCPU文件描述符的偏移量0处使用mmap()获取一个隐含的参数块，其大小由KVM_GET_VCPU_MMAP_SIZE给出。参数块格式化为一个'struct kvm_run'（见下文）。

### 4.11 KVM_GET_REGS

- **功能**：基本
- **架构**：除了ARM64的所有架构
- **类型**：vCPU ioctl
- **参数**：struct kvm_regs（输出）
- **返回值**：成功时返回0，错误时返回-1

从vCPU读取通用寄存器。

```c
/* x86 */
struct kvm_regs {
    __u64 rax, rbx, rcx, rdx;
    __u64 rsi, rdi, rsp, rbp;
    __u64 r8,  r9,  r10, r11;
    __u64 r12, r13, r14, r15;
    __u64 rip, rflags;
};

/* MIPS */
struct kvm_regs {
    __u64 gpr[32];
    __u64 hi;
    __u64 lo;
    __u64 pc;
};

/* LoongArch */
struct kvm_regs {
    unsigned long gpr[32];
    unsigned long pc;
};
```

### 4.12 KVM_SET_REGS

- **功能**：基本
- **架构**：除了ARM64的所有架构
- **类型**：vCPU ioctl
- **参数**：struct kvm_regs（输入）
- **返回值**：成功时返回0，错误时返回-1

将通用寄存器写入vCPU。参见KVM_GET_REGS中的数据结构。

### 4.13 KVM_GET_SREGS

- **功能**：基本
- **架构**：x86, ppc
- **类型**：vCPU ioctl
- **参数**：struct kvm_sregs（输出）
- **返回值**：成功时返回0，错误时返回-1

从vCPU读取特殊寄存器。

```c
/* x86 */
struct kvm_sregs {
    struct kvm_segment cs, ds, es, fs, gs, ss;
    struct kvm_segment tr, ldt;
    struct kvm_dtable gdt, idt;
    __u64 cr0, cr2, cr3, cr4, cr8;
    __u64 efer;
    __u64 apic_base;
    __u64 interrupt_bitmap[(KVM_NR_INTERRUPTS + 63) / 64];
};

/* PPC -- 参见 arch/powerpc/include/uapi/asm/kvm.h */
```

`interrupt_bitmap`是一个表示待处理外部中断的位图。最多只能设置一位。这个中断已被APIC确认，但尚未注入到CPU核心中。

### 4.14 KVM_SET_SREGS

- **功能**：基本
- **架构**：x86, ppc
- **类型**：vCPU ioctl
- **参数**：struct kvm_sregs（输入）
- **返回值**：成功时返回0，错误时返回-1

将特殊寄存器写入vCPU。参见KVM_GET_SREGS中的数据结构。

### 4.15 KVM_TRANSLATE

- **功能**：基本
- **架构**：x86
- **类型**：vCPU ioctl
- **参数**：struct kvm_translation（输入/输出）
- **返回值**：成功时返回0，错误时返回-1

根据vCPU当前的地址转换模式将虚拟地址进行转换。

```c
struct kvm_translation {
    __u64 linear_address; /* 输入 */
    __u64 physical_address; /* 输出 */
    __u8 valid;
    __u8 writeable;
    __u8 usermode;
    __u8 pad[5];
};
```

### 4.16 KVM_INTERRUPT

- **功能**：基本
- **架构**：x86, ppc, mips, riscv, loongarch
- **类型**：vCPU ioctl
- **参数**：struct kvm_interrupt（输入）
- **返回值**：成功时返回0，失败时返回负数
将硬件中断向量排队以注入：

```plaintext
/* 对于 KVM_INTERRUPT */
struct kvm_interrupt {
    /* 输入 */
    __u32 irq;
};
```

X86:
^^^^

**返回值:**

| 结果 | 解释                     |
|------|--------------------------|
| 0    | 成功                     |
| -EEXIST | 如果已有一个中断被排队     |
| -EINVAL | 中断号无效               |
| -ENXIO | 如果 PIC 在内核中         |
| -EFAULT | 如果指针无效             |

注意：`irq` 是一个中断向量，而不是中断引脚或线路。此 ioctl 在不使用内核中的 PIC 时非常有用。

PPC:
^^^^

将外部中断排队以注入。此 ioctl 被重载为三种不同的 irq 值：

a) KVM_INTERRUPT_SET

   当虚拟机准备好接收中断时，注入一次边沿类型外部中断。当注入后，中断完成。

b) KVM_INTERRUPT_UNSET

   取消任何待处理的中断。
   仅在启用 KVM_CAP_PPC_UNSET_IRQ 时可用。

c) KVM_INTERRUPT_SET_LEVEL

   将电平类型外部中断注入到虚拟机上下文中。该中断会一直待处理，直到通过带有 KVM_INTERRUPT_UNSET 的特定 ioctl 触发。
   仅在启用 KVM_CAP_PPC_IRQ_LEVEL 时可用。

注意：除上述值外的任何 `irq` 值都是无效的，并可能导致意外行为。
这是一个异步的 vcpu ioctl，可以从任何线程调用。

MIPS:
^^^^^

将外部中断排队以注入到虚拟 CPU 中。负的中断号表示取消排队的中断。
这是一个异步的虚拟CPU ioctl 操作，可以从任何线程调用。
RISC-V:
^^^^^^^

将一个外部中断排队注入虚拟CPU。此ioctl具有两个不同的中断值：

a) KVM_INTERRUPT_SET

   这设置了虚拟CPU的外部中断，并且一旦准备就绪就会接收到该中断。
b) KVM_INTERRUPT_UNSET

   这清除了虚拟CPU待处理的外部中断。
这是一个异步的虚拟CPU ioctl 操作，可以从任何线程调用。
LOONGARCH:
^^^^^^^^^^

将一个外部中断排队注入虚拟CPU。一个负数的中断号会取消排队该中断。
这是一个异步的虚拟CPU ioctl 操作，可以从任何线程调用。
4.18 KVM_GET_MSRS
-----------------

:功能: 基本（虚拟CPU），KVM_CAP_GET_MSR_FEATURES（系统）
:架构: x86
:类型: 系统ioctl，虚拟CPU ioctl
:参数: struct kvm_msrs（输入/输出）
:返回: 成功返回的MSR数量；错误时返回-1

当作为系统ioctl使用时：
读取VM可用的基于MSR的功能值。这类似于KVM_GET_SUPPORTED_CPUID，但返回的是MSR索引和值。
可以通过系统ioctl中的KVM_GET_MSR_FEATURE_INDEX_LIST获取基于MSR的功能列表。
当作为虚拟CPU ioctl使用时：
从虚拟CPU读取模型特定寄存器。支持的MSR索引可以通过系统ioctl中的KVM_GET_MSR_INDEX_LIST获取。

应用程序代码应设置'nmsrs'成员（表示entries数组的大小）以及每个数组条目的'index'成员。
### 4.19 KVM_SET_MSRS
-----------------

**功能**: 基本  
**架构**: x86  
**类型**: vcpu ioctl  
**参数**: struct kvm_msrs (输入)  
**返回值**: 成功设置的MSR数量（见下文），错误时返回-1  

将模型特定寄存器写入到vCPU。关于数据结构，请参见KVM_GET_MSRS。
应用程序代码应设置'nmsrs'成员（指示entries数组的大小），以及每个数组项的'index'和'data'成员。
它尝试逐个设置数组entries[]中的MSR。如果设置某个MSR失败，例如由于设置了保留位，或者该MSR不被KVM支持/模拟等，则停止处理MSR列表，并返回已成功设置的MSR数量。

### 4.20 KVM_SET_CPUID
------------------

**功能**: 基本  
**架构**: x86  
**类型**: vcpu ioctl  
**参数**: struct kvm_cpuid (输入)  
**返回值**: 成功时返回0，错误时返回-1  

定义vCPU对cpuid指令的响应。如果可用，应用程序应使用KVM_SET_CPUID2 ioctl。
注意事项：
  - 如果此IOCTL失败，KVM不保证先前有效的CPUID配置（如果有）不会被破坏。用户空间可以通过KVM_GET_CPUID2获取结果CPUID配置的副本。
  - 在KVM_RUN之后使用KVM_SET_CPUID{,2}，即在运行来宾后更改来宾vCPU模型，可能会导致来宾不稳定。
  - 使用异构CPUID配置（除APIC ID、拓扑等外）可能会导致来宾不稳定。

```c
struct kvm_cpuid_entry {
	__u32 function;
	__u32 eax;
	__u32 ebx;
	__u32 ecx;
	__u32 edx;
	__u32 padding;
};

/* 对于KVM_SET_CPUID */
struct kvm_cpuid {
	__u32 nent;
	__u32 padding;
	struct kvm_cpuid_entry entries[0];
};
```

### 4.21 KVM_SET_SIGNAL_MASK
------------------------

**功能**: 基本  
**架构**: 所有  
**类型**: vcpu ioctl  
**参数**: struct kvm_signal_mask (输入)  
**返回值**: 成功时返回0，错误时返回-1  

定义在执行KVM_RUN期间被阻止的信号。此信号掩码会暂时覆盖线程的信号掩码。接收到任何未被阻止的信号（除了SIGKILL和SIGSTOP，它们保持传统行为）将导致KVM_RUN返回-EINTR。
### 注意事项：信号仅在未被原始信号掩码阻塞的情况下传递
```
/* 用于 KVM_SET_SIGNAL_MASK */
struct kvm_signal_mask {
    __u32 len;
    __u8  sigset[0];
};
```

### 4.22 KVM_GET_FPU
-------------------

**功能：** 基本  
**架构：** x86, loongarch  
**类型：** vcpu ioctl  
**参数：** struct kvm_fpu (输出)  
**返回值：** 成功返回 0，失败返回 -1

从 vcpu 中读取浮点状态。
```
/* x86: 用于 KVM_GET_FPU 和 KVM_SET_FPU */
struct kvm_fpu {
    __u8  fpr[8][16];
    __u16 fcw;
    __u16 fsw;
    __u8  ftwx;  /* 在 fxsave 格式中 */
    __u8  pad1;
    __u16 last_opcode;
    __u64 last_ip;
    __u64 last_dp;
    __u8  xmm[16][16];
    __u32 mxcsr;
    __u32 pad2;
};

/* LoongArch: 用于 KVM_GET_FPU 和 KVM_SET_FPU */
struct kvm_fpu {
    __u32 fcsr;
    __u64 fcc;
    struct kvm_fpureg {
        __u64 val64[4];
    } fpr[32];
};
```

### 4.23 KVM_SET_FPU
-------------------

**功能：** 基本  
**架构：** x86, loongarch  
**类型：** vcpu ioctl  
**参数：** struct kvm_fpu (输入)  
**返回值：** 成功返回 0，失败返回 -1

将浮点状态写入 vcpu。
```
/* x86: 用于 KVM_GET_FPU 和 KVM_SET_FPU */
struct kvm_fpu {
    __u8  fpr[8][16];
    __u16 fcw;
    __u16 fsw;
    __u8  ftwx;  /* 在 fxsave 格式中 */
    __u8  pad1;
    __u16 last_opcode;
    __u64 last_ip;
    __u64 last_dp;
    __u8  xmm[16][16];
    __u32 mxcsr;
    __u32 pad2;
};

/* LoongArch: 用于 KVM_GET_FPU 和 KVM_SET_FPU */
struct kvm_fpu {
    __u32 fcsr;
    __u64 fcc;
    struct kvm_fpureg {
        __u64 val64[4];
    } fpr[32];
};
```

### 4.24 KVM_CREATE_IRQCHIP
---------------------------

**功能：** KVM_CAP_IRQCHIP, KVM_CAP_S390_IRQCHIP (s390)  
**架构：** x86, arm64, s390  
**类型：** vm ioctl  
**参数：** 无  
**返回值：** 成功返回 0，失败返回 -1

在内核中创建中断控制器模型。
- 在 x86 架构上，创建一个虚拟 IOAPIC、一个虚拟 PIC（两个嵌套的 PIC）并设置未来的 vCPU 拥有本地 APIC。GSIs 0-15 的中断路由设置为 PIC 和 IOAPIC；GSI 16-23 只路由到 IOAPIC。
- 在 arm64 架构上，创建一个 GICv2。其他版本的 GIC 需要使用 KVM_CREATE_DEVICE，它也支持创建 GICv2。对于 GICv2，建议使用 KVM_CREATE_DEVICE 而不是 KVM_CREATE_IRQCHIP。
- 在 s390 架构上，创建一个虚拟的中断路由表。注意，在 s390 上需要先启用 KVM_CAP_S390_IRQCHIP 功能才能使用 KVM_CREATE_IRQCHIP。

### 4.25 KVM_IRQ_LINE
----------------------

**功能：** KVM_CAP_IRQCHIP  
**架构：** x86, arm64  
**类型：** vm ioctl  
**参数：** struct kvm_irq_level  
**返回值：** 成功返回 0，失败返回 -1

设置内核中断控制器模型中的 GSI 输入级别。
在某些架构上，要求必须先通过 KVM_CREATE_IRQCHIP 创建中断控制器模型。请注意，边沿触发的中断需要先将级别设置为 1 然后回退到 0。
在真实硬件上，中断引脚可以是低电平有效或高电平有效。这对于 `struct kvm_irq_level` 中的 `level` 字段来说并不重要：1 始终表示有效（激活），0 表示无效（未激活）。
x86 允许操作系统为电平触发中断编程中断极性（低电平有效/高电平有效），并且 KVM 以前会考虑极性。然而，由于处理低电平有效中断时存在代码腐化问题，上述约定现在在 x86 上也适用。这是通过 `KVM_CAP_X86_IOAPIC_POLARITY_IGNORED` 能力信号来指示的。用户空间除非存在此能力（或者当然没有使用内核中的 irqchip），否则不应将中断以低电平有效的方式呈现给客户机。

arm64 可以在 CPU 级别或内核中的 irqchip（GIC）中发出中断，并且对于内核中的 irqchip，可以告诉 GIC 使用为特定 CPU 指定的 PPI。`irq` 字段解释如下：

```
位:   |  31 ... 28  | 27 ... 24 | 23  ... 16 | 15 ... 0 |
字段: | vcpu2_index | irq_type  | vcpu_index |  irq_id  |
```

`irq_type` 字段具有以下值：
- `irq_type[0]`: 外核 GIC：`irq_id 0` 是 IRQ，`irq_id 1` 是 FIQ
- `irq_type[1]`: 内核 GIC：SPI，`irq_id` 在 32 到 1019（包括）之间（`vcpu_index` 字段被忽略）
- `irq_type[2]`: 内核 GIC：PPI，`irq_id` 在 16 到 31（包括）

（因此，`irq_id` 字段很好地对应了 ARM GIC 规格中的 IRQ ID）

在这两种情况下，`level` 用于激活/去激活线。
当支持 `KVM_CAP_ARM_IRQ_LINE_LAYOUT_2` 时，目标 vcpu 识别为 `(256 * vcpu2_index + vcpu_index)`。否则，`vcpu2_index` 必须为零。
注意，在 arm64 上，`KVM_CAP_IRQCHIP` 能力仅影响内核 irqchip 的中断注入。`KVM_IRQ_LINE` 总是可以用于用户空间中断控制器。
```
struct kvm_irq_level {
	union {
		__u32 irq;     /* GSI */
		__s32 status;  /* 不适用于 KVM_IRQ_LEVEL */
	};
	__u32 level;           /* 0 或 1 */
};
```

### 4.26 KVM_GET_IRQCHIP

- **能力**：`KVM_CAP_IRQCHIP`
- **架构**：x86
- **类型**：vm ioctl
- **参数**：`struct kvm_irqchip` （输入/输出）
- **返回**：成功时返回 0，失败时返回 -1

读取由 `KVM_CREATE_IRQCHIP` 创建的内核中断控制器的状态到调用者提供的缓冲区中。
```
struct kvm_irqchip {
	__u32 chip_id;  /* 0 = PIC1, 1 = PIC2, 2 = IOAPIC */
	__u32 pad;
	union {
		char dummy[512];  /* 预留空间 */
		struct kvm_pic_state pic;
		struct kvm_ioapic_state ioapic;
	} chip;
};
```

### 4.27 KVM_SET_IRQCHIP

- **能力**：`KVM_CAP_IRQCHIP`
- **架构**：x86
- **类型**：vm ioctl
- **参数**：`struct kvm_irqchip` （输入）
- **返回**：成功时返回 0，失败时返回 -1

从调用者提供的缓冲区设置由 `KVM_CREATE_IRQCHIP` 创建的内核中断控制器的状态。
```
struct kvm_irqchip {
	__u32 chip_id;  /* 0 = PIC1, 1 = PIC2, 2 = IOAPIC */
	__u32 pad;
	union {
		char dummy[512];  /* 预留空间 */
		struct kvm_pic_state pic;
		struct kvm_ioapic_state ioapic;
	} chip;
};
```

### 4.28 KVM_XEN_HVM_CONFIG

- **能力**：`KVM_CAP_XEN_HVM`
- **架构**：x86
- **类型**：vm ioctl
- **参数**：`struct kvm_xen_hvm_config` （输入）
- **返回**：成功时返回 0，失败时返回 -1

设置 Xen HVM 客户机用来初始化其 hypercall 页面的 MSR，并提供用户空间中 hypercall blobs 的起始地址和大小。当客户机写入 MSR 时，KVM 将一个页面的 blob（32 位或 64 位，取决于 vcpu 模式）复制到客户机内存。
```
struct kvm_xen_hvm_config {
	__u32 flags;
	__u32 msr;
	__u64 blob_addr_32;
	__u64 blob_addr_64;
	__u8 blob_size_32;
	__u8 blob_size_64;
	__u8 pad2[30];
};
```

如果 `KVM_CAP_XEN_HVM` 检查返回某些标志，则可以在此 ioctl 的 `flags` 字段中设置这些标志：

`KVM_XEN_HVM_CONFIG_INTERCEPT_HCALL` 标志请求 KVM 自动生成 hypercall 页面的内容；hypercalls 将被拦截并传递给用户空间通过 `KVM_EXIT_XEN`。在这种情况下，所有 blob 大小和地址字段必须为零。
### KVM_XEN_HVM_CONFIG_EVTCHN_SEND 标志

`KVM_XEN_HVM_CONFIG_EVTCHN_SEND` 标志表示用户空间将始终使用 `KVM_XEN_HVM_EVTCHN_SEND` ioctl 来传递事件通道中断，而不是直接操作来宾的共享信息结构。这反过来可能允许 KVM 启用某些功能，例如拦截 SCHEDOP_poll 超调用来加速来宾的 PV 自旋锁操作。即使用户空间没有明确发送这个标志来表明它将始终这样做，它仍然可以使用 ioctl 来传递事件。

目前 `struct kvm_xen_hvm_config` 中没有其他有效的标志。

### 4.29 KVM_GET_CLOCK

---

**功能**: KVM_CAP_ADJUST_CLOCK  
**架构**: x86  
**类型**: vm ioctl  
**参数**: struct kvm_clock_data (输出)  
**返回值**: 成功时返回 0，错误时返回 -1  

获取当前来宾所见的 kvmclock 的当前时间戳。结合 `KVM_SET_CLOCK` 使用，用于确保在迁移等场景中的单调性。
当 `KVM_CAP_ADJUST_CLOCK` 传递给 `KVM_CHECK_EXTENSION` 时，它返回 `struct kvm_clock_data` 的 `flag` 成员中 KVM 可以返回的一组位。
定义了以下标志：

- `KVM_CLOCK_TSC_STABLE`
  如果设置，返回的值是所有 VCPU 在调用 `KVM_GET_CLOCK` 时所见的确切 kvmclock 值；如果未设置，则返回的值仅仅是 `CLOCK_MONOTONIC` 加上一个常量偏移量；可以通过 `KVM_SET_CLOCK` 修改该偏移量。KVM 将尝试使所有 VCPU 遵循此时钟，但由于主机 TSC 不稳定，每个 VCPU 读取的确切值可能会有所不同。
- `KVM_CLOCK_REALTIME`
  如果设置，`kvm_clock_data` 结构中的 `realtime` 字段将填充在调用 `KVM_GET_CLOCK` 时主机实时时钟源的值；如果未设置，则 `realtime` 字段不包含任何值。
- `KVM_CLOCK_HOST_TSC`
  如果设置，`kvm_clock_data` 结构中的 `host_tsc` 字段将填充在调用 `KVM_GET_CLOCK` 时主机的时间戳计数器（TSC）的值；如果未设置，则 `host_tsc` 字段不包含任何值。

```c
struct kvm_clock_data {
    __u64 clock;   // kvmclock 当前值
    __u32 flags;
    __u32 pad0;
    __u64 realtime;
    __u64 host_tsc;
    __u32 pad[4];
};
```

### 4.30 KVM_SET_CLOCK

---

**功能**: KVM_CAP_ADJUST_CLOCK  
**架构**: x86  
**类型**: vm ioctl  
**参数**: struct kvm_clock_data (输入)  
**返回值**: 成功时返回 0，错误时返回 -1  

将 kvmclock 的当前时间戳设置为参数中指定的值。结合 `KVM_GET_CLOCK` 使用，用于确保在迁移等场景中的单调性。
可以传递以下标志：

- `KVM_CLOCK_REALTIME`
  如果设置，KVM 将比较 `realtime` 字段的值与调用 `KVM_SET_CLOCK` 时主机实时时钟源的值。经过的时间差将加到最后提供给来宾的 kvmclock 值上。
### 4.31 KVM_GET_VCPU_EVENTS

#### 能力：KVM_CAP_VCPU_EVENTS
#### 扩展：KVM_CAP_INTR_SHADOW
#### 架构：x86, arm64
#### 类型：vcpu ioctl
#### 参数：struct kvm_vcpu_events (输出)
#### 返回值：成功时返回0，失败时返回-1

#### X86:
^^^^

获取当前待处理的异常、中断和非屏蔽中断（NMIs）以及与之相关的VCPU状态。

```c
struct kvm_vcpu_events {
    struct {
        __u8 injected;
        __u8 nr;
        __u8 has_error_code;
        __u8 pending;
        __u32 error_code;
    } exception;
    struct {
        __u8 injected;
        __u8 nr;
        __u8 soft;
        __u8 shadow;
    } interrupt;
    struct {
        __u8 injected;
        __u8 pending;
        __u8 masked;
        __u8 pad;
    } nmi;
    __u32 sipi_vector;
    __u32 flags;
    struct {
        __u8 smm;
        __u8 pending;
        __u8 smm_inside_nmi;
        __u8 latched_init;
    } smi;
    __u8 reserved[27];
    __u8 exception_has_payload;
    __u64 exception_payload;
};
```

`flags` 字段中定义了以下位：

- `KVM_VCPUEVENT_VALID_SHADOW` 可能被设置以指示 `interrupt.shadow` 包含有效状态。
- `KVM_VCPUEVENT_VALID_SMM` 可能被设置以指示 `smi` 包含有效状态。
- `KVM_VCPUEVENT_VALID_PAYLOAD` 可能被设置以指示 `exception_has_payload`, `exception_payload`, 和 `exception.pending` 字段包含有效状态。此位将在启用 `KVM_CAP_EXCEPTION_PAYLOAD` 时设置。
- `KVM_VCPUEVENT_VALID_TRIPLE_FAULT` 可能被设置以指示 `triple_fault_pending` 字段包含有效状态。此位将在启用 `KVM_CAP_X86_TRIPLE_FAULT_EVENT` 时设置。

#### ARM64:
^^^^^^

如果访客访问一个由主机内核模拟的设备，并且该设备在实际情况下会生成物理SErrors，则KVM可能会为该VCPU设置一个虚拟SErrors。这个系统错误中断将一直保持待处理状态，直到访客通过取消掩码PSTATE.A来接受该异常。运行VCPU可能会导致其接受一个待处理的SErrors，或者进行访问导致SErrors变为待处理状态。事件描述仅在VCPU未运行时有效。

此API提供了一种读取和写入待处理“事件”状态的方法，这些状态对访客是不可见的。为了保存、恢复或迁移VCPU，可以使用此GET/SET API读取然后写入表示状态的结构体，以及其他的访客可见寄存器。无法取消已经变为待处理状态的SErrors。

用户空间中模拟的设备也可能希望生成SErrors。为此，可以通过用户空间填充事件结构体。首先应该读取当前状态，以确保没有现有的SErrors待处理。如果有现有的SErrors待处理，则应遵循架构的“多重SErrors中断”规则。（DDI0587.a “ARM可靠性、可用性和可服务性（RAS）规范”的2.5.3节）
### SError 异常总是有一个 ESR 值。某些 CPU 具有指定虚拟 SError 的 ESR 值的能力。这些系统将宣传 `KVM_CAP_ARM_INJECT_SERROR_ESR`。在这种情况下，读取 `exception.has_esr` 时其值始终是非零的，并且使一个 SError 待处理的代理应该在 `exception.serror_esr` 的低 24 位中指定 ISS 字段。如果系统支持 `KVM_CAP_ARM_INJECT_SERROR_ESR`，但用户空间将 `exception.has_esr` 设置为零，则 KVM 将选择一个 ESR 值。在一个不支持 `exception.has_esr` 的系统上设置它会返回 `-EINVAL`。设置 `exception.serror_esr` 中除了低 24 位之外的任何值都会返回 `-EINVAL`。无法读取通过 `KVM_SET_VCPU_EVENTS` 或其他方式注入的外部中止（异常），因为此类异常总是直接发送到虚拟 CPU。

```c
struct kvm_vcpu_events {
    struct {
        __u8 serror_pending;
        __u8 serror_has_esr;
        __u8 ext_dabt_pending;
        /* 对齐到 8 字节 */
        __u8 pad[5];
        __u64 serror_esr;
    } exception;
    __u32 reserved[12];
};
```

### 4.32 KVM_SET_VCPU_EVENTS
------------------------

**功能：** KVM_CAP_VCPU_EVENTS  
**扩展：** KVM_CAP_INTR_SHADOW  
**架构：** x86, arm64  
**类型：** vcpu ioctl  
**参数：** struct kvm_vcpu_events (输入)  
**返回值：** 成功返回 0，失败返回 -1

#### X86:
^^^^

设置待处理的异常、中断和 NMI 以及 vcpu 的相关状态。  
参见 `KVM_GET_VCPU_EVENTS` 以获取数据结构。  
由运行中的 VCPU 异步修改的字段可以排除在更新之外。这些字段包括 `nmi.pending`, `sipi_vector`, `smi.smm`, `smi.pending`。为了不覆盖当前内核状态，请清除标志字段中的相应位。这些位是：

| 标志                                 | 描述                                       |
|------------------------------------|------------------------------------------|
| KVM_VCPUEVENT_VALID_NMI_PENDING     | 将 `nmi.pending` 转移到内核                     |
| KVM_VCPUEVENT_VALID_SIPI_VECTOR     | 转移 `sipi_vector`                         |
| KVM_VCPUEVENT_VALID_SMM             | 转移 `smi` 子结构                          |

如果 `KVM_CAP_INTR_SHADOW` 可用，则可以在标志字段中设置 `KVM_VCPUEVENT_VALID_SHADOW` 来表示 `interrupt.shadow` 包含有效状态并应写入 VCPU。  
只有当 `KVM_CAP_X86_SMM` 可用时，才能设置 `KVM_VCPUEVENT_VALID_SMM`。  
如果 `KVM_CAP_EXCEPTION_PAYLOAD` 启用，则可以在标志字段中设置 `KVM_VCPUEVENT_VALID_PAYLOAD` 来表示 `exception_has_payload`, `exception_payload`, `exception.pending` 字段包含有效状态并应写入 VCPU。  
如果 `KVM_CAP_X86_TRIPLE_FAULT_EVENT` 启用，则可以在标志字段中设置 `KVM_VCPUEVENT_VALID_TRIPLE_FAULT` 来表示 `triple_fault` 字段包含有效状态并应写入 VCPU。
### ARM64:

^^^^^^

用户空间可能需要向虚拟机注入多种类型的事件。为该VCPU设置待处理的SErron异常状态。无法取消已设置为待处理的SError。
如果虚拟机对I/O内存进行了访问，而这些访问无法由用户空间处理（例如，由于缺少指令综合征解码信息或访问的IPA没有映射设备），则用户空间可以请求内核使用退出时的地址在VCPU上注入外部中止。在不是KVM_EXIT_MMIO或KVM_EXIT_ARM_NISV的退出后设置ext_dabt_pending是一个编程错误。此功能仅在系统支持KVM_CAP_ARM_INJECT_EXT_DABT的情况下可用。这是一个帮助函数，用于在不同用户空间实现中统一报告上述情况下的访问方式。然而，用户空间仍然可以通过使用KVM_SET_ONE_REG API操作单个寄存器来模拟所有Arm异常。参见KVM_GET_VCPU_EVENTS获取数据结构。

#### 4.33 KVM_GET_DEBUGREGS
--------------------------

**能力**: KVM_CAP_DEBUGREGS  
**架构**: x86  
**类型**: vm ioctl  
**参数**: struct kvm_debugregs (输出)  
**返回值**: 成功返回0，失败返回-1  

从VCPU读取调试寄存器：

```c
struct kvm_debugregs {
    __u64 db[4];
    __u64 dr6;
    __u64 dr7;
    __u64 flags;
    __u64 reserved[9];
};
```

#### 4.34 KVM_SET_DEBUGREGS
--------------------------

**能力**: KVM_CAP_DEBUGREGS  
**架构**: x86  
**类型**: vm ioctl  
**参数**: struct kvm_debugregs (输入)  
**返回值**: 成功返回0，失败返回-1  

将调试寄存器写入VCPU。参见KVM_GET_DEBUGREGS获取数据结构。flags字段目前未使用，在输入时必须清零。

#### 4.35 KVM_SET_USER_MEMORY_REGION
-------------------------------

**能力**: KVM_CAP_USER_MEMORY  
**架构**: 所有架构  
**类型**: vm ioctl  
**参数**: struct kvm_userspace_memory_region (输入)  
**返回值**: 成功返回0，失败返回-1  

```c
struct kvm_userspace_memory_region {
    __u32 slot;
    __u32 flags;
    __u64 guest_phys_addr;
    __u64 memory_size; /* 字节 */
    __u64 userspace_addr; /* 用户空间分配内存的起始地址 */
};
```

```c
/* 对于kvm_userspace_memory_region::flags */
#define KVM_MEM_LOG_DIRTY_PAGES   (1UL << 0)
#define KVM_MEM_READONLY          (1UL << 1)
```

此ioctl允许用户创建、修改或删除一个虚拟物理内存槽。“slot”的第0到第15位指定槽ID，这个值应小于每个虚拟机支持的最大用户内存槽数量。最大允许槽数可以通过KVM_CAP_NR_MEMSLOTS查询。
如果支持KVM_CAP_MULTI_ADDRESS_SPACE，“slot”的第16到第31位指定正在修改的地址空间。它们必须小于KVM_CHECK_EXTENSION返回的KVM_CAP_MULTI_ADDRESS_SPACE能力值。不同地址空间中的槽是无关的；槽重叠的限制仅适用于每个地址空间内部。
删除一个内存槽是通过将内存大小设置为零来完成的。当修改已存在的内存槽时，它可能会在客户机物理内存空间中移动，或者其标志可能被修改，但不能调整其大小。
该区域的内存从由字段`userspace_addr`指定的地址开始分配，该字段必须指向整个内存槽大小所对应的用户可访问内存。任何对象都可以支持这部分内存，包括匿名内存、普通文件和hugetlbfs。
对于支持某种形式地址标记的架构，`userspace_addr`必须是一个未标记的地址。
建议`guest_phys_addr`和`userspace_addr`的最低21位相同。这允许客户机中的大页由主机中的大页支持。
标志字段支持两个标志：`KVM_MEM_LOG_DIRTY_PAGES`和`KVM_MEM_READONLY`。前者可以设置以指示KVM跟踪槽内内存的写入操作。参见`KVM_GET_DIRTY_LOG` ioctl了解如何使用它。后者可以在KVM_CAP_READONLY_MEM功能允许的情况下设置，以使新的内存槽只读。在这种情况下，对这部分内存的写入会被作为KVM_EXIT_MMIO退出发送到用户空间。
当KVM_CAP_SYNC_MMU功能可用时，内存区域的支持变化会自动反映到客户机中。例如，影响该区域的mmap()调用会立即可见。另一个例子是madvise(MADV_DROP)。
注意：在arm64上，由页表遍历器生成的写操作（例如更新访问和脏标志）永远不会导致带有KVM_MEM_READONLY标志的槽触发KVM_EXIT_MMIO退出。这是因为KVM无法提供页表遍历器将要写入的数据，使得模拟访问变得不可能。相反，在客户机中注入一个中止（如果页表更新的原因是加载或存储，则为数据中止；如果是指令获取，则为指令中止）。

### 4.36 KVM_SET_TSS_ADDR
---------------------

- **功能**：KVM_CAP_SET_TSS_ADDR
- **架构**：x86
- **类型**：vm ioctl
- **参数**：unsigned long tss_address (输入)
- **返回值**：成功时返回0，错误时返回-1

此ioctl定义了客户机物理地址空间中三页区域的物理地址。该区域必须位于客户机物理地址空间的前4GB内，并且不得与任何内存槽或任何mmio地址冲突。如果客户机访问这个内存区域，可能会导致其功能异常。
此ioctl在基于Intel的主机上是必需的。这是因为在Intel硬件上的虚拟化实现中存在一个特殊需求（详见内部文档）。
### 4.37 KVM_ENABLE_CAP

#### 功能：KVM_CAP_ENABLE_CAP
- **架构**：mips, ppc, s390, x86, loongarch
- **类型**：vcpu ioctl
- **参数**：struct kvm_enable_cap（输入）
- **返回值**：成功返回 0；失败返回 -1

#### 功能：KVM_CAP_ENABLE_CAP_VM
- **架构**：所有架构
- **类型**：vm ioctl
- **参数**：struct kvm_enable_cap（输入）
- **返回值**：成功返回 0；失败返回 -1

**注意**：

并非所有扩展默认都是启用的。使用此 ioctl，应用程序可以启用一个扩展，使其对客户机可用。在不支持此 ioctl 的系统上，它总是失败。在支持此 ioctl 的系统上，它仅适用于可启用的支持扩展。要检查某个功能是否可以启用，应使用 KVM_CHECK_EXTENSION ioctl。

```c
struct kvm_enable_cap {
    /* 输入 */
    __u32 cap;

    // 要启用的功能

    __u32 flags;

    // 保留位字段，目前必须为 0

    __u64 args[4];

    // 启用功能所需的参数。如果某个功能需要初始值才能正常工作，这些值应该放在这里

    __u8  pad[64];
};
```

对于特定于 vcpu 的功能，应使用 vcpu ioctl；对于整个 vm 的功能，应使用 vm ioctl。

### 4.38 KVM_GET_MP_STATE

#### 功能：KVM_CAP_MP_STATE
- **架构**：x86, s390, arm64, riscv, loongarch
- **类型**：vcpu ioctl
- **参数**：struct kvm_mp_state（输出）
- **返回值**：成功返回 0；失败返回 -1

```c
struct kvm_mp_state {
    __u32 mp_state;
};
```

返回 vcpu 当前的“多处理器状态”（即使在单处理器客户机上也有效）。

可能的值如下：

| 值                       | 描述                                                                                         |
|--------------------------|----------------------------------------------------------------------------------------------|
| KVM_MP_STATE_RUNNABLE    | vcpu 正在运行。[x86,arm64,riscv,loongarch]                                                    |
| KVM_MP_STATE_UNINITIALIZED | vcpu 是一个应用处理器（AP），尚未接收到 INIT 信号。[x86]                                      |
| KVM_MP_STATE_INIT_RECEIVED | vcpu 已接收到 INIT 信号，并且现在准备好接收 SIPI。[x86]                                        |
| KVM_MP_STATE_HALTED      | vcpu 执行了 HLT 指令，并等待中断。[x86]                                                        |
| KVM_MP_STATE_SIPI_RECEIVED | vcpu 刚刚接收到 SIPI（可通过 KVM_GET_VCPU_EVENTS 获取向量）。[x86]                              |
| KVM_MP_STATE_STOPPED     | vcpu 已停止。[s390,arm64,riscv]                                                                |
| KVM_MP_STATE_CHECK_STOP  | vcpu 处于特殊错误状态。[s390]                                                                  |
| KVM_MP_STATE_OPERATING   | vcpu 正在运行或暂停。[s390]                                                                    |
| KVM_MP_STATE_LOAD        | vcpu 处于特殊加载/启动状态。[s390]                                                             |
| KVM_MP_STATE_SUSPENDED   | vcpu 处于挂起状态，并等待唤醒事件。[arm64]                                                      |

在 x86 架构中，此 ioctl 只有在 KVM_CREATE_IRQCHIP 之后才有用。没有内核中的 irqchip，这些架构上的多处理器状态必须由用户空间维护。

对于 arm64：
^^^^^^^^^^

如果 vCPU 处于 KVM_MP_STATE_SUSPENDED 状态，KVM 将模拟执行 WFI 指令的架构行为。
如果检测到唤醒事件，KVM 将以 `KVM_SYSTEM_EVENT` 退出到用户空间，其中事件类型为 `KVM_SYSTEM_EVENT_WAKEUP`。如果用户空间希望处理这个唤醒事件，必须将 vCPU 的多处理器状态设置为 `KVM_MP_STATE_RUNNABLE`。如果不这样做，KVM 将继续在后续的 `KVM_RUN` 调用中等待唤醒事件。

**警告：**

如果用户空间打算让 vCPU 保持在 `SUSPENDED` 状态，强烈建议用户空间采取措施抑制唤醒事件（例如屏蔽中断）。否则，后续的 `KVM_RUN` 调用会立即退出，并带有 `KVM_SYSTEM_EVENT_WAKEUP` 事件，从而无意中浪费 CPU 周期。

此外，如果用户空间采取了抑制唤醒事件的措施，强烈建议在使 vCPU 变为 `RUNNABLE` 状态时恢复 vCPU 的原始状态。例如，如果用户空间通过屏蔽一个待处理中断来抑制唤醒，则应在返回控制权给来宾之前取消屏蔽该中断。

对于 RISC-V：
^^^^^^^^^^^

有效的状态只有 `KVM_MP_STATE_STOPPED` 和 `KVM_MP_STATE_RUNNABLE`，分别表示 vCPU 是否暂停。
在 LoongArch 上，仅使用 `KVM_MP_STATE_RUNNABLE` 状态来表示 vCPU 是否可运行。

### 4.39 KVM_SET_MP_STATE
-------------------------

- **功能**: `KVM_CAP_MP_STATE`
- **架构**: x86, s390, arm64, riscv, loongarch
- **类型**: vcpu ioctl
- **参数**: `struct kvm_mp_state` （输入）
- **返回值**: 成功返回 0；失败返回 -1

设置 vCPU 的当前“多处理器状态”；有关参数，请参见 `KVM_GET_MP_STATE`

在 x86 架构上，此 ioctl 只有在 `KVM_CREATE_IRQCHIP` 之后才有用。如果没有内核中的 irq 芯片，这些架构上的多处理器状态必须由用户空间维护。

对于 arm64/RISC-V：
^^^^^^^^^^^^^^^^

有效的状态只有 `KVM_MP_STATE_STOPPED` 和 `KVM_MP_STATE_RUNNABLE`，分别表示 vCPU 是否应暂停。
在 LoongArch 上，仅使用 `KVM_MP_STATE_RUNNABLE` 状态来表示 vCPU 是否可运行。

### 4.40 KVM_SET_IDENTITY_MAP_ADDR
----------------------------------

- **功能**: `KVM_CAP_SET_IDENTITY_MAP_ADDR`
- **架构**: x86
- **类型**: vm ioctl
- **参数**: `unsigned long identity` （输入）
- **返回值**: 成功返回 0，失败返回 -1

此 ioctl 定义了来宾物理地址空间中一页区域的物理地址。该区域必须位于来宾物理地址空间的前 4GB 内，并且不得与任何内存槽或任何 mmio 地址冲突。如果来宾访问此内存区域，可能会导致其功能异常。
### 设置地址为0将导致重置地址为其默认值（0xfffbc000）
此ioctl在基于Intel的主机上是必需的。在Intel硬件上需要此ioctl是因为虚拟化实现中存在一个特殊之处（请参阅内部文档以获取更多信息）。
如果任何VCPU已经创建，则会失败。

### 4.41 KVM_SET_BOOT_CPU_ID
------------------------

- **功能**: KVM_CAP_SET_BOOT_CPU_ID
- **架构**: x86
- **类型**: VM ioctl
- **参数**: unsigned long vcpu_id
- **返回值**: 成功时返回0，错误时返回-1

定义哪个VCPU是引导处理器（BSP）。值与KVM_CREATE_VCPU中的VCPU ID相同。如果不调用此ioctl，默认值为VCPU 0。此ioctl必须在创建VCPU之前调用，否则将返回EBUSY错误。

### 4.42 KVM_GET_XSAVE
------------------

- **功能**: KVM_CAP_XSAVE
- **架构**: x86
- **类型**: VCPU ioctl
- **参数**: struct kvm_xsave（输出）
- **返回值**: 成功时返回0，错误时返回-1

```c
struct kvm_xsave {
    __u32 region[1024];
    __u32 extra[0];
};
```

此ioctl会将当前VCPU的xsave结构复制到用户空间。

### 4.43 KVM_SET_XSAVE
------------------

- **功能**: KVM_CAP_XSAVE 和 KVM_CAP_XSAVE2
- **架构**: x86
- **类型**: VCPU ioctl
- **参数**: struct kvm_xsave（输入）
- **返回值**: 成功时返回0，错误时返回-1

```c
struct kvm_xsave {
    __u32 region[1024];
    __u32 extra[0];
};
```

此ioctl会将用户空间的xsave结构复制到内核。它复制的字节数等于通过 `KVM_CHECK_EXTENSION(KVM_CAP_XSAVE2)` 调用在vm文件描述符上调用时返回的大小值。`KVM_CHECK_EXTENSION(KVM_CAP_XSAVE2)` 返回的大小值始终至少为4096。目前，只有当使用 `arch_prctl()` 启用了动态特性时，该值才大于4096，但将来可能会发生变化。`struct kvm_xsave` 中状态保存区域的偏移遵循主机上的CPUID leaf 0xD的内容。

### 4.44 KVM_GET_XCRS
-----------------

- **功能**: KVM_CAP_XCRS
- **架构**: x86
- **类型**: VCPU ioctl
- **参数**: struct kvm_xcrs（输出）
- **返回值**: 成功时返回0，错误时返回-1

```c
struct kvm_xcr {
    __u32 xcr;
    __u32 reserved;
    __u64 value;
};

struct kvm_xcrs {
    __u32 nr_xcrs;
    __u32 flags;
    struct kvm_xcr xcrs[KVM_MAX_XCRS];
    __u64 padding[16];
};
```

此ioctl会将当前VCPU的xcrs复制到用户空间。

### 4.45 KVM_SET_XCRS
-----------------

- **功能**: KVM_CAP_XCRS
- **架构**: x86
- **类型**: VCPU ioctl
- **参数**: struct kvm_xcrs（输入）
- **返回值**: 成功时返回0，错误时返回-1

```c
struct kvm_xcr {
    __u32 xcr;
    __u32 reserved;
    __u64 value;
};

struct kvm_xcrs {
    __u32 nr_xcrs;
    __u32 flags;
    struct kvm_xcr xcrs[KVM_MAX_XCRS];
    __u64 padding[16];
};
```

此ioctl会将VCPU的xcr设置为用户空间指定的值。
### 4.46 KVM_GET_SUPPORTED_CPUID
----------------------

**功能:** KVM_CAP_EXT_CPUID  
**架构:** x86  
**类型:** 系统 ioctl  
**参数:** struct kvm_cpuid2 (输入/输出)  
**返回值:** 成功时返回 0，错误时返回 -1

```c
struct kvm_cpuid2 {
    __u32 nent;
    __u32 padding;
    struct kvm_cpuid_entry2 entries[0];
};

#define KVM_CPUID_FLAG_SIGNIFICANT_INDEX      BIT(0)
#define KVM_CPUID_FLAG_STATEFUL_FUNC          BIT(1) /* 已弃用 */
#define KVM_CPUID_FLAG_STATE_READ_NEXT        BIT(2) /* 已弃用 */

struct kvm_cpuid_entry2 {
    __u32 function;
    __u32 index;
    __u32 flags;
    __u32 eax;
    __u32 ebx;
    __u32 ecx;
    __u32 edx;
    __u32 padding[3];
};
```

此 ioctl 返回硬件和 KVM 默认配置下支持的 x86 cpuid 特性。用户空间可以使用此 ioctl 返回的信息来构建与硬件、内核和用户空间能力一致的 cpuid 信息（用于 KVM_SET_CPUID2），并满足用户需求（例如，用户可能希望限制 cpuid 以模拟较旧的硬件，或在集群中保持特性一致性）。

动态启用的特性位需要在调用此 ioctl 之前通过 `arch_prctl()` 请求。未请求的特性位将从结果中排除。

注意某些功能（如 KVM_CAP_X86_DISABLE_EXITS）可能会暴露 KVM 默认配置下不支持的 cpuid 特性（例如 MONITOR）。如果用户空间启用了这些功能，则需要相应地修改此 ioctl 的结果。

用户空间通过传递一个 kvm_cpuid2 结构来调用 KVM_GET_SUPPORTED_CPUID，其中 'nent' 字段表示变长数组 'entries' 中的条目数量。如果条目数量不足以描述 CPU 能力，则返回错误（E2BIG）。如果数量过多，则调整 'nent' 字段并返回错误（ENOMEM）。如果数量恰好合适，则调整 'nent' 字段为 'entries' 数组中的有效条目数，并填充该数组。

返回的条目是主机 cpuid 指令返回的结果，未知或不受支持的特性被屏蔽。某些特性（如 x2apic）可能不在主机 CPU 中存在，但如果 KVM 可以高效地模拟它们，则会暴露出来。每个条目的字段定义如下：

- function: 用于获取条目的 eax 值。
- index: 用于获取条目的 ecx 值（对于受 ecx 影响的条目）。
- flags: 以下标志的一个或多个或值：
  - KVM_CPUID_FLAG_SIGNIFICANT_INDEX: 如果 index 字段有效。
- eax, ebx, ecx, edx: 对于给定的 function/index 组合，cpuid 指令返回的值。

TSC 截止定时器特性（CPUID 叶子 1，ecx[24]）始终返回为 false，因为该特性依赖于 KVM_CREATE_IRQCHIP 支持本地 APIC。相反，它通过以下 ioctl 报告：

```c
ioctl(KVM_CHECK_EXTENSION, KVM_CAP_TSC_DEADLINE_TIMER)
```

如果上述 ioctl 返回 true 并且你使用了 KVM_CREATE_IRQCHIP，或者你在用户空间中模拟该特性，则可以在 KVM_SET_CPUID2 中启用该特性。

### 4.47 KVM_PPC_GET_PVINFO
--------------------------

**功能:** KVM_CAP_PPC_GET_PVINFO  
**架构:** ppc  
**类型:** vm ioctl  
**参数:** struct kvm_ppc_pvinfo (输出)  
**返回值:** 成功时返回 0，错误时返回非零值

```c
struct kvm_ppc_pvinfo {
    __u32 flags;
    __u32 hcall[4];
    __u8  pad[108];
};
```

此 ioctl 获取需要通过设备树或其他方式传递给来宾的 PV 特定信息。
hcall 数组定义了构成超调用的 4 条指令。
如果以后在此结构中添加任何其他字段，将在 flags 位图中设置一个标志。
flags 位图定义如下：

```c
/* 主机支持 ePAPR idle 超调用 */
#define KVM_PPC_PVINFO_FLAGS_EV_IDLE   (1<<0)
```

### 4.52 KVM_SET_GSI_ROUTING
---------------------------

**功能:** KVM_CAP_IRQ_ROUTING  
**架构:** x86, s390, arm64  
**类型:** vm ioctl  
**参数:** struct kvm_irq_routing (输入)  
**返回值:** 成功时返回 0，错误时返回 -1

设置 GSI 路由表条目，覆盖任何先前设置的条目。
在 arm64 上，GSI 路由具有以下限制：

- GSI 路由不适用于 KVM_IRQ_LINE，仅适用于 KVM_IRQFD。
```c
// kvm_irq_routing 结构体定义
struct kvm_irq_routing {
    __u32 nr;           // 路由条目数量
    __u32 flags;        // 标志位
    struct kvm_irq_routing_entry entries[0];  // 路由条目数组
};

// 目前没有指定任何标志位，对应字段必须设为零

// kvm_irq_routing_entry 结构体定义
struct kvm_irq_routing_entry {
    __u32 gsi;          // 全局中断号
    __u32 type;         // 类型
    __u32 flags;        // 标志位
    __u32 pad;          // 填充
    union {
        struct kvm_irq_routing_irqchip irqchip;
        struct kvm_irq_routing_msi msi;
        struct kvm_irq_routing_s390_adapter adapter;
        struct kvm_irq_routing_hv_sint hv_sint;
        struct kvm_irq_routing_xen_evtchn xen_evtchn;
        __u32 pad[8];   // 填充
    } u;
};

// gsi 路由条目类型定义
#define KVM_IRQ_ROUTING_IRQCHIP 1
#define KVM_IRQ_ROUTING_MSI 2
#define KVM_IRQ_ROUTING_S390_ADAPTER 3
#define KVM_IRQ_ROUTING_HV_SINT 4
#define KVM_IRQ_ROUTING_XEN_EVTCHN 5

// 标志位定义
- KVM_MSI_VALID_DEVID：与 KVM_IRQ_ROUTING_MSI 路由条目类型一起使用，指定 devid 字段包含有效值。每个虚拟机的 KVM_CAP_MSI_DEVID 功能会宣传提供设备 ID 的需求。如果没有此功能，则用户空间不应设置 KVM_MSI_VALID_DEVID 标志，因为 ioctl 可能会失败
- 否则为零

// kvm_irq_routing_irqchip 结构体定义
struct kvm_irq_routing_irqchip {
    __u32 irqchip;      // 中断控制器
    __u32 pin;          // 引脚
};

// kvm_irq_routing_msi 结构体定义
struct kvm_irq_routing_msi {
    __u32 address_lo;   // 地址低 32 位
    __u32 address_hi;   // 地址高 32 位
    __u32 data;         // 数据
    union {
        __u32 pad;      // 填充
        __u32 devid;    // 设备 ID
    };
};

// 如果设置了 KVM_MSI_VALID_DEVID，则 devid 包含写入 MSI 消息的设备的唯一标识符。对于 PCI，这通常是 BFD 标识符的低 16 位
在 x86 上，除非启用了 KVM_CAP_X2APIC_API 功能中的 KVM_X2APIC_API_USE_32BIT_IDS 特性，否则忽略 address_hi。如果启用，则 address_hi 的 31-8 位提供目标 ID 的 31-8 位。address_hi 的 7-0 位必须为零

// kvm_irq_routing_s390_adapter 结构体定义
struct kvm_irq_routing_s390_adapter {
    __u64 ind_addr;     // 指示地址
    __u64 summary_addr; // 汇总地址
    __u64 ind_offset;   // 指示偏移量
    __u32 summary_offset; // 汇总偏移量
    __u32 adapter_id;   // 适配器 ID
};

// kvm_irq_routing_hv_sint 结构体定义
struct kvm_irq_routing_hv_sint {
    __u32 vcpu;         // 虚拟 CPU
    __u32 sint;         // 软中断
};

// kvm_irq_routing_xen_evtchn 结构体定义
struct kvm_irq_routing_xen_evtchn {
    __u32 port;         // 端口
    __u32 vcpu;         // 虚拟 CPU
    __u32 priority;     // 优先级
};

// 当 KVM_CAP_XEN_HVM 包含 KVM_XEN_HVM_CONFIG_EVTCHN_2LEVEL 位时，支持路由到 Xen 事件通道。尽管存在优先级字段，但仅支持 KVM_XEN_HVM_CONFIG_EVTCHN_2LEVEL 值，这意味着通过两层事件通道传递。将来可能会添加 FIFO 事件通道支持

4.55 KVM_SET_TSC_KHZ
--------------------
:功能: KVM_CAP_TSC_CONTROL / KVM_CAP_VM_TSC_CONTROL
:架构: x86
:类型: vcpu ioctl / vm ioctl
:参数: 虚拟 tsc_khz
:返回: 成功返回 0，失败返回 -1

指定虚拟机的 TSC 频率。频率单位为 KHz
如果广告了 KVM_CAP_VM_TSC_CONTROL 功能，则此 ioctl 还可以用于设置随后创建的 vCPUs 的初始 TSC 频率

4.56 KVM_GET_TSC_KHZ
--------------------
:功能: KVM_CAP_GET_TSC_KHZ / KVM_CAP_VM_TSC_CONTROL
:架构: x86
:类型: vcpu ioctl / vm ioctl
:参数: 无
:返回: 成功返回虚拟 TSC-KHZ，失败返回负值

返回来宾的 TSC 频率。返回值的单位为 KHz。如果主机的 TSC 不稳定，则此 ioctl 返回 -EIO 作为错误

4.57 KVM_GET_LAPIC
------------------
:功能: KVM_CAP_IRQCHIP
:架构: x86
:类型: vcpu ioctl
:参数: struct kvm_lapic_state (输出)
:返回: 成功返回 0，失败返回 -1

#define KVM_APIC_REG_SIZE 0x400
struct kvm_lapic_state {
    char regs[KVM_APIC_REG_SIZE];
};

读取本地 APIC 寄存器并将它们复制到输入参数中。数据格式和布局与架构手册中所述相同
如果启用了 KVM_CAP_X2APIC_API 功能中的 KVM_X2APIC_API_USE_32BIT_IDS 特性，则 APIC_ID 寄存器的格式取决于其 VCPU 的 APIC 模式（由 MSR_IA32_APICBASE 报告）。x2APIC 将 APIC ID 存储在 APIC_ID 寄存器（字节 32-35）中。xAPIC 只允许 8 位 APIC ID，该 ID 存储在 APIC 寄存器的 31-24 位中，或等效地存储在 struct kvm_lapic_state 的 regs 字段的字节 35 中。然后必须在使用 KVM_SET_MSR 设置 MSR_IA32_APICBASE 之后调用 KVM_GET_LAPIC
```
如果禁用了KVM_X2APIC_API_USE_32BIT_IDS 功能，struct kvm_lapic_state 始终使用 xAPIC 格式。

4.58 KVM_SET_LAPIC
------------------

:功能: KVM_CAP_IRQCHIP
:架构: x86
:类型: vcpu ioctl
:参数: struct kvm_lapic_state (输入)
:返回值: 成功时返回 0，失败时返回 -1

::

  #define KVM_APIC_REG_SIZE 0x400
  struct kvm_lapic_state {
	char regs[KVM_APIC_REGSize];
  };

将输入参数复制到本地 APIC 寄存器。数据格式和布局与架构手册中记录的一致。
APIC ID 寄存器（位于 struct kvm_lapic_state 的 regs 字段的第 32 到 35 字节）的格式取决于 KVM_CAP_X2APIC_API 能力的状态。
请参阅 KVM_GET_LAPIC 中的注释。

4.59 KVM_IOEVENTFD
------------------

:功能: KVM_CAP_IOEVENTFD
:架构: 所有架构
:类型: vm ioctl
:参数: struct kvm_ioeventfd (输入)
:返回值: 成功时返回 0，失败时返回非零值

此 ioctl 将一个 ioeventfd 附加或分离到虚拟机中的合法 pio/mmio 地址。当虚拟机在已注册地址上进行写入操作时，将触发提供的事件而不是引发退出。

::

  struct kvm_ioeventfd {
	__u64 datamatch;
	__u64 addr;        /* 合法的 pio/mmio 地址 */
	__u32 len;         /* 0, 1, 2, 4, 或 8 字节 */
	__s32 fd;
	__u32 flags;
	__u8  pad[36];
  };

对于 s390 上的 virtio-ccw 设备的特殊情况，ioevent 与子通道/虚拟队列元组相匹配。
定义了以下标志：

::

  #define KVM_IOEVENTFD_FLAG_DATAMATCH (1 << kvm_ioeventfd_flag_nr_datamatch)
  #define KVM_IOEVENTFD_FLAG_PIO       (1 << kvm_ioeventfd_flag_nr_pio)
  #define KVM_IOEVENTFD_FLAG_DEASSIGN  (1 << kvm_ioeventfd_flag_nr_deassign)
  #define KVM_IOEVENTFD_FLAG_VIRTIO_CCW_NOTIFY \
	(1 << kvm_ioeventfd_flag_nr_virtio_ccw_notify)

如果设置了 datamatch 标志，则只有当写入已注册地址的值等于 struct kvm_ioeventfd 中的 datamatch 时才会触发事件。
对于 virtio-ccw 设备，addr 包含子通道 ID，而 datamatch 包含虚拟队列索引。
使用 KVM_CAP_IOEVENTFD_ANY_LENGTH，允许长度为零的 ioeventfd，并且内核会忽略虚拟机写入的长度，可能会获得更快的 vmexit。
该速度提升可能仅适用于特定架构，但 ioeventfd 仍然有效。
4.60 KVM_DIRTY_TLB
------------------

:功能: KVM_CAP_SW_TLB
:架构: ppc
:类型: vcpu ioctl
:参数: struct kvm_dirty_tlb（输入）
:返回值: 成功时返回0，出错时返回-1

::

  struct kvm_dirty_tlb {
	__u64 bitmap;
	__u32 num_dirty;
  };

每当用户空间修改了共享TLB中的条目时，必须在调用关联vcpu上的KVM_RUN之前调用此函数。
“bitmap”字段是用户空间中一个数组的地址。该数组包含的位数等于上次成功调用KVM_CONFIG_TLB确定的TLB条目的总数，并向上取整到最接近的64的倍数。
每个位对应一个TLB条目，顺序与共享TLB数组中的顺序相同。
该数组为小端字节序：位0是第一个字节的最低有效位，位8是第二个字节的最低有效位等，以此类推。这避免了不同字长带来的复杂性。
“num_dirty”字段是一个性能提示，用于让KVM决定是否应该跳过处理位图并直接无效化所有内容。它必须设置为位图中设置位的数量。

4.62 KVM_CREATE_SPAPR_TCE
-------------------------

:功能: KVM_CAP_SPAPR_TCE
:架构: powerpc
:类型: vm ioctl
:参数: struct kvm_create_spapr_tce（输入）
:返回值: 用于操作创建的TCE表的文件描述符

这会创建一个虚拟TCE（转换控制条目）表，这是一个用于PAPR风格虚拟I/O的IOMMU。它用于将虚拟I/O中使用的逻辑地址转换为访客物理地址，并为PAPR虚拟I/O提供散列/收集功能。

::

  /* 用于 KVM_CAP_SPAPR_TCE */
  struct kvm_create_spapr_tce {
	__u64 liobn;
	__u32 window_size;
  };

liobn字段给出了要为其创建TCE表的逻辑IO总线编号。window_size字段指定了此TCE表将要转换的DMA窗口大小——该表将为DMA窗口中的每4KiB包含一个64位TCE条目。
当访客对已使用此ioctl()创建TCE表的liobn发出H_PUT_TCE hcall时，内核将以真实模式处理它，并更新TCE表。对于其他liobn的H_PUT_TCE调用将导致vm退出，必须由用户空间处理。
返回值是一个可以传递给mmap(2)以将创建的TCE表映射到用户空间的文件描述符。这使得用户空间可以读取内核处理的H_PUT_TCE调用写入的条目，并且还允许用户空间直接更新TCE表，在某些情况下很有用。
4.63 KVM_ALLOCATE_RMA
---------------------
:功能: KVM_CAP_PPC_RMA
:架构: powerpc
:类型: vm ioctl
:参数: struct kvm_allocate_rma（输出）
:返回值: 映射分配的RMA的文件描述符

这从内核在启动时分配的池中分配一个真实模式区域（RMA）。RMA是一个物理连续且对齐的内存区域，用于较旧的POWER处理器提供KVM客户机中真实模式（MMU关闭）访问所需的内存。POWER处理器支持一组RMA大小，通常包括64MB、128MB、256MB和一些更大的2的幂。
```
/* 对于KVM_ALLOCATE_RMA */
struct kvm_allocate_rma {
    __u64 rma_size;
};
```
返回值是一个文件描述符，可以传递给mmap(2)，以将分配的RMA映射到用户空间。然后可以将映射的区域传递给KVM_SET_USER_MEMORY_REGION ioctl，以将其作为虚拟机的RMA。RMA的字节大小（在主机内核启动时固定）会返回在参数结构的rma_size字段中。如果支持KVM_ALLOCATE_RMA ioctl，则KVM_CAP_PPC_RMA功能为1或2；如果是2，则表示处理器要求所有虚拟机都有RMA；如果是1，则表示处理器可以使用RMA但不要求必须使用，因为它支持虚拟RMA（VRMA）设施。

4.64 KVM_NMI
------------
:功能: KVM_CAP_USER_NMI
:架构: x86
:类型: vcpu ioctl
:参数: 无
:返回值: 成功返回0，失败返回-1

在线程的vcpu上排队一个NMI。请注意，只有在未调用KVM_CREATE_IRQCHIP的情况下这是明确定义的，因为这是一个虚拟CPU核心与虚拟本地APIC之间的接口。在调用KVM_CREATE_IRQCHIP之后，此接口完全在内核内部模拟。要使用此功能在KVM_CREATE_IRQCHIP后模拟LINT1输入，请使用以下算法：
- 暂停vcpu
- 读取本地APIC的状态（KVM_GET_LAPIC）
- 检查更改LINT1是否会排队一个NMI（参见LINT1的LVT条目）
- 如果是，则发出KVM_NMI
- 恢复vcpu

一些客户机配置了LINT1 NMI输入以导致恐慌，有助于调试。

4.65 KVM_S390_UCAS_MAP
----------------------
:功能: KVM_CAP_S390_UCONTROL
:架构: s390
:类型: vcpu ioctl
:参数: struct kvm_s390_ucas_mapping（输入）
:返回值: 成功返回0

参数定义如下：
```
struct kvm_s390_ucas_mapping {
    __u64 user_addr;
    __u64 vcpu_addr;
    __u64 length;
};
```
此ioctl将“user_addr”处长度为“length”的内存映射到vcpu地址空间的“vcpu_addr”起始位置。所有参数都需要按1兆字节对齐。

4.66 KVM_S390_UCAS_UNMAP
------------------------
:功能: KVM_CAP_S390_UCONTROL
:架构: s390
:类型: vcpu ioctl
:参数: struct kvm_s390_ucas_mapping（输入）
:返回值: 成功返回0

参数定义如下：
```
struct kvm_s390_ucas_mapping {
    __u64 user_addr;
    __u64 vcpu_addr;
    __u64 length;
};
```
此ioctl取消映射vcpu地址空间中从“vcpu_addr”开始长度为“length”的内存。“user_addr”字段被忽略。所有参数都需要按1兆字节对齐。

4.67 KVM_S390_VCPU_FAULT
------------------------
:功能: KVM_CAP_S390_UCONTROL
:架构: s390
:类型: vcpu ioctl
:参数: vcpu绝对地址（输入）
:返回值: 成功返回0

此调用在虚拟CPU地址空间（对于用户控制的虚拟机）或虚拟机地址空间（对于常规虚拟机）创建一个页表项。这仅适用于次要故障，因此建议通过用户页表提前访问相关内存页。这对于处理用户控制虚拟机的有效性拦截很有用，可以在调用KVM_RUN ioctl之前将虚拟CPU的lowcore页面错误加载进来。
