============= 
CerfBoard/Cube
=============

*** 强ARM版本的CerfBoard/Cube已停止生产 ***

Intrinsyc CerfBoard是一款基于强ARM 1110的板载计算机，尺寸大约为2英寸见方。它包含一个以太网控制器、一个与RS232兼容的串行端口、一个USB功能端口和一个位于背面的CompactFlash+插槽。可以在Intrinsyc网站上找到图片，网址为http://www.intrinsyc.com
本文档描述了Linux内核对Intrinsyc CerfBoard的支持。

在本版本中支持的功能
======================

   - CompactFlash+插槽（在General Setup中选择PCMCIA以及可能需要的任何选项）
   - 板载Crystal CS8900以太网控制器（Cerf CS8900A在Network Devices中的支持）
   - 带串行控制台的串行端口（硬编码为38400 8N1）

为了将此内核安装到您的Cerf上，您需要一台同时运行BOOTP和TFTP的服务端。随评估套件应该会附带详细的使用引导加载程序的说明。以下命令序列就足够了： 

   make ARCH=arm CROSS_COMPILE=arm-linux- cerfcube_defconfig
   make ARCH=arm CROSS_COMPILE=arm-linux- zImage
   make ARCH=arm CROSS_COMPILE=arm-linux- modules
   cp arch/arm/boot/zImage <TFTP目录>

support@intrinsyc.com
