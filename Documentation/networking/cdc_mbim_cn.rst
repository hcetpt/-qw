SPDX 许可证标识符: GPL-2.0

======================================================
cdc_mbim - CDC MBIM 移动宽带调制解调器的驱动程序
======================================================

cdc_mbim 驱动程序支持符合“移动宽带接口模型通用串行总线通信类子类规范”[1]的 USB 设备，该规范是“网络控制模型设备通用串行总线通信类子类规范”[2]的进一步发展，并针对移动宽带设备（也称为“3G/LTE 调制解调器”）进行了优化。

命令行参数
=======================

cdc_mbim 驱动程序本身没有参数。但是，对于 NCM 1.0 向后兼容的 MBIM 功能（如 [1] 第 3.2 节中定义的“NCM/MBIM 功能”）的探测行为会受到 cdc_ncm 驱动程序参数的影响：

prefer_mbim
-----------
:类型:           布尔值
:有效范围:       N/Y (0-1)
:默认值:         Y (MBIM 优先)

此参数设置 NCM/MBIM 功能的系统策略。此类功能将根据 prefer_mbim 设置由 cdc_ncm 驱动程序或 cdc_mbim 驱动程序处理。将 prefer_mbim 设置为 N 将使 cdc_mbim 驱动程序忽略这些功能，并让 cdc_ncm 驱动程序处理它们。
此参数可写，并且可以在任何时候更改。为了使更改对绑定到“错误”驱动程序的 NCM/MBIM 功能生效，需要手动解除绑定/绑定。

基本使用
===========

当未被管理时，MBIM 功能处于非活动状态。cdc_mbim 驱动程序仅提供用户空间接口以访问 MBIM 控制通道，并不会参与功能的管理。这意味着始终需要一个用户空间的 MBIM 管理应用程序来启用 MBIM 功能。
这样的用户空间应用程序包括但不限于：

 - mbimcli（随 libmbim [3] 库一起提供），和
 - ModemManager [4]

建立 MBIM IP 会话至少需要管理应用程序执行以下操作：

 - 打开控制通道
 - 配置网络连接设置
 - 连接到网络
 - 配置 IP 接口

管理应用程序开发
-------------------

下面描述了驱动程序与用户空间接口。MBIM 控制通道协议在 [1] 中有描述。

MBIM 控制通道用户空间 ABI
==================================

/dev/cdc-wdmX 字符设备
------------------------------

驱动程序使用 cdc-wdm 驱动程序作为子驱动程序创建双向管道到 MBIM 功能控制通道。用户空间端的控制通道管道是一个 /dev/cdc-wdmX 字符设备。
cdc_mbim 驱动程序不处理或监控控制通道上的消息。通道完全委托给用户空间管理应用程序。因此，由该应用程序确保其遵守 [1] 中的所有控制通道要求。
cdc-wdmX 设备作为 MBIM 控制接口 USB 设备的子设备创建。可以通过 sysfs 查找特定 MBIM 功能关联的字符设备。例如：

bjorn@nemi:~$ ls /sys/bus/usb/drivers/cdc_mbim/2-4:2.12/usbmisc
cdc-wdm0

bjorn@nemi:~$ grep . /sys/bus/usb/drivers/cdc_mbim/2-4:2.12/usbmisc/cdc-wdm0/dev
180:0

USB 配置描述符
-----------------

CDC MBIM 功能描述符中的 wMaxControlMessage 字段限制了最大控制消息大小。管理应用程序负责协商符合 [1] 第 9.3.1 节要求的控制消息大小，同时考虑该描述符字段。
用户空间应用程序可以使用 [6] 或 [7] 中描述的两种 USB 配置描述符内核接口之一来访问 MBIM 功能的 CDC MBIM 功能描述符。
另请参阅下面的 ioctl 文档。

分片
-------------

用户空间应用程序负责所有控制消息的分片和反分片，如 [1] 第 9.5 节所述。
### /dev/cdc-wdmX write()
---------------------
来自管理应用程序的MBIM控制消息**不得**超过协商后的控制消息大小。

### /dev/cdc-wdmX read()
--------------------
管理应用程序**必须**接受最大达到协商后的控制消息大小的控制消息。

