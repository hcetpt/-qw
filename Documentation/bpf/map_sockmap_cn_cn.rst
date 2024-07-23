SPDX许可证标识符：仅GPL-2.0
版权所有Red Hat

==============================================
BPF_MAP_TYPE_SOCKMAP与BPF_MAP_TYPE_SOCKHASH
==============================================

.. 注意::
   - ``BPF_MAP_TYPE_SOCKMAP``在内核版本4.14中引入
   - ``BPF_MAP_TYPE_SOCKHASH``在内核版本4.18中引入

``BPF_MAP_TYPE_SOCKMAP``和``BPF_MAP_TYPE_SOCKHASH``映射能够用于在套接字之间重定向skb或依据BPF（判决）程序的结果在套接字层面应用策略，这得益于BPF辅助函数``bpf_sk_redirect_map()``、``bpf_sk_redirect_hash()``、``bpf_msg_redirect_map()``和``bpf_msg_redirect_hash()``。
``BPF_MAP_TYPE_SOCKMAP``由数组支持，使用整数键作为索引查找对``struct sock``的引用。映射值是套接字描述符。同样地，``BPF_MAP_TYPE_SOCKHASH``是一个由哈希支持的BPF映射，通过它们的套接字描述符持有对套接字的引用。
.. 注意::
    值类型要么是__u32要么是__u64；后者（__u64）是为了支持向用户空间返回套接字cookie。将映射持有的``struct sock *``返回到用户空间既不安全也无用。

这些映射可能有附加的BPF程序，具体而言是一个解析程序和一个判决程序。解析程序确定已解析了多少数据，从而需要多少数据排队以便做出判决。判决程序本质上是重定向程序，可以返回一个判决结果，即``__SK_DROP``、``__SK_PASS``或者``__SK_REDIRECT``。
当一个套接字被插入到这些映射中的一个时，其套接字回调会被替换，并且一个``struct sk_psock``被附加到它上面。此外，这个``sk_psock``继承了附加到映射上的程序。
一个sock对象可能存在于多个映射中，但只能继承单一的解析或判决程序。如果将一个sock对象添加到映射中会导致有多个解析程序，更新将返回一个EBUSY错误。
可以附加到这些映射的受支持程序如下：

.. 代码块:: c

    struct sk_psock_progs {
        struct bpf_prog *msg_parser;
        struct bpf_prog *stream_parser;
        struct bpf_prog *stream_verdict;
        struct bpf_prog *skb_verdict;
    };

.. 注意::
    用户不允许将``stream_verdict``和``skb_verdict``程序附加到同一个映射上。
映射程序的附加类型为：

- ``msg_parser``程序 - ``BPF_SK_MSG_VERDICT``
- ``stream_parser``程序 - ``BPF_SK_SKB_STREAM_PARSER``
- ``stream_verdict``程序 - ``BPF_SK_SKB_STREAM_VERDICT``
- ``skb_verdict``程序 - ``BPF_SK_SKB_VERDICT``
与解析器和判决程序一起使用的额外辅助函数有：``bpf_msg_apply_bytes()``和``bpf_msg_cork_bytes()``。通过``bpf_msg_apply_bytes()``，BPF程序可以指示基础设施判决应适用于多少字节。而辅助函数``bpf_msg_cork_bytes()``处理另一种情况，即BPF程序在收到更多字节之前无法对消息做出判决，并且在确定数据包有效前不想转发它。
最后，辅助函数``bpf_msg_pull_data()``和``bpf_msg_push_data()``可供``BPF_PROG_TYPE_SK_MSG``类型的BPF程序使用，以拉取数据并设置指针的起始和结束位置到给定值，或向``struct sk_msg_buff *msg``添加元数据。
下面将更详细地描述所有这些辅助函数。

使用说明
======
内核BPF
----------
bpf_msg_redirect_map()
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_msg_redirect_map(struct sk_msg_buff *msg, struct bpf_map *map, u32 key, u64 flags)

