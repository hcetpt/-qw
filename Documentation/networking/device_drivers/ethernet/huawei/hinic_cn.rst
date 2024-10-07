SPDX 许可证标识符: GPL-2.0

============================================================
华为智能网卡（HiNIC）系列的 Linux 内核驱动
============================================================

概述：
======
HiNIC 是一种用于数据中心区域的网络接口卡。
该驱动支持一系列链路速率设备（10GbE、25GbE、40GbE 等）。
该驱动还支持可协商和扩展的功能集。
某些 HiNIC 设备支持 SR-IOV。此驱动程序用于物理功能（PF）。
HiNIC 设备支持每个发送/接收队列的 MSI-X 中断向量及自适应中断调节。
HiNIC 设备还支持多种卸载功能，如校验和卸载、TCP 发送分段卸载（TSO）、接收侧扩展（RSS）和大接收卸载（LRO）。

支持的 PCI 厂商 ID/设备 ID：
===================================
19e5:1822 - HiNIC PF

驱动架构与源代码：
====================
hinic_dev - 实现一个逻辑网络设备，独立于特定硬件细节的数据结构格式。
hinic_hwdev - 实现设备的硬件细节，并包含访问 PCI NIC 的组件。
hinic_hwdev 包含以下组件：
===============================================
硬件接口：
=============
访问 pci 设备的接口（DMA 内存和 PCI BAR）
（hinic_hw_if.c, hinic_hw_if.h）

配置状态寄存器区域，描述配置和状态 BAR0 上的硬件寄存器。（hinic_hw_csr.h）

管理（MGMT）组件：
==================
异步事件队列（AEQs） - 从卡上的管理模块接收消息的事件队列。（hinic_hw_eqs.c, hinic_hw_eqs.h）

应用编程接口命令（API CMD） - 向卡发送管理命令的接口。（hinic_hw_api_cmd.c, hinic_hw_api_cmd.h）

管理（MGMT） - 使用 API CMD 向卡发送管理命令并从卡上的管理模块接收通知的 PF 到 MGMT 通道。同时设置硬件中 IO CMDQ 的地址。
### IO组件：
==================

完成事件队列（CEQs） - 描述已完成IO任务的完成事件队列。（hinic_hw_eqs.c, hinic_hw_eqs.h）

工作队列（WQ） - 包含用于CMD队列和队列对使用的内存和操作。WQ是一个页面中的内存块。该块包含指向工作队列元素（WQEs）内存区域的指针。（hinic_hw_wq.c, hinic_hw_wq.h）

命令队列（CMDQ） - 用于发送IO管理命令的队列，并用于在硬件中设置QP地址。命令完成事件会累积到配置为接收CMDQ完成事件的CEQ上。（hinic_hw_cmdq.c, hinic_hw_cmdq.h）

队列对（QPs） - 用于接收和传输数据的硬件接收和发送队列。（hinic_hw_qp.c, hinic_hw_qp.h, hinic_hw_qp_ctxt.h）

IO - 构建和销毁所有IO组件。（hinic_hw_io.c, hinic_hw_io.h）

### 硬件设备：
=================

硬件设备 - 在驱动初始化时构建和销毁硬件接口、MGMT组件以及在接口上下事件时构建和销毁IO组件。（hinic_hw_dev.c, hinic_hw_dev.h）

### hinic_dev 包含以下组件：
===============================================

PCI ID表 - 包含支持的PCI厂商/设备ID。（hinic_pci_tbl.h）

端口命令 - 发送命令到硬件设备进行端口管理（MAC、VLAN、MTU等）。（hinic_port.c, hinic_port.h）

发送队列（Tx Queues） - 使用硬件发送队列进行发送的逻辑发送队列。逻辑发送队列不依赖于硬件发送队列的格式。（hinic_tx.c, hinic_tx.h）

接收队列（Rx Queues） - 使用硬件接收队列进行接收的逻辑接收队列。逻辑接收队列不依赖于硬件接收队列的格式。（hinic_rx.c, hinic_rx.h）

hinic_dev - 构建和销毁逻辑发送和接收队列。（hinic_main.c, hinic_dev.h）

### 其他组件：
==================

被硬件和逻辑设备共同使用的通用函数。（hinic_common.c, hinic_common.h）

### 支持：
==================

如果在支持内核版本和适配器上发现发布的源代码存在问题，请将与问题相关的信息发送至aviad.krawczyk@huawei.com。
当然，请提供您需要翻译的文本。
