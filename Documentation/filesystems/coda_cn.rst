SPDX 许可证标识符: GPL-2.0

===========================
Coda 内核-Venus 接口
===========================

.. 注意::

   这是描述 Coda 组件之一的技术文档 —— 本文件描述了客户端内核-Venus 接口。欲了解更多信息：

  http://www.coda.cs.cmu.edu

获取运行 Coda 所需的用户级软件：

  ftp://ftp.coda.cs.cmu.edu

要运行 Coda，您需要获取客户端上的用户级缓存管理器 Venus 以及用于操作 ACL、登录等的工具。客户端需要在内核配置中选择 Coda 文件系统。服务器需要一个用户级服务器，并且目前不依赖内核支持。Venus 内核接口

  Peter J. Braam

  v1.0, 1997年11月9日

  本文档描述了 Venus 与 Coda 文件系统操作所需的内核级文件系统代码之间的通信。本文档版本旨在描述当前接口（版本 1.0）以及我们预期的改进。
.. 目录

  1. 引言

  2. 处理 Coda 文件系统调用

  3. 消息层

     3.1 实现细节

  4. 调用级别的接口

     4.1 内核和 Venus 共享的数据结构
     4.2 pioctl 接口
     4.3 root
     4.4 lookup
     4.5 getattr
     4.6 setattr
     4.7 access
     4.8 create
     4.9 mkdir
     4.10 link
     4.11 symlink
     4.12 remove
     4.13 rmdir
     4.14 readlink
     4.15 open
     4.16 close
     4.17 ioctl
     4.18 rename
     4.19 readdir
     4.20 vget
     4.21 fsync
     4.22 inactive
     4.23 rdwr
     4.24 odymount
     4.25 ody_lookup
     4.26 ody_expand
     4.27 prefetch
     4.28 signal

  5. mini 缓存和下行调用

     5.1 INVALIDATE
     5.2 FLUSH
     5.3 PURGEUSER
     5.4 ZAPFILE
     5.5 ZAPDIR
     5.6 ZAPVNODE
     5.7 PURGEFID
     5.8 REPLACE

  6. 初始化和清理

     6.1 要求

1. 引言
===============

  在 Coda 分布式文件系统中的一个关键组件是缓存管理器 Venus。当 Coda 启用系统的进程访问 Coda 文件系统中的文件时，请求会发送到操作系统中的文件系统层。操作系统将与 Venus 通信以处理进程的请求。Venus 管理一个持久的客户端缓存，并通过远程过程调用向 Coda 文件服务器及相关服务器（如认证服务器）服务这些请求。当 Venus 完成一个请求后，它会回复操作系统适当的返回码和其他与请求相关的信息。可选地，Coda 的内核支持可以维护一个最近处理请求的小型缓存，以减少与 Venus 的交互次数。Venus 具有告知内核其小型缓存中的元素不再有效的功能。

本文档精确描述了内核与 Venus 之间的这种通信。我们将给出所谓上行调用和下行调用的定义及其处理数据的格式。我们还将描述由这些调用产生的语义不变性。从历史上看，Coda 是在 Mach 2.6 中的 BSD 文件系统中实现的。内核与 Venus 之间的接口非常类似于 BSD VFS 接口。提供了类似的功能，并且参数和返回数据的格式也非常接近 BSD VFS。这为在 BSD 系统中实现 Coda 的内核级文件系统驱动程序提供了一个几乎自然的环境。然而，其他操作系统如 Linux 和 Windows 95 及 NT 有不同的虚拟文件系统接口。为了在这些系统上实现 Coda，有必要对 Venus/内核协议进行逆向工程。同时，其他系统也可以从对协议的一些小优化和修改中显著受益。为了便于这项工作并使未来的移植更容易，应详细记录 Venus 与内核之间的通信。这是本文档的目标。
### 2. 服务 Coda 文件系统调用

服务一个 Coda 文件系统的请求起始于访问 Coda 文件的进程 P。它会进行一个系统调用，该调用会捕获到操作系统内核。例如，在 Unix 环境中，这些调用包括 `read`、`write`、`open`、`close`、`create`、`mkdir`、`rmdir` 和 `chmod`。在 Win32 环境中也有类似的调用，如 `CreateFile`。通常，操作系统会在虚拟文件系统（VFS）层处理这个请求，该层在 NT 中被称为 I/O Manager，在 Windows 95 中被称为 IFS Manager。VFS 负责部分处理请求并定位将服务请求特定部分的具体文件系统。通常路径中的信息有助于找到正确的文件系统驱动程序。有时经过广泛的预处理后，VFS 开始调用文件系统驱动程序中的导出例程。这是请求开始进行特定文件系统处理的地方，也是 Coda 特定内核代码开始发挥作用的地方。

Coda 的文件系统层必须暴露和实现多个接口。首先，VFS 必须能够对 Coda 文件系统层进行所有必要的调用，因此 Coda 文件系统驱动程序必须暴露适用于操作系统的 VFS 接口。这些接口在不同操作系统之间差异很大，但都具有读写和创建及删除对象等功能。Coda 文件系统层通过调用缓存管理器 Venus 提供的一个或多个定义明确的服务来服务此类 VFS 请求。当 Venus 的回复返回到文件系统驱动程序时，VFS 调用的处理将继续，并以回复内核的 VFS 层而结束。最后，VFS 层返回到进程。

