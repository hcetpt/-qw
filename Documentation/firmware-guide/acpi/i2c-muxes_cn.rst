.. SPDX-License-Identifier: GPL-2.0

==============
ACPI I2C 多路复用器
==============

描述包含 I2C 多路复用器的 I2C 设备层次结构需要每个多路复用器通道有一个 ACPI Device () 范围。
考虑以下拓扑结构：

    +------+   +------+
    | SMB1 |-->| MUX0 |--CH00--> I2C 客户端 A (0x50)
    |      |   | 0x70 |--CH01--> I2C 客户端 B (0x50)
    +------+   +------+

这对应于以下 ASL（ACPI 标准定义语言）代码：

    Device (SMB1)
    {
        Name (_HID, ...)
        Device (MUX0)
        {
            Name (_HID, ...)
            Name (_CRS, ResourceTemplate () {
                I2cSerialBus (0x70, ControllerInitiated, I2C_SPEED,
                            AddressingMode7Bit, "^SMB1", 0x00,
                            ResourceConsumer,,)
            }

            Device (CH00)
            {
                Name (_ADR, 0)

                Device (CLIA)
                {
                    Name (_HID, ...)
                    Name (_CRS, ResourceTemplate () {
                        I2cSerialBus (0x50, ControllerInitiated, I2C_SPEED,
                                    AddressingMode7Bit, "^CH00", 0x00,
                                    ResourceConsumer,,)
                    }
                }
            }

            Device (CH01)
            {
                Name (_ADR, 1)

                Device (CLIB)
                {
                    Name (_HID, ...)
                    Name (_CRS, ResourceTemplate () {
                        I2cSerialBus (0x50, ControllerInitiated, I2C_SPEED,
                                    AddressingMode7Bit, "^CH01", 0x00,
                                    ResourceConsumer,,)
                    }
                }
            }
        }
    }
