SPDX 许可证标识符: 仅 GPL-2.0
版权所有 Red Hat

==============================================
BPF_MAP_TYPE_SOCKMAP 和 BPF_MAP_TYPE_SOCKHASH
==============================================

.. note::
   - ``BPF_MAP_TYPE_SOCKMAP`` 在内核版本 4.14 中引入
   - ``BPF_MAP_TYPE_SOCKHASH`` 在内核版本 4.18 中引入

``BPF_MAP_TYPE_SOCKMAP`` 和 ``BPF_MAP_TYPE_SOCKHASH`` 映射可用于在套接字间重定向 skbs（socket buffer）或根据 BPF（判决）程序的结果在套接字级别应用策略，这需要借助 BPF 辅助函数 ``bpf_sk_redirect_map()``、``bpf_sk_redirect_hash()``、``bpf_msg_redirect_map()`` 和 ``bpf_msg_redirect_hash()``。
``BPF_MAP_TYPE_SOCKMAP`` 由一个数组支持，该数组使用整数键作为索引来查找指向 ``struct sock`` 的引用。映射值是套接字描述符。同样地，``BPF_MAP_TYPE_SOCKHASH`` 是由哈希支持的 BPF 映射，它通过套接字描述符持有对套接字的引用。
.. note::
    值类型要么是 __u32 要么是 __u64；后者 (__u64) 用于支持将套接字 cookie 返回到用户空间。将映射持有的 ``struct sock *`` 返回给用户空间既不安全也没有用处
这些映射可能附带有 BPF 程序，特别是解析器程序和判决程序。解析器程序确定已解析多少数据，从而确定需要排队多少数据以得出判决。判决程序本质上是重定向程序，可以返回一个判决结果为 ``__SK_DROP``、``__SK_PASS`` 或者 ``__SK_REDIRECT``。
当一个套接字被插入到这些映射之一时，它的套接字回调会被替换，并且会有一个 ``struct sk_psock`` 附加到它上面。此外，这个 ``sk_psock`` 继承了附加到映射上的程序。
一个 sock 对象可以存在于多个映射中，但只能继承一个解析或判决程序。如果将一个 sock 对象添加到映射中会导致有多个解析程序，则更新将返回 EBUSY 错误。
可以附加到这些映射上的支持程序包括：

.. code-block:: c

    struct sk_psock_progs {
        struct bpf_prog *msg_parser;
        struct bpf_prog *stream_parser;
        struct bpf_prog *stream_verdict;
        struct bpf_prog *skb_verdict;
    };

.. note::
    用户不允许将 ``stream_verdict`` 和 ``skb_verdict`` 程序附加到同一个映射上
映射程序的附加类型为：

- ``msg_parser`` 程序 - ``BPF_SK_MSG_VERDICT``
- ``stream_parser`` 程序 - ``BPF_SK_SKB_STREAM_PARSER``
- ``stream_verdict`` 程序 - ``BPF_SK_SKB_STREAM_VERDICT``
``skb_verdict`` 程序 - ``BPF_SK_SKB_VERDICT``
与解析器和判决程序一起使用的额外辅助函数有：``bpf_msg_apply_bytes()`` 和 ``bpf_msg_cork_bytes()``。使用 ``bpf_msg_apply_bytes()``，BPF 程序可以告诉基础架构判决应该应用于多少字节。辅助函数 ``bpf_msg_cork_bytes()`` 处理另一种情况，即 BPF 程序在收到更多字节之前无法对消息做出判决，并且该程序不想转发数据包直到确认其为有效。
最后，辅助函数 ``bpf_msg_pull_data()`` 和 ``bpf_msg_push_data()`` 可供 ``BPF_PROG_TYPE_SK_MSG`` 类型的 BPF 程序使用以拉取数据并设置指针的起始和结束位置或向 ``struct sk_msg_buff *msg`` 添加元数据。
下面将详细描述所有这些辅助函数。

