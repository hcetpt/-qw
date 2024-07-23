SPDX 许可证标识符：仅限 GPL-2.0
版权所有 (C) 2020 Google LLC
===========================
BPF_MAP_TYPE_CGROUP_STORAGE
===========================

`BPF_MAP_TYPE_CGROUP_STORAGE` 映射类型表示一个本地固定大小的存储。它仅在启用了 `CONFIG_CGROUP_BPF` 的情况下可用，且只对那些附加到 cgroup 的程序开放；这些程序由同一 Kconfig 提供。该存储空间通过程序所附加的 cgroup 来识别。
该映射为 BPF 程序所附加的 cgroup 提供了本地存储。相比通用哈希表，它提供了更快捷、更简单的访问方式，因为哈希表需要进行查找操作，并要求用户自行追踪活跃的 cgroup。
本文档描述了 `BPF_MAP_TYPE_CGROUP_STORAGE` 映射类型的使用和语义。其部分行为在 Linux 5.9 中有所改变，本文档将阐述这些差异。
使用
=====

该映射使用 `__u64 cgroup_inode_id` 或 `struct bpf_cgroup_storage_key` 类型的键，后者在 `linux/bpf.h` 中声明，如下所示：

    struct bpf_cgroup_storage_key {
            __u64 cgroup_inode_id;
            __u32 attach_type;
    };

`cgroup_inode_id` 是 cgroup 目录的 inode id。
`attach_type` 是程序的附加类型。
Linux 5.9 添加了对 `__u64 cgroup_inode_id` 类型键的支持。
当使用这种键类型时，特定 cgroup 和映射的所有附加类型将共享相同的存储空间。否则，如果键类型是 `struct bpf_cgroup_storage_key`，那么不同附加类型的程序将被隔离并看到不同的存储空间。
要在程序中访问存储空间，请使用 `bpf_get_local_storage`：

    void *bpf_get_local_storage(void *map, u64 flags)

`flags` 保留以备将来使用，当前必须为 0。
没有隐式同步。`BPF_MAP_TYPE_CGROUP_STORAGE` 的存储空间可以被不同 CPU 上的多个程序访问，用户应自行处理同步问题。BPF 基础设施提供了 `struct bpf_spin_lock` 来同步存储空间。参见 `tools/testing/selftests/bpf/progs/test_spin_lock.c`。
示例
========

当键类型为`struct bpf_cgroup_storage_key`时的使用方法如下所示：

```c
#include <bpf/bpf.h>

struct {
        __uint(type, BPF_MAP_TYPE_CGROUP_STORAGE);
        __type(key, struct bpf_cgroup_storage_key);
        __type(value, __u32);
} cgroup_storage SEC(".maps");

int program(struct __sk_buff *skb)
{
        __u32 *ptr = bpf_get_local_storage(&cgroup_storage, 0);
        __sync_fetch_and_add(ptr, 1);

        return 0;
}
```

在用户空间访问上述声明的地图：

```c
#include <linux/bpf.h>
#include <linux/libbpf.h>

__u32 map_lookup(struct bpf_map *map, __u64 cgrp, enum bpf_attach_type type)
{
        struct bpf_cgroup_storage_key key = {
                .cgroup_inode_id = cgrp,
                .attach_type = type,
        };
        __u32 value;
        bpf_map_lookup_elem(bpf_map__fd(map), &key, &value);
        // 省略错误检查
        return value;
}
```

或者，仅使用`__u64 cgroup_inode_id`作为键类型：

```c
#include <bpf/bpf.h>

struct {
        __uint(type, BPF_MAP_TYPE_CGROUP_STORAGE);
        __type(key, __u64);
        __type(value, __u32);
} cgroup_storage SEC(".maps");

int program(struct __sk_buff *skb)
{
        __u32 *ptr = bpf_get_local_storage(&cgroup_storage, 0);
        __sync_fetch_and_add(ptr, 1);

        return 0;
}
```

以及用户空间代码：

```c
#include <linux/bpf.h>
#include <linux/libbpf.h>

__u32 map_lookup(struct bpf_map *map, __u64 cgrp, enum bpf_attach_type type)
{
        __u32 value;
        bpf_map_lookup_elem(bpf_map__fd(map), &cgrp, &value);
        // 省略错误检查
        return value;
}
```

语义
=========

`BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`是这种地图类型的变体。这个每CPU的变体会为每个存储区域的每个CPU提供不同的内存区域。非每CPU的变体将为每个存储提供相同的内存区域。在Linux 5.9之前，一个存储的生命周期恰好与附件相同，并且对于单一的`CGROUP_STORAGE`地图，最多只能有一个使用该地图的加载程序。一个程序可以附加到多个cgroup或具有多种附加类型，每个附加都会创建一个新的清零存储。在解除附加时，存储会被释放。

在Linux 5.9之后，存储可以被多个程序共享。当一个程序附加到一个cgroup时，内核只会创建一个新的存储，如果地图中不存在针对cgroup和附加类型对的条目，否则旧的存储会被重复用于新的附加。如果地图是共享的附加类型，则在比较过程中会忽略附加类型。只有在地图或附加到的cgroup被释放时，存储才会被释放。解除附加不会直接释放存储，但它可能会导致地图的引用达到零，从而间接释放地图中的所有存储。

地图不再与任何BPF程序关联，这使得共享成为可能。但是，BPF程序仍然只能与每种类型（每CPU和非每CPU）的一个地图相关联。BPF程序不能使用超过一个`BPF_MAP_TYPE_CGROUP_STORAGE`或超过一个`BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`。

在所有版本中，用户空间都可以使用cgroup和附加类型对的附加参数作为`struct bpf_cgroup_storage_key`的键来读取或更新给定附加的存储。对于Linux 5.9的共享附加类型存储，只在比较过程中使用结构中的第一个值，即cgroup inode id，因此用户空间可以直接指定一个`__u64`。

存储在附加时绑定。即使程序附加到父级并在子级触发，存储仍属于父级。

用户空间无法在地图中创建新条目或删除现有条目。

测试运行的程序始终使用临时存储。
你没有给出需要翻译的句子或词语，所以我无法为你提供具体的翻译。请提供需要翻译的内容，我将很乐意帮助你。例如，如果你需要翻译"Hello, how are you?"，那么中文翻译就是“你好，你怎么样？”。

如果你是想让我用中文描述我是如何作为一个助手的，那么可以这样表达：“作为一名助手，我的目标是帮助用户解决他们的问题和需求。无论是提供信息、提供建议还是执行任务，我都尽力以最有效和准确的方式为用户提供支持。”
