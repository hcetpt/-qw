.. SPDX-License-Identifier: GPL-2.0-or-later

============================================
戴尔 DDV WMI 接口驱动（dell-wmi-ddv）
============================================

介绍
============

许多 2020 年之后制造的戴尔笔记本电脑支持一种基于 WMI 的接口，用于检索各种系统数据，如电池温度、ePPID、诊断数据和风扇/热传感器数据。这个接口可能被 Windows 上的 `Dell Data Vault` 软件使用，因此被称为 `DDV`。目前，``dell-wmi-ddv`` 驱动支持该接口的版本 2 和 3，并且很容易添加对新接口版本的支持。
.. warning:: 戴尔将此接口视为内部接口，因此没有厂商提供的文档。所有知识都是通过试错获得的，请注意这一点。

戴尔 ePPID（电子零件识别码）
=================================

戴尔 ePPID 用于唯一标识戴尔机器中的组件，包括电池。它的形式类似于 `CC-PPPPPP-MMMMM-YMD-SSSS-FFF`，包含以下信息：

* 制造国代码（CC）
* 零件号，第一个字符为填充数字（PPPPPP）
* 制造商识别码（MMMMM）
* 制造年月日（YMD），以 36 进制表示，其中 Y 代表年份的最后一位
* 制造序列号（SSSS）
* 可选固件版本/修订号（FFF）

可以使用 `eppidtool <https://pypi.org/project/eppidtool>`_ Python 工具来解码并显示这些信息。
关于Dell ePPID的所有信息均通过Dell支持文档和此网站<https://telcontar.net/KBK/Dell/date_codes>收集。

WMI接口描述
=========================

使用`bmfdec <https://github.com/pali/bmfdec>`_工具可以从嵌入的二进制MOF（bmof）数据中解码WMI接口描述：

