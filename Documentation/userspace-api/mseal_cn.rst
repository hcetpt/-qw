SPDX 许可证标识符: GPL-2.0

=====================
mseal 介绍
=====================

:作者: Jeff Xu <jeffxu@chromium.org>

现代 CPU 支持诸如 RW 和 NX 位的内存权限功能。内存权限特性提高了内存损坏漏洞的安全性，即攻击者不能随便写入任意内存并指向该内存，内存必须标记为具有 X 位，否则会触发异常。内存密封进一步保护了映射本身免受修改。这对于缓解内存损坏问题非常有用，例如，当一个被篡改的指针传递给内存管理系统时。例如，这种攻击原语可以破坏控制流完整性保证，因为本应受信任的只读内存可能会变成可写的，或者 .text 页面可能被重新映射。内存密封可以在运行时由加载器自动应用以密封 .text 和 .rodata 页面，并且应用程序还可以在运行时额外密封关键安全数据。类似的功能已经存在于带有 VM_FLAGS_PERMANENT 标志的 XNU 内核中 [1]，以及带有 mimmutable 系统调用的 OpenBSD 中 [2]。

用户 API
========

mseal()
-----------
`mseal()` 系统调用的签名如下：

``int mseal(void *addr, size_t len, unsigned long flags)``

**addr/len**: 虚拟内存地址范围
由 `addr`/`len` 设置的地址范围必须满足以下条件：
   - 起始地址必须位于已分配的 VMA 中
- 起始地址必须是页面对齐的
- 结束地址 (`addr` + `len`) 必须位于已分配的 VMA 中
- 起始地址和结束地址之间不能有空隙（未分配的内存）
`len` 将被内核隐式地页面对齐。
**标志**：预留供将来使用

**返回值**：

- ``0``：成功
- ``-EINVAL``：
    - 无效的输入 ``flags``
    - 起始地址（``addr``）未对齐到页面
    - 地址范围（``addr`` + ``len``）溢出
- ``-ENOMEM``：
    - 起始地址（``addr``）未分配
    - 结束地址（``addr`` + ``len``）未分配
    - 起始和结束地址之间有空隙（未分配的内存）
- ``-EPERM``：
    - 只支持在64位CPU上进行密封，不支持32位

对于上述错误情况，用户可以预期给定的内存范围保持不变，即没有部分更新。
**可能存在其他内部错误或情况未在此列出，例如在合并/拆分VMAs时出现的错误，或者进程达到支持的最大VMA数量。在这些情况下，可能会对给定内存范围进行部分更新。然而，这些情况应该很少见。**

**封存后的阻塞操作：**
- 通过`munmap()`和`mremap()`进行解映射、移动到另一个位置或缩小大小，这会留下空空间，因此可以被具有新属性集的新VMA替换。
- 通过`mremap()`将不同的VMA移动或扩展到当前位置。
- 通过`mmap(MAP_FIXED)`修改VMA。
- 通过`mremap()`进行大小扩展，似乎不会对封存的VMAs造成特定的风险。无论如何，它仍然被包括在内，因为使用场景不明确。无论如何，用户可以依赖合并来扩展封存的VMA。
- `mprotect()`和`pkey_mprotect()`。
- 对匿名内存的一些破坏性的`madvice()`行为（例如MADV_DONTNEED），当用户没有对该内存的写权限时。这些行为可以通过丢弃页面来更改区域内容，实际上是对匿名内存执行memset(0)。

内核对于阻塞操作将返回-EPERM。
对于阻塞操作，可以预期给定地址不会被修改，即不会有部分更新。请注意，这与现有的mm系统调用行为不同，在现有行为中，会进行部分更新直到找到错误并返回用户空间。举个例子：

假设以下代码序列：
```
- ptr = mmap(null, 8192, PROT_NONE);
- munmap(ptr + 4096, 4096);
- ret1 = mprotect(ptr, 8192, PROT_READ);
- mseal(ptr, 4096);
- ret2 = mprotect(ptr, 8192, PROT_NONE);
```

`ret1`将是-ENOMEM，从`ptr`开始的页面会被更新为PROT_READ。
**注释**：

- `mseal()` 只在 64 位 CPU 上工作，不支持 32 位 CPU。
- 用户可以多次调用 `mseal()`。对于已经密封的内存再次调用 `mseal()` 不会产生任何操作（不会报错）。
- 不支持 `munseal()`。

使用场景：
==========

- glibc：
  动态链接器在加载 ELF 可执行文件时，可以对不可写入的内存段应用密封。
- Chrome 浏览器：保护一些敏感的安全数据结构。

关于要密封的内存的说明：
=======================

需要注意的是，密封会改变映射的生命周期，即密封后的映射在进程终止或调用 `exec` 系统调用之前不会被取消映射。应用程序可以从用户空间对任何虚拟内存区域应用密封，但在应用密封之前，必须彻底分析映射的生命周期。

例如：

- aio/shm

  aio/shm 可以代表用户空间调用 `mmap()` 和 `munmap()`，例如 `shm.c` 中的 `ksys_shmdt()`。这些映射的生命周期与进程的生命周期无关。如果从用户空间对这些内存进行密封，则 `munmap()` 会失败，在进程生命周期内导致 VMA 地址空间泄漏。

- Brk（堆）

  目前，用户空间应用程序可以通过调用 `malloc()` 和 `mseal()` 来密封堆的一部分。
  假设以下来自用户空间的调用：

  ```c
  void *ptr = malloc(size);
  mprotect(ptr, size, PROT_READ);
  mseal(ptr, size);
  free(ptr);
  ```

  从技术上讲，在添加 `mseal()` 之前，用户可以通过调用 `mprotect(PROT_READ)` 改变堆的保护属性。只要用户在调用 `free()` 之前将保护属性改回可读写（RW），则该内存范围可以被重用。
将 mseal() 引入后，堆会被部分封存，用户仍然可以释放它，但内存仍然是只读的。如果堆管理器重用该地址进行另一次 malloc 操作，进程可能会很快崩溃。因此，对于可能被回收的任何内存，不应对其实行封存。

此外，即使应用程序从未对指针 ptr 调用 free()，堆管理器也可能调用 brk 系统调用来缩小堆的大小。在内核中，brk 缩小操作会调用 munmap()。因此，根据 ptr 的位置，brk 缩小的结果是不确定的。

补充说明：
=============
正如 Jann Horn 在 [3] 中指出的那样，仍有一些方法可以写入只读内存，这在某种程度上是设计使然。这些情况不受 mseal() 的覆盖。如果应用程序希望阻止这些情况，可以考虑使用沙箱工具（如 seccomp、LSM 等）。
这些情况包括：

- 通过 /proc/self/mem 接口写入只读内存
- 通过 ptrace（如 PTRACE_POKETEXT）写入只读内存
- userfaultfd

启发这一补丁的想法来自 Stephen Röttger 在 V8 CFI [4] 中的工作。Chrome 浏览器在 ChromeOS 中将是此 API 的首位使用者。

参考：
==========
[1] https://github.com/apple-oss-distributions/xnu/blob/1031c584a5e37aff177559b9f69dbd3c8c3fd30a/osfmk/mach/vm_statistics.h#L274

[2] https://man.openbsd.org/mimmutable.2

[3] https://lore.kernel.org/lkml/CAG48ez3ShUYey+ZAFsU2i1RpQn0a5eOs2hzQ426FkcgnfUGLvA@mail.gmail.com

[4] https://docs.google.com/document/d/1O2jwK4dxI3nRcOJuPYkonhTkNQfbmwdvxQMyXgeaRHo/edit#heading=h.bvaojj9fu6hc
