SPDX 许可证标识符: GPL-2.0

=========================================
HPSA - 惠普智能阵列驱动程序
=========================================

此文件描述了用于惠普智能阵列控制器的 hpsa SCSI 驱动程序。
hpsa 驱动程序旨在取代较新的智能阵列控制器所使用的 cciss 驱动程序。hpsa 驱动程序是一个 SCSI 驱动程序，而 cciss 驱动程序是一个“块”驱动程序。实际上，cciss 同时是一个块驱动程序（用于逻辑驱动器）和一个 SCSI 驱动程序（用于磁带驱动器）。这种“双重功能”的设计使 cciss 驱动程序复杂性增加，消除这种复杂性是 hpsa 存在的一个原因。

支持的设备
=================

- 智能阵列 P212
- 智能阵列 P410
- 智能阵列 P410i
- 智能阵列 P411
- 智能阵列 P812
- 智能阵列 P712m
- 智能阵列 P711m
- 存储工作站 P1210m

此外，如果内核启动参数中指定了 "hpsa_allow_any=1"，较旧的智能阵列也可以使用 hpsa 驱动程序。然而，这些设备并未经过测试且不被惠普支持。对于较旧的智能阵列，仍应使用 cciss 驱动程序。

启动参数 "hpsa_simple_mode=1" 可用于防止驱动程序将控制器置于“高性能”模式。简单模式下，每个命令完成都需要中断，而在“高性能模式”（默认模式，通常性能更好）下，单次中断可以表示多个命令完成。

HPSA 特有的 /sys 条目
=============================

除了在 /sys 中可用的通用 SCSI 属性外，hpsa 还支持以下属性：

HPSA 特有的主机属性
=============================

  ::

    /sys/class/scsi_host/host*/rescan
    /sys/class/scsi_host/host*/firmware_revision
    /sys/class/scsi_host/host*/resettable
    /sys/class/scsi_host/host*/transport_mode

  主机 “rescan” 属性是只写属性。向此属性写入数据将导致驱动程序扫描新设备、更改或移除的设备（例如热插拔的磁带驱动器，或新配置或删除的逻辑驱动器等），并通知 SCSI 中间层任何检测到的变化。通常这会由惠普的阵列配置工具（图形界面或命令行版本）自动触发，因此对于逻辑驱动器的变化，用户通常不需要使用此功能。当热插拔像磁带驱动器或整个包含预先配置的逻辑驱动器的存储箱时，该功能可能有用。

“firmware_revision” 属性包含智能阵列的固件版本。例如：

	root@host:/sys/class/scsi_host/host4# cat firmware_revision
	7.14

  “transport_mode” 表示控制器是否处于“高性能”或“简单”模式。这是由 “hpsa_simple_mode” 模块参数控制的。

“resettable” 只读属性表示特定控制器是否能够响应“reset_devices”内核参数。如果设备可以重置，则此文件将包含 “1”，否则为 “0”。此参数由 kdump 使用，例如，在加载驱动程序时重置控制器以消除控制器上的任何悬而未决的命令，并使控制器进入已知状态，以便 kdump 引发的 I/O 能正常工作且不受先前内核留下的过期命令或其他过期状态的影响。此属性允许 kexec 工具警告用户，如果他们尝试指定一个无法响应 “reset_devices” 内核参数的设备作为转储设备。

HPSA 特定的磁盘属性
-----------------------------

  ::

    /sys/class/scsi_disk/c:b:t:l/device/unique_id
    /sys/class/scsi_disk/c:b:t:l/device/raid_level
    /sys/class/scsi_disk/c:b:t:l/device/lunid

  （其中 c:b:t:l 分别代表控制器、总线、目标和 LUN）

  例如：

	root@host:/sys/class/scsi_disk/4:0:0:0/device# cat unique_id
	600508B1001044395355323037570F77
	root@host:/sys/class/scsi_disk/4:0:0:0/device# cat lunid
	0x0000004000000000
	root@host:/sys/class/scsi_disk/4:0:0:0/device# cat raid_level
	RAID 0

HPSA 特定的 ioctl
====================

为了与为 cciss 驱动程序编写的应用程序兼容，hpsa 驱动程序支持 cciss 驱动程序支持的许多（但不是全部）ioctl。这些 ioctl 使用的数据结构在 include/linux/cciss_ioctl.h 中描述。

  CCISS_DEREGDISK, CCISS_REGNEWDISK, CCISS_REGNEWD
	上述三个 ioctl 都执行相同的操作，即导致驱动程序重新扫描新设备。这与写入 hpsa 特定的主机 “rescan” 属性完全相同。
CCISS_GETPCIINFO
	返回 PCI 域、总线、设备和功能以及“板卡 ID”（PCI 子系统 ID）。
CCISS_GETDRIVVER
返回用三个字节编码的驱动程序版本，编码格式如下：

(major_version << 16) | (minor_version << 8) | (subminor_version)

CCISS_PASSTHRU, CCISS_BIG_PASSTHRU
允许“BMIC”和“CISS”命令传递给Smart Array
这些命令被HP Array Configuration Utility、SNMP存储代理等广泛使用。有关一些示例，请参阅http://cciss.sf.net 上的 cciss_vol_status。
