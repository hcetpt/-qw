### 密钥请求服务

### 

密钥请求服务是密钥保留服务的一部分（参见 `Documentation/security/keys/core.rst`）。本文档更详细地解释了请求算法的工作原理。

该过程从内核或用户空间调用 `request_key*()` 开始：

```c
struct key *request_key(const struct key_type *type,
                        const char *description,
                        const char *callout_info);
```

或者：

```c
struct key *request_key_tag(const struct key_type *type,
                            const char *description,
                            const struct key_tag *domain_tag,
                            const char *callout_info);
```

或者：

```c
struct key *request_key_with_auxdata(const struct key_type *type,
                                     const char *description,
                                     const struct key_tag *domain_tag,
                                     const char *callout_info,
                                     size_t callout_len,
                                     void *aux);
```

或者：

```c
struct key *request_key_rcu(const struct key_type *type,
                            const char *description,
                            const struct key_tag *domain_tag);
```

或者通过用户空间调用 `request_key` 系统调用：

```c
key_serial_t request_key(const char *type,
                         const char *description,
                         const char *callout_info,
                         key_serial_t dest_keyring);
```

不同接口的主要区别在于内核接口不需要将密钥链接到密钥环以防止其立即被销毁。内核接口直接返回指向密钥的指针，由调用者负责销毁密钥。

`request_key_tag()` 调用类似于内核中的 `request_key()` 调用，但还接受一个域标签，允许按命名空间分离密钥并成组删除它们。

`request_key_with_auxdata()` 调用类似于 `request_key_tag()` 调用，但允许传递辅助数据给上层调用者（默认为 NULL）。这仅对定义了自己的上层调用机制的密钥类型有用，而不是使用 `/sbin/request-key`。

`request_key_rcu()` 调用类似于 `request_key_tag()` 调用，但它不检查正在构建的密钥，也不尝试构造缺失的密钥。

用户空间接口将密钥链接到与进程关联的密钥环以防止密钥消失，并将密钥的序列号返回给调用者。

以下示例假设涉及的密钥类型没有定义自己的上层调用机制。如果它们定义了，则应将其替换为 `/sbin/request-key` 的 fork 和执行。

### 过程

请求按照以下方式进行：

1. 进程 A 调用 `request_key()`（用户空间系统调用调用内核接口）。
2. `request_key()` 搜索进程订阅的密钥环以查看是否存在合适的密钥。如果存在，则返回该密钥；如果不存在，并且 `callout_info` 未设置，则返回错误。否则，进程继续下一步。
3. `request_key()` 发现 A 尚未拥有所需的密钥，因此创建两个东西：

   a. 创建一个未实例化的密钥 U，具有请求的类型和描述。
b) 授权密钥 V，该密钥引用密钥 U 并指出进程 A 是密钥 U 应实例化和保护的上下文，并且可以从其中满足相关的密钥请求。

4) request_key() 然后进行 fork 并以包含指向授权密钥 V 的链接的新会话密钥环执行 /sbin/request-key。

5) /sbin/request-key 假设与密钥 U 相关的权限。

6) /sbin/request-key 执行适当的程序来实际实例化密钥。

7) 该程序可能需要访问来自进程 A 上下文中的另一个密钥（例如 Kerberos TGT 密钥）。它只需请求相应的密钥，密钥环搜索会注意到会话密钥环在其最底层有授权密钥 V。这将允许它像进程 A 一样搜索进程 A 的密钥环，使用进程 A 的 UID、GID、组和安全信息，并找到密钥 W。

8) 程序然后执行必要的操作以获取用于实例化密钥 U 的数据，使用密钥 W 作为参考（可能是使用 TGT 联系 Kerberos 服务器），然后实例化密钥 U。

9) 在实例化密钥 U 后，授权密钥 V 自动被撤销，使其无法再次使用。

10) 程序随后退出状态码为 0，request_key() 删除密钥 V 并将密钥 U 返回给调用者。

这种机制还可以进一步扩展。如果密钥 W（如步骤 7 中所述）不存在，则会创建未实例化的密钥 W，并创建另一个授权密钥（X）（如步骤 3 所述），并启动另一个 /sbin/request-key 的副本（如步骤 4 所述）。但是，由授权密钥 X 指定的上下文仍然是进程 A，就像在授权密钥 V 中一样。
这是因为进程 A 的密钥环不能简单地在适当的位置附加到 `/sbin/request-key`，原因是（a）`execve` 会丢弃其中的两个密钥环，以及（b）它要求整个过程中具有相同的 UID/GID/用户组。

否定实例化和拒绝
=================

与其实例化一个密钥，授权密钥的持有者可以对正在构建中的密钥进行否定实例化。
这是一个短时占位符，导致在该密钥存在期间的任何重新请求操作都会以 ENOKEY 错误失败（如果被否定），或指定的错误（如果被拒绝）。
提供这一功能是为了防止反复生成 `/sbin/request-key` 进程来尝试获取一个永远无法获得的密钥。
如果 `/sbin/request-key` 进程退出状态码不是 0 或者因信号而终止，则正在构建中的密钥将自动进行短时间的否定实例化。

搜索算法
========

对特定密钥环的搜索按照以下方式进行：

1. 当密钥管理代码搜索一个密钥（使用 `keyring_search_rcu` 函数）时，首先会对开始的密钥环调用 `key_permission(SEARCH)`。如果这个调用拒绝权限，则不再进一步搜索。
2. 它会考虑该密钥环内的所有非密钥环类型的密钥。如果任何密钥匹配指定的标准，则对该密钥调用 `key_permission(SEARCH)` 来查看是否允许找到该密钥。如果允许，则返回该密钥；如果不允许，则继续搜索，并保留优先级更高的错误码（如果有的话）。
3. 然后它会考虑当前搜索的密钥环内的所有密钥环类型的密钥。对每个密钥环调用 `key_permission(SEARCH)`，如果授予了权限，则递归执行步骤（2）和（3）。

一旦找到一个具有使用权限的有效密钥，过程立即停止。之前匹配尝试中的任何错误都被忽略，并返回找到的密钥。

当调用 `request_key()` 时，如果配置项 `CONFIG_KEYS_REQUEST_CACHE=y` 被启用，则首先检查每个任务的单密钥缓存是否存在匹配项。
当 `search_process_keyrings()` 被调用时，它会依次执行以下搜索，直到成功为止：

1. 如果存在，则搜索进程的线程密钥环。
2. 如果存在，则搜索进程的进程密钥环。
3. 搜索进程的会话密钥环。
4. 如果进程已获得与 `request_key()` 授权密钥相关的权限，则：

   a. 如果存在，则搜索调用进程的线程密钥环。
   b. 如果存在，则搜索调用进程的进程密钥环。
   c. 搜索调用进程的会话密钥环。

一旦某次搜索成功，所有待处理的错误将被丢弃，并返回找到的密钥。如果 `CONFIG_KEYS_REQUEST_CACHE=y`，则该密钥将被放入每个任务的缓存中，替换之前的密钥。在退出或恢复用户空间之前，缓存会被清除。

只有在所有这些搜索都失败的情况下，整个操作才会以最高优先级的错误失败。请注意，可能有多个错误来自 LSM（安全模块）。

错误的优先级如下：

- EKEYREVOKED > EKEYEXPIRED > ENOKEY

EACCES/EPERM 只有在直接搜索某个特定密钥环且基础密钥环未授予搜索权限时才会返回。
