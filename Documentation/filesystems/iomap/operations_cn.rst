SPDX 许可证标识符: GPL-2.0
.. _iomap_operations:

.

一些笔记以保持作者的理智：
    请尝试在单独的行开始句子，以便在 diff 中颜色不会混在一起
标题装饰在 sphinx.rst 中有文档说明
=========================
支持的文件操作
=========================

.. contents:: 目录
   :local:

以下是关于 iomap 实现的高级文件操作的讨论。
缓冲 I/O
============

缓冲 I/O 是 Linux 中默认的文件 I/O 路径。
文件内容被缓存在内存中（“页缓存”），以满足读取和写入需求。
脏缓存将在某个时刻被写回磁盘，可以通过 `fsync` 及其变体强制执行。
iomap 几乎实现了所有在传统 I/O 模型下文件系统需要自己实现的 folio 和页缓存管理功能。
这意味着文件系统不需要知道分配、映射、管理 uptodate 和脏状态以及页缓存 folio 写回的具体细节。
在传统的 I/O 模型下，这些功能通过链表的缓冲头来管理，效率非常低，而 iomap 使用的是每个 folio 的位图。
除非文件系统明确选择使用缓冲区头（buffer heads），否则不会使用它们，这使得带缓冲的I/O操作更加高效，并且使页缓存维护者更加满意。

``struct address_space_operations``
-----------------------------------

以下iomap函数可以直接从地址空间操作结构中引用：

 * ``iomap_dirty_folio``
 * ``iomap_release_folio``
 * ``iomap_invalidate_folio``
 * ``iomap_is_partially_uptodate``

以下地址空间操作可以轻松包装：

 * ``read_folio``
 * ``readahead``
 * ``writepages``
 * ``bmap``
 * ``swap_activate``

``struct iomap_folio_ops``
--------------------------

对于页缓存操作，`->iomap_begin` 函数可以设置 `struct iomap::folio_ops` 字段为一个操作结构，以覆盖 iomap 的默认行为：

```c
struct iomap_folio_ops {
    struct folio *(*get_folio)(struct iomap_iter *iter, loff_t pos,
                               unsigned len);
    void (*put_folio)(struct inode *inode, loff_t pos, unsigned copied,
                      struct folio *folio);
    bool (*iomap_valid)(struct inode *inode, const struct iomap *iomap);
};
```

iomap 调用这些函数：

  - ``get_folio``：在开始写入之前分配并返回一个锁定的 folio 的活动引用。
    如果未提供此函数，iomap 将调用 `iomap_get_folio`。
    这可以用于为写入 `设置每个 folio 的文件系统状态`<https://lore.kernel.org/all/20190429220934.10415-5-agruenba@redhat.com/>。
  - ``put_folio``：在页缓存操作完成后解锁并释放 folio。
    如果未提供此函数，iomap 将自行调用 `folio_unlock` 和 `folio_put`。
    这可以用于 `提交由 ->get_folio 设置的每个 folio 的文件系统状态`<https://lore.kernel.org/all/20180619164137.13720-6-hch@lst.de/>。
  - ``iomap_valid``：文件系统在 `->iomap_begin` 和 `->iomap_end` 之间不能持有锁，因为页缓存操作可能会获取 folio 锁、在用户空间页面上发生错误、启动内存回收的写回或进行其他耗时的操作。
    如果文件的空间映射数据是可变的，那么在分配、安装和锁定 folio 所需的时间内，特定页缓存 folio 的映射可能会 `发生变化`<https://lore.kernel.org/all/20221123055812.747923-8-david@fromorbit.com/>。
    对于页缓存，如果写回不获取 `i_rwsem` 或 `invalidate_lock` 并更新映射信息，则可能会出现竞争。
如果文件系统允许并发写入，也可能发生竞态条件。对于此类文件，在获取 folio 锁之后必须重新验证映射，以便 iomap 能够正确管理 folio。
fsdax 不需要这种重新验证，因为它没有回写（writeback）机制，也不支持未写入的范围（unwritten extents）。
受这种竞态条件影响的文件系统必须提供一个 `->iomap_valid` 函数来决定映射是否仍然有效。
如果映射无效，则会再次采样映射。
为了支持有效性决策，文件系统的 `->iomap_begin` 函数可以在填充其他 iomap 字段的同时设置 `struct iomap::validity_cookie`。
一种简单的验证标记实现是一个序列计数器。
如果文件系统在每次修改节点的范围映射时都会增加序列计数器，那么可以在 `->iomap_begin` 期间将其放入 `struct iomap::validity_cookie` 中。
如果在将映射传递回 `->iomap_valid` 时发现标记中的值与文件系统持有的值不同，则认为 iomap 已过期，验证失败。

