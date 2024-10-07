SPDX 许可证标识符: GPL-2.0

====
L2TP
====

第二层隧道协议（L2TP）允许在 IP 网络上传输第二层（L2）帧。
本文档涵盖了内核的 L2TP 子系统。它为希望使用 L2TP 子系统的应用程序开发者提供了内核 API 的文档，并且提供了一些关于内部实现的技术细节，这些细节可能对内核开发者和维护者有用。

概述
========

内核的 L2TP 子系统实现了 L2TPv2 和 L2TPv3 的数据路径。L2TPv2 通过 UDP 进行传输。L2TPv3 可以通过 UDP 或直接通过 IP（协议号 115）进行传输。
L2TP RFC 定义了两种基本类型的 L2TP 数据包：控制数据包（“控制面”）和数据数据包（“数据面”）。内核只处理数据数据包。更复杂的控制数据包由用户空间处理。
一个 L2TP 隧道可以承载一个或多个 L2TP 会话。每个隧道与一个套接字相关联。每个会话与一个虚拟网络设备关联，例如 `pppN`、`l2tpethN`，数据帧通过这些设备进出 L2TP。L2TP 头中的字段用于识别隧道或会话以及它是控制数据包还是数据数据包。当使用 Linux 内核 API 设置隧道和会话时，我们只是在设置 L2TP 数据路径。所有关于控制协议的方面都应由用户空间处理。
这种职责划分导致了在建立隧道和会话时的一系列自然操作。该过程如下：

    1) 创建一个隧道套接字。通过该套接字与对端交换 L2TP 控制协议消息以建立隧道。
    2) 使用从对端获得的控制协议消息中的信息，在内核中创建隧道上下文。
    3) 通过隧道套接字与对端交换 L2TP 控制协议消息以建立会话。
    4) 使用从对端获得的控制协议消息中的信息，在内核中创建会话上下文。

L2TP API
=========

本节记录了 L2TP 子系统的每个用户空间 API。
隧道套接字
--------------

L2TPv2 始终使用 UDP。L2TPv3 可能使用 UDP 或 IP 封装。
为了创建一个供 L2TP 使用的隧道套接字，标准的 POSIX 套接字 API 被使用。
例如，对于使用 IPv4 地址和 UDP 封装的隧道：

    int sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

或者对于使用 IPv6 地址和 IP 封装的隧道：

    int sockfd = socket(AF_INET6, SOCK_DGRAM, IPPROTO_L2TP);

UDP 套接字编程在这里不需要详细介绍。
IPPROTO_L2TP 是由内核的 L2TP 子系统实现的一个 IP 协议类型。L2TPIP 套接字地址在 `include/uapi/linux/l2tp.h`_ 中定义为结构 sockaddr_l2tpip 和 sockaddr_l2tpip6。该地址包含 L2TP 隧道（连接）ID。为了使用 L2TP IP 封装，一个 L2TPv3 应用程序应该使用本地分配的隧道 ID 绑定 L2TPIP 套接字。当对等端的隧道 ID 和 IP 地址已知时，必须进行连接。
如果 L2TP 应用程序需要处理来自使用 L2TPIP 的对等端的 L2TPv3 隧道设置请求，它必须打开一个专门的 L2TPIP 套接字来监听这些请求，并使用隧道 ID 0 绑定该套接字，因为隧道设置请求是针对隧道 ID 0 的。
当其隧道套接字关闭时，L2TP 隧道及其所有会话将自动关闭。

Netlink API
-----------

