SNMP 计数器
==========

本文档解释了 SNMP 计数器的含义。
通用 IPv4 计数器
================
所有第四层数据包和 ICMP 数据包都会改变这些计数器，但是第二层数据包（如 STP）或 ARP 数据包不会改变这些计数器。
* IpInReceives

定义于 `RFC1213 IpInReceives`_

.. _RFC1213 IpInReceives: https://tools.ietf.org/html/rfc1213#page-26

IP 层接收到的数据包数量。在 ip_rcv 函数开始时递增，并始终与 IpExtInOctets 一起更新。即使数据包之后被丢弃（例如由于 IP 头无效或校验和错误等），也会增加该计数。它表示 GRO/LRO 后聚合的数据段数量。
* IpInDelivers

定义于 `RFC1213 IpInDelivers`_

.. _RFC1213 IpInDelivers: https://tools.ietf.org/html/rfc1213#page-28

传递给上层协议的数据包数量。例如 TCP、UDP、ICMP 等。如果没有监听原始套接字，则仅传递内核支持的协议；如果有监听原始套接字，则所有有效的 IP 数据包都将被传递。
* IpOutRequests

定义于 `RFC1213 IpOutRequests`_

.. _RFC1213 IpOutRequests: https://tools.ietf.org/html/rfc1213#page-28

通过 IP 层发送的数据包数量，包括单播和组播数据包，并始终与 IpExtOutOctets 一起更新。
* IpExtInOctets 和 IpExtOutOctets

它们是 Linux 内核扩展，没有 RFC 定义。请注意，虽然 RFC1213 确实定义了 ifInOctets 和 ifOutOctets，但它们是不同的概念。ifInOctets 和 ifOutOctets 包括 MAC 层头大小，而 IpExtInOctets 和 IpExtOutOctets 只包括 IP 层头和 IP 层数据。
* IpExtInNoECTPkts, IpExtInECT1Pkts, IpExtInECT0Pkts, IpExtInCEPkts

这些计数器表示四种 ECN IP 数据包的数量，请参阅 `显式拥塞通知`_ 获取更多详细信息。

.. _显式拥塞通知: https://tools.ietf.org/html/rfc3168#page-6

这四个计数器根据 ECN 状态计算接收的数据包数量。它们根据实际帧数进行计数，无论是否使用 LRO/GRO。因此对于同一个数据包，您可能会发现 IpInReceives 计为 1，而 IpExtInNoECTPkts 计为 2 或更多。
* IpInHdrErrors

定义于 `RFC1213 IpInHdrErrors`_。表示因 IP 头错误而被丢弃的数据包数量。可能发生在 IP 输入和 IP 转发路径中。

.. _RFC1213 IpInHdrErrors: https://tools.ietf.org/html/rfc1213#page-27

* IpInAddrErrors

定义于 `RFC1213 IpInAddrErrors`_。在以下两种情况下会增加：(1) IP 地址无效。(2) 目标 IP 地址不是本地地址且未启用 IP 转发。

.. _RFC1213 IpInAddrErrors: https://tools.ietf.org/html/rfc1213#page-27

* IpExtInNoRoutes

此计数器表示当 IP 栈接收到一个数据包并且无法从路由表中找到相应路由时丢弃的数据包数量。可能发生在启用 IP 转发时，目标 IP 地址不是本地地址且没有通往目标 IP 地址的路由。
以下是对提供的英文内容的中文翻译：

* IpInUnknownProtos

在 `RFC1213 ipInUnknownProtos`_ 中定义。如果第四层协议不被内核支持，该计数器将增加。如果应用程序使用原始套接字，内核会始终将数据包发送到原始套接字，而不会增加此计数器。
.. _RFC1213 ipInUnknownProtos: https://tools.ietf.org/html/rfc1213#page-27

* IpExtInTruncatedPkts

对于IPv4数据包，这意味着实际数据大小小于IPv4头部中的 "总长度" 字段。
* IpInDiscards

在 `RFC1213 ipInDiscards`_ 中定义。它表示数据包在IP接收路径中因内核内部原因（例如没有足够的内存）被丢弃。
.. _RFC1213 ipInDiscards: https://tools.ietf.org/html/rfc1213#page-28

* IpOutDiscards

在 `RFC1213 ipOutDiscards`_ 中定义。它表示数据包在IP发送路径中因内核内部原因被丢弃。
.. _RFC1213 ipOutDiscards: https://tools.ietf.org/html/rfc1213#page-28

* IpOutNoRoutes

在 `RFC1213 ipOutNoRoutes`_ 中定义。它表示数据包在IP发送路径中被丢弃，且未找到路由。
.. _RFC1213 ipOutNoRoutes: https://tools.ietf.org/html/rfc1213#page-29

ICMP计数器
==========
* IcmpInMsgs 和 IcmpOutMsgs

由 `RFC1213 icmpInMsgs`_ 和 `RFC1213 icmpOutMsgs`_ 定义。

.. _RFC1213 icmpInMsgs: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpOutMsgs: https://tools.ietf.org/html/rfc1213#page-43

如RFC1213所述，这两个计数器包括错误，即使ICMP数据包具有无效类型，这些计数器也会增加。ICMP输出路径会检查原始套接字的头部，因此即使IP头部是由用户空间程序构造的，IcmpOutMsgs仍然会被更新。
* ICMP命名类型

| 这些计数器包括大多数常见的ICMP类型，具体如下：
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

每种ICMP类型都有两个计数器：“In”和“Out”。例如，对于ICMP Echo数据包，它们是IcmpInEchos和IcmpOutEchos。其含义很直接。“In”计数器意味着内核接收到了这样的数据包，“Out”计数器意味着内核发送了这样的数据包。
* ICMP数字类型

它们是IcmpMsgInType[N]和IcmpMsgOutType[N]，[N]表示ICMP类型号。这些计数器跟踪所有种类的ICMP数据包。ICMP类型号的定义可以在 `ICMP参数`_ 文档中找到。
.. _ICMP 参数: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml

例如，如果Linux内核发送一个ICMP Echo数据包，则IcmpMsgOutType8将增加1。如果内核接收到一个ICMP Echo应答数据包，则IcmpMsgInType0将增加1。
* IcmpInCsumErrors

此计数器表示ICMP数据包的校验和错误。内核在更新IcmpInMsgs之后但在更新IcmpMsgInType[N]之前验证校验和。如果数据包的校验和有问题，IcmpInMsgs将被更新，但IcmpMsgInType[N]中的任何一个都不会被更新。
* IcmpInErrors 和 IcmpOutErrors

由 `RFC1213 icmpInErrors`_ 和 `RFC1213 icmpOutErrors`_ 定义。

.. _RFC1213 icmpInErrors: https://tools.ietf.org/html/rfc1213#page-41
.. _RFC1213 icmpOutErrors: https://tools.ietf.org/html/rfc1213#page-43

当ICMP包处理路径中发生错误时，这两个计数器会被更新。接收包路径使用 IcmpInErrors，而发送包路径则使用 IcmpOutErrors。当 IcmpInCsumErrors 增加时，IcmpInErrors 也会随之增加。
ICMP计数器之间的关系
-------------------------
IcmpMsgOutType[N]的总和始终等于 IcmpOutMsgs，因为它们同时被更新。IcmpMsgInType[N]加上 IcmpInErrors 的总和应当等于或大于 IcmpInMsgs。当内核接收到一个ICMP包时，它遵循以下逻辑：

1. 增加 IcmpInMsgs
2. 如果有任何错误，则更新 IcmpInErrors 并完成进程
3. 更新 IcmpMsgOutType[N]
4. 根据类型处理包；如果出现任何错误，则更新 IcmpInErrors 并完成进程

因此，如果所有错误都发生在步骤(2)中，那么 IcmpInMsgs 应该等于 IcmpMsgOutType[N]加上 IcmpInErrors 的总和。如果所有错误都发生在步骤(4)中，那么 IcmpInMsgs 应该等于 IcmpMsgOutType[N]的总和。如果错误同时发生在步骤(2)和步骤(4)中，那么 IcmpInMsgs 应该小于 IcmpMsgOutType[N]加上 IcmpInErrors 的总和。
通用TCP计数器
===============
* TcpInSegs

