SNMP 计数器
===========

本文档解释了 SNMP 计数器的含义。
通用 IPv4 计数器
=================
所有第 4 层数据包和 ICMP 数据包都会改变这些计数器，但第 2 层数据包（如 STP）或 ARP 数据包不会改变这些计数器。
* IpInReceives

定义在 `RFC1213 ipInReceives`_

.. _RFC1213 ipInReceives: https://tools.ietf.org/html/rfc1213#page-26

IP 层接收到的数据包数量。在 ip_rcv 函数开始时递增，并始终与 IpExtInOctets 一起更新。即使数据包后来被丢弃（例如由于 IP 头无效或校验和错误等），也会增加。它表示 GRO/LRO 后聚合的段数。
* IpInDelivers

定义在 `RFC1213 ipInDelivers`_

.. _RFC1213 ipInDelivers: https://tools.ietf.org/html/rfc1213#page-28

传递给上层协议的数据包数量。例如 TCP、UDP、ICMP 等。如果没有监听原始套接字，则仅传递内核支持的协议；如果有监听原始套接字，则传递所有有效的 IP 数据包。
* IpOutRequests

定义在 `RFC1213 ipOutRequests`_

.. _RFC1213 ipOutRequests: https://tools.ietf.org/html/rfc1213#page-28

通过 IP 层发送的数据包数量，包括单播和组播数据包，并始终与 IpExtOutOctets 一起更新。
* IpExtInOctets 和 IpExtOutOctets

它们是 Linux 内核扩展，没有 RFC 定义。请注意，RFC1213 确实定义了 ifInOctets 和 ifOutOctets，但它们是不同的东西。ifInOctets 和 ifOutOctets 包括 MAC 层头大小，而 IpExtInOctets 和 IpExtOutOctets 只包含 IP 层头和 IP 层数据。
* IpExtInNoECTPkts, IpExtInECT1Pkts, IpExtInECT0Pkts, IpExtInCEPkts

它们表示四种不同类型的 ECN IP 数据包的数量，请参阅 `Explicit Congestion Notification`_ 获取更多详细信息。
.. _Explicit Congestion Notification: https://tools.ietf.org/html/rfc3168#page-6

这四个计数器计算每种 ECN 状态接收的数据包数量。它们根据实际帧数进行计数，而不考虑 LRO/GRO。因此，对于同一个数据包，您可能会发现 IpInReceives 计数为 1，但 IpExtInNoECTPkts 计数为 2 或更多。
* IpInHdrErrors

定义在 `RFC1213 ipInHdrErrors`_。表示由于 IP 头错误而导致数据包被丢弃。这种情况可能发生在 IP 输入路径和 IP 转发路径中。
.. _RFC1213 ipInHdrErrors: https://tools.ietf.org/html/rfc1213#page-27

* IpInAddrErrors

定义在 `RFC1213 ipInAddrErrors`_。在两种情况下会增加：(1) IP 地址无效；(2) 目标 IP 地址不是本地地址且未启用 IP 转发。

.. _RFC1213 ipInAddrErrors: https://tools.ietf.org/html/rfc1213#page-27

* IpExtInNoRoutes

此计数器表示当 IP 栈接收到一个数据包并无法从路由表中找到其路由时，数据包被丢弃。这可能发生在启用了 IP 转发并且目标 IP 地址不是本地地址且没有到达目标 IP 地址的路由时。
* IpInUnknownProtos

定义于 `RFC1213 ipInUnknownProtos`_。如果第四层协议不被内核支持，该计数器将会增加。如果应用程序使用原始套接字，则内核始终会将数据包传递给原始套接字，并且此计数器不会增加。
.. _RFC1213 ipInUnknownProtos: https://tools.ietf.org/html/rfc1213#page-27

* IpExtInTruncatedPkts

对于IPv4数据包而言，这意味着实际数据大小小于IPv4报头中的“总长度”字段。
* IpInDiscards

定义于 `RFC1213 ipInDiscards`_。它表示由于内核内部原因（例如内存不足）在IP接收路径中丢弃了数据包。
.. _RFC1213 ipInDiscards: https://tools.ietf.org/html/rfc1213#page-28

* IpOutDiscards

定义于 `RFC1213 ipOutDiscards`_。它表示由于内核内部原因，在IP发送路径中丢弃了数据包。
.. _RFC1213 ipOutDiscards: https://tools.ietf.org/html/rfc1213#page-28

* IpOutNoRoutes

定义于 `RFC1213 ipOutNoRoutes`_。它表示由于找不到路由，在IP发送路径中丢弃了数据包。
.. _RFC1213 ipOutNoRoutes: https://tools.ietf.org/html/rfc1213#page-29

ICMP计数器
==========
* IcmpInMsgs 和 IcmpOutMsgs

由 `RFC1213 icmpInMsgs`_ 和 `RFC1213 icmpOutMsgs`_ 定义。

.. _RFC1213 icmpInMsgs: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpOutMsgs: https://tools.ietf.org/html/rfc1213#page-43

如RFC1213所述，这两个计数器包括错误，即使ICMP数据包类型无效，它们也会增加。ICMP输出路径会检查原始套接字的头部，因此即使IP头部是由用户空间程序构造的，IcmpOutMsgs仍然会被更新。
* ICMP命名类型

| 这些计数器包含大多数常见的ICMP类型，具体如下：
| IcmpInDestUnreachs: `RFC1213 icmpInDestUnreachs`_
| IcmpInTimeExcds: `RFC1213 icmpInTimeExcds`_
| IcmpInParmProbs: `RFC1213 icmpInParmProbs`_
| IcmpInSrcQuenchs: `RFC1213 icmpInSrcQuenchs`_
| IcmpInRedirects: `RFC1213 icmpInRedirects`_
| IcmpInEchos: `RFC1213 icmpInEchos`_
| IcmpInEchoReps: `RFC1213 icmpInEchoReps`_
| IcmpInTimestamps: `RFC1213 icmpInTimestamps`_
| IcmpInTimestampReps: `RFC1213 icmpInTimestampReps`_
| IcmpInAddrMasks: `RFC1213 icmpInAddrMasks`_
| IcmpInAddrMaskReps: `RFC1213 icmpInAddrMaskReps`_
| IcmpOutDestUnreachs: `RFC1213 icmpOutDestUnreachs`_
| IcmpOutTimeExcds: `RFC1213 icmpOutTimeExcds`_
| IcmpOutParmProbs: `RFC1213 icmpOutParmProbs`_
| IcmpOutSrcQuenchs: `RFC1213 icmpOutSrcQuenchs`_
| IcmpOutRedirects: `RFC1213 icmpOutRedirects`_
| IcmpOutEchos: `RFC1213 icmpOutEchos`_
| IcmpOutEchoReps: `RFC1213 icmpOutEchoReps`_
| IcmpOutTimestamps: `RFC1213 icmpOutTimestamps`_
| IcmpOutTimestampReps: `RFC1213 icmpOutTimestampReps`_
| IcmpOutAddrMasks: `RFC1213 icmpOutAddrMasks`_
| IcmpOutAddrMaskReps: `RFC1213 icmpOutAddrMaskReps`_

.. _RFC1213 icmpInDestUnreachs: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpInTimeExcds: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpInParmProbs: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInSrcQuenchs: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInRedirects: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInEchos: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInEchoReps: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInTimestamps: https://tools.ietf.org/html/rfc1213#page-42
.. _RFC1213 icmpInTimestampReps: https://tools.ietf.org/html/rfc1213#page-43
.. _RFC1213 icmpInAddrMasks: https://tools.ietf.org/html/rfc1213#page-43
.. _RFC1213 icmpInAddrMaskReps: https://tools.ietf.org/html/rfc1213#page-43

.. _RFC1213 icmpOutDestUnreachs: https://tools.ietf.org/html/rfc1213#page-44
.. _RFC1213 icmpOutTimeExcds: https://tools.ietf.org/html/rfc1213#page-44
.. _RFC1213 icmpOutParmProbs: https://tools.ietf.org/html/rfc1213#page-44
.. _RFC1213 icmpOutSrcQuenchs: https://tools.ietf.org/html/rfc1213#page-44
.. _RFC1213 icmpOutRedirects: https://tools.ietf.org/html/rfc1213#page-44
.. _RFC1213 icmpOutEchos: https://tools.ietf.org/html/rfc1213#page-45
.. _RFC1213 icmpOutEchoReps: https://tools.ietf.org/html/rfc1213#page-45
.. _RFC1213 icmpOutTimestamps: https://tools.ietf.org/html/rfc1213#page-45
.. _RFC1213 icmpOutTimestampReps: https://tools.ietf.org/html/rfc1213#page-45
.. _RFC1213 icmpOutAddrMasks: https://tools.ietf.org/html/rfc1213#page-45
.. _RFC1213 icmpOutAddrMaskReps: https://tools.ietf.org/html/rfc1213#page-46

