SPDX 许可证标识符: GPL-2.0

========================================
在非 0 的 D 状态下探测设备
========================================

介绍
============

在某些情况下，可能希望在整个系统启动过程中让某些设备保持关闭状态，如果开启这些设备会产生除设备本身供电之外的不良影响。

工作原理
============

_DSC（配置设备状态）对象可以计算为一个整数，用于告诉 Linux 在探测过程中设备允许的最高 D 状态。如果总线驱动程序通常将设备设置为 D0 状态进行探测，则对 _DSC 的支持需要内核总线类型的相应支持。
使用 _DSC 的缺点是，由于设备未被供电，即使设备有问题，驱动程序也可能顺利探测，但第一个用户会发现设备无法工作，而不是在探测时失败。因此，此功能应谨慎使用。

I²C
---

如果 I²C 驱动程序通过在 struct i2c_driver.flags 字段中设置 I2C_DRV_ACPI_WAIVE_D0_PROBE 标志，并且 _DSC 对象计算出的整数值高于设备当前的 D 状态，则该设备不会在探测时被供电（即不会被置于 D0 状态）。

D 状态
--------

D 状态及其允许的 _DSC 值如下所示。有关设备电源状态的更多信息，请参阅 [1]。
.. code-block:: text

    编号    状态        描述
    0       D0      设备完全供电
    1       D1
    2       D2
    3       D3hot
    4       D3cold  关闭

参考文献
==========

[1] https://uefi.org/specifications/ACPI/6.4/02_Definition_of_Terms/Definition_of_Terms.html#device-power-state-definitions

示例
=======

以下是一个描述使用 _DSC 对象告知操作系统在探测过程中设备应保持关闭状态的 ACPI 设备的 ASL 示例。已省略了一些与示例无关的对象。
.. code-block:: text

    Device (CAM0)
    {
        Name (_HID, "SONY319A")
        Name (_UID, Zero)
        Name (_CRS, ResourceTemplate ()
        {
            I2cSerialBus(0x0020, ControllerInitiated, 0x00061A80,
                         AddressingMode7Bit, "\\_SB.PCI0.I2C0",
                         0x00, ResourceConsumer)
        })
        Method (_DSC, 0, NotSerialized)
        {
            Return (0x4)
        }
    }