**使用**

**内核 BPF**

**bpf_msg_redirect_map()**
````c
long bpf_msg_redirect_map(struct sk_msg_buff *msg, struct bpf_map *map, u32 key, u64 flags)
````

此辅助函数用于实现套接字级别的策略程序。如果消息 ``msg`` 被允许通过（即，如果判决 BPF 程序返回 ``SK_PASS``），则将其重定向到由 ``map``（类型为 ``BPF_MAP_TYPE_SOCKMAP``）中索引为 ``key`` 的套接字。可以使用入站和出站接口进行重定向。“flags” 中的 ``BPF_F_INGRESS`` 值用于选择入站路径，否则选择出站路径。目前仅支持这个标志。
成功时返回 ``SK_PASS``，出错时返回 ``SK_DROP``。

**bpf_sk_redirect_map()**
````c
long bpf_sk_redirect_map(struct sk_buff *skb, struct bpf_map *map, u32 key, u64 flags)
````

将数据包重定向到由 ``map``（类型为 ``BPF_MAP_TYPE_SOCKMAP``）中索引为 ``key`` 的套接字。可以使用入站和出站接口进行重定向。“flags” 中的 ``BPF_F_INGRESS`` 值用于选择入站路径，否则选择出站路径。目前仅支持这个标志。
成功时返回 ``SK_PASS``，出错时返回 ``SK_DROP``。

**bpf_map_lookup_elem()**
````c
void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)
````

使用 ``bpf_map_lookup_elem()`` 辅助函数可以检索类型为 ``struct sock *`` 的套接字条目。

**bpf_sock_map_update()**
````c
long bpf_sock_map_update(struct bpf_sock_ops *skops, struct bpf_map *map, void *key, u64 flags)
````

向 ``map`` 中添加或更新引用套接字的条目。将 ``skops`` 作为与 ``key`` 关联的条目的新值。参数 ``flags`` 可以是以下之一：

- ``BPF_ANY``: 创建一个新元素或更新现有元素
```BPF_NOEXIST```: 如果该元素不存在，则创建一个新的元素  
```BPF_EXIST```: 更新一个已存在的元素  
如果`map`中包含BPF程序（解析器和判决），这些程序将被添加到的套接字继承。如果套接字已经关联了BPF程序，这会导致错误  
成功时返回0，失败时返回负数错误码  
`bpf_sock_hash_update()`  
^^^^^^^^^^^^^^^^^^^^^^  
.. code-block:: c  

    long bpf_sock_hash_update(struct bpf_sock_ops *skops, struct bpf_map *map, void *key, u64 flags)

向sockhash `map` 中添加或更新与套接字相关的条目。`skops` 作为与 `key` 关联的条目的新值使用  
`flags` 参数可以是以下之一：

- ```BPF_ANY```: 创建一个新的元素或更新一个已存在的元素  
- ```BPF_NOEXIST```: 只有当该元素不存在时才创建一个新的元素  
- ```BPF_EXIST```: 更新一个已存在的元素  
如果 `map` 中包含BPF程序（解析器和判决），这些程序将被添加到的套接字继承。如果套接字已经关联了BPF程序，这会导致错误  
成功时返回0，失败时返回负数错误码
这些是用于Linux eBPF（extended Berkeley Packet Filter）程序中的几个辅助函数的描述。下面是它们对应的中文翻译：

`bpf_msg_redirect_hash()`
^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_msg_redirect_hash(struct sk_msg_buff *msg, struct bpf_map *map, void *key, u64 flags)

此辅助函数用于实现套接字级别的策略程序。如果消息 `msg` 被允许通过（即，判决eBPF程序返回 `SK_PASS`），则使用哈希 `key` 将其重定向到由 `map`（类型为 `BPF_MAP_TYPE_SOCKHASH`）引用的套接字。可以使用入站和出站接口进行重定向。`flags` 中的 `BPF_F_INGRESS` 值用于选择入站路径；否则选择出站路径。这是目前唯一支持的标志。
成功时返回 `SK_PASS`，错误时返回 `SK_DROP`。

