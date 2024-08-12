将其翻译为中文如下：

.. SPDX-许可证标识符: GPL-2.0+ 

===============================
客户端驱动程序API文档
===============================

.. contents::
    :depth: 2


串行集线器通信
========================

.. kernel-doc:: include/linux/surface_aggregator/serial_hub.h

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_packet_layer.c
    :export:


控制器和核心接口
=============================

.. kernel-doc:: include/linux/surface_aggregator/controller.h

.. kernel-doc:: drivers/platform/surface/aggregator/controller.c
    :export:

.. kernel-doc:: drivers/platform/surface/aggregator/core.c
    :export:


客户端总线和客户端设备API
================================

.. kernel-doc:: include/linux/surface_aggregator/device.h

.. kernel-doc:: drivers/platform/surface/aggregator/bus.c
    :export:
