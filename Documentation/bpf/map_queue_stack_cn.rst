SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc
=========================================
BPF_MAP_TYPE_QUEUE 和 BPF_MAP_TYPE_STACK
=========================================

.. 注意::
   - `BPF_MAP_TYPE_QUEUE` 和 `BPF_MAP_TYPE_STACK` 在内核版本 4.20 中引入

`BPF_MAP_TYPE_QUEUE` 提供先进先出（FIFO）存储，而 `BPF_MAP_TYPE_STACK` 提供后进先出（LIFO）存储以供 BPF 程序使用。这些映射支持预览、弹出和推送操作，这些操作通过相应的辅助函数暴露给 BPF 程序。这些操作以以下方式通过现有的 `bpf` 系统调用暴露给用户空间应用：

- `BPF_MAP_LOOKUP_ELEM` -> 预览
- `BPF_MAP_LOOKUP_AND_DELETE_ELEM` -> 弹出
- `BPF_MAP_UPDATE_ELEM` -> 推送

`BPF_MAP_TYPE_QUEUE` 和 `BPF_MAP_TYPE_STACK` 不支持 `BPF_F_NO_PREALLOC`
使用
=====

内核 BPF
----------

bpf_map_push_elem()
~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_push_elem(struct bpf_map *map, const void *value, u64 flags)

可以使用 `bpf_map_push_elem` 辅助函数将一个元素 `value` 添加到队列或堆栈中。`flags` 参数必须设置为 `BPF_ANY` 或 `BPF_EXIST`。如果 `flags` 设置为 `BPF_EXIST`，则当队列或堆栈已满时，最旧的元素将被删除以腾出空间来添加 `value`。成功返回 `0`，失败返回负数错误码。
bpf_map_peek_elem()
~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_peek_elem(struct bpf_map *map, void *value)

此辅助函数从队列或堆栈中获取一个元素 `value` 而不将其移除。成功返回 `0`，失败返回负数错误码。
bpf_map_pop_elem()
~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_pop_elem(struct bpf_map *map, void *value)

此辅助函数从队列或堆栈中移除一个元素到 `value` 中。成功返回 `0`，失败返回负数错误码。
用户空间
---------

bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   int bpf_map_update_elem (int fd, const void *key, const void *value, __u64 flags)

用户空间程序可以使用 libbpf 的 `bpf_map_update_elem` 函数将 `value` 推送到队列或堆栈中。`key` 参数必须设置为 `NULL`，并且 `flags` 必须设置为 `BPF_ANY` 或 `BPF_EXIST`，与 `bpf_map_push_elem` 内核辅助函数具有相同的语义。成功返回 `0`，失败返回负数错误码。
bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   int bpf_map_lookup_elem (int fd, const void *key, void *value)

用户空间程序可以使用 libbpf 的 `bpf_map_lookup_elem` 函数预览队列或堆栈头部的 `value`。`key` 参数必须设置为 `NULL`。成功返回 `0`，失败返回负数错误码。
bpf_map_lookup_and_delete_elem()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   int bpf_map_lookup_and_delete_elem (int fd, const void *key, void *value)

用户空间程序可以使用 libbpf 的 `bpf_map_lookup_and_delete_elem` 函数从队列或堆栈头部弹出 `value`。`key` 参数必须设置为 `NULL`。成功返回 `0`，失败返回负数错误码。
示例
========

内核 BPF
----------

此代码片段展示了如何在 BPF 程序中声明一个队列：

.. 代码块:: c

    struct {
            __uint(type, BPF_MAP_TYPE_QUEUE);
            __type(value, __u32);
            __uint(max_entries, 10);
    } queue SEC(".maps");


用户空间
---------

此代码片段展示了如何使用 libbpf 的低级 API 从用户空间创建一个队列：

.. 代码块:: c

    int create_queue()
    {
            return bpf_map_create(BPF_MAP_TYPE_QUEUE,
                                  "sample_queue", /* 名称 */
                                  0,              /* key 大小，必须为零 */
                                  sizeof(__u32),  /* value 大小 */
                                  10,             /* 最大条目数 */
                                  NULL);          /* 创建选项 */
    }


参考资料
==========

https://lwn.net/ml/netdev/153986858555.9127.14517764371945179514.stgit@kernel/
