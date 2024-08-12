目标和iSCSI接口指南
==================

简介与概述
==========

待定

目标核心设备接口
=================

本节为空，因为尚未向`drivers/target/target_core_device.c`添加kerneldoc注释。

目标核心传输接口
==================

.. kernel-doc:: drivers/target/target_core_transport.c
    :export:

目标支持的用户空间I/O
=====================

.. kernel-doc:: drivers/target/target_core_user.c
    :doc: 用户空间I/O

.. kernel-doc:: include/uapi/linux/target_core_user.h
    :doc: 环设计

iSCSI辅助函数
=============

.. kernel-doc:: drivers/scsi/libiscsi.c
   :export:


iSCSI启动信息
=============

.. kernel-doc:: drivers/scsi/iscsi_boot_sysfs.c
   :export:

iSCSI TCP接口
=============

.. kernel-doc:: drivers/scsi/iscsi_tcp.c
   :internal:

.. kernel-doc:: drivers/scsi/libiscsi_tcp.c
   :export:
