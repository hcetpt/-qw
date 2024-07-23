SPDX 许可证标识符：仅 GPL-2.0
版权所有(C) 2022，红帽公司
=====================
BPF_MAP_TYPE_LPM_TRIE
=====================

.. 注意::
   - `BPF_MAP_TYPE_LPM_TRIE` 在内核版本 4.11 中被引入。

`BPF_MAP_TYPE_LPM_TRIE` 提供了一个最长前缀匹配算法，可用于将 IP 地址与存储的前缀集进行匹配。内部，数据以不平衡节点的前缀树形式存储，使用 `prefixlen, data` 对作为其键。`data` 以网络字节序解释，即大端序，因此 `data[0]` 存储最高位字节。
LPM 前缀树可以创建具有最大前缀长度，该长度为 8 的倍数，范围从 8 到 2048。用于查找和更新操作的键是 `struct bpf_lpm_trie_key_u8`，通过 `max_prefixlen/8` 字节扩展。
- 对于 IPv4 地址，数据长度为 4 字节
- 对于 IPv6 地址，数据长度为 16 字节

在 LPM 前缀树中存储的值类型可以是任何用户定义的类型。
.. 注意::
   创建类型为 `BPF_MAP_TYPE_LPM_TRIE` 的映射时，必须设置 `BPF_F_NO_PREALLOC` 标志
使用
=====

内核 BPF
----------

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

对于给定的数据值，可以使用 `bpf_map_lookup_elem()` 辅助函数找到最长前缀条目。此辅助函数返回与最长匹配 `key` 关联的值的指针，如果没有找到条目，则返回 `NULL`。
进行最长前缀查找时，`key` 的 `prefixlen` 应设置为 `max_prefixlen`。例如，在搜索 IPv4 地址的最长前缀匹配项时，应将 `prefixlen` 设置为 `32`。
bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)

可以使用 `bpf_map_update_elem()` 辅助函数添加或更新前缀条目。此辅助函数原子地替换现有元素。
`bpf_map_update_elem()` 成功时返回 `0`，失败时返回负错误码。
### 注意：
参数 `flags` 必须是 `BPF_ANY`、`BPF_NOEXIST` 或 `BPF_EXIST` 中的一个，
但是该值会被忽略，从而默认采用 `BPF_ANY` 的语义。
`bpf_map_delete_elem()`
-----------------------

```c
long bpf_map_delete_elem(struct bpf_map *map, const void *key);
```

可以使用 `bpf_map_delete_elem()` 辅助函数删除前缀条目。成功时返回 0，失败时返回负数错误码。

### 用户空间
------

用户空间通过使用与上述相同的 libbpf API 访问，其中通过 `fd` 标识 map。

`bpf_map_get_next_key()`
------------------------

```c
int bpf_map_get_next_key(int fd, const void *cur_key, void *next_key);
```

用户空间程序可以通过 libbpf 的 `bpf_map_get_next_key()` 函数遍历 LPM 三叉树中的条目。首先通过将 `cur_key` 设置为 `NULL` 调用 `bpf_map_get_next_key()` 来获取第一个键。随后的调用将获取紧随当前键之后的下一个键。`bpf_map_get_next_key()` 在成功时返回 `0`，如果 `cur_key` 是三叉树中的最后一个键则返回 `-ENOENT`，或者在失败时返回负数错误码。

`bpf_map_get_next_key()` 将从最左边的叶子节点开始遍历 LPM 三叉树元素。这意味着迭代将先返回更具体的键，然后再返回较不具体的键。

### 示例
------

请参阅 `tools/testing/selftests/bpf/test_lpm_map.c` 以了解用户空间中使用 LPM 三叉树的示例。下面的代码片段展示了 API 的使用。

#### 内核 BPF
--------------

以下 BPF 代码片段展示了如何声明一个新的用于 IPv4 地址前缀的 LPM 三叉树：

```c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct ipv4_lpm_key {
        __u32 prefixlen;
        __u32 data;
};

struct {
        __uint(type, BPF_MAP_TYPE_LPM_TRIE);
        __type(key, struct ipv4_lpm_key);
        __type(value, __u32);
        __uint(map_flags, BPF_F_NO_PREALLOC);
        __uint(max_entries, 255);
} ipv4_lpm_map SEC(".maps");
```

以下 BPF 代码片段展示了如何通过 IPv4 地址进行查找：

```c
void *lookup(__u32 ipaddr)
{
        struct ipv4_lpm_key key = {
                .prefixlen = 32,
                .data = ipaddr
        };

        return bpf_map_lookup_elem(&ipv4_lpm_map, &key);
}
```

#### 用户空间
--------------

以下代码片段展示了如何向 LPM 三叉树中插入一个 IPv4 前缀条目：

```c
int add_prefix_entry(int lpm_fd, __u32 addr, __u32 prefixlen, struct value *value)
{
        struct ipv4_lpm_key ipv4_key = {
                .prefixlen = prefixlen,
                .data = addr
        };
        return bpf_map_update_elem(lpm_fd, &ipv4_key, value, BPF_ANY);
}
```

以下代码片段展示了用户空间程序如何遍历 LPM 三叉树中的条目：

```c
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

void iterate_lpm_trie(int map_fd)
{
        struct ipv4_lpm_key *cur_key = NULL;
        struct ipv4_lpm_key next_key;
        struct value value;
        int err;

        for (;;) {
                err = bpf_map_get_next_key(map_fd, cur_key, &next_key);
                if (err)
                        break;

                bpf_map_lookup_elem(map_fd, &next_key, &value);

                /* 使用 key 和 value */

                cur_key = &next_key;
        }
}
```
