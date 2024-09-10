SPDX 许可证标识符: GPL-2.0

==============================
网络文件系统缓存 API
==============================

Fscache 提供了一个 API，使得网络文件系统可以利用本地缓存设施。API 围绕以下几个原则进行组织：

1. 缓存逻辑上被组织为卷和这些卷中的数据存储对象。
2. 卷和数据存储对象由不同类型的 cookie 表示。
3. cookie 有键来区分它们的同级对象。
4. cookie 有连贯性数据，允许缓存确定缓存的数据是否仍然有效。
5. 尽可能地异步执行 I/O 操作。

使用此 API 的方法如下：

	#include <linux/fscache.h>

本文档包含以下章节：

1. 概览
2. 卷注册
3. 数据文件注册
4. 声明一个 cookie 正在使用中
5. 调整数据文件大小（截断）
6. 数据 I/O API
7. 数据文件连贯性
8. 数据文件失效
9. 写回资源管理
10. 本地修改的缓存
11. 页面释放与失效

概览
========

从网络文件系统的角度来看，fscache 层次结构分为两个级别。上层表示“卷”，下层表示“数据存储对象”。这两者分别由两种类型的 cookie 表示，以下称为“卷 cookie”和“cookie”。

网络文件系统通过使用卷键获取一个卷的卷 cookie，卷键代表定义该卷的所有信息（例如，单元格名称或服务器地址、卷 ID 或共享名称）。这必须被渲染为可打印的字符串，并且可以用作目录名（即不能包含 '/' 字符并且不应以 '.' 开头）。最大名称长度比文件名组件的最大长度少一个字符（允许缓存后端使用一个字符用于其自身目的）。

文件系统通常对每个超级块有一个卷 cookie。

然后，文件系统使用对象键为该卷内的每个文件获取一个 cookie。对象键是二进制块，只需在其父卷内唯一即可。缓存后端负责将二进制块转换为其可以使用的内容，并可能使用哈希表、树或其他方式来提高其查找对象的能力。这对网络文件系统来说是透明的。
文件系统通常会为每个inode分配一个cookie，并在iget时获取它，在驱逐cookie时释放它。一旦拥有一个cookie，文件系统需要标记该cookie为使用中。这将导致fscache向缓存后端发送请求，在后台查找或创建资源以检查其一致性，并在必要时标记对象为修改状态。

文件系统通常会在其文件打开例程中“使用”cookie，并在文件释放时“不使用”cookie。它还需要在本地截断cookie时使用cookie。此外，当页缓存变脏时也需要使用cookie，并在回写完成后不再使用它。这一点稍微有些复杂，但已为此做了准备。

在对cookie执行读取、写入或调整大小操作时，文件系统必须首先开始一个操作。这将资源复制到一个临时结构中，并在缓存中添加额外的固定标识以阻止缓存回收过程中拆解正在使用的结构。然后可以发出实际的操作，并在完成时检测冲突的失效情况。

文件系统预计会使用netfslib来访问缓存，但这实际上并不是必需的，它可以使用fscache的I/O API直接进行访问。

### 卷注册

网络文件系统的第一个步骤是为其想要访问的卷获取一个卷cookie：

```c
struct fscache_volume *
fscache_acquire_volume(const char *volume_key,
		       const char *cache_name,
		       const void *coherency_data,
		       size_t coherency_len);
```

此函数使用指定的卷键作为名称创建一个卷cookie，并记录一致性数据。
卷键必须是一个可打印的字符串，其中不包含'/'字符。它应该以文件系统的名称开头，并且长度不应超过254个字符。它应该唯一地表示该卷，并将与缓存中存储的数据进行匹配。

调用者还可以指定要使用的缓存名称。如果指定了缓存名称，fscache将查找或创建一个具有该名称的缓存cookie，并在该缓存上线时使用它。如果没有指定缓存名称，则会使用手头的第一个缓存并将其名称设置为该名称。

