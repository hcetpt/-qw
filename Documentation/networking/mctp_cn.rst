SPDX 许可证标识符: GPL-2.0

==============================================
管理组件传输协议 (MCTP)
==============================================

`net/mctp/` 包含根据DMTF标准DSP0236定义的MCTP协议支持。物理接口驱动程序（在规范中称为“绑定”）位于 `drivers/net/mctp/` 中。
核心代码提供了一个基于套接字的接口来发送和接收MCTP消息，通过 `AF_MCTP`, `SOCK_DGRAM` 套接字实现。
结构：接口与网络
================================

内核通过两个项目来建模本地MCTP拓扑结构：接口和网络。

一个接口（或“链路”）是一个MCTP物理传输绑定的实例（如DSP0236第3.2.47节所定义），可能连接到特定硬件设备。这表示为一个 `struct netdevice` 结构体。
一个网络通过端点ID定义了一个唯一的MCTP端点地址空间（如DSP0236第3.2.31节所述）。网络具有用户可见的标识符以允许从用户空间进行引用。路由定义是针对特定网络的。
接口与一个网络相关联。一个网络可以与一个或多个接口相关联。
如果存在多个网络，则每个网络都可能包含也在其他网络上存在的端点ID (EID)。

套接字API
===========

协议定义
--------------------

MCTP使用 `AF_MCTP` / `PF_MCTP` 作为地址和协议族。
由于MCTP基于消息，仅支持 `SOCK_DGRAM` 类型的套接字。
.. code-block:: C

    int sd = socket(AF_MCTP, SOCK_DGRAM, 0);

`protocol` 参数当前唯一有效的值为0。
如同所有套接字地址族一样，源地址和目标地址通过`sockaddr`类型指定，其中包含一个单字节的端点地址：

.. code-block:: C

    typedef __u8       mctp_eid_t;

    struct mctp_addr {
            mctp_eid_t   s_addr;
    };

    struct sockaddr_mctp {
            __kernel_sa_family_t smctp_family;
            unsigned int         smctp_network;
            struct mctp_addr     smctp_addr;
            __u8                 smctp_type;
            __u8                 smctp_tag;
    };

    #define MCTP_NET_ANY      0x0
    #define MCTP_ADDR_ANY     0xff


系统调用行为
--------------

以下各节描述了标准套接字系统调用中与MCTP相关的特定行为。这些行为被选择以尽可能接近现有的套接字APIs。

``bind()``：设置本地套接字地址
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

接收传入请求包的套接字将绑定到本地地址，使用`bind()`系统调用。
.. code-block:: C

    struct sockaddr_mctp addr;

    addr.smctp_family = AF_MCTP;
    addr.smctp_network = MCTP_NET_ANY;
    addr.smctp_addr.s_addr = MCTP_ADDR_ANY;
    addr.smctp_type = MCTP_TYPE_PLDM;
    addr.smctp_tag = MCTP_TAG_OWNER;

    int rc = bind(sd, (struct sockaddr *)&addr, sizeof(addr));

这确立了该套接字的本地地址。匹配网络、地址和消息类型的传入MCTP消息将由这个套接字接收。
“传入”这个词在这里很重要；一个绑定的套接字只会接收带有TO位的消息，表明这是一个传入的请求消息，而不是响应。
`smctp_tag`值将配置从该套接字的远程端接受的标签。基于以上所述，唯一有效的值是`MCTP_TAG_OWNER`，这将导致远程"拥有"的标签被路由到此套接字。因为设置了`MCTP_TAG_OWNER`，`smctp_tag`的最低三位未被使用；调用者必须将其设置为零。
`smctp_network`值为`MCTP_NET_ANY`将配置套接字接收来自任何本地连接网络的传入数据包。一个具体的网络值将导致套接字仅接收来自那个网络的传入消息。
`smctp_addr`字段指定了要绑定的本地地址。`MCTP_ADDR_ANY`的值配置套接字接收发往任何本地目的地EID的消息。
`smctp_type`字段指定了要接收的消息类型。只有类型的最低7位在传入消息上进行匹配（即，最高位的IC位不参与匹配）。这导致套接字接收带有和不带有消息完整性检查尾部的包。

`sendto()`, `sendmsg()`, `send()`：传输MCTP消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

使用`sendto()`, `sendmsg()`或`send()`系统调用之一来发送MCTP消息。以`sendto()`作为主要示例：

.. code-block:: C

    struct sockaddr_mctp addr;
    char buf[14];
    ssize_t len;

    /* 设置消息目的地 */
    addr.smctp_family = AF_MCTP;
    addr.smctp_network = 0;
    addr.smctp_addr.s_addr = 8;
    addr.smctp_tag = MCTP_TAG_OWNER;
    addr.smctp_type = MCTP_TYPE_ECHO;

    /* 要发送的任意消息，带消息类型头 */
    buf[0] = MCTP_TYPE_ECHO;
    memcpy(buf + 1, "hello, world!", sizeof(buf) - 1);

    len = sendto(sd, buf, sizeof(buf), 0,
                    (struct sockaddr_mctp *)&addr, sizeof(addr));

