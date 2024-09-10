SPDX 许可证标识符: GPL-2.0

.. _fsverity:

=======================================================
fs-verity：基于文件的只读完整性保护
=======================================================

介绍
============

fs-verity（`fs/verity/`）是一个支持层，文件系统可以接入以支持透明的完整性和真实性保护。目前，ext4、f2fs 和 btrfs 文件系统都支持 fs-verity。与 fscrypt 类似，支持 fs-verity 并不需要太多特定于文件系统的代码。
fs-verity 类似于 `dm-verity <https://www.kernel.org/doc/Documentation/device-mapper/verity.txt>`_，但它作用于文件而不是块设备。在支持 fs-verity 的文件系统上的普通文件中，用户空间可以执行一个 ioctl 操作，使文件系统为该文件构建一个梅克尔树，并将其持久化到与文件关联的特定位置。在此之后，文件将被设置为只读，并且所有对该文件的读取操作都会自动与文件的梅克尔树进行验证。任何损坏数据（包括通过 mmap 读取的数据）的读取都将失败。
用户空间还可以使用另一个 ioctl 获取 fs-verity 执行的根哈希（实际上是“fs-verity 文件摘要”，它包含梅克尔树根哈希）。这个 ioctl 的执行时间是常数，与文件大小无关。
fs-verity 实质上是一种在常数时间内对文件进行哈希的方法，前提是那些会违反哈希值的读取将在运行时失败。

用例
========

单独来看，fs-verity 只提供完整性保护，即检测非恶意的意外损坏。
然而，由于 fs-verity 使得获取文件哈希极其高效，因此其主要目的是作为支持身份验证（检测恶意修改）或审计（在使用前记录文件哈希）的工具。
可以使用标准文件哈希来替代 fs-verity。但是，如果文件很大且仅访问其中一小部分，则这样做效率低下。例如，对于 Android 应用程序包（APK）文件来说，这种情况很常见。这些文件通常包含许多翻译、类和其他资源，它们在特定设备上很少甚至从未被访问过。在启动应用程序之前读取和哈希整个文件既慢又浪费。
与预先计算的哈希不同，fs-verity 在每次分页时都会重新验证数据。这确保了恶意磁盘固件无法在运行时未被察觉地更改文件内容。
fs-verity 并没有取代或使 dm-verity 过时。对于只读文件系统，仍应使用 dm-verity。fs-verity 是为那些必须存在于读写文件系统上的文件设计的，因为这些文件可能会被独立更新，并且可能是用户安装的，因此无法使用 dm-verity。fs-verity 没有规定特定的文件哈希认证方案。（同样，dm-verity 也没有规定特定的块设备根哈希认证方案。）用于认证 fs-verity 文件哈希的选项包括：

- 可信用户空间代码。通常，访问文件的用户空间代码可以被信任来进行认证。例如，一个希望在使用数据文件之前进行认证的应用程序，或者作为操作系统一部分的应用程序加载器（它已经通过其他方式进行了认证，例如从使用 dm-verity 的只读分区加载），并且希望在加载应用程序之前对其进行认证。在这种情况下，这个可信的用户空间代码可以通过使用 `FS_IOC_MEASURE_VERITY`_ 获取文件的 fs-verity 摘要，然后使用任何支持数字签名的用户空间加密库来验证其签名来认证文件内容。
- 完整性测量架构 (IMA)。IMA 支持将 fs-verity 文件摘要作为其传统完整文件摘要的替代。“IMA 评估”强制文件在其“security.ima”扩展属性中包含有效的、匹配的签名，这由 IMA 策略控制。更多信息，请参阅 IMA 文档。
- 可信用户空间代码与 `内置签名验证`_ 结合使用。这种方法仅应在极其谨慎的情况下使用。

用户 API
========

FS_IOC_ENABLE_VERITY
--------------------

FS_IOC_ENABLE_VERITY ioctl 用于在文件上启用 fs-verity。它接受指向 struct fsverity_enable_arg 的指针，该结构定义如下：

```c
    struct fsverity_enable_arg {
            __u32 version;
            __u32 hash_algorithm;
            __u32 block_size;
            __u32 salt_size;
            __u64 salt_ptr;
            __u32 sig_size;
            __u32 __reserved1;
            __u64 sig_ptr;
            __u64 __reserved2[11];
    };
```

此结构包含了用于构建文件的默克尔树的参数。必须按以下方式初始化：

