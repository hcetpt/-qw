========================
SPEAr ARM Linux 概览
========================

简介
------------

  SPEAr（Structured Processor Enhanced Architecture）
网址 : http://www.st.com/spear

  ST Microelectronics 的 SPEAr 系列 ARM9/CortexA9 系统级芯片 CPU 由 ARM Linux 的 'spear' 平台支持。目前支持的 SPEAr SOC 包括 SPEAr1310、SPEAr1340、SPEAr300、SPEAr310、SPEAr320 和 SPEAr600。SPEAr 的层级结构如下：

  SPEAr（平台）

	- SPEAr3XX（基于 ARM9 的 3XX SOC 系列）
		- SPEAr300（SOC）
			- SPEAr300 评估板
		- SPEAr310（SOC）
			- SPEAr310 评估板
		- SPEAr320（SOC）
			- SPEAr320 评估板
	- SPEAr6XX（基于 ARM9 的 6XX SOC 系列）
		- SPEAr600（SOC）
			- SPEAr600 评估板
	- SPEAr13XX（基于 ARM CORTEXA9 的 13XX SOC 系列）
		- SPEAr1310（SOC）
			- SPEAr1310 评估板
		- SPEAr1340（SOC）
			- SPEAr1340 评估板

配置
------------

  为每种机器提供了一个通用配置，可以作为默认配置使用：
	
	``make spear13xx_defconfig``
	``make spear3xx_defconfig``
	``make spear6xx_defconfig``

布局
------

  多个机器家族（SPEAr3xx、SPEAr6xx 和 SPEAr13xx）的通用文件位于 arch/arm/plat-spear 中的平台代码中，头文件位于 plat/ 目录下。
每个机器系列都有一个以 arch/arm/mach-spear 开头的目录，后面跟着系列名称。例如 mach-spear3xx、mach-spear6xx 和 mach-spear13xx。
SPEAr3xx 家族的通用文件是 mach-spear3xx/spear3xx.c，SPEAr6xx 是 mach-spear6xx/spear6xx.c，而 SPEAr13xx 家族的是 mach-spear13xx/spear13xx.c。mach-spear* 还包含 soc/机器特定文件，例如 spear1310.c、spear1340.c、spear300.c、spear310.c、spear320.c 和 spear600.c。mach-spear* 不包含特定于板卡的文件，因为它们完全支持 Flattened Device Tree。

文档作者
---------------

  Viresh Kumar <vireshk@kernel.org>，版权所有 © 2010-2012 ST Microelectronics
