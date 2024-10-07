===========================
SipHash - 短输入PRF
===========================

:作者: Jason A. Donenfeld <jason@zx2c4.com>

SipHash 是一种密码学安全的 PRF（带密钥的哈希函数），在处理短输入时表现非常出色，因此得名。它是由密码学家 Daniel J. Bernstein 和 Jean-Philippe Aumasson 设计的。它旨在替代某些用途中的 `jhash`、`md5_transform`、`sha1_transform` 等。
SipHash 接受一个填满了随机生成数字的秘密密钥以及一个输入缓冲区或几个输入整数。它输出一个无法与随机数区分的整数。然后你可以将该整数用于安全序列号、安全Cookie或将其用于哈希表。

生成密钥
================

密钥应始终从密码学安全的随机数源中生成，可以使用 `get_random_bytes` 或 `get_random_once`：

```c
siphash_key_t key;
get_random_bytes(&key, sizeof(key));
```

如果你不是通过这种方式生成密钥，那你就做错了。

使用这些函数
================

有两个变体的函数，一个接受整数列表，另一个接受缓冲区：

```c
u64 siphash(const void *data, size_t len, const siphash_key_t *key);
```

还有：

```c
u64 siphash_1u64(u64, const siphash_key_t *key);
u64 siphash_2u64(u64, u64, const siphash_key_t *key);
u64 siphash_3u64(u64, u64, u64, const siphash_key_t *key);
u64 siphash_4u64(u64, u64, u64, u64, const siphash_key_t *key);
u64 siphash_1u32(u32, const siphash_key_t *key);
u64 siphash_2u32(u32, u32, const siphash_key_t *key);
u64 siphash_3u32(u32, u32, u32, const siphash_key_t *key);
u64 siphash_4u32(u32, u32, u32, u32, const siphash_key_t *key);
```

如果你传递给通用的 `siphash` 函数一个固定长度的数据，它将在编译时常量折叠并自动选择一个优化函数。

哈希表键函数用法：

```c
struct some_hashtable {
    DECLARE_HASHTABLE(hashtable, 8);
    siphash_key_t key;
};

void init_hashtable(struct some_hashtable *table)
{
    get_random_bytes(&table->key, sizeof(table->key));
}

static inline hlist_head *some_hashtable_bucket(struct some_hashtable *table, struct interesting_input *input)
{
    return &table->hashtable[siphash(input, sizeof(*input), &table->key) & (HASH_SIZE(table->hashtable) - 1)];
}
```

然后你可以像往常一样迭代返回的哈希桶。

安全性
========

SipHash 拥有极高的安全性，其 128 位密钥使得只要密钥保密，攻击者就不可能猜测出函数的输出，即使能够观察到许多输出也是如此，因为 \(2^{128}\) 的输出量是巨大的。
Linux 实现了 SipHash 的 "2-4" 变体。

结构体传递陷阱
================

很多时候，`XuY` 函数可能不够大，相反，你可能希望传递一个预先填充的结构体给 `siphash`。在这种情况下，重要的是要确保结构体没有填充孔。最简单的方法是按大小降序排列结构体成员，并且使用 `offsetofend()` 而不是 `sizeof()` 来获取大小。出于性能原因，如果可能的话，最好将结构体对齐到正确的边界。以下是一个示例：

```c
const struct {
    struct in6_addr saddr;
    u32 counter;
    u16 dport;
} __aligned(SIPHASH_ALIGNMENT) combined = {
    .saddr = *(struct in6_addr *)saddr,
    .counter = counter,
    .dport = dport
};
u64 h = siphash(&combined, offsetofend(typeof(combined), dport), &secret);
```

资源
=====

如果你想了解更多，请阅读 SipHash 论文：https://131002.net/siphash/siphash.pdf

-------------------------------------------------------------------------------

===============================
HalfSipHash - SipHash 的不安全弟弟
===============================

:作者: Jason A. Donenfeld <jason@zx2c4.com>

万一 SipHash 对你的需求来说不够快，你可能会考虑使用 HalfSipHash，这是一个令人恐惧但可能有用的选项。HalfSipHash 将 SipHash 的轮数从 "2-4" 减少到 "1-3" 并且，更可怕的是，使用了一个容易暴力破解的 64 位密钥（输出为 32 位）而不是 SipHash 的 128 位密钥。然而，这可能会吸引一些高性能 `jhash` 用户。
HalfSipHash 支持通过 "hsiphash" 家族的函数提供。

.. warning::
   除了作为哈希表键函数外，永远不要使用 `hsiphash` 函数，并且只有当你完全确定输出永远不会传输出内核时才能使用。这仅比 `jhash` 在缓解哈希表洪水拒绝服务攻击方面稍微有用。
在64位内核上，`hsiphash` 函数实际上实现了 SipHash-1-3，这是 SipHash 的一个缩减轮数的变体，而不是 HalfSipHash-1-3。这是因为，在64位代码中，SipHash-1-3 的速度并不比 HalfSipHash-1-3 慢，并且可能更快。请注意，这**并不意味着**在64位内核中 `hsiphash` 函数与 `siphash` 函数相同，或者它们是安全的；`hsiphash` 函数仍然使用一个不太安全的缩减轮数算法，并将其输出截断为32位。

生成 `hsiphash` 密钥
================

密钥应始终从密码学安全的随机数源生成，可以使用 `get_random_bytes` 或 `get_random_once`：

```c
hsiphash_key_t key;
get_random_bytes(&key, sizeof(key));
```

如果你不是通过这种方式生成密钥，那么你做错了。

使用 `hsiphash` 函数
================

有两种变体的函数，一种接受整数列表，另一种接受缓冲区：

```c
u32 hsiphash(const void *data, size_t len, const hsiphash_key_t *key);
```

以及：

```c
u32 hsiphash_1u32(u32, const hsiphash_key_t *key);
u32 hsiphash_2u32(u32, u32, const hsiphash_key_t *key);
u32 hsiphash_3u32(u32, u32, u32, const hsiphash_key_t *key);
u32 hsiphash_4u32(u32, u32, u32, u32, const hsiphash_key_t *key);
```

如果你将通用的 `hsiphash` 函数传递一个固定长度的数据，它将在编译时进行常量折叠，并自动选择其中一个优化函数。

哈希表键函数的使用
==================

```c
struct some_hashtable {
	DECLARE_HASHTABLE(hashtable, 8);
	hsiphash_key_t key;
};

void init_hashtable(struct some_hashtable *table)
{
	get_random_bytes(&table->key, sizeof(table->key));
}

static inline hlist_head *some_hashtable_bucket(struct some_hashtable *table, struct interesting_input *input)
{
	return &table->hashtable[hsiphash(input, sizeof(*input), &table->key) & (HASH_SIZE(table->hashtable) - 1)];
}
```

然后你可以像往常一样迭代返回的哈希桶。

性能
====

`hsiphash()` 大约是 `jhash()` 的三倍慢。对于许多替换情况，这不会成为问题，因为哈希表查找并不是瓶颈。一般来说，为了获得 `hsiphash()` 的安全性和抗拒绝服务攻击能力，这种牺牲可能是值得的。
