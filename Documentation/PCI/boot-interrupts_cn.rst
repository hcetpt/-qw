### SPDX 许可标识符: GPL-2.0

=================
启动中断
=================

**作者:** Sean V Kelley <sean.v.kelley@linux.intel.com>

概述
====

在 PCI Express 中，中断通常通过 MSI 或入站中断消息（Assert_INTx/Deassert_INTx）表示。给定的核心 I/O 中集成的 IO-APIC 将 PCI Express 的传统中断消息转换为 MSI 中断。如果 IO-APIC 被禁用（通过 IO-APIC 表项中的掩码位），这些消息将被路由到传统 PCH。这种带内中断机制传统上对于不支持 IO-APIC 的系统和启动是必要的。过去，Intel 使用术语“启动中断”来描述这种机制。此外，PCI Express 协议描述了这种带内的传统线中断 INTx 机制，用于 I/O 设备发出 PCI 风格的电平触发中断。以下段落描述了与核心 I/O 处理 INTx 消息路由到 PCH 相关的问题以及在 BIOS 和操作系统中的缓解措施。

问题
====

当带内传统 INTx 消息被转发到 PCH 时，它们会触发一个新的中断，而操作系统可能缺乏处理这个中断的方法。当中断长时间未被处理时，Linux 内核将其追踪为“错误中断”。当达到特定计数时，Linux 内核会禁用 IRQ，并报告“nobody cared”的错误。这个被禁用的 IRQ 现在阻止了一个现有的、可能共享同一 IRQ 线的中断的正常工作：

```
irq 19: nobody cared (尝试使用 "irqpoll" 选项启动)
CPU: 0 PID: 2988 Comm: irq/34-nipalk Tainted: 4.14.87-rt49-02410-g4a640ec-dirty #1
硬件名称: National Instruments NI PXIe-8880/NI PXIe-8880, BIOS 2.1.5f1 01/09/2020
调用跟踪:

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

处理器:
irq_default_primary_handler threaded usb_hcd_irq
禁用 IRQ #19
```

条件
====

使用线程化中断是最有可能触发此问题的情况。线程化中断可能在 IRQ 处理器唤醒后不会重新启用。这些“一次性”情况意味着线程化中断需要保持中断线路屏蔽，直到线程化处理器运行完毕。特别是在处理高数据速率中断时，线程需要完全运行；否则一些处理器会因为发出设备的中断仍然处于激活状态而导致栈溢出。

受影响的芯片组
================

今天，许多设备中仍然存在传统的中断转发机制，包括但不限于来自 AMD/ATI、Broadcom 和 Intel 的芯片组。通过下面提到的缓解措施对 drivers/pci/quirks.c 进行了修改。

从 ICX 开始，核心 I/O 的设备中不再有任何 IO-APIC。IO-APIC 只存在于 PCH 中。连接到核心 I/O 的 PCIe 根端口的设备将使用原生 MSI/MSI-X 机制。

缓解措施
===========

缓解措施采取的形式是 PCI 特殊处理。首选的做法是首先识别并利用一种方法来禁用路由到 PCH，在这种情况下，可以添加一个特殊处理来禁用启动中断生成。[1]_

Intel® 6300ESB I/O 控制器集线器
  替代基址寄存器：
   BIE: 启动中断使能

	  ==  ===========================
	  0   启动中断被启用
1   启动中断被禁用
==  ===========================

Intel® Sandy Bridge 到 Skylake 基于 Xeon 的服务器:
  协同接口协议中断控制
   dis_intx_route2pch/dis_intx_route2ich/dis_intx_route2dmi2:
	  当这一位被设置时，从 Intel® 快速数据 DMA/PCI Express 端口收到的本地 INTx 消息不会被路由到传统 PCH — 它们要么通过集成 IO-APIC 转换为 MSI（如果相应条目的 IO-APIC 掩码位被清除）
	  要么不采取进一步的动作（当掩码位被设置）

如果没有直接禁用路由的方法，另一种做法是利用 PCI 中断引脚到 INTx 路由表将中断处理器默认重定向到重路由的中断线上。因此，在不能禁用这种 INTx 路由的芯片组上，Linux 内核将把有效的中断重路由到其传统中断。这种处理器的重定向将防止由于过多未处理计数导致的错误中断检测，通常会导致 IRQ 线被禁用。[2]_

配置选项 X86_REROUTE_FOR_BROKEN_BOOT_IRQS 存在以启用（或禁用）将中断处理器重定向到 PCH 中断线的功能。该选项可以通过 pci=ioapicreroute 或 pci=noioapicreroute 覆盖。[3]_

更多文档
==================

有几个数据手册概述了传统中断处理（如下所示的 6300ESB 和 6700PXH）。虽然大部分相同，但它提供了对芯片组处理演进的洞察。
禁用启动中断的例子
------------------------------------------

      - Intel® 6300ESB I/O 控制器集线器 (文档编号 300641-004US)
	5.7.3 启动中断
	https://www.intel.com/content/dam/doc/datasheet/6300esb-io-controller-hub-datasheet.pdf

      - Intel® Xeon® 处理器 E5-1600/2400/2600/4600 v3 产品系列
	数据手册 - 第二卷：寄存器 (文档编号 330784-003)
	6.6.41 cipintrc 协同接口协议中断控制
	https://www.intel.com/content/dam/www/public/us/en/documents/datasheets/xeon-e5-v3-datasheet-vol-2.pdf

处理器重定向的例子
----------------------------

      - Intel® 6700PXH 64 位 PCI 集线器 (文档编号 302628)
	2.15.2 PCI Express 传统 INTx 支持和启动中断
	https://www.intel.com/content/dam/doc/datasheet/6700pxh-64-bit-pci-hub-datasheet.pdf

如果您有关于传统 PCI 中断的疑问，请发送邮件给我。
祝好，
    Sean V Kelley
    sean.v.kelley@linux.intel.com

.. [1] https://lore.kernel.org/r/12131949181903-git-send-email-sassmann@suse.de/
.. [2] https://lore.kernel.org/r/12131949182094-git-send-email-sassmann@suse.de/
.. [3] https://lore.kernel.org/r/487C8EA7.6020205@suse.de/
