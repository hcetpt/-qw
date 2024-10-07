SPDX 许可声明标识符: GPL-2.0

======================================================
cdc_mbim - 用于 CDC MBIM 移动宽带调制解调器的驱动程序
======================================================

cdc_mbim 驱动程序支持符合“通用串行总线通信类子类规范：移动宽带接口模型”[1] 的 USB 设备，这是对“通用串行总线通信类子类规范：网络控制模型设备”[2] 的进一步发展，并针对移动宽带设备（即“3G/LTE 调制解调器”）进行了优化。

命令行参数
=======================

cdc_mbim 驱动程序本身没有参数。但是，对于向后兼容 NCM 1.0 的 MBIM 功能（根据 [1] 第 3.2 节定义的“NCM/MBIM 功能”），其探测行为受 cdc_ncm 驱动程序参数的影响：

prefer_mbim
-----------
:类型: 布尔值
:有效范围: 是/否 (0-1)
:默认值: 是 (优先使用 MBIM)

此参数设置了 NCM/MBIM 功能的系统策略。这些功能将由 cdc_ncm 驱动程序或 cdc_mbim 驱动程序处理，具体取决于 prefer_mbim 设置。将 prefer_mbim 设置为 否 会使 cdc_mbim 驱动程序忽略这些功能，并让 cdc_ncm 驱动程序来处理它们。
该参数是可写的，并且可以在任何时候更改。需要手动解绑定/绑定以使更改对已绑定到“错误”驱动程序的 NCM/MBIM 功能生效。

基本用法
===========

未管理时，MBIM 功能处于非活动状态。cdc_mbim 驱动程序仅提供一个用户空间接口来访问 MBIM 控制信道，并不参与功能的管理。这意味着始终需要一个用户空间 MBIM 管理应用程序来启用 MBIM 功能。
这样的用户空间应用程序包括但不限于：

- mbimcli（包含在 libmbim [3] 库中）
- ModemManager [4]

建立 MBIM IP 会话至少需要管理应用程序执行以下操作：

- 打开控制信道
- 配置网络连接设置
- 连接到网络
- 配置 IP 接口

管理应用程序开发
---------------------
下面描述了驱动程序与用户空间之间的接口。MBIM 控制信道协议在 [1] 中有详细描述。

MBIM 控制信道用户空间 ABI
==================================

/dev/cdc-wdmX 字符设备
------------------------------
驱动程序使用 cdc-wdm 驱动程序作为子驱动程序创建了一个到 MBIM 功能控制信道的双向管道。用户空间端的控制信道管道是一个 /dev/cdc-wdmX 字符设备。
cdc_mbim 驱动程序不会处理或监控控制信道上的消息。信道完全委托给用户空间管理应用程序。因此，应用程序必须确保它满足 [1] 中的所有控制信道要求。
cdc-wdmX 设备作为 MBIM 控制接口 USB 设备的子设备创建。可以通过 sysfs 查找与特定 MBIM 功能关联的字符设备。例如：

bjorn@nemi:~$ ls /sys/bus/usb/drivers/cdc_mbim/2-4:2.12/usbmisc
cdc-wdm0

bjorn@nemi:~$ grep . /sys/bus/usb/drivers/cdc_mbim/2-4:2.12/usbmisc/cdc-wdm0/dev
180:0

USB 配置描述符
-----------------
CDC MBIM 功能描述符中的 wMaxControlMessage 字段限制了最大控制消息大小。管理应用程序负责协商一个符合 [1] 第 9.3.1 节要求的控制消息大小，同时考虑该描述符字段。
用户空间应用程序可以使用 [6] 或 [7] 中描述的两个 USB 配置描述符内核接口之一来访问 MBIM 功能的 CDC MBIM 功能描述符。请参阅下面的 ioctl 文档。

分片
-------------
用户空间应用程序负责所有控制消息的分片和重组，如 [1] 第 9.5 节所述。
/dev/cdc-wdmX write()
---------------------
来自管理应用程序的MBIM控制消息长度**不得**超过协商确定的控制消息大小。

/dev/cdc-wdmX read()
--------------------
管理应用程序**必须**接受最大不超过协商确定的控制消息大小的消息。

