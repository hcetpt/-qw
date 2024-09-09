SPDX 许可声明标识符: GPL-2.0

====================
ACPI CA 调试输出
====================

ACPI CA 可以生成调试输出。本文档描述了如何使用此功能。

编译时配置
==========================

ACPI CA 的调试输出由 CONFIG_ACPI_DEBUG 全局启用。如果未设置此配置选项，则调试消息甚至不会被编译进内核中。

启动和运行时配置
=================================

当 CONFIG_ACPI_DEBUG 设置为 y 时，您可以选择感兴趣的组件和消息级别。在启动时，可以使用 acpi.debug_layer 和 acpi.debug_level 内核命令行选项。启动后，您可以使用 /sys/module/acpi/parameters/ 目录下的 debug_layer 和 debug_level 文件来控制调试消息。

debug_layer（组件）
=======================

“debug_layer” 是一个掩码，用于选择感兴趣的组件，例如，ACPI 解释器的特定部分。要构建 debug_layer 掩码，请查找 ACPI 源文件中的 “#define _COMPONENT”。

您可以在启动时使用 acpi.debug_layer 命令行参数设置 debug_layer 掩码，并且可以在启动后通过写入 /sys/module/acpi/parameters/debug_layer 来更改它。

可能的组件定义在 include/acpi/acoutput.h 中。

读取 /sys/module/acpi/parameters/debug_layer 可以显示支持的掩码值：

```
ACPI_UTILITIES                  0x00000001
ACPI_HARDWARE                   0x00000002
ACPI_EVENTS                     0x00000004
ACPI_TABLES                     0x00000008
ACPI_NAMESPACE                  0x00000010
ACPI_PARSER                     0x00000020
ACPI_DISPATCHER                 0x00000040
ACPI_EXECUTER                   0x00000080
ACPI_RESOURCES                  0x00000100
ACPI_CA_DEBUGGER                0x00000200
ACPI_OS_SERVICES                0x00000400
ACPI_CA_DISASSEMBLER            0x00000800
ACPI_COMPILER                   0x00001000
ACPI_TOOLS                      0x00002000
```

debug_level
===========

“debug_level” 是一个掩码，用于选择不同类型的消息，例如与初始化、方法执行、信息性消息等相关的消息。

要构建 debug_level，请查看 ACPI_DEBUG_PRINT() 语句中指定的级别。

ACPI 解释器使用多个不同的级别，但 Linux ACPI 核心和 ACPI 驱动程序通常只使用 ACPI_LV_INFO。

您可以在启动时使用 acpi.debug_level 命令行参数设置 debug_level 掩码，并且可以在启动后通过写入 /sys/module/acpi/parameters/debug_level 来更改它。
可能的级别定义在 `include/acpi/acoutput.h` 中。通过读取 `/sys/module/acpi/parameters/debug_level` 可以查看支持的掩码值，目前这些掩码值如下：

    ACPI_LV_INIT                    0x00000001
    ACPI_LV_DEBUG_OBJECT            0x00000002
    ACPI_LV_INFO                    0x00000004
    ACPI_LV_INIT_NAMES              0x00000020
    ACPI_LV_PARSE                   0x00000040
    ACPI_LV_LOAD                    0x00000080
    ACPI_LV_DISPATCH                0x00000100
    ACPI_LV_EXEC                    0x00000200
    ACPI_LV_NAMES                   0x00000400
    ACPI_LV_OPREGION                0x00000800
    ACPI_LV_BFIELD                  0x00001000
    ACPI_LV_TABLES                  0x00002000
    ACPI_LV_VALUES                  0x00004000
    ACPI_LV_OBJECTS                 0x00008000
    ACPI_LV_RESOURCES               0x00010000
    ACPI_LV_USER_REQUESTS           0x00020000
    ACPI_LV_PACKAGE                 0x00040000
    ACPI_LV_ALLOCATIONS             0x00100000
    ACPI_LV_FUNCTIONS               0x00200000
    ACPI_LV_OPTIMIZATIONS           0x00400000
    ACPI_LV_MUTEX                   0x01000000
    ACPI_LV_THREADS                 0x02000000
    ACPI_LV_IO                      0x04000000
    ACPI_LV_INTERRUPTS              0x08000000
    ACPI_LV_AML_DISASSEMBLE         0x10000000
    ACPI_LV_VERBOSE_INFO            0x20000000
    ACPI_LV_FULL_TABLES             0x40000000
    ACPI_LV_EVENTS                  0x80000000

### 示例

例如，在 `drivers/acpi/acpica/evxfevnt.c` 文件中有以下内容：

    #define _COMPONENT          ACPI_EVENTS
    ...
    ACPI_DEBUG_PRINT((ACPI_DB_INIT, "ACPI mode disabled\n"));

要启用这条消息，需要设置 `acpi.debug_layer` 的 `ACPI_EVENTS` 位以及 `acpi.debug_level` 的 `ACPI_LV_INIT` 位。（`ACPI_DEBUG_PRINT` 语句使用 `ACPI_DB_INIT`，这是一个基于 `ACPI_LV_INIT` 定义的宏。）

### 启用示例

在启动时启用所有 AML “调试” 输出（在解释 AML 时写入到调试对象）：

    acpi.debug_layer=0xffffffff acpi.debug_level=0x2

启用所有与 ACPI 硬件相关的消息：

    acpi.debug_layer=0x2 acpi.debug_level=0xffffffff

在启动后启用所有 `ACPI_DB_INFO` 消息：

    # echo 0x4 > /sys/module/acpi/parameters/debug_level

显示所有有效的组件值：

    # cat /sys/module/acpi/parameters/debug_layer
