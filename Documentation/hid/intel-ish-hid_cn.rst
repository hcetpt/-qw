英特尔集成传感器中枢 (ISH)
=================================

传感器中枢能够将传感器轮询和算法处理卸载到专用的低功耗协处理器上。这使得主处理器可以更频繁地进入低功耗模式，从而延长电池寿命。
有许多供应商提供了符合HID传感器使用表的外部传感器中枢。这些设备可以在平板电脑、二合一可转换笔记本电脑及嵌入式产品中找到。Linux自3.9版本起就已经支持这类设备。
英特尔®从Cherry Trail开始，在系统芯片(SoC)中引入了集成传感器中枢，并且现在已经在多个代际的CPU封装中得到了支持。已经有大量商用设备配备了集成传感器中枢（ISH）。
这些ISH同样遵守HID传感器规范，但是通信所使用的传输协议不同。当前的外部传感器中枢主要使用I2C或USB上的HID。但ISH不使用I2C或USB。

概述
========

以usbhid实现为例，ISH遵循类似的模型来进行高速通信：

	-----------------		----------------------
	|    USB HID	|	-->	|    ISH HID	     |
	-----------------		----------------------
	-----------------		----------------------
	|  USB协议	|	-->	|    ISH传输协议   |
	-----------------		----------------------
	-----------------		----------------------
	|  EHCI/XHCI	|	-->	|    ISH IPC	     |
	-----------------		----------------------
	      PCI				 PCI
	-----------------		----------------------
	|主机控制器|	-->	|    ISH处理器   |
	-----------------		----------------------
	     USB链路
	-----------------		----------------------
	| USB终端节点|	-->	|    ISH客户端     |
	-----------------		----------------------

就像USB协议提供了一种设备枚举、链路管理和用户数据封装的方法一样，ISH也提供了类似的服务。但它非常轻量级，专为管理和与ISH客户端应用程序（在固件中实现）进行通信而设计。
ISH允许多个传感器管理应用程序在固件中执行。像USB终端节点那样，消息可以发送至或接收自一个客户端。作为枚举过程的一部分，这些客户端会被识别出来。这些客户端可以是简单的HID传感器应用程序、传感器校准应用程序或传感器固件更新应用程序。

ISH实施模型：块图
=================================

::

	 ---------------------------
	|  用户空间应用程序  |
	 ---------------------------

  ----------------IIO ABI----------------
	 --------------------------
	|  IIO 传感器驱动程序	  |
	 --------------------------
	 --------------------------
	|	 IIO 核心	  |
	 --------------------------
	 --------------------------
	|   HID 传感器中枢 MFD	  |
	 --------------------------
	 --------------------------
	|       HID 核心	  |
	 --------------------------
	 --------------------------
	|   ISH上的HID 客户端   |
	 --------------------------
	 --------------------------
	|   ISH传输(ISHTP)      |
	 --------------------------
	 --------------------------
	|      IPC 驱动程序	  |
	 --------------------------
  操作系统(OS)
  ---------------- PCI -----------------
  硬件+固件
	 ----------------------------
	| ISH硬件/固件(FW) |
	 ----------------------------

上述各块中的高级处理
=====================================

硬件接口
------------------

ISH对主机表现为“非VGA未分类PCI设备”。PCI产品和供应商ID会随着不同代际的处理器变化。因此，枚举驱动程序的源代码需要随每一代进行更新。
处理器间通信 (IPC) 驱动程序
------------------------------------------

位置: drivers/hid/intel-ish-hid/ipc

IPC消息使用内存映射I/O。寄存器定义在hw-ish-regs.h中。
IPC/FW消息类型
^^^^^^^^^^^^^^^^^^^^

有两种类型的消息，一种用于链路管理，另一种用于传输层之间的消息发送和接收。
运输消息的TX和RX
..............................

一组内存映射寄存器支持多字节消息的TX和RX（例如IPC_REG_ISH2HOST_MSG、IPC_REG_HOST2ISH_MSG）。IPC层维护内部队列以对消息进行排序，并按顺序发送给固件。可选地，调用方可以注册处理器以接收完成通知。
在消息传递中使用门铃机制来触发主机和客户端固件中的处理。当ISH中断处理器被调用时，主机驱动程序使用ISH2HOST门铃寄存器来确定该中断是为ISH准备的。
每一端都有32个32位的消息寄存器和一个32位的门铃寄存器。门铃寄存器的格式如下：

  位0..6：分段长度（使用7位）
  位10..13：封装协议
  位16..19：管理命令（用于IPC管理协议）
  位31：门铃触发（向另一侧发出硬件中断信号）
  其他位保留，应为0
运输层接口
^^^^^^^^^^^^^^^^^^^^^^^^^

为了抽象出硬件级别的IPC通信，注册了一组回调函数。
运输层使用这些回调函数来发送和接收消息。
参见结构体ishtp_hw_ops中的回调函数。
ISH运输层
-------------------

位置：drivers/hid/intel-ish-hid/ishtp/

一种通用的运输层
^^^^^^^^^^^^^^^^^^^^^^^^^

运输层是一种双向协议，定义了：
- 一系列启动、停止、连接、断开连接和流量控制的命令（详情请参见ishtp/hbm.h）
- 一种避免缓冲区溢出的流量控制机制

此协议类似于以下文档中描述的总线消息：
http://www.intel.com/content/dam/www/public/us/en/documents/technical-\  
specifications/dcmi-hi-1-0-spec.pdf "第7章：总线消息层"

连接和流量控制机制
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

每个固件客户端和协议都由一个UUID标识。要与固件客户端通信，必须使用连接请求和响应总线消息建立连接。如果成功，一对(host_client_id 和 fw_client_id)将标识该连接。
一旦建立了连接，对等端会独立地互相发送流量控制总线消息。每个对等端只有在收到流量控制信用后才能发送消息。一旦它发送了一个消息，在收到下一个流量控制信用之前，就不能再发送另一个消息。
任一方都可以发送断开请求总线消息以终止通信。此外，如果发生主要的固件重置，连接也会被中断。

点对点数据传输
^^^^^^^^^^^^^^^^^^^^^^^^^^

点对点数据传输可以在使用或不使用直接内存访问（DMA）的情况下进行。根据传感器带宽需求，可以使用`intel_ishtp`模块参数`ishtp_use_dma`来启用DMA。每一方（主机和固件）独立管理其DMA传输内存。当任一方（主机或固件）的ISHTP客户端想要发送数据时，它会决定是通过IPC还是DMA发送；对于每次传输，这个决策都是独立的。发送方在消息位于相应的主机缓冲区中时（主机客户端发送时为TX，固件客户端发送时为RX）发送DMA_XFER消息。DMA消息的接收方会用DMA_XFER_ACK响应，表明发送方可重新使用该消息所对应的内存区域。
DMA初始化开始于主机发送包含RX缓冲区的DMA_ALLOC_NOTIFY总线消息，固件则会用DMA_ALLOC_NOTIFY_ACK响应。除了DMA地址通信之外，这一序列还检查能力：如果主机不支持DMA，则不会发送DMA分配，所以固件也不能发送DMA；如果固件不支持DMA，则不会用DMA_ALLOC_NOTIFY_ACK响应，在这种情况下，主机将不会使用DMA传输。
在这里，ISH作为总线主DMA控制器。因此，当主机发送DMA_XFER时，它是请求进行主机->ISH的DMA传输；当固件发送DMA_XFER时，意味着它已经完成了DMA，且消息位于主机上。因此，DMA_XFER和DMA_XFER_ACK充当所有权指示器。
在初始状态下，所有传出内存都属于发送方（向主机发送为TX，向固件发送为RX），DMA_XFER将包含ISHTP消息的区域内存的所有权转移到接收方，DMA_XFER_ACK则将所有权返回给发送方。发送方不必等待之前的DMA_XFER被确认，只要在其所有权限内的连续内存足够，就可以发送另一条消息。
原则上，可以一次发送多个DMA_XFER和DMA_XFER_ACK消息（最多达到IPC MTU），从而允许中断节流。
目前，ISH固件决定如果ISHTP消息大于3个IPC片段，则通过DMA发送，否则通过IPC发送。

