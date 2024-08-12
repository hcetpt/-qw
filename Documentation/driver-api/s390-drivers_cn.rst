编写 s390 通道设备驱动程序
=============================

:作者: Cornelia Huck

简介
====

本文档描述了用于驱动基于 s390 的通道连接 I/O 设备的驱动程序可用的接口。这包括与硬件交互的接口以及与通用驱动核心交互的接口。这些接口由 s390 通用 I/O 层提供。
本文档假设读者熟悉与 s390 通道 I/O 架构相关的技术术语。关于该架构的描述，请参阅“z/Architecture: Principles of Operation”（IBM 出版号 SA22-7832）。
尽管 s390 系统上的大多数 I/O 设备通常通过此处所述的通道 I/O 机制进行驱动，但还有其他各种方法（如 diag 接口）。这些不在本文档讨论范围内。
s390 通用 I/O 层还为一些不严格视为 I/O 设备的设备提供了访问途径。虽然它们不是本文档的重点，但也会在此提及。
更多相关信息可以在内核源码的 `Documentation/arch/s390/driver-model.rst` 中找到。
css 总线
========

css 总线上包含了系统上可用的子通道。它们可以分为几类：

* 标准 I/O 子通道，供系统使用。它们在 ccw 总线上有子设备，并将在下文描述。
* 绑定到 vfio-ccw 驱动的 I/O 子通道。请参阅 `Documentation/arch/s390/vfio-ccw.rst`。
* 消息子通道。目前没有相应的 Linux 驱动程序。
* CHSC 子通道（最多一个）。可以使用 chsc 子通道驱动来发送异步的 chsc 命令。
* eADM 子通道。用于与存储级内存通信。
ccw总线
==========

ccw总线通常包含大多数可用的s390系统的设备。以其基本命令结构——通道命令字（ccw）命名，该结构用于寻址其上的设备，ccw总线上包含了所谓的通道连接设备。这些设备通过I/O子通道进行寻址，在css总线上可见。然而，对于通道连接设备的设备驱动程序永远不会直接与子通道交互，而是仅通过ccw总线上的I/O设备，即ccw设备进行交互。

通道连接设备的I/O函数
------------------------------------------

一些硬件结构已被转换为C结构，供通用I/O层和设备驱动程序使用。有关此处表示的硬件结构的更多信息，请参阅《操作原理》。
.. kernel-doc:: arch/s390/include/asm/cio.h
   :internal:

ccw设备
-----------

想要发起通道I/O的设备需要连接到ccw总线。与驱动核心的交互是通过通用I/O层完成的，该层提供了ccw设备和ccw设备驱动程序的抽象。所有启动或终止通道I/O的功能都作用于一个ccw设备结构上。设备驱动程序必须不要绕过这些功能，否则可能会产生奇怪的副作用。
.. kernel-doc:: arch/s390/include/asm/ccwdev.h
   :internal:

.. kernel-doc:: drivers/s390/cio/device.c
   :export:

.. kernel-doc:: drivers/s390/cio/device_ops.c
   :export:

通道测量设施
--------------------------------

通道测量设施提供了一种收集由通道子系统为每个通道连接设备提供的测量数据的方式。
.. kernel-doc:: arch/s390/include/uapi/asm/cmb.h
   :internal:

.. kernel-doc:: drivers/s390/cio/cmf.c
   :export:

ccwgroup总线
================

ccwgroup总线只包含由用户创建的人工设备。
许多网络设备（如qeth）实际上是由几个ccw设备组成的（例如读取、写入和数据通道对于qeth）。ccwgroup总线提供了一种机制来创建一个元设备，其中包含这些ccw设备作为从属设备，并且可以与netdevice关联。
ccw组设备
-----------------

.. kernel-doc:: arch/s390/include/asm/ccwgroup.h
   :internal:

.. kernel-doc:: drivers/s390/cio/ccwgroup.c
   :export:

通用接口
==================

以下部分包含的接口不仅被处理ccw设备的驱动程序使用，也被其他各种s390硬件的驱动程序使用。
适配器中断
------------------

通用I/O层提供了处理适配器中断和中断向量的帮助函数。
翻译成中文：
.. kernel-doc:: 驱动/s390/cio/airq.c
   :导出: 

这是一个类似文档配置的语句，用于指定要文档化的内核代码文件。具体含义为：“使用kernel-doc工具处理位于`驱动/s390/cio/airq.c`的代码文件，并导出其文档。”
