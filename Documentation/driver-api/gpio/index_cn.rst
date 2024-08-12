通用输入/输出 (GPIO)
=====================

内容：

.. toctree::
   :maxdepth: 2

   引言
   使用-GPIO
   驱动程序
   消费者
   板卡
   基于-GPIO的驱动程序
   bt8xxgpio

核心
====

.. kernel-doc:: include/linux/gpio/driver.h
   :internal:

.. kernel-doc:: drivers/gpio/gpiolib.c
   :export:

ACPI 支持
============

.. kernel-doc:: drivers/gpio/gpiolib-acpi.c
   :export:

设备树支持
==========

.. kernel-doc:: drivers/gpio/gpiolib-of.c
   :export:

设备管理 API
============

.. kernel-doc:: drivers/gpio/gpiolib-devres.c
   :export:

sysfs 辅助工具
=============

.. kernel-doc:: drivers/gpio/gpiolib-sysfs.c
   :export:
