============================
内核密钥保留服务
============================

此服务允许加密密钥、身份验证令牌、跨域用户映射等被缓存在内核中，供文件系统和其他内核服务使用。
密钥环是允许使用的；这是一种特殊的密钥类型，可以持有指向其他密钥的链接。每个进程都有三个标准的密钥环订阅，内核服务可以搜索这些订阅以查找相关的密钥。
通过启用以下选项来配置密钥服务：

    "安全选项"/"启用密钥保留支持" (CONFIG_KEYS)

本文档包含以下部分：

.. contents:: :local:


密钥概述
============

在此上下文中，密钥表示加密数据单元、身份验证令牌、密钥环等。在内核中，它们由 `struct key` 表示。
每个密钥有多个属性：

    - 一个序列号
    - 一个类型
    - 一个描述（用于在搜索中匹配密钥）
    - 访问控制信息
    - 过期时间
    - 有效载荷
    - 状态
* 每个密钥都会被分配一个类型为 `key_serial_t` 的序列号，在该密钥的生命周期内是唯一的。所有序列号都是正的非零32位整数。
用户空间程序可以使用密钥的序列号作为访问它的方法，但需经过权限检查。

* 每个密钥都有一个定义好的“类型”。这些类型必须由内核服务（如文件系统）在内核中注册后，才能添加或使用该类型的密钥。用户空间程序不能直接定义新的类型。
密钥类型在内核中由 `struct key_type` 表示。这定义了可以对该类型密钥执行的一系列操作。
如果某个类型从系统中移除，所有该类型的密钥将失效。

* 每个密钥都有一个描述。这应该是一个可打印的字符串。密钥类型提供了一个操作来匹配密钥描述和标准字符串。

* 每个密钥都有一个拥有者用户ID、一个组ID和一个权限掩码。这些用于控制用户空间中的进程对密钥的操作权限，以及内核服务是否能够找到该密钥。

* 每个密钥可以通过其类型实例化函数设置在特定时间过期。密钥也可以是永生的。

* 每个密钥可以有一个负载。这个负载表示实际的“密钥”数据。在密钥环的情况下，这是密钥环链接的一系列密钥列表；在用户定义的密钥情况下，它是一段任意的数据。
拥有负载不是必需的；实际上，负载可以只是存储在 `struct key` 中的一个值。
当一个密钥被实例化时，会调用该密钥类型的实例化函数，并传入一段数据，从而以某种方式创建密钥的有效载荷。
同样地，当用户空间请求读取密钥的内容（如果被允许）时，会调用另一个密钥类型的操作，将密钥的附带有效载荷转换回一段数据。

每个密钥可以处于以下几种基本状态之一：

- 未实例化。密钥存在，但没有附加任何数据。从用户空间请求的密钥将处于这种状态。
- 实例化。这是正常状态。密钥是完全形成的，并且有数据附加。
- 负状态。这是一个相对短暂的状态。密钥作为标记，表示对用户空间的前一次调用失败，并作为密钥查找的节流机制。负状态的密钥可以更新为正常状态。
- 过期。密钥可以设置生命周期。如果其生命周期超出，则进入此状态。过期的密钥可以更新回正常状态。
- 吊销。密钥通过用户空间操作被置于这种状态。无法找到或操作它（除了解除链接）。
- 无效。密钥的类型被注销，因此密钥现在无用。

最后三种状态的密钥将被垃圾回收。详见“垃圾回收”部分。
关键服务概述
====================

除了提供密钥外，关键服务还包含以下特性：

  * 关键服务定义了三种特殊的密钥类型：
    (+) "密钥环（keyring）"

      密钥环是一种特殊的密钥，其中包含其他密钥的列表。可以使用各种系统调用来修改密钥环列表。创建时不应为密钥环指定有效负载。
    (+) "用户（user）"

      这种类型的密钥具有描述和任意数据块的有效负载。这些密钥可以在用户空间中创建、更新和读取，并不打算由内核服务使用。
    (+) "登录（logon）"

      类似于“用户”密钥，“登录”密钥也具有任意数据块的有效负载。其设计目的是存储对内核可访问但对用户空间程序不可见的秘密。
      描述可以是任意的，但必须以一个非空字符串开头，该字符串描述了密钥的“子类”。子类与描述的其余部分之间用':'分隔。“登录”密钥可以从用户空间创建和更新，但其有效负载只能从内核空间读取。
* 每个进程订阅三个密钥环：线程特定密钥环、进程特定密钥环和会话特定密钥环。
  线程特定密钥环在发生任何克隆、fork、vfork或execve时会被子进程丢弃。只有在需要时才会创建新的密钥环。
  进程特定密钥环在进行克隆、fork、vfork时（除非提供了CLONE_THREAD标志，否则会共享）会被替换为空的密钥环。execve也会丢弃当前进程的进程特定密钥环并创建一个新的。
  会话特定密钥环在克隆、fork、vfork甚至执行set-UID或set-GID二进制文件时都保持不变。但是，进程可以通过使用PR_JOIN_SESSION_KEYRING来替换其当前的会话密钥环。允许请求匿名的新密钥环，或者尝试创建或加入具有特定名称的密钥环。
  当线程的真实UID和GID发生变化时，线程密钥环的所有权也会随之改变。
* 系统中的每个用户ID持有两个特殊的密钥环：用户特定密钥环和默认用户会话密钥环。默认会话密钥环初始化时链接到用户特定密钥环。
当一个进程更改其实际的用户ID（UID）时，如果它之前没有会话密钥，则会被订阅到新UID的默认会话密钥。
如果一个进程尝试访问其会话密钥但没有密钥，则会被订阅到当前UID的默认会话密钥。
每个用户有两个配额来追踪他们拥有的密钥。一个限制了总的密钥和密钥环的数量，另一个限制了可以消耗的描述和有效载荷空间总量。
用户可以通过procfs文件查看这些信息和其他统计数据。root用户也可以通过sysctl文件修改配额限制（参见“新的procfs文件”部分）。
特定于进程和特定于线程的密钥环不计入用户的配额。
如果某个系统调用以某种方式修改了一个密钥或密钥环，并且会导致用户超出配额，则该操作将被拒绝，并返回错误EDQUOT。
有一个系统调用接口，允许用户空间程序创建和管理密钥及密钥环。
有一个内核接口，允许服务注册类型并搜索密钥。
有一种方法可以让内核中的搜索回调到用户空间，请求在进程的密钥环中找不到的密钥。
还有一个可选的文件系统，通过它可以查看和操作密钥数据库。
### 密钥访问权限

密钥具有一个所有者用户ID、一个组访问ID和一个权限掩码。掩码最多可以为持有者、用户、组和其他访问设置8位。每组8位中只有6位是定义好的。这些授予的权限包括：

- **查看**

    这允许查看密钥或密钥环的属性，包括密钥类型和描述。

- **读取**

    这允许查看密钥的有效载荷或密钥环中的链接密钥列表。

- **写入**

    这允许实例化或更新密钥的有效载荷，或者允许向密钥环添加或移除链接。

- **搜索**

    这允许搜索密钥环并找到密钥。搜索只能递归到设置了搜索权限的嵌套密钥环。

- **链接**

    这允许将密钥或密钥环进行链接。要从密钥环创建到密钥的链接，进程必须对密钥环具有写入权限，并且对密钥具有链接权限。

- **设置属性**

    这允许更改密钥的UID、GID和权限掩码。对于更改所有权、组ID或权限掩码，拥有密钥的所有权或具有系统管理员能力就足够了。

### SELinux支持

安全类“key”已被添加到SELinux中，以便可以在不同上下文中创建密钥时应用强制访问控制。此支持目前是初步的，预计在不久的将来会有显著变化。
目前，所有上述的基本权限在SELinux中也提供了；SELinux只是在执行完所有基本权限检查后被调用。
文件`/proc/self/attr/keycreate`的内容会影响新创建的密钥的标签。如果该文件的内容对应于一个SELinux安全上下文，则密钥将被分配该上下文。否则，密钥将被分配请求创建密钥的任务当前的上下文。任务必须被明确授权使用密钥安全类中的“create”权限来为新创建的密钥分配特定的上下文。
默认密钥环与用户关联时，只有在登录程序被适当地配置以在登录过程中正确初始化keycreate的情况下，才会被标记为用户的默认上下文。否则，它们将被标记为登录程序本身的上下文。
然而，请注意，与root用户关联的默认密钥环被标记为默认内核上下文，因为它们是在引导过程早期创建的，在root有机会登录之前。
与新线程关联的密钥环分别被标记为其关联线程的上下文，并且会话和进程密钥环也类似处理。

新的ProcFS文件
=================

已向ProcFS中添加了两个文件，管理员可以通过这些文件了解密钥服务的状态：

  *  /proc/keys

     这个文件列出了当前可由读取该文件的任务查看的密钥，并提供有关其类型、描述和权限的信息。
     虽然无法通过这种方式查看密钥的有效负载，但可能会提供一些关于它的信息。
     列表中包含的唯一密钥是那些授予读取进程查看权限的密钥，无论它是否拥有它们。请注意，LSM安全检查仍然执行，并可能进一步过滤掉当前进程无权查看的密钥。
     文件内容如下所示：

```
SERIAL   FLAGS  USAGE EXPY PERM     UID   GID   TYPE      DESCRIPTION: SUMMARY
00000001 I-----    39 perm 1f3f0000     0     0 keyring   _uid_ses.0: 1/4
00000002 I-----     2 perm 1f3f0000     0     0 keyring   _uid.0: empty
00000007 I-----     1 perm 1f3f0000     0     0 keyring   _pid.1: empty
0000018d I-----     1 perm 1f3f0000     0     0 keyring   _pid.412: empty
000004d2 I--Q--     1 perm 1f3f0000    32    -1 keyring   _uid.32: 1/4
000004d3 I--Q--     3 perm 1f3f0000    32    -1 keyring   _uid_ses.32: empty
00000892 I--QU-     1 perm 1f000000     0     0 user      metal:copper: 0
00000893 I--Q-N     1  35s 1f3f0000     0     0 user      metal:silver: 0
00000894 I--Q--     1  10h 003f0000     0     0 user      metal:gold: 0
```

     标记解释如下：

- I：已实例化
- R：已撤销
- D：已死亡
- Q：计入用户的配额
- U：正在通过回调到用户空间构建
- N：否定密钥

  *  /proc/key-users

     此文件列出了系统上至少有一个密钥的每个用户的跟踪数据。此类数据包括配额信息和统计信息：

```
[root@andromeda root]# cat /proc/key-users
0:     46 45/45 1/100 13/10000
29:     2 2/2 2/100 40/10000
32:     2 2/2 2/100 40/10000
38:     2 2/2 2/100 40/10000
```

     每行的格式如下：

- `<UID>`：此用户ID适用的用户
- `<usage>`：结构引用计数
- `<inst>/<keys>`：密钥总数和已实例化的数量
- `<keys>/<max>`：密钥计数配额
- `<bytes>/<max>`：密钥大小配额

为了控制密钥的配额限制，还添加了四个新的sysctl文件：

  *  /proc/sys/kernel/keys/root_maxkeys
     /proc/sys/kernel/keys/root_maxbytes

     这些文件保存了root可以拥有的最大密钥数量以及root可以在这些密钥中存储的最大字节数量。
  *  /proc/sys/kernel/keys/maxkeys
     /proc/sys/kernel/keys/maxbytes

     这些文件保存了每个非root用户可以拥有的最大密钥数量以及每个用户可以在其密钥中存储的最大字节数量。
root可以通过将每个新限制作为十进制数字字符串写入相应的文件来更改这些限制。

用户空间系统调用接口
===============================

用户空间可以通过三个新的系统调用来直接操作密钥：add_key，request_key 和 keyctl。后者提供了多种用于操作密钥的功能。
当直接引用一个密钥时，用户空间程序应使用密钥的序列号（一个32位正整数）。然而，有一些特殊值可用于引用与调用进程相关的特殊密钥和密钥环：

	常量				值	引用的密钥
	==============================	======	===========================
	KEY_SPEC_THREAD_KEYRING		-1	线程特定密钥环
	KEY_SPEC_PROCESS_KEYRING	-2	进程特定密钥环
	KEY_SPEC_SESSION_KEYRING	-3	会话特定密钥环
	KEY_SPEC_USER_KEYRING		-4	UID特定密钥环
	KEY_SPEC_USER_SESSION_KEYRING	-5	UID-会话密钥环
	KEY_SPEC_GROUP_KEYRING		-6	GID特定密钥环
	KEY_SPEC_REQKEY_AUTH_KEY	-7	假设的request_key()授权密钥

主要的系统调用包括：

  * 创建一个指定类型、描述和有效载荷的新密钥，并将其添加到指定的密钥环中：

	key_serial_t add_key(const char *type, const char *desc,
			     const void *payload, size_t plen,
			     key_serial_t keyring);

    如果密钥环中已存在具有相同类型和描述的密钥，则此函数将尝试用给定的有效载荷更新该密钥，或者如果该功能不被密钥类型支持，则返回错误EEXIST。进程还必须具有写入密钥的权限才能更新它。新密钥将授予所有用户权限，而不授予任何组或第三方权限。
    否则，这将尝试创建一个具有指定类型和描述的新密钥，并用提供的有效载荷实例化并将其附加到密钥环。在这种情况下，如果进程没有写入密钥环的权限，将会生成错误。
    如果密钥类型支持，如果描述为NULL或空字符串，密钥类型将尝试从有效载荷的内容生成描述。
    有效载荷是可选的，如果类型不需要，指针可以为NULL。有效载荷大小为plen，plen可以为零表示空有效载荷。
    可以通过设置类型为"keyring"，密钥环名称作为描述（或NULL），并将有效载荷设置为NULL来生成新的密钥环。
    用户定义的密钥可以通过指定类型"user"来创建。建议用户定义的密钥描述前缀加上类型ID和冒号，例如Kerberos 5票证授予票证使用"krb5tgt:"。
    任何其他类型必须由内核服务（如文件系统）提前注册。
    如果成功，返回新创建或更新的密钥的ID。

* 在进程的密钥环中搜索一个密钥，可能调用用户空间来创建它：

	key_serial_t request_key(const char *type, const char *description,
				 const char *callout_info,
				 key_serial_t dest_keyring);

    此函数按线程、进程、会话顺序搜索进程的所有密钥环，寻找匹配的密钥。这非常类似于KEYCTL_SEARCH，包括可选地将发现的密钥附加到密钥环。
    如果找不到密钥，并且callout_info不为NULL，则将调用/sbin/request-key试图获取密钥。callout_info字符串将作为参数传递给程序。
为了将一个密钥链接到目标密钥环中，该密钥必须对调用者授予链接权限，并且密钥环必须授予写入权限。
详见：Documentation/security/keys/request-key.rst

keyctl 系统调用的功能如下：

1. 将一个特殊的密钥ID映射为当前进程的实际密钥ID：

    ```c
    key_serial_t keyctl(KEYCTL_GET_KEYRING_ID, key_serial_t id, int create);
    ```

    根据 "id" 查找指定的特殊密钥（如果需要的话创建该密钥），并返回找到的密钥或密钥环的ID。如果密钥已存在，则返回其ID。

    如果密钥尚未存在，当 "create" 非零时将创建该密钥；如果 "create" 为零，则返回错误 ENOKEY。

2. 替换当前进程订阅的会话密钥环：

    ```c
    key_serial_t keyctl(KEYCTL_JOIN_SESSION_KEYRING, const char *name);
    ```

    如果 name 为 NULL，则创建一个匿名密钥环，并将其作为会话密钥环附加到进程上，替换旧的会话密钥环。

    如果 name 非 NULL，如果存在同名的密钥环，则尝试将其作为会话密钥环进行附加，如果不允许则返回错误；否则创建一个新的同名密钥环，并将其作为会话密钥环进行附加。

    要将进程附加到命名密钥环，该密钥环必须对进程的所有者具有搜索权限。

    成功后返回新的会话密钥环的ID。

