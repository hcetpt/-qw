用户空间接口
====================

简介
------------

内核加密API在内核空间可见的概念同样适用于用户空间接口。因此，对于内核内部用例的高级讨论也适用于此处。
然而，主要的区别在于用户空间只能作为转换或密码算法的消费者，而不能作为提供者。
以下内容涵盖了由内核加密API导出的用户空间接口。可以从[1]获得一个与此描述工作示例相关联的库libkcapi。此库可用于需要从内核获取加密服务的用户空间应用程序。
然而，并非所有内核加密API方面都适用于用户空间。这包括同步与异步调用之间的差异。用户空间API调用完全为同步。

用户空间API一般说明
------------------------------

内核加密API可以从用户空间访问。当前可访问以下加密：

- 消息摘要，包括密钥消息摘要（HMAC，CMAC）

- 对称加密

- AEAD加密

- 随机数生成器

接口通过socket类型提供，使用type AF_ALG。此外，setsockopt选项类型为SOL_ALG。如果用户空间头文件尚未导出这些标志，则使用以下宏：

```
#ifndef AF_ALG
#define AF_ALG 38
#endif
#ifndef SOL_ALG
#define SOL_ALG 279
#endif

```

通过与内核API调用相同的方式访问cipher，包括通用与唯一命名方案的cipher以及对通用名称的强制执行。为了与内核加密API交互，用户空间应用程序必须创建一个socket。用户空间通过send()/write()系统调用家族调用cipher操作。cipher操作的结果通过read()/recv()系统调用家族获得。
以下API调用假设socket描述符已经由用户空间应用程序打开，并仅讨论内核加密API特定的调用。
为了初始化socket接口，消费者必须执行以下序列：

1. 使用struct sockaddr_alg参数为不同的cipher类型创建一个AF_ALG类型的socket。
2. 使用socket描述符调用bind。

3. 使用socket描述符调用accept。accept系统调用返回一个新文件描述符，用于与特定cipher实例交互。当调用send/write或recv/read系统调用来向内核发送数据或从内核获取数据时，必须使用accept返回的文件描述符。
就地cipher操作
-------------------------

就像内核操作中的内核加密API一样，用户空间接口允许cipher操作就地进行。这意味着用于send/write系统调用的输入缓冲区和用于read/recv系统调用的输出缓冲区可以是同一个。这对避免对输出数据进行最终目的地的复制特别感兴趣，尤其是在对称cipher操作中。
如果消费者希望将明文和密文保存在不同的内存位置，只需要为加密和解密操作提供不同的内存指针即可。
消息摘要 API
-------------

用于密码操作的消息摘要类型在调用 bind 系统调用时选定。bind 要求调用者提供一个已填充的 struct sockaddr 数据结构。该数据结构必须按照以下方式填充：

::

    struct sockaddr_alg sa = {
        .salg_family = AF_ALG,
        .salg_type = "hash", /* 这会选定内核中的哈希逻辑 */
        .salg_name = "sha1" /* 这是密码算法名称 */
    };

salg_type 的值 "hash" 适用于消息摘要和带密钥的消息摘要。然而，带密钥的消息摘要通过相应的 salg_name 来引用。请参见下面的 setsockopt 接口说明如何为带密钥的消息摘要设置密钥。
使用 send() 系统调用，应用程序提供了需要进行消息摘要处理的数据。send 系统调用允许指定以下标志：

-  MSG_MORE: 如果设置了此标志，则 send 系统调用的行为类似于消息摘要更新函数，在其中最终的哈希值尚未计算。如果未设置此标志，则 send 系统调用立即计算最终的消息摘要。
通过 recv() 系统调用，应用程序可以从内核加密 API 中读取消息摘要。如果缓冲区对于消息摘要来说太小，内核将设置 MSG_TRUNC 标志。
为了设置消息摘要的密钥，调用的应用程序必须使用 setsockopt() 的 ALG_SET_KEY 或 ALG_SET_KEY_BY_KEY_SERIAL 选项。如果没有设置密钥，HMAC 操作将在没有由密钥引起的初始 HMAC 状态改变的情况下执行。
对称密码 API
-------------

操作与消息摘要讨论非常相似。在初始化期间，struct sockaddr 数据结构必须按如下方式填充：

::

    struct sockaddr_alg sa = {
        .salg_family = AF_ALG,
        .salg_type = "skcipher", /* 这会选定对称密码 */
        .salg_name = "cbc(aes)" /* 这是密码算法名称 */
    };

