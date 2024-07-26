SPDX 许可证标识符：(GPL-2.0-only 或 BSD-2-Clause)

====================================
Marvell OcteonTx2 RVU 内核驱动程序
====================================

版权所有 © 2020 Marvell International Ltd
内容
========

- `概述`_
- `驱动程序`_
- `基本数据包流程`_
- `Devlink 健康报告器`_
- `服务质量`_

概述
========

Marvell 的 OcteonTX2 SOC 中的资源虚拟化单元 (RVU) 将来自网络、加密和其他功能块的硬件资源映射为与 PCI 兼容的物理和虚拟功能。每个功能块又有多个本地功能 (LF)，用于配置给 PCI 设备。RVU 支持多个 PCIe SRIOV 物理功能 (PF) 和虚拟功能 (VF)。PF0 被称为管理/管理员功能 (AF)，并具有权限将 RVU 功能块的 LF 分配给每个 PF/VF。

RVU 管理的网络功能块包括：
- 网络池或缓冲分配器 (NPA)
- 网络接口控制器 (NIX)
- 网络解析 CAM (NPC)
- 调度/同步/排序单元 (SSO)
- 环回接口 (LBK)

RVU 管理的非网络功能块包括：
- 加密加速器 (CPT)
- 定时器单元 (TIM)
- 调度/同步/排序单元 (SSO)
  - 用于网络和非网络应用场景

资源配置示例：
- 具有 NIX-LF 和 NPA-LF 资源的 PF/VF 作为纯网络设备运行
- 具有 CPT-LF 资源的 PF/VF 作为纯加密卸载设备运行
RVU 功能块可根据软件需求高度自定义。
在内核启动前，固件会设置以下内容：
- 根据物理链路的数量启用所需的 RVU PF 数量
- 每个 PF 的 VF 数量是静态的或编译时可配置的
  - 根据配置，固件为每个 PF 分配 VF
- 也为每个 PF 和 VF 分配 MSIX 向量
- 这些设置在内核启动后不会改变
### 驱动程序

#### Linux 内核将有多个驱动程序注册到 RVU 的不同 PF 和 VF。

关于网络方面，会有三种类型的驱动程序：

#### 管理功能驱动程序

如上所述，RVU 的 PF0 被称为管理功能（AF），此驱动程序支持资源分配和功能块配置，并不处理任何 I/O。它会设置一些基本内容，但大部分功能是通过来自 PF 和 VF 的配置请求来实现的。
PF 和 VF 通过共享内存区域（邮箱）与 AF 进行通信。接收到请求后，AF 将进行资源分配和其他硬件配置。
AF 始终连接到主机内核，而 PF 及其 VF 可能被主机内核本身使用，或者连接到虚拟机或用户空间应用程序（例如 DPDK 等）。因此，AF 必须处理来自任何域中任何设备的配置/分配请求。
AF 驱动程序还与底层固件进行交互以实现以下功能：
- 管理物理以太网链路，即 CGX LMAC
- 获取信息，如速度、双工模式、自动协商等
- 获取 PHY EEPROM 和统计信息
- 配置 FEC、PAM 模式等

从纯粹的网络角度来看，AF 驱动程序支持以下功能：
- 将一个物理链路映射到已注册网络设备的 RVU PF
- 将 NIX 和 NPA 块的 LF 连接到 RVU PF/VF，为常规网络功能提供缓冲池、接收队列（RQ）、发送队列（SQ）等。
- 流控制（暂停帧）的启用/禁用/配置
- 硬件PTP时间戳相关配置
- NPC解析器配置文件配置，基本上是如何解析数据包以及提取哪些信息
- NPC提取配置文件配置，从数据包中提取什么信息以匹配MCAM条目中的数据
- 管理NPC的MCAM条目，根据请求可以构建并安装所需的包转发规则
- 定义接收端扩展（RSS）算法
- 定义分段卸载算法（例如TSO）
- VLAN剥离、捕获和插入配置
- SSO和TIM模块配置，提供数据包调度支持
- Debugfs支持，用于检查当前资源分配情况、NPA池的当前状态、NIX请求队列(RQ)、发送队列(SQ)和完成队列(CQ)，以及各种统计数据等，有助于问题调试
- 以及更多功能
### 物理功能驱动
------------------------

