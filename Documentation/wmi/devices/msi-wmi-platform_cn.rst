... 许可证标识符：GPL-2.0或更高版本

===================================================
MSI WMI 平台特性驱动（msi-wmi-platform）
===================================================

简介
============

许多微星笔记本电脑支持各种功能，如读取风扇传感器。这些功能由嵌入式控制器控制，ACPI固件在嵌入式控制器接口之上提供了一个标准的ACPI WMI接口。
WMI 接口描述
=========================

WMI 接口描述可以通过使用 `bmfdec <https://github.com/pali/bmfdec>`_ 工具解码嵌入的二进制MOF（bmof）数据：

::

  [WMI, Locale("MS\0x409"),
   Description("此类包含在其他类中使用的包定义"),
   guid("{ABBC0F60-8EA1-11d1-00A0-C90629100000}")]
  class Package {
    [WmiDataId(1), read, write, Description("16字节的数据")] uint8 Bytes[16];
  };

  [WMI, Locale("MS\0x409"),
   Description("此类包含在其他类中使用的包定义"),
   guid("{ABBC0F63-8EA1-11d1-00A0-C90629100000}")]
  class Package_32 {
    [WmiDataId(1), read, write, Description("32字节的数据")] uint8 Bytes[32];
  };

  [WMI, Dynamic, Provider("WmiProv"), Locale("MS\0x409"),
   Description("用于操作包方法的类"),
   guid("{ABBC0F6E-8EA1-11d1-00A0-C90629100000}")]
  class MSI_ACPI {
    [key, read] string InstanceName;
    [read] boolean Active;

    [WmiMethodId(1), Implemented, read, write, Description("返回包的内容")]
    void GetPackage([out, id(0)] Package Data);

    [WmiMethodId(2), Implemented, read, write, Description("设置包的内容")]
    void SetPackage([in, id(0)] Package Data);

    [WmiMethodId(3), Implemented, read, write, Description("返回包的内容")]
    void Get_EC([out, id(0)] Package_32 Data);

    [WmiMethodId(4), Implemented, read, write, Description("设置包的内容")]
    void Set_EC([in, id(0)] Package_32 Data);

    [WmiMethodId(5), Implemented, read, write, Description("返回包的内容")]
    void Get_BIOS([in, out, id(0)] Package_32 Data);

    [WmiMethodId(6), Implemented, read, write, Description("设置包的内容")]
    void Set_BIOS([in, out, id(0)] Package_32 Data);

    [WmiMethodId(7), Implemented, read, write, Description("返回包的内容")]
    void Get_SMBUS([in, out, id(0)] Package_32 Data);

    [WmiMethodId(8), Implemented, read, write, Description("设置包的内容")]
    void Set_SMBUS([in, out, id(0)] Package_32 Data);

    [WmiMethodId(9), Implemented, read, write, Description("返回包的内容")]
    void Get_MasterBattery([in, out, id(0)] Package_32 Data);

    [WmiMethodId(10), Implemented, read, write, Description("设置包的内容")]
    void Set_MasterBattery([in, out, id(0)] Package_32 Data);

    [WmiMethodId(11), Implemented, read, write, Description("返回包的内容")]
    void Get_SlaveBattery([in, out, id(0)] Package_32 Data);

    [WmiMethodId(12), Implemented, read, write, Description("设置包的内容")]
    void Set_SlaveBattery([in, out, id(0)] Package_32 Data);

    [WmiMethodId(13), Implemented, read, write, Description("返回包的内容")]
    void Get_Temperature([in, out, id(0)] Package_32 Data);

    [WmiMethodId(14), Implemented, read, write, Description("设置包的内容")]
    void Set_Temperature([in, out, id(0)] Package_32 Data);

    [WmiMethodId(15), Implemented, read, write, Description("返回包的内容")]
    void Get_Thermal([in, out, id(0)] Package_32 Data);

    [WmiMethodId(16), Implemented, read, write, Description("设置包的内容")]
    void Set_Thermal([in, out, id(0)] Package_32 Data);

    [WmiMethodId(17), Implemented, read, write, Description("返回包的内容")]
    void Get_Fan([in, out, id(0)] Package_32 Data);

    [WmiMethodId(18), Implemented, read, write, Description("设置包的内容")]
    void Set_Fan([in, out, id(0)] Package_32 Data);

    [WmiMethodId(19), Implemented, read, write, Description("返回包的内容")]
    void Get_Device([in, out, id(0)] Package_32 Data);

    [WmiMethodId(20), Implemented, read, write, Description("设置包的内容")]
    void Set_Device([in, out, id(0)] Package_32 Data);

    [WmiMethodId(21), Implemented, read, write, Description("返回包的内容")]
    void Get_Power([in, out, id(0)] Package_32 Data);

    [WmiMethodId(22), Implemented, read, write, Description("设置包的内容")]
    void Set_Power([in, out, id(0)] Package_32 Data);

    [WmiMethodId(23), Implemented, read, write, Description("返回包的内容")]
    void Get_Debug([in, out, id(0)] Package_32 Data);

    [WmiMethodId(24), Implemented, read, write, Description("设置包的内容")]
    void Set_Debug([in, out, id(0)] Package_32 Data);

    [WmiMethodId(25), Implemented, read, write, Description("返回包的内容")]
    void Get_AP([in, out, id(0)] Package_32 Data);

    [WmiMethodId(26), Implemented, read, write, Description("设置包的内容")]
    void Set_AP([in, out, id(0)] Package_32 Data);

    [WmiMethodId(27), Implemented, read, write, Description("返回包的内容")]
    void Get_Data([in, out, id(0)] Package_32 Data);

    [WmiMethodId(28), Implemented, read, write, Description("设置包的内容")]
    void Set_Data([in, out, id(0)] Package_32 Data);

    [WmiMethodId(29), Implemented, read, write, Description("返回包的内容")]
    void Get_WMI([out, id(0)] Package_32 Data);
  };