在可以使用 write/send 系统调用家族向内核发送数据之前，消费者必须设置密钥。密钥设置在下面的 setsockopt 调用中描述。
使用 sendmsg() 系统调用，应用程序提供了要进行加密或解密处理的数据。此外，IV（初始化向量）通过 sendmsg() 系统调用提供的数据结构来指定。
sendmsg 系统调用参数 struct msghdr 嵌入到 struct cmsghdr 数据结构中。有关如何将 cmsghdr 数据结构与 send/recv 系统调用家族一起使用的更多信息，请参阅 recv(2) 和 cmsg(3)。该 cmsghdr 数据结构包含以下信息，这些信息通过单独的头实例指定：

-  通过以下标志之一指定密码操作类型：

   -  ALG_OP_ENCRYPT - 数据加密

   -  ALG_OP_DECRYPT - 数据解密

-  通过 ALG_SET_IV 标志指定 IV 信息

send 系统调用家族允许指定以下标志：

-  MSG_MORE: 如果设置了此标志，则 send 系统调用的行为类似于密码更新函数，其中期望在后续调用 send 系统调用时提供更多输入数据。
注意：对于任何意外数据，内核会报告 -EINVAL。调用者必须确保所有数据符合 /proc/crypto 中所选密码的约束条件。
通过 recv() 系统调用，应用程序可以从内核加密 API 中读取密码操作的结果。输出缓冲区必须至少足够大以容纳所有加密或解密数据块。如果输出数据大小较小，则仅返回适合该输出缓冲区大小的数据块数。
AEAD 密码 API
------------

操作非常类似于对称密码的讨论。在初始化期间，`struct sockaddr` 数据结构必须按照以下方式填充：

::

    struct sockaddr_alg sa = {
        .salg_family = AF_ALG,
        .salg_type = "aead", /* 这里选择对称密码 */
        .salg_name = "gcm(aes)" /* 这是密码的名字 */
    };

在使用写入（write）/ 发送（send）系统调用家族向内核发送数据之前，用户必须设置密钥。密钥的设置如下所述的 `setsockopt` 调用中描述。

此外，在使用写入（write）/ 发送（send）系统调用家族向内核发送数据之前，用户还必须设置认证标签（tag）大小。要设置认证标签大小，调用者需要使用下面描述的 `setsockopt` 调用来完成。

通过 `sendmsg()` 系统调用，应用程序提供需要加密或解密的数据。此外，初始化向量（IV）通过 `sendmsg()` 系统调用提供的数据结构来指定。
`sendmsg` 系统调用中的 `struct msghdr` 参数嵌入到 `struct cmsghdr` 数据结构中。有关如何将 `cmsghdr` 数据结构与发送（send）/ 接收（recv）系统调用家族一起使用的更多信息，请参阅 `recv(2)` 和 `cmsg(3)`。该 `cmsghdr` 数据结构包含以下信息，这些信息通过单独的头实例指定：

-  通过以下标志之一指定密码操作类型：

   -  `ALG_OP_ENCRYPT` — 数据加密

   -  `ALG_OP_DECRYPT` — 数据解密

-  通过 `ALG_SET_IV` 标志指定 IV 信息

-  通过 `ALG_SET_AEAD_ASSOCLEN` 标志指定关联的身份验证数据（AAD）。AAD 与明文/密文一同发送给内核。有关内存结构的详细信息，请参见下方。
`send` 系统调用家族允许指定以下标志：

-  `MSG_MORE`：如果设置了此标志，则 `send` 系统调用像一个密码更新函数一样工作，其中期待后续调用 `send` 系统调用时提供更多输入数据。
注意：对于任何意外的数据，内核会报告 `-EINVAL` 错误。调用者必须确保所有数据都符合 `/proc/crypto` 中为所选密码定义的约束条件。
使用 `recv()` 系统调用，应用程序可以从内核密码 API 读取密码操作的结果。输出缓冲区的大小至少应与下方定义的内存结构相同。如果输出数据大小较小，则不会执行密码操作。
经过身份验证的解密操作可能会指示完整性错误。这种完整性的破坏标记为 `-EBADMSG` 错误代码。
### AEAD 内存结构

AEAD 加密算法使用以下信息，这些信息作为单一数据流在用户空间和内核空间之间传递：

- 明文或密文
- 关联认证数据（AAD）
- 认证标签

AAD 和认证标签的大小通过 `sendmsg` 和 `setsockopt` 调用提供（参见相关文档）。由于内核知道整个数据流的大小，现在它可以计算出数据流中各数据组件的正确偏移量。
用户空间调用者必须按照以下顺序安排上述信息：

- AEAD 加密输入：AAD || 明文
- AEAD 解密输入：AAD || 密文 || 认证标签

用户空间调用者提供的输出缓冲区至少要足够大以容纳以下数据：

- AEAD 加密输出：密文 || 认证标签
- AEAD 解密输出：明文

