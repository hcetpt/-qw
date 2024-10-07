SPDX 许可证标识符: (GPL-2.0-only 或 BSD-2-Clause)

====================================
Marvell OcteonTx2 RVU 内核驱动程序
====================================

版权所有 © 2020 Marvell International Ltd
目录
========

- `概述`_
- `驱动程序`_
- `基本数据包流`_
- `Devlink 健康报告器`_
- `服务质量`_

概述
========

Marvell 的 OcteonTX2 SOC 中的资源虚拟化单元（RVU）将网络、加密和其他功能块中的硬件资源映射为与 PCI 兼容的物理和虚拟功能。每个功能块又包含多个本地功能（LFs），用于分配给 PCI 设备。RVU 支持多个 PCIe SRIOV 物理功能（PFs）和虚拟功能（VFs）。PF0 被称为管理功能（AF），具有将 RVU 功能块的 LFs 分配给每个 PF/VF 的权限。

RVU 管理的网络功能块包括：
- 网络池或缓冲区分配器（NPA）
- 网络接口控制器（NIX）
- 网络解析 CAM（NPC）
- 调度/同步/排序单元（SSO）
- 环回接口（LBK）

RVU 管理的非网络功能块包括：
- 加密加速器（CPT）
- 定时器单元（TIM）
- 调度/同步/排序单元（SSO）
  用于网络和非网络用例

资源分配示例：
- 拥有 NIX-LF 和 NPA-LF 资源的 PF/VF 可作为纯网络设备工作
- 拥有 CPT-LF 资源的 PF/VF 可作为纯加密卸载设备工作

RVU 功能块可根据软件需求高度配置。固件在内核启动前设置以下内容：
- 根据物理链路数量启用所需数量的 RVU PFs
- 每个 PF 的 VF 数量可以在编译时静态设置或可配置
- 根据配置，固件将 VFs 分配给每个 PF
- 同时为每个 PF 和 VF 分配 MSIX 向量
- 这些配置在内核启动后不会改变
驱动程序
=======

Linux 内核将有多个驱动程序注册到 RVU 的不同 PF（物理功能）和 VF（虚拟功能）。关于网络方面，将有三种类型的驱动程序：

管理功能驱动程序
---------------------
如上所述，RVU 的 PF0 被称为管理功能（AF），该驱动程序支持资源分配和功能块配置。
不处理任何 I/O。它设置一些基本内容，但大部分功能是通过来自 PF 和 VF 的配置请求实现的。
PF/VF 通过共享内存区域（邮箱）与 AF 进行通信。接收到请求后，AF 将进行资源分配和其他硬件配置。
AF 始终连接到主机内核，但 PF 及其 VF 可能由主机内核使用，或连接到虚拟机或用户空间应用程序（如 DPDK 等）。因此，AF 必须处理来自任何域中的任何设备发送的资源分配/配置请求。
AF 驱动程序还与底层固件交互以：
- 管理物理以太网链路，即 CGX LMACs
- 获取信息，例如速度、双工模式、自动协商等
- 获取 PHY EEPROM 和统计信息
- 配置 FEC、PAM 模式等

从纯粹的网络角度来看，AF 驱动程序支持以下功能：
- 将物理链路映射到注册了 netdev 的 RVU PF
- 将 NIX 和 NPA 块的 LF 附加到 RVU PF/VF，这些 LF 提供用于常规网络功能的缓冲池、接收队列（RQs）和发送队列（SQs）
- 流量控制（暂停帧）的启用/禁用/配置
- 硬件PTP时间戳相关配置
- NPC解析器配置文件，基本上是如何解析数据包以及提取哪些信息
- NPC提取配置文件，从数据包中提取什么信息以匹配MCAM条目中的数据
- 管理NPC的MCAM条目，根据请求可以构建并安装所需的包转发规则
- 定义接收端扩展（RSS）算法
- 定义分段卸载算法（例如TSO）
- VLAN剥离、捕获和插入配置
- 提供数据包调度支持的SSO和TIM模块配置
- 调试文件系统（Debugfs）支持，用于检查当前资源分配情况、NPA池的状态、NIX请求队列（RQ）、发送队列（SQ）和完成队列（CQ），以及各种统计数据等，有助于调试问题
- 以及更多功能
物理功能驱动（Physical Function driver）
------------------------

