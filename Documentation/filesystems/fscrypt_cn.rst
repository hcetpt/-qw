文件系统级加密（fscrypt）
=====================================

简介
============

fscrypt 是一个库，文件系统可以调用它来支持文件和目录的透明加密。
注意：本文档中的“fscrypt”指的是内核级别的部分，实现在``fs/crypto/``中，而不是用户空间工具`fscrypt <https://github.com/google/fscrypt>`_。本文档仅涵盖内核级别的部分。关于如何使用加密的命令行示例，请参阅用户空间工具`fscrypt <https://github.com/google/fscrypt>`_ 的文档。此外，建议使用fscrypt用户空间工具或其他现有的用户空间工具如`fscryptctl <https://github.com/google/fscryptctl>`_ 或者`Android的密钥管理系统 <https://source.android.com/security/encryption/file-based>`_，而不是直接使用内核API。使用现有工具可以减少引入自身安全漏洞的机会。（尽管如此，为了完整性，此文档还是涵盖了内核的API。）

与dm-crypt不同，fscrypt在文件系统级别而非块设备级别运行。这使得它可以使用不同的密钥加密不同的文件，并在同一文件系统上拥有未加密的文件。这对于多用户系统非常有用，在这些系统中，每个用户的数据需要与其他用户的进行加密隔离。然而，除了文件名外，fscrypt不加密文件系统的元数据。
与eCryptfs（一种堆叠文件系统）不同，fscrypt直接集成到支持的文件系统中——目前包括ext4、F2FS、UBIFS和CephFS。这允许加密文件在读写时无需在页缓存中同时缓存解密和加密页面，从而几乎将内存使用量减半，并使其与未加密文件一致。类似地，所需的dentry和inode数量也减半。eCryptfs还将加密文件名限制为143字节，导致应用程序兼容性问题；而fscrypt允许完整的255字节（NAME_MAX）。最后，与eCryptfs不同，fscrypt API可以被非特权用户使用，无需挂载任何内容。
fscrypt不支持原地加密文件。相反，它支持标记一个空目录为加密目录。然后，在用户空间提供了密钥之后，该目录树中创建的所有普通文件、目录和符号链接都会被透明加密。

威胁模型
============

离线攻击
-------------

如果用户空间选择了强大的加密密钥，则fscrypt可以在单点永久离线破坏块设备内容的情况下保护文件内容和文件名的机密性。但是，fscrypt不保护非文件名元数据的机密性，例如文件大小、文件权限、文件时间戳和扩展属性。此外，文件中洞（未分配的块，逻辑上包含全部零）的存在和位置也不受保护。
如果攻击者能够在授权用户访问文件系统之前离线操作文件系统，fscrypt无法保证保护机密性或真实性。

在线攻击
--------------

fscrypt（以及存储加密总体上）对在线攻击只能提供有限的保护，甚至根本不能提供保护。具体如下：

侧信道攻击
~~~~~~~~~~~~~~~~~~~~

fscrypt对于侧信道攻击（如定时或电磁攻击）的抵抗力取决于底层Linux加密API算法或内联加密硬件。如果使用了易受攻击的算法，例如基于表的AES实现，攻击者可能能够对在线系统发起侧信道攻击。也可能针对消费解密数据的应用程序发起侧信道攻击。

未经授权的文件访问
~~~~~~~~~~~~~~~~~~~~~~~~

添加加密密钥后，fscrypt不会隐藏同一系统上其他用户对明文文件内容或文件名的访问。相反，应使用现有的访问控制机制，如文件模式位、POSIX ACL、LSM或命名空间来实现这一目的。
（其背后的原因是，虽然密钥已添加，但就系统本身而言，数据的机密性并不是通过加密的数学特性来保护的，而是仅依赖于内核的正确性。）
因此，任何特定于加密的访问控制检查仅由内核*代码*强制执行，因此在已经有各种访问控制机制的情况下，这些检查在很大程度上是多余的。

内核内存泄露
~~~~~~~~~~~~~~

如果攻击者能够通过物理攻击或利用内核安全漏洞读取任意内存，从而攻破系统，则可以泄露所有当前使用的加密密钥。然而，fscrypt允许从内核中移除加密密钥，这可能保护它们不被后续攻击泄露。具体来说，FS_IOC_REMOVE_ENCRYPTION_KEY ioctl（或FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS ioctl）可以从内核内存中擦除主加密密钥。如果这样做，它还会尝试驱逐所有使用该密钥“解锁”的缓存inode，从而擦除它们的每文件密钥，并使它们再次显示为“锁定”，即以密文或加密形式存在。
然而，这些ioctl有一些限制：

- 使用中的文件的每文件密钥不会被移除或擦除。因此，为了达到最佳效果，用户空间应在移除主密钥之前关闭相关的加密文件和目录，并终止工作目录位于受影响加密目录中的所有进程。
- 内核无法神奇地擦除用户空间可能拥有的主密钥副本。因此，用户空间必须擦除其创建的所有主密钥副本；通常这应该在FS_IOC_ADD_ENCRYPTION_KEY之后立即完成，而不是等待FS_IOC_REMOVE_ENCRYPTION_KEY。自然，这也适用于密钥层次结构中的所有更高层级。用户空间还应遵循其他安全预防措施，例如锁定包含密钥的内存以防止其被交换出去。
- 一般来说，内核VFS缓存中的解密内容和文件名会被释放但不会被擦除。因此，即使在相应的密钥被擦除后，它们的部分内容仍可从已释放的内存中恢复。为了解决这个问题，可以在内核配置中设置CONFIG_PAGE_POISONING=y，并在内核命令行中添加page_poison=1。然而，这会带来性能开销。
- 密钥可能仍然存在于CPU寄存器中、加密加速硬件中（如果加密API使用了任何算法的话），或者存在于未在此明确考虑的其他地方。

第一版策略的局限性
~~~~~~~~~~~~~~~~~~~~~~~~~

第一版加密策略在针对在线攻击时存在一些弱点：

- 没有验证提供的主密钥是否正确。因此，恶意用户可以暂时将错误的密钥与他们具有只读访问权限的另一个用户的加密文件关联起来。由于文件系统的缓存，即使另一个用户在其自己的密钥环中有正确的密钥，也会使用错误的密钥来访问这些文件。这违反了“只读访问”的含义。
### 密钥层次结构

#### 主密钥

每个加密目录树都由一个*主密钥*保护。主密钥可以长达64字节，并且必须至少与所使用的文件内容和文件名加密模式的安全强度一样长。例如，如果使用任何AES-256模式，则主密钥必须至少为256位，即32字节。如果密钥用于v1加密策略并且使用AES-256-XTS，则有更严格的要求；这种密钥必须为64字节。

为了“解锁”加密目录树，用户空间必须提供相应的主密钥。可以有任意数量的主密钥，每个主密钥可以保护任意数量的文件系统上的目录树。

主密钥必须是真正的密码学密钥，即不可与相同长度的随机字节区分开来。这意味着用户**不得**直接将密码用作主密钥、零填充较短的密钥或重复较短的密钥。如果用户空间有任何这样的错误，安全性无法保证，因为密码学证明和分析将不再适用。

相反，用户应通过密码学安全的随机数生成器或使用KDF（密钥派生函数）来生成主密钥。内核不进行任何密钥拉伸；因此，如果用户空间从低熵的秘密（如口令）派生密钥，则必须使用为此目的设计的KDF，例如scrypt、PBKDF2或Argon2。

#### 密钥派生函数

除了一个例外情况外，fscrypt从不直接使用主密钥进行加密。相反，它们仅作为输入到KDF（密钥派生函数）以派生实际的密钥。

对于特定的主密钥，所使用的KDF取决于该密钥是用于v1加密策略还是v2加密策略。用户**不得**在同一主密钥下同时使用v1和v2加密策略。（目前尚无针对这种情况的具体攻击，但由于密码学证明和分析不再适用，其安全性无法保证。）

