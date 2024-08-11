# BPF 迭代器

## 动机

目前有几种方法可以将内核数据转储到用户空间。其中最流行的一种是 `/proc` 系统。例如，`cat /proc/net/tcp6` 可以转储系统中的所有 tcp6 套接字，而 `cat /proc/net/netlink` 则可以转储系统中所有的 netlink 套接字。然而，这些命令的输出格式往往是固定的，如果用户想要获取更多关于这些套接字的信息，则需要修改内核代码，而这通常需要一段时间才能被上游接受并发布。流行的工具如 `ss` 也是如此，任何额外信息的获取都需要内核补丁。

为了解决这个问题，经常使用 `drgn` 工具来挖掘内核数据而无需更改内核。但是，drgn 的主要缺点在于性能方面，因为它无法在内核内部进行指针追踪。此外，drgn 无法验证指针值的有效性，在指针无效的情况下可能会读取到无效的数据。

BPF 迭代器通过提供灵活性来解决上述问题，即允许用户通过调用 BPF 程序来收集特定类型的数据（例如任务、BPF 映射等）。

## BPF 迭代器的工作原理

BPF 迭代器是一种类型的 BPF 程序，它允许用户遍历特定类型的内核对象。与传统 BPF 跟踪程序不同，后者允许用户定义在内核特定执行点被调用的回调函数，BPF 迭代器则允许用户定义针对各种内核数据结构中每个条目的回调函数。

例如，用户可以定义一个 BPF 迭代器，遍历系统上的每一个任务，并输出每个任务当前使用的总 CPU 运行时间。另一个 BPF 任务迭代器可能输出每个任务的 cgroup 信息。这种灵活性正是 BPF 迭代器的核心价值。

一个 BPF 程序总是由用户空间进程请求加载到内核中的。用户空间进程通过打开和初始化程序框架并调用系统调用来让内核验证和加载 BPF 程序。

在传统的跟踪程序中，程序通过用户空间获取 `bpf_link` 来激活程序，使用 `bpf_program__attach()`。一旦激活，当主内核中的跟踪点被触发时，程序回调就会被调用。对于 BPF 迭代器程序，通过 `bpf_link_create()` 获取程序的 `bpf_link`，并通过从用户空间发出系统调用来调用程序回调。

接下来，我们将看看如何使用迭代器遍历内核对象并读取数据。

## 如何使用 BPF 迭代器

BPF 自测是一个很好的资源，用于展示如何使用迭代器。在此节中，我们将通过一个 BPF 自测示例来说明如何加载和使用 BPF 迭代器程序。首先，我们来看 `bpf_iter.c` 文件，该文件位于 `https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/prog_tests/bpf_iter.c` ，展示了如何在用户空间加载和触发 BPF 迭代器。

稍后，我们将查看一个运行在内核空间的 BPF 程序。
从用户空间向内核加载BPF迭代器通常涉及以下步骤：

* 通过`libbpf`将BPF程序加载到内核中。一旦内核验证并加载了该程序，它会返回一个文件描述符（fd）给用户空间。
* 通过调用`bpf_link_create()`并指定接收到的BPF程序文件描述符来获取一个`link_fd`指向BPF程序。
* 接下来，通过调用`bpf_iter_create()`并指定第2步中获得的`bpf_link`来获取一个BPF迭代器文件描述符（`bpf_iter_fd`）。
* 通过调用`read(bpf_iter_fd)`触发迭代，直到没有数据可用。
* 使用`close(bpf_iter_fd)`关闭迭代器fd。
* 如果需要重新读取数据，则获取一个新的`bpf_iter_fd`并再次执行读取操作。

以下是几个自测BPF迭代器程序的例子：

* [bpf_iter_tcp4.c](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_tcp4.c)
* [bpf_iter_task_vma.c](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_task_vma.c)
* [bpf_iter_task_file.c](https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_task_file.c)

让我们看一下在内核空间运行的`bpf_iter_task_file.c`：

