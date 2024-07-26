SPDX 许可证标识符: GPL-2.0

====================================
Linux 数据包生成器的使用说明
====================================

启用 CONFIG_NET_PKTGEN 来编译和构建 pktgen，可以是内核的一部分或作为一个模块。推荐使用模块形式；如果需要的话，可以通过 `modprobe pktgen` 加载它。运行后，pktgen 会为每个 CPU 创建一个线程，并将该线程绑定到对应的 CPU 上。
监控和控制可通过 `/proc` 文件系统进行。最简单的方法是从合适的示例脚本开始配置。
在一个双 CPU 系统上，可以看到如下输出：

    ps aux | grep pkt
    root       129  0.3  0.0     0    0 ?        SW    2003 523:20 [kpktgend_0]
    root       130  0.3  0.0     0    0 ?        SW    2003 509:50 [kpktgend_1]

为了监控和控制 pktgen 的行为，创建了以下文件：

    /proc/net/pktgen/pgctrl
    /proc/net/pktgen/kpktgend_X
    /proc/net/pktgen/ethX

调整 NIC 以达到最大性能
==============================

默认的 NIC 设置可能没有针对 pktgen 这种人为超负载测试进行优化，因为这可能会影响到正常的使用场景。特别是增加 NIC 中的 TX 环形缓冲区的大小：

    # ethtool -G ethX tx 1024

较大的 TX 环形缓冲区可以提高 pktgen 的性能，但在一般情况下可能会产生负面影响：1) 因为 TX 环形缓冲区可能会超出 CPU 的 L1/L2 缓存大小；2) 因为它允许在 NIC 硬件层中进行更多的队列操作（这不利于缓冲区膨胀问题）。
人们不应该轻易得出结论说 TX 环形缓冲区中的数据包/描述符会导致延迟。驱动程序通常出于各种性能原因而延迟清理环形缓冲区，而停顿在 TX 环形缓冲区中的数据包可能只是在等待被清理。
这个清理问题是 ixgbe 驱动（Intel 82599 芯片）的一个特例。此驱动程序结合了 TX 和 RX 环形缓冲区的清理，且清理间隔受 ethtool 的 `--coalesce` 设置中的参数 `rx-usecs` 的影响。
对于 ixgbe，可以使用例如 "30"，这样大约每秒会产生 33K 次中断（1/30*10^6）：

    # ethtool -C ethX rx-usecs 30

内核线程
==============
pktgen 为每个 CPU 创建一个与其绑定的线程。
这些线程通过 `/proc/net/pktgen/kpktgend_X` 文件进行控制。
例如，`/proc/net/pktgen/kpktgend_0` 文件的内容如下：

    Running:
    Stopped: eth4@0
    Result: OK: add_device=eth4@0

最重要的是分配给线程的设备。
两个基本的线程命令是：

 * `add_device DEVICE@NAME` -- 添加一个单一设备
 * `rem_device_all`         -- 移除所有相关联的设备

当向线程添加一个设备时，会创建一个相应的 `/proc` 文件来配置该设备。因此，设备名称需要是唯一的。
为了支持将同一设备添加到多个线程中，这对于多队列网络接口卡（NIC）非常有用，设备命名方案通过添加“@”进行了扩展：
device@something

“@”之后的部分可以是任何内容，但通常使用线程编号。
查看设备
==========

`Params`部分保存配置信息。`Current`部分保存运行时统计信息。`Result`在运行结束后或中断后打印。示例如下：

```
/proc/net/pktgen/eth4@0

Params: count 100000  min_pkt_size: 60  max_pkt_size: 60
        frags: 0  delay: 0  clone_skb: 64  ifname: eth4@0
        flows: 0 flowlen: 0
        queue_map_min: 0  queue_map_max: 0
        dst_min: 192.168.81.2  dst_max:
        src_min:   src_max:
        src_mac: 90:e2:ba:0a:56:b4 dst_mac: 00:1b:21:3c:9d:f8
        udp_src_min: 9  udp_src_max: 109  udp_dst_min: 9  udp_dst_max: 9
        src_mac_count: 0  dst_mac_count: 0
        Flags: UDPSRC_RND  NO_TIMESTAMP  QUEUE_MAP_CPU
Current:
        pkts-sofar: 100000  errors: 0
        started: 623913381008us  stopped: 623913396439us idle: 25us
        seq_num: 100001  cur_dst_mac_offset: 0  cur_src_mac_offset: 0
        cur_saddr: 192.168.8.3  cur_daddr: 192.168.81.2
        cur_udp_dst: 9  cur_udp_src: 42
        cur_queue_map: 0
        flows: 0
Result: OK: 15430(c15405+d25) usec, 100000 (60byte,0frags)
        6480562pps 3110Mb/sec (3110669760bps) errors: 0
```

配置设备
=========

这可以通过`/proc`接口完成，并且最简单的方法是通过`pgset`命令，该命令在示例脚本中定义。
你需要指定`PGDEV`环境变量来使用示例脚本中的函数，例如：

```
export PGDEV=/proc/net/pktgen/eth4@0
source samples/pktgen/functions.sh
```

示例：

