### SPDX 许可证标识符：GPL-2.0-only
### 版权所有 (C) 2020 Google LLC
===========================
### BPF_MAP_TYPE_CGROUP_STORAGE
===========================

`BPF_MAP_TYPE_CGROUP_STORAGE` 类型的地图代表了一个本地固定大小的存储空间。它仅在启用了 `CONFIG_CGROUP_BPF` 的情况下可用，并且只对那些绑定到 cgroups 的程序开放；这些程序由同一个 Kconfig 配置提供。该存储空间通过程序所绑定的 cgroup 来识别。
该地图为绑定到 cgroup 的 BPF 程序提供了一个本地存储空间。与通用哈希表相比，它提供了更快捷和更简单的访问方式，因为通用哈希表需要进行哈希查找，并要求用户自行跟踪活跃的 cgroups。
本文档描述了 `BPF_MAP_TYPE_CGROUP_STORAGE` 地图类型的使用方法和语义。在 Linux 5.9 中，其某些行为发生了变化，本文档将对此进行说明。

#### 使用
=====

该地图使用键类型为 `__u64 cgroup_inode_id` 或 `struct bpf_cgroup_storage_key`，这些类型在 `linux/bpf.h` 中声明：

```c
struct bpf_cgroup_storage_key {
        __u64 cgroup_inode_id;
        __u32 attach_type;
};
```

`cgroup_inode_id` 是 cgroup 目录的inode ID。
`attach_type` 是程序的绑定类型。
在 Linux 5.9 中，增加了对 `__u64 cgroup_inode_id` 作为键类型的支援。
当使用这种键类型时，特定 cgroup 和地图的所有绑定类型将共享同一存储空间。而如果使用 `struct bpf_cgroup_storage_key` 类型，则不同绑定类型的程序将会被隔离并看到不同的存储空间。
要在程序中访问该存储空间，请使用 `bpf_get_local_storage` 函数：

```c
void *bpf_get_local_storage(void *map, u64 flags)
```

`flags` 字段保留以供将来使用，目前必须设置为 0。
该存储空间没有隐式同步机制。`BPF_MAP_TYPE_CGROUP_STORAGE` 类型的地图可以被不同 CPU 上的多个程序访问，用户应自行负责同步。BPF 基础架构提供了 `struct bpf_spin_lock` 用于同步存储空间。参考 `tools/testing/selftests/bpf/progs/test_spin_lock.c`。
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

`BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE` 是这种地图类型的变体。这个每个CPU的变体对于每个存储区域在每个CPU上都有不同的内存区域。非每个CPU的变体对每个存储区域有相同的内存区域。在Linux 5.9之前，存储的生命周期严格地与附件相关，并且对于一个 `CGROUP_STORAGE` 地图，最多只能有一个加载的程序使用该地图。一个程序可以附加到多个cgroup或具有多个附加类型，并且每次附加都会创建一个新的零初始化存储。当程序解除绑定时，存储被释放。

在Linux 5.9及以后的版本中，存储可以被多个程序共享。当一个程序附加到一个cgroup时，内核只会创建一个新的存储，如果地图不已经包含cgroup和附加类型对的条目，否则将重用旧的存储为新的附加。如果地图是附加类型共享，则比较时不考虑附加类型。只有当地图或所附的cgroup被释放时，才会释放存储。解除绑定不会直接释放存储，但它可能会导致地图的引用计数降至零，并间接释放地图中的所有存储。

地图不再与任何BPF程序关联，从而使得共享成为可能。然而，BPF程序仍然只能与每种类型（每个CPU和非每个CPU）的一个地图关联。一个BPF程序不能使用超过一个 `BPF_MAP_TYPE_CGROUP_STORAGE` 或超过一个 `BPF_MAP_TYPE_PERCPU_CGROUP_STORAGE`。

在所有版本中，用户空间都可以使用cgroup和附加类型对的附加参数作为 `struct bpf_cgroup_storage_key` 的键来读取或更新给定附加的存储。对于Linux 5.9的附加类型共享存储，结构中的第一个值，cgroup inode id，在比较期间被使用，因此用户空间可以直接指定一个 `__u64`。

存储在附加时绑定。即使程序附加到父级并在子级触发，存储仍然属于父级。

用户空间不能在地图中创建新条目或删除现有条目。

测试运行的程序始终使用临时存储。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