由于这种设计，文件系统驱动程序必须提供一个基本接口，使 Venus 能够管理消息流量。具体来说，Venus 必须能够检索和放置消息，并且在新消息到达时被通知。此通知机制不能阻塞 Venus，因为即使没有消息等待或正在处理，Venus 也需要处理其他任务。

**Coda 文件系统驱动程序的接口**

此外，文件系统层还提供了一种特殊的用户进程与 Venus 之间的通信路径，称为 pioctl 接口。pioctl 接口用于 Coda 特定的服务，例如请求有关由 Venus 管理的持久缓存的详细信息。这里内核的参与是有限的，它仅识别调用进程并将信息传递给 Venus。当 Venus 回复时，响应会原样返回给调用者。

最后，Venus 允许内核文件系统驱动程序缓存某些服务的结果。这样做是为了避免过多的上下文切换，从而提高系统效率。然而，Venus 可能会从网络获取信息，这意味着缓存的信息必须被刷新或替换。此时 Venus 会向 Coda 文件系统层发起下层调用来请求缓存刷新或更新。内核文件系统驱动程序同步处理此类请求。

在这些接口中，VFS 接口以及放置、接收和被通知消息的功能是平台特定的。我们不会深入讨论导出到 VFS 层的调用，但会说明消息交换机制的要求。

### 3. 消息层

在最低级别上，Venus 和文件系统驱动程序之间的通信是通过消息进行的。请求 Coda 文件服务的进程与 Venus 之间的同步依赖于阻塞和唤醒进程。Coda 文件系统驱动程序代表进程 P 处理 VFS 和 pioctl 请求，为 Venus 创建消息，等待回复，最后返回给调用者。消息交换的实现是平台特定的，但语义（到目前为止）普遍适用。数据缓冲区由文件系统驱动程序在内核内存中为 P 创建，并复制到 Venus 的用户内存中。

在服务 P 的过程中，文件系统驱动程序向上调用 Venus。这种向上调用是通过创建一个消息结构来分派给 Venus 的。该结构包含 P 的标识、消息序列号、请求的大小以及指向内核内存中请求数据的指针。由于数据缓冲区被重新使用以保存 Venus 的回复，因此有一个字段记录回复的大小。消息中的标志字段用于精确记录消息的状态。附加的平台相关结构涉及确定消息在队列中的位置的指针以及指向同步对象的指针。在向上调用例程中，消息结构被填充，标志被设置为 0，并被放置在“待处理”队列中。调用向上调用例程负责分配数据缓冲区；其结构将在下一节中描述。
必须存在一种机制来通知Venus消息已创建，并且使用操作系统中可用的同步对象来实现。此通知在进程P的上层调用(upcall)上下文中完成。当消息位于待处理队列中时，进程P无法继续执行上层调用。文件系统请求例程中的P（内核模式）处理必须暂停直到Venus回复。因此，在P中的调用线程会在上层调用中被阻塞。消息结构中的一个指针将定位到P正在等待的同步对象。

Venus检测到有消息到达的通知，并通过FS驱动允许Venus通过getmsg_from_kernel调用来获取该消息。此操作在内核中完成，即将消息放入处理消息队列并设置标志为READ。Venus会接收到数据缓冲区的内容。此时getmsg_from_kernel调用返回，Venus开始处理请求。

在某个时刻，FS驱动从Venus接收一条消息，即当Venus调用sendmsg_to_kernel时。此时Coda FS驱动会查看消息内容并决定：

* 如果消息是针对已挂起线程P的回复，则将其从处理队列中移除并标记消息为WRITTEN。最后，FS驱动解除P的阻塞状态（仍然在Venus的内核模式上下文中），sendmsg_to_kernel调用返回给Venus。进程P将在某个时刻被调度并继续处理其上层调用，数据缓冲区被替换为Venus的回复。
* 如果消息是一个“下层调用”（downcall）。下层调用是指Venus向FS驱动发出的请求。FS驱动会立即处理请求（通常是缓存驱逐或替换），完成后sendmsg_to_kernel返回。

现在P苏醒并继续处理上层调用。需要注意一些细节。首先，P需要判断它是由于来自其他来源的信号还是由Venus在sendmsg_to_kernel调用中唤醒的。在正常情况下，上层调用例程会释放消息结构并返回。此时FS例程可以继续其处理。

**睡眠和IPC安排**

如果P是由信号而不是Venus唤醒的，它首先会查看标志字段。如果消息尚未被标记为READ，则进程P可以在不通知Venus的情况下处理其信号。如果Venus已经标记为READ，并且不应处理请求，P可以发送一个信号消息给Venus以指示应忽略之前的请求。此类信号会被放在队列头部，由Venus优先读取。如果消息已被标记为WRITTEN，则处理已无法停止。VFS例程将继续。（-- 如果一个VFS请求涉及多个上层调用，这可能会导致复杂的状态，可以在消息结构中添加一个额外的字段“handle_signals”来指示已达到不可撤销点。--）

