SPDX 许可证标识符: GPL-2.0

==============================================
SMARTPQI - Microchip 智能存储 SCSI 驱动程序
==============================================

此文件描述了用于 Microchip（http://www.microchip.com）PQI 控制器的 smartpqi SCSI 驱动程序。smartpqi 驱动程序是 Microchip 公司的新一代 SCSI 驱动程序。smartpqi 驱动程序是第一个实现 PQI 排队模型的 SCSI 驱动程序。smartpqi 驱动程序将取代 Adaptec Series 9 控制器的 aacraid 驱动程序。使用较旧内核（4.9 之前的版本）和 Adaptec Series 9 控制器的客户必须配置 smartpqi 驱动程序，否则他们的卷将不会添加到操作系统中。
对于 Microchip smartpqi 控制器的支持，请在配置内核时启用 smartpqi 驱动程序。
有关 PQI 排队接口的更多信息，请参阅：

- http://www.t10.org/drafts.htm
- http://www.t10.org/members/w_pqi2.htm

支持的设备
=================
<随着这些控制器公开可用，将添加控制器名称。>

smartpqi 特定的 /sys 条目
=================================

smartpqi 主机属性
------------------------
  - /sys/class/scsi_host/host*/rescan
  - /sys/class/scsi_host/host*/driver_version

  主机 rescan 属性是一个只写属性。写入此属性会触发驱动程序扫描新、更改或移除的设备，并通知 SCSI 中间层任何检测到的变化。
  版本属性是只读的，并将返回驱动程序版本和控制器固件版本。
例如：
```
              driver: 0.9.13-370
              firmware: 0.01-522
```

smartpqi SAS 设备属性
------------------------------
  HBA 设备被添加到 SAS 传输层。这些属性由 SAS 传输层自动添加。
/sys/class/sas_device/end_device-X:X/sas_address  
  /sys/class/sas_device/end_device-X:X/enclosure_identifier  
  /sys/class/sas_device/end_device-X:X/scsi_target_id  

smartpqi 特定的 ioctl
========================

  为了与为 cciss 协议编写的应用程序兼容，以下 ioctl 命令提供：
CCISS_DEREGDISK, CCISS_REGNEWDISK, CCISS_REGNEWD  
  上述三个 ioctl 命令都执行相同的操作，即导致驱动程序重新扫描新设备。这与写入 smartpqi 特定主机的 "rescan" 属性完全相同。
CCISS_GETPCIINFO  
  返回 PCI 域、总线、设备和功能以及 "板 ID"（PCI 子系统 ID）。
CCISS_GETDRIVVER  
  以如下编码方式返回驱动程序版本：
```
  (DRIVER_MAJOR << 28) | (DRIVER_MINOR << 24) | (DRIVER_RELEASE << 16) | DRIVER_REVISION;
```
  CCISS_PASSTHRU  
  允许 "BMIC" 和 "CISS" 命令传递给智能存储阵列。
这些被SSA阵列配置工具、SNMP存储代理等广泛使用。