- `version` 必须是 1
- `hash_algorithm` 必须是用于默克尔树的哈希算法标识符，例如 FS_VERITY_HASH_ALG_SHA256。参见 `include/uapi/linux/fsverity.h` 以获取可能值的列表
- `block_size` 是默克尔树的块大小，以字节为单位。在 Linux v6.3 及更高版本中，这可以是介于（包括）1024 和系统页面大小及文件系统块大小中的较小者之间的任何 2 的幂。在早期版本中，页面大小是唯一允许的值
- `salt_size` 是盐的大小（以字节为单位），如果未提供盐，则为 0。盐是一个附加到每个哈希块前面的值；它可以用来为特定文件或设备个性化哈希。目前最大盐大小为 32 字节
- `salt_ptr` 是指向盐的指针，如果没有提供盐，则为 NULL
- ``sig_size`` 是内置签名的字节大小，如果没有提供内置签名，则为 0。目前，内置签名的大小被（有些随意地）限制在 16128 字节以内。
- ``sig_ptr`` 是指向内置签名的指针，如果没有提供内置签名，则为 NULL。只有在使用 `内置签名验证`_ 功能时才需要内置签名。对于 IMA 评估来说不需要内置签名，如果文件签名完全在用户空间处理也不需要它。
- 所有保留字段必须清零。

FS_IOC_ENABLE_VERITY 会为文件构建一个 Merkle 树，并将其持久化到与该文件关联的文件系统特定位置，然后将文件标记为 verity 文件。此 ioctl 在大文件上执行可能需要较长时间，并且可以被致命信号中断。
FS_IOC_ENABLE_VERITY 检查对节点的写访问权限。然而，它必须在一个只读（O_RDONLY）的文件描述符上执行，并且没有任何进程可以以写方式打开该文件。当此 ioctl 正在执行时尝试以写方式打开文件将会失败并返回 ETXTBSY。（这是为了保证在启用 verity 后不存在可写的文件描述符，并保证在构建 Merkle 树期间文件内容是稳定的。）

成功时，FS_IOC_ENABLE_VERITY 返回 0 并使文件成为 verity 文件。失败时（包括被致命信号中断的情况），文件不会发生任何变化。
FS_IOC_ENABLE_VERITY 可能会因为以下错误而失败：

- ``EACCES``：进程没有对文件的写访问权限
- ``EBADMSG``：内置签名格式不正确
- ``EBUSY``：此 ioctl 已经在这个文件上运行
- ``EEXIST``：文件已经启用了 verity
- ``EFAULT``：调用者提供了不可访问的内存
- ``EFBIG``：文件太大以至于无法启用 verity
- ``EINTR``：操作被致命信号中断
- ``EINVAL``：版本、哈希算法或块大小不受支持；或者保留位被设置；或者文件描述符既不是普通文件也不是目录
- ``EISDIR``：文件描述符指向的是一个目录
- ``EKEYREJECTED``：内置签名与文件不符
- ``EMSGSIZE``：盐或内置签名太长
- ``ENOKEY``：".fs-verity" 密钥环中没有包含验证内置签名所需的证书
- ``ENOPKG``：fs-verity 识别哈希算法，但该算法当前配置下未在内核加密 API 中可用（例如，缺少 CONFIG_CRYPTO_SHA512）
- ``ENOTTY``：这种类型的文件系统没有实现 fs-verity
- ``EOPNOTSUPP``：内核未配置 fs-verity 支持；或者文件系统的超级块未启用 verity 特性；或者文件系统不支持对此文件的 fs-verity。（参见 `文件系统支持`_。）
- ``EPERM``：文件是追加模式；或者需要内置签名但未提供
- ``EROFS``：文件系统是只读的
- ``ETXTBSY``：有人以写方式打开了文件。这可能是调用者的文件描述符、另一个打开的文件描述符，或者是可写的内存映射持有的文件引用。
### FS_IOC_MEASURE_VERITY

`FS_IOC_MEASURE_VERITY` 这个 ioctl 用于获取一个 verity 文件的摘要。`fs-verity` 文件的摘要是一个加密摘要，用于标识在读取时强制执行的文件内容；它是通过 Merkle 树计算得出的，并且不同于传统的全文件摘要。这个 ioctl 需要一个指向变长结构的指针：

```c
struct fsverity_digest {
        __u16 digest_algorithm;
        __u16 digest_size; /* 输入/输出 */
        __u8 digest[];
};
```

`digest_size` 是一个输入/输出字段。输入时，它必须初始化为为变长 `digest` 字段分配的字节数。成功返回 0 时，内核会填充该结构如下：

- `digest_algorithm` 将是用于文件摘要的哈希算法。它将与 `fsverity_enable_arg::hash_algorithm` 匹配。
- `digest_size` 将是摘要的字节大小，例如 SHA-256 的大小为 32 字节。（这可能与 `digest_algorithm` 有冗余。）
- `digest` 将是实际的摘要字节。

`FS_IOC_MEASURE_VERITY` 保证在常数时间内执行，无论文件的大小如何。

