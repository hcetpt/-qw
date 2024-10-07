============================
内核密钥保留服务
============================

此服务允许加密密钥、身份验证令牌、跨域用户映射等在内核中缓存，以便文件系统和其他内核服务使用。
密钥环是被允许的；这是一种特殊的密钥类型，可以包含指向其他密钥的链接。每个进程都有三个标准的密钥环订阅，内核服务可以搜索这些订阅以查找相关的密钥。
通过启用以下选项来配置密钥服务：

    "安全选项"/"启用访问密钥保留支持" (CONFIG_KEYS)

本文档包含以下部分：

.. contents:: :local:


密钥概述
============

在此上下文中，密钥代表加密数据单元、身份验证令牌、密钥环等。这些在内核中由 `struct key` 表示。
每个密钥有多个属性：

    - 一个序列号
    - 一种类型
    - 一个描述（用于在搜索中匹配密钥）
    - 访问控制信息
    - 过期时间
    - 有效负载
    - 状态
* 每个密钥都会被分配一个类型为 `key_serial_t` 的序列号，在该密钥的生命周期内是唯一的。所有序列号都是正的非零32位整数。
用户空间程序可以使用密钥的序列号作为访问它的方法，但需经过权限检查。

* 每个密钥都有一个定义好的“类型”。类型必须由内核服务（如文件系统）在内核中注册后，才能添加或使用该类型的密钥。用户空间程序不能直接定义新的类型。
密钥类型在内核中通过 `struct key_type` 表示，它定义了对该类型密钥可执行的一系列操作。
如果某个类型从系统中移除，那么所有该类型的密钥将失效。

* 每个密钥都有一个描述。这应该是一个可打印的字符串。密钥类型提供了一个用于匹配密钥描述和标准字符串的操作。

* 每个密钥都有一个拥有者用户ID、一个组ID和一个权限掩码。这些用于控制用户空间中的进程对密钥的操作权限，以及内核服务能否找到该密钥。

* 每个密钥可以通过其类型的实例化函数设置一个特定的过期时间。密钥也可以是永不过期的。

* 每个密钥可以有一个负载。这个负载表示实际的“密钥”数据。例如，在密钥环的情况下，它是密钥环链接的一系列密钥列表；在用户自定义密钥的情况下，它是一块任意的数据。
拥有负载不是必需的，并且实际上，负载可以只是存储在 `struct key` 中的一个值。
当一个密钥被实例化时，会调用该密钥类型的实例化函数，并传入一段数据，然后以某种方式创建密钥的有效载荷。
同样地，当用户空间希望读取密钥的内容（如果被允许的话），另一个密钥类型的操作将被调用，将密钥的附带有效载荷转换回一段数据。

每个密钥可以处于以下几种基本状态之一：

- 未实例化。密钥存在，但没有附带任何数据。从用户空间请求的密钥将处于这种状态。
- 实例化。这是正常状态。密钥是完整的，并且附带有数据。
- 负状态。这是一种相对短暂的状态。密钥充当一个标记，表示先前对用户空间的调用失败，并作为密钥查找的节流器。负状态的密钥可以更新为正常状态。
- 过期。密钥可以设置生命周期。如果其生命周期超出，则进入此状态。过期的密钥可以更新回正常状态。
- 吊销。密钥由用户空间操作置于这种状态。它无法被找到或操作（除了解除链接）。
- 无效。密钥的类型被注销，因此密钥现在无用。 

处于最后三种状态的密钥将被垃圾回收。详见“垃圾回收”部分。
关键服务概述
====================

除了提供密钥功能外，关键服务还提供了以下几种特性：

  * 关键服务定义了三种特殊的密钥类型：
     (+) “密钥环（keyring）”

	 密钥环是一种包含其他密钥列表的特殊密钥。可以通过各种系统调用来修改密钥环列表。创建密钥环时不应为其指定负载。
(+) “用户（user）”

	 这种类型的密钥具有描述和负载，它们是一些任意的数据块。这些密钥可以由用户空间创建、更新和读取，并且不打算用于内核服务。
(+) “登录（logon）”

	 与“用户”密钥类似，“登录”密钥也有一个任意数据块作为负载。它主要用于存储对内核可访问但对用户空间程序不可见的秘密信息。
描述可以是任意内容，但必须以非空字符串开头，该字符串描述了密钥的“子类”。子类与描述的其余部分之间用一个冒号（':'）分隔。“登录”密钥可以从用户空间创建和更新，但其负载仅在内核空间中可读。
* 每个进程订阅了三个密钥环：线程特定密钥环、进程特定密钥环和会话特定密钥环。
当发生任何形式的克隆（clone）、分叉（fork）、虚拟分叉（vfork）或执行（execve）时，子进程将丢弃线程特定密钥环。只有在需要时才会创建新的密钥环。
在克隆（clone）、分叉（fork）、虚拟分叉（vfork）时，除非提供了CLONE_THREAD标志，否则子进程中的进程特定密钥环将被替换为空的密钥环；execve也会丢弃进程的进程特定密钥环并创建一个新的。
会话特定密钥环在克隆、分叉、虚拟分叉和执行操作中保持不变，即使执行的是设置了用户ID或组ID的二进制文件。但是，进程可以使用PR_JOIN_SESSION_KEYRING来替换其当前的会话密钥环。允许请求一个匿名的新密钥环，或者尝试创建或加入一个具有特定名称的密钥环。
当线程的真实用户ID和组ID发生变化时，线程密钥环的所有权也随之改变。
* 系统中的每个用户ID都拥有两个特殊的密钥环：用户特定密钥环和默认用户会话密钥环。默认会话密钥环初始化时会链接到用户特定密钥环。
当一个进程更改其实际用户ID（UID）时，如果它之前没有会话密钥，则将订阅新UID的默认会话密钥。
如果一个进程试图访问其会话密钥但没有会话密钥，则将订阅其当前UID的默认会话密钥。
每个用户有两个配额来跟踪他们拥有的密钥。一个限制了密钥和密钥环的总数，另一个限制了可以消耗的描述和有效载荷空间的总量。
用户可以通过procfs文件查看这些和其他统计信息。root用户还可以通过sysctl文件修改配额限制（参见“新的procfs文件”部分）。
进程特定和线程特定的密钥环不计入用户的配额。
如果一个修改密钥或密钥环的系统调用会导致用户超过配额，则拒绝该操作并返回错误EDQUOT。
有一个系统调用接口，用户空间程序可以通过该接口创建和操作密钥及密钥环。
有一个内核接口，服务可以通过该接口注册类型并搜索密钥。
有一种方法可以让内核中的搜索回调到用户空间，请求在进程的密钥环中找不到的密钥。
有一个可选的文件系统，可以通过该文件系统查看和操作密钥数据库。
### 密钥访问权限

密钥具有所有者用户 ID、组访问 ID 和权限掩码。掩码最多为每个拥有者、用户、组和其他访问设置八位，但每组八位中只有六位是定义好的。这些授予的权限包括：

- **查看**

    这允许查看密钥或密钥环的属性——包括密钥类型和描述。
- **读取**

    这允许查看密钥的内容或密钥环中链接的密钥列表。
- **写入**

    这允许实例化或更新密钥的内容，或者允许添加或移除密钥环中的链接。
- **搜索**

    这允许搜索密钥环并找到密钥。搜索只能递归到设置了搜索权限的嵌套密钥环。
- **链接**

    这允许将密钥或密钥环进行链接。要从一个密钥环创建到另一个密钥的链接，进程必须对密钥环具有写入权限，并且对密钥具有链接权限。
- **设置属性**

    这允许更改密钥的 UID、GID 和权限掩码。对于更改所有权、组 ID 或权限掩码，拥有该密钥的所有权或具有系统管理员能力就足够了。

### SELinux 支持

