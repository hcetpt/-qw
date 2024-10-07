SPDX 许可证标识符: GPL-2.0

=============
DCCP 协议
=============

.. 目录
   - 简介
   - 缺失的功能
   - 套接字选项
   - Sysctl 变量
   - IOCTLs
   - 其他可调参数
   - 注意事项


简介
============
数据报拥塞控制协议（DCCP）是一种不可靠的、面向连接的协议，旨在解决 UDP 和 TCP 中存在的问题，特别是针对实时和多媒体（流媒体）流量。它分为一个基础协议（RFC 4340）和可插拔的拥塞控制模块，称为 CCIDs。就像可插拔的 TCP 拥塞控制一样，至少需要启用一个 CCID 才能使该协议正常工作。在 Linux 实现中，这是类似于 TCP 的 CCID2（RFC 4341）。其他 CCIDs，如与 TCP 兼容的 CCID3（RFC 4342），是可选的。

对于 CCIDs 的简要介绍以及如何选择适合特定应用的 CCID，请参阅 RFC 4340 第 10 节。
它有一个基础协议和可插拔的拥塞控制 ID（CCIDs）。
DCCP 是一个提议的标准（RFC 2026），作为协议的主页位于：http://www.ietf.org/html.charters/dccp-charter.html


缺失的功能
================
Linux 的 DCCP 实现目前不支持 RFCs 4340...42 中规定的所有功能。
已知的错误可以在以下网址找到：

	http://www.linuxfoundation.org/collaborate/workgroups/networking/todo#DCCP

为了获取更更新版本的 DCCP 实现，请考虑使用实验性的 DCCP 测试树；检查此树的说明位于：
http://www.linuxfoundation.org/collaborate/workgroups/networking/dccp_testing#Experimental_DCCP_source_tree


套接字选项
==============
DCCP_SOCKOPT_QPOLICY_ID 设置传出数据包的出队策略。它接受一个策略 ID 作为参数，并且只能在连接建立之前设置（即，在已建立的连接期间更改不被支持）。目前定义了两种策略：简单的策略（DCCPQ_POLICY_SIMPLE），不做任何特殊处理；以及基于优先级的变体（DCCPQ_POLICY_PRIO）。后者允许通过 sendmsg() 传递一个 u32 优先级值作为辅助数据，其中较高的数字表示较高的数据包优先级（类似于 SO_PRIORITY）。此辅助数据需要使用一个 cmsg(3) 消息头进行格式化，如下所示：

	cmsg->cmsg_level = SOL_DCCP;
	cmsg->cmsg_type = DCCP_SCM_PRIORITY;
	cmsg->cmsg_len = CMSG_LEN(sizeof(uint32_t)); /* 或 CMSG_LEN(4) */

DCCP_SOCKOPT_QPOLICY_TXQLEN 设置输出队列的最大长度。零值始终解释为无界队列长度。如果非零，则此参数的解释取决于当前的出队策略（见上文）：简单的策略将通过返回 EAGAIN 来强制固定队列大小，而基于优先级的策略则通过首先丢弃最低优先级的数据包来强制固定队列长度。此参数的默认值初始化自 /proc/sys/net/dccp/default/tx_qlen。
DCCP_SOCKOPT_SERVICE 设置服务。规范要求使用服务代码（RFC 4340，第 8.1.2 节）；如果未设置此套接字选项，则套接字将回退到 0（这意味着没有有效的服务代码）。对于主动套接字，此设置必须在 connect() 之前进行；指定多个代码没有效果（所有后续服务代码都将被忽略）。对于被动套接字，可以在调用 bind() 之前设置多达 32 个服务代码。
DCCP_SOCKOPT_GET_CUR_MPS 是只读的，并检索当前最大数据包大小（应用程序负载大小）以字节为单位，参见 RFC 4340 第 14 节。
DCCP_SOCKOPT_AVAILABLE_CCIDS 也是只读的，并返回端点支持的 CCIDs 列表。选项值是一个类型为 uint8_t 的数组，其大小作为选项长度传递。数组的最小大小为 4 个元素，optlen 参数返回的实际值始终反映内置 CCIDs 的真实数量。
DCCP_SOCKOPT_CCID 是写入专用的，并同时设置 TX 和 RX CCIDs，结合了接下来两个套接字选项的操作。此选项优于后两者，因为通常应用程序会在两个方向上使用相同类型的 CCID；并且目前对混合使用 CCIDs 的理解还不够充分。此套接字选项接受至少一个 uint8_t 值或一个 uint8_t 值数组作为参数，这些值必须匹配可用的 CCIDs（见上文）。必须在调用 connect() 或 listen() 之前在套接字上注册 CCIDs。
DCCP_SOCKOPT_TX_CCID 是可读写选项。它返回当前设置的 CCID（如果已设置），或者设置 TX CCID 的偏好列表，使用与 DCCP_SOCKOPT_CCID 相同的格式。
请注意，这里的 getsockopt 参数类型是 `int`，而不是 `uint8_t`。
DCCP_SOCKOPT_RX_CCID 与 DCCP_SOCKOPT_TX_CCID 类似，但针对的是 RX CCID。
DCCP_SOCKOPT_SERVER_TIMEWAIT 允许服务器（监听套接字）在关闭连接时保持 TIMEWAIT 状态（RFC 4340, 8.3）。通常情况下，关闭的服务器发送一个 CloseReq，此时客户端进入 TIMEWAIT 状态。当这个布尔类型的套接字选项被启用时，服务器会发送一个 Close 并进入 TIMEWAIT 状态。此选项必须在 accept() 返回后设置。
DCCP_SOCKOPT_SEND_CSCOV 和 DCCP_SOCKOPT_RECV_CSCOV 用于设置部分校验和覆盖（RFC 4340, 第 9.2 节）。默认情况下，校验和总是覆盖整个数据包，并且接收者只接受完全覆盖的应用数据。因此，在发送端使用此功能时，接收端也必须启用，并选择合适的 CsCov 值。
DCCP_SOCKOPT_SEND_CSCOV 设置发送端的校验和覆盖范围。值在 0 到 15 之间都是可接受的。默认设置为 0（完全覆盖），1 到 15 的值表示部分覆盖。
DCCP_SOCKOPT_RECV_CSCOV 用于接收端，并具有不同的含义：它设置了一个阈值，同样值在 0 到 15 之间都是可接受的。默认值 0 表示所有部分覆盖的数据包都将被丢弃。
值在 1 到 15 之间的表示最小覆盖值的数据包也是可接受的。数值越高，设置越严格（参见 [RFC 4340, 第 9.2.1 节]）。部分覆盖设置在接受后会被继承到子套接字中。
以下两个选项仅适用于 CCID 3，并且只能通过 getsockopt() 获取。
在这两种情况下，都会返回一个 TFRC 信息结构（定义在 `<linux/tfrc.h>` 中）。
DCCP_SOCKOPT_CCID_RX_INFO  
返回一个 `struct tfrc_rx_info` 到 optval；optval 和 optlen 的缓冲区必须设置为至少 `sizeof(struct tfrc_rx_info)` 的大小。

