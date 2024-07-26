### SPDX 许可证标识符：GPL-2.0

=====================
分段卸载
=====================

#### 引言
本文件描述了Linux网络栈中的一系列技术，以利用各种网卡的分段卸载功能。以下技术将被介绍：
* TCP 分段卸载 - TSO
* UDP 分片卸载 - UFO
* IPIP、SIT、GRE 和 UDP 隧道卸载
* 通用分段卸载 - GSO
* 通用接收卸载 - GRO
* 部分通用分段卸载 - GSO_PARTIAL
* 使用 GSO 的 SCTP 加速 - GSO_BY_FRAGS

#### TCP 分段卸载
TCP 分段允许设备将单个帧分割为多个具有特定数据负载大小（由 skb_shinfo()->gso_size 指定）的帧。当请求 TCP 分段时，skb_shinfo()->gso_type 中应设置 SKB_GSO_TCPV4 或 SKB_GSO_TCPV6 标志，并且 skb_shinfo()->gso_size 应设置为非零值。TCP 分段依赖于部分校验和卸载的支持。因此，如果禁用了给定设备的发送校验和卸载，通常也会禁用 TSO。
为了支持 TCP 分段卸载，需要填充 skbuff 中的网络和传输头偏移量，以便驱动程序能够确定 IP 或 IPv6 头以及 TCP 头的偏移量。此外，由于需要使用 CHECKSUM_PARTIAL，csum_start 也应指向数据包的 TCP 头。
对于 IPv4 分段，我们支持两种类型的 IP ID。默认行为是每段递增 IP ID。如果指定了 GSO 类型 SKB_GSO_TCP_FIXEDID，则不会递增 IP ID，所有分段将使用相同的 IP ID。如果设备设置了 NETIF_F_TSO_MANGLEID，则在执行 TSO 时可以忽略 IP ID，我们将根据驱动程序的偏好，为所有帧递增 IP ID 或将其保持为静态值。

#### UDP 分片卸载
UDP 分片卸载允许设备将超大的 UDP 数据报分割为多个 IPv4 分片。对于 UDP 分片卸载的要求与 TSO 相似，但是分片的 IPv4 ID 不应该递增，因为单个 IPv4 数据报被分片。
UFO 已被废弃：现代内核不再生成 UFO skbs，但仍然可以从 tuntap 等类似设备接收它们。基于 UDP 的隧道协议卸载仍然受支持。

#### IPIP、SIT、GRE、UDP 隧道及远程校验和卸载
除了上述卸载外，一个帧可能还包含额外的头部，如外部隧道。为了处理这种情况，引入了一组额外的分段卸载类型，包括 SKB_GSO_IPXIP4、SKB_GSO_IPXIP6、SKB_GSO_GRE 和 SKB_GSO_UDP_TUNNEL。这些额外的分段类型用于识别存在多组头部的情况。例如，在 IPIP 和 SIT 的情况下，网络和传输头部应从标准头部列表移动到“内部”头部偏移量。
目前仅支持两种级别的报头。通常将隧道报头称为外层报头，而被封装的数据通常被称为内层报头。以下是访问这些报头的函数调用列表：

IPIP/SIT 隧道::

             外层                  内层
  MAC        skb_mac_header
  网络层    skb_network_header     skb_inner_network_header
  传输层  skb_transport_header

UDP/GRE 隧道::

             外层                  内层
  MAC        skb_mac_header         skb_inner_mac_header
  网络层    skb_network_header     skb_inner_network_header
  传输层  skb_transport_header   skb_inner_transport_header

除了上述隧道类型之外，还有 SKB_GSO_GRE_CSUM 和 SKB_GSO_UDP_TUNNEL_CSUM。这两种额外的隧道类型反映了这样一个事实：外层报头还要求在外层报头中包含非零校验和。
最后，有 SKB_GSO_TUNNEL_REMCSUM，它表示某个隧道报头请求了远程校验和卸载。在这种情况下，内层报头将保留部分校验和，而仅计算外层报头的校验和。

通用分段卸载
============================

通用分段卸载是一种纯软件卸载，旨在处理设备驱动程序无法执行上述卸载的情况。在 GSO 中发生的是，给定的 skbuff 将其数据拆分为多个 skbuff，这些 skbuff 已调整大小以匹配通过 skb_shinfo()->gso_size 提供的 MSS（最大报文段大小）。
在启用任何硬件分段卸载之前，都需要在 GSO 中实现相应的软件卸载。否则，可能会出现帧在设备之间重新路由后无法传输的情况。

通用接收卸载
=======================

通用接收卸载是 GSO 的补充。理想情况下，由 GRO 组装的任何帧都应该使用 GSO 进行分段以创建相同的帧序列，并且由 GSO 分段的任何帧序列都应该能够通过 GRO 重新组装回原始帧。唯一的例外是当 IP 报头设置了 DF 位时的 IPv4 ID。
如果 IPv4 ID 的值不是顺序递增的，在通过 GRO 组装的帧通过 GSO 分段时，该值将被修改为递增。
部分通用分段卸载
====================================

部分通用分段卸载是 TSO 和 GSO 之间的混合体。它利用 TCP 和隧道的某些特性，使得无需为每个分段重写报头，只需更新最内层传输层报头和可能的最外层网络层报头即可。这使得不支持隧道卸载或带有校验和的隧道卸载的设备仍然可以利用分段功能。
在部分卸载中，除了内层传输层报头之外的所有报头都会被更新，以便它们包含如果只是简单复制报头时应有的正确值。唯一的一个例外是外层 IPv4 ID 字段。设备驱动程序需要保证在给定报头未设置 DF 位的情况下，IPv4 ID 字段递增。

SCTP 加速与 GSO
===========================

尽管缺乏硬件支持，SCTP 仍然可以利用 GSO 来通过网络堆栈传递一个大的数据包，而不是多个小的数据包。
这需要与其他卸载不同的方法，因为 SCTP 数据包不能仅仅按照 (P)MTU 进行分段。相反，块必须包含在 IP 分段中，并尊重填充。因此，与常规 GSO 不同，SCTP 不能简单地生成一个大的 skb，将 gso_size 设置为分片点并将其传递给 IP 层。
相反，SCTP协议层构建了一个skb，其中各段被正确填充并作为链式skb存储，而skb_segment()则是基于这些skb进行拆分。
为了指示这种情况，gso_size被设置为特殊值GSO_BY_FRAGS。
因此，核心网络堆栈中的任何代码都必须意识到gso_size可能是GSO_BY_FRAGS，并适当地处理这种情况。
有一些辅助函数可以简化这一过程：

- 使用skb_is_gso(skb) && skb_is_gso_sctp(skb)是判断一个skb是否为SCTP GSO skb的最佳方式；
- 对于大小检查，skb_gso_validate_*_len系列辅助函数会正确地考虑GSO_BY_FRAGS的情况；
- 对于操作数据包，skb_increase_gso_size和skb_decrease_gso_size会在检测到GSO_BY_FRAGS时发出警告，如果请求对这些skb进行操作。

这也影响到了设置了NETIF_F_FRAGLIST与NETIF_F_GSO_SCTP标志的驱动。需要注意的是，NETIF_F_GSO_SCTP也被包含在NETIF_F_GSO_SOFTWARE中。