安全类“key”已被添加到 SELinux 中，以便可以对在不同上下文中创建的密钥应用强制访问控制。此支持目前处于初步阶段，未来可能会有显著变化。

目前，所有上述基本权限在 SELinux 中也提供；SELinux 在执行所有基本权限检查之后被调用。

文件 `/proc/self/attr/keycreate` 的值会影响新创建密钥的标签。如果该文件的内容对应于 SELinux 安全上下文，则密钥将被分配该上下文。否则，密钥将被分配调用密钥创建请求的任务的当前上下文。任务必须被明确授予使用“创建”权限在密钥安全类中分配特定上下文的权利。
默认密钥环与用户相关联时，如果且仅如果登录程序在登录过程中正确地对 `keycreate` 进行了初始化，则这些密钥环将被标记为用户的默认上下文。否则，它们将被标记为登录程序本身的上下文。

然而，请注意，与 root 用户关联的默认密钥环会被标记为内核的默认上下文，因为它们是在启动过程的早期创建的，在 root 用户有机会登录之前。

与新线程关联的密钥环分别被标记为其关联线程的上下文，并且会话密钥环和进程密钥环的处理方式类似。

新的 ProcFS 文件
=================

已向 procfs 添加两个文件，管理员可以通过这些文件了解密钥服务的状态：

  * `/proc/keys`

    此文件列出了当前可由读取任务查看的所有密钥，提供了有关它们类型、描述和权限的信息。
    
    无法通过这种方式查看密钥的有效负载，但可能会提供一些相关信息。
    
    列表中只包含那些向读取进程授予 View 权限的密钥，无论该进程是否拥有这些密钥。请注意，LSM 安全检查仍然会执行，并可能进一步筛选掉当前进程无权查看的密钥。
    
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

    标志含义如下：
    
    - I：已实例化
    - R：已撤销
    - D：已失效
    - Q：计入用户的配额
    - U：正在通过回调到用户空间构建
    - N：负密钥

  * `/proc/key-users`

    此文件列出了系统上至少有一个密钥的每个用户的跟踪数据。此类数据包括配额信息和统计信息：

    ```
    [root@andromeda root]# cat /proc/key-users
    0:     46 45/45 1/100 13/10000
    29:     2 2/2 2/100 40/10000
    32:     2 2/2 2/100 40/10000
    38:     2 2/2 2/100 40/10000
    ```

    每行的格式如下：
    
    `<UID>`：适用于此用户的用户 ID
    
    `<usage>`：结构引用计数
    
    `<inst>/<keys>`：密钥总数及已实例化的数量
    
    `<keys>/<max>`：密钥数量配额
    
    `<bytes>/<max>`：密钥大小配额

还添加了四个新的 sysctl 文件，用于控制密钥的配额限制：

  * `/proc/sys/kernel/keys/root_maxkeys`
    `/proc/sys/kernel/keys/root_maxbytes`
    
    这些文件保存了 root 可拥有的最大密钥数量以及 root 可在这些密钥中存储的最大字节数量。
    
  * `/proc/sys/kernel/keys/maxkeys`
    `/proc/sys/kernel/keys/maxbytes`
    
    这些文件保存了每个非 root 用户可拥有的最大密钥数量以及每个用户可在其密钥中存储的最大字节数量。

root 可以通过向相应的文件写入每个新限制的十进制数字来修改这些值。

用户空间系统调用接口
===================

用户空间可以直接通过三个新的系统调用来操作密钥：`add_key`、`request_key` 和 `keyctl`。后者提供了多个用于操作密钥的功能。
当直接引用一个密钥时，用户空间程序应使用密钥的序列号（一个32位正整数）。然而，有一些特殊值可用于引用与调用进程相关的特殊密钥和密钥环：

	常量				值		引用的密钥
	==============================	======	===========================
	KEY_SPEC_THREAD_KEYRING			-1		线程特定密钥环
	KEY_SPEC_PROCESS_KEYRING		-2		进程特定密钥环
	KEY_SPEC_SESSION_KEYRING		-3		会话特定密钥环
	KEY_SPEC_USER_KEYRING			-4		UID特定密钥环
	KEY_SPEC_USER_SESSION_KEYRING		-5		UID-会话密钥环
	KEY_SPEC_GROUP_KEYRING			-6		GID特定密钥环
	KEY_SPEC_REQKEY_AUTH_KEY		-7		假设的request_key()授权密钥

主要的系统调用包括：

  * 创建一个新的指定类型的密钥，并赋予描述和有效负载，然后将其添加到指定的密钥环中：

	key_serial_t add_key(const char *type, const char *desc,
			     const void *payload, size_t plen,
			     key_serial_t keyring);

    如果密钥环中已经存在与提议创建的类型和描述相同的密钥，则此函数将尝试用给定的有效负载更新该密钥，或者如果该功能不被密钥类型支持则返回错误EEXIST。进程还必须具有写入要更新的密钥的权限。新密钥将拥有所有用户的权限，而没有组或第三方的权限。
    否则，这将尝试创建一个指定类型和描述的新密钥，并用提供的有效负载实例化它并将其附加到密钥环上。在这种情况下，如果进程没有写入密钥环的权限，则会产生错误。
    如果密钥类型支持的话，如果描述为空字符串或NULL，密钥类型将尝试从有效负载的内容生成描述。
    有效负载是可选的，如果类型不需要，指针可以为NULL。有效负载大小为plen，plen可以为零表示空有效负载。
    可以通过设置类型为"keyring"，密钥环名称作为描述（或NULL），并将有效负载设置为NULL来生成新的密钥环。
    用户定义的密钥可以通过指定类型"user"来创建。建议用户定义的密钥描述前缀加上类型ID和冒号，例如对于Kerberos 5票证授予票证，可以使用"krb5tgt:"。
    任何其他类型必须提前由内核服务（如文件系统）注册到内核。
    如果成功，返回新创建或更新的密钥的ID。

* 在进程的密钥环中搜索一个密钥，必要时调用用户空间创建它：

	key_serial_t request_key(const char *type, const char *description,
				 const char *callout_info,
				 key_serial_t dest_keyring);

    此函数按顺序在进程的所有密钥环中搜索匹配的密钥，顺序为线程、进程、会话。这非常类似于KEYCTL_SEARCH，包括可选地将发现的密钥附加到密钥环。
    如果找不到密钥，并且callout_info不为NULL，则将调用/sbin/request-key试图获取密钥。callout_info字符串将作为参数传递给程序。
为了将一个密钥链接到目标密钥环中，该密钥必须授予调用者对该密钥的链接权限，并且密钥环必须授予写入权限。
详见：Documentation/security/keys/request-key.rst

keyctl 系统调用的功能如下：

1. 将一个特殊的密钥ID映射为当前进程的真实密钥ID：
   
   ```c
   key_serial_t keyctl(KEYCTL_GET_KEYRING_ID, key_serial_t id, int create);
   ```

   根据"id"查找指定的特殊密钥（如果需要的话创建该密钥），并返回找到的密钥或密钥环的ID。如果密钥已经存在，则返回其ID；
   如果密钥尚不存在，当"create"非零时，创建该密钥；如果"create"为零，则返回错误ENOKEY。

2. 替换当前进程订阅的会话密钥环：

   ```c
   key_serial_t keyctl(KEYCTL_JOIN_SESSION_KEYRING, const char *name);
   ```

   如果"name"为NULL，则创建一个匿名密钥环作为进程的会话密钥环，并替换旧的会话密钥环；
   如果"name"不为NULL，如果存在同名的密钥环，则尝试将其作为会话密钥环，若不允许则返回错误；否则创建一个新的同名密钥环并作为会话密钥环。
   要将密钥环附加到命名密钥环上，该密钥环必须对进程的所有者具有搜索权限。
   成功后返回新会话密钥环的ID。