3. 更新指定的密钥：

    ```c
    long keyctl(KEYCTL_UPDATE, key_serial_t key, const void *payload, size_t plen);
    ```

    尝试使用给定的负载更新指定的密钥，如果该功能不被密钥类型支持，则返回错误 EOPNOTSUPP。进程还必须具有写入密钥的权限才能更新它。

    负载长度为 plen，可以为空或不存在，类似于 add_key() 的行为。
* 撤销一个密钥：

```c
long keyctl(KEYCTL_REVOKE, key_serial_t key);
```
这将使密钥无法用于进一步的操作。任何尝试使用该密钥的操作都会遇到错误 `EKEYREVOKED`，并且该密钥将不再可查找。

* 更改密钥的所有权：

```c
long keyctl(KEYCTL_CHOWN, key_serial_t key, uid_t uid, gid_t gid);
```
此函数允许更改密钥的所有者和组ID。`uid` 或 `gid` 中的任何一个可以设置为 `-1` 以抑制该更改。

只有超级用户才能将密钥的所有者更改为当前所有者之外的其他用户。同样地，只有超级用户才能将密钥的组ID更改为调用进程的组ID或其组列表成员之一之外的其他值。

* 更改密钥的权限掩码：

```c
long keyctl(KEYCTL_SETPERM, key_serial_t key, key_perm_t perm);
```
此函数允许密钥的所有者或超级用户更改密钥的权限掩码。
只允许可用的位；如果设置了其他位，则会返回错误 `EINVAL`。

* 描述一个密钥：

```c
long keyctl(KEYCTL_DESCRIBE, key_serial_t key, char *buffer, size_t buflen);
```
此函数在提供的缓冲区中返回密钥属性（但不包括其有效负载数据）的摘要字符串。
除非发生错误，它总是返回能够生成的数据量，即使这些数据超出了缓冲区大小，但它不会将超过请求的部分复制到用户空间。如果缓冲区指针为 `NULL`，则不会进行复制。

要成功调用此函数，进程必须具有查看密钥的权限。
如果成功，会在缓冲区中放置以下格式的字符串：

```
<type>;<uid>;<gid>;<perm>;<description>
```

其中 `type` 和 `description` 是字符串，`uid` 和 `gid` 是十进制数，`perm` 是十六进制数。如果缓冲区足够大，字符串末尾会包含一个空字符（NUL）。

可以通过以下方式解析该字符串：

```c
sscanf(buffer, "%[^;];%d;%d;%o;%s", type, &uid, &gid, &mode, desc);
```

* 清除密钥环中的密钥：

```c
long keyctl(KEYCTL_CLEAR, key_serial_t keyring);
```
此函数清除与密钥环关联的密钥列表。调用进程必须具有对密钥环的写入权限，并且该密钥环必须是真正的密钥环（否则将导致错误 `ENOTDIR`）。
此功能还可以用于清除特定的内核密钥环，前提是它们被适当地标记，并且用户具有CAP_SYS_ADMIN权限。DNS解析缓存密钥环就是一个例子。

* 将密钥链接到密钥环中 ::

    long keyctl(KEYCTL_LINK, key_serial_t keyring, key_serial_t key);

    此功能在密钥环与密钥之间创建一个链接。进程必须对密钥环有写权限，并且对密钥有链接权限。
    如果密钥环不是真正的密钥环，则会返回错误ENOTDIR；如果密钥环已满，则会返回错误ENFILE。
    链接过程会检查密钥环的嵌套情况，如果嵌套过深则返回ELOOP，如果链接会导致循环则返回EDEADLK。
    密钥环中任何与新密钥类型和描述相匹配的链接将在添加新密钥时被丢弃。

* 将密钥从一个密钥环移动到另一个密钥环 ::

    long keyctl(KEYCTL_MOVE,
                key_serial_t id,
                key_serial_t from_ring_id,
                key_serial_t to_ring_id,
                unsigned int flags);

    将由"id"指定的密钥从由"from_ring_id"指定的密钥环移动到由"to_ring_id"指定的密钥环。如果两个密钥环相同，则不做任何操作。
    "flags"可以设置KEYCTL_MOVE_EXCL标志，如果目标密钥环中存在匹配的密钥，则操作将以EEXIST失败；否则，这样的密钥将被替换。
    要使此功能成功，进程必须对密钥有链接权限，并且对两个密钥环都有写权限。从KEYCTL_LINK产生的任何错误在此处的目标密钥环上也适用。

* 从另一个密钥环中解除密钥或密钥环的链接 ::

    long keyctl(KEYCTL_UNLINK, key_serial_t keyring, key_serial_t key);

    此功能会在密钥环中查找第一个指向指定密钥的链接，并在找到后移除它。随后的链接将被忽略。进程必须对密钥环有写权限。
    如果密钥环不是真正的密钥环，则会返回错误ENOTDIR；如果密钥不存在，则会返回错误ENOENT。
* 在密钥环树中搜索一个密钥：

    ```c
    key_serial_t keyctl(KEYCTL_SEARCH, key_serial_t keyring,
                        const char *type, const char *description,
                        key_serial_t dest_keyring);
    ```

    这个函数会从指定的密钥环开始，在整个密钥环树中搜索符合类型和描述条件的密钥。在递归进入子密钥环之前，每个密钥环都会被检查。

    进程必须对顶层密钥环具有搜索权限，否则将返回错误EACCES。只有进程具有搜索权限的密钥环才会被递归进入，并且只有进程具有搜索权限的密钥和密钥环才能匹配。如果指定的密钥环不是一个真正的密钥环，则返回错误ENOTDIR。

    如果搜索成功，该函数将尝试将找到的密钥链接到提供的目标密钥环（非零ID）。所有适用于`KEYCTL_LINK`的约束在此情况下也适用。

    如果搜索失败，将返回错误ENOKEY、EKEYREVOKED或EKEYEXPIRED。成功时，返回找到的密钥ID。

* 从密钥中读取负载数据：

    ```c
    long keyctl(KEYCTL_READ, key_serial_t key, char *buffer,
                size_t buflen);
    ```

    此函数尝试从指定的密钥中读取负载数据到缓冲区。进程必须对该密钥具有读取权限才能成功。

    返回的数据将由密钥类型进行处理。例如，一个密钥环将返回一个`key_serial_t`数组，表示它订阅的所有密钥的ID。用户定义的密钥类型将直接返回其数据。如果密钥类型未实现此功能，则返回错误EOPNOTSUPP。

    如果指定的缓冲区太小，将返回所需的缓冲区大小。在这种情况下，请注意缓冲区的内容可能以某种未定义的方式被覆盖。

    否则，成功时返回复制到缓冲区的数据量。

* 实例化部分构建的密钥：

    ```c
    long keyctl(KEYCTL_INSTANTIATE, key_serial_t key,
                const void *payload, size_t plen,
                key_serial_t keyring);
    long keyctl(KEYCTL_INSTANTIATE_IOV, key_serial_t key,
                const struct iovec *payload_iov, unsigned ioc,
                key_serial_t keyring);
    ```

    如果内核回调用户空间以完成密钥的实例化，用户空间应使用此调用在被调用进程返回前提供密钥的数据，否则密钥将自动标记为无效。

    进程必须对要实例化的密钥具有写入访问权限，并且该密钥必须尚未实例化。
如果指定了密钥环（非零），密钥也将被链接到该密钥环，但在这种情况下，所有适用于`KEYCTL_LINK`的约束也同样适用。

`payload`和`plen`参数描述了与`add_key()`相同的负载数据。
`payload_iov`和`ioc`参数描述了一个`iovec`数组中的负载数据，而不是单个缓冲区。

* 负实例化部分构造的密钥：

```c
long keyctl(KEYCTL_NEGATE, key_serial_t key,
            unsigned timeout, key_serial_t keyring);
long keyctl(KEYCTL_REJECT, key_serial_t key,
            unsigned timeout, unsigned error, key_serial_t keyring);
```

如果内核回调用户空间以完成密钥的实例化，用户空间应在被调用进程返回之前使用此调用将密钥标记为负实例化，如果无法满足请求的话。
进程必须对要实例化的密钥具有写访问权限，并且该密钥必须是未实例化的。
如果指定了密钥环（非零），密钥也将被链接到该密钥环，但在这种情况下，所有适用于`KEYCTL_LINK`的约束也同样适用。
如果密钥被拒绝，将来对该密钥的搜索将返回指定的错误代码，直到拒绝的密钥过期。否定密钥等同于使用`ENOKEY`作为错误代码来拒绝密钥。

