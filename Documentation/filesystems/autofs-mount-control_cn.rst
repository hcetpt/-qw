SPDX 许可声明标识符: GPL-2.0

====================================================================
用于 autofs 内核模块的杂项设备控制操作
====================================================================

问题描述
===========

在 autofs 中存在一个与活动重启相关的问题（即在有忙挂载的情况下重启 autofs）。
在正常运行时，autofs 使用打开目标目录的文件描述符来执行控制操作。使用文件描述符使 ioctl 操作能够访问存储在超级块中的 autofs 特定信息。这些操作包括设置 autofs 挂载为僵化状态、设置超时到期时间以及请求到期检查。如下面解释的那样，某些类型的 autofs 触发挂载可能会覆盖 autofs 挂载本身，这导致我们无法使用 `open(2)` 获得用于这些操作的文件描述符，除非我们已经有一个打开的文件描述符。

目前 autofs 使用 "umount -l"（懒惰卸载）来在重启时清除活动挂载。虽然懒惰卸载在大多数情况下有效，但任何需要回溯挂载树以构建路径的操作，如 `getcwd(2)` 和 `/proc/<pid>/cwd` 文件系统，将不再起作用，因为构建路径的起点已经被从挂载树中分离了。

autofs 的实际问题是它无法重新连接到现有的挂载点。乍一看，添加重新挂载 autofs 文件系统的能力似乎可以解决问题，但实际上这行不通。这是因为 autofs 直接挂载和嵌套挂载树的“按需挂载和过期”实现使得文件系统直接挂载在触发目录 dentry 上。

例如，有两种类型的自动挂载映射：直接映射（在内核模块源代码中，你会看到第三种类型称为偏移量，实际上它只是直接挂载的一种变体）和间接映射。

这里是一个包含直接和间接映射条目的主映射示例：

```
/-      /etc/auto.direct
/test   /etc/auto.indirect
```

相应的映射文件如下：

```
/etc/auto.direct:

/automount/dparse/g6  budgie:/autofs/export1
/automount/dparse/g1  shark:/autofs/export1
等等
```

```
/etc/auto.indirect:

g1    shark:/autofs/export1
g6    budgie:/autofs/export1
等等
```

对于上述间接映射，一个 autofs 文件系统被挂载在 `/test` 上，并且每个子目录键通过 inode 查找操作触发挂载。例如，可以看到 `/test/g1` 上挂载了 `shark:/autofs/export1`。

直接挂载的处理方式是在每个完整路径上进行 autofs 挂载，如 `/automount/dparse/g1`，并将其作为挂载触发器。因此，当我们遍历路径时，我们会在这个挂载点上挂载 `shark:/autofs/export1`。由于这些总是目录，我们可以使用 `follow_link` inode 操作来触发挂载。

但是，直接映射和间接映射中的每个条目都可以有偏移量（使其成为多挂载映射条目）。
例如，一个间接挂载映射条目可以是这样的：

    g1  \
    /        shark:/autofs/export5/testing/test \
    /s1      shark:/autofs/export/testing/test/s1 \
    /s2      shark:/autofs/export5/testing/test/s2 \
    /s1/ss1  shark:/autofs/export1 \
    /s2/ss2  shark:/autofs/export2

类似地，一个直接挂载映射条目也可以是这样的：

    /automount/dparse/g1 \
    /       shark:/autofs/export5/testing/test \
    /s1     shark:/autofs/export/testing/test/s1 \
    /s2     shark:/autofs/export5/testing/test/s2 \
    /s1/ss1 shark:/autofs/export2 \
    /s2/ss2 shark:/autofs/export2

自动挂载系统第4版的一个问题是，在挂载具有大量偏移量的条目时（可能带有嵌套），我们需要将所有偏移量作为一个整体进行挂载和卸载。这本身并不是一个问题，除非有大量偏移量的映射条目的用户会遇到问题。这种机制用于众所周知的“hosts”映射，并且我们已经看到在2.4版本中出现过可用挂载数量耗尽或特权端口数量耗尽的情况。在第5版中，我们仅在遍历偏移量树的过程中进行挂载，并且同样地，这也解决了上述问题。实现细节稍微复杂一些，但对于解释问题来说并不需要了解这些细节。重要的一点是，这些偏移量使用了与上面直接挂载相同的机制，因此挂载点可以被覆盖。当前的自动挂载实现使用打开在挂载点上的ioctl文件描述符来进行控制操作。该描述符持有的引用在检查挂载是否正在使用时被考虑，并且也用于访问存储在挂载超级块中的自动挂载文件系统信息。因此，使用文件句柄的需求需要保留。

