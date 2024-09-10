SPDX许可证标识符: GPL-2.0

=========================================
Linux虚拟文件系统概述
=========================================

原始作者: Richard Gooch <rgooch@atnf.csiro.au>

- 版权所有 (C) 1999 Richard Gooch
- 版权所有 (C) 2005 Pekka Enberg

简介
============

虚拟文件系统（也称为虚拟文件系统开关）是内核中的软件层，为用户空间程序提供文件系统接口。它还提供了内核中的抽象机制，使不同的文件系统实现能够共存。VFS 系统调用如 open(2)，stat(2)，read(2)，write(2)，chmod(2) 等从进程上下文调用。文件系统的锁定在文档 Documentation/filesystems/locking.rst 中描述。

目录条目缓存（dcache）
------------------------------

VFS 实现了 open(2)，stat(2)，chmod(2) 和类似的系统调用。传递给这些函数的路径名参数被 VFS 用来搜索目录条目缓存（也称为 dentry 缓存或 dcache）。这提供了一种非常快速的查找机制，将路径名（文件名）转换为特定的 dentry。Dentries 存储在 RAM 中，永远不会保存到磁盘：它们仅为了性能而存在。
Dentry 缓存旨在成为您整个文件系统的视图。由于大多数计算机无法同时将所有 dentries 放入 RAM 中，因此缓存中的一些部分会缺失。为了将您的路径名解析为一个 dentry，VFS 可能需要创建沿途的 dentries，然后加载 inode。这是通过查找 inode 来完成的。

inode 对象
-----------------

一个单独的 dentry 通常有一个指向 inode 的指针。Inodes 是文件系统对象，例如普通文件、目录、FIFO 以及其他对象。它们要么存在于磁盘上（对于块设备文件系统），要么存在于内存中（对于伪文件系统）。位于磁盘上的 inode 在需要时会被复制到内存中，并且对 inode 的更改会被写回到磁盘。一个单独的 inode 可以被多个 dentries 指向（例如，硬链接就是这样做的）。
要查找一个 inode，VFS 需要调用父目录 inode 的 lookup() 方法。这个方法由 inode 所在的具体文件系统实现安装。一旦 VFS 获取所需的 dentry（从而获取 inode），我们就可以执行诸如打开文件（open(2)）或查看 inode 数据（stat(2)）等操作。stat(2) 操作相对简单：一旦 VFS 获取了 dentry，它就会查看 inode 数据并将其中的一部分返回给用户空间。

文件对象
---------------

打开一个文件需要另一个操作：分配一个文件结构（这是文件描述符的内核侧实现）。新分配的文件结构初始化为指向 dentry 和一组文件操作成员函数。这些是从 inode 数据中获取的。然后调用 open() 文件方法，以便具体的文件系统实现可以执行其工作。可以看出，这是 VFS 执行的另一个切换。文件结构被放置在进程的文件描述符表中。
读取、写入和关闭文件（以及其他各种 VFS 操作）是通过使用用户空间文件描述符来获取适当的文件结构，然后调用所需的文件结构方法来完成所需的操作。只要文件保持打开状态，它就会使 dentry 处于使用状态，这意味着 VFS inode 仍然处于使用状态。

注册和挂载文件系统
=====================================

要注册和注销文件系统，请使用以下 API 函数：

```c
#include <linux/fs.h>

extern int register_filesystem(struct file_system_type *);
extern int unregister_filesystem(struct file_system_type *);
```

传递的 struct file_system_type 描述了您的文件系统。当请求将文件系统挂载到您的命名空间中的目录时，VFS 将调用该具体文件系统的适当 mount() 方法。新的 vfsmount 引用由 ->mount() 返回的树，并将其附加到挂载点，这样当路径名解析到达挂载点时，它将跳转到该 vfsmount 的根目录。
你可以通过查看 `/proc/filesystems` 文件来获取所有注册到内核的文件系统的列表。
```c
struct file_system_type
-----------------------
```
这个结构体描述了一个文件系统。定义了以下成员：

```c
struct file_system_type {
    const char *name;
    int fs_flags;
    int (*init_fs_context)(struct fs_context *);
    const struct fs_parameter_spec *parameters;
    struct dentry *(*mount)(struct file_system_type *, int, const char *, void *);
    void (*kill_sb)(struct super_block *);
    struct module *owner;
    struct file_system_type *next;
    struct hlist_head fs_supers;

    struct lock_class_key s_lock_key;
    struct lock_class_key s_umount_key;
    struct lock_class_key s_vfs_rename_key;
    struct lock_class_key s_writers_key[SB_FREEZE_LEVELS];

    struct lock_class_key i_lock_key;
    struct lock_class_key i_mutex_key;
    struct lock_class_key invalidate_lock_key;
    struct lock_class_key i_mutex_dir_key;
};
```

- `name`：文件系统类型的名称，例如 "ext2"、"iso9660"、"msdos" 等。
- `fs_flags`：各种标志（例如 FS_REQUIRES_DEV、FS_NO_DCACHE 等）。
- `init_fs_context`：初始化 `struct fs_context` 的 `->ops` 和 `->fs_private` 字段，填充文件系统特定的数据。
- `parameters`：指向文件系统参数描述符数组 `struct fs_parameter_spec` 的指针。更多信息请参见 `Documentation/filesystems/mount_api.rst`。
- `mount`：当需要挂载一个新的文件系统实例时调用的方法。
- `kill_sb`：当需要关闭一个文件系统实例时调用的方法。
- `owner`：供内部 VFS 使用：通常应将其初始化为 `THIS_MODULE`。
- `next`：供内部 VFS 使用：通常应将其初始化为 `NULL`。
- `fs_supers`：供内部 VFS 使用：文件系统实例（超级块）的哈希链表。

`s_lock_key`、`s_umount_key`、`s_vfs_rename_key`、`s_writers_key`、`i_lock_key`、`i_mutex_key`、`invalidate_lock_key`、`i_mutex_dir_key`：这些是针对锁依赖（lockdep）的特定字段。

`mount()` 方法具有以下参数：

- `struct file_system_type *fs_type`：描述文件系统，部分由特定文件系统代码初始化。
- `int flags`：挂载标志。
- `const char *dev_name`：要挂载的设备名称。
- `void *data`：任意挂载选项，通常是一个 ASCII 字符串（详见“挂载选项”部分）。

`mount()` 方法必须返回请求者所需的根目录项。必须获取其超级块的活动引用，并锁定该超级块。如果失败，则应返回 `ERR_PTR(error)`。参数与 `mount(2)` 相匹配，具体解释取决于文件系统类型。例如，对于块文件系统，`dev_name` 被解释为块设备名称，打开该设备并检查是否包含合适的文件系统映像，然后创建并初始化 `struct super_block`，最后将根目录项返回给调用者。

`mount()` 可以选择返回现有文件系统的一个子树，而不一定要创建一个新的。从调用者的角度来看，主要结果是获取到子树根目录项的引用；创建新的超级块通常是附带的效果。

超级块结构中 `mount()` 方法填充的最有趣的成员是 `s_op` 字段。这是一个指向 `struct super_operations` 的指针，描述了文件系统实现的下一个层次。
通常情况下，文件系统会使用通用的 `mount()` 实现之一，并提供一个 `fill_super()` 回调函数。通用变体如下：