L2TP 应用程序使用 netlink 来管理内核中的 L2TP 隧道和会话实例。L2TP 的 netlink API 定义在 `include/uapi/linux/l2tp.h`_ 中。
L2TP 使用 `通用 Netlink`_（GENL）。定义了几个命令：Create、Delete、Modify 和 Get 对于隧道和会话实例，例如 ``L2TP_CMD_TUNNEL_CREATE``。API 头文件列出了每个命令可以使用的 netlink 属性类型。
隧道和会话实例通过本地唯一的 32 位 ID 标识。L2TP 隧道 ID 由属性 ``L2TP_ATTR_CONN_ID`` 和 ``L2TP_ATTR_PEER_CONN_ID`` 给出，而 L2TP 会话 ID 则由属性 ``L2TP_ATTR_SESSION_ID`` 和 ``L2TP_ATTR_PEER_SESSION_ID`` 给出。如果 netlink 用于管理 L2TPv2 隧道和会话实例，则 L2TPv2 的 16 位隧道/会话 ID 在这些属性中被转换为 32 位值。
在 ``L2TP_CMD_TUNNEL_CREATE`` 命令中，``L2TP_ATTR_FD`` 告诉内核正在使用的隧道套接字文件描述符。如果没有指定，则内核会使用在 ``L2TP_ATTR_IP[6]_SADDR``、``L2TP_ATTR_IP[6]_DADDR``、``L2TP_ATTR_UDP_SPORT`` 和 ``L2TP_ATTR_UDP_DPORT`` 属性中设置的 IP 参数为隧道创建一个内核套接字。内核套接字用于实现未管理的 L2TPv3 隧道（iproute2 的 "ip l2tp" 命令）。如果指定了 ``L2TP_ATTR_FD``，则它必须是一个已经绑定并连接的套接字文件描述符。关于未管理隧道的更多信息，请参阅本文档后面的章节。
``L2TP_CMD_TUNNEL_CREATE`` 属性：

================== ======== ===
属性               是否必需  用途
================== ======== ===
CONN_ID            Y        设置隧道（连接）ID
PEER_CONN_ID       Y        设置对端隧道（连接）ID
PROTO_VERSION      Y        协议版本。2 或 3
ENCAP_TYPE         Y        封装类型：UDP 或 IP
FD                 N        隧道套接字文件描述符
UDP_CSUM           N        启用 IPv4 UDP 校验和。仅在 FD 未设置时使用
UDP_ZERO_CSUM6_TX  N        发送时将 IPv6 UDP 校验和置零。仅在 FD 未设置时使用
UDP_ZERO_CSUM6_RX  N        接收时将 IPv6 UDP 校验和置零。仅在 FD 未设置时使用
IP_SADDR           N        IPv4 源地址。仅在 FD 未设置时使用
IP_DADDR           N        IPv4 目的地址。仅在 FD 未设置时使用
================== ======== ===
UDP_SPORT          N        UDP源端口。仅在未设置FD时使用  
UDP_DPORT          N        UDP目标端口。仅在未设置FD时使用  
IP6_SADDR          N        IPv6源地址。仅在未设置FD时使用  
IP6_DADDR          N        IPv6目标地址。仅在未设置FD时使用  
DEBUG              N        调试标志  

================== ======== ===
属性              必需     用途
================== ======== ===
CONN_ID            Y        标识要销毁的隧道ID
================== ======== ===

``L2TP_CMD_TUNNEL_MODIFY`` 属性：  

================== ======== ===
属性              必需     用途
================== ======== ===
CONN_ID            Y        标识要修改的隧道ID  
DEBUG              N        调试标志  
================== ======== ===

``L2TP_CMD_TUNNEL_GET`` 属性：  

================== ======== ===
属性              必需     用途
================== ======== ===
CONN_ID            N        标识要查询的隧道ID  
在DUMP请求中忽略  
================== ======== ===
``L2TP_CMD_SESSION_CREATE`` 属性：

================== ======== ===
属性               必需     用途
================== ======== ===
CONN_ID            Y        设置父隧道ID
SESSION_ID         Y        设置会话ID
PEER_SESSION_ID    Y        设置父会话ID
PW_TYPE            Y        设置伪线类型
DEBUG              N        调试标志
RECV_SEQ           N        启用接收数据序列号
SEND_SEQ           N        启用发送数据序列号
LNS_MODE           N        启用LNS模式（自动启用数据序列号）
RECV_TIMEOUT       N        在重新排序接收到的数据包时等待的超时时间
L2SPEC_TYPE        N        设置层2特定子层类型（仅限L2TPv3）
================== ======== ===
COOKIE             N        设置可选的Cookie（仅限L2TPv3）
PEER_COOKIE        N        设置可选的对等端Cookie（仅限L2TPv3）
IFNAME             N        设置接口名称（仅限L2TPv3）

