SPDX 许可证标识符: GPL-2.0

==============
Nitro 隔区
==============

概述
========

Nitro 隔区（NE）是 Amazon 弹性计算云（EC2）的一项新功能，允许客户在 EC2 实例内划分出隔离的计算环境 [1]。
例如，处理敏感数据的应用程序可以在虚拟机（VM）中运行，并与其他在同一 VM 中运行的应用程序分离。该应用程序将在一个独立的 VM 中运行，这个 VM 称为隔区（enclave），并与创建它的主 VM 并行运行。这种设置满足了低延迟应用的需求。
目前，在上游 Linux 内核中可用的 NE 内核驱动支持的架构有 x86 和 ARM64。
分配给隔区的资源（如内存和 CPU）从主 VM 中划分出来。每个隔区映射到主 VM 中运行的一个进程，通过 ioctl 接口与 NE 内核驱动进行通信。
在这种情况下，有两个组件：

1. 隔区抽象进程 —— 在主 VM 客户端中运行的用户空间进程，使用 NE 驱动提供的 ioctl 接口来启动一个隔区 VM（即下面的第 2 点）。
有一个 NE 模拟的 PCI 设备暴露给主 VM。这个新 PCI 设备的驱动包含在 NE 驱动中。
ioctl 逻辑映射到 PCI 设备命令，例如 NE_START_ENCLAVE ioctl 映射到一个启动隔区的 PCI 命令。然后这些 PCI 设备命令被转换成在管理程序侧执行的动作；这是运行在托管主 VM 的主机上的 Nitro 管理程序。Nitro 管理程序基于核心 KVM 技术。

2. 隔区本身 —— 运行在同一主机上的 VM，由主 VM 创建。内存和 CPU 从主 VM 中划分出来并专用于隔区 VM。隔区没有持久存储。
从主 VM 划分出来的并分配给隔区的内存区域需要对齐为 2 MiB / 1 GiB 物理连续内存区域（或其倍数，例如 8 MiB）。内存可以通过用户空间中的 hugetlbfs 分配 [2][3][7]。隔区的内存大小至少需要 64 MiB。隔区的内存和 CPU 必须来自同一个 NUMA 节点。
一个飞地（enclave）运行在专用的核心上。CPU 0 及其同级 CPU 需要保持可用，以供主虚拟机使用。具有管理员权限的用户需要设置一个 CPU 池用于飞地（NE）目的。请参阅内核文档中的 CPU 列表部分 [4]，了解 CPU 池格式的示例。

飞地通过本地通信信道与主虚拟机通信，使用 virtio-vsock [5]。主虚拟机有 virtio-pci vsock 模拟设备，而飞地虚拟机有 virtio-mmio vsock 模拟设备。vsock 设备使用 eventfd 进行信号传递。飞地虚拟机看到通常的接口——本地 APIC 和 IOAPIC——以便从 virtio-vsock 设备接收中断。virtio-mmio 设备位于典型 4 GiB 以下的内存中。

在飞地中运行的应用程序需要与操作系统（例如内核、RAM 磁盘、init）一起打包成飞地镜像。飞地虚拟机有自己的内核，并遵循标准的 Linux 引导协议 [6][8]。

内核 bzImage、内核命令行、RAM 磁盘等是 Enclave Image Format (EIF) 的一部分；此外还有一个包含元数据（如魔数、EIF 版本、图像大小和 CRC）的 EIF 头。

整个飞地镜像（EIF）、内核和 RAM 磁盘的哈希值会被计算出来。这用于验证加载到飞地虚拟机中的飞地镜像是预期要运行的那个。

这些加密度量被包含在一个由 Nitro 虚拟机生成的签名证明文件中，进一步用于证明飞地的身份；KMS 是一个与 NE 集成并检查证明文件的服务示例。

飞地镜像（EIF）在飞地内存中的偏移地址为 8 MiB。飞地中的 init 进程连接到主虚拟机的 vsock CID 和预定义端口——9000——发送心跳值——0xb7。这种机制用于验证主虚拟机上的飞地已启动。主虚拟机的 CID 为 3。

如果飞地虚拟机崩溃或正常退出，NE 驱动程序会收到一个中断事件。该事件通过轮询通知机制进一步发送给主虚拟机上运行的用户空间飞地进程。然后用户空间飞地进程可以退出。

[1] https://aws.amazon.com/ec2/nitro/nitro-enclaves/
[2] https://www.kernel.org/doc/html/latest/admin-guide/mm/hugetlbpage.html
[3] https://lwn.net/Articles/807108/
[4] https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html
[5] https://man7.org/linux/man-pages/man7/vsock.7.html
[6] https://www.kernel.org/doc/html/latest/x86/boot.html
[7] https://www.kernel.org/doc/html/latest/arm64/hugetlbpage.html
[8] https://www.kernel.org/doc/html/latest/arm64/booting.html