``mount_bdev``
    挂载位于块设备上的文件系统

``mount_nodev``
    挂载不依赖于任何设备的文件系统

``mount_single``
    挂载一个在所有挂载点之间共享实例的文件系统

`fill_super()` 回调函数实现的参数如下：

``struct super_block *sb``
    超级块结构。回调函数必须正确初始化它。
``void *data``
    任意的挂载选项，通常以ASCII字符串形式传递（参见“挂载选项”部分）。
``int silent``
    是否在出错时不显示错误信息。

超级块对象
==========

超级块对象表示一个已挂载的文件系统。

`struct super_operations`
------------------------

这描述了VFS如何操作你的文件系统的超级块。以下成员被定义为：

```c
struct super_operations {
    struct inode *(*alloc_inode)(struct super_block *sb);
    void (*destroy_inode)(struct inode *);
    void (*free_inode)(struct inode *);

    void (*dirty_inode) (struct inode *, int flags);
    int (*write_inode) (struct inode *, struct writeback_control *wbc);
    int (*drop_inode) (struct inode *);
    void (*evict_inode) (struct inode *);
    void (*put_super) (struct super_block *);
    int (*sync_fs)(struct super_block *sb, int wait);
    int (*freeze_super) (struct super_block *sb, enum freeze_holder who);
    int (*freeze_fs) (struct super_block *);
    int (*thaw_super) (struct super_block *sb, enum freeze_holder who);
    int (*unfreeze_fs) (struct super_block *);
    int (*statfs) (struct dentry *, struct kstatfs *);
    int (*remount_fs) (struct super_block *, int *, char *);
    void (*umount_begin) (struct super_block *);

    int (*show_options)(struct seq_file *, struct dentry *);
    int (*show_devname)(struct seq_file *, struct dentry *);
    int (*show_path)(struct seq_file *, struct dentry *);
    int (*show_stats)(struct seq_file *, struct dentry *);

    ssize_t (*quota_read)(struct super_block *, int, char *, size_t, loff_t);
    ssize_t (*quota_write)(struct super_block *, int, const char *, size_t, loff_t);
    struct dquot **(*get_dquots)(struct inode *);

    long (*nr_cached_objects)(struct super_block *, struct shrink_control *);
    long (*free_cached_objects)(struct super_block *, struct shrink_control *);
};
```

除非另有说明，所有方法在没有任何锁的情况下被调用。这意味着大多数方法可以安全地阻塞。所有方法仅从进程上下文被调用（即不是从中断处理程序或下半部调用）。

``alloc_inode``
    此方法由 `alloc_inode()` 调用来分配 `struct inode` 的内存并初始化它。如果此函数未定义，则分配一个简单的 `struct inode`。通常 `alloc_inode` 用于分配一个较大的结构，其中包含嵌入的 `struct inode`。
``destroy_inode``
    此方法由 `destroy_inode()` 调用来释放为 `struct inode` 分配的资源。只有当定义了 `->alloc_inode` 时才需要此方法，它只需撤销 `->alloc_inode` 所做的任何事情。
``free_inode``
    此方法从RCU回调中调用。如果你在 `->destroy_inode` 中使用 `call_rcu()` 来释放 `struct inode` 的内存，那么最好在此方法中释放内存。
``dirty_inode``
    当一个inode被标记为脏时，此方法由VFS调用。这是特别针对inode本身被标记为脏的情况，而不是它的数据。如果更新需要通过 `fdatasync()` 持久化，则会在 `flags` 参数中设置 `I_DIRTY_DATASYNC` 标志。如果启用了懒惰时间戳并且自上次 `->dirty_inode` 调用以来inode的时间戳已更新，则 `flags` 中会设置 `I_DIRTY_TIME` 标志。
``write_inode``
    当VFS需要将inode写入磁盘时调用此方法。第二个参数指示写入是否应同步进行，但并非所有文件系统都会检查这个标志。
``drop_inode``
当最后一个对inode的访问被释放时调用，此时会持有inode->i_lock自旋锁。
此方法应为NULL（普通UNIX文件系统语义）或“generic_delete_inode”（对于不希望缓存inode的文件系统——这会导致“delete_inode”无论i_nlink值如何总是被调用）。

“generic_delete_inode()”的行为等同于在put_inode()情况下使用“force_delete”的旧做法，但没有“force_delete()”方法中存在的竞态条件问题。

``evict_inode``
当VFS希望驱逐一个inode时调用。调用者不会驱逐页缓存或与inode相关的元数据缓冲；该方法必须使用truncate_inode_pages_final()来清除这些内容。调用者确保在调用->evict_inode()期间（或之后）异步写回不会运行。可选。

``put_super``
当VFS希望释放超级块（即卸载）时调用。这是在持有超级块锁的情况下调用的。

``sync_fs``
当VFS正在写入与超级块关联的所有脏数据时调用。第二个参数指示该方法是否应该等待直到写入完成。可选。

``freeze_super``
如果提供了此回调，则代替->freeze_fs回调调用。
主要区别在于->freeze_super是在不获取down_write(&sb->s_umount)的情况下调用的。如果文件系统实现了它并且希望->freeze_fs也被调用，则需要在此回调中显式调用->freeze_fs。可选。

``freeze_fs``
当VFS锁定一个文件系统并强制其进入一致状态时调用。此方法目前由逻辑卷管理器（LVM）和ioctl(FIFREEZE)使用。可选。

``thaw_super``
当VFS解锁一个文件系统并在->freeze_super后使其再次可写时调用。可选。

``unfreeze_fs``
当VFS解锁一个文件系统并在->freeze_fs后使其再次可写时调用。可选。

``statfs``
当VFS需要获取文件系统统计信息时调用。
``remount_fs``
在文件系统重新挂载时调用。此函数在持有内核锁的情况下被调用。

``umount_begin``
在VFS卸载文件系统时调用。

``show_options``
由VFS调用，用于显示`/proc/<pid>/mounts`和`/proc/<pid>/mountinfo`中的挂载选项（参见“挂载选项”部分）。

``show_devname``
可选。由VFS调用，用于显示`/proc/<pid>/{mounts,mountinfo,mountstats}`中的设备名称。如果没有提供，则使用`(struct mount).mnt_devname`。

``show_path``
可选。由VFS（对于`/proc/<pid>/mountinfo`）调用，用于显示相对于文件系统根目录的挂载根目录项路径。

``show_stats``
可选。由VFS（对于`/proc/<pid>/mountstats`）调用，用于显示特定于文件系统的挂载统计信息。

``quota_read``
由VFS调用，用于从文件系统的配额文件中读取数据。

``quota_write``
由VFS调用，用于向文件系统的配额文件写入数据。

``get_dquots``
由配额系统调用，用于获取特定inode的`struct dquot`数组。
（可选）

``nr_cached_objects``
由文件系统的sb缓存缩减函数调用，返回其包含的可释放缓存对象数量。
可选的 ``free_cache_objects``

由文件系统的 sb 缓存缩减函数调用，用于扫描指定数量的对象并尝试释放它们。

此方法是可选的，但任何实现该方法的文件系统还需要实现 `->nr_cached_objects` 才能正确调用。

对于文件系统可能遇到的任何错误，我们无法处理，因此返回类型为 void。如果虚拟内存（VM）试图在 GFP_NOFS 条件下回收资源，则永远不会调用此方法，因此该方法本身不需要处理这种情况。

实现中必须在任何扫描循环内包含条件重新调度调用。这允许 VFS 确定适当的扫描批量大小，而不必担心实现是否会导致由于大扫描批量导致的问题。

设置 inode 的人负责填充 “i_op” 字段。这是一个指向 “struct inode_operations” 的指针，描述了可以对单个 inode 执行的方法。

```struct xattr_handler```
---------------------

在支持扩展属性（xattrs）的文件系统上，s_xattr 超级块字段指向一个以 NULL 结尾的 xattr 处理程序数组。扩展属性是名称:值对。

``name``
表示处理程序匹配具有指定名称的属性（例如 "system.posix_acl_access"），前缀字段必须为 NULL。

``prefix``
表示处理程序匹配具有指定名称前缀的所有属性（例如 "user."），名称字段必须为 NULL。
``list``
	确定是否应为特定目录项列出与此扩展属性（xattr）处理器匹配的属性。由某些`listxattr`实现（如generic_listxattr）使用。

``get``
	由VFS调用以获取特定扩展属性的值。此方法由`getxattr(2)`系统调用调用。

``set``
	由VFS调用以设置特定扩展属性的值。当新值为NULL时，调用此方法以删除特定扩展属性。此方法由`setxattr(2)`和`removexattr(2)`系统调用调用。

当文件系统的任何扩展属性处理器不匹配指定的属性名称或文件系统不支持扩展属性时，各种`*xattr(2)`系统调用返回-EOPNOTSUPP。
Inode对象
================

Inode对象表示文件系统中的一个对象。
struct inode_operations
-----------------------

此结构描述了VFS如何在您的文件系统中操作一个inode。截至内核2.6.22版本，定义了以下成员：

.. code-block:: c

    struct inode_operations {
        int (*create) (struct mnt_idmap *, struct inode *, struct dentry *, umode_t, bool);
        struct dentry * (*lookup) (struct inode *, struct dentry *, unsigned int);
        int (*link) (struct dentry *, struct inode *, struct dentry *);
        int (*unlink) (struct inode *, struct dentry *);
        int (*symlink) (struct mnt_idmap *, struct inode *, struct dentry *, const char *);
        int (*mkdir) (struct mnt_idmap *, struct inode *, struct dentry *, umode_t);
        int (*rmdir) (struct inode *, struct dentry *);
        int (*mknod) (struct mnt_idmap *, struct inode *, struct dentry *, umode_t, dev_t);
        int (*rename) (struct mnt_idmap *, struct inode *, struct dentry *,
                       struct inode *, struct dentry *, unsigned int);
        int (*readlink) (struct dentry *, char __user *, int);
        const char *(*get_link) (struct dentry *, struct inode *, struct delayed_call *);
        int (*permission) (struct mnt_idmap *, struct inode *, int);
        struct posix_acl * (*get_inode_acl)(struct inode *, int, bool);
        int (*setattr) (struct mnt_idmap *, struct dentry *, struct iattr *);
        int (*getattr) (struct mnt_idmap *, const struct path *, struct kstat *, u32, unsigned int);
        ssize_t (*listxattr) (struct dentry *, char *, size_t);
        void (*update_time)(struct inode *, struct timespec *, int);
        int (*atomic_open)(struct inode *, struct dentry *, struct file *,
                           unsigned open_flag, umode_t create_mode);
        int (*tmpfile) (struct mnt_idmap *, struct inode *, struct file *, umode_t);
        struct posix_acl * (*get_acl)(struct mnt_idmap *, struct dentry *, int);
        int (*set_acl)(struct mnt_idmap *, struct dentry *, struct posix_acl *, int);
        int (*fileattr_set)(struct mnt_idmap *idmap,
                            struct dentry *dentry, struct fileattr *fa);
        int (*fileattr_get)(struct dentry *dentry, struct fileattr *fa);
        struct offset_ctx *(*get_offset_ctx)(struct inode *inode);
    };

再次提醒，除非另有说明，所有方法都是在没有任何锁的情况下被调用的。

``create``
	由`open(2)`和`creat(2)`系统调用调用。如果您希望支持普通文件，则需要实现此方法。您得到的dentry不应该有inode（即应该是一个负dentry）。您可能需要使用该dentry和新创建的inode调用`d_instantiate()`。

``lookup``
	当VFS需要在父目录中查找一个inode时调用。要查找的名字位于dentry中。此方法必须调用`d_add()`将找到的inode插入到dentry中。inode结构中的“i_count”字段应递增。如果命名的inode不存在，则应将一个NULL inode插入到dentry中（这称为负dentry）。只有在真正错误的情况下才能从此例程返回错误码，否则使用诸如`create(2)`、`mknod(2)`、`mkdir(2)`等系统调用来创建inode将会失败。
如果您希望重载dentry方法，则应初始化dentry中的“d_dop”字段；这是一个指向struct “dentry_operations”的指针。此方法是在持有目录inode信号量的情况下调用的。

``link``
	由`link(2)`系统调用调用。如果您希望支持硬链接，则需要实现此方法。您可能需要像在`create()`方法中那样调用`d_instantiate()`。

``unlink``
	由`unlink(2)`系统调用调用。如果您希望支持删除inode，则需要实现此方法。

``symlink``
	由`symlink(2)`系统调用调用。如果您希望支持符号链接，则需要实现此方法。您可能需要像在`create()`方法中那样调用`d_instantiate()`。

``mkdir``
	由`mkdir(2)`系统调用调用。如果您希望支持创建子目录，则需要实现此方法。您可能需要像在`create()`方法中那样调用`d_instantiate()`。

``rmdir``
	由`rmdir(2)`系统调用调用。如果您希望支持删除子目录，则需要实现此方法。

``mknod``
	由`mknod(2)`系统调用调用，用于创建设备（字符、块）inode或命名管道（FIFO）或套接字。如果您希望支持创建这些类型的inode，则需要实现此方法。您可能需要像在`create()`方法中那样调用`d_instantiate()`。

``rename``
	由`rename(2)`系统调用调用，用于重命名具有第二个inode和dentry给定的父目录和名字的对象。
文件系统必须对任何不受支持或未知的标志返回-EINVAL。目前实现了以下标志：
(1) RENAME_NOREPLACE：此标志表示如果重命名的目标已存在，则重命名应失败并返回-EEXIST而不是替换目标。VFS已经检查了存在的目标，因此对于本地文件系统，RENAME_NOREPLACE的实现等同于普通的重命名。
(2) `RENAME_EXCHANGE`: 交换源和目标文件夹。两者都必须存在；这一点由VFS进行检查。与普通的重命名不同，源和目标可以是不同类型。

`get_link`
  由VFS调用以跟随一个符号链接到其指向的inode。仅在支持符号链接时需要此功能。
