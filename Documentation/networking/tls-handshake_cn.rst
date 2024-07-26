### SPDX 许可证标识符：GPL-2.0

=======================
内核中的 TLS 握手
=======================

概述
========

传输层安全 (TLS) 是一种运行在 TCP 之上的上层协议 (ULP)。TLS 提供了端到端的数据完整性和保密性，同时还提供了对等方认证。
内核的 kTLS 实现处理了 TLS 记录子协议，但没有处理用于建立 TLS 会话的 TLS 握手子协议。内核用户可以使用本文档中描述的 API 请求建立 TLS 会话。
为提供握手服务有几种可能的方法。本文档中描述的 API 被设计为隐藏这些实现细节，以便内核中的 TLS 用户不需要了解握手是如何完成的。

用户握手代理
====================

截至本文档撰写之时，Linux 内核中尚无 TLS 握手实现。为了提供握手服务，需要在每个网络命名空间中启动一个握手代理（通常位于用户空间），其中内核消费者可能需要进行 TLS 握手。握手代理监听来自内核的事件，这些事件表明有等待中的握手请求。
通过 netlink 操作将打开的套接字传递给握手代理，在该代理的文件描述符表中创建一个套接字描述符。
如果握手成功完成，握手代理将该套接字升级为使用 TLS ULP，并使用 SOL_TLS 套接字选项设置会话信息。握手代理通过第二次 netlink 操作将套接字返回给内核。

内核握手 API
====================

内核 TLS 用户通过调用其中一个 `tls_client_hello()` 函数在一个已打开并连接的套接字上发起客户端侧的 TLS 握手。首先，它填充一个包含请求参数的结构：

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

`ta_sock` 字段引用了一个已打开并连接的套接字。用户必须持有对该套接字的引用以防止其在握手过程中被销毁。用户还必须已经在 `sock->file` 中实例化了一个 `struct file` 对象。
`ta_done` 包含一个回调函数，当握手完成后会被调用。关于该函数的进一步解释，请参见下面的“握手完成”部分。
用户可以在 `ta_peername` 字段中提供一个以 NUL 结尾的主机名，该主机名作为 ClientHello 的一部分发送出去。如果没有提供 peername，则使用与服务器 IP 地址关联的 DNS 主机名代替。
用户可以通过填写 `ta_timeout_ms` 字段来强制握手代理在经过一定毫秒数后退出。这使得一旦内核和握手代理都关闭它们的端点后，套接字就可以完全关闭。
认证材料，如 X.509 证书、私钥证书和预共享密钥，在握手请求发起前由消费者实例化并提供给握手代理。消费者可以提供一个私有密钥环，并将其链接到握手代理的进程密钥环中 (@ta_keyring 字段)，以防止这些密钥被其他子系统访问。

要请求基于 X.509 认证的 TLS 会话，消费者需要填写 @ta_my_cert 和 @ta_my_privkey 字段，分别用包含 X.509 证书和该证书私钥的密钥序列号。然后调用此函数：

```c
int ret = tls_client_hello_x509(tls_handshake_args *args, gfp_t gfp_flags);
```

当握手请求正在进行时，该函数返回零。返回零保证了回调函数 @ta_done 将为此套接字被调用。如果无法启动握手，则函数返回负的 errno 值。负的 errno 值保证了回调函数 @ta_done 不会在该套接字上调用。

要使用预共享密钥初始化客户端侧的 TLS 握手，可以使用：

```c
int ret = tls_client_hello_psk(tls_handshake_args *args, gfp_t gfp_flags);
```

在这种情况下，消费者需要在 @ta_my_peerids 数组中填入包含其希望提供的对等方身份的密钥序列号，并在 @ta_num_peerids 字段中填入已填充数组条目的数量。其他字段与上述相同方式填充。

要初始化匿名客户端侧的 TLS 握手，可以使用：

```c
int ret = tls_client_hello_anon(tls_handshake_args *args, gfp_t gfp_flags);
```

在这种类型的握手过程中，握手代理不会向远程端提供任何对等方身份信息。仅执行服务器认证（即客户端验证服务器的身份）。因此，建立的会话仅使用加密。

内核中的服务器消费者使用：

```c
int ret = tls_server_hello_x5009(tls_handshake_args *args, gfp_t gfp_flags);
```

或

```c
int ret = tls_server_hello_psk(tls_handshake_args *args, gfp_t gfp_flags);
```

参数结构与上述情况相同。

如果消费者需要取消握手请求（例如，由于按下 ^C 或其他紧急事件），可以调用：

```c
bool tls_handshake_cancel(struct sock *sock);
```

如果与 @sock 关联的握手请求已被取消，则该函数返回真。消费者的握手完成回调将不会被调用。如果该函数返回假，则表明消费者的完成回调已经调用过。

### 握手完成

当握手代理完成处理后，它会通知内核该套接字可以再次被消费者使用。此时，提供的握手完成回调（位于 tls_handshake_args 结构的 @ta_done 字段）会被调用。

此函数的概要是：

```c
typedef void (*tls_done_func_t)(void *data, int status, key_serial_t peerid);
```

消费者在 tls_handshake_args 结构的 @ta_data 字段中提供一个 cookie，该 cookie 在此回调的 @data 参数中返回。消费者使用此 cookie 来匹配回调与等待握手完成的线程。

握手成功的状态通过 @status 参数返回：

| 状态    | 含义                                                   |
|---------|--------------------------------------------------------|
| 0       | TLS 会话成功建立                                       |
| -EACCESS| 远程对等方拒绝握手或认证失败                            |
| -ENOMEM | 临时资源分配失败                                       |
| -EINVAL | 消费者提供了无效的参数                                 |
| -ENOKEY | 缺少认证材料                                           |
| -EIO    | 发生了意外故障                                         |

@peerid 参数包含包含远程对等方身份的密钥的序列号，或者在会话未经过认证的情况下为 TLS_NO_PEERID 的值。

最佳实践是在握手失败时立即关闭并销毁套接字。
其他考虑因素
--------------------

在握手过程中，内核消费者必须修改套接字的 `sk_data_ready` 回调函数以忽略所有传入的数据。
一旦握手完成的回调函数被调用，可以恢复正常的接收操作。
一旦建立了 TLS 会话，消费者必须提供一个缓冲区来接收随后每个 `sock_recvmsg()` 的控制消息（CMSG）。每个控制消息都会指示接收到的消息数据是 TLS 记录数据还是会话元数据。
有关 kTLS 消费者如何识别套接字升级为使用 TLS ULP 后传入的（解密后的）应用数据、警报和握手包的详细信息，请参见 `tls.rst`。