对于以太网会话类型，这将创建一个l2tpeth虚拟接口，然后可以根据需要进行配置。对于PPP会话类型，还必须打开并连接一个PPPoL2TP套接字，并将其映射到新的会话上。相关内容在后面的“PPPoL2TP套接字”部分中讨论。

``L2TP_CMD_SESSION_DESTROY``属性：

================== ======== ===
属性                必需     用途
================== ======== ===
CONN_ID            Y        识别要销毁的会话的父隧道ID
SESSION_ID         Y        识别要销毁的会话ID
IFNAME             N        通过接口名称识别会话。如果设置，则此属性会覆盖任何CONN_ID和SESSION_ID属性。目前仅支持L2TPv3以太网会话
================== ======== ===

``L2TP_CMD_SESSION_MODIFY``属性：

================== ======== ===
属性                必需     用途
================== ======== ===
CONN_ID            Y        识别要修改的会话的父隧道ID
SESSION_ID         Y        识别要修改的会话ID
IFNAME             N        通过接口名称识别会话。如果设置，则此属性会覆盖任何CONN_ID和SESSION_ID属性。目前仅支持L2TPv3以太网会话
================== ======== ===
```
调试标志              N        调试标志
接收序列号            N        启用接收数据序列号
发送序列号            N        启用发送数据序列号
LNS模式              N        启用LNS模式（自动启用数据序列号）
接收超时             N        重新排序接收到的数据包时的超时时间
================== ======== ===

`L2TP_CMD_SESSION_GET` 属性：-

================== ======== ===
属性                  必需     用途
================== ======== ===
CONN_ID              N        识别要查询的隧道ID
对于DUMP请求忽略此字段
SESSION_ID           N        识别要查询的会话ID
对于DUMP请求忽略此字段
IFNAME               N        通过接口名称识别会话
```
如果设置了该值，这将覆盖任何CONN_ID和SESSION_ID属性。对于DUMP请求会被忽略。目前仅支持L2TPv3以太网会话。

================== ======== ===

