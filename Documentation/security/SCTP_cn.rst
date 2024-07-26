SPDX 许可证标识符: GPL-2.0

====
SCTP
====

SCTP LSM 支持
================

安全钩子
--------------

为了支持安全模块，已实现三个特定于 SCTP 的钩子：

-  security_sctp_assoc_request()
-  security_sctp_bind_connect()
-  security_sctp_sk_clone()
-  security_sctp_assoc_established()

下面描述了这些钩子的使用，并在《SCTP SELinux 支持》一章中详细介绍了 SELinux 实现。

security_sctp_assoc_request()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
将关联 INIT 包的 `@asoc` 和 `@chunk->skb` 传递给安全模块。成功时返回 0，失败时返回错误。

    -  @asoc - 指向 SCTP 关联结构的指针
    -  @skb - 指向关联数据包的 skbuff 结构的指针

security_sctp_bind_connect()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
根据 `@optname` 将一个或多个 IPv4/IPv6 地址传递给安全模块进行验证，这将导致绑定或连接服务（如下表中的权限检查所示）。
成功时返回 0，失败时返回错误。

    -  @sk - 指向 sock 结构的指针
    -  @optname - 需要验证的选项名称
    -  @address - 一个或多个 IPv4 / IPv6 地址
    -  @addrlen - 地址的总长度。对于每个 IPv4 或 IPv6 地址，使用 `sizeof(struct sockaddr_in)` 或 `sizeof(struct sockaddr_in6)` 来计算。
以下是提供的内容的中文翻译：

---

### 绑定类型检查

|                     @optname                     |        @address 包含        |
|--------------------------------------------------|------------------------------|
| SCTP_SOCKOPT_BINDX_ADD                           | 一个或多个 IPv4/IPv6 地址    |
| SCTP_PRIMARY_ADDR                                | 单个 IPv4 或 IPv6 地址       |
| SCTP_SET_PEER_PRIMARY_ADDR                       | 单个 IPv4 或 IPv6 地址       |

---

### 连接类型检查

|                     @optname                     |        @address 包含        |
|--------------------------------------------------|------------------------------|
| SCTP_SOCKOPT_CONNECTX                            | 一个或多个 IPv4/IPv6 地址    |
| SCTP_PARAM_ADD_IP                                | 一个或多个 IPv4/IPv6 地址    |
| SCTP_SENDMSG_CONNECT                             | 单个 IPv4 或 IPv6 地址       |
| SCTP_PARAM_SET_PRIMARY                           | 单个 IPv4 或 IPv6 地址       |

---

对于 `@optname` 的条目总结如下：

- SCTP_SOCKOPT_BINDX_ADD：允许在调用 `bind(3)` 后（可选地）添加更多的绑定地址。
  - `sctp_bindx(3)` 在套接字上添加一组绑定地址。

- SCTP_SOCKOPT_CONNECTX：允许为到达对等端分配多个地址（多宿主）。
  - `sctp_connectx(3)` 使用多个目标地址在 SCTP 套接字上发起连接。

- SCTP_SENDMSG_CONNECT：通过 `sendmsg(2)` 或 `sctp_sendmsg(3)` 在新关联中发起连接。

- SCTP_PRIMARY_ADDR：设置本地主要地址。

- SCTP_SET_PEER_PRIMARY_ADDR：请求对等端将地址设置为主要关联地址。

- SCTP_PARAM_ADD_IP：当启用动态地址重新配置时使用。

- SCTP_PARAM_SET_PRIMARY：当启用动态地址重新配置时使用。

为了支持动态地址重新配置，必须在两端点上启用以下参数（或者使用适当的 `setsockopt(2)`）：

- `/proc/sys/net/sctp/addip_enable`
- `/proc/sys/net/sctp/addip_noauth_enable`

当对应的 `@optname` 出现时，下列的 `_PARAM_` 将被发送到对等端的 ASCONF 数据块中：

|           @optname               |         ASCONF 参数         |
|----------------------------------|-----------------------------|
| SCTP_SOCKOPT_BINDX_ADD          | -> SCTP_PARAM_ADD_IP         |
| SCTP_SET_PEER_PRIMARY_ADDR       | -> SCTP_PARAM_SET_PRIMARY    |

---

### security_sctp_sk_clone()

当通过 `accept(2)` 创建新的套接字（即 TCP 风格的套接字）或者用户空间调用 `sctp_peeloff(3)` 从现有的连接“剥离”出一个套接字时会调用此函数。

