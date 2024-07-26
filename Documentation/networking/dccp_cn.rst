### SPDX 许可证标识符: GPL-2.0

=============
DCCP 协议
=============

.. 目录
   - 引言
   - 缺失的功能
   - 套接字选项
   - Sysctl 变量
   - IOCTLs
   - 其他可调参数
   - 注意事项

引言
============

数据报拥塞控制协议（DCCP）是一种不可靠的、面向连接的协议，旨在解决在UDP和TCP中存在的问题，特别是针对实时和多媒体（流式传输）流量。它分为基础协议（RFC 4340）和可插拔的拥塞控制模块，这些模块被称为CCID（Congestion Control ID）。类似于可插拔的TCP拥塞控制，至少需要启用一个CCID才能使该协议正常工作。在Linux实现中，这是类似于TCP的CCID2（RFC 4341）。额外的CCID，例如与TCP兼容的CCID3（RFC 4342），是可选的。
对于简要介绍CCID以及为给定的应用程序选择合适的CCID的建议，请参阅RFC 4340第10节。
它具有基础协议和可插拔的拥塞控制ID（CCIDs）。
DCCP是一个提议的标准（RFC 2026），作为协议的DCCP主页位于http://www.ietf.org/html.charters/dccp-charter.html。

缺失的功能
================
当前Linux的DCCP实现并不支持所有在RFCs 4340...42中规定的所有功能。
已知的问题可以在以下链接找到：

	http://www.linuxfoundation.org/collaborate/workgroups/networking/todo#DCCP

为了使用更最新版本的DCCP实现，请考虑使用实验性的DCCP测试树；如何获取它的说明位于：
http://www.linuxfoundation.org/collaborate/workgroups/networking/dccp_testing#Experimental_DCCP_source_tree

套接字选项
==============
`DCCP_SOCKOPT_QPOLICY_ID` 设置出站数据包的排队策略。它接受一个策略ID作为参数，并且只能在建立连接之前设置（即，在已建立的连接期间更改不被支持）。目前定义了两种策略：一种是“简单”策略（DCCPQ_POLICY_SIMPLE），它不做任何特殊处理，另一种是基于优先级的变体（DCCPQ_POLICY_PRIO）。后者允许通过sendmsg()传递一个u32优先级值作为辅助数据，其中较高的数字表示更高的数据包优先级（类似于SO_PRIORITY）。此辅助数据需要按照如下格式使用cmsg(3)消息头填充：

```
cmsg->cmsg_level = SOL_DCCP;
cmsg->cmsg_type  = DCCP_SCM_PRIORITY;
cmsg->cmsg_len   = CMSG_LEN(sizeof(uint32_t));  /* 或 CMSG_LEN(4) */
```

`DCCP_SOCKOPT_QPOLICY_TXQLEN` 设置输出队列的最大长度。零值始终解释为无界队列长度。如果不同于零，则此参数的解释取决于当前的排队策略（见上文）：“简单”策略将通过返回EAGAIN来强制固定队列大小，而“prio”策略则通过首先丢弃最低优先级的数据包来强制固定队列长度。此参数的默认值从/proc/sys/net/dccp/default/tx_qlen初始化。
`DCCP_SOCKOPT_SERVICE` 设置服务。规范要求使用服务代码（RFC 4340，第8.1.2节）；如果未设置此套接字选项，则套接字将回退到0（这意味着没有有意义的服务代码存在）。在主动套接字上，这是在connect()之前设置的；指定多个代码没有效果（所有后续服务代码都将被忽略）。对于被动套接字来说情况不同，可以在调用bind()之前设置多达32个服务代码。
`DCCP_SOCKOPT_GET_CUR_MPS` 是只读的，用于检索当前最大数据包大小（应用程序负载大小）以字节为单位，参见RFC 4340第14节。
`DCCP_SOCKOPT_AVAILABLE_CCIDS` 也是只读的，并返回端点支持的CCID列表。选项值是一个uint8_t类型的数组，其大小作为选项长度传递。数组的最小大小是4个元素，optlen参数返回的值始终反映实际构建的CCID数量。
`DCCP_SOCKOPT_CCID` 是写入专用的，并同时设置TX和RX CCIDs，结合了后面两个套接字选项的操作。此选项优于后两者，因为通常应用程序会在两个方向上使用相同类型的CCID；而混合使用CCID目前还不太清楚。此套接字选项接受至少一个uint8_t值或uint8_t值的数组作为参数，这些值必须匹配可用的CCID（见上文）。CCID必须在调用connect()或listen()之前在套接字上注册。
DCCP_SOCKOPT_TX_CCID 是可读写的。它返回当前的 CCID（如果已设置）或设置 TX CCID 的优先级列表，使用与 DCCP_SOCKOPT_CCID 相同的格式。
请注意，这里的 getsockopt 参数类型是 `int`，而不是 uint8_t。
DCCP_SOCKOPT_RX_CCID 与 DCCP_SOCKOPT_TX_CCID 类似，但针对的是 RX CCID。
DCCP_SOCKOPT_SERVER_TIMEWAIT 允许服务器（监听套接字）在关闭连接时保持 TIMEWAIT 状态（RFC 4340, 8.3）。通常情况下，关闭的服务器发送 CloseReq，此时客户端将进入 TIMEWAIT 状态。当此布尔类型的套接字选项被启用时，服务器将发送 Close 并进入 TIMEWAIT 状态。此选项必须在 accept() 返回后设置。
DCCP_SOCKOPT_SEND_CSCOV 和 DCCP_SOCKOPT_RECV_CSCOV 用于设置部分校验和覆盖范围（RFC 4340, 第 9.2 节）。默认情况下，校验和总是覆盖整个数据包，并且接收方只接受完全覆盖的应用数据。因此，在发送端使用此功能时，接收端也必须启用该功能，并选择合适的 CsCov 值。
DCCP_SOCKOPT_SEND_CSCOV 设置发送端的校验和覆盖范围。0 到 15 之间的值都是可以接受的。默认设置为 0（完全覆盖），1 到 15 之间的值表示部分覆盖。
DCCP_SOCKOPT_RECV_CSCOV 是为接收端设置的，含义不同：它设置一个阈值，同样地，0 到 15 之间的值都是可以接受的。默认的 0 表示所有部分覆盖的数据包都将被丢弃。
1 到 15 之间的值表示至少具有这样的覆盖值的数据包也是可以接受的。数值越大，限制越严格（参见 [RFC 4340, 第 9.2.1 节]）。部分覆盖设置在接受后会继承给子套接字。
以下两个选项仅适用于 CCID 3，并且仅可通过 getsockopt() 获取。
在这两种情况下，都会返回一个 TFRC 信息结构（定义在 <linux/tfrc.h> 中）。
DCCP_SOCKOPT_CCID_RX_INFO  
返回一个 `struct tfrc_rx_info` 结构体在 optval 中；optval 和 optlen 的缓冲区必须至少设置为 sizeof(struct tfrc_rx_info) 大小。

