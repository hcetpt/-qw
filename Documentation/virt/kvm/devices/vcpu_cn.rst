```spdx
许可证标识符: GPL-2.0

======================
通用虚拟CPU接口
======================

虚拟CPU“设备”也支持ioctl命令KVM_SET_DEVICE_ATTR、KVM_GET_DEVICE_ATTR和KVM_HAS_DEVICE_ATTR。该接口使用与其他设备相同的`kvm_device_attr`结构，但针对的是整个虚拟CPU的设置和控制。每虚拟CPU的组和属性（如果有）是架构特定的。
1. 组: KVM_ARM_VCPU_PMU_V3_CTRL
==================================

:架构: ARM64

1.1. 属性: KVM_ARM_VCPU_PMU_V3_IRQ
---------------------------------------

:参数: 在`kvm_device_attr.addr`中，PMU溢出中断地址是一个指向int类型的指针

返回值:

	 =======  ========================================================
	 -EBUSY   PMU溢出中断已设置
	 -EFAULT  读取中断编号时出错
	 -ENXIO   不支持PMUv3或尝试获取未设置的溢出中断
	 -ENODEV  VCPU缺少KVM_ARM_VCPU_PMU_V3特性
	 -EINVAL  提供了无效的PMU溢出中断编号或尝试在没有使用内核irqchip的情况下设置IRQ编号
	 =======  ========================================================

描述此虚拟CPU的PMUv3（性能监控单元v3）溢出中断编号。此中断可以是PPI或SPI，但每个虚拟CPU的中断类型必须相同。作为PPI时，所有虚拟CPU的中断编号相同；作为SPI时，每个虚拟CPU需要单独的编号。
1.2 属性: KVM_ARM_VCPU_PMU_V3_INIT
---------------------------------------

:参数: `kvm_device_attr.addr`中无附加参数

返回值:

	 =======  ======================================================
	 -EEXIST  中断编号已被使用
	 -ENODEV  不支持PMUv3或GIC未初始化
	 -ENXIO   不支持PMUv3，缺少VCPU特性或中断编号未设置
	 -EBUSY   PMUv3已初始化
	 =======  ======================================================

请求初始化PMUv3。如果使用内核虚拟GIC实现，则必须在初始化内核irqchip之后执行此操作。
1.3 属性: KVM_ARM_VCPU_PMU_V3_FILTER
-----------------------------------------

:参数: 在`kvm_device_attr.addr`中，PMU事件过滤器地址是一个指向`kvm_pmu_event_filter`结构的指针

:返回值:

	 =======  ======================================================
	 -ENODEV  不支持PMUv3或GIC未初始化
	 -ENXIO   PMUv3配置不当或调用此属性前未正确配置内核irqchip
	 -EBUSY   PMUv3已初始化或虚拟CPU已运行
	 -EINVAL  过滤范围无效
	 =======  ======================================================

请求安装一个描述如下格式的PMU事件过滤器：

    struct kvm_pmu_event_filter {
	    __u16	base_event;
	    __u16	nevents;

    #define KVM_PMU_EVENT_ALLOW	0
    #define KVM_PMU_EVENT_DENY	1

	    __u8	action;
	    __u8	pad[3];
    };

过滤范围定义为[@base_event, @base_event + @nevents)，结合一个@action（KVM_PMU_EVENT_ALLOW或KVM_PMU_EVENT_DENY）。第一个注册的范围定义全局策略（如果第一个@action为DENY则为全局允许，如果第一个@action为ALLOW则为全局禁止）。可以编程多个范围，并且必须适合由PMU架构定义的事件空间（ARMv8.0为10位，ARMv8.1及以后版本为16位）。
注意：“取消”过滤器通过为同一范围注册相反的操作不会改变默认动作。例如，将事件范围[0:10)的ALLOW过滤器作为第一个过滤器安装，然后对同一范围应用DENY动作将使整个范围保持禁用状态。
限制：事件0（SW_INCR）从不被过滤，因为它不是硬件事件。过滤事件0x1E（CHAIN）也没有效果，因为严格来说它不是一个事件。可以使用事件0x11（CPU_CYCLES）来过滤周期计数器。
1.4 属性: KVM_ARM_VCPU_PMU_V3_SET_PMU
------------------------------------------

:参数: 在`kvm_device_attr.addr`中，表示PMU标识符的int类型的地址
:返回值:

	 =======  ====================================================
	 -EBUSY   PMUv3已初始化，虚拟CPU已运行或已设置了事件过滤器
	 -EFAULT  访问PMU标识符时出错
	 -ENXIO   未找到PMU
	 -ENODEV  不支持PMUv3或GIC未初始化
	 -ENOMEM  无法分配内存
	 =======  ====================================================

请求虚拟CPU在创建用于PMU仿真目的的客事件时使用指定的硬件PMU。PMU标识符可以从/sys/devices下的所需PMU实例的"type"文件中读取（或者等效地，/sys/bus/event_source）。此属性特别适用于具有至少两个CPU PMU的异构系统。为一个虚拟CPU设置的PMU将被所有其他虚拟CPU使用。如果已存在PMU事件过滤器，则无法设置PMU。
```