/dev/cdc-wdmX ioctl()
---------------------
IOCTL_WDM_MAX_COMMAND: 获取最大命令大小
此ioctl调用返回MBIM设备的CDC MBIM功能描述符中的wMaxControlMessage字段。这是为了方便使用，避免从用户空间解析USB描述符。
::

	#include <stdio.h>
	#include <fcntl.h>
	#include <sys/ioctl.h>
	#include <linux/types.h>
	#include <linux/usb/cdc-wdm.h>
	int main()
	{
		__u16 max;
		int fd = open("/dev/cdc-wdm0", O_RDWR);
		if (!ioctl(fd, IOCTL_WDM_MAX_COMMAND, &max))
			printf("wMaxControlMessage是%d\n", max);
	}

自定义设备服务
----------------------
MBIM规范允许供应商自由定义额外的服务。cdc_mbim驱动程序完全支持这一点。
对新的MBIM服务（包括供应商指定的服务）的支持完全在用户空间实现，就像MBIM控制协议的其余部分一样。

新服务应在MBIM注册表中进行注册。

MBIM数据通道用户空间ABI
===============================

wwanY网络设备
--------------------
cdc_mbim驱动程序将MBIM数据通道表示为一个“wwan”类型的单一网络设备。这个网络设备最初映射到MBIM IP会话0。

多路复用IP会话（IPS）
-----------------------------
MBIM允许通过单个USB数据通道多路复用最多256个IP会话。cdc_mbim驱动程序将这些IP会话建模为主设备wwanY的802.1q VLAN子设备，将MBIM IP会话Z映射到VLAN ID Z，对于所有大于0的Z值。
设备的最大Z值在[1]第10.5.1节描述的MBIM_DEVICE_CAPS_INFO结构中给出。
用户空间管理应用程序负责在建立MBIM IP会话之前添加新的VLAN链接，其中SessionId大于0。这些链接可以通过正常的VLAN内核接口添加，无论是ioctl还是netlink。
例如，添加一个SessionId为3的MBIM IP会话的链接：
:: 

  ip link add link wwan0 name wwan0.3 type vlan id 3

驱动程序将自动将“wwan0.3”网络设备映射到MBIM IP会话3。
设备服务流（DSS）
----------------------------
MBIM 还允许最多 256 个非 IP 数据流通过同一个共享的 USB 数据通道进行复用。cdc_mbim 驱动程序将这些会话建模为主 wwanY 设备下的另一组 802.1q VLAN 子设备，将 MBIM DSS 会话 A 映射到 VLAN ID (256 + A)，适用于所有 A 的值。
设备的最大 A 值在 [1] 中第 10.5.29 节描述的 MBIM_DEVICE_SERVICES_INFO 结构中给出。
DSS VLAN 子设备作为共享 MBIM 数据通道与 MBIM DSS 意识用户空间应用程序之间的实际接口使用。
它并不是直接提供给最终用户的。假设发起 DSS 会话的用户空间应用程序也负责必要的数据帧格式化，并以适合该流类型的方式向最终用户呈现流。
网络设备 ABI 要求每个传输中的 DSS 数据帧都有一个虚拟的以太网头部。此头部的内容是任意的，但有以下例外：

- 使用 IP 协议（0x0800 或 0x86dd）的 TX 帧将被丢弃
- RX 帧的协议字段将设置为 ETH_P_802_3（但不会是正确格式的 802.3 帧）
- RX 帧的目的地址将设置为主设备的硬件地址

支持 DSS 的用户空间管理应用程序负责在 TX 时添加虚拟以太网头部并在 RX 时移除它。
这是一个简单的示例，使用常用工具，将 DssSessionId 5 导出为指向 /dev/nmea 符号链接的 pty 字符设备：
```
ip link add link wwan0 name wwan0.dss5 type vlan id 261
ip link set dev wwan0.dss5 up
socat INTERFACE:wwan0.dss5,type=2 PTY:,echo=0,link=/dev/nmea
```