此方法返回要遍历的符号链接体（并可能通过`nd_jump_link()`重置当前位置）。如果该链接体直到inode消失前都不会失效，则无需其他操作；如果需要以其他方式固定该链接体，请通过`get_link(..., ..., done)`调用`set_delayed_call(done, destructor, argument)`来安排其释放。在这种情况下，一旦VFS完成了对该链接体的处理，将调用`destructor(argument)`。可能会在RCU模式下调用；这可以通过NULL dentry参数来指示。如果请求无法在不离开RCU模式的情况下处理，请返回`ERR_PTR(-ECHILD)`。

如果文件系统将符号链接的目标存储在`->i_link`中，VFS可以直接使用它而无需调用`->get_link()`；但是，仍然需要提供`->get_link()`。`->i_link`在经过一个RCU宽限期后才能被释放。在`iget()`之后写入`->i_link`需要一个“释放”内存屏障。

`readlink`
 现在这只是用于`readlink(2)`的覆盖，适用于`->get_link`使用`nd_jump_link()`的情况或对象实际上不是符号链接的情况。通常，文件系统应该只为符号链接实现`->get_link`，并且`readlink(2)`会自动使用它。

`permission`
  由VFS调用以检查POSIX类文件系统的访问权限。
可能会在rcu-walk模式下调用（掩码&MAY_NOT_BLOCK）。如果在rcu-walk模式下，文件系统必须在不阻塞或不存储到inode的情况下检查权限。
如果遇到rcu-walk无法处理的情况，请返回`-ECHILD`，然后它将以ref-walk模式再次被调用。

`setattr`
  由VFS调用以设置文件的属性。此方法由`chmod(2)`和相关系统调用调用。

`getattr`
  由VFS调用以获取文件的属性。此方法由`stat(2)`和相关系统调用调用。
``listxattr``
由VFS调用以列出给定文件的所有扩展属性。此方法由listxattr(2)系统调用调用。

``update_time``
由VFS调用以更新inode的特定时间或i_version。如果未定义此方法，VFS将自行更新inode并调用mark_inode_dirty_sync。

``atomic_open``
在打开操作的最后一部分被调用。使用这个可选的方法，文件系统可以在一个原子操作中查找、可能创建并打开文件。如果它希望将实际的打开操作留给调用者（例如，如果文件结果是符号链接、设备或其他文件系统不支持原子打开的情况），可以通过返回finish_no_open(file, dentry)来表示这一点。此方法仅在最后一个组件为负数或需要查找时调用。缓存的正dentry仍由f_op->open()处理。如果文件被创建，应在file->f_mode中设置FMODE_CREATED标志。在O_EXCL情况下，只有当文件不存在时该方法才能成功，并且在成功时应始终设置FMODE_CREATED标志。

``tmpfile``
在O_TMPFILE open()的末尾被调用。可选的，相当于在一个给定目录中原子地创建、打开并删除一个文件。成功时需要返回已打开的文件；这可以通过在最后调用finish_open_simple()来完成。

``fileattr_get``
在ioctl(FS_IOC_GETFLAGS)和ioctl(FS_IOC_FSGETXATTR)时被调用以检索文件的各种标志和属性。也在相关SET操作之前被调用以检查正在更改的内容（此时带有锁定的i_rwsem）。如果未设置，则回退到f_op->ioctl()。

``fileattr_set``
在ioctl(FS_IOC_SETFLAGS)和ioctl(FS_IOC_FSSETXATTR)时被调用以更改文件的各种标志和属性。调用者持有独占的i_rwsem。如果未设置，则回退到f_op->ioctl()。

``get_offset_ctx``
被调用以获取目录inode的偏移上下文。文件系统必须定义此操作才能使用simple_offset_dir_operations。

地址空间对象
===============
地址空间对象用于分组和管理页面缓存中的页面。它可以用来跟踪文件（或其他任何东西）中的页面，并且还可以跟踪文件各部分映射到进程地址空间的情况。
地址空间可以提供一些独立但相关的服务。这些服务包括传达内存压力、按地址查找页面以及跟踪标记为Dirty或Writeback的页面。
第一个服务可以独立于其他服务使用。虚拟内存管理器可以尝试通过写入脏页面来清理它们，或者释放干净页面以便重用。为此，它可以对脏页面调用->writepage方法，并对具有私有标志的干净页框调用->release_folio。没有PagePrivate标志且没有外部引用的干净页面将在没有任何通知的情况下被释放。
为了实现这一功能，页面需要放置在一个最近最少使用（LRU）列表中，并且每当使用页面时都需要调用 `lru_cache_add` 和 `mark_page_active`。

页面通常通过 `->index` 保存在径向树索引中。这棵树维护了每一页的 PG_Dirty 和 PG_Writeback 状态信息，以便能够快速找到设置了这些标志位的页面。

Dirty 标志主要用于 `mpage_writepages`——默认的 `->writepages` 方法。它利用这个标志来查找脏页面并调用 `->writepage`。如果未使用 `mpage_writepages`（即地址空间提供了自己的 `->writepages` 方法），那么 `PAGECACHE_TAG_DIRTY` 标志几乎不会被使用。`write_inode_now` 和 `sync_inode` 会通过 `__sync_single_inode` 使用该标志来检查 `->writepages` 是否成功地写出了整个地址空间的内容。

Writeback 标志被 `filemap*wait*` 和 `sync_page*` 函数通过 `filemap_fdatawait_range` 使用，以等待所有回写的完成。

地址空间处理程序可以附加额外的信息到页面上，通常使用 `struct page` 中的 `private` 字段。如果附加了此类信息，则应设置 PG_Private 标志。这将导致各种虚拟内存例程调用地址空间处理程序来处理这些数据。

地址空间作为存储和应用程序之间的中间层。数据以整页的形式读入地址空间，并通过复制页面或内存映射的方式提供给应用程序。数据由应用程序写入地址空间，然后通常以整页的形式回写到存储中，不过地址空间对写入大小有更细粒度的控制。

读取过程基本上只需要 `read_folio`。写入过程更为复杂，使用 `write_begin/write_end` 或 `dirty_folio` 将数据写入地址空间，并使用 `writepage` 和 `writepages` 将数据回写到存储中。

添加和移除地址空间中的页面受 inode 的 `i_mutex` 保护。

当数据写入页面时，应设置 PG_Dirty 标志。通常情况下，该标志会一直保留直到 `writepage` 要求将其写出。此时应清除 PG_Dirty 并设置 PG_Writeback。实际写出可以在清除 PG_Dirty 后的任何时间进行。一旦确认安全后，应清除 PG_Writeback。

回写操作使用一个 `writeback_control` 结构来指导操作。这为 `writepage` 和 `writepages` 操作提供了一些关于回写请求的性质、原因以及执行约束的信息。同时，它也被用来返回 `writepage` 或 `writepages` 请求的结果信息给调用者。
处理写回期间的错误
--------------------------------

