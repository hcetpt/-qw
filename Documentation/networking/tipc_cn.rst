SPDX 许可证标识符: GPL-2.0

=================
Linux 内核 TIPC
=================

介绍
============

TIPC（透明进程间通信）是一个特别为集群内通信设计的协议。它可以配置为通过 UDP 或直接跨以太网传输消息。消息传递是顺序保证、无损且具有流量控制的。其延迟时间比任何已知的其他协议都要短，而最大吞吐量与 TCP 相当。
TIPC 特性
-------------

- 集群范围内的进程间通信服务

  您是否曾经希望在集群节点之间传输数据时也能享受到类似于 Unix 域套接字的便利？在那里您可以自己决定要绑定和使用的地址？不需要进行 DNS 查找也不必担心 IP 地址？无需启动计时器来监控对等套接字的持续存在？同时又避免了该类型套接字的缺点，例如可能存在持久inode的问题？

  欢迎使用透明进程间通信服务（简称 TIPC），它能为您提供所有这些功能，以及更多。
- 服务寻址

  在 TIPC 中有一个核心概念叫做服务寻址，它使得程序员可以选择自己的地址，将其绑定到服务器套接字上，并让客户端程序仅使用该地址发送消息。
- 服务跟踪

  如果一个客户端想要等待服务器的可用性，可以使用服务跟踪机制来订阅绑定和解绑/关闭事件，这些事件针对与服务地址关联的套接字。

  服务跟踪机制也可以用于集群拓扑跟踪，即订阅集群节点的可用性和不可用性事件。

  同样，服务跟踪机制可用于集群连通性跟踪，即订阅集群节点间单个链路的上下线事件。
- 传输模式

  使用服务地址，客户端可以向服务器套接字发送数据报消息。

  使用相同类型的地址，它可以与接收方服务器套接字建立连接。

  它还可以使用服务地址创建并加入一个通信组，这是 TIPC 中的一种无代理消息总线表现形式。

  在数据报模式和通信组模式下均支持高性能和可扩展性的组播。
节点间链接

集群中任意两个节点间的通信由一个或两个节点间链接维持，这些链接既能保证数据流量的完整性，也能监控对等节点的可用性。

集群可扩展性

通过在节点间链接上应用重叠环监测算法，可以将TIPC集群扩展到1000个节点，同时保持邻居故障发现时间在1到2秒之间。对于较小的集群，这一时间可以大幅度缩短。

邻居发现

集群中的邻居节点发现可以通过以太网广播或UDP多播完成，如果这些服务可用的话。如果不具备这些服务，则可以使用配置好的对等IP地址。

配置

当TIPC运行在单节点模式下时，不需要任何配置。当运行在集群模式下时，TIPC至少需要被赋予一个节点地址（在Linux 4.17之前）并告知要连接到哪个接口。“tipc”配置工具使得添加和维护更多的配置参数成为可能。

性能

TIPC消息传输延迟时间优于任何已知协议。节点间连接的最大字节吞吐量略低于TCP，但在同一主机上的节点内和容器间传输方面则更为优越。

语言支持

TIPC用户API支持C、Python、Perl、Ruby、D和Go语言。

更多信息
---------

- 如何设置TIPC：
  
  http://tipc.io/getting_started.html

- 如何使用TIPC编程：

  http://tipc.io/programming.html

- 如何为TIPC做出贡献：

  http://tipc.io/contacts.html

- 更多关于TIPC规范的细节：

  http://tipc.io/protocol.html

实现
====

TIPC作为net/tipc/目录下的内核模块实现。
TIPC基础类型
-------------

.. kernel-doc:: net/tipc/subscr.h
   :internal:

.. kernel-doc:: net/tipc/bearer.h
   :internal:

.. kernel-doc:: net/tipc/name_table.h
   :internal:

.. kernel-doc:: net/tipc/name_distr.h
   :internal:

.. kernel-doc:: net/tipc/bcast.c
   :internal:

TIPC承载接口
-------------

.. kernel-doc:: net/tipc/bearer.c
   :internal:

.. kernel-doc:: net/tipc/udp_media.c
   :internal:

TIPC加密接口
-------------

.. kernel-doc:: net/tipc/crypto.c
   :internal:

TIPC发现接口
-------------

.. kernel-doc:: net/tipc/discover.c
   :internal:

TIPC链接接口
-------------

.. kernel-doc:: net/tipc/link.c
   :internal:

TIPC消息接口
-------------

.. kernel-doc:: net/tipc/msg.c
   :internal:

TIPC名称接口
-------------

.. kernel-doc:: net/tipc/name_table.c
   :internal:

.. kernel-doc:: net/tipc/name_distr.c
   :internal:

TIPC节点管理接口
-----------------

.. kernel-doc:: net/tipc/node.c
   :internal:

TIPC套接字接口
--------------

.. kernel-doc:: net/tipc/socket.c
   :internal:

TIPC网络拓扑接口
-----------------

.. kernel-doc:: net/tipc/subscr.c
   :internal:

TIPC服务器接口
--------------

.. kernel-doc:: net/tipc/topsrv.c
   :internal:

TIPC追踪接口
-------------

.. kernel-doc:: net/tipc/trace.c
   :internal:
