SPDX 许可证标识符: GPL-2.0

===============
引导中断
===============

:作者: - Sean V Kelley <sean.v.kelley@linux.intel.com>

概述
========

在 PCI Express 中，中断表示为 MSI 或入站中断消息（Assert_INTx/Deassert_INTx）。给定的 Core IO 中集成的 IO-APIC 将 PCI Express 的传统中断消息转换为 MSI 中断。如果 IO-APIC 被禁用（通过 IO-APIC 表项中的掩码位），则消息将被路由到传统的 PCH。这种带内中断机制在过去对于不支持 IO-APIC 的系统和引导是必要的。Intel 过去曾使用“引导中断”这一术语来描述这种机制。此外，PCI Express 协议描述了带内的传统线中断 INTx 机制，用于 I/O 设备发出 PCI 风格的电平中断。接下来的段落描述了 Core IO 处理 INTx 消息路由到 PCH 时的问题以及在 BIOS 和操作系统中的缓解措施。

问题
=====

当带内的传统 INTx 消息转发到 PCH 时，它们会触发一个新的中断，而这个中断很可能没有相应的处理程序。当中断长时间未被处理时，Linux 内核将其跟踪为虚假中断（Spurious Interrupts）。当达到特定次数后，Linux 内核将禁用该 IRQ，并显示错误信息“nobody cared”。这个被禁用的 IRQ 现在阻止了一个可能共享 IRQ 线的有效中断的正常使用：

```
irq 19: nobody cared (尝试使用 "irqpoll" 选项启动)
CPU: 0 PID: 2988 Comm: irq/34-nipalk Tainted: 4.14.87-rt49-02410-g4a640ec-dirty #1
硬件名称: National Instruments NI PXIe-8880/NI PXIe-8880, BIOS 2.1.5f1 01/09/2020
调用追踪:

<IRQ>
 ? dump_stack+0x46/0x5e
 ? __report_bad_irq+0x2e/0xb0
 ? note_interrupt+0x242/0x290
 ? nNIKAL100_memoryRead16+0x8/0x10 [nikal]
 ? handle_irq_event_percpu+0x55/0x70
 ? handle_irq_event+0x4f/0x80
 ? handle_fasteoi_irq+0x81/0x180
 ? handle_irq+0x1c/0x30
 ? do_IRQ+0x41/0xd0
 ? common_interrupt+0x84/0x84
</IRQ>

处理程序:
irq_default_primary_handler threaded usb_hcd_irq
禁用 IRQ #19
```

条件
======

使用线程化中断是最有可能触发此问题的情况。线程化中断可能在 IRQ 处理程序唤醒后无法重新启用。这些“一次性”的情况意味着线程化中断需要保持中断线被屏蔽直到线程化处理程序运行完毕。特别是在处理高数据速率中断时，线程需要运行到完成；否则一些处理程序会因为发出设备的中断仍然活跃而导致栈溢出。

受影响的芯片组
=================

目前存在多种设备中存在传统的中断转发机制，包括但不限于 AMD/ATI、Broadcom 和 Intel 的芯片组。通过下面的缓解措施对驱动程序 `drivers/pci/quirks.c` 进行了修改。

从 ICX 开始，Core IO 的设备中不再有 IO-APIC。IO-APIC 只存在于 PCH 中。连接到 Core IO 的 PCIe 根端口的设备将使用原生 MSI/MSI-X 机制。

缓解措施
===========

缓解措施采取的形式是 PCI 特殊处理（quirks）。首先识别并利用一种方法来禁用到 PCH 的路由。在这种情况下，可以添加一个禁用引导中断生成的特殊处理。[1]_

Intel® 6300ESB I/O 控制器集线器
  替代基址寄存器：
   BIE: 引导中断使能

	  ==  ===========================
	  0   启动中断已启用
1   启动中断已禁用
==  ===========================

Intel® Sandy Bridge 至 Skylake 基于 Xeon 的服务器：
  一致性接口协议中断控制
   dis_intx_route2pch/dis_intx_route2ich/dis_intx_route2dmi2:
	  当此位被设置时，从 Intel® Quick Data DMA/PCI Express 端口接收到的本地 INTx 消息不会被路由到传统的 PCH —— 它们要么通过集成的 IO-APIC 转换为 MSI（如果 IO-APIC 掩码位在相应表项中未设置）
	  要么不会导致进一步的动作（当掩码位置位时）

如果没有直接禁用路由的方法，另一种方法是利用 PCI 中断引脚到 INTx 路由表来重定向中断处理程序到重路由的中断线。因此，在不能禁用 INTx 路由的芯片组上，Linux 内核将有效中断重路由到其传统中断。这种处理程序重定向将防止因过多未处理计数而导致的虚假中断检测，从而禁用 IRQ 线。[2]_

配置选项 `X86_REROUTE_FOR_BROKEN_BOOT_IRQS` 存在以启用（或禁用）将中断处理程序重路由到 PCH 中断线。该选项可以通过 `pci=ioapicreroute` 或 `pci=noioapicreroute` 覆盖。[3]_

更多文档
==================

在多个数据手册中有关于传统中断处理的概述（如 6300ESB 和 6700PXH 下面所示）。虽然大体相同，但它提供了了解其处理方式随芯片组演化的洞察。
禁用引导中断的示例
------------------------------------------

      - Intel® 6300ESB I/O 控制器集线器（文档编号 300641-004US）
	5.7.3 启动中断
	https://www.intel.com/content/dam/doc/datasheet/6300esb-io-controller-hub-datasheet.pdf

      - Intel® Xeon® 处理器 E5-1600/2400/2600/4600 v3 产品系列
	数据手册 - 第二卷：寄存器（文档编号 330784-003）
	6.6.41 cipintrc 一致性接口协议中断控制
	https://www.intel.com/content/dam/www/public/us/en/documents/datasheets/xeon-e5-v3-datasheet-vol-2.pdf

处理程序重定向示例
----------------------------

      - Intel® 6700PXH 64 位 PCI 枢纽（文档编号 302628）
	2.15.2 PCI Express 传统 INTx 支持和引导中断
	https://www.intel.com/content/dam/doc/datasheet/6700pxh-64-bit-pci-hub-datasheet.pdf

如果您有任何关于传统 PCI 中断的问题，请发邮件给我。
致谢，
    Sean V Kelley
    sean.v.kelley@linux.intel.com

.. [1] https://lore.kernel.org/r/12131949181903-git-send-email-sassmann@suse.de/
.. [2] https://lore.kernel.org/r/12131949182094-git-send-email-sassmann@suse.de/
.. [3] https://lore.kernel.org/r/487C8EA7.6020205@suse.de/