指定的一致性数据将存储在cookie中，并与磁盘上存储的一致性数据进行匹配。如果未提供数据，数据指针可以为NULL。如果一致性数据不匹配，整个缓存卷将被作废。
此函数可能会返回如EBUSY之类的错误，如果卷键已被获取的卷使用；或者在分配失败时返回ENOMEM。它也可能在fscache未启用的情况下返回一个NULL卷句柄。将NULL句柄传递给任何需要卷句柄的函数是安全的，这会导致该函数不做任何操作。
当网络文件系统完成对某个卷的操作后，应通过调用以下函数来释放该卷：

```c
void fscache_relinquish_volume(struct fscache_volume *volume,
			       const void *coherency_data,
			       bool invalidate);
```

这将导致卷被提交或移除，并且如果已密封，则一致性数据将被设置为提供的值。一致性数据的长度必须与获取卷时指定的长度匹配。请注意，在释放卷之前，必须先释放该卷中的所有数据句柄。

### 数据文件注册

一旦网络文件系统获得了一个卷句柄，就可以使用它来获取用于数据存储的数据句柄：

```c
struct fscache_cookie *
fscache_acquire_cookie(struct fscache_volume *volume,
		       u8 advice,
		       const void *index_key,
		       size_t index_key_len,
		       const void *aux_data,
		       size_t aux_data_len,
		       loff_t object_size);
```

这会在卷中使用指定的索引键创建数据句柄。索引键是一个二进制块，其长度由给定值确定，并且在卷内必须是唯一的。这个键会被保存到数据句柄中。内容没有限制，但其长度不应超过最大文件名长度的大约四分之三以允许编码。
调用者还应在aux_data中传递一致性数据。将分配一个大小为aux_data_len的缓冲区，并将一致性数据复制进去。假设这个大小是不变的。一致性数据用于检查缓存中数据的有效性。提供了可以更新一致性数据的函数。
还应提供要缓存的对象的文件大小。这可能用于修剪数据，并会与一致性数据一起存储。
此函数永远不会返回错误，但在分配失败或fscache未启用的情况下可能会返回NULL数据句柄。将NULL卷句柄传递给任何需要它的函数是安全的，并将返回的NULL数据句柄传递给这些函数也是安全的。这将导致该函数不做任何操作。
当网络文件系统完成对某个数据句柄的操作后，应通过调用以下函数来释放它：

```c
void fscache_relinquish_cookie(struct fscache_cookie *cookie,
			       bool retire);
```

这将导致fscache要么提交支持该数据句柄的存储，要么删除它。

### 标记数据句柄为正在使用

一旦网络文件系统获得了某个数据句柄，该文件系统应在打算使用该数据句柄时（通常在打开文件时）通知fscache，并在使用完毕后（通常在关闭文件时）通知fscache：

```c
void fscache_use_cookie(struct fscache_cookie *cookie,
			bool will_modify);
void fscache_unuse_cookie(struct fscache_cookie *cookie,
			  const void *aux_data,
			  const loff_t *object_size);
```

`use` 函数告诉fscache它将使用该数据句柄，并且还指示用户是否打算本地修改内容。如果尚未完成，这将触发缓存后端去收集访问/存储缓存中的数据所需的资源。这是在后台完成的，因此在函数返回时可能尚未完成。
*unuse* 函数表示文件系统已经完成了对 cookie 的使用。它可选地更新存储的相干数据和对象大小，然后减少使用中的计数器。当最后一个用户不再使用该 cookie 时，它会被安排进行垃圾回收。如果在短时间内未被重用，资源将被释放以减少系统资源消耗。在可以访问 cookie 进行读取、写入或调整大小之前，必须将其标记为使用中，并且在页面缓存中有脏数据的情况下必须保持使用中的标记，以避免在进程退出期间尝试打开文件时出现错误。

请注意，使用中的标记是累积的。对于每次将 cookie 标记为使用中，都必须相应地取消使用。

数据文件的调整大小（截断）
==========================

