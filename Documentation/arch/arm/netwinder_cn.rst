NetWinder 特定文档
=================

NetWinder 是一款小型低功耗计算机，主要设计用于运行 Linux。它基于 StrongARM RISC 处理器、DC21285 PCI 桥接器，并在其周围集成了 PC 类型的硬件。

端口使用
========

======  ====== ===============================
最小值    最大值    描述
======  ====== ===============================
0x0000   0x000f   DMA1
0x0020   0x0021   PIC1
0x0060   0x006f   键盘
0x0070   0x007f   实时时钟 (RTC)
0x0080   0x0087   DMA1
0x0088   0x008f   DMA2
0x00a0   0x00a3   PIC2
0x00c0   0x00df   DMA2
0x0180   0x0187   红外数据关联 (IRDA)
0x01f0   0x01f6   IDE0
0x0201   游戏端口
0x0203   RWA010 配置读取
0x0220   ?       SoundBlaster
0x0250   ?       WaveArtist
0x0279   RWA010 配置索引
0x02f8   0x02ff   串行终端 ttyS1
0x0300   0x031f   以太网10 (Ether10)
0x0338   GPIO1
0x033a   GPIO2
0x0370   0x0371   W83977F 配置寄存器
0x0388   ?       AdLib
0x03c0   0x03df   VGA
0x03f6   IDE0
0x03f8   0x03ff   串行终端 ttyS0
0x0400   0x0408   DC21143
0x0480   0x0487   DMA1
0x0488   0x048f   DMA2
0x0a79   RWA010 配置写入
0xe800   0xe80f   IDE0/IDE1 块模式 DMA (BM DMA)
======  ====== ===============================

中断使用
========

====== ======= ========================
IRQ     类型    描述
====== ======= ========================
 0      ISA     100Hz 定时器
 1      ISA     键盘
 2      ISA     级联
 3      ISA     串行终端 ttyS1
 4      ISA     串行终端 ttyS0
 5      ISA     PS/2 鼠标
 6      ISA     红外数据关联 (IRDA)
 7      ISA     打印机
 8      ISA     实时时钟报警 (RTC alarm)
 9      ISA     
10      ISA     GP10 (橙色复位按钮)
11      ISA     
12      ISA     WaveArtist
13      ISA     
14      ISA     hda1
15      ISA     
====== ======= ========================

DMA 使用
========

====== ======= ===========
DMA     类型    描述
====== ======= ===========
 0      ISA     红外数据关联 (IRDA)
 1      ISA     
 2      ISA     级联
 3      ISA     WaveArtist
 4      ISA     
 5      ISA     
 6      ISA     
 7      ISA     WaveArtist
====== ======= ===========
