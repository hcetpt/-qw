英特尔集成传感器中心 (ISH)
=================================

传感器中心能够将传感器轮询和算法处理卸载到专用的低功耗协处理器。这使得核心处理器可以更频繁地进入低功耗模式，从而增加电池寿命。
有许多供应商提供了符合HID传感器使用表的外部传感器中心。这些设备可以在平板电脑、二合一可转换笔记本电脑以及嵌入式产品中找到。Linux自3.9版本起就支持这些设备。
英特尔®从Cherry Trail开始在SoC中引入了集成传感器中心（ISH），并已支持多个代际的CPU封装。已经有大量商业设备配备了集成传感器中心（ISH）。
这些ISH同样遵循HID传感器规范，但不同之处在于通信所使用的传输协议。当前的外部传感器中心主要使用通过I2C或USB的HID。但ISH不使用I2C或USB。

概述
========

使用一个与usbhid实现类似的类比，ISH遵循类似的高速通信模型：

```
	-----------------		----------------------
	|    USB HID	|	-->	|    ISH HID	     |
	-----------------		----------------------
	-----------------		----------------------
	|  USB protocol	|	-->	|    ISH Transport   |
	-----------------		----------------------
	-----------------		----------------------
	|  EHCI/XHCI	|	-->	|    ISH IPC	     |
	-----------------		----------------------
	      PCI				 PCI
	-----------------		----------------------
	|Host controller|	-->	|    ISH processor   |
	-----------------		----------------------
	     USB Link
	-----------------		----------------------
	| USB End points|	-->	|    ISH Clients     |
	-----------------		----------------------
```

就像USB协议提供了一种设备枚举、链接管理和用户数据封装的方法一样，ISH也提供了类似的服务。但它非常轻量级，专门用于管理和与在固件中实现的ISH客户端应用程序进行通信。
ISH允许多个传感器管理应用程序在固件中执行。像USB端点一样，消息可以是发送或接收自客户端。作为枚举过程的一部分，这些客户端会被识别出来。这些客户端可以是简单的HID传感器应用程序、传感器校准应用程序或传感器固件更新应用程序。
实现模型类似，像USB总线一样，ISH传输也被实现为一个总线。每个在ISH处理器上执行的客户端应用程序都注册为此总线上的设备。驱动程序（ISH HID驱动程序）会识别设备类型并注册到HID核心。

ISH实现：框图
=================================

```
	 ---------------------------
	|  用户空间应用程序  |
	 ---------------------------

  ----------------IIO ABI----------------
	 --------------------------
	|  IIO传感器驱动程序	  |
	 --------------------------
	 --------------------------
	|	 IIO核心	  |
	 --------------------------
	 --------------------------
	|   HID传感器中心MFD	  |
	 --------------------------
	 --------------------------
	|       HID核心	  |
	 --------------------------
	 --------------------------
	|   HID over ISH客户端   |
	 --------------------------
	 --------------------------
	|   ISH传输（ISHTP）  |
	 --------------------------
	 --------------------------
	|      IPC驱动程序	  |
	 --------------------------
  操作系统
  ---------------- PCI -----------------
  硬件+固件
	 ----------------------------
	| ISH硬件/固件（FW） |
	 ----------------------------
```

上述模块中的高级处理
=====================================

硬件接口
------------------

ISH以“非VGA未分类PCI设备”的形式暴露给主机。不同代际的处理器的PCI产品和供应商ID会有所不同。因此，枚举驱动程序的源代码需要从一代到另一代进行更新。

处理器间通信（IPC）驱动程序
------------------------------------------

位置：drivers/hid/intel-ish-hid/ipc

IPC消息使用内存映射I/O。寄存器定义在hw-ish-regs.h中。
IPC/FW消息类型
^^^^^^^^^^^^^^^^

有两种类型的消息，一种用于管理链接，另一种用于传输层之间的消息。
### 传输消息的TX和RX

一组内存映射寄存器支持多字节消息的TX和RX（例如IPC_REG_ISH2HOST_MSG，IPC_REG_HOST2ISH_MSG）。IPC层维护内部队列以对消息进行排序，并按顺序发送到固件。可选地，调用者可以注册一个处理器以接收完成通知。门铃机制用于触发主机和客户端固件中的消息处理。当ISH中断处理器被调用时，主机驱动程序使用ISH2HOST门铃寄存器来确定中断是否是针对ISH的。

每一侧有32个32位的消息寄存器和一个32位的门铃寄存器。门铃寄存器的格式如下：

  - 位0..6：片段长度（使用7位）
  - 位10..13：封装协议
  - 位16..19：管理命令（用于IPC管理协议）
  - 位31：门铃触发（向另一侧发出硬件中断信号）
  - 其他位保留，应为0

### 传输层接口

