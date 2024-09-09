.. SPDX-License-Identifier: GPL-2.0
.. include:: <isonum.txt>

===================================
引用层次数据节点
===================================

:版权所有: |copy| 2018, 2021 Intel 公司
:作者: Sakari Ailus <sakari.ailus@linux.intel.com>

ACPI 通常只允许在树中引用设备对象。
层次数据扩展节点不能直接引用，因此本文档定义了一种实现此类引用的方案。
一个引用由设备对象名称后跟一个或多个层次数据扩展 [dsd-guide] 键组成。具体来说，被键引用的层次数据扩展节点应当直接位于父对象下，即设备对象或其他层次数据扩展节点。
层次数据节点中的键应包含节点名称、“@”字符和节点编号的十六进制表示（不含前缀或后缀）。相同的 ACPI 对象应包含带有“reg”属性的 _DSD 属性扩展，该属性的数值应与节点编号相同。
如果层次数据扩展节点没有数值，则应省略 ACPI 对象的 _DSD 属性中的“reg”属性，并从层次数据扩展键中省略“@”字符和编号。

示例
=======

在下面的 ASL 代码片段中，“reference”_DSD 属性包含对设备对象 DEV0 的引用，在该设备对象下有一个层次数据扩展键 “node@1”，引用 NOD1 对象；最后还有一个层次数据扩展键 “anothernode”，引用 ANOD 对象，这也是引用的最终目标节点。
::

	Device (DEV0)
	{
	    Name (_DSD, Package () {
		ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
		Package () {
		    Package () { "node@0", "NOD0" },
		    Package () { "node@1", "NOD1" },
		}
	    })
	    Name (NOD0, Package() {
		ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
		Package () {
		    Package () { "reg", 0 },
		    Package () { "random-property", 3 },
		}
	    })
	    Name (NOD1, Package() {
		ToUUID("dbb8e3e6-5886-4ba6-8795-1319f52a966b"),
		Package () {
		    Package () { "reg", 1 },
		    Package () { "anothernode", "ANOD" },
		}
	    })
	    Name (ANOD, Package() {
		ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
		Package () {
		    Package () { "random-property", 0 },
		}
	    })
	}

	Device (DEV1)
	{
	    Name (_DSD, Package () {
		ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
		Package () {
		    Package () {
			"reference", Package () {
			    ^DEV0, "node@1", "anothernode"
			}
		    },
		}
	    })
	}

请参阅 Documentation/firmware-guide/acpi/dsd/graph.rst 中的图形示例。

参考文献
==========

[dsd-guide] DSD 指南
https://github.com/UEFI/DSD-Guide/blob/main/dsd-guide.adoc，参考日期：2021-11-30