### 解决方案

为了能够在保留现有直接、间接和偏移挂载的情况下重启自动挂载系统，我们需要能够获取这些潜在覆盖的自动挂载点的文件句柄。与其单独实现一个孤立的操作，决定重新实现现有的ioctl接口并添加新的操作来提供此功能。此外，为了能够重建包含忙挂载的挂载树，需要记录触发挂载请求的最后用户的uid和gid，因为这些可以作为自动挂载映射中的宏替换变量。它们在挂载请求时被记录，并且添加了一个操作来检索它们。由于我们在重新实现控制接口，因此还解决了现有接口的一些其他问题。首先，当挂载或到期操作完成时，通过“发送就绪”或“发送失败”操作将状态返回给内核。ioctl接口的“发送失败”操作只能发送ENOENT，而重新实现允许用户空间发送实际的状态。对于使用非常大映射表的用户来说，在用户空间中发现挂载是否存在是一个昂贵的操作。通常涉及扫描/proc/mounts，由于需要频繁执行此操作，当挂载表中有许多条目时，可能会引入显著的开销。因此，还添加了一个操作来查找挂载点dentry（无论是否被覆盖）的挂载状态。

当前内核开发策略建议避免使用ioctl机制，转而使用Netlink等系统。为此实现了一个使用该系统的版本以评估其适用性，但发现它不适用于此情况。这里使用的是通用Netlink系统，因为原始Netlink会导致复杂性的显著增加。毫无疑问，通用Netlink系统对于常见的ioctl功能是一个优雅的解决方案，但它并不是一个完整的替代品，可能是因为它的主要目的是作为消息总线实现，而不是专门作为ioctl的替代品。虽然可以绕过这个问题，但有一个担忧导致了不使用它的决定。即自动挂载守护进程中的到期操作变得过于复杂，因为卸载候选者被枚举，几乎只是为了“计数”要调用到期ioctl的次数。这涉及扫描挂载表，对于使用大型映射表的用户来说，这已经被证明是一个很大的开销。改进这一点的最佳方法是尝试恢复到以前处理到期的方式。即当发出挂载（文件句柄）的到期请求时，我们应该持续回调到守护进程，直到无法再卸载任何挂载为止，然后返回相应的状态给守护进程。目前我们一次只让一个挂载到期。通用Netlink实现将排除未来发展的可能性，因为消息总线架构的要求。

### 自动挂载杂项设备挂载控制接口

控制接口是打开一个设备节点，通常是/dev/autofs。
所有 `ioctl` 调用使用一个通用结构来传递所需的参数信息并返回操作结果：

```c
struct autofs_dev_ioctl {
    __u32 ver_major;            /* 主版本号 */
    __u32 ver_minor;            /* 次版本号 */
    __u32 size;                 /* 包括此结构在内的总数据大小 */
    __s32 ioctlfd;              /* automount 命令文件描述符 */

    /* 命令参数 */
    union {
        struct args_protover;       /* 协议主版本 */
        struct args_protosubver;    /* 协议次版本 */
        struct args_openmount;      /* 打开挂载点 */
        struct args_ready;          /* 准备就绪 */
        struct args_fail;           /* 失败 */
        struct args_setpipefd;      /* 设置管道文件描述符 */
        struct args_timeout;        /* 超时 */
        struct args_requester;      /* 请求者 */
        struct args_expire;         /* 过期 */
        struct args_askumount;      /* 请求卸载 */
        struct args_ismountpoint;   /* 是否为挂载点 */
    };

    char path[];                   /* 路径 */
};
```

`ioctlfd` 字段是一个自动挂载点的文件描述符。它由 `open` 调用返回，并用于除检查给定路径是否为挂载点外的所有调用，在这种情况下，它可以可选地用于检查特定的挂载点文件描述符。当请求自动挂载文件系统中目录的最后一个成功挂载的 `uid` 和 `gid` 时也会使用该字段。

联合体用于传递调用过程中需要的参数和结果。
`path` 字段在需要时用于传递路径，`size` 字段用于计算结构体长度增加的部分，当从用户空间翻译结构体时会用到。