每个ICMP类型都有两个计数器：“In”和“Out”。例如，对于ICMP回声数据包，它们是IcmpInEchos和IcmpOutEchos。其含义非常直接。“In”计数器表示内核接收到这样的数据包，“Out”计数器表示内核发送了这样的数据包。
* ICMP数字类型

它们是IcmpMsgInType[N]和IcmpMsgOutType[N]，[N]表示ICMP类型编号。这些计数器跟踪所有类型的ICMP数据包。ICMP类型编号定义可以在 `ICMP参数`_ 文档中找到。
.. _ICMP 参数: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml

例如，如果Linux内核发送了一个ICMP回声数据包，那么IcmpMsgOutType8将增加1。如果内核接收到一个ICMP回声应答数据包，那么IcmpMsgInType0将增加1。
* IcmpInCsumErrors

此计数器表示ICMP数据包的校验和错误。内核在更新IcmpInMsgs之后但在更新IcmpMsgInType[N]之前验证校验和。如果数据包的校验和错误，IcmpInMsgs会被更新，但任何IcmpMsgInType[N]都不会被更新。
* IcmpInErrors 和 IcmpOutErrors

由 `RFC1213 icmpInErrors`_ 和 `RFC1213 icmpOutErrors`_ 定义。

.. _RFC1213 icmpInErrors: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpOutErrors: https://tools.ietf.org/html/rfc1213#page-43

当ICMP包处理路径中发生错误时，这两个计数器会被更新。接收包路径使用 IcmpInErrors，发送包路径使用 IcmpOutErrors。当 IcmpInCsumErrors 增加时，IcmpInErrors 也会增加。

ICMP计数器的关系
-----------------
IcmpMsgOutType[N] 的总和始终等于 IcmpOutMsgs，因为它们同时被更新。IcmpMsgInType[N] 加上 IcmpInErrors 应该等于或大于 IcmpInMsgs。当内核接收到一个ICMP包时，内核遵循以下逻辑：

1. 增加 IcmpInMsgs
2. 如果有任何错误，更新 IcmpInErrors 并结束处理
3. 更新 IcmpMsgOutType[N]
4. 根据类型处理包，如果出现任何错误，更新 IcmpInErrors 并结束处理

因此，如果所有错误发生在步骤 (2)，则 IcmpInMsgs 应该等于 IcmpMsgOutType[N] 加上 IcmpInErrors 的总和。如果所有错误发生在步骤 (4)，则 IcmpInMsgs 应该等于 IcmpMsgOutType[N] 的总和。如果错误同时发生在步骤 (2) 和步骤 (4)，则 IcmpInMsgs 应该小于 IcmpMsgOutType[N] 加上 IcmpInErrors 的总和。

通用的TCP计数器
====================
* TcpInSegs

由 `RFC1213 tcpInSegs`_ 定义。

.. _RFC1213 tcpInSegs: https://tools.ietf.org/html/rfc1213#page-48

TCP层接收到的数据包数量。如RFC1213所述，它包括那些有错误的数据包，例如校验和错误、无效的TCP头部等。唯一不会包括的错误是：如果第二层的目标地址不是NIC的第二层地址。这种情况可能会在接收到组播或广播数据包时发生，或者NIC处于混杂模式。在这种情况下，数据包将被传递到TCP层，但在增加 TcpInSegs 之前，TCP层会丢弃这些数据包。TcpInSegs 计数器不关心 GRO。因此，如果两个数据包通过 GRO 合并为一个，TcpInSegs 计数器只会增加 1。

* TcpOutSegs

由 `RFC1213 tcpOutSegs`_ 定义。

.. _RFC1213 tcpOutSegs: https://tools.ietf.org/html/rfc1213#page-48

TCP层发送的数据包数量。如RFC1213所述，它不包括重传的数据包。但它包括 SYN、ACK 和 RST 数据包。与 TcpInSegs 不同，TcpOutSegs 关心 GSO，因此如果一个数据包通过 GSO 被拆分为两个，TcpOutSegs 将增加 2。

* TcpActiveOpens

由 `RFC1213 tcpActiveOpens`_ 定义。

.. _RFC1213 tcpActiveOpens: https://tools.ietf.org/html/rfc1213#page-47

这意味着TCP层发送了一个 SYN，并进入 SYN-SENT 状态。每次 TcpActiveOpens 增加 1，TcpOutSegs 应该总是增加 1。

* TcpPassiveOpens

由 `RFC1213 tcpPassiveOpens`_ 定义。

.. _RFC1213 tcpPassiveOpens: https://tools.ietf.org/html/rfc1213#page-47

这意味着TCP层接收到了一个 SYN，回复了 SYN+ACK，并进入了 SYN-RCVD 状态。

* TcpExtTCPRcvCoalesce

当数据包被TCP层接收但未被应用程序读取时，TCP层将尝试合并这些数据包。此计数器指示在此情况下合并了多少个数据包。如果启用了 GRO，则许多数据包将被 GRO 合并，这些数据包不会计入 TcpExtTCPRcvCoalesce。

* TcpExtTCPAutoCorking

在发送数据包时，TCP层将尝试将小数据包合并为一个较大的数据包。此计数器在每次数据包在此情况下被合并时增加 1。更多详细信息请参考 LWN 文章：
https://lwn.net/Articles/576263/

* TcpExtTCPOrigDataSent

此计数器由内核提交 f19c29e3e391 解释，我将解释内容附在下面::

  TCPOrigDataSent：带有原始数据（排除重传但包括数据在 SYN 中）的传出数据包数量。此计数器不同于 TcpOutSegs，因为 TcpOutSegs 还跟踪纯 ACK 数据包。TCPOrigDataSent 对于追踪TCP重传率更有用。

* TCPSynRetrans

此计数器由内核提交 f19c29e3e391 解释，我将解释内容附在下面::

  TCPSynRetrans：用于分解重传的 SYN 和 SYN/ACK 重传次数，例如，分解为 SYN、快速重传、超时重传等。

* TCPFastOpenActiveFail

此计数器由内核提交 f19c29e3e391 解释，我将解释内容附在下面::

  TCPFastOpenActiveFail：快速打开尝试（SYN/data）失败，因为远程端不接受它或尝试超时。
* TcpExtListenOverflows 和 TcpExtListenDrops

当内核接收到客户端的 SYN 包时，如果 TCP 接收队列已满，内核会丢弃该 SYN 包并将 TcpExtListenOverflows 的计数加 1。同时，内核还会将 TcpExtListenDrops 的计数加 1。当一个 TCP 套接字处于 LISTEN 状态且内核需要丢弃一个包时，内核总是会将 TcpExtListenDrops 的计数加 1。因此，增加 TcpExtListenOverflows 会使 TcpExtListenDrops 同时增加，但 TcpExtListenDrops 也可能在 TcpExtListenOverflows 没有增加的情况下增加，例如内存分配失败也会导致 TcpExtListenDrops 增加。
注意：上述解释基于 4.10 及以上版本的内核，在旧版内核中，当 TCP 接收队列已满时，TCP 栈的行为不同。在旧版内核中，TCP 栈不会丢弃 SYN 包，而是完成三次握手。由于接收队列已满，TCP 栈会将套接字保留在半开队列中。因为套接字在半开队列中，TCP 栈会在指数退避定时器上发送 SYN+ACK，当客户端回复 ACK 后，TCP 栈会检查接收队列是否仍然已满，如果没有满，则将套接字移动到接收队列；如果已满，则将其保留在半开队列中，当下次客户端回复 ACK 时，这个套接字将有机会再次尝试进入接收队列。

TCP 快速打开
=============

* TcpEstabResets

定义于 `RFC1213 tcpEstabResets`_
.. _RFC1213 tcpEstabResets: https://tools.ietf.org/html/rfc1213#page-48

* TcpAttemptFails

定义于 `RFC1213 tcpAttemptFails`_
.. _RFC1213 tcpAttemptFails: https://tools.ietf.org/html/rfc1213#page-48

* TcpOutRsts

定义于 `RFC1213 tcpOutRsts`_。RFC 中说此计数器表示“包含 RST 标志的已发送段”，但在 Linux 内核中，此计数器表示内核试图发送的段。发送过程可能会因某些错误（例如内存分配失败）而失败
.. _RFC1213 tcpOutRsts: https://tools.ietf.org/html/rfc1213#page-52

* TcpExtTCPSpuriousRtxHostQueues

当 TCP 栈想要重传一个包，并发现该包在网络中并未丢失，但还未发送时，TCP 栈会放弃重传并更新此计数器。这可能发生在包在一个 qdisc 或驱动程序队列中停留时间过长时

* TcpEstabResets

