SPDX 许可证标识符: GPL-2.0

==================
英特尔 IPU6 驱动程序
==================

作者: 曹炳部 <bingbu.cao@intel.com>

概述
=========

英特尔 IPU6 是第六代英特尔图像处理单元，在一些英特尔芯片组中使用，如 Tiger Lake、Jasper Lake、Alder Lake、Raptor Lake 和 Meteor Lake。IPU6 包含两个主要系统：输入系统（ISYS）和处理系统（PSYS）。在 PCI 总线上，IPU6 作为单一设备可见，可以通过 `lspci` 命令找到：

``0000:00:05.0 多媒体控制器: 英特尔公司 设备 xxxx (版本 xx)``

IPU6 在 PCI 配置空间中为 MMIO 寄存器分配了 16MB 的基址寄存器空间，该空间对驱动程序可见。

Buttress
=========

IPU6 通过 Buttress 连接到系统结构，使主机驱动程序能够控制 IPU6，并允许 IPU6 访问系统内存以存储和加载帧像素流及其他任何元数据。
Buttress 主要管理几个系统功能：电源管理、中断处理、固件验证和全局定时同步。

ISYS 和 PSYS 的电源流程
------------------------

IPU6 驱动程序通过设置 Buttress 中的 ISYS 和 PSYS 频率控制寄存器（`IPU6_BUTTRESS_REG_IS_FREQ_CTL` 和 `IPU6_BUTTRESS_REG_PS_FREQ_CTL`）来初始化 ISYS 和 PSYS 的电源上电或下电请求。

Buttress 将此请求转发给 Punit，在 Punit 执行电源上电流程后，Buttress 通过更新电源状态寄存器来指示驱动程序 ISYS 或 PSYS 已经上电。

.. Note:: 由于硬件限制，ISYS 上电必须先于 PSYS 上电，ISYS 下电必须在 PSYS 下电之后进行。

中断
---------

IPU6 的中断可以生成为 MSI 或 INTA 形式。当 ISYS、PSYS、Buttress 发生事件或错误时将触发中断。驱动程序可以通过读取中断状态寄存器 `BUTTRESS_REG_ISR_STATUS` 来获取中断原因，清除中断状态后调用特定的 ISYS 或 PSYS 中断处理函数。

.. c:function:: irqreturn_t ipu6_buttress_isr(int irq, ...)

安全性和固件验证
-------------------------------------

为了应对 IPU6 固件的安全问题，IPU6 固件在被允许在 IPU6 内部处理器上执行之前需要经过一个验证过程。IPU6 驱动程序将与集成安全引擎 (CSE) 协作完成验证过程。CSE 负责验证 IPU6 固件。已验证的固件二进制文件被复制到一个隔离的内存区域。固件验证过程由 CSE 实现，并与 IPU6 驱动程序通过 IPC 握手进行通信。有一些 Buttress 寄存器被 CSE 和 IPU6 驱动程序用于通过 IPC 相互沟通。

.. c:function:: int ipu6_buttress_authenticate(...)

全局定时同步
-----------------

每当启动摄像头操作时，IPU6 驱动程序都会启动 Hammock Harbor 同步流程。IPU6 会在 Buttress 中同步一个内部计数器与 SoC 时间的副本，这个计数器会一直保持最新的时间直到摄像头操作停止。IPU6 驱动程序可以利用这个时间计数器根据从固件响应事件中的时间戳来校准时间戳。

.. c:function:: int ipu6_buttress_start_tsc_sync(...)

DMA 和 MMU
============

IPU6 拥有其自身的标量处理器，固件在其上运行，并且有一个内部的 32 位虚拟地址空间。IPU6 具有 MMU 地址转换硬件，使得标量处理器能够通过 IPU6 虚拟地址访问内部内存和外部系统内存。地址转换基于存储在系统内存中的两级页表，这些页表由 IPU6 驱动程序维护。IPU6 驱动程序将一级页表基地址设置到 MMU 寄存器，并允许 MMU 执行页表查找。

IPU6 驱动程序提供了自己的 DMA 操作。对于每次 DMA 操作，IPU6 驱动程序都会更新页表条目并在每次解除映射和释放后使 MMU TLB 无效。
下面是提供的英文内容翻译成中文的结果：