* 设置默认请求密钥的目标密钥环：

```c
long keyctl(KEYCTL_SET_REQKEY_KEYRING, int reqkey_defl);
```

这设置了当前线程隐式请求的密钥将被附加到的默认密钥环。`reqkey_defl`应该是以下常量之一：

| 常量                         | 值   | 新的默认密钥环       |
|------------------------------|------|---------------------|
| `KEY_REQKEY_DEFL_NO_CHANGE`  | -1   | 不改变              |
| `KEY_REQKEY_DEFL_DEFAULT`    | 0    | 默认[1]             |
| `KEY_REQKEY_DEFL_THREAD_KEYRING` | 1 | 线程密钥环           |
| `KEY_REQKEY_DEFL_PROCESS_KEYRING` | 2 | 进程密钥环           |
| `KEY_REQKEY_DEFL_SESSION_KEYRING` | 3 | 会话密钥环           |
| `KEY_REQKEY_DEFL_USER_KEYRING`     | 4 | 用户密钥环           |
| `KEY_REQKEY_DEFL_USER_SESSION_KEYRING` | 5 | 用户会话密钥环       |
| `KEY_REQKEY_DEFL_GROUP_KEYRING`    | 6 | 组密钥环             |

如果成功，将返回旧的默认值；如果`reqkey_defl`不是上述值之一，则返回`EINVAL`错误。
默认密钥环可以通过在`request_key()`系统调用中指示的密钥环覆盖。
请注意，此设置在`fork/exec`时会继承。
[1] 默认顺序是：如果存在，则使用线程密钥环；否则，如果存在，则使用进程密钥环；否则，如果存在，则使用会话密钥环；否则，使用用户默认的会话密钥环。

* 设置密钥的超时时间：

```c
long keyctl(KEYCTL_SET_TIMEOUT, key_serial_t key, unsigned timeout);
```

这将设置或清除一个密钥的超时时间。超时时间可以为0以清除超时时间，或者是一个秒数来设置该密钥在未来某时刻过期的时间。

进程必须对密钥具有属性修改权限才能设置其超时时间。此功能不能用于负值、已撤销或已过期的密钥。

* 假设有权创建密钥：

```c
long keyctl(KEYCTL_ASSUME_AUTHORITY, key_serial_t key);
```

这将假设或取消指定密钥所需的创建权限。只有当线程在其密钥环中拥有与指定密钥关联的授权密钥时，才能假设权限。

一旦假设了权限，搜索密钥时也会使用请求者的安全标签、UID、GID和组来搜索请求者的密钥环。

如果请求的权限不可用，则返回错误EPERM；同样地，如果由于目标密钥已经创建而撤销了权限，也会返回错误EPERM。

如果指定的密钥为0，则取消任何已假设的权限。

假设的授权密钥会在fork和exec过程中继承。

* 获取附加到密钥的LSM安全上下文：

```c
long keyctl(KEYCTL_GET_SECURITY, key_serial_t key, char *buffer, size_t buflen);
```

此函数返回表示附加到密钥的LSM安全上下文的字符串，并将其存储在提供的缓冲区中。

除非出现错误，否则它总是返回能够生成的数据量，即使这些数据量超过了缓冲区大小，但它不会将超过请求的数据复制到用户空间。如果缓冲区指针为NULL，则不会进行任何复制操作。
如果缓冲区足够大，则在字符串末尾包含一个NUL字符。这个字符被包含在返回的计数中。如果没有强制执行LSM（长度-序列号-标记），则会返回一个空字符串。
要使此功能成功，进程必须对键具有查看权限。
* 安装调用进程的会话密钥环到其父进程：

    long keyctl(KEYCTL_SESSION_TO_PARENT);

    此函数尝试将调用进程的会话密钥环安装到调用进程的父进程上，替换父进程当前的会话密钥环。
调用进程必须与其父进程具有相同的拥有者，密钥环必须与调用进程具有相同的拥有者，调用进程必须对密钥环具有LINK权限，并且活动的LSM模块不能拒绝权限，否则将返回错误EPERM。
如果内存不足以完成操作，则返回错误ENOMEM，否则返回0表示成功。
下次父进程离开内核并恢复执行用户空间时，密钥环将被替换。
* 使密钥失效：

    long keyctl(KEYCTL_INVALIDATE, key_serial_t key);

    此函数将一个密钥标记为无效，并唤醒垃圾收集器。垃圾收集器立即将所有无效的密钥从密钥环中移除，并在密钥引用计数降至零时删除该密钥。
被标记为无效的密钥立即对正常的密钥操作不可见，尽管它们在/proc/keys中仍然可见直到被删除（它们会被标记为'i'标志）。
要使此功能成功，进程必须对密钥具有搜索权限。
* 计算Diffie-Hellman共享密钥或公钥：

    long keyctl(KEYCTL_DH_COMPUTE, struct keyctl_dh_params *params,
                char *buffer, size_t buflen, struct keyctl_kdf_params *kdf);

    参数结构体包含三个密钥的序号：

    - 双方都已知的大素数p
    - 本地私钥
    - 基数整数，可以是共享生成元或远程公钥

    计算的结果为：

    result = base ^ private (mod prime)

    如果基数是共享生成元，则结果是本地公钥。如果基数是远程公钥，则结果是共享密钥。
如果参数 `kdf` 为 `NULL`，则适用以下规则：

- 缓冲区长度必须至少等于素数的长度，或者为零。
- 如果缓冲区长度非零，则在成功计算并复制到缓冲区时返回结果的长度。当缓冲区长度为零时，返回所需的最小缓冲区长度。

`kdf` 参数允许调用者对 Diffie-Hellman 计算应用密钥派生函数（KDF），其中仅返回 KDF 的结果。KDF 通过 `struct keyctl_kdf_params` 描述如下：

- `char *hashname` 指定了用于从内核加密 API 中识别所使用的哈希算法的 NUL 终止字符串，并应用于 KDF 操作。KDF 实现符合 SP800-56A 以及 SP800-108（计数器 KDF）。
- `char *otherinfo` 指定了 SP800-56A 第 5.8.1.2 节中所述的 OtherInfo 数据。缓冲区的长度由 `otherinfolen` 给出。OtherInfo 的格式由调用者定义。

如果没有使用 OtherInfo，则 `otherinfo` 指针可以为 `NULL`。

如果密钥类型不受支持，则此函数将返回错误 `EOPNOTSUPP`；如果找不到密钥，则返回错误 `ENOKEY`；如果调用者无法读取密钥，则返回错误 `EACCES`。此外，如果参数 `kdf` 非 `NULL` 并且缓冲区长度或 OtherInfo 长度超过允许长度，则该函数将返回错误 `EMSGSIZE`。

限制密钥环链接::

    long keyctl(KEYCTL_RESTRICT_KEYRING, key_serial_t keyring,
                const char *type, const char *restriction);

现有密钥环可以通过评估密钥的内容来限制附加密钥的链接，根据某种限制方案进行评估。“keyring” 是要施加限制的现有密钥环的密钥 ID。它可以为空，也可以已经包含链接的密钥。即使新的限制会拒绝它们，现有的链接密钥仍保留在密钥环中。
“type” 是注册的密钥类型。
“restriction” 是描述如何限制密钥链接的字符串。
格式根据密钥类型的不同而变化，并将字符串传递给`lookup_restriction()`函数以处理请求的类型。它可能指定了用于限制的方法和相关数据，例如签名验证或对密钥负载的约束。如果请求的密钥类型后来被注销，则在删除该密钥类型后，密钥环中不得添加任何密钥。

要应用密钥环限制，进程必须具有设置属性权限，并且密钥环之前不得受到限制。

受限密钥环的一个应用是使用非对称密钥类型来验证X.509证书链或单个证书签名。

请参阅Documentation/crypto/asymmetric-keys.rst以了解适用于非对称密钥类型的特定限制。

* 查询非对称密钥：