`bpf_sk_redirect_hash()`
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_sk_redirect_hash(struct sk_buff *skb, struct bpf_map *map, void *key, u64 flags)

此辅助函数用于实现sk_buff套接字级别的策略程序。如果sk_buff `skb` 被允许通过（即，判决eBPF程序返回 `SK_PASS`），则使用哈希 `key` 将其重定向到由 `map`（类型为 `BPF_MAP_TYPE_SOCKHASH`）引用的套接字。可以使用入站和出站接口进行重定向。`flags` 中的 `BPF_F_INGRESS` 值用于选择入站路径；否则选择出站路径。这是目前唯一支持的标志。
成功时返回 `SK_PASS`，错误时返回 `SK_DROP`。

`bpf_msg_apply_bytes()`
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_msg_apply_bytes(struct sk_msg_buff *msg, u32 bytes)

对于套接字策略，将eBPF程序的判决应用于消息 `msg` 的下一个 `bytes` 字节。例如，此辅助函数可用于以下情况：

- 单个 `sendmsg()` 或 `sendfile()` 系统调用包含多个逻辑消息，eBPF程序需要读取并为其应用判决。
- eBPF程序仅关心读取 `msg` 的前 `bytes` 字节。如果消息具有较大的负载，那么即使判决已经确定，重复设置和调用eBPF程序处理所有字节也会造成不必要的开销。
返回 0。

`bpf_msg_cork_bytes()`
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_msg_cork_bytes(struct sk_msg_buff *msg, u32 bytes)

对于套接字策略，阻止对消息 `msg` 执行eBPF程序的判决，直到累积了 `bytes` 字节。
当需要特定数量的字节才能分配判决时，即使数据跨越多个 `sendmsg()` 或 `sendfile()` 调用，也可以使用此功能。
返回 0。

`bpf_msg_pull_data()`
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_msg_pull_data(struct sk_msg_buff *msg, u32 start, u32 end, u64 flags)

对于套接字策略，从用户空间拉取非线性数据到 `msg` 并将指针 `msg->data` 和 `msg->data_end` 设置为 `msg` 中的 `start` 和 `end` 字节偏移量。
如果一个类型为 `BPF_PROG_TYPE_SK_MSG` 的程序在 `msg` 上运行，它只能解析 (`data`, `data_end`) 指针已经消费的数据。对于 `sendmsg()` 钩子而言，这很可能是第一个散列元素。但对于依赖于 MSG_SPLICE_PAGES（例如，`sendfile()`）的调用来说，这将是范围 (**0**, **0**)，因为数据与用户空间共享，并且默认的目标是避免允许用户空间在 BPF 判决正在决定时（或之后）修改数据。此辅助函数可用于拉取数据，并将起始和结束指针设置为给定值。如果需要，数据会被复制（即，如果数据不是线性的，并且起始和结束指针不指向同一块）。
调用此辅助函数可能会改变底层的数据包缓冲区。因此，在加载时，所有先前由验证器完成的指针检查都会失效并必须重新执行，如果该辅助函数与直接数据包访问结合使用的话。
`flags` 中的所有值都保留用于将来使用，并且必须保持为零。
成功返回 0，失败返回负错误码。
bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: c

    void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

在 sockmap 或 sockhash 映射中查找套接字条目。
返回与 `key` 关联的套接字条目，如果没有找到条目则返回 NULL。
bpf_map_update_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_map_update_elem(struct bpf_map *map, const void *key, const void *value, u64 flags)

在 sockmap 或 sockhash 中添加或更新一个套接字条目。
`flags` 参数可以是以下之一：

