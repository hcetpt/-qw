SPDX 许可声明标识符: GPL-2.0

=================================
网络文件系统辅助库
=================================

.. 目录：

- 概览
- 每inode的上下文
- inode上下文辅助函数
- 缓冲读取辅助
- 读取辅助函数
- 读取辅助结构
- 读取辅助操作
- 读取辅助过程
- 读取辅助缓存API

概览
========

网络文件系统辅助库是一组旨在帮助网络文件系统实现VM/VFS操作的函数。目前，这仅包括将各种VM缓冲读取操作转换为从服务器读取的请求。然而，该辅助库也可以介入其他服务，例如本地缓存或本地数据加密。
请注意，库模块不会直接链接到本地缓存，因此必须通过网络文件系统（netfs）提供访问。
每inode上下文
=================

网络文件系统辅助库需要一个地方来存储它所管理的每个netfs inode的一点状态。为此，定义了一个上下文结构体：

```c
    struct netfs_inode {
        struct inode inode;
        const struct netfs_request_ops *ops;
        struct fscache_cookie *cache;
    };
```

希望使用netfs库的网络文件系统必须在其inode包装结构中放置这样一个结构体，而不是使用VFS的`struct inode`。这可以通过类似以下的方式完成：

```c
    struct my_inode {
        struct netfs_inode netfs; /* Netfslib上下文和VFS inode */
        ...
    };
```

这样允许netfslib通过从inode指针使用`container_of()`找到其状态，从而允许VFS/VM操作表直接指向netfslib帮助函数。
该结构包含以下字段：

 * `inode`

   VFS inode结构体
* `ops`

   网络文件系统为netfslib提供的操作集
* `cache`

   本地缓存cookie，如果没有启用缓存则为NULL。如果禁用了fscache，则此字段不存在

inode上下文帮助函数
------------------------------

为了处理每个inode上下文，提供了一组帮助函数。首先是一个用于对上下文执行基本初始化并设置操作表指针的函数：

```c
    void netfs_inode_init(struct netfs_inode *ctx,
                          const struct netfs_request_ops *ops);
```

然后是一个将VFS inode结构转换为netfs上下文的函数：

```c
    struct netfs_inode *netfs_node(struct inode *inode);
```

最后，有一个从附加到inode的上下文中获取缓存cookie指针（或如果禁用了fscache则为NULL）的函数：

```c
    struct fscache_cookie *netfs_i_cookie(struct netfs_inode *ctx);
```

带缓冲读取的帮助函数
=====================

该库提供了一组读取帮助函数，处理`->read_folio()`、`->readahead()`以及大部分`->write_begin()`VM操作，并将它们转换为一个通用调用框架。
提供的服务包括：

 * 处理跨越多个页面的folio
* 隔离netfs免受VM接口更改的影响
* 允许netfs任意分割读取操作，即使这些分割不匹配folio大小或对齐方式，并且可能跨越多个folio
* 允许网络文件系统（netfs）在两个方向上扩展预读请求以满足其需求
* 允许网络文件系统部分地完成一次读取，然后重新提交剩余部分
* 处理本地缓存，允许缓存数据与从服务器读取的数据交错，以满足单个请求
* 处理清除不在服务器上的缓冲区
* 处理重试失败的读取操作，并根据需要将缓存中的读取切换到服务器
* 在将来，这里还可以实现其他服务，例如对要远程存储或缓存的数据进行本地加密

从网络文件系统来看，辅助函数需要一个操作表。这包括一个强制性的读取操作方法以及一些可选的方法。

读取辅助函数
-------------

提供了三个读取辅助函数：

```plaintext
void netfs_readahead(struct readahead_control *ractl);
int netfs_read_folio(struct file *file,
                     struct folio *folio);
int netfs_write_begin(struct netfs_inode *ctx,
                      struct file *file,
                      struct address_space *mapping,
                      loff_t pos,
                      unsigned int len,
                      struct folio **_folio,
                      void **_fsdata);
```

每个辅助函数对应于虚拟内存地址空间的一个操作。这些操作使用每个inode上下文中的状态。
对于 `->readahead()` 和 `->read_folio()`，网络文件系统直接指向相应的读取辅助函数；而对于 `->write_begin()`，可能稍微复杂一些，因为网络文件系统可能需要刷新冲突写入或跟踪脏数据，并且如果在调用辅助函数后发生错误，需要释放已获取的页框（folio）。

