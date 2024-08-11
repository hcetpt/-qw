### 内存热插拔

#### 内存热插拔事件通知器

热插拔事件被发送到一个通知队列中。在`include/linux/memory.h`中定义了六种类型的通知：

- `MEM_GOING_ONLINE`
  在新内存变为可用之前生成，以便能够准备子系统来处理内存。此时页面分配器仍然无法从新内存中分配。
- `MEM_CANCEL_ONLINE`
  如果`MEM_GOING_ONLINE`失败时生成。
- `MEM_ONLINE`
  当内存成功上线时生成。回调函数可以从新内存中分配页面。
- `MEM_GOING_OFFLINE`
  生成以开始下线内存的过程。不再可能从该内存进行分配，但要下线的一些内存仍在使用中。可以通过回调函数释放子系统已知的、来自指定内存块的内存。
- `MEM_CANCEL_OFFLINE`
  如果`MEM_GOING_OFFLINE`失败时生成。再次可以从尝试下线的内存块中获取内存。
- `MEM_OFFLINE`
  在完成内存下线后生成。

可以通过调用以下函数注册回调例程：

```c
hotplug_memory_notifier(callback_func, priority)
```

具有较高优先级值的回调函数将在具有较低优先级值的回调函数之前被调用。
回调函数必须具有以下原型：

```c
int callback_func(
    struct notifier_block *self, unsigned long action, void *arg);
```

回调函数的第一个参数（self）是指向包含该回调函数自身的通知链表块的指针。
第二个参数（action）是上述事件类型之一。
第三个参数 (arg) 传递了 `struct memory_notify` 的指针:

    ```c
    struct memory_notify {
        unsigned long start_pfn;      // 在线/离线内存的起始页框号
        unsigned long nr_pages;       // 在线/离线内存的页数
        int status_change_nid_normal; // 当nodemask中的N_NORMAL_MEMORY被设置/清除时，设置节点ID；如果为-1，则nodemask状态不变
        int status_change_nid;        // 当nodemask中的N_MEMORY被设置/清除时，设置节点ID。这意味着新（无内存）节点通过在线操作获得新内存，或一个节点失去所有内存；如果为-1，则nodemask状态不变
    }
    ```

- `start_pfn` 是在线/离线内存的起始页框号。
- `nr_pages` 是在线/离线内存的页数。
- `status_change_nid_normal` 在nodemask中的N_NORMAL_MEMORY被设置/清除时，设置节点ID；如果为-1，则表示nodemask状态没有改变。
- `status_change_nid` 在nodemask中的N_MEMORY被设置/清除时，设置节点ID。这表示一个新的（无内存）节点通过在线操作获得了新内存，或者某个节点失去了所有内存；如果为-1，则表示nodemask状态没有改变。

如果 `status_change_nid* >= 0`，回调函数应该根据需要为该节点创建/删除结构。

回调例程应返回 `NOTIFY_DONE`, `NOTIFY_OK`, `NOTIFY_BAD`, 或 `NOTIFY_STOP` 中的一个值，这些值定义在 `include/linux/notifier.h` 中。

- `NOTIFY_DONE` 和 `NOTIFY_OK` 对后续处理没有影响。
- `NOTIFY_BAD` 作为对 `MEM_GOING_ONLINE`, `MEM_GOING_OFFLINE`, `MEM_ONLINE`, 或 `MEM_OFFLINE` 动作的响应来取消热插拔。它会停止通知队列的进一步处理。
- `NOTIFY_STOP` 停止通知队列的进一步处理。

### 内部锁定

当添加/移除使用内存块设备（即普通RAM）的内存时，应持有 `device_hotplug_lock` 以实现以下目的：

- 同步在线/离线请求（例如，通过sysfs）。这样，只有在内存完全添加后，用户空间才能访问内存块设备（.online/.state属性）。在移除内存时，我们知道没有人处于关键部分。
- 同步CPU热插拔和类似操作（例如，对于ACPI和PPC很重要）。

特别地，存在一种可能的锁倒置情况，通过使用 `device_hotplug_lock` 添加内存时可以避免这种情况，如果用户空间尝试比预期更快地将内存上线：

- `device_online()` 首先获取 `device_lock()`，然后是 `mem_hotplug_lock`。
- `add_memory_resource()` 首先获取 `mem_hotplug_lock`，然后是 `device_lock()`（在创建设备期间，即在 `bus_add_device()` 调用期间）。
由于在获取 `device_lock()` 之前设备对用户空间可见，这可能会导致锁倒置的问题。

内存的上线/下线操作应通过 `device_online()/device_offline()` 进行 —— 确保这些操作与通过 sysfs 的动作同步。建议持有 `device_hotplug_lock`（例如，为了保护 `online_type`）。

在添加/移除/上线/下线内存或添加/移除异构/设备内存时，我们应该始终以写模式持有 `mem_hotplug_lock` 来串行化内存热插拔（例如，访问全局/区域变量）。

此外，与 `device_hotplug_lock` 不同的是，`mem_hotplug_lock` 的读模式允许实现一个较为高效的 `get_online_mems/put_online_mems`，因此访问内存的代码可以防止该内存消失。
