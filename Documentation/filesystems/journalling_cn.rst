### Linux 日志 API

#### 概览

#### 详情

日志层易于使用。首先，你需要创建一个 `journal_t` 数据结构。有两种方法来实现这一点，取决于你如何分配存放日志的实际介质。如果你的日志存储在文件系统的inode中，可以调用 `jbd2_journal_init_inode()`；如果你的日志存储在一个原始设备（连续块范围）上，则可以使用 `jbd2_journal_init_dev()`。`journal_t` 是一个指向结构体的类型定义，因此当你最终完成使用后，请确保调用 `jbd2_journal_destroy()` 来释放任何已使用的内核内存。

一旦你获得了 `journal_t` 对象，你需要“挂载”或加载日志文件。日志层期望日志的空间已经被用户空间工具正确地分配和初始化。

在加载日志时，必须调用 `jbd2_journal_load()` 来处理日志内容。如果客户端文件系统检测到日志内容不需要处理（甚至不需要有有效内容），可以在调用 `jbd2_journal_load()` 之前调用 `jbd2_journal_wipe()` 来清除日志内容。

请注意，`jbd2_journal_wipe(...,0)` 调用会为你调用 `jbd2_journal_skip_recovery()`，如果它检测到日志中有未完成的事务，并且类似地，`jbd2_journal_load()` 在必要时会调用 `jbd2_journal_recover()`。我建议阅读 `fs/ext4/super.c` 中的 `ext4_load_journal()` 函数以获取此阶段的例子。

现在你可以开始修改底层文件系统了，几乎可以了。

你仍然需要实际记录你的文件系统更改，这通过将它们包装成事务来实现。此外，还需要用日志层的调用来包装每个缓冲区（块）的修改，以便它知道你实际在做什么修改。为此，可以使用 `jbd2_journal_start()`，它返回一个事务句柄。

`jbd2_journal_start()` 和其对应函数 `jbd2_journal_stop()` 是可嵌套调用的，因此如果你有必要可以重新进入一个事务，但请记住，在事务完成（更准确地说是离开更新阶段）之前，你必须调用相同次数的 `jbd2_journal_stop()`。Ext4/VFS 利用此功能简化了inode脏页处理、配额支持等功能。

在每个事务内部，你需要用日志层的调用来包装对各个缓冲区（块）的修改。在开始修改缓冲区之前，需要根据情况调用 `jbd2_journal_get_create_access()` / `jbd2_journal_get_write_access()` / `jbd2_journal_get_undo_access()`，这样可以让日志层在需要时复制未修改的数据。毕竟，该缓冲区可能是先前未提交的事务的一部分。此时你终于可以修改缓冲区了，一旦修改完毕，需要调用 `jbd2_journal_dirty_metadata()`。或者，如果你请求访问一个缓冲区，并且现在知道这个缓冲区不再需要推回到设备上，你可以像过去使用 `bforget()` 那样调用 `jbd2_journal_forget()`。

可以在任何时候调用 `jbd2_journal_flush()` 来提交并检查点所有事务。
然后在卸载（umount）时，在你的 `put_super()` 函数中可以调用 `jbd2_journal_destroy()` 来清理内核中的日志对象。
不幸的是，日志层可能会导致几种死锁的情况。首先需要注意的是，每个任务在同一时间只能有一个未完成的事务，记住没有任何操作会在最外层的 `jbd2_journal_stop()` 之前提交。这意味着你必须在执行每个文件/inode/地址等操作的末尾完成事务，以便日志系统不会在另一个日志上重新进入。由于事务不能跨不同的日志嵌套/批处理，并且除了你的文件系统之外（例如 ext4）可能在后续的系统调用中被修改。

需要考虑的第二种情况是 `jbd2_journal_start()` 在日志中没有足够的空间用于你的事务（基于传递的 `nblocks` 参数）时可能会阻塞 —— 当它阻塞时，仅仅是等待其他任务中的事务完成并提交，因此我们实际上是在等待 `jbd2_journal_stop()`。为了避免死锁，你必须将 `jbd2_journal_start()` 和 `jbd2_journal_stop()` 视为信号量，并将其包含在信号量排序规则中以防止死锁。请注意，`jbd2_journal_extend()` 的阻塞行为与 `jbd2_journal_start()` 类似，因此你在这里也可能会遇到死锁。尽量第一次就预留正确的块数。这将是此次事务中要访问的最大块数。我建议至少查看一下 `ext4_jbd.h`，看看 ext4 是如何做出这些决策的。

