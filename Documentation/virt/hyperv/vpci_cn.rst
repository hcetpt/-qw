SPDX 许可证标识符: GPL-2.0

PCI 直通设备
=========================

在 Hyper-V 客户机虚拟机中，PCI 直通设备（也称为虚拟 PCI 设备或 vPCI 设备）是直接映射到客户机物理地址空间的物理 PCI 设备。客户机设备驱动程序可以直接与硬件交互，无需通过主机虚拟机管理程序中介。这种方法相比通过虚拟机管理程序虚拟化的设备，提供了更高的带宽和更低的延迟。该设备对客户机的表现应如同在裸机上运行一样，因此不需要对 Linux 设备驱动程序进行任何更改。

Hyper-V 对 vPCI 设备的术语为“离散设备分配”（DDA）。有关 Hyper-V DDA 的公共文档可在此处找到：`DDA`_

.. _DDA: https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/plan-for-deploying-devices-using-discrete-device-assignment

DDA 通常用于存储控制器（如 NVMe）以及 GPU。对于 NIC（网络接口控制器），类似机制被称为 SR-IOV，并通过允许客户机设备驱动程序直接与硬件交互来产生相同的好处。请参阅 Hyper-V 公共文档中的相关内容：`SR-IOV`_

.. _SR-IOV: https://learn.microsoft.com/en-us/windows-hardware/drivers/network/overview-of-single-root-i-o-virtualization--sr-iov-

关于 vPCI 设备的讨论包括 DDA 和 SR-IOV 设备。

设备呈现
-------------------

Hyper-V 在 vPCI 设备运行时提供了完整的 PCI 功能，因此如果使用正确的 Linux 内核 API 来访问 PCI 配置空间并与其他 Linux 组件集成，则可以不变地使用 Linux 设备驱动程序。但是，PCI 设备的初始检测及其与 Linux PCI 子系统的集成必须使用特定于 Hyper-V 的机制。因此，在 Hyper-V 上的 vPCI 设备具有双重身份。它们最初通过标准 VMBus “提供”机制呈现给 Linux 客户机，因此具有 VMBus 身份并出现在 /sys/bus/vmbus/devices 下。Linux 中位于 drivers/pci/controller/pci-hyperv.c 的 VMBus vPCI 驱动程序通过创建一个 PCI 总线拓扑并生成所有正常的 PCI 设备数据结构来处理新引入的 vPCI 设备，这些数据结构就像在裸机系统上通过 ACPI 发现 PCI 设备时存在的一样。一旦这些数据结构设置完毕，该设备在 Linux 中也具有正常的 PCI 身份，常规的 Linux 设备驱动程序可以像在裸机上的 Linux 中运行一样工作。由于 vPCI 设备通过 VMBus 提供机制动态呈现，因此它们不会出现在 Linux 客户机的 ACPI 表格中。vPCI 设备可以在 VM 生命周期的任何时候添加到 VM 或从 VM 中移除，而不仅仅是在初始启动时。

通过这种方法，vPCI 设备同时是一个 VMBus 设备和一个 PCI 设备。作为对 VMBus 提供消息的响应，hv_pci_probe() 函数运行并建立到 Hyper-V 主机上的 vPCI VSP 的 VMBus 连接。该连接有一个单一的 VMBus 通道。该通道用于与 vPCI VSP 交换消息以在 Linux 中设置和配置 vPCI 设备。一旦设备完全作为 PCI 设备在 Linux 中配置好后，VMBus 通道仅在 Linux 更改 vCPU 中断状态或 vPCI 设备从运行中的 VM 中移除时使用。设备的持续操作直接发生在设备的 Linux 设备驱动程序和硬件之间，VMBus 和 VMBus 通道不再发挥作用。

PCI 设备设置
----------------

PCI 设备设置遵循 Hyper-V 最初为 Windows 客户机创建的序列，但由于 Linux PCI 子系统与 Windows 的整体结构差异，这可能不适合 Linux 客户机。尽管如此，通过在 Linux 的 Hyper-V 虚拟 PCI 驱动程序中进行一些调整，虚拟 PCI 设备可以在 Linux 中设置，使得通用 Linux PCI 子系统代码和设备的 Linux 驱动程序能够“正常工作”。

