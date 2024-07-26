SPDX 许可证标识符: GPL-2.0

=======================================
使用 CONFIGFS 配置 PCI 终端
=======================================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

PCI 终端核心提供了 configfs 条目（pci_ep）来配置 PCI 终端功能，并将终端功能绑定到终端控制器。（关于介绍其他配置 PCI 终端功能的机制，请参见[1]）
挂载 configfs
=================

PCI 终端核心层在已挂载的 configfs 目录中创建 pci_ep 目录。可以通过以下命令挂载 configfs ：

	mount -t configfs none /sys/kernel/config

目录结构
==================

pci_ep configfs 在其根目录下有两个目录：controllers 和 functions。系统中的每个 EPC 设备都将在 *controllers* 目录中有一个条目，而系统中的每个 EPF 驱动程序都将在 *functions* 目录中有一个条目。
::

	/sys/kernel/config/pci_ep/
		.. controllers/
		.. functions/

创建 EPF 设备
==================

每个注册的 EPF 驱动程序都会被列在 controllers 目录中。与 EPF 驱动程序对应的条目将由 EPF 核心创建。
::

	/sys/kernel/config/pci_ep/functions/
		.. <EPF Driver1>/
			... <EPF Device 11>/
			... <EPF Device 21>/
			... <EPF Device 31>/
		.. <EPF Driver2>/
			... <EPF Device 12>/
			... <EPF Device 22>/

为了创建类型为 <EPF Driver> 探测的 <EPF 设备>，用户需要在 <EPF DriverN> 内创建一个目录。每个 <EPF 设备> 目录包含以下条目，可用于配置终端功能的标准配置头（当任何新的 <EPF Device> 创建时，这些条目由框架创建）：
::

		.. <EPF Driver1>/
			... <EPF Device 11>/
				... vendorid
				... deviceid
				... revid
				... progif_code
				... subclass_code
				... baseclass_code
				... cache_line_size
				... subsys_vendor_id
				... subsys_id
				... interrupt_pin
			        ... <Symlink EPF Device 31>/
                                ... primary/
			                ... <Symlink EPC Device1>/
                                ... secondary/
			                ... <Symlink EPC Device2>/

如果 EPF 设备需要与 2 个 EPC 关联（例如，在非透明桥的情况下），则应将连接到主接口的终端控制器的符号链接添加到 'primary' 目录中，并将连接到次级接口的终端控制器的符号链接添加到 'secondary' 目录中。
<EPF Device> 目录可以有一系列指向其他 <EPF Device> 的符号链接（<Symlink EPF Device 31>）。这些符号链接应由用户创建以表示绑定到物理功能的虚拟功能。在上面的目录结构中，<EPF Device 11> 是一个物理功能，而 <EPF Device 31> 是一个虚拟功能。一旦 EPF 设备与其他 EPF 设备关联后，就不能再与 EPC 设备关联。

EPC 设备
==========

每个注册的 EPC 设备都会被列在 controllers 目录中。与 EPC 设备对应的条目将由 EPC 核心创建。
::

	/sys/kernel/config/pci_ep/controllers/
		.. <EPC Device1>/
			... <Symlink EPF Device11>/
			... <Symlink EPF Device12>/
			... start
		.. <EPC Device2>/
			... <Symlink EPF Device21>/
			... <Symlink EPF Device22>/
			... start

<EPC Device> 目录将有一系列指向 <EPF Device> 的符号链接。这些符号链接应由用户创建以表示终端设备中存在的功能。只有代表物理功能的 <EPF Device> 才能与 EPC 设备关联。
<EPC Device> 目录还将有一个 *start* 字段。一旦向此字段写入 "1"，终端设备将准备好与主机建立连接。这通常是在所有 EPF 设备创建并与其 EPC 设备关联之后完成的。
此文件结构描述可以翻译为：

```
| controllers/
    | <目录: EPC 名称>/
        | <符号链接: 功能>
        | start
| functions/
    | <目录: EPF 驱动>/
        | <目录: EPF 设备>/
            | vendorid
            | deviceid
            | revid
            | progif_code
            | subclass_code
            | baseclass_code
            | cache_line_size
            | subsys_vendor_id
            | subsys_id
            | interrupt_pin
            | function
```

说明文档位置：`[1] 文档/PCI/终端/pci-endpoint.rst`
