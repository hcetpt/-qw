SPDX 许可证标识符: GPL-2.0

===================================
Netfilter 连接跟踪 Sysfs 变量
===================================

/proc/sys/net/netfilter/nf_conntrack_* 变量:
=================================================

nf_conntrack_acct - 布尔值
	- 0 - 禁用（默认）
	- 非 0 - 启用

	启用连接跟踪流的会计。为每个流添加 64 位字节和数据包计数器。
nf_conntrack_buckets - 整数
	哈希表的大小。如果在模块加载时未指定参数，则默认大小是通过将总内存除以 16384 来确定桶的数量。哈希表永远不会少于 1024 个桶，也不会多于 262144 个桶。
此 sysctl 仅在初始网络命名空间中可写入。
nf_conntrack_checksum - 布尔值
	- 0 - 禁用
	- 非 0 - 启用（默认）

	验证传入数据包的校验和。校验和错误的数据包处于 INVALID 状态。如果启用了此选项，则这些数据包不会被考虑进行连接跟踪。
nf_conntrack_count - 整数（只读）
	当前分配的流条目的数量
nf_conntrack_events - 布尔值
	- 0 - 禁用
	- 1 - 启用
	- 2 - 自动（默认）

	如果启用了此选项，连接跟踪代码将通过 ctnetlink 向用户空间提供连接跟踪事件。
默认情况下，如果用户空间程序正在监听 ctnetlink 事件，则会分配扩展。
nf_conntrack_expect_max - 整数
	期望表的最大大小。默认值为 nf_conntrack_buckets / 256。最小值为 1。
nf_conntrack_frag6_high_thresh - 整数
	默认 262144

	用于重组 IPv6 分片的最大内存。当为这个目的分配了 nf_conntrack_frag6_high_thresh 字节的内存时，分片处理程序将丢弃数据包直到达到 nf_conntrack_frag6_low_thresh 的阈值。
nf_conntrack_frag6_low_thresh - 整数
	默认 196608

	参见 nf_conntrack_frag6_high_thresh。

nf_conntrack_frag6_timeout - 整数（秒）
	默认 60

	保存一个 IPv6 分片在内存中的时间。
`nf_conntrack_generic_timeout` - 整数（秒）
    默认值 600

    泛型超时的默认值。这指的是第四层未知/不受支持的协议。
`nf_conntrack_icmp_timeout` - 整数（秒）
    默认值 30

    ICMP 超时的默认值。
`nf_conntrack_icmpv6_timeout` - 整数（秒）
    默认值 30

    ICMPv6 超时的默认值。
`nf_conntrack_log_invalid` - 整数
    - 0   - 禁用（默认）
    - 1   - 记录 ICMP 数据包
    - 6   - 记录 TCP 数据包
    - 17  - 记录 UDP 数据包
    - 33  - 记录 DCCP 数据包
    - 41  - 记录 ICMPv6 数据包
    - 136 - 记录 UDPLITE 数据包
    - 255 - 记录任何协议的数据包

    根据值指定的类型记录无效数据包。
`nf_conntrack_max` - 整数
        允许的最大连接跟踪条目数量。此值默认设置为 `nf_conntrack_buckets`
        
        注意：连接跟踪条目会被添加两次 —— 一次用于原始方向，一次用于回复方向（即，地址相反）。这意味着在默认设置下，达到最大值的表将具有平均哈希链长度为 2，而不是 1。
`nf_conntrack_tcp_be_liberal` - 布尔值
    - 0 - 禁用（默认）
    - 非 0 - 启用

    在自己的行为上要保守，在接受他人行为时要宽容
    如果是非零值，我们仅标记窗口外的 RST 分段为 INVALID。
`nf_conntrack_tcp_ignore_invalid_rst` - 布尔值
    - 0 - 禁用（默认）
    - 1 - 启用

    如果是 1，我们不对窗口外的 RST 分段标记为 INVALID。
`nf_conntrack_tcp_loose` - 布尔值
    - 0 - 禁用
    - 非 0 - 启用（默认）

    如果设置为 0，则禁用接收已建立的连接。
`nf_conntrack_tcp_max_retrans` - 整数  
默认值 3  

在未收到目的地发来的（可接受的）确认应答前，可以重新传输的最大数据包数量。如果达到此数值，则会启动一个较短的计时器。

`nf_conntrack_tcp_timeout_close` - 整数（秒）
默认值 10  

`nf_conntrack_tcp_timeout_close_wait` - 整数（秒）
默认值 60  

`nf_conntrack_tcp_timeout_established` - 整数（秒）
默认值 432000（5天）  

`nf_conntrack_tcp_timeout_fin_wait` - 整数（秒）
默认值 120  

`nf_conntrack_tcp_timeout_last_ack` - 整数（秒）
默认值 30  

`nf_conntrack_tcp_timeout_max_retrans` - 整数（秒）
默认值 300  

`nf_conntrack_tcp_timeout_syn_recv` - 整数（秒）
默认值 60  

`nf_conntrack_tcp_timeout_syn_sent` - 整数（秒）
默认值 120  

`nf_conntrack_tcp_timeout_time_wait` - 整数（秒）
默认值 120  

`nf_conntrack_tcp_timeout_unacknowledged` - 整数（秒）
默认值 300  

`nf_conntrack_timestamp` - 布尔值  
- 0 - 禁用（默认值）
- 非0 - 启用  

启用连接跟踪流的时间戳记录功能。

`nf_conntrack_sctp_timeout_closed` - 整数（秒）
默认值 10  

`nf_conntrack_sctp_timeout_cookie_wait` - 整数（秒）
默认值 3  

`nf_conntrack_sctp_timeout_cookie_echoed` - 整数（秒）
默认值 3  

`nf_conntrack_sctp_timeout_established` - 整数（秒）
默认值 210  

默认值设置为 (hb_interval * path_max_retrans + rto_max)

`nf_conntrack_sctp_timeout_shutdown_sent` - 整数（秒）
默认值 3  

`nf_conntrack_sctp_timeout_shutdown_recd` - 整数（秒）
默认值 3  

`nf_conntrack_sctp_timeout_shutdown_ack_sent` - 整数（秒）
默认值 3  

`nf_conntrack_sctp_timeout_heartbeat_sent` - 整数（秒）
默认值 30  

此超时用于在辅助路径上建立连接跟踪条目。
默认值设置为 hb_interval

`nf_conntrack_udp_timeout` - 整数（秒）
默认值 30  

`nf_conntrack_udp_timeout_stream` - 整数（秒）
默认值 120  

如果检测到UDP流，则将使用此扩展超时时间。

`nf_conntrack_gre_timeout` - 整数（秒）
默认值 30  

`nf_conntrack_gre_timeout_stream` - 整数（秒）
默认值 180  

如果检测到GRE流，则将使用此扩展超时时间。

`nf_hooks_lwtunnel` - 布尔值  
- 0 - 禁用（默认值）
- 非0 - 启用  

如果启用此选项，则轻量级隧道netfilter钩子会被启用。一旦启用此选项后无法禁用。

`nf_flowtable_tcp_timeout` - 整数（秒）
默认值 30  

控制TCP连接卸载到nf flow表的超时时间。
TCP连接可以从nf conntrack卸载到nf flow表中。
过期后，连接将返回到nf conntrack。
nf_flowtable_udp_timeout - 整数 (秒)
        默认 30

        控制 UDP 连接的卸载超时时间
UDP 连接可以从 nf conntrack 卸载到 nf flow table
一旦老化，该连接将返回到 nf conntrack
