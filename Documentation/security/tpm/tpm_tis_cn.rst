SPDX 许可证标识符: GPL-2.0

=========================
TPM FIFO 接口驱动程序
=========================

TCG PTP 规范定义了两种接口类型：FIFO 和 CRB。前者基于顺序读写操作，后者基于包含完整命令或响应的缓冲区。
FIFO（先进先出）接口被 tpm_tis_core 依赖的驱动程序使用。最初，Linux 只有一个名为 tpm_tis 的驱动程序，它涵盖了内存映射（即 MMIO）接口，但后来扩展以覆盖 TCG 标准支持的其他物理接口。
由于历史原因，最初的 MMIO 驱动程序被称为 tpm_tis，而 FIFO 驱动程序框架命名为 tpm_tis_core。“tis” 后缀在 tpm_tis 中来源于 TPM 接口规范，这是针对 TPM 1.x 芯片的硬件接口规范。
通信基于一个由 TPM 芯片通过硬件总线或内存映射共享的 20 KiB 缓冲区，具体取决于物理连线方式。该缓冲区进一步分为五个等大小的 4 KiB 缓冲区，为 CPU 和 TPM 之间的通信提供了等效的寄存器集。这些通信端点在 TCG 术语中称为“局部性”。
当内核想要向 TPM 芯片发送命令时，它首先通过设置 TPM_ACCESS 寄存器中的 requestUse 位来预留局部性 0。芯片在授予访问权限后会清除该位。一旦完成通信，内核会写入 TPM_ACCESS.activeLocality 位。这通知芯片该局部性已被释放。
待处理的局部性由芯片按照降序依次处理：

- 局部性 0 优先级最低
- 局部性 5 优先级最高

关于局部性的目的和意义的更多信息可以在 TCG PC 客户平台 TPM 概要规范的第 3.2 节找到。

参考文献
==========

TCG PC 客户平台 TPM 概要规范 (PTP)
https://trustedcomputinggroup.org/resource/pc-client-platform-tpm-profile-ptp-specification/