辅助函数管理读取请求，并通过提供的操作表回调到网络文件系统。对于那些需要同步返回的辅助函数，在返回前会根据需要执行等待操作。
如果发生错误，将调用 `->free_request()` 来清理分配的 `netfs_io_request` 结构。如果在发生错误时请求的部分仍在处理中，并且读取了足够的数据，则请求将部分完成。
此外，还有：

  * `void netfs_subreq_terminated(struct netfs_io_subrequest *subreq, ssize_t transferred_or_error, bool was_async);`

这个函数用于完成一个读取子请求。它接收传输的字节数或负的错误代码，以及一个标志位，该标志位指示操作是否是异步的（即后续处理是否可以在当前上下文中完成，因为这可能涉及休眠）。

读取帮助结构
--------------

读取帮助器使用了一些结构来维护读取的状态。首先是管理整个读取请求的结构：

```c
struct netfs_io_request {
    struct inode       *inode;
    struct address_space *mapping;
    struct netfs_cache_resources cache_resources;
    void            *netfs_priv;
    loff_t           start;
    size_t           len;
    loff_t           i_size;
    const struct netfs_request_ops *netfs_ops;
    unsigned int     debug_id;
    ..
};
```

上述字段是网络文件系统可以使用的字段。它们是：

 * `inode`
 * `mapping`

   正在从中读取文件的inode和地址空间。`mapping` 可能指向 `inode->i_data`，也可能不指向。
* `cache_resources`

   如果存在本地缓存，供其使用的资源。
* `netfs_priv`

   网络文件系统的私有数据。此值可以在调用帮助函数时传递，或者在请求过程中设置。
* `start`
 * `len`

   读取请求的起始文件位置和长度。这些值可能会被 `->expand_readahead()` 操作修改。
* `i_size`

   请求开始时的文件大小。
* `netfs_ops`

   操作表的指针。此值会传递给帮助函数。
* `debug_id`

   分配给此操作的一个数字，可以在跟踪行中显示以供参考。
第二个结构用于管理整体读请求中的各个分片：

```c
struct netfs_io_subrequest {
    struct netfs_io_request *rreq; // 指向读请求的指针
    loff_t start;                  // 该分片在文件中的起始位置
    size_t len;                    // 分片长度
    size_t transferred;            // 已经传输的数据量
    unsigned long flags;           // 标志位
    unsigned short debug_index;    // 用于调试时显示的索引号
    // ...
};
```

每个子请求预期访问单个来源，尽管帮助函数会处理从一种类型回退到另一种类型的情况。成员包括：

- `rreq`：指向读请求的指针
- `start`：该分片在文件中的起始位置
- `len`：分片长度
- `transferred`：已经传输的数据量。网络文件系统或缓存应该从此位置开始操作。如果发生短读，帮助函数会再次调用，并更新此值以反映已读取的数据量。
- `flags`：与读操作相关的标志。有两个标志对文件系统或缓存特别重要：
  - `NETFS_SREQ_CLEAR_TAIL`：可以设置此标志以指示从 `transferred` 到 `len` 的剩余部分应被清零。
  - `NETFS_SREQ_SEEK_DATA_READ`：这是一个提示，表明缓存可能希望尝试跳过到下一个数据（即使用 `SEEK_DATA`）。
- `debug_index`：分配给这个分片的一个数字，可以在调试信息中显示以便参考。

读取帮助函数操作
----------------------

网络文件系统必须提供一组操作表给读取帮助函数，通过这些操作表它可以发出请求并进行协商：

```c
struct netfs_request_ops {
    void (*init_request)(struct netfs_io_request *rreq, struct file *file);
    void (*free_request)(struct netfs_io_request *rreq);
    void (*expand_readahead)(struct netfs_io_request *rreq);
    bool (*clamp_length)(struct netfs_io_subrequest *subreq);
    void (*issue_read)(struct netfs_io_subrequest *subreq);
    bool (*is_still_valid)(struct netfs_io_request *rreq);
    int (*check_write_begin)(struct file *file, loff_t pos, unsigned len,
                             struct folio **foliop, void **_fsdata);
    void (*done)(struct netfs_io_request *rreq);
};
```

操作如下：

