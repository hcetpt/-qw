SPDX 许可证标识符: GPL-2.0

Zoran 驱动程序
=============

统一的 Zoran 驱动程序 (zr360x7, zoran, buz, dc10(+), dc30(+), lml33)

网站: http://mjpeg.sourceforge.net/driver-zoran/

常见问题解答
--------------

支持哪些卡？
--------------

Iomega Buz、Linux Media Labs LML33/LML33R10、Pinnacle/Miro
DC10/DC10+/DC30/DC30+ 及其相关板卡（以各种名称提供）
Iomega Buz
~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Philips saa7111 电视解码器
* Philips saa7185 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, saa7111, saa7185, zr36060, zr36067

输入/输出: 复合和 S-视频

标准: PAL, SECAM (720x576 @ 25 fps), NTSC (720x480 @ 29.97 fps)

卡号: 7

AverMedia 6 Eyes AVS6EYES
~~~~~~~~~~~~~~~~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Samsung ks0127 电视解码器
* Conexant bt866 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, ks0127, bt866, zr36060, zr36067

输入/输出:
	六个物理输入。1-6 为复合，
	1-2, 3-4, 5-6 兼作 S-视频，
	1-3 还可作为分量信号
一个复合输出
标准: PAL, SECAM (720x576 @ 25 fps), NTSC (720x480 @ 29.97 fps)

卡号: 8

.. note:: 

   不会自动检测，必须指定 card=8
Linux Media Labs LML33
~~~~~~~~~~~~~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Brooktree bt819 电视解码器
* Brooktree bt856 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, bt819, bt856, zr36060, zr36067

输入/输出: 复合和 S-视频

标准: PAL (720x576 @ 25 fps), NTSC (720x480 @ 29.97 fps)

卡号: 5

Linux Media Labs LML33R10
~~~~~~~~~~~~~~~~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Philips saa7114 电视解码器
* Analog Devices adv7170 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, saa7114, adv7170, zr36060, zr36067

输入/输出: 复合和 S-视频

标准: PAL (720x576 @ 25 fps), NTSC (720x480 @ 29.97 fps)

卡号: 6

Pinnacle/Miro DC10(新)
~~~~~~~~~~~~~~~~~~~~~~~

* Zoran zr36057 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Philips saa7110a 电视解码器
* Analog Devices adv7176 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, saa7110, adv7175, zr36060, zr36067

输入/输出: 复合、S-视频和内部

标准: PAL, SECAM (768x576 @ 25 fps), NTSC (640x480 @ 29.97 fps)

卡号: 1

Pinnacle/Miro DC10+(增强版)
~~~~~~~~~~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36060 MJPEG 编码器
* Philips saa7110a 电视解码器
* Analog Devices adv7176 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, saa7110, adv7175, zr36060, zr36067

输入/输出: 复合、S-视频和内部

标准: PAL, SECAM (768x576 @ 25 fps), NTSC (640x480 @ 29.97 fps)

卡号: 2

Pinnacle/Miro DC10(旧版)
~~~~~~~~~~~~~~~~~~~~~~~

* Zoran zr36057 PCI 控制器
* Zoran zr36050 MJPEG 编码器
* Zoran zr36016 视频前端或 Fuji md0211 视频前端 (克隆?)
* Micronas vpx3220a 电视解码器
* mse3000 电视编码器或 Analog Devices adv7176 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, vpx3220, mse3000/adv7175, zr36050, zr36016, zr36067

输入/输出: 复合、S-视频和内部

标准: PAL, SECAM (768x576 @ 25 fps), NTSC (640x480 @ 29.97 fps)

卡号: 0

Pinnacle/Miro DC30
~~~~~~~~~~~~~~~~~~

* Zoran zr36057 PCI 控制器
* Zoran zr36050 MJPEG 编码器
* Zoran zr36016 视频前端
* Micronas vpx3225d/vpx3220a/vpx3216b 电视解码器
* Analog Devices adv7176 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, vpx3220/vpx3224, adv7175, zr36050, zr36016, zr36067

输入/输出: 复合、S-视频和内部

标准: PAL, SECAM (768x576 @ 25 fps), NTSC (640x480 @ 29.97 fps)

卡号: 3

Pinnacle/Miro DC30+(增强版)
~~~~~~~~~~~~~~~~~~~

* Zoran zr36067 PCI 控制器
* Zoran zr36050 MJPEG 编码器
* Zoran zr36016 视频前端
* Micronas vpx3225d/vpx3220a/vpx3216b 电视解码器
* Analog Devices adv7176 电视编码器

需要使用的驱动程序: videodev, i2c-core, i2c-algo-bit,
videocodec, vpx3220/vpx3224, adv7175, zr36050, zr36015, zr36067

输入/输出: 复合、S-视频和内部

标准: PAL, SECAM (768x576 @ 25 fps), NTSC (640x480 @ 29.97 fps)

卡号: 4

.. note:: 

   #) 尚未提供 mse3000 的模块
   #) 尚未提供 vpx3224 的模块

1.1 电视解码器可以做什么以及不能做什么
------------------------------------------

最知名的电视标准是 NTSC/PAL/SECAM。但是，对于解码一帧来说，这些信息并不足够。存在多种格式的电视标准，并非每个电视解码器都能处理所有格式。而且并非每种组合都受到驱动程序的支持。目前全球共有 11 种不同的电视广播格式。
CCIR 定义了进行信号广播所需的参数。
CCIR 制定了不同的标准：A,B,D,E,F,G,D,H,I,K,K1,L,M,N,..
CCIR 对所用的颜色系统并没有详细说明！！！
而谈论颜色系统并不能说明它是如何广播的。
CCIR 标准 A,E,F 已不再使用。