以下 `struct kiocb` 标志对带有 iomap 的缓冲 I/O 有重要意义：

 * `IOCB_NOWAIT`：启用 `IOMAP_NOWAIT`
内部每 Folio 状态
------------------------

如果 fsblock 的大小与页面缓存 folio 的大小相匹配，则假定所有磁盘 I/O 操作都将处理整个 folio。
在这种情况下，只需要 folio 的 uptodate（内存内容至少与磁盘上的内容一样新）和 dirty（内存内容比磁盘上的内容更新）状态。

如果 fsblock 的大小小于页面缓存 folio 的大小，iomap 会自行跟踪每个 fsblock 的 uptodate 和 dirty 状态。
这使得 iomap 能够处理 “bs < ps” 文件系统
<https://lore.kernel.org/all/20230725122932.144426-1-ritesh.list@gmail.com/> 和页面缓存中的大 folio。
iomap 内部为每个 fsblock 跟踪两个状态位：

 * ``uptodate``：iomap 将尝试保持 folio 完全最新。如果有读取（预读）错误，这些 fsblock 不会被标记为 uptodate。
   当 folio 内的所有 fsblock 都是 uptodate 时，该 folio 本身将被标记为 uptodate。
 * ``dirty``：当程序写入文件时，iomap 将设置每个块的 dirty 状态。
   当 folio 内的任何 fsblock 是 dirty 时，该 folio 本身将被标记为 dirty。

iomap 还跟踪正在进行的读取和写入磁盘 I/O 的数量。
此结构比 `struct buffer_head` 轻量得多，因为每个 folio 只有一个该结构，并且每个 fsblock 的开销是两位对104字节。
希望在页缓存中启用大 folio 的文件系统应在初始化内存inode时调用 `mapping_set_large_folios`。

缓冲预读和读取
--------------

`iomap_readahead` 函数启动到页缓存的预读。
`iomap_read_folio` 函数将一个 folio 的数据读入页缓存。
`->iomap_begin` 的 `flags` 参数将被设置为零。
页缓存会在调用文件系统之前获取所需的锁。

缓冲写入
--------------

`iomap_file_buffered_write` 函数将一个 `iocb` 写入页缓存。
`IOMAP_WRITE` 或 `IOMAP_WRITE` | `IOMAP_NOWAIT` 将作为 `->iomap_begin` 的 `flags` 参数传递。
调用者通常在调用此函数前以共享或独占模式获取 `i_rwsem`。

mmap 写入错误处理
~~~~~~~~~~~~~~~~~

`iomap_page_mkwrite` 函数处理页缓存中 folio 的写入错误。
``IOMAP_WRITE | IOMAP_FAULT`` 将作为 `flags` 参数传递给 `->iomap_begin`。

调用者通常在调用此函数之前以共享或独占模式获取 mmap 的 `invalidate_lock`。

缓冲写入失败
~~~~~~~~~~~~~~~~~~~~~~~

在对页面缓存进行短写操作后，未写入的区域不会被标记为脏数据。
文件系统必须安排取消此类预留（reservation），因为回写操作不会消耗这些预留。具体可以参考相关邮件：
- 取消预留：`<https://lore.kernel.org/all/20221123055812.747923-6-david@fromorbit.com/>`
- 预留详情：`<https://lore.kernel.org/linux-xfs/20220817093627.GZ3600936@dread.disaster.area/>`

可以在 `->iomap_end` 函数中调用 `iomap_file_buffered_write_punch_delalloc` 来查找所有干净的 folio 区域，这些 folio 缓存了新的（`IOMAP_F_NEW`）延迟分配映射。
它需要 `invalidate_lock`。
文件系统必须提供一个 `punch` 函数，用于处理每个处于这种状态的文件范围。
该函数只能取消延迟分配预留，以防另一个线程与当前线程竞争写入同一区域并触发回写以将脏数据刷新到磁盘。

文件操作中的清零
~~~~~~~~~~~~~~~~~~~~~~~~~~~