每个 vPCI 设备在 Linux 中都设置为拥有自己的 PCI 域和主机桥。PCI 域 ID 来自分配给 VMBus vPCI 设备的实例 GUID 的第 4 和第 5 字节。Hyper-V 主机不保证这些字节是唯一的，因此 hv_pci_probe() 包含一种解决冲突的算法。此冲突解决方案旨在确保在同一 VM 重新启动期间域 ID 不发生变化，因为域 ID 出现在某些设备的用户空间配置中。

hv_pci_probe() 分配一个客户机 MMIO 范围用作设备的 PCI 配置空间。此 MMIO 范围通过 VMBus 通道告知 Hyper-V 主机，作为告知主机设备准备进入 d0 状态的一部分。详见 hv_pci_enter_d0()。当客户机随后访问此 MMIO 范围时，Hyper-V 主机会拦截这些访问并将它们映射到物理设备的 PCI 配置空间。

hv_pci_probe() 还从 Hyper-V 主机获取设备的 BAR 信息，并使用这些信息分配 BAR 的 MMIO 空间。然后将该 MMIO 空间设置为与主机桥相关联，以便在 Linux 中处理 BAR 的通用 PCI 子系统代码可以正常工作。

最后，hv_pci_probe() 创建根 PCI 总线。此时 Hyper-V 虚拟 PCI 驱动程序的调整完成，常规的 Linux PCI 机制可以扫描根总线来检测设备、执行驱动匹配，并初始化驱动程序和设备。
### PCI 设备移除

在虚拟机（VM）的生命周期中的任何时候，Hyper-V 主机都可能发起从客户机 VM 中移除一个 vPCI 设备的操作。该移除操作是由 Hyper-V 主机上的管理员操作触发的，并不受客户机操作系统控制。

客户机 VM 会通过一条非请求的“弹出”消息来得知设备将被移除，这条消息是通过与 vPCI 设备相关的 VMBus 通道从主机发送到客户机的。当接收到该消息时，Linux 中的 Hyper-V 虚拟 PCI 驱动程序会异步调用 Linux 内核 PCI 子系统的函数来关闭并移除设备。当这些调用完成后，会通过 VMBus 通道向 Hyper-V 发送一条“移除完成”消息，表明设备已被移除。此时，Hyper-V 会向 Linux 客户机发送一条 VMBus 撤销消息，Linux 的 VMBus 驱动程序会处理该消息，移除设备的 VMBus 身份。一旦该处理完成，所有关于该设备存在的痕迹都将从 Linux 内核中消失。撤销消息还表明 Hyper-V 已经停止为该 vPCI 设备提供支持。如果客户机试图访问该设备的 MMIO 空间，则将是无效引用。影响该设备的 hypercalls 会返回错误，任何进一步通过 VMBus 通道发送的消息都将被忽略。

在发送“弹出”消息后，Hyper-V 允许客户机 VM 在 60 秒内干净地关闭设备并回复“移除完成”，然后再发送 VMBus 撤销消息。如果由于任何原因，在允许的 60 秒内“弹出”步骤没有完成，Hyper-V 主机会强制执行撤销步骤，这可能会导致客户机中出现一系列错误，因为设备现在已不存在于客户机的角度来看，并且访问设备的 MMIO 空间将会失败。

由于弹出操作是异步的，并且可以在客户机 VM 生命周期中的任何时候发生，因此在 Hyper-V 虚拟 PCI 驱动程序中实现适当的同步非常复杂。甚至在新提供的 vPCI 设备完全设置之前就观察到了弹出操作。Hyper-V 虚拟 PCI 驱动程序多年来已经多次更新以修复在不恰当时间发生弹出时的竞争条件问题。修改此代码时必须小心，以防重新引入此类问题。请参阅代码中的注释。

### 中断分配