```c
long keyctl(KEYCTL_PKEY_QUERY,
            key_serial_t key_id, unsigned long reserved,
            const char *params,
            struct keyctl_pkey_query *info);
```

获取有关非对称密钥的信息。可以通过`params`参数查询特定算法和编码。这是一个包含键值对的空格或制表符分隔的字符串。
目前支持的键包括`enc`和`hash`。信息返回在`keyctl_pkey_query`结构体中：

```c
__u32	supported_ops;
__u32	key_size;
__u16	max_data_size;
__u16	max_sig_size;
__u16	max_enc_size;
__u16	max_dec_size;
__u32	__spare[10];
```

`supported_ops`包含一个标志位掩码，指示支持的操作。这是通过按位或操作构建的：

`KEYCTL_SUPPORTS_{ENCRYPT,DECRYPT,SIGN,VERIFY}`

`key_size`表示密钥大小（以比特为单位）。

`max_*_size`表示要签名的数据块、签名数据块、要加密的数据块和要解密的数据块的最大大小（以字节为单位）。

`__spare[]`必须设置为0。这打算在未来用于传递解锁密钥所需的一个或多个口令。

如果成功，返回0。如果密钥不是非对称密钥，则返回EOPNOTSUPP。

* 使用非对称密钥加密、解密、签名或验证数据块：

```c
long keyctl(KEYCTL_PKEY_ENCRYPT,
            const struct keyctl_pkey_params *params,
            const char *info,
            const void *in,
            void *out);

long keyctl(KEYCTL_PKEY_DECRYPT,
            const struct keyctl_pkey_params *params,
            const char *info,
            const void *in,
            void *out);

long keyctl(KEYCTL_PKEY_SIGN,
            const struct keyctl_pkey_params *params,
            const char *info,
            const void *in,
            void *out);

long keyctl(KEYCTL_PKEY_VERIFY,
            const struct keyctl_pkey_params *params,
            const char *info,
            const void *in,
            const void *in2);
```

使用非对称密钥对数据块执行公钥密码操作。对于加密和验证，非对称密钥可能只需要公开部分即可，但对于解密和签名，则需要私有部分。
参数块 `params` 包含了多个整数值：

	__s32		key_id;
	__u32		in_len;
	__u32		out_len;
	__u32		in2_len;

`key_id` 是要使用的非对称密钥的 ID。`in_len` 和 `in2_len` 表示输入缓冲区 `in` 和 `in2` 中的数据量，而 `out_len` 表示输出缓冲区 `out` 的大小，适用于上述操作。

对于特定的操作，输入和输出缓冲区的使用如下：

	操作 ID		in, in_len	out, out_len	in2, in2_len
	=======================	===============	===============	===============
	KEYCTL_PKEY_ENCRYPT	原始数据	加密数据	-
	KEYCTL_PKEY_DECRYPT	加密数据	原始数据	-
	KEYCTL_PKEY_SIGN	原始数据	签名	-
	KEYCTL_PKEY_VERIFY	原始数据	-			签名

`info` 是一组键值对字符串，提供补充信息。这些包括：

	`enc=<编码>` 加密/签名块的编码。可以是 "pkcs1" 表示 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5；"pss" 表示 "RSASSA-PSS"；"oaep" 表示 "RSAES-OAEP"。如果省略或为 "raw"，则表示加密函数的原始输出。
	`hash=<算法>` 如果数据缓冲区包含哈希函数的输出，并且编码中包含指示使用了哪种哈希函数的信息，则可以通过此选项指定哈希函数，例如 "hash=sha256"

参数块中的 `__spare[]` 空间必须设置为 0。这主要是为了允许传递解锁密钥所需的口令。

如果成功，加密、解密和签名都会返回写入输出缓冲区的数据量。验证在成功时返回 0。

监视密钥或密钥环的变化：

	long keyctl(KEYCTL_WATCH_KEY, key_serial_t key, int queue_fd,
		    const struct watch_notification_filter *filter);

这将设置或移除对指定密钥或密钥环变化的监视。

`key` 是要监视的密钥的 ID。
`queue_fd` 是指向打开管道的文件描述符，该管道管理接收通知的缓冲区。
`filter` 要么为 NULL 以移除监视，要么是一个过滤器规范，用于指示需要从密钥获取哪些事件。

更多信息请参见 Documentation/core-api/watch_queue.rst。
请注意，对于任何特定的 { key, queue_fd } 组合，只能设置一个监视器。
通知记录的结构如下：

    struct key_notification {
        struct watch_notification watch;
        __u32 key_id;
        __u32 aux;
    };

在此结构中，`watch::type` 将被设置为 "WATCH_TYPE_KEY_NOTIFY"，子类型将是以下之一：

    NOTIFY_KEY_INSTANTIATED
    NOTIFY_KEY_UPDATED
    NOTIFY_KEY_LINKED
    NOTIFY_KEY_UNLINKED
    NOTIFY_KEY_CLEARED
    NOTIFY_KEY_REVOKED
    NOTIFY_KEY_INVALIDATED
    NOTIFY_KEY_SETATTR

这些表示密钥被实例化/拒绝、更新、在密钥环中创建链接、从密钥环中移除链接、清空密钥环、撤销密钥、使密钥失效或更改密钥的一个属性（用户、组、权限、超时时间、限制）。
如果监视的密钥被删除，将发出一个基本的 `watch_notification`，其中 "type" 被设置为 WATCH_TYPE_META，"subtype" 被设置为 `watch_meta_removal_notification`。监视点ID将被设置在 "info" 字段中。
这需要通过启用以下选项来配置：

    "提供密钥/密钥环变更通知"（KEY_NOTIFICATIONS）

内核服务
=========

内核提供的密钥管理服务相对简单。它们可以分为两个领域：密钥和密钥类型。
处理密钥相对直接。首先，内核服务注册其类型，然后搜索该类型的密钥。只要它还需要这个密钥，就应该保留它，之后应该释放它。对于文件系统或设备文件，在打开调用期间可能会执行搜索，并在关闭时释放密钥。如何处理由于两个不同用户打开同一个文件而导致的冲突密钥问题由文件系统作者解决。
要访问密钥管理器，需要包含以下头文件：

    <linux/key.h>

特定的密钥类型应该在 `include/keys/` 目录下有一个相应的头文件，用于访问该类型。例如，对于类型为 "user" 的密钥，应该是：

    <keys/user-type.h>

请注意，可能会遇到两种不同类型的指向密钥的指针：

  *  struct key *

     这只是指向密钥结构本身。密钥结构至少是四字节对齐的。

  *  key_ref_t

     这相当于 `struct key *`，但如果调用者“拥有”该密钥，则最低有效位会被设置。“拥有”意味着调用进程在其一个密钥环上有对该密钥的可搜索链接。有三个函数用于处理这些：

    key_ref_t make_key_ref(const struct key *key, bool possession);

    struct key *key_ref_to_ptr(const key_ref_t key_ref);

    bool is_key_possessed(const key_ref_t key_ref);

     第一个函数根据密钥指针和拥有信息（必须为真或假）构建一个密钥引用。
     第二个函数从引用中获取密钥指针，第三个函数获取拥有标志。
当访问密钥的有效载荷内容时，必须采取某些预防措施以防止访问与修改的竞争条件。更多信息请参阅“访问有效载荷内容注意事项”部分。
*  若要搜索密钥，请调用：

    struct key *request_key(const struct key_type *type,
                            const char *description,
                            const char *callout_info);

    这用于请求一个描述匹配指定描述的密钥或密钥环，根据密钥类型的 `match_preparse()` 方法进行匹配。这允许进行近似匹配。如果 `callout_info` 不为 NULL，则会调用 `/sbin/request-key` 程序试图从用户空间获取密钥。在这种情况下，`callout_info` 将作为参数传递给程序。
如果该函数失败，将会返回错误 `ENOKEY`、`EKEYEXPIRED` 或 `EKEYREVOKED`。
如果成功，密钥将被附加到默认密钥环中，这些密钥是通过 `KEYCTL_SET_REQKEY_KEYRING` 设置的隐式获取请求密钥。
参见 `Documentation/security/keys/request-key.rst`。

