...SPDX-Licenses-Identifier: GPL-2.0

=============================================
非对称/公钥加密密钥类型
=============================================

.. 内容列表：

  - 概述
- 密钥标识
- 访问非对称密钥
- 签名验证
- 非对称密钥子类型
- 实例化数据解析器
- 密钥环链接限制
概述
========

"非对称"密钥类型旨在作为用于公钥加密的密钥的容器，不对加密方法或密钥形式施加任何特定限制。非对称密钥被赋予一种子类型，定义与密钥关联的数据类型，并提供描述和销毁该数据的操作。然而，并不要求实际存储密钥数据在密钥中。
可以定义一个完全在内核中的密钥保留和操作子类型，但也可以提供对加密硬件（如TPM）的访问，这种硬件可用于保留相关密钥并使用该密钥执行操作。在这种情况下，非对称密钥将仅仅作为TPM驱动程序的接口。

还提供了一个数据解析器的概念。数据解析器负责从传递给实例化函数的数据块中提取信息。第一个识别数据块的解析器有权设置密钥的子类型，并定义可以在该密钥上执行的操作。
数据解析器可能会将数据块解释为表示密钥的位，或者将其解释为系统其他地方持有的密钥的引用（例如，TPM）。

### 密钥标识

如果添加一个名称为空的密钥，实例化数据解析器将有机会预解析密钥，并根据密钥内容确定应赋予密钥的描述。
这样就可以通过完全匹配或部分匹配来引用密钥。密钥类型还可以使用其他标准来引用密钥。
非对称密钥类型的匹配函数可以执行比简单地比较描述与标准字符串更广泛的比较：

  1) 如果标准字符串的形式是"id:<十六进制数字>"，则匹配函数将检查密钥的指纹，以查看"id:"后面的十六进制数字是否与尾部匹配。例如：
```
keyctl search @s asymmetric id:5acc2142
```
将匹配具有以下指纹的密钥：
```
1A00 2040 7601 7889 DE11  882C 3823 04AD 5ACC 2142
```

  2) 如果标准字符串的形式是"<子类型>:<十六进制数字>"，则匹配将像(1)那样匹配ID，但增加了只有指定子类型（例如tpm）的密钥才能匹配的限制。例如：
```
keyctl search @s asymmetric tpm:5acc2142
```
在`/proc/keys`中，会显示密钥指纹的最后8个十六进制数字以及子类型：
```
1a39e171 I-----     1 perm 3f010000     0     0 asymmetric modsign.0: DSA 5acc2142 []
```

### 访问非对称密钥

为了从内核中一般性地访问非对称密钥，需要包含以下文件：
```c
#include <crypto/public_key.h>
```
这提供了处理非对称/公钥的函数。
在那里定义了三个枚举来表示公钥加密算法：
```c
enum pkey_algo
```
这些算法使用的摘要算法：
```c
enum pkey_hash_algo
```
以及密钥标识符表示法：
```c
enum pkey_id_type
```
需要注意的是，因为不同标准下的密钥标识符不一定兼容，所以需要这些表示法类型。例如，PGP通过散列密钥数据加上一些PGP特定的元数据生成密钥标识符，而X.509具有任意的证书标识符。
在密钥上定义的操作包括：

  1) 签名验证
对于签名验证所需相同密钥数据，其他操作（如加密）也是可能的，但目前不支持；其他操作（如解密和签名生成）则需要额外的密钥数据。
#### 签名验证

提供了一个操作用于执行加密签名验证，使用非对称密钥提供或提供对公钥的访问：
```c
int verify_signature(const struct key *key,
                     const struct public_key_signature *sig);
```
调用者必须已经从某个来源获取了密钥，然后可以使用它来检查签名。调用者必须解析签名并将相关位转移到由sig指向的结构中：
```c
struct public_key_signature {
    u8 *digest;
    u8 digest_size;
    enum pkey_hash_algo pkey_hash_algo : 8;
    u8 nr_mpi;
    union {
        MPI mpi[2];
        ...
```
使用的算法必须记录在 `sig->pkey_hash_algo` 中，并且构成实际签名的所有 MPI（多精度整数）都应存储在 `sig->mpi[]` 中，同时 MPI 的数量应放置在 `sig->nr_mpi` 中。
此外，数据必须已经被调用者进行摘要处理，并且生成的哈希值应由 `sig->digest` 指向，哈希值的大小则应存放在 `sig->digest_size` 中。
该函数在成功时返回 0，如果签名不匹配则返回 -EKEYREJECTED。
如果指定了不受支持的公钥算法或公钥/哈希算法组合，或者密钥不支持该操作，则该函数也可能返回 -ENOTSUPP；如果某些参数包含异常数据，则可能返回 -EBADMSG 或 -ERANGE；如果无法分配内存，则返回 -ENOMEM。如果密钥参数类型错误或设置不完整，则可以返回 -EINVAL。
### 非对称密钥子类型