这个结构体可以通过 `init_autofs_dev_ioctl` 函数初始化特定字段。所有 `ioctl` 调用都会将此结构体从用户空间复制到内核空间，并在 `size` 参数小于结构体本身大小时返回 `-EINVAL`，在内核内存分配失败时返回 `-ENOMEM`，在复制失败时返回 `-EFAULT`。其他检查包括编译时的用户空间版本与模块版本之间的比较，不匹配则返回 `-EINVAL`。如果 `size` 字段大于结构体大小，则假定存在路径，并检查其是否以 `/` 开头且以 NULL 结尾，否则返回 `-EINVAL`。经过这些检查后，对于除了 `AUTOFS_DEV_IOCTL_VERSION_CMD`、`AUTOFS_DEV_IOCTL_OPENMOUNT_CMD` 和 `AUTOFS_DEV_IOCTL_CLOSEMOUNT_CMD` 以外的所有 `ioctl` 命令，`ioctlfd` 将被验证，如果不是有效的描述符或不对应于自动挂载点，则返回 `-EBADF`、`-ENOTTY` 或 `-EINVAL`（不是自动挂载描述符）错误。

### ioctl 调用

一个使用此接口的实现示例可以在自动挂载版本 5.0.4 及以后的版本中找到，具体位于从 kernel.org 下载的分发包中的 `lib/dev-ioctl-lib.c` 文件中，路径为 `/pub/linux/daemons/autofs/v5`。

此接口实现的设备节点 `ioctl` 操作如下：

#### AUTOFS_DEV_IOCTL_VERSION
获取自动挂载设备 `ioctl` 内核模块实现的主版本和次版本。需要一个初始化后的 `struct autofs_dev_ioctl` 作为输入参数，并在传入的结构体中设置版本信息。成功时返回 0，检测到版本不匹配时返回 `-EINVAL`。

#### AUTOFS_DEV_IOCTL_PROTOVER_CMD 和 AUTOFS_DEV_IOCTL_PROTOSUBVER_CMD
获取加载模块理解的自动挂载协议版本的主版本和次版本。需要一个初始化后的 `struct autofs_dev_ioctl`，并且 `ioctlfd` 字段设置为有效的自动挂载点描述符。这些命令会在 `struct args_protover` 的 `version` 字段或 `struct args_protosubver` 的 `sub_version` 字段中设置请求的版本号。成功时返回 0，验证失败时返回负错误代码。

#### AUTOFS_DEV_IOCTL_OPENMOUNT 和 AUTOFS_DEV_IOCTL_CLOSEMOUNT
获取和释放自动挂载管理的挂载点路径的文件描述符。`open` 调用需要一个初始化后的 `struct autofs_dev_ioctl`，其中 `path` 字段已设置，`size` 字段已适当调整，并且 `struct args_openmount` 的 `devid` 字段设置为自动挂载的设备编号。设备编号可以从 `/proc/mounts` 中显示的挂载选项获得。`close` 调用需要一个初始化后的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为 `open` 调用返回的描述符。也可以通过 `close(2)` 来释放文件描述符，因此任何打开的描述符将在进程退出时关闭。
近距离调用（close call）主要包含在已实现的操作中，以确保完整性并提供一致的用户空间实现。以下是具体的 ioctl 命令：

### AUTOFS_DEV_IOCTL_READY_CMD 和 AUTOFS_DEV_IOCTL_FAIL_CMD
---------------------------------------------

从用户空间返回挂载和过期结果状态到内核。
这两个调用都需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为从 `open` 调用获得的描述符，以及 `struct args_ready` 或 `struct args_fail` 中的 `token` 字段设置为用户空间在之前的挂载或过期请求中接收到的等待队列令牌号。
`struct args_fail` 的 `status` 字段设置为操作的 `errno`。如果成功，则将其设置为 0。

### AUTOFS_DEV_IOCTL_SETPIPEFD_CMD
-----------------------------------

设置用于内核通信的管道文件描述符。
通常这是在挂载时使用选项设置的，但在重新连接到现有挂载时，我们需要使用此命令来告诉自动挂载点关于新的内核管道描述符。为了保护挂载点不被错误地设置管道描述符，我们还要求自动挂载点处于僵化状态（参见下一个调用）。
该调用需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为从 `open` 调用获得的描述符，而 `struct args_setpipefd` 中的 `pipefd` 字段设置为管道的描述符。
成功后，该调用还将用于标识控制进程（例如，拥有 automount(8) 守护进程）的进程组 ID 设置为调用者的进程组。