* 若要在特定域中查找密钥，请调用：

```c
struct key *request_key_tag(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag,
                            const char *callout_info);
```

这与 `request_key()` 相同，只是可以指定一个域标签，使得搜索算法仅匹配与该标签相匹配的密钥。`domain_tag` 可以为 `NULL`，表示一个与任何指定域分开的全局域。

* 若要查找密钥并传递辅助数据给上层调用者，请调用：

```c
struct key *request_key_with_auxdata(const struct key_type *type,
                                     const char *description,
                                     struct key_tag *domain_tag,
                                     const void *callout_info,
                                     size_t callout_len,
                                     void *aux);
```

这与 `request_key_tag()` 相同，只是如果存在的话，辅助数据会传递给 `key_type->request_key()` 操作，并且 `callout_info` 是长度为 `callout_len` 的数据块（长度可以为 0）。

* 若要在 RCU 条件下查找密钥，请调用：

```c
struct key *request_key_rcu(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag);
```

这类似于 `request_key_tag()`，但不会检查正在构建中的密钥，并且如果找不到匹配项也不会调用用户空间来构建密钥。

* 当不再需要密钥时，应使用以下方法释放它：

```c
void key_put(struct key *key);
```

或者：

```c
void key_ref_put(key_ref_t key_ref);
```

这些方法可以在中断上下文中调用。如果未设置 `CONFIG_KEYS`，则不会解析参数。

* 可以通过调用以下函数之一来增加对密钥的引用：

```c
struct key *__key_get(struct key *key);
struct key *key_get(struct key *key);
```

通过 `key_get()` 引用的密钥需要在使用完毕后通过调用 `key_put()` 来释放。传入的密钥指针将被返回。

对于 `key_get()`，如果指针为 `NULL` 或未设置 `CONFIG_KEYS`，则不会对密钥进行引用，也不会发生递增操作。

* 可以通过调用以下方法来获取密钥的序列号：

```c
key_serial_t key_serial(struct key *key);
```

如果 `key` 为 `NULL` 或未设置 `CONFIG_KEYS`，则返回 0（在这种情况下不会解析参数）。
如果在搜索中找到了密钥环，可以进一步通过以下函数进行搜索：

```c
key_ref_t keyring_search(key_ref_t keyring_ref,
			 const struct key_type *type,
			 const char *description,
			 bool recurse)
```

此函数会搜索指定的密钥环（当 `recurse == false`）或整个密钥环树（当 `recurse == true`），以查找匹配的密钥。如果失败，将返回错误 `ENOKEY`（使用 `IS_ERR/PTR_ERR` 进行判断）。如果成功，则返回的密钥需要被释放。

密钥环引用中的所有权属性用于通过权限掩码控制访问，并且在成功时会被传递给返回的密钥引用指针。

密钥环可以通过以下函数创建：

```c
struct key *keyring_alloc(const char *description, uid_t uid, gid_t gid,
			  const struct cred *cred,
			  key_perm_t perm,
			  struct key_restriction *restrict_link,
			  unsigned long flags,
			  struct key *dest);
```

此函数根据给定的属性创建一个密钥环并返回它。如果 `dest` 不为 `NULL`，新密钥环将链接到其指向的密钥环。不会对目标密钥环进行权限检查。

如果创建的密钥环会超出配额限制，则可能会返回错误 `EDQUOT`（如果密钥环不应计入用户的配额，可以在 `flags` 中传递 `KEY_ALLOC_NOT_IN_QUOTA`）。还可能返回错误 `ENOMEM`。

如果 `restrict_link` 不为 `NULL`，则应指向包含每次尝试链接密钥到新密钥环时都会调用的函数的结构。该结构还可以包含一个密钥指针和一个关联的密钥类型。该函数用于检查是否可以将密钥添加到密钥环。如果给定的密钥类型被注销，该密钥类型将用于垃圾回收清理函数或数据指针。内核中的 `key_create_or_update()` 调用者可以通过传递 `KEY_ALLOC_BYPASS_RESTRICTION` 来抑制此检查。

使用此功能的一个示例是在内核启动时管理加密密钥环，同时允许用户空间添加密钥——前提是这些密钥可以通过内核已有的密钥验证。

调用时，限制函数将传递要添加到的密钥环、密钥类型、要添加的密钥的有效负载以及用于限制检查的数据。注意，在创建新密钥时，此函数会在有效负载预解析和实际密钥创建之间被调用。该函数应返回 0 以允许链接，或返回一个错误以拒绝链接。

为了方便起见，存在一个总是返回 `-EPERM` 的辅助函数 `restrict_link_reject`。

要检查密钥的有效性，可以调用以下函数：

```c
int validate_key(struct key *key);
```

此函数会检查指定的密钥是否已过期或被撤销。如果密钥无效，将返回错误 `EKEYEXPIRED` 或 `EKEYREVOKED`。如果密钥为 `NULL` 或未设置 `CONFIG_KEYS`，则返回 0（在后一种情况下不解析参数）。

要注册一个密钥类型，应调用以下函数：

```c
int register_key_type(struct key_type *type);
```

如果已存在同名类型的密钥，此函数将返回错误 `EEXIST`。
* 要取消注册一个密钥类型，请调用：

```c
void unregister_key_type(struct key_type *type);
```

在某些情况下，可能需要处理一组密钥。系统提供了访问密钥环类型的功能来管理这样的一组密钥：

```c
struct key_type key_type_keyring;
```

可以使用如 `request_key()` 这样的函数来查找进程中的特定密钥环。找到的密钥环可以用 `keyring_search()` 进行搜索。需要注意的是，不能使用 `request_key()` 来搜索特定的密钥环，因此这种方式的实用性有限。

### 访问有效载荷内容的注意事项
===================

最简单的情况是有效载荷直接存储在 `key->payload` 中。在这种情况下，在访问有效载荷时无需使用 RCU 或锁定机制。
对于更复杂的有效载荷内容，必须分配内存并在 `key->payload.data[]` 数组中设置指针。可以选择以下方法之一来访问数据：

1. **不可修改的密钥类型**
   如果密钥类型没有修改方法，则可以在不使用任何形式的锁的情况下访问密钥的有效载荷，前提是已知该密钥已被实例化（未实例化的密钥无法被“找到”）。

2. **密钥的信号量**
   可以使用信号量来控制对有效载荷的访问和有效载荷指针。修改时需要写锁，一般访问时需要读锁。这样做有一个缺点，即访问者可能需要休眠。

3. **RCU**
   当没有持有信号量时，必须使用 RCU；如果持有信号量，则内容不会意外更改，因为信号量仍然用于序列化对密钥的修改。密钥管理代码为密钥类型处理了这一点。
   然而，这意味着在读取指针时需要使用：

   ```c
   rcu_read_lock() ... rcu_dereference() ... rcu_read_unlock()
   ```

   在设置指针并在宽限期后处理旧内容时需要使用：

   ```c
   rcu_dereference() ... rcu_assign_pointer() ... call_rcu()
   ```
请注意，只有密钥类型本身才应修改密钥的有效载荷。
此外，RCU（Read-Copy-Update）控制的有效载荷必须包含一个用于调用 `call_rcu()` 的 `struct rcu_head`，如果有效载荷是可变大小的，则还需包含有效载荷的长度。如果未持有密钥的信号量，`key->datalen` 无法保证与刚被解引用的有效载荷一致。

注意 `key->payload.data[0]` 有一个为 __rcu 使用而标记的副本。这被称为 `key->payload.rcu_data0`。以下访问器封装了对此元素的 RCU 调用：

a) 设置或更改第一个有效载荷指针：
```c
rcu_assign_keypointer(struct key *key, void *data);
```

b) 在持有密钥信号量的情况下读取第一个有效载荷指针：
```c
[const] void *dereference_key_locked([const] struct key *key);
```
注意返回值会继承自密钥参数的 const 属性。如果静态分析认为锁没有被持有，将会报错。

c) 在持有 RCU 读锁的情况下读取第一个有效载荷指针：
```c
const void *dereference_key_rcu(const struct key *key);
```

定义密钥类型
=============

