====================
每个CPU的读写信号量
====================

每个CPU的读写信号量是一种新的读写信号量设计，针对读取锁定进行了优化。
传统读写信号量的问题在于，当多个核心获取读取锁时，包含信号量的缓存行会在这些核心的L1缓存之间来回传递，导致性能下降。
读取锁定非常快，它使用RCU（Read-Copy-Update）机制，并且在锁定和解锁路径中避免了任何原子指令。另一方面，写入锁定非常昂贵，因为它调用了synchronize_rcu()函数，这可能会耗时数百毫秒。
该锁通过“struct percpu_rw_semaphore”类型声明。
该锁通过percpu_init_rwsem进行初始化，成功时返回0，分配失败时返回-ENOMEM。
必须使用percpu_free_rwsem释放锁以避免内存泄漏。
该锁通过percpu_down_read和percpu_up_read进行读取锁定，通过percpu_down_write和percpu_up_write进行写入锁定。
使用RCU进行优化读写锁的想法由Eric Dumazet <eric.dumazet@gmail.com>提出。
代码由Mikulas Patocka <mpatocka@redhat.com>编写。
