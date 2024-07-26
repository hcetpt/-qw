============================
内核密钥保留服务
============================

此服务允许将加密密钥、身份验证令牌、跨域用户映射等缓存在内核中，供文件系统和其他内核服务使用。
允许使用密钥环；这是一种特殊的密钥类型，可以保存指向其他密钥的链接。每个进程都有三个标准的密钥环订阅项，内核服务可以通过这些订阅项搜索相关的密钥。

通过启用以下选项来配置此密钥服务：

	"安全选项"/"启用密钥保留支持" (CONFIG_KEYS)

本文档包含以下部分：

.. contents:: :local:


密钥概述
============

在此上下文中，密钥表示加密数据单元、身份验证令牌、密钥环等。在内核中，它们由 struct key 表示。
每个密钥具有多个属性：

	- 一个序列号
- 一个类型
- 一个描述（用于在搜索中匹配密钥）
- 访问控制信息
- 过期时间
- 一个有效负载
- 状态
* 每个密钥都会被分配一个类型为 `key_serial_t` 的序列号，在该密钥的生命周期内是唯一的。所有的序列号都是正的非零32位整数。
用户空间程序可以使用密钥的序列号作为访问该密钥的一种方式，但需经过权限检查。
* 每个密钥都有一个定义好的“类型”。类型必须由内核服务（如文件系统）在内核中注册后，才能添加或使用该类型的密钥。用户空间程序不能直接定义新的类型。
密钥类型在内核中通过 `struct key_type` 表示，这定义了一系列可以对该类型的密钥执行的操作。
如果一个类型从系统中移除，那么所有该类型的密钥将失效。
* 每个密钥都有一个描述。这应该是一个可打印的字符串。密钥类型提供了一个操作来匹配密钥的描述和标准字符串。
* 每个密钥都有一个拥有者用户ID、一个组ID和一个权限掩码。这些用于控制用户空间中的进程对密钥的操作，以及内核服务是否能够找到该密钥。
* 每个密钥可以通过其类型的实例化函数设置过期时间。密钥也可以是永不过期的。
* 每个密钥可以有一个负载。这是代表实际“密钥”的一段数据。例如，对于密钥环来说，这是密钥环链接的一系列密钥列表；对于用户定义的密钥，则是一段任意的数据块。
拥有负载不是必需的；事实上，负载可以直接存储在 `struct key` 中的一个值。
当一个密钥被实例化时，会调用该密钥类型的实例化函数，并传入一段数据，这之后会以某种方式创建密钥的有效载荷。
同样地，当用户空间希望读回密钥的内容（如果被允许的话），另一个密钥类型的操作将被调用来将密钥的关联有效载荷转换回一段数据。
每个密钥都可以处于以下几种基本状态之一：

    * 未实例化。密钥存在，但没有关联任何数据。从用户空间请求的密钥将处于这种状态。
    * 实例化。这是正常状态。密钥是完整的，并且有关联的数据。
    * 负状态。这是一个相对短暂的状态。密钥充当一个标记，表明先前对用户空间的调用失败了，并作为密钥查找的限制。负状态的密钥可以更新到正常状态。
    * 过期。密钥可以设置有效期。如果超过了其有效期，它们就会进入这种状态。过期的密钥可以更新回正常状态。
    * 撤销。密钥通过用户空间操作被置于这种状态。它无法被找到或操作（除了解除链接）。
    * 无效。密钥的类型已被注销，因此现在这个密钥无用了。

处于最后三种状态的密钥可能会被垃圾回收。请参阅“垃圾回收”部分。
### 主要服务概述

主要服务除了提供密钥功能外，还提供了以下特性：

- 主要服务定义了三种特殊的密钥类型：

    (+) "密钥环"

        密钥环是一种特殊的密钥，包含其他密钥的列表。可以通过各种系统调用来修改密钥环列表。创建密钥环时不应为其指定负载。
    (+) "用户"

        这种类型的密钥具有描述和负载，可以是任意的数据块。这些密钥可以从用户空间创建、更新和读取，并不是为内核服务设计的。
    (+) "登录"

        与“用户”密钥类似，“登录”密钥的负载也是任意的数据块。它旨在作为存储秘密的地方，这些秘密对内核可访问但对用户空间程序不可见。
        描述可以是任意内容，但必须以非空字符串开头，该字符串描述了密钥的“子类”。子类与描述的其余部分之间用':'分隔。“登录”密钥可以从用户空间创建和更新，但其负载只能从内核空间读取。
- 每个进程订阅三个密钥环：线程特定的密钥环、进程特定的密钥环以及会话特定的密钥环。
    - 线程特定的密钥环在发生任何克隆、分叉(fork)、虚拟分叉(vfork)或执行(execve)操作时，从子进程中被丢弃。只有当需要时才会创建新的密钥环。
    - 进程特定的密钥环在克隆、分叉(fork)、虚拟分叉(vfork)时（除非指定了CLONE_THREAD标志，否则将共享）被替换为空密钥环。执行(execve)也会丢弃当前进程的进程特定密钥环并创建一个新的。
    - 会话特定的密钥环即使在克隆、分叉(fork)、虚拟分叉(vfork)和执行(execve)操作中，包括后者执行设置了用户ID或组ID的二进制文件时，仍然保持不变。但是，一个进程可以使用PR_JOIN_SESSION_KEYRING来用一个新的会话密钥环替换其当前的会话密钥环。允许请求匿名的新密钥环，或者尝试创建或加入具有特定名称的密钥环。
    - 当线程的真实用户ID和组ID发生变化时，线程密钥环的所有权也会随之变化。
- 系统中的每个用户ID持有两个特殊的密钥环：用户特定的密钥环和默认用户会话密钥环。默认会话密钥环初始化时会链接到用户特定的密钥环。
当一个进程更改其实际的用户ID（UID）时，如果它之前没有会话密钥，则会订阅新UID对应的默认会话密钥。
如果一个进程尝试访问其会话密钥但并没有这样的密钥，则会订阅其当前UID对应的默认会话密钥。
每个用户有两个配额，用于追踪他们所拥有的密钥。其中一个限制了密钥和密钥环的总数，另一个限制了可以消耗的描述和负载空间的总量。
用户可以通过procfs文件查看这些配额和其他统计信息。root用户也可以通过sysctl文件来调整配额限制（参见“新的procfs文件”部分）。
特定于进程和线程的密钥环不会计入用户的配额中。
如果某个系统调用以某种方式修改密钥或密钥环会导致用户超出配额，则拒绝该操作并返回EDQUOT错误。
存在一个系统调用接口，允许用户空间程序创建和操作密钥及密钥环。
存在一个内核接口，允许服务注册类型并搜索密钥。
存在一种方法，允许从内核发起的搜索回调到用户空间请求无法在进程的密钥环中找到的密钥。
可选地提供了一个文件系统，通过它可以查看和操作密钥数据库。
### 密钥访问权限
密钥具有所有者用户ID、组访问ID以及权限掩码。该掩码针对持有者、用户、组和其他访问权限分别最多包含八位，但每组中只有六位被定义。授予的权限包括：

- **查看**

    允许查看密钥或密钥环的属性——包括密钥类型和描述。
- **读取**

    允许查看密钥的内容或密钥环中链接的密钥列表。
- **写入**

    允许实例化或更新密钥的内容，或者允许向密钥环添加或删除链接。
- **搜索**

    允许搜索密钥环并找到密钥。搜索只能递归进入设置了搜索权限的嵌套密钥环。
- **链接**

    允许链接到密钥或密钥环。为了从一个密钥环创建到一个密钥的链接，进程必须在密钥环上拥有写入权限，并且在密钥上拥有链接权限。
- **设置属性**

    允许更改密钥的所有者ID、组ID和权限掩码。
对于更改所有权、组ID或权限掩码，是密钥的所有者或拥有系统管理员能力就足够了。