这是`vmlinux.h`中`bpf_iter__task_file`的定义，[vmlinux.h](https://facebookmicrosites.github.io/bpf/blog/2020/02/19/bpf-portability-and-co-re.html#btf)中的任何以`bpf_iter__<iter_name>`格式命名的结构体都代表一个BPF迭代器。后缀`<iter_name>`表示迭代器的类型：
```c
struct bpf_iter__task_file {
        union {
            struct bpf_iter_meta *meta;
        };
        union {
            struct task_struct *task;
        };
        u32 fd;
        union {
            struct file *file;
        };
};
```

在上面的代码中，字段'meta'包含元数据，这对于所有BPF迭代器程序都是相同的。其余字段对于不同类型的迭代器是特定的。例如，对于`task_file`迭代器，内核层提供了'task'、'fd'和'file'字段的值。'task'和'file'是引用计数的，因此当BPF程序运行时它们不会消失。

下面是`bpf_iter_task_file.c`文件中的一个代码片段：
```c
SEC("iter/task_file")
int dump_task_file(struct bpf_iter__task_file *ctx)
{
    struct seq_file *seq = ctx->meta->seq;
    struct task_struct *task = ctx->task;
    struct file *file = ctx->file;
    __u32 fd = ctx->fd;

    if (task == NULL || file == NULL)
      return 0;

    if (ctx->meta->seq_num == 0) {
      count = 0;
      BPF_SEQ_PRINTF(seq, "    tgid      gid       fd      file\n");
    }

    if (tgid == task->tgid && task->tgid != task->pid)
      count++;

    if (last_tgid != task->tgid) {
      last_tgid = task->tgid;
      unique_tgid_count++;
    }

    BPF_SEQ_PRINTF(seq, "%8d %8d %8d %lx\n", task->tgid, task->pid, fd,
            (long)file->f_op);
    return 0;
}
```

在上述示例中，节名`SEC(iter/task_file)`表明该程序是一个BPF迭代器程序，用于遍历所有任务的所有文件。程序上下文为`bpf_iter__task_file`结构体。
用户空间程序通过发出`read()`系统调用来调用在内核中运行的BPF迭代器程序。一旦被调用，BPF程序可以使用多种BPF辅助函数将数据导出到用户空间。你可以根据需要格式化输出还是仅需要二进制数据来选择使用`bpf_seq_printf()`（和BPF_SEQ_PRINTF辅助宏）或`bpf_seq_write()`函数。对于二进制编码的数据，用户空间应用程序可以根据需要处理来自`bpf_seq_write()`的数据。对于格式化的数据，你可以使用`cat <路径>`来打印结果，类似于`cat /proc/net/netlink`，在将BPF迭代器固定到bpffs挂载点后。之后，使用`rm -f <路径>`来移除固定的迭代器。
例如，你可以使用以下命令从`bpf_iter_ipv6_route.o`对象文件创建一个BPF迭代器，并将其固定到`/sys/fs/bpf/my_route`路径：

```
$ bpftool iter pin ./bpf_iter_ipv6_route.o /sys/fs/bpf/my_route
```

然后使用以下命令打印结果：

```
$ cat /sys/fs/bpf/my_route
```

---

在内核中实现对BPF迭代器类型的支持
---

为了在内核中实现一个BPF迭代器，开发者必须对定义在`bpf.h`文件中的以下关键数据结构进行一次性更改：
```
struct bpf_iter_reg {
            const char *target;
            bpf_iter_attach_target_t attach_target;
            bpf_iter_detach_target_t detach_target;
            bpf_iter_show_fdinfo_t show_fdinfo;
            bpf_iter_fill_link_info_t fill_link_info;
            bpf_iter_get_func_proto_t get_func_proto;
            u32 ctx_arg_info_size;
            u32 feature;
            struct bpf_ctx_arg_aux ctx_arg_info[BPF_ITER_CTX_ARG_MAX];
            const struct bpf_iter_seq_info *seq_info;
};
```
填写完该数据结构的字段后，调用`bpf_iter_reg_target()`以将迭代器注册到主要的BPF迭代器子系统。

以下是`struct bpf_iter_reg`中每个字段的说明：
- **target**：指定BPF迭代器的名字，例如：`bpf_map`、`bpf_map_elem`。名称应与内核中的其他`bpf_iter`目标名称不同。
- **attach_target 和 detach_target**：允许针对特定目标执行`link_create`操作，因为某些目标可能需要特殊处理。在用户空间的`link_create`阶段调用。
- **show_fdinfo 和 fill_link_info**：当用户尝试获取与迭代器相关的链接信息时，用于填充特定于目标的信息。
- **get_func_proto**：允许BPF迭代器访问特定于迭代器的BPF辅助函数。
- **ctx_arg_info_size 和 ctx_arg_info**：指定了与BPF迭代器相关的BPF程序参数的验证器状态。
### BPF 迭代器特性说明

* - 特性 (`feature`)
     - 在内核 BPF 迭代器基础设施中指定某些动作请求。目前仅支持 `BPF_ITER_RESCHED`。这意味着会调用内核函数 `cond_resched()` 来避免其他内核子系统（例如，rcu）出现异常行为。
* - 序列信息 (`seq_info`)
     - 指定用于 BPF 迭代器的序列操作集以及初始化/释放相应 `seq_file` 的私有数据的帮助程序。

点击这里 [查看链接](https://lore.kernel.org/bpf/20210212183107.50963-2-songliubraving@fb.com/) 查看内核中 `task_vma` BPF 迭代器的一个实现示例。

### BPF 任务迭代器的参数化

默认情况下，BPF 迭代器遍历整个系统中的所有指定类型对象（进程、cgroup、映射等），以读取相关的内核数据。但在很多情况下，我们只关心一小部分可迭代的内核对象，例如仅迭代特定进程内的任务。因此，BPF 迭代器程序支持通过允许用户空间在绑定时配置迭代器程序来过滤掉不需要的对象。

### BPF 任务迭代器程序

下面是一个 BPF 迭代器程序的代码示例，它通过迭代器的 `seq_file` 打印文件和任务信息。这是一个标准的 BPF 迭代器程序，访问迭代器中的每个文件。稍后我们将使用这个 BPF 程序作为示例：

```c
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

char _license[] SEC("license") = "GPL";

SEC("iter/task_file")
int dump_task_file(struct bpf_iter__task_file *ctx)
{
        struct seq_file *seq = ctx->meta->seq;
        struct task_struct *task = ctx->task;
        struct file *file = ctx->file;
        __u32 fd = ctx->fd;
        if (task == NULL || file == NULL)
                return 0;
        if (ctx->meta->seq_num == 0) {
                BPF_SEQ_PRINTF(seq, "    tgid      pid       fd      file\n");
        }
        BPF_SEQ_PRINTF(seq, "%8d %8d %8d %lx\n", task->tgid, task->pid, fd,
                        (long)file->f_op);
        return 0;
}
```

### 创建带参数的文件迭代器

现在让我们看看如何创建一个仅包含特定进程文件的迭代器。
首先，按照以下方式填充 `bpf_iter_attach_opts` 结构体：

```c
LIBBPF_OPTS(bpf_iter_attach_opts, opts);
union bpf_iter_link_info linfo;
memset(&linfo, 0, sizeof(linfo));
linfo.task.pid = getpid();
opts.link_info = &linfo;
opts.link_info_len = sizeof(linfo);
```

如果 `linfo.task.pid` 非零，则指示内核创建一个仅包含指定 `pid` 进程已打开文件的迭代器。在这个例子中，我们只遍历当前进程的文件。如果 `linfo.task.pid` 为零，则迭代器将遍历每个进程的所有已打开文件。类似地，`linfo.task.tid` 指示内核创建一个仅遍历特定线程已打开文件的迭代器，而不是进程。在这个例子中，`linfo.task.tid` 与 `linfo.task.pid` 不同仅当线程具有独立的文件描述符表。大多数情况下，进程的所有线程共享同一个文件描述符表。

接下来，在用户空间程序中，将结构体指针传递给 `bpf_program__attach_iter()` 函数：

```c
link = bpf_program__attach_iter(prog, &opts);
iter_fd = bpf_iter_create(bpf_link__fd(link));
```

如果 *tid* 和 *pid* 均为零，从这个 `bpf_iter_attach_opts` 结构体创建的迭代器将包含系统中每个任务的所有已打开文件（实际上是在命名空间中）。这相当于将 `NULL` 作为第二个参数传递给 `bpf_program__attach_iter()`。

完整的程序如下所示：

```c
#include <stdio.h>
#include <unistd.h>
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include "bpf_iter_task_ex.skel.h"

static int do_read_opts(struct bpf_program *prog, struct bpf_iter_attach_opts *opts)
{
        struct bpf_link *link;
        char buf[16] = {};
        int iter_fd = -1, len;
        int ret = 0;

        link = bpf_program__attach_iter(prog, opts);
        if (!link) {
                fprintf(stderr, "bpf_program__attach_iter() fails\n");
                return -1;
        }
        iter_fd = bpf_iter_create(bpf_link__fd(link));
        if (iter_fd < 0) {
                fprintf(stderr, "bpf_iter_create() fails\n");
                ret = -1;
                goto free_link;
        }
        /* 不检查内容，但确保 read() 没有错误地结束 */
        while ((len = read(iter_fd, buf, sizeof(buf) - 1)) > 0) {
                buf[len] = 0;
                printf("%s", buf);
        }
        printf("\n");
free_link:
        if (iter_fd >= 0)
                close(iter_fd);
        bpf_link__destroy(link);
        return 0;
}

static void test_task_file(void)
{
        LIBBPF_OPTS(bpf_iter_attach_opts, opts);
        struct bpf_iter_task_ex *skel;
        union bpf_iter_link_info linfo;
        skel = bpf_iter_task_ex__open_and_load();
        if (skel == NULL)
                return;
        memset(&linfo, 0, sizeof(linfo));
        linfo.task.pid = getpid();
        opts.link_info = &linfo;
        opts.link_info_len = sizeof(linfo);
        printf("PID %d\n", getpid());
        do_read_opts(skel->progs.dump_task_file, &opts);
        bpf_iter_task_ex__destroy(skel);
}

int main(int argc, const char * const * argv)
{
        test_task_file();
        return 0;
}
```

下面是程序的输出结果：
### PID 1859

    tgid      pid       fd      file
    1859     1859        0 ffffffff82270aa0
    1859     1859        1 ffffffff82270aa0
    1859     1859        2 ffffffff82270aa0
    1859     1859        3 ffffffff82272980
    1859     1859        4 ffffffff8225e120
    1859     1859        5 ffffffff82255120
    1859     1859        6 ffffffff82254f00
    1859     1859        7 ffffffff82254d80
    1859     1859        8 ffffffff8225abe0

--------------

### 不带参数的情况

让我们看看一个没有参数的BPF迭代器如何跳过系统中其他进程的文件。在这种情况下，BPF程序需要检查任务的PID或TID，否则它会收到当前进程命名空间中的每一个打开的文件。因此，我们通常会在BPF程序中添加一个全局变量来传递一个PID给BPF程序。BPF程序可能如下所示：

    .....
int target_pid = 0;

    SEC("iter/task_file")
    int dump_task_file(struct bpf_iter__task_file *ctx)
    {
          .....
if (task->tgid != target_pid) /* 检查 task->pid 来代替检查线程ID */
                  return 0;
          BPF_SEQ_PRINTF(seq, "%8d %8d %8d %lx\n", task->tgid, task->pid, fd,
                          (long)file->f_op);
          return 0;
    }

用户空间程序可能如下所示：

  ::

    .....
static void test_task_file(void)
    {
          .....
skel = bpf_iter_task_ex__open_and_load();
          if (skel == NULL)
                  return;
          skel->bss->target_pid = getpid(); /* 进程ID。对于线程ID，请使用gettid() */
          memset(&linfo, 0, sizeof(linfo));
          linfo.task.pid = getpid();
          opts.link_info = &linfo;
          opts.link_info_len = sizeof(linfo);
          .....
}

`target_pid`是BPF程序中的一个全局变量。用户空间程序应该用进程ID初始化这个变量，以便在BPF程序中跳过其他进程打开的文件。当你为BPF迭代器设置参数时，迭代器调用BPF程序的次数会减少，这可以节省大量资源。

-------------

### 参数化VMA迭代器

默认情况下，BPF VMA迭代器包括每个进程中的所有VMA。但是，你仍然可以指定一个进程或一个线程来只包含它的VMA。与文件不同，自Linux 2.6.0-test6以来，线程不能拥有独立的地址空间。在这里，使用TID与使用PID没有区别。
--------------------------
参数化任务迭代器
--------------------------

带有 *pid* 的 BPF 任务迭代器包括一个进程中的所有任务（线程）。BPF 程序依次接收这些任务。你可以通过指定带有 *tid* 参数的 BPF 任务迭代器来只包含与给定 *tid* 匹配的任务。
