SPDX 许可声明标识符: GPL-2.0

==============================
驱动程序实现者的 API 指南
==============================

内核提供了大量的接口来支持设备驱动程序的开发。本文档是这些接口中的一部分较为杂乱的集合——希望随着时间推移会变得更好！下面可以看到现有的子章节。
对于驱动程序作者的一般信息
======================================

本节包含了一些文档，这些文档在某个时间点上对大多数从事设备驱动程序工作的开发者来说应该是感兴趣的。
.. toctree::
   :maxdepth: 1

   基础知识
   驱动模型/index
   设备链接
   基础设施
   ioctl
   电源管理/pm/index

有用的辅助库
========================

本节包含了一些文档，这些文档在某个时间点上对大多数从事设备驱动程序工作的开发者来说应该是感兴趣的。
.. toctree::
   :maxdepth: 1

   早期用户空间/index
   连接器
   设备输入输出
   动态频率调整
   DMA缓冲区
   组件
   输入输出映射
   输入输出排序
   UIO教程
   VFIO中介设备
   VFIO
   VFIO PCI设备特定驱动接受

总线级别的文档
=======================

.. toctree::
   :maxdepth: 1

   辅助总线
   cxl/index
   EISA
   火线
   I3C/index
   ISA
   Men Chameleon总线
   PCI/index
   RapidIO/index
   Slimbus
   USB/index
   VirtIO/index
   VME
   W1
   Xillybus


子系统特定的API
=======================

.. toctree::
   :maxdepth: 1

   80211/index
   ACPI/index
   背光/LP855X驱动.rst
   时钟
   控制台
   加密/index
   DMA引擎/index
   DPLL
   EDAC
   固件/index
   FPGA/index
   帧缓冲
   显示器内存
   通用计数器
   GPIO/index
   HSI
   HTE/index
   I2C
   IIO/index
   InfiniBand
   输入
   互联
   IPMB
   IPMI
   LibATA
   邮箱
   MD/index
   多媒体/index
   MEI/index
   内存设备/index
   基于消息的
   各种设备
   各种各样的
   MMC/index
   MTD/index
   MTD NAND
   NFC/index
   NTB
   NVDIMM/index
   NVMEM
   并口低层
   PHY/index
   引脚控制
   PLDM固件/index
   PPS
   PTP
   PWM
   电压调节器
   重置
   RFkill
   S390驱动程序
   SCSI
   串行/index
   SM501
   SoundWire/index
   SPI
   Surface Aggregator/index
   Switchtec
   同步文件
   目标
   TEE
   热管理/index
   TTY/index
   WBRF
   WMI
   Xilinx/index
   Zorro

.. only::  子项目和html

   索引
   =======

   * :ref:`genindex`
