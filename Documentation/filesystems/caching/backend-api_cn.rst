SPDX 许可证标识符: GPL-2.0

=================
缓存后端 API
=================

FS-Cache 系统提供了一个 API，通过该 API 可以向 FS-Cache 提供实际的缓存，然后 FS-Cache 将这些缓存提供给网络文件系统和其他感兴趣的方。此 API 被以下代码使用：

	#include <linux/fscache-cache.h>

概述
========

与 API 的交互处理分为三个级别：缓存、卷和数据存储，并且每个级别都有其对应的 cookie 对象类型：

	=======================	=======================
	COOKIE			C 类型
	=======================	=======================
	缓存 cookie		struct fscache_cache
	卷 cookie		struct fscache_volume
	数据存储 cookie	struct fscache_cookie
	=======================	=======================

cookie 用于向缓存提供一些文件系统数据、管理状态以及在访问期间固定缓存，此外还作为 API 函数的参考点。每个 cookie 都有一个调试 ID，该 ID 包含在跟踪点中，以便更容易关联跟踪信息。需要注意的是，调试 ID 是从递增计数器分配的，并且最终会回绕。缓存后端和网络文件系统都可以请求缓存 cookie —— 如果它们请求同一个名称的缓存 cookie，则会得到相同的 cookie。然而，卷 cookie 和数据 cookie 只有在文件系统的请求下才会创建。

缓存 cookie
=============

缓存在 API 中由缓存 cookie 表示。这些对象的类型为：

	struct fscache_cache {
		void		*cache_priv;
		unsigned int	debug_id;
		char		*name;
		..
	};

有几个字段可能是缓存后端感兴趣的。`debug_id` 可以在跟踪中用于匹配引用相同缓存的行，而 `name` 是注册缓存时使用的名称。`cache_priv` 成员是由缓存在线时提供的私有数据。其他字段用于内部使用。

注册缓存
===================

当缓存后端希望将缓存上线时，它应首先注册缓存名称，这将为其分配一个缓存 cookie。这是通过以下函数完成的：

	struct fscache_cache *fscache_acquire_cache(const char *name);

这将查找并可能创建一个缓存 cookie。缓存 cookie 可能已经由寻找它的网络文件系统创建，在这种情况下，将使用那个缓存 cookie。如果缓存 cookie 没有被其他缓存使用，它将进入准备状态；否则返回忙状态。

如果成功，缓存后端可以开始设置缓存。如果初始化失败，缓存后端应该调用：

	void fscache_relinquish_cache(struct fscache_cache *cache);

以重置并丢弃 cookie。

将缓存上线
=======================

一旦缓存设置完成，可以通过调用以下函数将其上线：

	int fscache_add_cache(struct fscache_cache *cache,
			      const struct fscache_cache_ops *ops,
			      void *cache_priv);

这将缓存操作表指针和缓存私有数据存储到缓存 cookie 中，并将缓存移至活动状态，从而允许访问发生。

撤除缓存服务
================================

缓存后端可以通过调用以下函数撤除缓存的服务：

	void fscache_withdraw_cache(struct fscache_cache *cache);

这将缓存移至撤除状态，以阻止新的缓存级和卷级访问启动，并等待正在进行的缓存级访问完成。

然后，缓存必须遍历其拥有的数据存储对象，并告诉 fscache 将其撤除，对每个对象所属的 cookie 调用：

	void fscache_withdraw_cookie(struct fscache_cookie *cookie);

这将指定的 cookie 排队进行撤除。这会被委托给工作队列。缓存后端可以通过调用：

	void fscache_wait_for_objects(struct fscache_cache *cache);

来等待完成。

一旦所有 cookie 被撤除，缓存后端可以撤除所有卷，调用：

	void fscache_withdraw_volume(struct fscache_volume *volume);

