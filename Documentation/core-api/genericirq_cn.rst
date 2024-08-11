包含:: <isonum.txt>

==========================
Linux 通用中断处理
==========================

:版权所有: |copy| 2005-2010: Thomas Gleixner
:版权所有: |copy| 2005-2006: Ingo Molnar

简介
============

通用中断处理层旨在为设备驱动程序提供完整的中断处理抽象。它可以处理所有不同类型的中断控制器硬件。设备驱动程序使用通用API函数来请求、启用、禁用和释放中断。驱动程序不必了解任何关于中断硬件的细节，因此它们可以在不同的平台上使用而无需更改代码。
此文档是为那些希望为其架构实现基于通用中断处理层的中断子系统的开发者提供的。

理由
=========

Linux中原始的中断处理实现使用了__do_IRQ()超级处理器，它能够应对各种类型的中断逻辑。
最初，Russell King确定了几种处理器以构建用于Linux 2.5/2.6中ARM中断处理器实现的一套相当通用的集合。他区分了：

- 级别类型

- 边沿类型

- 简单类型

在实现过程中，我们还确定了另一种类型：

- 快速EOI类型

在多处理器世界中，__do_IRQ()超级处理器还确定了另一种类型：

- 每CPU类型

这种高级中断处理器的拆分实现使我们可以针对每种特定的中断类型优化中断处理流程。这减少了该特定代码路径的复杂性，并允许优化特定类型的处理。
最初的通用中断实现使用了hw_interrupt_type结构及其`->ack`, `->end`等回调来区分超级处理器中的流程控制。这导致了流程逻辑与低级硬件逻辑的混合，同时也导致了不必要的代码重复：例如，在i386上，有一个`ioapic_level_irq`和一个`ioapic_edge_irq`中断类型，它们共享许多低级细节但具有不同的流程处理方式。
更自然的抽象是将“中断流程”和“芯片细节”干净地分离。
分析几个架构的中断子系统实现后发现，其中大多数可以使用一组通用的“中断流程”方法，并且只需要添加芯片级别的特定代码。这种分离对于需要在中断流程本身中有特定特性的(次)架构也非常有价值，而这些特性并不在芯片细节中——从而提供了一个更透明的中断子系统设计。
每个中断描述符都被分配了自己的高级流程处理器，这通常是通用实现之一。（这种高级流程处理器的实现也使得提供可以在各种架构上的嵌入式平台中找到的解复用处理器变得简单。）

这种分离使通用中断处理层更加灵活和可扩展。例如，一个(次)架构可以为“级别类型”中断使用通用的中断流程实现，并添加一个(次)架构特定的“边沿类型”实现。
为了使过渡到新模型更容易并防止现有实现的破坏，仍然提供了__do_IRQ()超级处理器。这导致了一种暂时的双重性。随着时间的推移，新模型应该在越来越多的架构中被使用，因为它使得更小和更清洁的中断子系统成为可能。现在它已经被废弃了三年，并即将被移除。

已知的错误和假设
==========================

没有已知的错误（敲木头）
抽象层
======

中断代码中有三个主要的抽象层次：

1. 高级驱动程序API

2. 高级IRQ流程处理程序

3. 芯片级别的硬件封装

中断控制流
-----------

每个中断都由一个中断描述符结构`irq_desc`来描述。中断通过一个`unsigned int`数值引用，该数值在描述符结构数组中选择对应的中断描述符结构。描述符结构包含状态信息以及指向分配给此中断的中断流程方法和中断芯片结构的指针。每当发生中断时，低级架构代码通过调用`desc->handle_irq()`进入通用中断代码。这个高级IRQ处理函数仅使用由分配的芯片描述符结构引用的`desc->irq_data.chip`原语。
高级驱动程序API
------------------

高级驱动程序API包括以下功能：

- `request_irq()`

- `request_threaded_irq()`

- `free_irq()`

- `disable_irq()`

- `enable_irq()`

- `disable_irq_nosync()`（仅SMP）

- `synchronize_irq()`（仅SMP）

- `irq_set_irq_type()`

- `irq_set_irq_wake()`

- `irq_set_handler_data()`

- `irq_set_chip()`

- `irq_set_chip_data()`

请参阅自动生成的功能文档以获取详细信息。
高级IRQ流程处理程序
------------------------

通用层提供了一组预定义的IRQ流程方法：

- `handle_level_irq()`

- `handle_edge_irq()`

- `handle_fasteoi_irq()`

- `handle_simple_irq()`

- `handle_percpu_irq()`

- `handle_edge_eoi_irq()`

- `handle_bad_irq()`

这些中断流程处理程序（预定义或特定于架构）由架构在启动期间或设备初始化期间分配给特定的中断。

默认流程实现
~~~~~~~~~~~~~~~~~~~~~~~~~~

辅助函数
^^^^^^^^^^^^^^^^

辅助函数调用芯片原语，并被默认流程实现所使用。实现了以下辅助函数（简化摘录）：

```c
default_enable(struct irq_data *data)
{
    desc->irq_data.chip->irq_unmask(data);
}

default_disable(struct irq_data *data)
{
    if (!delay_disable(data))
        desc->irq_data.chip->irq_mask(data);
}

default_ack(struct irq_data *data)
{
    chip->irq_ack(data);
}

default_mask_ack(struct irq_data *data)
{
    if (chip->irq_mask_ack) {
        chip->irq_mask_ack(data);
    } else {
        chip->irq_mask(data);
        chip->irq_ack(data);
    }
}

noop(struct irq_data *data)
{
}
```

默认流程处理程序实现
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

默认Level IRQ流程处理程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`handle_level_irq`为电平触发中断提供了一个通用实现。实现了以下控制流（简化摘录）：

