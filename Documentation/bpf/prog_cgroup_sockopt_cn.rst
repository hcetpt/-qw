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

`BPF_CGROUP_SETSOCKOPT` 在内核处理 `sockopt` 之前触发，并且具有可写入的上下文：可以在传递给内核之前修改提供的参数。此钩子可以访问 cgroup 和套接字本地存储。
如果 BPF 程序将 `optlen` 设置为 -1，则在 cgroup 链中的所有其他 BPF 程序完成后，控制权将返回用户空间（即内核 `setsockopt` 处理将 *不会* 被执行）。
注意，`optlen` 的值不能超过用户提供的值。它只能减少或设置为 -1。任何其他值都会触发 `EFAULT`。

**返回类型**

* `0` - 拒绝系统调用，将 `EPERM` 返回到用户空间
* `1` - 成功，继续执行 cgroup 链中的下一个 BPF 程序

BPF_CGROUP_GETSOCKOPT
=====================

`BPF_CGROUP_GETSOCKOPT` 在内核处理 `sockopt` 之后触发。BPF 钩子可以观察 `optval`、`optlen` 和 `retval`（如果对内核返回的内容感兴趣的话）。BPF 钩子可以覆盖上述值，调整 `optlen` 并将 `retval` 重置为 0。如果 `optlen` 增加超过了初始 `getsockopt` 的值（即用户空间缓冲区太小），则返回 `EFAULT`。
此钩子可以访问 cgroup 和套接字本地存储。
请注意，唯一可接受的`retval`设置值是0和内核返回的原始值。任何其他值将触发`EFAULT`。

返回类型
--------

* `0` - 拒绝系统调用，`EPERM`将被返回给用户空间。
* `1` - 成功：将`optval`和`optlen`复制到用户空间，从系统调用返回`retval`（注意这可能被父cgroup中的BPF程序覆盖）

cgroup继承
==========

假设存在以下cgroup层次结构，其中每个cgroup在每一级都附加了`BPF_CGROUP_GETSOCKOPT`，并带有`BPF_F_ALLOW_MULTI`标志：

```
A（根，父）
 \
  B（子）
```

当应用程序从cgroup B中调用`getsockopt`系统调用时，程序自下而上执行：B，然后A。第一个程序（B）看到内核`getsockopt`的结果。它可以可选地调整`optval`、`optlen`并将`retval`重置为0。之后控制将传递给第二个（A）程序，它将看到与B相同的上下文，包括任何潜在的修改。
对于`BPF_CGROUP_SETSOCKOPT`也是同样的情况：如果程序附着于A和B，触发顺序是B，然后是A。如果B对输入参数（`level`、`optname`、`optval`、`optlen`）进行任何更改，那么链中的下一个程序（A）将看到这些更改，而不是原始输入`setsockopt`参数。潜在修改后的值将随后传递给内核。

大的optval
==========

当`optval`大于`PAGE_SIZE`时，BPF程序只能访问该数据的前`PAGE_SIZE`部分。因此它有两个选项：

* 将`optlen`设置为零，这表明内核应使用用户空间的原始缓冲区。BPF程序对`optval`所做的任何修改都将被忽略。
* 将`optlen`设置为小于`PAGE_SIZE`的值，这表明内核应使用BPF裁剪过的`optval`。

当BPF程序以大于`PAGE_SIZE`的`optlen`返回时，用户空间将收到未经BPF程序可能应用的任何修改的原始内核缓冲区。

示例
====

处理BPF程序推荐的方式如下：

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

    /* 如果optval大于PAGE_SIZE，则使用内核的缓冲区。 */
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

    /* 如果optval大于PAGE_SIZE，则使用内核的缓冲区。 */
    if (ctx->optlen > PAGE_SIZE)
        ctx->optlen = 0;

    return 1;
}
```

请参阅`tools/testing/selftests/bpf/progs/sockopt_sk.c`以获取处理套接字选项的BPF程序示例。
