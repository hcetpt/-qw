=========================
内核驱动 i2c-ali15x3
=========================

支持的适配器：
  * Acer Labs, Inc. ALI 1533 和 1543C（南桥）

    数据手册：现在处于保密协议下
	http://www.ali.com.tw/

作者：
	- Frodo Looijaard <frodol@dds.nl>,
	- Philip Edelbrock <phil@netroedge.com>,
	- Mark D. Studebaker <mdsxyz123@yahoo.com>

模块参数
-----------------

* force_addr: 整数
    初始化 I2C 控制器的基本地址


注释
-----

force_addr 参数对于那些没有在 BIOS 中设置地址的主板很有用。不会执行 PCI 强制；设备仍然必须出现在 lspci 输出中。除非驱动程序抱怨基本地址未设置，否则不要使用此选项。
示例::

    modprobe i2c-ali15x3 force_addr=0xe800

ASUS P5A 主板上的 SMBus 偶尔会挂起，并且只能通过电源循环清除。原因未知（请参阅下面的问题）
描述
-----------

这是针对 Acer Labs Inc.（ALI）M1541 和 M1543C 南桥的 SMB 主机控制器的驱动程序。
M1543C 是面向台式机系统的南桥。
M1541 是面向便携式系统的南桥。
它们是以下 ALI 芯片组的一部分：

 * "Aladdin Pro 2" 包括 M1621 Slot 1 北桥，具有 AGP 和 100MHz CPU 前端总线
 * "Aladdin V" 包括 M1541 Socket 7 北桥，具有 AGP 和 100MHz CPU 前端总线

   部分 Aladdin V 主板：
	- Asus P5A
	- Atrend ATC-5220
	- BCM/GVC VP1541
	- Biostar M5ALA
	- Gigabyte GA-5AX（通常不起作用，因为 BIOS 没有启用 7101 设备！）
	- Iwill XA100 Plus
	- Micronics C200
	- Microstar (MSI) MS-5169

  * "Aladdin IV" 包括 M1541 Socket 7 北桥，具有高达 83.3 MHz 的主机总线
有关这些芯片的概述，请参阅 http://www.acerlabs.com。目前，网站上的完整数据手册受密码保护，但是如果您联系 ALI 在圣何塞的办公室，他们可能会提供密码
M1533/M1543C 设备在 PCI 总线上显示为四个独立的设备。lspci 的输出将显示如下内容::

  00:02.0 USB 控制器: Acer Laboratories Inc. M5237 (rev 03)
  00:03.0 桥接器: Acer Laboratories Inc. M7101      <= 这是我们需要的那个
  00:07.0 ISA 桥接器: Acer Laboratories Inc. M1533 (rev c3)
  00:0f.0 IDE 接口: Acer Laboratories Inc. M5229 (rev c1)

.. important::

   如果您的主板上有 M1533 或 M1543C 并且收到
   "ali15x3: 错误：无法检测到 ali15x3！"
   则运行 lspci
如果您看到 1533 和 5229 设备但看不到 7101 设备，
   那么您必须在 BIOS 中启用 ACPI、PMU、SMB 或类似功能
如果找不到 M7101 设备，则驱动程序将无法工作
SMB 控制器是 M7101 设备的一部分，该设备是一个符合 ACPI 标准的电源管理单元（PMU）。
必须启用整个 M7101 设备才能使 SMB 正常工作。您不能单独启用 SMB。SMB 和 ACPI 有独立的 I/O 空间。我们确保 SMB 已被启用。对于 ACPI，则不作改动。
功能
------

此驱动程序仅控制 SMB 主机。M15X3 上的 SMB 从属控制器未被启用。此驱动程序不使用中断。
问题
------

此驱动程序仅请求 SMB 寄存器所需的 I/O 空间。它不使用 ACPI 区域。
在 ASUS P5A 主板上，有多份报告指出 SMBus 会出现挂起现象，而这种问题只能通过关闭计算机电源来解决。主板发热时这种情况似乎更严重，例如在 CPU 负载较高或夏季时。
这块主板可能存在电气方面的问题。
在 P5A 上，W83781D 传感器芯片同时位于 ISA 总线和 SMBus 上。因此通常可以通过仅通过 ISA 总线访问 W83781D 来避免 SMBus 挂起的现象。
