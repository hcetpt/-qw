SipHash - 适用于短输入的伪随机函数
===========================================

:作者: 由Jason A. Donenfeld <jason@zx2c4.com> 编写

SipHash 是一种加密安全的伪随机函数（PRF）——即密钥散列函数——它在处理短输入时表现出色，这也是其名字的由来。该算法由密码学家Daniel J. Bernstein和Jean-Philippe Aumasson设计。SipHash旨在替代某些用途中的`jhash`、`md5_transform`、`sha1_transform`等。

SipHash接收一个充满随机生成数字的秘密密钥以及一个输入缓冲区或几个输入整数。它输出一个无法与随机数区分的整数。你可以将这个整数用作安全序列号、安全Cookie的一部分，或者将其用于哈希表中。

生成密钥
==================

密钥应当始终从加密安全的随机数源生成，可以使用`get_random_bytes`或`get_random_once`方法：

```c
siphash_key_t key;
get_random_bytes(&key, sizeof(key));
```

如果你不是从这里派生你的密钥，则说明你做错了。

使用函数
==================

有两种函数变体：一种接受整数列表，另一种则接受缓冲区：

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

如果你向通用的`siphash`函数传递固定长度的数据，它将在编译时进行常量折叠，并自动选择其中一个优化过的函数。

哈希表键函数的使用示例：

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

然后你可以像往常一样遍历返回的哈希桶。

安全性
========

SipHash具有非常高的安全性，拥有128位的密钥。只要密钥保持秘密，攻击者就不可能猜测出函数的输出，即使能够观察到许多输出，因为2^128个输出的数量是巨大的。

Linux实现了SipHash的“2-4”变种。

结构体传递的陷阱
==================

很多时候，XuY函数可能不够大，相反，你可能希望将预先填充的结构体传递给`siphash`。在这种情况下，重要的是要始终确保结构体没有填充空洞。最简单的方法是按照大小降序排列结构体成员，并使用`offsetofend()`而不是`sizeof()`来获取大小。为了性能原因，如果可能的话，最好将结构体对齐到正确的边界。下面是一个例子：

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
======

如果你有兴趣了解更多，请阅读SipHash论文：
https://131002.net/siphash/siphash.pdf

--------------------------------------------------------------------------------------

HalfSipHash - SipHash不那么安全的小兄弟
===========================================

:作者: 由Jason A. Donenfeld <jason@zx2c4.com> 编写

万一SipHash的速度不足以满足你的需求，你可能会考虑使用HalfSipHash，这是一个令人恐惧但可能有用的选项。HalfSipHash将SipHash的轮次从“2-4”减少到“1-3”，更可怕的是，它使用了一个容易暴力破解的64位密钥（带有32位输出），而不是SipHash的128位密钥。然而，这可能吸引一些高性能`jhash`用户。

HalfSipHash的支持通过“hsiphash”系列函数提供。
.. warning::
   除非作为哈希表键函数，并且你绝对确定输出永远不会离开内核，否则不要使用hsiphash函数。这仅在一定程度上比`jhash`有用，作为一种缓解哈希表洪水拒绝服务攻击的手段。
在64位内核上，hsiphash函数实际上实现了SipHash-1-3，这是SipHash的一个减少轮次的变体，而不是HalfSipHash-1-3。这是因为，在64位代码中，SipHash-1-3的速度并不比HalfSipHash-1-3慢，并且可能更快。请注意，这**并不意味着**在64位内核中hsiphash函数与siphash函数相同，或者它们是安全的；hsiphash函数仍然使用一种安全性较低的减少轮次算法，并将其输出截断为32位。

生成hsiphash密钥
================

密钥应始终从加密安全的随机数源生成，可以使用get_random_bytes或get_random_once：

```c
	hsiphash_key_t key;
	get_random_bytes(&key, sizeof(key));
```

如果你不是从这里导出你的密钥，那么你的方式是错误的。

使用hsiphash函数
================

该函数有两个变体，一个接收整数列表，另一个接收缓冲区：

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

如果你将通用的hsiphash函数用于固定长度的数据，它将在编译时进行常量折叠，并自动选择其中一个优化后的函数。

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

hsiphash()的速度大约是jhash()的三分之一。对于许多替换场景来说，这不是问题，因为哈希表查找并不是瓶颈所在。一般来说，为了hsiphash()的安全性和抵抗拒绝服务攻击的能力，这种牺牲可能是值得的。
