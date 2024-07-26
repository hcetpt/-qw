### SPDX 许可证标识符：GPL-2.0

====
L2TP
====

第二层隧道协议（L2TP）允许在IP网络上对L2帧进行隧道传输。
本文档涵盖了内核的L2TP子系统。它为希望使用L2TP子系统的应用程序开发者记录了内核API，并且提供了一些关于内部实现的技术细节，这些可能对于内核开发者和维护者有用。

概述
========

内核的L2TP子系统实现了L2TPv2和L2TPv3的数据路径。L2TPv2通过UDP承载。L2TPv3可以通过UDP或直接通过IP（协议号115）承载。
L2TP RFC定义了两种基本类型的L2TP数据包：控制数据包（“控制平面”）和数据数据包（“数据平面”）。内核仅处理数据数据包。更复杂的控制数据包由用户空间处理。
一个L2TP隧道可以承载一个或多个L2TP会话。每个隧道与一个套接字关联。每个会话与一个虚拟网络设备相关联，例如`pppN`、`l2tpethN`，数据帧通过这些设备进出L2TP。L2TP头中的字段用于识别隧道或会话以及它是控制数据包还是数据数据包。当使用Linux内核API设置隧道和会话时，我们实际上只是设置了L2TP的数据路径。所有与控制协议相关的方面都应在用户空间中处理。
这种职责划分导致在建立隧道和会话时出现自然的操作顺序。流程如下：

1. 创建一个隧道套接字。通过该套接字与对等体交换L2TP控制协议消息以建立隧道。
2. 使用从对等体获得的信息，在内核中创建隧道上下文。
3. 通过隧道套接字与对等体交换L2TP控制协议消息以建立会话。
4. 使用从对等体获得的信息，在内核中创建会话上下文。

L2TP API
=========

本节记录了L2TP子系统的每个用户空间API。
### 隧道套接字

L2TPv2 总是使用 UDP。L2TPv3 可能使用 UDP 或 IP 封装。
为了创建一个供 L2TP 使用的隧道套接字，标准 POSIX 套接字 API 被使用。
例如，对于使用 IPv4 地址和 UDP 封装的隧道：

    int sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

或者对于使用 IPv6 地址和 IP 封装的隧道：

    int sockfd = socket(AF_INET6, SOCK_DGRAM, IPPROTO_L2TP);

UDP 套接字编程在这里不需要详细说明。
IPPROTO_L2TP 是由内核的 L2TP 子系统实现的一种 IP 协议类型。L2TPIP 套接字地址在 `include/uapi/linux/l2tp.h`_ 中定义为结构 `sockaddr_l2tpip` 和 `sockaddr_l2tpip6`。该地址包括 L2TP 隧道（连接）ID。要使用 L2TP IP 封装，L2TPv3 应用程序应该使用本地分配的隧道 ID 绑定 L2TPIP 套接字。当知道了对等方的隧道 ID 和 IP 地址时，必须执行连接操作。
如果 L2TP 应用程序需要处理来自使用 L2TPIP 的对等方的 L2TPv3 隧道设置请求，则必须打开一个专用的 L2TPIP 套接字来监听这些请求，并使用隧道 ID 0 绑定套接字，因为隧道设置请求被发送到隧道 ID 0。
当其隧道套接字关闭时，L2TP 隧道及其所有会话将自动关闭。

### Netlink API

L2TP 应用程序使用 Netlink 来管理内核中的 L2TP 隧道和会话实例。L2TP 的 Netlink API 在 `include/uapi/linux/l2tp.h`_ 中定义。
L2TP 使用 `通用 Netlink`_ (GENL)。定义了几个命令：创建、删除、修改和获取隧道和会话实例，例如 `L2TP_CMD_TUNNEL_CREATE`。API 头文件列出了可以与每个命令一起使用的 Netlink 属性类型。
隧道和会话实例通过本地唯一的 32 位 ID 来标识。L2TP 隧道 ID 由 `L2TP_ATTR_CONN_ID` 和 `L2TP_ATTR_PEER_CONN_ID` 属性给出，而 L2TP 会话 ID 由 `L2TP_ATTR_SESSION_ID` 和 `L2TP_ATTR_PEER_SESSION_ID` 属性给出。如果使用 Netlink 管理 L2TPv2 隧道和会话实例，则 L2TPv2 的 16 位隧道/会话 ID 在这些属性中被转换为 32 位值。
在 `L2TP_CMD_TUNNEL_CREATE` 命令中，`L2TP_ATTR_FD` 告诉内核正在使用的隧道套接字文件描述符。如果没有指定，内核将为隧道创建一个内核套接字，使用在 `L2TP_ATTR_IP[6]_SADDR`、`L2TP_ATTR_IP[6]_DADDR`、`L2TP_ATTR_UDP_SPORT`、`L2TP_ATTR_UDP_DPORT` 属性中设置的 IP 参数。内核套接字用于实现未管理的 L2TPv3 隧道（iproute2 的 "ip l2tp" 命令）。如果指定了 `L2TP_ATTR_FD`，则它必须是一个已经绑定并连接的套接字文件描述符。关于未管理隧道的更多信息将在本文档后面提供。
``L2TP_CMD_TUNNEL_CREATE`` 属性：