`FS_IOC_MEASURE_VERITY` 可能会因为以下错误而失败：

- `EFAULT`：调用者提供了不可访问的内存
- `ENODATA`：文件不是 verity 文件
- `ENOTTY`：这种类型的文件系统没有实现 fs-verity
- `EOPNOTSUPP`：内核没有配置 fs-verity 支持，或者文件系统的超级块没有启用 `verity` 功能。（参见 `Filesystem support`_。）
- `EOVERFLOW`：摘要长度超过指定的 `digest_size` 字节。尝试提供更大的缓冲区

### FS_IOC_READ_VERITY_METADATA

`FS_IOC_READ_VERITY_METADATA` 这个 ioctl 从 verity 文件中读取 verity 元数据。这个 ioctl 自 Linux v5.12 起可用。

这个 ioctl 允许编写一个服务器程序，该程序接收一个 verity 文件并将其提供给客户端程序，以便客户端可以自行验证文件的 fs-verity 兼容性。只有当客户端不信任服务器并且服务器需要为客户端提供存储时，才有意义。

这是一个相对专业化的使用场景，大多数 fs-verity 用户不需要这个 ioctl。
此ioctl接收指向以下结构的指针：

   #define FS_VERITY_METADATA_TYPE_MERKLE_TREE     1
   #define FS_VERITY_METADATA_TYPE_DESCRIPTOR      2
   #define FS_VERITY_METADATA_TYPE_SIGNATURE       3

   struct fsverity_read_metadata_arg {
           __u64 metadata_type;
           __u64 offset;
           __u64 length;
           __u64 buf_ptr;
           __u64 __reserved;
   };

`metadata_type` 指定了要读取的元数据类型：

- `FS_VERITY_METADATA_TYPE_MERKLE_TREE` 读取默克尔树的块。这些块按从根层到叶层的顺序返回。在同一层内，这些块按照其哈希值被再次哈希的顺序返回。有关更多信息，请参见“默克尔树”。
- `FS_VERITY_METADATA_TYPE_DESCRIPTOR` 读取 fs-verity 描述符。请参见“fs-verity 描述符”。
- `FS_VERITY_METADATA_TYPE_SIGNATURE` 读取传递给 FS_IOC_ENABLE_VERITY 的内置签名（如果有的话）。请参见“内置签名验证”。

此ioctl的行为类似于 `pread()`。`offset` 指定了从元数据项中读取的字节偏移量，而 `length` 指定了从元数据项中最多读取的字节数。`buf_ptr` 是要读入缓冲区的指针，转换为一个64位整数。`__reserved` 必须为0。成功时返回读取的字节数。在元数据项末尾时返回0。返回的长度可能小于 `length`，例如当ioctl被中断时。

通过 FS_IOC_READ_VERITY_METADATA 返回的元数据不保证会针对 `FS_IOC_MEASURE_VERITY` 返回的文件摘要进行身份验证，因为预期这些元数据将用于实现与 fs-verity 兼容的验证（尽管在没有恶意磁盘的情况下，元数据确实会匹配）。例如，为了实现此ioctl，文件系统允许直接从磁盘读取默克尔树块，而不实际验证到根节点的路径。

FS_IOC_READ_VERITY_METADATA 可能会遇到以下错误：

- `EFAULT`：调用者提供了无法访问的内存。
- `EINTR`：ioctl 在任何数据读取之前被中断。
- `EINVAL`：保留字段被设置或 `offset + length` 超出了范围。
- `ENODATA`：文件不是 verity 文件，或者请求了 `FS_VERITY_METADATA_TYPE_SIGNATURE` 但文件没有内置签名。
- `ENOTTY`：这种类型的文件系统未实现 fs-verity 或此ioctl尚未在此文件系统上实现。
- `EOPNOTSUPP`：内核未配置 fs-verity 支持，或者文件系统的超级块未启用“verity”功能。（请参见“文件系统支持”。）

FS_IOC_GETFLAGS
---------------

现有的 ioctl FS_IOC_GETFLAGS（该ioctl不仅限于 fs-verity）也可以用来检查文件是否启用了 fs-verity。

为此，请检查返回的标志中是否有 FS_VERITY_FL（0x00100000）。

verity 标志不能通过 FS_IOC_SETFLAGS 设置。必须使用 FS_IOC_ENABLE_VERITY，因为需要提供参数。

statx
-----

自 Linux v5.5 起，statx() 系统调用会在文件启用 fs-verity 时设置 STATX_ATTR_VERITY。这比使用 FS_IOC_GETFLAGS 和 FS_IOC_MEASURE_VERITY 更高效，因为它不需要打开文件，而打开 verity 文件可能会很昂贵。
访问 verity 文件
======================

