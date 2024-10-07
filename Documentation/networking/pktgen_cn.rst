SPDX 许可证标识符: GPL-2.0

====================================
Linux 数据包生成器使用指南
====================================

启用 CONFIG_NET_PKTGEN 以编译并构建 pktgen，可以在内核中或作为模块构建。建议使用模块；如果需要，请执行 modprobe pktgen。启动后，pktgen 会为每个 CPU 创建一个线程，并将该线程绑定到该 CPU 上。监控和控制通过 /proc 实现。最简单的方法是选择一个合适的示例脚本并进行配置。在双 CPU 系统上，例如：

```
ps aux | grep pkt
root       129  0.3  0.0     0    0 ?        SW    2003 523:20 [kpktgend_0]
root       130  0.3  0.0     0    0 ?        SW    2003 509:50 [kpktgend_1]
```

为了监控和控制 pktgen 会创建以下文件：

```
/proc/net/pktgen/pgctrl
/proc/net/pktgen/kpktgend_X
/proc/net/pktgen/ethX
```

调整 NIC 以实现最大性能
==============================

默认的 NIC 设置可能没有针对 pktgen 的这种人工过载类型的基准测试进行优化，因为这可能会损害正常使用场景。特别是增加 NIC 中的 TX 环形缓冲区大小：

```
# ethtool -G ethX tx 1024
```

较大的 TX 环形缓冲区可以提高 pktgen 的性能，但在一般情况下可能会导致问题：1) 因为 TX 环形缓冲区可能会大于 CPU 的 L1/L2 缓存；2) 因为它允许在 NIC 硬件层中更多的队列（这会导致缓冲膨胀）。
不应轻易得出结论认为 TX 环形缓冲区中的数据包/描述符会引起延迟。驱动程序通常出于各种性能原因会延迟清理环形缓冲区，而停滯在 TX 环形缓冲区中的数据包可能只是在等待清理。
这个清理问题是驱动程序 ixgbe（Intel 82599 芯片）的具体情况。此驱动程序（ixgbe）结合了 TX 和 RX 环形缓冲区的清理，并且清理间隔受到 ethtool --coalesce 设置的参数 "rx-usecs" 的影响。
对于 ixgbe，可以使用例如 "30"，这将产生大约每秒 33K 次中断（1/30 * 10^6）：

```
# ethtool -C ethX rx-usecs 30
```

内核线程
==============
pktgen 为每个 CPU 创建一个线程，并将该线程绑定到该 CPU 上。
这通过 proc 文件 `/proc/net/pktgen/kpktgend_X` 进行控制。
示例：`/proc/net/pktgen/kpktgend_0`：

```
运行中：
已停止：eth4@0
结果：OK: add_device=eth4@0
```

最重要的是分配给线程的设备。
两个基本的线程命令是：

* `add_device DEVICE@NAME` -- 添加单个设备
* `rem_device_all` -- 移除所有关联设备

当向线程添加设备时，会创建相应的 proc 文件用于配置该设备。因此，设备名称需要唯一。
为了支持将同一个设备添加到多个线程中，这对于多队列网卡非常有用，设备命名方案通过添加“@”进行了扩展：
device@something

“@”之后的部分可以是任何内容，但通常使用线程编号。
查看设备
===============

`Params` 部分包含配置信息。`Current` 部分包含运行时的统计信息。`Result` 在运行后或中断后打印。示例：

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
===================
这可以通过 `/proc` 接口完成，并且最简单的方法是通过 `pgset` 命令，如样本脚本中定义的那样。
你需要指定 `PGDEV` 环境变量来使用样本脚本中的函数，例如：

```
export PGDEV=/proc/net/pktgen/eth4@0
source samples/pktgen/functions.sh
```

示例：