应用程序开发人员应参考 `include/uapi/linux/l2tp.h`_ 获取Netlink命令和属性定义。
使用libmnl_的示例用户空间代码：

  - 打开L2TP Netlink套接字::

        struct nl_sock *nl_sock;
        int l2tp_nl_family_id;

        nl_sock = nl_socket_alloc();
        genl_connect(nl_sock);
        genl_id = genl_ctrl_resolve(nl_sock, L2TP_GENL_NAME);

  - 创建隧道::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给genl套接字 */
        nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
        nlh->nlmsg_seq = seq;

        gnlh = mnl_nlmsg_put_extra_header(nlh, sizeof(*gnlh));
        gnlh->cmd = L2TP_CMD_TUNNEL_CREATE;
        gnlh->version = L2TP_GENL_VERSION;
        gnlh->reserved = 0;

        mnl_attr_put_u32(nlh, L2TP_ATTR_FD, tunl_sock_fd);
        mnl_attr_put_u32(nlh, L2TP_ATTR_CONN_ID, tid);
        mnl_attr_put_u32(nlh, L2TP_ATTR_PEER_CONN_ID, peer_tid);
        mnl_attr_put_u8(nlh, L2TP_ATTR_PROTO_VERSION, protocol_version);
        mnl_attr_put_u16(nlh, L2TP_ATTR_ENCAP_TYPE, encap);

  - 创建会话::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给genl套接字 */
        nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
        nlh->nlmsg_seq = seq;

        gnlh = mnl_nlmsg_put_extra_header(nlh, sizeof(*gnlh));
        gnlh->cmd = L2TP_CMD_SESSION_CREATE;
        gnlh->version = L2TP_GENL_VERSION;
        gnlh->reserved = 0;

        mnl_attr_put_u32(nlh, L2TP_ATTR_CONN_ID, tid);
        mnl_attr_put_u32(nlh, L2TP_ATTR_PEER_CONN_ID, peer_tid);
        mnl_attr_put_u32(nlh, L2TP_ATTR_SESSION_ID, sid);
        mnl_attr_put_u32(nlh, L2TP_ATTR_PEER_SESSION_ID, peer_sid);
        mnl_attr_put_u16(nlh, L2TP_ATTR_PW_TYPE, pwtype);
        /* 在创建会话期间可以使用其他Netlink属性设置其他会话选项 -- 参见l2tp.h */

  - 删除会话::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给genl套接字 */
        nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
        nlh->nlmsg_seq = seq;

        gnlh = mnl_nlmsg_put_extra_header(nlh, sizeof(*gnlh));
        gnlh->cmd = L2TP_CMD_SESSION_DELETE;
        gnlh->version = L2TP_GENL_VERSION;
        gnlh->reserved = 0;

        mnl_attr_put_u32(nlh, L2TP_ATTR_CONN_ID, tid);
        mnl_attr_put_u32(nlh, L2TP_ATTR_SESSION_ID, sid);

  - 删除隧道及其所有会话（如果有）::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给genl套接字 */
        nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
        nlh->nlmsg_seq = seq;

        gnlh = mnl_nlmsg_put_extra_header(nlh, sizeof(*gnlh));
        gnlh->cmd = L2TP_CMD_TUNNEL_DELETE;
        gnlh->version = L2TP_GENL_VERSION;
        gnlh->reserved = 0;

        mnl_attr_put_u32(nlh, L2TP_ATTR_CONN_ID, tid);

PPPoL2TP会话套接字API
---------------------------

对于PPP会话类型，必须打开并连接到L2TP会话的PPPoL2TP套接字。
在创建PPPoL2TP套接字时，应用程序通过socket connect()调用向内核提供关于隧道和会话的信息。提供源和目的隧道及会话ID，以及UDP或L2TPIP套接字的文件描述符。参见 `include/linux/if_pppol2tp.h`_ 中的struct pppol2tp_addr。由于历史原因，不幸的是，对于L2TPv2/L2TPv3 IPv4/IPv6隧道有稍微不同的地址结构，用户空间必须使用与隧道套接字类型匹配的适当结构。
用户空间可以通过在PPPoX套接字上调用setsockopt和ioctl来控制隧道或会话的行为。以下套接字选项是支持的：-

=========   ===========================================================
DEBUG       调试消息类别的位掩码。见下文
SENDSEQ     - 0 => 不发送带序列号的数据包
            - 1 => 发送带序列号的数据包
RECVSEQ     - 0 => 接收数据包序列号可选
            - 1 => 丢弃没有序列号的数据包
LNSMODE     - 0 => 作为LAC运行
- 1 => 作为LNS运行
REORDERTO   重新排序超时时间（毫秒）。如果为0，则不尝试重新排序
=========   ===========================================================

除了标准的PPP ioctl外，还提供了PPPIOCGL2TPSTATS以使用适当的隧道或会话的PPPoX套接字从内核检索隧道和会话统计信息。
示例用户空间代码：

  - 创建会话PPPoX数据套接字::

        /* 输入：已经绑定（sockname和peername）的L2TP隧道UDP套接字`tunnel_fd`，否则它将不会准备好 */