在 `RFC1213 tcpInSegs`_ 中定义。

.. _RFC1213 tcpInSegs: https://tools.ietf.org/html/rfc1213#page-48

这是TCP层接收到的数据包数量。正如RFC1213所提到的，它包括那些因错误而接收到的数据包，例如校验和错误、无效的TCP头部等。仅有一种错误不会被包括在内：即第二层的目标地址不是网卡的第二层地址。这种情况可能发生在数据包为组播或广播包，或者网卡处于混杂模式时。在这种情况下，数据包将被传送到TCP层，但在增加 TcpInSegs 计数之前，TCP层会丢弃这些数据包。TcpInSegs 计数器并不知道GRO的存在。因此，如果有两个数据包通过GRO合并，TcpInSegs 计数器只会增加1。
* TcpOutSegs

在 `RFC1213 tcpOutSegs`_ 中定义。

.. _RFC1213 tcpOutSegs: https://tools.ietf.org/html/rfc1213#page-48

这是TCP层发送的数据包数量。正如RFC1213所指出的，它不包括重传的数据包。但它包括 SYN、ACK 和 RST 数据包。与 TcpInSegs 不同的是，TcpOutSegs 知道GSO的存在，所以如果一个数据包会被GSO分割成2个数据包，TcpOutSegs 将增加2。
* TcpActiveOpens

在 `RFC1213 tcpActiveOpens`_ 中定义。

.. _RFC1213 tcpActiveOpens: https://tools.ietf.org/html/rfc1213#page-47

这意味着TCP层发送了一个 SYN，并进入了 SYN-SENT 状态。每当 TcpActiveOpens 增加1时，TcpOutSegs 应始终增加1。
* TcpPassiveOpens

在 `RFC1213 tcpPassiveOpens`_ 中定义。

.. _RFC1213 tcpPassiveOpens: https://tools.ietf.org/html/rfc1213#page-47

这意味着TCP层接收到了一个 SYN，回复了一个 SYN+ACK，并进入 SYN-RCVD 状态。
* TcpExtTCPRcvCoalesce

当数据包被TCP层接收但未被应用程序读取时，TCP层会尝试将它们合并。此计数器指示在此种情况下有多少数据包被合并。如果启用了GRO，许多数据包将被GRO合并，这些数据包将不会计入 TcpExtTCPRcvCoalesce。
* TcpExtTCPAutoCorking

在发送数据包时，TCP层会尝试将小数据包合并成更大的数据包。此计数器每有一个数据包在这种情况下被合并就会增加1。更多细节请参阅LWN文章：
https://lwn.net/Articles/576263/
* TcpExtTCPOrigDataSent

这个计数器由内核提交f19c29e3e391解释，我将解释内容复制如下::

  TCPOrigDataSent: 发送带有原始数据（不包括重传但包括数据在SYN中的）的数据包数量。这个计数器与 TcpOutSegs 不同，因为 TcpOutSegs 还跟踪纯ACK。TCPOrigDataSent 更有助于追踪TCP重传率。
* TCPSynRetrans

这个计数器由内核提交f19c29e3e391解释，我将解释内容复制如下::

  TCPSynRetrans: SYN 和 SYN/ACK 重传的数量，以分解重传为 SYN、快速重传、超时重传等。
* TCPFastOpenActiveFail

这个计数器由内核提交f19c29e3e391解释，我将解释内容复制如下::

  TCPFastOpenActiveFail: 快速打开（SYN/数据）尝试失败的数量，因为远程端不接受它或尝试超时。
* TcpExtListenOverflows 和 TcpExtListenDrops

当内核接收到客户端的 SYN 包时，如果 TCP 接收队列已满，内核会丢弃该 SYN 并将 TcpExtListenOverflows 的计数加一。同时，内核也会将 TcpExtListenDrops 的计数加一。当一个 TCP 套接字处于监听状态，且内核需要丢弃一个数据包时，内核总会将 TcpExtListenDrops 的计数加一。因此，TcpExtListenOverflows 的增加会导致 TcpExtListenDrops 同步增加，但 TcpExtListenDrops 也可能在 TcpExtListenOverflows 不增加的情况下增加，例如内存分配失败也会导致 TcpExtListenDrops 的增加。
注意：上述解释基于内核版本 4.10 及以上版本，在旧版内核中，当 TCP 接收队列满时，TCP 栈的行为有所不同。在旧版内核中，TCP 栈不会丢弃 SYN 包，而是完成三次握手过程。由于接收队列已满，TCP 栈会将套接字保留在半开连接队列中。在此状态下，TCP 栈会在指数退避定时器触发时发送 SYN+ACK，客户端回复 ACK 后，TCP 栈检查接收队列是否仍然已满；如果不满，则将套接字移至接收队列；如果仍满，则保持套接字在半开连接队列中。下一次客户端回复 ACK 时，该套接字将再次有机会移至接收队列。

TCP 快速打开
=============

* TcpEstabResets

定义于 `RFC1213 tcpEstabResets`_
.. _RFC1213 tcpEstabResets: https://tools.ietf.org/html/rfc1213#page-48

* TcpAttemptFails

定义于 `RFC1213 tcpAttemptFails`_
.. _RFC1213 tcpAttemptFails: https://tools.ietf.org/html/rfc1213#page-48

* TcpOutRsts

定义于 `RFC1213 tcpOutRsts`_。RFC 中说明此计数表示“包含 RST 标志位的发送段”，但在 Linux 内核中，此计数表示内核尝试发送的段数。发送过程中可能会因某些错误（如内存分配失败）而失败。
.. _RFC1213 tcpOutRsts: https://tools.ietf.org/html/rfc1213#page-52

* TcpExtTCPSpuriousRtxHostQueues

当 TCP 栈想要重传一个数据包时，发现该数据包在网络中并未丢失，但尚未发送出去，TCP 栈会放弃重传并更新此计数。这可能发生在数据包在排队调度器或驱动程序队列中停留时间过长的情况下。

* TcpEstabResets

套接字在建立或关闭等待状态下接收到 RST 包。

* TcpExtTCPKeepAlive

此计数表示发送了多少个保活探测包。默认情况下保活功能不会启用。用户空间程序可以通过设置 SO_KEEPALIVE 套接字选项来启用它。

* TcpExtTCPSpuriousRTOs

由 `F-RTO`_ 算法检测到的虚假重传超时。
_F-RTO: https://tools.ietf.org/html/rfc5682

TCP 快速路径
=============
当内核接收到一个 TCP 数据包时，它有两种处理该数据包的路径：一种是快速路径，另一种是慢速路径。内核代码中的注释很好地解释了这两种路径，我将其摘录如下：

  它分为快速路径和慢速路径。当以下任一条件满足时，禁用快速路径：
  - 我们宣布了一个零窗口大小
  - 零窗口探测仅在慢速路径中正确处理
  - 接收到乱序的数据段
  - 预期有紧急数据
  - 没有足够的缓冲区空间
  - 收到意外的 TCP 标志/窗口值/头长度（通过检查 TCP 头部与预设标志来检测）
  - 双向发送数据。快速路径仅支持纯发送方或纯接收方（这意味着序列号或确认值必须保持不变）
  - 收到意外的 TCP 选项
除非满足上述任何条件，否则内核将尝试使用快速路径。如果数据包乱序，内核将在慢速路径中处理它们，这意味着性能可能不是很好。如果使用“延迟确认”，内核也会进入慢速路径，因为使用“延迟确认”时，数据会在两个方向上发送。当未使用 TCP 窗口缩放选项时，连接进入已建立状态后，内核将尝试立即启用快速路径；但如果使用了 TCP 窗口缩放选项，则内核会首先禁用快速路径，并在接收到数据包后尝试启用。
* TcpExtTCPPureAcks 和 TcpExtTCPHPAcks

如果一个数据包设置了 ACK 标志且没有携带数据，则这是一个纯 ACK 数据包。如果内核在快速路径中处理它，TcpExtTCPHPAcks 将增加 1；如果内核在慢速路径中处理它，TcpExtTCPPureAcks 将增加 1。
* TcpExtTCPHPHits