应用程序可以透明地访问一个 verity 文件，就像访问非 verity 文件一样，但有以下例外：

- Verity 文件是只读的。它们不能被打开以供写入或截断（truncate），即使文件模式位允许这样做也不行。尝试执行这些操作将会因 EPERM 错误而失败。然而，对所有者、模式、时间戳和扩展属性（xattrs）等元数据的更改仍然是允许的，因为这些内容并不受 fs-verity 的度量影响。此外，verity 文件仍然可以被重命名、删除和创建硬链接。
- 不支持在 verity 文件上使用直接 I/O。尝试在这样的文件上使用直接 I/O 将会回退到缓冲 I/O。
- 不支持在 verity 文件上使用 DAX（直接访问），因为这将绕过数据验证。
- 读取与 verity Merkle 树不匹配的数据将会因 EIO 错误（对于 read() 操作）或 SIGBUS 信号（对于 mmap() 读取）而失败。
- 如果 sysctl 参数 "fs.verity.require_signatures" 被设置为 1，并且文件没有通过 ".fs-verity" 密钥环中的密钥签名，则打开该文件将会失败。详见《内置签名验证》部分。
- 不支持直接访问 Merkle 树。因此，如果一个 verity 文件被复制，或者备份并恢复，那么它将失去其“verity”特性。fs-verity 主要用于像可执行文件这样由包管理器管理的文件。

文件摘要计算
=======================

本节描述了 fs-verity 如何使用 Merkle 树对文件内容进行哈希运算，生成用于加密标识文件内容的摘要。此算法适用于所有支持 fs-verity 的文件系统。

用户空间仅在需要自行计算 fs-verity 文件摘要时才需要了解这一算法，例如为了签署文件。

.. _fsverity_merkle_tree:

Merkle 树
-------------

文件内容被划分为块，其中块大小是可配置的，默认通常是 4096 字节。如果需要，最后一个块的末尾会被零填充。然后每个块都会被哈希处理，生成第一级哈希值。接着，这些第一级哈希值会被分组成‘块大小’字节的块（如果需要则在末尾零填充），并对这些块再次进行哈希处理，生成第二级哈希值。这个过程一直继续直到只剩下一个块为止。这个块的哈希值即为“Merkle 树根哈希”。

如果文件恰好适合于一个块并且非空，则“Merkle 树根哈希”就是单个数据块的哈希值。如果文件为空，则“Merkle 树根哈希”全为零。
这里的“块”并不一定等同于“文件系统块”。
如果指定了盐，则将其零填充到哈希算法压缩函数输入大小的最接近倍数，例如SHA-256为64字节或SHA-512为128字节。填充后的盐将被添加到每个被哈希的数据块或默克尔树块之前。
块填充的目的在于使每个哈希都基于相同数量的数据进行计算，这简化了实现，并且为硬件加速保留了更多可能性。盐填充的目的是在预计算加盐哈希状态并在每个哈希中导入时使加盐变得“免费”。

示例：在推荐配置（SHA-256和4K块）下，每个块可以容纳128个哈希值。因此，默克尔树的每一层大约比前一层小128倍，对于大文件，默克尔树的大小收敛到原始文件大小的大约1/127。然而，对于小文件，填充变得显著，使得空间开销比例上更大。

.. _fsverity_descriptor：

fs-verity描述符
--------------------

单独来看，默克尔树根哈希是模糊的。例如，它无法区分一个大文件与一个小文件，后者的数据恰好是第一个文件的顶级哈希块。由于约定填充到下一个块边界也会引起模糊性。
为了解决这个问题，fs-verity文件摘要实际上是以下结构的哈希值，该结构包含默克尔树根哈希以及其他字段，如文件大小::

    struct fsverity_descriptor {
            __u8 version;           /* 必须是1 */
            __u8 hash_algorithm;    /* 默克尔树哈希算法 */
            __u8 log_blocksize;     /* 数据和树块大小的log2 */
            __u8 salt_size;         /* 盐的大小（以字节为单位）；如果没有则为0 */
            __le32 __reserved_0x04; /* 必须是0 */
            __le64 data_size;       /* 构建默克尔树的文件大小 */
            __u8 root_hash[64];     /* 默克尔树根哈希 */
            __u8 salt[32];          /* 每个哈希块前缀的盐 */
            __u8 __reserved[144];   /* 必须是0 */
    };

内置签名验证
===============================

CONFIG_FS_VERITY_BUILTIN_SIGNATURES=y 增加了对内核中验证fs-verity内置签名的支持。
**重要提示**！在使用此功能前请务必小心谨慎。
这不是唯一进行签名的方法，替代方案（如用户空间签名验证和IMA评估）可能会更好。也很容易陷入一种误区，认为这个功能解决了比实际更多的问题。
启用此选项会增加以下功能：

