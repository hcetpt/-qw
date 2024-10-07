SPDX 许可证标识符: GPL-2.0

==============================================
管理组件传输协议 (MCTP)
==============================================

`net/mctp/` 包含了根据 DMTF 标准 DSP0236 定义的 MCTP 协议支持。物理接口驱动程序（在规范中称为“绑定”）位于 `drivers/net/mctp/` 中。
核心代码提供了一个基于套接字的接口来发送和接收 MCTP 消息，通过 `AF_MCTP`, `SOCK_DGRAM` 套接字实现。

结构：接口与网络
==================

内核通过两个元素建模本地 MCTP 拓扑结构：接口和网络。

一个接口（或“链路”）是 MCTP 物理传输绑定的一个实例（如 DSP0236 第 3.2.47 节所定义），通常连接到特定硬件设备。这表示为一个 `struct netdevice`。
一个网络通过端点 ID（由 DSP0236 第 3.2.31 节描述）定义了 MCTP 端点的唯一地址空间。网络有一个用户可见的标识符，以便用户空间引用。路由定义是针对单个网络的。
接口关联到一个网络。一个网络可以关联到一个或多个接口。
如果存在多个网络，每个网络可能包含在其他网络上也存在的端点 ID（EID）。

套接字 API
===========

协议定义
--------------------

MCTP 使用 `AF_MCTP` / `PF_MCTP` 作为地址族和协议族。
由于 MCTP 是基于消息的，因此只支持 `SOCK_DGRAM` 类型的套接字。

.. code-block:: C

    int sd = socket(AF_MCTP, SOCK_DGRAM, 0);

目前 `protocol` 参数的唯一值是 0。
如同所有套接字地址族一样，源地址和目标地址通过 `sockaddr` 类型指定，并且使用一个字节的端点地址：

.. code-block:: C

    typedef __u8 mctp_eid_t;

    struct mctp_addr {
            mctp_eid_t s_addr;
    };

    struct sockaddr_mctp {
            __kernel_sa_family_t smctp_family;
            unsigned int smctp_network;
            struct mctp_addr smctp_addr;
            __u8 smctp_type;
            __u8 smctp_tag;
    };

    #define MCTP_NET_ANY 0x0
    #define MCTP_ADDR_ANY 0xff

系统调用行为
--------------

以下部分描述了标准套接字系统调用在 MCTP 特定情况下的行为。这些行为旨在与现有的套接字API保持一致。

``bind()``：设置本地套接字地址
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

接收传入请求包的套接字将绑定到本地地址，使用 ``bind()`` 系统调用：

.. code-block:: C

    struct sockaddr_mctp addr;

    addr.smctp_family = AF_MCTP;
    addr.smctp_network = MCTP_NET_ANY;
    addr.smctp_addr.s_addr = MCTP_ADDR_ANY;
    addr.smctp_type = MCTP_TYPE_PLDM;
    addr.smctp_tag = MCTP_TAG_OWNER;

    int rc = bind(sd, (struct sockaddr *)&addr, sizeof(addr));

这会建立套接字的本地地址。匹配网络、地址和消息类型的传入 MCTP 消息将被此套接字接收。这里“传入”的参考很重要；绑定的套接字只会接收带有 TO 标志的消息，以指示传入请求消息，而不是响应。

``smctp_tag`` 值将配置从该套接字的远端接收的标签。根据上述情况，唯一有效的值是 ``MCTP_TAG_OWNER``，这将导致远程“拥有”的标签被路由到此套接字。由于设置了 ``MCTP_TAG_OWNER``，因此 ``smctp_tag`` 的最低三位未使用；调用者必须将其设为零。

``smctp_network`` 值为 ``MCTP_NET_ANY`` 将配置套接字接收来自任何本地连接网络的传入数据包。特定的网络值将导致套接字仅接收来自该网络的传入消息。

``smctp_addr`` 字段指定了要绑定的本地地址。值为 ``MCTP_ADDR_ANY`` 配置套接字接收发送到任何本地目的地 EID 的消息。

