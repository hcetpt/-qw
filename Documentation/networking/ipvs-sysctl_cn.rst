SPDX 许可证标识符: GPL-2.0

==================
IPvs-sysctl
==================

/proc/sys/net/ipv4/vs/* 变量:
==================================

am_droprate - 整数
    默认 10

    设置始终模式下的丢包率，该值用于丢包率防御的第 3 模式中。
amemthresh - 整数
    默认 1024

    设置可用内存阈值（以页为单位），该值在防御的自动模式中使用。当没有足够的可用内存时，相应的策略将被启用，并且此变量自动设置为 2；否则，策略将被禁用，并且此变量设置为 1。
backup_only - 布尔值
    - 0 - 禁用（默认）
    - 非 0 - 启用

    如果设置，则在服务器处于备份模式时禁用调度功能，以避免对于 DR/TUN 方法的数据包环路问题。
conn_reuse_mode - 整数
    1 - 默认

    控制 IPVS 如何处理检测到端口重用的连接。这是一个位图，其中的值表示：

    0: 禁用任何关于端口重用的特殊处理。新连接将被发送到服务前一个连接的真实服务器。
    第 1 位：启用安全情况下新连接的重新调度。也就是说，在 expire_nodest_conn 有效的情况下，以及对于 TCP 套接字，在连接处于 TIME_WAIT 状态时（仅可能在使用 NAT 模式下）。
    第 2 位：这是第 1 位加上，对于 TCP 连接，当连接处于 FIN_WAIT 状态时，因为这是负载均衡器在直接路由模式下看到的最后一个状态。这一位有助于在一个非常繁忙的集群中添加新的真实服务器。
conntrack - 布尔值
    - 0 - 禁用（默认）
    - 非 0 - 启用

    如果设置，则为 IPVS 处理的连接维护连接跟踪条目。
    如果 IPVS 处理的连接也要由基于状态的防火墙规则处理，则应启用此设置。也就是说，使用连接跟踪的 iptables 规则。否则，禁用此设置是一种性能优化。
    不论此设置如何，由 IPVS FTP 应用模块处理的连接都将具有连接跟踪条目。
仅在使用 CONFIG_IP_VS_NFCT 配置编译 IPVS 时可用  
cache_bypass - 布尔值  
	- 0 - 禁用（默认）
	- 不为 0 - 启用

	如果启用，当没有缓存服务器可用且目标地址不是本地地址时（iph->daddr 是 RTN_UNICAST），直接将数据包转发到原始目的地。主要用于透明网络缓存集群中。
debug_level - 整数  
	- 0          - 传输错误信息（默认）
	- 1          - 非致命错误信息
	- 2          - 配置
	- 3          - 目标垃圾信息
	- 4          - 删除条目
	- 5          - 服务查找
	- 6          - 调度
	- 7          - 连接新建/过期、查找和同步
	- 8          - 状态转换
	- 9          - 绑定目标、模板检查和应用程序
	- 10         - IPVS 数据包传输
	- 11         - IPVS 数据包处理（ip_vs_in/ip_vs_out）
	- 12 或更高 - 数据包遍历

	仅在使用 CONFIG_IP_VS_DEBUG 配置编译 IPVS 时可用
较高的调试级别包括较低级别的消息，因此设置调试级别为 2 包括级别 0、1 和 2 的消息。因此，日志记录随着级别的提高而变得更加详细。
drop_entry - 整数  
	- 0  - 禁用（默认）

	drop_entry 防御策略是随机删除连接哈希表中的条目，以便为新连接回收一些内存。在当前代码中，drop_entry 过程可以每秒激活一次，然后随机扫描整个表的 1/32，并删除处于 SYN-RECV/SYNACK 状态的条目，这应该能有效对抗 syn 泛洪攻击。
drop_entry 的有效值范围是从 0 到 3，其中 0 表示该策略始终禁用，1 和 2 表示自动模式（当可用内存不足时启用该策略并将变量自动设置为 2，否则禁用该策略并将变量设置为 1），3 表示该策略始终启用。
drop_packet - 整数  
	- 0  - 禁用（默认）

	drop_packet 防御策略旨在在转发数据包到真实服务器之前丢弃 1/rate 的数据包。如果 rate 为 1，则丢弃所有传入的数据包。
rate 的值定义与 drop_entry 相同。在自动模式下，rate 由以下公式确定：rate = amemthresh / (amemthresh - available_memory)，当可用内存小于可用内存阈值时。当设置模式 3 时，始终启用的丢弃率由 /proc/sys/net/ipv4/vs/am_droprate 控制。
est_cpulist - CPU列表  
	允许用于估算 kthreads 的 CPU

	语法：标准 CPU 列表格式
	空列表 - 停止 kthread 任务和估算
	默认 - 系统为 kthreads 提供的维护 CPU

	示例：
	"all"：所有可能的 CPU
	"0-N"：所有可能的 CPU，N 表示最后一个 CPU 编号
	"0,1-N:1/2"：第一个和所有奇数编号的 CPU
	"": 空列表

est_nice - 整数  
	默认 0
	有效范围：-20（更优先）.. 19（较不优先）

	用于估算 kthreads 的优先级值（调度优先级）

expire_nodest_conn - 布尔值  
	- 0 - 禁用（默认）
	- 不为 0 - 启用

	默认值为 0，负载均衡器会默默地丢弃数据包，当其目标服务器不可用时。这在用户空间监控程序删除目标服务器（由于服务器过载或错误检测）并在稍后添加回服务器时可能会有用，此时连接到服务器可以继续。
如果启用了此功能，负载均衡器会在数据包到达且其目标服务器不可用时立即过期连接，然后客户端程序将被通知连接已关闭。这相当于一些人要求的功能，即当目标不可用时清除连接。
### expire_quiescent_template - BOOLEAN
- **0** - 禁用（默认）
- **非0** - 启用

当设置为非零值时，负载均衡器会在目标服务器处于静默状态时过期持久化模板。这可能在用户通过将目标服务器的权重设置为0来使其进入静默状态，并且希望随后的持久连接被发送到不同的目标服务器时有用。默认情况下，新的持久连接被允许发送到处于静默状态的目标服务器。如果启用了此功能，则负载均衡器将在使用持久化模板调度新连接并且目标服务器处于静默状态时使该模板过期。

### ignore_tunneled - BOOLEAN
- **0** - 禁用（默认）
- **非0** - 启用

如果设置，IPVS会为所有未识别协议的数据包设置IPVS属性。这可以防止我们路由像ipip这样的隧道协议，这对于防止被隧道到IPVS主机的数据包被重新调度很有用（即防止IPVS路由环路，当IPVS同时也作为真实服务器时）。

### nat_icmp_send - BOOLEAN
- **0** - 禁用（默认）
- **非0** - 启用

它控制了负载均衡器在收到真实服务器发来的数据包但连接条目不存在时发送ICMP错误消息（ICMP_DEST_UNREACH）的行为。

### pmtu_disc - BOOLEAN
- **0** - 禁用
- **非0** - 启用（默认）

默认情况下，无论转发方法如何，都拒绝所有超过PMTU的DF标志的数据包，并标记为FRAG_NEEDED。对于TUN方法，可以通过禁用此标志来分片此类数据包。

### secure_tcp - INTEGER
- **0** - 禁用（默认）

secure_tcp防御机制是使用更复杂的TCP状态转换表。对于VS/NAT，它还延迟进入TCP ESTABLISHED状态，直到完成三次握手。

### sync_threshold - 包含两个INTEGER的向量: sync_threshold, sync_period
- 默认值：3 50

它设置了同步阈值，即连接需要接收的最小入站数据包数量，在达到这个数量之前不会进行同步。每当连接的入站数据包数量模sync_period等于阈值时，连接就会同步一次。阈值范围从0到sync_period。

当sync_period和sync_refresh_period均为0时，仅在状态发生变化或数据包数量达到sync_threshold时发送同步信息。

### sync_refresh_period - UNSIGNED INTEGER
- 默认值：0

以秒为单位，触发新同步消息的已报告连接计时器差异。可以在连接状态自上次同步以来没有变化的情况下，在指定的时间段内（或者如果低于连接超时时间的一半）避免发送同步消息。
这段英文配置描述可以翻译为：

这有助于常规高流量连接，以降低同步频率。此外，以 `sync_refresh_period/8` 的周期重试 `sync_retries` 次。
  
- `sync_retries` — 整型
  默认值：0
  
  定义了以 `sync_refresh_period/8` 周期的同步重试次数。有助于防止同步消息丢失。`sync_retries` 的取值范围是 0 到 3。

- `sync_qlen_max` — 无符号长整型
  
  未发送的排队同步消息的硬限制。默认情况下为内存页面数量的 1/32，但实际上代表消息的数量。它能保护我们在发送速率低于队列速率时不会分配大量内存。

- `sync_sock_size` — 整型
  默认值：0
  
  设置 SNDBUF（主服务器）或 RCVBUF（备份服务器）的套接字限制。
  默认值为 0（保留系统默认设置）。

- `sync_ports` — 整型
  默认值：1
  
  主服务器和备份服务器用于同步流量的线程数量。每个线程将使用一个 UDP 端口，其中第 0 号线程使用默认端口 8848，而最后一个线程使用的端口号为 8848 + `sync_ports` - 1。

- `snat_reroute` — 布尔型
  - 0 — 禁用
  - 非 0 — 启用（默认）

  如果启用，则重新计算从真实服务器发出的 SNAT 包的路由，使其看起来像从调度器发出的一样。否则，它们会被当作由调度器转发一样进行路由。
  
  如果存在策略路由，则可能使得从调度器发出的包与被调度器转发的包有不同的路由路径。
  
  如果不存在策略路由，则重新计算的路由总是与原始路由相同，因此禁用 `snat_reroute` 并避免重新计算是一种优化手段。

- `sync_persist_mode` — 整型
  默认值：0
  
  控制使用持久性时的连接同步方式：
  
  - 0：所有类型的连接都会进行同步。
  
  - 1：根据连接类型尝试减少同步流量。对于持久服务，尽量避免常规连接的同步，仅对持久模板执行同步。
在这种情况下，对于TCP和SCTP，可能需要在备用服务器上启用`sloppy_tcp`和`sloppy_sctp`标志。对于非持久性服务，不应用此类优化，默认假设模式为0。

sync_version - 整数
默认 1

这是发送同步消息时所使用的同步协议版本。
0 选择原始的同步协议（版本0）。当向仅理解原始同步协议的遗留系统发送同步消息时应使用此版本。
1 选择当前的同步协议（版本1）。只要可能，应使用此版本。
具有此`sync_version`条目的内核能够接收同步协议版本1和版本2的消息。

run_estimation - 布尔值
0 - 禁用
非0 - 启用（默认）

如果禁用，则估算将被暂停，并且kthread任务将停止。
您始终可以通过将此值设置为1来重新启用估算，
但请注意，重新启用后的第一次估算是不准确的。
