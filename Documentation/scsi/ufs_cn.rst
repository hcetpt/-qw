SPDX 许可证标识符: GPL-2.0

=======================
通用闪存存储
=======================

.. 目录

   1. 概述
   2. UFS 架构概述
     2.1 应用层
     2.2 UFS 传输协议 (UTP) 层
     2.3 UFS 互连 (UIC) 层
   3. UFSHCD 概述
     3.1 UFS 控制器初始化
     3.2 UTP 传输请求
     3.3 UFS 错误处理
     3.4 SCSI 错误处理
   4. BSG 支持
   5. UFS 参考时钟频率配置


1. 概述
===========

通用闪存存储（UFS）是针对闪存设备的存储规范。
它旨在为智能手机和平板电脑等移动设备中的嵌入式和可移除闪存存储提供一个通用存储接口。该规范由 JEDEC 固态技术协会定义。UFS 基于 MIPI M-PHY 物理层标准。UFS 使用 MIPI M-PHY 作为物理层，MIPI Unipro 作为链路层。
UFS 的主要目标是：

 * 优化性能：
   对于 UFS 1.0 和 1.1 版本，目标性能如下：
   - 必须支持 Gear1（速率 A：1248 Mbps，速率 B：1457.6 Mbps）
   - 可选支持 Gear2（速率 A：2496 Mbps，速率 B：2915.2 Mbps）

   未来版本的标准，
   - Gear3（速率 A：4992 Mbps，速率 B：5830.4 Mbps）

 * 低功耗
 * 高随机 IOPs 和低延迟


2. UFS 架构概述
============================

UFS 采用分层通信架构，基于 SCSI SAM-5 架构模型。
UFS 通信架构包括以下几层：

2.1 应用层
---------------------

  应用层由 UFS 命令集层（UCS）、任务管理器和设备管理器组成。UFS 接口设计为协议无关的，但 SCSI 被选为 UFS 协议层 1.0 和 1.1 版本的基础协议。
UFS 支持由 SPC-4 和 SBC-3 定义的一组 SCSI 命令。

* UCS：
     处理 UFS 规范支持的 SCSI 命令
* 任务管理器：
     处理 UFS 定义的任务管理功能，用于命令队列控制
* 设备管理器：
     处理设备级别的操作和设备配置操作。设备级别操作主要包括设备电源管理操作和向互连层发送的命令。设备级别的配置涉及处理查询请求，这些请求用于修改和检索设备的配置信息

2.2 UFS 传输协议 (UTP) 层
--------------------------------------

  UTP 层通过服务访问点为更高层提供服务。UTP 定义了三个服务访问点供更高层使用。
* UDM_SAP: 设备管理服务访问点暴露给设备管理器，以执行设备级别的操作。这些设备级别的操作通过查询请求完成。
* UTP_CMD_SAP: 命令服务访问点暴露给UFS命令集层（UCS），用于传输命令。
* UTP_TM_SAP: 任务管理服务访问点暴露给任务管理器，用于传输任务管理功能。
UTP通过UFS协议信息单元（UPIU）传输消息。

### 2.3 UFS互连（UIC）层
--------------------------

UIC是UFS分层架构中的最低层。它处理UFS主机和UFS设备之间的连接。UIC包括MIPI UniPro和MIPI M-PHY。UIC向上层提供两个服务访问点：

* UIC_SAP: 用于在UFS主机和UFS设备之间传输UPIU。
* UIO_SAP: 用于向UniPro层发出命令。

### 3. UFS主机控制器驱动概述
==================

UFS主机控制器驱动基于Linux SCSI框架。UFSHCD是一个低级设备驱动程序，作为SCSI中间层和PCIe基UFS主机控制器之间的接口。
当前的UFSHCD实现支持以下功能：

#### 3.1 UFS控制器初始化
---------------------------------

初始化模块将UFS主机控制器带入活动状态，并准备控制器以在UFSHCD和UFS设备之间传输命令/响应。

#### 3.2 UTP传输请求
-------------------------

UFSHCD的传输请求处理模块接收来自SCSI中间层的SCSI命令，形成UPIU并将UPIU发送给UFS主机控制器。此外，该模块解码从UFS主机控制器接收到的UPIU形式的响应，并通知SCSI中间层命令的状态。
### 3.3 UFS 错误处理
----------------------

错误处理模块处理主机控制器致命错误、设备致命错误以及与 UIC 互连层相关的错误。

### 3.4 SCSI 错误处理
-----------------------

这是通过注册到 SCSI 中间层的 UFSHCD SCSI 错误处理例程来完成的。SCSI 中间层发出的一些错误处理命令示例包括中止任务、LUN 重置和主机重置。用于执行这些任务的 UFSHCD 例程通过 `.eh_abort_handler`、`.eh_device_reset_handler` 和 `.eh_host_reset_handler` 注册到 SCSI 中间层。

在当前版本的 UFSHCD 中，查询请求和电源管理功能尚未实现。

### 4. BSG 支持
==============

此传输驱动程序支持与 UFS 设备交换 UFS 协议信息单元（UPIU）。通常，用户空间会分配 `struct ufs_bsg_request` 和 `struct ufs_bsg_reply`（参见 `ufs_bsg.h`）作为 `request_upiu` 和 `reply_upiu`。填充这些 UPIU 应遵循 JEDEC 规范 UFS2.1 第 10.7 节的规定。
*买者自负*：驱动程序不会进一步验证输入，并将 UPIU 原封不动地发送给设备。打开 `/dev/ufs-bsg` 下的 bsg 设备并使用适用的 `sg_io_v4` 发送：

```c
io_hdr_v4.guard = 'Q';
io_hdr_v4.protocol = BSG_PROTOCOL_SCSI;
io_hdr_v4.subprotocol = BSG_SUB_PROTOCOL_SCSI_TRANSPORT;
io_hdr_v4.response = (__u64)reply_upiu;
io_hdr_v4.max_response_len = reply_len;
io_hdr_v4.request_len = request_len;
io_hdr_v4.request = (__u64)request_upiu;
if (dir == SG_DXFER_TO_DEV) {
    io_hdr_v4.dout_xfer_len = (uint32_t)byte_cnt;
    io_hdr_v4.dout_xferp = (uintptr_t)(__u64)buff;
} else {
    io_hdr_v4.din_xfer_len = (uint32_t)byte_cnt;
    io_hdr_v4.din_xferp = (uintptr_t)(__u64)buff;
}
```

如果您希望读取或写入描述符，请使用相应的 `xferp`。

与 ufs-bsg 端点交互并使用其基于 UPIU 的协议的用户空间工具可在以下位置找到：
```
https://github.com/westerndigitalcorporation/ufs-tool
```

有关该工具及其支持功能的更详细信息，请参阅工具的 README。

UFS 规范可在此处找到：
- UFS - http://www.jedec.org/sites/default/files/docs/JESD220.pdf
- UFSHCI - http://www.jedec.org/sites/default/files/docs/JESD223.pdf

### 5. UFS 参考时钟频率配置
==================================

设备树可以在 UFS 控制器节点下定义一个名为 “ref_clk” 的时钟，以指定 UFS 存储部件预期的参考时钟频率。ACPI 基础系统可以使用名为 “ref-clk-freq” 的 ACPI 设备特定数据属性来指定频率。在这两种情况下，值被解释为 Hz 频率，并且必须与 UFS 规范中给出的值之一匹配。UFS 子系统将在执行通用控制器初始化时尝试读取该值。如果该值可用，UFS 子系统将确保 UFS 存储设备的 `bRefClkFreq` 属性相应设置，并在不匹配的情况下进行修改。