环形缓冲区
^^^^^^^^^^^^

当一个客户端发起连接时，会分配一个RX和TX缓冲区的环形队列。
环形缓冲区的大小可由客户端指定。HID 客户端分别为 TX 和 RX 缓冲区设置 16 和 32。在客户端发送请求时，待发送的数据被复制到一个发送环形缓冲区中，并使用总线消息协议进行调度以发送。这些缓冲区是必要的，因为 FW 可能尚未处理完上一条消息，可能没有足够的流量控制信用额度来发送数据。接收端的情况也是如此，需要流量控制。

**主机枚举**
^^^^^^^^^^^^^^^^

主机枚举总线命令允许发现 FW 中存在的客户端。
可能存在多个传感器客户端和校准功能客户端。
为了简化实现并允许独立驱动程序处理每个客户端，这一传输层利用了 Linux 总线驱动模型。每个客户端都作为设备注册在传输总线上（ishtp 总线）。
枚举消息序列如下：

- 主机发送 HOST_START_REQ_CMD，表示主机 ISHTP 层已启动
- FW 响应 HOST_START_RES_CMD
- 主机发送 HOST_ENUM_REQ_CMD（枚举 FW 客户端）
- FW 响应 HOST_ENUM_RES_CMD，其中包含可用 FW 客户端 ID 的位图
- 对于位图中找到的每个 FW ID，主机发送 HOST_CLIENT_PROPERTIES_REQ_CMD
- FW 响应 HOST_CLIENT_PROPERTIES_RES_CMD。属性包括 UUID、最大 ISHTP 消息大小等
- 一旦主机收到最后一个发现客户端的属性，它认为 ISHTP 设备完全功能正常（并分配 DMA 缓冲区）

**ISHTP 上的 HID 客户端**
-------------------

位置：drivers/hid/intel-ish-hid

ISHTP 客户端驱动负责以下任务：

- 枚举 FW ISH 客户端下的 HID 设备
- 获取报告描述符
- 作为低级驱动注册至 HID 核心
- 处理获取/设置特性请求
- 获取输入报告

**HID 传感器中心 MFD 和 IIO 传感器驱动**
-----------------------------------------

这些驱动中的功能与外部传感器中心相同。
请参考：
Documentation/hid/hid-sensor.rst 了解 HID 传感器
Documentation/ABI/testing/sysfs-bus-iio 了解 IIO ABIs 到用户空间

**端到端 HID 传输序列图**
-----------------------------------------