### SELinux支持
已向SELinux添加“密钥”安全类，以便可以根据不同上下文对创建的密钥应用强制访问控制。此支持尚处于初步阶段，在不久的将来可能会发生显著变化。
目前，上述所有基本权限也在SELinux中提供；SELinux仅在执行完所有基本权限检查后被调用。
文件`/proc/self/attr/keycreate`的内容会影响新创建的密钥的标签。如果该文件的内容对应于一个SELinux安全上下文，则该密钥将被分配该上下文。否则，密钥将被分配为请求创建密钥的任务当前的上下文。任务必须被明确赋予权限以特定的安全上下文为新创建的密钥分配标签，这通过在密钥安全类中的“创建”权限实现。
默认的密钥环如果与用户关联，将会被标记为该用户的默认上下文，但这只有在登录程序被适当地修改以在登录过程中正确初始化`keycreate`时才会发生。否则，它们将被标记为登录程序本身的上下文。
然而，请注意与root用户关联的默认密钥环被标记为默认内核上下文，因为这些密钥环是在启动过程早期创建的，在root有机会登录之前。
与新线程关联的密钥环各自被标记为相应线程的上下文，并且会话和进程密钥环也类似处理。

新增的ProcFS文件
==================

管理员可以通过以下两个添加到ProcFS中的文件来了解密钥服务的状态：

* `/proc/keys`

    此文件列出了当前可由读取此文件的任务查看的所有密钥的信息，包括类型、描述和权限。
    不可能通过这种方式查看密钥的有效载荷，尽管可以提供一些关于它的信息。
    列表中仅包含那些向读取进程授予查看权限的密钥，无论该进程是否拥有它们。请注意，LSM安全检查仍然执行，并可能进一步过滤掉当前进程无权查看的密钥。
    文件的内容如下所示： 

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

    标志的含义是：

    I    已实例化
    R    已撤销
    D    已死亡
    Q    对用户的配额有贡献
    U    正在通过回调到用户空间构建
    N    负密钥

* `/proc/key-users`

    此文件列出了系统中至少有一个密钥的每个用户的跟踪数据。此类数据包括配额信息和统计信息：

        [root@andromeda root]# cat /proc/key-users
        0:     46 45/45 1/100 13/10000
        29:     2 2/2 2/100 40/10000
        32:     2 2/2 2/100 40/10000
        38:     2 2/2 2/100 40/10000

    每行的格式是：

        <UID>:            适用于此的用户ID
        <usage>           结构引用计数
        <inst>/<keys>     密钥总数和已实例化的数量
        <keys>/<max>      密钥数量配额
        <bytes>/<max>     密钥大小配额

还添加了四个新的sysctl文件用于控制密钥的配额限制：

* `/proc/sys/kernel/keys/root_maxkeys`
  `/proc/sys/kernel/keys/root_maxbytes`

    这些文件存储了root用户可以拥有的最大密钥数量以及可以在这些密钥中存储的最大总字节数。
* `/proc/sys/kernel/keys/maxkeys`
  `/proc/sys/kernel/keys/maxbytes`

    这些文件存储了每个非root用户可以拥有的最大密钥数量以及每个用户可以在其密钥中存储的最大总字节数。
root用户可以通过将每个新的限制作为十进制数字字符串写入相应的文件来更改这些值。

用户空间系统调用接口
======================

用户空间可以直接通过三个新的系统调用来操作密钥：add_key、request_key 和 keyctl。后者提供了多个用于操作密钥的功能。
当直接引用一个密钥时，用户空间程序应使用密钥的序列号（一个32位正整数）。但是，有一些特殊值可用于引用与调用进程相关的特殊密钥和密钥环：

	常量				值	引用的密钥
	==============================	======	===========================
	KEY_SPEC_THREAD_KEYRING		-1	线程特定的密钥环
	KEY_SPEC_PROCESS_KEYRING	-2	进程特定的密钥环
	KEY_SPEC_SESSION_KEYRING	-3	会话特定的密钥环
	KEY_SPEC_USER_KEYRING		-4	UID特定的密钥环
	KEY_SPEC_USER_SESSION_KEYRING	-5	UID-会话密钥环
	KEY_SPEC_GROUP_KEYRING		-6	GID特定的密钥环
	KEY_SPEC_REQKEY_AUTH_KEY	-7	假设的request_key() 
						  授权密钥

主要的系统调用包括：

  * 创建一个指定类型、描述和有效负载的新密钥，并将其添加到指定的密钥环中：

	key_serial_t add_key(const char *type, const char *desc,
			     const void *payload, size_t plen,
			     key_serial_t keyring);

     如果具有相同类型和描述的密钥已经存在于密钥环中，则此函数将尝试用给定的有效负载更新该密钥，或者如果密钥类型不支持该功能则返回错误EEXIST。进程还必须有权限写入密钥才能更新它。新密钥将被授予所有用户权限，并且没有组或第三方权限。
否则，这将尝试创建一个指定类型和描述的新密钥，并用提供的有效负载实例化它并将其附加到密钥环中。在这种情况下，如果进程没有权限写入密钥环则会产生错误。
如果密钥类型支持的话，如果描述为空指针或空字符串，密钥类型将尝试从有效负载的内容生成描述。
有效负载是可选的，如果没有需要可以设置为NULL。
有效负载的大小为plen，对于空的有效负载，plen可以为零。
可以通过设置类型为"keyring"，密钥环名称作为描述（或NULL），并将有效负载设置为NULL来生成新的密钥环。
可以通过指定类型"user"来创建用户定义的密钥。建议用户定义的密钥的描述以类型ID和冒号开头，例如"krb5tgt:"表示Kerberos 5的票证授予票证。
任何其他类型必须由内核服务（如文件系统）提前向内核注册。
如果成功，则返回新创建或更新的密钥的ID。

* 在进程的密钥环中搜索密钥，必要时调用用户空间创建它：

	key_serial_t request_key(const char *type, const char *description,
				 const char *callout_info,
				 key_serial_t dest_keyring);

     此函数按顺序在进程的所有密钥环中（线程、进程、会话）搜索匹配的密钥。这非常类似于KEYCTL_SEARCH，包括可选地将发现的密钥附加到密钥环。
如果找不到密钥，并且callout_info不是NULL，则将调用/sbin/request-key尝试获取密钥。callout_info字符串将作为参数传递给程序。
要将一个密钥链接到目标密钥环中，该密钥必须向调用者授予对该密钥的链接权限，并且密钥环必须授予写权限。
更多信息请参阅文档/安全/密钥/request-key.rst
keyctl系统调用的功能包括：

  *  为本进程将一个特殊的密钥ID映射到真实的密钥ID上：

```c
key_serial_t keyctl(KEYCTL_GET_KEYRING_ID, key_serial_t id,
			    int create);
```

根据"id"查找指定的特殊密钥（如果需要的话创建密钥），如果存在，则返回找到的密钥或密钥环的ID。
如果密钥尚不存在，当"create"非零时创建该密钥；如果"create"为零，则返回错误ENOKEY。
*  用一个新的密钥环替换此进程订阅的会话密钥环：

```c
key_serial_t keyctl(KEYCTL_JOIN_SESSION_KEYRING, const char *name);
```

如果"name"为NULL，创建一个匿名密钥环并将其作为会话密钥环与进程关联，取代旧的会话密钥环。
如果"name"不为NULL，如果存在同名的密钥环，尝试将其作为会话密钥环进行关联，若不允许则返回错误；否则创建一个新的同名密钥环并将其作为会话密钥环进行关联。
为了关联到一个命名的密钥环，该密钥环必须对进程的所有权具有搜索权限。
成功时返回新的会话密钥环的ID。
*  更新指定的密钥：

```c
long keyctl(KEYCTL_UPDATE, key_serial_t key, const void *payload,
		    size_t plen);
```

尝试使用给定的有效载荷更新指定的密钥，或者如果该功能不受密钥类型支持，则返回错误EOPNOTSUPP。进程还必须具有写入密钥的权限才能更新它。
有效载荷长度为plen，可以为空或不存在，类似于add_key()函数。
* 撤销一个密钥：