- `init_request()`：[可选] 用于初始化请求结构。它将文件作为参考参数传递。
- `free_request()`：[可选] 在请求被释放时调用，以便文件系统清理其附加的任何状态。
- `expand_readahead()`：[可选] 允许文件系统扩展读取预读请求的大小。文件系统可以在两个方向上扩展请求，但不允许减少请求大小，因为这些数值可能代表已经分配的资源。如果启用了本地缓存，则先由缓存扩展请求。
扩展通过更改请求结构中的`->start`和`->len`来实现。需要注意的是，如果进行了任何更改，`->len`必须至少增加与`->start`减少相同的量。
* `clamp_length()`

   [可选] 此函数用于允许文件系统减小子请求的大小。例如，文件系统可以使用此函数将需要拆分到多个服务器上的请求分割开，或将多次读取操作合并进行。
   成功时应返回0，错误时返回错误代码。
* `issue_read()`

   [必需] 帮助程序使用此函数将子请求分派给服务器进行读取。在子请求中，`->start`、`->len` 和 `->transferred` 指示应从服务器读取哪些数据。
   没有返回值；应调用 `netfs_subreq_terminated()` 函数来指示操作是否成功以及传输了多少数据。文件系统不应处理设置页面为最新状态、解锁页面或释放其引用的操作——帮助程序需要处理这些操作，因为它们需要与复制到本地缓存的操作协调。
   注意，帮助程序已锁定页面，但未固定。可以使用 `ITER_XARRAY` iov 迭代器引用正在操作的inode范围，而无需分配大型bvec表。
* `is_still_valid()`

   [可选] 此函数用于检查刚从本地缓存读取的数据是否仍然有效。如果数据仍然有效，则应返回true，否则返回false。如果数据不再有效，将重新从服务器读取。
* `check_write_begin()`

   [可选] 此函数由 `netfs_write_begin()` 帮助程序调用，在它分配/获取要修改的页面之后，以允许文件系统在允许修改之前刷新冲突的状态。
   它可能会解锁并丢弃给定的页面，并将调用者的页面指针设置为NULL。如果一切正常（`*foliop` 保持不变）或应重试操作（`*foliop` 清除）时，应返回0；其他任何错误代码将终止操作。
* `done`

   [可选] 在请求中的所有页面都已解锁（如果适用则标记为最新状态）后调用此函数。
读取帮助程序流程
---------------------

读取帮助程序的工作流程如下：

 * 设置请求
* 对于预读，允许本地缓存然后是网络文件系统提出扩展读取请求。这之后会提交给虚拟内存（VM）处理。如果虚拟内存无法完全执行扩展，则会执行部分扩展的读取操作，但可能不会全部写入缓存
* 循环切分请求中的块以形成子请求：

   * 如果存在本地缓存，则由它来完成切分，否则帮助程序尝试生成最大的切片
* 如果网络文件系统是数据源，它可以限制每个切片的大小。这使得可以实现 `rsize` 和分块功能
* 帮助程序从缓存或服务器发起读取操作，或者根据需要清除切片
* 下一个切片从上一个切片的末尾开始
* 当切片完成读取时，它们终止
* 当所有子请求都已终止后，评估这些子请求，并重新发出任何短的或失败的子请求：

   * 失败的缓存请求将改为对服务器发出
* 失败的服务器请求则直接失败
* 对于任一来源的短读请求，如果已经传输了一些更多的数据，则将重新针对该来源发出这些请求：

    * 缓存可能需要跳过无法直接进行DIO操作的空洞。

* 如果设置了NETFS_SREQ_CLEAR_TAIL标志，则短读请求将被清空到切片末尾，而不是重新发出。

* 一旦数据读取完成，那些已经被完全读取或清空的页框（folio）：

    * 将被标记为uptodate（已更新）。
    
* 如果存在缓存，则会被标记为PG_fscache。
* 解锁。

* 需要写入缓存的任何页框随后将发起DIO写操作。
* 同步操作将等待读取完成。
* 写入缓存的操作将异步进行，并且在完成时移除页框上的PG_fscache标记。
* 在所有操作完成后，请求结构将被清理。

读取帮助器缓存API
---------------------

在实现用于读取帮助器的本地缓存时，需要两件事：一种方法让网络文件系统初始化读取请求的缓存，以及一个供帮助器调用的操作表。
为了开始对fscache对象的缓存操作，需要调用以下函数：

```c
int fscache_begin_read_operation(struct netfs_io_request *rreq, struct fscache_cookie *cookie);
```

传入请求指针和与文件对应的cookie。这将填充下面提到的缓存资源。
`netfs_io_request`对象包含了一个供缓存挂载其状态的地方：

```c
    struct netfs_cache_resources {
        const struct netfs_cache_ops	*ops;
        void				*cache_priv;
        void				*cache_priv2;
    };
```

