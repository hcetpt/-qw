SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc

======================================
BPF_MAP_TYPE_ARRAY 和 BPF_MAP_TYPE_PERCPU_ARRAY
======================================

.. note::
   - ``BPF_MAP_TYPE_ARRAY`` 在内核版本 3.19 中引入
   - ``BPF_MAP_TYPE_PERCPU_ARRAY`` 在版本 4.6 中引入

``BPF_MAP_TYPE_ARRAY`` 和 ``BPF_MAP_TYPE_PERCPU_ARRAY`` 提供通用数组存储。键类型是一个无符号 32 位整数（4 字节），并且映射是固定大小的。数组的大小在创建时通过 ``max_entries`` 定义。所有数组元素在创建时都会预先分配并初始化为零。``BPF_MAP_TYPE_PERCPU_ARRAY`` 为每个 CPU 使用不同的内存区域，而 ``BPF_MAP_TYPE_ARRAY`` 使用相同的内存区域。可以存储的值可以是任意大小，但是所有数组元素都对齐到 8 字节。

自内核版本 5.5 起，可以通过设置标志 ``BPF_F_MMAPABLE`` 为 ``BPF_MAP_TYPE_ARRAY`` 启用内存映射。映射定义是按页对齐的，并且从第一页开始。分配足够数量的按页大小和按页对齐的内存块来存储所有的数组值，从第二页开始，在某些情况下这将导致内存过度分配。使用这种方法的好处是提高了性能和易用性，因为用户空间程序不需要使用辅助函数来访问和修改数据。

使用方法
========

内核 BPF
--------

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 ``bpf_map_lookup_elem()`` 辅助函数检索数组元素。此辅助函数返回指向数组元素的指针，因此为了避免与用户空间读取值时的数据竞争，用户必须在更新值时使用如 ``__sync_fetch_and_add()`` 这样的原语。
bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   long bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)

可以使用 ``bpf_map_update_elem()`` 辅助函数更新数组元素。
``bpf_map_update_elem()`` 在成功时返回 0，或在失败时返回负错误代码。

由于数组是固定大小的，所以不支持 ``bpf_map_delete_elem()``。要清空一个数组元素，可以使用 ``bpf_map_update_elem()`` 向该索引插入一个零值。

每 CPU 数组
------------

存储在 ``BPF_MAP_TYPE_ARRAY`` 中的值可以被不同 CPU 上的多个程序访问。为了将存储限制在一个 CPU 上，可以使用 ``BPF_MAP_TYPE_PERCPU_ARRAY``。
当使用 `BPF_MAP_TYPE_PERCPU_ARRAY` 类型时，`bpf_map_update_elem()` 和 `bpf_map_lookup_elem()` 辅助函数会自动访问当前 CPU 的槽。

`bpf_map_lookup_percpu_elem()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

```c
void *bpf_map_lookup_percpu_elem(struct bpf_map *map, const void *key, u32 cpu)
```

`bpf_map_lookup_percpu_elem()` 辅助函数可以用于查找特定 CPU 的数组值。如果成功则返回值，如果没有找到条目或 `cpu` 无效则返回 `NULL`。

并发性
------

从内核版本 5.1 开始，BPF 基础设施提供了 `struct bpf_spin_lock` 来同步访问。

用户空间
--------

从用户空间的访问使用与上述相同名称的 libbpf API，通过其 `fd` 来识别该 map。

示例
====

请参阅 `tools/testing/selftests/bpf` 目录中的功能示例。下面的代码样本展示了 API 的使用方法。

内核 BPF
--------

此代码段展示了如何在 BPF 程序中声明一个数组。
```c
struct {
        __uint(type, BPF_MAP_TYPE_ARRAY);
        __type(key, u32);
        __type(value, long);
        __uint(max_entries, 256);
} my_map SEC(".maps");
```

此示例 BPF 程序展示了如何访问数组元素。
```c
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
```

用户空间
--------

`BPF_MAP_TYPE_ARRAY`
~~~~~~~~~~~~~~~~~~~~~

此代码段展示了如何创建一个数组，使用 `bpf_map_create_opts` 来设置标志。
```c
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

int create_array()
{
        int fd;
        LIBBPF_OPTS(bpf_map_create_opts, opts, .map_flags = BPF_F_MMAPABLE);

        fd = bpf_map_create(BPF_MAP_TYPE_ARRAY,
                            "example_array",       /* name */
                            sizeof(__u32),         /* key size */
                            sizeof(long),          /* value size */
                            256,                   /* max entries */
                            &opts);                /* create opts */
        return fd;
}
```

此代码段展示了如何初始化数组的元素。
```c
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
```

此代码段展示了如何从数组中检索元素值。
这段代码和描述主要展示了如何使用 C 语言与 BPF (Berkeley Packet Filter) 接口进行交互，特别涉及到了 `BPF_MAP_TYPE_PERCPU_ARRAY` 类型的使用。下面是具体的中文翻译：

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

### 每个CPU数组 (BPF_MAP_TYPE_PERCPU_ARRAY)

这一段展示了如何初始化每个CPU数组中的元素。
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

这一段展示了如何访问数组值中每个CPU的元素。
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

### 语义

如上例所示，在用户空间访问 `BPF_MAP_TYPE_PERCPU_ARRAY` 类型时，每个值都是一个包含 `ncpus` 个元素的数组。当调用 `bpf_map_update_elem()` 函数时，这些映射不能使用 `BPF_NOEXIST` 标志。