```c
desc->irq_data.chip->irq_mask_ack();
handle_irq_event(desc->action);
desc->irq_data.chip->irq_unmask();
```

默认快速EOI IRQ流程处理程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`handle_fasteoi_irq`为只需要在处理程序末尾进行EOI的中断提供了一个通用实现。实现了以下控制流（简化摘录）：

```c
handle_irq_event(desc->action);
desc->irq_data.chip->irq_eoi();
```

默认Edge IRQ流程处理程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`handle_edge_irq`为边沿触发中断提供了一个通用实现。实现了以下控制流（简化摘录）：

```c
if (desc->status & running) {
    desc->irq_data.chip->irq_mask_ack();
    desc->status |= pending | masked;
    return;
}
desc->irq_data.chip->irq_ack();
desc->status |= running;
do {
    if (desc->status & masked)
        desc->irq_data.chip->irq_unmask();
    desc->status &= ~pending;
    handle_irq_event(desc->action);
} while (desc->status & pending);
desc->status &= ~running;
```

默认简单IRQ流程处理程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`handle_simple_irq`为简单的中断提供了一个通用实现。
.. note:: 

   简单的流程处理程序不调用任何处理程序/芯片原语。
实现了以下控制流（简化摘录）：

```c
handle_irq_event(desc->action);
```

默认每CPU流程处理程序
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`handle_percpu_irq`为每个CPU中断提供了一个通用实现。
每CPU中断仅在SMP系统上可用，处理程序提供了一个无需锁定的简化版本。
以下是实现的控制流程（简化的摘录）：

    如果 (desc->irq_data.chip->irq_ack)
        desc->irq_data.chip->irq_ack();
    处理中断事件(desc->action);
    如果 (desc->irq_data.chip->irq_eoi)
        desc->irq_data.chip->irq_eoi();

结束中断（EOI）边缘中断流处理器
^^^^^^^^^^^^^^^^^^^^^^^^^

handle_edge_eoi_irq 提供了一个异常的边缘处理器实现，仅用于驯服 PowerPC/Cell 上严重损坏的中断控制器。
不良中断流处理器
^^^^^^^^^^^^^^^^^^^^

handle_bad_irq 用于处理那些没有真正处理器分配的意外中断。
怪癖和优化
~~~~~~~~~~~~~~~~~~~~~~~~

通用函数旨在用于“干净”的架构和芯片，这些架构和芯片没有特定平台的中断处理怪癖。如果某个架构需要在“流”级别实现怪癖，则可以通过覆盖高级中断流处理器来实现。
延迟中断禁用
~~~~~~~~~~~~~~~~~~~~~~~~~

此每中断可选功能由 Russell King 在 ARM 中断实现中引入，当调用 disable_irq() 时不会在硬件级别屏蔽中断。中断保持启用状态，并且在发生中断事件时在流处理器中进行屏蔽。这可以防止在硬件级别禁用中断时丢失边缘中断。当中断到达时，如果设置了 IRQ_DISABLED 标志，则在硬件级别屏蔽该中断并设置 IRQ_PENDING 位。当中断通过 enable_irq() 重新启用时，检查待处理位，如果设置，则通过硬件或软件重发机制重新发送中断。（如果你想使用延迟中断禁用功能并且你的硬件无法重新触发中断，则必须启用 CONFIG_HARDIRQS_SW_RESEND 配置项。）延迟中断禁用功能不可配置。
芯片级硬件封装
---------------------------------

类型为 :c:type:`irq_chip` 的芯片级硬件描述结构包含所有与芯片直接相关的函数，这些函数可用于中断流的实现：
- `irq_ack`

- `irq_mask_ack` - 可选，推荐用于性能提升

- `irq_mask`

- `irq_unmask`

- `irq_eoi` - 可选，对于 EOI 流处理器是必需的

- `irq_retrigger` - 可选

- `irq_set_type` - 可选

- `irq_set_wake` - 可选

这些基本操作严格按字面意思解释：ACK 就是 ACK，屏蔽就是屏蔽一个中断线等。中断流处理器需要使用这些低级别的基本功能单元。
__do_IRQ 入口点
====================

原始实现 __do_IRQ() 是所有类型中断的替代入口点。它已不再存在。
该处理器后来被证明不适合所有类型的中断硬件，因此被重构以支持边缘/电平/简单/每CPU中断的功能分离。这不仅是功能上的优化，也缩短了中断的代码路径。
SMP 系统中的锁定
==============

芯片寄存器的锁定取决于定义芯片原语的架构。每个中断结构通过 desc->lock 进行保护，由通用层实现。
通用中断芯片
======================

为了避免重复实现相同IRQ芯片的副本，内核提供了一个可配置的通用中断芯片实现。开发者在以略有不同的方式实现相同功能之前，应该仔细检查通用芯片是否符合他们的需求。
.. kernel-doc:: kernel/irq/generic-chip.c
   :export:

结构体
==========

本章节包含通用IRQ层中使用的结构体自动生成的文档。
.. kernel-doc:: include/linux/irq.h
   :internal:

.. kernel-doc:: include/linux/interrupt.h
   :internal:

提供的公共函数
=========================

本章节包含内核API中导出的函数自动生成的文档。
.. kernel-doc:: kernel/irq/manage.c

.. kernel-doc:: kernel/irq/chip.c
   :export:

提供的内部函数
===========================

本章节包含内部函数自动生成的文档。
.. kernel-doc:: kernel/irq/irqdesc.c

.. kernel-doc:: kernel/irq/handle.c

.. kernel-doc:: kernel/irq/chip.c
   :internal:

致谢
=======

以下人员为此文档做出了贡献：

1. Thomas Gleixner tglx@linutronix.de

2. Ingo Molnar mingo@elte.hu