### /dev/cdc-wdmX ioctl()
---------------------
IOCTL_WDM_MAX_COMMAND: 获取最大命令大小
此ioctl调用返回MBIM设备的CDC MBIM功能描述符中的wMaxControlMessage字段。这是为了方便起见，避免从用户空间解析USB描述符：
```c
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
        printf("wMaxControlMessage is %d\n", max);
}
```

### 定制设备服务
----------------------
MBIM规范允许供应商自由定义额外的服务。cdc_mbim驱动程序完全支持这一点。
对于新的MBIM服务（包括供应商自定义的服务）的支持全部在用户空间实现，就像MBIM控制协议的其余部分一样。

新服务应当在MBIM注册表中注册。

### MBIM数据通道用户空间ABI
=================================

### wwanY网络设备
--------------------
cdc_mbim驱动程序将MBIM数据通道表示为一个“wwan”类型的单一网络设备。该网络设备最初映射到MBIM IP会话0。

### 多路复用IP会话（IPS）
-----------------------------
MBIM允许通过单一USB数据通道多路复用最多256个IP会话。cdc_mbim驱动程序将这些IP会话建模为主wwanY设备的802.1q VLAN子设备，将MBIM IP会话Z映射到VLAN ID Z，对于所有大于0的Z值。
设备的最大Z值在[1]第10.5.1节中描述的MBIM_DEVICE_CAPS_INFO结构中给出。
用户空间管理应用程序负责在建立SessionId大于0的MBIM IP会话之前添加新的VLAN链接。这些链接可以通过正常的VLAN内核接口添加，无论是ioctl还是netlink。
例如，为SessionId为3的MBIM IP会话添加链接：
```
ip link add link wwan0 name wwan0.3 type vlan id 3
```
驱动程序会自动将“wwan0.3”网络设备映射到MBIM IP会话3。
### 设备服务流 (DSS)

MBIM 还允许最多 256 个非 IP 数据流通过同一共享的 USB 数据通道进行复用。cdc_mbim 驱动程序将这些会话建模为主 wwanY 设备的另一组 802.1q VLAN 子设备，将 MBIM DSS 会话 A 映射到 VLAN ID (256 + A)，适用于所有的 A 值。
设备最大 A 的值在 [1] 的第 10.5.29 节中描述的 MBIM_DEVICE_SERVICES_INFO 结构中给出。
DSS VLAN 子设备作为共享 MBIM 数据通道与了解 MBIM DSS 的用户空间应用程序之间的实用接口使用。
它并不打算直接呈现给最终用户。假设发起 DSS 会话的用户空间应用程序也负责 DSS 数据的必要帧处理，以适当的方式向最终用户展示流类型。

网络设备 ABI 要求每个传输的 DSS 数据帧都包含一个虚拟的以太网头部。此头部的内容是任意的，但有以下例外：

- 使用 IP 协议 (0x0800 或 0x86dd) 的发送帧将被丢弃
- 接收帧的协议字段将设置为 ETH_P_802_3（但不会是正确格式的 802.3 帧）
- 接收帧的目标地址将设置为主设备的硬件地址

支持 DSS 的用户空间管理应用程序负责在发送时添加虚拟以太网头部并在接收时去除它。
这是一个使用常见工具的简单示例，将 DssSessionId 5 导出为指向 /dev/nmea 符号链接的 pty 字符设备：

```shell
ip link add link wwan0 name wwan0.dss5 type vlan id 261
ip link set dev wwan0.dss5 up
socat INTERFACE:wwan0.dss5,type=2 PTY:,echo=0,link=/dev/nmea
```

这只是一个示例，最适合测试 DSS 服务。支持特定 MBIM DSS 服务的用户空间应用程序预计会使用该服务所需的工具和编程接口。

请注意，为 DSS 会话添加 VLAN 链接完全是可选的。管理应用程序也可以选择直接绑定到主网络设备的包套接字，使用接收到的 VLAN 标签将帧映射到正确的 DSS 会话，并在发送时添加 18 字节的带有适当标签的 VLAN 以太网头部。在这种情况下，建议使用套接字过滤器，只匹配 DSS VLAN 子集。这样可以避免将无关的 IP 会话数据不必要的复制到用户空间。例如：

