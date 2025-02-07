SPDX 许可证标识符: 仅 GPL-2.0
版权所有 (C) 2022 红帽公司
=========================
BPF_MAP_TYPE_BLOOM_FILTER
=========================

.. note::
   - `BPF_MAP_TYPE_BLOOM_FILTER` 在内核版本 5.16 中引入。

`BPF_MAP_TYPE_BLOOM_FILTER` 提供了一种 BPF 布隆过滤器映射。布隆过滤器是一种空间效率高的概率数据结构，用于快速测试一个元素是否存在于集合中。在布隆过滤器中，可能存在假阳性结果但不会有假阴性结果。布隆过滤器映射没有键，只有值。创建布隆过滤器映射时，必须使用键大小为 0。此布隆过滤器映射支持以下两种操作：

- 推送：将元素添加到映射中
- 查看：确定元素是否存在于映射中

BPF 程序必须使用 `bpf_map_push_elem` 将元素添加到布隆过滤器映射，并使用 `bpf_map_peek_elem` 查询映射。这些操作通过现有的 `bpf` 系统调用以如下方式暴露给用户空间应用程序：

- `BPF_MAP_UPDATE_ELEM` -> 推送
- `BPF_MAP_LOOKUP_ELEM` -> 查看

创建映射时指定的 `max_entries` 大小用于近似布隆过滤器的合理位图大小，并不被严格强制执行。如果用户希望向布隆过滤器插入比 `max_entries` 更多的条目，则可能会导致更高的假阳性率。
使用 `union bpf_attr` 中的 `map_extra` 的低 4 位在创建映射时配置布隆过滤器使用的哈希函数数量。如果不指定数量，默认使用 5 个哈希函数。通常情况下，使用更多哈希函数可以降低假阳性率并减慢查询速度。
无法从布隆过滤器映射中删除元素。布隆过滤器映射可以用作内部映射。用户负责同步并发更新和查看，以确保不会出现假阴性的查看结果。
使用方法
=====

内核 BPF
----------

bpf_map_push_elem()
~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   long bpf_map_push_elem(struct bpf_map *map, const void *value, u64 flags)

可以使用 `bpf_map_push_elem()` 辅助函数将 `value` 添加到布隆过滤器中。添加条目到布隆过滤器时，`flags` 参数必须设置为 `BPF_ANY`。该辅助函数在成功时返回 `0`，失败时返回负错误代码。
bpf_map_peek_elem()
~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   long bpf_map_peek_elem(struct bpf_map *map, void *value)

使用 `bpf_map_peek_elem()` 辅助函数来确定 `value` 是否存在于布隆过滤器映射中。此辅助函数如果 `value` 可能存在于映射中则返回 `0`，如果 `value` 肯定不在映射中则返回 `-ENOENT`。
用户空间
---------

bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_update_elem (int fd, const void *key, const void *value, __u64 flags)

用户空间程序可以使用 libbpf 的 `bpf_map_update_elem` 函数将 `value` 添加到布隆过滤器中。`key` 参数必须设置为 `NULL` 并且 `flags` 必须设置为 `BPF_ANY`。成功时返回 `0`，失败时返回负错误代码。
bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_lookup_elem (int fd, const void *key, void *value)

用户空间程序可以使用 libbpf 的 `bpf_map_lookup_elem` 函数来确定 `value` 是否存在于布隆过滤器中。`key` 参数必须设置为 `NULL`。如果 `value` 可能存在于映射中则返回 `0`，如果 `value` 肯定不在映射中则返回 `-ENOENT`。
示例
========

内核 BPF
----------

以下代码展示了如何在 BPF 程序中声明布隆过滤器：

.. code-block:: c

    struct {
            __uint(type, BPF_MAP_TYPE_BLOOM_FILTER);
            __type(value, __u32);
            __uint(max_entries, 1000);
            __uint(map_extra, 3);
    } bloom_filter SEC(".maps");

以下代码展示了如何在 BPF 程序中确定一个值是否存在布隆过滤器中：

.. code-block:: c

    void *lookup(__u32 key)
    {
            if (bpf_map_peek_elem(&bloom_filter, &key) == 0) {
                    /* 验证不是假阳性并使用二次查找（例如，在哈希表中）获取关联的值 */
                    return bpf_map_lookup_elem(&hash_table, &key);
            }
            return 0;
    }

用户空间
---------

以下代码展示了如何使用 libbpf 从用户空间创建布隆过滤器映射：

.. code-block:: c

    int create_bloom()
    {
            LIBBPF_OPTS(bpf_map_create_opts, opts,
                        .map_extra = 3);             /* 哈希函数的数量 */

            return bpf_map_create(BPF_MAP_TYPE_BLOOM_FILTER,
                                  "ipv6_bloom",      /* 名称 */
                                  0,                 /* 键大小，必须为零 */
                                  sizeof(ipv6_addr), /* 值大小 */
                                  10000,             /* 最大条目数 */
                                  &opts);            /* 创建选项 */
    }

以下代码展示了如何从用户空间向布隆过滤器添加元素：

.. code-block:: c

    int add_element(struct bpf_map *bloom_map, __u32 value)
    {
            int bloom_fd = bpf_map__fd(bloom_map);
            return bpf_map_update_elem(bloom_fd, NULL, &value, BPF_ANY);
    }

参考资料
==========

https://lwn.net/ml/bpf/20210831225005.2762202-1-joannekoong@fb.com/