================== ======== ===
属性                必需     用途
================== ======== ===
CONN_ID            Y        设置隧道（连接）ID
PEER_CONN_ID       Y        设置对端隧道（连接）ID
PROTO_VERSION      Y        协议版本。2 或 3
ENCAP_TYPE         Y        封装类型：UDP 或 IP
FD                 N        隧道套接字文件描述符
UDP_CSUM           N        启用IPv4 UDP校验和。仅在未设置FD时使用
UDP_ZERO_CSUM6_TX  N        在传输时将IPv6 UDP校验和置零。仅在未设置FD时使用
UDP_ZERO_CSUM6_RX  N        在接收时将IPv6 UDP校验和置零。仅在未设置FD时使用
IP_SADDR           N        IPv4源地址。仅在未设置FD时使用
IP_DADDR           N        IPv4目的地址。仅在未设置FD时使用
================== ======== ===
UDP_SPORT          N        UDP源端口。仅在未设置FD时使用  
UDP_DPORT          N        UDP目标端口。仅在未设置FD时使用  
IP6_SADDR          N        IPv6源地址。仅在未设置FD时使用  
IP6_DADDR          N        IPv6目标地址。仅在未设置FD时使用  
DEBUG              N        调试标志  

``L2TP_CMD_TUNNEL_DESTROY``属性：  

================== ======== ===
属性                  必需    用途
================== ======== ===
CONN_ID            Y        标识要销毁的隧道ID
================== ======== ===

``L2TP_CMD_TUNNEL_MODIFY``属性：  

================== ======== ===
属性                  必需    用途
================== ======== ===
CONN_ID            Y        标识要修改的隧道ID  
DEBUG              N        调试标志  
================== ======== ===

``L2TP_CMD_TUNNEL_GET``属性：  

================== ======== ===
属性                  必需    用途
================== ======== ===
CONN_ID            N        标识要查询的隧道ID  
在DUMP请求中被忽略  
================== ======== ===
```L2TP_CMD_SESSION_CREATE``` 属性：

| 属性          | 必需 | 用途                                                         |
|---------------|------|--------------------------------------------------------------|
| CONN_ID       | Y    | 设置父隧道ID                                                 |
| SESSION_ID    | Y    | 设置会话ID                                                   |
| PEER_SESSION_ID| Y    | 设置父会话ID                                                 |
| PW_TYPE       | Y    | 设置伪线类型                                                 |
| DEBUG         | N    | 调试标志                                                     |
| RECV_SEQ      | N    | 启用接收数据序列号                                           |
| SEND_SEQ      | N    | 启用发送数据序列号                                           |
| LNS_MODE      | N    | 启用LNS模式（自动启用数据序列号）                           |
| RECV_TIMEOUT  | N    | 接收包重排序时的等待超时时间                                 |
| L2SPEC_TYPE   | N    | 设置第二层特定子层类型（仅L2TPv3）                         |

说明：
- “Y”表示必需，“N”表示可选。
- `CONN_ID`：标识父隧道的ID。
- `SESSION_ID`：设置当前会话的ID。
- `PEER_SESSION_ID`：设置与之关联的父会话ID。
- `PW_TYPE`：设置伪线的类型。
- `DEBUG`：用于调试的标志。
- `RECV_SEQ` 和 `SEND_SEQ`：启用数据包的序列号功能，以确保数据包按序传输。
- `LNS_MODE`：如果启用，则自动启用数据序列号功能。
- `RECV_TIMEOUT`：定义在对收到的数据包进行重排序时等待的超时时间。
- `L2SPEC_TYPE`：仅在L2TPv3中使用，用于设置第二层特定子层的类型。
翻译为中文：

