=======================================================
Configfs - 用户空间驱动的内核对象配置
=======================================================

乔尔·贝克尔 <joel.becker@oracle.com>

更新日期：2005年3月31日

版权所有 © 2005 Oracle 公司，
乔尔·贝克尔 <joel.becker@oracle.com>

什么是 configfs？
=================

configfs 是一个基于内存的文件系统，提供了与 sysfs 相反的功能。sysfs 是内核对象的一种基于文件系统的视图，而 configfs 则是内核对象或 config_items 的一种基于文件系统的管理器。
在 sysfs 中，当设备被发现时，会在内核中创建一个对象，并将其注册到 sysfs。其属性会出现在 sysfs 中，允许用户空间通过 readdir(3)/read(2) 来读取这些属性。它可能允许通过 write(2) 修改某些属性。重要的一点是，对象是在内核中创建和销毁的，内核控制着 sysfs 表示法的生命周期，而 sysfs 仅仅是所有这一切的一个窗口。
一个 configfs 的 config_item 是通过用户空间的明确操作创建的：mkdir(2)。它通过 rmdir(2) 销毁。属性在 mkdir(2) 时出现，并且可以通过 read(2) 和 write(2) 进行读取或修改。
与 sysfs 类似，readdir(3) 可以查询项目和/或属性列表，symlink(2) 可用于将项目分组。与 sysfs 不同的是，表示法的生命周期完全由用户空间驱动。支持这些项目的内核模块必须对此作出响应。
sysfs 和 configfs 都可以在同一系统上共存。一个不是另一个的替代品。

使用 configfs
==============

configfs 可以作为模块编译，也可以编译进内核。你可以通过以下命令来访问它：

```
mount -t configfs none /config
```

除非加载了客户端模块，否则 configfs 树将是空的。
这些是将它们的项类型注册为 configfs 子系统的模块。一旦加载了一个客户端子系统，它将作为一个子目录（或多个）出现在 /config 下。与 sysfs 类似，无论是否挂载在 /config 上，configfs 树始终存在。
一个项是通过 mkdir(2) 创建的。项的属性也会在此时出现。readdir(3) 可以确定属性是什么，read(2) 可以查询它们的默认值，write(2) 可以存储新值。不要在一个属性文件中混合超过一个属性。
有两种类型的 configfs 属性：

* 正常属性，类似于 sysfs 属性，是小的 ASCII 文本文件，最大大小为一页（PAGE_SIZE，在 i386 上为 4096）。每个文件最好只使用一个值，并且与 sysfs 相同的注意事项也适用。
Configfs 期望 `write(2)` 一次存储整个缓冲区。当写入正常的 configfs 属性时，用户空间进程应首先读取整个文件，修改他们想要更改的部分，然后将整个缓冲区写回。

* 二进制属性，类似于 sysfs 的二进制属性，但语义上有一些细微变化。PAGE_SIZE 限制不适用，但整个二进制项必须适合单个内核 vmalloc 分配的缓冲区。
从用户空间调用的 `write(2)` 被缓冲，并且在最终关闭时会调用属性的 `write_bin_attribute` 方法，因此用户空间必须检查 `close(2)` 的返回码以验证操作是否成功完成。
为了避免恶意用户使内核出现内存耗尽（OOM），每个二进制属性都有一个最大缓冲区值。
当需要销毁一个项时，使用 `rmdir(2)` 删除它。如果任何其他项有指向该项的链接（通过 `symlink(2)`），则不能销毁该项。链接可以通过 `unlink(2)` 删除。

配置 FakeNBD：一个示例
===============================

假设有一个网络块设备（NBD）驱动程序，允许你访问远程块设备。称其为 FakeNBD。FakeNBD 使用 configfs 进行配置。显然，会有个很好的程序供系统管理员用来配置 FakeNBD，但这个程序需要告诉驱动程序相关的配置信息。这就是 configfs 的作用所在。
当 FakeNBD 驱动程序加载时，它会在 configfs 中注册自己。`readdir(3)` 可以看到这一点：

	# ls /config
	fakenbd

