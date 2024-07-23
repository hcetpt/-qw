=============

BPF 迭代器
=============


----------
动机
----------

目前有几种方法将内核数据转储到用户空间。最流行的一种是`/proc`系统。例如，`cat /proc/net/tcp6`会转储系统中所有tcp6套接字，而`cat /proc/net/netlink`则会转储系统中所有netlink套接字。然而，它们的输出格式往往是固定的，如果用户想要获取更多关于这些套接字的信息，他们必须对内核进行补丁处理，这通常需要时间来向上游发布和发布。流行的工具如`ss <https://man7.org/linux/man-pages/man8/ss.8.html>`_也存在同样的情况，任何额外信息的获取都需要内核补丁。

为了解决这个问题，`drgn <https://www.kernel.org/doc/html/latest/bpf/drgn.html>`_工具经常被用来在不改变内核的情况下挖掘内核数据。但是，drgn的主要缺点是性能，因为它无法在内核内部进行指针追踪。此外，drgn无法验证指针值，如果指针在内核中变得无效，它可能会读取无效数据。

BPF迭代器通过调用BPF程序为每个内核数据对象收集所需的数据（例如任务、bpf_maps等）解决了上述问题，提供了灵活性。
----------------------

BPF 迭代器的工作原理
----------------------

BPF迭代器是一种BPF程序类型，允许用户遍历特定类型的内核对象。与传统的BPF追踪程序不同，后者允许用户定义在内核执行特定点被调用的回调，BPF迭代器允许用户定义应该为各种内核数据结构中的每一项执行的回调。

例如，用户可以定义一个BPF迭代器，遍历系统上的每个任务并转储每个任务当前使用的总CPU运行时间。另一个BPF任务迭代器可能转储每个任务的cgroup信息。这种灵活性正是BPF迭代器的核心价值。

BPF程序总是由用户空间进程请求加载到内核中。用户空间进程通过打开和初始化程序框架，并调用系统调用以使内核验证和加载BPF程序来加载BPF程序。

在传统的追踪程序中，通过用户空间获得`bpf_link`到程序，并使用`bpf_program__attach()`激活程序。一旦激活，当在主内核中触发tracepoint时，程序回调将被调用。对于BPF迭代器程序，使用`bpf_link_create()`获取程序的`bpf_link`，并通过从用户空间发出系统调用来调用程序回调。

接下来，让我们看看如何使用迭代器遍历内核对象并读取数据。
------------------------
如何使用BPF迭代器
------------------------

BPF自测是一个很好的资源，可以说明如何使用迭代器。在这一节中，我们将通过一个BPF自测，展示如何加载和使用BPF迭代器程序。首先，我们来看看`bpf_iter.c <https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/prog_tests/bpf_iter.c>`_，它展示了如何从用户空间加载和触发BPF迭代器。

稍后，我们将看看在内核空间中运行的BPF程序。
从用户空间在内核中加载BPF迭代器通常涉及以下步骤：

* 通过`libbpf`将BPF程序加载到内核。一旦内核验证并加载了该程序，它会向用户空间返回一个文件描述符（fd）。
* 通过调用`bpf_link_create()`，使用从内核接收到的BPF程序文件描述符，获取一个`link_fd`到BPF程序。
* 接下来，通过调用`bpf_iter_create()`，使用第二步得到的`bpf_link`，获取一个BPF迭代器文件描述符(`bpf_iter_fd`)。
* 通过调用`read(bpf_iter_fd)`触发迭代，直到没有数据可用。
* 使用`close(bpf_iter_fd)`关闭迭代器fd。
* 如果需要重新读取数据，获取一个新的`bpf_iter_fd`并再次进行读取。

以下是几个自测BPF迭代器程序的例子：

* `bpf_iter_tcp4.c <https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_tcp4.c>`_
* `bpf_iter_task_vma.c <https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_task_vma.c>`_
* `bpf_iter_task_file.c <https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/tools/testing/selftests/bpf/progs/bpf_iter_task_file.c>`_

让我们看一下在内核空间运行的`bpf_iter_task_file.c`：

这是`vmlinux.h`中`bpf_iter__task_file`的定义 `<https://facebookmicrosites.github.io/bpf/blog/2020/02/19/bpf-portability-and-co-re.html#btf>`_，`vmlinux.h`中的任何以`bpf_iter__<iter_name>`格式命名的struct都代表一个BPF迭代器。后缀`<iter_name>`表示迭代器的类型。
::
  
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

在上面的代码中，字段'meta'包含元数据，这对所有BPF迭代器程序都是相同的。其余的字段对不同的迭代器是特定的。例如，对于task_file迭代器，内核层提供了'task'、'fd'和'file'字段值。'task'和'file'是引用计数的 `<https://facebookmicrosites.github.io/bpf/blog/2018/08/31/object-lifetime.html#file-descriptors-and-reference-counters>`_ ，因此当BPF程序运行时，它们不会消失

以下是`bpf_iter_task_file.c`文件的一个片段：

::
  
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

在上面的例子中，部分名称`SEC(iter/task_file)`表明该程序是一个BPF迭代器程序，用于迭代所有任务的所有文件。程序的上下文是`bpf_iter__task_file`结构体。
用户空间程序通过发出`read()`系统调用来调用在内核中运行的BPF迭代器程序。一旦被调用，BPF程序可以使用多种BPF辅助函数将数据导出到用户空间。你可以根据需要格式化输出还是仅需要二进制数据，选择使用`bpf_seq_printf()`（和BPF_SEQ_PRINTF辅助宏）或`bpf_seq_write()`函数。对于二进制编码的数据，用户空间应用程序可以根据需要处理来自`bpf_seq_write()`的数据。对于格式化数据，你可以使用`cat <path>`来打印结果，类似于在将BPF迭代器固定到bpffs挂载点后执行`cat /proc/net/netlink`。之后，使用`rm -f <path>`删除固定的迭代器。

例如，你可以使用以下命令从`bpf_iter_ipv6_route.o`对象文件创建一个BPF迭代器，并将其固定到`/sys/fs/bpf/my_route`路径：

```
$ bpftool iter pin ./bpf_iter_ipv6_route.o /sys/fs/bpf/my_route
```

然后使用以下命令打印结果：

```
$ cat /sys/fs/bpf/my_route
```

---

实现内核对BPF迭代器程序类型的支持
---

为了在内核中实现一个BPF迭代器，开发者必须对`bpf.h`文件中定义的关键数据结构进行一次性的更改，该文件位于`https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf-next.git/tree/include/linux/bpf.h`。
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

填写完数据结构字段后，调用`bpf_iter_reg_target()`将迭代器注册到主BPF迭代器子系统。

以下是`struct bpf_iter_reg`中每个字段的详细说明：
- `target`：指定BPF迭代器的名称。例如：`bpf_map`、`bpf_map_elem`。名称应与内核中其他`bpf_iter`目标名称不同。
- `attach_target`和`detach_target`：允许针对特定目标的`link_create`操作，因为某些目标可能需要特殊处理。在用户空间`link_create`阶段调用。
- `show_fdinfo`和`fill_link_info`：当用户尝试获取与迭代器相关的链接信息时，用于填充特定于目标的信息。
- `get_func_proto`：允许BPF迭代器访问特定于迭代器的BPF辅助函数。
- `ctx_arg_info_size`和`ctx_arg_info`：指定与BPF迭代器关联的BPF程序参数的验证器状态。
* - 特性
     - 在内核BPF迭代器基础设施中指定某些操作请求。目前，仅支持BPF_ITER_RESCHED。这意味着会调用内核函数cond_resched()以避免其他内核子系统（例如rcu）出现异常行为。
* - seq_info
     - 指定用于BPF迭代器的seq操作集以及初始化/释放对应`seq_file`私有数据的辅助程序。

点击这里`查看在内核中实现的task_vma BPF迭代器<https://lore.kernel.org/bpf/20210212183107.50963-2-songliubraving@fb.com/>`_

-------------------------
参数化BPF任务迭代器
-------------------------

默认情况下，BPF迭代器遍历整个系统中指定类型的所有对象（进程、cgroup、映射等），以读取相关的内核数据。但通常情况下，我们只关心可迭代内核对象的一个小得多的子集，例如，仅遍历特定进程内的任务。因此，BPF迭代器程序通过允许用户空间在附加程序时配置迭代器来支持过滤掉迭代中的对象。

--------------------------
BPF任务迭代器程序
--------------------------

下面的代码是一个BPF迭代器程序，通过迭代器的`seq_file`打印文件和任务信息。这是一个标准的BPF迭代器程序，访问迭代器中的每个文件。我们将在后续示例中使用这个BPF程序。

