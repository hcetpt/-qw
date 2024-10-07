... SPDX 许可证标识符: GPL-2.0

===================================
AACRAID 驱动程序（Linux 版本二）
===================================

简介
============
aacraid 驱动程序为 Adaptec (http://www.adaptec.com) 的 RAID 控制器添加了支持。这是对原始 Adaptec 提供的驱动程序的重大重写。代码和运行时二进制文件大小都有显著改进（该模块的大小不到原始驱动的一半）。

支持的卡/芯片组
========================

	===================	=======	=======================================
	PCI ID (pci.ids)	OEM	产品
	===================	=======	=======================================
	9005:0285:9005:0285	Adaptec	2200S (Vulcan)
	9005:0285:9005:0286	Adaptec	2120S (Crusader)
	9005:0285:9005:0287	Adaptec	2200S (Vulcan-2m)
	9005:0285:9005:0288	Adaptec	3230S (Harrier)
	9005:0285:9005:0289	Adaptec	3240S (Tornado)
	9005:0285:9005:028a	Adaptec	2020ZCR (Skyhawk)
	9005:0285:9005:028b	Adaptec	2025ZCR (Terminator)
	9005:0286:9005:028c	Adaptec	2230S (Lancer)
	9005:0286:9005:028c	Adaptec	2230SLP (Lancer)
	9005:0286:9005:028d	Adaptec	2130S (Lancer)
	9005:0285:9005:028e	Adaptec	2020SA (Skyhawk)
	9005:0285:9005:028f	Adaptec	2025SA (Terminator)
	9005:0285:9005:0290	Adaptec	2410SA (Jaguar)
	9005:0285:103c:3227	Adaptec	2610SA (Bearcat HP 发行版)
	9005:0285:9005:0293	Adaptec	21610SA (Corsair-16)
	9005:0285:9005:0296	Adaptec	2240S (SabreExpress)
	9005:0285:9005:0292	Adaptec	2810SA (Corsair-8)
	9005:0285:9005:0297	Adaptec	4005 (AvonPark)
	9005:0285:9005:0298	Adaptec	4000 (BlackBird)
	9005:0285:9005:0299	Adaptec	4800SAS (Marauder-X)
	9005:0285:9005:029a	Adaptec	4805SAS (Marauder-E)
	9005:0286:9005:029b	Adaptec	2820SA (Intruder)
	9005:0286:9005:029c	Adaptec	2620SA (Intruder)
	9005:0286:9005:029d	Adaptec	2420SA (Intruder HP 发行版)
	9005:0286:9005:02ac	Adaptec	1800 (Typhoon44)
	9005:0285:9005:02b5	Adaptec	5445 (Voodoo44)
	9005:0285:15d9:02b5	SMC	AOC-USAS-S4i
	9005:0285:9005:02b6	Adaptec	5805 (Voodoo80)
	9005:0285:15d9:02b6	SMC	AOC-USAS-S8i
	9005:0285:9005:02b7	Adaptec	5085 (Voodoo08)
	9005:0285:9005:02bb	Adaptec	3405 (Marauder40LP)
	9005:0285:9005:02bc	Adaptec	3805 (Marauder80LP)
	9005:0285:9005:02c7	Adaptec	3085 (Marauder08ELP)
	9005:0285:9005:02bd	Adaptec	31205 (Marauder120)
	9005:0285:9005:02be	Adaptec	31605 (Marauder160)
	9005:0285:9005:02c3	Adaptec	51205 (Voodoo120)
	9005:0285:9005:02c4	Adaptec	51605 (Voodoo160)
	9005:0285:15d9:02c9	SMC	AOC-USAS-S4iR
	9005:0285:15d9:02ca	SMC	AOC-USAS-S8iR
	9005:0285:9005:02ce	Adaptec	51245 (Voodoo124)
	9005:0285:9005:02cf	Adaptec	51645 (Voodoo164)
	9005:0285:9005:02d0	Adaptec	52445 (Voodoo244)
	9005:0285:9005:02d1	Adaptec	5405 (Voodoo40)
	9005:0285:15d9:02d2	SMC	AOC-USAS-S8i-LP
	9005:0285:15d9:02d3	SMC	AOC-USAS-S8iR-LP
	9005:0285:9005:02d4	Adaptec	ASR-2045 (Voodoo04 Lite)
	9005:0285:9005:02d5	Adaptec	ASR-2405 (Voodoo40 Lite)
	9005:0285:9005:02d6	Adaptec	ASR-2445 (Voodoo44 Lite)
	9005:0285:9005:02d7	Adaptec	ASR-2805 (Voodoo80 Lite)
	9005:0285:9005:02d8	Adaptec	5405Z (Voodoo40 BLBU)
	9005:0285:9005:02d9	Adaptec	5445Z (Voodoo44 BLBU)
	9005:0285:9005:02da	Adaptec	5805Z (Voodoo80 BLBU)
	1011:0046:9005:0364	Adaptec	5400S (Mustang)
	1011:0046:9005:0365	Adaptec	5400S (Mustang)
	9005:0287:9005:0800	Adaptec	Themisto (Jupiter)
	9005:0200:9005:0200	Adaptec	Themisto (Jupiter)
	9005:0286:9005:0800	Adaptec	Callisto (Jupiter)
	1011:0046:9005:1364	Dell	PERC 2/QC (Quad Channel, Mustang)
	1011:0046:9005:1365	Dell	PERC 2/QC (Quad Channel, Mustang)
	1028:0001:1028:0001	Dell	PERC 2/Si (Iguana)
	1028:0003:1028:0003	Dell	PERC 3/Si (SlimFast)
	1028:0002:1028:0002	Dell	PERC 3/Di (Opal)
	1028:0004:1028:0004	Dell	PERC 3/SiF (Iguana)
	1028:0004:1028:00d0	Dell	PERC 3/DiF (Iguana)
	1028:0002:1028:00d1	Dell	PERC 3/DiV (Viper)
	1028:0002:1028:00d9	Dell	PERC 3/DiL (Lexus)
	1028:000a:1028:0106	Dell	PERC 3/DiJ (Jaguar)
	1028:000a:1028:011b	Dell	PERC 3/DiD (Dagger)
	1028:000a:1028:0121	Dell	PERC 3/DiB (Boxster)
	9005:0285:1028:0287	Dell	PERC 320/DC (Vulcan)
	9005:0285:1028:0291	Dell	CERC 2 (DellCorsair)
	1011:0046:103c:10c2	HP	NetRAID-4M (Mustang)
	9005:0285:17aa:0286	Legend	S220 (Crusader)
	9005:0285:17aa:0287	Legend	S230 (Vulcan)
	9005:0285:9005:0290	IBM	ServeRAID 7t (Jaguar)
	9005:0285:1014:02F2	IBM	ServeRAID 8i (AvonPark)
	9005:0286:1014:9540	IBM	ServeRAID 8k/8k-l4 (AuroraLite)
	9005:0286:1014:9580	IBM	ServeRAID 8k/8k-l8 (Aurora)
	9005:0285:1014:034d	IBM	ServeRAID 8s (Marauder-E)
	9005:0286:9005:029e	ICP	ICP9024RO (Lancer)
	9005:0286:9005:029f	ICP	ICP9014RO (Lancer)
	9005:0286:9005:02a0	ICP	ICP9047MA (Lancer)
	9005:0286:9005:02a1	ICP	ICP9087MA (Lancer)
	9005:0285:9005:02a4	ICP	ICP9085LI (Marauder-X)
	9005:0285:9005:02a5	ICP	ICP5085BR (Marauder-E)
	9005:0286:9005:02a6	ICP	ICP9067MA (Intruder-6)
	9005:0285:9005:02b2	ICP	(Voodoo 8 内置 8 外置)
	9005:0285:9005:02b8	ICP	ICP5445SL (Voodoo44)
	9005:0285:9005:02b9	ICP	ICP5085SL (Voodoo80)
	9005:0285:9005:02ba	ICP	ICP5805SL (Voodoo08)
	9005:0285:9005:02bf	ICP	ICP5045BL (Marauder40LP)
	9005:0285:9005:02c0	ICP	ICP5085BL (Marauder80LP)
	9005:0285:9005:02c8	ICP	ICP5805BL (Marauder08ELP)
	9005:0285:9005:02c1	ICP	ICP5125BR (Marauder120)
	9005:0285:9005:02c2	ICP	ICP5165BR (Marauder160)
	9005:0285:9005:02c5	ICP	ICP5125SL (Voodoo120)
	9005:0285:9005:02c6	ICP	ICP5165SL (Voodoo160)
	9005:0286:9005:02ab		(Typhoon40)
	9005:0286:9005:02ad		(Aurora ARK)
	9005:0286:9005:02ae		(Aurora Lite ARK)
	9005:0285:9005:02b0		(Sunrise Lake ARK)
	9005:0285:9005:02b1	Adaptec	(Voodoo 8 内置 8 外置)
	9005:0285:108e:7aac	SUN	STK RAID REM (Voodoo44 Coyote)
	9005:0285:108e:0286	SUN	STK RAID INT (Cougar)
	9005:0285:108e:0287	SUN	STK RAID EXT (Prometheus)
	9005:0285:108e:7aae	SUN	STK RAID EM (Narvi)
	===================	=======	=======================================

人员
======

Alan Cox <alan@lxorguk.ukuu.org.uk>

- 新式 PCI 探测和 SCSI 主机注册更新，小清理/修复

Matt Domsch <matt_domsch@dell.com>

- 修订 ioctl，适配器消息

Deanna Bonds

- 非 DASD 支持，PAE 修正和 64 位支持，添加新的 Adaptec 控制器
- 添加新的 ioctl，更改 SCSI 接口以使用新的错误处理程序，增加了容器中的 fibs 和未完成命令的数量
- 修正了 64 位和 64G 内存模型，更改了令人困惑的命名约定，其中发送到硬件的 fibs 一致称为 hw_fibs 而不是像驱动跟踪结构那样的 fibs

Mark Salyzyn <Mark_Salyzyn@adaptec.com>

- 解决了恐慌问题并为即将推出的 HBA 添加了一些新的产品 ID
- 性能调优，卡故障切换和错误缓解

Achim Leubner <Achim_Leubner@adaptec.com>

- 原始驱动程序

-------------------------

Adaptec Unix OEM 产品组

邮件列表
============

linux-scsi@vger.kernel.org （感兴趣的各方在此讨论）
请注意这与 Brian 的原始驱动程序非常不同，因此不要期望他支持它
Adaptec 支持此驱动程序。请联系 Adaptec 技术支持或 aacraid@adaptec.com

最初由 Brian Boerner 在 2001 年 2 月编写

由 Alan Cox 在 2001 年 11 月重写