这只是用于测试 DSS 服务的一个示例。支持特定 MBIM DSS 服务的用户空间应用程序预计会使用该服务所需的工具和编程接口。
请注意，为 DSS 会话添加 VLAN 链接完全是可选的。管理应用程序可以选择直接绑定到主网络设备的套接字，使用收到的 VLAN 标签将帧映射到正确的 DSS 会话，并在 TX 时添加带有适当标签的 18 字节 VLAN 以太网头部。在这种情况下建议使用套接字过滤器，仅匹配 DSS VLAN 子集。这可以避免将无关的 IP 会话数据不必要的复制到用户空间。例如：
```c
static struct sock_filter dssfilter[] = {
	/* 使用特殊负偏移量获取 VLAN 标签 */
	BPF_STMT(BPF_LD|BPF_B|BPF_ABS, SKF_AD_OFF + SKF_AD_VLAN_TAG_PRESENT),
	BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, 1, 0, 6), /* 真 */

	/* 验证 DSS VLAN 范围 */
	BPF_STMT(BPF_LD|BPF_H|BPF_ABS, SKF_AD_OFF + SKF_AD_VLAN_TAG),
	BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K, 256, 0, 4), /* 256 是第一个 DSS VLAN */
	BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K, 512, 3, 0), /* 511 是最后一个 DSS VLAN */

	/* 验证 Ethertype */
	BPF_STMT(BPF_LD|BPF_H|BPF_ABS, 2 * ETH_ALEN),
	BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, ETH_P_802_3, 0, 1),

	BPF_STMT(BPF_RET|BPF_K, (u_int)-1), /* 接受 */
	BPF_STMT(BPF_RET|BPF_K, 0), /* 忽略 */
};
```

标记 IP 会话 0 VLAN
------------------------
如上所述，MBIM IP 会话 0 被驱动程序视为特殊处理。它最初映射为 wwanY 网络设备上的未标记帧。
这种映射意味着对复用的 IPS 和 DSS 会话有一些限制，这可能并不总是实用：
- 任何 IPS 或 DSS 会话都不能使用大于 IP 会话 0 上的 MTU 的帧大小
- 除非代表 IP 会话 0 的网络设备也处于活动状态，否则任何 IPS 或 DSS 会话都不能处于活动状态

这些问题可以通过选择性地使驱动程序将 IP 会话 0 映射到 VLAN 子设备来避免，类似于所有其他 IP 会话。这种行为由添加 VLAN ID 4094 的 VLAN 链接触发。然后驱动程序将立即开始将 MBIM IP 会话 0 映射到此 VLAN，并在主 wwanY 设备上丢弃未标记的帧。
提示：将此 VLAN 子设备命名为 MBIM SessionID 而不是 VLAN ID 可能会让最终用户更少困惑。例如：
```
ip link add link wwan0 name wwan0.0 type vlan id 4094
```

VLAN 映射
------------

总结上述 cdc_mbim 驱动程序映射关系如下：
```
VLAN ID       MBIM 类型   MBIM SessionID           注释
---------------------------------------------------------
未标记        IPS         0                        a)
1 - 255       IPS         1 - 255 <VLANID>
256 - 511     DSS         0 - 255 <VLANID - 256>
512 - 4093                                        b)
4094          IPS         0                        c)

    a) 如果不存在 VLAN ID 4094 链接，则丢弃
    b) 不支持的 VLAN 范围，无条件丢弃
    c) 如果存在 VLAN ID 4094 链接，则丢弃
```

参考文献
==========

1) USB Implementers Forum, Inc. - "Universal Serial Bus Communications Class Subclass Specification for Mobile Broadband Interface Model", Revision 1.0 (Errata 1), May 1, 2013

      - http://www.usb.org/developers/docs/devclass_docs/

2) USB Implementers Forum, Inc. - "Universal Serial Bus Communications Class Subclass Specifications for Network Control Model Devices", Revision 1.0 (Errata 1), November 24, 2010

      - http://www.usb.org/developers/docs/devclass_docs/

3) libmbim - "一个基于 glib 的库，用于与使用移动宽带接口模型 (MBIM) 协议的 WWAN 调制解调器和设备通信"

      - http://www.freedesktop.org/wiki/Software/libmbim/

4) ModemManager - "一个通过 D-Bus 激活的守护进程，用于控制移动宽带 (2G/3G/4G) 设备和连接"

      - http://www.freedesktop.org/wiki/Software/ModemManager/

5) "MBIM (Mobile Broadband Interface Model) Registry"

       - http://compliance.usb.org/mbim/

6) "/sys/kernel/debug/usb/devices 输出格式"

       - Documentation/driver-api/usb/usb.rst

7) "/sys/bus/usb/devices/.../descriptors"

       - Documentation/ABI/stable/sysfs-bus-usb
