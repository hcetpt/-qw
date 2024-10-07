```SPDX-License-Identifier: GPL-2.0

==================
操作状态
==================

1. 引言
===============

Linux 区分接口的管理状态和操作状态。管理状态是通过命令 "ip link set dev <dev> up or down" 设置的结果，反映了管理员是否希望使用该设备进行数据传输。
然而，仅仅因为管理员启用了接口，并不意味着它就是可用的——以太网需要连接到交换机上，并且根据站点的网络策略和配置，可能还需要执行 802.1X 认证才能传输用户数据。操作状态显示了接口传输用户数据的能力。
由于 802.1X 的存在，用户空间必须被授予影响操作状态的可能性。为此，操作状态被分为两个部分：两个只能由驱动程序设置的标志，以及一个从这些标志、策略中得出的、符合 RFC2863 的状态，并且在特定规则下可以从用户空间更改。

2. 从用户空间查询
==========================

管理状态和操作状态都可以通过 netlink 操作 RTM_GETLINK 查询。也可以订阅 RTNLGRP_LINK，在接口处于管理启用状态时接收更新通知。这对于从用户空间设置非常重要。
这些值包含接口状态：

ifinfomsg::if_flags & IFF_UP：
 接口处于管理启用状态

ifinfomsg::if_flags & IFF_RUNNING：
 接口处于 RFC2863 操作状态 UP 或 UNKNOWN。这是为了向后兼容，路由守护进程和 DHCP 客户端可以使用此标志来确定是否应该使用该接口

ifinfomsg::if_flags & IFF_LOWER_UP：
 驱动程序已发出 netif_carrier_on() 信号

ifinfomsg::if_flags & IFF_DORMANT：
 驱动程序已发出 netif_dormant_on() 信号

TLV IFLA_OPERSTATE
------------------

包含接口的 RFC2863 状态的数值表示：

IF_OPER_UNKNOWN (0)：
 接口处于未知状态，既没有驱动程序也没有用户空间设置操作状态。由于并非每个驱动程序都实现了设置操作状态，因此接口必须被视为可以用于用户数据

IF_OPER_NOTPRESENT (1)：
 当前内核未使用（不存在的接口通常会消失），只是一个数值占位符

IF_OPER_DOWN (2)：
 接口无法在 L1 层传输数据，例如以太网未插或接口处于管理关闭状态

IF_OPER_LOWERLAYERDOWN (3)：
 堆叠在一个 IF_OPER_DOWN 接口上的接口将显示此状态（例如 VLAN）

IF_OPER_TESTING (4)：
 接口处于测试模式，例如执行驱动自测或媒体（电缆）测试。在测试完成之前，不能用于正常流量
```
IF_OPER_DORMANT (5):
接口处于L1激活状态，但等待外部事件（例如协议建立）。(802.1X)

IF_OPER_UP (6):
接口运行正常且可以使用
此TLV也可以通过sysfs查询

TLV IFLA_LINKMODE
-----------------
包含链路策略。这对于下面描述的用户空间交互是必需的
此TLV也可以通过sysfs查询

3. 内核驱动API
====================
内核驱动可以访问两个标志位，分别对应IFF_LOWER_UP和IFF_DORMANT。这些标志位可以从任何地方设置，甚至在中断中。可以保证只有驱动程序具有写入访问权限，但是，如果驱动程序的不同层次操作同一个标志位，则驱动程序需要提供所需的同步。

__LINK_STATE_NOCARRIER，映射到!IFF_LOWER_UP：
驱动程序使用netif_carrier_on()来清除该标志位，使用netif_carrier_off()来设置该标志位。在调用netif_carrier_off()时，调度器会停止发送数据包。“carrier”这个名称及其取反是历史遗留下来的，可以将其视为底层。
需要注意的是，对于某些不管理任何实际硬件的软设备，可以从用户空间设置这个位。应使用TLV IFLA_CARRIER来实现这一点。
可以使用netif_carrier_ok()来查询该位的状态。

__LINK_STATE_DORMANT，映射到IFF_DORMANT：
由驱动程序设置，表示设备还不能使用，因为需要完成一些由驱动程序控制的协议建立。相应的函数有netif_dormant_on()来设置该标志位，netif_dormant_off()来清除它，以及netif_dormant()来查询其状态。
在设备分配时，这两个标志位__LINK_STATE_NOCARRIER和__LINK_STATE_DORMANT都会被清除，因此有效状态等同于netif_carrier_ok()和!netif_dormant()。
每当驱动程序更改这些标志之一时，会安排一个工作队列事件将标志组合转换为 IFLA_OPERSTATE，具体如下：

- `!netif_carrier_ok()`:
  如果接口是堆叠的，则为 `IF_OPER_LOWERLAYERDOWN`；否则为 `IF_OPER_DOWN`。内核可以通过检查 `ifindex != iflink` 来识别堆叠接口。
- `netif_carrier_ok() && netif_dormant()`:
  `IF_OPER_DORMANT`
- `netif_carrier_ok() && !netif_dormant()`:
  如果禁用了用户空间交互，则为 `IF_OPER_UP`。否则为 `IF_OPER_DORMANT`，但用户空间可以随后发起 `IF_OPER_UP` 转换。

### 从用户空间设置
========================

应用程序必须使用 netlink 接口来影响接口的 RFC2863 运行状态。通过 RTM_SETLINK 将 IFLA_LINKMODE 设置为 1 指示内核，当驱动程序设置 `netif_carrier_ok() && !netif_dormant()` 时，接口应进入 `IF_OPER_DORMANT` 而不是 `IF_OPER_UP`。之后，用户空间应用可以在驱动程序不设置 `netif_carrier_off()` 或 `netif_dormant_on()` 的情况下将 IFLA_OPERSTATE 设置为 `IF_OPER_DORMANT` 或 `IF_OPER_UP`。用户空间所做的更改会在 netlink 组 RTNLGRP_LINK 上进行多播。

基本上，802.1X 认证客户端与内核的交互如下：

- 订阅 RTNLGRP_LINK
- 通过 RTM_SETLINK 将 IFLA_LINKMODE 设置为 1
- 发送一次 RTM_GETLINK 请求以获取初始状态
- 如果初始标志不是 `(IFF_LOWER_UP && !IFF_DORMANT)`，则等待 netlink 多播信号指示该状态
- 执行 802.1X 认证，如果标志再次下降则终止
- 如果认证成功，发送 RTM_SETLINK 将 operstate 设置为 `IF_OPER_UP`；否则设置为 `IF_OPER_DORMANT`
- 观察 operstate 和 IFF_RUNNING 通过 netlink 多播回显
- 如果 802.1X 再认证失败，将接口设置回 `IF_OPER_DORMANT`
- 如果内核更改了 IFF_LOWER_UP 或 IFF_DORMANT 标志，则重启

如果认证客户端关闭，请将 IFLA_LINKMODE 恢复为 0，并将 IFLA_OPERSTATE 设置为合理值。

路由守护进程或 DHCP 客户端只需关心 IFF_RUNNING 或等待 operstate 变为 `IF_OPER_UP` / `IF_OPER_UNKNOWN` 即可考虑该接口 / 查询 DHCP 地址。

对于技术问题和/或评论，请发送电子邮件至 Stefan Rompf（stefan at loplof.de）。
