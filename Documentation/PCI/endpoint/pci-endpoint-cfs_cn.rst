SPDX 许可证标识符: GPL-2.0

=======================================
使用 CONFIGFS 配置 PCI 终端
=======================================

:作者: Kishon Vijay Abraham I <kishon@ti.com>

PCI 终端核心提供了一个 configfs 条目（pci_ep）来配置 PCI 终端功能，并将终端功能与终端控制器绑定。（关于介绍其他机制以配置 PCI 终端功能，请参见[1]）
挂载 configfs
=============

PCI 终端核心层在已挂载的 configfs 目录中创建 pci_ep 目录。可以通过以下命令挂载 configfs ::

	mount -t configfs none /sys/kernel/config

目录结构
========

pci_ep configfs 在其根目录下有两个子目录：controllers 和 functions。系统中的每个 EPC 设备都会在 *controllers* 目录中有一个条目，系统中的每个 EPF 驱动程序都会在 *functions* 目录中有一个条目 ::

	/sys/kernel/config/pci_ep/
		.. controllers/
		.. functions/

创建 EPF 设备
============

每个注册的 EPF 驱动程序都会列在 controllers 目录中。与 EPF 驱动程序对应的条目将由 EPF 核心创建 ::

	/sys/kernel/config/pci_ep/functions/
		.. <EPF Driver1>/
			... <EPF Device 11>/
			... <EPF Device 21>/
			... <EPF Device 31>/
		.. <EPF Driver2>/
			... <EPF Device 12>/
			... <EPF Device 22>/

为了创建一个由 <EPF Driver> 探测类型的 <EPF 设备>，用户需要在 <EPF DriverN> 内创建一个目录。每个 <EPF 设备> 目录包含以下条目，可用于配置终端功能的标准配置头（这些条目在任何新的 <EPF Device> 创建时由框架生成） ::

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

如果一个 EPF 设备需要与两个 EPC 关联（如非透明桥接的情况），应将连接到主接口的终端控制器符号链接添加到 'primary' 目录中，并将连接到次接口的终端控制器符号链接添加到 'secondary' 目录中。
<EPF 设备> 目录可以包含指向其他 <EPF 设备> 的符号链接列表（<Symlink EPF Device 31>）。这些符号链接应由用户创建，以表示绑定到物理功能的虚拟功能。在上述目录结构中，<EPF Device 11> 是一个物理功能，而 <EPF Device 31> 是一个虚拟功能。一旦一个 EPF 设备与其他 EPF 设备关联后，就不能再与 EPC 设备关联。

EPC 设备
========

每个注册的 EPC 设备都会列在 controllers 目录中。与 EPC 设备对应的条目将由 EPC 核心创建 ::

	/sys/kernel/config/pci_ep/controllers/
		.. <EPC Device1>/
			... <Symlink EPF Device11>/
			... <Symlink EPF Device12>/
			... start
		.. <EPC Device2>/
			... <Symlink EPF Device21>/
			... <Symlink EPF Device22>/
			... start

<EPC 设备> 目录将包含指向 <EPF 设备> 的符号链接列表。这些符号链接应由用户创建，以表示终端设备中存在的功能。只有代表物理功能的 <EPF 设备> 才能与 EPC 设备关联。
<EPC 设备> 目录还将包含一个 *start* 字段。一旦向此字段写入 "1"，终端设备将准备好与主机建立连接。这通常是在所有 EPF 设备创建并与其 EPC 设备关联之后完成的。
```
| controllers/
|   <目录: EPC 名称>/
|       | <符号链接: 功能>
|       | start
| functions/
|   <目录: EPF 驱动>/
|       <目录: EPF 设备>/
|           | vendorid
|           | deviceid
|           | revid
|           | progif_code
|           | subclass_code
|           | baseclass_code
|           | cache_line_size
|           | subsys_vendor_id
|           | subsys_id
|           | interrupt_pin
|           | function

[1] 文档/PCI/终端/pci-endpoint.rst
```
