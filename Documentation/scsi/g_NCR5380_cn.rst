```
SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

================
g_NCR5380 驱动程序
================

版权所有 |copy| 1993 Drew Eckhard

NCR53c400 扩展版权所有 |copy| 1994, 1995, 1996 Kevin Lentin

此文件记录了由 Kevin Lentin 开发的 NCR53c400 扩展以及对 NCR5380 核心的一些增强。
此驱动程序支持 NCR5380 和 NCR53c400 及其兼容卡，并在端口或内存映射模式下工作。
如果主板支持中断，建议使用中断，这将允许目标设备断开连接，从而提高 SCSI 总线利用率。
如果 irq 参数为 254 或完全省略，则驱动程序会自动探测正确的中断线。如果 irq 参数为 0 或 255，则不使用中断。
NCR53c400 不支持 DMA，但它具有伪 DMA，该功能受驱动程序支持。
此驱动程序会在 /proc/scsi/g_NCR5380/x 中提供一些检测到的信息，其中 x 是启动时检测到的 SCSI 卡编号。未来将提供更多信息。
此驱动程序作为一个模块工作。
当作为模块包含时，可以在 insmod/modprobe 命令行中传递参数：

  ============= ===============================================================
  irq=xx[,...]    中断（中断线）
  base=xx[,...]   端口或基地址（对于端口或内存映射分别对应）
  card=xx[,...]   卡类型：

		==  ======================================
		0   NCR5380，
		1   NCR53C400，
		2   NCR53C400A，
		3   Domex Technology Corp 3181E (DTC3181E)
		4   Hewlett Packard C2502
		==  ======================================
  ============= ==============================================================

这些旧式参数只能支持一张卡：

  ============= =================================================
  ncr_irq=xx     中断
  ncr_addr=xx    端口或基地址（对于端口或内存映射分别对应）
  ncr_5380=1     设置为 NCR5380 板
  ncr_53c400=1   设置为 NCR53C400 板
  ncr_53c400a=1  设置为 NCR53C400A 板
  dtc_3181e=1    设置为 Domex Technology Corp 3181E 板
  hp_c2502=1     设置为 Hewlett Packard C2502 板
  ============= =================================================

例如：Trantor T130B 在默认配置下：

  modprobe g_NCR5380 irq=5 base=0x350 card=1

或者，使用旧语法：

  modprobe g_NCR5380 ncr_irq=5 ncr_addr=0x350 ncr_53c400=1

例如：一个端口映射的 NCR5380 板，驱动程序探测中断：

  modprobe g_NCR5380 base=0x350 card=0

或者：

  modprobe g_NCR5380 ncr_addr=0x350 ncr_5380=1

例如：没有中断的内存映射 NCR53C400 板：

  modprobe g_NCR5380 irq=255 base=0xc8000 card=1

或者：

  modprobe g_NCR5380 ncr_irq=255 ncr_addr=0xc8000 ncr_53c400=1

例如：两张卡，DTC3181（非 PnP 模式）位于 0x240 且无中断，HP C2502 位于 0x300 且中断为 7：

  modprobe g_NCR5380 irq=0,7 base=0x240,0x300 card=3,4

Kevin Lentin
K.Lentin@cs.monash.edu.au
```