```
HID-ISH-CLN                    ISHTP                    IPC                             HW
          |                        |                       |                               |
          |                        |                       |-----WAKE UP------------------>|
          |                        |                       |                               |
          |                        |                       |-----HOST READY--------------->|
          |                        |                       |                               |
          |                        |                       |<----MNG_RESET_NOTIFY_ACK----- |
          |                        |                       |                               |
          |                        |<----ISHTP_START------ |                               |
          |                        |                       |                               |
          |                        |<-----------------HOST_START_RES_CMD-------------------|
          |                        |                       |                               |
          |                        |------------------QUERY_SUBSCRIBER-------------------->|
          |                        |                       |                               |
          |                        |------------------HOST_ENUM_REQ_CMD------------------->|
          |                        |                       |                               |
          |                        |<-----------------HOST_ENUM_RES_CMD--------------------|
          |                        |                       |                               |
          |                        |------------------HOST_CLIENT_PROPERTIES_REQ_CMD------>|
          |                        |                       |                               |
          |                        |<-----------------HOST_CLIENT_PROPERTIES_RES_CMD-------|
          |       在 ishtp 总线上创建新设备                |                               |
          |                        |                       |                               |
          |                        |------------------HOST_CLIENT_PROPERTIES_REQ_CMD------>|
          |                        |                       |                               |
          |                        |<-----------------HOST_CLIENT_PROPERTIES_RES_CMD-------|
          |       在 ishtp 总线上创建新设备                |                               |
          |                        |                       |                               |
          |                        |--重复 HOST_CLIENT_PROPERTIES_REQ_CMD 直到最后一个--|
          |                        |                       |                               |
       probed()
          |----ishtp_cl_connect--->|----------------- CLIENT_CONNECT_REQ_CMD-------------->|
          |                        |                       |                               |
          |                        |<----------------CLIENT_CONNECT_RES_CMD----------------|
          |                        |                       |                               |
          | 注册事件回调函数         |                       |                               |
          |                        |                       |                               |
          |ishtp_cl_send(
          HOSTIF_DM_ENUM_DEVICES)  |----------填充 ishtp_msg_hdr 结构写入硬件------------>| 
          |                        |                       |                               |
          |                        |                       |<-----IRQ(IPC_PROTOCOL_ISHTP---|
          |                        |                       |                               |
          |<--ENUM_DEVICE RSP------|                       |                               |
          |                        |                       |                               |
  针对每个枚举设备
          |ishtp_cl_send(
          HOSTIF_GET_HID_DESCRIPTOR|----------填充 ishtp_msg_hdr 结构写入硬件------------>| 
          |                        |                       |                               |
          ...响应
          |                        |                       |                               |
  针对每个枚举设备
          |ishtp_cl_send(
       HOSTIF_GET_REPORT_DESCRIPTOR|--------------填充 ishtp_msg_hdr 结构写入硬件-------->| 
          |                        |                       |                               |
          |                        |                       |                               |
   hid_allocate_device
          |                        |                       |                               |
   hid_add_device                  |                       |                               |
          |                        |                       |                               |

```

**从主机加载 ISH 固件流程**
-----------------------------------

从 Lunar Lake 一代开始，ISH 固件已被分为两个组件以便更好地优化空间和增加灵活性。这些组件包括集成到 BIOS 中的引导加载程序，以及存储在操作系统文件系统中的主固件。
过程如下：

- 最初，ISHTP 驱动向 ISH 引导加载程序发送 HOST_START_REQ_CMD 命令。作为响应，引导加载程序返回 HOST_START_RES_CMD。此响应包含 ISHTP_SUPPORT_CAP_LOADER 位。随后，ISHTP 驱动检查该位是否被设置。如果设置，则从主机开始固件加载过程。
在这个过程中，ISHTP驱动程序首先调用request_firmware()函数，然后发送LOADER_CMD_XFER_QUERY命令。在从引导加载程序接收到响应后，ISHTP驱动程序发送LOADER_CMD_XFER_FRAGMENT命令。再次接收响应后，ISHTP驱动程序发送LOADER_CMD_START命令。引导加载程序响应并随后进入主固件。

过程结束后，ISHTP驱动程序调用release_firmware()函数。
为了获取更详细的信息，请参考下面提供的流程描述：

