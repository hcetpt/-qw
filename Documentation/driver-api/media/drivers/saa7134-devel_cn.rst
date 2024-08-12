SPDX 许可证标识符: GPL-2.0

saa7134 驱动程序
===============

作者 Gerd Hoffmann


卡的变体:
---------

卡可以使用以下两种晶体之一（xtal）：

- 32.11 MHz -> .audio_clock=0x187de7
- 24.576 MHz -> .audio_clock=0x200000 （xtal * .audio_clock = 51539600）

关于 30/34/35 的一些细节：

- saa7130 - 低价芯片，没有静音功能，因此所有这些
  卡在其调谐器结构中都应定义 .mute 字段
- saa7134 - 通常的芯片

- saa7133/35 - saa7135 可能是一个市场决策，因为所有这些
  芯片在 PCI 上都自识别为 33
LifeView GPIOs
--------------

本节由：Peter Missel <peter.missel@onlinehome.de> 编写

- LifeView FlyTV Platinum FM (LR214WF)

    - GP27    MDT2005 PB4 第 10 引脚
    - GP26    MDT2005 PB3 第 9 引脚
    - GP25    MDT2005 PB2 第 8 引脚
    - GP23    MDT2005 PB1 第 7 引脚
    - GP22    MDT2005 PB0 第 6 引脚
    - GP21    MDT2005 PB5 第 11 引脚
    - GP20    MDT2005 PB6 第 12 引脚
    - GP19    MDT2005 PB7 第 13 引脚
    - nc      MDT2005 PA3 第 2 引脚
    - Remote  MDT2005 PA2 第 1 引脚
    - GP18    MDT2005 PA1 第 18 引脚
    - nc      MDT2005 PA0 第 17 引脚，低电平连接
    - GP17    “GP7”=高电平
    - GP16    “GP6”=高电平

	- 0=收音机 1=电视
	- 驱动 SA630D ENCH1 和 HEF4052 A1 引脚以通过
	  SIF 输入进行 FM 收音机

    - GP15    nc
    - GP14    nc
    - GP13    nc
    - GP12    “GP5” = 高电平
    - GP11    “GP4” = 高电平
    - GP10    “GP3” = 高电平
    - GP09    “GP2” = 低电平
    - GP08    “GP1” = 低电平
    - GP07.00 nc

鸣谢
-------

andrew.stevens@philips.com + werner.leeb@philips.com 提供了
saa7134 硬件规格和示例板的信息。