```c
long keyctl(KEYCTL_REVOKE, key_serial_t key);
```

这会使密钥无法用于后续操作。进一步尝试使用该密钥将遇到错误EKEYREVOKED，并且该密钥将不再可查找。

* 更改密钥的所有权：

```c
long keyctl(KEYCTL_CHOWN, key_serial_t key, uid_t uid, gid_t gid);
```

此函数允许更改密钥的所有者和组ID。uid或gid中的任何一个可以设置为-1以抑制该更改。
只有超级用户才能将密钥的所有者更改为当前所有者以外的其他内容。同样地，只有超级用户才能将密钥的组ID更改为调用进程的组ID或其组列表成员以外的内容。

* 更改密钥上的权限掩码：

```c
long keyctl(KEYCTL_SETPERM, key_serial_t key, key_perm_t perm);
```

此函数允许密钥的所有者或超级用户更改密钥上的权限掩码。
仅允许可用的位；如果设置了任何其他位，则返回错误EINVAL。

* 描述一个密钥：

```c
long keyctl(KEYCTL_DESCRIBE, key_serial_t key, char *buffer,
            size_t buflen);
```

此函数返回密钥属性（但不包括其有效负载数据）的摘要作为提供的缓冲区中的字符串。
除非出现错误，它始终返回其可以生成的数据量，即使这些数据对于缓冲区来说太大，但它不会向用户空间复制超过请求的数据量。如果缓冲区指针为NULL，则不会进行复制。
要使此函数成功，进程必须具有查看密钥的权限。
如果成功，在缓冲区中放置格式如下所示的字符串：

```plaintext
<type>;<uid>;<gid>;<perm>;<description>
```

其中type和description是字符串，uid和gid是十进制数，而perm是十六进制数。如果缓冲区足够大，则在字符串末尾包含一个NUL字符。
这可以通过以下方式解析：

```c
sscanf(buffer, "%[^;];%d;%d;%o;%s", type, &uid, &gid, &mode, desc);
```

* 清空一个密钥环：

```c
long keyctl(KEYCTL_CLEAR, key_serial_t keyring);
```

此函数清除与密钥环关联的密钥列表。调用进程必须具有对密钥环的写入权限，并且它必须是一个密钥环（否则将导致错误ENOTDIR）。
此函数也可以用于清除特殊的内核密钥环，前提是这些密钥环被适当地标记，并且用户具有 `CAP_SYS_ADMIN` 的能力。DNS 解析缓存密钥环就是一个例子。
* 将一个密钥链接到一个密钥环中 ::

    long keyctl(KEYCTL_LINK, key_serial_t keyring, key_serial_t key);

    此函数在密钥环和密钥之间创建一个链接。进程必须对密钥环具有写权限，并且对密钥具有链接权限。
    如果密钥环不是一个真正的密钥环，则会返回错误 ENOTDIR；如果密钥环已满，则会返回错误 ENFILE。
    链接过程会检查密钥环的嵌套层次，如果嵌套太深则返回 ELOOP，如果链接会导致循环则返回 EDEADLK。
    密钥环内与新密钥类型和描述相匹配的所有链接将在添加新密钥时从密钥环中删除。
* 将一个密钥从一个密钥环移动到另一个密钥环 ::

    long keyctl(KEYCTL_MOVE,
                key_serial_t id,
                key_serial_t from_ring_id,
                key_serial_t to_ring_id,
                unsigned int flags);

    将由 "id" 指定的密钥从 "from_ring_id" 指定的密钥环移动到 "to_ring_id" 指定的密钥环。如果两个密钥环相同，则不执行任何操作。
    可以在 "flags" 中设置 KEYCTL_MOVE_EXCL，这样如果目标密钥环中存在匹配的密钥，操作将以 EEXIST 错误失败；否则，这样的密钥将被替换。
    要使此函数成功，进程必须对密钥具有链接权限，并且对两个密钥环都具有写权限。这里发生在目标密钥环上的任何 KEYCTL_LINK 可能产生的错误也适用。
* 从一个密钥环中解除链接一个密钥或密钥环 ::

    long keyctl(KEYCTL_UNLINK, key_serial_t keyring, key_serial_t key);

    此函数遍历密钥环，查找指向指定密钥的第一个链接，并在找到后将其移除。对于该密钥的后续链接将被忽略。进程必须对密钥环具有写权限。
    如果密钥环不是一个真正的密钥环，则会返回错误 ENOTDIR；如果密钥不存在，则返回错误 ENOENT。
* 在密钥环树中搜索一个密钥:

    `key_serial_t keyctl(KEYCTL_SEARCH, key_serial_t keyring,
                         const char *type, const char *description,
                         key_serial_t dest_keyring);`

    这个函数会在指定的密钥环所指向的密钥环树中查找与给定类型和描述相匹配的密钥。每个密钥环在递归到其子密钥环之前都会被检查。

    进程必须对顶层密钥环有搜索权限，否则会返回错误EACCES。只有进程具有搜索权限的密钥环才会被递归遍历，并且只有进程对之有搜索权限的密钥和密钥环才能被匹配。如果指定的密钥环不是一个真正的密钥环，则会返回错误ENOTDIR。

    如果搜索成功，该函数将尝试将找到的密钥链接到目标密钥环（如果提供了非零ID的目标密钥环）。这里适用的所有KEYCTL_LINK约束也适用。

    如果搜索失败，会返回错误ENOKEY、EKEYREVOKED或EKEYEXPIRED。如果成功，则返回找到的密钥ID。

* 从密钥中读取负载数据:

    `long keyctl(KEYCTL_READ, key_serial_t key, char *buffer,
                 size_t buflen);`

    此函数试图从指定的密钥中读取负载数据到缓冲区。进程必须对该密钥有读权限才能成功。

    返回的数据会被密钥类型处理以便呈现。例如，密钥环会返回一个key_serial_t类型的数组，表示所有它订阅的密钥的ID。用户定义的密钥类型则直接返回它的数据。如果密钥类型没有实现这个函数，则返回错误EOPNOTSUPP。

    如果指定的缓冲区太小，那么会返回所需的缓冲区大小。需要注意的是，在这种情况下，缓冲区的内容可能以某种未定义的方式被覆盖。

    否则，如果成功，则返回复制到缓冲区中的数据量。

* 实例化一个部分构造好的密钥:

    `long keyctl(KEYCTL_INSTANTIATE, key_serial_t key,
                 const void *payload, size_t plen,
                 key_serial_t keyring);`
    `long keyctl(KEYCTL_INSTANTIATE_IOV, key_serial_t key,
                 const struct iovec *payload_iov, unsigned ioc,
                 key_serial_t keyring);`

    如果内核回调用户空间来完成密钥实例化，用户空间应该使用此调用来为密钥提供数据，否则在被调用的进程返回前密钥将被自动标记为无效。

    进程必须对要实例化的密钥有写权限，并且密钥必须是未实例化的状态。
如果指定了密钥环（非零），该密钥也将被链接到该密钥环中，但是所有在`KEYCTL_LINK`中适用的约束在此情况下也适用。

`payload`和`plen`参数描述了与`add_key()`相同的负载数据。
`payload_iov`和`ioc`参数以`iovec`数组的形式而不是单一缓冲区来描述负载数据。

* 对部分构造完成的密钥进行否定实例化：

```c
long keyctl(KEYCTL_NEGATE, key_serial_t key,
            unsigned timeout, key_serial_t keyring);
long keyctl(KEYCTL_REJECT, key_serial_t key,
            unsigned timeout, unsigned error, key_serial_t keyring);
```

如果内核回调用户空间来完成密钥的实例化，在被调用进程返回前无法满足请求时，用户空间应该使用此调用来标记密钥为否定状态。
进程必须对要实例化的密钥具有写访问权限，并且该密钥必须尚未实例化。
如果指定了密钥环（非零），该密钥也将被链接到该密钥环中，但是所有在`KEYCTL_LINK`中适用的约束在此情况下也适用。
如果密钥被拒绝，未来对该密钥的搜索将返回指定的错误码，直到该拒绝的密钥过期。否定密钥等同于使用`ENOKEY`作为错误码来拒绝密钥。

