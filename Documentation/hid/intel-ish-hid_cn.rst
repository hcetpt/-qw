英特尔集成传感器中枢 (ISH)
=================================

传感器中枢能够将传感器轮询和算法处理卸载到专用的低功耗协处理器上。这使得主处理器可以更频繁地进入低功耗模式，从而延长电池寿命。
有许多供应商提供了符合HID传感器使用表的外部传感器中枢。这些设备可以在平板电脑、二合一可转换笔记本电脑及嵌入式产品中找到。自Linux 3.9起，Linux就已支持此类设备。
英特尔®从Cherry Trail开始在SoC中引入了集成传感器中枢，并现在已经在多个代际的CPU封装中得到支持。已有许多商业设备搭载了集成传感器中枢 (ISH)。
这些ISH同样遵循HID传感器规范，但不同之处在于用于通信的传输协议。当前的外部传感器中枢主要通过I2C或USB上的HID进行通信。而ISH并不使用I2C或USB。

概述
========

以usbhid实现为例，ISH采用类似的模型来实现高速通信：

	-----------------		----------------------
	|    USB HID	|	-->	|    ISH HID	     |
	-----------------		----------------------
	-----------------		----------------------
	|  USB 协议	|	-->	|    ISH 传输层   |
	-----------------		----------------------
	-----------------		----------------------
	|  EHCI/XHCI	|	-->	|    ISH IPC	     |
	-----------------		----------------------
	      PCI				 PCI
	-----------------		----------------------
	|主机控制器|	-->	|    ISH 处理器   |
	-----------------		----------------------
	     USB 链路
	-----------------		----------------------
	| USB 端点|	-->	|    ISH 客户端     |
	-----------------		----------------------

就像USB协议提供了一种设备枚举、链路管理和用户数据封装的方法一样，ISH也提供了类似的服务。但它非常轻量级，专门用来管理并与在固件中实现的ISH客户端应用程序进行通信。
ISH允许在固件中执行多个传感器管理应用。像USB端点一样，消息可以发送给或接收自一个客户端。作为枚举过程的一部分，这些客户端会被识别出来。这些客户端可以是简单的HID传感器应用、传感器校准应用或传感器固件更新应用。

ISH实现：模块图
==================

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
	|   ISH 上的 HID 客户端   |
	 --------------------------
	 --------------------------
	|   ISH 传输层 (ISHTP) |
	 --------------------------
	 --------------------------
	|      IPC 驱动程序	  |
	 --------------------------
  操作系统
  ---------------- PCI -----------------
  硬件 + 固件
	 ----------------------------
	| ISH 硬件/固件(FW) |
	 ----------------------------

上述模块中的高级处理
=====================

硬件接口
------------------

ISH被暴露为主机上的“非VGA未分类PCI设备”。对于不同代际的处理器，PCI产品和供应商ID会有所变化。因此，枚举驱动程序的源代码需要从一代到另一代进行更新。
处理器间通信 (IPC) 驱动程序
------------------------------------------

位置: drivers/hid/intel-ish-hid/ipc

IPC消息使用内存映射I/O。寄存器定义在hw-ish-regs.h中。
IPC/固件消息类型
^^^^^^^^^^^^^^^^^^^^

有两种类型的消息，一种用于链路管理，另一种用于与传输层之间的消息传递。
运输消息的TX和RX
..............................

一组内存映射寄存器支持多字节消息的TX和RX（例如IPC_REG_ISH2HOST_MSG、IPC_REG_HOST2ISH_MSG）。IPC层维护内部队列以对消息进行排序，并按顺序发送给固件。可选地，调用者可以注册处理器以接收完成通知。
在消息传递中使用门铃机制来触发主机和客户端固件中的处理。当ISH中断处理器被调用时，主机驱动程序使用ISH2HOST门铃寄存器来确定该中断是为ISH准备的。
每一侧都有32个32位的消息寄存器和一个32位的门铃。门铃寄存器具有以下格式：

  位0..6：分段长度（使用了7位）
  位10..13：封装协议
  位16..19：管理命令（用于IPC管理协议）
  位31：门铃触发器（向另一侧发出硬件中断信号）
  其他位保留，应为0
运输层接口
^^^^^^^^^^^^^^^^^^^^^^^^^

为了抽象出硬件级别的IPC通信，注册了一组回调函数。
运输层使用它们来发送和接收消息。
参见结构体ishtp_hw_ops了解回调函数详情。
ISH 运输层
-------------------

位置：drivers/hid/intel-ish-hid/ishtp/

一种通用的运输层
^^^^^^^^^^^^^^^^^^^^^^^^^

