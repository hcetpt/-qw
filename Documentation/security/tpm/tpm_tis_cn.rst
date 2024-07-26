SPDX 许可证标识符: GPL-2.0

=========================
TPM 先进先出接口驱动程序
=========================

TCG PTP 规范定义了两种接口类型：先进先出 (FIFO) 和控制寄存器基 (CRB)。前者基于有序的读写操作，而后者则基于包含完整命令或响应的缓冲区。
先进先出 (FIFO) 接口被 tpm_tis_core 依赖驱动程序所使用。最初，Linux 只有一个名为 tpm_tis 的驱动程序，它涵盖了内存映射（也称为 MMIO）接口，但后来扩展以覆盖 TCG 标准支持的其他物理接口。
出于历史原因，原始的 MMIO 驱动程序仍被称为 tpm_tis，而 FIFO 驱动程序框架被称为 tpm_tis_core。“tis”后缀在 tpm_tis 中来源于 TPM 接口规范，这是针对 TPM 1.x 芯片的硬件接口规范。
通信基于一个由 TPM 芯片通过硬件总线或内存映射共享的 20 KiB 缓冲区，这取决于物理连线方式。该缓冲区进一步分割为五个等大小的 4 KiB 缓冲区，这些缓冲区提供了用于 CPU 和 TPM 之间通信的等效寄存器集。这些通信端点在 TCG 术语中被称为“localities”。
当内核想要向 TPM 芯片发送命令时，它首先通过设置 TPM_ACCESS 寄存器中的 requestUse 位来保留 locality 0。当访问被芯片授予时，该位会被清除。一旦完成通信，内核将写入 TPM_ACCESS.activeLocality 位。这会告知芯片 locality 已经释放。
芯片按照降序依次处理待处理的 localities：

- Locality 0 优先级最低
- Locality 5 优先级最高

关于 localities 的目的和含义的更多信息可以在 TCG PC 客户平台 TPM 配置文件规范的第 3.2 节中找到。

参考文献
==========

TCG PC 客户平台 TPM 配置文件 (PTP) 规范
https://trustedcomputinggroup.org/resource/pc-client-platform-tpm-profile-ptp-specification/