大多数执行缓冲I/O的应用程序会周期性地调用文件同步函数（如fsync、fdatasync、msync或sync_file_range）以确保已写入的数据已到达后端存储。当写回过程中出现错误时，它们期望在进行文件同步请求时报告该错误。在一个请求报告了错误之后，对同一文件描述符的后续请求应返回0，除非自上次文件同步以来发生了进一步的写回错误。
理想情况下，内核只在那些写入操作未能成功回写的文件描述符上报告错误。然而，通用页面缓存基础设施并未跟踪每个脏页所对应的文件描述符，因此无法确定哪些文件描述符应该接收到错误信息。
相反，内核中的通用写回错误跟踪基础设施选择在发生错误时向所有打开的文件描述符报告错误。在多写入者的情况下，所有写入者都会在随后的fsync中收到错误，即使通过该特定文件描述符的所有写入都成功了（甚至该文件描述符上根本就没有写入）。

希望使用此基础设施的文件系统应在错误发生时调用`mapping_set_error`来记录地址空间中的错误。然后，在其`file->fsync`操作中从页面缓存写回数据之后，应调用`file_check_and_advance_wb_err`以确保文件结构中的错误指针已推进到由后端设备发出的错误流中的正确位置。

`struct address_space_operations`
-------------------------------

这描述了VFS如何操纵文件映射到您的文件系统的页面缓存。定义了以下成员：

```c
struct address_space_operations {
    int (*writepage)(struct page *page, struct writeback_control *wbc);
    int (*read_folio)(struct file *, struct folio *);
    int (*writepages)(struct address_space *, struct writeback_control *);
    bool (*dirty_folio)(struct address_space *, struct folio *);
    void (*readahead)(struct readahead_control *);
    int (*write_begin)(struct file *, struct address_space *mapping,
                       loff_t pos, unsigned len,
                       struct page **pagep, void **fsdata);
    int (*write_end)(struct file *, struct address_space *mapping,
                     loff_t pos, unsigned len, unsigned copied,
                     struct page *page, void *fsdata);
    sector_t (*bmap)(struct address_space *, sector_t);
    void (*invalidate_folio)(struct folio *, size_t start, size_t len);
    bool (*release_folio)(struct folio *, gfp_t);
    void (*free_folio)(struct folio *);
    ssize_t (*direct_IO)(struct kiocb *, struct iov_iter *iter);
    int (*migrate_folio)(struct mapping *, struct folio *dst,
                         struct folio *src, enum migrate_mode);
    int (*launder_folio)(struct folio *);

    bool (*is_partially_uptodate)(struct folio *, size_t from,
                                  size_t count);
    void (*is_dirty_writeback)(struct folio *, bool *, bool *);
    int (*error_remove_folio)(struct mapping *mapping, struct folio *);
    int (*swap_activate)(struct swap_info_struct *sis, struct file *f, sector_t *span);
    int (*swap_deactivate)(struct file *);
    int (*swap_rw)(struct kiocb *iocb, struct iov_iter *iter);
};
```

`writepage`
由VM调用来将脏页写入后端存储。这可能是出于数据完整性原因（例如“同步”），也可能是为了释放内存（刷新）。可以通过`wbc->sync_mode`看到两者的区别。PG_Dirty标志已被清除，并且PageLocked为真。`writepage`应该启动写操作，设置PG_Writeback，并确保在写操作完成时解锁该页，无论是同步还是异步。
如果`wbc->sync_mode`是WB_SYNC_NONE，则`writepage`不必太努力尝试写入，可以选择写入映射中的其他页（例如，由于内部依赖关系）。如果它选择不启动写操作，应返回AOP_WRITEPAGE_ACTIVATE，以便VM不会继续对该页调用`writepage`。
有关更多详细信息，请参阅“锁定”文件。

`read_folio`
由页面缓存调用来从后端存储读取一个folio。
`file`参数为网络文件系统提供身份验证信息，并通常不被基于块的文件系统使用。
如果调用者没有打开文件（例如，如果内核是在为自己而不是代表用户空间进程执行读取），则它可以为NULL。
如果映射不支持大页（folio），则该页将只包含一个页面。当调用 `read_folio` 时，该页会被锁定。如果读取操作成功完成，则应标记该页为最新状态（uptodate）。文件系统应在读取操作完成后解锁该页，无论读取是否成功。

文件系统无需修改页的引用计数；页缓存持有一个引用计数，并且在页解锁之前不会释放这个引用计数。

文件系统可以同步实现 `->read_folio()` 方法。
在正常操作中，页是通过 `->readahead()` 方法读取的。只有当此方法失败或调用者需要等待读取完成时，页缓存才会调用 `->read_folio()`。
文件系统不应尝试在 `->read_folio()` 操作中执行自己的预读取（readahead）。

如果文件系统此时无法执行读取操作，它可以解锁该页，执行确保未来读取能成功的必要操作，并返回 `AOP_TRUNCATED_PAGE`。
在这种情况下，调用者应查找该页并锁定它，然后再次调用 `->read_folio`。
调用者可以直接调用 `->read_folio()` 方法，但使用 `read_mapping_folio()` 可以处理锁定、等待读取完成以及处理 `AOP_TRUNCATED_PAGE` 等情况。

``writepages``
由虚拟内存管理器调用来写入与地址空间对象关联的页面。如果 `wbc->sync_mode` 是 `WB_SYNC_ALL`，则 `writeback_control` 会指定必须写入的一系列页面。如果是 `WB_SYNC_NONE`，则会给出一个 `nr_to_write` 的值，并且尽可能写入这么多页面。如果没有提供 `->writepages`，则使用 `mpage_writepages` 代替。
这将从地址空间中选择标记为 DIRTY 的页面，并传递给 `->writepage`。
``dirty_folio``
由虚拟内存（VM）调用来标记一个页集（folio）为脏。这在地址空间将私有数据附加到页集，并且该数据需要在页集变脏时更新的情况下特别需要。例如，当内存映射的页面被修改时会调用此函数。如果定义了这个函数，它应该设置页集的脏标志，并在`i_pages`中设置`PAGECACHE_TAG_DIRTY`搜索标记。

``readahead``
由虚拟内存（VM）调用来读取与`address_space`对象关联的页面。这些页面在页缓存中是连续的并且已被锁定。实现应减少每个页面的引用计数后开始I/O操作。通常页面会在I/O完成处理器中解锁。这些页面分为一些同步页面和一些异步页面，`rac->ra->async_size`给出了异步页面的数量。文件系统应尝试读取所有同步页面，但在到达异步页面时可以选择停止。如果决定停止尝试I/O操作，可以简单地返回。调用者将从地址空间中移除剩余页面、解锁它们并减少页面引用计数。如果I/O成功完成，则设置`PageUptodate`标志。任何页面上的`PageError`标志将被忽略；如果发生I/O错误，只需解锁页面即可。

``write_begin``
由通用缓冲写入代码调用，要求文件系统准备在文件给定偏移量处写入len字节的数据。
`address_space`应检查写入是否能够完成，必要时分配空间并进行其他内部管理。如果写入将更新存储中的任何基本块，则应在写入前预读这些块（如果尚未读取的话），以便正确写出更新后的块。
文件系统必须返回指定偏移量处的锁定页缓存页面`*pagep`，供调用者写入。
它必须能够处理短写入（传递给`write_begin`的长度大于实际复制到页面中的字节数）。
可以在`fsdata`中返回一个`void *`指针，然后将其传入`write_end`。
成功时返回0；失败时返回负值（即错误码），在这种情况下不调用`write_end`。