文件系统可以调用 `iomap_zero_range` 来执行非截断文件操作的页面缓存清零，这些操作不对齐到 fsblock 大小。
`IOMAP_ZERO` 将作为 `flags` 参数传递给 `->iomap_begin`。
调用者通常在调用此函数之前以独占模式持有 ``i_rwsem`` 和 ``invalidate_lock``

未共享 Reflinked 文件数据
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

文件系统可以调用 ``iomap_file_unshare`` 强制一个与另一个文件共享存储的文件预先复制共享数据到新分配的存储空间。
``IOMAP_WRITE | IOMAP_UNSHARE`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
调用者通常在调用此函数之前以独占模式持有 ``i_rwsem`` 和 ``invalidate_lock``。

截断
----------

文件系统可以调用 ``iomap_truncate_page`` 在文件截断操作期间将从文件末尾（EOF）到 fsblock 末尾的页缓存中的字节清零。
``truncate_setsize`` 或 ``truncate_pagecache`` 会在 EOF 块之后处理所有事务。
``IOMAP_ZERO`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
调用者通常在调用此函数之前以独占模式持有 ``i_rwsem`` 和 ``invalidate_lock``。

页缓存写回
-------------------

文件系统可以调用 ``iomap_writepages`` 来响应将脏页缓存 folios 写入磁盘的请求。
应该将 ``mapping`` 和 ``wbc`` 参数原样传递。
``wpc`` 指针应由文件系统分配，并且必须初始化为零。
页面缓存会在尝试调度每个页元数据（folio）进行回写之前将其锁定。
它不会锁定 ``i_rwsem`` 或 ``invalidate_lock``。
即使回写失败，所有通过下面描述的 ``->map_blocks`` 机制处理的页元数据（folio）的脏位也会被清除。
这是为了防止在存储设备故障时出现脏页元数据（folio）的聚集团；一个 ``-EIO`` 错误会被记录下来，以便用户空间通过 ``fsync`` 收集。
``ops`` 结构必须指定，并如下所示：

``struct iomap_writeback_ops``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    struct iomap_writeback_ops {
        int (*map_blocks)(struct iomap_writepage_ctx *wpc, struct inode *inode,
                          loff_t offset, unsigned len);
        int (*prepare_ioend)(struct iomap_ioend *ioend, int status);
        void (*discard_folio)(struct folio *folio, loff_t pos);
    };

字段说明如下：

  - ``map_blocks``：将 ``wpc->iomap`` 设置为由 ``offset`` 和 ``len`` 给出的文件范围（以字节为单位）的空间映射。
    iomap 对每个脏文件系统的块中的每个脏页元数据调用此函数，尽管对于页元数据内连续的脏文件系统块，它会重用映射。
    在这里不要返回 ``IOMAP_INLINE`` 映射；``->iomap_end`` 函数必须处理已写入的数据的持久化。
    在这里不要返回 ``IOMAP_DELALLOC`` 映射；iomap 目前要求映射到已分配的空间。
    如果映射没有改变，文件系统可以跳过可能昂贵的映射查找。
### 重新验证必须由文件系统进行开放编码；目前尚不清楚是否可以重用 `iomap::validity_cookie` 来实现这一目的

此函数必须由文件系统提供：
- `prepare_ioend`：允许文件系统在提交回写 I/O 之前转换回写的 ioend 或执行任何其他准备工作
这可能包括预写空间的更新，或者安装一个自定义的 `->bi_end_io` 函数用于内部目的，例如将 ioend 完成推迟到工作队列中以从进程上下文中运行元数据更新事务
此函数是可选的

- `discard_folio`：当 `->map_blocks` 失败且无法为脏 folio 的任何部分调度 I/O 时，iomap 会调用此函数
该函数应丢弃为写操作所做的任何预留
folio 将被标记为干净，并在页缓存中记录 `-EIO`
文件系统可以使用此回调来移除 delalloc 预留，以避免为干净的页缓存保留 delalloc 预留
此函数是可选的
页面缓存写回完成
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