* 设置默认请求密钥的目标密钥环：

```c
long keyctl(KEYCTL_SET_REQKEY_KEYRING, int reqkey_defl);
```

这会设置当前线程下隐式请求的密钥将被附着的默认密钥环。`reqkey_defl`应为以下常量之一：

| 常量                       | 值   | 新的默认密钥环             |
|------------------------|-----|----------------------------|
| `KEY_REQKEY_DEFL_NO_CHANGE` | -1 | 不改变                     |
| `KEY_REQKEY_DEFL_DEFAULT`   | 0  | 默认[1]                    |
| `KEY_REQKEY_DEFL_THREAD_KEYRING` | 1 | 线程密钥环                 |
| `KEY_REQKEY_DEFL_PROCESS_KEYRING` | 2 | 进程密钥环                 |
| `KEY_REQKEY_DEFL_SESSION_KEYRING` | 3 | 会话密钥环                 |
| `KEY_REQKEY_DEFL_USER_KEYRING` | 4 | 用户密钥环                 |
| `KEY_REQKEY_DEFL_USER_SESSION_KEYRING` | 5 | 用户会话密钥环             |
| `KEY_REQKEY_DEFL_GROUP_KEYRING` | 6 | 组密钥环                   |

如果成功，则返回旧的默认值；如果`reqkey_defl`不是上述值之一，则返回`EINVAL`错误。
默认密钥环可以通过传递给`request_key()`系统调用的密钥环来覆盖。
请注意，此设置在`fork/exec`过程中是继承的。
默认情况下：如果存在，则使用线程密钥环；否则，如果存在，则使用进程密钥环；否则，如果存在，则使用会话密钥环；否则，使用用户默认的会话密钥环。

* 为密钥设置超时时间:

    long keyctl(KEYCTL_SET_TIMEOUT, key_serial_t key, unsigned timeout);

    这将设置或清除一个密钥上的超时时间。超时时间可以是0以清除超时，或者是一个秒数，用于设定在未来的某个时刻过期。
    
    进程必须对密钥具有属性修改访问权限才能设置其超时时间。此函数不允许对负值、已撤销或已过期的密钥设置超时时间。

* 假设创建密钥所授予的权限:

    long keyctl(KEYCTL_ASSUME_AUTHORITY, key_serial_t key);

    这将假设或撤销创建指定密钥所需的权限。只有当线程在其密钥环中某处关联有与指定密钥对应的授权密钥时，才能假设权限。

    一旦假设了权限，对于密钥的搜索也将使用请求者的安全标签、UID、GID和组来搜索请求者的密钥环。

    如果请求的权限不可用，将会返回错误EPERM；同样地，如果因为目标密钥已经被创建而权限被撤销，也会返回该错误。

    如果指定的密钥为0，则任何假设的权限都将被撤销。

    假设的授权密钥将在fork和exec调用中继承。

* 获取附加到密钥的LSM安全上下文:

    long keyctl(KEYCTL_GET_SECURITY, key_serial_t key, char *buffer,
                size_t buflen)

    此函数返回一个字符串，表示附加到密钥的LSM安全上下文，该字符串存放在提供的缓冲区中。

    除非出现错误，它总是返回能够生成的数据量，即使这些数据对缓冲区来说过大，但它不会向用户空间复制超过请求的数据量。如果缓冲区指针为NULL，则不会发生复制操作。
如果缓冲区足够大，则在字符串末尾包含一个NUL字符。这个NUL字符被计入返回的计数中。如果没有强制执行LSM（Least Significant Modulus，此处可能指某种安全模块），则将返回一个空字符串。
要使此功能成功，进程必须对键具有查看权限。
* 安装调用进程的会话密钥环到其父进程上：

    long keyctl(KEYCTL_SESSION_TO_PARENT);

    此函数尝试将调用进程的会话密钥环安装到调用进程的父进程上，并替换父进程当前的会话密钥环。
调用进程必须与其父进程具有相同的拥有者，密钥环必须与调用进程具有相同的拥有者，调用进程必须对密钥环具有LINK权限，并且活动的LSM模块不得拒绝权限，否则将返回错误EPERM。
如果内存不足完成操作，则返回错误ENOMEM，否则返回0表示成功。
下一次父进程离开内核并恢复执行用户空间时，密钥环将被替换。
* 使一个密钥失效：

    long keyctl(KEYCTL_INVALIDATE, key_serial_t key);

    此函数标记一个密钥为失效状态，然后唤醒垃圾收集器。垃圾收集器立即从所有密钥环中移除已失效的密钥，并在其引用计数达到零时删除该密钥。
被标记为失效的密钥立刻对正常的密钥操作变得不可见，尽管它们仍然可以在/proc/keys中可见，直到被删除（它们会被标记为'i'标志）。
要使此功能成功，进程必须对密钥具有搜索权限。
* 计算Diffie-Hellman共享秘密或公钥：

    long keyctl(KEYCTL_DH_COMPUTE, struct keyctl_dh_params *params,
                char *buffer, size_t buflen, struct keyctl_kdf_params *kdf);

    `params`结构体包含三个密钥的序列号：

    - 素数p，双方皆知
    - 本地私钥
    - 基数整数，它要么是一个共享生成器，要么是远程公钥

    计算的值为：

    result = base ^ private (mod prime)

    如果基数是共享生成器，则结果是本地公钥。如果基数是远程公钥，则结果是共享秘密。
如果参数 `kdf` 为 `NULL`，则适用以下规则：

- 缓冲区长度必须至少等于素数的长度，或者为零。
- 如果缓冲区长度非零，则当结果成功计算并复制到缓冲区时返回结果的长度。当缓冲区长度为零时，返回所需的最小缓冲区长度。

参数 `kdf` 允许调用者在Diffie-Hellman运算上应用密钥派生函数（KDF），其中仅返回KDF的结果。KDF通过结构体 `struct keyctl_kdf_params` 进行如下描述：

- `char *hashname` 指定从内核加密API中使用的散列标识符的NUL终止字符串，并用于KDF操作。KDF实现符合SP800-56A以及SP800-108（计数器KDF）。
- `char *otherinfo` 指定根据SP800-56A第5.8.1.2节文档中的OtherInfo数据。该缓冲区的长度由 `otherinfolen` 给出。OtherInfo的格式由调用者定义。

如果不需要使用OtherInfo，`otherinfo` 指针可以为 `NULL`。

此函数会在密钥类型不支持时返回错误 `EOPNOTSUPP`，无法找到密钥时返回错误 `ENOKEY`，密钥对调用者不可读时返回错误 `EACCES`。此外，如果参数 `kdf` 非 `NULL` 并且缓冲区长度或OtherInfo长度超过允许的长度时，函数将返回 `EMSGSIZE` 错误。

* 限制密钥环链接 ::
  
  long keyctl(KEYCTL_RESTRICT_KEYRING, key_serial_t keyring,
	      const char *type, const const char *restriction);

  现有的密钥环可以通过评估密钥的内容来限制额外密钥的链接，依据某种限制方案。
  
  `"keyring"` 是要施加限制的现有密钥环的密钥ID。它可以为空，也可以已经包含链接的密钥。即使新的限制会拒绝它们，已链接的密钥仍将保留在密钥环中。
  `"type"` 是一个注册的密钥类型。
  `"restriction"` 是一个字符串，描述了如何限制密钥的链接。
格式会根据密钥类型的不同而变化，且该字符串将传递给针对请求类型的`lookup_restriction()`函数。它可能指定了用于限制的方法及其相关数据，例如签名验证或对密钥负载的约束。如果请求的密钥类型之后被注销，则在移除密钥类型后无法向密钥环中添加任何密钥。
要应用密钥环限制，进程必须具有设置属性权限，并且密钥环之前不能已经被限制。
受限密钥环的一个应用是使用非对称密钥类型来验证X.509证书链或单个证书签名。
请参阅Documentation/crypto/asymmetric-keys.rst以了解适用于非对称密钥类型的特定限制。

* 查询非对称密钥::

    long keyctl(KEYCTL_PKEY_QUERY,
                key_serial_t key_id, unsigned long reserved,
                const char *params,
                struct keyctl_pkey_query *info);

获取有关非对称密钥的信息。可以通过`params`参数查询特定算法和编码。这是一个包含键值对的空间分隔或制表符分隔的字符串。
目前支持的键包括`enc`和`hash`。信息返回在`keyctl_pkey_query`结构体中::

    __u32   supported_ops;
    __u32   key_size;
    __u16   max_data_size;
    __u16   max_sig_size;
    __u16   max_enc_size;
    __u16   max_dec_size;
    __u32   __spare[10];

`supported_ops`包含一个位掩码标志，指示支持哪些操作。这是通过按位或运算构建的，包括以下内容::

    KEYCTL_SUPPORTS_{ENCRYPT,DECRYPT,SIGN,VERIFY}

`key_size`表示密钥大小（以比特为单位）。
`max_*_size`表示要签名的数据块、签名数据块、要加密的数据块和要解密的数据块的最大大小（以字节为单位）。
`__spare[]`必须设为0。这预留用于将来传递解锁密钥所需的密码短语。
如果成功，返回0。如果密钥不是非对称密钥，则返回EOPNOTSUPP。

* 使用非对称密钥加密、解密、签名或验证数据块::

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

使用非对称密钥对数据块执行公钥加密操作。对于加密和验证，非对称密钥可能只需要公开部分即可，但对于解密和签名则还需要私有部分。
参数块 `params` 包含了多个整数值：

    __s32     key_id;
    __u32     in_len;
    __u32     out_len;
    __u32     in2_len;

`key_id` 是要使用的非对称密钥的ID。`in_len` 和 `in2_len` 表示输入缓冲区 `in` 和 `in2` 中的数据量，而 `out_len` 表示输出缓冲区的大小，适用于上述操作。
对于特定的操作，输入和输出缓冲区的使用方式如下：

| 操作ID | 输入, in_len | 输出, out_len | 输入2, in2_len |
|--------|--------------|--------------|---------------|
| KEYCTL_PKEY_ENCRYPT | 原始数据 | 加密后的数据 | - |
| KEYCTL_PKEY_DECRYPT | 加密后的数据 | 原始数据 | - |
| KEYCTL_PKEY_SIGN | 原始数据 | 签名 | - |
| KEYCTL_PKEY_VERIFY | 原始数据 | - | 签名 |

`info` 是一个键值对字符串，提供补充信息。这些包括：

- `enc=<encoding>`：加密或签名块的编码。这可以是 "pkcs1" 对应于 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5；"pss" 对应于 "RSASSA-PSS"；"oaep" 对应于 "RSAES-OAEP"。如果省略或者设置为 "raw"，则指定加密函数的原始输出。
- `hash=<algo>`：如果数据缓冲区包含哈希函数的输出，并且编码中包含有关所用哈希函数的指示，则可以通过此参数指定哈希函数，例如 "hash=sha256"。

参数块中的 `__spare[]` 空间必须被设置为 0。这是为了多种目的，其中包括允许传递用于解锁密钥所需的密码短语。

如果成功，加密、解密和签名操作都会返回写入输出缓冲区的数据量。验证操作在成功时返回 0。

* 监听密钥或密钥环的变化：

        long keyctl(KEYCTL_WATCH_KEY, key_serial_t key, int queue_fd,
                    const struct watch_notification_filter *filter);

这将为指定的密钥或密钥环设置或移除监听。

"key" 是要监听的密钥的ID。
"queue_fd" 是指向已打开管道的文件描述符，该管道管理着接收通知的缓冲区。
"filter" 要么为NULL以移除监听，要么是一个过滤器规范，用来表明从密钥中需要哪些事件。

更多信息，请参阅文档 `Documentation/core-api/watch_queue.rst`。
请注意，对于任何特定的{key, queue_fd}组合，只能设置一个监视器。
通知记录的结构如下：

    ```c
    struct key_notification {
        struct watch_notification watch;
        __u32 key_id;
        __u32 aux;
    };
    ```

在此结构中，`watch::type`将被设置为"WATCH_TYPE_KEY_NOTIFY"，子类型将是以下之一：

- NOTIFY_KEY_INSTANTIATED
- NOTIFY_KEY_UPDATED
- NOTIFY_KEY_LINKED
- NOTIFY_KEY_UNLINKED
- NOTIFY_KEY_CLEARED
- NOTIFY_KEY_REVOKED
- NOTIFY_KEY_INVALIDATED
- NOTIFY_KEY_SETATTR

这些分别表示键被实例化/拒绝、更新、在键环中创建链接、从键环中移除链接、清空键环、撤销键、使键失效或键的一个属性发生变化（用户、组、权限、超时时间、限制）。
如果被监视的键被删除，则会发出一个基本的`watch_notification`，其中"type"被设置为WATCH_TYPE_META，"subtype"被设置为watch_meta_removal_notification。监视点ID将在"info"字段中设置。

这需要通过启用以下选项来配置：

- "提供键/键环更改通知" (KEY_NOTIFICATIONS)

### 内核服务
####

内核提供的键管理服务相对简单，可以分为两个方面：键和键类型。

处理键相当直接。首先，内核服务注册其类型，然后搜索该类型的键。只要需要使用该键，就应该保持对该键的持有，并在不再需要时释放它。对于文件系统或设备文件，可能在打开调用期间执行搜索，并在关闭时释放键。如何处理由于两个不同用户打开同一文件导致的冲突键的问题留给文件系统作者解决。

为了访问键管理器，需要包含以下头文件：

```c
#include <linux/key.h>
```

特定的键类型应该有一个位于`include/keys/`目录下的头文件，用于访问该类型。例如，对于类型为"user"的键，应包含：

```c
#include <keys/user-type.h>
```

需要注意的是，可能会遇到两种不同类型的指向键的指针：

1. `struct key *`

   这个仅仅指向键结构本身。键结构至少是四字节对齐的。

2. `key_ref_t`

   这与`struct key *`等价，但是最低有效位被设置以表示调用者“拥有”该键。“拥有”意味着调用进程在其键环之一中有一个可搜索的链接到该键。有三个函数用于处理这些：

   ```c
   key_ref_t make_key_ref(const struct key *key, bool possession);

   struct key *key_ref_to_ptr(const key_ref_t key_ref);

   bool is_key_possessed(const key_ref_t key_ref);
   ```

   第一个函数根据键指针和拥有信息（必须为true或false）构造一个键引用。
   
   第二个函数从引用中获取键指针，第三个函数获取拥有标志。

当访问键的有效载荷内容时，必须采取一些预防措施以防止访问与修改之间的竞争。有关更多信息，请参阅“访问有效载荷内容的注意事项”部分。

要搜索一个键，可以调用：

```c
struct key *request_key(const struct key_type *type,
                        const char *description,
                        const char *callout_info);
```

此函数用于请求一个描述符与指定描述符匹配的键或键环，匹配方式依据键类型的方法`match_preparse()`。这允许进行近似匹配。如果`callout_info`不为NULL，则会调用`/sbin/request-key`试图从用户空间获取该键。在这种情况下，`callout_info`将作为参数传递给程序。
如果该函数调用失败，将返回错误 `ENOKEY`、`EKEYEXPIRED` 或 `EKEYREVOKED`。
如果成功，则密钥将被附加到默认的密钥环中，这是通过 `KEYCTL_SET_REQKEY_KEYRING` 设置的，用于隐式获取的 `request-key` 密钥。
更多信息请参阅文档 `Documentation/security/keys/request-key.rst`

