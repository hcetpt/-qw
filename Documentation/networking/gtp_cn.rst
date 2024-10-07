SPDX 许可证标识符: GPL-2.0

=====================================
Linux 内核 GTP 隧道模块
=====================================

文档作者：
		 Harald Welte <laforge@gnumonks.org> 和
		 Andreas Schultz <aschultz@tpip.net>

在 'drivers/net/gtp.c' 文件中，你可以找到一个内核级别的 GTP 隧道端点实现。
什么是 GTP
===========

GTP 是通用隧道协议（Generic Tunnel Protocol），这是一个 3GPP 协议，用于在移动站（如手机、调制解调器）和外部分组数据网络（例如互联网）之间传输用户 IP 负载。
因此，当你从手机上启动一个“数据连接”时，手机会使用控制面来建立与外部数据网络之间的这种隧道。隧道的两端分别位于手机和网关上，所有中间节点只是传输封装的数据包。
手机本身并不实现 GTP，而是使用其他技术相关的协议栈来传输用户 IP 负载，例如 LLC/SNDCP/RLC/MAC。
在蜂窝运营商基础设施中的某个网络元素内部（GPRS/EGPRS 或经典 UMTS 中的 SGSN，3G 微小区中的 hNodeB，4G/LTE 中的 eNodeB），蜂窝协议堆栈会被转换为 GTP *而不破坏端到端的隧道*。因此，中间节点只执行特定的中继功能。
在某个时刻，GTP 数据包最终到达所谓的 GGSN（GSM/UMTS）或 P-GW（LTE），这些设备终止隧道，解封装数据包，并将其转发到外部分组数据网络。这可以是公共互联网，也可以是任何私有 IP 网络（甚至理论上还可以是非 IP 网络，如 X.25）。
你可以在 3GPP TS 29.060 中找到该协议规范，通过 3GPP 网站公开获取：http://www.3gpp.org/DynaReport/29060.htm

为了方便起见，下面提供了一个直接链接到 v13.6.0 的 PDF 文件：
http://www.etsi.org/deliver/etsi_ts/129000_129099/129060/13.06.00_60/ts_129060v130600p.pdf

Linux GTP 隧道模块
===============================

该模块实现了隧道端点的功能，即它能够解封装来自手机上行链路的隧道 IP 数据包，并将从外部分组网络接收的原始 IP 数据包封装后发送到下行链路的手机。
它 *仅* 实现了所谓的“用户面”，承载用户 IP 负载，称为 GTP-U。它不实现“控制面”，后者是一个用于建立和拆除 GTP 隧道（GTP-C）的信令协议。
因此，要有一个正常工作的 GGSN/P-GW 系统，你需要一个用户空间程序来实现 GTP-C 协议，并使用 GTP-U 模块在内核中提供的 netlink 接口来配置内核模块。
这种分离架构遵循了其他协议的隧道模块，例如 PPPoE 或 L2TP，在这些协议中，你也运行一个用户空间守护进程来处理隧道建立、认证等，而数据面则在内核中加速。
不要被术语所迷惑：GTP用户面（GTP User Plane）通过内核加速路径，而GTP控制面（GTP Control Plane）则运行在用户空间（Userspace）。

该模块的官方网站位于：
https://osmocom.org/projects/linux-kernel-gtp-u/wiki

支持Linux内核GTP-U的用户空间程序
==================================

截至本文撰写时，至少有两个自由软件实现了GTP-C，并且可以通过netlink接口利用Linux内核的GTP-U支持：

* OpenGGSN（经典的2G/3G GGSN，使用C语言编写）:
  https://osmocom.org/projects/openggsn/wiki/OpenGGSN

* ergw（GGSN + P-GW，使用Erlang编写）:
  https://github.com/travelping/ergw

用户空间库/命令行工具
======================

有一个名为“libgtpnl”的用户空间库，基于libmnl，并实现了一个面向netlink接口的C语言API，该接口由内核GTP模块提供：

http://git.osmocom.org/libgtpnl/

协议版本
========

GTP-U有两种不同的版本：v0 [GSM TS 09.60] 和 v1 [3GPP TS 29.281]。这两种版本都在内核GTP模块中得到了实现。
版本0是一个遗留版本，并已在最近的3GPP规范中废弃。
GTP-U使用UDP传输PDU。接收的UDP端口为GTPv1-U的2152和GTPv0-U的3386。
GTP-C有三个版本：v0、v1和v2。由于内核不实现GTP-C，我们不需要关心这一点。这是用户空间中的控制面实现的责任。

