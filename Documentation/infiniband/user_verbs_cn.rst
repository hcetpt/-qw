用户空间动词访问
======================

通过启用CONFIG_INFINIBAND_USER_VERBS构建的`ib_uverbs`模块，允许直接从用户空间通过“动词”访问IB硬件，这些“动词”的描述见于《InfiniBand 架构规范》第11章。

要使用这些动词，需要来自https://github.com/linux-rdma/rdma-core的`libibverbs`库。`libibverbs`包含了一个用于使用`ib_uverbs`接口的设备无关API。

`libibverbs`还需要适用于您的InfiniBand硬件的适当设备相关内核和用户空间驱动程序。例如，要使用Mellanox HCA，您将需要安装`ib_mthca`内核模块和`libmthca`用户空间驱动程序。

用户-内核通信
=========================

用户空间通过`/dev/infiniband/uverbsN`字符设备与内核进行慢路径、资源管理操作的通信。快路径操作通常通过直接写入映射到用户空间的硬件寄存器来完成，无需系统调用或切换到内核上下文。

命令通过在这些设备文件上的write()发送给内核。
ABI定义在`drivers/infiniband/include/ib_user_verbs.h`中。
对于需要内核响应的命令结构体，包含一个64位字段，用于传递指向输出缓冲区的指针。
状态作为write()系统调用的返回值返回给用户空间。

资源管理
===================

由于所有IB资源的创建和销毁都是通过文件描述符传递的命令完成的，因此内核可以跟踪哪些资源与给定用户空间上下文相关联。`ib_uverbs`模块维护idr表，用于在内核指针和不透明的用户空间句柄之间进行转换，这样内核指针永远不会暴露给用户空间，并且用户空间无法欺骗内核去跟随错误的指针。

这也使得当进程退出时内核能够清理，并防止一个进程触及另一个进程的资源。
内存固定 (Memory Pinning)
===========================

直接用户空间I/O要求潜在的I/O目标内存区域在相同的物理地址上保持常驻。ib_uverbs模块通过get_user_pages()和put_page()调用管理内存区域的固定与解除固定。它还计算进程的pinned_vm中固定的内存数量，并确保非特权进程不会超过其RLIMIT_MEMLOCK限制。

被多次固定的页面每次固定时都会被计数，因此pinned_vm的值可能高估了进程实际固定的页面数量。

/dev 文件
==========

为了自动使用udev创建合适的字符设备文件，可以使用如下规则：

```
KERNEL=="uverbs*", NAME="infiniband/%k"
```

这将创建名为：

```
/dev/infiniband/uverbs0
```

等的设备节点。由于InfiniBand用户空间verbs对于非特权进程应该是安全的，因此在udev规则中添加适当的MODE或GROUP可能是有用的。
