```
SPDX 许可证标识符: GPL-2.0

=================
校验和卸载
=================

简介
============

本文档描述了 Linux 网络堆栈中的一系列技术，以利用各种网卡的校验和卸载功能。以下是所描述的技术：

* 发送校验和卸载（TX Checksum Offload）
* 本地校验和卸载（LCO：Local Checksum Offload）
* 远程校验和卸载（RCO：Remote Checksum Offload）

应当在此处记录但尚未记录的内容：

* 接收校验和卸载（RX Checksum Offload）
* 将 CHECKSUM_UNNECESSARY 转换

发送校验和卸载
==================

将发送校验和卸载到设备的接口在 `include/linux/skbuff.h` 的顶部附近有详细说明。简而言之，它允许请求设备填充由 `sk_buff` 字段 `skb->csum_start` 和 `skb->csum_offset` 定义的一个一补码校验和。设备应从 `csum_start` 到数据包末尾计算 16 位一补码校验和（即“IP 风格”的校验和），并将结果填充到 `(csum_start + csum_offset)` 处。由于 `csum_offset` 不能为负数，这确保了校验和字段的前一个值包含在校验和计算中，因此它可以用于提供任何所需的校验和修正（例如 UDP 或 TCP 的伪头之和）。此接口仅允许卸载一个校验和。当使用封装时，数据包可能在不同的头部层中有多个校验和字段，其余部分必须通过其他机制如 LCO 或 RCO 来处理。CRC32c 也可以通过此接口卸载，方法是按照上述方法填充 `skb->csum_start` 和 `skb->csum_offset` 并设置 `skb->csum_not_inet`；详见 `skbuff.h` 注释（“D”节）中的更多详细信息。不执行 IP 头校验和的卸载；它始终在软件中完成。这是可以接受的，因为当我们构建 IP 头时，显然已经将其缓存起来，所以对其进行求和并不昂贵。而且它的长度也较短。GSO 的要求更为复杂，因为在分割封装的数据包时，内部和外部校验和都可能需要对每个生成的分段进行编辑或重新计算。详见 `skbuff.h` 注释（“E”节）中的更多详细信息。驱动程序在其 `netdev->hw_features` 中声明其卸载能力；详见 `Documentation/networking/netdev-features.rst`。请注意，只宣传 `NETIF_F_IP[V6]_CSUM` 的设备仍需遵守 `SKB` 中提供的 `csum_start` 和 `csum_offset`；如果设备试图自行在硬件中推断这些值（某些网卡就是这样做的），则驱动程序应检查 `SKB` 中的值是否与硬件将推断出的值匹配，并且如果不匹配，则应回退到使用软件进行校验和（使用 `skb_csum_hwoffload_help()` 或 `skb_checksum_help()` / `skb_crc32c_csum_help` 函数之一，如 `include/linux/skbuff.h` 中所述）。
```
堆栈应主要假定底层设备支持校验和卸载。唯一需要检查的地方是`validate_xmit_skb()`及其直接或间接调用的函数。该函数会比较SKB请求的卸载特性（可能包括TX校验和卸载之外的其他卸载）并根据`netdev->features`判断这些特性是否受支持或启用，如果不受支持或未启用，则在软件中执行相应的卸载。对于TX校验和卸载，这意味着调用`skb_csum_hwoffload_help(skb, features)`。

LCO：本地校验和卸载
===================

LCO是一种在内层校验和将要卸载时高效计算封装数据报的外层校验和的技术。正确进行校验和的TCP或UDP数据包的一补和等于伪头部之和的补码，因为其他部分会被校验和字段“抵消”。这是因为在写入校验和字段之前已经对总和进行了补码操作。
更一般地，在任何使用“IP风格”的一补码校验和的情况下，这一点都成立，因此任何TX校验和卸载支持的校验和也适用。也就是说，如果我们设置了一个TX校验和卸载的起始/偏移对，我们知道在设备填充了这个校验和之后，从`csum_start`到数据包末尾的一补和将等于我们事先放入校验和字段中的值的补码。这使我们可以在不查看有效负载的情况下计算外层校验和：当我们到达`csum_start`时停止求和，然后加上位于`(csum_start + csum_offset)`处的16位字的补码。
当真正的内层校验和被填充（无论是由硬件还是通过`skb_checksum_help()`）时，由于算术关系，外层校验和将变得正确。
LCO在构建VXLAN或GENEVE等封装的外层UDP头时由堆栈执行，具体在`udp_set_csum()`中。类似地，对于IPv6等价物，在`udp6_set_csum()`中也是如此。
它还在构建IPv4 GRE头时执行，在`net/ipv4/ip_gre.c:build_header()`中。目前在构建IPv6 GRE头时没有执行LCO；GRE校验和在整个数据包上计算，具体在`net/ipv6/ip6_gre.c:ip6gre_xmit2()`中，但应该可以在这里使用LCO，因为IPv6 GRE仍然使用IP风格的校验和。
所有LCO实现都使用了辅助函数`lco_csum()`，位于`include/linux/skbuff.h`中。
LCO可以安全地用于嵌套封装；在这种情况下，外层封装层将对其自身的头部和“中间”头部进行求和。
这确实意味着“中间”报头将被多次累加，但似乎没有其他办法可以避免这种情况而不带来更大的成本（例如，SKB膨胀）。

RCO：远程校验和卸载
=================

RCO 是一种技术，用于省略封装数据报的内部校验和，从而允许外部校验和卸载。然而，它确实需要对封装协议进行修改，接收方也必须支持这些修改。因此，默认情况下它是禁用的。

RCO 详细描述在以下互联网草案中：

* https://tools.ietf.org/html/draft-herbert-remotecsumoffload-00
* https://tools.ietf.org/html/draft-herbert-vxlan-rco-00

在 Linux 中，RCO 在每个封装协议中单独实现，并且大多数隧道类型都有控制其使用的标志。例如，VXLAN 有一个标志 VXLAN_F_REMCSUM_TX（根据结构体 `vxlan_rdst`），表示在向某个远程目的地传输时应使用 RCO。
