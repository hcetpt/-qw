====================
自2.5.0以来的更改：
====================

---

**推荐**

新辅助函数：sb_bread()、sb_getblk()、sb_find_get_block()、set_bh()、sb_set_blocksize() 和 sb_min_blocksize()
使用它们
（sb_find_get_block() 替换了 2.4 版本中的 get_hash_table()）

---

**推荐**

新方法：->alloc_inode() 和 ->destroy_inode()
移除 inode->u.foo_inode_i

声明如下：

```c
struct foo_inode_info {
    /* 文件系统私有数据 */
    struct inode vfs_inode;
};

static inline struct foo_inode_info *FOO_I(struct inode *inode)
{
    return list_entry(inode, struct foo_inode_info, vfs_inode);
}
```

使用 FOO_I(inode) 而不是 &inode->u.foo_inode_i

添加 foo_alloc_inode() 和 foo_destroy_inode() — 前者应该分配 foo_inode_info 并返回 ->vfs_inode 的地址，后者应该释放 FOO_I(inode)（参见树内文件系统的示例）
将它们设置为 super_operations 中的 ->alloc_inode 和 ->destroy_inode
请注意，现在你需要在调用 iget_locked() 和解锁 inode 之间显式初始化私有数据
在某个时候这将成为强制要求
**强制**

foo_inode_info 应始终通过 alloc_inode_sb() 分配，而不是通过 kmem_cache_alloc() 或 kmalloc() 相关的方法来正确设置 inode 回收上下文

---

**强制**

文件系统类型方法的变化（从 ->read_super 变为 ->get_sb）

->read_super() 已经不再使用。同样，DECLARE_FSTYPE 和 DECLARE_FSTYPE_DEV 也不再使用
将你的 foo_read_super() 转换为一个成功时返回 0，错误时返回负数（默认为 -EINVAL，除非你有更具体的错误值）的函数，并将其命名为 foo_fill_super()。现在声明如下：

```c
int foo_get_sb(struct file_system_type *fs_type,
               int flags, const char *dev_name, void *data, struct vfsmount *mnt)
{
    return get_sb_bdev(fs_type, flags, dev_name, data, foo_fill_super, mnt);
}
```

（或者根据文件系统的类型，类似地使用 s/bdev/nodev/ 或 s/bdev/single/）
---

**替换 DECLARE_FSTYPE... 为显式的初始化器，并将 ->get_sb 设置为 foo_get_sb**

---

**强制性**

锁定变更：->s_vfs_rename_sem 只在跨目录重命名时获取。很可能你无需做任何更改，但如果你依赖于重命名之间的全局互斥来实现某些内部目的——你需要更改你的内部锁定机制。否则，互斥保证保持不变（即父目录和目标目录被锁定等）。

---

**信息性**

现在我们有了 ->lookup() 和目录移除（通过 ->rmdir() 和 ->rename() 实现）之间的互斥。如果你以前需要这种互斥并通过内部锁定实现（大多数文件系统并不关心这一点）——你现在可以放松你的锁定。

---

**强制性**

->lookup()、->truncate()、->create()、->unlink()、->mknod()、->mkdir()、->rmdir()、->link()、->lseek()、->symlink()、->rename() 和 ->readdir() 现在不再带有 BKL 调用。进入时获取 BKL，在返回时释放 BKL——这将保证你以前的锁定。如果你的方法或其部分不需要 BKL——更好，现在你可以调整 lock_kernel() 和 unlock_kernel() 的位置，以便它们只保护确实需要保护的部分。

---

**强制性**

BKL 也从 superblock 操作周围移动。BKL 应该被转移到各个 fs sb_op 函数中。如果你不需要它，请移除它。

---

**信息性**

对 ->link() 目标不是目录的检查由调用者完成。可以自由地移除它。

---

**信息性**

->link() 的调用者持有被链接对象的 ->i_mutex。你的一些问题可能已经解决了。

---

**强制性**

新的 file_system_type 方法 —— kill_sb(superblock)。如果你正在转换一个现有的文件系统，请根据 ->fs_flags 设置它：

    FS_REQUIRES_DEV       -   kill_block_super
    FS_LITTER             -   kill_litter_super
    都不满足            -   kill_anon_super

FS_LITTER 已经消失——只需从 fs_flags 中移除它。

---

**强制性**

FS_SINGLE 已经消失（实际上，当 ->get_sb() 加入时就已经发生了——只是没有记录；-/-）。只需从 fs_flags 中移除它（并参阅 ->get_sb() 条目以了解其他操作）。
**强制性**

现在调用 `->setattr()` 时不再需要 BKL。调用者 _始终_ 持有 `->i_mutex`，因此请注意可能被 `->setattr()` 使用的获取 `->i_mutex` 的代码。现在调用 `notify_change()` 需要 `->i_mutex`。

**推荐**