3.1 实现细节
--------------

Unix版本的这一机制是通过实现与Coda相关联的一个字符设备来完成的。Venus通过读取该设备来获取消息，回复则通过写入设备发送，而通知则是通过对该设备文件描述符的select系统调用。进程P在可中断等待队列对象上保持等待状态。

在Windows NT和DPMI Windows 95实现中使用了DeviceIoControl调用。DeviceIoControl调用设计用于通过OPCODES将缓冲区从用户内存复制到内核内存。sendmsg_to_kernel作为一个同步调用发出，而getmsg_from_kernel调用是异步的。Windows事件对象用于消息到达的通知。在NT中进程P在KernelEvent对象上保持等待状态，在Windows 95中则是在信号量上。

4. 调用级别的接口
==================

本节描述了Coda FS驱动可以对Venus进行的上层调用。每个上层调用都利用了两个结构：inputArgs和outputArgs。这些结构的伪BNF形式如下所示：

```c
struct inputArgs {
    u_long opcode;
    u_long unique;     /* 使多个待处理的消息彼此区分 */
    u_short pid;                 /* 共同字段 */
    u_short pgid;                /* 共同字段 */
    struct CodaCred cred;        /* 共同字段 */

    <union "in" of call dependent parts of inputArgs>
};

struct outputArgs {
    u_long opcode;
    u_long unique;       /* 使多个待处理的消息彼此区分 */
    u_long result;

    <union "out" of call dependent parts of inputArgs>
};
```

在进一步讨论之前，让我们阐明各个字段的作用。inputArgs以opcode开头，定义了向Venus请求的服务类型。目前大约有30个上层调用，我们将会讨论它们。unique字段为inputArg标记一个唯一编号，以便唯一识别消息。传递了一个进程ID和进程组ID。最后，包含了调用者的凭证信息。

在深入探讨具体调用之前，我们需要讨论一些内核和Venus共享的数据结构。
### 4.1. 内核和Venus共享的数据结构
----------------------------------------------------

`CodaCred` 结构定义了各种用户和组 ID，这些 ID 是为调用进程设置的。`vuid_t` 和 `vgid_t` 是 32 位无符号整数。它还定义了一个数组来表示组成员关系。在 Unix 系统上，`CodaCred` 已经证明足够实现良好的安全语义，但在 Windows 环境下可能需要进行修改：

```c
struct CodaCred {
    vuid_t cr_uid, cr_euid, cr_suid, cr_fsuid; /* 实际、有效、设置、文件系统用户 ID */
    vgid_t cr_gid, cr_egid, cr_sgid, cr_fsgid; /* 对于组同样适用 */
    vgid_t cr_groups[NGROUPS];        /* 调用者的组成员关系 */
};
```

.. Note::

   在 Venus 中是否需要 `CodaCreds` 还有疑问。最终 Venus 并不知道组的存在，尽管它确实会使用默认的 UID/GID 创建文件。也许组成员列表是多余的。

下一个重要的标识符用于识别 Coda 文件，即 `ViceFid`。一个文件的 `fid` 唯一地定义了 Coda 文件系统中的文件或目录 [1]_：

```c
typedef struct ViceFid {
    VolumeId Volume;
    VnodeId Vnode;
    Unique_t Unique;
} ViceFid;
```

.. [1] 一个“单元”是一组在单个系统控制机器（SCM）管理下的 Coda 服务器。请参阅 Coda 管理手册以获取有关 SCM 的详细描述。
每个组成部分字段：`VolumeId`、`VnodeId` 和 `Unique_t` 都是 32 位无符号整数。我们预计还需要一个前缀字段来标识 Coda 单元；这可能会采用 IPv6 大小的 IP 地址形式，并通过 DNS 命名 Coda 单元。

Venus 和内核之间共享的下一个重要结构是文件属性。以下结构用于交换信息。它预留了空间以便未来扩展，例如支持设备文件（目前 Coda 中没有设备文件）：

```c
struct coda_timespec {
    int64_t         tv_sec;         /* 秒 */
    long            tv_nsec;        /* 纳秒 */
};

struct coda_vattr {
    enum coda_vtype va_type;        /* 节点类型（用于创建） */
    u_short         va_mode;        /* 文件访问模式和类型 */
    short           va_nlink;       /* 引用文件的数量 */
    vuid_t          va_uid;         /* 所有者用户 ID */
    vgid_t          va_gid;         /* 所有者组 ID */
    long            va_fsid;        /* 文件系统 ID（目前为设备号） */
    long            va_fileid;      /* 文件 ID */
    u_quad_t        va_size;        /* 文件大小（字节） */
    long            va_blocksize;   /* 用于 I/O 的首选块大小 */
    struct coda_timespec va_atime;  /* 最后访问时间 */
    struct coda_timespec va_mtime;  /* 最后修改时间 */
    struct coda_timespec va_ctime;  /* 文件更改时间 */
    u_long          va_gen;         /* 文件的版本号 */
    u_long          va_flags;       /* 文件定义的标志 */
    dev_t           va_rdev;        /* 设备特殊文件代表的设备 */
    u_quad_t        va_bytes;       /* 文件占用的磁盘空间（字节） */
    u_quad_t        va_filerev;     /* 文件修改编号 */
    u_int           va_vaflags;     /* 操作标志，见下文 */
    long            va_spare;       /* 保留四字对齐 */
};
```