对于v1加密策略，KDF仅支持派生每文件加密密钥。它通过使用文件的16字节nonce作为AES密钥，使用AES-128-ECB对主密钥进行加密。产生的密文用作派生密钥。如果密文比所需的长度长，则将其截断至所需长度。

对于v2加密策略，KDF是HKDF-SHA512。主密钥作为“输入密钥材料”传递，不使用盐，并且为每个要派生的不同密钥使用一个不同的“应用程序特定信息字符串”。例如，在派生每文件加密密钥时，应用程序特定信息字符串是文件的nonce前缀为“fscrypt\0”和一个上下文字节。其他类型的派生密钥使用不同的上下文字节。
HKDF-SHA512 被优先于原始的基于 AES-128-ECB 的 KDF，因为 HKDF 更加灵活、不可逆，并且能够均匀地从主密钥中分配熵。HKDF 是标准化的并且被其他许多软件广泛使用，而基于 AES-128-ECB 的 KDF 则是临时性的。

### 每文件加密密钥

由于每个主密钥可以保护多个文件，因此有必要对每个文件的加密进行“调整”，以确保两个文件中的相同明文不会映射到相同的密文，反之亦然。在大多数情况下，fscrypt 通过生成每文件密钥来实现这一点。当创建一个新的加密节点（普通文件、目录或符号链接）时，fscrypt 随机生成一个 16 字节的 nonce 并将其存储在节点的加密扩展属性中。然后，它使用一个 KDF（如 `密钥派生函数`_ 中所述）从主密钥和 nonce 衍生出文件的密钥。

选择密钥派生而不是密钥包装是因为包装后的密钥会需要更大的扩展属性，这使得它们不太可能内联存储在文件系统的节点表中，而且似乎没有显著的优点。特别是，目前没有要求支持用多个备选主密钥解锁文件或支持主密钥轮换。相反，主密钥可以在用户空间中进行包装，例如 `fscrypt <https://github.com/google/fscrypt>`_ 工具所做的一样。

### DIRECT_KEY 策略

Adiantum 加密模式（见 `加密模式和用途`_）适用于内容和文件名加密，并且接受长 IV ——足够长以包含一个 8 字节的数据单元索引和一个 16 字节的每文件 nonce。此外，每个 Adiantum 密钥的开销大于 AES-256-XTS 密钥。

因此，为了提高性能并节省内存，对于 Adiantum 支持“直接密钥”配置。当用户通过在 fscrypt 策略中设置 FSCRYPT_POLICY_FLAG_DIRECT_KEY 启用此功能时，不使用每文件加密密钥。相反，在加密任何数据（内容或文件名）时，将文件的 16 字节 nonce 包含在 IV 中。此外：

- 对于 v1 加密策略，加密直接使用主密钥完成。因此，用户**必须不**将同一个主密钥用于任何其他用途，即使对于其他 v1 策略也是如此。
- 对于 v2 加密策略，加密使用通过 KDF 派生的每模式密钥完成。用户可以将同一个主密钥用于其他 v2 加密策略。

### IV_INO_LBLK_64 策略

当在 fscrypt 策略中设置了 FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64 时，加密密钥是从主密钥、加密模式编号和文件系统 UUID 衍生出来的。这通常会导致受同一主密钥保护的所有文件共享一个内容加密密钥和一个文件名加密密钥。为了仍然以不同的方式加密不同文件的数据，节点号被包含在 IV 中。

因此，缩小文件系统可能不允许。

此格式针对符合 UFS 标准的内联加密硬件进行了优化，该标准仅支持每 I/O 请求 64 位 IV，并且可能只有少量的密钥槽。

### IV_INO_LBLK_32 策略

IV_INO_LBLK_32 策略与 IV_INO_LBLK_64 类似，不同之处在于对于 IV_INO_LBLK_32，节点号通过 SipHash-2-4（其中 SipHash 密钥从主密钥派生）进行哈希处理，并加上文件数据单元索引 mod 2^32 来生成 32 位 IV。
此格式针对符合 eMMC v5.2 标准的内联加密硬件进行了优化，该标准仅支持每个 I/O 请求 32 位初始化向量 (IV)，并且可能只有少量密钥槽。此格式会导致一定程度的 IV 重用，因此仅在因硬件限制必要时才应使用。

密钥标识符
-----------

对于用于 v2 加密策略的主密钥，还会使用密钥派生函数 (KDF) 派生一个唯一的 16 字节“密钥标识符”。此值以明文形式存储，因为需要它来可靠地识别密钥本身。

目录哈希密钥
------------

对于使用密钥化的 dirhash 对明文文件名进行索引的目录，KDF 还用于为每个目录派生一个 128 位的 SipHash-2-4 密钥，以便对文件名进行哈希处理。这与派生每个文件的加密密钥的工作方式相同，只是使用了不同的 KDF 上下文。目前，只有折叠大小写（即“不区分大小写”）的加密目录使用这种哈希风格。

加密模式及其使用
=================

fscrypt 允许为文件内容指定一种加密模式，并为文件名指定一种加密模式。不同的目录树可以使用不同的加密模式。

支持的模式
-----------

目前，以下加密模式对是支持的：

- 文件内容使用 AES-256-XTS，文件名使用 AES-256-CBC-CTS
- 文件内容使用 AES-256-XTS，文件名使用 AES-256-HCTR2
- 文件内容和文件名都使用 Adiantum
- 文件内容使用 AES-128-CBC-ESSIV，文件名使用 AES-128-CBC-CTS
- 文件内容使用 SM4-XTS，文件名使用 SM4-CBC-CTS

注意：在 API 中，“CBC”表示 CBC-ESSIV，“CTS”表示 CBC-CTS。例如，FSCRYPT_MODE_AES_256_CTS 表示 AES-256-CBC-CTS。

由于处理密文扩展的困难，目前不支持认证加密模式。因此，文件内容加密使用的是 XTS 模式或 CBC-ESSIV 模式的分组密码，或者宽块密码。文件名加密使用的是 CBC-CTS 模式或宽块密码。

(AES-256-XTS, AES-256-CBC-CTS) 是推荐的默认选项。这也是唯一一个如果内核支持 fscrypt，则始终保证支持的选项；详见《内核配置选项》。

