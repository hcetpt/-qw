SPDX 许可证标识符: GPL-2.0

==============================================
管理组件传输协议 (MCTP)
==============================================

`net/mctp/` 包含根据DMTF标准DSP0236定义的MCTP协议支持。物理接口驱动程序（在规范中称为“绑定”）位于 `drivers/net/mctp/` 中。
核心代码提供了一个基于套接字的接口来发送和接收MCTP消息，通过 `AF_MCTP`, `SOCK_DGRAM` 套接字实现。
结构：接口与网络
================================

内核通过两个项目来建模本地MCTP拓扑结构：接口和网络。

一个接口（或“链路”）是一个MCTP物理传输绑定实例（如DSP0236第3.2.47节所定义），可能连接到特定硬件设备。这表示为 `struct netdevice`。
一个网络通过端点ID定义了MCTP端点唯一的地址空间（如DSP0236第3.2.31节所述）。每个网络都有一个用户可见的标识符以允许来自用户空间的引用。路由定义是针对特定网络的。
接口与一个网络相关联。一个网络可以与一个或多个接口关联。
如果存在多个网络，则每个网络都可能包含也在其他网络上存在的端点ID（EID）。

套接字API
===========

协议定义
--------------------

MCTP使用 `AF_MCTP` / `PF_MCTP` 表示地址族和协议族。
由于MCTP是基于消息的，仅支持 `SOCK_DGRAM` 类型的套接字。
.. code-block:: C

    int sd = socket(AF_MCTP, SOCK_DGRAM, 0);

`protocol` 参数当前唯一有效的值为0。
如同所有的套接字地址族一样，源地址和目标地址通过 `sockaddr` 类型指定，并且使用一个字节的端点地址：

