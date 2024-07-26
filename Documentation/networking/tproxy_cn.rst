此功能为当前内核添加了类似 Linux 2.2 的透明代理支持。

要使用它，您需要在内核配置中启用套接字匹配 (`socket match`) 和 `TPROXY` 目标。此外，您还需要策略路由，请确保也启用它。
从 Linux 4.18 开始，nf_tables 中也提供了透明代理支持。

1. 让非本地套接字工作
======================

思路是识别出目的地地址与本机套接字匹配的数据包，并将数据包标记设置为某个值：

```shell
# iptables -t mangle -N DIVERT
# iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT
# iptables -t mangle -A DIVERT -j MARK --set-mark 1
# iptables -t mangle -A DIVERT -j ACCEPT
```

或者，您可以在 nf_tables 中使用以下命令实现相同的目的：
```shell
# nft add table filter
# nft add chain filter divert "{ type filter hook prerouting priority -150; }"
# nft add rule filter divert meta l4proto tcp socket transparent 1 meta mark set 1 accept
```

然后，通过策略路由根据该值进行匹配，使这些数据包被本地递送：
```shell
# ip rule add fwmark 1 lookup 100
# ip route add local 0.0.0.0/0 dev lo table 100
```

由于 IPv4 路由输出代码中的某些限制，您需要修改应用程序以允许其从非本地 IP 地址发送数据报。您需要做的就是在调用 `bind` 之前启用 `(SOL_IP, IP_TRANSPARENT)` 套接字选项：
```c
fd = socket(AF_INET, SOCK_STREAM, 0);
/* - 8< -*/
int value = 1;
setsockopt(fd, SOL_IP, IP_TRANSPARENT, &value, sizeof(value));
/* - 8< -*/
name.sin_family = AF_INET;
name.sin_port = htons(0xCAFE);
name.sin_addr.s_addr = htonl(0xDEADBEEF);
bind(fd, &name, sizeof(name));
```

一个简单的 netcat 补丁可在此处获取：
http://people.netfilter.org/hidden/tproxy/netcat-ip_transparent-support.patch

2. 重定向流量
=============

透明代理通常涉及在路由器上“拦截”流量。这通常是通过 `iptables` 的 `REDIRECT` 目标完成的；但是，这种方法存在严重的局限性。其中一个主要问题是它会实际修改数据包以更改目标地址——这在某些情况下可能不可接受。（例如考虑为 UDP 进行代理：您将无法找出原始的目标地址。即使在 TCP 情况下，获取原始的目标地址也是有风险的。）

`TPROXY` 目标提供了类似的功能，但不依赖于网络地址转换（NAT）。只需像这样添加规则到上面的 iptables 规则集中：
```shell
# iptables -t mangle -A PREROUTING -p tcp --dport 80 -j TPROXY \
      --tproxy-mark 0x1/0x1 --on-port 50080
```

或者，在 nf_tables 中添加如下规则：
```shell
# nft add rule filter divert tcp dport 80 tproxy to :50080 meta mark set 1 accept
```

请注意，为了使此功能生效，您需要修改代理以启用 `(SOL_IP, IP_TRANSPARENT)` 用于监听套接字。
作为示例实现，tcprdr 可在此处获取：
https://git.breakpoint.cc/cgit/fw/tcprdr.git/
此工具由 Florian Westphal 编写，并在 nf_tables 实现期间用于测试。

3. iptables 和 nf_tables 扩展
==============================

要使用 tproxy，您需要为 iptables 编译以下模块：

- `NETFILTER_XT_MATCH_SOCKET`
- `NETFILTER_XT_TARGET_TPROXY`

对于 nf_tables，则需要以下模块：

- `NFT_SOCKET`
- `NFT_TPROXY`

4. 应用程序支持
================

4.1. Squid
----------

Squid 3.HEAD 已内置支持。要使用它，请在配置时传递 `--enable-linux-netfilter`，并在您使用 `TPROXY` iptables 目标重定向流量的 HTTP 监听器上设置 `tproxy` 选项。
更多信息请参阅 Squid 维基上的以下页面：http://wiki.squid-cache.org/Features/Tproxy4