DCCP_SOCKOPT_CCID_TX_INFO  
返回一个 `struct tfrc_tx_info` 到 optval；optval 和 optlen 的缓冲区必须设置为至少 `sizeof(struct tfrc_tx_info)` 的大小。

在单向连接中，关闭未使用的半连接（通过 shutdown(SHUT_WR 或 SHUT_RD)）是有用的：这将减少每个数据包的处理成本。

Sysctl 变量
============
多个 DCCP 默认参数可以通过以下 sysctl 进行管理（sysctl net.dccp.default 或 /proc/sys/net/dccp/default）：

request_retries  
主动连接初始化重试次数（请求次数减一）之前超时。此外，它还控制另一端被动方的行为：该变量还设置了当初始握手没有从 RESPOND 进展到 OPEN（即没有收到初始请求后的 Ack）时，DCCP 重复发送 Response 的次数。此值应大于 0，建议小于 10。类似于 tcp_syn_retries。

retries1  
DCCP 响应被重传的次数，直到监听的 DCCP 端认为其连接的对端已失效。类似于 tcp_retries1。

retries2  
一般 DCCP 数据包被重传的次数。这对于重传确认和特性协商很重要，数据包从不重传。类似于 tcp_retries2。

tx_ccid = 2  
发送者-接收者半连接的默认 CCID。根据所选的 CCID，自动启用 Send Ack Vector 特性。

rx_ccid = 2  
接收者-发送者半连接的默认 CCID；参见 tx_ccid。

seq_window = 100  
发送者的初始序列窗口（第 7.5.2 节）。这影响本地 ackno 有效性和远程 seqno 有效性窗口（第 7.5.1 节）。

可以设置的值范围是 Wmin = 32（RFC 4340, 第 7.5.2 节）到 2^32-1。
```txt
tx_qlen = 5
    发送缓冲区的大小，以数据包为单位。值为 0 表示发送缓冲区无界。

sync_ratelimit = 125 ms
    在响应同一套接字上的序列号无效的数据包时，发送后续 DCCP-Sync 数据包之间的超时时间（RFC 4340, 7.5.4）。此参数的单位是毫秒；值为 0 禁用速率限制。

IOCTLS
======
FIONREAD
    与 udp(7) 中的工作方式相同：返回下一个待处理数据报的大小（以字节为单位），或者当没有数据报待处理时返回 0。

SIOCOUTQ
    返回套接字发送队列中未发送的数据字节数，并将其作为 `int` 类型存储在由参数指针指定的缓冲区中。

其他可调参数
==============
每路由 RTO 最小值支持
    CCID-2 支持 RTAX_RTO_MIN 每路由设置，用于定义 RTO 定时器的最小值。此设置可以通过 iproute2 的 `rto_min` 选项进行修改；例如：

    > ip route change 10.0.0.0/24 rto_min 250j dev wlan0
    > ip route add 10.0.0.254/32 rto_min 800j dev wlan0
    > ip route show dev wlan0

    CCID-3 同样支持 rto_min 设置：它用于定义 nofeedback 定时器过期的下限。这在具有非常低 RTT 的局域网（如环回、千兆以太网）上很有用。

注意事项
=====
目前 DCCP 在许多设备上无法成功穿越 NAT。这是因为校验和覆盖了伪头部，就像 TCP 和 UDP 那样。Linux 已经添加了对 DCCP 的 NAT 支持。
```