DCCP_SOCKOPT_CCID_TX_INFO  
返回一个 `struct tfrc_tx_info` 结构体在 optval 中；optval 和 optlen 的缓冲区必须至少设置为 sizeof(struct tfrc_tx_info) 大小。

对于单向连接，通过调用 shutdown（SHUT_WR 或 SHUT_RD）关闭未使用的半连接是有益的：这将减少每个数据包处理的成本。

sysctl 变量
================
以下 sysctls （sysctl net.dccp.default 或 /proc/sys/net/dccp/default）可以管理多个 DCCP 默认参数：

request_retries  
主动连接初始化重试次数（请求次数减一）之前的时间超时。此外，它还控制另一端被动方的行为：此变量还设置了 DCCP 在初始握手未从 RESPOND 进展到 OPEN 状态（即在初始请求后未收到 Ack）时重复发送响应的次数。此值应大于 0，建议小于 10。类似于 tcp_syn_retries。

retries1  
DCCP 响应被重新传输的次数，直到监听的 DCCP 方认为其连接对等方已失效。类似于 tcp_retries1。

retries2  
一般 DCCP 数据包被重新传输的次数。这对于重传确认和特性协商很重要，数据包不会被重传。类似于 tcp_retries2。

tx_ccid = 2  
发送端-接收端半连接的默认 CCID。根据选择的 CCID，自动启用发送确认向量功能。

rx_ccid = 2  
接收端-发送端半连接的默认 CCID；参见 tx_ccid。

seq_window = 100  
发送方的初始序列窗口（第 7.5.2 节）。这影响本地 ackno 有效性和远程 seqno 有效性的窗口（第 7.5.1 节）。

可以设置的值范围为 Wmin = 32（RFC 4340, 第 7.5.2 节）至 2^32-1。
tx_qlen = 5  
发送缓冲区的大小，以数据包计数。值为0表示发送缓冲区无界。

sync_ratelimit = 125 毫秒  
在响应同一套接字上的序列号无效的数据包时，连续发送的 DCCP-Sync 数据包之间的超时时间（RFC 4340, 7.5.4）。此参数的单位是毫秒；值为0将禁用速率限制。

IOCTLS
======
FIONREAD  
与 udp(7) 中的工作方式相同：通过指针返回下一个待处理数据报的大小（以字节为单位），如果没有待处理的数据报则返回 0。

SIOCOUTQ  
返回套接字发送队列中未发送的数据字节数，并将其作为 `int` 类型存储到由参数指针指定的缓冲区中。

其他可调参数
==============
每路由 rto_min 支持  
CCID-2 支持 RTAX_RTO_MIN 的每路由设置，用于设定 RTO 定时器的最小值。可以通过 iproute2 的 'rto_min' 选项来修改此设置；例如：

```
> ip route change 10.0.0.0/24   rto_min 250j dev wlan0
> ip route add    10.0.0.254/32 rto_min 800j dev wlan0
> ip route show dev wlan0
```

CCID-3 同样支持 rto_min 设置：它用于定义 nofeedback 定时器过期的下限。对于具有非常低的 RTT 的局域网（例如，回环、千兆以太网）来说，这可能是有用的。

注释
=====
目前 DCCP 在许多设备上无法成功穿越 NAT。这是因为校验和覆盖了与 TCP 和 UDP 相同的伪头部。Linux 已经增加了对 DCCP 的 NAT 支持。