为了抽象硬件级别的IPC通信，注册了一组回调函数。传输层使用这些回调函数来发送和接收消息。请参阅结构体ishtp_hw_ops以获取回调函数详情。

### ISH传输层

位置：drivers/hid/intel-ish-hid/ishtp/

### 通用传输层

传输层是一种双向协议，定义了以下内容：
- 一系列启动、停止、连接、断开连接和流控制的命令（详见ishtp/hbm.h）
- 一种避免缓冲区溢出的流控制机制

此协议类似于以下文档中描述的总线消息：“http://www.intel.com/content/dam/www/public/us/en/documents/technical-specifications/dcmi-hi-1-0-spec.pdf 第7章：总线消息层”

### 连接和流控制机制

每个固件客户端和协议都由一个UUID标识。为了与固件客户端通信，必须通过连接请求和响应总线消息建立连接。如果成功，一对(host_client_id和fw_client_id)将标识该连接。
一旦建立了连接，对等方将独立地相互发送流控制总线消息。每个对等方只有在收到流控制信用后才能发送消息。一旦发送了一个消息，在收到下一个流控制信用之前不得再发送另一个消息。
任一方都可以发送断开请求的总线消息来结束通信。此外，如果发生主要固件重置，连接也会被断开。

点对点数据传输
^^^^^^^^^^^^^^^^^^^^^^^^^^

点对点数据传输可以使用或不使用直接内存访问（DMA）进行。根据传感器带宽需求，可以通过设置`intel_ishtp`模块参数`ishtp_use_dma`启用DMA。每一方（主机和固件）独立管理其DMA传输内存。当任一方（主机或固件）的ISHTP客户端想要发送数据时，它会决定是通过进程间通信（IPC）还是DMA发送；每次传输的决策都是独立的。发送方在消息位于相应的主机缓冲区中时（主机客户端发送时为TX缓冲区，固件客户端发送时为RX缓冲区）发送DMA_XFER消息。接收方收到DMA消息后会回应DMA_XFER_ACK，表示发送方可以重新使用该消息所占用的内存区域。

DMA初始化始于主机发送包含RX缓冲区的DMA_ALLOC_NOTIFY总线消息，固件会回应DMA_ALLOC_NOTIFY_ACK。除了DMA地址通信外，这一序列还会检查能力：如果主机不支持DMA，则不会发送DMA分配消息，因此固件也不能发送DMA；如果固件不支持DMA，则不会回应DMA_ALLOC_NOTIFY_ACK，在这种情况下，主机也不会使用DMA传输。在这里，ISH充当总线主控DMA控制器。因此，当主机发送DMA_XFER时，是在请求进行主机到ISH的DMA传输；当固件发送DMA_XFER时，表示它已经完成了DMA传输，消息已存放在主机上。因此，DMA_XFER和DMA_XFER_ACK作为所有权指示器。

初始状态下，所有传出内存都属于发送方（TX到主机，RX到固件），DMA_XFER将包含ISHTP消息的内存区域的所有权转移到接收方，DMA_XFER_ACK则将所有权返回给发送方。发送方无需等待前一个DMA_XFER被确认，只要其拥有的剩余连续内存足够，就可以发送另一条消息。

原则上，可以一次发送多个DMA_XFER和DMA_XFER_ACK消息（最多可达IPC MTU），从而实现中断节流。目前，如果ISHTP消息超过3个IPC片段，ISH固件会选择通过DMA发送，否则通过IPC发送。

环形缓冲区
^^^^^^^^^^^^

当客户端发起连接时，会分配一个RX和TX缓冲区环。
环形缓冲区的大小可以由客户端指定。HID 客户端分别为 TX 和 RX 缓冲区设置 16 和 32。在客户端发出发送请求时，要发送的数据会被复制到一个发送环形缓冲区，并使用总线消息协议进行调度发送。这些缓冲区是必要的，因为固件（FW）可能尚未处理完上一条消息，并且可能没有足够的流量控制信用额度来发送数据。接收端的情况也是如此，并且需要流量控制。

### 主机枚举
^^^^^^^^^^^^^^^^

主机枚举总线命令允许发现固件（FW）中存在的客户端。可能存在多个传感器客户端和校准功能客户端。为了简化实现并允许独立驱动程序处理每个客户端，这一传输层利用了 Linux 总线驱动模型。每个客户端都注册为传输总线（ishtp 总线）上的设备。枚举序列如下：

- 主机发送 `HOST_START_REQ_CMD`，表示主机 ISHTP 层已就绪。
- 固件响应 `HOST_START_RES_CMD`。
- 主机发送 `HOST_ENUM_REQ_CMD`（枚举 FW 客户端）。
- 固件响应 `HOST_ENUM_RES_CMD`，该响应包括可用 FW 客户端 ID 的位图。
- 对于位图中找到的每个 FW ID，主机发送 `HOST_CLIENT_PROPERTIES_REQ_CMD`。
- 固件响应 `HOST_CLIENT_PROPERTIES_RES_CMD`。属性包括 UUID、最大 ISHTP 消息大小等。
- 一旦主机接收到最后一个发现的客户端的属性，它认为 ISHTP 设备已完全功能化（并分配 DMA 缓冲区）。

### ISH 上的 HID 客户端
-------------------

位置：`drivers/hid/intel-ish-hid`

ISHTP 客户端驱动负责：

- 枚举 FW ISH 客户端下的 HID 设备。
- 获取报告描述符。
- 注册为 HID 核心的一个低级（LL）驱动。
- 处理获取/设置特性请求。
- 获取输入报告。

### HID 传感器中心 MFD 和 IIO 传感器驱动
-----------------------------------------

这些驱动的功能与外部传感器中心相同。请参阅：
- `Documentation/hid/hid-sensor.rst` 用于 HID 传感器
- `Documentation/ABI/testing/sysfs-bus-iio` 用于 IIO ABIs 到用户空间

### 端到端 HID 传输序列图
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
          |ishtp_cl_send(          |----------fill ishtp_msg_hdr struct write to HW-----  >|
          HOSTIF_DM_ENUM_DEVICES)  |                       |                               |
          |                        |                       |<-----IRQ(IPC_PROTOCOL_ISHTP---|
          |                        |                       |                               |
          |<--ENUM_DEVICE RSP------|                       |                               |
          |                        |                       |                               |
  for each enumerated device
          |ishtp_cl_send(          |----------fill ishtp_msg_hdr struct write to HW-----  >|
          HOSTIF_GET_HID_DESCRIPTOR|                       |                               |
          |                        |                       |                               |
          ...Response
          |                        |                       |                               |
  for each enumerated device
          |ishtp_cl_send(          |--------------fill ishtp_msg_hdr struct write to HW-- >|
       HOSTIF_GET_REPORT_DESCRIPTOR|                       |                               |
          |                        |                       |                               |
          |                        |                       |                               |
   hid_allocate_device
          |                        |                       |                               |
   hid_add_device                  |                       |                               |
          |                        |                       |                               |

```

### ISH 固件从主机加载流程
-----------------------------------

从 Lunar Lake 一代开始，ISH 固件被分为两个组件以更好地优化空间并增加灵活性。这些组件包括集成到 BIOS 中的引导加载程序以及存储在操作系统文件系统中的主固件。过程如下：

- 最初，ISHTP 驱动向 ISH 引导加载程序发送 `HOST_START_REQ_CMD` 命令。作为回应，引导加载程序返回 `HOST_START_RES_CMD`。此响应包含 ISHTP_SUPPORT_CAP_LOADER 位。随后，ISHTP 驱动检查此位是否被设置。如果设置了，则从主机开始加载固件。
### 在此过程中，ISHTP 驱动程序首先调用 `request_firmware()` 函数，然后发送一个 `LOADER_CMD_XFER_QUERY` 命令。在接收到引导加载程序的响应后，ISHTP 驱动程序发送一个 `LOADER_CMD_XFER_FRAGMENT` 命令。再次接收到响应后，ISHTP 驱动程序发送一个 `LOADER_CMD_START` 命令。引导加载程序响应后，跳转到主固件。
- 过程结束后，ISHTP 驱动程序调用 `release_firmware()` 函数。

为了获取更详细的信息，请参阅下面提供的流程描述：

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
  * 如果设置了 ISHTP_SUPPORT_CAP_LOADER 标志：                                      *
  ****************************************************************************************
          |                                                                     |
          |~~~开始从主机加载固件过程~~~+                      |
          |                                              |                      |
          |<---------------------------------------------+                      |
          |                                                                     |
  ---------------------------                                                   |
  | 调用 request_firmware() |                                                   |
  ---------------------------                                                   |
          |                                                                     |
          |~~~Send LOADER_CMD_XFER_QUERY~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send response-----------------------------------------------------|
          |                                                                     |
          |~~~Send LOADER_CMD_XFER_FRAGMENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send response-----------------------------------------------------|
          |                                                                     |
          |~~~Send LOADER_CMD_START~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~>|
          |                                                                     |
          |<--Send response-----------------------------------------------------|
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
  | ISHTP Driver  |                                                    | ISH Bootloader  |
  +---------------+                                                    +-----------------+
```

### ISH 调试
为了调试 ISH，使用事件跟踪机制。要启用调试日志：
```
echo 1 > /sys/kernel/tracing/events/intel_ish/enable
cat /sys/kernel/tracing/trace
```

### Lenovo ThinkPad Yoga 260 上的 ISH IIO sysfs 示例
```
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
```
