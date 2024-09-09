```spdx
SPDX 许可声明标识符: GPL-2.0

=====================
Intel 北端 Mux-Agent
=====================

介绍
============

北端 Mux-Agent 是 Intel PMC 固件的一个功能，支持大多数带有 PMC 微控制器的基于 Intel 的平台。它用于配置系统上的各种 USB 多路复用器/解复用器。允许从操作系统配置 mux-agent 的平台具有一个表示它的 ACPI 设备对象（节点），其 HID 为 "INTC105C"。北端 Mux-Agent（也称为 Intel PMC Mux 控制或简称 mux-agent）驱动程序通过使用 PMC IPC 方法（drivers/platform/x86/intel_scu_ipc.c）与 PMC 微控制器通信。该驱动程序注册了 USB Type-C 复用器类，使得 USB Type-C 控制器和接口驱动程序能够配置电缆插头方向和模式（带交替模式）。此外，该驱动程序还注册了 USB 角色类以支持 USB 主机和设备模式。该驱动程序位于此目录：drivers/usb/typec/mux/intel_pmc_mux.c

端口节点
==========

一般
-------

对于系统上每个由 mux-agent 控制的 USB Type-C 连接器，都有一个独立的子节点位于 PMC mux-agent 设备节点下。这些节点并不表示实际的连接器，而是表示与连接器相关的 mux-agent 中的“通道”：

	Scope (_SB.PCI0.PMC.MUX)
	{
	    Device (CH0)
	    {
		Name (_ADR, 0)
	    }

	    Device (CH1)
	    {
		Name (_ADR, 1)
	    }
	}

_PLD（设备物理位置）
----------------------------------

可选的 _PLD 对象可以与端口（通道）节点一起使用。如果提供了 _PLD，则应与连接器节点的 _PLD 匹配：

	Scope (_SB.PCI0.PMC.MUX)
	{
	    Device (CH0)
	    {
		Name (_ADR, 0)
	        Method (_PLD, 0, NotSerialized)
                {
		    /* 考虑这为伪代码。 */
		    Return (\_SB.USBC.CON0._PLD())
		}
	    }
	}

Mux-agent 特定的 _DSD 设备属性
-----------------------------------------

端口号
~~~~~~~~~~~~

为了配置 USB Type-C 连接器后面的复用器，PMC 固件需要知道与连接器关联的 USB2 端口和 USB3 端口。驱动程序通过读取特定的 _DSD 设备属性 “usb2-port-number” 和 “usb3-port-number” 来提取正确的端口号。这些属性具有整数值，表示端口索引。端口索引号是以 1 为基础的，值为 0 是非法的。当发送特定于 mux-agent 的消息到 PMC 时，驱动程序直接使用从这些设备属性中提取的数字：

	Name (_DSD, Package () {
	    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
	    Package() {
	        Package () {"usb2-port-number", 6},
	        Package () {"usb3-port-number", 3},
	    },
	})

方向
~~~~~~~~~~~

根据平台的不同，来自连接器的数据和 SBU 线可能在 mux-agent 的角度来看是“固定的”，这意味着 mux-agent 驱动程序不应根据电缆插头的方向来配置它们。例如，如果平台上的重定时器处理电缆插头的方向，就会发生这种情况。驱动程序使用特定的设备属性 “sbu-orientation”（SBU）和 “hsl-orientation”（数据）来了解这些线路是否“固定”，以及固定的方向。这些属性的值是一个字符串值，并且可以是为 USB Type-C 连接器定义的方向之一：“normal” 或 “reversed”：

	Name (_DSD, Package () {
	    ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
	    Package() {
	        Package () {"sbu-orientation", "normal"},
	        Package () {"hsl-orientation", "normal"},
	    },
	})

示例 ASL
===========

以下 ASL 是一个示例，显示了 mux-agent 节点及其控制下的两个连接器：

	Scope (_SB.PCI0.PMC)
	{
	    Device (MUX)
	    {
	        Name (_HID, "INTC105C")

	        Device (CH0)
	        {
	            Name (_ADR, 0)

	            Name (_DSD, Package () {
	                ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
	                Package() {
	                    Package () {"usb2-port-number", 6},
	                    Package () {"usb3-port-number", 3},
	                    Package () {"sbu-orientation", "normal"},
	                    Package () {"hsl-orientation", "normal"},
	                },
	            })
	        }

	        Device (CH1)
	        {
	            Name (_ADR, 1)

	            Name (_DSD, Package () {
	                ToUUID("daffd814-6eba-4d8c-8a91-bc9bbf4aa301"),
	                Package() {
	                    Package () {"usb2-port-number", 5},
	                    Package () {"usb3-port-number", 2},
	                    Package () {"sbu-orientation", "normal"},
	                    Package () {"hsl-orientation", "normal"},
	                },
	            })
	        }
	    }
	}
```