```c
// 定义一个 sockaddr_pppol2tp 结构体变量 sax
struct sockaddr_pppol2tp sax;
int session_fd; // 会话文件描述符
int ret; // 返回值

// 创建一个 PPPoX 套接字，用于 L2TP 会话
session_fd = socket(AF_PPPOX, SOCK_DGRAM, PX_PROTO_OL2TP);
if (session_fd < 0)
    return -errno;

// 设置 sockaddr_pppol2tp 结构体中的字段
sax.sa_family = AF_PPPOX;
sax.sa_protocol = PX_PROTO_OL2TP;
sax.pppol2tp.fd = tunnel_fd; // 隧道的 UDP/L2TP 文件描述符
sax.pppol2tp.addr.sin_addr.s_addr = addr->sin_addr.s_addr;
sax.pppol2tp.addr.sin_port = addr->sin_port;
sax.pppol2tp.addr.sin_family = AF_INET;
sax.pppol2tp.s_tunnel = tunnel_id;
sax.pppol2tp.s_session = session_id;
sax.pppol2tp.d_tunnel = peer_tunnel_id;
sax.pppol2tp.d_session = peer_session_id;

// 连接到 PPPoL2TP 会话
ret = connect(session_fd, (struct sockaddr *)&sax, sizeof(sax));
if (ret < 0) {
    close(session_fd);
    return -errno;
}

return session_fd;

// L2TP 控制包仍然可以在 `tunnel_fd` 上读取
// 创建 PPP 通道
/* 输入：创建的 PPPoX 数据套接字 `session_fd` */
int ppp_chan_fd;
int chindx;
int ret;

// 获取 PPP 通道索引
ret = ioctl(session_fd, PPPIOCGCHAN, &chindx);
if (ret < 0)
    return -errno;

// 打开 PPP 设备文件
ppp_chan_fd = open("/dev/ppp", O_RDWR);
if (ppp_chan_fd < 0)
    return -errno;

// 关联通道索引到 PPP 通道
ret = ioctl(ppp_chan_fd, PPPIOCATTCHAN, &chindx);
if (ret < 0) {
    close(ppp_chan_fd);
    return -errno;
}

return ppp_chan_fd;

// PPP LCP 帧可以在 `ppp_chan_fd` 上读取
// 创建 PPP 接口
/* 输入：创建的 PPP 通道 `ppp_chan_fd` */
int ifunit = -1;
int ppp_if_fd;
int ret;

// 打开 PPP 设备文件
ppp_if_fd = open("/dev/ppp", O_RDWR);
if (ppp_if_fd < 0)
    return -errno;

// 分配一个新的接口单元号
ret = ioctl(ppp_if_fd, PPPIOCNEWUNIT, &ifunit);
if (ret < 0) {
    close(ppp_if_fd);
    return -errno;
}

// 连接 PPP 通道到指定的接口单元号
ret = ioctl(ppp_chan_fd, PPPIOCCONNECT, &ifunit);
if (ret < 0) {
    close(ppp_if_fd);
    return -errno;
}

return ppp_if_fd;

// IPCP/IPv6CP PPP 帧可以在 `ppp_if_fd` 上读取
// 可以通过 netlink 的 RTM_NEWLINK、RTM_NEWADDR、RTM_NEWROUTE 或 ioctl 的 SIOCSIFMTU、SIOCSIFADDR、SIOCSIFDSTADDR、SIOCSIFNETMASK、SIOCSIFFLAGS 或者使用 `ip` 命令来配置 ppp<ifunit> 接口
// 桥接具有 PPP 伪线类型的 L2TP 会话（也称为 L2TP 隧道切换或 L2TP 多跳）
// 支持将两个 L2TP 会话的 PPP 通道桥接起来
/* 输入：创建的 PPPoX 数据套接字 `session_fd1` 和 `session_fd2` */
int ppp_chan_fd;
int chindx1;
int chindx2;
int ret;

// 获取第一个会话的通道索引
ret = ioctl(session_fd1, PPPIOCGCHAN, &chindx1);
if (ret < 0)
    return -errno;

// 获取第二个会话的通道索引
ret = ioctl(session_fd2, PPPIOCGCHAN, &chindx2);
if (ret < 0)
    return -errno;

// 打开 PPP 设备文件
ppp_chan_fd = open("/dev/ppp", O_RDWR);
if (ppp_chan_fd < 0)
    return -errno;

// 关联第一个通道索引到 PPP 通道
ret = ioctl(ppp_chan_fd, PPPIOCATTCHAN, &chindx1);
if (ret < 0) {
    close(ppp_chan_fd);
    return -errno;
}

// 将第二个通道桥接到 PPP 通道
ret = ioctl(ppp_chan_fd, PPPIOCBRIDGECHAN, &chindx2);
close(ppp_chan_fd);
if (ret < 0)
    return -errno;

return 0;

// 当桥接 PPP 通道时，PPP 会话不会本地终止，并且不会创建本地 PPP 接口。PPP 帧在一个通道上到达后会直接传递到另一个通道，反之亦然。
```
PPP通道不需要保持打开状态。只有会话PPPoX数据套接字需要保持打开。