3. 更新指定的密钥：

   ```c
   long keyctl(KEYCTL_UPDATE, key_serial_t key, const void *payload, size_t plen);
   ```

   尝试使用给定的有效载荷更新指定的密钥，如果该功能不被密钥类型支持，则返回错误EOPNOTSUPP。
   进程还必须具有写入密钥的权限才能更新它。
   有效载荷的长度为plen，可以为空或不存在，类似于add_key()函数。
* 撤销一个密钥：

```c
long keyctl(KEYCTL_REVOKE, key_serial_t key);
```

这会使密钥无法再进行任何操作。进一步使用该密钥的尝试将返回错误EKEYREVOKED，并且该密钥将不再可查找。

* 更改密钥的所有权：

```c
long keyctl(KEYCTL_CHOWN, key_serial_t key, uid_t uid, gid_t gid);
```

此函数允许更改密钥的所有者和组ID。uid或gid中的任何一个可以设置为-1以抑制该更改。

只有超级用户才能将密钥的所有者更改为当前所有者以外的其他用户。同样，只有超级用户才能将密钥的组ID更改为调用进程的组ID或其组列表成员之一以外的值。

* 更改密钥的权限掩码：

```c
long keyctl(KEYCTL_SETPERM, key_serial_t key, key_perm_t perm);
```

此函数允许密钥的所有者或超级用户更改密钥的权限掩码。

仅允许设置可用的位；如果设置了其他位，则返回错误EINVAL。

* 描述一个密钥：

```c
long keyctl(KEYCTL_DESCRIBE, key_serial_t key, char *buffer, size_t buflen);
```

此函数返回密钥属性（但不包括其有效载荷数据）的摘要作为提供的缓冲区中的字符串。

除非发生错误，它总是返回能够生成的数据量，即使这些数据比缓冲区大，但它不会复制超过请求的数据到用户空间。如果缓冲区指针为NULL，则不会进行复制。

要使此函数成功，进程必须具有查看密钥的权限。

如果成功，在缓冲区中放置格式如下所示的字符串：

```plaintext
<type>;<uid>;<gid>;<perm>;<description>
```

其中type和description是字符串，uid和gid是十进制数，perm是十六进制数。如果缓冲区足够大，字符串末尾会包含一个NUL字符。

这可以通过以下方式解析：

```c
sscanf(buffer, "%[^;];%d;%d;%o;%s", type, &uid, &gid, &mode, desc);
```

* 清空一个密钥环：

```c
long keyctl(KEYCTL_CLEAR, key_serial_t keyring);
```

此函数清空与密钥环关联的密钥列表。调用进程必须具有对密钥环的写入权限，并且它必须是一个密钥环（否则将导致错误ENOTDIR）。
此功能还可以用于清除特殊的内核密钥环，前提是它们被适当地标记，并且用户具有CAP_SYS_ADMIN权限。DNS解析缓存密钥环就是一个例子。

* 将密钥链接到密钥环中：

    long keyctl(KEYCTL_LINK, key_serial_t keyring, key_serial_t key);

    此功能在密钥环和密钥之间创建一个链接。进程必须对密钥环有写权限，并且对密钥有链接权限。
    
    如果密钥环不是一个真正的密钥环，则会产生ENOTDIR错误；如果密钥环已满，则会产生ENFILE错误。
    
    链接过程会检查密钥环的嵌套层级，如果嵌套太深则返回ELOOP，如果链接会导致循环则返回EDEADLK。
    
    密钥环中与新密钥类型和描述相匹配的任何链接将在添加新密钥时被丢弃。

* 将密钥从一个密钥环移动到另一个密钥环：

    long keyctl(KEYCTL_MOVE,
                key_serial_t id,
                key_serial_t from_ring_id,
                key_serial_t to_ring_id,
                unsigned int flags);

    将由"id"指定的密钥从由"from_ring_id"指定的密钥环移动到由"to_ring_id"指定的密钥环。如果两个密钥环相同，则不执行任何操作。
    
    "flags"可以设置KEYCTL_MOVE_EXCL标志，以使操作在目标密钥环中存在匹配密钥时失败并返回EEXIST，否则将替换该密钥。
    
    进程必须对密钥有链接权限，才能成功执行此功能，并且对两个密钥环都有写权限。这里针对目标密钥环的所有可能发生的KEYCTL_LINK错误同样适用。

* 从另一个密钥环中解除密钥或密钥环的链接：

    long keyctl(KEYCTL_UNLINK, key_serial_t keyring, key_serial_t key);

    此功能会在密钥环中查找第一个指向指定密钥的链接，并在找到后将其移除。后续的链接会被忽略。进程必须对密钥环有写权限。
    
    如果密钥环不是一个真正的密钥环，则会产生ENOTDIR错误；如果密钥不存在，则会产生ENOENT错误。
* 在密钥环树中查找密钥：

    `key_serial_t keyctl(KEYCTL_SEARCH, key_serial_t keyring,
                         const char *type, const char *description,
                         key_serial_t dest_keyring);`

    这个函数会在指定的密钥环树中搜索与类型和描述相匹配的密钥。每个密钥环在递归到其子密钥环之前都会被检查。

    进程必须具有对顶层密钥环的搜索权限，否则会返回错误 EACCES。只有进程具有搜索权限的密钥环才会被递归处理，并且只有进程具有搜索权限的密钥和密钥环才能被匹配。如果指定的密钥环不是密钥环，则会返回 ENOTDIR 错误。
    
    如果搜索成功，函数将尝试将找到的密钥链接到目标密钥环（如果提供了非零ID）。所有适用于 KEYCTL_LINK 的约束在这里同样适用。
    
    如果搜索失败，将会返回错误 ENOKEY、EKEYREVOKED 或 EKEYEXPIRED。如果成功，将返回找到的密钥ID。

* 从密钥中读取负载数据：

    `long keyctl(KEYCTL_READ, key_serial_t key, char *buffer,
                 size_t buflen);`

    此函数尝试从指定的密钥中读取负载数据到缓冲区。进程必须具有对该密钥的读取权限才能成功。

    返回的数据将由密钥类型进行处理以供展示。例如，密钥环会返回一个 key_serial_t 数组，表示它订阅的所有密钥的ID。用户定义的密钥类型会直接返回其数据。如果密钥类型没有实现此功能，则会返回错误 EOPNOTSUPP。
    
    如果指定的缓冲区太小，将返回所需的缓冲区大小。在这种情况下，请注意缓冲区的内容可能会被以某种未定义的方式覆盖。
    
    否则，在成功的情况下，函数将返回复制到缓冲区的数据量。

* 实例化部分构建的密钥：

    `long keyctl(KEYCTL_INSTANTIATE, key_serial_t key,
                 const void *payload, size_t plen,
                 key_serial_t keyring);`
    `long keyctl(KEYCTL_INSTANTIATE_IOV, key_serial_t key,
                 const struct iovec *payload_iov, unsigned ioc,
                 key_serial_t keyring);`

    如果内核回调用户空间来完成密钥的实例化，用户空间应该使用这个调用在被调用进程返回前提供密钥所需的数据，否则密钥将自动标记为负数。
    
    进程必须具有写入密钥的权限才能实例化它，并且密钥必须尚未实例化。
如果指定了密钥环（非零），该密钥还将被链接到该密钥环中，但在这种情况下，所有适用于`KEYCTL_LINK`的约束也同样适用。

`payload`和`plen`参数描述了与`add_key()`相同的负载数据。
`payload_iov`和`ioc`参数描述了一个`iovec`数组中的负载数据，而不是单个缓冲区中的数据。

* 负实例化一个部分构造的密钥：

```c
long keyctl(KEYCTL_NEGATE, key_serial_t key,
            unsigned timeout, key_serial_t keyring);
long keyctl(KEYCTL_REJECT, key_serial_t key,
            unsigned timeout, unsigned error, key_serial_t keyring);
```