### 4.2. pioctl 接口
--------------------------

应用程序可以通过 pioctl 接口发出特定于 Coda 的请求。pioctl 作为一个普通 ioctl 实现在虚构文件 `/coda/.CONTROL` 上。pioctl 调用打开此文件，获取文件句柄并执行 ioctl 调用，最后关闭文件。

内核在这方面的参与仅限于提供打开和关闭文件以及传递 ioctl 消息的功能，并验证 pioctl 数据缓冲区中的路径是否为 Coda 文件系统中的文件。

内核接收到的数据包形式如下：

```c
struct {
    const char *path;
    struct ViceIoctl vidata;
    int follow;
} data;
```

其中：

```c
struct ViceIoctl {
    caddr_t in, out;        /* 要传输的数据 */
    short in_size;          /* 输入缓冲区大小 ≤ 2K */
    short out_size;         /* 输出缓冲区最大大小，≤ 2K */
};
```

路径必须是一个 Coda 文件，否则不会执行 ioctl 上调。

.. Note:: 数据结构和代码一团糟。我们需要清理一下。

**我们现在继续记录各个调用：**

### 4.3. root
----------

**参数**
- 输入：空

- 输出：

```c
struct cfs_root_out {
    ViceFid VFid;
} cfs_root;
```

**描述**
此调用在初始化 Coda 文件系统时由 Venus 发出。如果结果为零，则 `cfs_root` 结构包含 Coda 文件系统的根 `ViceFid`。如果生成非零结果，其值是一个平台相关的错误代码，表示 Venus 在定位 Coda 文件系统根目录时遇到的问题。

### 4.4. lookup
--------------

**摘要**
查找目录中是否存在某个对象及其 `ViceFid` 和类型。

**参数**
- 输入：

```c
struct cfs_lookup_in {
    ViceFid VFid;
    char *name;          /* 数据占位符 */
} cfs_lookup;
```

- 输出：

```c
struct cfs_lookup_out {
    ViceFid VFid;
    int vtype;
} cfs_lookup;
```

**描述**
此调用用于确定目录条目的 `ViceFid` 和文件类型。请求的目录条目名为 `name`，Venus 将搜索由 `cfs_lookup_in.VFid` 标识的目录。
结果可能表明该名称不存在，或者在查找过程中遇到困难（例如，由于断开连接）
如果结果为零，则字段 cfs_lookup_out.VFid 包含目标的 ViceFid，cfs_lookup_out.vtype 包含表示该名称所指定对象类型的 coda_vtype
对象的名称是一个 8 位字符字符串，最大长度为 CFS_MAXNAMLEN，目前设置为 256（包括一个 0 终止符）

非常重要的一点是，Venus 使用按位或运算符将 cfs_lookup.vtype 与 CFS_NOCACHE 进行按位或操作，以指示该对象不应放入内核名称缓存中
.. 注意::

     当前 vtype 的类型是错误的。应该是 coda_vtype。Linux 不处理 CFS_NOCACHE。应该
4.5.  getattr
-------------

  摘要 获取文件属性
参数
     in::

		struct cfs_getattr_in {
		    ViceFid VFid;
		    struct coda_vattr attr; /* XXXXX */
		} cfs_getattr;



     out::

		struct cfs_getattr_out {
		    struct coda_vattr attr;
		} cfs_getattr;



  描述
    此调用返回由 fid 标识的文件的属性
错误
    如果具有 fid 的对象不存在、无法访问，或者调用者没有权限获取属性时，可能会发生错误
.. 注意::

     许多内核文件系统驱动程序（Linux、NT 和 Windows 95）需要获取属性以及 Fid 来实例化内部的 "inode" 或 "FileHandle"。通过合并 lookup 和 getattr 调用，在 Venus/内核交互层面和 RPC 层面可以显著提高此类系统的性能
输入参数中的 vattr 结构是多余的，应予以删除
4.6.  setattr
-------------

  摘要
    设置文件属性
### cfs_setattr

#### 参数
**输入:**

```c
struct cfs_setattr_in {
    ViceFid VFid;
    struct coda_vattr attr;
} cfs_setattr;
```

**输出:**

无

#### 描述
结构体 `attr` 中填充了要更改的属性，采用 BSD 风格。不需要更改的属性设置为 -1（除了 `vtype` 被设置为 `VNON`）。其他属性则设置为要分配的新值。

文件系统驱动程序唯一可以请求更改的属性是模式（mode）、所有者（owner）、组ID（groupid）、访问时间（atime）、修改时间（mtime）和创建时间（ctime）。返回值表示操作是否成功。