套接字在建立或 CloseWait 状态下接收到 RST 包

* TcpExtTCPKeepAlive

此计数器表示发送了多少个保活包。默认情况下不会启用保活功能。用户空间程序可以通过设置 SO_KEEPALIVE 套接字选项来启用它

* TcpExtTCPSpuriousRTOs

由 `F-RTO`_ 算法检测到的虚假重传超时
_F-RTO: https://tools.ietf.org/html/rfc5682

TCP快速路径
=============
当内核接收到一个TCP数据包时，它有两种处理方式：一种是快速路径，另一种是慢速路径。内核代码中的注释对此有很好的解释，我将其贴在下面：

  它被分为快速路径和慢速路径。快速路径在以下情况下会被禁用：
  - 发布了一个零窗口
  - 零窗口探测仅在慢速路径中正确处理
  - 接收到乱序的数据段
  - 预期有紧急数据
  - 没有足够的缓冲区空间
  - 收到意外的TCP标志/窗口值/头部长度（通过检查TCP头部与pred_flags来检测）
  - 数据在双向发送。快速路径只支持纯发送者或纯接收者（这意味着序列号或确认值必须保持不变）
  - 收到意外的TCP选项
除非满足上述任何条件之一，否则内核将尝试使用快速路径。如果数据包乱序，内核将在慢速路径中处理它们，这意味着性能可能不会很好。如果使用了“延迟确认”，内核也会进入慢速路径，因为使用“延迟确认”时，数据在双向发送。当不使用TCP窗口缩放选项时，内核会在连接进入已建立状态后立即尝试启用快速路径，但如果使用了TCP窗口缩放选项，内核最初会禁用快速路径，并在接收到数据包后尝试启用它。
* TcpExtTCPPureAcks 和 TcpExtTCPHPAcks

如果一个数据包设置了ACK标志且没有数据，则这是一个纯ACK数据包；如果内核在快速路径中处理它，TcpExtTCPHPAcks 将增加1；如果内核在慢速路径中处理它，TcpExtTCPPureAcks 将增加1。
* TcpExtTCPHPHits

如果一个TCP数据包包含数据（意味着不是纯ACK数据包），并且这个数据包在快速路径中处理，TcpExtTCPHPHits 将增加1。

TCP终止
=========
* TcpExtTCPAbortOnData

这意味着TCP层中有飞行中的数据，但需要关闭连接。因此TCP层向另一端发送RST，表明连接未能优雅地关闭。增加此计数器的一种简单方法是使用SO_LINGER选项。请参阅 `socket手册页`_ 的SO_LINGER部分：

.. _socket手册页: http://man7.org/linux/man-pages/man7/socket.7.html

默认情况下，当应用程序关闭一个连接时，close函数将立即返回，并且内核将异步尝试发送飞行中的数据。如果你使用SO_LINGER选项，设置l_onoff为1，并且l_linger为正数，close函数不会立即返回，而是等待飞行中的数据被另一端确认，最大等待时间为l_linger秒。如果设置l_onoff为1并将l_linger设置为0，当应用程序关闭连接时，内核将立即发送RST并增加TcpExtTCPAbortOnData计数器。
* TcpExtTCPAbortOnClose

此计数器表示当应用程序想要关闭TCP连接时，TCP层中有未读数据。在这种情况下，内核将向TCP连接的另一端发送RST。
* TcpExtTCPAbortOnMemory

当应用程序关闭TCP连接时，内核仍然需要跟踪该连接，使其完成TCP断开过程。例如，一个应用程序调用了socket的close方法，内核向连接的另一端发送FIN，然后应用程序与socket不再有任何关系，但内核需要保留该socket，该socket成为一个孤儿socket。内核等待另一端的回复，并最终进入TIME_WAIT状态。当内核没有足够的内存来保留孤儿socket时，内核将向另一端发送RST并删除socket，在这种情况下，内核将使TcpExtTCPAbortOnMemory增加1。两种情况会触发TcpExtTCPAbortOnMemory：

1. TCP协议使用的内存高于tcp_mem的第三个值。请参阅 `TCP手册页`_ 的tcp_mem部分：

.. _TCP手册页: http://man7.org/linux/man-pages/man7/tcp.7.html

2. 孤儿socket的数量高于net.ipv4.tcp_max_orphans。
* TcpExtTCPAbortOnTimeout

当任何TCP定时器到期时，此计数器将增加。在这种情况下，内核不会发送RST，只是放弃连接。
* TcpExtTCPAbortOnLinger

当一个TCP连接进入FIN_WAIT_2状态时，内核可以选择不等待对方的FIN包，而是发送RST并立即删除套接字。这并不是Linux内核TCP堆栈的默认行为。通过配置TCP_LINGER2套接字选项，可以让内核遵循这种行为。

* TcpExtTCPAbortFailed

如果满足`RFC2525 2.17节`_中的条件，内核TCP层将发送RST。如果在此过程中发生内部错误，TcpExtTCPAbortFailed计数器将增加。
.. _RFC2525 2.17节: https://tools.ietf.org/html/rfc2525#page-50

TCP混合慢启动
=====================

混合慢启动算法是对传统TCP拥塞窗口慢启动算法的增强。它使用两个信息来检测是否接近TCP路径的最大带宽。这两个信息是ACK列车长度和数据包延迟的增加。详细信息请参见`混合慢启动论文`_。当ACK列车长度或数据包延迟达到特定阈值时，拥塞控制算法将进入拥塞避免状态。截至v4.20版本，有两个拥塞控制算法使用了混合慢启动，分别是cubic（默认的拥塞控制算法）和cdg。有四个与混合慢启动算法相关的SNMP计数器。
.. _混合慢启动论文: https://pdfs.semanticscholar.org/25e9/ef3f03315782c7f1cbcd31b587857adae7d1.pdf

* TcpExtTCPHystartTrainDetect

检测到ACK列车长度阈值的次数。

* TcpExtTCPHystartTrainCwnd

由ACK列车长度检测到的CWND总和。将此值除以TcpExtTCPHystartTrainDetect即可得到由ACK列车长度检测到的平均CWND。

* TcpExtTCPHystartDelayDetect

检测到数据包延迟阈值的次数。

* TcpExtTCPHystartDelayCwnd

由数据包延迟检测到的CWND总和。将此值除以TcpExtTCPHystartDelayDetect即可得到由数据包延迟检测到的平均CWND。

TCP重传与拥塞控制
=========================================

TCP协议有两种重传机制：SACK和快速恢复。这两种机制是互斥的。当启用SACK时，内核TCP堆栈会使用SACK；否则，内核会使用快速恢复。SACK是一个TCP选项，在`RFC2018`_中定义；快速恢复在`RFC6582`_中定义，也称为Reno。
TCP拥塞控制是一个复杂的话题。为了理解相关SNMP计数器，我们需要了解拥塞控制状态机的状态。共有5个状态：Open、Disorder、CWR、Recovery和Loss。关于这些状态的详细信息，请参考文档第5页和第6页：
https://pdfs.semanticscholar.org/0e9c/968d09ab2e53e24c4dca5b2d67c7f7140f8e.pdf

.. _RFC2018: https://tools.ietf.org/html/rfc2018
.. _RFC6582: https://tools.ietf.org/html/rfc6582

* TcpExtTCPRenoRecovery 和 TcpExtTCPSackRecovery

当拥塞控制进入Recovery状态时，如果使用SACK，则TcpExtTCPSackRecovery增加1；如果不使用SACK，则TcpExtTCPRenoRecovery增加1。这两个计数器表示TCP堆栈开始重传丢失的数据包。

* TcpExtTCPSACKReneging

一个数据包被SACK确认，但接收方丢弃了这个数据包，因此发送方需要重新传输该数据包。在这种情况下，发送方将TcpExtTCPSACKReneging加1。接收方可以丢弃已被SACK确认的数据包，尽管这种情况并不常见，但TCP协议允许这样做。发送方并不真正知道接收方发生了什么，只是等到RTO过期后，假设该数据包已被接收方丢弃。

* TcpExtTCPRenoReorder

快速恢复算法检测到乱序数据包。只有在禁用SACK的情况下才会使用。快速恢复算法通过重复的ACK号来检测乱序。例如，如果触发了重传，并且原始重传的数据包没有丢失，只是乱序，接收方会多次确认，一次针对重传的数据包，另一次针对到达的乱序数据包。这样，发送方会发现比预期更多的ACK，从而知道发生了乱序。
* TcpExtTCPTSReorder

当填补了一个空洞时，会检测到重排序的报文。例如，假设发送方发送了报文1、2、3、4、5，接收顺序为1、2、4、5、3。当发送方收到报文3的ACK（这将填补空洞）时，有两个条件会让TcpExtTCPTSReorder增加：
1. （1）如果报文3尚未重新传输。
2. （2）如果报文3已经重新传输，但报文3的ACK的时间戳早于重新传输的时间戳。

