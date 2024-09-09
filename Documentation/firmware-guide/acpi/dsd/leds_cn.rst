SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

========================================
在 ACPI 中描述和引用 LED
========================================

单个 LED 通过设备节点下的分层数据扩展 [5] 节点进行描述，即 LED 驱动芯片。在特定于 LED 的节点中的 "reg" 属性指出了每个单独 LED 输出的数值 ID，这些输出与 LED 相连接。[leds] 这些分层数据节点命名为 "led@X"，其中 X 是 LED 输出的编号。
在设备树中引用 LED 的方法在 [video-interfaces] 的 "flash-leds" 属性文档中有详细说明。简而言之，LED 可以直接通过句柄（phandles）来引用。
虽然设备树允许引用树中的任何节点 [devicetree]，但在 ACPI 中引用仅限于设备节点 [acpi]。因此，在 ACPI 中使用相同的机制是不可能的。一种引用非设备 ACPI 节点的方法在 [data-node-ref] 中有详细说明。
ACPI 允许（与设备树类似）在引用之后使用整数参数。结合 LED 驱动设备的引用和一个整数参数（该参数指向相关 LED 的 "reg" 属性），可以用来识别单个 LED。"reg" 属性的值是固件和软件之间的约定，它唯一地标识了 LED 驱动的输出。
在 LED 驱动设备下，第一个分层数据扩展包列表条目应包含字符串 "led@"，其后跟 LED 编号，然后是被引用对象的名称。该对象应命名为 "LED" 后跟 LED 的编号。

示例
=======

下面是一个相机传感器设备和两个 LED 的 LED 驱动设备的 ASL 示例。无关的对象已被省略。 ::

	Device (LED)
	{
		Name (_DSD, Package () {
			ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
			Package () {
				Package () { "led@0", LED0 },
				Package () { "led@1", LED1 },
			}
		})
		Name (LED0, Package () {
			ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
			Package () {
				Package () { "reg", 0 },
				Package () { "flash-max-microamp", 1000000 },
				Package () { "flash-timeout-us", 200000 },
				Package () { "led-max-microamp", 100000 },
				Package () { "label", "white:flash" },
			}
		})
		Name (LED1, Package () {
			ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
			Package () {
				Package () { "reg", 1 },
				Package () { "led-max-microamp", 10000 },
				Package () { "label", "red:indicator" },
			}
		})
	}

	Device (SEN)
	{
		Name (_DSD, Package () {
			ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
			Package () {
				Package () {
					"flash-leds",
					Package () { ^LED, "led@0", ^LED, "led@1" },
				}
			}
		})
	}

其中
::

	LED	LED 驱动设备
	LED0	第一个 LED
	LED1	第二个 LED
	SEN	相机传感器设备（或 LED 关联的其他设备）

参考文献
==========

[acpi] 高级配置和电源接口规范
https://uefi.org/specifications/ACPI/6.4/，引用日期：2021-11-30
[data-node-ref] 文档/固件指南/ACPI/dsd/data-node-references.rst

[devicetree] 设备树。https://www.devicetree.org，引用日期：2019-02-21
[dsd-guide] DSD 指南
https://github.com/UEFI/DSD-Guide/blob/main/dsd-guide.adoc，引用日期：2021-11-30
当然，可以将这些路径翻译成中文：

- `[leds] Documentation/devicetree/bindings/leds/common.yaml`
  - [LEDs] 文档/devicetree/绑定/leds/common.yaml

- `[video-interfaces] Documentation/devicetree/bindings/media/video-interfaces.yaml`
  - [视频接口] 文档/devicetree/绑定/media/视频接口.yaml

如果你有其他需要翻译的内容或进一步的问题，请告诉我！
