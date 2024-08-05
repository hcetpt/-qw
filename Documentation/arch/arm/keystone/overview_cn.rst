==========================
TI Keystone Linux 概览
==========================

简介
------------
Keystone 系列的 SoC 基于 ARM Cortex-A15 MPCore 处理器和 c66x DSP 核心。本文档描述了用户在基于 Keystone 的德州仪器评估模块 (EVM) 上运行 Linux 所需的基本信息。以下 SoC 和 EVM 目前得到支持： 

K2HK SoC 和 EVM
=================

即 Keystone 2 Hawking/Kepler SoC
TCI6636K2H & TCI6636K2K: 请参阅文档

	http://www.ti.com/product/tci6638k2k
	http://www.ti.com/product/tci6638k2h

EVM:
  http://www.advantech.com/Support/TI-EVM/EVMK2HX_sd.aspx

K2E SoC 和 EVM
===============

即 Keystone 2 Edison SoC

K2E  -  66AK2E05:

请参阅文档

	http://www.ti.com/product/66AK2E05/technicaldocuments

EVM:
   https://www.einfochips.com/index.php/partnerships/texas-instruments/k2e-evm.html

K2L SoC 和 EVM
===============

即 Keystone 2 Lamarr SoC

K2L  -  TCI6630K2L:

请参阅文档
	http://www.ti.com/product/TCI6630K2L/technicaldocuments

EVM:
  https://www.einfochips.com/index.php/partnerships/texas-instruments/k2l-evm.html

配置
-------------

所有 K2 SoC/EVM 都共享一个通用的 defconfig，即 keystone_defconfig，并且使用相同的镜像来启动各个 EVM。平台配置是通过设备树 (DTS) 文件指定的。以下是使用的 DTS 文件：

	K2HK EVM:
		k2hk-evm.dts
	K2E EVM:
		k2e-evm.dts
	K2L EVM:
		k2l-evm.dts

Keystone 设备树文档位于

        Documentation/devicetree/bindings/arm/keystone/keystone.txt

文档作者
---------------
Murali Karicheri <m-karicheri2@ti.com>

版权所有 2015 德州仪器