由于Windows处理`CreateByteField()` ACPI操作符时的一个特殊性（错误仅在访问无效字节字段时发生），所有方法都需要一个32字节的输入缓冲区，即使二进制MOF数据表明并非如此。
输入缓冲区包含一个字节以选择要访问的子功能和31个字节的输入数据，其含义取决于所访问的子功能。
输出缓冲区包含一个字节，用于指示成功或失败（失败时为`0x00`）和31个字节的输出数据，其含义取决于所访问的子功能。
WMI 方法 Get_EC()
-------------------

返回嵌入式控制器信息，所选子功能无关紧要。输出数据包含一个标志字节和一个28字节的控制器固件版本字符串。
标志字节的前4位包含嵌入式控制器接口的小版本号，接下来的2位包含嵌入式控制器接口的主要版本号。
第7位表示嵌入式控制器页面是否更改（确切含义未知），最后一位表示平台是否为Tigerlake平台。
MSI软件似乎仅在最后一位被设置时使用此接口。
WMI 方法 Get_Fan()
--------------------

通过选择子功能`0x00`可以访问风扇速度传感器。输出数据包含最多四个16位的大端格式风扇速度读数。大多数机器不支持全部四个风扇速度传感器，因此剩余的读数被硬编码为`0x0000`。
风扇转速可以通过以下公式计算：

        RPM = 480000 / <风扇速度读数>

如果风扇速度读数为零，则风扇RPM也为零。
WMI 方法 Get_WMI()
--------------------

返回 ACPI WMI 接口的版本，所选子功能无关紧要。
输出数据包含两个字节，第一个字节表示主版本号，最后一个字节表示次修订版号。
MSI 软件似乎仅在主版本号大于两时使用此接口。

对 MSI WMI 平台接口进行反向工程
=================================

.. warning:: 随意操作嵌入式控制器接口可能会对机器造成损坏并引发其他不良后果，请务必小心。
底层嵌入式控制器接口由 ``msi-ec`` 驱动程序使用，并且许多方法似乎只是将嵌入式控制器内存的一部分复制到输出缓冲区。
这意味着可以通过查看 ACPI AML 代码访问嵌入式控制器内存的哪一部分来反向工程剩余的 WMI 方法。该驱动还支持一个 debugfs 接口用于直接执行 WMI 方法。此外，通过加载带有 `force=true` 参数的模块可以禁用任何有关不支持硬件的安全检查。
关于 MSI 嵌入式控制器接口的更多信息可以在 `msi-ec 项目 <https://github.com/BeardOverflow/msi-ec>`_ 中找到。
特别感谢 github 用户 `glpnk` 展示了如何解码风扇速度读数。