#### 错误
可能会出现各种错误。对象可能不存在、无法访问，或者未获得 Venus 的权限。

---

### cfs_access

#### 参数
**输入:**

```c
struct cfs_access_in {
    ViceFid VFid;
    int flags;
} cfs_access;
```

**输出:**

无

#### 描述
验证是否允许对由 `VFid` 标识的对象进行由 `flags` 描述的操作。结果表明是否授予访问权限。重要的是要记住，Coda 使用 ACL 来强制保护，并且最终是服务器而不是客户端来确保系统的安全性。此调用的结果取决于用户是否持有令牌。

#### 错误
对象可能不存在，或者描述保护的 ACL 可能无法访问。

---

### cfs_create

#### 概述
用于创建文件。

#### 参数
**输入:**

```c
struct cfs_create_in {
    ViceFid VFid;
    struct coda_vattr attr;
    int excl;
    int mode;
    char *name; // 数据占位符
} cfs_create;
```

**输出:**

```c
struct cfs_create_out {
    ViceFid VFid;
    struct coda_vattr attr;
} cfs_create;
```

#### 描述
此上层调用用于请求创建一个文件。文件将在由 `VFid` 标识的目录中创建，其名称为 `name`，模式为 `mode`。如果设置了 `excl` 并且文件已存在，则会返回错误。如果 `attr` 中的大小字段设置为零，则文件将被截断。文件的 `uid` 和 `gid` 通过使用宏 `CRTOUID` 将 CodaCred 转换为 `uid`（该宏依赖于平台）。成功时返回文件的 `VFid` 和属性。Coda 文件系统驱动程序通常会在内核级别为新对象实例化一个 vnode、inode 或文件句柄。

#### 错误
可能会出现各种错误。权限可能不足。如果对象存在并且不是文件，在 Unix 下会返回错误 `EISDIR`。

#### 注意
参数的打包非常低效，似乎在系统调用 `creat` 和 VFS 操作 `create` 之间存在混淆。VFS 操作 `create` 只用于创建新对象。
### 4.9. mkdir
-----------

**概述**
  创建一个新的目录

**参数**
  输入参数 `in`：

  ```c
  struct cfs_mkdir_in {
      ViceFid     VFid;
      struct coda_vattr attr;
      char        *name;          /* 占位符数据 */
  } cfs_mkdir;
  ```

  输出参数 `out`：

  ```c
  struct cfs_mkdir_out {
      ViceFid VFid;
      struct coda_vattr attr;
  } cfs_mkdir;
  ```

**描述**
  此调用类似于 `create`，但创建的是一个目录。
  只有输入参数中的 `mode` 字段用于创建。
  成功创建后，返回的 `attr` 包含新目录的属性。

**错误**
  与 `create` 相同。

**注意**
  输入参数应改为 `mode` 而不是 `attributes`。
  应返回父目录的属性，因为其大小和修改时间会改变。

### 4.10. link
-----------

**概述**
  创建指向现有文件的链接

**描述**
  此调用与 Unix 中的 `link` 类似，用于创建指向现有文件的新链接。
### link

#### 参数
**输入:**

```c
struct cfs_link_in {
    ViceFid sourceFid;          /* 要链接的目标节点 */
    ViceFid destFid;            /* 放置链接的目录 */
    char *tname;                /* 数据占位符 */
} cfs_link;
```

**输出:**

- 无

#### 描述
此调用会在由 `destFid` 标识的目录中创建一个指向 `sourceFid` 的链接，并命名为 `tname`。源文件必须位于目标目录的父目录中，即源文件的父目录必须是 `destFid`。Coda 不支持跨目录的硬链接。只有返回值是相关的，它表示成功或失败类型。

#### 错误
可能发生通常的错误。

### symlink

#### 概述
创建一个符号链接。

#### 参数
**输入:**

```c
struct cfs_symlink_in {
    ViceFid VFid;              /* 放置符号链接的目录 */
    char *srcname;
    struct coda_vattr attr;
    char *tname;
} cfs_symlink;
```

**输出:**

- 无

#### 描述
创建一个符号链接。该链接将放置在由 `VFid` 标识的目录中，并命名为 `tname`。它应该指向路径名 `srcname`。新创建对象的属性应设置为 `attr`。

**注意**
应返回目标目录的属性，因为其大小发生了变化。

### remove

#### 概述
删除一个文件。

#### 参数
**输入:**

```c
struct cfs_remove_in {
    ViceFid VFid;
    char *name;                /* 数据占位符 */
} cfs_remove;
```

**输出:**

- 无

#### 描述
删除由 `VFid` 标识的目录中的名为 `name` 的文件。

**注意**
应返回目录的属性，因为其修改时间（mtime）和大小可能发生变化。

### rmdir

#### 概述
删除一个目录。

#### 参数
**输入:**

```c
struct cfs_rmdir_in {
    ViceFid VFid;
    char *name;                /* 数据占位符 */
} cfs_rmdir;
```

**输出:**

- 无

#### 描述
从由 `VFid` 标识的目录中删除名为 `name` 的目录。

