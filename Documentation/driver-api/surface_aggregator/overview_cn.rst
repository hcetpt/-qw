### SPDX 许可证标识符：GPL-2.0+

#### 概述

Surface/System Aggregator Module（SAM，SSAM）是微软Surface设备上的嵌入式控制器（EC）。它最初出现在第四代设备（Surface Pro 4、Surface Book 1）上，但随着后续几代产品的推出，其职责和功能集已经显著扩展。

#### 特性和集成

目前对于第四代设备（Surface Pro 4、Surface Book 1）上的SAM了解不多，这是因为主机与EC之间使用了不同的通信接口（详情见下文）。在第五代（Surface Pro 2017、Surface Book 2、Surface Laptop 1）及之后的设备中，SAM负责提供电池信息（包括当前状态和最大容量等静态值），以及各种温度传感器（如皮肤温度）和冷却/性能模式设置。特别地，在Surface Book 2上，它还提供了一个用于正确处理剪贴板分离（即从键盘部分分离显示屏部分）的接口；在Surface Laptop 1和2上，它是键盘HID输入所必需的。第七代设备的HID子系统进行了重构，在这些设备上，特别是在Surface Laptop 3和Surface Book 3上，它负责所有主要的HID输入（即键盘和触控板）。

虽然自第五代以来，粗略的功能没有太多变化，但是内部接口发生了一些重大变化。在第五代和第六代设备上，电池和温度信息通过一个中间驱动程序（称为Surface ACPI Notify，或SAN）暴露给ACPI，该驱动将ACPI通用串行总线的写/读访问转换为SAM请求。而在第七代设备上，这个额外的层被移除，这些设备需要直接接入SAM接口的驱动程序。同样，在更新的几代产品中，ACPI声明的设备较少，这使得它们更难以发现，并且要求我们硬编码一种设备注册表。

由于这些原因，实现了一个SSAM总线和子系统，其中包含客户端设备（`struct ssam_device <ssam_device>` 类型）。

#### 通信

主机和EC之间的通信接口类型取决于Surface设备的代数。在第四代设备上，主机和EC通过HID进行通信，具体来说，使用的是I2C上的HID设备；而在第五代及以后的设备上，通信是通过USART串口设备进行的。根据其他操作系统中的驱动程序，我们将串口设备及其驱动程序称为Surface Serial Hub（SSH）。当有必要时，我们会区分两种类型的SAM，将其分别称为SSH上的SAM（SAM-over-SSH）和HID上的SAM（SAM-over-HID）。

目前，此子系统仅支持SSH上的SAM。SSH通信接口的详细描述如下。HID接口尚未被逆向工程，目前尚不清楚下面详细描述的SSH接口概念中有多少（以及哪些）可以移植到HID接口上。

##### Surface Serial Hub

如上所述，Surface Serial Hub（SSH）是第五代及以后所有Surface设备中SAM的通信接口。在最高层次上，通信可以分为两大类：请求，即从主机发送到EC的消息，可能触发EC的直接响应（明确与请求相关联）；以及事件（有时也称为通知），即由EC发送到主机而无需对之前的请求作出直接响应。我们也可以将无响应的请求称为命令。一般来说，需要通过多个专用请求之一来启用事件，EC才会发送这些事件。

有关更技术性的协议文档，请参阅 `Documentation/driver-api/surface_aggregator/ssh.rst`；关于内部驱动架构的概述，请参阅 `Documentation/driver-api/surface_aggregator/internal.rst`。