### AUTOFS_DEV_IOCTL_CATATONIC_CMD
-----------------------------------

使自动挂载点进入僵化状态。自动挂载点将不再发出挂载请求，内核通信管道描述符被释放，并且队列中剩余的所有等待也被释放。
该调用需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为从 `open` 调用获得的描述符。

### AUTOFS_DEV_IOCTL_TIMEOUT_CMD
--------------------------------

设置自动挂载点内的挂载过期超时时间。
### AUTOFS_DEV_IOCTL_REQUESTER_CMD

返回在给定路径 dentry 上成功触发挂载的最后一个进程的 uid 和 gid。
调用需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `path` 字段设置为要查询的挂载点，并且调整 `size` 字段。返回时，`struct args_requester` 中的 `uid` 字段包含 uid，`gid` 字段包含 gid。
当重新构建带有活动挂载的 autofs 挂载树时，我们需要重新连接到可能使用原始进程 uid 和 gid（或它们的字符串变体）进行挂载查找的挂载点。此调用提供了获取这些 uid 和 gid 的能力，以便用户空间可以用于挂载映射查找。

### AUTOFS_DEV_IOCTL_EXPIRE_CMD

向内核发送一个 autofs 挂载的过期请求。通常，这个 ioctl 调用会一直执行直到没有进一步的过期候选对象。
调用需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为从 `open` 调用中获得的描述符。此外，可以通过将 `struct args_expire` 中的 `how` 字段设置为 `AUTOFS_EXP_IMMEDIATE` 或 `AUTOFS_EXP_FORCED` 来请求立即过期（独立于挂载超时）或强制过期（独立于挂载是否忙碌）。如果没有找到过期候选对象，则 ioctl 返回 -1 并将 `errno` 设置为 `EAGAIN`。
此调用导致内核模块检查与给定 `ioctlfd` 对应的挂载点是否有可以过期的挂载点，然后向守护进程发出过期请求并等待完成。

### AUTOFS_DEV_IOCTL_ASKUMOUNT_CMD

检查一个 autofs 挂载点是否正在使用中。
调用需要一个初始化好的 `struct autofs_dev_ioctl`，其中 `ioctlfd` 字段设置为从 `open` 调用中获得的描述符，并且结果会返回在 `struct args_askumount` 的 `may_umount` 字段中，忙时返回 1，否则返回 0。
### AUTOFS_DEV_IOCTL_ISMOUNTPOINT_CMD

检查给定路径是否为挂载点。
此调用需要一个已初始化的 `struct autofs_dev_ioctl`。有两种可能的变化形式。两者都使用 `path` 字段设置为要检查的挂载点路径，并且调整了 `size` 字段。一种使用 `ioctlfd` 字段来标识特定的挂载点，而另一种变化形式则使用 `path` 和可选的 `in.type` 字段（`struct args_ismountpoint` 中的 `autofs` 挂载类型）。如果这是一个挂载点，则调用返回 1，并将 `out.devid` 字段设置为挂载设备的编号，将 `out.magic` 字段设置为相关的超级块魔法数字（如下所述）；如果不是挂载点，则返回 0。在两种情况下，设备编号（由 `new_encode_dev()` 返回）都会存储在 `out.devid` 字段中。

如果提供了一个文件描述符，我们寻找的是一个特定的挂载点，而不一定是挂载堆栈顶部的挂载点。在这种情况下，如果该描述符对应的路径本身是一个挂载点或者包含一个挂载点（如多挂载但没有根挂载），则认为它是挂载点。如果描述符对应于一个挂载点，则返回 1 并返回覆盖挂载的超级魔法数字（如果有）；如果不是挂载点，则返回 0。

如果提供了路径（并且 `ioctlfd` 字段设置为 -1），则查找该路径并检查它是否是挂载点的根目录。如果还指定了类型，我们正在寻找特定的 `autofs` 挂载点，如果没有找到匹配项，则返回失败。如果找到的路径是挂载点的根目录，则返回 1 并附带挂载点的超级魔法数字；否则返回 0。