```
pg_ctrl start           启动注入
pg_ctrl stop            中断注入。同样地，^C 也会中断生成器
pgset "clone_skb 1"     设置相同数据包的副本数量
pgset "clone_skb 0"     使用单个 SKB 进行所有传输
pgset "burst 8"         使用 xmit_more API 排队 8 个相同的数据包并一次性更新硬件 TX 队列尾指针
“burst 1” 是默认值
pgset "pkt_size 9014"   将数据包大小设置为 9014
pgset "frags 5"         数据包将由 5 个片段组成
pgset "count 200000"    设置要发送的数据包数量，设置为零表示连续发送直到明确停止
pgset "delay 5000"      在 hard_start_xmit() 中添加延迟（纳秒）

pgset "dst 10.0.0.1"    设置 IP 目标地址
			 （注意！此生成器非常激进！）

pgset "dst_min 10.0.0.1"            与 dst 相同
pgset "dst_max 10.0.0.254"          设置最大目标 IP
pgset "src_min 10.0.0.1"            设置最小（或唯一）源 IP
pgset "src_max 10.0.0.254"          设置最大源 IP
pgset "dst6 fec0::1"     IPv6 目标地址
pgset "src6 fec0::2"     IPv6 源地址
pgset "dstmac 00:00:00:00:00:00"    设置 MAC 目标地址
pgset "srcmac 00:00:00:00:00:00"    设置 MAC 源地址

pgset "queue_map_min 0" 设置 TX 队列区间的最小值
pgset "queue_map_max 7" 设置 TX 队列区间的最大值，对于多队列设备
			 要选择某个设备的队列 1，
			 使用 queue_map_min=1 和 queue_map_max=1

pgset "src_mac_count 1" 设置我们将遍历的 MAC 数量
```
```plaintext
'minimum' MAC 是您通过 srcmac 设置的
pgset "dst_mac_count 1" 设置我们将遍历的 MAC 地址数量
'minimum' MAC 是您通过 dstmac 设置的
pgset "flag [name]" 设置一个标志来确定行为。当前的标志有：
                IPSRC_RND  # 源 IP 是随机的（在最小值和最大值之间）
                IPDST_RND  # 目标 IP 是随机的
                UDPSRC_RND, UDPDST_RND,
                MACSRC_RND, MACDST_RND
                TXSIZE_RND, IPV6,
                MPLS_RND, VID_RND, SVID_RND
                FLOW_SEQ,
                QUEUE_MAP_RND  # 队列映射随机
                QUEUE_MAP_CPU  # 队列映射镜像 smp_processor_id()
                UDPCSUM,
                IPSEC  # IPsec 封装（需要 CONFIG_XFRM）
                NODE_ALLOC  # 节点特定内存分配
                NO_TIMESTAMP  # 禁用时间戳
                SHARED  # 启用共享 SKB

pgset 'flag ![name]' 清除一个标志来确定行为
请注意，在交互模式下，您可能需要使用单引号，以防止您的 shell 将指定的标志扩展为历史命令
pgset "spi [SPI_VALUE]" 设置用于转换数据包的具体安全关联(SA)
pgset "udp_src_min 9" 设置 UDP 源端口最小值，如果小于 udp_src_max，则遍历端口范围
pgset "udp_src_max 9" 设置 UDP 源端口最大值
pgset "udp_dst_min 9" 设置 UDP 目标端口最小值，如果小于 udp_dst_max，则遍历端口范围
pgset "udp_dst_max 9" 设置 UDP 目标端口最大值
```
```sh
# 设置MPLS标签（在此示例中，外层标签=16，中间标签=32，内层标签=0（IPv4 NULL））。注意参数之间不能有空格。前导零是必需的。
# 不要设置栈底位，这是自动完成的。如果你设置了栈底位，则表示你希望随机生成该地址，并且MPLS_RND标志将被启用。你可以混合使用随机和固定标签在标签栈中。
pgset "mpls 0001000a,0002000a,0000000a"

# 关闭MPLS（或任何无效参数也有效）
pgset "mpls 0"

# 设置VLAN ID 0-4095
pgset "vlan_id 77"

# 设置优先级位 0-7（默认为0）
pgset "vlan_p 3"

# 设置规范格式标识符 0-1（默认为0）
pgset "vlan_cfi 0"

# 设置SVLAN ID 0-4095
pgset "svlan_id 22"

# 设置优先级位 0-7（默认为0）
pgset "svlan_p 3"

# 设置规范格式标识符 0-1（默认为0）
pgset "svlan_cfi 0"

# 大于4095时移除VLAN和SVLAN标签
pgset "vlan_id 9999"

# 大于4095时移除SVLAN标签
pgset "svlan 9999"

# 设置前IPv4 TOS字段（例如“tos 28”表示AF11不带ECN，默认为00）
pgset "tos XX"

# 设置前IPv6 TRAFFIC CLASS（例如“traffic_class B8”表示EF不带ECN，默认为00）
pgset "traffic_class XX"

# 将速率设置为300 Mbps
pgset "rate 300M"

# 将速率设置为1 Mpps
pgset "ratep 1000000"

# 将发送模式设置为netif_receive_skb()
pgset "xmit_mode netif_receive"
# 这与“burst”模式一起工作，但不与“clone_skb”模式一起工作。默认的发送模式是“start_xmit”。

# 示例脚本
# ===========
# 包含用于pktgen的教程脚本和辅助脚本的目录是samples/pktgen。helper参数文件parameters.sh支持样本脚本中一致的参数解析。
# 使用示例和帮助：
#
# ./pktgen_sample01_simple.sh -i eth4 -m 00:1B:21:3C:9D:F8 -d 192.168.8.2
#
# 使用方法：
#
# ./pktgen_sample01_simple.sh [-vx] -i ethX
#
# 参数：
# -i : ($DEV) 输出接口/设备（必需）
# -s : ($PKT_SIZE) 数据包大小
# -d : ($DEST_IP) 目标IP。CIDR（例如198.18.0.0/15）也是允许的
# -m : ($DST_MAC) 目标MAC地址
# -p : ($DST_PORT) 目标端口范围（例如433-444）也是允许的
# -t : ($THREADS) 启动线程数
# -f : ($F_THREAD) 第一个线程的索引（从0开始的CPU编号）
# -c : ($SKB_CLONE) 在分配新SKB之前发送的SKB克隆数量
# -n : ($COUNT) 每个线程发送的消息数，0表示无限期发送
# -b : ($BURST) 硬件级别的SKB突发
# -v : ($VERBOSE) 显示详细信息
# -x : ($DEBUG) 调试模式
# -6 : ($IP6) IPv6
# -w : ($DELAY) 发送延迟值（纳秒）
# -a : ($APPEND) 脚本不会重置生成器的状态，而是追加其配置
#
# 设置的全局变量也列出了。例如，必需的接口/设备参数"-i"设置了变量$DEV。复制pktgen_sampleXX脚本并根据需要进行修改。

# 中断亲和性
# ====================
# 注意，在将设备添加到特定CPU时，最好也分配/proc/irq/XX/smp_affinity，以便TX中断绑定到同一CPU。这减少了释放skbs时的缓存抖动。
# 另外，使用设备标志QUEUE_MAP_CPU，它将SKBs的TX队列映射到运行线程的CPU（直接来自smp_processor_id()）。

# 启用IPsec
# =============
# 默认的IPsec转换，带有ESP封装和传输模式，可以通过简单设置来启用：
#
# pgset "flag IPSEC"
# pgset "flows 1"
#
# 为了避免破坏现有的测试脚本，这些脚本使用AH类型和隧道模式，你可以使用“pgset spi SPI_VALUE”来指定要使用的转换模式。

# 禁用共享SKB
# ===================
# 默认情况下，由pktgen发送的SKBs是共享的（用户计数>1）
```
为了使用非共享的SKBs进行测试，请移除“SHARED”标志，只需设置如下命令：

	pg_set "flag !SHARED"

但是，如果配置了“clone_skb”或“burst”参数，则仍然需要让pktgen持有skb以便进一步访问。因此，skb必须是共享的。

当前命令和配置选项
==================

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

    tos           (ipv4)
    traffic_class (ipv6)

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

参考：
- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/
- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/examples/

2004年在埃尔兰根举行的Linux-Kongress会议论文：
- ftp://robur.slu.se/pub/Linux/net-development/pktgen-testing/pktgen_paper.pdf

感谢以下人员的支持与测试：
- Grant Grundler 在 IA-64 和 parisc 上的测试，Harald Welte，Lennert Buytenhek
- Stephen Hemminger，Andi Kleen，Dave Miller 及其他许多人

祝你在 Linux 网络开发方面好运。