1. 在启动时，内核创建一个名为“.fs-verity”的密钥环。root用户可以使用add_key()系统调用向此密钥环添加受信任的X.509证书。
2. `FS_IOC_ENABLE_VERITY`_ 接受一个指向文件的 fs-verity 摘要的 DER 格式 PKCS#7 格式的分离签名的指针。
成功时，ioctl 将该签名与默克尔树一起持久化。之后，每次打开文件时，内核都会使用 ".fs-verity" 密钥环中的证书来验证文件的实际摘要与该签名是否一致。

3. 新增了一个 sysctl 参数 "fs.verity.require_signatures"
当设置为 1 时，内核要求所有 fs-verity 文件都有一个如 (2) 中所述的有效签名。
(2) 中所述的签名必须是对以下格式的 fs-verity 文件摘要进行签名：

```c
    struct fsverity_formatted_digest {
            char magic[8];                  /* 必须是 "FSVerity" */
            __le16 digest_algorithm;
            __le16 digest_size;
            __u8 digest[];
    };
```

仅此而已。需要再次强调的是，fs-verity 内置签名并不是唯一一种使用 fs-verity 的签名方式。详见 `用例`_ 部分以了解 fs-verity 可能的使用方法。fs-verity 内置签名有一些重要的限制，在使用之前应仔细考虑：

- 内置签名验证并不会使内核强制任何文件实际上启用 fs-verity。因此，它不是一个完整的认证策略。目前，如果使用了内置签名验证，唯一完成认证策略的方法是由可信用户空间代码在访问文件前显式检查文件是否启用了带有签名的 fs-verity。（当 fs.verity.require_signatures=1 时，仅仅检查 fs-verity 是否启用就足够了。）但是，在这种情况下，可信用户空间代码可以直接将签名存储在文件旁边，并使用加密库自行验证，而不是使用此功能。
- 文件的内置签名只能在启用 fs-verity 时同时设置。之后更改或删除内置签名需要重新创建文件。
- 内置签名验证使用同一组公钥对系统上所有启用 fs-verity 的文件进行验证。不同文件不能使用不同的密钥；每个密钥要么全部信任，要么完全不信任。
- sysctl 参数 fs.verity.require_signatures 应用于整个系统。将其设置为 1 只有在系统中所有使用 fs-verity 的用户都同意将其设置为 1 时才有效。这一限制可能会阻止在某些有用场景中使用 fs-verity。
内置签名验证只能使用内核支持的签名算法。例如，内核尚不支持Ed25519，尽管这通常是推荐用于新密码设计的签名算法。

fs-verity 的内置签名采用 PKCS#7 格式，公钥采用 X.509 格式。这些格式被广泛使用，包括由内核的一些其他特性所使用（这也是为什么 fs-verity 内置签名使用它们的原因），并且功能非常丰富。
不幸的是，历史表明，解析和处理这些格式（这些格式来自 20 世纪 90 年代，并基于 ASN.1）的代码通常由于其复杂性而存在漏洞。这种复杂性并不是密码学本身固有的。

对于不需要 X.509 和 PKCS#7 高级特性的 fs-verity 用户，强烈建议使用更简单的格式，如纯 Ed25519 密钥和签名，并在用户空间中验证签名。
即使选择使用 X.509 和 PKCS#7 的 fs-verity 用户也应考虑在用户空间中验证这些签名更加灵活（如本文档前面所述的其他原因），并且消除了启用 CONFIG_FS_VERITY_BUILTIN_SIGNATURES 及其相关内核攻击面增加的需要。在某些情况下，这样做甚至是必要的，因为高级 X.509 和 PKCS#7 特性并不总是能按预期与内核一起工作。例如，内核不会检查 X.509 证书的有效时间。
注意：IMA 评估支持 fs-verity，但其签名不使用 PKCS#7，因此部分避免了这里讨论的问题。IMA 评估确实使用 X.509。

文件系统支持
==============

fs-verity 支持多个文件系统，如下所述。必须启用 CONFIG_FS_VERITY kconfig 选项才能在这任何文件系统上使用 fs-verity。
`include/linux/fsverity.h` 声明了 `fs/verity/` 支持层与文件系统之间的接口。简而言之，文件系统必须提供一个 `fsverity_operations` 结构，该结构提供了将 verity 元数据读取和写入到特定于文件系统的存储位置的方法，包括默克尔树块和 `fsverity_descriptor`。文件系统还必须在某些时候调用 `fs/verity/` 中的函数，例如当文件打开时或页面缓存中读取页面时。（参见《验证数据》_。）

