==================================================================
RapidIO 子系统 MPORT 字符设备驱动程序 (rio_mport_cdev.c)
==================================================================

1. 概览
===========

该设备驱动程序是 RapidIO.org 软件任务组 (STG) 中 Texas Instruments、Freescale、Prodrive Technologies、Nokia Networks、BAE 和 IDT 之间合作的成果。此外还收到了来自 RapidIO.org 其他成员的额外输入。目标是创建一个字符模式驱动接口，以直接向应用程序暴露 RapidIO 设备的能力，同时允许众多不同的 RapidIO 实现能够相互操作。
此驱动程序 (MPORT_CDEV) 为用户空间应用程序提供了访问基本 RapidIO 子系统操作的功能。大多数 RapidIO 操作都是通过 `ioctl` 系统调用来支持的。
当加载此设备驱动程序时，它会在 `/dev` 目录中为每个注册的 RapidIO mport 设备创建名为 `rio_mportX` 的文件系统节点。“X”在节点名称中与分配给每个本地 mport 设备的唯一端口 ID 匹配。
使用可用的一系列 ioctl 命令，用户空间应用程序可以执行以下 RapidIO 总线和子系统的操作：

- 从/向 mport 设备的配置寄存器读取/写入 (RIO_MPORT_MAINT_READ_LOCAL/RIO_MPORT_MAINT_WRITE_LOCAL)
- 从/向远程 RapidIO 设备的配置寄存器读取/写入。这些操作定义为 RapidIO 维护读/写 (RIO_MPORT_MAINT_READ_REMOTE/RIO_MPORT_MAINT_WRITE_REMOTE)
- 设置 mport 设备的 RapidIO 目标 ID (RIO_MPORT_MAINT_HDID_SET)
- 设置 mport 设备的 RapidIO 组件标签 (RIO_MPORT_MAINT_COMPTAG_SET)
- 查询 mport 设备的逻辑索引 (RIO_MPORT_MAINT_PORT_IDX_GET)
- 查询 mport 设备的能力和 RapidIO 链路配置 (RIO_MPORT_GET_PROPERTIES)
- 启用/禁用向用户空间应用程序报告 RapidIO 门铃事件 (RIO_ENABLE_DOORBELL_RANGE/RIO_DISABLE_DOORBELL_RANGE)
- 启用/禁用向用户空间应用程序报告 RIO 端口写入事件 (RIO_ENABLE_PORTWRITE_RANGE/RIO_DISABLE_PORTWRITE_RANGE)
- 查询/控制通过此驱动程序报告的事件类型：门铃、端口写入或两者 (RIO_SET_EVENT_MASK/RIO_GET_EVENT_MASK)
- 配置/mport 的出站请求窗口（用于特定大小、RapidIO 目标 ID、跳数和请求类型）(RIO_MAP_OUTBOUND/RIO_UNMAP_OUTBOUND)
- 配置/mport 的入站请求窗口（用于特定大小、RapidIO 基地址和本地内存基地址）(RIO_MAP_INBOUND/RIO_UNMAP_INBOUND)
- 为 DMA 数据传输分配/释放连续的 DMA 协调内存缓冲区到/从远程 RapidIO 设备 (RIO_ALLOC_DMA/RIO_FREE_DMA)
- 发起到/从远程 RapidIO 设备的 DMA 数据传输 (RIO_TRANSFER) 支持阻塞、异步和发布（即“发而忘之”）数据传输模式
- 检查/等待异步 DMA 数据传输完成 (RIO_WAIT_FOR_ASYNC)
- 管理 RapidIO 子系统支持的设备对象 (RIO_DEV_ADD/RIO_DEV_DEL) 这允许实现各种 RapidIO 织物枚举算法作为用户空间应用程序，同时利用内核 RapidIO 子系统提供的其余功能

2. 硬件兼容性
=========================

此设备驱动程序使用由内核 RapidIO 子系统定义的标准接口，因此它可以与任何通过 RapidIO 子系统注册的 mport 设备驱动程序一起使用，其限制取决于可用 mport 实现的特性。
在此时刻，最常见的限制是特定mport设备的RapidIO专用DMA引擎框架的可用性。用户在计划使用此驱动程序时应验证其平台的功能：

- IDT Tsi721 PCIe到RapidIO桥接设备及其mport设备驱动程序与此驱动程序完全兼容
- Freescale SoCs的'fsl_rio'mport驱动程序没有实现RapidIO专用DMA引擎支持，因此，mport_cdev驱动程序中的DMA数据传输不可用
3. 模块参数
=============

- 'dma_timeout'
      - DMA传输完成超时（以毫秒为单位，默认值3000）
此参数设置SYNC模式DMA传输请求以及RIO_WAIT_FOR_ASYNC ioctl请求的最大等待完成时间
- 'dbg_level'
      - 此参数允许控制由该设备驱动程序生成的调试信息量。
        该参数由一组位掩码组成，这些掩码对应于特定的功能块
有关掩码定义，请参阅'drivers/rapidio/devices/rio_mport_cdev.c'
        此参数可以动态更改
使用CONFIG_RAPIDIO_DEBUG=y来启用顶层的调试输出
4. 已知问题
=============

  没有已知问题
5. 用户空间应用程序和API
==================================

使用此设备驱动程序的API库和应用程序可以从RapidIO.org获得
6. 待办事项列表
=============

- 添加发送/接收“原始”RapidIO消息包的支持
在不具备 RapidIO 特定的 DMA 选项时，增加内存映射的 DMA 数据传输作为一个备选方案。
