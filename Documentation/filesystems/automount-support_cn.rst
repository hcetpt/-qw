SPDX 许可声明标识符: GPL-2.0

=================
自动挂载支持
=================

对于希望进行自动挂载的文件系统（如可以在 fs/afs/ 中找到的 kAFS 和在 fs/nfs/ 中的 NFS），提供了支持。此功能包括允许内核中的挂载操作以及请求挂载点降级。后者也可以由用户空间请求。

内核自动挂载
======================

请参阅文档文件系统 autofs.rst 中的“挂载陷阱”部分。

然后，从用户空间，您可以执行类似以下的操作：

```
[root@andromeda root]# mount -t afs #root.afs. /afs
[root@andromeda root]# ls /afs
asd  cambridge  cambridge.redhat.com  grand.central.org
[root@andromeda root]# ls /afs/cambridge
afsdoc
[root@andromeda root]# ls /afs/cambridge/afsdoc/
ChangeLog  html  LICENSE  pdf  RELNOTES-1.2.2
```

然后，如果您查看挂载点目录，您将看到如下内容：

```
[root@andromeda root]# cat /proc/mounts
...
#root.afs. /afs afs rw 0 0
#root.cell. /afs/cambridge.redhat.com afs rw 0 0
#afsdoc. /afs/cambridge.redhat.com/afsdoc afs rw 0 0
```

自动挂载点过期
===========================

如果已按照单独描述的自动挂载过程挂载了要过期的挂载点，则自动挂载点过期很容易实现。要进行过期处理，需要遵循以下步骤：

1. 创建至少一个列表，以便可以将要过期的 vfsmount 挂在这个列表上。
2. 当在 ->d_automount 方法中创建新的挂载点时，使用 mnt_set_expiry() 将 mnt 添加到该列表中：

   ```
   mnt_set_expiry(newmnt, &afs_vfsmounts);
   ```

3. 当需要挂载点过期时，使用指向该列表的指针调用 mark_mounts_for_expiry()。这将处理列表，在下次调用时标记每个 vfsmount 以供潜在过期。
   如果一个 vfsmount 已被标记为过期，并且其使用计数为 1（仅由其父 vfsmount 引用），则它将从命名空间中删除并丢弃（实际上是卸载）。
   
可以定期调用此函数，使用某种定时事件来驱动它。
过期标志会在调用 mntput 时清除。这意味着过期只有在上次访问挂载点后的第二次过期请求时才会发生。
如果挂载点被移动，它将从过期列表中移除。如果对可过期挂载进行了绑定挂载，新 vfsmount 不会在过期列表中，也不会过期。
如果复制了命名空间，则包含的所有挂载点都将被复制，并且那些在过期列表上的副本将被添加到相同的过期列表中。
用户空间驱动的过期
=======================

作为一种替代方案，用户空间可以请求任何挂载点的过期（尽管某些挂载点会被拒绝，例如当前进程认为的根文件系统）。这通过向 `umount()` 传递 `MNT_EXPIRE` 标志来实现。这个标志被认为与 `MNT_FORCE` 和 `MNT_DETACH` 不兼容。

如果该挂载点被 `umount()` 之外的其他东西或其父挂载点引用，则会返回 `EBUSY` 错误，并且该挂载点不会被标记为过期或卸载。

如果该挂载点在那时还没有被标记为过期，则会给出 `EAGAIN` 错误，并且它不会被卸载。

否则，如果它已经被标记为过期并且没有被引用，则卸载将照常进行。

再次说明，每当除了 `umount()` 之外的任何操作查看一个挂载点时，过期标志都会被清除。