```plaintext
代码区块:: none

    常量结构 dma_map_ops ipu6_dma_ops = {
       .alloc = ipu6_dma_alloc,
       .free = ipu6_dma_free,
       .mmap = ipu6_dma_mmap,
       .map_sg = ipu6_dma_map_sg,
       .unmap_sg = ipu6_dma_unmap_sg,
       ..
};

.. 注意:: IPU6 MMU 在 IOMMU 后面工作，因此对于每个 IPU6 DMA 操作，驱动程序将调用通用的 PCI DMA 操作来请求 IOMMU 进行额外的映射，如果启用了 VT-d。

固件文件格式
=============

IPU6 固件采用 Code Partition Directory (CPD) 文件格式。CPD 固件包含一个 CPD 头、多个 CPD 条目和组件。CPD 组件包括 3 个条目 - 表明、元数据和模块数据。表明和元数据由 CSE 定义，并用于 CSE 认证。模块数据是 IPU6 特定的，其中包含固件二进制数据（称为包目录）。IPU6 驱动程序（特别是 `ipu6-cpd.c`）解析并验证 CPD 固件文件，并获取 IPU6 固件的包目录二进制数据，将其复制到特定的 DMA 缓冲区，并将其基地址设置为 Buttress 的 `FW_SOURCE_BASE` 寄存器。最后，CSE 将对这个固件二进制进行认证。
系统通信接口
=============

IPU6 驱动程序通过 Syscom ABI 与固件进行通信。Syscom 是 IPU 标量处理器与 CPU 之间的处理器间通信机制。存在许多固件和软件共享的资源：
- 系统内存区域，其中驻留消息队列，固件可以通过 IPU MMU 访问该内存区域。
- Syscom 队列为固定深度的先进先出队列，具有可配置数量的令牌（消息）。
- 也存在共同的 IPU6 MMIO 寄存器，其中存储了队列的读写索引。软件和固件作为队列中令牌的生产者和消费者，并在发送或接收每条消息时分别更新写入和读取索引。
在与固件开始通信之前，IPU6 驱动程序必须准备并配置输入和输出队列的数量、每个队列中的令牌计数以及每个令牌的大小。固件和软件必须使用相同的配置。IPU6 Buttress 具有若干固件启动参数寄存器，可用于存储配置地址并初始化 Syscom 状态，然后驱动程序可以通过设置标量处理器控制状态寄存器来请求固件启动并运行。
输入系统
==========

IPU6 输入系统包括 MIPI D-PHY 和多个 CSI-2 接收器。它可以捕获来自摄像头传感器或其他 MIPI CSI-2 输出设备的图像像素数据。
D-PHY 和 CSI-2 端口通道映射
-----------------------------------

IPU6 在不同的 SoC 上集成了不同的 D-PHY IP，在 Tiger Lake 和 Alder Lake 上，IPU6 集成了 MCD10 D-PHY；IPU6SE 在 Jasper Lake 上集成了 JSL D-PHY；而 IPU6EP 在 Meteor Lake 上集成了 Synopsys DWC D-PHY。在 D-PHY 和 CSI-2 接收器控制器之间有一个附加层，它包括端口配置、D-PHY 的 PHY 包装器或私有测试接口。有三个 D-PHY 驱动程序 `ipu6-isys-mcd-phy.c`、`ipu6-isys-jsl-phy.c` 和 `ipu6-isys-dwc-phy.c` 分别用于编程 IPU6 中的上述三种 D-PHY。
不同版本的 IPU6 具有不同的 D-PHY 通道映射：在 Tiger Lake 上，有 12 条数据通道和 8 条时钟通道，IPU6 支持最多 8 个 CSI-2 端口，有关更多信息，请参阅 `ipu6-isys-mcd-phy.c` 中的 PPI 映射。在 Jasper Lake 和 Alder Lake 上，D-PHY 有 8 条数据通道和 4 条时钟通道，IPU6 支持最多 4 个 CSI-2 端口。对于 Meteor Lake，D-PHY 有 12 条数据通道和 6 条时钟通道，因此 IPU6 支持最多 6 个 CSI-2 端口。
.. 注意:: 每一对 CSI-2 端口是一个可以共享数据通道的单个单元。例如，对于 CSI-2 端口 0 和 1，CSI-2 端口 0 最多支持 4 条数据通道，CSI-2 端口 1 最多支持 2 条数据通道，CSI-2 端口 0 使用 2 条数据通道可以与 CSI-2 端口 1 使用 2 条数据通道一起工作。如果尝试使用带有 4 条通道的 CSI-2 端口 0，则 CSI-2 端口 1 将不可用，因为这 4 条数据通道被 CSI-2 端口 0 和 1 共享。同样适用于 CSI 端口 2/3、4/5 和 7/8。
```
ISYS 固件 ABIs
--------------

IPU6 固件实现了一系列的 ABI 供软件访问。通常情况下，软件首先准备好流配置 `struct ipu6_fw_isys_stream_cfg_data_abi` 并通过发送 `STREAM_OPEN` 命令将配置发送给固件。流配置包括输入端口和输出端口；输入端口 `struct ipu6_fw_isys_input_pin_info_abi` 定义了输入源的分辨率和数据类型；输出端口 `struct ipu6_fw_isys_output_pin_info_abi` 定义了输出分辨率、步长及帧格式等。

一旦驱动程序从固件那里接收到指示流成功打开的中断，驱动程序就会发送 `STREAM_START` 和 `STREAM_CAPTURE` 命令请求固件开始捕获图像帧。`STREAM_CAPTURE` 命令将缓冲区队列发送给固件 (`struct ipu6_fw_isys_frame_buff_set`)，然后软件等待来自固件的中断和响应，`PIN_DATA_READY` 表示在特定输出端口上有一个缓冲区准备就绪，此时软件可以将缓冲区返回给用户。

.. 注意:: 关于如何使用 IPU6 ISYS 驱动进行捕获，请参阅 :ref:`示例<ipu6_isys_capture_examples>`。