Hyper-V 虚拟 PCI 驱动程序支持使用 MSI、多 MSI 或 MSI-X 的 vPCI 设备。由于 Linux 设置 IRQ 的方式映射到 Hyper-V 接口的方式，分配将接收特定 MSI 或 MSI-X 消息的客户机 vCPU 是一个复杂的过程。对于单个 MSI 和 MSI-X 的情况，Linux 会调用 hv_compse_msi_msg() 两次，第一次调用包含一个虚拟的 vCPU，第二次调用包含真实的 vCPU。此外，最终会在 x86 上调用 hv_irq_unmask() 或在 arm64 上设置 GICD 寄存器来再次指定真实的 vCPU。这三个调用都会与 Hyper-V 进行交互，Hyper-V 必须决定哪个物理 CPU 应该接收中断，然后将其转发给客户机 VM。

不幸的是，Hyper-V 的决策过程有些局限性，可能会导致物理中断集中在单个 CPU 上，从而导致性能瓶颈。请参阅 hv_compose_msi_req_get_cpu() 函数上方的详细注释以了解如何解决此问题。

Hyper-V 虚拟 PCI 驱动程序实现了 irq_chip.irq_compose_msi_msg 函数作为 hv_compose_msi_msg()。然而，在 Hyper-V 上，实现需要发送一条 VMBus 消息给 Hyper-V 主机并等待中断指示收到回复消息。由于 irq_chip.irq_compose_msi_msg 可能在持有 IRQ 锁的情况下被调用，因此不能像通常那样等待中断唤醒后再休眠。相反，hv_compose_msi_msg() 必须发送 VMBus 消息，然后轮询直到完成消息到达。进一步增加复杂性的是，vPCI 设备可能在轮询过程中被弹出/撤销，因此必须检测这种情况。请参阅代码中关于这一非常棘手区域的注释。
Hyper-V 虚拟 PCI 驱动程序（pci-hyperv.c）中的大部分代码适用于运行在 x86 和 arm64 架构上的 Hyper-V 和 Linux 客户机。但在中断分配管理方面存在差异。在 x86 上，客户机中的 Hyper-V 虚拟 PCI 驱动程序必须通过超调用告诉 Hyper-V 哪个客户机 vCPU 应该被每个 MSI/MSI-X 中断触发，并且中断所选择的 x86 中断向量号。这个超调用由 hv_arch_irq_unmask() 函数完成。而在 arm64 上，Hyper-V 虚拟 PCI 驱动程序管理为每个 MSI/MSI-X 中断分配一个 SPI。Hyper-V 虚拟 PCI 驱动程序将分配的 SPI 存储在架构 GICD 寄存器中，这些寄存器由 Hyper-V 模拟，因此与 x86 不同，不需要进行超调用。由于 Hyper-V 在 arm64 客户机 VM 中不模拟 GICv3 ITS，因此它不支持使用 LPI 用于 vPCI 设备。

Linux 中的 Hyper-V 虚拟 PCI 驱动程序支持那些驱动程序创建了受管或不受管 Linux IRQ 的 vPCI 设备。如果通过 /proc/irq 接口更新不受管 IRQ 的 smp_affinity，Hyper-V 虚拟 PCI 驱动程序会被调用来告诉 Hyper-V 主机更改中断目标，一切都能正常工作。然而，在 x86 上，如果 x86_vector IRQ 域需要重新分配中断向量（因为某个 CPU 上的向量不足），则没有路径来通知 Hyper-V 主机这一变化，从而导致问题。幸运的是，客户机 VM 运行在一个受限设备环境中，不会出现使用完所有 CPU 向量的情况。由于这个问题只是理论上的担忧而不是实际问题，因此尚未解决。

### DMA

默认情况下，当 VM 创建时，Hyper-V 会在主机上固定所有客户机 VM 内存，并编程物理 IOMMU 以允许 VM 访问其所有内存的 DMA。因此，可以安全地将 PCI 设备分配给 VM，并允许客户机操作系统编程 DMA 传输。物理 IOMMU 可防止恶意客户机发起到主机或其他主机上 VM 的内存的 DMA。从 Linux 客户机的角度来看，这种 DMA 传输处于“直接”模式，因为 Hyper-V 未在客户机中提供虚拟 IOMMU。

