=========================
内核驱动 i2c-amd-mp2
=========================

支持的适配器：
  * AMD MP2 PCIe 接口

数据手册：非公开可用
作者：
	- Shyam Sundar S K <Shyam-sundar.S-k@amd.com>
	- Nehal Shah <nehal-bakulchandra.shah@amd.com>
	- Elie Morisse <syniurge@gmail.com>

描述
-----------

MP2 是一个被编程为 I2C 控制器的 ARM 处理器，并通过 PCI 与 x86 主机通信。
如果你在你的 ``lspci -v`` 命令输出中看到类似这样的内容：

  03:00.7 MP2 I2C 控制器: Advanced Micro Devices, Inc. [AMD] Device 15e6

那么这个驱动适用于你的设备。