COOKIE             N        设置可选的 Cookie（仅限 L2TPv3）
PEER_COOKIE        N        设置可选的对等 Cookie（仅限 L2TPv3）
IFNAME             N        设置接口名称（仅限 L2TPv3）

对于以太网会话类型，这将创建一个 l2tpeth 虚拟接口，然后可以按需进行配置。对于 PPP 会话类型，还必须打开并连接一个 PPPoL2TP 套接字，并将其映射到新的会话上。这将在后面的“PPPoL2TP 套接字”部分中介绍。

`L2TP_CMD_SESSION_DESTROY` 属性： 

================== ======== ===
属性                必需     使用说明
================== ======== ===
CONN_ID            Y        标识要销毁的会话的父隧道 ID
SESSION_ID         Y        标识要销毁的会话 ID
IFNAME             N        通过接口名称标识会话。如果设置，则覆盖任何 CONN_ID 和 SESSION_ID 属性。目前仅支持 L2TPv3 以太网会话
================== ======== ===

`L2TP_CMD_SESSION_MODIFY` 属性：

================== ======== ===
属性                必需     使用说明
================== ======== ===
CONN_ID            Y        标识要修改的会话的父隧道 ID
SESSION_ID         Y        标识要修改的会话 ID
IFNAME             N        通过接口名称标识会话。如果设置，则覆盖任何 CONN_ID 和 SESSION_ID 属性。目前仅支持 L2TPv3 以太网会话
================== ======== ===
以下是提供的文本翻译为中文：

``DEBUG``              N        调试标志
``RECV_SEQ``          N        启用接收数据序列号
``SEND_SEQ``          N        启用发送数据序列号
``LNS_MODE``          N        启用LNS模式（自动启用数据序列号）
``RECV_TIMEOUT``      N        在重新排序接收到的数据包时等待的超时时间
================== ======== ===

`L2TP_CMD_SESSION_GET` 属性：-

================== ======== ===
属性                  必需    用途
================== ======== ===
``CONN_ID``            N        标识要查询的隧道ID
对于DUMP请求将被忽略
``SESSION_ID``         N        标识要查询的会话ID
对于DUMP请求将被忽略
``IFNAME``             N        通过接口名称标识会话
================== ======== ===

请注意，这里的"N"表示这些选项是非必需的。
如果已设置，这将覆盖任何 CONN_ID 和 SESSION_ID 属性。对于 DUMP 请求会被忽略。目前仅支持 L2TPv3 以太网会话。

================== ======== ===

应用程序开发者应参考 `include/uapi/linux/l2tp.h`_ 获取 Netlink 命令和属性定义。
使用 libmnl_ 的示例用户空间代码：

  - 打开 L2TP Netlink 套接字::

        struct nl_sock *nl_sock;
        int l2tp_nl_family_id;

        nl_sock = nl_socket_alloc();
        genl_connect(nl_sock);
        genl_id = genl_ctrl_resolve(nl_sock, L2TP_GENL_NAME);

  - 创建隧道::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给 genl 套接字 */
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
        nlh->nlmsg_type = genl_id; /* 分配给 genl 套接字 */
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
        /* 在创建会话时，可以使用 Netlink 属性设置其他会话选项 -- 参见 l2tp.h */

  - 删除会话::

        struct nlmsghdr *nlh;
        struct genlmsghdr *gnlh;

        nlh = mnl_nlmsg_put_header(buf);
        nlh->nlmsg_type = genl_id; /* 分配给 genl 套接字 */
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
        nlh->nlmsg_type = genl_id; /* 分配给 genl 套接字 */
        nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK;
        nlh->nlmsg_seq = seq;

        gnlh = mnl_nlmsg_put_extra_header(nlh, sizeof(*gnlh));
        gnlh->cmd = L2TP_CMD_TUNNEL_DELETE;
        gnlh->version = L2TP_GENL_VERSION;
        gnlh->reserved = 0;

        mnl_attr_put_u32(nlh, L2TP_ATTR_CONN_ID, tid);

PPPoL2TP 会话套接字 API
---------------------------