::

  +---------------+                                                    +-----------------+
  | ISHTP 驱动    |                                                    | ISH 引导加载程序 |
  +---------------+                                                    +-----------------+
          |                                                                     |
          |~~~发送 HOST_START_REQ_CMD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--发送 HOST_START_RES_CMD(包含 ISHTP_SUPPORT_CAP_LOADER 标志)------|
          |                                                                     |
  ****************************************************************************************
  * 如果设置了 ISHTP_SUPPORT_CAP_LOADER 标志                                             *
  ****************************************************************************************
          |                                                                     |
          |~~~开始从主机进程加载固件~~~+                                      |
          |                                              |                      |
          |<---------------------------------------------+                      |
          |                                                                     |
  ---------------------------                                                   |
  | 调用 request_firmware() |                                                   |
  ---------------------------                                                   |
          |                                                                     |
          |~~~发送 LOADER_CMD_XFER_QUERY~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--发送响应-----------------------------------------------------|
          |                                                                     |
          |~~~发送 LOADER_CMD_XFER_FRAGMENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--发送响应-----------------------------------------------------|
          |                                                                     |
          |~~~发送 LOADER_CMD_START~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--发送响应-----------------------------------------------------|
          |                                                                     |
          |                                                                     |~~~跳转到主固件~~~+
          |                                                                     |                           |
          |                                                                     |<--------------------------+
          |                                                                     |
  ---------------------------                                                   |
  | 调用 release_firmware() |                                                   |
  ---------------------------                                                   |
          |                                                                     |
  ****************************************************************************************
  * 结束 if                                                                               *
  ****************************************************************************************
          |                                                                     |
  +---------------+                                                    +-----------------+
  | ISHTP 驱动    |                                                    | ISH 引导加载程序 |
  +---------------+                                                    +-----------------+

ISH 调试
-------

要调试 ISH，使用事件跟踪机制。要启用调试日志::

  echo 1 > /sys/kernel/tracing/events/intel_ish/enable
  cat /sys/kernel/tracing/trace

在联想thinkpad Yoga 260上的 ISH IIO sysfs 示例
-------------------------------------------------

::

  root@otcpl-ThinkPad-Yoga-260:~# tree -l /sys/bus/iio/devices/
  /sys/bus/iio/devices/
  ├── iio:device0 -> ../../../devices/0044:8086:22D8.0001/HID-SENSOR-200073.9.auto/iio:device0
  │   ├── buffer
  │   │   ├── enable
  │   │   ├── length
  │   │   └── watermark
  ..
│   ├── in_accel_hysteresis
  │   ├── in_accel_offset
  │   ├── in_accel_sampling_frequency
  │   ├── in_accel_scale
  │   ├── in_accel_x_raw
  │   ├── in_accel_y_raw
  │   ├── in_accel_z_raw
  │   ├── name
  │   ├── scan_elements
  │   │   ├── in_accel_x_en
  │   │   ├── in_accel_x_index
  │   │   ├── in_accel_x_type
  │   │   ├── in_accel_y_en
  │   │   ├── in_accel_y_index
  │   │   ├── in_accel_y_type
  │   │   ├── in_accel_z_en
  │   │   ├── in_accel_z_index
  │   │   └── in_accel_z_type
  ..
│   │   ├── devices
  │   │   │   │   ├── buffer
  │   │   │   │   │   ├── enable
  │   │   │   │   │   ├── length
  │   │   │   │   │   └── watermark
  │   │   │   │   ├── dev
  │   │   │   │   ├── in_intensity_both_raw
  │   │   │   │   ├── in_intensity_hysteresis
  │   │   │   │   ├── in_intensity_offset
  │   │   │   │   ├── in_intensity_sampling_frequency
  │   │   │   │   ├── in_intensity_scale
  │   │   │   │   ├── name
  │   │   │   │   ├── scan_elements
  │   │   │   │   │   ├── in_intensity_both_en
  │   │   │   │   │   ├── in_intensity_both_index
  │   │   │   │   │   └── in_intensity_both_type
  │   │   │   │   ├── trigger
  │   │   │   │   │   └── current_trigger
  ..
│   │   │   │   ├── buffer
  │   │   │   │   │   ├── enable
  │   │   │   │   │   ├── length
  │   │   │   │   │   └── watermark
  │   │   │   │   ├── dev
  │   │   │   │   ├── in_magn_hysteresis
  │   │   │   │   ├── in_magn_offset
  │   │   │   │   ├── in_magn_sampling_frequency
  │   │   │   │   ├── in_magn_scale
  │   │   │   │   ├── in_magn_x_raw
  │   │   │   │   ├── in_magn_y_raw
  │   │   │   │   ├── in_magn_z_raw
  │   │   │   │   ├── in_rot_from_north_magnetic_tilt_comp_raw
  │   │   │   │   ├── in_rot_hysteresis
  │   │   │   │   ├── in_rot_offset
  │   │   │   │   ├── in_rot_sampling_frequency
  │   │   │   │   ├── in_rot_scale
  │   │   │   │   ├── name
  ..
