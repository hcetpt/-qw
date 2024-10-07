SPDX 许可证标识符: GPL-2.0

============================================
通过 sysfs 访问 PCI 设备资源
============================================

sysfs，通常挂载在 /sys，为支持它的平台提供了访问 PCI 资源的途径。例如，一个给定的总线可能看起来像这样：

```
/sys/devices/pci0000:17
|-- 0000:17:00.0
|   |-- class
|   |-- config
|   |-- device
|   |-- enable
|   |-- irq
|   |-- local_cpus
|   |-- remove
|   |-- resource
|   |-- resource0
|   |-- resource1
|   |-- resource2
|   |-- revision
|   |-- rom
|   |-- subsystem_device
|   |-- subsystem_vendor
|   `-- vendor
`-- ..
```

最顶层元素描述了 PCI 域和总线号。在这个例子中，域号是 0000，总线号是 17（两个值都是十六进制）。这个总线上有一个位于插槽 0 的功能设备。为了方便起见，重复了域号和总线号。在设备目录下有多个文件，每个文件都有其特定的功能：
```
    文件         功能
    ================ =====================================================
    class        PCI 类别（ASCII，只读）
    config       PCI 配置空间（二进制，读写）
    device       PCI 设备（ASCII，只读）
    enable       设备是否启用（ASCII，读写）
    irq          中断请求号（ASCII，只读）
    local_cpus    附近的 CPU 掩码（cpumask，只读）
    remove       从内核列表中移除设备（ASCII，写入）
    resource     PCI 资源主机地址（ASCII，只读）
    resource0..N 如果存在，则为 PCI 资源 N（二进制，内存映射，读写[1]_）
    resource0_wc..N_wc 如果可预取，则为 PCI WC 映射资源 N（二进制，内存映射）
    revision     PCI 版本（ASCII，只读）
    rom          如果存在，则为 PCI ROM 资源（二进制，只读）
    subsystem_device PCI 子系统设备（ASCII，只读）
    subsystem_vendor PCI 子系统供应商（ASCII，只读）
    vendor       PCI 供应商（ASCII，只读）
    ================ =====================================================
```

```
ro - 只读文件
rw - 文件可读可写
wo - 写入文件
mmap - 文件可以内存映射
ascii - 文件包含 ASCII 文本
binary - 文件包含二进制数据
cpumask - 文件包含 cpumask 类型
```

.. [1] 仅对 IORESOURCE_IO（I/O 端口）区域有效

只读文件提供信息，对其写入将被忽略，除了 'rom' 文件。可写文件可用于执行设备上的操作（例如更改配置空间、卸载设备）。可内存映射文件可通过在偏移量 0 处对文件进行内存映射来使用，从而实现用户空间中的实际设备编程。注意某些平台不支持对某些资源的内存映射，因此务必检查任何尝试的内存映射返回值。最值得注意的是 I/O 端口资源，它们也提供了读写访问。

'enable' 文件提供了一个计数器，指示设备已启用的次数。如果当前 'enable' 文件返回 '4'，并且向其中写入 '1'，则它将返回 '5'。向其中写入 '0' 将减少计数。即使计数回到 0，一些初始化也可能无法撤销。

'rom' 文件特别之处在于它提供了对设备 ROM 文件的只读访问（如果存在）。默认情况下它是禁用的，因此应用程序应在尝试读取调用之前写入字符串 "1" 来启用它，并在访问后写入 "0" 来禁用它。请注意，设备必须启用才能成功返回 ROM 读取的数据。

如果驱动程序未绑定到设备，可以通过上述文档中的 'enable' 文件启用它。

'remove' 文件用于移除 PCI 设备，方法是向该文件写入非零整数。这不涉及任何形式的热插拔功能，例如关闭设备电源。设备将从内核的 PCI 设备列表中移除，其 sysfs 目录也将被移除，并且设备将从任何附加的驱动程序中移除。禁止移除 PCI 根总线。

通过 sysfs 访问传统资源
----------------------------------------

如果底层平台支持，传统 I/O 端口和 ISA 内存资源也会在 sysfs 中提供。它们位于 PCI 类层次结构中，例如：

```
/sys/class/pci_bus/0000:17/
|-- bridge -> ../../../devices/pci0000:17
|-- cpuaffinity
|-- legacy_io
`-- legacy_mem
```

legacy_io 文件是一个读写文件，应用程序可以通过它进行传统端口 I/O。应用程序应打开该文件，定位到所需的端口（例如 0x3e8），然后进行 1、2 或 4 字节的读或写操作。legacy_mem 文件应使用对应于所需内存偏移量的偏移量进行内存映射，例如 VGA 帧缓冲区的 0xa0000。应用程序可以简单地解引用返回的指针（当然前提是检查错误）以访问传统内存空间。
支持新平台上的 PCI 访问
--------------------------------------

为了支持上述描述的 PCI 资源映射，Linux 平台代码理想上应定义 ARCH_GENERIC_PCI_MMAP_RESOURCE 并使用该功能的通用实现。为了支持通过 /proc/bus/pci 目录中的文件进行 mmap() 的历史接口，平台也可以设置 HAVE_PCI_MMAP。或者，设置了 HAVE_PCI_MMAP 的平台可以提供自己的 pci_mmap_resource_range() 实现，而不是定义 ARCH_GENERIC_PCI_MMAP_RESOURCE。

支持 PCI 资源写合并映射的平台必须定义 arch_can_pci_mmap_wc()，当允许写合并时，该函数在运行时应返回非零值。支持 I/O 资源映射的平台类似地定义 arch_can_pci_mmap_io()。

遗留资源由 HAVE_PCI_LEGACY 宏保护。希望支持遗留功能的平台应定义该宏，并提供 pci_legacy_read、pci_legacy_write 和 pci_mmap_legacy_page_range 函数。
