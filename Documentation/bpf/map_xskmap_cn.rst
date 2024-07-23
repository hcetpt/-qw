SPDX 许可证标识符：仅限 GPL-2.0
版权 (C) 2022 红帽公司
======================
BPF_MAP_TYPE_XSKMAP
======================

.. note::
   - ``BPF_MAP_TYPE_XSKMAP`` 在内核版本 4.18 中引入。

``BPF_MAP_TYPE_XSKMAP`` 被用作 XDP BPF 辅助函数调用 ``bpf_redirect_map()`` 和 ``XDP_REDIRECT`` 动作的后端映射，类似于 'devmap' 和 'cpumap'。这种映射类型将原始 XDP 帧重定向到 `AF_XDP`_ 套接字（XSK），这是内核中一种新的地址族类型，允许从驱动程序到用户空间重定向帧而无需遍历整个网络堆栈。一个 AF_XDP 套接字绑定到单个 netdev 队列。下面展示了 XSK 到队列的映射：

.. code-block:: none

    +---------------------------------------------------+
    |     xsk A      |     xsk B       |      xsk C     |<---+ 用户空间
    =========================================================|==========
    |    Queue 0     |     Queue 1     |     Queue 2    |    |  内核
    +---------------------------------------------------+    |
    |                  Netdev eth0                      |    |
    +---------------------------------------------------+    |
    |                            +=============+        |    |
    |                            | key |  xsk  |        |    |
    |  +---------+               +=============+        |    |
    |  |         |               |  0  | xsk A |        |    |
    |  |         |               +-------------+        |    |
    |  |         |               |  1  | xsk B |        |    |
    |  | BPF     |-- redirect -->+-------------+-------------+
    |  | prog    |               |  2  | xsk C |        |
    |  |         |               +-------------+        |
    |  |         |                                      |
    |  |         |                                      |
    |  +---------+                                      |
    |                                                   |
    +---------------------------------------------------+

.. note::
    绑定到特定 <netdev/queue_id> 的 AF_XDP 套接字*只*接受来自该 <netdev/queue_id> 的 XDP 帧。如果 XDP 程序尝试从与套接字绑定不同的 <netdev/queue_id> 重定向，帧将不会在该套接字上接收。
通常每个 netdev 创建一个 XSKMAP。此映射包含 XSK 文件描述符（FD）的数组。数组元素的数量通常使用 ``max_entries`` 映射参数设置或调整。对于 AF_XDP，``max_entries`` 等于 netdev 支持的队列数量。
.. note::
    映射键和映射值大小都必须为 4 字节。
使用
=====

内核 BPF
----------
bpf_redirect_map()
^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags)

将数据包重定向到由 ``map`` 在 ``key`` 指定的索引处引用的端点。对于 ``BPF_MAP_TYPE_XSKMAP``，此映射包含对绑定到 netdev 队列的 XSK FD 的引用。
.. note::
    如果在某个索引处映射为空，则丢弃数据包。这意味着至少需要有一个加载了 XDP 程序且在 XSKMAP 中至少有一个 XSK 才能通过套接字将任何流量传送到用户空间。
bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用 ``bpf_map_lookup_elem()`` 辅助函数检索类型为 ``struct xdp_sock *`` 的 XSK 入口引用。
用户空间
----------
.. note::
    只能在用户空间更新或删除 XSK 入口，而不能在 BPF 程序中进行。尝试从内核 BPF 程序调用这些函数将导致程序加载失败并出现验证器警告。
`bpf_map_update_elem()`函数可以用来添加或更新XSK条目。在C语言中，其定义如下：

```c
int bpf_map_update_elem(int fd, const void *key, const void *value, __u64 flags);
```

使用`bpf_map_update_elem()`助手时，`key`参数等于XSK所连接队列的queue_id。而`value`参数则是该socket的FD值。在内部，XSKMAP更新函数利用XSK的FD值来获取相关的`struct xdp_sock`实例。

`flags`参数可以是以下之一：

- BPF_ANY: 创建新元素或更新现有元素
- BPF_NOEXIST: 只有当元素不存在时才创建新元素
- BPF_EXIST: 更新现有元素

`bpf_map_lookup_elem()`函数用于查找元素：

```c
int bpf_map_lookup_elem(int fd, const void *key, void *value);
```

此函数返回`struct xdp_sock *`指针，或者在失败情况下返回负数错误代码。

`bpf_map_delete_elem()`函数用于删除XSK条目：

```c
int bpf_map_delete_elem(int fd, const void *key);
```

使用`bpf_map_delete_elem()`助手成功删除时将返回0，否则返回负数错误代码。

**注意：** 当`libxdp`删除一个XSK时，它也会从XSKMAP中移除与之关联的socket条目。

**示例**

**内核**

下面的代码片段展示了如何声明一个名为`xsks_map`的`BPF_MAP_TYPE_XSKMAP`类型，并展示如何将数据包重定向到XSK：

```c
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
```

**用户空间**

下面的代码片段展示了如何用XSK条目更新XSKMAP：
```c
// 假设我们已经获得了需要的queue_id和socket_fd
__u32 queue_id = ...; // 需要填充的queue_id
__u32 socket_fd = ...; // 需要填充的socket_fd

int ret = bpf_map_update_elem(xdp_sock_map_fd, &queue_id, &socket_fd, BPF_ANY);
if (ret < 0) {
    // 处理错误
}
``` 

其中`xdp_sock_map_fd`是XSKMAP的文件描述符。
```c
// 更新xsks_map的函数
int update_xsks_map(struct bpf_map *xsks_map, int queue_id, int xsk_fd)
{
    int ret;

    // 使用BPF map的文件描述符来更新元素
    ret = bpf_map_update_elem(bpf_map__fd(xsks_map), &queue_id, &xsk_fd, 0);
    if (ret < 0) {
        // 如果失败，打印错误信息到标准错误输出
        fprintf(stderr, "Failed to update xsks_map: %s\n", strerror(errno));
    }

    return ret;
}
```

关于如何创建AF_XDP套接字的例子，请参阅`bpf-examples`_目录下的`AF_XDP-example`和`AF_XDP-forwarding`程序，在`libxdp`_仓库中。

对于AF_XDP接口的详细解释，请参考：

- `libxdp-readme`_
- `AF_XDP`_ 内核文档

.. 注意::
   对于使用XSKMAPs和AF_XDP最全面的资源是`libxdp`_

.. _libxdp: https://github.com/xdp-project/xdp-tools/tree/master/lib/libxdp
.. _AF_XDP: https://www.kernel.org/doc/html/latest/networking/af_xdp.html
.. _bpf-examples: https://github.com/xdp-project/bpf-examples
.. _libxdp-readme: https://github.com/xdp-project/xdp-tools/tree/master/lib/libxdp#using-af_xdp-sockets

这段代码展示了如何更新一个BPF map，将队列ID和XSK文件描述符关联起来。同时，文档注释提供了创建AF_XDP套接字的相关示例和资源链接，以及AF_XDP接口的详细说明，强调了`libxdp`作为使用XSKMAPs和AF_XDP的最全面资源的地位。
