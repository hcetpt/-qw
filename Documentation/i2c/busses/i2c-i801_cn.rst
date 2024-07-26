======================
内核驱动 i2c-i801
======================

支持的适配器：
  * Intel 82801AA 和 82801AB (ICH 和 ICH0 —— 是‘810’和‘810E’芯片组的一部分)
  * Intel 82801BA (ICH2 —— 是‘815E’芯片组的一部分)
  * Intel 82801CA/CAM (ICH3)
  * Intel 82801DB (ICH4) (支持硬件PEC)
  * Intel 82801EB/ER (ICH5) (支持硬件PEC)
  * Intel 6300ESB
  * Intel 82801FB/FR/FW/FRW (ICH6)
  * Intel 82801G (ICH7)
  * Intel 631xESB/632xESB (ESB2)
  * Intel 82801H (ICH8)
  * Intel 82801I (ICH9)
  * Intel EP80579 (Tolapai)
  * Intel 82801JI (ICH10)
  * Intel 5/3400 系列 (PCH)
  * Intel 6 系列 (PCH)
  * Intel Patsburg (PCH)
  * Intel DH89xxCC (PCH)
  * Intel Panther Point (PCH)
  * Intel Lynx Point (PCH)
  * Intel Avoton (SOC)
  * Intel Wellsburg (PCH)
  * Intel Coleto Creek (PCH)
  * Intel Wildcat Point (PCH)
  * Intel BayTrail (SOC)
  * Intel Braswell (SOC)
  * Intel Sunrise Point (PCH)
  * Intel Kaby Lake (PCH)
  * Intel DNV (SOC)
  * Intel Broxton (SOC)
  * Intel Lewisburg (PCH)
  * Intel Gemini Lake (SOC)
  * Intel Cannon Lake (PCH)
  * Intel Cedar Fork (PCH)
  * Intel Ice Lake (PCH)
  * Intel Comet Lake (PCH)
  * Intel Elkhart Lake (PCH)
  * Intel Tiger Lake (PCH)
  * Intel Jasper Lake (SOC)
  * Intel Emmitsburg (PCH)
  * Intel Alder Lake (PCH)
  * Intel Raptor Lake (PCH)
  * Intel Meteor Lake (SOC 和 PCH)
  * Intel Birch Stream (SOC)

数据手册：在英特尔网站上公开可用。

在Intel Patsburg及以后的芯片组中，既支持常规的主机SMBus控制器，也支持额外的“集成设备功能”控制器。
作者：
	- Mark Studebaker <mdsxyz123@yahoo.com>
	- Jean Delvare <jdelvare@suse.de>

模块参数
--------

* disable_features (位向量)

禁用设备通常支持的选定功能。这使得可以解决可能存在的驱动或硬件错误，如果特定的功能不能按预期工作。位值：

 ====  =========================================
 0x01  禁用SMBus PEC
 0x02  禁用块缓冲区
 0x08  禁用I2C块读功能
 0x10  不使用中断
 0x20  禁用SMBus 主机通知
 ====  =========================================

描述
---

ICH（正式名称为82801AA）、ICH0（82801AB）、ICH2（82801BA）、ICH3（82801CA/CAM）以及后来的设备（PCH）是英特尔芯片，是用于基于赛扬PC的英特尔‘810’芯片组、基于奔腾PC的‘810E’芯片组、‘815E’芯片组等的一部分。
ICH芯片至少包含在两个逻辑PCI设备中的七个独立的PCI功能。lspci的输出将显示如下内容：

  00:1e.0 PCI桥接器: Intel Corporation: 未知设备 2418 (rev 01)
  00:1f.0 ISA桥接器: Intel Corporation: 未知设备 2410 (rev 01)
  00:1f.1 IDE接口: Intel Corporation: 未知设备 2411 (rev 01)
  00:1f.2 USB控制器: Intel Corporation: 未知设备 2412 (rev 01)
  00:1f.3 未知类[0c05]: Intel Corporation: 未知设备 2413 (rev 01)

SMBus控制器是设备1f中的功能3。类0c05是SMBus串行控制器。
ICH芯片与英特尔的PIIX4芯片非常相似，至少在SMBus控制器方面是如此。
过程调用支持
--------------------

从82801EB (ICH5)及其后续芯片开始支持块过程调用。
I2C块读支持
----------------------

从82801EB (ICH5)及其后续芯片开始支持I2C块读。
SMBus 2.0支持
-----------------

从82801DB (ICH4)及其后续芯片开始支持几个SMBus 2.0特性。
中断支持
-----------------

从82801EB (ICH5)及其后续芯片开始支持PCI中断。
隐藏的ICH SMBus
----------------

如果你的系统有Intel ICH南桥，但你在lspci中看不到00:1f.3处的SMBus设备，并且你无法在BIOS中找到任何启用它的方法，这意味着它已被BIOS代码隐藏了。华硕在其P4B主板上首先这样做了，并在之后的许多其他主板上也采用了这种方式。一些厂商机器也受到影响。
首先尝试的是“i2c-scmi”ACPI驱动。可能是SMBus被故意隐藏是因为它将由ACPI驱动。如果i2c-scmi驱动对你有用，那就忘记i2c-i801驱动，并不要试图解开隐藏的ICH SMBus。即使i2c-scmi不起作用，你也最好确保SMBus没有被ACPI代码使用。尝试加载“fan”和“thermal”驱动程序，并检查/sys/class/thermal。如果你发现一个类型为“acpitz”的热区，那么很可能ACPI正在访问SMBus，不揭开隐藏更安全。只有当你确定ACPI没有使用SMBus时，你才能尝试解开隐藏。
为了显示SMBus，我们需要在内核枚举PCI设备之前更改一个PCI寄存器的值。这在`drivers/pci/quirks.c`中完成，所有受影响的主板都必须在此列出（参见函数asus_hides_smbus_hostbridge）。如果SMBus设备缺失，并且你认为SMBus上有一些有趣的东西（例如硬件监控芯片），你需要将你的主板添加到列表中。  
主板是通过主机桥接器PCI设备的子供应商和子设备ID来识别的。使用`lspci -n -v -s 00:00.0`获取这些ID：

  00:00.0 类别 0600: 8086:2570 (rev 02)
          子系统: 1043:80f2
          标志: 总线主控, 快速设备选择, 延迟 0
          内存在fc000000 (32位, 可预取) [大小=32M]
          功能: [e4] #09 [2106]
          功能: [a0] AGP版本 3.0

这里主机桥接器ID为2570（82865G/PE/P），子供应商ID为1043（Asus），子设备ID为80f2（P4P800-X）。你可以在`include/linux/pci_ids.h`找到桥接器ID和子供应商ID的符号名称，然后在`drivers/pci/quirks.c`中适当的位置为你的子设备ID添加一个情况。然后请进行充分的测试以确保显示的SMBus不会与例如ACPI冲突。
如果它工作正常，证明是有用的（即SMBus上有可用的芯片）并且看起来是安全的，请提交补丁以便合并到内核。

注意：从lm_sensors 2.10.2及更高版本开始，有一个非常有用的脚本，名为`unhide_ICH_SMBus`（位于prog/hotplug目录下），该脚本使用fakephp驱动程序临时显示SMBus，而无需修补和重新编译内核。如果你只是想检查隐藏的ICH SMBus上是否有有趣的东西，这是非常方便的。

--------------------------------------------------------------------------------
lm_sensors项目衷心感谢得克萨斯仪器公司在开发此驱动程序初期提供的支持。
lm_sensors项目衷心感谢英特尔公司在开发此驱动程序的SMBus 2.0 / ICH4特性方面提供的支持。