* 要在一个特定域中查找密钥，请调用：

```c
struct key *request_key_tag(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag,
                            const char *callout_info);
```

这与 `request_key()` 相同，只是可以指定一个域标签，该标签使得搜索算法仅匹配符合该标签的密钥。`domain_tag` 可以是 `NULL`，表示一个与任何指定域分开的全局域。

* 若要查找密钥，并向回调函数传递辅助数据，请调用：

```c
struct key *request_key_with_auxdata(const struct key_type *type,
                                     const char *description,
                                     struct key_tag *domain_tag,
                                     const void *callout_info,
                                     size_t callout_len,
                                     void *aux);
```

这与 `request_key_tag()` 相同，只是如果存在的话，辅助数据会传递给 `key_type->request_key()` 函数，而 `callout_info` 是长度为 `callout_len` 的数据块（如果给出的话，其长度可能为0）。

* 若要在 RCU 条件下查找密钥，请调用：

```c
struct key *request_key_rcu(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag);
```

这类似于 `request_key_tag()`，但不会检查正在构建中的密钥，而且如果找不到匹配项，也不会调用用户空间来构建密钥。

* 当不再需要密钥时，应使用以下方法释放它：

```c
void key_put(struct key *key);
```

或者

```c
void key_ref_put(key_ref_t key_ref);
```

这些函数可以在中断上下文中调用。如果未设置 `CONFIG_KEYS`，则不会解析参数。

* 可以通过调用以下函数之一来增加对密钥的引用计数：

```c
struct key *__key_get(struct key *key);
struct key *key_get(struct key *key);
```

通过这些函数增加引用计数的密钥，在使用完毕后需要调用 `key_put()` 来释放。传入的密钥指针会被返回。

对于 `key_get()`，如果指针为 `NULL` 或者未设置 `CONFIG_KEYS`，则不会递增引用计数。

* 可以通过以下函数获取密钥的序列号：

```c
key_serial_t key_serial(struct key *key);
```

如果 `key` 为 `NULL` 或者未设置 `CONFIG_KEYS`，则返回 0（在这种情况下，不会解析参数）。
如果在搜索中找到了密钥环，可以通过以下函数进一步搜索：

```c
key_ref_t keyring_search(key_ref_t keyring_ref,
			 const struct key_type *type,
			 const char *description,
			 bool recurse)
```

此函数搜索指定的密钥环（当`recurse == false`时）或密钥环树（当`recurse == true`时），以查找匹配的密钥。如果失败，会返回错误`ENOKEY`（可以使用`IS_ERR/PTR_ERR`来确定）。如果成功，则需要释放返回的密钥。
来自密钥环引用的拥有属性用于通过权限掩码控制访问，并且如果成功则会传播到返回的密钥引用指针。

* 密钥环可以通过以下方式创建：

```c
struct key *keyring_alloc(const char *description, uid_t uid, gid_t gid,
			  const struct cred *cred,
			  key_perm_t perm,
			  struct key_restriction *restrict_link,
			  unsigned long flags,
			  struct key *dest);
```

这会创建一个具有给定属性的密钥环并返回它。如果`dest`不为`NULL`，新密钥环将链接到它所指向的密钥环中。不对目标密钥环进行权限检查。
如果密钥环会超出配额限制，则可以返回错误`EDQUOT`（如果密钥环不应计入用户的配额，请在`flags`中传递`KEY_ALLOC_NOT_IN_QUOTA`）。也可能返回错误`ENOMEM`。
如果`restrict_link`不为`NULL`，则应指向一个结构，其中包含每次尝试将密钥链接到新密钥环时将被调用的函数。该结构还可以包含一个密钥指针和关联的密钥类型。该函数被调用来检查是否可以将密钥添加到密钥环中。如果给定的密钥类型未注册，密钥类型会被垃圾回收器用来清理此结构中的函数或数据指针。内核中的`key_create_or_update()`调用者可以传递`KEY_ALLOC_BYPASS_RESTRICTION`来跳过此检查。
使用此功能的一个示例是管理在内核启动时设置的加密密钥环，同时允许用户空间添加密钥——前提是它们可以通过内核已有的密钥验证。
调用时，限制函数将传入要添加的密钥环、密钥类型、要添加的密钥的有效载荷以及用于限制检查的数据。请注意，在创建新密钥时，这会在有效载荷预解析和实际密钥创建之间调用。该函数应返回0以允许链接，或返回一个错误以拒绝链接。
存在一个便利函数`restrict_link_reject`，在此情况下始终返回`-EPERM`。

* 要检查密钥的有效性，可以调用以下函数：

```c
int validate_key(struct key *key);
```

此函数检查所讨论的密钥是否已过期或被撤销。如果密钥无效，则返回错误`EKEYEXPIRED`或`EKEYREVOKED`。如果密钥为`NULL`或者没有设置`CONFIG_KEYS`，则返回0（在后一种情况下，不会解析参数）。

* 要注册密钥类型，应调用以下函数：

```c
int register_key_type(struct key_type *type);
```

如果同名类型的密钥已经存在，则此函数将返回错误`EEXIST`。
* 要取消注册密钥类型，请调用：

```c
void unregister_key_type(struct key_type *type);
```

在某些情况下，可能需要处理一组密钥。为此提供了一种访问密钥环类型的机制来管理这样的一组密钥：

```c
struct key_type key_type_keyring;
```

这可以与 `request_key()` 等函数一起使用，以查找进程中的特定密钥环。找到的密钥环可以使用 `keyring_search()` 进行搜索。需要注意的是，无法使用 `request_key()` 来直接搜索特定的密钥环，因此这种方式的应用范围有限。

### 访问负载内容说明

####

最简单的负载只是直接存储在 `key->payload` 中的数据。在这种情况下，访问负载时无需进行 RCU 或加锁操作。
更复杂的负载内容必须分配内存，并将其指针设置在 `key->payload.data[]` 数组中。必须选择以下方法之一来访问数据：

1. **不可修改的密钥类型**
   如果密钥类型没有修改方法，则可以在没有任何形式锁定的情况下访问密钥的负载，前提是已知该密钥是实例化的（未实例化的密钥不能被“找到”）。
   
2. **密钥的信号量**
   可以使用信号量来控制对负载的访问和负载指针的控制。对于修改操作，必须写锁；对于一般访问，需要读锁。这样做不利之处在于访问者可能需要等待。
   
3. **RCU**
   当未持有信号量时，必须使用 RCU；如果已经持有信号量，则由于信号量仍然用于序列化对密钥的修改，所以内容不会意外改变。密钥管理代码为密钥类型处理了这一点。
   
   这意味着要使用：
   
   ```c
   rcu_read_lock() ... rcu_dereference() ... rcu_read_unlock()
   ```
   
   来读取指针，并使用：
   
   ```c
   rcu_dereference() ... rcu_assign_pointer() ... call_rcu()
   ```
   
   在一个宽限期后设置指针并清理旧的内容。
请注意，只有密钥类型应该修改密钥的有效载荷。
此外，RCU（Read-Copy-Update）控制的有效载荷必须持有用于调用`call_rcu()`的`struct rcu_head`，并且如果有效载荷是可变大小的，还需要持有有效载荷的长度。不能依赖`key->datalen`来与刚刚取消引用的有效载荷保持一致，除非持有密钥的信号量。

请注意`key->payload.data[0]`有一个标记为__rcu使用的影子副本。这被称为`key->payload.rcu_data0`。以下访问器封装了对此元素的RCU调用：

a) 设置或更改第一个有效载荷指针：

```c
    rcu_assign_keypointer(struct key *key, void *data);
```

b) 在持有密钥信号量的情况下读取第一个有效载荷指针：

```c
    [const] void *dereference_key_locked([const] struct key *key);

    注意返回值将继承自密钥参数的const属性。如果静态分析认为锁没有被持有，将会给出错误。
```

c) 在持有RCU读锁的情况下读取第一个有效载荷指针：

```c
    const void *dereference_key_rcu(const struct key *key);
```