* TcpExtTCPSACKReorder

通过SACK检测到的重排序报文。SACK有两种方法来检测重排序：（1）发送方接收到DSACK。这意味着发送方发送了同一个报文不止一次。唯一的原因是发送方认为一个乱序的报文丢失了，因此它再次发送该报文。（2）假设发送方发送了报文1、2、3、4、5，并且发送方已经收到了报文2和5的SACK，现在发送方又收到报文4的SACK，并且发送方尚未重新传输该报文，那么发送方就会知道报文4是乱序的。内核中的TCP栈在这两种情况下都会增加TcpExtTCPSACKReorder。

* TcpExtTCPSlowStartRetrans

TCP栈想要重新传输一个报文，并且拥塞控制状态为'Loss'。

* TcpExtTCPFastRetrans

TCP栈想要重新传输一个报文，并且拥塞控制状态不是'Loss'。

* TcpExtTCPLostRetransmit

一个SACK指出一个重新传输的报文再次丢失。

* TcpExtTCPRetransFail

TCP栈尝试将一个重新传输的报文传递给下层，但下层返回错误。

* TcpExtTCPSynRetrans

TCP栈重新传输一个SYN报文。

DSACK
=====

DSACK在`RFC2883`_中定义。接收方使用DSACK向发送方报告重复的报文。有两种类型的重复：（1）已经被确认的报文是重复的。（2）乱序的报文是重复的。TCP栈在接收方和发送方两侧都统计这两种重复情况。
.. _RFC2883 : https://tools.ietf.org/html/rfc2883

* TcpExtTCPDSACKOldSent

TCP栈接收到一个已被确认的重复报文，因此它向发送方发送一个DSACK。

* TcpExtTCPDSACKOfoSent

TCP栈接收到一个乱序的重复报文，因此它向发送方发送一个DSACK。
* TcpExtTCPDSACKRecv

TCP 栈接收到一个 DSACK，表明接收到一个已确认的重复数据包。

* TcpExtTCPDSACKOfoRecv

TCP 栈接收到一个 DSACK，表明接收到一个乱序的重复数据包。

无效的 SACK 和 DSACK
======================
当 SACK（或 DSACK）块无效时，相应的计数器会被更新。验证方法基于 SACK 块的起始/结束序列号。更多细节，请参考内核源代码中函数 `tcp_is_sackblock_valid` 的注释。一个 SACK 选项最多可以有 4 个块，它们分别进行检查。例如，如果一个 SACK 中有 3 个块无效，则相应的计数器将更新 3 次。提交 18f02545a9a1（“[TCP] MIB: Add counters for discarded SACK blocks”）的注释中有额外的解释：

* TcpExtTCPSACKDiscard

此计数器表示有多少 SACK 块是无效的。如果无效的 SACK 块是由 ACK 记录引起的，TCP 栈只会忽略它，并不会更新这个计数器。

* TcpExtTCPDSACKIgnoredOld 和 TcpExtTCPDSACKIgnoredNoUndo

当 DSACK 块无效时，这两个计数器中的一个会被更新。哪个计数器被更新取决于 TCP 套接字的 `undo_marker` 标志。如果 `undo_marker` 没有设置，TCP 栈不太可能重传任何数据包，如果我们仍然接收到一个无效的 DSACK 块，原因可能是数据包在网络中间被重复了。在这种情况下，`TcpExtTCPDSACKIgnoredNoUndo` 将被更新。如果 `undo_marker` 被设置了，`TcpExtTCPDSACKIgnoredOld` 将被更新。从其名称可以推断出，这可能是一个旧的数据包。

SACK 移位
==========
Linux 网络栈在 `sk_buff` 结构体（简称 skb）中存储数据。如果一个 SACK 块跨越多个 skb，TCP 栈将尝试重新安排这些 skb 中的数据。例如，如果一个 SACK 块确认了序列号 10 到 15，skb1 包含序列号 10 到 13，skb2 包含序列号 14 到 20。skb2 中的序列号 14 和 15 将被移动到 skb1。这种操作称为“移位”。如果一个 SACK 块确认了序列号 10 到 20，skb1 包含序列号 10 到 13，skb2 包含序列号 14 到 20。skb2 中的所有数据将被移动到 skb1，并且 skb2 将被丢弃，这种操作称为“合并”。

* TcpExtTCPSackShifted

一个 skb 被移位。

* TcpExtTCPSackMerged

一个 skb 被合并。

* TcpExtTCPSackShiftFallback

一个 skb 应该被移位或合并，但由于某些原因 TCP 栈没有执行这个操作。

TCP 乱序
================
* TcpExtTCPOFOQueue

TCP 层接收到一个乱序的数据包并且有足够的内存将其排队。

* TcpExtTCPOFODrop

TCP 层接收到一个乱序的数据包但没有足够的内存，因此丢弃了它。这样的数据包不会计入 `TcpExtTCPOFOQueue`。

* TcpExtTCPOFOMerge

接收到的乱序数据包与前一个数据包有重叠部分。重叠部分将被丢弃。所有 `TcpExtTCPOFOMerge` 数据包也会被计入 `TcpExtTCPOFOQueue`。

TCP PAWS
========
PAWS（Protection Against Wrapped Sequence numbers）是一种用于丢弃旧数据包的算法。它依赖于 TCP 时间戳。详细信息请参阅 `时间戳 Wiki`_ 和 `PAWS RFC`_。

_时间戳 Wiki：链接到时间戳相关文档。
_PAWS RFC：链接到 PAWS 相关 RFC 文档。
### PAWS 相关 RFC：[PAWS RFC](https://tools.ietf.org/html/rfc1323#page-17)
### 时间戳 维基百科：[TCP 时间戳](https://en.wikipedia.org/wiki/Transmission_Control_Protocol#TCP_timestamps)

* TcpExtPAWSActive

在 SYN-SENT 状态下，数据包被 PAWS（防止包裹序列号）丢弃。
* TcpExtPAWSEstab

在除 SYN-SENT 以外的任何状态下，数据包被 PAWS 丢弃。

### TCP ACK 跳过
在某些情况下，内核会避免频繁发送重复的 ACK。更多细节请参阅 `sysctl 文档`_ 中的 tcp_invalid_ratelimit 部分。当内核决定因 tcp_invalid_ratelimit 而跳过一个 ACK 时，内核会更新以下计数器之一，以指示在何种情况下 ACK 被跳过。只有在接收到的是 SYN 数据包或没有数据的情况下，ACK 才会被跳过。
.. _sysctl 文档: https://www.kernel.org/doc/Documentation/networking/ip-sysctl.rst

* TcpExtTCPACKSkippedSynRecv

在 SYN-RECV 状态下 ACK 被跳过。SYN-RECV 状态意味着 TCP 栈接收到了一个 SYN 并回复了 SYN+ACK。现在 TCP 栈正在等待 ACK。通常情况下，TCP 栈在 SYN-RECV 状态下不需要发送 ACK。但在某些情况下，TCP 栈需要发送 ACK。例如，TCP 栈反复接收到相同的 SYN 数据包、接收到的数据包未通过 PAWS 检查或接收到的数据包序列号超出窗口范围。在这种情况下，如果 ACK 发送频率高于 tcp_invalid_ratelimit 允许的频率，TCP 栈将跳过发送 ACK 并增加 TcpExtTCPACKSkippedSynRecv 的计数。
* TcpExtTCPACKSkippedPAWS

由于 PAWS（防止包裹序列号）检查失败而跳过 ACK。如果在 SYN-RECV、FIN-WAIT-2 或 TIME-WAIT 状态下 PAWS 检查失败，则跳过的 ACK 将被计入 TcpExtTCPACKSkippedSynRecv、TcpExtTCPACKSkippedFinWait2 或 TcpExtTCPACKSkippedTimeWait。在所有其他状态下，跳过的 ACK 将被计入 TcpExtTCPACKSkippedPAWS。
* TcpExtTCPACKSkippedSeq

序列号超出窗口范围且时间戳通过 PAWS 检查，并且 TCP 状态不是 SYN-RECV、FIN-WAIT-2 和 TIME-WAIT。
* TcpExtTCPACKSkippedFinWait2

在 FIN-WAIT-2 状态下跳过 ACK，原因可能是 PAWS 检查失败或接收到的序列号超出窗口范围。
* TcpExtTCPACKSkippedTimeWait

在 TIME-WAIT 状态下跳过 ACK，原因可能是 PAWS 检查失败或接收到的序列号超出窗口范围。
* TcpExtTCPACKSkippedChallenge

