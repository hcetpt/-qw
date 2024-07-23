SPDX 许可证标识符：仅 GPL-2.0
版权所有(C) 2022，红帽公司
================================================
BPF_MAP_TYPE_ARRAY 和 BPF_MAP_TYPE_PERCPU_ARRAY
================================================

.. 注意::
   - `BPF_MAP_TYPE_ARRAY` 在内核版本 3.19 中引入
   - `BPF_MAP_TYPE_PERCPU_ARRAY` 在版本 4.6 中引入

`BPF_MAP_TYPE_ARRAY` 和 `BPF_MAP_TYPE_PERCPU_ARRAY` 提供了通用数组存储。键类型是一个无符号的32位整数（4字节），且映射的大小是固定的。数组的大小在创建时由 `max_entries` 定义。所有数组元素在创建时预先分配并初始化为零。`BPF_MAP_TYPE_PERCPU_ARRAY` 对于每个 CPU 使用不同的内存区域，而 `BPF_MAP_TYPE_ARRAY` 则使用相同的内存区域。可以存储的值可以是任意大小，但是所有数组元素都对齐到8字节。
从内核 5.5 版本开始，通过设置 `BPF_F_MMAPABLE` 标志，可以为 `BPF_MAP_TYPE_ARRAY` 启用内存映射。映射定义以页对齐，并从第一页开始。为了存储所有数组值，从第二页开始分配足够的、页大小的、页对齐的内存块，在某些情况下这会导致内存的过度分配。使用这种方法的好处在于性能提升和使用的便捷性，因为用户空间程序不需要使用辅助函数来访问和修改数据。

使用
=====

内核 BPF
--------

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 `bpf_map_lookup_elem()` 辅助函数检索数组元素
此辅助函数返回指向数组元素的指针，因此为了避免与用户空间读取值时发生数据竞争，用户必须在就地更新值时使用如 `__sync_fetch_and_add()` 这样的原语
bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)

可以使用 `bpf_map_update_elem()` 辅助函数更新数组元素
`bpf_map_update_elem()` 在成功时返回0，或在失败时返回负错误码
由于数组的大小是固定的，`bpf_map_delete_elem()` 不被支持
要清除数组元素，你可以使用 `bpf_map_update_elem()` 将零值插入到该索引处

每 CPU 数组
------------

存储在 `BPF_MAP_TYPE_ARRAY` 中的值可以被不同 CPU 上的多个程序访问。若要限制存储到单个 CPU，可以使用 `BPF_MAP_TYPE_PERCPU_ARRAY`。
当使用 `BPF_MAP_TYPE_PERCPU_ARRAY` 类型时，`bpf_map_update_elem()` 和 `bpf_map_lookup_elem()` 辅助函数会自动访问当前 CPU 的槽位。
bpf_map_lookup_percpu_elem()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   void *bpf_map_lookup_percpu_elem(struct bpf_map *map, const void *key, u32 cpu)

`bpf_map_lookup_percpu_elem()` 辅助函数可以用于查找特定 CPU 的数组值。在成功时返回值，如果未找到条目或 `cpu` 无效则返回 `NULL`。
并发性
-------

从内核版本 5.1 开始，BPF 基础设施提供了 `struct bpf_spin_lock` 来同步访问。
用户空间
--------

用户空间的访问使用与上述相同名称的 libbpf API，通过其 `fd` 标识地图。
示例
=====

请参阅 `tools/testing/selftests/bpf` 目录以获取功能示例。下面的代码样本展示了 API 的使用。
内核 BPF
--------

这个片段展示了如何在 BPF 程序中声明一个数组。
.. code-block:: c

    struct {
            __uint(type, BPF_MAP_TYPE_ARRAY);
            __type(key, u32);
            __type(value, long);
            __uint(max_entries, 256);
    } my_map SEC(".maps");