``write_end``
在成功的`write_begin`和数据复制之后，必须调用`write_end`。`len`是最初传递给`write_begin`的长度，而`copied`是指能够被复制的实际字节数。
文件系统必须负责解锁页面并释放其引用计数，并更新 i_size。
失败时返回小于 0 的值，否则返回能够复制到页缓存中的字节数（<= 'copied'）。

``bmap``
由 VFS 调用以将对象内的逻辑块偏移映射到物理块编号。此方法用于 FIBMAP ioctl 和处理交换文件。为了能够将数据交换到一个文件中，该文件必须具有与块设备的稳定映射关系。交换系统不通过文件系统，而是使用 bmap 来查找文件中的块位置，并直接使用这些地址。

``invalidate_folio``
如果 folio 包含私有数据，则在部分或全部 folio 从地址空间移除时会调用 invalidate_folio。这通常对应于截断、打孔或地址空间的完全无效化（在这种情况下 'offset' 总是 0，'length' 是 folio_size()）。任何与 folio 相关的私有数据应更新以反映这种截断。如果 offset 是 0 并且 length 是 folio_size()，则私有数据应该被释放，因为 folio 必须能够被完全丢弃。这可以通过调用 ->release_folio 函数来完成，但在这种情况下，释放必须成功。

``release_folio``
当 folio 包含私有数据并且即将被释放时，会调用 release_folio 告知文件系统。->release_folio 应该从 folio 中移除任何私有数据并清除私有标志。如果 release_folio() 失败，它应该返回 false。

release_folio 在两种不同的但相关的情况下使用：

第一种情况是当 VM 想要释放一个没有活动用户的干净 folio。如果 ->release_folio 成功，folio 将从 address_space 中移除并被释放。

第二种情况是当请求需要使 address_space 中的部分或全部 folio 无效。这可以通过 fadvise(POSIX_FADV_DONTNEED) 系统调用或文件系统显式请求实现，如 NFS 和 9P 所做的那样（当它们认为缓存可能与存储不同步时），通过调用 invalidate_inode_pages2()。如果文件系统发出这样的调用，并且需要确保所有 folio 都被无效化，则其 release_folio 需要确保这一点。如果不能立即释放私有数据，可能可以清除 uptodate 标志。

``free_folio``
当 folio 不再出现在页缓存中时，会调用 free_folio 以允许清理任何私有数据。
由于它可能由内存回收器调用，因此不应假定原始 address_space 映射仍然存在，并且不应阻塞。
``direct_IO``
由通用读写例程调用以执行直接IO——即绕过页面缓存并将数据直接在存储设备和应用程序地址空间之间传输的IO请求。

``migrate_folio``
用于压缩物理内存使用。如果虚拟内存管理器（VM）想要重新定位一个页框（可能是因为该页框所在的内存设备发出了即将发生故障的信号），它会将一个新的页框和一个旧的页框传递给此函数。`migrate_folio` 应该将任何私有数据迁移，并更新其对页框的所有引用。

``launder_folio``
在释放一个页框之前被调用——它会将脏页框的数据写回。为了防止再次将页框标记为脏，整个操作过程中都会锁定该页框。

``is_partially_uptodate``
当通过页面缓存读取文件且底层块大小小于页框大小时，由虚拟内存管理器（VM）调用。如果所需的块是最新的，则读取操作可以完成而无需通过IO将整个页面更新到最新状态。

``is_dirty_writeback``
当虚拟内存管理器（VM）试图回收一个页框时被调用。VM 使用脏和写回信息来判断是否需要暂停以允许刷新程序完成一些IO操作。通常它可以使用 `folio_test_dirty` 和 `folio_test_writeback`，但是一些文件系统具有更复杂的状态（例如NFS中的不稳定页框阻止回收）或由于锁定问题未设置这些标志。此回调允许文件系统指示VM，对于暂停目的而言，某个页框是否应被视为脏或写回状态。

``error_remove_folio``
通常设置为 `generic_error_remove_folio`，如果截断对此地址空间是可以接受的话。用于内存故障处理。设置此函数意味着你需要处理页框消失的情况，除非你已经锁定了它们或增加了引用计数。
### `swap_activate`

当需要为交换文件做准备时调用。它应该执行任何必要的验证和准备工作，以确保能够以最小的内存分配进行写入操作。它应该调用`add_swap_extent()`或辅助函数`iomap_swapfile_activate()`，并返回添加的范围数量。如果IO应通过`->swap_rw()`提交，则应设置`SWP_FS_OPS`，否则IO将直接提交到块设备`sis->bdev`。

### `swap_deactivate`

在`swapoff`过程中调用，针对那些`swap_activate`成功的文件。

### `swap_rw`

当设置了`SWP_FS_OPS`时，用于读取或写入交换页面。

### 文件对象
文件对象表示由进程打开的文件。这在POSIX术语中也称为“打开文件描述符”。

### 结构体 `file_operations`
这个结构体描述了VFS如何操作一个打开的文件。截至内核4.18，定义了以下成员：

```c
struct file_operations {
    struct module *owner;
    loff_t (*llseek) (struct file *, loff_t, int);
    ssize_t (*read) (struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write) (struct file *, const char __user *, size_t, loff_t *);
    ssize_t (*read_iter) (struct kiocb *, struct iov_iter *);
    ssize_t (*write_iter) (struct kiocb *, struct iov_iter *);
    int (*iopoll)(struct kiocb *kiocb, bool spin);
    int (*iterate_shared) (struct file *, struct dir_context *);
    __poll_t (*poll) (struct file *, struct poll_table_struct *);
    long (*unlocked_ioctl) (struct file *, unsigned int, unsigned long);
    long (*compat_ioctl) (struct file *, unsigned int, unsigned long);
    int (*mmap) (struct file *, struct vm_area_struct *);
    int (*open) (struct inode *, struct file *);
    int (*flush) (struct file *, fl_owner_t id);
    int (*release) (struct inode *, struct file *);
    int (*fsync) (struct file *, loff_t, loff_t, int datasync);
    int (*fasync) (int, struct file *, int);
    int (*lock) (struct file *, int, struct file_lock *);
    unsigned long (*get_unmapped_area)(struct file *, unsigned long, unsigned long, unsigned long, unsigned long);
    int (*check_flags)(int);
    int (*flock) (struct file *, int, struct file_lock *);
    ssize_t (*splice_write)(struct pipe_inode_info *, struct file *, loff_t *, size_t, unsigned int);
    ssize_t (*splice_read)(struct file *, loff_t *, struct pipe_inode_info *, size_t, unsigned int);
    int (*setlease)(struct file *, long, struct file_lock **, void **);
    long (*fallocate)(struct file *file, int mode, loff_t offset, loff_t len);
    void (*show_fdinfo)(struct seq_file *m, struct file *f);
#ifndef CONFIG_MMU
    unsigned (*mmap_capabilities)(struct file *);
#endif
    ssize_t (*copy_file_range)(struct file *, loff_t, struct file *, loff_t, size_t, unsigned int);
    loff_t (*remap_file_range)(struct file *file_in, loff_t pos_in, struct file *file_out, loff_t pos_out, loff_t len, unsigned int remap_flags);
    int (*fadvise)(struct file *, loff_t, loff_t, int);
};
```