如果内核回调用户空间以完成密钥的实例化，用户空间应在被调用进程返回之前使用此调用将密钥标记为负实例化，如果它无法满足请求的话。
要实例化密钥，进程必须对该密钥具有写访问权限，并且该密钥必须未实例化。
如果指定了密钥环（非零），该密钥还将被链接到该密钥环中，但在这种情况下，所有适用于`KEYCTL_LINK`的约束也同样适用。
如果密钥被拒绝，将来对该密钥的搜索将返回指定的错误代码，直到被拒绝的密钥过期。否定密钥等同于以`ENOKEY`作为错误代码拒绝密钥。

* 设置默认请求密钥的目标密钥环：

```c
long keyctl(KEYCTL_SET_REQKEY_KEYRING, int reqkey_defl);
```

这设置了当前线程隐式请求的密钥所附着的默认密钥环。`reqkey_defl`应该是以下常量之一：

| 常量                           | 值   | 新的默认密钥环       |
|--------------------------------|------|----------------------|
| `KEY_REQKEY_DEFL_NO_CHANGE`    | -1   | 不更改              |
| `KEY_REQKEY_DEFL_DEFAULT`      | 0    | 默认[1]              |
| `KEY_REQKEY_DEFL_THREAD_KEYRING`| 1    | 线程密钥环           |
| `KEY_REQKEY_DEFL_PROCESS_KEYRING`| 2    | 进程密钥环           |
| `KEY_REQKEY_DEFL_SESSION_KEYRING`| 3    | 会话密钥环           |
| `KEY_REQKEY_DEFL_USER_KEYRING` | 4    | 用户密钥环           |
| `KEY_REQKEY_DEFL_USER_SESSION_KEYRING`| 5 | 用户会话密钥环       |
| `KEY_REQKEY_DEFL_GROUP_KEYRING`| 6    | 组密钥环             |

如果成功，则返回旧的默认值；如果`reqkey_defl`不是上述值之一，则返回`EINVAL`错误。
默认密钥环可以通过`request_key()`系统调用中指示的密钥环覆盖。
注意，此设置在`fork/exec`时是继承的。
[1] 默认顺序是：如果存在，则使用线程密钥环；否则，如果存在，则使用进程密钥环；否则，如果存在，则使用会话密钥环；否则，使用用户默认会话密钥环。

* 设置密钥的超时时间：

```
long keyctl(KEYCTL_SET_TIMEOUT, key_serial_t key, unsigned timeout);
```

这将设置或清除一个密钥的超时时间。超时时间可以为0以清除超时时间，或者设置为秒数来指定该密钥的有效期。

进程必须对密钥具有修改属性的访问权限才能设置其超时时间。此功能不能用于设置负值、已撤销或已过期密钥的超时时间。

* 假设有权实例化一个密钥：

```
long keyctl(KEYCTL_ASSUME_AUTHORITY, key_serial_t key);
```

这将假设或放弃实例化指定密钥所需的权限。只有当线程在其密钥环中拥有与指定密钥关联的授权密钥时，才能假设权限。

一旦假设了权限，搜索密钥时也会使用请求者的安全标签、UID、GID和组来搜索请求者的密钥环。

如果请求的权限不可用，将会返回错误EPERM；同样地，如果由于目标密钥已经实例化而导致权限被撤销，也会返回错误EPERM。

如果指定的密钥为0，则放弃任何已假设的权限。

假设的授权密钥在fork和exec时会被继承。

* 获取附加到密钥的LSM安全上下文：

```
long keyctl(KEYCTL_GET_SECURITY, key_serial_t key, char *buffer,
            size_t buflen);
```

此函数返回一个字符串，表示附加到密钥的LSM安全上下文，并将其存储在提供的缓冲区中。

除非出现错误，否则它总是返回能够生成的数据量，即使这些数据大于缓冲区的大小，但它不会复制超过请求的数据到用户空间。如果缓冲区指针为NULL，则不会进行复制。
如果缓冲区足够大，则在字符串末尾会包含一个NUL字符。这个NUL字符包含在返回的计数中。如果没有LSM（Least Significant Module）生效，则会返回一个空字符串。
要使此功能成功，进程必须对键具有查看权限。
* 安装调用进程的会话密钥环到其父进程：

    ```c
    long keyctl(KEYCTL_SESSION_TO_PARENT);
    ```

    此函数尝试将调用进程的会话密钥环安装到其父进程上，并替换父进程当前的会话密钥环。
    调用进程必须与其父进程具有相同的拥有者，密钥环必须与调用进程具有相同的拥有者，调用进程必须对密钥环具有LINK权限，并且活动的LSM模块不得拒绝权限，否则将返回错误EPERM。
    如果内存不足以完成操作，则返回错误ENOMEM，否则返回0表示成功。
    下次父进程离开内核并恢复执行用户空间时，密钥环将会被替换。
* 使一个密钥失效：

    ```c
    long keyctl(KEYCTL_INVALIDATE, key_serial_t key);
    ```

    此函数标记一个密钥为无效，并唤醒垃圾收集器。垃圾收集器立即将所有密钥环中的无效密钥移除，并在密钥的引用计数达到零时删除该密钥。
    标记为无效的密钥立即对正常的密钥操作不可见，尽管它们仍然可以在/proc/keys中看到，直到被删除（它们会被标记为'i'标志）。
    要使此功能成功，进程必须对密钥具有搜索权限。
* 计算Diffie-Hellman共享密钥或公钥：

    ```c
    long keyctl(KEYCTL_DH_COMPUTE, struct keyctl_dh_params *params,
                char *buffer, size_t buflen, struct keyctl_kdf_params *kdf);
    ```

    结构`params`包含三个密钥的序列号：

    - 公共素数p，双方都已知
    - 本地私钥
    - 基本整数，可以是共享生成元或远程公钥

    计算的结果为：

    ```
    result = base ^ private (mod prime)
    ```

    如果基是共享生成元，则结果是本地公钥。如果基是远程公钥，则结果是共享密钥。
如果参数 `kdf` 为 `NULL`，则适用以下规则：

- 缓冲区长度必须至少等于素数的长度，或者为零。
- 如果缓冲区长度非零，则在成功计算并复制到缓冲区时返回结果的长度。当缓冲区长度为零时，返回所需的最小缓冲区长度。

`kdf` 参数允许调用者在 Diffie-Hellman 计算过程中应用密钥派生函数（KDF），其中仅返回 KDF 的结果。KDF 通过 `struct keyctl_kdf_params` 定义如下：

- ``char *hashname`` 指定了用于内核加密 API 并应用于 KDF 操作的哈希算法名称。KDF 实现符合 SP800-56A 以及 SP800-108（计数器 KDF）。
- ``char *otherinfo`` 指定了 SP800-56A 第 5.8.1.2 节中定义的 OtherInfo 数据。OtherInfo 的缓冲区长度由 `otherinfolen` 给出。OtherInfo 的格式由调用者定义。

如果不需要使用 OtherInfo，则 `otherinfo` 指针可以为 `NULL`。

此函数会在密钥类型不支持时返回错误 `EOPNOTSUPP`，在找不到密钥时返回错误 `ENOKEY`，在密钥不可读时返回错误 `EACCES`。此外，当 `kdf` 参数非 `NULL` 且缓冲区长度或 OtherInfo 长度超过允许长度时，函数将返回错误 `EMSGSIZE`。

限制密钥环链接：

```c
long keyctl(KEYCTL_RESTRICT_KEYRING, key_serial_t keyring,
            const char *type, const char *restriction);
```

现有的密钥环可以通过评估密钥的内容来限制附加密钥的链接，根据某种限制方案进行评估。

`keyring` 是要应用限制的现有密钥环的键 ID。它可以为空，也可以已经有链接的密钥。即使新的限制会拒绝这些密钥，已链接的密钥仍会保留在密钥环中。

