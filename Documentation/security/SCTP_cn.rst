SPDX 许可证标识符: GPL-2.0

====
SCTP
====

SCTP LSM 支持
================

安全挂钩
--------------

为了支持安全模块，已经实现了三个特定于 SCTP 的挂钩：

- `security_sctp_assoc_request()`
- `security_sctp_bind_connect()`
- `security_sctp_sk_clone()`
- `security_sctp_assoc_established()`

这些挂钩的使用如下所述，在《SCTP SELinux 支持》章节中描述了 SELinux 实现。

`security_sctp_assoc_request()` 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
将关联 INIT 数据包的 `@asoc` 和 `@chunk->skb` 传递给安全模块。成功时返回 0，失败时返回错误。
::
    @asoc - 指向 SCTP 关联结构的指针
    @skb - 指向关联数据包的 skbuff 的指针

`security_sctp_bind_connect()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
根据 `@optname` 将一个或多个 IPv4/IPv6 地址传递给安全模块进行验证，这将导致绑定或连接服务，如下面的权限检查表所示。
成功时返回 0，失败时返回错误。
::
    @sk - 指向 sock 结构的指针
    @optname - 需要验证的选项名称
    @address - 一个或多个 IPv4/IPv6 地址
    @addrlen - 地址（s）的总长度。这是通过计算每个 IPv4 或 IPv6 地址的 `sizeof(struct sockaddr_in)` 或 `sizeof(struct sockaddr_in6)` 得到的
### 绑定类型检查

| `@optname`                 | `@address contains`                |
|----------------------------|------------------------------------|
| SCTP_SOCKOPT_BINDX_ADD     | 一个或多个 IPv4/IPv6 地址           |
| SCTP_PRIMARY_ADDR          | 单个 IPv4 或 IPv6 地址              |
| SCTP_SET_PEER_PRIMARY_ADDR | 单个 IPv4 或 IPv6 地址              |

### 连接类型检查

| `@optname`                 | `@address contains`                |
|----------------------------|------------------------------------|
| SCTP_SOCKOPT_CONNECTX      | 一个或多个 IPv4/IPv6 地址           |
| SCTP_PARAM_ADD_IP          | 一个或多个 IPv4/IPv6 地址           |
| SCTP_SENDMSG_CONNECT       | 单个 IPv4 或 IPv6 地址              |
| SCTP_PARAM_SET_PRIMARY     | 单个 IPv4 或 IPv6 地址              |

`@optname` 的条目总结如下：

- `SCTP_SOCKOPT_BINDX_ADD`：允许在调用 `bind(3)`（可选）之后关联额外的绑定地址。`sctp_bindx(3)` 在套接字上添加一组绑定地址。
- `SCTP_SOCKOPT_CONNECTX`：允许为到达对等方分配多个地址（多宿主）。`sctp_connectx(3)` 使用多个目标地址在 SCTP 套接字上发起连接。
- `SCTP_SENDMSG_CONNECT`：通过 `sendmsg(2)` 或 `sctp_sendmsg(3)` 发起一个新的关联连接。
- `SCTP_PRIMARY_ADDR`：设置本地主要地址。
- `SCTP_SET_PEER_PRIMARY_ADDR`：请求对等方将地址设置为主要地址。
- `SCTP_PARAM_ADD_IP`：这些参数在启用动态地址重新配置时使用。
- `SCTP_PARAM_SET_PRIMARY`：在启用动态地址重新配置时使用。

为了支持动态地址重新配置，以下参数必须在两端点上启用（或者使用相应的 `setsockopt(2)`）：

- `/proc/sys/net/sctp/addip_enable`
- `/proc/sys/net/sctp/addip_noauth_enable`

当对应的 `@optname` 存在时，以下 *_PARAM_* 将作为 ASCONF 数据块发送给对等方：

- `SCTP_SOCKOPT_BINDX_ADD` -> `SCTP_PARAM_ADD_IP`
- `SCTP_SET_PEER_PRIMARY_ADDR` -> `SCTP_PARAM_SET_PRIMARY`

### security_sctp_sk_clone()

当通过 `accept(2)` 创建新套接字（即 TCP 风格的套接字）或用户空间调用 `sctp_peeloff(3)` 从现有套接字中分离出新套接字时，会调用此函数：

- `@asoc`：指向当前的 SCTP 关联结构。
@sk - 当前 sock 结构的指针  
@newsk - 新 sock 结构的指针  
security_sctp_assoc_established()  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当接收到 COOKIE ACK 时调用，并将对等方的安全标识（secid）保存到 `@asoc->peer_secid` 中（客户端）：

    @asoc - 指向 SCTP 关联结构的指针  
@skb - 指向包含 COOKIE ACK 数据包的 skbuff 的指针  

用于建立关联的安全挂钩  
-----------------------------------

下图展示了在建立关联过程中如何使用 `security_sctp_bind_connect()`、`security_sctp_assoc_request()` 和 `security_sctp_assoc_established()`：  

      SCTP 端点 "A"                                SCTP 端点 "Z"  
      =================                                =================  
    sctp_sf_do_prm_asoc()  
关联设置可以通过 connect(2)、sctp_connectx(3)、sendmsg(2) 或 sctp_sendmsg(3) 来发起  
这些操作会导致调用 `security_sctp_bind_connect()`，以与 SCTP 对等端点 "Z" 建立关联  
INIT -------------------------------------------->  
                                                   sctp_sf_do_5_1B_init()  
                                                 响应 INIT 数据块  
SCTP 端点 "A" 请求一个临时关联  
调用 `security_sctp_assoc_request()`  
                                                 如果是首次关联，则设置对等方标签
如果不是首次关联，检查
是否允许，如果允许则发送：
                                             <----------------------------------------------- INIT ACK
          |                                  否则记录事件并静默丢弃数据包
          |
    COOKIE ECHO ------------------------------------------>
                                                  sctp_sf_do_5_1D_ce()
                                             响应一个COOKIE ECHO 数据块
确认cookie并创建一个
                                             永久关联
调用security_sctp_assoc_request()来
                                             对INIT数据块响应执行相同操作
<------------------------------------------- COOKIE ACK
          |                                               |
    sctp_sf_do_5_1E_ca                                    |
 调用security_sctp_assoc_established()                   |
 设置对等体标签。                                       |
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

上面的 `SCTP LSM 支持`_ 章节描述了以下SCTP安全钩子，并在下面扩展了SELinux的具体内容::

    security_sctp_assoc_request()
    security_sctp_bind_connect()
    security_sctp_sk_clone()
    security_sctp_assoc_established()

security_sctp_assoc_request()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
将关联INIT数据包的 ``@asoc`` 和 ``@chunk->skb`` 传递给安全模块。成功返回0，失败返回错误
::

    @asoc - 指向SCTP关联结构的指针
    @skb - 指向关联数据包skbuff的指针
安全模块执行以下操作：
     如果这是 ``@asoc->base.sk`` 上的首次关联，则将对等体sid设置为 ``@skb`` 中的值。这将确保只有唯一的对等体sid分配给可能支持多个关联的 ``@asoc->base.sk``
ELSE 验证 ``@asoc->base.sk peer_sid`` 是否与 ``@skb peer sid`` 匹配，以确定是否允许或拒绝该关联
将`sctp "@asoc sid"`设置为套接字的sid（从`asoc->base.sk`获取），并从`@skb peer sid`中获取MLS部分。这将被SCTP TCP风格的套接字和剥离连接使用，因为它们会导致生成新的套接字。

如果配置了IP安全选项（CIPSO/CALIPSO），则在套接字上设置IP选项。

`security_sctp_bind_connect()`函数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
根据`@optname`检查ipv4/ipv6地址所需的权限如下：

  ------------------------------------------------------------------
  |                   BIND 权限检查                               |
  |       @optname             |         @address 包含               |
  |----------------------------|-----------------------------------|
  | SCTP_SOCKOPT_BINDX_ADD     | 一个或多个ipv4 / ipv6地址           |
  | SCTP_PRIMARY_ADDR          | 单个ipv4或ipv6地址                 |
  | SCTP_SET_PEER_PRIMARY_ADDR | 单个ipv4或ipv6地址                 |
  ------------------------------------------------------------------

  ------------------------------------------------------------------
  |                 CONNECT 权限检查                              |
  |       @optname             |         @address 包含               |
  |----------------------------|-----------------------------------|
  | SCTP_SOCKOPT_CONNECTX      | 一个或多个ipv4 / ipv6地址           |
  | SCTP_PARAM_ADD_IP          | 一个或多个ipv4 / ipv6地址           |
  | SCTP_SENDMSG_CONNECT       | 单个ipv4或ipv6地址                 |
  | SCTP_PARAM_SET_PRIMARY     | 单个ipv4或ipv6地址                 |
  ------------------------------------------------------------------

`SCTP LSM Support`_ 提供了`@optname`条目的摘要，并描述了当启用动态地址重新配置时ASCONF数据块的处理过程。

`security_sctp_sk_clone()`函数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
每当通过`accept`(2)创建新套接字（即TCP风格的套接字）或当套接字被“剥离”时（例如用户空间调用`sctp_peeloff`(3)）。`security_sctp_sk_clone()`将新套接字的sid和对等sid分别设置为`@asoc sid`和`@asoc peer sid`中的值。

    @asoc - 指向当前的sctp关联结构
    @sk - 指向当前的sock结构
    @newsk - 指向新的sock结构

`security_sctp_assoc_established()`函数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
当接收到COOKIE ACK时调用，设置连接的对等sid为`@skb`中的值。

    @asoc - 指向sctp关联结构
    @skb - 指向COOKIE ACK数据包的skbuff

策略声明
-----------------
以下类和权限用于支持SCTP，在内核中可用：

    class sctp_socket 继承 socket { node_bind }

只要启用了以下策略能力：

    policycap extended_socket_class;

SELinux SCTP支持增加了`name_connect`权限，用于连接到特定端口类型，并增加了`association`权限，该权限在下面的部分中解释。
如果用户空间工具已更新，SCTP 将支持 `portcon` 声明，如下例所示：

    portcon sctp 1024-1036 system_u:object_r:sctp_ports_t:s0

SCTP 对等标签
-------------

一个 SCTP 套接字只会被分配一个对等标签。这个标签会在第一次关联建立时分配。在此套接字上的任何后续关联将比较其数据包对等标签与套接字的对等标签，只有在它们不同的情况下才会验证 `association` 权限。这是通过检查套接字对等 SID 与收到的数据包对等 SID 来确定是否允许该关联。

注意事项：
1) 如果未启用对等标签，则对等上下文始终为 `SECINITSID_UNLABELED`（参考策略中的 `unlabeled_t`）。
2) 由于 SCTP 可以支持每个端点的一个以上传输地址（多宿主），在一个套接字上，可以配置策略和 NetLabel 为这些地址提供不同的对等标签。由于套接字的对等标签是由第一个关联的传输地址决定的，因此建议所有对等标签保持一致。
3) 用户空间可以通过 **getpeercon**(3) 获取套接字的对等上下文。
4) 虽然这不是特定于 SCTP 的，但在使用 NetLabel 时需要注意，如果为某个接口分配了一个标签，并且该接口“失效”，则 NetLabel 服务会删除该条目。因此，请确保网络启动脚本调用 **netlabelctl**(8) 来设置所需的标签（参见 **netlabel-config**(8) 辅助脚本获取详细信息）。
5) NetLabel SCTP 对等标签规则如以下标记为 “netlabel” 的帖子所述：https://www.paul-moore.com/blog/t
6) CIPSO 仅支持 IPv4 地址：`socket(AF_INET, ...)`；CALIPSO 仅支持 IPv6 地址：`socket(AF_INET6, ...)`

测试 CIPSO/CALIPSO 时请注意以下事项：
   a) 如果 SCTP 数据包因无效标签而无法交付，CIPSO 会发送一个 ICMP 数据包。
   b) CALIPSO 不发送 ICMP 数据包，只是默默地丢弃它。
7) 不支持 IPSEC，因为 RFC 3554 - sctp/ipsec 支持尚未在用户空间实现（**racoon**(8) 或 **ipsec_pluto**(8)），尽管内核支持 SCTP/IPSEC。