内核服务可能希望定义自己的密钥类型。例如，AFS 文件系统可能希望定义一种 Kerberos 5 票据密钥类型。为此，开发者需要填充一个 `key_type` 结构体，并将其注册到系统中。
实现密钥类型的源文件应包含以下头文件：
```c
<linux/key-type.h>
```

该结构体有多个字段，其中一些是必需的：

* `const char *name`

   密钥类型的名称。此名称用于将用户空间提供的密钥类型名称转换为指向该结构体的指针。

* `size_t def_datalen`

   这个字段是可选的，它提供了默认的有效载荷数据长度，作为配额的一部分。如果密钥类型的有效载荷总是或几乎总是相同大小，那么这是一种更高效的方式。

在特定密钥上创建或更新时，可以通过调用以下函数来更改数据长度（和配额）：
```c
int key_payload_reserve(struct key *key, size_t datalen);
```
使用修订后的数据长度。如果这样做不可行，将返回错误 EDQUOT。

* `int (*vet_description)(const char *description);`

   这是一个可选方法，用于验证密钥描述。如果密钥类型不认可密钥描述，则可以返回错误，否则应返回 0。

* `int (*preparse)(struct key_preparsed_payload *prep);`

   这是一个可选方法，允许密钥类型尝试在创建密钥（添加密钥）或获取密钥信号量之前（更新或实例化密钥）解析有效载荷。由 prep 指向的结构体如下所示：
```c
struct key_preparsed_payload {
	char		*description;
	union key_payload payload;
	const void	*data;
	size_t		datalen;
	size_t		quotalen;
	time_t		expiry;
};
```
在调用该方法之前，调用者会用有效载荷块参数填充 data 和 datalen；quotalen 将被填充为来自密钥类型的默认配额大小；expiry 将被设置为 TIME_T_MAX，其余部分将被清空。
如果可以从有效载荷内容中提出描述，则应将其附加到 description 字段。如果调用者在调用 `add_key()` 时传递 NULL 或 ""，则将使用此描述作为密钥描述。
该方法可以将任何它想要的数据附加到负载中。这仅仅是传递给 `instantiate()` 或 `update()` 操作。如果设置了过期时间，则在从这些数据实例化密钥时，过期时间将应用于该密钥。

该方法成功时应返回 0，否则返回一个负的错误代码。

*  ``void (*free_preparse)(struct key_preparsed_payload *prep);``

    如果提供了 `preparse()` 方法，则需要此方法，否则它不会被使用。此方法清理由 `preparse()` 方法填充的 `key_preparsed_payload` 结构中的描述和负载字段。无论 `instantiate()` 或 `update()` 是否成功，只要 `preparse()` 成功返回后，此方法总会被调用。

*  ``int (*instantiate)(struct key *key, struct key_preparsed_payload *prep);``

    此方法用于在构造过程中将负载附加到密钥上。所附加的负载不一定与传递给此函数的数据相关。

    `prep->data` 和 `prep->datalen` 字段将定义原始的负载块。如果提供了 `preparse()` 方法，则其他字段也可能被填充。

    如果附加到密钥的数据量与 `keytype->def_datalen` 中的大小不同，则应调用 `key_payload_reserve()`。

    此方法不需要锁定密钥以附加负载。由于 `key->flags` 中未设置 `KEY_FLAG_INSTANTIATED`，因此其他操作无法访问该密钥。

    在此方法中休眠是安全的。
### 翻译成中文

`generic_key_instantiate()` 函数用于简单地将数据从 `prep->payload.data[]` 复制到 `key->payload.data[]`，并在第一个元素上进行 RCU 安全的赋值。然后它会清除 `prep->payload.data[]`，以防止 `free_preparse` 方法释放这些数据。

```c
*  ``int (*update)(struct key *key, const void *data, size_t datalen);``

    如果这种类型的密钥可以更新，则应提供此方法。该方法被调用以根据提供的数据块更新密钥的有效负载。`prep->data` 和 `prep->datalen` 字段将定义原始的有效负载数据块。如果提供了 `preparse()` 方法，则其他字段也可能被填充。如果数据长度可能会改变，在实际更改之前应调用 `key_payload_reserve()`。注意，如果此操作成功，则类型将致力于更改密钥，因为数据已经被修改，因此所有内存分配必须首先完成。
    
    在调用此方法之前，密钥的信号量会被写锁定，但这仅阻止其他写入者；对密钥有效负载的所有更改必须在 RCU 条件下进行，并且必须使用 `call_rcu()` 来处理旧的有效负载。
    
    应在进行更改之前调用 `key_payload_reserve()`，但在所有分配和其他可能导致失败的函数调用之后调用。
    
    此方法中睡眠是安全的。

*  ``int (*match_preparse)(struct key_match_data *match_data);``

    此方法是可选的。它在即将执行密钥搜索时被调用。给定以下结构体：

    ```c
    struct key_match_data {
        bool (*cmp)(const struct key *key,
                    const struct key_match_data *match_data);
        const void *raw_data;
        void *preparsed;
        unsigned lookup_type;
    };
    ```

    在调用时，`raw_data` 将指向调用者用于匹配密钥的标准，并且不应修改。`(*cmp)()` 将指向默认的匹配器函数（该函数会对 `raw_data` 进行精确描述匹配），并且 `lookup_type` 将被设置为指示直接查找。
    
    可用的 `lookup_type` 值如下：

    *  `KEYRING_SEARCH_LOOKUP_DIRECT` - 直接查找将对类型和描述进行哈希处理，以缩小搜索范围至少量密钥。
```
* `KEYRING_SEARCH_LOOKUP_ITERATE` - 迭代查找会遍历密钥环中的所有密钥，直到找到匹配的密钥。这必须用于任何不是直接通过密钥描述进行简单匹配的搜索。
方法可以设置 `cmp` 指向一个自定义的函数来进行其他形式的匹配，可以将 `lookup_type` 设置为 `KEYRING_SEARCH_LOOKUP_ITERATE`，并且可以附加一些数据到 `preparsed` 指针上供 `(*cmp)()` 使用。
`(*cmp)()` 应该在密钥匹配时返回 `true`，否则返回 `false`。
如果设置了 `preparsed`，可能需要使用 `match_free()` 方法来清理它。
此方法成功时应返回 0，否则返回一个负的错误代码。
在此方法中睡眠是可以的，但 `(*cmp)()` 不允许睡眠，因为它会被锁定。
如果没有提供 `match_preparse()` 方法，则这种类型的密钥将完全按照其描述进行匹配。
* `void (*match_free)(struct key_match_data *match_data);`

    此方法是可选的。如果提供了，会在成功调用 `match_preparse()` 后调用此方法来清理 `match_data->preparsed`。
* `void (*revoke)(struct key *key);`

    此方法是可选的。当密钥被撤销时调用此方法以丢弃部分有效负载数据。调用者会持有密钥信号量的写锁。
在此方法中睡眠是安全的，但需要注意避免与密钥信号量产生死锁。
```c
/* `destroy` 是一个可选的方法。当密钥被销毁时，此方法用于丢弃密钥中的负载数据。
   在调用此方法时，不需要锁定密钥来访问其负载；可以认为此时密钥已经不可访问。
   注意：在调用此函数之前，密钥的类型可能已经被更改了。
   在此方法中睡眠是不安全的；调用者可能持有自旋锁。*/

void (*destroy)(struct key *key);

/* `describe` 是一个可选的方法。在读取 `/proc/keys` 时，此方法会被调用，
   以文本形式总结密钥的描述和负载信息。
   此方法将在持有 RCU 读锁的情况下被调用。如果需要访问负载，应使用 `rcu_dereference()` 来读取负载指针。
   `key->datalen` 不能保证与负载内容保持一致。
   描述不会改变，但密钥的状态可能会改变。
   在此方法中睡眠是不安全的；调用者持有 RCU 读锁。*/

void (*describe)(const struct key *key, struct seq_file *p);

/* `read` 是一个可选的方法。此方法由 `KEYCTL_READ` 调用，将密钥的负载转换为用户空间可以处理的数据块。
   理想情况下，数据块应该与传递给实例化和更新方法的格式相同。
   如果成功，应返回可以生成的数据块大小，而不是实际复制的大小。*/

long (*read)(const struct key *key, char __user *buffer, size_t buflen);
```
此方法将在键的信号量被读锁的情况下被调用。这将防止键的有效载荷发生变化。在访问键的有效载荷时，无需使用RCU锁定。在此方法中睡眠是安全的，例如当访问用户空间缓冲区时。

