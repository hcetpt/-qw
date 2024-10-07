SPDX 许可证标识符: GPL-2.0

==========
嵌套 VMX
==========

概述
---------

在 Intel 处理器上，KVM 使用 Intel 的 VMX（虚拟机扩展）轻松高效地运行客户操作系统。通常情况下，这些客户操作系统本身*不能*作为运行自己客户的 Hypervisor，因为在 VMX 模式下，客户操作系统无法使用 VMX 指令。"嵌套 VMX"功能补充了这一缺失的能力——即运行使用 VMX 的客户 Hypervisor 及其自己的嵌套客户。它通过允许客户操作系统使用 VMX 指令，并利用硬件中可用的单层 VMX 正确且高效地模拟这些指令来实现。我们在 OSDI 2010 的论文《The Turtles Project: 设计与实现嵌套虚拟化》中详细描述了嵌套 VMX 特性的理论基础、实现及其性能特征，该论文可从以下网址获取：

	https://www.usenix.org/events/osdi10/tech/full_papers/Ben-Yehuda.pdf

术语
-----------

单层虚拟化有两个层级：主机（KVM）和客户操作系统。
在嵌套虚拟化中，我们有三个层级：主机（KVM），我们称之为 L0；客户 Hypervisor，我们称之为 L1；以及它的嵌套客户，我们称之为 L2。

运行嵌套 VMX
------------------

自 Linux 内核版本 4.20 起，默认启用了嵌套 VMX 功能。对于更早版本的 Linux 内核，可以通过给 kvm-intel 模块提供 "nested=1" 选项来启用此功能。
无需对用户空间（qemu）进行任何修改。然而，qemu 默认的仿真 CPU 类型（qemu64）不列出 "VMX" CPU 特性，因此必须显式启用，通过给 qemu 提供以下选项之一：

     - cpu host              （仿真的 CPU 具有真实 CPU 的所有特性）

     - cpu qemu64,+vmx       （向命名的 CPU 类型添加仅 vmx 特性）

ABIs
----

嵌套 VMX 致力于为客户提供一个标准且（最终）完全功能的 VMX 实现，以便客户 Hypervisor 使用。因此，它提供的 ABI 的官方规范是 Intel 的 VMX 规范，即他们的 "Intel 64 和 IA-32 架构软件开发者手册" 第 3B 卷。目前并非所有 VMX 功能都得到了完全支持，但目标是最终支持所有功能，首先从实际被流行的 Hypervisor（如 KVM 等）使用的 VMX 功能开始。
作为一个 VMX 实现，嵌套 VMX 向 L1 展示了一个 VMCS 结构。根据规范，除了 revision_id 和 abort 这两个字段外，该结构对其用户来说是*不透明*的，用户不应知道或关心其内部结构。相反，该结构是通过 VMREAD 和 VMWRITE 指令访问的。
尽管如此，出于调试目的，KVM 开发者可能仍希望了解该结构的内部细节；这是来自 arch/x86/kvm/vmx.c 的结构体 vmcs12。
"vmcs12" 名称指的是 L1 为 L2 构建的 VMCS。在代码中我们还有 "vmcs01"，即 L0 为 L1 构建的 VMCS，以及 "vmcs02"，即 L0 为实际运行 L2 构建的 VMCS——具体如何实现请参阅上述论文。
为了方便，我们在这里重复了 `struct vmcs12` 的内容。如果该结构体的内部发生变化，这可能会导致跨 KVM 版本的实时迁移失败。如果 `struct vmcs12` 或其内部的 `struct shadow_vmcs` 发生变化，应该更改 `VMCS12_REVISION`（来自 vmx.c）。