此RVU物理功能（PF）处理I/O操作，映射到一个物理以太网链路，并且该驱动注册了一个网络设备。这支持SR-IOV技术。如上所述，该驱动通过邮箱与适配器前端（AF）进行通信。为了从物理链路获取信息，此驱动与AF对话，而AF则从固件中获取这些信息并作出响应，即不能直接与固件通信。
该驱动支持使用ethtool配置链路、RSS、队列数量、队列大小、流控制、n-tuple过滤器、转储PHY EEPROM、配置FEC等功能。

### 虚拟功能驱动
-----------------------

存在两种类型的虚拟功能（VF）：一种与它们的父级SR-IOV PF共享物理链路；另一种则成对工作，利用内部硬件环回通道（LBK）。

**类型1:**
- 这些VF及其父级PF共享一个物理链路，用于外部通信。
- VF不能直接与AF通信，它们向PF发送邮箱消息，然后PF转发给AF。AF处理后，将响应返回给PF，再由PF转发给VF。
- 从功能角度来看，PF和VF之间没有区别，因为它们都连接了相同类型的硬件资源。但是用户只能从PF配置一些设置，因为PF被视为链接的所有者/管理员。

**类型2:**
- RVU PF0（即管理功能）创建这些VF，并将其映射到环回块的通道上。
- 两个VF（如VF0与VF1、VF2与VF3等）成对工作，即从VF0发出的数据包会被VF1接收，反之亦然。
- 这些VF可以被应用程序或虚拟机用来在它们之间进行通信，而无需将流量发送到外部。硬件中不存在交换机，因此支持环回VF。
- 这些VF通过邮箱直接与AF（PF0）通信。
除了用于接收和传输数据包的I/O通道或链接之外，这些VF类型之间没有其他区别。AF驱动程序负责处理I/O通道映射，因此同一VF驱动程序适用于这两种类型的设备。

基本的数据包流程
================

**入站**
--------

1. CGX LMAC接收数据包。
2. 将数据包转发至NIX模块。
3. 然后提交到NPC模块进行解析，随后通过MCAM查找以获取目标RVU设备。
4. 与目标RVU设备相连的NIX LF从NPA模块LF映射的RQ缓冲池中分配一个缓冲区。
5. RQ可能由RSS选择，或者通过配置带有RQ编号的MCAM规则来选择。
6. 数据包通过DMA传输，并通知驱动程序。

**出站**
--------

1. 驱动程序准备发送描述符并提交给SQ以进行传输。
2. SQ已经由AF配置好，以便在特定的链路/通道上进行传输。
3. SQ描述符环被维护在NPA模块LF映射的缓冲池中分配的缓冲区内。
### NIX块在指定信道上转发数据包
### NPC多播内存条目可以被安装以将数据包转向不同的信道

#### Devlink健康报告器

**NPA报告器**

NPA报告器负责报告和恢复以下错误组：

1. **GENERAL事件**

   - 由于未映射PF的操作导致的错误
   - 由于其他硬件块（NIX、SSO、TIM、DPI 和 AURA）的分配/释放功能被禁用而导致的错误
2. **ERROR事件**

   - 由于读取NPA_AQ_INST_S或写入NPA_AQ_RES_S而导致的故障
   - AQ门铃错误
3. **RAS事件**

   - 对于NPA_AQ_INST_S/NPA_AQ_RES_S的RAS错误报告
4. **RVU事件**

   - 由于未映射槽位导致的错误

示例输出：

    ~# devlink health
    pci/0002:01:00.0:
      reporter hw_npa_intr
          state healthy error 2872 recover 2872 last_dump_date 2020-12-10 last_dump_time 09:39:09 grace_period 0 auto_recover true auto_dump true
      reporter hw_npa_gen
          state healthy error 2872 recover 2872 last_dump_date 2020-12-11 last_dump_time 04:43:04 grace_period 0 auto_recover true auto_dump true
      reporter hw_npa_err
          state healthy error 2871 recover 2871 last_dump_date 2020-12-10 last_dump_time 09:39:17 grace_period 0 auto_recover true auto_dump true
       reporter hw_npa_ras
          state healthy error 0 recover 0 last_dump_date 2020-12-10 last_dump_time 09:32:40 grace_period 0 auto_recover true auto_dump true

每个报告器记录

- 错误类型
- 错误寄存器值
- 文字描述的原因

例如：

    ~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_gen
     NPA_AF_GENERAL:
             NPA General Interrupt Reg : 1
             NIX0: RX缓冲区释放功能禁用
    ~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_intr
     NPA_AF_RVU:
             NPA RVU Interrupt Reg : 1
             未映射槽位错误
    ~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_err
     NPA_AF_ERR:
            NPA Error Interrupt Reg : 4096
            AQ门铃错误

