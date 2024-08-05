==========================
三星 ARM Linux 概览
==========================

简介
------------

  三星的 ARM 系统芯片 (SoC) 系列涵盖了从最初的 ARM9 到最新的 ARM 内核的许多相似设备。本文档概述了当前内核支持、如何使用以及在哪里可以找到支持这些设备的代码。
目前支持的 SoC 包括：

  - S3C64XX: S3C6400 和 S3C6410
  - S5PC110 / S5PV210


配置
------------

  提供了多种配置，因为目前无法将所有 SoC 统一到一个内核中。
s5pc110_defconfig
	- S5PC110 的特定默认配置
  s5pv210_defconfig
	- S5PV210 的特定默认配置


布局
------

  目录布局正在进行重构，并由几个平台目录和为构建的 CPU 特定的机器目录组成。
plat-samsung 为所有实现提供了基础，并且是处理构建特定信息时包含目录中的最后一个。它包含了启动系统所需的基本时钟、GPIO 和设备定义。
plat-s5p 用于 s5p 特定的构建，并为 S5P 特定系统提供了通用支持。并非所有的 S5P 都使用此目录中的所有特性，因为硬件存在差异。
布局变更
--------------

  已经移除了旧的 plat-s3c 和 plat-s5pc1xx 目录，将支持分别移到了 plat-samsung 或 plat-s5p 中，根据需要进行调整。这些变动简化了包含多个不同平台目录所带来的包含和依赖问题。
贡献者
-----------------

  Ben Dooks (BJD)
  Vincent Sanders
  Herbert Potzl
  Arnaud Patard (RTP)
  Roc Wu
  Klaus Fetscher
  Dimitry Andric
  Shannon Holland
  Guillaume Gourat (NexVision)
  Christer Weinigel (wingel) (Acer N30)
  Lucas Correia Villa Real (S3C2400 端口)


文档作者
---------------

版权所有 2009-2010 Ben Dooks <ben-linux@fluff.org>