```
pg_ctrl start           # 开始注入数据包
pg_ctrl stop            # 中断注入数据包。同时，^C 也会中断生成器
pgset "clone_skb 1"     # 设置相同数据包的副本数量
pgset "clone_skb 0"     # 对所有发送使用单一SKB
pgset "burst 8"         # 使用xmit_more API来排队8个相同的数据包，并一次更新硬件TX队列尾指针
                         # “burst 1”为默认值
pgset "pkt_size 9014"   # 设置数据包大小为9014字节
pgset "frags 5"         # 数据包将由5个片段组成
pgset "count 200000"    # 设置要发送的数据包数量，设置为零则会持续发送直到明确停止
pgset "delay 5000"      # 在hard_start_xmit()中增加延迟。单位为纳秒

pgset "dst 10.0.0.1"    # 设置IP目标地址
                         # （警告！此生成器非常激进！）

pgset "dst_min 10.0.0.1"  # 同上
pgset "dst_max 10.0.0.254"  # 设置最大目标IP
pgset "src_min 10.0.0.1"  # 设置最小（或唯一）源IP
pgset "src_max 10.0.0.254"  # 设置最大源IP
pgset "dst6 fec0::1"     # IPv6目标地址
pgset "src6 fec0::2"     # IPv6源地址
pgset "dstmac 00:00:00:00:00:00"  # 设置MAC目标地址
pgset "srcmac 00:00:00:00:00:00"  # 设置MAC源地址

pgset "queue_map_min 0"  # 设置TX队列间隔的最小值
pgset "queue_map_max 7"  # 设置TX队列间隔的最大值，适用于多队列设备
                         # 要选择某个设备的队列1，
                         # 使用queue_map_min=1 和 queue_map_max=1

pgset "src_mac_count 1"  # 设置我们将遍历的MAC地址数量
```
`minimum` MAC 是您通过 `srcmac` 设置的。
使用 `pgset "dst_mac_count 1"` 设置我们将遍历的 MAC 地址数量。
`minimum` MAC 是您通过 `dstmac` 设置的。
使用 `pgset "flag [name]"` 设置一个标志来决定行为。当前的标志包括：
- IPSRC_RND：源 IP 地址随机（在最小值和最大值之间）
- IPDST_RND：目的 IP 地址随机
- UDPSRC_RND、UDPDST_RND：源 UDP 端口随机、目的 UDP 端口随机
- MACSRC_RND、MACDST_RND：源 MAC 地址随机、目的 MAC 地址随机
- TXSIZE_RND：传输大小随机
- IPV6：IPv6 支持
- MPLS_RND：MPLS 随机
- VID_RND、SVID_RND：VLAN ID 随机、SVLAN ID 随机
- FLOW_SEQ：流序列号启用
- QUEUE_MAP_RND：队列映射随机
- QUEUE_MAP_CPU：队列映射与处理器 ID 相匹配
- UDPCSUM：UDP 校验和启用
- IPSEC：IPsec 封装（需要 CONFIG_XFRM 配置）
- NODE_ALLOC：节点特定内存分配
- NO_TIMESTAMP：禁用时间戳
- SHARED：启用共享 SKB

使用 `pgset 'flag ![name]'` 清除一个标志以决定行为。
请注意，在交互模式下，您可能需要使用单引号，以免您的 shell 将指定的标志扩展为历史命令。

使用 `pgset "spi [SPI_VALUE]"` 设置用于转换数据包的具体安全关联(SA)。
使用 `pgset "udp_src_min 9"` 设置 UDP 源端口最小值，如果小于 UDP 源端口最大值，则循环遍历端口范围。
使用 `pgset "udp_src_max 9"` 设置 UDP 源端口最大值。
使用 `pgset "udp_dst_min 9"` 设置 UDP 目的端口最小值，如果小于 UDP 目的端口最大值，则循环遍历端口范围。
使用 `pgset "udp_dst_max 9"` 设置 UDP 目的端口最大值。
以下是提供的英文内容翻译成中文的结果：

设置 "mpls 0001000a,0002000a,0000000a" 设置MPLS标签（在这个例子中，外层标签=16，中间标签=32，内层标签=0（IPv4 NULL））。请注意，参数之间不能有空格。前导零是必需的。
不要设置栈底位，这将自动完成。如果你设置了栈底位，这表示你希望随机生成该地址，并且MPLS_RND标志将被打开。你可以混合使用随机和固定标签在标签栈中。
设置 "mpls 0" 关闭MPLS（或任何无效参数也有效！）

设置 "vlan_id 77" 设置VLAN ID 0-4095
设置 "vlan_p 3" 设置优先级位 0-7 （默认为0）
设置 "vlan_cfi 0" 设置规范格式标识符 0-1 （默认为0）

设置 "svlan_id 22" 设置SVLAN ID 0-4095
设置 "svlan_p 3" 设置优先级位 0-7 （默认为0）
设置 "svlan_cfi 0" 设置规范格式标识符 0-1 （默认为0）

设置 "vlan_id 9999" 大于4095，移除VLAN和SVLAN标签
设置 "svlan 9999" 大于4095，移除SVLAN标签

