SPDX 许可证标识符: GPL-2.0

========================================
裸UDP隧道模块文档
========================================

目前正讨论各种使用UDP的L3封装标准，以利用不同网络中基于UDP的负载均衡能力。
MPLSoUDP (__ https://tools.ietf.org/html/rfc7510) 就是其中之一。
裸UDP隧道模块为在UDP隧道内传输不同的L3协议（如MPLS、IP、NSH等）提供了一般的L3封装支持。
特殊处理
----------------
裸UDP设备对MPLS和IP提供了特殊处理，因为它们可以有多种以太类型。
MPLS协议可以有以太类型ETH_P_MPLS_UC（单播）和ETH_P_MPLS_MC（多播）。
IP协议可以有以太类型ETH_P_IP（IPv4）和ETH_P_IPV6（IPv6）。
这种特殊处理只能通过一个名为“多协议模式”的标志来为以太类型ETH_P_IP和ETH_P_MPLS_UC启用。
使用方法
------

1) 设备创建与删除

    a) ip link add dev bareudp0 type bareudp dstport 6635 ethertype mpls_uc

       这将创建一个裸UDP隧道设备，用于传输以太类型为0x8847（MPLS流量）的L3流量。UDP头的目的端口将设置为6635。该设备将在UDP端口6635上监听以接收流量。
b) ip link delete bareudp0

2) 启用多协议模式的设备创建

多协议模式允许裸UDP隧道处理同一族中的多种协议。目前仅适用于IP和MPLS。此模式必须明确使用“multiproto”标志启用。
a) ip link add dev bareudp0 type bareudp dstport 6635 ethertype ipv4 multiproto

       对于IPv4隧道，多协议模式允许隧道也能处理IPv6。
b) 添加名为 bareudp0 的 bareudp 设备类型，端口为 6635，以太网类型为 mpls_uc，并启用 multiproto 模式。

对于 MPLS，multiproto 模式允许隧道同时处理单播和组播的 MPLS 数据包。
3) 设备使用方法

bareudp 设备可以与 OVS 或 TC 中的花键过滤器配合使用。
在将数据包缓冲区发送给 bareudp 设备进行传输之前，OVS 或 TC 花键层必须在 SKB 的 dst 字段中设置隧道信息。接收时，
bareudp 设备会在将数据包缓冲区传递给网络堆栈之前提取并存储隧道信息到 SKB 的 dst 字段中。