这个示例 BPF 程序展示了如何访问数组元素。
.. code-block:: c

    int bpf_prog(struct __sk_buff *skb)
    {
            struct iphdr ip;
            int index;
            long *value;

            if (bpf_skb_load_bytes(skb, ETH_HLEN, &ip, sizeof(ip)) < 0)
                    return 0;

            index = ip.protocol;
            value = bpf_map_lookup_elem(&my_map, &index);
            if (value)
                    __sync_fetch_and_add(value, skb->len);

            return 0;
    }

用户空间
--------

BPF_MAP_TYPE_ARRAY
~~~~~~~~~~~~~~~~~~

这个片段展示了如何使用 `bpf_map_create_opts` 设置标志来创建一个数组。
.. code-block:: c

    #include <bpf/libbpf.h>
    #include <bpf/bpf.h>

    int create_array()
    {
            int fd;
            LIBBPF_OPTS(bpf_map_create_opts, opts, .map_flags = BPF_F_MMAPABLE);

            fd = bpf_map_create(BPF_MAP_TYPE_ARRAY,
                                "example_array",       /* 名称 */
                                sizeof(__u32),         /* 键大小 */
                                sizeof(long),          /* 值大小 */
                                256,                   /* 最大条目数 */
                                &opts);                /* 创建选项 */
            return fd;
    }

这个片段展示了如何初始化数组的元素。
.. code-block:: c

    int initialize_array(int fd)
    {
            __u32 i;
            long value;
            int ret;

            for (i = 0; i < 256; i++) {
                    value = i;
                    ret = bpf_map_update_elem(fd, &i, &value, BPF_ANY);
                    if (ret < 0)
                            return ret;
            }

            return ret;
    }

这个片段展示了如何从数组中检索元素值。请注意，检索元素值的代码块并未给出，但基于上下文和已展示的函数，可以推断出它类似于 `bpf_map_lookup_elem()` 函数的使用，只是可能需要根据具体需求进行调整。例如，在用户空间中使用 `bpf_map_lookup_elem()` 函数来查找数组中的元素，其调用方式如下：
.. code-block:: c

    long value;
    int ret;

    ret = bpf_map_lookup_elem(fd, &index, (void**)&value);
    if (ret < 0) {
        // handle error
    }
    // use value here
以上是基于上下文推测的示例代码，实际应用中应根据具体情况进行相应修改。
下面是给定代码段的中文翻译：

```c
int lookup(int fd)
{
        __u32 index = 42;
        long value;
        int ret;

        ret = bpf_map_lookup_elem(fd, &index, &value);
        if (ret < 0)
                return ret;

        /* 在这里使用 value */
        assert(value == 42);

        return ret;
}
```

BPF_MAP_TYPE_PERCPU_ARRAY
~~~~~~~~~~~~~~~~~~~~~~~~~
此代码片段展示了如何初始化每个CPU数组的元素。
```c
int initialize_array(int fd)
{
        int ncpus = libbpf_num_possible_cpus();
        long values[ncpus];
        __u32 i, j;
        int ret;

        for (i = 0; i < 256 ; i++) {
                for (j = 0; j < ncpus; j++)
                        values[j] = i;
                ret = bpf_map_update_elem(fd, &i, &values, BPF_ANY);
                if (ret < 0)
                        return ret;
        }

        return ret;
}
```
此代码片段展示了如何访问数组值中的每个CPU元素。
```c
int lookup(int fd)
{
        int ncpus = libbpf_num_possible_cpus();
        __u32 index = 42, j;
        long values[ncpus];
        int ret;

        ret = bpf_map_lookup_elem(fd, &index, &values);
        if (ret < 0)
                return ret;

        for (j = 0; j < ncpus; j++) {
                /* 在这里使用每个CPU的值 */
                assert(values[j] == 42);
        }

        return ret;
}
```

语义
=====
如上例所示，当在用户空间访问`BPF_MAP_TYPE_PERCPU_ARRAY`时，每个值都是包含`ncpus`个元素的数组。调用`bpf_map_update_elem()`时，这些映射不能使用`BPF_NOEXIST`标志。
