BPF 地图
========

BPF '地图' 提供了在内核和用户空间之间共享数据的通用存储，支持不同类型。可用的存储类型包括哈希、数组、布隆过滤器和基数树。某些地图类型的存在是为了支持特定的 BPF 辅助函数，这些函数根据地图内容执行操作。地图通过 BPF 辅助函数从 BPF 程序中访问，这些辅助函数在 `man-pages`_ 的 `bpf-helpers(7)`_ 文档中进行了描述。
BPF 地图通过 `bpf` 系统调用从用户空间访问，该系统调用提供了创建地图、查找元素、更新元素和删除元素的命令。更多关于 BPF 系统调用的详细信息可以在 `ebpf-syscall`_ 和 `man-pages`_ 的 `bpf(2)`_ 中找到。

地图类型
========

.. toctree::
   :maxdepth: 1
   :glob:

   map_*

使用说明
========

.. c:function::
   int bpf(int command, union bpf_attr *attr, u32 size)

使用 `bpf()` 系统调用来执行由 `command` 指定的操作。操作需要 `attr` 中提供的参数。`size` 参数是 `attr` 中 `union bpf_attr` 的大小。

**BPF_MAP_CREATE**

使用期望的类型和 `attr` 中的属性创建一个地图：

.. code-block:: c

    int fd;
    union bpf_attr attr = {
            .map_type = BPF_MAP_TYPE_ARRAY;  /* 必须 */
            .key_size = sizeof(__u32);       /* 必须 */
            .value_size = sizeof(__u32);     /* 必须 */
            .max_entries = 256;              /* 必须 */
            .map_flags = BPF_F_MMAPABLE;
            .map_name = "example_array";
    };

    fd = bpf(BPF_MAP_CREATE, &attr, sizeof(attr));

成功时返回进程本地文件描述符，失败时返回负错误。通过调用 `close(fd)` 可以删除地图。持有打开文件描述符的地图会在进程退出时自动删除。

.. note:: 对于 `map_name`，有效的字符为 `A-Z`、`a-z`、`0-9`、`'_'` 和 `'.'`

**BPF_MAP_LOOKUP_ELEM**

使用 `attr->map_fd`、`attr->key` 和 `attr->value` 在给定地图中查找键。成功时返回零，并将找到的元素存储到 `attr->value` 中，失败时返回负错误。

**BPF_MAP_UPDATE_ELEM**

使用 `attr->map_fd`、`attr->key` 和 `attr->value` 在给定地图中创建或更新键值对。成功时返回零，失败时返回负错误。

**BPF_MAP_DELETE_ELEM**

使用 `attr->map_fd` 和 `attr->key` 在给定地图中查找并删除元素。成功时返回零，失败时返回负错误。

.. Links:
.. _man-pages: https://www.kernel.org/doc/man-pages/
.. _bpf(2): https://man7.org/linux/man-pages/man2/bpf.2.html
.. _bpf-helpers(7): https://man7.org/linux/man-pages/man7/bpf-helpers.7.html
.. _ebpf-syscall: https://docs.kernel.org/userspace-api/ebpf/syscall.html
