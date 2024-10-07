===========================
SipHash - 短输入PRF
===========================

:作者: Jason A. Donenfeld <jason@zx2c4.com>

SipHash 是一种密码学安全的PRF（带密钥的哈希函数），在处理短输入时表现出色，因此得名。它是由密码学家 Daniel J. Bernstein 和 Jean-Philippe Aumasson 设计的。它旨在替代某些用途中的 `jhash`、`md5_transform`、`sha1_transform` 等。
SipHash 接受一个包含随机生成数字的秘密密钥以及一个输入缓冲区或几个输入整数。它会输出一个无法与随机数区分的整数。你可以将该整数用作安全序列号的一部分、安全Cookie 或用于哈希表。
生成密钥
================

密钥应始终从密码学安全的随机数源生成，可以使用 `get_random_bytes` 或 `get_random_once`：

```c
siphash_key_t key;
get_random_bytes(&key, sizeof(key));
```

如果你不是从这里获取密钥，那你就是在做错事。
使用函数
================

有两种函数变体：一种接受整数列表，另一种接受缓冲区：

```c
u64 siphash(const void *data, size_t len, const siphash_key_t *key);
```

以及：

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

如果你传递通用的 `siphash` 函数一个固定长度的数据，它会在编译时进行常量折叠，并自动选择其中一个优化函数。
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

然后你可以像平常一样遍历返回的哈希桶。
安全性
========

SipHash 拥有非常高的安全性，其 128 位密钥使得攻击者即使能够观察到许多输出，也无法猜测函数的输出，因为 2^128 的输出数量是巨大的。
Linux 实现了 SipHash 的 "2-4" 变体。
结构传递陷阱
================

很多时候，XuY 函数可能不够大，相反，你可能希望传递一个预先填充好的结构体给 `siphash`。在这种情况下，重要的是要确保结构体中没有填充空洞。最简单的方法是按降序排列结构体成员，并使用 `offsetofend()` 而不是 `sizeof()` 来获取大小。为了性能原因，如果可能的话，最好将结构体对齐到正确的边界。以下是一个示例：

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
=========

如果你感兴趣了解更多，请阅读 SipHash 论文：
https://131002.net/siphash/siphash.pdf

-------------------------------------------------------------------------------

===============================================
HalfSipHash - SipHash 的不安全小兄弟
===============================================

:作者: Jason A. Donenfeld <jason@zx2c4.com>

万一 SipHash 对你的需求来说还不够快，你可能会考虑使用 HalfSipHash，这是一种令人恐惧但可能有用的选项。HalfSipHash 将 SipHash 的轮数从 "2-4" 减少到 "1-3"，更可怕的是，它使用了一个容易暴力破解的 64 位密钥（32 位输出），而不是 SipHash 的 128 位密钥。然而，这可能会吸引一些高性能 `jhash` 用户。
HalfSipHash 支持通过 "hsiphash" 家族的函数提供。
.. warning::
   除了作为哈希表键函数外，绝不要使用 `hsiphash` 函数，并且只有在完全确定输出永远不会传输出内核的情况下才这样做。这仅比 `jhash` 更有用，作为一种缓解哈希表泛洪拒绝服务攻击的手段。
在64位内核上，hsiphash函数实际上实现了SipHash-1-3，这是SipHash的一个减少轮数的变体，而不是HalfSipHash-1-3。这是因为，在64位代码中，SipHash-1-3的速度并不比HalfSipHash-1-3慢，并且可能更快。
请注意，这并不意味着在64位内核中hsiphash函数与siphash函数相同，或者它们是安全的；hsiphash函数仍然使用一个不太安全的减少轮数算法，并将其输出截断为32位。

生成hsiphash密钥
================

密钥应始终从加密安全的随机数源生成，可以使用get_random_bytes或get_random_once方法：

```c
hsiphash_key_t key;
get_random_bytes(&key, sizeof(key));
```

如果你没有从这里生成密钥，那么你做错了。

使用hsiphash函数
================

该函数有两个变体，一个接受整数列表，另一个接受缓冲区：

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

如果你将通用的hsiphash函数传递一个固定长度的数据，它会在编译时进行常量折叠并自动选择其中一个优化后的函数。

哈希表键函数的使用
=================

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

hsiphash() 大约是 jhash() 的三倍慢。对于许多替换情况，这不是问题，因为哈希表查找并不是瓶颈。总的来说，为了获得hsiphash()的安全性和抗DoS攻击能力，这可能是值得做出的牺牲。