非对称密钥有一个子类型来定义可以在该密钥上执行的操作集以及确定哪些数据作为密钥负载附加。负载格式完全取决于子类型。
子类型由密钥数据解析器选择，解析器必须初始化所需的相应数据。非对称密钥保留对其子类型模块的引用。
可以在以下位置找到子类型的定义结构：

	#include <keys/asymmetric-subtype.h>

其定义如下：

    struct asymmetric_key_subtype {
	    struct module		*owner;
	    const char		*name;

	    void (*describe)(const struct key *key, struct seq_file *m);
	    void (*destroy)(void *payload);
	    int (*query)(const struct kernel_pkey_params *params,
			 struct kernel_pkey_query *info);
	    int (*eds_op)(struct kernel_pkey_params *params,
			  const void *in, void *out);
	    int (*verify_signature)(const struct key *key,
				    const struct public_key_signature *sig);
    };

非对称密钥通过它们的 `payload[asym_subtype]` 成员指向这个结构。
`owner` 和 `name` 字段应设置为拥有模块和子类型的名称。目前，名称仅用于打印语句。
子类型定义了一系列操作：

  1) `describe()`
必选。这允许子类型在 `/proc/keys` 中针对密钥显示一些信息。例如，可以显示公钥算法的名称。密钥类型将在显示完此信息后显示密钥身份字符串的尾部。
### 2) `destroy()`
**必选。** 这个函数应该释放与密钥相关的内存。非对称密钥会负责释放指纹并解除对子类型模块的引用。

### 3) `query()`
**必选。** 这是一个用于查询密钥功能的函数。

### 4) `eds_op()`
**可选。** 这是加密、解密和签名创建操作（通过参数结构中的操作ID来区分）的入口点。子类型可以以任何方式实现一个操作，包括卸载到硬件上。

### 5) `verify_signature()`
**可选。** 这是签名验证的入口点。子类型可以以任何方式实现一个操作，包括卸载到硬件上。

### 实例化数据解析器

非对称密钥类型通常不希望存储或处理包含密钥数据的原始数据块。如果需要使用它，则必须每次都对其进行解析和错误检查。此外，数据块的内容可能包含可以执行的各种检查（例如自我签名、有效期等），并且可能包含有关密钥的有用信息（标识符、能力等）。另外，该数据块可能表示指向包含密钥的硬件的指针，而不是密钥本身。
可以为其实现解析器的blob格式示例包括：

- OpenPGP数据包流 [RFC 4880]
- X.509 ASN.1 流
- 指向TPM密钥
- 指向UEFI密钥
- PKCS#8私钥 [RFC 5208]
- PKCS#5加密私钥 [RFC 2898]

在密钥实例化过程中，将尝试列表中的每个解析器，直到找到一个不返回-EBADMSG的解析器为止。
解析器定义结构可以在以下位置找到：

	#include <keys/asymmetric-parser.h>

其结构如下所示：

    struct asymmetric_key_parser {
	    struct module	*owner; // 所属模块
	    const char	*name; // 解析器名称

	    int (*parse)(struct key_preparsed_payload *prep); // 解析函数
    };

所属模块和名称字段应设置为拥有该解析器的模块及其名称。
目前仅定义了一个必须实现的解析器操作：

  1) parse()
此函数被调用以从密钥创建和更新路径预解析密钥。
特别地，它在密钥分配_之前_被调用，并且因此，在调用者拒绝提供描述的情况下，允许它为密钥提供描述。

调用者传递一个以下结构体的指针，除了data、datalen和quotalen之外的所有字段都被清空 [参见Documentation/security/keys/core.rst]::

    结构体 key_preparsed_payload {
        char         *description; // 描述
        void         *payload[4];  // 负载
        const void   *data;        // 数据
        size_t       datalen;      // 数据长度
        size_t       quotalen;     // 配额长度
    };

实例化数据位于由data指向的数据块中，其大小为datalen。解析(parse())函数不允许更改这两个值，并且不应该更改其他任何值_除非_它们识别该数据块格式并且不会返回-EBADMSG来表示这不是它们的格式。
如果解析器对数据块满意，它应当为密钥提议一个描述并将其附加到->description上，->payload[asym_subtype]应当设置为指向要使用的子类型，->payload[asym_crypto]应当设置为指向该子类型的初始化数据，
->payload[asym_key_ids]应当指向一个或多个十六进制指纹，而quotalen应当更新以指示此密钥应占用多少配额。
清理时，附加到->payload[asym_key_ids]和->description上的数据将通过kfree()释放，附加到->payload[asym_crypto]上的数据将传递给子类型的->destroy()方法进行处理。
对于由->payload[asym_subtype]指向的子类型，将增加模块引用计数。

