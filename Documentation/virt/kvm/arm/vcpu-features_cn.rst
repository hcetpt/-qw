SPDX 许可证标识符: GPL-2.0

===============================
ARM64 架构上的 vCPU 特性选择
===============================

KVM/arm64 提供了两种机制，允许用户空间配置呈现给虚拟机的 CPU 特性。

KVM_ARM_VCPU_INIT
=================

``KVM_ARM_VCPU_INIT`` ioctl 接受一个特性标志位图（`struct kvm_vcpu_init::features`）。通过此接口启用的特性是*选择性加入*，可能会更改或扩展 UAPI。有关 ioctl 控制特性的完整文档，请参阅 :ref:`KVM_ARM_VCPU_INIT`。
否则，所有由 KVM 支持的 CPU 特性都由架构定义的 ID 寄存器描述。

ID 寄存器
=================

ARM 架构指定了一个范围的 *ID 寄存器*，用于描述 CPU 实现所支持的一组架构特性。KVM 将虚拟机的 ID 寄存器初始化为系统支持的最大 CPU 特性集。在 KVM 中，ID 寄存器值可能是 VM 范围内的，这意味着这些值可以为 VM 中的所有 vCPU 共享。
KVM 允许用户空间通过 `KVM_SET_ONE_REG` ioctl 向 ID 寄存器写入值来选择退出某些由 ID 寄存器描述的 CPU 特性。直到 VM 启动之前，即用户空间在 VM 中至少一个 vCPU 上调用了 `KVM_RUN` 之前，ID 寄存器都是可修改的。用户空间可以通过 `KVM_ARM_GET_REG_WRITABLE_MASKS` 来发现 ID 寄存器中哪些字段是可以修改的。
请参阅 :ref:`ioctl 文档 <KVM_ARM_GET_REG_WRITABLE_MASKS>` 获取更多详细信息。
根据架构在 DDI0487J.a D19.1.3 'ID 寄存器字段的 ID 方案原则' 所概述的规则，用户空间被允许*限制*或*屏蔽*CPU 特性。KVM 不允许超出系统能力的 ID 寄存器值。
.. warning::
   **强烈建议** 用户空间在访问 vCPU 的其余 CPU 寄存器状态之前修改 ID 寄存器值。KVM 可能会使用 ID 寄存器值来控制特性仿真。将 ID 寄存器修改与其他系统寄存器访问交织在一起可能导致不可预测的行为。
