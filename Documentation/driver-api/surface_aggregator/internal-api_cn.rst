	SPDX许可标识符: GPL-2.0+

==========================
内部API文档
==========================

.. contents::
    :depth: 2


数据包传输层
======================

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_parser.h
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_parser.c
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_msgb.h
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_packet_layer.h
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_packet_layer.c
    :internal:


请求传输层
=======================

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_request_layer.h
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/ssh_request_layer.c
    :internal:


控制器
==========

.. kernel-doc:: drivers/platform/surface/aggregator/controller.h
    :internal:

.. kernel-doc:: drivers/platform/surface/aggregator/controller.c
    :internal:


客户端设备总线
=================

.. kernel-doc:: drivers/platform/surface/aggregator/bus.c
    :internal:


核心
====

.. kernel-doc:: drivers/platform/surface/aggregator/core.c
    :internal:


追踪辅助函数
=============

.. kernel-doc:: drivers/platform/surface/aggregator/trace.h
