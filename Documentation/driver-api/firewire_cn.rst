火线（IEEE 1394）驱动程序接口指南
===========================================

简介和概述
=========================

Linux 火线子系统向 Linux 系统添加了一些接口，用于使用/维护 IEEE 1394 总线上任何资源。这些接口的主要目的是通过 ISO/IEC 13213 (IEEE 1212) 过程访问 IEEE 1394 总线上每个节点的地址空间，并通过 IEEE 1394 过程控制总线上的等时资源。
根据接口使用者的不同，添加了两种类型的接口。一套用户空间接口可通过 `火线字符设备` 使用。一套内核接口则可通过 `firewire-core` 模块中的导出符号获取。

火线字符设备数据结构
====================================

.. include:: ../ABI/stable/firewire-cdev
    :literal:

.. kernel-doc:: include/uapi/linux/firewire-cdev.h
    :internal:

火线设备探测与 sysfs 接口
============================================

.. include:: ../ABI/stable/sysfs-bus-firewire
    :literal:

.. kernel-doc:: drivers/firewire/core-device.c
    :export:

火线核心交易接口
====================================

.. kernel-doc:: drivers/firewire/core-transaction.c
    :export:

火线等时I/O 接口
===================================

.. kernel-doc:: drivers/firewire/core-iso.c
   :export:
