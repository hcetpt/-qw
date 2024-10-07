SPDX 许可证标识符: GPL-2.0

=================
Lockdep-RCU 警告
=================

Lockdep-RCU 于 2010 年初被添加到 Linux 内核中（http://lwn.net/Articles/371986/）。此功能检查一些常见的 RCU API 使用错误，尤其是使用 rcu_dereference() 家族中的某个函数访问受 RCU 保护的指针而没有适当的保护。当检测到此类误用时，会发出 Lockdep-RCU 警告。

Lockdep-RCU 警告通常的原因是有人在没有（1）处于正确的 RCU 读临界区或（2）持有正确的更新锁的情况下访问受 RCU 保护的数据结构。这个问题可能是严重的：可能会导致随机内存覆盖甚至更糟糕的情况。当然，也可能存在误报，毕竟这是现实世界中的情况。

让我们来看一个来自 3.0-rc5 的已修复的 Lockdep-RCU 警告示例：

```
============================
WARNING: suspicious RCU usage
-----------------------------
block/cfq-iosched.c:2776 suspicious rcu_dereference_protected() usage!

其他有助于调试的信息如下：

rcu_scheduler_active = 1, debug_locks = 0
3 locks held by scsi_scan_6/1552:
#0:  (&shost->scan_mutex){+.+.}, at: [<ffffffff8145efca>]
scsi_scan_host_selected+0x5a/0x150
#1:  (&eq->sysfs_lock){+.+.}, at: [<ffffffff812a5032>]
elevator_exit+0x22/0x60
#2:  (&(&q->__queue_lock)->rlock){-.-.}, at: [<ffffffff812b6233>]
cfq_exit_queue+0x43/0x190

堆栈回溯：
Pid: 1552, comm: scsi_scan_6 Not tainted 3.0.0-rc5 #17
Call Trace:
[<ffffffff810abb9b>] lockdep_rcu_dereference+0xbb/0xc0
[<ffffffff812b6139>] __cfq_exit_single_io_context+0xe9/0x120
[<ffffffff812b626c>] cfq_exit_queue+0x7c/0x190
[<ffffffff812a5046>] elevator_exit+0x36/0x60
[<ffffffff812a802a>] blk_cleanup_queue+0x4a/0x60
[<ffffffff8145cc09>] scsi_free_queue+0x9/0x10
[<ffffffff81460944>] __scsi_remove_device+0x84/0xd0
[<ffffffff8145dca3>] scsi_probe_and_add_lun+0x353/0xb10
[<ffffffff817da069>] ? error_exit+0x29/0xb0
[<ffffffff817d98ed>] ? _raw_spin_unlock_irqrestore+0x3d/0x80
[<ffffffff8145e722>] __scsi_scan_target+0x112/0x680
[<ffffffff812c690d>] ? trace_hardirqs_off_thunk+0x3a/0x3c
[<ffffffff817da069>] ? error_exit+0x29/0xb0
[<ffffffff812bcc60>] ? kobject_del+0x40/0x40
[<ffffffff8145ed16>] scsi_scan_channel+0x86/0xb0
[<ffffffff8145f0b0>] scsi_scan_host_selected+0x140/0x150
[<ffffffff8145f149>] do_scsi_scan_host+0x89/0x90
[<ffffffff8145f170>] do_scan_async+0x20/0x160
[<ffffffff8145f150>] ? do_scsi_scan_host+0x90/0x90
[<ffffffff810975b6>] kthread+0xa6/0xb0
[<ffffffff817db154>] kernel_thread_helper+0x4/0x10
[<ffffffff81066430>] ? finish_task_switch+0x80/0x110
[<ffffffff817d9c04>] ? retint_restore_args+0xe/0xe
[<ffffffff81097510>] ? __kthread_init_worker+0x70/0x70
[<ffffffff817db150>] ? gs_change+0xb/0xb
```

3.0-rc5 版本中 block/cfq-iosched.c 文件第 2776 行如下：

```c
if (rcu_dereference(ioc->ioc_data) == cic) {
```

这种形式表明必须在一个普通的 RCU 读临界区内执行，但上面的“其他信息”列表显示这不是实际情况。相反，我们持有了三个锁，其中一个可能是与 RCU 相关的。也许这个锁确实保护了这个引用。如果是这样，修复方法是通知 RCU，例如通过将 cfq_exit_queue() 中的 struct request_queue "q" 作为参数传递给 __cfq_exit_single_io_context()，这允许我们如下调用 rcu_dereference_protected：

```c
if (rcu_dereference_protected(ioc->ioc_data,
			      lockdep_is_held(&q->queue_lock)) == cic) {
```

有了这一更改，如果这段代码是在 RCU 读临界区内或持有 ->queue_lock 时调用，则不会发出 Lockdep-RCU 警告。特别是，这会抑制上述 Lockdep-RCU 警告，因为 ->queue_lock 已经被持有（参见上面列表中的 #2）。

另一方面，也许我们确实需要一个 RCU 读临界区。在这种情况下，临界区必须跨越 rcu_dereference() 返回值的使用，或者至少直到某个引用计数递增或其他类似操作。一种处理方法是添加 rcu_read_lock() 和 rcu_read_unlock() 如下：

```c
rcu_read_lock();
if (rcu_dereference(ioc->ioc_data) == cic) {
    spin_lock(&ioc->lock);
    rcu_assign_pointer(ioc->ioc_data, NULL);
    spin_unlock(&ioc->lock);
}
rcu_read_unlock();
```

有了这一更改，rcu_dereference() 总是在 RCU 读临界区内执行，这同样会抑制上述 Lockdep-RCU 警告。

但在这种特定情况下，我们实际上并没有对从 rcu_dereference() 返回的指针进行解引用。相反，该指针只是与 cic 指针进行比较，这意味着可以将 rcu_dereference() 替换为 rcu_access_pointer() 如下：

```c
if (rcu_access_pointer(ioc->ioc_data) == cic) {
```

由于可以合法地在没有保护的情况下调用 rcu_access_pointer()，这一更改同样会抑制上述 Lockdep-RCU 警告。