还需要注意的一个问题是你的磁盘块分配策略。为什么？因为如果你执行删除操作，你需要确保在释放这些块之前不要重用任何已释放的块，直到释放这些块的事务提交。如果你重用了这些块并且发生崩溃，就没有办法在最后一个完全提交的事务结束时恢复重新分配块的内容。一个简单的方法是在释放这些块的事务提交之后，仅在内部内存块分配结构中标记这些块为可用。ext4 使用日志提交回调函数来实现这一点。

通过日志提交回调函数，你可以要求日志层在事务最终提交到磁盘时调用一个回调函数，从而进行一些自己的管理。你只需设置 `journal->j_commit_callback` 函数指针，该函数会在每次事务提交后被调用。你还可以使用 `transaction->t_private_list` 将需要在事务提交时处理的条目附加到事务上。

JBD2 还提供了一种通过 `jbd2_journal_lock_updates()` 和 `jbd2_journal_unlock_updates()` 阻止所有事务更新的方式。ext4 在需要一个干净稳定的文件系统窗口时会使用这种方法。例如：

```c
jbd2_journal_lock_updates(); // 停止新数据的发生
jbd2_journal_flush();        // 检查点所有内容
// 在稳定文件系统上执行操作
jbd2_journal_unlock_updates(); // 继续使用文件系统
```
滥用和DOS攻击的机会应该是显而易见的，如果你允许非特权用户空间触发包含这些调用的代码路径。

快速提交
~~~~~~~~~~~~

JBD2还允许你执行特定文件系统的增量提交，称为快速提交。为了使用快速提交，你需要设置以下回调函数来完成相应的工作：

`journal->j_fc_cleanup_cb`：在每次完整提交和快速提交后调用的清理函数。
`journal->j_fc_replay_cb`：用于快速提交块重播时调用的重播函数。

只要文件系统通过调用函数 `jbd2_fc_begin_commit()` 获得JBD2的许可，它就可以随时进行快速提交。一旦快速提交完成，客户端文件系统应通过调用 `jbd2_fc_end_commit()` 告知JBD2。如果文件系统希望在停止快速提交后立即让JBD2执行完整提交，则可以通过调用 `jbd2_fc_end_commit_fallback()` 来实现。这在快速提交操作因某些原因失败，并且唯一能保证一致性的方法是让JBD2执行完整的传统提交时非常有用。

JBD2提供了一些辅助函数来管理快速提交缓冲区。文件系统可以使用 `jbd2_fc_get_buf()` 和 `jbd2_fc_wait_bufs()` 来分配和等待快速提交缓冲区的IO完成。

目前，只有Ext4实现了快速提交。关于其快速提交的具体实现，请参阅 `fs/ext4/fast_commit.c` 中的顶层注释。

总结
~~~~~~~

使用日志记录层是一个将不同的上下文变化包装起来的过程，包括每次挂载、每次修改（事务）以及每个已更改的缓冲区，以告知日志记录层。

数据类型
----------

日志记录层使用typedef隐藏了所用结构的具体定义。作为JBD2层的客户端，你可以仅依赖于将指针作为一种某种意义上的魔术令牌来使用。显然，这种隐藏在C语言中并不强制实施。

结构体
~~~~~~~~~~

.. kernel-doc:: include/linux/jbd2.h
   :internal:

函数
---------

这里的函数分为两大类：一类影响整个日志，另一类用于管理事务。

日志级别
~~~~~~~~~~~~~

.. kernel-doc:: fs/jbd2/journal.c
   :export:

.. kernel-doc:: fs/jbd2/recovery.c
   :internal:

事务级别
~~~~~~~~~~~~~~~~~~

.. kernel-doc:: fs/jbd2/transaction.c

参考
--------

`Linux ext2fs 文件系统的日志记录，LinuxExpo 98，Stephen Tweedie <http://kernel.org/pub/linux/kernel/people/sct/ext3/journal-design.ps.gz>`__

`Ext3 日志记录文件系统，OLS 2000，Dr. Stephen Tweedie <http://olstrans.sourceforge.net/release/OLS2000-ext3/OLS2000-ext3.html>`__
