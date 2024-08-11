SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc.
===================
BPF_MAP_TYPE_XSKMAP
===================

.. note::
   - `BPF_MAP_TYPE_XSKMAP` 在内核版本 4.18 中被引入。

`BPF_MAP_TYPE_XSKMAP` 被用作 XDP BPF 辅助调用 `bpf_redirect_map()` 和 `XDP_REDIRECT` 动作的后端映射，类似于 'devmap' 和 'cpumap'。这种映射类型将原始 XDP 帧重定向到 `AF_XDP`_ 套接字（XSKs），这是内核中的一种新型地址族，允许从驱动程序到用户空间重定向帧，而无需遍历整个网络栈。一个 AF_XDP 套接字绑定到单一的网卡设备队列。下面展示了 XSKs 到队列的映射：

.. code-block:: none

    +---------------------------------------------------+
    |     xsk A      |     xsk B       |      xsk C     |<---+ 用户空间
    =========================================================|==========
    |    队列 0     |     队列 1     |     队列 2    |    |  内核
    +---------------------------------------------------+    |
    |                  网卡 eth0                      |    |
    +---------------------------------------------------+    |
    |                            +=============+        |    |
    |                            | key |  xsk  |        |    |
    |  +---------+               +=============+        |    |
    |  |         |               |  0  | xsk A |        |    |
    |  |         |               +-------------+        |    |
    |  |         |               |  1  | xsk B |        |    |
    |  | BPF     |-- 重定向 -->+-------------+-------------+
    |  | 程序    |               |  2  | xsk C |        |
    |  |         |               +-------------+        |
    |  |         |                                      |
    |  |         |                                      |
    |  +---------+                                      |
    |                                                   |
    +---------------------------------------------------+

.. note::
    绑定到特定 `<网卡/队列_id>` 的 AF_XDP 套接字 *仅* 接收来自该 `<网卡/队列_id>` 的 XDP 帧。如果 XDP 程序尝试从不同于套接字绑定的 `<网卡/队列_id>` 重定向，则帧不会在套接字上收到。
通常为每个网卡创建一个 XSKMAP。此映射包含一个 XSK 文件描述符（FD）数组。数组元素的数量通常使用 `max_entries` 映射参数设置或调整。对于 AF_XDP，`max_entries` 等于网卡支持的队列数量。
.. note::
    映射键和映射值大小都必须是 4 字节。

使用
=====

内核 BPF
----------
bpf_redirect_map()
^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags)

将包重定向到由 `map` 在索引 `key` 处引用的终端
对于 `BPF_MAP_TYPE_XSKMAP`，此映射包含指向绑定到网卡队列的 XSK FD 的引用
.. note::
    如果在某个索引处映射为空，则丢弃该包。这意味着必须加载至少包含一个 XSK 的 XDP 程序到 XSKMAP 中才能通过套接字将任何流量发送到用户空间。
bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 `bpf_map_lookup_elem()` 辅助函数检索类型为 `struct xdp_sock *` 的 XSK 条目引用。

用户空间
----------
.. note::
    XSK 条目只能从用户空间更新/删除，不能从 BPF 程序中操作。尝试从内核 BPF 程序调用这些函数会导致程序加载失败，并出现验证器警告。
`bpf_map_update_elem()`
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_update_elem(int fd, const void *key, const void *value, __u64 flags)

XSK条目可以使用`bpf_map_update_elem()`辅助函数进行添加或更新。参数`key`等于XSK所绑定队列的队列ID。参数`value`是该套接字的文件描述符（FD）值。在内部，XSKMAP更新函数利用XSK的FD值来获取相关的`struct xdp_sock`实例。
参数`flags`可以为以下之一：

- BPF_ANY: 创建一个新元素或更新现有元素
- BPF_NOEXIST: 只有当元素不存在时创建新元素
- BPF_EXIST: 更新现有元素

`bpf_map_lookup_elem()`
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_lookup_elem(int fd, const void *key, void *value)

返回`struct xdp_sock *`或在失败情况下返回负数错误代码

`bpf_map_delete_elem()`
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_delete_elem(int fd, const void *key)

XSK条目可以通过`bpf_map_delete_elem()`辅助函数删除。此辅助函数在成功时返回0，在失败时返回负数错误代码。
.. note::
    当`libxdp`_删除一个XSK时，也会从XSKMAP中移除关联的套接字条目。

示例
========

内核
------

下面的代码片段展示了如何声明一个名为`xsks_map`的`BPF_MAP_TYPE_XSKMAP`类型，并展示如何将数据包重定向到XSK
.. code-block:: c

    struct {
        __uint(type, BPF_MAP_TYPE_XSKMAP);
        __type(key, __u32);
        __type(value, __u32);
        __uint(max_entries, 64);
    } xsks_map SEC(".maps");


    SEC("xdp")
    int xsk_redir_prog(struct xdp_md *ctx)
    {
        __u32 index = ctx->rx_queue_index;

        if (bpf_map_lookup_elem(&xsks_map, &index))
            return bpf_redirect_map(&xsks_map, index, 0);
        return XDP_PASS;
    }

用户空间
----------

下面的代码片段展示了如何通过一个XSK条目更新XSKMAP。
```c
int update_xsks_map(struct bpf_map *xsks_map, int queue_id, int xsk_fd)
{
    int ret;

    ret = bpf_map_update_elem(bpf_map__fd(xsks_map), &queue_id, &xsk_fd, 0);
    if (ret < 0)
        fprintf(stderr, "更新 xsks_map 失败: %s\n", strerror(errno));

    return ret;
}
```

要了解如何创建 AF_XDP 套接字，请参阅 `bpf-examples`_ 目录中 `libxdp`_ 仓库的 AF_XDP-example 和 AF_XDP-forwarding 程序。

对于 AF_XDP 接口的详细解释，请参考：

- `libxdp-readme`_
- `AF_XDP`_ 内核文档

.. note::
   使用 XSKMAPs 和 AF_XDP 的最全面资源是 `libxdp`_。

.. _libxdp: https://github.com/xdp-project/xdp-tools/tree/master/lib/libxdp
.. _AF_XDP: https://www.kernel.org/doc/html/latest/networking/af_xdp.html
.. _bpf-examples: https://github.com/xdp-project/bpf-examples
.. _libxdp-readme: https://github.com/xdp-project/xdp-tools/tree/master/lib/libxdp#using-af_xdp-sockets
```