**NIX报告器**

NIX报告器负责报告和恢复以下错误组：

1. **GENERAL事件**

   - 由于接收镜像/多播数据包时缓冲区不足而导致的数据包丢弃
   - SMQ刷新操作
### 错误 (ERROR) 事件

- 因从多播/镜像缓冲区读写工作队列元素 (WQE) 而导致的内存故障
- 接收多播/镜像复制列表错误
- 在未映射的物理功能 (PF) 上接收数据包
- 因读取 NIX_AQ_INST_S 或写入 NIX_AQ_RES_S 导致的故障
- AQ 门铃错误

### 可靠性、可用性和可服务性 (RAS) 事件

- 对于 NIX 接收多播/镜像条目的 RAS 错误报告
- 对于从多播/镜像缓冲区读取 WQE/数据包数据的 RAS 错误报告
- 对于 NIX_AQ_INST_S/NIX_AQ_RES_S 的 RAS 错误报告

### RVU 事件

- 由于未映射插槽而产生的错误

### 示例输出:

```plaintext
~# ./devlink health
pci/0002:01:00.0:
  reporter hw_npa_intr
    state healthy error 0 recover 0 grace_period 0 auto_recover true auto_dump true
  reporter hw_npa_gen
    state healthy error 0 recover 0 grace_period 0 auto_recover true auto_dump true
  reporter hw_npa_err
    state healthy error 0 recover 0 grace_period 0 auto_recover true auto_dump true
  reporter hw_npa_ras
    state healthy error 0 recover 0 grace_period 0 auto_recover true auto_dump true
  reporter hw_nix_intr
    state healthy error 1121 recover 1121 last_dump_date 2021-01-19 last_dump_time 05:42:26 grace_period 0 auto_recover true auto_dump true
  reporter hw_nix_gen
    state healthy error 949 recover 949 last_dump_date 2021-01-19 last_dump_time 05:42:43 grace_period 0 auto_recover true auto_dump true
  reporter hw_nix_err
    state healthy error 1147 recover 1147 last_dump_date 2021-01-19 last_dump_time 05:42:59 grace_period 0 auto_recover true auto_dump true
  reporter hw_nix_ras
    state healthy error 409 recover 409 last_dump_date 2021-01-19 last_dump_time 05:43:16 grace_period 0 auto_recover true auto_dump true

每个报告器会输出：

- 错误类型
- 错误寄存器值
- 文字形式的原因

例如：

~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_intr
 NIX_AF_RVU:
        NIX RVU 中断寄存器 : 1
        未映射插槽错误
~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_gen
 NIX_AF_GENERAL:
        NIX 通用中断寄存器 : 1
        接收多播数据包丢弃
~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_err
 NIX_AF_ERR:
        NIX 错误中断寄存器 : 64
        在未映射的 PF_FUNC 上接收
```

### 服务质量

#### 硬件调度算法

Octeon TX2 芯片和 CN10K 发送接口包含五个发送级别，从 SMQ/MDQ 到 TL1。每个数据包都会经过 MDQ、TL4 到 TL1 级别。每个级别包含一个队列数组以支持调度和整形。
硬件根据调度队列的优先级使用以下算法：
一旦用户创建了具有不同优先级的TC类，驱动程序就会根据指定的优先级配置分配给该类的调度器，并进行速率限制配置。
1. 严格优先级

      - 当数据包提交到MDQ后，硬件会根据严格优先级选择所有具有不同优先级的活动MDQ。
2. 轮询（Round Robin）

      - 具有相同优先级级别的活动MDQ采用轮询方式选择。
设置HTB卸载
---------------

1. 在接口上启用硬件TC卸载：

        # ethtool -K <接口名> hw-tc-offload on

2. 创建HTB根：

        # tc qdisc add dev <接口名> clsact
        # tc qdisc replace dev <接口名> root handle 1: htb offload

3. 创建具有不同优先级的TC类：

        # tc class add dev <接口名> parent 1: classid 1:1 htb rate 10Gbit prio 1

        # tc class add dev <接口名> parent 1: classid 1:2 htb rate 10Gbit prio 7

4. 创建具有相同优先级但不同量子值的TC类：

        # tc class add dev <接口名> parent 1: classid 1:1 htb rate 10Gbit prio 2 quantum 409600

        # tc class add dev <接口名> parent 1: classid 1:2 htb rate 10Gbit prio 2 quantum 188416

        # tc class add dev <接口名> parent 1: classid 1:3 htb rate 10Gbit prio 2 quantum 32768