定义密钥类型
=============

内核服务可能想要定义自己的密钥类型。例如，AFS文件系统可能想要定义一个Kerberos 5票据密钥类型。为此，实现者需要填充一个`key_type`结构，并将其注册到系统中。
实现密钥类型的源文件应包含以下头文件：

```c
    #include <linux/key-type.h>
```

该结构体有许多字段，其中一些是必需的：

  * `const char *name`

    密钥类型的名称。这用于将用户空间提供的密钥类型名称转换为指向该结构体的指针。
* `size_t def_datalen`

    这个字段是可选的——它提供了作为配额贡献的默认有效载荷数据长度。如果密钥类型的有效载荷总是或几乎总是相同的大小，那么这是一种更高效的做法。
对于特定密钥的数据长度（和配额），总是在实例化或更新时通过调用以下函数进行更改：

```c
    int key_payload_reserve(struct key *key, size_t datalen);
```

带有修订后的数据长度。如果不可行，将返回EDQUOT错误。
* `int (*vet_description)(const char *description);`

    这个可选方法用于审核密钥描述。如果密钥类型不接受密钥描述，则可以返回一个错误，否则应返回0。
* `int (*preparse)(struct key_preparsed_payload *prep);`

    这个可选方法允许密钥类型在创建密钥（添加密钥）或获取密钥信号量（更新或实例化密钥）之前尝试解析有效载荷。`prep`指向的结构体如下所示：

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

在调用此方法之前，调用者会使用有效载荷块参数填充`data`和`datalen`；`quotalen`将使用来自密钥类型的默认配额大小填充；`expiry`将设置为`TIME_T_MAX`，其余部分将被清空。
如果可以从有效载荷内容中提出描述，则应将其附加为字符串到`description`字段。如果`add_key()`的调用者传递NULL或""，则将使用此描述作为密钥描述。
该方法可以将任何它想要的内容附加到负载中。这仅仅被传递给`instantiate()`或`update()`操作。如果设置了过期时间，则当从这些数据实例化密钥时，会将过期时间应用到该密钥上。

该方法在成功时应返回0，否则返回一个负的错误代码。

*  ``void (*free_preparse)(struct key_preparsed_payload *prep);``

    此方法仅在提供了`preparse()`方法的情况下才需要，否则它将不会被使用。此方法清理由`preparse()`方法填充的`key_preparsed_payload`结构中的描述和负载字段所附带的任何内容。无论`instantiate()`或`update()`是否成功，只要`preparse()`方法成功返回后，此方法总会被调用。

*  ``int (*instantiate)(struct key *key, struct key_preparsed_payload *prep);``

    此方法在构建密钥时被调用以将负载附加到密钥上。
    所附加的负载不一定与传递给此函数的数据有关。
    `prep->data`和`prep->datalen`字段定义了原始的负载块。如果提供了`preparse()`方法，则还可能填充其他字段。
    如果附加到密钥上的数据量与`keytype->def_datalen`中的大小不同，则应调用`key_payload_reserve()`。
    此方法不需要锁定密钥以附加负载。
    由于`KEY_FLAG_INSTANTIATED`标志未设置在`key->flags`中，因此可以防止其他操作访问该密钥。
    在此方法中进行休眠是安全的。
`generic_key_instantiate()` 函数被提供用于简单地将数据从 `prep->payload.data[]` 复制到 `key->payload.data[]`，并对第一个元素进行 RCU 安全的赋值。之后它会清除 `prep->payload.data[]`，以确保 `free_preparse` 方法不会释放这些数据。

```
int (*update)(struct key *key, const void *data, size_t datalen);
```

如果这种类型的密钥可以更新，则应提供此方法。它被调用来根据提供的数据块更新密钥的有效负载。`prep->data` 和 `prep->datalen` 字段定义了原始的有效负载块。如果提供了 `preparse()`，则可能还会填充其他字段。在实际做出更改之前，如果数据长度可能会发生变化，应调用 `key_payload_reserve()`。需要注意的是，如果这一步成功，类型就承诺要改变密钥，因为它已经被修改过了，因此所有内存分配都必须先完成。
在调用此方法之前，密钥的信号量会被写锁定，但这只能阻止其他写入者；对密钥有效负载的任何更改都必须在 RCU 条件下进行，并且必须使用 `call_rcu()` 来处理旧的有效负载。
应在做出更改之前调用 `key_payload_reserve()`，但在所有分配和其他可能导致失败的函数调用之后。
在此方法中睡眠是安全的。

```
int (*match_preparse)(struct key_match_data *match_data);
```

此方法是可选的。当即将执行密钥搜索时，会调用此方法。它接收如下结构体：

```c
struct key_match_data {
    bool (*cmp)(const struct key *key,
                const struct key_match_data *match_data);
    const void *raw_data;
    void *preparsed;
    unsigned lookup_type;
};
```

在进入时，`raw_data` 指向调用者用于匹配密钥的标准，不应对其进行修改。`(*cmp)()` 指向默认匹配函数（该函数根据 `raw_data` 进行精确描述匹配），而 `lookup_type` 将设置为指示直接查找。
以下 `lookup_type` 值可用：

   * `KEYRING_SEARCH_LOOKUP_DIRECT` — 直接查找通过散列类型和描述来缩小搜索范围至少量密钥。
* `KEYRING_SEARCH_LOOKUP_ITERATE` - 迭代查找会遍历密钥环中的所有密钥，直到找到匹配的密钥。这必须用于任何不是直接通过密钥描述进行简单匹配的搜索。
方法可以设置 `cmp` 指向一个自选的函数来进行其他形式的匹配，可以将 `lookup_type` 设置为 `KEYRING_SEARCH_LOOKUP_ITERATE`，并且可以附加一些内容到预解析（preparsed）指针上供 `(*cmp)()` 使用。
`(*cmp)()` 应当在找到匹配密钥时返回真，否则返回假。
如果设置了预解析（preparsed），可能需要使用 `match_free()` 方法来清理它。
该方法应当在成功时返回 0，或者在失败时返回负的错误码。
允许在此方法中睡眠，但 `(*cmp)()` 不允许睡眠，因为此时持有锁。
如果没有提供 `match_preparse()`，则该类型的密钥将根据其描述进行精确匹配。

* `void (*match_free)(struct key_match_data *match_data);`

    此方法是可选的。如果提供了此方法，则会在成功调用 `match_preparse()` 后调用它来清理 `match_data->preparsed`。

* `void (*revoke)(struct key *key);`

    此方法是可选的。它被调用来丢弃密钥被撤销时的部分有效负载数据。调用者将对密钥信号量进行写锁定。
在此方法中睡眠是安全的，但需要注意避免与密钥信号量产生死锁。
* `void (*destroy)(struct key *key);`

    该方法是可选的。当一个密钥被销毁时，此方法会被调用以丢弃密钥的有效载荷数据。
    
    此方法无需锁定密钥来访问有效载荷；此时可以认为密钥已经无法访问。请注意，在调用此函数之前，密钥的类型可能已经被更改。
    
    在此方法中睡眠是不安全的；调用者可能持有自旋锁。

* `void (*describe)(const struct key *key, struct seq_file *p);`

    该方法是可选的。在读取 `/proc/keys` 时，此方法会被调用来以文本形式总结密钥的描述和有效载荷。
    
    此方法将在持有 RCU 读锁的情况下被调用。如果要访问有效载荷，则应使用 `rcu_dereference()` 来读取有效载荷指针。不能信任 `key->datalen` 与有效载荷内容保持一致。
    
    描述不会改变，尽管密钥的状态可能会改变。
    
    在此方法中睡眠是不安全的；RCU 读锁由调用者持有。

* `long (*read)(const struct key *key, char __user *buffer, size_t buflen);`

    该方法是可选的。此方法由 `KEYCTL_READ` 调用来将密钥的有效载荷转换为用户空间处理的数据块。
    
    理想情况下，数据块应该与传递给实例化和更新方法中的格式相同。
    
    如果成功，应返回可以生成的数据块大小，而不是已复制的大小。
