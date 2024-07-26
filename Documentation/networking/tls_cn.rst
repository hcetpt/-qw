翻译为中文：

.. _kernel_tls:

==========
内核 TLS
==========

概述
========

传输层安全（TLS）是一种上层协议（ULP），运行在TCP之上。TLS提供了端到端的数据完整性和保密性。

用户界面
==============

创建一个TLS连接
-------------------------

首先创建一个新的TCP套接字并设置TLS ULP。
.. code-block:: c

  sock = socket(AF_INET, SOCK_STREAM, 0);
  setsockopt(sock, SOL_TCP, TCP_ULP, "tls", sizeof("tls"));

设置TLS ULP使我们能够设置/获取TLS套接字选项。目前，仅对称加密是在内核中处理的。完成TLS握手后，我们就有了将数据路径移至内核所需的所有参数。对于移动发送和接收操作，有一个单独的套接字选项。
.. code-block:: c

  /* 来自 linux/tls.h */
  struct tls_crypto_info {
          unsigned short version;
          unsigned short cipher_type;
  };

  struct tls12_crypto_info_aes_gcm_128 {
          struct tls_crypto_info info;
          unsigned char iv[TLS_CIPHER_AES_GCM_128_IV_SIZE];
          unsigned char key[TLS_CIPHER_AES_GCM_128_KEY_SIZE];
          unsigned char salt[TLS_CIPHER_AES_GCM_128_SALT_SIZE];
          unsigned char rec_seq[TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE];
  };


  struct tls12_crypto_info_aes_gcm_128 crypto_info;

  crypto_info.info.version = TLS_1_2_VERSION;
  crypto_info.info.cipher_type = TLS_CIPHER_AES_GCM_128;
  memcpy(crypto_info.iv, iv_write, TLS_CIPHER_AES_GCM_128_IV_SIZE);
  memcpy(crypto_info.rec_seq, seq_number_write,
					TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE);
  memcpy(crypto_info.key, cipher_key_write, TLS_CIPHER_AES_GCM_128_KEY_SIZE);
  memcpy(crypto_info.salt, implicit_iv_write, TLS_CIPHER_AES_GCM_128_SALT_SIZE);

  setsockopt(sock, SOL_TLS, TLS_TX, &crypto_info, sizeof(crypto_info));

发送和接收是分别设置的，但设置过程相同，只需使用TLS_TX或TLS_RX即可。

发送TLS应用程序数据
----------------------------

设置TLS_TX套接字选项后，通过此套接字发送的所有应用程序数据都会使用TLS和套接字选项中提供的参数进行加密。
例如，我们可以发送一个加密的“hello world”记录如下：
.. code-block:: c

  const char *msg = "hello world\n";
  send(sock, msg, strlen(msg));

如果可能的话，send()的数据会直接从用户空间缓冲区加密到加密的内核发送缓冲区。
sendfile系统调用将以最大长度（2^14）的TLS记录发送文件的数据。
.. code-block:: c

  file = open(filename, O_RDONLY);
  fstat(file, &stat);
  sendfile(sock, file, &offset, stat.st_size);

除非传递了MSG_MORE，否则每个send()调用后都会创建并发送TLS记录。如果传递了MSG_MORE，则会延迟记录的创建，直到没有传递MSG_MORE或者达到最大记录大小为止。
内核需要分配一个用于加密数据的缓冲区
这个缓冲区在调用send()时被分配，因此要么整个send()调用返回-ENOMEM（或等待内存），要么加密总是成功。如果send()返回-ENOMEM并且套接字缓冲区中还残留着前一个使用MSG_MORE调用的数据，那么这些MSG_MORE数据仍然保留在套接字缓冲区中。
接收 TLS 应用数据
------------------------------

在设置了 TLS_RX 套接字选项后，所有 recv 系列的套接字调用都会使用提供的 TLS 参数进行解密。必须接收到一个完整的 TLS 记录才能进行解密。
.. code-block:: c

  char buffer[16384];
  recv(sock, buffer, 16384);

如果用户缓冲区足够大，接收到的数据会直接解密到该缓冲区中，并且不会发生额外的分配。如果用户空间缓冲区太小，则数据会在内核中解密后再复制到用户空间。
如果接收到的消息中的 TLS 版本与通过 setsockopt 设置的版本不匹配，则返回 ``EINVAL``。
如果接收到的消息太大，则返回 ``EMSGSIZE``。
如果因其他原因导致解密失败，则返回 ``EBADMSG``。
发送 TLS 控制消息
-------------------------

除了应用数据之外，TLS 还有控制消息，例如警报消息（记录类型 21）和握手消息（记录类型 22）等。可以通过 CMSG 提供 TLS 记录类型来发送这些消息。下面的函数使用指定的记录类型发送 @data 中的 @length 字节数据：
.. code-block:: c

  /* 使用 record_type 发送 TLS 控制消息 */
  static int klts_send_ctrl_message(int sock, unsigned char record_type,
                                    void *data, size_t length)
  {
        struct msghdr msg = {0};
        int cmsg_len = sizeof(record_type);
        struct cmsghdr *cmsg;
        char buf[CMSG_SPACE(cmsg_len)];
        struct iovec msg_iov;   /* 数据发送/接收向量 */

        msg.msg_control = buf;
        msg.msg_controllen = sizeof(buf);
        cmsg = CMSG_FIRSTHDR(&msg);
        cmsg->cmsg_level = SOL_TLS;
        cmsg->cmsg_type = TLS_SET_RECORD_TYPE;
        cmsg->cmsg_len = CMSG_LEN(cmsg_len);
        *CMSG_DATA(cmsg) = record_type;
        msg.msg_controllen = cmsg->cmsg_len;

        msg_iov.iov_base = data;
        msg_iov.iov_len = length;
        msg.msg_iov = &msg_iov;
        msg.msg_iovlen = 1;

        return sendmsg(sock, &msg, 0);
  }