如果通过截断操作本地调整网络文件系统的文件大小，应调用以下函数来通知缓存：

```c
void fscache_resize_cookie(struct fscache_cookie *cookie, loff_t new_size);
```

调用者必须首先标记 cookie 为使用中。传递 cookie 和新大小，并同步调整缓存大小。这通常会在 `->setattr()` inode 操作下，在 inode 锁保护下调用。

数据 I/O API
===========

要直接通过 cookie 执行数据 I/O 操作，可以使用以下函数：

```c
int fscache_begin_read_operation(struct netfs_cache_resources *cres, struct fscache_cookie *cookie);
int fscache_read(struct netfs_cache_resources *cres, loff_t start_pos, struct iov_iter *iter, enum netfs_read_from_hole read_hole, netfs_io_terminated_t term_func, void *term_func_priv);
int fscache_write(struct netfs_cache_resources *cres, loff_t start_pos, struct iov_iter *iter, netfs_io_terminated_t term_func, void *term_func_priv);
```

*begin* 函数设置一个操作，将所需资源附加到从 cookie 获取的缓存资源块中。假设它没有返回错误（例如，如果给定空 cookie，它将返回 `-ENOBUFS`，否则不做任何操作），则可以发出其他两个函数之一。

*read* 和 *write* 函数发起直接 I/O 操作。两者都需要先前设置的缓存资源块、指示起始文件位置的信息以及描述缓冲区并指示数据量的 I/O 迭代器。

读取函数还接受一个参数，用于指示如何处理磁盘内容中的部分填充区域（空洞）。这可能是忽略它、跳过初始空洞并在缓冲区中放置零或返回错误。

读取和写入函数还可以接受一个可选的终止函数，在操作完成后运行：

```c
typedef void (*netfs_io_terminated_t)(void *priv, ssize_t transferred_or_error, bool was_async);
```

如果提供了终止函数，则异步执行操作，并在完成时调用终止函数。如果没有提供，则同步执行操作。请注意，在异步情况下，操作可能在函数返回前就已经完成。

读取和写入函数在完成时结束操作，并解除任何固定资源的关联。
读取操作将在操作进行过程中如果出现失效时以`ESTALE`失败。

数据文件一致性
===============

为了请求更新 cookie 上的一致性数据和文件大小，应调用以下函数：

```c
void fscache_update_cookie(struct fscache_cookie *cookie,
                           const void *aux_data,
                           const loff_t *object_size);
```

这将更新 cookie 的一致性数据和/或文件大小。

数据文件失效
==================

有时需要使包含数据的对象失效。通常在服务器通知网络文件系统远程第三方更改时需要这样做，此时文件系统必须丢弃该文件的状态和缓存数据，并从服务器重新加载。

为了指示应使缓存对象失效，应调用以下函数：

```c
void fscache_invalidate(struct fscache_cookie *cookie,
                        const void *aux_data,
                        loff_t size,
                        unsigned int flags);
```

这会增加 cookie 中的失效计数，使正在进行的读取操作以 `-ESTALE` 失败，根据提供的信息设置一致性数据和文件大小，阻止 cookie 上的新 I/O 操作，并调度缓存以清除旧数据。

失效操作在一个工作线程中异步运行，以避免过多阻塞。

写回资源管理
=====================

为了从网络文件系统的写回中向缓存写入数据，修改时（例如当页面被标记为脏页）需要锁定所需的缓存资源，因为不可能在一个退出的线程中打开文件。

为此提供了以下功能：

1. 提供了一个索引节点标志 `I_PINNING_FSCACHE_WB`，表示该索引节点持有的 cookie 正在使用中。只有在持有索引节点锁的情况下才能更改此标志。
2. 在 `writeback_control` 结构体中设置一个标志 `unpinned_fscache_wb`，如果 `__writeback_single_inode()` 因所有脏页被清除而清除了 `I_PINNING_FSCACHE_WB` 标志，则该标志会被设置。