对于 PPP 会话类型，必须打开并连接一个 PPPoL2TP 套接字到 L2TP 会话。
当创建 PPPoL2TP 套接字时，应用程序向内核提供有关隧道和会话的信息，在套接字的 connect() 调用中。提供了源和目标隧道与会话 ID，以及 UDP 或 L2TPIP 套接字的文件描述符。参见 `include/linux/if_pppol2tp.h`_ 中的 struct pppol2tp_addr。出于历史原因，不幸的是 L2TPv2/L2TPv3 IPv4/IPv6 隧道有不同的地址结构，用户空间必须使用与隧道套接字类型匹配的适当结构。
用户空间可以通过在 PPPoX 套接字上调用 setsockopt 和 ioctl 来控制隧道或会话的行为。以下套接字选项是支持的：-

=========   ===========================================================
DEBUG       调试消息类别的位掩码。参见下文
SENDSEQ     - 0 => 不发送带序列号的包
            - 1 => 发送带序列号的包
RECVSEQ     - 0 => 接收包序列号是可选的
            - 1 => 丢弃没有序列号的接收包
LNSMODE     - 0 => 作为 LAC 运行
- 1 => 作为 LNS 运行
REORDERTO   重排序超时（毫秒）。如果为 0，则不尝试重新排序
=========   ===========================================================

除了标准的 PPP ioctl 外，还提供了一个 PPPIOCGL2TPSTATS 用于从内核获取隧道和会话统计信息，使用适当的隧道或会话的 PPPoX 套接字。
示例用户空间代码：

  - 创建会话 PPPoX 数据套接字::

        /* 输入：已经绑定的 L2TP 隧道 UDP 套接字 `tunnel_fd`（sockname 和 peername），否则它将不会准备好
这段代码和描述主要涉及在Linux环境下使用PPPoL2TP（一种基于PPP over L2TP的协议）建立连接的过程，包括创建L2TP会话、PPP通道以及PPP接口，并提供了如何桥接两个具有PPP伪线类型的L2TP会话的方法。下面是具体的翻译：

```plaintext
// 定义一个用于存储L2TP地址信息的结构体
struct sockaddr_pppol2tp sax;
int session_fd; // 会话文件描述符
int ret; // 返回值

// 创建一个面向连接的套接字用于L2TP会话
session_fd = socket(AF_PPPOX, SOCK_DGRAM, PX_PROTO_OL2LP);
if (session_fd < 0)
        return -errno;

// 初始化L2TP地址信息
sax.sa_family = AF_PPPOX;
sax.sa_protocol = PX_PROTO_OL2LP;
sax.pppol2tp.fd = tunnel_fd; // 隧道文件描述符
sax.pppol2tp.addr.sin_addr.s_addr = addr->sin_addr.s_addr;
sax.pppol2tp.addr.sin_port = addr->sin_port;
sax.pppol2tp.addr.sin_family = AF_INET;
sax.pppol2tp.s_tunnel  = tunnel_id; // 本地隧道ID
sax.pppol2tp.s_session = session_id; // 本地会话ID
sax.pppol2tp.d_tunnel  = peer_tunnel_id; // 对端隧道ID
sax.pppol2tp.d_session = peer_session_id; // 对端会话ID

// 尝试连接到L2TP服务器
ret = connect(session_fd, (struct sockaddr *)&sax, sizeof(sax));
if (ret < 0 ) {
        close(session_fd);
        return -errno;
}

return session_fd;

// L2TP控制包仍然可以在`tunnel_fd`上读取
// 创建PPP通道
/* 输入：会话的PPPoX数据套接字`session_fd`，如上述过程所述 */
int ppp_chan_fd;
int chindx;
int ret;

// 获取通道索引
ret = ioctl(session_fd, PPPIOCGCHAN, &chindx);
if (ret < 0)
        return -errno;

// 打开/dev/ppp设备文件
ppp_chan_fd = open("/dev/ppp", O_RDWR);
if (ppp_chan_fd < 0)
        return -errno;

// 关联通道索引与PPP通道
ret = ioctl(ppp_chan_fd, PPPIOCATTCHAN, &chindx);
if (ret < 0) {
        close(ppp_chan_fd);
        return -errno;
}

return ppp_chan_fd;

// LCP PPP帧现在可以在`ppp_chan_fd`上读取
// 创建PPP接口
/* 输入：PPP通道`ppp_chan_fd`，如上述过程所述 */
int ifunit = -1;
int ppp_if_fd;
int ret;

// 打开/dev/ppp设备文件
ppp_if_fd = open("/dev/ppp", O_RDWR);
if (ppp_if_fd < 0)
        return -errno;