```c
static struct sock_filter dssfilter[] = {
	/* 使用特殊负偏移获取 VLAN 标签 */
	BPF_STMT(BPF_LD|BPF_B|BPF_ABS, SKF_AD_OFF + SKF_AD_VLAN_TAG_PRESENT),
	BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, 1, 0, 6), /* true */

	/* 验证 DSS VLAN 范围 */
	BPF_STMT(BPF_LD|BPF_H|BPF_ABS, SKF_AD_OFF + SKF_AD_VLAN_TAG),
	BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K, 256, 0, 4), /* 256 是第一个 DSS VLAN */
	BPF_JUMP(BPF_JMP|BPF_JGE|BPF_K, 512, 3, 0), /* 511 是最后一个 DSS VLAN */

	/* 验证 ethertype */
	BPF_STMT(BPF_LD|BPF_H|BPF_ABS, 2 * ETH_ALEN),
	BPF_JUMP(BPF_JMP|BPF_JEQ|BPF_K, ETH_P_802_3, 0, 1),

	BPF_STMT(BPF_RET|BPF_K, (u_int)-1), /* 接受 */
	BPF_STMT(BPF_RET|BPF_K, 0), /* 忽略 */
};
```

### 标记的 IP 会话 0 VLAN

如上所述，MBIM IP 会话 0 被驱动程序视为特殊。最初，它被映射到 wwanY 网络设备上的未标记帧。
这种映射意味着对复用的 IPS 和 DSS 会话存在一些限制，这些限制可能并不总是实际可行的：

- 没有任何 IPS 或 DSS 会话可以使用大于 IP 会话 0 上的 MTU 的帧大小
- 除非代表 IP 会话 0 的网络设备也处于活动状态，否则没有任何 IPS 或 DSS 会话可以处于活动状态

这些问题可以通过可选地让驱动程序将 IP 会话 0 映射到 VLAN 子设备来避免，类似于所有其他 IP 会话。这种行为由添加一个具有魔法 VLAN ID 4094 的 VLAN 链接触发。然后驱动程序将立即开始将 MBIM IP 会话 0 映射到这个 VLAN，并且将丢弃主 wwanY 设备上的未标记帧。
提示：对于最终用户来说，将此 VLAN 子设备命名为 MBIM SessionID 而不是 VLAN ID 可能会更少混淆。例如：

```shell
ip link add link wwan0 name wwan0.0 type vlan id 4094
```

### VLAN 映射

总结上面描述的 cdc_mbim 驱动程序映射关系，我们有以下 VLAN 标签与 wwanY 网络设备上的 MBIM 会话之间的关系：

| VLAN ID | MBIM 类型 | MBIM SessionID | 注释 |
|---------|-----------|---------------|------|
| 无标签  | IPS       | 0             | a)   |
| 1-255   | IPS       | 1-255<VLANID> |      |
| 256-511 | DSS       | 0-255<VLANID-256> |      |
| 512-4093|           |               | b)   |
| 4094    | IPS       | 0             | c)   |

a) 如果不存在 VLAN ID 4094 的链接，则丢弃；否则未标记帧被丢弃  
b) 不支持的 VLAN 范围，无条件地丢弃  
c) 如果存在 VLAN ID 4094 的链接，则丢弃未标记帧；否则丢弃

### 参考资料

1. USB Implementers Forum, Inc. - “通用串行总线通信类子类规范移动宽带接口模型”，修订版 1.0（勘误表 1），2013 年 5 月 1 日

   - http://www.usb.org/developers/docs/devclass_docs/

2. USB Implementers Forum, Inc. - “通用串行总线通信类子类规范网络控制模型设备”，修订版 1.0（勘误表 1），2010 年 11 月 24 日

   - http://www.usb.org/developers/docs/devclass_docs/

3. libmbim - “基于 glib 的用于与使用移动宽带接口模型 (MBIM) 协议的 WWAN 调制解调器和设备进行通信的库”

   - http://www.freedesktop.org/wiki/Software/libmbim/

4. ModemManager - “一个通过 DBus 激活的守护进程，用于控制移动宽带（2G/3G/4G）设备和连接”

   - http://www.freedesktop.org/wiki/Software/ModemManager/

5. “MBIM（移动宽带接口模型）注册”

   - http://compliance.usb.org/mbim/

6. “/sys/kernel/debug/usb/devices 输出格式”

   - 文档/driver-api/usb/usb.rst

7. “/sys/bus/usb/devices/.../descriptors”

   - 文档/ABI/stable/sysfs-bus-usb
