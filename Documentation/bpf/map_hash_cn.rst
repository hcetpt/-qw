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

可以通过 ``bpf_map_update_elem()`` 辅助函数添加或更新哈希表条目。此辅助函数以原子方式替换现有元素。``flags`` 参数可用于控制更新行为：

- ``BPF_ANY`` 将创建新元素或更新现有元素
- ``BPF_NOEXIST`` 只有当不存在时才会创建新元素
- ``BPF_EXIST`` 将更新现有元素

``bpf_map_update_elem()`` 成功时返回 0，失败时返回负错误码
bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以通过 ``bpf_map_lookup_elem()`` 辅助函数检索哈希表条目。此辅助函数返回与 ``key`` 关联的值的指针，如果未找到条目则返回 ``NULL``
bpf_map_delete_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_map_delete_elem(struct bpf_map *map, const void *key)

可以通过 ``bpf_map_delete_elem()`` 辅助函数删除哈希表条目。此辅助函数成功时返回 0，失败时返回负错误码
每 CPU 哈希表
--------------

对于 ``BPF_MAP_TYPE_PERCPU_HASH`` 和 ``BPF_MAP_TYPE_LRU_PERCPU_HASH``
``bpf_map_update_elem()`` 和 ``bpf_map_lookup_elem()`` 辅助函数会自动访问当前 CPU 的哈希槽
### 翻译成中文:

`bpf_map_lookup_percpu_elem()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   void *bpf_map_lookup_percpu_elem(struct bpf_map *map, const void *key, u32 cpu)

`bpf_map_lookup_percpu_elem()` 辅助函数可以用于在特定CPU的哈希槽中查找值。返回与 `key` 关联的值，如果未找到条目或 `cpu` 无效则返回 `NULL`。

#### 并发
--------------

存储在 `BPF_MAP_TYPE_HASH` 中的值可以被运行在不同CPU上的程序并发访问。从内核版本5.1开始，BPF基础设施提供了 `struct bpf_spin_lock` 来同步访问。参见 `tools/testing/selftests/bpf/progs/test_spin_lock.c`

#### 用户空间
-------------

`bpf_map_get_next_key()`
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_get_next_key(int fd, const void *cur_key, void *next_key)

在用户空间中，可以通过 libbpf 的 `bpf_map_get_next_key()` 函数遍历哈希中的键。首次调用 `bpf_map_get_next_key()` 时，将 `cur_key` 设置为 `NULL` 来获取第一个键。随后的调用将获取当前键之后的下一个键。`bpf_map_get_next_key()` 成功时返回 0，如果 `cur_key` 是哈希中的最后一个键，则返回 -ENOENT；在失败的情况下返回负数错误。
需要注意的是，如果 `cur_key` 被删除，那么 `bpf_map_get_next_key()` 将返回哈希表中的 **第一个** 键，这是不期望的行为。如果 `cur_key` 删除和 `bpf_map_get_next_key()` 调用之间有交错操作，建议使用批量查找。

#### 示例
========

请参阅 `tools/testing/selftests/bpf` 目录以获取功能示例。以下代码片段展示了API的使用方法。
这个例子展示了如何声明一个具有结构体键和结构体值的 LRU 哈希。
.. code-block:: c

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

.. code-block:: c

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

在用户空间中遍历上面声明的映射中的元素：

.. code-block:: c

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

                    // 使用 key 和 value

                    cur_key = &next_key;
            }
    }

#### 内部实现
=============

本节针对Linux开发者，并描述了不属于稳定ABI的映射实现方面的内容。以下细节可能会在未来版本的内核中发生变化。
`BPF_MAP_TYPE_LRU_HASH` 及其变种
--------------------------------------

当LRU映射的容量达到上限时，更新元素可能会触发驱逐行为。为了强制执行LRU属性，更新算法尝试了一系列对其他CPU影响递增的操作步骤：

- 尝试使用CPU本地状态来批处理操作
- 尝试从全局列表中获取空闲节点
- 尝试从全局列表中拉取任何节点并将其从哈希映射中移除
- 尝试从任何CPU的列表中拉取任何节点并将其从哈希映射中移除

以下图解描述了这些步骤。参见提交3a08c2fd7634 ("bpf: LRU List") 对应操作的完整解释：

.. kernel-figure::  map_lru_hash_update.dot
   :alt:    图解概述了在映射更新期间LRU驱逐所采取的步骤
LRU哈希映射更新期间的驱逐行为对于 `BPF_MAP_TYPE_LRU_HASH` 及其变种。参见 dot 文件源码中的内核函数名称代码参考。
地图更新从右上角的椭圆形开始，标注为"启动`bpf_map_update()`"，然后顺着图示向下推进，最终结果可能是成功更新或带有不同错误码的失败。右上角的图例提供了特定操作中可能涉及哪些锁的指示器。这旨在作为一个视觉提示，帮助理解地图竞争如何可能影响更新操作；不过，地图类型和标志可能会根据上述表格中描述的逻辑影响这些锁的实际竞争情况。例如，如果地图以类型`BPF_MAP_TYPE_LRU_PERCPU_HASH`和标志`BPF_F_NO_COMMON_LRU`创建，则所有地图属性都将按每核（per-CPU）分配。
