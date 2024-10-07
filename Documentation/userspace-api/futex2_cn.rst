SPDX 许可证标识符: GPL-2.0

======
futex2
======

:作者: André Almeida <andrealmeid@collabora.com>

futex（快速用户互斥锁）是一组系统调用，允许用户空间创建高效的同步机制，例如互斥锁、信号量和条件变量。像 glibc 这样的 C 标准库使用它来实现更高层次的接口，如 pthreads。
futex2 是初始 futex 系统调用的后续版本，旨在克服原始接口的局限性。

用户 API
========

`futex_waitv()`
-----------------

在一组 futex 上等待，任何 futex 被唤醒时结束等待：

```c
futex_waitv(struct futex_waitv *waiters, unsigned int nr_futexes,
            unsigned int flags, struct timespec *timeout, clockid_t clockid)
```

```c
struct futex_waitv {
        __u64 val;         // 预期值
        __u64 uaddr;       // 等待地址
        __u32 flags;       // 类型（例如私有）和大小标志
        __u32 __reserved;  // 保留字段，目前应为0，未来可能扩展
};
```

用户空间设置一个 `struct futex_waitv` 数组（最多 128 个条目），使用 `uaddr` 表示等待地址，`val` 表示预期值，`flags` 指定类型（例如私有）和大小。`__reserved` 字段需要设为0，但可以用于未来的扩展。数组的第一个元素指针作为 `waiters` 传入。如果 `waiters` 或任何 `uaddr` 地址无效，则返回 `-EFAULT`。

如果用户空间中的指针是 32 位的，应进行显式转换以确保高几位为零。`uintptr_t` 可以完成这一操作，并且适用于 32/64 位指针。

`nr_futexes` 指定数组的大小。超出 `[1, 128]` 区间的数值将使系统调用返回 `-EINVAL`。

系统调用的 `flags` 参数目前需要设为 0，但可以用于未来的扩展。

对于 `waiters` 数组中的每个条目，当前 `uaddr` 的值与 `val` 进行比较。如果不同，则系统调用撤销所有已完成的工作并返回 `-EAGAIN`。如果所有测试和验证成功，系统调用将等待以下情况之一发生：

- 超时到期，返回 `-ETIMEOUT`
- 向睡眠任务发送了信号，返回 `-ERESTARTSYS`
- 列表中的某个 futex 被唤醒，返回被唤醒的 futex 的索引
如何使用该接口的一个示例可以在 `tools/testing/selftests/futex/functional/futex_waitv.c` 中找到。
超时
------

`struct timespec *timeout` 参数是一个可选参数，指向一个绝对超时时间。你需要在 `clockid` 参数中指定所使用的时钟类型。支持 `CLOCK_MONOTONIC` 和 `CLOCK_REALTIME` 这两种时钟类型。此系统调用只接受 64 位的 timespec 结构体。

futex 的类型
--------------

futex 可以是私有的（private）或共享的（shared）。私有 futex 用于共享同一内存空间的进程，并且所有进程中的 futex 虚拟地址相同。这允许内核进行优化。要使用私有 futex，需要在 futex 标志中指定 `FUTEX_PRIVATE_FLAG`。对于不共享同一内存空间的进程，它们可能对同一个 futex 使用不同的虚拟地址（例如，通过文件支持的共享内存），这就需要不同的内部机制来正确地排队。这是默认行为，并且适用于私有和共享 futex。

futex 可以有不同的大小：8 位、16 位、32 位或 64 位。目前唯一支持的是 32 位大小的 futex，并且需要使用 `FUTEX_32` 标志来指定。