设置 "tos XX" 设置之前的IPv4服务类型字段（例如 "tos 28" 对应AF11不包含ECN，默认值为00）
设置 "traffic_class XX" 设置之前的IPv6流量分类（例如 "traffic_class B8" 对应EF不包含ECN，默认值为00）

设置 "rate 300M" 设置速率为300 Mbps
设置 "ratep 1000000" 设置速率为1 Mpps

设置 "xmit_mode netif_receive" 将接收注入到netif_receive_skb()堆栈中。与"burst"模式一起工作，但不支持"clone_skb"。
默认的xmit_mode是 "start_xmit"。
示例脚本
=========

pktgen的教程脚本和辅助程序集合位于samples/pktgen目录中。helper参数文件parameters.sh支持在示例脚本中轻松且一致地解析参数。
使用示例和帮助：
```
./pktgen_sample01_simple.sh -i eth4 -m 00:1B:21:3C:9D:F8 -d 192.168.8.2
```

使用方法：
```
./pktgen_sample01_simple.sh [-vx] -i ethX

-i : ($DEV) 输出接口/设备（必需）
-s : ($PKT_SIZE) 数据包大小
-d : ($DEST_IP) 目标IP。CIDR（例如198.18.0.0/15）也被允许
-m : ($DST_MAC) 目标MAC地址
-p : ($DST_PORT) 目标端口范围（例如433-444）也被允许
-t : ($THREADS) 启动线程数
-f : ($F_THREAD) 第一线程索引（以CPU编号为基准）
-c : ($SKB_CLONE) 在分配新SKB之前发送的SKB克隆数
-n : ($COUNT) 每个线程发送的消息数，0表示无限期
-b : ($BURST) SKB的硬件级别突发
-v : ($VERBOSE) 显示详细信息
-x : ($DEBUG) 调试
-6 : ($IP6) IPv6
-w : ($DELAY) 发送延迟值（纳秒）
-a : ($APPEND) 脚本不会重置生成器的状态，而是追加其配置
```

设置的全局变量也被列出。例如，必需的接口/设备参数 "-i" 设置变量$DEV。复制pktgen_sampleXX脚本并根据自己的需求进行修改。

中断亲和性
===========
添加特定CPU的设备时，最好也分配/proc/irq/XX/smp_affinity，以便TX中断绑定到同一CPU。这减少了释放skbs时的缓存跳转。
此外，使用设备标志QUEUE_MAP_CPU，它将SKBs的TX队列映射到运行线程的CPU（直接来自smp_processor_id()）。

启用IPsec
==========
默认情况下，可以启用ESP封装的IPsec转换加上传输模式，只需设置：
```
pgset "flag IPSEC"
pgset "flows 1"
```
为了避免破坏现有的测试台脚本，这些脚本使用AH类型和隧道模式，你可以使用 "pgset spi SPI_VALUE" 来指定要使用的转换模式。

禁用共享SKB
=============
默认情况下，pktgen发送的SKBs是共享的（用户计数>1）。
为了使用非共享的SKBs进行测试，请移除"SHARED"标志，只需设置如下：

	pg_set "flag !SHARED"

然而，如果配置了"clone_skb"或"burst"参数，pktgen仍需要持有skb以便进一步访问。因此，skb必须是共享的。

当前命令和配置选项
=====================

**Pgcontrol 命令**::

    start
    stop
    reset

**线程命令**::

    add_device
    rem_device_all

**设备命令**::

    count
    clone_skb
    burst
    debug

    frags
    delay

    src_mac_count
    dst_mac_count

    pkt_size
    min_pkt_size
    max_pkt_size

    queue_map_min
    queue_map_max
    skb_priority

    tos           (IPv4)
    traffic_class (IPv6)

    mpls

    udp_src_min
    udp_src_max

    udp_dst_min
    udp_dst_max

    node

    flag
    IPSRC_RND
    IPDST_RND
    UDPSRC_RND
    UDPDST_RND
    MACSRC_RND
    MACDST_RND
    TXSIZE_RND
    IPV6
    MPLS_RND
    VID_RND
    SVID_RND
    FLOW_SEQ
    QUEUE_MAP_RND
    QUEUE_MAP_CPU
    UDPCSUM
    IPSEC
    NODE_ALLOC
    NO_TIMESTAMP
    SHARED

    spi (ipsec)

    dst_min
    dst_max

    src_min
    src_max

    dst_mac
    src_mac

    clear_counters

    src6
    dst6
    dst6_max
    dst6_min

    flows
    flowlen

    rate
    ratep

    xmit_mode <start_xmit|netif_receive>

    vlan_cfi
    vlan_id
    vlan_p

    svlan_cfi
    svlan_id
    svlan_p


参考资料：

- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/
- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/examples/

2004年埃尔兰根Linux大会论文
- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/pktgen_paper.pdf

致谢：

感谢Grant Grundler在IA-64和parisc上进行的测试，Harald Welte, Lennert Buytenhek, Stephen Hemminger, Andi Kleen, Dave Miller以及许多其他人为Linux网络开发做出的贡献。

祝你好运，Linux网络开发！