这其中包括一个操作表指针和两个私有数据指针。操作表如下所示：

```c
    struct netfs_cache_ops {
        void (*end_operation)(struct netfs_cache_resources *cres);

        void (*expand_readahead)(struct netfs_cache_resources *cres,
                                 loff_t *_start, size_t *_len, loff_t i_size);

        enum netfs_io_source (*prepare_read)(struct netfs_io_subrequest *subreq,
                                             loff_t i_size);

        int (*read)(struct netfs_cache_resources *cres,
                    loff_t start_pos,
                    struct iov_iter *iter,
                    bool seek_data,
                    netfs_io_terminated_t term_func,
                    void *term_func_priv);

        int (*prepare_write)(struct netfs_cache_resources *cres,
                             loff_t *_start, size_t *_len, loff_t i_size,
                             bool no_space_allocated_yet);

        int (*write)(struct netfs_cache_resources *cres,
                     loff_t start_pos,
                     struct iov_iter *iter,
                     netfs_io_terminated_t term_func,
                     void *term_func_priv);

        int (*query_occupancy)(struct netfs_cache_resources *cres,
                               loff_t start, size_t len, size_t granularity,
                               loff_t *_data_start, size_t *_data_len);
    };
```

终止处理函数的指针定义如下：

```c
    typedef void (*netfs_io_terminated_t)(void *priv,
                                          ssize_t transferred_or_error,
                                          bool was_async);
```

表中定义的方法包括：

 * `end_operation()`

   [必需] 在读请求结束时调用，用于清理资源。
   
* `expand_readahead()`

   [可选] 在`netfs_readahead()`操作开始时调用，允许缓存在任一方向上扩展请求。这使得缓存能够根据其粒度要求适当调整请求大小。
   函数接收指向起始位置和长度的指针以及文件大小作为参考，并相应地调整起始位置和长度。它应该返回以下值之一：
   
   * `NETFS_FILL_WITH_ZEROES`
   * `NETFS_DOWNLOAD_FROM_SERVER`
   * `NETFS_READ_FROM_CACHE`
   * `NETFS_INVALID_READ`
   
   以指示该片段是否应被清空，或者是否应从服务器下载或从缓存中读取——或者是否应在此时放弃分片。

* `prepare_read()`

   [必需] 调用以配置请求的下一个片段。子请求中的`->start`和`->len`指示了下一个片段的位置和大小；缓存可以将其长度减少到符合其粒度要求的程度。

* `read()`

   [必需] 调用来从缓存中读取。提供文件的起始偏移量以及一个迭代器来读取，迭代器给出了长度。还可以提供一个提示，请求从起始位置向前查找数据。
   同时还提供了一个终止处理函数的指针和要传递给该函数的私有数据。终止函数应在传递已传输字节数或错误代码的同时，加上一个标志，指示终止是否肯定在调用者的上下文中发生。

* `prepare_write()`

   [必需] 调用来准备向缓存写入。这涉及检查缓存是否有足够的空间来完成写入。`*_start`和`*_len`指示要写入的区域；该区域可以根据直接I/O对齐的要求进行缩小或扩展到页边界。`i_size`持有对象的大小并提供参考。如果调用者确定该区域尚未分配空间，则将`no_space_allocated_yet`设置为`true`——例如，如果它已经尝试从那里读取数据。

* `write()`

   [必需] 调用来向缓存写入。提供文件的起始偏移量以及一个迭代器来写入，迭代器给出了长度。
   同时还提供了一个终止处理函数的指针和要传递给该函数的私有数据。终止函数应在传递已传输字节数或错误代码的同时，加上一个标志，指示终止是否肯定在调用者的上下文中发生。

* `query_occupancy()`

   [必需] 调用来查询缓存特定区域中下一块数据的位置。传入要查询的区域的起始位置和长度，以及答案需要对齐的粒度。函数返回该区域内可用的数据（如果有）的起始位置和长度。注意，前面可能存在空洞。
如果找到一些数据则返回0，如果没有可用数据则返回-ENODATA，如果此文件上没有缓存则返回-ENOBUFS。
注意，这些方法传递的是缓存资源结构的指针，而不是读取请求结构的指针，因为它们也可以用于没有读取请求结构的情况，例如将脏数据写入缓存。

API函数参考
=============
.. kernel-doc:: include/linux/netfs.h
.. kernel-doc:: fs/netfs/buffered_read.c
.. kernel-doc:: fs/netfs/io.c
