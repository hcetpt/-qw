内存保护键提供了一种实施基于页面的保护机制的方法，但当应用程序更改保护域时不需要修改页表。
Pkeys 用户空间（PKU）是一项可在以下设备上找到的功能：
        * Intel 服务器 CPU，Skylake 及以后版本
        * Intel 客户端 CPU，Tiger Lake（第 11 代 Core）及以后版本
        * 未来的 AMD CPU

Pkeys 通过将每个页表条目中的 4 个先前保留位专门用于“保护键”来工作，这提供了 16 种可能的键。
每个键的保护由每个 CPU 的用户可访问寄存器（PKRU）定义。这些寄存器是 32 位的，并为 16 个键中的每一个存储两位（访问禁用和写入禁用）。
由于 PKRU 是一个 CPU 寄存器，因此它本质上是线程本地的，这意味着每个线程可能拥有一组与所有其他线程不同的保护。
有两个指令（RDPKRU/WRPKRU）用于读取和写入寄存器。此功能仅在 64 位模式下可用，尽管理论上在 PAE PTE 中有空间。这些权限只在数据访问时执行，并且对指令获取没有影响。

### 系统调用

有三个直接与 pkeys 交互的系统调用：

```c
int pkey_alloc(unsigned long flags, unsigned long init_access_rights)
int pkey_free(int pkey);
int pkey_mprotect(unsigned long start, size_t len,
		  unsigned long prot, int pkey);
```

在使用 pkey 之前，必须首先通过 `pkey_alloc()` 分配它。应用程序可以直接调用 WRPKRU 指令以更改覆盖键的内存的访问权限。在这个例子中，WRPKRU 被一个名为 `pkey_set()` 的 C 函数封装：

```c
int real_prot = PROT_READ|PROT_WRITE;
pkey = pkey_alloc(0, PKEY_DISABLE_WRITE);
ptr = mmap(NULL, PAGE_SIZE, PROT_NONE, MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
ret = pkey_mprotect(ptr, PAGE_SIZE, real_prot, pkey);
// 应用程序在此运行
```

现在，如果应用程序需要更新 'ptr' 处的数据，它可以获取访问权限，进行更新，然后移除其写访问权限：

```c
pkey_set(pkey, 0); // 清除 PKEY_DISABLE_WRITE
*ptr = foo; // 分配某个值
pkey_set(pkey, PKEY_DISABLE_WRITE); // 再次设置 PKEY_DISABLE_WRITE
```

当它释放内存时，也将释放 pkey，因为它不再被使用：

```c
munmap(ptr, PAGE_SIZE);
pkey_free(pkey);
```

**注意：**`pkey_set()` 是 RDPKRU 和 WRPKRU 指令的包装器。一个示例实现可以在 `tools/testing/selftests/x86/protection_keys.c` 文件中找到。

### 行为

内核试图使保护键的行为与普通的 `mprotect()` 一致。例如，如果你这样做：

```c
mprotect(ptr, size, PROT_NONE);
something(ptr);
```

你可以期望使用保护键时这样做也会产生相同的效果：

```c
pkey = pkey_alloc(0, PKEY_DISABLE_WRITE | PKEY_DISABLE_READ);
pkey_mprotect(ptr, size, PROT_READ|PROT_WRITE, pkey);
something(ptr);
```

无论 `something()` 是否是对 'ptr' 的直接访问，如：

```c
*ptr = foo;
```

还是当内核代表应用程序进行访问时，比如使用 `read()`：

```c
read(fd, ptr, 1);
```

内核在这两种情况下都会发送一个 SIGSEGV，但是 `si_code` 在违反保护键时会被设置为 `SEGV_PKERR`，而在违反纯 `mprotect()` 权限时会被设置为 `SEGV_ACCERR`。