为了处理写回完成后磁盘 I/O 所需的账簿记录工作，iomap 创建了由 `struct iomap_ioend` 对象构成的链表，这些对象包裹了用于将页面缓存数据写入磁盘的 `bio`。默认情况下，iomap 通过清除与 `ioend` 关联的 folios 上的写回位来完成写回 ioends 的处理。如果写操作失败，它还会设置 folios 和地址空间上的错误位。这可能发生在中断上下文或进程上下文中，具体取决于存储设备。需要更新内部账簿记录的文件系统（例如未写入范围转换）应提供一个 `->prepare_ioend` 函数，以将其自己的函数设置为 `struct iomap_end::bio::bi_end_io`。该函数在完成其自身的工作（例如未写入范围转换）后，应调用 `iomap_finish_ioends`。某些文件系统可能希望分摊运行元数据事务的成本，以便在写回后更新时进行批处理。它们还可能要求事务从进程上下文运行，这意味着需要将批处理推迟到工作队列中。iomap ioends 包含一个 `list_head`，以支持批处理。对于一批 ioends，iomap 提供了一些辅助函数来帮助分摊成本：

* `iomap_sort_ioends`：按文件偏移量对列表中的所有 ioends 进行排序。
* ``iomap_ioend_try_merge``: 给定一个不在任何列表中的 ioend 以及一个已排序的 ioend 列表，将尽可能多的列表头部的 ioend 合并到给定的 ioend 中。
  ioend 只有在文件范围和存储地址连续、未写入和共享状态相同以及写入 I/O 结果相同时才能被合并。
  合并后的 ioend 将形成它们自己的列表。
* ``iomap_finish_ioends``: 完成一个可能链接了其他 ioend 的 ioend。

直接 I/O
========

在 Linux 中，直接 I/O 被定义为直接发送到存储而不经过页缓存的文件 I/O。
``iomap_dio_rw`` 函数实现了 O_DIRECT（直接 I/O）读取和写入文件的功能。
```c
ssize_t iomap_dio_rw(struct kiocb *iocb, struct iov_iter *iter,
                     const struct iomap_ops *ops,
                     const struct iomap_dio_ops *dops,
                     unsigned int dio_flags, void *private,
                     size_t done_before);
```

如果文件系统需要在 I/O 发送到存储之前或之后执行额外的工作，可以提供 ``dops`` 参数。
``done_before`` 参数告诉系统请求中已经完成了多少数据传输。
当部分请求已经同步完成时，它用于继续异步处理请求。
如果在调用该函数之前已经启动了 ``iocb`` 的写入操作，则应设置 ``done_before`` 参数。
I/O 的方向由传递的 `iocb` 确定。
`dio_flags` 参数可以设置为以下值的任意组合：

 * `IOMAP_DIO_FORCE_WAIT`：即使 `kiocb` 不是同步的，也要等待 I/O 完成。
 * `IOMAP_DIO_OVERWRITE_ONLY`：对该范围执行纯覆盖操作或失败并返回 `-EAGAIN`。
   这可以被具有复杂未对齐 I/O 写路径的文件系统使用，以提供优化的快速路径来处理未对齐写入。如果可以执行纯覆盖，则无需对同一文件系统块的其他 I/O 进行序列化，因为不存在旧数据暴露或数据丢失的风险。如果无法执行纯覆盖，则文件系统可以执行所需的序列化步骤，以提供对该未对齐 I/O 范围的独占访问，从而安全地进行分配和子块清零。文件系统可以使用此标志尝试减少锁竞争，但需要大量的详细检查才能正确实现。
 * `IOMAP_DIO_PARTIAL`：如果发生页错误，返回已经取得的进展。
   调用者可以处理页错误并重试该操作。如果调用者决定重试该操作，应将之前所有调用的累计返回值作为 `done_before` 参数传递给下一次调用。
这些 `struct kiocb` 标志对于使用 iomap 的直接 I/O 非常重要：

- `IOCB_NOWAIT`：启用 `IOMAP_NOWAIT`
- `IOCB_SYNC`：确保设备在完成调用之前已将数据持久化到磁盘
  对于纯覆盖操作，I/O 可以启用 FUA 发出
- `IOCB_HIPRI`：轮询 I/O 完成情况而不是等待中断
  仅对异步 I/O 有意义，并且只有在整个 I/O 可以作为一个单一的 `struct bio` 发出时才有意义
- `IOCB_DIO_CALLER_COMP`：尝试从调用者的进程上下文运行 I/O 完成处理
  更多详情请参阅 `linux/fs.h`

文件系统应该在 `->read_iter` 和 `->write_iter` 中调用 `iomap_dio_rw`，并在 `->open` 函数中为文件设置 `FMODE_CAN_ODIRECT`
它们不应该设置 `->direct_IO`，因为该选项已被弃用