- `@asoc`：指向当前的 SCTP 关联结构。
在收到COOKIE ACK时调用，此时对等方的安全标识（secid）将被保存到`@asoc->peer_secid`中，对于客户端而言：

    @asoc - 指向SCTP关联结构的指针
@skb - 指向包含COOKIE ACK数据包的skbuff的指针

安全钩子在建立关联时的应用
----------------------------------

下图展示了在建立一个关联时如何使用`security_sctp_bind_connect()`、`security_sctp_assoc_request()`和`security_sctp_assoc_established()`。

      SCTP终端"A"                                 SCTP终端"Z"
      ===============                                 ===============
    sctp_sf_do_prm_asoc()
关联设置可以由connect(2)，sctp_connectx(3)，  
sendmsg(2)或sctp_sendmsg(3)发起，
这些操作最终会导致调用
security_sctp_bind_connect()来
启动与SCTP对端终端"Z"的
关联。
INIT --------------------------------------------->
                                                   sctp_sf_do_5_1B_init()
                                                 响应INIT数据块
SCTP对端终端"A"正在请求
                                             临时关联
调用security_sctp_assoc_request()
                                             来设置对端标签，如果这是
                                             第一次建立关联的话。
如果这不是首次建立关联，则检查
                                             是否允许，如果是，则发送：
          <----------------------------------------------- INIT ACK
          |                                  否则审计事件并静默地
          |                                       丢弃该数据包
|
    COOKIE ECHO ------------------------------------------>
                                                  sctp_sf_do_5_1D_ce()
                                             响应一个COOKIE ECHO数据块
确认cookie并创建一个
                                             永久关联
调用security_sctp_assoc_request()来
                                             对INIT数据块响应执行相同操作
<------------------------------------------- COOKIE ACK
          |                                               |
    sctp_sf_do_5_1E_ca                                    |
 调用security_sctp_assoc_established()                   |
 设置对等方标签。                                       |
          |                                               |
          |                               如果是SCTP_SOCKET_TCP或剥离的套接字，
          |                               则调用security_sctp_sk_clone()克隆新套接字
|                                               |
      ESTABLISHED                                    ESTABLISHED
          |                                               |
    ------------------------------------------------------------------
    |                     关联已建立                         |
    ------------------------------------------------------------------


SCTP SELinux 支持
==================

安全钩子
--------

上面的 `SCTP LSM支持`_ 章节描述了以下SCTP安全
钩子，并在下面扩展了SELinux的具体实现:: 

    security_sctp_assoc_request()
    security_sctp_bind_connect()
    security_sctp_sk_clone()
    security_sctp_assoc_established()


security_sctp_assoc_request()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
将关联INIT数据包的 ``@asoc`` 和 ``@chunk->skb`` 传递给
安全模块。成功返回0，失败返回错误
::

    @asoc - 指向SCTP关联结构的指针
    @skb - 指向关联数据包的skbuff的指针
安全模块执行以下操作：
     如果这是 ``@asoc->base.sk`` 上的首次关联，则设置对等方
     SID为 ``@skb`` 中的SID。这将确保只有一个对等方SID
     被分配给可能支持多个关联的 ``@asoc->base.sk``
ELSE验证 ``@asoc->base.sk peer_sid`` 与 ``@skb peer sid``
     来决定是否应该允许或拒绝该关联
设置`sctp @asoc sid`为套接字的sid（来自`asoc->base.sk`），其中MLS部分取自`@skb peer sid`。这将被SCTP TCP风格的套接字和剥离连接使用，因为它们会导致生成新的套接字。

如果配置了IP安全选项（CIPSO/CALIPSO），则在套接字上设置IP选项。

### `security_sctp_bind_connect()` 函数
检查基于`@optname`的ipv4/ipv6地址所需的权限，如下所示：

| BIND 权限检查 |           @optname             |        @address 包含        |
|:-------------:|:-----------------------------:|:-------------------------:|
| SCTP_SOCKOPT_BINDX_ADD | 一个或多个ipv4 / ipv6地址 | 一个或多个ipv4 / ipv6地址 |
| SCTP_PRIMARY_ADDR      | 单个ipv4或ipv6地址       | 单个ipv4或ipv6地址       |
| SCTP_SET_PEER_PRIMARY_ADDR | 单个ipv4或ipv6地址       | 单个ipv4或ipv6地址       |