ext4
----

自从 Linux v5.4 和 e2fsprogs v1.45.2 开始，ext4 支持 fs-verity。
要在 ext4 文件系统上创建 verity 文件，文件系统必须使用 `-O verity` 进行格式化，或者运行过 `tune2fs -O verity`。"verity" 是一个 RO_COMPAT 文件系统特性，一旦设置，旧内核将只能以只读方式挂载文件系统，旧版本的 e2fsck 将无法检查文件系统。
最初，具有 "verity" 特性的 ext4 文件系统只能在其块大小等于系统页大小（通常为 4096 字节）时挂载。在 Linux v6.3 中，这一限制已被移除。
ext4 在 verity 文件的磁盘上设置 EXT4_VERITY_FL inode 标志。它只能通过 `FS_IOC_ENABLE_VERITY`_ 设置，并且无法清除。
ext4 还支持加密，可以与 fs-verity 同时使用。在这种情况下，验证的是明文数据而不是密文数据。这是为了使 fs-verity 文件摘要有意义，因为每个文件的加密方式都不同。
ext4 将 verity 元数据（Merkle 树和 fsverity_descriptor）存储在文件末尾之后，从超出 i_size 的第一个 64K 边界开始。这种方法可行的原因是：(a) verity 文件只读；(b) 超出 i_size 的页面对用户空间不可见，但 ext4 可以通过一些相对较小的改动内部读写这些页面。这种方法避免了依赖 EA_INODE 特性以及重新设计 ext4 的扩展属性支持来分页多千兆字节的扩展属性和支持加密扩展属性。请注意，当文件被加密时，verity 元数据 *必须* 加密，因为它包含明文数据的哈希值。
ext4 仅允许在基于范围（extent-based）的文件上使用 verity。

f2fs
----

f2fs 自 Linux v5.4 和 f2fs-tools v1.11.0 起支持 fs-verity。
要在 f2fs 文件系统上创建 verity 文件，该文件系统必须使用 ``-O verity`` 进行格式化。
f2fs 在 verity 文件的磁盘上设置 FADVISE_VERITY_BIT inode 标志。它只能通过 `FS_IOC_ENABLE_VERITY`_ 设置，并且无法清除。
与 ext4 类似，f2fs 也将 verity 元数据（Merkle 树和 fsverity_descriptor）存储在文件末尾之后，从超出 i_size 的第一个 64K 边界开始。参见上面的 ext4 解释。
此外，f2fs 每个inode最多支持 4096 字节的扩展属性条目，这通常不足以容纳一个 Merkle 树块。
f2fs 不支持在当前有原子或易失性写入待处理的文件上启用 verity
btrfs
-----

btrfs 自从 Linux v5.15 版本开始支持 fs-verity。启用 verity 的节点会用一个 RO_COMPAT inode 标志标记，并且 verity 元数据会存储在单独的 btree 项中。

实现细节
=========

验证数据
----------

fs-verity 确保对 verity 文件的所有读取操作都会进行验证，无论使用哪个系统调用来读取（例如 mmap()、read()、pread()），也无论这是第一次读取还是后续读取（除非后续读取可以返回已经被验证过的缓存数据）。下面我们将描述文件系统是如何实现这一点的。

页面缓存
~~~~~~~~~

对于使用 Linux 页面缓存的文件系统，必须修改 `->read_folio()` 和 `->readahead()` 方法，在将 folio 标记为 Uptodate 之前先进行验证。仅仅挂钩 `->read_iter()` 是不够的，因为 `->read_iter()` 不用于内存映射。因此，fs/verity/ 提供了 fsverity_verify_blocks() 函数来验证已经读入 verity 节点页面缓存中的数据。包含的 folio 必须仍然被锁定并且没有被标记为 Uptodate，这样用户空间还无法读取它。为了完成验证，fsverity_verify_blocks() 可能需要回调到文件系统通过 fsverity_operations::read_merkle_tree_page() 来读取哈希块。如果验证失败，fsverity_verify_blocks() 返回 false；在这种情况下，文件系统不应将 folio 标记为 Uptodate。按照通常的 Linux 页面缓存行为，用户空间尝试从包含该 folio 的文件部分读取时将失败并返回 EIO，而对该 folio 在内存映射中的访问将引发 SIGBUS。

原则上，验证一个数据块需要验证从该数据块到根哈希的整个 Merkle 树路径。然而，为了提高效率，文件系统可能会缓存哈希块。因此，fsverity_verify_blocks() 只会上溯树来读取哈希块，直到遇到已经被验证过的哈希块。然后它会验证到那个块的路径。