// 创建新的PPP单元
ret = ioctl(ppp_if_fd, PPPIOCNEWUNIT, &ifunit);
if (ret < 0) {
        close(ppp_if_fd);
        return -errno;
}

// 连接PPP通道到PPP单元
ret = ioctl(ppp_chan_fd, PPPIOCCONNECT, &ifunit);
if (ret < 0) {
        close(ppp_if_fd);
        return -errno;
}

return ppp_if_fd;

// IPCP/IPv6CP PPP帧现在可以在`ppp_if_fd`上读取
// 可以通过netlink的RTM_NEWLINK, RTM_NEWADDR, RTM_NEWROUTE或者ioctl的SIOCSIFMTU, SIOCSIFADDR等配置ppp<ifunit>接口
// 桥接具有PPP伪线类型的L2TP会话（也称为L2TP隧道切换或L2TP多跳）可以通过桥接两个要桥接的L2TP会话的PPP通道实现
/* 输入：会话的PPPoX数据套接字`session_fd1`和`session_fd2`，如上述过程所述 */
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

// 打开/dev/ppp设备文件
ppp_chan_fd = open("/dev/ppp", O_RDWR);
if (ppp_chan_fd < 0)
        return -errno;

// 关联第一个通道索引与PPP通道
ret = ioctl(ppp_chan_fd, PPPIOCATTCHAN, &chindx1);
if (ret < 0) {
        close(ppp_chan_fd);
        return -errno;
}

// 桥接第二个通道索引与PPP通道
ret = ioctl(ppp_chan_fd, PPPIOCBRIDGECHAN, &chindx2);
close(ppp_chan_fd);
if (ret < 0)
        return -errno;

return 0;

