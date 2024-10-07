### 密钥请求服务

#### 密钥请求服务

密钥请求服务是密钥保留服务的一部分（参见 `Documentation/security/keys/core.rst`）。本文档详细解释了请求算法的工作原理。

过程从内核或用户空间开始，通过调用 `request_key*()` 函数：

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

或者由用户空间调用 `request_key` 系统调用：

```c
key_serial_t request_key(const char *type,
                         const char *description,
                         const char *callout_info,
                         key_serial_t dest_keyring);
```

主要的区别在于内核接口不需要将密钥链接到密钥环以防止其立即被销毁。内核接口直接返回指向密钥的指针，并由调用者负责销毁密钥。

`request_key_tag()` 调用类似于内核中的 `request_key()`，但还接受一个域标签，允许按命名空间分隔密钥并批量销毁。

`request_key_with_auxdata()` 调用类似于 `request_key_tag()` 调用，但允许传递辅助数据给上层调用者（默认为 NULL）。这仅对那些定义了自己的上层调用机制而非使用 `/sbin/request-key` 的密钥类型有用。

`request_key_rcu()` 调用类似于 `request_key_tag()` 调用，但不检查正在构建的密钥，也不尝试构造缺失的密钥。

用户空间接口将密钥链接到与进程相关的密钥环以防止密钥消失，并将密钥的序列号返回给调用者。

以下示例假设涉及的密钥类型没有定义自己的上层调用机制。如果它们定义了，则应替换 `/sbin/request-key` 的派生和执行。

#### 过程

请求按照以下方式进行：

1. 进程 A 调用 `request_key()`（用户空间系统调用调用内核接口）。
2. `request_key()` 搜索进程订阅的密钥环，查看是否存在合适的密钥。如果存在，则返回该密钥；如果不存在且 `callout_info` 未设置，则返回错误。否则，进程进入下一步。
3. `request_key()` 发现 A 尚未拥有所需的密钥，因此创建两件事：

   a. 创建一个未实例化的密钥 U，类型和描述如请求所示。
b) 授权密钥 V 指向密钥 U，并指出进程 A 是密钥 U 应该实例化和保护的上下文，且可以从该上下文中满足相关的密钥请求。

4) request_key() 然后进行 fork 并以包含指向授权密钥 V 的链接的新会话密钥环执行 /sbin/request-key。

5) /sbin/request-key 假设与密钥 U 相关的权限。

6) /sbin/request-key 执行一个适当的程序来完成实际的实例化操作。

7) 该程序可能希望访问来自 A 上下文中的另一个密钥（例如 Kerberos TGT 密钥）。它只需请求相应的密钥，密钥环搜索会注意到会话密钥环在其最底层包含授权密钥 V。
这将允许其像进程 A 一样使用进程 A 的 UID、GID、组和安全信息搜索进程 A 的密钥环，并找到密钥 W。

8) 程序然后根据需要获取用于实例化密钥 U 的数据，使用密钥 W 作为参考（可能是使用 TGT 联系 Kerberos 服务器），然后实例化密钥 U。

9) 在实例化密钥 U 后，授权密钥 V 将自动被撤销，使其无法再次使用。

10) 程序随后退出并返回 0，request_key() 删除密钥 V 并将密钥 U 返回给调用者。

这种情况还可以进一步扩展。如果密钥 W（第 7 步）不存在，则会创建未实例化的密钥 W，并创建另一个授权密钥（X）（如第 3 步所述），然后生成另一个 /sbin/request-key 的副本（如第 4 步所述）；但由授权密钥 X 指定的上下文仍然是进程 A，就像授权密钥 V 一样。
这是因为进程 A 的密钥环不能简单地在适当的位置附加到 `/sbin/request-key`，原因是（a）`execve` 会丢弃其中的两个，（b）它要求整个过程中具有相同的 UID/GID/用户组。

否定实例化与拒绝
=================

与其实例化一个密钥，授权密钥的持有者可以选择否定实例化一个正在构建中的密钥。
这是一个短时占位符，会在其存在期间导致任何重新请求该密钥的操作失败，并返回错误 `ENOKEY`（如果被否定）或指定的错误码（如果被拒绝）。
这一机制是为了防止对一个永远无法获取的密钥反复生成 `/sbin/request-key` 进程。
如果 `/sbin/request-key` 进程退出状态码不是 0 或者因信号而终止，则正在构建中的密钥将自动被否定实例化一段时间。

搜索算法
========

对特定密钥环的搜索按照以下方式进行：

1. 当密钥管理代码搜索密钥（使用 `keyring_search_rcu` 函数）时，首先会对起始的密钥环调用 `key_permission(SEARCH)`。如果这个操作拒绝权限，则不再继续搜索。
2. 它会考虑该密钥环内的所有非密钥环类型的密钥。如果任何密钥符合指定的标准，则对该密钥调用 `key_permission(SEARCH)` 以查看是否允许找到该密钥。如果允许，则返回该密钥；如果不允许，则继续搜索，并保留优先级更高的错误码。
3. 然后它会考虑当前搜索的密钥环内的所有密钥环类型的密钥。对每个密钥环调用 `key_permission(SEARCH)`，如果允许权限，则递归执行步骤（2）和（3）。

一旦找到一个允许使用的有效密钥，搜索立即停止。之前匹配尝试产生的任何错误都会被丢弃，并返回找到的密钥。

当调用 `request_key()` 时，如果配置项 `CONFIG_KEYS_REQUEST_CACHE=y`，则首先检查每个任务的一个密钥缓存以查找匹配项。
当调用 `search_process_keyrings()` 时，它会执行以下搜索直到某一项成功：

1. 如果存在，则搜索进程的线程密钥环。
2. 如果存在，则搜索进程的进程密钥环。
3. 搜索进程的会话密钥环。
4. 如果进程已经获得了与 `request_key()` 授权密钥相关的权限，则：

   a. 如果存在，则搜索调用进程的线程密钥环。
   b. 如果存在，则搜索调用进程的进程密钥环。
   c. 搜索调用进程的会话密钥环。

一旦某一项搜索成功，所有待处理的错误都会被丢弃，并返回找到的密钥。如果 `CONFIG_KEYS_REQUEST_CACHE=y`，则将该密钥放入每个任务的缓存中，替换之前的密钥。在退出或重新恢复用户空间之前，缓存会被清空。

只有当所有这些搜索都失败时，整个操作才会以最高优先级的错误失败。需要注意的是，可能有多个错误来自 LSM（安全模块）。

错误优先级如下：

`EKEYREVOKED > EKEYEXPIRED > ENOKEY`

`EACCES` 或 `EPERM` 只有在直接搜索特定密钥环且基础密钥环未授予搜索权限的情况下才会返回。
