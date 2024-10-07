=============================
Xen 的虚拟 TPM 接口
=============================

作者：Matthew Fioravante（JHUAPL），Daniel De Graaf（NSA）

本文档描述了 Xen 中的虚拟可信平台模块（vTPM）子系统。假设读者熟悉构建和安装 Xen、Linux，并且对 TPM 和 vTPM 概念有基本了解。

介绍
------------

本工作的目标是为虚拟客户操作系统（在 Xen 术语中，称为 DomU）提供 TPM 功能。这使得程序可以在虚拟系统中与 TPM 进行交互，就像在物理系统中一样。每个客户机都有一个独特的、模拟的软件 TPM。然而，每个 vTPM 的秘密（密钥、NVRAM 等）由一个 vTPM 管理域管理，该管理域将这些秘密密封到物理 TPM 上。如果创建这些域（管理、vTPM 和客户机）的过程是受信任的，则 vTPM 子系统将硬件 TPM 根植的信任链扩展到了 Xen 中的虚拟机。vTPM 的每个主要组件作为一个独立的域实现，由虚拟机监控程序保证安全隔离。vTPM 域在 mini-os 中实现以减少内存和处理器开销。
这个 mini-os vTPM 子系统建立在 IBM 和 Intel 公司之前的 vTPM 工作基础上。

设计概述
---------------

vTPM 的架构如下所示：

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
            希望使用 vTPM 的基于 Linux 的客户机。可能有多个这样的客户机。
* xen-tpmfront.ko：
              Linux 内核虚拟 TPM 前端驱动程序。此驱动程序为基于 Linux 的 DomU 提供 vTPM 访问。
* mini-os/tpmback：
              mini-os 的 TPM 后端驱动程序。Linux 前端驱动程序连接到此后端驱动程序，以促进 Linux DomU 和其 vTPM 之间的通信。此驱动程序还被 vtpmmgr-stubdom 用来与 vtpm-stubdom 通信。
* vtpm-stubdom：
             实现 vTPM 的 mini-os 存根域。运行中的 vtpm-stubdom 实例与系统上的逻辑 vTPMs 之间存在一对一的映射关系。vTPM 平台配置寄存器（PCRs）通常都初始化为零。
* mini-os/tpmfront：
              mini-os 的 TPM 前端驱动程序。vTPM mini-os 域 vtpm-stubdom 使用此驱动程序与 vtpmmgr-stubdom 通信。此驱动程序还用于 mini-os 域，如 pv-grub，这些域与 vTPM 域进行通信。
* vtpmmgr-stubdom：
    实现 vTPM 管理器的小型操作系统域。只有一个 vTPM 管理器，并且在整个机器生命周期中都应该运行。此域负责管理对系统上物理 TPM 的访问，并保护每个 vTPM 的持久状态。

* mini-os/tpm_tis：
    小型操作系统 TPM 版本 1.2 的 TPM 接口规范（TIS）驱动程序。该驱动程序由 vtpmmgr-stubdom 使用，直接与硬件 TPM 通信。通信通过将硬件内存页面映射到 vtpmmgr-stubdom 来实现。

* Hardware TPM：
    焊接在主板上的物理 TPM。

### 与 Xen 的集成

Xen 4.3 中使用 libxl 工具栈添加了对 vTPM 驱动程序的支持。有关设置 vTPM 和 vTPM 管理器 stub 域的详细信息，请参阅 Xen 文档（docs/misc/vtpm.txt）。一旦 stub 域启动并运行，可以在域的配置文件中像设置磁盘或网络设备一样设置一个 vTPM 设备。

为了使用需要在 initrd 之前加载 TPM 的功能（如 IMA），必须将 xen-tpmfront 驱动程序编译进内核。如果不使用此类功能，可以将驱动程序作为模块编译，并按常规方式加载。