### 随机数生成器 API

随机数生成器 API 的操作与其它 API 类似。初始化时，`struct sockaddr` 数据结构必须如下填充：

```c
struct sockaddr_alg sa = {
    .salg_family = AF_ALG,
    .salg_type = "rng", /* 这里选择随机数生成器 */
    .salg_name = "drbg_nopr_sha256" /* 这是 RNG 的名称 */
};
```

根据随机数生成器类型的不同，可能需要对其进行种子初始化。种子可以通过 `setsockopt` 接口设置密钥来提供。例如，`ansi_cprng` 需要一个种子。DRBG 不需要种子，但可以进行种子初始化。在 NIST SP 800-90A 标准中，种子也被称为“个性化字符串”。
使用 `read()`/`recvmsg()` 系统调用可以获得随机数。
内核一次最多生成 128 字节。如果用户空间需要更多数据，则必须多次调用 `read()`/`recvmsg()`。
**警告**：用户空间调用者可能会多次调用初始提及的 `accept` 系统调用。在这种情况下，返回的文件描述符具有相同的状态。
当内核编译时包含 `CRYPTO_USER_API_RNG_CAVP` 选项时，会启用以下 CAVP 测试接口：

- *熵* 和 *nonce* 的拼接可以通过 `ALG_SET_DRBG_ENTROPY` `setsockopt` 接口提供给 RNG。设置熵需要 `CAP_SYS_ADMIN` 权限。
- *附加数据* 可以使用 `send()`/`sendmsg()` 系统调用来提供，但是只有在设置了熵之后才能这样做。

### 零拷贝接口

除了 `send`/`write`/`read`/`recv` 系统调用家族外，AF_ALG 接口还可以通过 `splice`/`vmsplice` 的零拷贝接口访问。如其名称所示，内核试图避免将数据复制到内核空间。
零拷贝操作要求数据对齐于页面边界。也可以使用未对齐的数据，但这可能需要内核执行更多操作，从而抵消了从零拷贝接口获得的速度提升。
系统固有限制单个零拷贝操作的大小为 16 页。如果要向 AF_ALG 发送更多数据，用户空间必须将输入分割成最大为 16 页的段。
零复制可以与以下代码示例一起使用（一个完整的可运行示例随libkcapi提供）：

::
    
    int pipes[2];

    pipe(pipes);
    /* 输入数据在 iov 中 */
    vmsplice(pipes[1], iov, iovlen, SPLICE_F_GIFT);
    /* opfd 是由 accept() 系统调用返回的文件描述符 */
    splice(pipes[0], NULL, opfd, NULL, ret, 0);
    read(opfd, out, outlen);

设置套接字选项接口
--------------------

除了通过读取/接收和发送/写入系统调用来发送和检索经过密码操作的数据外，用户还需要为密码操作设置额外的信息。这些额外信息是使用必须用打开的密码文件描述符（即由 accept 系统调用返回的文件描述符）调用的 `setsockopt` 系统调用来设置的。
每次 `setsockopt` 调用都必须使用级别 `SOL_ALG`。
`setsockopt` 接口允许使用以下提到的 `optname` 设置下列数据：

-  `ALG_SET_KEY` —— 设置密钥。密钥设置适用于：

   -  对称加密类型 (`skcipher`)

   -  带密钥的消息摘要类型 (`hash`)

   -  认证加密类型 (`AEAD`)

   -  随机数生成器类型 (`RNG`) 来提供种子

- `ALG_SET_KEY_BY_KEY_SERIAL` —— 通过 keyring 的 `key_serial_t` 设置密钥
此操作的行为与 `ALG_SET_KEY` 相同。从 keyring 密钥中复制解密数据，并将其作为对称加密的密钥使用
传入的 `key_serial_t` 必须具有 `KEY_(POS|USR|GRP|OTH)_SEARCH` 权限，否则返回 `-EPERM`。支持的密钥类型：用户、登录、加密和可信
-  `ALG_SET_AEAD_AUTHSIZE` —— 为 AEAD 加密设置认证标签大小
对于加密操作，将生成指定大小的认证标签。对于解密操作，假设提供的密文包含一个指定大小的认证标签（参见下面关于 AEAD 内存布局的部分）
-  `ALG_SET_DRBG_ENTROPY` —— 设置随机数生成器的熵
此选项仅适用于随机数生成器 (`RNG`) 类型

用户空间API示例
----------------------

请参阅 [1]，其中提供了围绕前述Netlink内核接口的一个易于使用的封装库 libkcapi。[1] 还包含了一个测试应用，该应用调用了所有 libkcapi API 调用。
[1] https://www.chronox.de/libkcapi.html