这段文本描述了与ARM架构虚拟化相关的KVM（Kernel-based Virtual Machine）中PMUv3（Performance Monitoring Unit version 3）相关的一系列属性及其功能和参数。
请注意，KVM不会尝试在与该属性指定的PMU相关的物理CPU上运行VCPU。这完全由用户空间控制。然而，在不受PMU支持的物理CPU上尝试运行VCPU将失败，并且KVM_RUN会返回`exit_reason = KVM_EXIT_FAIL_ENTRY`，通过设置`fail_entry`结构中的`hardware_entry_failure_reason`字段为`KVM_EXIT_FAIL_ENTRY_CPU_UNSUPPORTED`以及`cpu`字段为处理器ID。

2. 组：KVM_ARM_VCPU_TIMER_CTRL
==============================

:架构: ARM64

2.1 属性：KVM_ARM_VCPU_TIMER_IRQ_VTIMER, KVM_ARM_VCPU_TIMER_IRQ_PTIMER
-------------------------------------------------------------------

:参数: 在`kvm_device_attr.addr`中，计时器中断地址是一个指向int的指针

返回值：

	 =======  =================================
	 -EINVAL  无效的计时器中断号
	 -EBUSY   一个或多个VCPU已经运行
	 =======  =================================

当连接到内核虚拟GIC时，表示架构化计时器中断号。这些必须是PPI（16 <= intid < 32）。设置该属性会覆盖默认值（见下文）。
=============================  ==========================================
KVM_ARM_VCPU_TIMER_IRQ_VTIMER  EL1虚拟计时器中断号（默认：27）
KVM_ARM_VCPU_TIMER_IRQ_PTIMER  EL1物理计时器中断号（默认：30）
=============================  ==========================================

为不同的计时器设置相同的PPI将阻止VCPU运行。在创建所有VCPU并运行任何VCPU之前，用户空间应至少配置一个VCPU上的中断号。
.. _kvm_arm_vcpu_pvtime_ctrl:

3. 组：KVM_ARM_VCPU_PVTIME_CTRL
===============================

:架构: ARM64

3.1 属性：KVM_ARM_VCPU_PVTIME_IPA
-------------------------------

:参数: 64位基址

返回值：

	 =======  ======================================
	 -ENXIO   被窃时间未实现
	 -EEXIST  该VCPU的基址已设置
	 -EINVAL  基址不是64字节对齐
	 =======  ======================================

指定该VCPU的被窃时间结构的基址。基址必须是64字节对齐，并存在于有效的访客内存区域中。有关更多信息，包括被窃时间结构的布局，请参阅Documentation/virt/kvm/arm/pvtime.rst。

4. 组：KVM_VCPU_TSC_CTRL
========================

:架构: x86

4.1 属性：KVM_VCPU_TSC_OFFSET

:参数: 64位无符号TSC偏移量

返回值：

	 ======= ======================================
	 -EFAULT 读写提供的参数地址错误
	-ENXIO  不支持此属性
	 ======= ======================================

指定相对于主机TSC的访客TSC偏移量。访客TSC然后通过以下等式得出：

  guest_tsc = host_tsc + KVM_VCPU_TSC_OFFSET

此属性在实时迁移期间调整访客TSC非常有用，以便TSC可以计算VM暂停期间的时间。以下描述了一种可能的算法以供此目的使用：
从源VMM进程：

1. 调用KVM_GET_CLOCK ioctl记录主机TSC（tsc_src），kvmclock纳秒（guest_src），以及主机CLOCK_REALTIME纳秒（host_src）
2. 读取每个VCPU的KVM_VCPU_TSC_OFFSET属性以记录访客TSC偏移量（ofs_src[i]）
3. 调用KVM_GET_TSC_KHZ ioctl记录访客TSC的频率（freq）
从目标VMM进程执行如下步骤：

4. 调用KVM_SET_CLOCK ioctl，提供来自kvmclock（guest_src）和CLOCK_REALTIME（host_src）的源纳秒值，并将其分别填入各自的字段中。确保提供的结构中设置了KVM_CLOCK_REALTIME标志。
KVM将更新VM的kvmclock以计入自记录时钟值以来经过的时间。请注意，如果在源和目标之间没有同步CLOCK_REALTIME，或者从源暂停VM到目标执行步骤4-7之间的时间过长，这将在客机中引起问题（例如超时）。

5. 调用KVM_GET_CLOCK ioctl以记录主机TSC（tsc_dest）和kvmclock纳秒值（guest_dest）。

6. 调整每个vCPU的客机TSC偏移量以考虑到（1）自记录状态以来经过的时间，以及（2）源机器与目标机器之间的TSC差异：

   ofs_dst[i] = ofs_src[i] -
     (guest_src - guest_dest) * freq +
     (tsc_src - tsc_dest)

   （“ofs[i] + tsc - guest * freq”是对应于kvmclock时间为0的客机TSC值。上述公式确保该值在目标上与在源上相同）

7. 将每个vCPU的KVM_VCPU_TSC_OFFSET属性写入上一步骤中得出的相应值。
