=======================
内核驱动 i2c-piix4
=======================

支持的适配器：
  * Intel 82371AB PIIX4 和 PIIX4E
  * Intel 82443MX (440MX)
    数据手册：在Intel网站上公开可用
  * ServerWorks OSB4, CSB5, CSB6, HT-1000 和 HT-1100 南桥
    数据手册：仅通过ServerWorks的NDA获得
  * ATI IXP200, IXP300, IXP400, SB600, SB700 和 SB800 南桥
    数据手册：非公开可用
    SB700寄存器参考可在以下位置获取：
    http://support.amd.com/us/Embedded_TechDocs/43009_sb7xx_rrg_pub_1.00.pdf
  * AMD SP5100（SB700的衍生产品，用于某些服务器主板）
    数据手册：在AMD网站上公开可用
    http://support.amd.com/us/Embedded_TechDocs/44413.pdf
  * AMD Hudson-2, ML, CZ
    数据手册：非公开可用
  * Hygon CZ
    数据手册：非公开可用
  * 标准微系统公司（SMSC）SLC90E66 (Victory66) 南桥
    数据手册：在SMSC网站上公开可用 http://www.smsc.com

作者：
	- Frodo Looijaard <frodol@dds.nl>
	- Philip Edelbrock <phil@netroedge.com>

模块参数
-----------------

* force: int
  强制启用PIIX4。危险！
* force_addr: int
  在指定地址强制启用PIIX4。极其危险！

描述
-----------

PIIX4（正式名称为82371AB）是Intel的一个芯片，具有许多功能。它实现了PCI总线等功能。其中一个小功能是实现了一个系统管理总线。这是一个真正的SMBus - 您不能在I2C级别访问它。好消息是它原生理解SMBus命令，您不必担心定时问题。坏消息是连接到它的非SMBus设备可能会使其混乱。是的，这已知会发生...
运行`lspci -v`并查看是否包含如下条目：

  0000:00:02.3 Bridge: Intel Corp. 82371AB/EB/MB PIIX4 ACPI (rev 02)
	       标志: 中等devsel, IRQ 9

总线和设备编号可能不同，但功能编号必须相同（像许多PCI设备一样，PIIX4集成了多个不同的“功能”，这些可以被视为独立的设备）。如果找到这样的条目，则拥有一个PIIX4 SMBus控制器
在一些计算机上（最明显的是某些戴尔），SMBus默认被禁用。如果您使用insmod参数'force=1'，内核模块将尝试启用它。这是非常危险的！如果BIOS没有为此模块设置正确的地址，您可能会遇到大麻烦（读作：崩溃、数据损坏等）。请只在万不得已的情况下尝试这个（例如，首先尝试更新BIOS），并且先备份！一个更危险的选项是'force_addr=<IOPORT>'。这不仅会像'force'那样启用PIIX4，还会设置一个新的基本I / O端口地址。PIIX4的SMBus部分需要8个这样的地址才能正确运行。如果这些地址已被其他设备预留，您将会陷入大麻烦！除非您非常确定自己在做什么，否则不要使用此选项！

PIIX4E只是PIIX4的新版本；同样支持它
PIIX/PIIX3不实现SMBus或I2C总线，因此您不能在此类主板上使用此驱动程序
ServerWorks南桥、Intel 440MX和Victory66在I2C/SMBus支持方面与PIIX4完全相同
AMD SB700、SB800、SP5100和Hudson-2芯片组实现了两个兼容PIIX4的SMBus控制器。如果您的BIOS初始化了辅助控制器，此驱动程序会将其检测为"辅助SMBus主机控制器"
如果您拥有Force CPCI735主板或其他基于OSB4的系统，您可能需要更改SMBus中断选择寄存器，以便SMBus控制器使用SMI模式
1) 使用`lspci`命令并定位带有SMBus控制器的PCI设备：
   00:0f.0 ISA bridge: ServerWorks OSB4 South Bridge (rev 4f)
   对于不同芯片组，该行可能有所不同。请参阅驱动程序源代码以了解所有可能的PCI id（以及`lspci -n`来匹配它们）。假设设备位于00:0f.0
2) 现在只需更改0xD2寄存器中的值。首先使用命令获取它：`lspci -xxx -s 00:0f.0`
   如果值为0x3，则需要将其更改为0x1：
   `setpci  -s 00:0f.0 d2.b=1`

请注意，在所有情况下，您都不需要这样做，而是在SMBus无法正常工作时
硬件特定问题
------------------------

此驱动程序将在带有Intel PIIX4 SMBus的IBM系统上拒绝加载
这些机器中的一些具有连接到SMBus的RFID EEPROM（24RF08），由于状态机的错误，它很容易被损坏。这些主要是ThinkPad笔记本电脑，但台式机系统也可能受到影响。我们没有受影响系统的完整列表，因此唯一安全的解决办法是在所有IBM系统上（通过DMI数据检测）阻止对SMBus的访问。