这种优化方法也被 dm-verity 使用，从而实现了出色的顺序读取性能。这是因为通常情况下（例如
在128次中127次对于4K块和SHA-256的情况下，树的最底层的哈希块已经缓存并在读取前一个数据块时进行了检查。然而，随机读取的表现更差。

基于块设备的文件系统
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linux中的基于块设备的文件系统（例如ext4和f2fs）也使用页缓存，因此上述小节同样适用。但是，它们通常一次从文件中读取许多数据块，并将其分组为称为“bio”的结构。为了使这些类型的文件系统更容易支持fs-verity，fs/verity/还提供了一个函数fsverity_verify_bio()，用于验证bio中的所有数据块。
ext4和f2fs还支持加密。如果verity文件也被加密，则必须在验证之前先解密数据。为此，这些文件系统为每个bio分配一个“后读上下文”并存储在``->bi_private``中：

    结构体 bio_post_read_ctx {
           结构体 bio *bio;
           结构体 work_struct work;
           无符号整型 cur_step;
           无符号整型 enabled_steps;
    };

``enabled_steps``是一个位掩码，指定是否启用了解密、verity或两者。在bio完成后，对于每个需要的后处理步骤，文件系统将bio_post_read_ctx排入工作队列，然后工作队列执行解密或验证。最后，标记为Uptodate的folios（没有发生解密或verity错误）被解锁。

在许多文件系统中，文件可以包含空洞。通常情况下，``->readahead()``只是将空洞块清零，并认为相应数据是最新的；不会发出bios。为了防止这种情况绕过fs-verity，文件系统使用fsverity_verify_blocks()来验证空洞块。
文件系统还会禁用verity文件的直接I/O，否则直接I/O会绕过fs-verity。

用户空间工具
=================

本文档侧重于内核，但可以在以下位置找到fs-verity的用户空间工具：
	https://git.kernel.org/pub/scm/fs/fsverity/fsverity-utils.git

请参阅fsverity-utils源代码树中的README.md文件以获取详细信息，包括设置fs-verity保护文件的示例。

测试
=====

要测试fs-verity，请使用xfstests。例如，使用`kvm-xfstests <https://github.com/tytso/xfstests-bld/blob/master/Documentation/kvm-quickstart.md>`_：
    
    kvm-xfstests -c ext4,f2fs,btrfs -g verity

常见问题解答
===

本部分回答了本文档其他部分尚未直接回答的关于fs-verity的常见问题。

问：为什么fs-verity不是IMA的一部分？
答：fs-verity和IMA（完整性度量架构）有不同的关注点。fs-verity是一种文件系统级别的机制，用于使用Merkle树对单个文件进行哈希处理。相比之下，IMA规定了一种系统级策略，该策略指定了哪些文件被哈希处理以及如何处理这些哈希，例如记录它们、认证它们或将它们添加到测量列表中。
IMA支持fs-verity哈希机制作为完整文件哈希的替代方案，对于那些希望获得基于Merkle树哈希的性能和安全优势的人来说。然而，强迫所有使用fs-verity的情况都通过IMA是没有意义的。作为一个独立的文件系统特性，fs-verity已经满足了许多用户的需求，并且像其他文件系统特性一样可测试，例如使用xfstests。

问：攻击者不是可以修改存储在磁盘上的Merkle树中的哈希值吗？这样fs-verity不是变得无用了吗？
答：为了验证fs-verity文件的真实性，你必须验证“fs-verity文件摘要”的真实性，其中包含了Merkle树的根哈希。详情请见`用例`_。
问：如果攻击者可以将验证文件替换为非验证文件，fs-verity 是否就变得无用了？
答：请参阅《使用场景》。在最初的使用场景中，实际上是受信任的用户空间代码来验证文件；fs-verity 只是一个工具，用于高效且安全地完成这项工作。受信任的用户空间代码会认为非验证文件是未经过认证的。

问：为什么梅克尔树需要存储在磁盘上？难道不能只存储根哈希吗？
答：如果不把梅克尔树存储在磁盘上，那么在首次访问文件时，即使只读取一个字节，也需要计算整个树。这是梅克尔树哈希算法的基本后果。为了验证一个叶节点，你需要验证到根哈希的整个路径，包括根节点（即根哈希所基于的对象）。但如果根节点没有存储在磁盘上，你就必须通过哈希它的子节点来计算它，并以此类推直到实际哈希完整个文件。这样做基本上违背了使用梅克尔树哈希的目的，因为如果你无论如何都需要提前哈希完整个文件，那么可以直接做 sha256(file)。这样既更简单，速度也更快一些。
确实，在内存中的梅克尔树仍然可以在每次读取时提供验证的优势而不仅仅是在第一次读取时。然而，这将是低效的，因为每当一个哈希页面被驱逐时（你无法将整个梅克尔树固定在内存中，因为它可能非常大），为了恢复它，你需要重新哈希树下所有的数据。这再次违背了使用梅克尔树哈希的目的，因为一次块读取可能会触发重新哈希几GB的数据。