如果文件系统希望在直接 I/O 完成前执行一些自己的工作，则应调用 `__iomap_dio_rw`。
如果其返回值不是错误指针或空指针，文件系统应在完成其内部工作后将返回值传递给 `iomap_dio_complete`。

返回值
------

`iomap_dio_rw` 可以返回以下之一：

 * 一个非负的已传输字节数
 * `-ENOTBLK`：回退到带缓冲的 I/O
   `iomap` 本身会在无法在发出 I/O 到存储之前使页面缓存失效时返回此值。
   `->iomap_begin` 或 `->iomap_end` 函数也可能返回此值。
 * `-EIOCBQUEUED`：异步直接 I/O 请求已被排队，并将单独完成。
 * 其他任何负的错误代码。

直接读取
--------

直接 I/O 读取会从存储设备发起读取操作到调用者的缓冲区。
在发起读取 I/O 之前，会将页面缓存中的脏部分刷新到存储中。
`->iomap_begin` 的 `flags` 值将是 `IOMAP_DIRECT`，并可能包含以下增强选项的任意组合：

 * `IOMAP_NOWAIT`，如前所述。
调用者通常在调用此函数前以共享模式持有`i_rwsem`

直接写入
---------

直接I/O写入会从调用者的缓冲区启动对存储设备的写入操作。
在启动写入I/O之前，将页缓存中的脏部分刷新到存储中。
在写入I/O前后都会使页缓存失效。
`->iomap_begin`的`flags`值将是`IOMAP_DIRECT | IOMAP_WRITE`，并可能包含以下增强项中的任意组合：

 * `IOMAP_NOWAIT`：如前所述
* `IOMAP_OVERWRITE_ONLY`：不允许分配块和清零部分块
整个文件范围必须映射到一个已写或未写的扩展区域
如果映射未写，并且文件系统无法在不暴露陈旧内容的情况下清零未对齐的区域，则文件I/O范围必须对齐到文件系统的块大小
调用者通常在调用此函数前以共享或独占模式持有`i_rwsem`

`struct iomap_dio_ops`结构体
-----------------------------
```c
struct iomap_dio_ops {
    void (*submit_io)(const struct iomap_iter *iter, struct bio *bio, loff_t file_offset);
    int (*end_io)(struct kiocb *iocb, ssize_t size, int error, unsigned flags);
    struct bio_set *bio_set;
};
```

该结构体的字段如下：

  - `submit_io`：当iomap构造了一个用于请求I/O的`struct bio`对象，并希望将其提交给块设备时，会调用此函数。
如果未提供函数，则直接调用 `submit_bio`。
希望在操作前执行额外工作的文件系统（例如，btrfs 的数据复制）应实现此函数。
- `end_io`：在 `struct bio` 完成后被调用。
此函数应执行写入后转换未写入的范围映射、处理写入失败等操作。
`flags` 参数可以设置为以下组合之一：

    * `IOMAP_DIO_UNWRITTEN`：映射未写入，因此 ioend 应该标记范围已写入。
    * `IOMAP_DIO_COW`：对映射中的空间进行写入需要执行写时复制操作，因此 ioend 应该切换映射。