- BPF_ANY: 创建一个新的元素或更新已存在的元素
BPF_NOEXIST: 如果元素不存在，则创建新元素  
BPF_EXIST: 更新已存在的元素  
成功时返回0，失败时返回负数错误  
bpf_map_delete_elem()  
^^^^^^^^^^^^^^^^^^^^^^  
.. code-block:: c  

    long bpf_map_delete_elem(struct bpf_map *map, const void *key)

从sockmap或sockhash中删除一个socket条目  
成功时返回0，失败时返回负数错误  
用户空间  
----------
bpf_map_update_elem()  
^^^^^^^^^^^^^^^^^^^^^  
.. code-block:: c  

    int bpf_map_update_elem(int fd, const void *key, const void *value, __u64 flags)

可以使用`bpf_map_update_elem()`函数添加或更新sockmap条目。`key`参数是sockmap数组的索引值，而`value`参数是该socket的文件描述符（FD）值。  
在底层，sockmap更新函数使用socket的文件描述符值来检索关联的socket及其附加的psock结构。  
flags参数可以是以下之一：

- BPF_ANY: 创建新元素或更新已存在的元素
- BPF_NOEXIST: 只有当元素不存在时才创建新元素
- BPF_EXIST: 更新已存在的元素
使用`bpf_map_lookup_elem()`函数可以检索Sockmap条目
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_lookup_elem(int fd, const void *key, void *value)

通过`bpf_map_lookup_elem()`函数可以获取Sockmap条目。
.. note::
    返回的条目是一个socket cookie，而不是socket本身。

`bpf_map_delete_elem()`
^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    int bpf_map_delete_elem(int fd, const void *key)

Sockmap条目可以通过`bpf_map_delete_elem()`函数进行删除。
在成功时返回0，在失败时返回负数错误码。

示例
====
内核BPF
-------
使用Sockmap API的多个示例可以在以下文件中找到：

- `tools/testing/selftests/bpf/progs/test_sockmap_kern.h`_
- `tools/testing/selftests/bpf/progs/sockmap_parse_prog.c`_
- `tools/testing/selftests/bpf/progs/sockmap_verdict_prog.c`_
- `tools/testing/selftests/bpf/progs/test_sockmap_listen.c`_
- `tools/testing/selftests/bpf/progs/test_sockmap_update.c`_

下面的代码片段展示了如何声明一个Sockmap：
.. code-block:: c

    struct {
        __uint(type, BPF_MAP_TYPE_SOCKMAP);
        __uint(max_entries, 1);
        __type(key, __u32);
        __type(value, __u64);
    } sock_map_rx SEC(".maps");

下面的代码片段展示了一个样本解析器程序：
.. code-block:: c

    SEC("sk_skb/stream_parser")
    int bpf_prog_parser(struct __sk_buff *skb)
    {
        return skb->len;
    }

下面的代码片段展示了一个简单的判决程序，该程序与Sockmap交互以根据本地端口重定向流量到另一个socket：
.. code-block:: c

    SEC("sk_skb/stream_verdict")
    int bpf_prog_verdict(struct __sk_buff *skb)
    {
        __u32 lport = skb->local_port;
        __u32 idx = 0;

        if (lport == 10000)
            return bpf_sk_redirect_map(skb, &sock_map_rx, idx, 0);

        return SK_PASS;
    }

下面的代码片段展示了如何声明一个Sockhash map：
.. code-block:: c

    struct socket_key {
        __u32 src_ip;
        __u32 dst_ip;
        __u32 src_port;
        __u32 dst_port;
    };

    struct {
        __uint(type, BPF_MAP_TYPE_SOCKHASH);
        __uint(max_entries, 1);
        __type(key, struct socket_key);
        __type(value, __u64);
    } sock_hash_rx SEC(".maps");