**注意**
应返回父目录的属性，因为其修改时间（mtime）和大小可能发生变化。

### readlink

#### 概述
读取符号链接的值。

#### 参数
**输入:**

```c
struct cfs_readlink_in {
    ViceFid VFid;
} cfs_readlink;
```

**输出:**

```c
struct cfs_readlink_out {
    int count;
    caddr_t data;              /* 数据占位符 */
} cfs_readlink;
```

#### 描述
此函数将由 `VFid` 标识的符号链接的内容读入缓冲区 `data` 中。缓冲区 `data` 必须能够容纳任何长度不超过 CFS_MAXNAMLEN 的名称（PATH 或 NAM??）。
### 错误
没有异常错误

#### 4.15. 打开文件
**概要**
打开一个文件

**参数**
输入参数：
```c
struct cfs_open_in {
    ViceFid VFid;
    int flags;
} cfs_open;
```

输出参数：
```c
struct cfs_open_out {
    dev_t dev;
    ino_t inode;
} cfs_open;
```

**描述**
此请求要求Venus将由VFid标识的文件放入其缓存中，并记录调用进程希望以与`open(2)`相同的标志打开该文件。返回给内核的结果在Unix和Windows系统上有所不同。对于Unix系统，Coda文件系统驱动程序会被告知容器文件的设备号和inode号（通过字段`dev`和`inode`）。对于Windows系统，容器文件的路径会被返回给内核。
**注意**
目前`cfs_open_out`结构体还没有适当地适应Windows的情况。最好实现两个上层调用，一个用于获取容器文件名，另一个用于获取容器文件的inode。

#### 4.16. 关闭文件
**概要**
关闭一个文件并更新服务器上的内容

**参数**
输入参数：
```c
struct cfs_close_in {
    ViceFid VFid;
    int flags;
} cfs_close;
```

输出参数：
无

**描述**
关闭由VFid标识的文件。
**注意**
`flags`参数是无效的且未使用。然而，Venus代码中有空间处理一个`execp`输入字段，可能这个字段应该用来告知Venus文件虽然被关闭了但仍然被内存映射用于执行。在Venus的`vproc_vfscalls`中有关于是否获取数据的注释。这似乎很不合理。如果一个文件正在被关闭，容器文件中的数据应该是新的数据。这里再次`execp`标志可能会引起混淆：目前Venus可能认为一个仍然被内存映射的文件可以从缓存中刷新。这需要进一步理解。

#### 4.17. ioctl操作
**概要**
对文件执行ioctl操作。这包括pioctl接口

**参数**
输入参数：
```c
struct cfs_ioctl_in {
    ViceFid VFid;
    int cmd;
    int len;
    int rwflag;
    char *data; // 数据占位符
} cfs_ioctl;
```

输出参数：
```c
struct cfs_ioctl_out {
    int len;
    caddr_t data; // 数据占位符
} cfs_ioctl;
```

**描述**
对文件执行ioctl操作。命令、长度和数据参数按常规填充。`flags`不被Venus使用。
**注意**
另一个无效参数。`flags`不被使用。Venus代码中关于PREFETCHING的部分是什么意思？

#### 4.18. 重命名fid
**概要**
重命名一个fid
### 4.18. rename
--------------
**输入参数:**

```c
struct cfs_rename_in {
    ViceFid     sourceFid;
    char        *srcname;
    ViceFid destFid;
    char        *destname;
} cfs_rename;
```

**输出参数:**

无

**描述:**
将目录 `sourceFid` 中名为 `srcname` 的对象重命名为目录 `destFid` 中的 `destname`。重要的是，`srcname` 和 `destname` 必须是零终止字符串。在 Unix 内核中，字符串并不总是以零终止。

### 4.19. readdir
--------------
**概述:**
读取目录项

**输入参数:**

```c
struct cfs_readdir_in {
    ViceFid     VFid;
    int count;
    int offset;
} cfs_readdir;
```

**输出参数:**

```c
struct cfs_readdir_out {
    int size;
    caddr_t     data;           /* 数据占位符 */
} cfs_readdir;
```

**描述:**
从 `VFid` 开始读取目录项，从偏移量 `offset` 处开始，并且最多读取 `count` 字节。返回的数据存储在 `data` 中，并返回数据大小到 `size`。

**注意:**
此调用未使用。readdir 操作利用容器文件。我们将在即将进行的目录重构期间重新评估这一点。

### 4.20. vget
--------------
**概述:**
指示 Venus 进行 FSDB->Get 操作

**输入参数:**

```c
struct cfs_vget_in {
    ViceFid VFid;
} cfs_vget;
```

**输出参数:**

```c
struct cfs_vget_out {
    ViceFid VFid;
    int vtype;
} cfs_vget;
```

**描述:**
此上层调用要求 Venus 对由 `VFid` 标记的 fsobj 执行获取操作。

**注意:**
此操作未使用。然而，它非常有用，因为它可以用来处理读写内存映射文件。这些文件可以使用 `vget` 在 Venus 缓存中“锁定”，并使用 `inactive` 释放。

