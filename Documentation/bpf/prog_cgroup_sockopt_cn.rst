SPDX 许可证标识符: GPL-2.0

============================
BPF_PROG_TYPE_CGROUP_SOCKOPT
============================

`BPF_PROG_TYPE_CGROUP_SOCKOPT` 类型的程序可以附加到两种 cgroup 钩子上：

* `BPF_CGROUP_GETSOCKOPT` - 每当进程执行 `getsockopt` 系统调用时被调用
* `BPF_CGROUP_SETSOCKOPT` - 每当进程执行 `setsockopt` 系统调用时被调用
上下文 (`struct bpf_sockopt`) 包含相关的套接字 (`sk`) 和所有输入参数：`level`、`optname`、`optval` 和 `optlen`

BPF_CGROUP_SETSOCKOPT
=====================

`BPF_CGROUP_SETSOCKOPT` 在内核处理 `sockopt` 之前触发，并且具有可写入的上下文：它可以在将参数传递给内核之前修改这些参数。此钩子可以访问 cgroup 和套接字本地存储。
如果 BPF 程序将 `optlen` 设置为 -1，则在 cgroup 链中的所有其他 BPF 程序完成后，控制权将返回用户空间（即内核 `setsockopt` 处理将 *不会* 执行）。
请注意，`optlen` 不能增加超过用户提供的值。它只能减少或设置为 -1。任何其他值都将触发 `EFAULT`。

**返回类型**

* `0` - 拒绝系统调用，将向用户空间返回 `EPERM`
* `1` - 成功，继续执行 cgroup 链中的下一个 BPF 程序

BPF_CGROUP_GETSOCKOPT
=====================

`BPF_CGROUP_GETSOCKOPT` 在内核处理 `sockopt` 之后触发。如果 BPF 钩子对内核返回的内容感兴趣，它可以观察 `optval`、`optlen` 和 `retval`。BPF 钩子可以覆盖上述值，调整 `optlen` 并将 `retval` 重置为 0。如果 `optlen` 超过了初始 `getsockopt` 值（即用户空间缓冲区太小），则返回 `EFAULT`。
此钩子可以访问 cgroup 和套接字本地存储。
请注意，可以设置给 `retval` 的唯一可接受的值是 0 和内核返回的原始值。任何其他值都将触发 `EFAULT`。

返回类型
--------

* `0` - 拒绝系统调用，`EPERM` 将被返回到用户空间。
* `1` - 成功：将 `optval` 和 `optlen` 复制到用户空间，并从系统调用返回 `retval`（请注意，这可能被父 cgroup 中的 BPF 程序覆盖）。

Cgroup 继承
==========

假设存在以下 cgroup 层次结构，其中每个 cgroup 在各个层级上都附加了 `BPF_CGROUP_GETSOCKOPT`，并带有 `BPF_F_ALLOW_MULTI` 标志：

```
A (根，父级)
 \
  B (子级)
```

当应用程序从 cgroup B 调用 `getsockopt` 系统调用时，程序将从下至上执行：B、A。第一个程序（B）会看到内核 `getsockopt` 的结果。它可以可选地调整 `optval`、`optlen` 并将 `retval` 重置为 0。之后控制权将传递给第二个（A）程序，它将看到与 B 相同的上下文，包括任何可能的修改。
对于 `BPF_CGROUP_SETSOCKOPT` 也是一样：如果程序被附加到 A 和 B，则触发顺序为 B，然后是 A。如果 B 对输入参数（`level`、`optname`、`optval`、`optlen`）进行了任何更改，那么链中的下一个程序（A）将看到这些更改，而不是原始输入 `setsockopt` 参数。这些潜在修改后的值随后将传递给内核。

大的 `optval`
==============

当 `optval` 大于 `PAGE_SIZE` 时，BPF 程序只能访问该数据的前 `PAGE_SIZE`。因此，它有两种选择：

* 将 `optlen` 设置为零，这表示内核应使用用户空间中的原始缓冲区。BPF 程序对 `optval` 所做的任何修改都会被忽略。
* 将 `optlen` 设置为小于 `PAGE_SIZE` 的值，这表示内核应使用 BPF 修剪后的 `optval`。

当 BPF 程序返回的 `optlen` 大于 `PAGE_SIZE` 时，用户空间将收到原始内核缓冲区，而不包含 BPF 程序可能应用的任何修改。

示例
====

推荐处理 BPF 程序的方式如下：

```c
SEC("cgroup/getsockopt")
int getsockopt(struct bpf_sockopt *ctx)
{
    /* 自定义套接字选项。 */
    if (ctx->level == MY_SOL && ctx->optname == MY_OPTNAME) {
        ctx->retval = 0;
        optval[0] = ...;
        ctx->optlen = 1;
        return 1;
    }

    /* 修改内核的套接字选项。 */
    if (ctx->level == SOL_IP && ctx->optname == IP_FREEBIND) {
        ctx->retval = 0;
        optval[0] = ...;
        ctx->optlen = 1;
        return 1;
    }

    /* 如果 optval 大于 PAGE_SIZE，则使用内核的缓冲区。 */
    if (ctx->optlen > PAGE_SIZE)
        ctx->optlen = 0;

    return 1;
}

SEC("cgroup/setsockopt")
int setsockopt(struct bpf_sockopt *ctx)
{
    /* 自定义套接字选项。 */
    if (ctx->level == MY_SOL && ctx->optname == MY_OPTNAME) {
        /* 执行某些操作 */
        ctx->optlen = -1;
        return 1;
    }

    /* 修改内核的套接字选项。 */
    if (ctx->level == SOL_IP && ctx->optname == IP_FREEBIND) {
        optval[0] = ...;
        return 1;
    }

    /* 如果 optval 大于 PAGE_SIZE，则使用内核的缓冲区。 */
    if (ctx->optlen > PAGE_SIZE)
        ctx->optlen = 0;

    return 1;
}
```

请参阅 `tools/testing/selftests/bpf/progs/sockopt_sk.c` 以获取处理套接字选项的 BPF 程序示例。
