SPDX 许可证标识符: GPL-2.0

=============================
TTY 驱动程序与 TTY 操作
=============================

.. contents:: 目录
   :local:

分配
======

驱动程序需要做的第一件事是分配一个 `struct tty_driver`。这可以通过 `tty_alloc_driver()`（或 `__tty_alloc_driver()`）来完成。接下来，新分配的结构体将被填充信息。请参阅本文档末尾的 `TTY Driver Reference`_ ，了解实际应当填写的内容。
分配例程期望得到驱动程序最多可以处理的设备数量和标志。标志是以 `TTY_DRIVER_` 开头的那些，在下面的 `TTY Driver Flags`_ 中列出并描述。
当驱动程序即将释放时，将调用 `tty_driver_kref_put()`。
它会递减引用计数，并且如果计数降至零，则释放驱动程序。
作为参考，这里详细解释了分配和释放函数：

.. kernel-doc:: drivers/tty/tty_io.c
   :identifiers: __tty_alloc_driver tty_driver_kref_put

TTY 驱动程序标志
-----------------

以下是 `tty_alloc_driver()`（或 `__tty_alloc_driver()`）接受的标志文档：

.. kernel-doc:: include/linux/tty_driver.h
   :doc: TTY Driver Flags

----

注册
======

当 `struct tty_driver` 分配并填写完毕后，可以使用 `tty_register_driver()` 进行注册。建议在 `tty_alloc_driver()` 的标志中传递 `TTY_DRIVER_DYNAMIC_DEV`。如果没有传递该标志，则 *所有* 设备也会在 `tty_register_driver()` 期间注册，并且可以跳过以下关于注册设备的部分。然而，`Registering Devices`_ 中关于 `struct tty_port` 的部分仍然适用。
.. kernel-doc:: drivers/tty/tty_io.c
   :identifiers: tty_register_driver tty_unregister_driver

注册设备
--------------

每个 TTY 设备都应由 `struct tty_port` 支持。通常，TTY 驱动程序将 `tty_port` 嵌入到设备的私有结构中。有关处理 `tty_port` 的更多细节可以在 :doc:`tty_port` 中找到。驱动程序还建议使用 `tty_port` 的引用计数功能 `tty_port_get()` 和 `tty_port_put()`。最后的 put 应该释放 `tty_port` 及其包含的设备私有结构。
除非 `TTY_DRIVER_DYNAMIC_DEV` 作为标志传递给 `tty_alloc_driver()`，否则 TTY 驱动程序应该注册系统中发现的每个设备（后者更优选）。这通过 `tty_register_device()` 完成。或者如果驱动程序想要通过 `struct attribute_group` 暴露一些信息，则使用 `tty_register_device_attr()`。它们都会注册第 `index` 个设备，并且返回后，设备就可以打开。稍后的 `Linking Devices to Ports`_ 中描述了首选的 `tty_port` 变体。由驱动程序管理空闲索引并选择正确的索引。TTY 层只拒绝注册超过传递给 `tty_alloc_driver()` 的设备数量。
当设备打开时，TTY 层分配 `struct tty_struct` 并开始调用来自 `:c:member:'tty_driver.ops'` 的操作，详情见 `TTY Operations Reference`_。
注册例程如下文所述：

.. kernel-doc:: drivers/tty/tty_io.c
   :identifiers: tty_register_device tty_register_device_attr tty_unregister_device

----

连接设备与端口
---------------------
如前所述，每个 TTY 设备都应分配一个 `struct tty_port`。最晚应在 `:c:member:'tty_driver.ops.install()'` 时让 TTY 层知道这一点。有几个辅助函数用于 *连接* 这两者。理想情况下，驱动程序在注册时使用 `tty_port_register_device()` 或 `tty_port_register_device_attr()` 而不是 `tty_register_device()` 和 `tty_register_device_attr()`。
这样，驱动程序不必关心之后的连接问题。
如果无法直接关联，驱动程序仍然可以在通过 `tty_port_link_device()` 实际注册之前，将 `tty_port` 关联到特定的索引上。如果这种方式仍不适合，作为最后的选择，可以从 `tty_driver.ops.install` 钩子中使用 `tty_port_install()`。最后这种方式主要用于内存中的设备，如 PTY，其中 `tty_ports` 是按需分配的。

关联函数的文档在这里：

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_link_device tty_port_register_device
        tty_port_register_device_attr

----

TTY 驱动参考
============

`struct tty_driver` 中的所有成员都在这里进行了文档说明。必需的成员在末尾注明。`struct tty_operations` 的文档紧随其后。
.. kernel-doc:: include/linux/tty_driver.h
   :identifiers: tty_driver

----

TTY 操作参考
=============

当一个 TTY 被注册时，TTY 层可以调用这些驱动钩子：

.. kernel-doc:: include/linux/tty_driver.h
   :identifiers: tty_operations