如果一个 TCP 数据包携带数据（意味着这不是一个纯 ACK 数据包），并且此数据包在快速路径中处理，TcpExtTCPHPHits 将增加 1。
TCP 中断
=========
* TcpExtTCPAbortOnData

这表示 TCP 层中有正在传输的数据，但需要关闭连接。因此，TCP 层向另一端发送 RST，表明连接无法优雅地关闭。要增加这个计数器的一个简单方法是使用 SO_LINGER 选项。请参阅 `socket 手册页`_ 的 SO_LINGER 部分：

.. _socket 手册页: http://man7.org/linux/man-pages/man7/socket.7.html

默认情况下，当应用程序关闭一个连接时，close 函数将立即返回，而内核将尝试异步发送正在进行传输的数据。如果你使用 SO_LINGER 选项，设置 l_onoff 为 1 并且 l_linger 为一个正数，close 函数不会立即返回，而是等待正在进行传输的数据被另一端确认，最大等待时间为 l_linger 秒。如果设置 l_onoff 为 1 并且 l_linger 为 0，则当应用程序关闭连接时，内核将立即发送 RST 并增加 TcpExtTCPAbortOnData 计数器。
* TcpExtTCPAbortOnClose

此计数器表示应用程序想要关闭 TCP 连接时，在 TCP 层中有未读取的数据。在这种情况下，内核将向 TCP 连接的另一端发送 RST。
* TcpExtTCPAbortOnMemory

当应用程序关闭 TCP 连接时，内核仍然需要跟踪该连接，以便完成 TCP 断开过程。例如，应用程序调用套接字的 close 方法，内核向连接的另一端发送 FIN，然后应用程序不再与套接字相关联，但内核需要保留该套接字，该套接字成为孤儿套接字。内核等待另一端的回复，并最终进入 TIME_WAIT 状态。当内核没有足够的内存来保留孤儿套接字时，内核将向另一端发送 RST 并删除该套接字，在这种情况下，内核将 TcpExtTCPAbortOnMemory 增加 1。以下两种情况会触发 TcpExtTCPAbortOnMemory：

1. TCP 协议使用的内存高于 tcp_mem 的第三个值。请参考 `TCP 手册页`_ 的 tcp_mem 部分：

.. _TCP 手册页: http://man7.org/linux/man-pages/man7/tcp.7.html

2. 孤儿套接字的数量高于 net.ipv4.tcp_max_orphans
* TcpExtTCPAbortOnTimeout

当任何一个 TCP 定时器超时时，此计数器将增加。在这种情况下，内核不会发送 RST，只是放弃连接。
* TcpExtTCPAbortOnLinger

当一个TCP连接进入FIN_WAIT_2状态时，内核可以选择不等待来自对端的FIN包，而是发送一个RST并立即删除套接字。这不是Linux内核TCP堆栈的默认行为。通过配置TCP_LINGER2套接字选项，可以让内核遵循这种行为。

* TcpExtTCPAbortFailed

当满足`RFC2525第2.17节`_的要求时，内核TCP层将发送RST。如果在此过程中发生内部错误，TcpExtTCPAbortFailed计数器将会增加。
.. _RFC2525第2.17节: https://tools.ietf.org/html/rfc2525#page-50

TCP混合慢启动
=====================

混合慢启动算法是对传统TCP拥塞窗口慢启动算法的一种增强。它利用两个信息来检测是否接近TCP路径的最大带宽：确认（ACK）序列长度和数据包延迟的增加。详细信息请参阅`混合慢启动论文`_。一旦ACK序列长度或数据包延迟达到特定阈值，拥塞控制算法就会进入避免拥塞状态。截至版本4.20，有两个拥塞控制算法使用了混合慢启动：分别是cubic（默认的拥塞控制算法）和cdg。有四个SNMP计数器与混合慢启动算法相关联。
.. _混合慢启动论文: https://pdfs.semanticscholar.org/25e9/ef3f03315782c7f1cbcd31b587857adae7d1.pdf

* TcpExtTCPHystartTrainDetect

检测到ACK序列长度阈值的次数。

* TcpExtTCPHystartTrainCwnd

由ACK序列长度检测到的拥塞窗口（CWND）之和。将此值除以TcpExtTCPHystartTrainDetect得到由ACK序列长度检测到的平均CWND。

* TcpExtTCPHystartDelayDetect

检测到数据包延迟阈值的次数。

* TcpExtTCPHystartDelayCwnd

由数据包延迟检测到的拥塞窗口（CWND）之和。将此值除以TcpExtTCPHystartDelayDetect得到由数据包延迟检测到的平均CWND。

TCP重传与拥塞控制
=========================================

TCP协议有两种重传机制：SACK和快速恢复。这两种机制是互斥的。当启用SACK时，内核TCP堆栈会使用SACK；否则，内核会使用快速恢复。SACK是一种TCP选项，定义于`RFC2018`_中；而快速恢复则定义于`RFC6582`_中，通常也被称为“Reno”算法。
TCP拥塞控制是一个庞大且复杂的主题。为了理解相关的SNMP计数器，我们需要了解拥塞控制状态机的状态。共有5种状态：开放（Open）、无序（Disorder）、清除（CWR）、恢复（Recovery）和丢失（Loss）。关于这些状态的详细信息，请参考以下文档的第5页和第6页：
https://pdfs.semanticscholar.org/0e9c/968d09ab2e53e24c4dca5b2d67c7f7140f8e.pdf

.. _RFC2018: https://tools.ietf.org/html/rfc2018
.. _RFC6582: https://tools.ietf.org/html/rfc6582

* TcpExtTCPRenoRecovery 和 TcpExtTCPSackRecovery

当拥塞控制进入恢复（Recovery）状态时，如果使用了SACK，则TcpExtTCPSackRecovery增加1；如果不使用SACK，则TcpExtTCPRenoRecovery增加1。这两个计数器意味着TCP堆栈开始重新传输丢失的数据包。

* TcpExtTCPSACKReneging

一个被SACK确认过的数据包被接收方丢弃，因此发送方需要重新传输该数据包。在这种情况下，发送方将TcpExtTCPSACKReneging增加1。接收方可以丢弃已经被SACK确认的数据包，尽管这并不常见，但TCP协议允许这种情况的发生。发送方实际上并不知道接收方发生了什么情况。发送方只是等待该数据包的重传超时时间（RTO）到期，然后假设该数据包已被接收方丢弃。

* TcpExtTCPRenoReorder

通过快速恢复检测到乱序的数据包。仅在禁用SACK的情况下使用。快速恢复算法通过重复的确认（ACK）数量来检测乱序。例如，如果触发了重传，并且原始的重传数据包没有丢失，只是顺序错乱，接收方会多次确认：一次针对重传的数据包，另一次针对原本顺序错乱的数据包的到来。因此，发送方会发现比预期更多的ACK，从而得知发生了乱序的情况。
* TcpExtTCPTSReorder

当填充了一个空洞时检测到重排序的报文。例如，假设发送方发送了报文1、2、3、4、5，接收顺序为1、2、4、5、3。当发送方收到报文3的确认（这将填充空洞）时，以下两种情况会让TcpExtTCPTSReorder增加1：1) 如果报文3尚未重新传输。2) 如果报文3已重新传输，但报文3的确认的时间戳早于重新传输的时间戳。
* TcpExtTCPSACKReorder

通过SACK检测到的重排序报文。SACK有两种方法来检测重排序：1) 发送方收到了DSACK。这意味着发送方发送了同一个报文多次以上。唯一的原因是发送方认为一个乱序的报文丢失了，所以再次发送该报文。2) 假设发送方发送了报文1、2、3、4、5，并且已经收到了报文2和5的SACK，现在发送方又收到了报文4的SACK，而且发送方尚未重新传输此报文，发送方就能知道报文4是乱序的。内核中的TCP堆栈在这两种情况下都会增加TcpExtTCPSACKReorder计数。
* TcpExtTCPSlowStartRetrans

TCP堆栈想要重新传输一个报文，并且拥塞控制状态为'Loss'。
* TcpExtTCPFastRetrans

TCP堆栈想要重新传输一个报文，并且拥塞控制状态不是'Loss'。
* TcpExtTCPLostRetransmit