`type` 是一个注册的密钥类型。

`restriction` 是一个字符串，描述了如何限制密钥链接。
格式根据密钥类型的不同而变化，并且字符串将传递给针对请求类型的`lookup_restriction()`函数。它可能指定了用于限制的方法及其相关数据，例如签名验证或对密钥负载的约束。如果请求的密钥类型后来被注销，则在移除该密钥类型后，无法向密钥环中添加任何密钥。

要应用密钥环限制，进程必须具有设置属性权限，并且密钥环之前不能已被限制。
受限密钥环的一个应用是使用非对称密钥类型来验证X.509证书链或单个证书签名。
有关适用于非对称密钥类型的特定限制，请参阅`Documentation/crypto/asymmetric-keys.rst`。

* 查询非对称密钥：

```c
long keyctl(KEYCTL_PKEY_QUERY,
            key_serial_t key_id, unsigned long reserved,
            const char *params,
            struct keyctl_pkey_query *info);
```

获取关于非对称密钥的信息。可以通过`params`参数查询特定的算法和编码。这是一个包含键值对的空格或制表符分隔的字符串。
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

`supported_ops`包含一个标志位掩码，指示支持的操作。这是通过位或运算构造的：

`KEYCTL_SUPPORTS_{ENCRYPT,DECRYPT,SIGN,VERIFY}`

`key_size`表示密钥大小（以比特为单位）。

`max_*_size`表示要签名的数据块、签名块、要加密的数据块和要解密的数据块的最大字节大小。

`__spare[]`必须设置为0。这是为了将来使用，以便传递一个或多个解锁密钥所需的口令。

如果成功，返回0；如果密钥不是非对称密钥，则返回EOPNOTSUPP。

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

使用非对称密钥执行公钥密码操作的数据块。对于加密和验证，非对称密钥可能只需要公开部分即可，但对于解密和签名，则需要私有部分。
参数块 `params` 包含若干整数值：

    __s32 key_id;
    __u32 in_len;
    __u32 out_len;
    __u32 in2_len;

`key_id` 是要使用的非对称密钥的ID。`in_len` 和 `in2_len` 表示 in 和 in2 缓冲区中的数据量，而 `out_len` 表示输出缓冲区的大小，适用于上述操作。

对于特定的操作，输入和输出缓冲区的使用如下：

    操作ID           in, in_len       out, out_len       in2, in2_len
    ==================================  ===================  ===============
    KEYCTL_PKEY_ENCRYPT   原始数据       加密数据            -
    KEYCTL_PKEY_DECRYPT   加密数据       原始数据            -
    KEYCTL_PKEY_SIGN      原始数据       签名               -
    KEYCTL_PKEY_VERIFY    原始数据       -                   签名

`info` 是一组键值对字符串，提供补充信息。这些包括：

    `enc=<编码>`   加密/签名块的编码方式。可以是 "pkcs1"（用于 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5）、"pss"（用于 RSASSA-PSS）或 "oaep"（用于 RSAES-OAEP）。如果省略或为 "raw"，则指定加密函数的原始输出。
    `hash=<算法>`   如果数据缓冲区包含哈希函数的输出，并且编码包含关于所用哈希函数的信息，则可以通过此选项指定哈希函数，例如 "hash=sha256"

参数块中的 `__spare[]` 空间必须设置为0。这主要是为了允许传递解锁密钥所需的口令。

如果成功，加密、解密和签名都将返回写入输出缓冲区的数据量。验证在成功时返回0。

监视密钥或密钥环的变化：

    long keyctl(KEYCTL_WATCH_KEY, key_serial_t key, int queue_fd,
                const struct watch_notification_filter *filter);

这将设置或移除对指定密钥或密钥环变化的监视。

`key` 是要监视的密钥ID。
`queue_fd` 是一个指向打开管道的文件描述符，该管道管理接收通知的缓冲区。
`filter` 要么为 NULL 以移除监视，要么是一个过滤器规范，用于指示需要从密钥获取哪些事件。

更多信息请参阅 `Documentation/core-api/watch_queue.rst`。
请注意，对于任何特定的 { key, queue_fd } 组合，只能设置一个监视器。
通知记录如下所示：

    struct key_notification {
        struct watch_notification watch;
        __u32 key_id;
        __u32 aux;
    };

在此结构中，`watch::type` 将被设置为 "WATCH_TYPE_KEY_NOTIFY"，子类型将为以下之一：

    NOTIFY_KEY_INSTANTIATED
    NOTIFY_KEY_UPDATED
    NOTIFY_KEY_LINKED
    NOTIFY_KEY_UNLINKED
    NOTIFY_KEY_CLEARED
    NOTIFY_KEY_REVOKED
    NOTIFY_KEY_INVALIDATED
    NOTIFY_KEY_SETATTR

这些子类型分别表示键的实例化/拒绝、更新、在键环中创建链接、从键环中移除链接、清空键环、撤销键、使键失效或更改键的一个属性（用户、组、权限、超时时间、限制）。

如果监视的键被删除，则会发出一个基本的 `watch_notification`，其中 `type` 设置为 `WATCH_TYPE_META`，`subtype` 设置为 `watch_meta_removal_notification`。监视点 ID 将在 `info` 字段中设置。

这需要通过启用以下选项来配置：

    "提供键/键环变更通知"（KEY_NOTIFICATIONS）

内核服务
=========

内核提供的键管理服务相对简单。它们可以分为两个领域：键和键类型。
处理键相对直接。首先，内核服务注册其类型，然后搜索该类型的键。只要需要该键，就应保持该键，并最终释放它。对于文件系统或设备文件，可能在打开调用期间执行搜索，在关闭时释放键。如何处理由于两个不同用户打开同一文件而导致的键冲突问题，由文件系统作者自行解决。
要访问键管理器，必须包含以下头文件：

    <linux/key.h>

特定的键类型应该有一个位于 `include/keys/` 目录下的头文件，用于访问该类型。例如，对于类型为 "user" 的键，应该是：

    <keys/user-type.h>

请注意，可能会遇到两种不同类型的指向键的指针：

  *  struct key *

     这只是指向键结构本身。键结构至少对齐四个字节。
*  key_ref_t

     这相当于 `struct key *`，但最低有效位在调用者“拥有”该键时被设置。所谓“拥有”，是指调用进程在其键环中有可搜索的键链接。有三个函数用于处理这些情况：

    key_ref_t make_key_ref(const struct key *key, bool possession);

    struct key *key_ref_to_ptr(const key_ref_t key_ref);

    bool is_key_possessed(const key_ref_t key_ref);

    第一个函数根据键指针和拥有信息构造一个键引用（必须是真或假）。
    第二个函数从引用中获取键指针，第三个函数获取拥有标志。
当访问键的有效载荷内容时，必须采取某些预防措施以防止访问与修改之间的竞争。有关更多信息，请参阅“访问有效载荷内容注意事项”部分。
*  要搜索键，请调用：

    struct key *request_key(const struct key_type *type,
                            const char *description,
                            const char *callout_info);

    此函数用于请求一个匹配指定描述的键或键环，根据键类型的 match_preparse() 方法进行匹配。这允许近似匹配。如果 callout_info 不为 NULL，则会调用 /sbin/request-key 程序尝试从用户空间获取该键。在这种情况下，callout_info 将作为参数传递给程序。
如果该函数失败，将返回错误 `ENOKEY`、`EKEYEXPIRED` 或 `EKEYREVOKED`。
如果成功，密钥将被附加到默认密钥环中，这是由 `KEYCTL_SET_REQKEY_KEYRING` 设置的。
详见 `Documentation/security/keys/request-key.rst`

* 要在特定域中查找密钥，请调用：

```c
struct key *request_key_tag(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag,
                            const char *callout_info);
```

