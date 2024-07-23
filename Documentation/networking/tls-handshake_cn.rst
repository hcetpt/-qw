### SPDX 许可证标识符：GPL-2.0

=======================
内核中的 TLS 握手
=======================

概述
========

传输层安全 (TLS) 是一种运行在 TCP 之上的上层协议 (ULP)。TLS 提供了端到端的数据完整性和保密性，同时还提供了对等方认证。
内核的 kTLS 实现处理了 TLS 记录子协议，但没有处理用于建立 TLS 会话的 TLS 握手子协议。内核用户可以使用本文档中描述的 API 来请求建立 TLS 会话。
存在几种可能的方式在内核中提供握手服务。本文档中描述的 API 被设计为隐藏这些实现的细节，以便内核中的 TLS 用户无需了解握手是如何完成的。

用户握手代理
====================

截至本文撰写时，Linux 内核中尚无 TLS 握手实现。为了提供握手服务，需要在一个网络命名空间中启动一个握手代理（通常在用户空间），其中内核消费者可能需要进行 TLS 握手。握手代理监听来自内核的事件，这些事件表明有一个等待中的握手请求。
通过 netlink 操作将一个打开的套接字传递给握手代理，在握手代理的文件描述符表中创建一个套接字描述符。
如果握手成功完成，握手代理将该套接字升级为使用 TLS ULP，并使用 SOL_TLS 套接字选项设置会话信息。握手代理通过第二个 netlink 操作将套接字返回给内核。

内核握手 API
====================

内核 TLS 用户通过调用其中一个 `tls_client_hello()` 函数在打开的套接字上发起客户端侧的 TLS 握手。首先，它填充一个包含请求参数的结构体：

.. code-block:: c

  struct tls_handshake_args {
        struct socket   *ta_sock;
        tls_done_func_t ta_done;
        void            *ta_data;
        const char      *ta_peername;
        unsigned int    ta_timeout_ms;
        key_serial_t    ta_keyring;
        key_serial_t    ta_my_cert;
        key_serial_t    ta_my_privkey;
        unsigned int    ta_num_peerids;
        key_serial_t    ta_my_peerids[5];
  };

`@ta_sock` 字段引用了一个已打开且已连接的套接字。消费者必须持有对该套接字的引用以防止其在握手过程中被销毁。消费者还必须已经在 `sock->file` 中实例化了一个 `struct file`。
`@ta_done` 包含一个回调函数，当握手完成时会被调用。关于此函数的进一步解释，请参阅下面的“握手完成”部分。
消费者可以在 `@ta_peername` 字段中提供一个以空字符终止的主机名，该主机名作为 ClientHello 的一部分发送。如果没有提供 peername，则使用与服务器 IP 地址关联的 DNS 主机名。
消费者可以通过填写 `@ta_timeout_ms` 字段来强制服务握手代理在一定毫秒数后退出。这使得一旦内核和握手代理都关闭了它们的端点，套接字就可以完全关闭。
认证材料，如 X.509 证书、私钥证书和预共享密钥，在握手请求发起前由消费者实例化并提供给握手代理。消费者可以提供一个私有密钥环，并将其链接到握手代理的进程密钥环中 (@ta_keyring 字段)，以防止这些密钥被其他子系统访问。

要请求基于 X.509 认证的 TLS 会话，消费者需要填写 @ta_my_cert 和 @ta_my_privkey 字段，分别用包含 X.509 证书和该证书私钥的密钥序列号。然后调用此函数：

```c
int ret = tls_client_hello_x509(tls_handshake_args *args, gfp_t gfp_flags);
```

当握手请求正在进行时，该函数返回零。返回零保证了回调函数 @ta_done 将为此套接字被调用。如果无法启动握手，则函数返回负的 errno 值。负的 errno 值保证了回调函数 @ta_done 不会在该套接字上调用。

若要使用预共享密钥初始化客户端侧的 TLS 握手，可使用：

```c
int ret = tls_client_hello_psk(tls_handshake_args *args, gfp_t gfp_flags);
```

在这种情况下，消费者需要在 @ta_my_peerids 数组中填充包含其希望提供的对等方身份的密钥序列号，并在 @ta_num_peerids 字段中填写已填充的数组条目数量。其他字段则按上述方法填充。

要初始化匿名客户端侧的 TLS 握手，可以使用：

```c
int ret = tls_client_hello_anon(tls_handshake_args *args, gfp_t gfp_flags);
```

在这种类型的握手过程中，握手代理不会向远程端提供任何对等方身份信息。仅执行服务器认证（即客户端验证服务器的身份）。因此，建立的会话仅使用加密。

内核中的服务器消费者使用：

```c
int ret = tls_server_hello_x500(tls_handshake_args *args, gfp_t gfp_flags);
```

或

```c
int ret = tls_server_hello_psk(tls_handshake_args *args, gfp_t gfp_flags);
```

参数结构按照上述方式填充。

如果消费者需要取消握手请求，例如因为收到 ^C 或其他紧急事件，消费者可以调用：

```c
bool tls_handshake_cancel(struct sock *sock);
```

如果与 @sock 关联的握手请求已被取消，此函数返回 true。消费者的握手完成回调将不会被调用。如果此函数返回 false，则表示消费者的完成回调已经调用过。

握手完成
=========

当握手代理完成处理后，它会通知内核该套接字可以再次被消费者使用。此时，消费者在 tls_handshake_args 结构中的 @ta_done 字段提供的握手完成回调被调用。

此函数的概要是：

```c
typedef void (*tls_done_func_t)(void *data, int status, key_serial_t peerid);
```

消费者在 tls_handshake_args 结构的 @ta_data 字段中提供的 cookie 会通过此回调的 @data 参数返回。消费者利用此 cookie 来匹配回调与其等待握手完成的线程。

握手的成功状态通过 @status 参数返回：

| 状态    | 意义                                                         |
|---------|--------------------------------------------------------------|
| 0       | TLS 会话成功建立                                             |
| -EACCESS| 远程对等方拒绝握手或认证失败                                 |
| -ENOMEM | 临时资源分配失败                                             |
| -EINVAL | 消费者提供了无效参数                                         |
| -ENOKEY | 缺少认证材料                                                 |
| -EIO    | 发生了意外故障                                               |

@peerid 参数包含一个密钥的序列号，该密钥包含远程对等方的身份，或者如果会话未经过认证则为 TLS_NO_PEERID 的值。

最佳做法是，如果握手失败，则应立即关闭并销毁套接字。
其他考虑因素
--------------------

在握手过程中，内核消费者必须修改套接字的sk_data_ready回调函数，以忽略所有传入的数据。
一旦握手完成的回调函数被调用，就可以恢复正常的接收操作。
一旦建立了TLS会话，消费者必须提供一个缓冲区，并检查随后每次sock_recvmsg()调用中作为一部分的控制消息(CMSG)。每个控制消息都会指示接收到的消息数据是TLS记录数据还是会话元数据。
关于kTLS消费者如何识别已提升为使用TLS ULP的套接字上的传入（解密后的）应用程序数据、警报和握手数据包的详细信息，请参阅tls.rst。

这段翻译保持了原文的技术细节和专业术语，确保了技术文档的准确性和专业性。
