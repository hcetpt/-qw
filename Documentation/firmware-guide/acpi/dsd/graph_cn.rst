SPDX 许可证标识符: GPL-2.0

======
图表
======

_DSD
====

_DSD（设备特定数据）[dsd-guide] 是一个预定义的 ACPI 设备配置对象，可以用来传达未被 ACPI 规范 [acpi] 明确覆盖的硬件特性信息。有两个与图表相关的 _DSD 扩展：属性 [dsd-guide] 和分层数据扩展。属性扩展提供了通用的键值对，而分层数据扩展支持带有对其他节点引用的节点，形成一棵树。树中的节点可能包含由属性扩展定义的属性。这两种扩展共同提供了一个树状结构，在树的每个节点中可以有零个或多个属性（键值对）。

该数据结构可以在运行时通过使用在 include/linux/fwnode.h 中定义的 device_* 和 fwnode_* 函数访问。Fwnode 代表一个通用的固件节点对象。它独立于固件类型。在 ACPI 中，fwnode 是 _DSD 分层数据扩展对象。设备的 _DSD 对象由一个 fwnode 表示。

该数据结构可以通过在 ACPI 表格中使用对设备本身的硬引用和每个深度上分层数据扩展数组的索引来引用。
端口和端点
===================

端口和端点的概念与 Devicetree [devicetree, graph-bindings] 中的概念非常相似。端口表示设备中的一个接口，而端点表示与此接口的连接。更多关于通用数据节点引用的信息请参见 [data-node-ref]。

所有端口节点都位于设备的 "_DSD" 节点下的分层数据扩展树中。与每个端口节点相关的数据扩展必须以 "port" 开头，并且必须跟随 "@" 字符和端口号作为其键。它所指向的目标对象应命名为 "PRTX"，其中 "X" 是端口号。例如：

```acpi
Package() { "port@4", "PRT4" }
```

进一步地，端点位于端口节点下。端点节点的分层数据扩展键必须以 "endpoint" 开头，并且必须跟随 "@" 字符和端点号。它所指向的对象应命名为 "EPXY"，其中 "X" 是端口号，"Y" 是端点号。例如：

```acpi
Package() { "endpoint@0", "EP40" }
```

每个端口节点包含一个属性扩展键 "port"，其值是端口号。每个端点同样用属性扩展键 "reg" 编号，其值是端点号。端口号必须在设备内唯一，端点号必须在一个端口内唯一。如果一个设备对象只有一个端口，则该端口的编号应为零。类似地，如果一个端口只有一个端点，则该端点的编号应为零。

端点引用使用属性扩展，其名称为 "remote-endpoint" 并且在同一个包中有引用。此类引用包括远程设备引用、设备下的端口数据扩展的第一个包条目以及端口下的端点数据扩展的第一个包条目。单个引用如下所示：

```acpi
Package() { device, "port@X", "endpoint@Y" }
```

在上述示例中，"X" 是端口号，"Y" 是端点号。

对端点的引用必须始终双向进行，既要到远程端点，也要从被引用的远程端点节点返回。

下面是一个简单的示例：

```acpi
Scope (\_SB.PCI0.I2C2)
{
    Device (CAM0)
    {
        Name (_DSD, Package () {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "compatible", Package () { "nokia,smia" } },
            },
            ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
            Package () {
                Package () { "port@0", "PRT0" },
            }
        })
        Name (PRT0, Package() {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "reg", 0 },
            },
            ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
            Package () {
                Package () { "endpoint@0", "EP00" },
            }
        })
        Name (EP00, Package() {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "reg", 0 },
                Package () { "remote-endpoint", Package() { \_SB.PCI0.ISP, "port@4", "endpoint@0" } },
            }
        })
    }
}

Scope (\_SB.PCI0)
{
    Device (ISP)
    {
        Name (_DSD, Package () {
            ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
            Package () {
                Package () { "port@4", "PRT4" },
            }
        })

        Name (PRT4, Package() {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "reg", 4 }, /* CSI-2 端口号 */
            },
            ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
            Package () {
                Package () { "endpoint@0", "EP40" },
            }
        })

        Name (EP40, Package() {
            ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
            Package () {
                Package () { "reg", 0 },
                Package () { "remote-endpoint", Package () { \_SB.PCI0.I2C2.CAM0, "port@0", "endpoint@0" } },
            }
        })
    }
}
```

这里，“CAM0” 设备的端口 0 连接到 “ISP” 设备的端口 4 反之亦然。
参考文献
==========

[acpi] 高级配置和电源接口规范
以下是你提供的内容的中文翻译：

[acpi-specification] UEFI官方网站上的ACPI规范6.4版，参考日期：2021年11月30日
[data-node-ref] 文档/firmware-guide/acpi/dsd/data-node-references.rst

[devicetree] 设备树（Devicetree）官网：https://www.devicetree.org，参考日期：2016年10月3日
[dsd-guide] DSD指南
https://github.com/UEFI/DSD-Guide/blob/main/dsd-guide.adoc，参考日期：2021年11月30日
[dsd-rules] _DSD设备属性使用规则 文档/firmware-guide/acpi/DSD-properties-rules.rst

[graph-bindings] 设备图（Devicetree）的通用绑定
https://github.com/devicetree-org/dt-schema/blob/main/schemas/graph.yaml，参考日期：2021年11月30日

如果你需要进一步的帮助或有其他问题，请告诉我！