再次强调，除非另有说明，所有方法都是在没有持有任何锁的情况下被调用的。

- `llseek`: 当VFS需要移动文件位置索引时调用。
- `read`: 被read(2)及相关系统调用调用。
- `read_iter`: 可能是异步读取，目的地为iov_iter。
- `write`: 被write(2)及相关系统调用调用。
- `write_iter`: 可能是异步写入，源为iov_iter。
- `iopoll`: 当AIO想要轮询HIPRI iocbs的完成情况时调用。
- `iterate_shared`: 当VFS需要读取目录内容时调用。
- `poll`: 当进程想要检查文件是否有活动（可选地等待直到有活动）时被VFS调用。由select(2)和poll(2)系统调用调用。
- `unlocked_ioctl`: 被ioctl(2)系统调用调用。
- `compat_ioctl`: 当使用32位系统调用在64位内核上时被ioctl(2)系统调用调用。
- `mmap`: 被mmap(2)系统调用调用。
- `open`: 当一个inode应当被打开时被VFS调用。当VFS打开一个文件时，它会创建一个新的`struct file`，然后对新分配的文件结构调用打开方法。你可能会认为打开方法真正属于`struct inode_operations`，也许你是对的。我认为这样做是因为它使文件系统的实现更简单。`open()`方法是初始化文件结构中的`private_data`成员的好地方，如果你希望指向一个设备结构的话。
- `flush`: 被close(2)系统调用调用来刷新文件。
- `release`: 当最后一个对打开文件的引用被关闭时调用。
- `fsync`: 被fsync(2)系统调用调用。参见上面的“处理写回期间的错误”部分。
- `fasync`: 当非阻塞模式为文件启用时被fcntl(2)系统调用调用。
- `lock`: 被fcntl(2)系统调用用于F_GETLK、F_SETLK和F_SETLKW命令。
- `get_unmapped_area`: 被mmap(2)系统调用调用。
- `check_flags`: 被fcntl(2)系统调用用于F_SETFL命令。
- `flock`: 被flock(2)系统调用调用。
- `splice_write`: 被VFS调用来从管道拼接数据到文件。此方法由splice(2)系统调用使用。
- `splice_read`: 被VFS调用来从文件拼接数据到管道。此方法由splice(2)系统调用使用。
- `setlease`: 被VFS调用来设置或释放文件锁租约。`setlease`实现应该调用`generic_setlease`来记录或移除inode中的租约。
``fallocate``
	由VFS调用以预分配块或打孔

``copy_file_range``
	由copy_file_range(2)系统调用调用

``remap_file_range``
	由ioctl(2)系统调用（针对FICLONERANGE、FICLONE和FIDEDUPERANGE命令）调用来重映射文件范围。实现应将源文件中pos_in位置的len字节重映射到目标文件中的pos_out位置。实现必须处理传入len == 0的情况；这表示“重映射到源文件末尾”。返回值应该是重映射的字节数，如果在任何字节被重映射之前发生错误，则返回通常的负错误代码。remap_flags参数接受REMAP_FILE_*标志。如果设置了REMAP_FILE_DEDUP，则实现仅当请求的文件范围具有相同内容时才进行重映射。如果设置了REMAP_FILE_CAN_SHORTEN，则调用者允许实现根据对齐或EOF要求（或其他任何原因）缩短请求长度。

``fadvise``
	可能由fadvise64()系统调用调用

请注意，文件操作由包含该inode的具体文件系统实现。当打开设备节点（字符或块特殊设备）时，大多数文件系统会调用VFS中的特殊支持例程来定位所需的设备驱动信息。这些支持例程会替换文件系统的文件操作为设备驱动的操作，并调用新的open()方法。这就是文件系统中的设备文件最终调用设备驱动open()方法的方式。

目录项缓存（dcache）
====================

`struct dentry_operations`
--------------------------

此结构描述了文件系统如何重载标准的dentry操作。dentry和dcache是VFS和各个文件系统实现的领域。设备驱动程序不应涉及此处。这些方法可以设置为NULL，因为它们是可选的或者VFS使用默认值。截至内核2.6.22版本，定义的成员如下：

```c
struct dentry_operations {
	int (*d_revalidate)(struct dentry *, unsigned int);
	int (*d_weak_revalidate)(struct dentry *, unsigned int);
	int (*d_hash)(const struct dentry *, struct qstr *);
	int (*d_compare)(const struct dentry *,
			 unsigned int, const char *, const struct qstr *);
	int (*d_delete)(const struct dentry *);
	int (*d_init)(struct dentry *);
	void (*d_release)(struct dentry *);
	void (*d_iput)(struct dentry *, struct inode *);
	char *(*d_dname)(struct dentry *, char *, int);
	struct vfsmount *(*d_automount)(struct path *);
	int (*d_manage)(const struct path *, bool);
	struct dentry *(*d_real)(struct dentry *, enum d_real_type type);
};
```

``d_revalidate``
	当VFS需要重新验证一个dentry时调用。这在名称查找在dcache中找到一个dentry时调用

大多数本地文件系统将其保留为NULL，因为它们在dcache中的所有dentry都是有效的。网络文件系统则不同，因为服务器上的情况可能会发生变化而客户端不一定知道。

如果dentry仍然有效，此函数应返回正值；如果不是，则返回零或负错误代码。
d_revalidate可能在rcu-walk模式下被调用（flags & LOOKUP_RCU）。如果在rcu-walk模式下，文件系统必须在不阻塞或不修改dentry的情况下重新验证dentry，d_parent和d_inode应在小心使用的情况下才使用（因为它们可能会改变，在d_inode情况下，甚至可能变为NULL）

如果遇到rcu-walk无法处理的情况，请返回-ECHILD，然后将在ref-walk模式下调用。
``d_weak_revalidate``
在VFS需要重新验证一个“跳跃”的dentry时调用。这通常发生在路径遍历（path-walk）结束在一个未通过父目录查找获取的dentry时。这包括“/”、“.”、“..”，以及procfs风格的符号链接和挂载点遍历。
在这种情况下，我们更关心的是inode是否仍然有效，而不是dentry是否完全正确。
与`d_revalidate`类似，大多数本地文件系统会将此函数设置为NULL，因为它们的dcache条目始终有效。
该函数具有与`d_revalidate`相同的返回码语义。
`d_weak_revalidate`仅在退出rcu-walk模式后被调用。

``d_hash``
在VFS将一个dentry添加到哈希表时调用。传递给`d_hash`的第一个dentry是该名称要哈希进的父目录。
锁定和同步规则与`d_compare`相同，关于哪些内容可以安全地解引用等。