一个SACK指出一个重新传输的报文再次丢失。
* TcpExtTCPRetransFail

TCP堆栈尝试将一个重新传输的报文传递给下层，但是下层返回了一个错误。
* TcpExtTCPSynRetrans

TCP堆栈重新传输一个SYN报文。
DSACK
=====
DSACK在`RFC2883`_中定义。接收方使用DSACK向发送方报告重复的报文。有两种类型的重复：1) 已经被确认过的报文是重复的。2) 乱序的报文是重复的。TCP堆栈在这两方面（接收方和发送方）都统计这两种类型的重复。
* TcpExtTCPDSACKOldSent

TCP堆栈接收到一个已经被确认的重复报文，因此它向发送方发送一个DSACK。
* TcpExtTCPDSACKOfoSent

TCP堆栈接收到一个乱序的重复报文，因此它向发送方发送一个DSACK。
.. _RFC2883 : https://tools.ietf.org/html/rfc2883
* TcpExtTCPDSACKRecv

TCP 栈接收到一个 DSACK，这表明已接收到了一个被确认的重复数据包。
* TcpExtTCPDSACKOfoRecv

TCP 栈接收到一个 DSACK，这表明已接收到了一个次序错乱的重复数据包。

### 无效的 SACK 和 DSACK
当一个 SACK（或 DSACK）块无效时，相应的计数器将被更新。验证方法基于 SACK 块的起始/结束序列号。更多细节，请参考内核源代码中 `tcp_is_sackblock_valid` 函数的注释。一个 SACK 选项最多可以包含 4 个块，它们分别进行检查。例如，如果一个 SACK 中有 3 个块无效，则相应的计数器会被更新 3 次。提交 `18f02545a9a1`（“[TCP] MIB: 添加丢弃的 SACK 块的计数器”）的注释中有额外的解释：

* TcpExtTCPSACKDiscard

此计数器指示有多少 SACK 块是无效的。如果无效的 SACK 块是由 ACK 记录引起的，TCP 栈只会忽略它，并不会更新这个计数器。
* TcpExtTCPDSACKIgnoredOld 和 TcpExtTCPDSACKIgnoredNoUndo

当一个 DSACK 块无效时，其中一个计数器将被更新。哪个计数器被更新取决于 TCP 套接字的 `undo_marker` 标志。如果 `undo_marker` 未设置，TCP 栈不太可能重新传输任何数据包，而我们仍然接收到一个无效的 DSACK 块，原因可能是该数据包在网络中间被重复。在这种情况下，`TcpExtTCPDSACKIgnoredNoUndo` 将被更新。如果 `undo_marker` 已设置，`TcpExtTCPDSACKIgnoredOld` 将被更新。从其名称中可以推断，它可能是一个旧的数据包。

### SACK 移位
Linux 网络栈在 `sk_buff` 结构（简称 skb）中存储数据。如果一个 SACK 块跨越多个 skb，TCP 栈会尝试重新排列这些 skb 中的数据。例如，如果一个 SACK 块确认了序列号 10 到 15 的数据，skb1 包含序列号 10 到 13 的数据，skb2 包含序列号 14 到 20 的数据。那么 skb2 中序列号为 14 和 15 的数据将被移动到 skb1。这种操作称为“移位”。如果一个 SACK 块确认了序列号 10 到 20 的数据，skb1 包含序列号 10 到 13 的数据，skb2 包含序列号 14 到 20 的数据。那么 skb2 中的所有数据将被移动到 skb1，并且 skb2 将被丢弃，这种操作称为“合并”。

* TcpExtTCPSackShifted

一个 skb 被移位。

* TcpExtTCPSackMerged

一个 skb 被合并。

* TcpExtTCPSackShiftFallback

一个 skb 应该被移位或合并，但由于某些原因 TCP 栈没有执行该操作。

### TCP 次序错乱
* TcpExtTCPOFOQueue

TCP 层接收到一个次序错乱的数据包，并有足够的内存来将其排队。
* TcpExtTCPOFODrop

TCP 层接收到一个次序错乱的数据包，但没有足够的内存，因此丢弃了它。这样的数据包不会计入 `TcpExtTCPOFOQueue`。
* TcpExtTCPOFOMerge

接收到的次序错乱的数据包与前一个数据包有重叠部分。重叠部分将被丢弃。所有 `TcpExtTCPOFOMerge` 数据包也会计入 `TcpExtTCPOFOQueue`。

### TCP PAWS
PAWS（Protection Against Wrapped Sequence numbers，防止序列号回绕保护）是一种用于丢弃旧数据包的算法。它依赖于 TCP 时间戳。更多详细信息，请参阅 `时间戳 wiki`_ 和 `PAWS 的 RFC`_。
### PAWS 的 RFC：https://tools.ietf.org/html/rfc1323#page-17
### 时间戳 维基百科：https://en.wikipedia.org/wiki/Transmission_Control_Protocol#TCP_timestamps

* TcpExtPAWSActive

在 Syn-Sent 状态下，数据包被 PAWS（保护防止序列号回绕）丢弃。
* TcpExtPAWSEstab

在除 Syn-Sent 之外的任何状态下，数据包被 PAWS 丢弃。

#### TCP ACK 跳过
在某些情况下，内核会避免过于频繁地发送重复的 ACK。更多细节请参阅 `sysctl 文档`_ 中的 tcp_invalid_ratelimit 部分。当内核决定根据 tcp_invalid_ratelimit 跳过一个 ACK 时，内核会更新以下计数器之一来指示在何种场景下跳过了 ACK。只有当接收到的数据包是 SYN 数据包或没有携带数据时，才会跳过 ACK。
.. _sysctl 文档: https://www.kernel.org/doc/Documentation/networking/ip-sysctl.rst

* TcpExtTCPACKSkippedSynRecv

在 Syn-Recv 状态下跳过的 ACK。Syn-Recv 状态意味着 TCP 堆栈接收到了一个 SYN 并回复了 SYN+ACK。现在 TCP 堆栈正在等待 ACK。通常情况下，TCP 堆栈不需要在 Syn-Recv 状态下发送 ACK。但在某些情况下，TCP 堆栈需要发送 ACK。例如，TCP 堆栈反复接收到同一个 SYN 数据包、接收到的数据包未通过 PAWS 检查，或者接收到的数据包序列号超出窗口范围。在这种情况下，TCP 堆栈需要发送 ACK。如果 ACK 发送频率高于 tcp_invalid_ratelimit 允许的频率，TCP 堆栈将跳过发送 ACK，并增加 TcpExtTCPACKSkippedSynRecv 计数。
* TcpExtTCPACKSkippedPAWS

由于 PAWS（保护防止序列号回绕）检查失败而跳过的 ACK。如果 PAWS 检查在 Syn-Recv、Fin-Wait-2 或 Time-Wait 状态下失败，则跳过的 ACK 将计入 TcpExtTCPACKSkippedSynRecv、TcpExtTCPACKSkippedFinWait2 或 TcpExtTCPACKSkippedTimeWait。在所有其他状态下，跳过的 ACK 将计入 TcpExtTCPACKSkippedPAWS。
* TcpExtTCPACKSkippedSeq

序列号超出窗口范围，时间戳通过了 PAWS 检查，并且 TCP 状态不是 Syn-Recv、Fin-Wait-2 和 Time-Wait。
* TcpExtTCPACKSkippedFinWait2

在 Fin-Wait-2 状态下跳过的 ACK，原因可能是 PAWS 检查失败或接收到的序列号超出窗口范围。
* TcpExtTCPACKSkippedTimeWait

在 Time-Wait 状态下跳过的 ACK，原因可能是 PAWS 检查失败或接收到的序列号超出窗口范围。
* TcpExtTCPACKSkippedChallenge

如果 ACK 是挑战 ACK，则跳过 ACK。RFC 5961 定义了三种类型的挑战 ACK，请参考 `RFC 5961 第 3.2 节`_、`RFC 5961 第 4.2 节`_ 和 `RFC 5961 第 5.2 节`_。除了这三种情况外，在某些 TCP 状态下，Linux TCP 堆栈也会发送挑战 ACK，如果 ACK 号码位于第一个未确认号码之前（比 `RFC 5961 第 5.2 节`_ 更严格）。
.. _RFC 5961 第 3.2 节: https://tools.ietf.org/html/rfc5961#page-7
.. _RFC 5961 第 4.2 节: https://tools.ietf.org/html/rfc5961#page-9
.. _RFC 5961 第 5.2 节: https://tools.ietf.org/html/rfc5961#page-11