`addr`的网络和地址字段定义了要发送到的远程地址。
如果`smctp_tag`具有`MCTP_TAG_OWNER`，内核将忽略`MCTP_TAG_VALUE`中设置的任何位，并生成适合目的地EID的标签值。如果没有设置`MCTP_TAG_OWNER`，消息将按照指定的标签值发送。如果无法分配标签值，系统调用将报告`EAGAIN`的errno。
应用程序必须将消息类型字节作为传递给`sendto()`的第一个字节的消息缓冲区。如果要在传输的消息中包含消息完整性检查，那么也必须在消息缓冲区中提供，并且消息类型字节的最高有效位必须为1。
`sendmsg()`系统调用允许使用更紧凑的参数接口，并指定消息缓冲区为散集列表。目前没有定义任何辅助消息类型（用于通过`sendmsg()`传递的`msg_control`数据）。
通过未连接的套接字发送带有`MCTP_TAG_OWNER`标记的消息将在没有为该目的地分配有效的标记时分配一个标记。`(destination-eid,tag)`元组充当一个隐含的本地套接字地址，以允许该套接字接收对此传出消息的响应。如果之前已经执行过任何分配（例如，对于不同的远程EID），那么这些分配将丢失。
套接字仅会接收它们已发送的请求（TO=1）的响应，并且只能对它们已收到的请求（TO=0）进行响应。
`recvfrom()`、`recvmsg()`、`recv()`：接收MCTP消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

一个MCTP消息可以通过`recvfrom()`、`recvmsg()`或`recv()`系统调用来被应用程序接收。这里以`recvfrom()`为主要示例：

.. code-block:: C

    struct sockaddr_mctp addr;
    socklen_t addrlen;
    char buf[14];
    ssize_t len;

    addrlen = sizeof(addr);

    len = recvfrom(sd, buf, sizeof(buf), 0,
                   (struct sockaddr_mctp *)&addr, &addrlen);

    /* 我们可以期望addr描述了一个MCTP地址 */
    assert(addrlen >= sizeof(buf));
    assert(addr.smctp_family == AF_MCTP);

    printf("从远程EID %d 接收了 %zd 字节\n", addr.smctp_addr, len);

`recvfrom`和`recvmsg`中的地址参数会被填充为传入消息的远程地址，包括标记值（这将是回复消息所必需的）。
消息缓冲区的第一字节将包含消息类型字节。如果有一个完整性检查跟随消息，则它将包含在接收的缓冲区中。
`recv()`系统调用的行为类似，但不会向应用程序提供远程地址。因此，只有在远程地址已经已知或者消息不需要回复的情况下才会有用。
像发送调用一样，套接字仅会接收它们已发送的请求（TO=1）的响应，并且只能对它们已收到的请求（TO=0）进行响应。
`ioctl(SIOCMCTPALLOCTAG)`和`ioctl(SIOCMCTPDROPTAG)`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些标记让应用程序能够更直接地控制MCTP消息的标签，通过显式分配（和丢弃）标记值，而不是内核在`sendmsg()`时自动为每个消息分配一个标记。
通常情况下，你只需要在你的MCTP协议不符合通常的请求/响应模型时使用这些ioctls。例如，如果你需要跨多个请求保持标记，或者一个请求可能产生多于一个的响应。
在这些情况下，ioctl（输入/输出控制）命令允许你将标签分配（和释放）与单个消息发送和接收操作解耦。两个ioctl都传递一个指向`struct mctp_ioc_tag_ctl`结构的指针：

```C
struct mctp_ioc_tag_ctl {
    mctp_eid_t      peer_addr; // 对等端地址
    __u8            tag;       // 标签值
    __u16           flags;     // 标志
};
```

`SIOCMCTPALLOCTAG`为特定对等端分配一个标签，应用程序可以在未来的`sendmsg()`调用中使用。应用程序需要填充`peer_addr`成员，其中包含远程EID。其他字段必须置零。返回时，`tag`成员将被填充为分配的标签值。

分配的标签将设置以下标签位：

- `MCTP_TAG_OWNER`：只有当你拥有标签时才有意义去分配标签

- `MCTP_TAG_PREALLOC`：指示`sendmsg()`这是一个预分配的标签
- ...以及实际的标签值，在最低三位(`MCTP_TAG_MASK`)中。注意零是一个有效的标签值

应直接使用该标签值作为`struct sockaddr_mctp`中的`smctp_tag`成员。
`SIOCMCTPDROPTAG`用于释放之前由`SIOCMCTPALLOCTAG` ioctl分配的标签。`peer_addr`必须与分配时相同，且`tag`值必须完全匹配从分配中返回的标签（包括`MCTP_TAG_OWNER`和`MCTP_TAG_PREALLOC`位）。`flags`字段必须为零。

### 内核内部机制

MCTP堆栈中有几种可能的数据包流：

1. 本地TX到远程端点，消息<=MTU：

   `sendmsg()` -> `mctp_local_output()` -> 路由查找 -> `rt->output()`（== `mctp_route_output`） -> `dev_queue_xmit()`

2. 本地TX到远程端点，消息>MTU：

   `sendmsg()` -> `mctp_local_output()` -> `mctp_do_fragment_route()` -> 创建包大小的skbs。对于每个新的skb：-> `rt->output()`（== `mctp_route_output`） -> `dev_queue_xmit()`

3. 远程TX到本地端点，单包消息：

   `mctp_pkttype_receive()` -> 路由查找 -> `rt->output()`（== `mctp_route_input`） -> `sk_key`查找 -> `sock_queue_rcv_skb()`

4. 远程TX到本地端点，多包消息：

   `mctp_pkttype_receive()` -> 路由查找 -> `rt->output()`（== `mctp_route_input`） -> `sk_key`查找 -> 将skb存储在`struct sk_key->reasm_head`中

   `mctp_pkttype_receive()` -> 路由查找 -> `rt->output()`（== `mctp_route_input`） -> `sk_key`查找 -> 在`sk_key->reasm_head`中找到现有重组 -> 添加新片段 -> `sock_queue_rcv_skb()`

### 关键引用计数

- 键由以下引用：

  - 一个skb：在路由输出期间，存储在`skb->cb`中
  - netns和sock列表
* 密钥可以与一个设备相关联，在这种情况下，它们会持有对设备的引用（通过`key->dev`设置，通过`dev->key_count`计数）。多个密钥可以引用同一个设备。
