============================
内核驱动 i2c-diolan-u2c
============================

支持的适配器：
  * Diolan U2C-12 I2C-USB 适配器

    文档：
	http://www.diolan.com/i2c/u2c12.html

作者：Guenter Roeck <linux@roeck-us.net>

描述
-----------

这是 Diolan U2C-12 USB-I2C 适配器的驱动程序。
Diolan U2C-12 I2C-USB 适配器提供了一种低成本的解决方案，用于通过 USB 接口将计算机连接到 I2C 从设备。它还支持与 SPI 设备的连接。
此驱动程序仅支持 U2C-12 的 I2C 接口。该驱动程序不使用中断。

模块参数
-----------------

* frequency: I2C 总线频率
