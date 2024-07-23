SPDX 许可证标识符：仅限 GPL-2.0
版权 (C) 2022，红帽公司
=================================================
BPF_MAP_TYPE_DEVMAP 和 BPF_MAP_TYPE_DEVMAP_HASH
=================================================

.. 注意::
   - ``BPF_MAP_TYPE_DEVMAP`` 在内核版本 4.14 中引入
   - ``BPF_MAP_TYPE_DEVMAP_HASH`` 在内核版本 5.4 中引入

``BPF_MAP_TYPE_DEVMAP`` 和 ``BPF_MAP_TYPE_DEVMAP_HASH`` 主要用于作为 XDP BPF 辅助调用 ``bpf_redirect_map()`` 的后端映射。
``BPF_MAP_TYPE_DEVMAP`` 由一个数组支持，使用键作为索引来查找对网络设备的引用。而 ``BPF_MAP_TYPE_DEVMAP_HASH`` 则由一个哈希表支持，使用键来查找对网络设备的引用。
用户可以提供 <``key`` / ``ifindex``> 或 <``key`` / ``struct bpf_devmap_val``> 对来更新地图中的新网络设备。
.. 注意::
    - 哈希图的键不必是 ``ifindex``
- 虽然 ``BPF_MAP_TYPE_DEVMAP_HASH`` 允许密集地打包网络设备，
      这在执行查找时会带来对键的哈希成本。
设置和数据包入列/发送代码在这两种类型的 devmap 之间共享；只有查找和插入不同。

使用
=====
内核 BPF
----------
bpf_redirect_map()
^^^^^^^^^^^^^^^^^^
.. C代码块::

    long bpf_redirect_map(struct bpf_map *map, u32 key, u64 flags)

将数据包重定向到由 ``map`` 在 ``key`` 索引处引用的端点。
对于 ``BPF_MAP_TYPE_DEVMAP`` 和 ``BPF_MAP_TYPE_DEVMAP_HASH``，此映射包含
对网络设备（用于通过其他端口转发数据包）的引用。
*flags* 的最低两位用于作为映射查找失败时的返回码。这是为了让返回值可以是其中一个 XDP 程序返回
码，直到 ``XDP_TX``，由调用者选择。 ``flags`` 的更高位可以设置为下面定义的 ``BPF_F_BROADCAST`` 或 ``BPF_F_EXCLUDE_INGRESS``。
使用`BPF_F_BROADCAST`，数据包将广播到映射中的所有接口；使用`BPF_F_EXCLUDE_INGRESS`，入站接口将从广播中排除。

.. note::
    - 如果设置了`BPF_F_BROADCAST`，则忽略键。
    - 广播功能也可用于实现多播转发：只需创建多个DEVMAP，每个都对应一个单一的多播组。
此辅助函数在成功时返回`XDP_REDIRECT`，或如果映射查找失败，则返回`flags`参数的两个最低位的值。

关于重定向的更多信息可以在 :doc:`redirect` 中找到。

bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

   void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

可以使用`bpf_map_lookup_elem()`辅助函数检索网络设备条目。

用户空间
----------
.. note::
    DEVMAP条目只能从用户空间更新/删除，而不能从eBPF程序中进行。尝试从内核eBPF程序调用这些函数将导致程序加载失败并出现验证器警告。

bpf_map_update_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

   int bpf_map_update_elem(int fd, const void *key, const void *value, __u64 flags);

可以使用`bpf_map_update_elem()`辅助函数添加或更新网络设备条目。此辅助函数原子地替换现有元素。`value`参数可以是`struct bpf_devmap_val`或简单的`int ifindex`以保持向后兼容性。

.. code-block:: c

    struct bpf_devmap_val {
        __u32 ifindex;   /* 设备索引 */
        union {
            int   fd;  /* 在映射写入时的程序文件描述符 */
            __u32 id;  /* 在映射读取时的程序ID */
        } bpf_prog;
    };

`flags`参数可以是以下之一：
  - `BPF_ANY`：创建新元素或更新现有元素