Hyper-V 假设物理 PCI 设备始终执行缓存一致性的 DMA。在 x86 上，这种行为是架构要求的。而在 arm64 上，架构允许缓存一致性和非缓存一致性设备，每种设备的行为在 ACPI DSDT 中指定。但是，当 PCI 设备分配给客户机 VM 时，该设备不会出现在 DSDT 中，因此 Hyper-V VMBus 驱动程序会将缓存一致性信息从 VMBus 节点传播到所有 VMBus 设备（包括 vPCI 设备，因为它们具有双重身份：VMBus 设备和 PCI 设备）。参见 vmbus_dma_configure()。

当前版本的 Hyper-V 总是指定 VMBus 是缓存一致性的，因此 arm64 上的 vPCI 设备总是标记为缓存一致性的，并且 CPU 在 dma_map/unmap_*() 调用期间不执行任何同步操作。

### vPCI 协议版本

如前所述，在 vPCI 设备设置和拆除过程中，消息通过 VMBus 通道在 Hyper-V 主机和 Linux 客户机中的 Hyper-V vPCI 驱动程序之间传递。在较新版本的 Hyper-V 中，某些消息已进行了修订，因此客户机和主机必须就使用的 vPCI 协议版本达成一致。版本协商在首次建立 VMBus 通道通信时进行。参见 hv_pci_protocol_negotiation()。较新版本的协议扩展了对超过 64 个 vCPU 的 VM 的支持，并提供了有关 vPCI 设备的附加信息，例如它在底层硬件中最紧密关联的客户机虚拟 NUMA 节点。

### 客户机 NUMA 节点亲和性

当 vPCI 协议版本提供时，vPCI 设备的客户机 NUMA 节点亲和性作为 Linux 设备信息的一部分存储，供后续使用。参见 hv_pci_assign_numa_node()。如果协商的协议版本不支持主机提供 NUMA 亲和性信息，则 Linux 客户机将设备 NUMA 节点默认为 0。但即使协商的协议版本包含 NUMA 亲和性信息，主机提供此类信息的能力取决于某些主机配置选项。如果客户机接收到 NUMA 节点值 “0”，这可能意味着 NUMA 节点 0，也可能意味着“没有信息可用”。遗憾的是，从客户机端无法区分这两种情况。

### CoCo VM 中的 PCI 配置空间访问

Linux PCI 设备驱动程序使用 Linux PCI 子系统提供的标准函数集访问 PCI 配置空间。在 Hyper-V 客户机中，这些标准函数映射到 Hyper-V 虚拟 PCI 驱动程序中的 hv_pcifront_read_config() 和 hv_pcifront_write_config() 函数。在普通 VM 中，这些 hv_pcifront_*() 函数直接访问 PCI 配置空间，并且这些访问会捕获到 Hyper-V 进行处理。
但在 CoCo VM 中，内存加密阻止了 Hyper-V 读取来宾指令流以模拟访问，因此 hv_pcifront_*() 函数必须通过带有显式参数的超调用（hypercalls）来描述要进行的访问。

配置块后通道
-------------------------
Hyper-V 主机和 Linux 中的 Hyper-V 虚拟 PCI 驱动程序共同实现了一种非标准的主机与来宾之间的后通道通信路径。该后通道路径使用与 vPCI 设备关联的 VMBus 信道发送的消息。hyperv_read_cfg_blk() 和 hyperv_write_cfg_blk() 函数是提供给 Linux 内核其他部分的主要接口。截至本文撰写时，这些接口仅由 Mellanox mlx5 驱动程序使用，以便将诊断数据传递给运行在 Azure 公共云中的 Hyper-V 主机。hyperv_read_cfg_blk() 和 hyperv_write_cfg_blk() 函数实现在一个单独的模块中（pci-hyperv-intf.c，在 CONFIG_PCI_HYPERV_INTERFACE 下），当在非 Hyper-V 环境中运行时，实际上它们被存根化处理。
