SPDX许可证标识符: GPL-2.0

=========================
透明代理支持
=========================

此功能为当前内核添加了类似于Linux 2.2的透明代理支持。
要使用它，需要在内核配置中启用套接字匹配（socket match）和TPROXY目标。您还需要策略路由，因此请确保也启用它。
从Linux 4.18开始，透明代理支持也在nf_tables中可用。

1. 让非本地套接字工作
================================

思路是，您识别出目的地地址与本机上套接字相匹配的数据包，并将数据包标记设置为特定值：

    # iptables -t mangle -N DIVERT
    # iptables -t mangle -A PREROUTING -p tcp -m socket -j DIVERT
    # iptables -t mangle -A DIVERT -j MARK --set-mark 1
    # iptables -t mangle -A DIVERT -j ACCEPT

或者，您也可以通过以下命令在nft中实现相同的功能：

    # nft add table filter
    # nft add chain filter divert "{ type filter hook prerouting priority -150; }"
    # nft add rule filter divert meta l4proto tcp socket transparent 1 meta mark set 1 accept

然后通过策略路由匹配该值，以使这些数据包本地交付：

    # ip rule add fwmark 1 lookup 100
    # ip route add local 0.0.0.0/0 dev lo table 100

由于IPv4路由输出代码中的某些限制，您需要修改应用程序以允许其从非本地IP地址发送数据报。您只需在调用bind之前启用(SOL_IP, IP_TRANSPARENT)套接字选项即可：

    fd = socket(AF_INET, SOCK_STREAM, 0);
    /* - 8< -*/
    int value = 1;
    setsockopt(fd, SOL_IP, IP_TRANSPARENT, &value, sizeof(value));
    /* - 8< -*/
    name.sin_family = AF_INET;
    name.sin_port = htons(0xCAFE);
    name.sin_addr.s_addr = htonl(0xDEADBEEF);
    bind(fd, &name, sizeof(name));

一个简单的适用于netcat的补丁可在这里找到：
http://people.netfilter.org/hidden/tproxy/netcat-ip_transparent-support.patch

2. 重定向流量
======================

透明代理通常涉及在路由器上“拦截”流量。这通常是通过iptables的REDIRECT目标完成的；然而，这种方法存在严重的局限性。主要问题之一是它实际上会修改数据包以更改目标地址——这在某些情况下可能不可接受。（例如，考虑代理UDP：您将无法找出原始的目标地址。即使在TCP的情况下，获取原始目标地址也可能出现问题。）

TPROXY目标提供了类似的功能，但不依赖于NAT。只需像这样向iptables规则集中添加规则即可：

    # iptables -t mangle -A PREROUTING -p tcp --dport 80 -j TPROXY \
      --tproxy-mark 0x1/0x1 --on-port 50080

或者向nft添加如下规则：

    # nft add rule filter divert tcp dport 80 tproxy to :50080 meta mark set 1 accept

请注意，要使此功能生效，您需要修改代理以启用(SOL_IP, IP_TRANSPARENT)用于监听套接字。
作为一个示例实现，tcprdr可在此处找到：
https://git.breakpoint.cc/cgit/fw/tcprdr.git/
这个工具由Florian Westphal编写，并且在nf_tables实现过程中用于测试。

3. iptables和nf_tables扩展
====================================

要使用tproxy，您需要编译以下模块供iptables使用：

 - NETFILTER_XT_MATCH_SOCKET
 - NETFILTER_XT_TARGET_TPROXY

或者对于nf_tables，需要以下模块：

 - NFT_SOCKET
 - NFT_TPROXY

4. 应用程序支持
======================

4.1. Squid
----------

Squid 3.HEAD已内置支持。要使用它，请在configure时传递'--enable-linux-netfilter'并在使用TPROXY iptables目标重定向流量的HTTP监听器上设置'tproxy'选项。
更多信息，请参阅Squid wiki上的以下页面：http://wiki.squid-cache.org/Features/Tproxy4