### 4.21. fsync
--------------
**概述:**
告诉 Venus 更新文件的 RVM 属性

**输入参数:**

```c
struct cfs_fsync_in {
    ViceFid VFid;
} cfs_fsync;
```

**输出参数:**

无

**描述:**
请求 Venus 更新对象 `VFid` 的 RVM 属性。这应在内核级别的 fsync 类型调用中调用。结果表明同步是否成功。
### 4.22. inactive
-------------------

**概述**
  告知Venus某个vnode不再被使用

**参数**
  in::

      struct cfs_inactive_in {
          ViceFid VFid;
      } cfs_inactive;

  out
      无

**描述**
  此操作返回EOPNOTSUPP

**注释**
  这个操作或许应该被移除

### 4.23. rdwr
-------------------

**概述**
  从文件中读取或写入

**参数**
  in::

      struct cfs_rdwr_in {
          ViceFid     VFid;
          int rwflag;
          int count;
          int offset;
          int ioflag;
          caddr_t     data;           /* 数据占位符 */
      } cfs_rdwr;

  out::

      struct cfs_rdwr_out {
          int rwflag;
          int count;
          caddr_t     data;   /* 数据占位符 */
      } cfs_rdwr;

**描述**
  此上层调用请求Venus从文件中读取或写入

**注释**
  由于违反了Coda的哲学，即读/写操作永远不会到达Venus，这个操作应该被移除。据我所知，这个操作不起作用。目前并未使用

### 4.24. odymount
-------------------

**概述**
  允许在单个Unix挂载点上挂载多个Coda“文件系统”

**参数**
  in::

      struct ody_mount_in {
          char        *name;          /* 数据占位符 */
      } ody_mount;

  out::

      struct ody_mount_out {
          ViceFid VFid;
      } ody_mount;

**描述**
  请求Venus返回名为name的Coda系统的根fid。fid通过VFid返回

**注释**
  这个调用曾被David用于动态集合。由于它在VFS挂载区域中导致了一堆指针，因此应该被移除。Coda本身并未使用此调用。Venus未实现此调用
4.25. ody_lookup
-----------------
**摘要**
  查询某事物

**参数**
  - in: 无关
  - out: 无关

**注释**: 忽略。Venus 尚未实现此调用。

4.26. ody_expand
-----------------
**摘要**
  在动态集中扩展某事物

**参数**
  - in: 无关
  - out: 无关

**注释**: 忽略。Venus 尚未实现此调用。

4.27. prefetch
---------------
**摘要**
  预取动态集

**参数**
  - in: 未记录
  - out: 未记录

**描述**
  Venus 的 `worker.cc` 支持此调用，但已注明该功能不起作用。这并不奇怪，因为内核尚不支持此功能。（ODY_PREFETCH 未定义为一个操作）

**注释**: 忽略。此功能不起作用且未被 Coda 使用。

4.28. signal
-------------
**摘要**
  向 Venus 发送一个关于上层调用的信号
### 参数
在

无

出

不适用

### 描述
这是一个带外上层调用，用于通知Venus。调用进程在Venus读取输入队列中的消息后收到了一个信号。Venus 应该清理这个操作。
### 错误
没有回复

注意：
我们需要更好地理解Venus需要清理的内容以及它是否正确地执行了这些清理。同时，我们也需要正确处理每个系统调用的多个上层调用情况。了解内核负责通知Venus进行清理之后Venus的状态变化是很重要的（例如，打开肯定是这样的状态变化，但许多其他情况可能不是）。

### 5. 缓存和下层调用
#### 5.1 缓存和下层调用

Coda文件系统驱动程序可以缓存查找和访问上层调用的结果，以限制上层调用的频率。上层调用是有代价的，因为需要进行进程上下文切换。缓存信息的反面是Venus将通知文件系统驱动程序必须刷新或重命名缓存条目。

内核代码通常需要维护一个结构，将内部文件句柄（在BSD中称为vnodes，在Linux中称为inodes，在Windows中称为FileHandles）与Venus维护的ViceFid链接起来。原因是频繁的双向转换是必需的，以便进行上层调用并使用上层调用的结果。这种链接对象称为cnode。

当前的微型缓存实现具有记录以下内容的缓存条目：

1. 文件名
2. 包含对象的目录的cnode
3. 允许进行查找的CodaCred列表
4. 对象的cnode

在Coda文件系统驱动程序中，查找调用可以通过传递名称、目录和调用者的CodaCred来从缓存请求所需对象的cnode。缓存将返回cnode或指示无法找到。Coda文件系统驱动程序必须小心地在修改或删除对象时使缓存条目失效。

当Venus获得表明缓存条目不再有效的信息时，它会向内核发起下层调用。下层调用由Coda文件系统驱动程序拦截，并导致下面描述的缓存失效。除非无法将下层调用数据读入内核内存，否则Coda文件系统驱动程序不会返回错误。

#### 5.1 无效化

此调用没有相关信息。
5.2. 清空缓存 (FLUSH)
--------------------

参数
    无

