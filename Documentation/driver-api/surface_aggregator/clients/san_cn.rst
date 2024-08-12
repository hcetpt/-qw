下面是提供的英文文档的中文翻译：

SPDX-许可证标识符: GPL-2.0+

.. |san_client_link| replace:: :c:func:`san_client_link`
.. |san_dgpu_notifier_register| replace:: :c:func:`san_dgpu_notifier_register`
.. |san_dgpu_notifier_unregister| replace:: :c:func:`san_dgpu_notifier_unregister`

===================
Surface ACPI 通知
===================

Surface ACPI 通知（SAN）设备提供了ACPI与SAM控制器之间的桥梁。具体来说，ACPI代码可以通过该接口执行请求和处理电池及热事件。除此之外，还可以通过ACPI代码发送与Surface Book 2的独立显卡（dGPU）相关的事件（注：Surface Book 3使用了不同的方法）。目前所知唯一通过此接口发送的事件是dGPU开启的通知。虽然本驱动程序内部处理了前者，但对于dGPU事件，它仅通过其公共API转发给任何感兴趣的其他驱动程序，并不直接处理这些事件。

该驱动程序的公共接口分为两部分：客户端注册和通知器块注册。
可以通过 |san_client_link| 将SAN接口的客户端链接为SAN设备的消费者。这可以确保接收dGPU事件的客户端不会因为SAN接口尚未设置好而错过任何事件，因为它强制客户端驱动程序在SAN驱动程序卸载时解除绑定。
任何设备只要模块加载中，无论是否作为客户端链接，都可以注册通知器块。注册是通过 |san_dgpu_notifier_register| 完成的。如果不再需要通知器，则应通过 |san_dgpu_notifier_unregister| 进行注销。

有关更多详细信息，请参阅下面的API文档。
API 文档
=================

.. kernel-doc:: include/linux/surface_acpi_notify.h

.. kernel-doc:: drivers/platform/surface/surface_acpi_notify.c
    :export:
