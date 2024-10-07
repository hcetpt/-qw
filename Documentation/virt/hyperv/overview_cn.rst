SPDX 许可证标识符: GPL-2.0

概述
=====
Linux 内核包含了一系列用于在 Microsoft 的 Hyper-V 虚拟机监控程序上作为完全受支持的来宾运行的代码。Hyper-V 主要由一个裸机虚拟机监控程序加上一个在父分区中运行的虚拟机管理服务组成（大致相当于 KVM 和 QEMU）。来宾虚拟机在子分区中运行。在本文档中，提到的 Hyper-V 通常包括虚拟机监控程序和 VMM 服务，不区分哪些功能是由哪个组件提供的。

Hyper-V 支持 x86/x64 和 arm64 架构，并且在这两个架构上都支持 Linux 来宾。除非另有说明，Hyper-V 的功能和行为在这两个架构上通常是相同的。

Linux 来宾与 Hyper-V 的通信
--------------------------------------
Linux 来宾通过以下四种方式与 Hyper-V 进行通信：

* 隐式陷阱：根据 x86/x64 或 arm64 架构定义，某些来宾操作会陷入到 Hyper-V。Hyper-V 模拟该操作并返回控制权给来宾。这种行为对 Linux 内核通常是透明的。
* 显式超调用：Linux 明确地向 Hyper-V 发出函数调用，传递参数。Hyper-V 执行请求的操作并返回控制权给调用者。参数通过处理器寄存器或 Linux 来宾与 Hyper-V 之间共享的内存传递。在 x86/x64 上，超调用使用特定于 Hyper-V 的调用序列。在 arm64 上，超调用使用 ARM 标准 SMCCC 调用序列。
* 合成寄存器访问：Hyper-V 实现了各种合成寄存器。在 x86/x64 上，这些寄存器在来宾中表现为 MSRs，Linux 内核可以使用 x86/x64 架构定义的常规机制读取或写入这些 MSR。在 arm64 上，这些合成寄存器必须通过显式超调用来访问。
* VMBus：VMBus 是一种基于上述三种机制的更高层次的软件结构。它是 Hyper-V 主机与 Linux 来宾之间的消息传递接口。它使用 Hyper-V 和来宾之间共享的内存以及各种信号机制。

前三种通信机制在《Hyper-V 顶层功能规范 (TLFS)》_ 中进行了详细描述。TLFS 描述了通用的 Hyper-V 功能，并提供了有关超调用和合成寄存器的详细信息。目前，TLFS 只为 x86/x64 架构编写。
.. _Hyper-V 顶层功能规范 (TLFS): https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/tlfs/tlfs

VMBus 没有文档。本文档提供了一个关于 VMBus 及其工作原理的高层次概览，但具体细节只能从代码中推断出来。

共享内存
--------------
Hyper-V 和 Linux 之间的许多通信方面都是基于共享内存的。共享通常按照以下方式进行：

* Linux 使用标准 Linux 机制从其物理地址空间分配内存。
* Linux 告诉 Hyper-V 分配内存的来宾物理地址 (GPA)。许多共享区域保持在一页之内，因此单个 GPA 就足够了。较大的共享区域需要一个 GPA 列表，这些 GPA 通常不需要在来宾物理地址空间中连续。Hyper-V 如何被告知 GPA 或 GPA 列表因情况而异。在某些情况下，单个 GPA 被写入合成寄存器。在其他情况下，GPA 或 GPA 列表通过 VMBus 消息发送。
* Hyper-V 将 GPAs（Guest Physical Addresses，客户机物理地址）转换为“真实的”物理内存地址，并创建一个虚拟映射，以便能够访问这些内存。
* Linux 可以通过通知 Hyper-V 将共享的 GPA 设置为零来撤销先前已建立的共享。

Hyper-V 使用 4 KB 的页面大小。传递给 Hyper-V 的 GPA 可能采用页号的形式，并且始终描述 4 KB 的范围。由于 x86/x64 架构上的 Linux 客户机页大小也是 4 KB，因此从客户机页到 Hyper-V 页的映射是 1:1 的。

在 arm64 上，Hyper-V 支持使用 4/16/64 KB 页面的客户机，这由 arm64 架构定义。如果 Linux 使用 16 或 64 KB 页面，Linux 代码必须小心地仅以 4 KB 页面的形式与 Hyper-V 通信。HV_HYP_PAGE_SIZE 和相关宏用于与 Hyper-V 通信的代码中，以便在所有配置下都能正确工作。

如 TLFS 中所述，Hyper-V 与 Linux 客户机之间共享的少数内存页是“覆盖”页。对于覆盖页，Linux 使用通常的方法分配客户机内存，并告诉 Hyper-V 分配内存的 GPA。但是，Hyper-V 然后会用它自己分配的页替换该物理内存页，原始物理内存页将不再在客户机 VM 中可访问。Linux 可以像访问其最初分配的内存一样正常访问该内存。“覆盖”行为仅在 Linux 最初建立共享并将覆盖页插入时可见，因为此时页面内容（从 Linux 视角看）会发生变化。同样，如果 Linux 撤销共享，Hyper-V 会移除覆盖页，最初由 Linux 分配的客户机页再次变得可见。

在 Linux 执行 kexec 到 kdump 内核或其他内核之前，应撤销与 Hyper-V 共享的内存。否则，在新内核开始使用该页面用于其他目的之后，Hyper-V 可能会修改共享页或移除覆盖页，从而破坏新内核。

Hyper-V 不向客户机 VM 提供单一的“设置一切”操作，因此 Linux 代码必须在执行 kexec 前单独撤销所有共享。参见 hv_kexec_handler() 和 hv_crash_handler()。但崩溃/恐慌路径中的清理仍然存在漏洞，因为某些共享页是使用每个 CPU 的合成寄存器设置的，并且没有机制可以撤销除运行恐慌路径的 CPU 之外的其他 CPU 的共享页。

### CPU 管理

Hyper-V 没有在运行中的 VM 中热添加或热移除 CPU 的能力。然而，Windows Server 2019 Hyper-V 及更早版本可能提供给客户机的 ACPI 表格中指示的 CPU 数量多于实际存在于 VM 中的数量。按照常规，Linux 将这些额外的 CPU 视为潜在的热添加 CPU，并报告它们，即使 Hyper-V 实际上永远不会热添加它们。

从 Windows Server 2022 Hyper-V 开始，ACPI 表格只反映实际存在于 VM 中的 CPU，因此 Linux 不会报告任何热添加 CPU。

可以使用正常的 Linux 机制将 Linux 客户机 CPU 下线，前提是没有任何 VMBus 通道中断分配给该 CPU。有关如何重新分配 VMBus 通道中断以允许 CPU 下线的详细信息，请参阅关于 VMBus 中断的部分。
32 位和 64 位
-----------------
在 x86/x64 架构上，Hyper-V 支持 32 位和 64 位的虚拟机（guest），并且 Linux 可以在这两个版本中构建和运行。尽管 32 位版本预计可以正常工作，但其使用率很低，可能会出现未被发现的退化问题。
在 arm64 架构上，Hyper-V 仅支持 64 位的虚拟机。

字节序
-----------------
Hyper-V 与虚拟机之间的所有通信均使用 Little-Endian 格式，无论是在 x86/x64 还是 arm64 上。arm64 上的大端格式不被 Hyper-V 支持，并且 Linux 代码在访问与 Hyper-V 共享的数据时也不使用字节序宏。

版本
-----------------
当前的 Linux 内核能够与较旧版本的 Hyper-V 正常工作，直到 Windows Server 2012 的 Hyper-V。对于 Windows Server 2008/2008 R2 中最初的 Hyper-V 版本的支持已被移除。
在 Hyper-V 上运行的 Linux 虚拟机会在 dmesg 中输出所运行的 Hyper-V 版本。此版本号采用 Windows 构建编号的形式，仅用于显示目的。Linux 代码不会在运行时检查此版本号来确定可用的功能和功能。Hyper-V 通过提供给虚拟机的合成 MSRs（Model Specific Registers）中的标志来指示功能/功能的可用性，而虚拟机代码会测试这些标志。
VMBus 有自己的协议版本，在虚拟机首次连接到 Hyper-V 时进行协商。此版本号也会在启动时输出到 dmesg。在代码中有几个地方会检查此版本号以确定特定功能是否存在。
此外，每个 VMBus 上的合成设备都有一个独立于 VMBus 协议版本的设备协议版本。这些合成设备的驱动程序通常会协商设备协议版本，并可能测试该协议版本以确定特定设备功能是否存在。

代码打包
-----------------
与 Hyper-V 相关的代码出现在 Linux 内核代码树中的三个主要区域：

1. `drivers/hv`

2. `arch/x86/hyperv` 和 `arch/arm64/hyperv`

3. 各个设备驱动程序区域，如 `drivers/scsi`, `drivers/net`, `drivers/clocksource` 等
还有一些零散的文件出现在其他位置。请参阅 MAINTAINERS 文件中“Hyper-V/Azure CORE AND DRIVERS”和“DRM DRIVER FOR HYPERV SYNTHETIC VIDEO DEVICE”部分的完整列表。
只有当配置了 `CONFIG_HYPERV` 时，才会编译第 1 和第 2 部分的代码。
同样地，大多数与 Hyper-V 相关的驱动程序代码仅在设置了 CONFIG_HYPERV 时才会编译。
在 #1 和 #3 中的大多数与 Hyper-V 相关的代码可以作为模块进行编译。
在 #2 中的架构特定代码必须内置编译。此外，drivers/hv/hv_common.c 是跨架构的低级代码，也必须内置编译。