// 当桥接PPP通道时，PPP会话不会在当地终止，也不会创建本地PPP接口。到达一个通道的PPP帧会直接传递给另一个通道，反之亦然。
```

请注意，此段代码示例中的某些宏（例如`PX_PROTO_OL2LP`）和ioctl命令（例如`PPPIOCGCHAN`）可能需要根据实际使用的库和系统版本进行调整。
PPP通道无需保持常开。只需要保持PPPoX会话数据套接字的开启。
更一般地说，同样可以采用类似的方法来桥接PPPoL2TP的PPP通道与其他类型的PPP通道，例如PPPoE。
关于PPP方面的更多细节，请参阅`ppp_generic.rst`。

### 旧版仅支持L2TPv2的API
--------------

当L2TP最初在Linux内核2.6.23中被引入时，它仅实现了L2TPv2，并且没有包括netlink API。相反，内核中的隧道和会话实例直接通过仅使用PPPoL2TP套接字进行管理。PPPoL2TP套接字的使用方式如“PPPoL2TP会话套接字API”部分所述，但是隧道和会话实例是在套接字连接时自动创建，而不是通过单独的netlink请求创建：

- 隧道由一个专用的PPPoL2TP套接字（即隧道管理套接字）进行管理，该套接字连接到无效的会话ID 0。当PPPoL2TP隧道管理套接字连接时，L2TP隧道实例被创建；当套接字关闭时，隧道被销毁。
- 会话实例在PPPoL2TP套接字连接到非零会话ID时在内核中创建。使用setsockopt设置会话参数。当套接字关闭时，L2TP会话实例被销毁。

此API仍然得到支持，但不建议使用。新的L2TPv2应用程序应使用netlink首先创建隧道和会话，然后为会话创建PPPoL2TP套接字。

### 未管理的L2TPv3隧道
--------------

内核L2TP子系统也支持静态（未管理的）L2TPv3隧道。未管理的隧道没有用户空间的隧道套接字，并且与对等方之间不交换任何控制消息以建立隧道；隧道在隧道两端手动配置。所有配置都通过netlink完成。在这种情况下不需要L2TP用户空间应用程序——隧道套接字由内核创建，并通过在`L2TP_CMD_TUNNEL_CREATE` netlink请求中发送的参数进行配置。`iproute2`的`ip`工具提供了用于管理静态L2TPv3隧道的命令；执行`ip l2tp help`获取更多信息。

### 调试
---------

L2TP子系统通过debugfs文件系统提供了一系列调试接口。
要访问这些接口，必须先挂载debugfs文件系统：
```bash
# mount -t debugfs debugfs /debug
```

之后可以访问l2tp目录下的文件，以查看当前存在于内核中的隧道和会话上下文的摘要信息：
```bash
# cat /debug/l2tp/tunnels
```

由于debugfs文件格式可能会发生变化，因此不应由应用程序使用这些文件来获取L2TP状态信息。它们实现的目的在于提供额外的调试信息以帮助诊断问题。应用程序应该使用netlink API。

此外，L2TP子系统还使用标准内核事件跟踪API实现了追踪点。可以通过以下命令查看可用的L2TP事件：
```bash
# find /debug/tracing/events/l2tp
```

最后，为了与最初的pppol2tp代码保持向后兼容性，还提供了`/proc/net/pppol2tp`。它只列出有关L2TPv2隧道和会话的信息。其使用不被推荐。
内部实现
=======================

本节面向内核开发者和维护者。
套接字
-------

UDP 套接字由网络核心实现。当使用 UDP 套接字创建 L2TP 隧道时，该套接字通过设置 `encap_rcv` 和 `encap_destroy` 回调函数作为封装 UDP 套接字。当在套接字上收到数据包时会调用 `l2tp_udp_encap_recv`；当用户空间关闭套接字时会调用 `l2tp_udp_encap_destroy`。
L2TPIP 套接字在 `net/l2tp/l2tp_ip.c` 和 `net/l2tp/l2tp_ip6.c` 中实现。
隧道
-------

内核为每个 L2TP 隧道保持一个 `l2tp_tunnel` 结构体。L2TP 隧道总是与一个 UDP 或 L2TPIP 套接字相关联，并维护隧道内的会话列表。当隧道首次注册到 L2TP 核心时，会增加套接字的引用计数。这确保了在 L2TP 的数据结构引用该套接字时，套接字不会被移除。
隧道通过唯一的隧道 ID 来标识。对于 L2TPv2，ID 是 16 位；对于 L2TPv3，则是 32 位。内部存储为 32 位值。
隧道按网络（per-net）存储在一个列表中，以隧道 ID 索引。L2TPv2 和 L2TPv3 共享隧道 ID 名称空间。可以从套接字的 `sk_user_data` 获取隧道上下文。
处理隧道套接字关闭可能是 L2TP 实现中最棘手的部分。如果用户空间关闭了隧道套接字，必须关闭并销毁 L2TP 隧道及其所有会话。由于隧道上下文持有对隧道套接字的引用，因此只有当隧道执行 `sock_put` 操作释放其套接字时才会调用套接字的 `sk_destruct`。对于 UDP 套接字，当用户空间关闭隧道套接字时，将调用套接字的 `encap_destroy` 处理程序，L2TP 利用它来启动隧道关闭操作。对于 L2TPIP 套接字，套接字的关闭处理程序启动相同的隧道关闭操作。首先关闭所有会话。每个会话会释放其对隧道的引用。当隧道的引用计数降至零时，隧道会释放其对套接字的引用。当套接字最终被销毁时，其 `sk_destruct` 最终释放 L2TP 隧道上下文。
会话
--------

内核为每个会话保持一个 `l2tp_session` 结构体。每个会话都有私有数据，用于存储特定于会话类型的数据。对于 L2TPv2，会话始终承载 PPP 流量。对于 L2TPv3，会话可以承载以太网帧（以太网伪线）或其他数据类型，如 PPP、ATM、HDLC 或帧中继。目前，Linux 只实现了以太网和 PPP 会话类型。
某些 L2TP 会话类型也有一个套接字（PPP 伪线），而其他则没有（以太网伪线）。因此我们不能使用套接字的引用计数作为会话上下文的引用计数。因此，L2TP 实现为会话上下文维护自己的内部引用计数。
与隧道类似，L2TP 会话通过唯一的会话 ID 进行标识。与隧道 ID 类似，会话 ID 对于 L2TPv2 为 16 位，对于 L2TPv3 为 32 位。内部存储为 32 位值。
会话持有对其父隧道的引用以确保在有一个或多个会话引用该隧道时，该隧道仍然存在。会话被保存在一个按会话ID索引的每隧道列表中。L2TPv3会话也被保存在一个按会话ID索引的每网络列表中，因为L2TPv3会话ID在网络中的所有隧道中都是唯一的，并且L2TPv3数据包头中不包含隧道ID。因此，当无法从隧道套接字推导出隧道上下文时，需要此列表来查找与接收到的数据包关联的会话上下文。

尽管L2TPv3 RFC规定L2TPv3会话ID不受隧道范围限制，但内核并未对L2TPv3 UDP隧道实施此规则，并且不会将L2TPv3 UDP隧道的会话添加到每网络会话列表中。在UDP接收代码中，我们只能信任使用隧道套接字的sk_user_data可以识别隧道，并在隧道的会话列表而不是每网络会话列表中查找会话。

PPP
---
`net/l2tp/l2tp_ppp.c`_ 实现了PPPoL2TP套接字家族。每个PPP会话都有一个PPPoL2TP套接字。
PPPoL2TP套接字的sk_user_data引用了l2tp_session。
用户空间通过PPPoL2TP套接字发送和接收PPP数据包。只有PPP控制帧通过此套接字传输：PPP数据包完全由内核处理，通过内核PPP子系统的PPP通道接口，在L2TP会话及其关联的`pppN`网卡之间传递。

L2TP PPP实现通过关闭其对应的L2TP会话来处理PPPoL2TP套接字的关闭。这很复杂，因为它必须考虑与netlink会话创建/销毁请求以及pppol2tp_connect尝试重新连接正在关闭过程中的会话的竞争。与隧道不同，PPP会话不会在其关联的套接字上持有引用，因此在必要时代码必须小心地使用sock_hold。具体细节请参见commit 3d609342cc04129ff7568e19316ce3d7451a27e8。

以太网
------
`net/l2tp/l2tp_eth.c`_ 实现了L2TPv3以太网伪线。它为每个会话管理一个网卡。
L2TP以太网会话通过netlink请求创建和销毁，或者在隧道销毁时销毁。与PPP会话不同，以太网会话没有关联的套接字。

杂项
====

RFCs
----

内核代码实现了以下RFC中指定的数据路径特性：

======= =============== ===================================
RFC2661 L2TPv2          https://tools.ietf.org/html/rfc2661
RFC3931 L2TPv3          https://tools.ietf.org/html/rfc3931
RFC4719 L2TPv3 Ethernet https://tools.ietf.org/html/rfc4719
======= =============== ===================================

实现
----

一些开源应用程序使用了L2TP内核子系统：

============ ==============================================
iproute2     https://github.com/shemminger/iproute2
go-l2tp      https://github.com/katalix/go-l2tp
tunneldigger https://github.com/wlanslovenija/tunneldigger
xl2tpd       https://github.com/xelerance/xl2tpd
============ ==============================================

局限性
------

当前实现有一些局限性：

1) 不能使用具有相同五元组地址的多个UDP套接字。内核的隧道上下文是通过与套接字关联的私有数据标识的，因此重要的是每个套接字都必须通过其地址唯一标识。
### 翻译

2) 与 Open vSwitch 的接口尚未实现。可能有用的做法是将 OVS 以太网端口和 VLAN 端口映射到 L2TPv3 隧道中。

3) VLAN 伪线通过配置 VLAN 子接口的 `l2tpethN` 接口来实现。由于 L2TPv3 VLAN 伪线只承载一个 VLAN，因此最好使用单一的网络设备而不是每 VLAN 会话使用一对 `l2tpethN` 和 `l2tpethN`:M。为此添加了 netlink 属性 `L2TP_ATTR_VLAN_ID`，但它从未被实现。

### 测试

内核内置的自测程序测试了未管理的 L2TPv3 以太网特性。请参阅 `tools/testing/selftests/net/l2tp.sh`。
另一套测试套件 `l2tp-ktest` 覆盖了所有 L2TP API 和隧道/会话类型。未来可能会将其集成到内核内置的 L2TP 自测程序中。

### 链接
- [通用 Netlink](generic_netlink.html)
- [libmnl](https://www.netfilter.org/projects/libmnl)
- [include/uapi/linux/l2tp.h](../../../include/uapi/linux/l2tp.h)
- [include/linux/if_pppol2tp.h](../../../include/linux/if_pppol2tp.h)
- [net/l2tp/l2tp_ip.c](../../../net/l2tp/l2tp_ip.c)
- [net/l2tp/l2tp_ip6.c](../../../net/l2tp/l2tp_ip6.c)
- [net/l2tp/l2tp_ppp.c](../../../net/l2tp/l2tp_ppp.c)
- [net/l2tp/l2tp_eth.c](../../../net/l2tp/l2tp_eth.c)
- [tools/testing/selftests/net/l2tp.sh](../../../tools/testing/selftests/net/l2tp.sh)
- [l2tp-ktest](https://github.com/katalix/l2tp-ktest)