下面的代码片段展示了一个简单的判决程序，该程序与Sockhash交互以根据skb参数的一些哈希值重定向流量到另一个socket：
.. code-block:: c

    static inline
    void extract_socket_key(struct __sk_buff *skb, struct socket_key *key)
    {
        key->src_ip = skb->remote_ip4;
        key->dst_ip = skb->local_ip4;
        key->src_port = skb->remote_port >> 16;
        key->dst_port = (bpf_htonl(skb->local_port)) >> 16;
    }

    SEC("sk_skb/stream_verdict")
    int bpf_prog_verdict(struct __sk_buff *skb)
    {
        struct socket_key key;

        extract_socket_key(skb, &key);

        return bpf_sk_redirect_hash(skb, &sock_hash_rx, &key, 0);
    }

用户空间
-------
使用Sockmap API的多个示例可以在以下文件中找到：

- `tools/testing/selftests/bpf/prog_tests/sockmap_basic.c`_
- `tools/testing/selftests/bpf/test_sockmap.c`_
- `tools/testing/selftests/bpf/test_maps.c`_

下面的代码示例展示了如何创建一个Sockmap、附加一个解析器和判决程序以及添加一个socket条目。
```c
int create_sample_sockmap(int sock, int parse_prog_fd, int verdict_prog_fd)
{
    int index = 0;
    int map, err;

    // 创建一个类型为BPF_MAP_TYPE_SOCKMAP的BPF映射
    map = bpf_map_create(BPF_MAP_TYPE_SOCKMAP, NULL, sizeof(int), sizeof(int), 1, NULL);
    if (map < 0) {
        fprintf(stderr, "创建sockmap失败: %s\n", strerror(errno));
        return -1;
    }

    // 将解析程序附加到BPF映射
    err = bpf_prog_attach(parse_prog_fd, map, BPF_SK_SKB_STREAM_PARSER, 0);
    if (err){
        fprintf(stderr, "将解析程序附加到映射失败: %s\n", strerror(errno));
        goto out;
    }

    // 将判决程序附加到BPF映射
    err = bpf_prog_attach(verdict_prog_fd, map, BPF_SK_SKB_STREAM_VERDICT, 0);
    if (err){
        fprintf(stderr, "将判决程序附加到映射失败: %s\n", strerror(errno));
        goto out;
    }

    // 更新BPF映射中的元素
    err = bpf_map_update_elem(map, &index, &sock, BPF_NOEXIST);
    if (err) {
        fprintf(stderr, "更新sockmap失败: %s\n", strerror(errno));
        goto out;
    }

out:
    close(map);
    return err;
}
```

**参考资料**

- [https://github.com/jrfastab/linux-kernel-xdp/commit/c89fd73cb9d2d7f3c716c3e00836f07b1aeb261f](https://github.com/jrfastab/linux-kernel-xdp/commit/c89fd73cb9d2d7f3c716c3e00836f07b1aeb261f)
- [https://lwn.net/Articles/731133/](https://lwn.net/Articles/731133/)
- [http://vger.kernel.org/lpc_net2018_talks/ktls_bpf_paper.pdf](http://vger.kernel.org/lpc_net2018_talks/ktls_bpf_paper.pdf)
- [https://lwn.net/Articles/748628/](https://lwn.net/Articles/748628/)
- [https://lore.kernel.org/bpf/20200218171023.844439-7-jakub@cloudflare.com/](https://lore.kernel.org/bpf/20200218171023.844439-7-jakub@cloudflare.com/)

- [test_sockmap_kern.h](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/progs/test_sockmap_kern.h)
- [sockmap_parse_prog.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/progs/sockmap_parse_prog.c)
- [sockmap_verdict_prog.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/progs/sockmap_verdict_prog.c)
- [sockmap_basic.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/prog_tests/sockmap_basic.c)
- [test_sockmap.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/test_sockmap.c)
- [test_maps.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/test_maps.c)
- [test_sockmap_listen.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/progs/test_sockmap_listen.c)
- [test_sockmap_update.c](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/testing/selftests/bpf/progs/test_sockmap_update.c)
```