运输层是一种双向协议，定义了：
- 一系列启动、停止、连接、断开连接以及流量控制的命令（详细内容请参阅ishtp/hbm.h）
- 避免缓冲区溢出的流量控制机制

此协议类似于以下文档中描述的总线消息：“第7章：总线消息层”
http://www.intel.com/content/dam/www/public/us/en/documents/technical-\
specifications/dcmi-hi-1-0-spec.pdf

连接与流量控制机制
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

每个固件客户端及其协议都由一个UUID标识。为了与固件客户端进行通信，必须使用连接请求和响应总线消息建立连接。如果成功，一对(host_client_id 和 fw_client_id)将标识该连接。
一旦建立了连接，对等端之间独立地互相发送流量控制总线消息。每个对等端只有在收到流量控制信用后才能发送一条消息。一旦发送了消息，在收到下一个流量控制信用之前不得发送另一条消息。
任一方都可以发送断开请求的总线消息来结束通信。此外，如果发生主要固件重置，连接也会被断开。

### 对等数据传输
^^^^^^^^^^^^^^^^^^^^^^^^^^

对等数据传输可以在使用或不使用直接内存访问（DMA）的情况下进行。根据传感器带宽需求，可以通过设置`intel_ishtp`模块参数`ishtp_use_dma`来启用DMA。每一方（主机和固件）独立管理其DMA传输内存。当任一方（主机或固件）的ISHTP客户端想要发送数据时，它会决定是通过进程间通信（IPC）还是通过DMA发送；对于每次传输，这个决策都是独立的。发送方在消息位于相应的主机缓冲区中时（主机客户端发送时为TX缓冲区，固件客户端发送时为RX缓冲区）发送DMA_XFER消息。DMA消息的接收方以DMA_XFER_ACK响应，表明发送方可复用该消息所对应的内存区域。

DMA初始化从主机发送包含RX缓冲区的DMA_ALLOC_NOTIFY总线消息开始，并且固件会以DMA_ALLOC_NOTIFY_ACK响应。除了用于DMA地址通信之外，这一序列还检查能力：如果主机不支持DMA，则不会发送DMA分配，因此固件也无法发送DMA；如果固件不支持DMA，则不会响应DMA_ALLOC_NOTIFY_ACK，在这种情况下，主机将不会使用DMA传输。
这里，ISH充当总线主DMA控制器。因此，当主机发送DMA_XFER时，它是请求执行从主机到ISH的DMA传输；当固件发送DMA_XFER时，意味着它已经完成了DMA操作，而消息存储在主机上。因此，DMA_XFER和DMA_XFER_ACK作为所有权指示器。
初始状态下，所有传出内存都属于发送方（TX给主机，RX给固件），DMA_XFER将包含ISHTP消息的区域的所有权转移给接收方，DMA_XFER_ACK将所有权返回给发送方。发送方不必等待之前的DMA_XFER被确认，只要在其所有权内的剩余连续内存足够，就可以发送另一条消息。
原则上，可以一次发送多个DMA_XFER和DMA_XFER_ACK消息（最多可达IPC最大传输单元MTU），从而允许中断节流。
目前，ISH固件根据ISHTP消息是否超过3个IPC片段来决定是通过DMA发送还是通过IPC发送。

### 环形缓冲区
^^^^^^^^^^^^

当一个客户端发起连接时，会分配RX和TX环形缓冲区。
环形缓冲区的大小可由客户端指定。HID 客户端分别为 TX 和 RX 缓冲区设置 16 和 32。当从客户端发出发送请求时，待发送的数据被复制到一个发送环形缓冲区，并通过总线消息协议进行调度发送。这些缓冲区是必需的，因为固件（FW）可能尚未处理最后一条消息，因此可能没有足够的流量控制信用额度来发送数据。接收端的情况也是如此，并且需要流量控制。
### 主机枚举
```
^^^^^^^^^^^^^^^^
```

主机枚举总线命令允许发现存在于固件中的客户端。
可能存在多个传感器客户端以及校准功能的客户端。
为了简化实现并允许独立驱动程序处理每个客户端，此传输层利用了 Linux 总线驱动模型。每个客户端都作为传输总线（ishtp 总线）上的设备进行注册。
枚举序列如下：