为了支持这些功能，提供了以下函数：

```c
bool fscache_dirty_folio(struct address_space *mapping,
                         struct folio *folio,
                         struct fscache_cookie *cookie);
void fscache_unpin_writeback(struct writeback_control *wbc,
                             struct fscache_cookie *cookie);
void fscache_clear_inode_writeback(struct fscache_cookie *cookie,
                                   struct inode *inode,
                                   const void *aux);
```

`fscache_dirty_folio` 函数预期在文件系统的 `dirty_folio` 地址空间操作中调用。如果 `I_PINNING_FSCACHE_WB` 标志未设置，它会设置该标志并增加 cookie 的使用计数（调用者必须已经调用了 `fscache_use_cookie()`）。
* unpin 函数旨在从文件系统的 `write_inode` 超级块操作中调用。如果在写回控制结构中的 unpinned_fscache_wb 已设置，则它会在写入后通过取消使用 cookie 来完成清理工作。
* clear 函数旨在从网络文件系统的 `evict_inode` 超级块操作中调用。它必须在 `truncate_inode_pages_final()` 之后但 `clear_inode()` 之前被调用。这会清理任何悬而未决的 `I_PINNING_FSCACHE_WB`。同时允许更新一致性数据。

本地修改的缓存
===============
如果一个网络文件系统有本地修改的数据并希望将其写入缓存，它需要标记这些页面以表明正在进行写入，并且如果标记已经存在，则需要等待其被移除（可能是由于已经有正在进行的操作）。这可以防止对缓存中同一存储位置的多个竞争性直接 I/O 写入。
首先，网络文件系统应该通过如下方法确定是否可用缓存：

```c
bool caching = fscache_cookie_enabled(cookie);
```

如果要尝试缓存，应使用网络文件系统帮助库提供的以下函数来等待和标记页面：

```c
void set_page_fscache(struct page *page);
void wait_on_page_fscache(struct page *page);
int wait_on_page_fscache_killable(struct page *page);
```

一旦范围内的所有页面都被标记，网络文件系统可以请求 fscache 安排对该区域的写入：

```c
void fscache_write_to_cache(struct fscache_cookie *cookie,
                            struct address_space *mapping,
                            loff_t start, size_t len, loff_t i_size,
                            netfs_io_terminated_t term_func,
                            void *term_func_priv,
                            bool caching);
```

如果在此点之前发生错误，可以通过调用以下函数来移除标记：

```c
void fscache_clear_page_bits(struct address_space *mapping,
                             loff_t start, size_t len,
                             bool caching);
```

在这些函数中，传递了一个指向源页面所附着的映射的指针，start 和 len 指示将要写入的区域大小（不一定需要对齐到页面边界，但在底层文件系统上必须对齐到直接 I/O 边界）。caching 参数指示是否跳过缓存，如果为 false，则这些函数不做任何事情。

写入函数还需要一些额外参数：表示要写入的缓存对象的 cookie，i_size 表示网络文件系统的大小，term_func 表示一个可选的完成函数，该函数将接收 term_func_priv 以及错误或已写入的数量。

请注意，写入函数总是异步运行，并且在调用 term_func 之前会取消所有页面的标记。

页面释放与失效
=================
fscache 跟踪我们是否已经为刚刚创建的缓存对象在缓存中有任何数据。它知道在进行写入并且页面被虚拟内存管理系统释放之前不需要读取任何内容，之后它必须查找缓存。

为了通知 fscache 页面可能已经在缓存中，应从 `release_folio` 地址空间操作中调用以下函数：

```c
void fscache_note_page_release(struct fscache_cookie *cookie);
```

如果页面已被释放（即 release_folio 返回 true）。

页面释放和页面失效还应等待页面上的任何标记，以表明正在进行直接 I/O 写入：

```c
void wait_on_page_fscache(struct page *page);
int wait_on_page_fscache_killable(struct page *page);
```

API 函数参考
=============
.. kernel-doc:: include/linux/fscache.h
