=============================
Xen 的虚拟可信平台模块接口
=============================

作者：Matthew Fioravante（JHUAPL），Daniel De Graaf（NSA）

本文档描述了 Xen 的虚拟可信平台模块（vTPM）子系统。读者应熟悉构建和安装 Xen、Linux，并对 TPM 和 vTPM 概念有基本的了解。

介绍
------------

本工作的目标是为虚拟客户操作系统（在 Xen 术语中称为 DomU）提供 TPM 功能。这使得程序可以在虚拟系统中与 TPM 交互，就像在物理系统上一样。每个客户都有一个唯一的、模拟的软件 TPM。然而，每个 vTPM 的秘密（密钥、NVRAM 等）由一个 vTPM 管理域管理，并且这些秘密被密封到物理 TPM 上。如果创建这些域（管理器、vTPM 和客户）的过程是可信的，则 vTPM 子系统将信任链从硬件 TPM 扩展到 Xen 中的虚拟机。vTPM 的每个主要组件都作为一个单独的域实现，由虚拟机监控程序保证安全隔离。vTPM 域是在 mini-os 中实现的，以减少内存和处理器开销。
这个 mini-os vTPM 子系统是在 IBM 和 Intel 公司之前的工作基础上构建的。

设计概述
---------------

vTPM 的架构如下所示：

```
+------------------+
|    Linux DomU    | ..
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
|  vtpm-stubdom    | ..
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
            基于 Linux 的客户机，希望使用 vTPM。可能有多个这样的客户机。
* xen-tpmfront.ko：
                Linux 内核虚拟 TPM 前端驱动。此驱动程序为基于 Linux 的 DomU 提供 vTPM 访问功能。
* mini-os/tpmback：
                mini-os 的 TPM 后端驱动。Linux 前端驱动连接到此后端驱动，以促进 Linux DomU 和其 vTPM 之间的通信。此驱动也被 vtpmmgr-stubdom 使用来与 vtpm-stubdom 通信。
* vtpm-stubdom：
                实现 vTPM 的 mini-os 存根域。运行中的 vtpm-stubdom 实例与系统上的逻辑 vTPM 之间存在一对一映射关系。vTPM 平台配置寄存器（PCRs）通常初始化为零。
* mini-os/tpmfront：
                mini-os 的 TPM 前端驱动。vTPM mini-os 域 vtpm-stubdom 使用此驱动程序与 vtpmmgr-stubdom 通信。此驱动也在 mini-os 域（如 pv-grub）中使用，这些域与 vTPM 域进行通信。
* vtpmmgr-stubdom：
    一个实现了vTPM管理器的小型操作系统域。整个系统中只有一个vTPM管理器，并且它应该在整个机器生命周期内运行。该域负责管理对系统上物理TPM的访问，并确保每个vTPM的持久状态的安全。
* mini-os/tpm_tis：
    小型操作系统的TPM 1.2版本TPM接口规范（TIS）驱动程序。此驱动程序由vtpmmgr-stubdom使用，直接与硬件TPM通信。通信通过将硬件内存页面映射到vtpmmgr-stubdom来实现。
* 硬件TPM：
    焊接在主板上的物理TPM。

### 与Xen的集成

在Xen 4.3版本中，使用libxl工具栈添加了对vTPM驱动程序的支持。有关设置vTPM和vTPM管理器存根域的详细信息，请参阅Xen文档（docs/misc/vtpm.txt）。一旦存根域启动并运行，就可以像配置文件中的磁盘或网络设备一样设置vTPM设备。

为了使用需要在initrd之前加载TPM的功能（如IMA），xen-tpmfront驱动程序必须编译进内核。如果不使用此类功能，可以将驱动程序作为模块编译，并按常规方式加载。