- 主机发送 `HOST_START_REQ_CMD`，表明主机 ISHTP 层已启动
- 固件以 `HOST_START_RES_CMD` 响应
- 主机发送 `HOST_ENUM_REQ_CMD`（枚举固件客户端）
- 固件以 `HOST_ENUM_RES_CMD` 响应，该响应包含可用固件客户端 ID 的位图
- 对于在位图中找到的每个固件 ID，主机发送 `HOST_CLIENT_PROPERTIES_REQ_CMD`
- 固件以 `HOST_CLIENT_PROPERTIES_RES_CMD` 响应。属性包括 UUID、最大 ISHTP 消息大小等
- 一旦主机收到最后一个发现的客户端的属性，它就认为 ISHTP 设备完全可用（并分配 DMA 缓冲区）

### ISHTP 上的 HID 客户端
```
-------------------
```

位置：`drivers/hid/intel-ish-hid`

ISHTP 客户端驱动负责以下任务：

- 枚举固件 ISH 客户端下的 HID 设备
- 获取报告描述符
- 作为低级（LL）驱动注册到 HID 核心
- 处理获取/设置特征请求
- 获取输入报告

### HID 传感器中心 MFD 和 IIO 传感器驱动
```
-----------------------------------------
```

这些驱动的功能与外部传感器中心相同。
参考：
- `Documentation/hid/hid-sensor.rst` 用于 HID 传感器
- `Documentation/ABI/testing/sysfs-bus-iio` 用于 IIO ABI 到用户空间
### 端到端 HID 传输序列图
```
-----------------------------------------
```

```
HID-ISH-CLN                    ISHTP                    IPC                             HW
          |                        |                       |                               |
          |                        |                       |-----WAKE UP------------------>|
          |                        |                       |                               |
          |                        |                       |-----HOST READY--------------->|
          |                        |                       |                               |
          |                        |                       |<----MNG_RESET_NOTIFY_ACK----- |
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
          |       Create new device on in ishtp bus        |                               |
          |                        |                       |                               |
          |                        |------------------HOST_CLIENT_PROPERTIES_REQ_CMD------>|
          |                        |                       |                               |
          |                        |<-----------------HOST_CLIENT_PROPERTIES_RES_CMD-------|
          |       Create new device on in ishtp bus        |                               |
          |                        |                       |                               |
          |                        |--Repeat HOST_CLIENT_PROPERTIES_REQ_CMD-till last one--|
          |                        |                       |                               |
       probed()
          |----ishtp_cl_connect--->|----------------- CLIENT_CONNECT_REQ_CMD-------------->|
          |                        |                       |                               |
          |                        |<----------------CLIENT_CONNECT_RES_CMD----------------|
          |                        |                       |                               |
          |register event callback |                       |                               |
          |                        |                       |                               |
          |ishtp_cl_send(
          HOSTIF_DM_ENUM_DEVICES)  |----------fill ishtp_msg_hdr struct write to HW-----  >|
          |                        |                       |                               |
          |                        |                       |<-----IRQ(IPC_PROTOCOL_ISHTP---|
          |                        |                       |                               |
          |<--ENUM_DEVICE RSP------|                       |                               |
          |                        |                       |                               |
  for each enumerated device
          |ishtp_cl_send(
          HOSTIF_GET_HID_DESCRIPTOR|----------fill ishtp_msg_hdr struct write to HW-----  >|
          |                        |                       |                               |
          ...Response
          |                        |                       |                               |
  for each enumerated device
          |ishtp_cl_send(
       HOSTIF_GET_REPORT_DESCRIPTOR|--------------fill ishtp_msg_hdr struct write to HW-- >|
          |                        |                       |                               |
          |                        |                       |                               |
   hid_allocate_device
          |                        |                       |                               |
   hid_add_device                  |                       |                               |
          |                        |                       |                               |
```

### 从主机加载 ISH 固件流程
```
-----------------------------------
```

从 Lunar Lake 一代开始，ISH 固件已被分为两个组件以实现更好的空间优化和增加灵活性。这些组件包括集成到 BIOS 中的引导加载程序和存储在操作系统文件系统中的主固件。
该过程如下：

- 最初，ISHTP 驱动向 ISH 引导加载程序发送 `HOST_START_REQ_CMD` 命令。作为响应，引导加载程序回传 `HOST_START_RES_CMD`。该响应包括 ISHTP_SUPPORT_CAP_LOADER 位。随后，ISHTP 驱动检查此位是否被设置。如果设置了，则开始从主机加载固件的过程。
在这个过程中，ISHTP驱动程序首先调用`request_firmware()`函数，然后发送一个`LOADER_CMD_XFER_QUERY`命令。在接收到引导加载程序的响应后，ISHTP驱动程序发送一个`LOADER_CMD_XFER_FRAGMENT`命令。在接收另一响应后，ISHTP驱动程序发送一个`LOADER_CMD_START`命令。引导加载程序作出响应，然后进入主固件。

