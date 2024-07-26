### SPDX 许可证标识符: GPL-2.0

#### Sysfs 标签系统

（几乎逐字摘自 Eric Biederman 的网络命名空间标签补丁提交信息）

**问题。** 网络设备会出现在 sysfs 中，而且当网络命名空间启用时，相同名称的多个设备可能会出现在同一个目录中，这会导致冲突！

为了避免这个问题，并允许网络命名空间中的现有应用程序看到当前在 sysfs 中呈现的同一接口，sysfs 现在支持标签目录。
通过使用网络命名空间指针作为标签来区分 sysfs 目录条目，我们确保不会在目录中发生冲突，应用程序只能看到有限的一组网络设备。
每个 sysfs 目录条目可以通过其 `kernfs_node` 结构中的 `void *ns` 成员进行标记。如果一个目录条目被标记，则 `kernfs_node->flags` 将包含一个介于 `KOBJ_NS_TYPE_NONE` 和 `KOBJ_NS_TYPES` 之间的标志，而 `ns` 指向它所属的命名空间。
每个 sysfs 超级块的 `kernfs_super_info` 包含一个数组 `void *ns[KOBJ_NS_TYPES]`。当一个位于标签命名空间 `kobj_nstype` 中的任务首次挂载 sysfs 时，将创建一个新的超级块。它通过将其 `s_fs_info->ns[kobj_nstype]` 设置为新的命名空间与其他 sysfs 挂载区相区别。需要注意的是，通过绑定挂载和挂载传播，一个任务可以轻松查看其他命名空间的 sysfs 挂载的内容。因此，当一个命名空间退出时，它会调用 `kobj_ns_exit()` 来使指向它的任何 `kernfs_node->ns` 指针失效。

**此接口的使用者：**

- 在 `kobj_ns_type` 枚举中定义一个类型；
- 使用其 `kobj_ns_type_operations` 调用 `kobj_ns_type_register()`，其中包含：

  - `current_ns()` 函数返回当前命名空间；
  - `netlink_ns()` 函数返回套接字的命名空间；
  - `initial_ns()` 函数返回初始命名空间；

- 当某个特定标签不再有效时，调用 `kobj_ns_exit()`。