可以使用 `mkdir(2)` 创建一个 FakeNBD 连接。名称是任意的，但工具可能会利用名称。也许它是 UUID 或磁盘名称：

	# mkdir /config/fakenbd/disk1
	# ls /config/fakenbd/disk1
	target device rw

`target` 属性包含 FakeNBD 将连接到的服务器的 IP 地址。`device` 属性是服务器上的设备。
如预期的那样，`rw` 属性确定连接是只读还是读写：

	# echo 10.0.0.1 > /config/fakenbd/disk1/target
	# echo /dev/sda1 > /config/fakenbd/disk1/device
	# echo 1 > /config/fakenbd/disk1/rw

就这样。就是这样。现在设备已经通过 shell 配置好了。

使用 configfs 编程
====================

configfs 中的每个对象都是一个 config_item。config_item 反映了子系统中的一个对象。它具有与该对象匹配的属性。configfs 处理该对象及其属性的文件系统表示，允许子系统忽略除基本显示/存储交互之外的所有内容。
项目在 `config_group` 中创建和销毁。一个组是由具有相同属性和操作的项目组成的集合。项目通过 `mkdir(2)` 创建并通过 `rmdir(2)` 删除，但这些操作由 `configfs` 处理。组有一组用于执行这些任务的操作。

子系统是客户端模块的顶级部分。在初始化期间，客户端模块会将子系统注册到 `configfs`，此时子系统会作为 `configfs` 文件系统的顶层目录出现。子系统也是一个 `config_group`，可以执行 `config_group` 的所有操作。

`struct config_item`
==================
```c
struct config_item {
    char                    *ci_name;
    char                    ci_namebuf[UOBJ_NAME_LEN];
    struct kref             ci_kref;
    struct list_head        ci_entry;
    struct config_item      *ci_parent;
    struct config_group     *ci_group;
    struct config_item_type *ci_type;
    struct dentry           *ci_dentry;
};

void config_item_init(struct config_item *);
void config_item_init_type_name(struct config_item *, const char *name, struct config_item_type *type);
struct config_item *config_item_get(struct config_item *);
void config_item_put(struct config_item *);
```

通常情况下，`struct config_item` 嵌入在一个容器结构中，这个容器结构实际上表示了子系统正在做的事情。该结构中的 `config_item` 部分定义了对象如何与 `configfs` 交互。
无论是在源文件中静态定义还是由父 `config_group` 创建，`config_item` 必须调用其中一个 `_init()` 函数。这初始化引用计数并设置适当的字段。
所有使用 `config_item` 的用户都应通过 `config_item_get()` 获取一个引用，并在完成后通过 `config_item_put()` 释放引用。
单独的 `config_item` 除了在 `configfs` 中显示之外，不能做更多的事情。
通常子系统希望项目能够显示和/或存储属性等其他功能。为此，它需要一种类型。

`struct config_item_type`
=======================
```c
struct configfs_item_operations {
    void (*release)(struct config_item *);
    int (*allow_link)(struct config_item *src, struct config_item *target);
    void (*drop_link)(struct config_item *src, struct config_item *target);
};

struct config_item_type {
    struct module                           *ct_owner;
    struct configfs_item_operations         *ct_item_ops;
    struct configfs_group_operations        *ct_group_ops;
    struct configfs_attribute               **ct_attrs;
    struct configfs_bin_attribute           **ct_bin_attrs;
};
```

`config_item_type` 的最基本功能是定义可以对 `config_item` 执行哪些操作。所有动态分配的项目都需要提供 `ct_item_ops->release()` 方法。当 `config_item` 的引用计数达到零时，会调用此方法。