IPv6
====

3GPP规范指出，可以在内部（用户）IP层或外部（传输）IP层上使用IPv4或IPv6。
不幸的是，当前内核模块既不支持用于用户IP负载的IPv6，也不支持用于外部IP层的IPv6。欢迎提交补丁或其他贡献来修复这个问题！

邮件列表
========

如果您有关于如何从自己的软件中使用内核GTP模块的问题，或者想要为代码做出贡献，请使用osmocom-net-grps邮件列表进行相关讨论。该列表可以通过osmocom-net-gprs@lists.osmocom.org访问，管理订阅的邮件管理界面位于：
https://lists.osmocom.org/mailman/listinfo/osmocom-net-gprs

问题跟踪器
===========

Osmocom项目为内核GTP-U模块维护了一个问题跟踪器，地址为：
https://osmocom.org/projects/linux-kernel-gtp-u/issues

历史/致谢
=========

该模块最初由Harald Welte于2012年创建，但从未完成。Pablo接手了Harald留下的工作，但由于缺乏用户兴趣，它从未合并。
2015年，Andreas Schultz加入了进来，修复了许多bug，增加了新功能，并最终推动我们将其合并到主线，在4.7.0版本中被合并。

架构细节
========

本地GTP-U实体和隧道标识
------------------------

GTP-U使用UDP传输PDU。接收的UDP端口为GTPv1-U的2152和GTPv0-U的3386。
每个IP地址只有一个GTP-U实体（因此只有一个SGSN/GGSN/S-GW/PDN-GW实例）。隧道终端标识符（TEID）在每个GTP-U实体中是唯一的。
特定隧道仅由目的实体定义。由于目的端口是固定的，只有目的IP和TEID定义了一条隧道。源IP和端口对隧道没有意义。
因此：

  * 在发送时，远程实体由远程IP和隧道端点ID定义。源IP和端口没有意义，并且可以随时更改。
  * 在接收时，本地实体由本地目的IP和隧道端点ID定义。源IP和端口没有意义，并且可以随时更改。

根据[3GPP TS 29.281]第4.3.0节的规定：

  GTP-U报头中的TEID用于解复用从远程隧道端点传入的流量，以便以允许不同用户、不同的数据包协议和不同的QoS级别的方式将流量交付给用户面实体。
因此，两个远程GTP-U端点不应使用相同的TEID值向GTP-U协议实体发送流量，除非作为移动性过程的一部分进行数据转发。

上述定义仅说明了两个远程GTP-U端点不应当向同一个TEID发送流量，但它并没有禁止或排除这种情形。事实上，提到的移动性过程使得GTP-U实体必须接受来自多个或未知对等体的TEID流量。
因此，接收端仅基于TEID来识别隧道，而不是基于源IP！

APN与网络设备
=================

GTP-U驱动为每个Gi/SGi接口创建一个Linux网络设备。
[3GPP TS 29.281]称Gi/SGi参考点为接口。这可能导致误解，认为GGSN/P-GW只能有一个这样的接口。
正确的说法是，Gi/SGi参考点定义了基于GTP-U隧道和IP网络的3GPP分组域（PDN）之间的互操作。
3GPP文档中没有任何规定限制GGSN/P-GW实现的Gi/SGi接口数量。
[3GPP TS 29.061]第11.3节明确指出，特定Gi/SGi接口的选择是通过接入点名称（APN）进行的：

  每个私有网络管理自己的地址分配。通常这将导致不同的私有网络具有重叠的地址范围。在GGSN/P-GW和每个私有网络之间使用逻辑上独立的连接（例如IP-in-IP隧道或第二层虚拟电路）。
在这种情况下，单凭IP地址并不一定是唯一的。APN（接入点名称）与IPv4地址和/或IPv6前缀的组合才是唯一的。

为了支持重叠地址范围的用例，每个APN都映射到一个独立的Gi/SGi接口（网络设备）。
.. 注意::

   接入点名称纯粹是一个控制面（GTP-C）的概念
在GTP-U层面上，只有隧道端点标识符（TEID）出现在GTP-U数据包中，并且网络设备是通过这些标识符来识别的。

因此，对于给定的UE（用户设备），从IP到PDN（分组数据网络）的映射如下：

  * 网络设备 + MS IP（移动台IP）-> 对端IP + 对端TEID，

而从PDN到IP网络的映射为：

  * 本地GTP-U IP + TEID -> 网络设备

此外，在接收到的T-PDU被注入到网络设备之前，会检查MS IP是否与PDP上下文中记录的IP相符。
