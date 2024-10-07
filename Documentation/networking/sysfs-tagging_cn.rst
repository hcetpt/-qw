SPDX 许可证标识符: GPL-2.0

=============
Sysfs 标签
=============

（几乎逐字逐句地取自 Eric Biederman 的 netns 标签补丁提交信息）

问题所在。网络设备会出现在 sysfs 中，而当网络命名空间处于活动状态时，具有相同名称的多个设备可能会出现在同一个目录中，这会导致冲突！

为了避免这个问题，并允许网络命名空间中的现有应用程序看到当前在 sysfs 中呈现的相同接口，sysfs 现在支持标签目录。
通过使用网络命名空间指针作为标签来区分 sysfs 目录条目，我们确保目录中不会发生冲突，并且应用程序只能看到有限的一组网络设备。
每个 sysfs 目录条目的 `kernfs_node` 结构体中的 `void *ns member` 可以被一个命名空间标记。如果一个目录条目被标记，则 `kernfs_node->flags` 将包含介于 KOBJ_NS_TYPE_NONE 和 KOBJ_NS_TYPES 之间的标志，而 `ns` 指向它所属的命名空间。
每个 sysfs 超级块的 `kernfs_super_info` 包含一个数组 `void *ns[KOBJ_NS_TYPES]`。当一个在标签命名空间 kobj_nstype 下的任务首次挂载 sysfs 时，会创建一个新的超级块。它将通过设置 `s_fs_info->ns[kobj_nstype]` 到新的命名空间来与其他 sysfs 挂载区分开。需要注意的是，通过绑定挂载和挂载传播，一个任务可以轻松查看其他命名空间的 sysfs 挂载的内容。因此，当一个命名空间退出时，它将调用 `kobj_ns_exit()` 来使任何指向它的 `kernfs_node->ns` 指针失效。
此接口的使用者：

- 在 `kobj_ns_type` 枚举中定义一个类型
- 调用 `kobj_ns_type_register()` 并传入其 `kobj_ns_type_operations`，该结构包含：

  - `current_ns()`：返回当前命名空间
  - `netlink_ns()`：返回一个套接字的命名空间
  - `initial_ns()`：返回初始命名空间

- 当单个标签不再有效时，调用 `kobj_ns_exit()`
