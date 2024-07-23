SPDX 许可证标识符: GPL-2.0-only
.. 版权所有 (C) 2022 Red Hat, Inc
.. 版权所有 (C) 2022-2023 Isovalent, Inc
===============================================
BPF_MAP_TYPE_HASH，包括 PERCPU 和 LRU 变体
===============================================

.. 注意::
   - ``BPF_MAP_TYPE_HASH`` 在内核版本 3.19 中引入
   - ``BPF_MAP_TYPE_PERCPU_HASH`` 在版本 4.6 中引入
   - 两种类型 ``BPF_MAP_TYPE_LRU_HASH`` 和 ``BPF_MAP_TYPE_LRU_PERCPU_HASH``
     都在版本 4.10 中引入

``BPF_MAP_TYPE_HASH`` 和 ``BPF_MAP_TYPE_PERCPU_HASH`` 提供了一般的哈希表存储。键和值都可以是结构体，
允许使用复合键和复合值。
内核负责分配和释放键/值对，直到达到您指定的 max_entries 限制。哈希表默认使用预分配的方式。可以使用
``BPF_F_NO_PREALLOC`` 标志来禁用预分配，当预分配消耗过多内存时。
``BPF_MAP_TYPE_PERCPU_HASH`` 为每个 CPU 提供独立的值槽。这些每个 CPU 的值内部存储在一个数组中。
``BPF_MAP_TYPE_LRU_HASH`` 和 ``BPF_MAP_TYPE_LRU_PERCPU_HASH`` 变体为各自的哈希表添加了最近最少使用（LRU）语义。当哈希表达到容量时，LRU 哈希将自动驱逐最近最少使用的条目。LRU 哈希维护了一个内部 LRU 列表用于选择要驱逐的元素。这个内部 LRU 列表在 CPU 间共享，但可以通过在调用 ``bpf_map_create`` 时使用 ``BPF_F_NO_COMMON_LRU`` 标志请求每个 CPU 的 LRU 列表。下表概述了根据地图类型和创建地图所使用的标志，LRU 地图的不同属性：
======================== ========================= ================================
标志                     ``BPF_MAP_TYPE_LRU_HASH`` ``BPF_MAP_TYPE_LRU_PERCPU_HASH``
======================== ========================= ================================
**BPF_F_NO_COMMON_LRU**  每 CPU LRU，全局地图   每 CPU LRU，每 CPU 地图
**!BPF_F_NO_COMMON_LRU** 全局 LRU，全局地图    全局 LRU，每 CPU 地图
======================== ========================= ================================

使用
=====

内核 BPF
----------

bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)

可以使用 ``bpf_map_update_elem()`` 辅助函数添加或更新哈希条目。此辅助函数以原子方式替换现有元素。``flags`` 参数可用于控制更新行为：

- ``BPF_ANY`` 将创建新元素或更新现有元素
- ``BPF_NOEXIST`` 只有当不存在时才会创建新元素
- ``BPF_EXIST`` 更新现有元素

``bpf_map_update_elem()`` 成功返回 0，失败则返回负数错误
bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 ``bpf_map_lookup_elem()`` 辅助函数检索哈希条目。此辅助函数返回与 ``key`` 关联的值的指针，如果没有找到条目，则返回 ``NULL``
bpf_map_delete_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_delete_elem(struct bpf_map *map, const void *key)

可以使用 ``bpf_map_delete_elem()`` 辅助函数删除哈希条目。此辅助函数成功返回 0，失败则返回负数错误
每 CPU 哈希表
--------------

对于 ``BPF_MAP_TYPE_PERCPU_HASH`` 和 ``BPF_MAP_TYPE_LRU_PERCPU_HASH``
``bpf_map_update_elem()`` 和 ``bpf_map_lookup_elem()`` 辅助函数会自动访问当前 CPU 的哈希槽。
`bpf_map_lookup_percpu_elem()`函数的中文翻译如下：

~~~~~~~~~~~~~~
代码块：C语言

void *bpf_map_lookup_percpu_elem(struct bpf_map *map, const void *key, u32 cpu);
~~~~~~~~~~~~~~

`bpf_map_lookup_percpu_elem()`辅助函数可以用于在特定CPU的哈希槽中查找值。它返回与`key`相关联的值，如果未找到条目或`cpu`无效，则返回`NULL`。

并发性
------

存储在`BPF_MAP_TYPE_HASH`中的值可以由运行在不同CPU上的程序并发访问。从内核版本5.1开始，BPF基础设施提供了`struct bpf_spin_lock`来同步访问。参见`tools/testing/selftests/bpf/progs/test_spin_lock.c`

用户空间
--------

bpf_map_get_next_key()
~~~~~~~~~~~~~~~~~~~~~~

代码块：C语言

int bpf_map_get_next_key(int fd, const void *cur_key, void *next_key);