#### TCP 接收窗口
* TcpExtTCPWantZeroWindowAdv

根据当前内存使用情况，TCP 堆栈尝试将接收窗口设置为零。但接收窗口仍可能是一个非零值。例如，如果前一个窗口大小为 10，而 TCP 堆栈接收到 3 字节数据，即使根据内存使用计算出的窗口大小为零，当前窗口大小仍将为 7。
* TcpExtTCPToZeroWindowAdv

TCP接收窗口从非零值设置为零。

* TcpExtTCPFromZeroWindowAdv

TCP接收窗口从零设置为非零值。

延迟确认（Delayed ACK）
======================
TCP 延迟确认是一种技术，用于减少网络中的数据包数量。更多详情，请参阅
[延迟确认维基页面]_

.. _延迟确认维基页面: https://en.wikipedia.org/wiki/TCP_delayed_acknowledgment

* TcpExtDelayedACKs

延迟确认定时器过期。TCP 栈将发送纯确认（ACK）数据包并退出延迟确认模式。
* TcpExtDelayedACKLocked

延迟确认定时器过期，但由于用户空间程序锁定了套接字，TCP 栈无法立即发送确认（ACK）。TCP 栈将在稍后（当用户空间程序解锁套接字后）发送纯确认（ACK）数据包。当 TCP 栈稍后发送纯确认（ACK）时，它还会更新 TcpExtDelayedACKs 计数器并退出延迟确认模式。
* TcpExtDelayedACKLost

当 TCP 栈收到已被确认的数据包时，此计数器会被更新。延迟确认丢失可能会导致这个问题，但也可能是由其他原因触发的，例如网络中数据包重复。

尾部丢失探测（TLP）
====================
TLP 是一种用于检测 TCP 数据包丢失的算法。更多详情，请参阅
[TLP 论文]_

.. _TLP 论文: https://tools.ietf.org/html/draft-dukkipati-tcpm-tcp-loss-probe-01

* TcpExtTCPLossProbes

发送了一个 TLP 探测数据包。
* TcpExtTCPLossProbeRecovery

通过 TLP 检测到并恢复了数据包丢失。

TCP 快速打开描述
=================
TCP 快速打开是一项技术，允许在完成三路握手之前开始数据传输。请参考
[TCP 快速打开维基页面]_ 了解一般性描述。

.. _TCP 快速打开维基页面: https://en.wikipedia.org/wiki/TCP_Fast_Open

* TcpExtTCPFastOpenActive

当 TCP 栈在 SYN-SENT 状态下接收到一个确认（ACK）数据包，并且该确认数据包确认了 SYN 数据包中的数据时，TCP 栈理解 TFO 密钥已被另一端接受，然后更新此计数器。
* TcpExtTCPFastOpenActiveFail

此计数器表示TCP栈发起了TCP快速打开，但失败了。此计数器会在以下三种情况下更新：(1) 对方未确认SYN数据包中的数据。(2) 带有TFO Cookie的SYN数据包至少超时一次。(3) 三次握手之后，重传超时次数达到net.ipv4.tcp_retries1次，因为某些中间盒可能会在握手后屏蔽快速打开。
* TcpExtTCPFastOpenPassive

此计数器表示TCP栈接受快速打开请求的次数。
* TcpExtTCPFastOpenPassiveFail

此计数器表示TCP栈拒绝快速打开请求的次数。可能是由于TFO Cookie无效或TCP栈在创建套接字过程中发现错误所致。
* TcpExtTCPFastOpenListenOverflow

当待处理的快速打开请求数量大于fastopenq->max_qlen时，TCP栈将拒绝快速打开请求并更新此计数器。当此计数器被更新时，TCP栈不会更新TcpExtTCPFastOpenPassive或TcpExtTCPFastOpenPassiveFail。fastopenq->max_qlen由TCP_FASTOPEN套接字操作设置，并且不能大于net.core.somaxconn。例如：

```c
setsockopt(sfd, SOL_TCP, TCP_FASTOPEN, &qlen, sizeof(qlen));
```
* TcpExtTCPFastOpenCookieReqd

此计数器表示客户端想要请求TFO Cookie的次数。