----------------------------------------
创建带参数的文件迭代器
----------------------------------------

现在，让我们看看如何创建一个只包含特定进程文件的迭代器。首先，按照以下方式填充`bpf_iter_attach_opts`结构体：

如果`linfo.task.pid`非零，则指示内核创建一个只包含指定`pid`进程打开的文件的迭代器。在这个例子中，我们将只遍历我们自己的进程的文件。如果`linfo.task.pid`为零，迭代器将访问每个进程的每个打开的文件。类似地，`linfo.task.tid`指示内核创建一个访问特定线程（而非进程）打开文件的迭代器。在这个例子中，`linfo.task.tid`与`linfo.task.pid`不同，只有当线程具有独立的文件描述符表时。在大多数情况下，所有进程线程共享单一的文件描述符表。

现在，在用户空间程序中，将结构体指针传递给`bpf_program__attach_iter()`：

如果*tid*和*pid*都为零，从这个`bpf_iter_attach_opts`结构体创建的迭代器将包括系统中每个任务的每个打开的文件（实际上是在命名空间中）。这相当于将NULL作为第二个参数传递给`bpf_program__attach_iter()`。

整个程序如下所示：

输出结果如下：（注：由于输出依赖于运行环境，此处未给出具体输出内容。）
### 进程ID 1859 的文件描述符详情

- **进程ID** (`PID`)：1859
- **线程组ID** (`tgid`) | **进程ID** (`pid`) | **文件描述符** (`fd`) | **文件地址**
  - 1859 | 1859 | 0 | `ffffffff82270aa0`
  - 1859 | 1859 | 1 | `ffffffff82270aa0`
  - 1859 | 1859 | 2 | `ffffffff82270aa0`
  - 1859 | 1859 | 3 | `ffffffff82272980`
  - 1859 | 1859 | 4 | `ffffffff8225e120`
  - 1859 | 1859 | 5 | `ffffffff82255120`
  - 1859 | 1859 | 6 | `ffffffff82254f00`
  - 1859 | 1859 | 7 | `ffffffff82254d80`
  - 1859 | 1859 | 8 | `ffffffff8225abe0`

---

### 无参数情况

让我们看看一个没有参数的BPF迭代器如何跳过系统中其他进程的文件。在这种情况下，BPF程序必须检查任务的`pid`或`tid`，否则它会接收到系统中的每一个打开的文件（实际上是在当前的`pid`命名空间中）。因此，我们通常在BPF程序中添加一个全局变量来传递一个`pid`给BPF程序。

BPF程序可能如下所示：

```c
.....
int target_pid = 0;

SEC("iter/task_file")
int dump_task_file(struct bpf_iter__task_file *ctx)
{
      .....
if (task->tgid != target_pid) /* 检查thread ID时使用task->pid */
              return 0;
      BPF_SEQ_PRINTF(seq, "%8d %8d %8d %lx\n", task->tgid, task->pid, fd,
                      (long)file->f_op);
      return 0;
}
```

用户空间程序可能如下所示：

```c
.....
static void test_task_file(void)
{
      .....
skel = bpf_iter_task_ex__open_and_load();
      if (skel == NULL)
              return;
skel->bss->target_pid = getpid(); /* 进程ID。对于线程ID，使用gettid() */
      memset(&linfo, 0, sizeof(linfo));
      linfo.task.pid = getpid();
      opts.link_info = &linfo;
      opts.link_info_len = sizeof(linfo);
      .....
}
```

`target_pid`是BPF程序中的全局变量。用户空间程序应使用进程ID初始化该变量，以避免BPF程序处理其他进程的打开文件。当你为BPF迭代器参数化时，迭代器调用BPF程序的次数减少，这可以节省大量资源。

---

### 参数化VMA迭代器

默认情况下，BPF VMA迭代器包括每个进程中的所有VMA。然而，你仍然可以指定一个进程或线程仅包含其自身的VMAs。与文件不同，自Linux 2.6.0-test6以来，线程不能拥有独立的地址空间。在这里，使用`tid`和使用`pid`没有区别。
--------------------------
参数化任务迭代器
--------------------------

带有 *pid* 的 BPF 任务迭代器包括一个进程中的所有任务（线程）。BPF 程序会依次接收这些任务。你可以通过指定带有 *tid* 参数的 BPF 任务迭代器，仅包含与给定 *tid* 匹配的任务。