此RVU物理功能（PF）处理I/O，映射到一个物理以太网链路，并且该驱动注册了一个网络设备（netdev）。它支持SR-IOV。如上所述，这个驱动通过邮箱与AF通信。为了从物理链路获取信息，此驱动与AF通信，而AF则从固件中获取这些信息并作出响应，即不能直接与固件通信。
此外，它支持使用ethtool配置链路、RSS、队列数量、队列大小、流控制、n元组过滤器、转储PHY EEPROM、配置FEC等。

虚拟功能驱动（Virtual Function driver）
-----------------------

有两种类型的虚拟功能（VF）：一种是与其父级SR-IOV PF共享物理链路的VF；另一种是通过内部硬件环回通道（LBK）成对工作的VF。

类型1：
- 这些VF及其父级PF共享一个物理链路，用于外部通信。
- VF不能直接与AF通信，它们发送邮箱消息给PF，PF再转发给AF。AF处理后，将响应返回给PF，PF再将回复转发给VF。
- 从功能角度来看，PF和VF之间没有区别，因为它们都连接了相同类型的硬件资源。但是用户只能通过PF配置某些内容，因为PF被视为链路的所有者/管理员。

类型2：
- RVU PF0（即管理功能）创建这些VF，并将其映射到环回块的通道上。
- 一对VF（例如VF0和VF1，VF2和VF3等）作为一组工作，即从VF0发出的数据包会被VF1接收，反之亦然。
- 这些VF可以被应用程序或虚拟机用来在它们之间进行通信，而无需将流量发送到外部。由于硬件中没有交换机，因此支持环回VF。
- 这些VF通过邮箱直接与AF（PF0）通信。
除了用于接收和传输数据包的IO通道或链路外，这些VF类型之间没有其他区别。AF驱动程序负责处理IO通道映射，因此相同的VF驱动程序适用于这两种类型的设备。

基本的数据包流程
=================

入站
----

1. CGX LMAC 接收数据包
2. 将数据包转发到NIX模块
3. 然后提交到NPC模块进行解析，并通过MCAM查找获取目标RVU设备
4. 与目标RVU设备关联的NIX LF从NPA模块LF的RQ映射缓冲池中分配一个缓冲区
5. RQ 可能由RSS选择，或者通过配置带有RQ编号的MCAM规则来选择
6. 数据包通过DMA传送，并通知驱动程序

出站
----

1. 驱动程序准备发送描述符并提交到SQ以进行传输
2. SQ已经由AF配置为在特定的链路/通道上进行传输
3. SQ描述符环维护在从NPA模块LF的SQ映射缓冲池中分配的缓冲区内
4. NIX 块在指定信道上转发数据包（pkt）
5. NPC MCAM 条目可以安装以将数据包（pkt）重定向到不同的信道

Devlink 健康报告器
==================

NPA 报告器
-------------

NPA 报告器负责报告和恢复以下错误组：

1. **GENERAL 事件**

   - 由于操作未映射的 PF 引发的错误
   - 由于其他硬件块（NIX、SSO、TIM、DPI 和 AURA）禁用分配/释放操作引发的错误

2. **ERROR 事件**

   - 由于读取 NPA_AQ_INST_S 或写入 NPA_AQ_RES_S 引发的故障
   - AQ 门铃错误

3. **RAS 事件**

   - 对于 NPA_AQ_INST_S/NPA_AQ_RES_S 的 RAS 错误报告

4. **RVU 事件**

   - 由于未映射槽位引发的错误