如果 ACK 是挑战 ACK，则跳过 ACK。RFC 5961 定义了三种类型的挑战 ACK，请参阅 [RFC 5961 第 3.2 节]_、[RFC 5961 第 4.2 节]_ 和 [RFC 5961 第 5.2 节]_。除了这三种情况外，在某些 TCP 状态下，Linux TCP 栈也会发送挑战 ACK，如果 ACK 号码早于第一个未确认的号码（比 [RFC 5961 第 5.2 节]_ 更严格）。
.. _RFC 5961 第 3.2 节: https://tools.ietf.org/html/rfc5961#page-7
.. _RFC 5961 第 4.2 节: https://tools.ietf.org/html/rfc5961#page-9
.. _RFC 5961 第 5.2 节: https://tools.ietf.org/html/rfc5961#page-11

### TCP 接收窗口
* TcpExtTCPWantZeroWindowAdv

根据当前内存使用情况，TCP 栈尝试将接收窗口设置为零。但接收窗口可能仍然是非零值。例如，如果前一个窗口大小为 10，并且 TCP 栈接收到 3 字节数据，当前窗口大小将是 7，即使根据内存使用情况计算的窗口大小为零。
* TcpExtTCPToZeroWindowAdv

TCP接收窗口从非零值设置为零

* TcpExtTCPFromZeroWindowAdv

TCP接收窗口从零设置为非零值

延迟确认（Delayed ACK）
======================
TCP 延迟确认是一种技术，用于减少网络中的数据包数量。更多详情，请参阅[延迟确认维基页面](_)

.. _延迟确认维基页面: https://en.wikipedia.org/wiki/TCP_delayed_acknowledgment

* TcpExtDelayedACKs

延迟确认定时器到期。TCP 栈将发送一个纯确认（ACK）数据包并退出延迟确认模式
* TcpExtDelayedACKLocked

延迟确认定时器到期，但由于用户空间程序锁定了套接字，TCP 栈无法立即发送 ACK。TCP 栈将在稍后（用户空间程序解锁套接字后）发送一个纯 ACK 数据包。当 TCP 栈稍后发送纯 ACK 时，它还会更新 TcpExtDelayedACKs 并退出延迟确认模式
* TcpExtDelayedACKLost

当 TCP 栈收到已经被确认的数据包时，该计数器会被更新。延迟确认丢失可能会导致此问题，但也可能是由其他原因触发的，例如网络中数据包被重复

尾部丢包探测（TLP）
=====================
TLP 是一种用于检测 TCP 数据包丢失的算法。更多详情，请参阅[TLP 论文](_)
.. _TLP 论文: https://tools.ietf.org/html/draft-dukkipati-tcpm-tcp-loss-probe-01

* TcpExtTCPLossProbes

发送了一个 TLP 探测数据包
* TcpExtTCPLossProbeRecovery

检测到并通过 TLP 恢复了数据包丢失

TCP 快速打开描述
====================
TCP 快速打开是一种技术，允许在完成三次握手之前进行数据传输。请参阅[TCP 快速打开维基页面](_) 了解一般描述
.. _TCP 快速打开维基页面: https://en.wikipedia.org/wiki/TCP_Fast_Open

* TcpExtTCPFastOpenActive

当 TCP 栈在 SYN-SENT 状态下接收到一个 ACK 数据包，并且该 ACK 数据包确认了 SYN 数据包中的数据时，TCP 栈认为 TFO（TCP 快速打开）cookie 被对方接受，然后更新此计数器
* TcpExtTCPFastOpenActiveFail

此计数器表示TCP堆栈发起了TCP快速打开，但失败了。此计数器会在以下三种情况下更新：（1）对端未确认SYN数据包中的数据。（2）带有TFO cookie的SYN数据包至少超时一次。（3）在三次握手之后，重传超时次数达到net.ipv4.tcp_retries1次，因为某些中间盒设备可能会在握手后将快速打开丢弃。

* TcpExtTCPFastOpenPassive

此计数器表示TCP堆栈接受快速打开请求的次数。

* TcpExtTCPFastOpenPassiveFail

此计数器表示TCP堆栈拒绝快速打开请求的次数。原因可能是TFO cookie无效或在创建套接字过程中TCP堆栈检测到错误。

* TcpExtTCPFastOpenListenOverflow

当待处理的快速打开请求数量超过fastopenq->max_qlen时，TCP堆栈会拒绝快速打开请求并更新此计数器。当此计数器被更新时，TCP堆栈不会更新TcpExtTCPFastOpenPassive或TcpExtTCPFastOpenPassiveFail。fastopenq->max_qlen由TCP_FASTOPEN套接字操作设置，并且不能大于net.core.somaxconn。例如：

```c
setsockopt(sfd, SOL_TCP, TCP_FASTOPEN, &qlen, sizeof(qlen));
```

* TcpExtTCPFastOpenCookieReqd

此计数器表示客户端想要请求TFO cookie的次数。

### SYN Cookies
SYN Cookies用于缓解SYN泛洪攻击，详情请参阅`SYN Cookies维基页面`_。
.. _SYN Cookies维基页面: https://en.wikipedia.org/wiki/SYN_cookies

* TcpExtSyncookiesSent

此计数器表示发送了多少个SYN Cookies。

* TcpExtSyncookiesRecv

TCP堆栈接收了多少个SYN Cookies的回复数据包。

* TcpExtSyncookiesFailed

从SYN Cookie解码出的MSS无效。当此计数器被更新时，接收到的数据包不会被视为SYN Cookie，并且TcpExtSyncookiesRecv计数器也不会被更新。

### 挑战ACK
有关挑战ACK的详细信息，请参阅TcpExtTCPACKSkippedChallenge的解释。

* TcpExtTCPChallengeACK

发送的挑战ACK的数量。
* TcpExtTCPSYNChallenge

收到SYN数据包后发送的挑战确认数量。更新此计数器后，TCP堆栈可能会发送一个挑战ACK并更新TcpExtTCPChallengeACK计数器，或者也可能跳过发送挑战并更新TcpExtTCPACKSkippedChallenge计数器。

=====
当套接字处于内存压力下时，TCP堆栈会尝试从接收队列和乱序队列中回收内存。其中一种回收方法是“折叠”，即分配一个大的skb，将连续的小skb复制到这个大skb中，并释放这些连续的小skb。

* TcpExtPruneCalled

TCP堆栈尝试为套接字回收内存。更新此计数器后，TCP堆栈会尝试对乱序队列和接收队列进行折叠。如果内存仍然不足，TCP堆栈将尝试丢弃乱序队列中的数据包（并更新TcpExtOfoPruned计数器）。

* TcpExtOfoPruned

TCP堆栈尝试丢弃乱序队列中的数据包。

* TcpExtRcvPruned

在执行“折叠”和丢弃乱序队列中的数据包之后，如果实际使用的内存仍然大于最大允许内存，此计数器将被更新。这意味着“修剪”失败。

* TcpExtTCPRcvCollapsed

此计数器表示在“折叠”过程中释放了多少个skb。

示例
========

ping测试
---------
针对公共DNS服务器8.8.8.8运行ping命令：

```
nstatuser@nstat-a:~$ ping 8.8.8.8 -c 1
PING 8.8.8.8 (8.8.8.8) 56(84) 字节的数据
来自8.8.8.8的64字节：icmp_seq=1 ttl=119 时间=17.8 ms

--- 8.8.8.8 的 ping 统计信息 ---
传输了1个数据包，收到了1个数据包，0%的数据包丢失，时间0ms
往返时间最小值/平均值/最大值/标准差 = 17.875/17.875/17.875/0.000 ms
```

nstat结果如下：

```
nstatuser@nstat-a:~$ nstat
#内核
IpInReceives                    1                  0.0
IpInDelivers                    1                  0.0
IpOutRequests                   1                  0.0
IcmpInMsgs                      1                  0.0
IcmpInEchoReps                  1                  0.0
IcmpOutMsgs                     1                  0.0
IcmpOutEchos                    1                  0.0
IcmpMsgInType0                  1                  0.0
IcmpMsgOutType8                 1                  0.0
IpExtInOctets                   84                 0.0
IpExtOutOctets                  84                 0.0
IpExtInNoECTPkts                1                  0.0
```

Linux服务器发送了一个ICMP Echo数据包，因此IpOutRequests、IcmpOutMsgs、IcmpOutEchos 和 IcmpMsgOutType8 增加了1。服务器从8.8.8.8收到了ICMP Echo回复，因此IpInReceives、IcmpInMsgs、IcmpInEchoReps 和 IcmpMsgInType0 增加了1。ICMP Echo回复通过IP层传递到ICMP层，因此IpInDelivers增加了1。默认ping数据大小为48字节，因此一个ICMP Echo数据包及其对应的Echo回复数据包由以下部分构成：

* 14字节MAC头
* 20字节IP头
* 16字节ICMP头
* 48字节数据（ping命令的默认值）