``smctp_type`` 字段指定了要接收的消息类型。仅匹配消息类型中的最低7位（即，最高位IC不是匹配的一部分）。这使得套接字可以接收带有或不带消息完整性检查尾部的数据包。

``sendto()``，``sendmsg()``，``send()``：传输 MCTP 消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

使用 ``sendto()``、``sendmsg()`` 或 ``send()`` 系统调用来传输 MCTP 消息。以 ``sendto()`` 为例：

.. code-block:: C

    struct sockaddr_mctp addr;
    char buf[14];
    ssize_t len;

    /* 设置消息目标 */
    addr.smctp_family = AF_MCTP;
    addr.smctp_network = 0;
    addr.smctp_addr.s_addr = 8;
    addr.smctp_tag = MCTP_TAG_OWNER;
    addr.smctp_type = MCTP_TYPE_ECHO;

    /* 任意要发送的消息，包含消息类型头 */
    buf[0] = MCTP_TYPE_ECHO;
    memcpy(buf + 1, "hello, world!", sizeof(buf) - 1);

    len = sendto(sd, buf, sizeof(buf), 0,
                 (struct sockaddr_mctp *)&addr, sizeof(addr));

``addr`` 的网络和地址字段定义了要发送的目标地址。

如果 ``smctp_tag`` 设置为 ``MCTP_TAG_OWNER``，内核将忽略 ``MCTP_TAG_VALUE`` 中设置的任何位，并生成适合目标 EID 的标签值。如果没有设置 ``MCTP_TAG_OWNER``，则消息将使用指定的标签值发送。如果无法分配标签值，系统调用将报告 ``EAGAIN`` 错误号。
应用程序必须将消息类型字节作为传递给 `sendto()` 的消息缓冲区的第一个字节。如果要在传输的消息中包含消息完整性检查（MIC），则还必须在消息缓冲区中提供 MIC，并且消息类型字节的最高有效位必须为 1。

`sendmsg()` 系统调用允许更紧凑的参数接口，并将消息缓冲区指定为一个散列-聚集列表。目前没有定义任何辅助消息类型（用于通过 `sendmsg()` 传递的 `msg_control` 数据）。

在未连接的套接字上使用 `MCTP_TAG_OWNER` 标签发送消息时，如果没有为该目标分配有效的标签，则会分配一个标签。 `(destination-eid, tag)` 元组充当隐式本地套接字地址，以允许套接字接收对该传出消息的响应。如果之前已经进行了任何分配（对于不同的远程 EID），则该分配将丢失。

套接字只会接收它们已发送请求的响应（TO=1），并且只能对它们收到的请求进行响应（TO=0）。

`recvfrom()`、`recvmsg()`、`recv()`：接收 MCTP 消息
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

应用程序可以使用 `recvfrom()`、`recvmsg()` 或 `recv()` 系统调用来接收 MCTP 消息。以下以 `recvfrom()` 为例：

```c
struct sockaddr_mctp addr;
socklen_t addrlen;
char buf[14];
ssize_t len;

addrlen = sizeof(addr);

len = recvfrom(sd, buf, sizeof(buf), 0,
                (struct sockaddr_mctp *)&addr, &addrlen);

/* 我们可以期望 addr 描述一个 MCTP 地址 */
assert(addrlen >= sizeof(buf));
assert(addr.smctp_family == AF_MCTP);

printf("received %zd bytes from remote EID %d\n", rc, addr.smctp_addr);
```

`recvfrom` 和 `recvmsg` 的地址参数会被填充为传入消息的远程地址，包括标签值（这将需要用于回复消息）。

消息缓冲区的第一个字节将包含消息类型字节。如果消息后面跟有完整性检查，则会在接收到的缓冲区中包含该检查。

`recv()` 系统调用的行为类似，但不向应用程序提供远程地址。因此，这些函数只有在远程地址已知或消息不需要回复的情况下才有用。