这与 `request_key()` 相同，只是可以指定一个域标签，使得搜索算法仅匹配带有该标签的密钥。`domain_tag` 可以为 `NULL`，表示全局域，与任何指定域分开。

* 要查找密钥并传递辅助数据给上层调用者，请调用：

```c
struct key *request_key_with_auxdata(const struct key_type *type,
                                     const char *description,
                                     struct key_tag *domain_tag,
                                     const void *callout_info,
                                     size_t callout_len,
                                     void *aux);
```

这与 `request_key_tag()` 相同，只是辅助数据会传递给 `key_type->request_key()` 操作（如果存在），且 `callout_info` 是一个长度为 `callout_len` 的数据块（如果提供的话，长度可以为 0）。

* 要在 RCU 条件下查找密钥，请调用：

```c
struct key *request_key_rcu(const struct key_type *type,
                            const char *description,
                            struct key_tag *domain_tag);
```

这类似于 `request_key_tag()`，但是它不会检查正在构建中的密钥，并且如果找不到匹配项也不会调用用户空间来构建密钥。

* 当不再需要密钥时，应使用以下方法释放密钥：

```c
void key_put(struct key *key);
```

或者：

```c
void key_ref_put(key_ref_t key_ref);
```

这些可以在中断上下文中调用。如果未设置 `CONFIG_KEYS`，则不会解析参数。

* 可以通过调用以下函数之一增加对密钥的引用：

```c
struct key *__key_get(struct key *key);
struct key *key_get(struct key *key);
```

这样引用的密钥应在处理完毕后通过调用 `key_put()` 释放。传递的密钥指针将被返回。

对于 `key_get()`，如果指针为 `NULL` 或未设置 `CONFIG_KEYS`，则不会进行引用计数递增操作。

* 可以通过调用以下函数获取密钥的序列号：

```c
key_serial_t key_serial(struct key *key);
```

如果 `key` 为 `NULL` 或未设置 `CONFIG_KEYS`，则返回 0（在这种情况下不解析参数）。
* 如果在搜索中找到了密钥环，可以通过以下函数进一步搜索：

```c
key_ref_t keyring_search(key_ref_t keyring_ref,
			 const struct key_type *type,
			 const char *description,
			 bool recurse)
```

此函数将仅搜索指定的密钥环（recurse == false）或整个密钥环树（recurse == true），以查找匹配的密钥。如果失败，则返回错误 ENOKEY（使用 IS_ERR/PTR_ERR 进行判断）。如果成功，返回的密钥需要被释放。
密钥环引用的持有属性通过权限掩码控制访问，并且如果成功则传播到返回的密钥引用指针。

* 可以通过以下方式创建一个密钥环：

```c
struct key *keyring_alloc(const char *description, uid_t uid, gid_t gid,
			  const struct cred *cred,
			  key_perm_t perm,
			  struct key_restriction *restrict_link,
			  unsigned long flags,
			  struct key *dest);
```

这将根据给定的属性创建一个密钥环并返回它。如果 dest 不为 NULL，则新密钥环将链接到其指向的密钥环。不会对目标密钥环进行权限检查。
如果密钥环会超出配额限制，则可以返回错误 EDQUOT（如果密钥环不应计入用户的配额，请在 flags 中传递 KEY_ALLOC_NOT_IN_QUOTA）。也可以返回错误 ENOMEM。
如果 restrict_link 不为 NULL，则应指向一个结构体，其中包含每次尝试将密钥链接到新密钥环时调用的函数。该结构体可能还包含一个密钥指针和一个关联的密钥类型。该函数用于检查是否可以将密钥添加到密钥环中。当给定的密钥类型未注册时，垃圾收集器将使用密钥类型清理该结构体中的函数或数据指针。内核中的 key_create_or_update() 调用者可以通过传递 KEY_ALLOC_BYPASS_RESTRICTION 来忽略此检查。
使用此功能的一个示例是在内核启动时设置加密密钥环，允许用户空间添加密钥——前提是它们可以由内核已经拥有的密钥验证。
调用时，限制函数将传入要添加到的密钥环、密钥类型、要添加的密钥的有效载荷以及用于限制检查的数据。请注意，在创建新密钥时，此函数会在有效载荷预解析和实际密钥创建之间调用。该函数应返回 0 以允许链接，或返回错误以拒绝链接。
提供了一个方便函数 restrict_link_reject，总是返回 -EPERM。

* 要检查密钥的有效性，可以调用以下函数：

```c
int validate_key(struct key *key);
```

此函数检查所讨论的密钥是否已过期或被撤销。如果密钥无效，将返回错误 EKEYEXPIRED 或 EKEYREVOKED。如果密钥为 NULL 或未设置 CONFIG_KEYS，则返回 0（在后一种情况下不解析参数）。

* 要注册一个密钥类型，应调用以下函数：

```c
int register_key_type(struct key_type *type);
```

如果存在同名类型的密钥类型，则此函数将返回错误 EEXIST。
* 要取消注册一个密钥类型，请调用：

```c
void unregister_key_type(struct key_type *type);
```

在某些情况下，可能需要处理一组密钥。为此提供了一种机制来访问管理这样一组密钥的密钥环类型：

```c
struct key_type key_type_keyring;
```

这可以与`request_key()`函数一起使用，以查找进程中的特定密钥环。找到这样的密钥环后，可以使用`keyring_search()`进行搜索。需要注意的是，不能使用`request_key()`来搜索特定的密钥环，因此这种方式的实用性有限。

### 访问有效载荷内容注意事项
#### ==

最简单的有效载荷是直接存储在`key->payload`中的数据。在这种情况下，访问有效载荷时无需使用RCU或加锁。
更复杂的有效载荷内容必须分配空间，并将指向这些内容的指针设置在`key->payload.data[]`数组中。必须选择以下方法之一来访问数据：

1. **不可修改的密钥类型**
   如果密钥类型没有修改方法，则可以在不使用任何形式的锁定的情况下访问密钥的有效载荷，前提是已知该密钥已实例化（未实例化的密钥无法被“找到”）。

2. **密钥的信号量**
   可以使用信号量来控制对有效载荷的访问和有效载荷指针的控制。修改时必须写锁，一般访问时必须读锁。这样做的缺点是访问者可能需要休眠。

3. **RCU**
   当未持有信号量时必须使用RCU；如果持有信号量，则内容不会意外改变，因为信号量仍然用于序列化对密钥的修改。密钥管理代码为密钥类型处理了这一点。
   这意味着需要使用：
   
   ```c
   rcu_read_lock() ... rcu_dereference() ... rcu_read_unlock()
   ```
   
   来读取指针，并使用：
   
   ```c
   rcu_dereference() ... rcu_assign_pointer() ... call_rcu()
   ```
   
   在经过一段宽限期后设置指针并处理旧内容。
请注意，只有密钥类型应该修改密钥的有效载荷。
此外，RCU（Read-Copy-Update）控制的有效载荷必须持有用于调用`call_rcu()`的`struct rcu_head`结构体，并且如果有效载荷是可变大小的，则还应包含有效载荷的长度。如果未持有密钥的信号量，`key->datalen`不能保证与刚刚取消引用的有效载荷一致。

注意`key->payload.data[0]`有一个标记为`__rcu`使用的影子。这被称为`key->payload.rcu_data0`。以下访问器封装了对这个元素的RCU调用：

a) 设置或更改第一个有效载荷指针：
```c
rcu_assign_keypointer(struct key *key, void *data);
```

b) 在持有密钥信号量的情况下读取第一个有效载荷指针：
```c
[const] void *dereference_key_locked([const] struct key *key);
```
请注意返回值将继承自密钥参数的`const`属性。静态分析会给出错误提示，如果它认为锁没有被持有。

