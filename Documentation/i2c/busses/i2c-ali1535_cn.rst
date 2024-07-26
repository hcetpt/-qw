=========================
内核驱动 i2c-ali1535
=========================

支持的适配器：
  * Acer Labs, Inc. ALI 1535（南桥）

    数据手册：现处于保密协议（NDA）之下
	http://www.ali.com.tw/

作者：
	- Frodo Looijaard <frodol@dds.nl>,
	- Philip Edelbrock <phil@netroedge.com>,
	- Mark D. Studebaker <mdsxyz123@yahoo.com>,
	- Dan Eaton <dan.eaton@rocketlogix.com>,
	- Stephen Rousset <stephen.rousset@rocketlogix.com>

描述
-----------

这是用于 Acer Labs Inc.（ALI）
M1535 南桥上的 SMB 主控制器的驱动程序。
M1535 是为便携式系统设计的南桥。它与 Acer Labs Inc. 生产的 M15x3 南桥非常相似。该芯片内部的一些寄存器位置发生了变化，一些寄存器的功能略有调整。
此外，SMBus 交易的序列化方式已经修改，以更符合制造商推荐的序列，并且通过测试观察到。这些更改在本驱动程序中有所体现，并可以通过将此驱动程序与 i2c-ali15x3 驱动程序进行比较来识别。有关这些芯片的概述，请参阅 http://www.acerlabs.com。

SMB 控制器是 M7101 设备的一部分，这是一个符合 ACPI 标准的电源管理单元（PMU）。
要使 SMB 正常工作，必须启用整个 M7101 设备。您不能仅单独启用 SMB。SMB 和 ACPI 有独立的 I/O 空间。我们确保 SMB 已被启用。而对 ACPI 则不作处理。
功能
--------

此驱动程序仅控制 SMB 主控制器。此驱动程序不使用中断。