(AES-256-XTS, AES-256-HCTR2) 也是一个很好的选择，它将文件名加密升级为使用宽块密码。（宽块密码，也称为可调参数超伪随机置换，具有这样的特性：改变一个比特会使整个结果变得混乱。）如《文件名加密》所述，宽块密码是这个问题域的理想模式，尽管 CBC-CTS 在其他选择中是“最不坏”的选择。关于 HCTR2 的更多信息，请参见《HCTR2 论文》。
Adiantum适用于因缺乏硬件加速而导致AES过慢的系统。Adiantum是一种使用XChaCha12和AES-256作为底层组件的宽块密码。在没有AES加速的情况下，大部分工作由XChaCha12完成，其速度远超AES。关于Adiantum的更多信息，请参阅[Adiantum论文](https://eprint.iacr.org/2018/720.pdf)。

(AES-128-CBC-ESSIV, AES-128-CBC-CTS)这一对仅用于支持那些唯一形式的AES加速是CPU外加密加速器（如CAAM或CESA）且不支持XTS的系统。

其余的模式对是“国家骄傲密码”：

- (SM4-XTS, SM4-CBC-CTS)

通常来说，这些密码本身并不是“不好”，但相比常见的选择如AES和ChaCha，它们受到的安全审查较少。它们也没有带来太多新内容。建议仅在使用这些密码被强制要求时才使用。

内核配置选项
------------

启用fscrypt支持（CONFIG_FS_ENCRYPTION）会自动引入使用AES-256-XTS和AES-256-CBC-CTS加密所需的基本crypto API支持。为了获得最佳性能，强烈建议同时启用任何可用的平台特定的kconfig选项以加速您希望使用的算法。任何“非默认”的加密模式通常也需要额外的kconfig选项。
以下是按加密模式列出的一些相关选项。请注意，未列出的加速选项可能适用于您的平台；请参考kconfig菜单。文件内容加密也可以配置为使用内联加密硬件而不是内核crypto API（参见“内联加密支持”）；在这种情况下，文件内容模式不需要在内核crypto API中支持，但文件名模式仍然需要支持。

- AES-256-XTS 和 AES-256-CBC-CTS
    - 推荐：
        - arm64: CONFIG_CRYPTO_AES_ARM64_CE_BLK
        - x86: CONFIG_CRYPTO_AES_NI_INTEL

- AES-256-HCTR2
    - 必须：
        - CONFIG_CRYPTO_HCTR2
    - 推荐：
        - arm64: CONFIG_CRYPTO_AES_ARM64_CE_BLK
        - arm64: CONFIG_CRYPTO_POLYVAL_ARM64_CE
        - x86: CONFIG_CRYPTO_AES_NI_INTEL
        - x86: CONFIG_CRYPTO_POLYVAL_CLMUL_NI

- Adiantum
    - 必须：
        - CONFIG_CRYPTO_ADIANTUM
    - 推荐：
        - arm32: CONFIG_CRYPTO_CHACHA20_NEON
        - arm32: CONFIG_CRYPTO_NHPOLY1305_NEON
        - arm64: CONFIG_CRYPTO_CHACHA20_NEON
        - arm64: CONFIG_CRYPTO_NHPOLY1305_NEON
        - x86: CONFIG_CRYPTO_CHACHA20_X86_64
        - x86: CONFIG_CRYPTO_NHPOLY1305_SSE2
        - x86: CONFIG_CRYPTO_NHPOLY1305_AVX2

- AES-128-CBC-ESSIV 和 AES-128-CBC-CTS
    - 必须：
        - CONFIG_CRYPTO_ESSIV
        - CONFIG_CRYPTO_SHA256 或其他SHA-256实现
    - 推荐：
        - AES-CBC 加速

fscrypt还使用HMAC-SHA512进行密钥派生，因此启用SHA-512加速也是推荐的：

- SHA-512
    - 推荐：
        - arm64: CONFIG_CRYPTO_SHA512_ARM64_CE
        - x86: CONFIG_CRYPTO_SHA512_SSSE3

内容加密
--------

对于内容加密，每个文件的内容被划分为“数据单元”。每个数据单元独立加密。每个数据单元的IV包含了该数据单元在文件中的零基索引。这确保了文件内的每个数据单元被不同地加密，这是防止信息泄露所必需的。
注意：根据文件偏移量进行加密意味着像“合并范围”和“插入范围”这样的重新排列文件范围映射的操作在加密文件上不支持。
数据单元的大小有两种情况：

* 固定大小的数据单元。这是除UBIFS之外的所有文件系统的处理方式。文件的数据单元都是相同大小；如果需要，最后一个数据单元会被零填充。默认情况下，数据单元大小等于文件系统块大小。在某些文件系统中，用户可以通过加密策略中的``log2_data_unit_size``字段选择子块数据单元大小；参见`FS_IOC_SET_ENCRYPTION_POLICY`。
* 可变大小的数据单元。这是UBIFS的做法。每个“UBIFS数据节点”被视为一个加密数据单元。每个节点包含可变长度、可能被压缩的数据，并被零填充到下一个16字节边界。用户在UBIFS上不能选择子块数据单元大小。
在压缩加加密的情况下，压缩后的数据被加密。UBIFS压缩如上所述。f2fs压缩略有不同；它将多个文件系统块压缩为更少数量的文件系统块。
因此，f2fs 压缩文件仍然使用固定大小的数据单元，并且它的加密方式类似于包含空洞的文件。如在“密钥层次结构”中所述，默认的加密设置使用每个文件的密钥。在这种情况下，每个数据单元的初始化向量（IV）仅仅是该数据单元在文件中的索引。然而，用户可以选择不使用每个文件密钥的加密设置。对于这些情况，需要将某种文件标识符纳入 IV 中，如下所示：

- 使用 `DIRECT_KEY 策略`_ 时，数据单元索引位于 IV 的第 0-63 位，文件的随机数（nonce）位于第 64-191 位。
- 使用 `IV_INO_LBLK_64 策略`_ 时，数据单元索引位于 IV 的第 0-31 位，文件的inode号位于第 32-63 位。此设置仅在数据单元索引和inode号都能放入 32 位的情况下允许使用。
- 使用 `IV_INO_LBLK_32 策略`_ 时，文件的inode号经过哈希处理后与数据单元索引相加。结果值截断为 32 位并放置在 IV 的第 0-31 位。此设置也仅在数据单元索引和inode号都能放入 32 位的情况下允许使用。

IV 的字节顺序始终为小端模式。
如果用户选择 FSCRYPT_MODE_AES_128_CBC 作为内容模式，则会自动包含 ESSIV 层。在这种情况下，在将 IV 传递给 AES-128-CBC 之前，它会被 AES-256 加密，其中 AES-256 密钥是文件内容加密密钥的 SHA-256 哈希值。

### 文件名加密

对于文件名，每个完整的文件名都一次性进行加密。由于需要保留对高效目录查找的支持以及最大 255 字节的文件名长度，因此目录中的每个文件名都使用相同的 IV。
然而，每个加密目录仍然使用唯一的密钥，或者将文件的随机数（对于 `DIRECT_KEY 策略`_）或inode号（对于 `IV_INO_LBLK_64 策略`_）包含在 IV 中。因此，IV 的重复使用仅限于单个目录内。

使用 CBC-CTS 时，IV 的重复使用意味着当明文文件名共享一个至少与密码块大小（AES 为 16 字节）一样长的公共前缀时，相应的加密文件名也会共享一个公共前缀。这是不希望的情况。Adiantum 和 HCTR2 没有这种弱点，因为它们是宽块加密模式。
所有受支持的文件名加密模式都接受任何长度≥16字节的明文；不需要密码块对齐。然而，对于短于16字节的文件名，在加密之前会用NUL填充到16字节。此外，为了通过其密文减少文件名长度的信息泄漏，所有文件名都会被NUL填充到下一个4、8、16或32字节边界（可配置）。推荐使用32字节，因为这提供了最佳的保密性，但代价是使目录项占用的空间稍多一些。需要注意的是，由于NUL（``\0``）在文件名中不是有效的字符，因此填充不会产生重复的明文。
符号链接目标被视为一种文件名，并以与目录条目中的文件名相同的方式进行加密，不同之处在于每个符号链接都有自己的inode，因此IV重用不是问题。

用户API
=======

设置加密策略
-------------------

FS_IOC_SET_ENCRYPTION_POLICY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FS_IOC_SET_ENCRYPTION_POLICY ioctl用于在一个空目录上设置加密策略，或者验证一个目录或常规文件是否已经具有指定的加密策略。它需要一个指向struct fscrypt_policy_v1或struct fscrypt_policy_v2的指针，这些结构体定义如下：

    #define FSCRYPT_POLICY_V1               0
    #define FSCRYPT_KEY_DESCRIPTOR_SIZE     8
    struct fscrypt_policy_v1 {
            __u8 version;
            __u8 contents_encryption_mode;
            __u8 filenames_encryption_mode;
            __u8 flags;
            __u8 master_key_descriptor[FSCRYPT_KEY_DESCRIPTOR_SIZE];
    };
    #define fscrypt_policy  fscrypt_policy_v1

    #define FSCRYPT_POLICY_V2               2
    #define FSCRYPT_KEY_IDENTIFIER_SIZE     16
    struct fscrypt_policy_v2 {
            __u8 version;
            __u8 contents_encryption_mode;
            __u8 filenames_encryption_mode;
            __u8 flags;
            __u8 log2_data_unit_size;
            __u8 __reserved[3];
            __u8 master_key_identifier[FSCRYPT_KEY_IDENTIFIER_SIZE];
    };

此结构必须按以下方式初始化：

- ``version`` 必须为FSCRYPT_POLICY_V1（0），如果使用了struct fscrypt_policy_v1，或者为FSCRYPT_POLICY_V2（2），如果使用了struct fscrypt_policy_v2。（注意：我们将最初的策略版本称为“v1”，尽管其版本代码实际上是0。）对于新的加密目录，请使用v2策略。
- ``contents_encryption_mode`` 和 ``filenames_encryption_mode`` 必须设置为来自``<linux/fscrypt.h>``中的常量，以标识要使用的加密模式。如果不确定，请将 ``contents_encryption_mode`` 设置为FSCRYPT_MODE_AES_256_XTS（1），将 ``filenames_encryption_mode`` 设置为FSCRYPT_MODE_AES_256_CTS（4）。详细信息请参见《加密模式和用途》_。
v1加密策略仅支持三种模式组合：(FSCRYPT_MODE_AES_256_XTS, FSCRYPT_MODE_AES_256_CTS)，(FSCRYPT_MODE_AES_128_CBC, FSCRYPT_MODE_AES_128_CTS)，以及(FSCRYPT_MODE_ADIANTUM, FSCRYPT_MODE_ADIANTUM)。v2策略支持《支持的模式》_中列出的所有组合。
- ``flags`` 包含来自``<linux/fscrypt.h>``的可选标志：

  - FSCRYPT_POLICY_FLAGS_PAD_*：加密文件名时要使用的NUL填充量。如果不确定，请使用FSCRYPT_POLICY_FLAGS_PAD_32（0x3）
- FSCRYPT_POLICY_FLAG_DIRECT_KEY：详见《DIRECT_KEY策略》_
- FSCRYPT_POLICY_FLAG_IV_INO_LBLK_64：详见《IV_INO_LBLK_64策略》_
- FSCRYPT_POLICY_FLAG_IV_INO_LBLK_32：详见《IV_INO_LBLK_32策略》_
v1加密策略仅支持PAD_*和DIRECT_KEY标志。
其他标志仅受v2加密策略支持。
DIRECT_KEY、IV_INO_LBLK_64 和 IV_INO_LBLK_32 标志是互斥的。
- `log2_data_unit_size` 是数据单元大小（以字节为单位）的对数（以2为底），或者设置为0以选择默认的数据单元大小。数据单元大小是文件内容加密的粒度。例如，将 `log2_data_unit_size` 设置为12会导致文件内容以4096字节的数据单元传递给底层加密算法（如AES-256-XTS），每个数据单元都有自己的初始化向量（IV）。
并非所有文件系统都支持设置 `log2_data_unit_size`。ext4和f2fs从Linux v6.7开始支持它。在支持该功能的文件系统上，支持的非零值范围是从9到文件系统的块大小的对数值（以2为底），包括两端。默认值0选择文件系统的块大小。
`log2_data_unit_size` 的主要用例是为了选择一个比文件系统块大小更小的数据单元大小，以便与只支持较小数据单元大小的内联加密硬件兼容。`/sys/block/$disk/queue/crypto/` 可用于检查特定系统的内联加密硬件支持哪些数据单元大小。
除非你确定需要它，否则不要设置此字段为非零值。使用不必要的小数据单元大小会降低性能。
- 对于v2加密策略，`__reserved` 必须被清零。
- 对于v1加密策略，`master_key_descriptor` 指定如何在密钥环中查找主密钥；详见 `Adding keys`_。用户空间必须为每个主密钥选择一个唯一的 `master_key_descriptor`。e4crypt和fscrypt工具使用 `SHA-512(SHA-512(master_key))` 的前8个字节，但这不是必需的方案。此外，在执行 FS_IOC_SET_ENCRYPTION_POLICY 时，主密钥不必已经在密钥环中。然而，在任何文件可以在加密目录中创建之前，必须先添加主密钥。
对于v2加密策略，`master_key_descriptor` 已被 `master_key_identifier` 替换，后者更长且不能任意选择。相反，必须首先使用 `FS_IOC_ADD_ENCRYPTION_KEY`_ 添加密钥。然后，必须使用内核在结构 fscrypt_add_key_arg 中返回的 `key_spec.u.identifier` 作为结构 fscrypt_policy_v2 中的 `master_key_identifier`。
如果文件尚未加密，则 FS_IOC_SET_ENCRYPTION_POLICY 会验证文件是否为空目录。如果是，则指定的加密策略将分配给该目录，将其转换为加密目录。之后，以及按照 `Adding keys`_ 中描述的方法提供了相应的主密钥后，在该目录中创建的所有普通文件、目录（递归地）和符号链接都将被加密，并继承相同的加密策略。
目录条目中的文件名也将被加密。

或者，如果文件已经被加密，则
`FS_IOC_SET_ENCRYPTION_POLICY` 验证指定的加密策略是否完全匹配实际的加密策略。如果它们匹配，则 ioctl 返回 0。否则，返回 EEXIST 错误。这适用于普通文件和目录，包括非空目录。

当一个 v2 加密策略分配给一个目录时，要求指定的密钥必须由当前用户添加，或调用者在初始用户命名空间中具有 CAP_FOWNER 权限（这是为了防止用户使用其他用户的密钥加密自己的数据）。密钥必须在执行 `FS_IOC_SET_ENCRYPTION_POLICY` 期间保持添加状态。然而，如果新加密的目录不需要立即访问，则可以在之后立即将密钥移除。

请注意，ext4 文件系统不允许根目录被加密，即使它是空的。希望使用单一密钥加密整个文件系统的用户应考虑使用 dm-crypt。

`FS_IOC_SET_ENCRYPTION_POLICY` 可能会因为以下错误而失败：

- ``EACCES``：该文件不属于进程的 uid，且进程没有与文件所有者的 uid 映射到同一命名空间中的 CAP_FOWNER 能力
- ``EEXIST``：文件已使用不同于指定的加密策略进行加密
- ``EINVAL``：指定了无效的加密策略（版本、模式或标志无效；或保留位被设置）；或者指定了 v1 加密策略，但目录启用了 casefold 标志（大小写折叠与 v1 策略不兼容）
- ``ENOKEY``：指定了 v2 加密策略，但未添加具有指定 `master_key_identifier` 的密钥，且进程在初始用户命名空间中没有 CAP_FOWNER 能力
- ``ENOTDIR``：文件未加密且为普通文件，而非目录
- ``ENOTEMPTY``：文件未加密且为非空目录
- ``ENOTTY``：此类型的文件系统不支持加密
- ``EOPNOTSUPP``：内核未配置支持文件系统的加密功能，或文件系统的超级块未启用加密功能（例如，在 ext4 文件系统上使用加密功能，需要在内核配置中启用 CONFIG_FS_ENCRYPTION，并使用 `tune2fs -O encrypt` 或 `mkfs.ext4 -O encrypt` 启用超级块的 "encrypt" 特性）
- ``EPERM``：该目录不允许加密，例如，因为它是一个 ext4 文件系统的根目录
- ``EROFS``：文件系统为只读

获取加密策略
--------------

有两个 ioctl 可用于获取文件的加密策略：

- `FS_IOC_GET_ENCRYPTION_POLICY_EX`
- `FS_IOC_GET_ENCRYPTION_POLICY`

扩展版（_EX）ioctl 更通用，并建议尽可能使用。然而，在较旧的内核中，只有原始 ioctl 可用。应用程序应尝试使用扩展版，如果它返回 ENOTTY 错误，则回退到原始版本。

`FS_IOC_GET_ENCRYPTION_POLICY_EX`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`FS_IOC_GET_ENCRYPTION_POLICY_EX` ioctl 获取目录或普通文件的加密策略（如果有）。除了打开文件的能力外，不需要额外的权限。它接受指向 `struct fscrypt_get_policy_ex_arg` 的指针，定义如下：

```c
    struct fscrypt_get_policy_ex_arg {
            __u64 policy_size; /* 输入/输出 */
            union {
                    __u8 version;
                    struct fscrypt_policy_v1 v1;
                    struct fscrypt_policy_v2 v2;
            } policy; /* 输出 */
    };
```

调用者必须初始化 `policy_size` 为策略结构体可用的空间大小，即 `sizeof(arg.policy)`。

成功时，策略结构体将通过 `policy` 返回，并且其实际大小将通过 `policy_size` 返回。应检查 `policy.version` 以确定返回的策略版本。注意，“v1”策略的实际版本号实际上是 0（FSCRYPT_POLICY_V1）。

`FS_IOC_GET_ENCRYPTION_POLICY_EX` 可能会因为以下错误而失败：

- ``EINVAL``：文件已加密，但使用了无法识别的加密策略版本
- ``ENODATA``：文件未加密
- ``ENOTTY``：此类型的文件系统不支持加密，或内核版本过旧而不支持 `FS_IOC_GET_ENCRYPTION_POLICY_EX`（请尝试 `FS_IOC_GET_ENCRYPTION_POLICY`）
- ``EOPNOTSUPP``：内核未配置支持此文件系统的加密功能，或文件系统的超级块未启用加密功能
- ``EOVERFLOW``：文件已加密并使用了可识别的加密策略版本，但策略结构体无法放入提供的缓冲区

注意：如果您只需要知道文件是否已加密，对于大多数文件系统，也可以使用 `FS_IOC_GETFLAGS` ioctl 并检查 FS_ENCRYPT_FL 标志，或使用 statx() 系统调用并检查 stx_attributes 中的 STATX_ATTR_ENCRYPTED 标志。
### FS_IOC_GET_ENCRYPTION_POLICY

`FS_IOC_GET_ENCRYPTION_POLICY` ioctl 可以检索目录或普通文件的加密策略（如果有的话）。但是，与 `FS_IOC_GET_ENCRYPTION_POLICY_EX` 不同，`FS_IOC_GET_ENCRYPTION_POLICY` 只支持原始策略版本。它直接接收指向 `struct fscrypt_policy_v1` 的指针，而不是 `struct fscrypt_get_policy_ex_arg`。

`FS_IOC_GET_ENCRYPTION_POLICY` 的错误代码与 `FS_IOC_GET_ENCRYPTION_POLICY_EX` 相同，但当文件使用较新的加密策略版本加密时，还会返回 `EINVAL`。

#### 获取每个文件系统的盐值

一些文件系统（如 ext4 和 F2FS）还支持已废弃的 ioctl `FS_IOC_GET_ENCRYPTION_PWSALT`。这个 ioctl 检索存储在文件系统超级块中的一个随机生成的 16 字节值。这个值旨在用作从口令或其他低熵用户凭证派生加密密钥时的盐。

`FS_IOC_GET_ENCRYPTION_PWSALT` 已废弃。取而代之的是，在用户空间中生成和管理所需的任何盐值。

#### 获取文件的加密 nonce 值

自 Linux 5.7 版本起，支持 ioctl `FS_IOC_GET_ENCRYPTION_NONCE`。对于加密文件和目录，它获取 inode 的 16 字节 nonce 值；对于未加密的文件和目录，它会因缺少数据而失败（返回 `ENODATA`）。

这个 ioctl 对于验证加密是否正确执行的自动化测试很有用。但对于 fscrypt 的正常使用来说并不需要。

### 添加密钥

#### FS_IOC_ADD_ENCRYPTION_KEY

`FS_IOC_ADD_ENCRYPTION_KEY` ioctl 将主加密密钥添加到文件系统中，使文件系统上所有使用该密钥加密的文件看起来“解锁”，即以明文形式显示。

可以在目标文件系统上的任何文件或目录上执行此操作，但建议使用文件系统的根目录。它接收指向 `struct fscrypt_add_key_arg` 的指针，定义如下：

```c
    struct fscrypt_add_key_arg {
            struct fscrypt_key_specifier key_spec;
            __u32 raw_size;
            __u32 key_id;
            __u32 __reserved[8];
            __u8 raw[];
    };

    #define FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR        1
    #define FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER        2

    struct fscrypt_key_specifier {
            __u32 type;     /* one of FSCRYPT_KEY_SPEC_TYPE_* */
            __u32 __reserved;
            union {
                    __u8 __reserved[32]; /* reserve some extra space */
                    __u8 descriptor[FSCRYPT_KEY_DESCRIPTOR_SIZE];
                    __u8 identifier[FSCRYPT_KEY_IDENTIFIER_SIZE];
            } u;
    };

    struct fscrypt_provisioning_key_payload {
            __u32 type;
            __u32 __reserved;
            __u8 raw[];
    };
```

`struct fscrypt_add_key_arg` 必须先清零，然后按照以下方式初始化：

- 如果密钥是用于 v1 加密策略，则 `key_spec.type` 必须包含 `FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR`，并且 `key_spec.u.descriptor` 必须包含要添加的密钥的描述符，对应于 `struct fscrypt_policy_v1` 中的 `master_key_descriptor` 字段的值。
要添加这种类型的密钥，调用进程必须在初始用户命名空间中具有 `CAP_SYS_ADMIN` 权限。
或者，如果该密钥是为了使用 v2 加密策略而添加的，则 `key_spec.type` 必须包含 `FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER`，并且 `key_spec.u.identifier` 是一个*输出*字段，内核会用密钥的加密散列填充该字段。在这种情况下，调用进程不需要任何特权。但是，可以添加的密钥数量受用户对密钥环服务的配额限制（参见 `Documentation/security/keys/core.rst`）。

- `raw_size` 必须是以字节为单位提供的 `raw` 密钥的大小。
或者，如果 `key_id` 非零，则此字段必须为 0，因为在那种情况下，大小由指定的 Linux 密钥环密钥隐含决定。

- 如果原始密钥直接提供在 `raw` 字段中，则 `key_id` 为 0。否则，`key_id` 是类型为 "fscrypt-provisioning" 的 Linux 密钥环密钥的 ID，其有效载荷为 `struct fscrypt_provisioning_key_payload`，其中 `raw` 字段包含原始密钥，且 `type` 字段与 `key_spec.type` 匹配。由于 `raw` 是可变长度的，因此此密钥的有效载荷总大小必须是 `sizeof(struct fscrypt_provisioning_key_payload)` 加上原始密钥的大小。进程必须对此密钥具有搜索权限。

大多数用户应该将此值设为 0 并直接指定原始密钥。支持指定 Linux 密钥环密钥的主要目的是允许在文件系统卸载和重新挂载后重新添加密钥，而无需将原始密钥存储在用户空间内存中。

- `raw` 是一个可变长度的字段，必须包含实际的密钥，长度为 `raw_size` 字节。或者，如果 `key_id` 非零，则此字段未使用。

对于 v2 策略密钥，内核会跟踪添加密钥的用户（通过有效用户 ID 识别），并只允许该用户删除密钥——或者如果他们使用 `FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS`，则允许“root”用户删除密钥。
然而，如果另一个用户已添加了密钥，则可能希望防止该用户意外地移除它。因此，`FS_IOC_ADD_ENCRYPTION_KEY` 也可以用于再次添加一个版本2的策略密钥，即使它已经被其他用户添加过。在这种情况下，`FS_IOC_ADD_ENCRYPTION_KEY` 只会为当前用户安装对该密钥的声明，而不是实际再次添加密钥（但仍然需要提供原始密钥，作为知识证明）。

`FS_IOC_ADD_ENCRYPTION_KEY` 在以下情况返回 0：密钥或对该密钥的声明已被添加或已经存在。

`FS_IOC_ADD_ENCRYPTION_KEY` 可能会因为以下错误而失败：

- ``EACCES``：指定了 `FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR`，但在初始用户命名空间中调用者没有 `CAP_SYS_ADMIN` 能力；或者原始密钥通过 Linux 密钥ID指定，但进程没有对该密钥的搜索权限。
- ``EDQUOT``：添加该密钥将超过此用户的密钥配额。
- ``EINVAL``：无效的密钥大小或密钥指定类型，或者设置了保留位。
- ``EKEYREJECTED``：原始密钥通过 Linux 密钥ID指定，但密钥类型不正确。
- ``ENOKEY``：原始密钥通过 Linux 密钥ID指定，但不存在具有该ID的密钥。
- ``ENOTTY``：这种类型的文件系统未实现加密。
- ``EOPNOTSUPP``：内核未配置支持此文件系统的加密，或者文件系统的超级块尚未启用加密。

遗留方法
~~~~~~~~~~~~~

对于版本1的加密策略，可以通过将其添加到进程订阅的密钥环中来提供主加密密钥，例如添加到会话密钥环或用户密钥环（如果用户密钥环链接到了会话密钥环）。这种方法因多个原因被废弃（并且不支持版本2的加密策略）。首先，它不能与 `FS_IOC_REMOVE_ENCRYPTION_KEY` 结合使用（参见“移除密钥”部分），因此要移除密钥必须使用 `keyctl_unlink()` 结合 `sync; echo 2 > /proc/sys/vm/drop_caches` 这样的变通方法。其次，它不符合加密文件的锁定/解锁状态是全局的事实（即它们是否以明文形式或密文形式出现）。这种不匹配导致了很多困惑以及实际问题，特别是在不同UID下运行的进程（如 `sudo` 命令）需要访问加密文件时。

尽管如此，要将密钥添加到进程订阅的密钥环之一，可以使用 `add_key()` 系统调用（参见：`Documentation/security/keys/core.rst`）。密钥类型必须是 “logon”；这种类型的密钥保存在内核内存中，不能由用户空间读回。密钥描述必须是 “fscrypt:” 后跟 16 个字符的小写十六进制表示的 `master_key_descriptor`，该值已在加密策略中设置。密钥有效载荷必须符合以下结构：

    #define FSCRYPT_MAX_KEY_SIZE            64

    struct fscrypt_key {
            __u32 mode;
            __u8 raw[FSCRYPT_MAX_KEY_SIZE];
            __u32 size;
    };

`mode` 字段被忽略；只需将其设置为 0。实际密钥通过 `raw` 提供，并且 `size` 表示其大小（字节）。也就是说，`raw[0..size-1]` （包括这两个索引）是实际密钥。

密钥描述前缀 “fscrypt:” 也可以替换为特定于文件系统的前缀，例如 “ext4:”。但是，特定于文件系统的前缀已被废弃，不应在新程序中使用。

移除密钥
-------------

有两种 ioctl 可用于移除由 `FS_IOC_ADD_ENCRYPTION_KEY` 添加的密钥：

- `FS_IOC_REMOVE_ENCRYPTION_KEY`
- `FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS`

这两种 ioctl 的区别仅在于非 root 用户添加或移除版本2策略密钥的情况。

这些 ioctl 不适用于通过遗留进程订阅密钥环机制添加的密钥。

在使用这些 ioctl 之前，请阅读 `内核内存泄露` 部分，了解这些 ioctl 的安全目标和限制。
### FS_IOC_REMOVE_ENCRYPTION_KEY

`FS_IOC_REMOVE_ENCRYPTION_KEY` ioctl 从文件系统中移除对主加密密钥的声明，并可能移除该密钥本身。它可以在目标文件系统的任何文件或目录上执行，但建议使用文件系统的根目录。它需要一个指向 `struct fscrypt_remove_key_arg` 的指针，定义如下：

```c
struct fscrypt_remove_key_arg {
        struct fscrypt_key_specifier key_spec;
#define FSCRYPT_KEY_REMOVAL_STATUS_FLAG_FILES_BUSY      0x00000001
#define FSCRYPT_KEY_REMOVAL_STATUS_FLAG_OTHER_USERS     0x00000002
        __u32 removal_status_flags;     /* 输出 */
        __u32 __reserved[5];
};
```

此结构必须先清零，然后按以下方式初始化：

- 要移除的密钥由 `key_spec` 指定：

    - 要移除 v1 加密策略使用的密钥，请将 `key_spec.type` 设置为 `FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR` 并填充 `key_spec.u.descriptor`。要移除此类型的密钥，调用进程必须在初始用户命名空间中具有 `CAP_SYS_ADMIN` 能力。
    - 要移除 v2 加密策略使用的密钥，请将 `key_spec.type` 设置为 `FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER` 并填充 `key_spec.u.identifier`。对于 v2 策略密钥，此 ioctl 可以由非 root 用户使用。但是，为了实现这一点，它实际上只是移除当前用户的密钥声明，撤销一次对 `FS_IOC_ADD_ENCRYPTION_KEY` 的调用。只有当所有声明都被移除后，密钥才会真正被移除。例如，如果 `FS_IOC_ADD_ENCRYPTION_KEY` 是以 uid 1000 调用的，则密钥将被 uid 1000 “声明”，而 `FS_IOC_REMOVE_ENCRYPTION_KEY` 只有在以 uid 1000 运行时才能成功。或者，如果 uid 1000 和 2000 都添加了密钥，则对于每个 uid，`FS_IOC_REMOVE_ENCRYPTION_KEY` 只会移除自己的声明。只有当两者都被移除后，密钥才会真正被移除。（可以将其视为删除一个可能有硬链接的文件。）

如果 `FS_IOC_REMOVE_ENCRYPTION_KEY` 真正移除了密钥，它还会尝试“锁定”所有使用该密钥解锁的文件。它不会锁定仍在使用的文件，因此此 ioctl 预期与用户空间合作确保没有文件仍然打开。然而，如果必要，稍后可以再次执行此 ioctl 以重新尝试锁定任何剩余的文件。

`FS_IOC_REMOVE_ENCRYPTION_KEY` 返回 0，表示密钥已被移除（但仍可能有文件需要锁定），或者用户的密钥声明已被移除，或者密钥已被移除但仍有文件需要锁定，因此 ioctl 重试锁定它们。在这些情况下，`removal_status_flags` 会被填充以下信息状态标志：

- `FSCRYPT_KEY_REMOVAL_STATUS_FLAG_FILES_BUSY`: 如果某些文件仍在使用，则设置此标志。如果仅移除了用户的密钥声明，则此标志不保证被设置。
- `FSCRYPT_KEY_REMOVAL_STATUS_FLAG_OTHER_USERS`: 如果仅移除了用户的密钥声明而非密钥本身，则设置此标志。

`FS_IOC_REMOVE_ENCRYPTION_KEY` 可能出现以下错误：

- `EACCES`: 指定了 `FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR` 密钥规范类型，但调用者在初始用户命名空间中没有 `CAP_SYS_ADMIN` 能力。
- `EINVAL`: 无效的密钥规范类型，或保留位被设置。
- `ENOKEY`: 未找到密钥对象，即从未添加或已完全移除包括所有锁定的文件；或者，用户没有密钥声明（但其他人有）。
- `ENOTTY`: 此类文件系统不支持加密。
- `EOPNOTSUPP`: 内核未配置支持此类文件系统的加密，或者文件系统的超级块尚未启用加密功能。

### FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS

`FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS` 与 `FS_IOC_REMOVE_ENCRYPTION_KEY` 完全相同，不同之处在于对于 v2 策略密钥，`ALL_USERS` 版本的 ioctl 将移除所有用户的密钥声明，而不仅仅是当前用户的。也就是说，无论有多少用户添加了密钥，密钥本身都将被移除。这种差异仅在非 root 用户添加和移除密钥时有意义。

由于这个原因，`FS_IOC_REMOVE_ENCRYPTION_KEY_ALL_USERS` 同样需要“root”，即初始用户命名空间中的 `CAP_SYS_ADMIN` 能力。否则将会返回 `EACCES` 错误。
获取密钥状态
------------------

FS_IOC_GET_ENCRYPTION_KEY_STATUS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FS_IOC_GET_ENCRYPTION_KEY_STATUS ioctl 用于检索主加密密钥的状态。它可以在目标文件系统的任何文件或目录上执行，但建议使用文件系统的根目录。它需要一个指向如下定义的 struct fscrypt_get_key_status_arg 的指针：

    struct fscrypt_get_key_status_arg {
            /* 输入 */
            struct fscrypt_key_specifier key_spec;
            __u32 __reserved[6];

            /* 输出 */
    #define FSCRYPT_KEY_STATUS_ABSENT               1
    #define FSCRYPT_KEY_STATUS_PRESENT              2
    #define FSCRYPT_KEY_STATUS_INCOMPLETELY_REMOVED 3
            __u32 status;
    #define FSCRYPT_KEY_STATUS_FLAG_ADDED_BY_SELF   0x00000001
            __u32 status_flags;
            __u32 user_count;
            __u32 __out_reserved[13];
    };

调用者必须将所有输入字段清零，然后填写 `key_spec`：

    - 要获取版本1加密策略的密钥状态，请将 `key_spec.type` 设置为 FSCRYPT_KEY_SPEC_TYPE_DESCRIPTOR 并填写 `key_spec.u.descriptor`
    - 要获取版本2加密策略的密钥状态，请将 `key_spec.type` 设置为 FSCRYPT_KEY_SPEC_TYPE_IDENTIFIER 并填写 `key_spec.u.identifier`

成功时返回0，并且内核填充输出字段：

- `status` 指示密钥是不存在、存在还是部分移除。部分移除意味着已开始移除，但某些文件仍在使用中；即，`FS_IOC_REMOVE_ENCRYPTION_KEY` 返回0但设置了信息状态标志 FSCRYPT_KEY_REMOVAL_STATUS_FLAG_FILES_BUSY
- `status_flags` 可以包含以下标志：

    - `FSCRYPT_KEY_STATUS_FLAG_ADDED_BY_SELF` 表示当前用户添加了该密钥。这仅适用于由 `identifier` 而不是 `descriptor` 标识的密钥
- `user_count` 指定添加了密钥的用户数量。这仅适用于由 `identifier` 而不是 `descriptor` 标识的密钥

FS_IOC_GET_ENCRYPTION_KEY_STATUS 可能会因为以下错误而失败：

- `EINVAL`：无效的密钥标识符类型，或保留位被设置
- `ENOTTY`：这种类型的文件系统不支持加密
- `EOPNOTSUPP`：内核未配置支持此文件系统的加密，或者文件系统的超级块尚未启用加密

除了其他用途外，FS_IOC_GET_ENCRYPTION_KEY_STATUS 还可用于确定是否需要在提示用户提供用于派生密钥的口令之前添加给定加密目录的密钥。

FS_IOC_GET_ENCRYPTION_KEY_STATUS 仅能获取文件系统级密钥环中的密钥状态，即通过 `FS_IOC_ADD_ENCRYPTION_KEY` 和 `FS_IOC_REMOVE_ENCRYPTION_KEY` 管理的密钥环。它无法获取仅通过涉及进程订阅密钥环的旧机制添加用于版本1加密策略的密钥状态。

访问语义
================

持有密钥
------------

持有加密密钥时，加密的普通文件、目录和符号链接的行为与它们未加密的对应物非常相似——毕竟，加密是为了透明化。然而，细心的用户可能会注意到一些行为差异：

- 无法将未加密文件或使用不同加密策略（即不同的密钥、模式或标志）加密的文件重命名或链接到加密目录中；请参阅 `加密策略强制执行`_。尝试这样做将因 EXDEV 失败。但是，可以在加密目录内部或移到未加密目录中重命名加密文件。
注意："移动" 未加密文件到加密目录中，例如
使用 `mv` 程序实现的文件移动操作是在用户空间通过复制后再删除来完成的。请注意，原始未加密的数据可能仍可以从磁盘上的空闲空间中恢复；因此最好从一开始就保持所有文件的加密状态。可以使用 `shred` 程序覆盖源文件，但在所有文件系统和存储设备上并不能保证有效。

- 直接 I/O 只在某些情况下支持加密文件。详情请参阅 `Direct I/O 支持`_。
- `fallocate` 操作中的 `FALLOC_FL_COLLAPSE_RANGE` 和 `FALLOC_FL_INSERT_RANGE` 不支持加密文件，并将返回 `EOPNOTSUPP` 错误。
- 加密文件的在线碎片整理不被支持。`EXT4_IOC_MOVE_EXT` 和 `F2FS_IOC_MOVE_RANGE` 的 `ioctl` 调用将会失败并返回 `EOPNOTSUPP`。
- `ext4` 文件系统不支持加密普通文件的数据日志功能。它将回退到有序数据模式。
- 直接访问（DAX）不支持加密文件。
- 加密符号链接的最大长度比未加密符号链接的最大长度短2字节。例如，在具有4K块大小的 `ext4` 文件系统中，未加密符号链接的长度可以达到4095字节，而加密符号链接的长度只能达到4093字节（这两个长度都不包括终止的空字符）。
需要注意的是，内存映射（mmap）是支持的。这是可能的，因为加密文件的页面缓存中包含的是明文而不是密文。

没有密钥的情况下
------------------

即使在加密普通文件、目录或符号链接的加密密钥尚未添加，或者加密密钥已被移除的情况下，某些文件系统操作仍可执行：

- 可以读取文件元数据，例如使用 `stat()`。
- 可以列出目录，在这种情况下，文件名将以一种基于其密文的形式编码显示。当前的编码算法在 `Filename hashing and encoding`_ 中有描述。该算法可能会改变，但可以保证显示的文件名不会超过 `NAME_MAX` 字节，不会包含 `/` 或 `\0` 字符，并且会唯一标识目录项。
`.` 和 `..` 目录条目是特殊的。它们始终存在，并且不被加密或编码。
- 文件可以被删除。也就是说，非目录文件可以用 `unlink()` 如常删除，空目录可以用 `rmdir()` 如常删除。因此，`rm` 和 `rm -r` 将如预期地工作。
- 符号链接目标可以被读取和跟随，但将以加密形式呈现，类似于目录中的文件名。因此，它们很可能不会指向任何有用的地方。
没有密钥，普通文件无法打开或截断。尝试这样做将因缺少密钥（ENOKEY）而失败。这意味着任何需要文件描述符的普通文件操作，如 `read()`、`write()`、`mmap()`、`fallocate()` 和 `ioctl()` 也是禁止的。
同样，没有密钥，任何类型的文件（包括目录）都无法在加密目录中创建或链接，加密目录中的名称也不能作为重命名的源或目标，也不能在加密目录中创建 O_TMPFILE 临时文件。所有这些操作将因缺少密钥（ENOKEY）而失败。
目前不可能在没有加密密钥的情况下备份和恢复加密文件。这需要特殊API的支持，而这些API尚未实现。

### 加密策略执行

在目录上设置了加密策略后，该目录（递归地）内创建的所有普通文件、目录和符号链接都将继承该加密策略。特殊文件——即命名管道、设备节点和UNIX域套接字——将不会被加密。
除了这些特殊文件外，在加密目录树中禁止存在未加密的文件或用不同加密策略加密的文件。尝试将此类文件链接或重命名为加密目录将因跨设备链接错误（EXDEV）而失败。这也在线索查找（`->lookup()`）时进行强制实施，以提供有限的保护，防止离线攻击试图禁用或降级已知位置的加密，这些位置可能是应用程序稍后写入敏感数据的地方。建议实现某种“验证启动”的系统利用这一点，在访问前验证所有顶层加密策略。

### 内联加密支持

默认情况下，fscrypt 使用内核加密API来处理所有加密操作（除了部分由fscrypt自身实现的HKDF）。内核加密API支持硬件加密加速器，但仅限于传统方式工作的那些，即所有输入和输出（例如明文和密文）都在内存中。fscrypt 可以利用这种硬件，但传统的加速模型效率不高，fscrypt 也未针对其进行优化。
相反，许多较新的系统（尤其是移动SoC）具有*内联加密硬件*，可以在数据传输到/从存储设备的过程中对其进行加密/解密。Linux通过一组称为*blk-crypto*的块层扩展来支持内联加密。blk-crypto允许文件系统将加密上下文附加到I/O请求（bios），以指定如何在线加密或解密数据。关于blk-crypto的更多信息，请参阅 :ref:`Documentation/block/inline-encryption.rst <inline_encryption>`。

在支持的文件系统（目前为ext4和f2fs）上，fscrypt可以使用blk-crypto而不是内核加密API来加密/解密文件内容。为此，请在内核配置中设置CONFIG_FS_ENCRYPTION_INLINE_CRYPT=y，并在挂载文件系统时指定“inlinecrypt”挂载选项。

请注意，“inlinecrypt”挂载选项只是指明在可能的情况下使用内联加密；并不会强制使用。如果内联加密硬件不支持所需的加密功能（例如，所需加密算法和支持的数据单元大小），并且无法使用blk-crypto回退，则fscrypt仍会回退到使用内核加密API。为了使blk-crypto回退可用，必须在内核配置中启用CONFIG_BLK_INLINE_ENCRYPTION_FALLBACK=y。

目前，fscrypt总是使用文件系统的块大小（通常为4096字节）作为数据单元大小。因此，它只能使用支持该数据单元大小的内联加密硬件。

内联加密不会影响密文或其他磁盘格式方面，因此用户可以自由切换是否使用“inlinecrypt”。

直接I/O支持
=============

对于加密文件的直接I/O工作，除了未加密文件的直接I/O条件外，还必须满足以下条件：

* 文件必须使用内联加密。通常这意味着文件系统必须使用``-o inlinecrypt``挂载，并且存在内联加密硬件。但是，也有软件回退选项。详情请参见`内联加密支持`_。
* I/O请求必须完全对齐到文件系统的块大小。这意味着I/O所针对的文件位置、所有I/O段的长度以及所有I/O缓冲区的内存地址都必须是这个值的倍数。请注意，文件系统的块大小可能大于块设备的逻辑块大小。

如果上述任一条件未满足，则对加密文件的直接I/O将回退到带缓冲的I/O。

实现细节
==========

加密上下文
------------

加密策略由结构fscrypt_context_v1或fscrypt_context_v2表示。具体存储位置由各个文件系统决定，但通常会将其存储在一个隐藏的扩展属性中。不应通过getxattr()和setxattr()等与xattr相关的系统调用暴露，因为加密xattr具有特殊语义。
（特别是，如果在非空目录中添加或移除加密策略，将会引起很多混淆。）这些结构体定义如下：

    #define FSCRYPT_FILE_NONCE_SIZE 16
    
    #define FSCRYPT_KEY_DESCRIPTOR_SIZE 8
    struct fscrypt_context_v1 {
            u8 version;
            u8 contents_encryption_mode;
            u8 filenames_encryption_mode;
            u8 flags;
            u8 master_key_descriptor[FSCRYPT_KEY_DESCRIPTOR_SIZE];
            u8 nonce[FSCRYPT_FILE_NONCE_SIZE];
    };
    
    #define FSCRYPT_KEY_IDENTIFIER_SIZE 16
    struct fscrypt_context_v2 {
            u8 version;
            u8 contents_encryption_mode;
            u8 filenames_encryption_mode;
            u8 flags;
            u8 log2_data_unit_size;
            u8 __reserved[3];
            u8 master_key_identifier[FSCRYPT_KEY_IDENTIFIER_SIZE];
            u8 nonce[FSCRYPT_FILE_NONCE_SIZE];
    };

上下文结构体包含的信息与相应的策略结构体相同（参见《设置加密策略》），不同之处在于上下文结构体还包含一个nonce。这个nonce由内核随机生成，并作为KDF输入或调整因子，以使不同的文件以不同的方式加密；详见《每个文件的加密密钥》和《DIRECT_KEY策略》。

数据路径变化
------------

当使用内联加密时，文件系统只需将加密上下文与bios关联起来，以指定块层或内联加密硬件如何加密/解密文件内容。当不使用内联加密时，文件系统必须自己加密/解密文件内容，具体描述如下：

对于普通文件的读取路径（->read_folio()），文件系统可以将密文读入页面缓存并在原地解密。在解密完成之前，必须持有folio锁，以防止folio过早对用户空间可见。
对于普通文件的写入路径（->writepage()），文件系统不能在页面缓存中直接加密数据，因为必须保留缓存中的明文。因此，文件系统必须在一个临时缓冲区或“跳转页”中进行加密，然后写入临时缓冲区。某些文件系统，如UBIFS，无论是否加密都会使用临时缓冲区。其他文件系统，如ext4和F2FS，则需要特别分配跳转页用于加密。

文件名哈希与编码
-------------------

现代文件系统通过使用索引目录来加速目录查找。索引目录是按照文件名哈希组织的一棵树。当请求执行->lookup()时，文件系统通常会对要查找的文件名进行哈希处理，以便快速找到相应的目录项（如果有）。
使用加密后，必须支持并优化有无加密密钥情况下的查找。显然，不能对明文文件名进行哈希处理，因为没有密钥就无法获得明文文件名。（对明文文件名进行哈希处理也会使得文件系统的fsck工具无法优化加密目录。）相反，文件系统对密文文件名进行哈希处理，即实际上存储在磁盘上的目录项中的字节。当被要求使用密钥执行->lookup()时，文件系统只需加密用户提供的名称以获取密文。
没有密钥的查找更为复杂。原始密文中可能包含非法字符``\0``和``/``。因此，readdir()必须将密文进行base64url编码以供展示。对于大多数文件名，这工作得很好；在->lookup()时，文件系统只需将用户提供的名称进行base64url解码即可恢复为原始密文。
然而，对于非常长的文件名，base64url编码会导致文件名长度超过NAME_MAX。为了避免这种情况，readdir()实际上以一种简化的形式展示长文件名，该形式编码了密文文件名的一个强“哈希”，以及用于目录查找所需的可选文件系统特定哈希。这使得文件系统能够高置信度地将->lookup()中给定的文件名映射回之前由readdir()列出的特定目录项。详见源代码中的struct fscrypt_nokey_name。
请注意，无密钥情况下向用户空间展示文件名的具体方式将来可能会发生变化。这只是暂时展示有效文件名的一种方式，以便像`rm -r`这样的命令在加密目录上按预期工作。

测试
====

为了测试fscrypt，可以使用xfstests，这是Linux事实上的标准文件系统测试套件。首先，在相关的文件系统上运行“encrypt”组中的所有测试。也可以使用'inlinecrypt'挂载选项来测试内联加密支持的实现。例如，要使用`kvm-xfstests <https://github.com/tytso/xfstests-bld/blob/master/Documentation/kvm-quickstart.md>`_ 测试ext4和f2fs加密，可以执行以下命令：

    kvm-xfstests -c ext4,f2fs -g encrypt
    kvm-xfstests -c ext4,f2fs -g encrypt -m inlinecrypt

也可以用这种方式测试UBIFS加密，但应该单独执行，并且kvm-xfstests设置模拟UBI卷需要一些时间：

    kvm-xfstests -c ubifs -g encrypt

不应有任何测试失败。但是，使用非默认加密模式的测试（例如generic/549和generic/550）如果所需算法未构建到内核的crypto API中，则会被跳过。此外，访问原始块设备的测试（例如generic/399、generic/548、generic/549、generic/550）在UBIFS上会被跳过。
除了运行“encrypt”组测试外，对于ext4和f2fs，还可以使用“test_dummy_encryption”挂载选项来运行大多数xfstests。此选项会使所有新文件自动使用一个虚拟密钥加密，而无需进行任何API调用。这更彻底地测试了加密I/O路径。要使用kvm-xfstests执行此操作，请使用“encrypt”文件系统配置：

```
kvm-xfstests -c ext4/encrypt,f2fs/encrypt -g auto
kvm-xfstests -c ext4/encrypt,f2fs/encrypt -g auto -m inlinecrypt
```

由于这种方式运行的测试比使用“-g encrypt”更多，因此耗时也更长；因此也可以考虑使用`gce-xfstests <https://github.com/tytso/xfstests-bld/blob/master/Documentation/gce-xfstests.md>`_代替kvm-xfstests：

```
gce-xfstests -c ext4/encrypt,f2fs/encrypt -g auto
gce-xfstests -c ext4/encrypt,f2fs/encrypt -g auto -m inlinecrypt
```
