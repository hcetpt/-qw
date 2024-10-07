===================================
戴尔系统管理基础驱动
===================================

概述
========

戴尔系统管理基础驱动为系统管理软件（如戴尔OpenManage）提供了一个sysfs接口，以便在某些戴尔系统上执行系统管理中断和主机控制操作（系统循环供电或操作系统关闭后断电）。戴尔OpenManage要求以下戴尔PowerEdge系统安装此驱动：300、1300、1400、400SC、500SC、1500SC、1550、600SC、1600SC、650、1655MC、700 和 750。其他戴尔软件（如开源libsmbios项目）预计也会使用此驱动，并且可能会在其他戴尔系统上使用该驱动。戴尔的libsmbios项目旨在尽可能地提供对BIOS信息的访问。有关libsmbios项目的更多信息，请参阅http://linux.dell.com/libsmbios/main/。

系统管理中断
===========================

在某些戴尔系统中，系统管理软件必须通过系统管理中断（SMI）访问特定的管理信息。SMI数据缓冲区必须位于32位地址空间内，并且需要SMI的数据缓冲区的物理地址。该驱动程序维护了SMI所需的内存，并提供了一种方法供应用程序生成SMI。该驱动程序创建了以下sysfs条目，以便系统管理软件执行这些系统管理中断：

- /sys/devices/platform/dcdbas/smi_data
- /sys/devices/platform/dcdbas/smi_data_buf_phys_addr
- /sys/devices/platform/dcdbas/smi_data_buf_size
- /sys/devices/platform/dcdbas/smi_request

系统管理软件必须按照以下步骤来使用此驱动程序执行一个SMI：

1) 锁定smi_data
2) 将系统管理命令写入smi_data
3) 将“1”写入smi_request以生成调用接口SMI 或将“2”写入以生成原始SMI
4) 从smi_data读取系统管理命令响应
5) 解锁smi_data

主机控制操作
===================

戴尔OpenManage支持一项主机控制功能，允许管理员在操作系统完成关闭后进行系统循环供电或断电。在某些戴尔系统上，这项主机控制功能要求驱动程序在操作系统完成关闭后执行一个SMI。
驱动程序为系统管理软件创建了以下 sysfs 条目，以便在系统完成关机后调度驱动程序执行电源循环或关闭主机控制操作：

/sys/devices/platform/dcdbas/host_control_action  
/sys/devices/platform/dcdbas/host_control_smi_type  
/sys/devices/platform/dcdbas/host_control_on_shutdown  

Dell OpenManage 执行以下步骤以使用此驱动程序执行电源循环或关闭主机控制操作：

1) 将要执行的主机控制操作写入 host_control_action  
2) 将驱动程序需要执行的 SMI 类型写入 host_control_smi_type  
3) 将 "1" 写入 host_control_on_shutdown 以启用主机控制操作  
4) 启动操作系统关机  
（当驱动程序接收到操作系统已完成关机的通知时，将执行主机控制 SMI。）

主机控制 SMI 类型
=====================

下表显示了为执行电源循环或关闭主机控制操作而需写入 host_control_smi_type 的值：

=================== =====================
PowerEdge 系统      主机控制 SMI 类型
=================== =====================
      300             HC_SMITYPE_TYPE1
     1300             HC_SMITYPE_TYPE1
     1400             HC_SMITYPE_TYPE2
      500SC           HC_SMITYPE_TYPE2
     1500SC           HC_SMITYPE_TYPE2
     1550             HC_SMITYPE_TYPE2
      600SC           HC_SMITYPE_TYPE2
     1600SC           HC_SMITYPE_TYPE2
      650             HC_SMITYPE_TYPE2
     1655MC           HC_SMITYPE_TYPE2
      700             HC_SMITYPE_TYPE3
      750             HC_SMITYPE_TYPE3
=================== =====================
