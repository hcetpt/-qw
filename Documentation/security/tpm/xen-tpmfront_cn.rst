=============================
Xen 中的虚拟可信平台模块接口
=============================

作者：Matthew Fioravante（约翰斯·霍普金斯大学应用物理实验室），Daniel De Graaf（美国国家安全局）

本文档描述了 Xen 中的虚拟可信平台模块（vTPM）子系统。假设读者熟悉 Xen、Linux 的构建与安装流程，并对 TPM 和 vTPM 的基本概念有一定的了解。
简介
------------

本项目的目标是为虚拟客户操作系统（在 Xen 术语中称为 DomU）提供 TPM 功能。这使得程序可以在虚拟系统中像在物理系统上一样与 TPM 进行交互。每个客户机都有一个独立的、模拟的软件 TPM。然而，每个 vTPM 的秘密（密钥、非易失性内存等）都由 vTPM 管理器域管理，该管理器将这些秘密密封到物理 TPM 上。如果创建这些域（管理器、vTPM 和客户机）的过程是可信任的，则 vTPM 子系统可以将基于硬件 TPM 的信任链扩展到 Xen 中的虚拟机。vTPM 的每个主要组件都作为一个单独的域实现，确保了由虚拟机监视器提供的安全隔离。vTPM 域使用 mini-os 实现以减少内存和处理器开销。
此 mini-os vTPM 子系统是在 IBM 和英特尔公司之前完成的 vTPM 工作基础上构建的。
设计概述
---------------

下图描述了 vTPM 的架构：

```
+------------------+
|    Linux DomU    | ...
|       |  ^       |
|       v  |       |
|   xen-tpmfront   |
+------------------+
          |  ^
          v  |
+------------------+
| mini-os/tpmback  |
|       |  ^       |
|       v  |       |
|  vtpm-stubdom    | ...
|       |  ^       |
|       v  |       |
| mini-os/tpmfront |
+------------------+
          |  ^
          v  |
+------------------+
| mini-os/tpmback  |
|       |  ^       |
|       v  |       |
| vtpmmgr-stubdom  |
|       |  ^       |
|       v  |       |
| mini-os/tpm_tis  |
+------------------+
          |  ^
          v  |
+------------------+
|   Hardware TPM   |
+------------------+
```

* Linux DomU：
	* 使用 vTPM 的基于 Linux 的客户机。可能有多个此类客户机。
* xen-tpmfront.ko：
	* Linux 内核虚拟 TPM 前端驱动程序。此驱动程序为基于 Linux 的 DomU 提供 vTPM 访问功能。
* mini-os/tpmback：
	* mini-os TPM 后端驱动程序。Linux 前端驱动程序连接到此后端驱动程序以促进 Linux 客户机与其 vTPM 之间的通信。此驱动程序还被 vtpmmgr-stubdom 用来与 vtpm-stubdom 通信。
* vtpm-stubdom：
	* 实现 vTPM 的 mini-os 存根域。运行中的 vtpm-stubdom 实例与系统上的逻辑 vTPMs 之间存在一对一的映射关系。vTPM 平台配置寄存器（PCRs）通常都被初始化为零。
* mini-os/tpmfront：
	* mini-os TPM 前端驱动程序。vTPM mini-os 域 vtpm-stubdom 使用此驱动程序与 vtpmmgr-stubdom 通信。此驱动程序还用于如 pv-grub 等 mini-os 域，它们需要与 vTPM 域进行通信。
* vtpmmgr-stubdom:
    * 实现 vTPM 管理器的一个小型操作系统域。仅存在一个 vTPM 管理器，并且在整个机器的生命周期中都应该运行。该域负责管理对系统上物理 TPM 的访问，并确保每个 vTPM 的持久状态的安全。
* mini-os/tpm_tis:
    * 小型操作系统 TPM 版本 1.2 的 TPM 接口规范 (TIS) 驱动程序。此驱动程序由 vtpmmgr-stubdom 使用，以直接与硬件 TPM 进行通信。通信是通过将硬件内存页映射到 vtpmmgr-stubdom 中来实现的。
* 硬件 TPM:
    * 焊接在主板上的物理 TPM。

### 与 Xen 的集成

在 Xen 4.3 中使用 libxl 工具栈添加了对 vTPM 驱动程序的支持。有关设置 vTPM 和 vTPM 管理器 stub 域的详细信息，请参阅 Xen 文档（docs/misc/vtpm.txt）。一旦 stub 域开始运行，就可以像配置文件中的磁盘或网络设备一样设置 vTPM 设备。

为了使用诸如 IMA 这类需要在 initrd 之前加载 TPM 的功能，必须将 xen-tpmfront 驱动程序编译入内核。如果不使用此类功能，则可以将驱动程序作为模块编译，并按常规方式加载。