``d_compare``
用于比较一个dentry名称与给定名称。第一个dentry是待比较dentry的父目录，第二个是子dentry。len和name字符串是待比较dentry的属性，qstr是要与之比较的名称。
必须是常量且幂等的，并且如果可能的话不应获取锁，也不应修改或存储到dentry中。不应在不经过大量谨慎处理的情况下解引用dentry之外的指针（例如，不应使用d_parent、d_inode、d_name）。
然而，我们的vfsmount是固定的，并且RCU持有，因此dentries和inodes不会消失，sb或文件系统模块也不会消失。->d_sb可以使用。
这是一个棘手的调用约定，因为它需要在“rcu-walk”下被调用，即在没有任何锁或对`d_delete`的引用的情况下进行调用。
`d_delete`是在一个目录项（dentry）的最后一个引用被释放，并且dcache决定是否缓存它时被调用。返回1表示立即删除，返回0表示缓存该目录项。默认值为NULL，意味着总是缓存可到达的目录项。`d_delete`必须是常量和幂等的。

`d_init`在分配一个目录项时被调用。

`d_release`在目录项真正被解除分配时被调用。

`d_iput`在目录项失去其inode（在解除分配之前）时被调用。当此方法为NULL时，默认行为是VFS调用`iput()`。如果你定义了这个方法，则必须自己调用`iput()`。

`d_dname`在生成目录项的路径名时被调用。
对于一些伪文件系统（如sockfs、pipefs等）来说，延迟路径名生成是有用的。（不是在创建目录项时生成，而是在需要路径时生成）。真实的文件系统可能不想使用它，因为它们的目录项存在于全局dcache哈希表中，所以它们的哈希值应该是一个不变量。由于没有持有锁，`d_dname()`不应该尝试修改目录项本身，除非使用了适当的SMP保护。

**注意**：`d_path()`逻辑相当复杂。正确的返回方式例如是将字符串放在缓冲区的末尾，并返回指向第一个字符的指针。
提供了`dynamic_dname()`辅助函数来处理这一点。

示例：

```c
static char *pipefs_dname(struct dentry *dent, char *buffer, int buflen)
{
    return dynamic_dname(dent, buffer, buflen, "pipe:[%lu]", dent->d_inode->i_ino);
}
```

`d_automount`在要遍历一个自动挂载目录项时被调用（可选）。
这应该创建一个新的VFS挂载记录并将其返回给调用者。调用者会提供一个路径参数，给出描述自动挂载目标的自动挂载目录以及提供可继承挂载参数的父VFS挂载记录。如果其他人已经成功地进行了自动挂载，则应返回NULL。如果vfsmount创建失败，则应返回错误代码。如果返回-EISDIR，则该目录将被视为普通目录，并返回给路径遍历以继续遍历。
如果返回了一个vfsmount，则调用者将尝试在其挂载点上挂载它，并在失败的情况下从其过期列表中移除vfsmount。vfsmount应带有两个引用以防止自动过期——调用者将清理额外的引用。
此函数仅在目录项上设置了DCACHE_NEED_AUTOMOUNT标志时使用。如果在添加的inode上设置了S_AUTOMOUNT标志，则由`__d_instantiate()`设置此标志。
``d_manage``
调用此函数允许文件系统管理从一个目录项（dentry）的转换（可选）。例如，这允许autofs挂起正在等待探索“挂载点”后面的客户端，同时让守护进程继续前进并在此处构建子树。应返回0以让调用进程继续执行。可以返回-EISDIR来告诉路径遍历（pathwalk）将该目录视为普通目录，并忽略其上的任何挂载且不检查自动挂载标志。任何其他错误代码将完全中止路径遍历。

如果`rcu_walk`参数为真，则调用者正在RCU-walk模式下进行路径遍历。在这种模式下不允许睡眠，并且可以通过返回-ECHILD请求调用者离开该模式并再次调用。也可以返回-EISDIR告诉路径遍历忽略d_automount或任何挂载。

只有当被转换的目录项设置了DCACHE_MANAGE_TRANSIT标志时才会使用此函数。

``d_real``
覆盖/联合类型的文件系统实现此方法以返回一个被覆盖的常规文件的底层目录项。
参数`type`取值D_REAL_DATA或D_REAL_METADATA，用于返回指向包含文件数据或元数据的inode的底层目录项。
对于非常规文件，返回参数`dentry`本身。
每个目录项都有一个指向其父目录项的指针以及一个子目录项的哈希列表。子目录项基本上就像目录中的文件一样。

目录项缓存API
--------------------------

定义了多个函数允许文件系统操作目录项：

``dget``
为现有的目录项打开一个新的句柄（这仅增加使用计数）。

``dput``
关闭一个目录项的句柄（减少使用计数）。如果使用计数降为0，并且目录项仍在其父目录的哈希表中，则调用"d_delete"方法检查是否应该缓存。如果不应该缓存或者目录项未被哈希，则删除它。否则，缓存的目录项将放入LRU列表以便在内存不足时回收。

``d_drop``
将目录项从其父目录的哈希列表中解除哈希。随后对dput()的调用将在使用计数降至0时释放目录项。

``d_delete``
删除一个目录项。如果没有其他对目录项的引用，则将目录项转换为负目录项（调用d_iput()方法）。如果有其他引用，则调用d_drop()代替。

``d_add``
将目录项添加到其父目录的哈希列表中，然后调用d_instantiate()。

``d_instantiate``
将目录项添加到inode的别名哈希列表中并更新"d_inode"成员。inode结构中的"i_count"成员应设置/递增。如果inode指针为NULL，则称该目录项为“负目录项”。此函数通常在为现有负目录项创建inode时调用。

``d_lookup``
根据其父目录项和路径名组件查找目录项。它从dcache哈希表中查找具有指定名称的子目录项。如果找到，则递增引用计数并返回目录项。调用者必须在使用完毕后通过dput()释放目录项。

挂载选项
=============

解析选项
---------------

在挂载和重新挂载时，文件系统会收到一个包含逗号分隔的挂载选项列表的字符串。这些选项可以有以下两种形式：

  option
  option=value

<linux/parser.h>头文件定义了一个帮助解析这些选项的API。现有文件系统中有许多如何使用它的示例。
显示选项
---------------
如果一个文件系统接受挂载选项，则必须定义 `show_options()` 来显示所有当前激活的选项。规则如下：

- 必须显示那些非默认值或其值与默认值不同的选项。

- 可以选择性地显示那些默认情况下已启用或具有默认值的选项。

仅在挂载辅助程序和内核之间内部使用的选项（例如文件描述符），或者仅在挂载过程中有效的选项（例如控制日志创建的选项）不受上述规则限制。
制定上述规则的根本原因是确保能够根据 `/proc/mounts` 中的信息准确地复制挂载操作（例如卸载后重新挂载）。

资源
=========
（注意，以下一些资源可能没有更新到最新内核版本。）

创建 Linux 虚拟文件系统。2002
<https://lwn.net/Articles/13325/>

Neil Brown 的《Linux 虚拟文件系统层》。1999
<http://www.cse.unsw.edu.au/~neilb/oss/linux-commentary/vfs.html>

Michael K. Johnson 的《Linux VFS 导览》。1996
<https://www.tldp.org/LDP/khg/HyperNews/get/fs/vfstour.html>

Andries Brouwer 的《穿过 Linux 内核的小径》。2001
<https://www.win.tue.nl/~aeb/linux/vfs/trail.html>