更广泛地说，同样可以以类似的方式桥接PPPoL2TP PPP通道与其他类型的PPP通道，例如PPPoE。
有关PPP方面的更多详细信息，请参阅ppp_generic.rst。

旧的L2TPv2专用API
-------------------

当L2TP最初在2.6.23版中加入Linux内核时，它仅实现了L2TPv2，并且没有包含netlink API。相反，内核中的隧道和会话实例是直接通过仅使用PPPoL2TP套接字进行管理的。PPPoL2TP套接字的使用如“PPPoL2TP会话套接字API”部分所述，但在连接套接字时隧道和会话实例会被自动创建，而不是通过单独的netlink请求创建：

- 隧道由一个专用的PPPoL2TP套接字管理，该套接字连接到（无效的）会话ID 0。当PPPoL2TP隧道管理套接字连接时，L2TP隧道实例被创建；当套接字关闭时，该实例被销毁。
- 当一个PPPoL2TP套接字连接到非零会话ID时，会在内核中创建会话实例。会话参数通过setsockopt设置。当套接字关闭时，L2TP会话实例被销毁。

此API仍然得到支持，但不建议使用。相反，新的L2TPv2应用程序应使用netlink首先创建隧道和会话，然后再为会话创建一个PPPoL2TP套接字。

未管理的L2TPv3隧道
------------------------

内核的L2TP子系统还支持静态（未管理的）L2TPv3隧道。未管理的隧道没有用户空间隧道套接字，并且与对等体之间不交换控制消息来设置隧道；隧道在隧道两端手动配置。所有配置都通过netlink完成。在这种情况下，不需要L2TP用户空间应用程序——隧道套接字由内核创建，并使用`L2TP_CMD_TUNNEL_CREATE` netlink请求中发送的参数进行配置。`iproute2`的`ip`工具具有用于管理静态L2TPv3隧道的命令；执行`ip l2tp help`获取更多信息。

调试
-------

L2TP子系统通过debugfs文件系统提供了一系列调试接口。
要访问这些接口，首先必须挂载debugfs文件系统：

    # mount -t debugfs debugfs /debug

然后可以访问l2tp目录下的文件，以提供当前存在于内核中的隧道和会话上下文摘要：

    # cat /debug/l2tp/tunnels

应用程序不应使用debugfs文件来获取L2TP状态信息，因为文件格式可能会发生变化。其目的是为了提供额外的调试信息以帮助诊断问题。应用程序应改用netlink API。

此外，L2TP子系统使用标准内核事件跟踪API实现了跟踪点。 可以通过以下方式查看可用的L2TP事件：

    # find /debug/tracing/events/l2tp

最后，出于向后兼容性的考虑，也提供了/proc/net/pppol2tp，它仅列出关于L2TPv2隧道和会话的信息。不建议使用。
内部实现
=======================

本节适用于内核开发者和维护者
套接字
-------

