SPDX 许可证标识符: GPL-2.0

=========================
MPIC 中断控制器
=========================

支持的设备类型：

  - KVM_DEV_TYPE_FSL_MPIC_20     Freescale MPIC v2.0
  - KVM_DEV_TYPE_FSL_MPIC_42     Freescale MPIC v4.2

只能实例化一个 MPIC 设备，无论其类型。创建的 MPIC 将作为系统中断控制器，连接到每个 vcpu 的中断输入。

组：
  KVM_DEV_MPIC_GRP_MISC
   属性：

    KVM_DEV_MPIC_BASE_ADDR（读写，64位）
      256 KiB MPIC 寄存器空间的基本地址。必须自然对齐。零值禁用映射。
重置值为零。
KVM_DEV_MPIC_GRP_REGISTER（读写，32位）
    以与从客户机访问相同的方式访问 MPIC 寄存器。
"attr" 是 MPIC 寄存器空间中的字节偏移量。访问必须是 4 字节对齐。
可以通过使用此属性组写入相关的 MSIIR 来发送 MSI。
KVM_DEV_MPIC_GRP_IRQ_ACTIVE（读写，32位）
    每个标准 openpic 源的 IRQ 输入线。0 表示非激活状态，1 表示激活状态，无论中断感觉如何。
对于边沿触发中断：写入 1 被认为是一个激活边沿，而写入 0 被忽略。读取返回 1 如果之前发出的边沿尚未被确认，否则返回 0。
"attr" 是 IRQ 编号。标准源的 IRQ 编号是从 EIVPR0 开始的相关 IVPR 的字节偏移量除以 32。

IRQ 路由：

  MPIC 仿真支持 IRQ 路由。只能实例化一个 MPIC 设备。一旦该设备被创建，它将可用作 irqchip id 0。
这个 irqchip 0 拥有 256 个中断引脚，这些引脚暴露了主中断源数组中的中断（即“SRC”中断）。
其编号与 MPIC 设备树绑定相同——基于从源数组起始位置的寄存器偏移量，而不考虑芯片文档中诸如“内部”或“外部”中断的任何细分。
非 SRC 中断的访问未通过中断路由机制实现。
