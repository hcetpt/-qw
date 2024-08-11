SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc

========================================================
BPF_MAP_TYPE_ARRAY_OF_MAPS 和 BPF_MAP_TYPE_HASH_OF_MAPS
========================================================

.. note::
   - `BPF_MAP_TYPE_ARRAY_OF_MAPS` 和 `BPF_MAP_TYPE_HASH_OF_MAPS` 在内核版本 4.12 中引入。

`BPF_MAP_TYPE_ARRAY_OF_MAPS` 和 `BPF_MAP_TYPE_HASH_OF_MAPS` 提供了通用的存储器（map）内嵌套存储器的支持。支持一层嵌套，即外部存储器包含单一类型的内部存储器实例，例如 `array_of_maps->sock_map`。
在创建外部存储器时，使用一个内部存储器实例来初始化该外部存储器对其内部存储器的元数据。此内部存储器与外部存储器生命周期独立，在外部存储器创建后可以删除。
外部存储器支持用户空间通过系统调用 API 进行元素查找、更新和删除。BPF 程序只允许在外层存储器中进行元素查找。
.. note::
   - 不支持多级嵌套。
   - 任何 BPF 存储器类型都可以作为内部存储器，除了 `BPF_MAP_TYPE_PROG_ARRAY`。
   - BPF 程序不能更新或删除外层存储器条目。
对于 `BPF_MAP_TYPE_ARRAY_OF_MAPS`，键是一个无符号 32 位整数索引。数组是固定大小的，包含 `max_entries` 个元素，并且在创建时零初始化。
对于 `BPF_MAP_TYPE_HASH_OF_MAPS`，可以在定义存储器时选择键类型。内核负责分配和释放键/值对，直到达到你指定的最大条目限制。哈希表默认采用预分配的方式。可以使用 `BPF_F_NO_PREALLOC` 标志禁用预分配以减少内存消耗。

使用方法
=====

内核 BPF 辅助函数
-----------------

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 `bpf_map_lookup_elem()` 辅助函数检索内部存储器。此辅助函数返回指向内部存储器的指针，如果没有找到条目则返回 `NULL`。
### 示例
#### 内核BPF示例
---

此代码片段展示了如何在BPF程序中创建和初始化一个`devmaps`数组。请注意，外部数组只能通过系统调用API从用户空间进行修改。
```c
struct inner_map {
        __uint(type, BPF_MAP_TYPE_DEVMAP);
        __uint(max_entries, 10);
        __type(key, __u32);
        __type(value, __u32);
} inner_map1 SEC(".maps"), inner_map2 SEC(".maps");

struct {
        __uint(type, BPF_MAP_TYPE_ARRAY_OF_MAPS);
        __uint(max_entries, 2);
        __type(key, __u32);
        __array(values, struct inner_map);
} outer_map SEC(".maps") = {
        .values = { &inner_map1,
                    &inner_map2 }
};
```

更多关于外部映射声明式初始化的示例，请参考`tools/testing/selftests/bpf/progs/test_btf_map_in_map.c`。

#### 用户空间
---

此代码片段展示了如何创建基于数组的外部映射：
```c
int create_outer_array(int inner_fd) {
        LIBBPF_OPTS(bpf_map_create_opts, opts, .inner_map_fd = inner_fd);
        int fd;

        fd = bpf_map_create(BPF_MAP_TYPE_ARRAY_OF_MAPS,
                            "example_array",       /* 名称 */
                            sizeof(__u32),         /* 键大小 */
                            sizeof(__u32),         /* 值大小 */
                            256,                   /* 最大条目数 */
                            &opts);                /* 创建选项 */
        return fd;
}
```

此代码片段展示了如何将内部映射添加到外部映射中：
```c
int add_devmap(int outer_fd, int index, const char *name) {
        int fd;

        fd = bpf_map_create(BPF_MAP_TYPE_DEVMAP, name,
                            sizeof(__u32), sizeof(__u32), 256, NULL);
        if (fd < 0)
                return fd;

        return bpf_map_update_elem(outer_fd, &index, &fd, BPF_ANY);
}
```

### 参考资料
- [https://lore.kernel.org/netdev/20170322170035.923581-3-kafai@fb.com/](https://lore.kernel.org/netdev/20170322170035.923581-3-kafai@fb.com/)
- [https://lore.kernel.org/netdev/20170322170035.923581-4-kafai@fb.com/](https://lore.kernel.org/netdev/20170322170035.923581-4-kafai@fb.com/)