UDP 套接字由网络核心实现。当使用 UDP 套接字创建 L2TP 隧道时，该套接字将通过设置 encap_rcv 和 encap_destroy 回调函数来配置为封装的 UDP 套接字。当在套接字上收到数据包时会调用 l2tp_udp_encap_recv。当用户空间关闭套接字时会调用 l2tp_udp_encap_destroy。
L2TPIP 套接字在 `net/l2tp/l2tp_ip.c`_ 和 `net/l2tp/l2tp_ip6.c`_ 中实现。
隧道
-------

内核为每个 L2TP 隧道保持一个 l2tp_tunnel 结构体上下文。l2tp_tunnel 总是与一个 UDP 或 L2TP/IP 套接字关联，并且维护了一个隧道中的会话列表。当隧道首次注册到 L2TP 核心时，会增加套接字的引用计数。这确保了在 L2TP 的数据结构引用该套接字时，套接字不会被移除。
隧道由唯一的隧道 ID 标识。对于 L2TPv2，ID 是 16 位的；对于 L2TPv3，则是 32 位的。内部存储时，ID 是 32 位的值。
隧道按网络保存在一个列表中，以隧道 ID 作为索引。隧道 ID 命名空间由 L2TPv2 和 L2TPv3 共享。可以从套接字的 sk_user_data 推导出隧道上下文。
处理隧道套接字关闭可能是 L2TP 实现中最棘手的部分。如果用户空间关闭了一个隧道套接字，那么必须关闭并销毁 L2TP 隧道及其所有会话。由于隧道上下文持有对隧道套接字的引用，因此直到隧道使用 sock_put 释放其套接字之前，套接字的 sk_destruct 不会被调用。对于 UDP 套接字，当用户空间关闭隧道套接字时，会调用套接字的 encap_destroy 处理程序，L2TP 使用它来启动关闭隧道的操作。对于 L2TPIP 套接字，套接字的关闭处理程序会启动相同的隧道关闭操作。首先关闭所有会话。每个会话会丢弃其隧道引用。当隧道引用计数变为零时，隧道会释放其套接字引用。当套接字最终被销毁时，其 sk_destruct 最终会释放 L2TP 隧道上下文。
会话
--------

内核为每个会话保持一个 l2tp_session 结构体上下文。每个会话都有私有数据，用于存储特定于会话类型的数据。对于 L2TPv2，会话总是承载 PPP 流量。对于 L2TPv3，会话可以承载以太网帧（以太网伪线）或其他数据类型，如 PPP、ATM、HDLC 或帧中继。目前 Linux 只实现了以太网和 PPP 会话类型。
某些 L2TP 会话类型有一个套接字（PPP 伪线），而其他类型没有（以太网伪线）。因此我们不能使用套接字的引用计数作为会话上下文的引用计数。因此 L2TP 实现在会话上下文中维护了自己的内部引用计数。
像隧道一样，L2TP 会话也由唯一的会话 ID 标识。与隧道 ID 类似，会话 ID 对于 L2TPv2 是 16 位的，对于 L2TPv3 是 32 位的。内部存储时，ID 是 32 位的值。
会话持有其父隧道的引用，以确保在有一个或多个会话引用该隧道时，隧道仍然存在。会话被保存在一个按会话ID索引的每隧道列表中。L2TPv3会话还被保存在一个按会话ID索引的每网络列表中，因为L2TPv3会话ID在整个所有隧道中是唯一的，并且L2TPv3数据包的头部不包含隧道ID。因此，当无法从隧道套接字推导出隧道上下文时，需要此列表来查找与收到的数据包相关联的会话上下文。

尽管L2TPv3 RFC规定L2TPv3会话ID不受隧道范围限制，但内核对于L2TPv3 UDP隧道并不强制执行这一点，并且不会将L2TPv3 UDP隧道的会话添加到每网络会话列表中。在UDP接收代码中，我们必须信任使用隧道套接字的sk_user_data可以识别隧道，并在隧道的会话列表而不是每网络会话列表中查找会话。

PPP
---

