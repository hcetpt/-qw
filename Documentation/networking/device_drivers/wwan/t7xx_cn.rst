.. SPDX 许可证标识符: 只限 GPL-2.0

.. 版权所有 (C) 2020-21 英特尔公司

.. _t7xx_driver_doc:

============================================
适用于 MTK PCIe 基础 T700 5G 调制解调器的 t7xx 驱动程序
============================================

t7xx 驱动程序是为 Linux 或 Chrome OS 平台开发的 WWAN PCIe 主机驱动程序，用于在主机平台与联发科（MediaTek）T700 5G 调制解调器之间通过 PCIe 接口进行数据交换。该驱动程序提供了一个符合 MBIM 协议 [1] 的接口。任何前端应用（例如 Modem Manager）都可以轻松管理 MBIM 接口以实现 WWAN 数据通信。此外，该驱动程序还提供了一个通过 AT 命令与联发科调制解调器交互的接口。

基本使用
===========
当未被管理时，MBIM 和 AT 功能是不活跃的。t7xx 驱动程序提供了代表 MBIM 和 AT 控制通道的 WWAN 端口用户空间接口，并且不对它们的功能管理起作用。用户空间应用程序需要检测端口枚举并启用 MBIM 和 AT 功能。
一些示例用户空间应用程序包括：

- mbimcli（随 libmbim [2] 库一起提供），以及
- Modem Manager [3]

管理应用程序需要执行以下操作来建立 MBIM IP 会话：

- 打开 MBIM 控制通道
- 配置网络连接设置
- 连接到网络
- 配置 IP 网络接口

管理应用程序需要执行以下操作来发送一个 AT 命令并接收响应：

- 使用 UART 工具或专用用户工具打开 AT 控制通道

Sysfs
=====
驱动程序向用户空间提供 sysfs 接口。

t7xx_mode
---------
该 sysfs 接口允许用户空间访问设备模式，此接口支持读写操作。

设备模式：
- ``unknown`` 表示设备处于未知状态
- ``ready`` 表示设备处于就绪状态
- ``reset`` 表示设备处于重置状态
- ``fastboot_switching`` 表示设备处于快速引导切换状态
- ``fastboot_download`` 表示设备处于快速引导下载状态
- ``fastboot_dump`` 表示设备处于快速引导转储状态

从用户空间读取以获取当前设备模式：
::
  $ cat /sys/bus/pci/devices/${bdf}/t7xx_mode

从用户空间写入以设置设备模式：
::
  $ echo fastboot_switching > /sys/bus/pci/devices/${bdf}/t7xx_mode

管理应用程序开发
==================

下面描述了驱动程序和用户空间接口。MBIM 协议在 [1] Mobile Broadband Interface Model v1.0 Errata-1 中有详细说明。

MBIM 控制通道用户空间 ABI
----------------------------------

/dev/wwan0mbim0 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现 MBIM WWAN 端口向 MBIM 功能提供 MBIM 接口。控制通道的用户空间端是一个 /dev/wwan0mbim0 字符设备。应用程序应使用此接口进行 MBIM 协议通信。

分片
~~~~~~~~~~~~~
根据 MBIM 规范，用户空间应用程序负责所有控制消息的分片和重组。
### /dev/wwan0mbim0 write()
~~~~~~~~~~~~~~~~~~~~~~~
管理应用程序发出的MBIM控制消息不得超过协商的控制消息大小。

### /dev/wwan0mbim0 read()
~~~~~~~~~~~~~~~~~~~~~~
管理应用程序必须接受最大到协商控制消息大小的控制消息。

### MBIM 数据通道用户空间 ABI
-------------------------------

#### wwan0-X 网络设备
~~~~~~~~~~~~~~~~~~~~~~
t7xx 驱动程序暴露一个类型为 "wwan" 的 IP 链路接口 "wwan0-X"，用于 IP 流量。使用 Iproute 网络工具创建 "wwan0-X" 网络接口，并将其与 MBIM IP 会话关联。
用户空间管理应用程序负责在建立 MBIM IP 会话之前创建新的 IP 链路，其中 SessionId 大于 0。
例如，为具有 SessionId 1 的 MBIM IP 会话创建新的 IP 链路：

```
ip link add dev wwan0-1 parentdev wwan0 type wwan linkid 1
```

驱动程序将自动将 "wwan0-1" 网络设备映射到 MBIM IP 会话 1。

### AT 端口用户空间 ABI
----------------------------------

#### /dev/wwan0at0 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现 AT WWAN 端口来暴露一个 AT 端口。控制端的用户空间部分是一个 /dev/wwan0at0 字符设备。应用程序应使用此接口发送 AT 命令。

### fastboot 端口用户空间 ABI
---------------------------

#### /dev/wwan0fastboot0 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现 fastboot WWAN 端口来暴露一个 fastboot 协议接口。fastboot 通道管道的用户空间部分是一个 /dev/wwan0fastboot0 字符设备。应用程序应使用此接口进行 fastboot 协议通信。
请注意，为了导出 /dev/wwan0fastboot0 端口，需要重新加载驱动程序，因为设备进入“fastboot_switching”模式后需要冷重启。
MediaTek 的 T700 调制解调器支持 3GPP TS 27.007 [4] 规范。
参考文献
==========
[1] *MBIM（移动宽带接口模型）勘误表-1*

- https://www.usb.org/document-library/

[2] *libmbim “一个基于glib的库，用于与使用移动宽带接口模型（MBIM）协议的WWAN调制解调器和设备通信”*

- http://www.freedesktop.org/wiki/Software/libmbim/

[3] *Modem Manager “一个通过DBus激活的守护进程，用于控制移动宽带（2G/3G/4G/5G）设备和连接”*

- http://www.freedesktop.org/wiki/Software/ModemManager/

[4] *规范# 27.007 - 3GPP*

- https://www.3gpp.org/DynaReport/27007.htm

[5] *fastboot “一种与引导加载程序通信的机制”*

- https://android.googlesource.com/platform/system/core/+/refs/heads/main/fastboot/README.md