因此IpExtInOctets和IpExtOutOctets为20+16+48=84字节。

TCP三步握手
-------------------
在服务器端，我们运行：

```
nstatuser@nstat-b:~$ nc -lknv 0.0.0.0 9000
监听 [0.0.0.0]（家族0，端口9000）
```

在客户端，我们运行：

```
nstatuser@nstat-a:~$ nc -nv 192.168.122.251 9000
连接到 192.168.122.251 9000 端口 [tcp/*] 成功！
```

服务器监听TCP 9000端口，客户端连接到它，它们完成了三步握手。
在服务器端，我们可以找到以下nstat输出：

```
nstatuser@nstat-b:~$ nstat | grep -i tcp
TcpPassiveOpens                 1                  0.0
TcpInSegs                       2                  0.0
TcpOutSegs                      1                  0.0
TcpExtTCPPureAcks               1                  0.0
```

在客户端，我们可以找到以下nstat输出：

```
nstatuser@nstat-a:~$ nstat | grep -i tcp
TcpActiveOpens                  1                  0.0
TcpInSegs                       1                  0.0
TcpOutSegs                      2                  0.0
```

当服务器收到第一个SYN时，它回复了一个SYN+ACK，并进入了SYN-RCVD状态，因此TcpPassiveOpens增加了1。服务器收到了SYN，发送了SYN+ACK，收到了ACK，所以服务器发送了1个数据包，收到了2个数据包，TcpInSegs增加了2，TcpOutSegs增加了1。三步握手中的最后一个ACK是一个没有数据的纯ACK，因此TcpExtTCPPureAcks增加了1。
当客户端发送SYN时，客户端进入SYN-SENT状态，因此TcpActiveOpens增加了1。客户端发送了SYN，收到了SYN+ACK，发送了ACK，因此客户端发送了2个数据包，收到了1个数据包，TcpInSegs增加了1，TcpOutSegs增加了2。
TCP 正常流量
------------------
在服务器上运行 `nc` ：

  nstatuser@nstat-b:~$ nc -lkv 0.0.0.0 9000
  Listening on [0.0.0.0] (family 0, port 9000)

在客户端运行 `nc` ：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!

在 `nc` 客户端输入字符串（本例中为 'hello'）：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!
  hello

客户端的 `nstat` 输出：

  nstatuser@nstat-a:~$ nstat
  #kernel
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  TcpExtTCPPureAcks               1                  0.0
  TcpExtTCPOrigDataSent           1                  0.0
  IpExtInOctets                   52                 0.0
  IpExtOutOctets                  58                 0.0
  IpExtInNoECTPkts                1                  0.0

服务器端的 `nstat` 输出：

  nstatuser@nstat-b:~$ nstat
  #kernel
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  IpExtInOctets                   58                 0.0
  IpExtOutOctets                  52                 0.0
  IpExtInNoECTPkts                1                  0.0

再次在客户端输入字符串（本例中为 'world'）：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!
  hello
  world

客户端的 `nstat` 输出：

  nstatuser@nstat-a:~$ nstat
  #kernel
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  TcpExtTCPHPAcks                 1                  0.0
  TcpExtTCPOrigDataSent           1                  0.0
  IpExtInOctets                   52                 0.0
  IpExtOutOctets                  58                 0.0
  IpExtInNoECTPkts                1                  0.0

服务器端的 `nstat` 输出：

  nstatuser@nstat-b:~$ nstat
  #kernel
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  TcpExtTCPHPHits                 1                  0.0
  IpExtInOctets                   58                 0.0
  IpExtOutOctets                  52                 0.0
  IpExtInNoECTPkts                1                  0.0

比较第一次客户端的 `nstat` 输出和第二次客户端的 `nstat` 输出，我们可以发现一个不同之处：第一次有 'TcpExtTCPPureAcks'，而第二次有 'TcpExtTCPHPAcks'。第一次服务器端的 `nstat` 和第二次服务器端的 `nstat` 也有不同之处：第二次服务器端的 `nstat` 有一个 TcpExtTCPHPHits，但第一次服务器端的 `nstat` 没有。网络流量模式完全相同：客户端发送了一个数据包给服务器，服务器回复了一个 ACK。但是内核处理它们的方式不同。当没有使用 TCP 窗口扩展选项时，内核会在连接进入已建立状态后立即尝试启用快速路径；但如果使用了 TCP 窗口扩展选项，则内核会首先禁用快速路径，并在接收到数据包后再尝试启用它。我们可以使用 `ss` 命令来验证是否启用了窗口扩展选项。例如，在服务器或客户端上运行以下命令：

  nstatuser@nstat-a:~$ ss -o state established -i '( dport = :9000 or sport = :9000 )'
  Netid    Recv-Q     Send-Q            Local Address:Port             Peer Address:Port
  tcp      0          0               192.168.122.250:40654         192.168.122.251:9000
             ts sack cubic wscale:7,7 rto:204 rtt:0.98/0.49 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:10 bytes_acked:1 segs_out:2 segs_in:1 send 118.2Mbps lastsnd:46572 lastrcv:46572 lastack:46572 pacing_rate 236.4Mbps rcv_space:29200 rcv_ssthresh:29200 minrtt:0.98

'wscale:7,7' 表示服务器和客户端都将窗口扩展选项设置为 7。现在我们可以解释测试中的 `nstat` 输出：

在客户端第一次 `nstat` 输出中，客户端发送了一个数据包，服务器回复了一个 ACK，当内核处理这个 ACK 时，快速路径尚未启用，因此该 ACK 被计入 'TcpExtTCPPureAcks'。
在客户端第二次 `nstat` 输出中，客户端再次发送了一个数据包，并从服务器接收到了另一个 ACK。此时，快速路径已启用，且该 ACK 符合快速路径条件，因此被快速路径处理，因此该 ACK 被计入 'TcpExtTCPHPAcks'。
在服务器端第一次 `nstat` 输出中，快速路径尚未启用，因此没有 'TcpExtTCPHPHits'。
在服务器端第二次 `nstat` 输出中，快速路径已启用，且从客户端接收到的数据包符合快速路径条件，因此被计入 'TcpExtTCPHPHits'。

TcpExtTCPAbortOnClose
---------------------
在服务器端，我们运行以下 Python 脚本：

  import socket
  import time

  port = 9000

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('0.0.0.0', port))
  s.listen(1)
  sock, addr = s.accept()
  while True:
      time.sleep(9999999)

此 Python 脚本监听 9000 端口，但不读取任何内容。
在客户端，我们通过 `nc` 发送字符串 "hello" ：

  nstatuser@nstat-a:~$ echo "hello" | nc nstat-b 9000

然后回到服务器端，服务器已经收到了 "hello" 数据包，TCP 层也确认了这个数据包，但应用程序还没有读取它。我们按 Ctrl-C 终止服务器脚本。然后我们会发现服务器端的 TcpExtTCPAbortOnClose 增加了 1 ：

  nstatuser@nstat-b:~$ nstat | grep -i abort
  TcpExtTCPAbortOnClose           1                  0.0

如果我们在服务器端运行 `tcpdump` ，我们会发现在按 Ctrl-C 后，服务器发送了一个 RST。

TcpExtTCPAbortOnMemory 和 TcpExtTCPAbortOnTimeout
---------------------------------------------------
下面是一个让孤儿套接字数量超过 net.ipv4.tcp_max_orphans 的示例。
在客户端将 tcp_max_orphans 设置为较小值：

  sudo bash -c "echo 10 > /proc/sys/net/ipv4/tcp_max_orphans"

客户端代码（创建 64 个到服务器的连接）：

  nstatuser@nstat-a:~$ cat client_orphan.py
  import socket
  import time

  server = 'nstat-b' # 服务器地址
  port = 9000

  count = 64

  connection_list = []

  for i in range(64):
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect((server, port))
      connection_list.append(s)
      print("connection_count: %d" % len(connection_list))

  while True:
      time.sleep(99999)

服务器代码（接受来自客户端的 64 个连接）：

  nstatuser@nstat-b:~$ cat server_orphan.py
  import socket
  import time

  port = 9000
  count = 64

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('0.0.0.0', port))
  s.listen(count)
  connection_list = []
  while True:
      sock, addr = s.accept()
      connection_list.append((sock, addr))
      print("connection_count: %d" % len(connection_list))

在服务器和客户端上运行 Python 脚本
在服务器上：

  python3 server_orphan.py

在客户端上：

  python3 client_orphan.py

在服务器上运行 iptables ：

  sudo iptables -A INPUT -i ens3 -p tcp --destination-port 9000 -j DROP

在客户端按 Ctrl-C，停止 client_orphan.py
检查客户端上的 TcpExtTCPAbortOnMemory ：

  nstatuser@nstat-a:~$ nstat | grep -i abort
  TcpExtTCPAbortOnMemory          54                 0.0