新增了 `super_block` 字段 `struct export_operations *s_export_op`，用于显式支持导出（例如通过 NFS）。该结构在 `include/linux/fs.h` 中进行了详细说明，并且在 `Documentation/filesystems/nfs/exporting.rst` 中也有介绍。简而言之，它允许定义 `decode_fh` 和 `encode_fh` 操作来编码和解码文件句柄，并允许文件系统使用标准辅助函数进行 `decode_fh` 操作，并提供文件系统特定的支持，特别是 `get_parent`。计划在代码稳定后要求必须使用这个字段进行导出。

**强制性**

现在导出文件系统需要 `s_export_op`。
isofs、ext2、ext3、reiserfs 和 fat 可以作为非常不同的文件系统的示例。

**强制性**

`iget4()` 和 `read_inode2` 回调已经被 `iget5_locked()` 替代，后者具有以下原型：

```c
struct inode *iget5_locked(struct super_block *sb, unsigned long ino,
                           int (*test)(struct inode *, void *),
                           int (*set)(struct inode *, void *),
                           void *data);
```

`test` 是一个附加函数，当仅凭inode号不足以识别实际文件对象时可以使用。`set` 应该是一个非阻塞函数，用于初始化新创建的inode的某些部分，以便使测试函数能够成功。`data` 作为一个不透明值传递给 `test` 和 `set` 函数。
当inode由 `iget5_locked()` 创建后，将带有 I_NEW 标志并仍然处于锁定状态。文件系统需要完成初始化。一旦inode初始化完毕，必须通过调用 `unlock_new_inode()` 来解锁。
文件系统负责在适当的时候设置（并可能测试）`i_ino`。还有一个更简单的 `iget_locked` 函数，只需要传入超级块和inode号作为参数，并为你完成测试和设置操作。
```c
inode = iget_locked(sb, ino);
if (inode->i_state & I_NEW) {
    err = read_inode_from_disk(inode);
    if (err < 0) {
        iget_failed(inode);
        return err;
    }
    unlock_new_inode(inode);
}
```

请注意，如果设置新inode的过程失败，则应调用`iget_failed()`使inode失效，并将适当的错误返回给调用者。

---

**推荐**

`->getattr()`最终被使用。请参见nfs、minix等中的实例。

---

**强制**

`->revalidate()`已移除。如果你的文件系统中曾有此函数，请提供`->getattr()`，并让它调用你之前的`->revalidate()`（对于有`->revalidate()`的符号链接，还需在`->follow_link()`和`->readlink()`中添加调用）。

---

**强制**

`->d_parent`的更改不再受BKL保护。如果满足以下条件之一，则读取访问是安全的：

* 文件系统不支持跨目录重命名（`rename()`）。
* 父目录已锁定（例如，我们正在查看`->lookup()`参数中的`->d_parent`）。
* 我们从`->rename()`调用。
* 子项的`->d_lock`已被持有。

请审核代码并根据需要添加锁。请注意，任何未受上述条件保护的地方即使在旧树中也是有风险的——你依赖于BKL，而这容易出错。旧树中有不少这样的漏洞——对`->d_parent`的无保护访问可能导致各种问题，从oops到静默内存损坏。

---

**强制**

`FS_NOMOUNT`已移除。如果你使用它，请在标志中设置`SB_NOUSER`（参见rootfs作为一类解决方案，bdev/socket/pipe作为另一类）。

---

**推荐**

使用`bdev_read_only(bdev)`代替`is_read_only(kdev)`。后者仍然存在，但仅因为drivers/s390/block/dasd.c中的混乱。一旦修复，`is_read_only()`将被废弃。

---

**强制**

`->permission()`现在在没有BKL的情况下被调用。在入口处获取BKL，在返回时释放——这将保证你之前使用的锁。如果你的方法或其部分不需要BKL，更好，现在你可以调整`lock_kernel()`和`unlock_kernel()`以保护真正需要保护的部分。
**强制要求**

- 现在调用 statfs() 时不再持有 BKL。BKL 应该被转移到各个文件系统 sb_op 函数中，在这些函数中如果确认移除它是安全的，就移除它。
  
**强制要求**

- is_read_only() 已经移除；请改用 bdev_read_only()。

**强制要求**

- destroy_buffers() 已经移除；请改用 invalidate_bdev()。

**强制要求**

- fsync_dev() 已经移除；请改用 fsync_bdev()。注意：LVM 的破坏是故意的；一旦代码中以合理的方式传播了 `struct block_device *`，修复将变得非常简单；在此之前无法进行任何操作。

**强制要求**

- 在从 `->write_begin` 和 `->direct_IO` 返回错误退出时，应进行块截断。这些操作已从通用方法（如 `block_write_begin`、`cont_write_begin`、`nobh_write_begin`、`blockdev_direct_IO*`）移到调用者中。可以参考 `ext2_write_failed` 及其调用者作为示例。

**强制要求**

- `->truncate` 已经移除。整个截断序列需要在 `->setattr` 中实现，现在对于实现磁盘大小更改的文件系统来说这是强制性的。可以从旧的 `inode_setattr` 和 `vmtruncate` 开始，并重新排序 `vmtruncate + foofs_vmtruncate` 序列，使其按照使用 `block_truncate_page` 或类似辅助函数清零块、更新大小以及最终进行磁盘截断的顺序执行。截断不应导致 `setattr_prepare` 失败（`setattr_prepare` 以前称为 `inode_change_ok`），现在必须在 `->setattr` 的开始无条件调用 `setattr_prepare` 来进行大小检查。

**强制要求**

- `->clear_inode()` 和 `->delete_inode()` 已经移除；应改用 `->evict_inode()`。此方法会在索引节点被驱逐时调用，无论索引节点是否有剩余链接。调用者不会驱逐页缓存或与索引节点关联的元数据缓冲区；该方法必须使用 `truncate_inode_pages_final()` 来清除这些缓冲区。调用者确保在调用 `->evict_inode()` 期间或之后不会运行异步写回。
- `->drop_inode()` 现在返回 int 类型；它在最终的 `iput()` 调用中且 `inode->i_lock` 被持有时调用，并返回 true 如果文件系统希望删除该索引节点。与之前一样，默认情况下仍使用 `generic_drop_inode()` 并已相应更新。`generic_delete_inode()` 仍然存在，其内容仅为返回 1。请注意，实际的驱逐工作在 `->drop_inode()` 返回后由调用者完成。
- 与之前一样，每次调用 `->evict_inode()` 时必须调用一次 `clear_inode()`（就像以前每次调用 `->delete_inode()` 时那样）。不同的是，如果你使用与索引节点关联的元数据缓冲区（即
```markdown
标记 buffer dirty inode()时，你有责任在 clear_inode() 之前调用 invalidate_inode_buffers()。

注意：在 ->write_inode() 开始时检查 i_nlink 并在为零时退出是不够的，并且从来都不够。最终的 unlink() 和 iput() 可能会在 inode 处于 ->write_inode() 的中间阶段时发生；例如，如果你盲目地释放磁盘上的 inode，你可能会在 ->write_inode() 正在写入时进行该操作。

---

**强制性**

.d_delete() 现在仅建议 dcache 是否缓存未引用的 dentry，并且仅在 dentry 引用计数变为 0 时调用。即使在引用计数为 0 的转换期间，它也必须能够容忍被调用 0 次、1 次或多次（例如，恒定的、幂等的）。

---

**强制性**

.d_compare() 调用约定和锁定规则已显著改变。请阅读 Documentation/filesystems/vfs.rst 中更新的文档（并查看其他文件系统的示例）以获取指导。

---

**强制性**

.d_hash() 调用约定和锁定规则已显著改变。请阅读 Documentation/filesystems/vfs.rst 中更新的文档（并查看其他文件系统的示例）以获取指导。

---

**强制性**

dcache_lock 已经消失，取而代之的是细粒度锁。请参阅 fs/dcache.c 了解需要替换 dcache_lock 的锁的详细信息，以便保护特定内容。大多数情况下，文件系统只需要 ->d_lock，这可以保护给定 dentry 的所有 dcache 状态。

---

**推荐**

文件系统必须使用 RCU 释放其 inode，如果它们可以通过 RCU-walk 路径访问（基本上，如果文件可以在 VFS 命名空间中具有路径名称）。尽管 i_dentry 和 i_rcu 在一个 union 中共享存储，我们将在 inode_init_always() 中初始化前者，因此在回调中只需保持不变。以前确实需要在那里清理，但现在不再需要（从 3.2 版本开始）。

---

**强制性**

vfs 现在尝试以“rcu-walk 模式”执行路径遍历，这避免了在 dentry 和 inode 上的原子操作和可扩展性问题（见 Documentation/filesystems/path-lookup.txt）。d_hash 和 d_compare 的更改（如上所述）是支持此模式所需的更改示例。对于更复杂的文件系统回调，vfs 会在 fs 调用之前退出 rcu-walk 模式，因此文件系统不需要任何更改。然而，这是昂贵的并且会失去 rcu-walk 模式的优点。我们将开始添加对 rcu-walk 感知的文件系统回调，如下所示。文件系统应尽可能利用这一点。

---

**强制性**

d_revalidate 是在每个路径元素上调用的回调（如果文件系统提供了它），这要求退出 rcu-walk 模式。现在这个回调可能在 rcu-walk 模式下被调用（nd->flags & LOOKUP_RCU）。如果文件系统无法处理 rcu-walk，则应返回 -ECHILD。详见 Documentation/filesystems/vfs.rst 获取更多详情。
```
---

**权限检查**
权限检查（`permission`）是一个在路径遍历过程中对许多或所有目录节点执行的inode权限检查（用于检查执行权限）。现在，它必须支持rcu-walk（掩码 & `MAY_NOT_BLOCK`）。更多详细信息请参见`Documentation/filesystems/vfs.rst`。

---

**必填**

在`->fallocate()`中，你必须检查传递进来的模式选项。如果你的文件系统不支持打孔（即在文件中间释放空间），当`FALLOC_FL_PUNCH_HOLE`设置在模式中时，你必须返回`-EOPNOTSUPP`。目前，你只能在设置了`FALLOC_FL_KEEP_SIZE`的情况下使用`FALLOC_FL_PUNCH_HOLE`，因此即使在打孔文件末尾时，`i_size`也不应改变。

---

**必填**

`->get_sb()`已被移除。切换到使用`->mount()`。通常，这只需要将调用从`get_sb_`...切换到`mount_`...并更改函数类型。如果是手动操作，则只需从设置`->mnt_root`为某个指针切换到返回该指针。在发生错误时返回`ERR_PTR(...)`。

---

**必填**

`->permission()`和`generic_permission()`已失去`flags`参数；不再传递`IPERM_FLAG_RCU`，而是将`MAY_NOT_BLOCK`添加到掩码中。`generic_permission()`还失去了`check_acl`参数；ACL检查已经被移到VFS，文件系统需要提供非空的`->i_op->get_inode_acl`来从磁盘读取ACL。

---

**必填**

如果你实现了自己的`->llseek()`，则必须处理`SEEK_HOLE`和`SEEK_DATA`。你可以通过返回`-EINVAL`来处理这种情况，但最好以某种方式支持它。通用处理器假设整个文件都是数据，并且文件末尾有一个虚拟的洞。因此，如果提供的偏移量小于`i_size`并且指定了`SEEK_DATA`，则返回相同的偏移量。如果上述情况对于偏移量成立，并且你收到的是`SEEK_HOLE`，则返回文件末尾。如果偏移量等于或大于`i_size`，无论哪种情况都返回`-ENXIO`。

---

**必填**

如果你有自己的`->fsync()`，则必须确保调用`filemap_write_and_wait_range()`，以便正确同步所有脏页。你还需要注意，`->fsync()`不再持有`i_mutex`调用，因此如果你需要锁定`i_mutex`，必须确保自己获取和释放锁。
---

**强制要求**

`d_alloc_root()` 已被移除，随之解决了很多由误用该函数导致的错误。替代方案是 `d_make_root(inode)`。成功时，`d_make_root(inode)` 会分配并返回一个使用传入的inode实例化的新dentry；失败时返回NULL，并且传入的inode会被丢弃，因此无论在任何情况下inode的引用都会被消耗掉，失败处理时无需对inode进行清理。如果 `d_make_root(inode)` 传入的是NULL inode，则返回NULL并且不需要进一步的错误处理。典型用法如下：

```c
inode = foofs_new_inode(...);
s->s_root = d_make_root(inode);
if (!s->s_root)
    /* 不需要对inode进行清理 */
    return -ENOMEM;
...
```

---

**强制要求**

“女巫”已死！好吧，至少三分之二已经没了。`->d_revalidate()` 和 `->lookup()` 不再接收 `struct nameidata` 参数，只接收标志。

---

**强制要求**

`->create()` 不再接收 `struct nameidata *` 参数；与前两个不同的是，它接收一个布尔参数来判断是否为 `O_EXCL` 或等效操作。请注意，本地文件系统可以忽略这个参数——它们被保证对象不存在。只有远程/分布式文件系统可能关心这一点。

---

**强制要求**

`FS_REVAL_DOT` 已经移除；如果你之前使用过它，请在你的dentry操作中添加 `->d_weak_revalidate()`。

---

**强制要求**

`vfs_readdir()` 已经移除；请改为使用 `iterate_dir()`。

---

**强制要求**

`->readdir()` 已经移除；请改为使用 `->iterate_shared()`。

---

**强制要求**

`vfs_follow_link` 已被移除。文件系统必须在 `->follow_link` 中使用 `nd_set_link` 来处理普通符号链接，或使用 `nd_jump_link` 来处理 `/proc/<pid>` 风格的魔法链接。

---

**强制要求**

`iget5_locked()/ilookup5()/ilookup5_nowait()` 的 `test()` 回调之前是在 `->i_lock` 和 `inode_hash_lock` 持有时被调用的；现在前者不再持有，请确保你的回调不依赖于它（内核树中的所有实例都不依赖）。当然，`inode_hash_lock` 仍然持有，所以它们仍然相对于inode哈希表的移除以及 `iget5_locked()` 的 `set()` 回调进行序列化。

---

**强制要求**

`d_materialise_unique()` 已被移除；现在 `d_splice_alias()` 可以满足你所有的需求。记住它们的参数顺序相反。

---

**强制要求**

`f_dentry` 已被移除；请使用 `f_path.dentry`，或者更好的是，看看是否可以完全避免使用它。

---

**强制要求**

不要直接调用 `->read()` 和 `->write()`；应使用 `__vfs_{read,write}` 或者包装函数；而不是检查 `->write` 或 `->read` 是否为 NULL，应该查看 `file->f_mode` 中是否有 `FMODE_CAN_{WRITE,READ}` 标志。

---

**强制要求**

不要使用 `new_sync_{read,write}` 来处理 `->read` 和 `->write`；将其保持为 NULL 即可。
---

**必须**

->aio_read/->aio_write 已经被移除。请使用 ->read_iter/->write_iter。

---

**推荐**

对于嵌入式（"快速"）符号链接，只需将 inode->i_link 设置为符号链接体所在的位置，并在 ->follow_link() 中使用 simple_follow_link()。

---

**必须**

->follow_link() 的调用约定已更改。现在不再返回 cookie 并使用 nd_set_link() 来存储要遍历的链接体，而是返回要遍历的链接体并使用显式的 void ** 参数来存储 cookie。nameidata 不再传递 —— nd_jump_link() 不需要它，而 nd_[gs]et_link() 已经被移除。

---

**必须**

->put_link() 的调用约定已更改。它接收 inode 而不是 dentry，不接收 nameidata，并且仅在 cookie 非空时被调用。请注意，链接体不再可用，因此如果需要，应将其作为 cookie 存储。

---

**必须**

任何可能使用 page_follow_link_light/page_put_link() 的符号链接都必须在其页缓存开始操作之前调用 inode_nohighmem(inode)。这样的符号链接不应包含高内存页。这包括在创建符号链接期间可能执行的任何预填充。page_symlink() 将遵循映射的 gfp 标志，所以在调用 inode_nohighmem() 后可以安全使用，但如果手动分配和插入页面，请确保使用正确的 gfp 标志。

---

**必须**

->follow_link() 被 ->get_link() 替代；相同的 API，除了：

* ->get_link() 接收 inode 作为单独的参数
* ->get_link() 可能在 RCU 模式下调用——在这种情况下，会传入 NULL dentry

---

**必须**

->get_link() 现在接收 struct delayed_call *done，并应在原本设置 *cookie 的地方调用 set_delayed_call()。->put_link() 已经被移除——只需在 ->get_link() 中将析构函数传递给 set_delayed_call()。

---

**必须**

->getxattr() 和 xattr_handler.get() 分别接收 dentry 和 inode。dentry 可能尚未附加到 inode，因此在这些实例中不要使用其 ->d_inode。理由：!@#!@# security_d_instantiate() 需要在我们将 dentry 附加到 inode 之前被调用。
---

**强制要求**

符号链接不再是唯一一类在inode被驱逐时未将i_bdev/i_cdev/i_pipe/i_link联合体清零的inode。因此，你不能假设在`->destroy_inode()`时`->i_nlink`中的非空值意味着这是一个符号链接。现在确实需要检查`->i_mode`。在内核树中，我们不得不修复shmem_destroy_callback()函数，该函数以前使用了这种捷径；请注意，这种捷径已不再有效。

---

**强制要求**

`->i_mutex`已被替换为`->i_rwsem`。`inode_lock()`等函数仍然像以前一样工作——它们只是获取独占锁。然而，`->lookup()`可以在父目录锁定共享的情况下被调用。其实例必须不：

* 单独使用`d_instantiate`和`d_rehash()`——应改用`d_add()`或`d_splice_alias()`。
* 单独使用`d_rehash()`——改用`d_add(new_dentry, NULL)`。
* 在极不可能的情况下，如果由于某种原因需要对文件系统数据结构进行（只读）访问排除，请自行安排。内核树中的任何文件系统都不需要这样做。
* 依赖于在dentry传递给`d_add()`或`d_splice_alias()`之后`->d_parent`和`->d_name`不会改变。同样，内核树中的任何实例都没有依赖这一点。

可以保证在同一目录中查找相同名称的操作不会并行发生（“相同”是指根据你的`->d_compare()`）。在同一目录中查找不同名称的操作现在可以并且会并行发生。

---

**强制要求**

添加了`->iterate_shared()`。
在struct file级别的互斥（以及它与同一struct file上的lseek之间的互斥）仍然提供，但如果你的目录被打开多次，则这些函数可能会并行调用。
当然，该方法与所有修改目录的方法之间的互斥仍然提供。
---

**如果在内核中有任何由`->iterate_shared()`修改的每inode或每dentry的数据结构，你可能需要某种机制来序列化对它们的访问。如果你进行了dcache预填充，你需要切换到`d_alloc_parallel()`；可以查找树内的示例。**

**强制性要求**

`->atomic_open()`调用可能在没有O_CREAT标志的情况下并行发生。

**强制性要求**

`->setxattr()`和`xattr_handler.set()`现在分别接收dentry和inode。`xattr_handler.set()`传递了inode所见挂载点的用户命名空间，以便文件系统可以根据此命名空间映射`i_uid`和`i_gid`。dentry可能尚未附加到inode上，因此请勿使用其`->d_inode`。原因：`security_d_instantiate()`需要在将dentry附加到inode之前被调用，并且`smack ->d_instantiate()`不仅使用`->getxattr()`还使用`->setxattr()`。

**强制性要求**

`->d_compare()`不再接收单独的父节点参数。如果你之前使用它来找到涉及的`struct super_block`，则可以使用`dentry->d_sb`；如果是更复杂的情况，请使用`dentry->d_parent`。请注意不要假设多次获取该值会得到相同的结果——在RCU模式下，它可能会在你获取时发生变化。

**强制性要求**

`->rename()`增加了一个标志参数。任何未被文件系统处理的标志都应该导致返回EINVAL。

---

**推荐做法**

对于符号链接，`->readlink`是可选的。除非文件系统需要为`readlink(2)`伪造某些内容，否则无需设置。

**强制性要求**

`->getattr()`现在接收一个`struct path`而不是单独的vfsmount和dentry，并且现在增加了`request_mask`和`query_flags`参数来指定statx请求的字段和同步类型。不支持任何statx特定功能的文件系统可以忽略这些新参数。
---

**强制要求**

- `atomic_open()` 的调用约定已更改。`int *opened` 已经被移除，同时 FILE_OPENED/FILE_CREATED 也不再使用。取而代之的是 FMODE_OPENED/FMODE_CREATED，设置在 file->f_mode 中。此外，在“调用 finish_no_open()，自己打开文件”的情况下，返回值已从 1 变为 0。由于 finish_no_open() 现在返回 0，因此 ->atomic_open() 的实例不需要对此部分进行任何更改。

---

**强制要求**

- `alloc_file()` 现在已成为静态函数；应使用两个包装函数代替：
  - `alloc_file_pseudo(inode, vfsmount, name, flags, ops)` 用于需要创建 dentry 的情况；这是大多数旧版 `alloc_file()` 用户的情况。调用约定：成功时返回新 struct file 的引用，并且调用者的 inode 引用被该引用取代。失败时返回 ERR_PTR() 并且不影响调用者的引用，因此调用者需要释放其持有的 inode 引用。
  - `alloc_file_clone(file, flags, ops)` 不影响任何调用者的引用。成功时，您将获得一个新的 struct file，与原始文件共享相同的 mount/dentry；失败时返回 ERR_PTR()。

---

**强制要求**

- `clone_file_range()` 和 `dedupe_file_range` 已被 `remap_file_range()` 替换。更多信息请参阅 Documentation/filesystems/vfs.rst。

---

**推荐**

- 对于执行类似以下操作的 `->lookup()` 实例：

  ```c
  if (IS_ERR(inode))
    return ERR_CAST(inode);
  return d_splice_alias(inode, dentry);
  ```

  不需要进行检查 —— `d_splice_alias()` 在给定 ERR_PTR(...) 作为 inode 时会执行正确的行为。更重要的是，传递 NULL inode 给 `d_splice_alias()` 也会执行正确的操作（等同于 `d_add(dentry, NULL); return NULL;`），因此这种特殊情况也不需要单独处理。

---

**强烈推荐**

- 将 `->destroy_inode()` 中的 RCU 延迟部分提取到一个新方法 `->free_inode()` 中。如果 `->destroy_inode()` 变为空，则最好将其删除。同步工作（例如不能在 RCU 回调中完成的工作或任何需要堆栈跟踪的 WARN_ON()）可以移到 `->evict_inode()` 中；然而，这仅适用于不需要平衡 `->alloc_inode()` 所做工作的内容。换句话说，如果它是在清理内核 inode 生命周期中可能积累的内容，`->evict_inode()` 可能是一个合适的选择。

- inode 销毁规则如下：
  - 如果 `->destroy_inode()` 非 NULL，则调用它。
  - 如果 `->free_inode()` 非 NULL，则通过 call_rcu() 调度它。
  - `->destroy_inode` 和 `->free_inode` 同时为 NULL 的组合被视为 NULL/free_inode_nonrcu，以保持兼容性。

- 注意，回调（无论是通过 `->free_inode()` 还是 `->destroy_inode()` 中显式的 call_rcu()）与超级块销毁无关；实际上，超级块及其所有相关结构可能已经不存在了。文件系统驱动程序保证仍然存在，但仅此而已。在回调中释放内存是可以的；做更多的事情也是可能的，但这需要非常小心，最好避免。
---

**强制要求**

DCACHE_RCUACCESS 已经移除；在 dentry 释放时有 RCU 延迟是默认行为。DCACHE_NORCU 选择退出，默认只有 d_alloc_pseudo() 可以这样做。

---

**强制要求**

d_alloc_pseudo() 是内部使用的；在 alloc_file_pseudo() 之外的使用非常可疑（并且在模块中无法工作）。这样的使用很可能被误写为 d_alloc_anon()。

---

**强制要求**

[本应在 2016 年添加] 尽管 finish_open() 中存在过时的注释，但在 ->atomic_open() 实例中的失败退出不应调用 fput() 文件，无论什么情况都由调用者处理一切。

---

**强制要求**

clone_private_mount() 现在返回一个长期挂载，因此其结果的正确析构函数应为 kern_unmount() 或 kern_unmount_array()。

---

**强制要求**

禁止零长度的 bvec 段，必须在传递给迭代器之前将其过滤掉。

---

**强制要求**

对于基于 bvec 的迭代器，bio_iov_iter_get_pages() 现在不再复制 bvec 而是使用提供的 bvec。任何发出 kiocb-I/O 的操作应确保 bvec 和页面引用一直保持到 I/O 完成，即直到调用或返回非-EIOCBQUEUED 代码的 ->ki_complete()。

---

**强制要求**

mnt_want_write_file() 现在只能与 mnt_drop_write_file() 配对使用，而之前它可以与 mnt_drop_write() 配对使用。

---

**强制要求**

iov_iter_copy_from_user_atomic() 已经移除；使用 copy_page_from_iter_atomic()。区别在于 copy_page_from_iter_atomic() 会推进迭代器，之后不需要再调用 iov_iter_advance()。但是，如果你决定只使用部分获取的数据，你应该调用 iov_iter_revert()。

---

**强制要求**

file_open_root() 的调用约定已更改；现在它接受 struct path * 而不是分别传递 mount 和 dentry。对于以前传递 <mnt, mnt->mnt_root> 对（即给定挂载的根）的调用者，提供了一个新的辅助函数 file_open_root_mnt()。树内用户已进行调整。
---

**强制要求**

`no_llseek` 已经移除；不要将 `.llseek` 设置为 `no_llseek` —— 直接将其设置为 `NULL` 即可。
检查文件是否支持 `llseek(2)` 或者是否应该返回 `ESPIPE` 错误，应通过查看 `file->f_mode` 中的 `FMODE_LSEEK` 来实现。

---

*强制要求*

`filldir_t`（`readdir` 回调）的调用约定已经改变。现在它返回一个布尔值，而不是之前的 0 或 -E...。`false` 表示“没有更多”（与之前的 -E... 相同），`true` 表示“继续”（与旧的调用约定中的 0 相同）。理由：调用者从来不会查看具体的 -E... 值。所有 `iterate_shared()` 实例不需要任何更改，树中所有 `filldir_t` 的实例已转换完毕。

---

**强制要求**

`->tmpfile()` 的调用约定已经改变。现在它接受一个 `struct file` 指针而不是 `struct dentry` 指针。`d_tmpfile()` 也相应地进行了更改以简化调用者。传入的文件处于未打开状态，并且在成功时必须在返回之前打开（例如通过调用 `finish_open_simple()`）。

---

**强制要求**

`->huge_fault` 的调用约定已经改变。现在它接受一个页面大小顺序而不是 `enum page_entry_size`，并且可以在不持有 `mmap_lock` 的情况下被调用。所有树内的用户已经审计过，似乎都不依赖于持有 `mmap_lock`，但树外的用户需要自行验证。如果他们确实需要持有 `mmap_lock`，可以返回 `VM_FAULT_RETRY` 以便在持有 `mmap_lock` 的情况下再次调用。

---

**强制要求**

打开块设备和匹配或创建超级块的顺序已经改变。
旧逻辑先打开块设备，然后尝试根据块设备指针找到合适的超级块重用。
新逻辑首先根据设备编号尝试找到合适的超级块，然后再打开块设备。
由于打开块设备不能在 `s_umount` 下进行（因为锁顺序要求），现在在打开块设备时会释放 `s_umount`，并在调用 `fill_super()` 之前重新获取。
在旧逻辑中，并发挂载者会在文件系统的超级块列表上找到超级块。由于第一个打开块设备的人会持有 `s_umount`，他们会等待直到超级块诞生或者由于初始化失败而被丢弃。
自新的逻辑移除了`s_umount`后，并发挂载器可能会获取`s_umount`并陷入自旋。现在它们通过显式的等待-唤醒机制来等待，而无需持有`s_umount`。

---

**强制性**

块设备的持有者现在是超级块（superblock）
块设备的持有者过去是文件系统类型（`file_system_type`），这并不是特别有用。无法通过块设备直接找到拥有它的超级块，除非匹配超级块中存储的设备指针。这种机制只适用于单个设备，因此块层无法找到任何额外设备的拥有超级块。
在旧的机制中，为竞争挂载（`mount(2)`）和卸载（`umount(2)`）重用或创建超级块依赖于文件系统类型作为持有者。然而，这一点严重缺乏文档说明：

1. 任何成功获取现有超级块活动引用的并发挂载器会被要求等待，直到超级块准备好或从文件系统类型的超级块列表中移除。如果超级块已准备好，调用者会简单地重用它。
2. 如果挂载器在`deactivate_locked_super()`之后但超级块还未从文件系统类型的超级块列表中移除之前到来，则挂载器会等待超级块关闭，重用块设备并分配一个新的超级块。
3. 如果挂载器在`deactivate_locked_super()`之后且超级块已从文件系统类型的超级块列表中移除之后到来，则挂载器会重用块设备并分配一个新的超级块（`bd_holder`可能仍设置为文件系统类型）。
由于块设备的持有者是文件系统类型，任何并发挂载器都可以打开同一文件系统类型的任何超级块的块设备，而不会因为块设备仍被其他超级块使用而看到`EBUSY`错误。
将超级块作为块设备的所有者改变了这一点，因为现在的持有者是一个唯一的超级块，因此与之关联的块设备不能被并发挂载器重用。因此，在情况（2）中，并发挂载器在尝试打开持有者为不同超级块的块设备时，可能会突然看到`EBUSY`错误。
因此，新逻辑在`->kill_sb()`中等待超级块及其设备关闭。从文件系统类型的超级块列表中移除超级块现在移到设备关闭后的更晚时间点进行：

1. 任何成功获取现有超级块活动引用的并发挂载器会被要求等待，直到超级块准备好或超级块及其所有设备在`->kill_sb()`中关闭。如果超级块已准备好，调用者会简单地重用它。
(2) 如果在 `deactivate_locked_super()` 之后但超级块尚未从文件系统类型的超级块列表中移除时挂载者尝试挂载，则挂载者将被要求等待，直到在 `->kill_sb()` 中关闭超级块和设备，并且超级块从该文件系统类型的超级块列表中移除。然后挂载者将分配一个新的超级块并获取块设备的所有权（块设备的 `bd_holder` 指针将设置为新分配的超级块）。

(3) 现在这个情况已经合并到 (2) 中，因为超级块会一直保留在文件系统类型的超级块列表中，直到所有设备在 `->kill_sb()` 中关闭。换句话说，如果超级块不再存在于文件系统类型的超级块列表中，那么它已经放弃了所有相关块设备的所有权（`bd_holder` 指针为 NULL）。

由于这是 VFS 层级的更改，对于文件系统来说除了必须使用提供的 `kill_litter_super()`、`kill_anon_super()` 或 `kill_block_super()` 帮助函数之外没有实际影响。

---

**强制性**

锁的顺序已更改，使 `s_umount` 的优先级再次高于 `open_mutex`。
所有在 `open_mutex` 下获取 `s_umount` 的地方都已修复。

---

**强制性**

`export_operations ->encode_fh()` 不再有默认实现来编码 `FILEID_INO32_GEN*` 文件句柄。
使用默认实现的文件系统可以显式地使用通用帮助函数 `generic_encode_ino32_fh()`。

---

**强制性**

如果 `->rename()` 在跨目录移动时需要更新 `..` 并排除目录修改，请不要在您的 `->rename()` 中锁定相应的子目录——现在这是由调用者完成的[该项目应在 28eceeda130f "fs: Lock moved directories" 中添加]。

---

**强制性**

在同一目录下的 `->rename()` 中，对 `..` 的（同义反复的）更新不受任何锁的保护；如果旧父目录与新父目录相同，则不要进行该更新。
我们真的不能在同一目录重命名时锁定两个子目录——否则会导致死锁。
---

**强制要求**

`lock_rename()` 和 `lock_rename_child()` 在跨目录的情况下可能会失败，如果它们的参数没有共同的祖先。在这种情况下会返回 `ERR_PTR(-EXDEV)`，并且不会获取任何锁。树内用户已更新；树外用户需要进行更新。

---

**强制要求**

锚定在父目录项中的子项列表现在被转换为哈希表（hlist）。字段名称也进行了更改（`->d_children` / `->d_sib` 替代了 `->d_subdirs` / `->d_child`），因此任何受影响的地方将立即被编译器捕获。

---

**强制要求**

现在调用 `->d_delete()` 实例时，必须持有 `->d_lock` 并且引用计数等于 0。不允许在此过程中释放或重新获取 `->d_lock`。树内的实例都没有这样做。请确保您的实例也不会这样做。

---

**强制要求**

现在调用 `->d_prune()` 实例时，不持有父目录项上的 `->d_lock`。目录项本身的 `->d_lock` 仍然被持有；如果您需要针对父目录的排他性（树内实例没有这样做），请使用您自己的自旋锁。`->d_iput()` 和 `->d_release()` 被调用时，受害者目录项仍在父目录的子项列表中。它仍然是未散列的、标记为已删除等状态，只是还没有从父目录的 `->d_children` 中移除。遍历子项列表的任何人需要注意可能看到的半删除目录项；持有这些目录项的 `->d_lock` 将会看到它们是负引用计数、未散列的状态，这意味着大多数内核用户在没有任何调整的情况下已经做了正确的事情。

---

**推荐**

块设备的冻结和解冻操作已被移到持有者操作中。
在这次更改之前，`get_active_super()` 只能找到主块设备的超级块，即存储在 `sb->s_bdev` 中的那个。现在，块设备冻结功能适用于由给定超级块拥有的任何块设备，而不仅仅是主块设备。`get_active_super()` 辅助函数和 `bd_fsfreeze_sb` 指针已经被移除。

---

**必须**

`set_blocksize()` 现在接受已经打开的文件结构（`struct file`）而不是 `struct block_device`，并且该文件必须是独占打开的。
