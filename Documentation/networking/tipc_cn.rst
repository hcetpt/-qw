SPDX 许可证标识符: GPL-2.0

=================
Linux 内核 TIPC
=================

介绍
============

TIPC（透明进程间通信）是一种专门为集群内通信设计的协议。它可以配置为通过 UDP 或直接通过以太网传输消息。消息传递是顺序保证、无损且受流量控制的。延迟时间比任何其他已知协议都要短，而最大吞吐量与 TCP 相当。

TIPC 特性
-------------

- 集群范围内的进程间通信服务

  您是否曾经希望在集群节点之间传输数据时也能享受 Unix 域套接字的便利？在这里，您可以自己确定要绑定和使用的地址？无需执行 DNS 查找，也不必担心 IP 地址？无需启动计时器来监控对等套接字的持续存在？同时又没有这种套接字类型的缺点，例如滞留inode的风险？

  欢迎使用透明进程间通信服务（简称 TIPC），它为您提供这一切，以及更多功能。
- 服务寻址

  TIPC 的一个基本概念是服务寻址，这使得程序员可以选择自己的地址，将其绑定到服务器套接字，并让客户端程序仅使用该地址发送消息。
- 服务跟踪

  客户端如果想要等待服务器可用，可以使用服务跟踪机制订阅具有关联服务地址的套接字的绑定和解绑/关闭事件。
  服务跟踪机制也可以用于集群拓扑跟踪，即订阅集群节点的可用/不可用事件。
  同样，服务跟踪机制也可用于集群连接跟踪，即订阅集群节点之间单个链路的上下事件。
- 传输模式

  使用服务地址，客户端可以向服务器套接字发送数据报消息。
  使用相同地址类型，它可以建立到接受服务器套接字的连接。
  它还可以使用服务地址创建并加入一个通信组，这是 TIPC 中无代理消息总线的表现形式。
  在数据报模式和通信组模式下都提供了高性能和高可扩展性的组播。
### 节点间链接 (Inter Node Links)

集群中任意两个节点之间的通信由一条或两条节点间链接维护，这些链接既保证数据流量的完整性，也监控对等节点的可用性。

### 集群可扩展性 (Cluster Scalability)

通过在节点间链接上应用重叠环监测算法，可以将TIPC集群扩展到最多1000个节点，并保持邻居故障发现时间为1-2秒。对于较小的集群，这个时间可以缩短很多。

### 邻居发现 (Neighbor Discovery)

集群中的邻居节点发现是通过以太网广播或UDP组播完成的，如果这些服务可用的话。如果不具备这些服务，则可以使用配置好的对等IP地址。

### 配置 (Configuration)

当单节点模式下运行TIPC时，不需要任何配置。在集群模式下，TIPC至少需要一个节点地址（在Linux 4.17之前）并指定要连接的接口。“tipc”配置工具使得添加和维护更多配置参数成为可能。

### 性能 (Performance)

TIPC消息传输延迟时间优于其他已知协议。对于节点间连接的最大字节吞吐量仍略低于TCP，但对于同一主机上的节点内和容器间的吞吐量则更优。

### 语言支持 (Language Support)

TIPC用户API支持C、Python、Perl、Ruby、D和Go。

### 更多信息 (More Information)

- 如何设置TIPC：
  http://tipc.io/getting_started.html

- 如何使用TIPC编程：
  http://tipc.io/programming.html

- 如何为TIPC做出贡献：
  http://tipc.io/contacts.html

- 更多关于TIPC规范的详细信息：
  http://tipc.io/protocol.html

### 实现 (Implementation)

TIPC作为一个内核模块实现，位于`net/tipc/`目录中。

### TIPC基础类型 (TIPC Base Types)

- .. kernel-doc:: net/tipc/subscr.h
   :internal:

- .. kernel-doc:: net/tipc/bearer.h
   :internal:

- .. kernel-doc:: net/tipc/name_table.h
   :internal:

- .. kernel-doc:: net/tipc/name_distr.h
   :internal:

- .. kernel-doc:: net/tipc/bcast.c
   :internal:

### TIPC承载接口 (TIPC Bearer Interfaces)

- .. kernel-doc:: net/tipc/bearer.c
   :internal:

- .. kernel-doc:: net/tipc/udp_media.c
   :internal:

### TIPC加密接口 (TIPC Crypto Interfaces)

- .. kernel-doc:: net/tipc/crypto.c
   :internal:

### TIPC发现接口 (TIPC Discoverer Interfaces)

- .. kernel-doc:: net/tipc/discover.c
   :internal:

### TIPC链路接口 (TIPC Link Interfaces)

- .. kernel-doc:: net/tipc/link.c
   :internal:

### TIPC消息接口 (TIPC msg Interfaces)

- .. kernel-doc:: net/tipc/msg.c
   :internal:

### TIPC名称接口 (TIPC Name Interfaces)

- .. kernel-doc:: net/tipc/name_table.c
   :internal:

- .. kernel-doc:: net/tipc/name_distr.c
   :internal:

### TIPC节点管理接口 (TIPC Node Management Interfaces)

- .. kernel-doc:: net/tipc/node.c
   :internal:

### TIPC套接字接口 (TIPC Socket Interfaces)

- .. kernel-doc:: net/tipc/socket.c
   :internal:

### TIPC网络拓扑接口 (TIPC Network Topology Interfaces)

- .. kernel-doc:: net/tipc/subscr.c
   :internal:

### TIPC服务器接口 (TIPC Server Interfaces)

- .. kernel-doc:: net/tipc/topsrv.c
   :internal:

### TIPC跟踪接口 (TIPC Trace Interfaces)

- .. kernel-doc:: net/tipc/trace.c
   :internal:
