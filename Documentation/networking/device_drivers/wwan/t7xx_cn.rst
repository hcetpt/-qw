### SPDX 许可证标识符: GPL-2.0-only

### 版权 (C) 2020-21 英特尔公司

### _t7xx_driver_doc:

============================================
面向MTK PCIe 基础T700 5G调制解调器的t7xx驱动程序
============================================

t7xx驱动程序是一个WWAN PCIe主机驱动程序，为Linux或Chrome OS平台开发，用于通过PCIe接口在主机平台与MediaTek的T700 5G调制解调器之间进行数据交换。该驱动程序提供了一个符合MBIM协议[1]的接口。任何前端应用（例如Modem Manager）都可以轻松管理MBIM接口以实现WWAN上的数据通信。此外，该驱动程序还提供了一个通过AT命令与MediaTek调制解调器交互的接口。

#### 基本使用
======
当未被管理时，MBIM和AT功能处于非激活状态。t7xx驱动程序提供了表示MBIM和AT控制通道的WWAN端口用户空间接口，并不参与管理它们的功能性。由用户空间应用程序来检测端口枚举并启用MBIM和AT功能。
一些这样的用户空间应用程序示例包括：

- mbimcli（包含在libmbim [2]库中），以及
- Modem Manager [3]

管理应用程序需执行以下操作以建立MBIM IP会话：

- 打开MBIM控制通道
- 配置网络连接设置
- 连接到网络
- 配置IP网络接口

管理应用程序需执行以下操作以发送AT命令并接收响应：

- 使用UART工具或特殊用户工具打开AT控制通道

#### Sysfs
======
驱动程序向用户空间提供sysfs接口。
t7xx_mode
---------
此sysfs接口向用户空间提供了设备模式的访问权限，支持读写操作。
设备模式：

- `unknown` 表示设备处于未知状态
- `ready` 表示设备处于就绪状态
- `reset` 表示设备处于重置状态
- `fastboot_switching` 表示设备处于快速启动切换状态
- `fastboot_download` 表示设备处于快速启动下载状态
- `fastboot_dump` 表示设备处于快速启动转储状态

从用户空间读取以获取当前设备模式
::
  $ cat /sys/bus/pci/devices/${bdf}/t7xx_mode

从用户空间写入以设置设备模式
::
  $ echo fastboot_switching > /sys/bus/pci/devices/${bdf}/t7xx_mode

#### 管理应用程序开发
==================
下面描述了驱动程序和用户空间接口。MBIM协议在[1] Mobile Broadband Interface Model v1.0 Errata-1中有所描述。

##### MBIM控制通道用户空间ABI
----------------------------------

/dev/wwan0mbim0 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现MBIM WWAN端口向MBIM功能暴露一个MBIM接口。控制通道管道的用户空间端点是/dev/wwan0mbim0字符设备。应用程序应使用此接口进行MBIM协议通信。

##### 分割
~~~~~~~~~~~~~
根据MBIM规范，用户空间应用程序负责所有控制消息的分割和重组。
下面是提供的英文内容翻译成中文：

`/dev/wwan0mbim0 write()`
~~~~~~~~~~~~~~~~~~~~~~~
来自管理应用的MBIM控制消息不应超过协商确定的控制消息大小。

`/dev/wwan0mbim0 read()`
~~~~~~~~~~~~~~~~~~~~~~
管理应用必须能够接收达到协商确定的控制消息大小的消息。

MBIM数据通道用户空间ABI
-------------------------------

wwan0-X 网络设备
~~~~~~~~~~~~~~~~~~~~~~
t7xx驱动为IP流量暴露了类型为"wwan"的IP链路接口"wwan0-X"。使用Iproute网络工具来创建"wwan0-X"网络接口，并将其与MBIM IP会话关联。
用户空间中的管理应用负责在建立MBIM IP会话（其中SessionId大于0）之前创建新的IP链路。
例如，为一个SessionId为1的MBIM IP会话创建新的IP链路：

  ip link add dev wwan0-1 parentdev wwan0 type wwan linkid 1

驱动程序将自动将"wwan0-1"网络设备映射到MBIM IP会话1。

AT端口用户空间ABI
----------------------------------

`/dev/wwan0at0` 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现AT WWAN端口暴露了一个AT端口。
控制端的用户空间端是一个`/dev/wwan0at0`字符设备。应用程序应当使用此接口来发送AT命令。

fastboot端口用户空间ABI
---------------------------

`/dev/wwan0fastboot0` 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现fastboot WWAN端口暴露了一个fastboot协议接口。
fastboot通道管道的用户空间端是一个`/dev/wwan0fastboot0`字符设备。应用程序应当使用此接口进行fastboot协议通信。
请注意，为了导出`/dev/wwan0fastboot0`端口，需要重新加载驱动程序，因为设备在进入“fastboot_switching”模式后需要冷重置。

MediaTek的T700调制解调器支持3GPP TS 27.007 [4]规范。
参考文献  
==========
[1] *MBIM（移动宽带接口模型）勘误表-1*

- https://www.usb.org/document-library/

[2] *libmbim “一个基于glib的库，用于与遵循移动宽带接口模型（MBIM）协议的无线广域网调制解器和设备通信”*

- http://www.freedesktop.org/wiki/Software/libmbim/

[3] *Modem Manager “一个通过DBus激活的守护进程，用于控制移动宽带（2G/3G/4G/5G）设备和连接”*

- http://www.freedesktop.org/wiki/Software/ModemManager/

[4] *规范 # 27.007 - 3GPP*

- https://www.3gpp.org/DynaReport/27007.htm

[5] *fastboot “一种与启动加载程序进行通信的机制”*

- https://android.googlesource.com/platform/system/core/+/refs/heads/main/fastboot/README.md