在用户空间中，可以使用libbpf的`bpf_map_get_next_key()`函数遍历哈希表中的键。通过将`cur_key`设置为`NULL`调用`bpf_map_get_next_key()`可获取第一个键。后续调用将获取当前键之后的下一个键。`bpf_map_get_next_key()`在成功时返回0，在`cur_key`是哈希表中的最后一个键时返回-ENOENT，或者在失败情况下返回负错误码。

请注意，如果`cur_key`被删除，那么`bpf_map_get_next_key()`将返回哈希表中的*第一个*键，这是不希望看到的。如果存在键删除与`bpf_map_get_next_key()`混合使用的情况，建议使用批量查询。

示例
====

请参阅`tools/testing/selftests/bpf`目录以获取功能示例。下面的代码片段演示了API的使用。

这个例子展示了如何声明一个带有结构体键和结构体值的LRU哈希。
代码块：C语言

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct key {
    __u32 srcip;
};

struct value {
    __u64 packets;
    __u64 bytes;
};

struct {
        __uint(type, BPF_MAP_TYPE_LRU_HASH);
        __uint(max_entries, 32);
        __type(key, struct key);
        __type(value, struct value);
} packet_stats SEC(".maps");

这个例子展示了如何使用原子指令创建或更新哈希值：
代码块：C语言

static void update_stats(__u32 srcip, int bytes)
{
        struct key key = {
                .srcip = srcip,
        };
        struct value *value = bpf_map_lookup_elem(&packet_stats, &key);

        if (value) {
                __sync_fetch_and_add(&value->packets, 1);
                __sync_fetch_and_add(&value->bytes, bytes);
        } else {
                struct value newval = { 1, bytes };

                bpf_map_update_elem(&packet_stats, &key, &newval, BPF_NOEXIST);
        }
}

在用户空间中遍历上述声明的映射元素：
代码块：C语言

#include <bpf/libbpf.h>
#include <bpf/bpf.h>

static void walk_hash_elements(int map_fd)
{
        struct key *cur_key = NULL;
        struct key next_key;
        struct value value;
        int err;

        for (;;) {
                err = bpf_map_get_next_key(map_fd, cur_key, &next_key);
                if (err)
                        break;

                bpf_map_lookup_elem(map_fd, &next_key, &value);

                // 在此处使用键和值

                cur_key = &next_key;
        }
}

内部实现
=======

本节针对Linux开发者，描述了不属于稳定ABI的映射实现方面。以下细节可能会在未来版本的内核中发生变化。

`BPF_MAP_TYPE_LRU_HASH`及其变体
--------------------------------------

在LRU映射中更新元素可能在达到映射容量时触发驱逐行为。更新算法尝试执行以下步骤以强制执行LRU属性，这些步骤对其他CPU的参与操作的影响逐渐增加：

- 尝试使用CPU本地状态批处理操作
- 尝试从全局列表中获取空闲节点
- 尝试从全局列表中拉取任何节点并将其从哈希映射中移除
- 尝试从任何CPU的列表中拉取任何节点并将其从哈希映射中移除

下图以视觉方式描述了该算法。参见提交3a08c2fd7634("bpf: LRU List")以获取相应操作的完整解释：

内核图形：map_lru_hash_update.dot
替代文本：概述在映射更新期间采取的LRU驱逐步骤的图表
LRU哈希驱逐在`BPF_MAP_TYPE_LRU_HASH`及其变体的映射更新过程中。参见dot文件源代码以获取内核函数名称代码引用。
地图更新从右上角的椭圆形开始，标有"开始`bpf_map_update()`"，然后通过图表向下推进，最终结果可能是成功的更新或带有各种错误代码的失败。右上角的键提供了特定操作中可能涉及的锁的指示器。这旨在作为一个视觉提示，帮助理解地图竞争如何可能影响更新操作，尽管根据上述表格中描述的逻辑，地图类型和标志可能会影响那些锁上的实际竞争。例如，如果地图以类型`BPF_MAP_TYPE_LRU_PERCPU_HASH`和标志`BPF_F_NO_COMMON_LRU`创建，则所有地图属性都会是每个CPU独立的。

这段话详细描述了一个BPF（Berkeley Packet Filter）地图更新过程的可视化表示。它解释了如何从一个起点（即`bpf_map_update()`函数调用）开始，更新流程如何在图表中展开，以及可能的结果——成功或失败，并附带不同的错误码。同时，它强调了右上角的“键”（或图例）对于理解哪些锁可能会在特定操作中被涉及到的重要性。

此外，这段话还提到了地图类型和标志对锁竞争的影响，尤其是举例说明了当使用`BPF_MAP_TYPE_LRU_PERCPU_HASH`类型和`BPF_F_NO_COMMON_LRU`标志创建地图时，所有地图属性将按每个CPU分开存储，这会显著减少锁的竞争，因为每个CPU都有其自己的资源副本。