### SYN Cookies
SYN Cookies用于缓解SYN泛洪攻击，详情请参阅[SYN Cookies维基](https://en.wikipedia.org/wiki/SYN_cookies)

* TcpExtSyncookiesSent

表示发送了多少个SYN Cookie。
* TcpExtSyncookiesRecv

TCP栈接收了多少个SYN Cookie的回复数据包。
* TcpExtSyncookiesFailed

从SYN Cookie解码出的MSS无效。当此计数器被更新时，接收到的数据包不会被视为SYN Cookie，并且不会更新TcpExtSyncookiesRecv计数器。

### Challenge ACK

有关Challenge ACK的详细信息，请参阅TcpExtTCPACKSkippedChallenge的解释。
* TcpExtTCPChallengeACK

发送的挑战确认数据包的数量。
* TcpExtTCPSYNChallenge

响应 SYN 数据包发送的挑战确认的数量。更新此计数器后，TCP 堆栈可能会发送一个挑战 ACK 并更新 TcpExtTCPChallengeACK 计数器，或者也可能跳过发送挑战并更新 TcpExtTCPACKSkippedChallenge 计数器。

=====

内存压力下修剪
当套接字受到内存压力时，TCP 堆栈会尝试从接收队列和乱序队列中回收内存。一种回收方法是“压缩”，即分配一个大的 skb（socket buffer），将连续的 skb 复制到这个大的 skb 中，并释放这些连续的 skb。

* TcpExtPruneCalled

TCP 堆栈尝试为一个套接字回收内存。更新此计数器后，TCP 堆栈将尝试压缩乱序队列和接收队列。如果内存仍然不足，TCP 堆栈将尝试从乱序队列中丢弃数据包（并更新 TcpExtOfoPruned 计数器）。

* TcpExtOfoPruned

TCP 堆栈试图从乱序队列中丢弃数据包。

* TcpExtRcvPruned

在进行“压缩”和从乱序队列中丢弃数据包之后，如果实际使用的内存仍然大于最大允许内存，则更新此计数器。这意味着“修剪”失败了。

* TcpExtTCPRcvCollapsed

此计数器指示在“压缩”过程中释放了多少个 skb。

示例
=====

Ping 测试
---------
针对公共 DNS 服务器 8.8.8.8 运行 ping 命令：

```
nstatuser@nstat-a:~$ ping 8.8.8.8 -c 1
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=119 time=17.8 ms

--- 8.8.8.8 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 17.875/17.875/17.875/0.000 ms
```

nstat 的结果如下：

```
nstatuser@nstat-a:~$ nstat
#kernel
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

Linux 服务器发送了一个 ICMP Echo 数据包，因此 IpOutRequests、IcmpOutMsgs、IcmpOutEchos 和 IcmpMsgOutType8 都增加了 1。服务器收到了来自 8.8.8.8 的 ICMP Echo 回复，因此 IpInReceives、IcmpInMsgs、IcmpInEchoReps 和 IcmpMsgInType0 都增加了 1。ICMP Echo 回复通过 IP 层传递到了 ICMP 层，因此 IpInDelivers 增加了 1。默认的 ping 数据大小为 48 字节，所以一个 ICMP Echo 数据包及其对应的 Echo 回复数据包由以下部分构成：

* 14 字节 MAC 头部
* 20 字节 IP 头部
* 16 字节 ICMP 头部
* 48 字节 数据（ping 命令的默认值）

因此，IpExtInOctets 和 IpExtOutOctets 为 20 + 16 + 48 = 84 字节。

TCP 三次握手
--------------
在服务器端，我们运行：

```
nstatuser@nstat-b:~$ nc -lknv 0.0.0.0 9000
Listening on [0.0.0.0] (family 0, port 9000)
```

在客户端，我们运行：

```
nstatuser@nstat-a:~$ nc -nv 192.168.122.251 9000
Connection to 192.168.122.251 9000 port [tcp/*] succeeded!
```

服务器监听 TCP 端口 9000，客户端连接到它，它们完成了三次握手。
在服务器端，我们可以找到以下 nstat 输出：

```
nstatuser@nstat-b:~$ nstat | grep -i tcp
TcpPassiveOpens                 1                  0.0
TcpInSegs                       2                  0.0
TcpOutSegs                      1                  0.0
TcpExtTCPPureAcks               1                  0.0
```

在客户端，我们可以找到以下 nstat 输出：

```
nstatuser@nstat-a:~$ nstat | grep -i tcp
TcpActiveOpens                  1                  0.0
TcpInSegs                       1                  0.0
TcpOutSegs                      2                  0.0
```

当服务器收到第一个 SYN 数据包时，它回复了一个 SYN+ACK，并进入了 SYN-RCVD 状态，因此 TcpPassiveOpens 增加了 1。服务器收到了 SYN 数据包，发送了 SYN+ACK，收到了 ACK，所以服务器发送了 1 个数据包，接收了 2 个数据包，TcpInSegs 增加了 2，TcpOutSegs 增加了 1。三次握手中的最后一个 ACK 是一个不含数据的纯 ACK，因此 TcpExtTCPPureAcks 增加了 1。

当客户端发送 SYN 数据包时，客户端进入了 SYN-SENT 状态，因此 TcpActiveOpens 增加了 1。客户端发送了 SYN 数据包，接收了 SYN+ACK，发送了 ACK，因此客户端发送了 2 个数据包，接收了 1 个数据包，TcpInSegs 增加了 1，TcpOutSegs 增加了 2。
TCP 正常流量
------------------
在服务器上运行 `nc` ：

  nstatuser@nstat-b:~$ nc -lkv 0.0.0.0 9000
  监听中 [0.0.0.0] (家族 0, 端口 9000)

在客户端运行 `nc` ：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  连接到 nstat-b 9000 端口 [tcp/*] 成功！

在 `nc` 客户端输入字符串（例如 'hello'）：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  连接到 nstat-b 9000 端口 [tcp/*] 成功！
  hello

客户端侧 `nstat` 输出：

  nstatuser@nstat-a:~$ nstat
  #内核
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

服务器侧 `nstat` 输出：

  nstatuser@nstat-b:~$ nstat
  #内核
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  IpExtInOctets                   58                 0.0
  IpExtOutOctets                  52                 0.0
  IpExtInNoECTPkts                1                  0.0

再次在客户端侧的 `nc` 输入字符串（例如 'world'）：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  连接到 nstat-b 9000 端口 [tcp/*] 成功！
  hello
  world

客户端侧 `nstat` 输出：

  nstatuser@nstat-a:~$ nstat
  #内核
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

服务器侧 `nstat` 输出：

  nstatuser@nstat-b:~$ nstat
  #内核
  IpInReceives                    1                  0.0
  IpInDelivers                    1                  0.0
  IpOutRequests                   1                  0.0
  TcpInSegs                       1                  0.0
  TcpOutSegs                      1                  0.0
  TcpExtTCPHPHits                 1                  0.0
  IpExtInOctets                   58                 0.0
  IpExtOutOctets                  52                 0.0
  IpExtInNoECTPkts                1                  0.0

比较第一次客户端侧的 `nstat` 和第二次客户端侧的 `nstat`，
我们可以发现一个差异：第一次有 'TcpExtTCPPureAcks'，
而第二次有 'TcpExtTCPHPAcks'。第一次服务器侧
的 `nstat` 和第二次服务器侧的 `nstat` 也有差异：
第二次服务器侧的 `nstat` 有一个 TcpExtTCPHPHits，
但第一次没有。网络流量模式完全相同：客户端发送了一个数据包给服务器，服务器回复了一个确认。
但是内核以不同的方式处理它们。当不使用 TCP 窗口缩放选项时，
内核会在连接进入已建立状态时立即尝试启用快速路径，
但如果使用了 TCP 窗口缩放选项，则内核会先禁用快速路径，
并在接收到数据包后尝试启用它。我们可以使用 'ss' 命令来验证是否使用了窗口缩放选项。
例如，在服务器或客户端上运行以下命令：

  nstatuser@nstat-a:~$ ss -o state established -i '( dport = :9000 or sport = :9000 )
  Netid    Recv-Q     Send-Q            本地地址:端口             对等地址:端口
  tcp      0          0               192.168.122.250:40654         192.168.122.251:9000
             ts sack cubic wscale:7,7 rto:204 rtt:0.98/0.49 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:10 bytes_acked:1 segs_out:2 segs_in:1 send 118.2Mbps lastsnd:46572 lastrcv:46572 lastack:46572 pacing_rate 236.4Mbps rcv_space:29200 rcv_ssthresh:29200 minrtt:0.98

'wscale:7,7' 表示服务器和客户端都将窗口缩放选项设置为 7。
现在我们可以解释测试中的 `nstat` 输出：

在客户端侧的第一个 `nstat` 输出中，客户端发送了一个数据包，服务器回复了一个确认。
当内核处理这个确认时，快速路径未被启用，因此确认被计入 'TcpExtTCPPureAcks' 中。
在客户端侧的第二个 `nstat` 输出中，客户端再次发送了一个数据包，并从服务器收到了另一个确认，
这次快速路径被启用了，且确认符合快速路径的条件，因此它通过快速路径处理，所以这个确认被计入 TcpExtTCPHPAcks。
在服务器侧的第一个 `nstat` 输出中，快速路径未被启用，因此没有 'TcpExtTCPHPHits'。
在服务器侧的第二个 `nstat` 输出中，快速路径被启用了，且从客户端接收的数据包符合快速路径的条件，因此它被计入 'TcpExtTCPHPHits'。

TcpExtTCPAbortOnClose
---------------------
在服务器侧，我们运行以下 Python 脚本：

  import socket
  import time

  port = 9000

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('0.0.0.0', port))
  s.listen(1)
  sock, addr = s.accept()
  while True:
      time.sleep(9999999)

此 Python 脚本监听 9000 端口，但不读取任何来自连接的内容。
在客户端侧，我们通过 `nc` 发送字符串 "hello" ：

  nstatuser@nstat-a:~$ echo "hello" | nc nstat-b 9000

然后回到服务器侧，服务器已经接收到了 "hello" 数据包，TCP 层也确认了该数据包，
但应用程序尚未读取它。我们按下 Ctrl-C 来终止服务器脚本。
然后我们可以发现服务器侧的 TcpExtTCPAbortOnClose 增加了 1 ：

  nstatuser@nstat-b:~$ nstat | grep -i abort
  TcpExtTCPAbortOnClose           1                  0.0

如果我们在服务器侧运行 tcpdump，我们会发现按下 Ctrl-C 后服务器发送了一个 RST。

TcpExtTCPAbortOnMemory 和 TcpExtTCPAbortOnTimeout
---------------------------------------------------
下面是一个示例，让孤儿套接字的数量超过 net.ipv4.tcp_max_orphans 的值。
在客户端上将 tcp_max_orphans 设置为一个较小的值：

  sudo bash -c "echo 10 > /proc/sys/net/ipv4/tcp_max_orphans"

客户端代码（与服务器建立 64 个连接）：

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

在客户端上按下 Ctrl-C，停止 client_orphan.py
检查客户端上的 TcpExtTCPAbortOnMemory ：

  nstatuser@nstat-a:~$ nstat | grep -i abort
  TcpExtTCPAbortOnMemory          54                 0.0

检查客户端上的孤儿套接字数量：

  nstatuser@nstat-a:~$ ss -s
  总计: 131 (内核 0)
  TCP:   14 (已建立 1, 已关闭 0, 孤儿 10, 收到 SYN 0, TIME_WAIT 0/0)，端口 0

  传输 总数     IP        IPv6
  *         0         -         -
  RAW       1         0         1
  UDP       1         1         0
  TCP       14        13        1
  INET      16        14        2
  FRAG      0         0         0

测试解释：运行 server_orphan.py 和 client_orphan.py 后，
我们在服务器和客户端之间建立了 64 个连接。运行 iptables 命令后，
服务器会丢弃所有来自客户端的数据包。在客户端上按下 Ctrl-C，
客户端系统将尝试关闭这些连接，在它们优雅地关闭之前，
这些连接变成了孤儿套接字。由于服务器的 iptables 阻止了来自客户端的数据包，
服务器不会接收到客户端发来的 FIN，因此客户端上的所有连接都会停留在 FIN_WAIT_1 阶段，
直到超时为止。我们把 10 写入 /proc/sys/net/ipv4/tcp_max_orphans，
所以客户端系统只会保留 10 个孤儿套接字，对于其他孤儿套接字，
客户端系统发送 RST 并删除它们。我们有 64 个连接，因此 'ss -s' 命令显示系统有 10 个孤儿套接字，
而 TcpExtTCPAbortOnMemory 的值为 54。
关于孤儿套接字计数的额外解释：您可以通过`ss -s`命令找到确切的孤儿套接字数量，但是当内核决定是否增加`TcpExtTCPAbortOnMemory`并发送RST时，并不总是检查确切的孤儿套接字数量。为了提高性能，内核首先检查一个近似数量；如果这个近似数量超过了`tcp_max_orphans`，内核会再次检查确切的数量。因此，如果近似数量少于`tcp_max_orphans`，但确切的数量超过了`tcp_max_orphans`，您可能会发现`TcpExtTCPAbortOnMemory`根本没有增加。如果`tcp_max_orphans`足够大，则不会发生这种情况，但如果将其减小到像我们测试中的较小值，您可能会遇到这个问题。因此，在我们的测试中，客户端建立了64个连接，尽管`tcp_max_orphans`设置为10。如果客户端只建立11个连接，我们就无法观察到`TcpExtTCPAbortOnMemory`的变化。
继续之前的测试，我们等待几分钟。由于服务器上的`iptables`阻止了流量，服务器不会收到FIN包，客户端的所有孤儿套接字最终都会在`FIN_WAIT_1`状态下超时。因此，我们等待几分钟后，可以在客户端上找到10次超时：

  nstatuser@nstat-a:~$ nstat | grep -i abort
  TcpExtTCPAbortOnTimeout         10                 0.0

`TcpExtTCPAbortOnLinger`
------------------------
服务器端代码如下：

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

客户端代码如下：

  nstatuser@nstat-a:~$ cat client_linger.py
  import socket
  import struct

  server = 'nstat-b' # 服务器地址
  port = 9000

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 10))
  s.setsockopt(socket.SOL_TCP, socket.TCP_LINGER2, struct.pack('i', -1))
  s.connect((server, port))
  s.close()

在服务器上运行`server_linger.py`：

  nstatuser@nstat-b:~$ python3 server_linger.py

在客户端上运行`client_linger.py`：

  nstatuser@nstat-a:~$ python3 client_linger.py

运行`client_linger.py`后，检查`nstat`的输出：

  nstatuser@nstat-a:~$ nstat | grep -i abort
  TcpExtTCPAbortOnLinger          1                  0.0

`TcpExtTCPRcvCoalesce`
----------------------
在服务器上，我们运行一个监听TCP端口9000但不读取任何数据的程序：

  import socket
  import time
  port = 9000
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.bind(('0.0.0.0', port))
  s.listen(1)
  sock, addr = s.accept()
  while True:
      time.sleep(9999999)

保存上述代码为`server_coalesce.py`，并运行：

  python3 server_coalesce.py

在客户端上，保存以下代码为`client_coalesce.py`：

  import socket
  server = 'nstat-b'
  port = 9000
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((server, port))

运行：

  nstatuser@nstat-a:~$ python3 -i client_coalesce.py

使用`-i`进入交互模式，然后发送一个包：

  >>> s.send(b'foo')
  3

再发送一个包：

  >>> s.send(b'bar')
  3

在服务器上运行`nstat`：

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

客户端发送了两个包，服务器没有读取任何数据。当第二个包到达服务器时，第一个包仍在接收队列中。因此，TCP层合并了这两个包，我们可以看到`TcpExtTCPRcvCoalesce`增加了1。

`TcpExtListenOverflows` 和 `TcpExtListenDrops`
-------------------------------------------
在服务器上运行nc命令，监听端口9000：

  nstatuser@nstat-b:~$ nc -lkv 0.0.0.0 9000
  Listening on [0.0.0.0] (family 0, port 9000)

在客户端的不同终端上运行3个nc命令：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  Connection to nstat-b 9000 port [tcp/*] succeeded!

nc命令仅接受一个连接，且接受队列长度为1。在当前Linux实现中，设置队列长度为n意味着实际队列长度为n+1。现在我们创建3个连接，其中1个被nc接受，2个在等待队列中，因此接受队列已满。
在运行第4个nc之前，我们清理服务器上的`nstat`历史记录：

  nstatuser@nstat-b:~$ nstat -n

在客户端上运行第4个nc：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000

如果nc服务器运行在4.10或更高版本的内核上，您将不会看到“Connection to ... succeeded!”字符串，因为内核会在接受队列满时丢弃SYN包。如果nc客户端运行在旧版内核上，您会看到连接成功，因为内核会完成三次握手并将套接字保留在半开队列中。我在4.15版本的内核上进行了测试。以下是服务器上的`nstat`输出：

  nstatuser@nstat-b:~$ nstat
  #kernel
  IpInReceives                    4                  0.0
  IpInDelivers                    4                  0.0
  TcpInSegs                       4                  0.0
  TcpExtListenOverflows           4                  0.0
  TcpExtListenDrops               4                  0.0
  IpExtInOctets                   240                0.0
  IpExtInNoECTPkts                4                  0.0

`TcpExtListenOverflows`和`TcpExtListenDrops`均为4。如果第4个nc与`nstat`之间的时间更长，`TcpExtListenOverflows`和`TcpExtListenDrops`的值会更大，因为第4个nc的SYN包被丢弃了，客户端正在重试。

`IpInAddrErrors`, `IpExtInNoRoutes` 和 `IpOutNoRoutes`
-------------------------------------------------
服务器A的IP地址：192.168.122.250
服务器B的IP地址：192.168.122.251
在服务器A上准备，添加一条到服务器B的路由：

  $ sudo ip route add 8.8.8.8/32 via 192.168.122.251

在服务器B上准备，禁用所有接口的send_redirects：

  $ sudo sysctl -w net.ipv4.conf.all.send_redirects=0
  $ sudo sysctl -w net.ipv4.conf.ens3.send_redirects=0
  $ sudo sysctl -w net.ipv4.conf.lo.send_redirects=0
  $ sudo sysctl -w net.ipv4.conf.default.send_redirects=0

我们希望让服务器A向8.8.8.8发送一个包，并通过路由将该包路由到服务器B。当服务器B收到这样的包时，它可能会向服务器A发送一个ICMP重定向消息，将send_redirects设置为0将禁用这种行为。
首先，生成`IpInAddrErrors`。在服务器B上，我们禁用IP转发：

  $ sudo sysctl -w net.ipv4.conf.all.forwarding=0

在服务器A上，我们向8.8.8.8发送包：

  $ nc -v 8.8.8.8 53

在服务器B上，我们检查`nstat`的输出：

  $ nstat
  #kernel
  IpInReceives                    3                  0.0
  IpInAddrErrors                  3                  0.0
  IpExtInOctets                   180                0.0
  IpExtInNoECTPkts                3                  0.0

因为我们让服务器A将8.8.8.8路由到服务器B，并在服务器B上禁用了IP转发，服务器A向服务器B发送包，然后服务器B丢弃这些包并增加了`IpInAddrErrors`。由于nc命令如果没有收到SYN+ACK，将会重新发送SYN包，因此我们可以找到多个`IpInAddrErrors`。
其次，生成`IpExtInNoRoutes`。在服务器B上，我们启用IP转发：

  $ sudo sysctl -w net.ipv4.conf.all.forwarding=1

检查服务器B的路由表并删除默认路由：

  $ ip route show
  default via 192.168.122.1 dev ens3 proto static
  192.168.122.0/24 dev ens3 proto kernel scope link src 192.168.122.251
  $ sudo ip route delete default via 192.168.122.1 dev ens3 proto static

在服务器A上，我们再次联系8.8.8.8：

  $ nc -v 8.8.8.8 53
  nc: connect to 8.8.8.8 port 53 (tcp) failed: Network is unreachable

在服务器B上运行`nstat`：

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

我们在服务器B上启用了IP转发，当服务器B收到目的地IP地址为8.8.8.8的包时，服务器B会尝试转发这个包。我们已经删除了默认路由，没有针对8.8.8.8的路由，因此服务器B增加了`IpExtInNoRoutes`并向服务器A发送了“ICMP Destination Unreachable”消息。
最后，生成`IpOutNoRoutes`。在服务器B上运行ping命令：

  $ ping -c 1 8.8.8.8
  connect: Network is unreachable

在服务器B上运行`nstat`：

  $ nstat
  #kernel
  IpOutNoRoutes                   1                  0.0

我们在服务器B上删除了默认路由。服务器B找不到8.8.8.8的路由，因此增加了`IpOutNoRoutes`。

`TcpExtTCPACKSkippedSynRecv`
----------------------------
在这个测试中，我们从客户端向服务器发送3个相同的SYN包。第一个SYN包会让服务器创建一个套接字，将其设置为Syn-Recv状态，并回复SYN/ACK。第二个SYN包会让服务器再次回复SYN/ACK，并记录回复时间（重复ACK回复时间）。第三个SYN包会让服务器检查前一个重复ACK回复时间，并决定跳过重复ACK，然后增加`TcpExtTCPACKSkippedSynRecv`计数器。
运行tcpdump来捕获一个SYN包：

  nstatuser@nstat-a:~$ sudo tcpdump -c 1 -w /tmp/syn.pcap port 9000
  tcpdump: listening on ens3, link-type EN10MB (Ethernet), capture size 262144 bytes

在另一个终端上运行nc命令：

  nstatuser@nstat-a:~$ nc nstat-b 9000

因为nstat-b没有监听端口9000，它应该回复一个RST，并使nc命令立即退出。这足以让tcpdump命令捕获一个SYN包。一个Linux服务器可能使用硬件卸载来进行TCP校验和计算，所以/tmp/syn.pcap中的校验和可能是不正确的。我们调用tcprewrite来修复它：

  nstatuser@nstat-a:~$ tcprewrite --infile=/tmp/syn.pcap --outfile=/tmp/syn_fixcsum.pcap --fixcsum

在nstat-b上，我们运行nc来监听端口9000：

  nstatuser@nstat-b:~$ nc -lkv 9000
  Listening on [0.0.0.0] (family 0, port 9000)

在nstat-a上，我们阻止了来自端口9000的包，否则nstat-a会向nstat-b发送RST：

  nstatuser@nstat-a:~$ sudo iptables -A INPUT -p tcp --sport 9000 -j DROP

向nstat-b发送3个SYN包：

  nstatuser@nstat-a:~$ for i in {1..3}; do sudo tcpreplay -i ens3 /tmp/syn_fixcsum.pcap; done

在nstat-b上检查snmp计数器：

  nstatuser@nstat-b:~$ nstat | grep -i skip
  TcpExtTCPACKSkippedSynRecv      1                  0.0

正如我们所预期的那样，`TcpExtTCPACKSkippedSynRecv`为1。
触发 PAWS，我们可以发送一个旧的 SYN 包。
在 nstat-b 上，让 `nc` 监听 9000 端口：

  nstatuser@nstat-b:~$ nc -lkv 9000
  正在监听 [0.0.0.0]（家族 0，端口 9000）

在 nstat-a 上，运行 `tcpdump` 来捕获一个 SYN 包：

  nstatuser@nstat-a:~$ sudo tcpdump -w /tmp/paws_pre.pcap -c 1 port 9000
  tcpdump：正在监听 ens3，链接类型为 EN10MB（以太网），捕获大小为 262144 字节

在 nstat-a 上，运行 `nc` 作为客户端连接到 nstat-b：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  连接到 nstat-b 的 9000 端口 [tcp/*] 成功！

现在 `tcpdump` 已经捕获了 SYN 包并退出。我们应该修正校验和：

  nstatuser@nstat-a:~$ tcprewrite --infile /tmp/paws_pre.pcap --outfile /tmp/paws.pcap --fixcsum

两次发送 SYN 包：

  nstatuser@nstat-a:~$ for i in {1..2}; do sudo tcpreplay -i ens3 /tmp/paws.pcap; done

在 nstat-b 上，检查 snmp 计数器：

  nstatuser@nstat-b:~$ nstat | grep -i skip
  TcpExtTCPACKSkippedPAWS         1                  0.0

我们通过 `tcpreplay` 发送了两个 SYN 包，这两个包都会使 PAWS 检查失败，nstat-b 对第一个 SYN 发送了一个 ACK，并跳过了第二个 SYN 的 ACK，更新了 `TcpExtTCPACKSkippedPAWS`。

`TcpExtTCPACKSkippedSeq`
------------------------
为了触发 `TcpExtTCPACKSkippedSeq`，我们需要发送具有有效时间戳（以便通过 PAWS 检查）但序列号超出窗口范围的数据包。Linux 的 TCP 栈会避免跳过包含数据的包，因此我们需要一个纯 ACK 包。为了生成这样的包，我们可以创建两个套接字：一个在 9000 端口，另一个在 9001 端口。然后我们捕获 9001 端口上的 ACK 包，更改源/目标端口号以匹配 9000 端口的套接字。这样就可以通过这个包来触发 `TcpExtTCPACKSkippedSeq`。
在 nstat-b 上，打开两个终端，分别监听 9000 端口和 9001 端口：

  nstatuser@nstat-b:~$ nc -lkv 9000
  正在监听 [0.0.0.0]（家族 0，端口 9000）

  nstatuser@nstat-b:~$ nc -lkv 9001
  正在监听 [0.0.0.0]（家族 0，端口 9001）

在 nstat-a 上，运行两个 `nc` 客户端：

  nstatuser@nstat-a:~$ nc -v nstat-b 9000
  连接到 nstat-b 的 9000 端口 [tcp/*] 成功！

  nstatuser@nstat-a:~$ nc -v nstat-b 9001
  连接到 nstat-b 的 9001 端口 [tcp/*] 成功！

在 nstat-a 上，运行 `tcpdump` 来捕获一个 ACK 包：

  nstatuser@nstat-a:~$ sudo tcpdump -w /tmp/seq_pre.pcap -c 1 dst port 9001
  tcpdump：正在监听 ens3，链接类型为 EN10MB（以太网），捕获大小为 262144 字节

在 nstat-b 上，通过 9001 端口的套接字发送一个包。例如，在我们的示例中发送字符串 'foo'：

  nstatuser@nstat-b:~$ nc -lkv 9001
  正在监听 [0.0.0.0]（家族 0，端口 9001）
  收到来自 nstat-a 的 42132 的连接！
  foo

在 nstat-a 上，`tcpdump` 应该已经捕获到了 ACK 包。我们应该检查两个 `nc` 客户端的源端口号：

  nstatuser@nstat-a:~$ ss -ta '( dport = :9000 || dport = :9001 )' | tee
  状态  接收队列  发送队列         本地地址:端口           对等地址:端口
  ESTAB  0        0            192.168.122.250:50208       192.168.122.251:9000
  ESTAB  0        0            192.168.122.250:42132       192.168.122.251:9001

运行 `tcprewrite`，将端口 9001 更改为端口 9000，将端口 42132 更改为端口 50208：

  nstatuser@nstat-a:~$ tcprewrite --infile /tmp/seq_pre.pcap --outfile /tmp/seq.pcap -r 9001:9000 -r 42132:50208 --fixcsum

现在 `/tmp/seq.pcap` 就是我们需要的包。将其发送到 nstat-b：

  nstatuser@nstat-a:~$ for i in {1..2}; do sudo tcpreplay -i ens3 /tmp/seq.pcap; done

在 nstat-b 上检查 `TcpExtTCPACKSkippedSeq`：

  nstatuser@nstat-b:~$ nstat | grep -i skip
  TcpExtTCPACKSkippedSeq          1                  0.0