- `bio_set`：这允许文件系统提供一个自定义的 `bio_set` 用于分配直接 I/O 的 `bio` 对象。
这使得文件系统能够存储每个 `bio` 的附加信息以供私有使用（参考 [链接](https://lore.kernel.org/all/20220505201115.937837-3-hch@lst.de/)）。
如果此字段为 NULL，则使用通用的 `struct bio` 对象。
文件系统如果希望在 I/O 完成后执行额外的工作，应该通过 `->submit_io` 设置一个自定义的 `->bi_end_io` 函数。之后，这个自定义的 endio 函数必须调用 `iomap_dio_bio_end_io` 来完成直接 I/O。

DAX I/O
=======

某些存储设备可以直接映射为内存。这些设备支持一种新的访问模式，称为“fsdax”，允许通过 CPU 和内存控制器进行读取和写入操作。

fsdax 读取
-----------

一个 fsdax 读取操作是从存储设备复制数据到调用者的缓冲区。`->iomap_begin` 的 `flags` 值将被设置为 `IOMAP_DAX`，并可以结合以下任何增强项：

 * `IOMAP_NOWAIT`：如前所述
调用者通常在调用此函数之前以共享模式持有 `i_rwsem`。

fsdax 写入
------------

一个 fsdax 写入操作是从调用者的缓冲区复制数据到存储设备。`->iomap_begin` 的 `flags` 值将被设置为 `IOMAP_DAX | IOMAP_WRITE`，并可以结合以下任何增强项：

 * `IOMAP_NOWAIT`：如前所述
* `IOMAP_OVERWRITE_ONLY`：调用者要求从该映射中执行纯粹的覆盖操作。
这要求文件系统范围映射已经存在，并且类型为 ``IOMAP_MAPPED``，覆盖写入 I/O 请求的整个范围。
如果文件系统无法以允许 iomap 基础设施执行纯覆盖的方式映射此请求，则必须通过返回 ``-EAGAIN`` 使映射操作失败。
调用者通常在调用此函数之前以独占模式持有 ``i_rwsem``。
FSDAX mmap 故障
~~~~~~~~~~~~~~~~~

``dax_iomap_fault`` 函数处理对 FSDAX 存储的读取和写入故障。
对于读取故障，``IOMAP_DAX | IOMAP_FAULT`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
对于写入故障，``IOMAP_DAX | IOMAP_FAULT | IOMAP_WRITE`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
调用者通常持有与调用其 iomap 页缓存对应函数相同的锁。
FSDAX 截断、fallocate 和取消共享
------------------------------------------

对于 FSDAX 文件，提供了以下函数来替换其 iomap 页缓存 I/O 对应函数：
``->iomap_begin`` 的 ``flags`` 参数与页缓存对应函数相同，但增加了 ``IOMAP_DAX``。
* ``dax_file_unshare``
 * ``dax_zero_range``
 * ``dax_truncate_page``

调用者通常持有与调用其 iomap 页缓存对应函数相同的锁。
### Fsdax 去重

实现 ``FIDEDUPERANGE`` ioctl 的文件系统必须调用 ``dax_remap_file_range_prep`` 函数，并传入它们自己的 iomap 读操作。

### 寻找文件

iomap 实现了 ``llseek`` 系统调用的两种迭代模式：

#### SEEK_DATA

``iomap_seek_data`` 函数实现了 ``llseek`` 中的 SEEK_DATA "whence" 值。
``IOMAP_REPORT`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
对于未写入的映射，将搜索页缓存。
页缓存中具有已映射 folio 和这些 folio 内的最新 fsblocks 的区域将被报告为数据区域。
调用者通常在调用此函数之前以共享模式持有 ``i_rwsem``。

#### SEEK_HOLE

``iomap_seek_hole`` 函数实现了 ``llseek`` 中的 SEEK_HOLE "whence" 值。
``IOMAP_REPORT`` 将作为 ``flags`` 参数传递给 ``->iomap_begin``。
对于未写入的映射，将搜索页缓存。
页面缓存中没有映射 folio 的区域，或者 folio 内的 !uptodate fsblock 将被报告为稀疏空洞区域。
调用者通常在调用此函数之前以共享模式持有 `i_rwsem`。

交换文件激活
=============

`iomap_swapfile_activate` 函数查找文件中所有基页对齐的区域，并将它们设置为交换空间。
文件将在激活前执行 `fsync()` 操作。
`IOMAP_REPORT` 将作为 `flags` 参数传递给 `->iomap_begin`。
所有映射必须是已映射或未写入的；不能是脏数据或共享的，并且不能跨越多个块设备。
调用者必须以独占模式持有 `i_rwsem`；这已经由 `swapon` 提供。

文件空间映射报告
=================

iomap 实现了两种文件空间映射系统调用。

FS_IOC_FIEMAP
-------------

`iomap_fiemap` 函数按照 `FS_IOC_FIEMAP` ioctl 指定的格式向用户空间导出文件范围映射。
`IOMAP_REPORT` 将作为 `flags` 参数传递给 `->iomap_begin`。
调用者通常在调用此函数前以共享模式持有 ``i_rwsem``。
FIBMAP（已弃用）
-------------------

``iomap_bmap`` 实现了 FIBMAP。
调用约定与 FIEMAP 相同。
此函数仅提供以保持对在转换前实现了 FIBMAP 的文件系统的兼容性。
此 ioctl 已弃用；**不要**为没有 FIBMAP 实现的文件系统添加 FIBMAP 实现。
调用者可能应该在调用此函数前以共享模式持有 ``i_rwsem``，但这一点并不明确。
