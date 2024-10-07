SPDX 许可证标识符: GPL-2.0

======================
RxRPC 网络协议
======================

RxRPC 协议驱动程序在 UDP 基础上提供了一种可靠的两阶段传输机制，可用于执行 RxRPC 远程操作。这是通过 AF_RXRPC 类型的套接字实现的，使用带控制数据的 sendmsg() 和 recvmsg() 来发送和接收数据、中止和错误。

本文档内容：

1. 概览
2. RxRPC 协议概要
3. AF_RXRPC 驱动模型
4. 控制消息
5. 套接字选项
6. 安全性
7. 示例客户端用法
8. 示例服务器用法
9. AF_RXRPC 内核接口
(#) 可配置参数
概述
========
RxRPC 是一个两层协议。它有一个会话层，使用 UDP 作为传输层（IPv4 或 IPv6），提供可靠的虚拟连接，并实现了一个真正的网络协议；还有一个表示层，使用 XDR 将结构化数据转换为二进制块并反向转换（就像 SunRPC 一样）：

		+-------------+
		| 应用程序     |
		+-------------+
		|     XDR     |		表示层
		+-------------+
		|    RxRPC    |		会话层
		+-------------+
		|     UDP     |		传输层
		+-------------+

AF_RXRPC 提供了以下功能：

 (1) 为内核和用户空间应用程序提供了一部分 RxRPC 设施，通过将其会话部分作为一个 Linux 网络协议（AF_RXRPC）
(2) 一个两阶段协议。客户端发送一个二进制块（请求），然后接收一个二进制块（响应），而服务器接收请求后发送响应
(3) 保留传输系统为一次调用设置的可重用部分以加快后续调用
(4) 一种安全协议，使用 Linux 内核的密钥管理机制在客户端进行安全管理。服务器端必须更积极地参与安全性协商

AF_RXRPC 不提供 XDR 序列化/表示层设施。这部分由应用程序负责。AF_RXRPC 只处理二进制块。甚至操作ID也只是请求二进制块的前四个字节，因此超出了内核的兴趣范围。

AF_RXRPC 套接字具有以下特点：

 (1) 创建类型为 SOCK_DGRAM；
 (2) 提供它们将要使用的底层传输协议类型 —— 目前仅支持 PF_INET

安德鲁文件系统（AFS）是一个使用该协议的应用示例，它同时包含内核（文件系统）和用户空间（工具）组件。

RxRPC 协议概览
======================
RxRPC 协议概览：

 (#) RxRPC 基于另一个网络协议（目前只有 UDP），并使用此协议提供网络传输。例如，UDP 端口提供了传输端点
(#) RxRPC 支持从任何给定传输端点的多个虚拟“连接”，从而允许端点共享，即使到同一远程端点也是如此。
(#) 每个连接都指向一个特定的“服务”。一个连接不能同时指向多个服务。可以认为服务是RxRPC中的端口号等效物。AF_RXRPC允许多个服务共享一个端点。

(#) 来自客户端的数据包会被标记，因此传输端点可以在客户端和服务器连接之间共享（连接有方向性）。

(#) 在一个本地传输端点与一个远程端点上的一个服务之间，最多可支持十亿个并发连接。一个RxRPC连接由七个数字描述：

本地地址 }
本地端口 } 传输（UDP）地址
远程地址 }
远程端口 }
方向
连接ID
服务ID

(#) 每个RxRPC操作称为一个“调用”。一个连接最多可以进行四十亿次调用，但任何时刻在该连接上同时进行的调用不能超过四个。

(#) 调用分为两个阶段且不对称：客户端发送请求数据，服务端接收；然后服务端发送回复数据，客户端接收。

(#) 数据块的大小不定，每个阶段的结束由数据包中的标志位标记。构成一个数据块的数据包数量不能超过四十亿个，否则会导致序列号回绕。

(#) 请求数据的前四个字节是服务操作ID。

(#) 安全性是在每个连接的基础上协商的。连接由第一个数据包的到来启动。如果需要安全性，则服务器会发出一个“挑战”，然后客户端回复一个“响应”。如果响应成功，则为该连接设置安全性，并且所有后续的调用都将使用相同的安全性。如果服务器在客户端之前断开连接，当客户端再次使用该连接时，安全性将重新协商。

(#) 调用使用ACK数据包来处理可靠性。每个调用的数据包也是明确排序的。

(#) 有两种类型的肯定确认：硬ACK和软ACK。
硬ACK表示远端已经接收到并处理了某个点之前的所有数据；软ACK表示数据已经被接收到，但可能仍会被丢弃并重新请求。发送方不得在数据包被硬ACK确认之前丢弃任何可传输的数据包。
(#) 接收回复数据包会隐式地对构成请求的所有数据包进行硬确认（hard-ACK）
(#) 一次调用在以下条件满足时完成：请求已发送，回复已接收，并且回复的最后一个数据包的最终硬确认已到达服务器
(#) 在调用完成之前，任何一端都可以随时终止调用

AF_RXRPC 驱动模型
=====================

关于 AF_RXRPC 驱动：

(#) AF_RXRPC 协议透明地使用传输协议的内部套接字来表示传输端点
(#) AF_RXRPC 套接字映射到 RxRPC 连接捆绑。实际的 RxRPC 连接是透明处理的。一个客户端套接字可以用于向同一服务发起多个并发调用。一个服务器套接字可以处理来自多个客户端的调用
(#) 为了支持额外的并发调用，将根据可调参数启动额外的并行客户端连接
(#) 每个连接在最后一次使用它的调用完成后会被保留一定的时间（可调），以防新的调用可以重用它
(#) 每个内部 UDP 套接字在最后一个使用它的连接被丢弃后会被保留一定的时间（可调），以防新的连接可以使用它
(#) 客户端连接仅在调用具有相同的描述其安全性的键结构时共享（假设这些调用本来就会共享连接）。未受保护的调用也可以相互共享连接
(#) 如果客户端表明可以共享，则服务器端连接会被共享
(#) 确认（ACK）由协议驱动程序自动处理，包括回应ping请求。
(#) `SO_KEEPALIVE` 自动向另一端发送ping请求以保持连接活跃 [待办事项]。
(#) 如果收到ICMP错误，所有受该错误影响的调用将通过 `recvmsg()` 返回适当的网络错误而被终止。

与RxRPC套接字用户的交互：

(#) 通过绑定一个具有非零服务ID的地址，使一个套接字成为一个服务器套接字。
(#) 在客户端，发送请求是通过一个或多个 `sendmsg` 调用来实现的，随后通过一个或多个 `recvmsg` 接收响应。
(#) 发送给客户端的第一个请求的 `sendmsg` 包含一个标签，该标签将在与此调用相关的所有其他 `sendmsg` 或 `recvmsg` 中使用。这个标签包含在控制数据中。
(#) `connect()` 用于为客户端套接字提供一个默认的目标地址。这可以通过在调用的第一个 `sendmsg()` 中提供一个替代地址来覆盖（`struct msghdr::msg_name`）。
(#) 如果未绑定的客户端上进行了 `connect()` 调用，则在操作进行之前会随机绑定一个本地端口。
(#) 服务器套接字也可以用于发起客户端调用。为此，调用的第一个 `sendmsg()` 必须指定目标地址。服务器的传输端点用于发送数据包。
(#) 一旦应用程序接收到了与此调用相关的最后一个消息，该标签将保证不再出现，因此可以用于锁定客户端资源。然后可以使用相同的标签启动一个新的调用，而不必担心干扰。
(#) 在服务器中，接收到一个或多个 `recvmsg` 请求，然后通过一个或多个 `sendmsg` 发送回复，最后通过最后一个 `recvmsg` 接收最终的 ACK。
(#) 当发送调用数据时，如果还有更多数据要发送，则 `sendmsg` 会设置 `MSG_MORE` 标志。
(#) 当接收调用数据时，如果还有更多数据要接收，则 `recvmsg` 会设置 `MSG_MORE` 标志。
(#) 当接收调用的数据或消息时，`recvmsg` 会设置 `MSG_EOR` 标志来指示该调用的终端消息。
(#) 可以通过向控制数据中添加一个中止控制消息来终止一个调用。发出中止命令将终止内核对该调用标签的使用。任何等待在该调用接收队列中的消息都将被丢弃。
(#) 中止、忙通知和挑战包由 `recvmsg` 传递，并且控制数据消息将被设置以指示上下文。接收到中止或忙消息将终止内核对该调用标签的使用。
(#) `msghdr` 结构中的控制数据部分用于多种用途：

     (#) 预期或受影响调用的标签。
(#) 发送或接收错误、中止和忙通知。
(#) 传入调用的通知。
(#) 发送调试请求并接收调试回复 [待办]

(#) 当内核接收到一个传入的调用并设置完毕后，它会向服务器应用程序发送一条消息，告知有一个新的调用等待接受 [recvmsg 报告一个特殊的控制消息]。然后，服务器应用程序使用 sendmsg 为新调用分配一个标签。一旦完成，请求数据的第一部分将通过 recvmsg 传递。

(#) 服务器应用程序需要为服务器套接字提供一个密钥环，其中包含其允许的安全类型对应的秘密密钥。当建立安全连接时，内核会在密钥环中查找适当的秘密密钥，然后向客户端发送一个挑战包并接收响应包。内核随后检查该包的授权，并决定是中断连接还是设置安全性。

(#) 客户端用于保护通信的密钥名称由一个套接字选项指定。

sendmsg 的注意事项：

(#) 可以设置 MSG_WAITALL 来告诉 sendmsg 忽略信号，如果对等方在合理的时间内正在接受数据包，则我们可以排队传输所有数据。这要求客户端在每个 2*RTT 时间周期内至少接受一个数据包。
如果没有设置此标志，sendmsg() 将立即返回，如果没有任何数据被消费则返回 EINTR/ERESTARTSYS，否则返回已消费的数据量。

recvmsg 的注意事项：

(#) 如果接收队列中有属于特定调用的一系列数据消息，那么 recvmsg 将继续处理这些消息，直到：
(a) 遇到该调用的接收数据末尾，
(b) 遇到非数据消息，
(c) 遇到属于其他调用的消息，或
(d) 填充了用户缓冲区。
如果以阻塞模式调用 recvmsg，它将继续休眠，等待进一步的数据接收，直到上述四种情况之一发生。

(2) MSG_PEEK 类似地工作，但会在将任何数据放入缓冲区后立即返回，而不是等到能够填满缓冲区才返回。

(3) 如果填充用户缓冲区时只消费了一部分数据消息，则该消息的剩余部分将留在队列前面供下一个接收者使用。MSG_TRUNC 永远不会被标记。
(4) 如果在一次调用中有更多的数据（还没有复制该阶段最后一个数据消息的最后一个字节），则会标记 MSG_MORE。

控制消息
=========

AF_RXRPC 在 sendmsg() 和 recvmsg() 中使用控制消息来复用调用、触发某些操作以及报告某些条件。这些控制消息如下：

| 消息ID | SRT 数据 | 含义 |
| :--: | :--: | :--: |
| RXRPC_USER_CALL_ID | sr- 用户ID | 应用程序的调用标识符 |
| RXRPC_ABORT | srt 中断代码 | 发送/接收的中断代码 |
| RXRPC_ACK | -rt 无 | 收到最终ACK |
| RXRPC_NET_ERROR | -rt 错误编号 | 调用中的网络错误 |
| RXRPC_BUSY | -rt 无 | 调用被拒绝（服务器繁忙） |
| RXRPC_LOCAL_ERROR | -rt 错误编号 | 遇到本地错误 |
| RXRPC_NEW_CALL | -r- 无 | 收到新调用 |
| RXRPC_ACCEPT | s-- 无 | 接受新调用 |
| RXRPC_EXCLUSIVE_CALL | s-- 无 | 建立独占客户端调用 |
| RXRPC_UPGRADE_SERVICE | s-- 无 | 客户端调用可以升级 |
| RXRPC_TX_LENGTH | s-- 数据长度 | 发送数据的总长度 |

（SRT = 可用于Sendmsg / 由Recvmsg传递 / 终端消息）

(#) RXRPC_USER_CALL_ID

此字段用于指示应用程序的调用ID。它是一个无符号长整型，应用程序可以在客户端通过将其附加到第一个数据消息中指定，或者在服务器端通过与RXRPC_ACCEPT消息关联来指定。recvmsg()会在所有消息中传递它，除了RXRPC_NEW_CALL消息。

(#) RXRPC_ABORT

此字段可用于让应用程序通过sendmsg中断一个调用，或者由recvmsg传递以指示接收到远程中断。无论哪种方式，都必须与RXRPC_USER_CALL_ID关联以指明受影响的调用。如果发送中断时没有对应用户ID的调用，则返回错误EBADSLT。

(#) RXRPC_ACK

此字段传递给服务器应用程序，以指示已从客户端收到调用的最终ACK。它将与RXRPC_USER_CALL_ID关联以指示已完成的调用。

(#) RXRPC_NET_ERROR

此字段传递给应用程序，以指示在尝试与对等方通信过程中遇到ICMP错误消息。控制消息数据中包含表示问题的errno类整数值，并且RXRPC_USER_CALL_ID将指明受影响的调用。

(#) RXRPC_BUSY

此字段传递给客户端应用程序，以指示由于服务器繁忙导致调用被拒绝。它将与RXRPC_USER_CALL_ID关联以指明被拒绝的调用。

(#) RXRPC_LOCAL_ERROR

此字段传递给应用程序，以指示遇到本地错误并且因此调用被中断。控制消息数据中包含表示问题的errno类整数值，并且RXRPC_USER_CALL_ID将指明受影响的调用。

(#) RXRPC_NEW_CALL

此字段传递给服务器应用程序，以指示有一个新调用到达并等待接受。没有用户ID与此关联，因为必须通过执行RXRPC_ACCEPT来分配用户ID。

(#) RXRPC_ACCEPT

此字段由服务器应用程序用来尝试接受一个调用并为其分配用户ID。它应与RXRPC_USER_CALL_ID关联以指明要分配的用户ID。如果没有可接受的调用（可能超时、被中断等），则sendmsg将返回错误ENODATA。如果用户ID已被其他调用使用，则返回错误EBADSLT。

(#) RXRPC_EXCLUSIVE_CALL

此字段用于指示应在一次性连接上建立客户端调用。一旦调用终止，连接将被丢弃。
(#) RXRPC_UPGRADE_SERVICE

     此选项用于客户端调用，以探测指定的服务ID是否可以由服务器升级。调用者必须检查recvmsg()返回的msg_name，以确定实际使用的服务ID。被探测的操作在两个服务中必须接受相同的参数。
一旦使用此选项确定了服务器的升级能力（或缺乏该能力），则应使用返回的服务ID进行所有后续通信，并且不应再设置RXRPC_UPGRADE_SERVICE。

(#) RXRPC_TX_LENGTH

     此选项用于通知内核一个调用（无论是客户端请求还是服务响应）将要传输的总数据量。如果提供了这个值，则允许内核直接从用户空间缓冲区加密到数据包缓冲区，而不是先复制到缓冲区再进行加密。这只能与提供调用数据的第一个sendmsg()一起使用。如果实际提供的数据量不同，将生成EMSGSIZE错误。
此选项需要一个__s64类型的参数来指示将要传输的数据量。此值不得小于零。
符号RXRPC__SUPPORTED定义为最高支持的控制消息类型加一。在运行时，可以通过RXRPC_SUPPORTED_CMSG套接字选项查询此值（见下文）。

==============
SOCKET OPTIONS
==============

AF_RXRPC套接字在SOL_RXRPC级别上支持以下一些套接字选项：

(#) RXRPC_SECURITY_KEY

     此选项用于指定要使用的密钥描述。密钥通过request_key()从调用进程的密钥环中提取，应该属于"rxrpc"类型。
optval指针指向描述字符串，而optlen表示字符串长度，不包括NUL终止符。

(#) RXRPC_SECURITY_KEYRING

     类似于上述选项，但指定要使用的服务器秘密密钥环（密钥类型为"keyring"）。请参阅“安全性”部分。

(#) RXRPC_EXCLUSIVE_CONNECTION

     此选项用于请求每次通过此套接字进行调用时使用新连接。optval应为NULL，optlen为0。

(#) RXRPC_MIN_SECURITY_LEVEL

     此选项用于指定在此套接字上调用所需的最低安全级别。optval必须指向包含以下值之一的int变量：

     (a) RXRPC_SECURITY_PLAIN

         仅加密校验和
(b) RXRPC_SECURITY_AUTH

    加密校验和加上填充后的数据包及其前八个字节的加密——这包括实际的数据包长度。
(c) RXRPC_SECURITY_ENCRYPT

    加密校验和加上整个数据包的填充和加密，包括实际的数据包长度。
(#) RXRPC_UPGRADEABLE_SERVICE

    此选项用于指示一个具有两个绑定的服务套接字可以根据客户端请求将一个已绑定的服务升级为另一个服务。`optval` 必须指向一个包含两个无符号短整数的数组。第一个是需要升级的服务ID，第二个是要升级到的服务ID。
(#) RXRPC_SUPPORTED_CMSG

    这是一个只读选项，会将一个整数写入缓冲区，表示支持的最高控制消息类型。

========
安全
========

目前，仅实现了 Kerberos 4 等效协议（安全索引 2 - rxkad）。这要求加载 rxkad 模块，并且在客户端需要从 AFS KAServer 或 Kerberos 服务器获取适当类型的票据并安装为“rxrpc”类型的密钥。通常使用 klog 程序完成此操作。可以在以下位置找到一个简单的 klog 程序示例：

    http://people.redhat.com/~dhowells/rxrpc/klog.c

客户端传递给 `add_key()` 的负载应具有以下形式：

    struct rxrpc_key_sec2_v1 {
        uint16_t       security_index;      /* 2 */
        uint16_t       ticket_length;       /* ticket[] 的长度 */
        uint32_t       expiry;              /* 过期时间 */
        uint8_t        kvno;                /* 密钥版本号 */
        uint8_t        __pad[3];
        uint8_t        session_key[8];      /* DES 会话密钥 */
        uint8_t        ticket[0];           /* 加密票据 */
    };

其中票据块只是附加到上述结构的末尾。对于服务器，必须向服务器提供类型为“rxrpc_s”的密钥。它们的描述形式为 “<serviceID>:<securityIndex>”（例如：对于 AFS VL 服务的 rxkad 密钥，描述为 “52:2”）。创建此类密钥时，应将服务器的秘密密钥作为实例化数据（参见下面的示例）：

    add_key("rxrpc_s", "52:2", secret_key, 8, keyring);

通过在 sockopt 中命名一个密钥环来将其传递给服务器套接字。当建立安全的传入连接时，服务器套接字会在该密钥环中查找服务器的秘密密钥。可以在以下位置找到的一个示例程序中看到这一点：

    http://people.redhat.com/~dhowells/rxrpc/listen.c

====================
客户端使用示例
====================

客户端可以通过以下步骤发出操作：

1. 创建一个 RxRPC 套接字：

    client = socket(AF_RXRPC, SOCK_DGRAM, PF_INET);

    其中第三个参数指定了所使用的传输套接字的协议族——通常是 IPv4，但也可以是 IPv6 [待完成]。
2. 可选地绑定本地地址：

    struct sockaddr_rxrpc srx = {
        .srx_family   = AF_RXRPC,
        .srx_service  = 0,  /* 我们是客户端 */
        .transport_type = SOCK_DGRAM,  /* 传输套接字类型 */
        .transport.sin_family = AF_INET,
        .transport.sin_port   = htons(7000),  /* AFS 回调端口 */
        .transport.sin_address = 0,  /* 所有本地接口 */
    };
    bind(client, &srx, sizeof(srx));

    这指定了要使用的本地 UDP 端口。如果不指定，则使用一个随机的非特权端口。多个不相关的 RxRPC 套接字可以共享一个 UDP 端口。安全性基于每个 RxRPC 虚拟连接进行处理。
3. 设置安全性：

    const char *key = "AFS:cambridge.redhat.com";
    setsockopt(client, SOL_RXRPC, RXRPC_SECURITY_KEY, key, strlen(key));

    这将发出一个 `request_key()` 来获取代表安全上下文的密钥。可以设置最低安全级别：

    unsigned int sec = RXRPC_SECURITY_ENCRYPT;
    setsockopt(client, SOL_RXRPC, RXRPC_MIN_SECURITY_LEVEL,
               &sec, sizeof(sec));
4. 然后可以指定要联系的服务器（或者也可以通过 `sendmsg()` 完成）：

    struct sockaddr_rxrpc srx = {
        .srx_family   = AF_RXRPC,
        .srx_service  = VL_SERVICE_ID,
        .transport_type = SOCK_DGRAM,  /* 传输套接字类型 */
        .transport.sin_family = AF_INET,
        .transport.sin_port   = htons(7005),  /* AFS 卷管理器 */
        .transport.sin_address = ...,
    };
    connect(client, &srx, sizeof(srx));
5. 应使用一系列带有以下控制消息的 `sendmsg()` 调用将请求数据发布到服务器套接字：

    ==================    ===================================
    RXRPC_USER_CALL_ID    指定此调用的用户ID
    ==================    ===================================

    在请求的最后部分之外的所有部分中，应在 `msghdr::msg_flags` 中设置 `MSG_MORE`。可以同时发出多个请求。
一段RXRPC传输长度控制信息也可以在首次调用sendmsg()时指定。
如果一个调用的目的地不是通过connect()指定的默认目的地，那么应在该调用的第一个请求消息中设置msghdr::msg_name。

（6）回复数据将被发布到服务器套接字上，供recvmsg()接收。如果某个特定调用还有更多的回复数据需要读取，recvmsg()会标记MSG_MORE。对于某个调用的最后一段读取，MSG_EOR将被设置。
所有数据都将附带以下控制信息一起传递：

RXRPC_USER_CALL_ID - 指定此调用的用户ID

如果发生中断或错误，这将在控制数据缓冲区中返回，并且MSG_EOR将被标记以指示该调用的结束。
客户端可以在首次调用sendmsg()时提供RXRPC_UPGRADE_SERVICE，请求将其已知的服务ID升级为更优的服务（如果有可用的话）。然后，客户端应在收集结果时检查recvmsg()填充的msg_name中的srx_service。如果服务忽略了升级请求，srx_service将保持与sendmsg()提供的相同值；否则，它将被修改以指示服务器升级到的服务ID。请注意，升级后的服务ID由服务器选择。
调用者必须等到在回复中看到服务ID后才能发送更多调用（对同一目的地的进一步调用将被阻止，直到探测完成为止）。

示例服务器使用
====================
服务器可以按以下方式设置以接受操作：

（1）创建一个RxRPC套接字：

```
server = socket(AF_RXRPC, SOCK_DGRAM, PF_INET);
```

其中第三个参数指定了所使用的传输套接字的地址类型 - 通常是IPv4。
（2）如果需要，可以通过给套接字添加包含服务器密钥的密钥环来设置安全性：

```
keyring = add_key("keyring", "AFSkeys", NULL, 0, KEY_SPEC_PROCESS_KEYRING);

const char secret_key[8] = { 0xa7, 0x83, 0x8a, 0xcb, 0xc7, 0x83, 0xec, 0x94 };
add_key("rxrpc_s", "52:2", secret_key, 8, keyring);

setsockopt(server, SOL_RXRPC, RXRPC_SECURITY_KEYRING, "AFSkeys", 7);
```

在给套接字提供了密钥环之后，还可以对其进行操作。这允许服务器在运行过程中添加更多密钥、替换密钥等。
（3）然后必须绑定本地地址：

```
struct sockaddr_rxrpc srx = {
    .srx_family = AF_RXRPC,
    .srx_service = VL_SERVICE_ID, /* RxRPC服务ID */
    .transport_type = SOCK_DGRAM, /* 传输套接字类型 */
    .transport.sin_family = AF_INET,
    .transport.sin_port = htons(7000), /* AFS回调端口 */
    .transport.sin_address = 0, /* 所有本地接口 */
};
bind(server, &srx, sizeof(srx));
```

如果传输参数相同，可以将多个服务ID绑定到一个套接字。目前的限制是两个。为此，应调用两次bind()。
（4）如果需要服务升级，则首先必须绑定两个服务ID，然后设置以下选项：

```
unsigned short service_ids[2] = { from_ID, to_ID };
setsockopt(server, SOL_RXRPC, RXRPC_UPGRADEABLE_SERVICE, service_ids, sizeof(service_ids));
```

如果请求了服务升级，这将自动将来自from_ID的服务连接升级到to_ID的服务。这将反映在请求数据传递到用户空间时通过recvmsg()获得的msg_name中。
(5) 然后服务器设置为监听传入的调用：

```c
listen(server, 100);
```

(6) 内核通过向服务器发送每个待处理的传入连接的消息来通知服务器。这是通过在服务器套接字上使用 `recvmsg()` 接收的。它没有数据，并且附带一个无数据的控制消息：

```c
RXRPC_NEW_CALL
```

此时 `recvmsg()` 返回的地址应被忽略，因为当该消息被接收时，所对应的调用可能已经结束——在这种情况下，队列中剩余的第一个调用将被接受。

(7) 服务器通过发出带有两个控制数据而不带实际数据的 `sendmsg()` 来接受新的调用：

```plaintext
==================	==============================
RXRPC_ACCEPT		表示接受连接
RXRPC_USER_CALL_ID	指定此调用的用户ID
==================	==============================
```

(8) 第一个请求数据包随后将被发布到服务器套接字上，供 `recvmsg()` 捕获。此时，可以从此调用的 `msghdr` 结构中的地址字段读取 RxRPC 地址。

后续请求数据将在到达时发布到服务器套接字上供 `recvmsg()` 收集。除了最后一个数据包外，所有数据包都将带有 `MSG_MORE` 标志。

所有数据都将附带以下控制消息：

```plaintext
==================	===================================
RXRPC_USER_CALL_ID	指定此调用的用户ID
==================	===================================
```

(9) 应答数据应通过一系列带有以下控制消息的 `sendmsg()` 调用来发布到服务器套接字上：

```plaintext
==================	===================================
RXRPC_USER_CALL_ID	指定此调用的用户ID
==================	===================================
```

除最后一个消息外，对于特定调用的所有消息都应在 `msghdr::msg_flags` 中设置 `MSG_MORE`。

(10) 客户端的最终 ACK 将在收到时发布供 `recvmsg()` 检索。它将采取一个带有两个控制消息的无数据消息的形式：

```plaintext
==================	===================================
RXRPC_USER_CALL_ID	指定此调用的用户ID
RXRPC_ACK		表示最终ACK（无数据）
==================	===================================
```

`MSG_EOR` 将被标记以表示这是此调用的最后一个消息。

(11) 在发送最后一个应答数据包之前，可以通过带有以下控制消息的无数据消息调用 `sendmsg()` 来中止调用：

```plaintext
==================	===================================
RXRPC_USER_CALL_ID	指定此调用的用户ID
RXRPC_ABORT		表示中止代码（4字节数据）
==================	===================================
```

如果发出此命令，套接字接收队列中等待的数据包将被丢弃。

请注意，特定服务的所有通信都是通过一个服务器套接字进行的，使用 `sendmsg()` 和 `recvmsg()` 上的控制消息来确定受影响的调用。

AF_RXRPC 内核接口
=================

AF_RXRPC 模块还提供了一个用于内核工具（如 AFS 文件系统）的接口。这允许此类工具：

(1) 直接在单个套接字上的各个客户端调用中使用不同的密钥，而无需为每个可能使用的密钥打开大量的套接字。

(2) 避免在发出调用或打开套接字时让 RxRPC 调用 `request_key()`。相反，工具负责在适当的时间点请求密钥。例如，AFS 可以在执行 VFS 操作（如 `open()` 或 `unlink()`）期间这样做。然后在发起调用时传递该密钥。

(3) 请求使用不同于 `GFP_KERNEL` 的内存分配器。
(4) 避免使用 recvmsg() 调用带来的开销。RxRPC 消息可以在进入套接字接收队列之前被拦截，并直接操作套接字缓冲区。

要使用 RxRPC 设施，内核工具仍然需要打开一个 AF_RXRPC 套接字，根据需要绑定地址并监听（如果它是一个服务器套接字），然后将其传递给内核接口函数。
内核接口函数如下：

(#) 开始一个新的客户端调用：

```c
struct rxrpc_call *
rxrpc_kernel_begin_call(struct socket *sock,
                        struct sockaddr_rxrpc *srx,
                        struct key *key,
                        unsigned long user_call_ID,
                        s64 tx_total_len,
                        gfp_t gfp,
                        rxrpc_notify_rx_t notify_rx,
                        bool upgrade,
                        bool intr,
                        unsigned int debug_id);
```

这会分配新的 RxRPC 调用所需的基础设施，并分配调用和连接编号。该调用将在套接字绑定的 UDP 端口上进行。如果没有提供替代地址（srx 为非 NULL），则调用将发送到已连接客户端套接字的目的地址。

如果提供了 key，则将使用此 key 来保护调用，而不是使用与套接字绑定的 RXRPC_SECURITY_KEY sockopt。以这种方式保护的调用仍可能共享连接（如果可能的话）。

`user_call_ID` 与在控制数据缓冲区中提供给 `sendmsg()` 的值等效。完全可以使用它来指向一个内核数据结构。

`tx_total_len` 是调用者打算通过此调用传输的数据量（或在此时未知则为 -1）。设置数据大小可以让内核直接加密到数据包缓冲区，从而节省一次复制。该值不得小于 -1。

`notify_rx` 是一个指针，指向当发生诸如传入数据包或远程中止等事件时应调用的函数。

如果客户端操作希望请求服务器升级服务到更好的一种，则应将 `upgrade` 设置为 true。结果的服务 ID 将由 `rxrpc_kernel_recv_data()` 返回。

如果调用应该是可中断的，则应将 `intr` 设置为 true。如果没有设置此选项，此函数可能不会返回直到分配了通道；如果设置了此选项，该函数可能会返回 -ERESTARTSYS。

`debug_id` 是用于跟踪的调用调试 ID。可以通过原子递增 `rxrpc_debug_id` 获取它。
### 函数成功时的返回值

如果此函数成功，将返回一个指向RxRPC调用的不透明引用。此时调用者持有了对该调用的引用，并且必须正确结束该引用。

#### 关闭客户端调用

```c
void rxrpc_kernel_shutdown_call(struct socket *sock, struct rxrpc_call *call);
```

此函数用于关闭先前开始的一个调用。用户调用ID将从AF_RXRPC的知识中删除，并且不会再与指定的调用相关联。

#### 释放客户端调用的引用

```c
void rxrpc_kernel_put_call(struct socket *sock, struct rxrpc_call *call);
```

此函数用于释放调用者对RxRPC调用的引用。

#### 通过调用发送数据

```c
typedef void (*rxrpc_notify_end_tx_t)(struct sock *sk, unsigned long user_call_ID, struct sk_buff *skb);

int rxrpc_kernel_send_data(struct socket *sock, struct rxrpc_call *call, struct msghdr *msg, size_t len, rxrpc_notify_end_tx_t notify_end_rx);
```

此函数用于提供客户端调用的请求部分或服务器调用的响应部分。`msg->msg_iovlen` 和 `msg->msg_iov` 指定了要使用的数据缓冲区。`msg_iov` 不得为NULL，并且必须指向内核虚拟地址。如果后续还有数据发送，则可以给 `msg->msg_flags` 设置 `MSG_MORE` 标志。

消息不得指定目标地址、控制数据或任何除 `MSG_MORE` 以外的标志。`len` 是要传输的总数据量。

`notify_end_rx` 可以是NULL，也可以用于指定一个在调用状态变为结束Tx阶段时要调用的函数。此函数将在持有自旋锁的情况下被调用，以防止最后一个DATA包在函数返回前被发送出去。

#### 从调用接收数据

```c
int rxrpc_kernel_recv_data(struct socket *sock, struct rxrpc_call *call, void *buf, size_t size, size_t *_offset, bool want_more, u32 *_abort, u16 *_service);
```

此函数用于从客户端调用的响应部分或服务调用的请求部分接收数据。`buf` 和 `size` 指定了所需的数据量及其存储位置。内部会将 `_offset` 加到 `buf` 上，并从 `size` 中减去；在返回之前，复制到缓冲区中的数据量会被加到 `_offset` 上。

如果后续还需要更多数据，则 `want_more` 应为true；否则为false。

有三种正常的返回值：0 表示缓冲区已填满且 `want_more` 为true；1 表示缓冲区已填满，最后一个DATA包已被清空且 `want_more` 为false；-EAGAIN 表示需要再次调用该函数。

如果处理了最后一个DATA包但缓冲区中的数据少于请求的数量，则返回 EBADMSG。如果未设置 `want_more` 但还有更多数据可用，则返回 EMSGSIZE。
如果检测到远程中止，接收到的中止代码将存储在 ``*_abort`` 中，并返回 ECONNABORTED。
调用最终关联的服务ID将返回到 *_service。这可以用来判断一个调用是否得到了服务升级。
(#) 中止一个调用??

     ::

     void rxrpc_kernel_abort_call(struct socket *sock,
				      struct rxrpc_call *call,
				      u32 abort_code);

     当调用仍处于可中止状态时，此函数用于中止该调用。指定的中止代码将被放入发送的ABORT消息中。

(#) 拦截接收到的RxRPC消息::

     typedef void (*rxrpc_interceptor_t)(struct sock *sk,
					     unsigned long user_call_ID,
					     struct sk_buff *skb);

     void
     rxrpc_kernel_intercept_rx_messages(struct socket *sock,
					 rxrpc_interceptor_t interceptor);

     这个函数在指定的AF_RXRPC套接字上安装一个拦截器函数。所有原本会进入套接字接收队列的消息都将被重定向到这个函数。需要注意的是，必须正确处理这些消息以保持数据消息的顺序性。
拦截器函数本身提供了套接字地址和处理传入消息的方法、内核工具为调用分配的ID以及包含消息的套接字缓冲区。
skb->mark字段指示了消息类型：

	===============================	=======================================
	Mark				Meaning
	===============================	=======================================
	RXRPC_SKB_MARK_DATA		数据消息
	RXRPC_SKB_MARK_FINAL_ACK	接收到的传入调用的最终ACK
	RXRPC_SKB_MARK_BUSY		因服务器繁忙而拒绝的客户端调用
	RXRPC_SKB_MARK_REMOTE_ABORT	对端中止的调用
	RXRPC_SKB_MARK_NET_ERROR	检测到的网络错误
	RXRPC_SKB_MARK_LOCAL_ERROR	遇到的本地错误
	RXRPC_SKB_MARK_NEW_CALL		等待接受的新传入调用
	===============================	=======================================

     可以使用rxrpc_kernel_get_abort_code()探测远程中止消息。
两个错误消息可以用rxrpc_kernel_get_error_number()来探测。
一个新的调用可以通过rxrpc_kernel_accept_call()来接受。
数据消息的内容可以通过常规的套接字缓冲区操作函数进行提取。通过 `rxrpc_kernel_is_data_last()` 可以确定一个数据消息是否为序列中的最后一个。当一个数据消息被处理完毕后，应调用 `rxrpc_kernel_data_consumed()`。

消息应传递给 `rxrpc_kernel_free_skb()` 进行释放。可以获取各种类型消息的额外引用以便稍后释放，但这可能会将调用的状态锁定到消息最终被释放为止。

(#) 接受一个传入调用：

```c
struct rxrpc_call *
rxrpc_kernel_accept_call(struct socket *sock,
			 unsigned long user_call_ID);
```

此函数用于接受一个传入调用并为其分配一个调用ID。此函数类似于 `rxrpc_kernel_begin_call()`，且接受的调用必须以相同的方式结束。

如果此函数成功，将返回一个对 RxRPC 调用的不透明引用。调用者现在持有该引用，并且必须正确地结束调用。

(#) 拒绝一个传入调用：

```c
int rxrpc_kernel_reject_call(struct socket *sock);
```

此函数用于向套接字队列上的第一个传入调用发送 BUSY 消息以拒绝它。如果没有传入调用，则返回 `-ENODATA`。

如果调用已中止（-ECONNABORTED）或超时（-ETIME），则可能返回其他错误。

(#) 分配一个空密钥以实现匿名安全：

```c
struct key *rxrpc_get_null_key(const char *keyname);
```

此函数用于分配一个空的 RxRPC 密钥，可用于表示特定域中的匿名安全。

(#) 获取调用的对等方地址：

```c
void rxrpc_kernel_get_peer(struct socket *sock, struct rxrpc_call *call,
			   struct sockaddr_rxrpc *_srx);
```

此函数用于查找调用的远程对等方地址。

(#) 设置调用的总传输数据大小：

```c
void rxrpc_kernel_set_tx_length(struct socket *sock,
				struct rxrpc_call *call,
				s64 tx_total_len);
```

此函数设置调用中调用者打算传输的数据量。它旨在用于设置回复大小，而请求大小应在开始调用时设置。`tx_total_len` 不得小于零。

(#) 获取调用 RTT：

```c
u64 rxrpc_kernel_get_rtt(struct socket *sock, struct rxrpc_call *call);
```

此函数获取调用使用的对等方的往返时间（RTT）。返回的值以纳秒为单位。
(#) 检查调用是否仍然存活：

```c
bool rxrpc_kernel_check_life(struct socket *sock,
                             struct rxrpc_call *call,
                             u32 *_life);
void rxrpc_kernel_probe_life(struct socket *sock,
                             struct rxrpc_call *call);
```

第一个函数在接收到对等方的 ACK（包括由发送 PING ACK 引发的 PING 响应 ACK）时更新 `*_life` 中的数字。调用者应该在等待适当的时间间隔后比较两次调用的数值，以判断调用是否仍然存活。只要调用尚未进入完成状态，该函数就会返回 true。

这使得调用者能够在等待服务器处理客户端操作期间判断服务器是否仍然可联系，并且调用是否仍然存在于服务器上。
第二个函数会触发发送一个 PING ACK 来促使对等方回应，从而导致第一个函数返回的值发生变化。注意，此函数必须在 TASK_RUNNING 状态下调用。

(#) 获取远程客户端的纪元：

```c
u32 rxrpc_kernel_get_epoch(struct socket *sock,
                           struct rxrpc_call *call);
```

此函数允许查询传入客户端调用中的包所包含的纪元值。该值将被返回。如果调用仍在进行中，则该函数总是成功的。一旦调用过期，就不应再调用此函数。注意，对于本地客户端调用，仅返回本地纪元。

此值可用于判断远程客户端是否已重启，因为在其他情况下不应改变。

(#) 设置调用的最大生命周期：

```c
void rxrpc_kernel_set_max_life(struct socket *sock,
                               struct rxrpc_call *call,
                               unsigned long hard_timeout);
```

此函数设置调用的最大生命周期为 `hard_timeout`（单位为 jiffies）。如果超时发生，调用将被终止，并返回 -ETIME 或 -ETIMEDOUT。

(#) 在内核中应用 RXRPC_MIN_SECURITY_LEVEL sockopt 到套接字：

```c
int rxrpc_sock_set_min_security_level(struct sock *sk,
                                       unsigned int val);
```

此函数指定了此套接字上的调用所需的最低安全级别。

### 可配置参数

RxRPC 协议驱动程序有一些可通过 `/proc/net/rxrpc/` 中的 sysctl 进行调整的可配置参数：

(#) req_ack_delay

接收带有请求确认标志的包后，在实际发送请求的 ACK 之前等待的毫秒数。
通常，对端不会停止发送包，直到宣传的接收窗口满（最多 255 个包），因此延迟 ACK 允许一次性确认多个包。

(#) soft_ack_delay

接收新包后，在生成软 ACK 以告诉发送方不需要重发之前的毫秒数。
(#) idle_ack_delay

     在接收队列中的所有数据包被消耗后，我们生成硬确认（hard-ACK）以告诉发送方可以释放其缓冲区之前的时间（以毫秒为单位），假设没有其他原因需要发送确认

(#) resend_timeout

     在传输一个数据包之后，在我们再次传输它之前的时间（以毫秒为单位），假设没有从接收方收到确认告诉我们他们已经收到了数据包

(#) max_call_lifetime

     一个调用可能处于进行中状态的最大时间（以秒为单位），在此之后我们会主动终止它

(#) dead_call_expiry

     删除呼叫列表中的死呼叫之前的时间（以秒为单位）。死呼叫会保留一段时间以便重复发送确认（ACK）和中止（ABORT）数据包

(#) connection_expiry

     在连接最后一次使用后将其从连接列表中移除之前的时间（以秒为单位）。当连接存在时，它作为协商安全性的占位符；当它被删除时，必须重新协商安全性

(#) transport_expiry

     在传输最后一次使用后将其从传输列表中移除之前的时间（以秒为单位）。当传输存在时，它用于锚定对等数据并保持连接ID计数

(#) rxrpc_rx_window_size

     接收窗口的大小（以数据包为单位）。这是我们愿意为任何特定调用在内存中持有的未消耗接收数据包的最大数量

(#) rxrpc_rx_mtu

     我们愿意接收的最大数据包MTU大小（以字节为单位）。这向对等方表明我们是否愿意接受巨型数据包

(#) rxrpc_rx_jumbo_max

     我们愿意在一个巨型数据包中接收的数据包的最大数量。巨型数据包中的非终端数据包必须包含一个四字节的头部加上正好1412字节的数据。终端数据包必须包含一个四字节的头部加上任意数量的数据。无论如何，巨型数据包的大小不得超过rxrpc_rx_mtu