检查客户端上的孤儿套接字数量：

  nstatuser@nstat-a:~$ ss -s
  Total: 131 (kernel 0)
  TCP:   14 (estab 1, closed 0, orphaned 10, synrecv 0, timewait 0/0), ports 0

  Transport Total     IP        IPv6
  *         0         -         -
  RAW       1         0         1
  UDP       1         1         0
  TCP       14        13        1
  INET      16        14        2
  FRAG      0         0         0

测试解释：运行 server_orphan.py 和 client_orphan.py 后，我们建立了 64 个服务器与客户端之间的连接。运行 iptables 命令后，服务器会丢弃所有来自客户端的数据包。在 client_orphan.py 上按 Ctrl-C，客户端系统会尝试关闭这些连接，并在它们优雅关闭前变成孤儿套接字。由于服务器的 iptables 阻止了来自客户端的数据包，服务器不会收到 FIN，因此所有客户端上的连接都会卡在 FIN_WAIT_1 阶段，直到超时。我们把 10 写入 /proc/sys/net/ipv4/tcp_max_orphans，所以客户端系统只会保留 10 个孤儿套接字，对于其他孤儿套接字，客户端系统会发送 RST 并删除它们。我们有 64 个连接，因此 'ss -s' 命令显示系统中有 10 个孤儿套接字，而 TcpExtTCPAbortOnMemory 的值为 54。
关于孤儿套接字数量的额外解释：你可以通过`ss -s`命令找到确切的孤儿套接字数量，但当内核决定是否增加TcpExtTCPAbortOnMemory并发送RST时，并不总是检查确切的数量。为了提高性能，内核首先检查一个近似数量，如果这个近似数量超过tcp_max_orphans，则内核会再次检查确切的数量。因此，如果近似数量小于tcp_max_orphans，但实际上的确切数量超过了tcp_max_orphans，你可能会发现TcpExtTCPAbortOnMemory并没有增加。如果tcp_max_orphans足够大，这种情况不会发生；但如果将tcp_max_orphans减小到一个很小的值（如我们的测试），你可能会遇到这个问题。在我们的测试中，客户端虽然设置了tcp_max_orphans为10，但还是建立了64个连接。如果客户端只建立了11个连接，我们就无法发现TcpExtTCPAbortOnMemory的变化。

继续之前的测试，我们等待几分钟。由于服务器上的iptables阻止了流量，服务器不会收到FIN报文，客户端的所有孤儿套接字最终都会在FIN_WAIT_1状态下超时。因此，等待几分钟后，我们可以看到客户端有10个超时：

```
nstatuser@nstat-a:~$ nstat | grep -i abort
TcpExtTCPAbortOnTimeout         10                 0.0
```

### TcpExtTCPAbortOnLinger
#### 服务器端代码：
```python
nstatuser@nstat-b:~$ cat server_linger.py
import socket
import time

port = 9000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', port))
s.listen(1)
sock, addr = s.accept()
while True:
    time.sleep(9999999)
```

#### 客户端代码：
```python
nstatuser@nstat-a:~$ cat client_linger.py
import socket
import struct

server = 'nstat-b'  # 服务器地址
port = 9000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 10))
s.setsockopt(socket.SOL_TCP, socket.TCP_LINGER2, struct.pack('i', -1))
s.connect((server, port))
s.close()
```

在服务器上运行server_linger.py：
```
nstatuser@nstat-b:~$ python3 server_linger.py
```

在客户端上运行client_linger.py：
```
nstatuser@nstat-a:~$ python3 client_linger.py
```

运行client_linger.py后，检查nstat输出：
```
nstatuser@nstat-a:~$ nstat | grep -i abort
TcpExtTCPAbortOnLinger          1                  0.0
```

### TcpExtTCPRcvCoalesce
在服务器上运行一个监听TCP端口9000但不读取任何数据的程序：
```python
import socket
import time

port = 9000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', port))
s.listen(1)
sock, addr = s.accept()
while True:
    time.sleep(9999999)
```

保存上述代码为server_coalesce.py并运行：
```
python3 server_coalesce.py
```

在客户端上保存以下代码为client_coalesce.py：
```python
import socket

server = 'nstat-b'
port = 9000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((server, port))
```

运行：
```
nstatuser@nstat-a:~$ python3 -i client_coalesce.py
```

使用`-i`进入交互模式，然后发送一个数据包：
```
>>> s.send(b'foo')
3
```

再发送一个数据包：
```
>>> s.send(b'bar')
3
```

在服务器上运行nstat：
```
ubuntu@nstat-b:~$ nstat
#kernel
IpInReceives                    2                  0.0
IpInDelivers                    2                  0.0
IpOutRequests                   2                  0.0
TcpInSegs                       2                  0.0
TcpOutSegs                      2                  0.0
TcpExtTCPRcvCoalesce            1                  0.0
IpExtInOctets                   110                0.0
IpExtOutOctets                  104                0.0
IpExtInNoECTPkts                2                  0.0
```

客户端发送了两个数据包，服务器没有读取任何数据。当第二个数据包到达服务器时，第一个数据包仍在接收队列中。因此，TCP层合并了这两个数据包，我们可以看到TcpExtTCPRcvCoalesce增加了1。

### TcpExtListenOverflows 和 TcpExtListenDrops
在服务器上运行nc命令，监听端口9000：
```
nstatuser@nstat-b:~$ nc -lkv 0.0.0.0 9000
Listening on [0.0.0.0] (family 0, port 9000)
```

在客户端的不同终端上运行3个nc命令：
```
nstatuser@nstat-a:~$ nc -v nstat-b 9000
Connection to nstat-b 9000 port [tcp/*] succeeded!
```

nc命令只接受一个连接，且接受队列长度为1。在当前Linux实现中，设置队列长度为n意味着实际队列长度为n+1。现在我们创建3个连接，其中1个被nc接受，2个在队列中，因此接受队列已满。

在运行第四个nc之前，清除服务器上的nstat历史记录：
```
nstatuser@nstat-b:~$ nstat -n
```

在客户端运行第四个nc：
```
nstatuser@nstat-a:~$ nc -v nstat-b 9000
```

如果nc服务器运行在4.10或更高版本的内核上，你不会看到“Connection to ... succeeded!”字符串，因为内核会在接受队列满时丢弃SYN报文。如果nc客户端运行在较旧的内核上，你会看到连接成功，因为内核会完成三次握手并将套接字保留在半开放队列中。我在4.15内核上进行了测试，以下是服务器上的nstat输出：
```
nstatuser@nstat-b:~$ nstat
#kernel
IpInReceives                    4                  0.0
IpInDelivers                    4                  0.0
TcpInSegs                       4                  0.0
TcpExtListenOverflows           4                  0.0
TcpExtListenDrops               4                  0.0
IpExtInOctets                   240                0.0
IpExtInNoECTPkts                4                  0.0
```

TcpExtListenOverflows和TcpExtListenDrops都是4。如果第四个nc和nstat之间的时间更长，TcpExtListenOverflows和TcpExtListenDrops的值会更大，因为第四个nc的SYN被丢弃了，客户端正在重试。

### IpInAddrErrors, IpExtInNoRoutes 和 IpOutNoRoutes
#### 服务器A IP地址：192.168.122.250
#### 服务器B IP地址：192.168.122.251
在服务器A上准备，添加一条到服务器B的路由：
```
$ sudo ip route add 8.8.8.8/32 via 192.168.122.251
```

在服务器B上准备，禁用所有接口的send_redirects：
```
$ sudo sysctl -w net.ipv4.conf.all.send_redirects=0
$ sudo sysctl -w net.ipv4.conf.ens3.send_redirects=0
$ sudo sysctl -w net.ipv4.conf.lo.send_redirects=0
$ sudo sysctl -w net.ipv4.conf.default.send_redirects=0
```

我们希望让服务器A向8.8.8.8发送一个数据包，并将其路由到服务器B。当服务器B收到这个数据包时，它可能会向服务器A发送一个ICMP Redirect消息，将send_redirects设置为0可以禁用这种行为。
#### 第一步：生成InAddrErrors
在服务器B上禁用IP转发：
```
$ sudo sysctl -w net.ipv4.conf.all.forwarding=0
```

在服务器A上向8.8.8.8发送数据包：
```
$ nc -v 8.8.8.8 53
```

在服务器B上检查nstat输出：
```
$ nstat
#kernel
IpInReceives                    3                  0.0
IpInAddrErrors                  3                  0.0
IpExtInOctets                   180                0.0
IpExtInNoECTPkts                3                  0.0
```