`struct configfs_attribute`
=========================
```c
struct configfs_attribute {
    char                    *ca_name;
    struct module           *ca_owner;
    umode_t                  ca_mode;
    ssize_t (*show)(struct config_item *, char *);
    ssize_t (*store)(struct config_item *, const char *, size_t);
};
```

当 `config_item` 希望某个属性以文件的形式出现在其 `configfs` 目录中时，必须定义一个 `configfs_attribute` 来描述它。
然后将该属性添加到 `config_item_type->ct_attrs` 的 NULL 终止数组中。当项目出现在 `configfs` 中时，属性文件将以 `configfs_attribute->ca_name` 作为文件名出现。`configfs_attribute->ca_mode` 指定了文件权限。
如果一个属性是可读的并且提供了一个 `->show` 方法，那么每当用户空间请求对该属性进行读取操作时，该方法将被调用。如果一个属性是可写的并且提供了一个 `->store` 方法，那么每当用户空间请求对该属性进行写入操作时，该方法将被调用。

```c
struct configfs_bin_attribute {
    struct configfs_attribute cb_attr;
    void *cb_private;
    size_t cb_max_size;
};
```

二进制属性用于当需要使用二进制数据块作为文件内容出现在项目配置文件系统目录中时。为此，需要将二进制属性添加到 `config_item_type->ct_bin_attrs` 的空终止数组中。当项目出现在配置文件系统中时，属性文件将以 `configfs_bin_attribute->cb_attr.ca_name` 作为文件名出现。`configfs_bin_attribute->cb_attr.ca_mode` 指定了文件权限。
`cb_private` 成员供驱动程序使用，而 `cb_max_size` 成员指定了最大可用的 `vmalloc` 缓冲区大小。
如果二进制属性是可读的，并且 `config_item` 提供了 `ct_item_ops->read_bin_attribute()` 方法，则每当用户空间请求对该属性进行读取操作时，该方法将被调用。反之亦然，对于写入操作也是如此。读取/写入是缓冲的，因此只会发生一次读取/写入；属性无需关心这一点。

```c
struct config_group {
    struct config_item cg_item;
    struct list_head cg_children;
    struct configfs_subsystem *cg_subsys;
    struct list_head default_groups;
    struct list_head group_entry;
};

void config_group_init(struct config_group *group);
void config_group_init_type_name(struct config_group *group,
                                 const char *name,
                                 struct config_item_type *type);
```

`config_item` 不能孤立存在。唯一可以创建的方式是通过在 `config_group` 上调用 `mkdir(2)`。这将触发子项的创建：

`config_group` 结构包含一个 `config_item`。正确配置这个项意味着组本身可以作为一个项来表现。
然而，它可以做更多：它可以创建子项或组。这是通过组的操作指定在组的 `config_item_type` 上实现的：

```c
struct configfs_group_operations {
    struct config_item *(*make_item)(struct config_group *group,
                                     const char *name);
    struct config_group *(*make_group)(struct config_group *group,
                                       const char *name);
    void (*disconnect_notify)(struct config_group *group,
                              struct config_item *item);
    void (*drop_item)(struct config_group *group,
                      struct config_item *item);
};
```