概要
    完全清空名称缓存。

描述
    Venus 在启动和终止时会发出此调用。这是为了防止缓存中保存过期的信息。某些操作系统允许动态关闭内核名称缓存，当这种情况发生时，会进行此下调。

5.3. 清除用户 (PURGEUSER)
--------------------------

参数
    ::

      struct cfs_purgeuser_out {/* CFS_PURGEUSER 是 Venus 到内核的调用 */
          struct CodaCred cred;
      } cfs_purgeuser;

描述
    删除缓存中带有 Cred 的所有条目。当用户的令牌过期或被清除时，会发出此调用。

5.4. 清除文件 (ZAPFILE)
-------------------------

参数
    ::

      struct cfs_zapfile_out {  /* CFS_ZAPFILE 是 Venus 到内核的调用 */
          ViceFid CodaFid;
      } cfs_zapfile;

描述
    删除具有指定 (dir vnode, name) 对的所有条目。此调用是在一个节点的缓存属性无效化后发出的。
  
注意
    在 NetBSD 和 Mach 中，此调用命名不正确。minicache 的 zapfile 函数接受不同的参数。Linux 没有正确实现属性的无效化。

5.5. 清除目录 (ZAPDIR)
------------------------

参数
    ::

      struct cfs_zapdir_out {   /* CFS_ZAPDIR 是 Venus 到内核的调用 */
          ViceFid CodaFid;
      } cfs_zapdir;

描述
    删除位于目录 CodaFid 及其所有子目录中的所有缓存条目。当 Venus 收到关于该目录的回调时，会发出此调用。

5.6. 清除节点 (ZAPVNODE)
--------------------------

参数
    ::

      struct cfs_zapvnode_out { /* CFS_ZAPVNODE 是 Venus 到内核的调用 */
          struct CodaCred cred;
          ViceFid VFid;
      } cfs_zapvnode;

描述
    删除带有 cred 和 VFid（作为参数）的所有缓存条目。此下调可能永远不会发出。

5.7. 清除 FID (PURGEFID)
-------------------------

参数
    ::

      struct cfs_purgefid_out { /* CFS_PURGEFID 是 Venus 到内核的调用 */
          ViceFid CodaFid;
      } cfs_purgefid;

描述
    清除文件的属性。如果这是一个目录（奇数 vnode），则从名称缓存中删除其子项，并从名称缓存中移除该文件。
### 5.8. REPLACE
--------------

#### 摘要
替换一组名称的 Fid

#### 参数
```
struct cfs_replace_out { /* cfs_replace 是一个 venus->kernel 调用 */
    ViceFid NewFid;
    ViceFid OldFid;
} cfs_replace;
```

#### 描述
此例程在名称缓存中用另一个 ViceFid 替换现有的 ViceFid。添加此功能是为了允许 Venus 在重新集成过程中，即使那些 Fid 的引用计数不为零，也可以用全局 Fid 替换本地分配的临时 Fid。

### 6. 初始化和清理
==============================

本节简要介绍了 Coda 文件系统驱动程序在启动和关闭或 Venus 故障时所需的特性。在进入讨论之前，有必要重申 Coda 文件系统驱动程序维护以下数据：

1. 消息队列
2. cnodes
3. 名称缓存条目

名称缓存条目完全属于驱动程序私有，因此可以轻松操作。消息队列通常会有明确的初始化和销毁点。cnodes 则更为脆弱。用户进程在 Coda 文件系统中持有引用计数，清理 cnodes 可能会比较困难。

它可以接收以下请求：

1. 通过消息子系统
2. 通过 VFS 层
3. 通过 pioctl 接口

目前，pioctl 通过 VFS 层传递给 Coda，因此我们可以类似地处理这些请求。

#### 6.1. 要求
------------------

应满足以下要求：

1. 消息队列应具有打开和关闭例程。在 Unix 系统上，字符设备的打开就是这样的例程。
   - 打开前，不能放置任何消息
   - 打开时将清除所有待处理的旧消息
   - 关闭时应通知任何正在睡眠的进程其回调无法完成
   - 关闭时应释放消息队列分配的所有内存

2. 在打开时，名称缓存应初始化为空状态
3. 在消息队列打开之前，所有的VFS操作都会失败。幸运的是，这可以通过确保在打开消息队列之前Coda文件系统无法挂载来实现。
4. 在关闭消息队列之后，任何VFS操作都不能成功。这里需要注意，一些操作（如查找、读/写、readdir）可以在没有上层调用的情况下继续进行。这些操作必须明确地被阻止。
5. 在关闭消息队列时，应清空并禁用名称缓存。
6. 可以在不依赖于上层调用的情况下释放所有由cnodes持有的内存。
7. 卸载文件系统可以在不依赖于上层调用的情况下完成。
8. 如果Venus无法获取根节点的rootfid或其属性，则挂载Coda文件系统应优雅地失败。最好是通过Venus在尝试挂载之前先获取这些对象来实现。

注意：

特别是NetBSD，以及Linux，目前尚未完全实现上述要求。为了顺畅运行，需要对此进行修正。
