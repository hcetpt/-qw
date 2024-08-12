SPDX 许可证标识符: 仅 GPL-2.0

====================
重置控制器 API
====================

简介
============

重置控制器是控制多个外设重置信号的核心单元。重置控制器 API 被分为两个部分：消费者驱动接口（`消费者驱动接口 <#consumer-driver-interface>`__，`API 参考 <#reset-consumer-api>`__），允许外设驱动程序请求对其重置输入信号的控制；以及重置控制器驱动接口（`重置控制器驱动接口 <#reset-controller-driver-interface>`__，`API 参考 <#reset-controller-driver-api>`__），用于重置控制器设备的驱动程序注册其重置控制，以供消费者使用。

虽然某些重置控制器硬件单元也实现了系统重启功能，但重启处理程序不属于重置控制器 API 的范畴。

术语表
--------

重置控制器 API 使用以下术语，并赋予它们特定的意义：

重置线

    物理重置线，承载从重置控制器硬件单元到外围模块的重置信号。
重置控制

    确定一个或多个重置线状态的控制方法。最常见的是，在重置控制器寄存器空间中的一个比特位，它要么可以直接控制重置线的物理状态，要么可以自我清除并用于在重置线上触发预定的脉冲。在更复杂的重置控制中，单个触发动作可以启动对多个重置线进行精心计时的一系列脉冲。
重置控制器

    提供一系列重置控制来控制一系列重置线的硬件模块。
重置消费者

    通过重置线上的信号被置于重置状态的外围模块或外部 IC。

消费者驱动接口
=========================

此接口提供了一个与内核时钟框架类似的 API。
消费者驱动程序使用 get 和 put 操作来获取和释放复位控制。
提供了函数来激活和取消激活受控的复位线，触发复位脉冲，或者查询复位线的状态。
在请求复位控制时，消费者可以为其复位输入使用符号名称，这些名称由核心映射到现有复位控制器设备上的实际复位控制上。
当不使用复位控制器框架时，提供了一个此 API 的存根版本以尽量减少使用 `ifdef` 的需求。
共享和独占复位
--------------------------

复位控制器 API 提供了引用计数取消激活和激活或直接、独占控制。
共享和独占复位控制的区别是在请求复位控制时做出的，可以通过 `devm_reset_control_get_shared()` 或者 `devm_reset_control_get_exclusive()` 实现。
这个选择决定了与复位控制相关的 API 调用的行为。
共享复位的行为类似于内核时钟框架中的时钟。
它们提供引用计数取消激活，其中只有第一次取消激活（将取消激活的引用计数增加到一）和最后一次激活（将取消激活的引用计数减回到零）对复位线产生物理影响。
另一方面，独占复位保证了直接控制。
也就是说，一个断言（assert）会立即使复位线被激活，而取消断言（deassert）则会立即使复位线被取消激活。
#### 断言与取消断言

消费者驱动程序使用 `reset_control_assert()` 和 `reset_control_deassert()` 函数来激活和取消激活复位线。
对于共享的复位控制，对这两个函数的调用必须是平衡的。
需要注意的是，由于可能有多个消费者正在使用同一个共享复位控制，因此无法保证在共享复位控制上调用 `reset_control_assert()` 实际上会使复位线被激活。
使用共享复位控制的消费者驱动程序应该假设复位线可能会一直保持未激活状态。
API 只能保证只要有任何消费者请求复位线保持未激活状态，则该复位线就不能被激活。
#### 触发

消费者驱动程序使用 `reset_control_reset()` 来触发自取消断言复位控制上的复位脉冲。
通常，这些复位不能在多个消费者之间共享，因为任何消费者的驱动程序请求一个脉冲都会导致所有连接的外围设备复位。
复位控制器 API 允许将自取消断言复位控制作为共享请求，但只针对这些复位控制，第一个触发请求才会实际在复位线上发出脉冲。
所有后续对该函数的调用都没有效果，直到所有消费者都调用了 `reset_control_rearm()`。
对于共享复位控制，对这两个函数的调用必须保持平衡。
这允许仅在驱动程序被探测或恢复之前某个时刻需要初始复位的设备共享一个脉冲复位线。
查询
----

只有部分复位控制器支持通过 `reset_control_status()` 查询当前复位线的状态。
如果支持，当给定的复位线被激活时，该函数将返回一个正的非零值。
`reset_control_status()` 函数不接受 `复位控制数组` 作为其输入参数。
可选复位
--------

通常，外围设备在某些平台上需要复位线，在其他平台上则不需要。
为此，可以使用 `devm_reset_control_get_optional_exclusive()` 或 `devm_reset_control_get_optional_shared()` 将复位控制请求为可选。
当请求的复位控制未在设备树中指定时，这些函数将返回空指针而不是错误。
向复位控制函数传递空指针会导致它们静默返回而不会产生错误。
复位控制数组
--------------

一些驱动程序需要以任意顺序激活一组复位线。
`devm_reset_control_array_get()` 返回一个不透明的重置控制句柄，该句柄可用于一次性断言、取消断言或触发所有指定的重置控制。
重置控制API不保证其中各个控制项处理的顺序。
重置控制器驱动接口
===================

重置控制器模块的驱动程序提供了断言或取消断言重置信号、在重置线上触发重置脉冲或查询其当前状态所需的功能。
所有函数都是可选的。
初始化
-------

驱动程序在它们的探测函数中填充一个 `reset_controller_dev` 结构体，并使用 `reset_controller_register()` 进行注册。
实际功能通过 `reset_control_ops` 结构体中的回调函数实现。
API参考
=======

重置控制器API在这里分为两部分进行文档说明：`重置消费者API <#reset-consumer-api>`__ 和 `重置控制器驱动API <#reset-controller-driver-api>`__ 。
重置消费者API
---------------

重置消费者可以使用从 `devm_reset_control_get_exclusive()` 或 `devm_reset_control_get_shared()` 获取的不透明重置控制句柄来控制重置线。
给定重置控制后，消费者可以调用 `reset_control_assert()` 和 `reset_control_deassert()`，使用 `reset_control_reset()` 触发重置脉冲，或者使用 `reset_control_status()` 查询重置线的状态。
.. kernel-doc:: include/linux/reset.h
   :internal:

.. kernel-doc:: drivers/reset/core.c
   :functions: reset_control_reset
               reset_control_assert
               reset_control_deassert
               reset_control_status
               reset_control_acquire
               reset_control_release
               reset_control_rearm
               reset_control_put
               of_reset_control_get_count
               of_reset_control_array_get
               devm_reset_control_array_get
               reset_control_get_count

重置控制器驱动API
-------------------

重置控制器驱动应该在一个静态常量结构 `reset_control_ops` 中实现必要的函数，分配并填写一个 `reset_controller_dev` 结构体，并使用 `devm_reset_controller_register()` 进行注册。
翻译为中文：

.. kernel-doc:: include/linux/reset-controller.h
   :internal:

这段意味着：“在内核文档中包含对`include/linux/reset-controller.h`文件的说明。”

.. kernel-doc:: drivers/reset/core.c
   :functions: of_reset_simple_xlate
               reset_controller_register
               reset_controller_unregister
               devm_reset_controller_register
               reset_controller_add_lookup

这段意味着：“在内核文档中包含对`drivers/reset/core.c`文件中以下函数的说明：
- `of_reset_simple_xlate`
- `reset_controller_register`
- `reset_controller_unregister`
- `devm_reset_controller_register`
- `reset_controller_add_lookup`”
