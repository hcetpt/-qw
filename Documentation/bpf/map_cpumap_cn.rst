SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc

===================
BPF_MAP_TYPE_CPUMAP
===================

.. note::
   - `BPF_MAP_TYPE_CPUMAP` 在内核版本 4.15 中引入。

.. kernel-doc:: kernel/bpf/cpumap.c
 :doc: CPU 映射

这种映射类型的一个示例用例是基于软件的接收端扩展（Receive Side Scaling，RSS）。
CPUMAP 表示系统中的 CPU，以映射键进行索引，而映射值则是配置设置（每个 CPUMAP 元素）。每个 CPUMAP 元素都有一个专门的内核线程绑定到指定的 CPU 来表示远程 CPU 执行单元。
从 Linux 内核版本 5.9 开始，CPUMAP 可以在远程 CPU 上运行第二个 XDP 程序。这使得 XDP 程序能够将其处理分布在多个 CPU 上。例如，在初始 CPU（看到或接收到数据包的 CPU）需要进行最少的数据包处理的情况下，而远程 CPU（数据包指向的 CPU）可以负担更多的处理周期来处理帧。初始 CPU 是执行 XDP 重定向程序的位置。远程 CPU 接收原始的 `xdp_frame` 对象。

使用
=====

内核 BPF
----------
bpf_redirect_map()
^^^^^^^^^^^^^^^^^^
.. code-block:: c

     long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags)

将数据包重定向到由 `map` 和索引 `key` 引用的终端。
对于 `BPF_MAP_TYPE_CPUMAP`，此映射包含对 CPU 的引用。
`flags` 的最低两位在映射查找失败时用作返回码。这是为了让返回值可以是 XDP 程序返回码中的任何一个直到 `XDP_TX`，由调用者选择。

用户空间
----------
.. note::
    CPUMAP 元素只能从用户空间更新、查找和删除，不能从 eBPF 程序中操作。尝试从内核 eBPF 程序中调用这些函数将导致程序加载失败并产生验证警告。
bpf_map_update_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_update_elem(int fd, const void *key, const void *value, __u64 flags);

可以使用 `bpf_map_update_elem()` 辅助函数添加或更新 CPU 元素。此辅助函数会原子性地替换现有元素。`value` 参数可以是 `struct bpf_cpumap_val` 类型。
.. code-block:: c

    struct bpf_cpumap_val {
        __u32 qsize;  /* 到远程目标 CPU 的队列大小 */
        union {
            int   fd; /* 在映射写入时的程序描述符 */
            __u32 id; /* 在映射读取时的程序 ID */
        } bpf_prog;
    };

`flags` 参数可以是以下之一：
  - BPF_ANY: 创建新元素或更新现有元素
下面是给定文本的中文翻译：

- `BPF_NOEXIST`: 只有当元素不存在时创建新元素
- `BPF_EXIST`: 更新现有元素
bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_lookup_elem(int fd, const void *key, void *value);

可以使用`bpf_map_lookup_elem()`辅助函数来检索CPU条目。
bpf_map_delete_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_delete_elem(int fd, const void *key);

可以使用`bpf_map_delete_elem()`辅助函数删除CPU条目。此辅助函数在成功时返回0，失败时返回负数错误。

示例
========

内核
------

下面的代码片段展示了如何声明一个名为`cpu_map`的`BPF_MAP_TYPE_CPUMAP`类型，并如何使用轮询的方式将数据包重定向到远程CPU。

.. code-block:: c

   struct {
        __uint(type, BPF_MAP_TYPE_CPUMAP);
        __type(key, __u32);
        __type(value, struct bpf_cpumap_val);
        __uint(max_entries, 12);
    } cpu_map SEC(".maps");

    struct {
        __uint(type, BPF_MAP_TYPE_ARRAY);
        __type(key, __u32);
        __type(value, __u32);
        __uint(max_entries, 12);
    } cpus_available SEC(".maps");

    struct {
        __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
        __type(key, __u32);
        __type(value, __u32);
        __uint(max_entries, 1);
    } cpus_iterator SEC(".maps");

    SEC("xdp")
    int  xdp_redir_cpu_round_robin(struct xdp_md *ctx)
    {
        __u32 key = 0;
        __u32 cpu_dest = 0;
        __u32 *cpu_selected, *cpu_iterator;
        __u32 cpu_idx;

        cpu_iterator = bpf_map_lookup_elem(&cpus_iterator, &key);
        if (!cpu_iterator)
            return XDP_ABORTED;
        cpu_idx = *cpu_iterator;

        *cpu_iterator += 1;
        if (*cpu_iterator == bpf_num_possible_cpus())
            *cpu_iterator = 0;

        cpu_selected = bpf_map_lookup_elem(&cpus_available, &cpu_idx);
        if (!cpu_selected)
            return XDP_ABORTED;
        cpu_dest = *cpu_selected;

        if (cpu_dest >= bpf_num_possible_cpus())
            return XDP_ABORTED;

        return bpf_redirect_map(&cpu_map, cpu_dest, 0);
    }

用户空间
----------

下面的代码片段展示了如何动态地为CPUMAP设置最大条目数为系统上可用的最大CPU数量。

.. code-block:: c

    int set_max_cpu_entries(struct bpf_map *cpu_map)
    {
        if (bpf_map__set_max_entries(cpu_map, libbpf_num_possible_cpus()) < 0) {
            fprintf(stderr, "无法为cpu_map设置最大条目数: %s",
                strerror(errno));
            return -1;
        }
        return 0;
    }

参考
===========

- https://developers.redhat.com/blog/2021/05/13/receive-side-scaling-rss-with-ebpf-and-cpumap#redirecting_into_a_cpumap
