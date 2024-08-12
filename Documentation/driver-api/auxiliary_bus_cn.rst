SPDX 许可证标识符: 仅 GPL-2.0

.. _辅助总线:

=============
辅助总线
=============

.. kernel-doc:: drivers/base/auxiliary.c
   :doc: 目的

何时应使用辅助总线
=====================================

.. kernel-doc:: drivers/base/auxiliary.c
   :doc: 使用方法

创建辅助设备
=========================

.. kernel-doc:: include/linux/auxiliary_bus.h
   :identifiers: 辅助设备

.. kernel-doc:: drivers/base/auxiliary.c
   :identifiers: 辅助设备初始化 __添加辅助设备 辅助查找设备

辅助设备内存模型与生命周期
------------------------------------------

.. kernel-doc:: include/linux/auxiliary_bus.h
   :doc: 设备生命周期

辅助驱动程序
=================

.. kernel-doc:: include/linux/auxiliary_bus.h
   :identifiers: 辅助驱动程序 module_辅助驱动程序

.. kernel-doc:: drivers/base/auxiliary.c
   :identifiers: __注册辅助驱动程序 注销辅助驱动程序

示例用法
=============

.. kernel-doc:: drivers/base/auxiliary.c
   :doc: 示例
请注意，上述内容可能需要根据实际文档进行调整。