问：但你不能只存储叶节点并计算其余部分吗？
答：请参阅之前的答案；这实际上只是向上移动了一层，因为可以将数据块解释为梅克尔树的叶节点。如果存储叶节点而不是数据本身，树确实可以更快地计算出来，但这仅仅是因为每一层比下一层小不到1%（假设推荐设置的 SHA-256 和 4K 块）。由于同样的原因，存储“仅叶节点”实际上已经存储了超过99%的树，因此不妨直接存储整棵树。

问：梅克尔树是否可以提前构建，例如作为安装到多台计算机上的软件包的一部分？
答：目前不支持这一功能。它原本是设计的一部分，但由于简化内核UAPI以及不是关键使用场景而被移除。文件通常只安装一次，但会被多次使用，并且现代处理器上的加密哈希速度相当快。

问：为什么 fs-verity 不支持写入？
答：写入支持将会非常困难并且需要完全不同的设计，因此超出了 fs-verity 的范围。写入支持需要：
- 一种维持数据和哈希之间一致性的方法，包括所有级别的哈希，因为在崩溃后（尤其是可能影响整个文件！）发生损坏是不可接受的。
解决这个问题的主要选项包括数据日志、写时复制和日志结构化卷。但很难在现有的文件系统中引入新的一致性机制。
虽然 ext4 支持数据日志，但速度非常慢。
- 每次写入后重建梅克尔树，这将极其低效。或者，可以使用另一种认证数据结构，如“认证跳表”。然而，这将更加复杂。
与dm-verity相比，dm-integrity更为复杂。dm-verity非常简单：内核只是将只读数据与只读的Merkle树进行验证。相反，dm-integrity支持写入操作，但速度较慢，复杂度更高，并且不支持全设备认证，因为它独立地认证每个扇区，即没有“根哈希”。对于同一个device-mapper目标同时支持这两种截然不同的情况并不合理；这同样适用于fs-verity。

**问：既然verity文件是不可变的，为什么没有设置不可变位？**
答：现有的“不可变”位（FS_IMMUTABLE_FL）具有一组特定的语义，不仅使文件内容只读，还阻止文件被删除、重命名、链接或更改所有者和模式。这些额外属性对fs-verity来说是不需要的，因此重新使用不可变位并不合适。

**问：为什么API使用ioctl而不是setxattr()和getxattr()？**
答：大多数Linux文件系统开发人员强烈反对滥用xattr接口来进行基本上的任意系统调用。xattr应该只是一个磁盘上的扩展属性，而不是用于触发构建Merkle树的API。

**问：fs-verity是否支持远程文件系统？**
答：到目前为止，实现fs-verity支持的所有文件系统都是本地文件系统，但在原则上，任何能够存储per-file verity元数据的文件系统都可以支持fs-verity，无论它是本地还是远程。一些文件系统可能有较少的选择来存储verity元数据；一种可能是将其存储在文件末尾并通过操纵i_size来隐藏用户空间。由`fs/verity/`提供的数据验证函数也假设文件系统使用了Linux的pagecache，但本地和远程文件系统通常都这样做。

**问：为什么会有任何特定于文件系统的东西？fs-verity不应该完全在VFS级别实现吗？**
答：有很多原因使得这是不可能的或非常困难的，包括以下几点：

- 为了防止绕过验证，folios在被验证之前不能标记为Uptodate。目前，每个文件系统负责通过`->readahead()`标记folios为Uptodate。因此，目前VFS无法独自完成验证。改变这一点需要对VFS和所有文件系统进行重大修改。
- 需要定义一种文件系统无关的方式来存储verity元数据。扩展属性不适合这种情况，因为（a）Merkle树可能达到GB级，但许多文件系统假设所有xattr都能放入一个4K的文件系统块中；（b）ext4和f2fs加密不加密xattr，而当文件内容被加密时，Merkle树必须被加密，因为它存储的是明文文件内容的哈希值。
所以verity元数据必须存储在一个实际的文件中。使用单独的文件会非常丑陋，因为元数据本质上是受保护文件的一部分，可能导致用户可以删除真实文件但无法删除元数据文件，或者反过来。另一方面，将其放在同一文件中会破坏应用程序，除非文件系统的i_size概念与VFS分离，这会很复杂并需要对所有文件系统进行修改。
- 希望FS_IOC_ENABLE_VERITY使用文件系统的事务机制，以便文件要么启用verity，要么没有任何变化。允许在崩溃后出现中间状态可能会导致问题。
