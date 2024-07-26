SPDX 许可证标识符: GPL-2.0-only
版权所有 (C) 2022 Red Hat, Inc.
=======================
BPF_MAP_TYPE_SK_STORAGE
=======================

.. note::
   - `BPF_MAP_TYPE_SK_STORAGE` 在内核版本 5.2 中被引入。

`BPF_MAP_TYPE_SK_STORAGE` 用于为 BPF 程序提供基于套接字的本地存储。类型为 `BPF_MAP_TYPE_SK_STORAGE` 的映射声明了要提供的存储类型，并作为访问套接字本地存储的句柄。类型为 `BPF_MAP_TYPE_SK_STORAGE` 映射的值存储在每个套接字本地，而不是与映射一起存储。内核负责根据请求为套接字分配存储空间，并在删除映射或套接字时释放存储空间。
.. note::
  - 键类型必须是 `int` 并且 `max_entries` 必须设置为 `0`
  - 创建用于套接字本地存储的映射时必须使用 `BPF_F_NO_PREALLOC` 标志

使用
=====

内核 BPF
--------

bpf_sk_storage_get()
~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   void *bpf_sk_storage_get(struct bpf_map *map, void *sk, void *value, u64 flags)

可以使用 `bpf_sk_storage_get()` 辅助函数从套接字 `sk` 获取 `map` 的套接字本地存储。如果使用了 `BPF_LOCAL_STORAGE_GET_F_CREATE` 标志，则 `bpf_sk_storage_get()` 会为 `sk` 创建存储空间（如果尚未存在）。可以通过 `value` 与 `BPF_LOCAL_STORAGE_GET_F_CREATE` 一起使用来初始化存储值，否则将进行零初始化。成功时返回指向存储空间的指针，失败时返回 `NULL`。
.. note::
   - `sk` 是 LSM 或跟踪程序中的内核 `struct sock` 指针
   - 对于其他程序类型，`sk` 是 `struct bpf_sock` 指针

bpf_sk_storage_delete()
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   long bpf_sk_storage_delete(struct bpf_map *map, void *sk)

可以使用 `bpf_sk_storage_delete()` 辅助函数从套接字 `sk` 删除 `map` 的套接字本地存储。成功时返回 `0`，失败时返回负错误码。

用户空间
--------

bpf_map_update_elem()
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

   int bpf_map_update_elem(int map_fd, const void *key, const void *value, __u64 flags)

可以使用 libbpf 函数 `bpf_map_update_elem()` 将 `map_fd` 映射的套接字本地存储添加或更新到特定套接字。套接字由存储在 `key` 指针中的 `socket` 文件描述符 (`fd`) 标识。`value` 指针包含要添加或更新到 `socket` `fd` 的数据。`value` 的类型和大小应与映射定义中的值类型相同。
`flags` 参数可用于控制更新行为：

- `BPF_ANY` 将为 `socket` `fd` 创建存储空间或更新现有存储
### BPF_NOEXIST
`BPF_NOEXIST` 只有在针对 `socket` 的 `fd` 尚未存在存储时才会创建相应的存储空间，否则调用将以 `-EEXIST` 错误失败。

### BPF_EXIST
`BPF_EXIST` 如果针对 `socket` 的 `fd` 已经存在存储空间，则会更新该存储空间；否则调用将以 `-ENOENT` 错误失败。

成功返回 `0`，失败则返回负的错误码。
#### bpf_map_lookup_elem()

```c
int bpf_map_lookup_elem(int map_fd, const void *key, void *value);
```

可以使用 `bpf_map_lookup_elem()` 函数从一个套接字中获取与 `map_fd` 相关的本地存储。该存储通过指向包含 `socket` 的 `fd` 的指针 `key` 来识别。成功返回 `0`，失败则返回负的错误码。

#### bpf_map_delete_elem()

```c
int bpf_map_delete_elem(int map_fd, const void *key);
```

可以使用 `bpf_map_delete_elem()` 函数从一个套接字中删除与 `map_fd` 相关的本地存储。该存储通过指向包含 `socket` 的 `fd` 的指针 `key` 来识别。成功返回 `0`，失败则返回负的错误码。

### 示例

#### 内核 BPF

以下代码片段展示了如何在一个 BPF 程序中声明套接字本地存储：

```c
struct {
        __uint(type, BPF_MAP_TYPE_SK_STORAGE);
        __uint(map_flags, BPF_F_NO_PREALLOC);
        __type(key, int);
        __type(value, struct my_storage);
} socket_storage SEC(".maps");
```

以下代码片段展示了如何在一个 BPF 程序中检索套接字本地存储：

```c
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

        /* 使用 'storage' */

        return 1;
}
```

更多功能性的示例，请参考 `tools/testing/selftests/bpf` 目录。

### 参考资料

- [https://lwn.net/ml/netdev/20190426171103.61892-1-kafai@fb.com/](https://lwn.net/ml/netdev/20190426171103.61892-1-kafai@fb.com/)