`net/l2tp/l2tp_ppp.c`_ 实现了PPPoL2TP套接字家族。每个PPP会话都有一个PPPoL2TP套接字。
PPPoL2TP套接字的sk_user_data引用了l2tp_session。
用户空间通过PPPoL2TP套接字发送和接收PPP数据包。只有PPP控制帧通过此套接字传递：PPP数据包完全由内核处理，通过内核PPP子系统的PPP通道接口在L2TP会话与其关联的`pppN`网卡之间传输。
L2TP PPP实现通过关闭其对应的L2TP会话来处理PPPoL2TP套接字的关闭。这很复杂，因为它必须考虑与netlink会话创建/销毁请求以及pppol2tp_connect尝试重新连接正在关闭的会话的竞争情况。与隧道不同，PPP会话不会持有其关联套接字的引用，因此代码必须在必要时使用sock_hold。详细信息请参见提交记录3d609342cc04129ff7568e19316ce3d7451a27e8。

以太网
------

`net/l2tp/l2tp_eth.c`_ 实现了L2TPv3以太网伪线。它为每个会话管理一个网卡。
L2TP以太网会话由netlink请求创建和销毁，或者在隧道销毁时销毁。与PPP会话不同，以太网会话没有关联的套接字。

杂项
====

RFC
---

内核代码实现了以下RFC中指定的数据路径功能：

======= =============== ===================================
RFC2661 L2TPv2          https://tools.ietf.org/html/rfc2661
RFC3931 L2TPv3          https://tools.ietf.org/html/rfc3931
RFC4719 L2TPv3以太网    https://tools.ietf.org/html/rfc4719
======= =============== ===================================

实现
----

许多开源应用程序使用了L2TP内核子系统：

============ ==============================================
iproute2     https://github.com/shemminger/iproute2
go-l2tp      https://github.com/katalix/go-l2tp
tunneldigger https://github.com/wlanslovenija/tunneldigger
xl2tpd       https://github.com/xelerance/xl2tpd
============ ==============================================

限制
----

当前实现有一些限制：

1) 不能使用具有相同五元组地址的多个UDP套接字。内核的隧道上下文是通过与套接字关联的私有数据来识别的，因此重要的是每个套接字都通过其地址唯一标识。
2) 与 openvswitch 的接口尚未实现。将 OVS 以太网端口和 VLAN 端口映射到 L2TPv3 隧道中可能是有用的。

3) VLAN 伪线使用带有 VLAN 子接口的 `l2tpethN` 接口实现。由于 L2TPv3 VLAN 伪线仅携带一个 VLAN，因此对于每个 VLAN 会话使用单一的网络设备可能比使用 `l2tpethN` 和 `l2tpethN`:M 对更好。为此添加了 netlink 属性 `L2TP_ATTR_VLAN_ID`，但该功能从未实现。

测试
----

未管理的 L2TPv3 以太网功能由内核内置的自测程序进行测试。请参阅 `tools/testing/selftests/net/l2tp.sh`_。
另一个测试套件 l2tp-ktest_ 覆盖了所有 L2TP API 和隧道/会话类型。未来可能会将其集成到内核内置的 L2TP 自测程序中。

.. 链接
.. _Generic Netlink: generic_netlink.html
.. _libmnl: https://www.netfilter.org/projects/libmnl
.. _include/uapi/linux/l2tp.h: ../../../include/uapi/linux/l2tp.h
.. _include/linux/if_pppol2tp.h: ../../../include/linux/if_pppol2tp.h
.. _net/l2tp/l2tp_ip.c: ../../../net/l2tp/l2tp_ip.c
.. _net/l2tp/l2tp_ip6.c: ../../../net/l2tp/l2tp_ip6.c
.. _net/l2tp/l2tp_ppp.c: ../../../net/l2tp/l2tp_ppp.c
.. _net/l2tp/l2tp_eth.c: ../../../net/l2tp/l2tp_eth.c
.. _tools/testing/selftests/net/l2tp.sh: ../../../tools/testing/selftests/net/l2tp.sh
.. _l2tp-ktest: https://github.com/katalix/l2tp-ktest