来告诉 fscache 卷已被撤除。这将在返回前等待卷上所有正在进行的访问完成。
当缓存完全撤回时，应通过调用以下函数通知 fscache：

```c
void fscache_relinquish_cache(struct fscache_cache *cache);
```

以清除 cookie 中的字段并丢弃调用者对该 cookie 的引用。

### 卷 Cookie

在缓存中，数据存储对象被组织成逻辑卷。这些在 API 中表示为以下类型的对象：

```c
struct fscache_volume {
    struct fscache_cache       *cache;
    void                       *cache_priv;
    unsigned int               debug_id;
    char                       *key;
    unsigned int               key_hash;
    ..
    u8                         coherency_len;
    u8                         coherency[];
};
```

这里有几个字段对缓存后端来说是感兴趣的：

* `cache` - 父缓存 Cookie
* `cache_priv` - 缓存可以存放私有数据的地方
* `debug_id` - 用于跟踪点日志记录的调试 ID
* `key` - 一个不包含 '/' 字符的可打印字符串，代表卷的索引键。该键以 NUL 结尾，并填充至 4 字节的倍数
* `key_hash` - 索引键的哈希值。无论 CPU 架构和字节序如何，该哈希值应保持一致
* `coherency` - 在卷绑定到缓存时需要检查的一段一致性数据
* `coherency_len` - 一致性缓冲区中的数据量
```
数据存储 Cookie
====================

一个卷是一组逻辑数据存储对象，每个对象在网络文件系统中由一个 Cookie 表示。Cookie 在 API 中表示为以下类型的对象：

```c
struct fscache_cookie {
    struct fscache_volume       *volume;     // 父卷 Cookie
    void                *cache_priv;      // 缓存存放私有数据的地方
    unsigned long            flags;         // 位标志集合
    unsigned int            debug_id;      // 用于跟踪点记录的调试 ID
    unsigned int            inval_counter; // Cookie 被无效化的次数
    loff_t                object_size;    // 对象大小
    u8                advice;           // 建议
    u32                key_hash;        // 键的哈希值
    u8                key_len;          // 键长度
    u8                aux_len;          // 辅助数据长度
    ...
};
```

对缓存后端而言，Cookie 中感兴趣的字段包括：

   * ``volume`` - 父卷 Cookie
   * ``cache_priv`` - 缓存存放私有数据的地方
   * ``flags`` - 一组位标志，包括：
   
       * FSCACHE_COOKIE_NO_DATA_TO_READ - 没有数据可读取，因为该 Cookie 已被创建或失效
       * FSCACHE_COOKIE_NEEDS_UPDATE - 一致性数据和/或对象大小已更改，需要提交
       * FSCACHE_COOKIE_LOCAL_WRITE - 网络文件系统的数据已被本地修改，因此缓存对象可能与服务器不一致
       * FSCACHE_COOKIE_HAVE_DATA - 如果后端成功将数据存储到缓存中，则应设置此标志
       * FSCACHE_COOKIE_RETIRED - 当释放该 Cookie 时，其已失效，缓存数据应被丢弃
   * ``debug_id`` - 用于跟踪点记录的调试 ID
   * ``inval_counter`` - Cookie 被无效化的次数
* ``advice`` - 关于如何使用 cookie 的信息
* ``key_hash`` - 索引键的哈希值。这应该与 CPU 架构和字节序无关，始终相同。
* ``key_len`` - 索引键的长度
* ``aux_len`` - 一致性数据缓冲区的长度

每个 cookie 都有一个索引键，这个索引键可以内联存储在 cookie 中或存储在其他地方。可以通过调用以下函数获取指向该索引键的指针：

```c
void *fscache_get_key(struct fscache_cookie *cookie);
```

索引键是一个二进制块，其存储空间被填充到 4 字节的倍数。

每个 cookie 还有一个用于一致性数据的缓冲区。这个缓冲区也可以是内联的或从 cookie 中分离出来的，并且可以通过调用以下函数获得指向该缓冲区的指针：

```c
void *fscache_get_aux(struct fscache_cookie *cookie);
```

### Cookie 计数
数据存储 cookie 被计数，以此来阻止缓存撤销完成，直到所有对象都被销毁。以下是提供给缓存以处理这些情况的函数：

```c
void fscache_count_object(struct fscache_cache *cache);
void fscache_uncount_object(struct fscache_cache *cache);
void fscache_wait_for_objects(struct fscache_cache *cache);
```

计数函数记录了缓存中一个对象的分配，而未计数函数则记录其销毁。警告：当未计数函数返回时，缓存可能已经被销毁。

等待函数可以在撤销过程中使用，以等待 fscache 完成撤销缓存中的所有对象。当它完成时，将不会有剩余的对象引用缓存对象或任何卷对象。

### 缓存管理 API

缓存后端通过提供一组操作表来实现缓存管理 API，fscache 可以使用这些操作来管理缓存的各个方面。这些操作保存在一个名为 `fscache_cache_ops` 的结构体中：

```c
struct fscache_cache_ops {
    const char *name;
    ...
};
```

这包含了一个可打印的缓存后端驱动名称以及一些方法指针，允许 fscache 请求对缓存进行管理：

* 设置卷 cookie（可选）：

```c
void (*acquire_volume)(struct fscache_volume *volume);
```

当创建卷 cookie 时会调用此方法。调用者持有缓存级别的访问锁定，以防止缓存在此期间消失。此方法应设置访问缓存中卷所需的资源，并且在完成之前不应返回。

如果成功，它可以将 `cache_priv` 设置为自己的数据。
* 清理卷Cookie [可选] ::

       void (*free_volume)(struct fscache_volume *volume);

     当一个卷Cookie被释放时，如果设置了 `cache_priv`，将调用此方法。

* 在缓存中查找Cookie [必需] ::

     bool (*lookup_cookie)(struct fscache_cookie *cookie);

     此方法用于查找/创建访问数据存储所需的资源。它在具有卷级访问锁的工作者线程中被调用，以防止缓存中的卷被撤销。
     如果成功，则应返回 `true`，否则返回 `false`。如果返回 `false`，则会调用 `withdraw_cookie` 操作（见下文）。
     如果查找失败，但对象仍可以被创建（例如，该对象以前未被缓存过），则可以调用以下函数来让网络文件系统继续进行下载操作，同时缓存后端处理创建任务：
     
         void fscache_cookie_lookup_negative(struct fscache_cookie *cookie);
     
     如果成功，可以设置 `cookie->cache_priv`。

* 撤销没有访问计数的Cookie [必需] ::

     void (*withdraw_cookie)(struct fscache_cookie *cookie);

     此方法用于从服务中撤销一个Cookie。当Cookie被网络文件系统放弃、被缓存后端撤销或因长时间未使用而被关闭时，将调用此方法。
     调用者不持有任何访问锁，但在不可重入的工作项中调用以管理各种撤销方式之间的竞争。
     如果相关数据要从缓存中移除，Cookie将被设置 `FSCACHE_COOKIE_RETIRED` 标志。

* 更改数据存储对象的大小 [必需] ::

     void (*resize_cookie)(struct netfs_cache_resources *cres, loff_t new_size);

     此方法用于通知缓存后端由于本地截断而导致的网络文件大小变化。缓存后端应在返回前完成所有必要的更改，因为这是在网络文件系统的inode互斥锁下进行的。
     调用者持有一个Cookie级的访问锁，以防止与撤销的竞争，并且网络文件系统必须标记Cookie为使用中，以防止垃圾回收或清理删除任何资源。
* 使数据存储对象失效 [强制] ::

    bool (*invalidate_cookie)(struct fscache_cookie *cookie);

    当网络文件系统检测到第三方修改或本地执行O_DIRECT写入时，会调用此函数。这请求缓存后端丢弃该对象在缓存中的所有数据并重新开始。如果成功应返回true，否则返回false。

    调用时，新的I/O操作会被阻塞。一旦缓存准备好再次接受I/O操作，后端应该通过调用以下函数来解除阻塞 ::

        void fscache_resume_after_invalidation(struct fscache_cookie *cookie);

    如果此方法返回false，则将取消对此cookie的缓存。

* 准备对缓存进行本地修改 [强制] ::

    void (*prepare_to_write)(struct fscache_cookie *cookie);

    当网络文件系统发现由于本地写入或截断需要修改缓存内容时，会调用此方法。这给了缓存一个机会来记录缓存对象可能与服务器不一致，并且可能需要稍后写回。如果未正确提交，在后续重绑定时可能会导致缓存数据被废弃。

* 开始netfs库的操作 [强制] ::

    bool (*begin_operation)(struct netfs_cache_resources *cres,
                            enum fscache_want_state want_state);

    当设置I/O操作（读取、写入或调整大小）时，会调用此方法。调用者持有cookie上的访问锁，并且必须已经标记cookie为使用中。

    如果可以，后端应该将其需要保留的任何资源附加到netfs_cache_resources对象上并返回true。
    如果无法完成设置，则应返回false。

    参数want_state指示调用者需要缓存对象处于的状态以及它希望在此操作期间执行的操作：

        * ``FSCACHE_WANT_PARAMS`` - 调用者仅想访问缓存对象参数；它还不需要进行数据I/O
        * ``FSCACHE_WANT_READ`` - 调用者想要读取数据
        * ``FSCACHE_WANT_WRITE`` - 调用者想要写入或调整缓存对象的大小

    注意，如果cookie仍在创建过程中，其cache_priv中可能还没有任何东西附加。
数据 I/O API
============

缓存后端通过 netfs 库中的 `struct netfs_cache_ops` 提供数据 I/O API，并通过上述描述的 `begin_operation` 方法将其附加到 `struct netfs_cache_resources`。
详情请参阅 [Documentation/filesystems/netfs_library.rst](Documentation/filesystems/netfs_library.rst)。

杂项函数
=======================

FS-Cache 提供了一些缓存后端可能使用的工具：

- 记录缓存中发生的 I/O 错误：

```c
void fscache_io_error(struct fscache_cache *cache);
```

这会告诉 FS-Cache 缓存中发生了 I/O 错误。这将阻止在缓存上启动任何新的 I/O 操作。但是，实际上并不会从系统中撤回该缓存，需要单独进行此操作。

- 记录由于失败而停止对某个 cookie 的缓存：

```c
void fscache_caching_failed(struct fscache_cookie *cookie);
```

这表示缓存过程中某个 cookie 的缓存出现了问题，例如，底层存储未能创建或失效操作失败。在这种情况下，在缓存重置之前不应再对该 cookie 执行任何进一步的 I/O 操作。

- 计数 I/O 请求：

```c
void fscache_count_read(void);
void fscache_count_write(void);
```

这些函数记录从/向缓存读取和写入的数据。统计数字显示在 `/proc/fs/fscache/stats` 中。

- 计数空间不足错误：

```c
void fscache_count_no_write_space(void);
void fscache_count_no_create_space(void);
```

这些函数记录缓存中的 ENOSPC 错误，分为数据写入失败和文件系统对象创建失败（例如 `mkdir`）。

- 计数被清理的对象：

```c
void fscache_count_culled(void);
```

这个函数记录一个对象被清理的情况。

- 从一组缓存资源中获取 cookie：

```c
struct fscache_cookie *fscache_cres_cookie(struct netfs_cache_resources *cres);
```

从缓存资源中获取指向 cookie 的指针。如果未设置 cookie，则可能会返回 NULL。

API 函数参考
======================

.. kernel-doc:: include/linux/fscache-cache.h
