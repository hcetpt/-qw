SPDX 许可证标识符: GPL-2.0

========================================
裸UDP隧道模块文档
========================================

目前有多种使用UDP的L3封装标准正在讨论中，以利用不同网络中的基于UDP的负载均衡能力。MPLSoUDP（__ https://tools.ietf.org/html/rfc7510）是其中之一。裸UDP隧道模块提供了一种通用的L3封装支持，可以在UDP隧道内传输不同的L3协议，如MPLS、IP、NSH等。

特殊处理
----------------
裸UDP设备对MPLS和IP提供了特殊处理，因为它们可以有多个ethertype。
MPLS协议可以有ethertype ETH_P_MPLS_UC（单播）和ETH_P_MPLS_MC（多播）。
IP协议可以有ethertype ETH_P_IP（IPv4）和ETH_P_IPV6（IPv6）。
这种特殊处理只能通过一个名为“多协议模式”的标志来启用，适用于ethertype ETH_P_IP 和 ETH_P_MPLS_UC。

使用方法
--------

1) 设备创建与删除

    a) ip link add dev bareudp0 type bareudp dstport 6635 ethertype mpls_uc

       这将创建一个裸UDP隧道设备，该设备以ethertype 0x8847（MPLS流量）封装L3流量。UDP头部的目标端口将设置为6635。该设备将在UDP端口6635上监听接收流量。
    
    b) ip link delete bareudp0

2) 启用多协议模式下的设备创建

多协议模式允许裸UDP隧道处理同一族内的多种协议。目前仅对IP和MPLS可用。此模式需要显式地使用“multiproto”标志来启用。
    
    a) ip link add dev bareudp0 type bareudp dstport 6635 ethertype ipv4 multiproto

       对于IPv4隧道，多协议模式允许该隧道也处理IPv6流量。
b) ip link add dev bareudp0 type bareudp dstport 6635 ethertype mpls_uc multiproto

对于MPLS，multiproto模式允许隧道处理单播和组播的MPLS数据包。

3) 设备使用

bareudp设备可以与OVS或TC的flower过滤器一起使用。
在发送数据包缓冲区到bareudp设备进行传输之前，OVS或TC flower层必须在SKB dst字段中设置隧道信息。在接收时，bareudp设备会提取并存储SKB dst字段中的隧道信息，然后再将数据包缓冲区传递给网络堆栈。
