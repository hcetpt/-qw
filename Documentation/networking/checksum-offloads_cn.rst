### SPDX 许可证标识符：GPL-2.0

=================
校验和卸载
=================

#### 引言
=================

本文档描述了 Linux 网络堆栈中的一系列技术，以利用各种网卡的校验和卸载功能。以下是所描述的技术：

* 发送校验和卸载（TX Checksum Offload）
* 本地校验和卸载（LCO：Local Checksum Offload）
* 远程校验和卸载（RCO：Remote Checksum Offload）

以下内容应该在此处进行记录，但尚未完成：

* 接收校验和卸载（RX Checksum Offload）
* 将 CHECKSUM_UNNECESSARY 转换

#### 发送校验和卸载
==================

设备发送校验和卸载接口在 `include/linux/skbuff.h` 文件顶部附近的注释中有详细说明。简而言之，它允许请求设备根据 `sk_buff` 字段中的 `skb->csum_start` 和 `skb->csum_offset` 来填充一个按位求补的校验和。设备应从 `csum_start` 到数据包末尾计算出 16 位的按位求补校验和（即“IP 风格”的校验和），并将其结果填入 `(csum_start + csum_offset)` 处。由于 `csum_offset` 不可能是负数，这就确保了校验和字段的先前值被包含在校验和计算中，因此可以用于提供所需的校验和修正（例如，UDP 或 TCP 的伪头的总和）。此接口只允许卸载单个校验和。当使用封装时，数据包可能在不同的头部层有多个校验和字段，其余部分需要通过其他机制处理，如 LCO 或 RCO。
CRC32c 也可以使用此接口卸载，方法是按照上述方式填写 `skb->csum_start` 和 `skb->csum_offset`，并设置 `skb->csum_not_inet`；更多详情请参阅 `skbuff.h` 中的注释（节 'D'）。
不执行 IP 标头校验和的卸载；始终由软件完成。这是可以接受的，因为当我们构建 IP 标头时，显然它已经在缓存中，所以对其进行求和并不昂贵。此外，它的长度也较短。
GSO 的要求更为复杂，因为在分割封装的数据包时，可能需要为每个产生的分段编辑或重新计算内外部校验和。更多细节请参阅 `skbuff.h` 注释（节 'E'）。
驱动程序在其 `netdev->hw_features` 中声明其卸载能力；更多信息请参见 `Documentation/networking/netdev-features.rst`。请注意，仅宣传具有 `NETIF_F_IP[V6]_CSUM` 功能的设备仍需遵守 `SKB` 中给出的 `csum_start` 和 `csum_offset`；如果硬件尝试自行推断这些值（正如一些网卡所做的那样），则驱动程序应检查 `SKB` 中的值是否与硬件将推断出的值匹配，如果不匹配，则应回退到使用软件进行校验和计算（使用 `skb_csum_hwoffload_help()` 或其中一个 `skb_checksum_help()` / `skb_crc32c_csum_help` 函数，如 `include/linux/skbuff.h` 中所述）。
堆栈在大多数情况下应假设校验和卸载功能被底层设备支持。唯一需要检查的地方是 `validate_xmit_skb()` 函数及其直接或间接调用的函数。该函数会比较由 SKB 请求的卸载特性（可能包括除了发送校验和卸载之外的其他卸载）与设备实际支持或启用的特性（由 `netdev->features` 确定），如果请求的特性不被支持或未启用，则在软件中执行相应的卸载。对于发送校验和卸载而言，这意味着调用 `skb_csum_hwoffload_help(skb, features)`。

### 本地校验和卸载 (LCO)

LCO 是一种高效计算封装数据报的外部校验和的技术，当内部校验和即将被卸载时使用。
一个正确计算了校验和的 TCP 或 UDP 包的一补和等于伪头部值的反码，因为其余部分都被校验和字段“抵消”掉了。这是因为一补和在写入校验和字段之前已经被取反了。
更一般地讲，只要使用“IP 风格”的一补校验和，这个规则都适用，因此任何发送校验和卸载支持的校验和也适用。
也就是说，如果我们已经为发送校验和卸载设置了一个起始位置和偏移量，我们知道在设备填充了这个校验和之后，从 `csum_start` 到包尾的一补和将等于我们之前放入校验和字段中的值的反码。这使我们能够在不查看负载的情况下计算外部校验和：当我们到达 `csum_start` 时停止求和，然后加上位于 `(csum_start + csum_offset)` 的 16 位字的反码。
然后，当真正的内部校验和被填充（无论是硬件还是通过 `skb_checksum_help()` 完成），外部校验和就会因为算术关系而变得正确。
LCO 在堆栈构建 VXLAN 或 GENEVE 等封装的外部 UDP 头时由 `udp_set_csum()` 执行。对于 IPv6 的等价实现，在 `udp6_set_csum()` 中进行。
构建 IPv4 GRE 头时也在 `net/ipv4/ip_gre.c:build_header()` 中执行 LCO。目前构建 IPv6 GRE 头时 (`net/ipv6/ip6_gre.c:ip6gre_xmit2()`) 并没有执行 LCO；GRE 校验和是在整个包上计算的，但应该有可能在此处使用 LCO，因为 IPv6 GRE 仍然使用 IP 风格的校验和。
所有的 LCO 实现都使用了辅助函数 `lco_csum()`，该函数位于 `include/linux/skbuff.h` 中。
LCO 可以安全地用于嵌套封装；在这种情况下，外部封装层将对其自身的头部以及“中间”头部进行求和。
这意味着“中间”报头将被多次汇总，但似乎没有其他办法可以避免这一点，除非付出更大的代价（例如，导致SKB膨胀）。

RCO：远程校验和卸载
============================

RCO是一种技术，用于省略封装数据报的内部校验和，从而允许外部校验和卸载。但是，它确实需要对封装协议进行更改，接收端也必须支持这些更改。因此，默认情况下它是禁用的。

有关RCO的详细信息，请参阅以下Internet草案：

* https://tools.ietf.org/html/draft-herbert-remotecsumoffload-00
* https://tools.ietf.org/html/draft-herbert-vxlan-rco-00

在Linux中，RCO是在每个封装协议中单独实现的，并且大多数隧道类型都有控制其使用的标志。例如，VXLAN有一个标志VXLAN_F_REMCSUM_TX（根据struct vxlan_rdst），用于指示在向特定远程目的地传输时应使用RCO。
