SPDX 许可证标识符: 仅 GPL-2.0
版权所有 (C) 2022 Meta Platforms, Inc. 及其关联公司

=========================
BPF_MAP_TYPE_CGRP_STORAGE
=========================

`BPF_MAP_TYPE_CGRP_STORAGE` 类型的地图代表 cgroups 的本地固定大小的存储。它只有在启用 `CONFIG_CGROUPS` 配置时可用。此类程序通过相同的 Kconfig 可用。可以通过查找包含该 cgroup 的地图来获取特定 cgroup 的数据。
本文档描述了 `BPF_MAP_TYPE_CGRP_STORAGE` 地图类型的使用和语义。

使用
=====

地图键必须是 `sizeof(int)` 大小，表示一个 cgroup 文件描述符。
要在程序中访问存储，可以使用 `bpf_cgrp_storage_get`：

```c
void *bpf_cgrp_storage_get(struct bpf_map *map, struct cgroup *cgroup, void *value, u64 flags)
```

`flags` 可以为 0 或 `BPF_LOCAL_STORAGE_GET_F_CREATE`，后者指示如果不存在本地存储则创建一个新的本地存储。
可以使用 `bpf_cgrp_storage_delete` 删除本地存储：

```c
long bpf_cgrp_storage_delete(struct bpf_map *map, struct cgroup *cgroup)
```

此地图对所有程序类型都可用。

示例
=====

以下是一个使用 `BPF_MAP_TYPE_CGRP_STORAGE` 的 BPF 程序示例：

```c
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct {
        __uint(type, BPF_MAP_TYPE_CGRP_STORAGE);
        __uint(map_flags, BPF_F_NO_PREALLOC);
        __type(key, int);
        __type(value, long);
} cgrp_storage SEC(".maps");

SEC("tp_btf/sys_enter")
int BPF_PROG(on_enter, struct pt_regs *regs, long id)
{
        struct task_struct *task = bpf_get_current_task_btf();
        long *ptr;

        ptr = bpf_cgrp_storage_get(&cgrp_storage, task->cgroups->dfl_cgrp, 0,
                                   BPF_LOCAL_STORAGE_GET_F_CREATE);
        if (ptr)
            __sync_fetch_and_add(ptr, 1);

        return 0;
}
```

用户空间访问上述声明的地图：

```c
#include <linux/bpf.h>
#include <linux/libbpf.h>

__u32 map_lookup(struct bpf_map *map, int cgrp_fd)
{
        __u32 *value;
        value = bpf_map_lookup_elem(bpf_map__fd(map), &cgrp_fd);
        if (value)
                return *value;
        return 0;
}
```

`BPF_MAP_TYPE_CGRP_STORAGE` 和 `BPF_MAP_TYPE_CGROUP_STORAGE` 的区别
============================================================================

旧的 cgroup 存储地图 `BPF_MAP_TYPE_CGROUP_STORAGE` 已被标记为过时（重命名为 `BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED`）。应改用新的 `BPF_MAP_TYPE_CGRP_STORAGE` 地图。下面列出了 `BPF_MAP_TYPE_CGRP_STORAGE` 和 `BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED` 的主要区别：
1. `BPF_MAP_TYPE_CGRP_STORAGE` 可用于所有程序类型，而 `BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED` 只对 cgroup 类型的程序如 BPF_CGROUP_INET_INGRESS 或 BPF_CGROUP_SOCK_OPS 等可用。
2. `BPF_MAP_TYPE_CGRP_STORAGE` 支持多个 cgroup 的本地存储，而 `BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED` 只支持由 BPF 程序附加的一个 cgroup。
(3). ``BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED`` 在程序绑定时分配本地存储，因此 ``bpf_get_local_storage()`` 总是返回非空的本地存储。而 ``BPF_MAP_TYPE_CGRP_STORAGE`` 在运行时分配本地存储，因此 ``bpf_cgrp_storage_get()`` 可能会返回空的本地存储。
为了避免出现空的本地存储问题，用户空间可以在 BPF 程序绑定前通过 ``bpf_map_update_elem()`` 预先分配本地存储。
(4). ``BPF_MAP_TYPE_CGRP_STORAGE`` 支持由 BPF 程序删除本地存储，而 ``BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED`` 仅在程序解绑时删除存储。
总的来说，``BPF_MAP_TYPE_CGRP_STORAGE`` 支持所有 ``BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED`` 的功能，并且提供更多功能。因此建议使用 ``BPF_MAP_TYPE_CGRP_STORAGE`` 而不是 ``BPF_MAP_TYPE_CGROUP_STORAGE_DEPRECATED``。
