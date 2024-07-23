SPDX 许可证标识符：仅 GPL-2.0
版权所有(C) 2022，红帽公司
=======================
BPF_MAP_TYPE_SK_STORAGE
=======================

.. 注意::
   - “BPF_MAP_TYPE_SK_STORAGE”是在内核版本5.2中引入的。

“BPF_MAP_TYPE_SK_STORAGE”用于为BPF程序提供套接字本地存储。类型为“BPF_MAP_TYPE_SK_STORAGE”的映射声明了要提供的存储类型，并作为访问套接字本地存储的句柄。类型为“BPF_MAP_TYPE_SK_STORAGE”的映射的值存储在每个套接字本地，而不是与映射一起。当请求时，内核负责为套接字分配存储空间；当映射或套接字被删除时，释放该存储空间。
.. 注意::
  - 键类型必须是“int”，并且“max_entries”必须设置为“0”
- 创建用于套接字本地存储的映射时，必须使用“BPF_F_NO_PREALLOC”标志
使用方法
=====

内核 BPF
----------

bpf_sk_storage_get()
~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   void *bpf_sk_storage_get(struct bpf_map *map, void *sk, void *value, u64 flags)

可以使用“bpf_sk_storage_get()”辅助函数从套接字“sk”获取“map”的套接字本地存储。如果使用了“BPF_LOCAL_STORAGE_GET_F_CREATE”标志，则“bpf_sk_storage_get()”将在存储尚未存在的情况下为“sk”创建存储。可以将“value”与“BPF_LOCAL_STORAGE_GET_F_CREATE”一起使用以初始化存储值，否则它将被零初始化。成功时返回指向存储的指针，失败时返回“NULL”。
.. 注意::
   - “sk”是LSM或追踪程序中的内核“struct sock”指针
- 对于其他程序类型，“sk”是一个“struct bpf_sock”指针
bpf_sk_storage_delete()
~~~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   long bpf_sk_storage_delete(struct bpf_map *map, void *sk)

可以使用“bpf_sk_storage_delete()”辅助函数从套接字“sk”删除“map”的套接字本地存储。成功时返回“0”，失败时返回负错误
用户空间
----------

bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. 代码块:: c

   int bpf_map_update_elem(int map_fd, const void *key, const void *value, __u64 flags)

可以使用libbpf函数“bpf_map_update_elem()”将“map_fd”映射的套接字本地存储添加或更新到套接字。套接字由存储在指针“key”中的`socket`“fd”标识。指针“value”包含要添加或更新到套接字“fd”的数据。“value”的类型和大小应与映射定义的值类型相同
可以通过“flags”参数控制更新行为：

- “BPF_ANY”将为`socket`“fd”创建存储或更新现有存储
"BPF_NOEXIST"仅当`socket` "fd"尚不存在时才会为其创建存储空间，否则调用将以"-EEXIST"失败。
"BPF_EXIST"如果`socket` "fd"已存在，则会更新其现有的存储空间，否则调用将以"-ENOENT"失败。
成功返回`0`，或在失败情况下返回负数错误。

bpf_map_lookup_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_lookup_elem(int map_fd, const void *key, void *value)

使用libbpf函数`bpf_map_lookup_elem()`可以从`socket`中检索map "map_fd"的socket本地存储。存储从由`socket` "fd"标识的socket中检索，该"fd"存储在指针`key`中。成功返回`0`，或在失败情况下返回负数错误。

bpf_map_delete_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_delete_elem(int map_fd, const void *key)

使用libbpf函数`bpf_map_delete_elem()`可以从`socket`中删除map "map_fd"的socket本地存储。存储从由`socket` "fd"标识的socket中删除，该"fd"存储在指针`key`中。成功返回`0`，或在失败情况下返回负数错误。

示例
====

内核BPF
-------

以下代码段展示了如何在BPF程序中声明socket本地存储：

.. code-block:: c

    struct {
            __uint(type, BPF_MAP_TYPE_SK_STORAGE);
            __uint(map_flags, BPF_F_NO_PREALLOC);
            __type(key, int);
            __type(value, struct my_storage);
    } socket_storage SEC(".maps");

以下代码段展示了如何在BPF程序中检索socket本地存储：

.. code-block:: c

    SEC("sockops")
    int _sockops(struct bpf_sock_ops *ctx)
    {
            struct my_storage *storage;
            struct bpf_sock *sk;

            sk = ctx->sk;
            if (!sk)
                    return 1;

            storage = bpf_sk_storage_get(&socket_storage, sk, 0,
                                         BPF_LOCAL_STORAGE_GET_F_CREATE);
            if (!storage)
                    return 1;

            /* 在这里使用'storage' */

            return 1;
    }

请参阅`tools/testing/selftests/bpf`目录以获取功能示例。

参考文献
==========

https://lwn.net/ml/netdev/20190426171103.61892-1-kafai@fb.com/