c) 在持有RCU读锁的情况下读取第一个有效载荷指针：
```c
const void *dereference_key_rcu(const struct key *key);
```

定义密钥类型
=============

内核服务可能希望定义自己的密钥类型。例如，一个AFS文件系统可能希望定义一个Kerberos 5票据密钥类型。为此，开发者需要填写一个`key_type`结构并将其注册到系统中。实现密钥类型的源文件应包含以下头文件：
```c
<linux/key-type.h>
```

该结构有多个字段，其中一些是必需的：

* `const char *name`
  
  密钥类型的名称。此名称用于将用户空间提供的密钥类型名称转换为指向该结构的指针。

* `size_t def_datalen`

  这是可选的——它提供了默认的有效载荷数据长度，作为配额的一部分。如果密钥类型的有效载荷总是或几乎总是相同大小，那么这是更高效的方式。

特定密钥的数据长度（和配额）总是在实例化或更新时通过调用以下函数进行更改：
```c
int key_payload_reserve(struct key *key, size_t datalen);
```
使用修订后的数据长度。如果不可行，将返回EDQUOT错误。

* `int (*vet_description)(const char *description);`

  这个可选方法用于验证密钥描述。如果密钥类型不接受密钥描述，则可以返回错误，否则应返回0。

* `int (*preparse)(struct key_preparsed_payload *prep);`

  这个可选方法允许密钥类型在创建密钥（添加密钥）或获取密钥信号量（更新或实例化密钥）之前尝试解析有效载荷。`prep`所指向的结构如下所示：
```c
struct key_preparsed_payload {
    char *description;
    union key_payload payload;
    const void *data;
    size_t datalen;
    size_t quotalen;
    time_t expiry;
};
```
在调用该方法之前，调用者将用有效载荷块参数填充`data`和`datalen`；`quotalen`将用密钥类型的默认配额大小填充；`expiry`将设置为`TIME_T_MAX`，其余部分将清空。

如果可以从有效载荷内容中提出描述，应将其附加为字符串到`description`字段。如果`add_key()`的调用者传递`NULL`或`""`，则将使用此描述作为密钥描述。
该方法可以将任何它喜欢的内容附加到有效载荷中。这仅仅是传递给 `instantiate()` 或 `update()` 操作的。如果设置了过期时间，则在从这些数据实例化密钥时，过期时间将应用于该密钥。

该方法成功时应返回 0，否则返回一个负的错误代码。

*  ``void (*free_preparse)(struct key_preparsed_payload *prep);``

    如果提供了 `preparse()` 方法，则需要此方法，否则它是未使用的。此方法清理由 `preparse()` 方法填充的 `key_preparsed_payload` 结构中的描述和有效载荷字段内容。无论 `instantiate()` 或 `update()` 是否成功，只要 `preparse()` 返回成功，此方法总会被调用。

*  ``int (*instantiate)(struct key *key, struct key_preparsed_payload *prep);``

    此方法在构造过程中被调用以将有效载荷附加到密钥上。所附加的有效载荷不必与传递给此函数的数据有任何关系。

    `prep->data` 和 `prep->datalen` 字段定义了原始的有效载荷块。如果提供了 `preparse()` 方法，则其他字段也可能被填充。

    如果附加到密钥的数据量与 `keytype->def_datalen` 中指定的大小不同，则应调用 `key_payload_reserve()`。

    此方法不需要锁定密钥即可附加有效载荷。由于 `KEY_FLAG_INSTANTIATED` 标志没有设置在 `key->flags` 中，因此其他任何操作都无法访问该密钥。

    在此方法中睡眠是安全的。
* `generic_key_instantiate()` 函数用于简单地将数据从 `prep->payload.data[]` 复制到 `key->payload.data[]`，并在第一个元素上进行 RCU 安全的赋值。然后它会清除 `prep->payload.data[]`，以防止 `free_preparse` 方法释放这些数据。
* `int (*update)(struct key *key, const void *data, size_t datalen);`

    如果这种类型的密钥可以更新，则应提供此方法。该方法被调用以根据提供的数据块更新密钥的有效负载。`prep->data` 和 `prep->datalen` 字段定义了原始的有效负载块。如果提供了 `preparse()` 方法，则其他字段也可能被填充。在实际进行任何更改之前，应调用 `key_payload_reserve()` 来预留足够的空间。注意，如果这个操作成功了，那么类型就已经承诺要更改密钥了，因为密钥已经被修改，因此所有内存分配必须先完成。
    
    在调用此方法之前，密钥的信号量会被写锁定，但这仅阻止其他写入者；对密钥有效负载的任何更改必须在 RCU 条件下进行，并且必须使用 `call_rcu()` 来处理旧的有效负载。
    
    应在所有分配和其他可能失败的函数调用之后、但在实际更改之前调用 `key_payload_reserve()`。
    
    在此方法中休眠是安全的。
* `int (*match_preparse)(struct key_match_data *match_data);`

    此方法是可选的。当即将执行密钥搜索时会调用此方法。它接收到如下结构体：

    ```c
    struct key_match_data {
        bool (*cmp)(const struct key *key,
                    const struct key_match_data *match_data);
        const void *raw_data;
        void *preparsed;
        unsigned lookup_type;
    };
    ```

    调用时，`raw_data` 指向调用者用来匹配密钥的标准，不应对其进行修改。`(*cmp)()` 指向默认匹配函数（该函数会与 `raw_data` 进行精确描述匹配），并且 `lookup_type` 将设置为指示直接查找。

    可用的 `lookup_type` 值如下：

    * `KEYRING_SEARCH_LOOKUP_DIRECT` - 直接查找会对类型和描述进行哈希计算，从而将搜索范围缩小到少数几个密钥。
* `KEYRING_SEARCH_LOOKUP_ITERATE` - 迭代查找会遍历密钥环中的所有密钥，直到找到匹配的密钥。这必须用于任何非直接匹配密钥描述的搜索。
方法可以设置 `cmp` 指向一个自定义的函数来进行其他形式的匹配，可以将 `lookup_type` 设置为 `KEYRING_SEARCH_LOOKUP_ITERATE`，并且可以附加某些内容到预解析指针（`preparsed`）以供 `(*cmp)()` 使用。
`(*cmp)()` 应该在密钥匹配时返回 `true`，否则返回 `false`。
如果设置了 `preparsed`，可能需要使用 `match_free()` 方法来清理它。
此方法成功时应返回 `0`，否则返回一个负数错误代码。
允许在此方法中睡眠，但 `(*cmp)()` 不得睡眠，因为会持有锁。
如果没有提供 `match_preparse()`，则这种类型的密钥将通过其描述进行精确匹配。

* `void (*match_free)(struct key_match_data *match_data);`

    此方法是可选的。如果提供了，会在成功调用 `match_preparse()` 后被调用来清理 `match_data->preparsed`。

* `void (*revoke)(struct key *key);`

    此方法是可选的。当密钥被撤销时，调用此方法以丢弃部分有效负载数据。调用者会写锁定密钥信号量。
在此方法中睡眠是安全的，但应注意避免与密钥信号量产生死锁。
* ``void (*destroy)(struct key *key);``

    此方法是可选的。当密钥被销毁时，此方法会被调用来丢弃密钥的有效载荷数据。
    在此方法中访问有效载荷时无需锁定密钥；此时可以认为密钥是不可访问的。注意，在调用此函数之前，密钥的类型可能已经被更改了。
    在此方法中休眠是不安全的；调用者可能持有自旋锁。

* ``void (*describe)(const struct key *key, struct seq_file *p);``

    此方法是可选的。在读取 `/proc/keys` 时，此方法会被调用来以文本形式总结密钥的描述和有效载荷。
    调用此方法时会持有 RCU 读锁。如果要访问有效载荷，则应使用 `rcu_dereference()` 来读取有效载荷指针。`key->datalen` 不能保证与有效载荷内容保持一致。
    描述不会改变，尽管密钥的状态可能会改变。
    在此方法中休眠是不安全的；调用者持有 RCU 读锁。

