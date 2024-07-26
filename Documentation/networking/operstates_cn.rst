### SPDX 许可证标识符：GPL-2.0

#### 操作状态

#### 1. 引言

Linux 区分接口的管理状态和操作状态。管理状态是通过命令“ip link set dev <dev> up 或 down”设置的结果，反映了管理员是否希望使用该设备进行数据传输。
然而，仅仅因为管理员启用了接口，并不意味着它就可以被使用 —— 以太网需要连接到交换机上，并且根据站点的网络策略和配置，在可以传输用户数据之前可能还需要执行 802.1X 身份验证。操作状态显示了接口传输用户数据的能力。
由于 802.1X 的存在，用户空间必须能够影响操作状态。为了适应这一点，操作状态被分为两部分：驱动程序可以设置的两个标志，以及一个符合 RFC2863 的状态，该状态基于这些标志、策略和在特定规则下可以从用户空间更改。

#### 2. 从用户空间查询

管理状态和操作状态都可以通过 netlink 操作 RTM_GETLINK 查询。还可以订阅 RTNLGRP_LINK 来接收接口处于管理启用状态时的更新通知。这对于从用户空间设置非常重要。
以下值包含了接口的状态：

- `ifinfomsg::if_flags & IFF_UP`: 接口处于管理启用状态。
- `ifinfomsg::if_flags & IFF_RUNNING`: 接口处于 RFC2863 操作状态 UP 或 UNKNOWN。这是为了向后兼容，路由守护进程、DHCP 客户端可以使用此标志来判断是否应该使用该接口。
- `ifinfomsg::if_flags & IFF_LOWER_UP`: 驱动程序已发出 netif_carrier_on() 信号。
- `ifinfomsg::if_flags & IFF_DORMANT`: 驱动程序已发出 netif_dormant_on() 信号。

##### TLV IFLA_OPERSTATE

包含接口的 RFC2863 状态的数值表示：

- `IF_OPER_UNKNOWN (0)`：接口处于未知状态，既没有驱动程序也没有用户空间设置操作状态。对于用户数据而言，应考虑这个接口，因为并非每个驱动程序都实现了设置操作状态的功能。
- `IF_OPER_NOTPRESENT (1)`：当前内核中未使用（通常不存在的接口会消失），仅是一个数值占位符。
- `IF_OPER_DOWN (2)`：接口无法在第一层传输数据，例如以太网未连接或接口处于管理关闭状态。
- `IF_OPER_LOWERLAYERDOWN (3)`：堆叠在一个处于 IF_OPER_DOWN 状态的接口之上的接口会显示这种状态（例如 VLAN）。
- `IF_OPER_TESTING (4)`：接口处于测试模式，例如正在执行驱动自测或介质（电缆）测试。在测试完成前，它不能用于正常的数据传输。
IF_OPER_DORMANT (5):  
接口为L1就绪状态，但正在等待外部事件（例如某种协议建立完成）。(如802.1X)

IF_OPER_UP (6):  
接口处于可操作状态且可以使用  
此TLV也可以通过sysfs查询

TLV IFLA_LINKMODE  
--------------

包含链路策略。这对于用户空间交互是必需的，具体描述如下  
此TLV也可以通过sysfs查询

3. 内核驱动API  
==================

内核驱动能够访问两个标志位，它们映射到IFF_LOWER_UP和IFF_DORMANT。这些标志位可以从任何地方设置，甚至从中断中设置。可以保证只有驱动程序有写入权限，但如果不同层次的驱动程序修改同一个标志位，则驱动程序需要提供必要的同步机制。

__LINK_STATE_NOCARRIER, 映射到!IFF_LOWER_UP:  

驱动程序使用netif_carrier_on()来清除该标志位，使用netif_carrier_off()来设置该标志位。在调用netif_carrier_off()时，调度器会停止发送数据包。"carrier"这个词及其取反形式是历史遗留的，可以将其理解为底层。  
需要注意的是，对于某些不管理任何实际硬件的软设备，可以在用户空间中设置这个位。应该使用TLV IFLA_CARRIER来实现这一点。
可以通过netif_carrier_ok()查询该位的状态。

__LINK_STATE_DORMANT, 映射到IFF_DORMANT:  

由驱动程序设置以表示设备暂时无法使用，因为需要完成一些由驱动控制的协议建立过程。对应的函数包括：netif_dormant_on()用于设置该标志位，netif_dormant_off()用于清除该标志位，netif_dormant()用于查询该标志位的状态。
在分配设备时，__LINK_STATE_NOCARRIER和__LINK_STATE_DORMANT两个标志位都会被清除，因此有效的状态等同于netif_carrier_ok()和!netif_dormant()。
每当驱动程序更改这些标志之一时，就会安排一个工作队列事件，将标志组合转换为 IFLA_OPERSTATE，具体如下：

- `!netif_carrier_ok()`:
  - 如果接口是堆叠的，则为`IF_OPER_LOWERLAYERDOWN`；否则为`IF_OPER_DOWN`。内核能够识别出堆叠接口是因为它们的`ifindex != iflink`。
- `netif_carrier_ok() && netif_dormant()`:
  - `IF_OPER_DORMANT`
- `netif_carrier_ok() && !netif_dormant()`:
  - 如果禁用了用户空间交互，则为`IF_OPER_UP`。否则为`IF_OPER_DORMANT`，之后用户空间可以触发`IF_OPER_UP`状态的转换。

### 4. 从用户空间设置

应用必须使用netlink接口来影响接口的RFC2863运行状态。通过RTM_SETLINK将IFLA_LINKMODE设置为1指示内核，当驱动程序设置`netif_carrier_ok() && !netif_dormant()`组合时，接口应变为`IF_OPER_DORMANT`而不是`IF_OPER_UP`。之后，只要驱动程序没有设置`netif_carrier_off()`或`netif_dormant_on()`，用户空间应用就可以将IFLA_OPERSTATE设置为`IF_OPER_DORMANT`或`IF_OPER_UP`。用户空间所做的更改会通过netlink组RTNLGRP_LINK进行多播。

因此，一个802.1X认证客户端与内核的交互方式如下：

- 订阅RTNLGRP_LINK
- 通过RTM_SETLINK将IFLA_LINKMODE设置为1
- 查询RTM_GETLINK一次以获取初始状态
- 如果初始标志不是`(IFF_LOWER_UP && !IFF_DORMANT)`，则等待直到netlink多播信号指示此状态
- 执行802.1X认证，如果标志再次下降则终止
- 如果认证成功，则发送RTM_SETLINK将operstate设置为`IF_OPER_UP`；否则设置为`IF_OPER_DORMANT`
- 观察operstate和IFF_RUNNING如何通过netlink多播回显
- 如果802.1X重新认证失败，则将接口设置回`IF_OPER_DORMANT`
- 如果内核改变IFF_LOWER_UP或IFF_DORMANT标志，则重启
- 如果认证客户端关闭，则将IFLA_LINKMODE恢复为0，并将IFLA_OPERSTATE设置为合理值

路由守护进程或DHCP客户端只需关注IFF_RUNNING或等待operstate变为`IF_OPER_UP`/`IF_OPER_UNKNOWN`即可考虑接口/查询DHCP地址。

对于技术问题和/或评论，请发送电子邮件至Stefan Rompf (stefan at loplof.de)。