此方法将在键的信号量被读锁定的情况下被调用。这将防止键的负载发生变化。访问键的负载时，没有必要使用RCU锁。在此方法中睡眠是安全的，例如，在访问用户空间缓冲区时可能会发生这种情况。
```c
int (*request_key)(struct key_construction *cons, const char *op, void *aux);
```

此方法是可选的。如果提供，`request_key()`及其相关函数将调用这个函数，而不是上层调用到 `/sbin/request-key` 来处理这种类型的键。
参数 `aux` 是传递给 `request_key_async_with_auxdata()` 或类似函数的，如果不是通过这些函数传递则为 `NULL`。同时传递的还有要操作的键的构造记录和操作类型（目前只有 "create"）。

此方法可以在上层调用完成前返回，但无论成功与否、无论是否有错误，都必须在所有情况下调用以下函数以完成实例化过程：
```c
void complete_request_key(struct key_construction *cons, int error);
```

错误参数在成功时应为0，在出错时应为负值。此动作会销毁构造记录，并撤销授权键。如果指示有错误，则正在构建的键如果没有已经被实例化的话，将会被负向实例化。

如果此方法返回错误，该错误将返回给 `request_key*()` 的调用者。在返回之前必须调用 `complete_request_key()`。

正在构建的键和授权键可以在由 `cons` 指向的 `key_construction` 结构体中找到：

```c
struct key *key;  // 正在构建的键
struct key *authkey;  // 授权键
```

```c
struct key_restriction *(*lookup_restriction)(const char *params);
```

此可选方法用于启用用户空间配置密钥环限制。传递限制参数字符串（不包括键类型名称），此方法返回指向包含评估每个尝试的键链接操作的相关函数和数据的 `key_restriction` 结构体指针。如果没有匹配项，则返回 `-EINVAL`。

```c
asym_eds_op` 和 `asym_verify_signature`
```

这两个方法是可选的。如果提供，第一个允许使用键来加密、解密或签名一段数据，第二个允许使用键验证签名。
在所有情况下，以下信息在 `params` 块中提供：

```c
struct kernel_pkey_params {
    struct key *key;  // 要使用的键
    const char *encoding;  // 使用的编码方式（例如，"pkcs1" 可能与 RSA 键一起使用，表示 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5 编码或 "raw" 如果没有编码）
    const char *hash_algo;  // 用于生成签名数据的哈希算法名称（如果适用）
    char *info;  // 额外信息
    __u32 in_len;  // 输入缓冲区大小
    union {
        __u32 out_len;  // 输出缓冲区大小
        __u32 in2_len;  // 第二个输入缓冲区大小
    };
    enum kernel_pkey_operation op : 8;  // 要执行的操作标识
};
```
对于给定的操作ID，输入和输出缓冲区的使用如下：

| 操作ID | 输入, in_len | 输出, out_len | 第二输入, in2_len |
|========|==============|==============|==================|
| kernel_pkey_encrypt | 原始数据 | 加密数据 | - |
| kernel_pkey_decrypt | 加密数据 | 原始数据 | - |
| kernel_pkey_sign | 原始数据 | 签名 | - |
| kernel_pkey_verify | 原始数据 | - | 签名 |

`asym_eds_op()` 根据 `params->op` 处理加密、解密和签名创建。需要注意的是，`params->op` 同样适用于 `asym_verify_signature()`。
- 加密和签名创建都将原始数据作为输入缓冲区的内容，并在输出缓冲区返回加密结果。如果设置了编码，则可能添加了填充。
- 在签名创建的情况下，根据编码，创建的填充可能需要指示摘要算法——其名称应提供在 `hash_algo` 中。
- 解密将加密数据作为输入缓冲区的内容，并在输出缓冲区返回原始数据。如果设置了编码，则会检查并移除填充。
- 验证将原始数据作为输入缓冲区的内容，并将签名作为第二输入缓冲区的内容，以检查二者是否匹配。将验证填充。根据编码，用于生成原始数据的摘要算法可能需要在 `hash_algo` 中指示。
- 如果成功，`asym_eds_op()` 应返回写入输出缓冲区的字节数。`asym_verify_signature()` 应返回 0。
- 可能返回多种错误，包括：`EOPNOTSUPP`（不支持该操作）；`EKEYREJECTED`（验证失败）；`ENOPKG`（所需密码功能不可用）。

`asym_query` 方法：

    ```c
    int (*asym_query)(const struct kernel_pkey_params *params,
                      struct kernel_pkey_query *info);
    ```

此方法是可选的。如果提供，则允许确定密钥中持有的公钥或非对称密钥的信息。
参数块与 `asym_eds_op()` 类似，但 `in_len` 和 `out_len` 未被使用。`encoding` 和 `hash_algo` 字段应该用于适当地减小返回的缓冲区/数据大小。
如果成功，以下信息将被填写：

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

`supported_ops` 字段包含一个位掩码，表示密钥支持的操作，包括加密、解密、签名创建和签名验证。定义了以下常量：

- `KEYCTL_SUPPORTS_ENCRYPT`
- `KEYCTL_SUPPORTS_DECRYPT`
- `KEYCTL_SUPPORTS_SIGN`
- `KEYCTL_SUPPORTS_VERIFY`

`key_size` 字段是密钥的大小（以比特为单位）。`max_data_size` 和 `max_sig_size` 是签名创建和验证的最大原始数据和签名大小；`max_enc_size` 和 `max_dec_size` 是加密和解密的最大原始数据和签名大小。`max_*_size` 字段以字节为单位进行度量。
如果成功，将返回 0。如果不支持该密钥，则返回 `EOPNOTSUPP`。
请求密钥回调服务
============================

为了创建一个新的密钥，内核将尝试执行以下命令行：

	/sbin/request-key create <key> <uid> <gid> \
		<threadring> <processring> <sessionring> <callout_info>

其中 `<key>` 是正在构建的密钥，而三个密钥环（threadring、processring 和 sessionring）是发起搜索的进程的进程密钥环。这些信息被包括进来有两个原因：

   1. 在其中一个密钥环中可能存在一个认证令牌，这是获取密钥所必需的，例如：Kerberos 的 Ticket-Granting Ticket。
   2. 新的密钥很可能应该缓存在其中一个环中。
该程序在尝试访问更多密钥之前应将其 UID 和 GID 设置为指定的值。然后它可以寻找特定用户的进程来处理该请求（可能是由桌面管理器如 KDE 桌面管理器放置到另一个密钥中的路径）。
该程序（或它调用的任何其他程序）应通过调用 `KEYCTL_INSTANTIATE` 或 `KEYCTL_INSTANTIATE_IOV` 完成密钥的构建，这同样允许它将密钥缓存在其中一个密钥环中（可能是在会话环中），然后再返回。或者，可以使用 `KEYCTL_NEGATE` 或 `KEYCTL_REJECT` 标记密钥为否定状态；这也允许密钥缓存在其中一个密钥环中。
如果返回时密钥仍处于未构建状态，则密钥将被标记为否定状态，并添加到会话密钥环中，并向密钥请求者返回错误。
辅助信息可由调用此服务的实体提供。这将作为 `<callout_info>` 参数传递。如果没有此类信息可用，则将传递 `-` 作为此参数。
类似地，内核可能会尝试更新已过期或即将过期的密钥，方法是执行：

	/sbin/request-key update <key> <uid> <gid> \
		<threadring> <processring> <sessionring>

在这种情况下，程序不需要实际将密钥附加到环上；提供这些环仅作参考之用。
垃圾回收
==================

对于类型已被移除的无效密钥，将由后台垃圾回收器尽快自动从指向它们的密钥环中解除链接并删除。
类似地，被撤销和已过期的密钥也将进行垃圾回收，但只有在一定时间后才会进行。这个时间以秒为单位设置在：

	/proc/sys/kernel/keys/gc_delay