* ``long (*read)(const struct key *key, char __user *buffer, size_t buflen);``

    此方法是可选的。此方法由 `KEYCTL_READ` 调用，将密钥的有效载荷转换为用户空间可以处理的数据块。
    理想情况下，该数据块应与传递给实例化和更新方法的格式相同。
    如果成功，应返回能够生成的数据块大小，而不是实际复制的大小。
此方法将在键的信号量读锁状态下被调用。这将防止键的有效载荷发生变化。访问键的有效载荷时，不需要使用RCU锁。在此方法中睡眠是安全的，例如在访问用户空间缓冲区时可能会发生这种情况。
```c
int (*request_key)(struct key_construction *cons, const char *op, void *aux);
```

此方法是可选的。如果提供，`request_key()` 和相关函数将调用此函数，而不是上层调用 `/sbin/request-key` 来处理这种类型的键。
`aux` 参数是传递给 `request_key_async_with_auxdata()` 或类似函数的参数，如果没有传递则为 `NULL`。此外，还传递了要操作的键的构造记录和操作类型（目前只有 "create"）。

此方法可以在上层调用完成前返回，但在所有情况下都必须调用以下函数来完成实例化过程，无论成功与否，无论是否有错误：
```c
void complete_request_key(struct key_construction *cons, int error);
```
`error` 参数在成功时应为 0，在出错时应为负数。该构造记录将通过此操作销毁，并且授权键将被撤销。如果指示有错误，未完成的键将被负面实例化，除非它已经实例化。
如果此方法返回错误，则该错误将被返回给 `request_key*()` 的调用者。在返回前必须调用 `complete_request_key()`。

正在构建的键和授权键可以在 `key_construction` 结构体中找到，该结构体由 `cons` 指针指向：

* `struct key *key;`：正在构建的键
* `struct key *authkey;`：授权键
* `struct key_restriction *(*lookup_restriction)(const char *params);`

此可选方法用于启用用户空间配置密钥环限制。传递限制参数字符串（不包括键类型名称），此方法返回一个指向包含评估每个尝试的键链接操作所需函数和数据的 `key_restriction` 结构体的指针。如果没有匹配项，则返回 `-EINVAL`。
* `asym_eds_op` 和 `asym_verify_signature`：
```c
int (*asym_eds_op)(struct kernel_pkey_params *params, const void *in, void *out);
int (*asym_verify_signature)(struct kernel_pkey_params *params, const void *in, const void *in2);
```

这些方法是可选的。如果提供，第一个方法允许使用键加密、解密或签名一段数据，第二个方法允许使用键验证签名。
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

这包括要使用的键；表示要使用的编码的字符串（例如，对于 RSA 键，可以使用 "pkcs1" 表示 RSASSA-PKCS1-v1.5 或 RSAES-PKCS1-v1.5 编码或 "raw" 如果没有编码）；生成签名数据所使用的哈希算法名称（如果适用）；输入和输出（或第二输入）缓冲区的大小；以及要执行的操作标识。
对于给定的操作ID，输入和输出缓冲区的使用如下：

| 操作ID          | 输入, in_len        | 输出, out_len       | 第二输入, in2, in2_len |
|-----------------|---------------------|--------------------|------------------------|
| kernel_pkey_encrypt | 原始数据            | 加密数据           | -                      |
| kernel_pkey_decrypt | 加密数据            | 原始数据           | -                      |
| kernel_pkey_sign    | 原始数据            | 签名               | -                      |
| kernel_pkey_verify  | 原始数据            | -                  | 签名                   |

`asym_eds_op()` 处理加密、解密和签名创建，具体由 `params->op` 指定。请注意，`params->op` 也用于 `asym_verify_signature()`。

加密和签名创建都会从输入缓冲区中读取原始数据，并将加密结果返回到输出缓冲区。如果设置了编码，则可能会添加填充。在签名创建的情况下，根据编码方式，可能需要指示摘要算法的名字，该名字应提供在 `hash_algo` 中。

解密会从输入缓冲区中读取加密数据，并将原始数据返回到输出缓冲区。如果设置了编码，则会检查并移除填充。

验证会从输入缓冲区中读取原始数据，并从第二个输入缓冲区中读取签名，然后检查两者是否匹配。会验证填充。根据编码方式，生成原始数据时使用的摘要算法可能需要在 `hash_algo` 中指定。

如果成功，`asym_eds_op()` 应返回写入输出缓冲区的字节数。`asym_verify_signature()` 应返回 0。

可能出现各种错误，包括：如果操作不支持则返回 EOPNOTSUPP；如果验证失败则返回 EKEYREJECTED；如果所需的加密不可用则返回 ENOPKG。

```
asym_query:
int (*asym_query)(const struct kernel_pkey_params *params,
                  struct kernel_pkey_query *info);
```

此方法是可选的。如果提供了此方法，则可以确定密钥中持有的公钥或非对称密钥的信息。
参数块与 `asym_eds_op()` 相同，但 `in_len` 和 `out_len` 未使用。`encoding` 和 `hash_algo` 字段应根据情况适当减少返回的缓冲区/数据大小。

如果成功，以下信息会被填充：

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

`key_size` 字段表示密钥的大小（以比特为单位）。`max_data_size` 和 `max_sig_size` 是签名创建和验证的最大原始数据和签名大小；`max_enc_size` 和 `max_dec_size` 是加密和解密的最大原始数据和签名大小。所有 `max_*_size` 字段都以字节为单位进行测量。

如果成功，返回 0。如果不支持该操作，则返回 EOPNOTSUPP。
请求密钥回调服务
============================

为了创建一个新的密钥，内核将尝试执行以下命令行：

	/sbin/request-key create <key> <uid> <gid> \
		<threadring> <processring> <sessionring> <callout_info>

<key> 是正在构建的密钥，三个密钥环是触发搜索进程的进程密钥环。包含这些密钥环有两个原因：

   1. 可能有一个认证令牌在其中一个密钥环中，这是获取密钥所必需的，例如：Kerberos 票证授予票证。
   2. 新密钥应该可能被缓存在其中一个环中。
此程序应在尝试访问更多密钥之前将其 UID 和 GID 设置为指定的值。然后它可能会查找一个用户特定的进程来处理请求（可能是由 KDE 桌面管理器放置在另一个密钥中的路径）。
该程序（或其调用的任何程序）应通过调用 KEYCTL_INSTANTIATE 或 KEYCTL_INSTANTIATE_IOV 完成密钥的构建，这也允许它将密钥缓存在其中一个密钥环中（通常是会话环），然后再返回。或者，可以使用 KEYCTL_NEGATE 或 KEYCTL_REJECT 将密钥标记为负密钥；这也允许密钥被缓存在其中一个密钥环中。
如果它返回时密钥仍然处于未构建状态，则密钥将被标记为负密钥，并添加到会话密钥环中，请求者将收到错误信息。
补充信息可以从调用此服务的任何人或任何实体提供。这将作为 <callout_info> 参数传递。如果没有此类信息可用，则会将 "-" 作为此参数传递。
同样地，内核可以通过执行以下命令更新已过期或即将过期的密钥：

	/sbin/request-key update <key> <uid> <gid> \
		<threadring> <processring> <sessionring>

在这种情况下，程序不需要实际将密钥附加到某个环上；提供这些环只是为了参考。

垃圾回收
==================

已删除类型的死密钥（即类型已被移除的密钥）将自动从指向它们的密钥环中解除链接，并尽快由后台垃圾回收器删除。
类似地，撤销和过期的密钥也将进行垃圾回收，但只有在经过一定时间后才会进行。这个时间是以秒为单位设置的：

	/proc/sys/kernel/keys/gc_delay