组通过提供 `ct_group_ops->make_item()` 方法来创建子项。如果提供了此方法，此方法将在组目录上调用 `mkdir(2)` 时被调用。子系统分配一个新的 `config_item`（更可能是其容器结构），初始化它，并将其返回给配置文件系统。然后配置文件系统将更新文件系统树以反映新项。
如果子系统希望子项本身是一个组，子系统提供 `ct_group_ops->make_group()`。其他一切行为相同，使用组的 `_init()` 函数。
最后，当用户空间对项或组调用 `rmdir(2)` 时，`ct_group_ops->drop_item()` 将被调用。由于 `config_group` 也是一个 `config_item`，因此不需要单独的 `drop_group()` 方法。
子系统必须通过 `config_item_put()` 释放项分配时初始化的引用。如果子系统没有工作要做，它可以省略 `ct_group_ops->drop_item()` 方法，配置文件系统将代表子系统调用 `config_item_put()`。
重要：
   `drop_item()` 是一个空函数，因此无法失败。当调用 `rmdir(2)` 时，假设该项没有子项使其忙碌，configfs 将从文件系统树中移除该项。子系统需要对此作出响应。如果子系统在其他线程中有对该项的引用，则内存是安全的。该项实际从子系统的使用中消失可能需要一些时间，但在 configfs 中它已经消失了。
   
   当调用 `drop_item()` 时，该项的链接已经被拆除。它不再有对其父项的引用，并且在项目层次结构中没有位置。如果客户端需要在此拆卸之前进行一些清理工作，子系统可以实现 `ct_group_ops->disconnect_notify()` 方法。此方法在 configfs 从文件系统视图中移除该项但尚未将其从父组中移除之前被调用。与 `drop_item()` 类似，`disconnect_notify()` 也是空函数且不能失败。客户端子系统不应在这里释放任何引用，因为它们仍然必须在 `drop_item()` 中执行此操作。
   
   如果一个 `config_group` 还有子项，则不能被移除。这是在 configfs 的 `rmdir(2)` 代码中实现的。`->drop_item()` 不会被调用，因为该项并未被删除。`rmdir(2)` 将会失败，因为目录不为空。

结构体 `configfs_subsystem`
=========================
   
   子系统通常需要在模块初始化时注册自身。这告诉 configfs 在文件树中显示该子系统：

   ```c
   struct configfs_subsystem {
       struct config_group su_group;
       struct mutex su_mutex;
   };

   int configfs_register_subsystem(struct configfs_subsystem *subsys);
   void configfs_unregister_subsystem(struct configfs_subsystem *subsys);
   ```

   子系统由一个顶级 `config_group` 和一个互斥锁组成。该组是创建子 `config_item` 的地方。对于子系统，这个组通常是静态定义的。在调用 `configfs_register_subsystem()` 之前，子系统必须通过常规的 `group_init()` 函数初始化该组，并且还必须初始化互斥锁。
   
   当注册调用返回时，子系统已激活，并将通过 configfs 可见。此时，可以调用 `mkdir(2)` 并且子系统必须准备好接收此调用。

一个示例
========

这些基本概念的最佳示例是 `simple_children` 子系统/组和 `simple_child` 项，位于 `samples/configfs/configfs_sample.c` 中。它展示了一个简单的对象，用于显示和存储属性，以及一个简单的组来创建和销毁这些子项。

层次导航和子系统互斥锁
============================

configfs 提供了一个额外的好处。由于它们出现在文件系统中，`config_groups` 和 `config_items` 被组织成一个层次结构。子系统永远不要触碰文件系统部分，但子系统可能会对这个层次结构感兴趣。为此，该层次结构通过 `config_group->cg_children` 和 `config_item->ci_parent` 结构成员进行镜像。
   
   子系统可以通过遍历 `cg_children` 列表和 `ci_parent` 指针来查看由子系统创建的树。这可能会与 configfs 管理层次结构发生竞争，因此 configfs 使用子系统互斥锁来保护修改。每当子系统想要遍历层次结构时，它必须在子系统互斥锁的保护下进行。
   
   子系统在新分配的项未被链接到此层次结构时将无法获取互斥锁。同样，在一个即将移除的项未被解链之前，它也无法获取互斥锁。这意味着只要项在 configfs 中，其 `ci_parent` 指针永远不会为 NULL，并且项仅在其父项的 `cg_children` 列表中存在相同的时间段。这使得子系统可以在持有互斥锁时信任 `ci_parent` 和 `cg_children`。
通过符号链接 (symlink(2)) 进行项目聚合
===================================

`configfs` 通过 `group->item` 的父子关系提供了一个简单的分组方式。然而，在许多情况下，更大的环境需要在父子关系之外进行聚合。这可以通过 `symlink(2)` 来实现。

