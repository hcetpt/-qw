### SPDX 许可证标识符：GPL-2.0-only

### 版权所有 (C) 2020-21 英特尔公司

### _iosm_driver_doc:

===========================================
英特尔 M.2 PCIe 基础调制解调器的 IOSM 驱动程序
===========================================

IOSM（通过共享内存的 IPC）驱动程序是为 Linux 或 Chrome 平台开发的 WWAN PCIe 主机驱动程序，用于在主机平台和英特尔 M.2 调制解调器之间通过 PCIe 接口进行数据交换。该驱动程序提供了符合 MBIM 协议 [1] 的接口。任何前端应用（例如：Modem Manager）都可以轻松管理 MBIM 接口以实现 WWAN 数据通信。

基本使用
===========
当未被管理时，MBIM 功能处于非激活状态。IOSM 驱动程序仅提供一个用户空间接口 MBIM “WWAN 端口”，代表 MBIM 控制通道，并不参与管理功能。检测端口枚举并启用 MBIM 功能是用户空间应用程序的工作。
一些这样的用户空间应用程序示例包括：
- mbimcli（随 libmbim [2] 库一起提供），以及
- Modem Manager [3]

为了建立 MBIM IP 会话，管理应用程序需要执行以下操作：
- 打开 MBIM 控制通道
- 配置网络连接设置
- 连接到网络
- 配置 IP 网络接口

管理应用程序开发
==================

下面描述了驱动程序和用户空间接口。MBIM 协议在 [1] 中有详细说明：Mobile Broadband Interface Model v1.0 Errata-1
MBIM 控制通道用户空间 ABI
----------------------------------

/dev/wwan0mbim0 字符设备
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
驱动程序通过实现 MBIM WWAN 端口来为 MBIM 功能提供 MBIM 接口。控制通道的用户空间端点是一个 /dev/wwan0mbim0 字符设备。应用程序应使用此接口进行 MBIM 协议通信。
分片
~~~~~~~~~~~~~
根据 MBIM 规范，用户空间应用程序负责所有控制消息的分片和重组。
/dev/wwan0mbim0 写入()
~~~~~~~~~~~~~~~~~~~~~~~
来自管理应用程序的 MBIM 控制消息不应超过协商的控制消息大小。
/dev/wwan0mbim0 读取()
~~~~~~~~~~~~~~~~~~~~~~~
管理应用程序必须接受最大为协商的控制消息大小的控制消息。
MBIM 数据通道用户空间 ABI
-------------------------------

wwan0-X 网络设备
~~~~~~~~~~~~~~~~~~~~~~
IOSM 驱动程序为 IP 流量暴露了一个类型为 "wwan" 的 IP 链路接口 "wwan0-X"。iproute 网络实用工具用于创建 "wwan0-X" 网络接口，并将其与 MBIM IP 会话相关联。驱动程序支持最多 8 个 IP 会话同时进行 IP 通信。
用户空间管理应用程序负责在建立 MBIM IP 会话之前创建新的 IP 链路，其中 SessionId 大于 0。
例如，为 SessionId 为 1 的 MBIM IP 会话创建新的 IP 链路：

  ip link add dev wwan0-1 parentdev-name wwan0 type wwan linkid 1

驱动程序将自动将 "wwan0-1" 网络设备映射到 MBIM IP 会话 1。
参考文献  
==========
[1] "MBIM（移动宽带接口模型）勘误表-1"  
      - https://www.usb.org/document-library/

[2] libmbim - “一个基于glib的库，用于与遵循移动宽带接口模型（MBIM）协议的无线广域网调制解调器和设备通信”
      - http://www.freedesktop.org/wiki/Software/libmbim/

[3] Modem Manager - “一个通过DBus激活的守护进程，用于控制移动宽带（2G/3G/4G）设备和连接”
      - http://www.freedesktop.org/wiki/Software/ModemManager/