像发送调用一样，套接字只会接收它们已发送请求的响应（TO=1），并且只能对它们收到的请求进行响应（TO=0）。

`ioctl(SIOCMCTPALLOCTAG)` 和 `ioctl(SIOCMCTPDROPTAG)`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些标签为应用程序提供了更多控制 MCTP 消息标签的能力，通过显式分配（和丢弃）标签值，而不是内核在 `sendmsg()` 时自动为每个消息分配标签。

通常，只有当您的 MCTP 协议不符合常规的请求/响应模型时，才需要使用这些 ioctl。例如，如果您需要在多个请求之间持久化标签，或者一个请求可能生成多个响应。
在这些情况下，ioctl 系统调用允许您将标签分配（和释放）与单独的消息发送和接收操作解耦。两个 ioctl 都传递一个指向 `struct mctp_ioc_tag_ctl` 的指针：

```C
    struct mctp_ioc_tag_ctl {
        mctp_eid_t      peer_addr;
        __u8            tag;
        __u16           flags;
    };
```

`SIOCMCTPALLOCTAG` 为特定的对等端分配一个标签，应用程序可以在未来的 `sendmsg()` 调用中使用该标签。应用程序需要填充 `peer_addr` 成员为远程 EID。其他字段必须为零。返回时，`tag` 成员将被分配的标签值填充。所分配的标签将设置以下标签位：

- `MCTP_TAG_OWNER`：只有作为标签所有者才有意义去分配标签。

- `MCTP_TAG_PREALLOC`：指示 `sendmsg()` 这是一个预先分配的标签。
- ... 以及实际的标签值，在最低三位 (`MCTP_TAG_MASK`) 中。注意，零是一个有效的标签值。

该标签值应直接用于 `struct sockaddr_mctp` 中的 `smctp_tag` 成员。

`SIOCMCTPDROPTAG` 释放先前由 `SIOCMCTPALLOCTAG` ioctl 分配的标签。`peer_addr` 必须与分配时相同，并且 `tag` 值必须完全匹配从分配返回的标签（包括 `MCTP_TAG_OWNER` 和 `MCTP_TAG_PREALLOC` 位）。`flags` 字段必须为零。

内核内部
=========

MCTP 栈中有几种可能的数据包流：

1. 本地 TX 到远程端点，消息大小 <= MTU ::

    ```plaintext
    sendmsg()
     -> mctp_local_output()
         : 路由查找
         -> rt->output() (== mctp_route_output)
            -> dev_queue_xmit()
    ```

2. 本地 TX 到远程端点，消息大小 > MTU ::

    ```plaintext
    sendmsg()
    -> mctp_local_output()
         -> mctp_do_fragment_route()
            : 创建分包大小的 skbs。对于每个新 skb：
            -> rt->output() (== mctp_route_output)
               -> dev_queue_xmit()
    ```

3. 远程 TX 到本地端点，单包消息 ::

    ```plaintext
    mctp_pkttype_receive()
    : 路由查找
    -> rt->output() (== mctp_route_input)
       : sk_key 查找
       -> sock_queue_rcv_skb()
    ```

4. 远程 TX 到本地端点，多包消息 ::

    ```plaintext
    mctp_pkttype_receive()
    : 路由查找
    -> rt->output() (== mctp_route_input)
       : sk_key 查找
       : 将 skb 存储在 struct sk_key->reasm_head 中

    mctp_pkttype_receive()
    : 路由查找
    -> rt->output() (== mctp_route_input)
       : sk_key 查找
       : 在 sk_key->reasm_head 中找到现有的重组信息
       : 追加新的片段
       -> sock_queue_rcv_skb()
    ```

键引用计数
----------

- 键由以下方式引用：

  - 一个 skb：在路由输出期间，存储在 `skb->cb` 中
  - netns 和 sock 列表
* 密钥可以与一个设备关联，在这种情况下，它们会持有对该设备的引用（通过 `key->dev` 设置，并通过 `dev->key_count` 计数）。多个密钥可以引用同一个设备。