一个 `config_item` 可以提供 `ct_item_ops->allow_link()` 和 `ct_item_ops->drop_link()` 方法。如果存在 `->allow_link()` 方法，则可以调用 `symlink(2)` 将 `config_item` 作为链接的源。

这些链接仅允许在 `configfs` 中的 `config_item` 之间创建。任何尝试在 `configfs` 文件系统之外创建 `symlink(2)` 都会被拒绝。

当调用 `symlink(2)` 时，源 `config_item` 的 `->allow_link()` 方法会被调用，并传入自身和目标项。如果源项允许与目标项链接，则返回 0。如果源项只希望链接到特定类型的对象（例如，其子系统中的对象），它可以拒绝链接。

当对符号链接调用 `unlink(2)` 时，会通过 `->drop_link()` 方法通知源项。像 `->drop_item()` 方法一样，这是一个不返回失败的空函数。子系统负责响应这种变化。

一个 `config_item` 在链接到其他项时不能被移除，同样，当有其他项链接到它时也不能被移除。`configfs` 不允许存在悬挂的符号链接。

自动创建的子组
===================

一个新的 `config_group` 可能希望有两个不同类型的子 `config_item`。虽然可以通过在 `->make_item()` 中使用魔法名称来实现这一点，但更明确的方法是让用户空间看到这种差异。

与其让一个组中的一些项与其他项的行为不同，`configfs` 提供了一种方法，即在父组创建时自动创建一个或多个子组。因此，`mkdir("parent")` 会导致创建 "parent"、"parent/subgroup1" 到 "parent/subgroupN"。类型 1 的项现在可以在 "parent/subgroup1" 中创建，类型 N 的项可以在 "parent/subgroupN" 中创建。

这些自动创建的子组（或默认组）并不排除其他子项。如果存在 `ct_group_ops->make_group()`，则可以在父组上直接创建其他子组。
配置文件子系统通过使用 `configfs_add_default_group()` 函数将默认组添加到父 `config_group` 结构中来指定默认组。每个添加的组会在配置文件树中与父组同时创建。同样地，它们也会在父组被移除时同时被移除。不会提供额外的通知。当 `->drop_item()` 方法调用通知子系统父组即将消失时，这也意味着与该父组相关的所有默认组子项也将消失。因此，默认组不能直接通过 `rmdir(2)` 命令删除。在对父组执行 `rmdir(2)` 检查子项时，也不会考虑这些默认组。

### 依赖子系统

有时其他驱动程序依赖于特定的配置文件项。例如，ocfs2 挂载依赖于一个心跳区域项。如果该区域项通过 `rmdir(2)` 被移除，ocfs2 挂载必须触发 `BUG` 或者进入只读模式。这并不是理想的情况。

配置文件系统提供了两个额外的 API 调用：`configfs_depend_item()` 和 `configfs_undepend_item()`。客户端驱动可以通过调用 `configfs_depend_item()` 来告诉配置文件系统它依赖于某个现有项。配置文件系统会为该项返回 `-EBUSY` 以阻止 `rmdir(2)` 的操作。当该项不再被依赖时，客户端驱动可以通过调用 `configfs_undepend_item()` 来解除依赖。

这些 API 不能在任何配置文件回调函数下调用，因为它们会产生冲突。它们可以阻塞并分配资源。客户端驱动最好不要自作主张地调用它们，而是应该提供一个外部子系统可以调用的 API。

这是如何工作的？想象一下 ocfs2 挂载过程。当它挂载时，会请求一个心跳区域项。这是通过调用心跳代码实现的。在心跳代码内部，查找该区域项。此时，心跳代码会调用 `configfs_depend_item()`。如果调用成功，则心跳知道该区域是安全的，可以提供给 ocfs2 使用。如果失败，则表示该区域项本来就要被移除，心跳可以优雅地传递错误。
