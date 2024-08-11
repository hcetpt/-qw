SPDX 许可证标识符: GPL-2.0

=======================================
Padata 并行执行机制
=======================================

:日期: 2020年5月

Padata 是一种机制，通过该机制内核可以将任务分发到多个CPU上并行处理，同时可选择性地保持这些任务的顺序。它最初是为IPsec开发的，IPsec需要在大量数据包上进行加密和解密操作而不能重新排序这些数据包。目前这是Padata序列化作业支持的唯一消费者。Padata还支持多线程任务，在负载均衡和协调线程间的同时将任务均匀分割。

运行序列化作业
=======================

初始化
------------

使用Padata运行序列化作业的第一步是设置一个`padata_instance`结构，以总体控制如何运行任务：

    #include <linux/padata.h>

    struct padata_instance *padata_alloc(const char *name);

`name`仅仅用于标识这个实例。
然后，通过分配一个`padata_shell`来完成Padata的初始化：

   struct padata_shell *padata_alloc_shell(struct padata_instance *pinst);

`padata_shell`用于向Padata提交任务，并允许一系列这样的任务独立地序列化。一个`padata_instance`可以有一个或多个与之关联的`padata_shell`，每个都可以单独执行一系列任务。

修改 CPU 面具（cpumasks）
------------------

可以通过两种方式更改用于运行任务的CPU：程序化地使用`padata_set_cpumask()`函数，或者通过sysfs。前者定义如下：

    int padata_set_cpumask(struct padata_instance *pinst, int cpumask_type,
                           cpumask_var_t cpumask);

这里`cpumask_type`可以是`PADATA_CPU_PARALLEL`或`PADATA_CPU_SERIAL`，其中并行的CPU面具描述了哪些处理器将被用来并行执行提交给这个实例的任务，而序列化的CPU面具定义了哪些处理器被允许用作序列化回调处理器。`cpumask`指定了要使用的新的CPU面具。

可能有sysfs文件来表示实例的CPU面具。例如，`pcrypt`的sysfs文件位于`/sys/kernel/pcrypt/<instance-name>`。在实例目录下有两个文件：`parallel_cpumask`和`serial_cpumask`，可以通过向文件中写入位掩码的方式来改变任一CPU面具，例如：

    echo f > /sys/kernel/pcrypt/pencrypt/parallel_cpumask

读取这些文件会显示用户提供的CPU面具，这可能与“可用”的CPU面具不同。

Padata内部维护两对CPU面具：用户提供的CPU面具和“可用”的CPU面具。（每一对包括一个并行和一个序列化的CPU面具。）用户提供的CPU面具默认包含所有可能的CPU，并且可以在上述方式下更改。可用的CPU面具总是用户提供的CPU面具的子集，仅包含用户提供的面具中的在线CPU；这些是Padata实际使用的CPU面具。因此，向Padata提供包含离线CPU的CPU面具是合法的。一旦用户提供的CPU面具中的离线CPU上线，Padata就会使用它。

更改CPU面具是昂贵的操作，因此不应该频繁进行。
运行任务
-------------

实际上，向 `padata` 实例提交工作需要创建一个 `padata_priv` 结构体，它代表一个任务：

    struct padata_priv {
        /* 其他内容在这里... */
        void (*parallel)(struct padata_priv *padata);
        void (*serial)(struct padata_priv *padata);
    };

此结构体几乎肯定会嵌入到某个更大的、与要执行的工作相关的结构体中。它的大多数字段对 `padata` 是私有的，但在初始化时应该将该结构体清零，并提供 `parallel()` 和 `serial()` 函数。这些函数将在完成工作过程中被调用，我们很快就会看到。
任务的提交通过以下方式完成：

    int padata_do_parallel(struct padata_shell *ps,
                           struct padata_priv *padata, int *cb_cpu);

`ps` 和 `padata` 结构体必须如上所述设置；`cb_cpu` 指向任务完成后用于最终回调的首选 CPU；它必须在当前实例的 CPU 面具内（如果不是，`cb_cpu` 指针会被更新以指向实际选择的 CPU）。`padata_do_parallel()` 的返回值在成功时为零，表示任务正在进行中。`-EBUSY` 表示有人正在其他地方篡改实例的 CPU 面具，而 `-EINVAL` 则是对 `cb_cpu` 不在串行 CPU 面具内、并行或串行 CPU 面具中没有在线 CPU 或实例已停止的抱怨。
每个提交给 `padata_do_parallel()` 的任务都会依次传递给上面提到的 `parallel()` 函数的一个确切调用，在一个 CPU 上运行，因此真正的并行性是通过提交多个任务实现的。`parallel()` 在禁用了软件中断的情况下运行，因此无法休眠。`parallel()` 函数接受 `padata_priv` 结构体指针作为其唯一参数；有关要执行的实际工作的信息可能通过使用 `container_of()` 来查找包含结构体获得。
请注意，`parallel()` 没有返回值；`padata` 子系统假设从这一点开始 `parallel()` 将对任务负责。任务不必在此调用期间完成，但如果 `parallel()` 留下未完成的工作，则应准备好在前一个任务完成之前再次被调用新的任务。

串行化任务
-----------------

当任务确实完成时，`parallel()`（或实际上完成工作的任何函数）应通过调用来通知 `padata` 事实：

    void padata_do_serial(struct padata_priv *padata);

将来某个时刻，`padata_do_serial()` 将触发对 `padata_priv` 结构体中的 `serial()` 函数的调用。该调用将在初始调用 `padata_do_parallel()` 时请求的 CPU 上发生；它同样是在禁用了本地软件中断的情况下运行的。
请注意，这个调用可能会被推迟一段时间，因为 `padata` 代码尽力确保任务按照它们提交的顺序完成。

销毁
----------

清理 `padata` 实例可预测地涉及按相反顺序调用两个释放函数：

    void padata_free_shell(struct padata_shell *ps);
    void padata_free(struct padata_instance *pinst);

用户有责任确保在调用上述任何一项之前所有未完成的任务都已完成。

运行多线程任务
==========================

一个多线程任务有一个主线程和零个或多个辅助线程，其中主线程参与任务然后等待所有辅助线程完成。`padata` 将任务分割成称为块的单位，其中块是线程在一次线程函数调用中完成的任务的一部分。

为了运行一个多线程任务，用户需要做三件事。首先，通过定义 `padata_mt_job` 结构来描述任务，该结构在接口部分中有解释。这包括指向线程函数的指针，`padata` 将在每次分配任务块给线程时调用该函数。然后，定义线程函数，它接受三个参数：`start`、`end` 和 `arg`，其中前两个限定线程操作的范围，最后一个是指向任务共享状态的指针（如果有的话）。准备共享状态，这通常在主线程的堆栈上分配。最后，调用 `padata_do_multithreaded()`，该函数会在任务完成后返回。

接口
=========

.. kernel-doc:: include/linux/padata.h
.. kernel-doc:: kernel/padata.c