.. code-block:: C

    typedef __u8       mctp_eid_t;

    struct mctp_addr {
            mctp_eid_t     s_addr;
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

以下各节描述了标准套接字系统调用中与 MCTP 相关的行为。这些行为是基于现有的套接字 API 设计的。

``bind()``：设置本地套接字地址
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

接收传入请求包的套接字将绑定到本地地址，使用 `bind()` 系统调用：
.. code-block:: C

    struct sockaddr_mctp addr;

    addr.smctp_family = AF_MCTP;
    addr.smctp_network = MCTP_NET_ANY;
    addr.smctp_addr.s_addr = MCTP_ADDR_ANY;
    addr.smctp_type = MCTP_TYPE_PLDM;
    addr.smctp_tag = MCTP_TAG_OWNER;

    int rc = bind(sd, (struct sockaddr *)&addr, sizeof(addr));

这确定了套接字的本地地址。与网络、地址及消息类型匹配的传入 MCTP 消息将被这个套接字接收。
这里提到的“传入”很重要；已绑定的套接字仅接收带有 TO 标志的消息，以指示传入的请求消息，而不是响应。
`smctp_tag` 值会配置从该套接字远程端接收的标签。根据上述内容，唯一有效的值是 `MCTP_TAG_OWNER`，这会导致远程“拥有”的标签被路由到此套接字。因为设置了 `MCTP_TAG_OWNER`，所以 `smctp_tag` 的最低三位是不使用的；调用者必须将其设为零。
`smctp_network` 的值 `MCTP_NET_ANY` 将配置套接字接收来自任何本地连接网络的传入包。特定的网络值将导致套接字仅接收来自那个网络的传入消息。
`smctp_addr` 字段指定了要绑定的本地地址。值 `MCTP_ADDR_ANY` 配置套接字接收发往任何本地目的地 EID 的消息。
`smctp_type` 字段指定了要接收的消息类型。仅匹配消息的最低 7 位类型（即，最高位的 IC 位不是匹配的一部分）。这导致套接字接收包含或不包含消息完整性检查尾部的包。

``sendto()``、``sendmsg()``、``send()``：传输 MCTP 消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

使用 `sendto()`、`sendmsg()` 或 `send()` 系统调用来传输 MCTP 消息。以下以 `sendto()` 作为主要示例：

.. code-block:: C

    struct sockaddr_mctp addr;
    char buf[14];
    ssize_t len;

    /* 设置消息的目的地 */
    addr.smctp_family = AF_MCTP;
    addr.smctp_network = 0;
    addr.smctp_addr.s_addr = 8;
    addr.smctp_tag = MCTP_TAG_OWNER;
    addr.smctp_type = MCTP_TYPE_ECHO;

    /* 要发送的任意消息，带有消息类型头 */
    buf[0] = MCTP_TYPE_ECHO;
    memcpy(buf + 1, "hello, world!", sizeof(buf) - 1);

    len = sendto(sd, buf, sizeof(buf), 0,
                    (struct sockaddr *)&addr, sizeof(addr));

`addr` 中的网络和地址字段定义了要发送到的远程地址。
如果 `smctp_tag` 设置为 `MCTP_TAG_OWNER`，内核将会忽略 `MCTP_TAG_VALUE` 中设置的任何位，并生成一个适合目的 EID 的标签值。如果没有设置 `MCTP_TAG_OWNER`，消息将按照指定的标签值发送。如果无法分配标签值，系统调用将报告一个 `EAGAIN` 的 `errno` 错误。
应用程序必须将消息类型字节作为传递给`sendto()`的第一个字节的消息缓冲区。如果要在传输的消息中包含消息完整性检查，那么也必须在消息缓冲区中提供，并且消息类型字节的最高有效位必须为1。
`sendmsg()`系统调用允许使用更紧凑的参数接口，并指定消息缓冲区为散集列表。目前没有定义任何辅助消息类型（用于通过`sendmsg()`传递的`msg_control`数据）。
通过未连接的套接字发送带有`MCTP_TAG_OWNER`标记的消息将在没有为该目的地分配有效的标记时分配一个标记。`(destination-eid,tag)`元组充当一个隐含的本地套接字地址，以允许该套接字接收对此传出消息的响应。如果之前已经进行了任何分配（针对不同的远程EID），则这些分配将丢失。
套接字仅接收它们已发送的请求的响应（TO=1），并且只能对收到的请求作出响应（TO=0）。
`recvfrom()`、`recvmsg()`、`recv()`：接收MCTP消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

可以通过`recvfrom()`、`recvmsg()`或`recv()`系统调用来接收MCTP消息。以`recvfrom()`为例：

.. code-block:: C

    struct sockaddr_mctp addr;
    socklen_t addrlen;
    char buf[14];
    ssize_t len;

    addrlen = sizeof(addr);

    len = recvfrom(sd, buf, sizeof(buf), 0,
                    (struct sockaddr_mctp *)&addr, &addrlen);

    /* 我们可以预期addr描述了一个MCTP地址 */
    assert(addrlen >= sizeof(buf));
    assert(addr.smctp_family == AF_MCTP);

    printf("从远程EID %d 接收了 %zd 字节\n", addr.smctp_addr, len);

`recvfrom`和`recvmsg`的地址参数填充了传入消息的远程地址，包括标记值（这将是回复消息所必需的）。
消息缓冲区的第一个字节将包含消息类型字节。如果完整性检查跟随消息，则它将包含在接收的缓冲区中。
`recv()`系统调用的行为类似，但不会向应用程序提供远程地址。因此，只有在已知远程地址或消息不需要回复的情况下才适用。
像发送调用一样，套接字仅接收其已发送请求的响应（TO=1），并且只能对收到的请求作出响应（TO=0）。
`ioctl(SIOCMCTPALLOCTAG)` 和 `ioctl(SIOCMCTPDROPTAG)`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些标记使应用程序能够更直接地控制MCTP消息标签，通过显式分配（和丢弃）标签值，而不是内核在`sendmsg()`时自动为每个消息分配标签。
通常情况下，你只有在MCTP协议不符合常规请求/响应模型时才需要使用这些ioctl命令。例如，如果你需要跨多个请求保持标签，或者一个请求可能产生多个响应。
在这些情况下，`ioctl`（输入/输出控制命令）允许您将标签分配（及释放）与单独的消息发送和接收操作解耦。这两种`ioctl`都传递一个指向`struct mctp_ioc_tag_ctl`结构的指针：

```c
struct mctp_ioc_tag_ctl {
    mctp_eid_t      peer_addr;  // 对端地址
    __u8		tag;           // 标签值
    __u16   	flags;         // 标志
};
```

`SIOCMCTPALLOCTAG`为特定对端分配一个标签，应用程序可以在未来的`sendmsg()`调用中使用该标签。应用程序需要填充`peer_addr`成员以远程EID。其他字段必须置零。返回时，`tag`成员将被填充所分配的标签值。分配的标签将设置以下标签位：

- `MCTP_TAG_OWNER`: 只有当您是标签所有者时才有意义进行标签分配

- `MCTP_TAG_PREALLOC`: 用于指示`sendmsg()`这是一个预分配的标签
- ...以及实际标签值，位于最低三位(`MCTP_TAG_MASK`)。注意0是一个有效的标签值
分配得到的标签值可以直接用于`struct sockaddr_mctp`中的`smctp_tag`成员。
`SIOCMCTPDROPTAG`用于释放之前通过`SIOCMCTPALLOCTAG` ioctl分配的标签。`peer_addr`必须与分配时相同，并且`tag`值必须完全匹配从分配中返回的标签(包括`MCTP_TAG_OWNER`和`MCTP_TAG_PREALLOC`位)。`flags`字段必须为零。

### 内核内部机制

MCTP堆栈中有几种可能的数据包流：

1. 本地向远程端点发送数据，消息大小 <= MTU：
   
   ```
   sendmsg()
     -> mctp_local_output()
        : 路由查找
        -> rt->output() (== mctp_route_output)
           -> dev_queue_xmit()
   ```

2. 本地向远程端点发送数据，消息大小 > MTU：
   
   ```
   sendmsg()
     -> mctp_local_output()
        -> mctp_do_fragment_route()
           : 创建包大小的skbs。对于每个新的skb：
           -> rt->output() (== mctp_route_output)
              -> dev_queue_xmit()
   ```

3. 远程向本地端点发送数据，单包消息：
   
   ```
   mctp_pkttype_receive()
     : 路由查找
     -> rt->output() (== mctp_route_input)
        : sk_key查找
        -> sock_queue_rcv_skb()
   ```

4. 远程向本地端点发送数据，多包消息：
   
   ```
   mctp_pkttype_receive()
     : 路由查找
     -> rt->output() (== mctp_route_input)
        : sk_key查找
        : 将skb存储在struct sk_key->reasm_head中

   mctp_pkttype_receive()
     : 路由查找
     -> rt->output() (== mctp_route_input)
        : sk_key查找
        : 在sk_key->reasm_head中找到已存在的重组包
        : 添加新片段
        -> sock_queue_rcv_skb()
   ```

### 关键引用计数

- 键由以下内容引用：

  - 一个skb：在路由输出期间，存储在`skb->cb`中
  - 网络命名空间(netns)和套接字列表
* 密钥可以与一个设备关联，这种情况下它们会持有对该设备的引用（通过 `key->dev` 设置，通过 `dev->key_count` 计数）。多个密钥可以引用同一个设备。
