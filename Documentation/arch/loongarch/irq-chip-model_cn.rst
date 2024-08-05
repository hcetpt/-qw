### SPDX 许可证标识符: GPL-2.0

=======================================
LoongArch 的中断控制器模型（层次结构）
=======================================

目前，基于 LoongArch 的处理器（例如 Loongson-3A5000）只能与 LS7A 芯片组一起工作。LoongArch 计算机中的中断控制器包括 CPUINTC（CPU 核心中断控制器）、LIOINTC（传统 I/O 中断控制器）、EIOINTC（扩展 I/O 中断控制器）、HTVECINTC（Hyper-Transport 向量中断控制器）、PCH-PIC（LS7A 芯片组中的主中断控制器）、PCH-LPC（LS7A 芯片组中的 LPC 中断控制器）以及 PCH-MSI（MSI 中断控制器）。CPUINTC 是每个核心的控制器（位于 CPU 内），而 LIOINTC/EIOINTC/HTVECINTC 是每个封装的控制器（位于 CPU 内），PCH-PIC/PCH-LPC/PCH-MSI 则是位于 CPU 外部的控制器（即在芯片组中）。这些控制器（换句话说，中断芯片）以一种层次结构相连，并存在两种层次结构模型（传统模型和扩展模型）。

#### 传统中断模型
=================

在此模型中，IPI（处理器间中断）和 CPU 本地定时器中断直接进入 CPUINTC，CPU UART 中断进入 LIOINTC，而其他所有设备的中断则先进入 PCH-PIC/PCH-LPC/PCH-MSI，然后被 HTVECINTC 汇总，之后再进入 LIOINTC，最后到达 CPUINTC。
```
+-----+     +---------+     +-------+
| IPI | --> | CPUINTC | <-- | Timer |
+-----+     +---------+     +-------+
                      ^
                      |
                 +---------+     +-------+
                 | LIOINTC | <-- | UARTs |
                 +---------+     +-------+
                      ^
                      |
                +-----------+
                | HTVECINTC |
                +-----------+
                 ^         ^
                 |         |
           +---------+ +---------+
           | PCH-PIC | | PCH-MSI |
           +---------+ +---------+
             ^     ^           ^
             |     |           |
     +---------+ +---------+ +---------+
     | PCH-LPC | | Devices | | Devices |
     +---------+ +---------+ +---------+
          ^
          |
     +---------+
     | Devices |
     +---------+
```

#### 扩展中断模型
==================

在此模型中，IPI（处理器间中断）和 CPU 本地定时器中断直接进入 CPUINTC，CPU UART 中断进入 LIOINTC，而其他所有设备的中断则先进入 PCH-PIC/PCH-LPC/PCH-MSI，然后被 EIOINTC 汇总，之后直接进入 CPUINTC。
```
          +-----+     +---------+     +-------+
          | IPI | --> | CPUINTC | <-- | Timer |
          +-----+     +---------+     +-------+
                       ^       ^
                       |       |
                +---------+ +---------+     +-------+
                | EIOINTC | | LIOINTC | <-- | UARTs |
                +---------+ +---------+     +-------+
                 ^       ^
                 |       |
          +---------+ +---------+
          | PCH-PIC | | PCH-MSI |
          +---------+ +---------+
            ^     ^           ^
            |     |           |
    +---------+ +---------+ +---------+
    | PCH-LPC | | Devices | | Devices |
    +---------+ +---------+ +---------+
         ^
         |
    +---------+
    | Devices |
    +---------+
```

#### 与 ACPI 相关的定义
========================

- **CPUINTC**:
  - `ACPI_MADT_TYPE_CORE_PIC;`
  - `struct acpi_madt_core_pic;`
  - `enum acpi_madt_core_pic_version;`

- **LIOINTC**:
  - `ACPI_MADT_TYPE_LIO_PIC;`
  - `struct acpi_madt_lio_pic;`
  - `enum acpi_madt_lio_pic_version;`

- **EIOINTC**:
  - `ACPI_MADT_TYPE_EIO_PIC;`
  - `struct acpi_madt_eio_pic;`
  - `enum acpi_madt_eio_pic_version;`

- **HTVECINTC**:
  - `ACPI_MADT_TYPE_HT_PIC;`
  - `struct acpi_madt_ht_pic;`
  - `enum acpi_madt_ht_pic_version;`

- **PCH-PIC**:
  - `ACPI_MADT_TYPE_BIO_PIC;`
  - `struct acpi_madt_bio_pic;`
  - `enum acpi_madt_bio_pic_version;`

- **PCH-MSI**:
  - `ACPI_MADT_TYPE_MSI_PIC;`
  - `struct acpi_madt_msi_pic;`
  - `enum acpi_madt_msi_pic_version;`

- **PCH-LPC**:
  - `ACPI_MADT_TYPE_LPC_PIC;`
  - `struct acpi_madt_lpc_pic;`
  - `enum acpi_madt_lpc_pic_version;`

#### 参考资料
=============

- **Loongson-3A5000 文档**:
  - [中文版](https://github.com/loongson/LoongArch-Documentation/releases/latest/download/Loongson-3A5000-usermanual-1.02-CN.pdf)
  - [英文版](https://github.com/loongson/LoongArch-Documentation/releases/latest/download/Loongson-3A5000-usermanual-1.02-EN.pdf)

- **Loongson 的 LS7A 芯片组文档**:
  - [中文版](https://github.com/loongson/LoongArch-Documentation/releases/latest/download/Loongson-7A1000-usermanual-2.00-CN.pdf)
  - [英文版](https://github.com/loongson/LoongArch-Documentation/releases/latest/download/Loongson-7A1000-usermanual-2.00-EN.pdf)

.. Note::
    - CPUINTC 是 CSR.ECFG/CSR.ESTAT 和其在“LoongArch 参考手册 第一卷”第 7.4 节中描述的中断控制器；
    - LIOINTC 是“Loongson 3A5000 处理器参考手册”第 11.1 节中描述的“传统 I/O 中断”；
    - EIOINTC 是“Loongson 3A5000 处理器参考手册”第 11.2 节中描述的“扩展 I/O 中断”；
    - HTVECINTC 是“Loongson 3A5000 处理器参考手册”第 14.3 节中描述的“HyperTransport 中断”；
    - PCH-PIC/PCH-MSI 是“Loongson 7A1000 Bridge 用户手册”第 5 节中描述的“中断控制器”；
    - PCH-LPC 是“Loongson 7A1000 Bridge 用户手册”第 24.3 节中描述的“LPC 中断”。