```
[WMI, Dynamic, Provider("WmiProv"), Locale("MS\\0x409"), Description("WMI Function"), guid("{8A42EA14-4F2A-FD45-6422-0087F7A7E608}")]
class DDVWmiMethodFunction {
   [key, read] string InstanceName;
   [read] boolean Active;

   [WmiMethodId(1), Implemented, read, write, Description("返回电池设计容量。")] void BatteryDesignCapacity([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(2), Implemented, read, write, Description("返回电池满电容量。")] void BatteryFullChargeCapacity([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(3), Implemented, read, write, Description("返回电池制造商名称。")] void BatteryManufactureName([in] uint32 arg2, [out] string argr);
   [WmiMethodId(4), Implemented, read, write, Description("返回电池制造日期。")] void BatteryManufactureDate([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(5), Implemented, read, write, Description("返回电池序列号。")] void BatterySerialNumber([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(6), Implemented, read, write, Description("返回电池化学成分值。")] void BatteryChemistryValue([in] uint32 arg2, [out] string argr);
   [WmiMethodId(7), Implemented, read, write, Description("返回电池温度。")] void BatteryTemperature([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(8), Implemented, read, write, Description("返回电池电流。")] void BatteryCurrent([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(9), Implemented, read, write, Description("返回电池电压。")] void BatteryVoltage([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(10), Implemented, read, write, Description("返回电池制造商访问码(MA代码)。")] void BatteryManufactureAceess([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(11), Implemented, read, write, Description("返回电池相对荷电状态。")] void BatteryRelativeStateOfCharge([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(12), Implemented, read, write, Description("返回电池循环次数。")] void BatteryCycleCount([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(13), Implemented, read, write, Description("返回电池ePPID。")] void BatteryePPID([in] uint32 arg2, [out] string argr);
   [WmiMethodId(14), Implemented, read, write, Description("返回电池原始分析开始。")] void BatteryeRawAnalyticsStart([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(15), Implemented, read, write, Description("返回电池原始分析。")] void BatteryeRawAnalytics([in] uint32 arg2, [out] uint32 RawSize, [out, WmiSizeIs("RawSize") : ToInstance] uint8 RawData[]);
   [WmiMethodId(16), Implemented, read, write, Description("返回电池设计电压。")] void BatteryDesignVoltage([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(17), Implemented, read, write, Description("返回电池原始分析A块。")] void BatteryeRawAnalyticsABlock([in] uint32 arg2, [out] uint32 RawSize, [out, WmiSizeIs("RawSize") : ToInstance] uint8 RawData[]);
   [WmiMethodId(18), Implemented, read, write, Description("返回版本。")] void ReturnVersion([in] uint32 arg2, [out] uint32 argr);
   [WmiMethodId(32), Implemented, read, write, Description("返回风扇传感器信息。")] void FanSensorInformation([in] uint32 arg2, [out] uint32 RawSize, [out, WmiSizeIs("RawSize") : ToInstance] uint8 RawData[]);
   [WmiMethodId(34), Implemented, read, write, Description("返回热传感器信息。")] void ThermalSensorInformation([in] uint32 arg2, [out] uint32 RawSize, [out, WmiSizeIs("RawSize") : ToInstance] uint8 RawData[]);
};

每个WMI方法接受一个包含32位索引的ACPI缓冲区作为输入参数，当使用与电池相关的WMI方法时，前8位用于指定电池。其他WMI方法可能会忽略此参数或以不同的方式解释它。WMI方法的输出格式各不相同：

- 如果函数只有一个输出，则返回相应类型的ACPI对象；
- 如果函数有多个输出，则返回一个包含按顺序排列输出的ACPI包。

输出格式应仔细检查，因为许多方法在出错时可能会返回格式错误的数据。
许多与电池相关的方法的数据格式似乎基于《智能电池数据规范》，因此未知的与电池相关的WMI方法很可能遵循该标准。

WMI方法 GetBatteryDesignCapacity()
-------------------------------------

返回电池的设计容量（mAh），类型为u16。

WMI方法 BatteryFullCharge()
------------------------------

返回电池的满电容量（mAh），类型为u16。

WMI方法 BatteryManufactureName()
-----------------------------------

返回电池制造商名称，ASCII字符串形式。

WMI方法 BatteryManufactureDate()
-----------------------------------

返回电池的制造日期，类型为u16。
日期编码如下：

- 位0到4表示制造日；
- 位5到8表示制造月；
- 位9到15表示制造年份（基准为1980）。
.. note::
   数据格式需要在更多机器上进行验证

WMI 方法 BatterySerialNumber()
------------------------------

返回电池的序列号，类型为 u16

WMI 方法 BatteryChemistryValue()
-------------------------------

返回电池的化学成分，类型为 ASCII 字符串
已知值包括：

- "Li-I" 表示锂离子电池

WMI 方法 BatteryTemperature()
-----------------------------

返回电池的温度，单位为十分之一开尔文，类型为 u16

WMI 方法 BatteryCurrent()
-------------------------

返回电池的电流，单位为毫安（mA），类型为 s16
负值表示放电状态

WMI 方法 BatteryVoltage()
-------------------------

返回电池的电压，单位为毫伏（mV），类型为 u16

WMI 方法 BatteryManufactureAccess()
-----------------------------------

返回制造商定义的值，类型为 u16

WMI 方法 BatteryRelativeStateOfCharge()
----------------------------------------

返回电池容量的百分比，类型为 u16

WMI 方法 BatteryCycleCount()
----------------------------

返回电池的循环次数，类型为 u16
WMI 方法 BatteryePPID()
-------------------------

返回电池的 ePPID，格式为 ASCII 字符串。

WMI 方法 BatteryeRawAnalyticsStart()
--------------------------------------

执行电池分析并返回一个状态码：

- ``0x0``：成功
- ``0x1``：不支持该接口
- ``0xfffffffe``：错误/超时

.. note::
   该方法的具体含义仍大多未知。

WMI 方法 BatteryeRawAnalytics()
---------------------------------

返回一个通常包含 12 块分析数据的缓冲区。
这些块包含：

- 从 0 开始的块编号（u8）
- 31 字节的未知数据

.. note::
   该方法的具体含义仍大多未知。

WMI 方法 BatteryDesignVoltage()
---------------------------------

返回电池的设计电压，单位为毫伏（mV），类型为 u16。

WMI 方法 BatteryeRawAnalyticsABlock()
---------------------------------------

返回一个单一的分析数据块，其中索引的第二个字节用于选择块编号。
*自 WMI 接口版本 3 起支持！*

.. note::
   该方法的具体含义仍大多未知。

WMI 方法 ReturnVersion()
--------------------------

返回 WMI 接口版本，类型为 u32。

WMI 方法 FanSensorInformation()
---------------------------------

返回一个包含风扇传感器条目的缓冲区，以单个 ``0xff`` 结束。
这些条目包含：

- 风扇类型（u8）
- 风扇转速（RPM，小端序 u16）

WMI 方法 ThermalSensorInformation()
-------------------------------------

返回一个包含温度传感器条目的缓冲区，以单个 ``0xff`` 结束。
这些条目包含：

- 热类型（u8）
- 当前温度（s8）
- 最低温度（s8）
- 最高温度（s8）
- 未知字段（u8）

.. note::
   待办事项：查明最后一个字节的意义

ACPI 电池匹配算法
=================

用于将 ACPI 电池与索引进行匹配的算法基于 OEM 软件日志消息中的信息。
基本上，对于每个新的 ACPI 电池，会比较索引 1 至 3 对应电池的序列号与该 ACPI 电池的序列号。
由于 ACPI 电池的序列号可以是普通整数或十六进制值的形式，因此需要检查这两种情况。然后选择第一个匹配序列号的索引。
序列号为 0 表示相应的索引未关联实际电池，或者关联的电池不存在。
某些机器（如戴尔 Inspiron 3505）仅支持单个电池，因此忽略电池索引。正因为如此，驱动程序依赖于 ACPI 电池钩子机制来发现电池。
.. note::
   目前驱动程序中使用的 ACPI 电池匹配算法已经过时，并不符合上述算法。原因在于 Linux 和 Windows 在处理 ToHexString() ACPI 操作码时存在差异，导致许多机器上的 ACPI 电池序列号出现偏差。在解决这个问题之前，驱动程序无法使用上述算法。

逆向工程 DDV WMI 接口
=====================

1. 找到一台受支持的戴尔笔记本电脑，通常是 2020 年以后制造的。
2. 导出 ACPI 表并搜索 WMI 设备（通常称为“ADDV”）。
3. 解码对应的 bmof 数据并查看 ASL 代码。
4. 通过将控制流与其他ACPI方法（例如与电池相关的_BIX或_BIF方法）进行比较，尝试推断某个WMI方法的含义。
5. 使用内置的UEFI诊断工具查看与风扇/温度相关的传感器类型和值（有时可以通过覆盖静态ACPI数据字段来测试不同的传感器类型值，因为在某些机器上这些数据在热重启后不会重新初始化）。

或者：

1. 加载`dell-wmi-ddv`驱动程序，必要时使用`force`模块参数。
2. 使用debugfs接口访问原始风扇/温度传感器缓冲数据。
3. 将这些数据与内置的UEFI诊断工具进行比较。

如果你的Dell笔记本电脑上的DDV WMI接口版本不受支持，或者你看到了未知的风扇/温度传感器，请在`bugzilla <https://bugzilla.kernel.org>`_ 上提交一个错误报告，以便将其添加到`dell-wmi-ddv`驱动程序中。
更多信息请参阅Documentation/admin-guide/reporting-issues.rst。
