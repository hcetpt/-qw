```plaintext
SPDX 许可证标识符: GPL-2.0

======================
SCSI 内核参数
======================

有关指定模块参数的一般信息，请参阅 Documentation/admin-guide/kernel-parameters.rst
本文档可能不是完全最新的和全面的。命令 ``modinfo -p ${modulename}`` 会显示可加载模块当前的所有参数列表。在加载到正在运行的内核后，可加载模块也会在其路径 /sys/module/${modulename}/parameters/ 中显示其参数。这些参数中的一部分可以通过命令 ``echo -n ${value} > /sys/module/${modulename}/parameters/${parm}`` 在运行时进行更改。

advansys=	[HW,SCSI]
			参见 drivers/scsi/advansys.c 的头部
aha152x=	[HW,SCSI]
			参见 Documentation/scsi/aha152x.rst
aha1542=	[HW,SCSI]
			格式: <portbase>[,<buson>,<busoff>[,<dmaspeed>]]

	aic7xxx=	[HW,SCSI]
			参见 Documentation/scsi/aic7xxx.rst
aic79xx=	[HW,SCSI]
			参见 Documentation/scsi/aic79xx.rst
atascsi=	[HW,SCSI]
			参见 drivers/scsi/atari_scsi.c
BusLogic=	[HW,SCSI]
			参见 drivers/scsi/BusLogic.c，在函数 BusLogic_ParseDriverOptions() 前的注释
gvp11=		[HW,SCSI]

	ips=		[HW,SCSI] Adaptec / IBM ServeRAID 控制器
			参见 drivers/scsi/ips.c 的头部
mac5380=	[HW,SCSI]
			参见 drivers/scsi/mac_scsi.c
```
```plaintext
scsi_mod.max_luns=
			[SCSI] 要探测的最大 LUN 数量
应该在 1 到 2^32-1 之间

scsi_mod.max_report_luns=
			[SCSI] 接收到的最大 LUN 数量
应该在 1 到 16384 之间

NCR_D700=	[HW,SCSI]
			参见 drivers/scsi/NCR_D700.c 的头部

ncr5380=	[HW,SCSI]
			参见 Documentation/scsi/g_NCR5380.rst

ncr53c400=	[HW,SCSI]
			参见 Documentation/scsi/g_NCR5380.rst

ncr53c400a=	[HW,SCSI]
			参见 Documentation/scsi/g_NCR5380.rst

ncr53c8xx=	[HW,SCSI]

osst=		[HW,SCSI] SCSI 磁带驱动程序
			格式: <buffer_size>,<write_threshold>
			另见 Documentation/scsi/st.rst

scsi_debug_*=	[SCSI]
			参见 drivers/scsi/scsi_debug.c
```
```plaintext
scsi_mod.default_dev_flags=
	[SCSI] SCSI 默认设备标志
	格式: <整数>

scsi_mod.dev_flags=
	[SCSI] 摊贩和型号的黑白名单条目
	格式: <摊贩>:<型号>:<标志>
	(标志为整数值)

scsi_mod.scsi_logging_level=
	[SCSI] 日志记录级别的位掩码
	请参阅 drivers/scsi/scsi_logging.h 中的位定义。此外，
	也可以通过 sysctl 设置 dev.scsi.logging_level
	(/proc/sys/dev/scsi/logging_level)
S390-tools 包中还有一个方便的 'scsi_logging_level' 脚本，可从以下地址下载：
https://github.com/ibm-s390-linux/s390-tools/blob/master/scripts/scsi_logging_level

scsi_mod.scan=	[SCSI] sync（默认）在发现时同步扫描 SCSI 总线。async 在内核线程中扫描它们，
			允许系统启动继续进行。none 忽略它们，期望用户空间执行扫描

sim710=		[SCSI,HW]
			请参阅 drivers/scsi/sim710.c 的头部

st=		[HW,SCSI] SCSI 磁带参数（缓冲区等）
			请参阅 Documentation/scsi/st.rst

wd33c93=	[HW,SCSI]
			请参阅 drivers/scsi/wd33c93.c 的头部
```

以上是翻译后的中文版本。如果有任何特定部分需要进一步解释或修改，请告诉我。
