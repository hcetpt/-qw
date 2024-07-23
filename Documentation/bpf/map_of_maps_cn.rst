SPDX 许可证标识符：仅限 GPL-2.0
版权所有 (C) 2022，红帽公司
========================================================
BPF_MAP_TYPE_ARRAY_OF_MAPS 和 BPF_MAP_TYPE_HASH_OF_MAPS
========================================================

.. 注意::
   - 在内核版本 4.12 中引入了 `BPF_MAP_TYPE_ARRAY_OF_MAPS` 和 `BPF_MAP_TYPE_HASH_OF_MAPS`

`BPF_MAP_TYPE_ARRAY_OF_MAPS` 和 `BPF_MAP_TYPE_HASH_OF_MAPS` 提供了对映射中存储映射的一般支持。支持一层嵌套，其中外部映射包含单一类型的内部映射实例，例如 `array_of_maps->sock_map`
在创建外部映射时，使用一个内部映射实例来初始化外部映射关于其内部映射的元数据。这个内部映射与外部映射具有独立的生命周期，并且可以在创建外部映射后被删除
外部映射支持用户空间通过系统调用API进行元素查找、更新和删除。BPF程序只允许在外层映射中查找元素
.. 注意::
   - 不支持多级嵌套
- 任何BPF映射类型都可以作为内部映射使用，除了 `BPF_MAP_TYPE_PROG_ARRAY`
- BPF程序不能更新或删除外层映射条目
对于 `BPF_MAP_TYPE_ARRAY_OF_MAPS`，键是一个无符号32位整数索引，用于访问数组。该数组是固定大小的，有 `max_entries` 个元素，在创建时进行零初始化
对于 `BPF_MAP_TYPE_HASH_OF_MAPS`，定义映射时可以选择键类型。内核负责分配和释放键/值对，直到达到你指定的最大条目限制。哈希映射默认预分配哈希表元素。可以使用 `BPF_F_NO_PREALLOC` 标志在内存消耗过大时禁用预分配
使用
=====

内核 BPF 辅助函数
-----------------

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 `bpf_map_lookup_elem()` 辅助函数检索内部映射。此辅助函数返回指向内部映射的指针，如果没有找到条目则返回 `NULL`
示例
========

内核BPF示例
------------------

以下代码片段展示了如何在BPF程序中创建和初始化一个devmaps数组。需要注意的是，外部数组只能通过系统调用API从用户空间进行修改。
.. code-block:: c

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

更多关于外部映射声明性初始化的例子，请参考``progs/test_btf_map_in_map.c``文件，位于``tools/testing/selftests/bpf``目录下。

用户空间
----------

以下代码片段展示了如何创建基于数组的外部映射：

.. code-block:: c

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


以下代码片段展示了如何将内部映射添加到外部映射：

.. code-block:: c

    int add_devmap(int outer_fd, int index, const char *name) {
            int fd;

            fd = bpf_map_create(BPF_MAP_TYPE_DEVMAP, name,
                                sizeof(__u32), sizeof(__u32), 256, NULL);
            if (fd < 0)
                    return fd;

            return bpf_map_update_elem(outer_fd, &index, &fd, BPF_ANY);
    }

参考资料
==========

- https://lore.kernel.org/netdev/20170322170035.923581-3-kafai@fb.com/
- https://lore.kernel.org/netdev/20170322170035.923581-4-kafai@fb.com/