如果数据格式未被识别，则应当返回-EBADMSG。如果被识别但因某种原因无法设置密钥，则应当返回其他负错误代码。成功时，应当返回0。
密钥的指纹字符串可能部分匹配。对于RSA和DSA这样的公钥算法，这很可能是一个可打印的十六进制版本的密钥指纹。

提供了用于注册和注销解析器的函数::

    int register_asymmetric_key_parser(struct asymmetric_key_parser *parser);
    void unregister_asymmetric_key_parser(struct asymmetric_key_parser *subtype);

解析器不能有相同的名称。除此之外，这些名称仅用于调试消息中的显示。

密钥环链接限制
==================

从用户空间使用add_key创建的密钥环可以配置为检查待链接密钥的签名。没有有效签名的密钥不允许链接。
可用几种限制方法：

  1) 使用内建的信任密钥环进行限制

     - 与KEYCTL_RESTRICT_KEYRING一起使用的选项字符串：
       - "builtin_trusted"

     内建信任密钥环将被搜索以查找签名密钥。
如果没有配置内建信任密钥环，则所有链接都将被拒绝。ca_keys内核参数也会影响用于签名验证的密钥。
2) 限制使用内核内置和次级受信任的密钥环

     - 与 `KEYCTL_RESTRICT_KEYRING` 一起使用的选项字符串：
       - "builtin_and_secondary_trusted"

     内核内置和次级受信任的密钥环将被搜索以查找签名密钥。如果未配置次级受信任的密钥环，则此限制行为将类似于 "builtin_trusted" 选项。参数 `ca_keys` 也会影响用于签名验证的密钥。
3) 限制使用单独的密钥或密钥环

     - 与 `KEYCTL_RESTRICT_KEYRING` 一起使用的选项字符串：
       - "key_or_keyring:<密钥或密钥环序列号>[:chain]"

     每当请求创建密钥链接时，只有当要链接的密钥由指定的密钥之一签名时，链接才会成功。可以通过直接提供一个非对称密钥的序列号来指定该密钥，或者通过提供密钥环的序列号来搜索一组密钥中的签名密钥。
当在字符串末尾提供了 "chain" 选项时，还会在目标密钥环中搜索签名密钥。
这允许通过按顺序（从根证书开始）将每个证书添加到密钥环中来验证证书链。例如，可以创建并填充一个包含一组根证书链接的密钥环，并为要验证的每个证书链设置一个单独的、受限的密钥环：

	# 创建并填充包含根证书的密钥环
	root_id=`keyctl add keyring root-certs "" @s`
	keyctl padd asymmetric "" $root_id < root1.cert
	keyctl padd asymmetric "" $root_id < root2.cert

	# 创建并限制用于证书链的密钥环
	chain_id=`keyctl add keyring chain "" @s`
	keyctl restrict_keyring $chain_id asymmetric key_or_keyring:$root_id:chain

	# 尝试添加证书链中的每个证书，从最接近根的证书开始
keyctl padd asymmetric "" $chain_id < intermediateA.cert
	keyctl padd asymmetric "" $chain_id < intermediateB.cert
	keyctl padd asymmetric "" $chain_id < end-entity.cert

     如果最终的实体证书成功地添加到了 "chain" 密钥环中，我们可以确信它具有有效的签名链，该签名链可追溯到其中一个根证书。
单个密钥环可用于验证签名链，方法是在链接根证书后限制该密钥环：

	# 为证书链创建密钥环并添加根证书
	chain2_id=`keyctl add keyring chain2 "" @s`
	keyctl padd asymmetric "" $chain2_id < root1.cert

	# 限制已链接根1.cert的密钥环。证书将继续被密钥环链接
keyctl restrict_keyring $chain2_id asymmetric key_or_keyring:0:chain

	# 尝试添加证书链中的每个证书，从最接近根的证书开始
keyctl padd asymmetric "" $chain2_id < intermediateA.cert
	keyctl padd asymmetric "" $chain2_id < intermediateB.cert
	keyctl padd asymmetric "" $chain2_id < end-entity.cert

     如果最终的实体证书成功地添加到了 "chain2" 密钥环中，我们可以确信存在有效的签名链，该签名链可追溯到添加到密钥环被限制之前的根证书。
在所有这些情况下，如果找到了签名密钥，则将使用该签名密钥验证要链接的密钥的签名。仅当签名验证成功时，请求的密钥才会被添加到密钥环中。如果找不到父证书，则返回 `-ENOKEY`；如果签名检查失败或密钥被列入黑名单，则返回 `-EKEYREJECTED`。如果无法执行签名检查，则可能会返回其他错误。