此辅助函数用于实现套接字级别的策略程序中。如果消息``msg``被允许通过（即，如果判决BPF程序返回``SK_PASS``），则将其重定向至由``map``（类型为``BPF_MAP_TYPE_SOCKMAP``）在索引``key``处引用的套接字。可使用入站和出站接口进行重定向。在``flags``中的``BPF_F_INGRESS``值用于选择入站路径，否则选择出站路径。目前仅支持此标志。
成功时返回``SK_PASS``，错误时返回``SK_DROP``。

bpf_sk_redirect_map()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_sk_redirect_map(struct sk_buff *skb, struct bpf_map *map, u32 key, u64 flags)

将数据包重定向至由``map``（类型为``BPF_MAP_TYPE_SOCKMAP``）在索引``key``处引用的套接字。可使用入站和出站接口进行重定向。在``flags``中的``BPF_F_INGRESS``值用于选择入站路径，否则选择出站路径。目前仅支持此标志。
成功时返回``SK_PASS``，错误时返回``SK_DROP``。

bpf_map_lookup_elem()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    void *bpf_map_lookup_elem(struct bpf_map *map, const void *key)

类型为``struct sock *``的套接字条目可通过``bpf_map_lookup_elem()``辅助函数获取。

bpf_sock_map_update()
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: c

    long bpf_sock_map_update(struct bpf_sock_ops *skops, struct bpf_map *map, void *key, u64 flags)

向``map``中添加或更新引用套接字的条目。``skops``作为与``key``关联的条目的新值。``flags``参数可以是以下之一：

- ``BPF_ANY``: 创建新元素或更新现有元素
- ``BPF_NOEXIST``: 如果元素不存在，则创建一个新的元素  
- ``BPF_EXIST``: 更新一个已存在的元素  
如果`map`中包含BPF程序（解析器和判决），这些程序将被添加到的套接字继承。如果套接字已经与BPF程序关联，这将导致错误  
成功时返回0，失败时返回负数错误码  
`bpf_sock_hash_update()`函数  
^^^^^^^^^^^^^^^^^^^^^^^  

下面是C语言代码块：

    long bpf_sock_hash_update(struct bpf_sock_ops *skops, struct bpf_map *map, void *key, u64 flags)

向sockhash ``map`` 中添加或更新一个引用套接字的条目。``skops``作为与``key``相关联的条目的新值使用  
``flags``参数可以是以下之一：  

- ``BPF_ANY``: 创建一个新元素或更新已存在元素  
- ``BPF_NOEXIST``: 只有在元素不存在时才创建新的元素  
- ``BPF_EXIST``: 更新已存在的元素  
如果``map``中有BPF程序（解析器和判决），这些程序将被添加的套接字继承。如果套接字已经与BPF程序关联，这将导致错误  
成功时返回0，失败时返回负数错误码
bpf_msg_redirect_hash()
------------------------
.. code-block:: c

    long bpf_msg_redirect_hash(struct sk_msg_buff *msg, struct bpf_map *map, void *key, u64 flags);

此辅助函数用于在套接字级别实施策略的程序中。如果消息``msg``被允许通过（即，判决BPF程序返回``SK_PASS``），则使用哈希``key``将其重定向到由``map``（类型为``BPF_MAP_TYPE_SOCKHASH``）引用的套接字。可以使用入站和出站接口进行重定向。``flags``中的``BPF_F_INGRESS``值用于选择入站路径，否则选择出站路径。这是目前唯一支持的标志。
成功时返回``SK_PASS``，错误时返回``SK_DROP``。

bpf_sk_redirect_hash()
------------------------
.. code-block:: c

    long bpf_sk_redirect_hash(struct sk_buff *skb, struct bpf_map *map, void *key, u64 flags);

此辅助函数用于在skb套接字级别实施策略的程序中。如果sk_buff``skb``被允许通过（即，判决BPF程序返回``SK_PASS``），则使用哈希``key``将其重定向到由``map``（类型为``BPF_MAP_TYPE_SOCKHASH``）引用的套接字。可以使用入站和出站接口进行重定向。``flags``中的``BPF_F_INGRESS``值用于选择入站路径，否则选择出站路径。这是目前唯一支持的标志。
成功时返回``SK_PASS``，错误时返回``SK_DROP``。

bpf_msg_apply_bytes()
------------------------
.. code-block:: c

    long bpf_msg_apply_bytes(struct sk_msg_buff *msg
