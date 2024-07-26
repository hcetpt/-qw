========================
内核驱动 w1_ds28e04
========================

支持的芯片：

  * Maxim DS28E04-100 4096位可寻址1线EEPROM带PIO

支持的家庭代码：

        =================	====
	W1_FAMILY_DS28E04	0x1C
        =================	====

作者: Markus Franke, <franke.m@sebakmt.com> <franm@hrz.tu-chemnitz.de>

描述
-----------

支持通过 sysfs 文件 "eeprom" 和 "pio" 提供。在内存访问期间的 CRC 校验可以选通过设备属性 "crccheck" 启用/禁用。强上拉可以通过模块参数 "w1_strong_pullup" 选启用/禁用。
内存访问

	对 "eeprom" 文件的读操作从 DS28E04 的 EEPROM 中读取指定数量的字节。
对 "eeprom" 文件的写操作将给定的字节序列写入 DS28E04 的 EEPROM。如果启用了 CRC 校验模式，则只允许写入完全对齐的 32 字节块，并且具有有效的 CRC16 值（位于第 30 和 31 字节）。
PIO 访问

	DS28E04-100 的两个 PIO 可以通过 "pio" sysfs 文件访问。
PIO 的当前状态以一个 8 位值返回。位 0/1 表示 PIO_0/PIO_1 的状态。位 2..7 无意义。PIO 为低电平有效，即驱动程序提供/期望低电平有效值。