```c
int (*request_key)(struct key_construction *cons, const char *op, void *aux);
```

此方法是可选的。如果提供了此方法，`request_key()` 及其相关函数将调用此函数，而不是上层调用 `/sbin/request-key` 来操作这种类型的键。
`aux` 参数是在调用 `request_key_async_with_auxdata()` 或类似函数时传递的，否则为 `NULL`。同时传递的还有要操作的键的构造记录和操作类型（目前只有 "create"）。

此方法可以在上层调用完成之前返回，但无论是否成功，无论是否有错误，都必须在所有情况下调用以下函数以完成实例化过程：

```c
void complete_request_key(struct key_construction *cons, int error);
```

`error` 参数在成功时应为 0，在出错时应为负数。此操作会销毁构造记录并撤销授权键。如果指示了错误，则正在构造的键将被负面实例化（如果它尚未被实例化）。

如果此方法返回错误，该错误将被返回给 `request_key*()` 的调用者。在返回前必须先调用 `complete_request_key()`。

正在构造的键和授权键可以在 `key_construction` 结构体中找到，该结构体由 `cons` 指向：

```c
struct key_construction {
    struct key *key;       // 正在构造的键
    struct key *authkey;   // 授权键
};
```

```c
struct key_restriction *(*lookup_restriction)(const char *params);
```

此可选方法用于启用用户空间配置密钥环限制。传递限制参数字符串（不包括键类型名称），此方法返回一个指向 `key_restriction` 结构体的指针，其中包含评估每次尝试的键链接操作的相关函数和数据。如果没有匹配项，则返回 `-EINVAL`。

```c
asym_eds_op` 和 `asym_verify_signature`:
```
```c
int (*asym_eds_op)(struct kernel_pkey_params *params, const void *in, void *out);
int (*asym_verify_signature)(struct kernel_pkey_params *params, const void *in, const void *in2);
```

这些方法是可选的。如果提供了第一个方法，则允许使用键来加密、解密或签名数据块；第二个方法则允许验证签名。
在所有情况下，`params` 块中提供了以下信息：

```c
struct kernel_pkey_params {
    struct key *key;
    const char *encoding;
    const char *hash_algo;
    char *info;
    __u32 in_len;
    union {
        __u32 out_len;
        __u32 in2_len;
    };
    enum kernel_pkey_operation op : 8;
};
```

这包括要使用的键；表示要使用的编码方式的字符串（例如，对于 RSA 键，可以使用 "pkcs1" 表示 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5 编码或 "raw" 表示无编码）；用于生成签名数据的哈希算法名称（如果适用）；输入和输出（或第二个输入）缓冲区的大小；以及要执行的操作的标识符。
对于给定的操作ID，输入和输出缓冲区的使用方式如下：

| 操作ID        | 输入缓冲区, in, in_len    | 输出缓冲区, out, out_len   | 第二输入缓冲区, in2, in2_len |
|----------------|-------------------------|--------------------------|-------------------------------|
| kernel_pkey_encrypt | 原始数据            | 加密数据               | -                             |
| kernel_pkey_decrypt | 加密数据            | 原始数据               | -                             |
| kernel_pkey_sign    | 原始数据            | 签名                   | -                             |
| kernel_pkey_verify  | 原始数据            | -                       | 签名                          |

`asym_eds_op()` 处理加密、解密和签名创建，具体由 `params->op` 指定。注意 `params->op` 同样适用于 `asym_verify_signature()`。
加密和签名创建都会从输入缓冲区中读取原始数据，并在输出缓冲区中返回加密结果。如果设置了编码，则可能已经添加了填充。在签名创建的情况下，根据编码，可能需要指示摘要算法——其名称应在 `hash_algo` 中提供。
解密会从输入缓冲区中读取加密数据，并在输出缓冲区中返回原始数据。如果设置了编码，则会检查并移除填充。
验证会从输入缓冲区中读取原始数据，并从第二个输入缓冲区中读取签名，然后检查二者是否匹配。将验证填充。根据编码，生成原始数据时所用的摘要算法可能需要在 `hash_algo` 中指示。
如果成功，`asym_eds_op()` 应返回写入输出缓冲区的字节数。`asym_verify_signature()` 应返回 0。
可能会返回各种错误，包括：
- EOPNOTSUPP：如果操作不被支持；
- EKEYREJECTED：如果验证失败；
- ENOPKG：如果所需的加密算法不可用。

```
asym_query:
int (*asym_query)(const struct kernel_pkey_params *params,
		  struct kernel_pkey_query *info);
```

此方法是可选的。如果提供了该方法，可以确定密钥中持有的公钥或非对称密钥的相关信息。
参数块与 `asym_eds_op()` 相同，但 `in_len` 和 `out_len` 未使用。应使用 `encoding` 和 `hash_algo` 字段来适当减少返回的缓冲区/数据大小。
如果成功，将填充以下信息：

```c
struct kernel_pkey_query {
	__u32 supported_ops;
	__u32 key_size;
	__u16 max_data_size;
	__u16 max_sig_size;
	__u16 max_enc_size;
	__u16 max_dec_size;
};
```

`supported_ops` 字段包含一个位掩码，指示密钥支持的操作，包括加密、解密、签名以及验证签名。定义了以下常量：

`KEYCTL_SUPPORTS_{ENCRYPT,DECRYPT,SIGN,VERIFY}`

`key_size` 字段表示密钥的大小（以比特为单位）。`max_data_size` 和 `max_sig_size` 是签名创建和验证的最大原始数据和签名大小；`max_enc_size` 和 `max_dec_size` 是加密和解密的最大原始数据和签名大小。所有 `max_*_size` 字段均以字节为单位测量。
如果成功，将返回 0。如果密钥不支持此功能，则返回 EOPNOTSUPP。
请求密钥回调服务
============================

为了创建一个新的密钥，内核将尝试执行以下命令行：

	/sbin/request-key create <key> <uid> <gid> \
		<threadring> <processring> <sessionring> <callout_info>

<key> 是正在构建的密钥，三个密钥环（threadring、processring 和 sessionring）是从触发搜索的进程中获取的。包含这些密钥环的原因有两个：

   1. 其中一个密钥环可能包含获取密钥所需的认证令牌，例如 Kerberos 的 Ticket-Granting Ticket。
   2. 新创建的密钥很可能应该缓存在这三个环中的一个（可能是会话环）。

该程序应在尝试访问更多密钥之前将其UID和GID设置为指定的值。然后它可以查找特定用户的进程来处理这个请求（例如，KDE桌面管理器可能会在另一个密钥中放置一个路径）。程序（或它调用的任何程序）应通过调用KEYCTL_INSTANTIATE或KEYCTL_INSTANTIATE_IOV完成密钥的构建，并允许将密钥缓存在其中一个密钥环（通常是会话环）中。作为替代方案，可以使用KEYCTL_NEGATE或KEYCTL_REJECT标记密钥为无效；这也允许将密钥缓存在其中一个密钥环中。如果返回时密钥仍然未构建，则该密钥将被标记为无效，添加到会话密钥环，并向密钥请求者返回错误。

补充信息可以从调用此服务的任何人或任何程序提供。这将作为<callout_info>参数传递。如果没有此类信息可用，则将传递“-”作为此参数。

同样，内核可以通过执行以下命令来更新已过期或即将过期的密钥：

	/sbin/request-key update <key> <uid> <gid> \
		<threadring> <processring> <sessionring>

在这种情况下，程序不需要实际将密钥附加到环上；这些环仅用于参考。

垃圾回收
==================

对于类型已被移除的无效密钥（dead keys），将由后台垃圾回收器尽快从指向它们的密钥环中自动解除链接并删除。

同样，被撤销和已过期的密钥也将进行垃圾回收，但只有在经过一定时间后才会进行。这段时间以秒为单位设置在：

	/proc/sys/kernel/keys/gc_delay
