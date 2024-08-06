======================
内核驱动 i2c-ismt
======================


支持的适配器：
  * Intel S12xx 系列 SOC

作者：
	Bill Brown <bill.e.brown@intel.com>


模块参数
-----------------

* bus_speed（无符号整数）

允许更改总线速度。通常，总线速度由 BIOS 设置，并且不需要更改。但是，一些 SMBus 分析器在调试过程中监控总线时速度太慢，因此需要这个模块参数。
以 kHz 指定总线速度。
可用的总线频率设置：

  ====   =========
  0      不变
  80     kHz
  100    kHz
  400    kHz
  1000   kHz
  ====   =========


描述
-----------

S12xx 系列 SOC 集成了两个 SMBus 2.0 控制器，主要面向微型服务器和存储市场。
S12xx 系列包含两个 PCI 功能。使用 `lspci` 输出会显示如下信息：

  00:13.0 系统外围设备：Intel Corporation Centerton SMBus 2.0 控制器 0
  00:13.1 系统外围设备：Intel Corporation Centerton SMBus 2.0 控制器 1
