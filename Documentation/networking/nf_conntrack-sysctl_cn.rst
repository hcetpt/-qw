SPDX 许可证标识符: GPL-2.0

===================================
Netfilter 连接跟踪 Sysfs 变量
===================================

/proc/sys/net/netfilter/nf_conntrack_* 变量:
=================================================

nf_conntrack_acct - 布尔值
	- 0 - 禁用（默认）
	- 非 0 - 启用

启用连接跟踪流计费。每个流添加 64 位字节和数据包计数器。
nf_conntrack_buckets - 整数
哈希表的大小。如果在模块加载时未指定此参数，则默认大小通过将总内存除以 16384 来计算以确定桶的数量。哈希表的桶数量永远不会少于 1024，也不会多于 262144。
此 sysctl 只能在初始网络命名空间中写入。
nf_conntrack_checksum - 布尔值
	- 0 - 禁用
	- 非 0 - 启用（默认）

验证传入数据包的校验和。校验和错误的数据包处于 INVALID 状态。如果启用此选项，此类数据包将不被考虑用于连接跟踪。
nf_conntrack_count - 整数（只读）
当前分配的流条目数量。
nf_conntrack_events - 布尔值
	- 0 - 禁用
	- 1 - 启用
	- 2 - 自动（默认）

如果启用此选项，连接跟踪代码将通过 ctnetlink 向用户空间提供连接跟踪事件。
默认情况下，如果用户空间程序监听 ctnetlink 事件，则会分配扩展。
nf_conntrack_expect_max - 整数
期望表的最大大小。默认值为 nf_conntrack_buckets / 256。最小值为 1。
nf_conntrack_frag6_high_thresh - 整数
默认 262144

用于重组 IPv6 分片的最大内存。当为该目的分配了 nf_conntrack_frag6_high_thresh 字节的内存时，分片处理器将丢弃数据包直到达到 nf_conntrack_frag6_low_thresh。
nf_conntrack_frag6_low_thresh - 整数
默认 196608

参见 nf_conntrack_frag6_low_thresh。

nf_conntrack_frag6_timeout - 整数（秒）
默认 60

保持 IPv6 分片在内存中的时间。
nf_conntrack_generic_timeout - 整数（秒）
默认值 600

通用超时的默认值。这指的是第4层未知或不受支持的协议。
nf_conntrack_icmp_timeout - 整数（秒）
默认值 30

ICMP超时的默认值。
nf_conntrack_icmpv6_timeout - 整数（秒）
默认值 30

ICMPv6超时的默认值。
nf_conntrack_log_invalid - 整数
- 0   - 禁用（默认）
- 1   - 记录ICMP数据包
- 6   - 记录TCP数据包
- 17  - 记录UDP数据包
- 33  - 记录DCCP数据包
- 41  - 记录ICMPv6数据包
- 136 - 记录UDPLITE数据包
- 255 - 记录任何协议的数据包

记录指定类型的无效数据包。
nf_conntrack_max - 整数
允许的最大连接跟踪条目数量。此值默认设置为nf_conntrack_buckets。

注意：连接跟踪条目会被添加两次——一次是原始方向，一次是回复方向（即，地址反转）。这意味着，在默认设置下，一个达到最大值的表将具有平均哈希链长度为2，而不是1。
nf_conntrack_tcp_be_liberal - 布尔值
- 0 - 禁用（默认）
- 非0 - 启用

对自己严格，对他人宽容。
如果非零，则仅标记窗口外的RST段为INVALID。
nf_conntrack_tcp_ignore_invalid_rst - 布尔值
- 0 - 禁用（默认）
- 1 - 启用

如果为1，则不标记窗口外的RST段为INVALID。
nf_conntrack_tcp_loose - 布尔值
- 0 - 禁用
- 非0 - 启用（默认）

如果设置为0，则禁用接收已建立的连接。
`nf_conntrack_tcp_max_retrans` - 整数  
默认值：3  

在未收到目标端的（可接受的）ACK的情况下，可以重新传输的最大数据包数量。如果达到此数量，将启动一个较短的定时器。

`nf_conntrack_tcp_timeout_close` - 整数（秒）
默认值：10  

`nf_conntrack_tcp_timeout_close_wait` - 整数（秒）
默认值：60  

`nf_conntrack_tcp_timeout_established` - 整数（秒）
默认值：432000（5天）  

`nf_conntrack_tcp_timeout_fin_wait` - 整数（秒）
默认值：120  

`nf_conntrack_tcp_timeout_last_ack` - 整数（秒）
默认值：30  

`nf_conntrack_tcp_timeout_max_retrans` - 整数（秒）
默认值：300  

`nf_conntrack_tcp_timeout_syn_recv` - 整数（秒）
默认值：60  

`nf_conntrack_tcp_timeout_syn_sent` - 整数（秒）
默认值：120  

`nf_conntrack_tcp_timeout_time_wait` - 整数（秒）
默认值：120  

`nf_conntrack_tcp_timeout_unacknowledged` - 整数（秒）
默认值：300  

`nf_conntrack_timestamp` - 布尔值
- 0 - 禁用（默认）
- 非0 - 启用

启用连接跟踪流的时间戳功能。

`nf_conntrack_sctp_timeout_closed` - 整数（秒）
默认值：10  

`nf_conntrack_sctp_timeout_cookie_wait` - 整数（秒）
默认值：3  

`nf_conntrack_sctp_timeout_cookie_echoed` - 整数（秒）
默认值：3  

`nf_conntrack_sctp_timeout_established` - 整数（秒）
默认值：210  

默认值设置为（hb_interval * path_max_retrans + rto_max）

`nf_conntrack_sctp_timeout_shutdown_sent` - 整数（秒）
默认值：3  

`nf_conntrack_sctp_timeout_shutdown_recd` - 整数（秒）
默认值：3  

`nf_conntrack_sctp_timeout_shutdown_ack_sent` - 整数（秒）
默认值：3  

`nf_conntrack_sctp_timeout_heartbeat_sent` - 整数（秒）
默认值：30  

此超时用于在辅助路径上设置连接跟踪条目。
默认值设置为 hb_interval

`nf_conntrack_udp_timeout` - 整数（秒）
默认值：30  

`nf_conntrack_udp_timeout_stream` - 整数（秒）
默认值：120  

如果检测到UDP流，则使用此扩展超时。

`nf_conntrack_gre_timeout` - 整数（秒）
默认值：30  

`nf_conntrack_gre_timeout_stream` - 整数（秒）
默认值：180  

如果检测到GRE流，则使用此扩展超时。

`nf_hooks_lwtunnel` - 布尔值
- 0 - 禁用（默认）
- 非0 - 启用

如果启用此选项，则启用轻量级隧道netfilter钩子。一旦启用，此选项不能被禁用。

`nf_flowtable_tcp_timeout` - 整数（秒）
默认值：30  

控制TCP连接的卸载超时。
TCP连接可以从nf conntrack卸载到nf flow表。
一旦老化，连接将返回到nf conntrack。
`nf_flowtable_udp_timeout` - 整数（秒）
默认值 30

控制 UDP 连接的卸载超时时间
UDP 连接可以从 nf conntrack 卸载到 nf flow table
一旦过期，连接将返回到 nf conntrack
