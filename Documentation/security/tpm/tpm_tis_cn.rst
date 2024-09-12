SPDX 许可证标识符: GPL-2.0

=========================
TPM FIFO 接口驱动程序
=========================

TCG PTP 规范定义了两种接口类型：FIFO 和 CRB。前者基于顺序读写操作，而后者基于包含完整命令或响应的缓冲区。
FIFO（先进先出）接口被 tpm_tis_core 依赖的驱动程序使用。最初，Linux 只有一个名为 tpm_tis 的驱动程序，它覆盖了内存映射（即 MMIO）接口，但后来扩展以覆盖 TCG 标准支持的其他物理接口。
出于历史原因，原来的 MMIO 驱动程序被称为 tpm_tis，而 FIFO 驱动程序框架命名为 tpm_tis_core。“tis” 后缀在 tpm_tis 中来源于 TPM 接口规范，这是针对 TPM 1.x 芯片的硬件接口规范。
通信基于一个由 TPM 芯片通过硬件总线或内存映射共享的 20 KiB 缓冲区，具体取决于物理连接方式。该缓冲区进一步划分为五个等大小的 4 KiB 缓冲区，为 CPU 和 TPM 之间的通信提供等效的寄存器集。这些通信端点在 TCG 术语中称为本地性。
当内核想要向 TPM 芯片发送命令时，首先通过设置 TPM_ACCESS 寄存器中的 requestUse 位来保留本地性 0。芯片在授予访问权限后会清除该位。一旦完成通信，内核会写入 TPM_ACCESS.activeLocality 位，这会通知芯片该本地性已被释放。
芯片按降序依次处理待处理的本地性：

- 本地性 0 的优先级最低
- 本地性 5 的优先级最高

关于本地性的目的和含义的更多信息可以在 TCG PC 客户平台 TPM 配置文件规范的第 3.2 节找到。

参考文献
==========

TCG PC 客户平台 TPM 配置文件 (PTP) 规范  
https://trustedcomputinggroup.org/resource/pc-client-platform-tpm-profile-ptp-specification/