- `BPF_NOEXIST`：仅在不存在的情况下创建新元素
- `BPF_EXIST`：更新现有元素
DEVMAPs可以通过向`struct bpf_devmap_val`中添加`bpf_prog.fd`将程序与设备条目关联。程序在`XDP_REDIRECT`之后运行，并且可以访问Rx设备和Tx设备。与`fd`关联的程序必须是XDP类型，预期的附加类型为`xdp_devmap`。

当程序与设备索引关联时，在缓冲区添加到per-CPU队列之前，程序将在`XDP_REDIRECT`上运行。如何附加/使用xdp_devmap程序的例子可以在内核自测中找到：

- `tools/testing/selftests/bpf/prog_tests/xdp_devmap_attach.c`
- `tools/testing/selftests/bpf/progs/test_xdp_with_devmap_helpers.c`

bpf_map_lookup_elem()
---------------------
```c
int bpf_map_lookup_elem(int fd, const void *key, void *value);
```
网络设备条目可以使用`bpf_map_lookup_elem()`助手检索。

bpf_map_delete_elem()
---------------------
```c
int bpf_map_delete_elem(int fd, const void *key);
```
网络设备条目可以使用`bpf_map_delete_elem()`助手删除。此助手在成功时返回0，失败时返回负错误代码。

例子
====
内核BPF
-------

下面的代码片段展示了如何声明一个名为`tx_port`的`BPF_MAP_TYPE_DEVMAP`
```c
struct {
    __uint(type, BPF_MAP_TYPE_DEVMAP);
    __type(key, __u32);
    __type(value, __u32);
    __uint(max_entries, 256);
} tx_port SEC(".maps");
```

下面的代码片段展示了如何声明一个名为`forward_map`的`BPF_MAP_TYPE_DEVMAP_HASH`
```c
struct {
    __uint(type, BPF_MAP_TYPE_DEVMAP_HASH);
    __type(key, __u32);
    __type(value, struct bpf_devmap_val);
    __uint(max_entries, 32);
} forward_map SEC(".maps");
```
**注释：**

上面DEVMAP中的值类型是`struct bpf_devmap_val`

下面的代码片段展示了一个简单的xdp_redirect_map程序。这个程序将与基于入口ifindexes填充devmap`forward_map`的用户空间程序一起工作。BPF程序（如下）正在使用入口`ifindex`作为`key`重定向数据包。
```c
SEC("xdp")
int xdp_redirect_map_func(struct xdp_md *ctx)
{
    int index = ctx->ingress_ifindex;

    return bpf_redirect_map(&forward_map, index, 0);
}
```

下面的代码片段展示了一个BPF程序，该程序正将数据包广播到`tx_port` devmap中的所有接口
```c
SEC("xdp")
int xdp_redirect_map_func(struct xdp_md *ctx)
{
    return bpf_redirect_map(&tx_port, 0, BPF_F_BROADCAST | BPF_F_EXCLUDE_INGRESS);
}
```

用户空间
--------

下面的代码片段展示了如何更新名为`tx_port`的devmap
```c
int update_devmap(int ifindex, int redirect_ifindex)
{
    int ret;

    ret = bpf_map_update_elem(bpf_map__fd(tx_port), &ifindex, &redirect_ifindex, 0);
    if (ret < 0) {
        fprintf(stderr, "Failed to update devmap_ value: %s\n",
            strerror(errno));
    }

    return ret;
}
```

下面的代码片段展示了如何更新名为`forward_map`的hash_devmap
```c
int update_devmap(int ifindex, int redirect_ifindex)
{
    struct bpf_devmap_val devmap_val = { .ifindex = redirect_ifindex };
    int ret;

    ret = bpf_map_update_elem(bpf_map__fd(forward_map), &ifindex, &devmap_val, 0);
    if (ret < 0) {
        fprintf(stderr, "Failed to update devmap_ value: %s\n",
            strerror(errno));
    }
    return ret;
}
```

参考
====
- https://lwn.net/Articles/728146/
- https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/commit/?id=6f9d451ab1a33728adb72d7ff66a7b374d665176
- https://elixir.bootlin.com/linux/latest/source/net/core/filter.c#L4106