因为我们让服务器A将8.8.8.8的数据包路由到服务器B，并且禁用了服务器B上的IP转发，所以服务器A发送的数据包被服务器B丢弃并增加了IpInAddrErrors。由于nc命令会在没有收到SYN+ACK时重新发送SYN报文，我们会看到多次IpInAddrErrors。
#### 第二步：生成IpExtInNoRoutes
在服务器B上启用IP转发：
```
$ sudo sysctl -w net.ipv4.conf.all.forwarding=1
```

检查服务器B的路由表并删除默认路由：
```
$ ip route show
default via 192.168.122.1 dev ens3 proto static
192.168.122.0/24 dev ens3 proto kernel scope link src 192.168.122.251
$ sudo ip route delete default via 192.168.122.1 dev ens3 proto static
```

在服务器A上联系8.8.8.8：
```
$ nc -v 8.8.8.8 53
nc: connect to 8.8.8.8 port 53 (tcp) failed: Network is unreachable
```

在服务器B上运行nstat：
```
$ nstat
#kernel
IpInReceives                    1                  0.0
IpOutRequests                   1                  0.0
IcmpOutMsgs                     1                  0.0
IcmpOutDestUnreachs             1                  0.0
IcmpMsgOutType3                 1                  0.0
IpExtInNoRoutes                 1                  0.0
IpExtInOctets                   60                 0.0
IpExtOutOctets                  88                 0.0
IpExtInNoECTPkts                1                  0.0
```

我们在服务器B上启用了IP转发，当服务器B收到目标IP地址为8.8.8.8的数据包时，服务器B会尝试转发该数据包。由于我们删除了默认路由，没有路由指向8.8.8.8，因此服务器B增加了IpExtInNoRoutes，并向服务器A发送了“ICMP Destination Unreachable”消息。
#### 第三步：生成IpOutNoRoutes
在服务器B上运行ping命令：
```
$ ping -c 1 8.8.8.8
connect: Network is unreachable
```

在服务器B上运行nstat：
```
$ nstat
#kernel
IpOutNoRoutes                   1                  0.0
```

我们在服务器B上删除了默认路由，服务器B找不到8.8.8.8的路由，因此增加了IpOutNoRoutes。
### TcpExtTCPACKSkippedSynRecv
在这个测试中，我们从客户端向服务器发送3个相同的SYN报文。第一个SYN报文会让服务器创建一个套接字，将其设置为Syn-Recv状态，并回复一个SYN/ACK。第二个SYN报文会让服务器再次回复SYN/ACK，并记录回复时间（重复ACK回复时间）。第三个SYN报文会让服务器检查之前的重复ACK回复时间，并决定跳过重复ACK，然后增加TcpExtTCPACKSkippedSynRecv计数器。

运行tcpdump捕获一个SYN报文：
```
nstatuser@nstat-a:~$ sudo tcpdump -c 1 -w /tmp/syn.pcap port 9000
tcpdump: listening on ens3, link-type EN10MB (Ethernet), capture size 262144 bytes
```

在另一个终端上运行nc命令：
```
nstatuser@nstat-a:~$ nc nstat-b 9000
```

由于nstat-b没有监听端口9000，它应该回复一个RST，nc命令会立即退出。这对于tcpdump命令来说已经足够捕获一个SYN报文。Linux服务器可能会使用硬件卸载来计算TCP校验和，因此/tmp/syn.pcap中的校验和可能不正确。我们调用tcprewrite来修复它：
```
nstatuser@nstat-a:~$ tcprewrite --infile=/tmp/syn.pcap --outfile=/tmp/syn_fixcsum.pcap --fixcsum
```

在nstat-b上运行nc来监听端口9000：
```
nstatuser@nstat-b:~$ nc -lkv 9000
Listening on [0.0.0.0] (family 0, port 9000)
```

在nstat-a上阻止来自端口9000的数据包，否则nstat-a会向nstat-b发送RST：
```
nstatuser@nstat-a:~$ sudo iptables -A INPUT -p tcp --sport 9000 -j DROP
```

反复发送3次SYN到nstat-b：
```
nstatuser@nstat-a:~$ for i in {1..3}; do sudo tcpreplay -i ens3 /tmp/syn_fixcsum.pcap; done
```

检查nstat-b上的SNMP计数器：
```
nstatuser@nstat-b:~$ nstat | grep -i skip
TcpExtTCPACKSkippedSynRecv      1                  0.0
```

正如预期的那样，TcpExtTCPACKSkippedSynRecv为1。
TcpExtTCPACKSkippedPAWS
-----------------------
要触发 PAWS，我们可以发送一个旧的 SYN 包。
在 nstat-b 上，使用 nc 监听 9000 端口：

  nstatuser@nstat-b:~$ nc -lkv 9000
  Listening on [0.0.0.0] (family 0, port 9000)

在 nstat-a 上，运行 tcpdump 捕获一个 SYN 包：

  nstatuser@nstat-a:~$ sudo tcpdump -w /tmp/paws_pre.pcap -c 1 port 9000
  tcpdump: listening on ens3, link-type EN10MB (Ethernet), capture size 262144 bytes

在 nstat-a 上，运行 nc 作为客户端连接 nstat-b：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!

现在 tcpdump 已经捕获了 SYN 包并退出。我们需要修复校验和：

  nstatuser@nstat-a:~$ tcprewrite --infile /tmp/paws_pre.pcap --outfile /tmp/paws.pcap --fixcsum

发送两次 SYN 包：

  nstatuser@nstat-a:~$ for i in {1..2}; do sudo tcpreplay -i ens3 /tmp/paws.pcap; done

在 nstat-b 上，检查 snmp 计数器：

  nstatuser@nstat-b:~$ nstat | grep -i skip
  TcpExtTCPACKSkippedPAWS         1                  0.0

我们通过 tcpreplay 发送了两个 SYN 包，这两个包都会让 PAWS 检查失败。nstat-b 对第一个 SYN 发送了一个 ACK，并跳过了对第二个 SYN 的 ACK，同时更新了 TcpExtTCPACKSkippedPAWS。

TcpExtTCPACKSkippedSeq
----------------------
要触发 TcpExtTCPACKSkippedSeq，我们需要发送具有有效时间戳（以通过 PAWS 检查）但序列号超出窗口范围的包。Linux TCP 栈会避免跳过包含数据的包，因此我们需要一个纯 ACK 包。为此，我们可以创建两个套接字：一个监听 9000 端口，另一个监听 9001 端口。然后我们捕获 9001 端口上的 ACK 包，修改源端口和目标端口使其匹配 9000 端口的套接字。这样就可以通过这个包触发 TcpExtTCPACKSkippedSeq。

在 nstat-b 上打开两个终端，分别监听 9000 端口和 9001 端口：

  nstatuser@nstat-b:~$ nc -lkv 9000
  Listening on [0.0.0.0] (family 0, port 9000)

  nstatuser@nstat-b:~$ nc -lkv 9001
  Listening on [0.0.0.0] (family 0, port 9001)

在 nstat-a 上运行两个 nc 客户端：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!

  nstatuser@nstat-a:~$ nc -v nstat-b 9001
  Connection to nstat-b 9001 port [tcp/*] succeeded!

在 nstat-a 上，运行 tcpdump 捕获一个 ACK 包：

  nstatuser@nstat-a:~$ sudo tcpdump -w /tmp/seq_pre.pcap -c 1 dst port 9001
  tcpdump: listening on ens3, link-type EN10MB (Ethernet), capture size 262144 bytes

在 nstat-b 上，通过 9001 端口的套接字发送一个包。例如，在我们的示例中发送字符串 'foo'：

  nstatuser@nstat-b:~$ nc -lkv 9001
  Listening on [0.0.0.0] (family 0, port 9001)
  Connection from nstat-a 42132 received!
  foo

在 nstat-a 上，tcpdump 应该已经捕获到了 ACK 包。我们需要检查两个 nc 客户端的源端口号：

  nstatuser@nstat-a:~$ ss -ta '( dport = :9000 || dport = :9001 )' | tee
  State  Recv-Q   Send-Q         Local Address:Port           Peer Address:Port
  ESTAB  0        0            192.168.122.250:50208       192.168.122.251:9000
  ESTAB  0        0            192.168.122.250:42132       192.168.122.251:9001

运行 tcprewrite，将端口 9001 改为 9000，将端口 42132 改为 50208：

  nstatuser@nstat-a:~$ tcprewrite --infile /tmp/seq_pre.pcap --outfile /tmp/seq.pcap -r 9001:9000 -r 42132:50208 --fixcsum

现在 /tmp/seq.pcap 是我们需要的包。将其发送到 nstat-b：

  nstatuser@nstat-a:~$ for i in {1..2}; do sudo tcpreplay -i ens3 /tmp/seq.pcap; done

在 nstat-b 上检查 TcpExtTCPACKSkippedSeq：

  nstatuser@nstat-b:~$ nstat | grep -i skip
  TcpExtTCPACKSkippedSeq          1                  0.0
