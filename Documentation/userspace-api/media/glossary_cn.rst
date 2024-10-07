SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1 无不变部分或更高版本

========
术语表
========

.. 注意::

   本节的目标是统一媒体用户空间 API 文档中使用的术语。这是一项正在进行的工作。
请保持术语表条目的字母顺序。

.. 术语表::

    Bridge Driver（桥接驱动程序）
   一个 :term:`设备驱动程序`，实现了与媒体硬件通信的主要逻辑。
CEC API
   **消费者电子控制 API**

   一个设计用于通过 HDMI CEC 接口接收和传输数据的 API
见 :ref:`cec`
Data Unit（数据单元）

   由总线传输的数据单元。在并行总线上，数据单元包含一个或多个相关的样本；而在串行总线上，数据单元是逻辑上的。如果数据单元是图像数据，它也可以被称为像素。
Device Driver（设备驱动程序）
   Linux 内核的一部分，实现了对硬件组件的支持。
Device Node（设备节点）

   文件系统中的字符设备节点，用于控制并传输进出内核驱动的数据。
Digital TV API（数字电视 API）
   **以前称为 DVB API**

   一个设计用于控制 :term:`媒体硬件` 的子集的 API，这些硬件实现数字电视（例如 DVB、ATSC、ISDB 等）。
见 :ref:`dvbapi`
DSP
   **数字信号处理器**

   一种专门的 :term:`微处理器`，其架构针对数字信号处理的操作需求进行了优化。
FPGA
**现场可编程门阵列**

一种**集成电路（IC）**，设计为在制造后由客户或设计师进行配置。
参见 https://en.wikipedia.org/wiki/Field-programmable_gate_array

硬件组件
**媒体硬件**的一个子集。例如一个**I²C**或**SPI**设备，或者是一个位于**系统级芯片（SoC）**或**FPGA**内部的**IP模块**。

硬件外设
一组**硬件组件（Hardware Component）**，它们共同构成一个更大的面向用户的功能性外设。例如，**SoC**中的**图像信号处理器（ISP）** **IP模块**和外部摄像头传感器一起构成了一个摄像头硬件外设。
也称为**外设（Peripheral）**。

I²C
**互连集成电路**

一种多主控、多从属、分组交换、单端、串行计算机总线，用于控制某些硬件组件，如子设备硬件组件。
参见 http://www.nxp.com/docs/en/user-guide/UM10204.pdf

IC
**集成电路**

一组电子电路集成在一个小而平坦的半导体材料上，通常为硅。
也称为芯片。

IP模块
**知识产权核心**

在电子设计中，半导体知识产权核心是一种可重用的逻辑单元、单元或集成电路布局设计，属于某个方的知识产权。
### IP Blocks
IP Blocks 可以授权给另一方使用，也可以由单一方拥有和使用。
参见：https://en.wikipedia.org/wiki/Semiconductor_intellectual_property_core

### ISP
**图像信号处理器（Image Signal Processor）**

一种专门的处理器，实现了一套用于处理图像数据的算法。ISP 可能会实现镜头阴影校正、去马赛克、缩放和像素格式转换等算法，并生成统计数据供控制算法使用（例如自动曝光、白平衡和对焦）。

### Media API
一组用户空间 API 用于控制多媒体硬件。它包括：

- CEC API；
- 数字电视 API；
- MC API；
- RC API；以及
- V4L2 API

参见：Documentation/userspace-api/media/index.rst

### MC API
**媒体控制器 API（Media Controller API）**

一个设计用于暴露和控制多媒体设备及其子设备之间关系的 API。

参见：:ref:`media_controller`

### MC-centric
一种需要 :term:`MC API` 的 :term:`V4L2 Hardware` 设备驱动程序。
此类驱动程序设置了 `V4L2_CAP_IO_MC` 设备能力字段（参见 :ref:`VIDIOC_QUERYCAP`）。

参见：:ref:`v4l2_hardware_control` 了解更多信息。
### 媒体硬件
媒体硬件是受 Linux Media API 支持的硬件子集。
这包括音频和视频捕获及播放硬件、数字和模拟电视、摄像头传感器、图像信号处理器（ISP）、遥控器、编解码器、HDMI 消费电子控制（CEC）、HDMI 捕获等。

### 微处理器
微处理器是一种电子电路，通过执行计算机程序的基本算术、逻辑、控制和输入/输出（I/O）操作来完成指令，在单一集成电路中实现这些功能。

### 外设
与术语“硬件外设”相同。

### 遥控器 API (RC API)
这是一种设计用于接收和传输来自遥控器的数据的 API。
参见：:ref:`remote_controllers`

### SMBus
SMBus 是 I²C 的一个子集，定义了对总线的更严格使用。

### 串行外设接口总线 (SPI)
一种用于短距离通信的同步串行通信接口规范，主要用于嵌入式系统。

### 系统级芯片 (SoC)
一种将计算机或其他电子系统的所有组件集成在一个集成电路中的技术。

### 数据流
从初始源到最终接收端的数据流（图像数据或元数据）。初始源可以是一个图像传感器，而最终接收端可以是一个内存缓冲区。
V4L2 API  
**V4L2 用户空间 API**

在 :ref:`v4l2spec` 中定义的用户空间 API，用于控制 V4L2 硬件。

V4L2 设备节点  
与 V4L 驱动程序关联的 :term:`设备节点`。
V4L2 设备节点的命名规范在 :ref:`v4l2_device_naming` 中指定。

V4L2 硬件  
由 :term:`V4L2 API` 支持的媒体硬件的一部分。

V4L2 子设备  
不受 :term:`桥接驱动程序` 控制的 V4L2 硬件组件。详情参见 :ref:`subdev`。

以视频节点为中心  
不需要使用媒体控制器的 V4L2 设备驱动程序。
此类驱动程序的 `device_caps` 字段中的 `V4L2_CAP_IO_MC` 标志未设置（参见 :ref:`VIDIOC_QUERYCAP`）。

V4L2 子设备 API  
:term:`V4L2 API` 的一部分，用于控制 :term:`V4L2 子设备`，如传感器、HDMI 接收器、缩放器和去交织器。
更多详细信息请参见 :ref:`v4l2_hardware_control`。