```c
typedef u64 natural_width;

struct __packed vmcs12 {
    /* 根据英特尔规范，一个 VMCS 区域必须以这两个用户可见字段开始 */
    u32 revision_id;
    u32 abort;

    u32 launch_state; /* VMCLEAR 时设置为 0，VMLAUNCH 时设置为 1 */
    u32 padding[7]; /* 用于将来扩展的空间 */

    u64 io_bitmap_a;
    u64 io_bitmap_b;
    u64 msr_bitmap;
    u64 vm_exit_msr_store_addr;
    u64 vm_exit_msr_load_addr;
    u64 vm_entry_msr_load_addr;
    u64 tsc_offset;
    u64 virtual_apic_page_addr;
    u64 apic_access_addr;
    u64 ept_pointer;
    u64 guest_physical_address;
    u64 vmcs_link_pointer;
    u64 guest_ia32_debugctl;
    u64 guest_ia32_pat;
    u64 guest_ia32_efer;
    u64 guest_pdptr0;
    u64 guest_pdptr1;
    u64 guest_pdptr2;
    u64 guest_pdptr3;
    u64 host_ia32_pat;
    u64 host_ia32_efer;
    u64 padding64[8]; /* 用于将来扩展的空间 */
    natural_width cr0_guest_host_mask;
    natural_width cr4_guest_host_mask;
    natural_width cr0_read_shadow;
    natural_width cr4_read_shadow;
    natural_width dead_space[4]; /* 最后残余的 cr3_target_value[0-3] */
    natural_width exit_qualification;
    natural_width guest_linear_address;
    natural_width guest_cr0;
    natural_width guest_cr3;
    natural_width guest_cr4;
    natural_width guest_es_base;
    natural_width guest_cs_base;
    natural_width guest_ss_base;
    natural_width guest_ds_base;
    natural_width guest_fs_base;
    natural_width guest_gs_base;
    natural_width guest_ldtr_base;
    natural_width guest_tr_base;
    natural_width guest_gdtr_base;
    natural_width guest_idtr_base;
    natural_width guest_dr7;
    natural_width guest_rsp;
    natural_width guest_rip;
    natural_width guest_rflags;
    natural_width guest_pending_dbg_exceptions;
    natural_width guest_sysenter_esp;
    natural_width guest_sysenter_eip;
    natural_width host_cr0;
    natural_width host_cr3;
    natural_width host_cr4;
    natural_width host_fs_base;
    natural_width host_gs_base;
    natural_width host_tr_base;
    natural_width host_gdtr_base;
    natural_width host_idtr_base;
    natural_width host_ia32_sysenter_esp;
    natural_width host_ia32_sysenter_eip;
    natural_width host_rsp;
    natural_width host_rip;
    natural_width paddingl[8]; /* 用于将来扩展的空间 */
    u32 pin_based_vm_exec_control;
    u32 cpu_based_vm_exec_control;
    u32 exception_bitmap;
    u32 page_fault_error_code_mask;
    u32 page_fault_error_code_match;
    u32 cr3_target_count;
    u32 vm_exit_controls;
    u32 vm_exit_msr_store_count;
    u32 vm_exit_msr_load_count;
    u32 vm_entry_controls;
    u32 vm_entry_msr_load_count;
    u32 vm_entry_intr_info_field;
    u32 vm_entry_exception_error_code;
    u32 vm_entry_instruction_len;
    u32 tpr_threshold;
    u32 secondary_vm_exec_control;
    u32 vm_instruction_error;
    u32 vm_exit_reason;
    u32 vm_exit_intr_info;
    u32 vm_exit_intr_error_code;
    u32 idt_vectoring_info_field;
    u32 idt_vectoring_error_code;
    u32 vm_exit_instruction_len;
    u32 vmx_instruction_info;
    u32 guest_es_limit;
    u32 guest_cs_limit;
    u32 guest_ss_limit;
    u32 guest_ds_limit;
    u32 guest_fs_limit;
    u32 guest_gs_limit;
    u32 guest_ldtr_limit;
    u32 guest_tr_limit;
    u32 guest_gdtr_limit;
    u32 guest_idtr_limit;
    u32 guest_es_ar_bytes;
    u32 guest_cs_ar_bytes;
    u32 guest_ss_ar_bytes;
    u32 guest_ds_ar_bytes;
    u32 guest_fs_ar_bytes;
    u32 guest_gs_ar_bytes;
    u32 guest_ldtr_ar_bytes;
    u32 guest_tr_ar_bytes;
    u32 guest_interruptibility_info;
    u32 guest_activity_state;
    u32 guest_sysenter_cs;
    u32 host_ia32_sysenter_cs;
    u32 padding32[8]; /* 用于将来扩展的空间 */
    u16 virtual_processor_id;
    u16 guest_es_selector;
    u16 guest_cs_selector;
    u16 guest_ss_selector;
    u16 guest_ds_selector;
    u16 guest_fs_selector;
    u16 guest_gs_selector;
    u16 guest_ldtr_selector;
    u16 guest_tr_selector;
    u16 host_es_selector;
    u16 host_cs_selector;
    u16 host_ss_selector;
    u16 host_ds_selector;
    u16 host_fs_selector;
    u16 host_gs_selector;
    u16 host_tr_selector;
};
```

作者
----

这些补丁由以下人员编写：
- Abel Gordon, abelg <at> il.ibm.com
- Nadav Har'El, nyh <at> il.ibm.com
- Orit Wasserman, oritw <at> il.ibm.com
- Ben-Ami Yassor, benami <at> il.ibm.com
- Muli Ben-Yehuda, muli <at> il.ibm.com

贡献者包括：
- Anthony Liguori, aliguori <at> us.ibm.com
- Mike Day, mdday <at> us.ibm.com
- Michael Factor, factor <at> il.ibm.com
- Zvi Dubitzky, dubi <at> il.ibm.com

并得到了以下人员宝贵的评审：
- Avi Kivity, avi <at> redhat.com
- Gleb Natapov, gleb <at> redhat.com
- Marcelo Tosatti, mtosatti <at> redhat.com
- Kevin Tian, kevin.tian <at> intel.com
- 及其他人员
```
