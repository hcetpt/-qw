SPDX 许可证标识符: GPL-2.0

======================
RxRPC 网络协议
======================

RxRPC 协议驱动程序在 UDP 基础上提供了一个可靠的两阶段传输，可用于执行 RxRPC 远程操作。这是通过 AF_RXRPC 家族的套接字实现的，使用 sendmsg() 和 recvmsg() 并带有控制数据来发送和接收数据、中止和错误。
本文件内容：

(#) 概览
(#) RxRPC 协议概要
(#) AF_RXRPC 驱动模型
(#) 控制消息
(#) 套接字选项
(#) 安全性
(#) 示例客户端使用
(#) 示例服务器使用
(#) AF_RXRPC 内核接口
(#) 可配置参数
概述
========

RxRPC 是一个两层协议。存在一个会话层，它使用 UDP 在 IPv4（或 IPv6）之上提供可靠的虚拟连接，并实现了一个真正的网络协议；还有一个表示层，利用 XDR 将结构化数据转换为二进制块并反向操作（正如 SunRPC 所做的那样）：

		+-------------+
		| 应用程序    |
		+-------------+
		|     XDR     |		表示层
		+-------------+
		|    RxRPC    |		会话层
		+-------------+
		|     UDP     |		传输层
		+-------------+

AF_RXRPC 提供了以下功能：

(1) 对于内核和用户空间应用程序，AF_RXRPC 都是 RxRPC 设施的一部分，通过将其会话部分作为 Linux 网络协议 (AF_RXRPC) 实现；
(2) 采用两阶段协议。客户端发送一个二进制块（请求），然后接收另一个二进制块（响应），而服务器端则接收请求后发送响应；
(3) 保留为单次调用设置的传输系统可重用部分以加速后续调用；
(4) 安全协议，使用 Linux 内核密钥保留设施来管理客户端的安全性。服务器端在安全协商中必须更加积极。
AF_RXRPC 不提供 XDR 序列化/表示层功能。这部分由应用负责。AF_RXRPC 只处理二进制块。甚至操作ID也只是请求二进制块的前四个字节，因此不在内核的关注范围内。
AF_RXRPC 套接字具有以下特点：

(1) 创建时类型为 SOCK_DGRAM；

(2) 需要指定其使用的底层传输协议类型 — 目前仅支持 PF_INET。
Andrew 文件系统 (AFS) 是使用该协议的一个示例，它既包含内核（文件系统）组件也包括用户空间（工具）组件。
RxRPC 协议概览
======================

RxRPC 协议概览：

(#) RxRPC 构建在另一个网络协议（目前仅支持 UDP）之上，并使用它来提供网络传输。例如，UDP 端口提供传输端点。
(#) RxRPC 支持从任何给定的传输端点发起的多个虚拟“连接”，这允许端点被共享，即使它们指向同一个远程端点。
(#) 每个连接都指向一个特定的“服务”。一个连接不能同时指向多个服务。服务可以被认为等同于端口号在 RxRPC 中的概念。AF_RXRPC 允许多个服务共享一个终端。
(#) 来自客户端的数据包会被标记，因此传输终端可以在客户端和服务器连接之间共享（连接具有方向性）。
(#) 在一个本地传输终端与一个远程终端上的单一服务之间，最多可同时支持十亿个连接。一个 RxRPC 连接由七个数字描述：

本地地址	}
本地端口	} 传输（UDP）地址
远程地址	}
远程端口	}
方向
连接ID
服务ID

(#) 每个 RxRPC 操作被称为一次“调用”。一个连接最多可以进行四十亿次调用，但在任何时刻，一个连接上最多只能有四个调用正在进行。
(#) 调用分为两个阶段且不对称：客户端发送请求数据，服务端接收；然后服务端发送回复数据，客户端接收。
(#) 数据块的大小不定，每个阶段的结束通过数据包中的标志表示。构成单个数据块的数据包数量不得超过四十亿个，否则会导致序列号回绕。
(#) 请求数据的前四个字节是服务操作ID。
(#) 安全性是在每个连接的基础上协商的。连接由第一个到达的数据包发起。如果需要安全性，服务器随后会发出一个“挑战”，然后客户端以“响应”来应答。如果响应成功，则为该连接的生命周期设置安全性，并且所有后续的调用都使用相同的安全设置。如果服务器让连接超时而客户端没有，当客户端再次使用此连接时，安全性将重新协商。
(#) 调用使用确认包(ACK)来处理可靠性问题。每个调用的数据包也被明确排序。
(#) 有两种类型的肯定确认：硬确认(hard-ACKs)和软确认(soft-ACKs)。
硬确认向对端表明所有收到的数据到某个点已被接收并处理；软确认则表明数据已接收但可能仍会被丢弃并重新请求。发送方不得丢弃任何可传输的数据包，直到它们被硬确认为止。
(#) 接收回复数据包隐式地对构成请求的所有数据包进行了硬确认（hard-ACK）。
(#) 一次调用在以下条件满足时完成：请求已发送，回复已接收，并且回复的最后一个数据包的最终硬确认已到达服务器。
(#) 在调用完成之前，任一端都可以随时中止调用。
AF_RXRPC 驱动模型
==================

关于 AF_RXRPC 驱动：

(#) AF_RXRPC 协议透明地使用传输协议的内部套接字来表示传输端点。
(#) AF_RXRPC 套接字映射到 RxRPC 连接捆绑。实际的 RxRPC 连接被透明处理。一个客户端套接字可以用于向同一服务发起多个同时调用。一个服务器套接字可以处理来自多个客户端的调用。
(#) 为了支持额外的同时调用，会根据可调参数的限制启动额外的并行客户端连接。
(#) 每个连接在最后一次使用它的调用完成后会被保留一定时间（可调参数），以防有新的调用可以重用它。
(#) 每个内部 UDP 套接字在最后一次使用它的连接被丢弃后也会被保留一定时间（可调参数），以防有新的连接可以使用它。
(#) 如果调用具有相同的安全描述符结构（即密钥结构），则客户端侧的连接仅在这类调用间共享（假设这些调用本来就会共享连接）。未加密的调用之间也可以共享连接。
(#) 如果客户端声明可以共享，则服务器侧的连接是共享的。
(#) ACK确认由协议驱动程序自动处理，包括对Ping请求的回应。
     
(#) SO_KEEPALIVE通过自动向另一端发送Ping请求来保持连接活性（待办事项）。
     
(#) 如果收到ICMP错误，所有受该错误影响的调用将会被终止，并通过recvmsg()传递一个合适的网络错误。

与RxRPC套接字用户的交互：

(#) 通过使用非零服务ID绑定地址，可以将一个套接字变成服务器套接字。
     
(#) 在客户端中，发送请求是通过一个或多个sendmsg调用来实现的，随后通过一个或多个recvmsg调用来接收响应。
     
(#) 客户端发送请求的第一个sendmsg包含一个标签，这个标签将在与此调用相关的所有其他sendmsg或recvmsg中使用。该标签存在于控制数据中。
     
(#) 使用connect()为客户端套接字提供一个默认的目的地址。可以通过在调用的第一个sendmsg()中提供替代地址（struct msghdr::msg_name）来覆盖此默认地址。
     
(#) 如果在未绑定的客户端上调用connect()，则在操作执行之前会随机绑定一个本地端口。
     
(#) 服务器套接字也可以用于发起客户端调用。为此，在调用的第一个sendmsg()中必须指定目标地址。服务器的传输端点用于发送数据包。
     
(#) 当应用程序接收到与一次调用相关的最后一个消息后，保证不会再看到该标签，因此可以利用该标签来锁定客户端资源。然后可以使用相同的标签发起一个新的调用，而不必担心干扰。
在服务器中，使用一个或多个 `recvmsg` 接收到请求，然后使用一个或多个 `sendmsg` 发送回复，最后使用最后一个 `recvmsg` 接收最终的 ACK。

发送呼叫的数据时，如果该呼叫还有更多数据要发送，则 `sendmsg` 会带有 `MSG_MORE` 标志。

接收呼叫的数据时，如果该呼叫还有更多数据要接收，则 `recvmsg` 的标志中会设置 `MSG_MORE`。

接收呼叫的数据或消息时，`recvmsg` 会标记 `MSG_EOR` 来指示该呼叫的终止消息。

可以通过向控制数据中添加一个中止控制消息来中止一个呼叫。发出中止会终止内核对该呼叫标签的使用。该呼叫接收队列中等待的任何消息将被丢弃。

中止、忙通知和挑战包通过 `recvmsg` 发送，并且控制数据消息会被设置以指示上下文。接收到中止或忙通知会终止内核对该呼叫标签的使用。

`msghdr` 结构体中的控制数据部分用于多种目的：

- 该呼叫的目标或受影响的呼叫标签。
- 发送或接收错误、中止和忙通知。
- 接收入站呼叫的通知。
(#) 发送调试请求并接收调试回复 [待办事项]

(#) 当内核接收到一个传入的调用并设置好后，它会向服务器应用程序发送一条消息以告知有一个新的调用正在等待接受 [recvmsg 报告一个特殊的控制消息]。然后服务器应用程序使用 sendmsg 为新调用分配一个标签。一旦完成，请求数据的第一部分将通过 recvmsg 传递。

(#) 服务器应用程序必须为服务器套接字提供一组密钥环，这些密钥对应于其允许的安全类型。在建立安全连接时，内核会在密钥环中查找相应的秘密密钥，然后向客户端发送挑战数据包并接收响应数据包。内核随后检查数据包的授权，并根据结果中断连接或设置安全性。

(#) 客户端用于保护其通信的密钥名称由一个套接字选项指定。
关于 sendmsg 的说明：

(#) 可以设置 MSG_WAITALL 来告诉 sendmsg 忽略信号，前提是对等方在合理的时间内接受数据包以确保我们能够排队传输所有数据。这要求客户端每 2*RTT 时间段至少接受一个数据包。
如果没有设置这个标志，sendmsg() 将立即返回，如果没有任何数据被消费则返回 EINTR/ERESTARTSYS，或者返回被消费的数据量。

关于 recvmsg 的说明：

(#) 如果接收队列中有一系列属于特定调用的数据消息，则 recvmsg 会一直处理这些消息，直到：

(a) 遇到该调用接收数据的结尾，

(b) 遇到非数据消息，

(c) 遇到另一个调用的消息，或

(d) 填充完用户缓冲区。
如果以阻塞模式调用 recvmsg，它将继续休眠，等待接收更多数据，直到满足上述四个条件之一。

(2) MSG_PEEK 操作类似，但如果已将任何数据放入缓冲区则会立即返回，而不是等到可以填充整个缓冲区才返回。

(3) 如果填充用户缓冲区时仅部分消费了一个数据消息，那么剩余的部分将保留在队列前端供下一个处理者使用。MSG_TRUNC 标志永远不会被设置。
(4) 如果在一次调用中还有更多的数据（即还没有复制该阶段最后一个数据消息的最后一个字节），那么将会设置MSG_MORE标志。

控制消息
=========

AF_RXRPC 利用sendmsg()和recvmsg()中的控制消息来复用调用、触发某些动作以及报告某些状态。这些控制消息包括：

	=======================	=== ===========	===============================
	消息ID		SRT 数据	含义
	=======================	=== ===========	===============================
	RXRPC_USER_CALL_ID	sr- 用户ID	应用程序的调用标识符
	RXRPC_ABORT		srt 中止代码	要发出/已收到的中止代码
	RXRPC_ACK		-rt 无	最终ACK已收到
	RXRPC_NET_ERROR		-rt 错误编号	调用时遇到的网络错误
	RXRPC_BUSY		-rt 无	调用被拒绝（服务器繁忙）
	RXRPC_LOCAL_ERROR	-rt 错误编号	遇到本地错误
	RXRPC_NEW_CALL		-r- 无	收到新的调用
	RXRPC_ACCEPT		s-- 无	接受新调用
	RXRPC_EXCLUSIVE_CALL	s-- 无	发起独占客户端调用
	RXRPC_UPGRADE_SERVICE	s-- 无	客户端调用可以升级
	RXRPC_TX_LENGTH		s-- 数据长度	发送数据的总长度
	=======================	=== ===========	===============================

	(SRT = 可用于Sendmsg / 由Recvmsg传递 / 终端消息)

 (#) RXRPC_USER_CALL_ID

     用于指示应用程序的调用ID。这是一个由应用程序指定的无符号长整型值，在客户端通过将其附加到第一条数据消息或在服务器端与RXRPC_ACCEPT消息一起传递来指定。recvmsg()除了在处理RXRPC_NEW_CALL消息之外的所有消息中都会将它传递。
(#) RXRPC_ABORT

     应用程序可以通过向sendmsg传递此消息来中止一个调用，或者由recvmsg传递以表明远程端发起了中止。无论哪种方式，都必须与RXRPC_USER_CALL_ID相关联，以指定受影响的调用。如果正在发送一个中止消息，并且没有与该用户ID对应的调用，则会返回错误EBADSLT。
(#) RXRPC_ACK

     向服务器应用程序传递，表明从客户端收到了调用的最终ACK。它将与RXRPC_USER_CALL_ID相关联，以指示现在已完成的调用。
(#) RXRPC_NET_ERROR

     向应用程序传递，表明尝试与对等方通信过程中遇到了ICMP错误消息。控制消息的数据中将包含一个errno类整数值以指示问题所在，而RXRPC_USER_CALL_ID则指示受影响的调用。
(#) RXRPC_BUSY

     向客户端应用程序传递，表明由于服务器繁忙而导致调用被拒绝。它将与RXRPC_USER_CALL_ID相关联，以指示被拒绝的调用。
(#) RXRPC_LOCAL_ERROR

     向应用程序传递，表明遇到了本地错误并且因此中止了调用。控制消息的数据中将包含一个errno类整数值以指示问题所在，而RXRPC_USER_CALL_ID则指示受影响的调用。
(#) RXRPC_NEW_CALL

     传递给服务器应用程序，表明有一个新的调用到达并等待接受。这个消息不附带用户ID，因为随后必须通过执行RXRPC_ACCEPT来分配一个用户ID。
(#) RXRPC_ACCEPT

     由服务器应用程序使用以尝试接受一个调用并为其分配用户ID。它应该与RXRPC_USER_CALL_ID相关联以指示要分配的用户ID。如果没有可接受的调用（可能已超时、被中止等），则sendmsg将返回错误ENODATA。如果用户ID已被另一个调用占用，则返回错误EBADSLT。
(#) RXRPC_EXCLUSIVE_CALL

     用于指示应在一次性连接上发起客户端调用。一旦调用终止，该连接将被丢弃。
(#) RXRPC_UPGRADE_SERVICE

     这用于让客户端调用以探测指定的服务ID是否可以由服务器升级。调用者必须检查recvmsg()返回的msg_name以获取实际使用的服务ID。所探测的操作在两种服务中都必须采用相同的参数。
一旦使用此功能确定了服务器的升级能力（或缺乏此类能力），则应使用返回的服务ID进行与该服务器的所有后续通信，并且不应再设置RXRPC_UPGRADE_SERVICE。
(#) RXRPC_TX_LENGTH

     这用于告知内核一个调用（无论是客户端请求还是服务响应）将要传输的数据总量。如果给出，它允许内核直接从用户空间缓冲区加密到数据包缓冲区，而不是先复制到缓冲区然后再就地加密。这只能与提供调用数据的第一个sendmsg()一起给出。如果实际给出的数据量不同，则会生成EMSGSIZE错误。
此参数为__s64类型，指示将传输多少数据。此值不得小于零。
符号RXRPC__SUPPORTED定义为支持的最高控制消息类型的序号加一。在运行时，可以通过RXRPC_SUPPORTED_CMSG套接字选项（见下文）查询此值。

==============
套接字选项
==============

AF_RXRPC套接字在SOL_RXRPC级别上支持以下几种套接字选项：

(#) RXRPC_SECURITY_KEY

     此选项用于指定要使用的密钥描述。密钥通过request_key()从调用进程的密钥环中提取，并且应该是"rxrpc"类型。
optval指向描述字符串，而optlen指示字符串的长度，不包括NUL终止符。
(#) RXRPC_SECURITY_KEYRING

     类似于上述选项，但指定了要使用的服务器秘密密钥环（密钥类型为"keyring"）。请参阅“安全性”部分。
(#) RXRPC_EXCLUSIVE_CONNECTION

     此选项用于请求对通过此套接字进行的每个后续调用使用新的连接。optval应为NULL，optlen为0。
(#) RXRPC_MIN_SECURITY_LEVEL

     此选项用于指定此套接字上的调用所需的最小安全级别。optval必须指向包含以下值之一的int变量：

     (a) RXRPC_SECURITY_PLAIN

	 仅加密校验和
下面是提供的英文内容翻译成中文：

(b) RXRPC_SECURITY_AUTH

    加密的校验和加上填充后的数据包以及数据包的前八个字节被加密，其中包括实际的数据包长度。
(c) RXRPC_SECURITY_ENCRYPT

    加密的校验和加上整个数据包被填充并加密，包括实际的数据包长度。
(#) RXRPC_UPGRADEABLE_SERVICE

    这个选项用于指示如果客户端请求，一个具有两种绑定的服务套接字可以将一种绑定的服务升级到另一种。`optval`必须指向两个无符号短整型数组。第一个是需要升级的服务ID，第二个是升级后的服务ID。
(#) RXRPC_SUPPORTED_CMSG

    这是一个只读选项，它会在缓冲区中写入一个整数来指示支持的最高控制消息类型。

======
安全
======

目前，仅实现了Kerberos 4等效协议（安全索引2 - rxkad）。这要求加载rxkad模块，并且在客户端，从AFS kaserver或Kerberos服务器获取适当类型的票证，并将其安装为"rxrpc"类型的密钥。通常使用klog程序完成。可以在以下位置找到一个简单的klog程序示例：

	http://people.redhat.com/~dhowells/rxrpc/klog.c

客户端通过add_key()提供的负载应如下所示：

    struct rxrpc_key_sec2_v1 {
        uint16_t security_index;       /* 2 */
        uint16_t ticket_length;        /* ticket[] 的长度 */
        uint32_t expiry;               /* 到期时间 */
        uint8_t kvno;                  /* 密钥版本号 */
        uint8_t __pad[3];
        uint8_t session_key[8];        /* DES会话密钥 */
        uint8_t ticket[0];             /* 加密的票证 */
    };

其中票证块只是附加到上述结构之后。
对于服务器，必须向服务器提供类型为"rxrpc_s"的密钥。它们的描述形式为"<serviceID>:<securityIndex>"（例如："52:2"表示AFS VL服务的rxkad密钥）。创建此类密钥时，应该将服务器的私有密钥作为实例化数据（参见下面的例子）：
add_key("rxrpc_s", "52:2", secret_key, 8, keyring);

通过在sockopt中命名它，可以将密钥环传递给服务器套接字。当建立安全的传入连接时，服务器套接字随后会在该密钥环中查找服务器的私有密钥。可以在以下位置找到的一个示例程序中看到这一点：

	http://people.redhat.com/~dhowells/rxrpc/listen.c


==================
客户端使用示例
==================

客户端可以通过以下步骤发起操作：

(1) 通过以下方式设置RxRPC套接字：

	client = socket(AF_RXRPC, SOCK_DGRAM, PF_INET);

    其中第三个参数指示所用传输套接字的协议族 - 通常是IPv4，但也可以是IPv6 [待办]
(2) 可选地绑定本地地址：

	struct sockaddr_rxrpc srx = {
		.srx_family	= AF_RXRPC,
		.srx_service	= 0,  /* 我们是客户端 */
		.transport_type	= SOCK_DGRAM,	/* 传输套接字的类型 */
		.transport.sin_family	= AF_INET,
		.transport.sin_port	= htons(7000), /* AFS回调 */
		.transport.sin_address	= 0,  /* 所有本地接口 */
	};
	bind(client, &srx, sizeof(srx));

    这指定了要使用的本地UDP端口。如果不指定，则使用随机的非特权端口。一个UDP端口可以在几个不相关的RxRPC套接字之间共享。安全性基于每个RxRPC虚拟连接处理
(3) 设置安全性：

	const char *key = "AFS:cambridge.redhat.com";
	setsockopt(client, SOL_RXRPC, RXRPC_SECURITY_KEY, key, strlen(key));

    这将发出一个request_key()以获取代表安全上下文的密钥。可以设置最低安全级别：

	unsigned int sec = RXRPC_SECURITY_ENCRYPT;
	setsockopt(client, SOL_RXRPC, RXRPC_MIN_SECURITY_LEVEL,
		   &sec, sizeof(sec));

(4) 然后可以指定要联系的服务器（或者可以通过sendmsg完成）：

	struct sockaddr_rxrpc srx = {
		.srx_family	= AF_RXRPC,
		.srx_service	= VL_SERVICE_ID,
		.transport_type	= SOCK_DGRAM,	/* 传输套接字的类型 */
		.transport.sin_family	= AF_INET,
		.transport.sin_port	= htons(7005), /* AFS卷管理器 */
		.transport.sin_address	= ...,
	};
	connect(client, &srx, sizeof(srx));

(5) 应使用一系列sendmsg()调用将请求数据发布到服务器套接字，每个调用都带有以下控制消息：

	==================	===================================
	RXRPC_USER_CALL_ID	指定此调用的用户ID
	==================	===================================

    在请求的所有部分中，除了最后一部分之外，都应该在msghdr::msg_flags中设置MSG_MORE。可以同时发起多个请求。
一段 RXRPC_TX_LENGTH 控制消息也可以在首次调用 `sendmsg()` 时指定。
如果一个调用的目的地不是通过 `connect()` 指定的默认目的地，那么在该调用的第一个请求消息上应该设置 `msghdr::msg_name`。
（6）回复数据随后将被发布到服务器套接字上，以便 `recvmsg()` 获取。如果对于某个特定调用还有更多的回复数据可读，`recvmsg()` 将标记 MSG_MORE。对于调用的终端读取操作，MSG_EOR 将被设置。
所有数据都将附带以下控制消息交付：

    RXRPC_USER_CALL_ID —— 指定此调用的用户 ID。

    如果发生中止或错误，这将在控制数据缓冲区中返回，并且 MSG_EOR 将被标记以指示该调用的结束。
客户端可以请求其已知的服务 ID，并要求如果存在更优的服务，则将其升级为该服务，在调用的第一个 `sendmsg()` 中提供 RXRPC_UPGRADE_SERVICE。当收集结果时，客户端应该检查由 `recvmsg()` 填充的 `msg_name` 中的 `srx_service`。如果服务忽略了升级请求，则 `srx_service` 将持有与提供给 `sendmsg()` 相同的值；否则，它将被更改以指示服务器升级到的服务 ID。请注意，升级后的服务 ID 由服务器选择。
调用者必须等到在回复中看到服务 ID 后才能发送更多调用（对同一目的地的进一步调用将被阻止，直到探测完成为止）。

示例服务器使用
====================

服务器将以如下方式设置以接受操作：

（1）创建一个 RxRPC 套接字：

    server = socket(AF_RXRPC, SOCK_DGRAM, PF_INET);

    其中第三个参数指定了传输套接字使用的地址类型——通常是 IPv4。
（2）如果需要，可以通过向套接字提供包含服务器密钥的密钥环来设置安全性：

    keyring = add_key("keyring", "AFSkeys", NULL, 0,
                      KEY_SPEC_PROCESS_KEYRING);

    const char secret_key[8] = {
        0xa7, 0x83, 0x8a, 0xcb, 0xc7, 0x83, 0xec, 0x94 };
    add_key("rxrpc_s", "52:2", secret_key, 8, keyring);

    setsockopt(server, SOL_RXRPC, RXRPC_SECURITY_KEYRING, "AFSkeys", 7);

    密钥环可以在提供给套接字后进行操作。这允许服务器在运行时添加更多密钥、替换密钥等。
（3）然后必须绑定一个本地地址：

    struct sockaddr_rxrpc srx = {
        .srx_family   = AF_RXRPC,
        .srx_service  = VL_SERVICE_ID, /* RxRPC 服务 ID */
        .transport_type = SOCK_DGRAM, /* 传输套接字的类型 */
        .transport.sin_family = AF_INET,
        .transport.sin_port   = htons(7000), /* AFS 回调 */
        .transport.sin_address = 0,  /* 所有本地接口 */
    };
    bind(server, &srx, sizeof(srx));

    可以将多个服务 ID 绑定到一个套接字上，前提是传输参数相同。当前限制为两个。为此，应调用两次 `bind()` 函数。
（4）如果需要服务升级，首先必须绑定两个服务 ID，然后设置以下选项：

    unsigned short service_ids[2] = { from_ID, to_ID };
    setsockopt(server, SOL_RXRPC, RXRPC_UPGRADEABLE_SERVICE,
               service_ids, sizeof(service_ids));

    这将自动将来自 from_ID 的连接升级到 to_ID 的服务，如果它们请求这样做的话。这将反映在通过 `recvmsg()` 获取的 `msg_name` 中，当请求数据被传递到用户空间时。
(5) 然后设置服务器监听传入的调用：

	listen(server, 100);

(6) 内核通过向服务器发送每条待处理的传入连接的消息来通知服务器。这些消息是通过服务器套接字上的recvmsg()接收的，它们没有数据，并且附带一个无数据的控制消息：

	RXRPC_NEW_CALL

 此时recvmsg()返回的地址应该被忽略，因为当该调用被接受时，发布此消息所针对的调用可能已经完成——在这种情况下，队列中尚未处理的第一个调用将被接受。

(7) 接着服务器通过发出包含两个控制数据但没有实际数据的sendmsg()来接受新的调用：

	==================	==============================
	RXRPC_ACCEPT		表明接受连接
	RXRPC_USER_CALL_ID	为此次调用指定用户ID
	==================	==============================

(8) 第一个请求数据包随后将被发布到服务器套接字上以供recvmsg()获取。此时，可以从此调用的msghdr结构的地址字段中读取RxRPC地址。
后续请求数据将在到达时被发布到服务器套接字上以供recvmsg()收集。除了最后一个请求数据包外，所有数据包都将带有MSG_MORE标志。
所有数据都将带有以下控制消息：

	==================	===================================
	RXRPC_USER_CALL_ID	为此次调用指定用户ID
	==================	===================================

(9) 回复数据应通过一系列带有以下控制消息的sendmsg()调用来发布到服务器套接字上：

	==================	===================================
	RXRPC_USER_CALL_ID	为此次调用指定用户ID
	==================	===================================

 对于特定调用的最后一条消息之外的所有消息，在msghdr::msg_flags中应设置MSG_MORE。

(10) 当收到客户端的最终确认时，将以数据为空且附带两个控制消息的形式发布给recvmsg()以供检索：

	==================	===================================
	RXRPC_USER_CALL_ID	为此次调用指定用户ID
	RXRPC_ACK		表明最终确认（无数据）
	==================	===================================

 将使用MSG_EOR标志来表明这是此次调用的最后一条消息。

(11) 在发送回复数据的最后一个包之前，可以通过带有以下控制消息的数据为空的消息调用sendmsg()来中断调用：

	==================	===================================
	RXRPC_USER_CALL_ID	为此次调用指定用户ID
	RXRPC_ABORT		表明中断代码（4字节数据）
	==================	===================================

 如果发出此命令，则将丢弃套接字接收队列中等待的任何数据包。

请注意，对于特定服务的所有通信都是通过一个服务器套接字进行的，使用sendmsg()和recvmsg()上的控制消息来确定受影响的调用。

AF_RXRPC内核接口
=================

AF_RXRPC模块还提供了一个用于内核工具（如AFS文件系统）使用的接口。这允许此类工具：

 (1) 在一个套接字上的单个客户端调用中直接使用不同的密钥，而无需为可能要使用的每个密钥打开大量的套接字。
(2) 避免在发起调用或打开套接字时让RxRPC调用request_key()。相反，该工具负责在适当的时候请求密钥。例如，AFS会在VFS操作（如open()或unlink()）期间这样做。然后在发起调用时传递密钥。
(3) 请求使用GFP_KERNEL以外的内存分配方式。
(4) 避免使用`recvmsg()`调用带来的开销。RxRPC消息可以在进入套接字接收队列之前被拦截，并直接操作套接字缓冲区。

要使用RxRPC功能，内核实用程序仍然需要打开一个AF_RXRPC类型的套接字，根据需要绑定地址，并监听（如果它是一个服务器套接字），然后将其传递给内核接口函数。
内核接口函数如下：

(#) 开始一个新的客户端调用:

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

这分配了发起新的RxRPC调用所需的基础设施，并分配了调用和连接编号。调用将通过该套接字绑定的UDP端口进行。除非提供了替代地址（srx非NULL），否则该调用将发送到已连接客户端套接字的目的地址。
如果提供了密钥，则将使用此密钥来保护调用，而不是使用RXRPC_SECURITY_KEY套接字选项绑定到套接字上的密钥。以这种方式保护的调用仍将尽可能共享连接。
`user_call_ID`等同于在控制数据缓冲区中提供给sendmsg()的值。完全可以使用它来指向一个内核数据结构。
`tx_total_len`是调用者打算通过此调用传输的数据量（或如果此时未知则为-1）。设置数据大小允许内核直接加密到数据包缓冲区，从而节省一次复制。该值不得小于-1。
`notify_rx`是指向当发生诸如传入数据包或远程中断等事件时应调用的函数的指针。
如果客户端操作要求服务器升级服务到更好的服务，则应将`upgrade`设置为true。结果的服务ID由`rxrpc_kernel_recv_data()`返回。
如果调用应该是可中断的，则应将`intr`设置为true。如果没有设置，此函数可能不会返回直到分配了一个通道；如果设置了，函数可能会返回-ERESTARTSYS。
`debug_id`是用于跟踪的调用调试ID。可以通过原子递增`rxrpc_debug_id`获得。
### 如果此功能成功，将返回对 RxRPC 调用的不透明引用。
该调用者现在持有了对该调用的引用，并且必须正确地结束它。

#### 关闭客户端调用:

```c
void rxrpc_kernel_shutdown_call(struct socket *sock,
					struct rxrpc_call *call);
```

此函数用于关闭先前开始的调用。用户调用 ID 从 AF_RXRPC 的记录中删除，并且不再与指定的调用相关联。

#### 释放客户端调用的引用:

```c
void rxrpc_kernel_put_call(struct socket *sock,
				   struct rxrpc_call *call);
```

此函数用于释放调用者在 RxRPC 调用上的引用。

#### 通过调用发送数据:

```c
typedef void (*rxrpc_notify_end_tx_t)(struct sock *sk,
					      unsigned long user_call_ID,
					      struct sk_buff *skb);

int rxrpc_kernel_send_data(struct socket *sock,
				   struct rxrpc_call *call,
				   struct msghdr *msg,
				   size_t len,
				   rxrpc_notify_end_tx_t notify_end_rx);
```

此函数用于提供客户端调用的请求部分或服务器调用的响应部分。`msg.msg_iovlen` 和 `msg.msg_iov` 指定了要使用的数据缓冲区。`msg_iov` 不得为 NULL，并且必须指向内核虚拟地址。如果此调用后续还有数据发送，则可以在 `msg.msg_flags` 中设置 `MSG_MORE` 标志。
消息不得指定目标地址、控制数据或其他标志，除了 `MSG_MORE`。`len` 是要传输的总数据量。
`notify_end_rx` 可以是 NULL，也可以用来指定一个函数，在调用状态变为结束 Tx 阶段时调用该函数。当持有自旋锁时调用此函数，以防止最后一个 DATA 数据包在函数返回前被传输。

#### 从调用接收数据:

```c
int rxrpc_kernel_recv_data(struct socket *sock,
				   struct rxrpc_call *call,
				   void *buf,
				   size_t size,
				   size_t *_offset,
				   bool want_more,
				   u32 *_abort,
				   u16 *_service)
```

此函数用于从客户端调用的响应部分或服务调用的请求部分接收数据。`buf` 和 `size` 指定所需的数据量以及存储位置。`*_offset` 在内部加到 `buf` 上并从 `size` 减去；复制到缓冲区的数据量会在返回前加到 `*_offset` 上。
如果满足条件后还需要更多数据，则 `want_more` 应设为真；如果这是接收阶段的最后一项，则设为假。
有三种正常返回值：0 表示缓冲区已填满且 `want_more` 为真；1 表示缓冲区已填满、最后一个 DATA 数据包已被清空且 `want_more` 为假；-EAGAIN 表示需要再次调用此函数。
如果处理了最后一个 DATA 数据包但缓冲区中的数据少于请求的数量，则返回 EBADMSG。如果未设置 `want_more` 但仍有更多数据可用，则返回 EMSGSIZE。
如果检测到远程 ABORT，接收到的中止代码将被存储在 ``*_abort`` 中，并返回 ECONNABORTED。
调用最终所使用的的服务 ID 将被返回到 *_service 中。
这可以用来判断一个调用是否获得了服务升级。

(#) 中止一个调用??

     ::

     void rxrpc_kernel_abort_call(struct socket *sock,
                                  struct rxrpc_call *call,
                                  u32 abort_code);

     当调用仍处于可中止状态时，此函数用于中止该调用。指定的中止代码将会被放置在发送的 ABORT 消息中。

(#) 拦截接收的 RxRPC 消息 ::

     typedef void (*rxrpc_interceptor_t)(struct sock *sk,
                                         unsigned long user_call_ID,
                                         struct sk_buff *skb);

     void
     rxrpc_kernel_intercept_rx_messages(struct socket *sock,
                                        rxrpc_interceptor_t interceptor);

     此函数为指定的 AF_RXRPC 套接字安装了一个拦截器函数。
所有原本会进入套接字接收队列的消息都被重定向到这个函数中。
需要注意的是，必须妥善处理这些消息以保持数据消息的顺序性。
拦截器函数本身会获得套接字地址、处理传入消息、由内核工具分配给调用的ID以及包含消息的套接字缓冲区。
skb->mark 字段指示了消息类型：

	===============================	=======================================
	Mark				Meaning
	===============================	=======================================
	RXRPC_SKB_MARK_DATA		数据消息
	RXRPC_SKB_MARK_FINAL_ACK	接收到的对一个传入调用的最终确认
	RXRPC_SKB_MARK_BUSY		因服务器繁忙而被拒绝的客户端调用
	RXRPC_SKB_MARK_REMOTE_ABORT	被对等方中止的调用
	RXRPC_SKB_MARK_NET_ERROR	检测到的网络错误
	RXRPC_SKB_MARK_LOCAL_ERROR	遇到的本地错误
	RXRPC_SKB_MARK_NEW_CALL		等待接受的新传入调用
	===============================	=======================================

     可以使用 rxrpc_kernel_get_abort_code() 探测远程中止消息。
两个错误消息可以通过 rxrpc_kernel_get_error_number() 进行探测。
新调用可以通过 rxrpc_kernel_accept_call() 接受。
数据消息可以通过常规的一系列套接字缓冲区操作函数来提取其内容。使用`rxrpc_kernel_is_data_last()`可以判断一个数据消息是否为一系列消息中的最后一个。当一个数据消息被完全处理后，应调用`rxrpc_kernel_data_consumed()`。

消息应当通过`rxrpc_kernel_free_skb()`来处理以进行释放。对于所有类型的消息，都可以获取额外的引用以便稍后释放，但这可能会锁定调用的状态直到消息最终被释放。

(#) 接受传入的调用:

```c
struct rxrpc_call * rxrpc_kernel_accept_call(struct socket *sock, unsigned long user_call_ID);
```

此函数用于接受传入的调用并为其分配一个调用ID。这个函数与`rxrpc_kernel_begin_call()`相似，并且所接受的调用必须以相同的方式结束。
如果此函数成功，将返回RxRPC调用的一个不透明引用。调用者现在持有该引用，并且必须正确地结束调用。

(#) 拒绝传入的调用:

```c
int rxrpc_kernel_reject_call(struct socket *sock);
```

此函数用于向套接字队列中的第一个传入调用发送BUSY消息以拒绝它。如果没有传入调用，则返回-ENODATA。
如果调用已中止（-ECONNABORTED）或超时（-ETIME），可能会返回其他错误。

(#) 分配一个空密钥以实现匿名安全:

```c
struct key *rxrpc_get_null_key(const char *keyname);
```

此函数用于分配一个空的RxRPC密钥，该密钥可用于指示特定域中的匿名安全性。

(#) 获取调用的对等方地址:

```c
void rxrpc_kernel_get_peer(struct socket *sock, struct rxrpc_call *call, struct sockaddr_rxrpc *_srx);
```

此函数用于查找调用的远程对等方地址。

(#) 设置调用上的总传输数据大小:

```c
void rxrpc_kernel_set_tx_length(struct socket *sock, struct rxrpc_call *call, s64 tx_total_len);
```

此函数设置调用者打算在一个调用上传输的数据量。它的预期用途是设置回复的大小，因为请求的大小应在开始调用时设置。`tx_total_len`不能小于零。

(#) 获取调用RTT:

```c
u64 rxrpc_kernel_get_rtt(struct socket *sock, struct rxrpc_call *call);
```

获取调用使用的对等方的往返时间（RTT）。返回的值是以纳秒为单位的时间。
### 检查调用是否仍然存活：

```c
bool rxrpc_kernel_check_life(struct socket *sock,
                             struct rxrpc_call *call,
                             u32 *_life);
void rxrpc_kernel_probe_life(struct socket *sock,
                             struct rxrpc_call *call);
```

第一个函数在接收到对等端的确认（包括PING响应确认，我们可以通过发送PING确认来检测服务器上是否仍然存在该调用）时更新`*_life`中的数字，并将其传递回去。调用者应该比较两次调用返回的数字，以判断调用在等待合适的时间间隔后是否仍然存活。只要调用还没有到达完成状态，该函数就会返回真。

这使得调用者能够判断服务器是否仍然可联系，并且在等待服务器处理客户端操作时，调用在服务器上是否仍然存活。
第二个函数会触发发送一个PING确认，试图促使对等端作出响应，从而导致第一个函数返回的值发生变化。注意，此函数必须在TASK_RUNNING状态下被调用。

### 获取远程客户端的周期：

```c
u32 rxrpc_kernel_get_epoch(struct socket *sock,
                           struct rxrpc_call *call);
```

这允许查询传入客户端调用包中包含的周期值。此值会被返回。如果调用仍在进行中，则该函数总是成功。一旦调用过期，就不应再调用此函数。注意，在本地客户端调用上调用此函数只会返回本地周期。

此值可用于判断远程客户端是否已被重启，因为在其他情况下它不应该改变。

### 设置调用的最大生命周期：

```c
void rxrpc_kernel_set_max_life(struct socket *sock,
                               struct rxrpc_call *call,
                               unsigned long hard_timeout);
```

此函数将调用的最大生命周期设置为`hard_timeout`（单位为时钟节拍）。如果超时发生，调用将被终止并返回-ETIME或-ETIMEDOUT。

### 在内核中为套接字应用RXRPC_MIN_SECURITY_LEVEL套接字选项：

```c
int rxrpc_sock_set_min_security_level(struct sock *sk,
                                       unsigned int val);
```

这指定了此套接字上的调用所需的最小安全级别。

### 可配置参数

RxRPC协议驱动程序有多个可通过/proc/net/rxrpc/中的sysctls进行调整的可配置参数：

1. **req_ack_delay**

    在收到设置了请求确认标志的包之后，在我们遵守该标志并实际发送请求的确认之前等待的时间（毫秒）。
    通常，另一方不会停止发送包直到已宣告的接收窗口满（最多255个包），因此延迟ACK可以一次性确认多个包。

2. **soft_ack_delay**

    在接收到新包之后，在我们生成软确认以告诉发送方不需要重发之前的等待时间（毫秒）。
(#) 闲置确认延迟

    在已接收队列中的所有数据包被处理完后，我们生成硬确认（hard-ACK）以告知发送方可以释放其缓冲区之前等待的时间（以毫秒为单位）。假设在此期间没有其他原因需要我们发送确认。

(#) 重传超时

    发送一个数据包后，在未收到接收方告知已接收到该数据包的确认前，我们再次传输该数据包之前等待的时间（以毫秒为单位）。

(#) 最大调用生命周期

    调用可能处于进行中状态的最大时间（以秒为单位），在此之后我们会主动终止它。

(#) 死调用过期

    从调用列表中移除死调用之前等待的时间（以秒为单位）。死调用会被保留一段时间，以便重复发送确认和中止数据包。

(#) 连接过期

    一个连接自最后一次使用以来经过的时间（以秒为单位），在此之后我们将从连接列表中移除它。当一个连接存在时，它作为协商安全性的占位符；当它被删除时，必须重新协商安全性。

(#) 传输过期

    一个传输自最后一次使用以来经过的时间（以秒为单位），在此之后我们将从传输列表中移除它。当一个传输存在时，它用于锚定对等数据并保持连接ID计数器。

(#) RXRPC接收窗口大小

    接收窗口的大小，以数据包为单位。这是我们愿意为任何特定调用在内存中持有的未处理接收数据包的最大数量。

(#) RXRPC接收MTU

    我们愿意接收的最大数据包MTU大小（以字节为单位）。这向对等方表明我们是否愿意接受巨型数据包。

(#) RXRPC接收巨型数据包最大值

    我们愿意在一个巨型数据包中接收的数据包的最大数量。巨型数据包中的非终结数据包必须包含一个四字节的头部加上正好1412字节的数据。终结数据包必须包含一个四字节的头部加上任意数量的数据。无论如何，巨型数据包的大小不得超出RXRPC接收MTU的限制。
