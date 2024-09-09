... SPDX 许可证标识符: GPL-2.0

=========================
ACPI 中的 MDIO 总线和 PHY
=========================

MDIO 总线上的 PHY [phy] 通过 fwnode_mdiobus_register_phy() 探测并注册。
之后，为了将这些 PHY 连接到各自的 MAC 上，必须引用在 MDIO 总线上注册的 PHY。
本文档引入了两个_DSD 属性，用于将 MDIO 总线上的 PHY [dsd-properties-rules] 连接到 MAC 层。
这些属性根据 "Device Properties UUID For _DSD" [dsd-guide] 文档定义，并且包含这些属性的设备数据描述符中必须使用 daffd814-6eba-4d8c-8a91-bc9bbf4aa301 UUID。

phy-handle
----------
对于每个 MAC 节点，使用设备属性 "phy-handle" 来引用在 MDIO 总线上注册的 PHY。这在网络接口通过 MDIO 总线连接 PHY 到 MAC 时是强制性的。
在 MDIO 总线驱动程序初始化期间，使用 _ADR 对象探测此总线上的 PHY 并将其注册到 MDIO 总线上，如下所示：
```none
      Scope(\_SB.MDI0)
      {
        Device(PHY1) {
          Name (_ADR, 0x1)
        } // end of PHY1

        Device(PHY2) {
          Name (_ADR, 0x2)
        } // end of PHY2
      }
```
在 MAC 驱动程序初始化期间，需要从 MDIO 总线上检索已注册的 PHY 设备。为此，MAC 驱动程序需要引用之前注册的 PHY，这些引用作为设备对象（例如 \_SB.MDI0.PHY1）提供。

phy-mode
--------
"phy-mode" _DSD 属性用于描述与 PHY 的连接方式。"phy-mode" 的有效值定义在 [ethernet-controller] 中。

managed
-------
可选属性，指定 PHY 管理类型。"managed" 的有效值定义在 [ethernet-controller] 中。
固定链接（fixed-link）

“固定链接”由MAC端口的数据子节点描述，该子节点通过层次数据扩展链接到_DSD包中（UUID为dbb8e3e6-5886-4ba6-8795-1319f52a966b，遵循[dsd-guide] "_DSD实现指南"文档）。该子节点应包含一个必需的属性（"speed"）和可能的可选属性——参数列表及其值在[ethernet-controller]中有详细说明。以下ASL示例说明了这些属性的使用方法。

MDIO节点的DSDT条目
------------------------

MDIO总线有一个SoC组件（MDIO控制器）和一个平台组件（MDIO总线上的PHY设备）。

a) 硅组件
此节点描述了MDIO控制器MDI0。
---------------------------------------------

```none
Scope(_SB)
{
  Device(MDI0) {
    Name(_HID, "NXP0006")
    Name(_CCA, 1)
    Name(_UID, 0)
    Name(_CRS, ResourceTemplate() {
      Memory32Fixed(ReadWrite, MDI0_BASE, MDI_LEN)
      Interrupt(ResourceConsumer, Level, ActiveHigh, Shared)
      {
        MDI0_IT
      }
    }) // end of _CRS for MDI0
  } // end of MDI0
}
```

b) 平台组件
PHY1和PHY2节点表示连接到MDIO总线MDI0上的PHY设备。
---------------------------------------------------------------------

```none
Scope(\_SB.MDI0)
{
  Device(PHY1) {
    Name (_ADR, 0x1)
  } // end of PHY1

  Device(PHY2) {
    Name (_ADR, 0x2)
  } // end of PHY2
}
```

表示MAC节点的DSDT条目
-----------------------------------

以下是引用PHY节点的MAC节点。
phy-mode和phy-handle如前所述。
------------------------------------------------------

```none
Scope(\_SB.MCE0.PR17)
{
  Name (_DSD, Package () {
     ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
     Package () {
         Package (2) {"phy-mode", "rgmii-id"},
         Package (2) {"phy-handle", \_SB.MDI0.PHY1}
     }
  })
}

Scope(\_SB.MCE0.PR18)
{
  Name (_DSD, Package () {
    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
    Package () {
        Package (2) {"phy-mode", "rgmii-id"},
        Package (2) {"phy-handle", \_SB.MDI0.PHY2}}
    }
  })
}
```

指定"managed"属性的MAC节点示例
-------------------------------------------------------

```none
Scope(\_SB.PP21.ETH0)
{
  Name (_DSD, Package () {
     ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
     Package () {
         Package () {"phy-mode", "sgmii"},
         Package () {"managed", "in-band-status"}
     }
  })
}
```

具有“fixed-link”子节点的MAC节点示例
---------------------------------------------

```none
Scope(\_SB.PP21.ETH1)
{
  Name (_DSD, Package () {
    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
    Package () {"phy-mode", "sgmii"},
    ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
    Package () {"fixed-link", "LNK0"}
  })
  Name (LNK0, Package(){ // 数据子节点
    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
    Package () {
        Package () {"speed", 1000},
        Package () {"full-duplex", 1}
    }
  })
}
```

参考文献
==========

[phy] 文档/networking/phy.rst

[dsd-properties-rules] 文档/firmware-guide/acpi/DSD-properties-rules.rst

[ethernet-controller] 文档/devicetree/bindings/net/ethernet-controller.yaml

[dsd-guide] DSD指南 https://github.com/UEFI/DSD-Guide/blob/main/dsd-guide.adoc，参考日期：2021-11-30
当然，请提供您需要翻译的文本。