控制消息数据应提供未加密的形式，并由内核进行加密。
接收 TLS 控制消息
------------------------------

TLS 控制消息通过用户空间缓冲区传递，消息类型通过 cmsg 提供。如果没有提供 cmsg 缓冲区，接收到控制消息时会返回错误。数据消息可以在没有设置 cmsg 缓冲区的情况下接收。
.. code-block:: c

  char buffer[16384];
  char cmsg[CMSG_SPACE(sizeof(unsigned char))];
  struct msghdr msg = {0};
  msg.msg_control = cmsg;
  msg.msg_controllen = sizeof(cmsg);

  struct iovec msg_iov;
  msg_iov.iov_base = buffer;
  msg_iov.iov_len = 16384;

  msg.msg_iov = &msg_iov;
  msg.msg_iovlen = 1;

  int ret = recvmsg(sock, &msg, 0 /* 标志 */);

  struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
  if (cmsg->cmsg_level == SOL_TLS &&
      cmsg->cmsg_type == TLS_GET_RECORD_TYPE) {
      int record_type = *((unsigned char *)CMSG_DATA(cmsg));
      // 对 record_type 和缓冲区中的控制消息数据执行相应操作
  }
请注意，`record_type` 可能等于应用数据（23）} 否则 {
      // 缓冲区包含应用数据
}

`recv` 永远不会返回来自混合类型的 TLS 记录的数据。
集成到用户空间的 TLS 库
------------------------------

在高层次上，内核 TLS 用户层协议 (ULP) 是用户空间 TLS 库记录层的替代品。
一个使用 ktls 作为记录层的 OpenSSL 补丁集可以在 [这里](https://github.com/Mellanox/openssl/commits/tls_rx2) 找到。
使用 gnutls 在握手后直接调用 `send` 的[示例](https://github.com/ktls/af_ktls-tool/commits/RX)。
因为它没有实现完整的记录层，所以不支持控制消息。
可选优化
--------------

如果被请求的话，在某些特定条件下，TLS ULP 可以进行一些优化。这些优化要么不是普遍有益的，要么可能会影响正确性，因此需要明确选择启用。
所有选项都是通过 `setsockopt()` 按每个套接字设置，并且可以使用 `getsockopt()` 和 socket 诊断工具（如 `ss` 命令）来检查它们的状态。
TLS_TX_ZEROCOPY_RO
~~~~~~~~~~~~~~~~~~

仅适用于设备卸载。允许 `sendfile()` 数据直接传输到 NIC，而无需在内核中进行复制。这使得当设备卸载启用时，可以实现真正的零拷贝行为。
应用程序必须确保数据在提交和传输完成之间不被修改。换句话说，这主要适用于通过sendfile()发送的套接字数据为只读的情况。修改数据可能导致原始TCP传输与TCP重传使用了不同版本的数据。对接收方而言，这看起来像是TLS记录已被篡改，并将导致记录验证失败。

TLS_RX_EXPECT_NO_PAD
~~~~~~~~~~~~~~~~~~~~

仅适用于TLS 1.3。期望发送方不对记录进行填充。这允许数据直接解密到用户空间缓冲区中（针对TLS 1.3）。
只有当远程端点值得信任时启用此优化才是安全的，否则它可能成为使TLS处理成本翻倍的攻击向量。
如果解密后的记录实际上进行了填充或不是数据记录，则将在无零拷贝的情况下再次解密到内核缓冲区中。
此类事件统计在“TlsDecryptRetry”统计数据中。

### 统计信息

TLS实现暴露了以下每个命名空间的统计信息（`/proc/net/tls_stat`）：

- `TlsCurrTxSw`, `TlsCurrRxSw` - 当前安装的TX和RX会话数量，其中主机处理加密。
- `TlsCurrTxDevice`, `TlsCurrRxDevice` - 当前安装的TX和RX会话数量，其中NIC处理加密。
- `TlsTxSw`, `TlsRxSw` - 使用主机加密打开的TX和RX会话数量。
- `TlsTxDevice`, `TlsRxDevice` - 使用NIC加密打开的TX和RX会话数量。
- `TlsDecryptError` - 记录解密失败（例如，由于认证标签不正确）。
- `TlsDeviceRxResync` - 发送给处理加密的NIC的RX重新同步数量。
- `TlsDecryptRetry` - 由于`TLS_RX_EXPECT_NO_PAD`预测错误而需要重新解密的RX记录数量。注意，这个计数器也会因非数据记录而增加。
- `TlsRxNoPadViolation` - 由于`TLS_RX_EXPECT_NO_PAD`预测错误而需要重新解密的数据RX记录数量。