示例输出：

```
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
```

每个报告器会记录以下内容：

- 错误类型
- 错误寄存器值
- 文字描述的原因

例如：

```
~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_gen
NPA_AF_GENERAL:
        NPA General Interrupt Reg : 1
        NIX0: 禁用 RX 的释放操作
~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_intr
NPA_AF_RVU:
        NPA RVU Interrupt Reg : 1
        未映射槽位错误
~# devlink health dump show  pci/0002:01:00.0 reporter hw_npa_err
NPA_AF_ERR:
       NPA Error Interrupt Reg : 4096
       AQ 门铃错误
```

NIX 报告器
-------------

NIX 报告器负责报告和恢复以下错误组：

1. **GENERAL 事件**

   - 由于缓冲区不足导致的接收镜像/多播数据包丢弃
   - SMQ 刷新操作
### 2. 错误事件

   - 由于从多播/镜像缓冲区读写 WQE 导致的内存故障
   - 接收多播/镜像复制列表错误
   - 在未映射的 PF 上接收数据包
   - 由于读取 NIX_AQ_INST_S 或写入 NIX_AQ_RES_S 导致的故障
   - AQ 门铃错误

### 3. RAS 事件

   - 对 NIX 接收多播/镜像条目结构的 RAS 错误报告
   - 对从多播/镜像缓冲区读取 WQE/数据包数据的 RAS 错误报告
   - 对 NIX_AQ_INST_S/NIX_AQ_RES_S 的 RAS 错误报告

### 4. RVU 事件

   - 由于未映射槽位导致的错误

#### 示例输出：

```
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

每个 reporter 输出以下信息：

- 错误类型
- 错误寄存器值
- 文字描述的原因

例如：

```
```
~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_intr
NIX_AF_RVU:
        NIX RVU 中断寄存器 : 1
        未映射槽位错误
~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_gen
NIX_AF_GENERAL:
        NIX 通用中断寄存器 : 1
        接收多播数据包丢弃
~# devlink health dump show pci/0002:01:00.0 reporter hw_nix_err
NIX_AF_ERR:
        NIX 错误中断寄存器 : 64
        在未映射的 PF_FUNC 上接收数据包
```

### 服务质量
#### 硬件调度算法

Octeon TX2 芯片和 CN10K 发送接口包含五个发送级别，从 SMQ/MDQ 到 TL4 再到 TL1。每个数据包将遍历 MDQ、TL4 到 TL1 各个级别。每个级别包含一个队列数组以支持调度和整形。
硬件根据调度队列的优先级使用以下算法：
一旦用户创建了具有不同优先级的TC类，驱动程序就会为分配给该类的调度器配置指定的优先级以及速率限制设置。
1. 严格优先级

    - 一旦报文提交到MDQ，硬件会根据严格优先级选择所有具有不同优先级的活动MDQ。
2. 轮询（Round Robin）

    - 具有相同优先级级别的活动MDQ使用轮询方式选择。

设置HTB卸载
------------

1. 在接口上启用硬件TC卸载：

        # ethtool -K <interface> hw-tc-offload on

2. 创建HTB根：

        # tc qdisc add dev <interface> clsact
        # tc qdisc replace dev <interface> root handle 1: htb offload

3. 创建具有不同优先级的TC类：

        # tc class add dev <interface> parent 1: classid 1:1 htb rate 10Gbit prio 1

        # tc class add dev <interface> parent 1: classid 1:2 htb rate 10Gbit prio 7

4. 创建具有相同优先级但不同量子大小（quantum）的TC类：

        # tc class add dev <interface> parent 1: classid 1:1 htb rate 10Gbit prio 2 quantum 409600

        # tc class add dev <interface> parent 1: classid 1:2 htb rate 10Gbit prio 2 quantum 188416

        # tc class add dev <interface> parent 1: classid 1:3 htb rate 10Gbit prio 2 quantum 32768