| CONNECT 权限检查 |           @optname             |        @address 包含        |
|:--------------:|:-----------------------------:|:-------------------------:|
| SCTP_SOCKOPT_CONNECTX  | 一个或多个ipv4 / ipv6地址 | 一个或多个ipv4 / ipv6地址 |
| SCTP_PARAM_ADD_IP      | 一个或多个ipv4 / ipv6地址 | 一个或多个ipv4 / ipv6地址 |
| SCTP_SENDMSG_CONNECT   | 单个ipv4或ipv6地址       | 单个ipv4或ipv6地址       |
| SCTP_PARAM_SET_PRIMARY | 单个ipv4或ipv6地址       | 单个ipv4或ipv6地址       |

`SCTP LSM Support`_ 提供了一个关于`@optname`条目的总结，并且描述了当动态地址重新配置启用时ASCONF块处理的过程。

### `security_sctp_sk_clone()` 函数
每当通过**accept**(2)创建一个新的套接字（即TCP风格的套接字）或者当一个套接字被“剥离”时（例如用户空间调用**sctp_peeloff**(3)）。`security_sctp_sk_clone()`将会把新套接字的sid和peer sid设置为`@asoc sid`和`@asoc peer sid`中包含的内容。
- `@asoc` — 指向当前的sctp关联结构
- `@sk` — 指向当前的sock结构
- `@newsk` — 指向新的sock结构

### `security_sctp_assoc_established()` 函数
当收到COOKIE ACK时被调用，在这里设置连接的peer sid为`@skb`中的值。
- `@asoc` — 指向sctp关联结构
- `@skb` — 指向COOKIE ACK数据包的skbuff

### 策略声明
以下类和支持SCTP的权限在内核中可用：

- 类`sctp_socket`继承自`socket` { `node_bind` }

只要启用了以下策略能力：

- `policycap extended_socket_class;`

SELinux SCTP支持增加了`name_connect`权限，用于连接到特定端口类型，以及下面解释的`association`权限。
如果用户空间工具已更新，SCTP 将支持 `portcon` 声明，如下例所示：

    portcon sctp 1024-1036 system_u:object_r:sctp_ports_t:s0

SCTP 对等端标签
-----------------
一个 SCTP 套接字只会被分配一个对等端标签。这会在建立首个关联时进行分配。对于该套接字上的任何后续关联，其数据包的对等端标签将与套接字的对等端标签进行比较，只有当它们不同时，才会验证 `association` 权限。这是通过检查套接字对等端 SID 与收到的数据包的对等端 SID 来确定是否允许或拒绝关联。

注解：
   1) 如果未启用对等端标签，则对等上下文始终为 `SECINITSID_UNLABELED`（参考策略中的 `unlabeled_t`）
2) 由于 SCTP 可以支持每个端点的一个以上的传输地址（多宿主）在单个套接字上，因此可以配置策略和 NetLabel 为这些地址提供不同的对等端标签。由于套接字的对等端标签由首次关联的传输地址决定，建议所有对等端标签保持一致。
3) 用户空间可通过使用 **getpeercon**(3) 获取套接字的对等上下文。
4) 虽然不是特指 SCTP，但在使用 NetLabel 时需要注意，如果给某个接口分配了标签，而该接口“失效”，NetLabel 服务会移除该条目。因此，请确保网络启动脚本调用 **netlabelctl**(8) 来设置所需的标签（请参阅 **netlabel-config**(8) 辅助脚本了解详情）。
5) 关于 NetLabel SCTP 对等端标签规则的讨论，可参考以下一组带有 "netlabel" 标签的帖子：https://www.paul-moore.com/blog/t
6) CIPSO 仅支持 IPv4 地址：`socket(AF_INET, ...)`；CALIPSO 仅支持 IPv6 地址：`socket(AF_INET6, ...)`

      测试 CIPSO/CALIPSO 时请注意以下事项：
         a) 当 SCTP 数据包因无效标签而无法传递时，CIPSO 会发送一个 ICMP 数据包
b) CALIPSO 不发送 ICMP 数据包，而是静默丢弃它
7) 不支持 IPSEC，因为 RFC 3554 - sctp/ipsec 支持尚未在用户空间实现（**racoon**(8) 或 **ipsec_pluto**(8)），尽管内核支持 SCTP/IPSEC。
