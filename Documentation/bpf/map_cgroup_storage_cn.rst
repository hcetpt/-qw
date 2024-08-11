### SPDX 许可证标识符：GPL-2.0-only
### 版权所有 (C) 2020 Google LLC
===========================
### BPF_MAP_TYPE_CGROUP_STORAGE
===========================

`BPF_MAP_TYPE_CGROUP_STORAGE` 地图类型代表一个本地固定大小的存储空间。它仅在启用了 `CONFIG_CGROUP_BPF` 的情况下可用，并且只对那些绑定到 cgroups 的程序可用；这些程序由同一个 Kconfig 提供。该存储空间通过程序所绑定的 cgroup 来识别。地图为 BPF 程序所绑定的 cgroup 提供了本地存储。相比于通用哈希表，它提供了更快捷简单的访问方式，因为哈希表需要进行查找操作，并且要求用户自行追踪活跃的 cgroups。

本文档描述了 `BPF_MAP_TYPE_CGROUP_STORAGE` 地图类型的使用和语义。它的某些行为在 Linux 5.9 中有所变化，本文档将对此进行说明。

### 使用
=====

该地图使用键的类型为 `__u64 cgroup_inode_id` 或 `struct bpf_cgroup_storage_key`，这两种类型定义在 `linux/bpf.h` 中：

```c
struct bpf_cgroup_storage_key {
        __u64 cgroup_inode_id;
        __u32 attach_type;
};
```

`cgroup_inode_id` 是 cgroup 目录的 inode ID。
`attach_type` 是程序的绑定类型。

Linux 5.9 添加了对 `__u64 cgroup_inode_id` 键类型的直接支持。当使用这种键类型时，特定 cgroup 和地图的所有绑定类型将共享同一存储空间。否则，如果键类型是 `struct bpf_cgroup_storage_key`，那么不同绑定类型的程序将是隔离的，并且看到不同的存储空间。

要在程序中访问该存储空间，请使用 `bpf_get_local_storage`：

```c
void *bpf_get_local_storage(void *map, u64 flags)
```

`flags` 保留用于将来使用，目前必须为 0。

没有隐式同步。`BPF_MAP_TYPE_CGROUP_STORAGE` 类型的存储空间可以被不同 CPU 上的多个程序访问，用户应该自行处理同步问题。BPF 基础设施提供了 `struct bpf_spin_lock` 来同步存储空间。请参阅 `tools/testing/selftests/bpf/progs/test_spin_lock.c`。
### 示例
####

**使用 `struct bpf_cgroup_storage_key` 作为键类型的情况：**

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

**用户空间访问上述声明的地图：**

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
        // 错误检查省略
        return value;
}
```

**或者，仅使用 `__u64 cgroup_inode_id` 作为键类型：**

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

**以及用户空间：**

```c
#include <linux/bpf.h>
#include <linux/libbpf.h>

__u32 map_lookup(struct bpf_map *map, __u64 cgrp, enum bpf_attach_type type)
{
        __u32 value;
        bpf_map_lookup_elem(bpf_map__fd(map), &cgrp, &value);
        // 错误检查省略
        return value;
}
```

### 语义
####

`BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE` 是这种地图类型的变体。这个每个CPU的变体对于每个存储区域在每个CPU上都有不同的内存区域。非每个CPU的变体对每个存储区域有相同的内存区域。在Linux 5.9之前，存储的生命周期严格地与附件相关，并且对于一个`CGROUP_STORAGE`地图，最多只能有一个加载了该地图的程序。一个程序可以附加到多个cgroup或具有多种附加类型，并且每次附加都会创建一个新的零初始化的存储区域。当程序解除附加时，存储区域会被释放。

从Linux 5.9开始，存储可以被多个程序共享。当一个程序附加到一个cgroup时，内核仅在地图不包含对应于cgroup和附加类型对的条目时创建一个新的存储，否则就重用旧的存储以供新的附加使用。如果地图是附加类型共享的，则在比较时忽略附加类型。只有当地图本身或附加的cgroup被释放时，存储才会被释放。解除附加不会直接释放存储，但它可能会导致对地图的引用计数达到零，从而间接释放地图中的所有存储。

地图不再与任何BPF程序关联，这使得共享成为可能。然而，BPF程序仍然只能与每种类型（每个CPU和非每个CPU）的一个地图关联。一个BPF程序不能使用超过一个`BPF_MAP_TYPE_CGROUP_STORAGE`或超过一个`BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`。

在所有版本中，用户空间可以使用cgroup和附加类型对的附加参数作为`struct bpf_cgroup_storage_key`中的键来读取或更新给定附加的存储。对于Linux 5.9的附加类型共享存储，仅在比较期间使用结构中的第一个值，即cgroup inode id，因此用户空间可以直接指定`__u64`。

存储在附加时间绑定。即使程序附加到父级并在子级触发，存储仍然属于父级。

用户空间不能在地图中创建新条目或删除现有条目。

测试运行程序总是使用临时存储。
您没有提供需要翻译的文本。请提供需要翻译成中文的句子或词语。
