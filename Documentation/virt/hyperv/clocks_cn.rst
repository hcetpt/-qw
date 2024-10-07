SPDX 许可证标识符: GPL-2.0

时钟和定时器
=============

arm64
-----
在 arm64 上，Hyper-V 虚拟化了 ARMv8 架构系统计数器和定时器。客户机虚拟机通过标准的 `arm_arch_timer.c` 驱动程序使用这个虚拟化的硬件作为 Linux 的时钟源和时钟事件，就像在裸机上一样。Linux 对架构系统计数器的 vDSO 支持在 Hyper-V 客户机上是功能完整的。尽管 Hyper-V 还提供了合成系统时钟和四个每 CPU 合成定时器（如 TLFS 中所述），但这些定时器在 arm64 的 Hyper-V 客户机中并未被 Linux 内核使用。然而，旧版本的 arm64 Hyper-V 只部分虚拟化了 ARMv8 架构定时器，使得该定时器在虚拟机中不会生成中断。由于这一限制，在这些旧版本的 Hyper-V 上运行当前的 Linux 内核版本需要一个外部补丁来使用 Hyper-V 的合成时钟/定时器。

x86/x64
-------
在 x86/x64 上，Hyper-V 为客户机虚拟机提供了合成系统时钟和四个每 CPU 的合成定时器（如 TLFS 中所述）。Hyper-V 还通过 RDTSC 和相关指令提供对虚拟化 TSC 的访问。这些 TSC 指令不会陷入到虚拟机监控程序中，因此在虚拟机中提供了出色的性能。Hyper-V 执行 TSC 校准，并通过合成的 MSR 向客户机虚拟机提供 TSC 频率。Linux 中的 Hyper-V 初始化代码读取此 MSR 来获取频率，因此跳过了 TSC 校准并设置了 `tsc_reliable`。Hyper-V 提供了 PIT（仅限于 Hyper-V 第一代虚拟机）、本地 APIC 定时器和 RTC 的虚拟化版本。Hyper-V 在客户机虚拟机中不提供虚拟化的 HPET。
Hyper-V 的合成系统时钟可以通过合成的 MSR 读取，但这会陷入到虚拟机监控程序。作为一种更快的替代方案，客户机可以配置一个内存页，以在客户机和虚拟机监控程序之间共享。Hyper-V 将这个内存页填充 64 位缩放值和偏移值。要读取合成时钟值，客户机读取 TSC 并应用缩放和偏移，具体方法如 Hyper-V TLFS 中所述。最终得到的值以恒定的 10 MHz 频率递增。在实时迁移至具有不同 TSC 频率的主机时，Hyper-V 会调整共享页中的缩放和偏移值，以保持 10 MHz 频率不变。
从 Windows Server 2022 Hyper-V 开始，Hyper-V 使用硬件支持的 TSC 频率缩放功能，使虚拟机能够在不同 TSC 频率的 Hyper-V 主机之间进行实时迁移。当 Linux 客户机检测到此 Hyper-V 功能可用时，它更倾向于使用 Linux 的标准基于 TSC 的时钟源。否则，它使用通过共享页实现的 Hyper-V 合成系统时钟（识别为 "hyperv_clocksource_tsc_page"）。
Hyper-V 的合成系统时钟可通过 vDSO 提供给用户空间，`gettimeofday()` 和相关系统调用可以在用户空间完全执行。vDSO 通过将带有缩放和偏移值的共享页映射到用户空间来实现。用户空间代码执行相同的算法，即读取 TSC 并应用缩放和偏移以获得恒定的 10 MHz 时钟。
Linux 的时钟事件基于 Hyper-V 合成定时器 0（stimer0）。
虽然Hyper-V为每个CPU提供了4个合成定时器，但Linux仅使用定时器0。在较旧版本的Hyper-V中，来自stimer0的中断会生成一个VMBus控制消息，该消息由vmbus_isr()进行解复用，具体描述参见Documentation/virt/hyperv/vmbus.rst文档。在较新版本的Hyper-V中，stimer0中断可以映射到架构级别的中断，这被称为“直接模式”。当直接模式可用时，Linux倾向于使用它。由于x86/x64不支持每CPU的中断，因此直接模式在所有CPU上静态分配了一个x86中断向量（HYPERV_STIMER0_VECTOR），并明确编码调用stimer0中断处理程序。因此，来自stimer0的中断会在/proc/interrupts中的"HVS"行记录，而不是与Linux IRQ关联。基于虚拟化的PIT和本地APIC定时器的Clockevents也可以工作，但Hyper-V stimer0是首选。

Hyper-V合成系统时钟和定时器的驱动程序位于drivers/clocksource/hyperv_timer.c。
