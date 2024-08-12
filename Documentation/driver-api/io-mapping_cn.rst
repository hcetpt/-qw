========================
I/O 映射函数
========================

API
===

`linux/io-mapping.h` 中的 I/O 映射函数提供了一种高效地将 I/O 设备的小区域映射到 CPU 的抽象。最初的应用是在 32 位处理器上支持大图形窗口，因为 `ioremap_wc` 不能静态地将整个窗口映射到 CPU，因为它会消耗太多的内核地址空间。创建映射对象的过程如下：

```c
struct io_mapping *io_mapping_create_wc(unsigned long base,
						unsigned long size)
```

其中 `'base'` 是要使其可映射的区域的总线地址，而 `'size'` 表示要启用的映射区域有多大。两者都是以字节为单位。

这个 `_wc` 变体提供了一个只能与 `io_mapping_map_atomic_wc()`、`io_mapping_map_local_wc()` 或 `io_mapping_map_wc()` 一起使用的映射。

使用此映射对象，可以根据需要临时或长期映射单个页面。当然，临时映射更有效率。它们有两种形式：

```c
void *io_mapping_map_local_wc(struct io_mapping *mapping,
				      unsigned long offset)

void *io_mapping_map_atomic_wc(struct io_mapping *mapping,
				       unsigned long offset)
```

`'offset'` 是定义的映射区域内的偏移量。访问超出创建函数中指定的区域的地址会导致未定义的结果。如果偏移量不是页对齐的，结果也是未定义的。返回值指向 CPU 地址空间中的单个页面。

这个 `_wc` 变体返回一个写合并映射到该页，并且只能与通过 `io_mapping_create_wc()` 创建的映射一起使用。

临时映射仅在调用者的上下文中有效。不能保证映射是全局可见的。

`io_mapping_map_local_wc()` 在 x86 32 位架构上有副作用，因为它禁用了迁移以使映射代码工作。没有调用者可以依赖这个副作用。

`io_mapping_map_atomic_wc()` 有禁用抢占和页错误的副作用。不要在新代码中使用它。请改用 `io_mapping_map_local_wc()`。

由于映射代码使用栈来跟踪嵌套映射，因此必须按相反的顺序撤销嵌套映射：

```c
addr1 = io_mapping_map_local_wc(map1, offset1);
addr2 = io_mapping_map_local_wc(map2, offset2);
..
io_mapping_unmap_local(addr2);
io_mapping_unmap_local(addr1);
```

可以通过以下函数释放映射：

```c
void io_mapping_unmap_local(void *vaddr)
void io_mapping_unmap_atomic(void *vaddr)
```

`'vaddr'` 必须是上次 `io_mapping_map_local_wc()` 或 `io_mapping_map_atomic_wc()` 调用返回的值。这将取消指定的映射并撤销映射函数的副作用。

如果您需要在持有映射时休眠，可以使用常规变体，尽管这可能会慢得多：

```c
void *io_mapping_map_wc(struct io_mapping *mapping,
				unsigned long offset)
```

这与 `io_mapping_map_atomic/local_wc()` 类似，但没有副作用，并且指针是全局可见的。
这些映射通过以下函数释放：

```c
void io_mapping_unmap(void *vaddr)
```

这用于通过 `io_mapping_map_wc()` 映射的页面。

在驱动程序关闭时，必须释放 `io_mapping` 对象：

```c
void io_mapping_free(struct io_mapping *mapping)
```
