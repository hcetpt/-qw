### 密钥请求服务

密钥请求服务是密钥保留服务的一部分（参见
[Documentation/security/keys/core.rst]）。本文档更详细地解释了请求算法的工作原理。

流程从以下几种方式开始：

- 内核通过调用 `request_key*()` 请求一项服务：

```c
struct key *request_key(const struct key_type *type,
                        const char *description,
                        const char *callout_info);
```

或

```c
struct key *request_key_tag(const struct key_type *type,
                            const char *description,
                            const struct key_tag *domain_tag,
                            const char *callout_info);
```

或

```c
struct key *request_key_with_auxdata(const struct key_type *type,
                                     const char *description,
                                     const struct key_tag *domain_tag,
                                     const char *callout_info,
                                     size_t callout_len,
                                     void *aux);
```

或

```c
struct key *request_key_rcu(const struct key_type *type,
                            const char *description,
                            const struct key_tag *domain_tag);
```

- 用户空间调用 `request_key` 系统调用：

```c
key_serial_t request_key(const char *type,
                         const char *description,
                         const char *callout_info,
                         key_serial_t dest_keyring);
```

不同接口的主要区别在于内核接口不需要将密钥链接到密钥环以防止它被立即销毁。内核接口直接返回指向密钥的指针，由调用者负责销毁该密钥。

`request_key_tag()` 调用类似于内核中的 `request_key()`，但还接受一个域标签，这允许密钥按命名空间分离，并且可以作为一个组进行销毁。

`request_key_with_auxdata()` 调用类似于 `request_key_tag()`，但允许传递辅助数据给上层调用者（默认为 NULL）。这仅对那些定义了自己的上层调用机制而非使用 `/sbin/request-key` 的密钥类型有用。

`request_key_rcu()` 调用类似于 `request_key_tag()`，但它不检查正在构建中的密钥，也不尝试构造缺失的密钥。

用户空间接口将密钥链接到与进程关联的密钥环以防止密钥消失，并向调用者返回密钥的序列号。

### 过程

请求过程如下：

1. 进程 A 调用 `request_key()`（用户空间系统调用调用内核接口）。
2. `request_key()` 搜索进程订阅的密钥环以查看是否有合适的密钥。如果有，则返回该密钥；如果没有，且 `callout_info` 未设置，则返回错误。否则，进程进入下一步。
3. `request_key()` 发现 A 尚未拥有所需的密钥，因此创建以下两项：

   a) 创建一个未实例化的密钥 U，类型和描述符如请求所示。
b) 授权密钥V，该密钥指向密钥U，并指出进程A是密钥U应当实例化和保护的上下文环境，以及从中可以满足关联密钥请求的环境。
4) request_key()随后进行分叉并执行/sbin/request-key，使用包含指向授权密钥V链接的新会话密钥环。
5) /sbin/request-key承担与密钥U相关联的权限。
6) /sbin/request-key执行适当的程序来实际完成实例化工作。
7) 该程序可能希望访问来自A上下文中的另一个密钥（例如Kerberos TGT密钥）。它只需请求相应的密钥，而密钥环搜索注意到会话密钥环在其最低级别包含授权密钥V。
这将允许它以如同自身就是进程A一样，使用进程A的UID、GID、组和安全信息来搜索进程A的密钥环，并找到密钥W。
8) 程序然后根据需要获取用于实例化密钥U的数据，使用密钥W作为参考（也许它会使用TGT联系Kerberos服务器），然后实例化密钥U。
9) 在实例化密钥U之后，授权密钥V自动被撤销，因此不能再次使用。
10) 程序随后退出状态码为0，request_key()删除密钥V并将密钥U返回给调用者。

这一过程还可以进一步扩展。如果密钥W（步骤7）不存在，则会创建未实例化的密钥W，同时创建另一个授权密钥（X）（如步骤3所述），并启动另一个/sbin/request-key的副本（如步骤4所述）；但是由授权密钥X指定的上下文仍然为进程A，就像在授权密钥V中一样。
这是因为无法简单地将进程A的密钥环连接到 `/sbin/request-key` 的适当位置，原因有二：(a) `execve` 将会丢弃其中两个密钥环；(b) 它要求从头至尾具有相同的UID/GID/用户组。

### 负面实例化与拒绝

#### 

与其实例化一个密钥，授权密钥的所有者可以对正在构建中的密钥进行负面实例化。这是一个短暂存在的占位符，当它存在时，任何尝试重新请求该密钥的操作都会因为被否定而返回错误 `ENOKEY` 或者如果被拒绝则返回指定的错误。
这主要是为了防止对于永远无法获取的密钥反复启动 `/sbin/request-key` 进程。
如果 `/sbin/request-key` 进程以非0值退出或因信号而终止，则正在构建中的密钥将自动被负面实例化一段时间。

### 密钥搜索算法

对特定密钥环的搜索按照以下方式进行：

1) 当密钥管理代码搜索密钥（通过 `keyring_search_rcu`）时，首先会对开始搜索的密钥环调用 `key_permission(SEARCH)`，如果这一步拒绝了权限，则不再进行进一步的搜索。

2) 接下来考虑该密钥环内的所有非密钥环类型的密钥，如果任何密钥符合指定的标准，则调用 `key_permission(SEARCH)` 来判断是否允许找到该密钥。如果允许，则返回该密钥；如果不允许，则继续搜索，并且如果当前设置的错误优先级更高则保留该错误码。

3) 然后考虑当前搜索密钥环中的所有密钥环类型密钥。对每个密钥环调用 `key_permission(SEARCH)`，如果这授予了权限，则递归执行步骤 (2) 和 (3) 在那个密钥环上。

一旦找到一个有效的、被允许使用的密钥，搜索过程立即停止。之前匹配尝试中的任何错误都会被丢弃，并返回找到的密钥。

当调用 `request_key()` 时，如果配置 `CONFIG_KEYS_REQUEST_CACHE=y`，则首先检查每个任务的单密钥缓存是否存在匹配项。
当调用 `search_process_keyrings()` 时，它会执行以下搜索，直到某一项成功：

1) 如果存在，则搜索进程的线程密钥环
2) 如果存在，则搜索进程的进程密钥环
3) 搜索进程的会话密钥环
4) 如果进程已获得与 `request_key()` 授权密钥相关的权限，则：

    a) 如果存在，则搜索调用进程的线程密钥环
    b) 如果存在，则搜索调用进程的进程密钥环
    c) 搜索调用进程的会话密钥环

一旦搜索成功，所有待处理的错误都会被忽略，并返回找到的密钥。如果配置了 `CONFIG_KEYS_REQUEST_CACHE=y`，则该密钥将被放入每个任务的缓存中，替换之前的密钥。在退出或恢复用户空间之前清理缓存。

只有当上述所有尝试都失败时，整个操作才会以最高优先级的错误失败。需要注意的是，一些错误可能来自安全模块（LSM）。
错误的优先级如下：

`EKEYREVOKED > EKEYEXPIRED > ENOKEY`

`EACCES` 或 `EPERM` 只有在直接搜索特定密钥环且基础密钥环未授予搜索权限的情况下返回。