过程结束后，ISHTP驱动程序调用`release_firmware()`函数。

更详细的信息，请参阅下面提供的流程描述：

```
+---------------+                                                    +-----------------+
| ISHTP Driver  |                                                    | ISH Bootloader  |
+---------------+                                                    +-----------------+
          |                                                                     |
          |~~~Send HOST_START_REQ_CMD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send HOST_START_RES_CMD(Includes ISHTP_SUPPORT_CAP_LOADER bit)----|
          |                                                                     |
  ****************************************************************************************
  * 如果设置了ISHTP_SUPPORT_CAP_LOADER位，则执行以下步骤：                                     *
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
          |~~~Send LOADER_CMD_XFER_QUERY~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send 响应-----------------------------------------------------|
          |                                                                     |
          |~~~Send LOADER_CMD_XFER_FRAGMENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send 响应-----------------------------------------------------|
          |                                                                     |
          |~~~Send LOADER_CMD_START~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send 响应-----------------------------------------------------|
          |                                                                     |
          |                                                                     |~~~跳转到主固件~~~+|
          |                                                                     |                           |
          |                                                                     |<--------------------------+|
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
  | ISHTP Driver  |                                                    | ISH Bootloader  |
  +---------------+                                                    +-----------------+
```

### ISH调试

为了调试ISH，使用了事件跟踪机制。要启用调试日志，请执行如下操作：

```
echo 1 > /sys/kernel/tracing/events/intel_ish/enable
cat /sys/kernel/tracing/trace
```

### 在Lenovo ThinkPad Yoga 260上的ISH IIO sysfs示例

```
root@otcpl-ThinkPad-Yoga-260:~# tree -l /sys/bus/iio/devices/
/sys/bus/iio/devices/
├── iio:device0 -> ../../../devices/0044:8086:22D8.0001/HID-SENSOR-200073.9.auto/iio:device0
│   ├── buffer
│   │   ├── enable
│   │   ├── length
│   │   └── watermark
...
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
...
│   ├── in_intensity_both_raw
│   ├── in_intensity_hysteresis
│   ├── in_intensity_offset
│   ├── in_intensity_sampling_frequency
│   ├── in_intensity_scale
│   ├── name
│   ├── scan_elements
│   │   ├── in_intensity_both_en
│   │   ├── in_intensity_both_index
│   │   └── in_intensity_both_type
│   ├── trigger
│   │   └── current_trigger
...
│   ├── in_magn_hysteresis
│   ├── in_magn_offset
│   ├── in_magn_sampling_frequency
│   ├── in_magn_scale
│   ├── in_magn_x_raw
│   ├── in_magn_y_raw
│   ├── in_magn_z_raw
│   ├── in_rot_from_north_magnetic_tilt_comp_raw
│   ├── in_rot_hysteresis
│   ├── in_rot_offset
│   ├── in_rot_sampling_frequency
│   ├── in_rot_scale
│   ├── name
│   ├── scan_elements
│   │   ├── in_magn_x_en
│   │   ├── in_magn_x_index
│   │   ├── in_magn_x_type
│   │   ├── in_magn_y_en
│   │   ├── in_magn_y_index
│   │   ├── in_magn_y_type
│   │   ├── in_magn_z_en
│   │   ├── in_magn_z_index
│   │   ├── in_magn_z_type
│   │   ├── in_rot_from_north_magnetic_tilt_comp_en
│   │   ├── in_rot_from_north_magnetic_tilt_comp_index
│   │   └── in_rot_from_north_magnetic_tilt_comp_type
│   ├── trigger
│   │   └── current_trigger
...
│   ├── in_anglvel_hysteresis
│   ├── in_anglvel_offset
│   ├── in_anglvel_sampling_frequency
│   ├── in_anglvel_scale
│   ├── in_anglvel_x_raw
│   ├── in_anglvel_y_raw
│   ├── in_anglvel_z_raw
│   ├── name
│   ├── scan_elements
│   │   ├── in_anglvel_x_en
│   │   ├── in_anglvel_x_index
│   │   ├── in_anglvel_x_type
│   │   ├── in_anglvel_y_en
│   │   ├── in_anglvel_y_index
│   │   ├── in_anglvel_y_type
│   │   ├── in_anglvel_z_en
│   │   ├── in_anglvel_z_index
│   │   └── in_anglvel_z_type
│   ├── trigger
│   │   └── current_trigger
...
```
以上是Lenovo ThinkPad Yoga 260上IIO设备树的一个示例。