│   │   │   │   ├── scan_elements
  │   │   │   │   │   ├── in_magn_x_en
  │   │   │   │   │   ├── in_magn_x_index
  │   │   │   │   │   ├── in_magn_x_type
  │   │   │   │   │   ├── in_magn_y_en
  │   │   │   │   │   ├── in_magn_y_index
  │   │   │   │   │   ├── in_magn_y_type
  │   │   │   │   │   ├── in_magn_z_en
  │   │   │   │   │   ├── in_magn_z_index
  │   │   │   │   │   ├── in_magn_z_type
  │   │   │   │   │   ├── in_rot_from_north_magnetic_tilt_comp_en
  │   │   │   │   │   ├── in_rot_from_north_magnetic_tilt_comp_index
  │   │   │   │   │   └── in_rot_from_north_magnetic_tilt_comp_type
  │   │   │   │   ├── trigger
  │   │   │   │   │   └── current_trigger
  ..
│   │   │   │   ├── buffer
  │   │   │   │   │   ├── enable
  │   │   │   │   │   ├── length
  │   │   │   │   │   └── watermark
  │   │   │   │   ├── dev
  │   │   │   │   ├── in_anglvel_hysteresis
  │   │   │   │   ├── in_anglvel_offset
  │   │   │   │   ├── in_anglvel_sampling_frequency
  │   │   │   │   ├── in_anglvel_scale
  │   │   │   │   ├── in_anglvel_x_raw
  │   │   │   │   ├── in_anglvel_y_raw
  │   │   │   │   ├── in_anglvel_z_raw
  │   │   │   │   ├── name
  │   │   │   │   ├── scan_elements
  │   │   │   │   │   ├── in_anglvel_x_en
  │   │   │   │   │   ├── in_anglvel_x_index
  │   │   │   │   │   ├── in_anglvel_x_type
  │   │   │   │   │   ├── in_anglvel_y_en
  │   │   │   │   │   ├── in_anglvel_y_index
  │   │   │   │   │   ├── in_anglvel_y_type
  │   │   │   │   │   ├── in_anglvel_z_en
  │   │   │   │   │   ├── in_anglvel_z_index
  │   │   │   │   │   └── in_anglvel_z_type
  │   │   │   │   ├── trigger
  │   │   │   │   │   └── current_trigger
  ..
│   │   │   │   ├── buffer
  │   │   │   │   │   ├── enable
  │   │   │   │   │   ├── length
  │   │   │   │   │   └── watermark
  │   │   │   │   ├── dev
  │   │   │   │   ├── in_anglvel_hysteresis
  │   │   │   │   ├── in_anglvel_offset
  │   │   │   │   ├── in_anglvel_sampling_frequency
  │   │   │   │   ├── in_anglvel_scale
  │   │   │   │   ├── in_anglvel_x_raw
  │   │   │   │   ├── in_anglvel_y_raw
  │   │   │   │   ├── in_anglvel_z_raw
  │   │   │   │   ├── name
  │   │   │   │   ├── scan_elements
  │   │   │   │   │   ├── in_anglvel_x_en
  │   │   │   │   │   ├── in_anglvel_x_index
  │   │   │   │   │   ├── in_anglvel_x_type
  │   │   │   │   │   ├── in_anglvel_y_en
  │   │   │   │   │   ├── in_anglvel_y_index
  │   │   │   │   │   ├── in_anglvel_y_type
  │   │   │   │   │   ├── in_anglvel_z_en
  │   │   │   │   │   ├── in_anglvel_z_index
  │   │   │   │   │   └── in_anglvel_z_type
  │   │   │   │   ├── trigger
  │   │   │   │   │   └── current_trigger
  ..
