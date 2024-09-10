锁定
=====

下面的文本描述了与VFS相关方法的锁定规则。这些规则被认为是最新且准确的。*请*，如果您在原型或锁定协议中进行了任何更改，请更新此文件。同时，请更新树中的相关实例，不要将此任务留给文件系统/设备等维护者。至少，请在文件末尾列出所有可疑情况。不要将其变成日志——树外代码的维护者应该能够使用`diff(1)`。

目前缺少的内容：套接字操作。Alexey？

`dentry_operations`
===================

原型::
    
    int (*d_revalidate)(struct dentry *, unsigned int);
    int (*d_weak_revalidate)(struct dentry *, unsigned int);
    int (*d_hash)(const struct dentry *, struct qstr *);
    int (*d_compare)(const struct dentry *, unsigned int, const char *, const struct qstr *);
    int (*d_delete)(struct dentry *);
    int (*d_init)(struct dentry *);
    void (*d_release)(struct dentry *);
    void (*d_iput)(struct dentry *, struct inode *);
    char *(*d_dname)((struct dentry *dentry, char *buffer, int buflen);
    struct vfsmount *(*d_automount)(struct path *path);
    int (*d_manage)(const struct path *, bool);
    struct dentry *(*d_real)(struct dentry *, enum d_real_type type);

锁定规则:

================== =========== ======== =============== ========
操作              rename_lock ->d_lock 可能阻塞  RCU遍历
================== =========== ======== =============== ========
d_revalidate:      否         否        是（引用遍历）   可能
d_weak_revalidate: 否         否        是              否
d_hash             否         否        否              可能
d_compare:         是         否        否              可能
d_delete:          否         是        否              否
d_init:            否         否        是              否
d_release:         否         否        是              否
d_prune:           否         是        否              否
d_iput:            否         否        是              否
d_dname:           否         否        否              否
d_automount:       否         否        是              否
d_manage:          否         否        是（引用遍历）   可能
d_real             否         否        是              否
================== =========== ======== =============== ========

`inode_operations`
==================

原型::

    int (*create)(struct mnt_idmap *, struct inode *, struct dentry *, umode_t, bool);
    struct dentry *(*lookup)(struct inode *, struct dentry *, unsigned int);
    int (*link)(struct dentry *, struct inode *, struct dentry *);
    int (*unlink)(struct inode *, struct dentry *);
    int (*symlink)(struct mnt_idmap *, struct inode *, struct dentry *, const char *);
    int (*mkdir)(struct mnt_idmap *, struct inode *, struct dentry *, umode_t);
    int (*rmdir)(struct inode *, struct dentry *);
    int (*mknod)(struct mnt_idmap *, struct inode *, struct dentry *, umode_t, dev_t);
    int (*rename)(struct mnt_idmap *, struct inode *, struct dentry *, struct inode *, struct dentry *, unsigned int);
    int (*readlink)(struct dentry *, char __user *, int);
    const char *(*get_link)(struct dentry *, struct inode *, struct delayed_call *);
    void (*truncate)(struct inode *);
    int (*permission)(struct mnt_idmap *, struct inode *, int, unsigned int);
    struct posix_acl *(*get_inode_acl)(struct inode *, int, bool);
    int (*setattr)(struct mnt_idmap *, struct dentry *, struct iattr *);
    int (*getattr)(struct mnt_idmap *, const struct path *, struct kstat *, u32, unsigned int);
    ssize_t (*listxattr)(struct dentry *, char *, size_t);
    int (*fiemap)(struct inode *, struct fiemap_extent_info *, u64 start, u64 len);
    void (*update_time)(struct inode *, struct timespec *, int);
    int (*atomic_open)(struct inode *, struct dentry *, struct file *, unsigned open_flag, umode_t create_mode);
    int (*tmpfile)(struct mnt_idmap *, struct inode *, struct file *, umode_t);
    int (*fileattr_set)(struct mnt_idmap *idmap, struct dentry *dentry, struct fileattr *fa);
    int (*fileattr_get)(struct dentry *dentry, struct fileattr *fa);
    struct posix_acl *(*get_acl)(struct mnt_idmap *, struct dentry *, int);
    struct offset_ctx *(*get_offset_ctx)(struct inode *inode);

锁定规则：
所有操作都可能阻塞

============== ===================================================
操作           i_rwsem(inode)
============== ===================================================
lookup:        共享
create:        独占
link:          独占（双方）
mknod:         独占
symlink:       独占
mkdir:         独占
unlink:        独占（双方）
rmdir:         独占（双方）（参见下方）
rename:        独占（双方父目录，部分子目录）（参见下方）
readlink:      否
get_link:      否
setattr:       独占
permission:    否（如果在RCU遍历模式下调用，则不会阻塞）
get_inode_acl: 否
get_acl:       否
getattr:       否
listxattr:     否
fiemap:        否
update_time:   否
atomic_open:   共享（如果打开标志中设置了O_CREAT，则为独占）
tmpfile:       否
fileattr_get:  否或独占
fileattr_set:  独占
get_offset_ctx 否
============== ===================================================

此外，`->rmdir()`、`->unlink()` 和 `->rename()` 在受害者上具有 `i_rwsem` 独占。
跨目录 `->rename()` 操作具有（每个超级块）`s_vfs_rename_sem`。
`->unlink()` 和 `->rename()` 在所有非目录项上具有 `i_rwsem` 独占。
`->rename()` 在任何更改父目录的子目录上具有 `i_rwsem` 独占。
关于目录操作的锁定方案详细讨论，请参阅 `Documentation/filesystems/directory-locking.rst`。

`xattr_handler` 操作
====================

原型::

    bool (*list)(struct dentry *dentry);
    int (*get)(const struct xattr_handler *handler, struct dentry *dentry, struct inode *inode, const char *name, void *buffer, size_t size);
    int (*set)(const struct xattr_handler *handler, struct mnt_idmap *idmap, struct dentry *dentry, struct inode *inode, const char *name, const void *buffer, size_t size, int flags);

锁定规则：
所有操作都可能阻塞

===== ===============
操作     i_rwsem(inode)
===== ===============
list:    否
get:     否
set:     独占
===== ===============

`super_operations`
==================

原型::

    struct inode *(*alloc_inode)(struct super_block *sb);
    void (*free_inode)(struct inode *);
    void (*destroy_inode)(struct inode *);
    void (*dirty_inode)(struct inode *, int flags);
    int (*write_inode)(struct inode *, struct writeback_control *wbc);
    int (*drop_inode)(struct inode *);
    void (*evict_inode)(struct inode *);
    void (*put_super)(struct super_block *);
    int (*sync_fs)(struct super_block *sb, int wait);
    int (*freeze_fs)(struct super_block *);
    int (*unfreeze_fs)(struct super_block *);
    int (*statfs)(struct dentry *, struct kstatfs *);
    int (*remount_fs)(struct super_block *, int *, char *);
    void (*umount_begin)(struct super_block *);
    int (*show_options)(struct seq_file *, struct dentry *);
    ssize_t (*quota_read)(struct super_block *, int, char *, size_t, loff_t);
    ssize_t (*quota_write)(struct super_block *, int, const char *, size_t, loff_t);

锁定规则：
所有操作都可能阻塞[不完全正确，参见下方]

====================== ============= =========================
操作               s_umount    注释
====================== ============= =========================
alloc_inode:
free_inode:                  从RCU回调中调用
destroy_inode:
dirty_inode:
write_inode:
drop_inode:                  !!!inode->i_lock!!!
evict_inode:
put_super:       写
sync_fs:         读
freeze_fs:       写
unfreeze_fs:     写
statfs:          可能（读）（参见下方）
remount_fs:      写
umount_begin:    否
show_options:    否（命名空间锁）
quota_read:      否（参见下方）
quota_write:     否（参见下方）
====================== ============= =========================

`->statfs()` 在被 `ustat(2)`（本机或兼容）调用时会持有 `s_umount`（共享），但这只是由于API设计不佳；`s_umount` 用于在仅通过用户空间提供的 `dev_t` 来识别超级块时固定超级块。其他一切（如 `statfs()`、`fstatfs()` 等）在调用 `->statfs()` 时不持有它，因为超级块通过解析传递给系统调用的路径名来固定。
`->quota_read()` 和 `->quota_write()` 函数都由配额代码通过 `dqio_sem` 保证是唯一操作配额文件的函数（除非管理员真的想搞破坏并直接写入配额文件）。有关更多锁定细节，请参阅 `dquot_operations` 部分。
文件系统类型
================

原型::

    struct dentry *(*mount) (struct file_system_type *, int,
               const char *, void *);
    void (*kill_sb) (struct super_block *);

锁定规则:

=======		=========
操作		可能阻塞
=======		=========
mount		是
kill_sb		是
=======		=========

-> mount() 返回 ERR_PTR 或根目录项；返回时其超级块应被锁定
-> kill_sb() 接收一个写锁定的超级块，执行所有关闭工作，解锁并释放引用

地址空间操作
========================
原型::

    int (*writepage)(struct page *page, struct writeback_control *wbc);
    int (*read_folio)(struct file *, struct folio *);
    int (*writepages)(struct address_space *, struct writeback_control *);
    bool (*dirty_folio)(struct address_space *, struct folio *folio);
    void (*readahead)(struct readahead_control *);
    int (*write_begin)(struct file *, struct address_space *mapping,
                       loff_t pos, unsigned len,
                       struct page **pagep, void **fsdata);
    int (*write_end)(struct file *, struct address_space *mapping,
                     loff_t pos, unsigned len, unsigned copied,
                     struct page *page, void *fsdata);
    sector_t (*bmap)(struct address_space *, sector_t);
    void (*invalidate_folio) (struct folio *, size_t start, size_t len);
    bool (*release_folio)(struct folio *, gfp_t);
    void (*free_folio)(struct folio *);
    int (*direct_IO)(struct kiocb *, struct iov_iter *iter);
    int (*migrate_folio)(struct address_space *, struct folio *dst,
                         struct folio *src, enum migrate_mode);
    int (*launder_folio)(struct folio *);
    bool (*is_partially_uptodate)(struct folio *, size_t from, size_t count);
    int (*error_remove_folio)(struct address_space *, struct folio *);
    int (*swap_activate)(struct swap_info_struct *sis, struct file *f, sector_t *span);
    int (*swap_deactivate)(struct file *);
    int (*swap_rw)(struct kiocb *iocb, struct iov_iter *iter);

锁定规则:
除了 dirty_folio 和 free_folio 外的所有操作都可能阻塞

======================	======================== =========	===============
操作			folio 锁定		 i_rwsem	invalidate_lock
======================	======================== =========	===============
writepage:		是，解锁（见下文）
read_folio:		是，解锁				共享
writepages:
dirty_folio:		可能
readahead:		是，解锁				共享
write_begin:		锁定页面		 独占
write_end:		是，解锁		 独占
bmap:
invalidate_folio:	是					独占
release_folio:		是
free_folio:		是
direct_IO:
migrate_folio:		是（两个）
launder_folio:		是
is_partially_uptodate:	是
error_remove_folio:	是
swap_activate:		否
swap_deactivate:	否
swap_rw:		是，解锁
======================	======================== =========	===============

-> write_begin()、-> write_end() 和 -> read_folio() 可能从请求处理器 (/dev/loop) 调用
-> read_folio() 解锁 folio，无论是同步还是通过 I/O 完成
-> readahead() 解锁尝试进行 I/O 的 folio，就像 -> read_folio()
-> writepage() 用于两种目的：内存清理和同步。这些是相当不同的操作，并且行为可能因模式而异
如果 writepage 被调用以进行同步（wbc->sync_mode != WBC_SYNC_NONE），则必须启动针对页面的 I/O，即使这需要阻塞正在进行的 I/O
如果 writepage 被调用以进行内存清理（sync_mode == WBC_SYNC_NONE），则其作用是尽可能多地开始写入。因此，writepage 应尽量避免阻塞当前正在进行的 I/O
如果文件系统未被要求进行“同步”，并且确定需要阻塞正在进行的 I/O 才能启动针对页面的新 I/O，则文件系统应使用 redirty_page_for_writepage() 标记页面为脏，然后解锁页面并返回零
这也可能为了防止内部死锁而完成，但很少如此。
如果文件系统被要求进行同步（sync），则必须等待任何正在进行的I/O操作，然后开始新的I/O操作。
文件系统应该同步解锁页面，在返回给调用者之前，除非`->writepage()`返回特殊的`WRITEPAGE_ACTIVATE`值。`WRITEPAGE_ACTIVATE`表示当前页面实际上不能被写入，虚拟内存（VM）应暂时停止对该页面调用`->writepage()`。VM通过将页面移动到活动列表的头部来实现这一点，因此得名。
除非文件系统打算调用`redirty_page_for_writepage()`，否则应解锁页面并返回零；否则，`writepage`必须对页面运行`set_page_writeback()`，然后再解锁它。一旦对页面运行了`set_page_writeback()`，就可以提交写I/O操作，并且在I/O完成时，写I/O完成处理程序必须运行`end_page_writeback()`。如果没有提交I/O，则文件系统必须在从`writepage`返回前对页面运行`end_page_writeback()`。

也就是说：在2.5.12之后，正在写入中的页面*不是*锁定状态。注意，如果文件系统需要在写入过程中锁定页面，那也是可以的，页面可以在`set_page_writeback()`和`end_page_writeback()`调用之间的任何时候解锁。

请注意，未能对提交给`writepage`的页面运行`redirty_page_for_writepage()`或`set_page_writeback()/end_page_writeback()`组合，将导致页面本身标记为干净，但在radix树中仍标记为脏。这种不一致性会导致文件系统中各种难以调试的问题，例如卸载时有脏inode和丢失已写入的数据。

`->writepages()`用于周期性回写和由系统调用触发的同步操作。地址空间应对至少`*nr_to_write`个页面启动I/O操作。对于每个已写入的页面，`*nr_to_write`必须递减。地址空间实现可以写入比`*nr_to_write`请求的更多（或更少）的页面，但它应尽量接近这个数目。
如果`nr_to_write`为NULL，则必须写入所有脏页面。
`writepages`应仅写入`mapping->io_pages`中存在的页面。
当目标folio被标记为需要回写时，内核中的多个地方会调用`->dirty_folio()`。由于调用者持有folio锁，或者调用者在持有页表锁的情况下找到folio，这会阻止截断操作，因此folio不能被截断。
`->bmap()`目前由一些文件系统提供的遗留ioctl()（FIBMAP）和交换器使用。后者最终会被移除。请保持现状，不要增加新的调用者。
```invalidate_folio()`在文件系统尝试在截断页面时丢弃页面的一些或所有缓冲区时被调用。成功时返回零。文件系统必须在无效化页面缓存之前独占获取`invalidate_lock`，以阻止页面缓存无效化和页面缓存填充函数（如fault、read等）之间的竞争。

`release_folio()`在MM（内存管理器）需要对folio进行更改，这将使文件系统的私有数据失效时被调用。例如，它可能即将从地址空间中移除或拆分。此时folio已被锁定且不在回写中。它可能是脏的。gfp参数通常不用于分配，而是用来指示文件系统可以采取什么措施来释放私有数据。如果文件系统返回false，则表示folio的私有数据无法被释放。如果返回true，则应已从folio中移除了私有数据。如果文件系统没有提供`release_folio`方法，页面缓存将假设私有数据为buffer_heads，并调用`try_to_free_buffers()`。

`free_folio()`在内核从页面缓存中移除folio时被调用。

`launder_folio()`可能在释放folio之前被调用，如果发现它仍然是脏的。成功清理后返回零，否则返回错误值。请注意，为了防止folio重新映射并再次变脏，需要在整个操作过程中保持其锁定状态。

`swap_activate()`将被调用以准备给定文件进行交换。它应执行任何必要的验证和准备工作，以确保能够以最小的内存分配执行写入。它应调用`add_swap_extent()`或辅助函数`iomap_swapfile_activate()`，并返回添加的extent数量。如果IO应通过`swap_rw()`提交，则应设置SWP_FS_OPS；否则，IO将直接提交到块设备`sis->bdev`。

`swap_deactivate()`将在sys_swapoff()路径中被调用，在`swap_activate()`返回成功之后。

`swap_rw`将在设置了SWP_FS_OPS的情况下被调用以处理交换IO。

file_lock_operations
====================

原型::

    void (*fl_copy_lock)(struct file_lock *, struct file_lock *);
    void (*fl_release_private)(struct file_lock *);

锁定规则:

===================	=============	=========
操作			i_lock	是否可阻塞
===================	=============	=========
fl_copy_lock:		是	否
fl_release_private:	也许	也许[1]_
===================	=============	=========

.. [1]: 对于flock或POSIX锁，当前允许`fl_release_private`阻塞。然而，租约可以在持有i_lock时被释放，因此对租约调用`fl_release_private`时不应阻塞。

lock_manager_operations
=======================

原型::

    void (*lm_notify)(struct file_lock *);  /* 解除阻塞回调 */
    int (*lm_grant)(struct file_lock *, struct file_lock *, int);
    void (*lm_break)(struct file_lock *); /* 租约解除回调 */
    int (*lm_change)(struct file_lock **, int);
    bool (*lm_breaker_owns_lease)(struct file_lock *);
    bool (*lm_lock_expirable)(struct file_lock *);
    void (*lm_expire_lock)(void);

锁定规则:

======================	=============	=================	=========
操作			   flc_lock   blocked_lock_lock	是否可阻塞
======================	=============	=================	=========
lm_notify:		否      	是			否
lm_grant:		否		否			否
lm_break:		是		否			否
lm_change:		是		否			否
lm_breaker_owns_lease:	是     	否			否
lm_lock_expirable:	是		否			否
lm_expire_lock:	否		否			是
======================	=============	=================	=========

buffer_head
===========

原型::

    void (*b_end_io)(struct buffer_head *bh, int uptodate);

锁定规则:

从中断中调用。换句话说，这里需要极其小心。
```
bh被锁定，但这是我们这里所有的保证。目前只有RAID1、高内存、fs/buffer.c和fs/ntfs/aops.c提供了这些功能。块设备在IO完成时调用此方法。

`block_device_operations`
=======================
原型：
```
int (*open) (struct block_device *, fmode_t);
int (*release) (struct gendisk *, fmode_t);
int (*ioctl) (struct block_device *, fmode_t, unsigned, unsigned long);
int (*compat_ioctl) (struct block_device *, fmode_t, unsigned, unsigned long);
int (*direct_access) (struct block_device *, sector_t, void **, unsigned long *);
void (*unlock_native_capacity) (struct gendisk *);
int (*getgeo)(struct block_device *, struct hd_geometry *);
void (*swap_slot_free_notify) (struct block_device *, unsigned long);
```

锁定规则：

```
======================= ===================
ops			open_mutex
======================= ===================
open:			是
release:		是
ioctl:			否
compat_ioctl:		否
direct_access:		否
unlock_native_capacity:	否
getgeo:			否
swap_slot_free_notify:	否（见下文）
======================= ===================
```

`swap_slot_free_notify`是在持有swap_lock的情况下被调用，并且有时会持有页面锁。

`file_operations`
===============
原型：
```
loff_t (*llseek) (struct file *, loff_t, int);
ssize_t (*read) (struct file *, char __user *, size_t, loff_t *);
ssize_t (*write) (struct file *, const char __user *, size_t, loff_t *);
ssize_t (*read_iter) (struct kiocb *, struct iov_iter *);
ssize_t (*write_iter) (struct kiocb *, struct iov_iter *);
int (*iopoll) (struct kiocb *kiocb, bool spin);
int (*iterate_shared) (struct file *, struct dir_context *);
__poll_t (*poll) (struct file *, struct poll_table_struct *);
long (*unlocked_ioctl) (struct file *, unsigned int, unsigned long);
long (*compat_ioctl) (struct file *, unsigned int, unsigned long);
int (*mmap) (struct file *, struct vm_area_struct *);
int (*open) (struct inode *, struct file *);
int (*flush) (struct file *);
int (*release) (struct inode *, struct file *);
int (*fsync) (struct file *, loff_t start, loff_t end, int datasync);
int (*fasync) (int, struct file *, int);
int (*lock) (struct file *, int, struct file_lock *);
unsigned long (*get_unmapped_area)(struct file *, unsigned long,
			unsigned long, unsigned long, unsigned long);
int (*check_flags)(int);
int (*flock) (struct file *, int, struct file_lock *);
ssize_t (*splice_write)(struct pipe_inode_info *, struct file *, loff_t *,
			size_t, unsigned int);
ssize_t (*splice_read)(struct file *, loff_t *, struct pipe_inode_info *,
			size_t, unsigned int);
int (*setlease)(struct file *, long, struct file_lock **, void **);
long (*fallocate)(struct file *, int, loff_t, loff_t);
void (*show_fdinfo)(struct seq_file *m, struct file *f);
unsigned (*mmap_capabilities)(struct file *);
ssize_t (*copy_file_range)(struct file *, loff_t, struct file *,
			loff_t, size_t, unsigned int);
loff_t (*remap_file_range)(struct file *file_in, loff_t pos_in,
			struct file *file_out, loff_t pos_out,
			loff_t len, unsigned int remap_flags);
int (*fadvise)(struct file *, loff_t, loff_t, int);
```

锁定规则：
所有函数都可能阻塞。
- `llseek()`的锁定已从`llseek`移动到各个`llseek`实现中。如果您的文件系统没有使用`generic_file_llseek`，则需要在`->llseek()`中获取并释放适当的锁。对于许多文件系统，获取inode互斥锁或仅使用`i_size_read()`可能是安全的。
注意：这不会保护`file->f_pos`免受并发修改的影响，因为这是用户空间需要处理的问题。
- `iterate_shared()`在读取时持有`i_rwsem`，并且独占地持有`file->f_pos_lock`。

- `fasync()`负责维护`filp->f_flags`中的FASYNC位。大多数实例调用`fasync_helper()`，该函数执行此维护工作，因此通常不需要担心这个问题。返回值大于0将在VFS层映射为零。
- 目录上的`readdir()`和`ioctl()`必须更改。理想情况下，我们会将`readdir()`移动到`inode_operations`并使用一个单独的方法来处理目录`ioctl()`，或者完全删除后者。其中一个问题是对于任何类似union-mount的情况，我们不会为所有组件都有一个`struct file`。还有其他原因导致当前接口存在问题。
- 对目录的`read()`操作可能需要消失——我们应该在`sys_read()`及其相关函数中强制执行-EISDIR。
```plaintext
-> 设置租约的操作应在设置文件系统内部的租约之前或之后调用generic_setlease()，以记录操作的结果。

-> fallocate实现必须非常小心地维护页缓存的一致性，当打孔或执行其他使页缓存内容失效的操作时。通常文件系统需要调用truncate_inode_pages_range()来使相关范围的页缓存失效。然而，文件系统通常还需要更新其内部（以及磁盘上的）文件偏移到磁盘块映射。在完成此更新之前，文件系统需要阻止页错误和读取操作重新加载现在已过时的页缓存内容。由于VFS在从磁盘加载页面时获取mapping->invalidate_lock（共享模式）（filemap_fault()、filemap_read()、预读路径），fallocate实现必须获取invalidate_lock以防止重新加载。

-> copy_file_range和remap_file_range的实现需要在操作运行期间对文件数据的修改进行序列化。为了通过write(2)等操作阻止更改，可以使用inode->i_rwsem。为了阻止操作期间通过内存映射更改文件内容，文件系统必须获取mapping->invalidate_lock以与->page_mkwrite协调。

dquot_operations
================

原型::
    int (*write_dquot) (struct dquot *);
    int (*acquire_dquot) (struct dquot *);
    int (*release_dquot) (struct dquot *);
    int (*mark_dirty) (struct dquot *);
    int (*write_info) (struct super_block *, int);

这些操作旨在作为包装函数，确保文件系统锁的正确性，并调用通用配额操作。文件系统应从通用配额功能中期望什么：

==============  =============  ==========================
操作            文件系统递归   调用时持有的锁
==============  =============  ==========================
write_dquot:     是             dqonoff_sem 或 dqptr_sem
acquire_dquot:   是             dqonoff_sem 或 dqptr_sem
release_dquot:   是             dqonoff_sem 或 dqptr_sem
mark_dirty:      否             -
write_info:      是             dqonoff_sem
==============  =============  ==========================

文件系统递归意味着从超级块操作中调用->quota_read()和->quota_write()。
有关配额锁定的更多详细信息，请参阅fs/dquot.c。

vm_operations_struct
====================

原型::
    void (*open)(struct vm_area_struct *);
    void (*close)(struct vm_area_struct *);
    vm_fault_t (*fault)(struct vm_fault *);
    vm_fault_t (*huge_fault)(struct vm_fault *, unsigned int order);
    vm_fault_t (*map_pages)(struct vm_fault *, pgoff_t start, pgoff_t end);
    vm_fault_t (*page_mkwrite)(struct vm_area_struct *, struct vm_fault *);
    vm_fault_t (*pfn_mkwrite)(struct vm_area_struct *, struct vm_fault *);
    int (*access)(struct vm_area_struct *, unsigned long, void*, int, int);

锁定规则：

=============  ==========  ============================
操作           mmap_lock    PageLocked(page)
=============  ==========  ============================
open:          写入
close:         读/写
fault:         读           可能返回已锁定的页面
huge_fault:    可能读
map_pages:     可能读
page_mkwrite:  读           可能返回已锁定的页面
pfn_mkwrite:   读
access:        读
=============  ==========  ============================

->fault()在先前不存在的pte即将被错误注入时被调用。文件系统必须找到并返回与vm_fault结构中传入的"pgoff"关联的页面。如果页面可能被截断和/或无效，则文件系统必须锁定invalidate_lock，然后确保页面尚未被截断（invalidate_lock将阻止随后的截断），然后返回VM_FAULT_LOCKED，并且页面被锁定。VM将解锁页面。
->huge_fault()在没有PUD或PMD条目存在时被调用。这给文件系统提供了安装PUD或PMD大小页面的机会。文件系统也可以使用->fault方法返回一个PMD大小的页面，因此实现此函数可能不必要。特别是，文件系统不应从->huge_fault()调用filemap_fault()。
当调用此方法时，不得持有mmap_lock。
```
```->map_pages() 在虚拟内存请求映射易于访问的页面时被调用。文件系统应找到并映射从 "start_pgoff" 到 "end_pgoff" 的偏移量关联的页面。->map_pages() 是在持有 RCU 锁的情况下被调用的，因此不得阻塞。如果无法在不阻塞的情况下访问某个页面，文件系统应该跳过该页面。文件系统应使用 set_pte_range() 来设置页表项。与页面关联的条目指针通过 vm_fault 结构中的 "pte" 字段传递。其他偏移量的条目指针应相对于 "pte" 计算。

->page_mkwrite() 在先前为只读的 pte 即将变为可写时被调用。文件系统必须再次确保没有截断/无效竞争或与如 ->remap_file_range 或 ->copy_file_range 等操作的竞争，并返回锁定的页面。通常 mapping->invalidate_lock 适合适当的序列化。如果页面已被截断，文件系统不应像 ->fault() 处理程序那样查找新页面，而应仅返回 VM_FAULT_NOPAGE，这将导致虚拟内存重试错误。

->pfn_mkwrite() 与 page_mkwrite 相同，但在 pte 为 VM_PFNMAP 或 VM_MIXEDMAP 并且带有无页面条目的情况下。预期的返回值是 VM_FAULT_NOPAGE。或者 VM_FAULT_ERROR 类型之一。此调用后的默认行为是使 pte 可读写，除非 pfn_mkwrite 返回错误。

->access() 在 access_process_vm() 中 get_user_pages() 失败时被调用，通常用于通过 /proc/pid/mem 或 ptrace 调试进程。此函数仅适用于 VM_IO | VM_PFNMAP VMAs。

--------------------------------------------------------------------------------

			可疑的东西

（如果你发现某些功能有问题或注意到其存在问题但未自行修复 - 至少把它记录在这里）```
