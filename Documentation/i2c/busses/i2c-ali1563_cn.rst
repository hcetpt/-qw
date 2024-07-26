=========================
内核驱动 i2c-ali1563
=========================

支持的适配器：
  * Acer Labs, Inc. ALI 1563（南桥）

    数据手册：现处于保密协议（NDA）之下
	http://www.ali.com.tw/

作者：Patrick Mochel <mochel@digitalimplant.org>

描述
-----------

这是用于 Acer Labs Inc. (ALI) M1563 南桥上的 SMB 主控制器的驱动程序。
有关这些芯片的概述，请参见 http://www.acerlabs.com

M1563 南桥与 M1533 非常相似，但有几个值得注意的不同之处。其中一个不同之处在于他们将 I2C 核心升级为符合 SMBus 2.0 的标准，并且几乎与 Intel 801 南桥中找到的 I2C 控制器相同。
特性
--------

此驱动程序仅控制 SMB 主机。该驱动程序不使用中断。
